"""Bounded direct Messages adapter; no scientific or payment authorization.

Only explicitly supplied keys, endpoints, profiles and shared ledgers are used.
Count estimates are preflight observations; settlement uses inclusive billed usage.
"""
from copy import deepcopy
from dataclasses import dataclass, field
import http.client
import json
from pathlib import Path
import re
import time
import uuid

from .codec import MAX_BYTES, Invalid, canonical, decode, digest, integer, text
from .openai_provider import SpendLedger, WireFailure, _remaining

MODEL = 'claude-sonnet-5-5'
API_VERSION = '2026-10-21'
PROVIDER = 'anthropic.messages/1'
PRICING = {
    'version': 'anthropic-sonnet-5-5-standard-global-2026-10-25/1',
    'currency': 'USD', 'units_per_usd': 1000000000,
    'input_upper_nano_per_token': 4000, 'output_nano_per_token': 10000,
    'qualification': 'Conservative published-rate bound using the one-hour cache-write rate for all input; not an invoice.',
    'sources': ['https://platform.claude.com/docs/en/models/sonnet-5-5/overview',
                'https://platform.claude.com/docs/en/about-claude/pricing'],
}


def require(condition, message):
    if not condition:
        raise Invalid(message)


def provider_identity(reported_model=None):
    return {'requested_model': MODEL, 'reported_model': reported_model,
            'catalog_name': 'Claude Sonnet 5.5', 'catalog_version': '5.5',
            'catalog_source': 'https://platform.claude.com/docs/en/models/sonnet-5-5/overview',
            'immutable_snapshot_id': None, 'immutable_snapshot_status': 'UNKNOWN'}


def configuration(*, aggregate_budget_nano, budget_scope_ref, input_token_limit=20000,
                  output_token_limit=4096, now=None, workspace_id=None):
    result = {'schema': 'anthropic-messages-configuration/1', 'model': MODEL,
              'api_version': API_VERSION, 'input_token_limit': input_token_limit,
              'output_token_limit': output_token_limit, 'effort': 'high', 'pricing': deepcopy(PRICING),
              'expires_at': int(time.time() if now is None else now) + 86400,
              'aggregate_budget_nano': aggregate_budget_nano, 'budget_scope_ref': budget_scope_ref,
              'workspace_id': workspace_id}
    _config(result)
    return result


def _config(config):
    require(type(config) is dict and set(config) == {'schema', 'model', 'api_version',
            'input_token_limit', 'output_token_limit', 'effort', 'pricing', 'expires_at',
            'aggregate_budget_nano', 'budget_scope_ref', 'workspace_id'}, 'Exact frozen Messages configuration required')
    require(config['schema'] == 'anthropic-messages-configuration/1' and config['model'] == MODEL
            and config['api_version'] == API_VERSION and canonical(config['pricing']) == canonical(PRICING)
            and config['effort'] in ('low', 'medium', 'high', 'xhigh', 'max'), 'Unsupported Messages profile')
    for key in ('input_token_limit', 'output_token_limit', 'expires_at', 'aggregate_budget_nano'):
        integer(config[key], key, 1)
    require(config['input_token_limit'] + config['output_token_limit'] <= 80000, 'Call exceeds epoch token ceiling')
    text(config['budget_scope_ref'], 'operator supplied budget scope reference')
    workspace = config['workspace_id']
    require(workspace is None or type(workspace) is str and
            re.fullmatch(r'wrkspc_[A-Za-z0-9_-]{1,128}', workspace), 'Invalid explicit workspace')
    canonical(config)


def cost_bound(input_tokens, output_tokens):
    integer(input_tokens, 'input tokens')
    integer(output_tokens, 'output tokens')
    return input_tokens * 4000 + output_tokens * 10000


