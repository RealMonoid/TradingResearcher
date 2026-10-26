"""Development measurements retain gaps and never identify scientific power."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import unittest

from bootstrap_support import report
from trading_researcher.codec import Invalid, canonical
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.outcomes import _read_rational, _rational, STATES


class InformationDiagnosticsTests(unittest.TestCase):
    def test_degenerate_rates_keep_measurements_and_full_grid(self):
        source=report(times=6)
        contributions=[]
        result=diagnose(source,[1,2,9],on_contribution=contributions.append)
        self.assertEqual(result['status'],'COMPUTED_DIAGNOSTICS')
        self.assertEqual(result['time_rows'],6)
        self.assertEqual(result['totals']['scope']['count'],10)
        self.assertEqual(result['totals']['scope']['rate'],_rational(1))
        self.assertIn('degenerate_scope_rate',result['model_identification_gaps'])
        self.assertIn('all_scope_conditioned',result['model_identification_gaps'])
        self.assertEqual(len(contributions),6)
        self.assertEqual(contributions[-1]['scope_count'],0)
        self.assertIsNone(result['n_min'])
        self.assertFalse(result['scientific_readiness'])
        self.assertFalse(result['classification_permitted'])
        unavailable=result['grid_moments']['scope_count']['lags'][-1]
        self.assertEqual(unavailable['pairs'],0)
        self.assertIsNone(unavailable['covariance'])
        raw=b''.join((canonical(row)+'\n').encode() for row in contributions)
        self.assertEqual(result['contributions_sha256'],hashlib.sha256(raw).hexdigest())

    def test_no_true_condition_keeps_scope_rate_and_null_score(self):
        source=report(times=6)
        for row in source['cases']:
            if row['status']=='ELIGIBLE':row['condition']=None
        result=diagnose(source,[1])
        self.assertEqual(result['totals']['unknown']['count'],10)
        self.assertEqual(result['totals']['condition_fraction'],_rational(0))
        self.assertIsNone(result['grid_moments']['contrast_score'])
        self.assertIn('no_conditioned_cases',result['model_identification_gaps'])
        self.assertEqual(result['status'],'COMPUTED_DIAGNOSTICS')

    def test_explicit_lags_are_bounded_unique_sorted_integers(self):
        for lags in (None,[],[0],[True],[2,1],[1,1],[100001],list(range(1,18))):
            with self.subTest(lags=lags),self.assertRaises(Invalid):diagnose(report(),lags)

    def test_malformed_grid_is_not_repaired_or_truncated(self):
        source=report()
        source['cases'][0]['decision_time']=900
        with self.assertRaises(ValueError):diagnose(source,[1])

    def test_nonbinary_profile_preserves_the_original_outcome_as_gap(self):
        source=report()
        source['request']['outcome_scale']='quantity'
        source['outcome_unit']='ratio'
        original=deepcopy(source)
        result=diagnose(source,[1])
        self.assertEqual(result['status'],'EVALUATION_GAP')
        self.assertEqual(result['reason'],'binary_population_profile_required')
        self.assertEqual(source,original)
        self.assertIsNone(result['n_min'])

    def test_unfinished_outcomes_cannot_become_complete_diagnostics(self):
        result=diagnose(report(times=6,as_of=900),[1])
        self.assertEqual(result['status'],'INPUT_GAP')
        self.assertEqual(result['reason'],'outcomes_pending')

    def test_callback_error_propagates_and_records_are_detached(self):
        def fail(record):raise RuntimeError('retention failed')
        with self.assertRaisesRegex(RuntimeError,'retention failed'):
            diagnose(report(),[1],on_contribution=fail)
        source=report();original=deepcopy(source)
        expected=diagnose(source,[1])
        def change(record):record['scope_count']=-99
        self.assertEqual(diagnose(source,[1],on_contribution=change),expected)
        self.assertEqual(source,original)


if __name__=='__main__':unittest.main()
