"""Budget-bound formalization and review transport; no semantic/scientific certificate."""
from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Denied
from .formalization import validate_inputs


KINDS={'formalization/v1','semantic-review/v1'}
PROFILE_FIELDS={'model','prompt_version','prompt','generation_parameters','max_output_tokens',
                'call_timeout_seconds','max_retries'}
REVIEW_SCHEMA='semantic-review-record/1'
JUDGMENTS={'faithful','different','uncertain'}


def require(value,message):
    if not value:raise Invalid(message)


def validate_profile(profile,epoch):
    require(type(profile) is dict and set(profile)==PROFILE_FIELDS,'Auxiliary profile has missing or unexpected fields')
    for name in ('model','prompt_version','prompt'):text(profile[name],name)
    require(type(profile['generation_parameters']) is dict,'Explicit generation parameters required')
    integer(profile['max_output_tokens'],'max_output_tokens',1)
    integer(profile['call_timeout_seconds'],'call_timeout_seconds',1)
    integer(profile['max_retries'],'max_retries')
    require(profile['max_output_tokens']<=epoch['max_tokens']
        and profile['call_timeout_seconds']<=epoch['max_seconds']
        and profile['max_retries']<=epoch['max_retries'],'Auxiliary settings exceed the original epoch limits')


def request_for(spec,packet):
    profile=spec['research_call_profile']
    return {'model':profile['model'],'prompt_version':profile['prompt_version'],
        'generation_parameters':profile['generation_parameters'],'tools':[],
        'messages':[{'role':'system','content':profile['prompt']},{'role':'user','content':canonical(packet)}]}


def check_definition_origins(definitions,catalog_id,snapshot_id=None):
    for artifact in definitions:
        origins=strings(artifact['body'].get('input_refs'),'definition input references')
        require(catalog_id in origins,'Definition provenance does not bind the selected catalog')
        if type(snapshot_id) is str:
            require(snapshot_id in origins,'Definition provenance does not bind the represented data snapshot')


def validate_judgment(review,segments):
    require(type(review) is dict and set(review)=={'judgment','reason','added_assumptions','omitted_assumptions',
        'conflicts','unresolved_meaning','mapping_checks'},'Incomplete independent review report')
    require(type(review['judgment']) is str and review['judgment'] in JUDGMENTS,'Unknown review judgment')
    text(review['reason'],'independent review reason')
    for name in ('added_assumptions','omitted_assumptions','conflicts','unresolved_meaning'):
        strings(review[name],name)
    checks=review['mapping_checks']
    require(type(checks) is list and len(checks)==segments,'Every original mapping segment needs a review')
    seen=set()
    for check in checks:
        require(type(check) is dict and set(check)=={'segment','judgment','reason'},'Invalid mapping review')
        integer(check['segment'],'mapping segment')
        require(check['segment']<segments and check['segment'] not in seen
            and type(check['judgment']) is str and check['judgment'] in JUDGMENTS,
            'Duplicate, missing or invalid mapping judgment')
        seen.add(check['segment'])
        text(check['reason'],'mapping review reason')
    if review['judgment']=='faithful':
        require(not any(review[n] for n in ('added_assumptions','omitted_assumptions','conflicts','unresolved_meaning'))
            and all(c['judgment']=='faithful' for c in checks),'Faithful judgment conflicts with its stated unresolved differences')


def mapping_count(target):
    report=target['body']['semantic_report']
    segments=report.get('segments',[]) if type(report) is dict else []
    return len(segments) if type(segments) is list else 0


def validate_review_record(record,sources):
    require(type(record) is dict and record.get('schema')==REVIEW_SCHEMA,'Expected an owned review record')
    require(record.get('scientific_readiness') is False and record.get('actual_independent_model_review')=='UNVERIFIED',
        'Review transport cannot certify actual independent model judgment')
    lookup={s['id']:s for s in sources}
    require(record.get('formalization_id') in lookup,'Review target is absent from retained ancestry')
    target=lookup[record['formalization_id']]
    require(target['creator']!=record.get('reviewer_id') and target['creator']==record.get('formalizer_id'),
        'Formalizer cannot supply its own independent review')
    validate_judgment(record['review'],mapping_count(target))


