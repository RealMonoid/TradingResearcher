"""Independent population identities, exact draw mappings and synthetic provenance."""
from copy import deepcopy
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid, digest
from trading_researcher.expressions import ExpressionGap
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.outcomes import _rational, reference_contrast
from trading_researcher import population_models as models


def fixture(name='six_time_hand_report'):
    data=json.loads((Path(__file__).parent/'fixtures/information_diagnostics_cases.json').read_text())
    return deepcopy(next(x for x in data['fixtures'] if x['id']==name)['report'])


def number(value):return F(int(value['numerator']),int(value['denominator']))


class IntegerStream:
    """Finite controlled integer draws; any floating random use is an error."""
    def __init__(self,size,values):
        self.size=size;self.values=list(values);self.position=0;self.bounds=[]

    def randrange(self,stop):
        self.bounds.append(stop)
        if stop==1:return 0
        if stop!=self.size:raise AssertionError(f'Unexpected integer bound {stop}, expected {self.size}')
        if self.position>=len(self.values):raise AssertionError('More latent/mask draws than declared')
        value=self.values[self.position];self.position+=1
        if not 0<=value<stop:raise AssertionError('Invalid controlled integer draw')
        return value

    def random(self):raise AssertionError('Floating random threshold used')


class PopulationModelAdversarialTests(unittest.TestCase):
    def model(self,report=None,effects=None,spec=None):
        report=fixture() if report is None else report
        effects=[F(0),F(1,20),F(1,10),F(-1,20),F(-1,10)] if effects is None else effects
        spec=models.specification(1,F(0),F(1),'Explicit independent stress fixture; not a fitted market model.') if spec is None else spec
        return models.build_model(report,diagnose(report,[1,2]),spec,[_rational(x) for x in effects])

    def test_exact_population_truth_accounts_for_unknown_and_all_signed_scenarios(self):
        model=self.model()
        expected=[('3/7','3/7'),('67/140','38/105'),('37/70','31/105'),('53/140','52/105'),('23/70','59/105')]
        self.assertEqual(model['status'],'MODEL_SPECIFIED')
        self.assertEqual(model['population']['q'],_rational(F(3,7)))
        self.assertEqual(model['population']['w'],_rational(F(4,7)))
        self.assertEqual(model['lattice_size'],'420')
        for scenario,(pt,po) in zip(model['scenarios'],expected):
            self.assertEqual(scenario['p_true'],_rational(F(pt)))
            self.assertEqual(scenario['p_other'],_rational(F(po)))
            baseline=F(4,7)*F(pt)+F(3,7)*F(po)
            self.assertEqual(baseline,F(3,7))
            self.assertEqual(F(pt)-baseline,number(scenario['effect']))
        self.assertTrue(model['observed_negative_products'])
        self.assertEqual(model['assumption_status'],'DECLARED_STRESS_NOT_FITTED_OR_VALIDATED')
        self.assertIsNone(model['n_min'])
        self.assertFalse(model['classification_permitted'])

    def test_common_lattice_covariance_hand_identity_is_not_realized_sample_truth(self):
        # Independently enumerate U_common,U_A,U_B in {0,...,4}, plus two
        # independent half-probability choices. No production generator is used
        # to calculate this fixed common-share identity.
        pairs=[]
        for common,private_a,private_b,choice_a,choice_b in product(range(5),range(5),range(5),(0,1),(0,1)):
            a=int((common if choice_a else private_a)<3)
            b=int((common if choice_b else private_b)<2)
            pairs.append((a,b))
        self.assertEqual(len(pairs),500)
        mean_a=F(sum(a for a,b in pairs),500);mean_b=F(sum(b for a,b in pairs),500)
        covariance=F(sum(a*b for a,b in pairs),500)-mean_a*mean_b
        self.assertEqual((mean_a,mean_b,covariance),(F(3,5),F(2,5),F(1,25)))
        world=models.generate_world(fixture(),self.model(),2,2,11)
        self.assertEqual(world['truth']['effect'],_rational(F(1,10)))
        # At most two eligible rows survive this finite artificial horizon;
        # their sample contrast is undefined, zero or a half, never 1/10.
        self.assertNotEqual(world['descriptive']['effect'],world['truth']['effect'])

    def test_exact_bernoulli_mapping_enumerates_every_integer_atom(self):
        for probability in (F(0),F(1),F(1,3),F(2,5),F(999,1000)):
            class Cycle:
                def __init__(self):self.value=0;self.bounds=[]
                def randrange(self,bound):
                    self.bounds.append(bound);value=self.value;self.value+=1;return value
                def random(self):raise AssertionError('Floating threshold used')
            rng=Cycle()
            values=[models._bernoulli(rng,probability) for _ in range(probability.denominator)]
            self.assertEqual(sum(values),probability.numerator)
            self.assertEqual(rng.bounds,[probability.denominator]*probability.denominator)

    def test_joint_mask_sequence_and_latent_updates_include_ineligible_times(self):
        report=fixture();model=self.model();before=deepcopy([report,model])
        mask=IntegerStream(6,[0,1,2,3,4,5,0,1,2])
        common=IntegerStream(420,[0,200,419,0,419,419,0,200,0])
        private={name:IntegerStream(420,[0]*9) for name in ('A','B')}
        choices={name:IntegerStream(1,[]) for name in ('A','B')}
        def rng(seed,component):
            if component=='joint-mask':return mask
            if component=='common-latent':return common
            if component[0]=='instrument-latent':return private[component[1]]
            if component[0]=='common-choice':return choices[component[1]]
            raise AssertionError('Undeclared randomness component')
        with patch.object(models,'_rng',side_effect=rng):
            world=models.generate_world(report,model,2,8,17)
        cases=world['report']['cases']
        self.assertEqual([c['simulation_mask']['source_time_index'] for c in cases],
                         [i for i in (0,1,2,3,4,5,0,1) for _ in range(2)])
        wanted=[1,1,0,1,None,None,1,1,0,None,None,None,1,1,None,None]
        self.assertEqual([number(c['outcome']) if c['outcome'] is not None else None for c in cases],wanted)
        self.assertEqual(common.position,9)
        self.assertEqual(mask.position,9)
        self.assertEqual([private[name].position for name in ('A','B')],[9,9])
        self.assertEqual(world['terminal_censored_cases'],2)
        self.assertEqual([report,model],before)
        self.assertFalse(world['report']['simulation']['raw_AST_executed'])
        self.assertEqual(world['report']['primitive_steps'],0)
        self.assertEqual(world['report']['request']['candidate_ref'],'synthetic-population:'+digest(model))
        for key in ('scope_program','condition_program','outcome_program'):
            self.assertNotEqual(world['report']['request'][key],report['request'][key])

    def test_source_boundary_and_outcome_gap_map_separately_from_artificial_maturity(self):
        report=fixture('six_time_raw_coherent');model=self.model(report)
        lattice=int(model['lattice_size']);mask=IntegerStream(6,[5,1,2,4,0])
        def rng(seed,component):
            if component=='joint-mask':return mask
            if component=='common-latent' or component[0]=='instrument-latent':
                return IntegerStream(lattice,[0]*5)
            return IntegerStream(1,[])
        with patch.object(models,'_rng',side_effect=rng):
            world=models.generate_world(report,model,2,4,19)
        cases=world['report']['cases']
        self.assertEqual([c['status'] for c in cases],
            ['OUTCOME_MISSING']*4+['DATA_GAP']*2+['PARTITION_BOUNDARY']*2)
        self.assertEqual([c['simulation_mask']['source_status'] for c in cases],
            ['PARTITION_BOUNDARY']*2+['DATA_GAP']*4+['ELIGIBLE','OUTCOME_MISSING'])
        self.assertTrue(all(c['outcome'] is None for c in cases))
        self.assertEqual(world['descriptive']['status'],'INFORMATION_GAP')
        self.assertEqual(world['descriptive']['scope_count'],0)
        self.assertEqual(world['status'],'GENERATED_UNCALIBRATED')
        self.assertEqual(world['terminal_censored_cases'],2)
        self.assertEqual(world['truth']['effect'],_rational(F(1,10)))

    def test_persistent_chains_and_circular_mask_continuation_use_declared_integer_choices(self):
        class Routed:
            def __init__(self,values):self.values={bound:iter(items) for bound,items in values.items()}
            def randrange(self,bound):
                if bound==1:return 0
                if bound not in self.values:raise AssertionError('Undeclared integer bound')
                return next(self.values[bound])
            def random(self):raise AssertionError('Floating random threshold used')
        report=fixture()
        for share,expected in [(0,[None,None,0,1,1,0,None,None]),
                               (1,[None,None,1,1,0,0,None,None])]:
            model=self.model(report,spec=models.specification(2,F(1,2),share,'Fixed transition oracle'))
            mask=Routed({6:[5,4],2:[1,1,0,1]})
            common=Routed({420:[0,419,0],2:[0,1,0,1]})
            private={'A':Routed({420:[419,0,419],2:[0,1,0,1]}),
                     'B':Routed({420:[0,419,0],2:[0,1,0,1]})}
            def rng(seed,component):
                if component=='joint-mask':return mask
                if component=='common-latent':return common
                if component[0]=='instrument-latent':return private[component[1]]
                return Routed({})
            with patch.object(models,'_rng',side_effect=rng):
                world=models.generate_world(report,model,2,4,31)
            self.assertEqual([c['simulation_mask']['source_time_index'] for c in world['report']['cases']],
                             [5,5,0,0,1,1,4,4])
            self.assertEqual([number(c['outcome']) if c['outcome'] is not None else None
                              for c in world['report']['cases']],expected)

    def test_returned_model_does_not_alias_supplied_diagnostics(self):
        report=fixture();diagnostics=diagnose(report,[1,2]);before=deepcopy(diagnostics)
        model=models.build_model(report,diagnostics,models.specification(2,0,0,'Detached output fixture'),[_rational(0)])
        model['diagnostics']['totals']['scope']['successes']=999
        self.assertEqual(diagnostics,before)
        with self.assertRaises(Invalid):models.generate_world(report,model,0,20,1)

    def test_malformed_or_missing_model_fields_fail_with_controlled_validation(self):
        report=fixture();model=self.model(report)
        for value in (None,[],{}, {'schema':models.MODEL}):
            with self.subTest(value=value),self.assertRaises((Invalid,ExpressionGap)):
                models.generate_world(report,value,0,20,1)
        for key in ('specification','diagnostics','effects','population','scenarios','lattice_size'):
            changed=deepcopy(model);changed.pop(key)
            with self.subTest(missing=key),self.assertRaises((Invalid,ExpressionGap)):
                models.generate_world(report,changed,0,20,1)

    def test_large_exact_lattice_retains_resource_gap_without_decimal_conversion(self):
        effects=[F(1,10**2000+d) for d in (1,3,7)]
        model=self.model(effects=effects)
        self.assertEqual(model['status'],'MODEL_OR_INFORMATION_GAP')
        self.assertIn('exact_lattice_resource_envelope',model['gaps'])
        self.assertIsNone(model['lattice_size'])
        self.assertEqual(model['effects'],[_rational(x) for x in effects])
        self.assertEqual(len(model['scenarios']),3)
        with self.assertRaises(Invalid):models.generate_world(fixture(),model,0,20,1)

    def test_degenerate_and_infeasible_scenarios_are_not_repaired_or_selected_away(self):
        for name,gap in [('no_true_condition','no_conditioned_cases'),('all_zero_observed_binary','degenerate_scope_rate')]:
            report=fixture(name);model=self.model(report)
            self.assertEqual(model['status'],'MODEL_OR_INFORMATION_GAP')
            self.assertIn(gap,model['gaps'])
            with self.assertRaises(Invalid):models.generate_world(report,model,0,20,1)
        model=self.model(effects=[F(0),F(1),F(-1)])
        self.assertEqual(len(model['scenarios']),3)
        self.assertEqual([row['feasible'] for row in model['scenarios']],[True,False,False])
        self.assertGreater(number(model['scenarios'][1]['p_true']),1)
        self.assertLess(number(model['scenarios'][2]['p_true']),0)
        with self.assertRaises(Invalid):models.generate_world(fixture(),model,0,20,1)

    def test_specification_seed_scenario_and_bound_source_validation(self):
        report=fixture();model=self.model(report)
        for field,value in [('persistence',_rational(F(-1,3))),('persistence',_rational(1)),
                            ('common_share',_rational(F(4,3))),('common_share',True),
                            ('persistence',_rational(F(1,1000001))),('mask_mean_block',True),('rationale','')]:
            spec=deepcopy(model['specification']);spec[field]=value
            with self.subTest(field=field,value=value),self.assertRaises((Invalid,ExpressionGap)):
                models.build_model(report,diagnose(report,[1,2]),spec,model['effects'])
        for scenario,rows,seed in [(-1,20,1),(True,20,1),(5,20,1),(0,1,1),(0,20,1<<256),(0,20,True)]:
            with self.subTest(scenario=scenario,rows=rows,seed=seed),self.assertRaises(Invalid):
                models.generate_world(report,model,scenario,rows,seed)
        changed=deepcopy(report);changed['cases'][0]['reason']='different_retained_source'
        with self.assertRaises(Invalid):models.generate_world(changed,model,0,20,1)
        changed=deepcopy(model);changed['scenarios'][0]['p_true']=_rational(F(1,2))
        with self.assertRaises(Invalid):models.generate_world(report,changed,0,20,1)


if __name__=='__main__':unittest.main()
