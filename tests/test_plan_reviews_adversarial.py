"""Independent review-to-plan boundaries; data resolution is explicitly stubbed.

The support fixture retains genuine controller-owned review provenance and runs
the actual policy child/replay. It does not certify scientific data or features.
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import plan_review_support as support
from trading_researcher import evaluation_plans, meaning_reviews
from trading_researcher.codec import Invalid, canonical
from trading_researcher.errors import Conflict, Denied


class PlanReviewAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.f=support.Fixture().setup_plan()
        self.addCleanup(self.f.close)

    def plans(self):
        return [self.f.op('get_artifact',artifact_id=row[0]) for row in self.f.broker._db.execute(
            "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')='evaluation-plan/1'")]

    def test_wrong_target_assessment_is_rejected_before_calculation(self):
        other=self.f.formalize()
        assessment=self.f.op('assess_meaning_review',key='other-target',formalization_id=other['target']['id'])
        with patch.object(evaluation_plans,'run_plan_child',side_effect=AssertionError('Wrong target launched')) as child:
            with self.assertRaises((Invalid,Denied)):
                self.f.prepare(meaning_review_id=assessment['id'])
        self.assertFalse(child.called);self.assertEqual(self.plans(),[])

    def test_null_empty_and_wrapped_assessments_cannot_supply_review_evidence(self):
        wrapper=self.f.op('add_source',body={'schema':'untrusted-wrapper/1','assessment':self.f.assessment['body']},data_class='development')
        for value in (None,'',wrapper['id'],self.f.review_result['outcome']['artifact_id']):
            with self.subTest(value=value),patch.object(evaluation_plans,'run_plan_child',side_effect=AssertionError('Invalid review launched')) as child:
                with self.assertRaises((Invalid,Denied)):
                    self.f.prepare(key='bad-'+str(value),meaning_review_id=value)
                self.assertFalse(child.called)
        self.assertEqual(self.plans(),[])

    def test_worker_cannot_prepare_or_inspect_review_qualified_plan(self):
        with patch.object(self.f.broker,'_plan_inputs',side_effect=AssertionError('Unauthorized dependent read')):
            with self.assertRaises(Denied):
                self.f.review_result['client'].call('prepare_evaluation_plan',**self.f.arguments())
        plan=self.f.prepare()
        with patch.object(self.f.broker,'_artifact',side_effect=AssertionError('Unauthorized plan read')):
            with self.assertRaises(Denied):
                self.f.review_result['client'].call('inspect_evaluation_plan',plan_id=plan['id'])

    def test_review_sources_and_inherited_exposure_survive_input_and_final_plan(self):
        plan=self.f.prepare();capsule=self.f.op('get_artifact',artifact_id=plan['body']['input_capsule_id'])
        review=self.f.assessment
        needed={review['id'],*review['source_refs'],*review['exposure']}
        for artifact in (capsule,plan):
            with self.subTest(schema=artifact['body']['schema']):
                self.assertTrue(needed<=set(artifact['exposure']))
                self.assertIn(review['id'],artifact['source_refs'])
        self.assertEqual(capsule['body']['payload'],self.f.payload)
        self.assertIn('independent_semantic_review',plan['body']['plan']['remaining_gates'])

    def test_current_critical_review_cannot_close_gate_or_erase_prior_opinion(self):
        self.f.review(self.f.target_case,'different')
        self.f.assessment=self.f.op('assess_meaning_review',key='critical-inventory',formalization_id=self.f.target_case['target']['id'])
        self.assertEqual(self.f.assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
        plan=self.f.prepare();inspection=self.f.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertTrue(inspection['meaning_review']['current'])
        self.assertIn('independent_semantic_review',inspection['current_remaining_gates'])
        self.assertFalse(inspection['scientific_readiness'])

    def test_current_unverified_provider_review_keeps_semantic_gap(self):
        self.f.review(self.f.target_case,hosted=False)
        self.f.assessment=self.f.op('assess_meaning_review',key='unverified',formalization_id=self.f.target_case['target']['id'])
        plan=self.f.prepare();inspection=self.f.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertIn('independent_semantic_review',inspection['current_remaining_gates'])
        self.assertEqual(inspection['meaning_review']['independent_semantic_review'],'NOT_SATISFIED')

    def test_new_review_during_child_retains_interrupted_input_without_final_plan(self):
        original=evaluation_plans.run_plan_child;calls=0
        def changed_inventory(*args,**kwargs):
            nonlocal calls
            calls+=1
            if calls==1:self.f.review(self.f.target_case,run=False)
            return original(*args,**kwargs)
        with patch.object(evaluation_plans,'run_plan_child',side_effect=changed_inventory):
            with self.assertRaises((Invalid,Conflict)):
                self.f.prepare()
        self.assertEqual(self.plans(),[])
        attempts=self.f.op('inspect_bound_computations')['attempts']
        latest=next(item for item in reversed(attempts) if item['kind']=='evaluation_plan')
        self.assertEqual(latest['state'],'INTERRUPTED')
        capsule=self.f.op('get_artifact',artifact_id=latest['retained_input_id'])
        self.assertIn(self.f.assessment['id'],capsule['source_refs'])
        before=canonical(capsule)
        with patch.object(evaluation_plans,'run_plan_child',side_effect=AssertionError('Changed inventory retried')) as child:
            with self.assertRaises((Invalid,Conflict)):
                self.f.prepare()
        self.assertFalse(child.called)
        self.assertEqual(before,canonical(self.f.op('get_artifact',artifact_id=capsule['id'])))

    def test_policy_change_reopens_only_semantic_gate_in_current_inspection(self):
        plan=self.f.prepare();raw=canonical(plan)
        changed=meaning_reviews.policy_identity();changed['sources']['meaning_reviews.py']='0'*64
        with patch.object(meaning_reviews,'policy_identity',return_value=changed):
            current=self.f.op('inspect_evaluation_plan',plan_id=plan['id'])
            self.assertFalse(current['meaning_review']['current'])
            self.assertEqual(current['current_remaining_gates'],plan['body']['plan']['remaining_gates'])
            self.assertEqual(self.f.prepare(),plan)
        self.assertEqual(raw,canonical(self.f.op('get_artifact',artifact_id=plan['id'])))

    def test_completed_key_cannot_be_rebound_to_new_assessment(self):
        plan=self.f.prepare();self.f.review(self.f.target_case)
        assessment=self.f.op('assess_meaning_review',key='later-assessment',formalization_id=self.f.target_case['target']['id'])
        self.assertNotEqual(assessment['id'],self.f.assessment['id'])
        with patch.object(evaluation_plans,'run_plan_child',side_effect=AssertionError('Rebound completed request launched')) as child:
            with self.assertRaises(Conflict):self.f.prepare(meaning_review_id=assessment['id'])
        self.assertFalse(child.called)
        self.assertEqual(self.f.prepare(),plan)

    def test_policy_gap_cannot_become_empty_ready_gate_list(self):
        self.f.payload['candidate']['outcome']['scale']='unsupported-fixture-profile'
        plan=self.f.prepare();self.assertEqual(plan['body']['status'],'EVALUATION_GAP')
        self.assertIsNone(plan['body']['plan'])
        current=self.f.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertEqual(current['status'],'EVALUATION_GAP')
        self.assertIsNone(current['current_remaining_gates'])
        for name in ('scientific_readiness','allocation_reserved','frozen'):self.assertFalse(current[name])

    def test_wrapped_plan_does_not_gain_inspection_authority(self):
        plan=self.f.prepare()
        wrapper=self.f.op('add_source',body={'schema':'untrusted-wrapper/1','plan':plan['body']},data_class='development')
        with self.assertRaises((Invalid,Denied)):
            self.f.op('inspect_evaluation_plan',plan_id=wrapper['id'])


if __name__=='__main__':unittest.main()
