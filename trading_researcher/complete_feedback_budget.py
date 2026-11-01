"""D093 complete-feedback one-use resource overlay; not a scientific or model-issued permission.

The shared spend ledger is outside registry rollback. A committed fence whose
registry transaction fails is deliberately NOT refunded or recreated.
"""
import hashlib
from pathlib import Path

from .codec import Invalid, canonical, decode, digest
from .errors import Conflict, Denied
from .openai_provider import MODEL, SpendLedger, cost_bound

POLICY = 'research-epoch-feedback-budget/2.0'
APPROVAL = 'SESSION-2026-10-30-COMPLETE-FEEDBACK-BUDGET'
SPEC = 'docs/architecture/22_COMPLETE_FEEDBACK_RESEARCH_EPOCH.md'
SPEC_SHA256 = '0874945cef5d08bd8c023b8e83def3ea99ed94004d61e301beb5ca9f0afa2763'
TOKEN_CAP = 420000
COST_CAP = 1400000000
AGGREGATE_CAP = 5000000000


from .epoch_budget import _ledger, _schema

SOURCE_IDS = frozenset(('12b6d0242e48f935559ece31eff19ab35a69e48bb976828bd4f05925185d521d', '2b8617908630ef3a8f108407f90fc6262a49ab1cd81495a449c86c0c9e9e328b', '2f177872e1fedc0e9205d4b4ad79cd946066109aa2955c2e5bde77e6127d2428', '3c199714862409d80df3850a352d439c0ef397767596355cccebff78a8c75938', '5d402dfe2f113c2734c6567539e48abe4cb228ce08e252df753f3cb47f055e2d', '6b36faab76fb227c0b501661f18d7c0b3b35ef927721421dd6240e460e7ba35e', 'bc465d2aeefcf5954b3ff155c059bebab6edc34c2644f00cbe028831179f3626', 'd97d080ba0657d7fb2be67629829ea85ea3346e67a41a0b55c4ccc772d2fb035'))
FEEDBACK_COHORTS = 2
INITIAL_WIRE_HASHES = ('2f40170cb28903af120fe5a6479295a635575898da89d8cdbd571fe2fc2a3103', 'ff8b731e220845344f12d1f8b41d862e76c321d876055f53f36552b28cc4d355')


def _call_settings(profile, kind):
    from .openai_provider import _config
    from .auxiliary_views import PROFILE, REUSE_SCOPE
    limits = {'research-record/v1': (74000, 6000, 'low', 240),
              'formalization/v1': (62000, 18000, 'high', 360),
              'semantic-review/v1': (76000, 4000, 'low', 360)}
    if kind not in limits:
        raise Denied('No slot exists for this job kind')
    parameters = profile.get('generation_parameters')
    if type(parameters) is not dict or set(parameters) != {'openai_responses'}:
        raise Invalid('The approved direct provider configuration is required')
    config = parameters['openai_responses']
    _config(config)
    max_input, output, reasoning, timeout = limits[kind]
    if (profile.get('model') != MODEL or profile.get('max_retries') != 0
            or profile.get('max_output_tokens') != output
            or profile.get('call_timeout_seconds') != timeout
            or config['input_token_limit'] != max_input or config['output_token_limit'] != output
            or config['reasoning_effort'] != reasoning or config['test_budget_nano'] != AGGREGATE_CAP):
        raise Denied('Call settings differ from the fixed approved role allocation')
    if kind != 'research-record/v1':
        if config.get('source_presentation') != PROFILE or config.get('bounded_math_scope') != REUSE_SCOPE:
            raise Denied('Full auxiliary provenance and the approved scope must be preserved')
        if (kind == 'formalization/v1' and config.get('output_formatting') != 'compact-json/1'
                or kind == 'semantic-review/v1' and 'output_formatting' in config):
            raise Denied('Role output formatting differs from the approved settings')
    elif set(config) & {'source_presentation', 'bounded_math_scope', 'output_formatting'}:
        raise Denied('No additional discovery representation is approved')


