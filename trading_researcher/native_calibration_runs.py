"""Operator-owned native resource custody using the existing Registry.

This owner does not accept model verdicts or admit a numerical final series.
Controlled numerical work and its classifier belong to the consuming runner.
Retired Scalar records are read solely as financial history, never scheduled.
"""
import hashlib
import math
import time
from types import MappingProxyType

from .binding import require
from .calibration_recovery import CalibrationRecovery
from .codec import Invalid, canonical, decode, digest, integer, text
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .native_calibration_resources import (
    NativeResourceHistory, POOL, INVENTORY, GRANT, AUTHORITY, RESULT_SCHEMAS,
    RESULT_AUTHORITIES, MAX_COMPUTE_MS, MAX_STORAGE_BYTES, META)


LOADED_SOURCE = footprint(source_bundle())
AUTHORITY_FILES = {
    'native': ('native-parallel-calibration-approval-2026-11-03.json',
               '9c28969e7078bba1dbd22b30d6746b3c1c7badb71d5ad36fa88a5076760123c3'),
    'original': ('calibration-resource-approval-2026-11-02.json',
                 '0b0475cab83f5d0c839ee2de9afba67a3b83eb5eb933ca583e251ceead20647a'),
    'proposal': ('native-calibration-proposal-revision-5-2026-11-03.source',
                 '0995cf21a7278a8f72cfc05fa12b16160327b2ee27c5b3206aa9bd6ef7ad2b05')}
SETUP_NAMES = ('controller_source', 'runtime_retain', 'runtime_qualification',
               'acceptance_summary', 'prepare_final_input', 'prepared_copies', 'terminal_copies')

# These reviewed versions give caller_cancelled its narrow meaning here: the
# family caller supplies a time-only callback. Other callers/reasons acquire no
# clock authority. Requalification alone must not broaden that interpretation.
CALCULATOR_CLOCK_SOURCE = MappingProxyType({
    'trading_researcher/study_pipeline.py':
        '2d8b00d6f4f3c5e52ae0f1569b0ad4f7bfef628943dab0e5107385ed73fbb8de',
    'trading_researcher/family_pipeline.py':
        'c082918d76595f15a89c4607578c526eb5354619deccf7e991d9319d9095c0bb',
    'trading_researcher/stationary_bootstrap.py':
        'f6f1b27ca43acde60972caa3af2fbec082e324180b13cb60f4fb64142dfd8d57'})


class AttemptDeadlineExceeded(Invalid):
    """This parent's whole-attempt clock elapsed, outside a running child."""


class AuthenticatedCalculatorDeadline(Invalid):
    """An authenticated generation used the pinned calculator's time stop."""


def _validate_native_calculation(result, manifest, world):
    from . import family_study
    require(type(result) is dict and result.get('schema') == 'development-family-computation/1'
            and result.get('world_id') == world['id']
            and result.get('scientific_readiness') is False
            and result.get('classification_permitted') is False
            and 'n_min' in result and result['n_min'] is None,
            'Native calculation identity or authority differs')
    expected = family_study.outcome_record(manifest, world, result['outcomes'])
    require(canonical(result['outcome']) == canonical(expected), 'Native calculation outcome differs')
    family_study.summarize(manifest, [expected])


def _authenticated_inner_clock(source, result):
    if (result['outcome']['state'] != 'TECHNICAL_FAILURE'
            or any(name not in source or hashlib.sha256(source[name]).hexdigest() != expected
                   for name, expected in CALCULATOR_CLOCK_SOURCE.items())):
        return False
    bootstraps = result.get('bootstraps')
    if type(bootstraps) is not list:
        return False
    outcomes = {item['id']: item for item in result['outcomes']}
    if len(bootstraps) != len(outcomes) or {item['id'] for item in bootstraps} != set(outcomes):
        return False
    clock = False
    for item in bootstraps:
        value, outcome = item['result'], outcomes[item['id']]
        if outcome['state'] == 'TECHNICAL_FAILURE':
            if (value.get('status') != 'RESOURCE_STOP'
                    or value.get('reason') not in ('caller_cancelled', 'computation_time_limit')):
                return False
            clock = True
        elif value.get('status') == 'COMPUTED_UNCALIBRATED':
            if outcome['state'] != 'VERIFIED':
                return False
        elif (value.get('status') == 'INFORMATION_GAP' or value.get('status') == 'INPUT_GAP'
              and value.get('reason') in ('no_scope_cases', 'no_conditioned_cases')):
            if outcome['state'] != 'INFORMATION_GAP':
                return False
        else:
            return False
    return clock


