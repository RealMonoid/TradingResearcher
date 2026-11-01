"""Independent exact-case/diagnostic expectations on invented observations.

The committed tree fixture is an engineering shape, never an H_exec or a
qualified original-idea mapping. The complete expression is exercised on a
small synthetic interval; this proves no whole-Q1 resource fit or market fact.
No private artifacts, registries, keys, providers, or external data are read.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path
import unittest

from trading_researcher.bounded_outcomes import materialize_bounded
from trading_researcher.codec import canonical, digest
from trading_researcher.exact_compositions import ExactCompositionEngine
from trading_researcher.exact_outcomes import (
    REQUEST, CASES, DIAGNOSTICS, CONTRAST, materialize_exact, exact_contrast,
    add_exact_diagnostics, exact_base_projection, lookback,
)
from trading_researcher.expressions import ExpressionGap
from trading_researcher.required_inputs import materialize_required


D = 900
T = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
CATALOG = {'x@1': {'type': 'real', 'unit': 'ratio'},
           'flag@1': {'type': 'boolean', 'unit': None}}
FIXTURE = json.loads((Path(__file__).parent / 'fixtures' /
                      'exact_composition_shape_2026-11-01.json').read_text(encoding='utf-8'))


def utc(when):
    return datetime.fromtimestamp(when, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit,
            'value': None if value is None else str(value)}


def boolean(value):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def feature(ref):
    return {'op': 'feature', 'ref': ref}


def window(op, arg, bars):
    return {'op': op, 'arg': arg, 'bars': bars}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def program(expression, catalog=CATALOG):
    return {'schema': 'research-ast/4', 'catalog_hash': digest(catalog), 'expression': expression}


def request(count=6):
    return {'schema': REQUEST, 'candidate_ref': 'synthetic-independent-review',
            'data_snapshot_ref': 'synthetic-never-market-evidence',
            'scope_program': program(boolean(True)),
            'condition_program': program(feature('flag@1')),
            'outcome_program': program(binary('mul', literal(1, 'basis_points'), feature('x@1'))),
            'outcome_scale': 'quantity', 'horizon_bars': 1,
            'universe': {'start': utc(T), 'end': utc(T + count * D), 'instruments': ['SYNTHETIC']},
            'as_of': utc(T + count * D), 'max_steps': 100_000}


def history(count=6, flags=(True, False, None, True, False, True)):
    return [{'time': T + i * D, 'instrument': 'SYNTHETIC', 'features': {
        'x@1': {'value': str(i + 1), 'available_at': T + i * D},
        'flag@1': {'value': flags[i % len(flags)], 'available_at': T + i * D}}}
        for i in range(count)]


def number(pair):
    return Fraction(int(pair['numerator']), int(pair['denominator']))


def enclosure(value):
    return number(value['lower']), number(value['upper'])


def a_history(count=55):
    """Invented values; no outcome-driven threshold or real snapshot input."""
    result = []
    for i in range(count):
        values = {'H': '120', 'L': '80', 'C': str(Decimal(100) + Decimal(i) / 10),
                  'Q': '100', 'B': '50'}
        if i == 39:
            values.update(H='100.5', L='100', Q='250', B='125')
        result.append({'time': T + i * D, 'instrument': 'BTCUSDT', 'features': {
            ref + '@1': {'value': value, 'available_at': T + (i + 1) * D}
            for ref, value in values.items()}})
    return result


def a_request(count=55):
    result = request(count)
    result.update(scope_program=deepcopy(FIXTURE['programs']['scope']),
                  condition_program=deepcopy(FIXTURE['programs']['condition']),
                  outcome_program=deepcopy(FIXTURE['programs']['outcome']), horizon_bars=5)
    result['universe']['instruments'] = ['BTCUSDT']
    # Explicit engineering fixture allowance for both base and diagnostic
    # replay (the measured negative-endpoint fixture needs 194,788 steps).
    # This stays below the existing 10M ceiling and sets no research default.
    result['max_steps'] = 250_000
    return result


def literal_a_condition(data, decision):
    """Original log formula and complete validity, not a power/product DSL."""
    lookup = {row['time']: row['features'] for row in data}
    def read(when, ref):
        sample = lookup[when][ref + '@1']
        if sample['value'] is None or sample['available_at'] > decision:
            raise ValueError('Unavailable synthetic required input')
        return Decimal(sample['value'])
    with localcontext() as context:
        context.prec = 120
        try:
            b = decision - D
            h, low, q, buy = [read(b, ref) for ref in ('H', 'L', 'Q', 'B')]
            baseline = [tuple(read(b - k * D, ref) for ref in ('H', 'L', 'Q')) for k in range(1, 33)]
            if not (h >= low > 0 and q > 0 and 0 <= buy <= q):
                return None
            if any(not (high >= bottom > 0 and volume >= 0) for high, bottom, volume in baseline):
                return None
            mq = sum(volume for _, _, volume in baseline) / 32
            mw = sum((high / bottom).ln() for high, bottom, _ in baseline) / 32
            if not (mq > 0 and mw > 0):
                return None
            return q >= 2 * mq and Decimal('0.45') <= buy / q <= Decimal('0.55') and (h / low).ln() <= mw / 2
        except (KeyError, ValueError):
            return None


class ExactOutcomesReview(unittest.TestCase):
    def assert_gap(self, callback):
        with self.assertRaises(ExpressionGap) as caught:
            callback()
        self.assertTrue(caught.exception.code.endswith('_GAP'))

    def diagnostics(self, base, catalog, data):
        return add_exact_diagnostics(base, catalog, data,
                                     base['request']['max_steps'] - base['primitive_steps'])

    def test_explicit_versions_contracts_and_original_engineering_shape(self):
        self.assertEqual((REQUEST, CASES, DIAGNOSTICS, CONTRAST), (
            'exact-composition-case-request/1', 'exact-composition-cases/1',
            'diagnostic-exact-composition-cases/1', 'exact-composition-contrast/1'))
        req, data = a_request(), a_history()
        before = canonical([req, data])
        report = materialize_exact(req, FIXTURE['catalog'], data)
        self.assertEqual(report['schema'], CASES)
        self.assertEqual(report['evaluation_contract'], 'required-inputs/1')
        self.assertEqual(report['expression_contract'], 'bounded-exact-compositions/1.0')
        self.assertEqual(report['numerical_contract'], 'bounded-math/1.0')
        self.assertFalse(report['scientific_readiness'])
        self.assertTrue(report['processing_complete'])
        self.assertEqual(report['expected_case_count'], 55)
        self.assertEqual(report['state_counts']['ELIGIBLE'], 50)
        self.assertEqual(report['state_counts']['PARTITION_BOUNDARY'], 5)
        for i, case in enumerate(report['cases']):
            with self.subTest(case=i):
                self.assertIs(case['condition'], literal_a_condition(data, T + i * D))
                self.assertEqual(case['outcome_anchor'], T + (i + 5) * D)
                if i >= 50:
                    self.assertIsNone(case['outcome'])
                    continue
                lo, hi = enclosure(case['outcome'])
                with localcontext() as context:
                    context.prec = 100
                    expected = Fraction(abs(((Decimal(100) + Decimal(i + 4) / 10) /
                                              (Decimal(100) + Decimal(i) / 10)).ln()) * 10000)
                self.assertLessEqual(lo, expected)
                self.assertLessEqual(expected, hi)
                self.assertEqual(case['trace']['declared_earliest_observation'], T + i * D)
        contrast = exact_contrast(report)
        self.assertEqual(contrast['scope_count'], 50)
        self.assertEqual(contrast['condition_count'], 1)
        self.assertEqual(contrast['status'], 'DESCRIPTIVE_ONLY')
        self.assertFalse(contrast['scientific_readiness'])
        self.assertEqual(before, canonical([req, data]))

    def test_unknown_and_false_conditions_stay_in_whole_scope_denominator(self):
        report = materialize_exact(request(), CATALOG, history())
        self.assertEqual([c['condition'] for c in report['cases'][:5]], [True, False, None, True, False])
        self.assertTrue(all(c['status'] == 'ELIGIBLE' for c in report['cases'][:5]))
        result = exact_contrast(report)
        self.assertEqual(result['schema'], CONTRAST)
        self.assertEqual((result['scope_count'], result['condition_count']), (5, 2))
        self.assertEqual(enclosure(result['scope_mean']), (Fraction(4), Fraction(4)))
        self.assertEqual(enclosure(result['condition_mean']), (Fraction(7, 2), Fraction(7, 2)))
        self.assertEqual(enclosure(result['effect']), (Fraction(-1, 2), Fraction(-1, 2)))

    def test_observed_zero_is_defined_but_empty_condition_is_not(self):
        data = history()
        for row in data:
            row['features']['x@1']['value'] = '0'
        result = exact_contrast(materialize_exact(request(), CATALOG, data))
        self.assertEqual(result['status'], 'DESCRIPTIVE_ONLY')
        self.assertEqual(enclosure(result['effect']), (0, 0))
        for row in data:
            row['features']['flag@1']['value'] = False
        result = exact_contrast(materialize_exact(request(), CATALOG, data))
        self.assertEqual(result['status'], 'INFORMATION_GAP')
        self.assertEqual(result['reason'], 'no_conditioned_cases')
        self.assertIsNone(result['effect'])

    def test_no_unused_decision_or_anchor_container_prerequisite(self):
        req, data = request(8), history(8)
        req['condition_program'] = program(window('lag', feature('flag@1'), 1))
        req['outcome_program'] = program(binary('mul', literal(1, 'basis_points'), window('lag', feature('x@1'), 2)))
        req['horizon_bars'] = 3
        data = [row for row in data if row['time'] not in (T + D, T + 4 * D)]
        case = materialize_exact(req, CATALOG, data)['cases'][1]
        self.assertEqual(case['status'], 'ELIGIBLE')
        self.assertEqual(enclosure(case['outcome']), (3, 3))
        self.assertIs(case['condition'], True)
        self.assertEqual(case['trace']['earliest_observation'], T + 2 * D)
        self.assertEqual(case['label_information_interval'], {'start': T + D, 'end': T + 4 * D})

    def test_new_window_lookback_and_diagnostic_declared_earliest_match(self):
        req, data = request(12), history(12)
        product = window('lag', window('trailing_product', window('lag', feature('x@1'), 2), 3), 1)
        req['outcome_program'] = program(binary('mul', literal(1, 'basis_points'), product))
        req['horizon_bars'] = 5
        engine = ExactCompositionEngine(CATALOG, data, allow_log=True)
        self.assertEqual(lookback(engine._program_node(req['outcome_program'])), 5 * D)
        boolean_window = window('lag', window('trailing_all', window('lag', feature('flag@1'), 2), 4), 3)
        self.assertEqual(lookback(engine._program_node(program(boolean_window))), 8 * D)
        base = materialize_exact(req, CATALOG, data)
        for i, case in enumerate(base['cases'][:7]):
            self.assertEqual(case['status'], 'ELIGIBLE')
            self.assertEqual(enclosure(case['outcome']), ((i + 1) * (i + 2) * (i + 3),) * 2)
            self.assertEqual(case['trace']['declared_earliest_observation'], T + i * D)
        diagnostic = self.diagnostics(base, CATALOG, data)
        self.assertEqual(diagnostic['diagnostics']['status'], 'COMPLETE')
        self.assertEqual(exact_base_projection(diagnostic), base)
        self.assertEqual(diagnostic, self.diagnostics(base, CATALOG, data))

    def test_prior_universe_window_remains_review_required_and_reports_warmup(self):
        req, data = request(), history()
        req['outcome_program'] = program(binary('mul', literal(1, 'basis_points'),
                                                 window('trailing_product', feature('x@1'), 3)))
        for prior_present in (False, True):
            with self.subTest(prior_present=prior_present):
                actual = deepcopy(data)
                if prior_present:
                    actual.insert(0, {'time': T - D, 'instrument': 'SYNTHETIC', 'features': {
                        'x@1': {'value': '2', 'available_at': T - D}}})
                base = materialize_exact(req, CATALOG, actual)
                first = base['cases'][0]
                self.assertEqual(first['status'], 'REVIEW_REQUIRED')
                self.assertEqual(first['trace']['declared_earliest_observation'], T - D)
                self.assertTrue(first['trace']['outcome_lookback_before_universe'])
                diag = self.diagnostics(base, CATALOG, actual)
                categories = diag['cases'][0]['diagnostics']['reason_categories']
                self.assertIn('input_before_universe', categories)
                if not prior_present:
                    self.assertIn('missing_warmup', categories)
                self.assertEqual(exact_base_projection(diag), base)

    def test_horizon_cutoff_and_exclusive_end_have_distinct_states(self):
        req = request()
        req['as_of'] = utc(T + 3 * D)
        cases = materialize_exact(req, CATALOG, history())['cases']
        self.assertEqual([c['status'] for c in cases],
                         ['ELIGIBLE'] * 3 + ['OUTCOME_PENDING', 'NOT_YET_OBSERVED', 'NOT_YET_OBSERVED'])
        self.assertEqual(cases[3]['reason'], 'horizon_not_elapsed')
        final = materialize_exact(request(), CATALOG, history())['cases'][-1]
        self.assertEqual(final['status'], 'PARTITION_BOUNDARY')
        self.assertEqual(final['reason'], 'anchor_at_or_after_exclusive_end')
        self.assertIsNone(final['outcome'])

    def test_existing_asof_cutoff_is_not_silently_replaced_with_anchor_cap(self):
        # This checks inherited required-input semantics, not qualification of
        # the original A's independently required fixed publication delay.
        req, data = request(), history()
        req['as_of'] = utc(T + 4 * D)
        data[1]['features']['x@1']['available_at'] = T + 3 * D
        case = materialize_exact(req, CATALOG, data)['cases'][0]
        self.assertEqual(case['status'], 'ELIGIBLE')
        self.assertEqual(case['label_information_interval']['end'], T + 3 * D)
        data[1]['features']['x@1']['available_at'] = T + 5 * D
        case = materialize_exact(req, CATALOG, data)['cases'][0]
        self.assertEqual(case['status'], 'OUTCOME_PENDING')
        self.assertEqual(case['reason'], 'required_publication_not_available')

    def test_unknown_factor_plus_zero_outcome_is_missing_and_retains_diagnostics(self):
        req, data = request(), history()
        req['outcome_program'] = program(binary('mul', literal(1, 'basis_points'),
            window('trailing_product', feature('x@1'), 2)))
        data[0]['features']['x@1']['value'] = None
        data[1]['features']['x@1']['value'] = '0'
        base = materialize_exact(req, CATALOG, data)
        self.assertEqual(base['cases'][0]['status'], 'OUTCOME_MISSING')
        self.assertIsNone(base['cases'][0]['outcome'])
        diag = self.diagnostics(base, CATALOG, data)
        self.assertIn('missing_value', diag['cases'][0]['diagnostics']['reason_categories'])
        self.assertEqual(exact_base_projection(diag), base)

    def test_original_outcome_rejects_two_negative_endpoints_not_only_bad_ratio(self):
        req, data = a_request(), a_history()
        data[40]['features']['C@1']['value'] = '-100'
        data[44]['features']['C@1']['value'] = '-110'
        base = materialize_exact(req, FIXTURE['catalog'], data)
        self.assertEqual(base['cases'][40]['status'], 'OUTCOME_MISSING')
        self.assertIsNone(base['cases'][40]['outcome'])
        diag = self.diagnostics(base, FIXTURE['catalog'], data)
        self.assertIn('numeric_domain', diag['cases'][40]['diagnostics']['reason_categories'])
        self.assertEqual(exact_base_projection(diag), base)

    def test_resource_stopped_base_is_exact_prefix_with_no_effect(self):
        full = materialize_exact(request(), CATALOG, history())
        req = request()
        req['max_steps'] = 12
        base = materialize_exact(req, CATALOG, history())
        self.assertFalse(base['processing_complete'])
        self.assertEqual(base['status'], 'RESOURCE_STOP')
        self.assertEqual(base['processed_case_count'], 2)
        self.assertEqual(base['cases'], full['cases'][:2])
        self.assertEqual(base['primitive_steps'], 12)
        contrast = exact_contrast(base)
        self.assertEqual(contrast['status'], 'RESOURCE_STOP')
        self.assertIsNone(contrast['effect'])
        diag = add_exact_diagnostics(base, CATALOG, history(), 0)
        self.assertEqual(diag['diagnostics']['status'], 'RESOURCE_STOP')
        self.assertEqual(diag['diagnostics']['processed_cases'], 0)
        self.assertTrue(all(c['diagnostics'] is None for c in diag['cases']))
        self.assertEqual(exact_base_projection(diag), base)

    def test_diagnostic_resource_stop_preserves_complete_base_and_later_replay(self):
        base = materialize_exact(request(), CATALOG, history())
        diag = add_exact_diagnostics(base, CATALOG, history(), 1)
        self.assertEqual(diag['diagnostics']['status'], 'RESOURCE_STOP')
        self.assertEqual(exact_base_projection(diag), base)
        self.assertEqual(self.diagnostics(base, CATALOG, history())['diagnostics']['status'], 'COMPLETE')
        for budget in (-1, True, 10_000_001):
            with self.subTest(budget=budget):
                self.assert_gap(lambda: add_exact_diagnostics(base, CATALOG, history(), budget))

    def test_projection_and_replay_reject_changed_base_values_and_inputs(self):
        base = materialize_exact(request(), CATALOG, history())
        diag = self.diagnostics(base, CATALOG, history())
        altered = deepcopy(diag)
        altered['cases'][0]['condition'] = False
        self.assert_gap(lambda: exact_base_projection(altered))
        altered = deepcopy(diag)
        altered['processed_case_count'] -= 1
        self.assert_gap(lambda: exact_base_projection(altered))
        altered = deepcopy(base)
        altered['cases'][0]['outcome']['upper']['numerator'] = '9'
        altered['cases'][0]['outcome']['lower']['numerator'] = '9'
        # Contrast has no source rows or authenticated original: another
        # well-formed numeric value is not distinguishable there. Replay is
        # the operation that must reject the mismatch with supplied inputs.
        self.assert_gap(lambda: self.diagnostics(altered, CATALOG, history()))
        changed = history()
        changed[1]['features']['x@1']['value'] = '9'
        self.assert_gap(lambda: self.diagnostics(base, CATALOG, changed))
        self.assertEqual(exact_base_projection(diag), base)

    def test_replay_rejects_reclassification_that_removes_an_observed_case(self):
        base = materialize_exact(request(), CATALOG, history())
        altered = deepcopy(base)
        altered['cases'][0]['status'] = 'OUTCOME_MISSING'
        altered['cases'][0]['reason'] = 'missing_value'
        altered['state_counts']['ELIGIBLE'] -= 1
        altered['state_counts']['OUTCOME_MISSING'] += 1
        # Preserve values, trace and global counts: a replay must still reject
        # a status that excludes the independently observed value from means.
        self.assert_gap(lambda: self.diagnostics(altered, CATALOG, history()))

    def test_replay_cannot_skip_an_outcome_after_trace_and_value_removal(self):
        base = materialize_exact(request(), CATALOG, history())
        altered = deepcopy(base)
        altered['cases'][0].update(status='OUTCOME_MISSING', reason='missing_value',
                                   outcome=None, trace=None, label_information_interval=None)
        altered['state_counts']['ELIGIBLE'] -= 1
        altered['state_counts']['OUTCOME_MISSING'] += 1
        self.assert_gap(lambda: self.diagnostics(altered, CATALOG, history()))

    def test_replay_rejects_reason_mutation_even_when_values_and_traces_match(self):
        base = materialize_exact(request(), CATALOG, history())
        for index in (0, 5):
            altered = deepcopy(base)
            altered['cases'][index]['reason'] = 'fabricated_reason'
            with self.subTest(index=index):
                self.assert_gap(lambda: self.diagnostics(altered, CATALOG, history()))

    def test_diagnostic_budget_is_the_explicit_remaining_shared_allowance(self):
        base = materialize_exact(request(), CATALOG, history())
        remaining = base['request']['max_steps'] - base['primitive_steps']
        self.assertEqual(add_exact_diagnostics(base, CATALOG, history(), remaining)['diagnostics']['status'], 'COMPLETE')
        self.assert_gap(lambda: add_exact_diagnostics(base, CATALOG, history(), remaining + 1))
        for invalid in (-1, True, base['request']['max_steps'] + 1):
            altered = deepcopy(base)
            altered['primitive_steps'] = invalid
            with self.subTest(primitive_steps=invalid):
                self.assert_gap(lambda: self.diagnostics(altered, CATALOG, history()))

    def test_contrast_rejects_case_order_counts_and_contract_tampering(self):
        base = materialize_exact(request(), CATALOG, history())
        for field, value in (('schema', 'required-input-bounded-reference-cases/1'),
                             ('evaluation_contract', 'different/1'),
                             ('expression_contract', 'different/1'),
                             ('numerical_contract', 'different/1'),
                             ('processed_case_count', 0)):
            changed = deepcopy(base)
            changed[field] = value
            with self.subTest(field=field):
                self.assert_gap(lambda: exact_contrast(changed))
        changed = deepcopy(base)
        changed['cases'][0], changed['cases'][1] = changed['cases'][1], changed['cases'][0]
        self.assert_gap(lambda: exact_contrast(changed))

    def test_request_versions_types_and_required_outcome_feature_are_explicit(self):
        for schema in ('reference-case-request/1', 'bounded-reference-case-request/1', 'unknown/1'):
            req = request()
            req['schema'] = schema
            with self.subTest(schema=schema):
                self.assert_gap(lambda: materialize_exact(req, CATALOG, history()))
        for old_materializer in (materialize_bounded, materialize_required):
            self.assert_gap(lambda: old_materializer(request(), CATALOG, history()))
        for key, value in (('outcome_scale', 'binary_probability'), ('horizon_bars', True),
                           ('max_steps', 10_000_001)):
            req = request()
            req[key] = value
            with self.subTest(key=key):
                self.assert_gap(lambda: materialize_exact(req, CATALOG, history()))
        req = request()
        req['outcome_program'] = program(literal(1, 'basis_points'))
        self.assert_gap(lambda: materialize_exact(req, CATALOG, history()))


if __name__ == '__main__':
    unittest.main()
