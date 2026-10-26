"""Owned pre-assessment plan drafts; scientific admission and freeze remain separate."""
import hashlib
from pathlib import Path
import re
import sys
import tempfile
import uuid

from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .evaluation_policy import draft_plan
from .binding import environment, write_file, require
from .certification import _environment_current, _runtime_identity
from .binance_normalize import _run_child
from .storage import _hash_file


ROOT=Path(__file__).resolve().parents[1]
SCHEMA='evaluation-plan/1'
INPUT_SCHEMA='evaluation-plan-input/1'


def source_bundle():
    bundle={path.relative_to(ROOT).as_posix():path.read_bytes() for path in sorted((ROOT/'trading_researcher').glob('*.py'))}
    if len(bundle)>128 or sum(map(len,bundle.values()))>16*1024*1024:
        raise Invalid('Plan source capsule exceeds the resource envelope')
    return bundle


def footprint(bundle):
    return {name:hashlib.sha256(raw).hexdigest() for name,raw in bundle.items()}


LOADED_SOURCE=footprint(source_bundle())


BOOTSTRAP=('import sys;sys.path.insert(0,sys.argv[1]);'
    'from trading_researcher.evaluation_plans import child_entry;child_entry(sys.argv[2])')


def child_entry(request_path):
    request=decode(Path(request_path).read_bytes())
    expected=request['footprint']
    require(footprint(source_bundle())==expected,'Retained plan source differs')
    environment(expected)
    try:
        result={'plan':draft_plan(**request['payload']),'gap':None}
    except Invalid as exc:
        result={'plan':None,'gap':{'code':'EVALUATION_GAP','reason':str(exc),
            'reopen_condition':'Supply compatible approved meaning and required development design without changing the original claim'}}
    if request['verify_hash'] is not None:
        require(digest(result)==request['verify_hash'],'Plan response differs from exact retained replay')
        result={'verified_result_hash':digest(result)}
    require(footprint(source_bundle())==expected,'Plan source changed during computation')
    print(canonical({'result':result,'request_hash':digest(request),'footprint':expected,
        'environment':environment(expected)}),flush=True)


def run_plan_child(bundle,payload,verify_hash=None):
    expected=footprint(bundle)
    request={'payload':payload,'footprint':expected,'verify_hash':verify_hash}
    with tempfile.TemporaryDirectory(prefix='trf-plan-') as temporary:
        directory=Path(temporary)
        for name,raw in bundle.items():
            path=directory/name
            path.parent.mkdir(parents=True,exist_ok=True)
            write_file(path,raw)
        write_file(directory/'request.json',canonical(request).encode())
        report=_run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],directory)
        require(type(report) is dict and set(report)=={'result','request_hash','footprint','environment'},'Malformed plan response')
        require(report['request_hash']==digest(request) and report['footprint']==expected
            and _environment_current(report['environment']),'Plan response identity/environment mismatch')
        require(footprint({name:(directory/name).read_bytes() for name in bundle})==expected,'Plan package changed')
        return report


