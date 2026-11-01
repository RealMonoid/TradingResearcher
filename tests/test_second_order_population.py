"""Second-order dependence varies without changing the assigned contrast."""
from copy import deepcopy
from fractions import Fraction as F
import unittest

from test_source_process_scope import source_fixture
from trading_researcher.codec import Invalid
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.outcomes import _rational, _read_rational
from trading_researcher.population_models import build_model, generate_world
from trading_researcher.family_models import generate_family
from trading_researcher.second_order_population import specification, stationary_joint


def model(source=None,beta=F(1,2),share=F(1,2)):
    source=source_fixture() if source is None else source
    return build_model(source,diagnose(source,[1,2,4]),
        specification(2,beta,share,'Declared second-order stress, not market fit'),
        [_rational(x) for x in (F(0),F(1,20),F(1,10))])


class SecondOrderPopulationTests(unittest.TestCase):
    def assert_link(self,report):
        rows={(c['decision_time'],c['instrument']):c for c in report['cases']};compared=0
        for case in report['cases']:
            previous=rows.get((case['decision_time']-1800,case['instrument']))
            if previous and previous['outcome'] is not None and case['condition'] is not None:
                self.assertEqual(int(case['condition']),_read_rational(previous['outcome']));compared+=1
        self.assertGreater(compared,0)

    def test_signed_dependence_keeps_exact_effect_and_pair_law(self):
        for beta in (F(-1,2),F(0),F(1,2)):
            bound=model(beta=beta);q=_read_rational(bound['population']['q'])
            self.assertEqual(bound['status'],'MODEL_SPECIFIED')
            for row in bound['scenarios']:
                effect=_read_rational(row['effect'])
                law=stationary_joint([[_read_rational(x) for x in row['history_transitions']]],F(1,2))
                p=[_read_rational(x) for x in law['probabilities']]
                self.assertEqual(p,[_read_rational(x) for x in row['lag_pair_probabilities']])
                self.assertEqual(p[3]/q-q,effect)
                self.assertTrue(row['within_transition_capability'])

    def test_scalar_and_mixed_family_replay_with_shared_masks(self):
        source=source_fixture();bound=model(source,beta=F(-1,2));before=deepcopy((source,bound))
        world=generate_world(source,bound,2,96,2026102609)
        self.assert_link(world['report'])
        self.assertEqual(world,generate_world(source,bound,2,96,2026102609))
        self.assertEqual(world['initialization']['history_order'],2)
        items=[{'id':'null','scenario':0},{'id':'alternative','scenario':2}]
        family=generate_family(source,bound,items,96,2026102610)
        self.assertEqual(family,generate_family(source,bound,list(reversed(items)),96,2026102610))
        reports=[x['report'] for x in family['components']]
        for report in reports:self.assert_link(report)
        self.assertEqual([c['simulation_mask']['source_time_index'] for c in reports[0]['cases']],
                         [c['simulation_mask']['source_time_index'] for c in reports[1]['cases']])
        self.assertEqual((source,bound),before)
        self.assertEqual(family['outer_world_count'],1)
        self.assertFalse(family['scientific_readiness']);self.assertIsNone(family['n_min'])

    def test_missing_conditions_preserve_observed_complement_meaning(self):
        source=source_fixture();source['cases'][0]['condition']=None
        bound=model(source);q=_read_rational(bound['population']['q']);w=q*F(5,6)
        self.assertEqual(bound['population']['w'],_rational(w))
        self.assertEqual(bound['scenarios'][2]['p_other'],_rational(q-w*F(1,10)/(1-w)))
        self.assert_link(generate_world(source,bound,2,96,2026102611)['report'])

    def test_infeasible_history_law_is_not_clipped_or_replaced(self):
        bound=model(beta=F(-9,10))
        self.assertEqual(bound['status'],'MODEL_OR_INFORMATION_GAP')
        self.assertIn('infeasible_second_order_transition',bound['gaps'])
        self.assertTrue(any(not x['feasible'] for x in bound['scenarios']))
        with self.assertRaises(Invalid):generate_world(source_fixture(),bound,0,96,1)


if __name__=='__main__':unittest.main()
