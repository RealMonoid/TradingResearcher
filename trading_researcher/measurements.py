"""Qualified development measurements from retained, permitted provider tool calls."""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib

from .codec import canonical, decode, digest, integer, text, Invalid
from .data import window
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .evaluation_policy import require
from .expressions import ReferenceEngine, ExpressionGap
from .outcomes import _read_rational, _rational


INPUT='development-measurement-input/1'
RESULT='development-measurement/1'
MAX_STEPS=100000
MAX_VALUE_BYTES=256*1024
LOADED_SOURCE=footprint(source_bundle())
MEASUREMENT_TOOL={'name':'measure_development',
    'description':'Evaluate a causal expression on an authorized development snapshot. Retain missing/late values, '
        'exact descriptive summaries and source qualifications. No scientific verdict. At most256 time/instrument '
        'output cells,512 explicit warmup bars,100000 shared primitive steps; resource gaps remain visible.',
    'parameters':{'type':'object','properties':{'snapshot_id':{'type':'string'},
        'universe':{'type':'object','properties':{'start':{'type':'string'},'end':{'type':'string'},
            'instruments':{'type':'array','items':{'type':'string'}}},
            'required':['start','end','instruments'],'additionalProperties':False},
        'warmup_bars':{'type':'integer','minimum':0,'maximum':512},'program':{'type':'object'}},
        'required':['snapshot_id','universe','warmup_bars','program'],'additionalProperties':False}}


def validate_request(request):
    require(type(request) is dict and set(request)=={'snapshot_id','universe','warmup_bars','program'},
        'Exact development measurement request required')
    text(request['snapshot_id'],'snapshot id');lower,upper,instruments=window(request['universe'])
    integer(request['warmup_bars'],'warmup bars',0)
    require(request['warmup_bars']<=512 and (upper-lower)//900*len(instruments)<=256,
        'Measurement window exceeds its explicit envelope')
    require(lower>=900*request['warmup_bars'] and type(request['program']) is dict,'Invalid measurement warmup/program')
    canonical(request)
    return lower,upper,instruments


def _summary(values,complete):
    present=[row for row in values if row['missing'] is None]
    result={'scope':'requested_grid' if complete else 'completed_prefix_only','defined':len(present),
        'missing':dict(sorted(Counter(row['missing'] for row in values if row['missing']).items())),
        'mean':None,'minimum':None,'maximum':None,'true':None,'false':None}
    if not present:return result
    if present[0]['type']=='boolean':
        result.update(true=sum(row['value'] is True for row in present),false=sum(row['value'] is False for row in present))
    else:
        numbers=[_read_rational(row['value']) for row in present];total=Fraction(0)
        for value in numbers:
            total+=value
            if max(total.numerator.bit_length(),total.denominator.bit_length())>8192:
                raise ExpressionGap('RESOURCE_GAP','Descriptive sum exceeds its exact numeric envelope')
        mean=total/len(numbers)
        if max(mean.numerator.bit_length(),mean.denominator.bit_length())>8192:
            raise ExpressionGap('RESOURCE_GAP','Descriptive mean exceeds its exact numeric envelope')
        result.update(mean=_rational(mean),minimum=_rational(min(numbers)),maximum=_rational(max(numbers)))
    return result


