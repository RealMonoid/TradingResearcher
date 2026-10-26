"""Owned development bootstrap binding, input retention and replay."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from binding_support import BindingFixture
from trading_researcher.codec import Invalid
from trading_researcher.errors import Conflict, Denied
from trading_researcher.stationary_bootstrap import randomness


class BootstrapRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=BindingFixture()
        cls.broker,cls.token=cls.fixture.broker,cls.fixture.token
        candidate=deepcopy(cls.fixture.base['candidate'])
        candidate['estimand']['unit']='ratio'
        candidate['outcome']['scale']='binary_probability'
        candidate['outcome']['program']['expression']={'op':'literal','type':'boolean','unit':None,'value':True}
        candidate['parameter_origins'].append({'path':'/outcome/program/expression/value',
            'basis':'preexisting_specification','source_refs':[],'rationale':'Synthetic bootstrap integration fixture'})
        case={'change':{'candidate':candidate,'original_idea_text':'Synthetic Boolean computation; no market claim.'}}
        formalization=cls.fixture.create_formalization(case)
        cls.compiled=cls.fixture.compile(formalization,case)
        cls.execution=cls.op('execute_development',compiled_id=cls.compiled['id'])
        cls.plan=cls.op('prepare_evaluation_plan',key='bootstrap-plan',compiled_id=cls.compiled['id'],primary_count=2,
            dependence={'base_length':4,'rationale':'Synthetic fixture profile, not scientific adequacy.',
                        'development_refs':[cls.execution['id']],'randomness':randomness(713)})

    @classmethod
    def op(cls,op,**args):return cls.broker.call(cls.token,op,**args)
    @classmethod
    def tearDownClass(cls):cls.fixture.close()

    def args(self,key):
        return {'key':key,'plan_id':self.plan['id'],'execution_id':self.execution['id'],
                'limits':{'max_seconds':180,'max_segments':2000000}}

    def test_owned_run_retains_input_draws_and_separate_replay(self):
        args=self.args('complete')
        result=self.op('run_development_bootstrap',**args)
        body=result['body']
        self.assertIn(body['status'],('COMPUTED_UNCALIBRATED','INFORMATION_GAP'))
        self.assertFalse(body['scientific_readiness'])
        self.assertIsNotNone(body['verification'])
        self.assertEqual([c['attempted'] for c in body['result']['cases']],[19999]*3)
        capsule=self.op('get_artifact',artifact_id=body['input_capsule_id'])
        self.assertEqual(capsule['body']['request'],args)
        self.assertIn(self.execution['id'],capsule['source_refs'])
        self.assertIn(body['draw_blob']['sha256'],result['blob_refs'])
        self.assertEqual(self.op('run_development_bootstrap',**args),result)
        with self.assertRaises(Conflict):
            self.op('run_development_bootstrap',**{**args,'limits':{'max_seconds':179,'max_segments':2000000}})

    def test_unowned_inputs_and_worker_are_denied_before_blob_load(self):
        worker=self.op('register_worker',name='no-bootstrap',role='discovery',capabilities=['research-record/v1'])['token']
        with self.assertRaises(Denied):self.broker.call(worker,'run_development_bootstrap',**self.args('worker'))
        source=self.op('add_source',body={'unowned':'plan'},data_class='development')
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('premature blob read')):
            with self.assertRaises(Denied):self.op('run_development_bootstrap',**{**self.args('unowned'),'plan_id':source['id']})
        for schema in ('bootstrap-input/1','development-bootstrap/1'):
            with self.subTest(schema=schema),self.assertRaises(Invalid):
                self.op('add_source',body={'schema':schema},data_class='development')

    def test_interrupted_key_keeps_original_request_and_source(self):
        from trading_researcher import bootstrap_runs
        args=self.args('interrupted')
        with patch.object(bootstrap_runs,'run_child',side_effect=RuntimeError('synthetic interruption')):
            with self.assertRaises(RuntimeError):self.op('run_development_bootstrap',**args)
        with self.assertRaises(Conflict):
            self.op('run_development_bootstrap',**{**args,'limits':{'max_seconds':179,'max_segments':2000000}})
        with patch.object(bootstrap_runs,'source_bundle',side_effect=AssertionError('retry consulted checkout')):
            result=self.op('run_development_bootstrap',**args)
        self.assertIsNotNone(result['body']['input_capsule_id'])

    def test_explicit_mc_policy_is_bound_before_run_and_replayed(self):
        from trading_researcher.outcomes import _rational
        from fractions import Fraction
        from trading_researcher import bootstrap_runs
        args={**self.args('mc-bound'),'mc_policy':{'schema':'mc-boundary-policy/1',
                                                  'noncoverage':_rational(Fraction(1,100))}}
        with patch.object(bootstrap_runs,'run_child',side_effect=RuntimeError('synthetic interruption')):
            with self.assertRaises(RuntimeError):self.op('run_development_bootstrap',**args)
        with self.assertRaises(Conflict):
            self.op('run_development_bootstrap',**{**args,'mc_policy':{'schema':'mc-boundary-policy/1',
                'noncoverage':_rational(Fraction(1,20))}})
        result=self.op('run_development_bootstrap',**args)
        capsule=self.op('get_artifact',artifact_id=result['body']['input_capsule_id'])
        policy=capsule['body']['payload']['design']['mc_policy']
        criterion=self.plan['body']['plan']['effect_criterion']
        self.assertEqual(policy,{**args['mc_policy'],'delta':criterion['delta'],'direction':criterion['direction']})
        self.assertEqual(result['body']['result']['monte_carlo']['config'],policy)
        self.assertIsNotNone(result['body']['verification'])
        self.assertFalse(result['body']['scientific_readiness'])

    def test_mc_policy_cannot_replace_plan_effect(self):
        from trading_researcher.outcomes import _rational
        from fractions import Fraction
        args={**self.args('mc-effect'),'mc_policy':{'schema':'mc-boundary-policy/1',
                'noncoverage':_rational(Fraction(1,100)),'delta':_rational(Fraction(1,1000))}}
        with self.assertRaises(Invalid):self.op('run_development_bootstrap',**args)


if __name__=='__main__':unittest.main()
