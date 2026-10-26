"""Bounded provider-neutral researcher; fixture adapters prove machinery only.

Adapters are trusted installed code, never code supplied by a model. Only their
public request/response contract crosses the child-process boundary. The model
gets no RPC capability, operator key, shell, or arbitrary network tool.
"""
from dataclasses import dataclass
import multiprocessing
import threading
import time

from .codec import Invalid, MAX_BYTES, canonical, decode, text
from .errors import Conflict, Denied
from .server import RemoteError
from .measurements import MEASUREMENT_TOOL
from .context_views import SECTION_TOOL, PRESENTATION_PROFILES, TOOL_VIEW_PROFILE, source_section, source_view


TOOL_DEFINITIONS = [
    {'name': 'read_source', 'description': 'Read an authorized source from this frozen context.',
     'parameters': {'type': 'object', 'properties': {'artifact_id': {'type': 'string'}},
                    'required': ['artifact_id'], 'additionalProperties': False}},
    {'name': 'search_memory', 'description': 'Search only this context and current private attempt.',
     'parameters': {'type': 'object', 'properties': {'query': {'type': 'string'}},
                    'required': ['query'], 'additionalProperties': False}},
    {'name': 'record_research', 'description': 'Retain an unverified idea, observation, or capability gap.',
     'parameters': {'type': 'object', 'properties': {
         'kind': {'enum': ['idea', 'observation', 'gap', 'research_experience']},
         'content': {'type': 'object'}, 'scope': {'type': 'object'},
         'source_refs': {'type': 'array', 'items': {'type': 'string'}}},
         'required': ['kind', 'content', 'scope', 'source_refs'], 'additionalProperties': False}},
    {'name': 'capabilities', 'description': 'Read installed research capabilities and their limits.',
     'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}},
]
DEVELOPMENT_TOOL_DEFINITIONS = [*TOOL_DEFINITIONS, MEASUREMENT_TOOL]
CONTEXT_TOOL_DEFINITIONS = [*DEVELOPMENT_TOOL_DEFINITIONS, SECTION_TOOL]
ERRORS = (Invalid, Conflict, Denied, RemoteError)


@dataclass
class ScriptedProvider:
    """Deterministic public replies, no model invocation and no network traffic.

    Token counts are synthetic UTF-8 byte counts for the fixture only. They are
    not a tokenizer or cost estimate for any real provider.
    """
    replies: list
    delay_seconds: int = 0
    model: str = 'fixture/1'
    mode: str = 'fixture'

    def reservation(self, request, output_limit):
        return {'input_token_bound': len(canonical(request).encode('utf-8')) + 1024,
                'output_token_limit': output_limit, 'cost_bound_units': 0}

    def complete(self, request, ordinal, timeout):
        if self.delay_seconds:
            time.sleep(self.delay_seconds)
        reply = self.replies[ordinal]
        return {'response': {'status': 'completed', 'provider_id': 'scripted-fixture/1',
                             'provider_request_id': 'fixture-' + str(ordinal), 'output': reply},
                'usage': {'input_tokens': len(canonical(request).encode('utf-8')),
                          'output_tokens': len(canonical(reply).encode('utf-8')), 'cost_units': 0}}


def _provider_child(send, provider, request, ordinal, timeout):
    try:
        result = provider.complete(request, ordinal, timeout)
        send.send_bytes(canonical(result).encode('utf-8'))
    except Exception as exc:
        # Exception strings may contain credentials or headers. Retain the class.
        send.send_bytes(canonical({'response': {'status': 'failed', 'error_type': type(exc).__name__},
                                   'usage': None}).encode('utf-8'))
    finally:
        send.close()


def _invoke(provider, request, ordinal, seconds, cancelled):
    """Hard local timeout, including startup, with cleanup before returning."""
    if seconds <= 0 or cancelled():
        return {'response': {'status': 'cancelled' if cancelled() else 'timeout'}, 'usage': None}
    context = multiprocessing.get_context('spawn')
    receive, send = context.Pipe(duplex=False)
    process = context.Process(target=_provider_child, args=(send, provider, request, ordinal, seconds), daemon=True)
    deadline = time.monotonic() + seconds
    started = False
    try:
        process.start()
        started = True
        send.close()
        while True:
            if cancelled():
                return {'response': {'status': 'cancelled'}, 'usage': None}
            if time.monotonic() >= deadline:
                return {'response': {'status': 'timeout'}, 'usage': None}
            if receive.poll(min(0.05, max(0, deadline - time.monotonic()))):
                result = decode(receive.recv_bytes(MAX_BYTES).decode('utf-8'))
                if type(result) is not dict or set(result) != {'response', 'usage'} or type(result['response']) is not dict:
                    raise Invalid('Malformed adapter envelope')
                return result
            if not process.is_alive():
                return {'response': {'status': 'failed', 'error_type': 'ProviderProcessExit'}, 'usage': None}
    except Exception as exc:
        return {'response': {'status': 'failed', 'error_type': type(exc).__name__}, 'usage': None}
    finally:
        if started:
            if process.is_alive():
                process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join(2)
            process.close()
        receive.close()
        send.close()


def _tool(client, lease, call, provider_call_id=None, tools=None):
    if type(call) is not dict or set(call) != {'id', 'name', 'arguments'}:
        raise Invalid('Malformed tool request')
    text(call['id'], 'tool call id')
    name, arguments = call['name'], call['arguments']
    allowed=TOOL_DEFINITIONS if tools is None else tools
    if name not in [item['name'] for item in allowed]:raise Denied('Tool is absent from the frozen profile')
    if type(arguments) is not dict:
        raise Invalid('Tool arguments must be an object')
    if name == 'read_source' and set(arguments) == {'artifact_id'}:
        return client.call('read_artifact', lease=lease, **arguments)
    if name == 'read_source_section' and set(arguments) == {'artifact_id', 'path', 'offset', 'limit'}:
        # Authenticate the original read before inspecting paths or slice controls.
        artifact = client.call('read_artifact', lease=lease, artifact_id=arguments['artifact_id'])
        return source_section(artifact, arguments['path'], arguments['offset'], arguments['limit'])
    if name == 'search_memory' and set(arguments) == {'query'}:
        return client.call('search_memory', lease=lease, **arguments)
    if name == 'record_research' and set(arguments) == {'kind', 'content', 'scope', 'source_refs'}:
        if arguments['kind'] not in ('idea', 'observation', 'gap', 'research_experience'):
            raise Denied('Researcher cannot publish evidence')
        return client.call('record_research', lease=lease, **arguments)
    if name == 'capabilities' and not arguments:
        result = {'version': 'research-tools/2' if MEASUREMENT_TOOL in allowed else 'research-tools/1',
                'memory': True, 'development_measurements': MEASUREMENT_TOOL in allowed,
                'formalization': False, 'scientific_evaluation': False, 'capital_authority': False}
        if SECTION_TOOL in allowed:
            result.update(version='research-tools/3', source_sections=True)
        return result
    if name == 'measure_development':
        return client.call('measure_development',lease=lease,call_id=provider_call_id,tool_id=call['id'])
    raise Denied('Tool or arguments unavailable')


def run_research_once(client, provider, cancel=None):
    """Run one fenced perspective; never retry an unresolved dispatch blindly."""
    claimed = client.call('claim')
    if claimed is None:
        return None
    lease, spec = claimed['lease'], claimed['spec']
    stopped, lost = threading.Event(), threading.Event()
    cancel = cancel or threading.Event()
    records, transcript = [], []

    def cancelled():
        return cancel.is_set() or lost.is_set()

    def blocked(reason):
        if lost.is_set():
            return {'state': 'lease_lost', 'accepted': False}
        result = client.call('block', lease=lease, reason=reason,
                             needs=['research continuation'],
                             retry_when='The recorded cause is resolved within the original budgets')
        return {**result, 'accepted': False, 'record_ids': records, 'transcript_ids': transcript,
                'scientific_authority': False, 'genuine_discovery': False}

    def heartbeat():
        while not stopped.wait(max(0.05, spec['lease_seconds'] / 3)):
            try:
                client.call('heartbeat', lease=lease)
            except Exception:
                lost.set()
                return

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        state = client.call('research_call_state', lease=lease)
        profile = state['profile']
        if (spec['kind'] != 'research-record/v1' or provider.mode != profile['mode']
                or provider.model != profile['model'] or canonical(profile['tools']) not in
                (canonical(TOOL_DEFINITIONS),canonical(DEVELOPMENT_TOOL_DEFINITIONS),
                 canonical(CONTEXT_TOOL_DEFINITIONS))):
            return blocked('Installed adapter or tools do not match the frozen research profile')
        if state['calls']:
            return blocked('Existing attempt transcript requires explicit reconciliation')
        sources = [client.call('read_artifact', lease=lease, artifact_id=ref)
                   for ref in claimed['context']['artifact_ids']]
        if profile.get('source_presentation') in PRESENTATION_PROFILES:
            sources = [source_view(source) for source in sources]
        messages = [{'role': 'system', 'content': profile['prompts'][spec['allowed_workers'][0]]},
                    {'role': 'user', 'content': canonical({'purpose': spec['purpose'], 'sources': sources})}]
        retries, ordinal = 0, 0
        while not cancelled():
            request = {'model': profile['model'], 'prompt_version': profile['prompt_version'],
                       'messages': messages, 'tools': profile['tools'],
                       'generation_parameters': profile['generation_parameters']}
            try:
                reservation = provider.reservation(request, profile['max_output_tokens'])
                if (type(reservation) is not dict or set(reservation) != {
                        'input_token_bound', 'output_token_limit', 'cost_bound_units'}):
                    raise Invalid('Malformed adapter reservation')
                if any(type(value) is not int or value < 0 for value in reservation.values()):
                    raise Invalid('Malformed adapter bounds')
            except Exception as exc:
                return blocked('Adapter reservation failed: ' + type(exc).__name__)
            intent = client.call('reserve_research_call', lease=lease, key='turn-' + str(ordinal),
                                 request=request, **reservation)
            if not intent['dispatch']:
                return blocked('Dispatch already reserved; reconcile its recorded outcome')
            result = _invoke(provider, request, ordinal, intent['deadline'] - time.time(), cancelled)
            receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'], **result)
            transcript.append(receipt['response_id'])
            if lost.is_set():
                return {'state': 'lease_lost', 'accepted': False, 'transcript_ids': transcript}
            if receipt['late']:
                try:return blocked('Provider response missed its frozen dispatch or epoch deadline')
                except ERRORS:return {'state':'reconciliation_required','accepted':False,'transcript_ids':transcript}
            if not receipt['within_reservation']:
                return blocked('Provider usage exceeded its reservation; epoch halted')
            ordinal += 1
            response = result['response']
            output = response.get('output')
            status = response.get('status')
            if status == 'completed' and type(output) is dict:
                status = output.get('status')
            messages.append({'role': 'assistant', 'content': canonical(response)})
            if status in ('failed', 'timeout') and retries < profile['max_retries'] and not cancelled():
                retries += 1
                continue
            if status == 'final' and type(output) is dict:
                record = output.get('record')
                if (type(record) is not dict or set(record) != {'kind', 'content', 'scope', 'source_refs'}
                        or record['kind'] not in ('idea', 'gap')):
                    return blocked('Final public output has no valid idea or retained gap')
                saved = client.call('record_research', lease=lease, **record)
                records.append(saved['id'])
                outcome = client.call('submit', lease=lease, artifact_id=saved['id'])
                return {**outcome, 'record_ids': records, 'transcript_ids': transcript,
                        'provider_mode': profile['mode'],
                        'genuine_discovery': False if profile['mode'] == 'fixture' else None}
            if status != 'tools' or type(output) is not dict:
                return blocked('Provider ended without a usable research record: ' + str(status)[:60])
            calls = output.get('calls')
            if type(calls) is not list or not 1 <= len(calls) <= 16:
                return blocked('Tool batch is malformed or exceeds 16 requests')
            identifiers = set()
            for call in calls:
                if cancelled():
                    return blocked('Research attempt cancelled')
                try:
                    if type(call) is not dict or type(call.get('id')) is not str or call['id'] in identifiers:
                        raise Invalid('Tool identifiers must be unique strings')
                    identifiers.add(call['id'])
                    value = _tool(client, lease, call, intent['call_id'], profile['tools'])
                    tool_result = {'status': 'ok', 'value': value}
                    if call['name'] == 'record_research':
                        records.append(value['id'])
                except ERRORS:
                    tool_result = {'status': 'tool_denied', 'reason': 'Unavailable or invalid request'}
                body = {'schema': 'provider-tool-result/1', 'call_id': intent['call_id'],
                        'tool_request': call, 'result': tool_result}
                stored = client.call('put_artifact', lease=lease, body=body, source_refs=[])
                transcript.append(stored['id'])
                visible = body
                if (profile.get('source_presentation') == TOOL_VIEW_PROFILE
                        and tool_result['status'] == 'ok' and call['name'] == 'measure_development'):
                    visible = {**body, 'result': {'status': 'ok', 'value': source_view(tool_result['value'])}}
                    view_record = client.call('put_artifact', lease=lease, source_refs=[stored['id']], body={
                        'schema': 'provider-tool-view/1', 'presentation_profile': TOOL_VIEW_PROFILE,
                        'source_tool_result_id': stored['id'], 'model_visible_body': visible})
                    transcript.append(view_record['id'])
                messages.append({'role': 'tool', 'content': canonical(visible)})
        return blocked('Research attempt cancelled')
    except ERRORS as exc:
        return blocked('Controller stopped research: ' + str(exc)[:240])
    finally:
        stopped.set()
        thread.join(client.timeout + 1)
