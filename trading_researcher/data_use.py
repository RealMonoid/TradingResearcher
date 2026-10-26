"""Exact qualified development use under research-contract/1.0 sections 1, 6, 12.

This is a data-purpose/exposure check, not an outcome verdict or holdout grant.
Provider text is reviewed once by exact bytes; arbitrary rights prose cannot pass.
"""
import hashlib
from pathlib import Path

from .binding import require
from .codec import Invalid, decode, digest, integer, text
from .errors import Conflict, Denied
from .features import binding


SCHEMA='data-use-assessment/1'
PROFILE='qualified-development-data-use/1'
AUTHORITY='qualified_exploration_data_use_only'
PROTECTED_PROFILE='qualified-protected-target-data-use/1'
PROTECTED_AUTHORITY='private_plan_data_prerequisite_only'
PURPOSE='Personal non-production historical research'
REVIEWED_DOCUMENTS={
    'README.md':'2e133d9945a9263a02781369078e72805eff074680f305cd5460016471c6caad',
    'TERMS_AND_CONDITIONS.md':'99c4921dbe023cd68c1a447775707d621453cc78aec6ac0bfe2e6c06a5114ee0'}
LOADED_SELF=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def checker_current(expected):
    try:return expected==LOADED_SELF and hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==LOADED_SELF
    except OSError:return False


def protected_knowledge_gaps(knowledge):
    """Inspect concrete retained ancestry, not unknowable pretraining contents."""
    return [gap for field,gap in (
        ('protected_knowledge_ids','PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY'),
        ('operations_knowledge_ids','OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT'),
        ('unresolved_exposure_refs','UNRESOLVED_CANDIDATE_EXPOSURE')) if knowledge[field]]


def use_profile(compiled):
    return PROTECTED_PROFILE if 'data_target_binding_id' in compiled['body']['dependency_arguments'] else PROFILE


def prior_knowledge(broker, formalization):
    """Start before compiler dependency expansion; never subtract target IDs.

    Missing source/worker-context bindings are integrity failures. Opaque exposure
    annotations remain unresolved, even when exploration can proceed with them.
    """
    pending=[(formalization['id'],True)];seen=set();unresolved=set();protected=set();contexts=set()
    operations=set();technical=set()
    while pending:
        identity,required=pending.pop()
        if identity in seen:continue
        require(len(seen)+len(unresolved)<4096,'Candidate ancestry exceeds the inspection envelope')
        exists=broker._db.execute('SELECT 1 FROM artifacts WHERE id=?',(identity,)).fetchone()
        if exists is None:
            require(not required,'Required candidate source is unavailable')
            unresolved.add(identity);continue
        artifact=broker._artifact(identity);seen.add(identity)
        body=artifact['body'];schema=body.get('schema') if type(body) is dict else None
        if artifact['data_class']=='assessment' or schema in ('evaluator-calibration-input/1','evaluator-calibration-attempt/1'):
            protected.add(identity)
        if artifact['data_class']=='operations':
            owned=artifact['creator']==artifact['origin']=='controller'
            implementation=(schema in ('reference-source-package/1','feature-source-package/1',
                'binding-source-package/1','composition-source-package/1')
                and artifact['authority']=='retained_source_not_certified')
            certificate=schema=='implementation-certificate/1' and artifact['authority']=='implementation_conformance_only'
            (technical if owned and (implementation or certificate) else operations).add(identity)
        pending.extend((ref,True) for ref in artifact['source_refs'])
        pending.extend((ref,False) for ref in artifact['exposure'])
        if artifact['origin']=='worker':
            context=broker._context(artifact['context_id']);job=broker._job(artifact['job_id'])
            require(job['spec']['context_id']==context['id'],'Worker context binding differs')
            contexts.add(context['id'])
            require(set(context['artifact_ids'])<=set(artifact['source_refs'])
                and set(context['exposure'])<=set(artifact['exposure']),'Worker ancestry omits its authorized context')
            pending.extend((ref,True) for ref in context['artifact_ids'])
            pending.extend((ref,False) for ref in context['exposure'])
    return {'artifact_ids':sorted(seen),'context_ids':sorted(contexts),
        'unresolved_exposure_refs':sorted(unresolved),'protected_knowledge_ids':sorted(protected),
        'operations_knowledge_ids':sorted(operations),'technical_provenance_ids':sorted(technical),
        'basis':'Original idea and complete authorized formalization ancestry, before compiler-added dependencies.'}


