"""Host-selected exact-count auxiliary path for frozen finite role settings."""
import time
from datetime import datetime, timezone

from ..auxiliary import KINDS, request_for
from ..codec import Invalid, canonical, digest, text
from ..controller_providers import _invoke, source_hashes
from ..errors import Denied
from ..openai_provider import MODEL, CountedOpenAIResponsesProvider, provider_identity, wire_request
from . import resources


def _capture(host, token, args):
    actor = host._principal(token)
    job = host._owned(actor, args['lease'])
    if actor['role'] != 'formalizer' or job['spec']['kind'] not in KINDS:
        raise Denied('Only a scoped downstream auxiliary job may invoke this path')
    epoch = host._epoch(job['spec']['research_epoch_id'])
    host._inquiry_epoch_current(epoch)
    host._check_feedback_context(host._context(job['spec']['context_id']))
    profile = host._effective_research_profile(job)
    index = resources._stage(epoch, job['spec'])
    config = resources._settings(profile, index)
    route = host._provider_routes.get(MODEL)
    if route is None or route['provider'] != 'openai':
        raise Denied('Only the installed direct OpenAI credential/shared-ledger route is available')
    # The role config is frozen by the operator, never supplied by this call or model.
    resources.inspect(host, epoch)
    request = request_for(job['spec'], host._auxiliary_packet_for_spec(job['spec']))
    return actor, job, epoch, profile, config, route, request


def invoke_auxiliary(host, token, args):
    canonical(args)
    if set(args) != {'lease', 'key'}:
        raise Invalid('Only the current lease and dispatch key may be supplied')
    text(args['key'], 'dispatch key')
    with host._mutex:
        captured = _capture(host, token, args)
        actor, job, epoch, profile, config, route, request = captured
        prior = host._db.execute('''SELECT id FROM research_calls
            WHERE job_id=? AND generation=? AND request_key=?''',
            (job['id'], job['generation'], args['key'])).fetchone()
        if prior is not None:
            return host._invocation_result(prior['id'])
        resources.preflight(host, epoch, job)
        adapter = CountedOpenAIResponsesProvider(route['key_file'], route['budget_file'], config,
                                                epoch_id=epoch['id'], worker=actor['name'])
        started = _count_record(host, captured, 'STARTED', adapter, key=args['key'])
    try:
        # Count the full wire without a registry transaction or mutex held.
        bounds = adapter.reservation(request, profile['max_output_tokens'])
        counted = _count_record(host, captured, 'OBSERVED', adapter, key=args['key'], attempt_id=started['id'])
        with host._transaction():
            fresh = _capture(host, token, args)
            if _fingerprint(fresh) != _fingerprint(captured):
                raise Denied('Lease, complete packet, frozen configuration or installed route changed while counting')
            prior = host._db.execute('''SELECT id FROM research_calls
                WHERE job_id=? AND generation=? AND request_key=?''',
                (job['id'], job['generation'], args['key'])).fetchone()
            if prior is not None:
                return host._invocation_result(prior['id'])
            resources.preflight(host, fresh[2], fresh[1])
            intent = host._reserve_research_call(actor, args['lease'], args['key'], request, **bounds)
            call_id = intent['call_id']
            adapter.run_id = 'controller-' + call_id
            call = host._db.execute('SELECT * FROM research_calls WHERE id=?', (call_id,)).fetchone()
            sources = source_hashes('openai')
            body = {'schema': 'provider-invocation-input/1', 'created_at': host._now(),
                    'call_id': call_id, 'request_id': call['request_id'], 'request_sha256': digest(request),
                    'provider': 'openai', 'model': MODEL, 'configuration': config,
                    'adapter_run_id': adapter.run_id, 'adapter_ordinal': 0,
                    'units_per_usd': 1000000000, 'installed_sources': sources,
                    'input_count_receipts': adapter.count_receipts, 'input_count_attempt_id': started['id'],
                    'input_count_observation_id': counted['id'], 'scientific_readiness': False}
            saved = host._invocation_artifact(call, body, [call['request_id'], started['id'], counted['id']])
            host._db.execute('INSERT INTO provider_invocations VALUES(?,?,NULL)', (call_id, saved['id']))
            host._event('controller', 'provider_invocation_admitted', call_id=call_id, input_id=saved['id'])
    except Exception as exc:
        # This transaction is deliberately separate from failed native admission.
        # A counted, late or source-stale attempt must not disappear on rollback.
        _count_record(host, captured, 'FAILED', adapter, key=args['key'], attempt_id=started['id'],
                      error_type=type(exc).__name__, halt=True)
        raise

    def cancelled():
        with host._mutex:
            try:
                host._owned(actor, args['lease'])
                return False
            except Denied:
                return True

    response = _invoke(adapter, request, 0, intent['deadline'] - time.time(), cancelled)
    try:
        unchanged = sources == source_hashes('openai')
    except OSError:
        unchanged = False
    with host._transaction():
        receipt = host._settle_research_call(actor, args['lease'], call_id, **response)
        body = {'schema': 'provider-invocation/1', 'created_at': host._now(), 'call_id': call_id,
                'input_id': saved['id'], 'request_id': call['request_id'], 'response_id': receipt['response_id'],
                'execution_path': 'controller-counted-inquiry-adapter/1',
                'installed_sources_unchanged': unchanged, 'response_status': response['response'].get('status'),
                'receipt': receipt,
                'response_usable': (unchanged and not receipt['late'] and receipt['within_reservation']
                                    and receipt['accounting_valid'] and not receipt['usage_unknown']
                                    and receipt.get('installed_sources_unchanged', False)
                                    and receipt.get('resource_settlement_verified', False)),
                'scientific_readiness': False,
                'qualification': 'Trusted local controller invocation and accounting only; no semantic or scientific certificate.'}
        result = host._invocation_artifact(call, body, [saved['id'], receipt['response_id']])
        host._db.execute('UPDATE provider_invocations SET result_id=? WHERE call_id=?', (result['id'], call_id))
        host._event('controller', 'provider_invocation_recorded', call_id=call_id, result_id=result['id'])
        return host._invocation_result(call_id)


