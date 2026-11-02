"""Finite resource decisions for the one approved scalar family inventory.

The pure planner interprets a view without authenticating it. The consuming
guard checks owned custody under a sealed trusted-driver binding and dispatches
the Registry's existing APIs. The driver pins the one actual approval, recipe,
isolated host and destination. Neither layer grants scientific admission.
"""
import hashlib
from pathlib import Path
import re
import shutil

from trading_researcher.binding import require
from trading_researcher.codec import Invalid, MAX_BYTES, canonical, decode, digest
from trading_researcher.storage import _hash_file


MAX_COMPUTE_MS = 648000000
MAX_STORAGE_BYTES = 107374182400
MAX_GRANTS = 179
ATTEMPT_COMPUTE_MS = 300000
ATTEMPT_STORAGE_BYTES = 268435456
METADATA_BYTES = 1048576
COMPUTE_TRANCHE_MS = 3600000
STORAGE_TRANCHE_BYTES = 4294967296
PER_WORLD_PHYSICAL_PLANNING_BYTES = 7525747
_LOADED_SELF = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _identity(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None,
            'Exact finite study, world and checkpoint identities required')
    return value


def _number(value):
    require(type(value) is int and value >= 0, 'Nonnegative integer resource accounting required')
    return value


def next_request(view):
    """Return the next bounded public request; unsafe states require diagnosis.

    Registry continuation validation remains authoritative for exact checkpoint,
    progress, dependencies and immutable grant replay. COMPLETE never renews a
    series, regardless of its count-assessment result.
    """
    try:
        require(type(view) is dict, 'Owned finite study view required')
        study = _identity(view['study_id'])
        checkpoint = _identity(view['resource_checkpoint'])
        budget = view['budget']
        require(type(budget) is dict, 'Resource accounting required')
        grants = view['continuation_ids']
        require(type(grants) is list and len(grants) <= MAX_GRANTS,
                'Finite continuation count exhausted or malformed')
        for identity in grants:
            _identity(identity)
        require(len(set(grants)) == len(grants), 'Duplicate continuation history')
        for flag in ('overrun', 'usage_uncertain'):
            require(budget[flag] is False, 'Uncertain or excessive use cannot be renewed')
        require(type(budget['outstanding_attempts']) is list and not budget['outstanding_attempts'],
                'Outstanding use cannot be replaced')
        require(type(budget['next_reservation_fits']) is bool, 'Exact reservation verdict required')
        numbers = {name: _number(budget[name]) for name in (
            'charged_compute_ms', 'charged_storage_bytes', 'initial_storage_bytes',
            'continuation_storage_bytes', 'original_max_compute_ms',
            'original_max_storage_bytes', 'max_compute_ms', 'max_storage_bytes')}
        compute, storage = numbers['charged_compute_ms'], numbers['charged_storage_bytes']
        maximum_compute, maximum_storage = numbers['max_compute_ms'], numbers['max_storage_bytes']
        original_compute = numbers['original_max_compute_ms']
        original_storage = numbers['original_max_storage_bytes']
        require(0 < original_compute <= COMPUTE_TRANCHE_MS and
                0 < original_storage <= STORAGE_TRANCHE_BYTES,
                'Initial allowance exceeds the approved tranche')
        require(original_compute <= maximum_compute <= min(
                    MAX_COMPUTE_MS, original_compute + len(grants) * COMPUTE_TRANCHE_MS) and
                original_storage <= maximum_storage <= min(
                    MAX_STORAGE_BYTES, original_storage + len(grants) * STORAGE_TRANCHE_BYTES),
                'Allocated capacity exceeds finite authority or recorded grant count')
        require(numbers['continuation_storage_bytes'] == len(grants) * METADATA_BYTES and
                numbers['initial_storage_bytes'] <= original_storage and
                numbers['initial_storage_bytes'] + numbers['continuation_storage_bytes'] <= storage,
                'Retention and continuation metadata accounting differs')
        require(compute <= maximum_compute and storage <= maximum_storage,
                'Observed charges exceed allocated capacity')
        attempts = budget['attempts_per_world']
        require(type(attempts) is dict and len(attempts) <= 2048, 'Bounded attempt history required')
        for identity, count in attempts.items():
            _identity(identity)
            require(type(count) is int and count == 1, 'Frozen max-one attempt cannot be reset')
        summary = view['summary']
        require(type(summary) is dict and type(summary['complete']) is bool and
                view['scientific_readiness'] is False and view['n_min'] is None,
                'Finite resource decisions grant no scientific authority')
        state = view['status']
        require(state in ('READY', 'RESOURCE_STOP', 'COMPLETE') and
                summary['complete'] == (state == 'COMPLETE'),
                'Only healthy unfinished work or an exact completion may proceed')
        if state == 'COMPLETE':
            return None
        fits = (compute + ATTEMPT_COMPUTE_MS <= maximum_compute and
                storage + ATTEMPT_STORAGE_BYTES <= maximum_storage)
        require(budget['next_reservation_fits'] == fits, 'Reservation verdict contradicts accounting')
        if state == 'READY':
            world = _identity(view['next_world_id'])
            require(fits and world not in attempts, 'Next full unused world reservation required')
            return {'op': 'advance_family_calibration', 'args': {'calibration_id': study}}
        require(not fits and view['next_world_id'] is None and len(grants) < MAX_GRANTS,
                'A continuation requires a real resource stop and an available grant')
        additional_compute = min(COMPUTE_TRANCHE_MS, MAX_COMPUTE_MS - maximum_compute)
        additional_storage = min(STORAGE_TRANCHE_BYTES, MAX_STORAGE_BYTES - maximum_storage)
        require(additional_compute + additional_storage > 0 and
                compute + ATTEMPT_COMPUTE_MS <= maximum_compute + additional_compute and
                storage + METADATA_BYTES + ATTEMPT_STORAGE_BYTES <= maximum_storage + additional_storage,
                'Remaining finite authority cannot hold metadata and the next full attempt')
        return {'op': 'continue_study', 'args': {
            'key': 'finite-family:' + digest({'study_id': study, 'checkpoint': checkpoint}),
            'study_id': study, 'expected_checkpoint': checkpoint,
            'additional_compute_ms': additional_compute,
            'additional_storage_bytes': additional_storage,
            'rationale': 'Continue the one approved fixed scalar family inventory within '
                         '180 compute hours and 100 GiB logical storage.',
            'expected_progress': 'Complete the next predeclared world with full separate replay '
                                 'and no replacement or reset.',
            'stop_reason': 'Stop at the next resource checkpoint, terminal failure, source or '
                           'capacity gap, or aggregate limit.'}}
    except (KeyError, TypeError) as exc:
        raise Invalid('Malformed finite resource view') from exc


