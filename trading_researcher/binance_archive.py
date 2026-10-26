"""Bounded public spot archive acquisition; no historical-availability or trading claim."""
import csv
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import io
import re
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler
import zipfile
import zlib

from .codec import Invalid, canonical, decode, integer, MAX_BYTES
from .data import MAX_UTC_SECOND
from .formalization import utc
from .expressions import DECIMAL
from .storage import _durable_file


MAX_ARCHIVE = 8 * 1024 * 1024
MAX_CSV = 16 * 1024 * 1024
README_URL = 'https://raw.githubusercontent.com/binance/binance-public-data/master/README.md'
TERMS_URL = 'https://raw.githubusercontent.com/binance/binance-public-data/master/TERMS_AND_CONDITIONS.md'
PURPOSE = 'Personal non-production historical research'
RIGHTS = 'Personal non-production scope; separate terms snapshot required'
DOWNLOAD_TIMEOUT = 125
DOWNLOAD_BOOTSTRAP = 'import sys;sys.path.insert(0,sys.argv[1]);from trading_researcher.binance_archive import _download_child;_download_child(sys.argv[2],int(sys.argv[3]))'


def archive_spec(symbol, month):
    if type(symbol) is not str or symbol not in ('BTCUSDT', 'ETHUSDT'):
        raise Invalid('Only the adopted BTCUSDT/ETHUSDT spot profile is available')
    if type(month) is not str or not re.fullmatch(r'202[0-5]-(?:0[1-9]|1[0-2])', month):
        raise Invalid('Use a calendar month from the adopted 2020-2025 profile')
    year, number = map(int, month.split('-'))
    start = datetime(year, number, 1, tzinfo=timezone.utc)
    end = datetime(year + (number == 12), number % 12 + 1, 1, tzinfo=timezone.utc)
    name = f'{symbol}-15m-{month}.zip'
    return {'symbol': symbol, 'month': month, 'name': name,
        'url': f'https://data.binance.vision/data/spot/monthly/klines/{symbol}/15m/{name}',
        'start': int(start.timestamp()), 'end': int(end.timestamp()),
        'factor': 1000000 if year >= 2025 else 1000,
        'timestamp_unit': 'microseconds' if year >= 2025 else 'milliseconds'}


def unpack_archive(payload, checksum, name):
    if type(payload) is not bytes or len(payload) > MAX_ARCHIVE:
        raise Invalid('Archive exceeds the 8 MiB monthly resource envelope')
    try:
        tokens = checksum.decode('ascii').split()
    except (AttributeError, UnicodeError) as exc:
        raise Invalid('Checksum must be the original ASCII checksum file') from exc
    if (len(checksum) > 4096 or len(tokens) != 2 or tokens[1].lstrip('*') != name
            or tokens[0].lower() != hashlib.sha256(payload).hexdigest()):
        raise Invalid('Archive filename or retained provider checksum mismatch')
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            member = name.removesuffix('.zip') + '.csv'
            if archive.namelist() != [member]:
                raise Invalid('Archive must contain exactly its expected CSV member')
            info = archive.getinfo(member)
            if info.is_dir() or info.file_size > MAX_CSV or info.flag_bits & 1:
                raise Invalid('Unsupported or oversized archive member')
            with archive.open(info) as stream:
                raw = stream.read(MAX_CSV+1)
            if len(raw) != info.file_size or len(raw) > MAX_CSV:
                raise Invalid('Uncompressed CSV size mismatch or resource overflow')
            return raw
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError, zlib.error, EOFError) as exc:
        raise Invalid('Archive decompression or CRC validation failed') from exc


def _quantity(value):
    if type(value) is not str or len(value) > 100 or not DECIMAL.fullmatch(value):
        raise Invalid('Source quantities require bounded plain finite decimal strings')
    number = Fraction(value)
    if number < 0:
        raise Invalid('Prices and quantities cannot be negative')
    normalized = value.rstrip('0').rstrip('.') if '.' in value else value
    return ('0' if number == 0 else normalized), number


class _InvalidBar(Invalid):
    def __init__(self, reason, message):
        super().__init__(message)
        self.reason = reason