def _content(blocks):
    require(type(blocks) is list, 'Native Messages content required')
    for block in blocks:
        require(type(block) is dict, 'Native content block required')
        kind = block.get('type')
        if kind == 'text':
            require(set(block) <= {'type', 'text', 'citations'} and type(block.get('text')) is str
                    and block.get('citations') in (None, []), 'Unsupported annotated text')
        elif kind == 'thinking':
            require(set(block) == {'type', 'thinking', 'signature'} and block['thinking'] == '',
                    'Only omitted thinking is requested and replayed')
            require(type(block['signature']) is str and block['signature'], 'Opaque thinking signature required')
        elif kind == 'redacted_thinking':
            require(set(block) == {'type', 'data'}, 'Unsupported redacted continuation')
            require(type(block['data']) is str and block['data'], 'Opaque continuation required')
        elif kind == 'tool_use':
            require(set(block) <= {'type', 'id', 'name', 'input', 'caller'}
                    and type(block.get('input')) is dict, 'Only native client tools are supported')
            text(block.get('id'), 'native tool identity')
            text(block.get('name'), 'native tool name')
            require(block.get('caller', {'type': 'direct'}) == {'type': 'direct'}, 'Hosted callers are unsupported')
        else:
            raise Invalid('Unsupported provider content type')
    canonical(blocks)
    return deepcopy(blocks)


def wire_request(request, config):
    _config(config)
    require(type(request) is dict and set(request) == {'model', 'prompt_version', 'messages', 'tools',
            'generation_parameters'}, 'Exact normalized request required')
    require(request['model'] == MODEL and canonical(request['generation_parameters']) ==
            canonical({'anthropic_messages': config}), 'Request differs from frozen Messages profile')
    text(request['prompt_version'], 'prompt version')
    require(type(request['tools']) is list and type(request['messages']) is list, 'Explicit tools and messages required')
    tools, names = [], set()
    for tool in request['tools']:
        require(type(tool) is dict and set(tool) == {'name', 'description', 'parameters'}
                and type(tool['parameters']) is dict, 'Explicit client tool required')
        name = text(tool['name'], 'tool name')
        text(tool['description'], 'tool description')
        require(name not in names, 'Duplicate tool definition')
        names.add(name)
        tools.append({'name': name, 'description': tool['description'], 'input_schema': deepcopy(tool['parameters'])})
    history, pending, seen, tool_results = [], {}, set(), []
    system = None
    for index, message in enumerate(request['messages']):
        require(type(message) is dict and set(message) == {'role', 'content'}
                and type(message['content']) is str, 'Normalized public message required')
        role = message['role']
        if role == 'system':
            require(index == 0 and system is None, 'Exactly one initial system prompt required')
            system = message['content']
        elif role == 'user':
            require(not pending and system is not None, 'Missing tool results or initial system prompt')
            history.append({'role': 'user', 'content': message['content']})
        elif role == 'assistant':
            require(not pending and history, 'Missing input or previous tool results')
            response = decode(message['content'])
            require(type(response) is dict and response.get('provider_id') == PROVIDER,
                    'Cannot replay a different provider as Claude')
            # Transport failures contain no provider-generated continuation.
            if response.get('status') in ('failed', 'timeout', 'cancelled', 'input_limit'):
                require(not response.get('provider_content'), 'Failed call contains unverified native content')
                continue
            require(response.get('status') == 'completed' and response.get('resolved_model') == MODEL,
                    'Only completed matching-model responses can be replayed')
            blocks = _content(response.get('provider_content'))
            for block in blocks:
                if block['type'] == 'tool_use':
                    identity, name = block['id'], block['name']
                    require(identity not in seen and name in names, 'Duplicate or unauthorized tool')
                    pending[identity] = {'id': identity, 'name': name, 'arguments': block['input']}
                    seen.add(identity)
            require(bool(pending) == (response.get('stop_reason') == 'tool_use'), 'Stop reason and native tools disagree')
            history.append({'role': 'assistant', 'content': blocks})
        elif role == 'tool':
            body = decode(message['content'])
            require(type(body) is dict, 'Tool response body required')
            call = body.get('tool_request')
            require(type(call) is dict and type(call.get('id')) is str, 'Tool response identity required')
            identity = call['id']
            require(body.get('schema') == 'provider-tool-result/1' and identity in pending
                    and canonical(call) == canonical(pending[identity]), 'Unmatched, altered or duplicate tool result')
            tool_results.append({'type': 'tool_result', 'tool_use_id': identity, 'content': canonical(body['result'])})
            del pending[identity]
            if not pending:
                history.append({'role': 'user', 'content': tool_results})
                tool_results = []
        else:
            raise Invalid('Unsupported normalized message role')
    require(system is not None and history and not pending and not tool_results
            and history[0]['role'] == 'user' and history[-1]['role'] == 'user', 'Incomplete provider conversation')
    result = {'model': MODEL, 'system': system, 'messages': history, 'tools': tools,
              'max_tokens': config['output_token_limit'], 'stream': False,
              'service_tier': 'standard_only', 'inference_geo': 'global',
              'thinking': {'type': 'adaptive', 'display': 'omitted'},
              'output_config': {'effort': config['effort']}}
    if tools:
        result['tool_choice'] = {'type': 'auto', 'disable_parallel_tool_use': True}
    canonical(result)
    return result


