"""Review evidence joins plan preparation without granting scientific authority."""
import unittest
from trading_researcher.codec import canonical
import plan_review_support as support


class PlanReviewTests(unittest.TestCase):
    def setUp(self):
        self.f=support.Fixture().setup_plan()
        self.addCleanup(self.f.close)

    def test_matching_review_closes_only_current_semantic_gate(self):
        plan=self.f.prepare()
        raw=canonical(plan)
        self.assertIn('independent_semantic_review',plan['body']['plan']['remaining_gates'])
        current=self.f.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertNotIn('independent_semantic_review',current['current_remaining_gates'])
        self.assertEqual(current['current_remaining_gates'],[
            gate for gate in plan['body']['plan']['remaining_gates'] if gate!='independent_semantic_review'])
        self.assertFalse(current['scientific_readiness'])
        self.assertFalse(current['allocation_reserved'])
        self.assertFalse(current['frozen'])
        self.assertEqual(raw,canonical(self.f.op('get_artifact',artifact_id=plan['id'])))
        capsule=self.f.op('get_artifact',artifact_id=plan['body']['input_capsule_id'])
        self.assertIn(self.f.assessment['id'],capsule['source_refs'])
        self.assertIn(self.f.assessment['id'],plan['exposure'])
        self.assertEqual(plan['body']['meaning_review_at_preparation'],capsule['body']['meaning_review_at_preparation'])

    def test_later_review_reopens_gate_without_rewriting_historical_plan(self):
        plan=self.f.prepare()
        self.f.review(self.f.target_case,run=False)
        current=self.f.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertFalse(current['meaning_review']['current'])
        self.assertIn('independent_semantic_review',current['current_remaining_gates'])
        self.assertEqual(self.f.prepare(),plan)

    def test_legacy_preparation_remains_missing_review_and_has_no_new_fields(self):
        plan=self.f.prepare(with_review=False)
        self.assertNotIn('meaning_review_at_preparation',plan['body'])
        current=self.f.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertIsNone(current['meaning_review'])
        self.assertEqual(current['current_remaining_gates'],plan['body']['plan']['remaining_gates'])