def reviewed_documents(broker, identity):
    from .binance_ingest import validate_provider_document_bytes
    # Internal reads reuse the caller's transaction. The standalone ingestion
    # helpers use public broker calls and would start a nested transaction here.
    artifact=broker._artifact(identity);body=artifact['body']
    require(artifact['creator']=='operator' and artifact['origin']=='source' and type(body) is dict
        and body.get('schema')=='binance-provider-documents/1' and body.get('scientific_readiness') is False)
    files=body['files'];values={}
    require(set(files)=={'documents.json','README.md','TERMS_AND_CONDITIONS.md'})
    for name,descriptor in files.items():
        require(set(descriptor)=={'sha256','size','artifact_ref'})
        require(integer(descriptor['size'],'provider document size')<=1048576)
        require(descriptor['artifact_ref'] in artifact['exposure'],'Provider document ancestry is incomplete')
        source=broker._artifact(descriptor['artifact_ref'])
        require(source['creator']=='operator' and source['origin']=='source'
            and source['body'].get('schema')=='blob-source/1'
            and source['body']['blob']=={key:descriptor[key] for key in ('sha256','size')})
        raw=broker._read_blob_bytes(descriptor['sha256'])
        require(len(raw)==descriptor['size']);values[name]=raw
    receipt=decode(values['documents.json'])
    validate_provider_document_bytes(receipt,{name:values[name] for name in ('README.md','TERMS_AND_CONDITIONS.md')})
    require(receipt['retrieved_at']==body['retrieved_at'],'Provider document receipt differs')
    actual={name:files[name]['sha256'] for name in REVIEWED_DOCUMENTS}
    return {'provider_documents_id':identity,'document_sha256':actual,
        'receipt_sha256':files['documents.json']['sha256'],'retrieved_at':artifact['body']['retrieved_at'],
        'reviewed_bytes_match':actual==REVIEWED_DOCUMENTS,'purpose':PURPOSE,
        'basis':'Reviewed dataset terms v1.0 section 4.1 and research-contract/1.0 section 6; no commercial or production permission.'}