def _complete_bar(columns, spec):
    """The shared complete-bar specification; no repair or missing-value policy."""
    if len(columns) != 12 or not re.fullmatch(r'[0-9]{1,20}', columns[0]):
        raise Invalid('Unexpected open timestamp or 12-column CSV layout')
    opened, factor = int(columns[0]), spec['factor']
    if opened % (900*factor) or not spec['start']*factor <= opened < spec['end']*factor:
        raise Invalid('Open timestamp units, grid or declared month do not match')
    if not re.fullmatch(r'[0-9]{1,20}', columns[6]) or int(columns[6]) != opened+900*factor-1:
        raise _InvalidBar('INVALID_CLOSE_TIME', 'Timestamp units or exact bar close do not match')
    if not re.fullmatch(r'[0-9]{1,20}', columns[8]):
        raise _InvalidBar('INVALID_TRADE_COUNT', 'Trade count must be a nonnegative bounded integer')
    names = {1: 'open', 2: 'high', 3: 'low', 4: 'close', 5: 'volume',
             7: 'quote_volume', 9: 'taker_base_volume', 10: 'taker_quote_volume'}
    normalized, numbers = {}, {}
    try:
        for index, name in names.items():
            normalized[name], numbers[name] = _quantity(columns[index])
        _quantity(columns[11])
    except Invalid as exc:
        raise _InvalidBar('INVALID_QUANTITY', str(exc)) from exc
    if (min(numbers[name] for name in ('open', 'high', 'low', 'close')) <= 0
            or numbers['low'] > min(numbers['open'], numbers['close'])
            or numbers['high'] < max(numbers['open'], numbers['close'])
            or numbers['low'] > numbers['high']
            or numbers['taker_base_volume'] > numbers['volume']
            or numbers['taker_quote_volume'] > numbers['quote_volume']):
        raise _InvalidBar('OHLC_VOLUME_INVARIANT', 'OHLC or volume invariants fail')
    when = opened//factor
    return {'open_time': when, 'end_time': when+900, **normalized, 'trades': int(columns[8])}


def parse_month(raw, symbol, month):
    spec = archive_spec(symbol, month)
    if type(raw) is not bytes or len(raw) > MAX_CSV:
        raise Invalid('CSV exceeds its monthly byte envelope')
    try:
        content = raw.decode('utf-8')
    except UnicodeError as exc:
        raise Invalid('Source CSV must be UTF-8 without replacement') from exc
    lines = content.splitlines()
    if not lines or any(not line or len(line) > 4096 for line in lines):
        raise Invalid('Empty or oversized CSV lines are unsupported')
    bars, previous, present = [], None, set()
    # Preserve embedded line endings, so quoted multiline numbers cannot be repaired by concatenation.
    try:
        records = list(csv.reader(io.StringIO(content, newline=''), strict=True))
    except csv.Error as exc:
        raise Invalid('Malformed CSV quoting or field layout') from exc
    for columns in records:
        bar = _complete_bar(columns, spec)
        when = bar['open_time']
        if previous is not None and when <= previous:
            raise Invalid('Duplicate or reversed source observations')
        previous = when
        bars.append(bar)
        present.add(when)
    gaps, active = [], None
    for when in range(spec['start'], spec['end'], 900):
        if when not in present:
            if active is None:
                active = {'start': when, 'end': when+900, 'missing_bars': 1}
                gaps.append(active)
            else:
                active['end'] = when+900
                active['missing_bars'] += 1
        else:
            active = None
    expected = (spec['end']-spec['start'])//900
    return {'bars': bars, 'timestamp_unit': spec['timestamp_unit'], 'coverage': {
        'expected_bars': expected, 'observed_bars': len(bars), 'missing_bars': expected-len(bars), 'gaps': gaps},
        'availability': 'UNKNOWN_HISTORICAL_PUBLICATION', 'source_month': month, 'symbol': symbol}


def availability_scenario(bar_end_time, delay_seconds):
    integer(bar_end_time, 'bar end time')
    integer(delay_seconds, 'explicit assumed delay')
    if bar_end_time % 900 or bar_end_time+delay_seconds > MAX_UTC_SECOND:
        raise Invalid('Scenario requires an aligned bar end and representable UTC seconds')
    return {'row_time': bar_end_time, 'available_at': bar_end_time+delay_seconds,
            'availability_basis': 'assumed', 'historical_publication_time': None, 'scientific_readiness': False}


def reference_rows(parsed, *, delay_seconds):
    """Explicit simulation scenario; no publication truth and no partition selection."""
    symbol = archive_spec(parsed['symbol'], parsed['source_month'])['symbol']
    base = 'BTC' if symbol == 'BTCUSDT' else 'ETH'
    units = {name: 'USDT/'+base for name in ('open', 'high', 'low', 'close')}
    units.update({'volume': base, 'taker_base_volume': base, 'quote_volume': 'USDT',
                  'taker_quote_volume': 'USDT', 'trades': 'count'})
    names = {name: symbol+'.'+name+'@binance-spot-15m-v1' for name in units}
    catalog = {names[name]: {'type': 'real', 'unit': unit} for name, unit in units.items()}
    rows = []
    for bar in parsed['bars']:
        scenario = availability_scenario(bar['end_time'], delay_seconds)
        rows.append({'time': bar['end_time'], 'instrument': symbol, 'features': {
            names[name]: {'value': str(bar[name]), 'available_at': scenario['available_at']} for name in units}})
    return {'catalog': catalog, 'rows': rows,
            'availability': {'basis': 'assumed', 'delay_seconds': delay_seconds,
                             'historical_publication_time': None}, 'scientific_readiness': False}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        return None


