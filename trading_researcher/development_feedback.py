"""Closed development feedback; no scientific verdict or raw-result release."""
import hashlib
from pathlib import Path

from .codec import Invalid, canonical, decode, digest, integer, text
from .data_use import prior_knowledge
from .errors import Conflict, Denied


MANIFEST = 'development-feedback-manifest/1'
RELEASE = 'development-feedback-release/1'
AUTHORITY = 'descriptive_development_feedback_only'


def require(condition, message):
    if not condition:
        raise Invalid(message)


def collect_cohort(host, root_epoch_id):
    """Derive both perspectives and all linked attempts without changing state."""
    root = host._epoch(text(root_epoch_id, 'root research epoch'))
    specs = {row['id']: decode(row['envelope']) for row in host._db.execute('SELECT id,envelope FROM job_specs')}
    require(len(specs) <= 4096, 'Feedback inventory exceeds its job envelope')
    root_jobs = {identity for identity, spec in specs.items()
                 if spec.get('research_epoch_id') == root_epoch_id and spec['kind'] == 'research-record/v1'}
    workers = root['request']['workers']
    require(len(workers) == 2 and len(set(workers)) == 2 and len(root_jobs) == 2,
            'Feedback requires the complete two-perspective discovery cohort')
    require({tuple(specs[identity]['allowed_workers']) for identity in root_jobs}
            == {(worker,) for worker in workers}, 'Discovery identities differ from the root epoch')
    require(all(specs[identity]['context_id'] == root['request']['context_id'] for identity in root_jobs),
            'Discovery does not use the original shared frozen context')
    root_results, ideas = set(), set()
    for identity in root_jobs:
        job = host._job(identity)
        if job['result_id'] is None:
            continue  # A failed perspective remains in the job/attempt inventory.
        artifact = host._artifact(job['result_id'])
        body = artifact['body']
        require(artifact['origin'] == 'worker' and artifact.get('job_id') == identity
                and artifact['creator'] in specs[identity]['allowed_workers']
                and type(body) is dict and body.get('schema') == 'research-record/1'
                and body.get('kind') in ('idea','gap'), 'Unexpected original discovery result')
        root_results.add(artifact['id'])
        if body['kind'] == 'idea':
            ideas.add(artifact['id'])

    # Restrict the forward linkage to owned workflow fields. Shared raw data alone
    # never imports an unrelated research epoch into this checkpoint.
    records = {}
    for row in host._db.execute('''SELECT id FROM artifacts WHERE
            json_extract(envelope,'$.job_id') IS NOT NULL OR
            json_extract(envelope,'$.body.schema') IN
            ('compiled-hypothesis/1','reference-execution/1','data-use-assessment/1','semantic-review-assessment/1')'''):
        artifact = host._artifact(row['id'])
        records[artifact['id']] = artifact
        body = artifact['body']
        if (artifact.get('job_id') in root_jobs and type(body) is dict
                and body.get('schema') == 'research-record/1' and body.get('kind') == 'idea'):
            require(artifact['origin'] == 'worker'
                    and artifact['creator'] in specs[artifact['job_id']]['allowed_workers'],
                    'Unexpected retained discovery idea')
            # A final result does not supersede earlier ideas or erase their
            # separately attempted formalizations from the feedback cohort.
            ideas.add(artifact['id'])
    require(len(records) <= 10000, 'Feedback inventory exceeds its artifact envelope')
    selected, epochs, roots = set(root_jobs), {root_epoch_id}, set(root_results)
    formalizations, compiled = set(), set()
    for _ in range(32):
        before = (len(selected), len(epochs), len(roots))
        for identity, artifact in records.items():
            body = artifact['body']
            if artifact.get('job_id') in selected:
                roots.add(identity)
            if type(body) is not dict:
                continue
            schema = body.get('schema')
            if (schema == 'formalization-record/1' and body.get('idea_id') in ideas
                    and artifact['origin'] == 'worker'):
                require(artifact.get('job_id') in specs
                    and specs[artifact['job_id']]['kind'] == 'formalization/v1', 'Unbound formalization record')
                roots.add(identity); formalizations.add(identity); selected.add(artifact['job_id'])
            if artifact['creator'] != 'controller' or artifact['origin'] != 'controller':
                continue
            if (schema == 'compiled-hypothesis/1'
                    and body.get('dependency_arguments',{}).get('formalization_id') in formalizations):
                roots.add(identity); compiled.add(identity)
            if ((schema in ('reference-execution/1','data-use-assessment/1') and body.get('compiled_id') in compiled)
                    or (schema == 'semantic-review-assessment/1' and body.get('formalization_id') in formalizations)):
                roots.add(identity)
        for identity, spec in specs.items():
            inputs = spec.get('research_inputs', {})
            if (identity in selected or spec.get('research_epoch_id') in epochs
                    or inputs.get('idea_id') in ideas or inputs.get('formalization_id') in formalizations):
                require(spec.get('research_epoch_id') is not None, 'Related research job has no epoch')
                selected.add(identity); epochs.add(spec['research_epoch_id'])
        if before == (len(selected), len(epochs), len(roots)):
            break
    else:
        raise Invalid('Feedback linkage exceeds its bounded closure')
    require(len(selected) <= 256 and len(epochs) <= 32, 'Feedback checkpoint is too large')
    jobs, contexts, batch_ids = [], set(), set()
    now = host._now()
    for identity in sorted(selected):
        job = host._job(identity); spec = job['spec']
        terminal = job['state'] in ('completed','failed') or (job['state'] == 'blocked'
            and (spec['deadline'] <= now or job['generation'] >= spec['max_attempts']))
        require(terminal, 'Feedback cannot publish active or resumable work')
        batch_ids.add(job['batch_id']); contexts.add(spec['context_id'])
        attempts = [dict(row) for row in host._db.execute(
            'SELECT * FROM attempts WHERE job_id=? ORDER BY generation', (identity,))]
        require(all(item['ended_at'] is not None for item in attempts), 'Feedback includes an unresolved attempt')
        for item in attempts:
            item['detail'] = decode(item['detail'])
            if item['result_id']:
                roots.add(item['result_id'])
        if job['result_id']:
            roots.add(job['result_id'])
        jobs.append({key: job[key] for key in ('id','state','generation','owner','result_id','detail','batch_id')}
            | {'spec_sha256':digest(spec),'context_id':spec['context_id'],'kind':spec['kind'],
               'epoch_id':spec['research_epoch_id'],'deadline':spec['deadline'],'max_attempts':spec['max_attempts'],
               'attempts':attempts})
    batches = [dict(host._db.execute('SELECT * FROM batches WHERE id=?', (identity,)).fetchone())
               for identity in sorted(batch_ids)]
    require(all(batch['sealed'] == 1 for batch in batches), 'Feedback needs sealed source batches')
    for batch in batches:
        members = {row[0] for row in host._db.execute('SELECT id FROM job_specs WHERE batch_id=?',(batch['id'],))}
        require(members <= selected, 'Feedback cannot omit another member of a source batch')
    calls, epoch_inventory = [], []
    for identity in sorted(epochs):
        epoch = host._epoch(identity); usage = host._call_usage(identity)
        profile = epoch['request']['profile']
        require(epoch['state'] == 'halted' or now >= epoch['created_at'] + profile['max_seconds']
            or usage['calls'] >= profile['max_calls'], 'Research epoch still admits new model calls')
        contexts.add(epoch['request']['context_id'])
        epoch_inventory.append({'id':identity,'created_at':epoch['created_at'],'state':epoch['state'],
            'request_sha256':digest(epoch['request']),'usage':usage})
        for row in host._db.execute('SELECT * FROM research_calls WHERE epoch_id=? ORDER BY rowid',(identity,)):
            require(row['state'] == 'recorded' and row['job_id'] in selected,
                    'Feedback includes an unsettled or omitted model call')
            require(row['request_id'] is not None and row['response_id'] is not None, 'Model call lacks retained public records')
            roots.update((row['request_id'], row['response_id']))
            calls.append({key:row[key] for key in ('id','epoch_id','job_id','generation','owner','state',
                'request_id','response_id','charged_tokens','charged_cost')}
                | {'receipt_sha256':digest(decode(row['receipt'])) if row['receipt'] is not None else None})
    bound = [item for item in host._bound_attempts() if item['input_ref'] in roots]
    require(all(item['state'] != 'STARTED' for item in bound), 'Feedback includes an unresolved computation')
    for item in bound:
        roots.update(ref for ref in (item['artifact_id'],item['retained_input_id']) if ref)
    context_exposure = set()
    for identity in contexts:
        context = host._context(identity)
        context_exposure.update(context['exposure'])
        roots.update(context['artifact_ids'])
        roots.update(ref for ref in context['exposure']
            if host._db.execute('SELECT 1 FROM artifacts WHERE id=?',(ref,)).fetchone())
    all_ids, unresolved = set(), {ref for ref in context_exposure
        if not host._db.execute('SELECT 1 FROM artifacts WHERE id=?',(ref,)).fetchone()}
    for identity in sorted(roots):
        artifact = host._artifact(identity)
        host._deny_final_calibration_ancestry(artifact)
        knowledge = prior_knowledge(host,artifact)
        if knowledge['protected_knowledge_ids'] or knowledge['operations_knowledge_ids']:
            raise Denied('Feedback includes protected or uncontrolled operations knowledge')
        all_ids.update(knowledge['artifact_ids']); unresolved.update(knowledge['unresolved_exposure_refs'])
        require(len(all_ids) <= 4096, 'Feedback ancestry exceeds its bounded envelope')
    return {'schema':'development-feedback-cohort/1','root_epoch_id':root_epoch_id,
        'root_result_ids':sorted(root_results),'idea_ids':sorted(ideas),'epoch_ids':sorted(epochs),
        'job_ids':sorted(selected),'batch_ids':sorted(batch_ids),'artifact_ids':sorted(all_ids),
        'jobs':jobs,'batches':batches,'calls':calls,'epochs':epoch_inventory,'bound_attempts':bound,
        'unresolved_exposure_refs':sorted(unresolved),'scientific_readiness':False,
        'qualification':'Complete current closed-development workflow metadata; no publication or scientific authority.'}


