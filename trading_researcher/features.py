"""Host-owned raw-feature conformance; no historical-availability or scientific authority."""
from copy import deepcopy
import base64
import csv
import hashlib
import io
import os
from pathlib import Path
import sys
import tempfile
import uuid
import zipfile

from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .certification import _environment_current
from .storage import _durable_file


ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'binance-raw-features/1'
PINS = {
    'docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md': 'e8513ced048dd3c60f30490736e666cadf4d3da0929002b4923a8d70ac31a76d',
    'tests/fixtures/reference_binance_cases.json': 'a951d1a6cff1e459afb0588f2286c66c9b9533db375c6dc8a27515a4244ada00',
    'tests/fixtures/reference_binance_quality_cases.json': 'c71da72c766f01a055590b65bf9ddcc84add0bde15a6b114d79007217a34c67a',
    'tests/fixtures/reference_binance_partition_cases.json': '7921f6119c8f23ef4bb0c366624d1a4fda01baf98dd5531b6733e6c2ed373ae0',
    'tests/fixtures/reference_feature_cases.json': '57a7b923aa975cfa6fe4b588e162364449f0ccaed033dc3cd2730c49e6021081',
    'tests/fixtures/reference_feature_expectations.md': 'dfe226e663270702473c5efc16bf008f6bf30ce670ed619e63693539dd3794ee',
}
CHECKS = {'archive_cases': 43, 'quality_cases': 32, 'partition_cases': 22, 'definition_cases': 18,
          'projection_cases': 10}
SCOPE = {'authority': 'raw_measurement_implementation_conformance',
    'not_certified': ['historical_publication_time', 'source_truth', 'scientific_missingness_policy',
        'semantic_equivalence_of_hypotheses', 'scientific_evidence', 'calibration', 'capital_authority', 'OS_sandbox']}
NORMALIZATION_FIELDS = {'schema', 'status', 'partition', 'universe', 'delay_seconds',
    'availability_basis', 'historical_publication_time', 'local_copy_retrieved_at', 'source_bundle_refs',
    'provider_documents_ref', 'code_snapshot_ref', 'row_source_ref', 'selection_counts',
    'selected_invalid_rows', 'outside_profile_source_months', 'scientific_readiness', 'qualification'}


def footprint(bundle):
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in sorted(bundle.items())}


def read_bundle():
    names = sorted({*PINS, *(path.relative_to(ROOT).as_posix() for path in (ROOT/'trading_researcher').glob('*.py'))})
    return {name: (ROOT/name).read_bytes() for name in names}


def valid_names(names):
    names = set(names)
    return (set(PINS) <= names and len(names) <= 128
        and {'trading_researcher/__init__.py', 'trading_researcher/features.py',
             'trading_researcher/coordination.py', 'trading_researcher/binance_normalize.py'} <= names
        and all(name in PINS or (name.startswith('trading_researcher/')
            and name.count('/') == 1 and Path(name).suffix == '.py'
            and Path(name).stem.isidentifier()) for name in names))


def pins_match(values):
    return valid_names(values) and all(values.get(name) == value for name, value in PINS.items())


def definitions(instruments):
    """Versioned field projection of the already implemented provider format."""
    result = []
    columns = {'open': 1, 'high': 2, 'low': 3, 'close': 4, 'volume': 5,
               'quote_volume': 7, 'trades': 8, 'taker_base_volume': 9, 'taker_quote_volume': 10}
    for instrument in sorted(instruments):
        if instrument not in ('BTCUSDT', 'ETHUSDT'):
            raise Invalid('Raw feature profile requires adopted spot instruments')
        base = instrument.removesuffix('USDT')
        for name, column in columns.items():
            price = name in ('open', 'high', 'low', 'close')
            unit = 'USDT/'+base if price else ('count' if name == 'trades' else
                'USDT' if name in ('quote_volume', 'taker_quote_volume') else base)
            result.append({'schema': 'raw-binance-feature-definition/1',
                'feature_ref': instrument+'.'+name+'@binance-spot-15m-v1', 'instrument': instrument,
                'source_field': name, 'csv_column_index': column, 'type': 'real', 'unit': unit,
                'source_scalar': 'positive_decimal' if price else 'nonnegative_integer' if name == 'trades' else 'nonnegative_decimal',
                'transformation': 'EXACT_DECIMAL_FIELD_PROJECTION',
                'time': {'grid_seconds': 900, 'row_anchor': 'EXPECTED_EXCLUSIVE_BAR_END',
                    'source_open_column': 0, 'source_close_column': 6,
                    'timestamp_unit_rule': 'milliseconds_before_2025_microseconds_from_2025'},
                'missingness': {'invalid_keyed_bar': 'NULL_ALL_SYMBOL_FIELDS', 'absent_bar': 'NO_ROW',
                    'other_instrument_fields': 'ABSENT'},
                'availability': {'basis': 'assumed', 'rule': 'row_time + delay_seconds',
                    'parameter': 'EXPLICIT_NONNEGATIVE_INTEGER_SECONDS_NO_DEFAULT', 'historical_publication_time': None},
                'fitted_state': None})
    return result


