"""Static controller dispatch with the additional exact nested source closure.

All authorization, transaction, cancellation and settlement checks are preserved
from controller_providers.py. No global monkeypatch or worker-supplied adapter.
"""
import time
from ..codec import Invalid, canonical, decode, digest, text
from ..errors import Denied
from ..controller_providers import backend, source_hashes, _invoke

class BreakoutProviders:
    def _invoke_auxiliary_provider_external(self, token, args):
        from ..auxiliary import KINDS, request_for
        canonical(args)
        if set(args) != {'lease', 'key'}:
            raise Invalid('Only the current lease and dispatch key may be supplied')
        lease, key = args['lease'], text(args['key'], 'dispatch key')
        with self._transaction():
            actor = self._principal(token)
            job = self._owned(actor, lease)
            if actor['role'] != 'formalizer' or job['spec']['kind'] not in KINDS:
                raise Denied('Controller invocation requires a scoped auxiliary job')
            prior = self._db.execute('''SELECT id FROM research_calls
                WHERE job_id=? AND generation=? AND request_key=?''', (job['id'], job['generation'], key)).fetchone()
            if prior is not None:
                return self._invocation_result(prior['id'])
            self._check_feedback_context(self._context(job['spec']['context_id']))
            profile = self._effective_research_profile(job)
            if profile['mode'] != 'live' or profile['currency'] != 'USD':
                raise Denied('Direct invocation requires an explicit live USD epoch')
            route = self._provider_routes.get(profile['model'])
            if route is None:
                raise Denied('No operator-configured route for this exact model')
            parameter = 'openai_responses' if route['provider'] == 'openai' else 'anthropic_messages'
            if canonical(profile['generation_parameters']) != canonical({parameter: route['config']}):
                raise Invalid('Frozen generation settings differ from the exact controller route')
            _, adapter_class = backend(route['provider'])
            adapter = adapter_class(route['key_file'], route['budget_file'], route['config'],
                                    epoch_id=job['spec']['research_epoch_id'], worker=actor['name'])
            request = request_for(job['spec'], self._auxiliary_packet_for_spec(job['spec']))
            bounds = adapter.reservation(request, profile['max_output_tokens'])
            intent = self._reserve_research_call(actor, lease, key, request, **bounds)
            if not intent['dispatch']:
                raise Denied('Existing dispatch requires reconciliation')
            call_id = intent['call_id']
            adapter.run_id = 'controller-' + call_id
            call = self._db.execute('SELECT * FROM research_calls WHERE id=?', (call_id,)).fetchone()
            captured = {**source_hashes(route['provider']), **self._breakout_research_sources()}
            body = {'schema': 'provider-invocation-input/1', 'created_at': self._now(),
                    'call_id': call_id, 'request_id': call['request_id'], 'request_sha256': digest(request),
                    'provider': route['provider'], 'model': profile['model'], 'configuration': route['config'],
                    'adapter_run_id': adapter.run_id, 'adapter_ordinal': 0,
                    'units_per_usd': 1000000000, 'installed_sources': captured,
                    'scientific_readiness': False}
            saved = self._invocation_artifact(call, body, [call['request_id']])
            self._db.execute('INSERT INTO provider_invocations VALUES(?,?,NULL)', (call_id, saved['id']))
            self._event('controller', 'provider_invocation_admitted', call_id=call_id, input_id=saved['id'])

        def cancelled():
            with self._mutex:
                try:
                    self._owned(actor, lease)
                    return False
                except Denied:
                    return True

        # No SQLite transaction or registry mutex is held during network/process work.
        response = _invoke(adapter, request, 0, intent['deadline'] - time.time(), cancelled)
        try:
            unchanged = captured == {**source_hashes(route['provider']), **self._breakout_research_sources()}
        except (OSError, Denied, Invalid):
            unchanged = False
        with self._transaction():
            receipt = self._settle_research_call(actor, lease, call_id, **response)
            body = {'schema': 'provider-invocation/1', 'created_at': self._now(), 'call_id': call_id,
                    'input_id': saved['id'], 'request_id': call['request_id'], 'response_id': receipt['response_id'],
                    'execution_path': 'controller-direct-adapter/1', 'installed_sources_unchanged': unchanged,
                    'response_status': response['response'].get('status'), 'receipt': receipt,
                    'response_usable': (unchanged and not receipt['late'] and receipt['within_reservation']
                                        and receipt['accounting_valid'] and not receipt['usage_unknown']),
                    'scientific_readiness': False,
                    'qualification': 'The trusted local controller selected the installed direct adapter and retained its returned result. '
                        'Failed/preflight/cancelled calls are not successful model reviews. Local operator, installed code and OS remain trusted; '
                        'this is not remote attestation, semantic correctness, diverse thought or scientific approval.'}
            result = self._invocation_artifact(call, body, [saved['id'], receipt['response_id']])
            self._db.execute('UPDATE provider_invocations SET result_id=? WHERE call_id=?', (result['id'], call_id))
            self._event('controller', 'provider_invocation_recorded', call_id=call_id, result_id=result['id'])
            reply = self._invocation_result(call_id)
            canonical(reply)
            return reply