class NativeCalibrationResources:
    """Short atomic Registry operations; no child waits under SQL transactions."""
    def __init__(self, broker):
        self.broker = broker
        with broker._mutex:
            if not hasattr(broker, '_native_calibration_active'):
                broker._native_calibration_active = set()

    def _read_authority(self):
        from pathlib import Path
        directory = Path(__file__).resolve().parents[1] / 'docs/reviews/implementation-2026-10-25'
        texts, hashes = {}, {}
        for key, (name, expected) in AUTHORITY_FILES.items():
            raw = (directory / name).read_bytes()
            require(hashlib.sha256(raw).hexdigest() == expected, 'Pinned native calibration authority bytes differ')
            texts[key], hashes[key] = raw.decode('utf-8'), expected
        native, original = decode(texts['native']), decode(texts['original'])
        require(native['schema'] == 'native-parallel-calibration-approval/1' and native['decision'] == 'D100'
                and original['schema'] == 'conditional-calibration-resource-approval/1'
                and native['resources']['existing_compute_aggregate_ms'] == MAX_COMPUTE_MS
                and native['resources']['existing_logical_aggregate_bytes'] == MAX_STORAGE_BYTES
                and original['limits']['aggregate_compute_ms'] == MAX_COMPUTE_MS
                and original['limits']['aggregate_logical_bytes'] == MAX_STORAGE_BYTES
                and original['limits']['additional_grants_max'] == 179
                and native['scope']['worlds_total'] == 2048
                and native['scope']['max_parallel_world_workers'] == 6,
                'Supported bounded native replacement authority required')
        return {'native': native, 'original': original, 'texts': texts, 'hashes': hashes}

    def _retired_carry(self, authority):
        """Reuse the unchanged, source-independent retired financial parser only."""
        b = self.broker
        expected = authority['native']['retired_scalar_state']
        amendment = b._artifact(expected['prepared_amendment_id'])
        input_record = b._artifact(amendment['body']['input_id'])
        binding = {**input_record['body']['binding_scope'], 'registry_path': str(b.directory)}
        reader = CalibrationRecovery(b, binding)
        reader._owned(input_record['id'], 'calibration-recovery-input/1')
        reader._owned(amendment['id'], 'calibration-recovery-amendment/1')
        state = reader._history(input_record, amendment)
        base, original = state['base'], state['base']['history']
        require(base['study']['id'] == expected['study_id']
                and amendment['body']['study_id'] == expected['study_id']
                and len(base['study']['body']['manifest']['worlds']) == authority['native']['scope']['worlds_total'],
                'Retired financial study differs from its native replacement authority')
        require(state['setup_complete'] and not state['pending'] and not state['unknown']
                and not state['orphan'] and not state['failure'] and not state['overrun'],
                'Retired financial setup or resource use is unresolved')
        require(state['results'] == input_record['body']['original_attempt_ids']
                and [g['id'] for g in state['grants']] == input_record['body']['original_continuation_ids']
                and not any(e['action'] in ('calibration_recovery_reserved', 'calibration_recovery_settled',
                                            'calibration_recovery_continued') for e in reader._events()),
                'Retired Scalar execution or allocation changed after its prepared prefix')
        verified = sum(row['state'] == 'VERIFIED' for row in original.records.values())
        require(len(original.reservations) == len(original.settlements) == expected['old_attempts']
                and verified == expected['verified_worlds'] and len(original.grants) == expected['old_grants']
                and state['compute'] == expected['known_compute_ms']
                and state['storage'] == expected['known_logical_bytes_after_setup']
                and input_record['body']['setup_storage_bytes'] == expected['setup_fee_bytes_retained'],
                'Retained native carry charges or grant inventory differ')
        carry = {'schema': 'native-calibration-resource-carry/1', 'basis_id': amendment['id'],
                 'charged_compute_ms': state['compute'], 'charged_storage_bytes': state['storage'],
                 'allocated_compute_ms': state['max_compute'], 'allocated_storage_bytes': state['max_storage'],
                 'grants_used': len(state['grants']),
                 'progress_units': sum(row['state'] in ('VERIFIED', 'INFORMATION_GAP') for row in original.records.values()),
                 'last_grant_progress': original.last_completed, 'no_progress_grants': original.no_progress}
        refs = sorted({base['study']['id'], input_record['id'], amendment['id'], *[g['id'] for g in original.grants]})
        exposure = set(refs)
        for identity in refs:
            exposure.update(b._artifact(identity)['exposure'])
        return {'carry': carry, 'source_refs': refs, 'exposure': sorted(exposure),
                'original_checkpoint': original.checkpoint, 'prepared_checkpoint': state['checkpoint']}

    def _pool(self, identity):
        item = self.broker._artifact(identity)
        # The same constructor validates every historical pool before replay.
        NativeResourceHistory(item)
        return item

    def _objects(self, schema):
        return [self.broker._artifact(row[0]) for row in self.broker._db.execute(
            "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=? "
            "AND json_extract(envelope,'$.creator')='controller' AND json_extract(envelope,'$.origin')='controller'",
            (schema,))]

    def _history(self, pool):
        history = NativeResourceHistory(pool)
        for row in self.broker._db.execute('SELECT envelope FROM events ORDER BY seq'):
            history.apply(decode(row[0]), self.broker._artifact)
        return history

    def _current(self, pool):
        require(pool['body']['source_footprint'] == LOADED_SOURCE == footprint(source_bundle()),
                'Native resource controller source differs; no new work')
        authority = self._read_authority()
        require(pool['body']['approval_hashes'] == authority['hashes'], 'Native resource authority differs')
        self.broker._require_usable_dependencies(pool['id'])

    def _save(self, schema, body, refs, *, authority=AUTHORITY, blobs=()):
        refs = sorted(set(refs))
        exposure = set(refs)
        for identity in refs:
            exposure.update(self.broker._artifact(identity)['exposure'])
        return self.broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'data_class': 'operations', 'authority': authority,
            'source_refs': refs, 'exposure': sorted(exposure), 'blob_refs': sorted(set(blobs)),
            'body': {'schema': schema, 'created_at': self.broker._now(), **body, 'scientific_readiness': False}})

    def _event(self, action, pool_id, **details):
        self.broker._event('controller', action, pool_id=pool_id, **details)

    def prepare(self, token, args):
        b = self.broker
        with b._transaction():
            b._binding_owner(token)
            require(type(args) is dict and set(args) == {'key'}, 'Exact native pool preparation required')
            key = text(args['key'], 'Native pool key')
            for row in b._db.execute('SELECT envelope FROM events ORDER BY seq'):
                event = decode(row[0])
                if event['actor'] == 'controller' and event['action'] == 'native_calibration_pool_key':
                    if event['details']['key'] == key:
                        return self._pool(event['details']['pool_id'])
            authority = self._read_authority()
            retired = self._retired_carry(authority)
            identity = digest({'schema': 'native-calibration-pool-identity/1',
                               'approval': authority['hashes']['native'],
                               'study': authority['native']['retired_scalar_state']['study_id'],
                               'original_checkpoint': retired['original_checkpoint']})
            matches = [p for p in self._objects(POOL) if p['body'].get('identity') == identity]
            require(len(matches) <= 1, 'Duplicate native resource pools for the same authority')
            if matches:
                pool = matches[0]
                self._current(pool)
            else:
                require(LOADED_SOURCE == footprint(source_bundle()),
                        'Native pool preparation source changed since import')
                tasks = {name: digest({'pool_identity': identity, 'setup': name}) for name in SETUP_NAMES}
                body = {'identity': identity, 'carry': retired['carry'], 'max_parallel': 6,
                        'source_footprint': LOADED_SOURCE, 'approval_texts': authority['texts'],
                        'approval_hashes': authority['hashes'], 'setup_tasks': tasks,
                        'retired_checkpoints': {k: retired[k] for k in ('original_checkpoint', 'prepared_checkpoint')},
                        'accounting': 'Retired carry plus owned new inventory/grant metadata and attempt charges. '
                                      'Initial 1MiB setup-inventory tariff covers bounded pool/authority/setup metadata; '
                                      'preparation inspection/final commit are outside attempt elapsed metering.'}
                require(len(canonical(body).encode()) < META, 'Native pool metadata exceeds its setup tariff')
                pool = self._save(POOL, body, retired['source_refs'])
                history = NativeResourceHistory(pool)
                request = {'key': 'native-setup-' + pool['id'], 'pool_id': pool['id'], 'phase': 'setup',
                           'task_ids': sorted(tasks.values()), 'execution_deadline_ms': 600000,
                           'attempt_compute_ms': 630000, 'attempt_storage_bytes': 268435456,
                           'max_attempts': 1, 'expected_checkpoint': history.checkpoint}
                self._bind_locked(pool, history, request)
            self._event('native_calibration_pool_key', pool['id'], key=key)
            return pool

    def inspect(self, token, pool_id):
        with self.broker._mutex:
            self.broker._binding_owner(token)
            pool = self._pool(pool_id)
            history = self._history(pool)
            return {'pool_id': pool_id, 'budget': history.budget(), 'resource_checkpoint': history.checkpoint,
                    'inventories': {phase: item['id'] for phase, item in history.inventories.items()},
                    'scientific_readiness': False}

    def _bind_locked(self, pool, history, request, input_id=None):
        history.inventory_terms(request)
        refs, extra = [pool['id']], {}
        if request['phase'] == 'final':
            require(input_id is not None, 'Final native inventory requires its owned input')
            from .native_study_runs import NativeFamilyCalibrationStudies
            study = NativeFamilyCalibrationStudies(self.broker)._study(input_id)
            self.broker._require_usable_dependencies(input_id)
            require(request['task_ids'] == sorted(w['id'] for w in study['body']['manifest']['worlds']),
                    'Native final task inventory differs from its reserved worlds')
            refs.append(input_id)
            extra['input_id'] = input_id
        else:
            require(input_id is None, 'Only a final task inventory binds a native final input')
        item = self._save(INVENTORY, {'request': request, **extra}, refs)
        self._event('native_calibration_inventory_bound', pool['id'], artifact_id=item['id'])
        self._history(pool).budget()
        return item

    def bind_inventory(self, token, request, *, input_id=None):
        with self.broker._transaction():
            self.broker._binding_owner(token)
            request = decode(canonical(request))
            for item in self._objects(INVENTORY):
                old = item['body']['request']
                if old.get('pool_id') == request.get('pool_id') and old.get('key') == request.get('key'):
                    if canonical(old) != canonical(request) or item['body'].get('input_id') != input_id:
                        raise Conflict('Native inventory key already binds its original request')
                    return item
            pool = self._pool(request['pool_id'])
            self._current(pool)
            return self._bind_locked(pool, self._history(pool), request, input_id)

    def reserve(self, token, request):
        b = self.broker
        added = False
        try:
            with b._transaction():
                b._binding_owner(token)
                request = decode(canonical(request))
                pool = self._pool(request['pool_id'])
                self._current(pool)
                history = self._history(pool)
                terms = history.reservation_terms(request)
                b._require_usable_dependencies(terms['inventory_id'])
                self._event('native_calibration_reserved', pool['id'], reservation=terms)
                b._event('controller', 'bound_computation_started', attempt_id=terms['attempt_id'],
                         kind='native_calibration_' + terms['phase'], input_ref=pool['id'], retained_input_id=pool['id'])
                self._history(pool).budget()
                b._native_calibration_active.add(terms['attempt_id'])
                added = True
        except BaseException:
            if added:
                b._native_calibration_active.discard(terms['attempt_id'])
            raise
        return terms

    @staticmethod
    def _failed(body, exc):
        failure = {'type': type(exc).__name__, 'message': str(exc)[:2000]}
        failures = list(body.get('failures', []))
        if body.get('failure') is not None and body['failure'] not in failures:
            failures.append(body['failure'])
        failures.append(failure)
        body.update(resource_state='FAILED', currency_checked=False,
                    failure=body.get('failure') or failure, failures=failures)

    def _settle_locked(self, pool, body, source_refs, descriptors, *, orphan=False):
        b = self.broker
        history = self._history(pool)
        attempt = body['attempt_id']
        require(attempt in history.pending, 'Native result is stale or already settled')
        reservation = history.pending[attempt]
        phase = reservation['phase']
        require(body['phase'] == phase and body['task_id'] == reservation['task_id'], 'Native result task differs')
        for key, expected in (('schema', RESULT_SCHEMAS[phase]), ('resource_pool_id', pool['id']),
                              ('resource_inventory_id', reservation['inventory_id']), ('scientific_readiness', False)):
            require(key not in body or canonical(body[key]) == canonical(expected), 'Native result overrides owned custody')
            body[key] = expected
        body.setdefault('created_at', b._now())
        body.setdefault('technical_refs', [])
        refs = [pool['id'], reservation['inventory_id'], *source_refs, *body['technical_refs']]
        inventory = history.inventories[phase]
        if phase == 'final':
            require(body.get('study_id') == inventory['body']['input_id'], 'Native result final input differs')
            refs.append(body['study_id'])
        if not orphan:
            try:
                self._current(pool)
                b._require_usable_dependencies(reservation['inventory_id'])
                for identity in body['technical_refs']:
                    b._require_usable_dependencies(identity)
            except (Invalid, Conflict, Denied, OSError) as exc:
                self._failed(body, exc)
            item = body['settlement']
            if item['usage_known'] is False:
                self._failed(body, Invalid('Native attempt resource usage is unknown'))
            if (integer(item['compute_ms'], 'Native compute') > reservation['compute_ms']
                    or integer(item['storage_bytes'], 'Native storage') > reservation['storage_bytes']):
                self._failed(body, Invalid('Observed native work exceeded its full reservation'))
        for descriptor in descriptors:
            b._register_blob(descriptor)
        item = self._save(RESULT_SCHEMAS[phase], body, refs, authority=RESULT_AUTHORITIES[phase],
                          blobs=[d['sha256'] for d in descriptors])
        self._event('native_calibration_settled', pool['id'], artifact_id=item['id'])
        b._event('controller', 'bound_computation_checked', attempt_id=attempt,
                 artifact_id=item['id'], status=body['resource_state'])
        self._history(pool).budget()
        return item

    def settle(self, token, pool_id, body, *, source_refs=(), blob_refs=()):
        b = self.broker
        with b._transaction():
            b._binding_owner(token)
            pool = self._pool(pool_id)
            item = self._settle_locked(pool, decode(canonical(body)), source_refs, blob_refs)
        b._native_calibration_active.discard(item['body']['attempt_id'])
        return item

    def continue_pool(self, token, request):
        with self.broker._transaction():
            self.broker._binding_owner(token)
            request = decode(canonical(request))
            for item in self._objects(GRANT):
                old = item['body']['request']
                if old.get('pool_id') == request.get('pool_id') and old.get('key') == request.get('key'):
                    if canonical(old) != canonical(request):
                        raise Conflict('Native continuation key already binds its original request')
                    return item
            pool = self._pool(request['pool_id'])
            self._current(pool)
            history = self._history(pool)
            terms = history.continuation_terms(request)
            self.broker._require_usable_dependencies(history.inventories[request['phase']]['id'])
            refs = [pool['id']] + ([terms['previous_continuation_id']] if terms['previous_continuation_id'] else [])
            item = self._save(GRANT, {'request': request, 'terms': terms}, refs)
            self._event('native_calibration_continued', pool['id'], artifact_id=item['id'])
            self._history(pool).budget()
            return item

    def stop(self, token, pool_id, reason):
        with self.broker._transaction():
            self.broker._binding_owner(token)
            pool = self._pool(pool_id)
            reason = text(reason, 'Native stop reason')
            history = self._history(pool)
            if reason not in history.halt_reasons:
                self._event('native_calibration_stopped', pool_id, reason=reason)
        return self.inspect(token, pool_id)

    def recover(self):
        """Inherited pending work is uncertain; never infer a replacement grant."""
        b = self.broker
        with b._transaction():
            for pool in self._objects(POOL):
                history = self._history(pool)
                pending = [r for a, r in history.pending.items() if a not in b._native_calibration_active]
                for reservation in pending:
                    phase, task = reservation['phase'], reservation['task_id']
                    failure = {'type': 'OrphanUncertain', 'message': 'Native attempt survived a controller boundary without settlement'}
                    body = {'resource_pool_id': pool['id'], 'phase': phase, 'task_id': task,
                            'attempt_id': reservation['attempt_id'],
                            'settlement': {'attempt_id': reservation['attempt_id'], 'compute_ms': 0,
                                           'storage_bytes': 0, 'usage_known': False},
                            'resource_state': 'ORPHAN_UNCERTAIN', 'currency_checked': False,
                            'failure': failure, 'failures': [failure], 'output_blobs': {}}
                    if phase == 'final':
                        from .family_study import outcome_record
                        study_id = history.inventories[phase]['body']['input_id']
                        study = b._artifact(study_id)
                        world = next(w for w in study['body']['manifest']['worlds'] if w['id'] == task)
                        body.update(study_id=study_id, world_id=task, result=None, proofs=[],
                                    outcome=outcome_record(study['body']['manifest'], world, failed=True))
                    self._settle_locked(pool, body, (), (), orphan=True)


