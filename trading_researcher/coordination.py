"""Single-writer SQLite broker with authenticated, frozen worker capabilities.

The local operator and installed Python handlers are trusted. Workers/model tool
surfaces receive only the RPC capability, never database or administrator access.
This is not an OS sandbox or a scientific evaluator.
"""
from contextlib import closing, contextmanager
import hashlib
import inspect
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
import uuid

from . import checks
from .codec import Invalid, canonical, decode, digest, integer, strings, text


class Denied(PermissionError):
    pass


class Conflict(RuntimeError):
    pass


SCHEMA = '''
CREATE TABLE IF NOT EXISTS principals(name TEXT PRIMARY KEY, token_hash TEXT UNIQUE NOT NULL,
 role TEXT NOT NULL, capabilities TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS artifacts(id TEXT PRIMARY KEY, envelope TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS contexts(id TEXT PRIMARY KEY, envelope TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS batches(id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
 epoch INTEGER NOT NULL, sealed INTEGER NOT NULL DEFAULT 0, released_epoch INTEGER);
CREATE TABLE IF NOT EXISTS job_specs(id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
 envelope TEXT NOT NULL, context_id TEXT NOT NULL REFERENCES contexts(id),
 batch_id TEXT NOT NULL REFERENCES batches(id));
CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY REFERENCES job_specs(id),
 state TEXT NOT NULL, generation INTEGER NOT NULL DEFAULT 0, owner TEXT REFERENCES principals(name),
 lease_until INTEGER, result_id TEXT REFERENCES artifacts(id), detail TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS attempts(job_id TEXT NOT NULL REFERENCES jobs(id), generation INTEGER NOT NULL,
 owner TEXT NOT NULL REFERENCES principals(name), state TEXT NOT NULL,
 started_at INTEGER NOT NULL, ended_at INTEGER, result_id TEXT REFERENCES artifacts(id),
 detail TEXT NOT NULL DEFAULT '{}', PRIMARY KEY(job_id,generation));
CREATE TABLE IF NOT EXISTS releases(artifact_id TEXT PRIMARY KEY REFERENCES artifacts(id),
 epoch INTEGER NOT NULL, batch_id TEXT NOT NULL REFERENCES batches(id));
CREATE TABLE IF NOT EXISTS schedules(id TEXT PRIMARY KEY, request_key TEXT UNIQUE NOT NULL,
 envelope TEXT NOT NULL, next_at INTEGER, fired INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS trigger_deliveries(schedule_id TEXT NOT NULL REFERENCES schedules(id),
 occurrence TEXT NOT NULL, job_id TEXT NOT NULL REFERENCES jobs(id), PRIMARY KEY(schedule_id,occurrence));
CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, previous_hash TEXT NOT NULL,
 envelope TEXT NOT NULL, hash TEXT UNIQUE NOT NULL);
'''


