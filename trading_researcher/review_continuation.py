"""D092 single review continuation, with untouched ordinary review semantics.

The trusted operator owns activation. Source/model content cannot authorize a
call. The spend-ledger fence survives registry rollback; no fence is refunded.
Legacy methods below are copied under exact source pins with only the epoch
relation replaced. Ordinary work delegates to the unchanged legacy methods.
"""
import hashlib
from pathlib import Path

from .auxiliary import (KINDS, require, request_for, reporting_contract,
    check_definition_origins, expression_contract, validate_review_record,
    validate_inputs, availability_packet)
from .codec import Invalid, canonical, decode, digest, strings, text
from .errors import Denied
from .meaning_reviews import PROTOCOL, PROMPT, policy_identity
from .epoch_budget import _ledger, _schema
from .openai_provider import MODEL, cost_bound, wire_request

POLICY = 'independent-review-continuation/1.0'
APPROVAL = 'SESSION-2026-10-29-INDEPENDENT-BTC-REVIEW'
SPEC = 'docs/architecture/21_INDEPENDENT_REVIEW_CONTINUATION.md'
TARGET = 'c6b85475ab4a4b4a2657d46ecbe8b0a1517ae45fcf8de389345e65904ca91415'
ORIGINAL_EPOCH = '83a7e355615d4354a19bcc61a9406370'
ORIGINAL_USAGE = {'calls': 1, 'tokens': 41192, 'cost_units': 228597500}
WIRE_SHA256 = 'd530b6e8cba693933cb8270f8b442bb94f9b6ba7dc8faef042971a796869c9d4'
COST_CAP = 150000000
AGGREGATE_CAP = 5000000000
# Exact specification and original-source pins are inserted at adoption.
SPEC_SHA256 = 'a52036de9c386cd37480a13524fff81a00dea3bbd67d36fa87a6e45878b586d6'
LEGACY_SOURCES = {'meaning_reviews.py': 'a0669647d08578bbf07a16f8a849905c31eed689fccf6bef5ba30e142bfe61ee', 'auxiliary.py': '975f4eff94f10bd89b1daf879cc4b62b2d4cb363e1d1d5a2c08517619ecfd13a', 'formalization.py': '857d53bc9c5b84a89329b2857e525a011ad01e841171c5dc7adc252309cc7696'}


def pins():
    root = Path(__file__).resolve().parents[1]
    require(hashlib.sha256((root / SPEC).read_bytes()).hexdigest() == SPEC_SHA256,
            'Approved review continuation specification changed')
    require(policy_identity()['sources'] == LEGACY_SOURCES,
            'The continuation needs its exact unchanged legacy review implementation')


def template(spec):
    return {key: value for key, value in spec.items() if key not in ('research_epoch_id', 'deadline')}


def original(host):
    target, job = host._meaning_target(TARGET)
    require(job['spec'].get('research_epoch_id') == ORIGINAL_EPOCH
            and target['body']['assessment']['status'] == 'STRUCTURE_CHECKED', 'Original target/epoch differs')
    require(host._call_usage(ORIGINAL_EPOCH) == ORIGINAL_USAGE, 'Original usage changed; no reset is allowed')
    calls = [dict(row) for row in host._db.execute(
        'SELECT * FROM research_calls WHERE epoch_id=? ORDER BY rowid', (ORIGINAL_EPOCH,))]
    require(len(calls) == 1 and calls[0]['state'] == 'recorded' and calls[0]['job_id'] == job['id'],
            'Original formalization call is incomplete or differs')
    return {'target_id': TARGET, 'epoch_id': ORIGINAL_EPOCH, 'usage': ORIGINAL_USAGE,
            'epoch_request_sha256': digest(host._epoch(ORIGINAL_EPOCH)['request']), 'calls_sha256': digest(calls)}