def measure(catalog,rows,request):
    lower,upper,instruments=validate_request(request)
    expected=(upper-lower)//900*len(instruments);remaining=[MAX_STEPS];values=[];size=0
    result={'schema':'development-measurement-calculation/1','status':'MEASURED_DEVELOPMENT','reason':None,
        'expected_positions':expected,'processed_positions':0,'uncomputed_positions':expected,
        'processing_complete':False,'primitive_steps':0,'values':values,'summary':None,'description':None,
        'interrupted_position':None,'scientific_readiness':False,'classification_permitted':False,
        'limits':{'max_output_positions':256,'max_warmup_bars':512,'max_steps':MAX_STEPS,
            'value_bytes_stop':MAX_VALUE_BYTES,'byte_stop_scope':'after_one_complete_bounded_value'},
        'qualification':'Exact descriptive development calculation on supplied availability. No feature certification, '
            'population inference, scientific evidence or unseen-data claim.'}
    try:
        # Filter even direct pure callers: omitted warmup is never silently supplied.
        selected=[row for row in rows if lower-900*request['warmup_bars']<=row['time']<upper and row['instrument'] in instruments]
        engine=ReferenceEngine(catalog,selected);node=engine._program_node(request['program'])
        result['description']=engine.describe(request['program'])
        for when in range(lower,upper,900):
            for instrument in instruments:
                result['interrupted_position']={'time':when,'instrument':instrument}
                trace={'earliest_observation':None,'latest_available_at':None,'events':{}}
                def observe(observed,available,reason):
                    trace['earliest_observation']=observed if trace['earliest_observation'] is None else min(observed,trace['earliest_observation'])
                    if available is not None:
                        trace['latest_available_at']=available if trace['latest_available_at'] is None else max(available,trace['latest_available_at'])
                    trace['events'][reason]=trace['events'].get(reason,0)+1
                value=engine._calculate(node,when,instrument,when,remaining,observe).public()
                row={'time':when,'instrument':instrument,**value,'trace':trace}
                size+=len(canonical(row).encode());values.append(row)
                if size>MAX_VALUE_BYTES:raise ExpressionGap('RESOURCE_GAP','Retained value bytes exceed the output stop')
        result['processing_complete']=True;result['interrupted_position']=None
        result['summary']=_summary(values,True)
    except ExpressionGap as exc:
        result.update(status='RESOURCE_STOP' if exc.code=='RESOURCE_GAP' else 'MEASUREMENT_GAP',
            reason={'code':exc.code,'message':str(exc)},processing_complete=False)
        try:result['summary']=_summary(values,False)
        except ExpressionGap:result['summary']=None
    result.update(processed_positions=len(values),uncomputed_positions=expected-len(values),
        primitive_steps=min(MAX_STEPS,MAX_STEPS-remaining[0]))
    canonical(result)
    return result