def validate_job(host, epoch, spec):
    if len(spec['allowed_workers']) != 1 or spec['max_attempts'] != 1:
        raise Denied('Exactly one authenticated worker and attempt per slot are required')
    state = inspect(host, epoch)
    if state['revoked']:
        raise Denied('The complete-feedback grant is revoked')
    kind = spec['kind']
    _call_settings(host._effective_research_profile({'spec': spec}), kind)
    # A failed job does not create another job or another candidate allowance.
    prior = [decode(row[0]) for row in host._db.execute(
        "SELECT envelope FROM job_specs WHERE json_extract(envelope,'$.research_epoch_id')=?", (epoch['id'],))]
    if any(old['kind'] == kind and (kind != 'research-record/v1'
           or old['allowed_workers'] == spec['allowed_workers']) for old in prior):
        raise Denied('This stage job has already been declared')
    if kind != 'research-record/v1':
        rows = host._db.execute('''SELECT s.envelope,j.state,j.result_id FROM job_specs s
            JOIN jobs j ON j.id=s.id WHERE json_extract(s.envelope,'$.research_epoch_id')=?''',
            (epoch['id'],)).fetchall()
        first = [row for row in rows if decode(row[0])['kind'] == 'research-record/v1'
                 and decode(row[0])['allowed_workers'] == [epoch['request']['workers'][0]]]
        if len(first) != 1 or first[0][1] != 'completed' or first[0][2] is None:
            raise Denied('The preselected first perspective has no completed primary idea')
        idea = host._artifact(first[0][2])
        if idea['body'].get('kind') != 'idea':
            raise Denied('A retained discovery gap cannot be substituted by another idea')
        inputs = spec['research_inputs']
        if kind == 'formalization/v1':
            if inputs['idea_id'] != idea['id']:
                raise Denied('Only the first perspective primary idea is selected')
        else:
            formal = [row for row in rows if decode(row[0])['kind'] == 'formalization/v1']
            if (len(formal) != 1 or formal[0][1] != 'completed'
                    or formal[0][2] != inputs['formalization_id']):
                raise Denied('Review must use this epoch single completed formalization')


def _check_request(host, epoch, job, request):
    if job['spec']['kind'] != 'research-record/v1':
        return  # The broker requires exact request_for(controller-owned packet).
    from .context_views import FEEDBACK_VIEW_PROFILE, source_view
    from .openai_provider import wire_request
    spec = job['spec']
    context = host._context(epoch['request']['context_id'])
    worker = spec['allowed_workers'][0]
    messages = [{'role': 'system', 'content': epoch['request']['profile']['prompts'][worker]},
                {'role': 'user', 'content': canonical({'purpose': spec['purpose'], 'sources': [
                    source_view(host._artifact(identity), profile=FEEDBACK_VIEW_PROFILE)
                    for identity in context['artifact_ids']]})}]
    previous = host._calls_for(epoch['id'], job['id'], job['generation'])
    if not previous:
        config = request['generation_parameters']['openai_responses']
        if digest(wire_request(request, config)) != INITIAL_WIRE_HASHES[epoch['request']['workers'].index(worker)]:
            raise Denied('Initial wire differs from the exact approved complete input')
    else:
        if len(previous) != 1 or previous[0]['reply'] is None:
            raise Denied('Only one settled tool followup is approved')
        response = previous[0]['reply']['response']
        output = response.get('output')
        if type(output) is not dict or output.get('status') != 'tools':
            raise Denied('A completed, failed or incomplete response cannot be retried')
        calls = output.get('calls')
        if type(calls) is not list or not 1 <= len(calls) <= 16:
            raise Denied('The retained tool batch is invalid')
        messages.append({'role': 'assistant', 'content': canonical(response)})
        stored = [decode(row[0]) for row in host._db.execute(
            "SELECT envelope FROM artifacts WHERE json_extract(envelope,'$.body.call_id')=? ORDER BY rowid",
            (previous[0]['id'],))]
        for call in calls:
            results = [a for a in stored if a.get('job_id') == job['id']
                       and a.get('creator') == worker and a['body'].get('schema') == 'provider-tool-result/1'
                       and canonical(a['body'].get('tool_request')) == canonical(call)]
            if len(results) != 1:
                raise Denied('Each tool result must have one exact retained source')
            body = results[0]['body']
            if call['name'] == 'measure_development' and body['result']['status'] == 'ok':
                body = {**body, 'result': {'status': 'ok', 'value': source_view(
                    body['result']['value'], profile=FEEDBACK_VIEW_PROFILE)}}
            messages.append({'role': 'tool', 'content': canonical(body)})
    if canonical(request['messages']) != canonical(messages):
        raise Denied('Complete discovery sources or the retained tool transcript differ')


