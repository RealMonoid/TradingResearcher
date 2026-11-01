"""Actual retained-process v2 checks; invented data, no registry or provider."""
from copy import deepcopy
from datetime import datetime
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_exact_runtime import payload, history, write_rows
from trading_researcher import exact_runtime as legacy, exact_runtime_v2 as runtime
from trading_researcher.codec import canonical, digest, Invalid


class ExactRetainedV2Tests(unittest.TestCase):
    def supplied(self):
        return payload(max_steps=20000000)

    def test_compile_keeps_actual20m_and_old_api_stays10m(self):
        supplied = self.supplied()
        before = canonical(supplied)
        compiled = runtime.compile_payload(supplied)
        self.assertEqual(compiled['schema'], 'exact-compilation/2')
        self.assertEqual(compiled['request']['schema'], 'exact-resource-case-request/2')
        self.assertEqual(compiled['request']['max_steps'], 20000000)
        self.assertEqual(compiled['resource_contract'], 'exact-computation-resources/2.0')
        self.assertEqual(canonical(supplied), before)
        with self.assertRaises(Invalid): legacy.compile_payload(supplied)
        for limit in (0, -1, True, 20000001, '20000000'):
            with self.subTest(limit=limit), self.assertRaises(Invalid):
                runtime.compile_payload({**supplied, 'max_steps': limit})

    def test_retained_child_runs_all72_bound_conformance_methods(self):
        with tempfile.TemporaryDirectory() as directory:
            result = runtime.run_child(runtime.read_bundle(), 'certify', {'profile': runtime.PROFILE}, directory)
            self.assertEqual(result['result'], {'schema': 'exact-conformance-result/2',
                'profile': runtime.PROFILE, 'resource_contract': runtime.RESOURCE_CONTRACT,
                'tests': 72, 'failures': 0, 'errors': 0, 'skipped': 0, 'scientific_readiness': False})
            self.assertEqual(result['environment']['isolation'], {'isolated': 1, 'no_site': 1,
                'ignore_environment': 1, 'no_bytecode_writes': 1})
            self.assertFalse(list(Path(directory).rglob('*.pyc')))

    def test_full_case_bytes_and_real_separate_replay_share_one_operation(self):
        supplied = self.supplied(); compiled = runtime.compile_payload(supplied)
        with tempfile.TemporaryDirectory() as directory:
            execution = {'compilation_input': supplied, 'compilation_hash': digest(compiled),
                'rows': write_rows(directory, history())}
            result = runtime.run_operation(runtime.read_bundle(), execution, directory)
            actual, checked = result['execution']['result'], result['verification']['result']
            self.assertEqual(actual['schema'], 'exact-execution-result/2')
            self.assertEqual(actual['report']['processed_case_count'], 55)
            self.assertTrue(actual['report']['diagnostics']['processing_complete'])
            self.assertEqual(checked['checked_cases'], 55)
            self.assertEqual(checked['result_hash'], digest(actual))
            self.assertEqual(checked['primitive_steps'] * 2, result['aggregate_primitive_steps'])
            self.assertLessEqual(result['aggregate_primitive_steps'], 40000000)
            self.assertEqual((Path(directory) / 'execute/cases.jsonl').read_bytes(),
                (Path(directory) / 'replay/cases.jsonl').read_bytes())
            timing = result['timing']
            self.assertEqual(timing['execute_elapsed_ns'] + timing['replay_elapsed_ns'], timing['total_elapsed_ns'])
            self.assertGreater(timing['total_elapsed_ns'], 0)
            self.assertLessEqual(timing['total_elapsed_ns'], 1800 * 1000000000)
            self.assertLessEqual(datetime.fromisoformat(timing['started_at_utc']),
                datetime.fromisoformat(timing['completed_at_utc']))
            self.assertEqual(actual['case_blob']['sha256'], hashlib.sha256((Path(directory) / 'execute/cases.jsonl').read_bytes()).hexdigest())

    def test_failed_replay_keeps_first_numeric_bytes(self):
        supplied = self.supplied(); compiled = runtime.compile_payload(supplied)
        original = runtime._run_retained
        def fail_replay(bundle, mode, *args, **kwargs):
            if mode == 'verify': raise Invalid('Synthetic separate replay failure')
            return original(bundle, mode, *args, **kwargs)
        with tempfile.TemporaryDirectory() as directory:
            execution = {'compilation_input': supplied, 'compilation_hash': digest(compiled),
                'rows': write_rows(directory, history())}
            with patch.object(runtime, '_run_retained', side_effect=fail_replay), self.assertRaises(Invalid):
                runtime.run_operation(runtime.read_bundle(), execution, directory)
            raw = (Path(directory) / 'execute/cases.jsonl').read_bytes()
            self.assertEqual(len(raw.splitlines()), 55)
            self.assertTrue((Path(directory) / 'execute/child-output.json').is_file())

    def test_plain_base_comparison_streams_more_than_one_mib(self):
        supplied = payload(count=5000, max_steps=20000000)
        catalog = {'y@1': {'type': 'real', 'unit': 'basis_points'}}
        program = lambda expression: {'schema': 'research-ast/4', 'catalog_hash': digest(catalog), 'expression': expression}
        candidate = supplied['candidate']
        candidate['scope_ast'] = program({'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True})
        candidate['condition_ast'] = program({'op': 'literal', 'type': 'boolean', 'unit': None, 'value': False})
        candidate['outcome'] = {'program': program({'op': 'lag', 'bars': 1,
            'arg': {'op': 'feature', 'ref': 'y@1'}}), 'scale': 'quantity'}
        candidate['horizons']['outcome_bars'] = 1
        candidate['feature_refs'] = ['y@1']
        supplied['catalog'] = catalog
        compiled = runtime.compile_payload(supplied)
        rows = [{'time': 1672531200 + i * 900, 'instrument': 'BTCUSDT',
            'features': {'y@1': {'value': '1', 'available_at': 1672531200 + (i + 1) * 900}}} for i in range(5000)]
        with tempfile.TemporaryDirectory() as directory:
            execution = {'compilation_input': supplied, 'compilation_hash': digest(compiled),
                'rows': write_rows(directory, rows)}
            result = runtime.run_operation(runtime.read_bundle(), execution, directory)
            actual = result['execution']['result']
            self.assertGreater(actual['case_blob']['size'], 1048576)
            self.assertEqual(actual['report']['processed_case_count'], 5000)
            self.assertEqual(result['verification']['result']['checked_cases'], 5000)

    def test_source_input_and_deadline_adversaries_fail_before_dispatch(self):
        bundle = runtime.read_bundle()
        changed = deepcopy(bundle); changed['trading_researcher/exact_resources_v2.py'] += b'\n# changed\n'
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(Invalid):
            runtime.run_child(changed, 'certify', {'profile': runtime.PROFILE}, directory)
        for limit in (0, True, 1801):
            with self.subTest(timeout=limit), tempfile.TemporaryDirectory() as directory, self.assertRaises(Invalid):
                runtime.run_operation(bundle, {}, directory, timeout=limit)
        for value in (None, {}, {'request': None, 'diagnostics': {}}):
            with self.subTest(report=value), self.assertRaises(Invalid): runtime.primitive_steps(value)


if __name__ == '__main__': unittest.main()
