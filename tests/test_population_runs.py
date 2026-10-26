"""Exercise population worlds through owned plans and retained source replay."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import unittest
from unittest.mock import patch

from binding_support import BindingFixture
from trading_researcher.codec import Invalid, decode
from trading_researcher.errors import Conflict, Denied
from trading_researcher.population_models import specification


class PopulationRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=BindingFixture()
        cls.broker,cls.token=cls.fixture.broker,cls.fixture.token
        candidate=deepcopy(cls.fixture.base['candidate'])
        candidate['estimand']['unit']='ratio'
        candidate['outcome']['scale']='binary_probability'
        candidate['outcome']['program']['expression']={'op':'gt',
            'left':{'op':'feature','ref':'BTCUSDT.close@binance-spot-15m-v1'},
            'right':{'op':'literal','type':'real','unit':'USDT/BTC','value':'102'}}
        candidate['parameter_origins'].append({'path':'/outcome/program/expression/right/value',
            'basis':'preexisting_specification','source_refs':[],'rationale':'Fixed population integration fixture'})
        case={'change':{'candidate':candidate,'original_idea_text':'Synthetic binary population input.'}}
        formalization=cls.fixture.create_formalization(case)
        compiled=cls.fixture.compile(formalization,case)
        cls.execution=cls.op('execute_development',compiled_id=compiled['id'])
        cls.plan=cls.op('prepare_evaluation_plan',key='population-plan',compiled_id=compiled['id'],primary_count=2,
            dependence={'base_length':4,'rationale':'Declared fixture; not a fitted model.',
                'development_refs':[cls.execution['id']],
                'randomness':{'algorithm':'not-used-by-population','version':'1','seed':1}})
        cls.diagnostics=cls.op('prepare_information_diagnostics',key='population-diagnostics',
            plan_id=cls.plan['id'],execution_id=cls.execution['id'],lags=[1,2],limits={'max_seconds':60})

    @classmethod
    def op(cls,op,**args):return cls.broker.call(cls.token,op,**args)
    @classmethod
    def tearDownClass(cls):cls.fixture.close()

    def args(self,key):
        return {'key':key,'plan_id':self.plan['id'],'execution_id':self.execution['id'],
            'diagnostics_id':self.diagnostics['id'],'specification':specification(2,Fraction(1,2),0,'Fixed stress scenario'),
            'scenario':2,'time_rows':20,'seed':101,'limits':{'max_seconds':60}}

    def test_owned_world_binds_plan_truth_input_source_and_replay(self):
        args=self.args('owned')
        result=self.op('run_population_world',**args)
        body=result['body']
        self.assertEqual(body['status'],'GENERATED_UNCALIBRATED')
        self.assertFalse(body['scientific_readiness'])
        self.assertEqual(body['result']['world']['truth']['effect'],{'numerator':'1','denominator':'10'})
        self.assertIsNone(body['result']['n_min'])
        capsule=self.op('get_artifact',artifact_id=body['input_capsule_id'])
        self.assertEqual(capsule['body']['request'],args)
        self.assertIn(self.diagnostics['id'],capsule['source_refs'])
        self.assertIn(self.plan['id'],result['exposure'])
        raw=self.broker._read_blob_bytes(body['world_blob']['sha256'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(),body['world_blob']['sha256'])
        self.assertEqual(len(raw.splitlines()),20)
        self.assertEqual(decode(raw.splitlines()[-1])['status'],'PARTITION_BOUNDARY')
        self.assertEqual(self.op('run_population_world',**args),result)
        with self.assertRaises(Conflict):self.op('run_population_world',**{**args,'seed':102})

    def test_only_operator_and_owned_matching_diagnostics_are_admitted(self):
        worker=self.op('register_worker',name='no-worlds',role='discovery',capabilities=['research-record/v1'])['token']
        with self.assertRaises(Denied):self.broker.call(worker,'run_population_world',**self.args('worker'))
        source=self.op('add_source',body={'unowned':'diagnostics'},data_class='development')
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('premature read')):
            with self.assertRaises(Denied):
                self.op('run_population_world',**{**self.args('unowned'),'diagnostics_id':source['id']})
        for schema in ('population-world-input/1','development-population-world/1'):
            with self.subTest(schema=schema),self.assertRaises(Invalid):
                self.op('add_source',body={'schema':schema},data_class='development')
        with self.assertRaises(Invalid):self.op('run_population_world',**{**self.args('bad-scenario'),'scenario':3})

    def test_interruption_retains_original_recipe_and_replays_original_source(self):
        from trading_researcher import population_runs
        args=self.args('interrupted')
        with patch.object(population_runs,'run_child',side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError):self.op('run_population_world',**args)
        with self.assertRaises(Conflict):self.op('run_population_world',**{**args,'time_rows':21})
        with patch.object(population_runs,'source_bundle',side_effect=AssertionError('retry used new source')):
            result=self.op('run_population_world',**args)
        self.assertEqual(result['body']['status'],'GENERATED_UNCALIBRATED')

    def test_forged_world_bytes_are_denied_by_separate_replay(self):
        from trading_researcher import population_runs
        real=population_runs.run_child
        def corrupt(*args,**kwargs):
            response,raw=real(*args,**kwargs)
            if kwargs.get('verify') is None:
                raw=raw.replace(b'"numerator":"1"',b'"numerator":"0"',1)
                response['world_blob']={'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}
            return response,raw
        with patch.object(population_runs,'run_child',side_effect=corrupt):
            with self.assertRaises(Invalid):self.op('run_population_world',**self.args('tampered'))


if __name__=='__main__':unittest.main()