def _binding(host, epoch):
    return {'policy': POLICY, 'approval': APPROVAL, 'spec_sha256': SPEC_SHA256,
            'registry_identity': digest(str(host.directory.resolve())),
            'epoch_id': epoch['id'], 'created_at': epoch['created_at'],
            'request_key': epoch['request_key'], 'request_sha256': digest(epoch['request'])}


def _bound_row(host, epoch, db):
    row = db.execute('SELECT binding,calls,revoked FROM research_epoch_budget_grants WHERE approval=?',
                     (APPROVAL,)).fetchone()
    if row is None or row[0] != canonical(_binding(host, epoch)):
        raise Denied('The one-use epoch binding is absent or differs from this registry')
    return {'binding': decode(row[0]), 'calls': decode(row[1]), 'revoked': bool(row[2])}


def validate(host, context, profile, policy):
    if policy != POLICY:
        raise Invalid('Unknown research epoch budget overlay')
    if hashlib.sha256((Path(__file__).resolve().parents[1] / SPEC).read_bytes()).hexdigest() != SPEC_SHA256:
        raise Denied('Approved resource-overlay specification changed')
    if (profile.get('model') != MODEL or profile.get('mode') != 'live'
            or profile.get('currency') != 'USD' or profile.get('max_tokens') != TOKEN_CAP
            or profile.get('max_cost_units') != COST_CAP or profile.get('max_retries') != 0
            or profile.get('max_calls') != 6 or profile.get('max_seconds') != 1800
            or profile.get('call_timeout_seconds') != 240
            or profile.get('max_output_tokens') != 6000
            or profile.get('source_presentation') != 'discovery-source-view/3'):
        raise Invalid('Overlay requires its explicit approved provider, limits and feedback profile')
    perspectives = profile.get('perspective_profiles', {})
    if type(perspectives) is not dict:
        raise Invalid('Overlay perspective profiles must be an object')
    for settings in perspectives.values():
        if (type(settings) is not dict or settings.get('model') != MODEL
                or settings.get('max_retries') != 0 or settings.get('max_output_tokens') != 6000):
            raise Invalid('Overlay perspective settings change the approved allocation')
    if set(context['artifact_ids']) != SOURCE_IDS:
        raise Denied('The approved exact eight-source context differs')
    artifacts = [host._artifact(identity) for identity in context['artifact_ids']]
    if sum(item['body'].get('schema') == 'development-feedback-manifest/1' for item in artifacts) != FEEDBACK_COHORTS:
        raise Denied('Both complete closed feedback cohorts are required')
    if (not artifacts or any(item['data_class'] != 'development' for item in artifacts)
            or not any(item['body'].get('schema') == 'development-feedback-manifest/1' for item in artifacts)):
        raise Denied('The overlay requires the complete authorized closed development feedback context')
    from .development_feedback import released_feedback
    for manifest in artifacts:
        if manifest['body'].get('schema') != 'development-feedback-manifest/1':
            continue
        release = released_feedback(host, manifest, context['epoch'], context['research_time'])
        if release is None or not {release['body'][key] for key in
                ('manifest_id', 'observation_id', 'experience_id')} <= set(context['artifact_ids']):
            raise Denied('Overlay requires the exact released manifest, observation and experience together')
    host._check_feedback_context(context)
    _ledger(host)
    expected = {'openai_responses': host._provider_routes[MODEL]['config']}
    if any(canonical(settings.get('generation_parameters')) != canonical(expected)
           for settings in [profile, *perspectives.values()]):
        raise Invalid('Overlay discovery settings differ from the installed provider configuration')
    for settings in [profile, *perspectives.values()]:
        _call_settings(settings, 'research-record/v1')
    return TOKEN_CAP


def claim(host, epoch):
    ledger = _ledger(host)
    with ledger._connect() as db:
        db.execute('BEGIN IMMEDIATE')
        _schema(db)
        if db.execute('SELECT 1 FROM research_epoch_budget_grants WHERE approval=?', (APPROVAL,)).fetchone():
            raise Denied('The approved one-use epoch authorization is already consumed')
        rows = db.execute('SELECT reserved,charged,state FROM dispatches').fetchall()
        if (any(state != 'settled' for _, _, state in rows)
                or sum(reserved if charged is None else charged for reserved, charged, _ in rows) + COST_CAP > AGGREGATE_CAP):
            raise Denied('Pending, unknown or insufficient aggregate spending allowance')
        db.execute('INSERT INTO research_epoch_budget_grants VALUES(?,?,?,0)',
                   (APPROVAL, canonical(_binding(host, epoch)), '[]'))