def validate(host, context, profile, grant):
    pins()
    require(type(grant) is dict and set(grant) == {'policy', 'spec'} and grant['policy'] == POLICY,
            'Exact explicit review continuation required')
    spec = grant['spec']
    require(type(spec) is dict and template(spec) == spec and spec.get('kind') == 'semantic-review/v1'
            and type(spec.get('research_inputs')) is dict
            and spec['research_inputs'].get('formalization_id') == TARGET
            and type(spec.get('max_attempts')) is int and spec['max_attempts'] == 1,
            'Only the retained target review is authorized')
    target = host._artifact(TARGET)
    workers = spec.get('allowed_workers', [])
    require(type(workers) is list and len(workers) == 1 and workers[0] != target['creator'],
            'An independent reviewer identity is required')
    principal = host._db.execute('SELECT role FROM principals WHERE name=?', (workers[0],)).fetchone()
    require(principal is not None and principal['role'] == 'formalizer', 'Registered reviewer required')
    original(host)
    require(context['id'] == host._epoch(ORIGINAL_EPOCH)['request']['context_id'], 'Original base context required')
    selected = spec.get('research_call_profile', {})
    require(type(selected) is dict and selected.get('prompt_version') == PROTOCOL and selected.get('prompt') == PROMPT
            and selected.get('max_retries') == 0 and selected.get('model') == MODEL
            and selected.get('max_output_tokens') == 4000, 'Unchanged substantive independent review required')
    for name, value in {'model': MODEL, 'mode': 'live', 'currency': 'USD', 'max_calls': 1,
            'max_tokens': 40000, 'max_seconds': 600, 'max_cost_units': COST_CAP,
            'max_retries': 0, 'max_output_tokens': 4000}.items():
        require(type(profile.get(name)) is type(value) and profile[name] == value, 'Review-only bounds differ: ' + name)
    require(profile['tools'] == [] and not set(profile) & {'source_presentation', 'perspective_profiles'},
            'No discovery tools or alternative perspective settings are authorized')
    route = host._provider_routes.get(MODEL)
    _ledger(host)
    expected = {'openai_responses': route['config']}
    require(profile['generation_parameters'] == selected.get('generation_parameters') == expected,
            'Review settings differ from the host-selected route')
    require(route['config']['input_token_limit'] <= 36000 and route['config']['output_token_limit'] == 4000,
            'Review allocation exceeds the approved slots')
    # Full input validation before irreversible claim; this method retains every
    # original check and receives the actual prospective epoch relation explicitly.
    prospective = {**spec, 'research_epoch_id': 'prospective-continuation', 'deadline': host._now() + 600}
    review_context = host._spec_structure(prospective)
    from .auxiliary import validate_profile
    validate_profile(selected, profile)
    if spec.get('batch_id'):
        batch = host._db.execute('SELECT * FROM batches WHERE id=?', (spec['batch_id'],)).fetchone()
        require(batch is not None and not batch['sealed'] and batch['epoch'] == review_context['epoch'],
                'Review batch is absent, sealed or belongs to a different epoch')
    packet = host._continuation_packet(prospective, admission=grant)
    require(digest(wire_request(request_for(prospective, packet), route['config'])) == WIRE_SHA256,
            'The complete approved review wire changed')
    host._check_feedback_context(context)


def binding(host, epoch):
    return {'policy': POLICY, 'approval': APPROVAL, 'spec_sha256': SPEC_SHA256,
            'registry_identity': digest(str(host.directory.resolve())), 'epoch_id': epoch['id'],
            'created_at': epoch['created_at'], 'request_key': epoch['request_key'],
            'request_sha256': digest(epoch['request']), 'original': original(host)}


def row(host, epoch, db):
    found = db.execute('SELECT binding,calls,revoked FROM research_epoch_budget_grants WHERE approval=?', (APPROVAL,)).fetchone()
    if found is None or found[0] != canonical(binding(host, epoch)):
        raise Denied('No matching external one-use review authorization')
    return {'binding': decode(found[0]), 'calls': decode(found[1]), 'revoked': bool(found[2])}


