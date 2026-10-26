"""Population truth is fixed before draws and differs from realized contrast."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import unittest

from trading_researcher.codec import Invalid, digest
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.outcomes import _rational, reference_contrast
from trading_researcher.population_models import build_model, generate_world, specification


def fixture():
    return json.loads((Path(__file__).parent/'fixtures/information_diagnostics_cases.json').read_text())['fixtures'][0]['report']


class PopulationModelTests(unittest.TestCase):
    def model(self, source=None, effects=None):
        source = fixture() if source is None else source
        effects = [Fraction(0), Fraction(1,20), Fraction(1,10)] if effects is None else effects
        return build_model(source, diagnose(source,[1,2]), specification(2, Fraction(1,2), Fraction(1,3),
            'Declared stress assumptions; neither fitted nor empirically validated.'), [_rational(x) for x in effects])

    def test_population_equations_include_unknown_conditions(self):
        model = self.model()
        self.assertEqual(model['status'], 'MODEL_SPECIFIED')
        self.assertEqual(model['population']['q'], _rational(Fraction(3,7)))
        self.assertEqual(model['population']['w'], _rational(Fraction(4,7)))
        self.assertEqual(model['scenarios'][2]['p_true'], _rational(Fraction(37,70)))
        self.assertEqual(model['scenarios'][2]['p_other'], _rational(Fraction(31,105)))
        self.assertFalse(model['scientific_readiness'])
        self.assertIsNone(model['n_min'])

    def test_infeasible_scenario_is_not_clipped_or_dropped(self):
        model=self.model(effects=[Fraction(0),Fraction(1)])
        self.assertEqual(model['status'],'MODEL_OR_INFORMATION_GAP')
        self.assertEqual(len(model['scenarios']),2)
        self.assertFalse(model['scenarios'][1]['feasible'])
        with self.assertRaises(Invalid):generate_world(fixture(),model,0,20,11)

    def test_world_replays_preserves_masks_and_uses_synthetic_identity(self):
        source=fixture();before=deepcopy(source);model=self.model(source)
        world=generate_world(source,model,2,100,11)
        self.assertEqual(world,generate_world(source,model,2,100,11))
        self.assertEqual(source,before)
        self.assertEqual(world['truth']['effect'],_rational(Fraction(1,10)))
        self.assertEqual(world['report']['request']['candidate_ref'],'synthetic-population:'+digest(model))
        self.assertNotEqual(world['report']['request']['condition_program'],source['request']['condition_program'])
        self.assertEqual(len(world['report']['cases']),200)
        self.assertEqual(reference_contrast(world['report'])['status'],'DESCRIPTIVE_ONLY')
        self.assertTrue(any(row['status']=='DATA_GAP' for row in world['report']['cases']))
        self.assertTrue(any(row['condition'] is None and row['status']=='ELIGIBLE' for row in world['report']['cases']))
        self.assertTrue(all(row['outcome'] is None for row in world['report']['cases'] if row['status']!='ELIGIBLE'))
        self.assertFalse(world['classification_permitted'])

    def test_diagnostics_and_model_cannot_be_substituted(self):
        source=fixture();diagnostics=diagnose(source,[1,2]);diagnostics['totals']['scope']['successes']+=1
        with self.assertRaises(Invalid):build_model(source,diagnostics,specification(2,0,0,'fixed stress'),[_rational(0)])
        model=self.model();model['population']['q']=_rational(Fraction(1,2))
        with self.assertRaises(Invalid):generate_world(source,model,0,20,11)

    def test_bounds_and_resource_inputs_are_exact(self):
        for value in (True,0,1000001):
            with self.subTest(value=value),self.assertRaises(Invalid):specification(value,0,0,'fixed stress')
        for rho in (Fraction(-1,2),1):
            with self.assertRaises(Invalid):specification(2,rho,0,'fixed stress')
        for rows,seed in ((True,0),(1,0),(50001,0),(20,True),(20,-1)):
            with self.subTest(rows=rows,seed=seed),self.assertRaises(Invalid):
                generate_world(fixture(),self.model(),0,rows,seed)


if __name__=='__main__':unittest.main()
