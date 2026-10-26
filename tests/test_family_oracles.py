"""Independent exact oracles for the bounded shared-template response family.

Expectations were derived before inspecting family_models implementation.
The pinned input has seven eligible observations, three successes and four true
conditions, hence q=3/7 and w=4/7. For effects 0, 1/20 and 1/10:

              p_true    p_other     thresholds on the shared lattice L=420
    null        3/7       3/7                    180, 180
    boundary   67/140    38/105                   201, 152
    planted    37/70     31/105                   222, 124

False and unknown conditions share p_other. Controlled draws test exact integer
thresholds and state evolution, not PRNG distribution, market adequacy, original
AST overlap or a completed calibration. Event expectations are separately fixed
and never obtained from family_events itself.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid
from trading_researcher.family_models import generate_family, family_events
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.population_models import build_model, specification


FIXTURE = Path(__file__).parent / 'fixtures/information_diagnostics_cases.json'
FIXTURE_SHA = 'e2b8233b7b8ed1917f9392eb0c989279837f88219843371f35740908ccbb6b6f'
COMPONENTS = [{'id': 'null', 'scenario': 0}, {'id': 'boundary', 'scenario': 1},
              {'id': 'planted', 'scenario': 2}]


def rational(numerator, denominator=1):
    value = Fraction(numerator, denominator)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def source_and_model(share=1, effects=None):
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_SHA
    report = json.loads(raw)['fixtures'][0]['report']
    effects = effects if effects is not None else [rational(0), rational(1, 20), rational(1, 10)]
    model = build_model(report, diagnose(report, [1]),
        specification(1, 0, share, 'Independent fixed synthetic family oracle; no market fit.'), effects)
    return report, model


class ControlledStreams:
    """The documented RNG hook; only randrange's supplied finite outcomes vary."""
    def __init__(self, common_values, mask_values=(0,), individual=None):
        self.common_values = list(common_values)
        self.mask_values = list(mask_values)
        self.individual = individual or {}
        self.streams = {}

    def __call__(self, seed, component):
        key = json.dumps(component, sort_keys=True)
        if key in self.streams:
            raise AssertionError('A named component stream was recreated')
        if component == 'common-latent':
            values, expected_bound = self.common_values, 420
        elif component == 'joint-mask':
            values, expected_bound = self.mask_values, 6
        elif isinstance(component, list) and component[0] == 'response-latent':
            values, expected_bound = [self.individual.get((component[1], component[2]), 0)], 420
        elif isinstance(component, list) and component[0] == 'common-choice':
            values, expected_bound = [0], None
        else:
            raise AssertionError('Unexpected random component: ' + repr(component))

        class Stream:
            def __init__(self):
                self.value_draws = 0

            def randrange(self, bound):
                # Exact probabilities zero and one have denominator one.
                if bound == 1:
                    return 0
                if expected_bound is None or bound != expected_bound:
                    raise AssertionError(('Unexpected finite draw bound', bound, expected_bound))
                value = values[self.value_draws % len(values)]
                self.value_draws += 1
                if not 0 <= value < bound:
                    raise AssertionError('Oracle draw lies outside its lattice')
                return value

        stream = Stream()
        self.streams[key] = stream
        return stream


def outcome(identity, truth, state='VERIFIED', decision='TESTED_INCONCLUSIVE', covered=True):
    return {'id': identity, 'truth': rational(*truth), 'state': state,
            'decision': decision, 'covered': covered}


