"""Caller integration for the pre-final correction, with explicit input seams.

These root-authored checks do not independently qualify numerical responses.
The runtime/qualification/reference units invoke real controller closures while
substituting those external owners and setup accounting. The clock case uses a
real disposable Broker and ledger, substituting only correction authorization.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

import test_native_calibration_resource_owner_independent as financial
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher import native_calibration_runs as runs
from trading_researcher.native_calibration_controller import NativeCalibrationController, CONTROL_BYTES
from trading_researcher.native_calibration_resources import META, NativeResourceHistory
from trading_researcher.native_qualification import NativeQualifications
from trading_researcher import native_qualification_profile as profile
from trading_researcher.native_runtime import NativeRuntimes


class SourceCorrectionInputCallerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-correction-caller-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.archive = self.root / 'runtime.zip'
        self.archive.write_bytes(b'Explicit runtime-input adapter seam; never executed.')
        self.manifest = self.root / 'manifest.json'
        self.manifest.write_bytes(canonical({'fixture': 'runtime membership seam'}).encode())
        self.archive_sha = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.pool = 'a' * 64
        self.runtime = {'id': 'b' * 64, 'body': {
            'archive': {'sha256': self.archive_sha, 'size': self.archive.stat().st_size},
            'manifest': {'fixture': 'runtime membership seam'},
            'request': {'key': 'd100-exact-native-runtime'}}}
        self.qualification = {'id': 'c' * 64, 'body': {'status': 'CERTIFIED', 'failure': None,
            'settlement': {'storage_bytes': 1234, 'usage_known': True}}}
        self.reference = {'id': 'd' * 64, 'body': {'initial_storage_bytes': 2345}}
        self.broker = Mock()
        self.broker.call.side_effect = AssertionError('A correction must not import another archive source')
        self.controller = object.__new__(NativeCalibrationController)
        self.controller.broker = self.broker
        self.controller.resources = Mock()
        self.controller.resources._pool.return_value = {'body': {
            'source_correction': {'runtime_id': self.runtime['id']}}}
        self.setup_names = []

        def setup(token, pool_id, name, work):
            self.assertEqual(pool_id, self.pool)
            self.setup_names.append(name)
            return {'body': work()}

        self.controller._setup = setup
        for target, attribute, value in ((profile, 'ARCHIVE_SHA', self.archive_sha),
                (profile, 'MANIFEST_SHA', hashlib.sha256(self.manifest.read_bytes()).hexdigest())):
            handle = patch.object(target, attribute, value)
            handle.start()
            self.addCleanup(handle.stop)

    def invoke(self, runtime=None):
        with patch.object(NativeRuntimes, 'inspect', return_value=runtime or self.runtime) as inspect, \
                patch.object(NativeRuntimes, 'retain', side_effect=AssertionError('Runtime retention reset')), \
                patch.object(NativeQualifications, 'qualify', return_value=self.qualification) as qualify, \
                patch.object(NativeQualifications, '_require_inputs', return_value={}) as current, \
                patch.object(runs.NativeCalibrationCorrectionReferences, 'prepare', return_value=self.reference) as prepare, \
                patch.object(runs.NativeCalibrationReferences, '_study', return_value=self.reference):
            result = self.controller.prepare_inputs('synthetic-token', self.pool, self.archive, self.manifest)
            return result, inspect, qualify, current, prepare

    def test_reuses_runtime_without_archive_import_and_binds_fresh_qualification_and_reference_keys(self):
        result, inspect, qualify, current, prepare = self.invoke()
        self.assertEqual(result, (self.qualification['id'], self.reference))
        self.assertEqual(self.setup_names, ['runtime_retain', 'runtime_qualification', 'prepare_reference_input'])
        self.broker.call.assert_not_called()
        self.assertEqual(inspect.call_count, 2)
        self.assertTrue(all(call.args[1] == {'runtime_id': self.runtime['id']} for call in inspect.call_args_list))
        qualification_request = qualify.call_args.args[1]
        self.assertEqual(qualification_request, {
            'key': 'd100-source-correction-qualification-' + self.pool, 'runtime_id': self.runtime['id']})
        current.assert_called_once_with(self.qualification['id'])
        request = prepare.call_args.args[1]
        self.assertEqual(request['key'], 'd100-source-correction-reference-' + self.pool)
        self.assertEqual(request['native_qualification_id'], self.qualification['id'])
        self.assertEqual(request['source_correction_pool_id'], self.pool)

    def test_wrong_retained_runtime_manifest_cannot_reach_qualification(self):
        runtime = deepcopy(self.runtime)
        runtime['body']['manifest'] = {'fixture': 'different runtime'}
        with self.assertRaisesRegex(Invalid, 'exact already-retained runtime'):
            self.invoke(runtime)
        self.assertEqual(self.setup_names, ['runtime_retain'])
        self.broker.call.assert_not_called()

    def test_changed_archive_file_is_denied_before_setup_or_runtime_lookup(self):
        self.archive.write_bytes(b'Changed input bytes')
        with self.assertRaisesRegex(Invalid, 'runtime inputs differ'):
            self.invoke()
        self.assertEqual(self.setup_names, [])
        self.broker.call.assert_not_called()


class SourceCorrectionControllerClockTests(unittest.TestCase):
    def test_real_source_reservation_binding_and_reopen_preserve_the_predecessor_operational_start(self):
        with tempfile.TemporaryDirectory(prefix='trf-correction-clock-') as temporary:
            fixture = financial.RetiredFinancialFixture(temporary)
            broker = fixture.broker
            try:
                with patch.object(runs.NativeCalibrationResources, '_read_authority', return_value=fixture.authority), \
                        patch.object(runs.NativeCalibrationResources, '_correction_observation', return_value={}):
                    manager = runs.NativeCalibrationResources(broker)
                    parent = manager.prepare(fixture.token, {'key': 'clock-unit-parent'})
                    args = {'key': 'clock-unit-correction', 'predecessor_pool_id': parent['id'],
                        'expected_checkpoint': manager._history(parent).checkpoint,
                        'terminal_receipt_path': str(Path(temporary) / 'authorization-seam.json')}
                    # The independent constructor tests own authorization/copy
                    # guards. This unit isolates real caller metering and clocks.
                    body = {k: deepcopy(v) for k, v in parent['body'].items()
                            if k not in ('schema', 'created_at', 'scientific_readiness')}
                    body['identity'] = digest({'fixture': 'clock-correction'})
                    body['source_correction'] = {'schema': 'native-calibration-source-correction/1',
                        'request': args, 'predecessor_pool_id': parent['id'],
                        'controller_directory': str(Path(temporary) / 'new-controller'),
                        'operational_start_utc': '2026-11-03T13:02:06.210244+00:00'}
                    with broker._transaction():
                        child = manager._save(runs.POOL, body, [parent['id']])
                        history = NativeResourceHistory(child)
                        manager._bind_locked(child, history, {'key': 'clock-correction-setup',
                            'pool_id': child['id'], 'phase': 'setup',
                            'task_ids': sorted(body['setup_tasks'].values()),
                            'execution_deadline_ms': 600000, 'attempt_compute_ms': 630000,
                            'attempt_storage_bytes': 268435456, 'max_attempts': 1,
                            'expected_checkpoint': history.checkpoint})
                    directory = Path(temporary) / 'new-controller'
                    controller = NativeCalibrationController(broker, directory)
                    before = manager.inspect(fixture.token, child['id'])['budget']
                    with patch.object(runs.NativeCalibrationResources, 'correct_source', return_value=child) as authorize:
                        saved = controller.prepare(fixture.token, args['key'], correction_args=args)
                    authorize.assert_called_once_with(fixture.token, args)
                    self.assertEqual(saved['id'], child['id'])
                    self.assertEqual(controller.binding['operational_start_utc'], body['source_correction']['operational_start_utc'])
                    after = manager.inspect(fixture.token, child['id'])['budget']
                    self.assertEqual(after['charged_storage_bytes'] - before['charged_storage_bytes'],
                        2 * controller.driver_file.stat().st_size + META + CONTROL_BYTES)
                    self.assertGreater(after['charged_compute_ms'], before['charged_compute_ms'])
                    reopened = NativeCalibrationController(broker, directory)
                    self.assertEqual(reopened.prepare(fixture.token, args['key'], correction_args=args)['id'], child['id'])
                    self.assertEqual(reopened.binding, controller.binding)
                    self.assertEqual(manager.inspect(fixture.token, child['id'])['budget'], after)
            finally:
                broker.close()

    def test_partial_predecessor_cli_arguments_fail_before_creating_a_registry(self):
        with tempfile.TemporaryDirectory(prefix='trf-correction-cli-') as temporary:
            root = Path(temporary)
            command = [sys.executable, '-B', 'tools/calibration/native_parallel.py',
                '--registry', str(root / 'never-created-registry'), '--run-directory', str(root / 'never-created-control'),
                '--runtime-archive', str(root / 'never-read.zip'), '--runtime-manifest', str(root / 'never-read.json'),
                '--predecessor-pool', 'a' * 64]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('All three predecessor fields are required', result.stderr)
            self.assertEqual(list(root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