def _path(value):
    require(type(value) is str, 'Explicit pinned operator path required')
    path = Path(value)
    require(path.is_absolute() and str(path.resolve()) == value, 'Resolved absolute operator path required')
    return path


def _pinned_file(path, expected):
    _identity(expected)
    require(_hash_file(path, limit=None)[0] == expected, 'Pinned operator or recovery file changed')


def _recovery(broker, bound):
    path = _path(bound['recovery_path'])
    expected = _identity(bound['recovery_sha256'])
    checksum, _, raw = _hash_file(path, collect=True, limit=MAX_BYTES)
    require(checksum == expected, 'Pinned recovery receipt changed')
    proof = decode(raw)
    fields = {'schema', 'status', 'calibration_id', 'artifact_hash', 'initial_attempts',
              'initial_grants', 'backup_manifest', 'restored_database'}
    require(type(proof) is dict and set(proof) == fields and
            proof['schema'] == 'prepared-family-recovery/1' and proof['status'] == 'PASS' and
            proof['calibration_id'] == bound['calibration_id'] and
            proof['artifact_hash'] == bound['artifact_hash'], 'Exact prepared-capsule recovery proof required')
    require(type(proof['initial_attempts']) is int and proof['initial_attempts'] == 0 and
            type(proof['initial_grants']) is int and proof['initial_grants'] == 0,
            'Before-run recovery proof must preserve zero numerical attempts and grants')
    paths = []
    for key, name in (('backup_manifest', 'manifest.json'), ('restored_database', 'registry.sqlite3')):
        item = proof[key]
        require(type(item) is dict and set(item) == {'path', 'sha256'}, 'Exact recovery file binding required')
        preserved = _path(item['path'])
        require(preserved.name == name and not preserved.is_relative_to(broker.directory.resolve()),
                'Recovery files must be preserved separately from the active Registry')
        _pinned_file(preserved, item['sha256'])
        paths.append(preserved)
    require(paths[0].parent != paths[1].parent, 'Separate backup and restored Registry required')


