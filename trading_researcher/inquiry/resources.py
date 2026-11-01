"""One conditional four-stage allocation; native records and cash stay separate."""
import hashlib
from pathlib import Path
import time

from ..codec import Invalid, canonical, decode, digest, integer, text
from ..errors import Denied
from ..epoch_budget import _ledger, _schema
from ..openai_provider import MODEL, _config, cost_bound, wire_request, provider_identity

POLICY = 'inquiry-four-stage-resources/1'
APPROVAL = 'SESSION-2026-11-01-DISCRETIONARY-INQUIRY-FOUR-STAGE'
SPEC = 'trading_researcher/inquiry/RESOURCES.md'
SPEC_SHA256 = '17d182aeabf5bdceba7753eb8f10e6a15d239aec19e877fe9d6dd7d3b36863df'
TOKEN_CAP = 320000
COST_CAP = 1043277500
AGGREGATE_CAP = 5000000000
STAGES = ('discovery:0', 'discovery:1', 'formalization/v1', 'semantic-review/v1')
INPUT_MAX = (74000, 74000, 48000, 76000)
OUTPUT = (6000, 6000, 32000, 4000)
INPUT_HOLD = (68362, 68372, 29083, 43346)
TIMEOUT = (240, 240, 360, 360)
OLD_APPROVALS = (
    'SESSION-2026-10-29-FEEDBACK-BUDGET',
    'SESSION-2026-10-29-INDEPENDENT-BTC-REVIEW',
    'SESSION-2026-10-30-COMPLETE-FEEDBACK-BUDGET',
    'SESSION-2026-10-30-DISCRETIONARY-BUDGET-PAIRED-BREAKOUT',
    'SESSION-2026-10-30-DISCRETIONARY-BUDGET-PAIRED-CORRECTION',
    'SESSION-2026-10-30-PAIRED-DEVELOPMENT',
)


def disposition(role_profiles, discovery_run_ids):
    """Operator data; creation still validates exact profiles and one-use cash."""
    return decode(canonical({'policy': POLICY, 'approval': APPROVAL, 'spec_sha256': SPEC_SHA256,
                             'role_profiles': role_profiles, 'discovery_run_ids': discovery_run_ids}))


def _settings(profile, index):
    from ..auxiliary_views import PROFILE
    parameters = profile.get('generation_parameters')
    if type(parameters) is not dict or set(parameters) != {'openai_responses'}:
        raise Invalid('Exactly one direct OpenAI configuration is required')
    config = parameters['openai_responses']
    _config(config)
    if (time.time() >= config['expires_at'] or profile.get('model') != MODEL or profile.get('max_retries') != 0
            or profile.get('max_output_tokens') != OUTPUT[index]
            or profile.get('call_timeout_seconds') != TIMEOUT[index]
            or config['input_token_limit'] != INPUT_MAX[index]
            or config['output_token_limit'] != OUTPUT[index]
            or config['reasoning_effort'] != ('high' if index == 2 else 'low')
            or config['test_budget_nano'] != AGGREGATE_CAP
            or 'output_formatting' in config
            or (index < 2 and 'bounded_math_scope' in config)
            or (index >= 2 and config.get('source_presentation') != PROFILE)):
        raise Denied('Frozen role/model/reasoning/full-output allocation differs')
    return config


