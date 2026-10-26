"""Qualified decision-time snapshots from committed Binance sources, without scientific authority."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

from .binance_archive import archive_spec, unpack_archive, MAX_ARCHIVE, MAX_CSV, validate_acquisition_bytes
from .binance_ingest import validate_failed_acquisition_bytes, validate_provider_document_bytes
from .binance_quality import quality_reference_rows
from .codec import Invalid, MAX_BYTES, canonical, decode, digest, integer, strings
from .data import PARTITIONS, window
from .errors import Conflict, Denied
from .formalization import utc
from .storage import MAX_BLOB_BYTES, _durable_file
from .certification import _runtime_identity, _runtime_path_allowed


_BOUND_SNAPSHOT = None
NORMALIZATION_TIMEOUT = 600
BOOTSTRAP = 'import sys;sys.path.insert(0,sys.argv[1]);from trading_researcher.binance_normalize import _bound_entry;_bound_entry(sys.argv[2],sys.argv[3])'


def _environment(expected):
    isolation = {'isolated': sys.flags.isolated, 'no_site': sys.flags.no_site,
                 'ignore_environment': sys.flags.ignore_environment, 'no_bytecode_writes': int(sys.dont_write_bytecode)}
    if isolation != {'isolated': 1, 'no_site': 1, 'ignore_environment': 1, 'no_bytecode_writes': 1}:
        raise Invalid('Normalization requires fresh isolated Python without site packages or cached bytecode')
    root, base = Path(__file__).parent.resolve(), Path(sys.base_prefix).resolve()
    libraries = {}
    for name, module in tuple(sys.modules.items()):
        path = getattr(module, '__file__', None)
        if not path:
            continue
        path = Path(path).resolve()
        if path.parent == root and path.name in expected:
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected[path.name]:
                raise Conflict('Imported normalization package changed')
        elif _runtime_path_allowed(path) and name.split('.')[0] in sys.stdlib_module_names:
            libraries[path.relative_to(base).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            raise Invalid('Imported module lies outside the bound package/runtime')
    return {'identity': _runtime_identity(), 'isolation': isolation, 'standard_library': dict(sorted(libraries.items()))}


def _run_child(command, directory, timeout=NORMALIZATION_TIMEOUT):
    output, errors = directory/'child-output.json', directory/'child-errors.txt'
    with output.open('xb') as stdout, errors.open('xb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        try:
            deadline = time.monotonic()+timeout
            while process.poll() is None:
                if time.monotonic() >= deadline or output.stat().st_size > MAX_BYTES or errors.stat().st_size > 8192:
                    raise Invalid('Normalization child exceeded its time/output envelope')
                try:
                    process.wait(timeout=0.2)
                except subprocess.TimeoutExpired:
                    pass
        except BaseException:
            process.kill()
            process.wait()
            raise
    if output.stat().st_size > MAX_BYTES or errors.stat().st_size > 8192:
        raise Invalid('Normalization child output exceeds its envelope')
    if process.returncode != 0:
        raise Invalid('Normalization child failed: '+errors.read_text(encoding='utf-8',errors='replace'))
    return decode(output.read_bytes())


def normalize_retained_partition(directory, source_bundle_refs, provider_documents_ref, *, partition, universe, delay_seconds):
    """Exclusive operator utility. The target registry must not be open elsewhere."""
    directory = Path(directory).resolve()
    if not (directory/'registry.sqlite3').is_file() or not (directory/'operator.key').is_file():
        raise Invalid('Normalization needs an existing owned registry and its operator credential')
    request = {'directory': str(directory), 'source_bundle_refs': source_bundle_refs,
        'provider_documents_ref': provider_documents_ref, 'partition': partition,
        'universe': universe, 'delay_seconds': delay_seconds}
    request_bytes = canonical(request).encode('utf-8')
    bundle = {path.name: path.read_bytes() for path in sorted(Path(__file__).parent.glob('*.py'))}
    expected = {name: hashlib.sha256(raw).hexdigest() for name, raw in bundle.items()}
    with tempfile.TemporaryDirectory(prefix='trf-normalization-execution-') as temporary:
        root = Path(temporary)
        package = root/'trading_researcher'
        package.mkdir()
        for name, raw in bundle.items():
            _durable_file(package/name, raw)
        _durable_file(root/'request.json', request_bytes)
        _durable_file(root/'source-manifest.json', canonical(expected).encode('utf-8'))
        result = _run_child([sys.executable, '-I', '-S', '-B', '-c', BOOTSTRAP, str(root),
                             str(root/'request.json'), str(root/'source-manifest.json')], root)
        if {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in package.glob('*.py')} != expected:
            raise Conflict('Bound normalization source snapshot changed during execution')
        code = result['code_snapshot']['body']
        if (code.get('execution_binding') != 'FRESH_ISOLATED_SOURCE_SNAPSHOT'
                or {name: item['sha256'] for name, item in code['files'].items()} != expected
                or code['environment']['identity'] != _runtime_identity()):
            raise Conflict('Returned normalization source/runtime binding differs from the launched snapshot')
        for name, checksum in code['environment']['standard_library'].items():
            path = Path(sys.base_prefix)/name
            if not _runtime_path_allowed(path) or hashlib.sha256(path.read_bytes()).hexdigest() != checksum:
                raise Conflict('Normalization runtime dependency changed')
        return result


def _bound_entry(request_path, manifest_path):
    global _BOUND_SNAPSHOT
    try:
        request = decode(Path(request_path).read_bytes())
        _BOUND_SNAPSHOT = decode(Path(manifest_path).read_bytes())
        if {path.name: value for path, value in _code_hashes().items()} != _BOUND_SNAPSHOT:
            raise Conflict('Normalization snapshot does not match the parent manifest')
        if list(Path(__file__).parent.glob('**/*.pyc')):
            raise Invalid('Bound snapshot must not contain cached bytecode')
        _environment(_BOUND_SNAPSHOT)
        from .coordination import Broker
        broker = Broker(request.pop('directory'))
        try:
            result = normalize_partition(broker, broker.admin_token, **request)
            print(canonical(result), flush=True)
        finally:
            broker.close()
    except Exception as exc:
        sys.stderr.write(type(exc).__name__+': '+str(exc))
        raise SystemExit(2)


def _source(broker, token, identity, schema):
    artifact = broker.call(token, 'get_artifact', artifact_id=identity)
    if (artifact['origin'] != 'source' or artifact['creator'] != 'operator'
            or type(artifact['body']) is not dict or artifact['body'].get('schema') != schema):
        raise Denied('Normalization requires owned source records of the declared schema')
    return artifact


def _check_ancestry(broker, roots, partition):
    # Same known-ancestry boundary as DataSnapshots, applied before reading raw bytes.
    pending, seen = list(roots), set()
    with broker._mutex:
        while pending:
            identity = pending.pop()
            if identity in seen:
                continue
            artifact = broker._artifact(identity)
            if (artifact['origin'] != 'source' or artifact['data_class'] == 'operations'
                    or partition == 'development' and artifact['data_class'] == 'assessment'):
                raise Denied('Protected or unreleased ancestry cannot enter this data partition')
            seen.add(identity)
            for parent in set(artifact.get('source_refs', [])) | set(artifact['exposure']):
                if broker._db.execute('SELECT 1 FROM artifacts WHERE id=?', (parent,)).fetchone():
                    pending.append(parent)


def _blob(broker, token, descriptor, limit):
    if type(descriptor) is not dict or set(descriptor) != {'sha256', 'size', 'artifact_ref'}:
        raise Invalid('Retained file needs an exact descriptor and owned artifact reference')
    integer(descriptor['size'], 'retained byte size')
    if descriptor['size'] > limit:
        raise Invalid('Retained input exceeds its normalization resource envelope')
    source = _source(broker, token, descriptor['artifact_ref'], 'blob-source/1')
    if source['body']['blob'] != {key: descriptor[key] for key in ('sha256', 'size')}:
        raise Invalid('Retained file descriptor differs from its owned source')
    with broker._mutex:
        return broker._read_blob_bytes(descriptor['sha256'])


def _required_sources(start, end, instruments):
    expected, outside = set(), set()
    first = datetime.fromtimestamp(start-900, timezone.utc)
    last = datetime.fromtimestamp(end-1800, timezone.utc)
    year, month = first.year, first.month
    while (year, month) <= (last.year, last.month):
        name = f'{year:04}-{month:02}'
        if 2020 <= year <= 2025:
            expected.update((symbol, name) for symbol in instruments)
        else:
            outside.add(name)
        year, month = year+(month == 12), month % 12+1
    return expected, sorted(outside)


def _documents(broker, token, artifact):
    body = artifact['body']
    if body.get('scientific_readiness') is not False or type(body.get('files')) is not dict:
        raise Invalid('Unsupported provider documentation assertion')
    files = body['files']
    if set(files) != {'documents.json', 'README.md', 'TERMS_AND_CONDITIONS.md'}:
        raise Invalid('Missing exact provider documentation sources')
    if not {item['artifact_ref'] for item in files.values()} <= set(artifact['exposure']):
        raise Invalid('Provider document ancestry is incomplete')
    values = {name: _blob(broker, token, desc, MAX_BYTES) for name, desc in files.items()}
    receipt = decode(values['documents.json'])
    validate_provider_document_bytes(receipt, {name: values[name] for name in ('README.md', 'TERMS_AND_CONDITIONS.md')})
    if (type(receipt) is not dict or receipt.get('schema') != 'binance-document-snapshot/1'
            or receipt.get('retrieved_at') != body.get('retrieved_at') or type(receipt.get('sources')) is not dict):
        raise Invalid('Provider document receipt differs from its bundle')


def _month(broker, token, artifact, delay_seconds):
    body = artifact['body']
    spec = archive_spec(body['symbol'], body['source_month'])
    files = body.get('files')
    names = (spec['name'], spec['name']+'.CHECKSUM', spec['name'].removesuffix('.zip')+'.csv')
    receipt_name = 'acquisition.json' if body.get('original_acquisition_status') == 'SOURCE_INTEGRITY_CHECKED' else 'failure.json'
    if (type(files) is not dict or set(files) != {*names, receipt_name}
            or body.get('status') != 'SOURCE_QUALITY_AUDITED' or body.get('scientific_readiness') is not False
            or body.get('source_url') != spec['url'] or body.get('quality_schema') != 'binance-row-quality/1'):
        raise Invalid('Incomplete or unsupported retained monthly source bundle')
    quality_descriptor = body.get('quality_file')
    if (type(quality_descriptor) is not dict or quality_descriptor.get('artifact_ref') != body.get('quality_ref')
            or body.get('original_receipt_ref') != files[receipt_name]['artifact_ref']
            or not {item['artifact_ref'] for item in files.values()} | {body['quality_ref']} <= set(artifact['exposure'])):
        raise Invalid('Monthly source ancestry is incomplete')
    values = {name: _blob(broker, token, files[name], limit)
              for name, limit in zip((*names, receipt_name), (MAX_ARCHIVE, 4096, MAX_CSV, MAX_BYTES))}
    raw = unpack_archive(values[names[0]], values[names[1]], names[0])
    if raw != values[names[2]] or hashlib.sha256(raw).hexdigest() != body.get('source_sha256'):
        raise Invalid('Monthly CSV no longer matches its verified archive')
    normalized = quality_reference_rows(raw, spec['symbol'], spec['month'], delay_seconds=delay_seconds)
    quality = normalized['quality']
    expected = ''.join(canonical(record)+'\n' for record in quality['records']).encode('utf-8')
    if (_blob(broker, token, quality_descriptor, MAX_CSV) != expected
            or quality['coverage'] != body.get('coverage') or quality['timestamp_unit'] != body.get('timestamp_unit')):
        raise Invalid('Retained row audit differs from fresh source normalization')
    receipt = decode(values[receipt_name])
    if receipt_name == 'acquisition.json':
        validate_acquisition_bytes(receipt, {name: values[name] for name in names})
        binding = 'VERIFIED_FILE_HASHES'
    else:
        binding = validate_failed_acquisition_bytes(receipt, {name: values[name] for name in names})
    if (type(receipt) is not dict or receipt.get('status') != body.get('original_acquisition_status')
            or receipt.get('retrieved_at') != body.get('original_receipt_retrieved_at')):
        raise Invalid('Retained acquisition receipt differs from its source bundle')
    if body.get('receipt_file_binding') != binding or body.get('retrieved_at') != (receipt['retrieved_at'] if binding == 'VERIFIED_FILE_HASHES' else None):
        raise Invalid('Acquisition time qualification changed')
    return normalized


def _code_hashes():
    return {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(Path(__file__).parent.glob('*.py'))}


def _retain_code(broker, token, expected):
    if _code_hashes() != expected:
        raise Conflict('Processing source checkout changed during normalization')
    files = {}
    for path, checksum in expected.items():
        source = broker.call(token, 'add_blob_source', path=str(path.resolve()), data_class='development',
            description='Normalization source checkout; execution identity and transformation are not certified')
        if source['body']['blob']['sha256'] != checksum:
            raise Conflict('Processing source changed during retention')
        files[path.name] = {'sha256': checksum, 'artifact_ref': source['id']}
    return broker.call(token, 'add_source', data_class='development', exposure=[item['artifact_ref'] for item in files.values()],
        body={'schema': 'binance-normalization-code/1', 'files': files, 'python_version': sys.version,
              'execution_binding': 'FRESH_ISOLATED_SOURCE_SNAPSHOT',
              'environment': _environment({path.name: value for path, value in expected.items()}),
              'scientific_transformation_certified': False})


def normalize_partition(broker, token, source_bundle_refs, provider_documents_ref, *, partition, universe, delay_seconds):
    """No default latency, no absent-row filling, no cross-partition evidence grant."""
    broker.call(token, 'status')
    source_bundle_refs = strings(source_bundle_refs, 'monthly source bundles')
    integer(delay_seconds, 'explicit assumed delay')
    start, end, instruments = window(universe)
    if type(partition) is not str or partition not in PARTITIONS:
        raise Invalid('Unknown research partition')
    lower, upper = (int(utc(value).timestamp()) for value in PARTITIONS[partition])
    if start < lower or end > upper:
        raise Invalid('Normalization universe crosses its declared partition')
    required, outside = _required_sources(start, end, instruments)
    sources = {}
    for identity in source_bundle_refs:
        artifact = _source(broker, token, identity, 'binance-source-bundle/1')
        body = artifact['body']
        spec = archive_spec(body.get('symbol'), body.get('source_month'))
        key = spec['symbol'], spec['month']
        if key in sources:
            raise Invalid('Duplicate symbol/month source bundles are not a revision policy')
        if artifact['data_class'] != ('development' if spec['month'] < '2024-01' else 'assessment'):
            raise Denied('Monthly source class does not match its declared scope')
        sources[key] = artifact
    if set(sources) != required:
        raise Invalid('Required monthly sources are missing or irrelevant sources were supplied')
    if not sources:
        raise Invalid('NO_OBSERVATIONS: requested decisions have no source within the adopted profile')
    documents = _source(broker, token, provider_documents_ref, 'binance-provider-documents/1')
    _check_ancestry(broker, [*source_bundle_refs, provider_documents_ref], partition)
    if _BOUND_SNAPSHOT is None or {path.name: value for path, value in _code_hashes().items()} != _BOUND_SNAPSHOT:
        raise Invalid('Use normalize_retained_partition to execute a fresh bound source snapshot')
    _environment(_BOUND_SNAPSHOT)
    _documents(broker, token, documents)
    code_before = _code_hashes()
    catalog, counts, selected_invalid, size, row_count = {}, [], 0, 0, 0
    raw_refs, checksum_refs, source_uris = [], [], []
    data_class = 'development' if partition == 'development' else 'assessment'
    with tempfile.TemporaryDirectory(prefix='trf-binance-normalize-') as temporary:
        path = Path(temporary)/'normalized-rows.jsonl'
        with path.open('xb') as stream:
            for month in sorted({key[1] for key in sources}):
                month_rows = []
                for symbol in sorted(instruments):
                    source = sources[symbol, month]
                    normalized = _month(broker, token, source, delay_seconds)
                    catalog.update(normalized['catalog'])
                    selection = {'symbol': symbol, 'month': month, 'selected': 0, 'before': 0, 'after': 0}
                    for row, quality in zip(normalized['rows'], normalized['quality']['records'], strict=True):
                        if row['time'] < start:
                            selection['before'] += 1
                        elif row['time'] >= end:
                            selection['after'] += 1
                        else:
                            month_rows.append(row)
                            selection['selected'] += 1
                            selected_invalid += quality['status'] == 'INVALID_BAR'
                    counts.append(selection)
                    spec = archive_spec(symbol, month)
                    files = source['body']['files']
                    raw_refs.append(files[spec['name'].removesuffix('.zip')+'.csv']['artifact_ref'])
                    checksum_refs.append(files[spec['name']+'.CHECKSUM']['artifact_ref'])
                    source_uris.append(spec['url'])
                for row in sorted(month_rows, key=lambda value: (value['time'], value['instrument'])):
                    raw = (canonical(row)+'\n').encode('utf-8')
                    size += len(raw)
                    if size > MAX_BLOB_BYTES:
                        raise Invalid('Normalized partition exceeds its 512 MiB byte envelope')
                    stream.write(raw)
                    row_count += 1
            stream.flush()
            os.fsync(stream.fileno())
        if not row_count:
            raise Invalid('NO_OBSERVATIONS: no present source row falls in the requested universe')
        code = _retain_code(broker, token, code_before)
        rows = broker.call(token, 'add_blob_source', path=str(path), data_class=data_class,
            description='Exact decision-time rows; assumed latency and unusable-source nulls; not scientific acceptance')
    catalog_source = broker.call(token, 'add_source', data_class=data_class,
        body={'schema': 'feature-catalog/1', 'features': catalog})
    retrieved_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    normalization = broker.call(token, 'add_source', data_class=data_class,
        exposure=[*sorted(source_bundle_refs), provider_documents_ref, code['id'], rows['id']],
        body={'schema': 'binance-normalization/1', 'status': 'NORMALIZED_ROWS_RETAINED',
            'partition': partition, 'universe': universe, 'delay_seconds': delay_seconds,
            'availability_basis': 'assumed', 'historical_publication_time': None,
            'local_copy_retrieved_at': retrieved_at, 'source_bundle_refs': sorted(source_bundle_refs),
            'provider_documents_ref': provider_documents_ref, 'code_snapshot_ref': code['id'], 'row_source_ref': rows['id'],
            'selection_counts': sorted(counts, key=lambda value: (value['symbol'], value['month'])),
            'selected_invalid_rows': selected_invalid, 'outside_profile_source_months': outside,
            'scientific_readiness': False,
            'qualification': 'Decision-time containers preserve source ancestry and prior exposure; outcome label-boundary eligibility and scientific missingness are separate. Retrieval time describes current verified local copies, not historical publication or original network acquisition.'})
    manifest = {'schema': 'reference-data-request/1', 'profile': 'historical-spot-pilot/1',
        'partition': partition, 'grid_seconds': 900, 'timestamp_unit': 'seconds', 'universe': universe,
        'observation_time_definition': 'Exclusive complete-bar end; for invalid keyed bars only the expected grid boundary, with all values null.',
        'provenance': {'provider': 'Binance public archives, verified retained local copies',
            'revision': 'retained-bundles/'+digest(sorted(source_bundle_refs)), 'retrieved_at': retrieved_at,
            'source_uris': source_uris, 'raw_source_refs': raw_refs, 'checksum_evidence_refs': checksum_refs},
        'availability': {'basis': 'assumed', 'description': f'Explicit {delay_seconds}-second delay after expected bar end; historical publication unknown. Local-copy retrieval time is separate from original receipt times, including legacy unbound times.', 'evidence_refs': [normalization['id']]},
        'rights': {'basis': 'documented', 'description': 'Retained provider statements for personal non-production research; no deployment or redistribution authority.', 'evidence_refs': [provider_documents_ref]},
        'transformation': {'description': 'Fresh isolated source snapshot: complete-bar quality replay and exact exclusive-end selection; invalid present bars all-null, absent bars unfilled. Execution binding does not certify scientific data or feature meaning.', 'code_refs': [code['id']]},
        'supersedes': []}
    if _code_hashes() != code_before:
        raise Conflict('Bound transformation source changed before data commitment')
    snapshot = broker.call(token, 'register_data_snapshot', catalog_id=catalog_source['id'], row_source_ids=[rows['id']], manifest=manifest)
    return {'snapshot': snapshot, 'normalization': normalization, 'code_snapshot': code}