def binding(broker, snapshot_id):
    snapshot = broker._data_snapshot(snapshot_id)
    broker._require_usable_dependencies(snapshot_id)
    body = snapshot['body']
    inputs = broker._data_inputs(body['catalog_id'], body['row_source_ids'], body['manifest'])
    broker._check_data_blobs(inputs)
    refs = body['manifest']['availability']['evidence_refs']
    if len(refs) != 1:
        raise Invalid('Raw feature certification needs one exact normalization record')
    normalization = broker._artifact(refs[0])
    value = normalization['body']
    if (normalization['creator'] != 'operator' or normalization['origin'] != 'source'
            or type(value) is not dict or value.get('schema') != 'binance-normalization/1'
            or set(value) != NORMALIZATION_FIELDS
            or value.get('status') != 'NORMALIZED_ROWS_RETAINED'
            or value.get('scientific_readiness') is not False
            or value.get('availability_basis') != 'assumed'
            or value.get('historical_publication_time') is not None
            or body['manifest']['availability']['basis'] != 'assumed'
            or body['row_source_ids'] != [value.get('row_source_ref')]
            or body['manifest']['universe'] != value.get('universe')
            or body['manifest']['partition'] != value.get('partition')
            or body['manifest']['provenance']['retrieved_at'] != value.get('local_copy_retrieved_at')
            or body['manifest']['transformation']['code_refs'] != [value.get('code_snapshot_ref')]
            or body['manifest']['rights']['evidence_refs'] != [value.get('provider_documents_ref')]):
        raise Invalid('Snapshot and normalization binding differ or are unsupported')
    integer(value['delay_seconds'], 'assumed delay')
    strings(value['source_bundle_refs'], 'source bundle references')
    text(value['provider_documents_ref'], 'provider documents reference')
    request = {key: deepcopy(value[key]) for key in ('source_bundle_refs', 'provider_documents_ref',
        'partition', 'universe', 'delay_seconds')}
    if not set([*request['source_bundle_refs'], request['provider_documents_ref']]) <= set(inputs['ancestors']):
        raise Invalid('Normalized data omits its declared source ancestry')
    return {'snapshot': snapshot, 'normalization': normalization,
            'row_blobs': [source['body']['blob'] for source in inputs['sources']],
            'catalog': inputs['catalog'], 'request': request,
            'closure': sorted(inputs['ancestors']), 'exposure': inputs['exposure']}


def replay_equal(original, replayed):
    """Ignore only newly generated replay IDs and the replay's local-copy read time."""
    left, right = original['snapshot']['body'], replayed['snapshot']['body']
    a, b = deepcopy(left['manifest']), deepcopy(right['manifest'])
    for manifest in (a, b):
        manifest['provenance'].pop('retrieved_at')
        manifest['availability']['evidence_refs'] = []
        manifest['transformation']['code_refs'] = []
    x, y = deepcopy(original['normalization']['body']), deepcopy(replayed['normalization']['body'])
    for record in (x, y):
        for key in ('local_copy_retrieved_at', 'code_snapshot_ref', 'row_source_ref'):
            record.pop(key)
    if digest([original['row_blobs'], original['catalog'], left['coverage'], left['catalog_hash'],
               a, x, original['request']]) != digest([replayed['row_blobs'], replayed['catalog'],
               right['coverage'], right['catalog_hash'], b, y, replayed['request']]):
        raise Conflict('Raw source replay differs from the supplied data snapshot')
    return replay_summary(original)