class AuxiliaryResearch:
    def _auxiliary_packet_for_spec(self,spec):
        require(spec['kind'] in KINDS and 'research_epoch_id' in spec,'An auxiliary job needs its original epoch')
        context=self._context(spec['context_id'])
        require(context['role']=='formalizer' and len(spec['allowed_workers'])==1,'Auxiliary work needs one scoped formalizer capability')
        inputs=spec.get('research_inputs')
        expected={'idea_id','catalog_id','definition_ids'} if spec['kind']=='formalization/v1' else {'formalization_id','definition_ids'}
        require(type(inputs) is dict and set(inputs)==expected,'Missing or unexpected typed auxiliary inputs')
        definitions=strings(inputs['definition_ids'],'definition_ids')
        require(len(definitions)<=16,'At most sixteen definition records may be supplied')
        identities=set(definitions)|{text(inputs[n],'auxiliary input identity') for n in expected-{'definition_ids'}}
        if not identities<=set(context['artifact_ids']):raise Denied('Auxiliary input is outside its frozen context')
        retained=[self._artifact(identity) for identity in definitions]
        defined={}
        for artifact in retained:
            body=artifact['body']
            require(artifact['creator']=='controller' and artifact['data_class']=='development'
                and type(body) is dict and body.get('schema')=='feature-definitions/1'
                and type(body.get('definitions')) is list,'Owned development feature definitions required')
            for definition in body['definitions']:
                ref=definition['feature_ref']
                require(ref not in defined,'Ambiguous duplicate feature definition')
                defined[ref]=definition
        if spec['kind']=='formalization/v1':
            idea,catalog=(self._artifact(inputs[n]) for n in ('idea_id','catalog_id'))
            validate_inputs(idea['body'],catalog['body'])
            check_definition_origins(retained,catalog['id'])
            return {'schema':'formalization-input/1','context_id':context['id'],'inputs':inputs,
                'sources':[self._artifact(n) for n in context['artifact_ids']]}
        target=self._artifact(inputs['formalization_id'])
        body=target['body']
        require(target['origin']=='worker' and type(body) is dict and body.get('schema')=='formalization-record/1',
            'Review target must be a retained formalization')
        job=self._job(target['job_id'])
        require(job['state']=='completed' and job['result_id']==target['id'] and job['spec']['kind']=='formalization/v1',
            'Review target must be the accepted completed formalization result')
        if 'research_epoch_id' in job['spec']:
            require(spec['research_epoch_id']==job['spec']['research_epoch_id'],
                'Review must use the formalization original epoch; a new epoch cannot reset its budget')
        if spec['allowed_workers'][0]==target['creator']:raise Denied('Formalizer cannot independently review its own artifact')
        allowed={target['id'],body['idea_id'],body['catalog_id'],*definitions}
        catalog=self._artifact(body['catalog_id'])
        candidate=body['candidate']
        universe=candidate.get('test_universe',{}) if type(candidate) is dict else {}
        snapshot_id=universe.get('data_snapshot_ref') if type(universe) is dict else None
        public_target=None
        # Retained DATA_GAP drafts may contain arbitrary untrusted references.
        # Such text cannot become an existence/schema oracle outside the original
        # authorization snapshot merely because a reviewer inspects the draft.
        if (type(snapshot_id) is str and snapshot_id in target['source_refs']
                and snapshot_id in body['authorization_snapshot']
                and self._declared_definition_origins(retained,catalog['id'],snapshot_id)):
            public_target=self._public_data_target(snapshot_id)
            allowed.add(snapshot_id)
            if snapshot_id not in context['artifact_ids']:raise Denied('Review requires the original public data-target declaration')
        if not set(context['artifact_ids'])<=allowed:raise Denied('Review context contains unrelated material')
        if body['catalog_id'] not in context['artifact_ids']:raise Denied('Review catalog is outside the frozen context')
        if public_target is None:
            check_definition_origins(retained,catalog['id'],snapshot_id)
        required_refs=candidate.get('feature_refs',[]) if type(candidate) is dict else []
        strings(required_refs,'candidate feature references')
        require(set(required_refs)<=set(defined),'Review requires explicit meanings for every referenced feature')
        for ref in required_refs:
            require(canonical({n:defined[ref][n] for n in ('type','unit')})==canonical(catalog['body']['features'][ref]),
                'Review definitions differ from the retained catalog')
        return {'schema':'semantic-review-input/1','context_id':context['id'],'inputs':inputs,
            'formalization':target,'catalog':catalog,'definitions':retained,
            **({'data_target':public_target} if public_target is not None else {}),
            'qualification':'Assess meaning independently; supplied mappings are formalizer assertions. No assessment outcomes are supplied.'}

    def _auxiliary_input(self,actor,lease):
        job=self._owned(actor,lease)
        if actor['role']!='formalizer' or 'research_call_profile' not in job['spec']:
            raise Denied('No auxiliary input capability for this job')
        packet=self._auxiliary_packet_for_spec(job['spec'])
        self._event(actor['name'],'auxiliary_input_read',job_id=job['id'],generation=job['generation'],packet_hash=digest(packet))
        return packet

    def _auxiliary_response(self,actor,job,call_id):
        self._research_completion_check(job)
        call=self._db.execute('SELECT * FROM research_calls WHERE id=?',(text(call_id,'provider_call_id'),)).fetchone()
        if (call is None or call['owner']!=actor['name'] or call['job_id']!=job['id']
                or call['generation']!=job['generation'] or call['epoch_id']!=job['spec']['research_epoch_id']
                or call['state']!='recorded'):
            raise Denied('A completed call from this exact auxiliary attempt is required')
        receipt=decode(call['receipt'])
        require(receipt['late'] is False and receipt['within_reservation'] is True and receipt['accounting_valid'] is True,
            'Late or invalid provider response cannot supply an auxiliary result')
        invocation=self._db.execute('SELECT result_id FROM provider_invocations WHERE call_id=?',(call_id,)).fetchone()
        if invocation is not None:
            require(invocation['result_id'] is not None
                and self._artifact(invocation['result_id'])['body'].get('response_usable') is True,
                'Controller invocation is unresolved or unusable')
        packet=self._auxiliary_packet_for_spec(job['spec'])
        request=self._artifact(call['request_id'])['body']['request']
        require(canonical(request)==canonical(request_for(job['spec'],packet)),'Provider request does not bind the exact auxiliary input')
        response=self._artifact(call['response_id'])['body']['response']
        require(response.get('status')=='completed' and type(response.get('output')) is dict
            and response['output'].get('status')=='final','A final completed public provider response is required')
        return dict(call),packet,response['output']

    def _semantic_body(self,actor,job,call_id,created_at):
        if actor['role']!='formalizer' or job['spec']['kind']!='semantic-review/v1':
            raise Denied('Independent review requires its own scoped job')
        call,packet,output=self._auxiliary_response(actor,job,call_id)
        require(set(output)=={'status','review'},'Unexpected semantic review output fields')
        target=packet['formalization']
        validate_judgment(output['review'],mapping_count(target))
        profile=self._effective_research_profile(job)
        return {'schema':REVIEW_SCHEMA,'created_at':created_at,'formalization_id':target['id'],
            'idea_id':target['body']['idea_id'],'formalizer_id':target['creator'],'reviewer_id':actor['name'],
            'input_hash':digest(packet),'call_id':call_id,'request_id':call['request_id'],'response_id':call['response_id'],
            'model':profile['model'],'prompt_version':profile['prompt_version'],'provider_mode':profile['mode'],
            'review':output['review'],'role_separation_checked':True,
            'actual_independent_model_review':'UNVERIFIED','scientific_readiness':False,
            'qualification':'Host verifies inputs, role separation and recorded transport. Provider labels and structural checks do not prove actual independent model judgment.'}

    def _record_semantic_review(self,actor,lease,call_id):
        job=self._owned(actor,lease)
        body=self._semantic_body(actor,job,call_id,self._now())
        context=self._context(job['spec']['context_id'])
        saved=self._worker_artifact(actor,job,context,body,[body['formalization_id'],body['request_id'],body['response_id']])
        self._event(actor['name'],'semantic_review_recorded',job_id=job['id'],generation=job['generation'],
            artifact_id=saved['id'],call_id=call_id,judgment=body['review']['judgment'],scientific_readiness=False)
        return saved


