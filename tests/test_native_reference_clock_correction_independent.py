"""Independent bounded reference-clock correction controls, not acceptance.

Only the parent's outer reference deadline changes. Synthetic financial/result
metadata is labelled where used; actual Registry/ledger/full-copy owners remain
responsible for immutable charges and custody. No actual series is accessed.
"""
from copy import deepcopy
from contextlib import ExitStack
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher import native_calibration_controller as controller
from trading_researcher import native_calibration_runs as owner
from trading_researcher import family_study
from trading_researcher.codec import canonical, digest
import test_native_dependency_correction_independent as dependency_support


MIB = 1048576
ERRORS = dependency_support.ERRORS


class ReferenceClockFixture:
    """Three retained financial stages, no actual numerical result assertion.

    The eight COMPLETE/full-match labels and two-proof shapes below are
    synthetic controller-owned financial rows, as are the two failures. Actual
    resource, output-blob, full-copy, SQL, ancestry and clock-binding owners run.
    They are never supplied to an empirical acceptance or scientific judge.
    """
    def __init__(self, root, *, wrong_policy=False, wrong_failure=False):
        self.root = Path(root)
        old_policy = deepcopy(controller.policy()); old_policy['acceptance_deadline_ms'] = 300000
        if wrong_policy: old_policy['max_workers'] = 5
        with patch.object(controller, 'policy', return_value=old_policy):
            self.dependency = dependency_support.DependencyCorrectionFixture(root)
            self.broker, self.token = self.dependency.broker, self.dependency.token
            self.manager = self.dependency.manager
            try:
                self.predecessor = self.dependency.correct()
                self.first_pins = self.dependency.first.pins
                self.dependency_pins = self.dependency.pins
                with patch.object(owner, 'SOURCE_CORRECTION', self.first_pins), \
                        patch.object(owner, 'SOURCE_DEPENDENCY_CORRECTION', self.dependency_pins):
                    binding = self.predecessor['body']['source_correction']
                    self.control = controller.NativeCalibrationController(self.broker,
                        binding['controller_directory'], driver_file=self.dependency.first.control.driver_file)
                    self.control.prepare(self.token, self.dependency.args['key'], correction_args=self.dependency.args)
                    self.source_result = self.broker._artifact(self.control.binding['source_result_id'])
                    previous = self.dependency.reference
                    profile = deepcopy(previous['body']['manifest']['profile'])
                    profile['worlds_per_cell'] = 2
                    manifest = family_study.make_manifest(previous['body']['manifest']['assigned'], profile)
                    self.reference = self.dependency.first.financial.save({
                        'schema': 'native-calibration-reference-input/1', 'created_at': 1,
                        'request': {'key': 'synthetic-clock-reference',
                            'development_study_id': previous['body']['request']['development_study_id'],
                            'native_qualification_id': previous['body']['request']['native_qualification_id'],
                            'source_correction_pool_id': self.predecessor['id']},
                        'payload': deepcopy(previous['body']['payload']), 'manifest': manifest, 'references': {},
                        'native_binding': deepcopy(previous['body']['native_binding']),
                        'source_footprint': deepcopy(self.predecessor['body']['source_footprint']),
                        'process_control': deepcopy(previous['body']['process_control']),
                        'synthetic_financial_only': True, 'scientific_readiness': False},
                        refs=[previous['id'], self.predecessor['id']])
                    self.copies = owner.NativeCalibrationCopies(self.broker)
                    self.bookings = {label: self.copies.book(self.token, self.predecessor['id'], label)
                                     for label in ('prepared', 'terminal')}
                    tasks = owner.NativeCalibrationReferences.tasks(self.reference)
                    self.inventory = self.manager.bind_inventory(self.token, {
                        'key': 'synthetic-old-three-hundred-second-reference-inventory',
                        'pool_id': self.predecessor['id'], 'phase': 'acceptance', 'task_ids': sorted(tasks),
                        'execution_deadline_ms': 300000, 'attempt_compute_ms': 330000,
                        'attempt_storage_bytes': 256 * MIB, 'max_attempts': 1,
                        'expected_checkpoint': self.view()['resource_checkpoint']}, input_id=self.reference['id'])
                    selected = sorted(task for task, value in tasks.items() if value['mode'] == 'parallel')[:10]
                    assert len(selected) == 10
                    self.results = []
                    # Respect the actual6-slot ledger and drain all pending work
                    # after its first failure. No fake scheduler is substituted.
                    for offset, group in ((0, selected[:6]), (6, selected[6:])):
                        reservations = [self.manager.reserve(self.token, {
                            'pool_id': self.predecessor['id'], 'phase': 'acceptance', 'task_id': task,
                            'attempt_id': format(index + offset + 400, '032x'),
                            'expected_checkpoint': self.view()['resource_checkpoint']})
                            for index, task in enumerate(group)]
                        for index, reservation in enumerate(reservations, offset):
                            world = tasks[reservation['task_id']]['world_id']
                            complete, full = index < 8, index < 9
                            result = ({'schema': 'synthetic-financial-reference-result/1', 'world_id': world,
                                       'synthetic_financial_only': True} if full else None)
                            failure = (None if complete else {'type': 'AttemptDeadlineExceeded',
                                'message': 'Owned native whole-attempt deadline elapsed'} if index == 8 else {
                                'type': 'StudyProcessCancelled', 'message': 'Native study parent requested cancellation'})
                            if wrong_failure and index == 8: failure['type'] = 'TimeoutError'
                            descriptors, proofs = [], []
                            output = {}
                            if full:
                                raw = (canonical(result) + '\n').encode()
                                stream = self.broker._stage_blob_bytes(raw)
                                descriptors.append(stream)
                                output = {'generate/stream.jsonl': stream, 'replay/expected-stream.jsonl': stream}
                                proofs = [{'phase': phase, 'stream_blob': stream, 'synthetic_financial_only': True}
                                          for phase in ('generate', 'replay')]
                            self.results.append(self.manager.settle(self.token, self.predecessor['id'], {
                                'phase': 'acceptance', 'task_id': reservation['task_id'],
                                'attempt_id': reservation['attempt_id'], 'study_id': self.reference['id'],
                                'reference_id': self.reference['id'], 'reference_mode': 'parallel', 'world_id': world,
                                'resource_state': 'COMPLETE' if complete else 'FAILED', 'currency_checked': True,
                                'failure': failure, 'failures': [] if failure is None else [failure],
                                'result': result, 'replay_result': {'verified_result_hash': digest(result)} if full else None,
                                'proofs': proofs, 'reference_comparison': 'FULL_REFERENCE_MATCH' if full else 'NO_FULL_CURRENT_GENERATION',
                                'numerical_caller': 'native-reserved-calculation/1', 'synthetic_financial_only': True,
                                'output_blobs': output,
                                'custody': {'schema': 'native-attempt-custody/1', 'binding': {} if not full else {
                                    'source_footprint': self.reference['body']['source_footprint'],
                                    'payload_hash': digest(self.reference['body']['payload']), 'manifest_hash': digest(manifest),
                                    'world_id': world, 'native_binding': digest(self.reference['body']['native_binding']),
                                    'process_control': self.reference['body']['process_control']},
                                    'phases': [] if not full else [
                                        {'phase': 'generate', 'result_hash': digest(result), 'proof_hash': digest(proofs[0])},
                                        {'phase': 'replay', 'result_hash': digest({'verified_result_hash': digest(result)}),
                                         'proof_hash': digest(proofs[1])}]},
                                'settlement': {'attempt_id': reservation['attempt_id'],
                                    'compute_ms': 100 if complete else 327127 if index == 8 else 52353,
                                    'storage_bytes': MIB + sum(d['size'] for d in output.values()), 'usage_known': True}},
                                blob_refs=descriptors))
                    self.receipt_path = self.copies.receipt_path(self.predecessor['id'], 'terminal')
                    self.receipt = self.copies.create(self.token, self.predecessor['id'], 'terminal',
                        backup_directory=self.root / 'clock-terminal-backup',
                        restore_directory=self.root / 'clock-terminal-restore', receipt_path=self.receipt_path)
                self.before = deepcopy(self.view())
                self.pins = {**dict(getattr(owner, 'SOURCE_REFERENCE_CLOCK_CORRECTION', {})),
                    'schema': 'native-calibration-source-correction/3', 'predecessor_pool_id': self.predecessor['id'],
                    'expected_checkpoint': self.before['resource_checkpoint'], 'reference_id': self.reference['id'],
                    'source_result_id': self.source_result['id'], 'predecessor_correction_schema': 'native-calibration-source-correction/2',
                    'ancestor_pool_id': self.dependency.predecessor['id'],
                    'old_coordination_sha256': dependency_support.first_support.FIXED_COORDINATION,
                    'fixed_coordination_sha256': dependency_support.first_support.FIXED_COORDINATION,
                    'completed_attempts': 8, 'failed_attempts': 2,
                    'acceptance_artifact_ids': tuple(item['id'] for item in self.results),
                    'failure_pairs': (('AttemptDeadlineExceeded', 'Owned native whole-attempt deadline elapsed'),
                                      ('StudyProcessCancelled', 'Native study parent requested cancellation')),
                    'old_acceptance_deadline_ms': 300000, 'new_acceptance_deadline_ms': 600000,
                    'scope': 'Prospective outer reference measurement only; no final or scientific authority.'}
                self.args = {'key': 'reference-clock-correction-' + self.predecessor['id'],
                    'predecessor_pool_id': self.predecessor['id'], 'expected_checkpoint': self.before['resource_checkpoint'],
                    'terminal_receipt_path': str(self.receipt_path)}
            except BaseException:
                self.close()
                raise

    def view(self):
        return self.manager.inspect(self.token, self.predecessor['id'])

    def pinned(self, pins=None):
        stack = ExitStack()
        stack.enter_context(patch.object(owner, 'SOURCE_CORRECTION', self.first_pins))
        stack.enter_context(patch.object(owner, 'SOURCE_DEPENDENCY_CORRECTION', self.dependency_pins))
        stack.enter_context(patch.object(owner, 'SOURCE_REFERENCE_CLOCK_CORRECTION',
                                         self.pins if pins is None else pins, create=True))
        return stack

    def correct(self, pins=None):
        with self.pinned(pins): return self.manager.correct_source(self.token, self.args)

    def close(self):
        self.dependency.close()


