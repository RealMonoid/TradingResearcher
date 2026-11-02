"""Thin finite consumer guards, not approval of a calibration or its results.

The shared setup genuinely normalizes/certifies/compiles three synthetic rows,
completes four tiny development worlds, and prepares a fresh 1024-world target3
family calibration. No real final numerical world is run. Final transport spies
return explicitly synthetic INFORMATION_GAP observations solely to exercise the
real reservation/settlement/continuation and post-response guard machinery.

Each test uses a distinct restored Registry, real complete backup/full restore,
and sealed recovery-file hashes. Arbitrary pinned approval/driver fixture bytes
are operator-file custody fixtures, never another real-series authorization.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import family_run_support as family_support
from tools.calibration import finite_family as owner
from trading_researcher import calibration_runs, family_study
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.family_study_runs import FamilyCalibrationStudies
from trading_researcher.storage import restore_bundle


GIB = 1073741824
MIB = 1048576
ERRORS = (Invalid, Denied, Conflict, OSError)
PER_WORLD_RETAINED_BOUND = 7525747  # ceil(15412729856 / 2048), fixed physical planning bytes.


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def identity(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class FiniteFamilyConsumerEntrypointIndependentTests(unittest.TestCase):
    def test_entrypoint_accepts_only_broker_and_sealed_binding_no_caller_verdict(self):
        consume = getattr(owner, 'consume_next', None)
        self.assertTrue(callable(consume), 'The actual thin consuming guard is absent')
        self.assertEqual(['broker', 'bound_run'], list(inspect.signature(consume).parameters))


class FiniteFamilyConsumerIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = family_support.FamilyFixture()
        cls.addClassCleanup(cls.family.close)
        broker, token = cls.family.broker, cls.family.token
        estimate = {'world_time_rows': 3, 'observed_compute_ms': 10000,
            'observed_storage_bytes': 32 * MIB,
            'qualification': 'Synthetic consumer fixture; not a calibration cost guarantee.'}
        cost = broker.call(token, 'add_source',
            body={'schema': 'development-study-cost-estimate/1', **estimate},
            data_class='development')
        profile = {'specifications': [cls.family.args('unused')['specification']],
            'targets': [3], 'worlds_per_cell': 1, 'seed': 713,
            'mc_noncoverage': {'numerator': '1', 'denominator': '100'},
            'outer_noncoverage': {'numerator': '1', 'denominator': '20'},
            'responses': ['a', 'b'], 'patterns': [[0, 0], [0, 1], [1, 1], [2, 2]],
            'budget': {'max_compute_ms': 3600000, 'attempt_compute_ms': 300000,
                'max_storage_bytes': 4 * GIB, 'attempt_storage_bytes': 268435456,
                'max_attempts': 1}, 'cost_estimate': {'source_ref': cost['id'], **estimate}}
        development = broker.call(token, 'prepare_family_study', key='consumer-development',
            plan_id=cls.family.plan['id'], execution_id=cls.family.execution['id'],
            diagnostics_id=cls.family.diagnostics['id'], profile=profile)
        assert len(development['body']['manifest']['worlds']) == 4
        for _ in range(4):
            completed = broker.call(token, 'advance_family_study', study_id=development['id'])
        assert completed['status'] == 'COMPLETE', completed
        budget = {**profile['budget'], 'max_compute_ms': 300000}
        cls.final = broker.call(token, 'prepare_family_calibration',
            key='consumer-prepared-final', development_study_id=development['id'],
            time_rows=3, seed=714, budget=budget, cost_estimate=profile['cost_estimate'],
            applicability={name: {'status': 'not_applicable', 'cohort_ids': [],
                'reason': 'Synthetic small-row consumer fixture; no scientific applicability claim.'}
                for name in ('heavy_tail', 'overlap', 'common_shock')})
        assert len(cls.final['body']['manifest']['worlds']) == 1024
        initial = broker.call(token, 'inspect_family_calibration', calibration_id=cls.final['id'])
        assert initial['status'] == 'READY' and not initial['attempt_artifact_ids']
        cls.master = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.master.cleanup)
        cls.master_backup = Path(cls.master.name) / 'prepared-baseline-backup'
        assert broker.call(token, 'backup_bundle', destination=str(cls.master_backup))['status'] == 'PASS'

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        working = self.root / 'active-registry'
        key = self.family.broker.directory / 'operator.key'
        self.assertEqual('PASS', restore_bundle(self.master_backup, working, key)['status'])
        self.broker = Broker(working)
        self.addCleanup(self.broker.close)
        self.token = self.broker.admin_token
        self.approval = self.root / 'synthetic-operator-approval.json'
        self.approval.write_bytes(encoded({'scope': 'Synthetic file custody fixture only',
                                           'actual_series_authorized': False}))
        self.driver = self.root / 'synthetic-driver.py'
        self.driver.write_bytes(b'# Pinned synthetic operator bytes; this file is never executed.\n')
        self.backup = self.root / 'preserved-prepared-backup'
        self.assertEqual('PASS', self.broker.call(self.token, 'backup_bundle',
                                                  destination=str(self.backup))['status'])
        restored = self.root / 'preserved-full-restore'
        self.assertEqual('PASS', restore_bundle(self.backup, restored,
            self.broker.directory / 'operator.key')['status'])
        restored_broker = Broker(restored)
        try:
            self.assertEqual(self.final, restored_broker.call(restored_broker.admin_token,
                'get_artifact', artifact_id=self.final['id']))
        finally:
            restored_broker.close()
        self.restored_database = restored / 'registry.sqlite3'
        self.proof = {'schema': 'prepared-family-recovery/1', 'status': 'PASS',
            'calibration_id': self.final['id'], 'artifact_hash': identity(self.final),
            'initial_attempts': 0, 'initial_grants': 0,
            'backup_manifest': {'path': str((self.backup / 'manifest.json').resolve()),
                                'sha256': file_hash(self.backup / 'manifest.json')},
            'restored_database': {'path': str(self.restored_database.resolve()),
                                  'sha256': file_hash(self.restored_database)}}
        self.recovery = self.root / 'prepared-recovery.json'
        self.recovery.write_bytes(encoded(self.proof))
        body = self.final['body']
        operator_path = Path(owner.__file__).resolve()
        self.bound = {'schema': 'finite-family-run-binding/1',
            'calibration_id': self.final['id'], 'artifact_hash': identity(self.final),
            'request_hash': identity(body['request']), 'manifest_hash': identity(body['manifest']),
            'approval_path': str(self.approval.resolve()), 'approval_sha256': file_hash(self.approval),
            'assessment_footprint': deepcopy(body['assessment_source_footprint']),
            'calculation_footprint': deepcopy(body['source_footprint']),
            'runtime_identity': deepcopy(body['runtime_identity']),
            'registry_path': str(self.broker.directory.resolve()),
            'recovery_path': str(self.recovery.resolve()), 'recovery_sha256': file_hash(self.recovery),
            'driver_files': {str(operator_path): file_hash(operator_path),
                             str(self.driver.resolve()): file_hash(self.driver)}}

    def view(self):
        return self.broker.call(self.token, 'inspect_family_calibration',
                                calibration_id=self.final['id'])

    def threshold(self):
        # Logical continuation charges are not this physical file-length sum.
        committed = self.broker._db.execute('SELECT COALESCE(SUM(size),0) FROM blobs').fetchone()[0]
        retained = committed + (self.broker.directory / 'registry.sqlite3').stat().st_size
        remaining = len(self.final['body']['manifest']['worlds']) - self.view()['summary']['recorded_worlds']
        # Existing retained bytes need two future terminal copies. Future
        # results need their primary files as well as those same two copies.
        return 6 * GIB + 2 * retained + 3 * remaining * PER_WORLD_RETAINED_BOUND

    @contextmanager
    def observed_free(self, free=None):
        usage = shutil.disk_usage(self.broker.directory)
        observed = usage._replace(free=(1 << 50) if free is None else free)
        with patch('shutil.disk_usage', return_value=observed) as physical:
            yield physical

    @contextmanager
    def synthetic_final_transport(self):
        def synthetic(source, payload, manifest, world, cases, remaining, meter, outputs, **kwargs):
            # No sampling, estimator, bootstrap, or final replay occurs here.
            responses = [{'id': value['id'], 'truth': manifest['effects'][value['scenario']],
                          'state': 'INFORMATION_GAP', 'decision': None, 'covered': None}
                         for value in family_study.components(manifest, world)]
            outcome = family_study.outcome_record(manifest, world, responses)
            result = {'world_id': world['id'], 'outcome': outcome, 'scientific_readiness': False,
                      'classification_permitted': False, 'n_min': None}
            return result, [{'scope': 'synthetic transport fixture only'},
                            {'scope': 'synthetic replay placeholder; no numerical proof'}]
        with patch('trading_researcher.study_runs.execute_attempt', side_effect=synthetic) as transport:
            yield transport

    def assert_no_consumption(self, binding=None, extra_context=None):
        before = self.view()
        events = self.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        original_call = self.broker.call
        with self.observed_free(), patch.object(self.broker, 'call', wraps=original_call) as calls:
            if extra_context is None:
                with self.assertRaises(ERRORS):
                    owner.consume_next(self.broker, self.bound if binding is None else binding)
            else:
                with extra_context, self.assertRaises(ERRORS):
                    owner.consume_next(self.broker, self.bound if binding is None else binding)
        dispatched = [call.args[1] for call in calls.call_args_list if len(call.args) >= 2]
        self.assertNotIn('advance_family_calibration', dispatched)
        self.assertNotIn('continue_study', dispatched)
        self.assertEqual(before, self.view())
        self.assertEqual(events, self.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0])

    def test_ready_advance_then_real_continuation_bind_exact_fresh_results_and_usage(self):
        before = self.view()
        action = {'op': 'advance_family_calibration', 'args': {'calibration_id': self.final['id']}}
        original_call = self.broker.call
        with self.observed_free() as physical, self.synthetic_final_transport() as transport, \
                patch.object(self.broker, 'call', wraps=original_call) as calls:
            result = owner.consume_next(self.broker, self.bound)
        self.assertEqual(1, transport.call_count)
        self.assertEqual({'request', 'view', 'result_id'}, set(result))
        self.assertEqual(action, result['request'])
        after = self.view()
        self.assertEqual(after, result['view'])
        self.assertEqual(before['attempt_artifact_ids'], after['attempt_artifact_ids'][:-1])
        self.assertEqual(1, len(after['attempt_artifact_ids']))
        self.assertEqual(after['attempt_artifact_ids'][-1], result['result_id'])
        self.assertEqual('RESOURCE_STOP', after['status'])
        self.assertGreater(after['budget']['charged_compute_ms'], 0)
        self.assertEqual(MIB, after['budget']['charged_storage_bytes'] - before['budget']['charged_storage_bytes'])
        self.assertGreaterEqual(sum(call.args[1] == 'inspect_family_calibration'
            for call in calls.call_args_list if len(call.args) >= 2), 2)
        self.assertTrue(physical.called)
        expected_action = owner.next_request(after)
        with self.observed_free(), self.synthetic_final_transport() as transport:
            continued = owner.consume_next(self.broker, self.bound)
        transport.assert_not_called()
        fresh = self.view()
        self.assertEqual(expected_action, continued['request'])
        self.assertEqual(fresh, continued['view'])
        self.assertEqual(after['continuation_ids'], fresh['continuation_ids'][:-1])
        self.assertEqual(fresh['continuation_ids'][-1], continued['result_id'])
        grant = self.broker.call(self.token, 'get_artifact', artifact_id=continued['result_id'])
        self.assertEqual(expected_action['args'], grant['body']['request'])
        self.assertEqual(after['attempt_artifact_ids'], fresh['attempt_artifact_ids'])
        self.assertEqual(after['budget']['charged_compute_ms'], fresh['budget']['charged_compute_ms'])
        self.assertEqual(MIB, fresh['budget']['charged_storage_bytes'] - after['budget']['charged_storage_bytes'])
        self.assertEqual(3600000, fresh['budget']['max_compute_ms'] - after['budget']['max_compute_ms'])
        self.assertEqual(4 * GIB, fresh['budget']['max_storage_bytes'] - after['budget']['max_storage_bytes'])
        self.assertEqual(MIB, fresh['budget']['continuation_storage_bytes'])
        self.assertEqual(self.final, self.broker.call(self.token, 'get_artifact', artifact_id=self.final['id']))
        self.assertIs(fresh['scientific_readiness'], False)
        self.assertIsNone(fresh['n_min'])

    def test_binding_hash_identity_registry_runtime_and_loaded_driver_cannot_be_overridden(self):
        changes = [
            {'schema': 'finite-family-run-binding/999'}, {'calibration_id': 'f' * 64},
            {'artifact_hash': '0' * 64}, {'request_hash': '0' * 64}, {'manifest_hash': '0' * 64},
            {'assessment_footprint': {}}, {'calculation_footprint': {}},
            {'runtime_identity': {'not': 'the retained runtime'}},
            {'registry_path': str((self.root / 'another-registry').resolve())},
            {'approval_sha256': '0' * 64}, {'recovery_sha256': '0' * 64},
            {'driver_files': {str(self.driver.resolve()): file_hash(self.driver)}},
            {'driver_files': {**self.bound['driver_files'], str(Path(owner.__file__).resolve()): '0' * 64}},
            {'view': {'status': 'READY'}}, {'readiness': True},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.assert_no_consumption({**deepcopy(self.bound), **change})
        missing = deepcopy(self.bound)
        del missing['request_hash']
        self.assert_no_consumption(missing)
        foreign = self.broker.call(self.token, 'add_source',
            body={'purpose': 'Authentic generic source, never an owned final-calibration input'},
            data_class='operations')
        self.assert_no_consumption({**deepcopy(self.bound),
            'calibration_id': foreign['id'], 'artifact_hash': identity(foreign)})

    def test_changed_approval_driver_and_preserved_recovery_files_deny_before_dispatch(self):
        for path in (self.approval, self.driver, self.backup / 'manifest.json', self.restored_database):
            original = path.read_bytes()
            try:
                path.write_bytes(original + b'\nindependent owned fixture corruption\n')
                with self.subTest(path=path.name):
                    self.assert_no_consumption()
            finally:
                path.write_bytes(original)

    def test_recovery_receipt_requires_exact_identity_zero_initial_counts_and_preserved_paths(self):
        original = self.recovery.read_bytes()
        active_database = self.broker.directory / 'registry.sqlite3'
        changes = [
            {'schema': 'prepared-family-recovery/999'}, {'status': 'FAIL'},
            {'calibration_id': 'f' * 64}, {'artifact_hash': '0' * 64},
            {'initial_attempts': 1}, {'initial_grants': 1},
            {'initial_attempts': False}, {'initial_grants': False},
            {'backup_manifest': {'path': str(active_database.resolve()),
                                 'sha256': file_hash(active_database)}},
            {'restored_database': {'path': str(active_database.resolve()),
                                   'sha256': file_hash(active_database)}},
            {'backup_manifest': deepcopy(self.proof['restored_database'])},
            {'readiness': True},
        ]
        try:
            for change in changes:
                self.recovery.write_bytes(encoded({**deepcopy(self.proof), **change}))
                binding = {**deepcopy(self.bound), 'recovery_sha256': file_hash(self.recovery)}
                with self.subTest(change=change):
                    self.assert_no_consumption(binding)
        finally:
            self.recovery.write_bytes(original)

    def test_physical_threshold_uses_real_file_lengths_with_below_and_exact_equality(self):
        threshold = self.threshold()
        self.assertEqual(7525747 * 2048, 15412729856)
        before = self.view()
        with self.observed_free(threshold - 1), self.synthetic_final_transport() as transport:
            with self.assertRaises(Invalid):
                owner.consume_next(self.broker, self.bound)
        transport.assert_not_called()
        self.assertEqual(before, self.view())
        with self.observed_free(threshold), self.synthetic_final_transport() as transport:
            result = owner.consume_next(self.broker, self.bound)
        self.assertEqual(1, transport.call_count)
        self.assertEqual(self.view(), result['view'])
        self.assertEqual(1, len(result['view']['attempt_artifact_ids']))

    def test_old_two_copy_threshold_omits_future_primary_and_cannot_authorize_advance(self):
        before = self.view()
        remaining = len(self.final['body']['manifest']['worlds']) - before['summary']['recorded_worlds']
        required = self.threshold()
        old_two_copy_only = required - remaining * PER_WORLD_RETAINED_BOUND
        self.assertGreater(remaining, 0)
        self.assertLess(old_two_copy_only, required)
        events = self.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        original_call = self.broker.call
        with self.observed_free(old_two_copy_only), self.synthetic_final_transport() as transport, \
                patch.object(self.broker, 'call', wraps=original_call) as calls:
            with self.assertRaises(Invalid):
                owner.consume_next(self.broker, self.bound)
        transport.assert_not_called()
        dispatched = [call.args[1] for call in calls.call_args_list if len(call.args) >= 2]
        self.assertNotIn('advance_family_calibration', dispatched)
        self.assertNotIn('continue_study', dispatched)
        self.assertEqual(before, self.view())
        self.assertEqual(events, self.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0])

    def test_bound_fail_proof_cannot_be_upgraded_by_unbound_pass_bytes_after_hash(self):
        valid_pass_bytes = self.recovery.read_bytes()
        failed = {**deepcopy(self.proof), 'status': 'FAIL'}
        self.recovery.write_bytes(encoded(failed))
        binding = {**deepcopy(self.bound), 'recovery_sha256': file_hash(self.recovery)}
        hashed_failures = []
        original_hash = owner._hash_file

        def swap_after_hash(path, *args, **kwargs):
            result = original_hash(path, *args, **kwargs)
            if Path(path).resolve() == self.recovery.resolve():
                hashed_failures.append(result[0])
                self.assertEqual(binding['recovery_sha256'], result[0])
                # The bound bytes are FAIL. Later valid bytes do not upgrade
                # that exact receipt. A valid bound snapshot may otherwise be
                # used even if its pathname changes after the snapshot read.
                self.recovery.write_bytes(valid_pass_bytes)
            return result

        with self.synthetic_final_transport() as transport:
            self.assert_no_consumption(binding,
                extra_context=patch.object(owner, '_hash_file', side_effect=swap_after_hash))
        transport.assert_not_called()
        self.assertEqual([binding['recovery_sha256']], hashed_failures)
        self.assertEqual(valid_pass_bytes, self.recovery.read_bytes())

    def test_current_assessment_runtime_and_recomputed_input_mismatch_deny_before_reservation(self):
        self.assert_no_consumption(extra_context=patch.object(calibration_runs, 'source_bundle', return_value={}))
        self.assert_no_consumption(extra_context=patch('trading_researcher.study_runs._runtime_identity',
                                                      return_value={'not': 'the retained runtime'}))
        original = FamilyCalibrationStudies._study_inputs

        def changed_inputs(runner, actor, request):
            payload, manifest, refs, exposure = original(runner, actor, request)
            payload = deepcopy(payload)
            payload['changed_after_preparation'] = 'Synthetic retained-input mismatch'
            return payload, manifest, refs, exposure

        self.assert_no_consumption(extra_context=patch.object(FamilyCalibrationStudies,
            '_study_inputs', changed_inputs))

    def test_corrupt_retained_source_and_case_bytes_deny_before_any_attempt(self):
        body = self.final['body']
        source_identity = next(iter(body['source_files'].values()))['sha256']
        for identity_value in (source_identity, body['payload']['case_blob']['sha256']):
            path = self.broker._blob_path(identity_value)
            self.assertTrue(path.resolve().is_relative_to(self.broker.directory.resolve()))
            original = path.read_bytes()
            try:
                path.write_bytes(b'Independent copied committed blob corruption\n')
                with self.subTest(identity=identity_value):
                    self.assert_no_consumption()
            finally:
                path.write_bytes(original)

    def test_revoked_latest_grant_is_denied_before_the_next_advance(self):
        with self.observed_free(), self.synthetic_final_transport():
            owner.consume_next(self.broker, self.bound)
            grant_result = owner.consume_next(self.broker, self.bound)
        evidence = self.broker.call(self.token, 'add_source',
            body={'defect': 'Synthetic latest-resource-grant revocation fixture'}, data_class='operations')
        self.broker.call(self.token, 'revoke_dependency', key='consumer-revoke-latest-grant',
            dependency_id=grant_result['result_id'], reason='Independent synthetic technical revocation',
            evidence_refs=[evidence['id']])
        self.assert_no_consumption()
        self.assertEqual(1, len(self.view()['attempt_artifact_ids']))
        self.assertEqual(1, len(self.view()['continuation_ids']))

    def test_malformed_return_after_real_settlement_retains_usage_without_automatic_retry(self):
        before = self.view()
        original_call = self.broker.call
        dispatched = []

        def changed_response(token, operation, **args):
            result = original_call(token, operation, **args)
            if operation == 'advance_family_calibration':
                dispatched.append(operation)
                result = deepcopy(result)
                result['study_id'] = 'f' * 64
            return result

        with self.observed_free(), self.synthetic_final_transport() as transport, \
                patch.object(self.broker, 'call', side_effect=changed_response):
            with self.assertRaises(Invalid):
                owner.consume_next(self.broker, self.bound)
        self.assertEqual(['advance_family_calibration'], dispatched)
        self.assertEqual(1, transport.call_count)
        after = self.view()
        self.assertEqual(self.final['id'], after['study_id'])
        self.assertEqual(before['attempt_artifact_ids'], after['attempt_artifact_ids'][:-1])
        self.assertEqual(1, len(after['attempt_artifact_ids']))
        self.assertGreater(after['budget']['charged_compute_ms'], before['budget']['charged_compute_ms'])
        self.assertGreater(after['budget']['charged_storage_bytes'], before['budget']['charged_storage_bytes'])
        self.assertEqual([], after['continuation_ids'])

    def test_genuine_owner_technical_failure_is_returned_and_stops_without_retry(self):
        before = self.view()
        with self.observed_free(), patch('trading_researcher.study_runs.execute_attempt',
                side_effect=RuntimeError('Independent synthetic final transport failure')) as transport:
            result = owner.consume_next(self.broker, self.bound)
        self.assertEqual(1, transport.call_count)
        after = self.view()
        self.assertEqual(after, result['view'])
        self.assertEqual('TECHNICAL_FAILURE', after['status'])
        self.assertEqual(before['attempt_artifact_ids'], after['attempt_artifact_ids'][:-1])
        self.assertEqual(1, len(after['attempt_artifact_ids']))
        self.assertEqual(after['attempt_artifact_ids'][-1], result['result_id'])
        attempt = self.broker.call(self.token, 'get_artifact', artifact_id=result['result_id'])
        self.assertEqual('RuntimeError', attempt['body']['failure']['type'])
        self.assertGreater(after['budget']['charged_compute_ms'], before['budget']['charged_compute_ms'])
        self.assertGreater(after['budget']['charged_storage_bytes'], before['budget']['charged_storage_bytes'])
        with self.assertRaises(Invalid):
            owner.next_request(after)
        self.assertEqual([], after['continuation_ids'])


if __name__ == '__main__':
    unittest.main()