def validate(host, context, workers, profile, policy):
    from ..auxiliary import validate_profile
    from ..meaning_reviews import PROMPT, PROTOCOL
    if (type(policy) is not dict or set(policy) != {
            'policy', 'approval', 'spec_sha256', 'role_profiles', 'discovery_run_ids'}
            or policy['policy'] != POLICY or policy['approval'] != APPROVAL
            or policy['spec_sha256'] != SPEC_SHA256):
        raise Invalid('Explicit exact finite resource disposition required')
    root = Path(__file__).resolve().parents[2]
    if hashlib.sha256((root / SPEC).read_bytes()).hexdigest() != SPEC_SHA256:
        raise Denied('The finite resource specification changed')
    if (profile.get('mode') != 'live' or profile.get('currency') != 'USD'
            or profile.get('max_tokens') != TOKEN_CAP or profile.get('max_calls') != 4
            or profile.get('max_cost_units') != COST_CAP or profile.get('max_seconds') != 1800):
        raise Denied('The finite epoch requires its exact declared resource envelope')
    _settings(profile, 0)
    perspectives = profile.get('perspective_profiles', {})
    if type(perspectives) is not dict:
        raise Invalid('Perspective configurations must be an object')
    for settings in perspectives.values():
        _settings(settings, 0)
    runs = policy['discovery_run_ids']
    if type(runs) is not dict or set(runs) != set(workers):
        raise Invalid('Each discovery perspective requires its prebound provider run identity')
    for run in runs.values():
        text(run, 'discovery provider run')
        if len(run) > 200 or run.startswith('controller-') or ':' in run:
            raise Invalid('Bounded independent discovery provider identity required')
    if len(set(runs.values())) != 2:
        raise Denied('Discovery dispatch identities must be distinct')
    roles = policy['role_profiles']
    if type(roles) is not dict or set(roles) != set(STAGES[2:]):
        raise Invalid('Freeze both complete downstream role profiles')
    identities = list(workers)
    for index, kind in enumerate(STAGES[2:], 2):
        role = roles[kind]
        if type(role) is not dict or set(role) != {'worker', 'profile'}:
            raise Invalid('One explicit downstream identity and full profile required')
        text(role['worker'], 'downstream worker')
        principal = host._db.execute('SELECT role FROM principals WHERE name=?', (role['worker'],)).fetchone()
        if principal is None or principal[0] != 'formalizer':
            raise Denied('Both downstream identities require scoped formalizer capabilities')
        identities.append(role['worker'])
        validate_profile(role['profile'], profile)
        _settings(role['profile'], index)
    if len(set(identities)) != 4:
        raise Denied('The original perspectives, formalizer and independent reviewer must be distinct')
    scopes = [roles[kind]['profile']['generation_parameters']['openai_responses'].get('bounded_math_scope')
              for kind in STAGES[2:]]
    if scopes[0] != scopes[1]:
        raise Denied('Both downstream roles must receive the same exact bounded-math activation supplement')
    review = roles[STAGES[3]]['profile']
    if review['prompt'] != PROMPT or review['prompt_version'] != PROTOCOL:
        raise Denied('Preserve the complete independent meaning-review protocol')
    host._check_feedback_context(context)
    for identity in context['artifact_ids']:
        host._deny_final_calibration_ancestry(host._artifact(identity))
    _ledger(host)
    return TOKEN_CAP


def _binding(host, epoch):
    return {'policy': POLICY, 'approval': APPROVAL, 'spec_sha256': SPEC_SHA256,
            'registry_identity': digest(str(host.directory.resolve())),
            'ledger_identity': digest(str(Path(host._provider_routes[MODEL]['budget_file']).resolve())),
            'epoch_id': epoch['id'], 'created_at': epoch['created_at'],
            'request_key': epoch['request_key'], 'request_sha256': digest(epoch['request'])}


def _row(host, epoch, db):
    row = db.execute('SELECT binding,calls,revoked FROM research_epoch_budget_grants WHERE approval=?',
                     (APPROVAL,)).fetchone()
    if row is None or row[0] != canonical(_binding(host, epoch)):
        raise Denied('Missing or different one-use registry/epoch/ledger/source binding')
    return {'binding': decode(row[0]), 'calls': decode(row[1]), 'revoked': bool(row[2])}


def _financial(db):
    rows = db.execute('SELECT reserved,charged,state FROM dispatches').fetchall()
    if any(state != 'settled' or charged is None for _, charged, state in rows):
        raise Denied('Pending, unknown or invalid shared spending prevents continuation')
    return sum(charged for _, charged, _ in rows)


