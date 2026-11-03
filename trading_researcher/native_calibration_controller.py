"""Finite D100 host caller: existing numerical/storage owners, one shared ledger.

The estimates are explicit operational planning rules, not confidence bounds or
scientific thresholds. Workers never receive a Broker capability. External
observations only deny stale restoration; they cannot create spending authority.
"""
from collections import defaultdict, deque
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import math
import os
from pathlib import Path
import shutil
import threading
import time
import uuid

from .binding import require
from .codec import Invalid, canonical, decode, digest, integer
from .errors import Conflict
from .evaluation_plans import source_bundle, footprint
from .native_calibration_resources import (
    META, MAX_COMPUTE_MS, MAX_STORAGE_BYTES, MAX_ATTEMPT_STORAGE_BYTES,
    COMPUTE_TRANCHE_MS, STORAGE_TRANCHE_BYTES, POOL)
from .native_calibration_runs import (
    NativeCalibrationResources, NativeCalibrationAttempts, NativeCalibrationCopies,
    NativeCalibrationReferences, NativeCalibrationCorrectionReferences)
from .native_study_runs import NativeFamilyCalibrationStudies
from .storage import _durable_file


CONTROL_BYTES = 16 * META
WALL_LIMIT_MS = 24 * 60 * 60 * 1000
FREE_FLOOR = 20 * 1024**3
READINESS_CUTOFF = '2026-11-04T22:59:59+00:00'
DEVELOPMENT_ID = '37208f834cf223fc3a94a4aa55ddf620d40c6b5f42bbd956d0936e69d507c9ab'


def policy():
    return {'schema': 'native-calibration-controller-policy/1', 'max_workers': 6,
        'metadata_bytes_prepaid': CONTROL_BYTES, 'order': 'replicate_then_target_spec_pattern_id',
        'acceptance_order': 'parallel_then_serial_fixed_old_corpus',
        'acceptance_deadline_ms': 600000,
        'retry_order': 'due_retry_before_unstarted', 'deadline_multiplier': 2,
        'cleanup_reservation_ms': 30000, 'forecast_checkpoint_worlds': 64,
        'forecast_wall_limit_ms': WALL_LIMIT_MS, 'retry_planning_floor': {'num': 1, 'den': 32},
        'physical_planning_factor': {'num': 5, 'den': 4},
        'forecast_scope': 'operational_estimate_not_confidence_bound_or_runtime_guarantee',
        'process_control': {'schema': 'native-study-process-control/1',
                            'library_threads': 1, 'priority': 'BELOW_NORMAL'}}


def round_robin(worlds):
    require(type(worlds) is list and len({w['id'] for w in worlds}) == len(worlds),
            'Distinct fixed native worlds required')
    return [w['id'] for w in sorted(worlds, key=lambda w:
        (w['replicate'], w['time_rows'], w['spec_index'], w['pattern_index'], w['id']))]


def retained_bytes(body):
    values = {}
    for item in body.get('output_blobs', {}).values():
        previous = values.setdefault(item['sha256'], integer(item['size'], 'Retained output size'))
        require(previous == item['size'], 'Retained output descriptor size differs')
    # A fresh future seed need not share CAS bytes with the reference corpus.
    # Include a DB/control planning reserve per attempt, not reference CAS delta.
    return sum(values.values()) + META


def forecast(manifest, attempts, pending, *, fallback, elapsed_ms, final_elapsed_ms,
             deadline_ms, charged_storage_bytes, copy_overhead_ms, primary_bytes,
             prepared_copies, terminal_copies):
    for name, value in locals().copy().items():
        if name not in ('manifest', 'attempts', 'pending', 'fallback'):
            integer(value, name)
    require(deadline_ms > 0, 'Positive frozen native deadline required')
    worlds = {w['id']: w for w in manifest['worlds']}
    require(len(worlds) == len(manifest['worlds']) and len({w['time_rows'] for w in worlds.values()}) == 1,
            'Forecast requires the fixed single-target final inventory')
    by_world, live, cells = defaultdict(list), {}, defaultdict(list)
    for world in worlds.values():
        cells[f"{world['spec_index']}/{world['pattern_index']}"].append(world['id'])
    seen = set()
    for body in attempts:
        identity = body['world_id']
        require(identity in worlds and body['attempt_id'] not in seen
                and body['resource_state'] in ('COMPLETE', 'KNOWN_TIMEOUT')
                and body['settlement']['usage_known'] is True, 'Unknown or failed native forecast input')
        seen.add(body['attempt_id'])
        by_world[identity].append(body)
    for item in pending:
        identity = item['task_id']
        require(item['phase'] == 'final' and identity in worlds and identity not in live,
                'Pending native forecast inventory differs')
        live[identity] = item
    def whole(body):
        return integer(body.get('whole_call_ms', body['settlement']['compute_ms']), 'Whole native attempt time')
    for body in attempts:
        require(type(body.get('timing_measured', True)) is bool, 'Explicit native timing provenance required')
    measured_attempts = [b for b in attempts if b.get('timing_measured', True)]
    total_compute = sum(whole(b) for b in measured_attempts)
    measured = bool(measured_attempts)
    require(not measured or final_elapsed_ms > 0 and total_compute > 0, 'Measured final wall denominator unavailable')
    parallel = (min(Fraction(6), Fraction(total_compute, final_elapsed_ms)) if measured
                else Fraction(1) if attempts else Fraction(6))
    work, logical, growth, terminal, unavailable, contingency = Fraction(), charged_storage_bytes, 0, 0, 0, 0
    details = {}
    for key, ids in sorted(cells.items()):
        require(key in fallback, 'Actual parallel reference fallback missing for a final cell')
        basis = fallback[key]
        for field in ('compute_ms', 'storage_bytes', 'retained_bytes'):
            integer(basis[field], 'Parallel reference ' + field, 1)
        records = [body for identity in ids for body in by_world[identity]]
        duration = (Fraction(sum(whole(b) for b in records), len(records))
                    if records else Fraction(basis['compute_ms']))
        storage = max([basis['storage_bytes']] + [b['settlement']['storage_bytes'] for b in records])
        physical = max([basis['retained_bytes']] + [retained_bytes(b) for b in records])
        unstarted = first_live = retry_due = retry_live = first_timeouts = first_attempts = 0
        for identity in ids:
            history = by_world[identity]
            require(len(history) <= 2 and (len(history) < 2 or history[0]['resource_state'] == 'KNOWN_TIMEOUT'),
                    'Native forecast world has an invalid retry history')
            if history:
                first_attempts += 1
                first_timeouts += history[0]['resource_state'] == 'KNOWN_TIMEOUT'
            if history and (history[-1]['resource_state'] == 'COMPLETE' or len(history) == 2):
                require(identity not in live, 'Terminal native forecast world still pending')
                terminal += 1
                unavailable += history[-1]['resource_state'] != 'COMPLETE'
            elif history:
                retry_live += identity in live
                retry_due += identity not in live
            elif identity in live:
                first_live += 1
            else:
                unstarted += 1
        first = unstarted + first_live
        rate = max(Fraction(1, 32), Fraction(first_timeouts, first_attempts) if first_attempts else Fraction())
        extra = math.ceil(rate * first)
        contingency += extra
        reservation = deadline_ms + 30000
        cell_work = duration * first + reservation * (retry_due + retry_live + extra)
        work += cell_work
        # Already charged full in-flight envelopes remain charged. Do not add
        # their expected normal cost a second time, or refund their reservation.
        logical += storage * unstarted + MAX_ATTEMPT_STORAGE_BYTES * (retry_due + extra)
        growth += math.ceil(Fraction(5, 4) * physical) * (first + retry_due + retry_live + extra)
        details[key] = {'unstarted': unstarted, 'first_inflight': first_live,
            'retry_due': retry_due, 'retry_inflight': retry_live, 'future_retry_reserve': extra,
            'mean_attempt_ms': {'num': duration.numerator, 'den': duration.denominator},
            'logical_per_first_bytes': storage, 'physical_per_attempt_bytes': physical}
    wall = elapsed_ms + math.ceil(work / parallel) + copy_overhead_ms
    scratch = 6 * MAX_ATTEMPT_STORAGE_BYTES + CONTROL_BYTES
    required = (FREE_FLOOR + growth + scratch + prepared_copies * primary_bytes
                + terminal_copies * (primary_bytes + growth))
    return {'schema': 'native-calibration-forecast/1', 'total_wall_ms': wall,
        'time_exceeds_24h': wall > WALL_LIMIT_MS, 'logical_forecast_bytes': logical,
        'required_free_bytes': required, 'forecast_growth_bytes': growth,
        'terminal_worlds': terminal, 'unavailable_worlds': unavailable,
        'effective_parallelism': {'num': parallel.numerator, 'den': parallel.denominator},
        'effective_parallelism_measured': measured, 'future_retry_reserve_worlds': contingency,
        'timing_missing_attempts': len(attempts) - len(measured_attempts),
        'per_cell': details, 'scientific_readiness': False, 'scope': policy()['forecast_scope']}


