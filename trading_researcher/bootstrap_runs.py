"""Owned exploratory bootstrap runs; no assessment access or scientific admission."""
import hashlib
import io
from pathlib import Path
import re
import sys
import tempfile
import time
import uuid

from .binding import environment, require, write_file
from .binance_normalize import _run_child
from .certification import _environment_current, _runtime_identity
from .codec import canonical, decode, digest, text, integer
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .stationary_bootstrap import calculate, _configuration, _numerics, SAMPLER, NUMERICS
from .monte_carlo import diagnose, unassessed, validate_config
from .evaluation_policy import MAX_RESAMPLES, basic_interval, enclosing_interval
from .outcomes import _read_rational
from .storage import _hash_file


INPUT='bootstrap-input/1'
RESULT='development-bootstrap/1'
AUTHORITY='exploratory_bootstrap_not_scientific_admission'
LOADED_SOURCE=footprint(source_bundle())
BOOTSTRAP=('import sys;sys.path.insert(0,sys.argv[1]);'
           'from trading_researcher.bootstrap_runs import child_entry;child_entry(sys.argv[2])')


def validate_result(result,payload,draws,descriptive):
    """Check every returned envelope/stream, including an unreplayed stopped prefix."""
    fields={'schema','sampler','design','limits','numerics','case_report_hash','case_stream_sha256',
            'required_lengths','marginal_noncoverage','descriptive','time_rows','cases','interval','status','reason',
            'scientific_readiness','classification_permitted','remaining_gates'}
    mc_policy=payload['design'].get('mc_policy')
    if mc_policy is not None:fields.add('monte_carlo')
    require(type(result) is dict and set(result)==fields,'Incomplete or unexpected bootstrap result fields')
    # Canonical comparison excludes Python's Boolean/integer equality shortcuts.
    canonical(result)
    lengths,alpha=_configuration(payload['design'],payload['limits'],payload['report']['request']['horizon_bars'])
    size=payload['report']['processed_case_count']//len(payload['report']['request']['universe']['instruments'])
    expected={'schema':'joint-bootstrap-computation/2' if mc_policy is not None else 'joint-bootstrap-computation/1',
              'sampler':SAMPLER,'design':payload['design'],
              'limits':payload['limits'],'numerics':_numerics(payload['design']),'case_report_hash':digest(payload['report']),
              'case_stream_sha256':payload['case_blob']['sha256'],'required_lengths':lengths,
              'marginal_noncoverage':alpha,'descriptive':descriptive,'time_rows':size,
              'scientific_readiness':False,'classification_permitted':False,
              'remaining_gates':['calibration','assumption_and_information_assessment','monte_carlo_boundary_stability',
                                 'owned_scientific_inputs','atomic_allocation_and_freeze']}
    require(digest({key:result[key] for key in expected})==digest(expected),'Bootstrap result input/design identity differs')
    status=result['status']
    require(type(status) is str and status in ('COMPUTED_UNCALIBRATED','INFORMATION_GAP','INPUT_GAP','RESOURCE_STOP'),
            'Unexpected bootstrap completion state')
    require(descriptive['status']=='DESCRIPTIVE_ONLY' or status=='INPUT_GAP',
            'Unusable reference inputs must retain their original input gap')
    text(result['reason'],'bootstrap reason')
    cases=result['cases']
    require(type(cases) is list and len(cases)<=len(lengths),'Unexpected sensitivity cases')
    require(type(draws) is bytes and len(draws)<=256*1024*1024,'Unexpected draw stream envelope')
    stream=io.BytesIO(draws)
    segments=0; retained=0; undefined=0
    mc_values={}
    case_fields={'length','derived_seed','attempted','defined','undefined','interrupted','interval',
                 'replicate_sha256','interrupted_draw'}
    draw_fields={'schema','length','index','value','scope_count','condition_count','segments','path_sha256'}
    def hash_value(value):return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None
    for offset,current in enumerate(cases):
        require(type(current) is dict and set(current)==case_fields,'Malformed bootstrap sensitivity result')
        for field in ('length','attempted','defined','undefined','interrupted'):integer(current[field],field,0)
        require(current['length']==lengths[offset] and current['attempted']<=MAX_RESAMPLES
                and current['interrupted']<=1 and current['attempted']==current['defined']+current['undefined']+current['interrupted'],
                'Bootstrap draw counters or sensitivity order differ')
        seed=int(hashlib.sha256(canonical({'sampler':SAMPLER,'seed':payload['design']['randomness']['seed'],
                                          'length':current['length']}).encode()).hexdigest(),16)
        require(current['derived_seed']==str(seed),'Bootstrap derived seed differs')
        digest_stream=hashlib.sha256(); values=[]; count_undefined=0
        for ordinal in range(current['defined']+current['undefined']):
            line=stream.readline(1048577)
            require(line.endswith(b'\n') and len(line)<=1048576,'Missing or oversized bootstrap draw')
            draw=decode(line)
            require(type(draw) is dict and set(draw)==draw_fields and line==(canonical(draw)+'\n').encode(),
                    'Malformed or noncanonical bootstrap draw')
            require(draw['schema']=='joint-bootstrap-draw/1','Unsupported draw schema')
            for field in ('length','index','scope_count','condition_count','segments'):integer(draw[field],field,0)
            require(draw['length']==current['length'] and draw['index']==ordinal
                    and 0<=draw['condition_count']<=draw['scope_count']<=size*len(payload['report']['request']['universe']['instruments'])
                    and 1<=draw['segments']<=size and hash_value(draw['path_sha256']),
                    'Draw ordinal, counts or path identity differ')
            if draw['value'] is None:
                require(draw['scope_count']==0 or draw['condition_count']==0,'Undefined draw has defined denominators')
                count_undefined+=1
            else:
                _read_rational(draw['value'])
                require(draw['scope_count']>0 and draw['condition_count']>0,'Defined draw lacks denominator')
                values.append(draw['value'])
            segments+=draw['segments']; retained+=1; digest_stream.update(line)
        require(count_undefined==current['undefined'] and len(values)==current['defined']
                and current['replicate_sha256']==digest_stream.hexdigest(),'Draw stream counts or digest differ')
        undefined+=count_undefined
        if mc_policy is not None:mc_values[current['length']]=values
        if current['interrupted']:
            partial=current['interrupted_draw']
            require(status=='RESOURCE_STOP' and offset==len(cases)-1 and type(partial) is dict
                    and set(partial)=={'index','sampled_times','segments','path_sha256'},'Malformed interrupted draw')
            for field in ('index','sampled_times','segments'):integer(partial[field],field,0)
            require(partial['index']==current['defined']+current['undefined']
                    and 0<=partial['segments']<=partial['sampled_times']<=size and hash_value(partial['path_sha256']),
                    'Interrupted draw counters differ')
            segments+=partial['segments']
        else:require(current['interrupted_draw'] is None,'Unexpected interrupted draw detail')
        complete=current['attempted']==MAX_RESAMPLES and current['interrupted']==0
        if offset<len(cases)-1:require(complete,'A later sensitivity cannot follow an incomplete one')
        if current['interval'] is not None:
            require(complete and count_undefined==0,'An incomplete or undefined case cannot construct an interval')
            require(digest(current['interval'])==digest(basic_interval(descriptive['effect'],values,alpha)),
                    'Interval differs from its retained draws')
        elif status not in ('RESOURCE_STOP','INPUT_GAP'):
            require(count_undefined>0,'A complete defined sensitivity must retain its interval')
    require(stream.read(1)==b'' and segments<=payload['limits']['max_segments'],'Unexpected draw suffix or segment overrun')
    if status in ('COMPUTED_UNCALIBRATED','INFORMATION_GAP'):
        require(len(cases)==len(lengths) and all(c['attempted']==MAX_RESAMPLES and c['interrupted']==0 for c in cases),
                'Incomplete required sensitivity family')
        interval=enclosing_interval([c['interval'] for c in cases])
        require(digest(result['interval'])==digest(interval),'Combined interval differs')
        require((status=='COMPUTED_UNCALIBRATED' and interval is not None and result['reason']=='prespecified_draws_completed')
                or (status=='INFORMATION_GAP' and interval is None and undefined>0 and result['reason']=='undefined_resampled_mean'),
                'Completion state and interval construction disagree')
    else:
        require(result['interval'] is None,'Incomplete bootstrap cannot present a combined interval')
        if status=='INPUT_GAP':
            require(cases==[] and descriptive['status']!='DESCRIPTIVE_ONLY' and result['reason']==descriptive['reason'],
                    'Input gap does not match the retained descriptive calculation')
        else:
            require(result['reason'] in ('caller_cancelled','computation_time_limit','computation_segment_limit',
                    'exact_arithmetic_exceeds_numeric_envelope','interval_numeric_envelope','monte_carlo_numeric_envelope'),
                    'Unrecognized resource stop')
            if result['reason']=='computation_segment_limit':
                require(segments==payload['limits']['max_segments'],'Segment-limit reason contradicts retained work')
    if mc_policy is not None:
        diagnostic=(diagnose(descriptive['effect'],mc_values,alpha,mc_policy) if status=='COMPUTED_UNCALIBRATED'
                    else unassessed(mc_policy,'bootstrap_not_complete_and_defined'))
        require(digest(result['monte_carlo'])==digest(diagnostic),'Monte Carlo diagnostic differs from retained draws and policy')
    return {'schema':'bootstrap-stream-validation/1','retained_draws':retained,'sampled_segments':segments,
            'bound_input_and_counts_checked':True,'partial_numeric_replay_performed':False,
            'qualification':'Schema, input identity, counters, stream ordinals/hashes and interval arithmetic checked; stopped paths and draw values are not numerically replayed.'}