class EvaluationPlans:
    def _existing_plan_input(self,request):
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            envelope=decode(row['envelope'])
            body=envelope.get('body')
            if (envelope['creator']==envelope['origin']=='controller' and type(body) is dict
                    and body.get('schema')==INPUT_SCHEMA and body['request']['key']==request['key']):
                if digest(body['request'])!=digest(request):
                    raise Conflict('Plan key already binds a retained request, including after interruption')
                return self._artifact(row['id'])
        return None

    def _load_plan_input_source(self,capsule):
        body=capsule['body']
        require(capsule['creator']==capsule['origin']=='controller' and capsule['data_class']=='development'
            and type(body) is dict and body.get('schema')==INPUT_SCHEMA,'Unowned plan input capsule')
        require(body['request_hash']==digest(body['request']) and body['payload_hash']==digest(body['payload']),
            'Retained plan inputs differ')
        require(body['bootstrap_sha256']==hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),
            'Retained plan bootstrap is incompatible with this host')
        if body['runtime_identity']!=_runtime_identity():
            raise Conflict('Retained plan Python runtime differs; no silent runtime substitution')
        files=body['source_files']
        require(type(files) is dict and 1<=len(files)<=128
            and all(re.fullmatch(r'trading_researcher/[A-Za-z_][A-Za-z0-9_]*\.py',name) for name in files),
            'Invalid retained plan source paths')
        require({'trading_researcher/__init__.py','trading_researcher/evaluation_plans.py',
            'trading_researcher/evaluation_policy.py'}<=set(files),'Incomplete retained plan source')
        require(all(type(item) is dict and set(item)=={'sha256','size'} and type(item['size']) is int
            and 0<=item['size']<=16*1024*1024 for item in files.values())
            and sum(item['size'] for item in files.values())<=16*1024*1024,'Invalid retained source envelope')
        require(set(capsule['blob_refs'])=={item['sha256'] for item in files.values()},
            'Retained source references differ')
        bundle={}
        for name,item in files.items():
            raw=self._read_blob_bytes(item['sha256'])
            require(len(raw)==item['size'],'Retained source size differs')
            bundle[name]=raw
        require(footprint(bundle)==body['source_footprint'],'Retained source footprint differs')
        return bundle

    def _retain_plan_attempt(self,request,payload,refs,exposure,source,capsule,meaning=None):
        # The caller holds the broker mutex. No child may run until the capsule,
        # committed blob references and STARTED event commit together.
        attempt=uuid.uuid4().hex
        files=None if capsule is not None else {name:self._stage_blob_bytes(raw) for name,raw in source.items()}
        with self._transaction():
            if capsule is None:
                for descriptor in files.values():self._register_blob(descriptor)
                capsule=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':'development','source_refs':refs,'exposure':exposure,
                    'blob_refs':sorted({item['sha256'] for item in files.values()}),
                    'authority':'retained_preparation_input_not_scientific_admission',
                    'body':{'schema':INPUT_SCHEMA,'created_at':self._now(),'request':request,'request_hash':digest(request),
                        'payload':payload,'payload_hash':digest(payload),'source_files':files,'source_footprint':footprint(source),
                        'bootstrap_sha256':hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),
                        'runtime_identity':_runtime_identity(),'scientific_readiness':False,
                        'allocation_reserved':False,'frozen':False,
                        **({'meaning_review_at_preparation':meaning} if meaning is not None else {})}})
            self._event('controller','bound_computation_started',attempt_id=attempt,kind='evaluation_plan',
                input_ref=request['compiled_id'],retained_input_id=capsule['id'])
        return attempt,capsule

    def _existing_evaluation_plan(self,request):
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            envelope=decode(row['envelope'])
            body=envelope.get('body')
            if (envelope['creator']==envelope['origin']=='controller' and type(body) is dict
                    and body.get('schema')==SCHEMA and body['request']['key']==request['key']):
                if digest(body['request'])!=digest(request):raise Conflict('Plan key already binds a different request')
                return self._artifact(row['id'])
        return None

    def _plan_inputs(self,actor,request):
        compiled=self._artifact(request['compiled_id'])
        body=compiled['body']
        if (compiled['creator']!=compiled['origin'] or compiled['creator']!='controller'
                or type(body) is not dict or body.get('schema')!='compiled-hypothesis/1'
                or body.get('status')!='COMPILED'):
            raise Denied('Plan preparation requires an owned compiled hypothesis')
        snapshot=self._data_snapshot(body['data_snapshot_id'])
        if snapshot['data_class']!='development' or snapshot['body']['manifest']['partition']!='development':
            raise Denied('This preparation route accepts development bindings only')
        references=strings(request['dependence'].get('development_refs'),'development diagnostic references')
        if not 1<=len(references)<=16:raise Invalid('One through sixteen retained development diagnostics required')
        diagnostics=[]
        for identity in references:
            artifact=self._artifact(identity)
            value=artifact['body']
            if (artifact['creator']!=artifact['origin'] or artifact['creator']!='controller'
                    or artifact['data_class']!='development' or type(value) is not dict
                    or value.get('schema')!='reference-execution/1' or value.get('status')!='DESCRIPTIVE_EXECUTION'
                    or value.get('data_snapshot_id')!=snapshot['id']):
                raise Denied('Dependence references must be owned computations on this development snapshot')
            descriptor=value['result']['case_blob']
            require(artifact['blob_refs']==[descriptor['sha256']],'Diagnostic blob binding differs')
            try:
                actual,size,_=_hash_file(self._blob_path(descriptor['sha256']))
            except (OSError,Invalid) as exc:
                raise Conflict('Retained diagnostic cases unavailable') from exc
            require(actual==descriptor['sha256'] and type(descriptor['size']) is int and size==descriptor['size'],
                'Retained diagnostic cases differ from the committed result')
            diagnostics.append(artifact)
        args=body['dependency_arguments']
        dependencies=self._bound_dependencies(actor,*(args[name] for name in ('formalization_id','feature_certificate_id','reference_certificate_id')))
        definitions=self._artifact(dependencies['feature_certificate']['body']['definitions_id'])['body']['definitions']
        payload={'candidate':dependencies['formalization']['body']['candidate'],'definitions':definitions,
            'outcome_description':body['compilation']['programs']['outcome_program'],
            'primary_count':request['primary_count'],'dependence':request['dependence']}
        refs=sorted(set([compiled['id'],*references,*dependencies['refs']]))
        exposure=set(refs)|set(compiled['exposure'])|set(dependencies['exposure'])
        for artifact in diagnostics:exposure.update(artifact['exposure'])
        return payload,refs,sorted(exposure)

    def _plan_meaning_reference(self,request):
        assessment=self._artifact(text(request['meaning_review_id'],'meaning-review identity'))
        body=assessment['body']
        require(assessment['creator']==assessment['origin']=='controller' and type(body) is dict
            and body.get('schema')=='semantic-review-assessment/1'
            and self._db.execute('SELECT 1 FROM meaning_review_assessments WHERE artifact_id=?',
                (assessment['id'],)).fetchone() is not None,'Owned meaning-review assessment required')
        compiled=self._artifact(request['compiled_id'])
        binding=compiled['body']
        require(compiled['creator']==compiled['origin']=='controller' and type(binding) is dict
            and binding.get('schema')=='compiled-hypothesis/1' and binding.get('status')=='COMPILED',
            'Review must bind an owned compiled hypothesis')
        require(body['formalization_id']==binding['dependency_arguments']['formalization_id'],
            'Meaning review targets a different formalization')
        self._deny_final_calibration_ancestry(assessment)
        target,_=self._meaning_target(body['formalization_id'])
        required_definition=None
        # Equal feature names/types do not establish equal parameters or timing.
        # Literal-only candidates do not depend on unused feature definitions.
        if target['body']['candidate']['feature_refs']:
            certificate=self._artifact(binding['dependency_arguments']['feature_certificate_id'])
            certificate_body=certificate['body']
            require(certificate['creator']==certificate['origin']=='controller'
                and type(certificate_body) is dict and certificate_body.get('schema')=='feature-certificate/1',
                'Owned feature certificate required for meaning-review scope')
            required_definition=certificate_body['definitions_id']
            require(all(required_definition in job['spec']['research_inputs']['definition_ids']
                for job in body['inventory']['jobs']),
                'Meaning review did not use the compiled feature-definition identity')
        return assessment,required_definition

    def _plan_meaning_evidence(self,actor,request):
        if 'meaning_review_id' not in request:return None,None
        assessment,required_definition=self._plan_meaning_reference(request)
        evidence={**self._inspect_meaning_review(actor,assessment['id']),
            'formalization_id':assessment['body']['formalization_id'],
            'required_definition_id':required_definition}
        return evidence,assessment

    def _reviewed_plan_inputs(self,actor,request):
        payload,refs,exposure=self._plan_inputs(actor,request)
        meaning,assessment=self._plan_meaning_evidence(actor,request)
        if assessment is not None:
            refs=sorted(set(refs)|{assessment['id'],*assessment['source_refs']})
            exposure=sorted(set(exposure)|set(refs)|set(assessment['exposure']))
        return payload,refs,exposure,meaning

    def _inspect_evaluation_plan(self,actor,plan_id):
        artifact=self._artifact(text(plan_id,'evaluation-plan identity'))
        body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and artifact['data_class']=='development'
            and type(body) is dict and body.get('schema')==SCHEMA,'Owned evaluation plan required')
        meaning,_=self._plan_meaning_evidence(actor,body['request'])
        gates=None if body['plan'] is None else list(body['plan']['remaining_gates'])
        if gates is not None and meaning is not None and meaning['independent_semantic_review']=='SATISFIED':
            gates=[gate for gate in gates if gate!='independent_semantic_review']
        return {'plan_id':plan_id,'status':body['status'],'gap':body['gap'],
            'meaning_review':meaning,'current_remaining_gates':gates,
            'scientific_readiness':False,'allocation_reserved':False,'frozen':False}

    def _prepare_evaluation_plan_external(self,token,args):
        with self._mutex:
            actor=self._binding_owner(token)
            required={'key','compiled_id','primary_count','dependence'}
            require(required<=set(args)<=required|{'meaning_review_id'},'Missing or unexpected plan request fields')
            request=decode(canonical(args))
            text(request['key'],'plan request key')
            text(request['compiled_id'],'compiled identity')
            if 'meaning_review_id' in request:text(request['meaning_review_id'],'meaning-review identity')
            integer(request['primary_count'],'primary count',1)
            require(request['primary_count']<=8 and type(request['dependence']) is dict,
                'A bounded family and explicit dependence design are required')
            existing=self._existing_evaluation_plan(request)
            if existing is not None:return existing
            capsule=self._existing_plan_input(request)
            new_input=capsule is None
            payload,refs,exposure,meaning=self._reviewed_plan_inputs(actor,request)
            if capsule is not None:
                require(digest([payload,refs,exposure])==digest([capsule['body']['payload'],capsule['source_refs'],capsule['exposure']]),
                    'Retained plan dependencies differ; no silent input substitution')
                require(meaning==capsule['body'].get('meaning_review_at_preparation'),
                    'Retained meaning-review inventory differs; use a new preparation key')
                source=self._load_plan_input_source(capsule)
            else:
                source=source_bundle()
                if footprint(source)!=LOADED_SOURCE:
                    raise Conflict('Plan source changed since process import; restart with the intended source version')
            attempt,capsule=self._retain_plan_attempt(request,payload,refs,exposure,source,capsule,meaning)
        try:
            # Consume the durable bytes, including on the first attempt. Staged
            # but uncommitted files never stand in for a retained input.
            with self._mutex:source=self._load_plan_input_source(capsule)
            calculated=run_plan_child(source,payload)
            result=calculated['result']
            require(type(result) is dict and set(result)=={'plan','gap'},'Malformed plan calculation')
            verified=run_plan_child(source,payload,verify_hash=digest(result))
            require(verified['result']=={'verified_result_hash':digest(result)},'Malformed plan verification')
            if result['plan'] is not None:
                require(result['gap'] is None and result['plan']['scientific_readiness'] is False,
                    'Plan preparation cannot issue scientific readiness')
            else:
                require(type(result['gap']) is dict and result['gap']['code']=='EVALUATION_GAP','Missing plan gap')
            source_files=capsule['body']['source_files']
            with self._transaction():
                actor=self._binding_owner(token)
                current=self._reviewed_plan_inputs(actor,request)
                require(digest(list(current))==digest([payload,refs,exposure,meaning]),'Plan dependencies changed before commitment')
                require(footprint(self._load_plan_input_source(capsule))==footprint(source),
                    'Retained source changed before commitment')
                if new_input and footprint(source_bundle())!=LOADED_SOURCE:
                    raise Conflict('Plan source changed before commitment')
                require(_environment_current(calculated['environment']) and _environment_current(verified['environment']),
                    'Plan runtime changed before commitment')
                existing=self._existing_evaluation_plan(request)
                if existing is not None:
                    require(existing['body'].get('input_capsule_id')==capsule['id']
                        and digest({'plan':existing['body']['plan'],'gap':existing['body']['gap']})==digest(result),
                        'Concurrent completed plan contradicts this retained calculation')
                    self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=existing['id'],status='REUSED')
                    return existing
                saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':'development','source_refs':sorted(set(refs)|{capsule['id']}),
                    'exposure':sorted(set(exposure)|{capsule['id']}),
                    'blob_refs':sorted({descriptor['sha256'] for descriptor in source_files.values()}),
                    'authority':'plan_preparation_not_scientific_admission',
                    'body':{'schema':SCHEMA,'created_at':self._now(),'request':request,
                        'status':'POLICY_DRAFT' if result['gap'] is None else 'EVALUATION_GAP',
                        'plan':result['plan'],'gap':result['gap'],'attempt_id':attempt,'input_capsule_id':capsule['id'],
                        'source_files':source_files,'source_footprint':footprint(source),
                        'calculation_environment':calculated['environment'],'verification':verified,
                        'family_count_authority':'declared_preparation_only_recompute_from_frozen_batch',
                        'scientific_readiness':False,'allocation_reserved':False,'frozen':False,
                        **({'meaning_review_at_preparation':meaning} if meaning is not None else {}),
                        'qualification':'Preparation retains assigned pilot policy and pending gates; no protected execution or result publication permission.'}})
                self._event('controller','evaluation_plan_prepared',artifact_id=saved['id'],request_key=request['key'],status=saved['body']['status'])
                self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=saved['id'],status=saved['body']['status'])
                canonical(saved)
                return saved
        except BaseException:
            with self._transaction():
                self._event('controller','bound_computation_interrupted',attempt_id=attempt,reason='plan_preparation_failed_or_cancelled')
            raise
