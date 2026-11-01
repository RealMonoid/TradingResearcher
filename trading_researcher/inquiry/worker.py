"""Opt-in static inquiry worker; actual requests are retained before dispatch.

The legacy loop is preserved with explicit presentation/tool/source gates.
No provider-side rewrite, monkeypatch or runtime code generation is used.
"""
import threading
import time
from datetime import datetime, timezone

from ..codec import Invalid, canonical, digest, text
from ..errors import Denied
from ..researcher import ERRORS, _invoke, _tool as legacy_tool
from ..feedback.inline_bodies import SCHEMA, read_ancestry
from ..feedback.reference_views import REFERENCE_TOOL, read_references, source_view
from .presentation import TOOLS, current_sources, initial_messages


def _tool(client, lease, call, provider_call_id=None, tools=None):
    if type(call) is not dict or set(call) != {'id', 'name', 'arguments'}:
        raise Invalid('Malformed inquiry tool request')
    text(call['id'], 'tool call id')
    if canonical(tools) != canonical(TOOLS):
        raise Denied('Exact inquiry tools required')
    current_sources()
    if call['name'] == REFERENCE_TOOL['name']:
        return read_references(client, lease, call['arguments'])
    if call['name'] == 'read_feedback_ancestry_references':
        return read_ancestry(client, lease, call['arguments'])
    result = legacy_tool(client, lease, call, provider_call_id, tools)
    if call['name'] == 'capabilities':
        result.update(version='research-tools/5', paired_reference_sections=True,
                      feedback_ancestry_sections=True, inline_record_bodies=True)
    return result


# Static loop source: 6404fbf66334a13112a67871977e212ef27dac93b8cf2da94933d8a667867abc
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
        retained = {'accepted': False, 'record_ids': records, 'transcript_ids': transcript,
                    'scientific_authority': False, 'genuine_discovery': False,
                    'input_count_receipts': getattr(provider, 'count_receipts', [])}
        if lost.is_set():
            return {'state': 'lease_lost', **retained}
        try:
            result = client.call('block', lease=lease, reason=reason,
                                 needs=['research continuation'],
                                 retry_when='The recorded cause is resolved within the original budgets')
        except ERRORS:
            # No stale capability write or lease revival. The operator must retain
            # the returned observations when the last authorized write was STARTED.
            return {'state': 'reconciliation_required', 'reason': reason, **retained}
        return {**result, **retained}

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
        finite = state.get('finite_resource')
        if finite and getattr(provider, 'run_id', None) != finite['discovery_run_id']:
            return blocked('Provider run identity differs from the frozen single-use discovery slot')
        if (spec['kind'] != 'research-record/v1' or provider.mode != profile['mode']
                or provider.model != profile['model'] or profile.get('source_presentation') != SCHEMA
                or canonical(profile['tools']) != canonical(TOOLS)):
            return blocked('Installed inquiry worker or tools differ from the frozen profile')
        installed = state.get('inquiry_runtime', {}).get('installed_sources', {})
        if any(installed.get(name) != value for name, value in current_sources().items()):
            return blocked('Inquiry worker and controller source bindings differ')
        if state['calls']:
            return blocked('Existing attempt transcript requires explicit reconciliation')
        sources = [client.call('read_artifact', lease=lease, artifact_id=ref)
                   for ref in claimed['context']['artifact_ids']]
        messages = initial_messages(profile, spec['allowed_workers'][0], spec['purpose'], sources)
        retries, ordinal = 0, 0
        while not cancelled():
            current_sources()
            if finite:
                if ordinal >= finite['max_calls_per_job']:
                    return blocked('The single-use finite discovery slot permits no successor count or call')
                client.call('research_call_state', lease=lease)
            request = {'model': profile['model'], 'prompt_version': profile['prompt_version'],
                       'messages': messages, 'tools': profile['tools'],
                       'generation_parameters': profile['generation_parameters']}
            def retain_count(state, error_type=None):
                if finite and hasattr(provider, 'count_receipts'):
                    stored = client.call('put_artifact', lease=lease, source_refs=[], body={
                        'schema': 'inquiry-discovery-count-attempt/1', 'state': state,
                        'at_utc': datetime.now(timezone.utc).isoformat(),
                        'request': request, 'request_sha256': digest(request),
                        'error_type': error_type, 'count_receipts': provider.count_receipts,
                        'billing': 'UNVERIFIED_COUNT_SERVICE_NOT_INFERENCE_USAGE',
                        'inference_dispatched': False, 'scientific_readiness': False})
                    transcript.append(stored['id'])
            try:
                retain_count('STARTED')
                reservation = provider.reservation(request, profile['max_output_tokens'])
                if (type(reservation) is not dict or set(reservation) != {
                        'input_token_bound', 'output_token_limit', 'cost_bound_units'}):
                    raise Invalid('Malformed adapter reservation')
                if any(type(value) is not int or value < 0 for value in reservation.values()):
                    raise Invalid('Malformed adapter bounds')
                retain_count('OBSERVED')
            except Exception as exc:
                try:
                    retain_count('FAILED', type(exc).__name__)
                except ERRORS:
                    pass  # The durable start and returned receipts retain an unresolved count.
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
            if not receipt.get('installed_sources_unchanged', False):
                return blocked('Inquiry sources changed during dispatch; response and usage retained')
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
                        'input_count_receipts': getattr(provider, 'count_receipts', []),
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
                if tool_result['status'] == 'ok' and call['name'] == 'measure_development':
                    visible = {**body, 'result': {'status': 'ok', 'value': source_view(tool_result['value'])}}
                    view_record = client.call('put_artifact', lease=lease, source_refs=[stored['id']], body={
                        'schema': 'provider-tool-view/1', 'presentation_profile': profile['source_presentation'],
                        'source_tool_result_id': stored['id'], 'model_visible_body': visible})
                    transcript.append(view_record['id'])
                messages.append({'role': 'tool', 'content': canonical(visible)})
        return blocked('Research attempt cancelled')
    except ERRORS as exc:
        return blocked('Controller stopped research: ' + str(exc)[:240])
    finally:
        stopped.set()
        thread.join(client.timeout + 1)
