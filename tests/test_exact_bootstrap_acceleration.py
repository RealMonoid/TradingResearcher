"""Equality to retained Fraction arithmetic, including streams and stop prefixes."""
from fractions import Fraction
import unittest

from bootstrap_oracle import binary_report,fraction_reference
from bootstrap_support import report
from trading_researcher.codec import digest
from trading_researcher.stationary_bootstrap import calculate,randomness


class ExactAccelerationTests(unittest.TestCase):
    def design(self,base=4):return {'base_length':base,'primary_count':2,'randomness':randomness(713)}
    def compare(self,source,design,limits,**kwargs):
        with fraction_reference() as reference:
            expected=reference.calculate(source,design,limits,**kwargs)
        actual=calculate(source,design,limits,**kwargs)
        self.assertEqual(digest(actual),digest(expected))
        return actual

    def test_binary_full_draws_and_mc_diagnostic_match_retained_fraction(self):
        from trading_researcher.outcomes import _rational
        design={**self.design(),'mc_policy':{'schema':'mc-boundary-policy/1',
            'noncoverage':_rational(Fraction(1,100)),'delta':_rational(Fraction(1,20)),'direction':'positive'}}
        result=self.compare(binary_report(32),design,{'max_seconds':180,'max_segments':2000000})
        self.assertEqual(result['status'],'COMPUTED_UNCALIBRATED')
        self.assertEqual(sum(c['attempted'] for c in result['cases']),59997)

    def test_partial_segment_budget_keeps_exact_original_ordinals_and_paths(self):
        for cap in (1,17,137):
            with self.subTest(cap=cap):
                value=self.compare(report(times=12),self.design(),{'max_seconds':180,'max_segments':cap})
                self.assertEqual(value['status'],'RESOURCE_STOP')

    def test_undefined_draws_stay_in_the_same_positions(self):
        value=self.compare(report(times=6,rare=True),self.design(),{'max_seconds':180,'max_segments':2000000})
        self.assertEqual(value['status'],'INFORMATION_GAP')
        self.assertGreater(sum(c['undefined'] for c in value['cases']),0)

    def test_fractional_report_keeps_reference_arithmetic(self):
        # Construct a genuine fractional report through the independent fixture.
        from test_stationary_bootstrap_adversarial import quantity_report
        source=quantity_report([[str(i),str(2*i+1)] for i in range(8)],
                               [[True,False]]*8,[[True,True]]*8,divisor=3)
        self.compare(source,self.design(),{'max_seconds':180,'max_segments':2000000})


if __name__=='__main__':unittest.main()
