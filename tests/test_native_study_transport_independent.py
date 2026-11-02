"""Independent selected-study transport and failure cases using invented bytes.

The actual retained-source writer, response validator, stream reader and output
retention run here. Child process transport, fixed binary membership and native
environment observations are explicit trusted seams. No fixture imports NumPy,
loads a native image, grants a certificate, or performs scientific simulation.
"""
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
from fractions import Fraction
import hashlib
import io
from pathlib import Path
import random
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from test_native_runtime_independent import manifest
from trading_researcher import native_study_pipeline as pipeline, study_runs
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict
from trading_researcher.evaluation_plans import footprint
from trading_researcher.study_stream import EncodedStream, decode_stream


REJECTED = (Invalid, Conflict, KeyError, TypeError)
STREAM = b'{"kind":"case","value":{"invented":true}}\n'
RESULT = {'outcome': {'state': 'INFORMATION_GAP'}, 'invented_transport_fixture': True}


def descriptor(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


class NativeStudyTransportIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='trf-native-transport-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.cache = self.root / 'cache'
        self.cache.mkdir()
        members = {'example/LICENSE.txt': b'Invented notice.\n',
                   pipeline.KERNEL_FILE: b'Invented bytes; never executable.\n'}
        self.manifest = manifest(members)
        for name, raw in members.items():
            path = self.cache / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.source = {'trading_researcher/fixture.py': b'# Invented retained source, never imported.\n'}
        self.binding = {'schema': pipeline.SCHEMA, 'profile': pipeline.PROFILE,
            'qualification_id': '1' * 64, 'runtime_id': '2' * 64,
            'runtime_manifest': deepcopy(self.manifest), 'host_images': [],
            'source_footprint': footprint(self.source)}
        self.selected = {'binding': deepcopy(self.binding), 'directory': str(self.cache)}
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(pipeline, 'MANIFEST_SHA', digest(self.manifest)))
        self.stack.enter_context(patch.object(pipeline, 'KERNEL_SHA', self.manifest['files'][pipeline.KERNEL_FILE]['sha256']))
        self.observations = []

        def current(observed, runtime_id, spec, directory, hosts):
            self.observations.append(deepcopy(observed))
            self.assertEqual(runtime_id, self.binding['runtime_id'])
            self.assertEqual(spec, self.manifest)
            self.assertEqual(Path(directory), self.cache)
            self.assertEqual(hosts, [])
            return observed == {'invented_environment': 'current'}

        self.stack.enter_context(patch.object(pipeline, 'current', side_effect=current))
        self.calls = []
        self.meter = {'materialized_bytes': 0, 'accounting_complete': True}
        self.outputs = []
        self.payload = {'case_blob': descriptor(b'{}\n')}
        self.study_manifest = {'profile': {'budget': {'attempt_storage_bytes': 32 * 1024**2}}}
        self.world = {'id': 'fixture-world'}

    def context(self, selected=None):
        return pipeline.ParentContext(self.source, self.selected if selected is None else selected)

    def child_response(self, command, directory, timeout, *, mutate=None):
        directory = Path(directory)
        request = decode((directory / 'request.json').read_bytes())
        self.assertEqual(command[:4], [sys.executable, '-I', '-S', '-B'])
        self.assertEqual(command[4:6], ['-c', pipeline.BOOTSTRAP])
        self.assertEqual(command[-2:], [str(directory), str(directory / 'request.json')])
        self.assertEqual(timeout, 10)
        self.assertEqual((directory / 'cases.jsonl').read_bytes(), b'{}\n')
        self.assertEqual(footprint({name: (directory / name).read_bytes() for name in self.source}), footprint(self.source))
        phase = 'generate' if request['verify'] is None else 'replay'
        path = directory / ('stream.jsonl.gz' if phase == 'generate' else 'expected-stream.jsonl.gz')
        with path.open('xb' if phase == 'generate' else 'rb') as stream:
            encoded = EncodedStream(stream, encoded_limit=request['stream_limit'], verify=phase == 'replay')
            encoded.write(STREAM)
            encoding = encoded.finish()
        (directory / 'computed-result.json').write_text(canonical(RESULT), encoding='utf-8')
        (directory / 'child-output.json').write_bytes(b'Synthetic bounded child stdout.\n')
        (directory / 'child-errors.txt').write_bytes(b'Synthetic bounded child diagnostic.\n')
        result = deepcopy(RESULT) if phase == 'generate' else {'verified_result_hash': digest(RESULT)}
        response = {'result': result, 'stream_blob': descriptor(path.read_bytes()), 'stream_encoding': encoding,
            'request_hash': digest(request), 'footprint': footprint(self.source),
            'environment_before': {'invented_environment': 'current'},
            'environment': {'invented_environment': 'current'},
            'native_binding': digest(self.binding), 'draw_engines': [{'length': 4, 'native': True}]}
        self.calls.append({'phase': phase, 'directory': str(directory), 'request': request})
        if mutate is not None:
            mutate(response, directory, phase)
        return response

    def execute(self, mutate=None):
        with patch.object(study_runs, '_run_child', side_effect=lambda command, directory, timeout:
                          self.child_response(command, directory, timeout, mutate=mutate)):
            return study_runs.execute_attempt(self.source, self.payload, self.study_manifest, self.world,
                b'{}\n', lambda: 10, self.meter, self.outputs, _native=self.selected)

    def test_selected_inputs_are_detached_and_complete_source_runtime_members_are_checked(self):
        selected = deepcopy(self.selected)
        context = self.context(selected)
        selected['binding']['host_images'].append({'arbitrary': True})
        selected['binding']['runtime_manifest']['files'].clear()
        self.assertEqual(context.binding, self.binding)
        self.assertEqual(context.cold_bytes, sum(value['size'] for value in self.manifest['files'].values()))
        self.assertEqual(context.request(), self.selected)
        (self.cache / pipeline.KERNEL_FILE).write_bytes(b'mutated')
        with self.assertRaises(REJECTED): self.context()

    def test_exact_private_input_shape_rejects_callbacks_relative_paths_and_version_substitution(self):
        variants = [None, [], {'binding': self.binding}, {**self.selected, 'factory': lambda: None}]
        for change in ({'directory': 'relative/cache'}, {'directory': self.cache},
                       {'binding': {**self.binding, 'schema': 'other/1'}},
                       {'binding': {**self.binding, 'profile': 'other/1'}},
                       {'binding': {**self.binding, 'runtime_id': '2' * 63}},
                       {'binding': {**self.binding, 'qualification_id': 'A' * 64}},
                       {'binding': {**self.binding, 'source_footprint': {}}},
                       {'binding': {**self.binding, 'factory': 'request-supplied'}},
                       {'binding': {**self.binding, 'runtime_manifest': {**self.manifest, 'schema': 'other/1'}}}):
            variants.append({**self.selected, **change})
        for index, selected in enumerate(variants):
            with self.subTest(case=index), self.assertRaises(REJECTED):
                pipeline.ParentContext(self.source, selected)

    def test_response_binds_pre_and_post_environment_and_exact_engine_observations(self):
        context = self.context()
        base = {'native_binding': digest(self.binding), 'draw_engines': [{'length': 100001, 'native': False}],
                'environment_before': {'invented_environment': 'current'},
                'environment': {'invented_environment': 'current'}}
        self.assertIs(context.validate_response(base), True)
        self.assertEqual(len(self.observations), 2)
        variants = [{'native_binding': '0' * 64}, {'environment_before': {'stale': True}},
                    {'environment': {'stale': True}}, {'draw_engines': {}},
                    {'draw_engines': [{'length': 4, 'native': 1}]},
                    {'draw_engines': [{'length': True, 'native': False}]},
                    {'draw_engines': [{'length': 0, 'native': False}]},
                    {'draw_engines': [{'length': 4, 'native': False, 'extra': 1}]},
                    {'draw_engines': [{'length': 4, 'native': False}] * 129}]
        for change in variants:
            with self.subTest(change=change), self.assertRaises(REJECTED):
                context.validate_response({**base, **change})

    def test_generation_and_replay_use_distinct_directories_and_complete_equal_bytes(self):
        result, proofs = self.execute()
        self.assertEqual(result, RESULT)
        self.assertEqual([call['phase'] for call in self.calls], ['generate', 'replay'])
        self.assertNotEqual(self.calls[0]['directory'], self.calls[1]['directory'])
        self.assertIsNone(self.calls[0]['request']['verify'])
        self.assertEqual(self.calls[1]['request']['verify'], digest(RESULT))
        self.assertEqual(len(proofs), 2)
        retained = dict(self.outputs)
        self.assertEqual(retained['generate/stream.jsonl.gz'], retained['replay/expected-stream.jsonl.gz'])
        self.assertEqual(decode_stream(retained['generate/stream.jsonl.gz'], proofs[0]['stream_encoding']), STREAM)
        for phase in ('generate', 'replay'):
            self.assertEqual(decode(retained[phase + '/computed-result.json']), RESULT)
        self.assertIs(self.meter['accounting_complete'], True)
        self.assertGreater(self.meter['materialized_bytes'], sum(map(len, self.source.values())) * 2)

    def test_controller_transport_never_imports_numpy_or_native_kernel(self):
        import builtins
        original = builtins.__import__
        def checked(name, *args, **kwargs):
            self.assertFalse(name == 'numpy' or name.startswith('numpy.') or name.startswith('_trf_stationary_native'))
            return original(name, *args, **kwargs)
        with patch('builtins.__import__', side_effect=checked): self.execute()

    def test_malformed_response_keeps_generation_stream_result_and_diagnostics(self):
        def mutate(response, directory, phase): response['extra'] = True
        with self.assertRaises(REJECTED): self.execute(mutate)
        self.assertEqual(len(self.calls), 1)
        retained = dict(self.outputs)
        self.assertIn('generate/stream.jsonl.gz', retained)
        self.assertEqual(decode(retained['generate/computed-result.json']), RESULT)
        self.assertIn('generate/child-errors.txt', retained)
        self.assertIs(self.meter['accounting_complete'], True)

    def test_stale_generation_or_replay_environment_is_denied_with_available_output_retained(self):
        for phase in ('generate', 'replay'):
            for field in ('environment_before', 'environment'):
                self.calls.clear(); self.outputs.clear()
                def mutate(response, directory, observed_phase):
                    if observed_phase == phase: response[field] = {'stale': True}
                with self.subTest(phase=phase, field=field), self.assertRaises(REJECTED): self.execute(mutate)
                self.assertIn(phase + '/computed-result.json', dict(self.outputs))
                self.assertEqual(len(self.calls), 1 if phase == 'generate' else 2)

    def test_replay_engine_substitution_result_mismatch_and_changed_stream_cannot_pass(self):
        def engines(response, directory, phase):
            if phase == 'replay': response['draw_engines'] = [{'length': 4, 'native': False}]
        def result(response, directory, phase):
            if phase == 'replay': response['result']['verified_result_hash'] = '0' * 64
        def stream(response, directory, phase):
            if phase == 'replay':
                path = directory / 'expected-stream.jsonl.gz'
                path.write_bytes(path.read_bytes() + b'changed')
                response['stream_blob'] = descriptor(path.read_bytes())
        for mutate in (engines, result, stream):
            self.calls.clear(); self.outputs.clear()
            with self.subTest(mutation=mutate.__name__), self.assertRaises(REJECTED): self.execute(mutate)
            self.assertEqual(len(self.calls), 2)
            self.assertIn('replay/computed-result.json', dict(self.outputs))

    def test_source_or_response_identity_mutation_is_denied_before_replay(self):
        def source(response, directory, phase):
            (directory / next(iter(self.source))).write_bytes(b'changed source')
        for mutate in (source, lambda response, directory, phase: response.update(request_hash='0' * 64),
                       lambda response, directory, phase: response.update(footprint={}),
                       lambda response, directory, phase: response.update(native_binding='0' * 64),
                       lambda response, directory, phase: response['stream_blob'].update(sha256='0' * 64)):
            self.calls.clear(); self.outputs.clear()
            with self.subTest(mutation=mutate), self.assertRaises(REJECTED): self.execute(mutate)
            self.assertEqual(len(self.calls), 1)
            self.assertIn('generate/computed-result.json', dict(self.outputs))

    def test_child_transport_error_retains_actual_prefix_without_fabricated_replay(self):
        def broken(command, directory, timeout):
            directory = Path(directory)
            (directory / 'stream.jsonl.gz').write_bytes(b'partial gzip prefix')
            (directory / 'child-errors.txt').write_bytes(b'Independent synthetic timeout')
            raise TimeoutError('Independent synthetic process failure')
        with patch.object(study_runs, '_run_child', side_effect=broken), self.assertRaises(TimeoutError):
            study_runs.execute_attempt(self.source, self.payload, self.study_manifest, self.world,
                b'{}\n', lambda: 10, self.meter, self.outputs, _native=self.selected)
        self.assertEqual(dict(self.outputs)['generate/stream.jsonl.gz'], b'partial gzip prefix')
        self.assertFalse(any(name.startswith('replay/') for name, raw in self.outputs))
        self.assertIs(self.meter['accounting_complete'], True)

    def test_storage_refusal_precedes_child_and_keeps_existing_meter(self):
        self.study_manifest['profile']['budget']['attempt_storage_bytes'] = 1
        with patch.object(study_runs, '_run_child') as child, self.assertRaises(REJECTED):
            study_runs.execute_attempt(self.source, self.payload, self.study_manifest, self.world,
                b'{}\n', lambda: 10, self.meter, self.outputs, _native=self.selected)
        child.assert_not_called()
        self.assertEqual(self.outputs, [])
        self.assertEqual(self.meter, {'materialized_bytes': 0, 'accounting_complete': True})

    def test_failed_output_inventory_keeps_usage_unknown_and_available_prefix(self):
        def mutate(response, directory, phase):
            path = directory / 'computed-result.json'
            path.unlink()
            path.mkdir()
        with self.assertRaises(REJECTED): self.execute(mutate)
        self.assertIs(self.meter['accounting_complete'], False)
        self.assertIn('generate/stream.jsonl.gz', dict(self.outputs))
        self.assertFalse(any(name.startswith('replay/') for name, raw in self.outputs))

    def test_resource_stopped_generation_keeps_one_proof_without_starting_replay(self):
        stopped = {**deepcopy(RESULT), 'outcome': {'state': 'TECHNICAL_FAILURE'}}
        def mutate(response, directory, phase):
            response['result'] = stopped
            (directory / 'computed-result.json').write_text(canonical(stopped), encoding='utf-8')
        result, proofs = self.execute(mutate)
        self.assertEqual(result, stopped)
        self.assertEqual(len(proofs), 1)
        self.assertEqual([call['phase'] for call in self.calls], ['generate'])
        self.assertEqual(decode(dict(self.outputs)['generate/computed-result.json']), stopped)

    def child_request(self, directory, verify=None):
        request = {'payload': deepcopy(self.payload), 'manifest': deepcopy(self.study_manifest),
                   'world': self.world, 'footprint': footprint(self.source), 'verify': verify,
                   'stream_limit': 1024**2, 'native': deepcopy(self.selected)}
        (directory / 'cases.jsonl').write_bytes(b'{}\n')
        path = directory / 'request.json'
        path.write_text(canonical(request), encoding='utf-8')
        return path

    def child_seams(self, calculate, *, factory=None, environment=None, source=None):
        stack = ExitStack()
        stack.enter_context(patch.object(sys, 'path', list(sys.path)))
        stack.enter_context(patch.object(pipeline, 'source_bundle', side_effect=source or (lambda: self.source)))
        stack.enter_context(patch.object(pipeline, 'environment', side_effect=environment or
                                        (lambda *args, **kwargs: {'invented_environment': 'current'})))
        numpy = types.SimpleNamespace(__version__='never imported NumPy')
        core = types.SimpleNamespace(implementation_info=lambda: deepcopy(pipeline.INFO))
        stack.enter_context(patch.object(pipeline.importlib, 'import_module',
            side_effect=lambda name: {'numpy': numpy, '_trf_stationary_native': core}[name]))
        stack.enter_context(patch.object(pipeline, 'make_draw_factory', return_value=factory or (lambda *args: None)))
        stack.enter_context(patch.object(pipeline, 'calculate_world', side_effect=calculate))
        return stack

    def test_child_forwards_unsupported_numeric_fallback_without_advancing_rng_or_omitting_sinks(self):
        directory = self.root / 'child'; directory.mkdir()
        path = self.child_request(directory)
        rng = random.Random(743)
        state = rng.getstate()
        rows = [(0, 0, 0, 0), (1, Fraction(1, 3), 1, Fraction(1, 3))]
        seen = []
        def factory(actual_rng, actual_rows, length):
            self.assertIs(actual_rng, rng); self.assertIs(actual_rows, rows)
            self.assertEqual(length, 4)
            seen.append('unsupported numeric input returned None')
            return None
        def calculate(payload, manifest_value, world, cases, retain, **options):
            self.assertEqual(cases, [{}])
            self.assertEqual(set(options), {'retain_draw_bytes', 'retain_family_draw_bytes', '_draw_factory'})
            self.assertIsNone(options['_draw_factory'](rng, rows, 4))
            retain({'kind': 'case', 'value': {'invented': True}})
            options['retain_draw_bytes'](b'{"invented_draw":true}')
            options['retain_family_draw_bytes'](b'{"kind":"family-fixture"}\n')
            return deepcopy(RESULT)
        output = io.StringIO()
        with self.child_seams(calculate, factory=factory), redirect_stdout(output): pipeline.child_entry(path)
        response = decode(output.getvalue())
        self.assertEqual(seen, ['unsupported numeric input returned None'])
        self.assertEqual(rng.getstate(), state)
        self.assertEqual(response['draw_engines'], [{'length': 4, 'native': False}])
        decoded = decode_stream((directory / 'stream.jsonl.gz').read_bytes(), response['stream_encoding'])
        self.assertEqual(decoded, STREAM + b'{"kind":"draw","value":{"invented_draw":true}}\n'
                         + b'{"kind":"family-fixture"}\n')
        self.assertEqual(decode((directory / 'computed-result.json').read_bytes()), RESULT)

    def test_child_refuses_factory_that_consumes_original_rng(self):
        directory = self.root / 'child'; directory.mkdir()
        path = self.child_request(directory)
        rng = random.Random(123)
        def factory(actual_rng, rows, length): actual_rng.random(); return None
        def calculate(payload, manifest_value, world, cases, retain, **options):
            options['_draw_factory'](rng, [(0, 0, 0, 0)], 4)
            return deepcopy(RESULT)
        with self.child_seams(calculate, factory=factory), self.assertRaises(REJECTED): pipeline.child_entry(path)
        self.assertFalse((directory / 'computed-result.json').exists())
        self.assertTrue((directory / 'stream.jsonl.gz').exists())

    def test_child_post_environment_or_source_failure_keeps_full_computed_result_and_stream(self):
        for cause in ('environment', 'source'):
            directory = self.root / cause; directory.mkdir()
            path = self.child_request(directory)
            observed = [0]
            def environment(*args, **kwargs):
                observed[0] += 1
                if observed[0] == 2 and cause == 'environment': raise Invalid('Synthetic post-use environment failure')
                return {'invented_environment': 'current'}
            source_calls = [0]
            def source():
                source_calls[0] += 1
                return {} if source_calls[0] == 2 and cause == 'source' else self.source
            def calculate(payload, manifest_value, world, cases, retain, **options):
                retain({'kind': 'case', 'value': {'invented': True}})
                return deepcopy(RESULT)
            output = io.StringIO()
            with self.subTest(cause=cause), self.child_seams(calculate, environment=environment, source=source), \
                    redirect_stdout(output), self.assertRaises(REJECTED): pipeline.child_entry(path)
            self.assertEqual(output.getvalue(), '')
            self.assertEqual(decode((directory / 'computed-result.json').read_bytes()), RESULT)
            self.assertGreater((directory / 'stream.jsonl.gz').stat().st_size, 10)

    def test_child_replay_result_mismatch_retains_computed_bytes_without_success_response(self):
        directory = self.root / 'replay'; directory.mkdir()
        path = self.child_request(directory, verify='0' * 64)
        with (directory / 'expected-stream.jsonl.gz').open('xb') as stream:
            encoded = EncodedStream(stream, encoded_limit=1024**2)
            encoded.write(STREAM); encoded.finish()
        def calculate(payload, manifest_value, world, cases, retain, **options):
            retain({'kind': 'case', 'value': {'invented': True}})
            return deepcopy(RESULT)
        output = io.StringIO()
        with self.child_seams(calculate), redirect_stdout(output), self.assertRaises(REJECTED): pipeline.child_entry(path)
        self.assertEqual(output.getvalue(), '')
        self.assertEqual(decode((directory / 'computed-result.json').read_bytes()), RESULT)


if __name__ == '__main__':
    unittest.main()
