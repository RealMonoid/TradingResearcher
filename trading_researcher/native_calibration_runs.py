"""Operator-owned native resource custody using the existing Registry.

This owner does not accept model verdicts or admit a numerical final series.
Controlled numerical work and its classifier belong to the consuming runner.
Retired Scalar records are read solely as financial history, never scheduled.
"""
import hashlib

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
