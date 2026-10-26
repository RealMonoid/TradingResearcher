"""Independent boundary probes; fixed expectations and runtime sources remain unchanged."""
from copy import deepcopy
from fractions import Fraction
import unittest

from trading_researcher import evaluation_policy as policy
from trading_researcher.codec import Invalid
from trading_researcher.outcomes import _rational, _read_rational
from test_evaluation_policy import profile_inputs, read_cases


def rational(numerator, denominator=1):
    return _rational(Fraction(numerator, denominator))


def return_inputs():
    case = next(case for case in read_cases()
                if case['name'] == 'profile_simple_24h_return_BTCUSDT')
    return profile_inputs(deepcopy(case['input']))


class EvaluationPolicyAdversarialTests(unittest.TestCase):
    def test_quantile_growth_returns_typed_resource_failure(self):
        # Each input fits the existing 8192-bit envelope; interpolation does not.
        left, right = 2**8190 - 1, 2**8190 + 1
        values = [rational(1, left), rational(1, right)]
        for value in values:
            _read_rational(value)
        with self.assertRaises(Invalid):
            policy.quantile(values, rational(1, 2))

    def test_basic_interval_final_growth_returns_typed_resource_failure(self):
        # The reflected endpoint is 3*point and exceeds the input/output envelope.
        point = 2**8191 - 1
        with self.assertRaises(Invalid):
            policy.basic_interval(rational(point), [rational(-point)], rational(1, 20))

    def test_large_exact_cancellation_remains_usable(self):
        denominator = 2**8190 - 1
        value = rational(1, denominator)
        self.assertEqual(policy.quantile([value, value], rational(1, 2)), value)
        self.assertEqual(policy.basic_interval(value, [value, value], rational(1, 20)),
                         {'lower': value, 'upper': value})

    def test_raw_close_unit_mismatch_is_not_a_return_profile(self):
        candidate, definitions, description = return_inputs()
        definitions[0]['unit'] = 'BTC'
        with self.assertRaises(Invalid):
            policy.effect_profile(candidate, definitions, description)

    def test_boolean_type_cannot_replace_real_close(self):
        candidate, definitions, description = return_inputs()
        definitions[0]['type'] = 'boolean'
        with self.assertRaises(Invalid):
            policy.effect_profile(candidate, definitions, description)

    def test_price_like_name_does_not_replace_volume_semantics(self):
        candidate, definitions, description = return_inputs()
        definitions[0]['field'] = 'volume'
        with self.assertRaises(Invalid):
            policy.effect_profile(candidate, definitions, description)

    def test_binary_description_requires_actual_boolean_type(self):
        candidate, definitions, description = return_inputs()
        candidate['outcome']['scale'] = 'binary_probability'
        for value_type, unit in [('real', 'ratio'), ('boolean', 'ratio'), (True, None)]:
            with self.subTest(value_type=value_type, unit=unit), self.assertRaises(Invalid):
                policy.effect_profile(candidate, definitions, {'type': value_type, 'unit': unit})

    def test_boolean_counts_and_release_flags_are_not_coerced(self):
        for value in (True, False):
            with self.subTest(value=value), self.assertRaises(Invalid):
                policy.family_budget(value)
            with self.subTest(draw_count=value), self.assertRaises(Invalid):
                policy.bootstrap_completeness(19999, value)
        for value in (0, 1, 'true', None):
            with self.subTest(release_flag=value), self.assertRaises(Invalid):
                policy.release_decision(value, True, False, True, ['effect'])

    def test_accounting_cannot_hide_missing_duplicate_or_undefined_sensitivity(self):
        complete = {'length': 96, 'attempted': 19999, 'defined': 19999, 'undefined': 0}
        missing = policy.bootstrap_family_completeness([96, 192], [complete])
        self.assertFalse(missing['interval_construction_permitted'])
        undefined = {'length': 192, 'attempted': 19999, 'defined': 19998, 'undefined': 1}
        result = policy.bootstrap_family_completeness([96, 192], [complete, undefined])
        self.assertFalse(result['interval_construction_permitted'])
        self.assertFalse(result['discard_undefined_draws_permitted'])
        with self.assertRaises(Invalid):
            policy.bootstrap_family_completeness([96, 192], [complete, complete])
        inconsistent = {'length': 192, 'attempted': 19999, 'defined': 19999, 'undefined': 1}
        with self.assertRaises(Invalid):
            policy.bootstrap_family_completeness([96, 192], [complete, inconsistent])
        with self.assertRaises(Invalid):
            policy.basic_interval(rational(0), [rational(0), None], rational(1, 20))

    def test_nondirectional_endpoints_do_not_change_directional_policy(self):
        delta = rational(1, 20)
        self.assertEqual(policy.classify_interval(delta, delta, delta, 'nondirectional'),
                         'TESTED_NEGATIVE')
        self.assertEqual(policy.classify_interval(delta, delta, delta, 'positive'),
                         'TESTED_INCONCLUSIVE')
        self.assertEqual(policy.classify_interval(delta, rational(1, 10), delta, 'nondirectional'),
                         'TESTED_INCONCLUSIVE')

    def test_technical_termination_cannot_release_scientific_results_even_if_complete(self):
        for complete in (False, True):
            result = policy.release_decision(True, complete, True, True,
                                             ['effect', 'interval', 'rank', 'pass_fail'])
            self.assertEqual(result, {'scientific_outputs_releasable': False,
                                      'technical_status_only_releasable': True})
        self.assertFalse(policy.release_decision(False, True, False, True, ['effect'])[
            'scientific_outputs_releasable'])

    def test_draft_remains_incomplete_and_detached_from_caller_mutation(self):
        candidate, definitions, description = return_inputs()
        candidate['estimand']['weighting'] = 'equal_rows'
        dependence = {'base_length': 97, 'rationale': 'Synthetic development-only test input',
                      'development_refs': ['fixture:diagnostic'],
                      'randomness': {'algorithm': 'fixture-only', 'version': '1', 'seed': 1}}
        result = policy.draft_plan(candidate, definitions, description, 2, dependence)
        self.assertFalse(result['scientific_readiness'])
        self.assertIsNone(result['sample_precision_plan']['n_min'])
        self.assertIn('independent_semantic_review', result['remaining_gates'])
        self.assertIn('calibrated_estimator_and_information_plan', result['remaining_gates'])
        dependence['randomness']['seed'] = 2
        dependence['development_refs'].append('fixture:changed')
        candidate['estimand']['weighting'] = 'caller_changed'
        self.assertEqual(result['dependence_design']['randomness']['seed'], 1)
        self.assertEqual(result['dependence_design']['development_refs'], ['fixture:diagnostic'])
        self.assertEqual(result['estimand']['weighting'], 'equal_rows')


if __name__ == '__main__':
    unittest.main()