class SharedTemplateFamilyOracleTests(unittest.TestCase):
    def test_fixed_rate_equations_and_strict_threshold_edges(self):
        report, model = source_and_model()
        self.assertEqual(model['population']['q'], rational(3, 7))
        self.assertEqual(model['population']['w'], rational(4, 7))
        expected_rates = {
            'null': {'effect': rational(0), 'p_true': rational(3, 7), 'p_other': rational(3, 7)},
            'boundary': {'effect': rational(1, 20), 'p_true': rational(67, 140), 'p_other': rational(38, 105)},
            'planted': {'effect': rational(1, 10), 'p_true': rational(37, 70), 'p_other': rational(31, 105)}}
        thresholds = {'null': (180, 180), 'boundary': (201, 152), 'planted': (222, 124)}
        self.assertEqual(model['lattice_size'], '420')
        for latent in (0, 123, 124, 151, 152, 179, 180, 200, 201, 221, 222, 419):
            streams = ControlledStreams([latent])
            with self.subTest(latent=latent), patch('trading_researcher.family_models._rng', side_effect=streams):
                world = generate_family(report, model, COMPONENTS, 2, 17)
            for item in world['components']:
                identity = item['id']
                self.assertEqual({key: item['truth'][key] for key in expected_rates[identity]}, expected_rates[identity])
                first = item['report']['cases'][:2]
                self.assertEqual([case['condition'] for case in first], [True, False])
                self.assertEqual([case['outcome'] for case in first],
                    [rational(int(latent < threshold)) for threshold in thresholds[identity]])
                self.assertTrue(all(case['outcome'] is None for case in item['report']['cases'][2:]))

    def test_shared_mask_unknown_condition_and_hidden_time_evolution(self):
        report, model = source_and_model()
        # t=2 is wholly ineligible. U_3=180 must still be used at t=3.
        streams = ControlledStreams([0, 419, 0, 180, 419, 0, 419, 0], range(6))
        with patch('trading_researcher.family_models._rng', side_effect=streams):
            world = generate_family(report, model, COMPONENTS, 8, 19)
        expected = {
            'null': [1, 1, 0, 0, None, None, 0, 0, 0, None, None, None, 0, 0, None, None],
            'boundary': [1, 1, 0, 0, None, None, 0, 1, 0, None, None, None, 0, 0, None, None],
            'planted': [1, 1, 0, 0, None, None, 0, 1, 0, None, None, None, 0, 0, None, None]}
        expected_mask = [index for index in (0, 1, 2, 3, 4, 5, 0, 1) for _ in range(2)]
        for item in world['components']:
            cases = item['report']['cases']
            self.assertEqual([case['simulation_mask']['source_time_index'] for case in cases], expected_mask)
            self.assertEqual([case['outcome'] for case in cases],
                [None if value is None else rational(value) for value in expected[item['id']]])
            self.assertIsNone(cases[2]['condition'])
            self.assertEqual(cases[2]['status'], 'ELIGIBLE')
            self.assertEqual([case['status'] for case in cases[4:6]], ['DATA_GAP', 'DATA_GAP'])
            self.assertEqual([case['status'] for case in cases[10:12]], ['OUTCOME_MISSING', 'OUTCOME_MISSING'])
            self.assertEqual([case['status'] for case in cases[14:]], ['PARTITION_BOUNDARY', 'PARTITION_BOUNDARY'])
            self.assertFalse(item['report']['simulation']['raw_AST_executed'])
            self.assertEqual(item['descriptive']['effect'], rational(-1, 45) if item['id'] == 'null' else rational(1, 15))
        # One initial state and at least one advancement per complete timestamp.
        self.assertGreaterEqual(streams.streams[json.dumps('common-latent')].value_draws, 8)

    def test_response_components_have_distinct_individual_streams(self):
        report, model = source_and_model(share=0)
        individual = {(identity, symbol): (419 if identity == 'null' else 0)
            for identity in ('null', 'planted') for symbol in ('A', 'B')}
        streams = ControlledStreams([0], individual=individual)
        with patch('trading_researcher.family_models._rng', side_effect=streams):
            world = generate_family(report, model, [COMPONENTS[0], COMPONENTS[2]], 2, 23)
        values = {item['id']: [case['outcome'] for case in item['report']['cases'][:2]] for item in world['components']}
        self.assertEqual(values, {'null': [rational(0), rational(0)], 'planted': [rational(1), rational(1)]})

    def test_order_replay_and_original_input_are_preserved(self):
        report, model = source_and_model(share=Fraction(1, 2))
        before = deepcopy((report, model, COMPONENTS))
        left = generate_family(report, model, COMPONENTS, 32, 29)
        right = generate_family(report, model, list(reversed(COMPONENTS)), 32, 29)
        self.assertEqual(left, right)
        self.assertEqual(left, generate_family(report, model, COMPONENTS, 32, 29))
        self.assertEqual([item['id'] for item in left['components']], ['boundary', 'null', 'planted'])
        self.assertEqual((report, model, COMPONENTS), before)
        refs = [item['report']['request']['candidate_ref'] for item in left['components']]
        self.assertEqual(len(set(refs)), 3)
        self.assertNotIn(report['request']['candidate_ref'], refs)

    def test_invalid_family_or_unusable_model_cannot_drop_a_component(self):
        report, model = source_and_model()
        malformed = [[], [COMPONENTS[0]], [COMPONENTS[0], COMPONENTS[0]],
            [{'id': str(index), 'scenario': 0} for index in range(9)],
            [{'id': 'a', 'scenario': True}, {'id': 'b', 'scenario': 0}],
            [{'id': 'a', 'scenario': 0}, {'id': 'b', 'scenario': 3}]]
        for components in malformed:
            with self.subTest(components=components), self.assertRaises(Invalid):
                generate_family(report, model, components, 8, 31)
        source, infeasible = source_and_model(effects=[rational(0), rational(1)])
        self.assertEqual(infeasible['status'], 'MODEL_OR_INFORMATION_GAP')
        with self.assertRaises(Invalid):
            generate_family(source, infeasible, [{'id': 'a', 'scenario': 0}, {'id': 'b', 'scenario': 1}], 8, 31)


