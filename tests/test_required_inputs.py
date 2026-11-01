"""Independent required-inputs/1 expectations on small invented observations.

Coordinates are not additional market observations. Actual feature dependencies,
complete windows, causal cutoffs and legacy versions keep their stated rules.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
import unittest

from trading_researcher.bounded_outcomes import bounded_contrast, materialize_bounded
from trading_researcher.codec import canonical, digest
from trading_researcher.expressions import ExpressionGap
from trading_researcher.outcomes import reference_contrast
from trading_researcher.required_inputs import (
    add_required_diagnostics, materialize_required, required_contrast,
)


CATALOG = {'open@1': {'type': 'real', 'unit': 'USDT/A'},
           'close@1': {'type': 'real', 'unit': 'USDT/A'},
           'x@1': {'type': 'real', 'unit': 'ratio'},
           'flag@1': {'type': 'boolean', 'unit': None}}


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': value}


def boolean(value):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def feature(name):
    return {'op': 'feature', 'ref': name}


def lag(arg, bars):
    return {'op': 'lag', 'arg': arg, 'bars': bars}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def program(expression):
    return {'schema': 'research-ast/2', 'catalog_hash': digest(CATALOG), 'expression': expression}


def example():
    expression = binary('mul', literal('10000', 'basis_points'), {'op': 'ln', 'arg':
        binary('div', lag(feature('close@1'), 1), lag(feature('open@1'), 2))})
    request = {'schema': 'bounded-reference-case-request/1', 'candidate_ref': 'invented-required-inputs',
        'data_snapshot_ref': 'invented-eight-observations', 'scope_program': program(boolean(True)),
        'condition_program': program(lag(feature('flag@1'), 1)), 'outcome_program': program(expression),
        'outcome_scale': 'quantity', 'horizon_bars': 3,
        'universe': {'start': '1970-01-01T00:00:00Z', 'end': '1970-01-01T02:00:00Z', 'instruments': ['A']},
        'as_of': '1970-01-01T02:00:00Z', 'max_steps': 100000}
    rows = [{'time': i * 900, 'instrument': 'A', 'features': {
        'open@1': {'value': '100', 'available_at': i * 900},
        'close@1': {'value': '200', 'available_at': i * 900},
        'x@1': {'value': str(2 * i + 1), 'available_at': i * 900},
        'flag@1': {'value': (True, False, None, True)[i % 4], 'available_at': i * 900}}} for i in range(8)]
    return request, deepcopy(CATALOG), rows


def without(rows, *times):
    return [row for row in rows if row['time'] not in times]


def stream_hash(cases):
    checksum = hashlib.sha256()
    for case in cases:
        checksum.update((canonical(case) + '\n').encode('utf-8'))
    return checksum.hexdigest()


class RequiredInputTests(unittest.TestCase):
    def assert_gap(self, callback):
        with self.assertRaises(ExpressionGap) as caught:
            callback()
        self.assertTrue(caught.exception.code.endswith('_GAP'))

    def assert_log_two(self, enclosure):
        self.assertEqual(enclosure['schema'], 'bounded-real/1')
        low, high = [Fraction(int(enclosure[key]['numerator']), int(enclosure[key]['denominator']))
                     for key in ('lower', 'upper')]
        with localcontext() as context:
            context.prec = 100
            independent = Fraction(Decimal(2).ln()) * 10000
        self.assertLessEqual(low, independent)
        self.assertLessEqual(independent, high)
        self.assertLessEqual(high - low, Fraction(1, 10**12))

    def test_missing_decision_container_preserves_true_false_and_unknown_condition(self):
        for flag in (True, False, None):
            request, catalog, rows = example()
            rows[0]['features']['flag@1']['value'] = flag
            with self.subTest(flag=flag):
                report = materialize_required(request, catalog, without(rows, 900))
                self.assertEqual(report['schema'], 'required-input-bounded-reference-cases/1')
                case = report['cases'][1]
                self.assertEqual(case['status'], 'ELIGIBLE')
                self.assertIs(case['scope'], True)
                self.assertIs(case['condition'], flag)
                self.assert_log_two(case['outcome'])
                self.assertFalse(report['scientific_readiness'])

    def test_missing_anchor_does_not_hide_present_lagged_prices(self):
        request, catalog, rows = example()
        case = materialize_required(request, catalog, without(rows, 3600))['cases'][1]
        self.assertEqual(case['outcome_anchor'], 3600)
        self.assertEqual(case['status'], 'ELIGIBLE')
        self.assert_log_two(case['outcome'])
        self.assertEqual(case['trace']['earliest_observation'], 1800)
        self.assertEqual(case['trace']['latest_available_at'], 2700)
        self.assertFalse(case['trace']['unknown_input'])
        self.assertEqual(case['trace']['reasons'], [])
        self.assertEqual(case['label_information_interval'], {'start': 900, 'end': 3600})

    def test_two_absent_containers_are_not_fabricated_missing_dependencies(self):
        request, catalog, rows = example()
        selected = without(rows, 900, 3600)
        report = materialize_required(request, catalog, selected)
        self.assertEqual(report['cases'][1]['status'], 'ELIGIBLE')
        diagnostic = add_required_diagnostics(report, catalog, selected, 100000)
        case = diagnostic['cases'][1]
        self.assertEqual(case['diagnostics']['reason_categories'], [])
        self.assertFalse(any(event['reason'] == 'missing_observation'
                             for event in case['diagnostics']['events']))

    def test_unknown_condition_keeps_exact_observed_scope_denominator(self):
        request, catalog, rows = example()
        request['condition_program'] = program(boolean(None))
        report = materialize_required(request, catalog, without(rows, 900))
        contrast = required_contrast(report)
        self.assertEqual(contrast['schema'], 'required-input-bounded-reference-contrast/1')
        self.assertEqual((contrast['scope_count'], contrast['condition_count']), (4, 0))
        self.assertIsNone(contrast['effect'])
        self.assertFalse(contrast['scientific_readiness'])

    def test_absent_required_prices_remain_missing_without_nearest_substitution(self):
        for missing in (1800, 2700):
            request, catalog, rows = example()
            with self.subTest(missing=missing):
                case = materialize_required(request, catalog, without(rows, missing))['cases'][1]
                self.assertEqual(case['status'], 'OUTCOME_MISSING')
                self.assertIsNone(case['outcome'])
                self.assertIn('missing_observation', case['trace']['reasons'])

    def test_absent_required_signal_is_unknown_but_observed_outcome_stays_in_scope(self):
        request, catalog, rows = example()
        case = materialize_required(request, catalog, without(rows, 0))['cases'][1]
        self.assertEqual(case['status'], 'ELIGIBLE')
        self.assertIsNone(case['condition'])
        self.assert_log_two(case['outcome'])

    def test_lagged_complete_windows_use_exact_operand_times_and_never_skip(self):
        for operator in ('trailing_median', 'trailing_mean'):
            request, catalog, rows = example()
            window = {'op': operator, 'bars': 2, 'arg': lag(feature('x@1'), 1)}
            request['condition_program'] = program(binary('eq', window, literal('2')))
            with self.subTest(operator=operator, complete=True):
                case = materialize_required(request, catalog, without(rows, 1800))['cases'][2]
                self.assertEqual(case['status'], 'ELIGIBLE')
                self.assertIs(case['condition'], True)
            for missing in (0, 900):
                with self.subTest(operator=operator, missing=missing):
                    case = materialize_required(request, catalog, without(rows, 1800, missing))['cases'][2]
                    self.assertEqual(case['status'], 'ELIGIBLE')
                    self.assertIsNone(case['condition'])

    def test_actual_current_feature_still_requires_its_row_and_scope_precedes_outcome(self):
        request, catalog, rows = example()
        selected = without(rows, 900)
        request['scope_program'] = program(feature('flag@1'))
        case = materialize_required(request, catalog, selected)['cases'][1]
        self.assertEqual(case['status'], 'SCOPE_UNKNOWN')
        self.assertIsNone(case['outcome'])
        request['scope_program'] = program(boolean(False))
        case = materialize_required(request, catalog, selected)['cases'][1]
        self.assertEqual(case['status'], 'SCOPE_FALSE')
        self.assertIs(case['scope'], False)
        self.assertIsNone(case['trace'])

    def test_decision_cutoff_and_inherited_global_outcome_cutoff_remain_distinct(self):
        request, catalog, rows = example()
        rows[0]['features']['flag@1']['available_at'] = 901
        rows[3]['features']['close@1']['available_at'] = 3601
        case = materialize_required(request, catalog, without(rows, 900))['cases'][1]
        self.assertIsNone(case['condition'])
        self.assertEqual(case['status'], 'ELIGIBLE')
        self.assertEqual(case['label_information_interval']['end'], 3601)
        rows[3]['features']['close@1']['available_at'] = 7200
        case = materialize_required(request, catalog, without(rows, 900))['cases'][1]
        self.assertEqual(case['status'], 'OUTCOME_MISSING')
        self.assertIsNone(case['outcome'])
        self.assertIn('not_yet_available', case['trace']['reasons'])

    def test_future_anchor_and_exclusive_boundary_still_stop_outcome_reads(self):
        request, catalog, rows = example()
        report = materialize_required(request, catalog, rows)
        self.assertTrue(all(case['status'] == 'PARTITION_BOUNDARY' and case['trace'] is None
                            for case in report['cases'][5:]))
        request['as_of'] = '1970-01-01T00:15:00Z'
        report = materialize_required(request, catalog, without(rows, 900))
        self.assertEqual(report['cases'][1]['status'], 'OUTCOME_PENDING')
        self.assertIsNone(report['cases'][1]['outcome'])
        self.assertEqual(report['cases'][2]['status'], 'NOT_YET_OBSERVED')

    def test_three_valued_logic_and_literal_null_do_not_fabricate_raw_missing_values(self):
        for expression, expected in ((binary('and', boolean(False), boolean(None)), False),
                                     (binary('or', boolean(True), boolean(None)), True),
                                     (binary('and', boolean(True), boolean(None)), None)):
            request, catalog, rows = example()
            request['condition_program'] = program(expression)
            selected = without(rows, 900)
            with self.subTest(expected=expected):
                report = materialize_required(request, catalog, selected)
                self.assertIs(report['cases'][1]['condition'], expected)
                observed = add_required_diagnostics(report, catalog, selected, 100000)['cases'][1]
                self.assertNotIn('missing_value', observed['diagnostics']['reason_categories'])

    def test_domains_and_null_actual_prices_remain_missing(self):
        for ref, value, reason in (('open@1', '0', 'division_by_zero'),
                                   ('close@1', '0', 'log_domain'),
                                   ('close@1', None, 'missing_value')):
            request, catalog, rows = example()
            rows[2 if ref == 'open@1' else 3]['features'][ref]['value'] = value
            with self.subTest(ref=ref, value=value):
                case = materialize_required(request, catalog, rows)['cases'][1]
                self.assertEqual(case['status'], 'OUTCOME_MISSING')
                self.assertIsNone(case['outcome'])
                self.assertIn(reason, case['trace']['reasons'])

    def test_feature_free_outcome_is_an_explicit_capability_gap(self):
        request, catalog, rows = example()
        request['outcome_program'] = program(literal('7', 'basis_points'))
        self.assert_gap(lambda: materialize_required(request, catalog, rows))

    def test_resource_stops_keep_partial_status_and_diagnostic_base_projection(self):
        request, catalog, rows = example()
        request['max_steps'] = 1
        stopped = materialize_required(request, catalog, rows)
        self.assertEqual(stopped['status'], 'RESOURCE_STOP')
        self.assertFalse(stopped['processing_complete'])
        self.assertEqual(required_contrast(stopped)['status'], 'RESOURCE_STOP')
        request['max_steps'] = 100000
        base = materialize_required(request, catalog, without(rows, 900))
        diagnostic = add_required_diagnostics(base, catalog, without(rows, 900), 0)
        self.assertEqual(diagnostic['diagnostics']['status'], 'RESOURCE_STOP')
        self.assertFalse(diagnostic['diagnostics']['processing_complete'])
        self.assertEqual(diagnostic['diagnostics']['processed_cases'], 0)
        self.assertTrue(all(case['diagnostics'] is None for case in diagnostic['cases']))
        self.assert_projection(diagnostic, base)

    def assert_projection(self, diagnostic, base):
        self.assertEqual(diagnostic['schema'], 'diagnostic-required-input-bounded-reference-cases/1')
        self.assertEqual(diagnostic['diagnostics']['schema'], 'case-diagnostics/2')
        checksum = stream_hash(base['cases'])
        self.assertEqual(diagnostic['base_case_stream_sha256'], checksum)
        self.assertEqual(diagnostic['base_report_hash'], digest({
            'report': {key: value for key, value in base.items() if key != 'cases'},
            'case_stream_sha256': checksum}))
        restored = {key: deepcopy(value) for key, value in diagnostic.items()
                    if key not in ('diagnostics', 'base_report_hash', 'base_case_stream_sha256')}
        restored['schema'] = 'required-input-bounded-reference-cases/1'
        restored['cases'] = [{key: value for key, value in case.items() if key != 'diagnostics'}
                             for case in restored['cases']]
        self.assertEqual(restored, base)

    def test_complete_diagnostics_are_versioned_immutable_and_source_bound(self):
        request, catalog, rows = example()
        selected = without(rows, 900)
        original = deepcopy((request, catalog, selected))
        base = materialize_required(request, catalog, selected)
        saved = deepcopy(base)
        observed = add_required_diagnostics(base, catalog, selected, 100000)
        self.assertEqual(observed['diagnostics']['status'], 'COMPLETE')
        self.assertEqual(observed['diagnostics']['processed_cases'], 8)
        self.assert_projection(observed, base)
        self.assertEqual((request, catalog, selected), original)
        self.assertEqual(base, saved)
        changed = deepcopy(selected)
        next(row for row in changed if row['time'] == 2700)['features']['close@1']['value'] = '300'
        self.assert_gap(lambda: add_required_diagnostics(base, catalog, changed, 100000))

    def test_legacy_profile_results_and_schema_admission_remain_separate(self):
        request, catalog, rows = example()
        selected = without(rows, 900, 3600)
        legacy = materialize_bounded(request, catalog, selected)
        old_bytes = canonical(legacy)
        self.assertEqual(legacy['cases'][1]['status'], 'DATA_GAP')
        self.assertEqual(legacy['cases'][1]['reason'], 'missing_decision_observation')
        updated = materialize_required(request, catalog, selected)
        self.assertEqual(updated['cases'][1]['status'], 'ELIGIBLE')
        self.assertEqual(canonical(materialize_bounded(request, catalog, selected)), old_bytes)
        self.assert_gap(lambda: bounded_contrast(updated))
        self.assert_gap(lambda: reference_contrast(updated))
        self.assert_gap(lambda: required_contrast(legacy))
        self.assert_gap(lambda: add_required_diagnostics(legacy, catalog, selected, 100000))


if __name__ == '__main__':
    unittest.main()
