"""Independent count-kernel checks; no simulated-world or scientific certification."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from math import comb
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher import calibration as api
from trading_researcher.codec import Invalid, canonical, digest


FIXTURES = Path(__file__).parent / 'fixtures'
PINS = {
    'reference_calibration_counts.json': 'c1c7d41e24b20c4b3c170e7051fb597c1e6b761712274c287d008c485ac27ae9',
    'reference_calibration_counts.md': '04e272af558ff9b7c0c469aa5290217a9966c9a3c1807f42f0acb25d6163b303',
}
KINDS = ('false_support', 'boundary_decisive', 'joint_miscoverage', 'detection')


def rational(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def worlds(prefix='same-world'):
    return [f'{prefix}-{index:03d}' for index in range(256)]


def records(cohort='cohort-false_support', count=0, ids=None):
    return [{'cohort_id': cohort, 'world_id': world, 'state': 'observed', 'event': index < count,
             'source_ref': 'synthetic:shared-retained-batch', 'reason': None}
            for index, world in enumerate(worlds() if ids is None else ids)]


def manifest():
    return {'schema': 'narrow-calibration-assessment-plan/1', 'estimator_ref': 'synthetic:estimator',
            'population_ref': 'synthetic:population',
            'cohorts': [{'id': 'cohort-' + kind, 'criterion': kind, 'world_ids': worlds(),
                        'rationale': 'Independently fixed count fixture, not a real simulation.'} for kind in KINDS],
            'applicability': {
                'heavy_tail': {'status': 'not_applicable', 'cohort_ids': [], 'reason': 'Declared bounded binary fixture.'},
                'overlap': {'status': 'included', 'cohort_ids': ['cohort-boundary_decisive'], 'reason': 'Declared overlap fixture.'},
                'common_shock': {'status': 'included', 'cohort_ids': ['cohort-joint_miscoverage'], 'reason': 'Declared joint fixture.'}}}


def complete_records(plan):
    return [row for cohort in plan['cohorts'] for row in records(
        cohort['id'], 192 if cohort['criterion'] == 'detection' else 17, cohort['world_ids'])]


def exact_tail(k, n, p, side):
    # Independent direct polynomial; never call the production tail helper.
    a, b = p.numerator, p.denominator
    indices = range(k, n + 1) if side == 'lower' else range(k + 1)
    return Fraction(sum(comb(n, j) * a**j * (b-a)**(n-j) for j in indices), b**n)


class IndependentCalibrationTests(unittest.TestCase):
    def test_frozen_fixtures_and_all_exact_endpoint_inequalities(self):
        for filename, expected in PINS.items():
            self.assertEqual(hashlib.sha256((FIXTURES / filename).read_bytes()).hexdigest(), expected)
        fixture = json.loads((FIXTURES / 'reference_calibration_counts.json').read_text())
        for case in fixture['bounds']:
            with self.subTest(case=case['id']):
                actual = api.one_sided_bound(case['k'], case['n'], case['side'], bits=case['bits'])
                lo, hi = map(rational, actual['root_bracket'])
                bracket = case['bracket']; denominator = int(bracket['denominator'])
                self.assertEqual((lo, hi), (Fraction(int(bracket['lower_numerator']), denominator),
                                           Fraction(int(bracket['upper_numerator']), denominator)))
                self.assertEqual(rational(actual['bound']), rational(case['outward_endpoint']))
                self.assertEqual(rational(actual['noncoverage']), Fraction(1, 20))
                self.assertEqual(rational(actual['maximum_bracket_width']), Fraction(1, 1 << 40))
                self.assertLessEqual(hi-lo, Fraction(1, 1 << 40))
                endpoint = case['side'] == 'lower' and case['k'] == 0 or case['side'] == 'upper' and case['k'] == case['n']
                if not endpoint:
                    left = exact_tail(case['k'], case['n'], lo, case['side'])
                    right = exact_tail(case['k'], case['n'], hi, case['side'])
                    if case['side'] == 'upper':
                        left, right = right, left
                    self.assertLessEqual(left, Fraction(1, 20))
                    self.assertGreaterEqual(right, Fraction(1, 20))

    def test_bounds_exact_endpoints_closed_form_roots_and_precision_envelope(self):
        for bits in (8, 40, 64):
            for k, side, root in [(0, 'lower', Fraction(0)), (1, 'upper', Fraction(1)),
                                  (1, 'lower', Fraction(1, 20)), (0, 'upper', Fraction(19, 20))]:
                actual = api.one_sided_bound(k, 1, side, bits=bits)
                lo, hi = map(rational, actual['root_bracket'])
                self.assertLessEqual(lo, root); self.assertGreaterEqual(hi, root)
                self.assertLessEqual(hi-lo, Fraction(1, 1 << bits))
                if root in (0, 1):
                    self.assertEqual(lo, hi)
                    self.assertEqual(lo, root)
        for value in (True, False, None, '1', 1.0, -1):
            for name in ('k', 'n', 'bits'):
                arguments = {'k': 1, 'n': 2, 'side': 'upper', 'bits': 40}; arguments[name] = value
                with self.subTest(name=name, value=value), self.assertRaises(Invalid):
                    api.one_sided_bound(**arguments)
        for arguments in ((3, 2, 'upper', 40), (0, 0, 'lower', 40), (0, 257, 'upper', 40),
                          (1, 2, 'upper', 7), (1, 2, 'lower', 65)):
            with self.subTest(arguments=arguments), self.assertRaises(Invalid):
                api.one_sided_bound(*arguments)
        for side in (None, True, [], {}, 'both', 'UPPER'):
            with self.subTest(side=side), self.assertRaises(Invalid):
                api.one_sided_bound(1, 2, side)

    def test_all_three_error_criteria_and_detection_keep_distinct_thresholds(self):
        for criterion in KINDS:
            cases = [(0, False), (191, False), (192, True), (204, True), (205, True), (256, True)] if criterion == 'detection' else [(0, True), (17, True), (18, False), (34, False), (256, False)]
            for count, passed in cases:
                with self.subTest(criterion=criterion, count=count):
                    result = api.evaluate_cohort(criterion, worlds(), records(count=count))
                    self.assertIs(result['threshold_met'], passed)
                    self.assertEqual(result['status'], 'PASS_COUNTS_ONLY' if passed else 'FAIL_COUNTS_ONLY')
                    self.assertEqual(result['observed_events'], count)
                    self.assertEqual(rational(result['point']), Fraction(count, 256))
                    self.assertEqual(result['design_target_met'], count >= 205 if criterion == 'detection' else None)

    def test_exact_threshold_acceptance_is_independent_of_outward_display_rounding(self):
        original = api.one_sided_bound
        with patch.object(api, 'one_sided_bound', side_effect=lambda k, n, side: original(k, n, side, bits=8)):
            errors = api.evaluate_cohort('false_support', worlds(), records(count=17))
            detection = api.evaluate_cohort('detection', worlds(), records(count=192))
        self.assertEqual(rational(errors['bound']['bound']), Fraction(26, 256))
        self.assertGreater(rational(errors['bound']['bound']), Fraction(1, 10))
        self.assertIs(errors['threshold_met'], True)
        self.assertEqual(rational(detection['bound']['bound']), Fraction(179, 256))
        self.assertLess(rational(detection['bound']['bound']), Fraction(7, 10))
        self.assertIs(detection['threshold_met'], True)

    def test_empty_partial_and_unavailable_cohorts_never_renormalize(self):
        for criterion in KINDS:
            for mode in ('empty', 'missing', 'unavailable', 'all_unavailable'):
                with self.subTest(criterion=criterion, mode=mode):
                    rows = records(count=256 if criterion == 'detection' else 0)
                    if mode == 'empty': rows = []
                    elif mode == 'missing': rows.pop()
                    else:
                        for row in rows if mode == 'all_unavailable' else rows[-1:]:
                            row.update(state='unavailable', event=None, reason='Execution truth unavailable.')
                    result = api.evaluate_cohort(criterion, worlds(), rows)
                    self.assertEqual(result['status'], 'NOT_ASSESSED')
                    self.assertFalse(result['complete']); self.assertEqual(result['planned'], 256)
                    self.assertEqual(result['observed'], 0 if mode in ('empty', 'all_unavailable') else 255)
                    for field in ('point', 'bound', 'threshold_met', 'design_target_met'):
                        self.assertIsNone(result[field])
                    self.assertEqual(len(result['missing_world_ids']), 256 if mode == 'empty' else 1 if mode == 'missing' else 0)
                    self.assertEqual(len(result['unavailable_world_ids']), 256 if mode == 'all_unavailable' else 1 if mode == 'unavailable' else 0)

    def test_incomplete_manifest_retains_complete_failure_without_overall_pass(self):
        plan = manifest(); rows = complete_records(plan)
        rows[17]['event'] = True
        rows[-1].update(state='unavailable', event=None, reason='Retained technical failure.')
        result = api.assess_calibration(plan, rows)
        self.assertEqual(result['status'], 'NOT_ASSESSED')
        self.assertEqual(result['cohorts'][0]['status'], 'FAIL_COUNTS_ONLY')
        self.assertEqual(result['cohorts'][0]['observed_events'], 18)
        self.assertEqual(result['cohorts'][-1]['observed_events'], 192)
        self.assertIsNone(result['cohorts'][-1]['point'])
        self.assertFalse(result['scientific_readiness'])

    def test_stress_cohorts_are_not_pooled_to_hide_a_failed_world_law(self):
        plan = manifest()
        plan['cohorts'].append({'id': 'cohort-additional-null', 'criterion': 'false_support',
                                'world_ids': worlds('additional'), 'rationale': 'A separate predeclared null world law.'})
        rows = complete_records(plan)
        rows[17]['event'] = True
        for row in rows[-256:]: row['event'] = False
        result = api.assess_calibration(plan, rows)
        self.assertEqual(result['status'], 'FAIL_COUNTS_ONLY')
        self.assertEqual(result['cohorts'][0]['observed_events'], 18)
        self.assertEqual(result['cohorts'][-1]['observed_events'], 0)
        self.assertEqual(result['cohorts'][-1]['status'], 'PASS_COUNTS_ONLY')

    def test_world_ids_may_recur_across_criteria_and_source_batches_are_not_worlds(self):
        plan = manifest(); rows = complete_records(plan)
        result = api.assess_calibration(plan, rows)
        self.assertEqual(result['status'], 'PASS_COUNTS_ONLY')
        self.assertEqual(len({row['world_id'] for row in rows}), 256)
        self.assertEqual(len(rows), 1024)
        for cohort in result['cohorts']:
            self.assertEqual(cohort['observed'], 256)
            self.assertEqual(cohort['source_refs'], ['synthetic:shared-retained-batch'])

    def test_world_inventory_must_be_exact_unique_bounded_strings(self):
        invalid = [None, {}, 'world', tuple(worlds()), worlds()[:-1], worlds()+['extra'], ['same']*256]
        for value in (True, 1, None, [], {}, '', '   ', 'x'*8193):
            changed = worlds(); changed[0] = value; invalid.append(changed)
        for ids in invalid:
            with self.subTest(type=type(ids).__name__), self.assertRaises(Invalid):
                api.evaluate_cohort('false_support', ids, [])

    def test_observations_reject_duplicates_unplanned_and_mixed_cohorts(self):
        cases = []
        changed = records(); changed[-1] = deepcopy(changed[0]); cases.append(changed)
        changed = records(); changed[0]['world_id'] = 'unplanned'; cases.append(changed)
        changed = records(); changed[0]['cohort_id'] = 'different'; cases.append(changed)
        cases.extend((records()+[deepcopy(records()[0])], {}, None, tuple(records())))
        for rows in cases:
            with self.subTest(type=type(rows).__name__), self.assertRaises(Invalid):
                api.evaluate_cohort('false_support', worlds(), rows)

    def test_observation_schema_rejects_forged_states_events_and_evidence(self):
        first = records()[0]; bad = [None, [], True]
        for field in first:
            changed = deepcopy(first); del changed[field]; bad.append(changed)
        changed = deepcopy(first); changed['authenticated'] = True; bad.append(changed)
        for field in ('cohort_id', 'world_id', 'source_ref'):
            for value in (None, True, 7, {}, '', '  '):
                changed = deepcopy(first); changed[field] = value; bad.append(changed)
        for value in (None, 0, 1, 'false', [], {}):
            changed = deepcopy(first); changed['event'] = value; bad.append(changed)
        for state in (None, True, [], {}, 'failed', 'complete'):
            changed = deepcopy(first); changed['state'] = state; bad.append(changed)
        changed = deepcopy(first); changed['reason'] = 'Observed with an unavailable reason'; bad.append(changed)
        for event, reason in [(False, 'Missing'), (True, 'Missing'), (None, None), (None, ''), (None, '   ')]:
            changed = deepcopy(first); changed.update(state='unavailable', event=event, reason=reason); bad.append(changed)
        for row in bad:
            with self.subTest(row=row), self.assertRaises(Invalid):
                api.evaluate_cohort('false_support', worlds(), [row])
        for criterion in (None, True, [], {}, 'power', 'FALSE_SUPPORT'):
            with self.subTest(criterion=criterion), self.assertRaises(Invalid):
                api.evaluate_cohort(criterion, worlds(), [])

    def test_manifest_exact_schema_and_all_four_criteria_are_required(self):
        original = manifest(); invalid = [None, [], True]
        for field in original:
            changed = deepcopy(original); del changed[field]; invalid.append(changed)
        changed = deepcopy(original); changed['scientific_readiness'] = True; invalid.append(changed)
        for field, value in [('schema', 'narrow-calibration-assessment-plan/2'), ('estimator_ref', ''),
                             ('population_ref', None), ('cohorts', []), ('cohorts', {})]:
            changed = deepcopy(original); changed[field] = value; invalid.append(changed)
        for field, value in [('id', original['cohorts'][1]['id']), ('id', True), ('criterion', []),
                             ('criterion', 'detection'), ('rationale', ''), ('world_ids', worlds()[:-1])]:
            changed = deepcopy(original); changed['cohorts'][0][field] = value; invalid.append(changed)
        for removed in range(4):
            changed = deepcopy(original); changed['cohorts'].pop(removed); invalid.append(changed)
        changed = deepcopy(original); changed['cohorts'][0]['seed_authentication'] = 'verified'; invalid.append(changed)
        for plan in invalid:
            with self.subTest(type=type(plan).__name__), self.assertRaises(Invalid):
                api.assess_calibration(plan, [])

    def test_applicability_requires_reasons_and_consistent_declared_cohort_refs(self):
        original = manifest(); invalid = []
        for issue in ('heavy_tail', 'overlap', 'common_shock'):
            changed = deepcopy(original); del changed['applicability'][issue]; invalid.append(changed)
        for declaration in [None, {}, {'status': 'included', 'cohort_ids': [], 'reason': 'Declared'},
                            {'status': 'not_applicable', 'cohort_ids': ['cohort-false_support'], 'reason': 'Declared'},
                            {'status': 'included', 'cohort_ids': ['undeclared'], 'reason': 'Declared'},
                            {'status': 'included', 'cohort_ids': ['cohort-false_support']*2, 'reason': 'Declared'},
                            {'status': 'included', 'cohort_ids': ['cohort-false_support'], 'reason': ''},
                            {'status': 'verified', 'cohort_ids': [], 'reason': 'Declared'}]:
            changed = deepcopy(original); changed['applicability']['heavy_tail'] = declaration; invalid.append(changed)
        changed = deepcopy(original); changed['applicability']['extra'] = {}; invalid.append(changed)
        for plan in invalid:
            with self.subTest(plan=plan['applicability']), self.assertRaises(Invalid):
                api.assess_calibration(plan, [])

    def test_observations_cannot_cross_manifest_cohort_or_world_binding(self):
        plan = manifest(); plan['cohorts'][1]['world_ids'] = worlds('different-law')
        for row in [records(cohort='undeclared')[0], records(cohort=plan['cohorts'][1]['id'])[0]]:
            with self.subTest(row=row), self.assertRaises(Invalid):
                api.assess_calibration(plan, [row])
        rows = complete_records(plan); rows[-1] = deepcopy(rows[-2])
        with self.assertRaises(Invalid): api.assess_calibration(plan, rows)

    def test_sixteen_cohorts_are_bounded_and_seventeenth_is_rejected(self):
        plan = manifest()
        for index in range(12):
            plan['cohorts'].append({'id': f'extra-{index}', 'criterion': 'false_support', 'world_ids': worlds(),
                                    'rationale': 'Separate fixed world law.'})
        result = api.assess_calibration(plan, complete_records(plan))
        self.assertEqual(len(result['cohorts']), 16)
        self.assertEqual(result['status'], 'PASS_COUNTS_ONLY')
        extra = deepcopy(plan['cohorts'][-1]); extra['id'] = 'seventeenth'; plan['cohorts'].append(extra)
        with self.assertRaises(Invalid): api.assess_calibration(plan, [])

    def test_inputs_outputs_and_cached_endpoints_are_detached(self):
        plan = manifest(); rows = complete_records(plan); before = canonical({'manifest': plan, 'observations': rows})
        result = api.assess_calibration(plan, rows)
        self.assertEqual(result['input_hash'], digest({'manifest': plan, 'observations': rows}))
        self.assertEqual(result['plan_hash'], digest(plan))
        self.assertEqual(canonical({'manifest': plan, 'observations': rows}), before)
        result['applicability']['overlap']['cohort_ids'].append('mutation')
        result['cohorts'][0]['source_refs'].append('mutation')
        result['cohorts'][0]['bound']['root_bracket'][0]['numerator'] = '999'
        self.assertEqual(canonical({'manifest': plan, 'observations': rows}), before)
        self.assertNotIn('mutation', canonical(api.assess_calibration(plan, rows)))
        bound = api.one_sided_bound(17, 256, 'upper'); expected = deepcopy(bound)
        bound['root_bracket'][0]['numerator'] = '999'
        self.assertEqual(api.one_sided_bound(17, 256, 'upper'), expected)

    def test_order_does_not_change_counts_and_all_pass_states_remain_non_authoritative(self):
        plan = manifest(); rows = complete_records(plan)
        first = api.assess_calibration(plan, rows)
        reversed_result = api.assess_calibration(plan, list(reversed(rows)))
        self.assertEqual(first['cohorts'], reversed_result['cohorts'])
        self.assertNotEqual(first['input_hash'], reversed_result['input_hash'])
        for report in (first, reversed_result):
            self.assertEqual(report['status'], 'PASS_COUNTS_ONLY'); self.assertIs(report['scientific_readiness'], False)
            self.assertIsNone(report['n_min'])
            for field in ('input_authentication', 'freshness', 'event_semantics', 'applicability_evidence'):
                self.assertEqual(report[field], 'UNVERIFIED')
            for cohort in report['cohorts']:
                self.assertIs(cohort['scientific_readiness'], False)
                self.assertEqual(cohort['input_authentication'], 'UNVERIFIED')


if __name__ == '__main__':
    unittest.main()
