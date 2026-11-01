"""D090 one-use resource overlay; not a scientific or model-issued permission.

The shared spend ledger is outside registry rollback. A committed fence whose
registry transaction fails is deliberately NOT refunded or recreated.
"""
import hashlib
from pathlib import Path

from .codec import Invalid, canonical, decode, digest
from .errors import Conflict, Denied
from .openai_provider import MODEL, SpendLedger, cost_bound

POLICY = 'research-epoch-feedback-budget/1.0'
APPROVAL = 'SESSION-2026-10-29-FEEDBACK-BUDGET'
SPEC = 'docs/architecture/19_RESEARCH_EPOCH_FEEDBACK_BUDGET.md'
SPEC_SHA256 = '80453cb2e45e1f6efd4a748644bf1d6d1863feca1ca8f0e512f12de995b311fd'
TOKEN_CAP = 240000
COST_CAP = 1000000000
AGGREGATE_CAP = 5000000000


def _ledger(host):
    route = host._provider_routes.get(MODEL)
    if (route is None or route['provider'] != 'openai'
            or route['config']['test_budget_nano'] != AGGREGATE_CAP
            or not Path(route['budget_file']).is_file()):
        raise Denied('The overlay requires the existing host-selected OpenAI spend ledger')
    return SpendLedger(route['budget_file'], AGGREGATE_CAP)


def _schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS research_epoch_budget_grants(
        approval TEXT PRIMARY KEY, binding TEXT NOT NULL, calls TEXT NOT NULL,
        revoked INTEGER NOT NULL CHECK(revoked IN (0,1)))''')
    db.execute('''CREATE TRIGGER IF NOT EXISTS retain_epoch_budget_grant
        BEFORE DELETE ON research_epoch_budget_grants
        BEGIN SELECT RAISE(ABORT,'retain one-use authorization'); END''')
    db.execute('''CREATE TRIGGER IF NOT EXISTS immutable_epoch_budget_binding
        BEFORE UPDATE OF approval,binding ON research_epoch_budget_grants
        BEGIN SELECT RAISE(ABORT,'immutable one-use binding'); END''')
    db.execute('''CREATE TRIGGER IF NOT EXISTS permanent_epoch_budget_revocation
        BEFORE UPDATE OF revoked ON research_epoch_budget_grants WHEN OLD.revoked=1 AND NEW.revoked!=1
        BEGIN SELECT RAISE(ABORT,'permanent resource revocation'); END''')


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
    artifacts = [host._artifact(identity) for identity in context['artifact_ids']]
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
        return stage, (28238 + 10 * workers.index(worker) if used == 0 else 40000), 6000
    limits = {'formalization/v1': (27015, 18000), 'semantic-review/v1': (30000, 4000)}
    if kind not in limits or any(call['stage'] == kind for call in previous):
        raise Denied('The single downstream stage is unavailable or already consumed')
    return kind, *limits[kind]


def reserve(host, epoch, job, identity, input_bound, output_bound, cost):
    if input_bound + output_bound > 80000:
        raise Denied('The existing per-call token ceiling remains 80000')
    if cost != cost_bound(input_bound, output_bound):
        raise Denied('Overlay reservation must use the trusted conservative OpenAI tariff')
    profile = host._effective_research_profile(job)
    if profile['model'] != MODEL or profile['max_retries'] != 0:
        raise Denied('Overlay calls must preserve the approved model and no-retry policy')
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
