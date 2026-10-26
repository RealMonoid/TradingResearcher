"""Retained reference computations; compilation is not scientific freeze or semantic approval."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile
import uuid

from .codec import Invalid, canonical, decode, digest, integer, text
from .errors import Conflict, Denied
from .certification import FILES, _runtime_identity, _runtime_path_allowed, _environment_current


ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'bound-reference/1'
DRIVER = 'trading_researcher/binding.py'
PACKAGE_FILES = (*FILES, DRIVER)
BOOTSTRAP = ('import sys;sys.path.insert(0,sys.argv[1]);'
    'from trading_researcher.binding import child_entry;child_entry(sys.argv[2])')
MAX_OUTPUT_BYTES = 512*1024*1024
AUTHORITY = 'descriptive_reference_computation_only'


def hashes(bundle):
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(bundle.items())}


def require(condition, message='Bound reference input or result differs from its committed contract'):
    if not condition:
        raise Invalid(message)


def write_file(path, raw):
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def environment(expected):
    libraries = {}
    base = Path(sys.base_prefix).resolve()
    isolation = {'isolated':sys.flags.isolated, 'no_site':sys.flags.no_site,
        'ignore_environment':sys.flags.ignore_environment, 'no_bytecode_writes':int(sys.dont_write_bytecode)}
    require(isolation == {'isolated':1,'no_site':1,'ignore_environment':1,'no_bytecode_writes':1})
    for name, module in tuple(sys.modules.items()):
        source = getattr(module, '__file__', None)
        if not source:
            continue
        source = Path(source).resolve()
        if source.is_relative_to(ROOT) and source.relative_to(ROOT).as_posix() in expected:
            require(hashlib.sha256(source.read_bytes()).hexdigest() == expected[source.relative_to(ROOT).as_posix()])
        elif _runtime_path_allowed(source) and name.split('.')[0] in sys.stdlib_module_names:
            libraries[source.relative_to(base).as_posix()] = hashlib.sha256(source.read_bytes()).hexdigest()
        else:
            raise Invalid('Bound computation imported a module outside its retained closure')
    return {'identity':_runtime_identity(),'standard_library':dict(sorted(libraries.items())),'isolation':isolation}


def expected_request(payload):
    candidate = payload['candidate']
    universe = candidate['test_universe']
    return {'schema':'reference-case-request/1','candidate_ref':payload['formalization_id'],
        'data_snapshot_ref':universe['data_snapshot_ref'],'scope_program':candidate['scope_ast'],
        'condition_program':candidate['condition_ast'],'outcome_program':candidate['outcome']['program'],
        'outcome_scale':candidate['outcome']['scale'],'horizon_bars':candidate['horizons']['outcome_bars'],
        'universe':{key:universe[key] for key in ('start','end','instruments')},
        'as_of':payload['as_of'],'max_steps':payload['max_steps']}


def validate_compilation(result, payload):
    """Host transport/identity bounds only; AST semantics belong to the retained child."""
    require(type(result) is dict and set(result) == {'request','candidate_hash','programs','feature_refs',
        'row_window','warmup_seconds','unavailable_warmup_seconds','maximum_input_rows',
        'expected_case_count','outcome_unit','scientific_readiness'})
    request = expected_request(payload)
    require(digest(result['request']) == digest(request) and result['candidate_hash'] == digest(payload['candidate'])
        and result['scientific_readiness'] is False)
    instant = lambda value:int(datetime.fromisoformat(value).timestamp())
    start,end = (instant(request['universe'][key]) for key in ('start','end'))
    data_start,data_end = (instant(payload['data_manifest']['universe'][key]) for key in ('start','end'))
    require(data_start <= start < end <= data_end and start%900 == end%900 == 0)
    for key in ('warmup_seconds','unavailable_warmup_seconds','maximum_input_rows','expected_case_count'):
        integer(result[key],key,0)
    require(result['warmup_seconds']%900 == 0)
    row_start = max(data_start,start-result['warmup_seconds'])
    stamp = datetime.fromtimestamp(row_start,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    instruments = sorted(request['universe']['instruments'])
    require(digest(result['row_window']) == digest({'start':stamp,'end':request['universe']['end'],'instruments':instruments}))
    require(result['unavailable_warmup_seconds'] == max(0,data_start-(start-result['warmup_seconds']))
        and result['maximum_input_rows'] == ((end-row_start)//900)*len(instruments)
        and 1 <= result['maximum_input_rows'] <= 100000
        and result['expected_case_count'] == ((end-start)//900)*len(instruments))
    require(result['feature_refs'] == sorted(payload['candidate']['feature_refs'])
        and result['outcome_unit'] == payload['candidate']['estimand']['unit'])
    programs = result['programs']
    require(type(programs) is dict and set(programs) == {'scope_program','condition_program','outcome_program'})
    for item in programs.values():
        require(type(item) is dict and set(item) == {'type','unit','feature_refs','parameter_paths'}
            and type(item['feature_refs']) is list and type(item['parameter_paths']) is list)
    require(programs['scope_program']['type'] == programs['condition_program']['type'] == 'boolean'
        and programs['outcome_program']['type'] == ('boolean' if request['outcome_scale'] == 'binary_probability' else 'real'))
    require(sorted({ref for item in programs.values() for ref in item['feature_refs']}) == result['feature_refs'])


def compile_payload(payload):
    """Compile exact existing AST semantics; never infer a natural-language meaning."""
    from .expressions import ReferenceEngine
    from .outcomes import _validate, _instant, _lookback
    require(type(payload) is dict and set(payload) == {'formalization_id','candidate','catalog','data_manifest','as_of','max_steps'})
    candidate = payload['candidate']
    request = expected_request(payload)
    start,end,as_of,_,count,instruments = _validate(request)
    require(start%900 == 0 and end%900 == 0, 'The bound data loader needs an exact 900-second universe')
    manifest = payload['data_manifest']
    data_start,data_end = (_instant(manifest['universe'][key]) for key in ('start','end'))
    require(data_start <= start < end <= data_end and set(instruments) <= set(manifest['universe']['instruments']))
    engine = ReferenceEngine(payload['catalog'], [{'time':start,'instrument':instruments[0],'features':{}}])
    programs = {key:engine.describe(request[key]) for key in ('scope_program','condition_program','outcome_program')}
    require(programs['scope_program']['type'] == programs['condition_program']['type'] == 'boolean')
    expected_type = 'boolean' if request['outcome_scale'] == 'binary_probability' else 'real'
    require(programs['outcome_program']['type'] == expected_type)
    outcome_unit = 'ratio' if expected_type == 'boolean' else programs['outcome_program']['unit']
    require(candidate['estimand']['unit'] == outcome_unit)
    refs = sorted({ref for item in programs.values() for ref in item['feature_refs']})
    require(refs == sorted(candidate['feature_refs']))
    decision_lookback = max(_lookback(engine._program_node(request[key])) for key in ('scope_program','condition_program'))
    outcome_lookback = _lookback(engine._program_node(request['outcome_program']))
    lookback = max(decision_lookback,max(0,outcome_lookback-request['horizon_bars']*900))
    row_start = max(data_start,start-lookback)
    maximum_rows = ((end-row_start)//900)*len(instruments)
    require(maximum_rows <= 100000, 'RESOURCE_GAP: required data plus warmup exceeds the reference row bound')
    stamp = lambda value:datetime.fromtimestamp(value,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return {'request':deepcopy(request),'candidate_hash':digest(candidate),'programs':programs,
        'feature_refs':refs,'row_window':{'start':stamp(row_start),'end':stamp(end),'instruments':instruments},
        'warmup_seconds':lookback,'unavailable_warmup_seconds':max(0,data_start-(start-lookback)),
        'maximum_input_rows':maximum_rows,'expected_case_count':count,'outcome_unit':outcome_unit,
        'scientific_readiness':False}


def _compute(payload, directory):
    from .outcomes import materialize_reference
    require(type(payload) is dict and set(payload) == {'compilation_input','compilation_hash','rows'})
    compiled = compile_payload(payload['compilation_input'])
    require(digest(compiled) == payload['compilation_hash'])
    checksum,size,rows = hashlib.sha256(),0,[]
    with (Path(directory)/'rows.jsonl').open('rb') as stream:
        while line := stream.readline(1048577):
            size += len(line)
            require(len(line) <= 1048576 and size <= MAX_OUTPUT_BYTES and len(rows) < compiled['maximum_input_rows'])
            checksum.update(line)
            rows.append(decode(line))
    require(digest({'sha256':checksum.hexdigest(),'size':size}) == digest(payload['rows']))
    return materialize_reference(compiled['request'],payload['compilation_input']['catalog'],rows)


def _execute(payload, directory):
    from .outcomes import reference_contrast
    report = _compute(payload,directory)
    contrast = reference_contrast(report)
    output,checksum,size = Path(directory)/'cases.jsonl',hashlib.sha256(),0
    with output.open('xb') as stream:
        for case in report['cases']:
            raw = (canonical(case)+'\n').encode()
            size += len(raw)
            require(size <= MAX_OUTPUT_BYTES, 'Reference cases exceed their output resource envelope')
            checksum.update(raw)
            stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'report':{key:value for key,value in report.items() if key != 'cases'},'contrast':contrast,
        'case_blob':{'sha256':checksum.hexdigest(),'size':size},'rows':payload['rows'],
        'compilation_hash':payload['compilation_hash'],'scientific_readiness':False}


def _verify_execution(payload, directory):
    """Exact replay of already selected immutable rows; no extra data permission."""
    from .outcomes import reference_contrast
    require(type(payload) is dict and set(payload) == {'execution_input','result'})
    result,execution = payload['result'],payload['execution_input']
    require(type(result) is dict and set(result) == {'report','contrast','case_blob','rows','compilation_hash','scientific_readiness'})
    require(result['compilation_hash'] == execution['compilation_hash'] and result['scientific_readiness'] is False
        and digest(result['rows']) == digest(execution['rows']))
    report = _compute(execution,directory)
    require(digest(result['report']) == digest({key:value for key,value in report.items() if key != 'cases'}))
    require(digest(result['contrast']) == digest(reference_contrast(report)))
    checksum,size = hashlib.sha256(),0
    with (Path(directory)/'cases.jsonl').open('rb') as stream:
        for case in report['cases']:
            expected = (canonical(case)+'\n').encode()
            require(stream.read(len(expected)) == expected,'Returned case differs from exact retained replay')
            size += len(expected)
            require(size <= MAX_OUTPUT_BYTES)
            checksum.update(expected)
        require(stream.read(1) == b'','Returned cases contain an unexpected suffix')
    require(digest(result['case_blob']) == digest({'sha256':checksum.hexdigest(),'size':size}))
    return {'schema':'bound-case-verification/1','result_hash':digest(result),
        'compilation_hash':execution['compilation_hash'],'case_blob':result['case_blob'],
        'checked_cases':len(report['cases']),'scientific_readiness':False}


def child_entry(request_path):
    request = decode(Path(request_path).read_bytes())
    expected = request['footprint']
    require(set(expected) == set(PACKAGE_FILES))
    require(hashes({name:(ROOT/name).read_bytes() for name in expected}) == expected)
    require(not list((ROOT/'trading_researcher').glob('**/*.pyc')))
    environment(expected)
    if request['mode'] == 'compile':
        result = compile_payload(request['payload'])
    elif request['mode'] == 'execute':
        result = _execute(request['payload'],Path(request_path).parent)
    elif request['mode'] == 'verify':
        result = _verify_execution(request['payload'],Path(request_path).parent)
    else:
        raise Invalid('Unknown bound computation operation')
    require(hashes({name:(ROOT/name).read_bytes() for name in expected}) == expected)
    print(canonical({'mode':request['mode'],'result':result,'footprint':expected,
        'request_hash':digest(request['payload']),'environment':environment(expected)}),flush=True)


def run_child(bundle, mode, payload, directory):
    from .binance_normalize import _run_child
    directory = Path(directory)
    expected = hashes(bundle)
    for name, raw in bundle.items():
        path = directory/name
        path.parent.mkdir(parents=True,exist_ok=True)
        write_file(path,raw)
    request = {'mode':mode,'payload':payload,'footprint':expected}
    write_file(directory/'request.json',canonical(request).encode())
    report = _run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],directory)
    require(type(report) is dict and set(report) == {'mode','result','footprint','request_hash','environment'})
    require(report['mode'] == mode and report['request_hash'] == digest(payload)
        and report['footprint'] == expected and _environment_current(report['environment']))
    require(hashes({name:(directory/name).read_bytes() for name in bundle}) == expected)
    return report


class BoundComputation:
    def _binding_owner(self, token):
        actor = self._principal(token)
        if actor['role'] != 'operator':
            raise Denied('Compilation and bound computation require the host operator')
        return actor

    def _bound_dependencies(self, actor, formalization_id, feature_certificate_id, reference_certificate_id):
        from .certification import _pins_match, EXPECTED_CHECKS
        record = self._artifact(text(formalization_id,'formalization identity'))
        require(record['origin'] == 'worker' and type(record['body']) is dict
            and record['body'].get('schema') == 'formalization-record/1', 'A retained formalization is required')
        job = self._job(record['job_id'])
        require(job['state'] == 'completed' and job['result_id'] == formalization_id
            and job['spec']['kind'] == 'formalization/v1','Formalization must be the accepted completed job result')
        sources = {ref:self._artifact(ref) for ref in record['source_refs']}
        original = record['body']
        require(original['scientific_readiness'] is False and original['authorization_snapshot'] == sorted(sources)
            and original['idea_id'] in sources and original['catalog_id'] in sources)
        require(digest(original['original_idea']) == digest(sources[original['idea_id']]['body'])
            and original['candidate']['idea_ref'] == original['idea_id'])
        require(record['body']['assessment']['status'] == 'STRUCTURE_CHECKED','The formalization retains an unresolved gap')
        candidate = record['body']['candidate']
        snapshot = self._data_snapshot(candidate['test_universe']['data_snapshot_ref'])
        require(snapshot['id'] in sources)
        require(record['body']['catalog_id'] == snapshot['body']['catalog_id'],'Formalization and data catalog identities differ')
        catalog = self._artifact(snapshot['body']['catalog_id'])['body']['features']
        require(digest(catalog) == snapshot['body']['catalog_hash'])
        feature = self._artifact(text(feature_certificate_id,'feature certificate identity'))
        status = self._feature_certificate_status(actor,feature_certificate_id,data_snapshot_id=snapshot['id'])
        require(status['status'] in ('CURRENT','STALE'),'The exact raw measurement certificate is not intact')
        definitions = self._artifact(feature['body']['definitions_id'])['body']['definitions']
        require(digest({item['feature_ref']:{'type':item['type'],'unit':item['unit']} for item in definitions}) == digest(catalog))
        reference = self._artifact(text(reference_certificate_id,'reference certificate identity'))
        status = self._reference_certificate_status(actor,reference_certificate_id)
        require(status['status'] in ('CURRENT','STALE') and status['retained_source_status'] == 'VERIFIED')
        refbody = reference['body']
        reference_bundle = self._load_reference_package(refbody['source_package_id'])
        require(hashes(reference_bundle) == refbody['footprint'] and _pins_match(refbody['footprint'])
            and digest(refbody['checks']) == digest(EXPECTED_CHECKS) and _environment_current(refbody['environment']),
            'The retained calculator needs its exact compatible certified runtime')
        identities = [formalization_id,feature_certificate_id,reference_certificate_id,snapshot['id'],snapshot['body']['catalog_id']]
        exposure = set(identities)
        for identity in identities:
            exposure.update(self._artifact(identity)['exposure'])
        return {'formalization':record,'snapshot':snapshot,'catalog':catalog,
            'feature_certificate':feature,'reference_certificate':reference,
            'reference_bundle':reference_bundle,'refs':sorted(identities),'exposure':sorted(exposure)}

    def _retain_binding_package(self, bundle):
        require(set(bundle) == set(PACKAGE_FILES) and sum(map(len,bundle.values())) <= 16*1024*1024)
        files = {name:self._stage_blob_bytes(raw) for name,raw in sorted(bundle.items())}
        with self._transaction():
            for descriptor in files.values():self._register_blob(descriptor)
            artifact = self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'operations','source_refs':[],'exposure':[],
                'blob_refs':sorted({descriptor['sha256'] for descriptor in files.values()}),
                'authority':'retained_source_not_certified','body':{'schema':'binding-source-package/1',
                    'profile':PROFILE,'created_at':self._now(),'files':files,'footprint':hashes(bundle),
                    'bootstrap_sha256':hashlib.sha256(BOOTSTRAP.encode()).hexdigest()}})
            self._event('controller','binding_source_retained',artifact_id=artifact['id'])
            return artifact['id']

    def _load_binding_package(self, identity):
        artifact = self._artifact(identity)
        body = artifact['body']
        require(artifact['creator'] == artifact['origin'] == 'controller' and type(body) is dict
            and body.get('schema') == 'binding-source-package/1' and body.get('profile') == PROFILE
            and set(body['files']) == set(PACKAGE_FILES))
        self._require_usable_dependencies(identity)
        require(body['bootstrap_sha256'] == hashlib.sha256(BOOTSTRAP.encode()).hexdigest())
        bundle = {}
        for name,item in body['files'].items():
            raw = self._read_blob_bytes(item['sha256'])
            require(len(raw) == item['size'])
            bundle[name] = raw
        require(sum(map(len,bundle.values())) <= 16*1024*1024 and hashes(bundle) == body['footprint']
            and set(artifact['blob_refs']) == {item['sha256'] for item in body['files'].values()})
        return bundle

    def _bound_attempts(self):
        attempts = {}
        for row in self._db.execute('SELECT envelope FROM events ORDER BY seq'):
            event = decode(row[0])
            action,details = event['action'],event['details']
            identity = details.get('attempt_id')
            if event['actor'] != 'controller':continue
            if action == 'bound_computation_started':
                attempts[identity] = {'attempt_id':identity,'kind':details['kind'],'input_ref':details['input_ref'],
                    'state':'STARTED','started_at':event['time'],'ended_at':None,'artifact_id':None,
                    'retained_input_id':details.get('retained_input_id'),'reason':None}
            elif identity in attempts and action in ('bound_computation_checked','bound_computation_interrupted'):
                attempts[identity].update(state='COMPLETED' if action.endswith('_checked') else 'INTERRUPTED',
                    ended_at=event['time'],artifact_id=details.get('artifact_id'),reason=details.get('reason'))
        return list(attempts.values())

    def _recover_bound_computations(self):
        with self._transaction():
            for item in self._bound_attempts():
                if item['state'] == 'STARTED':
                    self._event('controller','bound_computation_interrupted',attempt_id=item['attempt_id'],reason='previous_writer_ended')

    def _inspect_bound_computations(self, actor, limit=50):
        integer(limit,'limit',1)
        require(limit <= 100)
        attempts = self._bound_attempts()
        return {'attempts':list(reversed(attempts[-limit:])),'total':len(attempts),
            'pending':sum(item['state'] == 'STARTED' for item in attempts),'scientific_authority':False}

    def _bound_start(self, kind, identity):
        attempt = uuid.uuid4().hex
        with self._transaction():
            self._event('controller','bound_computation_started',attempt_id=attempt,kind=kind,input_ref=identity)
        return attempt

    def _bound_interrupted(self, attempt):
        with self._transaction():
            self._event('controller','bound_computation_interrupted',attempt_id=attempt,reason='caller_cancelled')

    def _compile_hypothesis_external(self, token, args):
        with self._mutex:
            actor = self._binding_owner(token)
            require(set(args) == {'formalization_id','feature_certificate_id','reference_certificate_id','as_of','max_steps'})
            args = decode(canonical(args))
            from .outcomes import _instant
            require(_instant(args['as_of']) <= self._now(),'The computation as_of time cannot be in the future')
            integer(args['max_steps'],'primitive step budget',1)
            require(args['max_steps'] <= 10000000)
            dependencies = self._bound_dependencies(actor,*(args[key] for key in ('formalization_id','feature_certificate_id','reference_certificate_id')))
        payload = {'formalization_id':args['formalization_id'],'candidate':dependencies['formalization']['body']['candidate'],
            'catalog':dependencies['catalog'],'data_manifest':dependencies['snapshot']['body']['manifest'],
            'as_of':args['as_of'],'max_steps':args['max_steps']}
        bundle = {**dependencies['reference_bundle'],DRIVER:(ROOT/DRIVER).read_bytes()}
        package_id = self._retain_binding_package(bundle)
        attempt = self._bound_start('compile',args['formalization_id'])
        report,error = None,None
        try:
            with self._mutex:self._require_usable_dependencies(package_id)
            with tempfile.TemporaryDirectory(prefix='trf-bound-compile-') as temporary:
                report = run_child(bundle,'compile',payload,temporary)
            validate_compilation(report['result'],payload)
        except Exception as exc:
            error = type(exc).__name__
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            actor = self._binding_owner(token)
            if error is None:
                try:
                    current = self._bound_dependencies(actor,*(args[key] for key in ('formalization_id','feature_certificate_id','reference_certificate_id')))
                    require(current['refs'] == dependencies['refs'] and current['exposure'] == dependencies['exposure'])
                    require(hashes(self._load_binding_package(package_id)) == hashes(bundle)
                        and (ROOT/DRIVER).read_bytes() == bundle[DRIVER] and _environment_current(report['environment']))
                except (Invalid,Denied,Conflict,OSError,ValueError,TypeError) as exc:error = type(exc).__name__
            refs = [*dependencies['refs'],package_id]
            artifact = self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':dependencies['snapshot']['data_class'],'source_refs':refs,
                'exposure':sorted(set(refs+dependencies['exposure'])),'authority':AUTHORITY,
                'body':{'schema':'compiled-hypothesis/1','profile':PROFILE,'created_at':self._now(),
                    'status':'COMPILED' if error is None else 'COMPILATION_GAP','failure_type':error,
                    'attempt_id':attempt,'source_package_id':package_id,'dependency_arguments':args,
                    'data_snapshot_id':dependencies['snapshot']['id'],'compilation_input':payload,
                    'compilation':report['result'] if error is None else None,
                    'environment':report['environment'] if error is None else None,
                    'mapping_authority':'formalizer_assertion_not_independent_semantic_certification',
                    'scientific_readiness':False}})
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=artifact['id'],status=artifact['body']['status'])
            canonical(artifact)
            return artifact

    def _execute_development_external(self, token, args):
        with self._mutex:
            actor = self._binding_owner(token)
            require(set(args) == {'compiled_id'})
            compiled = self._artifact(text(args['compiled_id'],'compiled identity'))
            body = compiled['body']
            require(compiled['creator'] == compiled['origin'] == 'controller' and compiled.get('authority') == AUTHORITY
                and type(body) is dict and body.get('schema') == 'compiled-hypothesis/1' and body.get('status') == 'COMPILED')
            snapshot = self._data_snapshot(body['data_snapshot_id'])
            # This check must precede any certificate/blob/row loader.
            if snapshot['data_class'] != 'development' or snapshot['body']['manifest']['partition'] != 'development':
                raise Denied('Protected outcomes require a separately frozen scientific plan and allocation')
            self._require_usable_dependencies(compiled['id'])
            arguments = body['dependency_arguments']
            dependencies = self._bound_dependencies(actor,*(arguments[key] for key in ('formalization_id','feature_certificate_id','reference_certificate_id')))
            bundle = self._load_binding_package(body['source_package_id'])
            require(all(bundle[name] == raw for name,raw in dependencies['reference_bundle'].items()))
            require(_environment_current(body['environment']))
        attempt = self._bound_start('development_execution',compiled['id'])
        report,verification,descriptor,error = None,None,None,None
        try:
            selection = body['compilation']['row_window']
            loaded = self._load_reference_data(snapshot['id'],selection['start'],selection['end'],selection['instruments'])
            require(digest(loaded['catalog']) == digest(body['compilation_input']['catalog']))
            with tempfile.TemporaryDirectory(prefix='trf-bound-execute-') as temporary:
                directory = Path(temporary)
                checksum,size = hashlib.sha256(),0
                with (directory/'rows.jsonl').open('xb') as stream:
                    for row in loaded['rows']:
                        raw = (canonical(row)+'\n').encode()
                        size += len(raw)
                        require(size <= MAX_OUTPUT_BYTES)
                        checksum.update(raw)
                        stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                payload = {'compilation_input':body['compilation_input'],'compilation_hash':digest(body['compilation']),
                    'rows':{'sha256':checksum.hexdigest(),'size':size}}
                report = run_child(bundle,'execute',payload,directory)
                result = report['result']
                require(type(result) is dict and set(result) == {'report','contrast','case_blob','rows','compilation_hash','scientific_readiness'})
                require(result['scientific_readiness'] is False and digest(result['rows']) == digest(payload['rows'])
                    and result['compilation_hash'] == payload['compilation_hash']
                    and digest(result['report']['request']) == digest(body['compilation']['request'])
                    and result['report']['scientific_readiness'] is False and result['contrast']['scientific_readiness'] is False)
                with tempfile.TemporaryDirectory(prefix='trf-bound-verify-') as verification_directory:
                    shutil.copyfile(directory/'cases.jsonl',Path(verification_directory)/'cases.jsonl')
                    shutil.copyfile(directory/'rows.jsonl',Path(verification_directory)/'rows.jsonl')
                    verification = run_child(bundle,'verify',{'execution_input':payload,'result':result},verification_directory)
                require(digest(verification['result']) == digest({'schema':'bound-case-verification/1',
                    'result_hash':digest(result),'compilation_hash':payload['compilation_hash'],
                    'case_blob':result['case_blob'],'checked_cases':result['report']['processed_case_count'],
                    'scientific_readiness':False}))
                with (directory/'cases.jsonl').open('rb') as stream:descriptor = self._stage_blob_stream(stream)
                require(digest(descriptor) == digest(result['case_blob']))
        except Exception as exc:error = type(exc).__name__
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            actor = self._binding_owner(token)
            if error is None:
                try:
                    self._bound_dependencies(actor,*(arguments[key] for key in ('formalization_id','feature_certificate_id','reference_certificate_id')))
                    require(hashes(self._load_binding_package(body['source_package_id'])) == hashes(bundle))
                    require(_environment_current(report['environment']))
                    require(_environment_current(verification['environment']))
                except (Invalid,Denied,Conflict,OSError,ValueError,TypeError) as exc:error = type(exc).__name__
            if error is None:self._register_blob(descriptor)
            refs = sorted(set([compiled['id'],*compiled['source_refs']]))
            artifact = self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'development','source_refs':refs,'exposure':sorted(set(refs+compiled['exposure'])),
                'blob_refs':[descriptor['sha256']] if error is None else [],'authority':AUTHORITY,
                'body':{'schema':'reference-execution/1','profile':PROFILE,'created_at':self._now(),
                    'status':'DESCRIPTIVE_EXECUTION' if error is None else 'EXECUTION_GAP','failure_type':error,
                    'attempt_id':attempt,'compiled_id':compiled['id'],'data_snapshot_id':snapshot['id'],
                    'result':report['result'] if error is None else None,'environment':report['environment'] if error is None else None,
                    'verification':verification if error is None else None,
                    'case_format':'reference-cases-jsonl/1','scientific_readiness':False,
                    'qualification':'Exploratory development computation; no semantic approval, calibrated inference, scientific freeze or D087 event.'}})
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=artifact['id'],status=artifact['body']['status'])
            canonical(artifact)
            return artifact