def parse_response(raw, request_id, config):
    _config(config)
    require(type(raw) is dict, 'Expected Messages object')
    public = {'provider_id': PROVIDER, 'provider_request_id': raw.get('id') if type(raw.get('id')) is str else None,
              'transport_request_id': request_id if type(request_id) is str else None,
              'resolved_model': raw.get('model') if type(raw.get('model')) is str else None,
              'status': 'unverified_response', 'output': None, 'provider_content': [], 'provider_usage': None,
              'stop_reason': raw.get('stop_reason') if type(raw.get('stop_reason')) is str else None,
              'pricing': deepcopy(PRICING), 'token_usage_details': {
                  'cached_input_tokens': None, 'reasoning_output_tokens': None}}
    public['model_identity'] = provider_identity(public['resolved_model'])
    # Retain representable public content even when unusable; never execute it then.
    for field, source in (('provider_content', 'content'), ('provider_usage', 'usage')):
        try:
            canonical(raw.get(source))
            public[field] = deepcopy(raw.get(source))
        except Invalid:
            public[field + '_json'] = json.dumps(raw.get(source), ensure_ascii=False, separators=(',', ':'))
    usage = None
    try:
        measured = raw['usage']
        require(type(measured) is dict and raw.get('model') == MODEL
                and measured.get('service_tier') == 'standard' and measured.get('inference_geo') == 'global'
                and measured.get('speed') in (None, 'standard'), 'Unknown served model or tariff')
        require(measured.get('iterations') in (None, []), 'Unpriced provider iterations')
        hosted = measured.get('server_tool_use')
        require(hosted is None or type(hosted) is dict and
                set(hosted) == {'web_fetch_requests', 'web_search_requests'} and
                all(type(value) is int and value == 0 for value in hosted.values()), 'Unpriced hosted work')
        blocks = raw.get('content')
        if type(blocks) is list:
            for block in blocks:
                if type(block) is dict:
                    require(block.get('type') in ('text', 'thinking', 'redacted_thinking', 'tool_use'),
                            'Unpriced provider content')
                    if block['type'] == 'tool_use':
                        require(block.get('caller', {'type': 'direct'}) == {'type': 'direct'},
                                'Unpriced hosted caller')
        a = sum(integer(measured[name], name) for name in
                ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))
        b = integer(measured['output_tokens'], 'output tokens')
        usage = {'input_tokens': a, 'output_tokens': b, 'cost_units': cost_bound(a, b)}
        public['token_usage_details']['cached_input_tokens'] = measured['cache_read_input_tokens']
        details = measured.get('output_tokens_details')
        thinking = details.get('thinking_tokens') if type(details) is dict else None
        if type(thinking) is int and 0 <= thinking <= b:
            public['token_usage_details']['reasoning_output_tokens'] = thinking
    except (Invalid, KeyError, TypeError):
        pass
    metadata_valid = (type(raw.get('id')) is str and bool(raw['id'])
                      and raw.get('type') == 'message' and raw.get('role') == 'assistant')
    overrun = usage is not None and (usage['input_tokens'] > config['input_token_limit']
                                    or usage['output_tokens'] > config['output_token_limit'])
    if metadata_valid and usage is not None and not overrun:
        try:
            blocks = _content(raw.get('content'))
            calls = [{'id': b['id'], 'name': b['name'], 'arguments': b['input']}
                     for b in blocks if b['type'] == 'tool_use']
            require(len({c['id'] for c in calls}) == len(calls) and len(calls) <= 16, 'Duplicate or too many tools')
            reason = raw.get('stop_reason')
            if reason == 'tool_use':
                require(calls and raw.get('stop_sequence') is None, 'Tool stop requires native client calls')
                public.update(status='completed', output={'status': 'tools', 'calls': calls})
            elif reason == 'end_turn':
                require(not calls and raw.get('stop_sequence') is None, 'Final turn contains unresolved tools')
                result = decode(''.join(b['text'] for b in blocks if b['type'] == 'text'))
                require(type(result) is dict and result.get('status') == 'final', 'Only final JSON is accepted as text')
                public.update(status='completed', output=result)
            elif reason == 'refusal':
                public['status'] = 'refused'
            elif reason in ('max_tokens', 'model_context_window_exceeded', 'stop_sequence', 'pause_turn'):
                public['status'] = 'incomplete'
            else:
                public['status'] = 'invalid_output'
        except (Invalid, TypeError, KeyError):
            public['status'] = 'invalid_output'
    elif overrun:
        public['status'] = 'bounds_exceeded'
    result = {'response': public, 'usage': usage}
    canonical(result)
    return result


