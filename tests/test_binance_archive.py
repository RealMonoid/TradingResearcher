"""Real archive integrity and time/quantity normalization, without market verdicts."""
import hashlib
import base64
import csv
import io
import json
import tempfile
import time
import subprocess
from pathlib import Path
import unittest
import zipfile
from unittest.mock import patch

from trading_researcher.codec import Invalid, canonical
from trading_researcher.binance_archive import archive_spec, unpack_archive, parse_month, acquire_month


def zipped(name, raw):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(name.removesuffix('.zip')+'.csv', raw)
    value = output.getvalue()
    return value, (hashlib.sha256(value).hexdigest()+'  '+name+'\n').encode()


class ArchiveTests(unittest.TestCase):
    def test_independently_fixed_cases(self):
        from trading_researcher.binance_archive import availability_scenario
        path = Path(__file__).parent/'fixtures/reference_binance_cases.json'
        raw = path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), 'a951d1a6cff1e459afb0588f2286c66c9b9533db375c6dc8a27515a4244ada00')
        fixture = json.loads(raw)
        self.assertEqual(len(fixture['cases']), 43)
        for case in fixture['cases']:
            with self.subTest(case=case['name']):
                expected = case['expected']
                if case['kind'] == 'availability_scenario':
                    self.assertEqual(availability_scenario(case['bar_end_time'], case['delay_seconds']), expected)
                    continue
                if case['kind'] == 'parse_csv':
                    output = io.StringIO(newline='')
                    csv.writer(output, lineterminator='\n').writerows(case['csv_rows'])
                    callback = lambda: parse_month(output.getvalue().encode(), case['symbol'], case['month'])
                else:
                    blob = fixture['archives'][case['archive_ref']]
                    payload = base64.b64decode(blob['bytes_base64'])
                    self.assertEqual(hashlib.sha256(payload).hexdigest(), blob['sha256'])
                    checksum = case.get('checksum_text', blob['sha256']+'  '+case['archive_name']+'\n').encode()
                    callback = lambda: unpack_archive(payload, checksum, case['archive_name'])
                if not expected['accepted']:
                    with self.assertRaises(Invalid):
                        callback()
                else:
                    result = callback()
                    if case['kind'] == 'parse_csv':
                        self.assertEqual(result['bars'], expected['bars'])
                        self.assertEqual(result['timestamp_unit'], case['timestamp_unit'])
                        self.assertEqual(result['availability'], 'UNKNOWN_HISTORICAL_PUBLICATION')
                    elif case['kind'] == 'read_archive':
                        self.assertEqual(result.decode(), expected['csv_text'])
                    else:
                        self.assertEqual(hashlib.sha256(payload).hexdigest(), expected['sha256'])

    def test_symbol_qualified_features_preserve_units_and_assumed_availability(self):
        from trading_researcher.binance_archive import reference_rows
        fixture = json.loads((Path(__file__).parent/'fixtures/reference_binance_cases.json').read_text())
        for symbol, base in (('BTCUSDT', 'BTC'), ('ETHUSDT', 'ETH')):
            case = next(c for c in fixture['cases'] if c['kind']=='parse_csv' and c['symbol']==symbol and c['expected']['accepted'])
            output = io.StringIO(newline='')
            csv.writer(output).writerows(case['csv_rows'])
            parsed = parse_month(output.getvalue().encode(), symbol, case['month'])
            normalized = reference_rows(parsed, delay_seconds=5)
            prefix = symbol+'.'
            suffix = '@binance-spot-15m-v1'
            self.assertEqual(normalized['catalog'][prefix+'close'+suffix]['unit'], 'USDT/'+base)
            self.assertEqual(normalized['catalog'][prefix+'volume'+suffix]['unit'], base)
            sample = normalized['rows'][0]
            self.assertEqual(sample['time'], parsed['bars'][0]['end_time'])
            self.assertEqual(sample['features'][prefix+'close'+suffix]['available_at'], sample['time']+5)
            self.assertEqual(normalized['availability']['basis'], 'assumed')
            self.assertIs(normalized['scientific_readiness'], False)
    def test_expected_url_and_declared_units(self):
        early = archive_spec('BTCUSDT', '2020-01')
        late = archive_spec('ETHUSDT', '2025-01')
        self.assertEqual(early['factor'], 1000)
        self.assertEqual(late['factor'], 1000000)
        self.assertEqual(early['name'], 'BTCUSDT-15m-2020-01.zip')
        self.assertEqual(early['url'], 'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/15m/BTCUSDT-15m-2020-01.zip')
        for symbol, month in (('../BTC', '2020-01'), ('BTCUSDT', '2019-12'), ('BTCUSDT', '2020-13')):
            with self.subTest(symbol=symbol, month=month), self.assertRaises(Invalid):
                archive_spec(symbol, month)

    def test_zip_checksum_and_exact_member_are_both_checked(self):
        spec = archive_spec('BTCUSDT', '2020-01')
        payload, checksum = zipped(spec['name'], b'exact original CSV bytes\r\n')
        self.assertEqual(unpack_archive(payload, checksum, spec['name']), b'exact original CSV bytes\r\n')
        with self.assertRaises(Invalid):
            unpack_archive(payload+b'changed', checksum, spec['name'])
        with self.assertRaises(Invalid):
            unpack_archive(payload, checksum.replace(b'BTCUSDT', b'ETHUSDT'), spec['name'])
        wrong, _ = zipped('other.zip', b'test')
        with self.assertRaises(Invalid):
            unpack_archive(wrong, hashlib.sha256(wrong).hexdigest().encode()+b'  '+spec['name'].encode(), spec['name'])

    def test_download_retains_failed_attempt_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)/'failed'
            def failing_download(url, limit):
                raise OSError('fixture transport failure')
            with self.assertRaises(OSError):
                acquire_month('BTCUSDT', '2020-01', target, downloader=failing_download)
            self.assertTrue((target/'failure.json').is_file())
            with self.assertRaises(FileExistsError):
                acquire_month('BTCUSDT', '2020-01', target, downloader=failing_download)

    def test_complete_acquisition_can_be_rechecked_without_network_or_new_receipt_time(self):
        from trading_researcher.binance_archive import read_acquisition
        fixture = json.loads((Path(__file__).parent/'fixtures/reference_binance_cases.json').read_text())
        payload = base64.b64decode(fixture['archives']['valid_one_csv']['bytes_base64'])
        name = 'BTCUSDT-15m-2020-01.zip'
        checksum = hashlib.sha256(payload).hexdigest().encode()+b'  '+name.encode()+b'\n'
        calls = []

        def download(url, limit):
            calls.append((url, limit))
            return (checksum if url.endswith('.CHECKSUM') else payload), {'etag': 'fixture', 'last_modified': None}

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/'source'
            receipt = acquire_month('BTCUSDT', '2020-01', directory, downloader=download)
            original = (directory/'acquisition.json').read_bytes()
            retained, parsed = read_acquisition(directory)
            self.assertEqual(retained, receipt)
            self.assertEqual(len(calls), 2)
            self.assertEqual(receipt['coverage']['missing_bars'], 2975)
            self.assertEqual(len(parsed['bars']), 1)
            self.assertEqual((directory/'acquisition.json').read_bytes(), original)
            (directory/name).write_bytes(b'corrupt')
            with self.assertRaises(Invalid):
                read_acquisition(directory)

    def test_checksum_failure_keeps_raw_bytes_without_success_receipt(self):
        payload, checksum = zipped('BTCUSDT-15m-2020-01.zip', b'not reached')
        checksum = checksum.replace(checksum[:64], b'0'*64)
        def download(url, limit):
            return (checksum if url.endswith('.CHECKSUM') else payload), {}
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/'bad-checksum'
            with self.assertRaises(Invalid):
                acquire_month('BTCUSDT', '2020-01', directory, downloader=download)
            self.assertTrue((directory/'failure.json').is_file())
            self.assertFalse((directory/'acquisition.json').exists())
            self.assertEqual((directory/'BTCUSDT-15m-2020-01.zip').read_bytes(), payload)

    def test_provider_document_capture_preserves_exact_bytes(self):
        from trading_researcher.binance_archive import capture_provider_docs
        def download(url, limit):
            return url.encode()+b'\r\noriginal\n', {}
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/'documents'
            receipt = capture_provider_docs(directory, downloader=download)
            for name, source in receipt['sources'].items():
                raw = (directory/name).read_bytes()
                self.assertEqual(raw, source['url'].encode()+b'\r\noriginal\n')
                self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])

    def test_multiline_and_unterminated_csv_are_typed_rejections_without_repair(self):
        for raw in (b'"unterminated\n',
                    b'1577836800000,"1\n0",12,9,11,4,1577837699999,42,4,2,22,0\n'):
            with self.subTest(raw=raw), self.assertRaises(Invalid):
                parse_month(raw, 'BTCUSDT', '2020-01')

    def test_reuse_rejects_forged_authority_and_receipt_time(self):
        from trading_researcher.binance_archive import read_acquisition
        fixture = json.loads((Path(__file__).parent/'fixtures/reference_binance_cases.json').read_text())
        payload = base64.b64decode(fixture['archives']['valid_one_csv']['bytes_base64'])
        checksum = hashlib.sha256(payload).hexdigest().encode()+b'  BTCUSDT-15m-2020-01.zip\n'
        def download(url, limit):
            return (checksum if url.endswith('.CHECKSUM') else payload), {}
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)/'source'
            receipt = acquire_month('BTCUSDT', '2020-01', directory, downloader=download)
            for field, value in (('scientific_readiness', True), ('availability', 'VERIFIED_HISTORICAL_PUBLICATION'),
                                 ('rights', 'UNRESTRICTED_LIVE_CAPITAL_USE'), ('retrieved_at', 'invented')):
                changed = dict(receipt, **{field: value})
                (directory/'acquisition.json').write_text(canonical(changed), encoding='utf-8')
                with self.subTest(field=field), self.assertRaises(Invalid):
                    read_acquisition(directory)

    def test_malformed_deflate_returns_typed_invalid(self):
        name = 'BTCUSDT-15m-2020-01.zip'
        payload, _ = zipped(name, b'synthetic data'*100)
        bad = bytearray(payload)
        length = int.from_bytes(bad[26:28], 'little')
        extra = int.from_bytes(bad[28:30], 'little')
        bad[30+length+extra] = 7  # Invalid DEFLATE block type.
        bad = bytes(bad)
        checksum = hashlib.sha256(bad).hexdigest().encode()+b'  '+name.encode()+b'\n'
        with self.assertRaises(Invalid):
            unpack_archive(bad, checksum, name)

    def test_download_checks_deadline_even_when_next_read_is_eof(self):
        from trading_researcher.binance_archive import _download_transport
        class Response:
            status = 200
            headers = {}
            def __enter__(self): return self
            def __exit__(self, *_): pass
            def geturl(self): return 'https://data.binance.vision/test'
            def read1(self, _count): return b''
        class Opener:
            def open(self, *_args, **_kwargs): return Response()
        with patch('trading_researcher.binance_archive.build_opener', return_value=Opener()), \
             patch('trading_researcher.binance_archive.time.monotonic', side_effect=[0, 0, 181]):
            with self.assertRaises(Invalid):
                _download_transport('https://data.binance.vision/test', 100)

    def test_download_terminates_real_stuck_child(self):
        from trading_researcher.binance_archive import _download
        started = time.monotonic()
        with patch('trading_researcher.binance_archive.DOWNLOAD_BOOTSTRAP', 'import time;time.sleep(30)'), \
             patch('trading_researcher.binance_archive.DOWNLOAD_TIMEOUT', 0.1):
            with self.assertRaisesRegex(Invalid, 'terminated'):
                _download('https://data.binance.vision/test', 100)
        self.assertLess(time.monotonic()-started, 5)

    def test_download_cancellation_reaps_owned_child(self):
        from trading_researcher.binance_archive import _download
        real_popen = subprocess.Popen
        children = []
        def spawn(*args, **kwargs):
            child = real_popen(*args, **kwargs)
            children.append(child)
            communicate = child.communicate
            calls = 0
            def interrupted(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise KeyboardInterrupt()
                return communicate(*args, **kwargs)
            child.communicate = interrupted
            return child
        try:
            with patch('trading_researcher.binance_archive.DOWNLOAD_BOOTSTRAP', 'import time;time.sleep(30)'), \
                 patch('trading_researcher.binance_archive.subprocess.Popen', side_effect=spawn):
                with self.assertRaises(KeyboardInterrupt):
                    _download('https://data.binance.vision/test', 100)
            self.assertIsNotNone(children[0].poll())
        finally:
            for child in children:
                if child.poll() is None:
                    child.kill()
                    child.communicate()
