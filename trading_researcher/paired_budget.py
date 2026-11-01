"""D094 retained-original-idea budget, independent of all consumed grants."""
import hashlib
from pathlib import Path

from .codec import Invalid, canonical, decode, digest
from .errors import Denied
from .openai_provider import MODEL, cost_bound, _config, COMPACT_OUTPUT_SUFFIX
from .epoch_budget import _ledger, _schema
from .paired_development import CONTRACT

POLICY='paired-development-continuation/1'
APPROVAL='SESSION-2026-10-30-PAIRED-DEVELOPMENT'
SPEC='docs/architecture/23_PAIRED_DEVELOPMENT.md'
TOKEN_CAP=160000
COST_CAP=600000000
AGGREGATE_CAP=5000000000
IDEA='94cf7b732406785e98d1c5a42daccce4c43685fbf0471f517d2a960311c8e6c3'
SPEC_SHA256='5452da26300174b729faff0a30881a7ede0522429c57baf0f5d9968d281d994e'


def _call_settings(profile,kind):
    from .auxiliary_views import PROFILE
    from .meaning_reviews import PROMPT, PROTOCOL
    limits={'formalization/v1':(62000,18000,'high'),'semantic-review/v1':(76000,4000,'low')}
    if kind not in limits:
        raise Denied('D094 authorizes no discovery or successor call')
    parameters=profile.get('generation_parameters')
    if type(parameters) is not dict or set(parameters)!={'openai_responses'}:
        raise Invalid('Exact direct provider configuration required')
    config=parameters['openai_responses']
    _config(config)
    max_input,output,reasoning=limits[kind]
    if (profile.get('model')!=MODEL or profile.get('max_retries')!=0
            or profile.get('max_output_tokens')!=output or profile.get('call_timeout_seconds')!=360
            or config['input_token_limit']!=max_input or config['output_token_limit']!=output
            or config['reasoning_effort']!=reasoning or config['test_budget_nano']!=AGGREGATE_CAP
            or config.get('source_presentation')!=PROFILE
            or set(config)&{'bounded_math_scope','output_formatting'}):
        raise Denied('Paired role settings differ from the approved allocation/full-source transport')
    prompts=profile.get('prompts')
    if type(prompts) is not dict or len(prompts)!=1 or any(type(value) is not str for value in prompts.values()):
        raise Denied('One authenticated role prompt is required')
    prompt=next(iter(prompts.values()))
    if kind=='semantic-review/v1' and (prompt!=PROMPT or profile.get('prompt_version')!=PROTOCOL):
        raise Denied('The existing full independent meaning-review protocol must be unchanged')
    if kind=='formalization/v1' and not prompt.endswith(COMPACT_OUTPUT_SUFFIX):
        raise Denied('The exact approved compact-output formatting instruction is required')


def validate(host,context,profile,policy):
    if policy!=POLICY or getattr(host,'PAIRED_RUNTIME',False) is not True:
        raise Denied('Paired continuation requires the explicit owned paired broker')
    if hashlib.sha256((Path(__file__).resolve().parents[1]/SPEC).read_bytes()).hexdigest()!=SPEC_SHA256:
        raise Denied('The adopted paired specification changed')
    if (profile.get('model')!=MODEL or profile.get('mode')!='live' or profile.get('currency')!='USD'
            or profile.get('max_tokens')!=TOKEN_CAP or profile.get('max_cost_units')!=COST_CAP
            or profile.get('max_calls')!=2 or profile.get('max_retries')!=0
            or profile.get('max_seconds')!=1800 or profile.get('call_timeout_seconds')!=360
            or profile.get('max_output_tokens')!=18000 or profile.get('tools')!=[]
            or set(profile)&{'perspective_profiles','source_presentation'}):
        raise Invalid('Paired continuation requires the exact approved complete allocation')
    if IDEA not in context['artifact_ids']:
        raise Denied('Only the retained preselected original idea may be continued')
    for identity in context['artifact_ids']:
        host._deny_final_calibration_ancestry(host._artifact(identity))
    host._paired_require_qualification()
    _ledger(host)
    return TOKEN_CAP


def validate_job(host,epoch,spec):
    if spec['max_attempts']!=1 or len(spec['allowed_workers'])!=1:
        raise Denied('One authenticated attempt per paired role is required')
    if inspect(host,epoch)['revoked']:
        raise Denied('Paired continuation has been revoked')
    kind=spec['kind']
    _call_settings(host._effective_research_profile({'spec':spec}),kind)
    inputs=spec.get('research_inputs',{})
    if inputs.get('paired_contract')!=CONTRACT or 'feature_certificate_id' not in inputs:
        raise Denied('Full paired semantics and current exact availability evidence required')
    rows=host._db.execute("SELECT s.envelope,j.state,j.result_id FROM job_specs s JOIN jobs j ON j.id=s.id WHERE json_extract(s.envelope,'$.research_epoch_id')=?",(epoch['id'],)).fetchall()
    if any(decode(row[0])['kind']==kind for row in rows):
        raise Denied('This paired stage was already declared; failure is not a new slot')
    if kind=='formalization/v1':
        if inputs.get('idea_id')!=IDEA:
            raise Denied('A different or easier idea cannot replace the retained original')
    else:
        formal=[row for row in rows if decode(row[0])['kind']=='formalization/v1']
        if len(formal)!=1 or formal[0][1]!='completed' or formal[0][2]!=inputs.get('formalization_id'):
            raise Denied('Review requires this epoch completed exact formalization')
        target=host._artifact(formal[0][2])
        if target['body']['assessment']['status']!='STRUCTURE_CHECKED' or target['body']['candidate'] is None:
            raise Denied('Null or incomplete formalization cannot spend the reviewer slot')


def _slot(epoch,job,previous):
    kind=job['spec']['kind']
    limits={'formalization/v1':(62000,18000),'semantic-review/v1':(76000,4000)}
    if kind not in limits or any(call['stage']==kind for call in previous):
        raise Denied('Paired stage unavailable or already consumed')
    if (kind=='formalization/v1' and previous
            or kind=='semantic-review/v1' and [call['stage'] for call in previous]!=['formalization/v1']):
        raise Denied('The single formalization must precede its single reviewer')
    return kind,*limits[kind]


def _check_request(host,epoch,job,request):
    from .auxiliary import request_for
    if canonical(request)!=canonical(request_for(job['spec'],host._auxiliary_packet_for_spec(job['spec']))):
        raise Denied('Only the complete owned paired packet may be dispatched')
    host._paired_require_qualification()

def _binding(host, epoch):
    return {'policy': POLICY, 'approval': APPROVAL, 'spec_sha256': SPEC_SHA256,
            'registry_identity': digest(str(host.directory.resolve())),
            'epoch_id': epoch['id'], 'created_at': epoch['created_at'],
            'request_key': epoch['request_key'], 'request_sha256': digest(epoch['request']), 'paired_sources': host._paired_source_identity()}

def _bound_row(host, epoch, db):
    row = db.execute('SELECT binding,calls,revoked FROM research_epoch_budget_grants WHERE approval=?',
                     (APPROVAL,)).fetchone()
    if row is None or row[0] != canonical(_binding(host, epoch)):
        raise Denied('The one-use epoch binding is absent or differs from this registry')
    return {'binding': decode(row[0]), 'calls': decode(row[1]), 'revoked': bool(row[2])}

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
