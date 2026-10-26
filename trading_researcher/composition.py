"""D084 conformance of an exact composition of certified reference primitives."""
import hashlib
from pathlib import Path
import sys
import tempfile
import uuid

from .binding import PACKAGE_FILES, compile_payload, environment, hashes, require, write_file
from .certification import _environment_current, _runtime_identity
from .codec import Invalid, canonical, decode, digest, text
from .errors import Conflict, Denied


ROOT=Path(__file__).resolve().parents[1]
PROFILE='certified-reference-composition/1'
SCHEMA='composition-certificate/1'
AUTHORITY='implementation_composition_conformance_only'
DRIVER='trading_researcher/composition.py'
FIXTURE='tests/fixtures/composition_conformance_cases.json'
FIXTURE_SHA256='b28025c09fb9292998328fc698aa06f2ab0275ced8a74d0370d38437551baa64'
FILES=(*PACKAGE_FILES,DRIVER,FIXTURE)
LOADED_SELF=hashlib.sha256((ROOT/DRIVER).read_bytes()).hexdigest()
BOOTSTRAP=('import sys;sys.path.insert(0,sys.argv[1]);'
    'from trading_researcher.composition import child_entry;child_entry(sys.argv[2])')


def fixed_checks():
    from .expressions import ExpressionGap
    raw=(ROOT/FIXTURE).read_bytes()
    require(hashlib.sha256(raw).hexdigest()==FIXTURE_SHA256,'Independent composition expectations changed')
    fixed=decode(raw);passed=[]
    for case in fixed['cases']:
        try:actual=compile_payload(case['payload'])
        except (Invalid,ExpressionGap) as exc:
            expected=case.get('error')
            require(expected is not None and type(exc).__name__==expected['type'],case['name'])
            if 'code' in expected:require(getattr(exc,'code',None)==expected['code'],case['name'])
        else:
            require('error' not in case and case.get('expected'),case['name'])
            require(actual==case['expected'],case['name']+': exact compilation differs')
        passed.append(case['name'])
    require(passed and len(set(passed))==len(passed),'Unique fixed cases required')
    return {'fixture_sha256':FIXTURE_SHA256,'passed_cases':passed}


def child_entry(request_path):
    request=decode(Path(request_path).read_bytes());expected=request['footprint']
    require(set(expected)==set(FILES))
    require(hashes({name:(ROOT/name).read_bytes() for name in FILES})==expected)
    environment(expected)
    checks=fixed_checks()
    compilation=compile_payload(request['payload'])
    require(digest(compilation)==request['compilation_hash'],'Candidate compilation differs from retained binding')
    result={'checks':checks,'compilation_hash':digest(compilation),'candidate_hash':compilation['candidate_hash'],
        'profile':PROFILE,'scientific_readiness':False}
    require(hashes({name:(ROOT/name).read_bytes() for name in FILES})==expected)
    print(canonical({'result':result,'request_hash':digest(request),'footprint':expected,
        'environment':environment(expected)}),flush=True)


def run_composition_child(bundle,payload,compilation_hash):
    from .binance_normalize import _run_child
    expected=hashes(bundle)
    request={'payload':payload,'compilation_hash':compilation_hash,'footprint':expected}
    with tempfile.TemporaryDirectory(prefix='trf-composition-') as temporary:
        directory=Path(temporary)
        for name,raw in bundle.items():
            path=directory/name;path.parent.mkdir(parents=True,exist_ok=True);write_file(path,raw)
        write_file(directory/'request.json',canonical(request).encode())
        report=_run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],directory)
        require(type(report) is dict and set(report)=={'result','request_hash','footprint','environment'})
        require(report['request_hash']==digest(request) and report['footprint']==expected
            and _environment_current(report['environment']))
        require(hashes({name:(directory/name).read_bytes() for name in bundle})==expected)
        return report


