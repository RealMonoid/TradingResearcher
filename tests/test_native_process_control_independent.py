"""Independent AC-N3/N5/N12 process-control and selected transport checks.

Only tiny isolated Python probes execute. Invented native members and the
existing transport fixture are metadata seams, never binary qualification or
numerical calibration. A parent deadline is a process cause, not retry authority
or an aggregate accounting reservation. Legacy launches retain their contract.
"""
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import importlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher import binance_normalize as launcher
from trading_researcher.codec import Invalid, MAX_BYTES, decode


EXPECTED_POLICY = {'schema': 'native-study-process-control/1',
                   'library_threads': 1, 'priority': 'BELOW_NORMAL'}
EXPECTED_THREADS = {name: '1' for name in (
    'OMP_NUM_THREADS', 'OMP_THREAD_LIMIT', 'OPENBLAS_NUM_THREADS',
    'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS',
    'BLIS_NUM_THREADS')}
EXPECTED_OBSERVATION = {'policy': EXPECTED_POLICY,
                        'thread_environment': EXPECTED_THREADS,
                        'priority_class': 0x4000}


def owner():
    # Deferred import keeps discovery runnable before the new owner exists.
    return importlib.import_module('trading_researcher.study_process_control')


class NativeProcessControlIndependentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-process-control-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def directory(self, name='child'):
        path = self.root / name
        path.mkdir()
        return path

    def command(self, code):
        return [sys.executable, '-I', '-S', '-B', '-c', code]

    def test_invalid_control_is_rejected_before_output_creation_or_launch(self):
        directory = self.directory()
        with patch.object(launcher.subprocess, 'Popen') as launch:
            with self.assertRaises(Invalid):
                launcher._run_child(self.command('print("{}")'), directory,
                                    timeout=1, _control=object())
        launch.assert_not_called()
        self.assertEqual(list(directory.iterdir()), [])

    def test_marker_is_immutable_and_request_mutation_does_not_change_authority(self):
        control = owner().ProcessControl()
        self.assertEqual(control.request(), EXPECTED_POLICY)
        request = control.request()
        request['library_threads'] = 99
        request['priority'] = 'HIGH'
        self.assertEqual(control.request(), EXPECTED_POLICY)
        self.assertIsNot(control.request(), control.request())
        for field, value in (('policy', request), ('library_threads', 99), ('_policy', request)):
            with self.subTest(field=field), self.assertRaises((AttributeError, TypeError)):
                setattr(control, field, value)
        with self.assertRaises(TypeError):
            owner().POLICY['library_threads'] = 99
        with self.assertRaises(TypeError):
            owner().THREAD_ENVIRON['OMP_NUM_THREADS'] = '99'

    def test_exact_marker_rejects_subclasses_and_lookalike_requests(self):
        control_owner = owner()
        class Lookalike:
            def request(self):
                return deepcopy(EXPECTED_POLICY)
        variants = [Lookalike(), deepcopy(EXPECTED_POLICY), True]
        try:
            class Derived(control_owner.ProcessControl):
                pass
        except TypeError:
            pass  # A final marker is also an exact-type boundary.
        else:
            variants.append(Derived())
        for index, value in enumerate(variants):
            directory = self.directory(str(index))
            with self.subTest(index=index), patch.object(launcher.subprocess, 'Popen') as launch:
                with self.assertRaises(Invalid):
                    launcher._run_child(self.command('print("{}")'), directory,
                                        timeout=1, _control=value)
                launch.assert_not_called()
                self.assertEqual(list(directory.iterdir()), [])

    def test_nonfinite_nonpositive_and_boolean_timeouts_deny_before_files_or_launch(self):
        control = owner().ProcessControl()
        for index, timeout in enumerate((0, -1, float('inf'), float('-inf'), float('nan'), True, False, '1', None)):
            directory = self.directory(str(index))
            with self.subTest(timeout=timeout), patch.object(launcher.subprocess, 'Popen') as launch:
                with self.assertRaises(Invalid):
                    launcher._run_child(self.command('print("{}")'), directory,
                                        timeout=timeout, _control=control)
                launch.assert_not_called()
                self.assertEqual(list(directory.iterdir()), [])

    def test_observation_validator_checks_exact_policy_environment_and_priority(self):
        validate = owner().validate_observation
        validate(deepcopy(EXPECTED_OBSERVATION))
        variants = [None, [], {}, {**deepcopy(EXPECTED_OBSERVATION), 'extra': True}]
        for key in EXPECTED_OBSERVATION:
            value = deepcopy(EXPECTED_OBSERVATION)
            del value[key]
            variants.append(value)
        for key, changed in (('schema', 'other/1'), ('library_threads', True),
                             ('library_threads', 2), ('priority', 'NORMAL')):
            value = deepcopy(EXPECTED_OBSERVATION)
            value['policy'][key] = changed
            variants.append(value)
        for environment in ({}, {**EXPECTED_THREADS, 'OTHER': '1'},
                            {**EXPECTED_THREADS, 'OMP_NUM_THREADS': 1},
                            {**EXPECTED_THREADS, 'OPENBLAS_NUM_THREADS': '2'}):
            variants.append({**deepcopy(EXPECTED_OBSERVATION), 'thread_environment': environment})
        for priority in (True, '16384', 0x20, 0):
            variants.append({**deepcopy(EXPECTED_OBSERVATION), 'priority_class': priority})
        for index, value in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(Invalid):
                validate(value)

    @unittest.skipUnless(sys.platform == 'win32', 'Genuine Windows priority probe')
    def test_real_isolated_child_receives_thread_caps_and_below_normal_priority(self):
        code = ("import ctypes,json,os,sys; k=ctypes.WinDLL('kernel32',use_last_error=True);"
                "k.GetCurrentProcess.restype=ctypes.c_void_p;"
                "k.GetPriorityClass.argtypes=[ctypes.c_void_p];k.GetPriorityClass.restype=ctypes.c_uint32;"
                "print(json.dumps({'thread_environment':{n:os.environ.get(n) for n in "
                + repr(list(EXPECTED_THREADS)) + "},'priority_class':k.GetPriorityClass(k.GetCurrentProcess()),"
                "'isolation':[sys.flags.isolated,sys.flags.no_site,int(sys.dont_write_bytecode)]}))")
        # Explicit hostile inheritance proves launch-time replacement, not the
        # test host's incidental environment. Parent environment remains intact.
        hostile = {key: '8' for key in EXPECTED_THREADS}
        with patch.dict(os.environ, hostile):
            result = launcher._run_child(self.command(code), self.directory(),
                                        timeout=5, _control=owner().ProcessControl())
            self.assertEqual({key: os.environ[key] for key in EXPECTED_THREADS}, hostile)
        self.assertEqual(result, {'thread_environment': EXPECTED_THREADS,
                                 'priority_class': 0x4000, 'isolation': [1, 1, 1]})

    @unittest.skipUnless(sys.platform == 'win32', 'Genuine Windows observation probe')
    def test_child_observes_real_state_and_rejects_its_environment_or_priority_drift(self):
        root = str(Path(__file__).resolve().parents[1])
        code = '''import ctypes,json,os,sys
sys.path.insert(0,sys.argv[1])
from trading_researcher import study_process_control as control
from trading_researcher.codec import Invalid
policy=control.ProcessControl().request()
before=control.observe_control(policy)
os.environ['MKL_NUM_THREADS']='2'
try: control.observe_control(policy)
except Invalid: environment_denied=True
else: environment_denied=False
os.environ['MKL_NUM_THREADS']='1'
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.GetCurrentProcess.restype=ctypes.c_void_p
k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
assert k.SetPriorityClass(k.GetCurrentProcess(),0x20)
try: control.observe_control(policy)
except Invalid: priority_denied=True
else: priority_denied=False
print(json.dumps({'before':before,'environment_denied':environment_denied,'priority_denied':priority_denied}))
'''
        result = launcher._run_child(self.command(code) + [root], self.directory(),
                                    timeout=5, _control=owner().ProcessControl())
        self.assertEqual(result, {'before': EXPECTED_OBSERVATION,
                                 'environment_denied': True, 'priority_denied': True})

    def test_controlled_path_fails_closed_off_windows_before_files_or_launch(self):
        directory = self.directory()
        with patch.object(sys, 'platform', 'linux'), patch.object(launcher.subprocess, 'Popen') as launch:
            with self.assertRaises(Invalid):
                launcher._run_child(self.command('print("{}")'), directory,
                                    timeout=1, _control=owner().ProcessControl())
        launch.assert_not_called()
        self.assertEqual(list(directory.iterdir()), [])

    @unittest.skipUnless(sys.platform == 'win32', 'Controlled Windows child')
    def test_owned_elapsed_deadline_kills_reaps_and_retains_both_prefixes(self):
        directory = self.directory()
        actual_launch = subprocess.Popen
        children = []
        def launch(*args, **kwargs):
            child = actual_launch(*args, **kwargs)
            children.append(child)
            return child
        code = "import sys,time;print('{\"started\":true}',flush=True);sys.stderr.write('diagnostic-prefix');sys.stderr.flush();time.sleep(30)"
        with patch.object(launcher.subprocess, 'Popen', side_effect=launch):
            with self.assertRaises(owner().ChildDeadlineExceeded):
                launcher._run_child(self.command(code), directory,
                                    timeout=0.8, _control=owner().ProcessControl())
        self.assertEqual(len(children), 1)
        self.assertIsNotNone(children[0].poll())
        self.assertEqual((directory / 'child-output.json').read_bytes().strip(), b'{"started":true}')
        self.assertEqual((directory / 'child-errors.txt').read_bytes(), b'diagnostic-prefix')

    @unittest.skipUnless(sys.platform == 'win32', 'Controlled Windows child')
    def test_exact_output_caps_pass_but_overflow_is_not_a_deadline(self):
        code = ("import sys;sys.stdout.write('{}'+' '*" + str(MAX_BYTES - 2)
                + ");sys.stderr.write('e'*8192)")
        self.assertEqual(launcher._run_child(self.command(code), self.directory('equal'),
                         timeout=5, _control=owner().ProcessControl()), {})
        for name, code in (('stdout', "import sys;sys.stdout.write('x'*" + str(MAX_BYTES + 1) + ")"),
                           ('stderr', "import sys;print('{}');sys.stderr.write('e'*8193)")):
            with self.subTest(stream=name), self.assertRaises(Invalid) as raised:
                launcher._run_child(self.command(code), self.directory(name),
                                    timeout=5, _control=owner().ProcessControl())
            self.assertNotIsInstance(raised.exception, owner().ChildDeadlineExceeded)

    @unittest.skipUnless(sys.platform == 'win32', 'Controlled Windows child')
    def test_nonzero_child_timeout_and_bad_json_never_claim_parent_deadline(self):
        cases = ("raise TimeoutError('a child assertion, not a parent deadline')",
                 "import sys;sys.exit(7)", "print('not-json')")
        for index, code in enumerate(cases):
            with self.subTest(index=index), self.assertRaises(Invalid) as raised:
                launcher._run_child(self.command(code), self.directory(str(index)),
                                    timeout=5, _control=owner().ProcessControl())
            self.assertNotIsInstance(raised.exception, owner().ChildDeadlineExceeded)

    def fake_launch(self, *, stdout=b'prefix', stderr=b'diagnostic', kill_error=None, reap_error=None,
                    first_wait_error=None):
        class Process:
            returncode = None
            killed = False
            wait_timeouts = []
            first_wait = True
            def poll(self):
                return self.returncode
            def kill(self):
                self.killed = True
                if kill_error is not None:
                    raise kill_error
                self.returncode = -9
            def wait(self, timeout=None):
                self.wait_timeouts.append(timeout)
                if self.killed:
                    if reap_error is not None:
                        raise reap_error
                    return self.returncode
                if self.first_wait and first_wait_error is not None:
                    self.first_wait = False
                    raise first_wait_error
                raise subprocess.TimeoutExpired('invented child', timeout)
        process = Process()
        def launch(command, **kwargs):
            kwargs['stdout'].write(stdout); kwargs['stdout'].flush()
            kwargs['stderr'].write(stderr); kwargs['stderr'].flush()
            return process
        return process, launch

    def test_output_overflow_wins_over_simultaneous_parent_deadline(self):
        process, launch = self.fake_launch(stdout=b'x' * (MAX_BYTES + 1))
        ticks = iter(range(100))
        with patch.object(launcher.subprocess, 'Popen', side_effect=launch), \
                patch.object(owner().time, 'monotonic', side_effect=lambda: next(ticks)):
            with self.assertRaises(Invalid) as raised:
                launcher._run_child(self.command('never executed'), self.directory(),
                                    timeout=0.1, _control=owner().ProcessControl())
        self.assertNotIsInstance(raised.exception, owner().ChildDeadlineExceeded)
        self.assertTrue(process.killed)
        self.assertIsNotNone(process.returncode)

    def test_failed_kill_or_bounded_reap_never_acquires_deadline_authority(self):
        failures = ({'kill_error': OSError('synthetic kill failure')},
                    {'reap_error': subprocess.TimeoutExpired('synthetic reap', 5)})
        for index, failure in enumerate(failures):
            process, launch = self.fake_launch(**failure)
            ticks = iter(range(100))
            with self.subTest(index=index), patch.object(launcher.subprocess, 'Popen', side_effect=launch), \
                    patch.object(owner().time, 'monotonic', side_effect=lambda: next(ticks)):
                with self.assertRaises((Invalid, OSError, subprocess.TimeoutExpired)) as raised:
                    launcher._run_child(self.command('never executed'), self.directory(str(index)),
                                        timeout=0.1, _control=owner().ProcessControl())
            self.assertNotIsInstance(raised.exception, owner().ChildDeadlineExceeded)
            self.assertTrue(process.killed)
            for timeout in process.wait_timeouts:
                self.assertIsNotNone(timeout)
                self.assertLessEqual(timeout, 5)

    def test_cancellation_and_generic_supervisor_timeout_are_not_reclassified(self):
        for index, cause in enumerate((KeyboardInterrupt('operator cancellation'), TimeoutError('not owned elapsed deadline'))):
            process, launch = self.fake_launch(first_wait_error=cause)
            with self.subTest(index=index), patch.object(launcher.subprocess, 'Popen', side_effect=launch):
                with self.assertRaises(type(cause)) as raised:
                    launcher._run_child(self.command('never executed'), self.directory(str(index)),
                                        timeout=100, _control=owner().ProcessControl())
            self.assertIs(raised.exception, cause)
            self.assertTrue(process.killed)
            self.assertIsNotNone(process.returncode)

    def test_default_launch_remains_an_unselected_isolated_json_child(self):
        # No selected marker, policy field or new retry cause is inferred.
        self.assertEqual(launcher._run_child(self.command('print("{\\"legacy\\":true}")'),
                         self.directory(), timeout=5), {'legacy': True})


