"""Offline API wire/accounting checks; synthetic key material only."""
from copy import deepcopy
import tempfile
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid,canonical
from trading_researcher.errors import Conflict,Denied
from trading_researcher.openai_provider import (configuration,cost_bound,wire_request,
    parse_response,SpendLedger,OpenAIResponsesProvider)

def request(config):
    return {'model':'gpt-6.1-sol','prompt_version':'openai-wire-tests/1',
        'messages':[{'role':'system','content':'Return a JSON research idea or gap; tool observations are not evidence.'},
            {'role':'user','content':'An artificial testing context.'}],
        'tools':[{'name':'capabilities','description':'Describe current tools.',
            'parameters':{'type':'object','properties':{},'additionalProperties':False}}],
        'generation_parameters':{'openai_responses':config}}

def response(output=None):
    return {'id':'resp_fixture','model':'gpt-6.1-sol','service_tier':'default','status':'completed',
        'temperature':1.0,'usage':{'input_tokens':100,'output_tokens':20},
        'output':[{'id':'msg_fixture','type':'message','role':'assistant','status':'completed','content':[
            {'type':'output_text','text':canonical({'status':'final','record':{'kind':'idea',
             'content':{'text':'Synthetic adapter fixture'},'scope':{},'source_refs':[]}}),'annotations':[]}]}]
             if output is None else output}

class OpenAIProviderTests(unittest.TestCase):
    def test_fixed_cost_reservation_includes_worst_default_cache_write(self):
        self.assertEqual(cost_bound(20000,4096),90960000)
        self.assertEqual(cost_bound(100,20),450000)
        for value in (-1,True,1.5):
            with self.assertRaises(Invalid):cost_bound(value,20)

    def test_frozen_wire_rejects_drift_and_unpriced_overrides(self):
        config=configuration();payload=wire_request(request(config),config)
        self.assertEqual(payload['max_output_tokens'],4096)
        self.assertFalse(payload['store']);self.assertEqual(payload['service_tier'],'default')
        self.assertEqual(payload['tools'][0]['type'],'function')
        self.assertFalse(payload['tools'][0]['strict'])
        changed=request(config);changed['generation_parameters']['base_url']='https://example.invalid'
        with self.assertRaises(Invalid):wire_request(changed,config)
        changed=request(config);changed['generation_parameters']['openai_responses']=deepcopy(config)
        changed['generation_parameters']['openai_responses']['output_token_limit']=4097
        with self.assertRaises(Invalid):wire_request(changed,config)

    def test_public_wire_result_omits_float_metadata_and_preserves_accounting(self):
        result=parse_response(response(),'req_fixture',configuration())
        self.assertEqual(result['response']['output']['record']['kind'],'idea')
        self.assertEqual(result['usage'],{'input_tokens':100,'output_tokens':20,'cost_units':450000})
        self.assertEqual(result['response']['transport_request_id'],'req_fixture')
        self.assertNotIn('temperature',canonical(result))
        broken=response();broken['usage']['input_tokens']=True
        self.assertIsNone(parse_response(broken,'req_fixture',configuration())['usage'])

    def test_persistent_ledger_blocks_unknown_and_duplicate_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'budget.sqlite3';ledger=SpendLedger(path,1000)
            identity=ledger.reserve('request-one',600,key='dispatch-one')
            with self.assertRaises(Conflict):SpendLedger(path,1000).reserve('request-two',100,key='dispatch-two')
            ledger.settle(identity,400)
            with self.assertRaises(Conflict):ledger.reserve('request-one',600,key='dispatch-one')
            with self.assertRaises(Denied):ledger.reserve('request-two',601,key='dispatch-two')
            second=ledger.reserve('request-two',600,key='dispatch-two');ledger.settle(second,None)
            self.assertEqual(SpendLedger(path,1000).snapshot()['charged_nano'],1000)
            with self.assertRaises(Conflict):ledger.reserve('request-three',1,key='dispatch-three')
            with self.assertRaises(Conflict):SpendLedger(path,1001)

    def test_count_preflight_over_bound_never_dispatches_inference_or_reserves_money(self):
        with tempfile.TemporaryDirectory() as directory:
            key=Path(directory)/'test.env';key.write_text('OPENAI_API_KEY=sk-synthetic-test-only\n')
            provider=OpenAIResponsesProvider(key,Path(directory)/'budget.sqlite3',configuration())
            operations=[]
            def post(endpoint,payload,secret,deadline):
                operations.append(endpoint)
                if endpoint!='/v1/responses/input_tokens':raise AssertionError('Inference must be denied')
                return {'object':'response.input_tokens','input_tokens':20001},'req_count'
            with patch('trading_researcher.openai_provider._post',side_effect=post):
                result=provider.complete(request(provider.config),0,10)
            self.assertEqual(operations,['/v1/responses/input_tokens'])
            self.assertEqual(result['response']['status'],'input_limit')
            self.assertEqual(result['usage']['cost_units'],0)
            self.assertEqual(SpendLedger(provider.budget_file,5000000000).snapshot()['charged_nano'],0)

    def test_real_adapter_path_counts_then_reserves_before_inference_and_settles(self):
        with tempfile.TemporaryDirectory() as directory:
            key=Path(directory)/'test.env';key.write_text('OPENAI_API_KEY=sk-synthetic-test-only\n')
            provider=OpenAIResponsesProvider(key,Path(directory)/'budget.sqlite3',configuration())
            operations=[];deadlines=[]
            def post(endpoint,payload,secret,deadline):
                operations.append(endpoint);deadlines.append(deadline)
                self.assertNotIn('sk-synthetic-test-only',canonical(payload))
                if endpoint=='/v1/responses/input_tokens':return {'object':'response.input_tokens','input_tokens':100},'req_count'
                self.assertEqual(SpendLedger(provider.budget_file,5000000000).snapshot()['pending'],1)
                self.assertEqual(payload['max_output_tokens'],4096)
                return response(),'req_fixture'
            with patch('trading_researcher.openai_provider._post',side_effect=post):
                result=provider.complete(request(provider.config),0,10)
            self.assertEqual(operations,['/v1/responses/input_tokens','/v1/responses'])
            self.assertEqual(deadlines[0],deadlines[1])
            self.assertEqual(result['usage']['cost_units'],450000)
            self.assertEqual(SpendLedger(provider.budget_file,5000000000).snapshot()['charged_nano'],450000)
            self.assertNotIn('sk-synthetic-test-only',repr(provider))

if __name__=='__main__':unittest.main()