def _download_transport(url, limit):
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    started = time.monotonic()
    request = Request(url, headers={'User-Agent': 'TradingResearcher-personal-research/0.1'})
    with opener.open(request, timeout=30) as response:
        if response.status != 200 or response.geturl() != url:
            raise Invalid('Download did not return the exact requested HTTPS resource')
        length = response.headers.get('Content-Length')
        if length is not None and (not length.isdigit() or int(length) > limit):
            raise Invalid('Download exceeds its declared size bound')
        pieces, size = [], 0
        while True:
            if time.monotonic()-started > 120:
                raise Invalid('Download exceeded its success deadline')
            piece = response.read1(min(65536, limit-size+1))
            if time.monotonic()-started > 120:
                raise Invalid('Download exceeded its success deadline')
            if not piece:
                break
            size += len(piece)
            if size > limit or time.monotonic()-started > 120:
                raise Invalid('Download exceeded its byte/time resource envelope')
            pieces.append(piece)
        if length is not None and size != int(length):
            raise Invalid('Download size differs from Content-Length')
        metadata = {'etag': response.headers.get('ETag'), 'last_modified': response.headers.get('Last-Modified')}
        if any(value is not None and len(value) > 8192 for value in metadata.values()):
            raise Invalid('Response metadata exceeds its bounded envelope')
        return b''.join(pieces), metadata


def _download_child(url, limit):
    try:
        raw, metadata = _download_transport(url, limit)
        header = canonical(metadata).encode()
        sys.stdout.buffer.write(len(header).to_bytes(4, 'big')+header+raw)
    except Exception as exc:
        sys.stderr.write(type(exc).__name__)
        raise SystemExit(2)


def _download(url, limit):
    """Own one child so slow headers, DNS or trickled bodies cannot retain execution indefinitely."""
    process = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', DOWNLOAD_BOOTSTRAP,
        str(Path(__file__).resolve().parents[1]), url, str(limit)], stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    try:
        output, error = process.communicate(timeout=DOWNLOAD_TIMEOUT)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise Invalid('Download child exceeded its hard lifetime and was terminated') from None
    except BaseException:
        if process.poll() is None:
            process.kill()
        process.communicate()
        raise
    if process.returncode != 0 or len(output) < 4 or len(output) > limit+20004:
        raise Invalid('Bounded HTTPS acquisition failed')
    size = int.from_bytes(output[:4], 'big')
    if size > 20000 or size > len(output)-4:
        raise Invalid('Invalid acquisition child envelope')
    metadata = decode(output[4:4+size])
    if (type(metadata) is not dict or set(metadata) != {'etag', 'last_modified'}
            or any(value is not None and (type(value) is not str or len(value) > 8192) for value in metadata.values())):
        raise Invalid('Invalid acquisition metadata')
    raw = output[4+size:]
    if len(raw) > limit:
        raise Invalid('Acquisition child exceeded its byte envelope')
    return raw, metadata


