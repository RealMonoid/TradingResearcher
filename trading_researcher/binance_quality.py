"""Row-keyed data quarantine under the unchanged complete-bar specification."""
import csv
import hashlib
import io
import re

from .codec import Invalid, integer
from .binance_archive import (MAX_CSV, archive_spec, _complete_bar, _InvalidBar,
                              reference_rows, availability_scenario)


def audit_month(raw, symbol, month):
    """Keep invalid keyed observations; reject ambiguous source structure atomically."""
    spec = archive_spec(symbol, month)
    if type(raw) is not bytes or not raw or len(raw) > MAX_CSV:
        raise Invalid('Quality audit needs a nonempty bounded monthly CSV')
    try:
        content = raw.decode('utf-8')
    except UnicodeError as exc:
        raise Invalid('Quality source must be exact UTF-8') from exc
    records, previous, present = [], None, set()
    for line, original in enumerate(io.StringIO(content, newline=''), 1):
        if len(original.rstrip('\r\n')) > 4096:
            raise Invalid('Source line exceeds the bounded CSV layout')
        try:
            rows = list(csv.reader([original], strict=True))
        except csv.Error as exc:
            raise Invalid('Ambiguous quoting or multiline source record') from exc
        if len(rows) != 1 or len(rows[0]) != 12:
            raise Invalid('Ambiguous or empty source record layout')
        columns = rows[0]
        if not re.fullmatch(r'[0-9]{1,20}', columns[0]):
            raise Invalid('Source record has no unambiguous open timestamp')
        opened, factor = int(columns[0]), spec['factor']
        if opened % (900*factor) or not spec['start']*factor <= opened < spec['end']*factor:
            raise Invalid('Source open timestamp does not match its declared grid/month/unit')
        when = opened//factor
        if previous is not None and when <= previous:
            raise Invalid('Duplicate or reversed source keys cannot be partially salvaged')
        previous = when
        present.add(when)
        record = {'line': line, 'open_time': when, 'end_time': when+900,
                  'raw_line_sha256': hashlib.sha256(original.encode('utf-8')).hexdigest(),
                  'status': 'VALID_COMPLETE_BAR', 'bar': None, 'reason': None}
        try:
            record['bar'] = _complete_bar(columns, spec)
        except _InvalidBar as exc:
            record.update(status='INVALID_BAR', reason=exc.reason)
        records.append(record)
    valid = sum(record['status'] == 'VALID_COMPLETE_BAR' for record in records)
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
    return {'schema': 'binance-row-quality/1', 'source_sha256': hashlib.sha256(raw).hexdigest(),
            'symbol': symbol, 'source_month': month, 'timestamp_unit': spec['timestamp_unit'],
            'records': records, 'coverage': {'expected_bars': expected, 'present_bars': len(records),
                'valid_bars': valid, 'invalid_bars': len(records)-valid,
                'missing_bars': expected-len(records), 'gaps': gaps},
            'expected_end_definition': 'open_time + 900; expected grid boundary, not an observed close for invalid bars',
            'availability': 'UNKNOWN_HISTORICAL_PUBLICATION', 'scientific_readiness': False}


def quality_reference_rows(raw, symbol, month, *, delay_seconds):
    """Explicit scenario from freshly audited bytes, never a supplied quality assertion."""
    integer(delay_seconds, 'explicit assumed delay')
    quality = audit_month(raw, symbol, month)
    valid = [record['bar'] for record in quality['records'] if record['bar'] is not None]
    result = reference_rows({'symbol': symbol, 'source_month': month, 'bars': valid}, delay_seconds=delay_seconds)
    rows = {row['time']: row for row in result['rows']}
    for record in quality['records']:
        if record['bar'] is None:
            scenario = availability_scenario(record['end_time'], delay_seconds)
            rows[record['end_time']] = {'time': record['end_time'], 'instrument': symbol,
                'features': {name: {'value': None, 'available_at': scenario['available_at']}
                             for name in result['catalog']}}
    result['rows'] = [rows[record['end_time']] for record in quality['records']]
    result['quality'] = quality
    return result
