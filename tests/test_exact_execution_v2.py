"""Native resource-version binding; no actual provider or market evidence."""
import unittest
from pathlib import Path
import tempfile

from exact_execution_v2_support import ExactExecutionV2Fixture
from test_exact_composition_v2_review import supplied
from trading_researcher import exact_composition_v2 as composition, exact_runtime_v2 as runtime
from trading_researcher.codec import Invalid, digest


class ExactRetainedCompositionV2(unittest.TestCase):
    def test_separate_child_binds_complete_compilation_and_six_independent_goldens(self):
        value = supplied()
        compiled = runtime.compile_payload(value)
        with tempfile.TemporaryDirectory() as directory:
            report = composition.run_child(composition.read_bundle(), value, digest(compiled), directory)
            self.assertEqual(report['result']['resource_contract'], 'exact-computation-resources/2.0')
            self.assertEqual(len(report['result']['checks']['passed_cases']), 6)
            self.assertEqual(len(report['footprint']), 37)
            self.assertEqual(report['result']['compilation_hash'], digest(compiled))
            self.assertFalse(list(Path(directory).rglob('*.pyc')))

    def test_changed_binding_or_independent_expected_source_rejects(self):
        value = supplied()
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(Invalid):
            composition.run_child(composition.read_bundle(), value, '0' * 64, directory)
        changed = composition.read_bundle()
        changed[composition.TEST] += b'\n# changed independent expectation\n'
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(Invalid):
            composition.run_child(changed, value, digest(runtime.compile_payload(value)), directory)


class ExactNativeV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = ExactExecutionV2Fixture()
        cls.addClassCleanup(cls.f.close)

    def test_owned_twenty_million_route_keeps_complete_replay(self):
        f = self.f
        self.assertEqual(f.runtime['body']['schema'], 'exact-reference-certificate/2')
        self.assertEqual(f.runtime['body']['result']['result']['tests'], 72)
        compiled = f.compile(20_000_000)
        self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'])
        self.assertEqual(compiled['body']['compilation']['request']['max_steps'], 20_000_000)
        composed = f.composition(compiled['id'])
        self.assertEqual(composed['body']['status'], 'CONFORMANT', composed['body'])
        executed = f.execute(compiled['id'], composed['id'])
        body = executed['body']
        self.assertEqual(body['schema'], 'exact-reference-execution/2')
        self.assertEqual(body['status'], 'DESCRIPTIVE_EXECUTION', body)
        self.assertTrue(body['complete_required_report'])
        self.assertIs(body['scientific_readiness'], False)
        self.assertEqual(body['verification']['result']['checked_cases'], 3)
        self.assertEqual(body['resource_usage']['aggregate_primitive_steps'],
            2 * body['verification']['result']['primitive_steps'])
        self.assertLessEqual(body['resource_usage']['aggregate_primitive_steps'], 40_000_000)
        events = body['operational_timing']['events']
        self.assertEqual([event['phase'] for event in events], ['operation_started', 'inputs_retained',
            'execute_completed', 'cases_retained', 'replay_started', 'replay_completed', 'checks_completed'])
        self.assertEqual([event['elapsed_ns'] for event in events], sorted(event['elapsed_ns'] for event in events))
        self.assertTrue(all(event['at_utc'].endswith('+00:00') for event in events))
        self.assertLessEqual(events[-1]['elapsed_ns'], 1800_000_000_000)
        capsule = f.broker._artifact(compiled['body']['input_id'])
        self.assertEqual(capsule['body']['data_use']['schema'], 'exact-development-data-use/2')
        self.assertIn('controlled_feedback', capsule['body']['data_use'])


if __name__ == '__main__':
    unittest.main()
