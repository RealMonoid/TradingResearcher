"""Operator-owned finite studies with immutable inputs and aggregate accounting."""
import hashlib
import math
from pathlib import Path
import re
import stat
import sys
import tempfile
import time
import uuid

from .binding import require, write_file
from .binance_normalize import _run_child
from .certification import _environment_current, _runtime_identity
from .codec import Invalid, canonical, decode, digest, text
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .information_study import make_manifest, summarize, budget_state
from .study_pipeline import BOOTSTRAP
from .study_stream import validate_stream
from .study_resources import ResourceHistory, validate_request, SCHEMA as CONTINUATION, AUTHORITY as RESOURCE_AUTHORITY


INPUT='information-study-input/1'
RESULT='development-information-study-attempt/1'
AUTHORITY='development_study_not_scientific_admission'
LOADED_SOURCE=footprint(source_bundle())
METADATA_BYTES=1024*1024


def execute_attempt(source,payload,manifest,world,cases,remaining,meter,outputs):
    """Generate and replay in separate processes; account aborted files as well."""
    expected=footprint(source)
    # Includes two complete materializations, stdout/stderr bounds and retained
    # outputs. This is a logical byte budget, not an OS disk/memory quota.
    budget=manifest['profile']['budget']['attempt_storage_bytes']
    overhead=2*(sum(map(len,source.values()))+len(cases)+4*METADATA_BYTES)+METADATA_BYTES
    stream_limit=min(256*1024*1024,(budget-overhead)//4)
    require(stream_limit>0,'Attempt storage cannot hold inputs and bounded metadata')
    calculated=None;raw=None;proofs=[];encoding=None
    for phase in ('generate','replay'):
        request={'payload':payload,'manifest':manifest,'world':world,'footprint':expected,
            'verify':None if calculated is None else digest(calculated),'stream_limit':stream_limit}
        with tempfile.TemporaryDirectory(prefix='trf-study-') as temporary:
            directory=Path(temporary)
            meter['accounting_complete']=False
            try:
                for name,value in source.items():
                    path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);write_file(path,value)
                write_file(directory/'cases.jsonl',cases)
                write_file(directory/'request.json',canonical(request).encode())
                if raw is not None:
                    write_file(directory/('expected-stream.jsonl.gz' if encoding is not None else 'expected-stream.jsonl'),raw)
                response=_run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],
                    directory,timeout=remaining())
                fields={'result','stream_blob','request_hash','footprint','environment'}
                require(type(response) is dict and (set(response)==fields or set(response)==fields|{'stream_encoding'}),
                    'Malformed study child response')
                encoded='stream_encoding' in response
                if phase=='replay':
                    require(encoded==(encoding is not None) and response.get('stream_encoding')==encoding,
                        'Study replay encoding differs')
                require(response['request_hash']==digest(request) and response['footprint']==expected
                    and _environment_current(response['environment']),'Study response identity differs')
                path=directory/(('stream' if phase=='generate' else 'expected-stream')+'.jsonl'+('.gz' if encoded else ''))
                require(path.stat().st_size<=stream_limit,'Study encoded file exceeds bound')
                observed=path.read_bytes()
                require(len(observed)<=stream_limit and response['stream_blob']==
                    {'sha256':hashlib.sha256(observed).hexdigest(),'size':len(observed)},'Study stream digest differs')
                if encoded:validate_stream(observed,response['stream_encoding'],encoded_limit=stream_limit)
                require(footprint({name:(directory/name).read_bytes() for name in source})==expected,
                    'Retained study package changed')
                proof={key:response[key] for key in ('request_hash','footprint','environment','stream_blob')}
                if encoded:proof['stream_encoding']=response['stream_encoding']
                proofs.append(proof)
                if phase=='generate':
                    calculated=response['result'];raw=observed;encoding=response.get('stream_encoding')
                    # Time/segment/numeric stops are not deterministic successful
                    # computations and must never acquire a completed-world status.
                    if calculated['outcome']['state']=='TECHNICAL_FAILURE':return calculated,proofs
                else:
                    require(response['result']=={'verified_result_hash':digest(calculated)} and observed==raw,
                        'Independent study replay differs')
            finally:
                for path in directory.rglob('*'):
                    observed_stat=path.stat()
                    if stat.S_ISREG(observed_stat.st_mode):meter['materialized_bytes']+=observed_stat.st_size
                # Originals already exist in the input capsule; preserve every
                # output/prefix, diagnostic and replay input even after failure.
                for name in ('stream.jsonl','expected-stream.jsonl','stream.jsonl.gz','expected-stream.jsonl.gz',
                        'child-output.json','child-errors.txt'):
                    path=directory/name
                    try:observed_stat=path.stat()
                    except FileNotFoundError:continue
                    require(stat.S_ISREG(observed_stat.st_mode),'Unexpected study output file type')
                    outputs.append((phase+'/'+name,path.read_bytes()))
                meter['accounting_complete']=True
    return calculated,proofs


