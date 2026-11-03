"""Fixed option-A recovery of the retained scalar inventory; no new series.

Run only from the separately pinned recovery worktree. Preparation commits no
numerical attempt. Run mode consumes only its already sealed amendment identity.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import time
import uuid


REPOSITORY = Path(r'C:\Users\monoi\Documents\ChatGPT\Trading Research Framework')
WORK = REPOSITORY / '.trf-runtime/scalar-final-calibration-2026-11-02'
HOST = WORK / 'recovery-host'
PRIMARY = WORK / 'registry'
STUDY = '8ab8334f134f75145857d8c4975bdf514f854ec00d8680a7831cb9cea5241b96'
OLD_CHECKPOINT = '2e4c3cdea3e3778b54eab106c4fe4596dc933af40f001137e4e43054bd10efa7'
CONTROLLER = 'ef8781db4db7d531d1cf5d7d9133968c12ffb7d4d4456ae01662a1dfa9c286ef'
OPERATOR_HASH = 'b2294e34de142e2b5f326eb35063d8324b4e787b926f805aa053af7f65ca0c2f'
FINITE_HASH = 'cf51ab733329ddcf02fdd3f4884e4ba25cf2422e8f51d164ee26f3e9aae2d5ef'
APPROVAL_HASH = '7aee698e473f0d6106f635bc49627011d672887526940e5396d342fb210a3728'
ORIGINAL_APPROVAL_HASH = '0b0475cab83f5d0c839ee2de9afba67a3b83eb5eb933ca583e251ceead20647a'
KEY = 'scalar-final-2048-20261103-approved-recovery-once-v1'
SELF_HASH = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

if __name__ == '__main__':
    sys.path.insert(0, str(HOST))

from tools.calibration import finite_family as finite
from tools.calibration import finite_family_recovery as operator
from trading_researcher.binding import require, write_file
from trading_researcher.calibration_recovery import CalibrationRecovery, _path
from trading_researcher.codec import Invalid, MAX_BYTES, decode, digest
from trading_researcher.coordination import Broker
from trading_researcher.evaluation_plans import source_bundle, footprint
from trading_researcher.storage import _hash_file, restore_bundle


def utc():
    return datetime.now(timezone.utc).isoformat()


def _execution_state(flags):
    """Unchanged API body from retained run_once.py; alter no power-plan setting."""
    import ctypes
    from ctypes import wintypes

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    operation = kernel.SetThreadExecutionState
    operation.argtypes = [wintypes.DWORD]
    operation.restype = wintypes.DWORD
    return int(operation(flags))


def _read(path):
    return decode(_hash_file(path, collect=True, limit=MAX_BYTES)[2])


def save(name, value, *, frozen=False):
    path = WORK / name
    require(path.parent == WORK, 'Only fixed local operator records are supported')
    raw = (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode('utf-8')
    if frozen:
        if path.exists():
            require(path.read_bytes() == raw, 'Frozen recovery record differs: ' + name)
        else:
            write_file(path, raw)
    else:
        temporary = path.with_suffix(path.suffix + '.tmp')
        write_file(temporary, raw)
        temporary.replace(path)


def host_and_authority():
    require(Path(__file__).resolve() == HOST / 'tools/calibration/scalar_recovery_run.py',
            'Execute the fixed driver only from its isolated recovery host')
    require(_path(str(PRIMARY)) == PRIMARY and PRIMARY.drive.upper() == 'C:'
            and PRIMARY.is_dir() and (PRIMARY / 'registry.sqlite3').is_file()
            and (PRIMARY / 'operator.key').is_file(),
            'Existing approved C: primary required; never initialize a replacement')
    require(digest(footprint(source_bundle())) == CONTROLLER,
            'Qualified recovery controller source differs')
    for module, expected, relative in (
            (operator, OPERATOR_HASH, 'tools/calibration/finite_family_recovery.py'),
            (finite, FINITE_HASH, 'tools/calibration/finite_family.py')):
        require(Path(module.__file__).resolve() == HOST / relative,
                'Loaded finite operator belongs to another host')
        finite._pinned_file(_path(str(HOST / relative)), expected)
    finite._pinned_file(_path(str(Path(__file__).resolve())), SELF_HASH)
    base = HOST / 'docs/reviews/implementation-2026-10-25'
    approval = base / 'calibration-recovery-approval-2026-11-03.json'
    original = base / 'calibration-resource-approval-2026-11-02.json'
    finite._pinned_file(_path(str(approval)), APPROVAL_HASH)
    finite._pinned_file(_path(str(original)), ORIGINAL_APPROVAL_HASH)
    return {'schema': 'calibration-recovery-authority-binding/1',
        'calibration_id': STUDY, 'registry_path': str(PRIMARY),
        'assessment_host': str(WORK / 'host'),
        'approval_path': str(approval), 'approval_sha256': APPROVAL_HASH,
        'original_approval_path': str(original), 'original_approval_sha256': ORIGINAL_APPROVAL_HASH}


def _stopped():
    return any((WORK / name).exists() for name in (
        'recovery-stop-after-current-world.request', 'stop-after-current-world.request'))


def check_observed_prefix(view):
    """Deny forgotten history; observations cannot grant an unused allowance.

    This does not detect loss before observation or loss of both stores. Keep
    both the original observations and the new append-only observations intact.
    """
    try:
        require(view['study_id'] == STUDY, 'Observed study identity differs')
        attempts = view['attempt_artifact_ids']
        grants = view['continuation_ids']
        require(type(attempts) is list and type(grants) is list
                and len(set(attempts)) == len(attempts) and len(set(grants)) == len(grants),
                'Owned ordered attempt/grant history required')
        for name in ('observations.jsonl', 'recovery-observations.jsonl'):
            path = WORK / name
            if not path.exists():
                continue
            with path.open('rb') as stream:
                while raw := stream.readline(MAX_BYTES + 1):
                    require(len(raw) <= MAX_BYTES, 'Observed record exceeds the existing envelope')
                    item = decode(raw)
                    require(type(item) is dict and item['study_id'] == STUDY,
                            'Observed study identity differs')
                    if name == 'observations.jsonl':
                        last = item['last_attempt_id']
                        require(last is None or last in attempts, 'Registry forgot an original observed attempt')
                    else:
                        for key in ('recovery_id', 'input_id', 'original_checkpoint', 'prepared_checkpoint'):
                            require(item[key] == view[key], 'Observed recovery identity differs: ' + key)
                        if item.get('action') == 'dispatch_intent':
                            require(finite._identity(item['recovery_checkpoint'])
                                    != view['recovery_checkpoint'],
                                    'Unresolved dispatch intent or stale restored checkpoint; diagnose before reuse')
                        prior = item['attempt_artifact_ids']
                        require(type(prior) is list and attempts[:len(prior)] == prior,
                                'Registry forgot or reordered an observed recovery attempt')
                    prior = item['continuation_ids']
                    require(type(prior) is list and grants[:len(prior)] == prior,
                            'Registry forgot or reordered an observed continuation')
    except (KeyError, TypeError, ValueError) as exc:
        raise Invalid('Malformed or contradicted observed prefix; never reset recovery automatically') from exc


def observe(action, view, started, result_id=None):
    item = {key: deepcopy(view[key]) for key in (
        'study_id', 'recovery_id', 'input_id', 'original_checkpoint', 'prepared_checkpoint',
        'recovery_checkpoint', 'attempt_artifact_ids', 'continuation_ids')}
    item.update(at_utc=utc(), pid=os.getpid(), action=action, result_id=result_id,
        status=view['status'], driver_sha256=SELF_HASH, operator_sha256=OPERATOR_HASH,
        wall_elapsed_ms=int((time.monotonic() - started) * 1000), budget=view['budget'])
    with (WORK / 'recovery-observations.jsonl').open('ab') as stream:
        stream.write((json.dumps(item, ensure_ascii=False) + '\n').encode('utf-8'))
        stream.flush()
        os.fsync(stream.fileno())
    save('recovery-latest.json', {'observation': item, 'view': view})
    print(json.dumps({k: v for k, v in item.items()
        if k not in ('attempt_artifact_ids', 'budget')}), flush=True)


def _restored_view(view):
    return {key: value for key, value in view.items() if key not in ('status', 'next_world_id')}


def _full_copies(broker, owner, recovery_id, label):
    committed = broker._db.execute('SELECT COALESCE(SUM(size),0) FROM blobs').fetchone()[0]
    committed += (PRIMARY / 'registry.sqlite3').stat().st_size
    require(shutil.disk_usage(PRIMARY).free >= 6 * 1024**3 + 2 * committed,
            'Capacity cannot hold both complete copies and reserve')
    before = owner.inspect(recovery_id)
    backup = WORK / (label + '-backup')
    restored = WORK / (label + '-restore')
    require(not backup.exists() and not restored.exists(), 'Never overwrite a preserved recovery copy')
    require(broker.call(broker.admin_token, 'backup_bundle', destination=str(backup))['status'] == 'PASS',
            'Complete recovery backup failed')
    require(restore_bundle(backup, restored, PRIMARY / 'operator.key')['status'] == 'PASS',
            'Complete recovery restore failed')
    recovered = None
    try:
        recovered = Broker(restored)
        require(recovered.call(recovered.admin_token, 'verify')['status'] == 'PASS',
                'Restored Registry integrity failed')
        copied_authority = {**owner.binding, 'registry_path': str(restored)}
        reader = CalibrationRecovery(recovered, copied_authority)
        after = reader.inspect(recovery_id)
        require(after['status'] == 'RESTORED_COPY' and after['next_world_id'] is None
                and _restored_view(after) == _restored_view(before),
                'Restored complete recovery accounting/count interpretation differs')
        amendment = owner._owned(recovery_id, 'calibration-recovery-amendment/1')
        for identity in (STUDY, recovery_id, amendment['body']['input_id'], amendment['body']['source_id']):
            require(recovered.call(recovered.admin_token, 'get_artifact', artifact_id=identity)
                    == broker.call(broker.admin_token, 'get_artifact', artifact_id=identity),
                    'Restored original/recovery capsule differs')
    finally:
        if recovered is not None:
            recovered.close()
    return {'status': 'PASS', 'backup': str(backup), 'restored': str(restored),
        'backup_manifest': {'path': str(backup / 'manifest.json'),
            'sha256': _hash_file(backup / 'manifest.json', limit=None)[0]},
        'restored_database': {'path': str(restored / 'registry.sqlite3'),
            'sha256': _hash_file(restored / 'registry.sqlite3', limit=None)[0]}}


def prepare(broker):
    require(not _stopped(), 'Operator stop requested before recovery preparation')
    require(not (WORK / 'recovery-prepare-intent.json').exists()
            and not (WORK / 'recovery-bound-run.json').exists(),
            'Existing intent or sealed binding forbids another automatic preparation')
    authority = host_and_authority()
    owner = CalibrationRecovery(broker, authority)
    original = owner._original(owner._approval_bytes())
    require(original['study']['id'] == STUDY and original['history'].checkpoint == OLD_CHECKPOINT,
            'Exact approved original terminal prefix required')
    require(shutil.disk_usage(PRIMARY).free >= 60 * 1024**3, 'Initial60GiB capacity unavailable')
    save('recovery-prepare-intent.json', {'schema': 'scalar-recovery-prepare-intent/1',
        'study_id': STUDY, 'original_checkpoint': OLD_CHECKPOINT, 'key': KEY,
        'controller_footprint_sha256': CONTROLLER, 'driver_sha256': SELF_HASH,
        'recorded_at_utc': utc(), 'authority': 'DENIAL_ONLY_NOT_AN_ALLOWANCE'}, frozen=True)
    amendment = owner.prepare(KEY)
    view = owner.inspect(amendment['id'])
    require(view['status'] == 'READY' and len(view['attempt_artifact_ids']) == 20
            and len(view['continuation_ids']) == 1
            and view['recovery_checkpoint'] == view['prepared_checkpoint']
            and view['budget']['charged_compute_ms'] == 5029797,
            'Prepared amendment must preserve all20 original attempts and one grant')
    check_observed_prefix(view)
    operator._physical_capacity(broker, original['study'], view)
    copied = _full_copies(broker, owner, amendment['id'], 'recovery-prepared')
    study = original['study']
    source = owner._owned(amendment['body']['source_id'], 'calibration-recovery-source/1')
    proof = {'schema': 'prepared-family-amendment-recovery/1', 'status': 'PASS',
        'study_id': STUDY, 'recovery_id': amendment['id'], 'input_id': view['input_id'],
        'artifact_hash': digest(study), 'recovery_artifact_hash': digest(amendment),
        'original_checkpoint': OLD_CHECKPOINT, 'prepared_checkpoint': view['prepared_checkpoint'],
        'initial_attempt_ids': view['attempt_artifact_ids'], 'initial_continuation_ids': view['continuation_ids'],
        'charged_compute_ms': view['budget']['charged_compute_ms'],
        'charged_storage_bytes': view['budget']['charged_storage_bytes'],
        'backup_manifest': copied['backup_manifest'], 'restored_database': copied['restored_database']}
    save('recovery-prepared-proof.json', proof, frozen=True)
    binding = {'schema': operator.SCHEMA, 'authority_binding': authority,
        'recovery_id': amendment['id'], 'artifact_hash': digest(study),
        'recovery_artifact_hash': digest(amendment), 'request_hash': digest(study['body']['request']),
        'manifest_hash': digest(study['body']['manifest']),
        'assessment_footprint': study['body']['assessment_source_footprint'],
        'calculation_footprint': study['body']['source_footprint'],
        'controller_footprint': source['body']['footprint'],
        'runtime_identity': amendment['body']['runtime_identity'],
        'recovery_path': str(WORK / 'recovery-prepared-proof.json'),
        'recovery_sha256': _hash_file(WORK / 'recovery-prepared-proof.json', limit=None)[0],
        'driver_files': {str(Path(__file__).resolve()): SELF_HASH,
            str(Path(operator.__file__).resolve()): OPERATOR_HASH,
            str(Path(finite.__file__).resolve()): FINITE_HASH}}
    # Authenticate this proof without dispatching a numerical attempt or grant.
    input_record = owner._owned(view['input_id'], 'calibration-recovery-input/1')
    operator._prepared_custody(broker, binding, view, input_record)
    save('recovery-bound-run.json', binding, frozen=True)
    return binding, view


def run(broker, binding, started):
    authority = host_and_authority()
    require(type(binding) is dict and set(binding) == operator.FIELDS
            and binding['schema'] == operator.SCHEMA and binding['authority_binding'] == authority
            and binding['recovery_path'] == str(WORK / 'recovery-prepared-proof.json'),
            'Original sealed recovery binding required; run never prepares another amendment')
    for module, expected in ((operator, OPERATOR_HASH), (finite, FINITE_HASH)):
        require(binding['driver_files'].get(str(Path(module.__file__).resolve())) == expected,
                'Sealed finite operator source differs')
    require(binding['driver_files'].get(str(Path(__file__).resolve())) == SELF_HASH,
            'Sealed loaded driver source differs')
    owner = CalibrationRecovery(broker, authority)
    owner.recover_incomplete()
    view = owner.inspect(binding['recovery_id'])
    check_observed_prefix(view)
    require(view['status'] in ('READY', 'RESOURCE_STOP', 'COMPLETE'),
            'Retained recovery failure requires diagnosis, never another automatic attempt')
    observe('started_or_same_amendment_resumed', view, started)
    for _ in range(2049 + 179 + 1):
        check_observed_prefix(view)
        if _stopped():
            return 'STOPPED_AT_SAFE_BOUNDARY_BY_OPERATOR', view
        if view['status'] != 'COMPLETE':
            # Durable denial evidence precedes reservation, including a crash
            # before its outcome can be observed. It never grants an attempt.
            observe('dispatch_intent', view, started)
        result = operator.consume_next(broker, binding)
        view = result['view']
        observe('complete' if result['request'] is None else result['request']['op'],
                view, started, result_id=result['result_id'])
        require(view['status'] in ('READY', 'RESOURCE_STOP', 'COMPLETE'),
                'New recovery failure retained; stop without retry')
        if result['request'] is None:
            require(view['status'] == 'COMPLETE', 'No-action response is not a completed inventory')
            return 'COMPLETE_FIXED_INVENTORY_COUNTS_ONLY', view
    raise RuntimeError('Finite action bound exhausted; no renewed recovery authority')


def terminal_copies(broker, session):
    binding = _read(WORK / 'recovery-bound-run.json')
    owner = CalibrationRecovery(broker, binding['authority_binding'])
    return _full_copies(broker, owner, binding['recovery_id'], 'recovery-terminal-' + session)


def main():
    require(len(sys.argv) == 2 and sys.argv[1] in ('prepare', 'run'),
            'Only the fixed prepare/run modes are supported')
    phase = sys.argv[1]
    started = time.monotonic()
    session = uuid.uuid4().hex
    broker = None
    view = None
    binding = None
    original_error = None
    power_attempted = False
    terminal = {'schema': 'scalar-recovery-driver-terminal/1', 'session': session,
        'phase': phase, 'started_at_utc': utc(), 'driver_sha256': SELF_HASH,
        'operator_sha256': OPERATOR_HASH, 'scientific_readiness': False, 'n_min': None}
    try:
        host_and_authority()
        power_attempted = True
        require(bool(_execution_state(0x80000001)), 'Windows execution-state acquisition failed')
        broker = Broker(PRIMARY)
        if phase == 'prepare':
            if _stopped():
                terminal['status'] = 'STOPPED_AT_SAFE_BOUNDARY_BY_OPERATOR'
            else:
                binding, view = prepare(broker)
                terminal['status'] = 'PREPARED_AMENDMENT_AND_FULL_RESTORE_NO_NEW_ATTEMPTS'
        else:
            binding = _read(WORK / 'recovery-bound-run.json')
            terminal['status'], view = run(broker, binding, started)
        terminal['view'] = view
    except BaseException as exc:
        original_error = exc
        terminal.update(status='STOPPED_RETAINED_STATE', failure_type=type(exc).__name__,
                        failure=str(exc)[:2000])
        if broker is not None and binding is not None:
            try:
                owner = CalibrationRecovery(broker, binding['authority_binding'])
                terminal['view'] = owner.inspect(binding['recovery_id'])
            except BaseException as diagnostic:
                terminal['inspection_failure'] = type(diagnostic).__name__ + ': ' + str(diagnostic)[:1000]
        raise
    finally:
        if broker is not None:
            if phase == 'run' and binding is not None:
                try:
                    terminal['complete_terminal_copies'] = terminal_copies(broker, session)
                except BaseException as exc:
                    terminal['terminal_copy_failure'] = type(exc).__name__ + ': ' + str(exc)[:1500]
            try:
                broker.close()
            except BaseException as exc:
                terminal['close_failure'] = type(exc).__name__ + ': ' + str(exc)[:1000]
        if power_attempted:
            try:
                require(bool(_execution_state(0x80000000)), 'Windows execution-state release failed')
            except BaseException as exc:
                terminal['power_clear_failure'] = type(exc).__name__ + ': ' + str(exc)[:1000]
        failed = any(key in terminal for key in ('terminal_copy_failure', 'close_failure', 'power_clear_failure'))
        if failed:
            terminal['count_status_before_operational_failure'] = terminal.get('status')
            terminal['status'] = 'STOPPED_OPERATIONAL_CLOSEOUT_FAILED'
        terminal.update(finished_at_utc=utc(), wall_seconds=time.monotonic() - started)
        publication_error = None
        try:
            save('recovery-terminal-' + session + '.json', terminal, frozen=True)
        except BaseException as exc:
            publication_error = exc
            terminal['receipt_failure'] = type(exc).__name__ + ': ' + str(exc)[:1000]
        try:
            print(json.dumps({k: v for k, v in terminal.items() if k != 'view'}), flush=True)
        except BaseException as exc:
            if publication_error is None:
                publication_error = exc
        # Closing evidence channels must never mask the original work failure.
        # If both sinks are unavailable, their durable delivery is unverified;
        # the existing Registry reservation/settlement is still authoritative.
        if publication_error is not None and original_error is None:
            raise publication_error
        if failed and original_error is None:
            raise RuntimeError('Recovery closeout failed; repair retained state without rerunning worlds')


if __name__ == '__main__':
    main()
