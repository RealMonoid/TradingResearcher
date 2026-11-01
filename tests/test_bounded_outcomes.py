"""Independent bounded-outcome expectations, defined before source inspection.

D089 preserves whole-scope denominators, temporal dependency evidence and
explicit numerical enclosures. Decimal is a finite cross-check, not a proof.
All observations below are small invented fixtures, not protected market data.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import unittest

from trading_researcher.bounded_outcomes import bounded_contrast, materialize_bounded
from trading_researcher.codec import digest
from trading_researcher.expressions import ExpressionGap
from trading_researcher.outcomes import reference_contrast


MAX_WIDTH = Fraction(1, 10**12)


def rational(value):
    value = Fraction(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def enclosure(lower, upper=None):
    return {'schema': 'bounded-real/1', 'lower': rational(lower),
            'upper': rational(lower if upper is None else upper)}


def feature(ref='x@1'):
    return {'op': 'feature', 'ref': ref}


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': value}


def boolean(value):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def scaled_log(arg):
    return {'op': 'mul', 'left': literal('10000', 'basis_points'),
            'right': {'op': 'ln', 'arg': arg}}


def oracle_log(value):
    value = Fraction(value)
    with localcontext() as context:
        context.prec = 120
        return Fraction((Decimal(value.numerator) / Decimal(value.denominator)).ln())


def example():
    catalog = {'x@1': {'type': 'real', 'unit': 'ratio'},
               'c@1': {'type': 'boolean', 'unit': None}}
    def program(expression):
        return {'schema': 'research-ast/2', 'catalog_hash': digest(catalog),
                'expression': expression}
    request = {
        'schema': 'bounded-reference-case-request/1',
        'candidate_ref': 'independent-bounded-candidate',
        'data_snapshot_ref': 'invented-four-observation-snapshot',
        'scope_program': program(boolean(True)),
        'condition_program': program(feature('c@1')),
        'outcome_program': program(scaled_log(feature())),
        'outcome_scale': 'quantity', 'horizon_bars': 1,
        'universe': {'start': '1970-01-01T00:00:00Z',
                     'end': '1970-01-01T01:00:00Z', 'instruments': ['A']},
        'as_of': '1970-01-01T01:00:00Z', 'max_steps': 10000,
    }
    rows = [{'time': index * 900, 'instrument': 'A', 'features': {
                'x@1': {'value': value, 'available_at': index * 900},
                'c@1': {'value': condition, 'available_at': index * 900}}}
            for index, (value, condition) in enumerate(
                [('5', True), ('1', False), ('2', None), ('4', True)])]
    return request, catalog, rows


class BoundedOutcomeTests(unittest.TestCase):
    def assert_gap(self, callback, code=None):
        with self.assertRaises(ExpressionGap) as error:
            callback()
        if code is not None:
            self.assertEqual(error.exception.code, code)
        self.assertTrue(error.exception.code.endswith('_GAP'))

    def assert_contains(self, value, expected, max_width=None):
        self.assertEqual(set(value), {'schema', 'lower', 'upper'})
        self.assertEqual(value['schema'], 'bounded-real/1')
        bounds = []
        for name in ('lower', 'upper'):
            pair = value[name]
            self.assertEqual(set(pair), {'numerator', 'denominator'})
            self.assertIs(type(pair['numerator']), str)
            self.assertIs(type(pair['denominator']), str)
            number = Fraction(int(pair['numerator']), int(pair['denominator']))
            self.assertEqual(pair, rational(number))
            bounds.append(number)
        lower, upper = bounds
        self.assertLessEqual(lower, expected)
        self.assertLessEqual(expected, upper)
        if max_width is not None:
            self.assertLessEqual(upper - lower, max_width)
        return lower, upper

    def report(self):
        return materialize_bounded(*example())

    def test_log_cases_and_unknown_condition_keep_the_whole_scope_denominator(self):
        request, catalog, rows = example()
        before = deepcopy((request, catalog, rows))
        report = materialize_bounded(request, catalog, rows)
        self.assertEqual(report['schema'], 'bounded-reference-cases/1')
        self.assertEqual(report['outcome_unit'], 'basis_points')
        self.assertEqual([case['status'] for case in report['cases']],
                         ['ELIGIBLE', 'ELIGIBLE', 'ELIGIBLE', 'PARTITION_BOUNDARY'])
        self.assertEqual([case['condition'] for case in report['cases'][:3]],
                         [True, False, None])
        log_two = 10000 * oracle_log(2)
        for case, expected in zip(report['cases'], [0, log_two, 2 * log_two]):
            self.assert_contains(case['outcome'], expected, MAX_WIDTH)
        result = bounded_contrast(report)
        self.assertEqual(result['schema'], 'bounded-reference-contrast/1')
        self.assertEqual(result['status'], 'DESCRIPTIVE_ONLY')
        self.assertEqual((result['scope_count'], result['condition_count']), (3, 1))
        self.assert_contains(result['scope_mean'], log_two, MAX_WIDTH)
        self.assert_contains(result['condition_mean'], 0, MAX_WIDTH)
        self.assert_contains(result['effect'], -log_two, 2 * MAX_WIDTH)
        self.assertFalse(report['scientific_readiness'])
        self.assertFalse(result['scientific_readiness'])
        self.assertEqual((request, catalog, rows), before)

    def test_nonzero_input_widths_propagate_through_both_means_and_difference(self):
        report = self.report()
        epsilon = Fraction(1, 10**14)
        for case, middle in zip(report['cases'], [10, 20, 30]):
            case['outcome'] = enclosure(middle - epsilon, middle + 2 * epsilon)
        result = bounded_contrast(report)
        scope_low, scope_high = self.assert_contains(result['scope_mean'], 20)
        condition_low, condition_high = self.assert_contains(result['condition_mean'], 10)
        effect_low, effect_high = self.assert_contains(result['effect'], -10)
        self.assertLessEqual(scope_low, 20 - epsilon)
        self.assertGreaterEqual(scope_high, 20 + 2 * epsilon)
        self.assertLessEqual(condition_low, 10 - epsilon)
        self.assertGreaterEqual(condition_high, 10 + 2 * epsilon)
        self.assertLessEqual(effect_low, -10 - 3 * epsilon)
        self.assertGreaterEqual(effect_high, -10 + 3 * epsilon)
        self.assertGreater(effect_high, effect_low)

    def test_all_conditioned_cases_have_zero_contained_not_fabricated_precision(self):
        request, catalog, rows = example()
        request['condition_program']['expression'] = boolean(True)
        result = bounded_contrast(materialize_bounded(request, catalog, rows))
        self.assertEqual((result['scope_count'], result['condition_count']), (3, 3))
        self.assert_contains(result['effect'], 0, 2 * MAX_WIDTH)

    def test_empty_scope_and_empty_condition_return_information_gaps(self):
        for field, reason, expected_counts in [
                ('scope_program', 'no_scope_cases', (0, 0)),
                ('condition_program', 'no_conditioned_cases', (3, 0))]:
            with self.subTest(field=field):
                request, catalog, rows = example()
                request[field]['expression'] = boolean(False)
                result = bounded_contrast(materialize_bounded(request, catalog, rows))
                self.assertEqual(result['status'], 'INFORMATION_GAP')
                self.assertEqual(result['reason'], reason)
                self.assertEqual((result['scope_count'], result['condition_count']), expected_counts)
                self.assertIsNone(result['effect'])

    def test_pending_outcomes_never_yield_a_partial_effect(self):
        request, catalog, rows = example()
        request['as_of'] = '1970-01-01T00:15:00Z'
        report = materialize_bounded(request, catalog, rows)
        self.assertEqual([case['status'] for case in report['cases']],
                         ['ELIGIBLE', 'OUTCOME_PENDING', 'NOT_YET_OBSERVED', 'NOT_YET_OBSERVED'])
        self.assertFalse(report['outcomes_complete'])
        result = bounded_contrast(report)
        self.assertEqual(result['status'], 'INFORMATION_GAP')
        self.assertEqual(result['reason'], 'outcomes_pending')
        self.assertIsNone(result['effect'])
        self.assertIsNone(result['scope_count'])

    def test_resource_stop_is_retained_without_partial_contrast(self):
        request, catalog, rows = example()
        request['max_steps'] = 1
        report = materialize_bounded(request, catalog, rows)
        self.assertEqual(report['status'], 'RESOURCE_STOP')
        self.assertFalse(report['processing_complete'])
        self.assertLess(report['processed_case_count'], report['expected_case_count'])
        self.assertIsNotNone(report['resource_reason'])
        result = bounded_contrast(report)
        self.assertIsNone(result['effect'])
        self.assertIsNone(result['scope_count'])
        self.assertNotEqual(result['status'], 'DESCRIPTIVE_ONLY')

    def test_aggregate_numeric_resource_stop_does_not_publish_a_partial_effect(self):
        report = self.report()
        for case, value in zip(report['cases'],
                               [Fraction(1, 2**8191), Fraction(1, 3**5168), Fraction(0)]):
            case['outcome'] = enclosure(value)
        result = bounded_contrast(report)
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertIsNone(result['effect'])
        self.assertIsNone(result['scope_count'])

    def test_log_domain_failures_are_missing_cases_not_clipped_values(self):
        for value in ['0', '-1', None]:
            with self.subTest(value=value):
                request, catalog, rows = example()
                rows[1]['features']['x@1']['value'] = value
                report = materialize_bounded(request, catalog, rows)
                case = report['cases'][0]
                self.assertEqual(case['status'], 'OUTCOME_MISSING')
                self.assertIsNone(case['outcome'])
                self.assertEqual(case['reason'], 'missing_value' if value is None else 'log_domain')
                self.assertIn(case['reason'], case['trace']['reasons'])

    def test_delayed_outcome_publication_stays_pending_until_it_is_available(self):
        request, catalog, rows = example()
        request['as_of'] = '1970-01-01T00:30:00Z'
        rows[2]['features']['x@1']['available_at'] = 2700
        report = materialize_bounded(request, catalog, rows)
        case = report['cases'][1]
        self.assertEqual(case['status'], 'OUTCOME_PENDING')
        self.assertEqual(case['reason'], 'required_publication_not_available')
        self.assertIsNone(case['outcome'])
        self.assertTrue(case['trace']['admissible_pending_publication'])
        request['as_of'] = '1970-01-01T00:45:00Z'
        completed = materialize_bounded(request, catalog, rows)['cases'][1]
        self.assertEqual(completed['status'], 'ELIGIBLE')
        self.assertEqual(completed['label_information_interval'], {'start': 900, 'end': 2700})

    def test_median_decisions_remain_causal_and_full_window(self):
        request, catalog, rows = example()
        request['condition_program']['expression'] = {
            'op': 'gt', 'left': {'op': 'trailing_median', 'bars': 2, 'arg': feature()},
            'right': literal('2')}
        report = materialize_bounded(request, catalog, rows)
        self.assertEqual([case['condition'] for case in report['cases'][:3]], [None, True, False])
        rows[0]['features']['x@1']['available_at'] = 1800
        first = materialize_bounded(request, catalog, rows)
        rows[0]['features']['x@1']['value'] = '999999'
        second = materialize_bounded(request, catalog, rows)
        self.assertEqual(first, second)
        self.assertIsNone(first['cases'][1]['condition'])

    def test_log_cannot_enter_scope_or_condition_via_materialization(self):
        for field in ['scope_program', 'condition_program']:
            with self.subTest(field=field):
                request, catalog, rows = example()
                request[field]['expression'] = {
                    'op': 'gt', 'left': {'op': 'ln', 'arg': feature()}, 'right': literal('0')}
                self.assert_gap(lambda: materialize_bounded(request, catalog, rows))

    def test_missing_operand_cannot_hide_late_predecision_dependency(self):
        request, catalog, rows = example()
        request['outcome_program']['expression'] = scaled_log({
            'op': 'div', 'left': feature(),
            'right': {'op': 'lag', 'bars': 2, 'arg': feature()}})
        rows[0]['features']['x@1']['available_at'] = 1800
        rows[2]['features']['x@1']['value'] = None
        report = materialize_bounded(request, catalog, rows)
        case = report['cases'][1]
        self.assertEqual(case['status'], 'REVIEW_REQUIRED')
        self.assertTrue(case['trace']['predecision_input_published_late'])
        self.assertEqual(case['trace']['declared_earliest_observation'], 0)
        self.assertIsNone(bounded_contrast(report)['effect'])

    def test_median_outcome_declared_lookback_cannot_hide_partition_crossing(self):
        request, catalog, rows = example()
        request['outcome_program']['expression'] = scaled_log({
            'op': 'trailing_median', 'bars': 3, 'arg': feature()})
        rows[1]['features']['x@1']['value'] = None
        report = materialize_bounded(request, catalog, rows)
        case = report['cases'][0]
        self.assertEqual(case['status'], 'REVIEW_REQUIRED')
        self.assertEqual(case['trace']['declared_earliest_observation'], -900)
        self.assertTrue(case['trace']['outcome_lookback_before_universe'])
        self.assertIsNone(bounded_contrast(report)['effect'])

    def test_missing_or_other_instrument_anchor_is_not_substituted(self):
        request, catalog, rows = example()
        rows[1]['instrument'] = 'B'
        report = materialize_bounded(request, catalog, rows)
        self.assertEqual(report['cases'][0]['status'], 'DATA_GAP')
        self.assertEqual(report['cases'][0]['reason'], 'missing_exact_outcome_observation')
        self.assertIsNone(report['cases'][0]['outcome'])

    def test_materialization_is_deterministic_and_unrelated_rows_do_not_change_it(self):
        request, catalog, rows = example()
        first = materialize_bounded(request, catalog, rows)
        rows.extend([{'time': 3600, 'instrument': 'A', 'features': {}},
                     {'time': 900, 'instrument': 'B', 'features': {}}])
        rows.sort(key=lambda row: (row['time'], row['instrument']))
        self.assertEqual(materialize_bounded(request, catalog, rows), first)
        self.assertEqual(materialize_bounded(request, catalog, rows), first)

    def test_quantity_and_basis_point_unit_are_explicit(self):
        for scale in ['binary_probability', 'basis_points', 'arbitrary']:
            with self.subTest(scale=scale):
                request, catalog, rows = example()
                request['outcome_scale'] = scale
                self.assert_gap(lambda: materialize_bounded(request, catalog, rows))
        request, catalog, rows = example()
        request['outcome_program']['expression']['left']['unit'] = 'ratio'
        self.assert_gap(lambda: materialize_bounded(request, catalog, rows), 'TYPE_GAP')

    def test_request_catalog_and_resource_metadata_are_not_coerced(self):
        for key, value in [('horizon_bars', True), ('horizon_bars', 0),
                           ('max_steps', 0), ('as_of', '1970-01-01'),
                           ('candidate_ref', []), ('extra', 'ignored')]:
            with self.subTest(key=key):
                request, catalog, rows = example()
                request[key] = value
                self.assert_gap(lambda: materialize_bounded(request, catalog, rows))
        request, catalog, rows = example()
        request['outcome_program']['catalog_hash'] = 'substituted-catalog'
        self.assert_gap(lambda: materialize_bounded(request, catalog, rows), 'FEATURE_GAP')

    def test_missing_malformed_reversed_and_wide_enclosures_are_typed_gaps(self):
        valid = enclosure(0)
        invalid = [None, rational(0), {}, {'schema': 'bounded-real/1', 'lower': rational(0)},
                   {**valid, 'schema': 'bounded-real/2'}, {**valid, 'extra': True},
                   {**valid, 'lower': {'numerator': '0', 'denominator': '0'}},
                   {**valid, 'lower': {'numerator': '2', 'denominator': '2'}},
                   enclosure(1, 0), enclosure(0, MAX_WIDTH + Fraction(1, 10**20))]
        for value in invalid:
            with self.subTest(value=value):
                report = self.report()
                report['cases'][0]['outcome'] = value
                self.assert_gap(lambda: bounded_contrast(report))

    def test_precision_limit_is_inclusive_and_not_only_a_schema_check(self):
        report = self.report()
        report['cases'][0]['outcome'] = enclosure(0, MAX_WIDTH)
        self.assertEqual(bounded_contrast(report)['status'], 'DESCRIPTIVE_ONLY')
        report['cases'][0]['outcome'] = enclosure(0, 2 * MAX_WIDTH)
        self.assert_gap(lambda: bounded_contrast(report), 'NUMERICAL_GAP')

    def test_materialization_rejects_an_outcome_wider_than_the_approved_limit(self):
        request, catalog, rows = example()
        request['outcome_program']['expression']['left']['value'] = '1' + '0' * 50
        self.assert_gap(lambda: materialize_bounded(request, catalog, rows), 'NUMERICAL_GAP')

    def test_case_omission_duplication_and_count_tampering_are_rejected(self):
        for mutation in ['omission', 'duplicate', 'forged_counts']:
            with self.subTest(mutation=mutation):
                report = self.report()
                if mutation == 'omission':
                    report['cases'].pop()
                elif mutation == 'duplicate':
                    report['cases'][1] = deepcopy(report['cases'][0])
                else:
                    report['processed_case_count'] -= 1
                    report['expected_case_count'] -= 1
                self.assert_gap(lambda: bounded_contrast(report), 'EVALUATION_GAP')

    def test_trace_anchor_and_label_metadata_cannot_be_forged(self):
        for mutation in ['trace_missing', 'late', 'unknown', 'lookback', 'label',
                         'anchor', 'condition_number', 'scope_false']:
            with self.subTest(mutation=mutation):
                report = self.report()
                case = report['cases'][0]
                if mutation == 'trace_missing':
                    case['trace'].pop('latest_available_at')
                elif mutation == 'late':
                    case['trace']['predecision_input_published_late'] = True
                elif mutation == 'unknown':
                    case['trace']['unknown_input'] = True
                elif mutation == 'lookback':
                    case['trace']['declared_earliest_observation'] = -900
                elif mutation == 'label':
                    case['label_information_interval']['end'] += 900
                elif mutation == 'anchor':
                    case['outcome_anchor'] += 900
                elif mutation == 'condition_number':
                    case['condition'] = 1
                else:
                    case['scope'] = False
                self.assert_gap(lambda: bounded_contrast(report), 'EVALUATION_GAP')

    def test_required_report_metadata_omissions_and_substitutions_are_typed(self):
        for key in ['request', 'cases', 'numerical_contract', 'outcome_unit']:
            with self.subTest(omitted=key):
                report = self.report()
                report.pop(key)
                self.assert_gap(lambda: bounded_contrast(report))
        for key, value in [('outcome_unit', 'ratio'),
                           ('numerical_contract', 'bounded-math/unknown')]:
            with self.subTest(changed=key):
                report = self.report()
                report[key] = value
                self.assert_gap(lambda: bounded_contrast(report), 'EVALUATION_GAP')

    def test_scalar_pipeline_rejects_bounded_report_and_disguised_interval(self):
        report = self.report()
        self.assert_gap(lambda: reference_contrast(report), 'EVALUATION_GAP')
        report['schema'] = 'reference-cases/1'
        report['request']['schema'] = 'reference-case-request/1'
        self.assert_gap(lambda: reference_contrast(report), 'EVALUATION_GAP')


if __name__ == '__main__':
    unittest.main()
