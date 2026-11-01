"""Independent bounded-math/1.0 conformance expectations, fixed before implementation.

Authority: D089 and docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md.
Decimal.ln at 120 digits supplies a separately implemented numerical oracle; it
is a cross-check, not a proof of the production enclosure algorithm. Exact
median answers, ln(1), resource fences and legacy equality have exact oracles.
No provider, market dataset, or production module is mocked or modified here.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path
import unittest

from trading_researcher.bounded_math import BoundedReferenceEngine, log_enclosure
from trading_researcher.codec import digest
from trading_researcher.expressions import ExpressionGap, ReferenceEngine


CATALOG = {'x@1': {'type': 'real', 'unit': 'ratio'}}
MAX_BPS_WIDTH = Fraction(1, 10**12)


def ratio(value):
    value = Fraction(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def read_ratio(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': value}


def feature(ref='x@1'):
    return {'op': 'feature', 'ref': ref}


def program(expression, catalog=CATALOG, schema='research-ast/2'):
    return {'schema': schema, 'catalog_hash': digest(catalog), 'expression': expression}


def rows(values, instrument='A', ref='x@1'):
    return [{'time': i*900, 'instrument': instrument,
             'features': {ref: {'value': None if value is None else str(value), 'available_at': i*900}}}
            for i, value in enumerate(values)]


def median(bars, arg=None):
    return {'op': 'trailing_median', 'bars': bars, 'arg': feature() if arg is None else arg}


def logarithm(arg):
    return {'op': 'ln', 'arg': arg}


def oracle_log(value):
    value = Fraction(value)
    with localcontext() as context:
        context.prec = 120
        return Fraction((Decimal(value.numerator)/Decimal(value.denominator)).ln())


class BoundedMathTests(unittest.TestCase):
    def assert_code(self, code, callback):
        with self.assertRaises(ExpressionGap) as failure:
            callback()
        self.assertEqual(failure.exception.code, code)

    def public_bounds(self, output):
        self.assertEqual(set(output), {'type', 'unit', 'value', 'missing'})
        self.assertEqual(output['type'], 'real')
        self.assertEqual(output['unit'], 'ratio')
        self.assertIsNone(output['missing'])
        self.assertEqual(set(output['value']), {'schema', 'lower', 'upper'})
        self.assertEqual(output['value']['schema'], 'bounded-real/1')
        low, high = (read_ratio(output['value'][key]) for key in ('lower', 'upper'))
        self.assertLessEqual(low, high)
        return low, high

    def test_exact_odd_even_ties_negative_and_singleton_medians(self):
        cases = [(['7', '1', '4'], Fraction(4)),
                 (['1', '7', '4', '2'], Fraction(3)),
                 (['2', '2', '2', '9'], Fraction(2)),
                 (['-0.2', '-0.1', '4', '0'], Fraction(-1, 20)),
                 (['9.125'], Fraction(73, 8))]
        for values, expected in cases:
            with self.subTest(values=values):
                actual = BoundedReferenceEngine(CATALOG, rows(values)).evaluate(program(median(len(values))), len(values)-1)
                self.assertEqual(actual, {'type': 'real', 'unit': 'ratio', 'value': ratio(expected), 'missing': None})

    def test_declared_96_bar_window_excludes_signal_and_current_bar(self):
        source = rows([*range(96), 999999, -999999])
        expression = {'op': 'lag', 'bars': 2, 'arg': median(96)}
        actual = BoundedReferenceEngine(CATALOG, source).evaluate(program(expression), 97)
        self.assertEqual(actual['value'], ratio(Fraction(95, 2)))
        self.assertIsNone(actual['missing'])

    def test_median_retains_non_dimensionless_input_unit(self):
        catalog = {'p@1': {'type': 'real', 'unit': 'USDT/ETH'}}
        output = BoundedReferenceEngine(catalog, rows(['1.1', '2.2'], ref='p@1')).evaluate(
            program(median(2, feature('p@1')), catalog), 1)
        self.assertEqual(output, {'type': 'real', 'unit': 'USDT/ETH', 'value': ratio(Fraction(33, 20)), 'missing': None})

    def test_missing_null_and_absent_samples_never_shorten_median(self):
        absent = rows(['1', '2', '3', '4'])
        del absent[1]
        missing_feature = rows(['1', '2', '3'])
        missing_feature[1]['features'] = {}
        for source, index, count in [(rows(['1', None, '3']), 2, 3),
                                      (absent, 2, 3), (missing_feature, 2, 3),
                                      (rows(['1', '2']), 1, 3)]:
            with self.subTest(source=source):
                output = BoundedReferenceEngine(CATALOG, source).evaluate(program(median(count)), index)
                self.assertIsNone(output['value'])
                self.assertEqual(output['missing'], 'incomplete_window')

    def test_late_window_input_respects_original_decision_cutoff(self):
        source = rows(['1', '3', '2', '999'])
        source[1]['features']['x@1']['available_at'] = 2700
        engine = BoundedReferenceEngine(CATALOG, source)
        self.assertEqual(engine.evaluate(program(median(3)), 2)['missing'], 'incomplete_window')
        output = engine.evaluate(program({'op': 'lag', 'bars': 1, 'arg': median(3)}), 3)
        self.assertEqual(output['value'], ratio(2))

    def test_interleaved_instruments_never_share_window_values(self):
        source = sorted(rows(['1', '100', '2']) + rows(['9000', '9000', '9000'], instrument='B'),
                        key=lambda item: (item['time'], item['instrument']))
        engine = BoundedReferenceEngine(CATALOG, source)
        self.assertEqual(engine.evaluate(program(median(3)), 4)['value'], ratio(2))
        del source[2]  # B remains present at t=900; it cannot replace the absent A row.
        self.assertEqual(BoundedReferenceEngine(CATALOG, source).evaluate(program(median(3)), 3)['missing'],
                         'incomplete_window')

    def test_window_parameters_boolean_and_incompatible_units_are_rejected(self):
        engine = BoundedReferenceEngine(CATALOG, rows(['1']))
        bad = [median(0), median(-1), median(True), median('1'),
               median(1, {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}),
               median(1, {'op': 'add', 'left': feature(), 'right': literal('1', 'USDT/ETH')})]
        for expression in bad:
            with self.subTest(expression=expression), self.assertRaises(ExpressionGap):
                engine.evaluate(program(expression), 0)

    def test_median_description_retains_dependency_and_parameter_paths(self):
        expression = {'op': 'lag', 'bars': 2, 'arg': median(96)}
        description = BoundedReferenceEngine(CATALOG, rows(['1'])).describe(program(expression))
        self.assertEqual(description, {'type': 'real', 'unit': 'ratio', 'feature_refs': ['x@1'],
            'parameter_paths': ['/expression/bars', '/expression/arg/bars']})

    def test_log_one_is_exact_zero_inside_an_explicit_enclosure(self):
        bound = log_enclosure(Fraction(1), remaining=[10000])
        self.assertIsInstance(bound.lower, Fraction)
        self.assertIsInstance(bound.upper, Fraction)
        self.assertEqual((bound.lower, bound.upper), (Fraction(0), Fraction(0)))
        output = BoundedReferenceEngine(CATALOG, rows(['1']), allow_log=True).evaluate(
            program(logarithm(feature())), 0)
        self.assertEqual(self.public_bounds(output), (Fraction(0), Fraction(0)))

    def test_independent_decimal_log_containment_and_scaled_width(self):
        samples = [Fraction(1, 10**40), Fraction(1, 7), Fraction(1, 2),
                   Fraction(999999999999, 10**12), Fraction(1000000000001, 10**12),
                   Fraction(2), Fraction(7), Fraction(10**40)]
        for value in samples:
            with self.subTest(value=value):
                bound = log_enclosure(value, remaining=[100000])
                expected = oracle_log(value)
                self.assertIsInstance(bound.lower, Fraction)
                self.assertIsInstance(bound.upper, Fraction)
                self.assertLessEqual(bound.lower, expected)
                self.assertGreaterEqual(bound.upper, expected)
                self.assertGreaterEqual(bound.upper-bound.lower, 0)
                self.assertLessEqual(10000*(bound.upper-bound.lower), MAX_BPS_WIDTH)

    def test_log_reciprocal_symmetry_and_ordered_separated_ranges(self):
        for value in (Fraction(2), Fraction(7, 3), Fraction(100)):
            with self.subTest(value=value):
                direct = log_enclosure(value, remaining=[100000])
                reciprocal = log_enclosure(1/value, remaining=[100000])
                self.assertLessEqual(direct.lower + reciprocal.lower, 0)
                self.assertGreaterEqual(direct.upper + reciprocal.upper, 0)
        bounds = [log_enclosure(value, remaining=[100000]) for value in
                  (Fraction(1, 3), Fraction(1, 2), Fraction(1), Fraction(2), Fraction(3))]
        for left, right in zip(bounds, bounds[1:]):
            self.assertLess(left.upper, right.lower)

    def test_direct_nonpositive_log_is_numerical_gap(self):
        for value in (Fraction(0), Fraction(-1), Fraction(-1, 100)):
            with self.subTest(value=value):
                self.assert_code('NUMERICAL_GAP', lambda: log_enclosure(value, remaining=[100000]))

    def test_expression_log_domain_and_missing_inputs_remain_missing(self):
        for value in ('0', '-1', '-0.001'):
            with self.subTest(value=value):
                output = BoundedReferenceEngine(CATALOG, rows([value]), allow_log=True).evaluate(
                    program(logarithm(feature())), 0)
                self.assertEqual(output, {'type': 'real', 'unit': 'ratio', 'value': None, 'missing': 'log_domain'})
        missing = BoundedReferenceEngine(CATALOG, rows([None]), allow_log=True).evaluate(
            program(logarithm(feature())), 0)
        self.assertIsNone(missing['value'])
        self.assertIsNotNone(missing['missing'])
        late = rows(['2']); late[0]['features']['x@1']['available_at'] = 900
        output = BoundedReferenceEngine(CATALOG, late, allow_log=True).evaluate(program(logarithm(feature())), 0)
        self.assertIsNone(output['value'])
        self.assertEqual(output['missing'], 'not_yet_available')

    def test_log_is_outcome_only_and_requires_dimensionless_real(self):
        source = rows(['2'])
        with self.assertRaises(ExpressionGap):
            BoundedReferenceEngine(CATALOG, source).evaluate(program(logarithm(feature())), 0)
        engine = BoundedReferenceEngine(CATALOG, source, allow_log=True)
        for arg in (literal('2', 'USDT/ETH'),
                    {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}):
            with self.subTest(arg=arg), self.assertRaises(ExpressionGap):
                engine.evaluate(program(logarithm(arg)), 0)

    def test_scaled_log_outcome_public_bounds_and_exact_input_immutability(self):
        source = rows(['1.003']); catalog = deepcopy(CATALOG)
        expression = {'op': 'mul', 'left': literal('10000'), 'right': logarithm(feature())}
        request = program(expression, catalog)
        original = deepcopy((source, catalog, request))
        output = BoundedReferenceEngine(catalog, source, allow_log=True).evaluate(request, 0)
        lower, upper = self.public_bounds(output)
        expected = 10000*oracle_log(Fraction(1003, 1000))
        self.assertLessEqual(lower, expected)
        self.assertGreaterEqual(upper, expected)
        self.assertLessEqual(upper-lower, MAX_BPS_WIDTH)
        self.assertEqual((source, catalog, request), original)

    def test_exact_arithmetic_propagates_log_enclosures(self):
        source = rows(['2']); engine = BoundedReferenceEngine(CATALOG, source, allow_log=True)
        ln_two = logarithm(feature())
        expressions = [({'op': 'add', 'left': ln_two, 'right': literal('3')}, oracle_log(2)+3),
                       ({'op': 'sub', 'left': literal('3'), 'right': ln_two}, 3-oracle_log(2)),
                       ({'op': 'mul', 'left': ln_two, 'right': literal('-2')}, -2*oracle_log(2)),
                       ({'op': 'div', 'left': ln_two, 'right': literal('2')}, oracle_log(2)/2)]
        for expression, expected in expressions:
            with self.subTest(op=expression['op']):
                lower, upper = self.public_bounds(engine.evaluate(program(expression), 0))
                self.assertLessEqual(lower, expected)
                self.assertGreaterEqual(upper, expected)

    def test_intervals_do_not_silently_supply_comparisons_or_median(self):
        engine = BoundedReferenceEngine(CATALOG, rows(['2', '3']), allow_log=True)
        for operator in ('lt', 'le', 'gt', 'ge', 'eq'):
            expression = {'op': operator, 'left': logarithm(feature()), 'right': literal('1')}
            with self.subTest(operator=operator), self.assertRaises(ExpressionGap):
                engine.evaluate(program(expression), 1)
        with self.assertRaises(ExpressionGap):
            engine.evaluate(program(median(2, logarithm(feature()))), 1)

    def test_old_version_rejects_each_new_operator_even_on_opted_in_engine(self):
        source = rows(['2'])
        for engine in (ReferenceEngine(CATALOG, source), BoundedReferenceEngine(CATALOG, source, allow_log=True)):
            for expression in (median(1), logarithm(feature())):
                with self.subTest(engine=type(engine).__name__, expression=expression):
                    self.assert_code('LANGUAGE_GAP', lambda: engine.evaluate(program(expression, schema='research-ast/1'), 0))
        self.assert_code('LANGUAGE_GAP', lambda: ReferenceEngine(CATALOG, source).evaluate(program(median(1)), 0))

    def test_ordinary_new_version_scalar_results_stay_exact(self):
        engine = BoundedReferenceEngine(CATALOG, rows(['1.1', '2.2']))
        output = engine.evaluate(program({'op': 'trailing_mean', 'arg': feature(), 'bars': 2}), 1)
        self.assertEqual(output, {'type': 'real', 'unit': 'ratio', 'value': ratio(Fraction(33, 20)), 'missing': None})

    def test_bound_and_expression_resource_budgets(self):
        self.assert_code('RESOURCE_GAP', lambda: log_enclosure(Fraction(2), remaining=[0]))
        engine = BoundedReferenceEngine(CATALOG, rows(['2']), allow_log=True)
        self.assert_code('RESOURCE_GAP', lambda: engine.evaluate(program(median(1000001)), 0))
        expression = median(1)
        for _ in range(32):
            expression = {'op': 'lag', 'bars': 0, 'arg': expression}
        self.assert_code('RESOURCE_GAP', lambda: engine.evaluate(program(expression), 0))
        node = engine._program_node(program(median(1)))
        self.assert_code('RESOURCE_GAP', lambda: engine._calculate(node, 0, 'A', 0, [0]))

    def test_catalog_version_cannot_be_substituted(self):
        request = program(median(1)); request['catalog_hash'] = 'not-the-bound-catalog'
        self.assert_code('FEATURE_GAP', lambda: BoundedReferenceEngine(CATALOG, rows(['1'])).evaluate(request, 0))

    def test_legacy_fixed_expectations_are_preserved_by_optional_engine(self):
        fixture = json.loads((Path(__file__).parent/'fixtures/reference_expression_cases.json').read_text(encoding='utf-8'))
        for case in fixture['cases']:
            with self.subTest(case=case['name']):
                request = program(case['expression'], case['catalog'], schema='research-ast/1')
                if 'error_code' in case:
                    self.assert_code(case['error_code'], lambda: BoundedReferenceEngine(case['catalog'], case['rows']).evaluate(request, case['index']))
                else:
                    output = BoundedReferenceEngine(case['catalog'], case['rows']).evaluate(request, case['index'])
                    self.assertEqual(output, case['expected'])


if __name__ == '__main__':
    unittest.main()
