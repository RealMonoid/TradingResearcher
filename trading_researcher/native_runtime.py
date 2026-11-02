"""Retained native inputs and derived caches; neither execution nor certification.

The trusted host owns these operations. A future reserved computation must meter
materialization, bind its environment and check this tree again after use. This
module deliberately imports no external package and starts no native code.
"""
import hashlib
import io
import os
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile
import zlib

from .binding import require
from .certification import _runtime_identity
from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .storage import (BLOCK, MAX_BLOB_BYTES, _contained, _hash_file,
                      _owned_staging, _remove_staging, blob_identity)


SCHEMA = 'native-runtime-package/1'
MANIFEST = 'native-runtime-files/1'
AUTHORITY = 'retained_native_runtime_not_certified'
MAX_FILES = 4096
PENDING = 'runtime-pending-'
SAFE = re.compile(r'[A-Za-z0-9_./+@-]{1,512}\Z')
RESERVED = {'CON', 'PRN', 'AUX', 'NUL',
            *(f'COM{number}' for number in range(1, 10)),
            *(f'LPT{number}' for number in range(1, 10))}


def _path(name):
    require(type(name) is str and SAFE.fullmatch(name), 'Unsafe runtime path')
    path = PurePosixPath(name)
    require(bool(path.parts) and not path.is_absolute() and path.as_posix() == name,
            'Runtime path must be relative and canonical')
    require(all(part not in ('.', '..') and not part.endswith('.')
                and part.split('.')[0].upper() not in RESERVED
                for part in path.parts), 'Unsafe runtime path component')
    return path


def _manifest(manifest):
    require(type(manifest) is dict and set(manifest) ==
            {'schema', 'runtime_identity', 'dependencies', 'files'}
            and manifest['schema'] == MANIFEST, 'Exact runtime manifest required')
    # This also detaches mutable inputs and applies the existing canonical size,
    # nesting and no-float/duplicate-key constraints. Old runtimes stay retained;
    # this current-use interface never substitutes a different Python runtime.
    manifest = decode(canonical(manifest))
    require(manifest['runtime_identity'] == _runtime_identity(),
            'Native package Python runtime differs')
    files = manifest['files']
    require(type(files) is dict and 1 <= len(files) <= MAX_FILES,
            'Runtime file inventory exceeds its envelope')
    aliases = set()
    unpacked = 0
    for name, descriptor in files.items():
        _path(name)
        require(name.casefold() not in aliases, 'Runtime paths alias by case')
        aliases.add(name.casefold())
        require(type(descriptor) is dict and set(descriptor) == {'sha256', 'size'},
                'Exact runtime file descriptor required')
        blob_identity(descriptor['sha256'])
        unpacked += integer(descriptor['size'], 'Runtime file size')
        require(unpacked <= MAX_BLOB_BYTES, 'Unpacked runtime exceeds 512 MiB')
    for name in files:
        require(not any(parent.as_posix().casefold() in aliases
                        for parent in _path(name).parents if parent.as_posix() != '.'),
                'Runtime file collides with a parent directory')
    spellings = {}
    for name in files:
        path = _path(name)
        for part in (path, *path.parents):
            spelling = part.as_posix()
            previous = spellings.setdefault(spelling.casefold(), spelling)
            require(previous == spelling, 'Runtime parent directories alias by case')
    dependencies = manifest['dependencies']
    require(type(dependencies) is dict and 1 <= len(dependencies) <= 32,
            'Explicit bounded dependency versions required')
    for name, dependency in dependencies.items():
        require(type(name) is str and re.fullmatch(r'[A-Za-z0-9_.-]{1,128}', name),
                'Invalid runtime dependency name')
        require(type(dependency) is dict and set(dependency) ==
                {'version', 'distribution_sha256', 'license_files'},
                'Exact dependency provenance required')
        text(dependency['version'], 'Dependency version')
        blob_identity(dependency['distribution_sha256'])
        for license_file in strings(dependency['license_files'], 'Retained license files'):
            require(license_file in files, 'Declared license file is absent')
    return manifest


