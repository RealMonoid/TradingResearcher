"""Exact development timing evidence for both roles; no equivalence verdict."""
from copy import deepcopy

from .codec import Invalid, digest, integer, strings, text
from .data import PARTITIONS, window
from .errors import Conflict, Denied
from .features import PROFILE, SCOPE


def require(condition, message):
    if not condition:
        raise Invalid(message)


def availability_summary(rows, feature_definitions, delay_seconds, universe):
    """Check every supplied timing entry, including nulls, without exporting values."""
    start, end, instruments = window(universe)
    integer(delay_seconds, 'explicit availability delay')
    expected_count = (end-start)//900 * len(instruments)
    require(expected_count <= 100000 and type(rows) is list, 'Availability evidence exceeds its bounded data view')
    by_instrument = {instrument: set() for instrument in instruments}
    for definition in feature_definitions:
        if definition['instrument'] in by_instrument:
            refs = by_instrument[definition['instrument']]
            require(definition['feature_ref'] not in refs, 'Duplicate availability feature definition')
            refs.add(definition['feature_ref'])
    require(all(by_instrument.values()), 'Availability evidence needs explicit feature definitions')
    seen, samples, nulls, missing = set(), 0, 0, 0
    for row in rows:
        require(type(row) is dict and set(row) == {'time', 'instrument', 'features'}, 'Malformed timing-evidence row')
        when, instrument, features = row['time'], row['instrument'], row['features']
        require(type(when) is int and start <= when < end and when % 900 == 0
                and type(instrument) is str and instrument in by_instrument,
                'Timing evidence row is outside its declared scope')
        require((when, instrument) not in seen, 'Duplicate timing-evidence coordinate')
        seen.add((when, instrument))
        required = by_instrument[instrument]
        require(type(features) is dict and set(features) <= required, 'Unknown timing-evidence feature')
        missing += len(required-set(features))
        for ref, sample in features.items():
            require(type(sample) is dict and set(sample) == {'value', 'available_at'}, 'Malformed timing entry')
            require(type(sample['available_at']) is int and sample['available_at'] == when+delay_seconds,
                    'Retained availability differs from the exact fixed-delay rule at ' + ref + ':' + str(when))
            samples += 1
            nulls += sample['value'] is None
    return {'status': 'MATCHED_EXACT_FIXED_DELAY', 'checked_rows': len(seen),
        'checked_feature_samples': samples, 'null_feature_samples': nulls,
        'missing_feature_samples': missing, 'absent_grid_rows': expected_count-len(seen)}