class StopAfterInventory(Exception):
    pass


class NativeReferenceClockCallerIndependentTests(unittest.TestCase):
    def test_actual_reference_workflow_passes_ten_minute_outer_deadline_to_inventory(self):
        # Caller-only metadata seam: owning source qualification is not claimed,
        # no Registry/calculation runs, and execution stops at the captured bind.
        worlds = [{'id': hashlib.sha256(f'fixed-reference-{target}-{spec}-{pattern}-{replicate}'.encode()).hexdigest(),
            'time_rows': target, 'spec_index': spec, 'pattern_index': pattern, 'replicate': replicate}
            for target in (2048, 4096) for spec in range(2) for pattern in range(4) for replicate in range(2)]
        reference = {'id': '1' * 64, 'body': {'schema': 'native-calibration-reference-input/1',
            'request': {'development_study_id':
            '37208f834cf223fc3a94a4aa55ddf620d40c6b5f42bbd956d0936e69d507c9ab'},
            'manifest': {'profile': {'targets': [2048, 4096], 'worlds_per_cell': 2,
                'specifications': [{}, {}], 'patterns': [[0, 0], [0, 1], [1, 1], [2, 2]]},
                'worlds': worlds}}}
        invocation = []
        instance = controller.NativeCalibrationController.__new__(controller.NativeCalibrationController)
        instance.broker = object()
        def bound(token, pool_id, phase, input_id, task_ids, deadline_ms):
            invocation.append((pool_id, phase, input_id, list(task_ids), deadline_ms))
            raise StopAfterInventory()
        instance.bind_inventory = bound
        instance._run = lambda *a, **k: self.fail('Caller unit must stop before any numerical scheduling')
        with patch.object(owner.NativeCalibrationReferences, '_study_before_execute', return_value=None):
            with self.assertRaises(StopAfterInventory): instance.references('operator', '2' * 64, reference)
        self.assertEqual(len(invocation), 1)
        self.assertEqual(invocation[0][:3], ('2' * 64, 'acceptance', reference['id']))
        self.assertEqual(len(invocation[0][3]), 64)
        self.assertEqual(invocation[0][4], 600000)

    def test_policy_declares_six_hundred_seconds_and_preserves_thirty_second_cleanup(self):
        policy = controller.policy()
        self.assertEqual(policy['acceptance_deadline_ms'], 600000)
        self.assertEqual(policy['cleanup_reservation_ms'], 30000)
        self.assertEqual(policy['max_workers'], 6)


