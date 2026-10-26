"""Adopted calibration count rules against independently frozen expectations."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest

from trading_researcher.calibration import assess_calibration, evaluate_cohort, one_sided_bound


FIXTURE = Path(__file__).parent / 'fixtures/reference_calibration_counts.json'
PIN = 'c1c7d41e24b20c4b3c170e7051fb597c1e6b761712274c287d008c485ac27ae9'
KINDS = ('false_support', 'boundary_decisive', 'joint_miscoverage', 'detection')


def rational(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def plan():
    return {'schema': 'narrow-calibration-assessment-plan/1', 'estimator_ref': 'fixture:estimator',
            'population_ref': 'fixture:population', 'cohorts': [
                {'id': kind, 'criterion': kind, 'world_ids': ['world-' + str(i) for i in range(256)],
                 'rationale': 'Predeclared synthetic count fixture.'} for kind in KINDS],
            'applicability': {
                'heavy_tail': {'status': 'not_applicable', 'cohort_ids': [], 'reason': 'Bounded binary fixture.'},
                'overlap': {'status': 'included', 'cohort_ids': ['boundary_decisive'], 'reason': 'Declared fixture case.'},
                'common_shock': {'status': 'included', 'cohort_ids': ['joint_miscoverage'], 'reason': 'Declared joint fixture.'}}}


def observations(cohort_id, count):
    return [{'cohort_id': cohort_id, 'world_id': 'world-' + str(i), 'state': 'observed',
             'event': i < count, 'source_ref': 'fixture:batch-output', 'reason': None} for i in range(256)]


class CalibrationTests(unittest.TestCase):
    def test_independent_exact_endpoint_brackets(self):
        raw = FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), PIN)
        for case in json.loads(raw)['bounds']:
            with self.subTest(case=case['id']):
                actual = one_sided_bound(case['k'], case['n'], case['side'], bits=case['bits'])
                bracket = case['bracket']
                self.assertEqual(list(map(rational, actual['root_bracket'])),
                    [Fraction(int(bracket[key]), int(bracket['denominator']))
                     for key in ('lower_numerator', 'upper_numerator')])
                self.assertEqual(rational(actual['bound']), rational(case['outward_endpoint']))

    def test_error_and_detection_thresholds_are_separate_from_design_target(self):
        worlds = plan()['cohorts'][0]['world_ids']
        for kind, count, expected, design in [
                ('false_support', 17, True, None), ('false_support', 18, False, None),
                ('detection', 191, False, False), ('detection', 192, True, False),
                ('detection', 204, True, False), ('detection', 205, True, True),
                ('boundary_decisive', 34, False, None)]:
            with self.subTest(kind=kind, count=count):
                result = evaluate_cohort(kind, worlds, observations(kind, count))
                self.assertIs(result['threshold_met'], expected)
                self.assertIs(result['design_target_met'], design)

    def test_complete_plan_passes_counts_without_claiming_authentication_or_science(self):
        manifest = plan()
        records = sum((observations(kind, 192 if kind == 'detection' else 17) for kind in KINDS), [])
        before = deepcopy((manifest, records))
        result = assess_calibration(manifest, records)
        self.assertEqual(result['status'], 'PASS_COUNTS_ONLY')
        self.assertTrue(result['complete'])
        self.assertFalse(result['scientific_readiness'])
        self.assertEqual(result['input_authentication'], 'UNVERIFIED')
        self.assertEqual(result['freshness'], 'UNVERIFIED')
        self.assertEqual((manifest, records), before)

    def test_missing_and_explicit_unknown_never_become_zero_errors(self):
        for missing in (True, False):
            with self.subTest(missing=missing):
                records = observations('false_support', 0)
                if missing:
                    records.pop()
                else:
                    records[-1].update(state='unavailable', event=None, reason='Retained failed simulation.')
                result = evaluate_cohort('false_support', plan()['cohorts'][0]['world_ids'], records)
                self.assertEqual(result['status'], 'NOT_ASSESSED')
                self.assertEqual(result['observed'], 255)
                self.assertIsNone(result['point'])
                self.assertIsNone(result['bound'])
                self.assertIsNone(result['threshold_met'])


if __name__ == '__main__':
    unittest.main()
