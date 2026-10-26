"""Owned meaning-review process checks. Mock answers never establish real fidelity."""
import unittest
from unittest.mock import patch

from controller_provider_support import Fixture
from trading_researcher.auxiliary import run_auxiliary_once
from trading_researcher.errors import Denied


class MeaningReviewTests(unittest.TestCase):
    def setUp(self):
        self.f=Fixture()
        self.addCleanup(self.f.close)
        self.case=self.f.case()
        with patch('trading_researcher.controller_providers._invoke',return_value=self.f.result(self.case)):
            result=run_auxiliary_once(self.case['client'])
        self.assertTrue(result['accepted'],result)
        self.target=result['artifact_id']

    def test_missing_review_retains_gap_without_promoting_unsupported_idea(self):
        result=self.f.op('assess_meaning_review',key='first',formalization_id=self.target)
        self.assertFalse(result['body']['scientific_readiness'])
        self.assertEqual(result['body']['independent_semantic_review'],'NOT_SATISFIED')
        self.assertIn('NO_REVIEW_REGISTERED',[gap['code'] for gap in result['body']['gaps']])

    def test_assessment_is_operator_owned_and_idempotent(self):
        result=self.f.op('assess_meaning_review',key='first',formalization_id=self.target)
        self.assertEqual(result,self.f.op('assess_meaning_review',key='first',formalization_id=self.target))
        with self.assertRaises(Denied):
            self.case['client'].call('assess_meaning_review',key='forge',formalization_id=self.target)


class MeaningCompletionTests(unittest.TestCase):
    def setUp(self):
        import meaning_review_support as support
        self.f=support.Fixture()
        self.addCleanup(self.f.close)

    def assess(self,case,key='assessment'):
        return self.f.op('assess_meaning_review',key=key,formalization_id=case['target']['id'])

    def test_completed_qualified_review_satisfies_only_process_prerequisite(self):
        case=self.f.formalize()
        review=self.f.review(case)
        before=self.f.op('get_artifact',artifact_id=review['outcome']['artifact_id'])
        assessment=self.assess(case)
        self.assertEqual(assessment['body']['independent_semantic_review'],'SATISFIED')
        self.assertFalse(assessment['body']['scientific_readiness'])
        self.assertEqual(before,self.f.op('get_artifact',artifact_id=before['id']))
        self.assertEqual(before['body']['actual_independent_model_review'],'UNVERIFIED')

    def test_different_review_remains_gap(self):
        case=self.f.formalize()
        self.f.review(case,'different')
        assessment=self.assess(case)
        self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
        self.assertIn('MEANING_DIFFERENCE_OR_UNCERTAINTY',[g['code'] for g in assessment['body']['gaps']])

    def test_new_review_makes_prior_positive_assessment_stale(self):
        case=self.f.formalize()
        self.f.review(case)
        assessment=self.assess(case)
        self.f.review(case,run=False)
        status=self.f.op('inspect_meaning_review',assessment_id=assessment['id'])
        self.assertEqual(status['status'],'STALE')
        self.assertEqual(status['independent_semantic_review'],'NOT_SATISFIED')
        self.assertEqual(self.assess(case,'new')['body']['independent_semantic_review'],'NOT_SATISFIED')

    def test_historically_timely_review_can_be_assessed_after_epoch_expiry(self):
        case=self.f.formalize()
        self.f.review(case)
        now=self.f.broker._now()
        self.f.broker.clock=lambda:now+3600
        self.assertEqual(self.assess(case)['body']['independent_semantic_review'],'SATISFIED')

    def test_scripted_live_label_does_not_satisfy_prerequisite(self):
        case=self.f.formalize()
        self.f.review(case,hosted=False)
        self.assertEqual(self.assess(case)['body']['independent_semantic_review'],'NOT_SATISFIED')

    def test_arbitrary_prompt_does_not_satisfy_prerequisite(self):
        case=self.f.formalize()
        self.f.review(case,qualified=False)
        assessment=self.assess(case)
        self.assertIn('REVIEW_PROTOCOL_GAP',[g['code'] for g in assessment['body']['gaps']])
        self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
