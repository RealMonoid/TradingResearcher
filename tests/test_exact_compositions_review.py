"""Independent expectations for the approved exact-compositions core.

Expectations come from the approved November 1 operator meanings, ordinary
Fraction arithmetic, Kleene truth tables, and an independent Decimal oracle.
All inputs are synthetic and self-contained. No private runtime artifacts,
registry, provider, research candidate, or market data are used. This suite
does not qualify the complete retained idea, a native route, or research use.
"""
from decimal import Decimal, localcontext
from fractions import Fraction
from itertools import product
import random
import unittest

from trading_researcher.bounded_math import BoundedReferenceEngine
from trading_researcher.codec import digest
from trading_researcher.exact_compositions import ExactCompositionEngine
from trading_researcher.expressions import ExpressionGap, ReferenceEngine
from trading_researcher.required_inputs import RequiredInputEngine


CATALOG = {
    'x@1': {'type': 'real', 'unit': 'ratio'},
    'price@1': {'type': 'real', 'unit': 'price:SYNTHETIC'},
    'flag@1': {'type': 'boolean', 'unit': None},
}


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit,
            'value': None if value is None else str(value)}


def boolean(value):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def feature(ref='x@1'):
    return {'op': 'feature', 'ref': ref}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def power(arg, exponent):
    return {'op': 'integer_power', 'arg': arg, 'exponent': exponent}


def window(op, arg, bars):
    return {'op': op, 'arg': arg, 'bars': bars}


def absolute(arg):
    return {'op': 'abs', 'arg': arg}


def logarithm(arg):
    return {'op': 'ln', 'arg': arg}


def program(expression, schema='research-ast/4'):
    return {'schema': schema, 'catalog_hash': digest(CATALOG), 'expression': expression}


def rows(values, ref='x@1', late=None):
    return [{'time': index * 900, 'instrument': 'SYNTHETIC',
             'features': {ref: {'value': value,
                                'available_at': (late[index] if late is not None else index * 900)}}}
            for index, value in enumerate(values)]


