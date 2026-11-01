"""Independent retained-runtime protocol checks using invented eight-row data.

Real isolated children cover the route. Explicit transport/clock doubles test
host boundary rejection and retention; those doubles are not conformance,
source ownership, a model response, a native admission, or a market result.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from test_exact_resources_v2_review import CATALOG, T, D, program, boolean, guard, binary, feature, real, rows, stamp
from trading_researcher import exact_runtime as legacy, exact_runtime_v2 as runtime
from trading_researcher.codec import Invalid, canonical, decode, digest


def supplied(steps=20_000_000):
    """An unaccepted engineering candidate, not a source/meaning certificate."""
    universe = {'start': stamp(T), 'end': stamp(T + 8 * D), 'instruments': ['SYNTHETIC']}
    validity = {'op': 'trailing_all', 'bars': 3, 'arg': feature('flag@1')}
    candidate = {'schema': 'hypothesis-exec/3', 'idea_ref': 'invented-runtime-review',
        'claim_kind': 'difference', 'comparator': {'kind': 'whole_scope'},
        'estimand': {'kind': 'conditional-minus-scope-mean/1', 'weighting': 'equal_rows',
            'missingness': 'scope-true-outcome-observed/1',
            'condition_unknown': 'exclude-from-condition-retain-in-scope',
            'nuisance_fit': 'none', 'unit': 'basis_points', 'direction': 'nondirectional'},
        'scope_ast': program(boolean(True)),
        'condition_ast': program(guard(validity, binary('gt', feature('x@1'), real(1)))),
        'outcome': {'program': program(binary('mul', real(1, 'basis_points'), feature('x@1'))),
                    'scale': 'quantity'},
        'horizons': {'grid_seconds': D, 'outcome_bars': 1},
        'test_universe': {**universe, 'data_snapshot_ref': 'no-native-snapshot'},
        'parameter_origins': [], 'feature_refs': ['flag@1', 'x@1']}
    return {'formalization_id': 'no-native-formalization', 'candidate': candidate,
        'catalog': deepcopy(CATALOG), 'data_manifest': {'partition': 'development', 'universe': universe},
        'as_of': stamp(T + 8 * D), 'max_steps': steps}


def write_rows(directory, data=None):
    raw = ''.join(canonical(row) + '\n' for row in (rows() if data is None else data)).encode('utf-8')
    (Path(directory) / 'rows.jsonl').write_bytes(raw)
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def execution_input(directory, steps=20_000_000):
    original = supplied(steps)
    return {'compilation_input': original, 'compilation_hash': digest(runtime.compile_payload(original)),
            'rows': write_rows(directory)}


class ExactRuntimeV2Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.directory.cleanup)
        cls.bundle = runtime.read_bundle()
        cls.input = execution_input(cls.directory.name)
        cls.actual = runtime.run_operation(cls.bundle, cls.input, cls.directory.name)
        cls.case_bytes = (Path(cls.directory.name) / 'execute/cases.jsonl').read_bytes()

    def protocol(self, *, execute_change=None, verify_change=None, fail_verify=False):
        """A controlled child seam; no source/OS isolation assertion is made."""
        calls = []
        current = {}

        def retained(bundle, mode, payload, directory, timeout):
            calls.append((mode, timeout))
            if mode == 'execute':
                body = deepcopy(self.actual['execution']['result'])
                if execute_change is not None: execute_change(body)
                (Path(directory) / 'cases.jsonl').write_bytes(self.case_bytes)
                current['result'] = body
            else:
                if fail_verify: raise Invalid('Retained separate-replay failure fixture')
                original = current['result']
                used = original['report']['primitive_steps'] + original['report']['diagnostics']['primitive_steps']
                body = {'schema': 'exact-case-verification/2', 'resource_contract': runtime.RESOURCE_CONTRACT,
                    'result_hash': digest(original), 'compilation_hash': payload['execution_input']['compilation_hash'],
                    'case_blob': deepcopy(original['case_blob']),
                    'checked_cases': original['report']['processed_case_count'],
                    'primitive_steps': used, 'scientific_readiness': False}
                if verify_change is not None: verify_change(body)
            envelope = deepcopy(self.actual['execution' if mode == 'execute' else 'verification'])
            envelope.update(mode=mode, request_hash=digest(payload), result=body)
            return envelope
        return calls, retained

    def run_protocol(self, directory, retained, *, clock=None, timeout=1800):
        payload = execution_input(directory)
        with patch.object(runtime, '_run_retained', side_effect=retained):
            if clock is None:
                return runtime.run_operation(self.bundle, payload, directory, timeout=timeout)
            with patch.object(runtime.time, 'monotonic_ns', side_effect=clock):
                return runtime.run_operation(self.bundle, payload, directory, timeout=timeout)

    def assert_retained(self, directory):
        self.assertEqual((Path(directory) / 'execute/cases.jsonl').read_bytes(), self.case_bytes)

    def test_real_two_child_operation_binds_exact_stream_and_operational_timing(self):
        actual = self.actual
        result, verified = actual['execution']['result'], actual['verification']['result']
        self.assertEqual(actual['execution']['mode'], 'execute')
        self.assertEqual(actual['verification']['mode'], 'verify')
        self.assertEqual(result['schema'], 'exact-execution-result/2')
        self.assertEqual(verified, {'schema': 'exact-case-verification/2',
            'resource_contract': 'exact-computation-resources/2.0', 'result_hash': digest(result),
            'compilation_hash': self.input['compilation_hash'], 'case_blob': result['case_blob'],
            'checked_cases': 8, 'primitive_steps': 274, 'scientific_readiness': False})
        self.assertEqual(actual['aggregate_primitive_steps'], 548)
        self.assertEqual(len(self.case_bytes.splitlines()), 8)
        self.assertEqual(result['case_blob'], {'sha256': hashlib.sha256(self.case_bytes).hexdigest(),
                                              'size': len(self.case_bytes)})
        self.assertEqual((Path(self.directory.name) / 'replay/cases.jsonl').read_bytes(), self.case_bytes)
        for mode in ('execution', 'verification'):
            self.assertEqual(actual[mode]['environment']['isolation'],
                             {'isolated': 1, 'no_site': 1, 'ignore_environment': 1, 'no_bytecode_writes': 1})
            self.assertEqual(actual[mode]['footprint'],
                             {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(self.bundle.items())})
        timing = actual['timing']
        self.assertEqual(timing['total_elapsed_ns'], timing['execute_elapsed_ns'] + timing['replay_elapsed_ns'])
        self.assertGreaterEqual(timing['execute_elapsed_ns'], 0)
        self.assertGreaterEqual(timing['replay_elapsed_ns'], 0)
        self.assertLessEqual(timing['total_elapsed_ns'], 1800 * 1_000_000_000)
        self.assertLessEqual(datetime.fromisoformat(timing['started_at_utc']),
                             datetime.fromisoformat(timing['completed_at_utc']))
        self.assertNotIn('timing', result)

    def test_complete_verifier_body_must_match_the_execution_and_json_types(self):
        changes = {
            'result_hash': lambda body: body.update(result_hash='0' * 64),
            'compilation_hash': lambda body: body.update(compilation_hash='0' * 64),
            'case_hash': lambda body: body['case_blob'].update(sha256='0' * 64),
            'case_size': lambda body: body['case_blob'].update(size=body['case_blob']['size'] + 1),
            'checked_cases': lambda body: body.update(checked_cases=7),
            'case_count_type': lambda body: body.update(checked_cases=8.0),
            'scientific_type': lambda body: body.update(scientific_readiness=0),
            'missing_identity': lambda body: body.pop('result_hash'),
            'extra_field': lambda body: body.update(unbound=True),
        }
        for label, change in changes.items():
            with self.subTest(field=label), tempfile.TemporaryDirectory() as directory:
                calls, retained = self.protocol(verify_change=change)
                with self.assertRaises(Invalid): self.run_protocol(directory, retained)
                self.assertEqual([mode for mode, _ in calls], ['execute', 'verify'])
                self.assert_retained(directory)

    def test_counter_types_shared_per_child_maximum_and_aggregate_boundary(self):
        for field, value in (('numerical', True), ('numerical', -1), ('diagnostic', False),
                             ('diagnostic', 1.0), ('budget', 0), ('budget', 20_000_001)):
            bad = deepcopy(self.actual['execution']['result']['report'])
            if field == 'budget': bad['request']['max_steps'] = value
            elif field == 'numerical': bad['primitive_steps'] = value
            else: bad['diagnostics']['primitive_steps'] = value
            with self.subTest(field=field, value=value), self.assertRaises(Invalid):
                runtime.primitive_steps(bad)
        for amount in (20_000_000, 20_000_001):
            def change(body):
                body['report']['primitive_steps'] = amount - 1
                body['report']['diagnostics']['primitive_steps'] = 1
            with self.subTest(total=amount), tempfile.TemporaryDirectory() as directory:
                calls, retained = self.protocol(execute_change=change)
                if amount > 20_000_000:
                    with self.assertRaises(Invalid): self.run_protocol(directory, retained)
                    self.assertEqual([mode for mode, _ in calls], ['execute'])
                else:
                    answer = self.run_protocol(directory, retained)
                    self.assertEqual(answer['aggregate_primitive_steps'], 40_000_000)
        for bad in (-1, True, 274.0, 275, 20_000_001):
            calls, retained = self.protocol(verify_change=lambda body, value=bad: body.update(primitive_steps=value))
            with self.subTest(replay=bad), tempfile.TemporaryDirectory() as directory, self.assertRaises(Invalid):
                self.run_protocol(directory, retained)

    def test_shared_deadline_passes_only_remaining_time_and_exact_phase_durations(self):
        clock = [0, 250_000_000, 1_250_000_000, 1_500_000_000, 1_750_000_000]
        calls, retained = self.protocol()
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_protocol(directory, retained, clock=clock, timeout=2)
        self.assertEqual(calls, [('execute', 1.75), ('verify', 0.5)])
        self.assertEqual(result['timing']['execute_elapsed_ns'], 1_250_000_000)
        self.assertEqual(result['timing']['replay_elapsed_ns'], 500_000_000)
        self.assertEqual(result['timing']['total_elapsed_ns'], 1_750_000_000)
        self.assertEqual(result['timing']['shared_timeout_seconds'], 2)

    def test_exhausted_deadline_never_dispatches_first_child(self):
        calls, retained = self.protocol()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(Invalid):
                self.run_protocol(directory, retained, clock=[0, 1_000_000_000], timeout=1)
            self.assertEqual(calls, [])

    def test_late_execute_or_replay_retains_first_bytes_and_does_not_retry(self):
        for clock, count in (([0, 0, 1_000_000_001], 1),
                             ([0, 0, 100_000_000, 100_000_000, 1_000_000_001], 2)):
            with self.subTest(phases=count), tempfile.TemporaryDirectory() as directory:
                calls, retained = self.protocol()
                with self.assertRaises(Invalid): self.run_protocol(directory, retained, clock=clock, timeout=1)
                self.assertEqual(len(calls), count)
                self.assert_retained(directory)

    def test_replay_and_clock_errors_keep_execute_bytes(self):
        for label in ('replay', 'clock'):
            with self.subTest(failure=label), tempfile.TemporaryDirectory() as directory:
                calls, retained = self.protocol(fail_verify=label == 'replay')
                if label == 'clock':
                    with self.assertRaises(OSError):
                        self.run_protocol(directory, retained, clock=[0, 0, OSError('clock unavailable')])
                else:
                    with self.assertRaises(Invalid): self.run_protocol(directory, retained)
                self.assert_retained(directory)
                self.assertEqual(len(calls), 1 if label == 'clock' else 2)

    def test_v2_compilation_retains_exact_budget_and_full_causal_window(self):
        original = supplied(); before = canonical(original)
        with patch.object(legacy, 'compile_payload', wraps=legacy.compile_payload) as structural:
            compiled = runtime.compile_payload(original)
        self.assertEqual(structural.call_args.args[0]['max_steps'], 10_000_000)
        self.assertEqual(compiled['request']['max_steps'], 20_000_000)
        self.assertEqual(compiled['schema'], 'exact-compilation/2')
        self.assertEqual(compiled['candidate_hash'], digest(original['candidate']))
        self.assertEqual(compiled['warmup_seconds'], 2 * D)
        self.assertEqual(compiled['unavailable_warmup_seconds'], 2 * D)
        self.assertEqual(compiled['row_window'], original['data_manifest']['universe'])
        self.assertEqual(compiled['maximum_input_rows'], 8)
        self.assertEqual(compiled['expected_case_count'], 8)
        self.assertEqual(canonical(original), before)
        for limit in (True, 0, -1, 20_000_001, 20_000_000.0):
            with self.subTest(limit=limit), patch.object(legacy, 'compile_payload') as forbidden:
                with self.assertRaises(Invalid): runtime.compile_payload({**original, 'max_steps': limit})
                forbidden.assert_not_called()
        with self.assertRaises(Invalid): legacy.compile_payload(original)

    def test_protected_manifest_and_invalid_versions_fail_before_raw_row_loader(self):
        changes = [lambda value: value['data_manifest'].update(partition='assessment'),
                   lambda value: value['data_manifest']['universe'].update(instruments=['OTHER']),
                   lambda value: value['data_manifest']['universe'].update(end=stamp(T + 7 * D)),
                   lambda value: value['candidate'].update(schema='hypothesis-exec/2'),
                   lambda value: value['candidate']['scope_ast'].update(schema='research-ast/2'),
                   lambda value: value['candidate']['scope_ast'].update(catalog_hash='0' * 64)]
        for index, change in enumerate(changes):
            payload = deepcopy(self.input); change(payload['compilation_input'])
            with self.subTest(change=index), patch.object(legacy, '_read_rows') as forbidden:
                with self.assertRaises(Invalid): runtime._calculate(payload, Path(self.directory.name))
                forbidden.assert_not_called()

    def test_actual_replay_rejects_case_suffix_corruption_and_compilation_changes(self):
        for label in ('suffix', 'byte', 'row', 'compilation', 'report_type'):
            with self.subTest(change=label), tempfile.TemporaryDirectory() as directory:
                path = Path(directory)
                write_rows(path)
                (path / 'cases.jsonl').write_bytes(self.case_bytes)
                payload = {'execution_input': deepcopy(self.input), 'result': deepcopy(self.actual['execution']['result'])}
                if label == 'suffix':
                    with (path / 'cases.jsonl').open('ab') as stream: stream.write(b'\n')
                elif label == 'byte':
                    raw = bytearray(self.case_bytes); raw[10] ^= 1; (path / 'cases.jsonl').write_bytes(raw)
                elif label == 'row':
                    changed = rows(); changed[4]['features']['x@1']['value'] = '99'; write_rows(path, changed)
                elif label == 'compilation': payload['execution_input']['compilation_hash'] = '0' * 64
                else: payload['result']['report']['scientific_readiness'] = 0
                with self.assertRaises(Invalid): runtime._verify(payload, path)

    def test_low_level_row_descriptor_json_types_are_not_coerced(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = execution_input(directory)
            payload['rows']['size'] = float(payload['rows']['size'])
            with self.assertRaises(Invalid): runtime._calculate(payload, Path(directory))

    def test_outside_row_selection_and_typed_compilation_binding_are_rejected(self):
        for label in ('before', 'instrument', 'hash'):
            with self.subTest(change=label), tempfile.TemporaryDirectory() as directory:
                payload = execution_input(directory)
                data = rows()
                if label == 'before': data[0]['time'] -= D
                elif label == 'instrument': data[0]['instrument'] = 'OTHER'
                else: payload['compilation_hash'] = '0' * 64
                payload['rows'] = write_rows(directory, data)
                with self.assertRaises(Invalid): runtime._calculate(payload, Path(directory))

    def test_returned_child_envelope_hash_mode_environment_and_source_are_bound(self):
        good = deepcopy(self.actual['execution'])
        original = supplied()
        good.update(mode='compile', request_hash=digest(original), result=runtime.compile_payload(original))
        changes = {'mode': lambda answer: answer.update(mode='execute'),
                   'request_hash': lambda answer: answer.update(request_hash='0' * 64),
                   'footprint': lambda answer: answer['footprint'].update({'unexpected.py': '0' * 64}),
                   'environment': lambda answer: answer['environment']['identity'].update(version='not-this-runtime')}
        for label, change in changes.items():
            answer = deepcopy(good); change(answer)
            with self.subTest(change=label), tempfile.TemporaryDirectory() as directory:
                with patch('trading_researcher.binance_normalize._run_child', return_value=answer), self.assertRaises(Invalid):
                    runtime.run_child(self.bundle, 'compile', original, directory)

    def test_staged_and_installed_source_drift_are_not_silently_rebound(self):
        original = supplied()
        good = deepcopy(self.actual['execution'])
        good.update(mode='compile', request_hash=digest(original), result=runtime.compile_payload(original))
        owner = 'trading_researcher/exact_resources_v2.py'
        with tempfile.TemporaryDirectory() as directory:
            def alter_staged(command, target, timeout):
                path = Path(target) / owner
                path.write_bytes(path.read_bytes() + b'\n# staged drift\n')
                return deepcopy(good)
            with patch('trading_researcher.binance_normalize._run_child', side_effect=alter_staged), self.assertRaises(Invalid):
                runtime.run_child(self.bundle, 'compile', original, directory)
        changed = {**self.bundle, owner: self.bundle[owner] + b'\n# installed fixture drift\n'}
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(runtime, 'read_bundle', side_effect=[self.bundle, changed]), \
                    patch('trading_researcher.binance_normalize._run_child', return_value=good), self.assertRaises(Invalid):
                runtime.run_child(self.bundle, 'compile', original, directory)

    def test_invalid_timeout_and_source_membership_fail_before_subprocess(self):
        for timeout in (True, False, 0, -1, 1801, 1.0):
            with self.subTest(timeout=timeout), tempfile.TemporaryDirectory() as directory:
                with patch('trading_researcher.binance_normalize._run_child') as forbidden:
                    with self.assertRaises(Invalid):
                        runtime.run_child(self.bundle, 'compile', supplied(), directory, timeout=timeout)
                    forbidden.assert_not_called()
        for label in ('missing', 'extra', 'raw_type', 'modified'):
            changed = dict(self.bundle)
            key = 'trading_researcher/exact_resources_v2.py'
            if label == 'missing': changed.pop(key)
            elif label == 'extra': changed['../untrusted.py'] = b''
            elif label == 'raw_type': changed[key] = bytearray(changed[key])
            else: changed[key] += b'\n# different\n'
            with self.subTest(bundle=label), tempfile.TemporaryDirectory() as directory:
                with patch('trading_researcher.binance_normalize._run_child') as forbidden:
                    with self.assertRaises(Invalid): runtime.run_child(changed, 'compile', supplied(), directory)
                    forbidden.assert_not_called()
        self.assertNotIn('tests/test_exact_runtime_v2_review.py', runtime.FILES)

    def test_real_resource_stopped_prefix_replays_without_claiming_completeness(self):
        with tempfile.TemporaryDirectory() as directory:
            payload = execution_input(directory, steps=1)
            result = runtime.run_operation(self.bundle, payload, directory)
            actual = result['execution']['result']
            self.assertEqual(actual['report']['processed_case_count'], 0)
            self.assertEqual(actual['report']['status'], 'RESOURCE_STOP')
            self.assertFalse(actual['report']['diagnostics']['processing_complete'])
            self.assertEqual(actual['contrast']['status'], 'RESOURCE_STOP')
            self.assertIsNone(actual['contrast']['effect'])
            self.assertEqual(result['verification']['result']['checked_cases'], 0)
            self.assertEqual(result['aggregate_primitive_steps'], 2)
            self.assertEqual((Path(directory) / 'execute/cases.jsonl').read_bytes(), b'')


if __name__ == '__main__':
    unittest.main()
