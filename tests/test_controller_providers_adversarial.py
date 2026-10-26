"""Independent local dispatch-boundary probes, with no real provider traffic."""
from copy import deepcopy
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch

import controller_provider_support as support
from trading_researcher import controller_providers as host
from trading_researcher import openai_provider as openai
from trading_researcher.auxiliary import request_for, run_auxiliary_once
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied


class SimulatedHostCrash(BaseException):
    pass


class ControllerProvidersAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.f=support.Fixture();self.addCleanup(self.f.close)

    def case(self,**changes):
        previous=getattr(self,'previous_case',None)
        if previous is not None and self.f.broker._job(previous['job'])['state']=='running':
            previous['client'].call('block',lease=previous['lease'],reason='Independent test branch ended',
                needs=['separate test branch'],retry_when='This fixture does not resume prior model work')
        case=self.f.case(**changes)
        case['lease']=case['client'].call('claim')['lease']
        self.previous_case=case
        return case

    def invoke(self,case,key='host',**extra):
        return case['client'].call('invoke_auxiliary_provider',lease=case['lease'],key=key,**extra)

    def record(self,case,call_id):
        inputs=case['spec']['research_inputs']
        return case['client'].call('record_formalization',lease=case['lease'],
            idea_id=inputs['idea_id'],catalog_id=inputs['catalog_id'],candidate=None,
            semantic_report=None,provider_call_id=call_id)

    def test_concurrent_same_key_is_one_dispatch_and_other_key_stays_reserved(self):
        case=self.case();entered=threading.Event();release=threading.Event();results=[];errors=[]
        def dispatch(*args):
            self.assertFalse(self.f.broker._db.in_transaction)
            entered.set()
            if not release.wait(5):raise RuntimeError('test dispatch was not released')
            return self.f.result(case)
        def work():
            try:results.append(self.invoke(case))
            except BaseException as exc:errors.append(exc)
        with patch.object(host,'_invoke',side_effect=dispatch) as invoke:
            thread=threading.Thread(target=work);thread.start()
            try:
                self.assertTrue(entered.wait(5))
                pending=self.invoke(case)
                self.assertEqual(pending['state'],'unresolved')
                self.assertNotIn('response',pending)
                case['client'].call('heartbeat',lease=case['lease'])
                with self.assertRaises(Denied):self.invoke(case,key='second-key')
            finally:release.set();thread.join(5)
            self.assertFalse(thread.is_alive());self.assertEqual(errors,[])
            self.assertEqual(self.invoke(case),results[0])
            self.assertEqual(invoke.call_count,1)
        state=self.f.op('inspect_research_epoch',epoch_id=case['epoch'])
        self.assertEqual(state['usage'],{'calls':1,'tokens':200,'cost_units':1})

    def test_pending_crash_survives_restart_without_dispatch_or_budget_reset(self):
        case=self.case()
        with patch.object(host,'_invoke',side_effect=SimulatedHostCrash):
            with self.assertRaises(SimulatedHostCrash):self.invoke(case)
        before=self.f.op('inspect_research_epoch',epoch_id=case['epoch'])
        self.assertEqual(before['usage'],{'calls':1,'tokens':21024,'cost_units':60240000})
        self.f.broker.close()
        self.f.broker=Broker(self.f.root/'registry',provider_routes=self.f.route)
        case['client'].broker=self.f.broker
        with patch.object(host,'_invoke') as invoke:
            result=self.invoke(case)
            self.assertEqual(result['state'],'unresolved')
            with self.assertRaises(Denied):self.invoke(case,key='after-restart')
            with self.assertRaises(Denied):
                case['client'].call('finish_research_call',lease=case['lease'],
                    call_id=result['call_id'],**self.f.result(case))
            invoke.assert_not_called()
        self.assertEqual(self.f.op('inspect_research_epoch',epoch_id=case['epoch'])['usage'],before['usage'])

    def test_worker_completion_and_private_rpc_forgery_cannot_settle_host_call(self):
        case=self.case()
        with patch.object(host,'_invoke',side_effect=SimulatedHostCrash):
            with self.assertRaises(SimulatedHostCrash):self.invoke(case)
        pending=self.invoke(case);args={'lease':case['lease'],'call_id':pending['call_id'],**self.f.result(case)}
        for op,extra in [('finish_research_call',{}),('finish_research_call',{'internal':True}),
                ('finish_research_call',{'host_owned':True}),('settle_research_call',{}),('_settle_research_call',{})]:
            with self.subTest(op=op,extra=extra),self.assertRaises((Denied,Invalid)):
                case['client'].call(op,**args,**extra)
        self.assertEqual(self.invoke(case)['state'],'unresolved')
        self.assertEqual(self.f.broker._db.execute('SELECT result_id FROM provider_invocations').fetchone()[0],None)

    def test_prior_worker_call_key_never_acquires_host_provenance(self):
        for completed in (False,True):
            case=self.case();packet=case['client'].call('auxiliary_input',lease=case['lease'])
            request=request_for(case['spec'],packet)
            adapter=openai.OpenAIResponsesProvider('unused','unused',self.f.config)
            intent=case['client'].call('reserve_research_call',lease=case['lease'],key='old',request=request,
                **adapter.reservation(request,1024))
            if completed:
                case['client'].call('finish_research_call',lease=case['lease'],call_id=intent['call_id'],**self.f.result(case))
            with self.subTest(completed=completed),patch.object(host,'_invoke') as invoke:
                with self.assertRaises(Denied):self.invoke(case,key='old')
                invoke.assert_not_called()
            self.assertIsNone(self.f.broker._db.execute('SELECT * FROM provider_invocations WHERE call_id=?',
                (intent['call_id'],)).fetchone())

    def test_route_is_detached_and_credentials_paths_never_enter_provenance(self):
        case=self.case();original=deepcopy(self.f.config)
        self.f.route[self.f.model]['key_file']='mutated-local-key-path'
        self.f.route[self.f.model]['config']['reasoning_effort']='max'
        self.f.route[self.f.model]['config']['pricing']['sources'].append('mutated-source')
        with patch.object(host,'_invoke',return_value=self.f.result(case)) as invoke:
            result=self.invoke(case)
        adapter,request,ordinal=invoke.call_args.args[:3]
        self.assertIs(type(adapter),openai.OpenAIResponsesProvider)
        self.assertEqual(adapter.config,original)
        self.assertEqual(adapter.run_id,'controller-'+result['receipt']['call_id'])
        self.assertEqual((adapter.epoch_id,adapter.worker,ordinal),(case['epoch'],case['spec']['allowed_workers'][0],0))
        output=self.f.op('get_artifact',artifact_id=result['invocation_id'])
        retained=self.f.op('get_artifact',artifact_id=output['body']['input_id'])
        self.assertEqual(retained['body']['configuration'],original)
        self.assertEqual(retained['body']['request_sha256'],digest(request))
        self.assertEqual(retained['body']['units_per_usd'],1000000000)
        for artifact in (retained,output):
            raw=canonical(artifact)
            for secret in ('key_file','budget_file',str(self.f.root),'mutated-local-key-path'):
                self.assertNotIn(secret,raw)
            self.assertFalse(artifact['body']['scientific_readiness'])
            self.assertEqual((artifact['creator'],artifact['origin']),('controller','controller'))
        self.assertFalse((self.f.root/'unused-key').exists())
        self.assertFalse((self.f.root/'unused-ledger').exists())

    def test_exact_route_configuration_mismatch_never_dispatches(self):
        changed=deepcopy(self.f.config);changed['reasoning_effort']='high'
        case=self.case(generation_parameters={'openai_responses':changed})
        with patch.object(host,'_invoke') as invoke:
            with self.assertRaises(Invalid):self.invoke(case)
            invoke.assert_not_called()
        self.assertEqual(self.f.op('inspect_research_epoch',epoch_id=case['epoch'])['usage']['calls'],0)

    def test_boolean_alias_cannot_match_frozen_integer_configuration(self):
        self.f.config['input_token_limit']=1
        self.f.broker.close()
        self.f.broker=Broker(self.f.root/'registry',provider_routes=self.f.route)
        changed=deepcopy(self.f.config);changed['input_token_limit']=True
        case=self.case(generation_parameters={'openai_responses':changed})
        reply=self.f.result(case);reply['usage']['input_tokens']=1
        with patch.object(host,'_invoke',return_value=reply) as invoke:
            with self.assertRaises(Invalid):self.invoke(case)
            invoke.assert_not_called()

    def test_currency_mode_missing_route_and_budget_denials_precede_dispatch(self):
        for changes in ({'currency':'TEST'},{'mode':'fixture'},
                {'max_tokens':20000},{'max_cost_units':1}):
            case=self.case(**changes)
            with self.subTest(changes=changes),patch.object(host,'_invoke') as invoke:
                with self.assertRaises(Denied):self.invoke(case)
                invoke.assert_not_called()
            self.assertEqual(self.f.op('inspect_research_epoch',epoch_id=case['epoch'])['usage']['calls'],0)
        case=self.case()
        self.f.broker.close();self.f.broker=Broker(self.f.root/'registry')
        case['client'].broker=self.f.broker
        with patch.object(host,'_invoke') as invoke:
            with self.assertRaises(Denied):self.invoke(case)
            invoke.assert_not_called()

    def test_route_and_rpc_cannot_select_arbitrary_adapter_or_backend(self):
        for value in ({'alias':self.f.route[self.f.model]},
                {self.f.model:{**self.f.route[self.f.model],'provider':'scripted'}},
                {self.f.model:{**self.f.route[self.f.model],'adapter':object()}}):
            with self.subTest(value=str(value)[:80]),self.assertRaises(Invalid):host.routes(value)
        case=self.case()
        with patch.object(host,'_invoke') as invoke:
            for extra in ({'provider':'openai'},{'response':{}},{'usage':None},{'request':{}},{'config':self.f.config}):
                with self.subTest(extra=next(iter(extra))),self.assertRaises(Invalid):self.invoke(case,**extra)
            invoke.assert_not_called()

    def test_provenance_schema_and_worker_identity_cannot_be_forged(self):
        case=self.case();other=self.f.case()
        for schema in ('provider-invocation/1','provider-invocation-input/1','provider-invocation/999'):
            with self.subTest(schema=schema):
                with self.assertRaises(Invalid):
                    self.f.op('add_source',body={'schema':schema},data_class='development')
                with self.assertRaises(Invalid):
                    case['client'].call('put_artifact',lease=case['lease'],body={'schema':schema},source_refs=[])
        with patch.object(host,'_invoke') as invoke:
            with self.assertRaises(Denied):
                other['client'].call('invoke_auxiliary_provider',lease=case['lease'],key='spoof')
            with self.assertRaises(Denied):
                self.f.op('invoke_auxiliary_provider',lease=case['lease'],key='operator-spoof')
            invoke.assert_not_called()

    def test_source_drift_is_retained_but_unusable_on_return_lookup_and_formalization(self):
        case=self.case()
        with patch.object(host,'source_hashes',side_effect=[{'source':'a'*64},{'source':'b'*64}]),\
                patch.object(host,'_invoke',return_value=self.f.result(case)) as invoke:
            result=self.invoke(case)
        self.assertEqual(result['state'],'unusable');self.assertNotIn('response',result)
        self.assertEqual(self.invoke(case),result);self.assertEqual(invoke.call_count,1)
        retained=self.f.op('get_artifact',artifact_id=result['invocation_id'])
        self.assertFalse(retained['body']['installed_sources_unchanged'])
        self.assertFalse(retained['body']['response_usable'])
        with self.assertRaises((Invalid,Denied)):self.record(case,result['receipt']['call_id'])

    def test_lost_lease_cancellation_is_observed_and_late_reply_never_accepted(self):
        case=self.case();seen=[]
        def dispatch(adapter,request,ordinal,seconds,cancelled):
            self.assertFalse(cancelled())
            case['client'].call('block',lease=case['lease'],reason='synthetic cancellation',
                needs=['retained audit'],retry_when='Do not automatically repeat dispatch')
            seen.append(cancelled())
            return self.f.result(case)
        with patch.object(host,'_invoke',side_effect=dispatch):result=self.invoke(case)
        self.assertEqual(seen,[True]);self.assertEqual(result['state'],'unusable')
        self.assertNotIn('response',result);self.assertTrue(result['receipt']['late'])
        with self.assertRaises(Denied):self.invoke(case)
        with self.assertRaises((Denied,Invalid)):self.record(case,result['receipt']['call_id'])

    def test_unknown_usage_and_overruns_cannot_supply_formalization(self):
        for usage in (None,{'input_tokens':20001,'output_tokens':0,'cost_units':1},
                {'input_tokens':0,'output_tokens':1025,'cost_units':1},
                {'input_tokens':0,'output_tokens':0,'cost_units':60240001}):
            case=self.case();reply={**self.f.result(case),'usage':usage}
            with self.subTest(usage=usage),patch.object(host,'_invoke',return_value=reply):
                result=self.invoke(case)
            self.assertEqual(result['state'],'unusable');self.assertNotIn('response',result)
            with self.assertRaises((Invalid,Denied)):self.record(case,result['receipt']['call_id'])
            state=self.f.op('inspect_research_epoch',epoch_id=case['epoch'])
            self.assertEqual(state['state'],'active' if usage is None else 'halted')

    def test_runner_cancellation_watch_blocks_long_lease_and_keeps_review_unverified(self):
        case=self.f.case();cancel=threading.Event();observed=[]
        def dispatch(adapter,request,ordinal,seconds,cancelled):
            cancel.set();deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                if cancelled():observed.append(True);break
                time.sleep(0.02)
            return {'response':{'status':'cancelled'},'usage':None}
        with patch.object(host,'_invoke',side_effect=dispatch):
            result=run_auxiliary_once(case['client'],cancel=cancel)
        self.assertEqual(observed,[True]);self.assertFalse(result['accepted'])
        self.assertEqual(result['actual_independent_model_review'],'UNVERIFIED')
        self.assertFalse(result['scientific_authority'])


if __name__=='__main__':unittest.main()
