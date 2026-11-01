"""Owned AST4 metadata/composition/execution gates; no scientific authority."""
from pathlib import Path
import hashlib
import shutil
import tempfile
import time

from .binding import hashes, require
from .certification import _environment_current
from .codec import canonical, digest, integer, text
from .errors import Denied
from .exact_certification import ExactRuntimeBroker
from .exact_formalization import SCHEMA, validate_record
from .exact_meaning import ExactMeaning
from .exact_research import selected
from .features import binding as feature_binding
from .paired_computation import PairedComputation
from .storage import blob_identity
from . import exact_runtime as runtime, exact_composition as composition

ROOT=Path(__file__).resolve().parents[1]
AUTHORITY='exact_descriptive_development_only'
PROFILE='exact-descriptive-development/1'
HOST_FILES=('trading_researcher/exact_execution.py','trading_researcher/EXACT_EXECUTION.md',
            'trading_researcher/exact_composition.py','trading_researcher/exact_meaning.py',composition.TEST)
LOADED={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in HOST_FILES}
RESERVED=('exact-compilation-input/','exact-compiled-hypothesis/','exact-composition-source-package/',
          'exact-composition-certificate/','exact-execution-input/','exact-reference-execution/')


class ExactExecutionBroker(ExactMeaning,ExactRuntimeBroker):
    def _execution_sources(self):
        current={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in HOST_FILES}
        require(current==LOADED,'Exact execution sources changed; restart and independently requalify')
        composition.read_bundle()
        return {**super()._breakout_research_sources(),**current}

    def _breakout_research_sources(self):return self._execution_sources()

    def _add_source(self,actor,body,data_class,exposure=None):
        if type(body) is dict and str(body.get('schema','')).startswith(RESERVED):
            raise Denied('Exact computations require owned controller operations')
        return super()._add_source(actor,body,data_class,exposure)

    def _put_artifact(self,actor,lease,body,source_refs):
        if type(body) is dict and str(body.get('schema','')).startswith(RESERVED):
            raise Denied('Exact computations require owned controller operations')
        return super()._put_artifact(actor,lease,body,source_refs)

    def _exact_save(self,body,refs,*,blobs=(),data_class='development',authority=AUTHORITY):
        refs=sorted(set(refs));exposure=set(refs)
        for identity in refs:exposure.update(self._artifact(identity)['exposure'])
        return self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
            'data_class':data_class,'source_refs':refs,'exposure':sorted(exposure),'blob_refs':sorted(set(blobs)),
            'authority':authority,'body':body})

    def _exact_dependencies(self,formalization_id,feature_certificate_id):
        self._execution_sources()
        target=self._artifact(text(formalization_id,'formalization identity'))
        require(target['origin']=='worker' and type(target['body']) is dict and target['body'].get('schema')==SCHEMA,
                'Owned exact formalization required')
        job=self._job(target['job_id'])
        require(job['state']=='completed' and job['result_id']==formalization_id
            and job['spec']['kind']=='formalization/v1' and selected(job['spec']))
        validate_record(target['body'],[self._artifact(ref) for ref in target['source_refs']])
        require(target['body']['assessment']['status']=='STRUCTURE_CHECKED','Original meaning retains a structural gap')
        self._deny_final_calibration_ancestry(target)
        candidate=target['body']['candidate'];snapshot_id=candidate['test_universe']['data_snapshot_ref']
        require(snapshot_id in target['source_refs'],'Selected data was not authorized to the original formalizer')
        snapshot=self._artifact(snapshot_id);body=snapshot['body']
        # Must precede every certificate, source package and outcome-row loader.
        if (snapshot['data_class']!='development' or type(body) is not dict
                or body.get('schema')!='data-snapshot/1' or body.get('manifest',{}).get('partition')!='development'):
            raise Denied('Exact development cannot read protected outcomes')
        require(snapshot['creator']=='controller' and snapshot['origin']=='source'
            and body['catalog_id']==target['body']['catalog_id'])
        certificate=self._artifact(text(feature_certificate_id,'feature certificate'))
        inputs=job['spec']['research_inputs']
        require(inputs.get('feature_certificate_id')==certificate['id'] and certificate['id'] in target['source_refs'],
                'Original full packet must supply this exact feature evidence')
        require(self._feature_certificate_status(None,certificate['id'],data_snapshot_id=snapshot_id)['status']=='CURRENT',
                'Exact execution requires current raw certification')
        definition=self._artifact(certificate['body']['definitions_id'])
        require(definition['id'] in inputs['definition_ids'] and definition['id'] in target['source_refs'])
        catalog=self._artifact(body['catalog_id'])['body']['features']
        require(digest(catalog)==body['catalog_hash'] and digest(catalog)==digest({
            item['feature_ref']:{key:item[key] for key in ('type','unit')} for item in definition['body']['definitions']}))
        reference,bundle=self._require_exact_qualification()
        for identity in (snapshot_id,certificate['id'],definition['id'],reference['id']):
            self._require_usable_dependencies(identity)
        return {'formalization':target,'snapshot':snapshot,'feature_certificate':certificate,
            'definition':definition,'catalog':catalog,'reference':reference,'bundle':bundle,
            'refs':sorted({target['id'],snapshot_id,certificate['id'],definition['id'],body['catalog_id'],reference['id']})}

    def _exact_data_use(self,dependencies):
        # Reuse the unchanged approved development rights/exposure/availability
        # findings. This routine is scalar as well as paired; it reads no outcome.
        result=PairedComputation._paired_data_use(self,dependencies)
        return {**result,'schema':'exact-development-data-use/1'}

    def compile_exact(self,token,*,formalization_id,feature_certificate_id,as_of,max_steps=10000000):
        with self._mutex:
            self._binding_owner(token)
            dependencies=self._exact_dependencies(formalization_id,feature_certificate_id)
            from .outcomes import _instant
            require(_instant(as_of)<=self._now(),'Future as_of is unavailable')
            findings=self._exact_data_use(dependencies)
            require(findings['status']=='QUALIFIED','Qualified development data use is required')
            payload={'formalization_id':formalization_id,'candidate':dependencies['formalization']['body']['candidate'],
                'catalog':dependencies['catalog'],'data_manifest':dependencies['snapshot']['body']['manifest'],
                'as_of':as_of,'max_steps':max_steps}
            bundle=dependencies['bundle']
        with self._transaction():
            capsule=self._exact_save({'schema':'exact-compilation-input/1','created_at':self._now(),
                'input':payload,'input_sha256':digest(payload),'data_use':findings,
                'dependencies':{'data_snapshot_id':dependencies['snapshot']['id'],
                    'feature_certificate_id':feature_certificate_id,'reference_certificate_id':dependencies['reference']['id']},
                'scientific_readiness':False},dependencies['refs'])
        attempt=self._bound_start('exact_compile',capsule['id']);report=error=None
        try:
            with tempfile.TemporaryDirectory(prefix='trf-exact-compile-') as directory:
                report=runtime.run_child(bundle,'compile',payload,directory)
            require(canonical(report['result'])==canonical(runtime.compile_payload(payload)))
        except Exception as exc:error={'type':type(exc).__name__,'reason':str(exc)}
        except BaseException:self._bound_interrupted(attempt);raise
        with self._transaction():
            self._binding_owner(token)
            if error is None:
                try:
                    current=self._exact_dependencies(formalization_id,feature_certificate_id)
                    require(current['refs']==dependencies['refs'] and canonical(self._exact_data_use(current))==canonical(findings))
                except Exception as exc:error={'type':type(exc).__name__,'reason':str(exc)}
            record=self._exact_save({'schema':'exact-compiled-hypothesis/1','profile':PROFILE,'created_at':self._now(),
                'status':'COMPILED' if error is None else 'COMPILATION_GAP','attempt_id':attempt,'error':error,
                'input_id':capsule['id'],'formalization_id':formalization_id,'feature_certificate_id':feature_certificate_id,
                'reference_certificate_id':dependencies['reference']['id'],'data_snapshot_id':dependencies['snapshot']['id'],
                'source_package_id':dependencies['reference']['body']['source_package_id'],
                'compilation':report['result'] if error is None else None,'report':report,
                'environment':report['environment'] if report is not None else None,'scientific_readiness':False},[capsule['id'],*dependencies['refs']])
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=record['id'],status=record['body']['status'])
            return record

    def _exact_compiled(self,identity):
        artifact=self._artifact(text(identity,'exact compiled identity'));body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and artifact['authority']==AUTHORITY
            and type(body) is dict and body.get('schema')=='exact-compiled-hypothesis/1'
            and body.get('profile')==PROFILE and body.get('status')=='COMPILED' and body.get('scientific_readiness') is False)
        self._require_usable_dependencies(identity)
        dependencies=self._exact_dependencies(body['formalization_id'],body['feature_certificate_id'])
        require(dependencies['reference']['id']==body['reference_certificate_id']
            and dependencies['snapshot']['id']==body['data_snapshot_id']
            and dependencies['reference']['body']['source_package_id']==body['source_package_id']
            and _environment_current(body['environment']))
        capsule=self._artifact(body['input_id'])
        require(capsule['creator']==capsule['origin']=='controller' and capsule['authority']==AUTHORITY
            and capsule['body']['schema']=='exact-compilation-input/1')
        payload=capsule['body']['input']
        require(digest(payload)==capsule['body']['input_sha256']
            and canonical(capsule['body']['dependencies'])==canonical({'data_snapshot_id':body['data_snapshot_id'],
                'feature_certificate_id':body['feature_certificate_id'],'reference_certificate_id':body['reference_certificate_id']})
            and canonical(payload['candidate'])==canonical(dependencies['formalization']['body']['candidate'])
            and canonical(payload['catalog'])==canonical(dependencies['catalog'])
            and canonical(payload['data_manifest'])==canonical(dependencies['snapshot']['body']['manifest'])
            and canonical(runtime.compile_payload(payload))==canonical(body['compilation'])
            and canonical(self._exact_data_use(dependencies))==canonical(capsule['body']['data_use']))
        return artifact,dependencies,payload

    def _retain_exact_composition(self,bundle):
        require(set(bundle)==set(composition.FILES) and sum(map(len,bundle.values()))<=16*1024*1024)
        files={name:self._stage_blob_bytes(raw) for name,raw in sorted(bundle.items())}
        with self._transaction():
            for descriptor in files.values():self._register_blob(descriptor)
            return self._exact_save({'schema':'exact-composition-source-package/1','profile':composition.PROFILE,
                'created_at':self._now(),'files':files,'footprint':hashes(bundle),
                'bootstrap_sha256':hashlib.sha256(composition.BOOTSTRAP.encode()).hexdigest()},[],
                blobs=[descriptor['sha256'] for descriptor in files.values()],data_class='operations',authority='retained_source_not_certified')

    def _exact_composition_package(self,identity):
        item=self._artifact(text(identity,'exact composition source package'));body=item['body']
        require(item['creator']==item['origin']=='controller' and item['authority']=='retained_source_not_certified'
            and item['data_class']=='operations' and type(body) is dict
            and body.get('schema')=='exact-composition-source-package/1' and body.get('profile')==composition.PROFILE
            and type(body.get('files')) is dict and set(body['files'])==set(composition.FILES))
        self._require_usable_dependencies(identity)
        require(body.get('bootstrap_sha256')==hashlib.sha256(composition.BOOTSTRAP.encode()).hexdigest())
        for descriptor in body['files'].values():
            require(type(descriptor) is dict and set(descriptor)=={'sha256','size'})
            blob_identity(descriptor['sha256']);integer(descriptor['size'],'composition source byte size')
        require(sum(item['size'] for item in body['files'].values())<=16*1024*1024)
        bundle={}
        for name,descriptor in body['files'].items():
            row=self._db.execute('SELECT size FROM blobs WHERE sha256=?',(descriptor['sha256'],)).fetchone()
            require(row is not None and row['size']==descriptor['size'])
            bundle[name]=self._read_blob_bytes(descriptor['sha256']);require(len(bundle[name])==descriptor['size'])
        require(hashes(bundle)==body['footprint'] and set(item.get('blob_refs',[]))=={entry['sha256'] for entry in body['files'].values()})
        return bundle

    def certify_exact_composition(self,token,*,compiled_id):
        with self._mutex:
            self._binding_owner(token);compiled,dependencies,payload=self._exact_compiled(compiled_id)
            bundle=composition.read_bundle()
            require(all(bundle[name]==raw for name,raw in dependencies['bundle'].items()))
        package=self._retain_exact_composition(bundle)
        attempt=self._bound_start('exact_composition',compiled_id);report=error=None
        comp_hash=digest(compiled['body']['compilation'])
        try:
            with tempfile.TemporaryDirectory(prefix='trf-exact-composition-') as directory:
                report=composition.run_child(bundle,payload,comp_hash,directory)
        except Exception as exc:error={'type':type(exc).__name__,'reason':str(exc)}
        except BaseException:self._bound_interrupted(attempt);raise
        with self._transaction():
            self._binding_owner(token)
            if error is None:
                try:
                    self._exact_compiled(compiled_id)
                    require(hashes(self._exact_composition_package(package['id']))==hashes(composition.read_bundle()))
                except Exception as exc:error={'type':type(exc).__name__,'reason':str(exc)}
            record=self._exact_save({'schema':'exact-composition-certificate/1','profile':composition.PROFILE,
                'created_at':self._now(),'status':'CONFORMANT' if error is None else 'CERTIFICATION_GAP',
                'attempt_id':attempt,'error':error,'compiled_id':compiled_id,'source_package_id':package['id'],
                'candidate_hash':digest(payload['candidate']),'compilation_hash':comp_hash,'report':report,
                'scientific_readiness':False},[compiled_id,package['id']])
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=record['id'],status=record['body']['status'])
            return record

    def _require_exact_composition(self,identity,compiled,payload):
        artifact=self._artifact(text(identity,'exact composition certificate'));body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and artifact['authority']==AUTHORITY
            and type(body) is dict and body.get('schema')=='exact-composition-certificate/1'
            and body.get('profile')==composition.PROFILE and body.get('status')=='CONFORMANT'
            and body.get('compiled_id')==compiled['id'] and body.get('scientific_readiness') is False)
        self._require_usable_dependencies(identity)
        bundle=self._exact_composition_package(body['source_package_id']);report=body['report']
        comp_hash=digest(compiled['body']['compilation'])
        require(type(report) is dict and set(report)=={'result','request_hash','footprint','environment'}
            and report['request_hash']==digest({'payload':payload,'compilation_hash':comp_hash,'footprint':hashes(bundle)})
            and body['candidate_hash']==digest(payload['candidate']) and body['compilation_hash']==comp_hash
            and hashes(bundle)==hashes(composition.read_bundle()) and report['footprint']==hashes(bundle)
            and canonical(report['result'])==canonical(composition.expected(payload,comp_hash))
            and _environment_current(report['environment']))
        return artifact

    def execute_exact(self,token,*,compiled_id,meaning_assessment_id,composition_id):
        started=time.monotonic()
        with self._mutex:
            actor=self._binding_owner(token);compiled,dependencies,payload=self._exact_compiled(compiled_id)
            assessment=self._artifact(text(meaning_assessment_id,'meaning assessment'))
            require(assessment['body']['formalization_id']==compiled['body']['formalization_id'])
            meaning=self._inspect_meaning_review(actor,meaning_assessment_id)
            require(meaning['current'] and meaning['independent_semantic_review']=='SATISFIED','Current independent meaning review required')
            self._require_exact_composition(composition_id,compiled,payload)
            bundle=self._exact_package(compiled['body']['source_package_id'])
            require(hashes(bundle)==hashes(dependencies['bundle']))
        attempt=self._bound_start('exact_development_execution',compiled_id)
        report=verification=descriptor=capsule=error=None
        remaining=lambda:int(1800-(time.monotonic()-started))
        try:
            selection=compiled['body']['compilation']['row_window']
            loaded=self._load_reference_data(compiled['body']['data_snapshot_id'],selection['start'],selection['end'],selection['instruments'])
            require(digest(loaded['catalog'])==digest(payload['catalog']))
            with tempfile.TemporaryDirectory(prefix='trf-exact-execute-') as temporary:
                directory=Path(temporary);size=0
                with (directory/'rows.jsonl').open('xb') as stream:
                    for row in loaded['rows']:
                        raw=(canonical(row)+'\n').encode();size+=len(raw);require(size<=runtime.MAX_STREAM);stream.write(raw)
                execution={'compilation_input':payload,'compilation_hash':digest(compiled['body']['compilation']),
                    'rows':runtime._stream(directory/'rows.jsonl')}
                with self._transaction():
                    capsule=self._exact_save({'schema':'exact-execution-input/1','created_at':self._now(),
                        'compiled_id':compiled_id,'composition_id':composition_id,'meaning_assessment_id':meaning_assessment_id,
                        'input':execution,'scientific_readiness':False},[compiled_id,meaning_assessment_id,composition_id])
                report=runtime.run_child(bundle,'execute',execution,directory,timeout=remaining())
                with (directory/'cases.jsonl').open('rb') as stream:descriptor=self._stage_blob_stream(stream)
                require(descriptor==report['result']['case_blob'])
                with tempfile.TemporaryDirectory(prefix='trf-exact-replay-') as second:
                    for name in ('rows.jsonl','cases.jsonl'):shutil.copyfile(directory/name,Path(second)/name)
                    verification=runtime.run_child(bundle,'verify',{'execution_input':execution,'result':report['result']},second,timeout=remaining())
                require(canonical(verification['result'])==canonical({'schema':'exact-case-verification/1',
                    'result_hash':digest(report['result']),'compilation_hash':execution['compilation_hash'],
                    'case_blob':report['result']['case_blob'],'checked_cases':report['result']['report']['processed_case_count'],
                    'scientific_readiness':False}))
        except Exception as exc:error={'type':type(exc).__name__,'reason':str(exc)}
        except BaseException:self._bound_interrupted(attempt);raise
        with self._transaction():
            actor=self._binding_owner(token)
            if error is None:
                try:
                    self._exact_compiled(compiled_id)
                    require(self._inspect_meaning_review(actor,meaning_assessment_id)==meaning)
                    self._require_exact_composition(composition_id,compiled,payload)
                except Exception as exc:error={'type':type(exc).__name__,'reason':str(exc)}
            if descriptor is not None:self._register_blob(descriptor)
            complete=(report is not None and report['result']['report']['processing_complete']
                and report['result']['report']['diagnostics']['processing_complete'])
            refs=[compiled_id,meaning_assessment_id,composition_id,*([capsule['id']] if capsule else [])]
            record=self._exact_save({'schema':'exact-reference-execution/1','profile':PROFILE,'created_at':self._now(),
                'status':'EXECUTION_GAP' if error is not None else 'DESCRIPTIVE_EXECUTION' if complete else 'RESOURCE_STOP',
                'attempt_id':attempt,'error':error,'compiled_id':compiled_id,'data_snapshot_id':compiled['body']['data_snapshot_id'],
                'composition_id':composition_id,'meaning_assessment_id':meaning_assessment_id,
                'elapsed_ms':int(1000*(time.monotonic()-started)),'result':report['result'] if report is not None else None,
                'environment':report['environment'] if report is not None else None,'verification':verification,
                'complete_required_report':bool(complete and error is None),'scientific_readiness':False,
                'qualification':'COMPUTED_UNCALIBRATED development computation; no scientific classification, independent confirmation or policy return.'},
                refs,blobs=[descriptor['sha256']] if descriptor is not None else [])
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=record['id'],status=record['body']['status'])
            return record
