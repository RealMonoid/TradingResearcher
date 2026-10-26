"""Actual isolated fixture adapter calls through owned formalization/review handoff."""
import unittest

from auxiliary_support import AuxiliaryFixture
from trading_researcher.auxiliary import run_auxiliary_once
from trading_researcher.researcher import ScriptedProvider


class AuxiliaryPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fixture=AuxiliaryFixture()
    @classmethod
    def tearDownClass(cls):cls.fixture.close()

    def test_isolated_formalizer_and_reviewer_share_epoch_without_issuing_approval(self):
        case=self.fixture.case()
        outcome=run_auxiliary_once(case['client'],ScriptedProvider([case['output']]))
        self.assertTrue(outcome['accepted'],outcome)
        target=self.fixture.op('get_artifact',artifact_id=outcome['artifact_id'])
        review=self.fixture.review(case,target)
        result=run_auxiliary_once(review['client'],ScriptedProvider([review['output']]))
        self.assertTrue(result['accepted'],result)
        saved=self.fixture.op('get_artifact',artifact_id=result['artifact_id'])
        body=saved['body']
        self.assertEqual(body['formalization_id'],target['id'])
        self.assertNotEqual(body['formalizer_id'],body['reviewer_id'])
        self.assertEqual(body['actual_independent_model_review'],'UNVERIFIED')
        self.assertFalse(body['scientific_readiness'])
        self.assertEqual(body['review']['judgment'],'uncertain')
        self.assertEqual(self.fixture.op('inspect_research_epoch',epoch_id=case['epoch'])['usage']['calls'],2)
        self.assertIn(body['response_id'],saved['source_refs'])
        self.assertEqual(self.fixture.op('get_artifact',artifact_id=target['id']),target)

    def test_unrepresentable_candidate_can_receive_retained_uncertainty_review(self):
        case=self.fixture.case()
        target=self.fixture.formalize(case,{'status':'final','candidate':None,'semantic_report':None})
        self.assertEqual(target['body']['assessment']['status'],'RETAINED_GAP')
        review=self.fixture.review(case,target)
        result=run_auxiliary_once(review['client'],ScriptedProvider([review['output']]))
        self.assertTrue(result['accepted'],result)
        saved=self.fixture.op('get_artifact',artifact_id=result['artifact_id'])
        self.assertEqual(saved['body']['review']['judgment'],'uncertain')
        self.assertFalse(saved['body']['scientific_readiness'])


if __name__=='__main__':unittest.main()
