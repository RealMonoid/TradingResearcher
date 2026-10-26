"""Host-owned normalized data snapshots; structure is not acquisition acceptance."""
from copy import deepcopy
import hashlib

from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .expressions import ReferenceEngine, scalar
from .formalization import fields, utc
from .storage import MAX_BLOB_BYTES, _hash_file


SCHEMA = 'data-snapshot/1'
MAX_ROWS = 500000
MAX_LINE = 1048576
MAX_UTC_SECOND = 253402300799  # 9999-12-31T23:59:59Z, not a latency policy.
PARTITIONS = {
    'development': ('2020-01-01T00:00:00Z', '2024-01-01T00:00:00Z'),
    'assessment': ('2024-01-01T00:00:00Z', '2025-01-01T00:00:00Z'),
    'corroboration': ('2025-01-01T00:00:00Z', '2026-01-01T00:00:00Z'),
}
REMAINING_GATES = ('AVAILABILITY_UNVERIFIED', 'RIGHTS_UNVERIFIED', 'PROVIDER_CHECKSUM_UNVERIFIED',
                   'TRANSFORMATION_UNVERIFIED', 'FEATURE_CERTIFICATION_REQUIRED',
                   'EXPOSURE_AND_SCIENTIFIC_PLAN_REQUIRED')


def window(value):
    fields(value, {'start', 'end', 'instruments'}, 'DATA_GAP')
    start, end = (int(utc(value[key]).timestamp()) for key in ('start', 'end'))
    instruments = strings(value['instruments'], 'instruments')
    if (start < 0 or start >= end or start % 900 or end % 900 or not instruments
            or not set(instruments) <= {'BTCUSDT', 'ETHUSDT'}):
        raise Invalid('The pilot requires a nonempty aligned BTCUSDT/ETHUSDT spot universe')
    if (end-start)//900 * len(instruments) > MAX_ROWS:
        raise Invalid('Declared universe exceeds the snapshot resource envelope')
    return start, end, instruments


def validate_manifest(manifest, now):
    fields(manifest, {'schema', 'profile', 'partition', 'grid_seconds', 'timestamp_unit',
        'universe', 'observation_time_definition', 'provenance', 'availability', 'rights',
        'transformation', 'supersedes'}, 'DATA_GAP')
    if (manifest['schema'] != 'reference-data-request/1' or manifest['profile'] != 'historical-spot-pilot/1'
            or type(manifest['partition']) is not str or manifest['partition'] not in PARTITIONS
            or type(manifest['grid_seconds']) is not int or manifest['grid_seconds'] != 900
            or manifest['timestamp_unit'] != 'seconds'):
        raise Invalid('Unsupported data profile, partition, grid or timestamp unit')
    start, end, instruments = window(manifest['universe'])
    lower, upper = (int(utc(v).timestamp()) for v in PARTITIONS[manifest['partition']])
    if start < lower or end > upper:
        raise Invalid('A data snapshot cannot cross its declared calendar partition')
    text(manifest['observation_time_definition'], 'observation time definition')
    provenance = manifest['provenance']
    fields(provenance, {'provider', 'revision', 'retrieved_at', 'source_uris',
                       'raw_source_refs', 'checksum_evidence_refs'}, 'DATA_GAP')
    for key in ('provider', 'revision'):
        text(provenance[key], key)
    if int(utc(provenance['retrieved_at']).timestamp()) > now:
        raise Invalid('Retrieval time cannot be in the future')
    if not strings(provenance['source_uris'], 'source URIs'):
        raise Invalid('Acquisition needs explicit source locations')
    parents = set(strings(provenance['raw_source_refs'], 'raw source references'))
    if not parents:
        raise Invalid('Acquisition needs retained raw source references')
    parents.update(strings(provenance['checksum_evidence_refs'], 'checksum evidence'))
    for key, choices in (('availability', {'unknown', 'assumed', 'documented'}),
                         ('rights', {'unknown', 'documented'})):
        item = manifest[key]
        fields(item, {'basis', 'description', 'evidence_refs'}, 'DATA_GAP')
        if type(item['basis']) is not str or item['basis'] not in choices:
            raise Invalid('Unsupported provenance assertion')
        text(item['description'], key + ' description')
        refs = strings(item['evidence_refs'], key + ' evidence references')
        if item['basis'] == 'documented' and not refs:
            raise Invalid('Documented assertions need retained evidence references')
        parents.update(refs)
    fields(manifest['transformation'], {'description', 'code_refs'}, 'DATA_GAP')
    text(manifest['transformation']['description'], 'transformation description')
    parents.update(strings(manifest['transformation']['code_refs'], 'transformation code references'))
    parents.update(strings(manifest['supersedes'], 'superseded snapshots'))
    canonical(manifest)
    return start, end, instruments, parents