def _owned(host, identity, schema, authority=AUTHORITY, data_class='development'):
    artifact = host._artifact(text(identity, 'feedback input identity'))
    require(artifact['creator'] == artifact['origin'] == 'controller'
        and artifact['data_class'] == data_class and artifact['authority'] == authority
        and type(artifact['body']) is dict and artifact['body'].get('schema') == schema,
        'Owned development feedback input required')
    return artifact


def _evidence(host, actor, request, *, read_cases):
    authority = 'descriptive_reference_computation_only'
    execution = _owned(host, request['execution_id'], 'reference-execution/1', authority)
    body = execution['body']
    require(body['status'] == 'DESCRIPTIVE_EXECUTION' and body['scientific_readiness'] is False,
            'Feedback requires a descriptive execution')
    compiled = _owned(host, body['compiled_id'], 'compiled-hypothesis/1', authority)
    require(compiled['body']['status'] == 'COMPILED'
        and body['data_snapshot_id'] == compiled['body']['data_snapshot_id'], 'Execution target differs')
    snapshot = host._data_snapshot(body['data_snapshot_id'])
    require(snapshot['data_class'] == 'development' and snapshot['body']['manifest']['partition'] == 'development',
            'Feedback cannot publish protected outcomes')
    for artifact in (execution, compiled):
        host._deny_final_calibration_ancestry(artifact)
        host._require_usable_dependencies(artifact['id'])
        knowledge = prior_knowledge(host, artifact)
        if knowledge['protected_knowledge_ids'] or knowledge['operations_knowledge_ids']:
            raise Denied('Feedback evidence includes protected or uncontrolled operations knowledge')
    meaning = _owned(host, request['meaning_review_assessment_id'], 'semantic-review-assessment/1',
                     'meaning_review_process_not_scientific_evidence', data_class='work_product')
    require(meaning['body']['formalization_id'] == compiled['body']['dependency_arguments']['formalization_id'],
            'Feedback meaning review targets another formalization')
    data_use = host._inspect_data_use(actor, request['data_use_assessment_id'], compiled_id=compiled['id'])
    review = host._inspect_meaning_review(actor, meaning['id'])
    require(data_use['qualified_exploration_data_use'] == 'SATISFIED'
        and review['current'] is True and review['independent_semantic_review'] == 'SATISFIED',
        'Feedback needs current qualified data use and independent meaning review')
    result = body.get('result')
    require(type(result) is dict and {'report','case_blob','contrast','compilation_hash','scientific_readiness'} <= set(result),
            'Feedback result is malformed')
    report = result['report']; descriptor = result['case_blob']
    require(type(report) is dict and {'processing_complete','scientific_readiness','request','processed_case_count'} <= set(report)
        and type(result['contrast']) is dict and type(descriptor) is dict and set(descriptor) == {'sha256','size'},
        'Feedback report or case descriptor is malformed')
    require(report['processing_complete'] is True and result['scientific_readiness'] is False
        and report['scientific_readiness'] is False and result['contrast'].get('scientific_readiness') is False,
        'Feedback requires complete descriptive computation')
    require(result['compilation_hash'] == digest(compiled['body']['compilation'])
        and digest(report['request']) == digest(compiled['body']['compilation']['request']),
        'Feedback result differs from the retained compilation')
    verification = body.get('verification')
    require(type(verification) is dict and {'mode','result'} <= set(verification),
            'Feedback verification is malformed')
    expected = {'schema':'bound-case-verification/1','result_hash':digest(result),
        'compilation_hash':result['compilation_hash'],'case_blob':descriptor,
        'checked_cases':report['processed_case_count'],'scientific_readiness':False}
    require(verification['mode'] == 'verify' and verification['result'] == expected
        and execution['blob_refs'] == [descriptor['sha256']], 'Feedback lacks exact separate case verification')
    if read_cases:
        require(len(host._read_blob_bytes(descriptor['sha256'])) == descriptor['size'],
                'Feedback case blob size differs')
    return execution, {'data_use':data_use,'meaning_review':review,'case_verification':expected}