def _post(endpoint, payload, key, deadline, workspace_id):
    require(endpoint in ('/v1/messages/count_tokens', '/v1/messages'), 'Unsupported Anthropic endpoint')
    body = canonical(payload).encode('utf-8')
    headers = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'anthropic-version': API_VERSION}
    if workspace_id is not None:
        require(type(workspace_id) is str and re.fullmatch(r'wrkspc_[A-Za-z0-9_-]{1,128}', workspace_id),
                'Invalid workspace header')
        headers['anthropic-workspace-id'] = workspace_id
    connection = http.client.HTTPSConnection('api.anthropic.com', 443, timeout=_remaining(deadline))
    try:
        connection.request('POST', endpoint, body=body, headers=headers)
        if connection.sock:
            connection.sock.settimeout(_remaining(deadline))
        response = connection.getresponse()
        identity = response.getheader('request-id')
        identity = identity if type(identity) is str and re.fullmatch(r'req_[A-Za-z0-9_-]{1,128}', identity) else None
        if not 200 <= response.status < 300:
            raise WireFailure('http_error', response.status, identity)
        blocks, size = [], 0
        while True:
            remaining = _remaining(deadline)
            if connection.sock:
                connection.sock.settimeout(remaining)
            block = response.read1(min(65536, MAX_BYTES + 1 - size))
            if not block:
                break
            blocks.append(block)
            size += len(block)
            if size > MAX_BYTES:
                raise WireFailure('response_size', request_id=identity)
        _remaining(deadline)
        def unique(pairs):
            result = {}
            for name, value in pairs:
                if name in result:
                    raise WireFailure('duplicate_json_key', request_id=identity)
                result[name] = value
            return result
        raw = json.loads(b''.join(blocks), object_pairs_hook=unique)
        require(type(raw) is dict, 'Expected API object')
        return raw, identity
    except WireFailure:
        raise
    except Exception as exc:
        raise WireFailure(type(exc).__name__) from None
    finally:
        connection.close()


