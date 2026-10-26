"""Owned development population worlds with pre-computation retention and replay."""
import hashlib
from pathlib import Path
import re
import sys
import tempfile
import time
import uuid

from .binding import environment, require, write_file
from .binance_normalize import _run_child
from .certification import _environment_current, _runtime_identity
from .codec import canonical, decode, digest, integer, text
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .population_models import build_model, generate_world, validate_specification, WORLD
from .outcomes import _read_rational, _rational
from .stationary_bootstrap import randomness
from .storage import _hash_file


INPUT='population-world-input/1'
RESULT='development-population-world/1'
AUTHORITY='development_population_world_not_scientific_admission'
LOADED_SOURCE=footprint(source_bundle())
BOOTSTRAP=('import sys;sys.path.insert(0,sys.argv[1]);'
    'from trading_researcher.population_runs import child_entry;child_entry(sys.argv[2])')


def child_entry(request_path):
    directory=Path(request_path).parent;request=decode(Path(request_path).read_bytes())
    expected=request['footprint'];payload=request['payload'];verify=request['verify']
    require(footprint(source_bundle())==expected,'Retained population source differs')
    observed_environment=environment(expected)
    identity,size,_=_hash_file(directory/'cases.jsonl')
    require({'sha256':identity,'size':size}==payload['case_blob'],'Population cases differ')
    cases=[]
    with (directory/'cases.jsonl').open('rb') as stream:
        while line:=stream.readline(1048577):
            require(len(line)<=1048576 and len(cases)<100000,'Population case envelope exceeded')
            cases.append(decode(line))
    path=directory/('expected-world.jsonl' if verify is not None else 'world.jsonl')
    checksum=hashlib.sha256();total=0
    with path.open('rb' if verify is not None else 'xb') as stream:
        def retain(record):
            nonlocal total
            raw=(canonical(record)+'\n').encode();total+=len(raw)
            require(total<=128*1024*1024,'Population cases exceed their storage envelope')
            checksum.update(raw)
            if verify is None:stream.write(raw)
            else:require(stream.read(len(raw))==raw,'Population contribution replay differs')
        report={**payload['report'],'cases':cases}
        model=build_model(report,payload['diagnostics'],payload['specification'],payload['effects'])
        world=None
        if model['status']=='MODEL_SPECIFIED':
            world=generate_world(report,model,payload['scenario'],payload['time_rows'],payload['seed'])
            for case in world['report'].pop('cases'):retain(case)
        result={'schema':WORLD,'status':model['status'] if world is None else world['status'],
            'model':model,'world':world,'n_min':None,'scientific_readiness':False,'classification_permitted':False}
        if verify is not None:
            require(stream.read(1)==b'','Unexpected contribution suffix')
            require(digest(result)==verify,'Population result differs from exact replay')
    require(footprint(source_bundle())==expected,'Population source changed during computation')
    print(canonical({'result':result if verify is None else {'verified_result_hash':verify},
        'world_blob':{'sha256':checksum.hexdigest(),'size':total},'request_hash':digest(request),
        'footprint':expected,'environment':observed_environment}),flush=True)


