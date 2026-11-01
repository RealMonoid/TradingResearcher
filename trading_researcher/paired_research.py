"""Opt-in paired research transport; existing v1 host methods remain unchanged.

Static copies preserve the original authorization, lease, source and receipt
checks. Only the explicit D094 packet/record validation is routed here.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path

from . import checks
from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .auxiliary import (KINDS, require, request_for, check_definition_origins,
                        mapping_count, validate_judgment)
from .auxiliary_availability import availability_summary
from .data import window
from .features import PROFILE, SCOPE
from .formalization import validate_inputs
from .paired_formalization import SCHEMA, assess_candidate, definitions_from_sources, validate_record as validate_formalization
from .paired_development import CONTRACT
from .meaning_reviews import policy_identity

ROOT=Path(__file__).resolve().parents[1]
CONTRACT_PATH='docs/architecture/23_PAIRED_DEVELOPMENT.md'


def paired_policy_identity():
    return {**policy_identity(), 'paired_contract': CONTRACT,
        'paired_sources': {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in
            ('trading_researcher/paired_development.py','trading_researcher/paired_formalization.py',
             'trading_researcher/paired_research.py',CONTRACT_PATH,'trading_researcher/PAIRED_DEVELOPMENT.md')}}


def paired_contract(inputs):
    require(inputs.get('paired_contract')==CONTRACT and 'reporting_contract' not in inputs,
            'Explicit paired semantics required without legacy reporting substitution')
    from .certification import BOUNDED_PINS
    paths=[CONTRACT_PATH,'trading_researcher/PAIRED_DEVELOPMENT.md','docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md']
    documents=[]
    for path in paths:
        raw=(ROOT/path).read_bytes()
        checksum=hashlib.sha256(raw).hexdigest()
        if path in BOUNDED_PINS:
            require(checksum==BOUNDED_PINS[path],'Existing bounded numerical contract changed')
        documents.append({'path':path,'sha256':checksum,'text':raw.decode('utf-8')})
    return {'paired_contract':{'schema':CONTRACT,'documents':documents}}


def paired_check(kind,result,sources):
    if kind=='formalization/v1' and type(result) is dict and result.get('schema')==SCHEMA:
        validate_formalization(result,sources)
        return 'Paired structure and original source retention checked; no scientific authority'
    return checks.validate(kind,result,sources)


def availability_packet(host, context, inputs, catalog_id, definitions, target=None):
    if 'feature_certificate_id' not in inputs:
        return {}
    identity = text(inputs['feature_certificate_id'], 'feature certificate identity')
    authorized = set(context['artifact_ids'])
    if identity not in authorized:
        raise Denied('Availability certificate is outside the frozen context')
    certificate = host._artifact(identity)
    body = certificate['body']
    require(certificate['creator'] == 'controller' and certificate['origin'] == 'controller'
        and certificate['data_class'] == 'development' and certificate['authority'] == SCOPE['authority']
        and type(body) is dict and body.get('schema') == 'feature-certificate/1'
        and body.get('profile') == PROFILE and body.get('status') == 'CERTIFIED',
        'Availability evidence needs an owned certified development measurement')
    snapshot_id = text(body.get('data_snapshot_id'), 'certified snapshot identity')
    definition_id = text(body.get('definitions_id'), 'certified definition identity')
    required_ids = {identity, snapshot_id, catalog_id, definition_id}
    if not required_ids <= authorized:
        raise Denied('Availability certificate does not authorize unlisted inputs')
    definition = next((item for item in definitions if item['id'] == definition_id), None)
    require(definition is not None, 'Availability evidence must use the supplied certified definitions')
    require({snapshot_id, catalog_id} <= set(definition['body']['input_refs']), 'Availability definition origins differ')
    snapshot = host._artifact(snapshot_id)
    data = snapshot['body']
    require(snapshot['creator'] == 'controller' and snapshot['origin'] == 'source'
        and snapshot['data_class'] == 'development' and type(data) is dict
        and data.get('schema') == 'data-snapshot/1' and data.get('catalog_id') == catalog_id,
        'Availability evidence needs the exact owned development snapshot and catalog')
    manifest = data['manifest']
    require(manifest['partition'] == 'development' and manifest['availability']['basis'] == 'assumed',
        'Availability evidence cannot expose a protected or different data profile')
    universe = manifest['universe']
    start, end, instruments = window(universe)
    require((end-start)//900 * len(instruments) <= 100000, 'Availability evidence exceeds its bounded data view')
    declared = definition['body']['definitions']
    delay = definition['body']['parameters']['delay_seconds']
    integer(delay, 'explicit certified delay')
    require(all(item['availability'] == {'basis': 'assumed', 'rule': 'row_time + delay_seconds',
        'parameter': 'EXPLICIT_NONNEGATIVE_INTEGER_SECONDS_NO_DEFAULT', 'historical_publication_time': None}
        for item in declared), 'Unsupported certified availability rule')
    if target is not None:
        original_context = host._context(host._job(target['job_id'])['spec']['context_id'])
        if not all(required_ids <= set(ids) for ids in (original_context['artifact_ids'],
                target['source_refs'], target['body']['authorization_snapshot'])):
            raise Denied('Availability evidence was not authorized to the original formalization')
        allowed = {target['id'], target['body']['idea_id'], catalog_id,
                   *(item['id'] for item in definitions), identity, snapshot_id}
        if not authorized <= allowed:
            raise Denied('Availability review context contains unrelated material')
        candidate = target['body']['candidate']
        if type(candidate) is dict:
            selected = candidate.get('test_universe', {})
            require(type(selected) is dict, 'candidate universe must be an object')
            require(selected.get('data_snapshot_ref') == snapshot_id, 'Candidate and availability snapshots differ')
            lower, upper, chosen = window({'start': selected.get('start'), 'end': selected.get('end'), 'instruments': selected.get('pair')})
            require(start <= lower < upper <= end and set(chosen) <= set(instruments),
                    'Candidate is outside its availability evidence scope')
            refs = strings(candidate.get('feature_refs'), 'candidate feature references')
            require(set(refs) <= {item['feature_ref'] for item in declared}, 'Candidate dependencies lack timing evidence')
    # Status checks read retained packages/blobs: all identity and access checks
    # above deliberately precede this operation, including protected-data denial.
    status = host._feature_certificate_status(None, identity, data_snapshot_id=snapshot_id)
    require(status['status'] in ('CURRENT', 'STALE'), 'Availability certificate is not intact and usable')
    loaded = host._load_reference_data(snapshot_id, universe['start'], universe['end'], instruments)
    require(loaded['data_snapshot_ref'] == snapshot_id and digest(loaded['catalog']) == data['catalog_hash'],
            'Availability source identity changed')
    summary = availability_summary(loaded['rows'], declared, delay, universe)
    for dependency in (identity, snapshot_id, definition_id):
        host._require_usable_dependencies(dependency)
    return {'availability_evidence': {'schema': 'development-availability-evidence/1',
        'certificate_id': identity, 'data_snapshot_id': snapshot_id, 'catalog_id': catalog_id,
        'definitions_id': definition_id, 'certificate_body_sha256': digest(body),
        'source_footprint_sha256': digest(body['footprint']),
        'row_blobs': deepcopy(body['replay']['row_blobs']), 'universe': deepcopy(universe),
        'delay_seconds': delay, 'rule': 'For every present feature entry, including null-valued entries, available_at equals row_time + delay_seconds exactly.',
        'summary': summary, 'availability_basis': 'assumed', 'historical_publication_time': None,
        'qualification': 'Exhaustive timing check of this exact certified development snapshot. Absent rows and missing/null values remain missing. No later recorded availability exists among these entries. This is not historical publication truth, a hypothesis-equivalence verdict, an outcome result or scientific admission. The reviewer must separately derive the candidate-specific cutoff implications.',
        'scientific_readiness': False}}


class PairedResearch:
    def _auxiliary_packet_for_spec(self,spec):
        if spec.get('research_inputs',{}).get('paired_contract')!=CONTRACT:
            return super()._auxiliary_packet_for_spec(spec)
        require(spec['kind'] in KINDS and 'research_epoch_id' in spec,'An auxiliary job needs its original epoch')
        context=self._context(spec['context_id'])
        require(context['role']=='formalizer' and len(spec['allowed_workers'])==1,'Auxiliary work needs one scoped formalizer capability')
        inputs=spec.get('research_inputs')
        expected={'idea_id','catalog_id','definition_ids'} if spec['kind']=='formalization/v1' else {'formalization_id','definition_ids'}
        require(type(inputs) is dict and expected <= set(inputs) <= expected|{'paired_contract','feature_certificate_id'},
            'Missing or unexpected typed auxiliary inputs')
        reporting = paired_contract(inputs)
        definitions=strings(inputs['definition_ids'],'definition_ids')
        require(len(definitions)<=16,'At most sixteen definition records may be supplied')
        identities=set(definitions)|{text(inputs[n],'auxiliary input identity') for n in expected-{'definition_ids'}}
        if 'feature_certificate_id' in inputs:
            identities.add(text(inputs['feature_certificate_id'],'feature certificate identity'))
        if not identities<=set(context['artifact_ids']):raise Denied('Auxiliary input is outside its frozen context')
        retained=[self._artifact(identity) for identity in definitions]
        defined={}
        for artifact in retained:
            body=artifact['body']
            require(artifact['creator']=='controller' and artifact['data_class']=='development'
                and type(body) is dict and body.get('schema')=='feature-definitions/1'
                and type(body.get('definitions')) is list,'Owned development feature definitions required')
            for definition in body['definitions']:
                ref=definition['feature_ref']
                require(ref not in defined,'Ambiguous duplicate feature definition')
                defined[ref]=definition
        if spec['kind']=='formalization/v1':
            idea,catalog=(self._artifact(inputs[n]) for n in ('idea_id','catalog_id'))
            validate_inputs(idea['body'],catalog['body'])
            check_definition_origins(retained,catalog['id'])
            availability = availability_packet(self,context,inputs,catalog['id'],retained)
            return {'schema':'formalization-input/1','context_id':context['id'],'inputs':inputs,
                'sources':[self._artifact(n) for n in context['artifact_ids']
                           if n != inputs.get('feature_certificate_id')], **reporting, **availability}
        target=self._artifact(inputs['formalization_id'])
        body=target['body']
        require(target['origin']=='worker' and type(body) is dict and body.get('schema')=='formalization-record/2',
            'Review target must be a retained formalization')
        job=self._job(target['job_id'])
        require(job['state']=='completed' and job['result_id']==target['id'] and job['spec']['kind']=='formalization/v1',
            'Review target must be the accepted completed formalization result')
        require(inputs.get('paired_contract') == job['spec'].get('research_inputs',{}).get('paired_contract'),
            'Review must preserve the original reporting contract')
        require(inputs.get('feature_certificate_id') == job['spec'].get('research_inputs',{}).get('feature_certificate_id'),
            'Review must preserve the original availability evidence identity')
        if 'research_epoch_id' in job['spec']:
            require(spec['research_epoch_id']==job['spec']['research_epoch_id'],
                'Review must use the formalization original epoch; a new epoch cannot reset its budget')
        if spec['allowed_workers'][0]==target['creator']:raise Denied('Formalizer cannot independently review its own artifact')
        allowed={target['id'],body['idea_id'],body['catalog_id'],*definitions}
        catalog=self._artifact(body['catalog_id'])
        candidate=body['candidate']
        universe=candidate.get('test_universe',{}) if type(candidate) is dict else {}
        snapshot_id=universe.get('data_snapshot_ref') if type(universe) is dict else None
        availability = availability_packet(self,context,inputs,catalog['id'],retained,target)
        if availability:
            allowed.update((availability['availability_evidence']['certificate_id'],
                            availability['availability_evidence']['data_snapshot_id']))
        public_target=None
        # Retained DATA_GAP drafts may contain arbitrary untrusted references.
        # Such text cannot become an existence/schema oracle outside the original
        # authorization snapshot merely because a reviewer inspects the draft.
        if (type(snapshot_id) is str and snapshot_id in target['source_refs']
                and snapshot_id in body['authorization_snapshot']
                and self._declared_definition_origins(retained,catalog['id'],snapshot_id)):
            public_target=self._public_data_target(snapshot_id)
            allowed.add(snapshot_id)
            if snapshot_id not in context['artifact_ids']:raise Denied('Review requires the original public data-target declaration')
        if not set(context['artifact_ids'])<=allowed:raise Denied('Review context contains unrelated material')
        if body['catalog_id'] not in context['artifact_ids']:raise Denied('Review catalog is outside the frozen context')
        if public_target is None:
            check_definition_origins(retained,catalog['id'],snapshot_id)
        required_refs=candidate.get('feature_refs',[]) if type(candidate) is dict else []
        strings(required_refs,'candidate feature references')
        require(set(required_refs)<=set(defined),'Review requires explicit meanings for every referenced feature')
        for ref in required_refs:
            require(canonical({n:defined[ref][n] for n in ('type','unit')})==canonical(catalog['body']['features'][ref]),
                'Review definitions differ from the retained catalog')
        return {'schema':'semantic-review-input/1','context_id':context['id'],'inputs':inputs,
            'formalization':target,'catalog':catalog,'definitions':retained,
            **reporting,
            **availability,
            **({'data_target':public_target} if public_target is not None else {}),
            'qualification':'Assess meaning independently; supplied mappings are formalizer assertions. No assessment outcomes are supplied.'}

    def _record_formalization(self, actor, lease, idea_id, catalog_id, candidate, semantic_report, provider_call_id=None):
        if self._job(lease['job_id'])['spec'].get('research_inputs',{}).get('paired_contract')!=CONTRACT:
            return super()._record_formalization(actor,lease,idea_id,catalog_id,candidate,semantic_report,provider_call_id)
        job = self._owned(actor, lease)
        if actor['role'] != 'formalizer' or job['spec']['kind'] != 'formalization/v1':
            raise Denied('Formalization requires its own formalizer capability')
        if 'research_call_profile' in job['spec']:
            _,_,output=self._auxiliary_response(actor,job,provider_call_id)
            inputs=job['spec']['research_inputs']
            if (idea_id!=inputs['idea_id'] or catalog_id!=inputs['catalog_id'] or set(output)!={'status','candidate','semantic_report'}
                    or canonical(output['candidate'])!=canonical(candidate)
                    or canonical(output['semantic_report'])!=canonical(semantic_report)):
                raise Invalid('Formalization must preserve the exact task and recorded provider output')
        elif provider_call_id is not None:
            raise Invalid('Provider provenance requires an epoch-bound auxiliary job')
        text(idea_id, 'idea_id')
        text(catalog_id, 'catalog_id')
        context = self._context(job['spec']['context_id'])
        allowed = self._attempt_sources(actor, job, context)
        if idea_id not in allowed or catalog_id not in allowed:
            raise Denied('Idea or catalog unavailable to this frozen capability')
        idea, catalog = self._artifact(idea_id)['body'], self._artifact(catalog_id)['body']
        validate_inputs(idea, catalog)
        assessment = assess_candidate(idea_id, idea['content']['text'], candidate,
                                      semantic_report, catalog['features'], allowed,
                                      definitions_from_sources([self._artifact(ref) for ref in allowed],
                                          job['spec']['research_inputs']['definition_ids'], catalog_id))
        body = {'schema': SCHEMA, 'paired_contract': CONTRACT,
                'definition_ids': job['spec']['research_inputs']['definition_ids'], 'idea_id': idea_id, 'catalog_id': catalog_id,
                'original_idea': idea, 'candidate': candidate, 'semantic_report': semantic_report,
                'authorization_snapshot': sorted(allowed),
                'created_at': datetime.fromtimestamp(self._now(), timezone.utc).isoformat().replace('+00:00', 'Z'),
                'assessment': assessment, 'scientific_readiness': False}
        try:
            saved = self._worker_artifact(actor, job, context, body, [idea_id, catalog_id])
        except Invalid as exc:
            if str(exc).startswith(('Payload exceeds', 'JSON nesting exceeds')):
                raise Invalid('RESOURCE_GAP: retained formalization envelope exceeds the local size/depth admission bound; no draft committed') from exc
            raise
        issue = assessment['gap']
        if issue:
            content = {'text': 'Retained formalization draft ' + saved['id'],
                       'reason': issue['code'] + ': ' + issue['reason'],
                       'reopen_condition': issue['reopen_condition']}
        else:
            content = {'text': 'Structurally checked formalization draft ' + saved['id'],
                       'uncertainty': 'Semantic fidelity, certification and scientific readiness remain unverified',
                       'measurement': saved['id']}
        journal = self._record_research(actor, lease, 'gap' if issue else 'observation', content,
                                        {}, [saved['id'], idea_id, catalog_id])
        self._event(actor['name'], 'formalization_recorded', artifact_id=saved['id'],
                    idea_id=idea_id, assessment=assessment, job_id=job['id'], generation=job['generation'])
        return {**saved, 'journal_id': journal['id'], 'assessment': assessment, 'scientific_readiness': False}

    def _submit(self, actor, lease, artifact_id):
        if self._job(lease['job_id'])['spec'].get('research_inputs',{}).get('paired_contract')!=CONTRACT:
            return super()._submit(actor,lease,artifact_id)
        # A retry of the exact accepted/rejected delivery is safe after acknowledgement loss.
        if type(lease) is dict and set(lease) == {'job_id', 'generation'}:
            prior = self._db.execute('SELECT * FROM attempts WHERE job_id=? AND generation=?',
                                     (lease['job_id'], lease['generation'])).fetchone()
            if prior and prior['owner'] == actor['name'] and prior['state'] in ('completed', 'rejected'):
                if prior['result_id'] != artifact_id:
                    raise Conflict('Attempt already submitted a different result')
                return decode(prior['detail'])
        job = self._owned(actor, lease)
        self._research_completion_check(job)
        result = self._artifact(artifact_id)
        if (result['origin'] != 'worker' or result['creator'] != actor['name']
                or result['job_id'] != job['id'] or result['generation'] != job['generation']):
            raise Denied('Result does not belong to this attempt')
        context = self._context(job['spec']['context_id'])
        sources = [self._artifact(ref) for ref in context['artifact_ids']]
        if job['spec']['kind'] in ('formalization/v1','semantic-review/v1'):
            sources = [self._artifact(ref) for ref in result['source_refs']]
        try:
            if job['spec']['kind']=='semantic-review/v1':
                body=result['body']
                expected=self._semantic_body(actor,job,body['call_id'],body['created_at'])
                if canonical(expected)!=canonical(body):raise Invalid('Semantic review differs from its owned input/response binding')
            message = paired_check(job['spec']['kind'], result['body'], sources)
            accepted = True
        except Invalid as exc:
            message, accepted = str(exc), False
        state = 'completed' if accepted else 'blocked'
        outcome = {'accepted': accepted, 'state': state, 'check': job['spec']['kind'],
                   'message': message, 'artifact_id': artifact_id, 'scientific_authority': False}
        self._finish_attempt(job, 'completed' if accepted else 'rejected', outcome, artifact_id)
        self._db.execute('UPDATE jobs SET state=?,result_id=?,detail=?,lease_until=NULL WHERE id=?',
                         (state, artifact_id if accepted else None, canonical(outcome), job['id']))
        self._event('controller', 'completion_checked', job_id=job['id'], generation=job['generation'], **outcome)
        return outcome

    def _meaning_target(self, identity):
        if self._artifact(identity)['body'].get('schema')!=SCHEMA:
            return super()._meaning_target(identity)
        target=self._artifact(text(identity,'formalization identity'))
        require(target['origin']=='worker' and target['body'].get('schema')=='formalization-record/2',
                'An owned formalization record is required')
        job=self._job(target['job_id'])
        require(job['spec']['kind']=='formalization/v1' and job['state']=='completed' and job['result_id']==identity,
                'Formalization must be the accepted completed result')
        self._deny_final_calibration_ancestry(target)
        validate_formalization(target['body'],[self._artifact(ref) for ref in target['source_refs']])
        return target,job

    def _meaning_inventory(self, target):
        if target['body'].get('schema')!=SCHEMA:
            return super()._meaning_inventory(target)
        jobs=[]
        refs={target['id'],*target['source_refs']}
        rows=self._db.execute('''SELECT id FROM job_specs WHERE json_extract(envelope,'$.kind')='semantic-review/v1'
            AND json_extract(envelope,'$.research_inputs.formalization_id')=? ORDER BY rowid''',(target['id'],)).fetchall()
        for row in rows:
            job=self._job(row[0])
            attempts=[{name:a[name] for name in ('generation','owner','state','result_id')}
                for a in self._db.execute('SELECT * FROM attempts WHERE job_id=? ORDER BY generation',(job['id'],))]
            calls=[]
            for call in self._db.execute('SELECT * FROM research_calls WHERE job_id=? ORDER BY rowid',(job['id'],)):
                invocation=self._db.execute('SELECT input_id,result_id FROM provider_invocations WHERE call_id=?',(call['id'],)).fetchone()
                entry={name:call[name] for name in ('id','epoch_id','generation','owner','state','request_id','response_id','receipt')}
                entry['invocation']=None if invocation is None else dict(invocation)
                calls.append(entry)
                refs.update(n for n in (call['request_id'],call['response_id']) if n)
                if invocation:refs.update(n for n in invocation if n)
            refs.update(a['result_id'] for a in attempts if a['result_id'])
            jobs.append({'id':job['id'],'spec':job['spec'],'state':job['state'],'generation':job['generation'],
                         'owner':job['owner'],'result_id':job['result_id'],'attempts':attempts,'calls':calls})
        return {'formalization_id':target['id'],'jobs':jobs,'policy':paired_policy_identity()},refs