def _key(path):
    path = Path(path)
    require(not path.is_symlink() and path.stat().st_size <= 65536, 'Invalid credential destination')
    matches = []
    for line in path.read_text(encoding='utf-8').splitlines():
        found = re.fullmatch(r'ANTHROPIC_API_KEY=(sk-ant-api[A-Za-z0-9_-]+)[ \t]*', line)
        if found:
            matches.append(found.group(1))
    require(len(matches) == 1, 'Exactly one explicit Anthropic API key required')
    return matches[0]


@dataclass
class AnthropicMessagesProvider:
    key_file: object = field(repr=False)
    budget_file: object
    config: dict
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    epoch_id: str | None = None
    worker: str | None = None
    model: str = field(default=MODEL, init=False)
    mode: str = field(default='live', init=False)

    def __post_init__(self):
        _config(self.config)
        self.config = deepcopy(self.config)

    def reservation(self, request, output_limit):
        wire_request(request, self.config)
        require(output_limit == self.config['output_token_limit'], 'Output limit differs from frozen profile')
        require(time.time() < self.config['expires_at'], 'Dated tariff requires refresh')
        return {'input_token_bound': self.config['input_token_limit'], 'output_token_limit': output_limit,
                'cost_bound_units': cost_bound(self.config['input_token_limit'], output_limit)}

    def complete(self, request, ordinal, timeout):
        integer(ordinal, 'call ordinal')
        deadline, reserved = time.monotonic() + timeout, None
        ledger = SpendLedger(self.budget_file, self.config['aggregate_budget_nano'])
        try:
            bounds = self.reservation(request, self.config['output_token_limit'])
            payload = wire_request(request, self.config)
            key = _key(self.key_file)
            counted = {name: payload[name] for name in ('model', 'messages', 'system', 'tools', 'thinking', 'tool_choice')
                       if name in payload}
            count, count_id = _post('/v1/messages/count_tokens', counted, key, deadline, self.config['workspace_id'])
            tokens = integer(count.get('input_tokens'), 'estimated input tokens')
            if tokens > bounds['input_token_bound']:
                return {'response': {'status': 'input_limit', 'provider_id': PROVIDER, 'counted_input_tokens': tokens,
                        'transport_request_id': count_id}, 'usage': {'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0}}
            reserved = ledger.reserve(digest(payload), bounds['cost_bound_units'], key=self.run_id + ':' + str(ordinal),
                metadata={'provider': 'anthropic', 'budget_scope_ref': self.config['budget_scope_ref'],
                          'run_id': self.run_id, 'epoch_id': self.epoch_id, 'worker': self.worker, 'ordinal': ordinal,
                          'model': MODEL, 'model_identity': provider_identity(), 'prompt_version': request['prompt_version'],
                          'counted_input_tokens': tokens})
            raw, request_id = _post('/v1/messages', payload, key, deadline, self.config['workspace_id'])
            result = parse_response(raw, request_id, self.config)
            public, usage = result['response'], result['usage']
            public.update(counted_input_tokens=tokens, wire_request_sha256=digest(payload),
                          aggregate_dispatch_id=reserved, usage_charge_basis='conservative_published_rate_upper_bound')
            canonical(result)
            receipt = {'usage': usage, 'token_details': public['token_usage_details'], 'response_status': public['status'],
                       'transport_request_id': public['transport_request_id'], 'provider_request_id': public['provider_request_id'],
                       'model_identity': public['model_identity']}
            ledger.settle(reserved, None if usage is None else usage['cost_units'],
                          halt=public['status'] in ('bounds_exceeded', 'unverified_response'), receipt=receipt)
            return result
        except Exception as exc:
            if reserved is not None:
                try:
                    ledger.settle(reserved, None)
                except Exception:
                    pass  # Failed persistence leaves the original reservation charged.
            public = {'status': 'failed', 'provider_id': PROVIDER, 'error_type': type(exc).__name__}
            if isinstance(exc, WireFailure):
                public.update(error_kind=exc.kind, http_status=exc.status, transport_request_id=exc.request_id)
            return {'response': public, 'usage': None if reserved is not None else
                    {'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0}}