def child_entry(request_path):
    directory=Path(request_path).parent
    request=decode(Path(request_path).read_bytes())
    expected=request['footprint']
    require(footprint(source_bundle())==expected,'Retained bootstrap source differs')
    observed_environment=environment(expected)
    payload=request['payload']
    identity,size,_=_hash_file(directory/'cases.jsonl')
    require({'sha256':identity,'size':size}==payload['case_blob'],'Bootstrap cases differ')
    cases=[]
    with (directory/'cases.jsonl').open('rb') as stream:
        while line:=stream.readline(1048577):
            require(len(line)<=1048576 and len(cases)<100000,'Bootstrap case envelope exceeded')
            cases.append(decode(line))
    report={**payload['report'],'cases':cases}
    verify=request['verify']
    path=directory/('expected-draws.jsonl' if verify is not None else 'draws.jsonl')
    checksum=hashlib.sha256(); total=0
    with path.open('rb' if verify is not None else 'xb') as stream:
        def retain(record):
            nonlocal total
            raw=(canonical(record)+'\n').encode()
            total+=len(raw)
            require(total<=256*1024*1024,'Bootstrap draw stream exceeds the retained envelope')
            checksum.update(raw)
            if verify is None:stream.write(raw)
            else:require(stream.read(len(raw))==raw,'Bootstrap draw differs from retained replay')
        result=calculate(report,payload['design'],payload['limits'],on_draw=retain)
        if verify is not None:
            require(stream.read(1)==b'','Unexpected draw suffix')
            require(digest(result)==verify,'Bootstrap result differs from exact replay')
    draws={'sha256':checksum.hexdigest(),'size':total}
    require(footprint(source_bundle())==expected,'Bootstrap source changed during computation')
    output={'result':result if verify is None else {'verified_result_hash':verify},'draw_blob':draws,
            'request_hash':digest(request),'footprint':expected,'environment':observed_environment}
    print(canonical(output),flush=True)


