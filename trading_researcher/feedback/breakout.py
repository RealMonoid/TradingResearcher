"""Static second-original publication adapter; no scientific authority.

The separately loaded publication adapter is outside the unchanged numerical
feature/evaluator source closure and checks its own identity at every use.
"""
import hashlib
from pathlib import Path

from ..codec import Invalid, canonical, decode, digest, integer, strings, text
from .paired import prior_knowledge as base_prior_knowledge
from ..errors import Conflict, Denied



from ..binding import hashes
from ..certification import _environment_current
from ..formalization import utc
from ..paired_breakout.research import BreakoutResearchBroker
from ..paired_breakout.host import EXECUTION_PROFILE
from ..paired_breakout import runtime, composition
from ..paired_breakout.composition import PROFILE
from ..revocations import SCHEMA as REVOCATION_SCHEMA, AUTHORITY as REVOCATION_AUTHORITY

LOADED_SELF = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def prior_knowledge(host, artifact):
    """Recognize only exact breakout package metadata in addition to prior paired metadata; retain full ancestry."""
    result = base_prior_knowledge(host, artifact)
    operations = []
    technical_ids = set(result['technical_provenance_ids'])
    bundle = runtime.read_bundle()
    expected = hashes(bundle)
    def package_matches(item):
        body = item['body']
        if (item['creator'] != 'controller' or item['origin'] != 'controller'
                or item['data_class'] != 'operations' or item['authority'] != 'retained_source_not_certified'
                or type(body) is not dict or set(body) != {'schema','profile','created_at','files','footprint','bootstrap_sha256'}):
            return False
        files = body['files']
        return (body['schema'] == 'paired-source-package/1' and body['profile'] == PROFILE
            and type(body['created_at']) is int and body['created_at'] >= 0
            and body['bootstrap_sha256'] == hashlib.sha256(runtime.BOOTSTRAP.encode()).hexdigest()
            and body['footprint'] == expected and type(files) is dict and set(files) == set(expected)
            and all(type(v) is dict and set(v) == {'sha256','size'} and v['sha256'] == expected[k]
                and type(v['size']) is int and v['size'] == len(bundle[k]) for k,v in files.items())
            and set(item.get('blob_refs',[])) == {v['sha256'] for v in files.values()}
            and not item['source_refs'] and not item['exposure'])
    for identity in result['operations_knowledge_ids']:
        item = host._artifact(identity); body = item['body']
        owned = item['creator'] == item['origin'] == 'controller' and item['data_class'] == 'operations'
        schema = body.get('schema') if type(body) is dict else None
        technical = False
        if owned and schema == 'paired-source-package/1' and item['authority'] == 'retained_source_not_certified':
            technical = package_matches(item)
        if not technical:
            operations.append(identity)
        else:
            technical_ids.add(identity)
    result['operations_knowledge_ids'] = operations
    result['technical_provenance_ids'] = sorted(technical_ids)
    return result

