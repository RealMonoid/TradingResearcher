"""Independent exact shifted-value scope oracles, not process-adequacy tests."""
from copy import deepcopy
from datetime import datetime, timezone
import importlib
import unittest

from trading_researcher.codec import Invalid, digest
from trading_researcher.outcomes import materialize_reference, reference_contrast


def instant(index):
    return datetime.fromtimestamp(index * 900, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def feature(name='up@1'):
    return {'op':'feature', 'ref':name}


def lag(node, bars):
    return deepcopy(node) if bars == 0 else {'op':'lag', 'arg':deepcopy(node), 'bars':bars}


def literal(value, kind='boolean', unit=None):
    return {'op':'literal', 'type':kind, 'unit':unit, 'value':value}


def fixture(*, condition_lag=1, outcome_lag=0, horizon=1, instruments=('A',),
            missing_rows=(), condition=None, outcome=None):
    """Eight target instants plus explicit warmup; opposite instrument paths."""
    catalog = {'up@1':{'type':'boolean', 'unit':None},
        'close@1':{'type':'real', 'unit':'USD'}, 'open@1':{'type':'real', 'unit':'USD'}}
    def program(expression):
        return {'schema':'research-ast/1', 'catalog_hash':digest(catalog), 'expression':deepcopy(expression)}
    request = {'schema':'reference-case-request/1', 'candidate_ref':'independent-scope-fixture',
        'data_snapshot_ref':'synthetic-raw-feature-fixture', 'scope_program':program(literal(True)),
        'condition_program':program(lag(feature(), condition_lag) if condition is None else condition),
        'outcome_program':program(lag(feature(), outcome_lag) if outcome is None else outcome),
        'outcome_scale':'binary_probability', 'horizon_bars':horizon,
        'universe':{'start':instant(4), 'end':instant(12), 'instruments':list(instruments)},
        'as_of':instant(13), 'max_steps':100000}
    pattern = (False, True, True, False, True, False, False, True, False, True, True, False)
    rows = []
    for index in range(12):
        for symbol in instruments:
            if (index, symbol) in missing_rows:continue
            value = pattern[index] if symbol == 'A' else not pattern[index]
            rows.append({'time':index * 900, 'instrument':symbol, 'features':{
                'up@1':{'value':value, 'available_at':index * 900},
                'close@1':{'value':'2' if value else '0', 'available_at':index * 900},
                'open@1':{'value':'1', 'available_at':index * 900}}})
    return materialize_reference(request, catalog, rows)


class SourceProcessScopeAdversarialTests(unittest.TestCase):
    def diagnose(self, report):
        # An absent implementation fails each proposed behavior explicitly.
        module = importlib.import_module('trading_researcher.source_process_scope')
        return module.diagnose_source_process(report)

    def assert_counts(self, result, **expected):
        counts = result['observations']
        self.assertEqual({key:counts[key] for key in expected}, expected)
        self.assertEqual(counts['target_rows'], sum(counts[key] for key in (
            'partner_absent', 'both_unobserved', 'condition_unobserved', 'outcome_unobserved', 'compared')))
        self.assertEqual(counts['compared'], counts['equal'] + counts['unequal'])

    def test_two_instruments_match_exact_timestamps_and_include_observed_terminal_conditions(self):
        report = fixture(instruments=('A', 'B')); before = deepcopy(report)
        result = self.diagnose(report)
        self.assertEqual(result['schema'], 'source-process-scope/1')
        self.assertEqual(result['source_request_hash'], digest(report['request']))
        self.assertEqual(result['status'], 'SHIFTED_VALUE_IDENTITY')
        self.assertEqual(result['identity']['condition_equals_outcome_at_offset_bars'], -2)
        self.assert_counts(result, target_rows=16, partner_absent=4, both_unobserved=0,
            condition_unobserved=0, outcome_unobserved=0, compared=12, equal=12, unequal=0,
            both_eligible_compared=10)
        self.assertEqual(result['original_process_adequacy'], 'NOT_ASSESSED')
        self.assertFalse(result['scientific_readiness']); self.assertFalse(result['classification_permitted'])
        self.assertEqual(report, before)

    def test_positive_offset_remains_descriptive_with_valid_review_gap_at_first_outcome(self):
        report = fixture(condition_lag=0, outcome_lag=2)
        self.assertTrue(report['review_required'])
        self.assertEqual(reference_contrast(report)['status'], 'INFORMATION_GAP')
        self.assertEqual(reference_contrast(report)['reason'], 'dependency_review_required')
        result = self.diagnose(report)
        self.assertEqual(result['status'], 'SHIFTED_VALUE_IDENTITY')
        self.assertEqual(result['identity']['condition_equals_outcome_at_offset_bars'], 1)
        self.assert_counts(result, target_rows=8, partner_absent=1, both_unobserved=0,
            condition_unobserved=0, outcome_unobserved=1, compared=6, equal=6, unequal=0,
            both_eligible_compared=5)

    def test_zero_offset_is_not_confused_with_no_identified_shift(self):
        result = self.diagnose(fixture(condition_lag=0, outcome_lag=1))
        self.assertEqual(result['status'], 'SHIFTED_VALUE_IDENTITY')
        self.assertEqual(result['identity']['condition_equals_outcome_at_offset_bars'], 0)
        self.assert_counts(result, target_rows=8, partner_absent=0, both_unobserved=0,
            condition_unobserved=0, outcome_unobserved=1, compared=7, equal=7, unequal=0,
            both_eligible_compared=7)

    def test_horizon_and_condition_lookback_both_contribute_with_negative_sign(self):
        result = self.diagnose(fixture(condition_lag=2, horizon=3))
        self.assertEqual(result['identity']['condition_equals_outcome_at_offset_bars'], -5)
        self.assert_counts(result, target_rows=8, partner_absent=5, both_unobserved=0,
            condition_unobserved=0, outcome_unobserved=0, compared=3, equal=3, unequal=0,
            both_eligible_compared=0)

    def test_missing_current_intermediate_and_partner_rows_have_exclusive_buckets(self):
        # Removing row7 affects target7's condition, both values at target8,
        # and target9's earlier outcome through three different execution gates.
        result = self.diagnose(fixture(missing_rows={(7, 'A')}))
        self.assertEqual(result['identity']['condition_equals_outcome_at_offset_bars'], -2)
        self.assert_counts(result, target_rows=8, partner_absent=2, both_unobserved=1,
            condition_unobserved=1, outcome_unobserved=1, compared=3, equal=3, unequal=0,
            both_eligible_compared=1)

    def test_featurewise_and_whole_expression_lags_match_only_values_not_missingness(self):
        compare = {'op':'gt', 'left':feature('close@1'), 'right':feature('open@1')}
        condition = {'op':'gt', 'left':lag(feature('close@1'), 1), 'right':lag(feature('open@1'), 1)}
        result = self.diagnose(fixture(condition=condition, outcome=compare, missing_rows={(7, 'A')}))
        self.assertEqual(result['status'], 'SHIFTED_VALUE_IDENTITY')
        self.assertEqual(result['identity']['condition_equals_outcome_at_offset_bars'], -2)
        self.assert_counts(result, target_rows=8, partner_absent=2, both_unobserved=1,
            condition_unobserved=1, outcome_unobserved=1, compared=3, equal=3, unequal=0,
            both_eligible_compared=1)

    def test_exact_not_and_nested_lags_preserve_signed_value_identity(self):
        condition = {'op':'not', 'arg':lag(lag(feature(), 1), 1)}
        outcome = {'op':'not', 'arg':feature()}
        result = self.diagnose(fixture(condition=condition, outcome=outcome))
        self.assertEqual(result['identity']['condition_equals_outcome_at_offset_bars'], -3)
        self.assertEqual(result['observations']['equal'], 5)

    def test_nonuniform_feature_shifts_are_not_a_single_time_translation(self):
        condition = {'op':'gt', 'left':lag(feature('close@1'), 1), 'right':lag(feature('open@1'), 2)}
        outcome = {'op':'gt', 'left':feature('close@1'), 'right':feature('open@1')}
        result = self.diagnose(fixture(condition=condition, outcome=outcome))
        self.assertEqual(result['status'], 'NOT_ASSESSED')

    def test_no_catalog_alias_operator_or_commutation_equivalence_is_invented(self):
        condition = {'op':'gt', 'left':lag(feature('close@1'), 1), 'right':lag(feature('open@1'), 1)}
        outcome = {'op':'gt', 'left':feature('close@1'), 'right':feature('open@1')}
        original = fixture(condition=condition, outcome=outcome)
        for kind in ('catalog', 'version', 'weak_operator', 'equivalent_swapped_operands'):
            report = deepcopy(original); program = report['request']['outcome_program']; node = program['expression']
            if kind == 'catalog':program['catalog_hash'] = 'a' * 64
            elif kind == 'version':node['left']['ref'] = 'close@2'
            elif kind == 'weak_operator':node['op'] = 'ge'
            else:node['op'] = 'lt'; node['left'], node['right'] = node['right'], node['left']
            with self.subTest(kind=kind):self.assertEqual(self.diagnose(report)['status'], 'NOT_ASSESSED')

    def test_literal_values_units_and_decimal_spellings_remain_exact(self):
        condition = {'op':'gt', 'left':lag(feature('close@1'), 1),
            'right':literal('1', 'real', 'USD')}
        outcome = {'op':'gt', 'left':feature('close@1'), 'right':literal('1', 'real', 'USD')}
        original = fixture(condition=condition, outcome=outcome)
        self.assertEqual(self.diagnose(original)['status'], 'SHIFTED_VALUE_IDENTITY')
        for field, value in (('value', '1.0'), ('value', '2'), ('unit', 'EUR')):
            changed = deepcopy(original)
            changed['request']['outcome_program']['expression']['right'][field] = value
            with self.subTest(field=field, value=value):
                self.assertEqual(self.diagnose(changed)['status'], 'NOT_ASSESSED')

    def test_constant_only_and_unsupported_window_have_no_generic_independence_claim(self):
        constant = self.diagnose(fixture(condition=literal(True), outcome=literal(True)))
        self.assertEqual(constant['status'], 'NOT_ASSESSED')
        average = {'op':'trailing_mean', 'bars':2, 'arg':feature('close@1')}
        compare = {'op':'gt', 'left':average, 'right':literal('1', 'real', 'USD')}
        window = self.diagnose(fixture(condition=lag(compare, 1), outcome=compare))
        self.assertEqual(window['status'], 'NOT_ASSESSED')
        self.assertEqual(window['original_process_adequacy'], 'NOT_ASSESSED')

    def test_structurally_valid_observed_mismatch_is_retained_not_forced_equal(self):
        report = fixture(); old = report['cases'][3]['outcome']
        report['cases'][3]['outcome'] = {'numerator':'0' if old['numerator'] == '1' else '1', 'denominator':'1'}
        reference_contrast(report)  # Valid case structure is not data authenticity.
        result = self.diagnose(report)
        self.assertEqual(result['status'], 'SHIFTED_VALUE_IDENTITY')
        self.assertEqual(result['observations']['unequal'], 1)
        self.assertEqual(result['observations']['equal'], 5)
        self.assertEqual(result['original_process_adequacy'], 'NOT_ASSESSED')

    def test_duplicate_and_reordered_case_keys_fail_existing_report_validation(self):
        for mutation in ('duplicate', 'reversed', 'nonbinary'):
            report = fixture()
            if mutation == 'duplicate':report['cases'][1] = deepcopy(report['cases'][0])
            elif mutation == 'reversed':report['cases'].reverse()
            else:report['cases'][0]['outcome'] = {'numerator':'1', 'denominator':'2'}
            with self.subTest(mutation=mutation), self.assertRaises(Invalid):self.diagnose(report)

    def test_no_observed_comparisons_never_becomes_process_adequacy(self):
        # A long valid condition lookback has no matching outcome case inside
        # the eight-row reporting window; retain the zero denominator explicitly.
        result = self.diagnose(fixture(condition_lag=20))
        self.assertEqual(result['status'], 'SHIFTED_VALUE_IDENTITY')
        self.assert_counts(result, target_rows=8, partner_absent=8, both_unobserved=0,
            condition_unobserved=0, outcome_unobserved=0, compared=0, equal=0, unequal=0,
            both_eligible_compared=0)
        self.assertEqual(result['original_process_adequacy'], 'NOT_ASSESSED')
        self.assertFalse(result['scientific_readiness'])


if __name__ == '__main__':
    unittest.main()