def run_child(source,payload,cases,timeout,verify=None,draws=None):
    expected=footprint(source)
    request={'payload':payload,'footprint':expected,'verify':verify}
    with tempfile.TemporaryDirectory(prefix='trf-bootstrap-') as temporary:
        directory=Path(temporary)
        for name,raw in source.items():
            path=directory/name; path.parent.mkdir(parents=True,exist_ok=True); write_file(path,raw)
        write_file(directory/'cases.jsonl',cases)
        write_file(directory/'request.json',canonical(request).encode())
        if verify is not None:write_file(directory/'expected-draws.jsonl',draws)
        report=_run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],
                          directory,timeout=timeout)
        require(type(report) is dict and set(report)=={'result','draw_blob','request_hash','footprint','environment'},
                'Malformed bootstrap response')
        require(report['request_hash']==digest(request) and report['footprint']==expected
                and _environment_current(report['environment']),'Bootstrap response identity differs')
        raw=(directory/('draws.jsonl' if verify is None else 'expected-draws.jsonl')).read_bytes()
        require({'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}==report['draw_blob'],
                'Bootstrap draw stream differs')
        require(footprint({name:(directory/name).read_bytes() for name in source})==expected,'Bootstrap source changed')
        return report,raw


class BootstrapRuns:
    def _find_bootstrap(self,schema,request):
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            value=decode(row['envelope']); body=value.get('body')
            if (value['creator']==value['origin']=='controller' and type(body) is dict
                    and body.get('schema')==schema and body['request']['key']==request['key']):
                if digest(body['request'])!=digest(request):raise Conflict('Bootstrap key already binds its retained inputs')
                return self._artifact(row['id'])
        return None

    def _development_plan_execution(self,actor,plan_id,execution_id):
        """Shared ownership boundary; deterministic diagnostics need no sampler."""
        plan=self._artifact(plan_id); execution=self._artifact(execution_id)
        for value,schema,status in ((plan,'evaluation-plan/1','POLICY_DRAFT'),
                                   (execution,'reference-execution/1','DESCRIPTIVE_EXECUTION')):
            body=value.get('body')
            if not (value['creator']==value['origin']=='controller' and value['data_class']=='development'
                    and type(body) is dict and body.get('schema')==schema and body.get('status')==status):
                raise Denied('Computation requires owned development plan and execution records')
        p,e=plan['body'],execution['body']
        snapshot=self._data_snapshot(e['data_snapshot_id'])
        if snapshot['data_class']!='development' or snapshot['body']['manifest']['partition']!='development':
            raise Denied('Protected outcomes require a separately frozen scientific plan and allocation')
        require(e['compiled_id']==p['request']['compiled_id']
                and execution['id'] in p['request']['dependence']['development_refs'],
                'Development execution must be a declared diagnostic of this exact plan')
        self._require_usable_dependencies(plan_id)
        self._require_usable_dependencies(execution_id)
        self._plan_inputs(actor,p['request'])
        result=e['result']; descriptor=result['case_blob']
        require(execution['blob_refs']==[descriptor['sha256']], 'Execution case binding differs')
        require(result['report']['processing_complete'] is True,'Incomplete reference computation')
        refs=sorted({plan['id'],execution['id'],*plan['source_refs'],*execution['source_refs']})
        exposure=sorted(set(refs)|set(plan['exposure'])|set(execution['exposure']))
        return plan,execution,refs,exposure

    def _bootstrap_inputs(self,actor,request):
        plan,execution,refs,exposure=self._development_plan_execution(actor,request['plan_id'],request['execution_id'])
        p,e=plan['body'],execution['body'];result=e['result'];descriptor=result['case_blob']
        design={'base_length':p['request']['dependence']['base_length'],'primary_count':p['request']['primary_count'],
                'randomness':p['request']['dependence']['randomness']}
        if 'mc_policy' in request:
            policy=request['mc_policy']
            require(type(policy) is dict and set(policy)=={'schema','noncoverage'},
                    'Monte Carlo request cannot replace the owned plan effect or direction')
            criterion=p['plan']['effect_criterion']
            design['mc_policy']=validate_config({**policy,'delta':criterion['delta'],'direction':criterion['direction']})
        _configuration(design,request['limits'],result['report']['request']['horizon_bars'])
        payload={'report':result['report'],'case_blob':descriptor,'design':design,'limits':request['limits']}
        return payload,refs,exposure

    def _load_bootstrap_source(self,capsule):
        body=capsule['body']
        require(capsule['creator']==capsule['origin']=='controller' and capsule['data_class']=='development'
                and body.get('schema')==INPUT,'Unowned bootstrap input')
        require(body['request_hash']==digest(body['request']) and body['payload_hash']==digest(body['payload']),
                'Bootstrap input digest differs')
        require(body['runtime_identity']==_runtime_identity() and
                body['bootstrap_sha256']==hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),'Bootstrap runtime differs')
        files=body['source_files']
        require(type(files) is dict and 1<=len(files)<=128
                and all(re.fullmatch(r'trading_researcher/[A-Za-z_][A-Za-z0-9_]*\.py',n) for n in files),
                'Invalid bootstrap source paths')
        require({'trading_researcher/__init__.py','trading_researcher/bootstrap_runs.py',
                 'trading_researcher/stationary_bootstrap.py'}<=set(files),'Incomplete bootstrap source')
        require(all(type(v) is dict and set(v)=={'sha256','size'} and type(v['size']) is int
                    and 0<=v['size']<=16*1024*1024 for v in files.values())
                and sum(v['size'] for v in files.values())<=16*1024*1024,'Invalid bootstrap source envelope')
        require(set(capsule['blob_refs'])=={v['sha256'] for v in files.values()}|{body['payload']['case_blob']['sha256']},
                'Bootstrap retained blob references differ')
        source={n:self._read_blob_bytes(v['sha256']) for n,v in files.items()}
        require(all(len(source[n])==v['size'] for n,v in files.items()) and footprint(source)==body['source_footprint'],
                'Retained bootstrap source differs')
        return source

    def _run_development_bootstrap_external(self,token,args):
        with self._mutex:
            actor=self._binding_owner(token)
            fields={'key','plan_id','execution_id','limits'}
            require(set(args) in (fields,fields|{'mc_policy'}),'Exact bootstrap request required')
            request=decode(canonical(args))
            for key in ('key','plan_id','execution_id'):text(request[key],key)
            existing=self._find_bootstrap(RESULT,request)
            if existing is not None:return existing
            capsule=self._find_bootstrap(INPUT,request)
            payload,refs,exposure=self._bootstrap_inputs(actor,request)
            descriptive=self._artifact(request['execution_id'])['body']['result']['contrast']
            fresh=capsule is None
            if fresh:
                source=source_bundle()
                if footprint(source)!=LOADED_SOURCE:raise Conflict('Bootstrap code changed since import; restart')
            else:
                require(digest([payload,refs,exposure])==digest([capsule['body']['payload'],capsule['source_refs'],capsule['exposure']]),
                        'Bootstrap dependencies differ from admitted inputs')
                source=self._load_bootstrap_source(capsule)
            attempt=uuid.uuid4().hex
            files={n:self._stage_blob_bytes(raw) for n,raw in source.items()} if fresh else capsule['body']['source_files']
            with self._transaction():
                if fresh:
                    for value in files.values():self._register_blob(value)
                    self._register_blob(payload['case_blob'])
                    capsule=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                        'data_class':'development','source_refs':refs,'exposure':exposure,
                        'blob_refs':sorted({v['sha256'] for v in files.values()}|{payload['case_blob']['sha256']}),
                        'authority':AUTHORITY,'body':{'schema':INPUT,'created_at':self._now(),'request':request,
                            'request_hash':digest(request),'payload':payload,'payload_hash':digest(payload),
                            'source_files':files,'source_footprint':footprint(source),'runtime_identity':_runtime_identity(),
                            'bootstrap_sha256':hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),'scientific_readiness':False}})
                self._event('controller','bound_computation_started',attempt_id=attempt,kind='development_bootstrap',
                            input_ref=request['execution_id'],retained_input_id=capsule['id'])
        deadline=time.monotonic()+request['limits']['max_seconds']
        def remaining():
            seconds=deadline-time.monotonic()
            require(seconds>0,'Bootstrap calculation/replay exhausted its total time cap')
            return seconds
        try:
            with self._mutex:
                source=self._load_bootstrap_source(capsule)
                cases=self._read_blob_bytes(payload['case_blob']['sha256'])
                require(len(cases)==payload['case_blob']['size'],'Retained case size differs')
            calculated,draws=run_child(source,payload,cases,remaining())
            result=calculated['result']
            validation=validate_result(result,payload,draws,descriptive)
            verification=None
            if result['status']!='RESOURCE_STOP':
                verification,replayed=run_child(source,payload,cases,remaining(),verify=digest(result),draws=draws)
                require(verification['result']=={'verified_result_hash':digest(result)} and replayed==draws,
                        'Bootstrap independent process replay differs')
            remaining()
            descriptor=self._stage_blob_bytes(draws)
            require(descriptor==calculated['draw_blob'],'Draw commitment differs')
            with self._transaction():
                actor=self._binding_owner(token)
                require(digest(list(self._bootstrap_inputs(actor,request)))==digest([payload,refs,exposure]),
                        'Bootstrap dependencies changed before commitment')
                require(footprint(self._load_bootstrap_source(capsule))==footprint(source),'Bootstrap source changed')
                if fresh:require(footprint(source_bundle())==LOADED_SOURCE,'Installed bootstrap source changed')
                require(_environment_current(calculated['environment']) and
                        (verification is None or _environment_current(verification['environment'])),'Bootstrap runtime changed')
                existing=self._find_bootstrap(RESULT,request)
                if existing is not None:
                    require(existing['body']['input_capsule_id']==capsule['id'] and digest(existing['body']['result'])==digest(result),
                            'Concurrent bootstrap results differ')
                    self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=existing['id'],status='REUSED')
                    return existing
                self._register_blob(descriptor)
                saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':'development','source_refs':sorted(set(refs)|{capsule['id']}),
                    'exposure':sorted(set(exposure)|{capsule['id']}),'blob_refs':[descriptor['sha256']],
                    'authority':AUTHORITY,'body':{'schema':RESULT,'created_at':self._now(),'request':request,
                        'input_capsule_id':capsule['id'],'attempt_id':attempt,'status':result['status'],'result':result,
                        'draw_blob':descriptor,'environment':calculated['environment'],'verification':verification,
                        'validation':validation,
                        'scientific_readiness':False,'qualification':'Exploratory computation and source replay; no calibration, scientific freeze or evidence publication.'}})
                self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=saved['id'],status=result['status'])
                return saved
        except BaseException:
            with self._transaction():
                self._event('controller','bound_computation_interrupted',attempt_id=attempt,reason='bootstrap_failed_or_cancelled')
            raise
