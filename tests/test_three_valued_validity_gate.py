"""One offline expressibility probe, not a registered or approved research candidate.

The synthetic Boolean/AST expectations test existing semantics only. They do
not alter any original idea, supply model formalization, establish its meaning
review, inspect market data, or demonstrate scientific readiness.
"""
from copy import deepcopy
from functools import reduce
import unittest

from trading_researcher.bounded_math import BoundedReferenceEngine
from trading_researcher.codec import digest
from trading_researcher.expressions import ExpressionGap, ReferenceEngine


CATALOG = {name + '@1': {'type': 'real', 'unit': 'price' if name in ('O', 'H', 'C') else 'volume'}
           for name in ('O', 'H', 'C', 'Q', 'B')}
DECISION_INDEX = 97
DECISION = DECISION_INDEX * 900


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': value}


def unknown():
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': None}


def feature(name):
    return {'op': 'feature', 'ref': name + '@1'}


def shifted(name, bars=1):
    return {'op': 'lag', 'bars': bars, 'arg': feature(name)}


def conjunction(nodes):
    return reduce(lambda left, right: binary('and', left, right), nodes)


def validity_gate(validity, predicate):
    return binary('or', binary('and', deepcopy(validity), predicate),
                  binary('and', {'op': 'not', 'arg': deepcopy(validity)}, unknown()))


def engineering_condition():
    """Synthetic expression probe of the fixed original thresholds and checks."""
    o, h, c, q, b = [shifted(name) for name in ('O', 'H', 'C', 'Q', 'B')]
    median = {'op': 'lag', 'bars': 2,
              'arg': {'op': 'trailing_median', 'bars': 96, 'arg': feature('Q')}}
    validity = conjunction([
        binary('gt', deepcopy(o), literal('0', 'price')),
        binary('gt', deepcopy(q), literal('0', 'volume')),
        binary('gt', deepcopy(median), literal('0', 'volume')),
        binary('ge', deepcopy(b), literal('0', 'volume')),
        binary('le', deepcopy(b), deepcopy(q)),
        binary('eq', deepcopy(h), deepcopy(h)),
        binary('eq', deepcopy(c), deepcopy(c)),
    ])
    def body(price):
        return binary('sub', binary('div', deepcopy(price), deepcopy(o)), literal('1'))
    predicate = conjunction([
        binary('ge', binary('div', deepcopy(b), deepcopy(q)), literal('0.65')),
        binary('ge', deepcopy(q), binary('mul', literal('2'), deepcopy(median))),
        binary('ge', body(h), literal('0.003')),
        binary('ge', body(c), literal('0')),
        binary('le', body(c), literal('0.0005')),
    ])
    return validity_gate(validity, predicate)


def program(expression, catalog=CATALOG, version='research-ast/2'):
    return {'schema': version, 'catalog_hash': digest(catalog), 'expression': expression}


def shape(expression):
    children = [shape(expression[name]) for name in ('arg', 'left', 'right') if name in expression]
    return 1 + sum(size for size, _ in children), 1 + max((depth for _, depth in children), default=0)


def synthetic_rows():
    rows = [{'time': index * 900, 'instrument': 'synthetic-ETH', 'features': {
                name + '@1': {'value': value, 'available_at': (index + 1) * 900}
                for name, value in [('O', '100'), ('H', '100.3'), ('C', '100.05'), ('Q', '50'), ('B', '40')]}}
            for index in range(103)]
    rows[96]['features']['Q@1']['value'] = '100'
    rows[96]['features']['B@1']['value'] = '65'
    return rows


def evaluate_condition(rows, when=DECISION):
    engine = BoundedReferenceEngine(CATALOG, rows)
    return engine.evaluate(program(engineering_condition()), engine.rows.index((when, 'synthetic-ETH')))