MANIFEST = 'paired-breakout-development-feedback-manifest/1'
RELEASE = 'paired-breakout-development-feedback-release/1'
AUTHORITY = 'paired_breakout_descriptive_feedback_only'


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
            ('compiled-hypothesis/1','reference-execution/1','data-use-assessment/1','semantic-review-assessment/1', 'paired-compiled-hypothesis/1','paired-reference-execution/1','paired-composition-certificate/1')'''):
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
            if (schema in ('formalization-record/1','formalization-record/2') and body.get('idea_id') in ideas
                    and artifact['origin'] == 'worker'):
                require(artifact.get('job_id') in specs
                    and specs[artifact['job_id']]['kind'] == 'formalization/v1', 'Unbound formalization record')
                roots.add(identity); formalizations.add(identity); selected.add(artifact['job_id'])
            if artifact['creator'] != 'controller' or artifact['origin'] != 'controller':
                continue
            if (schema == 'compiled-hypothesis/1'
                    and body.get('dependency_arguments',{}).get('formalization_id') in formalizations):
                roots.add(identity); compiled.add(identity)
            if schema == 'paired-compiled-hypothesis/1' and body.get('formalization_id') in formalizations:
                roots.add(identity); compiled.add(identity)
            if ((schema in ('reference-execution/1','data-use-assessment/1','paired-reference-execution/1','paired-composition-certificate/1') and body.get('compiled_id') in compiled)
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
    return {'schema':'paired-breakout-development-feedback-cohort/1','root_epoch_id':root_epoch_id,
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
    host._breakout_feedback_source_current()
    authority = 'paired_descriptive_development_only'
    execution = _owned(host, request['execution_id'], 'paired-reference-execution/1', authority)
    body = execution['body']
    require(body['status'] == 'DESCRIPTIVE_EXECUTION' and body['error'] is None
        and body['scientific_readiness'] is False
        and body.get('profile') == EXECUTION_PROFILE
        and body.get('host_sources') == host._breakout_source_identity(), 'Complete current breakout execution required')
    compiled, dependencies, payload = host._breakout_compiled(body['compiled_id'])
    require(body['data_snapshot_id'] == compiled['body']['data_snapshot_id'], 'Paired snapshot differs')
    for artifact in (execution, compiled):
        host._deny_final_calibration_ancestry(artifact)
        host._require_usable_dependencies(artifact['id'])
        knowledge = prior_knowledge(host, artifact)
        require(not knowledge['protected_knowledge_ids'] and not knowledge['operations_knowledge_ids'],
            'Feedback includes protected or uncontrolled operations knowledge')
    meaning = _owned(host, request['meaning_review_assessment_id'], 'semantic-review-assessment/1',
        'meaning_review_process_not_scientific_evidence', data_class='work_product')
    require(meaning['body']['formalization_id'] == compiled['body']['formalization_id'], 'Paired meaning target differs')
    review = host._inspect_meaning_review(actor, meaning['id'])
    require(review['current'] is True and review['independent_semantic_review'] == 'SATISFIED',
        'Paired feedback requires current independent meaning review')
    composition_record = host._breakout_composition_status(request['composition_id'], compiled)
    require(body.get('composition_id') == request['composition_id']
        and body.get('meaning_assessment_id') == request['meaning_review_assessment_id'],
        'Stored breakout execution evidence identities differ')
    require({compiled['id'],meaning['id'],composition_record['id']} <= set(execution['source_refs']),
        'Paired execution evidence linkage differs')
    data_use = host._artifact(compiled['body']['input_id'])['body']['data_use']
    require(data_use == host._paired_data_use(dependencies) and not data_use['gaps'],
        'Paired data-use evidence differs')
    result = body['result']; report = result['report']; descriptor = result['case_blob']
    require(report['processing_complete'] is True and report['scientific_readiness'] is False
        and result['scientific_readiness'] is False and result['contrast']['scientific_readiness'] is False,
        'Paired feedback requires complete descriptive processing')
    require(result['compilation_hash'] == digest(compiled['body']['compilation'])
        and report['request'] == compiled['body']['compilation']['request'], 'Paired request differs')
    capsules = [host._artifact(identity) for identity in execution['source_refs']
        if host._artifact(identity)['body'].get('schema') == 'paired-execution-input/1']
    require(len(capsules) == 1, 'Exactly one retained breakout execution capsule required')
    capsule = _owned(host, capsules[0]['id'], 'paired-execution-input/1', authority)
    input_body = capsule['body']
    require(set(input_body) == {'schema','profile','created_at','compiled_id','composition_id','input','scientific_readiness'}
        and input_body['profile'] == EXECUTION_PROFILE and input_body['scientific_readiness'] is False
        and input_body['compiled_id'] == compiled['id'] and input_body['composition_id'] == composition_record['id']
        and set(capsule['source_refs']) == {compiled['id'],meaning['id'],composition_record['id']},
        'Breakout execution capsule identities differ')
    source = input_body['input']
    require(set(source) == {'compilation_input','compilation_hash','rows'}
        and source['compilation_input'] == payload
        and source['compilation_hash'] == result['compilation_hash']
        and source['rows'] == result['rows'], 'Breakout execution capsule payload differs')
    host._require_usable_dependencies(capsule['id'])
    receipt_hash = digest({'execution_input':source,'result':result})
    expected = {'schema':'paired-case-verification/1', 'result_hash':digest(result),
        'case_blob':descriptor, 'checked_cases':report['processed_case_count'], 'scientific_readiness':False}
    verification = body['verification']; audit = body['independent_original_audit']
    footprint = hashes(dependencies['bundle'])
    require(verification['mode'] == 'verify' and verification['request_hash'] == receipt_hash and verification['result'] == expected
        and verification['footprint'] == footprint and _environment_current(verification['environment'])
        and execution['blob_refs'] == [descriptor['sha256']], 'Paired replay differs')
    original = audit['result']
    require(audit['mode'] == 'audit' and audit['request_hash'] == receipt_hash
        and audit['footprint'] == hashes(runtime.read_bundle())
        and _environment_current(audit['environment'])
        and original['schema'] == 'paired-breakout-row-audit/1'
        and original['profile'] == composition.PROFILE and original['idea_id'] == composition.IDEA_ID
        and original['candidate_hash'] == compiled['body']['compilation']['candidate_hash']
        and original['checked_cases'] == report['processed_case_count']
        and original['oracle_sha256'] == composition.ORACLE_SHA256
        and original['scientific_readiness'] is False, 'Independent paired original audit differs')
    require(report['expected_case_count'] == report['processed_case_count']
        and original['observed_outcomes'] == sum(row['observed'] for row in report['diagnostics']['condition_outcome_counts'].values()),
        'Paired audit population differs')
    if read_cases:
        raw = host._read_blob_bytes(descriptor['sha256'])
        require(len(raw) == descriptor['size'] and hashlib.sha256(raw).hexdigest() == descriptor['sha256'],
            'Paired case bytes differ')
    return execution, {'data_use':data_use,'meaning_review':review,'case_verification':expected,
        'composition_id':composition_record['id'],'execution_capsule_id':capsule['id'],'original_formula_audit':original}


def _save(host, body, refs, exposure, target_epoch):
    return host._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
        'data_class':'development','authority':AUTHORITY,'body':body,
        'source_refs':sorted(set(refs)),'exposure':sorted(set(exposure) | set(refs)),
        'not_before_epoch':target_epoch})


def publish_feedback(host, actor, root_epoch_id, execution_id, composition_id,
                     meaning_review_assessment_id, target_epoch):
    """Called only inside the authenticated broker transaction; all four or none."""
    if actor['role'] != 'operator':
        raise Denied('Only the operator may publish development feedback')
    request = {'root_epoch_id':text(root_epoch_id,'root epoch'),'execution_id':text(execution_id,'execution'),
        'composition_id':text(composition_id,'paired composition'),
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
    require({execution_id,composition_id,meaning_review_assessment_id} <= set(cohort['artifact_ids']),
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
        'publisher_sha256':host._breakout_feedback_source_current(),
        'retained_research_records':retained,
        'evidence_at_publication':evidence,'scientific_readiness':False,
        'qualification':'Closed development snapshot including failures; neither independent confirmation nor economic or scientific evidence.'},
        refs, exposure, target_epoch)
    scope = {'root_epoch_id':root_epoch_id,'execution_id':execution_id,'manifest_id':manifest['id'],
             'evidence_class':'descriptive_development_only'}
    result = execution['body']['result']
    measurement = canonical({'execution_id':execution_id,'processed_case_count':result['report']['processed_case_count'],
        'contrast':result['contrast'],'case_blob':result['case_blob']})
    condition_count = integer(result['contrast']['condition_count'], 'conditioned observations')
    scope_count = integer(result['contrast']['scope_count'], 'baseline observations')
    limitation = ('There is only one qualifying observed case. ' if condition_count == 1
        else 'There are ' + str(condition_count) + ' qualifying observed cases. ')
    limitation += ('The whole-scope baseline has ' + str(scope_count) + ' observed outcomes. '
        'Numerical enclosures bound arithmetic rounding, not statistical uncertainty. '
        'Economic usefulness remains unknown; no executable policy costs or profitability are established. ')
    contents = [('observation', {'text':'Completed development computation with all original ideas, attempts and gaps retained.',
        'measurement':measurement,
        'uncertainty':limitation+'Descriptive only. Unknown training exposure and exposed history remain inherited; no calibrated inference or economic conclusion.'}),
        ('research_experience', {'text':'This closed development checkpoint is available as qualified research feedback.',
        'interpretation':'The recorded result describes the exact original scope. An information gap is not falsification; a computed effect is not independent confirmation.',
        'uncertainty':limitation+'No scientific or economic conclusion follows. Source failures and later exposure remain part of any descendant idea. Reassess on changed meaning/data-use evidence or technical revocation.',
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
    require(manifest['body']['publisher_sha256'] == host._breakout_feedback_source_current(), 'Paired publisher source changed')
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


class BreakoutFeedbackBroker(BreakoutResearchBroker):
    """Opt-in publication/access adapter; numeric source closures are unchanged."""
    def _breakout_feedback_source_current(self):
        self._breakout_research_sources()
        current = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        require(current == LOADED_SELF, 'Paired publisher changed; restart and requalify')
        return current

    def publish_breakout_feedback(self, token, **request):
        with self._transaction():
            actor = self._binding_owner(token)
            self._breakout_feedback_source_current()
            return publish_feedback(self, actor, **request)

    def _released_feature_evidence(self, artifact, epoch, research_time):
        # Broker's existing general release fallback preserves returned grant
        # exposure; the returned object remains an explicitly paired release.
        grant = super()._released_feature_evidence(artifact, epoch, research_time)
        return grant if grant is not None else released_feedback(self, artifact, epoch, research_time)

    def _check_feedback_context(self, context):
        super()._check_feedback_context(context)
        check_context(self, context)

    def _paired_data_use(self, dependencies):
        result = super()._paired_data_use(dependencies)
        target = dependencies['formalization']
        inherited = set(target['exposure'])
        grants = sorted(row[0] for row in self._db.execute(
            "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?", (RELEASE,))
            if row[0] in inherited)
        if not grants:
            # Existing immutable compilations retain exactly their original
            # data-use assessment; no retroactive certificate substitution.
            return result
        context = self._context(target['context_id'])
        require(set(grants) <= set(context['exposure']), 'Paired feedback was not in the authorized formalizer context')
        self._check_feedback_context(context)
        knowledge = prior_knowledge(self, target)
        gaps = [gap for gap in result['gaps'] if gap != 'OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT']
        if knowledge['operations_knowledge_ids']:
            gaps.append('OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT')
        return {**result, 'prior_knowledge':knowledge, 'gaps':gaps,
            'status':'QUALIFIED' if not gaps else 'DATA_USE_GAP',
            'paired_breakout_feedback_import':{'profile':'paired-breakout-development-feedback-import/1',
                'publisher_sha256':self._breakout_feedback_source_current(), 'release_ids':grants,
                'scientific_readiness':False}}

    def _technical_dependencies(self, artifact):
        body = artifact['body']; schema = body.get('schema') if type(body) is dict else None
        if artifact['creator'] == artifact['origin'] == 'controller' and artifact['authority'] == AUTHORITY:
            if schema == MANIFEST:
                return [body['request'][key] for key in ('execution_id','composition_id')]
            if schema == RELEASE:
                return [body['manifest_id']]
            if schema == 'research-record/1':
                return [body['scope']['manifest_id']]
        return super()._technical_dependencies(artifact)

    def _breakout_feedback_selector(self, artifact):
        body = artifact['body']
        require(type(body) is dict and body.get('schema') in (MANIFEST, RELEASE)
            and artifact['creator'] == artifact['origin'] == 'controller'
            and artifact['authority'] == AUTHORITY and artifact['data_class'] == 'development',
            'Owned paired feedback version required')
        return {'schema':body['schema'], 'artifact_id':artifact['id']}

    def _revoke_dependency(self, actor, key, dependency_id, reason, evidence_refs):
        target = self._artifact(dependency_id)
        if type(target['body']) is not dict or target['body'].get('schema') not in (MANIFEST, RELEASE):
            return super()._revoke_dependency(actor, key, dependency_id, reason, evidence_refs)
        selector = self._breakout_feedback_selector(target)
        request = decode(canonical({'key':text(key,'revocation key'),
            'dependency_id':text(dependency_id,'dependency identity'), 'reason':text(reason,'defect reason'),
            'evidence_refs':strings(evidence_refs,'defect evidence')}))
        require(1 <= len(request['evidence_refs']) <= 32, 'One through 32 defect references required')
        for previous in self._revocation_records():
            if previous['body']['request']['key'] == key:
                if previous['body']['request'] != request:
                    raise Conflict('Revocation key already binds different evidence')
                return previous
        refs = sorted({dependency_id,*request['evidence_refs']}); exposure = set(refs)
        for identity in refs: exposure.update(self._artifact(identity)['exposure'])
        saved = self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
            'data_class':'operations','source_refs':refs,'exposure':sorted(exposure),'authority':REVOCATION_AUTHORITY,
            'body':{'schema':REVOCATION_SCHEMA,'created_at':self._now(),'request':request,'selector':selector,
                'affected_artifact_ids':self._affected_dependency_uses(selector),
                'affected_scope':'supported_typed_bindings_at_revocation','status':'REVOKED','scientific_readiness':False,
                'qualification':'Operator-recorded technical defect; immutable history, no empirical falsification or deployment authority.'}})
        self._event(actor['name'],'dependency_revoked',artifact_id=saved['id'],dependency_id=dependency_id)
        return saved

    def _affected_dependency_uses(self, selector):
        if selector.get('schema') not in (MANIFEST, RELEASE):
            return super()._affected_dependency_uses(selector)
        root = self._artifact(selector['artifact_id'])
        require(self._breakout_feedback_selector(root) == selector, 'Paired feedback revocation selector differs')
        reverse = {}
        for row in self._db.execute('SELECT id FROM artifacts'):
            artifact = self._artifact(row[0])
            try: dependencies = self._technical_dependencies(artifact)
            except (Invalid,Denied,KeyError,TypeError): continue
            if dependencies is None: continue
            require(type(dependencies) is list and len(dependencies) <= 256, 'Invalid technical dependency list')
            for dependency in dependencies:
                reverse.setdefault(text(dependency,'technical dependency'),set()).add(artifact['id'])
        affected = {root['id']}; pending = [root['id']]
        while pending:
            for identity in reverse.get(pending.pop(),()):
                if identity not in affected:
                    affected.add(identity); pending.append(identity)
        return sorted(affected)

    def _dependency_use(self, artifact_id):
        result = super()._dependency_use(artifact_id)
        used = set(result['checked_versions'])
        extra = []
        for record in self._revocation_records():
            selector = record['body']['selector']
            if selector.get('schema') in (MANIFEST, RELEASE) and selector.get('artifact_id') in used:
                target = self._artifact(selector['artifact_id'])
                require(self._breakout_feedback_selector(target) == selector, 'Paired feedback revocation selector differs')
                extra.append({'revocation_id':record['id'],
                    'dependency_id':record['body']['request']['dependency_id'],'used_version_id':target['id']})
        if extra:
            result = {**result,'status':'INVALIDATED_BY_DEPENDENCY',
                'invalidations':sorted([*result['invalidations'],*extra],
                    key=lambda item:(item['used_version_id'],item['revocation_id']))}
        return result

    def _add_source(self, actor, body, data_class, exposure=None):
        if type(body) is dict and body.get('schema') in (MANIFEST, RELEASE):
            raise Denied('Paired feedback host records cannot be arbitrary sources')
        return super()._add_source(actor, body, data_class, exposure)