def run_child(source,payload,cases,timeout,verify=None,world_cases=None):
    expected=footprint(source)
    request={'payload':payload,'footprint':expected,'verify':verify}
    with tempfile.TemporaryDirectory(prefix='trf-population-') as temporary:
        directory=Path(temporary)
        for name,raw in source.items():
            path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);write_file(path,raw)
        write_file(directory/'cases.jsonl',cases)
        write_file(directory/'request.json',canonical(request).encode())
        if verify is not None:write_file(directory/'expected-world.jsonl',world_cases)
        response=_run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],
            directory,timeout=timeout)
        require(type(response) is dict and set(response)=={'result','world_blob','request_hash','footprint','environment'},
            'Malformed population child response')
        require(response['request_hash']==digest(request) and response['footprint']==expected
            and _environment_current(response['environment']),'Population response identity differs')
        raw=(directory/('expected-world.jsonl' if verify is not None else 'world.jsonl')).read_bytes()
        require(len(raw)<=128*1024*1024 and {'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}==response['world_blob'],
            'Population contribution bytes differ')
        require(footprint({name:(directory/name).read_bytes() for name in source})==expected,'Population package changed')
        return response,raw


class PopulationWorlds:
    def _find_population_world(self,schema,request):
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            envelope=decode(row['envelope']);body=envelope.get('body')
            if (envelope['creator']==envelope['origin']=='controller' and type(body) is dict
                    and body.get('schema')==schema and body['request']['key']==request['key']):
                if digest(body['request'])!=digest(request):raise Conflict('Population key already binds its original request')
                return self._artifact(row['id'])
        return None

    def _population_inputs(self,actor,request):
        diagnostic=self._artifact(request['diagnostics_id']);body=diagnostic.get('body')
        if not (diagnostic['creator']==diagnostic['origin']=='controller' and diagnostic['data_class']=='development'
                and type(body) is dict and body.get('schema')=='development-information-diagnostics/1'):
            raise Denied('Population world requires owned development diagnostics')
        require(body['request']['plan_id']==request['plan_id'] and body['request']['execution_id']==request['execution_id'],
            'Population diagnostic lineage differs')
        plan,execution,refs,exposure=self._development_plan_execution(actor,request['plan_id'],request['execution_id'])
        result=execution['body']['result'];criterion=plan['body']['plan']['effect_criterion']
        bound=result['report']['request']
        require(bound['horizon_bars']<request['time_rows']
            and request['time_rows']*len(bound['universe']['instruments'])<=100000,
            'Population target exceeds its bound case/horizon envelope')
        require(criterion['profile']=='binary-probability-five-percentage-points/1',
            'Population world requires the owned binary effect profile')
        delta=_read_rational(criterion['delta']);direction=criterion['direction']
        require(direction in ('positive','negative','nondirectional'),'Unsupported owned direction')
        effects=([0,delta,2*delta,-delta,-2*delta] if direction=='nondirectional' else
                 [0,delta,2*delta] if direction=='positive' else [0,-delta,-2*delta])
        require(request['scenario']<len(effects),'Undeclared population scenario')
        refs=sorted(set(refs)|{diagnostic['id']})
        exposure=sorted(set(exposure)|set(diagnostic['exposure'])|set(refs))
        return {'report':result['report'],'case_blob':result['case_blob'],'diagnostics':body['result'],
            'effects':[_rational(value) for value in effects],
            **{key:request[key] for key in ('specification','scenario','time_rows','seed','limits')}},refs,exposure

    def _load_population_source(self,capsule):
        body=capsule['body']
        require(capsule['creator']==capsule['origin']=='controller' and capsule['data_class']=='development'
            and type(body) is dict and body.get('schema')==INPUT,'Unowned population input')
        require(body['request_hash']==digest(body['request']) and body['payload_hash']==digest(body['payload']),
            'Retained population request differs')
        require(body['runtime_identity']==_runtime_identity()
            and body['bootstrap_sha256']==hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),'Population runtime differs')
        files=body['source_files']
        require(type(files) is dict and 1<=len(files)<=128
            and all(re.fullmatch(r'trading_researcher/[A-Za-z_][A-Za-z0-9_]*\.py',name) for name in files),
            'Invalid population source paths')
        require({'trading_researcher/__init__.py','trading_researcher/population_runs.py',
            'trading_researcher/population_models.py'}<=set(files),'Incomplete population source')
        require(all(type(item) is dict and set(item)=={'sha256','size'} and type(item['size']) is int
            and 0<=item['size']<=16*1024*1024 for item in files.values())
            and sum(item['size'] for item in files.values())<=16*1024*1024,'Invalid source resource envelope')
        require(set(capsule['blob_refs'])=={item['sha256'] for item in files.values()}|{body['payload']['case_blob']['sha256']},
            'Population source references differ')
        source={name:self._read_blob_bytes(item['sha256']) for name,item in files.items()}
        require(all(len(source[name])==item['size'] for name,item in files.items())
            and footprint(source)==body['source_footprint'],'Retained population source differs')
        return source

    def _run_population_world_external(self,token,args):
        with self._mutex:
            actor=self._binding_owner(token)
            require(set(args)=={'key','plan_id','execution_id','diagnostics_id','specification','scenario','time_rows','seed','limits'},'Exact population request required')
            request=decode(canonical(args))
            for key in ('key','plan_id','execution_id','diagnostics_id'):text(request[key],key)
            validate_specification(request['specification'])
            integer(request['scenario'],'scenario',0)
            integer(request['time_rows'],'joint time rows',1)
            require(request['time_rows']<=100000,'World target exceeds its grid envelope')
            randomness(request['seed'])
            limits=request['limits']
            require(type(limits) is dict and set(limits)=={'max_seconds'},'Explicit population time limit required')
            integer(limits['max_seconds'],'population time limit',1)
            require(limits['max_seconds']<=1800,'Population time limit exceeds the development envelope')
            existing=self._find_population_world(RESULT,request)
            if existing is not None:return existing
            capsule=self._find_population_world(INPUT,request)
            payload,refs,exposure=self._population_inputs(actor,request)
            fresh=capsule is None
            if fresh:
                source=source_bundle()
                if footprint(source)!=LOADED_SOURCE:raise Conflict('Population source changed since import; restart')
            else:
                require(digest([payload,refs,exposure])==digest([capsule['body']['payload'],capsule['source_refs'],capsule['exposure']]),
                    'Population dependencies differ from the retained inputs')
                source=self._load_population_source(capsule)
            attempt=uuid.uuid4().hex
            files={name:self._stage_blob_bytes(raw) for name,raw in source.items()} if fresh else capsule['body']['source_files']
            with self._transaction():
                if fresh:
                    for descriptor in files.values():self._register_blob(descriptor)
                    self._register_blob(payload['case_blob'])
                    capsule=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                        'data_class':'development','source_refs':refs,'exposure':exposure,
                        'blob_refs':sorted({v['sha256'] for v in files.values()}|{payload['case_blob']['sha256']}),
                        'authority':AUTHORITY,'body':{'schema':INPUT,'created_at':self._now(),'request':request,
                            'request_hash':digest(request),'payload':payload,'payload_hash':digest(payload),
                            'source_files':files,'source_footprint':footprint(source),'runtime_identity':_runtime_identity(),
                            'bootstrap_sha256':hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),'scientific_readiness':False}})
                self._event('controller','bound_computation_started',attempt_id=attempt,kind='population_world',
                    input_ref=request['execution_id'],retained_input_id=capsule['id'])
        deadline=time.monotonic()+limits['max_seconds']
        def remaining():
            seconds=deadline-time.monotonic()
            require(seconds>0,'Population computation/replay exhausted its time cap')
            return seconds
        try:
            with self._mutex:
                source=self._load_population_source(capsule)
                cases=self._read_blob_bytes(payload['case_blob']['sha256'])
                require(len(cases)==payload['case_blob']['size'],'Retained case size differs')
            calculated,raw=run_child(source,payload,cases,remaining())
            result=calculated['result']
            require(type(result) is dict and result.get('schema')==WORLD and result.get('n_min') is None
                and result.get('scientific_readiness') is False and result.get('classification_permitted') is False,
                'Populations cannot grant scientific authority')
            require(result['model']['diagnostics_hash']==digest(payload['diagnostics']),
                'Population input binding differs')
            if result['world'] is None:
                require(raw==b'' and result['status']=='MODEL_OR_INFORMATION_GAP','Invalid model gap')
            else:
                require(result['world']['time_rows']==payload['time_rows']
                    and len(raw.splitlines())==payload['time_rows']*len(payload['report']['request']['universe']['instruments']),
                    'Population world case count differs')
            verified,replayed=run_child(source,payload,cases,remaining(),verify=digest(result),world_cases=raw)
            require(verified['result']=={'verified_result_hash':digest(result)} and replayed==raw,
                'Population independent process replay differs')
            remaining()
            descriptor=self._stage_blob_bytes(raw)
            require(descriptor==calculated['world_blob'],'Population contribution commitment differs')
            with self._transaction():
                actor=self._binding_owner(token)
                require(digest(list(self._population_inputs(actor,request)))==digest([payload,refs,exposure]),
                    'Population dependencies changed before commitment')
                require(footprint(self._load_population_source(capsule))==footprint(source),'Population source changed')
                if fresh:require(footprint(source_bundle())==LOADED_SOURCE,'Installed population source changed')
                require(_environment_current(calculated['environment']) and _environment_current(verified['environment']),
                    'Population runtime changed before commitment')
                existing=self._find_population_world(RESULT,request)
                if existing is not None:
                    require(existing['body']['input_capsule_id']==capsule['id']
                        and digest(existing['body']['result'])==digest(result),'Concurrent population results differ')
                    self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=existing['id'],status='REUSED')
                    return existing
                self._register_blob(descriptor)
                saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':'development','source_refs':sorted(set(refs)|{capsule['id']}),
                    'exposure':sorted(set(exposure)|{capsule['id']}),'blob_refs':[descriptor['sha256']],
                    'authority':AUTHORITY,'body':{'schema':RESULT,'created_at':self._now(),'request':request,
                        'input_capsule_id':capsule['id'],'attempt_id':attempt,'status':result['status'],'result':result,
                        'world_blob':descriptor,'environment':calculated['environment'],'verification':verified,
                        'scientific_readiness':False,
                        'qualification':'Declared estimator-level stress world only; no fitted model, power, information target, calibration, evidence or freeze.'}})
                self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=saved['id'],status=result['status'])
                return saved
        except BaseException:
            with self._transaction():
                self._event('controller','bound_computation_interrupted',attempt_id=attempt,reason='population_world_failed_or_cancelled')
            raise
