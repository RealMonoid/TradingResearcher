"""Full synthetic data/feature/compile/review/plan integration; no live model calls."""
from copy import deepcopy
import time
import unittest
from unittest.mock import patch

import binding_support
from controller_provider_support import Fixture as ProviderFixture
from test_researcher import LocalClient
from trading_researcher import evaluation_plans, openai_provider
from trading_researcher.auxiliary import mapping_count, run_auxiliary_once
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.meaning_reviews import profile
from trading_researcher.researcher import ScriptedProvider


class PlanReviewBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=binding_support.BindingFixture()
        cls.addClassCleanup(cls.f.close)
        directory=cls.f.broker.directory
        cls.f.broker.close()
        cls.config=openai_provider.configuration(input_token_limit=20000,output_token_limit=1024)
        cls.f.broker=cls.f.normalizer.broker=Broker(directory,provider_routes={openai_provider.MODEL:{
            'provider':'openai','key_file':str(directory/'unused-key'),'budget_file':str(directory/'unused-budget'),
            'config':cls.config}})
        cls.broker=cls.f.broker
        cls.token=cls.broker.admin_token
        for name in ('review-first','review-second'):
            cls.op('register_worker',name=name,role='discovery',capabilities=['research-record/v1'])
        cls.common={'model':openai_provider.MODEL,'prompt_version':'synthetic-plan-review/1',
            'generation_parameters':{'openai_responses':cls.config},'max_output_tokens':1024,
            'call_timeout_seconds':10,'max_retries':0}
        context=cls.op('create_context',role='discovery',epoch=1,
            artifact_ids=[cls.f.snapshot['body']['catalog_id']])['id']
        cls.epoch=cls.op('create_research_epoch',key='review-plan',context_id=context,
            workers=['review-first','review-second'],profile={**cls.common,'mode':'live','currency':'USD',
                'max_calls':12,'max_tokens':80000,'max_seconds':1800,'max_cost_units':5000000000,
                'tools':[],'prompts':{'review-first':'Unused synthetic perspective','review-second':'Unused synthetic perspective'}})['id']
        cls.counter=0

    @classmethod
    def op(cls,operation,**args):return cls.broker.call(cls.token,operation,**args)

    def make_plan_inputs(self,changed_definition=False):
        type(self).counter+=1
        name='full-review-'+str(self.counter)
        idea_text='Synthetic Boolean-outcome infrastructure fixture; fixed output is not a meaning-quality claim.'
        idea=self.op('add_research',kind='idea',content={'text':idea_text},scope={},source_refs=[])['id']
        snapshot=self.f.snapshot['id'];catalog=self.f.snapshot['body']['catalog_id']
        definition=self.f.feature['body']['definitions_id']
        if changed_definition:
            # Supplied review metadata is not a new feature certificate. Keep
            # names/types/units and ancestry equal while changing declared lag.
            original=self.op('get_artifact',artifact_id=definition)
            body=deepcopy(original['body']);body['parameters']['delay_seconds']+=1
            with self.broker._transaction():
                definition=self.broker._save_artifact({
                    key:value for key,value in {**original,'body':body}.items() if key!='id'})['id']
        candidate=binding_support.resolve(deepcopy(self.f.base['candidate']),{
            'fixture:idea':idea,'fixture:data_snapshot':snapshot})
        candidate['estimand']['unit']='ratio'
        candidate['outcome']['scale']='binary_probability'
        candidate['outcome']['program']['expression']={'op':'literal','type':'boolean','unit':None,'value':True}
        candidate['parameter_origins'].append({'path':'/outcome/program/expression/value',
            'basis':'preexisting_specification','source_refs':[],'rationale':'Synthetic test input only'})
        report=deepcopy(self.f.base['semantic_report']);report['segments'][0]['text']=idea_text
        context=self.op('create_context',role='formalizer',epoch=1,artifact_ids=[idea,catalog,snapshot])['id']
        worker=self.op('register_worker',name=name,role='formalizer',capabilities=['formalization/v1'])['token']
        scripted={**self.common,'model':'fixed-plan-input/1','generation_parameters':{},'max_output_tokens':16000,
            'prompt':'Retain the fixed synthetic input without changing it.'}
        spec={'kind':'formalization/v1','context_id':context,'purpose':'Full synthetic integration',
            'allowed_workers':[name],'max_attempts':1,'lease_seconds':60,'deadline':int(time.time())+1800,
            'dependencies':[],'research_epoch_id':self.epoch,'research_call_profile':scripted,
            'research_inputs':{'idea_id':idea,'catalog_id':catalog,'definition_ids':[]}}
        job=self.op('enqueue',key=name,spec=spec)['id']
        output={'status':'final','candidate':candidate,'semantic_report':report}
        result=run_auxiliary_once(LocalClient(self.broker,worker),ScriptedProvider([output],model=scripted['model'],mode='live'))
        self.assertTrue(result['accepted'],result)
        target=self.op('get_artifact',artifact_id=result['artifact_id'])
        compiled=self.f.compile(target)
        self.assertEqual(compiled['body']['status'],'COMPILED',compiled['body'])
        execution=self.op('execute_development',compiled_id=compiled['id'])
        self.assertEqual(execution['body']['status'],'DESCRIPTIVE_EXECUTION',execution['body'])
        self.op('release_batch',batch_id=self.op('inspect',job_id=job)['batch_id'],target_epoch=2)
        context=self.op('create_context',role='formalizer',epoch=2,
            artifact_ids=[target['id'],idea,catalog,definition])['id']
        reviewer=self.op('register_worker',name=name+'-review',role='formalizer',capabilities=['semantic-review/v1'])['token']
        self.op('enqueue',key=name+'-review',spec={**spec,'kind':'semantic-review/v1','context_id':context,
            'allowed_workers':[name+'-review'],'dependencies':[job],'research_call_profile':profile(self.common),
            'research_inputs':{'formalization_id':target['id'],'definition_ids':[definition]}})
        review={'judgment':'faithful','reason':'Mocked infrastructure response, not actual model-quality evidence.',
            'added_assumptions':[],'omitted_assumptions':[],'conflicts':[],'unresolved_meaning':[],
            'mapping_checks':[{'segment':i,'judgment':'faithful','reason':'Fixed synthetic response.'}
                for i in range(mapping_count(target))]}
        with patch('trading_researcher.controller_providers._invoke',return_value=ProviderFixture.result(
                {'output':{'status':'final','review':review}})):
            result=run_auxiliary_once(LocalClient(self.broker,reviewer))
        self.assertTrue(result['accepted'],result)
        assessment=self.op('assess_meaning_review',key=name,formalization_id=target['id'])
        self.assertEqual(assessment['body']['independent_semantic_review'],'SATISFIED')
        return {'key':name,'compiled_id':compiled['id'],'meaning_review_id':assessment['id'],'primary_count':1,
            'dependence':{'base_length':4,'rationale':'Synthetic integration only; dependence adequacy remains unverified.',
                'development_refs':[execution['id']],'randomness':{'algorithm':'fixture','version':'1','seed':17}}}

    def test_exact_feature_definition_reaches_real_preparation_and_inspection(self):
        request=self.make_plan_inputs()
        plan=self.op('prepare_evaluation_plan',**request)
        current=self.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertEqual(plan['body']['status'],'POLICY_DRAFT')
        self.assertEqual(current['meaning_review']['required_definition_id'],self.f.feature['body']['definitions_id'])
        self.assertNotIn('independent_semantic_review',current['current_remaining_gates'])
        self.assertEqual(len(current['current_remaining_gates']),4)
        self.assertFalse(current['scientific_readiness'])

    def test_review_with_different_feature_parameters_cannot_supply_plan_gate(self):
        request=self.make_plan_inputs(changed_definition=True)
        with patch.object(evaluation_plans,'run_plan_child',side_effect=AssertionError('Unbound review launched')) as child:
            with self.assertRaisesRegex(Invalid,'feature-definition identity'):
                self.op('prepare_evaluation_plan',**request)
        self.assertFalse(child.called)


if __name__=='__main__':unittest.main()