class NativeControlledTransportIndependentTests(unittest.TestCase):
    """Real parent/child metadata owners; invented native bytes and transport.

    Composition reuses setup helpers without importing another TestCase class
    into discovery or rerunning its unrelated methods. No native image is loaded.
    """
    def setUp(self):
        import test_native_study_transport_independent as support
        self.support = support
        self.fixture = support.NativeStudyTransportIndependentTests('runTest')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()
        self.control = owner().ProcessControl()
        self.controls = []

    def execute(self, mutate=None):
        fixture = self.fixture
        def child(command, directory, timeout, *, _control=None):
            self.assertIs(_control, self.control)
            self.controls.append(_control)
            response = fixture.child_response(command, directory, timeout)
            request = fixture.calls[-1]['request']
            self.assertEqual(request['process_control'], EXPECTED_POLICY)
            response['process_control'] = {'before': deepcopy(EXPECTED_OBSERVATION),
                                           'after': deepcopy(EXPECTED_OBSERVATION)}
            if mutate is not None:
                mutate(response, Path(directory), fixture.calls[-1]['phase'])
            return response
        with patch.object(self.support.study_runs, '_run_child', side_effect=child):
            return self.support.study_runs.execute_attempt(fixture.source, fixture.payload,
                fixture.study_manifest, fixture.world, b'{}\n', lambda: 10,
                fixture.meter, fixture.outputs, _native=fixture.selected, _control=self.control)

    def test_both_fresh_native_children_bind_policy_and_retain_actual_observations(self):
        result, proofs = self.execute()
        self.assertEqual(result, self.support.RESULT)
        self.assertEqual(len(self.controls), 2)
        self.assertEqual([call['phase'] for call in self.fixture.calls], ['generate', 'replay'])
        self.assertNotEqual(self.fixture.calls[0]['directory'], self.fixture.calls[1]['directory'])
        self.assertEqual(len(proofs), 2)
        for proof in proofs:
            self.assertEqual(proof['process_control'], {'before': EXPECTED_OBSERVATION,
                                                        'after': EXPECTED_OBSERVATION})
        retained = dict(self.fixture.outputs)
        self.assertEqual(retained['generate/stream.jsonl.gz'], retained['replay/expected-stream.jsonl.gz'])

    def test_control_requires_native_selection_and_exact_host_marker_before_transport(self):
        fixture = self.fixture
        for native, control in ((None, self.control), (fixture.selected, EXPECTED_POLICY),
                                (fixture.selected, object())):
            with self.subTest(native=native is not None, control=type(control).__name__), \
                    patch.object(self.support.study_runs, '_run_child') as child:
                with self.assertRaises(Invalid):
                    self.support.study_runs.execute_attempt(fixture.source, fixture.payload,
                        fixture.study_manifest, fixture.world, b'{}\n', lambda: 10,
                        fixture.meter, fixture.outputs, _native=native, _control=control)
                child.assert_not_called()
                self.assertEqual(fixture.outputs, [])
                self.assertEqual(fixture.meter, {'materialized_bytes': 0, 'accounting_complete': True})

    def test_bad_missing_or_changed_control_observation_denies_and_keeps_actual_prefix(self):
        def missing(response):
            del response['process_control']
        def before(response):
            response['process_control']['before']['thread_environment']['OMP_NUM_THREADS'] = '2'
        def after(response):
            response['process_control']['after']['priority_class'] = 0x20
        def extra(response):
            response['process_control']['unobserved'] = True
        for phase in ('generate', 'replay'):
            for mutation in (missing, before, after, extra):
                self.fixture.calls.clear(); self.fixture.outputs.clear(); self.controls.clear()
                def mutate(response, directory, actual_phase):
                    if phase == actual_phase:
                        mutation(response)
                with self.subTest(phase=phase, mutation=mutation.__name__), self.assertRaises(Invalid):
                    self.execute(mutate)
                self.assertEqual(len(self.fixture.calls), 1 if phase == 'generate' else 2)
                retained = dict(self.fixture.outputs)
                self.assertIn(phase + '/computed-result.json', retained)
                self.assertIn(phase + '/child-errors.txt', retained)
                self.assertIs(self.fixture.meter['accounting_complete'], True)

    def test_parent_context_independently_enforces_control_without_observing_parent_priority(self):
        fixture = self.fixture
        context = self.support.pipeline.ParentContext(fixture.source, fixture.selected, _control=self.control)
        response = {'native_binding': self.support.digest(fixture.binding), 'draw_engines': [],
                    'environment_before': {'invented_environment': 'current'},
                    'environment': {'invented_environment': 'current'},
                    'process_control': {'before': deepcopy(EXPECTED_OBSERVATION),
                                        'after': deepcopy(EXPECTED_OBSERVATION)}}
        with patch.object(owner(), 'observe_control', side_effect=AssertionError('Parent priority is irrelevant')):
            self.assertIs(context.validate_response(response), True)
            for key in ('before', 'after'):
                changed = deepcopy(response)
                changed['process_control'][key]['policy']['library_threads'] = True
                with self.subTest(key=key), self.assertRaises(Invalid):
                    context.validate_response(changed)

    def test_child_observes_before_numpy_and_after_calculation_without_numerical_execution(self):
        fixture = self.fixture
        control_owner = owner()
        directory = fixture.root / 'controlled-child'; directory.mkdir()
        request_path = fixture.child_request(directory)
        request = decode(request_path.read_bytes())
        request['process_control'] = deepcopy(EXPECTED_POLICY)
        request_path.write_text(self.support.canonical(request), encoding='utf-8')
        order = []
        def observe(policy):
            self.assertEqual(policy, EXPECTED_POLICY)
            order.append('observe')
            return deepcopy(EXPECTED_OBSERVATION)
        def calculate(payload, manifest, world, cases, retain, **options):
            order.append('calculate')
            retain({'kind': 'case', 'value': {'invented': True}})
            return deepcopy(self.support.RESULT)
        output = io.StringIO()
        with fixture.child_seams(calculate), ExitStack() as stack:
            stack.enter_context(patch.object(control_owner, 'observe_control', side_effect=observe))
            # Support either a direct owner import or a locally imported alias;
            # a missing real call still fails the fixed call-order assertion.
            stack.enter_context(patch.object(self.support.pipeline, 'observe_control', side_effect=observe, create=True))
            original_import = self.support.pipeline.importlib.import_module
            def selected_import(name):
                if name == 'numpy':
                    order.append('numpy')
                return original_import(name)
            stack.enter_context(patch.object(self.support.pipeline.importlib, 'import_module', side_effect=selected_import))
            with redirect_stdout(output):
                self.support.pipeline.child_entry(request_path)
        response = decode(output.getvalue())
        self.assertEqual(order, ['observe', 'numpy', 'calculate', 'observe'])
        self.assertEqual(response['process_control'], {'before': EXPECTED_OBSERVATION,
                                                       'after': EXPECTED_OBSERVATION})

    def test_integrity_failure_overrides_owned_deadline_with_available_prefix_retained(self):
        # The deadline is a trusted synthetic supervisor cause here. Corrupting
        # copied inputs must remove its retry eligibility at the real transport
        # owner, even though no successful response exists for identity checks.
        fixture = self.fixture
        for target in ('source', 'cases', 'request', 'replay_input'):
            fixture.calls.clear(); fixture.outputs.clear(); self.controls.clear()
            phase = 'replay' if target == 'replay_input' else 'generate'
            def child(command, directory, timeout, *, _control=None):
                self.assertIs(_control, self.control)
                response = fixture.child_response(command, directory, timeout)
                response['process_control'] = {'before': deepcopy(EXPECTED_OBSERVATION),
                                               'after': deepcopy(EXPECTED_OBSERVATION)}
                if fixture.calls[-1]['phase'] == phase:
                    name = {'source': next(iter(fixture.source)), 'cases': 'cases.jsonl',
                            'request': 'request.json', 'replay_input': 'expected-stream.jsonl.gz'}[target]
                    (Path(directory) / name).write_bytes(b'changed immutable copied input')
                    raise owner().ChildDeadlineExceeded('Synthetic owned reaped deadline')
                return response
            with self.subTest(target=target), patch.object(self.support.study_runs, '_run_child', side_effect=child):
                with self.assertRaises((Invalid, self.support.Conflict)) as raised:
                    self.support.study_runs.execute_attempt(fixture.source, fixture.payload,
                        fixture.study_manifest, fixture.world, b'{}\n', lambda: 10,
                        fixture.meter, fixture.outputs, _native=fixture.selected, _control=self.control)
                self.assertNotIsInstance(raised.exception, owner().ChildDeadlineExceeded)
                self.assertEqual(len(fixture.calls), 1 if phase == 'generate' else 2)
                self.assertIn(phase + '/child-errors.txt', dict(fixture.outputs))
                self.assertIn(phase + '/computed-result.json', dict(fixture.outputs))
                self.assertIs(fixture.meter['accounting_complete'], True)
                self.assertGreater(fixture.meter['materialized_bytes'], 0)

    def test_failed_child_cleanup_keeps_usage_unknown_despite_available_prefix_inventory(self):
        # Actual supervisor -> execute_attempt composition. Only Popen/clock
        # are synthetic: a non-reaped child could still append after inventory,
        # so successfully reading the available prefix cannot certify use.
        fixture = self.fixture
        control_owner = owner()
        failures = ({'kill_error': OSError('Synthetic live-child kill failure')},
                    {'reap_error': subprocess.TimeoutExpired('Synthetic non-reaped child', 5)})
        for index, failure in enumerate(failures):
            fixture.calls.clear(); fixture.outputs.clear()
            fixture.meter.update(materialized_bytes=0, accounting_complete=True)
            process, launch = NativeProcessControlIndependentTests('runTest').fake_launch(**failure)
            ticks = iter(range(100))
            with self.subTest(index=index), patch.object(launcher.subprocess, 'Popen', side_effect=launch) as launched, \
                    patch.object(control_owner.time, 'monotonic', side_effect=lambda: next(ticks)):
                with self.assertRaises((Invalid, OSError, subprocess.TimeoutExpired)) as raised:
                    self.support.study_runs.execute_attempt(fixture.source, fixture.payload,
                        fixture.study_manifest, fixture.world, b'{}\n', lambda: 0.1,
                        fixture.meter, fixture.outputs, _native=fixture.selected, _control=self.control)
            self.assertEqual(launched.call_count, 1)
            self.assertTrue(process.killed)
            self.assertNotIsInstance(raised.exception, control_owner.ChildDeadlineExceeded)
            self.assertEqual(dict(fixture.outputs)['generate/child-output.json'], b'prefix')
            self.assertEqual(dict(fixture.outputs)['generate/child-errors.txt'], b'diagnostic')
            self.assertFalse(any(name.startswith('replay/') for name, raw in fixture.outputs))
            self.assertGreater(fixture.meter['materialized_bytes'], 0)
            self.assertIs(fixture.meter['accounting_complete'], False)
            self.assertIs(type(raised.exception), control_owner.ChildCleanupFailed)
            self.assertIsNotNone(raised.exception.__cause__)

    def test_default_native_transport_has_no_new_policy_request_response_or_proof(self):
        result, proofs = self.fixture.execute()
        self.assertEqual(result, self.support.RESULT)
        self.assertEqual(len(proofs), 2)
        for call in self.fixture.calls:
            self.assertNotIn('process_control', call['request'])
        for proof in proofs:
            self.assertNotIn('process_control', proof)


if __name__ == '__main__':
    unittest.main()
