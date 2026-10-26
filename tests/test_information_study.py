"""Fixed study inventory, uncertainty and conservative resource accounting."""
from copy import deepcopy
from fractions import Fraction
import unittest

from trading_researcher.codec import Invalid
from trading_researcher.outcomes import _rational
from trading_researcher.population_models import specification
from trading_researcher.information_study import make_manifest,outer_interval,summarize,budget_state


def assigned():
    return {'input_binding':'a'*64,'base_length':4,'primary_count':1,'delta':_rational(Fraction(1,20)),
        'direction':'positive','horizon_bars':1,'available_time_rows':96,'instruments':1}


def profile():
    return {'specifications':[specification(4,0,0,'Fixed independent stress fixture')],
        'targets':[16,32],'worlds_per_cell':2,'seed':1,'mc_noncoverage':_rational(Fraction(1,100)),
        'outer_noncoverage':_rational(Fraction(1,20)),
        'budget':{'max_compute_ms':120000,'attempt_compute_ms':10000,'max_storage_bytes':1024*1024*1024,
            'attempt_storage_bytes':64*1024*1024,'max_attempts':2},
        'cost_estimate':{'source_ref':'fixed-engineering-estimate','world_time_rows':128,
            'observed_compute_ms':20000,'observed_storage_bytes':20*1024*1024,
            'qualification':'Measured smaller workload is not a whole-study runtime guarantee.'}}


class InformationStudyTests(unittest.TestCase):
    def test_manifest_has_complete_fixed_inventory_and_distinct_seed_streams(self):
        manifest=make_manifest(assigned(),profile())
        self.assertEqual(len(manifest['worlds']),12)
        self.assertEqual(manifest,make_manifest(assigned(),profile()))
        self.assertEqual(len({x['id'] for x in manifest['worlds']}),12)
        seeds=[x[key] for x in manifest['worlds'] for key in ('population_seed','bootstrap_seed')]
        self.assertEqual(len(set(seeds)),24)
        self.assertEqual([x['effect'] for x in manifest['worlds'][:6]],
            [_rational(x) for x in (0,0,Fraction(1,20),Fraction(1,20),Fraction(1,10),Fraction(1,10))])
        self.assertFalse(manifest['scientific_readiness'])

    def test_outward_interval_endpoint_hand_cases(self):
        result=outer_interval(0,1,_rational(Fraction(1,20)),bits=8)
        self.assertEqual(result['lower'],_rational(0))
        self.assertEqual(result['upper'],_rational(Fraction(125,128)))
        reflected=outer_interval(1,1,_rational(Fraction(1,20)),bits=8)
        self.assertEqual(reflected['lower'],_rational(Fraction(3,128)))
        self.assertEqual(reflected['upper'],_rational(1))

    def test_no_partial_grid_nomination(self):
        manifest=make_manifest(assigned(),profile())
        results=[{'world_id':world['id'],'state':'VERIFIED','decision':'SUPPORTED_INITIAL',
            'scope_count':10,'condition_count':4,'covered':True} for world in manifest['worlds']]
        partial=summarize(manifest,results[:-1])
        self.assertFalse(partial['complete'])
        self.assertIsNone(partial['candidate_time_rows'])
        complete=summarize(manifest,results)
        self.assertTrue(complete['complete'])
        self.assertEqual(complete['candidate_time_rows'],16)
        self.assertIsNone(complete['n_min'])
        with self.assertRaises(Invalid):summarize(manifest,[*results,results[0]])

    def test_reservations_are_charged_until_settled(self):
        manifest=make_manifest(assigned(),profile())
        reservation={'attempt_id':'a','world_id':manifest['worlds'][0]['id'],
            'compute_ms':10000,'storage_bytes':64*1024*1024}
        usage=budget_state(manifest,[reservation],[])
        self.assertEqual(usage['charged_compute_ms'],10000)
        self.assertEqual(usage['outstanding_attempts'],['a'])
        settlement={'attempt_id':'a','compute_ms':2000,'storage_bytes':10000,'usage_known':True}
        usage=budget_state(manifest,[reservation],[settlement])
        self.assertEqual(usage['charged_compute_ms'],2000)
        self.assertEqual(usage['outstanding_attempts'],[])
        unknown={**settlement,'usage_known':False}
        self.assertEqual(budget_state(manifest,[reservation],[unknown])['charged_compute_ms'],10000)

    def test_profile_cannot_change_effects_grid_or_boolean_counts(self):
        for changes in ({'targets':[32,16]},{'targets':[16,16]},{'targets':[97]},
                        {'worlds_per_cell':True},{'seed':True}):
            with self.subTest(changes=changes),self.assertRaises(Invalid):
                make_manifest(assigned(),{**profile(),**changes})
        with self.assertRaises(Invalid):make_manifest({**assigned(),'primary_count':9},profile())


if __name__=='__main__':unittest.main()
