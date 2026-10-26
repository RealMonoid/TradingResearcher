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
from .errors import Conflict, Denied
from .memory import ResearchMemory
from .research_calls import ResearchCalls
from .formalization import FormalizationRecords
from .certification import ReferenceCertification
from .storage import ExternalStorage, RESERVED as STORAGE_SCHEMAS
from .data import DataSnapshots
from .features import FeatureCertification
from .binding import BoundComputation
from .evaluation_plans import EvaluationPlans
from .auxiliary import AuxiliaryResearch
from .bootstrap_runs import BootstrapRuns
from .information_runs import InformationDiagnostics
from .population_runs import PopulationWorlds
from .study_runs import InformationStudies
from .measurements import DevelopmentMeasurements
from .controller_providers import ControllerProviders, routes as provider_routes_config
from .meaning_reviews import MeaningReviews
from .revocations import DependencyRevocations
from .composition import CompositionCertification
from .data_use import DataUseAssessments


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


class Broker(ResearchMemory, ResearchCalls, FormalizationRecords, ReferenceCertification, ExternalStorage, DataSnapshots, FeatureCertification, BoundComputation, EvaluationPlans, AuxiliaryResearch, BootstrapRuns, InformationDiagnostics, PopulationWorlds, InformationStudies, DevelopmentMeasurements, ControllerProviders, MeaningReviews, DependencyRevocations, CompositionCertification, DataUseAssessments):
    def __init__(self, directory, clock=None, *, provider_routes=None):
        self._provider_routes = provider_routes_config(provider_routes)
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        existing_registry = (self.directory / 'registry.sqlite3').is_file()
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
            self._initialize_memory(existing_registry)
            self._initialize_research_calls(existing_registry)
            self._initialize_controller_providers(existing_registry)
            self._initialize_meaning_reviews(existing_registry)
            self._initialize_storage(existing_registry)
            self._verify()
            self._recover_reference_checks()
            self._recover_feature_checks()
            self._recover_bound_computations()
            self._recover_information_studies()
            from .calibration_runs import CalibrationStudies
            CalibrationStudies(self)._recover_information_studies()
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
        if op == 'invoke_auxiliary_provider':
            return self._invoke_auxiliary_provider_external(token, args)
        if op in ('prepare_evaluator_calibration','advance_evaluator_calibration','inspect_evaluator_calibration'):
            from .calibration_runs import CalibrationStudies
            runner=CalibrationStudies(self)
            if op=='prepare_evaluator_calibration':return runner._prepare_information_study_external(token,args)
            if set(args)!={'calibration_id'}:raise Invalid('Exact calibration identity required')
            method=(runner._advance_information_study_external if op=='advance_evaluator_calibration'
                else runner._inspect_information_study_external)
            return method(token,{'study_id':args['calibration_id']})
        if op == 'measure_development':
            return self._measure_development_external(token, args)
        if op == 'prepare_information_study':
            return self._prepare_information_study_external(token, args)
        if op == 'advance_information_study':
            return self._advance_information_study_external(token, args)
        if op == 'inspect_information_study':
            return self._inspect_information_study_external(token, args)
        if op == 'run_population_world':
            return self._run_population_world_external(token, args)
        if op == 'prepare_information_diagnostics':
            return self._prepare_information_diagnostics_external(token, args)
        if op == 'run_development_bootstrap':
            return self._run_development_bootstrap_external(token, args)
        canonical(args)
        if op == 'compile_hypothesis':
            return self._compile_hypothesis_external(token, args)
        if op == 'certify_composition':
            return self._certify_composition_external(token, args)
        if op == 'execute_development':
            return self._execute_development_external(token, args)
        if op == 'prepare_evaluation_plan':
            return self._prepare_evaluation_plan_external(token, args)
        if op == 'certify_features':
            return self._certify_features_external(token, args)
        if op == 'certify_reference':
            return self._certify_reference_external(token, args)
        if op == 'revalidate_reference':
            return self._certify_reference_external(token, args, retained=True)
        if op == 'add_blob_source':
            return self._add_blob_source_external(token, args)
        if op == 'register_data_snapshot':
            return self._register_data_snapshot_external(token, args)
        if op == 'backup_bundle':
            return self._backup_bundle_external(token, args)
        with self._transaction():
            actor = self._principal(token)
            worker_ops = {'claim', 'heartbeat', 'read_artifact', 'put_artifact', 'submit', 'block',
                          'record_research', 'search_memory', 'reserve_research_call',
                          'finish_research_call', 'research_call_state', 'record_formalization',
                          'auxiliary_input', 'record_semantic_review'}
            admin_ops = {'register_worker', 'add_source', 'create_context', 'create_batch', 'seal_batch',
                         'enqueue', 'resume', 'release_batch', 'inspect', 'status', 'verify',
                         'add_schedule', 'emit', 'tick', 'backup', 'get_artifact',
                         'add_research', 'inspect_memory', 'rebuild_memory',
                         'create_research_epoch', 'inspect_research_epoch', 'reference_certificate_status',
                         'inspect_reference_checks', 'feature_certificate_status', 'inspect_feature_checks',
                         'inspect_bound_computations','assess_meaning_review','inspect_meaning_review','inspect_evaluation_plan',
                         'revoke_dependency','inspect_dependency_use','composition_certificate_status','assess_data_use','inspect_data_use'}
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
        blob_refs = strings(envelope.get('blob_refs', []), 'blob references')
        for identity in blob_refs:
            if not self._db.execute('SELECT 1 FROM blobs WHERE sha256=?', (identity,)).fetchone():
                raise Denied('Artifact refers to an uncommitted blob')
        identity = digest(envelope)
        self._db.execute('INSERT OR IGNORE INTO artifacts VALUES(?,?)', (identity, canonical(envelope)))
        for blob_id in blob_refs:
            self._db.execute('INSERT OR IGNORE INTO artifact_blobs VALUES(?,?)', (identity, blob_id))
        return {'id': identity, **envelope}

    def _add_source(self, actor, body, data_class, exposure=None):
        if type(body) is dict and str(body.get('schema', '')).startswith(STORAGE_SCHEMAS):
            raise Invalid('Blob sources and reference packages require owned host operations')
        if type(body) is dict and str(body.get('schema', '')).startswith('implementation-certificate/'):
            raise Invalid('Implementation certificates require the host-owned validator')
        if type(body) is dict and str(body.get('schema', '')).startswith('formalization-record/'):
            raise Invalid('Formalization records require the owned formalizer operation')
        if type(body) is dict and str(body.get('schema', '')).startswith('research-record/'):
            raise Invalid('Use add_research for typed memory records')
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

    def _create_context(self, actor, role, epoch, artifact_ids, research_time=None):
        if role not in ('discovery', 'formalizer', 'executor', 'reporter'):
            raise Invalid('Unknown context role')
        integer(epoch, 'epoch')
        strings(artifact_ids, 'artifact_ids')
        research_time = self._now() if research_time is None else integer(research_time, 'research_time')
        if research_time > self._now():
            raise Invalid('Research time cannot be in the future')
        exposure = set(artifact_ids)
        for identity in artifact_ids:
            artifact = self._artifact(identity)
            if role in ('discovery','formalizer'):
                self._deny_final_calibration_ancestry(artifact)
            self._record_context_check(artifact, research_time, epoch)
            exposure.update(artifact['exposure'])
            if artifact['origin'] == 'source':
                if artifact['data_class'] != 'development' and role in ('discovery', 'formalizer'):
                    raise Denied('Protected raw input is unavailable to discovery/formalization')
            else:
                released = self._db.execute('SELECT epoch FROM releases WHERE artifact_id=?', (identity,)).fetchone()
                if released is None or epoch < released[0]:
                    raise Denied('Work product has not been released for this epoch')
        envelope = {'version': 'local-context/2', 'role': role, 'epoch': epoch,
                    'artifact_ids': sorted(artifact_ids), 'exposure': sorted(exposure),
                    'research_time': research_time}
        identity = digest(envelope)
        self._db.execute('INSERT OR IGNORE INTO contexts VALUES(?,?)', (identity, canonical(envelope)))
        self._event(actor['name'], 'context_frozen', context_id=identity)
        return {'id': identity, **envelope}

    def _deny_final_calibration_ancestry(self,artifact):
        pending=[artifact];seen=set()
        while pending:
            current=pending.pop()
            if current['id'] in seen:continue
            seen.add(current['id']);body=current.get('body')
            if type(body) is dict and str(body.get('schema','')).startswith(
                    ('evaluator-calibration-input/','evaluator-calibration-attempt/')):
                raise Denied('Reserved final calibration and its descendants are unavailable to research roles')
            for ref in set(current['source_refs'])|set(current['exposure']):
                if ref not in seen and self._db.execute('SELECT 1 FROM artifacts WHERE id=?',(ref,)).fetchone():
                    pending.append(self._artifact(ref))

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
        if type(spec) is not dict or not required <= set(spec) or set(spec) - required - {
                'batch_id', 'research_epoch_id','research_call_profile','research_inputs'}:
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
        self._research_spec_check(spec)
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
        spec=decode(canonical(spec))
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
        self._journal_attempt(job, state, detail)

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
        if artifact_id not in self._attempt_sources(actor, job, context):
            raise Denied('Artifact unavailable in frozen context')
        result = self._artifact(artifact_id)
        self._event(actor['name'], 'artifact_read', job_id=job['id'], artifact_id=artifact_id)
        return result

    def _put_artifact(self, actor, lease, body, source_refs):
        job = self._owned(actor, lease)
        context = self._context(job['spec']['context_id'])
        strings(source_refs, 'source_refs')
        if not set(source_refs) <= self._attempt_sources(actor, job, context):
            raise Denied('References must belong to the frozen context')
        if type(body) is dict and str(body.get('schema', '')).startswith(STORAGE_SCHEMAS):
            raise Invalid('Blob sources and reference packages require owned host operations')
        if type(body) is dict and str(body.get('schema', '')).startswith('research-record/'):
            raise Invalid('Use record_research for typed memory records')
        if type(body) is dict and str(body.get('schema', '')).startswith('implementation-certificate/'):
            raise Invalid('Implementation certificates require the host-owned validator')
        if type(body) is dict and str(body.get('schema', '')).startswith('formalization-record/'):
            raise Invalid('Use record_formalization for retained formalization records')
        return self._worker_artifact(actor, job, context, body, source_refs)

    def _worker_artifact(self, actor, job, context, body, source_refs):
        # Preserve the base snapshot and the separately accumulated private attempt.
        # A retry cannot quietly inherit an unreleased previous attempt's scratch.
        ancestry = self._attempt_sources(actor, job, context)
        exposure = set(context['exposure']) | ancestry
        for identity in ancestry:
            exposure.update(self._artifact(identity)['exposure'])
        result = self._save_artifact({'version': 'local-artifact/1', 'creator': actor['name'],
            'origin': 'worker', 'job_id': job['id'], 'generation': job['generation'],
            'context_id': context['id'], 'data_class': 'work_product', 'body': body,
            'source_refs': sorted(ancestry), 'cited_refs': sorted(source_refs),
            'exposure': sorted(exposure), 'authority': 'unverified_work_product'})
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
        identities = [row['result_id'] for row in rows]
        jobs = {row['id'] for row in rows}
        # Preserve all typed inquiry history of this completed batch, including
        # unsuccessful earlier attempts. Only the operator can release the batch.
        for record in self._db.execute('SELECT artifact_id FROM research_records ORDER BY seq'):
            artifact = self._artifact(record['artifact_id'])
            if artifact['origin'] in ('worker', 'controller') and artifact.get('job_id') in jobs:
                identities.append(record['artifact_id'])
        for record in self._db.execute('SELECT id,envelope FROM artifacts'):
            artifact = decode(record['envelope'])
            if (artifact['origin'] == 'worker' and artifact.get('job_id') in jobs
                    and type(artifact['body']) is dict and artifact['body'].get('schema') == 'formalization-record/1'):
                identities.append(record['id'])
        identities = list(dict.fromkeys(identities))
        for identity in identities:
            self._db.execute('INSERT OR IGNORE INTO releases VALUES(?,?,?)', (identity, target_epoch, batch_id))
        self._db.execute('UPDATE batches SET released_epoch=? WHERE id=?', (target_epoch, batch_id))
        self._event(actor['name'], 'batch_released', batch_id=batch_id, target_epoch=target_epoch)
        return {'artifact_ids': identities, 'epoch': target_epoch}

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
        blobs = self._verify_blobs()
        return {'status': blobs['status'], 'events': count, 'foreign_keys': True, 'synchronous': 'FULL',
                'schema_version': 1, 'scope': 'local coordination and research memory integrity only',
                'research_memory': self._verify_memory(), 'blobs': blobs}

    def _backup(self, actor, destination):
        if self._db.execute('SELECT 1 FROM blobs LIMIT 1').fetchone():
            raise Conflict('Database-only backup cannot omit blobs; use backup_bundle')
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
