"""Independent file/control orchestration cases for the fixed recovery driver.

All Brokers, kernel/adapter operations, backup/restore and Windows requests here
are spies. Temporary files are ordinary test records. These cases qualify no
actual2048-world Registry, approval, source host, full restore or numerical use.
The real prepared full-owner roundtrip remains a separate intended-use check.
"""
from copy import deepcopy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock, patch

from trading_researcher.codec import Invalid
from trading_researcher.errors import Conflict, Denied


MODULE = 'tools.calibration.scalar_recovery_run'
STUDY = '8ab8334f134f75145857d8c4975bdf514f854ec00d8680a7831cb9cea5241b96'
OLD_CHECKPOINT = '2e4c3cdea3e3778b54eab106c4fe4596dc933af40f001137e4e43054bd10efa7'
ERRORS = (Invalid, Conflict, Denied, OSError, RuntimeError)


def identity(number):
    return f'{number:064x}'


def view(status='READY', *, attempts=None, grants=None):
    return {
        'study_id': STUDY, 'recovery_id': identity(10), 'input_id': identity(11),
        'original_checkpoint': OLD_CHECKPOINT,
        'prepared_checkpoint': identity(12), 'recovery_checkpoint': identity(13),
        'status': status, 'source_failure': None,
        'attempt_artifact_ids': list(attempts if attempts is not None else [identity(1), identity(2)]),
        'continuation_ids': list(grants if grants is not None else [identity(3)]),
        'next_world_id': identity(20) if status == 'READY' else None,
        'summary': {'complete': status == 'COMPLETE', 'planned_worlds': 2048,
            'recorded_worlds': 2, 'cells': [{'states': {
                'VERIFIED': 1, 'INFORMATION_GAP': 0, 'TECHNICAL_FAILURE': 1, 'MODEL_GAP': 0}}]},
        'budget': {'charged_compute_ms': 5_029_797,
            'charged_storage_bytes': 887_970_493, 'max_compute_ms': 7_200_000,
            'max_storage_bytes': 8 * 1024**3, 'continuation_count': 1,
            'outstanding_attempts': [], 'current_overrun': False,
            'usage_uncertain': status == 'USAGE_UNCERTAIN',
            'next_reservation_fits': status == 'READY'},
        'scientific_readiness': False, 'n_min': None,
    }


class ScalarRecoveryDriverPreimplementationTests(unittest.TestCase):
    def test_required_driver_entrypoint_exists_without_execution_claim(self):
        self.assertIsNotNone(importlib.util.find_spec(MODULE),
            'Fixed recovery driver is absent:0 new driver-flow coverage')
        driver = importlib.import_module(MODULE)
        for name in ('check_observed_prefix', 'save', 'host_and_authority',
                     'prepare', 'run', 'main', 'observe', 'terminal_copies', '_execution_state'):
            self.assertTrue(callable(getattr(driver, name, None)), name)