class ThreeValuedValidityGateTests(unittest.TestCase):
    def test_all_nine_existing_boolean_truth_table_cases(self):
        catalog = {name + '@1': {'type': 'boolean', 'unit': None} for name in ('V', 'P')}
        expression = validity_gate(feature('V'), feature('P'))
        for validity in (True, False, None):
            for predicate in (True, False, None):
                with self.subTest(validity=validity, predicate=predicate):
                    rows = [{'time': 0, 'instrument': 'synthetic', 'features': {
                        'V@1': {'value': validity, 'available_at': 0},
                        'P@1': {'value': predicate, 'available_at': 0}}}]
                    actual = ReferenceEngine(catalog, rows).evaluate(program(expression, catalog, 'research-ast/1'), 0)
                    expected = predicate if validity is True else None
                    self.assertIs(actual['value'], expected)
                    self.assertEqual(actual['missing'] is not None, expected is None)

    def test_complete_fixed_threshold_tree_fits_existing_node_and_depth_limits(self):
        expression = engineering_condition()
        self.assertEqual(shape(expression), (127, 12))
        engine = BoundedReferenceEngine(CATALOG, synthetic_rows())
        described = engine.describe(program(expression))
        self.assertEqual(described['type'], 'boolean')
        self.assertEqual(described['feature_refs'], sorted(CATALOG))
        self.assertIs(evaluate_condition(synthetic_rows())['value'], True)

    def test_every_threshold_retains_its_original_inclusive_boundary(self):
        cases = [('B', '64.999', False), ('Q', '99.999', False),
                 ('H', '100.299', False), ('C', '99.999', False),
                 ('C', '100.0501', False), ('C', '100', True),
                 ('C', '100.05', True), ('H', '100.3', True), ('B', '65', True)]
        for field, value, expected in cases:
            with self.subTest(field=field, value=value):
                rows = synthetic_rows()
                rows[96]['features'][field + '@1']['value'] = value
                actual = evaluate_condition(rows)
                self.assertIs(actual['value'], expected)
                self.assertIsNone(actual['missing'])

    def test_invalid_values_force_unknown_even_when_a_partial_condition_is_false(self):
        for field, value in [('O', '0'), ('O', '-1'), ('Q', '0'), ('Q', '-1'),
                             ('B', '-1'), ('B', '101'), ('H', None), ('C', None)]:
            with self.subTest(field=field, value=value):
                rows = synthetic_rows()
                rows[96]['features']['C@1']['value'] = '99'
                rows[96]['features'][field + '@1']['value'] = value
                actual = evaluate_condition(rows)
                self.assertIsNone(actual['value'])
                self.assertIsNotNone(actual['missing'])
        rows = synthetic_rows()
        for row in rows[:96]:
            row['features']['Q@1']['value'] = '0'
        self.assertIsNone(evaluate_condition(rows)['value'])

    def test_every_required_signal_or_baseline_input_is_complete_and_causal(self):
        for field in CATALOG:
            for mode in ('null', 'absent', 'late'):
                with self.subTest(field=field, mode=mode):
                    rows = synthetic_rows()
                    rows[96]['features']['B@1']['value'] = '1'
                    if mode == 'absent':
                        rows[96]['features'].pop(field)
                    elif mode == 'late':
                        rows[96]['features'][field]['available_at'] = DECISION + 1
                    else:
                        rows[96]['features'][field]['value'] = None
                    self.assertIsNone(evaluate_condition(rows)['value'])
        for index in range(96):
            with self.subTest(missing_baseline=index):
                rows = synthetic_rows()
                rows[96]['features']['B@1']['value'] = '1'
                rows[index]['features']['Q@1']['value'] = None
                self.assertIsNone(evaluate_condition(rows)['value'])
        rows = synthetic_rows()
        rows[50]['features']['Q@1']['available_at'] = DECISION + 1
        self.assertIsNone(evaluate_condition(rows)['value'])
        rows = synthetic_rows()
        rows.pop(20)
        self.assertIsNone(evaluate_condition(rows)['value'])
        self.assertIsNone(evaluate_condition(synthetic_rows(), 96 * 900)['value'])

    def test_no_extra_positive_high_close_or_individual_baseline_screen_is_added(self):
        for field in ('H', 'C'):
            with self.subTest(field=field):
                rows = synthetic_rows()
                rows[96]['features'][field + '@1']['value'] = '-1'
                self.assertIs(evaluate_condition(rows)['value'], False)
        rows = synthetic_rows()
        rows[0]['features']['Q@1']['value'] = '-100'
        self.assertIs(evaluate_condition(rows)['value'], True)
        for field in CATALOG:
            rows[97]['features'][field]['value'] = '999999'
        self.assertIs(evaluate_condition(rows)['value'], True)

    def test_nonfinite_inputs_are_admission_gaps_not_per_row_unknown_results(self):
        for value in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(value=value):
                rows = synthetic_rows()
                rows[96]['features']['O@1']['value'] = value
                with self.assertRaises(ExpressionGap) as error:
                    evaluate_condition(rows)
                self.assertEqual(error.exception.code, 'DATA_GAP')

    def test_declared_five_bar_anchor_preserves_original_positive_price_keys(self):
        # Only the time-key representability is tested; this is not a complete
        # outcome formalization or proof of invalid-price handling.
        expression = binary('mul', literal('10000', 'basis_points'),
                            {'op': 'ln', 'arg': binary('div', shifted('C', 1), shifted('O', 4))})
        self.assertEqual(shape(expression), (8, 5))
        rows = synthetic_rows()
        rows[98]['features']['O@1']['value'] = '200'   # t+900
        rows[101]['features']['C@1']['value'] = '200'  # t+3600
        engine = BoundedReferenceEngine(CATALOG, rows, allow_log=True)
        result = engine.evaluate(program(expression), DECISION_INDEX + 5)
        self.assertEqual(result['value'], {
            'schema': 'bounded-real/1',
            'lower': {'numerator': '0', 'denominator': '1'},
            'upper': {'numerator': '0', 'denominator': '1'}})
        self.assertIsNone(result['missing'])


if __name__ == '__main__':
    unittest.main()
