"""Independent additive diagnostic expectations; no research/validity authority.

All data are invented, and expectations are fixed separately from the observer
implementation. Original case projections and estimands must remain unchanged.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import unittest

from trading_researcher.bounded_outcomes import materialize_bounded
from trading_researcher.case_diagnostics import add_diagnostics
from trading_researcher.codec import Invalid, canonical, digest


CATALOG = {'x@1': {'type': 'real', 'unit': 'ratio'},
           'c@1': {'type': 'boolean', 'unit': None}}


def boolean(value):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def number(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': value}


def feature(ref='x@1'):
    return {'op': 'feature', 'ref': ref}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def guard(validity, predicate):
    return binary('or', binary('and', deepcopy(validity), predicate),
                  binary('and', {'op': 'not', 'arg': deepcopy(validity)}, boolean(None)))


def program(expression):
    return {'schema': 'research-ast/2', 'catalog_hash': digest(CATALOG), 'expression': expression}


def example(condition=None, outcome=None, count=4):
    end = datetime.fromtimestamp(count * 900, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    request = {
        'schema': 'bounded-reference-case-request/1', 'candidate_ref': 'synthetic-diagnostic-candidate',
        'data_snapshot_ref': 'synthetic-diagnostic-snapshot', 'scope_program': program(boolean(True)),
        'condition_program': program(feature('c@1') if condition is None else condition),
        'outcome_program': program(binary('mul', number('10000', 'basis_points'),
                                         {'op': 'ln', 'arg': feature()}) if outcome is None else outcome),
        'outcome_scale': 'quantity', 'horizon_bars': 1,
        'universe': {'start': '1970-01-01T00:00:00Z', 'end': end, 'instruments': ['A']},
        'as_of': end, 'max_steps': 1000000,
    }
    rows = [{'time': index * 900, 'instrument': 'A', 'features': {
                'x@1': {'value': '1', 'available_at': index * 900},
                'c@1': {'value': (True, False, None, True)[index % 4], 'available_at': index * 900}}}
            for index in range(count)]
    return request, deepcopy(CATALOG), rows


def case_hash(cases):
    checksum = hashlib.sha256()
    for case in cases:
        checksum.update((canonical(case) + '\n').encode('utf-8'))
    return checksum.hexdigest()


class CaseDiagnosticTests(unittest.TestCase):
    def calculate(self, request, catalog, rows, max_steps=1000000):
        base = materialize_bounded(request, catalog, rows)
        original = deepcopy((base, catalog, rows))
        result = add_diagnostics(base, catalog, rows, max_steps)
        self.assertEqual((base, catalog, rows), original)
        self.assert_base_projection(result, base)
        return base, result

    def assert_base_projection(self, result, base):
        self.assertEqual(result['schema'], 'diagnostic-bounded-reference-cases/1')
        stream_hash = case_hash(base['cases'])
        metadata = {key: value for key, value in base.items() if key != 'cases'}
        self.assertEqual(result['base_case_stream_sha256'], stream_hash)
        self.assertEqual(result['base_report_hash'], digest({'report': metadata, 'case_stream_sha256': stream_hash}))
        projected = {key: deepcopy(value) for key, value in result.items()
                     if key not in ('diagnostics', 'base_report_hash', 'base_case_stream_sha256')}
        projected['schema'] = 'bounded-reference-cases/1'
        projected['cases'] = [{key: value for key, value in case.items() if key != 'diagnostics'}
                              for case in projected['cases']]
        self.assertEqual(projected, base)
        self.assertEqual(case_hash(projected['cases']), stream_hash)
        self.assertFalse(result['scientific_readiness'])

    def assert_categories(self, case, required=(), absent=()):
        categories = case['diagnostics']['reason_categories']
        self.assertEqual(categories, sorted(set(categories)))
        for reason in required:
            self.assertIn(reason, categories)
        for reason in absent:
            self.assertNotIn(reason, categories)
        events = case['diagnostics']['events']
        self.assertEqual(len(events), len({canonical(event) for event in events}))
        for event in events:
            self.assertEqual(set(event), {'program', 'path', 'observation_time', 'available_at', 'reason'})
            self.assertIn(event['program'], ('scope_program', 'condition_program', 'outcome_program'))
            self.assertTrue(event['path'].startswith('/expression'))

    def test_literal_unknown_event_does_not_turn_valid_rows_into_missing_inputs(self):
        request, catalog, rows = example(guard(boolean(True), feature('c@1')))
        base, result = self.calculate(request, catalog, rows)
        summary = result['diagnostics']
        self.assertEqual(summary['schema'], 'case-diagnostics/1')
        self.assertEqual(summary['status'], 'COMPLETE')
        self.assertTrue(summary['processing_complete'])
        self.assertEqual((summary['expected_cases'], summary['processed_cases']), (4, 4))
        self.assertEqual(summary['guard_counts']['true'], 4)
        for index in (0, 1):
            case = result['cases'][index]
            self.assert_categories(case, absent=('missing_value', 'condition_unknown', 'numeric_domain'))
            self.assertEqual(case['condition'], index == 0)
            self.assertEqual(case['diagnostics']['validity_guard'],
                             {'recognized': True, 'path': '/expression/left/left', 'value': True, 'evaluated': True})
            self.assertTrue(any(event['reason'] == 'missing_value' and
                                event['path'] == '/expression/right/right'
                                for event in case['diagnostics']['events']))
        self.assert_categories(result['cases'][2], required=('missing_value', 'condition_unknown'))
        self.assertEqual(summary['reason_counts'].get('missing_value', 0), 1)
        self.assertEqual(add_diagnostics(base, catalog, rows, 1000000), result)

    def test_guard_false_is_neutral_and_structural_identity_is_required(self):
        request, catalog, rows = example(guard(boolean(False), boolean(True)))
        _, result = self.calculate(request, catalog, rows)
        self.assertEqual(result['diagnostics']['guard_counts']['false'], 4)
        for case in result['cases']:
            self.assert_categories(case, required=('condition_unknown',), absent=('missing_value', 'numeric_domain'))
            self.assertIs(case['diagnostics']['validity_guard']['value'], False)
            self.assertNotIn('invalid_condition', case['diagnostics'])
            self.assertFalse(any('invalid' in reason for reason in case['diagnostics']['reason_categories']))
        expression = guard(boolean(True), boolean(True))
        expression['right']['left']['arg'] = boolean(False)
        request, catalog, rows = example(expression)
        _, result = self.calculate(request, catalog, rows)
        self.assertEqual(result['diagnostics']['guard_counts']['unrecognized'], 4)
        self.assertTrue(all(case['diagnostics']['validity_guard']['recognized'] is False
                            for case in result['cases']))

    def test_outer_lag_and_missing_decision_distinguish_unknown_from_not_evaluated(self):
        expression = {'op': 'lag', 'bars': 1, 'arg': guard(feature('c@1'), boolean(True))}
        request, catalog, rows = example(expression)
        _, result = self.calculate(request, catalog, rows)
        self.assert_categories(result['cases'][0], required=('missing_warmup', 'input_before_universe', 'condition_unknown'),
                               absent=('absent_row',))
        self.assertEqual(result['cases'][1]['diagnostics']['validity_guard'],
                         {'recognized': True, 'path': '/expression/arg/left/left', 'value': True, 'evaluated': True})
        request, catalog, rows = example(guard(boolean(True), boolean(True)))
        rows.pop(0)
        _, result = self.calculate(request, catalog, rows)
        self.assert_categories(result['cases'][0], required=('absent_row',))
        item = result['cases'][0]['diagnostics']['validity_guard']
        self.assertTrue(item['recognized'])
        self.assertFalse(item['evaluated'])
        self.assertIsNone(item['value'])
        self.assertEqual(result['diagnostics']['guard_counts']['not_evaluated'], 1)

    def test_feature_null_absence_and_delay_have_distinct_source_causes(self):
        expression = binary('gt', feature(), number('0'))
        for mode, required, absent in [
                ('null', 'missing_value', 'missing_feature'),
                ('absent', 'missing_feature', 'missing_value'),
                ('late', 'unavailable_data', 'missing_value')]:
            with self.subTest(mode=mode):
                request, catalog, rows = example(expression)
                if mode == 'null':
                    rows[0]['features']['x@1']['value'] = None
                elif mode == 'absent':
                    rows[0]['features'].pop('x@1')
                else:
                    rows[0]['features']['x@1']['available_at'] = 1
                    rows[0]['features']['x@1']['value'] = '0'
                _, result = self.calculate(request, catalog, rows)
                self.assert_categories(result['cases'][0], required=(required, 'condition_unknown'), absent=(absent,))
                if mode == 'late':
                    rows[0]['features']['x@1']['value'] = '999999'
                    _, changed = self.calculate(request, catalog, rows)
                    self.assertEqual(changed, result)

    def test_numeric_domains_and_in_universe_missing_rows_are_not_warmup(self):
        condition = binary('gt', binary('div', feature(), number('0')), number('0'))
        request, catalog, rows = example(condition)
        _, result = self.calculate(request, catalog, rows)
        self.assert_categories(result['cases'][0], required=('numeric_domain', 'condition_unknown'),
                               absent=('missing_value', 'missing_warmup'))
        request, catalog, rows = example()
        rows[1]['features']['x@1']['value'] = '0'
        _, result = self.calculate(request, catalog, rows)
        self.assert_categories(result['cases'][0], required=('numeric_domain',))
        condition = {'op': 'lag', 'bars': 1, 'arg': binary('gt', feature(), number('0'))}
        request, catalog, rows = example(condition)
        rows.pop(1)
        _, result = self.calculate(request, catalog, rows)
        self.assert_categories(result['cases'][2], required=('absent_row', 'condition_unknown'), absent=('missing_warmup',))

    def test_boundary_and_future_cases_do_not_trigger_outcome_reads(self):
        request, catalog, rows = example()
        _, result = self.calculate(request, catalog, rows)
        last = result['cases'][-1]
        self.assert_categories(last, required=('boundary_censoring',))
        self.assertFalse(any(event['program'] == 'outcome_program' for event in last['diagnostics']['events']))
        request['as_of'] = '1970-01-01T00:15:00Z'
        _, result = self.calculate(request, catalog, rows)
        for case in result['cases'][2:]:
            self.assertEqual(case['status'], 'NOT_YET_OBSERVED')
            self.assertEqual(case['diagnostics']['events'], [])
            self.assertFalse(case['diagnostics']['validity_guard']['evaluated'])

    def test_separate_diagnostic_budget_retains_base_result_and_partial_status(self):
        request, catalog, rows = example(guard(boolean(True), feature('c@1')))
        _, result = self.calculate(request, catalog, rows, max_steps=1)
        summary = result['diagnostics']
        self.assertEqual(summary['status'], 'RESOURCE_STOP')
        self.assertFalse(summary['processing_complete'])
        self.assertEqual(summary['expected_cases'], 4)
        self.assertEqual(summary['processed_cases'], 0)
        self.assertEqual(summary['primitive_steps'], 1)
        self.assertTrue(all(case['diagnostics'] is None for case in result['cases']))
        self.assertEqual(result['status'], 'PROCESSED')
        self.assertTrue(result['processing_complete'])
        self.assertTrue(all(value == 0 for value in summary['reason_counts'].values()))

    def test_different_source_values_cannot_diagnose_an_unchanged_base_report(self):
        request, catalog, rows = example()
        base = materialize_bounded(request, catalog, rows)
        for field, index, value in [('c@1', 0, False), ('x@1', 1, '2')]:
            with self.subTest(field=field):
                changed = deepcopy(rows)
                changed[index]['features'][field]['value'] = value
                with self.assertRaises(Invalid):
                    add_diagnostics(base, catalog, changed, 1000000)
        with self.subTest(removed_decision_row=True):
            with self.assertRaises(Invalid):
                add_diagnostics(base, catalog, rows[1:], 1000000)

    def test_stream_projection_hash_supports_reports_larger_than_one_mib(self):
        request, catalog, rows = example(boolean(True), number('0', 'basis_points'), count=2200)
        base, result = self.calculate(request, catalog, rows)
        with self.assertRaises(Invalid):
            canonical(base)
        self.assertEqual(result['diagnostics']['status'], 'COMPLETE')
        self.assertEqual(result['diagnostics']['processed_cases'], 2200)


if __name__ == '__main__':
    unittest.main()