class DataSnapshots:
    def _owned_row_source(self, identity):
        source = self._artifact(identity)
        if (source['origin'] != 'source' or source['creator'] != 'operator' or type(source['body']) is not dict
                or source['body'].get('schema') != 'blob-source/1'):
            raise Denied('Rows and raw inputs require owned committed blob sources')
        return source

    def _data_inputs(self, catalog_id, row_source_ids, manifest):
        text(catalog_id, 'catalog identity')
        start, end, instruments, parents = validate_manifest(manifest, self._now())
        if not strings(row_source_ids, 'row source IDs'):
            raise Invalid('A snapshot needs at least one row source')
        catalog_source = self._artifact(catalog_id)
        if catalog_source['origin'] != 'source':
            raise Denied('Feature catalogs must be retained source records')
        fields(catalog_source['body'], {'schema', 'features'}, 'DATA_GAP')
        if catalog_source['body']['schema'] != 'feature-catalog/1':
            raise Invalid('Unsupported catalog schema')
        catalog = catalog_source['body']['features']
        ReferenceEngine(catalog, [{'time': start, 'instrument': instruments[0], 'features': {}}])
        if not catalog:
            raise Invalid('A data snapshot needs an explicit nonempty feature catalog')
        sources = [self._owned_row_source(ref) for ref in row_source_ids]
        for ref in manifest['provenance']['raw_source_refs']:
            self._owned_row_source(ref)
        for ref in manifest['supersedes']:
            self._data_snapshot(ref)
        parents.update(row_source_ids)
        parents.add(catalog_id)
        pending, ancestors, exposure = list(parents), {}, set(parents)
        while pending:
            ref = pending.pop()
            if ref in ancestors:
                continue
            artifact = self._artifact(ref)
            if artifact['origin'] != 'source':
                raise Denied('Unreleased work products cannot become raw data inputs')
            if artifact['data_class'] == 'operations':
                raise Denied('Operational sources cannot silently become research data')
            if artifact['data_class'] == 'assessment' and manifest['partition'] == 'development':
                raise Denied('Protected source ancestry cannot be relabeled development')
            ancestors[ref] = artifact
            for parent in set(artifact.get('source_refs', [])) | set(artifact['exposure']):
                exposure.add(parent)
                if self._db.execute('SELECT 1 FROM artifacts WHERE id=?', (parent,)).fetchone():
                    pending.append(parent)
        descriptors = {source['body']['blob']['sha256']: source['body']['blob'] for source in sources}
        if len(descriptors) != len(sources):
            raise Invalid('The same row content cannot be supplied twice')
        if sum(item['size'] for item in descriptors.values()) > MAX_BLOB_BYTES:
            raise Invalid('Snapshot rows exceed the total 512 MiB byte envelope')
        return {'catalog': catalog, 'sources': sources, 'parents': sorted(parents),
                'ancestors': ancestors, 'exposure': sorted(exposure),
                'start': start, 'end': end, 'instruments': instruments}

    def _check_data_blobs(self, inputs):
        identities = {ref for artifact in inputs['ancestors'].values() for ref in artifact.get('blob_refs', [])}
        for identity in identities:
            row = self._db.execute('SELECT size FROM blobs WHERE sha256=?', (identity,)).fetchone()
            if row is None:
                raise Denied('Data ancestry contains an uncommitted blob')
            try:
                actual, size, _ = _hash_file(self._blob_path(identity))
            except OSError as exc:
                raise Conflict('Referenced data bytes are unavailable') from exc
            if (actual, size) != (identity, row[0]):
                raise Conflict('Referenced data bytes are corrupt')

    def _scan_data(self, inputs, selection=None):
        catalog = inputs['catalog']
        coverage = {'expected_rows': (inputs['end']-inputs['start'])//900 * len(inputs['instruments']),
            'observed_rows': 0, 'missing_rows': 0, 'missing_features': {ref: 0 for ref in catalog},
            'null_values': {ref: 0 for ref in catalog}, 'late_samples': {ref: 0 for ref in catalog}}
        previous, selected = None, []
        for source in inputs['sources']:
            descriptor = source['body']['blob']
            checksum, size = hashlib.sha256(), 0
            try:
                stream = self._blob_path(descriptor['sha256']).open('rb')
            except OSError as exc:
                raise Conflict('Row source is unavailable') from exc
            with stream:
                while raw := stream.readline(MAX_LINE+1):
                    size += len(raw)
                    if len(raw) > MAX_LINE or size > descriptor['size']:
                        raise Invalid('A row source exceeds its declared size or line bound')
                    checksum.update(raw)
                    row = decode(raw)
                    fields(row, {'time', 'instrument', 'features'}, 'DATA_GAP')
                    when = integer(row['time'], 'observation time')
                    if (when % 900 or not inputs['start'] <= when < inputs['end']
                            or type(row['instrument']) is not str or row['instrument'] not in inputs['instruments']
                            or type(row['features']) is not dict):
                        raise Invalid('Row lies outside the exact declared grid, universe or schema')
                    key = when, row['instrument']
                    if previous is not None and key <= previous:
                        raise Invalid('Rows must be ordered and unique across all shards')
                    previous = key
                    if not set(row['features']) <= set(catalog):
                        raise Invalid('Row uses an unregistered feature version')
                    for ref, spec in catalog.items():
                        if ref not in row['features']:
                            coverage['missing_features'][ref] += 1
                            continue
                        sample = row['features'][ref]
                        fields(sample, {'value', 'available_at'}, 'DATA_GAP')
                        available = integer(sample['available_at'], 'sample availability')
                        if available > MAX_UTC_SECOND:
                            raise Invalid('Sample availability must be representable UTC seconds; units are never guessed')
                        scalar(spec['type'], spec['unit'], sample['value'], 'DATA_GAP')
                        coverage['null_values'][ref] += sample['value'] is None
                        coverage['late_samples'][ref] += available > when
                    coverage['observed_rows'] += 1
                    if coverage['observed_rows'] > MAX_ROWS:
                        raise Invalid('Snapshot exceeds its row resource bound')
                    if selection is not None:
                        start, end, instruments, limit = selection
                        if start <= when < end and row['instrument'] in instruments:
                            if len(selected) >= limit:
                                raise Invalid('Requested data window exceeds its row bound; no truncation applied')
                            selected.append(row)
            if (checksum.hexdigest(), size) != (descriptor['sha256'], descriptor['size']):
                raise Conflict('Row bytes changed or do not match their committed identity')
        if not coverage['observed_rows']:
            raise Invalid('An empty row snapshot is an explicit data gap')
        coverage['missing_rows'] = coverage['expected_rows'] - coverage['observed_rows']
        return coverage, selected

    def _register_data_snapshot_external(self, token, args):
        with self._mutex:
            actor = self._principal(token)
            if actor['role'] != 'operator':
                raise Denied('Data registration is owned by the host')
            args = decode(canonical(args))
            fields(args, {'catalog_id', 'row_source_ids', 'manifest'}, 'DATA_GAP')
            inputs = self._data_inputs(**args)
        coverage, _ = self._scan_data(inputs)
        with self._transaction():
            actor = self._principal(token)
            if actor['role'] != 'operator':
                raise Denied('Data registration is owned by the host')
            # Immutable descriptors are rebound and all retained ancestors rechecked before commitment.
            inputs = self._data_inputs(**args)
            self._check_data_blobs(inputs)
            body = {'schema': SCHEMA, 'created_at': self._now(), 'manifest': args['manifest'],
                    'catalog_id': args['catalog_id'], 'catalog_hash': digest(inputs['catalog']),
                    'row_source_ids': args['row_source_ids'], 'row_format': 'reference-rows-jsonl/1',
                    'coverage': coverage, 'status': 'STRUCTURE_VERIFIED',
                    'remaining_gates': list(REMAINING_GATES), 'scientific_readiness': False}
            result = self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'source', 'data_class': 'development' if args['manifest']['partition'] == 'development' else 'assessment',
                'body': body, 'source_refs': inputs['parents'], 'exposure': inputs['exposure'],
                'blob_refs': sorted(source['body']['blob']['sha256'] for source in inputs['sources']),
                'authority': 'data_structure_not_scientific_acceptance'})
            self._event(actor['name'], 'data_snapshot_registered', artifact_id=result['id'])
            canonical(result)
            return result

    def _data_snapshot(self, identity):
        snapshot = self._artifact(identity)
        if (snapshot['creator'] != 'controller' or snapshot['origin'] != 'source'
                or type(snapshot['body']) is not dict or snapshot['body'].get('schema') != SCHEMA):
            raise Denied('Expected an owned data snapshot')
        return snapshot

    def _load_reference_data(self, snapshot_id, start, end, instruments, max_rows=100000):
        """Trusted-host seam, not an RPC capability or a scientific execution grant."""
        lower, upper, instruments = window({'start': start, 'end': end, 'instruments': instruments})
        integer(max_rows, 'maximum returned rows', 1)
        if max_rows > 100000:
            raise Invalid('Reference calculation accepts at most 100000 rows')
        with self._mutex:
            snapshot = self._data_snapshot(snapshot_id)
            self._require_usable_dependencies(snapshot_id)
            body = snapshot['body']
            inputs = self._data_inputs(body['catalog_id'], body['row_source_ids'], body['manifest'])
            if (lower < inputs['start'] or upper > inputs['end']
                    or not set(instruments) <= set(inputs['instruments'])):
                raise Denied('Requested window is outside the bound snapshot')
            self._check_data_blobs(inputs)
        coverage, rows = self._scan_data(inputs, (lower, upper, instruments, max_rows))
        if coverage != body['coverage'] or digest(inputs['catalog']) != body['catalog_hash']:
            raise Conflict('Retained data no longer matches its snapshot')
        with self._mutex:self._require_usable_dependencies(snapshot_id)
        return {'data_snapshot_ref': snapshot_id, 'catalog': deepcopy(inputs['catalog']), 'rows': rows,
                'availability': deepcopy(body['manifest']['availability']),
                'remaining_gates': list(body['remaining_gates']), 'scientific_readiness': False}
