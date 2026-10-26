"""Independent owned meaning-review boundary checks; all model replies are mocks."""
from contextlib import closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch

import meaning_review_support as support
from trading_researcher import meaning_reviews as meaning
from trading_researcher.auxiliary import run_auxiliary_once
from trading_researcher.codec import Invalid, canonical
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied


class MeaningReviewsAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.f=support.Fixture();self.addCleanup(self.f.close)

    def assess(self,case,key='assessment'):
        return self.f.op('assess_meaning_review',key=key,formalization_id=case['target']['id'])

    def codes(self,assessment):
        return [item['code'] for item in assessment['body']['gaps']]

    def test_later_favorable_completed_review_does_not_hide_earlier_critical_job(self):
        case=self.f.formalize()
        critical=self.f.review(case,'different');favorable=self.f.review(case,'faithful')
        assessment=self.assess(case)
        self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
        observations=assessment['body']['review_observations']
        self.assertEqual([x['judgment'] for x in observations],['different','faithful'])
        self.assertEqual({x['job_id'] for x in observations},{critical['job'],favorable['job']})
        self.assertIn('MEANING_DIFFERENCE_OR_UNCERTAINTY',self.codes(assessment))

    def test_critical_call_from_prior_generation_survives_unsubmitted_result(self):
        case=self.f.formalize();review=self.f.review(case,'different',run=False)
        first=review['client'].call('claim')['lease']
        with patch('trading_researcher.controller_providers._invoke',return_value=self.f.result(review)):
            critical=review['client'].call('invoke_auxiliary_provider',lease=first,key='first-opinion')
        review['client'].call('block',lease=first,reason='First opinion retained without publishing a review artifact',
            needs=['retained meaning conflict'],retry_when='An unchanged target must not erase this opinion')
        self.f.op('resume',job_id=review['job'],reason='Exercise retained prior-generation accounting')
        faithful=deepcopy(review['output']);faithful['review'].update(judgment='faithful',unresolved_meaning=[])
        for mapping in faithful['review']['mapping_checks']:mapping['judgment']='faithful'
        reply=self.f.result({**review,'output':faithful})
        with patch('trading_researcher.controller_providers._invoke',return_value=reply):
            result=run_auxiliary_once(review['client'])
        self.assertTrue(result['accepted'],result)
        assessment=self.assess(case);job=assessment['body']['inventory']['jobs'][0]
        self.assertEqual([x['generation'] for x in job['attempts']],[1,2])
        self.assertEqual([x['generation'] for x in job['calls']],[1,2])
        self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
        self.assertTrue(any(g.get('call_id')==critical['receipt']['call_id']
            and g['code']=='MEANING_DIFFERENCE_OR_UNCERTAINTY' for g in assessment['body']['gaps']))

    def test_unfinished_inventory_stales_prior_assessment_and_cannot_reuse_key(self):
        case=self.f.formalize();self.f.review(case)
        original=self.assess(case);before=canonical(original)
        pending=self.f.review(case,'uncertain',run=False)
        status=self.f.op('inspect_meaning_review',assessment_id=original['id'])
        self.assertFalse(status['current']);self.assertEqual(status['independent_semantic_review'],'NOT_SATISFIED')
        with self.assertRaises(Conflict):self.assess(case)
        gap=self.assess(case,'complete-inventory')
        self.assertIn('REVIEW_INCOMPLETE',self.codes(gap))
        self.assertEqual(gap['body']['independent_semantic_review'],'NOT_SATISFIED')
        lease=pending['client'].call('claim')['lease']
        status=self.f.op('inspect_meaning_review',assessment_id=gap['id'])
        self.assertFalse(status['current'])
        pending['client'].call('block',lease=lease,reason='Known pending review retained',
            needs=['comparison'],retry_when='Keep the inventory incomplete')
        self.assertEqual(before,canonical(self.f.op('get_artifact',artifact_id=original['id'])))

    def test_source_policy_change_stales_even_a_positive_completed_assessment(self):
        case=self.f.formalize();self.f.review(case);assessment=self.assess(case)
        original=meaning.policy_identity();changed=deepcopy(original)
        changed['sources']['meaning_reviews.py']='0'*64
        with patch.object(meaning,'policy_identity',return_value=changed):
            status=self.f.op('inspect_meaning_review',assessment_id=assessment['id'])
            self.assertEqual(status['status'],'STALE')
            self.assertEqual(status['independent_semantic_review'],'NOT_SATISFIED')
            with self.assertRaises(Conflict):self.assess(case)
        self.assertEqual(self.assess(case),assessment)

    def test_review_cannot_move_target_to_fresh_epoch_budget(self):
        case=self.f.formalize();review=self.f.review(case,run=False)
        epoch=self.f.op('inspect_research_epoch',epoch_id=case['epoch'])
        request=epoch['request']
        fresh=self.f.op('create_research_epoch',key='attempted-budget-reset',**request)['id']
        spec=deepcopy(review['spec']);spec['research_epoch_id']=fresh
        before=self.f.broker._db.execute('SELECT COUNT(*) FROM job_specs').fetchone()[0]
        with self.assertRaisesRegex(Invalid,'original epoch'):
            self.f.op('enqueue',key='changed-budget',spec=spec)
        self.assertEqual(self.f.broker._db.execute('SELECT COUNT(*) FROM job_specs').fetchone()[0],before)
        self.assertEqual(self.f.op('inspect_research_epoch',epoch_id=fresh)['usage']['calls'],0)

    def test_protected_schema_and_operator_only_assessment_cannot_be_forged(self):
        case=self.f.formalize();review=self.f.review(case,run=False)
        lease=review['client'].call('claim')['lease'];assessment=self.assess(case)
        for schema in ('semantic-review-assessment/1','semantic-review-assessment/999'):
            with self.subTest(schema=schema):
                with self.assertRaises(Invalid):self.f.op('add_source',body={'schema':schema},data_class='development')
                with self.assertRaises(Invalid):
                    review['client'].call('put_artifact',lease=lease,body={'schema':schema},source_refs=[])
        for operation,args in [('assess_meaning_review',{'key':'worker-forgery','formalization_id':case['target']['id']}),
                ('inspect_meaning_review',{'assessment_id':assessment['id']})]:
            with self.subTest(operation=operation),self.assertRaises(Denied):review['client'].call(operation,**args)
        wrapper=self.f.op('add_source',body={'schema':'untrusted-wrapper/1','assessment':assessment['body']},data_class='development')
        with self.assertRaises(Invalid):self.f.op('inspect_meaning_review',assessment_id=wrapper['id'])

    def test_faithful_gap_review_never_promotes_candidate_and_old_record_stays_unverified(self):
        case=self.f.formalize(complete=False);review=self.f.review(case)
        record=self.f.op('get_artifact',artifact_id=review['outcome']['artifact_id']);before=canonical(record)
        assessment=self.assess(case)
        self.assertIn('FORMALIZATION_GAP',self.codes(assessment))
        self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
        self.assertFalse(assessment['body']['scientific_readiness'])
        self.assertEqual(record['body']['actual_independent_model_review'],'UNVERIFIED')
        self.assertEqual(before,canonical(self.f.op('get_artifact',artifact_id=record['id'])))

    def test_same_key_different_target_conflicts_even_when_both_have_review_gaps(self):
        first=self.f.formalize(complete=False);assessment=self.assess(first)
        second=self.f.formalize(complete=False)
        with self.assertRaises(Conflict):self.assess(second)
        self.assertEqual(self.f.op('get_artifact',artifact_id=assessment['id']),assessment)

    def test_corrupt_or_forged_receipts_are_typed_gaps_not_positive_assessments(self):
        case=self.f.formalize();review=self.f.review(case)
        record=self.f.op('get_artifact',artifact_id=review['outcome']['artifact_id'])
        call_id=record['body']['call_id']
        old=self.f.broker._db.execute('SELECT receipt FROM research_calls WHERE id=?',(call_id,)).fetchone()[0]
        receipt=json.loads(old)
        variants=['[]','{}','not-json',canonical({**receipt,'late':0}),canonical({**receipt,'call_id':'wrong-call'})]
        # Direct changes below simulate corruption of the local call projection,
        # not an authorized worker API. Immutable host artifacts stay unchanged.
        try:
            for index,raw in enumerate(variants):
                self.f.broker._db.execute('UPDATE research_calls SET receipt=? WHERE id=?',(raw,call_id))
                with self.subTest(index=index):
                    assessment=self.assess(case,'corrupt-receipt-'+str(index))
                    self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
                    self.assertIn('REVIEW_PROVENANCE_GAP',self.codes(assessment))
        finally:self.f.broker._db.execute('UPDATE research_calls SET receipt=? WHERE id=?',(old,call_id))

    def test_false_live_label_and_bad_prompt_cannot_be_selected_around(self):
        case=self.f.formalize();self.f.review(case,hosted=False)
        self.f.review(case,qualified=False);self.f.review(case)
        assessment=self.assess(case)
        self.assertEqual(len(assessment['body']['inventory']['jobs']),3)
        self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
        self.assertIn('REVIEW_PROVENANCE_GAP',self.codes(assessment))
        self.assertIn('REVIEW_PROTOCOL_GAP',self.codes(assessment))

    def test_historical_completion_restart_and_sqlite_backup_preserve_assessment(self):
        case=self.f.formalize();review=self.f.review(case)
        record=self.f.op('get_artifact',artifact_id=review['outcome']['artifact_id'])
        original_record=canonical(record);now=self.f.broker._now()
        self.f.broker.clock=lambda:now+3600
        assessment=self.assess(case)
        self.assertEqual(assessment['body']['independent_semantic_review'],'SATISFIED')
        backup=self.f.root/'assessment-backup.sqlite3'
        self.f.op('backup',destination=str(backup))
        with closing(sqlite3.connect('file:'+backup.as_posix()+'?mode=ro',uri=True)) as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            row=db.execute('SELECT artifact_id FROM meaning_review_assessments WHERE request_key=?',('assessment',)).fetchone()
            self.assertEqual(row[0],assessment['id'])
            envelope=db.execute('SELECT envelope FROM artifacts WHERE id=?',(row[0],)).fetchone()[0]
            self.assertEqual(json.loads(envelope)['body'],assessment['body'])
        self.f.broker.close();self.f.broker=Broker(self.f.root/'registry',clock=lambda:now+3600)
        self.assertEqual(self.assess(case),assessment)
        status=self.f.op('inspect_meaning_review',assessment_id=assessment['id'])
        self.assertTrue(status['current']);self.assertEqual(status['independent_semantic_review'],'SATISFIED')
        self.assertEqual(canonical(self.f.op('get_artifact',artifact_id=record['id'])),original_record)

    def test_unresolved_owned_review_dispatch_blocks_assessment_without_retry(self):
        case=self.f.formalize();self.f.review(case)
        pending=self.f.review(case,run=False);lease=pending['client'].call('claim')['lease']
        class Crash(BaseException):pass
        with patch('trading_researcher.controller_providers._invoke',side_effect=Crash):
            with self.assertRaises(Crash):pending['client'].call('invoke_auxiliary_provider',lease=lease,key='pending')
        assessment=self.assess(case)
        self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
        self.assertIn('REVIEW_INCOMPLETE',self.codes(assessment))
        self.assertIn('REVIEW_PROVENANCE_GAP',self.codes(assessment))
        state=self.f.op('inspect_research_epoch',epoch_id=case['epoch'])
        self.assertEqual(state['usage']['calls'],3)
        self.assertEqual(state['calls'][-1]['state'],'reserved')


if __name__=='__main__':unittest.main()
