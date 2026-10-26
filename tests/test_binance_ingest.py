"""Exact acquisition bytes and row quality survive owned registry retention."""
import hashlib
import json
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

from trading_researcher.binance_archive import acquire_month, archive_spec
from trading_researcher.binance_ingest import retain_acquisition, retain_provider_documents
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.storage import restore_bundle
from test_binance_archive import zipped
from test_binance_quality import row


class IngestTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.broker = Broker(self.root/'registry')
        self.token = self.broker.admin_token

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def acquire(self, raw, month='2020-01'):
        spec = archive_spec('BTCUSDT',month)
        payload, checksum = zipped(spec['name'], raw)
        target = self.root/spec['name']
        try:
            acquire_month('BTCUSDT',month,target,downloader=lambda url,limit: (checksum if url.endswith('.CHECKSUM') else payload, {}))
        except Invalid:
            pass
        return target, spec

    def test_failed_strict_source_is_preserved_with_separate_quality_record_and_backup(self):
        source, spec = self.acquire(row()+row(1577837700000,close=1577838000000))
        original = (source/'failure.json').read_bytes()
        bundle = retain_acquisition(self.broker,self.token,source)
        body = bundle['body']
        self.assertEqual(body['schema'],'binance-source-bundle/1')
        self.assertEqual(body['original_acquisition_status'],'ACQUISITION_FAILED')
        self.assertEqual(body['coverage']['invalid_bars'],1)
        self.assertEqual(body['coverage']['valid_bars'],1)
        self.assertIs(body['scientific_readiness'],False)
        self.assertEqual(bundle['data_class'],'development')
        self.assertEqual((source/'failure.json').read_bytes(),original)
        self.assertEqual(len(body['files']),4)
        for name, descriptor in body['files'].items():
            self.assertEqual(descriptor['sha256'],hashlib.sha256((source/name).read_bytes()).hexdigest())
            self.assertIn(descriptor['artifact_ref'],bundle['exposure'])
        backup = self.root/'backup'
        self.broker.call(self.token,'backup_bundle',destination=str(backup))
        destination = self.root/'restored'
        restore_bundle(backup,destination,self.root/'registry/operator.key')
        restored = Broker(destination)
        try:
            saved = restored.call(restored.admin_token,'get_artifact',artifact_id=bundle['id'])
            self.assertEqual(saved,bundle)
            quality = restored.call(restored.admin_token,'get_artifact',artifact_id=body['quality_ref'])
            lines = restored._read_blob_bytes(quality['body']['blob']['sha256']).splitlines()
            self.assertEqual(json.loads(lines[1])['status'],'INVALID_BAR')
            self.assertEqual(json.loads(lines[1])['reason'],'INVALID_CLOSE_TIME')
        finally:
            restored.close()

    def test_corrupt_or_ambiguous_inputs_create_no_bundle(self):
        source, spec = self.acquire(row())
        (source/spec['name']).write_bytes(b'corrupt')
        before = self.broker._db.execute('SELECT count(*) FROM artifacts').fetchone()[0]
        with self.assertRaises(Invalid):
            retain_acquisition(self.broker,self.token,source)
        self.assertEqual(self.broker._db.execute('SELECT count(*) FROM artifacts').fetchone()[0],before)

    def test_protected_month_cannot_be_imported_as_development(self):
        source, spec = self.acquire(row(1704067200000),'2024-01')
        bundle = retain_acquisition(self.broker,self.token,source)
        self.assertEqual(bundle['data_class'],'assessment')
        for ref in bundle['exposure']:
            saved = self.broker.call(self.token,'get_artifact',artifact_id=ref)
            self.assertEqual(saved['data_class'],'assessment')

    def test_failed_receipt_cannot_claim_scientific_or_historical_authority(self):
        source, spec = self.acquire(row(close=1577837000000))
        path = source/'failure.json'
        receipt = json.loads(path.read_bytes())
        receipt['scientific_readiness'] = True
        path.write_text(json.dumps(receipt))
        with self.assertRaises(Invalid):
            retain_acquisition(self.broker,self.token,source)

    def test_new_failure_receipt_binds_completed_files_before_content_check(self):
        source, spec = self.acquire(row(close=1577837000000))
        receipt = json.loads((source/'failure.json').read_bytes())
        self.assertEqual(len(receipt['files']),3)
        bundle = retain_acquisition(self.broker,self.token,source)
        self.assertEqual(bundle['body']['receipt_file_binding'],'VERIFIED_FILE_HASHES')
        self.assertEqual(bundle['body']['retrieved_at'],receipt['retrieved_at'])
        self.assertIs(bundle['body']['scientific_readiness'],False)

    def test_legacy_failure_does_not_bind_its_old_time_to_replacement_bytes(self):
        source, spec = self.acquire(row(close=1577837000000))
        path = source/'failure.json'
        receipt = json.loads(path.read_bytes())
        receipt['files'] = {}
        receipt['started_at'] = '2026-01-01T00:00:00Z'
        receipt['retrieved_at'] = '2026-01-01T00:00:01Z'
        path.write_text(json.dumps(receipt))
        raw = row(close=1577837100000)
        payload, checksum = zipped(spec['name'], raw)
        (source/spec['name']).write_bytes(payload)
        (source/(spec['name']+'.CHECKSUM')).write_bytes(checksum)
        (source/(spec['name'].removesuffix('.zip')+'.csv')).write_bytes(raw)
        body = retain_acquisition(self.broker,self.token,source)['body']
        self.assertIsNone(body['retrieved_at'])
        self.assertEqual(body['receipt_file_binding'],'UNVERIFIED_LEGACY_FAILURE')
        self.assertEqual(body['original_receipt_retrieved_at'],receipt['retrieved_at'])
        self.assertGreater(body['verified_at'], receipt['retrieved_at'])

    def test_bound_failure_rejects_consistent_replacement_files(self):
        source, spec = self.acquire(row(close=1577837000000))
        path = source/'failure.json'
        receipt = json.loads(path.read_bytes())
        receipt['files'] = {name: {'sha256':hashlib.sha256((source/name).read_bytes()).hexdigest(),
            'size':(source/name).stat().st_size} for name in (spec['name'],spec['name']+'.CHECKSUM',spec['name'].removesuffix('.zip')+'.csv')}
        path.write_text(json.dumps(receipt))
        raw = row(close=1577837100000)
        payload, checksum = zipped(spec['name'],raw)
        (source/spec['name']).write_bytes(payload)
        (source/(spec['name']+'.CHECKSUM')).write_bytes(checksum)
        (source/(spec['name'].removesuffix('.zip')+'.csv')).write_bytes(raw)
        with self.assertRaises(Invalid):
            retain_acquisition(self.broker,self.token,source)

    def test_provider_documents_retain_exact_bytes_and_qualified_rights(self):
        from trading_researcher.binance_archive import capture_provider_docs
        source = self.root/'docs'
        receipt = capture_provider_docs(source,downloader=lambda url,limit:(b'provider fixture\n', {}))
        bundle = retain_provider_documents(self.broker,self.token,source)
        self.assertEqual(bundle['body']['retrieved_at'],receipt['retrieved_at'])
        self.assertIs(bundle['body']['scientific_readiness'],False)
        self.assertEqual(len(bundle['body']['files']),3)
        (source/'README.md').write_bytes(b'changed')
        with self.assertRaises(Invalid):
            retain_provider_documents(self.broker,self.token,source)

    def test_cli_retains_a_month_without_printing_market_values(self):
        source, _ = self.acquire(row())
        result = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'retain-binance-month',
            '--directory', str(self.root/'cli-registry'), '--source-directory', str(source)],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)['body']
        self.assertEqual(body['coverage']['valid_bars'], 1)
        self.assertNotIn('records',body)
        self.assertIs(body['scientific_readiness'],False)


if __name__ == '__main__':
    unittest.main()
