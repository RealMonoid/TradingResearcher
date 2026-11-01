"""Opt-in D097 native auxiliary routing; all original brokers stay unchanged."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path

from . import checks
from .auxiliary import (KINDS, check_definition_origins, require, reporting_contract)
from .auxiliary_availability import availability_packet
from .codec import Invalid, canonical, decode, strings, text
from .errors import Conflict, Denied
from .exact_formalization import (CONTRACT, SCHEMA, EXEC, EVALUATION, REPORTING,
                                  assess_candidate, validate_record)
from .formalization import validate_inputs
from .inquiry.resource_host import FiniteInquiryBroker

ROOT = Path(__file__).resolve().parents[1]
OWNER = 'docs/architecture/26_BOUNDED_EXACT_COMPOSITIONS.md'
OWNER_SHA256 = 'fcff34f14878773bd817155121a62212f934a07ba9cba57c3a7864777420418f'
DOCUMENTS = (OWNER, 'docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md',
    'docs/architecture/20_BOUNDED_MATH_REUSE.md','trading_researcher/REQUIRED_INPUTS.md',
    'trading_researcher/EXACT_COMPOSITIONS.md','trading_researcher/EXACT_RESEARCH.md')
FILES = ('trading_researcher/exact_research.py','trading_researcher/exact_formalization.py',
         'trading_researcher/exact_compositions.py','trading_researcher/exact_outcomes.py',*DOCUMENTS)
LOADED = {path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in FILES}


def selected(spec):
    inputs = spec.get('research_inputs')
    return type(inputs) is dict and inputs.get('expression_contract') == CONTRACT


def current_sources():
    current = {path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in FILES}
    require(current == LOADED and current[OWNER] == OWNER_SHA256,
            'Exact research sources changed; restart and independently requalify')
    return current


def contract_packet():
    sources = current_sources()
    # Preserve the original numerical/reporting owners' fixed source identities.
    from .certification import BOUNDED_PINS, REQUIRED_PINS
    from .auxiliary_views import REUSE_PATH, REUSE_SHA256
    for path,expected in {**BOUNDED_PINS,**REQUIRED_PINS,REUSE_PATH:REUSE_SHA256}.items():
        if path in DOCUMENTS:
            require(sources[path] == expected, 'An inherited exact research contract changed')
    return {'expression_contract':{'schema':CONTRACT,'candidate_schema':EXEC,
        'formalization_schema':SCHEMA,'evaluation_contract':EVALUATION,
        'reporting_contract':REPORTING,'documents':[
            {'path':path,'sha256':sources[path],'text':(ROOT/path).read_bytes().decode('utf-8')}
            for path in DOCUMENTS]}}


class ExactResearch:
    """Version-specific methods composed with the existing native controller."""

    def _breakout_research_sources(self):
        return {**super()._breakout_research_sources(),**current_sources()}

    def _auxiliary_packet_for_spec(self, spec):
        if not selected(spec):
            return super()._auxiliary_packet_for_spec(spec)
        require(spec['kind'] in KINDS and 'research_epoch_id' in spec,
                'An auxiliary job needs its original epoch')
        context = self._context(spec['context_id'])
        require(context['role'] == 'formalizer' and len(spec['allowed_workers']) == 1,
                'Auxiliary work needs one scoped formalizer capability')
        inputs = spec['research_inputs']
        expected = ({'idea_id','catalog_id','definition_ids'} if spec['kind'] == 'formalization/v1'
                    else {'formalization_id','definition_ids'})
        require(expected|{'expression_contract','reporting_contract'} <= set(inputs)
            <= expected|{'expression_contract','reporting_contract','feature_certificate_id'},
            'Missing or unexpected exact auxiliary inputs')
        require(inputs['reporting_contract'] == REPORTING, 'Exact research requires its fixed reporting contract')
        contracts = {**reporting_contract(inputs),**contract_packet()}
        definitions = strings(inputs['definition_ids'], 'definition_ids')
        require(len(definitions) <= 16, 'At most sixteen definition records may be supplied')
        identities = set(definitions)|{text(inputs[name],'auxiliary input identity') for name in expected-{'definition_ids'}}
        if 'feature_certificate_id' in inputs:
            identities.add(text(inputs['feature_certificate_id'],'feature certificate identity'))
        if not identities <= set(context['artifact_ids']):
            raise Denied('Auxiliary input is outside its frozen context')
        retained = [self._artifact(identity) for identity in definitions]
        defined = {}
        for artifact in retained:
            body = artifact['body']
            require(artifact['creator'] == 'controller' and artifact['data_class'] == 'development'
                and type(body) is dict and body.get('schema') == 'feature-definitions/1'
                and type(body.get('definitions')) is list, 'Owned development feature definitions required')
            for definition in body['definitions']:
                ref = definition['feature_ref']
                require(ref not in defined, 'Ambiguous duplicate feature definition')
                defined[ref] = definition
        if spec['kind'] == 'formalization/v1':
            idea,catalog = (self._artifact(inputs[name]) for name in ('idea_id','catalog_id'))
            validate_inputs(idea['body'],catalog['body'])
            check_definition_origins(retained,catalog['id'])
            availability = availability_packet(self,context,inputs,catalog['id'],retained)
            return {'schema':'formalization-input/1','context_id':context['id'],'inputs':inputs,
                'sources':[self._artifact(identity) for identity in context['artifact_ids']
                           if identity != inputs.get('feature_certificate_id')], **contracts, **availability}
        target = self._artifact(inputs['formalization_id'])
        body = target['body']
        require(target['origin'] == 'worker' and type(body) is dict and body.get('schema') == SCHEMA,
                'Review target must be a retained exact-composition formalization')
        job = self._job(target['job_id'])
        require(job['state'] == 'completed' and job['result_id'] == target['id']
            and job['spec']['kind'] == 'formalization/v1' and selected(job['spec']),
            'Review target must be the accepted completed exact formalization result')
        for key in ('expression_contract','reporting_contract','feature_certificate_id'):
            require(inputs.get(key) == job['spec']['research_inputs'].get(key),
                    'Review must preserve the original expression/reporting/availability contracts')
        require(definitions == job['spec']['research_inputs']['definition_ids'],
                'Review must preserve the exact original declared feature definitions')
        require(spec['research_epoch_id'] == job['spec'].get('research_epoch_id'),
                'Review must use the formalization original epoch; a new epoch cannot reset its budget')
        if spec['allowed_workers'][0] == target['creator']:
            raise Denied('Formalizer cannot independently review its own artifact')
        validate_record(body,[self._artifact(ref) for ref in target['source_refs']])
        allowed = {target['id'],body['idea_id'],body['catalog_id'],*definitions}
        catalog = self._artifact(body['catalog_id'])
        candidate = body['candidate']
        universe = candidate.get('test_universe',{}) if type(candidate) is dict else {}
        snapshot_id = universe.get('data_snapshot_ref') if type(universe) is dict else None
        availability = availability_packet(self,context,inputs,catalog['id'],retained,target)
        if availability:
            allowed.update((availability['availability_evidence']['certificate_id'],
                            availability['availability_evidence']['data_snapshot_id']))
        public_target = None
        # Untrusted retained references are never an existence/schema oracle.
        if (type(snapshot_id) is str and snapshot_id in target['source_refs']
                and snapshot_id in body['authorization_snapshot']
                and self._declared_definition_origins(retained,catalog['id'],snapshot_id)):
            public_target = self._public_data_target(snapshot_id)
            allowed.add(snapshot_id)
            if snapshot_id not in context['artifact_ids']:
                raise Denied('Review requires the original public data-target declaration')
        if not set(context['artifact_ids']) <= allowed:
            raise Denied('Review context contains unrelated material')
        if body['catalog_id'] not in context['artifact_ids']:
            raise Denied('Review catalog is outside the frozen context')
        if public_target is None:
            check_definition_origins(retained,catalog['id'],snapshot_id)
        required_refs = candidate.get('feature_refs',[]) if type(candidate) is dict else []
        strings(required_refs,'candidate feature references')
        require(set(required_refs) <= set(defined), 'Review requires explicit meanings for every referenced feature')
        for ref in required_refs:
            require(ref in catalog['body']['features'] and canonical({name:defined[ref][name] for name in ('type','unit')})
                == canonical(catalog['body']['features'][ref]), 'Review definitions differ from the retained catalog')
        return {'schema':'semantic-review-input/1','context_id':context['id'],'inputs':inputs,
            'formalization':target,'catalog':catalog,'definitions':retained,**contracts,**availability,
            **({'data_target':public_target} if public_target is not None else {}),
            'qualification':'Assess meaning independently; supplied mappings are formalizer assertions. No assessment outcomes are supplied.'}

    def _record_formalization(self, actor, lease, idea_id, catalog_id, candidate, semantic_report, provider_call_id=None):
        job = self._owned(actor,lease)
        if not selected(job['spec']):
            return super()._record_formalization(actor,lease,idea_id,catalog_id,candidate,semantic_report,provider_call_id)
        if actor['role'] != 'formalizer' or job['spec']['kind'] != 'formalization/v1':
            raise Denied('Formalization requires its own formalizer capability')
        current_sources()
        _,_,output = self._auxiliary_response(actor,job,provider_call_id)
        inputs = job['spec']['research_inputs']
        if (idea_id != inputs['idea_id'] or catalog_id != inputs['catalog_id']
                or set(output) != {'status','candidate','semantic_report'}
                or canonical(output['candidate']) != canonical(candidate)
                or canonical(output['semantic_report']) != canonical(semantic_report)):
            raise Invalid('Formalization must preserve the exact task and recorded provider output')
        text(idea_id,'idea_id');text(catalog_id,'catalog_id')
        context = self._context(job['spec']['context_id'])
        allowed = self._attempt_sources(actor,job,context)
        if idea_id not in allowed or catalog_id not in allowed:
            raise Denied('Idea or catalog unavailable to this frozen capability')
        idea,catalog = self._artifact(idea_id)['body'],self._artifact(catalog_id)['body']
        validate_inputs(idea,catalog)
        assessment = assess_candidate(idea_id,idea['content']['text'],candidate,semantic_report,catalog['features'],allowed)
        body = {'schema':SCHEMA,'expression_contract':CONTRACT,'evaluation_contract':EVALUATION,
            'reporting_contract':REPORTING,'idea_id':idea_id,'catalog_id':catalog_id,
            'original_idea':idea,'candidate':candidate,'semantic_report':semantic_report,
            'authorization_snapshot':sorted(allowed),
            'created_at':datetime.fromtimestamp(self._now(),timezone.utc).isoformat().replace('+00:00','Z'),
            'assessment':assessment,'scientific_readiness':False}
        try:
            saved = self._worker_artifact(actor,job,context,body,[idea_id,catalog_id])
        except Invalid as exc:
            if str(exc).startswith(('Payload exceeds','JSON nesting exceeds')):
                raise Invalid('RESOURCE_GAP: exact formalization envelope exceeds local size/depth bounds; no draft committed') from exc
            raise
        issue = assessment['gap']
        content = ({'text':'Retained formalization draft '+saved['id'],
                    'reason':issue['code']+': '+issue['reason'],'reopen_condition':issue['reopen_condition']} if issue else
            {'text':'Structurally checked formalization draft '+saved['id'],
             'uncertainty':'Semantic fidelity, certification and scientific readiness remain unverified','measurement':saved['id']})
        journal = self._record_research(actor,lease,'gap' if issue else 'observation',content,{},[saved['id'],idea_id,catalog_id])
        self._event(actor['name'],'formalization_recorded',artifact_id=saved['id'],idea_id=idea_id,
            assessment=assessment,job_id=job['id'],generation=job['generation'])
        return {**saved,'journal_id':journal['id'],'assessment':assessment,'scientific_readiness':False}

    def _submit(self, actor, lease, artifact_id):
        # Preserve the original safe acknowledgement-loss retry semantics.
        if type(lease) is dict and set(lease) == {'job_id','generation'}:
            prior = self._db.execute('SELECT * FROM attempts WHERE job_id=? AND generation=?',
                                    (lease['job_id'],lease['generation'])).fetchone()
            if prior and prior['owner'] == actor['name'] and prior['state'] in ('completed','rejected'):
                if prior['result_id'] != artifact_id:
                    raise Conflict('Attempt already submitted a different result')
                return decode(prior['detail'])
        job = self._owned(actor,lease)
        if not selected(job['spec']):
            return super()._submit(actor,lease,artifact_id)
        self._research_completion_check(job)
        current_sources()
        result = self._artifact(artifact_id)
        if (result['origin'] != 'worker' or result['creator'] != actor['name']
                or result['job_id'] != job['id'] or result['generation'] != job['generation']):
            raise Denied('Result does not belong to this attempt')
        sources = [self._artifact(ref) for ref in result['source_refs']]
        try:
            if job['spec']['kind'] == 'formalization/v1':
                validate_record(result['body'],sources)
                message = 'Exact structure and original source retention checked; no scientific authority'
            else:
                body = result['body']
                expected = self._semantic_body(actor,job,body['call_id'],body['created_at'])
                if canonical(expected) != canonical(body):
                    raise Invalid('Semantic review differs from its owned input/response binding')
                message = checks.validate(job['spec']['kind'],body,sources)
            accepted = True
        except Invalid as exc:
            message,accepted = str(exc),False
        state = 'completed' if accepted else 'blocked'
        outcome = {'accepted':accepted,'state':state,'check':job['spec']['kind'],
            'message':message,'artifact_id':artifact_id,'scientific_authority':False}
        self._finish_attempt(job,'completed' if accepted else 'rejected',outcome,artifact_id)
        self._db.execute('UPDATE jobs SET state=?,result_id=?,detail=?,lease_until=NULL WHERE id=?',
                        (state,artifact_id if accepted else None,canonical(outcome),job['id']))
        self._event('controller','completion_checked',job_id=job['id'],generation=job['generation'],**outcome)
        return outcome

    def _meaning_target(self, identity):
        target = self._artifact(text(identity,'formalization identity'))
        if type(target['body']) is not dict or target['body'].get('schema') != SCHEMA:
            return super()._meaning_target(identity)
        job = self._job(target['job_id'])
        require(target['origin'] == 'worker' and job['state'] == 'completed'
            and job['result_id'] == identity and job['spec']['kind'] == 'formalization/v1' and selected(job['spec']),
            'Formalization must be the accepted completed exact result')
        self._deny_final_calibration_ancestry(target)
        validate_record(target['body'],[self._artifact(ref) for ref in target['source_refs']])
        return target,job

    def _release_batch(self, actor, batch_id, target_epoch):
        result = super()._release_batch(actor,batch_id,target_epoch)
        # The legacy controller explicitly retains every scalar /1 draft.
        # Extend that same later-epoch release to /3 without changing old code.
        rows = self._db.execute('''SELECT a.id FROM artifacts a JOIN job_specs s
            ON json_extract(a.envelope,'$.job_id')=s.id
            WHERE s.batch_id=? AND json_extract(a.envelope,'$.origin')='worker'
            AND json_extract(a.envelope,'$.body.schema')=? ORDER BY a.rowid''',(batch_id,SCHEMA)).fetchall()
        added = []
        for row in rows:
            if self._db.execute('INSERT OR IGNORE INTO releases VALUES(?,?,?)',
                    (row['id'],target_epoch,batch_id)).rowcount:
                added.append(row['id'])
        if added:
            self._event(actor['name'],'exact_formalizations_released',batch_id=batch_id,
                        target_epoch=target_epoch,artifact_ids=added)
        if rows:
            result = {**result,'artifact_ids':sorted(set(result['artifact_ids'])|{row['id'] for row in rows})}
        return result

    def _meaning_inventory(self, target):
        inventory,refs = super()._meaning_inventory(target)
        if target['body'].get('schema') == SCHEMA:
            inventory = {**inventory,'policy':{**inventory['policy'],
                'expression_contract':CONTRACT,'exact_sources':current_sources()}}
        return inventory,refs


class ExactInquiryBroker(ExactResearch, FiniteInquiryBroker):
    """Explicit production entry point; funding and full qualification stay required."""
