"""Content-addressed blobs, committed references and complete backup restoration."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.storage import restore_bundle


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.directory = self.root / 'runtime'
        self.broker = Broker(self.directory, clock=lambda: 1000)
        self.admin = self.broker.admin_token

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def op(self, operation, **args):
        return self.broker.call(self.admin, operation, **args)

    def source(self, raw=b'original source\x00bytes\r\n', data_class='development'):
        path = self.root / 'input.bin'
        path.write_bytes(raw)
        return self.op('add_blob_source', path=str(path), data_class=data_class,
                       description='A supplied fixture, not a certified market dataset')

    def test_bytes_larger_than_rpc_limit_are_retained_by_hash(self):
        raw = bytes(range(256)) * 8193
        source = self.source(raw)
        descriptor = source['body']['blob']
        self.assertEqual(descriptor, {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)})
        self.assertEqual(self.broker._read_blob_bytes(descriptor['sha256']), raw)
        self.assertEqual(source['blob_refs'], [descriptor['sha256']])
        self.assertEqual(self.op('verify')['blobs']['committed'], 1)
        self.assertEqual(self.op('get_artifact', artifact_id=source['id']), source)

    def test_duplicate_content_deduplicates_and_staging_alone_grants_no_reference(self):
        first = self.source()
        second = self.source()
        self.assertEqual(first['body']['blob'], second['body']['blob'])
        self.assertEqual(self.op('verify')['blobs']['committed'], 1)
        orphan = self.broker._stage_blob_bytes(b'uncommitted bytes')
        with self.assertRaises(Denied):
            self.broker._read_blob_bytes(orphan['sha256'])
        self.assertEqual(self.op('verify')['blobs']['committed'], 1)

    def test_workers_cannot_import_files_and_typed_namespace_cannot_be_forged(self):
        token = self.op('register_worker', name='reader', role='discovery', capabilities=['draft/v1'])['token']
        with self.assertRaises(Denied):
            self.broker.call(token, 'add_blob_source', path=str(self.root / 'unknown'),
                             data_class='development', description='denied')
        for schema in ('blob-source/1', 'reference-source-package/1'):
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                self.op('add_source', body={'schema': schema}, data_class='development')

    def test_missing_or_corrupt_committed_content_is_quarantined_on_restart(self):
        source = self.source()
        identity = source['body']['blob']['sha256']
        path = self.broker._blob_path(identity)
        path.write_bytes(b'corrupt')
        self.broker.close()
        self.broker = Broker(self.directory, clock=lambda: 1000)
        report = self.op('verify')
        self.assertEqual(report['status'], 'QUARANTINED')
        self.assertEqual(report['blobs']['quarantined'][0]['sha256'], identity)
        with self.assertRaises(Conflict):
            self.broker._read_blob_bytes(identity)
        path.unlink()
        self.assertEqual(self.op('verify')['blobs']['quarantined'][0]['reason'], 'MISSING')

    def test_database_only_backup_cannot_omit_committed_blobs(self):
        self.source()
        with self.assertRaises(Conflict):
            self.op('backup', destination=str(self.root / 'incomplete.sqlite3'))
        self.assertFalse((self.root / 'incomplete.sqlite3').exists())

    def test_complete_backup_restore_preserves_data_records_and_projection(self):
        source = self.source()
        record = self.op('add_research', kind='observation', content={'text': 'Source received'},
                         scope={}, source_refs=[source['id']])
        record = self.op('get_artifact', artifact_id=record['id'])
        destination = self.root / 'backup'
        backup = self.op('backup_bundle', destination=str(destination))
        self.assertEqual(backup['status'], 'PASS')
        self.assertFalse((destination / 'operator.key').exists())
        restored = self.root / 'restored'
        result = restore_bundle(destination, restored, self.directory / 'operator.key')
        self.assertEqual(result['status'], 'PASS')
        other = Broker(restored, clock=lambda: 1000)
        try:
            self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=source['id']), source)
            self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=record['id']), record)
            self.assertEqual(other.call(other.admin_token, 'verify')['status'], 'PASS')
            self.assertEqual(other._read_blob_bytes(source['body']['blob']['sha256']), b'original source\x00bytes\r\n')
        finally:
            other.close()

    def test_backup_and_restore_refuse_corrupt_missing_or_substituted_inputs(self):
        source = self.source()
        destination = self.root / 'backup'
        self.op('backup_bundle', destination=str(destination))
        manifest = json.loads((destination / 'manifest.json').read_text(encoding='utf-8'))
        identity = source['body']['blob']['sha256']
        blob = destination / 'blobs' / identity[:2] / identity
        blob.write_bytes(b'changed backup content')
        target = self.root / 'bad-restore'
        with self.assertRaises(Conflict):
            restore_bundle(destination, target, self.directory / 'operator.key')
        self.assertFalse(target.exists())
        self.assertEqual(manifest['blobs'][identity], source['body']['blob']['size'])
        self.broker._blob_path(identity).unlink()
        with self.assertRaises(Conflict):
            self.op('backup_bundle', destination=str(self.root / 'bad-backup'))
        self.assertFalse((self.root / 'bad-backup').exists())

    def test_restore_never_overwrites_existing_destination_or_accepts_wrong_key(self):
        self.source()
        destination = self.root / 'backup'
        self.op('backup_bundle', destination=str(destination))
        occupied = self.root / 'occupied'
        occupied.mkdir()
        (occupied / 'keep.txt').write_text('preserve', encoding='utf-8')
        with self.assertRaises(Conflict):
            restore_bundle(destination, occupied, self.directory / 'operator.key')
        self.assertEqual((occupied / 'keep.txt').read_text(encoding='utf-8'), 'preserve')
        wrong = self.root / 'wrong.key'
        wrong.write_text('wrong-secret-value' * 3, encoding='utf-8')
        with self.assertRaises(Denied):
            restore_bundle(destination, self.root / 'wrong-key-restore', wrong)

    def test_registry_references_are_immutable_and_existing_small_artifacts_survive_extension(self):
        source = self.source()
        with self.assertRaises(sqlite3.IntegrityError):
            self.broker._db.execute('DELETE FROM artifact_blobs WHERE artifact_id=?', (source['id'],))
        self.assertEqual(self.op('get_artifact', artifact_id=source['id']), source)

    def test_actual_process_exit_before_and_after_reference_commit(self):
        for committed in (False, True):
            with self.subTest(committed=committed):
                directory = self.root / ('committed-crash' if committed else 'staging-crash')
                input_file = self.root / 'crash-source.bin'
                input_file.write_bytes(b'crash fixture')
                action = ('broker.call(broker.admin_token,"add_blob_source",path=sys.argv[2],'
                          'data_class="development",description="crash fixture")' if committed else
                          'broker._stage_blob_bytes(b"crash fixture")')
                script = ('import os,sys\nfrom trading_researcher.coordination import Broker\n'
                          'broker=Broker(sys.argv[1])\n' + action + '\nos._exit(27)\n')
                process = subprocess.run([sys.executable, '-B', '-c', script, str(directory), str(input_file)],
                                         capture_output=True, timeout=30)
                self.assertEqual(process.returncode, 27, process.stderr)
                other = Broker(directory)
                try:
                    report = other.call(other.admin_token, 'verify')
                    self.assertEqual(report['status'], 'PASS')
                    self.assertEqual(report['blobs']['committed'], int(committed))
                    identity = hashlib.sha256(b'crash fixture').hexdigest()
                    if committed:
                        self.assertEqual(other._read_blob_bytes(identity), b'crash fixture')
                    else:
                        with self.assertRaises(Denied):
                            other._read_blob_bytes(identity)
                finally:
                    other.close()

    def test_legacy_extension_migration_preserves_small_artifacts_and_checkpoint(self):
        source = self.op('add_source', body={'text': 'legacy small record'}, data_class='development')
        self.broker.close()
        with closing(sqlite3.connect(self.directory / 'registry.sqlite3')) as db:
            for table in ('artifact_blobs', 'blobs', 'blob_meta'):
                db.execute('DROP TABLE ' + table)
            db.commit()
        self.broker = Broker(self.directory, clock=lambda: 1000)
        self.assertTrue((self.directory / 'before-external-blobs-v1.sqlite3').is_file())
        self.assertEqual(self.op('get_artifact', artifact_id=source['id']), source)

    def test_cli_backup_restore_and_quarantine_exit(self):
        source = self.source()
        self.broker.close()
        destination, restored = self.root / 'cli-backup', self.root / 'cli-restored'
        backup = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'backup-bundle',
                                 '--directory', str(self.directory), '--destination', str(destination)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(backup.returncode, 0, backup.stderr)
        restore = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'restore-bundle',
                                  '--directory', str(restored), '--bundle', str(destination),
                                  '--operator-key-file', str(self.directory / 'operator.key')],
                                 capture_output=True, text=True, timeout=30)
        self.assertEqual(restore.returncode, 0, restore.stderr)
        self.assertEqual(json.loads(restore.stdout)['status'], 'PASS')
        identity = source['body']['blob']['sha256']
        (restored / 'blobs' / identity[:2] / identity).write_bytes(b'corrupt')
        verify = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'verify',
                                 '--directory', str(restored)], capture_output=True, text=True, timeout=30)
        self.assertEqual(verify.returncode, 2, verify.stderr)
        self.assertEqual(json.loads(verify.stdout)['status'], 'QUARANTINED')
        self.broker = Broker(self.directory, clock=lambda: 1000)


if __name__ == '__main__':
    unittest.main()