def inspect(host, epoch):
    with _ledger(host)._connect() as db:
        db.execute('BEGIN')
        if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_epoch_budget_grants'").fetchone():
            raise Denied('One-use authorization is missing')
        return _bound_row(host, epoch, db)


def _slot(epoch, job, previous):
    kind = job['spec']['kind']
    worker = job['spec']['allowed_workers'][0]
    if kind == 'research-record/v1':
        workers = epoch['request']['workers']
        if worker not in workers:
            raise Denied('Overlay discovery identity differs')
        stage = 'discovery:' + str(workers.index(worker))
        used = sum(call['stage'] == stage for call in previous)
        if used >= 2:
            raise Denied('The discovery perspective has exhausted its two reserved calls')
        return stage, (43358 + 10 * workers.index(worker) if used == 0 else 74000), 6000
    limits = {'formalization/v1': (62000, 18000), 'semantic-review/v1': (76000, 4000)}
    if kind not in limits or any(call['stage'] == kind for call in previous):
        raise Denied('The single downstream stage is unavailable or already consumed')
    return kind, *limits[kind]


def reserve(host, epoch, job, identity, input_bound, output_bound, cost, *, request):
    if input_bound + output_bound > 80000:
        raise Denied('The existing per-call token ceiling remains 80000')
    if cost != cost_bound(input_bound, output_bound):
        raise Denied('Overlay reservation must use the trusted conservative OpenAI tariff')
    profile = host._effective_research_profile(job)
    if profile['model'] != MODEL or profile['max_retries'] != 0:
        raise Denied('Overlay calls must preserve the approved model and no-retry policy')
    _call_settings(profile, job['spec']['kind'])
    if host._now() + profile['call_timeout_seconds'] > epoch['created_at'] + epoch['request']['profile']['max_seconds']:
        raise Denied('Insufficient remaining epoch time for the unchanged call allowance')
    _check_request(host, epoch, job, request)
    with _ledger(host)._connect() as db:
        db.execute('BEGIN IMMEDIATE')
        state = _bound_row(host, epoch, db)
        if state['revoked']:
            raise Denied('The one-use resource authorization is revoked')
        actual = [row[0] for row in host._db.execute(
            'SELECT id FROM research_calls WHERE epoch_id=? ORDER BY rowid', (epoch['id'],))]
        if actual != [call['call_id'] for call in state['calls']]:
            raise Denied('External reservation fence differs; stale backup or incomplete transaction requires reconciliation')
        stage, max_input, max_output = _slot(epoch, job, state['calls'])
        if input_bound > max_input or output_bound != max_output:
            raise Denied('Call exceeds its predeclared complete-path allocation')
        if any(row[0] != 'settled' for row in db.execute('SELECT state FROM dispatches')):
            raise Denied('Pending or unknown provider spending prevents another reservation')
        # Charge the entire slot to the nonrecyclable allocation independently of
        # worker-reported usage. Actual money still settles in the shared ledger.
        calls = [*state['calls'], {'call_id': identity, 'stage': stage, 'job_id': job['id'],
                 'input_bound': input_bound, 'output_bound': output_bound, 'cost_bound': cost,
                 'allocated_tokens': max_input + max_output,
                 'allocated_cost': cost_bound(max_input, max_output)}]
        if sum(call['allocated_tokens'] for call in calls) > TOKEN_CAP or sum(call['allocated_cost'] for call in calls) > COST_CAP:
            raise Denied('Overlay aggregate allocation exhausted')
        db.execute('UPDATE research_epoch_budget_grants SET calls=? WHERE approval=?', (canonical(calls), APPROVAL))


def revoke(host, epoch):
    with _ledger(host)._connect() as db:
        db.execute('BEGIN IMMEDIATE')
        _bound_row(host, epoch, db)
        db.execute('UPDATE research_epoch_budget_grants SET revoked=1 WHERE approval=?', (APPROVAL,))
    return {'epoch_id': epoch['id'], 'status': 'REVOKED', 'pending_calls_still_require_settlement': True}
