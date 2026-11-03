"""Independent exact pre-final host-input recovery financial controls.

Qualification/result labels below are explicitly synthetic financial metadata.
Actual immutable Registry/resource/controller bookings, ancestry, full copies,
markers and source-currentness owners run. No native qualification, numerical
child, empirical acceptance, actual Registry, final seed or study is used.
"""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import test_native_reference_clock_correction_independent as clock_support
from trading_researcher import native_calibration_controller as controller
from trading_researcher import native_calibration_runs as owner
from trading_researcher import native_qualification
from trading_researcher.codec import canonical
from trading_researcher.evaluation_plans import footprint


MIB = 1048576
ERRORS = clock_support.ERRORS
FIRST = clock_support.dependency_support.first_support
PROFILE_FILE = 'trading_researcher/native_qualification_profile.py'
OLD_PROFILE_SHA = '58d5478e0cc12be426540d6c6acf9b1ef02305ccb79af9906c5e4acd6f470d88'
NEW_PROFILE_SHA = 'b31c300924834b61e627d8ea0d5d2ebb5372e55081338980061be0de15059dda'
HOST_AMENDMENT_SHA = 'c9ff91a14403bf05676857e9d25e9991402a6be004fcac646fd0abc587660988'
HOST_FAILURE = 'Native host image was not independently qualified'


