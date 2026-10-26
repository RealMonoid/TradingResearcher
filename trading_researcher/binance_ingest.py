"""Owned source retention, not scientific data acceptance or normalization freeze."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tempfile

from .binance_archive import (MAX_ARCHIVE, MAX_CSV, PURPOSE, README_URL, TERMS_URL,
    archive_spec, unpack_archive, read_acquisition, _read_bounded)
from .binance_quality import audit_month
from .codec import Invalid, MAX_BYTES, canonical, decode
from .formalization import utc
from .storage import _durable_file


def _descriptor(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def _times(receipt):
    if not utc(receipt['started_at']) <= utc(receipt['retrieved_at']) <= datetime.now(timezone.utc):
        raise Invalid('Invalid retained source receipt times')


def _failed_header(receipt):
    fields = {'schema', 'symbol', 'month', 'url', 'started_at', 'retrieved_at',
              'purpose', 'files', 'status', 'error_type', 'scientific_readiness'}
    if type(receipt) is not dict or set(receipt) != fields:
        raise Invalid('Unsupported failed acquisition receipt fields')
    spec = archive_spec(receipt['symbol'], receipt['month'])
    if (receipt['schema'] != 'binance-month-acquisition/1'
            or receipt['url'] != spec['url'] or receipt['purpose'] != PURPOSE
            or receipt['status'] != 'ACQUISITION_FAILED' or type(receipt['files']) is not dict
            or receipt['error_type'] not in ('Invalid', '_InvalidBar')
            or receipt['scientific_readiness'] is not False):
        raise Invalid('Unsupported failed acquisition receipt; no source authority inferred')
    _times(receipt)
    return spec


def validate_failed_acquisition_bytes(receipt, values):
    spec = _failed_header(receipt)
    names = (spec['name'], spec['name']+'.CHECKSUM', spec['name'].removesuffix('.zip')+'.csv')
    if (type(values) is not dict or set(values) != set(names)
            or any(type(values[name]) is not bytes or len(values[name]) > limit
                   for name, limit in zip(names, (MAX_ARCHIVE, 4096, MAX_CSV)))):
        raise Invalid('Failed source reuse needs its three bounded original files')
    if not receipt['files']:
        return 'UNVERIFIED_LEGACY_FAILURE'
    if receipt['files'] != {name: _descriptor(value) for name, value in values.items()}:
        raise Invalid('Failed receipt does not bind the exact retained source files')
    return 'VERIFIED_FILE_HASHES'


def validate_provider_document_bytes(receipt, values):
    if (type(receipt) is not dict or set(receipt) != {'schema', 'started_at', 'retrieved_at', 'sources'}
            or receipt['schema'] != 'binance-document-snapshot/1' or type(receipt['sources']) is not dict
            or set(receipt['sources']) != {'README.md', 'TERMS_AND_CONDITIONS.md'}
            or type(values) is not dict or set(values) != {'README.md', 'TERMS_AND_CONDITIONS.md'}):
        raise Invalid('Unsupported provider-document receipt')
    _times(receipt)
    for name, url in (('README.md', README_URL), ('TERMS_AND_CONDITIONS.md', TERMS_URL)):
        content, metadata = values[name], receipt['sources'][name]
        if (type(content) is not bytes or len(content) > MAX_BYTES or type(metadata) is not dict
                or set(metadata) != {'url', 'sha256', 'size', 'http'} or metadata['url'] != url
                or {key: metadata[key] for key in ('sha256', 'size')} != _descriptor(content)):
            raise Invalid('Provider-document bytes or declared URL changed')


def _retain_files(broker, token, directory, values, data_class):
    retained = {}
    for name, raw in values.items():
        path = directory/name
        _durable_file(path, raw)
        artifact = broker.call(token, 'add_blob_source', path=str(path), data_class=data_class,
            description='Exact Binance research source bytes; acquisition/quality is not scientific acceptance')
        descriptor = _descriptor(raw)
        if artifact['body']['blob'] != descriptor:
            raise Invalid('Committed source differs from the inspected bytes')
        retained[name] = {**descriptor, 'artifact_ref': artifact['id']}
    return retained


def retain_acquisition(broker, token, source_directory):
    """Append exact files and a separate fresh quality audit, preserving failure receipts.

    Raw source imports may survive an interrupted compound operation. Only the final
    bundle binds a complete audit; even that bundle has no scientific authority.
    """
    broker.call(token, 'status')  # Authenticate operator before reading local paths.
    source = Path(source_directory).resolve()
    receipt_names = [name for name in ('acquisition.json', 'failure.json') if (source/name).is_file()]
    if len(receipt_names) != 1:
        raise Invalid('Retention needs exactly one original success or failure receipt')
    receipt_name = receipt_names[0]
    receipt_raw = _read_bounded(source/receipt_name, MAX_BYTES)
    receipt = decode(receipt_raw)
    if type(receipt) is not dict or not {'symbol', 'month'} <= set(receipt):
        raise Invalid('Missing acquisition identity')
    spec = archive_spec(receipt['symbol'], receipt['month'])
    if receipt_name == 'failure.json':
        _failed_header(receipt)
    names = (spec['name'], spec['name']+'.CHECKSUM', spec['name'].removesuffix('.zip')+'.csv')
    values = {name: _read_bounded(source/name, limit)
              for name, limit in zip(names, (MAX_ARCHIVE, 4096, MAX_CSV))}
    raw = unpack_archive(values[names[0]], values[names[1]], names[0])
    if values[names[2]] != raw:
        raise Invalid('Retained CSV differs from the verified archive')
    binding = 'VERIFIED_FILE_HASHES'
    if receipt_name == 'failure.json':
        binding = validate_failed_acquisition_bytes(receipt, values)
    values[receipt_name] = receipt_raw
    quality = audit_month(raw, spec['symbol'], spec['month'])
    data_class = 'development' if spec['month'] < '2024-01' else 'assessment'
    with tempfile.TemporaryDirectory(prefix='trf-binance-retain-') as temporary:
        stage = Path(temporary)
        # Validate a success receipt against precisely the already captured bytes.
        if receipt_name == 'acquisition.json':
            check = stage/'check'
            check.mkdir()
            for name, content in values.items():
                _durable_file(check/name, content)
            read_acquisition(check)
        files = _retain_files(broker, token, stage, values, data_class)
        quality_bytes = ''.join(canonical(record)+'\n' for record in quality['records']).encode('utf-8')
        quality_file = _retain_files(broker, token, stage, {'row-quality.jsonl': quality_bytes}, data_class)['row-quality.jsonl']
    refs = [item['artifact_ref'] for item in files.values()]+[quality_file['artifact_ref']]
    body = {key: value for key, value in quality.items() if key != 'records'}
    body.update(schema='binance-source-bundle/1', quality_schema=quality['schema'],
        quality_ref=quality_file['artifact_ref'], quality_file=quality_file,
        files=files, original_acquisition_status=receipt['status'],
        original_receipt_ref=files[receipt_name]['artifact_ref'],
        retrieved_at=receipt['retrieved_at'] if binding == 'VERIFIED_FILE_HASHES' else None,
        original_receipt_retrieved_at=receipt['retrieved_at'], receipt_file_binding=binding,
        verified_at=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), source_url=spec['url'],
        checksum='MATCHES_RETAINED_PROVIDER_FILE',
        status='SOURCE_QUALITY_AUDITED', authority='SUPPLIED_SOURCE_NOT_CERTIFIED',
        rights='Separate provider-document snapshot required; no deployment authority')
    return broker.call(token, 'add_source', body=body, data_class=data_class, exposure=refs)


def retain_provider_documents(broker, token, source_directory):
    """Bind exact documentation/terms without granting rights or publishing raw data."""
    broker.call(token, 'status')
    source = Path(source_directory).resolve()
    raw_receipt = _read_bounded(source/'documents.json', MAX_BYTES)
    receipt = decode(raw_receipt)
    values = {name: _read_bounded(source/name, MAX_BYTES) for name in ('README.md', 'TERMS_AND_CONDITIONS.md')}
    validate_provider_document_bytes(receipt, values)
    values['documents.json'] = raw_receipt
    with tempfile.TemporaryDirectory(prefix='trf-binance-docs-') as temporary:
        files = _retain_files(broker, token, Path(temporary), values, 'development')
    return broker.call(token, 'add_source', data_class='development',
        exposure=[item['artifact_ref'] for item in files.values()],
        body={'schema': 'binance-provider-documents/1', 'files': files,
            'retrieved_at': receipt['retrieved_at'], 'scientific_readiness': False,
            'rights': 'Retained provider statements; personal non-production research only; no deployment authority'})
