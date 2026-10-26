"""Typed research history and permission-scoped projections, research-memory/1.

Records retain observations and interpretations. No public memory operation can
issue scientific evidence; the market-model projection awaits the independent
evaluator. The SQLite index is disposable; immutable artifacts are authoritative.
"""
from contextlib import closing
import hashlib
import os
import sqlite3
import tempfile

from .codec import Invalid, canonical, decode, integer, strings, text
from .errors import Conflict, Denied


SCHEMA = 'research-record/1'
VIEWS = ('journal', 'market_model', 'research_experience', 'policy_experience')
FIELDS = {
    'source': ({'text', 'uri'}, {'retrieved_at', 'availability_note'}),
    'idea': ({'text'}, {'assumptions', 'uncertainty', 'question'}),
    'observation': ({'text'}, {'uncertainty', 'measurement'}),
    'gap': ({'text', 'reason', 'reopen_condition'}, {'uncertainty'}),
    'attempt': ({'text', 'outcome'}, {'error', 'next_action', 'job_id', 'generation', 'details'}),
    'research_experience': ({'text', 'interpretation'}, {'uncertainty', 'next_action'}),
    'policy_experience': ({'text', 'interpretation'}, {'uncertainty', 'next_action'}),
}
RELATIONS = {'supersedes', 'contradicts', 'depends_on'}
WRITERS = {
    'discovery': {'idea', 'observation', 'gap', 'attempt', 'research_experience'},
    'formalizer': {'idea', 'observation', 'gap', 'attempt', 'research_experience'},
    'executor': {'observation', 'gap', 'attempt', 'policy_experience'},
    'reporter': {'observation', 'gap', 'attempt'},
}


def scope_object(scope):
    if type(scope) is not dict or len(scope) > 32:
        raise Invalid('Scope must be a bounded object')
    for key, value in scope.items():
        text(key, 'scope key')
        if type(value) is list:
            strings(value, 'scope values')
        else:
            text(value, 'scope value')
    return scope


def validate_record(record):
    required = {'schema', 'kind', 'content', 'scope', 'relations', 'created_at', 'available_at'}
    if type(record) is not dict or set(record) != required or record['schema'] != SCHEMA:
        raise Invalid('Unsupported or incomplete research-record schema')
    kind, content = record['kind'], record['content']
    if type(kind) is not str or kind not in FIELDS:
        raise Invalid('Unsupported research record kind; scientific publication is not a memory tool')
    required_content, optional = FIELDS[kind]
    if (type(content) is not dict or not required_content <= set(content)
            or set(content) - required_content - optional):
        raise Invalid('Unexpected or missing record content fields')
    for name, value in content.items():
        if name == 'assumptions':
            strings(value, name)
        elif name in ('retrieved_at', 'generation'):
            integer(value, name)
        elif name == 'details':
            if type(value) is not dict:
                raise Invalid('Attempt details must be an object')
            canonical(value)
        else:
            text(value, name)
    scope_object(record['scope'])
    relations = record['relations']
    if type(relations) is not dict or set(relations) - RELATIONS:
        raise Invalid('Unsupported record relationship')
    for values in relations.values():
        strings(values, 'relationship targets')
    integer(record['created_at'], 'created_at')
    integer(record['available_at'], 'available_at')
    if record['available_at'] < record['created_at']:
        raise Invalid('A record cannot be available before it was recorded')
    canonical(record)
    return record


def view_for(kind):
    return kind if kind in ('research_experience', 'policy_experience') else 'journal'


