"""Owned development diagnostic runs with pre-computation retention and replay."""
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
from .errors import Conflict
from .evaluation_plans import source_bundle, footprint
from .information_diagnostics import diagnose, validate_lags, SCHEMA
from .storage import _hash_file


INPUT='information-diagnostics-input/1'
RESULT='development-information-diagnostics/1'
AUTHORITY='development_diagnostics_not_scientific_admission'
LOADED_SOURCE=footprint(source_bundle())
BOOTSTRAP=('import sys;sys.path.insert(0,sys.argv[1]);'
    'from trading_researcher.information_runs import child_entry;child_entry(sys.argv[2])')


def child_entry(request_path):
    directory=Path(request_path).parent;request=decode(Path(request_path).read_bytes())
    expected=request['footprint'];payload=request['payload'];verify=request['verify']
    require(footprint(source_bundle())==expected,'Retained diagnostic source differs')
    observed_environment=environment(expected)
    identity,size,_=_hash_file(directory/'cases.jsonl')
    require({'sha256':identity,'size':size}==payload['case_blob'],'Diagnostic cases differ')
    cases=[]
    with (directory/'cases.jsonl').open('rb') as stream:
        while line:=stream.readline(1048577):
            require(len(line)<=1048576 and len(cases)<100000,'Diagnostic case envelope exceeded')
            cases.append(decode(line))
    path=directory/('expected-contributions.jsonl' if verify is not None else 'contributions.jsonl')
    checksum=hashlib.sha256();total=0
    with path.open('rb' if verify is not None else 'xb') as stream:
        def retain(record):
            nonlocal total
            raw=(canonical(record)+'\n').encode();total+=len(raw)
            require(total<=32*1024*1024,'Diagnostic contributions exceed their storage envelope')
            checksum.update(raw)
            if verify is None:stream.write(raw)
            else:require(stream.read(len(raw))==raw,'Diagnostic contribution replay differs')
        result=diagnose({**payload['report'],'cases':cases},payload['lags'],on_contribution=retain)
        if verify is not None:
            require(stream.read(1)==b'','Unexpected contribution suffix')
            require(digest(result)==verify,'Diagnostic result differs from exact replay')
    require(footprint(source_bundle())==expected,'Diagnostic source changed during computation')
    print(canonical({'result':result if verify is None else {'verified_result_hash':verify},
        'contribution_blob':{'sha256':checksum.hexdigest(),'size':total},'request_hash':digest(request),
        'footprint':expected,'environment':observed_environment}),flush=True)


