"""Independent owned-plan probes; no protected data or scientific authority is created."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from trading_researcher import evaluation_plans, evaluation_policy
from trading_researcher.coordination import Conflict, Denied, Invalid
import test_evaluation_plans as plan_support


class EvaluationPlansAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan_support.EvaluationPlanTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.close()

    arguments = plan_support.EvaluationPlanTests.arguments

    def completed_plan_count(self):
        # Retained input capsules are required even when a child fails; only a
        # falsely published completed plan is forbidden by these assertions.
        return sum(1 for row in self.broker._db.execute('SELECT envelope FROM artifacts')
                   if '"schema":"evaluation-plan/1"' in row[0])

    def assert_no_pending_plan_attempts(self):
        attempts = self.broker.call(self.token, 'inspect_bound_computations')
        self.assertEqual(attempts['pending'], 0)
        latest = next(item for item in attempts['attempts'] if item['kind'] == 'evaluation_plan')
        self.assertEqual(latest['state'], 'INTERRUPTED')
        self.assertIsNone(latest['artifact_id'])

    def test_malformed_child_responses_leave_no_false_plan_or_pending_attempt(self):
        before = self.completed_plan_count()
        with patch.object(evaluation_plans, '_run_child', return_value={}):
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.broker.call(self.token, 'prepare_evaluation_plan',
                                 **self.arguments('independent-empty-child-response'))
        self.assert_no_pending_plan_attempts()
        self.assertEqual(self.completed_plan_count(), before)

        original = evaluation_plans._run_child
        count = 0

        def falsify_first_result(*args, **kwargs):
            nonlocal count
            result = original(*args, **kwargs)
            count += 1
            if count == 1:
                result['result']['plan']['effect_criterion']['delta'] = {
                    'numerator': '1', 'denominator': '10000'}
            return result

        with patch.object(evaluation_plans, '_run_child', side_effect=falsify_first_result):
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.broker.call(self.token, 'prepare_evaluation_plan',
                                 **self.arguments('independent-forged-child-result'))
        self.assert_no_pending_plan_attempts()
        self.assertEqual(self.completed_plan_count(), before)

    def test_child_cancellation_closes_attempt_without_publishing_plan(self):
        before = self.completed_plan_count()
        for interruption in (KeyboardInterrupt, TimeoutError):
            with self.subTest(interruption=interruption.__name__):
                with patch.object(evaluation_plans, '_run_child', side_effect=interruption):
                    with self.assertRaises(interruption):
                        self.broker.call(self.token, 'prepare_evaluation_plan',
                                         **self.arguments('independent-abort-' + interruption.__name__))
                self.assert_no_pending_plan_attempts()
                self.assertEqual(self.completed_plan_count(), before)

    def test_plan_calculation_ignores_stale_parent_imports(self):
        with patch.object(evaluation_plans, 'draft_plan',
                          side_effect=AssertionError('Parent calculation used'), create=True), \
             patch.object(evaluation_policy, 'draft_plan',
                          side_effect=AssertionError('Parent policy calculation used')):
            result = self.broker.call(self.token, 'prepare_evaluation_plan',
                                     **self.arguments('independent-stale-parent'))
        self.assertEqual(result['body']['status'], 'POLICY_DRAFT')
        self.assertEqual(result['body']['plan']['effect_criterion']['delta'],
                         {'numerator': '1', 'denominator': '20'})
        self.assertFalse(result['body']['scientific_readiness'])

    def test_plan_and_idempotency_request_use_same_copied_dependence(self):
        args = self.arguments('independent-caller-mutation')
        expected = deepcopy(args['dependence'])
        original = self.broker._bound_dependencies

        def mutate_after_admission(*values):
            result = original(*values)
            args['dependence']['base_length'] = 8
            args['dependence']['randomness']['seed'] = 999
            args['dependence']['development_refs'] = ['unvalidated:replacement']
            return result

        with patch.object(self.broker, '_bound_dependencies', side_effect=mutate_after_admission):
            result = self.broker.call(self.token, 'prepare_evaluation_plan', **args)
        self.assertEqual(result['body']['request']['dependence'], expected)
        actual = result['body']['plan']['dependence_design']
        for key in expected:
            self.assertEqual(actual[key], expected[key], key)

    def test_corrupt_diagnostic_case_bytes_cannot_be_admitted_as_available_basis(self):
        identity = self.execution['blob_refs'][0]
        path = self.broker._blob_path(identity)
        original = path.read_bytes()
        try:
            path.write_bytes(b'corrupt diagnostic cases\n')
            with self.assertRaises((Invalid, Denied, Conflict, OSError)):
                self.broker.call(self.token, 'prepare_evaluation_plan',
                                 **self.arguments('independent-corrupt-diagnostic'))
        finally:
            path.write_bytes(original)

    def test_missing_diagnostic_case_bytes_cannot_be_admitted_as_available_basis(self):
        identity = self.execution['blob_refs'][0]
        path = self.broker._blob_path(identity)
        original = path.read_bytes()
        try:
            path.unlink()
            with self.assertRaises((Invalid, Denied, Conflict, OSError)):
                self.broker.call(self.token, 'prepare_evaluation_plan',
                                 **self.arguments('independent-missing-diagnostic'))
        finally:
            path.write_bytes(original)

    def test_source_version_mismatch_denies_before_source_staging(self):
        changed = evaluation_plans.source_bundle()
        name = 'trading_researcher/evaluation_policy.py'
        changed[name] += b'\n# simulated different source version\n'
        with patch.object(evaluation_plans, 'source_bundle', return_value=changed), \
             patch.object(self.broker, '_stage_blob_bytes', side_effect=AssertionError('Stale source staged')):
            with self.assertRaises(Conflict):
                self.broker.call(self.token, 'prepare_evaluation_plan',
                                 **self.arguments('independent-source-mismatch'))

    def test_mid_commit_failure_leaves_no_visible_completed_draft(self):
        args = self.arguments('independent-rollback')
        before = self.completed_plan_count()
        original = self.broker._event

        def fail_event(actor, action, **details):
            if action == 'evaluation_plan_prepared':
                raise RuntimeError('Injected interruption before transaction commit')
            return original(actor, action, **details)

        with patch.object(self.broker, '_event', side_effect=fail_event):
            with self.assertRaises(RuntimeError):
                self.broker.call(self.token, 'prepare_evaluation_plan', **args)
        self.assertEqual(self.completed_plan_count(), before)
        result = self.broker.call(self.token, 'prepare_evaluation_plan', **args)
        self.assertEqual(result['body']['status'], 'POLICY_DRAFT')
        self.assertFalse(result['body']['frozen'])
        self.assertFalse(result['body']['allocation_reserved'])
        self.assertFalse(result['body']['scientific_readiness'])

    def test_worker_denied_before_reading_compiled_or_diagnostic_artifacts(self):
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Worker accessed plan inputs')):
            with self.assertRaises(Denied):
                self.broker.call(self.fixture.worker, 'prepare_evaluation_plan',
                                 **self.arguments('independent-worker'))

    def test_protected_binding_denied_before_dependencies_or_blob_reads(self):
        # A deliberately injected trusted metadata return tests the denial seam;
        # it does not create an assessment draft or grant access to real data.
        snapshot = deepcopy(self.fixture.snapshot)
        snapshot['data_class'] = 'assessment'
        snapshot['body']['manifest']['partition'] = 'assessment'
        with patch.object(self.broker, '_data_snapshot', return_value=snapshot), \
             patch.object(self.broker, '_bound_dependencies', side_effect=AssertionError('Protected binding reached dependencies')), \
             patch.object(self.broker, '_read_blob_bytes', side_effect=AssertionError('Protected binding read bytes')):
            with self.assertRaises(Denied):
                self.broker.call(self.token, 'prepare_evaluation_plan',
                                 **self.arguments('independent-protected'))

    def test_reserved_namespace_cannot_be_forged_by_generic_source(self):
        with self.assertRaises(Invalid):
            self.broker.call(self.token, 'add_source', data_class='development',
                             body={'schema': 'evaluation-plan/1', 'scientific_readiness': True})


if __name__ == '__main__':
    unittest.main()
