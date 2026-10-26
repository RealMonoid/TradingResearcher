"""Owned data-use path with synthetic market bytes and explicit document-pin substitution.

All normalization, feature replay, formalization, compilation and plan paths are
real. Only the reviewed document hash is substituted for the synthetic fixture;
this proves no real-provider licensing. Real retained documents are checked by
the separately retained local integration observation.
"""
import hashlib
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_evaluation_plans as support
from trading_researcher import data_use, evaluation_plans
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied
from trading_researcher.storage import restore_bundle


class DataUseBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        support.EvaluationPlanTests.setUpClass()
        cls.base=support.EvaluationPlanTests;cls.addClassCleanup(cls.base.tearDownClass)
        cls.backup=cls.base.fixture.root/'data-use-baseline'
        assert cls.base.broker.call(cls.base.token,'backup_bundle',destination=str(cls.backup))['status']=='PASS'

    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        restored=Path(temporary.name)/'registry'
        assert restore_bundle(self.backup,restored,self.base.broker.directory/'operator.key')['status']=='PASS'
        self.broker=Broker(restored);self.addCleanup(self.broker.close);self.token=self.broker.admin_token
        self.compiled,self.execution=self.base.compiled,self.base.execution
        checksum=hashlib.sha256(b'Synthetic provider-document fixture\n').hexdigest()
        self.pins=patch.object(data_use,'REVIEWED_DOCUMENTS',{name:checksum for name in data_use.REVIEWED_DOCUMENTS})
        self.pins.start();self.addCleanup(self.pins.stop)

    def op(self,operation,**args):return self.broker.call(self.token,operation,**args)

    def assess(self):return self.op('assess_data_use',compiled_id=self.compiled['id'])

    def request(self,key='plan',assessment=None):
        return {**support.EvaluationPlanTests.arguments(self,key),
            'data_use_assessment_id':(assessment or self.assess())['id']}

    def revoke(self,identity):
        evidence=self.op('add_source',body={'defect':'Synthetic test only'},data_class='operations')
        return self.op('revoke_dependency',key='revoke',dependency_id=identity,
            reason='Synthetic defect',evidence_refs=[evidence['id']])

    def test_qualified_development_retains_exposure_delay_and_unknown_origin(self):
        with patch.object(self.broker,'_load_reference_data',side_effect=AssertionError('Outcome read')):
            assessment=self.assess()
            current=self.op('inspect_data_use',assessment_id=assessment['id'])
        self.assertEqual(current['status'],'QUALIFIED_EXPLORATION',assessment['body'])
        findings=assessment['body']['findings']
        self.assertTrue(findings['exposure']['target_in_candidate_ancestry'])
        self.assertIsNone(findings['exposure']['evidence_origin'])
        self.assertEqual(findings['exposure']['model_training_exposure'],'UNKNOWN')
        self.assertFalse(findings['exposure']['independent_confirmation'])
        self.assertEqual(findings['availability']['delay_seconds'],self.base.fixture.base['delay_seconds'])
        self.assertEqual(findings['availability']['basis'],'assumed')
        self.assertIsNone(findings['availability']['historical_publication_time'])
        self.assertFalse(findings['availability']['historical_vintage_verified'])
        self.assertNotIn(self.compiled['body']['source_package_id'],findings['prior_knowledge']['artifact_ids'])
        self.assertFalse(current['scientific_readiness'])
        self.assertFalse(current['protected_target_admission'])

    def test_unreviewed_document_bytes_retain_gap_despite_documented_rights_prose(self):
        self.pins.stop()
        assessment=self.assess()
        self.assertEqual(assessment['body']['status'],'DATA_USE_GAP')
        self.assertEqual(assessment['body']['findings']['gaps'],['PROVIDER_DOCUMENT_REVIEW_REQUIRED'])
        self.assertEqual(self.op('inspect_data_use',assessment_id=assessment['id'])['qualified_exploration_data_use'],'NOT_SATISFIED')

    def test_worker_cannot_assess_or_inspect(self):
        token=self.op('register_worker',name='worker',role='formalizer',capabilities=[])['token']
        for operation,args in [('assess_data_use',{'compiled_id':self.compiled['id']}),
                ('inspect_data_use',{'assessment_id':'unavailable'})]:
            with self.subTest(operation=operation),self.assertRaises(Denied):self.broker.call(token,operation,**args)

    def test_assessment_cannot_transfer_to_different_compilation(self):
        assessment=self.assess()
        other=self.op('compile_hypothesis',**{**self.compiled['body']['dependency_arguments'],'max_steps':9999})
        with self.assertRaises(Invalid):self.op('inspect_data_use',assessment_id=assessment['id'],compiled_id=other['id'])
        with self.assertRaises(Invalid):self.op('prepare_evaluation_plan',**{**self.request(assessment=assessment),'compiled_id':other['id']})

    def test_plan_view_closes_only_scoped_gate_and_preserves_historical_records(self):
        plan=self.op('prepare_evaluation_plan',**self.request())
        view=self.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertEqual(view['current_remaining_gates'],[g for g in plan['body']['plan']['remaining_gates'] if g!='scientific_data_and_exposure_acceptance'])
        self.assertEqual(view['data_use_scope'],'exact_compiled_development_exploration_only')
        self.assertFalse(view['protected_target_admission'])
        self.assertFalse(view['scientific_readiness'])
        self.assertIn('scientific_data_and_exposure_acceptance',plan['body']['plan']['remaining_gates'])
        capsule=self.op('get_artifact',artifact_id=plan['body']['input_capsule_id'])
        self.assertEqual(capsule['body']['data_use_at_preparation'],plan['body']['data_use_at_preparation'])
        self.assertEqual(self.op('get_artifact',artifact_id=plan['id']),plan)

    def test_revocation_invalidates_use_and_plan_without_rewriting_history(self):
        assessment=self.assess();plan=self.op('prepare_evaluation_plan',**self.request(assessment=assessment))
        revocation=self.revoke(self.compiled['body']['data_snapshot_id'])
        self.assertIn(assessment['id'],revocation['body']['affected_artifact_ids'])
        self.assertIn(plan['id'],revocation['body']['affected_artifact_ids'])
        view=self.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertEqual(view['data_use']['status'],'INVALIDATED_BY_DEPENDENCY')
        self.assertIn('scientific_data_and_exposure_acceptance',view['current_remaining_gates'])
        self.assertEqual(self.op('get_artifact',artifact_id=assessment['id']),assessment)
        self.assertEqual(self.assess()['body']['status'],'DATA_USE_GAP')

    def test_review_policy_change_reopens_existing_pass(self):
        assessment=self.assess();self.pins.stop()
        self.assertEqual(self.op('inspect_data_use',assessment_id=assessment['id'])['status'],'STALE_EVIDENCE')

    def test_availability_parameter_mismatch_is_not_hidden_by_matching_feature_names(self):
        assessment=self.assess();original=self.broker._artifact
        definition_id=assessment['body']['findings']['scope']['feature_definitions_id']
        def changed(identity):
            value=original(identity)
            if identity==definition_id:
                value=deepcopy(value);value['body']['parameters']['delay_seconds']+=1
            return value
        # Inject after normal artifact integrity verification to exercise the
        # separate parameter-binding check, not just the content-address check.
        with patch.object(self.broker,'_artifact',side_effect=changed):
            self.assertEqual(self.op('inspect_data_use',assessment_id=assessment['id'])['status'],'QUARANTINED')
            self.assertEqual(self.assess()['body']['status'],'DATA_USE_GAP')

    def test_original_worker_context_is_required(self):
        original=self.broker._context
        def changed(identity):
            value=deepcopy(original(identity));value['artifact_ids'].append('missing-authorized-source')
            return value
        with patch.object(self.broker,'_context',side_effect=changed):
            assessment=self.assess()
        self.assertEqual(assessment['body']['status'],'DATA_USE_GAP')
        self.assertIsNone(assessment['body']['findings'])

    def test_cancellation_keeps_plan_input_bound_to_data_use(self):
        request=self.request('cancel')
        with patch.object(evaluation_plans,'run_plan_child',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.op('prepare_evaluation_plan',**request)
        attempt=self.op('inspect_bound_computations')['attempts'][0]
        capsule=self.op('get_artifact',artifact_id=attempt['retained_input_id'])
        self.assertEqual(capsule['body']['data_use_at_preparation']['assessment_id'],request['data_use_assessment_id'])
        plan=self.op('prepare_evaluation_plan',**request)
        self.assertEqual(plan['body']['input_capsule_id'],capsule['id'])

    def test_backup_restore_preserves_owned_assessment(self):
        assessment=self.assess();destination=self.broker.directory.parent/'backup'
        self.assertEqual(self.op('backup_bundle',destination=str(destination))['status'],'PASS')
        restored=self.broker.directory.parent/'restored'
        self.assertEqual(restore_bundle(destination,restored,self.broker.directory/'operator.key')['status'],'PASS')
        broker=Broker(restored)
        try:
            self.assertEqual(broker.call(broker.admin_token,'get_artifact',artifact_id=assessment['id']),assessment)
            self.assertEqual(broker.call(broker.admin_token,'inspect_data_use',assessment_id=assessment['id'])['status'],'QUALIFIED_EXPLORATION')
        finally:broker.close()

    def test_current_checker_change_cannot_reuse_pass(self):
        assessment=self.assess()
        with patch.object(data_use,'LOADED_SELF','0'*64):
            self.assertEqual(self.op('inspect_data_use',assessment_id=assessment['id'])['status'],'STALE_CHECKER')
            with self.assertRaises(Invalid):self.assess()

    def test_revocation_during_plan_preparation_prevents_commit(self):
        request=self.request('race');original=evaluation_plans.run_plan_child;calls=0
        def revoke_during(*args,**kwargs):
            nonlocal calls
            result=original(*args,**kwargs);calls+=1
            if calls==1:self.revoke(self.compiled['body']['data_snapshot_id'])
            return result
        with patch.object(evaluation_plans,'run_plan_child',side_effect=revoke_during):
            with self.assertRaises((Invalid,Denied)):self.op('prepare_evaluation_plan',**request)
        attempt=self.op('inspect_bound_computations')['attempts'][0]
        self.assertEqual(attempt['state'],'INTERRUPTED')
        self.assertIsNone(attempt['artifact_id'])
        self.assertIsNotNone(attempt['retained_input_id'])

    def test_legacy_plan_keeps_gate_without_implicit_data_admission(self):
        plan=self.op('prepare_evaluation_plan',**support.EvaluationPlanTests.arguments(self))
        self.assertNotIn('data_use_at_preparation',plan['body'])
        view=self.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertIsNone(view['data_use'])
        self.assertEqual(view['current_remaining_gates'],plan['body']['plan']['remaining_gates'])


if __name__=='__main__':unittest.main()
