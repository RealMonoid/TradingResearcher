"""Independent authenticated-phase custody and parent-only cancellation.

The actual source/case/stream/response/retention owners run over invented native
bytes and simulated numerical transport. Tiny isolated children exercise only
cancellation. Neither custody nor a known deadline grants retry/admission.
"""
from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch

import test_native_process_control_independent as process_support
import test_native_study_transport_independent as transport_support
from trading_researcher import binance_normalize as launcher, native_study_runs, study_process_control as control, study_runs
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict
from trading_researcher.evaluation_plans import footprint


POLICY = {'schema': 'native-study-process-control/1', 'library_threads': 1, 'priority': 'BELOW_NORMAL'}
OBSERVATION = {'policy': POLICY, 'priority_class': 0x4000,
    'thread_environment': {name: '1' for name in ('OMP_NUM_THREADS', 'OMP_THREAD_LIMIT',
        'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
        'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS')}}


class NativeAttemptCustodyEntrypointIndependentTests(unittest.TestCase):
    def test_untrusted_custody_is_denied_before_tempfiles_or_child(self):
        with patch.object(study_runs.tempfile, 'TemporaryDirectory', side_effect=AssertionError('Input files created')):
            with self.assertRaises(Invalid):
                study_runs.execute_attempt({}, {}, {}, {'id': 'invented'}, b'', lambda: 1,
                    {'materialized_bytes': 0, 'accounting_complete': True}, [], _custody=object())


