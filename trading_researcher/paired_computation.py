"""Operator-owned D094 compilation and development execution gates."""
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import time

from .binding import require, hashes
from .codec import canonical, decode, digest, text
from .errors import Denied
from .certification import _environment_current
from .data_use import prior_knowledge, reviewed_documents
from .features import binding as feature_binding
from .paired_development import CONTRACT, PAIR, PROFILE
from .paired_formalization import SCHEMA, validate_record
from . import paired_runtime
from . import paired_composition

AUTHORITY='paired_descriptive_development_only'


class PairedComputation:
    def _paired_save(self,body,refs,*,blobs=(),data_class='development',authority=AUTHORITY):
        refs=sorted(set(refs))
        exposure=set(refs)
        for identity in refs:
            exposure.update(self._artifact(identity)['exposure'])
        return self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
            'data_class':data_class,'source_refs':refs,'exposure':sorted(exposure),'blob_refs':sorted(set(blobs)),
            'authority':authority,'body':body})

    def _paired_dependencies(self,formalization_id,feature_certificate_id):
        target=self._artifact(text(formalization_id,'formalization identity'))
        require(target['origin']=='worker' and target['body'].get('schema')==SCHEMA,
                'Owned paired formalization required')
        job=self._job(target['job_id'])
        require(job['state']=='completed' and job['result_id']==formalization_id and job['spec']['kind']=='formalization/v1'
            and job['spec'].get('research_inputs',{}).get('paired_contract')==CONTRACT)
        validate_record(target['body'],[self._artifact(ref) for ref in target['source_refs']])
        require(target['body']['assessment']['status']=='STRUCTURE_CHECKED','Original meaning retains a structural gap')
        self._deny_final_calibration_ancestry(target)
        candidate=target['body']['candidate']
        snapshot_id=candidate['test_universe']['data_snapshot_ref']
        require(snapshot_id in target['source_refs'],'Selected data was not authorized to the original formalizer')
        snapshot=self._artifact(snapshot_id)
        body=snapshot['body']
        # This guard precedes every certificate, source-package and raw-row loader.
        if (snapshot['data_class']!='development' or body.get('schema')!='data-snapshot/1'
                or body.get('manifest',{}).get('partition')!='development'):
            raise Denied('Paired development cannot read protected outcomes')
        require(snapshot['creator']=='controller' and snapshot['origin']=='source'
            and body['catalog_id']==target['body']['catalog_id'])
        certificate=self._artifact(text(feature_certificate_id,'feature certificate'))
        require(job['spec']['research_inputs'].get('feature_certificate_id')==certificate['id']
            and certificate['id'] in target['source_refs'],'Original full packet must carry this exact feature evidence')
        current=self._feature_certificate_status(None,certificate['id'],data_snapshot_id=snapshot_id)
        require(current['status']=='CURRENT','Paired execution requires current raw certification')
        definition=self._artifact(certificate['body']['definitions_id'])
        require(definition['id'] in target['body']['definition_ids'])
        catalog=self._artifact(body['catalog_id'])['body']['features']
        definitions=definition['body']['definitions']
        require(digest(catalog)==body['catalog_hash'] and digest(catalog)==digest({
            item['feature_ref']:{key:item[key] for key in ('type','unit')} for item in definitions}))
        reference,bundle=self._paired_require_qualification()
        refs=sorted({target['id'],snapshot_id,certificate['id'],definition['id'],body['catalog_id'],reference['id']})
        # Generic catalog/idea provenance is not a technical-use dependency.
        # Its exact bytes and meaning inventory are checked separately above.
        for identity in (snapshot_id,certificate['id'],definition['id'],reference['id']):
            self._require_usable_dependencies(identity)
        return {'formalization':target,'snapshot':snapshot,'feature_certificate':certificate,
            'definition':definition,'catalog':catalog,'reference':reference,'bundle':bundle,'refs':refs}

    def _paired_data_use(self,dependencies):
        snapshot=dependencies['snapshot']
        manifest=snapshot['body']['manifest']
        original=feature_binding(self,snapshot['id'])
        definition=dependencies['definition']['body']
        delay=original['request']['delay_seconds']
        require(definition['parameters']=={'delay_seconds':delay})
        rights=reviewed_documents(self,original['request']['provider_documents_ref'])
        knowledge=prior_knowledge(self,dependencies['formalization'])
        gaps=[]
        if knowledge['protected_knowledge_ids']:
            gaps.append('PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY')
        if knowledge['operations_knowledge_ids']:
            gaps.append('OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT')
        if manifest['rights']['basis']!='documented' or not rights['reviewed_bytes_match']:
            gaps.append('PROVIDER_DOCUMENT_REVIEW_REQUIRED')
        return {'schema':'paired-data-use-assessment/1','status':'QUALIFIED' if not gaps else 'DATA_USE_GAP',
            'data_snapshot_id':snapshot['id'],'formalization_id':dependencies['formalization']['id'],
            'rights':rights,'prior_knowledge':knowledge,'gaps':gaps,
            'availability':{'basis':'assumed','delay_seconds':delay,'historical_publication_time':None,
                'historical_vintage_verified':False,'provenance':manifest['provenance']},
            'model_training_exposure':'UNKNOWN','independent_confirmation':False,'evidence_origin':None,
            'scientific_readiness':False}

    def compile_paired(self,token,*,formalization_id,feature_certificate_id,as_of,max_steps=10000000):
        with self._mutex:
            self._binding_owner(token)
            dependencies=self._paired_dependencies(formalization_id,feature_certificate_id)
            from .outcomes import _instant
            require(_instant(as_of)<=self._now(),'Future as_of is unavailable')
            data_use=self._paired_data_use(dependencies)
            require(data_use['status']=='QUALIFIED','Qualified development data use is required')
            payload={'formalization_id':formalization_id,'candidate':dependencies['formalization']['body']['candidate'],
                'catalog':dependencies['catalog'],'feature_definitions':dependencies['definition']['body']['definitions'],
                'data_manifest':dependencies['snapshot']['body']['manifest'],'as_of':as_of,'max_steps':max_steps}
            bundle=dependencies['bundle']
        with self._transaction():
            capsule=self._paired_save({'schema':'paired-compilation-input/1','created_at':self._now(),
                'input':payload,'input_sha256':digest(payload),'data_use':data_use,'scientific_readiness':False},dependencies['refs'])
        attempt=self._bound_start('paired_compile',capsule['id'])
        report,error=None,None
        try:
            with tempfile.TemporaryDirectory(prefix='trf-paired-compile-') as directory:
                report=paired_runtime.run_child(bundle,'compile',payload,directory)
            require(report['result']==paired_runtime.compile_payload(payload))
        except Exception as exc:
            error={'type':type(exc).__name__,'reason':str(exc)}
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            self._binding_owner(token)
            if error is None:
                try:
                    current=self._paired_dependencies(formalization_id,feature_certificate_id)
                    require(current['refs']==dependencies['refs'] and self._paired_data_use(current)==data_use)
                except Exception as exc:
                    error={'type':type(exc).__name__,'reason':str(exc)}
            result=self._paired_save({'schema':'paired-compiled-hypothesis/1','profile':PROFILE,
                'created_at':self._now(),'status':'COMPILED' if error is None else 'COMPILATION_GAP',
                'attempt_id':attempt,'error':error,'input_id':capsule['id'],
                'formalization_id':formalization_id,'feature_certificate_id':feature_certificate_id,
                'reference_certificate_id':dependencies['reference']['id'],
                'data_snapshot_id':dependencies['snapshot']['id'],'source_package_id':dependencies['reference']['body']['source_package_id'],
                'compilation':report['result'] if error is None else None,
                'environment':report['environment'] if error is None else None,'scientific_readiness':False},
                [capsule['id'],*dependencies['refs']])
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=result['id'],status=result['body']['status'])
            return result

    def _paired_compiled(self,identity):
        artifact=self._artifact(text(identity,'paired compiled identity'))
        body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and artifact['authority']==AUTHORITY
            and body.get('schema')=='paired-compiled-hypothesis/1' and body.get('profile')==PROFILE
            and body.get('status')=='COMPILED' and body.get('scientific_readiness') is False)
        self._require_usable_dependencies(identity)
        dependencies=self._paired_dependencies(body['formalization_id'],body['feature_certificate_id'])
        require(dependencies['reference']['id']==body['reference_certificate_id']
            and dependencies['snapshot']['id']==body['data_snapshot_id'] and _environment_current(body['environment']))
        capsule=self._artifact(body['input_id'])
        require(capsule['creator']==capsule['origin']=='controller' and capsule['body']['schema']=='paired-compilation-input/1')
        payload=capsule['body']['input']
        require(digest(payload)==capsule['body']['input_sha256']
            and payload['candidate']==dependencies['formalization']['body']['candidate']
            and payload['catalog']==dependencies['catalog']
            and payload['feature_definitions']==dependencies['definition']['body']['definitions']
            and payload['data_manifest']==dependencies['snapshot']['body']['manifest']
            and paired_runtime.compile_payload(payload)==body['compilation']
            and self._paired_data_use(dependencies)==capsule['body']['data_use'])
        return artifact,dependencies,payload

    def certify_paired_composition(self,token,*,compiled_id):
        with self._mutex:
            self._binding_owner(token)
            compiled,dependencies,payload=self._paired_compiled(compiled_id)
            require(dependencies['formalization']['body']['idea_id']==paired_composition.IDEA_ID,
                    'Other paired ideas need independent composition expectations')
            bundle=dependencies['bundle']
        attempt=self._bound_start('paired_composition',compiled_id)
        report,error=None,None
        try:
            with tempfile.TemporaryDirectory(prefix='trf-paired-composition-') as directory:
                report=paired_runtime.run_child(bundle,'composition',payload,directory)
            require(report['result']['candidate_hash']==digest(payload['candidate'])
                and report['result']['oracle_sha256']==paired_composition.ORACLE_SHA256
                and report['result']['scenario_count']>0 and report['result']['checked_cases']>0)
        except Exception as exc:
            error={'type':type(exc).__name__,'reason':str(exc)}
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            self._binding_owner(token)
            if error is None:
                try:self._paired_compiled(compiled_id)
                except Exception as exc:error={'type':type(exc).__name__,'reason':str(exc)}
            result=self._paired_save({'schema':'paired-composition-certificate/1',
                'profile':paired_composition.PROFILE,'created_at':self._now(),'attempt_id':attempt,
                'compiled_id':compiled_id,'candidate_hash':digest(payload['candidate']),
                'status':'CERTIFIED' if error is None else 'COMPOSITION_GAP','error':error,
                'report':report,'scientific_readiness':False},[compiled_id])
            self._event('controller','bound_computation_checked',attempt_id=attempt,
                artifact_id=result['id'],status=result['body']['status'])
            return result

    def _paired_composition_status(self,identity,compiled):
        artifact=self._artifact(text(identity,'paired composition certificate'))
        body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and artifact['authority']==AUTHORITY
            and body.get('schema')=='paired-composition-certificate/1'
            and body.get('profile')==paired_composition.PROFILE and body.get('status')=='CERTIFIED'
            and body.get('compiled_id')==compiled['id'] and body.get('scientific_readiness') is False
            and body.get('candidate_hash')==compiled['body']['compilation']['candidate_hash'])
        self._require_usable_dependencies(identity)
        report=body['report']
        require(report['result']['candidate_hash']==body['candidate_hash']
            and report['result']['oracle_sha256']==paired_composition.ORACLE_SHA256
            and report['footprint']==hashes(paired_runtime.read_bundle())
            and _environment_current(report['environment']))
        return artifact

    def execute_paired(self,token,*,compiled_id,meaning_assessment_id,composition_id):
        started=time.monotonic()
        with self._mutex:
            actor=self._binding_owner(token)
            compiled,dependencies,payload=self._paired_compiled(compiled_id)
            assessment=self._artifact(meaning_assessment_id)
            require(assessment['body']['formalization_id']==compiled['body']['formalization_id'])
            meaning=self._inspect_meaning_review(actor,meaning_assessment_id)
            require(meaning['current'] and meaning['independent_semantic_review']=='SATISFIED')
            self._paired_composition_status(composition_id,compiled)
            bundle=self._paired_package(compiled['body']['source_package_id'])
            require(hashes(bundle)==hashes(dependencies['bundle']))
        attempt=self._bound_start('paired_development_execution',compiled_id)
        report,verification,audit,descriptor,error=None,None,None,None,None
        try:
            selection=compiled['body']['compilation']['row_window']
            loaded=self._load_reference_data(compiled['body']['data_snapshot_id'],selection['start'],selection['end'],selection['instruments'])
            require(digest(loaded['catalog'])==digest(payload['catalog']))
            with tempfile.TemporaryDirectory(prefix='trf-paired-execute-') as temporary:
                directory=Path(temporary)
                with (directory/'rows.jsonl').open('xb') as stream:
                    size=0
                    for row in loaded['rows']:
                        raw=(canonical(row)+'\n').encode()
                        size+=len(raw)
                        require(size<=paired_runtime.MAX_STREAM)
                        stream.write(raw)
                execution_input={'compilation_input':payload,'compilation_hash':digest(compiled['body']['compilation']),
                    'rows':paired_runtime._stream(directory/'rows.jsonl')}
                # Retain exact inputs before starting any original market calculation.
                with self._transaction():
                    capsule=self._paired_save({'schema':'paired-execution-input/1','created_at':self._now(),
                        'compiled_id':compiled_id,'input':execution_input,'scientific_readiness':False},
                        [compiled_id,meaning_assessment_id,composition_id])
                report=paired_runtime.run_child(bundle,'execute',execution_input,directory,
                    timeout=int(1800-(time.monotonic()-started)))
                with tempfile.TemporaryDirectory(prefix='trf-paired-replay-') as second:
                    for name in ('rows.jsonl','cases.jsonl'):
                        shutil.copyfile(directory/name,Path(second)/name)
                    verification=paired_runtime.run_child(bundle,'verify',{
                        'execution_input':execution_input,'result':report['result']},second,
                        timeout=int(1800-(time.monotonic()-started)))
                require(verification['result']=={'schema':'paired-case-verification/1',
                    'result_hash':digest(report['result']),'case_blob':report['result']['case_blob'],
                    'checked_cases':report['result']['report']['processed_case_count'],'scientific_readiness':False})
                with (directory/'cases.jsonl').open('rb') as stream:
                    descriptor=self._stage_blob_stream(stream)
                require(descriptor==report['result']['case_blob'])
                if report['result']['report']['processing_complete']:
                    with tempfile.TemporaryDirectory(prefix='trf-paired-oracle-') as third:
                        for name in ('rows.jsonl','cases.jsonl'):
                            shutil.copyfile(directory/name,Path(third)/name)
                        audit=paired_runtime.run_child(bundle,'audit',{
                            'execution_input':execution_input,'result':report['result']},third,
                            timeout=int(1800-(time.monotonic()-started)))
        except Exception as exc:
            error={'type':type(exc).__name__,'reason':str(exc)}
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            actor=self._binding_owner(token)
            if error is None:
                try:
                    self._paired_compiled(compiled_id)
                    current=self._inspect_meaning_review(actor,meaning_assessment_id)
                    require(current==meaning)
                    self._paired_composition_status(composition_id,compiled)
                except Exception as exc:
                    error={'type':type(exc).__name__,'reason':str(exc)}
            if descriptor is not None:
                self._register_blob(descriptor)
            refs=[compiled_id,meaning_assessment_id,composition_id]
            if 'capsule' in locals():
                refs.append(capsule['id'])
            result=self._paired_save({'schema':'paired-reference-execution/1','profile':PROFILE,
                'created_at':self._now(),'status':('EXECUTION_GAP' if error is not None else
                    'DESCRIPTIVE_EXECUTION' if report['result']['report']['processing_complete'] else 'RESOURCE_STOP'),
                'attempt_id':attempt,'error':error,'compiled_id':compiled_id,
                'data_snapshot_id':compiled['body']['data_snapshot_id'],'elapsed_ms':int(1000*(time.monotonic()-started)),
                'result':report['result'] if report is not None else None,
                'environment':report['environment'] if report is not None else None,
                'verification':verification,'scientific_readiness':False,
                'independent_original_audit':audit,
                'qualification':'COMPUTED_UNCALIBRATED development computation; no scientific classification or policy return.'},
                refs,blobs=[descriptor['sha256']] if descriptor is not None else [])
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=result['id'],status=result['body']['status'])
            return result