class ScalarRecoveryDriverIndependentTests(unittest.TestCase):
    def setUp(self):
        self.driver = importlib.import_module(MODULE)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.work = self.root / 'work'
        self.host = self.root / 'recovery-host'
        self.primary = self.work / 'registry'
        for directory in (self.work, self.host, self.primary):
            directory.mkdir(parents=True, exist_ok=True)
        for filename in ('registry.sqlite3', 'operator.key'):
            (self.primary / filename).write_bytes(b'SYNTHETIC TEST FILE; NOT A REGISTRY OR KEY')
        for name, value in {'WORK': self.work, 'HOST': self.host,
                            'PRIMARY': self.primary, 'REPOSITORY': self.root}.items():
            item = patch.object(self.driver, name, value)
            item.start()
            self.addCleanup(item.stop)
        self.authority = {'schema': 'calibration-recovery-authority-binding/1',
            'calibration_id': STUDY, 'registry_path': str(self.primary),
            'assessment_host': str(self.root / 'old-host'),
            'approval_path': str(self.host / 'recovery-approval.json'),
            'approval_sha256': '7aee698e473f0d6106f635bc49627011d672887526940e5396d342fb210a3728',
            'original_approval_path': str(self.host / 'original-approval.json'),
            'original_approval_sha256': '0b0475cab83f5d0c839ee2de9afba67a3b83eb5eb933ca583e251ceead20647a'}
        self.binding = {'schema': 'finite-family-recovery-run-binding/1',
            'authority_binding': deepcopy(self.authority), 'recovery_id': identity(10),
            'artifact_hash': identity(30), 'recovery_artifact_hash': identity(31),
            'request_hash': identity(32), 'manifest_hash': identity(33),
            'assessment_footprint': {}, 'calculation_footprint': {},
            'controller_footprint': {}, 'runtime_identity': {},
            'recovery_path': str(self.work / 'recovery-prepared-proof.json'),
            'recovery_sha256': identity(34), 'driver_files': {}}
        project = Path(__file__).resolve().parents[1]
        for relative in ('tools/calibration/scalar_recovery_run.py',
                         'tools/calibration/finite_family_recovery.py',
                         'tools/calibration/finite_family.py'):
            source = project / relative
            raw = source.read_bytes()
            copied = self.host / relative
            copied.parent.mkdir(parents=True, exist_ok=True)
            copied.write_bytes(raw)
            checksum = hashlib.sha256(raw).hexdigest()
            self.binding['driver_files'][str(source.resolve())] = checksum
            self.binding['driver_files'][str(copied.resolve())] = checksum
        self.broker = Mock(name='SyntheticBroker')
        self.broker.directory = self.primary
        self.broker.admin_token = 'SYNTHETIC_NOT_A_CAPABILITY'
        self.owner = Mock(name='SyntheticRecoveryOwner')
        self.owner.binding = deepcopy(self.authority)
        self.owner.inspect.return_value = view()
        self.owner.recover_incomplete.return_value = {'reconciled': [], 'scientific_readiness': False}
        self.owner._approval_bytes.return_value = {'synthetic': b'not authority'}
        self.owner._original.return_value = {
            'study': {'id': STUDY, 'body': {}},
            'history': SimpleNamespace(checkpoint=OLD_CHECKPOINT),
            'budget': {'charged_compute_ms': 5_029_797, 'charged_storage_bytes': 877_970_493}}

    def patcher(self, name, **kwargs):
        item = patch.object(self.driver, name, **kwargs)
        result = item.start()
        self.addCleanup(item.stop)
        return result

    def write_lines(self, name, records):
        (self.work / name).write_text(''.join(json.dumps(item) + '\n' for item in records),
                                      encoding='utf-8')

    def observation(self, current):
        return {key: deepcopy(current[key]) for key in (
            'study_id', 'recovery_id', 'input_id', 'original_checkpoint',
            'prepared_checkpoint', 'attempt_artifact_ids', 'continuation_ids')}

    def run_spies(self):
        self.patcher('host_and_authority', return_value=deepcopy(self.authority))
        self.patcher('CalibrationRecovery', return_value=self.owner)
        self.patcher('prepare', side_effect=AssertionError('run attempted setup'))
        observe = self.patcher('observe')
        operator = self.driver.operator
        item = patch.object(operator, 'consume_next')
        item.start()
        self.addCleanup(item.stop)
        (self.work / 'recovery-bound-run.json').write_text(json.dumps(self.binding), encoding='utf-8')
        return operator, observe

    def main_spies(self, phase):
        self.patcher('host_and_authority', return_value=deepcopy(self.authority))
        self.patcher('CalibrationRecovery', return_value=self.owner)
        factory = self.patcher('Broker', return_value=self.broker)
        power = self.patcher('_execution_state', return_value=1)
        records = []
        self.patcher('save', side_effect=lambda name, value, **kw: records.append(
            (name, deepcopy(value), kw)))
        self.patcher('terminal_copies', return_value={'status': 'PASS', 'synthetic': True})
        self.patcher('prepare', return_value=(deepcopy(self.binding), view()))
        self.patcher('run', return_value=('COMPLETE_FIXED_INVENTORY_COUNTS_ONLY', view('COMPLETE')))
        self.patcher('sys', new=SimpleNamespace(argv=['scalar_recovery_run.py', phase]))
        return factory, power, records

    def terminal(self, records):
        candidates = [value for _, value, _ in records
                      if isinstance(value, dict) and 'finished_at_utc' in value]
        self.assertEqual(1, len(candidates))
        return candidates[0]

    def test_save_frozen_exact_replay_preserves_bytes_and_rejects_changed_record(self):
        self.driver.save('fixed.json', {'value': 1}, frozen=True)
        initial = (self.work / 'fixed.json').read_bytes()
        self.driver.save('fixed.json', {'value': 1}, frozen=True)
        with self.assertRaises(ERRORS):
            self.driver.save('fixed.json', {'value': 2}, frozen=True)
        self.assertEqual(initial, (self.work / 'fixed.json').read_bytes())

    def test_missing_observations_do_not_invent_unused_history_or_authority(self):
        current = view()
        before = deepcopy(current)
        self.driver.check_observed_prefix(current)
        self.assertEqual(before, current)
        self.assertEqual([], list(self.work.glob('*observations*')))

    def test_matching_old_and_new_ordered_observations_accept_retained_prefix(self):
        current = view(attempts=[identity(1), identity(2), identity(4)],
                       grants=[identity(3), identity(5)])
        self.write_lines('observations.jsonl', [{'study_id': STUDY,
            'last_attempt_id': identity(2), 'continuation_ids': [identity(3)]}])
        previous = view()
        self.write_lines('recovery-observations.jsonl', [self.observation(previous)])
        self.driver.check_observed_prefix(current)

    def test_old_observed_attempt_or_grant_cannot_be_forgotten(self):
        for record in ({'study_id': STUDY, 'last_attempt_id': identity(99),
                        'continuation_ids': [identity(3)]},
                       {'study_id': STUDY, 'last_attempt_id': identity(2),
                        'continuation_ids': [identity(99)]}):
            with self.subTest(record=record):
                self.write_lines('observations.jsonl', [record])
                with self.assertRaises(ERRORS):
                    self.driver.check_observed_prefix(view())

    def test_new_observed_identity_or_ordered_prefix_cannot_be_rewritten(self):
        current = view()
        for field in ('study_id', 'recovery_id', 'input_id',
                      'original_checkpoint', 'prepared_checkpoint',
                      'attempt_artifact_ids', 'continuation_ids'):
            record = self.observation(current)
            record[field] = ([identity(99)] if isinstance(record[field], list) else identity(99))
            with self.subTest(field=field):
                self.write_lines('recovery-observations.jsonl', [record])
                with self.assertRaises(ERRORS):
                    self.driver.check_observed_prefix(current)
        record = self.observation(current)
        record['attempt_artifact_ids'].reverse()
        self.write_lines('recovery-observations.jsonl', [record])
        with self.assertRaises(ERRORS):
            self.driver.check_observed_prefix(current)

    def test_malformed_observation_is_denial_not_automatic_reset(self):
        path = self.work / 'recovery-observations.jsonl'
        path.write_bytes(b'{broken-json\n')
        with self.assertRaises(ERRORS):
            self.driver.check_observed_prefix(view())
        self.assertEqual(b'{broken-json\n', path.read_bytes())

    def test_loaded_driver_outside_the_fixed_host_has_no_authority(self):
        # This is a negative structural check only; no fake host is qualified.
        with self.assertRaises(ERRORS):
            self.driver.host_and_authority()

    def test_existing_intent_or_binding_never_invokes_another_core_prepare(self):
        self.patcher('host_and_authority', return_value=deepcopy(self.authority))
        factory = self.patcher('CalibrationRecovery', return_value=self.owner)
        for name in ('recovery-prepare-intent.json', 'recovery-bound-run.json'):
            path = self.work / name
            path.write_text('{}\n', encoding='utf-8')
            with self.subTest(name=name), self.assertRaises(ERRORS):
                self.driver.prepare(self.broker)
            path.unlink()
        self.owner.prepare.assert_not_called()
        self.broker.call.assert_not_called()

    def test_intent_is_durable_before_core_prepare_and_failed_setup_cannot_restart(self):
        self.patcher('host_and_authority', return_value=deepcopy(self.authority))
        self.patcher('CalibrationRecovery', return_value=self.owner)
        original = RuntimeError('Synthetic core setup interruption')
        def interrupted(*args, **kwargs):
            marker = self.work / 'recovery-prepare-intent.json'
            self.assertTrue(marker.is_file())
            self.assertIsInstance(json.loads(marker.read_text(encoding='utf-8')), dict)
            self.assertFalse((self.work / 'recovery-bound-run.json').exists())
            raise original
        self.owner.prepare.side_effect = interrupted
        disk = shutil.disk_usage(self.work)
        with patch('shutil.disk_usage', return_value=disk._replace(free=1 << 50)), \
                self.assertRaises(RuntimeError) as caught:
            self.driver.prepare(self.broker)
        self.assertIs(original, caught.exception)
        retained = (self.work / 'recovery-prepare-intent.json').read_bytes()
        with self.assertRaises(ERRORS):
            self.driver.prepare(self.broker)
        self.assertEqual(1, self.owner.prepare.call_count)
        self.assertEqual(retained, (self.work / 'recovery-prepare-intent.json').read_bytes())
        self.broker.call.assert_not_called()

    def test_both_operator_stop_sentinels_prevent_dispatch_and_setup(self):
        operator, observe = self.run_spies()
        for filename in ('recovery-stop-after-current-world.request',
                         'stop-after-current-world.request'):
            marker = self.work / filename
            marker.write_bytes(b'operator stop')
            with self.subTest(filename=filename):
                status, current = self.driver.run(self.broker, deepcopy(self.binding), 0)
                self.assertEqual('STOPPED_AT_SAFE_BOUNDARY_BY_OPERATOR', status)
                self.assertEqual(STUDY, current['study_id'])
            marker.unlink()
        operator.consume_next.assert_not_called()
        self.owner.prepare.assert_not_called()

    def test_first_new_uncertain_result_is_observed_once_and_never_retried(self):
        operator, observe = self.run_spies()
        stopped = view('USAGE_UNCERTAIN', attempts=[identity(1), identity(2), identity(4)])
        operator.consume_next.return_value = {'request': {'op': 'advance_calibration_recovery'},
            'view': stopped, 'result_id': identity(4)}
        with self.assertRaises(ERRORS):
            self.driver.run(self.broker, deepcopy(self.binding), 0)
        self.assertEqual(1, operator.consume_next.call_count)
        self.assertTrue(any(call.args[1] == stopped and call.kwargs.get('result_id') == identity(4)
                            for call in observe.call_args_list))
        self.owner.prepare.assert_not_called()

    def test_reconciled_orphan_state_never_reaches_consuming_dispatch(self):
        operator, observe = self.run_spies()
        self.owner.recover_incomplete.return_value = {'reconciled': [identity(50)],
                                                     'scientific_readiness': False}
        self.owner.inspect.return_value = view('ORPHAN_UNCERTAIN')
        with self.assertRaises(ERRORS):
            self.driver.run(self.broker, deepcopy(self.binding), 0)
        operator.consume_next.assert_not_called()
        self.owner.prepare.assert_not_called()

    def test_completion_performs_no_renewal_and_run_never_prepares(self):
        operator, observe = self.run_spies()
        complete = view('COMPLETE')
        self.owner.inspect.return_value = complete
        operator.consume_next.return_value = {'request': None, 'view': complete, 'result_id': None}
        status, current = self.driver.run(self.broker, deepcopy(self.binding), 0)
        self.assertEqual('COMPLETE_FIXED_INVENTORY_COUNTS_ONLY', status)
        self.assertEqual(complete, current)
        self.assertEqual(1, operator.consume_next.call_count)
        self.owner.prepare.assert_not_called()
        self.assertFalse(any(call.args[0] == 'dispatch_intent' for call in observe.call_args_list),
                         'Completed inventory must not create an ambiguous dispatch intent')

    def test_unknown_dispatch_then_same_checkpoint_restore_cannot_consume_again(self):
        # Actual observer writes/fsyncs ordinary temp files. The consuming call
        # alone is a spy: SystemExit represents a process loss with an unknown
        # commit. Returning the same old owned view models a stale primary at
        # its original path while the external observer files survive.
        actual_observe = self.driver.observe
        operator, unused_observe_spy = self.run_spies()
        self.patcher('observe', new=actual_observe)
        operator.consume_next.side_effect = SystemExit('Synthetic unknown dispatch boundary')
        before = deepcopy(self.owner.inspect.return_value)
        with self.assertRaises(SystemExit):
            self.driver.run(self.broker, deepcopy(self.binding), 0)
        self.assertEqual(1, operator.consume_next.call_count,
                         'The counterexample must reach its first dispatch')
        self.assertTrue((self.work / 'recovery-observations.jsonl').is_file())
        self.assertEqual(before, self.owner.inspect.return_value)
        rejected = None
        try:
            self.driver.run(self.broker, deepcopy(self.binding), 0)
        except BaseException as error:
            rejected = error
        self.assertEqual(1, operator.consume_next.call_count,
            'A surviving ambiguous intent must deny a stale same-checkpoint primary')
        self.assertIsInstance(rejected, ERRORS)
        self.owner.prepare.assert_not_called()

    def test_main_rejects_nonfixed_cli_before_host_or_broker(self):
        host = self.patcher('host_and_authority')
        factory = self.patcher('Broker')
        for arguments in ([], ['retry'], ['run', '--budget', '999'], ['prepare', 'run']):
            with self.subTest(arguments=arguments), patch.object(
                    self.driver, 'sys', SimpleNamespace(argv=['driver', *arguments])):
                with self.assertRaises(ERRORS):
                    self.driver.main()
        host.assert_not_called()
        factory.assert_not_called()

    def test_main_host_failure_never_constructs_or_initializes_registry(self):
        factory, power, records = self.main_spies('run')
        original = Invalid('Synthetic existing-primary/source authority failure')
        self.driver.host_and_authority.side_effect = original
        with self.assertRaises(Invalid) as caught:
            self.driver.main()
        self.assertIs(original, caught.exception)
        factory.assert_not_called()
        power.assert_not_called()

    def test_run_mode_missing_sealed_binding_never_prepares(self):
        factory, power, records = self.main_spies('run')
        with self.assertRaises(ERRORS):
            self.driver.main()
        self.driver.prepare.assert_not_called()
        self.driver.run.assert_not_called()
        self.assertEqual([0x80000001, 0x80000000], [call.args[0] for call in power.call_args_list])
        self.broker.close.assert_called_once()

    def test_prepare_main_uses_scoped_power_and_records_no_attempt_preparation(self):
        factory, power, records = self.main_spies('prepare')
        self.driver.main()
        self.driver.prepare.assert_called_once_with(self.broker)
        self.driver.run.assert_not_called()
        self.assertEqual([0x80000001, 0x80000000], [call.args[0] for call in power.call_args_list])
        self.broker.close.assert_called_once()
        self.assertEqual('PREPARED_AMENDMENT_AND_FULL_RESTORE_NO_NEW_ATTEMPTS',
                         self.terminal(records)['status'])

    def test_copy_close_or_power_clear_failure_is_nonzero_after_complete(self):
        for kind in ('copy', 'close', 'power'):
            with self.subTest(kind=kind):
                # Each subcase gets fresh mocks; the real files never contain
                # an authority-bearing binding and no real Broker is opened.
                factory, power, records = self.main_spies('run')
                (self.work / 'recovery-bound-run.json').write_text(json.dumps(self.binding), encoding='utf-8')
                self.broker.close.reset_mock(side_effect=True)
                if kind == 'copy':
                    self.driver.terminal_copies.side_effect = RuntimeError('Synthetic terminal copy failure')
                elif kind == 'close':
                    self.broker.close.side_effect = RuntimeError('Synthetic close failure')
                else:
                    power.side_effect = [1, 0]
                with self.assertRaises(RuntimeError):
                    self.driver.main()
                self.assertEqual('STOPPED_OPERATIONAL_CLOSEOUT_FAILED', self.terminal(records)['status'])
                self.broker.close.side_effect = None

    def test_original_exception_identity_survives_all_closeout_failures(self):
        factory, power, records = self.main_spies('run')
        (self.work / 'recovery-bound-run.json').write_text(json.dumps(self.binding), encoding='utf-8')
        original = RuntimeError('Synthetic first dispatch failure')
        self.driver.run.side_effect = original
        self.driver.terminal_copies.side_effect = RuntimeError('Synthetic second backup failure')
        self.broker.close.side_effect = RuntimeError('Synthetic third close failure')
        power.side_effect = [1, 0]
        with self.assertRaises(RuntimeError) as caught:
            self.driver.main()
        self.assertIs(original, caught.exception)
        self.assertEqual('STOPPED_OPERATIONAL_CLOSEOUT_FAILED', self.terminal(records)['status'])

    def test_original_exception_identity_survives_terminal_receipt_or_output_failure(self):
        for sink in ('receipt', 'output'):
            with self.subTest(sink=sink):
                factory, power, records = self.main_spies('run')
                self.broker.close.reset_mock(side_effect=True)
                (self.work / 'recovery-bound-run.json').write_text(
                    json.dumps(self.binding), encoding='utf-8')
                original = RuntimeError('Synthetic first run exception before publication')
                publication = OSError('Synthetic terminal ' + sink + ' write failure')
                self.driver.run.side_effect = original
                if sink == 'receipt':
                    self.driver.save.side_effect = publication
                observed = None
                if sink == 'output':
                    with patch('builtins.print', side_effect=publication):
                        try:
                            self.driver.main()
                        except BaseException as error:
                            observed = error
                else:
                    try:
                        self.driver.main()
                    except BaseException as error:
                        observed = error
                self.driver.run.assert_called_once()
                self.broker.close.assert_called_once()
                self.assertEqual([0x80000001, 0x80000000],
                    [call.args[0] for call in power.call_args_list])
                self.assertIs(original, observed,
                    'Final publication must not replace the first retained run exception')


if __name__ == '__main__':
    unittest.main()
