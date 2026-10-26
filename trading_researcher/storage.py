"""D078 immutable external blobs and verified database-plus-blob backup bundles."""
from contextlib import closing
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import tempfile

from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied


SHA = re.compile(r'[0-9a-f]{64}\Z')
MAX_BLOB_BYTES = 512 * 1024 * 1024
BLOCK = 1024 * 1024
RESERVED = ('dependency-revocation/', 'blob-source/', 'reference-source-package/', 'data-snapshot/',
            'feature-source-package/', 'feature-definitions/', 'feature-certificate/',
            'compiled-hypothesis/', 'reference-execution/', 'binding-source-package/', 'evaluation-plan/',
            'evaluation-plan-input/','semantic-review-record/','semantic-review-assessment/','provider-invocation/','provider-invocation-input/',
            'bootstrap-input/','development-bootstrap/',
            'information-diagnostics-input/','development-information-diagnostics/',
            'population-world-input/','development-population-world/',
            'information-study-input/','development-information-study-attempt/',
            'evaluator-calibration-input/','evaluator-calibration-attempt/',
            'development-measurement-input/','development-measurement/')


def blob_identity(value):
    if type(value) is not str or not SHA.fullmatch(value):
        raise Invalid('Expected a SHA-256 blob identity')
    return value


def _contained(root, path):
    root, path = Path(root).resolve(), Path(path)
    if not path.resolve().is_relative_to(root):
        raise Conflict('Storage path escapes its owned directory')
    for part in (path, *path.parents):
        if part == root:
            break
        if part.is_symlink() or (hasattr(part, 'is_junction') and part.is_junction()):
            raise Conflict('Linked storage paths are not accepted')
    return path


def _content_path(directory, identity):
    identity = blob_identity(identity)
    directory = Path(directory).resolve()
    return _contained(directory, directory / 'blobs' / identity[:2] / identity)


def _hash_file(path, *, collect=False, limit=MAX_BLOB_BYTES):
    checksum, size, chunks = hashlib.sha256(), 0, []
    with Path(path).open('rb') as stream:
        while chunk := stream.read(BLOCK):
            size += len(chunk)
            if limit is not None and size > limit:
                raise Invalid('Blob exceeds the 512 MiB resource envelope')
            checksum.update(chunk)
            if collect:
                chunks.append(chunk)
    return checksum.hexdigest(), size, b''.join(chunks) if collect else None