class InformationStudies:
    _study_input_schema=INPUT
    _study_result_schema=RESULT
    _study_data_class='development'
    _study_authority=AUTHORITY
    _study_request_fields={'key','plan_id','execution_id','diagnostics_id','profile'}

    def _study_identity(self,request):
        return digest({key:value for key,value in request.items() if key!='key'})

    def _study_existing_request(self,existing,request):
        pass

    def _study_capture_source(self,request):
        source=source_bundle()
        if footprint(source)!=LOADED_SOURCE:raise Conflict('Study source changed since import; restart')
        return source

    def _study_extra_input(self,request,manifest):
        return {}

    def _study_input_ref(self,study):
        return study['body']['request']['execution_id']

    def _study_summary(self,study,records,results):
        return summarize(study['body']['manifest'],records)

    def _study_before_execute(self,study):
        pass

    def _study_manifest(self,assigned,profile):
        return make_manifest(assigned,profile)

    def _study_failed_outcome(self,manifest,world,prior=None):
        base=prior or {'world_id':world['id'],'scope_count':None,'condition_count':None}
        return {**base,'state':'TECHNICAL_FAILURE','decision':None,'covered':None}

    def _study_artifacts(self):
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            envelope=decode(row['envelope']);body=envelope.get('body')
            if (envelope['creator']==envelope['origin']=='controller' and type(body) is dict
                    and body.get('schema')==self._study_input_schema):yield self._artifact(row['id'])

    def _study(self,identity):
        text(identity,'study id');artifact=self._artifact(identity);body=artifact.get('body')
        require(artifact['creator']==artifact['origin']=='controller' and artifact['data_class']==self._study_data_class
            and type(body) is dict and body.get('schema')==self._study_input_schema,'Owned study input required')
        return artifact

    def _study_cost_source(self,estimate):
        require(type(estimate) is dict and set(estimate)=={'source_ref','world_time_rows','observed_compute_ms',
            'observed_storage_bytes','qualification'},'Exact retained cost estimate required')
        identity=estimate['source_ref'];text(identity,'cost source')
        source=self._artifact(identity);pending=[source];seen=set()
        while pending:
            current=pending.pop()
            if current['id'] in seen:continue
            seen.add(current['id'])
            if current['data_class']!='development':raise Denied('Study cost ancestry must be development-only')
            for ref in set(current['source_refs'])|set(current['exposure']):
                if ref not in seen:pending.append(self._artifact(ref))
        require(source['body']=={'schema':'development-study-cost-estimate/1',
            **{key:value for key,value in estimate.items() if key!='source_ref'}},'Cost estimate differs from its retained source')
        return source,seen

    def _study_inputs(self,actor,request):
        diagnostic=self._artifact(request['diagnostics_id']);body=diagnostic.get('body')
        if not (diagnostic['creator']==diagnostic['origin']=='controller' and diagnostic['data_class']=='development'
                and type(body) is dict and body.get('schema')=='development-information-diagnostics/1'):
            raise Denied('Study requires owned development diagnostics')
        require(body['request']['plan_id']==request['plan_id'] and body['request']['execution_id']==request['execution_id'],
            'Study diagnostic lineage differs')
        require(type(request['profile']) is dict,'Exact study profile required')
        cost,ancestry=self._study_cost_source(request['profile'].get('cost_estimate'))
        plan,execution,refs,exposure=self._development_plan_execution(actor,request['plan_id'],request['execution_id'])
        p=plan['body'];result=execution['body']['result'];report=result['report']
        criterion=p['plan']['effect_criterion'];width=len(report['request']['universe']['instruments'])
        require(criterion['profile']=='binary-probability-five-percentage-points/1','Binary study profile required')
        payload={'report':report,'case_blob':result['case_blob'],'diagnostics':body['result']}
        assigned={'input_binding':digest({'payload':payload,'plan_id':plan['id'],'diagnostics_id':diagnostic['id']}),
            'base_length':p['request']['dependence']['base_length'],'primary_count':p['request']['primary_count'],
            'delta':criterion['delta'],'direction':criterion['direction'],'horizon_bars':report['request']['horizon_bars'],
            'available_time_rows':report['expected_case_count']//width,'instruments':width}
        manifest=self._study_manifest(assigned,request['profile'])
        refs=sorted(set(refs)|{diagnostic['id'],cost['id']}|ancestry)
        exposure=sorted(set(exposure)|set(diagnostic['exposure'])|set(refs))
        return payload,manifest,refs,exposure

    def _prepare_information_study_external(self,token,args):
        with self._mutex:
            actor=self._binding_owner(token)
            require(set(args)==self._study_request_fields,'Exact study request required')
            request=decode(canonical(args))
            for key in ('key','plan_id','execution_id','diagnostics_id'):
                if key in request:text(request[key],key)
            for row in self._db.execute('SELECT envelope FROM events ORDER BY seq'):
                event=decode(row[0]);details=event['details']
                if event['actor']=='controller' and event['action']=='information_study_key' and details['key']==request['key']:
                    if details['request_hash']!=digest(request):raise Conflict('Study key already binds its original request')
                    return self._study(details['study_id'])
            identity=self._study_identity(request)
            existing=next((item for item in self._study_artifacts() if item['body']['identity']==identity),None)
            if existing is not None:
                self._study_existing_request(existing,request)
                with self._transaction():self._event('controller','information_study_key',key=request['key'],
                    request_hash=digest(request),study_id=existing['id'])
                return existing
            payload,manifest,refs,exposure=self._study_inputs(actor,request)
            source=self._study_capture_source(request)
            extra=self._study_extra_input(request,manifest)
            initial=2*sum(map(len,source.values()))+payload['case_blob']['size']+METADATA_BYTES
            require(initial<=manifest['profile']['budget']['max_storage_bytes'],'Study input retention exceeds aggregate storage')
            files={name:self._stage_blob_bytes(raw) for name,raw in source.items()}
            with self._transaction():
                for descriptor in files.values():self._register_blob(descriptor)
                self._register_blob(payload['case_blob'])
                study=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':self._study_data_class,'source_refs':refs,'exposure':exposure,
                    'blob_refs':sorted({value['sha256'] for value in files.values()}|{payload['case_blob']['sha256']}),
                    'authority':self._study_authority,'body':{'schema':self._study_input_schema,'created_at':self._now(),'request':request,
                        'identity':identity,'payload':payload,'manifest':manifest,'source_files':files,
                        'source_footprint':footprint(source),'runtime_identity':_runtime_identity(),
                        'bootstrap_sha256':hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),'initial_storage_bytes':initial,
                        'cost_estimate_authority':'retained_operator_input_not_authenticated_benchmark',
                        'accounting':'logical_materializations_plus_retained_outputs_plus_1MiB_metadata_per_attempt; '
                            'parent_elapsed_through_staging_excludes_final_commit; unknown_usage_charges_full_reservation',
                        'scientific_readiness':False,**extra}})
                self._event('controller','information_study_key',key=request['key'],request_hash=digest(request),study_id=study['id'])
            return study

    def _study_history(self,study):
        history=self._study_resources(study)
        return history.reservations,history.settlements,list(history.records.values()),history.results,history.orphan

    def _study_resources(self,study):
        history=ResourceHistory(study)
        for row in self._db.execute('SELECT envelope FROM events ORDER BY seq'):
            history.apply(decode(row[0]),self._artifact)
        return history

    def _study_resource_dependency(self,study,view):
        identity=view['continuation_ids'][-1] if view['continuation_ids'] else study['id']
        self._require_usable_dependencies(identity)
        return identity

    def _continue_study_external(self,token,args):
        with self._transaction():
            actor=self._binding_owner(token);request=decode(canonical(args));validate_request(request)
            # An exact replay returns its immutable decision even after later
            # work or revocation. This does not authorize a new computation.
            for row in self._db.execute('SELECT envelope FROM events ORDER BY seq'):
                event=decode(row[0])
                if event['actor']=='controller' and event['action']=='information_study_continued':
                    grant=self._artifact(event['details']['artifact_id'])
                    if grant['body']['request']['key']==request['key']:
                        if grant['body']['request']!=request:raise Conflict('Continuation key already binds its original request')
                        return grant
            study=self._study(request['study_id']);history=self._study_resources(study);terms=history.terms(request)
            view=self._study_view(study);require(view['status']=='RESOURCE_STOP','Study is not at a resource stop')
            self._study_resource_dependency(study,view);self._study_before_execute(study)
            body=study['body'];inputs=self._study_inputs(actor,body['request'])
            require(digest(list(inputs))==digest([body['payload'],body['manifest'],study['source_refs'],study['exposure']]),
                'Study dependencies changed')
            self._load_study_source(study)
            refs,exposure=history.references()
            saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'operations','source_refs':refs,'exposure':exposure,'blob_refs':[],'authority':RESOURCE_AUTHORITY,
                'body':{'schema':CONTINUATION,'created_at':self._now(),'request':request,**terms,'scientific_readiness':False}})
            self._event('controller','information_study_continued',study_id=study['id'],artifact_id=saved['id'])
            # Verify the same chronological replay used after restart before
            # committing the artifact and event together.
            self._study_resources(study).budget()
            return saved

    def _study_view(self,study):
        history=self._study_resources(study)
        records=list(history.records.values());results=history.results;orphan=history.orphan
        manifest=study['body']['manifest'];budget=history.budget()
        limits=manifest['profile']['budget']
        summary=self._study_summary(study,records,results);by_world={r['world_id']:r for r in records}
        pending=next((w for w in manifest['worlds'] if w['id'] not in by_world
            or by_world[w['id']]['state']=='TECHNICAL_FAILURE'),None)
        state=('ORPHAN_UNCERTAIN' if orphan else 'RUNNING' if budget['outstanding_attempts'] else
            'COMPLETE' if summary['complete'] else 'MODEL_GAP' if any(r['state']=='MODEL_GAP' for r in records) else
            'TECHNICAL_FAILURE' if pending and budget['attempts_per_world'].get(pending['id'],0)>=limits['max_attempts'] else
            'RESOURCE_STOP' if not budget['next_reservation_fits'] else 'READY')
        # A complete numerical grid cannot hide an observed resource overrun.
        if not orphan and not budget['outstanding_attempts'] and budget['overrun']:state='RESOURCE_STOP'
        if state!='COMPLETE':summary['candidate_time_rows']=None
        return {'study_id':study['id'],'status':state,'budget':budget,'summary':summary,
            'next_world_id':pending['id'] if state=='READY' and pending else None,'attempt_artifact_ids':results,
            'resource_checkpoint':history.checkpoint,'continuation_ids':[g['id'] for g in history.grants],
            'scientific_readiness':False,'n_min':None}

    def _load_study_source(self,study):
        body=study['body'];files=body['source_files']
        require(body['runtime_identity']==_runtime_identity() and
            body['bootstrap_sha256']==hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),'Retained study runtime differs')
        require(type(files) is dict and 1<=len(files)<=128 and all(
            re.fullmatch(r'trading_researcher/[A-Za-z_][A-Za-z0-9_]*\.py',name) for name in files),'Invalid retained study paths')
        require(sum(value['size'] for value in files.values())<=16*1024*1024,'Retained study source exceeds envelope')
        require(set(study['blob_refs'])=={value['sha256'] for value in files.values()}|{body['payload']['case_blob']['sha256']},
            'Retained study references differ')
        source={name:self._read_blob_bytes(value['sha256']) for name,value in files.items()}
        require(footprint(source)==body['source_footprint'] and all(len(source[name])==value['size'] for name,value in files.items()),
            'Retained study source differs')
        return source

    def _settle_study(self,study,attempt,settlement,outcome,artifact_id,orphan=False):
        view=self._study_view(study)
        require(attempt in view['budget']['outstanding_attempts'],'Stale or already settled study attempt')
        reservations,settlements,*_=self._study_history(study)
        reservation=next(r for r in reservations if r['attempt_id']==attempt)
        require(settlement.get('attempt_id')==attempt,'Settlement attempt differs from its reservation')
        require(outcome['world_id']==reservation['world_id'],'Settlement world differs from its reservation')
        budget_state(study['body']['manifest'],reservations,settlements+[settlement],
            additional_compute_ms=view['budget']['max_compute_ms']-view['budget']['original_max_compute_ms'],
            additional_storage_bytes=view['budget']['max_storage_bytes']-view['budget']['original_max_storage_bytes'])
        summarize(study['body']['manifest'],[outcome])
        self._event('controller','information_study_settled',study_id=study['id'],settlement=settlement,
            outcome=outcome,artifact_id=artifact_id,orphan_uncertain=orphan)
        self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=artifact_id,status=outcome['state'])

    def _recover_information_studies(self):
        with self._transaction():
            for study in list(self._study_artifacts()):
                reservations,settlements,*_=self._study_history(study)
                closed={item['attempt_id'] for item in settlements}
                for reservation in reservations:
                    attempt=reservation['attempt_id']
                    if attempt in closed:continue
                    world=next(w for w in study['body']['manifest']['worlds'] if w['id']==reservation['world_id'])
                    outcome=self._study_failed_outcome(study['body']['manifest'],world)
                    self._settle_study(study,attempt,{'attempt_id':attempt,'compute_ms':0,'storage_bytes':0,
                        'usage_known':False},outcome,None,orphan=True)

    def _inspect_information_study_external(self,token,args):
        with self._mutex:
            self._binding_owner(token);require(set(args)=={'study_id'},'Exact study inspection required')
            return self._study_view(self._study(args['study_id']))

    def _advance_information_study_external(self,token,args):
        started=time.monotonic()
        with self._transaction():
            actor=self._binding_owner(token);require(set(args)=={'study_id'},'Exact study advance required')
            study=self._study(args['study_id']);view=self._study_view(study)
            if view['status']=='RUNNING':raise Conflict('Study already has an outstanding attempt')
            if view['status']!='READY':return view
            continuation_id=view['continuation_ids'][-1] if view['continuation_ids'] else None
            resource_dependency=self._study_resource_dependency(study,view) if continuation_id else study['id']
            resource_exposure=self._artifact(resource_dependency)['exposure'] if continuation_id else []
            body=study['body'];manifest=body['manifest'];limits=manifest['profile']['budget']
            world=next(w for w in manifest['worlds'] if w['id']==view['next_world_id'])
            attempt=uuid.uuid4().hex
            self._event('controller','information_study_reserved',study_id=study['id'],reservation={
                'attempt_id':attempt,'world_id':world['id'],'compute_ms':limits['attempt_compute_ms'],
                'storage_bytes':limits['attempt_storage_bytes']})
            self._event('controller','bound_computation_started',attempt_id=attempt,kind='information_study',
                input_ref=self._study_input_ref(study),retained_input_id=study['id'])
        def remaining():
            seconds=limits['attempt_compute_ms']/1000-(time.monotonic()-started)
            require(seconds>0,'Study attempt exhausted its compute reservation')
            return seconds
        meter={'materialized_bytes':0,'accounting_complete':True};outputs=[];result=None;proofs=[];failure=None;cancelled=None
        outcome=self._study_failed_outcome(manifest,world)
        try:
            with self._mutex:
                actor=self._binding_owner(token)
                self._study_before_execute(study)
                inputs=self._study_inputs(actor,body['request'])
                require(digest(list(inputs))==digest([body['payload'],manifest,study['source_refs'],study['exposure']]),
                    'Study dependencies changed')
                source=self._load_study_source(study);cases=self._read_blob_bytes(body['payload']['case_blob']['sha256'])
            result,proofs=execute_attempt(source,body['payload'],manifest,world,cases,remaining,meter,outputs)
            require(result['world_id']==world['id'] and result['scientific_readiness'] is False
                and result['classification_permitted'] is False and result['n_min'] is None,'Study result claims forbidden authority')
            summarize(manifest,[result['outcome']])
            if result['outcome']['state']!='TECHNICAL_FAILURE':require(len(proofs)==2,'Completed study world requires separate replay')
            remaining()
            outcome=(self._study_failed_outcome(manifest,world,result['outcome'])
                if result['outcome']['state']=='TECHNICAL_FAILURE' else result['outcome'])
        except BaseException as exc:
            failure={'type':type(exc).__name__,'message':str(exc)[:2000]}
            if not isinstance(exc,Exception):cancelled=exc
        # Stage retained outputs before charging elapsed work. Any failure here
        # leaves the full reservation outstanding and fences all replacement work.
        with self._mutex:
            descriptors={name:self._stage_blob_bytes(raw) for name,raw in outputs}
            storage=meter['materialized_bytes']+sum(len(raw) for _,raw in outputs)+METADATA_BYTES
            compute=math.ceil((time.monotonic()-started)*1000)
            settlement={'attempt_id':attempt,'compute_ms':compute,'storage_bytes':storage,
                'usage_known':meter['accounting_complete']}
            if compute>limits['attempt_compute_ms'] or storage>limits['attempt_storage_bytes']:
                outcome=self._study_failed_outcome(manifest,world,outcome)
                failure={'type':'ResourceOverrun','message':'Observed work exceeded its frozen attempt reservation'}
            with self._transaction():
                require(attempt in self._study_view(study)['budget']['outstanding_attempts'],'Stale study result')
                # Revocation can arrive while the isolated computation runs.
                # Retain/charge its output, but never settle it as a valid world.
                try:self._require_usable_dependencies(resource_dependency)
                except (Invalid,Denied,Conflict) as exc:
                    outcome=self._study_failed_outcome(manifest,world,outcome)
                    failure={'type':type(exc).__name__,'message':str(exc)[:2000]}
                for descriptor in descriptors.values():self._register_blob(descriptor)
                saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':self._study_data_class,'source_refs':sorted({study['id'],resource_dependency}),
                    'exposure':sorted(set(study['exposure'])|set(resource_exposure)|{study['id'],resource_dependency}),
                    'blob_refs':sorted({v['sha256'] for v in descriptors.values()}),'authority':self._study_authority,
                    'body':{'schema':self._study_result_schema,'created_at':self._now(),'study_id':study['id'],'attempt_id':attempt,
                        **({'continuation_id':continuation_id} if continuation_id else {}),
                        'world_id':world['id'],'outcome':outcome,'result':result,'proofs':proofs,
                        'output_blobs':descriptors,'settlement':settlement,'failure':failure,'scientific_readiness':False}})
                self._settle_study(study,attempt,settlement,outcome,saved['id'])
            view=self._study_view(study)
        if cancelled is not None:raise cancelled
        return view