class HostRecoveryFixture:
    """Four small historical financial stages, with no qualifying computation.

    Historical profile bytes come from the retained fixed adoption archive and
    are only source/custody inputs. The trusted analogous pin-ID seam does not
    bypass any financial/history/full-copy/controller resolver.
    """
    def __init__(self, root, *, variant=None):
        self.root = Path(root)
        self.clock = None
        with ZipFile(FIRST.PROJECT / 'tests/fixtures/native-packing-adoption-checks-2026-11-02.zip') as archive:
            old_profile = archive.read(PROFILE_FILE)
        assert hashlib.sha256(old_profile).hexdigest() == OLD_PROFILE_SHA
        self.old_source = {**FIRST.source_bundle(), PROFILE_FILE: old_profile}
        if variant == 'forbidden_source':
            self.old_source['trading_researcher/codec.py'] += b'\n# Unsupported unrelated historical owner change.\n'
        try:
            with FIRST.historical_source(self.old_source), \
                    patch.object(FIRST, 'source_bundle', return_value=self.old_source):
                self.clock = clock_support.ReferenceClockFixture(self.root)
                self.broker, self.token = self.clock.broker, self.clock.token
                self.manager = self.clock.manager
                self.predecessor = self.clock.correct()
                self.reference = self.clock.reference
                self.financial = self.clock.dependency.first.financial
                with self.clock.pinned():
                    correction = self.predecessor['body']['source_correction']
                    self.control = controller.NativeCalibrationController(self.broker,
                        correction['controller_directory'], driver_file=self.clock.control.driver_file)
                    self.control.prepare(self.token, self.clock.args['key'], correction_args=self.clock.args)
                    self.source_result = self.broker._artifact(self.control.binding['source_result_id'])
                    self.copies = owner.NativeCalibrationCopies(self.broker)
                    self.bookings = {label: self.copies.book(self.token, self.predecessor['id'], label)
                                     for label in ('prepared', 'terminal')}
                    self.runtime_result = self._settle_setup('runtime_retain', {
                        'runtime_id': self.reference['body']['native_binding']['runtime_id']},
                        refs=[self.reference['body']['native_binding']['runtime_id']])
                    if variant == 'acceptance':
                        tasks = owner.NativeCalibrationReferences.tasks(self.reference)
                        self.manager.bind_inventory(self.token, {
                            'key': 'forbidden-host-stage-acceptance', 'pool_id': self.predecessor['id'],
                            'phase': 'acceptance', 'task_ids': sorted(tasks),
                            'execution_deadline_ms': 600000, 'attempt_compute_ms': 630000,
                            'attempt_storage_bytes': 256 * MIB, 'max_attempts': 1,
                            'expected_checkpoint': self.view()['resource_checkpoint']},
                            input_id=self.reference['id'])
                    if variant == 'pending':
                        self.manager.reserve(self.token, {'pool_id': self.predecessor['id'],
                            'phase': 'setup', 'task_id': self.predecessor['body']['setup_tasks']['acceptance_summary'],
                            'attempt_id': 'a' * 32, 'expected_checkpoint': self.view()['resource_checkpoint']})
                    q_failure = {'type': 'Invalid', 'message': HOST_FAILURE}
                    if variant == 'wrong_failure':
                        q_failure = {'type': 'Invalid', 'message': 'A different qualification or integrity defect'}
                    self.qualification = self.financial.save({
                        'schema': 'native-runtime-qualification/1',
                        'profile': native_qualification.profile.PROFILE, 'created_at': 1,
                        'input_id': self.financial.recovery_source['id'],
                        'status': 'CERTIFIED' if variant == 'wrong_qualification' else 'CERTIFICATION_GAP',
                        'failure': q_failure, 'failures': [q_failure], 'proofs': [], 'report': None,
                        'settlement': {'attempt_id': 'b' * 32, 'compute_ms': 29,
                            'storage_bytes': MIB, 'usage_known': True},
                        'synthetic_financial_only': True, 'scientific_readiness': False},
                        refs=[self.financial.recovery_source['id']], authority=native_qualification.AUTHORITY)
                    failure = {'type': 'Invalid',
                               'message': 'Native setup did not satisfy its owned completion criterion'}
                    self.failed_setup = self._settle_setup('runtime_qualification', {
                        'qualification_id': self.qualification['id'], 'ok': False, 'failure': q_failure},
                        refs=[self.qualification['id']], failure=failure)
                    self.receipt_path = self.copies.receipt_path(self.predecessor['id'], 'terminal')
                    self.receipt = None
                    if variant != 'pending':
                        self.receipt = self.copies.create(self.token, self.predecessor['id'], 'terminal',
                            backup_directory=self.root / 'host-terminal-backup',
                            restore_directory=self.root / 'host-terminal-restore', receipt_path=self.receipt_path)
                self.before = deepcopy(self.view())
            self.pins = {**dict(getattr(owner, 'SOURCE_HOST_INPUT_CORRECTION', {})),
                'schema': 'native-calibration-source-correction/4',
                'predecessor_pool_id': self.predecessor['id'],
                'expected_checkpoint': self.before['resource_checkpoint'],
                'reference_id': self.reference['id'], 'source_result_id': self.source_result['id'],
                'predecessor_correction_schema': 'native-calibration-source-correction/3',
                'ancestor_pool_id': self.clock.predecessor['id'],
                'qualification_id': self.qualification['id'], 'failed_setup_artifact_id': self.failed_setup['id'],
                'old_coordination_sha256': FIRST.FIXED_COORDINATION,
                'fixed_coordination_sha256': FIRST.FIXED_COORDINATION,
                'old_profile_sha256': OLD_PROFILE_SHA, 'new_profile_sha256': NEW_PROFILE_SHA,
                'host_amendment_sha256': HOST_AMENDMENT_SHA,
                'scope': 'Exact known failed host-input qualification; no acceptance or final retry authority.'}
            self.args = {'key': 'host-input-correction-' + self.predecessor['id'],
                'predecessor_pool_id': self.predecessor['id'],
                'expected_checkpoint': self.before['resource_checkpoint'],
                'terminal_receipt_path': str(self.receipt_path)}
        except BaseException:
            self.close()
            raise

    def _settle_setup(self, name, result, *, refs, failure=None):
        task = self.predecessor['body']['setup_tasks'][name]
        reservation = self.manager.reserve(self.token, {'pool_id': self.predecessor['id'],
            'phase': 'setup', 'task_id': task, 'attempt_id': ('c' if failure else 'd') * 32,
            'expected_checkpoint': self.view()['resource_checkpoint']})
        return self.manager.settle(self.token, self.predecessor['id'], {
            'phase': 'setup', 'task_id': task, 'attempt_id': reservation['attempt_id'],
            'resource_state': 'COMPLETE' if failure is None else 'FAILED',
            'currency_checked': failure is None, 'failure': failure,
            'failures': [] if failure is None else [failure], 'result': result,
            'technical_refs': refs, 'output_blobs': {}, 'synthetic_financial_only': True,
            'settlement': {'attempt_id': reservation['attempt_id'],
                'compute_ms': 13 if failure is None else 31, 'storage_bytes': MIB, 'usage_known': True}})

    def view(self):
        return self.manager.inspect(self.token, self.predecessor['id'])

    def pinned(self, pins=None):
        stack = ExitStack()
        stack.enter_context(self.clock.pinned())
        stack.enter_context(patch.object(owner, 'SOURCE_HOST_INPUT_CORRECTION',
                                         self.pins if pins is None else pins, create=True))
        return stack

    def correct(self, *, pins=None, args=None):
        with self.pinned(pins):
            return self.manager.correct_source(self.token, self.args if args is None else args)

    def close(self):
        if self.clock is not None:
            self.clock.close()


