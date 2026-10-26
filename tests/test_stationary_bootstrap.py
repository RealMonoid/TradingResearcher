"""Executable contract probes for joint fixed-length-count resampling."""
from copy import deepcopy
from fractions import Fraction
import unittest

from bootstrap_support import report
from trading_researcher import stationary_bootstrap as bootstrap
from trading_researcher.codec import Invalid


class BootstrapTests(unittest.TestCase):
    def design(self,base=2):
        return {'base_length':base,'primary_count':2,'randomness':bootstrap.randomness(713)}

    def limits(self):return {'max_seconds':60,'max_segments':2000000}

    def test_geometric_mean_is_not_a_minimum_and_final_segment_is_truncated(self):
        class Random:
            starts=iter([3,1,4]); uniforms=iter([0.75,0.0,0.9])
            def randrange(self,n):return next(self.starts)
            def random(self):return next(self.uniforms)
        self.assertEqual(list(bootstrap._segments(5,2,Random())),[(3,3),(1,1),(4,1)])

    def test_exact_prefix_sums_wrap_without_changing_weight(self):
        prefix=[Fraction(0),Fraction(1,3),Fraction(7,3),Fraction(10,3)]
        self.assertEqual(bootstrap._segment_sum(prefix,2,2),Fraction(4,3))
        self.assertEqual(bootstrap._segment_sum(prefix,1,3),Fraction(10,3))

    def test_full_fixed_resamples_and_sensitivities_are_reproducible(self):
        source=report(); original=deepcopy(source)
        first=bootstrap.calculate(source,self.design(),self.limits())
        second=bootstrap.calculate(source,self.design(),self.limits())
        self.assertEqual(first,second)
        self.assertEqual(first['status'],'COMPUTED_UNCALIBRATED')
        self.assertEqual(first['time_rows'],12)
        self.assertEqual(first['required_lengths'],[1,2,4])
        self.assertEqual([c['attempted'] for c in first['cases']],[19999]*3)
        self.assertTrue(all(c['defined']==19999 and c['undefined']==0 for c in first['cases']))
        zero={'numerator':'0','denominator':'1'}
        self.assertEqual(first['interval'],{'lower':zero,'upper':zero})
        self.assertFalse(first['scientific_readiness'])
        self.assertFalse(first['classification_permitted'])
        self.assertEqual(source,original)

    def test_undefined_draws_are_retained_and_never_replaced(self):
        records=[]
        result=bootstrap.calculate(report(rare=True),self.design(),self.limits(),on_draw=records.append)
        self.assertEqual(result['status'],'INFORMATION_GAP')
        self.assertIsNone(result['interval'])
        self.assertEqual(len(records),19999*3)
        self.assertTrue(any(c['undefined']>0 for c in result['cases']))
        self.assertTrue(all(c['attempted']==c['defined']+c['undefined']==19999 for c in result['cases']))
        self.assertTrue(any(r['value'] is None for r in records))

    def test_resource_stop_and_pending_input_cannot_construct_interval(self):
        result=bootstrap.calculate(report(),self.design(),{'max_seconds':60,'max_segments':1})
        self.assertEqual(result['status'],'RESOURCE_STOP')
        self.assertIsNone(result['interval'])
        self.assertEqual(sum(c['interrupted'] for c in result['cases']),1)
        pending=bootstrap.calculate(report(as_of=900),self.design(),self.limits())
        self.assertEqual(pending['status'],'INPUT_GAP')
        self.assertEqual(pending['cases'],[])

    def test_seed_runtime_and_configuration_are_bound(self):
        for key,value in [('base_length',True),('primary_count',9),('extra','ignored')]:
            design=self.design(); design[key]=value
            with self.subTest(key=key),self.assertRaises(Invalid):bootstrap.calculate(report(),design,self.limits())
        design=self.design(); design['randomness']['version']='other-runtime'
        with self.assertRaises(Invalid):bootstrap.calculate(report(),design,self.limits())
        with self.assertRaises(Invalid):bootstrap.randomness(True)


if __name__=='__main__':unittest.main()