class NativeCalibrationController:
    def __init__(self, broker, run_directory, *, driver_file=None):
        self.broker = broker
        self.directory = Path(run_directory).resolve()
        self.driver_file = Path(driver_file or Path(__file__).resolve().parents[1]
                                / 'tools/calibration/native_parallel.py').resolve()
        require(not self.directory.is_relative_to(broker.directory), 'Native control files must be external to Registry')
        self.resources = NativeCalibrationResources(broker)
        self.caller = NativeCalibrationAttempts(broker)
        self.copies = NativeCalibrationCopies(broker)
        self.cancel = threading.Event()
        self.binding = None
        self._journal_bytes = 0
        self._timing_values = {}
        self._seen_results = set()
        self._final_bodies = {}

    def _path(self, name):
        return self.directory / name

    def _metadata_size(self):
        return sum(p.stat().st_size for p in self.directory.iterdir() if p.is_file())

    def _write(self, name, value):
        raw = canonical(value).encode()
        require(self._metadata_size() + len(raw) <= CONTROL_BYTES, 'Prepaid native control metadata is exhausted')
        _durable_file(self._path(name), raw)

    def _current(self, token, pool_id):
        self.broker._binding_owner(token)
        pool = self.resources._pool(pool_id)
        self.resources._current(pool)
        require(self.binding is not None and self.binding['pool_id'] == pool_id
                and self.binding['registry_path'] == str(self.broker.directory)
                and self.binding['run_directory'] == str(self.directory)
                and self.binding['driver_path'] == str(self.driver_file)
                and self.binding['source_footprint'] == pool['body']['source_footprint']
                and self.binding['policy'] == policy()
                and self.binding['driver_sha256'] == hashlib.sha256(self.driver_file.read_bytes()).hexdigest(),
                'Native controller binding, source, policy or location differs')
        if 'source_correction' in pool['body']:
            correction = pool['body']['source_correction']
            require(correction['controller_directory'] == str(self.directory)
                    and correction['operational_start_utc'] == self.binding['operational_start_utc'],
                    'Correction controller directory and original clock are permanently bound')
        return pool, self.resources._history(pool)

    def prepare(self, token, key, *, correction_args=None):
        b, r = self.broker, self.resources
        with b._mutex:
            b._binding_owner(token)
            path = self._path('binding.json')
            if path.exists():
                self.binding = decode(path.read_bytes())
                self.validate(token, self.binding['pool_id'])
                pool = r._pool(self.binding['pool_id'])
                if correction_args is not None:
                    require(pool['body'].get('source_correction', {}).get('request') == correction_args,
                            'Existing controller binds another source correction')
                return pool
            require(not self.directory.exists(), 'Missing native binding forbids automatic preparation/reset')
            operational_start = datetime.now(timezone.utc).isoformat()
            require(datetime.now(timezone.utc) <= datetime.fromisoformat(READINESS_CUTOFF),
                    'D100 integration readiness deadline passed; stop and report')
            if correction_args is None:
                pool = r.prepare(token, {'key': key})
            else:
                require(correction_args.get('key') == key, 'Controller source correction key differs')
                pool = r.correct_source(token, correction_args)
            r._current(pool)
            correction = pool['body'].get('source_correction')
            if correction is not None:
                operational_start = correction['operational_start_utc']
                require(correction['controller_directory'] == str(self.directory),
                        'Correction controller directory is permanently bound')
            history = r._history(pool)
            task = pool['body']['setup_tasks']['controller_source']
            require(('setup', task) not in history.records and not history.pending,
                    'Existing native source work cannot be automatically rebound')
            if correction is not None:
                # Claim the one fixed external location before spending. A
                # crash before binding leaves a closed, visible boundary.
                self.directory.mkdir(parents=True, exist_ok=False)
            started = time.monotonic()
            reservation = r.reserve(token, {'pool_id': pool['id'], 'phase': 'setup', 'task_id': task,
                'attempt_id': uuid.uuid4().hex, 'expected_checkpoint': history.checkpoint})
            raw = self.driver_file.read_bytes()
            driver = b._stage_blob_bytes(raw)
            binding = {'schema': 'native-calibration-controller-binding/1', 'pool_id': pool['id'],
                'registry_path': str(b.directory), 'run_directory': str(self.directory),
                'driver_path': str(self.driver_file), 'driver_sha256': driver['sha256'],
                'source_footprint': pool['body']['source_footprint'], 'policy': policy(),
                'operational_start_utc': operational_start,
                'scientific_readiness': False}
            body = {'resource_pool_id': pool['id'], 'phase': 'setup', 'task_id': task,
                'attempt_id': reservation['attempt_id'], 'resource_state': 'COMPLETE',
                'currency_checked': True, 'failure': None, 'failures': [], 'output_blobs': {'driver': driver},
                'controller_binding': binding,
                'settlement': {'attempt_id': reservation['attempt_id'],
                    'compute_ms': max(1, math.ceil((time.monotonic() - started) * 1000)),
                    'storage_bytes': 2 * len(raw) + META + CONTROL_BYTES, 'usage_known': True}}
            result = r.settle(token, pool['id'], body, blob_refs=[driver])
            require(result['body']['resource_state'] == 'COMPLETE', 'Native controller source setup failed')
            if correction is None:
                self.directory.mkdir(parents=True, exist_ok=False)
            self.binding = {**binding, 'source_result_id': result['id']}
            self._write('binding.json', self.binding)
            _durable_file(self._path('observations.jsonl'), b'')
            self._journal_bytes = 0
            return pool

    def _observe(self, token, pool_id, operation, kind, state, *, request_hash,
                 attempt_id=None, result_id=None, whole_call_ms=None):
        with self.broker._mutex:
            _, history = self._current(token, pool_id)
            tip = NativeCalibrationCopies._tip(self.broker._db)
            record = {'schema': 'native-calibration-controller-observation/1',
                'binding_id': self.binding['source_result_id'], 'operation': operation, 'kind': kind,
                'state': state, 'event_prefix': tip, 'resource_checkpoint': history.checkpoint,
                'request_hash': request_hash, 'attempt_id': attempt_id, 'result_id': result_id,
                'whole_call_ms': whole_call_ms}
            raw = (canonical(record) + '\n').encode()
            require(len(raw) <= 2048 and self._metadata_size() + len(raw) <= CONTROL_BYTES,
                    'Prepaid native observations exceed their fixed bound')
            path = self._path('observations.jsonl')
            require(path.is_file() and path.stat().st_size == self._journal_bytes,
                    'Native observation file disappeared or changed outside its owner')
            with path.open('ab') as stream:
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
            self._journal_bytes += len(raw)
            if kind == 'execute' and state == 'ACK':
                self._timing_values[attempt_id] = whole_call_ms
            return record

    def validate(self, token, pool_id):
        b = self.broker
        with b._mutex:
            pool, history = self._current(token, pool_id)
            require(decode(self._path('binding.json').read_bytes()) == self.binding,
                    'Native external binding changed')
            source = b._artifact(self.binding['source_result_id'])
            require(source['body']['controller_binding'] == {k: v for k, v in self.binding.items()
                    if k != 'source_result_id'} and source['body']['resource_state'] == 'COMPLETE',
                    'Native controller binding is not its charged source work')
            b._require_usable_dependencies(source['id'])
            require(self._metadata_size() <= CONTROL_BYTES, 'Native control metadata exceeds prepaid capacity')
            pending, operations, previous_seq = {}, set(), 0
            self._timing_values = {}
            proofs = self._operation_proofs(pool_id)
            with self._path('observations.jsonl').open('rb') as stream:
                for raw in stream:
                    require(len(raw) <= 2048 and raw.endswith(b'\n'), 'Truncated or oversized native observation')
                    item = decode(raw)
                    require(type(item) is dict and set(item) == {'schema', 'binding_id', 'operation', 'kind',
                            'state', 'event_prefix', 'resource_checkpoint', 'request_hash', 'attempt_id',
                            'result_id', 'whole_call_ms'}
                            and item['schema'] == 'native-calibration-controller-observation/1'
                            and item['binding_id'] == source['id']
                            and item['kind'] in ('reserve', 'execute', 'grant', 'setup', 'inventory', 'copy_booking'),
                            'Native observation binding or shape differs')
                    prefix = item['event_prefix']
                    require(type(prefix) is dict and set(prefix) == {'seq', 'hash'}
                            and type(prefix['seq']) is int and prefix['seq'] >= previous_seq,
                            'Native observations reordered their actual prefixes')
                    previous_seq = prefix['seq']
                    row = b._db.execute('SELECT hash FROM events WHERE seq=?', (prefix['seq'],)).fetchone()
                    require(row is not None and row[0] == prefix['hash'],
                            'Registry lost an observed native prefix; stale restoration cannot authorize work')
                    key = item['operation']
                    if item['state'] == 'INTENT':
                        require(key not in operations and item['result_id'] is None
                                and item['whole_call_ms'] is None, 'Duplicate or completed native operation intent')
                        operations.add(key)
                        pending[key] = item
                    else:
                        require(item['state'] == 'ACK' and key in pending
                                and all(item[field] == pending[key][field] for field in
                                        ('kind', 'request_hash', 'attempt_id')),
                                'Native observation acknowledgement differs')
                        proof = self._proved_result(proofs, item)
                        require(proof is not None and proof == item['result_id'],
                                'Native acknowledgement is not its actual owned committed transition')
                        if item['whole_call_ms'] is not None:
                            require(item['kind'] == 'execute', 'Only numerical calls have whole-call timing')
                            integer(item['whole_call_ms'], 'Observed whole-call timing', 1)
                        if item['kind'] == 'execute':
                            self._timing_values[item['attempt_id']] = item['whole_call_ms']
                        pending.pop(key)
            self._journal_bytes = self._path('observations.jsonl').stat().st_size
            for operation, item in pending.items():
                result = self._proved_result(proofs, item)
                require(result is not None, 'Unresolved native intent or stale restore requires diagnosis; never repeat work')
                self._observe(token, pool_id, operation, item['kind'], 'ACK', request_hash=item['request_hash'],
                              attempt_id=item['attempt_id'], result_id=result)
            return self.binding

    def _operation_proofs(self, pool_id):
        """One pass over existing events; no second ledger or per-line replay."""
        from .native_calibration_resources import RESERVE_FIELDS
        proofs = {}
        tasks = self.resources._pool(pool_id)['body']['setup_tasks']
        names = {value: key for key, value in tasks.items()}
        for seq, raw in self.broker._db.execute('SELECT seq,envelope FROM events ORDER BY seq'):
            event = decode(raw); d = event['details']
            if event['actor'] != 'controller' or d.get('pool_id') != pool_id:
                continue
            if event['action'] == 'native_calibration_reserved':
                request = {key: d['reservation'][key] for key in RESERVE_FIELDS}
                proofs[('reserve', digest(request))] = (request['attempt_id'], seq, request['attempt_id'])
            elif event['action'] == 'native_calibration_continued':
                item = self.broker._artifact(d['artifact_id'])
                proofs[('grant', digest(item['body']['request']))] = (item['id'], seq, None)
            elif event['action'] == 'native_calibration_inventory_bound':
                item = self.broker._artifact(d['artifact_id'])
                request = {'request': item['body']['request'], 'input_id': item['body'].get('input_id')}
                proofs[('inventory', digest(request))] = (item['id'], seq, None)
            elif event['action'] == 'native_calibration_settled':
                item = self.broker._artifact(d['artifact_id']); body = item['body']
                proofs[('execute', digest({'attempt_id': body['attempt_id']}))] = (item['id'], seq, body['attempt_id'])
                if body['phase'] == 'setup':
                    setup = {'setup': names[body['task_id']], 'attempt_id': body['attempt_id']}
                    proofs[('setup', digest(setup))] = (item['id'], seq, body['attempt_id'])
                booking = body.get('copy_metadata_booking')
                if booking:
                    proofs[('copy_booking', digest({'pool_id': pool_id, 'label': booking['label']}))] = (item['id'], seq, None)
        return proofs

    @staticmethod
    def _proved_result(proofs, item):
        proof = proofs.get((item['kind'], item['request_hash']))
        if proof is None:
            return None
        identity, seq, attempt_id = proof
        require(item['attempt_id'] == attempt_id and
                (item['state'] != 'ACK' or seq <= item['event_prefix']['seq']),
                'Native proof belongs to another attempt or a later committed prefix')
        return identity

    def _transition(self, token, pool_id, kind, request, function, *, attempt_id=None):
        operation, request_hash = uuid.uuid4().hex, digest(request)
        self._observe(token, pool_id, operation, kind, 'INTENT',
                      request_hash=request_hash, attempt_id=attempt_id)
        result = function()
        identity = result.get('id', result.get('attempt_id'))
        self._observe(token, pool_id, operation, kind, 'ACK', request_hash=request_hash,
                      attempt_id=attempt_id, result_id=identity)
        return result

    def _grant(self, token, pool, phase, task):
        _, history = self._current(token, pool['id'])
        request = {'key': 'native-grant-' + history.checkpoint, 'pool_id': pool['id'],
            'phase': phase, 'task_id': task, 'expected_checkpoint': history.checkpoint,
            'additional_compute_ms': min(COMPUTE_TRANCHE_MS, MAX_COMPUTE_MS - history.allocated_compute),
            'additional_storage_bytes': min(STORAGE_TRANCHE_BYTES, MAX_STORAGE_BYTES - history.allocated_storage),
            'rationale': 'The next fixed task cannot fit its complete reserved envelope after all pending work settled.',
            'expected_progress': 'Advance the original fixed task/retry inventory without resetting prior charges.',
            'stop_reason': 'Stop on finite authority, unknown use, source/integrity failure or approved A2/A3 limits.'}
        return self._transition(token, pool['id'], 'grant', request,
                                lambda: self.resources.continue_pool(token, request))

    def _reserve(self, token, pool_id, phase, task):
        with self.broker._mutex:
            pool, history = self._current(token, pool_id)
            history._live()
            inventory, _ = history._eligible(phase, task)
            if not history._fits(inventory):
                require(not history.pending, 'Native funding waits for active attempts to drain')
                self._grant(token, pool, phase, task)
                history = self.resources._history(pool)
            request = {'pool_id': pool_id, 'phase': phase, 'task_id': task,
                'attempt_id': uuid.uuid4().hex, 'expected_checkpoint': history.checkpoint}
            return self._transition(token, pool_id, 'reserve', request,
                lambda: self.resources.reserve(token, request), attempt_id=request['attempt_id'])

    def bind_inventory(self, token, pool_id, phase, input_id, task_ids, deadline_ms):
        with self.broker._mutex:
            _, history = self._current(token, pool_id)
            existing = history.inventories.get(phase)
            request = {'key': 'native-' + phase + '-' + input_id, 'pool_id': pool_id,
                'phase': phase, 'task_ids': sorted(task_ids), 'execution_deadline_ms': deadline_ms,
                'attempt_compute_ms': deadline_ms + 30000,
                'attempt_storage_bytes': MAX_ATTEMPT_STORAGE_BYTES,
                'max_attempts': 2 if phase == 'final' else 1,
                'expected_checkpoint': history.checkpoint}
            if existing is not None:
                old = existing['body']['request']
                require(existing['body'].get('input_id') == input_id
                        and all(value == request[key] for key, value in old.items() if key != 'expected_checkpoint'),
                        'Native inventory was already bound to different input/limits')
                return existing
            bound = {'request': request, 'input_id': input_id}
            return self._transition(token, pool_id, 'inventory', bound,
                lambda: self.resources.bind_inventory(token, request, input_id=input_id))

    def _setup(self, token, pool_id, name, work):
        """Run one fixed setup task; callbacks are installed host code only."""
        with self.broker._mutex:
            pool, history = self._current(token, pool_id)
            history._live()
            task = pool['body']['setup_tasks'][name]
            previous = history.records.get(('setup', task))
            if previous is not None:
                item = self.broker._artifact(previous['artifact_id'])
                self.broker._require_usable_dependencies(item['id'])
                require(previous['state'] == 'COMPLETE', 'Failed native setup cannot be automatically repeated')
                return item
            reservation = self._reserve(token, pool_id, 'setup', task)
            operation, request_hash = uuid.uuid4().hex, digest({'setup': name, 'attempt_id': reservation['attempt_id']})
            self._observe(token, pool_id, operation, 'setup', 'INTENT', request_hash=request_hash,
                          attempt_id=reservation['attempt_id'])
        started = time.monotonic()
        value, failure, known = None, None, False
        try:
            value = work()
            require(type(value) is dict and set(value) == {'result', 'refs', 'storage_bytes', 'usage_known'},
                    'Exact metered native setup result required')
            known = value['usage_known'] is True
            require(known, 'Native setup usage is unknown')
            require(type(value['result']) is dict and value['result'].get('ok', True) is True,
                    'Native setup did not satisfy its owned completion criterion')
            self._current(token, pool_id)
        except BaseException as exc:
            failure = {'type': type(exc).__name__, 'message': str(exc)[:2000]}
            if value is None:
                # The operation may have retained partial native inputs/output.
                # Conservative full reservation, rather than CAS-delta billing.
                value = {'result': None, 'refs': [], 'storage_bytes': 0, 'usage_known': False}
        body = {'resource_pool_id': pool_id, 'phase': 'setup', 'task_id': task,
            'attempt_id': reservation['attempt_id'], 'result': value['result'],
            'technical_refs': value['refs'], 'output_blobs': {},
            'resource_state': 'COMPLETE' if failure is None else 'FAILED',
            'currency_checked': failure is None, 'failure': failure, 'failures': [] if failure is None else [failure],
            'settlement': {'attempt_id': reservation['attempt_id'],
                'compute_ms': max(1, math.ceil((time.monotonic() - started) * 1000)),
                'storage_bytes': integer(value['storage_bytes'], 'Native setup storage') + META,
                'usage_known': known}}
        item = self.resources.settle(token, pool_id, body)
        self._observe(token, pool_id, operation, 'setup', 'ACK', request_hash=request_hash,
                      attempt_id=reservation['attempt_id'], result_id=item['id'])
        require(item['body']['resource_state'] == 'COMPLETE', 'Native setup failed; inspect retained failure and charges')
        return item

    def _stop(self, token, pool_id, reason):
        self.cancel.set()
        return self.resources.stop(token, pool_id, reason)

    @contextmanager
    def _executor(self, token, pool_id, workers):
        executor = ThreadPoolExecutor(max_workers=workers, thread_name_prefix='native-world')
        try:
            yield executor
        except BaseException as exc:
            # Signal active controlled children before Executor joins them.
            self.cancel.set()
            try:
                self._stop(token, pool_id, 'NATIVE_SCHEDULER_ABORT_BEFORE_JOIN')
            except BaseException as stop_error:
                exc.add_note('Durable native stop failed: ' + type(stop_error).__name__)
            raise
        finally:
            executor.shutdown(wait=True)

    def _run(self, token, pool_id, phase, task_ids, *, workers, on_checkpoint=None):
        self.validate(token, pool_id)
        require(phase in ('acceptance', 'final') and type(workers) is int and workers in (1, 6),
                'Native scheduling uses one serial or at most six parallel workers')
        require(type(task_ids) is list and len(task_ids) == len(set(task_ids)), 'Distinct native schedule required')
        with self.broker._mutex:
            pool, history = self._current(token, pool_id)
            history._live()
            require(phase in history.inventories
                    and set(task_ids) <= set(history.inventories[phase]['body']['request']['task_ids']),
                    'Native schedule is outside its immutable inventory')
            require(not history.pending, 'Native phase cannot inherit outstanding work')
        attempts, futures, first_failure, stop_failures = [], {}, None, []
        terminal, unavailable, attempted_stops = set(), set(), set()
        def request_stop(reason, primary=None):
            self.cancel.set()
            if reason in attempted_stops:
                return
            attempted_stops.add(reason)
            try:
                self._stop(token, pool_id, reason)
            except BaseException as exc:
                stop_failures.append({'type': type(exc).__name__, 'message': str(exc)[:2000], 'reason': reason})
                if primary is not None:
                    primary.add_note('Durable native stop failed: ' + type(exc).__name__)
        def queue_state():
            nonlocal terminal, unavailable
            h = self.resources._history(pool)
            terminal, unavailable, retries, fresh = set(), set(), [], []
            active = {r['task_id'] for r in h.pending.values() if r['phase'] == phase}
            for task in task_ids:
                row = h.records.get((phase, task))
                count = len(h.attempts.get((phase, task), []))
                if row and task not in active and (row['state'] == 'COMPLETE'
                                                   or row['state'] == 'KNOWN_TIMEOUT' and count == 2):
                    terminal.add(task)
                    if row['state'] != 'COMPLETE': unavailable.add(task)
                elif task not in active:
                    (retries if row and row['state'] == 'KNOWN_TIMEOUT' else fresh).append(task)
            return h, retries + fresh
        try:
            with self._executor(token, pool_id, workers) as executor:
                while True:
                    with self.broker._mutex:
                        history, queue = queue_state()
                        if self._path('stop.request').exists() and not history.halted:
                            request_stop('OPERATOR_NATIVE_STOP_REQUEST')
                            history = self.resources._history(pool)
                        if history.halted or self.cancel.is_set():
                            if self.cancel.is_set() and not history.halted:
                                request_stop('NATIVE_CONTROLLER_CANCELLED')
                            self.cancel.set()
                            queue = []
                        elif on_checkpoint is not None:
                            on_checkpoint(history, len(terminal))
                            history = self.resources._history(pool)
                            if history.halted or self.cancel.is_set(): queue = []
                        while queue and len(futures) < workers:
                            history._live()
                            task = queue.pop(0)
                            inventory = history.inventories[phase]
                            if not history._fits(inventory) and history.pending:
                                break  # Drain before requesting the next paired grant.
                            whole_started = time.monotonic()
                            reservation = self._reserve(token, pool_id, phase, task)
                            attempt_id = reservation['attempt_id']
                            try:
                                if on_checkpoint is not None:
                                    current = self.resources._history(pool)
                                    on_checkpoint(current, len(terminal))
                                    current = self.resources._history(pool)
                                    current._live()
                                    require(not self.cancel.is_set(), 'Native pre-dispatch guard stopped this task')
                                operation, request_hash = uuid.uuid4().hex, digest({'attempt_id': attempt_id})
                                self._observe(token, pool_id, operation, 'execute', 'INTENT',
                                              request_hash=request_hash, attempt_id=attempt_id)
                                future = executor.submit(self.caller.execute, token, pool_id, attempt_id, _cancel=self.cancel)
                                futures[future] = (reservation, operation, request_hash, whole_started)
                            except BaseException as exc:
                                try:
                                    self._reject_unlaunched(token, pool, reservation, whole_started, exc)
                                except BaseException as settlement_error:
                                    exc.add_note('Unlaunched task settlement failed: ' + type(settlement_error).__name__)
                                raise
                            history = self.resources._history(pool)
                    if not futures:
                        break
                    done, _ = wait(futures, timeout=1, return_when=FIRST_COMPLETED)
                    for future in done:
                        reservation, operation, request_hash, whole_started = futures.pop(future)
                        try:
                            item = future.result()
                            require(item['body']['attempt_id'] == reservation['attempt_id'],
                                    'Native scheduler received another attempt result')
                            attempts.append(item['id'])
                            self._observe(token, pool_id, operation, 'execute', 'ACK', request_hash=request_hash,
                                          attempt_id=reservation['attempt_id'], result_id=item['id'],
                                          whole_call_ms=max(1, math.ceil((time.monotonic() - whole_started) * 1000)))
                            if item['body']['resource_state'] not in ('COMPLETE', 'KNOWN_TIMEOUT'):
                                request_stop('NATIVE_TASK_FAILED')
                        except BaseException as exc:
                            first_failure = first_failure or exc
                            request_stop('NATIVE_EXECUTION_OR_OBSERVATION_FAILED', exc)
        except BaseException as exc:
            first_failure = first_failure or exc
            request_stop('NATIVE_SCHEDULER_STOPPED', exc)
        finally:
            # Executor exit has joined all submitted futures. Only now classify
            # any missing settlement conservatively; never recover a live slot.
            try:
                with self.broker._mutex:
                    for future, (reservation, operation, request_hash, whole_started) in futures.items():
                        try:
                            item = future.result()
                            if item['id'] not in attempts:
                                attempts.append(item['id'])
                                self._observe(token, pool_id, operation, 'execute', 'ACK', request_hash=request_hash,
                                              attempt_id=reservation['attempt_id'], result_id=item['id'],
                                              whole_call_ms=max(1, math.ceil((time.monotonic() - whole_started) * 1000)))
                        except BaseException as exc:
                            first_failure = first_failure or exc
                    history = self.resources._history(pool)
                    for attempt_id in list(history.pending):
                        self.broker._native_calibration_active.discard(attempt_id)
                    if history.pending:
                        self.resources.recover()
                    history, _ = queue_state()
            except BaseException as accounting_error:
                if first_failure is not None:
                    first_failure.add_note('Final native accounting is unverified: ' + type(accounting_error).__name__)
                    raise first_failure from accounting_error
                raise
        stopped = history.halted or self.cancel.is_set() or first_failure is not None or len(terminal) != len(task_ids)
        return {'status': 'STOPPED' if stopped else 'INCOMPLETE_UNAVAILABLE' if unavailable else 'COMPLETE',
            'attempts': attempts, 'terminal_tasks': sorted(terminal), 'unavailable_tasks': sorted(unavailable),
            'failure': None if first_failure is None else {'type': type(first_failure).__name__,
                'message': str(first_failure)[:2000],
                **({'notes': list(first_failure.__notes__)} if getattr(first_failure, '__notes__', None) else {})},
            'stop_failures': stop_failures,
            'resource_checkpoint': history.checkpoint, 'budget': history.budget(), 'scientific_readiness': False}

    def _timings(self):
        return dict(self._timing_values)

    def _reject_unlaunched(self, token, pool, reservation, started, exc):
        """Known control-only work is not an unknown/orphan numerical run."""
        b = self.broker
        require(reservation['attempt_id'] not in b._native_calibration_dispatched,
                'A dispatched native attempt cannot claim unlaunched usage')
        history = self.resources._history(pool)
        phase = reservation['phase']
        inventory = history.inventories[phase]
        failure = {'type': type(exc).__name__, 'message': str(exc)[:2000]}
        body = {'resource_pool_id': pool['id'], 'phase': phase, 'task_id': reservation['task_id'],
            'attempt_id': reservation['attempt_id'], 'resource_state': 'FAILED', 'currency_checked': False,
            'failure': failure, 'failures': [failure], 'output_blobs': {},
            'not_launched': True, 'settlement': {'attempt_id': reservation['attempt_id'],
                'compute_ms': max(1, math.ceil((time.monotonic() - started) * 1000)),
                'storage_bytes': META, 'usage_known': True}}
        if inventory['body'].get('input_id'):
            from .family_study import outcome_record
            study_id = inventory['body']['input_id']; study = b._artifact(study_id)
            selection = (NativeCalibrationReferences.tasks(study)[reservation['task_id']]
                         if phase == 'acceptance' else {'world_id': reservation['task_id']})
            world = next(w for w in study['body']['manifest']['worlds'] if w['id'] == selection['world_id'])
            body.update(study_id=study_id, world_id=world['id'], result=None, proofs=[],
                        outcome=outcome_record(study['body']['manifest'], world, failed=True))
            if phase == 'acceptance':
                body.update(reference_id=study_id, input_id=study_id, reference_mode=selection['mode'])
        self.resources.settle(token, pool['id'], body)

    def prepare_inputs(self, token, pool_id, archive_path, manifest_path):
        from .native_runtime import NativeRuntimes
        from .native_qualification import NativeQualifications
        from .native_qualification_profile import ARCHIVE_SHA, MANIFEST_SHA
        archive_path, manifest_path = Path(archive_path), Path(manifest_path)
        require(hashlib.sha256(archive_path.read_bytes()).hexdigest() == ARCHIVE_SHA
                and hashlib.sha256(manifest_path.read_bytes()).hexdigest() == MANIFEST_SHA,
                'Actual native runtime inputs differ from the pinned approved version')
        correction = self.resources._pool(pool_id)['body'].get('source_correction')
        def retain():
            runtimes = NativeRuntimes(self.broker)
            if correction is None:
                source = self.broker.call(token, 'add_blob_source', path=str(archive_path), data_class='operations',
                    description='Pinned exact D100 native runtime; no scientific authority.')
                item = runtimes.retain(token, {'key': 'd100-exact-native-runtime',
                    'archive_id': source['id'], 'manifest': decode(manifest_path.read_bytes())})
            else:
                item = runtimes.inspect(token, {'runtime_id': correction['runtime_id']})
                require(item['body']['archive']['sha256'] == ARCHIVE_SHA
                        and item['body']['manifest'] == decode(manifest_path.read_bytes())
                        and item['body']['request']['key'] == 'd100-exact-native-runtime',
                        'Correction must reuse the exact already-retained runtime package')
            return {'result': {'runtime_id': item['id']}, 'refs': [item['id']],
                    'storage_bytes': item['body']['archive']['size'], 'usage_known': True}
        runtime = self._setup(token, pool_id, 'runtime_retain', retain)['body']['result']['runtime_id']
        NativeRuntimes(self.broker).inspect(token, {'runtime_id': runtime})
        def qualify():
            item = NativeQualifications(self.broker).qualify(token,
                {'key': 'd100-fixed-source-qualification' if correction is None
                        else 'd100-source-correction-qualification-' + pool_id, 'runtime_id': runtime})
            return {'result': {'qualification_id': item['id'], 'ok': item['body']['status'] == 'CERTIFIED',
                               'failure': item['body']['failure']}, 'refs': [item['id']],
                    'storage_bytes': item['body']['settlement']['storage_bytes'],
                    'usage_known': item['body']['settlement']['usage_known']}
        qualification = self._setup(token, pool_id, 'runtime_qualification', qualify)['body']['result']['qualification_id']
        NativeQualifications(self.broker)._require_inputs(qualification)
        def reference():
            request = {'key': 'd100-complete-old-reference' if correction is None
                       else 'd100-source-correction-reference-' + pool_id,
                'development_study_id': DEVELOPMENT_ID, 'native_qualification_id': qualification}
            owner = NativeCalibrationReferences(self.broker)
            if correction is not None:
                request['source_correction_pool_id'] = pool_id
                owner = NativeCalibrationCorrectionReferences(self.broker)
            item = owner.prepare(token, request)
            return {'result': {'reference_id': item['id']}, 'refs': [item['id']],
                    'storage_bytes': item['body']['initial_storage_bytes'], 'usage_known': True}
        reference = self._setup(token, pool_id, 'prepare_reference_input', reference)['body']['result']['reference_id']
        return qualification, NativeCalibrationReferences(self.broker)._study(reference)

    def references(self, token, pool_id, reference):
        runner = NativeCalibrationReferences(self.broker)
        runner._study_before_execute(reference)
        manifest = reference['body']['manifest']
        p = manifest['profile']
        require(reference['body']['request']['development_study_id'] == DEVELOPMENT_ID
                and p['targets'] == [2048, 4096] and p['worlds_per_cell'] == 2
                and len(p['specifications']) == 2 and len(p['patterns']) == 4
                and len(manifest['worlds']) == 32, 'D100 requires the entire fixed original reference corpus')
        tasks = runner.tasks(reference)
        self.bind_inventory(token, pool_id, 'acceptance', reference['id'], list(tasks),
                            policy()['acceptance_deadline_ms'])
        rank = {identity: i for i, identity in enumerate(round_robin(manifest['worlds']))}
        for mode, workers in (('parallel', 6), ('serial', 1)):
            selected = sorted([task for task in tasks if tasks[task]['mode'] == mode],
                              key=lambda task: rank[tasks[task]['world_id']])
            result = self._run(token, pool_id, 'acceptance', selected, workers=workers)
            require(result['status'] == 'COMPLETE', 'Actual native fixed reference acceptance failed or stopped')
        def summarize():
            timings, metrics, fallback = self._timings(), [], {}
            _, history = self._current(token, pool_id)
            for task_id, selected in tasks.items():
                row = history.records[('acceptance', task_id)]
                item = self.broker._artifact(row['artifact_id']); body = item['body']
                require(row['state'] == 'COMPLETE' and body['numerical_caller'] == 'native-reserved-calculation/1'
                        and body['reference_id'] == reference['id']
                        and body['reference_comparison'] == 'FULL_REFERENCE_MATCH'
                        and len(body['proofs']) == 2 and body['settlement']['usage_known'] is True,
                        'Actual reference acceptance lacks complete owned calculation/replay')
                elapsed = timings.get(body['attempt_id'])
                require(type(elapsed) is int and elapsed > 0,
                        'Actual reference whole-call timing is unavailable; never invent or repeat it')
                world = next(w for w in manifest['worlds'] if w['id'] == selected['world_id'])
                metric = {'task_id': task_id, 'world_id': world['id'], 'mode': selected['mode'],
                    'time_rows': world['time_rows'], 'spec_index': world['spec_index'],
                    'pattern_index': world['pattern_index'], 'result_id': item['id'],
                    'whole_call_ms': elapsed, 'compute_ms': body['settlement']['compute_ms'],
                    'storage_bytes': body['settlement']['storage_bytes'], 'retained_bytes': retained_bytes(body)}
                metrics.append(metric)
                if selected['mode'] == 'parallel' and world['time_rows'] == 4096:
                    key = f"{world['spec_index']}/{world['pattern_index']}"
                    basis = fallback.setdefault(key, {'compute_ms': 0, 'storage_bytes': 0, 'retained_bytes': 0})
                    for field in basis:
                        basis[field] = max(basis[field], elapsed if field == 'compute_ms' else metric[field])
            require(len(metrics) == 64 and len(fallback) == 8, 'Actual native reference measurement inventory incomplete')
            deadline = 1000 * ((2 * max(v['compute_ms'] for v in fallback.values()) + 999) // 1000)
            runner._study_after_execute(reference)
            result = {'schema': 'native-calibration-fixed-acceptance/1', 'reference_id': reference['id'],
                'deadline_ms': deadline, 'attempt_compute_ms': deadline + 30000,
                'metrics': metrics, 'fallback': fallback, 'policy': policy(), 'ok': True,
                'scientific_readiness': False}
            return {'result': result, 'refs': [reference['id'], *[m['result_id'] for m in metrics]],
                    'storage_bytes': 0, 'usage_known': True}
        item = self._setup(token, pool_id, 'acceptance_summary', summarize)
        return item['body']['result']

    def prepare_final(self, token, pool_id, qualification_id, acceptance):
        require(acceptance['ok'] is True and acceptance['policy'] == policy(), 'Fixed actual acceptance required')
        def prepare():
            # The retained development-only estimate is an operator claim; actual
            # acceptance metrics stay separately bound in operational provenance.
            development = self.broker._artifact(DEVELOPMENT_ID)
            estimate = development['body']['manifest']['profile']['cost_estimate']
            old = self.resources._read_authority()['native']['retired_scalar_state']['study_id']
            applicability = self.broker._artifact(old)['body']['request']['applicability']
            request = {'key': 'd100-native-final-2048', 'development_study_id': DEVELOPMENT_ID,
                'native_qualification_id': qualification_id, 'time_rows': 4096, 'seed': 2026110301,
                'budget': {'max_compute_ms': max(3600000, acceptance['deadline_ms']),
                    'attempt_compute_ms': acceptance['deadline_ms'], 'max_storage_bytes': 4 * 1024**3,
                    'attempt_storage_bytes': MAX_ATTEMPT_STORAGE_BYTES, 'max_attempts': 1},
                'cost_estimate': estimate, 'applicability': applicability}
            item = NativeFamilyCalibrationStudies(self.broker)._prepare_information_study_external(token, request)
            manifest = item['body']['manifest']
            require(len(manifest['worlds']) == 2048 and len(manifest['profile']['specifications']) == 2
                    and len(manifest['profile']['patterns']) == 4 and manifest['profile']['worlds_per_cell'] == 256,
                    'D100 final inventory differs from its full approved scope')
            return {'result': {'study_id': item['id']}, 'refs': [item['id']],
                    'storage_bytes': item['body']['initial_storage_bytes'], 'usage_known': True}
        item = self._setup(token, pool_id, 'prepare_final_input', prepare)
        study = NativeFamilyCalibrationStudies(self.broker)._study(item['body']['result']['study_id'])
        self.bind_inventory(token, pool_id, 'final', study['id'],
                            [w['id'] for w in study['body']['manifest']['worlds']], acceptance['deadline_ms'])
        return study

    def _primary_bytes(self):
        return (self.broker._db.execute('SELECT COALESCE(SUM(size),0) FROM blobs').fetchone()[0]
                + (self.broker.directory / 'registry.sqlite3').stat().st_size)

    def _forecast(self, token, pool_id, study, acceptance, *, prepared_copies, copy_wall_ms=0):
        _, history = self._current(token, pool_id)
        timings = self._timings()
        for identity in history.seen_results - self._seen_results:
            body = self.broker._artifact(identity)['body']
            if body['phase'] == 'final':
                self._final_bodies[body['attempt_id']] = body
            self._seen_results.add(identity)
        bodies = []
        for (phase, _), ids in history.attempts.items():
            if phase != 'final': continue
            for attempt_id in ids:
                if attempt_id in self._final_bodies:
                    timing = timings.get(attempt_id)
                    bodies.append({**self._final_bodies[attempt_id],
                        'whole_call_ms': timing or acceptance['attempt_compute_ms'],
                        'timing_measured': timing is not None})
        now = datetime.now(timezone.utc)
        elapsed = math.ceil((now - datetime.fromisoformat(self.binding['operational_start_utc'])).total_seconds() * 1000)
        require(elapsed >= 0, 'Native operational wall clock moved before its fixed start')
        start = self._path('final-start.json')
        final_elapsed = (math.ceil((now - datetime.fromisoformat(decode(start.read_bytes())['at_utc'])).total_seconds() * 1000)
                         if start.exists() else 0)
        require(final_elapsed >= 0, 'Native final wall clock moved before its fixed start')
        primary = self._primary_bytes()
        result = forecast(study['body']['manifest'], bodies, list(history.pending.values()),
            fallback=acceptance['fallback'], elapsed_ms=elapsed, final_elapsed_ms=final_elapsed,
            deadline_ms=acceptance['deadline_ms'], charged_storage_bytes=history.storage,
            copy_overhead_ms=900000, primary_bytes=primary, prepared_copies=prepared_copies, terminal_copies=2)
        if copy_wall_ms:
            reserve = math.ceil(2 * copy_wall_ms * Fraction(primary + result['forecast_growth_bytes'], max(1, primary)))
            result['total_wall_ms'] += max(0, reserve - 900000)
            result['time_exceeds_24h'] = result['total_wall_ms'] > WALL_LIMIT_MS
        free = shutil.disk_usage(self.broker.directory).free
        free_c = shutil.disk_usage(Path('C:/')).free if os.name == 'nt' else free
        result.update(resource_checkpoint=history.checkpoint, free_bytes=free, free_C_bytes=free_c,
                      pool_id=pool_id, study_id=study['id'])
        return result

    def _admit_forecast(self, token, pool_id, report, *, measured_a2):
        reason = ('NATIVE_A3_LOGICAL_FORECAST' if report['logical_forecast_bytes'] > MAX_STORAGE_BYTES
            else 'NATIVE_A3_PHYSICAL_FORECAST' if report['free_bytes'] < report['required_free_bytes']
                 or report['free_C_bytes'] < FREE_FLOOR
            else 'NATIVE_A2_WALL_FORECAST' if measured_a2 and report['time_exceeds_24h'] else None)
        if reason:
            primary = Invalid(reason + ': controlled stop; retain all evidence and report')
            try:
                self._stop(token, pool_id, reason)
            except BaseException as exc:
                primary.add_note('Durable native stop failed: ' + type(exc).__name__)
            raise primary

    def run_final(self, token, pool_id, study, acceptance):
        runner = NativeFamilyCalibrationStudies(self.broker)
        runner._study_before_execute(study)
        receipt_path = self.copies.receipt_path(pool_id, 'prepared')
        if receipt_path.exists():
            copied = self.copies.require(token, pool_id, 'prepared', receipt_path)
        else:
            report = self._forecast(token, pool_id, study, acceptance, prepared_copies=2)
            self._write('prestart-forecast.json', report)
            self._admit_forecast(token, pool_id, report, measured_a2=False)
            copied = self.copies.create(token, pool_id, 'prepared',
                backup_directory=self.directory.parent / 'native-prepared-backup',
                restore_directory=self.directory.parent / 'native-prepared-restore', receipt_path=receipt_path)
        if self._path('final-start.json').exists():
            clock = decode(self._path('final-start.json').read_bytes())
            require(set(clock) == {'at_utc', 'study_id', 'acceptance_hash', 'prepared_prefix', 'scientific_readiness'}
                    and clock['study_id'] == study['id'] and clock['acceptance_hash'] == digest(acceptance)
                    and clock['prepared_prefix'] == copied['event_prefix']
                    and clock['scientific_readiness'] is False
                    and datetime.fromisoformat(clock['at_utc']) <= datetime.fromisoformat(READINESS_CUTOFF),
                    'Fixed native final clock, acceptance or prepared prefix differs')
        fresh = self._forecast(token, pool_id, study, acceptance, prepared_copies=0,
                               copy_wall_ms=copied['wall_elapsed_ms'])
        self._admit_forecast(token, pool_id, fresh, measured_a2=False)
        if not self._path('final-start.json').exists():
            _, before = self._current(token, pool_id)
            require(not any(phase == 'final' for phase, _ in before.attempts),
                    'Missing final phase clock cannot reset existing native work')
            require(datetime.now(timezone.utc) <= datetime.fromisoformat(READINESS_CUTOFF),
                    'D100 readiness deadline passed before actual admission; stop and report')
            require(len(study['body']['manifest']['worlds']) == 2048, 'Full native final inventory required')
            self._write('final-start.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
                'study_id': study['id'], 'acceptance_hash': digest(acceptance),
                'prepared_prefix': copied['event_prefix'], 'scientific_readiness': False})
        marker, saved_marker, cached = None, None, None
        def monitor(history, terminal):
            nonlocal marker, saved_marker, cached
            observed = (terminal // 64, len(history.grants))
            if cached is None or history.checkpoint != marker:
                cached = self._forecast(token, pool_id, study, acceptance, prepared_copies=0,
                                        copy_wall_ms=copied['wall_elapsed_ms'])
                name = 'forecast-' + history.checkpoint + '.json'
                if observed != saved_marker and not self._path(name).exists():
                    self._write(name, cached)
                    saved_marker = observed
                if (cached['logical_forecast_bytes'] > MAX_STORAGE_BYTES
                        or cached['free_bytes'] < cached['required_free_bytes']
                        or terminal >= 64 and cached['time_exceeds_24h']):
                    if not self._path(name).exists(): self._write(name, cached)
                self._admit_forecast(token, pool_id, cached, measured_a2=terminal >= 64)
                marker = history.checkpoint
            # Actual floor/copy/scratch capacity checked before each batch even
            # when no new forecast checkpoint has become available.
            free = shutil.disk_usage(self.broker.directory).free
            free_c = shutil.disk_usage(Path('C:/')).free if os.name == 'nt' else free
            if free < cached['required_free_bytes'] or free_c < FREE_FLOOR:
                self._stop(token, pool_id, 'NATIVE_A3_CURRENT_PHYSICAL_CAPACITY')
        result = self._run(token, pool_id, 'final', round_robin(study['body']['manifest']['worlds']),
                           workers=6, on_checkpoint=monitor)
        runner._study_after_execute(study)
        from . import family_study
        _, history = self._current(token, pool_id)
        records, sources = [], {}
        for world in study['body']['manifest']['worlds']:
            row = history.records.get(('final', world['id']))
            if row:
                body = self.broker._artifact(row['artifact_id'])['body']
                records.append(body['outcome']); sources[world['id']] = row['artifact_id']
        count = family_study.count_assessment(study['body']['manifest'], records, sources,
                                              study['body']['request']['applicability'])
        require(count['plan_hash'] == study['body']['count_plan_hash'], 'Frozen final count plan differs')
        final = {'schema': 'native-calibration-controller-result/1', 'pool_id': pool_id, 'study_id': study['id'],
            'status': 'COMPLETE_NUMERICAL_INVENTORY' if result['status'] == 'COMPLETE' else result['status'],
            'worlds_total': 2048, 'worlds_recorded': len(records),
            'worlds_available': sum(r['state'] in ('VERIFIED', 'INFORMATION_GAP') for r in records),
            'worlds_unavailable': sum(r['state'] not in ('VERIFIED', 'INFORMATION_GAP') for r in records),
            'count_assessment': count,
            'summary': family_study.summarize(study['body']['manifest'], records), 'budget': history.budget(),
            'failure': result['failure'], 'stop_failures': result['stop_failures'],
            'resource_checkpoint': history.checkpoint, 'scientific_readiness': False, 'n_min': None}
        name = 'final-result-' + history.checkpoint + '.json'
        if not self._path(name).exists(): self._write(name, final)
        return final

    def _terminal_copy(self, token, pool_id):
        receipt = self.copies.receipt_path(pool_id, 'terminal')
        if receipt.exists():
            return self.copies.require(token, pool_id, 'terminal', receipt)
        return self.copies.create(token, pool_id, 'terminal',
            backup_directory=self.directory.parent / 'native-terminal-backup',
            restore_directory=self.directory.parent / 'native-terminal-restore', receipt_path=receipt)

    def run_all(self, token, *, archive_path, manifest_path, correction_args=None):
        key = 'd100-native-bounded-controller' if correction_args is None else correction_args['key']
        pool = self.prepare(token, key, correction_args=correction_args)
        try:
            for label in ('prepared', 'terminal'):
                history = self.resources._history(pool)
                task = pool['body']['setup_tasks'][label + '_copies']
                if ('setup', task) not in history.records:
                    self._transition(token, pool['id'], 'copy_booking', {'pool_id': pool['id'], 'label': label},
                                     lambda label=label: self.copies.book(token, pool['id'], label))
            qualification, reference = self.prepare_inputs(token, pool['id'], archive_path, manifest_path)
            acceptance = self.references(token, pool['id'], reference)
            study = self.prepare_final(token, pool['id'], qualification, acceptance)
            result = self.run_final(token, pool['id'], study, acceptance)
            self._terminal_copy(token, pool['id'])
            return result
        except BaseException as exc:
            try:
                self._stop(token, pool['id'], 'NATIVE_CONTROLLER_WORKFLOW_FAILED')
                with self.broker._mutex:
                    history = self.resources._history(pool)
                    for attempt_id in history.pending:
                        self.broker._native_calibration_active.discard(attempt_id)
                    self.resources.recover()
                self._terminal_copy(token, pool['id'])
            except BaseException as copy_error:
                exc.add_note('Actual terminal full-copy obligation is unverified: '
                             + type(copy_error).__name__ + ': ' + str(copy_error)[:500])
            raise
