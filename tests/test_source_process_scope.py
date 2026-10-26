"""A source time identity is distinct from an estimator-only stress law."""
from copy import deepcopy
import unittest

from trading_researcher.codec import digest
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.outcomes import materialize_reference, _rational
from trading_researcher.population_models import build_model, generate_world, specification
from trading_researcher.source_process_scope import diagnose_source_process


def source_fixture():
    catalog = {name+'@1': {'type': 'real', 'unit': 'USD'} for name in ('open', 'close')}
    def program(node):
        return {'schema': 'research-ast/1', 'catalog_hash': digest(catalog), 'expression': node}
    outcome = {'op': 'gt', 'left': {'op': 'feature', 'ref': 'close@1'},
               'right': {'op': 'feature', 'ref': 'open@1'}}
    condition = {'op': 'gt', 'left': {'op': 'lag', 'bars': 1, 'arg': outcome['left']},
                 'right': {'op': 'lag', 'bars': 1, 'arg': outcome['right']}}
    request = {'schema': 'reference-case-request/1', 'candidate_ref': 'scope-fixture',
        'data_snapshot_ref': 'scope-fixture',
        'scope_program': program({'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}),
        'condition_program': program(condition), 'outcome_program': program(outcome),
        'outcome_scale': 'binary_probability', 'horizon_bars': 1,
        'universe': {'start': '1970-01-01T00:15:00Z', 'end': '1970-01-01T02:00:00Z',
                     'instruments': ['A']}, 'as_of': '1970-01-01T02:00:00Z', 'max_steps': 10000}
    values = [0, 1, 0, 1, 1, 0, 0, 1]
    rows = [{'time': t*900, 'instrument': 'A', 'features': {
        'open@1': {'value': '10', 'available_at': t*900},
        'close@1': {'value': str(9+2*value), 'available_at': t*900}}}
        for t, value in enumerate(values)]
    return materialize_reference(request, catalog, rows)


class SourceProcessScopeTests(unittest.TestCase):
    def test_actual_reference_execution_has_separate_observed_and_eligible_support(self):
        source = source_fixture(); before = deepcopy(source)
        result = diagnose_source_process(source)
        self.assertEqual(result['status'], 'SHIFTED_VALUE_IDENTITY')
        self.assertEqual(result['identity']['condition_equals_outcome_at_offset_bars'], -2)
        self.assertEqual(result['observations'], {'target_rows': 7, 'partner_absent': 2,
            'both_unobserved': 0, 'condition_unobserved': 0, 'outcome_unobserved': 0,
            'compared': 5, 'equal': 5, 'unequal': 0, 'both_eligible_compared': 4})
        self.assertEqual(result['source_request_hash'], digest(source['request']))
        self.assertEqual(source, before)
        self.assertEqual(result['original_process_adequacy'], 'NOT_ASSESSED')
        self.assertFalse(result['scientific_readiness'])
        self.assertFalse(result['classification_permitted'])

    def test_model_retains_diagnostic_without_changing_declared_probabilities(self):
        source = source_fixture()
        model = build_model(source, diagnose(source, [1, 2]),
                            specification(1, 0, 0, 'Fixed estimator-only null stress'), [_rational(0)])
        self.assertEqual(model['status'], 'MODEL_SPECIFIED')
        self.assertEqual(model['source_process_scope'], diagnose_source_process(source))
        self.assertEqual(model['source_identity_preservation'], 'NOT_GUARANTEED')
        self.assertEqual(model['scenarios'][0]['p_true'], model['population']['q'])
        self.assertEqual(model['scenarios'][0]['p_other'], model['population']['q'])
        self.assertIsNone(model['n_min'])

    def test_fixed_stress_counterexample_is_not_source_process_execution(self):
        source = source_fixture()
        model = build_model(source, diagnose(source, [1, 2]),
                            specification(1, 0, 0, 'Fixed independent null stress'), [_rational(0)])
        world = generate_world(source, model, 0, 96, 20261026)
        cases = world['report']['cases']
        pairs = [(row, cases[i-2]) for i, row in enumerate(cases) if i >= 2
                 and type(row['condition']) is bool and cases[i-2]['outcome'] is not None]
        self.assertTrue(any(_rational(int(row['condition'])) != partner['outcome']
                            for row, partner in pairs))
        self.assertFalse(world['report']['simulation']['raw_AST_executed'])
        self.assertEqual(diagnose_source_process(world['report'])['status'], 'NOT_ASSESSED')
        self.assertFalse(world['classification_permitted'])


if __name__ == '__main__':
    unittest.main()
