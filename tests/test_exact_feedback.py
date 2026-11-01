"""Fresh native integration of controlled feedback data-use routing; synthetic only."""
import unittest
from unittest.mock import patch

import exact_execution_support as support
from trading_researcher.codec import canonical, decode, digest
from trading_researcher.exact_execution import ExactExecutionBroker
from trading_researcher.exact_feedback import ExactFeedbackBroker, FILES, PROFILE, SCHEMA


class ExactFeedbackNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Construct under the new entry point before any qualification or
        # frozen input. No historical source/epoch binding is refreshed.
        with patch.object(support, 'ExactExecutionBroker', ExactFeedbackBroker):
            cls.f = support.ExactExecutionFixture()
        cls.addClassCleanup(cls.f.close)

    def test_new_source_identity_is_in_both_native_and_runtime_bindings(self):
        host = self.f.broker
        for sources in (host._execution_sources(), host._exact_source_identity(),
                        self.f.runtime['body']['host_sources']):
            self.assertTrue(set(FILES) <= set(sources))
        self.assertIn('BreakoutFeedbackBroker', {base.__name__ for base in type(host).__mro__})

    def test_complete_native_route_retains_versioned_data_use_and_fresh_replay(self):
        f = self.f
        compiled = f.compile()
        self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'])
        composition = f.composition(compiled['id'])
        self.assertEqual(composition['body']['status'], 'CONFORMANT', composition['body'])
        result = f.execute(compiled['id'], composition['id'])
        body = result['body']
        self.assertEqual(body['status'], 'DESCRIPTIVE_EXECUTION', body)
        self.assertTrue(body['complete_required_report'])
        self.assertIs(body['scientific_readiness'], False)
        self.assertEqual(body['verification']['result']['checked_cases'], 3)
        self.assertEqual(body['verification']['result']['result_hash'], digest(body['result']))
        cases = [decode(line) for line in f.broker._read_blob_bytes(body['result']['case_blob']['sha256']).splitlines()]
        self.assertEqual(len(cases), 3)
        capsule = f.broker._artifact(compiled['body']['input_id'])
        use = capsule['body']['data_use']
        self.assertEqual(use['schema'], SCHEMA)
        self.assertEqual(use['controlled_feedback']['profile'], PROFILE)
        self.assertEqual(use['status'], 'QUALIFIED')
        self.assertEqual(use['controlled_feedback']['installed_sources'], f.broker._execution_sources())
        self.assertFalse(use['independent_confirmation'])

    def test_existing_data_use_result_is_preserved_as_a_distinct_version(self):
        f = self.f
        compiled = f.compile()
        self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'])
        target, dependencies, payload = f.broker._exact_compiled(compiled['id'])
        old = ExactExecutionBroker._exact_data_use(f.broker, dependencies)
        current = f.broker._exact_data_use(dependencies)
        self.assertEqual(old['schema'], 'exact-development-data-use/1')
        self.assertEqual(current['schema'], SCHEMA)
        self.assertNotEqual(canonical(old), canonical(current))
        for key in old.keys() - {'schema'}:
            self.assertEqual(canonical(current[key]), canonical(old[key]))
        self.assertEqual(target['id'], compiled['id'])
        self.assertEqual(payload['max_steps'], 100000)


if __name__ == '__main__':
    unittest.main()