class DataUseAssessments:
    def _data_use_findings(self,actor,compiled_id):
        compiled,_=self._composition_inputs(actor,compiled_id)
        body=compiled['body'];args=body['dependency_arguments']
        formalization=self._artifact(args['formalization_id'])
        original=binding(self,body['data_snapshot_id'])
        snapshot=original['snapshot'];manifest=snapshot['body']['manifest']
        feature=self._artifact(args['feature_certificate_id'])
        definitions=self._artifact(feature['body']['definitions_id'])
        delay=original['request']['delay_seconds']
        require(definitions['body']['parameters']=={'delay_seconds':delay},'Feature availability parameter differs from normalization')
        require(all(item['availability']=={'basis':'assumed','rule':'row_time + delay_seconds',
            'parameter':'EXPLICIT_NONNEGATIVE_INTEGER_SECONDS_NO_DEFAULT','historical_publication_time':None}
            for item in definitions['body']['definitions']),'Feature availability meaning differs')
        rights=reviewed_documents(self,original['request']['provider_documents_ref'])
        knowledge=prior_knowledge(self,formalization)
        private=None
        if use_profile(compiled)==PROTECTED_PROFILE:
            private=self._checked_target_binding(actor,args['data_target_binding_id'])
            resolved=private['body']['resolved']
            require(resolved['data_snapshot_id']==snapshot['id'] and resolved['feature_certificate_id']==feature['id'],
                'Private data qualification differs from compilation')
        gaps=[]
        if private is None and (manifest['partition']!='development' or snapshot['data_class']!='development'):
            gaps.append('PROTECTED_TARGET_REQUIRES_SEPARATE_ADMISSION')
        if knowledge['protected_knowledge_ids']:gaps.append('PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY')
        if knowledge['operations_knowledge_ids']:gaps.append('OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT')
        if private is not None and knowledge['unresolved_exposure_refs']:gaps.append('UNRESOLVED_CANDIDATE_EXPOSURE')
        if manifest['rights']['basis']!='documented' or not rights['reviewed_bytes_match']:gaps.append('PROVIDER_DOCUMENT_REVIEW_REQUIRED')
        findings={'scope':{'compiled_id':compiled_id,'formalization_id':formalization['id'],
                'data_snapshot_id':snapshot['id'],'catalog_id':snapshot['body']['catalog_id'],
                'feature_certificate_id':feature['id'],'feature_definitions_id':definitions['id'],
                'normalization_id':original['normalization']['id'],'partition':manifest['partition'],
                'universe':body['compilation']['request']['universe'],'row_window':body['compilation']['row_window'],
                'purpose':PURPOSE,'use':'qualified_historical_exploration'},
            'rights':rights,'prior_knowledge':knowledge,
            'availability':{'basis':'assumed','delay_seconds':delay,'historical_publication_time':None,
                'historical_vintage_verified':False,'provenance':manifest['provenance']},
            'exposure':{'target_in_candidate_ancestry':snapshot['id'] in knowledge['artifact_ids'],
                'model_training_exposure':'UNKNOWN','evidence_origin':None,
                'origin_reason':'Training exposure and historical publication vintage are unverified; known and unresolved candidate exposure is retained.',
                'independent_confirmation':False},
            'gaps':gaps,'scientific_readiness':False,'allocation_reserved':False,'frozen':False}
        if private is not None:
            findings['scope'].update({'use':'qualified_private_plan_preparation',
                'data_target_binding_id':private['id'],'public_target_id':resolved['target_id'],
                'public_definitions_id':resolved['public_definitions_id']})
            findings['exposure'].update({'candidate_ancestry_check':'RECORDED_ANCESTRY_ONLY',
                'external_selection_knowledge':'UNKNOWN','reserved_role_verified':False,
                'campaign_selection_and_prior_use':'NOT_ASSESSED'})
        return findings

    def _assess_data_use(self,actor,compiled_id):
        text(compiled_id,'compiled identity')
        compiled=self._artifact(compiled_id);body=compiled['body']
        require(compiled['creator']==compiled['origin']=='controller' and type(body) is dict
            and body.get('schema')=='compiled-hypothesis/1' and body.get('status')=='COMPILED',
            'Owned successful compilation required')
        require(checker_current(LOADED_SELF),'Restart after data-use checker changes')
        profile=use_profile(compiled)
        protected=profile==PROTECTED_PROFILE
        findings=None;failure=None
        try:findings=self._data_use_findings(actor,compiled_id)
        except (Invalid,Conflict,Denied,OSError,KeyError,TypeError,ValueError) as exc:failure=type(exc).__name__
        passed=findings is not None and not findings['gaps']
        refs=sorted({compiled_id,*compiled['source_refs']})
        saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
            'data_class':compiled['data_class'],'source_refs':refs,'exposure':sorted(set(refs)|set(compiled['exposure'])),
            'authority':PROTECTED_AUTHORITY if protected else AUTHORITY,'body':{'schema':SCHEMA,'profile':profile,'created_at':self._now(),
                'compiled_id':compiled_id,'checker_sha256':LOADED_SELF,
                'status':('QUALIFIED_PRIVATE_PLAN_DATA' if protected else 'QUALIFIED_EXPLORATION') if passed else 'DATA_USE_GAP',
                'findings':findings,'failure_type':failure,'scientific_readiness':False,
                'qualification':('Exact private plan prerequisite only; recorded candidate ancestry is not complete campaign/selection chronology or an unused reservation. '
                    if protected else 'Exact exploratory use only. ')
                    +'No unseen-history, outcome eligibility, estimator validity, holdout admission, allocation, freeze or deployment authority.'}})
        self._event(actor['name'],'data_use_assessed',artifact_id=saved['id'],compiled_id=compiled_id,status=saved['body']['status'])
        return saved

    def _inspect_data_use(self,actor,assessment_id,compiled_id=None):
        artifact=self._artifact(text(assessment_id,'data-use assessment'));body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and type(body) is dict and body.get('schema')==SCHEMA
            and body.get('profile') in (PROFILE,PROTECTED_PROFILE)
            and artifact['authority']==(PROTECTED_AUTHORITY if body['profile']==PROTECTED_PROFILE else AUTHORITY),
            'Owned data-use assessment required')
        if compiled_id is not None:require(body['compiled_id']==compiled_id,'Data use targets another compilation')
        status=body['status']
        if self._dependency_use(assessment_id)['status']=='INVALIDATED_BY_DEPENDENCY':status='INVALIDATED_BY_DEPENDENCY'
        elif not checker_current(body['checker_sha256']):status='STALE_CHECKER'
        elif status in ('QUALIFIED_EXPLORATION','QUALIFIED_PRIVATE_PLAN_DATA'):
            try:current=self._data_use_findings(actor,body['compiled_id'])
            except (Invalid,Conflict,Denied,OSError,KeyError,TypeError,ValueError):status='QUARANTINED'
            else:
                if digest(current)!=digest(body['findings']):status='STALE_EVIDENCE'
        return {'assessment_id':assessment_id,'compiled_id':body['compiled_id'],'status':status,
            'qualified_exploration_data_use':'SATISFIED' if status=='QUALIFIED_EXPLORATION' else 'NOT_SATISFIED',
            **({'qualified_protected_target_data_use':'SATISFIED' if status=='QUALIFIED_PRIVATE_PLAN_DATA' else 'NOT_SATISFIED'}
                if body['profile']==PROTECTED_PROFILE else {}),
            'scientific_readiness':False,'independent_confirmation':False,'protected_target_admission':False}
