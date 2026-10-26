"""Reference outcomes: fixed independent expectations and temporal invariants."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from trading_researcher.codec import digest
from trading_researcher.expressions import ExpressionGap
from trading_researcher.outcomes import materialize_reference, reference_contrast


FIXTURES = Path(__file__).parent / 'fixtures/reference_outcome_cases.json'


class OutcomeTests(unittest.TestCase):
    def test_independent_golden_cases(self):
        raw = FIXTURES.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'e36ee6997ef7fb9f09e11156d4ed3d3c44ab6faea9caa7a7db44ea7c9f2e5817')
        bundle = json.loads(raw)
        self.assertEqual(bundle['schema'], 'reference-outcome-cases/1')
        self.assertGreaterEqual(len(bundle['cases']), 12)
        for case in bundle['cases']:
            with self.subTest(case=case['name']):
                original = copy.deepcopy(case)
                result = materialize_reference(case['request'], case['catalog'], case['rows'])
                contrast = reference_contrast(result)
                expected = case['expected']
                self.assertEqual([x['status'] for x in result['cases']], expected['case_states'])
                self.assertEqual([x['outcome'] for x in result['cases']], expected['outcome_values'])
                self.assertEqual(contrast['effect'], expected['effect'])
                self.assertEqual(contrast['scope_count'], expected['scope_count'])
                self.assertEqual(contrast['condition_count'], expected['condition_count'])
                self.assertFalse(result['scientific_readiness'])
                self.assertFalse(contrast['scientific_readiness'])
                self.assertEqual(case, original)

    @staticmethod
    def example():
        catalog = {'price@1': {'type': 'real', 'unit': 'USD'}}
        def program(node):
            return {'schema': 'research-ast/1', 'catalog_hash': digest(catalog), 'expression': node}
        yes = program({'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True})
        request = {
            'schema': 'reference-case-request/1', 'candidate_ref': 'example-candidate',
            'data_snapshot_ref': 'example-snapshot', 'scope_program': yes,
            'condition_program': copy.deepcopy(yes),
            'outcome_program': program({'op': 'feature', 'ref': 'price@1'}),
            'outcome_scale': 'quantity', 'horizon_bars': 1,
            'universe': {'start': '1970-01-01T00:00:00Z', 'end': '1970-01-01T00:45:00Z',
                         'instruments': ['A']},
            'as_of': '1970-01-01T00:45:00Z', 'max_steps': 1000,
        }
        rows = [{'time': t, 'instrument': 'A',
                 'features': {'price@1': {'value': str(10 + t // 900), 'available_at': t}}}
                for t in (0, 900, 1800)]
        return request, catalog, rows

    def test_future_data_cannot_change_decision_scope(self):
        request, catalog, rows = self.example()
        request['scope_program']['expression'] = {
            'op': 'gt', 'left': {'op': 'feature', 'ref': 'price@1'},
            'right': {'op': 'literal', 'type': 'real', 'unit': 'USD', 'value': '5'}}
        rows[0]['features']['price@1']['available_at'] = 900
        first = materialize_reference(request, catalog, rows)
        rows[0]['features']['price@1']['value'] = '0'
        second = materialize_reference(request, catalog, rows)
        self.assertEqual(first, second)
        self.assertEqual(first['cases'][0]['status'], 'SCOPE_UNKNOWN')

    def test_unrelated_instrument_and_later_rows_cannot_change_cases(self):
        request, catalog, rows = self.example()
        first = materialize_reference(request, catalog, rows)
        rows.extend([{'time': 2700, 'instrument': 'A', 'features': {}},
                     {'time': 2700, 'instrument': 'B', 'features': {}}])
        self.assertEqual(materialize_reference(request, catalog, rows), first)

    def test_request_boundaries_and_no_silent_coercion(self):
        request, catalog, rows = self.example()
        mutations = [
            ('horizon_bars', True), ('horizon_bars', 0), ('horizon_bars', -1),
            ('max_steps', 0), ('max_steps', 10000001), ('as_of', '1970-01-01'),
            ('candidate_ref', []), ('outcome_scale', 'arbitrary'), ('extra', 'ignored'),
        ]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(request)
                changed[field] = value
                with self.assertRaises(ExpressionGap):
                    materialize_reference(changed, catalog, rows)
        request['universe']['end'] = '2020-01-01T00:00:00Z'
        with self.assertRaises(ExpressionGap) as error:
            materialize_reference(request, catalog, rows)
        self.assertEqual(error.exception.code, 'RESOURCE_GAP')

    def test_type_and_catalog_boundaries_are_enforced(self):
        request, catalog, rows = self.example()
        request['outcome_scale'] = 'binary_probability'
        with self.assertRaises(ExpressionGap) as error:
            materialize_reference(request, catalog, rows)
        self.assertEqual(error.exception.code, 'TYPE_GAP')
        request['outcome_scale'] = 'quantity'
        request['condition_program']['catalog_hash'] = 'substitution'
        with self.assertRaises(ExpressionGap) as error:
            materialize_reference(request, catalog, rows)
        self.assertEqual(error.exception.code, 'FEATURE_GAP')

    def test_contrast_rejects_duplicate_missing_cases_and_malformed_values(self):
        request, catalog, rows = self.example()
        report = materialize_reference(request, catalog, rows)
        duplicate = copy.deepcopy(report)
        duplicate['cases'][1] = copy.deepcopy(duplicate['cases'][0])
        with self.assertRaises(ExpressionGap):
            reference_contrast(duplicate)
        truncated = copy.deepcopy(report)
        truncated['cases'].pop()
        with self.assertRaises(ExpressionGap):
            reference_contrast(truncated)
        truncated['expected_case_count'] -= 1
        with self.assertRaises(ExpressionGap):
            reference_contrast(truncated)
        for numerator, denominator in [('1', '0'), ('2', '2'), ('01', '1'),
                                       ('-0', '1'), (True, '1'), ('9' * 2469, '1')]:
            with self.subTest(numerator=str(numerator)[:12], denominator=denominator):
                malformed = copy.deepcopy(report)
                malformed['cases'][0]['outcome'] = {'numerator': numerator, 'denominator': denominator}
                with self.assertRaises(ExpressionGap):
                    reference_contrast(malformed)

    def test_contrast_retains_numeric_resource_stop_without_partial_effect(self):
        request, catalog, rows = self.example()
        report = materialize_reference(request, catalog, rows)
        report['cases'][0]['outcome'] = {'numerator': '1', 'denominator': str(2 ** 8191)}
        report['cases'][1]['outcome'] = {'numerator': '1', 'denominator': str(3 ** 5168)}
        result = reference_contrast(report)
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertIsNone(result['effect'])
        self.assertIsNone(result['scope_count'])

    def test_cancellation_cannot_hide_an_oversized_final_contrast(self):
        request, catalog, rows = self.example()
        request['universe']['end'] = '1970-01-01T01:00:00Z'
        request['as_of'] = '1970-01-01T01:00:00Z'
        rows.append({'time': 2700, 'instrument': 'A',
                     'features': {'price@1': {'value': '13', 'available_at': 2700}}})
        report = materialize_reference(request, catalog, rows)
        p, q = 2 ** 8190 - 1, 2 ** 8190 + 1
        for case, numerator, denominator, condition in zip(
                report['cases'], ['1', '-1', '1'], [p, p, q], [True, False, False]):
            case['outcome'] = {'numerator': numerator, 'denominator': str(denominator)}
            case['condition'] = condition
        result = reference_contrast(report)
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertEqual(result['reason'], 'exact_contrast_exceeds_numeric_envelope')
        self.assertIsNone(result['effect'])

    def test_changed_status_cannot_conceal_review_trace_or_pending_metadata(self):
        bundle = json.loads(FIXTURES.read_bytes())
        case = next(case for case in bundle['cases']
                    if case['name'] == 'determinate_true_with_missing_operand_requires_review')
        report = materialize_reference(case['request'], case['catalog'], case['rows'])
        report['cases'][0]['status'] = 'ELIGIBLE'
        with self.assertRaises(ExpressionGap):
            reference_contrast(report)
        report['state_counts']['REVIEW_REQUIRED'] -= 1
        report['state_counts']['ELIGIBLE'] += 1
        report['review_required'] = False
        with self.assertRaises(ExpressionGap):
            reference_contrast(report)
        request, catalog, rows = self.example()
        report = materialize_reference(request, catalog, rows)
        report['cases'][0]['label_information_interval']['end'] += 900
        with self.assertRaises(ExpressionGap):
            reference_contrast(report)

    def test_missing_window_member_cannot_hide_declared_partition_crossing(self):
        request, catalog, _ = self.example()
        request['universe'].update(start='1970-01-01T00:15:00Z', end='1970-01-01T01:30:00Z')
        request['as_of'] = '1970-01-01T01:45:00Z'
        request['outcome_program']['expression'] = {
            'op': 'trailing_mean', 'bars': 3, 'arg': {'op': 'feature', 'ref': 'price@1'}}
        rows = [{'time': index * 900, 'instrument': 'A',
                 'features': {'price@1': {'value': value, 'available_at': index * 900}}}
                for index, value in enumerate(['1', '2', None, '4', '6', '8'])]
        report = materialize_reference(request, catalog, rows)
        self.assertEqual(report['cases'][0]['status'], 'REVIEW_REQUIRED')
        self.assertEqual(report['cases'][0]['trace']['declared_earliest_observation'], 0)
        self.assertIsNone(reference_contrast(report)['effect'])

    def test_binary_reports_cannot_contain_outcomes_outside_zero_and_one(self):
        bundle = json.loads(FIXTURES.read_bytes())
        case = next(case for case in bundle['cases']
                    if case['name'] == 'binary_whole_scope_probability_contrast')
        report = materialize_reference(case['request'], case['catalog'], case['rows'])
        self.assertEqual(report['outcome_unit'], 'ratio')
        report['cases'][0]['outcome'] = {'numerator': '2', 'denominator': '1'}
        with self.assertRaises(ExpressionGap):
            reference_contrast(report)

    def test_missing_window_member_cannot_hide_late_predecision_publication(self):
        request, catalog, _ = self.example()
        catalog['in_scope@1'] = {'type': 'boolean', 'unit': None}
        for name in ('scope_program', 'condition_program', 'outcome_program'):
            request[name]['catalog_hash'] = digest(catalog)
        request['scope_program']['expression'] = {'op': 'feature', 'ref': 'in_scope@1'}
        request['outcome_program']['expression'] = {
            'op': 'trailing_mean', 'bars': 3, 'arg': {'op': 'feature', 'ref': 'price@1'}}
        request['universe']['end'] = '1970-01-01T01:30:00Z'
        request['as_of'] = '1970-01-01T01:45:00Z'
        rows = [{'time': index * 900, 'instrument': 'A', 'features': {
                    'price@1': {'value': value, 'available_at': 1800 if index == 0 else index * 900},
                    'in_scope@1': {'value': index != 0, 'available_at': index * 900}}}
                for index, value in enumerate(['7', '2', None, '4', '6', '8'])]
        report = materialize_reference(request, catalog, rows)
        self.assertEqual(report['cases'][0]['status'], 'SCOPE_FALSE')
        self.assertEqual(report['cases'][1]['status'], 'REVIEW_REQUIRED')
        self.assertTrue(report['cases'][1]['trace']['predecision_input_published_late'])
        self.assertIsNone(reference_contrast(report)['effect'])


if __name__ == '__main__':
    unittest.main()