def _future_cost(index):
    return sum(cost_bound(INPUT_HOLD[i], OUTPUT[i]) for i in range(index + 1, 4))


def claim(host, epoch):
    with _ledger(host)._connect() as db:
        db.execute('BEGIN IMMEDIATE')
        _schema(db)
        if db.execute('SELECT 1 FROM research_epoch_budget_grants WHERE approval=?', (APPROVAL,)).fetchone():
            raise Denied('This finite allocation was already consumed; rollback creates no successor')
        old = {row[0]: row[1:] for row in db.execute(
            'SELECT approval,calls,revoked FROM research_epoch_budget_grants')}
        if (any(key not in old or old[key][1] != 1 or not decode(old[key][0]) for key in OLD_APPROVALS)
                or any(revoked != 1 for _, revoked in old.values())):
            raise Denied('All six old grants must remain consumed and revoked')
        if _financial(db) + sum(cost_bound(i, o) for i, o in zip(INPUT_HOLD, OUTPUT)) > AGGREGATE_CAP:
            raise Denied('The initial complete-path planning holds cannot be funded')
        db.execute('INSERT INTO research_epoch_budget_grants VALUES(?,?,?,0)',
                   (APPROVAL, canonical(_binding(host, epoch)), '[]'))
        db.execute(f'''CREATE TRIGGER IF NOT EXISTS inquiry_resource_calls_append_only
            BEFORE UPDATE OF calls ON research_epoch_budget_grants WHEN OLD.approval='{APPROVAL}'
            AND (json_array_length(NEW.calls)!=json_array_length(OLD.calls)+1
                 OR EXISTS(SELECT 1 FROM json_each(OLD.calls) p
                           WHERE p.value!=json_extract(NEW.calls,'$['||p.key||']')))
            BEGIN SELECT RAISE(ABORT,'retain consumed inquiry slots'); END''')


def inspect(host, epoch):
    with _ledger(host)._connect() as db:
        db.execute('BEGIN')
        return _row(host, epoch, db)


def _stage(epoch, spec):
    if len(spec['allowed_workers']) != 1 or spec['max_attempts'] != 1:
        raise Denied('One authenticated worker and one attempt per finite stage required')
    worker = spec['allowed_workers'][0]
    if spec['kind'] == 'research-record/v1':
        try:
            return epoch['request']['workers'].index(worker)
        except ValueError as exc:
            raise Denied('Unknown discovery perspective') from exc
    if spec['kind'] not in STAGES[2:]:
        raise Denied('No other model stage is part of this allocation')
    role = epoch['request']['resource_disposition']['role_profiles'][spec['kind']]
    if role['worker'] != worker or canonical(role['profile']) != canonical(spec.get('research_call_profile')):
        raise Denied('Downstream worker or full profile differs from its frozen role')
    return STAGES.index(spec['kind'])


def _jobs(host, epoch):
    return [host._job(row[0]) for row in host._db.execute(
        "SELECT id FROM job_specs WHERE json_extract(envelope,'$.research_epoch_id')=? ORDER BY rowid",
        (epoch['id'],))]


def _target(host, epoch, spec, index):
    if index < 2:
        return
    prior = [job for job in _jobs(host, epoch) if _stage(epoch, job['spec']) == (0 if index == 2 else 2)]
    if len(prior) != 1 or prior[0]['state'] != 'completed' or not prior[0]['result_id']:
        raise Denied('The exact preceding target is not an accepted completed result')
    target = host._artifact(prior[0]['result_id'])
    if index == 2:
        if target['body'].get('kind') != 'idea' or spec['research_inputs'].get('idea_id') != target['id']:
            raise Denied('Only A final accepted idea may proceed; no intermediate or B fallback')
    elif (spec['research_inputs'].get('formalization_id') != target['id']
            or target['body'].get('assessment', {}).get('status') != 'STRUCTURE_CHECKED'
            or target['body'].get('candidate') is None):
        raise Denied('Independent review requires the exact accepted non-null complete formalization')


