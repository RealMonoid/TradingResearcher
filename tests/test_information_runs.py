"""Owned diagnostic computation must preserve source, input and authority bounds."""
from copy import deepcopy
import hashlib
import unittest
from unittest.mock import patch

from binding_support import BindingFixture
from trading_researcher.codec import Invalid, decode
from trading_researcher.errors import Conflict, Denied


class InformationRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=BindingFixture()
        cls.broker,cls.token=cls.fixture.broker,cls.fixture.token
        candidate=deepcopy(cls.fixture.base['candidate'])
        candidate['estimand']['unit']='ratio'
        candidate['outcome']['scale']='binary_probability'
        candidate['outcome']['program']['expression']={'op':'literal','type':'boolean','unit':None,'value':True}
        candidate['parameter_origins'].append({'path':'/outcome/program/expression/value',
            'basis':'preexisting_specification','source_refs':[],'rationale':'Synthetic diagnostic boundary fixture'})
        case={'change':{'candidate':candidate,'original_idea_text':'Synthetic binary diagnostic input.'}}
        formalization=cls.fixture.create_formalization(case)
        cls.compiled=cls.fixture.compile(formalization,case)
        cls.execution=cls.op('execute_development',compiled_id=cls.compiled['id'])
        cls.plan=cls.op('prepare_evaluation_plan',key='information-plan',compiled_id=cls.compiled['id'],primary_count=2,
            dependence={'base_length':4,'rationale':'Declared development fixture, not a fitted scientific model.',
                'development_refs':[cls.execution['id']],
                'randomness':{'algorithm':'not-used-by-diagnostics','version':'1','seed':1}})

    @classmethod
    def op(cls,op,**args):return cls.broker.call(cls.token,op,**args)
    @classmethod
    def tearDownClass(cls):cls.fixture.close()

    def args(self,key):
        return {'key':key,'plan_id':self.plan['id'],'execution_id':self.execution['id'],
            'lags':[1,2],'limits':{'max_seconds':60}}

    def test_owned_result_retains_exact_inputs_contributions_and_replay(self):
        args=self.args('complete')
        result=self.op('prepare_information_diagnostics',**args)
        body=result['body']
        self.assertEqual(body['status'],'COMPUTED_DIAGNOSTICS')
        self.assertFalse(body['scientific_readiness'])
        self.assertIsNone(body['result']['n_min'])
        self.assertIn('degenerate_scope_rate',body['result']['model_identification_gaps'])
        capsule=self.op('get_artifact',artifact_id=body['input_capsule_id'])
        self.assertEqual(capsule['body']['request'],args)
        self.assertIn(self.execution['id'],capsule['source_refs'])
        self.assertIn(self.plan['id'],result['exposure'])
        raw=self.broker._read_blob_bytes(body['contribution_blob']['sha256'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),body['result']['contributions_sha256'])
        self.assertEqual(len(raw.splitlines()),body['result']['time_rows'])
        self.assertEqual(decode(raw.splitlines()[-1])['scope_count'],0)
        self.assertIsNotNone(body['verification'])
        self.assertEqual(self.op('prepare_information_diagnostics',**args),result)
        with self.assertRaises(Conflict):
            self.op('prepare_information_diagnostics',**{**args,'lags':[1]})

    def test_worker_unowned_input_and_reserved_namespace_are_denied(self):
        worker=self.op('register_worker',name='no-information',role='discovery',capabilities=['research-record/v1'])['token']
        with self.assertRaises(Denied):self.broker.call(worker,'prepare_information_diagnostics',**self.args('worker'))
        source=self.op('add_source',body={'unowned':'execution'},data_class='development')
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('premature read')):
            with self.assertRaises(Denied):
                self.op('prepare_information_diagnostics',**{**self.args('unowned'),'execution_id':source['id']})
        for schema in ('information-diagnostics-input/1','development-information-diagnostics/1'):
            with self.subTest(schema=schema),self.assertRaises(Invalid):
                self.op('add_source',body={'schema':schema},data_class='development')

    def test_interruption_keeps_original_source_and_request(self):
        from trading_researcher import information_runs
        args=self.args('interrupted')
        with patch.object(information_runs,'run_child',side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError):self.op('prepare_information_diagnostics',**args)
        with self.assertRaises(Conflict):
            self.op('prepare_information_diagnostics',**{**args,'lags':[2]})
        with patch.object(information_runs,'source_bundle',side_effect=AssertionError('retry read checkout')):
            result=self.op('prepare_information_diagnostics',**args)
        self.assertEqual(result['body']['status'],'COMPUTED_DIAGNOSTICS')

    def test_result_tampering_fails_separate_replay_and_retains_attempt(self):
        from trading_researcher import information_runs
        real=information_runs.run_child
        def corrupt(*args,**kwargs):
            response,raw=real(*args,**kwargs)
            if kwargs.get('verify') is None:
                response['result']['totals']['scope']['successes']+=1
            return response,raw
        with patch.object(information_runs,'run_child',side_effect=corrupt):
            with self.assertRaises(Invalid):self.op('prepare_information_diagnostics',**self.args('tampered'))
        # The same immutable request remains retryable; it was not published.
        result=self.op('prepare_information_diagnostics',**self.args('tampered'))
        self.assertEqual(result['body']['status'],'COMPUTED_DIAGNOSTICS')


if __name__=='__main__':unittest.main()
