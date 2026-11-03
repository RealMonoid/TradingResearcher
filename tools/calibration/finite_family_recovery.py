"""One owned recovery action under a sealed, host-local operator binding.

This is the consuming adapter for the approved append-only amendment, not an
approval issuer or a model API. The isolated driver fixes actual authority and
creates the prepared full-backup/restore proof through existing storage owners.
"""
import hashlib
from pathlib import Path
import shutil

from tools.calibration import finite_family as finite
from trading_researcher.binding import require
from trading_researcher.calibration_recovery import (
    CalibrationRecovery, AMENDMENT, SOURCE, INPUT, GRANT, RESULT, _path)
from trading_researcher.codec import Invalid, MAX_BYTES, canonical, decode, digest
from trading_researcher.storage import _hash_file


SCHEMA = 'finite-family-recovery-run-binding/1'
FIELDS = {'schema', 'authority_binding', 'recovery_id', 'artifact_hash',
          'recovery_artifact_hash', 'request_hash', 'manifest_hash',
          'assessment_footprint', 'calculation_footprint', 'controller_footprint',
          'runtime_identity', 'recovery_path', 'recovery_sha256', 'driver_files'}
PROOF_FIELDS = {'schema', 'status', 'study_id', 'recovery_id', 'input_id',
                'artifact_hash', 'recovery_artifact_hash', 'original_checkpoint',
                'prepared_checkpoint', 'initial_attempt_ids', 'initial_continuation_ids',
                'charged_compute_ms', 'charged_storage_bytes', 'backup_manifest',
                'restored_database'}
_LOADED_SELF = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def _prepared_custody(broker, bound, view, input_record):
    path = _path(bound['recovery_path'])
    checksum, _, raw = _hash_file(path, collect=True, limit=MAX_BYTES)
    require(checksum == finite._identity(bound['recovery_sha256']),
            'Pinned prepared amendment recovery proof changed')
    proof = decode(raw)
    require(type(proof) is dict and set(proof) == PROOF_FIELDS
            and proof['schema'] == 'prepared-family-amendment-recovery/1'
            and proof['status'] == 'PASS', 'Exact prepared amendment recovery proof required')
    for key, value in {'study_id': view['study_id'], 'recovery_id': view['recovery_id'],
                       'input_id': view['input_id'], 'artifact_hash': bound['artifact_hash'],
                       'recovery_artifact_hash': bound['recovery_artifact_hash'],
                       'original_checkpoint': view['original_checkpoint'],
                       'prepared_checkpoint': view['prepared_checkpoint']}.items():
        require(proof[key] == value, 'Prepared recovery identity/checkpoint differs: ' + key)
    ib = input_record['body']
    require(proof['initial_attempt_ids'] == ib['original_attempt_ids']
            and proof['initial_continuation_ids'] == ib['original_continuation_ids'],
            'Prepared proof does not preserve the complete original prefix')
    fixed = ib['approval']['fixed_identity']
    require(finite._number(proof['charged_compute_ms']) == fixed['known_compute_ms_retained']
            and finite._number(proof['charged_storage_bytes'])
                == fixed['known_logical_bytes_retained'] + ib['setup_storage_bytes'],
            'Prepared proof must retain original charges and the complete setup tariff')
    require(view['attempt_artifact_ids'][:len(proof['initial_attempt_ids'])]
                == proof['initial_attempt_ids']
            and view['continuation_ids'][:len(proof['initial_continuation_ids'])]
                == proof['initial_continuation_ids'], 'Current history lost its prepared prefix')
    preserved = []
    for key, filename in (('backup_manifest', 'manifest.json'),
                          ('restored_database', 'registry.sqlite3')):
        item = proof[key]
        require(type(item) is dict and set(item) == {'path', 'sha256'},
                'Exact separately preserved recovery file required')
        file = _path(item['path'])
        require(file.name == filename and not file.is_relative_to(broker.directory.resolve()),
                'Prepared recovery files must be separate from the live Registry')
        finite._pinned_file(file, item['sha256'])
        preserved.append(file)
    require(preserved[0].parent != preserved[1].parent,
            'Separate full backup and restored Registry required')