def availability_packet(host, context, inputs, catalog_id, definitions, target=None):
    if 'feature_certificate_id' not in inputs:
        return {}
    identity = text(inputs['feature_certificate_id'], 'feature certificate identity')
    authorized = set(context['artifact_ids'])
    if identity not in authorized:
        raise Denied('Availability certificate is outside the frozen context')
    certificate = host._artifact(identity)
    body = certificate['body']
    require(certificate['creator'] == 'controller' and certificate['origin'] == 'controller'
        and certificate['data_class'] == 'development' and certificate['authority'] == SCOPE['authority']
        and type(body) is dict and body.get('schema') == 'feature-certificate/1'
        and body.get('profile') == PROFILE and body.get('status') == 'CERTIFIED',
        'Availability evidence needs an owned certified development measurement')
    snapshot_id = text(body.get('data_snapshot_id'), 'certified snapshot identity')
    definition_id = text(body.get('definitions_id'), 'certified definition identity')
    required_ids = {identity, snapshot_id, catalog_id, definition_id}
    if not required_ids <= authorized:
        raise Denied('Availability certificate does not authorize unlisted inputs')
    definition = next((item for item in definitions if item['id'] == definition_id), None)
    require(definition is not None, 'Availability evidence must use the supplied certified definitions')
    require({snapshot_id, catalog_id} <= set(definition['body']['input_refs']), 'Availability definition origins differ')
    snapshot = host._artifact(snapshot_id)
    data = snapshot['body']
    require(snapshot['creator'] == 'controller' and snapshot['origin'] == 'source'
        and snapshot['data_class'] == 'development' and type(data) is dict
        and data.get('schema') == 'data-snapshot/1' and data.get('catalog_id') == catalog_id,
        'Availability evidence needs the exact owned development snapshot and catalog')
    manifest = data['manifest']
    require(manifest['partition'] == 'development' and manifest['availability']['basis'] == 'assumed',
        'Availability evidence cannot expose a protected or different data profile')
    universe = manifest['universe']
    start, end, instruments = window(universe)
    require((end-start)//900 * len(instruments) <= 100000, 'Availability evidence exceeds its bounded data view')
    declared = definition['body']['definitions']
    delay = definition['body']['parameters']['delay_seconds']
    integer(delay, 'explicit certified delay')
    require(all(item['availability'] == {'basis': 'assumed', 'rule': 'row_time + delay_seconds',
        'parameter': 'EXPLICIT_NONNEGATIVE_INTEGER_SECONDS_NO_DEFAULT', 'historical_publication_time': None}
        for item in declared), 'Unsupported certified availability rule')
    if target is not None:
        original_context = host._context(host._job(target['job_id'])['spec']['context_id'])
        if not all(required_ids <= set(ids) for ids in (original_context['artifact_ids'],
                target['source_refs'], target['body']['authorization_snapshot'])):
            raise Denied('Availability evidence was not authorized to the original formalization')
        allowed = {target['id'], target['body']['idea_id'], catalog_id,
                   *(item['id'] for item in definitions), identity, snapshot_id}
        if not authorized <= allowed:
            raise Denied('Availability review context contains unrelated material')
        candidate = target['body']['candidate']
        if type(candidate) is dict:
            selected = candidate.get('test_universe', {})
            require(type(selected) is dict, 'candidate universe must be an object')
            require(selected.get('data_snapshot_ref') == snapshot_id, 'Candidate and availability snapshots differ')
            lower, upper, chosen = window({key: selected.get(key) for key in ('start', 'end', 'instruments')})
            require(start <= lower < upper <= end and set(chosen) <= set(instruments),
                    'Candidate is outside its availability evidence scope')
            refs = strings(candidate.get('feature_refs'), 'candidate feature references')
            require(set(refs) <= {item['feature_ref'] for item in declared}, 'Candidate dependencies lack timing evidence')
    # Status checks read retained packages/blobs: all identity and access checks
    # above deliberately precede this operation, including protected-data denial.
    status = host._feature_certificate_status(None, identity, data_snapshot_id=snapshot_id)
    require(status['status'] in ('CURRENT', 'STALE'), 'Availability certificate is not intact and usable')
    loaded = host._load_reference_data(snapshot_id, universe['start'], universe['end'], instruments)
    require(loaded['data_snapshot_ref'] == snapshot_id and digest(loaded['catalog']) == data['catalog_hash'],
            'Availability source identity changed')
    summary = availability_summary(loaded['rows'], declared, delay, universe)
    for dependency in (identity, snapshot_id, definition_id):
        host._require_usable_dependencies(dependency)
    return {'availability_evidence': {'schema': 'development-availability-evidence/1',
        'certificate_id': identity, 'data_snapshot_id': snapshot_id, 'catalog_id': catalog_id,
        'definitions_id': definition_id, 'certificate_body_sha256': digest(body),
        'source_footprint_sha256': digest(body['footprint']),
        'row_blobs': deepcopy(body['replay']['row_blobs']), 'universe': deepcopy(universe),
        'delay_seconds': delay, 'rule': 'For every present feature entry, including null-valued entries, available_at equals row_time + delay_seconds exactly.',
        'summary': summary, 'availability_basis': 'assumed', 'historical_publication_time': None,
        'qualification': 'Exhaustive timing check of this exact certified development snapshot. Absent rows and missing/null values remain missing. No later recorded availability exists among these entries. This is not historical publication truth, a hypothesis-equivalence verdict, an outcome result or scientific admission. The reviewer must separately derive the candidate-specific cutoff implications.',
        'scientific_readiness': False}}


RELEASE = 'feature-evidence-release/1'
RELEASE_AUTHORITY = 'development_feature_input_release_only'


def _release_inputs(host, certificate_id):
    """Operator-side grant validation; never a generic work-product release."""
    certificate = host._artifact(text(certificate_id, 'feature certificate identity'))
    body = certificate['body']
    require(certificate['creator'] == 'controller' and certificate['origin'] == 'controller'
        and certificate['data_class'] == 'development' and certificate['authority'] == SCOPE['authority']
        and type(body) is dict and body.get('schema') == 'feature-certificate/1'
        and body.get('profile') == PROFILE and body.get('status') == 'CERTIFIED',
        'Only owned certified development raw-feature evidence may be released')
    snapshot = host._data_snapshot(text(body.get('data_snapshot_id'), 'certified snapshot identity'))
    data = snapshot['body']
    definition = host._artifact(text(body.get('definitions_id'), 'certified definition identity'))
    require(snapshot['data_class'] == 'development' and data['manifest']['partition'] == 'development'
        and definition['creator'] == 'controller' and definition['origin'] == 'source'
        and definition['data_class'] == 'development' and definition['body'].get('schema') == 'feature-definitions/1'
        and {snapshot['id'], data['catalog_id']} <= set(definition['body']['input_refs']),
        'Feature evidence release cannot expose protected or mismatched inputs')
    universe = data['manifest']['universe']
    window(universe)
    require(PARTITIONS['development'][0] <= universe['start'] < universe['end'] <= PARTITIONS['development'][1],
        'Feature evidence release is outside the development calendar')
    host._deny_final_calibration_ancestry(certificate)
    status = host._feature_certificate_status(None, certificate_id, data_snapshot_id=snapshot['id'])
    require(status['status'] in ('CURRENT', 'STALE'), 'Feature evidence certificate is not intact and usable')
    return certificate, snapshot, definition


def _find_release(host, certificate_id):
    rows = host._db.execute('''SELECT id FROM artifacts WHERE
        json_extract(envelope,'$.body.schema')=? AND json_extract(envelope,'$.body.certificate_id')=?
        AND json_extract(envelope,'$.creator')='controller' AND json_extract(envelope,'$.origin')='controller'
        AND json_extract(envelope,'$.authority')=?''', (RELEASE, certificate_id, RELEASE_AUTHORITY)).fetchall()
    require(len(rows) <= 1, 'Ambiguous feature evidence release')
    return host._artifact(rows[0][0]) if rows else None


def release_feature_evidence(host, actor, certificate_id, target_epoch):
    if actor['role'] != 'operator':
        raise Denied('Only the operator may release development feature evidence')
    integer(target_epoch, 'target epoch')
    certificate, snapshot, definition = _release_inputs(host, certificate_id)
    prior = _find_release(host, certificate_id)
    if prior:
        if prior['body']['target_epoch'] != target_epoch:
            raise Conflict('Feature evidence release epoch is immutable')
        return prior
    refs = sorted({certificate_id, snapshot['id'], definition['id']})
    artifact = host._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
        'origin': 'controller', 'data_class': 'operations', 'source_refs': refs,
        'exposure': sorted(set(refs) | set(certificate['exposure']) | set(snapshot['exposure']) | set(definition['exposure'])),
        'authority': RELEASE_AUTHORITY, 'body': {'schema': RELEASE, 'certificate_id': certificate_id,
            'data_snapshot_id': snapshot['id'], 'definitions_id': definition['id'], 'target_epoch': target_epoch,
            'created_at': host._now(), 'scientific_readiness': False}})
    host._event(actor['name'], 'development_feature_evidence_released', artifact_id=artifact['id'],
                certificate_id=certificate_id, target_epoch=target_epoch)
    return artifact


def released_feature_evidence(host, certificate, epoch, research_time):
    if type(certificate['body']) is not dict or certificate['body'].get('schema') != 'feature-certificate/1':
        return None
    release = _find_release(host, certificate['id'])
    if release is None:
        return None
    body = release['body']
    require(release['data_class'] == 'operations' and set(body) == {'schema', 'certificate_id',
        'data_snapshot_id', 'definitions_id', 'target_epoch', 'created_at', 'scientific_readiness'}
        and body['scientific_readiness'] is False, 'Invalid feature evidence release')
    integer(body['target_epoch'], 'feature evidence release epoch')
    integer(body['created_at'], 'feature evidence release time')
    if epoch < body['target_epoch'] or research_time < body['created_at']:
        raise Denied('Feature evidence release is unavailable to this epoch or research time')
    intact, snapshot, definition = _release_inputs(host, certificate['id'])
    require(body['data_snapshot_id'] == snapshot['id'] and body['definitions_id'] == definition['id']
        and release['source_refs'] == sorted({intact['id'], snapshot['id'], definition['id']}),
        'Feature evidence release inputs differ')
    host._require_usable_dependencies(release['id'])
    return release