class Broker:
    def __init__(self, directory, clock=None):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.clock = clock or (lambda: int(time.time()))
        self._mutex = threading.RLock()
        self._lock_file = (self.directory / 'writer.lock').open('a+b')
        self._db = None
        try:
            self._lock_file.seek(0)
            if os.name == 'nt':
                import msvcrt
                if self._lock_file.read(1) == b'':
                    self._lock_file.write(b'0')
                    self._lock_file.flush()
                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            self._lock_file.close()
            raise Conflict('Another broker owns this registry') from exc
        try:
            self._db = sqlite3.connect(self.directory / 'registry.sqlite3', isolation_level=None,
                                       check_same_thread=False)
            self._db.row_factory = sqlite3.Row
            self._db.execute('PRAGMA foreign_keys=ON')
            self._db.execute('PRAGMA synchronous=FULL')
            version = self._db.execute('PRAGMA user_version').fetchone()[0]
            if version not in (0, 1):
                raise Invalid('Unsupported registry schema; migration is required')
            self._db.executescript(SCHEMA)
            for table in ('artifacts', 'contexts', 'job_specs', 'events', 'releases'):
                for action in ('UPDATE', 'DELETE'):
                    self._db.execute(f'''CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action}
                        BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT,'immutable record'); END''')
            self._db.execute('PRAGMA user_version=1')
            key_path = self.directory / 'operator.key'
            if not self._db.execute('SELECT 1 FROM principals').fetchone():
                if key_path.exists():
                    # A previous process may have stopped after persisting the key.
                    token = key_path.read_text(encoding='utf-8').strip()
                    if not 32 <= len(token) <= 256:
                        raise Conflict('Incomplete bootstrap credential; no principal was granted')
                else:
                    token = secrets.token_urlsafe(32)
                    # Persist the recovery credential before granting authority in the DB.
                    descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                    with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                        stream.write(token)
                        stream.flush()
                        os.fsync(stream.fileno())
                self._db.execute('INSERT INTO principals VALUES(?,?,?,?)',
                                 ('operator', self._token_hash(token), 'operator', '[]'))
            self.admin_token = key_path.read_text(encoding='utf-8').strip()
            if self._principal(self.admin_token)['role'] != 'operator':
                raise Denied('Operator credential mismatch')
            self._verify()
        except BaseException:
            self.close()
            raise

    def close(self):
        with self._mutex:
            if self._db is not None:
                self._db.close()
                self._db = None
            if not self._lock_file.closed:
                if os.name == 'nt':
                    import msvcrt
                    self._lock_file.seek(0)
                    msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                self._lock_file.close()

    @staticmethod
    def _token_hash(token):
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def _now(self):
        return integer(self.clock(), 'host time')

    @contextmanager
    def _transaction(self):
        with self._mutex:
            self._db.execute('BEGIN IMMEDIATE')
            try:
                yield
                self._db.execute('COMMIT')
            except BaseException:
                self._db.execute('ROLLBACK')
                raise

    def _principal(self, token):
        if type(token) is not str or len(token) > 256:
            raise Denied('Invalid capability')
        row = self._db.execute('SELECT * FROM principals WHERE token_hash=?',
                               (self._token_hash(token),)).fetchone()
        if row is None:
            raise Denied('Invalid capability')
        return dict(row)

    def call(self, token, op, **args):
        canonical(args)
        with self._transaction():
            actor = self._principal(token)
            worker_ops = {'claim', 'heartbeat', 'read_artifact', 'put_artifact', 'submit', 'block'}
            admin_ops = {'register_worker', 'add_source', 'create_context', 'create_batch', 'seal_batch',
                         'enqueue', 'resume', 'release_batch', 'inspect', 'status', 'verify',
                         'add_schedule', 'emit', 'tick', 'backup', 'get_artifact'}
            allowed = admin_ops if actor['role'] == 'operator' else worker_ops
            if op not in allowed:
                raise Denied('Operation unavailable for this capability')
            method = getattr(self, '_' + op)
            try:
                inspect.signature(method).bind(actor, **args)
            except TypeError as exc:
                raise Invalid('Unexpected or missing request fields') from exc
            result = method(actor, **args)
            # Reject an undeliverable response before committing any mutation.
            canonical(result)
            return result

    def _event(self, actor, action, **details):
        last = self._db.execute('SELECT hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        previous = last[0] if last else '0' * 64
        envelope = {'time': self._now(), 'actor': actor, 'action': action, 'details': details}
        body = canonical(envelope)
        value = hashlib.sha256((previous + body).encode('utf-8')).hexdigest()
        self._db.execute('INSERT INTO events(previous_hash,envelope,hash) VALUES(?,?,?)', (previous, body, value))

    def _register_worker(self, actor, name, role, capabilities):
        text(name, 'worker name')
        if name in ('operator', 'controller'):
            raise Invalid('This identity is reserved for the host')
        if role not in ('discovery', 'formalizer', 'executor', 'reporter'):
            raise Invalid('Unsupported worker role')
        strings(capabilities, 'capabilities')
        if self._db.execute('SELECT 1 FROM principals WHERE name=?', (name,)).fetchone():
            raise Conflict('Worker identity already exists')
        token = secrets.token_urlsafe(32)
        self._db.execute('INSERT INTO principals VALUES(?,?,?,?)',
                         (name, self._token_hash(token), role, canonical(capabilities)))
        self._event(actor['name'], 'worker_registered', name=name, role=role, capabilities=capabilities)
        return {'name': name, 'token': token}

    def _artifact(self, artifact_id):
        row = self._db.execute('SELECT envelope FROM artifacts WHERE id=?', (artifact_id,)).fetchone()
        if row is None:
            raise Denied('Artifact unavailable')
        envelope = decode(row[0])
        if digest(envelope) != artifact_id:
            raise Conflict('Artifact integrity failure')
        return {'id': artifact_id, **envelope}

    def _save_artifact(self, envelope):
        identity = digest(envelope)
        self._db.execute('INSERT OR IGNORE INTO artifacts VALUES(?,?)', (identity, canonical(envelope)))
        return {'id': identity, **envelope}

    def _add_source(self, actor, body, data_class, exposure=None):
        if data_class not in ('development', 'assessment', 'operations'):
            raise Invalid('Unknown source class')
        exposure = strings(exposure or [], 'exposure')
        result = self._save_artifact({'version': 'local-artifact/1', 'creator': actor['name'],
            'origin': 'source', 'data_class': data_class, 'body': body, 'source_refs': [],
            'exposure': sorted(exposure), 'authority': 'supplied_source_not_certified'})
        self._event(actor['name'], 'source_registered', artifact_id=result['id'])
        return result

    def _context(self, context_id):
        row = self._db.execute('SELECT envelope FROM contexts WHERE id=?', (context_id,)).fetchone()
        if row is None:
            raise Denied('Context unavailable')
        value = decode(row[0])
        if digest(value) != context_id:
            raise Conflict('Context integrity failure')
        return {'id': context_id, **value}

    def _create_context(self, actor, role, epoch, artifact_ids):
        if role not in ('discovery', 'formalizer', 'executor', 'reporter'):
            raise Invalid('Unknown context role')
        integer(epoch, 'epoch')
        strings(artifact_ids, 'artifact_ids')
        exposure = set(artifact_ids)
        for identity in artifact_ids:
            artifact = self._artifact(identity)
            exposure.update(artifact['exposure'])
            if artifact['origin'] == 'source':
                if artifact['data_class'] != 'development' and role in ('discovery', 'formalizer'):
                    raise Denied('Protected raw input is unavailable to discovery/formalization')
            else:
                released = self._db.execute('SELECT epoch FROM releases WHERE artifact_id=?', (identity,)).fetchone()
                if released is None or epoch < released[0]:
                    raise Denied('Work product has not been released for this epoch')
        envelope = {'version': 'local-context/1', 'role': role, 'epoch': epoch,
                    'artifact_ids': sorted(artifact_ids), 'exposure': sorted(exposure)}
        identity = digest(envelope)
        self._db.execute('INSERT OR IGNORE INTO contexts VALUES(?,?)', (identity, canonical(envelope)))
        self._event(actor['name'], 'context_frozen', context_id=identity)
        return {'id': identity, **envelope}

    def _create_batch(self, actor, key, epoch):
        text(key, 'batch key')
        integer(epoch, 'epoch')
        row = self._db.execute('SELECT * FROM batches WHERE request_key=?', (key,)).fetchone()
        if row:
            if row['epoch'] != epoch:
                raise Conflict('Batch key has different content')
            return {'id': row['id']}
        identity = uuid.uuid4().hex
        self._db.execute('INSERT INTO batches(id,request_key,epoch) VALUES(?,?,?)', (identity, key, epoch))
        self._event(actor['name'], 'batch_created', batch_id=identity)
        return {'id': identity}

    def _seal_batch(self, actor, batch_id):
        row = self._db.execute('SELECT * FROM batches WHERE id=?', (batch_id,)).fetchone()
        if row is None or not self._db.execute('SELECT 1 FROM job_specs WHERE batch_id=?', (batch_id,)).fetchone():
            raise Invalid('Cannot seal an absent or empty batch')
        self._db.execute('UPDATE batches SET sealed=1 WHERE id=?', (batch_id,))
        self._event(actor['name'], 'batch_sealed', batch_id=batch_id)
        return {'id': batch_id, 'sealed': True}

    def _spec(self, spec):
        required = {'kind', 'context_id', 'purpose', 'allowed_workers', 'max_attempts',
                    'lease_seconds', 'deadline', 'dependencies'}
        if type(spec) is not dict or not required <= set(spec) or set(spec) - required - {'batch_id'}:
            raise Invalid('Job specification fields are missing or unexpected')
        text(spec['kind'], 'kind')
        text(spec['purpose'], 'purpose')
        strings(spec['allowed_workers'], 'allowed_workers')
        if not spec['allowed_workers']:
            raise Invalid('An explicit worker allowlist is required')
        strings(spec['dependencies'], 'dependencies')
        integer(spec['max_attempts'], 'max_attempts', 1)
        # Integer-second host clocks can shorten the initial lease by <1 second.
        # Three seconds leaves room before the wrapper's first lease/3 heartbeat.
        integer(spec['lease_seconds'], 'lease_seconds', 3)
        integer(spec['deadline'], 'deadline', 1)
        context = self._context(spec['context_id'])
        for name in spec['allowed_workers']:
            row = self._db.execute('SELECT role,capabilities FROM principals WHERE name=?', (name,)).fetchone()
            if row is None or row['role'] != context['role'] or spec['kind'] not in decode(row['capabilities']):
                raise Invalid('Worker does not have the required role/capability')
        for dependency in spec['dependencies']:
            if not self._db.execute('SELECT 1 FROM jobs WHERE id=?', (dependency,)).fetchone():
                raise Invalid('Dependency must already be registered')
        return context

    def _enqueue(self, actor, key, spec):
        text(key, 'job key')
        row = self._db.execute('SELECT id,envelope FROM job_specs WHERE request_key=?', (key,)).fetchone()
        if row:
            if row['envelope'] != canonical(spec):
                raise Conflict('Job key has different content')
            return {'id': row['id']}
        context = self._spec(spec)
        batch_id = spec.get('batch_id')
        if batch_id:
            batch = self._db.execute('SELECT * FROM batches WHERE id=?', (batch_id,)).fetchone()
            if batch is None or batch['sealed'] or batch['epoch'] != context['epoch']:
                raise Conflict('Batch is absent, sealed or belongs to a different epoch')
        else:
            # An operator's chosen batch key must not alias this implicit batch.
            batch_id = self._create_batch(actor, 'standalone:' + uuid.uuid4().hex, context['epoch'])['id']
            self._db.execute('UPDATE batches SET sealed=1 WHERE id=?', (batch_id,))
        identity = uuid.uuid4().hex
        self._db.execute('INSERT INTO job_specs VALUES(?,?,?,?,?)',
                         (identity, key, canonical(spec), context['id'], batch_id))
        supported = spec['kind'] in checks.VERSIONS
        state = 'ready' if supported else 'blocked'
        detail = {} if supported else {'reason': 'Trusted completion check unavailable', 'needs': [spec['kind']]}
        self._db.execute('INSERT INTO jobs(id,state,detail) VALUES(?,?,?)', (identity, state, canonical(detail)))
        self._event(actor['name'], 'job_enqueued', job_id=identity, state=state)
        return {'id': identity}

    def _job(self, job_id):
        row = self._db.execute('''SELECT jobs.*,job_specs.envelope,job_specs.batch_id
                                 FROM jobs JOIN job_specs USING(id) WHERE id=?''', (job_id,)).fetchone()
        if row is None:
            raise Denied('Work unavailable')
        result = dict(row)
        result['spec'] = decode(result.pop('envelope'))
        result['detail'] = decode(result['detail'])
        return result

    def _finish_attempt(self, job, state, detail, result_id=None):
        self._db.execute('''UPDATE attempts SET state=?,ended_at=?,detail=?,result_id=?
                            WHERE job_id=? AND generation=?''',
                         (state, self._now(), canonical(detail), result_id, job['id'], job['generation']))

    def _expire(self):
        now = self._now()
        for row in self._db.execute("SELECT id FROM jobs WHERE state IN ('ready','running')").fetchall():
            job = self._job(row['id'])
            expired = job['state'] == 'running' and job['lease_until'] <= now
            deadline = job['spec']['deadline'] <= now
            if not expired and not deadline:
                continue
            detail = {'reason': 'Deadline exceeded' if deadline else 'Lease expired'}
            if job['state'] == 'running':
                self._finish_attempt(job, 'expired', detail)
            state = 'failed' if deadline or job['generation'] >= job['spec']['max_attempts'] else 'ready'
            self._db.execute('UPDATE jobs SET state=?,owner=NULL,lease_until=NULL,detail=? WHERE id=?',
                             (state, canonical(detail), job['id']))
            self._event('controller', 'attempt_expired', job_id=job['id'], state=state)

    def _claim(self, actor):
        self._expire()
        # Initial contract is sequential. The broker serializes model work globally.
        if self._db.execute("SELECT 1 FROM jobs WHERE state='running'").fetchone():
            return None
        rows = self._db.execute("SELECT id FROM jobs WHERE state='ready' ORDER BY rowid").fetchall()
        for row in rows:
            job = self._job(row['id'])
            spec = job['spec']
            if not self._db.execute('SELECT sealed FROM batches WHERE id=?', (job['batch_id'],)).fetchone()[0]:
                continue
            if any(self._job(dep)['state'] != 'completed' for dep in spec['dependencies']):
                continue
            # First eligible task retains the host order; workers cannot cherry-pick IDs.
            if actor['name'] not in spec['allowed_workers']:
                return None
            generation = job['generation'] + 1
            until = min(self._now() + spec['lease_seconds'], spec['deadline'])
            self._db.execute("UPDATE jobs SET state='running',owner=?,generation=?,lease_until=?,detail='{}' WHERE id=?",
                             (actor['name'], generation, until, job['id']))
            self._db.execute('INSERT INTO attempts(job_id,generation,owner,state,started_at) VALUES(?,?,?,?,?)',
                             (job['id'], generation, actor['name'], 'running', self._now()))
            self._event(actor['name'], 'claimed', job_id=job['id'], generation=generation)
            return {'lease': {'job_id': job['id'], 'generation': generation}, 'lease_until': until,
                    'spec': spec, 'context': self._context(spec['context_id'])}
        return None

    def _owned(self, actor, lease):
        if type(lease) is not dict or set(lease) != {'job_id', 'generation'}:
            raise Denied('Invalid work capability')
        if type(lease['job_id']) is not str or type(lease['generation']) is not int:
            raise Denied('Invalid work capability')
        job = self._job(lease['job_id'])
        if (job['owner'] != actor['name'] or job['generation'] != lease['generation']
                or job['state'] != 'running' or job['lease_until'] <= self._now()
                or job['spec']['deadline'] <= self._now()):
            raise Denied('Work capability is not current')
        return job

    def _heartbeat(self, actor, lease):
        job = self._owned(actor, lease)
        until = min(self._now() + job['spec']['lease_seconds'], job['spec']['deadline'])
        self._db.execute('UPDATE jobs SET lease_until=? WHERE id=?', (until, job['id']))
        return {'lease_until': until}

    def _read_artifact(self, actor, lease, artifact_id):
        job = self._owned(actor, lease)
        context = self._context(job['spec']['context_id'])
        if artifact_id not in context['artifact_ids']:
            raise Denied('Artifact unavailable in frozen context')
        result = self._artifact(artifact_id)
        self._event(actor['name'], 'artifact_read', job_id=job['id'], artifact_id=artifact_id)
        return result

    def _put_artifact(self, actor, lease, body, source_refs):
        job = self._owned(actor, lease)
        context = self._context(job['spec']['context_id'])
        strings(source_refs, 'source_refs')
        if not set(source_refs) <= set(context['artifact_ids']):
            raise Denied('References must belong to the frozen context')
        # Conservatively inherit the entire supplied context, not worker-selected ancestry.
        result = self._save_artifact({'version': 'local-artifact/1', 'creator': actor['name'],
            'origin': 'worker', 'job_id': job['id'], 'generation': job['generation'],
            'context_id': context['id'], 'data_class': 'work_product', 'body': body,
            'source_refs': sorted(set(context['artifact_ids'])), 'cited_refs': sorted(source_refs),
            'exposure': context['exposure'], 'authority': 'unverified_work_product'})
        self._event(actor['name'], 'artifact_staged', job_id=job['id'], artifact_id=result['id'])
        return {'id': result['id']}

    def _submit(self, actor, lease, artifact_id):
        # A retry of the exact accepted/rejected delivery is safe after acknowledgement loss.
        if type(lease) is dict and set(lease) == {'job_id', 'generation'}:
            prior = self._db.execute('SELECT * FROM attempts WHERE job_id=? AND generation=?',
                                     (lease['job_id'], lease['generation'])).fetchone()
            if prior and prior['owner'] == actor['name'] and prior['state'] in ('completed', 'rejected'):
                if prior['result_id'] != artifact_id:
                    raise Conflict('Attempt already submitted a different result')
                return decode(prior['detail'])
        job = self._owned(actor, lease)
        result = self._artifact(artifact_id)
        if (result['origin'] != 'worker' or result['creator'] != actor['name']
                or result['job_id'] != job['id'] or result['generation'] != job['generation']):
            raise Denied('Result does not belong to this attempt')
        context = self._context(job['spec']['context_id'])
        sources = [self._artifact(ref) for ref in context['artifact_ids']]
        try:
            message = checks.validate(job['spec']['kind'], result['body'], sources)
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

    def _block(self, actor, lease, reason, needs, retry_when):
        job = self._owned(actor, lease)
        detail = {'reason': text(reason, 'reason'), 'needs': strings(needs, 'needs'),
                  'retry_when': text(retry_when, 'retry_when')}
        self._finish_attempt(job, 'blocked', detail)
        self._db.execute("UPDATE jobs SET state='blocked',lease_until=NULL,detail=? WHERE id=?",
                         (canonical(detail), job['id']))
        self._event(actor['name'], 'blocked', job_id=job['id'], **detail)
        return {'state': 'blocked'}

    def _resume(self, actor, job_id, reason):
        text(reason, 'resume reason')
        job = self._job(job_id)
        if (job['state'] != 'blocked' or job['generation'] >= job['spec']['max_attempts']
                or job['spec']['deadline'] <= self._now() or job['spec']['kind'] not in checks.VERSIONS):
            raise Conflict('Task cannot resume within its existing contract')
        self._db.execute("UPDATE jobs SET state='ready',owner=NULL WHERE id=?", (job_id,))
        self._event(actor['name'], 'resumed', job_id=job_id, reason=reason)
        return {'state': 'ready'}

    def _release_batch(self, actor, batch_id, target_epoch):
        integer(target_epoch, 'target_epoch')
        batch = self._db.execute('SELECT * FROM batches WHERE id=?', (batch_id,)).fetchone()
        if batch is None or not batch['sealed'] or target_epoch <= batch['epoch']:
            raise Conflict('Release requires a sealed batch and later epoch')
        rows = self._db.execute('SELECT jobs.* FROM jobs JOIN job_specs USING(id) WHERE batch_id=?', (batch_id,)).fetchall()
        if not rows or any(r['state'] != 'completed' for r in rows):
            raise Conflict('Incomplete batch cannot release partial results')
        if batch['released_epoch'] is not None and batch['released_epoch'] != target_epoch:
            raise Conflict('Release epoch is immutable')
        for row in rows:
            self._db.execute('INSERT OR IGNORE INTO releases VALUES(?,?,?)', (row['result_id'], target_epoch, batch_id))
        self._db.execute('UPDATE batches SET released_epoch=? WHERE id=?', (target_epoch, batch_id))
        self._event(actor['name'], 'batch_released', batch_id=batch_id, target_epoch=target_epoch)
        return {'artifact_ids': [r['result_id'] for r in rows], 'epoch': target_epoch}

    @staticmethod
    def _page(limit, after):
        integer(limit, 'limit', 1)
        integer(after, 'after')
        if limit > 50:
            raise Invalid('Page limit must not exceed 50')

    def _inspect(self, actor, job_id, after=0, limit=50):
        self._page(limit, after)
        job = self._job(job_id)
        rows = self._db.execute('''SELECT * FROM attempts WHERE job_id=? AND generation>?
                                  ORDER BY generation LIMIT ?''', (job_id, after, limit + 1)).fetchall()
        job['attempts'] = [{**dict(r), 'detail': decode(r['detail'])} for r in rows[:limit]]
        job['next_cursor'] = rows[limit - 1]['generation'] if len(rows) > limit else None
        return job

    def _get_artifact(self, actor, artifact_id):
        return self._artifact(artifact_id)

    def _status(self, actor, after=0, limit=50):
        self._page(limit, after)
        self._expire()
        rows = self._db.execute('''SELECT rowid,id,state,generation,owner,lease_until,result_id
                                  FROM jobs WHERE rowid>? ORDER BY rowid LIMIT ?''', (after, limit + 1)).fetchall()
        jobs = [{key: row[key] for key in row.keys() if key != 'rowid'} for row in rows[:limit]]
        return {'jobs': jobs, 'next_cursor': rows[limit - 1]['rowid'] if len(rows) > limit else None,
                'scientific_authority': False}

    def _add_schedule(self, actor, key, spec, max_fires, at=None, interval=None, event_type=None):
        text(key, 'schedule key')
        integer(max_fires, 'max_fires', 1)
        self._spec(spec)
        if 'batch_id' in spec:
            raise Invalid('Triggers cannot append to a predeclared batch')
        if (at is None) == (event_type is None):
            raise Invalid('Choose one time trigger or event trigger')
        if at is not None:
            integer(at, 'at')
            if interval is not None:
                integer(interval, 'interval', 1)
            elif max_fires != 1:
                raise Invalid('A one-shot timer must have max_fires=1')
        else:
            text(event_type, 'event_type')
            if interval is not None:
                raise Invalid('Event triggers have no interval')
        envelope = {'spec': spec, 'at': at, 'interval': interval,
                    'event_type': event_type, 'max_fires': max_fires}
        row = self._db.execute('SELECT * FROM schedules WHERE request_key=?', (key,)).fetchone()
        if row:
            if row['envelope'] != canonical(envelope):
                raise Conflict('Schedule key has different content')
            return {'id': row['id']}
        identity = uuid.uuid4().hex
        self._db.execute('INSERT INTO schedules(id,request_key,envelope,next_at) VALUES(?,?,?,?)',
                         (identity, key, canonical(envelope), at))
        self._event(actor['name'], 'schedule_registered', schedule_id=identity)
        return {'id': identity}

    def _fire(self, actor, schedule, occurrence):
        prior = self._db.execute('SELECT job_id FROM trigger_deliveries WHERE schedule_id=? AND occurrence=?',
                                 (schedule['id'], occurrence)).fetchone()
        if prior:
            return prior[0]
        config = decode(schedule['envelope'])
        if schedule['fired'] >= config['max_fires']:
            return None
        job = self._enqueue(actor, 'trigger:' + schedule['id'] + ':' + occurrence, config['spec'])
        self._db.execute('INSERT INTO trigger_deliveries VALUES(?,?,?)', (schedule['id'], occurrence, job['id']))
        self._db.execute('UPDATE schedules SET fired=fired+1 WHERE id=?', (schedule['id'],))
        self._event('controller', 'trigger_fired', schedule_id=schedule['id'], occurrence=occurrence, job_id=job['id'])
        return job['id']

    def _emit(self, actor, event_type, event_id):
        text(event_type, 'event_type')
        text(event_id, 'event_id')
        jobs = []
        for row in self._db.execute('SELECT * FROM schedules ORDER BY rowid').fetchall():
            if decode(row['envelope'])['event_type'] == event_type:
                job = self._fire(actor, row, 'event:' + event_id)
                if job:
                    jobs.append(job)
        return {'enqueued': jobs, 'scientific_authority': False}

    def _tick(self, actor):
        self._expire()
        jobs = []
        # Bounded catch-up, retaining every missed occurrence rather than silently skipping.
        for _ in range(64):
            row = self._db.execute('SELECT * FROM schedules WHERE next_at<=? ORDER BY next_at,rowid LIMIT 1',
                                   (self._now(),)).fetchone()
            if row is None:
                break
            config = decode(row['envelope'])
            job = self._fire(actor, row, 'time:' + str(row['next_at']))
            if job:
                jobs.append(job)
            next_at = (row['next_at'] + config['interval']
                       if config['interval'] and row['fired'] + 1 < config['max_fires'] else None)
            self._db.execute('UPDATE schedules SET next_at=? WHERE id=?', (next_at, row['id']))
        return {'enqueued': jobs, 'scientific_authority': False}

    def _verify(self, actor=None):
        if self._db.execute('PRAGMA foreign_keys').fetchone()[0] != 1:
            raise Conflict('Foreign keys are disabled')
        if self._db.execute('PRAGMA synchronous').fetchone()[0] != 2:
            raise Conflict('FULL synchronization is disabled')
        if self._db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or self._db.execute('PRAGMA foreign_key_check').fetchall():
            raise Conflict('Registry integrity failure')
        for table in ('artifacts', 'contexts'):
            for row in self._db.execute(f'SELECT id,envelope FROM {table}'):
                if digest(decode(row['envelope'])) != row['id']:
                    raise Conflict(f'{table} content hash mismatch')
        previous = '0' * 64
        count = 0
        for row in self._db.execute('SELECT * FROM events ORDER BY seq'):
            expected = hashlib.sha256((previous + row['envelope']).encode('utf-8')).hexdigest()
            if row['previous_hash'] != previous or row['hash'] != expected:
                raise Conflict('Audit chain mismatch')
            previous, count = row['hash'], count + 1
        return {'status': 'PASS', 'events': count, 'foreign_keys': True, 'synchronous': 'FULL',
                'schema_version': 1, 'scope': 'local coordination integrity only'}

    def _backup(self, actor, destination):
        # Backup uses a separate read connection; backing up the active write transaction blocks.
        path = Path(destination).resolve()
        if path.exists():
            raise Conflict('Backup destination already exists')
        path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.directory / 'registry.sqlite3')) as source:
            with closing(sqlite3.connect(path)) as target:
                source.backup(target)
                if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise Conflict('Backup integrity check failed')
        return {'path': str(path), 'status': 'PASS', 'credentials_included': False}
