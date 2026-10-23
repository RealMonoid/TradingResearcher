"""Bounded AmiBroker CLI smoke test. Standard library; no scientific verdicts."""
import argparse
import csv
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import uuid
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
START_MS = 1577836800000
NAME = 'BTCUSDT-15m-2020-01-01.zip'
URL = 'https://data.binance.vision/data/spot/daily/klines/BTCUSDT/15m/' + NAME
EXE = Path(r'C:\Program Files (x86)\AmiBroker\Broker.exe')


def unpack_verified(payload, checksum, name):
    parts = checksum.strip().split()
    if len(parts) != 2 or parts[1].lstrip('*') != name or parts[0].lower() != hashlib.sha256(payload).hexdigest():
        raise ValueError('Provider checksum or archive filename mismatch')
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        member = name.removesuffix('.zip') + '.csv'
        if archive.namelist() != [member] or archive.getinfo(member).file_size > 2_000_000:
            raise ValueError('Unexpected ZIP content')
        return archive.read(member)


def parse_klines(text):
    source = list(csv.reader(io.StringIO(text)))
    if len(source) != 96:
        raise ValueError('Expected exactly 96 15-minute candles for this fixed fixture')
    result = []
    for i, row in enumerate(source):
        expected = START_MS + i * 900000
        if len(row) != 12 or int(row[0]) != expected or int(row[6]) != expected + 899999:
            raise ValueError('Unexpected timestamp units, gaps, duplicates or kline layout')
        o, h, low, c, v = map(Decimal, row[1:6])
        if not all(x.is_finite() for x in (o, h, low, c, v)):
            raise ValueError('Nonfinite OHLCV')
        if min(o, h, low, c) <= 0 or v < 0 or low > min(o, c) or h < max(o, c) or low > h:
            raise ValueError('Invalid OHLCV ranges')
        # End boundary in UTC; do not present a fully formed candle at its opening time.
        end = datetime.fromtimestamp(expected / 1000, timezone.utc) + timedelta(minutes=15)
        result.append(dict(date=end.strftime('%Y-%m-%d'), time=end.strftime('%H:%M:%S'),
                           open=str(o), high=str(h), low=str(low), close=str(c), volume=str(v)))
    return result


def verify_export(text, expected):
    if not text.strip():
        raise ValueError('Empty export')
    delimiter = ';' if text.splitlines()[0].count(';') > text.splitlines()[0].count(',') else ','
    actual = list(csv.DictReader(io.StringIO(text), delimiter=delimiter))
    required = ['Day', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'LagClose', 'MA3', 'Interval']
    if len(actual) != len(expected) or not actual or list(actual[0]) != required:
        raise ValueError('Unexpected export columns or row count')
    max_error = 0.0
    for i, (got, want) in enumerate(zip(actual, expected)):
        dt = datetime.strptime(want['date'] + ' ' + want['time'], '%Y-%m-%d %H:%M:%S')
        values = {'Day': (dt.year-1900)*10000+dt.month*100+dt.day,
                  'Time': dt.hour*10000+dt.minute*100+dt.second, 'Interval': 900}
        values.update({k.capitalize(): float(want[k]) for k in ('open', 'high', 'low', 'close', 'volume')})
        values['LagClose'] = float(expected[i-1]['close']) if i else None
        values['MA3'] = sum(float(r['close']) for r in expected[i-2:i+1])/3 if i >= 2 else None
        for key, value in values.items():
            cell = got[key].strip()
            if value is None:
                if cell.lower() not in ('', '{empty}', 'null', 'n/a'):
                    raise ValueError(f'Unexpected non-null {key} at row {i}')
                continue
            number = float(cell.replace(',', '.'))
            tolerance = 0 if key in ('Day', 'Time', 'Interval') else max(0.002, abs(value)*2e-7)
            if not math.isfinite(number) or abs(number-value) > tolerance:
                raise ValueError(f'Export mismatch: row {i}, {key}, got {number}, expected {value}')
            max_error = max(max_error, abs(number-value))
    return {'rows': len(actual), 'ohlcv': 'PASS', 'utc_end_timestamps': 'PASS',
            'lag_close': 'PASS', 'ma3': 'PASS', 'interval_seconds': 900,
            'numeric_tolerance': 'max(0.002, abs(expected)*2e-7); timestamps/interval exact',
            'max_absolute_numeric_error': max_error}


def running_brokers():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq Broker.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, check=True)
    return [int(row[1]) for row in csv.reader(io.StringIO(result.stdout)) if row and row[0].lower() == 'broker.exe']


def host_call(action, database, *args):
    host = Path(os.environ['WINDIR']) / 'SysWOW64/cscript.exe'
    command = [str(host), '//nologo', '//T:45', str(HERE/'worker.js'), action, str(database), *map(str, args)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=50)
    if result.returncode:
        raise RuntimeError(f'WSH exit {result.returncode}: {result.stdout.strip()} {result.stderr.strip()}')
    return dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)