def run_auxiliary_once(client,provider=None,cancel=None):
    """Run one exact-input auxiliary task through a trusted installed adapter.

    A recorded reply never verifies actual independent model judgment merely
    because its mode/provider labels say live. That provenance gate stays open.
    """
    import threading
    import time
    from .researcher import _invoke, ERRORS
    claimed=client.call('claim')
    if claimed is None:return None
    lease,spec=claimed['lease'],claimed['spec']
    cancel=cancel or threading.Event()
    stopped,lost=threading.Event(),threading.Event()
    transcripts=[]

    def cancelled():return cancel.is_set() or lost.is_set()

    def blocked(reason):
        try:
            result=client.call('block',lease=lease,reason=reason,needs=['auxiliary research continuation'],
                retry_when='Resolve the recorded cause within the original epoch and task budgets')
        except ERRORS:
            result={'state':'reconciliation_required'}
        return {**result,'accepted':False,'transcript_ids':transcripts,'scientific_authority':False,
            'actual_independent_model_review':'UNVERIFIED'}

    def heartbeat():
        interval=max(0.05,spec['lease_seconds']/3)
        next_heartbeat=time.monotonic()+interval
        while not stopped.wait(min(0.1,interval)):
            try:
                if provider is None and cancel.is_set():
                    client.call('block',lease=lease,reason='Auxiliary attempt cancelled',
                        needs=['auxiliary research continuation'],retry_when='Inspect retained dispatch before continuation')
                    lost.set()
                    return
                if time.monotonic()<next_heartbeat:continue
                client.call('heartbeat',lease=lease)
                next_heartbeat=time.monotonic()+interval
            except Exception:
                lost.set()
                return

    thread=threading.Thread(target=heartbeat,daemon=True)
    thread.start()
    try:
        state=client.call('research_call_state',lease=lease)
        profile=state['profile']
        if (spec['kind'] not in KINDS or 'research_call_profile' not in spec or state['calls']
                or (provider is not None and (provider.mode!=profile['mode'] or provider.model!=profile['model']))
                or profile['tools']!=[]):
            return blocked('Adapter, task or existing transcript does not match an unused auxiliary attempt')
        packet=client.call('auxiliary_input',lease=lease)
        request=request_for(spec,packet)
        for ordinal in range(profile['max_retries']+1):
            if cancelled():return blocked('Auxiliary attempt cancelled')
            if provider is None:
                from .server import Client
                transport=(Client(client.url,client.token,max(client.timeout,profile['call_timeout_seconds']+10))
                    if isinstance(client,Client) else client)
                dispatched=transport.call('invoke_auxiliary_provider',lease=lease,key='auxiliary-'+str(ordinal))
                if dispatched['state']!='recorded':return blocked('Controller dispatch is unresolved or unusable; inspect its retained record')
                receipt=dispatched['receipt']
                response={n:dispatched[n] for n in ('response','usage')}
                intent={'call_id':receipt['call_id']}
            else:
                try:
                    bounds=provider.reservation(request,profile['max_output_tokens'])
                    require(type(bounds) is dict and set(bounds)=={'input_token_bound','output_token_limit','cost_bound_units'},
                        'Malformed adapter reservation')
                    require(all(type(v) is int and v>=0 for v in bounds.values()),'Invalid adapter bounds')
                except Exception as exc:
                    return blocked('Adapter reservation failed: '+type(exc).__name__)
                intent=client.call('reserve_research_call',lease=lease,key='auxiliary-'+str(ordinal),request=request,**bounds)
                if not intent['dispatch']:return blocked('An existing provider dispatch requires reconciliation')
                response=_invoke(provider,request,ordinal,intent['deadline']-time.time(),cancelled)
                receipt=client.call('finish_research_call',lease=lease,call_id=intent['call_id'],**response)
            transcripts.append(receipt['response_id'])
            if receipt['late'] or lost.is_set():return blocked('Auxiliary response missed its frozen dispatch or epoch deadline')
            if not receipt['within_reservation']:return blocked('Provider accounting halted the original epoch')
            if cancelled():return blocked('Auxiliary attempt cancelled')
            reply=response['response']
            if reply.get('status') in ('failed','timeout') and ordinal<profile['max_retries']:continue
            output=reply.get('output')
            if reply.get('status')!='completed' or type(output) is not dict or output.get('status')!='final':
                return blocked('Provider ended without a final auxiliary result; its public response is retained')
            if spec['kind']=='formalization/v1':
                require(set(output)=={'status','candidate','semantic_report'},'Malformed formalization response')
                inputs=spec['research_inputs']
                saved=client.call('record_formalization',lease=lease,idea_id=inputs['idea_id'],catalog_id=inputs['catalog_id'],
                    candidate=output['candidate'],semantic_report=output['semantic_report'],provider_call_id=intent['call_id'])
            else:
                saved=client.call('record_semantic_review',lease=lease,call_id=intent['call_id'])
            result=client.call('submit',lease=lease,artifact_id=saved['id'])
            return {**result,'transcript_ids':transcripts,'provider_mode':profile['mode'],
                'actual_independent_model_review':'UNVERIFIED','scientific_authority':False}
        return blocked('Auxiliary transport retry allowance exhausted')
    except ERRORS as exc:
        return blocked('Controller stopped auxiliary work: '+str(exc)[:240])
    finally:
        stopped.set()
        thread.join(client.timeout+1)