def _durable_file(path, raw):
    with Path(path).open('xb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def _owned_staging(parent, prefix):
    parent = Path(parent).resolve()
    path = Path(tempfile.mkdtemp(prefix=prefix, dir=parent)).resolve()
    if path.parent != parent or not path.name.startswith(prefix):
        raise Conflict('Invalid owned staging location')
    return path


def _remove_staging(path, parent, prefix):
    path, parent = Path(path).resolve(), Path(parent).resolve()
    if path.parent != parent or not path.name.startswith(prefix):
        raise Conflict('Refusing cleanup outside owned staging directory')
    if path.exists():
        shutil.rmtree(path)


def _validate_registry(path):
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok' or db.execute('PRAGMA foreign_key_check').fetchall():
            raise Conflict('Backup registry integrity failure')
        for name in ('artifacts', 'contexts', 'events', 'blobs', 'artifact_blobs', 'blob_meta'):
            row = db.execute('SELECT type FROM sqlite_master WHERE name=?', (name,)).fetchone()
            if row is None or row[0] != 'table':
                raise Conflict('Backup registry lacks an expected table')
        if db.execute('SELECT version FROM blob_meta WHERE singleton=1').fetchone() != (1,):
            raise Conflict('Unsupported blob registry version')
        artifacts = {}
        for table in ('artifacts', 'contexts'):
            for identity, raw in db.execute(f'SELECT id,envelope FROM {table}'):
                body = decode(raw)
                if digest(body) != identity:
                    raise Conflict('Backup immutable envelope hash mismatch')
                if table == 'artifacts':
                    artifacts[identity] = body
        previous = '0' * 64
        for before, raw, value in db.execute('SELECT previous_hash,envelope,hash FROM events ORDER BY seq'):
            if before != previous or hashlib.sha256((previous + raw).encode('utf-8')).hexdigest() != value:
                raise Conflict('Backup audit chain mismatch')
            previous = value
        blobs = {}
        for identity, size in db.execute('SELECT sha256,size FROM blobs ORDER BY sha256'):
            blob_identity(identity)
            integer(size, 'blob size')
            if size > MAX_BLOB_BYTES:
                raise Conflict('Backup blob exceeds the resource envelope')
            blobs[identity] = size
        links = {}
        for artifact_id, identity in db.execute('SELECT artifact_id,sha256 FROM artifact_blobs'):
            links.setdefault(artifact_id, set()).add(identity)
        for identity, envelope in artifacts.items():
            declared = strings(envelope.get('blob_refs', []), 'blob references')
            if set(declared) != links.get(identity, set()) or not set(declared) <= set(blobs):
                raise Conflict('Backup blob references do not match immutable artifacts')
        return blobs


def _validate_backup(directory):
    directory = Path(directory).resolve()
    manifest = decode(_contained(directory, directory / 'manifest.json').read_bytes())
    if (type(manifest) is not dict or set(manifest) != {'schema', 'registry_sha256', 'blobs', 'credentials_included'}
            or manifest['schema'] != 'runtime-backup/1' or manifest['credentials_included'] is not False
            or type(manifest['blobs']) is not dict):
        raise Invalid('Unsupported backup manifest')
    blob_identity(manifest['registry_sha256'])
    database = _contained(directory, directory / 'registry.sqlite3')
    if _hash_file(database, limit=None)[0] != manifest['registry_sha256']:
        raise Conflict('Backup database hash mismatch')
    expected = _validate_registry(database)
    if manifest['blobs'] != expected or any(type(size) is not int for size in manifest['blobs'].values()):
        raise Conflict('Backup manifest differs from committed database references')
    for identity, size in expected.items():
        try:
            actual, actual_size, _ = _hash_file(_content_path(directory, identity))
        except (OSError, Invalid) as exc:
            raise Conflict('Backup blob is unavailable') from exc
        if (actual, actual_size) != (identity, size):
            raise Conflict('Backup blob hash or size mismatch')
    return manifest


def restore_bundle(source, destination, operator_key_file):
    """Restore a trusted backup into a new location; credentials stay separately supplied."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise Conflict('Restore destination must be new')
    manifest = _validate_backup(source)
    key = Path(operator_key_file).read_text(encoding='utf-8').strip()
    with closing(sqlite3.connect((source / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
        row = db.execute("SELECT role FROM principals WHERE token_hash=?", (hashlib.sha256(key.encode()).hexdigest(),)).fetchone()
        if row != ('operator',):
            raise Denied('Restore requires a matching separately preserved operator credential')
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = _owned_staging(destination.parent, 'restore-pending-')
    try:
        shutil.copyfile(source / 'registry.sqlite3', stage / 'registry.sqlite3')
        for identity in manifest['blobs']:
            target = _content_path(stage, identity)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(_content_path(source, identity), target)
            with target.open('r+b') as stream:
                os.fsync(stream.fileno())
        with (stage / 'registry.sqlite3').open('r+b') as stream:
            os.fsync(stream.fileno())
        _durable_file(stage / 'manifest.json', canonical(manifest).encode())
        _validate_backup(stage)
        _durable_file(stage / 'operator.key', key.encode())
        os.chmod(stage / 'operator.key', 0o600)
        # Runtime integrity includes the replayed research-memory projection.
        from .coordination import Broker
        broker = Broker(stage)
        try:
            report = broker.call(broker.admin_token, 'verify')
            if report['status'] != 'PASS':
                raise Conflict('Restored runtime failed integrity validation')
        finally:
            broker.close()
        # The source manifest describes the imported backup before normal startup.
        (stage / 'manifest.json').rename(stage / 'restore-origin.json')
        if destination.exists():
            raise Conflict('Restore destination appeared during validation')
        stage.rename(destination)
    finally:
        _remove_staging(stage, destination.parent, 'restore-pending-')
    return {'status': 'PASS', 'directory': str(destination), 'blobs': len(manifest['blobs']),
            'projection_validation': 'PASS', 'credentials': 'separately supplied matching operator key'}


class ExternalStorage:
    def _initialize_storage(self, existing):
        found = self._db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='blob_meta'").fetchone()
        if found:
            row = self._db.execute('SELECT version FROM blob_meta WHERE singleton=1').fetchone()
            if row is None or row[0] != 1:
                raise Invalid('Unsupported blob registry schema')
            return
        if existing:
            self._preserve_schema_checkpoint('before-external-blobs-v1.sqlite3')
        with self._transaction():
            self._db.execute('CREATE TABLE blob_meta(singleton INTEGER PRIMARY KEY CHECK(singleton=1),version INTEGER NOT NULL)')
            self._db.execute('INSERT INTO blob_meta VALUES(1,1)')
            self._db.execute('CREATE TABLE blobs(sha256 TEXT PRIMARY KEY,size INTEGER NOT NULL,created_at INTEGER NOT NULL)')
            self._db.execute('''CREATE TABLE artifact_blobs(artifact_id TEXT NOT NULL REFERENCES artifacts(id),
                sha256 TEXT NOT NULL REFERENCES blobs(sha256),PRIMARY KEY(artifact_id,sha256))''')
            for table in ('blobs', 'artifact_blobs'):
                for action in ('UPDATE', 'DELETE'):
                    self._db.execute(f'''CREATE TRIGGER immutable_{table}_{action} BEFORE {action} ON {table}
                        BEGIN SELECT RAISE(ABORT,'immutable blob record'); END''')

    def _blob_path(self, identity):
        return _content_path(self.directory, identity)

    def _stage_blob_stream(self, source):
        staging = _contained(self.directory, self.directory / 'blob-staging')
        staging.mkdir(parents=True, exist_ok=True)
        descriptor, filename = tempfile.mkstemp(prefix='pending-', dir=staging)
        temporary = Path(filename)
        checksum, size = hashlib.sha256(), 0
        try:
            with os.fdopen(descriptor, 'wb') as target:
                while chunk := source.read(BLOCK):
                    size += len(chunk)
                    if size > MAX_BLOB_BYTES:
                        raise Invalid('Blob exceeds the 512 MiB resource envelope')
                    checksum.update(chunk)
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
            identity = checksum.hexdigest()
            final = self._blob_path(identity)
            final.parent.mkdir(parents=True, exist_ok=True)
            try:
                # Same-volume, atomic no-clobber publication. Existing bytes are never overwritten.
                os.link(temporary, final)
            except FileExistsError:
                pass
            actual, actual_size, _ = _hash_file(final)
            if (actual, actual_size) != (identity, size):
                raise Conflict('Conflicting bytes at an immutable blob identity; object quarantined')
            return {'sha256': identity, 'size': size}
        finally:
            temporary.unlink(missing_ok=True)

    def _stage_blob_bytes(self, raw):
        if type(raw) is not bytes:
            raise Invalid('Blob staging requires exact bytes')
        return self._stage_blob_stream(io.BytesIO(raw))

    def _register_blob(self, descriptor):
        if type(descriptor) is not dict or set(descriptor) != {'sha256', 'size'}:
            raise Invalid('Invalid staged blob descriptor')
        identity = blob_identity(descriptor['sha256'])
        size = integer(descriptor['size'], 'blob size')
        actual, actual_size, _ = _hash_file(self._blob_path(identity))
        if (identity, size) != (actual, actual_size):
            raise Conflict('Staged blob changed before reference commitment')
        row = self._db.execute('SELECT size FROM blobs WHERE sha256=?', (identity,)).fetchone()
        if row is not None and row[0] != size:
            raise Conflict('Committed blob size differs from staged content')
        self._db.execute('INSERT OR IGNORE INTO blobs VALUES(?,?,?)', (identity, size, self._now()))

    def _read_blob_bytes(self, identity):
        identity = blob_identity(identity)
        row = self._db.execute('SELECT size FROM blobs WHERE sha256=?', (identity,)).fetchone()
        if row is None:
            raise Denied('Blob is not committed')
        try:
            actual, size, raw = _hash_file(self._blob_path(identity), collect=True)
        except (OSError, Invalid) as exc:
            raise Conflict('Committed blob is unavailable; object quarantined') from exc
        if (actual, size) != (identity, row[0]):
            raise Conflict('Committed blob is corrupt; object quarantined')
        return raw

    def _verify_blobs(self):
        quarantined = []
        rows = self._db.execute('SELECT sha256,size FROM blobs ORDER BY sha256').fetchall()
        for row in rows:
            identity, size = row[0], row[1]
            try:
                actual, actual_size, _ = _hash_file(self._blob_path(identity))
                reason = None if (actual, actual_size) == (identity, size) else 'CORRUPT'
            except FileNotFoundError:
                reason = 'MISSING'
            except (OSError, Invalid, Conflict):
                reason = 'UNREADABLE'
            if reason:
                quarantined.append({'sha256': identity, 'reason': reason})
        links = {}
        for row in self._db.execute('SELECT artifact_id,sha256 FROM artifact_blobs'):
            links.setdefault(row[0], set()).add(row[1])
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            envelope = decode(row[1])
            if set(envelope.get('blob_refs', [])) != links.get(row[0], set()):
                raise Conflict('Immutable artifact and blob-reference index disagree')
        return {'status': 'QUARANTINED' if quarantined else 'PASS', 'committed': len(rows),
                'quarantined': quarantined, 'orphan_policy': 'uncommitted files confer no authority; no automatic deletion'}

    def _add_blob_source_external(self, token, args):
        with self._mutex:
            actor = self._principal(token)
            if actor['role'] != 'operator':
                raise Denied('File import is owned by the host')
        if set(args) != {'path', 'data_class', 'description'} or args['data_class'] not in ('development', 'assessment', 'operations'):
            raise Invalid('Blob source requires path, data_class and description')
        path = Path(text(args['path'], 'path')).resolve()
        description = text(args['description'], 'description')
        with path.open('rb') as source:
            before = os.fstat(source.fileno())
            descriptor = self._stage_blob_stream(source)
            after = os.fstat(source.fileno())
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise Conflict('Source changed during import; no registry authority granted')
        with self._transaction():
            actor = self._principal(token)
            if actor['role'] != 'operator':
                raise Denied('File import is owned by the host')
            self._register_blob(descriptor)
            body = {'schema': 'blob-source/1', 'created_at': self._now(), 'source_name': path.name,
                    'description': description, 'blob': descriptor}
            result = self._save_artifact({'version': 'local-artifact/1', 'creator': actor['name'],
                'origin': 'source', 'data_class': args['data_class'], 'body': body, 'source_refs': [],
                'exposure': [], 'blob_refs': [descriptor['sha256']], 'authority': 'supplied_source_not_certified'})
            self._event(actor['name'], 'blob_source_registered', artifact_id=result['id'])
            canonical(result)
            return result

    def _backup_bundle_external(self, token, args):
        with self._mutex:
            actor = self._principal(token)
            if actor['role'] != 'operator':
                raise Denied('Backup is owned by the host')
        if set(args) != {'destination'}:
            raise Invalid('Backup bundle requires a destination')
        destination = Path(text(args['destination'], 'destination')).resolve()
        if destination.exists():
            raise Conflict('Backup destination must be new')
        destination.parent.mkdir(parents=True, exist_ok=True)
        stage = _owned_staging(destination.parent, 'backup-pending-')
        try:
            with closing(sqlite3.connect((self.directory / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as source:
                with closing(sqlite3.connect(stage / 'registry.sqlite3')) as target:
                    source.backup(target)
            blobs = _validate_registry(stage / 'registry.sqlite3')
            for identity, size in blobs.items():
                target = _content_path(stage, identity)
                target.parent.mkdir(parents=True, exist_ok=True)
                try:
                    shutil.copyfile(self._blob_path(identity), target)
                    actual, actual_size, _ = _hash_file(target)
                except (OSError, Invalid) as exc:
                    raise Conflict('Cannot back up an unavailable committed blob') from exc
                if (actual, actual_size) != (identity, size):
                    raise Conflict('Copied backup blob differs from committed identity')
                with target.open('r+b') as stream:
                    os.fsync(stream.fileno())
            with (stage / 'registry.sqlite3').open('r+b') as stream:
                os.fsync(stream.fileno())
            manifest = {'schema': 'runtime-backup/1', 'registry_sha256': _hash_file(stage / 'registry.sqlite3', limit=None)[0],
                        'blobs': blobs, 'credentials_included': False}
            _durable_file(stage / 'manifest.json', canonical(manifest).encode())
            _validate_backup(stage)
            if destination.exists():
                raise Conflict('Backup destination appeared during validation')
            stage.rename(destination)
        finally:
            _remove_staging(stage, destination.parent, 'backup-pending-')
        return {'status': 'PASS', 'directory': str(destination), 'blobs': len(blobs), 'credentials_included': False}
