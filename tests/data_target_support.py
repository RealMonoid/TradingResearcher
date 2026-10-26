"""Actual owned development and protected synthetic data for target-boundary tests."""
from copy import deepcopy
import time

from binding_support import BindingFixture, resolve
from test_binance_quality import row
from trading_researcher.auxiliary import request_for, run_auxiliary_once
from trading_researcher.researcher import ScriptedProvider
from test_researcher import LocalClient


UNIVERSE={'start':'2024-01-01T00:15:00Z','end':'2024-01-01T01:00:00Z','instruments':['BTCUSDT']}


class Fixture:
    def __init__(self,private_versions=3):
        self.base=BindingFixture()
        try:self._setup(private_versions)
        except BaseException:self.base.close();raise

    def _setup(self,private_versions):
        assert private_versions in (1,3)
        self.broker=self.base.broker;self.token=self.base.token;self.root=self.base.root
        self.target=self.op('declare_data_target',key='target',partition='assessment',universe=UNIVERSE,
            development_feature_certificate_id=self.base.feature['id'])
        self.common={'model':'target-fixture/1','prompt_version':'target-fixture/1','generation_parameters':{},
            'max_output_tokens':16000,'call_timeout_seconds':30,'max_retries':0}
        for name in ('unused-one','unused-two'):
            self.op('register_worker',name=name,role='discovery',capabilities=['research/v1'])
        discovery=self.op('create_context',role='discovery',epoch=1,artifact_ids=[self.target['id']])
        self.epoch=self.op('create_research_epoch',key='targets',context_id=discovery['id'],
            workers=['unused-one','unused-two'],profile={**self.common,'mode':'live','currency':'USD',
                'max_calls':12,'max_tokens':80000,'max_seconds':1800,'max_cost_units':5000000000,'tools':[],
                'prompts':{'unused-one':'Synthetic context','unused-two':'Synthetic context'}})['id']
        self.versions=[]
        opened=1704067200000
        raw=b''.join(row(opened+900000*n) for n in range(3))
        alternative=row(opened,price='11')+row(opened+1800000,price='11')
        for index,(values,delay) in enumerate(((raw,self.base.base['delay_seconds']),
                (alternative,self.base.base['delay_seconds']),(raw,self.base.base['delay_seconds']+1))[:private_versions]):
            normalizer=self.base.normalizer
            source=normalizer.source(values,month='2024-01')
            normalized=normalizer.run_normalize([source],start=UNIVERSE['start'],end=UNIVERSE['end'],partition='assessment',delay=delay)
            self.broker=self.base.broker=normalizer.broker
            certificate=self.op('certify_features',data_snapshot_id=normalized['snapshot']['id'])
            assert certificate['body']['status']=='CERTIFIED',certificate['body']
            self.versions.append({'snapshot':normalized['snapshot'],'certificate':certificate})
        self.counter=0

    def op(self,operation,**args):return self.broker.call(self.token,operation,**args)

    def close(self):self.base.close()

    def bind(self,index=0,key='bind'):
        version=self.versions[index]
        return self.op('bind_data_target',key=key,target_id=self.target['id'],
            data_snapshot_id=version['snapshot']['id'],feature_certificate_id=version['certificate']['id'])

    def formalize(self,universe_override=None):
        self.counter+=1;name='target-formalizer-'+str(self.counter)
        idea_text='Synthetic declared-target infrastructure fixture; not a discovered market hypothesis.'
        idea=self.op('add_research',kind='idea',content={'text':idea_text},scope={},source_refs=[])['id']
        catalog=self.target['body']['catalog_id'];definition=self.target['body']['definitions_id']
        context=self.op('create_context',role='formalizer',epoch=1,artifact_ids=[idea,catalog,definition,self.target['id']])
        candidate=resolve(deepcopy(self.base.base['candidate']),{'fixture:idea':idea,'fixture:data_snapshot':self.target['id']})
        candidate['test_universe'].update(deepcopy(UNIVERSE))
        if universe_override:candidate['test_universe'].update(universe_override)
        report=deepcopy(self.base.base['semantic_report']);report['segments'][0]['text']=idea_text
        worker=self.op('register_worker',name=name,role='formalizer',capabilities=['formalization/v1'])['token']
        spec={'kind':'formalization/v1','context_id':context['id'],'purpose':'Synthetic protected target formalization',
            'allowed_workers':[name],'max_attempts':1,'lease_seconds':300,'deadline':int(time.time())+3600,
            'dependencies':[],'research_epoch_id':self.epoch,'research_call_profile':{**self.common,'prompt':'Preserve the synthetic input.'},
            'research_inputs':{'idea_id':idea,'catalog_id':catalog,'definition_ids':[definition]}}
        job=self.op('enqueue',key=name,spec=spec)['id']
        packet=self.broker._auxiliary_packet_for_spec(spec)
        output={'status':'final','candidate':candidate,'semantic_report':report}
        client=LocalClient(self.broker,worker)
        result=run_auxiliary_once(client,ScriptedProvider([output],model=self.common['model'],mode='live'))
        assert result['accepted'],result
        formalization=self.op('get_artifact',artifact_id=result['artifact_id'])
        assert formalization['body']['assessment']['status']=='STRUCTURE_CHECKED',formalization['body']['assessment']
        return {'formalization':formalization,'job':job,'spec':spec,'packet':packet,'worker':worker,
            'provider_request':request_for(spec,packet)}

    def compile(self,case,private,index=0,**overrides):
        return self.op('compile_hypothesis',formalization_id=case['formalization']['id'],
            feature_certificate_id=self.versions[index]['certificate']['id'],reference_certificate_id=self.base.reference['id'],
            as_of='2024-01-02T00:00:00Z',max_steps=10000,data_target_binding_id=private['id'],**overrides)

    def review_packet(self,case):
        target=case['formalization'];catalog=target['body']['catalog_id'];definition=self.target['body']['definitions_id']
        self.op('release_batch',batch_id=self.op('inspect',job_id=case['job'])['batch_id'],target_epoch=2)
        context=self.op('create_context',role='formalizer',epoch=2,
            artifact_ids=[target['id'],target['body']['idea_id'],catalog,definition,self.target['id']])
        spec={**case['spec'],'kind':'semantic-review/v1','context_id':context['id'],'allowed_workers':['independent-reviewer'],
            'research_inputs':{'formalization_id':target['id'],'definition_ids':[definition]},'dependencies':[case['job']]}
        packet=self.broker._auxiliary_packet_for_spec(spec)
        return spec,packet