class FamilyEventOracleTests(unittest.TestCase):
    def test_mixed_boundary_and_justified_alternative_have_separate_events(self):
        values = [outcome('boundary', (1, 20)), outcome('alternative', (1, 10), decision='SUPPORTED_INITIAL')]
        self.assertEqual(family_events(values, rational(1, 20), 'positive'), {
            'joint_miscoverage': False, 'false_support': None, 'boundary_decisive': False,
            'detections': {'alternative': True}})
        values.append(outcome('null', (0, 1), decision='TESTED_NEGATIVE'))
        self.assertEqual(family_events(values, rational(1, 20), 'positive'), {
            'joint_miscoverage': False, 'false_support': False, 'boundary_decisive': False,
            'detections': {'alternative': True}})

    def test_boundary_error_and_known_miss_survive_unavailable_sibling(self):
        for decision in ('SUPPORTED_INITIAL', 'TESTED_NEGATIVE'):
            for state in ('INFORMATION_GAP', 'MODEL_GAP', 'TECHNICAL_FAILURE'):
                values = [outcome('boundary', (1, 20), decision=decision, covered=False),
                    outcome('alternative', (1, 10), state=state, decision=None, covered=None)]
                with self.subTest(decision=decision, state=state):
                    self.assertEqual(family_events(values, rational(1, 20), 'positive'), {
                        'joint_miscoverage': True, 'false_support': None, 'boundary_decisive': True,
                        'detections': {'alternative': False if state == 'INFORMATION_GAP' else None}})

    def test_unavailable_interval_is_not_joint_coverage_success(self):
        for state in ('INFORMATION_GAP', 'MODEL_GAP', 'TECHNICAL_FAILURE'):
            values = [outcome('null', (0, 1), decision='TESTED_NEGATIVE'),
                outcome('boundary', (1, 20), state=state, decision=None, covered=None)]
            with self.subTest(state=state):
                self.assertEqual(family_events(values, rational(1, 20), 'positive'), {
                    'joint_miscoverage': None, 'false_support': False,
                    'boundary_decisive': False if state == 'INFORMATION_GAP' else None, 'detections': {}})

    def test_null_false_support_survives_missing_boundary_component(self):
        values = [outcome('null', (0, 1), decision='SUPPORTED_INITIAL', covered=False),
            outcome('boundary', (1, 20), state='TECHNICAL_FAILURE', decision=None, covered=None)]
        self.assertEqual(family_events(values, rational(1, 20), 'positive'), {
            'joint_miscoverage': True, 'false_support': True, 'boundary_decisive': None, 'detections': {}})

    def test_negative_direction_uses_assigned_negative_boundary_and_alternative(self):
        values = [outcome('boundary', (-1, 20)),
            outcome('alternative', (-1, 10), decision='SUPPORTED_INITIAL')]
        self.assertEqual(family_events(values, rational(1, 20), 'negative'), {
            'joint_miscoverage': False, 'false_support': None, 'boundary_decisive': False,
            'detections': {'alternative': True}})


if __name__ == '__main__':
    unittest.main()