class NativeCalibrationAttempts:
    """Host-only numerical consumer of already reserved final tasks.

    This is not a Broker RPC or a series-admission API. The consuming controller
    still owes fixed reference acceptance, pinned-host/source/copy/capacity
    admission and monitoring before actual final use. No caller supplies a
    numerical verdict, resource amount, seed or readiness flag here.
    """
    def __init__(self, broker):
        from .native_study_runs import NativeFamilyCalibrationStudies
        self.broker = broker
        self.resources = NativeCalibrationResources(broker)
        self.runner = NativeFamilyCalibrationStudies(broker)
        with broker._mutex:
            if not hasattr(broker, '_native_calibration_dispatched'):
                broker._native_calibration_dispatched = set()

    @staticmethod
    def _failure(exc):
        return {'type': type(exc).__name__, 'message': str(exc)[:2000]}

    def _retry_origin(self, prior, binding):
        """Bookkeeping clock labels alone are not numerical retry authority."""
        if prior is None:
            return
        old = prior.get('body', {})
        require(prior.get('creator') == prior.get('origin') == 'controller'
                and prior.get('authority') == RESULT_AUTHORITIES['final']
                and old.get('schema') == RESULT_SCHEMAS['final']
                and old.get('numerical_caller') == 'native-reserved-calculation/1'
                and old.get('phase') == 'final'
                and old.get('world_id') == old.get('task_id') == binding['world_id']
                and old.get('resource_state') == 'KNOWN_TIMEOUT'
                and old.get('currency_checked') is True
                and old.get('settlement', {}).get('usage_known') is True
                and old.get('failure') is not None
                and old.get('failures') == [old['failure']],
                'Retry predecessor is not an owned numerical clock result')
        dispatch = old.get('dispatch_event')
        require(type(dispatch) is dict and set(dispatch) == {'seq', 'hash'}
                and type(dispatch['seq']) is int, 'Retry predecessor lacks numerical dispatch custody')
        row = self.broker._db.execute('SELECT envelope,hash FROM events WHERE seq=?',
                                      (dispatch['seq'],)).fetchone()
        require(row is not None and row['hash'] == dispatch['hash'], 'Retry dispatch event is unavailable')
        event = decode(row['envelope'])
        require(event['actor'] == 'controller' and event['action'] == 'native_calibration_numerical_dispatched'
                and event['details'] == {
                    'pool_id': old['resource_pool_id'], 'inventory_id': old['resource_inventory_id'],
                    'study_id': old['study_id'], 'attempt_id': old['attempt_id'],
                    'world_id': old['world_id'], 'binding_hash': digest(binding),
                    'numerical_caller': 'native-reserved-calculation/1'},
                'Retry dispatch source/input/world custody differs')
        compact = old.get('custody', {})
        phases = compact.get('phases')
        require(compact.get('schema') == 'native-attempt-custody/1' and type(phases) is list
                and len(phases) == len(old.get('proofs', [])) <= 2
                and (compact.get('binding') == binding or not phases and compact.get('binding') == {}),
                'Retry predecessor phase custody differs')
        if not phases:
            require(old.get('result') is None and old.get('replay_result') is None,
                    'Unacknowledged retry predecessor cannot supply a result')
        else:
            require(phases[0] == {'phase': 'generate', 'result_hash': digest(old['result']),
                                  'proof_hash': digest(old['proofs'][0])},
                    'Retry generation acknowledgement differs')
            if len(phases) == 2:
                require(old['replay_result'] == {'verified_result_hash': digest(old['result'])}
                        and phases[1] == {'phase': 'replay', 'result_hash': digest(old['replay_result']),
                                          'proof_hash': digest(old['proofs'][1])},
                        'Retry replay acknowledgement differs')

    def _retry_equal(self, prior, result, proofs, outputs, binding):
        """Compare available full generations; never invent a missing first one."""
        if prior is None:
            return 'NOT_APPLICABLE'
        self._retry_origin(prior, binding)
        old = prior['body']
        previous = old.get('result')
        if previous is None or previous['outcome']['state'] == 'TECHNICAL_FAILURE':
            return 'NO_FULL_PREVIOUS_GENERATION'
        old_custody = old.get('custody', {})
        require(old.get('numerical_caller') == 'native-reserved-calculation/1'
                and old_custody.get('binding') == binding
                and old_custody.get('phases', [{}])[0].get('phase') == 'generate'
                and old_custody['phases'][0]['result_hash'] == digest(previous)
                and old_custody['phases'][0]['proof_hash'] == digest(old['proofs'][0]),
                'Retained retry generation lacks owned authenticated custody')
        before = old['proofs'][0]
        name = 'generate/stream.jsonl' + ('.gz' if 'stream_encoding' in before else '')
        descriptor = old['output_blobs'][name]
        raw = self.broker._read_blob_bytes(descriptor['sha256'])
        require(descriptor == before['stream_blob']
                and len(raw) == descriptor['size']
                and hashlib.sha256(raw).hexdigest() == descriptor['sha256'],
                'Retained original generation bytes differ')
        if 'stream_encoding' in before:
            from .study_stream import validate_stream
            validate_stream(raw, before['stream_encoding'], encoded_limit=268435456)
        if result is None or result['outcome']['state'] == 'TECHNICAL_FAILURE':
            return 'NO_FULL_CURRENT_GENERATION'
        require(canonical(previous) == canonical(result), 'Retry full calculation differs')
        after = proofs[0]
        for key in ('request_hash', 'footprint', 'native_binding', 'draw_engines',
                    'stream_blob', 'stream_encoding'):
            require(before.get(key) == after.get(key), 'Retry generation proof differs: ' + key)
        require(dict(outputs).get(name) == raw, 'Retry retained full generation bytes differ')
        return 'FULL_GENERATION_MATCH'

    def execute(self, token, pool_id, attempt_id, *, _cancel=None):
        from .study_process_control import (
            NativeAttemptCustody, ChildDeadlineExceeded, ChildCleanupFailed,
            StudyProcessCancelled, validate_cancellation)
        b, owner = self.broker, self.resources
        with b._mutex:
            actor = b._binding_owner(token)
            validate_cancellation(_cancel)
            pool = owner._pool(pool_id)
            history = owner._history(pool)
            history._live()
            require(attempt_id in history.pending, 'A pending native reservation is required')
            reservation = history.pending[attempt_id]
            require(reservation['phase'] == 'final', 'Numerical final caller requires a final reservation')
            require(attempt_id in b._native_calibration_active
                    and attempt_id not in b._native_calibration_dispatched,
                    'Native attempt was inherited or already dispatched')
            inventory = history.inventories['final']
            study = self.runner._study(inventory['body']['input_id'])
            manifest, payload = study['body']['manifest'], study['body']['payload']
            world = next(w for w in manifest['worlds'] if w['id'] == reservation['task_id'])
            previous = history.records.get(('final', world['id']))
            prior = b._artifact(previous['artifact_id']) if previous is not None else None
            limits = inventory['body']['request']
            binding = {'source_footprint': study['body']['source_footprint'],
                       'payload_hash': digest(payload), 'manifest_hash': digest(manifest),
                       'world_id': world['id'], 'native_binding': digest(study['body']['native_binding']),
                       'process_control': self.runner._study_process_control().request()}
            with b._transaction():
                require(not any(decode(row[0])['details'].get('attempt_id') == attempt_id
                    for row in b._db.execute("SELECT envelope FROM events WHERE "
                        "json_extract(envelope,'$.action')='native_calibration_numerical_dispatched'")),
                    'Native reservation already has a numerical dispatch')
                b._event('controller', 'native_calibration_numerical_dispatched',
                    pool_id=pool_id, inventory_id=inventory['id'], study_id=study['id'],
                    attempt_id=attempt_id, world_id=world['id'], binding_hash=digest(binding),
                    numerical_caller='native-reserved-calculation/1')
                row = b._db.execute('SELECT seq,hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
                dispatch_event = {'seq': row['seq'], 'hash': row['hash']}
            # A failed call cannot re-enter this reservation in the same Broker;
            # restart recovery handles a still-pending one conservatively.
            b._native_calibration_dispatched.add(attempt_id)
        started = time.monotonic()
        custody = NativeAttemptCustody()
        meter = {'materialized_bytes': 0, 'accounting_complete': True}
        outputs, failures = [], []
        source = None
        result, proofs, replay_result, returned = None, [], None, None
        clock_candidate = False
        parent_clock_observed = False
        currency_checked = True
        cancelled = None
        retry_comparison = 'NOT_CHECKED'

        def add_failure(exc):
            failures.append(self._failure(exc))

        def stop_dispatch():
            nonlocal cancelled
            if _cancel is not None:
                _cancel.set()
            try:
                owner.stop(token, pool_id, 'NATIVE_NUMERICAL_ATTEMPT_FAILED')
            except BaseException as exc:
                add_failure(exc)
                if not isinstance(exc, Exception):
                    cancelled = cancelled or exc

        def remaining():
            nonlocal parent_clock_observed
            if _cancel is not None and _cancel.is_set():
                raise StudyProcessCancelled('Native study parent requested cancellation')
            seconds = limits['execution_deadline_ms'] / 1000 - (time.monotonic() - started)
            if seconds <= 0:
                parent_clock_observed = True
                raise AttemptDeadlineExceeded('Owned native whole-attempt deadline elapsed')
            return seconds

        try:
            with b._mutex:
                owner._current(pool)
                b._require_usable_dependencies(inventory['id'])
                b._require_usable_dependencies(study['id'])
                if prior is not None:
                    b._require_usable_dependencies(prior['id'])
                    require(prior['body']['study_id'] == study['id']
                            and prior['body']['resource_pool_id'] == pool_id,
                            'Retry predecessor belongs to another input or pool')
                    self._retry_equal(prior, None, [], [], binding)
                self.runner._study_before_execute(study)
                inputs = self.runner._study_inputs(actor, study['body']['request'])
                require(digest(list(inputs)) == digest(
                    [payload, manifest, study['source_refs'], study['exposure']]),
                    'Native study dependencies changed')
                source = self.runner._load_study_source(study)
                require(footprint(source) == study['body']['source_footprint'],
                        'Native retained calculation source differs')
                cases = b._read_blob_bytes(payload['case_blob']['sha256'])
                require({'sha256': hashlib.sha256(cases).hexdigest(), 'size': len(cases)}
                        == payload['case_blob'], 'Native retained case bytes differ')
            remaining()
            returned = self.runner._execute_study_attempt(study, source, payload, manifest, world,
                cases, remaining, meter, outputs, _custody=custody, _cancel=_cancel)
        except BaseException as exc:
            add_failure(exc)
            clock_candidate = (type(exc) is ChildDeadlineExceeded
                               or type(exc) is AttemptDeadlineExceeded and parent_clock_observed)
            if isinstance(exc, ChildCleanupFailed):
                meter['accounting_complete'] = False
            if not isinstance(exc, Exception):
                cancelled = exc
            if not clock_candidate:
                stop_dispatch()

        # Preserve authenticated generation even when replay or final response
        # handling raised. Raw computed-result files alone do not enter custody.
        # An aggregate snapshot can exceed the codec envelope even when each
        # authenticated phase fits separately. Keep an explicitly unqualified
        # fallback and still retain raw outputs, check currency and settle the
        # failure; serialization must not leave the pool admitting new work.
        snapshot = {'schema': 'native-attempt-custody/1', 'binding': {}, 'phases': []}
        phases = []
        try:
            snapshot = custody.snapshot()
            phases = snapshot['phases']
            if snapshot['binding']:
                require(snapshot['binding'] == binding, 'Native attempt custody inputs differ')
            if phases:
                require(phases[0]['phase'] == 'generate', 'Native generation acknowledgement required')
                result = phases[0]['result']
                proofs = [item['proof'] for item in phases]
                _validate_native_calculation(result, manifest, world)
                if len(phases) == 2:
                    replay_result = phases[1]['result']
                    require(phases[1]['phase'] == 'replay'
                            and replay_result == {'verified_result_hash': digest(result)},
                            'Native separate replay acknowledgement differs')
            if not failures:
                require(type(returned) is tuple and len(returned) == 2 and phases
                        and canonical(list(returned)) == canonical([result, proofs]),
                        'Native return differs from authenticated phase custody')
                if result['outcome']['state'] == 'TECHNICAL_FAILURE':
                    require(_authenticated_inner_clock(source, result),
                            'Native technical failure is not an authenticated calculator deadline')
                    add_failure(AuthenticatedCalculatorDeadline('Pinned native calculator time stop'))
                    clock_candidate = True
                else:
                    require(result['outcome']['state'] in ('VERIFIED', 'INFORMATION_GAP')
                            and len(phases) == 2, 'Native completed world requires full separate replay')
            retry_comparison = self._retry_equal(prior, result, proofs, outputs,
                                                 binding)
        except BaseException as exc:
            add_failure(exc)
            clock_candidate = False
            if not isinstance(exc, Exception):
                cancelled = cancelled or exc
            stop_dispatch()

        # Error paths owe the same intended-use currency check. A clock cannot
        # bypass late source/cache/dependency withdrawal or mask its evidence.
        with b._mutex:
            checks = (lambda: self.runner._study_after_execute(study),
                      lambda: owner._current(pool),
                      lambda: b._require_usable_dependencies(inventory['id']),
                      lambda: b._require_usable_dependencies(study['id']))
            for check in checks:
                try:
                    check()
                except BaseException as exc:
                    currency_checked = False
                    add_failure(exc)
                    if not isinstance(exc, Exception):
                        cancelled = cancelled or exc
            if prior is not None:
                try:
                    b._require_usable_dependencies(prior['id'])
                except BaseException as exc:
                    currency_checked = False
                    add_failure(exc)
                    if not isinstance(exc, Exception):
                        cancelled = cancelled or exc
        if not failures:
            try:
                remaining()
            except BaseException as exc:
                add_failure(exc)
                clock_candidate = type(exc) is AttemptDeadlineExceeded and parent_clock_observed
                if not isinstance(exc, Exception):
                    cancelled = cancelled or exc
        if not meter['accounting_complete']:
            add_failure(Invalid('Native attempt resource usage is unknown'))

        state = ('COMPLETE' if not failures else 'KNOWN_TIMEOUT'
                 if clock_candidate and len(failures) == 1 and currency_checked
                 and meter['accounting_complete'] else 'FAILED')
        if state == 'FAILED':
            stop_dispatch()
        try:
            with b._mutex:
                require(len({name for name, raw in outputs}) == len(outputs),
                        'Native output names must be distinct')
                descriptors = {name: b._stage_blob_bytes(raw) for name, raw in outputs}
                storage = integer(meter['materialized_bytes'], 'Native materialized bytes') \
                    + sum(len(raw) for name, raw in outputs) + META
                compute = math.ceil((time.monotonic() - started) * 1000)
                if compute > reservation['compute_ms'] or storage > reservation['storage_bytes']:
                    add_failure(Invalid('Observed native numerical work exceeded its full reservation'))
                    state = 'FAILED'
                    stop_dispatch()
                outcome = (result['outcome'] if state == 'COMPLETE'
                           else self.runner._study_failed_outcome(manifest, world))
                compact = {'schema': snapshot['schema'], 'binding': snapshot['binding'],
                           'phases': [{'phase': p['phase'], 'result_hash': digest(p['result']),
                                       'proof_hash': digest(p['proof'])} for p in phases]}
                body = {'phase': 'final', 'task_id': world['id'], 'attempt_id': attempt_id,
                        'study_id': study['id'], 'world_id': world['id'],
                        'numerical_caller': 'native-reserved-calculation/1',
                        'dispatch_event': dispatch_event,
                        'result': result, 'proofs': proofs, 'replay_result': replay_result,
                        'custody': compact, 'outcome': outcome, 'retry_comparison': retry_comparison,
                        'resource_state': state, 'currency_checked': currency_checked,
                        'failure': failures[0] if failures else None, 'failures': failures,
                        'output_blobs': descriptors,
                        'technical_refs': [study['id']] + ([prior['id']] if prior is not None else []),
                        'settlement': {'attempt_id': attempt_id, 'compute_ms': compute,
                                       'storage_bytes': storage, 'usage_known': meter['accounting_complete']}}
                saved = owner.settle(token, pool_id, body,
                    source_refs=([prior['id']] if prior is not None else ()),
                    blob_refs=tuple(descriptors.values()))
        except BaseException:
            # Unsettled/staged work keeps its full reservation, cannot redispatch
            # here, and becomes unknown on reopen under the existing owner.
            stop_dispatch()
            raise
        if saved['body']['resource_state'] == 'FAILED' and _cancel is not None:
            _cancel.set()
        if cancelled is not None:
            raise cancelled
        return saved
