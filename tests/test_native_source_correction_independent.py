"""Independent one-shot pre-final source-correction controls.

Disposable actual Registry/ledger/full-copy paths use explicitly synthetic
financial history and trusted fixture pins. No actual Registry, native/scalar
numerical work, certificate use or study restart is authorized by these tests.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

import test_native_calibration_resource_owner_independent as financial_support
import test_native_study_independent as native_support
import test_native_runtime_independent as runtime_support
import test_native_reference_caller_independent as reference_support
from trading_researcher import family_study, native_calibration_controller as controller
from trading_researcher import native_study_runs, study_runs, native_study_pipeline as pipeline
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.evaluation_plans import footprint, source_bundle
from trading_researcher.storage import restore_bundle
from trading_researcher.native_qualification import NativeQualifications

from trading_researcher import native_calibration_runs as owner


MIB = 1048576
ERRORS = (Invalid, Conflict, Denied, OSError)
PROJECT = Path(__file__).resolve().parents[1]
OLD_COORDINATION = 'd335e3ec64c2c82a6bcf8ad56ff3a8059c1590bd272b727d253a5d662769982b'
FIXED_COORDINATION = '25c67fa1d48371108aa1e91f630d953cc5e7e33e5615f503feadb851e3782dfc'
FAILURES = [('InterfaceError', 'bad parameter or other API misuse')] * 3 + [
    ('Denied', 'Artifact unavailable')] * 2 + [('Invalid', 'Expecting value: line 1 column 1 (char 0)')]


def previous_source():
    """Historical source transport only; archived code is never executed."""
    source = source_bundle()
    current = source['trading_researcher/coordination.py']
    assert current.count(b', cached_statements=0') == 1
    old = current.replace(b', cached_statements=0', b'', 1)
    assert hashlib.sha256(old).hexdigest() == OLD_COORDINATION
    assert hashlib.sha256(current).hexdigest() == FIXED_COORDINATION
    return {**source, 'trading_researcher/coordination.py': old}


@contextmanager
def historical_source(source):
    with patch.object(owner, 'LOADED_SOURCE', footprint(source)), \
            patch.object(owner, 'source_bundle', return_value=source):
        yield


class CorrectionFixture:
    """Actual immutable financial/copy owners; synthetic pre-child failures.

    The pin seam substitutes fixture IDs, keeping the exact archived/current
    coordination SHA pair. This small fixture's reference is metadata only;
    separate genuine-reference cases exercise actual corpus preparation.
    """
    def __init__(self, root, *, broker=None, authority=None, reference=None,
                 old_source=None, variant=None):
        self.root = Path(root)
        self.financial = None
        if broker is None:
            self.financial = financial_support.RetiredFinancialFixture(self.root)
            broker, authority = self.financial.broker, self.financial.authority
        self.broker, self.token = broker, broker.admin_token
        self.authority = deepcopy(authority)
        self.old_source = old_source or previous_source()
        if variant == 'forbidden_source':
            self.old_source = dict(self.old_source)
            self.old_source['trading_researcher/codec.py'] += b'\n# Unsupported historical semantic change.\n'
        self.authority_patch = patch.object(owner.NativeCalibrationResources, '_read_authority',
                                           side_effect=lambda: deepcopy(self.authority))
        self.authority_patch.start()
        try:
            with historical_source(self.old_source):
                self.manager = owner.NativeCalibrationResources(broker)
                driver = self.root / 'fixture-native-driver.py'
                driver.write_bytes(b'# Pinned synthetic driver; never executed.\n')
                self.control = controller.NativeCalibrationController(broker, self.root / 'old-controller', driver_file=driver)
                self.pool = self.control.prepare(self.token, 'independent-pre-final-old-pool')
                self.source_result = broker._artifact(self.control.binding['source_result_id'])
                if reference is None:
                    f = self.financial
                    profile = deepcopy(f.study['body']['manifest']['profile'])
                    profile.update(worlds_per_cell=1, targets=[15, 16])
                    manifest = family_study.make_manifest(f.study['body']['manifest']['assigned'], profile)
                    reference = f.save({'schema': 'native-calibration-reference-input/1', 'created_at': 1,
                        'request': {'key': 'synthetic-pre-child-reference',
                            'development_study_id': f.recovery_source['id'],
                            'native_qualification_id': f.recovery_source['id']},
                        'payload': deepcopy(f.study['body']['payload']), 'manifest': manifest,
                        'source_footprint': footprint(self.old_source), 'references': {},
                        'native_binding': {'runtime_id': f.recovery_source['id']},
                        'process_control': {'schema': 'native-study-process-control/1',
                            'library_threads': 1, 'priority': 'BELOW_NORMAL'},
                        'scientific_readiness': False}, refs=[f.recovery_source['id']])
                self.reference = reference
                self.copies = owner.NativeCalibrationCopies(broker)
                self.bookings = {label: self.copies.book(self.token, self.pool['id'], label)
                                 for label in ('prepared', 'terminal')}
                tasks = owner.NativeCalibrationReferences.tasks(reference)
                self.inventory = self.manager.bind_inventory(self.token, {
                    'key': 'pre-child-acceptance', 'pool_id': self.pool['id'], 'phase': 'acceptance',
                    'task_ids': sorted(tasks), 'execution_deadline_ms': 10000,
                    'attempt_compute_ms': 15000, 'attempt_storage_bytes': 256 * MIB,
                    'max_attempts': 1, 'expected_checkpoint': self.view()['resource_checkpoint']}, input_id=reference['id'])
                selected = sorted(task for task, value in tasks.items() if value['mode'] == 'parallel')[:6]
                assert len(selected) == 6
                reservations = [self.manager.reserve(self.token, {'pool_id': self.pool['id'],
                    'phase': 'acceptance', 'task_id': task, 'attempt_id': format(index + 100, '032x'),
                    'expected_checkpoint': self.view()['resource_checkpoint']}) for index, task in enumerate(selected)]
                self.failed = []
                for index, reservation in enumerate(reservations):
                    if variant == 'pending' and index == 5:
                        continue
                    task = tasks[reservation['task_id']]
                    failure = dict(zip(('type', 'message'), FAILURES[index]))
                    if variant == 'wrong_failure' and index == 5:
                        failure['message'] = 'A different unsupported protocol failure'
                    settlement = {'attempt_id': reservation['attempt_id'], 'compute_ms': 11 + index,
                        'storage_bytes': MIB, 'usage_known': not (variant == 'unknown' and index == 5)}
                    if variant == 'overrun' and index == 5:
                        settlement['compute_ms'] = reservation['compute_ms'] + 1
                    self.failed.append(self.manager.settle(self.token, self.pool['id'], {
                        'resource_pool_id': self.pool['id'], 'phase': 'acceptance',
                        'task_id': reservation['task_id'], 'attempt_id': reservation['attempt_id'],
                        'study_id': reference['id'], 'reference_id': reference['id'],
                        'world_id': task['world_id'], 'reference_mode': task['mode'],
                        'resource_state': 'FAILED', 'currency_checked': True,
                        'failure': failure, 'failures': [failure], 'settlement': settlement,
                        'result': None, 'replay_result': None, 'proofs': [], 'output_blobs': {},
                        'custody': {'schema': 'native-attempt-custody/1', 'binding': {}, 'phases': []}}))
                self.receipt_path = self.copies.receipt_path(self.pool['id'], 'terminal')
                self.backup, self.restored = self.root / 'old-terminal-backup', self.root / 'old-terminal-restore'
                if variant not in ('pending', 'unknown', 'overrun'):
                    self.receipt = self.copies.create(self.token, self.pool['id'], 'terminal',
                        backup_directory=self.backup, restore_directory=self.restored, receipt_path=self.receipt_path)
            self.original_pool_bytes = canonical(broker._artifact(self.pool['id']))
            self.before = deepcopy(self.view())
            self.pins = {**dict(owner.SOURCE_CORRECTION), 'predecessor_pool_id': self.pool['id'],
                'expected_checkpoint': self.before['resource_checkpoint'], 'reference_id': reference['id'],
                'source_result_id': self.source_result['id']}
            self.args = {'key': 'one-independent-correction', 'predecessor_pool_id': self.pool['id'],
                'expected_checkpoint': self.pins['expected_checkpoint'], 'terminal_receipt_path': str(self.receipt_path)}
            self.operator_key = self.root / 'fixture-operator.key'
            self.operator_key.write_bytes((broker.directory / 'operator.key').read_bytes())
        except BaseException:
            self.close()
            raise

    def view(self):
        return self.manager.inspect(self.token, self.pool['id'])

    def correct(self, **changes):
        with patch.object(owner, 'SOURCE_CORRECTION', self.pins):
            return self.manager.correct_source(self.token, {**self.args, **changes})

    def close(self):
        self.authority_patch.stop()
        self.broker.close()


class NativeSourceCorrectionFinancialIndependentTests(unittest.TestCase):
    def fixture(self, **options):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-source-correction-')
        self.addCleanup(temporary.cleanup)
        result = CorrectionFixture(Path(temporary.name), **options)
        self.addCleanup(result.close)
        return result

    def assert_no_successor(self, f):
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 1)
        self.assertEqual(canonical(f.broker._artifact(f.pool['id'])), f.original_pool_bytes)

    def test_one_child_preserves_every_charge_limit_grant_progress_and_original_operational_start(self):
        f = self.fixture()
        before = f.before['budget']
        old_rows = {item['id']: canonical(f.broker._artifact(item['id']))
                    for item in [f.pool, f.reference, f.source_result, *f.failed]}
        child = f.correct()
        body = child['body']; carry = body['carry']
        self.assertEqual(body['schema'], 'native-calibration-resource-pool/1')
        self.assertEqual(carry, {'schema': 'native-calibration-resource-carry/1', 'basis_id': f.pool['id'],
            **{key: before[key] for key in ('charged_compute_ms', 'charged_storage_bytes',
                'allocated_compute_ms', 'allocated_storage_bytes', 'grants_used', 'progress_units', 'no_progress_grants')},
            'last_grant_progress': f.manager._history(f.pool).last_grant_progress})
        after = f.manager.inspect(f.token, child['id'])
        self.assertEqual(after['budget']['charged_storage_bytes'], before['charged_storage_bytes'] + MIB)
        for key in ('charged_compute_ms', 'allocated_compute_ms', 'allocated_storage_bytes',
                    'grants_used', 'progress_units', 'no_progress_grants'):
            self.assertEqual(after['budget'][key], before[key])
        self.assertEqual(after['budget']['grants_remaining'], 178)
        self.assertFalse(after['budget']['outstanding_attempts'])
        self.assertFalse(after['budget']['halted'])
        self.assertTrue(f.view()['budget']['halted'])
        self.assertEqual(set(body['setup_tasks']), {'controller_source', 'runtime_retain', 'runtime_qualification',
            'acceptance_summary', 'prepare_reference_input', 'prepare_final_input', 'prepared_copies', 'terminal_copies'})
        self.assertTrue(set(body['setup_tasks'].values()).isdisjoint(f.pool['body']['setup_tasks'].values()))
        correction = body['source_correction']
        self.assertEqual(correction['schema'], 'native-calibration-source-correction/1')
        self.assertEqual(correction['request'], f.args)
        self.assertEqual(correction['predecessor_pool_id'], f.pool['id'])
        self.assertEqual(correction['predecessor_checkpoint'], f.before['resource_checkpoint'])
        self.assertEqual(correction['predecessor_reference_id'], f.reference['id'])
        self.assertEqual(correction['predecessor_source_result_id'], f.source_result['id'])
        self.assertEqual(correction['operational_start_utc'], f.control.binding['operational_start_utc'])
        self.assertEqual(correction['controller_directory'],
                         str(f.control.directory.parent / 'source-correction' / 'actual-run'))
        self.assertEqual(correction['runtime_id'], f.reference['body']['native_binding']['runtime_id'])
        self.assertEqual(correction['terminal_event_prefix'], f.receipt['event_prefix'])
        self.assertEqual(correction['terminal_receipt_sha256'], hashlib.sha256(f.receipt_path.read_bytes()).hexdigest())
        self.assertEqual(body['source_footprint'], footprint(source_bundle()))
        self.assertIs(body['scientific_readiness'], False)
        self.assertIn(f.pool['id'], f.broker._dependency_use(child['id'])['checked_versions'])
        self.assertEqual(f.correct(), child)
        self.assertEqual(f.manager.inspect(f.token, child['id']), after)
        for identity, raw in old_rows.items():
            self.assertEqual(canonical(f.broker._artifact(identity)), raw)
        for changes in ({'key': 'second-key'}, {'expected_checkpoint': 'f' * 64},
                        {'predecessor_pool_id': child['id']}):
            with self.subTest(changes=changes), self.assertRaises(ERRORS): f.correct(**changes)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 2)

    def test_worker_and_public_forgery_are_denied_before_private_lookup(self):
        f = self.fixture()
        worker = f.broker.call(f.token, 'register_worker', name='correction-worker', role='discovery', capabilities=[])['token']
        with patch.object(f.broker, '_artifact', side_effect=AssertionError('Private lookup before authentication')):
            with self.assertRaises(Denied): f.manager.correct_source(worker, f.args)
        for extra in ({'approved': True}, {'carry': {}}, {'budget': {'max_compute_ms': 648000001}}):
            with self.subTest(extra=extra), patch.object(owner, 'SOURCE_CORRECTION', f.pins), self.assertRaises(ERRORS):
                f.manager.correct_source(f.token, {**f.args, **extra})
        self.assert_no_successor(f)

    def test_pending_unknown_and_overrun_prefixes_never_gain_a_successor(self):
        for variant in ('pending', 'unknown', 'overrun'):
            with self.subTest(variant=variant):
                f = self.fixture(variant=variant)
                before = deepcopy(f.view())
                with self.assertRaises(ERRORS): f.correct()
                self.assertEqual(f.view(), before)
                self.assert_no_successor(f)

    def test_different_failure_or_semantic_source_change_cannot_use_the_narrow_exception(self):
        for variant in ('wrong_failure', 'forbidden_source'):
            with self.subTest(variant=variant):
                f = self.fixture(variant=variant)
                with self.assertRaises(ERRORS): f.correct()
                self.assert_no_successor(f)

    def test_any_native_final_input_closes_the_pre_final_source_correction_path(self):
        f = self.fixture()
        # Negative typed-metadata seam only: no final input is qualified or run.
        f.financial.save({'schema': 'native-family-calibration-input/1', 'created_at': 1,
            'scientific_readiness': False}, refs=[f.reference['id']])
        with self.assertRaises(ERRORS): f.correct()
        self.assert_no_successor(f)

    def test_current_source_and_predecessor_withdrawal_are_required(self):
        f = self.fixture()
        with patch.object(owner, 'source_bundle', return_value={}):
            with self.assertRaises(ERRORS): f.correct()
        evidence = f.broker.call(f.token, 'add_source', data_class='development', body={'synthetic_source_withdrawal': True})
        f.broker.call(f.token, 'revoke_dependency', key='withdraw-old-source-pool', dependency_id=f.pool['id'],
            reason='Synthetic pre-final source withdrawal.', evidence_refs=[evidence['id']])
        with self.assertRaises(ERRORS): f.correct()
        self.assert_no_successor(f)

    def test_historical_terminal_guard_rejects_changed_primary_prefix_and_corrupted_fullcopy(self):
        f = self.fixture()
        receipt_bytes = f.receipt_path.read_bytes()
        f.broker.call(f.token, 'add_source', data_class='operations', body={'later_primary_prefix': True})
        with self.assertRaises(ERRORS): f.correct()
        self.assertEqual(f.receipt_path.read_bytes(), receipt_bytes)
        self.assert_no_successor(f)
        other = self.fixture()
        row = other.broker._db.execute('SELECT sha256 FROM blobs ORDER BY sha256 LIMIT 1').fetchone()
        path = other.backup / 'blobs' / row[0][:2] / row[0]
        original = path.read_bytes(); path.write_bytes(original + b'corrupted-owned-copy')
        with self.assertRaises(ERRORS): other.correct()
        self.assert_no_successor(other)

    def test_final_commit_failure_rolls_back_child_inventory_and_key_without_reset_or_retry(self):
        f = self.fixture()
        before = f.view()
        original_event = f.manager._event
        def interrupted(action, *args, **kwargs):
            if action == 'native_calibration_pool_key':
                raise RuntimeError('Synthetic source-correction final commit interruption')
            return original_event(action, *args, **kwargs)
        with patch.object(f.manager, '_event', side_effect=interrupted):
            with self.assertRaisesRegex(RuntimeError, 'Synthetic source-correction final commit interruption'):
                f.correct()
        self.assertEqual(f.view(), before)
        self.assert_no_successor(f)
        # External intent must prevent an unaccounted automatic replay after
        # the SQL rollback; no heavy work/authority is inferred from an intent.
        with self.assertRaises(ERRORS): f.correct()
        self.assert_no_successor(f)

    def test_lost_ack_can_only_reconcile_the_already_committed_child_without_another_fee(self):
        f = self.fixture()
        child = f.correct()
        before = f.manager.inspect(f.token, child['id'])
        ack = Path(str(f.receipt_path) + '.source-correction-ack.json')
        retained = f.root / 'retained-original-source-correction-ack.json'
        raw = ack.read_bytes()
        ack.rename(retained)
        with self.assertRaises(ERRORS): f.manager._current(child)
        self.assertEqual(f.correct(), child)
        self.assertEqual(ack.read_bytes(), raw)
        self.assertEqual(retained.read_bytes(), raw)
        self.assertEqual(f.manager.inspect(f.token, child['id']), before)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 2)

    def test_missing_intent_or_tampered_intent_or_ack_denies_new_use_without_rebinding(self):
        f = self.fixture()
        child = f.correct()
        before = f.manager.inspect(f.token, child['id'])
        for stage in ('intent', 'ack'):
            path = Path(str(f.receipt_path) + '.source-correction-' + stage + '.json')
            raw = path.read_bytes()
            changed = decode(raw); changed['source_footprint_sha256'] = 'f' * 64
            path.write_text(canonical(changed), encoding='utf-8')
            with self.subTest(stage=stage):
                with self.assertRaises(ERRORS): f.manager._current(child)
                with self.assertRaises(ERRORS): f.correct()
            path.write_bytes(raw)
        intent = Path(str(f.receipt_path) + '.source-correction-intent.json')
        retained = f.root / 'retained-original-source-correction-intent.json'
        intent.rename(retained)
        with self.assertRaises(ERRORS): f.manager._current(child)
        with self.assertRaises(ERRORS): f.correct()
        self.assertEqual(f.manager.inspect(f.token, child['id']), before)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 2)

    def test_child_creation_restore_cannot_rebook_controller_source_in_a_new_directory(self):
        f = self.fixture()
        child = f.correct()
        child_prefix_backup = f.root / 'child-creation-prefix-backup'
        self.assertEqual(f.broker.call(f.token, 'backup_bundle', destination=str(child_prefix_backup))['status'], 'PASS')
        first = controller.NativeCalibrationController(f.broker, f.control.directory.parent / 'source-correction' / 'actual-run',
                                                       driver_file=f.control.driver_file)
        with patch.object(owner, 'SOURCE_CORRECTION', f.pins):
            self.assertEqual(first.prepare(f.token, f.args['key'], correction_args=f.args), child)
        source_result = f.broker._artifact(first.binding['source_result_id'])
        self.assertEqual(source_result['body']['settlement']['storage_bytes'],
                         2 * f.control.driver_file.stat().st_size + 17 * MIB)
        original, retained = f.broker.directory, f.root / 'retained-primary-with-corrected-source-charge'
        self.assertTrue(original.resolve().is_relative_to(f.root.resolve()))
        self.assertTrue(retained.resolve().is_relative_to(f.root.resolve()))
        f.broker.close(); original.rename(retained)
        self.assertEqual(restore_bundle(child_prefix_backup, original, f.operator_key)['status'], 'PASS')
        f.broker = financial_support.Broker(original); f.token = f.broker.admin_token
        f.manager = owner.NativeCalibrationResources(f.broker)
        before = f.manager.inspect(f.token, child['id'])
        second = controller.NativeCalibrationController(f.broker, f.root / 'corrected-controller-B',
                                                        driver_file=f.control.driver_file)
        with patch.object(owner, 'SOURCE_CORRECTION', f.pins), self.assertRaises(ERRORS):
            second.prepare(f.token, f.args['key'], correction_args=f.args)
        same_directory = controller.NativeCalibrationController(f.broker, first.directory,
                                                                driver_file=f.control.driver_file)
        with patch.object(owner, 'SOURCE_CORRECTION', f.pins), self.assertRaises(ERRORS):
            same_directory.prepare(f.token, f.args['key'], correction_args=f.args)
        self.assertEqual(f.manager.inspect(f.token, child['id']), before)
        self.assertTrue((retained / 'registry.sqlite3').is_file())

    def test_correction_directory_claim_survives_failure_before_source_reservation_and_cannot_reset(self):
        f = self.fixture()
        child = f.correct()
        directory = f.control.directory.parent / 'source-correction' / 'actual-run'
        current = controller.NativeCalibrationController(f.broker, directory, driver_file=f.control.driver_file)
        before = f.manager.inspect(f.token, child['id'])
        with patch.object(owner, 'SOURCE_CORRECTION', f.pins), \
                patch.object(current.resources, 'reserve', side_effect=RuntimeError('Synthetic interruption before source reserve')):
            with self.assertRaisesRegex(RuntimeError, 'Synthetic interruption before source reserve'):
                current.prepare(f.token, f.args['key'], correction_args=f.args)
        self.assertTrue(directory.is_dir())
        self.assertFalse((directory / 'binding.json').exists())
        self.assertEqual(f.manager.inspect(f.token, child['id']), before)
        reopened = controller.NativeCalibrationController(f.broker, directory, driver_file=f.control.driver_file)
        with patch.object(owner, 'SOURCE_CORRECTION', f.pins), self.assertRaises(ERRORS):
            reopened.prepare(f.token, f.args['key'], correction_args=f.args)
        self.assertEqual(f.manager.inspect(f.token, child['id']), before)

    def test_existing_child_key_without_correction_args_still_inherits_clock_and_enforces_directory(self):
        for scenario in ('fixed_directory', 'different_directory'):
            with self.subTest(scenario=scenario):
                f = self.fixture()
                child = f.correct()
                expected = child['body']['source_correction']
                directory = (Path(expected['controller_directory']) if scenario == 'fixed_directory'
                             else f.root / 'unbound-correction-controller-directory')
                current = controller.NativeCalibrationController(f.broker, directory, driver_file=f.control.driver_file)
                before = f.manager.inspect(f.token, child['id'])
                if scenario == 'different_directory':
                    with self.assertRaises(ERRORS):
                        current.prepare(f.token, f.args['key'])
                    self.assertEqual(f.manager.inspect(f.token, child['id']), before)
                else:
                    self.assertEqual(current.prepare(f.token, f.args['key']), child)
                    self.assertEqual(current.binding['operational_start_utc'], expected['operational_start_utc'])
                    self.assertEqual(current.binding['run_directory'], expected['controller_directory'])
                    self.assertEqual(current.validate(f.token, child['id']), current.binding)

    def test_restoring_old_terminal_prefix_cannot_mint_a_second_successor_or_forget_first_fee(self):
        f = self.fixture()
        child = f.correct()
        after = f.manager.inspect(f.token, child['id'])
        self.assertEqual(after['budget']['charged_storage_bytes'], f.before['budget']['charged_storage_bytes'] + MIB)
        original, retained = f.broker.directory, f.root / 'retained-primary-after-source-correction'
        self.assertTrue(original.resolve().is_relative_to(f.root.resolve()))
        self.assertTrue(retained.resolve().is_relative_to(f.root.resolve()))
        f.broker.close()
        original.rename(retained)
        self.assertEqual(restore_bundle(f.backup, original, f.operator_key)['status'], 'PASS')
        f.broker = financial_support.Broker(original)
        f.token = f.broker.admin_token
        f.manager = owner.NativeCalibrationResources(f.broker)
        before = f.view()
        with self.assertRaises(ERRORS):
            f.correct()
        self.assertEqual(f.view(), before)
        self.assertEqual(len(f.manager._objects('native-calibration-resource-pool/1')), 1)
        self.assertTrue((retained / 'registry.sqlite3').is_file())


class NativeSourceCorrectionEntrypointIndependentTests(unittest.TestCase):
    def test_correction_reference_owner_exists_before_domain_cases(self):
        self.assertTrue(callable(getattr(owner, 'NativeCalibrationCorrectionReferences', None)),
                        'Correction reference entrypoint absent; zero correction domain-flow coverage')


class NativeSourceCorrectionReferenceIndependentTests(unittest.TestCase):
    """Actual completed eight-world corpus; invented numerical/Q responses.

    This deliberately reuses the real input, immutable source/case, separate
    generation/replay, full stream, old continuation and native input owners.
    Neither a binary qualification nor real statistical acceptance is claimed.
    """
    @classmethod
    def setUpClass(cls):
        native_support.NativeStudyIndependentTests.setUpClass()
        cls.addClassCleanup(native_support.NativeStudyIndependentTests.doClassCleanups)
        temporary = tempfile.TemporaryDirectory(prefix='trf-correction-reference-base-')
        cls.addClassCleanup(temporary.cleanup)
        root = Path(temporary.name)
        actual_transport = study_runs.execute_attempt
        builder = native_support.NativeStudyIndependentTests('runTest')
        builder.setUp()
        try:
            wire = reference_support.ReferenceWireFixture(builder)
            with patch.object(study_runs, 'execute_attempt', side_effect=actual_transport), \
                    patch.object(study_runs, '_run_child', side_effect=wire.child), \
                    patch.object(study_runs, '_environment_current',
                        side_effect=lambda value: value == {'invented_environment': 'old-reference'}):
                args = builder.args('source-correction-original-corpus', 'family', native=False,
                                    budget={'max_compute_ms': 10000}, seed=713)
                args['profile']['targets'] = [2, 3]
                cls.development = builder.op('prepare_family_study', **args)
                stopped = builder.op('advance_family_study', study_id=cls.development['id'])
                assert stopped['status'] == 'RESOURCE_STOP'
                cls.old_grant = builder.op('continue_study', **builder.grant(cls.development, stopped,
                    key='source-correction-original-completion'))
                for _ in range(7):
                    complete = builder.op('advance_family_study', study_id=cls.development['id'])
                assert complete['status'] == 'COMPLETE' and len(complete['attempt_artifact_ids']) == 8
                assert len(wire.calls) == 16
            cls.attempts = [builder.broker._artifact(identity) for identity in complete['attempt_artifact_ids']]
            cls.expected_vectors = {a['body']['world_id']: {
                'attempt_id': a['id'], 'result_hash': digest(a['body']['result']),
                'stream_blob': deepcopy(a['body']['proofs'][0]['stream_blob']),
                'stream_encoding': deepcopy(a['body']['proofs'][0]['stream_encoding'])} for a in cls.attempts}
            members = {'example/LICENSE.txt': b'Invented technical membership; not an executable binary.\n',
                pipeline.KERNEL_FILE: b'Invented kernel membership; never executed.\n'}
            builder.raw = runtime_support.archive(members.items())
            builder.runtime_manifest = runtime_support.manifest(members)
            path = builder.root / 'correction-invented-runtime.zip'; path.write_bytes(builder.raw)
            builder.archive_source = builder.op('add_blob_source', path=str(path), data_class='operations',
                description='Synthetic qualification membership seam only; no native code executes.')
            builder.runtime = builder.op('retain_native_runtime', key='correction-invented-runtime',
                archive_id=builder.archive_source['id'], manifest=builder.runtime_manifest)
            builder.qualified = builder.qualification(key='correction-base-qualification')
            with patch.object(financial_support, 'Broker', return_value=builder.broker):
                financial = financial_support.RetiredFinancialFixture(builder.root)
            cls.authority = deepcopy(financial.authority)
            cls.facts = {name: deepcopy(getattr(builder, name)) for name in (
                'project', 'raw', 'runtime_manifest', 'archive_source', 'runtime', 'qualified',
                'cost', 'estimate', 'plans', 'execution', 'diagnostics')}
            cls.backup = root / 'completed-corpus-backup'
            assert builder.op('backup_bundle', destination=str(cls.backup))['status'] == 'PASS'
            cls.operator_key = root / 'operator.key'
            cls.operator_key.write_bytes((builder.directory / 'operator.key').read_bytes())
        finally:
            builder.doCleanups()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-correction-reference-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.s = native_support.NativeStudyIndependentTests('runTest')
        for name, value in self.facts.items(): setattr(self.s, name, deepcopy(value))
        self.s.root, self.s.directory = self.root, self.root / 'registry'
        self.assertEqual(restore_bundle(self.backup, self.s.directory, self.operator_key)['status'], 'PASS')
        self.s.broker = financial_support.Broker(self.s.directory)
        self.addCleanup(self.s.broker.close)
        self.s.token = self.s.broker.admin_token
        self.s.current, self.s.qualification_aliases, self.s.resolve_calls = True, {}, []
        resolver = patch.object(NativeQualifications, '_require_inputs', autospec=True,
            side_effect=lambda instance, identity, **options: self.s.resolve(instance, identity, **options))
        resolver.start(); self.addCleanup(resolver.stop)
        membership = patch.object(native_support.qualification_owner.profile, 'validate_runtime', return_value=None)
        membership.start(); self.addCleanup(membership.stop)
        old_source = previous_source()
        self.s.project = old_source
        old_qualified = self.s.qualification(key='source-correction-old-qualified-namespace')
        self.s.qualified = old_qualified
        with historical_source(old_source), patch.object(native_study_runs, 'LOADED_SOURCE', footprint(old_source)), \
                patch.object(native_study_runs, 'source_bundle', return_value=old_source):
            self.previous = owner.NativeCalibrationReferences(self.s.broker).prepare(self.s.token, {
                'key': 'source-correction-retained-old-reference', 'development_study_id': self.development['id'],
                'native_qualification_id': old_qualified['certificate']['id']})
        self.s.project = source_bundle()
        self.s.qualified = self.s.qualification(key='source-correction-current-qualified-namespace')
        self.s.qualification_aliases[old_qualified['certificate']['id']] = old_qualified
        # Both qualifications and the old reference precede the terminal full
        # snapshot; no post-copy event can accidentally make its prefix stale.
        self.f = CorrectionFixture(self.root, broker=self.s.broker, authority=self.authority,
                                   reference=self.previous, old_source=old_source)
        self.addCleanup(self.f.close)
        self.child = self.f.correct()
        self.ref_owner = owner.NativeCalibrationCorrectionReferences(self.s.broker)
        self.request = {'key': 'same-corpus-corrected-native-reference',
            'development_study_id': self.development['id'],
            'native_qualification_id': self.s.qualified['certificate']['id'],
            'source_correction_pool_id': self.child['id']}
        self.old_bytes = {a['id']: canonical(self.s.broker._artifact(a['id']))
            for a in [self.development, self.previous, *self.attempts]}

    def test_genuine_correction_prepare_retains_full_corpus_and_denies_missing_wrong_or_ordinary_alias(self):
        with patch.object(owner, 'SOURCE_CORRECTION', self.f.pins):
            corrected = self.ref_owner.prepare(self.s.token, self.request)
            self.assertNotEqual(corrected['id'], self.previous['id'])
            for key in ('payload', 'manifest', 'references'):
                self.assertEqual(corrected['body'][key], self.previous['body'][key])
            self.assertEqual(corrected['body']['references'], self.expected_vectors)
            self.assertEqual(len(corrected['body']['manifest']['worlds']), 8)
            self.assertEqual(len(self.ref_owner.tasks(corrected)), 16)
            self.assertEqual(corrected['body']['native_binding']['source_footprint'], footprint(source_bundle()))
            self.assertEqual(corrected['body']['request']['source_correction_pool_id'], self.child['id'])
            self.assertEqual(corrected['body']['native_binding']['runtime_id'],
                             self.previous['body']['native_binding']['runtime_id'])
            self.assertIs(corrected['body']['scientific_readiness'], False)
            self.assertEqual(self.ref_owner.prepare(self.s.token, {**self.request, 'key': 'same-correction-alias'}), corrected)
            self.ref_owner._study_before_execute(corrected)
            for changes in ({'source_correction_pool_id': self.f.pool['id']},
                            {'development_study_id': self.f.reference['id']}):
                with self.subTest(changes=changes), self.assertRaises(ERRORS):
                    self.ref_owner.prepare(self.s.token, {**self.request, **changes, 'key': 'wrong-correction'})
            missing = {key: value for key, value in self.request.items() if key != 'source_correction_pool_id'}
            with self.assertRaises(ERRORS): self.ref_owner.prepare(self.s.token, missing)
            with self.assertRaises(ERRORS):
                owner.NativeCalibrationReferences(self.s.broker).prepare(self.s.token, missing)
        for identity, raw in self.old_bytes.items():
            self.assertEqual(canonical(self.s.broker._artifact(identity)), raw)
        self.assertFalse(self.f.manager._objects('native-family-calibration-input/1'))

    def test_genuine_correction_reference_rechecks_pool_withdrawal_and_original_case_custody(self):
        with patch.object(owner, 'SOURCE_CORRECTION', self.f.pins):
            corrected = self.ref_owner.prepare(self.s.token, self.request)
            self.ref_owner._study_before_execute(corrected)
            descriptor = corrected['body']['payload']['case_blob']
            path = self.s.directory / 'blobs' / descriptor['sha256'][:2] / descriptor['sha256']
            original = path.read_bytes()
            path.write_bytes(original + b'corrupted-owned-case')
            try:
                with self.assertRaises(ERRORS): self.ref_owner._study_before_execute(corrected)
                with self.assertRaises(ERRORS):
                    self.ref_owner.prepare(self.s.token, {**self.request, 'key': 'corrupt-case-alias'})
            finally:
                path.write_bytes(original)
            evidence = self.s.op('add_source', data_class='development', body={'synthetic_corrected_pool_defect': True})
            self.s.op('revoke_dependency', key='withdraw-source-correction-pool', dependency_id=self.child['id'],
                reason='Synthetic source correction dependency withdrawal.', evidence_refs=[evidence['id']])
            with self.assertRaises(ERRORS): self.ref_owner._study_before_execute(corrected)
            with self.assertRaises(ERRORS):
                self.ref_owner.prepare(self.s.token, {**self.request, 'key': 'withdrawn-correction-alias'})
        use = self.s.broker._dependency_use(corrected['id'])
        self.assertEqual(use['status'], 'INVALIDATED_BY_DEPENDENCY')
        self.assertIn(self.child['id'], use['checked_versions'])
        for identity, raw in self.old_bytes.items():
            self.assertEqual(canonical(self.s.broker._artifact(identity)), raw)

    @contextmanager
    def controlled_reference_transport(self):
        """Real reserved caller/transport, invented wire/math/Q and clock only.

        Do not replace the actual caller's base reference_runner or its input
        builder. That precise composition is the regression under test.
        """
        self.s.clock = [0.0]
        clock = types.SimpleNamespace(monotonic=lambda: self.s.clock[0])
        wire = reference_support.ReferenceWireFixture(self.s)
        cancel = threading.Event(); wire.cancel = cancel
        with patch.object(study_runs, 'time', clock), patch.object(owner, 'time', clock), \
                patch.object(pipeline, 'MANIFEST_SHA', digest(self.s.runtime_manifest)), \
                patch.object(pipeline, 'KERNEL_SHA', self.s.runtime_manifest['files'][pipeline.KERNEL_FILE]['sha256']), \
                patch.object(pipeline, 'current', side_effect=lambda value, *args: value == {'invented_environment': 'current'}), \
                patch.object(study_runs, '_run_child', side_effect=wire.child):
            yield owner.NativeCalibrationAttempts(self.s.broker), wire, cancel

    def bind_corrected_acceptance(self, corrected):
        return self.f.manager.bind_inventory(self.s.token, {'key': 'corrected-reserved-caller-corpus',
            'pool_id': self.child['id'], 'phase': 'acceptance',
            'task_ids': sorted(self.ref_owner.tasks(corrected)), 'execution_deadline_ms': 10000,
            'attempt_compute_ms': 15000, 'attempt_storage_bytes': 256 * MIB,
            'max_attempts': 1,
            'expected_checkpoint': self.f.manager.inspect(self.s.token, self.child['id'])['resource_checkpoint']},
            input_id=corrected['id'])

    def reserve_corrected(self, task, index):
        return self.f.manager.reserve(self.s.token, {'pool_id': self.child['id'], 'phase': 'acceptance',
            'task_id': task, 'attempt_id': format(index + 200, '032x'),
            'expected_checkpoint': self.f.manager.inspect(self.s.token, self.child['id'])['resource_checkpoint']})

    def test_actual_reserved_base_caller_completes_both_correction_reference_modes_with_full_replay(self):
        with patch.object(owner, 'SOURCE_CORRECTION', self.f.pins):
            corrected = self.ref_owner.prepare(self.s.token, self.request)
            before_bind = self.f.manager.inspect(self.s.token, self.child['id'])['budget']
            inventory = self.bind_corrected_acceptance(corrected)
            before = self.f.manager.inspect(self.s.token, self.child['id'])['budget']
            self.assertEqual(before['charged_storage_bytes'], before_bind['charged_storage_bytes'] + MIB)
            tasks = self.ref_owner.tasks(corrected)
            world = corrected['body']['manifest']['worlds'][0]['id']
            results = []
            with self.controlled_reference_transport() as (caller, wire, cancel):
                self.assertIs(type(caller.reference_runner), owner.NativeCalibrationReferences)
                for index, mode in enumerate(('serial', 'parallel')):
                    task = next(identity for identity, value in tasks.items()
                                if value == {'world_id': world, 'mode': mode})
                    reserved = self.reserve_corrected(task, index)
                    saved = caller.execute(self.s.token, self.child['id'], reserved['attempt_id'], _cancel=cancel)
                    body = saved['body']; results.append(saved)
                    self.assertEqual(body['resource_state'], 'COMPLETE')
                    self.assertEqual(body['schema'], 'native-calibration-acceptance-attempt/1')
                    self.assertEqual(body['reference_id'], corrected['id'])
                    self.assertEqual(body['reference_mode'], mode)
                    self.assertEqual(body['task_id'], task); self.assertEqual(body['world_id'], world)
                    self.assertEqual(body['resource_inventory_id'], inventory['id'])
                    self.assertEqual(body['reference_comparison'], 'FULL_REFERENCE_MATCH')
                    self.assertIs(body['currency_checked'], True)
                    self.assertIsNone(body['failure']); self.assertEqual(body['failures'], [])
                    self.assertEqual(len(body['proofs']), 2)
                    self.assertEqual(body['replay_result'], {'verified_result_hash': digest(body['result'])})
                    self.assertEqual(body['result'], next(a['body']['result'] for a in self.attempts
                        if a['body']['world_id'] == world))
                    vector = self.expected_vectors[world]
                    for proof in body['proofs']:
                        self.assertEqual(proof['stream_blob'], vector['stream_blob'])
                        self.assertEqual(proof['stream_encoding'], vector['stream_encoding'])
                    stream = body['output_blobs']['generate/stream.jsonl.gz']
                    self.assertEqual(self.s.broker._read_blob_bytes(stream['sha256']),
                                     self.s.broker._read_blob_bytes(vector['stream_blob']['sha256']))
                    self.assertIs(body['settlement']['usage_known'], True)
                    self.assertEqual(body['settlement']['compute_ms'], 2)
                    self.assertGreater(body['settlement']['storage_bytes'], MIB)
                    self.assertLessEqual(body['settlement']['storage_bytes'], reserved['storage_bytes'])
                self.assertEqual([phase for phase, _, _ in wire.calls], ['generate', 'replay', 'generate', 'replay'])
                self.assertFalse(cancel.is_set())
            after = self.f.manager.inspect(self.s.token, self.child['id'])['budget']
            self.assertEqual(after['charged_compute_ms'], before['charged_compute_ms'] + 4)
            self.assertEqual(after['charged_storage_bytes'], before['charged_storage_bytes'] + sum(
                item['body']['settlement']['storage_bytes'] for item in results))
            self.assertEqual(after['progress_units'], before['progress_units'] + 2)
            for field in ('grants_used', 'allocated_compute_ms', 'allocated_storage_bytes'):
                self.assertEqual(after[field], before[field])
            self.assertFalse(after['outstanding_attempts'])
            self.assertFalse(after['usage_uncertain']); self.assertFalse(after['overrun']); self.assertFalse(after['halted'])
        for identity, raw in self.old_bytes.items():
            self.assertEqual(canonical(self.s.broker._artifact(identity)), raw)

    def test_actual_reserved_correction_reference_withdrawal_retains_failed_slot_and_stops_without_child(self):
        with patch.object(owner, 'SOURCE_CORRECTION', self.f.pins):
            corrected = self.ref_owner.prepare(self.s.token, self.request)
            self.bind_corrected_acceptance(corrected)
            task = sorted(self.ref_owner.tasks(corrected))[0]
            reserved = self.reserve_corrected(task, 0)
            evidence = self.s.op('add_source', data_class='development', body={'reserved_correction_withdrawal': True})
            self.s.op('revoke_dependency', key='reserved-correction-qualification-withdrawal',
                dependency_id=self.s.qualified['certificate']['id'],
                reason='Synthetic current qualification withdrawal after reservation.', evidence_refs=[evidence['id']])
            with self.controlled_reference_transport() as (caller, wire, cancel):
                saved = caller.execute(self.s.token, self.child['id'], reserved['attempt_id'], _cancel=cancel)
                self.assertEqual(wire.calls, [])
                self.assertTrue(cancel.is_set())
            body = saved['body']
            self.assertEqual(body['resource_state'], 'FAILED')
            self.assertEqual(body['failure']['type'], 'Denied')
            self.assertIs(body['currency_checked'], False)
            self.assertEqual(body['proofs'], []); self.assertEqual(body['output_blobs'], {})
            self.assertIsNone(body['result']); self.assertIsNone(body['replay_result'])
            self.assertEqual(body['settlement'], {'attempt_id': reserved['attempt_id'],
                'compute_ms': 0, 'storage_bytes': MIB, 'usage_known': True})
            view = self.f.manager.inspect(self.s.token, self.child['id'])
            self.assertFalse(view['budget']['outstanding_attempts'])
            self.assertTrue(view['budget']['halted'])
            self.assertFalse(view['budget']['usage_uncertain'])
            self.assertIn(saved['id'], [item['artifact_id'] for item in self.f.manager._history(self.child).records.values()])
            with self.assertRaises(ERRORS):
                caller.execute(self.s.token, self.child['id'], reserved['attempt_id'])


if __name__ == '__main__':
    unittest.main()