class NativeReferenceClockFinancialIndependentTests(unittest.TestCase):
    def fixture(self, **options):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-reference-clock-')
        self.addCleanup(temporary.cleanup)
        result = ReferenceClockFixture(Path(temporary.name), **options)
        self.addCleanup(result.close)
        return result

    def test_exact_clock_prefix_carries_every_charge_and_binds_new_controller_six_hundred_seconds(self):
        f = self.fixture()
        old_bytes = {item['id']: canonical(f.broker._artifact(item['id'])) for item in (
            f.dependency.first.pool, f.dependency.predecessor, f.predecessor, f.reference, *f.results)}
        before = f.before['budget']
        self.assertEqual(f.inventory['body']['request']['execution_deadline_ms'], 300000)
        self.assertEqual(f.inventory['body']['request']['attempt_compute_ms'], 330000)
        self.assertEqual(len(f.results), 10)
        self.assertEqual([item['body']['resource_state'] for item in f.results], ['COMPLETE'] * 8 + ['FAILED'] * 2)
        child = f.correct(); correction = child['body']['source_correction']
        self.assertEqual(correction['schema'], 'native-calibration-source-correction/3')
        self.assertEqual(correction['predecessor_pool_id'], f.predecessor['id'])
        self.assertEqual(correction['predecessor_reference_id'], f.reference['id'])
        self.assertEqual(correction['predecessor_source_result_id'], f.source_result['id'])
        self.assertEqual(correction['operational_start_utc'], f.dependency.first.control.binding['operational_start_utc'])
        self.assertEqual(correction['terminal_event_prefix'], f.receipt['event_prefix'])
        self.assertEqual(correction['reference_measurement_policy_change'], {
            'old_outer_deadline_ms': 300000, 'new_outer_deadline_ms': 600000,
            'scope': 'Prospective outer reference measurement only; frozen inner calculator and all acceptance criteria unchanged.'})
        self.assertEqual(child['body']['carry'], {'schema': 'native-calibration-resource-carry/1',
            'basis_id': f.predecessor['id'], **{key: before[key] for key in (
                'charged_compute_ms', 'charged_storage_bytes', 'allocated_compute_ms', 'allocated_storage_bytes',
                'grants_used', 'progress_units', 'no_progress_grants')},
            'last_grant_progress': f.manager._history(f.predecessor).last_grant_progress})
        after = f.manager.inspect(f.token, child['id'])['budget']
        self.assertEqual(after['charged_storage_bytes'], before['charged_storage_bytes'] + MIB)
        for key in ('charged_compute_ms', 'allocated_compute_ms', 'allocated_storage_bytes',
                    'grants_used', 'progress_units', 'no_progress_grants'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(after['grants_used'], 1); self.assertEqual(after['grants_remaining'], 178)
        self.assertFalse(after['outstanding_attempts']); self.assertFalse(after['usage_uncertain'])
        self.assertFalse(after['overrun']); self.assertFalse(after['halted'])
        self.assertTrue(f.view()['budget']['halted'])
        self.assertEqual(f.correct(), child)
        for stage in ('intent', 'ack'):
            path = Path(str(f.receipt_path) + '.source-correction-' + stage + '.json')
            self.assertTrue(path.is_file())
            self.assertLessEqual(path.stat().st_size, 4096)
        with f.pinned():
            current = controller.NativeCalibrationController(f.broker, correction['controller_directory'],
                driver_file=f.dependency.first.control.driver_file)
            self.assertEqual(current.prepare(f.token, f.args['key'], correction_args=f.args), child)
            self.assertEqual(current.binding['policy']['acceptance_deadline_ms'], 600000)
            self.assertEqual(current.binding['operational_start_utc'], correction['operational_start_utc'])
            # Metadata-only new reference retains the exact old inner manifest;
            # this tests actual inventory binding, never numerical admission.
            previous = f.reference
            reference = f.dependency.first.financial.save({**deepcopy(previous['body']),
                'request': {**previous['body']['request'], 'key': 'future-six-hundred-second-reference',
                            'source_correction_pool_id': child['id']}}, refs=[previous['id'], child['id']])
            tasks = owner.NativeCalibrationReferences.tasks(reference)
            inventory = current.bind_inventory(f.token, child['id'], 'acceptance', reference['id'],
                                               list(tasks), controller.policy()['acceptance_deadline_ms'])
            self.assertEqual(inventory['body']['request']['execution_deadline_ms'], 600000)
            self.assertEqual(inventory['body']['request']['attempt_compute_ms'], 630000)
            self.assertEqual(inventory['body']['request']['max_attempts'], 1)
            self.assertEqual(reference['body']['manifest'], previous['body']['manifest'])
            self.assertEqual(reference['body']['manifest']['profile']['budget']['attempt_compute_ms'], 300000)
        for identity, raw in old_bytes.items(): self.assertEqual(canonical(f.broker._artifact(identity)), raw)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 4)
        self.assertFalse(f.manager._objects('native-family-calibration-input/1'))

    def test_wrong_policy_attempt_set_failure_final_or_ancestor_cannot_use_clock_correction(self):
        f = self.fixture()
        for pins in ({**f.pins, 'acceptance_artifact_ids': tuple(item['id'] for item in f.results[:-1])},
                     {**f.pins, 'ancestor_pool_id': 'f' * 64}):
            with self.subTest(pins=list(pins)), self.assertRaises(ERRORS): f.correct(pins)
        self.assertEqual(f.view(), f.before)
        self.assertFalse(Path(str(f.receipt_path) + '.source-correction-intent.json').exists())
        f.dependency.first.financial.save({'schema': 'native-family-calibration-input/1', 'created_at': 1,
                                         'scientific_readiness': False}, refs=[f.reference['id']])
        with self.assertRaises(ERRORS): f.correct()
        self.assertEqual(f.view(), f.before)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 3)
        for variant in ('wrong_policy', 'wrong_failure'):
            with self.subTest(variant=variant):
                other = self.fixture(**{variant: True})
                with self.assertRaises(ERRORS): other.correct()
                self.assertEqual(other.view(), other.before)
                self.assertFalse(Path(str(other.receipt_path) + '.source-correction-intent.json').exists())
                self.assertEqual(len(other.manager._objects('native-calibration-resource-pool/1')), 3)


if __name__ == '__main__':
    unittest.main()
