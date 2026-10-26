"""Host-owned auxiliary dispatch. Trusts the local operator, installed code and OS.

No worker-supplied response, route label or historical ledger entry can create
this execution record. This is invocation provenance, not semantic certification.
"""
import hashlib
from pathlib import Path
import time

from .codec import Invalid, canonical, decode, digest, text
from .errors import Denied


def _invoke(*args):
    from .researcher import _invoke as invoke
    return invoke(*args)


def backend(name):
    if name == 'openai':
        from . import openai_provider as module
        return module, module.OpenAIResponsesProvider
    if name == 'anthropic':
        from . import anthropic_provider as module
        return module, module.AnthropicMessagesProvider
    raise Invalid('Only installed direct provider adapters are available')


def routes(value):
    if value is None:
        return {}
    if type(value) is not dict or len(value) > 2:
        raise Invalid('Expected at most two explicit controller provider routes')
    result = {}
    for model, route in value.items():
        if type(route) is not dict or set(route) != {'provider', 'key_file', 'budget_file', 'config'}:
            raise Invalid('Exact local provider route required')
        module, _ = backend(route['provider'])
        if model != module.MODEL:
            raise Invalid('Route must bind the exact installed model')
        module._config(route['config'])
        result[model] = {**route, 'key_file': str(Path(route['key_file']).resolve()),
                        'budget_file': str(Path(route['budget_file']).resolve())}
    # Neither caller dictionary mutation nor a supplied adapter object changes a route.
    return decode(canonical(result))


def source_hashes(provider):
    # Observed installed-source fingerprints, not a cryptographic remote attestation.
    names = {'controller_providers.py', 'researcher.py', 'research_calls.py',
             'codec.py', 'openai_provider.py', 'provider_usage.py', 'coordination.py',
             'auxiliary.py', 'storage.py', 'memory.py', 'server.py', 'errors.py'}
    if provider == 'anthropic':
        names.add('anthropic_provider.py')
    root = Path(__file__).parent
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in sorted(names)}


class ControllerProviders:
    def _initialize_controller_providers(self, existing):
        if self._db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='provider_invocations'").fetchone():
            return
        if existing:
            self._preserve_schema_checkpoint('before-controller-providers-v1.sqlite3')
        with self._transaction():
            self._db.execute('''CREATE TABLE provider_invocations(
                call_id TEXT PRIMARY KEY REFERENCES research_calls(id),
                input_id TEXT NOT NULL REFERENCES artifacts(id),
                result_id TEXT REFERENCES artifacts(id))''')
            self._db.execute('''CREATE TRIGGER immutable_provider_invocation_identity
                BEFORE UPDATE OF call_id,input_id ON provider_invocations
                BEGIN SELECT RAISE(ABORT,'immutable invocation identity'); END''')
            self._db.execute('''CREATE TRIGGER immutable_provider_invocation_result
                BEFORE UPDATE OF result_id ON provider_invocations WHEN OLD.result_id IS NOT NULL
                BEGIN SELECT RAISE(ABORT,'immutable invocation result'); END''')
            self._db.execute('''CREATE TRIGGER immutable_provider_invocation_delete
                BEFORE DELETE ON provider_invocations
                BEGIN SELECT RAISE(ABORT,'retained invocation history'); END''')

    def _invocation_artifact(self, call, body, refs):
        request = self._artifact(call['request_id'])
        return self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'job_id': call['job_id'], 'generation': call['generation'],
            'exposed_to': call['owner'], 'context_id': request['context_id'], 'data_class': 'work_product',
            'body': body, 'source_refs': refs,
            'exposure': sorted(set(request['exposure']) | set(refs)),
            'authority': 'invocation_provenance_not_scientific_evidence'})

    def _invocation_result(self, call_id):
        row = self._db.execute('SELECT * FROM provider_invocations WHERE call_id=?', (call_id,)).fetchone()
        if row is None:
            raise Denied('A worker-owned call cannot acquire controller dispatch provenance')
        if row['result_id'] is None:
            return {'state': 'unresolved', 'call_id': call_id, 'input_id': row['input_id']}
        call = self._db.execute('SELECT * FROM research_calls WHERE id=?', (call_id,)).fetchone()
        if self._artifact(row['result_id'])['body']['response_usable'] is not True:
            return {'state': 'unusable', 'call_id': call_id, 'invocation_id': row['result_id'],
                    'receipt': decode(call['receipt'])}
        retained = self._artifact(call['response_id'])['body']
        return {'state': 'recorded', 'receipt': decode(call['receipt']),
                'invocation_id': row['result_id'], 'response': retained['response'], 'usage': retained['usage']}

    def _invoke_auxiliary_provider_external(self, token, args):
        from .auxiliary import KINDS, request_for
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
            captured = source_hashes(route['provider'])
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
            unchanged = captured == source_hashes(route['provider'])
        except OSError:
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
