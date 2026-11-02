"""Independent synthetic archive/cache qualification; no native execution.

Every archive is invented here and contains data/notices, not NumPy, executable
code, market observations, or a scientific certificate. Derived caches confer
no authority. All registries and fault-injection writes use temporary paths.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
import warnings
import zipfile

from trading_researcher import native_runtime as runtime
from trading_researcher.certification import _runtime_identity
from trading_researcher.codec import canonical, digest
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.revocations import version_selector
from trading_researcher.server import Client, LocalServer, RemoteError
from trading_researcher.storage import restore_bundle


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'native-runtime-package/1'
AUTHORITY = 'retained_native_runtime_not_certified'
IDENTITY = _runtime_identity()
MEMBERS = {'example/LICENSE.txt': b'Fictional independent fixture notice.\n',
           'example/data.bin': b'\x00\x01\xffdata',
           'example/notes.txt': b'Fixed synthetic resource fixture.\n'}
REJECTED = (Invalid, Conflict, Denied)


def archive(entries=None, modes=None):
    entries = list(MEMBERS.items()) if entries is None else list(entries)
    output = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as target:
            for name, raw in entries:
                info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = ((modes or {}).get(name, stat.S_IFREG | 0o600)) << 16
                target.writestr(info, raw)
    return output.getvalue()


def manifest(members=None):
    members = MEMBERS if members is None else members
    return {'schema': 'native-runtime-files/1', 'runtime_identity': deepcopy(IDENTITY),
            'dependencies': {'fictional-fixture': {
                'version': '1.0',
                'distribution_sha256': hashlib.sha256(b'fictional distribution identity').hexdigest(),
                'license_files': ['example/LICENSE.txt']}},
            'files': {name: {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
                      for name, raw in members.items()}}


def cache_identity(raw, spec):
    return digest({'archive': {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)},
                   'manifest': spec})


def snapshot(directory):
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob('*') if path.is_file()}


class NativeArchiveIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.raw, self.spec = archive(), manifest()

    def reject(self, raw=None, spec=None):
        with self.assertRaises(REJECTED):
            runtime.validate_archive(self.raw if raw is None else raw,
                                     self.spec if spec is None else spec)

    def test_exact_manifest_and_bytes_validate_without_mutation_or_authority(self):
        original = deepcopy(self.spec)
        self.assertIsNone(runtime.validate_archive(self.raw, self.spec))
        self.assertEqual(self.spec, original)
        self.assertNotIn('scientific_readiness', self.spec)
        self.assertNotIn('certified', self.spec)

    def test_manifest_exact_shape_types_identity_hashes_and_license_references(self):
        variants = []
        changed = deepcopy(self.spec); changed['extra'] = True; variants.append(changed)
        changed = deepcopy(self.spec); changed['schema'] = 'native-runtime-files/2'; variants.append(changed)
        changed = deepcopy(self.spec); changed['runtime_identity']['executable_sha256'] = '0' * 64; variants.append(changed)
        changed = deepcopy(self.spec); changed['files'] = {}; variants.append(changed)
        for change in ({'size': True}, {'size': -1}, {'size': 512 * 1024**2 + 1},
                       {'sha256': 'A' * 64}, {'sha256': 'not-a-digest'}, {'extra': 0}):
            changed = deepcopy(self.spec)
            changed['files']['example/data.bin'].update(change)
            variants.append(changed)
        for change in ({'version': ''}, {'version': False}, {'distribution_sha256': 'A' * 64},
                       {'license_files': ['missing/LICENSE.txt']}, {'extra': True}):
            changed = deepcopy(self.spec)
            changed['dependencies']['fictional-fixture'].update(change)
            variants.append(changed)
        changed = deepcopy(self.spec)
        changed['dependencies']['fictional-fixture']['version'] = 'x' * (1024**2)
        variants.append(changed)
        for index, changed in enumerate(variants):
            with self.subTest(case=index):
                self.reject(spec=changed)
        for wrong in (bytearray(self.raw), memoryview(self.raw), 'not exact bytes'):
            with self.subTest(raw_type=type(wrong).__name__):
                self.reject(raw=wrong)

    def test_file_inventory_boundary_is_4096_without_old_128_package_limit(self):
        members = {'example/LICENSE.txt': MEMBERS['example/LICENSE.txt']}
        members.update({f'example/item-{index:04d}.bin': b'' for index in range(4095)})
        self.assertEqual(len(members), 4096)
        self.assertIsNone(runtime.validate_archive(archive(members.items()), manifest(members)))
        members['example/one-too-many.bin'] = b''
        self.reject(archive(members.items()), manifest(members))

    def test_member_names_are_canonical_contained_and_windows_safe(self):
        names = ('../escape', '/absolute', 'C:/absolute', 'example\\backslash',
                 'example/a:b', 'example//double', 'example/./dot', 'example/../up',
                 '.', '..', 'example/trailing/', 'example/trailing.', 'example/trailing ',
                 'example/NUL', 'example/con.txt', 'example/COM1.log', 'example/Lpt9')
        for name in names:
            with self.subTest(name=name):
                members = {**MEMBERS, name: b'bad path'}
                self.reject(archive(members.items()), manifest(members))
        for names in (('example/data.bin', 'example/DATA.bin'),
                      ('example/parent', 'example/parent/child.bin')):
            with self.subTest(colliding=names):
                members = {**MEMBERS, **dict.fromkeys(names, b'collision')}
                self.reject(archive(members.items()), manifest(members))

    def test_duplicate_missing_extra_hash_size_and_invalid_zip_reject(self):
        self.reject(raw=b'not a zip archive')
        self.reject(raw=self.raw[:30])
        self.reject(raw=archive([*MEMBERS.items(), ('example/data.bin', b'duplicate')]))
        self.reject(raw=archive([(name, raw) for name, raw in MEMBERS.items()
                                 if name != 'example/data.bin']))
        self.reject(raw=archive([*MEMBERS.items(), ('example/undeclared.bin', b'extra')]))
        changed = deepcopy(self.spec); changed['files']['example/data.bin']['size'] += 1
        self.reject(spec=changed)
        changed = deepcopy(self.spec); changed['files']['example/data.bin']['sha256'] = '0' * 64
        self.reject(spec=changed)

    def test_parent_directory_case_alias_is_rejected_before_materialization(self):
        members = {**MEMBERS, 'Example/one.bin': b'one', 'example/two.bin': b'two'}
        raw, spec = archive(members.items()), manifest(members)
        with self.subTest(phase='validation'):
            self.reject(raw, spec)
        with self.subTest(phase='materialization'):
            cache = self.root / 'case-alias-must-not-be-created'
            charges = []
            with self.assertRaises(REJECTED):
                runtime.materialize(raw, spec, cache, on_bytes=charges.append)
            self.assertFalse(cache.exists())
            self.assertEqual(charges, [])

    def test_reserved_deflate_block_type_is_a_normalized_archive_rejection(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as target:
            for name, raw in MEMBERS.items():
                info = zipfile.ZipInfo(name, date_time=(2000, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o600) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                target.writestr(info, raw)
        raw = bytearray(output.getvalue())
        self.assertEqual(raw[:4], b'PK\x03\x04')
        name_length, extra_length = struct.unpack_from('<HH', raw, 26)
        payload = 30 + name_length + extra_length
        # RFC1951 BTYPE=11 is reserved. Preserve the rest of this fixed tiny ZIP
        # so its actual raw decoder error, not a bad ZIP header, is exercised.
        raw[payload] = (raw[payload] & 0xf8) | 0x07
        with self.assertRaises((Invalid, Conflict)):
            runtime.validate_archive(bytes(raw), self.spec)

    def test_embedded_nul_in_matching_local_and_central_names_is_not_normalized(self):
        declared = 'example/data.bin'
        original_name = declared + 'Xhidden'
        nul_name = declared + '\x00hidden'
        entries = [(original_name if name == declared else name, raw)
                   for name, raw in MEMBERS.items()]
        raw = archive(entries)
        self.assertEqual(raw.count(original_name.encode()), 2)
        raw = raw.replace(original_name.encode(), nul_name.encode())
        # Both local/central names now agree byte for byte, but ZipInfo exposes
        # the shorter filename alongside the untrimmed orig_filename.
        with zipfile.ZipFile(io.BytesIO(raw)) as source:
            entry = source.getinfo(declared)
            self.assertEqual(entry.filename, declared)
            self.assertEqual(entry.orig_filename, nul_name)
        self.reject(raw=raw)

    def test_symlink_directory_nonregular_and_encrypted_zip_members_reject(self):
        name = 'example/data.bin'
        for mode in (stat.S_IFLNK | 0o777, stat.S_IFDIR | 0o700, stat.S_IFIFO | 0o600):
            with self.subTest(mode=mode):
                self.reject(raw=archive(modes={name: mode}))
        self.reject(raw=archive([*MEMBERS.items(), ('example/', b'')],
                                modes={'example/': stat.S_IFDIR | 0o700}))
        encrypted = bytearray(self.raw)
        # Mark the first local and central headers encrypted, without relying
        # on a third-party encryption writer or manufacturing encrypted data.
        for signature, flag_offset in ((b'PK\x03\x04', 6), (b'PK\x01\x02', 8)):
            offset = encrypted.index(signature) + flag_offset
            struct.pack_into('<H', encrypted, offset,
                             struct.unpack_from('<H', encrypted, offset)[0] | 1)
        self.reject(raw=bytes(encrypted))

    def test_validation_finishes_before_any_cache_write(self):
        changed = deepcopy(self.spec)
        changed['files']['example/data.bin']['sha256'] = '0' * 64
        cache = self.root / 'never-created'
        charges = []
        with self.assertRaises(REJECTED):
            runtime.materialize(self.raw, changed, cache, on_bytes=charges.append)
        self.assertFalse(cache.exists())
        self.assertEqual(charges, [])

    def test_atomic_full_tree_exact_reuse_metering_and_orphan_preservation(self):
        cache = self.root / 'cache'; cache.mkdir()
        orphan = cache / 'runtime-pending-unrelated'; orphan.mkdir()
        (orphan / 'keep.bin').write_bytes(b'unrelated interrupted materialization')
        before = snapshot(orphan)
        expected = cache / cache_identity(self.raw, self.spec)
        charges = []

        def charge(size):
            self.assertIs(type(size), int)
            self.assertGreaterEqual(size, 0)
            self.assertFalse(expected.exists(), 'A partial tree became visible')
            charges.append(size)

        path = runtime.materialize(self.raw, self.spec, cache, on_bytes=charge)
        self.assertEqual(path, expected)
        self.assertEqual(snapshot(path), MEMBERS)
        self.assertEqual(sum(charges), sum(map(len, MEMBERS.values())))
        self.assertEqual(snapshot(orphan), before)
        hits = []
        self.assertEqual(runtime.materialize(self.raw, self.spec, cache, on_bytes=hits.append), path)
        self.assertEqual(sum(hits), 0)
        self.assertEqual(snapshot(path), MEMBERS)
        self.assertEqual(snapshot(orphan), before)
        self.assertEqual(sorted(p.name for p in cache.iterdir()), sorted([path.name, orphan.name]))

    def test_corrupt_partial_extra_or_non_directory_published_cache_never_overwrites(self):
        for kind in ('corrupt', 'missing', 'extra', 'extra-directory', 'directory-member', 'root-file'):
            with self.subTest(kind=kind):
                cache = self.root / kind
                path = runtime.materialize(self.raw, self.spec, cache)
                member = path / 'example/data.bin'
                if kind == 'corrupt': member.write_bytes(b'corrupt retained cache bytes')
                elif kind == 'missing': member.unlink()
                elif kind == 'extra': (path / 'unexpected.bin').write_bytes(b'extra')
                elif kind == 'extra-directory': (path / 'unexpected-directory').mkdir()
                elif kind == 'directory-member': member.unlink(); member.mkdir()
                else: shutil.rmtree(path); path.write_bytes(b'occupied cache identity')
                before = path.read_bytes() if path.is_file() else snapshot(path)
                charges = []
                with self.assertRaises(Conflict):
                    runtime.materialize(self.raw, self.spec, cache, on_bytes=charges.append)
                self.assertEqual(sum(charges), 0)
                self.assertEqual(path.read_bytes() if path.is_file() else snapshot(path), before)

    def test_linked_cache_root_and_published_members_are_not_followed(self):
        outside = self.root / 'outside'; outside.mkdir()
        linked_root = self.root / 'linked-cache'
        try:
            linked_root.symlink_to(outside, target_is_directory=True)
        except OSError as error:
            self.skipTest('This host cannot create the required real symlink: ' + type(error).__name__)
        with self.assertRaises(Conflict):
            runtime.materialize(self.raw, self.spec, linked_root)
        self.assertEqual(list(outside.iterdir()), [])
        cache = self.root / 'normal-cache'
        path = runtime.materialize(self.raw, self.spec, cache)
        alias_cache = self.root / 'published-root-link'; alias_cache.mkdir()
        (alias_cache / path.name).symlink_to(path, target_is_directory=True)
        with self.assertRaises(Conflict):
            runtime.materialize(self.raw, self.spec, alias_cache)
        self.assertEqual(snapshot(path), MEMBERS)
        member = path / 'example/data.bin'; member.unlink()
        target = outside / 'preserve.bin'; target.write_bytes(MEMBERS['example/data.bin'])
        member.symlink_to(target)
        with self.assertRaises(Conflict):
            runtime.materialize(self.raw, self.spec, cache)
        self.assertEqual(target.read_bytes(), MEMBERS['example/data.bin'])

    @unittest.skipUnless(os.name == 'nt', 'Windows junction qualification')
    def test_real_windows_junction_roots_and_member_parent_never_touch_targets(self):
        def literal(path):
            path = path.absolute()
            self.assertTrue(path.is_relative_to(self.root.absolute()))
            return "'" + str(path).replace("'", "''") + "'"

        def remove_owned_junction(link):
            # RemoveDirectory removes this junction entry, never its target.
            # Keep cleanup in the explicitly owned temporary directory.
            self.assertTrue(link.absolute().is_relative_to(self.root.absolute()))
            if link.is_junction():
                link.rmdir()

        def junction(link, target):
            self.assertTrue(target.is_dir())
            command = ("$ErrorActionPreference = 'Stop'; "
                       'New-Item -ItemType Junction -Path ' + literal(link)
                       + ' -Target ' + literal(target) + ' | Out-Null')
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(link.is_junction(), 'A real Windows junction is required')
            self.addCleanup(remove_owned_junction, link)

        def reject_without_touching(cache, target):
            before = snapshot(target)
            charges = []
            with self.assertRaises(Conflict):
                runtime.materialize(self.raw, self.spec, cache, on_bytes=charges.append)
            self.assertEqual(charges, [])
            self.assertEqual(snapshot(target), before)

        # The cache root itself points at an unrelated owned target.
        target = self.root / 'junction-cache-target'; target.mkdir()
        (target / 'keep.bin').write_bytes(b'preserve root target')
        root_link = self.root / 'junction-cache-root'
        junction(root_link, target)
        reject_without_touching(root_link, target)

        # A published identity points at otherwise exact bytes. Matching hashes
        # do not authorize following the junction to a different tree.
        published_target = self.root / 'junction-published-target'
        for name, raw in MEMBERS.items():
            path = published_target / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        cache = self.root / 'junction-published-cache'; cache.mkdir()
        junction(cache / cache_identity(self.raw, self.spec), published_target)
        reject_without_touching(cache, published_target)

        # The cache root is ordinary, but an expected member-parent is linked.
        cache = self.root / 'junction-member-cache'
        published = runtime.materialize(self.raw, self.spec, cache)
        parent = published / 'example'
        self.assertTrue(parent.resolve().is_relative_to(self.root.resolve()))
        self.assertFalse(parent.is_junction())
        shutil.rmtree(parent)
        member_target = self.root / 'junction-member-target'; member_target.mkdir()
        for name, raw in MEMBERS.items():
            (member_target / Path(name).name).write_bytes(raw)
        junction(parent, member_target)
        reject_without_touching(cache, member_target)

    def test_callback_failure_keeps_charge_and_cleans_only_owned_staging(self):
        cache = self.root / 'callback-cache'; cache.mkdir()
        orphan = cache / 'runtime-pending-preserve'; orphan.mkdir()
        (orphan / 'keep').write_bytes(b'preserve')
        charges = []

        def fail(size):
            charges.append(size)
            raise RuntimeError('Independent accounting callback failure')

        with self.assertRaises(RuntimeError):
            runtime.materialize(self.raw, self.spec, cache, on_bytes=fail)
        self.assertGreater(sum(charges), 0)
        self.assertLessEqual(sum(charges), sum(map(len, MEMBERS.values())))
        self.assertEqual(list(cache.iterdir()), [orphan])
        self.assertEqual((orphan / 'keep').read_bytes(), b'preserve')

    def test_actual_partial_file_write_is_charged_before_cleanup(self):
        cache = self.root / 'partial-cache'
        original_open = Path.open
        charges = []
        actual_written = []

        class PartialWriter:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): return self
            def __exit__(self, *args): return self.stream.__exit__(*args)
            def __getattr__(self, name): return getattr(self.stream, name)
            def write(self, raw):
                count = self.stream.write(raw[:2])
                self.stream.flush()
                actual_written.append(count)
                raise OSError('Independent partial disk-write failure')

        def partial_open(path, mode='r', *args, **kwargs):
            stream = original_open(path, mode, *args, **kwargs)
            if ('w' in mode or 'x' in mode) and path.resolve().is_relative_to(cache.resolve()):
                return PartialWriter(stream)
            return stream

        with patch.object(Path, 'open', partial_open), self.assertRaises(OSError):
            runtime.materialize(self.raw, self.spec, cache, on_bytes=charges.append)
        self.assertEqual(sum(actual_written), 2)
        self.assertEqual(sum(charges), 2)
        self.assertFalse((cache / cache_identity(self.raw, self.spec)).exists())
        self.assertEqual(list(cache.iterdir()), [])

    def test_hard_crash_pending_tree_is_retained_and_ignored_on_next_materialization(self):
        input_file = self.root / 'archive.zip'; input_file.write_bytes(self.raw)
        spec_file = self.root / 'manifest.json'; spec_file.write_text(canonical(self.spec), encoding='utf-8')
        cache = self.root / 'crash-cache'
        code = ('import json,os,sys\nfrom pathlib import Path\n'
                'from trading_researcher.native_runtime import materialize\n'
                'materialize(Path(sys.argv[1]).read_bytes(),json.loads(Path(sys.argv[2]).read_text()),'
                'Path(sys.argv[3]),on_bytes=lambda size: os._exit(29))\n')
        result = subprocess.run([sys.executable, '-B', '-c', code, str(input_file), str(spec_file), str(cache)],
                                cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 29, result.stderr)
        pending = list(cache.glob('runtime-pending-*'))
        self.assertEqual(len(pending), 1)
        preserved = snapshot(pending[0])
        self.assertTrue(preserved)
        self.assertFalse((cache / cache_identity(self.raw, self.spec)).exists())
        charges = []
        path = runtime.materialize(self.raw, self.spec, cache, on_bytes=charges.append)
        self.assertEqual(snapshot(path), MEMBERS)
        self.assertEqual(sum(charges), sum(map(len, MEMBERS.values())))
        self.assertEqual(snapshot(pending[0]), preserved)


class NativeRegistryIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / 'registry'
        self.broker = Broker(self.directory)
        self.addCleanup(self.broker.close)
        self.token = self.broker.admin_token
        self.raw, self.spec = archive(), manifest()

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def source(self, raw=None, data_class='operations'):
        path = self.root / 'runtime-input.zip'; path.write_bytes(self.raw if raw is None else raw)
        return self.op('add_blob_source', path=str(path), data_class=data_class,
                       description='Fictional runtime fixture; supplied bytes, no certification')

    def retain(self, source=None, key='runtime', spec=None):
        source = self.source() if source is None else source
        return self.op('retain_native_runtime', key=key, archive_id=source['id'],
                       manifest=self.spec if spec is None else spec)

    def packages(self):
        return [self.broker._artifact(row[0]) for row in self.broker._db.execute(
            "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?", (SCHEMA,))]

    def test_owned_retention_detachment_exact_binding_and_immutable_artifact(self):
        source = self.source()
        self.assertEqual((source['creator'], source['origin'], source['data_class']),
                         ('operator', 'source', 'operations'))
        given = deepcopy(self.spec)
        saved = self.retain(source, spec=given)
        expected_request = {'key': 'runtime', 'archive_id': source['id'], 'manifest': self.spec}
        self.assertEqual((saved['creator'], saved['origin'], saved['data_class'], saved['authority']),
                         ('controller', 'controller', 'operations', AUTHORITY))
        self.assertEqual(saved['body']['schema'], SCHEMA)
        self.assertIs(saved['body']['scientific_readiness'], False)
        self.assertEqual(saved['body']['request'], expected_request)
        self.assertEqual(saved['body']['manifest'], self.spec)
        self.assertEqual(saved['body']['footprint'],
                         {'runtime_archive': hashlib.sha256(self.raw).hexdigest(),
                          'runtime_manifest': digest(self.spec)})
        self.assertEqual(saved['source_refs'], [source['id']])
        self.assertIn(source['id'], saved['exposure'])
        self.assertEqual(saved['blob_refs'], [hashlib.sha256(self.raw).hexdigest()])
        given['dependencies']['fictional-fixture']['version'] = 'mutated caller'
        saved['body']['manifest']['files'].clear()
        inspected = self.op('inspect_native_runtime', runtime_id=saved['id'])
        self.assertEqual(inspected['body']['request'], expected_request)
        self.assertEqual(inspected['body']['manifest'], self.spec)
        self.assertEqual(self.broker._technical_dependencies(inspected), [])
        with self.assertRaises(sqlite3.IntegrityError):
            self.broker._db.execute('UPDATE artifacts SET envelope=? WHERE id=?',
                                    (canonical({'forged': True}), inspected['id']))
        self.assertEqual(self.op('verify')['status'], 'PASS')

    def test_operator_http_and_worker_denials_use_real_transport(self):
        source = self.source()
        worker = self.op('register_worker', name='runtime-reader', role='discovery', capabilities=[])['token']
        server = LocalServer(self.broker)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            operator = Client(server.url, self.token)
            researcher = Client(server.url, worker)
            for operation, args in (
                ('retain_native_runtime', {'key': 'denied', 'archive_id': source['id'], 'manifest': self.spec}),
                ('inspect_native_runtime', {'runtime_id': '0' * 64})):
                with self.subTest(operation=operation), self.assertRaises(RemoteError) as rejected:
                    researcher.call(operation, **args)
                self.assertEqual(rejected.exception.status, 403)
            saved = operator.call('retain_native_runtime', key='http', archive_id=source['id'], manifest=self.spec)
            self.assertEqual(operator.call('inspect_native_runtime', runtime_id=saved['id']), saved)
            changed = deepcopy(self.spec); changed['dependencies']['fictional-fixture']['version'] = '2.0'
            with self.assertRaises(RemoteError) as rejected:
                operator.call('retain_native_runtime', key='http', archive_id=source['id'], manifest=changed)
            self.assertEqual(rejected.exception.status, 409)
        finally:
            server.shutdown(); thread.join(timeout=5); server.server_close()

    def test_worker_denied_before_artifact_or_blob_lookup(self):
        worker = self.op('register_worker', name='no-native-authority', role='discovery', capabilities=[])['token']
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Unauthorized artifact lookup')), \
                patch.object(self.broker, '_read_blob_bytes', side_effect=AssertionError('Unauthorized blob read')):
            for operation, args in (
                ('retain_native_runtime', {'key': 'denied', 'archive_id': '0' * 64, 'manifest': self.spec}),
                ('inspect_native_runtime', {'runtime_id': '0' * 64})):
                with self.subTest(operation=operation), self.assertRaises(Denied):
                    self.broker.call(worker, operation, **args)

    def test_owned_namespace_and_archive_origin_cannot_be_forged(self):
        with self.assertRaises(Invalid):
            self.op('add_source', data_class='operations',
                    body={'schema': SCHEMA, 'scientific_readiness': True})
        source = self.source(data_class='development')
        with self.assertRaises(Denied): self.retain(source)
        genuine = self.source()
        for creator, origin in (('controller', 'controller'), ('operator', 'controller')):
            with self.subTest(creator=creator, origin=origin):
                with self.broker._transaction():
                    fake = self.broker._save_artifact({
                        'version': 'local-artifact/1', 'creator': creator, 'origin': origin,
                        'data_class': 'operations', 'source_refs': [], 'exposure': [],
                        'blob_refs': genuine['blob_refs'], 'authority': genuine['authority'], 'body': genuine['body']})
                with self.assertRaises(Denied): self.retain(fake, key=creator + origin)
        self.assertEqual(self.packages(), [])

    def test_same_key_exact_idempotency_changed_request_conflict_and_concurrency(self):
        source = self.source()
        barrier = threading.Barrier(4)

        def deliver(_):
            barrier.wait(timeout=5)
            return self.retain(source)

        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(deliver, range(4)))
        self.assertTrue(all(result == results[0] for result in results))
        self.assertEqual(len(self.packages()), 1)
        changed = deepcopy(self.spec); changed['dependencies']['fictional-fixture']['version'] = '2.0'
        with self.assertRaises(Conflict): self.retain(source, spec=changed)
        self.assertEqual(len(self.packages()), 1)
        self.assertEqual(self.retain(source), results[0])

    def test_inspector_requires_owned_origin_and_retention_authority(self):
        saved = self.retain()
        for creator, origin, authority in (
            ('operator', 'source', AUTHORITY),
            ('controller', 'source', AUTHORITY),
            ('controller', 'controller', 'forged_runtime_claim')):
            with self.subTest(creator=creator, origin=origin, authority=authority):
                with self.broker._transaction():
                    forged = self.broker._save_artifact({
                        **{key: value for key, value in saved.items() if key != 'id'},
                        'creator': creator, 'origin': origin, 'authority': authority})
                with self.assertRaises(Denied):
                    self.op('inspect_native_runtime', runtime_id=forged['id'])

    def test_final_event_failure_rolls_back_retention_and_retry_is_complete(self):
        source = self.source()
        original_event = self.broker._event

        def fail(actor, action, **details):
            if action == 'native_runtime_retained':
                raise RuntimeError('Independent precommit event failure')
            return original_event(actor, action, **details)

        with patch.object(self.broker, '_event', side_effect=fail), self.assertRaises(RuntimeError):
            self.retain(source)
        self.assertEqual(self.packages(), [])
        self.assertEqual(self.op('verify')['status'], 'PASS')
        saved = self.retain(source)
        self.assertEqual(self.op('inspect_native_runtime', runtime_id=saved['id']), saved)
        self.assertEqual(len(self.packages()), 1)

    def test_corrupt_committed_archive_denies_inspection_and_materialization_without_charge(self):
        saved = self.retain()
        self.broker._blob_path(saved['blob_refs'][0]).write_bytes(b'corrupt immutable archive')
        with self.assertRaises(Conflict): self.op('inspect_native_runtime', runtime_id=saved['id'])
        meter = {'materialized_bytes': 0}
        with self.assertRaises(Conflict): runtime.NativeRuntimes(self.broker)._materialize(saved['id'], meter)
        self.assertEqual(meter, {'materialized_bytes': 0})

    def test_private_materializer_serializes_exact_cache_and_reports_only_new_bytes(self):
        saved = self.retain()
        barrier = threading.Barrier(3)

        def use(_):
            meter = {'materialized_bytes': 7}
            barrier.wait(timeout=5)
            path = runtime.NativeRuntimes(self.broker)._materialize(saved['id'], meter)
            return path, meter['materialized_bytes'] - 7

        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(use, range(3)))
        self.assertTrue(all(path == results[0][0] for path, _ in results))
        self.assertEqual(sorted(size for _, size in results), [0, 0, sum(map(len, MEMBERS.values()))])
        self.assertEqual(snapshot(results[0][0]), MEMBERS)

    def test_more_than_128_members_use_compact_existing_version_selector(self):
        members = {**MEMBERS, **{f'example/member-{index}.bin': b'' for index in range(130)}}
        raw = archive(members.items())
        saved = self.retain(self.source(raw), spec=manifest(members))
        self.assertEqual(len(saved['body']['manifest']['files']), 133)
        self.assertEqual(len(saved['body']['footprint']), 2)
        self.assertEqual(version_selector(saved),
                         {'schema': SCHEMA, 'footprint_sha256': digest(saved['body']['footprint'])})
        self.assertEqual(len(saved['blob_refs']), 1)

    def test_new_retain_key_cannot_bypass_revoked_exact_runtime_version(self):
        source = self.source()
        first = self.retain(source)
        evidence = self.op('add_source', data_class='operations', body={'synthetic_defect': 'fixture only'})
        self.op('revoke_dependency', key='runtime-defect', dependency_id=first['id'],
                reason='Independent synthetic technical defect', evidence_refs=[evidence['id']])
        meter = {'materialized_bytes': 0}
        with self.assertRaises(Denied): runtime.NativeRuntimes(self.broker)._materialize(first['id'], meter)
        self.assertEqual(meter['materialized_bytes'], 0)
        self.assertEqual(self.op('get_artifact', artifact_id=first['id']), first)
        # Retention may itself refuse a revoked version. If history is retained,
        # its new key must still resolve to the already revoked exact selector.
        try:
            alias = self.retain(source, key='new-key-same-runtime')
        except Denied:
            return
        self.assertEqual(version_selector(alias), version_selector(first))
        self.assertEqual(self.op('inspect_dependency_use', artifact_id=alias['id'])['status'],
                         'INVALIDATED_BY_DEPENDENCY')
        with self.assertRaises(Denied): runtime.NativeRuntimes(self.broker)._materialize(alias['id'], meter)
        self.assertEqual(meter['materialized_bytes'], 0)

    def test_cache_free_backup_restore_reconstructs_only_verified_retained_bytes(self):
        saved = self.retain()
        first_meter = {'materialized_bytes': 0}
        old_cache = runtime.NativeRuntimes(self.broker)._materialize(saved['id'], first_meter)
        self.assertEqual(first_meter['materialized_bytes'], sum(map(len, MEMBERS.values())))
        backup = self.root / 'backup'
        self.assertEqual(self.op('backup_bundle', destination=str(backup))['status'], 'PASS')
        self.assertFalse(any(path.is_dir() and path.name == old_cache.name for path in backup.rglob('*')))
        shutil.rmtree(old_cache)
        restored = self.root / 'restored'
        self.assertEqual(restore_bundle(backup, restored, self.directory / 'operator.key')['status'], 'PASS')
        other = Broker(restored)
        try:
            self.assertEqual(other.call(other.admin_token, 'inspect_native_runtime', runtime_id=saved['id']), saved)
            meter = {'materialized_bytes': 0}
            path = runtime.NativeRuntimes(other)._materialize(saved['id'], meter)
            self.assertTrue(path.resolve().is_relative_to(restored.resolve()))
            self.assertEqual(snapshot(path), MEMBERS)
            self.assertEqual(meter['materialized_bytes'], sum(map(len, MEMBERS.values())))
            self.assertEqual(other.call(other.admin_token, 'verify')['status'], 'PASS')
        finally:
            other.close()


if __name__ == '__main__':
    unittest.main()