class DevelopmentMeasurements:
    def _measurement_authorized(self,actor,lease,call_id,tool_id):
        text(call_id,'provider call id');text(tool_id,'tool id')
        job=self._owned(actor,lease)
        if actor['role']!='discovery' or job['spec']['kind']!='research-record/v1':raise Denied('Discovery measurement capability required')
        call=self._db.execute('SELECT * FROM research_calls WHERE id=?',(call_id,)).fetchone()
        if (call is None or call['owner']!=actor['name'] or call['job_id']!=job['id']
                or call['generation']!=job['generation'] or call['state']!='recorded'):
            raise Denied('Recorded provider call unavailable')
        receipt=decode(call['receipt']);epoch=self._epoch(call['epoch_id']);profile=self._effective_research_profile(job)
        if (receipt['late'] or not receipt['within_reservation'] or not receipt['accounting_valid']
                or epoch['state']!='active' or self._now()>=epoch['created_at']+epoch['request']['profile']['max_seconds']
                or canonical(MEASUREMENT_TOOL) not in [canonical(item) for item in profile['tools']]):
            raise Denied('Measurement is outside its active frozen profile')
        response=self._artifact(call['response_id'])['body']['response'];output=response.get('output')
        if response.get('status')!='completed' or type(output) is not dict or output.get('status')!='tools':
            raise Denied('No completed provider tool request')
        calls=output.get('calls')
        require(type(calls) is list and 1<=len(calls)<=16,'Bounded tool batch required')
        identifiers=[]
        for item in calls:
            require(type(item) is dict and set(item)=={'id','name','arguments'},'Exact retained tool request required')
            identifiers.append(text(item['id'],'tool id'))
        require(len(set(identifiers))==len(identifiers),'Tool identifiers must be unique')
        matched=next((item for item in calls if item['id']==tool_id),None)
        if matched is None or matched['name']!='measure_development':raise Denied('Requested measurement is absent')
        request=matched['arguments'];lower,upper,instruments=validate_request(request)
        context=self._context(job['spec']['context_id']);ancestry=self._attempt_sources(actor,job,context)
        if request['snapshot_id'] not in ancestry:raise Denied('Snapshot unavailable in the frozen context')
        snapshot=self._data_snapshot(request['snapshot_id']);manifest=snapshot['body']['manifest']
        if snapshot['data_class']!='development' or manifest['partition']!='development':raise Denied('Development partition required')
        start,end,allowed=window(manifest['universe'])
        if lower-900*request['warmup_bars']<start or upper>end or not set(instruments)<=set(allowed):
            raise Denied('Measurement and explicit warmup must stay within the authorized snapshot')
        return job,context,call,snapshot,request,ancestry

    def _measurement_find(self,schema,call_id,tool_id):
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            envelope=decode(row['envelope']);body=envelope.get('body')
            if (envelope['creator']==envelope['origin']=='controller' and type(body) is dict and body.get('schema')==schema
                    and body['call_id']==call_id and body['tool_id']==tool_id):return self._artifact(row['id'])
        return None

    def _measure_development_external(self,token,args):
        canonical(args);require(set(args)=={'lease','call_id','tool_id'},'Measurement arguments come only from the recorded call')
        with self._mutex:
            actor=self._principal(token)
            job,context,call,snapshot,request,ancestry=self._measurement_authorized(actor,**args)
            existing=self._measurement_find(RESULT,args['call_id'],args['tool_id'])
            if existing is not None:
                if existing['body']['delivered'] is not True:raise Denied('Measurement finished outside its original authority')
                return existing
            if self._measurement_find(INPUT,args['call_id'],args['tool_id']) is not None:
                raise Conflict('Prior measurement is unresolved; no automatic re-execution')
            source=source_bundle()
            if footprint(source)!=LOADED_SOURCE:raise Conflict('Measurement source changed since import; restart')
            files={name:self._stage_blob_bytes(raw) for name,raw in source.items()}
            exposure=set(context['exposure'])|ancestry|{snapshot['id'],call['response_id']}
            for identity in ancestry:exposure.update(self._artifact(identity)['exposure'])
            envelope={'version':'local-artifact/1','creator':'controller','origin':'controller','exposed_to':actor['name'],
                'job_id':job['id'],'generation':job['generation'],'context_id':context['id'],'data_class':'work_product',
                'source_refs':sorted(ancestry|{snapshot['id'],call['response_id']}),'exposure':sorted(exposure),
                'authority':'development_measurement_not_scientific_evidence'}
            with self._transaction():
                for descriptor in files.values():self._register_blob(descriptor)
                capsule=self._save_artifact({**envelope,'blob_refs':sorted({v['sha256'] for v in files.values()}),
                    'body':{'schema':INPUT,'created_at':self._now(),'call_id':args['call_id'],'tool_id':args['tool_id'],
                        'request':request,'source_files':files,'source_footprint':footprint(source),
                        'scientific_readiness':False}})
                self._event('controller','bound_computation_started',attempt_id=capsule['id'],kind='development_measurement',
                    input_ref=snapshot['id'],retained_input_id=capsule['id'])
        failure=None;loaded=None
        try:
            lower,upper,instruments=validate_request(request)
            start=datetime.fromtimestamp(lower-900*request['warmup_bars'],timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            loaded=self._load_reference_data(snapshot['id'],start,request['universe']['end'],instruments,
                max_rows=256+request['warmup_bars']*len(instruments))
            result=measure(loaded['catalog'],loaded['rows'],request)
            require(footprint(source_bundle())==LOADED_SOURCE,'Installed measurement source changed during calculation')
        except Exception as exc:
            failure={'type':type(exc).__name__}
            result={'schema':'development-measurement-calculation/1','status':'TECHNICAL_FAILURE',
                'scientific_readiness':False,'classification_permitted':False,
                'qualification':'Calculation failed; no descriptive or scientific conclusion.'}
        except BaseException:
            with self._transaction():self._event('controller','bound_computation_interrupted',
                attempt_id=capsule['id'],reason='measurement_cancelled')
            raise
        window_hash=None
        if loaded is not None:
            checksum=hashlib.sha256()
            for row in loaded['rows']:checksum.update((canonical(row)+'\n').encode())
            window_hash=checksum.hexdigest()
        with self._transaction():
            try:self._measurement_authorized(actor,**args);delivered=True
            except (Invalid,Conflict,Denied):delivered=False
            saved=self._save_artifact({**envelope,'source_refs':sorted(set(envelope['source_refs'])|{capsule['id']}),
                'exposed_to':actor['name'] if delivered else None,
                'exposure':sorted(set(envelope['exposure'])|{capsule['id']}),
                'body':{'schema':RESULT,'created_at':self._now(),'call_id':args['call_id'],'tool_id':args['tool_id'],
                    'input_capsule_id':capsule['id'],'request':request,'result':result,'failure':failure,'delivered':delivered,
                    'availability':snapshot['body']['manifest']['availability'],'remaining_gates':snapshot['body']['remaining_gates'],
                    'canonical_source_window_sha256':window_hash,
                    'scientific_readiness':False}})
            self._event('controller','bound_computation_checked',attempt_id=capsule['id'],artifact_id=saved['id'],status=result['status'])
        if not delivered:raise Denied('Measurement was retained but cannot be released outside its original authority')
        return saved