class ResearchMemory:
    """Mixin: all operations run inside Broker.call's authenticated transaction."""

    def _initialize_memory(self, existing):
        found = self._db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_meta'").fetchone()
        if found:
            version = self._db.execute('SELECT version FROM research_meta WHERE singleton=1').fetchone()
            if version is None or version[0] != 1:
                raise Invalid('Unsupported research-memory schema; migration required')
            return
        if existing:
            self._preserve_schema_checkpoint('before-research-memory-v1.sqlite3')
        with self._transaction():
            self._db.execute('CREATE TABLE research_meta(singleton INTEGER PRIMARY KEY CHECK(singleton=1), version INTEGER NOT NULL)')
            self._db.execute('CREATE TABLE research_records(seq INTEGER PRIMARY KEY, artifact_id TEXT UNIQUE NOT NULL REFERENCES artifacts(id), kind TEXT NOT NULL, view_name TEXT NOT NULL)')
            self._db.execute('INSERT INTO research_meta VALUES(1,1)')
            self._rebuild_memory({'name': 'controller'})

    def _preserve_schema_checkpoint(self, name):
        backup = self.directory / name
        # A pathname alone is not evidence of a completed or matching backup.
        if not backup.exists():
            descriptor, filename = tempfile.mkstemp(prefix='schema-backup-', suffix='.pending',
                                                    dir=self.directory)
            os.close(descriptor)
            try:
                with closing(sqlite3.connect(filename)) as target:
                    self._db.backup(target)
                    self._check_migration_backup(target)
                with open(filename, 'r+b') as stream:
                    os.fsync(stream.fileno())
                os.replace(filename, backup)
            finally:
                if os.path.exists(filename):
                    os.unlink(filename)
        try:
            with closing(sqlite3.connect(backup.as_uri() + '?mode=ro', uri=True)) as target:
                self._check_migration_backup(target)
        except sqlite3.DatabaseError as exc:
            raise Conflict('Pre-migration backup is unreadable; original registry retained') from exc

    def _check_migration_backup(self, target):
        if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise Conflict('Pre-migration backup integrity failure')
        def checksum(connection):
            result = hashlib.sha256()
            for line in connection.iterdump():
                result.update(line.encode('utf-8') + b'\n')
            return result.digest()
        if checksum(target) != checksum(self._db):
            raise Conflict('Pre-migration backup does not match the original registry')

    def _attempt_sources(self, actor, job, context):
        identities = set(context['artifact_ids'])
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            envelope = decode(row['envelope'])
            owned = (envelope['origin'] == 'worker' and envelope['creator'] == actor['name'])
            supplied = (envelope['origin'] == 'controller' and envelope.get('exposed_to') == actor['name'])
            if ((owned or supplied)
                    and envelope.get('job_id') == job['id']
                    and envelope.get('generation') == job['generation']):
                identities.add(row['id'])
        return identities

    def _make_record(self, kind, content, scope, relations, available_at):
        now = self._now()
        return validate_record({'schema': SCHEMA, 'kind': kind, 'content': content,
                                'scope': scope, 'relations': {} if relations is None else relations,
                                'created_at': now,
                                'available_at': now if available_at is None else available_at})

    def _index_record(self, artifact_id, record):
        validate_record(record)
        seq = self._db.execute('SELECT rowid FROM artifacts WHERE id=?', (artifact_id,)).fetchone()[0]
        self._db.execute('INSERT OR IGNORE INTO research_records VALUES(?,?,?,?)',
                         (seq, artifact_id, record['kind'], view_for(record['kind'])))

    def _add_research(self, actor, kind, content, scope, source_refs,
                      relations=None, available_at=None, data_class='development'):
        if data_class not in ('development', 'assessment', 'operations'):
            raise Invalid('Unknown data class')
        record = self._make_record(kind, content, scope, relations, available_at)
        strings(source_refs, 'source_refs')
        references = set(source_refs)
        for targets in record['relations'].values():
            references.update(targets)
        exposure, epoch = set(references), 0
        for ref in sorted(references):
            parent = self._artifact(ref)
            exposure.update(parent['exposure'])
            if parent['origin'] != 'source':
                release = self._db.execute('SELECT epoch FROM releases WHERE artifact_id=?', (ref,)).fetchone()
                if release is None:
                    raise Denied('Unreleased provenance cannot be imported as a source')
                epoch = max(epoch, release[0])
            epoch = max(epoch, parent.get('not_before_epoch', 0))
            if parent['data_class'] == 'assessment':
                data_class = 'assessment'
            elif parent['data_class'] == 'operations' and data_class != 'assessment':
                data_class = 'operations'
            record['available_at'] = max(record['available_at'], self._artifact_availability(parent))
        artifact = self._save_artifact({'version': 'local-artifact/1', 'creator': actor['name'],
            'origin': 'source', 'data_class': data_class, 'body': record,
            'source_refs': sorted(references), 'exposure': sorted(exposure),
            'not_before_epoch': epoch, 'authority': 'supplied_source_not_certified'})
        self._index_record(artifact['id'], record)
        self._event(actor['name'], 'research_recorded', artifact_id=artifact['id'], kind=kind)
        return {'id': artifact['id']}

    def _record_research(self, actor, lease, kind, content, scope, source_refs,
                         relations=None):
        job = self._owned(actor, lease)
        context = self._context(job['spec']['context_id'])
        record = self._make_record(kind, content, scope, relations, None)
        if kind not in WRITERS.get(actor['role'], set()):
            raise Denied('Record kind unavailable to this role')
        strings(source_refs, 'source_refs')
        references = set(source_refs)
        for targets in record['relations'].values():
            references.update(targets)
        if not references <= self._attempt_sources(actor, job, context):
            raise Denied('References must belong to the frozen context')
        result = self._worker_artifact(actor, job, context, record, sorted(references))
        self._index_record(result['id'], record)
        self._event(actor['name'], 'research_recorded', artifact_id=result['id'], kind=kind,
                    job_id=job['id'], generation=job['generation'])
        return result

    def _record_context_check(self, artifact, research_time, epoch):
        if artifact.get('not_before_epoch', 0) > epoch:
            raise Denied('Record unavailable for this epoch')
        if self._artifact_availability(artifact) > research_time:
            raise Denied('Record or known ancestry unavailable at the frozen research time')

    def _artifact_availability(self, artifact):
        """Inherit known record availability through wrappers; unknown source history stays unverified."""
        latest, pending, seen = 0, [artifact], set()
        scheduled = {artifact['id']}
        while pending:
            current = pending.pop()
            if current['id'] in seen:
                continue
            seen.add(current['id'])
            body = current['body']
            if type(body) is dict and body.get('schema') == SCHEMA:
                validate_record(body)
                latest = max(latest, body['available_at'])
            elif type(body) is dict and body.get('schema') == 'formalization-record/1':
                # Runtime import avoids a module-level cycle with the draft validator.
                from .formalization import utc
                latest = max(latest, int(utc(body.get('created_at')).timestamp()))
            elif type(body) is dict and body.get('schema') == 'implementation-certificate/1':
                latest = max(latest, integer(body.get('created_at'), 'certificate creation time'))
            elif type(body) is dict and body.get('schema') in ('blob-source/1', 'reference-source-package/1', 'data-snapshot/1',
                    'feature-source-package/1', 'feature-definitions/1', 'feature-certificate/1',
                    'compiled-hypothesis/1', 'reference-execution/1', 'binding-source-package/1', 'evaluation-plan/1',
                    'evaluation-plan-input/1','semantic-review-record/1','semantic-review-assessment/1','provider-invocation/1','provider-invocation-input/1',
                    'bootstrap-input/1','development-bootstrap/1',
                    'information-diagnostics-input/1','development-information-diagnostics/1',
                    'population-world-input/1','development-population-world/1',
                    'information-study-input/1','development-information-study-attempt/1',
                    'evaluator-calibration-input/1','evaluator-calibration-attempt/1',
                    'development-measurement-input/1','development-measurement/1'):
                latest = max(latest, integer(body.get('created_at'), 'retained source creation time'))
            for identity in current['exposure']:
                if identity not in scheduled:
                    scheduled.add(identity)
                    if self._db.execute('SELECT 1 FROM artifacts WHERE id=?', (identity,)).fetchone():
                        pending.append(self._artifact(identity))
        return latest

    def _journal_attempt(self, job, state, details):
        """Record actual host transitions; model-written attempts remain unverified."""
        context = self._context(job['spec']['context_id'])
        ancestry = self._attempt_sources({'name': job['owner']}, job, context)
        exposure = set(context['exposure']) | ancestry
        for identity in ancestry:
            exposure.update(self._artifact(identity)['exposure'])
        record = self._make_record('attempt', {
            'text': 'Controller observed attempt ' + state, 'outcome': state,
            'job_id': job['id'], 'generation': job['generation'], 'details': details},
            {'task_kind': job['spec']['kind']}, None, None)
        artifact = self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'job_id': job['id'], 'generation': job['generation'],
            'context_id': context['id'], 'data_class': 'work_product', 'body': record,
            'source_refs': sorted(ancestry), 'exposure': sorted(exposure),
            'authority': 'observed_operational_event'})
        self._index_record(artifact['id'], record)
        self._event('controller', 'research_recorded', artifact_id=artifact['id'], kind='attempt',
                    job_id=job['id'], generation=job['generation'])

    def _memory_item(self, identity):
        artifact = self._artifact(identity)
        return {'id': identity, 'record': artifact['body'], 'authority': artifact['authority'],
                'source_refs': artifact['source_refs'], 'exposure': artifact['exposure']}

    def _memory_results(self, allowed_ids, view, query, scope, kind, after, limit):
        if view not in VIEWS:
            raise Invalid('Unknown memory view')
        if type(query) is not str or len(query) > 8192:
            raise Invalid('Query must be bounded text')
        scope_object(scope)
        self._page(limit, after)
        if kind is not None and (type(kind) is not str or kind not in FIELDS):
            raise Invalid('Unknown record kind')
        candidates = self._db.execute('SELECT artifact_id,kind,view_name FROM research_records ORDER BY seq')
        matched = []
        for row in candidates:
            # No ranking, text matching, totals, or cursor positions from denied entries.
            if allowed_ids is not None and row['artifact_id'] not in allowed_ids:
                continue
            if view != 'journal' and row['view_name'] != view:
                continue
            if kind is not None and row['kind'] != kind:
                continue
            item = self._memory_item(row['artifact_id'])
            if any(item['record']['scope'].get(k) != v for k, v in scope.items()):
                continue
            if query.casefold() not in canonical(item['record']['content']).casefold():
                continue
            matched.append(item)
        page = matched[after:after + limit]
        return {'records': page, 'total': len(matched),
                'next_cursor': after + limit if after + limit < len(matched) else None,
                'retrieval_policy': 'metadata-text/1', 'scientific_authority': False}

    def _search_memory(self, actor, lease, view='journal', query='', scope=None,
                       kind=None, after=0, limit=20):
        job = self._owned(actor, lease)
        context = self._context(job['spec']['context_id'])
        scope = {} if scope is None else scope
        result = self._memory_results(self._attempt_sources(actor, job, context), view, query,
                                      scope, kind, after, limit)
        self._event(actor['name'], 'memory_retrieved', job_id=job['id'],
                    generation=job['generation'], context_id=context['id'], view=view,
                    query=query, scope=scope, kind=kind, after=after, limit=limit,
                    policy=result['retrieval_policy'], returned_ids=[r['id'] for r in result['records']],
                    bundle=result)
        return result

    def _inspect_memory(self, actor, view='journal', query='', scope=None,
                        kind=None, after=0, limit=20):
        return self._memory_results(None, view, query, {} if scope is None else scope, kind, after, limit)

    def _expected_memory(self):
        expected = []
        for row in self._db.execute('SELECT rowid,id,envelope FROM artifacts ORDER BY rowid'):
            body = decode(row['envelope'])['body']
            if type(body) is dict and body.get('schema') == SCHEMA:
                validate_record(body)
                expected.append((row['rowid'], row['id'], body['kind'], view_for(body['kind'])))
        return expected

    def _verify_memory(self):
        expected = self._expected_memory()
        actual = [tuple(row) for row in self._db.execute('SELECT * FROM research_records ORDER BY seq')]
        if actual != expected:
            raise Conflict('Research memory projection mismatch')
        return {'status': 'PASS', 'records': len(expected), 'version': 'research-memory/1',
                'scientific_authority': False}

    def _rebuild_memory(self, actor):
        # Verify immutable source hashes before replacing a disposable index.
        for row in self._db.execute('SELECT id FROM artifacts'):
            self._artifact(row['id'])
        expected = self._expected_memory()
        self._db.execute('DELETE FROM research_records')
        self._db.executemany('INSERT INTO research_records VALUES(?,?,?,?)', expected)
        self._event(actor['name'], 'memory_rebuilt', records=len(expected))
        return self._verify_memory()