def replay_summary(original):
    body = original['snapshot']['body']
    normalization = original['normalization']['body']
    return {'row_blobs': original['row_blobs'], 'catalog_hash': body['catalog_hash'],
        'coverage': body['coverage'], 'normalization_id': original['normalization']['id'],
        'original_closure_hash': digest(original['closure']), 'original_exposure_hash': digest(original['exposure']),
        'selection_counts': normalization['selection_counts'], 'selected_invalid_rows': normalization['selected_invalid_rows'],
        'outside_profile_source_months': normalization['outside_profile_source_months']}


REPORT_FIELDS = {'status', 'reason', 'checks', 'replay', 'definitions', 'binding_hash', 'environment', 'footprint'}


def validate_report(report, original, bundle):
    """Host recomputation of report fields, without executing a second transformation."""
    require(type(report) is dict and set(report) == REPORT_FIELDS)
    require(report['status'] == 'CERTIFIED' and report['reason'] == 'FIXED_CASES_AND_FULL_SOURCE_REPLAY_PASSED')
    require(digest(report['checks']) == digest(CHECKS) and report['binding_hash'] == digest(original))
    require(report['footprint'] == footprint(bundle) and pins_match(report['footprint']))
    fixed = decode(bundle['tests/fixtures/reference_feature_cases.json'])['definitions']
    expected = [entry for entry in fixed if entry['instrument'] in original['request']['universe']['instruments']]
    require(digest(report['definitions']) == digest(expected)
        and digest(report['replay']) == digest(replay_summary(original)))
    require(_environment_current(report['environment']))


def gap_report(bundle, reason, failure_type=None):
    return {'status': 'CERTIFICATION_GAP', 'reason': reason, 'failure_type': failure_type,
        'checks': {}, 'replay': None, 'environment': None, 'footprint': footprint(bundle)}


def require(condition):
    if not condition:
        raise Invalid('Independent feature expectation mismatch')


def expect_rejected(callback):
    try:
        callback()
    except (Invalid, Denied, Conflict):
        return
    raise Invalid('Independent rejection case was accepted')


def fixture_sources(broker, root, sources):
    from .binance_archive import acquire_month, archive_spec, capture_provider_docs
    from .binance_ingest import retain_acquisition, retain_provider_documents
    docs = root/'documents'
    capture_provider_docs(docs, downloader=lambda url, limit: (b'Synthetic independent fixture\n', {}))
    document_id = retain_provider_documents(broker, broker.admin_token, docs)['id']
    identities = []
    for index, source in enumerate(sources):
        spec = archive_spec(source['symbol'], source['month'])
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(spec['name'].removesuffix('.zip')+'.csv', source['raw_csv'].encode())
        payload = output.getvalue()
        checksum = (hashlib.sha256(payload).hexdigest()+'  '+spec['name']+'\n').encode()
        directory = root/str(index)
        try:
            acquire_month(source['symbol'], source['month'], directory,
                downloader=lambda url, limit: (checksum if url.endswith('.CHECKSUM') else payload, {}))
        except Invalid:
            pass  # The retained failure still undergoes the independent quality audit.
        identities.append(retain_acquisition(broker, broker.admin_token, directory)['id'])
    return identities, document_id