def _save(host, body, refs, exposure, target_epoch):
    return host._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
        'data_class':'development','authority':AUTHORITY,'body':body,
        'source_refs':sorted(set(refs)),'exposure':sorted(set(exposure) | set(refs)),
        'not_before_epoch':target_epoch})


def publish_feedback(host, actor, root_epoch_id, execution_id, data_use_assessment_id,
                     meaning_review_assessment_id, target_epoch):
    """Called only inside the authenticated broker transaction; all four or none."""
    if actor['role'] != 'operator':
        raise Denied('Only the operator may publish development feedback')
    request = {'root_epoch_id':text(root_epoch_id,'root epoch'),'execution_id':text(execution_id,'execution'),
        'data_use_assessment_id':text(data_use_assessment_id,'data use'),
        'meaning_review_assessment_id':text(meaning_review_assessment_id,'meaning review'),
        'target_epoch':integer(target_epoch,'target epoch')}
    # An acknowledgement retry returns the historical snapshot. New work never
    # rewrites it; a different execution requires its own complete snapshot.
    rows = host._db.execute("""SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?
        AND json_extract(envelope,'$.body.request.root_epoch_id')=?
        AND json_extract(envelope,'$.body.request.execution_id')=?""",(MANIFEST,root_epoch_id,execution_id)).fetchall()
    require(len(rows) <= 1, 'Ambiguous feedback checkpoint publication')
    if rows:
        manifest = _owned(host, rows[0][0], MANIFEST)
        if manifest['body']['request'] != request:
            raise Conflict('Published checkpoint inputs and target epoch are immutable')
        grants = host._db.execute("""SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?
            AND json_extract(envelope,'$.body.manifest_id')=?""",(RELEASE,manifest['id'])).fetchall()
        require(len(grants) == 1, 'Feedback checkpoint lacks its unique atomic release')
        grant = _owned(host, grants[0][0], RELEASE)
        return {**{key:grant['body'][key] for key in ('manifest_id','observation_id','experience_id')},'grant_id':grant['id']}
    cohort = collect_cohort(host, root_epoch_id)
    require({execution_id,data_use_assessment_id,meaning_review_assessment_id} <= set(cohort['artifact_ids']),
            'Feedback evidence is outside the closed discovery cohort')
    require(all(target_epoch > batch['epoch'] for batch in cohort['batches']),
            'Feedback must become available in a later epoch')
    execution, evidence = _evidence(host, actor, request, read_cases=True)
    refs = cohort['artifact_ids']
    exposure = set(refs) | set(cohort['unresolved_exposure_refs'])
    now = host._now()
    require(all(host._artifact_availability(host._artifact(ref)) <= now for ref in refs),
            'Feedback has future-dated source records')
    retained = []
    for identity in refs:
        artifact = host._artifact(identity)
        body = artifact['body']
        if (type(body) is dict and body.get('schema') == 'research-record/1'
                and body.get('kind') in ('idea','gap')):
            retained.append({key:artifact[key] for key in ('id','creator','authority','body','source_refs','exposure')})
    manifest = _save(host, {'schema':MANIFEST,'created_at':now,'request':request,'cohort':cohort,
        'publisher_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'retained_research_records':retained,
        'evidence_at_publication':evidence,'scientific_readiness':False,
        'qualification':'Closed development snapshot including failures; neither independent confirmation nor economic or scientific evidence.'},
        refs, exposure, target_epoch)
    scope = {'root_epoch_id':root_epoch_id,'execution_id':execution_id,'manifest_id':manifest['id'],
             'evidence_class':'descriptive_development_only'}
    result = execution['body']['result']
    measurement = canonical({'execution_id':execution_id,'processed_case_count':result['report']['processed_case_count'],
        'contrast':result['contrast'],'case_blob':result['case_blob']})
    contents = [('observation', {'text':'Completed development computation with all original ideas, attempts and gaps retained.',
        'measurement':measurement,
        'uncertainty':'Descriptive only. Unknown training exposure and exposed history remain inherited; no calibrated inference or economic conclusion.'}),
        ('research_experience', {'text':'This closed development checkpoint is available as qualified research feedback.',
        'interpretation':'The recorded result describes the exact original scope. An information gap is not falsification; a computed effect is not independent confirmation.',
        'uncertainty':'No scientific or economic conclusion follows. Source failures and later exposure remain part of any descendant idea. Reassess on changed meaning/data-use evidence or technical revocation.',
        'next_action':'Consult the exact manifest, retained gaps and original meaning before a separately admitted continuation; do not silently tune the claim.'})]
    records = []
    for kind, content in contents:
        body = host._make_record(kind, content, scope, {'depends_on':[manifest['id']]}, None)
        record = _save(host, body, [manifest['id']], exposure | {manifest['id']}, target_epoch)
        host._index_record(record['id'], body)
        records.append(record['id'])
    grant = _save(host, {'schema':RELEASE,'manifest_id':manifest['id'],'observation_id':records[0],
        'experience_id':records[1],'target_epoch':target_epoch,'created_at':host._now(),'scientific_readiness':False},
        [manifest['id'],*records], exposure | {manifest['id'],*records}, target_epoch)
    host._event(actor['name'],'development_feedback_published',manifest_id=manifest['id'],grant_id=grant['id'])
    return {'manifest_id':manifest['id'],'observation_id':records[0],'experience_id':records[1],'grant_id':grant['id']}