def run_child(source,payload,cases,timeout,verify=None,contributions=None):
    expected=footprint(source)
    request={'payload':payload,'footprint':expected,'verify':verify}
    with tempfile.TemporaryDirectory(prefix='trf-information-') as temporary:
        directory=Path(temporary)
        for name,raw in source.items():
            path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);write_file(path,raw)
        write_file(directory/'cases.jsonl',cases)
        write_file(directory/'request.json',canonical(request).encode())
        if verify is not None:write_file(directory/'expected-contributions.jsonl',contributions)
        response=_run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],
            directory,timeout=timeout)
        require(type(response) is dict and set(response)=={'result','contribution_blob','request_hash','footprint','environment'},
            'Malformed diagnostic child response')
        require(response['request_hash']==digest(request) and response['footprint']==expected
            and _environment_current(response['environment']),'Diagnostic response identity differs')
        raw=(directory/('expected-contributions.jsonl' if verify is not None else 'contributions.jsonl')).read_bytes()
        require(len(raw)<=32*1024*1024 and {'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}==response['contribution_blob'],
            'Diagnostic contribution bytes differ')
        require(footprint({name:(directory/name).read_bytes() for name in source})==expected,'Diagnostic package changed')
        return response,raw


class InformationDiagnostics:
    def _find_information_diagnostics(self,schema,request):
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            envelope=decode(row['envelope']);body=envelope.get('body')
            if (envelope['creator']==envelope['origin']=='controller' and type(body) is dict
                    and body.get('schema')==schema and body['request']['key']==request['key']):
                if digest(body['request'])!=digest(request):raise Conflict('Diagnostic key already binds its original request')
                return self._artifact(row['id'])
        return None

    def _information_inputs(self,actor,request):
        plan,execution,refs,exposure=self._development_plan_execution(actor,request['plan_id'],request['execution_id'])
        result=execution['body']['result']
        return {'report':result['report'],'case_blob':result['case_blob'],
            'lags':request['lags'],'limits':request['limits']},refs,exposure

    def _load_information_source(self,capsule):
        body=capsule['body']
        require(capsule['creator']==capsule['origin']=='controller' and capsule['data_class']=='development'
            and type(body) is dict and body.get('schema')==INPUT,'Unowned diagnostic input')
        require(body['request_hash']==digest(body['request']) and body['payload_hash']==digest(body['payload']),
            'Retained diagnostic request differs')
        require(body['runtime_identity']==_runtime_identity()
            and body['bootstrap_sha256']==hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),'Diagnostic runtime differs')
        files=body['source_files']
        require(type(files) is dict and 1<=len(files)<=128
            and all(re.fullmatch(r'trading_researcher/[A-Za-z_][A-Za-z0-9_]*\.py',name) for name in files),
            'Invalid diagnostic source paths')
        require({'trading_researcher/__init__.py','trading_researcher/information_runs.py',
            'trading_researcher/information_diagnostics.py'}<=set(files),'Incomplete diagnostic source')
        require(all(type(item) is dict and set(item)=={'sha256','size'} and type(item['size']) is int
            and 0<=item['size']<=16*1024*1024 for item in files.values())
            and sum(item['size'] for item in files.values())<=16*1024*1024,'Invalid source resource envelope')
        require(set(capsule['blob_refs'])=={item['sha256'] for item in files.values()}|{body['payload']['case_blob']['sha256']},
            'Diagnostic source references differ')
        source={name:self._read_blob_bytes(item['sha256']) for name,item in files.items()}
        require(all(len(source[name])==item['size'] for name,item in files.items())
            and footprint(source)==body['source_footprint'],'Retained diagnostic source differs')
        return source

    def _prepare_information_diagnostics_external(self,token,args):
        with self._mutex:
            actor=self._binding_owner(token)
            require(set(args)=={'key','plan_id','execution_id','lags','limits'},'Exact diagnostic request required')
            request=decode(canonical(args))
            for key in ('key','plan_id','execution_id'):text(request[key],key)
            validate_lags(request['lags'])
            limits=request['limits']
            require(type(limits) is dict and set(limits)=={'max_seconds'},'Explicit diagnostic time limit required')
            integer(limits['max_seconds'],'diagnostic time limit',1)
            require(limits['max_seconds']<=1800,'Diagnostic time limit exceeds the development envelope')
            existing=self._find_information_diagnostics(RESULT,request)
            if existing is not None:return existing
            capsule=self._find_information_diagnostics(INPUT,request)
            payload,refs,exposure=self._information_inputs(actor,request)
            fresh=capsule is None
            if fresh:
                source=source_bundle()
                if footprint(source)!=LOADED_SOURCE:raise Conflict('Diagnostic source changed since import; restart')
            else:
                require(digest([payload,refs,exposure])==digest([capsule['body']['payload'],capsule['source_refs'],capsule['exposure']]),
                    'Diagnostic dependencies differ from the retained inputs')
                source=self._load_information_source(capsule)
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
                self._event('controller','bound_computation_started',attempt_id=attempt,kind='information_diagnostics',
                    input_ref=request['execution_id'],retained_input_id=capsule['id'])
        deadline=time.monotonic()+limits['max_seconds']
        def remaining():
            seconds=deadline-time.monotonic()
            require(seconds>0,'Diagnostic computation/replay exhausted its time cap')
            return seconds
        try:
            with self._mutex:
                source=self._load_information_source(capsule)
                cases=self._read_blob_bytes(payload['case_blob']['sha256'])
                require(len(cases)==payload['case_blob']['size'],'Retained case size differs')
            calculated,raw=run_child(source,payload,cases,remaining())
            result=calculated['result']
            require(type(result) is dict and result.get('schema')==SCHEMA and result.get('n_min') is None
                and result.get('scientific_readiness') is False and result.get('classification_permitted') is False,
                'Diagnostics cannot grant scientific authority')
            require(result['lags']==payload['lags'] and result['case_report_hash']==digest(payload['report'])
                and result['case_stream_sha256']==payload['case_blob']['sha256'], 'Diagnostic input binding differs')
            require(result['contributions_sha256']==calculated['contribution_blob']['sha256']
                and type(result['contribution_count']) is int and result['contribution_count']==len(raw.splitlines()),
                'Diagnostic contribution binding differs')
            verified,replayed=run_child(source,payload,cases,remaining(),verify=digest(result),contributions=raw)
            require(verified['result']=={'verified_result_hash':digest(result)} and replayed==raw,
                'Diagnostic independent process replay differs')
            remaining()
            descriptor=self._stage_blob_bytes(raw)
            require(descriptor==calculated['contribution_blob'],'Diagnostic contribution commitment differs')
            with self._transaction():
                actor=self._binding_owner(token)
                require(digest(list(self._information_inputs(actor,request)))==digest([payload,refs,exposure]),
                    'Diagnostic dependencies changed before commitment')
                require(footprint(self._load_information_source(capsule))==footprint(source),'Diagnostic source changed')
                if fresh:require(footprint(source_bundle())==LOADED_SOURCE,'Installed diagnostic source changed')
                require(_environment_current(calculated['environment']) and _environment_current(verified['environment']),
                    'Diagnostic runtime changed before commitment')
                existing=self._find_information_diagnostics(RESULT,request)
                if existing is not None:
                    require(existing['body']['input_capsule_id']==capsule['id']
                        and digest(existing['body']['result'])==digest(result),'Concurrent diagnostic results differ')
                    self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=existing['id'],status='REUSED')
                    return existing
                self._register_blob(descriptor)
                saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':'development','source_refs':sorted(set(refs)|{capsule['id']}),
                    'exposure':sorted(set(exposure)|{capsule['id']}),'blob_refs':[descriptor['sha256']],
                    'authority':AUTHORITY,'body':{'schema':RESULT,'created_at':self._now(),'request':request,
                        'input_capsule_id':capsule['id'],'attempt_id':attempt,'status':result['status'],'result':result,
                        'contribution_blob':descriptor,'environment':calculated['environment'],'verification':verified,
                        'scientific_readiness':False,
                        'qualification':'Development measurements only; no fitted world, information target, calibration, evidence or freeze.'}})
                self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=saved['id'],status=result['status'])
                return saved
        except BaseException:
            with self._transaction():
                self._event('controller','bound_computation_interrupted',attempt_id=attempt,reason='information_diagnostics_failed_or_cancelled')
            raise
