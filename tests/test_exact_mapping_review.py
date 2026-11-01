"""Inactive exact representations; no native idea repair or profile activation.

Only synthetic public engineering inputs are used. The full quarter lower
bound is conditional on complete valid windows for this concrete tree, not a
proof that every faithful AST4 representation must exceed the cap.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import unittest

from exact_mapping_support import programs, supplied
from test_exact_compositions import FIXTURE, D, history, change
from test_exact_runtime import payload, history as timed_history
from trading_researcher.case_diagnostics import _guard
from trading_researcher.codec import canonical, digest
from trading_researcher.exact_compositions import ExactCompositionEngine
from trading_researcher.exact_outcomes import materialize_exact, add_exact_diagnostics
from trading_researcher.exact_runtime import compile_payload
from trading_researcher.expressions import ExpressionGap


def literal(value, kind='boolean', unit=None):
    return {'op': 'literal', 'type': kind, 'unit': unit, 'value': value}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def wrapped(expression, catalog):
    return {'schema': 'research-ast/4', 'catalog_hash': digest(catalog), 'expression': expression}


def evaluate(program, rows, when, *, outcome=False, cutoff=None, trace=None, budget=1_000_000):
    engine = ExactCompositionEngine(FIXTURE['catalog'], rows, allow_log=outcome)
    remaining = [budget]
    value = engine._calculate(engine._program_node(program), when, 'BTCUSDT',
                              when if cutoff is None else cutoff, remaining, trace)
    return value.public(), budget - remaining[0]


def size(node):
    return 1 + sum(size(node[key]) for key in ('arg', 'left', 'right') if key in node)


def depth(node):
    return max([depth(node[key]) + 1 for key in ('arg', 'left', 'right') if key in node] or [0])


class ExactMappingReview(unittest.TestCase):
    def test_all_nine_strict_guard_values_and_false_unknown_counterexample(self):
        engine = ExactCompositionEngine({}, [{'time': 0, 'instrument': 'X', 'features': {}}])
        for valid in (True, False, None):
            for predicate in (True, False, None):
                v, p, unknown = literal(valid), literal(predicate), literal(None)
                old = binary('or', binary('and', v, p),
                             binary('and', {'op': 'not', 'arg': v}, unknown))
                new = binary('eq', binary('or', v, unknown), p)
                expected = predicate if valid is True else None
                with self.subTest(valid=valid, predicate=predicate):
                    for expression in (old, new):
                        node = engine._program_node(wrapped(expression, {}))
                        self.assertIs(engine._calculate(node, 0, 'X', 0, [1000]).value, expected)
        # Merely ANDing the predicate with V OR unknown is incorrect: a known
        # false clause would hide invalidity, contrary to the original idea.
        wrong = binary('and', binary('or', literal(False), literal(None)), literal(False))
        value = engine._calculate(engine._program_node(wrapped(wrong, {})), 0, 'X', 0, [1000])
        self.assertIs(value.value, False)

    def test_concrete_tree_cost_and_conditional_two_pass_lower_bound(self):
        before = canonical(FIXTURE)
        alternative = programs()
        self.assertEqual(canonical(FIXTURE), before)
        self.assertEqual(alternative['scope'], FIXTURE['programs']['scope'])
        self.assertEqual((size(alternative['condition']['expression']), depth(alternative['condition']['expression'])),
                         (81, 11))
        self.assertEqual((size(alternative['outcome']['expression']), depth(alternative['outcome']['expression'])),
                         (29, 8))
        old, old_steps = evaluate(FIXTURE['programs']['condition'], history(), 40 * D)
        new, new_steps = evaluate(alternative['condition'], history(), 40 * D)
        self.assertIs(old['value'], True)
        self.assertEqual(new, old)
        self.assertEqual((old_steps, new_steps), (1454, 844))
        # In an all-valid 8640-coordinate engineering quarter, indices33..8639
        # have complete signal/baseline windows. Each numerical and diagnostic
        # pass evaluates this unchanged V/P tree. Outcomes are ignored here.
        lower_bound = 2 * (8640 - 33) * 844
        self.assertEqual(lower_bound, 14_528_616)
        self.assertGreater(lower_bound, 10_000_000)

    def test_original_condition_domains_equalities_and_unknown_dominance(self):
        selected = programs()['condition']
        cases = []
        rows = history()
        for index in range(7, 39):
            change(rows, index, 'H', '4'); change(rows, index, 'L', '1')
        change(rows, 39, 'H', '2'); change(rows, 39, 'L', '1')
        cases.append(('exact_log_equality', rows, True))
        for share, expected in (('112.5', True), ('137.5', True), ('112.49', False), ('137.51', False)):
            rows = history(); change(rows, 39, 'B', share)
            cases.append(('share_' + share, rows, expected))
        for label, index, feature, value in (
            ('signal_low_zero', 39, 'L', '0'), ('signal_H_below_L', 39, 'H', '99'),
            ('signal_Q_zero', 39, 'Q', '0'), ('signal_B_negative', 39, 'B', '-1'),
            ('signal_B_above_Q', 39, 'B', '251'), ('baseline_Q_negative', 10, 'Q', '-1'),
            ('baseline_L_zero', 10, 'L', '0'), ('baseline_H_below_L', 10, 'H', '70'),
            ('baseline_H_null', 10, 'H', None)):
            rows = history(); change(rows, index, feature, value)
            cases.append((label, rows, None))
        for feature, value in (('Q', '0'), ('H', '80')):
            rows = history()
            for index in range(7, 39): change(rows, index, feature, value)
            cases.append(('zero_baseline_' + feature, rows, None))
        rows = history(); change(rows, 39, 'Q', '100'); change(rows, 39, 'B', '50')
        change(rows, 10, 'H', None); cases.append(('known_false_and_missing', rows, None))
        rows = history(); rows[7]['features']['L@1']['available_at'] = 40 * D + 1
        cases.append(('earliest_required_late', rows, None))
        rows = history(); rows.pop(7); cases.append(('earliest_required_absent', rows, None))
        for label, rows, expected in cases:
            with self.subTest(case=label):
                trace_old, trace_new = [], []
                old, _ = evaluate(FIXTURE['programs']['condition'], rows, 40 * D,
                                  trace=lambda *event: trace_old.append(event))
                new, _ = evaluate(selected, rows, 40 * D, trace=lambda *event: trace_new.append(event))
                self.assertIs(new['value'], expected)
                self.assertEqual(new['value'], old['value'])
                self.assertEqual(set(trace_new), set(trace_old))
                self.assertTrue(all(event[0] < 40 * D for event in trace_new))

    def test_valid_outcome_enclosures_and_endpoint_domains(self):
        selected = programs()['outcome']
        for first, last in (('100', '110'), ('110', '100'), ('100', '100'),
                            ('0.' + '0' * 96 + '1', '9' * 99),
                            ('-100', '-110'), ('-100', '110'), ('100', '-110'),
                            ('0', '1'), ('1', '0'), (None, '1'), ('1', None)):
            rows = history(); change(rows, 40, 'C', first); change(rows, 44, 'C', last)
            with self.subTest(first=first, last=last):
                old, _ = evaluate(FIXTURE['programs']['outcome'], rows, 45 * D, outcome=True)
                new, _ = evaluate(selected, rows, 45 * D, outcome=True)
                self.assertEqual(new, old)
                valid = first is not None and last is not None and Fraction(first) > 0 and Fraction(last) > 0
                self.assertEqual(new['value'] is not None, valid)
                if valid:
                    with localcontext() as context:
                        context.prec = 220
                        oracle = Fraction(abs((Decimal(last) / Decimal(first)).ln()) * 10000)
                    lower, upper = (Fraction(int(new['value'][side]['numerator']),
                                            int(new['value'][side]['denominator'])) for side in ('lower', 'upper'))
                    self.assertLessEqual(lower, oracle)
                    self.assertGreaterEqual(upper, oracle)
                    self.assertLess(upper - lower, Fraction(1, 10**12))

    def test_endpoint_missingness_availability_and_required_coordinates(self):
        selected = programs()['outcome']
        for which in (40, 44):
            for kind in ('null', 'missing_feature', 'absent_row', 'late'):
                rows = history()
                if kind == 'null': change(rows, which, 'C', None)
                elif kind == 'missing_feature': rows[which]['features'].pop('C@1')
                elif kind == 'absent_row': rows.pop(which)
                else: rows[which]['features']['C@1']['available_at'] = 45 * D + 1
                with self.subTest(endpoint=which, defect=kind):
                    old, _ = evaluate(FIXTURE['programs']['outcome'], rows, 45 * D, outcome=True)
                    trace = []
                    new, _ = evaluate(selected, rows, 45 * D, outcome=True,
                                      trace=lambda *event: trace.append(event))
                    self.assertEqual(new, old)
                    self.assertIsNone(new['value'])
                    self.assertEqual({event[0] for event in trace}, {40 * D, 44 * D})
        result, _ = evaluate(selected, history(), 45 * D, outcome=True, cutoff=45 * D - 1)
        self.assertIsNone(result['value'])
        rows = history(); rows[39]['features'].pop('C@1')
        self.assertIs(evaluate(programs()['condition'], rows, 40 * D)[0]['value'], True)

    def test_sign_domain_guard_preserves_8192_intermediate_bounds(self):
        # Raw source decimals are at most100characters; an8192bit endpoint
        # cannot be injected as an admitted raw string. Exercise this exact
        # algebraic identity at the core's rational boundary with an existing
        # AST power, without representing it as an actual market close.
        catalog = {}; rows = [{'time': 0, 'instrument': 'X', 'features': {}}]
        engine = ExactCompositionEngine(catalog, rows, allow_log=True)
        def operand(exponent, sign):
            value = {'op': 'integer_power', 'arg': literal('2', 'real', 'ratio'), 'exponent': exponent}
            return binary('mul', literal(str(sign), 'real', 'price:BTCUSDT'), value)
        def guards(value):
            old = binary('mul', literal('0', 'real', 'ratio'),
                         {'op': 'ln', 'arg': binary('div', deepcopy(value), literal('1', 'real', 'price:BTCUSDT'))})
            new = binary('mul', literal('0', 'real', 'ratio'),
                         {'op': 'ln', 'arg': binary('div', deepcopy(value), {'op': 'abs', 'arg': deepcopy(value)})})
            return old, new
        for sign in (1, -1):
            for expression in guards(operand(8191, sign)):
                value = engine._calculate(engine._program_node(wrapped(expression, catalog)), 0, 'X', 0, [100000])
                self.assertEqual(value.value is None, sign < 0)
                if sign > 0:
                    self.assertEqual(value.value.lower, 0); self.assertEqual(value.value.upper, 0)
        for expression in guards(operand(8192, 1)):
            with self.assertRaises(ExpressionGap) as failure:
                engine._calculate(engine._program_node(wrapped(expression, catalog)), 0, 'X', 0, [100000])
            self.assertEqual(failure.exception.code, 'RESOURCE_GAP')

    def test_complete_diagnostics_retains_explicit_unrecognized_guard_gap(self):
        alternative_request = compile_payload(supplied())['request']
        original_request = compile_payload(payload())['request']
        rows = timed_history()
        original = materialize_exact(original_request, FIXTURE['catalog'], rows)
        alternative = materialize_exact(alternative_request, FIXTURE['catalog'], rows)
        self.assertEqual(alternative['cases'], original['cases'])
        self.assertIsNone(_guard(programs()['condition']['expression']))
        self.assertIsNotNone(_guard(FIXTURE['programs']['condition']['expression']))
        report = add_exact_diagnostics(alternative, FIXTURE['catalog'], rows,
                    alternative_request['max_steps'] - alternative['primitive_steps'])
        self.assertTrue(report['diagnostics']['processing_complete'])
        self.assertEqual(report['diagnostics']['guard_counts']['unrecognized'], 55)
        self.assertTrue(all(not case['diagnostics']['validity_guard']['recognized'] for case in report['cases']))
        self.assertIs(report['scientific_readiness'], False)

    def test_tracing_missing_mean_has_different_work_and_resource_prefix(self):
        catalog = {'x@1': {'type': 'real', 'unit': 'ratio'}}
        rows = [{'time': i * D, 'instrument': 'X', 'features': {
            'x@1': {'value': None if i == 31 else '1', 'available_at': i * D}}} for i in range(32)]
        expression = {'op': 'trailing_mean', 'bars': 32, 'arg': {'op': 'feature', 'ref': 'x@1'}}
        engine = ExactCompositionEngine(catalog, rows)
        node = engine._program_node(wrapped(expression, catalog))
        costs = []
        for trace in (None, lambda *event: None):
            remaining = [1000]
            value = engine._calculate(node, 31 * D, 'X', 31 * D, remaining, trace)
            self.assertIsNone(value.value)
            costs.append(1000 - remaining[0])
        self.assertEqual(costs, [2, 33])
        self.assertIsNone(engine._calculate(node, 31 * D, 'X', 31 * D, [10]).value)
        with self.assertRaises(ExpressionGap) as failure:
            engine._calculate(node, 31 * D, 'X', 31 * D, [10], lambda *event: None)
        self.assertEqual(failure.exception.code, 'RESOURCE_GAP')


if __name__ == '__main__':
    unittest.main()