class NativeAttemptCustodyIndependentTests(unittest.TestCase):
    def setUp(self):
        self.f = transport_support.NativeStudyTransportIndependentTests('runTest')
        self.addCleanup(self.f.doCleanups)
        self.f.setUp()
        self.f.world = {'id': 'a' * 64}
        self.control = control.ProcessControl()
        self.custody = control.NativeAttemptCustody()
        self.responses = []

    def clear(self):
        self.custody = control.NativeAttemptCustody()
        self.responses.clear(); self.f.calls.clear(); self.f.outputs.clear()
        self.f.meter.update(materialized_bytes=0, accounting_complete=True)

    def binding(self):
        return {'source_footprint': footprint(self.f.source), 'payload_hash': digest(self.f.payload),
            'manifest_hash': digest(self.f.study_manifest), 'world_id': self.f.world['id'],
            'native_binding': digest(self.f.binding), 'process_control': POLICY}

    def execute(self, mutate=None, *, cancel=None, child=None):
        def response(command, directory, timeout, **options):
            self.assertIs(options['_control'], self.control)
            self.assertEqual(set(options), {'_control'} if cancel is None else {'_control', '_cancel'})
            if cancel is not None: self.assertIs(options['_cancel'], cancel)
            if child is not None: return child(command, Path(directory), timeout)
            value = self.f.child_response(command, directory, timeout)
            self.assertNotIn('cancel', self.f.calls[-1]['request'])
            self.assertNotIn('_cancel', self.f.calls[-1]['request'])
            self.assertNotIn('custody', self.f.calls[-1]['request'])
            value['process_control'] = {'before': deepcopy(OBSERVATION), 'after': deepcopy(OBSERVATION)}
            if mutate is not None: mutate(value, Path(directory), self.f.calls[-1]['phase'])
            self.responses.append(value)
            return value
        options = {'_native': self.f.selected, '_control': self.control, '_custody': self.custody}
        if cancel is not None: options['_cancel'] = cancel
        with patch.object(study_runs, '_run_child', side_effect=response):
            return study_runs.execute_attempt(self.f.source, self.f.payload, self.f.study_manifest,
                self.f.world, b'{}\n', lambda: 10, self.f.meter, self.f.outputs, **options)

    def test_full_generation_and_replay_bind_inputs_and_detach_phase_results_and_proofs(self):
        expected_binding = self.binding()
        result, proofs = self.execute()
        snapshot = self.custody.snapshot()
        self.assertEqual(snapshot, {'schema': 'native-attempt-custody/1', 'binding': expected_binding,
            'phases': [{'phase': 'generate', 'result': transport_support.RESULT, 'proof': proofs[0]},
                       {'phase': 'replay', 'result': {'verified_result_hash': digest(transport_support.RESULT)}, 'proof': proofs[1]}]})
        self.assertIs(self.f.meter['accounting_complete'], True)
        self.assertEqual([call['phase'] for call in self.f.calls], ['generate', 'replay'])
        result['outcome']['state'] = 'mutated'
        proofs[0]['request_hash'] = 'f' * 64
        self.responses[1]['result']['verified_result_hash'] = 'f' * 64
        detached = self.custody.snapshot(); detached['binding']['process_control']['library_threads'] = 999
        detached['phases'].clear()
        self.assertEqual(self.custody.snapshot(), snapshot)

    def test_exact_fresh_container_controlled_native_and_unchanged_source_are_required_before_files(self):
        class Lookalike:
            def snapshot(self): return {'schema': 'native-attempt-custody/1', 'binding': {}, 'phases': []}
        variants = [(object(), self.control, self.f.selected), (Lookalike(), self.control, self.f.selected),
                    ({}, self.control, self.f.selected), (self.custody, None, self.f.selected),
                    (self.custody, self.control, None)]
        try:
            class Derived(control.NativeAttemptCustody): pass
        except TypeError:
            pass
        else:
            variants.append((Derived(), self.control, self.f.selected))
        bad_source = deepcopy(self.f.selected); bad_source['binding']['source_footprint'] = {}
        variants.append((control.NativeAttemptCustody(), self.control, bad_source))
        for index, (custody, selected_control, native) in enumerate(variants):
            with self.subTest(index=index), patch.object(study_runs.tempfile, 'TemporaryDirectory',
                    side_effect=AssertionError('Invalid custody input wrote files')):
                with self.assertRaises(Invalid):
                    study_runs.execute_attempt(self.f.source, self.f.payload, self.f.study_manifest,
                        self.f.world, b'{}\n', lambda: 10, self.f.meter, self.f.outputs,
                        _native=native, _control=selected_control, _custody=custody)
        self.assertEqual(self.f.outputs, [])

    def test_one_use_container_cannot_begin_again_or_restart_another_attempt(self):
        self.execute(); snapshot = self.custody.snapshot()
        with self.assertRaises(Invalid): self.custody._begin(self.binding())
        with patch.object(study_runs.tempfile, 'TemporaryDirectory', side_effect=AssertionError('Used custody restarted')):
            with self.assertRaises(Invalid): self.execute()
        self.assertEqual(self.custody.snapshot(), snapshot)

    def test_cancellation_event_is_only_parent_transport_state_never_child_request_data(self):
        cancel = threading.Event()
        result, proofs = self.execute(cancel=cancel)
        self.assertEqual(result, transport_support.RESULT); self.assertEqual(len(proofs), 2)
        for call in self.f.calls:
            self.assertEqual(set(call['request']), {'payload', 'manifest', 'world', 'footprint',
                            'verify', 'stream_limit', 'native', 'process_control'})

    def test_replay_deadline_cancel_or_generic_error_preserves_only_authenticated_generation(self):
        causes = [control.ChildDeadlineExceeded('Synthetic owned reaped deadline'),
                  control.StudyProcessCancelled('Synthetic owned parent cancellation'),
                  RuntimeError('Synthetic replay transport failure'),
                  control.ChildCleanupFailed('Synthetic replay cleanup uncertainty')]
        for cause in causes:
            self.clear()
            def mutate(response, directory, phase):
                if phase == 'replay': raise cause
            with self.subTest(cause=type(cause).__name__), self.assertRaises(type(cause)):
                self.execute(mutate)
            phases = self.custody.snapshot()['phases']
            self.assertEqual(len(phases), 1)
            self.assertEqual(phases[0]['phase'], 'generate')
            self.assertEqual(phases[0]['result'], transport_support.RESULT)
            self.assertEqual(phases[0]['proof'], {key: value for key, value in self.responses[0].items()
                if key not in ('result',)})
            self.assertIn('replay/computed-result.json', dict(self.f.outputs))
            self.assertIs(self.f.meter['accounting_complete'], not isinstance(cause, control.ChildCleanupFailed))

    def test_generation_failure_before_authenticated_ack_never_qualifies_computed_result_file(self):
        def child(command, directory, timeout):
            (directory / 'computed-result.json').write_text(canonical(transport_support.RESULT), encoding='utf-8')
            (directory / 'child-errors.txt').write_bytes(b'Synthetic pre-ack deadline')
            raise control.ChildDeadlineExceeded('Owned synthetic deadline before acknowledgement')
        with self.assertRaises(control.ChildDeadlineExceeded): self.execute(child=child)
        self.assertEqual(self.custody.snapshot()['phases'], [])
        self.assertEqual(decode(dict(self.f.outputs)['generate/computed-result.json']), transport_support.RESULT)

    def test_cases_request_and_single_link_source_integrity_must_pass_finally_before_phase_recording(self):
        for target in ('cases', 'request', 'source_hardlink', 'replay_hardlink'):
            self.clear()
            phase = 'replay' if target == 'replay_hardlink' else 'generate'
            def mutate(response, directory, actual_phase):
                if actual_phase != phase: return
                if target == 'cases': (directory / 'cases.jsonl').write_bytes(b'changed cases')
                elif target == 'request': (directory / 'request.json').write_bytes(b'changed request')
                else:
                    path = directory / ('expected-stream.jsonl.gz' if target == 'replay_hardlink' else next(iter(self.f.source)))
                    os.link(path, directory / 'owned-second-link')
            with self.subTest(target=target), self.assertRaises((Invalid, Conflict)): self.execute(mutate)
            self.assertEqual([item['phase'] for item in self.custody.snapshot()['phases']], [] if phase == 'generate' else ['generate'])

    def test_output_inventory_failure_keeps_usage_unknown_and_cannot_qualify_acknowledged_phase(self):
        def mutate(response, directory, phase):
            path = directory / 'computed-result.json'; path.unlink(); path.mkdir()
        with self.assertRaises(Invalid): self.execute(mutate)
        self.assertEqual(self.custody.snapshot()['phases'], [])
        self.assertIs(self.f.meter['accounting_complete'], False)
        self.assertIn('generate/stream.jsonl.gz', dict(self.f.outputs))

    def test_replay_result_stream_encoding_engine_or_environment_mismatch_never_qualifies_replay(self):
        for fault in ('result', 'encoded_stream', 'decoded_stream', 'engines', 'environment', 'request'):
            self.clear()
            def mutate(response, directory, phase):
                if phase != 'replay': return
                if fault == 'result': response['result']['verified_result_hash'] = 'f' * 64
                elif fault == 'encoded_stream':
                    path = directory / 'expected-stream.jsonl.gz'; path.write_bytes(path.read_bytes() + b'changed')
                    response['stream_blob'] = transport_support.descriptor(path.read_bytes())
                elif fault == 'decoded_stream': response['stream_encoding']['decoded_blob']['sha256'] = 'f' * 64
                elif fault == 'engines': response['draw_engines'][0]['native'] = False
                elif fault == 'environment': response['environment'] = {'stale': True}
                else: response['request_hash'] = 'f' * 64
            with self.subTest(fault=fault), self.assertRaises(Invalid): self.execute(mutate)
            self.assertEqual([item['phase'] for item in self.custody.snapshot()['phases']], ['generate'])

    def test_generation_technical_failure_retains_one_transport_phase_without_replay_or_world_completion(self):
        stopped = {**deepcopy(transport_support.RESULT), 'outcome': {'state': 'TECHNICAL_FAILURE'}}
        def mutate(response, directory, phase):
            response['result'] = deepcopy(stopped)
            (directory / 'computed-result.json').write_text(canonical(stopped), encoding='utf-8')
        result, proofs = self.execute(mutate)
        self.assertEqual(result, stopped); self.assertEqual(len(proofs), 1)
        self.assertEqual(self.custody.snapshot()['phases'], [{'phase': 'generate', 'result': stopped, 'proof': proofs[0]}])
        self.assertEqual([call['phase'] for call in self.f.calls], ['generate'])

    def test_default_uncontrolled_native_transport_keeps_legacy_request_and_two_proof_shape(self):
        result, proofs = self.f.execute()
        self.assertEqual(result, transport_support.RESULT); self.assertEqual(len(proofs), 2)
        for call in self.f.calls:
            self.assertEqual(set(call['request']), {'payload', 'manifest', 'world', 'footprint', 'verify', 'stream_limit', 'native'})
        for proof in proofs: self.assertNotIn('process_control', proof)

    def test_default_scalar_execute_keeps_original_wire_kwargs_proofs_and_return_values(self):
        seen = []
        def scalar_child(command, directory, timeout, **options):
            self.assertEqual(options, {})
            directory = Path(directory); request = decode((directory / 'request.json').read_bytes())
            self.assertEqual(set(request), {'payload', 'manifest', 'world', 'footprint', 'verify', 'stream_limit'})
            self.assertEqual(command[5], study_runs.BOOTSTRAP)
            self.assertEqual(timeout, 10)
            replay = request['verify'] is not None
            path = directory / ('expected-stream.jsonl.gz' if replay else 'stream.jsonl.gz')
            with path.open('rb' if replay else 'xb') as stream:
                encoded = transport_support.EncodedStream(stream, encoded_limit=request['stream_limit'], verify=replay)
                encoded.write(transport_support.STREAM); encoding = encoded.finish()
            seen.append(request)
            return {'result': {'verified_result_hash': digest(transport_support.RESULT)} if replay else deepcopy(transport_support.RESULT),
                'request_hash': digest(request), 'footprint': footprint(self.f.source),
                'stream_blob': transport_support.descriptor(path.read_bytes()), 'stream_encoding': encoding,
                'environment': {'invented_scalar_environment': True}}
        with patch.object(study_runs, '_run_child', side_effect=scalar_child), \
                patch.object(study_runs, '_environment_current', return_value=True):
            result, proofs = study_runs.execute_attempt(self.f.source, self.f.payload, self.f.study_manifest,
                self.f.world, b'{}\n', lambda: 10, self.f.meter, self.f.outputs)
        self.assertEqual(result, transport_support.RESULT); self.assertEqual(len(seen), 2)
        self.assertEqual(len(proofs), 2)
        for proof in proofs:
            self.assertEqual(set(proof), {'request_hash', 'footprint', 'environment', 'stream_blob', 'stream_encoding'})

    def test_generation_source_identity_or_decoded_stream_failure_never_records_a_phase(self):
        for fault in ('source', 'binding', 'environment', 'request_hash', 'decoded_stream'):
            self.clear()
            def mutate(response, directory, phase):
                if fault == 'source': (directory / next(iter(self.f.source))).write_bytes(b'changed source')
                elif fault == 'binding': response['native_binding'] = 'f' * 64
                elif fault == 'environment': response['environment_before'] = {'stale': True}
                elif fault == 'request_hash': response['request_hash'] = 'f' * 64
                else: response['stream_encoding']['decoded_blob']['sha256'] = 'f' * 64
            with self.subTest(fault=fault), self.assertRaises(Invalid): self.execute(mutate)
            self.assertEqual(self.custody.snapshot()['phases'], [])

    def test_transport_valid_but_malformed_generation_result_never_enters_custody(self):
        for malformed in ({}, {'outcome': {}}):
            self.clear()
            def mutate(response, directory, phase):
                self.assertEqual(phase, 'generate')
                response['result'] = deepcopy(malformed)
                (directory / 'computed-result.json').write_text(canonical(malformed), encoding='utf-8')
            with self.subTest(result=malformed):
                with self.assertRaises((Invalid, KeyError, TypeError)):
                    self.execute(mutate)
                self.assertEqual([call['phase'] for call in self.f.calls], ['generate'])
                self.assertEqual(decode(dict(self.f.outputs)['generate/computed-result.json']), malformed)
                self.assertIn('generate/stream.jsonl.gz', dict(self.f.outputs))
                self.assertIn('generate/child-errors.txt', dict(self.f.outputs))
                self.assertEqual(self.custody.snapshot()['phases'], [])

    def test_cancel_cleanup_failure_keeps_meter_unknown_and_no_phase_despite_retained_prefix(self):
        cancel = threading.Event()
        helper = process_support.NativeProcessControlIndependentTests('runTest')
        process, launch = helper.fake_launch(kill_error=OSError('Synthetic cancel kill failure'))
        def cancelled_launch(*args, **kwargs):
            value = launch(*args, **kwargs)
            cancel.set()
            return value
        with patch.object(launcher.subprocess, 'Popen', side_effect=cancelled_launch), \
                self.assertRaises(control.ChildCleanupFailed):
            study_runs.execute_attempt(self.f.source, self.f.payload, self.f.study_manifest,
                self.f.world, b'{}\n', lambda: 10, self.f.meter, self.f.outputs,
                _native=self.f.selected, _control=self.control, _custody=self.custody, _cancel=cancel)
        self.assertTrue(process.killed)
        self.assertEqual(dict(self.f.outputs)['generate/child-output.json'], b'prefix')
        self.assertIs(self.f.meter['accounting_complete'], False)
        self.assertEqual(self.custody.snapshot()['phases'], [])


class ParentCancellationIndependentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-parent-cancel-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.control = control.ProcessControl()

    def directory(self, name='child'):
        path = self.root / name; path.mkdir(); return path

    def command(self, code):
        return [sys.executable, '-I', '-S', '-B', '-c', code]

    def test_already_set_event_cancels_before_launch_and_output_creation(self):
        cancel = threading.Event(); cancel.set(); directory = self.directory()
        with patch.object(launcher.subprocess, 'Popen') as launch, self.assertRaises(control.StudyProcessCancelled):
            launcher._run_child(self.command('print("{}")'), directory, timeout=5,
                                _control=self.control, _cancel=cancel)
        launch.assert_not_called(); self.assertEqual(list(directory.iterdir()), [])

    def test_non_event_subclass_and_cancel_without_control_fail_before_files_or_launch(self):
        class Lookalike:
            def is_set(self): return False
        class Derived(threading.Event): pass
        variants = [True, {}, lambda: True, Lookalike(), Derived()]
        for index, cancel in enumerate(variants):
            directory = self.directory(str(index))
            with self.subTest(index=index), patch.object(launcher.subprocess, 'Popen') as launch:
                with self.assertRaises(Invalid):
                    launcher._run_child(self.command('print("{}")'), directory, timeout=5,
                                        _control=self.control, _cancel=cancel)
                launch.assert_not_called(); self.assertEqual(list(directory.iterdir()), [])
        directory = self.directory('legacy')
        with patch.object(launcher.subprocess, 'Popen') as launch, self.assertRaises(Invalid):
            launcher._run_child(self.command('print("{}")'), directory, timeout=5, _cancel=threading.Event())
        launch.assert_not_called(); self.assertEqual(list(directory.iterdir()), [])

    @unittest.skipUnless(sys.platform == 'win32', 'Genuine controlled Windows cancellation')
    def test_mid_child_event_kills_reaps_and_keeps_prefix_with_distinct_cancel_cause(self):
        cancel = threading.Event(); directory = self.directory(); launched = []
        actual = subprocess.Popen
        def launch(*args, **kwargs):
            child = actual(*args, **kwargs); launched.append(child); return child
        def request_cancel():
            until = time.monotonic() + 4
            while time.monotonic() < until:
                path = directory / 'child-output.json'
                if path.exists() and path.stat().st_size:
                    break
                time.sleep(0.01)
            cancel.set()
        thread = threading.Thread(target=request_cancel, daemon=True); thread.start()
        code = "import sys,time;print('{\"started\":true}',flush=True);sys.stderr.write('cancel-prefix');sys.stderr.flush();time.sleep(30)"
        try:
            with patch.object(launcher.subprocess, 'Popen', side_effect=launch):
                with self.assertRaises(control.StudyProcessCancelled) as raised:
                    launcher._run_child(self.command(code), directory, timeout=5,
                                        _control=self.control, _cancel=cancel)
        finally:
            cancel.set(); thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertNotIsInstance(raised.exception, control.ChildDeadlineExceeded)
        self.assertEqual(len(launched), 1); self.assertIsNotNone(launched[0].poll())
        self.assertEqual((directory / 'child-output.json').read_bytes().strip(), b'{"started":true}')
        self.assertEqual((directory / 'child-errors.txt').read_bytes(), b'cancel-prefix')

    def test_cancellation_failed_bounded_reap_never_claims_known_cancel_or_deadline(self):
        cancel = threading.Event()
        helper = process_support.NativeProcessControlIndependentTests('runTest')
        process, launch = helper.fake_launch(reap_error=subprocess.TimeoutExpired('Synthetic cancel reap', 5))
        def cancelled_launch(*args, **kwargs):
            child = launch(*args, **kwargs); cancel.set(); return child
        with patch.object(launcher.subprocess, 'Popen', side_effect=cancelled_launch), \
                self.assertRaises(control.ChildCleanupFailed) as raised:
            launcher._run_child(self.command('never executed'), self.directory(), timeout=5,
                                _control=self.control, _cancel=cancel)
        self.assertTrue(process.killed)
        self.assertNotIsInstance(raised.exception, control.StudyProcessCancelled)
        self.assertNotIsInstance(raised.exception, control.ChildDeadlineExceeded)
        self.assertIsNotNone(raised.exception.__cause__)

    def test_default_legacy_launcher_still_accepts_tiny_isolated_json_without_cancel_options(self):
        self.assertEqual(launcher._run_child(self.command('print("{}")'), self.directory(), timeout=5), {})


