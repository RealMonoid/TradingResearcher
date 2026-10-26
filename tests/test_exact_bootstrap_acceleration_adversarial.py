"""Independent exact-integer path probes; performance and power are separate."""
from copy import deepcopy
from fractions import Fraction
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from bootstrap_oracle import fraction_reference, binary_report
from test_stationary_bootstrap_adversarial import arithmetic_probe, quantity_report
from trading_researcher import stationary_bootstrap as current
from trading_researcher.codec import canonical, digest


def q(value):
    value=Fraction(value)
    return {'numerator':str(value.numerator),'denominator':str(value.denominator)}


class ExactAccelerationAdversarialTests(unittest.TestCase):
    def design(self,base=1):
        return {'base_length':base,'primary_count':2,'randomness':current.randomness(713)}

    def limits(self,segments=2000000):
        return {'max_seconds':180,'max_segments':segments}

    def paired(self,run):
        with fraction_reference() as reference:
            expected=run(reference)
        actual=run(current)
        self.assertEqual(actual,expected)
        return actual

    def test_archived_oracle_bytes_match_prior_reviewed_sampler(self):
        with fraction_reference() as reference:
            self.assertEqual(hashlib.sha256(Path(reference.__file__).read_bytes()).hexdigest(),
                             '789d172ad4e4fff99f9f506c65ac9d6b0ca3fdc1bcc8e8a79702704cf2a1daf6')
            self.assertNotEqual(reference.__name__,current.__name__)

    def test_hand_prefixes_preserve_unknown_baseline_and_empty_grid_bucket(self):
        source=arithmetic_probe()
        expected=[[0,2,3,3],[0,10,14,14],[0,1,2,2],[0,0,4,4]]
        prefixes=self.paired(lambda module:module._prefixes(source))
        self.assertEqual(prefixes,expected)
        self.assertTrue(all(type(x) is int for prefix in current._prefixes(source) for x in prefix))
        self.assertEqual(Fraction(prefixes[3][-1],prefixes[2][-1])-Fraction(prefixes[1][-1],prefixes[0][-1]),
                         Fraction(-8,3))

    def test_public_integer_sums_keep_fractional_mean_without_float_division(self):
        def run(module):
            records=[]
            with patch.object(module,'_segments',side_effect=lambda size,length,rng:iter([(0,size)])):
                result=module.calculate(arithmetic_probe(),self.design(),self.limits(1),on_draw=records.append)
            return result,records
        result,records=self.paired(run)
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]['value'],q(Fraction(-8,3)))
        self.assertEqual(result['reason'],'computation_segment_limit')

    def test_signed_large_integer_outcomes_preserve_sub_float_unit_difference(self):
        source=quantity_report([['0','0'],['9007199254740993','-9007199254740992'],['0','0']],
                               [[True,False]]*3,[[True,True],[False,False],[False,False]])
        def run(module):
            records=[]
            with patch.object(module,'_segments',side_effect=lambda size,length,rng:iter([(0,size)])):
                result=module.calculate(source,self.design(),self.limits(1),on_draw=records.append)
            return result,records
        result,records=self.paired(run)
        self.assertEqual(records[0]['value'],q(Fraction(18014398509481985,2)))
        self.assertEqual(result['descriptive']['effect'],records[0]['value'])

    def test_bounded_signed_integer_edges_match_fraction_oracle(self):
        with fraction_reference() as reference:
            for x in (0,1,-1,2**8191,-2**8191,2**8192-1,-(2**8192-1)):
                self.assertEqual(current._bounded(x),reference._bounded(x))
                self.assertIs(type(current._bounded(x)),int)
            for x in (2**8192,-2**8192):
                for module in (reference,current):
                    with self.subTest(sign=x>0,module=module.__name__),self.assertRaises(ArithmeticError):
                        module._bounded(x)

    def test_prefix_overflow_is_not_hidden_by_later_integer_cancellation(self):
        source={'request':{'universe':{'instruments':['A','B','C']}},'cases':[
            {'status':'ELIGIBLE','outcome':q(x),'condition':True}
            for x in (2**8191,2**8191,-2**8191)]}
        with fraction_reference() as reference:
            for module in (reference,current):
                with self.subTest(module=module.__name__),self.assertRaises(ArithmeticError):
                    module._prefixes(source)

    def test_nonintegral_quantity_and_mixed_signs_keep_reference_draw_bytes(self):
        source=quantity_report([['0','0'],['1','-2'],['5','0'],['-1','2']],
                               [[True,None],[False,True],[True,False],[True,True]],
                               [[True,True]]*4,divisor=3)
        def run(module):
            records=[]
            result=module.calculate(source,self.design(),self.limits(31),on_draw=records.append)
            return canonical(result),[canonical(record) for record in records]
        self.paired(run)
        self.assertTrue(any(type(x) is Fraction and x.denominator!=1 for x in current._prefixes(source)[1]))

    def test_full_fixed_count_stream_is_identical_not_only_final_interval(self):
        source=binary_report(8)
        def run(module):
            stream=hashlib.sha256();count=0;undefined=0
            def sink(record):
                nonlocal count,undefined
                stream.update((canonical(record)+'\n').encode())
                count+=1;undefined+=record['value'] is None
            result=module.calculate(source,self.design(),self.limits(),on_draw=sink)
            return digest(result),stream.hexdigest(),count,undefined
        unused,checksum,count,undefined=self.paired(run)
        self.assertEqual(count,2*19999)
        self.assertEqual(len(checksum),64)
        self.assertGreaterEqual(undefined,0)

    def test_segment_budget_interruption_keeps_partial_ordinal_and_path(self):
        for cap in (1,2,7,23):
            def run(module):
                records=[]
                result=module.calculate(arithmetic_probe(),self.design(),self.limits(cap),on_draw=records.append)
                return canonical(result),[canonical(record) for record in records]
            with self.subTest(cap=cap):self.paired(run)

    def test_callback_cancellation_keeps_completed_draw_and_detached_hash(self):
        def run(module):
            source=arithmetic_probe();design=self.design();limits=self.limits()
            records=[];cancelled=[False]
            def sink(record):
                records.append(deepcopy(record))
                source['cases'].clear();design['randomness']['seed']=999;limits['max_segments']=1
                record['value']='untrusted callback mutation'
                if len(records)==3:cancelled[0]=True
            result=module.calculate(source,design,limits,stop=lambda:cancelled[0],on_draw=sink)
            return result,records
        result,records=self.paired(run)
        self.assertEqual(result['reason'],'caller_cancelled')
        self.assertEqual(len(records),3)
        self.assertEqual(result['cases'][0]['attempted'],3)
        self.assertEqual(result['cases'][0]['replicate_sha256'],hashlib.sha256(
            ''.join(canonical(x)+'\n' for x in records).encode()).hexdigest())
        self.assertIsNone(result['interval'])

    def test_preexisting_cancel_and_callback_exception_are_not_success(self):
        with fraction_reference() as reference:
            for module in (reference,current):
                stopped=module.calculate(binary_report(4),self.design(),self.limits(),stop=lambda:True)
                self.assertEqual(stopped['cases'],[])
                self.assertEqual(stopped['reason'],'caller_cancelled')
                seen=[]
                def failing(record):
                    seen.append(record)
                    raise RuntimeError('independent sink failure')
                with self.assertRaisesRegex(RuntimeError,'independent sink failure'):
                    module.calculate(binary_report(4),self.design(),self.limits(),on_draw=failing)
                self.assertEqual(len(seen),1)

    def test_public_malformed_numeric_and_boolean_metadata_still_fail_closed(self):
        source=binary_report(4)
        altered=[]
        bad=deepcopy(source);bad['state_counts']['ELIGIBLE']=True;altered.append(bad)
        bad=deepcopy(source);bad['cases'][0]['outcome']={'numerator':True,'denominator':'1'};altered.append(bad)
        bad=deepcopy(source);bad['cases'][0]['outcome']={'numerator':'2','denominator':'1'};altered.append(bad)
        with fraction_reference() as reference:
            for module in (reference,current):
                for bad in altered:
                    with self.subTest(module=module.__name__),self.assertRaises(module.Invalid):
                        module.calculate(bad,self.design(),self.limits(1))


if __name__=='__main__':unittest.main()
