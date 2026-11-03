"""Independent thin recovery-consumer guards, not live/scientific authority.

The genuine owned tiny kernel fixture is reused by composition, never TestCase
inheritance. Old failure timing and kernel transport spies remain explicitly
synthetic. Existing source/certification/input owners are not replaced. No live
Registry, original2048-world series, provider call or protected data is used.
"""
from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib
import importlib.util
import inspect
import json
from pathlib import Path
import shutil
import unittest
from unittest.mock import patch

import test_calibration_recovery_independent as kernel_support
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.storage import restore_bundle


MODULE = 'tools.calibration.finite_family_recovery'
GIB = 1073741824
MIB = 1048576
PER_WORLD = 7525747
ERRORS = (Invalid, Denied, Conflict, OSError)
BOUND_FIELDS = {'schema', 'authority_binding', 'recovery_id', 'artifact_hash',
    'recovery_artifact_hash', 'request_hash', 'manifest_hash', 'assessment_footprint',
    'calculation_footprint', 'controller_footprint', 'runtime_identity',
    'recovery_path', 'recovery_sha256', 'driver_files'}
PROOF_FIELDS = {'schema', 'status', 'study_id', 'recovery_id', 'input_id',
    'artifact_hash', 'recovery_artifact_hash', 'original_checkpoint', 'prepared_checkpoint',
    'initial_attempt_ids', 'initial_continuation_ids', 'charged_compute_ms',
    'charged_storage_bytes', 'backup_manifest', 'restored_database'}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def identity(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class RecoveryConsumerEntrypointIndependentTests(unittest.TestCase):
    def test_entrypoint_accepts_only_broker_and_sealed_binding(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE),
            'Recovery consumer absent; this check supplies0 adapter-domain coverage')
        owner = importlib.import_module(MODULE)
        self.assertTrue(callable(getattr(owner, 'consume_next', None)))
        self.assertEqual(['broker', 'bound_run'], list(inspect.signature(owner.consume_next).parameters))


class FiniteFamilyRecoveryIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = kernel_support.RecoveryKernelFixture()
        cls.addClassCleanup(cls.baseline.close)

    def setUp(self):
        # Composition borrows fixture helpers only: none of its30 TestCase
        # methods are inherited, discovered, or silently executed here.
        self.support = kernel_support.CalibrationRecoveryIndependentTests('runTest')
        self.support.baseline = self.baseline
        self.addCleanup(self.support.doCleanups)
        self.support.setUp()
        self.root, self.broker = self.support.root, self.support.broker
        self.token, self.kernel = self.support.token, self.support.kernel
        self.kernel_owner = self.support.owner
        self.study = self.support.study
        self.amendment = self.support.prepare()
        self.input = self.broker._artifact(self.amendment['body']['input_id'])
        self.source = self.broker._artifact(self.amendment['body']['source_id'])
        self.owner = importlib.import_module(MODULE)
        self.prepared = self.kernel.inspect(self.amendment['id'])
        self.backup = self.root / 'preserved-amendment-backup'
        self.restored_path = self.root / 'preserved-amendment-restore'
        self.assertEqual('PASS', self.broker.call(self.token, 'backup_bundle',
                                                 destination=str(self.backup))['status'])
        self.assertEqual('PASS', restore_bundle(self.backup, self.restored_path,
            self.broker.directory / 'operator.key')['status'])
        restored = Broker(self.restored_path)
        try:
            self.assertEqual(self.amendment, restored.call(restored.admin_token,
                'get_artifact', artifact_id=self.amendment['id']))
        finally:
            restored.close()
        ib = self.input['body']
        self.proof = {'schema': 'prepared-family-amendment-recovery/1', 'status': 'PASS',
            'study_id': self.study['id'], 'recovery_id': self.amendment['id'], 'input_id': self.input['id'],
            'artifact_hash': identity(self.study), 'recovery_artifact_hash': identity(self.amendment),
            'original_checkpoint': self.prepared['original_checkpoint'],
            'prepared_checkpoint': self.prepared['prepared_checkpoint'],
            'initial_attempt_ids': deepcopy(ib['original_attempt_ids']),
            'initial_continuation_ids': deepcopy(ib['original_continuation_ids']),
            'charged_compute_ms': ib['approval']['fixed_identity']['known_compute_ms_retained'],
            'charged_storage_bytes': ib['approval']['fixed_identity']['known_logical_bytes_retained']
                + ib['setup_storage_bytes'],
            'backup_manifest': {'path': str((self.backup / 'manifest.json').resolve()),
                                'sha256': file_hash(self.backup / 'manifest.json')},
            'restored_database': {'path': str((self.restored_path / 'registry.sqlite3').resolve()),
                                  'sha256': file_hash(self.restored_path / 'registry.sqlite3')}}
        self.proof_path = self.root / 'prepared-amendment-recovery.json'
        self.proof_path.write_bytes(encoded(self.proof))
        self.driver = self.root / 'synthetic-pinned-driver.py'
        self.driver.write_bytes(b'# Synthetic custody fixture; never executed or a live-series approval.\n')
        adapter = Path(self.owner.__file__).resolve()
        finite = Path(self.owner.finite.__file__).resolve()
        body = self.study['body']
        self.bound = {'schema': 'finite-family-recovery-run-binding/1',
            'authority_binding': deepcopy(self.support.bound), 'recovery_id': self.amendment['id'],
            'artifact_hash': identity(self.study), 'recovery_artifact_hash': identity(self.amendment),
            'request_hash': identity(body['request']), 'manifest_hash': identity(body['manifest']),
            'assessment_footprint': deepcopy(body['assessment_source_footprint']),
            'calculation_footprint': deepcopy(body['source_footprint']),
            'controller_footprint': deepcopy(self.source['body']['footprint']),
            'runtime_identity': deepcopy(body['runtime_identity']),
            'recovery_path': str(self.proof_path.resolve()), 'recovery_sha256': file_hash(self.proof_path),
            'driver_files': {str(adapter): file_hash(adapter), str(finite): file_hash(finite),
                             str(self.driver.resolve()): file_hash(self.driver)}}
        self.serial = 0
        self.assertEqual(BOUND_FIELDS, set(self.bound))
        self.assertEqual(PROOF_FIELDS, set(self.proof))

    def view(self):
        return self.kernel.inspect(self.amendment['id'])

    def threshold(self):
        view = self.view()
        completed = sum(cell['states']['VERIFIED'] + cell['states']['INFORMATION_GAP']
                        for cell in view['summary']['cells'])
        committed = self.broker._db.execute('SELECT COALESCE(SUM(size),0) FROM blobs').fetchone()[0]
        committed += (self.broker.directory / 'registry.sqlite3').stat().st_size
        return 6 * GIB + 2 * committed + 3 * (len(self.study['body']['manifest']['worlds']) - completed) * PER_WORLD

    @contextmanager
    def physical_free(self, free=None):
        observation = shutil.disk_usage(self.broker.directory)
        with patch('shutil.disk_usage', return_value=observation._replace(
                free=(1 << 50) if free is None else free)) as observed:
            yield observed

    def with_proof(self, proof):
        # This re-seals only deliberately invalid synthetic metadata so owner
        # consistency is tested independently of byte-hash rejection. A trusted
        # operator's arbitrary file seal is not scientific or legal approval.
        self.serial += 1
        path = self.root / ('negative-proof-' + str(self.serial) + '.json')
        path.write_bytes(encoded(proof))
        return {**self.bound, 'recovery_path': str(path), 'recovery_sha256': file_hash(path)}

    def no_dispatch(self, binding=None, free=None, context=None):
        before = self.view()
        events = len(self.support.events())
        kernel = self.kernel_owner.CalibrationRecovery
        with self.physical_free(free), \
                patch.object(kernel, 'advance', side_effect=AssertionError('Unsafe adapter advance')) as advance, \
                patch.object(kernel, 'continue_capacity', side_effect=AssertionError('Unsafe adapter grant')) as grant:
            if context is None:
                with self.assertRaises(ERRORS):
                    self.owner.consume_next(self.broker, self.bound if binding is None else binding)
            else:
                with context, self.assertRaises(ERRORS):
                    self.owner.consume_next(self.broker, self.bound if binding is None else binding)
        advance.assert_not_called()
        grant.assert_not_called()
        self.assertEqual(before, self.view())
        self.assertEqual(events, len(self.support.events()))

    def test_actual_tiny_adapter_advance_binds_one_fresh_generation_and_separate_replay(self):
        before = self.view()
        with self.physical_free() as physical:
            result = self.owner.consume_next(self.broker, self.bound)
        after = self.view()
        self.assertEqual({'request', 'view', 'result_id'}, set(result))
        self.assertEqual({'op': 'advance_calibration_recovery', 'args': {
            'recovery_id': self.amendment['id'], 'expected_checkpoint': before['recovery_checkpoint']}},
            result['request'])
        self.assertEqual(after, result['view'])
        self.assertEqual(before['attempt_artifact_ids'] + [result['result_id']], after['attempt_artifact_ids'])
        self.assertEqual(before['continuation_ids'], after['continuation_ids'])
        saved = self.broker._artifact(result['result_id'])['body']
        self.assertEqual(2, len(saved['proofs']))
        self.assertEqual(self.baseline.generation['result'], saved['result'])
        self.assertIs(saved['settlement']['usage_known'], True)
        self.assertEqual(before['budget']['charged_compute_ms'] + saved['settlement']['compute_ms'],
                         after['budget']['charged_compute_ms'])
        self.assertEqual(before['budget']['charged_storage_bytes'] + saved['settlement']['storage_bytes'],
                         after['budget']['charged_storage_bytes'])
        self.assertEqual(self.prepared['prepared_checkpoint'], after['prepared_checkpoint'])
        self.assertTrue(physical.called)
        self.support.assert_study_unchanged()

    def test_unknown_meter_returns_retained_uncertain_view_with_full_charge_and_no_retry(self):
        before = self.view()
        rejection = None
        reply = None
        def unknown(result, proofs, outputs, meter):
            meter['accounting_complete'] = False
        with self.physical_free(), self.support.transport(change=unknown) as transport:
            try:
                reply = self.owner.consume_next(self.broker, self.bound)
            except ERRORS as error:
                rejection = error
        after = self.view()
        self.assertEqual(1, transport.call_count)
        self.assertEqual(1, len(self.support.artifacts(kernel_support.RESULT)))
        saved = self.support.artifacts(kernel_support.RESULT)[0]
        settlement = saved['body']['settlement']
        self.assertIs(settlement['usage_known'], False)
        self.assertEqual('USAGE_UNCERTAIN', after['status'])
        self.assertEqual(before['budget']['charged_compute_ms'] + 600000,
                         after['budget']['charged_compute_ms'])
        self.assertEqual(before['budget']['charged_storage_bytes'] + 256 * MIB,
                         after['budget']['charged_storage_bytes'])
        self.assertEqual(before['attempt_artifact_ids'] + [saved['id']], after['attempt_artifact_ids'])
        self.assertEqual(before['continuation_ids'], after['continuation_ids'])
        self.unknown_meter_evidence = {'before': before, 'after': after, 'settlement': settlement,
            'adapter_rejection': None if rejection is None else {
                'type': type(rejection).__name__, 'message': str(rejection)}}
        self.no_dispatch()
        self.assertIsNone(rejection,
            'A correctly returned owned USAGE_UNCERTAIN view must reconcile conservative charges')
        self.assertEqual(after, reply['view'])
        self.assertEqual(saved['id'], reply['result_id'])

    def test_bound_hashes_source_runtime_identity_and_caller_flags_deny_before_dispatch(self):
        for field in ('artifact_hash', 'recovery_artifact_hash', 'request_hash', 'manifest_hash', 'recovery_id'):
            with self.subTest(field=field):
                self.no_dispatch({**self.bound, field: '0' * 64})
        for field in ('assessment_footprint', 'calculation_footprint', 'controller_footprint'):
            altered = deepcopy(self.bound)
            name = sorted(altered[field])[0]
            altered[field][name] = 'f' * 64
            with self.subTest(field=field):
                self.no_dispatch(altered)
        altered = deepcopy(self.bound)
        altered['runtime_identity']['version'] += ' synthetic mismatch'
        self.no_dispatch(altered)
        for field, value in (('ready', True), ('approved', True), ('view', self.view()),
                             ('action', {}), ('additional_compute_ms', 3600000)):
            with self.subTest(extra_field=field):
                self.no_dispatch({**self.bound, field: value})

    def test_both_loaded_finite_sources_and_optional_driver_bytes_are_pinned(self):
        for path in (Path(self.owner.__file__).resolve(), Path(self.owner.finite.__file__).resolve()):
            altered = deepcopy(self.bound)
            del altered['driver_files'][str(path)]
            with self.subTest(missing=str(path)):
                self.no_dispatch(altered)
            altered = deepcopy(self.bound)
            altered['driver_files'][str(path)] = 'f' * 64
            with self.subTest(wrong_hash=str(path)):
                self.no_dispatch(altered)
        self.driver.write_bytes(b'# Deliberately changed owned synthetic driver bytes.\n')
        self.no_dispatch()

    def test_proof_identity_prefix_charges_and_stable_prepared_checkpoint_are_owned(self):
        alterations = [('status', 'FAIL'), ('input_id', self.study['id']),
            ('study_id', 'e' * 64), ('recovery_id', 'd' * 64), ('artifact_hash', 'c' * 64),
            ('recovery_artifact_hash', 'b' * 64), ('original_checkpoint', 'a' * 64),
            ('prepared_checkpoint', '9' * 64), ('initial_attempt_ids', []),
            ('initial_continuation_ids', []), ('charged_compute_ms', True),
            ('charged_storage_bytes', self.proof['charged_storage_bytes'] - 1)]
        for field, value in alterations:
            with self.subTest(field=field):
                self.no_dispatch(self.with_proof({**deepcopy(self.proof), field: value}))
        self.no_dispatch(self.with_proof({**self.proof, 'ready': True}))

    def test_preserved_manifest_database_bytes_and_separate_paths_are_required(self):
        for key in ('backup_manifest', 'restored_database'):
            proof = deepcopy(self.proof)
            proof[key]['sha256'] = '0' * 64
            with self.subTest(changed_file=key):
                self.no_dispatch(self.with_proof(proof))
        proof = deepcopy(self.proof)
        proof['restored_database'] = {'path': str((self.broker.directory / 'registry.sqlite3').resolve()),
                                      'sha256': file_hash(self.broker.directory / 'registry.sqlite3')}
        self.no_dispatch(self.with_proof(proof))
        proof = deepcopy(self.proof)
        # Both files exist and hash correctly; this isolates the requirement
        # that the preserved backup and restored database occupy separate paths.
        (self.restored_path / 'manifest.json').write_bytes((self.backup / 'manifest.json').read_bytes())
        proof['backup_manifest']['path'] = str(self.restored_path / 'manifest.json')
        self.no_dispatch(self.with_proof(proof))

    def test_pinned_fail_proof_cannot_be_upgraded_by_a_second_unbound_read(self):
        valid = self.proof_path.read_bytes()
        self.proof_path.write_bytes(encoded({**self.proof, 'status': 'FAIL'}))
        bound = {**self.bound, 'recovery_sha256': file_hash(self.proof_path)}
        original_hash = self.owner._hash_file
        swaps = []
        def swap_after_hash(path, *args, **kwargs):
            result = original_hash(path, *args, **kwargs)
            if Path(path).resolve() == self.proof_path.resolve():
                self.proof_path.write_bytes(valid)
                swaps.append(True)
            return result
        self.no_dispatch(bound, context=patch.object(self.owner, '_hash_file', side_effect=swap_after_hash))
        self.assertEqual([True], swaps)

    def test_physical_planning_keeps_named_failed_retry_and_accepts_exact_equality(self):
        self.assertEqual(1, self.view()['summary']['recorded_worlds'])
        completed = sum(cell['states']['VERIFIED'] + cell['states']['INFORMATION_GAP']
                        for cell in self.view()['summary']['cells'])
        self.assertEqual(0, completed)
        threshold = self.threshold()
        # Omitting the one already recorded failed world understates all three
        # future copies. This must deny although that older formula would fit.
        self.no_dispatch(free=threshold - 3 * PER_WORLD + 1)
        self.no_dispatch(free=threshold - 1)
        with self.physical_free(threshold), self.support.transport() as transport:
            result = self.owner.consume_next(self.broker, self.bound)
        self.assertEqual(1, transport.call_count)
        self.assertEqual(self.view(), result['view'])

    def test_one_actual_paired_grant_keeps_old_ids_fee_and_immutable_prepared_proof(self):
        original_proof_bytes = self.proof_path.read_bytes()
        initial = self.view()
        for index in range(5):
            with self.physical_free(), self.support.transport(index=index,
                    elapsed=Fraction(5999999, 10000)) as transport:
                result = self.owner.consume_next(self.broker, self.bound)
            self.assertEqual(1, transport.call_count)
            self.assertEqual('advance_calibration_recovery', result['request']['op'])
        stopped = self.view()
        self.assertEqual('RESOURCE_STOP', stopped['status'])
        with self.physical_free(), self.support.transport() as transport:
            result = self.owner.consume_next(self.broker, self.bound)
        transport.assert_not_called()
        after = self.view()
        self.assertEqual({'op': 'continue_calibration_recovery', 'args': {
            'recovery_id': self.amendment['id'], 'expected_checkpoint': stopped['recovery_checkpoint']}},
            result['request'])
        self.assertEqual(stopped['continuation_ids'] + [result['result_id']], after['continuation_ids'])
        self.assertEqual(initial['continuation_ids'], after['continuation_ids'][:-1])
        self.assertEqual(2, after['budget']['continuation_count'])
        self.assertEqual(stopped['attempt_artifact_ids'], after['attempt_artifact_ids'])
        self.assertEqual(stopped['budget']['max_compute_ms'] + 3600000, after['budget']['max_compute_ms'])
        self.assertEqual(stopped['budget']['max_storage_bytes'] + 4 * GIB, after['budget']['max_storage_bytes'])
        self.assertEqual(stopped['budget']['charged_compute_ms'], after['budget']['charged_compute_ms'])
        self.assertEqual(stopped['budget']['charged_storage_bytes'] + MIB, after['budget']['charged_storage_bytes'])
        self.assertEqual(original_proof_bytes, self.proof_path.read_bytes())
        self.assertEqual(self.prepared['prepared_checkpoint'], after['prepared_checkpoint'])
        self.assertEqual(after, result['view'])

    def test_known_failure_is_returned_retained_then_next_call_denies_without_retry(self):
        before = self.view()
        with self.physical_free(), self.support.transport(error=RuntimeError('Synthetic retained consumer failure')) as transport:
            reply = self.owner.consume_next(self.broker, self.bound)
        self.assertEqual(1, transport.call_count)
        after = self.view()
        self.assertEqual('TECHNICAL_FAILURE', after['status'])
        self.assertEqual(after, reply['view'])
        self.assertEqual(before['attempt_artifact_ids'] + [reply['result_id']], after['attempt_artifact_ids'])
        self.assertEqual(2, after['budget']['attempts_per_world'][self.support.failed['body']['world_id']])
        self.no_dispatch()

    def test_bad_response_after_real_owned_settlement_cannot_trigger_a_second_action(self):
        before = self.view()
        actual = self.kernel_owner.CalibrationRecovery.advance
        def committed_bad_response(instance, *args, **kwargs):
            response = actual(instance, *args, **kwargs)
            return {**response, 'study_id': 'f' * 64}
        with self.physical_free(), self.support.transport() as transport, \
                patch.object(self.kernel_owner.CalibrationRecovery, 'advance', autospec=True,
                             side_effect=committed_bad_response) as advance:
            with self.assertRaises(Invalid):
                self.owner.consume_next(self.broker, self.bound)
        self.assertEqual(1, advance.call_count)
        self.assertEqual(1, transport.call_count)
        after = self.view()
        self.assertEqual(1, len(self.support.artifacts(kernel_support.RESULT)))
        self.assertEqual(before['attempt_artifact_ids'], after['attempt_artifact_ids'][:-1])
        self.assertEqual(1, len(self.support.events('calibration_recovery_reserved')))
        self.assertEqual(1, len(self.support.events('calibration_recovery_settled')))
        self.assertGreater(after['budget']['charged_compute_ms'], before['budget']['charged_compute_ms'])
        self.assertEqual(before['continuation_ids'], after['continuation_ids'])

    def test_revoked_amendment_has_no_fresh_consuming_authority(self):
        self.support.revoke(self.amendment['id'])
        self.no_dispatch()

    def test_cloned_bound_run_cannot_activate_a_different_restored_registry_path(self):
        # Keep the proof's preserved restored database offline and outside this
        # attempted active clone, so its proof hashes/paths remain valid. Only
        # the immutable original execution location distinguishes this clone.
        activated_copy = self.root / 'attempted-active-restore'
        self.assertEqual('PASS', restore_bundle(self.backup, activated_copy,
            self.broker.directory / 'operator.key')['status'])
        restored = Broker(activated_copy)
        try:
            binding = deepcopy(self.bound)
            binding['authority_binding']['registry_path'] = str(activated_copy.resolve())
            reader = self.kernel_owner.CalibrationRecovery(restored, binding['authority_binding'])
            self.assertEqual('RESTORED_COPY', reader.inspect(self.amendment['id'])['status'])
            with self.physical_free(), \
                    patch.object(self.kernel_owner.CalibrationRecovery, 'advance',
                                 side_effect=AssertionError('Restored copy advanced')) as advance, \
                    patch.object(self.kernel_owner.CalibrationRecovery, 'continue_capacity',
                                 side_effect=AssertionError('Restored copy granted')) as grant:
                with self.assertRaises(ERRORS):
                    self.owner.consume_next(restored, binding)
            advance.assert_not_called()
            grant.assert_not_called()
        finally:
            restored.close()


if __name__ == '__main__':
    unittest.main()