class CompositionCertification:
    def _composition_inputs(self,actor,compiled_id):
        compiled=self._artifact(text(compiled_id,'compiled identity'));body=compiled['body']
        require(compiled['creator']==compiled['origin']=='controller' and type(body) is dict
            and body.get('schema')=='compiled-hypothesis/1' and body.get('status')=='COMPILED',
            'An owned successful compilation is required')
        self._require_usable_dependencies(compiled_id)
        args=body['dependency_arguments']
        deps=self._bound_request_dependencies(actor,args)
        payload={'formalization_id':args['formalization_id'],'candidate':deps['formalization']['body']['candidate'],
            'catalog':deps['catalog'],'data_manifest':deps['snapshot']['body']['manifest'],
            'as_of':args['as_of'],'max_steps':args['max_steps']}
        require(payload==body['compilation_input'],'Compilation no longer matches its exact dependencies')
        bundle=self._load_binding_package(body['source_package_id'])
        require(all(bundle[name]==raw for name,raw in deps['reference_bundle'].items()),
            'Binding package differs from certified reference primitives')
        require(_environment_current(body['environment']),'Compiled runtime no longer matches')
        return compiled,bundle

    def _load_composition_package(self,identity):
        artifact=self._artifact(identity);body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and type(body) is dict
            and body.get('schema')=='composition-source-package/1' and body.get('profile')==PROFILE,
            'Owned composition source required')
        self._require_usable_dependencies(identity)
        require(set(body['files'])==set(FILES) and body['bootstrap_sha256']==hashlib.sha256(BOOTSTRAP.encode()).hexdigest())
        bundle={}
        for name,descriptor in body['files'].items():
            raw=self._read_blob_bytes(descriptor['sha256'])
            require(len(raw)==descriptor['size']);bundle[name]=raw
        require(hashes(bundle)==body['footprint'] and sum(map(len,bundle.values()))<=16*1024*1024)
        require(set(artifact['blob_refs'])=={d['sha256'] for d in body['files'].values()})
        return bundle

    def _certify_composition_external(self,token,args):
        with self._mutex:
            actor=self._binding_owner(token)
            require(set(args)=={'compiled_id'},'Exact compiled identity required')
            compiled,bundle=self._composition_inputs(actor,args['compiled_id'])
            bundle={**bundle,DRIVER:(ROOT/DRIVER).read_bytes(),FIXTURE:(ROOT/FIXTURE).read_bytes()}
            require(hashes(bundle)[DRIVER]==LOADED_SELF,'Restart after validator source changes')
            require(hashes(bundle)[FIXTURE]==FIXTURE_SHA256,'Independent expectations changed')
            files={name:self._stage_blob_bytes(raw) for name,raw in bundle.items()}
            attempt=uuid.uuid4().hex
            with self._transaction():
                for item in files.values():self._register_blob(item)
                package=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':'operations','source_refs':[],'exposure':[],
                    'blob_refs':sorted({d['sha256'] for d in files.values()}),'authority':'retained_source_not_certified',
                    'body':{'schema':'composition-source-package/1','profile':PROFILE,'created_at':self._now(),
                        'files':files,'footprint':hashes(bundle),'bootstrap_sha256':hashlib.sha256(BOOTSTRAP.encode()).hexdigest()}})
                refs=sorted({compiled['id'],package['id'],*compiled['source_refs']})
                capsule=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                    'data_class':compiled['data_class'],'source_refs':refs,'exposure':sorted(set(refs)|set(compiled['exposure'])),
                    'authority':'retained_composition_input_not_certification',
                    'body':{'schema':'composition-input/1','created_at':self._now(),'compiled_id':compiled['id'],
                        'source_package_id':package['id'],'compilation_hash':digest(compiled['body']['compilation']),
                        'runtime_identity':_runtime_identity(),'scientific_readiness':False}})
                self._event('controller','bound_computation_started',attempt_id=attempt,kind='composition',
                    input_ref=compiled['id'],retained_input_id=capsule['id'])
        report=None;failure=None
        try:
            with self._mutex:bundle=self._load_composition_package(package['id'])
            report=run_composition_child(bundle,compiled['body']['compilation_input'],capsule['body']['compilation_hash'])
            fixed=decode(bundle[FIXTURE]);expected={'fixture_sha256':FIXTURE_SHA256,'passed_cases':[c['name'] for c in fixed['cases']]}
            require(report['result']=={'checks':expected,'compilation_hash':capsule['body']['compilation_hash'],
                'candidate_hash':digest(compiled['body']['compilation_input']['candidate']),
                'profile':PROFILE,'scientific_readiness':False},'Malformed composition report')
        except Exception as exc:failure=type(exc).__name__
        except BaseException:
            self._bound_interrupted(attempt);raise
        with self._transaction():
            actor=self._binding_owner(token)
            if failure is None:
                try:
                    current,_=self._composition_inputs(actor,compiled['id'])
                    require(current==compiled and hashes(self._load_composition_package(package['id']))==hashes(bundle))
                    require((ROOT/DRIVER).read_bytes()==bundle[DRIVER] and (ROOT/FIXTURE).read_bytes()==bundle[FIXTURE]
                        and _environment_current(report['environment']))
                except (Invalid,Denied,Conflict,OSError,ValueError,TypeError) as exc:failure=type(exc).__name__
            refs=sorted({capsule['id'],*capsule['source_refs']})
            saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':compiled['data_class'],'source_refs':refs,'exposure':sorted(set(refs)|set(capsule['exposure'])),
                'authority':AUTHORITY,'body':{'schema':SCHEMA,'profile':PROFILE,'created_at':self._now(),
                    'compiled_id':compiled['id'],'input_capsule_id':capsule['id'],'source_package_id':package['id'],
                    'status':'CONFORMANT' if failure is None else 'CERTIFICATION_GAP','failure_type':failure,
                    'report':report,'attempt_id':attempt,'scientific_readiness':False}})
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=saved['id'],status=saved['body']['status'])
            canonical(saved);return saved

    def _composition_certificate_status(self,actor,certificate_id,compiled_id=None):
        artifact=self._artifact(text(certificate_id,'composition certificate'));body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and artifact['authority']==AUTHORITY
            and type(body) is dict and body.get('schema')==SCHEMA and body.get('profile')==PROFILE,
            'Owned composition certificate required')
        if compiled_id is not None:require(body['compiled_id']==compiled_id,'Composition targets another compiled hypothesis')
        status=body['status']
        try:
            self._require_usable_dependencies(certificate_id)
            if status=='CONFORMANT':
                self._composition_inputs(actor,body['compiled_id'])
                bundle=self._load_composition_package(body['source_package_id'])
                require(_environment_current(body['report']['environment']))
                installed=hashes({name:(ROOT/name).read_bytes() for name in (DRIVER,FIXTURE)})
                if (hashes(bundle)[DRIVER]!=LOADED_SELF or hashes(bundle)[FIXTURE]!=FIXTURE_SHA256
                        or installed[DRIVER]!=LOADED_SELF or installed[FIXTURE]!=FIXTURE_SHA256):
                    status='STALE_VALIDATOR'
        except Denied:status='INVALIDATED_BY_DEPENDENCY'
        except (Invalid,Conflict,OSError,KeyError,TypeError,ValueError):status='QUARANTINED'
        return {'certificate_id':certificate_id,'compiled_id':body['compiled_id'],'status':status,
            'composition_conformance':'SATISFIED' if status=='CONFORMANT' else 'NOT_SATISFIED','scientific_readiness':False}