def _entries(archive, files):
    entries = archive.infolist()
    require(len(entries) == len(files), 'Runtime archive inventory differs')
    names = set()
    for entry in entries:
        name = entry.filename
        require(entry.orig_filename == name, 'Runtime member name was normalized')
        _path(name)
        require(name not in names and name in files, 'Duplicate or undeclared runtime member')
        names.add(name)
        kind = stat.S_IFMT(entry.external_attr >> 16)
        require(not entry.is_dir() and kind in (0, stat.S_IFREG)
                and not entry.external_attr & 0x10 and not entry.flag_bits & 1,
                'Only unencrypted regular runtime files are permitted')
        require(entry.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                'Unsupported runtime archive compression')
        require(entry.file_size == files[name]['size'], 'Runtime member size differs')
    require(names == set(files), 'Missing runtime member')
    return entries


def _blocks(stream, expected_size):
    size = 0
    while chunk := stream.read(BLOCK):
        size += len(chunk)
        require(size <= expected_size, 'Runtime member exceeds its declared size')
        yield chunk
    require(size == expected_size, 'Runtime member was truncated')


def validate_archive(raw, manifest):
    """Validate exact compressed bytes, detached metadata and every decoded file."""
    require(type(raw) is bytes and len(raw) <= MAX_BLOB_BYTES, 'Bounded exact archive bytes required')
    manifest = _manifest(manifest)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for entry in _entries(archive, manifest['files']):
                expected = manifest['files'][entry.filename]
                checksum = hashlib.sha256()
                with archive.open(entry) as source:
                    for chunk in _blocks(source, expected['size']):
                        checksum.update(chunk)
                require(checksum.hexdigest() == expected['sha256'], 'Runtime member hash differs')
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError, EOFError, zlib.error) as exc:
        raise Invalid('Unreadable runtime archive') from exc


