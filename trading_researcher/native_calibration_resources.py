"""Finite native-calibration accounting, not execution or scientific admission.

The consuming owner authenticates retired carry and derives outcomes from actual
controlled work. This reducer authenticates its owned journal, reserves complete
envelopes for at most six tasks, and never uses a new key/version as a refund.
Legacy single-inflight ResourceHistory and its historical failures stay intact.
"""
import hashlib
import re
from types import MappingProxyType

from .binding import require
from .codec import canonical, decode, digest, integer, text
from .errors import Conflict


POOL = 'native-calibration-resource-pool/1'
INVENTORY = 'native-calibration-resource-inventory/1'
GRANT = 'native-calibration-resource-grant/1'
AUTHORITY = 'bounded_native_calibration_resources_not_scientific_admission'
META = 1048576
MAX_COMPUTE_MS = 648000000
MAX_STORAGE_BYTES = 107374182400
COMPUTE_TRANCHE_MS = 3600000
STORAGE_TRANCHE_BYTES = 4294967296
MAX_GRANTS = 179
MAX_ATTEMPT_STORAGE_BYTES = 268435456
MAX_TASKS = MappingProxyType({'setup': 16, 'acceptance': 64, 'final': 2048})
RESULT_SCHEMAS = MappingProxyType({
    'setup': 'native-calibration-setup-attempt/1',
    'acceptance': 'native-calibration-acceptance-attempt/1',
    'final': 'native-family-calibration-attempt/1'})
RESULT_AUTHORITIES = MappingProxyType({
    'setup': AUTHORITY, 'acceptance': AUTHORITY,
    'final': 'conditional_native_joint_family_calibration_not_scientific_admission'})
RESERVE_FIELDS = {'pool_id', 'phase', 'task_id', 'attempt_id', 'expected_checkpoint'}
INVENTORY_FIELDS = {'pool_id', 'key', 'phase', 'task_ids', 'execution_deadline_ms',
                    'attempt_compute_ms', 'attempt_storage_bytes', 'max_attempts', 'expected_checkpoint'}
GRANT_FIELDS = {'key', 'pool_id', 'phase', 'task_id', 'expected_checkpoint',
                'additional_compute_ms', 'additional_storage_bytes', 'rationale',
                'expected_progress', 'stop_reason'}
CLOCK_TYPES = {'ChildDeadlineExceeded', 'AttemptDeadlineExceeded', 'AuthenticatedCalculatorDeadline'}
ACTIONS = {'native_calibration_inventory_bound', 'native_calibration_reserved',
           'native_calibration_settled', 'native_calibration_continued', 'native_calibration_stopped'}


def _exact(value, fields, message):
    require(type(value) is dict and set(value) == fields, message)


def _identity(value, length=64):
    require(type(value) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None,
            'Exact native resource identity required')
    return value


def _owned(artifact, schema, authority, refs=()):
    require(type(artifact) is dict and artifact.get('creator') == artifact.get('origin') == 'controller'
            and artifact.get('data_class') == 'operations' and artifact.get('authority') == authority,
            'Owned native resource artifact required')
    _identity(artifact['id'])
    body = artifact.get('body')
    require(type(body) is dict and body.get('schema') == schema
            and body.get('scientific_readiness') is False, 'Native resource artifact type differs')
    require(type(artifact.get('source_refs')) is list and set(refs) <= set(artifact['source_refs']),
            'Native resource artifact omits its typed custody')
    integer(body['created_at'], 'Native resource creation time')
    return body