class NativeHostRecoveryIndependentTests(unittest.TestCase):
    def fixture(self, **options):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-host-recovery-')
        self.addCleanup(temporary.cleanup)
        result = HostRecoveryFixture(Path(temporary.name), **options)
        self.addCleanup(result.close)
        return result

    def assert_denied_without_successor(self, f, **kwargs):
        count = len(f.manager._objects('native-calibration-resource-pool/1'))
        with self.assertRaises(ERRORS):
            f.correct(**kwargs)
        self.assertEqual(f.view(), f.before)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), count)
        self.assertFalse(Path(str(f.receipt_path) + '.source-correction-intent.json').exists())

    def test_exact_five_setup_rows_carry_every_charge_and_only_one_current_host_successor(self):
        f = self.fixture()
        self.assertEqual(hashlib.sha256(FIRST.source_bundle()[PROFILE_FILE]).hexdigest(), NEW_PROFILE_SHA)
        history = f.manager._history(f.predecessor)
        self.assertEqual(set(history.inventories), {'setup'})
        expected_names = {'controller_source', 'runtime_retain', 'runtime_qualification',
                          'prepared_copies', 'terminal_copies'}
        self.assertEqual(set(history.records), {('setup', f.predecessor['body']['setup_tasks'][name])
                                               for name in expected_names})
        self.assertEqual(sorted(row['state'] for row in history.records.values()), ['COMPLETE'] * 4 + ['FAILED'])
        old = {item['id']: canonical(f.broker._artifact(item['id'])) for item in (
            f.predecessor, f.reference, f.source_result, f.runtime_result, f.qualification,
            f.failed_setup, *f.bookings.values())}
        before = f.before['budget']
        child = f.correct()
        correction = child['body']['source_correction']
        self.assertEqual(correction['schema'], 'native-calibration-source-correction/4')
        self.assertEqual(correction['predecessor_pool_id'], f.predecessor['id'])
        self.assertEqual(correction['predecessor_checkpoint'], f.before['resource_checkpoint'])
        self.assertEqual(correction['predecessor_reference_id'], f.reference['id'])
        self.assertEqual(correction['predecessor_source_result_id'], f.source_result['id'])
        self.assertEqual(correction['operational_start_utc'], f.clock.dependency.first.control.binding['operational_start_utc'])
        self.assertEqual(correction['terminal_event_prefix'], f.receipt['event_prefix'])
        self.assertEqual(child['body']['carry'], {'schema': 'native-calibration-resource-carry/1',
            'basis_id': f.predecessor['id'], **{key: before[key] for key in (
                'charged_compute_ms', 'charged_storage_bytes', 'allocated_compute_ms', 'allocated_storage_bytes',
                'grants_used', 'progress_units', 'no_progress_grants')}, 'last_grant_progress': history.last_grant_progress})
        after = f.manager.inspect(f.token, child['id'])['budget']
        self.assertEqual(after['charged_storage_bytes'], before['charged_storage_bytes'] + MIB)
        for key in ('charged_compute_ms', 'allocated_compute_ms', 'allocated_storage_bytes',
                    'grants_used', 'progress_units', 'no_progress_grants'):
            self.assertEqual(after[key], before[key])
        self.assertEqual(after['grants_used'], 1)
        self.assertEqual(after['grants_remaining'], 178)
        self.assertFalse(after['halted'])
        self.assertFalse(after['usage_uncertain'])
        self.assertFalse(after['overrun'])
        self.assertFalse(after['outstanding_attempts'])
        self.assertTrue(f.view()['budget']['halted'])
        self.assertEqual(f.correct(), child)
        with self.assertRaises(ERRORS):
            f.correct(args={**f.args, 'key': 'another-host-correction-key'})
        with f.pinned():
            current = controller.NativeCalibrationController(f.broker, correction['controller_directory'],
                driver_file=f.clock.control.driver_file)
            self.assertEqual(current.prepare(f.token, f.args['key'], correction_args=f.args), child)
            self.assertEqual(current.binding['policy'], controller.policy())
            self.assertEqual(current.binding['policy']['acceptance_deadline_ms'], 600000)
            self.assertEqual(current.binding['operational_start_utc'], correction['operational_start_utc'])
            dependencies = f.broker._dependency_use(child['id'])
            self.assertEqual(dependencies['status'], 'NOT_REVOKED')
            self.assertIn(f.predecessor['id'], dependencies['checked_versions'])
        for identity, raw in old.items():
            self.assertEqual(canonical(f.broker._artifact(identity)), raw)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 5)
        self.assertFalse(f.manager._objects('native-family-calibration-input/1'))
        for stage in ('intent', 'ack'):
            self.assertTrue(Path(str(f.receipt_path) + '.source-correction-' + stage + '.json').is_file())
        self.assertIs(child['body']['scientific_readiness'], False)

    def test_wrong_exact_ids_profile_amendment_or_ancestor_and_any_final_input_deny_before_intent(self):
        f = self.fixture()
        for field in ('qualification_id', 'failed_setup_artifact_id', 'reference_id',
                      'ancestor_pool_id', 'old_profile_sha256', 'new_profile_sha256', 'host_amendment_sha256'):
            with self.subTest(field=field):
                self.assert_denied_without_successor(f, pins={**f.pins, field: 'f' * 64})
        f.financial.save({'schema': 'native-family-calibration-input/1', 'created_at': 1,
                          'scientific_readiness': False}, refs=[f.reference['id']])
        self.assert_denied_without_successor(f)

    def test_wrong_failed_qualification_status_or_host_failure_is_not_recoverable(self):
        for variant in ('wrong_qualification', 'wrong_failure'):
            with self.subTest(variant=variant):
                self.assert_denied_without_successor(self.fixture(variant=variant))

    def test_pending_acceptance_or_unrelated_source_change_cannot_use_host_exception(self):
        for variant in ('pending', 'acceptance', 'forbidden_source'):
            with self.subTest(variant=variant):
                self.assert_denied_without_successor(self.fixture(variant=variant))


if __name__ == '__main__':
    unittest.main()
