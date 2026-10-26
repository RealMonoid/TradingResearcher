"""Private draft preparation with real owned synthetic data and exact binding.

Only provider-document pins are substituted for synthetic fixture text. This
exercises no real provider acceptance, market inference or model judgment.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import data_target_support as support
from trading_researcher import data_use, evaluation_plans
from trading_researcher.codec import Invalid, canonical
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.storage import restore_bundle


class ProtectedPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=support.Fixture(private_versions=1);cls.addClassCleanup(cls.base.close)
        fixture=cls.base
        fixture.common['max_output_tokens']=8192
        fixture.base.base=deepcopy(fixture.base.base)
        candidate=fixture.base.base['candidate']
        candidate['estimand']['unit']='ratio'
        candidate['outcome']['scale']='binary_probability'
        candidate['outcome']['program']['expression']={'op':'literal','type':'boolean','unit':None,'value':True}
        candidate['parameter_origins'].append({'path':'/outcome/program/expression/value',
            'basis':'preexisting_specification','source_refs':[],'rationale':'Synthetic infrastructure input only'})
        cls.development=fixture.base.compile()
        assert cls.development['body']['status']=='COMPILED',cls.development['body']
        cls.diagnostic=fixture.op('execute_development',compiled_id=cls.development['id'])
        assert cls.diagnostic['body']['status']=='DESCRIPTIVE_EXECUTION',cls.diagnostic['body']
        cls.case=fixture.formalize();cls.private=fixture.bind();cls.compiled=fixture.compile(cls.case,cls.private)
        assert cls.compiled['body']['status']=='COMPILED',cls.compiled['body']
        cls.backup=fixture.root/'protected-plan-baseline'
        assert fixture.op('backup_bundle',destination=str(cls.backup))['status']=='PASS'

    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        path=Path(temporary.name)/'registry'
        assert restore_bundle(self.backup,path,self.base.broker.directory/'operator.key')['status']=='PASS'
        self.f=object.__new__(support.Fixture);self.f.__dict__=self.base.__dict__.copy()
        self.f.broker=Broker(path);self.addCleanup(self.f.broker.close);self.f.token=self.f.broker.admin_token
        checksum=hashlib.sha256(b'Synthetic provider-document fixture\n').hexdigest()
        pins=patch.object(data_use,'REVIEWED_DOCUMENTS',{name:checksum for name in data_use.REVIEWED_DOCUMENTS})
        pins.start();self.addCleanup(pins.stop);self.pins=pins

    def op(self,operation,**args):return self.f.op(operation,**args)

    def assess(self):return self.op('assess_data_use',compiled_id=self.compiled['id'])

    def request(self,key='private-plan',assessment=None):
        return {'key':key,'compiled_id':self.compiled['id'],'primary_count':2,
            'data_use_assessment_id':(assessment or self.assess())['id'],
            'dependence':{'base_length':4,'rationale':'Synthetic development design; adequacy remains pending.',
                'development_refs':[self.diagnostic['id']],
                'randomness':{'algorithm':'fixture-generator','version':'1','seed':17}}}

    def clone(self,artifact,**updates):
        value=deepcopy(artifact);value.pop('id');value.update(updates)
        with self.f.broker._transaction():return self.f.broker._save_artifact(value)

    def revoke(self):
        defect=self.op('add_source',body={'text':'Synthetic feature defect'},data_class='operations')
        return self.op('revoke_dependency',key='private-defect',dependency_id=self.private['body']['request']['feature_certificate_id'],
            reason='Synthetic defect',evidence_refs=[defect['id']])

    def test_exact_private_data_qualifies_without_inventing_unseen_history(self):
        with patch.object(self.f.broker,'_load_reference_data',side_effect=AssertionError('Protected outcome read')):
            assessment=self.assess();view=self.op('inspect_data_use',assessment_id=assessment['id'])
        self.assertEqual(view['status'],'QUALIFIED_PRIVATE_PLAN_DATA',assessment['body'])
        self.assertEqual(view['qualified_protected_target_data_use'],'SATISFIED')
        self.assertEqual(view['qualified_exploration_data_use'],'NOT_SATISFIED')
        findings=assessment['body']['findings']
        self.assertEqual(findings['scope']['data_target_binding_id'],self.private['id'])
        self.assertEqual(findings['scope']['public_target_id'],self.f.target['id'])
        self.assertNotIn(self.private['id'],findings['prior_knowledge']['artifact_ids'])
        self.assertIn(self.f.target['id'],findings['prior_knowledge']['artifact_ids'])
        self.assertIsNone(findings['exposure']['evidence_origin'])
        self.assertEqual(findings['exposure']['model_training_exposure'],'UNKNOWN')
        self.assertFalse(findings['exposure']['reserved_role_verified'])
        self.assertFalse(findings['exposure']['independent_confirmation'])
        self.assertFalse(findings['availability']['historical_vintage_verified'])
        self.assertEqual(findings['availability']['basis'],'assumed')
        self.assertFalse(view['protected_target_admission'])

    def test_private_plan_consumes_development_diagnostics_and_keeps_remaining_gates(self):
        request=self.request()
        before=canonical(self.f.broker._auxiliary_packet_for_spec(self.case['spec']))
        with patch.object(self.f.broker,'_load_reference_data',side_effect=AssertionError('Protected outcome read')):
            plan=self.op('prepare_evaluation_plan',**request)
        self.assertEqual(plan['body']['status'],'POLICY_DRAFT',plan['body'])
        capsule=self.op('get_artifact',artifact_id=plan['body']['input_capsule_id'])
        self.assertEqual((plan['data_class'],capsule['data_class']),('assessment','assessment'))
        self.assertEqual(capsule['body']['data_use_at_preparation'],plan['body']['data_use_at_preparation'])
        self.assertEqual(capsule['body']['payload']['candidate'],self.case['formalization']['body']['candidate'])
        self.assertIn(self.diagnostic['id'],plan['exposure'])
        view=self.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertEqual(view['data_use_scope'],'exact_private_target_preparation_only')
        self.assertEqual(view['protected_selection_and_reservation_review'],'NOT_ASSESSED')
        for gate in ('scientific_data_and_exposure_acceptance','atomic_allocation_and_freeze'):
            self.assertIn(gate,view['current_remaining_gates'])
        for key in ('frozen','allocation_reserved','scientific_readiness'):self.assertFalse(view[key])
        self.assertEqual(self.op('prepare_evaluation_plan',**request),plan)
        self.assertEqual(canonical(self.f.broker._auxiliary_packet_for_spec(self.case['spec'])),before)
        with self.assertRaises(Denied):self.op('execute_development',compiled_id=self.compiled['id'])

    def test_private_assessment_plan_and_wrappers_are_unavailable_to_research_roles(self):
        assessment=self.assess();plan=self.op('prepare_evaluation_plan',**self.request(assessment=assessment))
        wrapper=self.op('add_source',body={'text':'Private plan wrapper'},data_class='development',exposure=[plan['id']])
        for role in ('discovery','formalizer'):
            for value in (assessment,plan,wrapper):
                with self.subTest(role=role,id=value['id']),self.assertRaises(Denied):
                    self.op('create_context',role=role,epoch=3,artifact_ids=[value['id']])
        for operation,args in [('assess_data_use',{'compiled_id':self.compiled['id']}),
                ('inspect_data_use',{'assessment_id':assessment['id']}),('prepare_evaluation_plan',self.request())]:
            with self.subTest(operation=operation),self.assertRaises(Denied):self.f.broker.call(self.case['worker'],operation,**args)

    def test_missing_or_other_compilation_qualification_cannot_prepare(self):
        request=self.request();request.pop('data_use_assessment_id')
        with self.assertRaises(Denied):self.op('prepare_evaluation_plan',**request)
        other=self.op('assess_data_use',compiled_id=self.development['id'])
        with self.assertRaises(Invalid):self.op('prepare_evaluation_plan',**self.request(assessment=other))

    def test_unreviewed_rights_keep_gap_and_public_packet_unchanged(self):
        before=canonical(self.f.broker._auxiliary_packet_for_spec(self.case['spec']))
        self.pins.stop();assessment=self.assess()
        self.assertEqual(assessment['body']['status'],'DATA_USE_GAP')
        self.assertIn('PROVIDER_DOCUMENT_REVIEW_REQUIRED',assessment['body']['findings']['gaps'])
        with self.assertRaises(Invalid):self.op('prepare_evaluation_plan',**self.request(assessment=assessment))
        self.assertEqual(canonical(self.f.broker._auxiliary_packet_for_spec(self.case['spec'])),before)

    def test_actual_opaque_candidate_ancestry_is_retained_and_prevents_private_preparation(self):
        wrapper=self.op('add_source',body={'text':'Earlier unspecified inquiry'},data_class='development',exposure=['opaque:prior-inquiry'])
        original=self.f.op
        def with_ancestry(operation,**args):
            if operation=='add_research':args={**args,'source_refs':[wrapper['id']]}
            return original(operation,**args)
        with patch.object(self.f,'op',side_effect=with_ancestry):case=self.f.formalize()
        compiled=self.f.compile(case,self.private)
        assessment=self.op('assess_data_use',compiled_id=compiled['id'])
        self.assertEqual(assessment['body']['status'],'DATA_USE_GAP')
        self.assertIn('UNRESOLVED_CANDIDATE_EXPOSURE',assessment['body']['findings']['gaps'])

    def test_protected_or_unresolved_diagnostic_ancestry_blocks_before_child(self):
        protected=self.op('add_source',body={'text':'Protected diagnostic knowledge'},data_class='assessment')
        for ref in (protected['id'],'opaque:diagnostic-selection'):
            diagnostic=self.clone(self.diagnostic,exposure=sorted(set(self.diagnostic['exposure'])|{ref}))
            request=self.request('bad-diagnostic-'+ref)
            request['dependence']['development_refs']=[diagnostic['id']]
            with self.subTest(ref=ref),patch('trading_researcher.evaluation_plans.run_plan_child',side_effect=AssertionError('Invalid ancestry reached child')):
                with self.assertRaises((Invalid,Denied)):self.op('prepare_evaluation_plan',**request)

    def test_wrong_snapshot_or_protected_diagnostic_cannot_replace_declared_development(self):
        body={**self.diagnostic['body'],'data_snapshot_id':self.f.versions[0]['snapshot']['id']}
        diagnostic=self.clone(self.diagnostic,body=body)
        for identity in (diagnostic['id'],self.compiled['id']):
            request=self.request('wrong-diagnostic-'+identity);request['dependence']['development_refs']=[identity]
            with self.subTest(identity=identity),self.assertRaises(Denied):self.op('prepare_evaluation_plan',**request)

    def test_revocation_between_child_and_commit_retains_only_private_interruption(self):
        original=evaluation_plans.run_plan_child;calls=[]
        def revoke_after_child(*args,**kwargs):
            result=original(*args,**kwargs);calls.append(True)
            if len(calls)==1:self.revoke()
            return result
        request=self.request()
        with patch('trading_researcher.evaluation_plans.run_plan_child',side_effect=revoke_after_child):
            with self.assertRaises((Invalid,Denied)):self.op('prepare_evaluation_plan',**request)
        self.assertIsNone(self.f.broker._existing_evaluation_plan(request))
        capsule=self.f.broker._existing_plan_input(request)
        self.assertEqual(capsule['data_class'],'assessment')

    def test_interrupted_private_capsule_can_retry_without_changing_input(self):
        request=self.request()
        with patch('trading_researcher.evaluation_plans.run_plan_child',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.op('prepare_evaluation_plan',**request)
        capsule=self.f.broker._existing_plan_input(request)
        plan=self.op('prepare_evaluation_plan',**request)
        self.assertEqual(plan['body']['input_capsule_id'],capsule['id'])
        self.assertEqual(plan['body']['status'],'POLICY_DRAFT')

    def test_backup_restore_preserves_private_qualification_and_plan(self):
        assessment=self.assess();plan=self.op('prepare_evaluation_plan',**self.request(assessment=assessment))
        with tempfile.TemporaryDirectory() as temporary:
            bundle=Path(temporary)/'backup';restored=Path(temporary)/'restored'
            self.assertEqual(self.op('backup_bundle',destination=str(bundle))['status'],'PASS')
            self.assertEqual(restore_bundle(bundle,restored,self.f.broker.directory/'operator.key')['status'],'PASS')
            broker=Broker(restored)
            try:
                self.assertEqual(broker.call(broker.admin_token,'get_artifact',artifact_id=plan['id']),plan)
                view=broker.call(broker.admin_token,'inspect_evaluation_plan',plan_id=plan['id'])
                self.assertEqual(view['data_use']['qualified_protected_target_data_use'],'SATISFIED')
                self.assertFalse(view['protected_target_admission'])
            finally:broker.close()

    def test_private_plan_consumes_owned_composition_and_public_meaning_evidence(self):
        from trading_researcher.auxiliary import mapping_count, run_auxiliary_once
        from trading_researcher.meaning_reviews import profile
        from trading_researcher.researcher import ScriptedProvider
        from test_researcher import LocalClient
        composition=self.op('certify_composition',compiled_id=self.compiled['id'])
        self.assertEqual(composition['body']['status'],'CONFORMANT',composition['body'])
        spec,_=self.f.review_packet(self.case);spec['research_call_profile']=profile(self.f.common)
        worker=self.op('register_worker',name='independent-reviewer',role='formalizer',capabilities=['semantic-review/v1'])['token']
        self.op('enqueue',key='review',spec=spec)
        review={'judgment':'faithful','reason':'Scripted transport fixture, not a model-quality result.',
            'added_assumptions':[],'omitted_assumptions':[],'conflicts':[],'unresolved_meaning':[],
            'mapping_checks':[{'segment':index,'judgment':'faithful','reason':'Synthetic mapping.'}
                for index in range(mapping_count(self.case['formalization']))]}
        result=run_auxiliary_once(LocalClient(self.f.broker,worker),
            ScriptedProvider([{'status':'final','review':review}],model=self.f.common['model'],mode='live'))
        self.assertTrue(result['accepted'],result)
        meaning=self.op('assess_meaning_review',key='meaning',formalization_id=self.case['formalization']['id'])
        plan=self.op('prepare_evaluation_plan',**self.request(),composition_certificate_id=composition['id'],meaning_review_id=meaning['id'])
        self.assertEqual(plan['body']['status'],'POLICY_DRAFT')
        view=self.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertEqual(view['composition']['composition_conformance'],'SATISFIED')
        self.assertNotIn('composition_conformance',view['current_remaining_gates'])
        self.assertEqual(view['meaning_review']['required_definition_id'],self.f.target['body']['definitions_id'])
        # A single scripted review does not establish the complete independent
        # comparison prerequisite. Its correct binding must not close that gate.
        self.assertEqual(view['meaning_review']['independent_semantic_review'],'NOT_SATISFIED')
        self.assertIn('independent_semantic_review',view['current_remaining_gates'])
        self.assertIn('scientific_data_and_exposure_acceptance',view['current_remaining_gates'])
        self.assertFalse(view['scientific_readiness'])

    def test_private_host_exception_never_admits_final_calibration_ancestry(self):
        assessment=self.assess()
        calibration={'version':'local-artifact/1','creator':'controller','origin':'controller','data_class':'assessment',
            'source_refs':[],'exposure':[],'authority':'test-only-fault-injection',
            'body':{'schema':'evaluator-calibration-input/1'}}
        with self.f.broker._transaction():calibration=self.f.broker._save_artifact(calibration)
        wrapped=self.clone(assessment,exposure=sorted(set(assessment['exposure'])|{calibration['id']}))
        request=self.request(assessment=wrapped)
        with patch('trading_researcher.evaluation_plans.run_plan_child',side_effect=AssertionError('Calibration reached preparation')):
            with self.assertRaises(Denied):self.op('prepare_evaluation_plan',**request)


if __name__=='__main__':unittest.main()