class NativeResourceHistory:
    """Replay one immutable, finite resource pool through every journal prefix."""
    def __init__(self, pool):
        pool = decode(canonical(pool))
        body = _owned(pool, POOL, AUTHORITY)
        require(type(body['max_parallel']) is int and body['max_parallel'] == 6,
                'The approved native pool has at most six slots')
        carry = body['carry']
        fields = {'schema', 'basis_id', 'charged_compute_ms', 'charged_storage_bytes',
                  'allocated_compute_ms', 'allocated_storage_bytes', 'grants_used',
                  'progress_units', 'last_grant_progress', 'no_progress_grants'}
        _exact(carry, fields, 'Exact retained native resource carry required')
        require(carry['schema'] == 'native-calibration-resource-carry/1', 'Native resource carry version differs')
        _identity(carry['basis_id'])
        for key in fields - {'schema', 'basis_id'}:
            integer(carry[key], key)
        require(carry['grants_used'] <= MAX_GRANTS and carry['no_progress_grants'] <= 2
                and carry['last_grant_progress'] <= carry['progress_units'], 'Retained finite grant state differs')
        for allocated, charged, tranche, maximum in (
                ('allocated_compute_ms', 'charged_compute_ms', COMPUTE_TRANCHE_MS, MAX_COMPUTE_MS),
                ('allocated_storage_bytes', 'charged_storage_bytes', STORAGE_TRANCHE_BYTES, MAX_STORAGE_BYTES)):
            require(tranche <= carry[allocated] <= min(maximum, tranche * (1 + carry['grants_used']))
                    and carry[charged] <= carry[allocated], 'Retained allocation or charge exceeds authority')
        self.pool_id = pool['id']
        self._carry = carry
        self.compute = carry['charged_compute_ms']
        self.storage = carry['charged_storage_bytes']
        self.allocated_compute = carry['allocated_compute_ms']
        self.allocated_storage = carry['allocated_storage_bytes']
        self.progress = carry['progress_units']
        self.last_grant_progress = carry['last_grant_progress']
        self.no_progress = carry['no_progress_grants']
        self.inventories = {}
        self.pending = {}
        self.seen_attempts = set()
        self.seen_results = set()
        self.attempts = {}
        self.records = {}
        self.grants = []
        self.progress_tasks = set()
        self.unknown = False
        self.overrun = False
        self.halted = False
        self.halt_reasons = []
        self.hasher = hashlib.sha256(canonical({'schema': 'native-calibration-resource-checkpoint/1',
                                               'pool_id': self.pool_id, 'carry': carry}).encode())

    @property
    def checkpoint(self):
        return self.hasher.hexdigest()

    def budget(self):
        used = self._carry['grants_used'] + len(self.grants)
        return {'charged_compute_ms': self.compute, 'charged_storage_bytes': self.storage,
                'allocated_compute_ms': self.allocated_compute, 'allocated_storage_bytes': self.allocated_storage,
                'aggregate_compute_ms': MAX_COMPUTE_MS, 'aggregate_storage_bytes': MAX_STORAGE_BYTES,
                'grants_used': used, 'grants_remaining': MAX_GRANTS - used,
                'outstanding_attempts': sorted(self.pending), 'usage_uncertain': self.unknown,
                'overrun': self.overrun, 'halted': self.halted, 'halt_reasons': list(self.halt_reasons),
                'progress_units': self.progress, 'no_progress_grants': self.no_progress,
                'scientific_readiness': False}

    def _live(self):
        require(not self.halted and not self.unknown and not self.overrun,
                'Native resource uncertainty, failure or withdrawal fences new work')

    def _request(self, request, fields):
        _exact(request, fields, 'Exact native resource request required')
        require(request['pool_id'] == self.pool_id, 'Native resource pool differs')
        _identity(request['expected_checkpoint'])
        if request['expected_checkpoint'] != self.checkpoint:
            raise Conflict('Native resource checkpoint is stale')

    def inventory_terms(self, request):
        self._request(request, INVENTORY_FIELDS)
        self._live()
        text(request['key'], 'Native inventory key')
        phase = request['phase']
        require(type(phase) is str and phase in MAX_TASKS, 'Unknown native task phase')
        if phase in self.inventories:
            raise Conflict('Native task inventory already binds its original policy')
        tasks = request['task_ids']
        require(type(tasks) is list and 1 <= len(tasks) <= MAX_TASKS[phase], 'Bounded fixed task inventory required')
        for task in tasks:
            _identity(task)
        require(tasks == sorted(set(tasks)), 'Native task inventory must be sorted and distinct')
        deadline = integer(request['execution_deadline_ms'], 'Native execution deadline', 1)
        compute = integer(request['attempt_compute_ms'], 'Full native compute reservation', 1)
        storage = integer(request['attempt_storage_bytes'], 'Full native storage reservation', 1)
        require(deadline + 5000 <= compute <= MAX_COMPUTE_MS and storage <= MAX_ATTEMPT_STORAGE_BYTES,
                'Native reservation must include bounded cleanup and fit its authority')
        require(type(request['max_attempts']) is int and request['max_attempts'] == (2 if phase == 'final' else 1),
                'Only final known-clock tasks have one retry')
        require(self.storage + META <= self.allocated_storage, 'Native inventory metadata exceeds allocated storage')
        return decode(canonical(request))

    def _task(self, phase, task_id):
        require(type(phase) is str and phase in self.inventories, 'Native task phase is not bound')
        _identity(task_id)
        inventory = self.inventories[phase]
        require(task_id in inventory['body']['request']['task_ids'], 'Native task is outside its fixed inventory')
        return inventory, (phase, task_id)

    def _eligible(self, phase, task_id):
        inventory, task = self._task(phase, task_id)
        require(not any((item['phase'], item['task_id']) == task for item in self.pending.values()),
                'Native task already has an outstanding attempt')
        attempts = self.attempts.get(task, [])
        if attempts:
            prior = self.records.get(task)
            require(phase == 'final' and len(attempts) == 1 and prior is not None
                    and prior['state'] == 'KNOWN_TIMEOUT', 'Native task has no remaining eligible clock retry')
        return inventory, task

    def _fits(self, inventory, *, compute=0, storage=0):
        limits = inventory['body']['request']
        return (self.compute + limits['attempt_compute_ms'] <= self.allocated_compute + compute
                and self.storage + limits['attempt_storage_bytes'] <= self.allocated_storage + storage)

    def reservation_terms(self, request):
        self._request(request, RESERVE_FIELDS)
        self._live()
        identity = _identity(request['attempt_id'], 32)
        require(identity not in self.seen_attempts, 'Duplicate native attempt reservation')
        inventory, _ = self._eligible(request['phase'], request['task_id'])
        require(len(self.pending) < 6, 'All six native task slots are reserved')
        require(self._fits(inventory), 'Native task reached its full-envelope resource stop')
        limits = inventory['body']['request']
        return {**decode(canonical(request)), 'inventory_id': inventory['id'],
                'compute_ms': limits['attempt_compute_ms'], 'storage_bytes': limits['attempt_storage_bytes']}

    def continuation_terms(self, request):
        self._request(request, GRANT_FIELDS)
        self._live()
        for key in ('key', 'rationale', 'expected_progress', 'stop_reason'):
            text(request[key], key)
        require(not self.pending, 'Native allocation waits for every pending attempt to settle')
        inventory, _ = self._eligible(request['phase'], request['task_id'])
        require(not self._fits(inventory), 'Native continuation requires a genuine full-envelope resource stop')
        require(self._carry['grants_used'] + len(self.grants) < MAX_GRANTS, 'Finite native grants are exhausted')
        compute = integer(request['additional_compute_ms'], 'Native compute grant')
        storage = integer(request['additional_storage_bytes'], 'Native storage grant')
        require(compute == min(COMPUTE_TRANCHE_MS, MAX_COMPUTE_MS - self.allocated_compute)
                and storage == min(STORAGE_TRANCHE_BYTES, MAX_STORAGE_BYTES - self.allocated_storage)
                and compute + storage > 0, 'Native grant must use its exact remaining paired tranche')
        require(self.compute + inventory['body']['request']['attempt_compute_ms'] <= self.allocated_compute + compute
                and self.storage + META + inventory['body']['request']['attempt_storage_bytes'] <=
                    self.allocated_storage + storage, 'Native grant cannot hold metadata and the next full reservation')
        no_progress = 0 if self.progress > self.last_grant_progress else self.no_progress + 1
        require(no_progress <= 2, 'Two native grants without operational task progress already recorded')
        return {**decode(canonical(request)),
                'previous_continuation_id': self.grants[-1]['id'] if self.grants else None,
                'charged_compute_ms_before': self.compute, 'charged_storage_bytes_before': self.storage,
                'progress_units_before': self.progress, 'no_progress_grants': no_progress}

    def _settlement(self, artifact):
        body = artifact.get('body') if type(artifact) is dict else None
        require(type(body) is dict and body.get('resource_pool_id') == self.pool_id,
                'Native settlement pool differs')
        phase, task_id = body['phase'], body['task_id']
        inventory, task = self._task(phase, task_id)
        body = _owned(artifact, RESULT_SCHEMAS[phase], RESULT_AUTHORITIES[phase],
                      (self.pool_id, inventory['id']))
        attempt = body['attempt_id']
        require(attempt in self.pending and artifact['id'] not in self.seen_results,
                'Unreserved or repeated native settlement')
        reservation = self.pending[attempt]
        require((reservation['phase'], reservation['task_id']) == task, 'Native settlement task differs')
        item = body['settlement']
        _exact(item, {'attempt_id', 'compute_ms', 'storage_bytes', 'usage_known'}, 'Exact native settlement required')
        require(item['attempt_id'] == attempt and type(item['usage_known']) is bool
                and type(body['currency_checked']) is bool, 'Native settlement binding differs')
        compute = integer(item['compute_ms'], 'Observed native compute')
        storage = integer(item['storage_bytes'], 'Observed native storage')
        state = body['resource_state']
        require(state in ('COMPLETE', 'KNOWN_TIMEOUT', 'FAILED', 'ORPHAN_UNCERTAIN'), 'Unknown native task state')
        failure, failures = body['failure'], body['failures']
        require(type(failures) is list and len(failures) <= 16, 'Bounded retained native failures required')
        for value in failures + ([failure] if failure is not None else []):
            _exact(value, {'type', 'message'}, 'Exact retained native failure required')
            text(value['type'], 'Native failure type')
            require(type(value['message']) is str and len(value['message']) <= 2000,
                    'Bounded native failure message required')
        if state == 'COMPLETE':
            require(item['usage_known'] and body['currency_checked'] and failure is None and failures == [],
                    'Completed native task requires known use and current dependencies')
        if state == 'KNOWN_TIMEOUT':
            require(item['usage_known'] and body['currency_checked'] and failure is not None
                    and failure['type'] in CLOCK_TYPES and failures == [failure],
                    'Only an owned, current, known-use clock cause can retain retry eligibility')
        if not item['usage_known'] or state == 'ORPHAN_UNCERTAIN':
            compute = max(compute, reservation['compute_ms'])
            storage = max(storage, reservation['storage_bytes'])
        overrun = (item['compute_ms'] > reservation['compute_ms']
                   or item['storage_bytes'] > reservation['storage_bytes'])
        return body, task, reservation, compute, storage, overrun

    def apply(self, event, load_artifact):
        """Validate a complete transition before mutating this in-memory prefix."""
        details = event['details']
        if (event['actor'] != 'controller' or details.get('pool_id') != self.pool_id
                or event['action'] not in ACTIONS):
            return
        event = decode(canonical(event))
        details, action = event['details'], event['action']
        if action == 'native_calibration_inventory_bound':
            _exact(details, {'pool_id', 'artifact_id'}, 'Exact native inventory event required')
            artifact = decode(canonical(load_artifact(details['artifact_id'])))
            body = _owned(artifact, INVENTORY, AUTHORITY, (self.pool_id,))
            require(artifact['id'] == details['artifact_id'] and artifact.get('blob_refs') == [],
                    'Native inventory custody differs')
            self.inventory_terms(body['request'])
            self.inventories[body['request']['phase']] = artifact
            self.storage += META
        elif action == 'native_calibration_reserved':
            _exact(details, {'pool_id', 'reservation'}, 'Exact native reservation event required')
            item = details['reservation']
            _exact(item, RESERVE_FIELDS | {'inventory_id', 'compute_ms', 'storage_bytes'}, 'Exact native reservation required')
            expected = self.reservation_terms({key: item[key] for key in RESERVE_FIELDS})
            require(canonical(item) == canonical(expected), 'Native reservation differs from its fixed envelope')
            task = (item['phase'], item['task_id'])
            self.pending[item['attempt_id']] = item
            self.seen_attempts.add(item['attempt_id'])
            self.attempts.setdefault(task, []).append(item['attempt_id'])
            self.compute += item['compute_ms']
            self.storage += item['storage_bytes']
        elif action == 'native_calibration_settled':
            _exact(details, {'pool_id', 'artifact_id'}, 'Exact native settlement event required')
            artifact = decode(canonical(load_artifact(details['artifact_id'])))
            require(artifact['id'] == details['artifact_id'], 'Native settlement identity differs')
            body, task, reservation, compute, storage, overrun = self._settlement(artifact)
            self.pending.pop(body['attempt_id'])
            self.seen_results.add(artifact['id'])
            self.compute += compute - reservation['compute_ms']
            self.storage += storage - reservation['storage_bytes']
            state = body['resource_state']
            self.records[task] = {'state': state, 'artifact_id': artifact['id'], 'attempt_id': body['attempt_id']}
            self.unknown = self.unknown or not body['settlement']['usage_known'] or state == 'ORPHAN_UNCERTAIN'
            self.overrun = self.overrun or overrun
            if state in ('FAILED', 'ORPHAN_UNCERTAIN') or self.unknown or self.overrun:
                self.halted = True
                self.halt_reasons.append(state if not overrun else 'RESOURCE_OVERRUN')
            if (state in ('COMPLETE', 'KNOWN_TIMEOUT') and not overrun
                    and task not in self.progress_tasks):
                self.progress_tasks.add(task)
                self.progress += 1
        elif action == 'native_calibration_continued':
            _exact(details, {'pool_id', 'artifact_id'}, 'Exact native continuation event required')
            artifact = decode(canonical(load_artifact(details['artifact_id'])))
            refs = (self.pool_id,) + ((self.grants[-1]['id'],) if self.grants else ())
            body = _owned(artifact, GRANT, AUTHORITY, refs)
            require(artifact['id'] == details['artifact_id'] and artifact.get('blob_refs') == [],
                    'Native continuation custody differs')
            terms = self.continuation_terms(body['request'])
            require(canonical(body['terms']) == canonical(terms), 'Native continuation terms differ')
            self.allocated_compute += body['request']['additional_compute_ms']
            self.allocated_storage += body['request']['additional_storage_bytes']
            self.storage += META
            self.grants.append(artifact)
            self.last_grant_progress = self.progress
            self.no_progress = terms['no_progress_grants']
        else:
            _exact(details, {'pool_id', 'reason'}, 'Exact native stop event required')
            reason = text(details['reason'], 'Native stop reason')
            self.halted = True
            self.halt_reasons.append(reason)
        self.overrun = self.overrun or self.compute > self.allocated_compute or self.storage > self.allocated_storage
        self.halted = self.halted or self.overrun
        self.hasher.update(b'\n' + canonical(event).encode())
