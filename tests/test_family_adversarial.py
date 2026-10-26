"""Independent family boundary checks, with explicit mock/fixture limitations.

Pipeline tests retain actual generated cases but substitute bootstrap outputs to
exercise event extraction. They do not replace genuine fixed-draw integrations.
Host/graph cases use synthetic owned envelopes; they are not claimed as valid
scientific plans or a way an untrusted client could mint controller identities.
"""
from collections import Counter
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import patch

import test_family_oracles as oracle
from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied
from trading_researcher.family_models import generate_family
from trading_researcher.family_pipeline import calculate_family


class FamilyPipelineAdversarialTests(unittest.TestCase):
    def payload(self, effects=None):
        source, model = oracle.source_and_model(effects=effects)
        return {'report': {key: value for key, value in source.items() if key != 'cases'},
            'diagnostics': model['diagnostics'], 'specification': model['specification'],
            'effects': model['effects'], 'components': [{'id': 'boundary', 'scenario': 1}, {'id': 'planted', 'scenario': 2}],
            'time_rows': 8, 'seed': 37, 'bootstrap_seed': 41, 'limits': {'max_seconds': 2},
            'design': {'primary_count': 2, 'base_length': 4,
                'mc_policy': {'schema': 'mc-boundary-policy/1', 'noncoverage': oracle.rational(1, 20),
                    'delta': oracle.rational(1, 20), 'direction': 'positive'}}}, source['cases']

    def bootstrap(self, lower, upper, decision='TESTED_INCONCLUSIVE', stable=True):
        return {'status': 'COMPUTED_UNCALIBRATED',
            'interval': {'lower': oracle.rational(*lower), 'upper': oracle.rational(*upper)},
            'monte_carlo': {'nominal_classification': decision, 'boundary_stable': stable}}

    def test_actual_generated_family_uses_bound_design_and_shared_bootstrap_seed(self):
        payload, cases = self.payload(); before = deepcopy((payload, cases)); retained = []
        outputs = [self.bootstrap((0, 1), (1, 10)),
            self.bootstrap((3, 40), (1, 8), 'SUPPORTED_INITIAL')]
        with patch('trading_researcher.family_pipeline.calculate', side_effect=outputs) as bootstrap:
            result = calculate_family(payload, cases, retained.append)
        self.assertEqual(result['status'], 'COMPUTED_UNCALIBRATED')
        self.assertEqual(result['events'], {'joint_miscoverage': False, 'false_support': None,
            'boundary_decisive': False, 'detections': {'planted': True}})
        self.assertEqual(Counter(record['response_id'] for record in retained), {'boundary': 16, 'planted': 16})
        self.assertTrue(all(record['kind'] == 'case' for record in retained))
        designs = [call.args[1] for call in bootstrap.call_args_list]
        self.assertEqual(designs[0], designs[1])
        self.assertEqual(designs[0]['primary_count'], 2)
        self.assertEqual(designs[0]['base_length'], 4)
        self.assertEqual(designs[0]['mc_policy']['delta'], oracle.rational(1, 20))
        self.assertEqual((payload, cases), before)
        self.assertEqual(result['outer_world_count'], 1)
        self.assertFalse(result['scientific_readiness'])
        self.assertFalse(result['classification_permitted'])

    def test_unstable_classification_does_not_erase_actual_interval_miscoverage(self):
        payload, cases = self.payload()
        outputs = [self.bootstrap((3, 50), (2, 25), 'SUPPORTED_INITIAL', False),
            self.bootstrap((3, 40), (1, 8), 'SUPPORTED_INITIAL')]
        with patch('trading_researcher.family_pipeline.calculate', side_effect=outputs):
            result = calculate_family(payload, cases, lambda value: None)
        self.assertEqual(result['outcomes'][0]['decision'], 'TESTED_INCONCLUSIVE')
        self.assertFalse(result['outcomes'][0]['covered'])
        self.assertTrue(result['events']['joint_miscoverage'])
        self.assertFalse(result['events']['boundary_decisive'])

    def test_information_gap_is_distinct_from_invalid_input_failure(self):
        for reason, state, detection in [('no_scope_cases', 'INFORMATION_GAP', False),
                ('dependency_review_required', 'TECHNICAL_FAILURE', None)]:
            payload, cases = self.payload()
            outputs = [self.bootstrap((3, 50), (2, 25), 'SUPPORTED_INITIAL'),
                {'status': 'INPUT_GAP', 'reason': reason}]
            with self.subTest(reason=reason), patch('trading_researcher.family_pipeline.calculate', side_effect=outputs):
                result = calculate_family(payload, cases, lambda value: None)
            self.assertEqual(result['status'], 'INCOMPLETE')
            self.assertEqual(result['outcomes'][1]['state'], state)
            self.assertEqual(result['events'], {'joint_miscoverage': True, 'false_support': None,
                'boundary_decisive': True, 'detections': {'planted': detection}})

    def test_second_component_inherits_global_deadline(self):
        payload, cases = self.payload(); stops = []
        def bootstrap(report, design, limits, *, stop, on_draw):
            stops.append(stop())
            return self.bootstrap((0, 1), (1, 5)) if not stops[-1] else {'status': 'RESOURCE_STOP'}
        with patch('trading_researcher.family_pipeline.time.monotonic', side_effect=[0, 1, 2]), \
                patch('trading_researcher.family_pipeline.calculate', side_effect=bootstrap):
            result = calculate_family(payload, cases, lambda value: None)
        self.assertEqual(stops, [False, True])
        self.assertEqual(result['outcomes'][1]['state'], 'TECHNICAL_FAILURE')
        self.assertIsNone(result['events']['joint_miscoverage'])

    def test_infeasible_required_model_retains_all_outcomes_without_bootstrap(self):
        payload, cases = self.payload(effects=[oracle.rational(0), oracle.rational(1, 20), oracle.rational(1)])
        payload['components'] = [{'id': 'null', 'scenario': 0}, {'id': 'boundary', 'scenario': 1}]
        with patch('trading_researcher.family_pipeline.calculate', side_effect=AssertionError('Unusable model reached estimator')):
            result = calculate_family(payload, cases, lambda value: self.fail('Unusable model retained cases'))
        self.assertEqual(result['status'], 'MODEL_OR_INFORMATION_GAP')
        self.assertEqual([item['state'] for item in result['outcomes']], ['MODEL_GAP', 'MODEL_GAP'])
        self.assertEqual(result['events'], {'joint_miscoverage': None, 'false_support': None,
            'boundary_decisive': None, 'detections': {}})

    def test_exhaustive_common_lattice_matches_fixed_joint_probabilities(self):
        report, model = oracle.source_and_model()
        streams = oracle.ControlledStreams(range(420))
        with patch('trading_researcher.family_models._rng', side_effect=streams):
            world = generate_family(report, model, [oracle.COMPONENTS[0], oracle.COMPONENTS[2]], 421, 43)
        by_id = {item['id']: item['report']['cases'] for item in world['components']}
        for offset, expected in [(0, {(1, 1): 180, (0, 1): 42, (0, 0): 198}),
                (1, {(1, 1): 124, (1, 0): 56, (0, 0): 240})]:
            observed = Counter(tuple(int(by_id[identity][2*time+offset]['outcome']['numerator'])
                for identity in ('null', 'planted')) for time in range(420))
            self.assertEqual(observed, expected)


class FamilyHostBoundaryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.broker = Broker(temporary.name); self.addCleanup(self.broker.close)

    def owned(self, schema, data_class='development', origin='controller', **body):
        with self.broker._transaction():
            return self.broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': origin, 'data_class': data_class, 'source_refs': [], 'exposure': [],
                'authority': 'synthetic_graph_fixture_only', 'body': {'schema': schema, **body}})

    def test_protected_diagnostics_are_denied_before_development_binding(self):
        for data_class in ('assessment', 'operations'):
            diagnostic = self.owned('development-information-diagnostics/1', data_class)
            with self.subTest(data_class=data_class), patch.object(self.broker, '_development_plan_execution',
                    side_effect=AssertionError('Protected diagnostics reached downstream binding')):
                with self.assertRaises(Denied):
                    self.broker._population_inputs({}, {'diagnostics_id': diagnostic['id']}, family=True)

    def test_private_plan_class_cannot_be_laundered_through_development_diagnostics(self):
        plan = self.owned('evaluation-plan/1', 'assessment', status='POLICY_DRAFT')
        execution = self.owned('reference-execution/1', status='DESCRIPTIVE_EXECUTION')
        request = {'plan_id': plan['id'], 'execution_id': execution['id']}
        diagnostic = self.owned('development-information-diagnostics/1', request=request)
        with patch.object(self.broker, '_data_snapshot', side_effect=AssertionError('Private plan reached snapshot access')):
            with self.assertRaises(Denied):
                self.broker._population_inputs({}, {**request, 'diagnostics_id': diagnostic['id']}, family=True)

    def test_family_input_and_result_follow_existing_typed_revocation_graph(self):
        snapshot = self.owned('data-snapshot/1', origin='source')
        plan = self.owned('evaluation-plan/1', request={'compiled_id': snapshot['id'], 'dependence': {'development_refs': []}})
        execution = self.owned('reference-execution/1', compiled_id=snapshot['id'])
        information_input = self.owned('information-diagnostics-input/1', request={'plan_id': plan['id'], 'execution_id': execution['id']})
        diagnostic = self.owned('development-information-diagnostics/1', input_capsule_id=information_input['id'])
        capsule = self.owned('population-family-input/1', request={'plan_id': plan['id'],
            'execution_id': execution['id'], 'diagnostics_id': diagnostic['id']})
        result = self.owned('development-population-family/1', input_capsule_id=capsule['id'])
        self.assertEqual(self.broker._dependency_use(result['id'])['status'], 'NOT_REVOKED')
        evidence = self.broker.call(self.broker.admin_token, 'add_source', body={'reason': 'Synthetic revoked input'}, data_class='operations')
        revoked = self.broker.call(self.broker.admin_token, 'revoke_dependency', key='family-input-defect',
            dependency_id=snapshot['id'], reason='Synthetic graph defect', evidence_refs=[evidence['id']])
        self.assertEqual(self.broker._dependency_use(result['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
        self.assertIn(result['id'], revoked['body']['affected_artifact_ids'])


if __name__ == '__main__':
    unittest.main()
