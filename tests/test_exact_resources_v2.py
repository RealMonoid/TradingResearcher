"""D098 pure calculation version; resource success grants no native authority."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from test_exact_compositions import FIXTURE
from test_exact_outcomes_review import a_history as history, a_request
from trading_researcher import exact_resources_v2 as resources
from trading_researcher import exact_resource_candidate as engineering
from trading_researcher.codec import canonical
from trading_researcher.exact_outcomes import materialize_exact
from trading_researcher.expressions import ExpressionGap


def selected_request(steps=20000000):
    result = a_request()
    guard = result['condition_program']['expression']['arg']
    validity, predicate = guard['left']['left'], guard['left']['right']
    result['condition_program']['expression']['arg'] = {'op': 'eq',
        'left': {'op': 'or', 'left': validity, 'right': guard['right']['right']}, 'right': predicate}
    return {**result, 'schema': resources.REQUEST, 'max_steps': steps}


class ExactResourceV2Tests(unittest.TestCase):
    def test_distinct_approved_contract_and_typed_limit_preserve_old_versions(self):
        self.assertEqual(resources.PROFILE, 'exact-reference-computation/2')
        self.assertEqual(resources.RESOURCE_CONTRACT, 'exact-computation-resources/2.0')
        self.assertEqual(engineering.ACTIVATION, 'PENDING_SPECIFIC_RESOURCE_DECISION')
        for limit in (0, True, False, -1, '20000000', 20000001):
            with self.subTest(limit=limit), self.assertRaises(ExpressionGap):
                resources.materialize(selected_request(limit), FIXTURE['catalog'], history())
        actual = selected_request()
        with self.assertRaises(ExpressionGap):
            materialize_exact({**actual, 'schema': 'exact-composition-case-request/1'}, FIXTURE['catalog'], history())
        with self.assertRaises(ExpressionGap):
            engineering.materialize(actual, FIXTURE['catalog'], history())

    def test_complete_numeric_and_diagnostic_results_keep_actual_budget_and_base(self):
        catalog, rows = FIXTURE['catalog'], history()
        base = resources.materialize(selected_request(), catalog, rows)
        reference = engineering.materialize({**selected_request(), 'schema': engineering.REQUEST}, catalog, rows)
        self.assertEqual(base['cases'], reference['cases'])
        self.assertEqual(base['primitive_steps'], reference['primitive_steps'])
        self.assertEqual(base['request']['max_steps'], 20000000)
        self.assertEqual(base['resource_contract'], resources.RESOURCE_CONTRACT)
        self.assertIs(base['scientific_readiness'], False)
        observed = resources.add_diagnostics(base, catalog, rows, 20000000 - base['primitive_steps'])
        self.assertEqual(resources.base_projection(observed), base)
        self.assertTrue(observed['diagnostics']['processing_complete'])
        self.assertEqual(observed['diagnostics']['guard_counts']['unrecognized'], 0)
        self.assertLessEqual(base['primitive_steps'] + observed['diagnostics']['primitive_steps'], 20000000)

    def test_numeric_retention_and_base_binding_survive_diagnostic_stops(self):
        catalog, rows = FIXTURE['catalog'], history()
        base = resources.materialize(selected_request(), catalog, rows)
        for limit in (0, 1):
            with self.subTest(limit=limit):
                stopped = resources.add_diagnostics(base, catalog, rows, limit)
                self.assertFalse(stopped['diagnostics']['processing_complete'])
                self.assertEqual(resources.base_projection(stopped), base)
        with patch.object(resources, 'MAX_CASE_BYTES', 1):
            stopped = resources.add_diagnostics(base, catalog, rows, 100000)
        self.assertEqual(resources.base_projection(stopped), base)
        tampered = deepcopy(stopped); tampered['cases'][0]['scope'] = False
        with self.assertRaises(ExpressionGap): resources.base_projection(tampered)

    def test_full_observed_equality_and_remaining_budget_cannot_be_bypassed(self):
        catalog, rows = FIXTURE['catalog'], history()
        base = resources.materialize(selected_request(), catalog, rows)
        before = canonical(base)
        with self.assertRaises(ExpressionGap):
            resources.add_diagnostics(base, catalog, rows, 20000000 - base['primitive_steps'] + 1)
        with patch.object(resources, '_case', return_value={**base['cases'][0], 'scope': False}), self.assertRaises(ExpressionGap):
            resources.add_diagnostics(base, catalog, rows, 100000)
        self.assertEqual(canonical(base), before)


if __name__ == '__main__': unittest.main()
