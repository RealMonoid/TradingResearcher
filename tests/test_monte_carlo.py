"""Fixed Monte Carlo rank arithmetic and conservative boundary diagnostics."""
from fractions import Fraction
import unittest

from trading_researcher.codec import Invalid
from trading_researcher.outcomes import _rational as q
from trading_researcher.monte_carlo import rank_bounds, quantile_band, diagnose, validate_config


def config(direction='positive', beta=Fraction(1,100), delta=Fraction(1,20)):
    return {'schema':'mc-boundary-policy/1','noncoverage':q(beta),'delta':q(delta),'direction':direction}


class MonteCarloTests(unittest.TestCase):
    def test_sampler_assesses_explicit_policy_without_changing_draws(self):
        from bootstrap_support import report
        from trading_researcher.stationary_bootstrap import calculate, randomness
        source=report(times=12)
        design={'base_length':4,'primary_count':2,'randomness':randomness(713)}
        limits={'max_seconds':180,'max_segments':2000000}
        plain=calculate(source,design,limits)
        result=calculate(source,{**design,'mc_policy':config()},limits)
        self.assertEqual(result['schema'],'joint-bootstrap-computation/2')
        self.assertEqual(result['cases'],plain['cases'])
        self.assertEqual(result['interval'],plain['interval'])
        self.assertEqual(result['monte_carlo']['status'],'ASSESSED_UNCALIBRATED')
        stopped=calculate(source,{**design,'mc_policy':config()},limits,stop=lambda:True)
        self.assertEqual(stopped['monte_carlo']['status'],'NOT_ASSESSED')

    def test_exact_small_binomial_ranks_and_unbounded_ends(self):
        # Binomial(5,1/2) tails: P(K=0)=1/32, P(K<=1)=6/32.
        self.assertEqual(rank_bounds(5,q(Fraction(1,2)),q(Fraction(1,20))),[1,5])
        self.assertEqual(rank_bounds(5,q(Fraction(1,2)),q(Fraction(1,32))),[1,5])
        self.assertEqual(rank_bounds(5,q(Fraction(1,2)),q(Fraction(1,100))),[0,6])
        self.assertEqual(quantile_band([q(i) for i in range(5)],q(Fraction(1,2)),q(Fraction(1,100))),
                         {'ranks':[0,6],'lower':None,'upper':None})

    def test_full_constant_draws_are_stable_without_authority(self):
        result=diagnose(q(Fraction(1,10)),{4:[q(Fraction(1,10))]*19999},q(Fraction(1,20)),config())
        self.assertEqual(result['status'],'ASSESSED_UNCALIBRATED')
        self.assertTrue(result['boundary_stable'])
        self.assertEqual(result['nominal_classification'],'SUPPORTED_INITIAL')
        self.assertFalse(result['classification_permitted'])
        self.assertFalse(result['scientific_readiness'])
        self.assertFalse(result['selective_reseeding_permitted'])

    def test_equality_and_direction_are_preserved(self):
        for direction,point,expected in [('positive',Fraction(1,20),'TESTED_INCONCLUSIVE'),
                ('negative',Fraction(-1,10),'SUPPORTED_INITIAL'),
                ('nondirectional',Fraction(1,20),'TESTED_NEGATIVE')]:
            with self.subTest(direction=direction):
                result=diagnose(q(point),{4:[q(point)]*19999},q(Fraction(1,20)),config(direction))
                self.assertEqual(result['nominal_classification'],expected)
                self.assertTrue(result['boundary_stable'])

    def test_missing_draw_is_retained_as_gap_not_dropped(self):
        values=[q(0)]*19998+[None]
        result=diagnose(q(0),{4:values},q(Fraction(1,20)),config())
        self.assertEqual(result['status'],'NOT_ASSESSED')
        self.assertIsNone(result['boundary_stable'])
        self.assertFalse(result['classification_permitted'])
        self.assertEqual(result['reason'],'incomplete_or_undefined_draws')

    def test_no_default_budget_and_bounded_exact_input(self):
        for bad in [dict(config(),noncoverage=q(0)),dict(config(),noncoverage=q(1)),
                    dict(config(),delta=q(0)),dict(config(),direction='either'),
                    {'schema':'mc-boundary-policy/1'}]:
            with self.subTest(bad=bad),self.assertRaises(Invalid):validate_config(bad)
        with self.assertRaises(Invalid):rank_bounds(True,q(Fraction(1,2)),q(Fraction(1,20)))
        with self.assertRaises(Invalid):rank_bounds(20000,q(Fraction(1,2)),q(Fraction(1,20)))


if __name__=='__main__':unittest.main()