def rational(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def bounds(value):
    return rational(value['lower']), rational(value['upper'])


def balanced_sum(count):
    if count == 1:
        return literal(1)
    left = count // 2
    return binary('add', balanced_sum(left), balanced_sum(count - left))


class ExactCompositionReview(unittest.TestCase):
    def engine(self, data=None, *, outcome=False):
        return ExactCompositionEngine(CATALOG, rows(['2']) if data is None else data,
                                      allow_log=outcome)

    def value(self, expression, *, outcome=False, data=None, index=None, schema='research-ast/4'):
        engine = self.engine(data, outcome=outcome)
        return engine.evaluate(program(expression, schema), len(engine.rows) - 1 if index is None else index)

    def raw(self, engine, expression, *, when=None, cutoff=None, budget=1_000_000, trace=None):
        node = engine._program_node(program(expression))
        when = engine.rows[-1][0] if when is None else when
        remaining = [budget]
        result = engine._calculate(node, when, 'SYNTHETIC', when if cutoff is None else cutoff,
                                   remaining, trace)
        return result, remaining[0]

    def test_exact_power_fixed_and_independent_random_rational_oracle(self):
        rng = random.Random(0xD097)
        cases = [('0', 1), ('0', 17), ('-2', 3), ('-2', 4), ('0.5', 7), ('1', 1_000_000)]
        cases += [(str(Decimal(rng.randint(-25, 25)) / Decimal(10)), rng.randint(1, 21))
                  for _ in range(80)]
        for base, exponent in cases:
            with self.subTest(base=base, exponent=exponent):
                got = self.value(power(literal(base), exponent))
                self.assertIsNone(got['missing'])
                self.assertEqual(rational(got['value']), Fraction(base) ** exponent)

    def test_power_parameter_and_operand_rejections(self):
        for exponent in (0, -1, True, False, '2', None, 1_000_001):
            with self.subTest(exponent=exponent), self.assertRaises(ExpressionGap):
                self.value(power(literal(2), exponent))
        for arg in (boolean(True), literal(2, 'price:SYNTHETIC'), logarithm(literal(2))):
            with self.subTest(arg=arg), self.assertRaises(ExpressionGap):
                self.value(power(arg, 2), outcome=True)
        self.assertIsNone(self.value(power(literal(None), 2))['value'])

    def test_power_exact_step_boundaries_and_recovery(self):
        # A literal costs one; the power root costs one. Each binary bit and
        # each multiplication attempt adds one, including factor squaring.
        engine = self.engine()
        for exponent, steps in ((1, 4), (2, 6), (3, 7), (64, 16), (1_000_000, 48)):
            expression = power(literal(1), exponent)
            with self.subTest(exponent=exponent):
                with self.assertRaises(ExpressionGap) as caught:
                    self.raw(engine, expression, budget=steps - 1)
                self.assertEqual(caught.exception.code, 'RESOURCE_GAP')
                result, remaining = self.raw(engine, expression, budget=steps)
                self.assertEqual(result.value, Fraction(1))
                self.assertEqual(remaining, 0)

    def test_power_numeric_envelope_boundary_for_numerator_and_denominator(self):
        for base in ('2', '0.5'):
            with self.subTest(base=base):
                self.assertEqual(rational(self.value(power(literal(base), 8191))['value']),
                                 Fraction(base) ** 8191)
                with self.assertRaises(ExpressionGap) as caught:
                    self.value(power(literal(base), 8192))
                self.assertEqual(caught.exception.code, 'RESOURCE_GAP')

    def test_product_fixed_and_random_fraction_oracle(self):
        rng = random.Random(741)
        cases = [['-2', '0.5', '-3'], ['-2', '0', '3'], ['0'], ['-1']]
        cases += [[str(Decimal(rng.randint(-40, 40)) / Decimal(10))
                   for _ in range(rng.randint(1, 15))] for _ in range(60)]
        for values in cases:
            with self.subTest(values=values):
                expected = Fraction(1)
                for value in values:
                    expected *= Fraction(value)
                got = self.value(window('trailing_product', feature(), len(values)), data=rows(values))
                self.assertEqual(rational(got['value']), expected)

    def test_all_full_kleene_truth_table_and_no_implicit_unknown_override(self):
        for values in product((True, False, None), repeat=3):
            expected = False if False in values else None if None in values else True
            with self.subTest(values=values):
                got = self.value(window('trailing_all', feature('flag@1'), 3),
                                 data=rows(values, ref='flag@1'))
                self.assertIs(got['value'], expected)
                if expected is None:
                    self.assertEqual(got['missing'], 'unknown_boolean')
                else:
                    self.assertIsNone(got['missing'])

    def test_windows_trace_every_dependency_in_oldest_first_order(self):
        for op, values, ref in (
            ('trailing_product', [None, '0', '3'], 'x@1'),
            ('trailing_all', [False, None, True], 'flag@1'),
        ):
            with self.subTest(op=op):
                seen = []
                got, _ = self.raw(self.engine(rows(values, ref=ref)), window(op, feature(ref), 3),
                                  trace=lambda *event: seen.append(event))
                self.assertEqual([t for t, _, reason in seen if reason == 'observation'], [0, 900, 1800])
                self.assertIn((900 if op == 'trailing_all' else 0, 'missing_value'),
                              [(t, reason) for t, _, reason in seen])
                self.assertIs(got.value, False if op == 'trailing_all' else None)

    def test_late_false_window_stays_false_until_explicit_outer_guard(self):
        engine = self.engine(rows([False, True], ref='flag@1', late=[0, 1800]))
        validity = window('trailing_all', feature('flag@1'), 2)
        seen = []
        folded, _ = self.raw(engine, validity, trace=lambda *event: seen.append(event))
        self.assertIs(folded.value, False)
        self.assertIn((900, 1800, 'not_yet_available'), seen)
        # G(V,P) supplies the original whole-condition unknown rule. The
        # window primitive itself must keep the ordinary Kleene result.
        guarded = binary('or', binary('and', validity, boolean(False)),
                         binary('and', {'op': 'not', 'arg': validity}, boolean(None)))
        result, _ = self.raw(engine, guarded)
        self.assertIsNone(result.value)
        self.assertEqual(result.missing, 'unknown_boolean')

    def test_window_step_charges_include_offsets_and_known_multiplications(self):
        for op, values, ref, steps in (
            ('trailing_product', ['2', '3'], 'x@1', 7),
            ('trailing_product', [None, '2', '3'], 'x@1', 9),
            ('trailing_all', [False, None, True], 'flag@1', 7),
        ):
            with self.subTest(op=op, values=values):
                engine = self.engine(rows(values, ref=ref))
                expression = window(op, feature(ref), len(values))
                with self.assertRaises(ExpressionGap) as caught:
                    self.raw(engine, expression, budget=steps - 1)
                self.assertEqual(caught.exception.code, 'RESOURCE_GAP')
                _, remaining = self.raw(engine, expression, budget=steps)
                self.assertEqual(remaining, 0)

    def test_no_early_zero_unknown_or_false_hides_later_resource_failure(self):
        cases = [
            ('trailing_product', ['0', '2'], power(feature(), 8192)),
            ('trailing_product', [None, '2', '2'], power(feature(), 4096)),
            ('trailing_all', ['0', '2'], binary('gt', power(feature(), 8192), literal(0))),
        ]
        for op, values, arg in cases:
            with self.subTest(op=op, values=values), self.assertRaises(ExpressionGap) as caught:
                self.value(window(op, arg, len(values)), data=rows(values))
            self.assertEqual(caught.exception.code, 'RESOURCE_GAP')

    def test_product_cannot_reorder_away_an_overlarge_intermediate(self):
        expression = window('trailing_product', power(feature(), 4096), 4)
        with self.assertRaises(ExpressionGap) as caught:
            self.value(expression, data=rows(['2', '2', '0.5', '0.5']))
        self.assertEqual(caught.exception.code, 'RESOURCE_GAP')
        # Same factors, explicitly different time order: each prescribed
        # intermediate is small enough. This is not permission to reorder.
        self.assertEqual(rational(self.value(expression, data=rows(['2', '0.5', '2', '0.5']))['value']), 1)

    def test_window_parameters_types_units_and_bounded_operand_rejections(self):
        for op in ('trailing_product', 'trailing_all'):
            arg = feature() if op == 'trailing_product' else feature('flag@1')
            for bars in (0, -1, True, '2', None, 1_000_001):
                with self.subTest(op=op, bars=bars), self.assertRaises(ExpressionGap):
                    self.value(window(op, arg, bars))
            self.engine().describe(program(window(op, arg, 1_000_000)))
        for expression in (
            window('trailing_product', feature('price@1'), 1),
            window('trailing_product', boolean(True), 1),
            window('trailing_product', logarithm(literal(2)), 1),
            window('trailing_all', literal(1), 1),
        ):
            with self.subTest(expression=expression), self.assertRaises(ExpressionGap):
                self.value(expression, outcome=True)

    def test_causal_exact_slots_and_no_cross_instrument_substitution(self):
        data = [
            {'time': t, 'instrument': instrument,
             'features': {'x@1': {'value': value, 'available_at': t}}}
            for t, instrument, value in ((0, 'A', '2'), (0, 'B', '19'),
                                         (900, 'A', '3'), (900, 'B', '23'),
                                         (1800, 'A', '5'), (1800, 'B', '29'))
        ]
        engine = self.engine(data)
        self.assertEqual(rational(engine.evaluate(program(window('trailing_product', feature(), 2)), 4)['value']), 15)
        missing = [row for row in data if not (row['time'] == 900 and row['instrument'] == 'A')]
        self.assertIsNone(self.value(window('trailing_product', feature(), 2), data=missing, index=3)['value'])
        for availability, expected in ((1800, Fraction(30)), (1801, None)):
            got = self.value(window('trailing_product', feature(), 3),
                             data=rows(['2', '3', '5'], late=[availability, 900, 1800]))
            self.assertEqual(None if got['value'] is None else rational(got['value']), expected)

    def test_only_required_features_need_rows_not_window_or_lag_containers(self):
        engine = self.engine(rows(['2', '3']))
        expression = window('trailing_product', window('lag', feature(), 1), 2)
        got, _ = self.raw(engine, expression, when=1800)
        self.assertEqual(got.value, Fraction(6))
        self.assertIsNone(self.value(window('trailing_product', feature(), 3), data=rows(['2', '3']))['value'])
        flag_engine = self.engine(rows([True, True], ref='flag@1'))
        got, _ = self.raw(flag_engine, window('trailing_all', window('lag', feature('flag@1'), 1), 2), when=1800)
        self.assertIs(got.value, True)

    def test_abs_preserves_rational_units_and_missingness_and_is_outcome_only(self):
        for text in ('-3.25', '0', '7'):
            got = self.value(absolute(literal(text, 'price:SYNTHETIC')), outcome=True)
            self.assertEqual(rational(got['value']), abs(Fraction(text)))
            self.assertEqual(got['unit'], 'price:SYNTHETIC')
        self.assertIsNone(self.value(absolute(literal(None)), outcome=True)['value'])
        for expression, outcome in ((absolute(literal(-1)), False), (absolute(boolean(True)), True)):
            with self.subTest(expression=expression), self.assertRaises(ExpressionGap):
                self.value(expression, outcome=outcome)

    def test_abs_enclosure_nonnegative_nonpositive_crossing_and_zero(self):
        old = BoundedReferenceEngine(CATALOG, rows(['2']), allow_log=True)
        ln2 = logarithm(literal(2))
        crossing = binary('sub', ln2, ln2)
        for child in (ln2, logarithm(literal('0.5')), crossing, logarithm(literal(1))):
            before = bounds(old.evaluate(program(child, 'research-ast/2'), 0)['value'])
            got = bounds(self.value(absolute(child), outcome=True)['value'])
            expected = (Fraction(0) if before[0] <= 0 <= before[1] else min(map(abs, before)),
                        max(map(abs, before)))
            self.assertEqual(got, expected)
        self.assertGreater(bounds(self.value(absolute(crossing), outcome=True)['value'])[1], 0)

    def test_absolute_log_contains_independent_decimal_reference_in_basis_points(self):
        for text in ('0.001', '0.5', '0.99999999', '1', '1.00000001', '2', '1000'):
            expression = binary('mul', literal(10000, 'basis_points'), absolute(logarithm(literal(text))))
            with self.subTest(text=text):
                got = self.value(expression, outcome=True)
                lo, hi = bounds(got['value'])
                with localcontext() as context:
                    context.prec = 100
                    reference = Fraction(abs(Decimal(text).ln()) * Decimal(10000))
                self.assertLessEqual(lo, reference + Fraction(1, 10**80))
                self.assertGreaterEqual(hi, reference - Fraction(1, 10**80))
                self.assertLessEqual(hi - lo, Fraction(1, 10**12))
                self.assertEqual(got['unit'], 'basis_points')
        for text in ('0', '-1'):
            self.assertIsNone(self.value(absolute(logarithm(literal(text))), outcome=True)['value'])

    def test_log_restrictions_survive_abs_and_nested_new_operators(self):
        forbidden = [
            (absolute(logarithm(literal(2))), False),
            (binary('gt', absolute(logarithm(literal(2))), literal(0)), True),
            (window('trailing_mean', absolute(logarithm(literal(2))), 2), True),
            (window('trailing_median', absolute(logarithm(literal(2))), 2), True),
            (logarithm(absolute(logarithm(literal(2)))), True),
        ]
        for expression, outcome in forbidden:
            with self.subTest(expression=expression), self.assertRaises(ExpressionGap):
                self.value(expression, outcome=outcome)

    def test_node_and_depth_ceilings_count_new_nodes_and_both_branches(self):
        self.assertEqual(rational(self.value(absolute(balanced_sum(128)), outcome=True)['value']), 128)
        with self.assertRaises(ExpressionGap) as caught:
            self.value(absolute(balanced_sum(129)), outcome=True)
        self.assertEqual(caught.exception.code, 'RESOURCE_GAP')
        expression = literal(-2)
        for _ in range(31):
            expression = absolute(expression)
        self.assertEqual(rational(self.value(expression, outcome=True)['value']), 2)
        with self.assertRaises(ExpressionGap) as caught:
            self.value(absolute(expression), outcome=True)
        self.assertEqual(caught.exception.code, 'RESOURCE_GAP')
        oversized_false_branch = binary('and', boolean(False), window('trailing_all', boolean(True), 1_000_001))
        with self.assertRaises(ExpressionGap):
            self.value(oversized_false_branch)

    def test_describe_exposes_all_new_parameter_origins_without_changing_inputs(self):
        expression = window('lag', window('trailing_product', power(feature(), 3), 2), 1)
        before = digest(expression)
        description = self.engine().describe(program(expression))
        self.assertEqual(description['type'], 'real')
        self.assertEqual(description['unit'], 'ratio')
        self.assertEqual(description['feature_refs'], ['x@1'])
        self.assertEqual(set(description['parameter_paths']), {
            '/expression/bars', '/expression/arg/bars', '/expression/arg/arg/exponent'})
        self.assertEqual(digest(expression), before)

    def test_new_operators_need_ast4_and_legacy_engines_reject_them(self):
        expressions = [power(literal(2), 2), window('trailing_product', literal(2), 1),
                       window('trailing_all', boolean(True), 1), absolute(literal(-2))]
        for expression in expressions:
            for schema in ('research-ast/1', 'research-ast/2', 'research-ast/3'):
                with self.subTest(expression=expression, schema=schema), self.assertRaises(ExpressionGap):
                    self.value(expression, schema=schema, outcome=True)
            for engine_type in (ReferenceEngine, BoundedReferenceEngine, RequiredInputEngine):
                engine = engine_type(CATALOG, rows(['2']))
                for schema in ('research-ast/4', 'research-ast/2'):
                    with self.subTest(engine=engine_type.__name__, schema=schema), self.assertRaises(ExpressionGap):
                        engine.describe(program(expression, schema))

    def test_old_ast1_and_ast2_results_remain_identical(self):
        data = rows(['2', '3', '5'])
        for expression, schema in (
            (binary('div', literal(1), literal(0)), 'research-ast/1'),
            (binary('and', boolean(False), boolean(None)), 'research-ast/1'),
            (window('trailing_mean', feature(), 2), 'research-ast/1'),
            (window('trailing_median', feature(), 2), 'research-ast/2'),
            (binary('sub', logarithm(literal(2)), logarithm(literal(2))), 'research-ast/2'),
        ):
            with self.subTest(expression=expression):
                original = RequiredInputEngine(CATALOG, data, allow_log=True)
                got = self.value(expression, schema=schema, outcome=True, data=data)
                self.assertEqual(got, original.evaluate(program(expression, schema), 2))

    def test_exact_operator_envelopes_reject_extra_or_missing_fields(self):
        for expression in (power(literal(2), 2), window('trailing_product', literal(2), 1),
                           window('trailing_all', boolean(True), 1), absolute(literal(-2))):
            for malformed in ({**expression, 'unapproved': 1},
                              {key: value for key, value in expression.items() if key != 'arg'}):
                with self.subTest(malformed=malformed), self.assertRaises(ExpressionGap):
                    self.value(malformed, outcome=True)

    def test_nonstring_operator_tags_retain_typed_language_rejection(self):
        for tag in ([], {}, ['abs'], {'name': 'abs'}, None, True, 1):
            with self.subTest(tag=tag):
                with self.assertRaises(ExpressionGap) as caught:
                    self.value({'op': tag, 'arg': literal(1)}, outcome=True)
                self.assertEqual(caught.exception.code, 'LANGUAGE_GAP')


if __name__ == '__main__':
    unittest.main()
