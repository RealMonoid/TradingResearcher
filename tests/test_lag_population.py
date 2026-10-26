"""The declared law preserves the recognized lag identity, including under gaps."""
from copy import deepcopy
from fractions import Fraction as F
import unittest

from test_source_process_scope import source_fixture
from trading_researcher.codec import Invalid
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.outcomes import _rational, _read_rational
from trading_researcher.population_models import build_model, generate_world
from trading_researcher.family_models import generate_family
from trading_researcher.lag_population import specification


def model(source=None, share=F(1, 2)):
    source=source_fixture() if source is None else source
    return build_model(source,diagnose(source,[1,2]),specification(2,share,'Declared linked-value stress, not market fit'),
                       [_rational(x) for x in (F(0),F(1,20),F(1,10))])


class LagPopulationTests(unittest.TestCase):
    def assert_link(self, report, shift=2):
        lookup={(c['decision_time'],c['instrument']):c for c in report['cases']}
        compared=0
        for case in report['cases']:
            prior=lookup.get((case['decision_time']-900*shift,case['instrument']))
            if prior is not None and prior['outcome'] is not None and case['condition'] is not None:
                self.assertEqual(int(case['condition']),_read_rational(prior['outcome']))
                compared+=1
        self.assertGreater(compared,0)

    def test_world_preserves_shift_and_replays_without_modifying_inputs(self):
        source=source_fixture();bound=model(source);before=deepcopy((source,bound))
        self.assertEqual(bound['status'],'MODEL_SPECIFIED')
        self.assertEqual(bound['lag_bars'],2)
        self.assertEqual(bound['population']['w'],bound['population']['q'])
        world=generate_world(source,bound,2,96,2026102602)
        self.assert_link(world['report'])
        self.assertEqual(world,generate_world(source,bound,2,96,2026102602))
        self.assertEqual((source,bound),before)
        self.assertFalse(world['scientific_readiness'])
        self.assertIsNone(world['n_min'])
        self.assertFalse(world['report']['simulation']['raw_AST_executed'])

    def test_family_has_response_specific_condition_values_and_shared_mask_positions(self):
        source=source_fixture();bound=model(source)
        components=[{'id':'null','scenario':0},{'id':'effect','scenario':2}]
        family=generate_family(source,bound,components,96,2026102603)
        self.assertEqual(family,generate_family(source,bound,list(reversed(components)),96,2026102603))
        reports=[item['report'] for item in family['components']]
        for report in reports:self.assert_link(report)
        self.assertTrue(any(a['condition']!=b['condition'] for a,b in zip(reports[0]['cases'],reports[1]['cases'])))
        self.assertEqual([c['simulation_mask']['source_time_index'] for c in reports[0]['cases']],
                         [c['simulation_mask']['source_time_index'] for c in reports[1]['cases']])
        self.assertEqual(family['outer_world_count'],1)

    def test_unknown_condition_changes_observed_other_group_not_latent_transition(self):
        source=source_fixture()
        source['cases'][0]['condition']=None
        bound=model(source);q=_read_rational(bound['population']['q']);known=F(5,6)
        self.assertEqual(bound['population']['known_condition_fraction'],_rational(known))
        self.assertEqual(bound['population']['w'],_rational(q*known))
        effect=F(1,10);scenario=bound['scenarios'][2]
        self.assertEqual(scenario['transition_p_zero'],_rational(q-q*effect/(1-q)))
        self.assertEqual(scenario['p_other'],_rational(q-q*known*effect/(1-q*known)))
        self.assertNotEqual(scenario['p_other'],scenario['transition_p_zero'])
        world=generate_world(source,bound,2,96,2026102604)
        self.assertTrue(any(c['condition'] is None for c in world['report']['cases']))
        self.assert_link(world['report'])

    def test_unsupported_identity_or_scope_retains_a_model_gap(self):
        for change in ('identity','scope','values'):
            source=source_fixture()
            if change=='identity':source['request']['condition_program']['expression']['left']['bars']=2
            elif change=='scope':source['request']['scope_program']['expression']['value']=False
            else:source['cases'][2]['outcome']=_rational(0)
            bound=model(source)
            with self.subTest(change=change):
                self.assertEqual(bound['status'],'MODEL_OR_INFORMATION_GAP')
                with self.assertRaises(Invalid):generate_world(source,bound,0,96,1)


if __name__=='__main__':unittest.main()