def _check_grant(host, grant, epoch, research_time):
    body = grant['body']
    require(set(body) == {'schema','manifest_id','observation_id','experience_id','target_epoch','created_at','scientific_readiness'}
        and body['scientific_readiness'] is False, 'Invalid development feedback release')
    if epoch < integer(body['target_epoch'],'release epoch') or research_time < integer(body['created_at'],'release time'):
        raise Denied('Development feedback is unavailable at this epoch or research time')
    manifest = _owned(host, body['manifest_id'], MANIFEST)
    require(manifest['body']['request']['target_epoch'] == body['target_epoch']
        and manifest['body']['scientific_readiness'] is False
        and grant['source_refs'] == sorted({body['manifest_id'],body['observation_id'],body['experience_id']}),
        'Feedback release bindings differ')
    for key,kind in (('observation_id','observation'),('experience_id','research_experience')):
        record = _owned(host, body[key], 'research-record/1')
        require(record['body']['kind'] == kind and record['source_refs'] == [manifest['id']]
            and record['body']['scope']['manifest_id'] == manifest['id'], 'Feedback typed record differs')
    host._require_usable_dependencies(grant['id'])
    _evidence(host, None, manifest['body']['request'], read_cases=True)
    return grant


def released_feedback(host, artifact, epoch, research_time):
    if (artifact.get('authority') != AUTHORITY or type(artifact['body']) is not dict
            or artifact['body'].get('schema') not in ('research-record/1',MANIFEST)):
        return None
    rows = host._db.execute("""SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?
        AND (json_extract(envelope,'$.body.observation_id')=? OR json_extract(envelope,'$.body.experience_id')=?
            OR json_extract(envelope,'$.body.manifest_id')=?)""",
        (RELEASE,artifact['id'],artifact['id'],artifact['id'])).fetchall()
    require(len(rows) == 1, 'Feedback record lacks its unique owned release')
    return _check_grant(host, _owned(host,rows[0][0],RELEASE), epoch, research_time)


def check_context(host, context):
    """Check grants inherited through later records too, without changing history."""
    exposed = set(context['exposure'])
    for row in host._db.execute("SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?",(RELEASE,)):
        if row[0] in exposed:
            _check_grant(host, _owned(host,row[0],RELEASE), context['epoch'], context['research_time'])