def validate_job(host, epoch, spec):
    state = inspect(host, epoch)
    if state['revoked']:
        raise Denied('The finite allocation is permanently revoked')
    index = _stage(epoch, spec)
    if any(_stage(epoch, job['spec']) == index for job in _jobs(host, epoch)):
        raise Denied('A declared stage cannot be recreated after failure')
    _target(host, epoch, spec, index)


def preflight(host, epoch, job):
    """Check access/slot eligibility before sending a full packet for counting."""
    host._check_feedback_context(host._context(job['spec']['context_id']))
    index = _stage(epoch, job['spec'])
    _settings(host._effective_research_profile(job), index)
    _target(host, epoch, job['spec'], index)
    if (epoch['state'] != 'active' or host._now() + TIMEOUT[index]
            > min(epoch['created_at'] + 1800, job['spec']['deadline'])):
        raise Denied('The stage is halted or cannot retain its full call-time allowance')
    with _ledger(host)._connect() as db:
        db.execute('BEGIN')
        state = _row(host, epoch, db)
        calls = state['calls']
        native = [row[0] for row in host._db.execute(
            'SELECT id FROM research_calls WHERE epoch_id=? ORDER BY rowid', (epoch['id'],))]
        if (state['revoked'] or native != [entry['call_id'] for entry in calls]
                or index != len(calls) or [entry['stage'] for entry in calls] != list(STAGES[:index])):
            raise Denied('Revoked, consumed, out-of-order or unreconciled stage cannot count a packet')
        _financial(db)
        for entry in calls:
            authenticate(host, epoch, entry, db)
            if host._job(entry['job_id'])['state'] != 'completed':
                raise Denied('An incomplete prior stage cannot start a successor count')


def authenticate(host, epoch, entry, db):
    """Reconcile trusted local ledger provenance, never just worker usage."""
    call = host._db.execute('SELECT * FROM research_calls WHERE id=?', (entry['call_id'],)).fetchone()
    if (call is None or call['state'] != 'recorded' or not call['response_id']
            or call['epoch_id'] != epoch['id'] or call['job_id'] != entry['job_id']
            or call['input_bound'] != entry['input_bound'] or call['output_bound'] != entry['output_bound']
            or call['cost_bound'] != entry['cost_bound']):
        raise Denied('The consumed slot has no retained settled native response')
    receipt = decode(call['receipt'])
    if (receipt['late'] or receipt['usage_unknown'] or not receipt['accounting_valid']
            or not receipt['within_reservation'] or not receipt.get('installed_sources_unchanged')):
        raise Denied('Late, unknown, invalid or source-stale native settlement cannot release funds')
    body = host._artifact(call['response_id'])['body']
    response, usage = body['response'], body['usage']
    row = db.execute('''SELECT d.request_hash,d.reserved,d.charged,d.state,m.body,r.body
        FROM dispatches d LEFT JOIN token_metadata m ON m.id=d.id
        LEFT JOIN usage_receipts r ON r.id=d.id WHERE d.id=?''', (entry['dispatch_id'],)).fetchone()
    if row is None or row[3] != 'settled' or row[2] is None or row[4] is None or row[5] is None:
        raise Denied('No authenticated known settled shared-ledger dispatch')
    meta, public = decode(row[4]), decode(row[5])
    expected_receipt = {'usage': usage, 'token_details': response.get('token_usage_details'),
                        'response_status': response.get('status'),
                        'transport_request_id': response.get('transport_request_id'),
                        'provider_request_id': response.get('provider_request_id'),
                        'model_identity': response.get('model_identity')}
    if (row[0] != entry['wire_sha256'] or row[1] != entry['cost_bound']
            or response.get('aggregate_dispatch_id') != entry['dispatch_id']
            or response.get('wire_request_sha256') != entry['wire_sha256']
            or canonical(public) != canonical(expected_receipt)
            or meta.get('run_id') != entry['run_id'] or meta.get('ordinal') != 0
            or meta.get('epoch_id') != epoch['id'] or meta.get('worker') != call['owner']
            or meta.get('model') != MODEL or meta.get('prompt_version') != entry['prompt_version']
            or meta.get('model_identity') != provider_identity()
            or response.get('model_identity') != provider_identity(MODEL)
            or type(meta.get('counted_input_tokens')) is not int
            or not 0 <= meta['counted_input_tokens'] <= entry['input_bound']
            or response.get('counted_input_tokens') != meta['counted_input_tokens']
            or usage is None or row[2] != usage['cost_units']
            or usage['cost_units'] != cost_bound(usage['input_tokens'], usage['output_tokens'])
            or call['charged_cost'] != row[2]
            or call['charged_tokens'] != usage['input_tokens'] + usage['output_tokens']):
        raise Denied('Shared ledger/native call/wire/identity/receipt accounting mismatch')
    return row[2]


