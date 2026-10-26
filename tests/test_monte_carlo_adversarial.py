"""Independent MC rank/stability probes; no market calibration or admission."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
from math import comb
import random
import unittest
from unittest.mock import patch

import test_bootstrap_runs as owned_support
from trading_researcher.codec import Invalid, decode
from trading_researcher.errors import Conflict, Denied
from trading_researcher import bootstrap_runs
from trading_researcher import monte_carlo as mc


def rational(value):
    value = Fraction(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def value(encoded):
    return None if encoded is None else Fraction(int(encoded['numerator']), int(encoded['denominator']))


def config(direction='positive', beta=Fraction(1, 100), delta=Fraction(1, 20)):
    return {'schema': 'mc-boundary-policy/1', 'noncoverage': rational(beta),
            'delta': rational(delta), 'direction': direction}


def exact_rank_oracle(n, p, tail):
    """Independent small-n enumeration, not the production recurrence/reflection."""
    probabilities = [Fraction(comb(n, k)) * p ** k * (1-p) ** (n-k) for k in range(n+1)]
    lower = max(r for r in range(n+1) if sum(probabilities[:r]) <= tail)
    upper = min(r for r in range(1, n+2) if sum(probabilities[r:]) <= tail)
    return [lower, upper]


class MonteCarloAdversarialTests(unittest.TestCase):
    def test_hand_calculated_rank_boundaries_and_unbounded_sentinels(self):
        # P(Bin(4,1/2)=0)=1/16: equality admits rank1; a tighter tail does not.
        cases = [(1,Fraction(1,2),Fraction(1,4),[0,2]),
                 (4,Fraction(1,2),Fraction(1,16),[1,4]),
                 (4,Fraction(1,2),Fraction(1,17),[0,5]),
                 (5,Fraction(1,4),Fraction(1,8),[0,3]),
                 (5,Fraction(3,4),Fraction(1,8),[3,6])]
        for n,p,tail,expected in cases:
            with self.subTest(n=n,p=p,tail=tail):
                self.assertEqual(mc.rank_bounds(n,rational(p),rational(tail)), expected)

    def test_small_n_exhaustive_exact_binomial_oracle(self):
        for n,p,tail in product(range(1,13),
                (Fraction(1,10),Fraction(1,4),Fraction(1,2),Fraction(3,4),Fraction(9,10)),
                (Fraction(1,100),Fraction(1,16),Fraction(1,4))):
            with self.subTest(n=n,p=p,tail=tail):
                self.assertEqual(mc.rank_bounds(n,rational(p),rational(tail)), exact_rank_oracle(n,p,tail))

    def test_rank_reflection_and_tighter_tail_nesting(self):
        for n,p in product((2,7,19,100), (Fraction(1,40),Fraction(1,4),Fraction(1,2))):
            left = mc.rank_bounds(n,rational(p),rational(Fraction(1,100)))
            right = mc.rank_bounds(n,rational(1-p),rational(Fraction(1,100)))
            self.assertEqual(right, [n+1-left[1],n+1-left[0]])
            tight = mc.rank_bounds(n,rational(p),rational(Fraction(1,1000)))
            self.assertLessEqual(tight[0],left[0])
            self.assertGreaterEqual(tight[1],left[1])

    def test_constant_sample_does_not_clip_unbounded_quantile_band(self):
        band = mc.quantile_band([rational(7)],rational(Fraction(1,2)),rational(Fraction(1,4)))
        self.assertEqual(band, {'ranks':[0,2], 'lower':None, 'upper':None})

    def test_atoms_have_conservative_exact_coverage(self):
        # Exhaust all 32 samples from P(X=0)=1/4, P(X=1)=3/4. The left
        # population quantile at p=1/4 is0; at p=1/2 it is1.
        for p,q in ((Fraction(1,4),0),(Fraction(1,2),1)):
            missed = Fraction(0)
            for sample in product((0,1),repeat=5):
                band = mc.quantile_band([rational(x) for x in sample],rational(p),rational(Fraction(1,8)))
                low,high = value(band['lower']),value(band['upper'])
                if (low is not None and low>q) or (high is not None and high<q):
                    missed += Fraction(1,4)**sample.count(0) * Fraction(3,4)**sample.count(1)
            self.assertLessEqual(missed,Fraction(1,4))

    def test_rank_resource_and_scalar_envelopes(self):
        invalid = [(True,Fraction(1,2),Fraction(1,10)),(0,Fraction(1,2),Fraction(1,10)),
                   (20000,Fraction(1,2),Fraction(1,10)),(2,True,Fraction(1,10)),
                   (2,Fraction(1,2),True),(2,Fraction(-1,2),Fraction(1,10)),
                   (2,Fraction(3,2),Fraction(1,10)),(2,Fraction(1,2),Fraction(0)),
                   (2,Fraction(1,2**32+1),Fraction(1,10))]
        for args in invalid:
            with self.subTest(args=args),self.assertRaises(Invalid):
                mc.rank_bounds(args[0],rational(args[1]) if type(args[1]) is Fraction else args[1],
                               rational(args[2]) if type(args[2]) is Fraction else args[2])

    def test_config_rejects_untyped_unknown_and_unbounded_policies(self):
        cases = [None,{},config(beta=Fraction(0)),config(beta=Fraction(1)),
                 config(beta=Fraction(1,1000001)),config(delta=0),config(delta=-1)]
        for key,bad in (('schema','other'),('direction',{}),('direction',True),
                        ('noncoverage',True),('delta',{'numerator':True,'denominator':'1'})):
            altered=config();altered[key]=bad;cases.append(altered)
        altered=config();altered['scientific_readiness']=True;cases.append(altered)
        for policy in cases:
            with self.subTest(policy=policy),self.assertRaises(Invalid):
                mc.validate_config(policy)

    def test_fixed_full_count_constant_draws_obey_exact_directional_boundaries(self):
        draws={1:[rational(0)]*19999}
        for direction,estimate,expected in [
                ('positive',Fraction(1,40),'TESTED_INCONCLUSIVE'),
                ('negative',Fraction(-1,40),'TESTED_INCONCLUSIVE'),
                ('nondirectional',Fraction(1,40),'TESTED_NEGATIVE'),
                ('nondirectional',Fraction(-1,40),'TESTED_NEGATIVE'),
                ('positive',Fraction(1,40)+Fraction(1,10**20),'SUPPORTED_INITIAL'),
                ('positive',Fraction(1,40)-Fraction(1,10**20),'TESTED_NEGATIVE')]:
            with self.subTest(direction=direction,estimate=estimate):
                result=mc.diagnose(rational(estimate),draws,rational(Fraction(1,20)),config(direction))
                self.assertEqual(result['status'],'ASSESSED_UNCALIBRATED')
                self.assertIs(result['boundary_stable'],True)
                self.assertEqual(result['nominal_classification'],expected)
                for name in ('scientific_readiness','classification_permitted','selective_reseeding_permitted'):
                    self.assertIs(result[name],False)

    def test_decisive_finite_interval_is_unstable_when_rank_band_crosses_delta(self):
        # n19999, type7 p.975 has zero-based rank19498.05; 19499 zeros
        # then500 ones produce q=.05. Estimate.1 gives [.15,.2]. The
        # exact rank band straddles the step, admitting lower endpoints -.8.. .2.
        draws={1:[rational(0)]*19499+[rational(1)]*500}
        result=mc.diagnose(rational(Fraction(1,10)),draws,rational(Fraction(1,20)),config())
        self.assertEqual(result['nominal_classification'],'SUPPORTED_INITIAL')
        self.assertIs(result['boundary_stable'],False)
        self.assertEqual(list(map(value,result['endpoint_bounds']['lower'])),[Fraction(-4,5),Fraction(1,5)])
        self.assertEqual(list(map(value,result['endpoint_bounds']['upper'])),[Fraction(1,5),Fraction(1,5)])

    def test_point_endpoint_is_included_when_population_band_ends_before_interpolation(self):
        # Very small p: rank upper1 can bound q by the observed minimum0,
        # while finite type7 interpolation is19998/10000000>0.
        result=mc.diagnose(rational(0),{1:[rational(0)]+[rational(1)]*19998},
                           rational(Fraction(1,5000000)),config())
        self.assertEqual(value(result['endpoint_bounds']['upper'][0]),Fraction(-9999,5000000))
        self.assertIsNone(result['endpoint_bounds']['upper'][1])
        self.assertIs(result['boundary_stable'],False)

    def test_undefined_and_incomplete_draws_cannot_be_filtered_into_stability(self):
        incomplete=[rational(0)]*19998
        undefined=[rational(0)]*19999;undefined[9999]=None
        for draws in ({1:incomplete},{1:undefined},{1:[rational(0)]*19999,2:undefined}):
            with self.subTest(lengths=list(draws)):
                result=mc.diagnose(rational(0),draws,rational(Fraction(1,20)),config())
                self.assertEqual(result['status'],'NOT_ASSESSED')
                self.assertIsNone(result['boundary_stable'])
                self.assertIs(result['scientific_readiness'],False)
                self.assertIs(result['classification_permitted'],False)

    def test_joint_sensitivity_enclosure_and_tail_allocation(self):
        # Individual point intervals are.2 and0. Enclosing both gives[0,.2],
        # hence inconclusive even though either individually is decisive.
        result=mc.diagnose(rational(Fraction(1,10)),
                {1:[rational(0)]*19999,2:[rational(Fraction(1,5))]*19999},
                rational(Fraction(1,20)),config())
        self.assertEqual(result['nominal_classification'],'TESTED_INCONCLUSIVE')
        self.assertIs(result['boundary_stable'],True)
        self.assertEqual(list(map(value,result['endpoint_bounds']['lower'])),[Fraction(0),Fraction(0)])
        self.assertEqual(list(map(value,result['endpoint_bounds']['upper'])),[Fraction(1,5),Fraction(1,5)])
        expected=mc.rank_bounds(19999,rational(Fraction(1,40)),rational(Fraction(1,800)))
        for case in result['cases']:
            self.assertEqual(case['quantiles']['lower']['ranks'],expected)

    def test_diagnosis_is_detached_deterministic_and_does_not_use_randomness(self):
        draws={2:[rational(0)]*19999,1:[rational(0)]*19999}
        policy=config();original=deepcopy((draws,policy));state=random.getstate()
        one=mc.diagnose(rational(0),draws,rational(Fraction(1,20)),policy)
        two=mc.diagnose(rational(0),dict(reversed(list(draws.items()))),rational(Fraction(1,20)),policy)
        self.assertEqual(one,two)
        self.assertEqual((draws,policy),original)
        self.assertEqual(random.getstate(),state)

    def test_stable_endpoint_boxes_never_contain_distinct_feasible_classifications(self):
        grid=[Fraction(-2),Fraction(-1),Fraction(-1,2),Fraction(0),Fraction(1,2),Fraction(1),Fraction(2)]
        def independent_classification(low,high,direction):
            if direction=='negative':low,high=-high,-low
            if direction=='nondirectional':
                if low>1 or high<-1:return 'support'
                if low>=-1 and high<=1:return 'negative'
            else:
                if low>1:return 'support'
                if high<1:return 'negative'
            return 'inconclusive'
        for ll,lu,ul,uu in product(grid,repeat=4):
            if ll>lu or ul>uu or ll>uu:continue
            bounds={'lower':[rational(ll),rational(lu)],'upper':[rational(ul),rational(uu)]}
            lows={ll,lu,(ll+lu)/2,*[x for x in (-1,1) if ll<=x<=lu]}
            highs={ul,uu,(ul+uu)/2,*[x for x in (-1,1) if ul<=x<=uu]}
            for direction in ('positive','negative','nondirectional'):
                if mc._stable(bounds,Fraction(1),direction):
                    outcomes={independent_classification(low,high,direction)
                              for low,high in product(lows,highs) if low<=high}
                    self.assertEqual(len(outcomes),1,(bounds,direction,outcomes))

    def test_sensitivity_identity_and_numeric_values_are_strict(self):
        for draws in ({True:[rational(0)]*19999},{0:[rational(0)]*19999},
                      {k:[rational(0)]*19999 for k in range(1,5)},
                      {1:[rational(0)]*20000},{1:[True]*19999}):
            with self.subTest(keys=list(draws)),self.assertRaises(Invalid):
                mc.diagnose(rational(0),draws,rational(Fraction(1,20)),config())

    def test_exact_endpoint_overflow_does_not_produce_a_stability_verdict(self):
        with self.assertRaises(Invalid):
            mc.diagnose(rational(2**8192-1),{1:[rational(0)]*19999},
                        rational(Fraction(1,20)),config())

    def test_validated_config_does_not_share_nested_caller_state(self):
        original=config();accepted=mc.validate_config(original)
        original['noncoverage']['numerator']='99'
        original['delta']['numerator']='99'
        self.assertEqual(accepted,config())


class OwnedMonteCarloAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        owned_support.BootstrapRunTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        owned_support.BootstrapRunTests.tearDownClass.__func__(cls)

    @classmethod
    def op(cls,operation,**args):
        return cls.broker.call(cls.token,operation,**args)

    def args(self,key):
        return {**owned_support.BootstrapRunTests.args(self,key),
                'limits':{'max_seconds':180,'max_segments':1},
                'mc_policy':{'schema':'mc-boundary-policy/1','noncoverage':rational(Fraction(1,100))}}

    def retained(self,schema,key):
        values=[]
        for row in self.broker._db.execute('SELECT envelope FROM artifacts'):
            record=decode(row['envelope']);body=record.get('body')
            if type(body) is dict and body.get('schema')==schema and body.get('request',{}).get('key')==key:
                values.append(record)
        return values

    def test_caller_cannot_replace_owned_delta_direction_or_role(self):
        with patch.object(bootstrap_runs,'run_child',side_effect=AssertionError('invalid policy launched')) as launch:
            for field,replacement in (('delta',rational(1)),('direction','negative')):
                args=self.args('independent-mc-forbidden-'+field);args['mc_policy'][field]=replacement
                with self.subTest(field=field),self.assertRaises(Invalid):
                    self.op('run_development_bootstrap',**args)
                self.assertEqual(self.retained('bootstrap-input/1',args['key']),[])
            launch.assert_not_called()
        worker=self.op('register_worker',name='independent-no-mc',role='discovery',
                       capabilities=['research-record/v1'])['token']
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('worker reached blobs')):
            with self.assertRaises(Denied):
                self.broker.call(worker,'run_development_bootstrap',**self.args('independent-mc-worker'))

    def test_interrupted_policy_is_durable_detached_and_replayed_without_checkout(self):
        args=self.args('independent-mc-interrupted');expected=deepcopy(args)
        criterion=self.plan['body']['plan']['effect_criterion']
        expected_config={**expected['mc_policy'],'delta':criterion['delta'],'direction':criterion['direction']}
        def interrupted(*unused,**kwargs):
            capsule=self.retained('bootstrap-input/1',expected['key'])
            self.assertEqual(len(capsule),1)
            self.assertEqual(capsule[0]['body']['request'],expected)
            self.assertEqual(capsule[0]['body']['payload']['design']['mc_policy'],expected_config)
            args['mc_policy']['noncoverage']['numerator']='2'
            raise RuntimeError('independent MC interruption')
        with patch.object(bootstrap_runs,'run_child',side_effect=interrupted),self.assertRaises(RuntimeError):
            self.op('run_development_bootstrap',**args)
        with self.assertRaises(Conflict):
            self.op('run_development_bootstrap',**args)
        self.assertEqual(self.retained('development-bootstrap/1',expected['key']),[])
        with patch.object(bootstrap_runs,'source_bundle',side_effect=AssertionError('retained retry used checkout')):
            saved=self.op('run_development_bootstrap',**expected)
        diagnostic=saved['body']['result']['monte_carlo']
        self.assertEqual(saved['body']['request'],expected)
        self.assertEqual(diagnostic['config'],expected_config)
        self.assertEqual(diagnostic['status'],'NOT_ASSESSED')
        self.assertIsNone(diagnostic['boundary_stable'])
        self.assertIs(saved['body']['scientific_readiness'],False)

    def test_returned_stability_or_policy_cannot_be_forged_on_resource_stop(self):
        original=bootstrap_runs.run_child
        for mode in ('status','policy'):
            args=self.args('independent-mc-forged-'+mode);observed=[]
            def changed(*parameters,**kwargs):
                report,raw=original(*parameters,**kwargs)
                self.assertEqual(report['result']['status'],'RESOURCE_STOP')
                altered=deepcopy(report)
                if mode=='status':
                    altered['result']['monte_carlo'].update(status='ASSESSED_UNCALIBRATED',boundary_stable=True,
                                                          nominal_classification='SUPPORTED_INITIAL')
                else:
                    altered['result']['monte_carlo']['config']['noncoverage']=rational(Fraction(1,2))
                observed.append(altered)
                return altered,raw
            with self.subTest(mode=mode),patch.object(bootstrap_runs,'run_child',side_effect=changed),self.assertRaises(Invalid):
                self.op('run_development_bootstrap',**args)
            self.assertEqual(len(observed),1)
            self.assertEqual(self.retained('development-bootstrap/1',args['key']),[])
            self.assertEqual(len(self.retained('bootstrap-input/1',args['key'])),1)

    def test_legacy_request_without_policy_stays_unassessed(self):
        args=self.args('independent-mc-legacy');del args['mc_policy']
        saved=self.op('run_development_bootstrap',**args)
        result=saved['body']['result']
        self.assertEqual(result['schema'],'joint-bootstrap-computation/1')
        self.assertNotIn('monte_carlo',result)
        self.assertEqual(result['numerics']['boundary_instability'],'not_assessed_no_classification')
        capsule=self.retained('bootstrap-input/1',args['key'])[0]
        self.assertNotIn('mc_policy',capsule['body']['payload']['design'])
        self.assertIs(result['classification_permitted'],False)


if __name__ == '__main__':
    unittest.main()