def _physical_capacity(broker, study, view):
    # Include the named failed world: recorded != successfully completed. The
    # unchanged planning rate is conditional, not a physical occupancy promise.
    states = study['body']['manifest']['worlds']
    completed = sum(cell['states']['VERIFIED'] + cell['states']['INFORMATION_GAP']
                    for cell in view['summary']['cells'])
    remaining = len(states) - completed
    require(type(remaining) is int and 0 <= remaining <= len(states),
            'Remaining original world executions differ')
    committed = broker._db.execute('SELECT COALESCE(SUM(size),0) FROM blobs').fetchone()[0]
    committed += (broker.directory / 'registry.sqlite3').stat().st_size
    required = (6 * 1024**3 + 2 * committed
                + 3 * remaining * finite.PER_WORLD_PHYSICAL_PLANNING_BYTES)
    require(shutil.disk_usage(broker.directory).free >= required,
            'Physical capacity cannot hold planned terminal copies and reserves')


def consume_next(broker, bound_run):
    """Fetch, authenticate and consume at most one genuine owned action.

    Accept no caller-supplied state, action, amount or readiness verdict. A bad
    response or a retained failure stops the driver; neither causes a retry.
    """
    try:
        require(type(bound_run) is dict and set(bound_run) == FIELDS
                and bound_run['schema'] == SCHEMA, 'Exact sealed recovery run binding required')
        bound = decode(canonical(bound_run))
        owner = CalibrationRecovery(broker, bound['authority_binding'])
        require(_path(owner.binding['registry_path']) == broker.directory.resolve(),
                'Approved primary Registry differs')
        drivers = bound['driver_files']
        require(type(drivers) is dict and 2 <= len(drivers) <= 8
                and drivers.get(str(Path(__file__).resolve())) == _LOADED_SELF
                and drivers.get(str(Path(finite.__file__).resolve())) == finite._LOADED_SELF,
                'Loaded finite operator sources are not pinned')
        for name, expected in drivers.items():
            finite._pinned_file(_path(name), expected)
        identity = finite._identity(bound['recovery_id'])
        amendment = owner._owned(identity, AMENDMENT)
        require(digest(amendment) == finite._identity(bound['recovery_artifact_hash']),
                'Owned recovery amendment differs')
        ab = amendment['body']
        study = owner.runner._study(owner.binding['calibration_id'])
        body = study['body']
        require(ab['study_id'] == study['id'] and digest(study) == bound['artifact_hash']
                and digest(body['request']) == bound['request_hash']
                and digest(body['manifest']) == bound['manifest_hash']
                and body['assessment_source_footprint'] == bound['assessment_footprint']
                and body['source_footprint'] == bound['calculation_footprint']
                and ab['runtime_identity'] == bound['runtime_identity'],
                'Original immutable recovery study inputs or source identities differ')
        source = owner._owned(ab['source_id'], SOURCE)
        require(source['body']['footprint'] == bound['controller_footprint'],
                'Recovery controller footprint differs')
        input_record = owner._owned(ab['input_id'], INPUT)
        before = owner.inspect(identity)
        require(before['recovery_id'] == identity and before['study_id'] == study['id']
                and before['scientific_readiness'] is False and before['n_min'] is None,
                'Owned recovery view identity or authority differs')
        _prepared_custody(broker, bound, before, input_record)
        require(before['status'] in ('READY', 'RESOURCE_STOP', 'COMPLETE')
                and before['source_failure'] is None, 'Recovery requires a healthy owned state')
        # Inspect is descriptive. Intended execution performs the same strong
        # owned input/source/runtime/dependency check even at COMPLETE.
        with broker._mutex:
            original_input, original_amendment = owner._resolve(identity)
            owner._source_guard(owner._history(original_input, original_amendment))
        if before['status'] == 'COMPLETE':
            return {'request': None, 'view': before, 'result_id': None}
        _physical_capacity(broker, study, before)
        args = {'recovery_id': identity, 'expected_checkpoint': before['recovery_checkpoint']}
        if before['status'] == 'READY':
            action = {'op': 'advance_calibration_recovery', 'args': args}
            response = owner.advance(**args)
        else:
            action = {'op': 'continue_calibration_recovery', 'args': args}
            response = owner.continue_capacity(**args)
        after = owner.inspect(identity)
        require(after['study_id'] == before['study_id'] and after['recovery_id'] == identity
                and after['input_id'] == before['input_id']
                and after['original_checkpoint'] == before['original_checkpoint']
                and after['prepared_checkpoint'] == before['prepared_checkpoint'],
                'Post-call recovery identity/checkpoint differs; no automatic retry')
        old, new = before['budget'], after['budget']
        if action['op'] == 'advance_calibration_recovery':
            require(response == after and after['attempt_artifact_ids'][:-1]
                        == before['attempt_artifact_ids']
                    and len(after['attempt_artifact_ids']) == len(before['attempt_artifact_ids']) + 1
                    and after['continuation_ids'] == before['continuation_ids'],
                    'Advance response differs from retained single-attempt history; no automatic retry')
            result_id = after['attempt_artifact_ids'][-1]
            attempt = owner._owned(result_id, RESULT)['body']
            charge = attempt['settlement']
            # Preserve observed use in its settlement. Unknown use consumes at
            # least the full reservation in the owner's conservative ledger.
            charged_compute = charge['compute_ms'] if charge['usage_known'] else max(
                charge['compute_ms'], 600000)
            charged_storage = charge['storage_bytes'] if charge['usage_known'] else max(
                charge['storage_bytes'], finite.ATTEMPT_STORAGE_BYTES)
            require(attempt['recovery_id'] == identity and attempt['world_id'] == before['next_world_id']
                    and new['charged_compute_ms'] == old['charged_compute_ms'] + charged_compute
                    and new['charged_storage_bytes'] == old['charged_storage_bytes'] + charged_storage
                    and new['max_compute_ms'] == old['max_compute_ms']
                    and new['max_storage_bytes'] == old['max_storage_bytes'],
                    'Actual retained recovery attempt charges differ')
        else:
            grant = owner._owned(response['id'], GRANT)
            gb = grant['body']
            require(response == grant and gb['recovery_id'] == identity
                    and gb['expected_checkpoint'] == args['expected_checkpoint']
                    and after['attempt_artifact_ids'] == before['attempt_artifact_ids']
                    and after['continuation_ids'] == before['continuation_ids'] + [grant['id']],
                    'Continuation response differs from retained exact grant; no automatic retry')
            add_compute = min(finite.COMPUTE_TRANCHE_MS, finite.MAX_COMPUTE_MS - old['max_compute_ms'])
            add_storage = min(finite.STORAGE_TRANCHE_BYTES, finite.MAX_STORAGE_BYTES - old['max_storage_bytes'])
            require(gb['additional_compute_ms'] == add_compute and gb['additional_storage_bytes'] == add_storage
                    and new['charged_compute_ms'] == old['charged_compute_ms']
                    and new['charged_storage_bytes'] == old['charged_storage_bytes'] + finite.METADATA_BYTES
                    and new['max_compute_ms'] == old['max_compute_ms'] + add_compute
                    and new['max_storage_bytes'] == old['max_storage_bytes'] + add_storage
                    and new['continuation_count'] == old['continuation_count'] + 1,
                    'Paired continuation capacity or metadata settlement differs')
            result_id = grant['id']
        return {'request': action, 'view': after, 'result_id': result_id}
    except (KeyError, TypeError, ValueError) as exc:
        raise Invalid('Malformed finite recovery binding or response; no automatic retry') from exc