def reserve(host, epoch, job, identity, request, input_bound, output_bound, cost):
    index = _stage(epoch, job['spec'])
    profile = host._effective_research_profile(job)
    config = _settings(profile, index)
    if (integer(input_bound, 'input bound', 1) > INPUT_MAX[index] or output_bound != OUTPUT[index]
            or cost != cost_bound(input_bound, output_bound)):
        raise Denied('Complete call exceeds its unchanged role reservation')
    if host._now() + TIMEOUT[index] > min(epoch['created_at'] + 1800, job['spec']['deadline']):
        raise Denied('Insufficient remaining epoch time for the full call timeout')
    _target(host, epoch, job['spec'], index)
    with _ledger(host)._connect() as db:
        db.execute('BEGIN IMMEDIATE')
        state = _row(host, epoch, db)
        calls = state['calls']
        actual = [row[0] for row in host._db.execute(
            'SELECT id FROM research_calls WHERE epoch_id=? ORDER BY rowid', (epoch['id'],))]
        if state['revoked'] or actual != [c['call_id'] for c in calls] + [identity]:
            raise Denied('Revoked allocation or stale/rolled-back native reservation fence')
        if index != len(calls) or [c['stage'] for c in calls] != list(STAGES[:index]):
            raise Denied('Finite stage slot is out of order or already consumed')
        spent = sum(authenticate(host, epoch, call, db) for call in calls)
        if any(host._job(call['job_id'])['state'] != 'completed' for call in calls):
            raise Denied('A failed or incomplete prior stage cannot create a successor')
        if (spent + cost + _future_cost(index) > COST_CAP
                or _financial(db) + cost + _future_cost(index) > AGGREGATE_CAP):
            raise Denied('Actual full reservation plus protected later planning holds cannot be funded')
        if sum(c['input_bound'] + c['output_bound'] for c in calls) + input_bound + output_bound > TOKEN_CAP:
            raise Denied('Consumed token reservations never reset')
        run = (epoch['request']['resource_disposition']['discovery_run_ids'][job['spec']['allowed_workers'][0]]
               if index < 2 else 'controller-' + identity)
        entry = {'call_id': identity, 'stage': STAGES[index], 'job_id': job['id'],
                 'input_bound': input_bound, 'output_bound': output_bound, 'cost_bound': cost,
                 'wire_sha256': digest(wire_request(request, config)),
                 'prompt_version': profile['prompt_version'], 'run_id': run, 'dispatch_id': run + ':0'}
        db.execute('UPDATE research_epoch_budget_grants SET calls=? WHERE approval=?',
                   (canonical([*calls, entry]), APPROVAL))


def revoke(host, epoch):
    with _ledger(host)._connect() as db:
        db.execute('BEGIN IMMEDIATE')
        _row(host, epoch, db)
        db.execute('UPDATE research_epoch_budget_grants SET revoked=1 WHERE approval=?', (APPROVAL,))
    return {'epoch_id': epoch['id'], 'status': 'REVOKED', 'pending_calls_still_require_settlement': True}