def consume_next(broker, bound_run):
    """Consume one actual owned action under a sealed trusted-operator binding.

    The run-specific driver pins the real approval, one recipe and C: destination
    and creates the recovery proof with the existing full backup/restore owners.
    This function accepts no caller view, action, amount or readiness verdict.
    File custody is operational evidence, not scientific admission. Observers may
    retain a failure after dispatch; they never cause an automatic retry.
    """
    from trading_researcher.family_study_runs import FamilyCalibrationStudies

    try:
        fields = {'schema', 'calibration_id', 'artifact_hash', 'request_hash', 'manifest_hash',
                  'approval_path', 'approval_sha256', 'assessment_footprint', 'calculation_footprint',
                  'runtime_identity', 'registry_path', 'recovery_path', 'recovery_sha256', 'driver_files'}
        require(type(bound_run) is dict and set(bound_run) == fields and
                bound_run['schema'] == 'finite-family-run-binding/1', 'Exact sealed run binding required')
        bound = decode(canonical(bound_run))
        identity = _identity(bound['calibration_id'])
        require(_path(bound['registry_path']) == broker.directory.resolve(), 'Approved primary Registry differs')
        _pinned_file(_path(bound['approval_path']), bound['approval_sha256'])
        drivers = bound['driver_files']
        loaded_path = str(Path(__file__).resolve())
        require(type(drivers) is dict and 1 <= len(drivers) <= 8 and
                drivers.get(loaded_path) == _LOADED_SELF, 'Loaded operator source is not pinned')
        for name, expected in drivers.items():
            _pinned_file(_path(name), expected)
        token = broker.admin_token
        artifact = broker.call(token, 'get_artifact', artifact_id=identity)
        require(digest(artifact) == bound['artifact_hash'], 'Owned calibration artifact differs')
        runner = FamilyCalibrationStudies(broker)
        require(runner._study(identity) == artifact and artifact['authority'] == runner._study_authority,
                'Owned final family-calibration input required')
        body = artifact['body']
        require(digest(body['request']) == bound['request_hash'] and
                digest(body['manifest']) == bound['manifest_hash'] and
                body['assessment_source_footprint'] == bound['assessment_footprint'] and
                body['source_footprint'] == bound['calculation_footprint'] and
                body['runtime_identity'] == bound['runtime_identity'], 'Frozen run inputs or source identities differ')
        limits = body['manifest']['profile']['budget']
        require(limits['attempt_compute_ms'] == ATTEMPT_COMPUTE_MS and
                limits['attempt_storage_bytes'] == ATTEMPT_STORAGE_BYTES and
                type(limits['max_attempts']) is int and limits['max_attempts'] == 1,
                'Approved per-attempt envelope differs')
        _recovery(broker, bound)
        broker._require_usable_dependencies(identity)
        runner._study_before_execute(artifact)
        inputs = runner._study_inputs(broker._binding_owner(token), body['request'])
        require(digest(list(inputs)) == digest(
            [body['payload'], body['manifest'], artifact['source_refs'], artifact['exposure']]),
            'Recomputed owned inputs differ before reservation')
        runner._load_study_source(artifact)
        descriptor = body['payload']['case_blob']
        require(len(broker._read_blob_bytes(descriptor['sha256'])) == descriptor['size'],
                'Retained case bytes differ before reservation')
        before = broker.call(token, 'inspect_family_calibration', calibration_id=identity)
        require(before['study_id'] == identity, 'Fetched study view differs')
        if before['continuation_ids']:
            broker._require_usable_dependencies(before['continuation_ids'][-1])
        action = next_request(before)
        if action is None:
            return {'request': None, 'view': before, 'result_id': None}
        # Conditional file-length planning includes future primary growth and
        # both complete terminal copies, plus 2 GiB setup/temp and 4 GiB free.
        # Already retained files consume current disk space, not future growth.
        committed = broker._db.execute('SELECT COALESCE(SUM(size),0) FROM blobs').fetchone()[0]
        committed += (broker.directory / 'registry.sqlite3').stat().st_size
        remaining = len(body['manifest']['worlds']) - before['summary']['recorded_worlds']
        require(type(remaining) is int and 0 <= remaining <= 2048, 'Remaining world inventory differs')
        required_free = (6 * 1024**3 + 2 * committed +
                         3 * remaining * PER_WORLD_PHYSICAL_PLANNING_BYTES)
        require(shutil.disk_usage(broker.directory).free >= required_free,
                'Physical capacity cannot hold planned terminal copies and reserves')
        result = broker.call(token, action['op'], **action['args'])
        after = broker.call(token, 'inspect_family_calibration', calibration_id=identity)
        require(after['study_id'] == identity, 'Post-call study identity differs')
        if action['op'] == 'advance_family_calibration':
            require(result == after and after['attempt_artifact_ids'][:-1] == before['attempt_artifact_ids'] and
                    len(after['attempt_artifact_ids']) == len(before['attempt_artifact_ids']) + 1 and
                    after['continuation_ids'] == before['continuation_ids'],
                    'Advance response differs from retained single-attempt history; no automatic retry')
            result_id = after['attempt_artifact_ids'][-1]
        else:
            require(action['op'] == 'continue_study' and result['body']['request'] == action['args'] and
                    after['continuation_ids'] == before['continuation_ids'] + [result['id']] and
                    after['attempt_artifact_ids'] == before['attempt_artifact_ids'],
                    'Continuation differs from its exact saved request/history')
            old, new = before['budget'], after['budget']
            require(new['charged_compute_ms'] == old['charged_compute_ms'] and
                    new['charged_storage_bytes'] == old['charged_storage_bytes'] + METADATA_BYTES and
                    new['max_compute_ms'] == old['max_compute_ms'] + action['args']['additional_compute_ms'] and
                    new['max_storage_bytes'] == old['max_storage_bytes'] + action['args']['additional_storage_bytes'] and
                    new['continuation_storage_bytes'] == old['continuation_storage_bytes'] + METADATA_BYTES,
                    'Continuation capacity or metadata settlement differs')
            next_request(after)
            result_id = result['id']
        return {'request': action, 'view': after, 'result_id': result_id}
    except (KeyError, TypeError, ValueError) as exc:
        raise Invalid('Malformed finite consuming binding or response; no automatic retry') from exc