def _descriptor(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def _identity(raw, manifest):
    return digest({'archive': _descriptor(raw), 'manifest': manifest})


def verify_tree(directory, manifest):
    """Recheck a complete derived tree; corruption is never repaired in place."""
    directory = Path(directory)
    _contained(directory.parent, directory)
    if not directory.is_dir():
        raise Conflict('Runtime cache is not a complete directory')
    expected = manifest['files']
    parents = {parent.as_posix() for name in expected for parent in PurePosixPath(name).parents
               if parent.as_posix() != '.'}
    observed = set()
    for base, directories, filenames in os.walk(directory, followlinks=False):
        for name in directories:
            path = _contained(directory, Path(base) / name)
            if path.relative_to(directory).as_posix() not in parents:
                raise Conflict('Unexpected runtime cache directory')
        for name in filenames:
            path = _contained(directory, Path(base) / name)
            relative = path.relative_to(directory).as_posix()
            value = path.lstat()
            if (relative not in expected or not stat.S_ISREG(value.st_mode)
                    or value.st_nlink != 1):
                raise Conflict('Unexpected runtime cache file')
            checksum, size, _ = _hash_file(path)
            if {'sha256': checksum, 'size': size} != expected[relative]:
                raise Conflict('Runtime cache file differs from retained input')
            observed.add(relative)
    if observed != set(expected):
        raise Conflict('Runtime cache is incomplete')


def materialize(raw, manifest, cache_root, on_bytes=None):
    """Atomically publish a verified derived tree and charge new/partial writes.

    The caller owns reservations and durable attempt accounting. This function
    never evicts or overwrites a published cache or unrelated interrupted stage.
    """
    manifest = _manifest(manifest)
    validate_archive(raw, manifest)
    require(on_bytes is None or callable(on_bytes), 'Materialization meter must be callable')
    cache_root = Path(cache_root).absolute()
    _contained(cache_root.parent, cache_root)
    cache_root.mkdir(parents=True, exist_ok=True)
    directory = _contained(cache_root, cache_root / _identity(raw, manifest))
    if directory.exists():
        verify_tree(directory, manifest)
        return directory
    stage = _owned_staging(cache_root, PENDING)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for entry in _entries(archive, manifest['files']):
                path = _contained(stage, stage / entry.filename)
                path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with archive.open(entry) as source, path.open('xb') as target:
                        for chunk in _blocks(source, entry.file_size):
                            written = target.write(chunk)
                            require(written == len(chunk), 'Incomplete runtime cache write')
                        target.flush()
                        os.fsync(target.fileno())
                finally:
                    # Count even a write that raises after storing a prefix.
                    if on_bytes is not None and path.exists():
                        on_bytes(path.stat().st_size)
        verify_tree(stage, manifest)
        try:
            stage.rename(directory)
        except OSError:
            if not directory.exists():
                raise
            # A concurrent exact publication may win. Never replace its files.
            verify_tree(directory, manifest)
        verify_tree(directory, manifest)
        return directory
    finally:
        _remove_staging(stage, cache_root, PENDING)


class NativeRuntimes:
    """Small adapter over the existing single-writer registry and blob owners."""
    def __init__(self, broker):
        self.broker = broker

    def _archive_source(self, identity):
        source = self.broker._artifact(text(identity, 'Runtime archive source'))
        body = source.get('body')
        if (source['creator'] != 'operator' or source['origin'] != 'source'
                or source['data_class'] != 'operations' or type(body) is not dict
                or body.get('schema') != 'blob-source/1'
                or source['authority'] != 'supplied_source_not_certified'):
            raise Denied('A genuine operator-imported operations archive is required')
        require(source['blob_refs'] == [body['blob']['sha256']], 'Runtime archive reference differs')
        return source

    def _package(self, identity):
        item = self.broker._artifact(text(identity, 'Native runtime identity'))
        body = item.get('body')
        if (item['creator'] != item['origin'] or item['creator'] != 'controller'
                or item['data_class'] != 'operations' or item['authority'] != AUTHORITY
                or type(body) is not dict or body.get('schema') != SCHEMA):
            raise Denied('Owned retained native runtime required')
        require(body['scientific_readiness'] is False
                and body['manifest'] == body['request']['manifest'], 'Runtime metadata differs')
        source = self._archive_source(body['request']['archive_id'])
        require(item['source_refs'] == [source['id']] and source['id'] in item['exposure']
                and set(source['exposure']) <= set(item['exposure'])
                and item['blob_refs'] == source['blob_refs']
                and body['archive'] == source['body']['blob']
                and body['footprint'] == {'runtime_archive': body['archive']['sha256'],
                                         'runtime_manifest': digest(body['manifest'])},
                'Runtime retained input closure differs')
        return item

    def _raw(self, item):
        raw = self.broker._read_blob_bytes(item['body']['archive']['sha256'])
        require(_descriptor(raw) == item['body']['archive'], 'Runtime archive descriptor differs')
        validate_archive(raw, item['body']['manifest'])
        return raw

    def retain(self, token, args):
        broker = self.broker
        with broker._transaction():
            actor = broker._binding_owner(token)
            require(set(args) == {'key', 'archive_id', 'manifest'}, 'Exact runtime retention request required')
            request = decode(canonical(args))
            text(request['key'], 'Runtime retention key')
            for row in broker._db.execute("SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?", (SCHEMA,)):
                prior = self._package(row[0])
                if prior['body']['request']['key'] == request['key']:
                    if prior['body']['request'] != request:
                        raise Conflict('Runtime key already binds different inputs')
                    return prior
            source = self._archive_source(request['archive_id'])
            raw = broker._read_blob_bytes(source['body']['blob']['sha256'])
            require(_descriptor(raw) == source['body']['blob'], 'Supplied runtime descriptor differs')
            validate_archive(raw, request['manifest'])
            body = {'schema': SCHEMA, 'created_at': broker._now(), 'request': request,
                    'manifest': request['manifest'], 'archive': _descriptor(raw),
                    'footprint': {'runtime_archive': hashlib.sha256(raw).hexdigest(),
                                  'runtime_manifest': digest(request['manifest'])},
                    'scientific_readiness': False}
            item = broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'operations', 'source_refs': [source['id']],
                'exposure': sorted(set(source['exposure']) | {source['id']}),
                'blob_refs': source['blob_refs'], 'authority': AUTHORITY, 'body': body})
            broker._event(actor['name'], 'native_runtime_retained', artifact_id=item['id'],
                          archive_id=source['id'], request_hash=digest(request))
            canonical(item)
            return item

    def inspect(self, token, args):
        with self.broker._mutex:
            self.broker._binding_owner(token)
            require(set(args) == {'runtime_id'}, 'Exact runtime inspection required')
            item = self._package(args['runtime_id'])
            self._raw(item)
            return item

    def _materialize(self, identity, meter):
        with self.broker._mutex:
            item = self._package(identity)
            self.broker._require_usable_dependencies(item['id'])
            raw = self._raw(item)
            integer(meter['materialized_bytes'], 'Materialized byte meter')
            def charge(size):
                meter['materialized_bytes'] += size
            meter['accounting_complete'] = False
            directory = materialize(raw, item['body']['manifest'],
                                    self.broker.directory / 'native-runtime-cache', charge)
            meter['accounting_complete'] = True
            return directory