def fixed_checks():
    from .binance_archive import availability_scenario, parse_month, unpack_archive
    from .binance_quality import audit_month, quality_reference_rows
    from .binance_normalize import normalize_partition
    from .coordination import Broker
    checks = dict.fromkeys(CHECKS, 0)
    fixtures = ROOT/'tests/fixtures'
    fixture = decode((fixtures/'reference_binance_cases.json').read_bytes())
    for case in fixture['cases']:
        expected = case['expected']
        if case['kind'] == 'availability_scenario':
            require(availability_scenario(case['bar_end_time'], case['delay_seconds']) == expected)
        else:
            if case['kind'] == 'parse_csv':
                output = io.StringIO(newline='')
                csv.writer(output, lineterminator='\n').writerows(case['csv_rows'])
                callback = lambda: parse_month(output.getvalue().encode(), case['symbol'], case['month'])
            else:
                blob = fixture['archives'][case['archive_ref']]
                payload = base64.b64decode(blob['bytes_base64'])
                require(hashlib.sha256(payload).hexdigest() == blob['sha256'])
                checksum = case.get('checksum_text', blob['sha256']+'  '+case['archive_name']+'\n').encode()
                callback = lambda: unpack_archive(payload, checksum, case['archive_name'])
            if not expected['accepted']:
                expect_rejected(callback)
            else:
                actual = callback()
                if case['kind'] == 'parse_csv':
                    require(actual['bars'] == expected['bars'] and actual['timestamp_unit'] == case['timestamp_unit']
                        and actual['availability'] == 'UNKNOWN_HISTORICAL_PUBLICATION')
                elif case['kind'] == 'read_archive':
                    require(actual.decode() == expected['csv_text'])
                else:
                    require(hashlib.sha256(payload).hexdigest() == expected['sha256'])
        checks['archive_cases'] += 1
    for case in decode((fixtures/'reference_binance_quality_cases.json').read_bytes())['cases']:
        expected, args = case['expected'], (case['raw_csv'].encode(), case['symbol'], case['month'])
        if not expected['accepted']:
            expect_rejected(lambda: audit_month(*args))
            expect_rejected(lambda: quality_reference_rows(*args, delay_seconds=case['delay_seconds']))
        else:
            actual = audit_month(*args)
            require(all(actual[key] == expected[key] for key in ('schema', 'source_sha256', 'records',
                'coverage', 'expected_end_definition', 'scientific_readiness')))
            normalized = quality_reference_rows(*args, delay_seconds=case['delay_seconds'])
            require(normalized['rows'] == expected['reference_rows']
                and normalized['availability']['basis'] == expected['reference_availability_basis']
                and normalized['availability']['historical_publication_time'] is None
                and normalized['scientific_readiness'] is False)
            if expected['strict_parser_accepted']:
                require(parse_month(*args)['bars'] == [record['bar'] for record in actual['records']])
            else:
                expect_rejected(lambda: parse_month(*args))
        checks['quality_cases'] += 1
    feature_cases = decode((fixtures/'reference_feature_cases.json').read_bytes())
    cases = [(case, 'partition_cases') for case in decode((fixtures/'reference_binance_partition_cases.json').read_bytes())['cases']]
    cases += [(case, 'projection_cases') for case in feature_cases['cases'] if case['kind'] == 'raw_projection']
    for case, counter in cases:
        with tempfile.TemporaryDirectory(prefix='trf-feature-case-') as temporary:
            root = Path(temporary)
            broker = Broker(root/'registry')
            try:
                def execute():
                    refs, documents = fixture_sources(broker, root, case['sources'])
                    return normalize_partition(broker, broker.admin_token, refs, documents,
                        partition=case['partition'], universe=case['universe'], delay_seconds=case['delay_seconds'])
                expected = case['expected']
                if not expected.get('accepted', expected.get('certificate_allowed')):
                    expect_rejected(execute)
                else:
                    actual = execute()
                    universe = case['universe']
                    loaded = broker._load_reference_data(actual['snapshot']['id'],
                        universe['start'], universe['end'], universe['instruments'])
                    require(loaded['rows'] == expected['rows'])
                    if counter == 'partition_cases':
                        require(actual['normalization']['body']['selection_counts'] == expected['selection_counts'])
                    else:
                        coverage = actual['snapshot']['body']['coverage']
                        require([item['feature_ref'] for item in definitions(universe['instruments'])] == expected['definition_refs'])
                        require(coverage['expected_rows'] == expected['expected_grid_rows']
                            and coverage['observed_rows'] == expected['observed_rows']
                            and coverage['missing_rows'] == expected['missing_grid_rows']
                            and actual['normalization']['body']['selected_invalid_rows'] == expected['invalid_present_rows']
                            and loaded['availability']['basis'] == expected['availability_basis']
                            and actual['normalization']['body']['historical_publication_time'] == expected['historical_publication_time']
                            and loaded['scientific_readiness'] is expected['scientific_readiness'])
            finally:
                broker.close()
        checks[counter] += 1
    expected = feature_cases['definitions']
    require(digest(definitions(['BTCUSDT', 'ETHUSDT'])) == digest(expected))
    checks['definition_cases'] = len(expected)
    require(checks == CHECKS)
    return checks


