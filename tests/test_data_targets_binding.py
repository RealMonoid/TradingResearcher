"""Public target bytes are invariant to private values, missingness and failure."""
from copy import deepcopy
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

import data_target_support as support
from trading_researcher.codec import Invalid, canonical
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.storage import restore_bundle


class TargetBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=support.Fixture();cls.addClassCleanup(cls.base.close)
        cls.backup=cls.base.root/'target-baseline'
        assert cls.base.op('backup_bundle',destination=str(cls.backup))['status']=='PASS'

    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        path=Path(temporary.name)/'registry'
        assert restore_bundle(self.backup,path,self.base.broker.directory/'operator.key')['status']=='PASS'
        self.f=object.__new__(support.Fixture);self.f.__dict__=self.base.__dict__.copy()
        self.f.broker=Broker(path);self.addCleanup(self.f.broker.close)
        self.f.token=self.f.broker.admin_token

    def test_real_formalization_binds_without_protected_artifacts_in_provider_request(self):
        case=self.f.formalize();before=canonical(case['provider_request'])
        private=self.f.bind();self.assertEqual(private['body']['status'],'TARGET_BOUND',private['body'])
        with patch.object(self.f.broker,'_load_reference_data',side_effect=AssertionError('Protected row expansion')):
            compiled=self.f.compile(case,private)
        self.assertEqual(compiled['body']['status'],'COMPILED',compiled['body'])
        self.assertEqual(compiled['body']['compilation_input']['candidate'],case['formalization']['body']['candidate'])
        self.assertEqual(compiled['body']['data_snapshot_id'],self.f.versions[0]['snapshot']['id'])
        self.assertEqual(compiled['body']['dependency_arguments']['data_target_binding_id'],private['id'])
        self.assertEqual(compiled['data_class'],'assessment')
        self.assertIn(private['id'],compiled['exposure'])
        self.assertNotIn(private['id'],case['formalization']['exposure'])
        for version in self.f.versions:
            for identity in (version['snapshot']['id'],version['certificate']['id'],version['certificate']['body']['definitions_id']):
                self.assertNotIn(identity,before)
        self.assertEqual(canonical(self.f.broker._auxiliary_packet_for_spec(case['spec'])),canonical(case['packet']))
        with self.assertRaises(Denied):self.f.op('execute_development',compiled_id=compiled['id'])
        self.assertFalse(compiled['body']['scientific_readiness'])

    def test_private_values_missingness_and_binding_failure_do_not_change_model_packets(self):
        case=self.f.formalize();spec,review=self.f.review_packet(case)
        public=canonical(self.f.target);before=canonical(case['packet']);review_before=canonical(review)
        for index,expected in ((0,'TARGET_BOUND'),(1,'TARGET_BOUND'),(2,'TARGET_BINDING_GAP')):
            private=self.f.bind(index,'bind-'+str(index))
            self.assertEqual(private['body']['status'],expected,private['body'])
            self.assertEqual(canonical(self.f.op('get_artifact',artifact_id=self.f.target['id'])),public)
            self.assertEqual(canonical(self.f.broker._auxiliary_packet_for_spec(case['spec'])),before)
            self.assertEqual(canonical(self.f.broker._auxiliary_packet_for_spec(spec)),review_before)
        self.assertFalse(self.f.target['body']['allocation_reserved'])

    def test_private_binding_and_wrappers_cannot_enter_discovery_or_review_contexts(self):
        private=self.f.bind()
        wrapper=self.f.op('add_source',body={'wrapper':'private binding'},data_class='development',exposure=[private['id']])
        for role in ('discovery','formalizer'):
            for artifact in (private,wrapper):
                with self.subTest(role=role,id=artifact['id']),self.assertRaises(Denied):
                    self.f.op('create_context',role=role,epoch=2,artifact_ids=[artifact['id']])

    def test_binding_is_explicit_never_automatically_selected(self):
        case=self.f.formalize();private=self.f.bind()
        self.assertEqual(private['body']['status'],'TARGET_BOUND')
        with self.assertRaises((Invalid,Denied)):
            self.f.op('compile_hypothesis',formalization_id=case['formalization']['id'],
                feature_certificate_id=self.f.versions[0]['certificate']['id'],reference_certificate_id=self.f.base.reference['id'],
                as_of='2024-01-02T00:00:00Z',max_steps=10000)
        with self.assertRaises(Invalid):self.f.compile(case,private,index=1)
        with self.assertRaises(Invalid):
            self.f.op('compile_hypothesis',formalization_id=case['formalization']['id'],
                feature_certificate_id=self.f.base.feature['id'],reference_certificate_id=self.f.base.reference['id'],
                as_of='2024-01-02T00:00:00Z',max_steps=10000,data_target_binding_id=None)

    def test_review_receives_original_declared_scope_and_requires_its_explicit_context(self):
        case=self.f.formalize({'start':'2024-01-01T00:30:00Z'});spec,packet=self.f.review_packet(case)
        self.assertEqual(packet['data_target'],self.f.target)
        self.assertNotEqual(packet['data_target']['body']['request']['universe']['start'],
            packet['formalization']['body']['candidate']['test_universe']['start'])
        with self.assertRaises(Invalid):self.f.compile(case,self.f.bind())
        context=self.f.broker._context(spec['context_id'])
        missing=self.f.op('create_context',role='formalizer',epoch=2,
            artifact_ids=[identity for identity in context['artifact_ids'] if identity!=self.f.target['id']])
        with self.assertRaises(Denied):self.f.broker._auxiliary_packet_for_spec({**spec,'context_id':missing['id']})

    def test_active_worker_can_read_only_public_target_not_private_binding_or_rows(self):
        private=self.f.bind()
        worker=self.f.op('register_worker',name='reader',role='formalizer',capabilities=['formalization/v1'])['token']
        context=self.f.op('create_context',role='formalizer',epoch=1,artifact_ids=[self.f.target['id']])
        self.f.op('enqueue',key='reader',spec={'kind':'formalization/v1','context_id':context['id'],
            'purpose':'Synthetic capability inspection','allowed_workers':['reader'],'max_attempts':1,
            'lease_seconds':300,'deadline':int(time.time())+3600,'dependencies':[]})
        lease=self.f.broker.call(worker,'claim')['lease']
        self.assertEqual(self.f.broker.call(worker,'read_artifact',lease=lease,artifact_id=self.f.target['id']),self.f.target)
        for identity in (private['id'],self.f.versions[0]['snapshot']['id'],self.f.versions[0]['certificate']['id']):
            with self.subTest(identity=identity),self.assertRaises(Denied):
                self.f.broker.call(worker,'read_artifact',lease=lease,artifact_id=identity)

    def test_private_binding_survives_complete_backup_and_restore(self):
        private=self.f.bind();destination=self.f.broker.directory.parent/'backup'
        self.assertEqual(self.f.op('backup_bundle',destination=str(destination))['status'],'PASS')
        restored=self.f.broker.directory.parent/'restored'
        self.assertEqual(restore_bundle(destination,restored,self.f.broker.directory/'operator.key')['status'],'PASS')
        broker=Broker(restored)
        try:
            self.assertEqual(broker.call(broker.admin_token,'get_artifact',artifact_id=private['id']),private)
            self.assertEqual(broker._checked_target_binding({},private['id']),private)
        finally:broker.close()

    def test_owned_meaning_assessment_maps_only_the_exact_declared_public_definition(self):
        from trading_researcher.auxiliary import mapping_count, run_auxiliary_once
        from trading_researcher.meaning_reviews import profile
        from trading_researcher.researcher import ScriptedProvider
        from test_researcher import LocalClient
        case=self.f.formalize();private=self.f.bind();compiled=self.f.compile(case,private)
        spec,_=self.f.review_packet(case)
        spec['research_call_profile']=profile(self.f.common)
        worker=self.f.op('register_worker',name='independent-reviewer',role='formalizer',capabilities=['semantic-review/v1'])['token']
        self.f.op('enqueue',key='review',spec=spec)
        review={'judgment':'faithful','reason':'Scripted integration assertion, not independent model-quality evidence.',
            'added_assumptions':[],'omitted_assumptions':[],'conflicts':[],'unresolved_meaning':[],
            'mapping_checks':[{'segment':index,'judgment':'faithful','reason':'Synthetic test mapping.'}
                for index in range(mapping_count(case['formalization']))]}
        result=run_auxiliary_once(LocalClient(self.f.broker,worker),
            ScriptedProvider([{'status':'final','review':review}],model=self.f.common['model'],mode='live'))
        self.assertTrue(result['accepted'],result)
        assessment=self.f.op('assess_meaning_review',key='meaning',formalization_id=case['formalization']['id'])
        _,definition_id=self.f.broker._plan_meaning_reference({'compiled_id':compiled['id'],'meaning_review_id':assessment['id']})
        self.assertEqual(definition_id,self.f.target['body']['definitions_id'])
        self.assertNotEqual(definition_id,self.f.versions[0]['certificate']['body']['definitions_id'])
        # Exercise the final mapping check independently of the earlier packet
        # guard, with a fault injected after owned artifact-integrity validation.
        original=self.f.broker._artifact
        def changed(identity):
            value=original(identity)
            if identity==assessment['id']:
                value=deepcopy(value)
                for job in value['body']['inventory']['jobs']:
                    job['spec']['research_inputs']['definition_ids']=[self.f.versions[0]['certificate']['body']['definitions_id']]
            return value
        with patch.object(self.f.broker,'_artifact',side_effect=changed),self.assertRaises(Invalid):
            self.f.broker._plan_meaning_reference({'compiled_id':compiled['id'],'meaning_review_id':assessment['id']})

    def test_key_replay_is_exact_and_changed_binding_conflicts(self):
        private=self.f.bind();self.assertEqual(self.f.bind(),private)
        with self.assertRaises(Conflict):self.f.bind(1)
        target=self.f.op('declare_data_target',**self.f.target['body']['request'])
        self.assertEqual(target,self.f.target)
        with self.assertRaises(Conflict):self.f.op('declare_data_target',**{**self.f.target['body']['request'],'partition':'corroboration'})

    def test_review_requires_exact_public_definitions_not_equal_named_replacements(self):
        case=self.f.formalize();spec,_=self.f.review_packet(case)
        private=self.f.bind();self.assertEqual(private['body']['status'],'TARGET_BOUND')
        definition=self.f.op('get_artifact',artifact_id=self.f.target['body']['definitions_id'])
        other=deepcopy(definition);other.pop('id');other['body']['created_at']+=1
        with self.f.broker._transaction():other=self.f.broker._save_artifact(other)
        with self.assertRaises(Invalid):self.f.broker._declared_definition_origins([other],self.f.target['body']['catalog_id'],self.f.target['id'])
        protected=self.f.op('get_artifact',artifact_id=self.f.versions[0]['certificate']['body']['definitions_id'])
        with self.assertRaises(Invalid):self.f.broker._declared_definition_origins([protected],self.f.target['body']['catalog_id'],self.f.target['id'])

    def test_revoked_private_version_blocks_new_compile_without_changing_public_target(self):
        case=self.f.formalize();private=self.f.bind();public=canonical(self.f.target)
        defect=self.f.op('add_source',body={'defect':'Synthetic invalidation'},data_class='operations')
        self.f.op('revoke_dependency',key='defect',dependency_id=self.f.versions[0]['certificate']['id'],
            reason='Synthetic defect',evidence_refs=[defect['id']])
        with self.assertRaises(Denied):self.f.compile(case,private)
        self.assertEqual(canonical(self.f.op('get_artifact',artifact_id=self.f.target['id'])),public)
        self.assertEqual(canonical(self.f.broker._auxiliary_packet_for_spec(case['spec'])),canonical(case['packet']))

    def test_declaration_rejects_protected_semantics_before_any_public_artifact(self):
        with self.assertRaises(Invalid):self.f.op('declare_data_target',key='bad',partition='assessment',universe=support.UNIVERSE,
            development_feature_certificate_id=self.f.versions[0]['certificate']['id'])

    def test_workers_cannot_declare_or_bind(self):
        token=self.f.op('register_worker',name='untrusted',role='formalizer',capabilities=[])['token']
        for operation,args in [('declare_data_target',self.f.target['body']['request']),
                ('bind_data_target',{'key':'bad','target_id':self.f.target['id'],
                    'data_snapshot_id':self.f.versions[0]['snapshot']['id'],'feature_certificate_id':self.f.versions[0]['certificate']['id']})]:
            with self.subTest(operation=operation),self.assertRaises(Denied):self.f.broker.call(token,operation,**args)


if __name__=='__main__':unittest.main()
