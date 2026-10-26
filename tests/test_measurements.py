"""Development measurement semantics and fenced provider-tool authorization."""
from copy import deepcopy
import time
import unittest
from unittest.mock import patch

import test_data as data_support
from test_researcher import LocalClient, final
from trading_researcher.codec import canonical, decode, digest, Invalid
from trading_researcher.errors import Conflict, Denied
from trading_researcher.measurements import measure, validate_request
from trading_researcher.researcher import DEVELOPMENT_TOOL_DEFINITIONS, TOOL_DEFINITIONS, ScriptedProvider, run_research_once


def query(snapshot='fixture', start=data_support.START, warmup=0):
    catalog={'close@1':{'type':'real','unit':'USDT'}}
    return {'snapshot_id':snapshot,'universe':{'start':data_support.iso(start),
        'end':data_support.iso(start+2700),'instruments':['BTCUSDT']},'warmup_bars':warmup,
        'program':{'schema':'research-ast/1','catalog_hash':digest(catalog),'expression':{'op':'feature','ref':'close@1'}}}


class MeasurementTests(unittest.TestCase):
    def test_exact_values_missing_grid_and_late_sample_are_not_filled(self):
        catalog={'close@1':{'type':'real','unit':'USDT'}}
        rows=[data_support.row(value='10'),data_support.row(data_support.START+1800,value='30',
            available_at=data_support.START+2700)]
        result=measure(catalog,rows,query())
        self.assertEqual(result['status'],'MEASURED_DEVELOPMENT')
        self.assertEqual(result['summary']['defined'],1)
        self.assertEqual(result['summary']['mean'],{'numerator':'10','denominator':'1'})
        self.assertEqual(result['values'][1]['missing'],'missing_observation')
        self.assertIsNone(result['values'][2]['value'])
        self.assertFalse(result['scientific_readiness'])

    def test_warmup_is_explicit_and_does_not_enter_the_requested_summary(self):
        catalog={'close@1':{'type':'real','unit':'USDT'}}
        request=query(start=data_support.START+900,warmup=1)
        request['program']['expression']={'op':'lag','bars':1,'arg':{'op':'feature','ref':'close@1'}}
        rows=[data_support.row(data_support.START+900*i,value=str(10*(i+1))) for i in range(4)]
        result=measure(catalog,rows,request)
        self.assertEqual(result['summary']['mean'],{'numerator':'20','denominator':'1'})
        self.assertEqual([v['time'] for v in result['values']],[data_support.START+900*i for i in range(1,4)])

    def test_unbounded_requests_and_boolean_limits_are_rejected(self):
        for key,value in [('warmup_bars',True),('warmup_bars',513)]:
            with self.assertRaises(Invalid):validate_request({**query(),key:value})
        request=query();request['universe']['end']=data_support.iso(data_support.START+257*900)
        with self.assertRaises(Invalid):validate_request(request)