def write_project(path):
    root = ET.Element('AmiBroker-Analysis', CompactMode='0')
    general = ET.SubElement(root, 'General')
    formula = (HERE/'smoke.afl').read_text(encoding='ascii')
    for key, value in {'FormatVersion': '1', 'Symbol': 'BTCUSDT_TEST',
                       'FormulaPath': str(HERE/'smoke.afl'), 'FormulaContent': formula,
                       'ApplyTo': '0', 'RangeType': '0', 'RangeAmount': '1'}.items():
        ET.SubElement(general, key).text = value
    settings = ET.SubElement(root, 'BacktestSettings')
    ET.SubElement(settings, 'Periodicity').text = '3'  # 15-minute preset; independently verified in export.
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['probe', 'smoke-binance'])
    args = parser.parse_args()
    if os.name != 'nt' or not EXE.is_file():
        parser.error('This CLI requires the recorded Windows AmiBroker installation')
    existing = running_brokers()
    if args.command == 'probe' and existing:
        print(json.dumps({'status': 'PASS', 'scope': 'read-only existing application probe',
                          'application': host_call('probe', '')}, indent=2))
        return
    if existing:
        parser.error('AmiBroker is already running. Close it before starting an isolated smoke run.')
    base = ROOT/'.local/amibroker'
    base.mkdir(parents=True, exist_ok=True)
    (base/'.gitignore').write_text('*\n', encoding='ascii')
    run = base/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    run.mkdir()
    db = run/'database'
    db.mkdir()
    report = {'status': 'FAIL', 'scope': 'technical integration only', 'run_directory': str(run),
              'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'executable_sha256': hashlib.sha256(EXE.read_bytes()).hexdigest(),
              'controller_sha256': {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest()
                                    for name in ('cli.py', 'worker.js', 'smoke.afl', 'binance.format')}}
    process = None
    try:
        if args.command == 'smoke-binance':
            payload = urllib.request.urlopen(URL, timeout=30).read(2_000_001)
            checksum = urllib.request.urlopen(URL+'.CHECKSUM', timeout=30).read(4096).decode('ascii')
            raw_csv = unpack_verified(payload, checksum, NAME)
            rows = parse_klines(raw_csv.decode('utf-8-sig'))
            (run/NAME).write_bytes(payload)
            (run/(NAME+'.CHECKSUM')).write_text(checksum, encoding='ascii')
            (run/NAME.replace('.zip', '.csv')).write_bytes(raw_csv)
            with (run/'import.csv').open('w', newline='', encoding='ascii') as f:
                writer = csv.writer(f)
                for row in rows:
                    writer.writerow(['BTCUSDT_TEST', row['date'], row['time'],
                                     *[row[k] for k in ('open', 'high', 'low', 'close', 'volume')]])
            write_project(run/'smoke.apx')
            report['source'] = {'url': URL, 'sha256': hashlib.sha256(payload).hexdigest(),
                                'raw_csv_sha256': hashlib.sha256(raw_csv).hexdigest(),
                                'provider_checksum': 'PASS', 'rows': len(rows),
                                'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                                'timestamp_unit': 'milliseconds; explicit UTC conversion to bar-end boundary',
                                'role': 'exposed development/technical fixture; not confirmation',
                                'pit_vintage': 'unverified present-day archive download'}
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = 0
        process = subprocess.Popen([str(EXE), '/database', str(db)], cwd=EXE.parent, startupinfo=startup)
        time.sleep(2)
        if process.poll() is not None:
            raise RuntimeError('AmiBroker exited before automation connection')
        report['application'] = host_call('probe', db)
        if args.command == 'smoke-binance':
            report['automation'] = host_call('smoke', db, run/'import.csv', HERE/'binance.format',
                                              run/'smoke.apx', run/'exploration.csv')
            report['verification'] = verify_export((run/'exploration.csv').read_text(encoding='utf-8-sig'), rows)
        report['status'] = 'PASS'
    except Exception as error:
        report['error'] = str(error)
    finally:
        if process is not None and process.poll() is None:
            try:
                host_call('quit', db)
                process.wait(timeout=10)
            except Exception as error:
                report['status'] = 'FAIL'
                report['cleanup_error'] = str(error)
                # Only the process started by this invocation is eligible for termination.
                process.kill()
                process.wait(timeout=10)
        report['finished_at_utc'] = datetime.now(timezone.utc).isoformat()
        report['artifact_sha256'] = {str(p.relative_to(run)): hashlib.sha256(p.read_bytes()).hexdigest()
                                     for p in run.iterdir() if p.is_file()}
        (run/'result.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