def acquire_month(symbol, month, destination, *, downloader=None):
    """New attempt directory, exact files and immutable success/failure receipts; no retries."""
    spec = archive_spec(symbol, month)
    directory = Path(destination).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    download = downloader or _download
    receipt = {'schema': 'binance-month-acquisition/1', 'symbol': symbol, 'month': month,
        'url': spec['url'], 'started_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'purpose': PURPOSE, 'files': {}}
    try:
        payload, metadata = download(spec['url'], MAX_ARCHIVE)
        _durable_file(directory/spec['name'], payload)
        receipt['files'][spec['name']] = {'sha256': hashlib.sha256(payload).hexdigest(), 'size': len(payload)}
        checksum_name = spec['name']+'.CHECKSUM'
        checksum, checksum_metadata = download(spec['url']+'.CHECKSUM', 4096)
        receipt['retrieved_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        _durable_file(directory/checksum_name, checksum)
        receipt['files'][checksum_name] = {'sha256': hashlib.sha256(checksum).hexdigest(), 'size': len(checksum)}
        raw = unpack_archive(payload, checksum, spec['name'])
        csv_name = spec['name'].removesuffix('.zip')+'.csv'
        _durable_file(directory/csv_name, raw)
        receipt['files'][csv_name] = {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
        parsed = parse_month(raw, symbol, month)
        receipt.update({'status': 'SOURCE_INTEGRITY_CHECKED', 'timestamp_unit': spec['timestamp_unit'],
            'checksum': 'MATCHES_RETRIEVED_PROVIDER_FILE', 'http': metadata, 'checksum_http': checksum_metadata,
            'coverage': parsed['coverage'], 'availability': parsed['availability'],
            'scientific_readiness': False, 'rights': RIGHTS})
        _durable_file(directory/'acquisition.json', (canonical(receipt)+'\n').encode())
        return receipt
    except Exception as exc:
        receipt.update({'status': 'ACQUISITION_FAILED', 'error_type': type(exc).__name__,
                        'scientific_readiness': False})
        _durable_file(directory/'failure.json', (canonical(receipt)+'\n').encode())
        raise


def _acquisition_header(receipt):
    expected_fields = {'schema', 'symbol', 'month', 'url', 'started_at', 'retrieved_at', 'purpose', 'files',
        'status', 'timestamp_unit', 'checksum', 'http', 'checksum_http', 'coverage', 'availability',
        'scientific_readiness', 'rights'}
    if type(receipt) is not dict or set(receipt) != expected_fields:
        raise Invalid('Unexpected acquisition receipt fields')
    spec = archive_spec(receipt['symbol'], receipt['month'])
    names = [spec['name'], spec['name']+'.CHECKSUM', spec['name'].removesuffix('.zip')+'.csv']
    if (receipt.get('schema') != 'binance-month-acquisition/1' or receipt.get('url') != spec['url']
            or receipt.get('status') != 'SOURCE_INTEGRITY_CHECKED' or type(receipt['files']) is not dict
            or set(receipt['files']) != set(names) or receipt['scientific_readiness'] is not False
            or receipt['availability'] != 'UNKNOWN_HISTORICAL_PUBLICATION' or receipt['rights'] != RIGHTS
            or receipt['purpose'] != PURPOSE or receipt['checksum'] != 'MATCHES_RETRIEVED_PROVIDER_FILE'):
        raise Invalid('Unsupported or incomplete acquisition receipt')
    if not utc(receipt['started_at']) <= utc(receipt['retrieved_at']) <= datetime.now(timezone.utc):
        raise Invalid('Invalid acquisition receipt times')
    return spec, names


def validate_acquisition_bytes(receipt, values):
    """Validate complete success semantics against captured bytes, including registry reuse."""
    spec, names = _acquisition_header(receipt)
    if type(values) is not dict or set(values) != set(names):
        raise Invalid('Success receipt requires exactly its original source files')
    for name, limit in zip(names, (MAX_ARCHIVE, 4096, MAX_CSV)):
        value = values[name]
        if (type(value) is not bytes or len(value) > limit
                or receipt['files'][name] != {'sha256': hashlib.sha256(value).hexdigest(), 'size': len(value)}):
            raise Invalid('Retained acquisition bytes changed')
    raw = unpack_archive(values[names[0]], values[names[1]], names[0])
    if raw != values[names[2]]:
        raise Invalid('Retained CSV differs from its verified archive')
    parsed = parse_month(raw, spec['symbol'], spec['month'])
    if parsed['coverage'] != receipt['coverage'] or parsed['timestamp_unit'] != receipt['timestamp_unit']:
        raise Invalid('Retained acquisition checks differ from their receipt')
    return parsed


def read_acquisition(directory):
    """Validate retained exact files before reuse, without refreshing historical receipt time."""
    directory = Path(directory).resolve()
    receipt = decode(_read_bounded(directory/'acquisition.json', MAX_BYTES))
    _, names = _acquisition_header(receipt)
    values = {name: _read_bounded(directory/name, limit)
              for name, limit in zip(names, (MAX_ARCHIVE, 4096, MAX_CSV))}
    return receipt, validate_acquisition_bytes(receipt, values)


def _read_bounded(path, limit):
    with Path(path).open('rb') as stream:
        value = stream.read(limit+1)
    if len(value) > limit:
        raise Invalid('Retained acquisition exceeds its resource envelope')
    return value


def capture_provider_docs(destination, *, downloader=None):
    """Retain acquisition-time documentation/terms; no acceptance of later production use."""
    directory = Path(destination).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    download = downloader or _download
    receipt = {'schema': 'binance-document-snapshot/1',
        'started_at': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), 'sources': {}}
    for name, url in (('README.md', README_URL), ('TERMS_AND_CONDITIONS.md', TERMS_URL)):
        raw, metadata = download(url, MAX_BYTES)
        _durable_file(directory/name, raw)
        receipt['sources'][name] = {'url': url, 'sha256': hashlib.sha256(raw).hexdigest(),
                                    'size': len(raw), 'http': metadata}
    receipt['retrieved_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    _durable_file(directory/'documents.json', (canonical(receipt)+'\n').encode())
    return receipt