def _fingerprint(captured):
    actor, job, epoch, profile, config, route, request = captured
    # Heartbeats may extend the same lease while counting; identity/ownership
    # is independently revalidated by _owned rather than comparing timestamps.
    return canonical({'actor': actor['name'], 'role': actor['role'], 'job_id': job['id'],
                      'generation': job['generation'], 'epoch_id': epoch['id'],
                      'profile': profile, 'configuration': config, 'route': route, 'request': request})


def _count_record(host, captured, state, adapter, *, key, attempt_id=None, error_type=None, halt=False):
    actor, job, epoch, profile, config, route, request = captured
    with host._transaction():
        if state == 'STARTED' and host._db.execute(
                "SELECT 1 FROM artifacts WHERE json_extract(envelope,'$.job_id')=? "
                "AND json_extract(envelope,'$.generation')=? "
                "AND json_extract(envelope,'$.body.schema')='inquiry-input-count-attempt/1' "
                "AND json_extract(envelope,'$.body.state')='STARTED'", (job['id'], job['generation'])).fetchone():
            raise Denied('The single count attempt already started; reconcile without another count')
        context = host._context(job['spec']['context_id'])
        refs = sorted(set(context['artifact_ids']) | ({attempt_id} if attempt_id else set()))
        body = {'schema': 'inquiry-input-count-attempt/1', 'state': state, 'dispatch_key': key,
                'epoch_id': epoch['id'], 'attempt_id': attempt_id, 'error_type': error_type,
                'at_utc': datetime.now(timezone.utc).isoformat(), 'model_identity': provider_identity(),
                'request_sha256': digest(request), 'wire_sha256': digest(wire_request(request, config)),
                'count_receipts': adapter.count_receipts, 'inference_dispatched': False,
                'billing': 'UNVERIFIED_COUNT_SERVICE_NOT_INFERENCE_USAGE', 'scientific_readiness': False}
        if state == 'STARTED':
            body['request'] = request
        saved = host._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'job_id': job['id'], 'generation': job['generation'],
            'exposed_to': actor['name'], 'context_id': context['id'], 'data_class': 'work_product',
            'body': body, 'source_refs': refs, 'exposure': sorted(set(context['exposure']) | set(refs)),
            'authority': 'operational_count_attempt_not_inference_or_scientific_evidence'})
        if halt:
            host._db.execute("UPDATE research_epochs SET state='halted' WHERE id=?", (epoch['id'],))
        host._event('controller', 'inquiry_input_count_attempt_recorded', artifact_id=saved['id'], state=state)
        return saved
