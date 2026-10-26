"""Owned synthetic artifacts for auxiliary handoff tests; no genuine model call."""
from copy import deepcopy
import time

from binding_support import BindingFixture, resolve
from test_researcher import LocalClient
from trading_researcher.codec import canonical
from trading_researcher.auxiliary import request_for


class AuxiliaryFixture:
    def __init__(self):
        self.base=BindingFixture()
        self.broker,self.token=self.base.broker,self.base.token
        self.counter=0
        for name in ('aux-first','aux-second'):
            self.op('register_worker',name=name,role='discovery',capabilities=['research-record/v1'])

    def op(self,op,**args):return self.broker.call(self.token,op,**args)
    def close(self):self.base.close()

    def case(self,mode='fixture',max_calls=12):
        self.counter+=1
        label='aux-'+str(self.counter)
        idea=self.op('add_research',kind='idea',content={'text':self.base.base['original_idea_text']},scope={},source_refs=[])
        catalog=self.base.snapshot['body']['catalog_id']
        definitions=self.base.feature['body']['definitions_id']
        refs=[idea['id'],catalog,definitions,self.base.snapshot['id']]
        discovery=self.op('create_context',role='discovery',epoch=1,artifact_ids=refs)
        profile={'model':'fixture/1','prompt_version':'aux-base-fixture/1','max_calls':max_calls,'max_tokens':80000,
            'max_seconds':1800,'max_cost_units':0 if mode=='fixture' else 1000,'currency':'NONE' if mode=='fixture' else 'TEST',
            'mode':mode,'prompts':{'aux-first':'Independent first fixture perspective','aux-second':'Independent second fixture perspective'},
            'tools':[],'generation_parameters':{},'max_output_tokens':8192,'call_timeout_seconds':20,'max_retries':1}
        epoch=self.op('create_research_epoch',key=label,context_id=discovery['id'],workers=['aux-first','aux-second'],profile=profile)['id']
        context=self.op('create_context',role='formalizer',epoch=1,artifact_ids=refs)
        name=label+'-formalizer'
        worker=self.op('register_worker',name=name,role='formalizer',capabilities=['formalization/v1'])['token']
        call_profile={'model':'fixture/1','prompt_version':'aux-formalize-fixture/1',
            'prompt':'Translate the exact supplied idea. Preserve unsupported meaning as a gap. This is a synthetic fixture.',
            'generation_parameters':{},'max_output_tokens':8192,'call_timeout_seconds':20,'max_retries':1}
        inputs={'idea_id':idea['id'],'catalog_id':catalog,'definition_ids':[definitions]}
        spec={'kind':'formalization/v1','context_id':context['id'],'purpose':'Faithful fixture formalization',
            'allowed_workers':[name],'max_attempts':2,'lease_seconds':60,'deadline':int(time.time())+1800,'dependencies':[],
            'research_epoch_id':epoch,'research_call_profile':call_profile,'research_inputs':inputs}
        job=self.op('enqueue',key=label+'-formalize',spec=spec)['id']
        candidate=resolve(deepcopy(self.base.base['candidate']),{'fixture:idea':idea['id'],'fixture:data_snapshot':self.base.snapshot['id']})
        output={'status':'final','candidate':candidate,'semantic_report':deepcopy(self.base.base['semantic_report'])}
        return {'label':label,'epoch':epoch,'idea':idea,'catalog':catalog,'definitions':definitions,
            'worker':worker,'worker_name':name,'job':job,'spec':spec,'output':output,'client':LocalClient(self.broker,worker)}

    def respond(self,case,output=None,key='fixture-call'):
        client=case['client']
        lease=client.call('claim')['lease']
        packet=client.call('auxiliary_input',lease=lease)
        request=request_for(case['spec'],packet)
        intent=client.call('reserve_research_call',lease=lease,key=key,request=request,
            input_token_bound=len(canonical(request).encode())+1024,output_token_limit=8192,cost_bound_units=0)
        reply=case['output'] if output is None else output
        receipt=client.call('finish_research_call',lease=lease,call_id=intent['call_id'],
            response={'status':'completed','provider_id':'manual-fixture','output':reply},
            usage={'input_tokens':len(canonical(request).encode()),'output_tokens':len(canonical(reply).encode()),'cost_units':0})
        return lease,intent,receipt

    def formalize(self,case,output=None):
        lease,intent,_=self.respond(case,output)
        output=case['output'] if output is None else output
        saved=case['client'].call('record_formalization',lease=lease,idea_id=case['idea']['id'],catalog_id=case['catalog'],
            candidate=output['candidate'],semantic_report=output['semantic_report'],provider_call_id=intent['call_id'])
        outcome=case['client'].call('submit',lease=lease,artifact_id=saved['id'])
        assert outcome['accepted'],outcome
        return self.op('get_artifact',artifact_id=saved['id'])

    def review(self,case,target):
        job=self.op('inspect',job_id=case['job'])
        self.op('release_batch',batch_id=job['batch_id'],target_epoch=2)
        context=self.op('create_context',role='formalizer',epoch=2,
            artifact_ids=[target['id'],case['idea']['id'],case['catalog'],case['definitions']])
        name=case['label']+'-reviewer'
        token=self.op('register_worker',name=name,role='formalizer',capabilities=['semantic-review/v1'])['token']
        profile={**case['spec']['research_call_profile'],'prompt_version':'aux-review-fixture/1',
            'prompt':'Independently compare original idea, candidate, mappings and supplied definitions. Explain differences and uncertainty. No empirical verdict.'}
        spec={**case['spec'],'kind':'semantic-review/v1','context_id':context['id'],'allowed_workers':[name],
            'purpose':'Independent meaning review transport fixture','research_call_profile':profile,
            'research_inputs':{'formalization_id':target['id'],'definition_ids':[case['definitions']]},'dependencies':[case['job']]}
        self.op('enqueue',key=case['label']+'-review',spec=spec)
        semantic=target['body']['semantic_report']
        segments=semantic.get('segments',[]) if type(semantic) is dict else []
        review={'judgment':'uncertain','reason':'Synthetic reply exercises transport only; no model judgment is established.',
            'added_assumptions':[],'omitted_assumptions':[],'conflicts':[],
            'unresolved_meaning':['Actual independent model judgment has not been demonstrated.'],
            'mapping_checks':[{'segment':i,'judgment':'uncertain','reason':'Synthetic fixture, not a substantive model review.'}
                for i in range(len(segments))]}
        return {'spec':spec,'client':LocalClient(self.broker,token),'output':{'status':'final','review':review}}
