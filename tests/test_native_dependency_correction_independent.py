"""Independent second pinned pre-final correction accounting/custody controls.

The original and two dependency failures are explicitly synthetic financial
metadata, not native or scientific evidence. Actual Registry/resource/event,
blob, controller source booking, full backup/restore and correction owners run.
Only analogous trusted authority/pin identities are substituted. No real series,
qualification, numerical child, actual Registry or protected outcome is used.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_native_source_correction_independent as first_support
from trading_researcher import native_calibration_runs as owner
from trading_researcher.codec import canonical


MIB = 1048576
ERRORS = first_support.ERRORS


class DependencyCorrectionFixture:
    def __init__(self, root, *, wrong_failure=False):
        self.first = first_support.CorrectionFixture(root)
        self.broker, self.token = self.first.broker, self.first.token
        self.manager = self.first.manager
        try:
            self.predecessor = self.first.correct()
            correction = self.predecessor['body']['source_correction']
            with patch.object(owner, 'SOURCE_CORRECTION', self.first.pins):
                self.control = first_support.controller.NativeCalibrationController(
                    self.broker, Path(correction['controller_directory']), driver_file=self.first.control.driver_file)
                self.control.prepare(self.token, self.first.args['key'], correction_args=self.first.args)
                self.source_result = self.broker._artifact(self.control.binding['source_result_id'])
                previous = self.first.reference
                # Typed metadata seam only: no request/input resolver or
                # qualification is replaced to claim a successful computation.
                self.reference = self.first.financial.save({
                    'schema': 'native-calibration-reference-input/1', 'created_at': 1,
                    'request': {'key': 'synthetic-dependency-failure-reference',
                        'development_study_id': previous['body']['request']['development_study_id'],
                        'native_qualification_id': previous['body']['request']['native_qualification_id'],
                        'source_correction_pool_id': self.predecessor['id']},
                    'payload': deepcopy(previous['body']['payload']),
                    'manifest': deepcopy(previous['body']['manifest']), 'references': {},
                    'native_binding': deepcopy(previous['body']['native_binding']),
                    'source_footprint': deepcopy(self.predecessor['body']['source_footprint']),
                    'process_control': deepcopy(previous['body']['process_control']),
                    'scientific_readiness': False}, refs=[previous['id'], self.predecessor['id']])
                self.copies = owner.NativeCalibrationCopies(self.broker)
                self.bookings = {label: self.copies.book(self.token, self.predecessor['id'], label)
                                 for label in ('prepared', 'terminal')}
                tasks = owner.NativeCalibrationReferences.tasks(self.reference)
                self.inventory = self.manager.bind_inventory(self.token, {
                    'key': 'dependency-failure-acceptance-inventory', 'pool_id': self.predecessor['id'],
                    'phase': 'acceptance', 'task_ids': sorted(tasks), 'execution_deadline_ms': 10000,
                    'attempt_compute_ms': 15000, 'attempt_storage_bytes': 256 * MIB,
                    'max_attempts': 1, 'expected_checkpoint': self.view()['resource_checkpoint']},
                    input_id=self.reference['id'])
                selected = sorted(task for task, value in tasks.items() if value['mode'] == 'parallel')[:2]
                reservations = [self.manager.reserve(self.token, {'pool_id': self.predecessor['id'],
                    'phase': 'acceptance', 'task_id': task, 'attempt_id': format(index + 300, '032x'),
                    'expected_checkpoint': self.view()['resource_checkpoint']}) for index, task in enumerate(selected)]
                self.failures = []
                for index, reservation in enumerate(reservations):
                    failure = {'type': 'Invalid', 'message': 'Native study dependencies changed'}
                    if wrong_failure and index == 1:
                        failure['message'] = 'A different input or integrity defect'
                    task = tasks[reservation['task_id']]
                    self.failures.append(self.manager.settle(self.token, self.predecessor['id'], {
                        'phase': 'acceptance', 'task_id': reservation['task_id'],
                        'attempt_id': reservation['attempt_id'], 'study_id': self.reference['id'],
                        'reference_id': self.reference['id'], 'reference_mode': 'parallel',
                        'world_id': task['world_id'], 'resource_state': 'FAILED', 'currency_checked': False,
                        'failure': failure, 'failures': [failure], 'result': None, 'replay_result': None,
                        'proofs': [], 'output_blobs': {},
                        'custody': {'schema': 'native-attempt-custody/1', 'binding': {}, 'phases': []},
                        'settlement': {'attempt_id': reservation['attempt_id'], 'compute_ms': 7 + index,
                            'storage_bytes': MIB, 'usage_known': True}}))
                self.receipt_path = self.copies.receipt_path(self.predecessor['id'], 'terminal')
                self.receipt = self.copies.create(self.token, self.predecessor['id'], 'terminal',
                    backup_directory=Path(root) / 'dependency-terminal-backup',
                    restore_directory=Path(root) / 'dependency-terminal-restore', receipt_path=self.receipt_path)
            self.before = deepcopy(self.view())
            self.pins = {**dict(owner.SOURCE_DEPENDENCY_CORRECTION),
                'predecessor_pool_id': self.predecessor['id'],
                'expected_checkpoint': self.before['resource_checkpoint'],
                'reference_id': self.reference['id'], 'source_result_id': self.source_result['id'],
                'ancestor_pool_id': self.first.pool['id']}
            self.args = {'key': 'dependency-correction-' + self.predecessor['id'],
                'predecessor_pool_id': self.predecessor['id'],
                'expected_checkpoint': self.before['resource_checkpoint'],
                'terminal_receipt_path': str(self.receipt_path)}
        except BaseException:
            self.close()
            raise

    def view(self):
        return self.manager.inspect(self.token, self.predecessor['id'])

    def correct(self, *, pins=None, args=None):
        with patch.object(owner, 'SOURCE_CORRECTION', self.first.pins), \
                patch.object(owner, 'SOURCE_DEPENDENCY_CORRECTION', self.pins if pins is None else pins):
            return self.manager.correct_source(self.token, self.args if args is None else args)

    def close(self):
        self.first.close()


class NativeDependencyCorrectionIndependentTests(unittest.TestCase):
    def fixture(self, **options):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-dependency-correction-')
        self.addCleanup(temporary.cleanup)
        result = DependencyCorrectionFixture(Path(temporary.name), **options)
        self.addCleanup(result.close)
        return result

    def test_exact_second_known_correction_preserves_all_financial_ancestry_and_only_one_child(self):
        f = self.fixture()
        old = {item['id']: canonical(f.broker._artifact(item['id'])) for item in (
            f.first.pool, f.predecessor, f.reference, f.source_result, *f.failures)}
        before = f.before['budget']
        child = f.correct(); body = child['body']; correction = body['source_correction']
        self.assertEqual(correction['schema'], 'native-calibration-source-correction/2')
        self.assertEqual(correction['predecessor_pool_id'], f.predecessor['id'])
        self.assertEqual(correction['predecessor_checkpoint'], f.before['resource_checkpoint'])
        self.assertEqual(correction['predecessor_reference_id'], f.reference['id'])
        self.assertEqual(correction['predecessor_source_result_id'], f.source_result['id'])
        self.assertEqual(correction['operational_start_utc'], f.first.control.binding['operational_start_utc'])
        self.assertEqual(correction['terminal_event_prefix'], f.receipt['event_prefix'])
        self.assertEqual(body['carry'], {'schema': 'native-calibration-resource-carry/1',
            'basis_id': f.predecessor['id'], **{key: before[key] for key in (
                'charged_compute_ms', 'charged_storage_bytes', 'allocated_compute_ms',
                'allocated_storage_bytes', 'grants_used', 'progress_units', 'no_progress_grants')},
            'last_grant_progress': f.manager._history(f.predecessor).last_grant_progress})
        after = f.manager.inspect(f.token, child['id'])['budget']
        self.assertEqual(after['charged_storage_bytes'], before['charged_storage_bytes'] + MIB)
        for key in ('charged_compute_ms', 'allocated_compute_ms', 'allocated_storage_bytes',
                    'grants_used', 'progress_units', 'no_progress_grants'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(after['grants_used'], 1); self.assertEqual(after['grants_remaining'], 178)
        self.assertFalse(after['halted']); self.assertFalse(after['outstanding_attempts'])
        self.assertTrue(f.view()['budget']['halted'])
        self.assertEqual(f.correct(), child)
        with self.assertRaises(ERRORS): f.correct(args={**f.args, 'key': 'another-second-stage-key'})
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 3)
        dependencies = f.broker._dependency_use(child['id'])
        self.assertEqual(dependencies['status'], 'NOT_REVOKED')
        self.assertTrue({f.first.pool['id'], f.predecessor['id']} <= set(dependencies['checked_versions']))
        for identity, raw in old.items(): self.assertEqual(canonical(f.broker._artifact(identity)), raw)
        self.assertIs(body['scientific_readiness'], False)
        self.assertFalse(f.manager._objects('native-family-calibration-input/1'))

    def test_wrong_stage_ancestor_failure_final_or_foreign_key_cannot_create_second_stage(self):
        f = self.fixture()
        wrong_stage = {**f.pins, 'predecessor_pool_id': f.first.pool['id'],
            'expected_checkpoint': f.first.before['resource_checkpoint']}
        wrong_stage_args = {**f.args, 'predecessor_pool_id': f.first.pool['id'],
            'expected_checkpoint': f.first.before['resource_checkpoint']}
        with self.assertRaises(ERRORS): f.correct(pins=wrong_stage, args=wrong_stage_args)
        with self.assertRaises(ERRORS): f.correct(pins={**f.pins, 'ancestor_pool_id': 'f' * 64})
        with self.assertRaises(ERRORS): f.correct(args={**f.args, 'key': f.first.args['key']})
        self.assertEqual(f.view(), f.before)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 2)
        self.assertFalse(Path(str(f.receipt_path) + '.source-correction-intent.json').exists())
        f.first.financial.save({'schema': 'native-family-calibration-input/1', 'created_at': 1,
                               'scientific_readiness': False}, refs=[f.reference['id']])
        with self.assertRaises(ERRORS): f.correct()
        self.assertEqual(f.view(), f.before)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 2)
        other = self.fixture(wrong_failure=True)
        with self.assertRaises(ERRORS): other.correct()
        self.assertEqual(other.view(), other.before)
        self.assertEqual(len(other.manager._objects('native-calibration-resource-pool/1')), 2)
        self.assertFalse(Path(str(other.receipt_path) + '.source-correction-intent.json').exists())


if __name__ == '__main__':
    unittest.main()