class MeasurementRunTests(unittest.TestCase):
    def setUp(self):
        self.fixture=data_support.DataTests();self.fixture.setUp();self.fixture.now=int(time.time())
        self.broker=self.fixture.broker;self.admin=self.fixture.admin
        self.snapshot=self.fixture.register([self.fixture.source([data_support.row(value='10'),
            data_support.row(data_support.START+900,value='20'),data_support.row(data_support.START+1800,value='30')])])
        self.clients={}
        for name in ('first','second'):
            token=self.op('register_worker',name=name,role='discovery',capabilities=['research-record/v1'])['token']
            self.clients[name]=LocalClient(self.broker,token)
        self.context=self.op('create_context',role='discovery',epoch=1,artifact_ids=[self.snapshot['id']])
        self.profile={'model':'fixture/1','prompt_version':'measurement-tests/1','max_calls':4,'max_tokens':80000,
            'max_seconds':60,'max_cost_units':0,'currency':'NONE','mode':'fixture','prompts':{'first':'Explore','second':'Explore independently'},
            'tools':DEVELOPMENT_TOOL_DEFINITIONS,'generation_parameters':{},'max_output_tokens':4096,
            'call_timeout_seconds':15,'max_retries':0}
        self.epoch=self.op('create_research_epoch',key='measure',context_id=self.context['id'],workers=['first','second'],profile=self.profile)
        self.batch=self.op('create_batch',key='measurement-batch',epoch=1)
        self.jobs=[]
        for name in self.clients:
            self.jobs.append(self.op('enqueue',key=name,spec={'kind':'research-record/v1','context_id':self.context['id'],
                'purpose':'Qualified development measurement','allowed_workers':[name],'max_attempts':2,
                'lease_seconds':30,'deadline':self.fixture.now+120,'dependencies':[],'batch_id':self.batch['id'],
                'research_epoch_id':self.epoch['id']}))
        self.op('seal_batch',batch_id=self.batch['id'])

    def tearDown(self):self.fixture.tearDown()
    def op(self,operation,**args):return self.broker.call(self.admin,operation,**args)

    def record_call(self,request=None,tool_id='measurement-1'):
        client=self.clients['first'];claimed=client.call('claim');self.lease=claimed['lease']
        self.request=query(self.snapshot['id']) if request is None else request
        self.call={'id':tool_id,'name':'measure_development','arguments':self.request}
        intent=client.call('reserve_research_call',lease=self.lease,key='measure-turn',request={
            'model':self.profile['model'],'prompt_version':self.profile['prompt_version'],
            'messages':[{'role':'system','content':'Explore'}],'tools':self.profile['tools'],'generation_parameters':{}},
            input_token_bound=10000,output_token_limit=4096,cost_bound_units=0)
        client.call('finish_research_call',lease=self.lease,call_id=intent['call_id'],response={
            'status':'completed','provider_id':'fixture','output':{'status':'tools','calls':[self.call]}},
            usage={'input_tokens':1,'output_tokens':1,'cost_units':0})
        self.args={'lease':self.lease,'call_id':intent['call_id'],'tool_id':tool_id}
        return self.args

    def test_owned_measurement_retains_source_scope_and_idempotent_result(self):
        args=self.record_call();client=self.clients['first'];saved=client.call('measure_development',**args)
        self.assertEqual(saved['body']['result']['summary']['mean'],{'numerator':'20','denominator':'1'})
        self.assertEqual(client.call('measure_development',**args),saved)
        self.assertEqual(client.call('read_artifact',lease=self.lease,artifact_id=saved['id']),saved)
        capsule=self.op('get_artifact',artifact_id=saved['body']['input_capsule_id'])
        self.assertIn('trading_researcher/measurements.py',capsule['body']['source_files'])
        self.assertIn(self.snapshot['id'],saved['exposure'])
        self.assertFalse(saved['body']['scientific_readiness'])
        self.assertEqual(saved['body']['availability']['basis'],'unknown')

    def test_unrecorded_tools_and_argument_substitution_fail_before_data_read(self):
        args=self.record_call()
        with patch.object(self.broker,'_load_reference_data',side_effect=AssertionError('premature data read')):
            with self.assertRaises(Denied):self.clients['first'].call('measure_development',**{**args,'tool_id':'invented'})
            with self.assertRaises(Invalid):self.clients['first'].call('measure_development',**args,request=self.request)
            with self.assertRaises(Denied):self.clients['second'].call('measure_development',**args)
        for schema in ('development-measurement-input/1','development-measurement/1'):
            with self.assertRaises(Invalid):self.clients['first'].call('put_artifact',lease=self.lease,body={'schema':schema},source_refs=[])

    def test_expired_lease_retains_outcome_but_does_not_deliver_it(self):
        args=self.record_call();load=self.broker._load_reference_data
        def expire(*a,**kw):
            value=load(*a,**kw);self.fixture.now+=31;return value
        with patch.object(self.broker,'_load_reference_data',side_effect=expire):
            with self.assertRaises(Denied):self.clients['first'].call('measure_development',**args)
        from trading_researcher.measurements import RESULT
        saved=self.broker._measurement_find(RESULT,args['call_id'],args['tool_id'])
        self.assertFalse(saved['body']['delivered']);self.assertEqual(saved['body']['result']['status'],'MEASURED_DEVELOPMENT')

    def test_installed_research_loop_consumes_measurement_and_retains_observation(self):
        call={'id':'measure-real-loop','name':'measure_development','arguments':query(self.snapshot['id'])}
        result=run_research_once(self.clients['first'],ScriptedProvider([
            {'status':'tools','calls':[call]},final('Hypothesis invented by a fixture; not genuine discovery')]))
        self.assertTrue(result['accepted']);self.assertFalse(result['genuine_discovery'])
        calls=self.op('inspect_research_epoch',epoch_id=self.epoch['id'])['calls']
        self.assertIn('MEASURED_DEVELOPMENT',str(calls[1]['request']))
        tool_message=next(item for item in calls[1]['request']['messages'] if item['role']=='tool')
        observed=decode(tool_message['content'])['result']['value']['body']['result']
        self.assertEqual(observed['summary']['mean'],{'numerator':'20','denominator':'1'})
        self.assertEqual(self.op('verify')['status'],'PASS')


if __name__=='__main__':unittest.main()