def _child(directory, snapshot_id, manifest_path):
    from . import binance_normalize as normalizer
    from .coordination import Broker
    expected = decode(Path(manifest_path).read_bytes())
    require(pins_match(expected) and footprint(read_bundle()) == expected)
    require(not list((ROOT/'trading_researcher').glob('**/*.pyc')))
    app = {Path(name).name: value for name, value in expected.items() if name.startswith('trading_researcher/')}
    normalizer._BOUND_SNAPSHOT = app
    normalizer._environment(app)
    checks = fixed_checks()
    broker = Broker(directory)
    try:
        original = binding(broker, snapshot_id)
        result = normalizer.normalize_partition(broker, broker.admin_token, **original['request'])
        replay = replay_equal(original, binding(broker, result['snapshot']['id']))
        declared = definitions(original['request']['universe']['instruments'])
        require({entry['feature_ref']: {'type': entry['type'], 'unit': entry['unit']} for entry in declared} == original['catalog'])
        require(footprint(read_bundle()) == expected)
        report = {'status': 'CERTIFIED', 'reason': 'FIXED_CASES_AND_FULL_SOURCE_REPLAY_PASSED',
            'checks': checks, 'replay': replay, 'definitions': declared,
            'binding_hash': digest(original), 'environment': normalizer._environment(app), 'footprint': expected}
    finally:
        broker.close()
    return report


def run_validation(bundle, directory, snapshot_id, root):
    from .binance_normalize import _run_child
    root = Path(root)
    expected = footprint(bundle)
    if not pins_match(expected):
        raise Invalid('Pinned independent feature expectations changed')
    for name, raw in bundle.items():
        target = root/name
        target.parent.mkdir(parents=True, exist_ok=True)
        _durable_file(target, raw)
    _durable_file(root/'source-manifest.json', canonical(expected).encode())
    bootstrap = ('import sys;sys.path.insert(0,sys.argv[1]);'
        'from trading_researcher.features import _child;from trading_researcher.codec import canonical;'
        'print(canonical(_child(sys.argv[2],sys.argv[3],sys.argv[4])),flush=True)')
    report = _run_child([sys.executable, '-I', '-S', '-B', '-c', bootstrap, str(root),
        str(directory), snapshot_id, str(root/'source-manifest.json')], root)
    if (type(report) is not dict or set(report) != REPORT_FIELDS
            or report.get('reason') != 'FIXED_CASES_AND_FULL_SOURCE_REPLAY_PASSED'
            or footprint({name: (root/name).read_bytes() for name in bundle}) != expected
            or report.get('footprint') != expected or report.get('checks') != CHECKS
            or report.get('status') != 'CERTIFIED' or not _environment_current(report.get('environment'))):
        raise Conflict('Feature child did not return the bound conformance report')
    return report


