"""Admitted plan requests survive failures and retries preserve their exact closure."""
from copy import deepcopy
import hashlib
import unittest
from unittest.mock import patch

from trading_researcher import evaluation_plans
from trading_researcher.codec import digest
from trading_researcher.coordination import Conflict
import test_evaluation_plans as plan_support


class PlanRetentionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan_support.EvaluationPlanTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.close()

    arguments = plan_support.EvaluationPlanTests.arguments

    def latest(self):
        return next(item for item in self.broker.call(self.token, 'inspect_bound_computations')['attempts']
                    if item['kind'] == 'evaluation_plan')

    def test_exact_request_payload_and_sources_are_committed_before_launch(self):
        args = self.arguments('retention-before-launch')
        expected = deepcopy(args)

        def interrupt(bundle, payload, verify_hash=None):
            attempt = self.latest()
            self.assertEqual(attempt['state'], 'STARTED')
            capsule = self.broker.call(self.token, 'get_artifact', artifact_id=attempt['retained_input_id'])
            body = capsule['body']
            self.assertEqual(body['schema'], 'evaluation-plan-input/1')
            self.assertEqual(body['request'], expected)
            self.assertEqual(body['request_hash'], digest(expected))
            self.assertEqual(body['payload'], payload)
            self.assertEqual(body['payload_hash'], digest(payload))
            self.assertEqual(body['source_footprint'], evaluation_plans.footprint(bundle))
            self.assertEqual(body['bootstrap_sha256'], hashlib.sha256(evaluation_plans.BOOTSTRAP.encode()).hexdigest())
            self.assertIn(self.execution['id'], capsule['source_refs'])
            self.assertIn(self.execution['id'], capsule['exposure'])
            for name, descriptor in body['source_files'].items():
                self.assertEqual(self.broker._read_blob_bytes(descriptor['sha256']), bundle[name])
            self.assertFalse(body['scientific_readiness'])
            args['dependence']['randomness']['seed'] = 12345
            raise TimeoutError('Injected before calculation')

        with patch.object(evaluation_plans, 'run_plan_child', side_effect=interrupt):
            with self.assertRaises(TimeoutError):
                self.broker.call(self.token, 'prepare_evaluation_plan', **args)
        attempt = self.latest()
        self.assertEqual(attempt['state'], 'INTERRUPTED')
        self.assertIsNone(attempt['artifact_id'])
        capsule = self.broker.call(self.token, 'get_artifact', artifact_id=attempt['retained_input_id'])
        self.assertEqual(capsule['body']['request'], expected)

    def test_retry_uses_retained_closure_and_completed_plan_links_original_input(self):
        args = self.arguments('retention-retry')
        with patch.object(evaluation_plans, 'run_plan_child', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.broker.call(self.token, 'prepare_evaluation_plan', **args)
        first = self.latest()
        capsule = self.broker.call(self.token, 'get_artifact', artifact_id=first['retained_input_id'])
        changed = evaluation_plans.source_bundle()
        changed['trading_researcher/evaluation_policy.py'] += b'\n# A later installed source version\n'
        original = evaluation_plans.run_plan_child

        def check_original(bundle, payload, verify_hash=None):
            self.assertEqual(evaluation_plans.footprint(bundle), capsule['body']['source_footprint'])
            self.assertEqual(payload, capsule['body']['payload'])
            return original(bundle, payload, verify_hash)

        # Simulate a restarted host running a later version; the child must still
        # receive the original capsule rather than these new checkout bytes.
        with patch.object(evaluation_plans, 'source_bundle', return_value=changed), \
             patch.object(evaluation_plans, 'LOADED_SOURCE', evaluation_plans.footprint(changed)), \
             patch.object(evaluation_plans, 'run_plan_child', side_effect=check_original):
            result = self.broker.call(self.token, 'prepare_evaluation_plan', **args)
        self.assertEqual(result['body']['status'], 'POLICY_DRAFT')
        self.assertEqual(result['body']['input_capsule_id'], capsule['id'])
        self.assertIn(capsule['id'], result['source_refs'])
        self.assertIn(capsule['id'], result['exposure'])
        self.assertNotEqual(result['body']['attempt_id'], first['attempt_id'])
        attempts = self.broker.call(self.token, 'inspect_bound_computations')['attempts']
        self.assertEqual(next(a for a in attempts if a['attempt_id'] == first['attempt_id'])['state'], 'INTERRUPTED')
        self.assertEqual(self.broker.call(self.token, 'prepare_evaluation_plan', **args), result)

    def test_interrupted_key_cannot_be_rebound_to_different_arguments(self):
        args = self.arguments('retention-conflict')
        with patch.object(evaluation_plans, 'run_plan_child', side_effect=TimeoutError):
            with self.assertRaises(TimeoutError):
                self.broker.call(self.token, 'prepare_evaluation_plan', **args)
        with patch.object(evaluation_plans, 'run_plan_child', side_effect=AssertionError('Conflicting request launched')):
            with self.assertRaises(Conflict):
                self.broker.call(self.token, 'prepare_evaluation_plan', **{**args, 'primary_count': 3})


if __name__ == '__main__':
    unittest.main()