def claim(host, epoch):
    with _ledger(host)._connect() as db:
        db.execute('BEGIN IMMEDIATE'); _schema(db)
        require(not db.execute('SELECT 1 FROM research_epoch_budget_grants WHERE approval=?', (APPROVAL,)).fetchone(),
                'One-use review authorization is already consumed')
        charges = db.execute('SELECT reserved,charged,state FROM dispatches').fetchall()
        require(all(state == 'settled' for _, _, state in charges)
                and sum(reserved if charged is None else charged for reserved, charged, _ in charges) + COST_CAP <= AGGREGATE_CAP,
                'Pending, unknown or insufficient shared budget')
        db.execute('INSERT INTO research_epoch_budget_grants VALUES(?,?,?,0)', (APPROVAL, canonical(binding(host, epoch)), '[]'))


def inspect(host, epoch):
    with _ledger(host)._connect() as db:
        if not db.execute("SELECT 1 FROM sqlite_master WHERE name='research_epoch_budget_grants'").fetchone():
            raise Denied('Review authorization ledger is missing')
        state = row(host, epoch, db)
        actual = [item[0] for item in host._db.execute(
            'SELECT id FROM research_calls WHERE epoch_id=? ORDER BY rowid', (epoch['id'],))]
        require(actual == [call['call_id'] for call in state['calls']],
                'External review fence differs from registry call history; reconciliation is required')
        return state


def relation(host, spec, target, original_job, admission=None):
    pins()
    require(target['id'] == TARGET and original_job['spec'].get('research_epoch_id') == ORIGINAL_EPOCH,
            'Continuation target or original epoch differs')
    if admission is None:
        epoch = host._epoch(spec['research_epoch_id'])
        grant = epoch['request'].get('review_continuation')
        inspect(host, epoch)  # Historical qualification survives administrative closure.
    else:
        grant = admission
    require(type(grant) is dict and grant.get('policy') == POLICY and template(spec) == grant.get('spec'),
            'Review differs from its exact approved relation')


def reserve(host, epoch, job, identity, input_bound, output_bound, cost):
    relation(host, job['spec'], *host._meaning_target(TARGET))
    require(0 < input_bound <= 36000 and output_bound == 4000 and input_bound + output_bound <= 40000
            and cost == cost_bound(input_bound, output_bound) and cost <= COST_CAP, 'Review reservation differs')
    with _ledger(host)._connect() as db:
        db.execute('BEGIN IMMEDIATE')
        state = row(host, epoch, db)
        require(not state['revoked'] and not state['calls'], 'One-use review slot is revoked or consumed')
        require(not host._db.execute('SELECT 1 FROM research_calls WHERE epoch_id=?', (epoch['id'],)).fetchone(),
                'Registry call history differs from the external review fence')
        charges = db.execute('SELECT reserved,charged,state FROM dispatches').fetchall()
        require(all(status == 'settled' for _, _, status in charges)
                and sum(reserved if charged is None else charged for reserved, charged, _ in charges) + cost <= AGGREGATE_CAP,
                'Shared budget cannot admit the review')
        calls = [{'call_id': identity, 'job_id': job['id'], 'input_bound': input_bound,
                  'output_bound': output_bound, 'cost_bound': cost}]
        db.execute('UPDATE research_epoch_budget_grants SET calls=? WHERE approval=?', (canonical(calls), APPROVAL))


def revoke(host, epoch):
    with _ledger(host)._connect() as db:
        db.execute('BEGIN IMMEDIATE'); row(host, epoch, db)
        db.execute('UPDATE research_epoch_budget_grants SET revoked=1 WHERE approval=?', (APPROVAL,))
    return {'epoch_id': epoch['id'], 'status': 'REVOKED', 'pending_calls_still_require_settlement': True}