class NativeStudyCustodyForwardingIndependentTests(unittest.TestCase):
    """Actual caller method; qualification/cache/execute are metadata seams."""
    def setUp(self):
        self.f = transport_support.NativeStudyTransportIndependentTests('runTest')
        self.addCleanup(self.f.doCleanups); self.f.setUp()
        self.study = {'body': {'request': {}, 'native_binding': self.f.binding}}
        self.qualified = {'runtime': {'id': self.f.binding['runtime_id'], 'body': {'manifest': self.f.manifest}}}

    def test_final_caller_forwards_same_host_custody_event_and_control_with_selected_native(self):
        runner = native_study_runs.NativeFamilyCalibrationStudies(types.SimpleNamespace())
        custody = control.NativeAttemptCustody(); cancel = threading.Event()
        with patch.object(runner, '_qualified', return_value=self.qualified), \
                patch.object(native_study_runs.NativeRuntimes, '_materialize', return_value=self.f.cache), \
                patch.object(study_runs, 'execute_attempt', return_value=('synthetic', [])) as execute:
            result = runner._execute_study_attempt(self.study, self.f.source, self.f.payload,
                self.f.study_manifest, self.f.world, b'{}\n', lambda: 10, self.f.meter, self.f.outputs,
                _custody=custody, _cancel=cancel)
        self.assertEqual(result, ('synthetic', []))
        self.assertEqual(set(execute.call_args.kwargs), {'_native', '_control', '_custody', '_cancel'})
        self.assertIs(execute.call_args.kwargs['_custody'], custody)
        self.assertIs(execute.call_args.kwargs['_cancel'], cancel)
        self.assertIs(type(execute.call_args.kwargs['_control']), control.ProcessControl)
        self.assertEqual(execute.call_args.kwargs['_native']['binding'], self.f.binding)

    def test_default_development_caller_passes_no_new_optional_kwargs_and_denies_selected_options(self):
        runner = native_study_runs.NativeFamilyStudies(types.SimpleNamespace())
        with patch.object(runner, '_qualified', return_value=self.qualified), \
                patch.object(native_study_runs.NativeRuntimes, '_materialize', return_value=self.f.cache) as materialize, \
                patch.object(study_runs, 'execute_attempt', return_value=('synthetic', [])) as execute:
            runner._execute_study_attempt(self.study, self.f.source, self.f.payload,
                self.f.study_manifest, self.f.world, b'{}\n', lambda: 10, self.f.meter, self.f.outputs)
            self.assertEqual(set(execute.call_args.kwargs), {'_native'})
            execute.reset_mock(); materialize.reset_mock()
            with self.assertRaises(Invalid):
                runner._execute_study_attempt(self.study, self.f.source, self.f.payload,
                    self.f.study_manifest, self.f.world, b'{}\n', lambda: 10, self.f.meter, self.f.outputs,
                    _custody=control.NativeAttemptCustody(), _cancel=threading.Event())
            execute.assert_not_called(); materialize.assert_not_called()


if __name__ == '__main__':
    unittest.main()