class FeatureCertification:
    def _feature_attempts(self):
        attempts = {}
        for row in self._db.execute('SELECT envelope FROM events ORDER BY seq'):
            event = decode(row[0])
            action, details = event['action'], event['details']
            identity = details.get('attempt_id')
            if event['actor'] != 'controller':
                continue
            if action == 'feature_certification_started':
                attempts[identity] = {'attempt_id': identity, 'data_snapshot_id': details['data_snapshot_id'],
                    'state': 'STARTED', 'started_at': event['time'], 'ended_at': None, 'certificate_id': None}
            elif identity in attempts and action in ('feature_certification_checked', 'feature_certification_interrupted'):
                attempts[identity].update(state='COMPLETED' if action.endswith('_checked') else 'INTERRUPTED',
                    ended_at=event['time'], certificate_id=details.get('artifact_id'))
        return list(attempts.values())

    def _recover_feature_checks(self):
        with self._transaction():
            for item in self._feature_attempts():
                if item['state'] == 'STARTED':
                    self._event('controller', 'feature_certification_interrupted', attempt_id=item['attempt_id'],
                        reason='previous_writer_ended_before_commit')

    def _inspect_feature_checks(self, actor, limit=50):
        integer(limit, 'limit', 1)
        if limit > 100:
            raise Invalid('Feature check view is bounded to 100 records')
        attempts = self._feature_attempts()
        return {'attempts': list(reversed(attempts[-limit:])), 'total': len(attempts),
            'pending': sum(item['state'] == 'STARTED' for item in attempts), 'scientific_authority': False}

    def _retain_feature_package(self, bundle):
        if not valid_names(bundle) or sum(len(raw) for raw in bundle.values()) > 16*1024*1024:
            raise Invalid('Feature source package exceeds its fixed closure/resource envelope')
        files = {name: self._stage_blob_bytes(raw) for name, raw in sorted(bundle.items())}
        with self._transaction():
            for descriptor in files.values():
                self._register_blob(descriptor)
            artifact = self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'operations', 'source_refs': [], 'exposure': [],
                'blob_refs': sorted({item['sha256'] for item in files.values()}),
                'authority': 'retained_source_not_certified',
                'body': {'schema': 'feature-source-package/1', 'profile': PROFILE, 'created_at': self._now(),
                    'files': files, 'footprint': footprint(bundle)}})
            self._event('controller', 'feature_source_retained', artifact_id=artifact['id'])
            return artifact['id']

    def _load_feature_package(self, identity):
        artifact = self._artifact(identity)
        body = artifact['body']
        if (artifact['creator'] != 'controller' or artifact['origin'] != 'controller'
                or type(body) is not dict or body.get('schema') != 'feature-source-package/1'
                or body.get('profile') != PROFILE or not valid_names(body.get('files', {}))):
            raise Denied('Expected a protected feature source package')
        self._require_usable_dependencies(identity)
        bundle = {}
        for name, descriptor in body['files'].items():
            raw = self._read_blob_bytes(descriptor['sha256'])
            if len(raw) != descriptor['size']:
                raise Conflict('Retained feature source size changed')
            bundle[name] = raw
        if (sum(len(raw) for raw in bundle.values()) > 16*1024*1024
                or footprint(bundle) != body['footprint']
                or set(artifact['blob_refs']) != {item['sha256'] for item in body['files'].values()}):
            raise Conflict('Retained feature source identity changed')
        return bundle

    def _certify_features_external(self, token, args):
        with self._mutex:
            if self._principal(token)['role'] != 'operator':
                raise Denied('Feature certification is owned by the host')
            if set(args) != {'data_snapshot_id'}:
                raise Invalid('Feature certification accepts only an owned snapshot identity')
            snapshot_id = text(args['data_snapshot_id'], 'data snapshot identity')
            original = binding(self, snapshot_id)
        bundle = read_bundle()
        package_id = self._retain_feature_package(bundle)
        attempt = uuid.uuid4().hex
        with self._transaction():
            self._event('controller', 'feature_certification_started', attempt_id=attempt,
                data_snapshot_id=snapshot_id, source_package_id=package_id)
        report = None
        try:
            with self._mutex:self._require_usable_dependencies(package_id)
            with tempfile.TemporaryDirectory(prefix='trf-feature-validation-') as temporary:
                root = Path(temporary)
                self._backup_bundle_external(token, {'destination': str(root/'registry')})
                descriptor = os.open(root/'registry/operator.key', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                    stream.write(self.admin_token)
                    stream.flush()
                    os.fsync(stream.fileno())
                report = run_validation(bundle, root/'registry', snapshot_id, root)
        except Exception as error:
            report = gap_report(bundle, 'VALIDATION_FAILED', type(error).__name__)
        except BaseException:
            with self._transaction():
                self._event('controller', 'feature_certification_interrupted', attempt_id=attempt,
                    reason='caller_cancelled_before_commit')
            raise
        with self._transaction():
            if self._principal(token)['role'] != 'operator':
                raise Denied('Feature certification is owned by the host')
            if report['status'] == 'CERTIFIED':
                try:
                    validate_report(report, original, bundle)
                    require(digest(binding(self, snapshot_id)) == digest(original) == report['binding_hash'])
                    require(footprint(read_bundle()) == footprint(self._load_feature_package(package_id)) == report['footprint'])
                    require(_environment_current(report['environment']))
                except (OSError, ValueError, TypeError, Invalid, Conflict, Denied):
                    report = gap_report(bundle, 'INPUT_OR_REPORT_CHANGED_DURING_VALIDATION')
            definition_id = None
            if report['status'] == 'CERTIFIED':
                parents = sorted(set([snapshot_id, original['snapshot']['body']['catalog_id'],
                    *original['snapshot']['body']['row_source_ids']]))
                definition = self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                    'origin': 'source', 'data_class': original['snapshot']['data_class'], 'source_refs': parents,
                    'exposure': sorted(set(parents+original['exposure'])),
                    'authority': 'measurement_definition_not_scientific_acceptance',
                    'body': {'schema': 'feature-definitions/1', 'created_at': self._now(),
                        'specification_version': PROFILE, 'input_refs': parents,
                        'parameters': {'delay_seconds': original['request']['delay_seconds']},
                        'golden_case_refs': deepcopy(PINS), 'definitions': report['definitions'],
                        'scientific_readiness': False}})
                definition_id = definition['id']
            report.pop('definitions', None)
            body = {**report, 'schema': 'feature-certificate/1', 'profile': PROFILE, 'scope': deepcopy(SCOPE),
                'created_at': self._now(), 'attempt_id': attempt, 'source_package_id': package_id,
                'data_snapshot_id': snapshot_id, 'definitions_id': definition_id,
                'scientific_readiness': False}
            refs = [snapshot_id, package_id]+([definition_id] if definition_id else [])
            certificate = self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': original['snapshot']['data_class'],
                'source_refs': refs, 'exposure': sorted(set(refs+original['exposure'])),
                'authority': SCOPE['authority'], 'body': body})
            self._event('controller', 'feature_certification_checked', attempt_id=attempt,
                artifact_id=certificate['id'], status=body['status'])
            canonical(certificate)
            return certificate

    def _feature_certificate_status(self, actor, certificate_id, data_snapshot_id=None):
        artifact = self._artifact(text(certificate_id, 'certificate identity'))
        body = artifact['body']
        if (artifact['creator'] != 'controller' or artifact['origin'] != 'controller'
                or artifact.get('authority') != SCOPE['authority'] or type(body) is not dict
                or body.get('schema') != 'feature-certificate/1' or body.get('profile') != PROFILE):
            raise Denied('Expected a host-owned feature certificate')
        if data_snapshot_id is not None and data_snapshot_id != body['data_snapshot_id']:
            raise Denied('Feature certificate belongs to a different data snapshot')
        if self._dependency_use(certificate_id)['status']=='INVALIDATED_BY_DEPENDENCY':
            return {'certificate_id':certificate_id,'status':'INVALIDATED_BY_DEPENDENCY',
                'data_snapshot_id':body['data_snapshot_id'],'scientific_readiness':False,'scope':deepcopy(SCOPE)}
        status = 'CERTIFICATION_GAP'
        if body['status'] == 'CERTIFIED':
            try:
                retained = self._load_feature_package(body['source_package_id'])
                original = binding(self, body['data_snapshot_id'])
                require(footprint(retained) == body['footprint'])
                require(digest(original) == body['binding_hash'])
                definition = self._artifact(body['definitions_id'])
                require(definition['creator'] == 'controller' and definition['body']['schema'] == 'feature-definitions/1')
                require(body['scientific_readiness'] is False and body['scope'] == SCOPE)
                fixed = decode(retained['tests/fixtures/reference_feature_cases.json'])['definitions']
                require(digest(definition['body']['definitions']) == digest([entry for entry in fixed
                    if entry['instrument'] in original['request']['universe']['instruments']]))
                require(digest(body['checks']) == digest(CHECKS) and digest(body['replay']) == digest(replay_summary(original))
                    and body['reason'] == 'FIXED_CASES_AND_FULL_SOURCE_REPLAY_PASSED')
            except (OSError, ValueError, TypeError, Invalid, Conflict, Denied):
                status = 'QUARANTINED'
            else:
                try:
                    current = footprint(read_bundle()) == body['footprint'] and _environment_current(body['environment'])
                except (OSError, ValueError, TypeError):
                    current = False
                status = 'CURRENT' if current else 'STALE'
        return {'certificate_id': certificate_id, 'status': status, 'data_snapshot_id': body['data_snapshot_id'],
            'scientific_readiness': False, 'scope': deepcopy(SCOPE)}