class ReviewContinuation:
    def _auxiliary_packet_for_spec(self, spec):
        if spec.get('kind') == 'semantic-review/v1' and 'research_epoch_id' in spec:
            epoch = self._epoch(spec['research_epoch_id'])
            if 'review_continuation' in epoch['request']:
                return self._continuation_packet(spec)
        return super()._auxiliary_packet_for_spec(spec)

    def _meaning_inventory(self, target):
        inventory, refs = super()._meaning_inventory(target)
        original_epoch = self._job(target['job_id'])['spec'].get('research_epoch_id')
        if any(job['spec'].get('research_epoch_id') != original_epoch for job in inventory['jobs']):
            root = Path(__file__).parent
            inventory['policy'] = {'legacy': policy_identity(), 'continuation': POLICY,
                'spec_sha256': hashlib.sha256((root.parent / SPEC).read_bytes()).hexdigest(),
                'sources': {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                            for name in ('review_continuation.py', 'research_calls.py', 'coordination.py', 'epoch_budget.py')}}
            inventory['continuation_authorizations'] = []
            for job in inventory['jobs']:
                if job['spec'].get('research_epoch_id') == original_epoch:
                    continue
                try:
                    state = inspect(self, self._epoch(job['spec']['research_epoch_id']))
                    entry = {'job_id': job['id'], 'binding': state['binding'], 'calls': state['calls']}
                except (Invalid, Denied) as exc:
                    entry = {'job_id': job['id'], 'authorization_gap': str(exc)}
                inventory['continuation_authorizations'].append(entry)
        return inventory, refs

    def _calculate_meaning_assessment(self, target, original_job, inventory):
        if any(job['spec'].get('research_epoch_id') != original_job['spec'].get('research_epoch_id')
               for job in inventory['jobs']):
            return self._continuation_assessment(target, original_job, inventory)
        return super()._calculate_meaning_assessment(target, original_job, inventory)

    def _continuation_packet(self,spec,admission=None):
        require(spec['kind'] in KINDS and 'research_epoch_id' in spec,'An auxiliary job needs its original epoch')
        context=self._context(spec['context_id'])
        require(context['role']=='formalizer' and len(spec['allowed_workers'])==1,'Auxiliary work needs one scoped formalizer capability')
        inputs=spec.get('research_inputs')
        expected={'idea_id','catalog_id','definition_ids'} if spec['kind']=='formalization/v1' else {'formalization_id','definition_ids'}
        require(type(inputs) is dict and expected <= set(inputs) <= expected|{'reporting_contract','feature_certificate_id'},
            'Missing or unexpected typed auxiliary inputs')
        reporting = reporting_contract(inputs)
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
        require(target['origin']=='worker' and type(body) is dict and body.get('schema')=='formalization-record/1',
            'Review target must be a retained formalization')
        job=self._job(target['job_id'])
        require(job['state']=='completed' and job['result_id']==target['id'] and job['spec']['kind']=='formalization/v1',
            'Review target must be the accepted completed formalization result')
        require(inputs.get('reporting_contract') == job['spec'].get('research_inputs',{}).get('reporting_contract'),
            'Review must preserve the original reporting contract')
        require(inputs.get('feature_certificate_id') == job['spec'].get('research_inputs',{}).get('feature_certificate_id'),
            'Review must preserve the original availability evidence identity')
        relation(self, spec, target, job, admission)
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
            **expression_contract(candidate),
            **({'data_target':public_target} if public_target is not None else {}),
            'qualification':'Assess meaning independently; supplied mappings are formalizer assertions. No assessment outcomes are supplied.'}


    def _continuation_assessment(self, target, original_job, inventory):
        gaps=[];observed=[];accepted=0
        def gap(code, reason, **ids):gaps.append({'code':code,'reason':reason,**ids})
        if target['body']['assessment']['status']!='STRUCTURE_CHECKED':
            gap('FORMALIZATION_GAP','A faithful review of retained uncertainty does not make a candidate executable')
        if not inventory['jobs']:gap('NO_REVIEW_REGISTERED','No independent review job was declared for this exact target')
        for job in inventory['jobs']:
            spec=job['spec'];selected=spec['research_call_profile']
            qualified=(selected['prompt_version']==PROTOCOL and selected['prompt']==PROMPT)
            if not qualified:gap('REVIEW_PROTOCOL_GAP','The substantive comparison protocol was not frozen before the response',job_id=job['id'])
            if spec['research_epoch_id']!=original_job['spec'].get('research_epoch_id'):
                try:
                    relation(self, spec, target, original_job)
                except (Invalid, Denied) as exc:
                    gap('REVIEW_EPOCH_GAP', str(exc), job_id=job['id'])
            if job['state']!='completed':gap('REVIEW_INCOMPLETE','A declared review job has not completed',job_id=job['id'])
            valid_calls={}
            for call in job['calls']:
                if call['response_id'] is not None:
                    public=self._artifact(call['response_id'])['body']['response']
                    if public.get('status') in ('failed','timeout'):
                        observed.append({'job_id':job['id'],'call_id':call['id'],'status':'TRANSPORT_FAILURE_RETAINED'})
                        continue  # Existing bounded transport retries are not semantic opinions.
                try:
                    review,packet=self._historical_meaning_call(target,job,call)
                    valid_calls[call['id']]=(review,packet,call)
                    observed.append({'job_id':job['id'],'call_id':call['id'],
                        'invocation_id':call['invocation']['result_id'],'status':'HOST_OBSERVED_REVIEW',
                        'judgment':review['judgment']})
                    if review['judgment']!='faithful':
                        gap('MEANING_DIFFERENCE_OR_UNCERTAINTY','A retained review reports different or uncertain meaning',
                            job_id=job['id'],call_id=call['id'])
                except (Invalid,Denied) as exc:
                    gap('REVIEW_PROVENANCE_GAP',str(exc),job_id=job['id'],call_id=call['id'])
            if job['state']=='completed':
                try:
                    artifact=self._artifact(job['result_id']);body=artifact['body']
                    validate_review_record(body,[self._artifact(ref) for ref in artifact['source_refs']])
                    require(body['call_id'] in valid_calls,'Accepted review has no verified provider call')
                    review,packet,call=valid_calls[body['call_id']]
                    require(artifact['origin']=='worker' and artifact['creator']==job['owner']==call['owner']
                        and artifact['job_id']==job['id'] and artifact['generation']==job['generation']==call['generation']
                        and body['formalization_id']==target['id'] and body['idea_id']==target['body']['idea_id']
                        and body['reviewer_id']==call['owner'] and body['formalizer_id']==target['creator']
                        and body['input_hash']==digest(packet) and body['request_id']==call['request_id']
                        and body['response_id']==call['response_id'] and body['model']==selected['model']
                        and body['prompt_version']==selected['prompt_version'] and body['provider_mode']=='live'
                        and body['role_separation_checked'] is True and canonical(body['review'])==canonical(review),
                        'Completed review differs from its retained target, call or model response')
                    accepted+=1
                except (Invalid,Denied,KeyError,TypeError) as exc:
                    gap('REVIEW_COMPLETION_GAP',str(exc),job_id=job['id'])
        if accepted==0 and inventory['jobs']:gap('NO_VERIFIED_REVIEW_COMPLETION','No accepted review binds a verified direct call')
        satisfied=not gaps and accepted>0
        return {'status':'INDEPENDENT_REVIEW_SATISFIED' if satisfied else 'REVIEW_GAP',
            'independent_semantic_review':'SATISFIED' if satisfied else 'NOT_SATISFIED',
            'formalization_structure':target['body']['assessment']['status'],
            'review_observations':observed,'gaps':gaps}

