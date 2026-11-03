"""Independent finite native ledger expectations; metadata events only.

Owned artifact envelopes are explicit in-memory fixtures, not custody/admission
certificates. No Registry, child, numerical calculation or retry is executed.
Carried costs remain charges; historical progress is operational bookkeeping.
"""
from copy import deepcopy
import importlib
import importlib.util
import unittest

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.errors import Conflict, Denied


POOL = 'native-calibration-resource-pool/1'
INVENTORY = 'native-calibration-resource-inventory/1'
GRANT = 'native-calibration-resource-grant/1'
AUTHORITY = 'bounded_native_calibration_resources_not_scientific_admission'
FINAL_AUTHORITY = 'conditional_native_joint_family_calibration_not_scientific_admission'
RESULT_SCHEMAS = {'setup': 'native-calibration-setup-attempt/1',
                  'acceptance': 'native-calibration-acceptance-attempt/1',
                  'final': 'native-family-calibration-attempt/1'}
MIB, GIB = 1048576, 1073741824
COMPUTE, STORAGE = 65000, 8 * MIB
ERRORS = (Invalid, Conflict, Denied)
CARRY = {'schema': 'native-calibration-resource-carry/1', 'basis_id': 'b' * 64,
         'charged_compute_ms': 5029797, 'charged_storage_bytes': 887402753,
         'allocated_compute_ms': 7200000, 'allocated_storage_bytes': 8 * GIB,
         'grants_used': 1, 'progress_units': 19, 'last_grant_progress': 14,
         'no_progress_grants': 0}


def artifact(body, *, refs=(), authority=AUTHORITY):
    envelope = {'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
                'data_class': 'operations', 'authority': authority, 'source_refs': sorted(set(refs)),
                'exposure': sorted(set(refs)), 'blob_refs': [], 'body': deepcopy(body)}
    return {'id': digest(envelope), **envelope}


def pool(**carry_changes):
    return artifact({'schema': POOL, 'created_at': 1,
                     'carry': {**deepcopy(CARRY), **carry_changes},
                     'max_parallel': 6, 'scientific_readiness': False})


def task(index):
    return format(index + 1, '064x')


def owner():
    return importlib.import_module('trading_researcher.native_calibration_resources')


class NativeResourceEntrypointIndependentTests(unittest.TestCase):
    def test_owning_ledger_entrypoint_exists_before_event_semantics_can_run(self):
        self.assertIsNotNone(importlib.util.find_spec('trading_researcher.native_calibration_resources'),
                             'The native finite ledger owner is absent; zero event-flow coverage')
        self.assertTrue(callable(getattr(owner(), 'NativeResourceHistory', None)))


class NativeCalibrationResourcesIndependentTests(unittest.TestCase):
    def setUp(self):
        self.reset()

    def reset(self, **carry):
        self.pool = pool(**carry)
        self.h = owner().NativeResourceHistory(self.pool)
        self.artifacts = {self.pool['id']: deepcopy(self.pool)}
        self.events = []
        self.attempt_serial = 0

    def event(self, action, **details):
        return {'time': len(self.events) + 2, 'actor': 'controller', 'action': action,
                'details': {'pool_id': self.pool['id'], **details}}

    def apply(self, event):
        self.h.apply(event, self.artifacts.__getitem__)
        self.events.append(deepcopy(event))

    def snapshot(self):
        return deepcopy(self.h.budget()), self.h.checkpoint

    def rejected(self, operation):
        before = self.snapshot()
        with self.assertRaises(ERRORS): operation()
        self.assertEqual(self.snapshot(), before)

    def inventory_request(self, phase='final', count=8, **changes):
        return {'pool_id': self.pool['id'], 'key': 'fixed-' + phase, 'phase': phase,
                'task_ids': [task(index) for index in range(count)],
                'execution_deadline_ms': 60000, 'attempt_compute_ms': COMPUTE,
                'attempt_storage_bytes': STORAGE, 'max_attempts': 2 if phase == 'final' else 1,
                'expected_checkpoint': self.h.checkpoint, **changes}

    def bind(self, phase='final', count=8, **changes):
        request = self.inventory_request(phase, count, **changes)
        self.assertEqual(self.h.inventory_terms(request), request)
        item = artifact({'schema': INVENTORY, 'created_at': 2, 'request': request,
                         'scientific_readiness': False}, refs=[self.pool['id']])
        self.artifacts[item['id']] = item
        self.apply(self.event('native_calibration_inventory_bound', artifact_id=item['id']))
        return item

    def reserve_request(self, index=0, phase='final', **changes):
        self.attempt_serial += 1
        return {'pool_id': self.pool['id'], 'phase': phase, 'task_id': task(index),
                'attempt_id': format(self.attempt_serial, '032x'),
                'expected_checkpoint': self.h.checkpoint, **changes}

    def reserve(self, index=0, phase='final'):
        request = self.reserve_request(index, phase)
        terms = self.h.reservation_terms(request)
        self.assertEqual({key: terms[key] for key in request}, request)
        self.apply(self.event('native_calibration_reserved', reservation=terms))
        return terms

    def result(self, reservation, *, state='COMPLETE', compute=1000, storage=1234,
               known=True, currency=True, failure=None, failures=None):
        return artifact({'schema': RESULT_SCHEMAS[reservation['phase']], 'created_at': 3,
            'resource_pool_id': self.pool['id'], 'phase': reservation['phase'],
            'task_id': reservation['task_id'], 'attempt_id': reservation['attempt_id'],
            'settlement': {'attempt_id': reservation['attempt_id'], 'compute_ms': compute,
                           'storage_bytes': storage, 'usage_known': known},
            'resource_state': state, 'currency_checked': currency, 'failure': failure,
            'failures': ([] if failure is None else [deepcopy(failure)]) if failures is None else failures,
            'scientific_readiness': False}, refs=[self.pool['id'], reservation['inventory_id']],
            authority=FINAL_AUTHORITY if reservation['phase'] == 'final' else AUTHORITY)

    def settle(self, reservation, **options):
        item = self.result(reservation, **options)
        self.artifacts[item['id']] = item
        self.apply(self.event('native_calibration_settled', artifact_id=item['id']))
        return item

    def grant_request(self, index=0, phase='final', **changes):
        budget = self.h.budget()
        return {'key': 'finite-grant-' + self.h.checkpoint, 'pool_id': self.pool['id'],
            'phase': phase, 'task_id': task(index), 'expected_checkpoint': self.h.checkpoint,
            'additional_compute_ms': min(3600000, 648000000 - budget['allocated_compute_ms']),
            'additional_storage_bytes': min(4 * GIB, 100 * GIB - budget['allocated_storage_bytes']),
            'rationale': 'Continue the fixed owned inventory within the retained aggregate authority.',
            'expected_progress': 'Complete the next eligible task with full source and accounting checks.',
            'stop_reason': 'Stop at a technical, integrity, unknown-use or aggregate boundary.', **changes}

    def grant(self, **changes):
        request = self.grant_request(**changes)
        terms = self.h.continuation_terms(request)
        refs = [self.pool['id']]
        if terms['previous_continuation_id'] is not None: refs.append(terms['previous_continuation_id'])
        item = artifact({'schema': GRANT, 'created_at': 4, 'request': request, 'terms': terms,
                         'scientific_readiness': False}, refs=refs)
        self.artifacts[item['id']] = item
        self.apply(self.event('native_calibration_continued', artifact_id=item['id']))
        return item

    def test_immutable_carry_retains_charges_allocations_grants_progress_without_old_health(self):
        budget = self.h.budget()
        for key in ('charged_compute_ms', 'charged_storage_bytes', 'allocated_compute_ms',
                    'allocated_storage_bytes', 'grants_used', 'progress_units', 'no_progress_grants'):
            self.assertEqual(budget[key], CARRY[key])
        self.assertEqual(budget['grants_remaining'], 178)
        self.assertEqual(budget['outstanding_attempts'], [])
        for key in ('usage_uncertain', 'overrun', 'halted'): self.assertIs(budget[key], False)
        checkpoint = self.h.checkpoint
        self.pool['body']['carry'].update(charged_compute_ms=0, charged_storage_bytes=0, grants_used=0)
        self.assertEqual(self.h.budget(), budget); self.assertEqual(self.h.checkpoint, checkpoint)

    def test_malformed_pool_authority_limits_and_boolean_carry_reject(self):
        cases = [(('creator',), 'operator'), (('origin',), 'source'),
            (('data_class',), 'development'), (('authority',), 'caller-approved'),
            (('body', 'schema'), 'other/1'), (('body', 'max_parallel'), 7),
            (('body', 'max_parallel'), True), (('body', 'scientific_readiness'), True),
            (('body', 'carry', 'basis_id'), 'B' * 64),
            (('body', 'carry', 'charged_compute_ms'), True),
            (('body', 'carry', 'charged_storage_bytes'), -1),
            (('body', 'carry', 'allocated_compute_ms'), 648000001),
            (('body', 'carry', 'allocated_storage_bytes'), 100 * GIB + 1),
            (('body', 'carry', 'grants_used'), 180),
            (('body', 'carry', 'last_grant_progress'), 20),
            (('body', 'carry', 'no_progress_grants'), 3)]
        for index, (path, value) in enumerate(cases):
            item = pool(); target = item
            for key in path[:-1]: target = target[key]
            target[path[-1]] = value
            item['id'] = digest({key: value for key, value in item.items() if key != 'id'})
            with self.subTest(index=index), self.assertRaises(ERRORS): owner().NativeResourceHistory(item)

    def test_inventory_phase_caps_exact_shape_and_cleanup_margin(self):
        for phase, maximum in (('setup', 16), ('acceptance', 64), ('final', 2048)):
            valid = self.inventory_request(phase, maximum)
            self.assertEqual(self.h.inventory_terms(valid), valid)
            changes = [{'task_ids': valid['task_ids'] + [task(maximum)]},
                       {'task_ids': [task(1), task(0)]}, {'task_ids': [task(0), task(0)]},
                       {'task_ids': []}, {'attempt_compute_ms': 64999},
                       {'execution_deadline_ms': True}, {'execution_deadline_ms': 0},
                       {'attempt_storage_bytes': 256 * MIB + 1}, {'max_attempts': 3},
                       {'expected_checkpoint': 'f' * 64}, {'approved': True}]
            if phase != 'final': changes.append({'max_attempts': 2})
            for index, change in enumerate(changes):
                with self.subTest(phase=phase, index=index):
                    self.rejected(lambda change=change: self.h.inventory_terms({**valid, **change}))

    def test_inventory_metadata_charged_once_no_phase_alias_or_rebinding(self):
        before = self.snapshot(); item = self.bind(count=7)
        self.assertEqual(self.h.budget()['charged_storage_bytes'], CARRY['charged_storage_bytes'] + MIB)
        self.assertNotEqual(self.h.checkpoint, before[1])
        self.rejected(lambda: self.h.inventory_terms(self.inventory_request(key='alias', count=7)))
        self.rejected(lambda: self.apply(self.event('native_calibration_inventory_bound', artifact_id=item['id'])))
        self.bind('setup', 1); self.bind('acceptance', 1)
        self.assertEqual(self.h.budget()['charged_storage_bytes'], CARRY['charged_storage_bytes'] + 3 * MIB)
        self.assertEqual(self.h.budget()['progress_units'], 19)

    def test_six_full_pending_reservations_and_seventh_or_same_task_denied_atomically(self):
        inventory = self.bind(count=7)
        reservations = [self.reserve(index) for index in range(6)]
        for item in reservations:
            self.assertEqual(item['inventory_id'], inventory['id'])
            self.assertEqual(item['compute_ms'], COMPUTE); self.assertEqual(item['storage_bytes'], STORAGE)
        budget = self.h.budget()
        self.assertEqual(set(budget['outstanding_attempts']), {item['attempt_id'] for item in reservations})
        self.assertEqual(budget['charged_compute_ms'], CARRY['charged_compute_ms'] + 6 * COMPUTE)
        self.assertEqual(budget['charged_storage_bytes'], CARRY['charged_storage_bytes'] + MIB + 6 * STORAGE)
        self.rejected(lambda: self.h.reservation_terms(self.reserve_request(6)))
        self.rejected(lambda: self.h.reservation_terms(self.reserve_request(0)))

    def test_reservation_equality_and_one_unit_short_in_each_resource(self):
        for dimension in ('equal', 'compute', 'storage'):
            self.reset(charged_compute_ms=7200000 - COMPUTE + (dimension == 'compute'),
                       charged_storage_bytes=8 * GIB - MIB - STORAGE + (dimension == 'storage'))
            self.bind(count=1)
            if dimension == 'equal':
                self.reserve()
                self.assertEqual(self.h.budget()['charged_compute_ms'], 7200000)
                self.assertEqual(self.h.budget()['charged_storage_bytes'], 8 * GIB)
            else:
                self.rejected(lambda: self.h.reservation_terms(self.reserve_request()))

    def test_stale_unplanned_duplicate_or_forged_reservation_cannot_mutate(self):
        self.bind(count=2); stale = self.reserve_request(); first = self.reserve(1)
        self.rejected(lambda: self.h.reservation_terms(stale))
        fresh = self.reserve_request()
        for changes in ({'task_id': task(100)}, {'attempt_id': 'A' * 32}, {'attempt_id': True},
                        {'phase': 'other'}, {'compute_ms': 1}, {'pool_id': 'f' * 64}):
            self.rejected(lambda changes=changes: self.h.reservation_terms({**fresh, **changes}))
        self.rejected(lambda: self.apply(self.event('native_calibration_reserved', reservation=first)))

    def test_known_settlement_replaces_reservation_by_actual_cost_and_completed_task_cannot_retry(self):
        self.bind(count=2); reservation = self.reserve()
        before = self.h.budget(); self.settle(reservation, compute=123, storage=456)
        budget = self.h.budget()
        self.assertEqual(budget['charged_compute_ms'], CARRY['charged_compute_ms'] + 123)
        self.assertEqual(budget['charged_storage_bytes'], CARRY['charged_storage_bytes'] + MIB + 456)
        self.assertEqual(budget['outstanding_attempts'], []); self.assertEqual(budget['progress_units'], 20)
        self.assertGreater(before['charged_compute_ms'], budget['charged_compute_ms'])
        self.rejected(lambda: self.h.reservation_terms(self.reserve_request()))

    def test_out_of_order_six_settlements_drain_with_exact_retained_costs(self):
        self.bind(count=6); reservations = [self.reserve(index) for index in range(6)]
        for index in (5, 1, 4, 0, 3, 2): self.settle(reservations[index], compute=index + 1, storage=10 * (index + 1))
        budget = self.h.budget()
        self.assertEqual(budget['charged_compute_ms'], CARRY['charged_compute_ms'] + 21)
        self.assertEqual(budget['charged_storage_bytes'], CARRY['charged_storage_bytes'] + MIB + 210)
        self.assertEqual(budget['outstanding_attempts'], []); self.assertEqual(budget['progress_units'], 25)

    def test_three_authenticated_clock_types_allow_one_final_retry_and_one_progress_unit(self):
        for kind in ('ChildDeadlineExceeded', 'AttemptDeadlineExceeded', 'AuthenticatedCalculatorDeadline'):
            self.reset(); self.bind(count=2); reservation = self.reserve()
            self.settle(reservation, state='KNOWN_TIMEOUT', failure={'type': kind, 'message': 'Synthetic owned clock'})
            retry = self.reserve(); self.assertNotEqual(retry['attempt_id'], reservation['attempt_id'])
            self.settle(retry)
            self.assertEqual(self.h.budget()['progress_units'], 20)
            self.rejected(lambda: self.h.reservation_terms(self.reserve_request()))
            self.reserve(1)

    def test_second_clock_exhaustion_keeps_independent_tasks_eligible_and_unresolved_task_visible(self):
        self.bind(count=2)
        for _ in range(2):
            reservation = self.reserve()
            self.settle(reservation, state='KNOWN_TIMEOUT', failure={'type': 'ChildDeadlineExceeded', 'message': 'Synthetic clock'})
        self.rejected(lambda: self.h.reservation_terms(self.reserve_request()))
        budget = self.h.budget()
        self.assertIs(budget['halted'], False); self.assertIs(budget['usage_uncertain'], False)
        self.assertEqual(budget['progress_units'], 20)
        self.reserve(1)

    def test_setup_and_acceptance_clock_does_not_acquire_a_retry_or_scientific_authority(self):
        for phase in ('setup', 'acceptance'):
            self.reset(); self.bind(phase, 2); reservation = self.reserve(phase=phase)
            self.settle(reservation, state='KNOWN_TIMEOUT', failure={'type': 'ChildDeadlineExceeded', 'message': 'Synthetic clock'})
            self.rejected(lambda phase=phase: self.h.reservation_terms(self.reserve_request(phase=phase)))
            self.assertEqual(self.h.budget()['progress_units'], 20)

    def test_forged_clock_currency_or_failure_list_never_releases_reserved_use(self):
        self.bind(count=1); reservation = self.reserve()
        base = self.result(reservation, state='KNOWN_TIMEOUT', failure={'type': 'ChildDeadlineExceeded', 'message': 'Owned synthetic cause'})
        changes = [{'failure': {'type': kind, 'message': 'deadline expired'},
                    'failures': [{'type': kind, 'message': 'deadline expired'}]}
                   for kind in ('Invalid', 'TimeoutError', 'ResourceOverrun', 'caller_cancelled')]
        changes += [{'currency_checked': False}, {'failures': []},
                    {'failures': [base['body']['failure'], {'type': 'IntegrityFailure', 'message': 'also failed'}]},
                    {'settlement': {**base['body']['settlement'], 'usage_known': False}}]
        for index, change in enumerate(changes):
            item = artifact({**base['body'], **change}, refs=base['source_refs'], authority=FINAL_AUTHORITY)
            self.artifacts[item['id']] = item
            with self.subTest(index=index):
                self.rejected(lambda item=item: self.apply(self.event('native_calibration_settled', artifact_id=item['id'])))
        self.assertEqual(self.h.budget()['outstanding_attempts'], [reservation['attempt_id']])

    def test_unknown_use_is_conservative_sticky_and_other_pending_results_still_drain(self):
        self.bind(count=3); first = self.reserve(); second = self.reserve(1)
        self.settle(first, state='FAILED', known=False, compute=1, storage=2,
                    failure={'type': 'ChildCleanupFailed', 'message': 'Synthetic unreaped writer'})
        budget = self.h.budget()
        self.assertIs(budget['usage_uncertain'], True); self.assertIs(budget['halted'], True)
        self.assertEqual(budget['charged_compute_ms'], CARRY['charged_compute_ms'] + 2 * COMPUTE)
        self.assertEqual(budget['charged_storage_bytes'], CARRY['charged_storage_bytes'] + MIB + 2 * STORAGE)
        self.rejected(lambda: self.h.reservation_terms(self.reserve_request(2)))
        self.rejected(lambda: self.h.continuation_terms(self.grant_request(index=2)))
        self.settle(second, compute=3, storage=4)
        budget = self.h.budget()
        self.assertEqual(budget['charged_compute_ms'], CARRY['charged_compute_ms'] + COMPUTE + 3)
        self.assertEqual(budget['charged_storage_bytes'], CARRY['charged_storage_bytes'] + MIB + STORAGE + 4)
        self.assertEqual(budget['outstanding_attempts'], []); self.assertIs(budget['usage_uncertain'], True)

    def test_known_observed_overrun_halts_even_clock_and_cannot_be_healed_by_grant(self):
        self.bind(count=2); reservation = self.reserve()
        self.settle(reservation, state='KNOWN_TIMEOUT', compute=COMPUTE + 1,
                    failure={'type': 'ChildDeadlineExceeded', 'message': 'Clock plus known excess'})
        budget = self.h.budget()
        self.assertEqual(budget['charged_compute_ms'], CARRY['charged_compute_ms'] + COMPUTE + 1)
        self.assertIs(budget['overrun'], True); self.assertIs(budget['halted'], True)
        self.rejected(lambda: self.h.reservation_terms(self.reserve_request(1)))
        self.rejected(lambda: self.h.continuation_terms(self.grant_request(index=1)))

    def test_failed_currentness_or_orphan_is_globally_fatal_and_retains_usage(self):
        for state, known, currency, kind in (('FAILED', True, False, 'DependencyRevoked'),
                                           ('ORPHAN_UNCERTAIN', False, False, 'Interrupted')):
            self.reset(); self.bind(count=2); reservation = self.reserve()
            self.settle(reservation, state=state, known=known, currency=currency,
                        failure={'type': kind, 'message': 'Synthetic retained failure'})
            budget = self.h.budget(); self.assertIs(budget['halted'], True)
            self.rejected(lambda: self.h.reservation_terms(self.reserve_request(1)))
            self.assertGreater(budget['charged_compute_ms'], CARRY['charged_compute_ms'])

    def test_bad_owned_settlement_binding_authority_or_duplicate_cannot_mutate(self):
        self.bind(count=1); reservation = self.reserve(); base = self.result(reservation)
        variants = []
        for field, value in (('creator', 'operator'), ('origin', 'source'), ('data_class', 'development'),
                             ('authority', AUTHORITY), ('source_refs', [self.pool['id']])):
            item = deepcopy(base); item[field] = value; variants.append(item)
        for field, value in (('schema', RESULT_SCHEMAS['setup']), ('phase', 'setup'),
                ('resource_pool_id', 'f' * 64), ('task_id', task(55)), ('attempt_id', 'a' * 32),
                ('currency_checked', False), ('failure', {'type': 'Invalid', 'message': 'conflict'}),
                ('scientific_readiness', True)):
            item = deepcopy(base); item['body'][field] = value; variants.append(item)
        for value in (-1, True):
            item = deepcopy(base); item['body']['settlement']['compute_ms'] = value; variants.append(item)
        for index, item in enumerate(variants):
            item['id'] = digest({key: value for key, value in item.items() if key != 'id'})
            self.artifacts[item['id']] = item
            with self.subTest(index=index):
                self.rejected(lambda item=item: self.apply(self.event('native_calibration_settled', artifact_id=item['id'])))
        completed = self.settle(reservation)
        self.rejected(lambda: self.apply(self.event('native_calibration_settled', artifact_id=completed['id'])))

    def test_grant_requires_real_stop_drain_exact_paired_tranches_and_one_metadata_fee(self):
        self.rejected(lambda: self.h.continuation_terms(self.grant_request()))
        self.reset(charged_compute_ms=7200000 - COMPUTE + 1); self.bind(count=2)
        request = self.grant_request(); terms = self.h.continuation_terms(request)
        self.assertEqual(terms, {**request, 'previous_continuation_id': None,
            'charged_compute_ms_before': 7200000 - COMPUTE + 1,
            'charged_storage_bytes_before': CARRY['charged_storage_bytes'] + MIB,
            'progress_units_before': 19, 'no_progress_grants': 0})
        for change in ({'additional_storage_bytes': 0}, {'additional_compute_ms': 3599999},
                       {'additional_compute_ms': True}, {'expected_checkpoint': 'f' * 64}):
            self.rejected(lambda change=change: self.h.continuation_terms({**request, **change}))
        before = self.h.budget(); grant = self.grant(); budget = self.h.budget()
        self.assertEqual(budget['allocated_compute_ms'], 10800000)
        self.assertEqual(budget['allocated_storage_bytes'], 12 * GIB)
        self.assertEqual(budget['charged_compute_ms'], before['charged_compute_ms'])
        self.assertEqual(budget['charged_storage_bytes'], before['charged_storage_bytes'] + MIB)
        self.assertEqual(budget['grants_used'], 2); self.assertEqual(budget['grants_remaining'], 177)
        self.rejected(lambda: self.apply(self.event('native_calibration_continued', artifact_id=grant['id'])))
        self.reserve()
        self.rejected(lambda: self.h.continuation_terms(self.grant_request(index=1)))

    def test_ready_inventory_cannot_receive_extra_capacity(self):
        self.bind(count=1)
        self.rejected(lambda: self.h.continuation_terms(self.grant_request()))

    def test_179_total_limit_includes_carry_on_storage_only_stop(self):
        self.reset(grants_used=179, allocated_compute_ms=648000000, allocated_storage_bytes=100 * GIB,
                   charged_storage_bytes=100 * GIB - MIB - STORAGE + 1)
        self.bind(count=1)
        self.assertEqual(self.h.budget()['grants_remaining'], 0)
        self.rejected(lambda: self.h.continuation_terms(self.grant_request()))

    def test_one_exhausted_aggregate_dimension_only_allows_zero_tranche_if_next_task_still_fits(self):
        self.reset(grants_used=178, allocated_compute_ms=644400000,
                   allocated_storage_bytes=100 * GIB, charged_compute_ms=644400000 - COMPUTE + 1)
        self.bind(count=1); request = self.grant_request()
        self.assertEqual((request['additional_compute_ms'], request['additional_storage_bytes']), (3600000, 0))
        self.grant(); self.assertEqual(self.h.budget()['grants_used'], 179)
        self.reserve()
        # Original1h +178 bounded1h grants can allocate at most179h. Full180h
        # before grant179 was an invalid authored fixture, not spare authority.
        unreachable = pool(grants_used=178, allocated_compute_ms=648000000,
                           allocated_storage_bytes=96 * GIB)
        with self.assertRaises(Invalid): owner().NativeResourceHistory(unreachable)
        self.reset(grants_used=179, allocated_compute_ms=648000000,
                   allocated_storage_bytes=96 * GIB,
                   charged_storage_bytes=96 * GIB - MIB - STORAGE + 1)
        self.bind(count=1)
        self.assertEqual(self.h.budget()['grants_remaining'], 0)
        self.rejected(lambda: self.h.continuation_terms(self.grant_request()))

    def test_grant_metadata_plus_full_next_reservation_fit_at_global_equality_and_one_byte_short(self):
        for extra in (0, 1):
            self.reset(grants_used=178, allocated_compute_ms=644400000,
                       allocated_storage_bytes=100 * GIB,
                       charged_compute_ms=644400000 - COMPUTE + 1,
                       charged_storage_bytes=100 * GIB - 2 * MIB - STORAGE + extra)
            self.bind(count=1)
            if extra:
                self.rejected(lambda: self.h.continuation_terms(self.grant_request()))
            else:
                self.grant(); self.reserve()
                self.assertEqual(self.h.budget()['charged_storage_bytes'], 100 * GIB)

    def test_no_progress_state_from_carry_allows_at_most_two_grants(self):
        for previous in (0, 1, 2):
            self.reset(charged_compute_ms=7200000 - COMPUTE + 1,
                       last_grant_progress=19, no_progress_grants=previous)
            self.bind(count=1)
            if previous < 2:
                self.assertEqual(self.h.continuation_terms(self.grant_request())['no_progress_grants'], previous + 1)
            else:
                self.rejected(lambda: self.h.continuation_terms(self.grant_request()))

    def test_explicit_stop_is_sticky_but_pending_results_can_still_drain(self):
        self.bind(count=2); reservation = self.reserve()
        self.apply(self.event('native_calibration_stopped', reason='Physical reserve forecast failed'))
        self.assertIs(self.h.budget()['halted'], True)
        self.rejected(lambda: self.h.reservation_terms(self.reserve_request(1)))
        self.settle(reservation)
        self.assertIs(self.h.budget()['halted'], True)
        self.assertEqual(self.h.budget()['outstanding_attempts'], [])

    def test_other_pool_noncontroller_or_unknown_actions_do_not_change_checkpoint_or_cost(self):
        before = self.snapshot()
        events = [self.event('native_calibration_stopped', reason='foreign'),
                  self.event('native_calibration_stopped', pool_id='f' * 64, reason='foreign'),
                  self.event('not-a-native-ledger-event', reason='ignored')]
        events[0]['actor'] = 'operator'
        for event in events:
            self.h.apply(event, lambda identity: self.fail('Ignored event loaded artifact'))
            self.assertEqual(self.snapshot(), before)

    def test_replaying_accepted_prefix_restores_pending_cost_retry_eligibility_and_checkpoint(self):
        self.bind(count=3); first = self.reserve(); second = self.reserve(1)
        self.settle(first, state='KNOWN_TIMEOUT', failure={'type': 'ChildDeadlineExceeded', 'message': 'Synthetic owned clock'})
        retry = self.reserve()
        rebuilt = owner().NativeResourceHistory(deepcopy(self.pool))
        for event in self.events: rebuilt.apply(deepcopy(event), self.artifacts.__getitem__)
        self.assertEqual(rebuilt.budget(), self.h.budget()); self.assertEqual(rebuilt.checkpoint, self.h.checkpoint)
        self.assertEqual(set(rebuilt.budget()['outstanding_attempts']), {second['attempt_id'], retry['attempt_id']})
        request = self.reserve_request(2)
        self.assertEqual(rebuilt.reservation_terms(request), self.h.reservation_terms(request))

    def test_forged_inventory_and_grant_artifact_bindings_cannot_mutate_prefix(self):
        request = self.inventory_request(count=1)
        base = artifact({'schema': INVENTORY, 'created_at': 2, 'request': request,
                         'scientific_readiness': False}, refs=[self.pool['id']])
        for field, value in (('authority', 'caller-approved'), ('source_refs', []), ('creator', 'operator')):
            item = deepcopy(base); item[field] = value
            item['id'] = digest({key: value for key, value in item.items() if key != 'id'})
            self.artifacts[item['id']] = item
            self.rejected(lambda item=item: self.apply(self.event('native_calibration_inventory_bound', artifact_id=item['id'])))
        self.reset(charged_compute_ms=7200000 - COMPUTE + 1); self.bind(count=1)
        request = self.grant_request(); terms = self.h.continuation_terms(request)
        base = artifact({'schema': GRANT, 'created_at': 4, 'request': request,
                         'terms': terms, 'scientific_readiness': False}, refs=[self.pool['id']])
        variants = []
        for field, value in (('authority', 'caller-approved'), ('source_refs', []), ('data_class', 'development')):
            item = deepcopy(base); item[field] = value; variants.append(item)
        item = deepcopy(base); item['body']['terms']['charged_compute_ms_before'] -= 1; variants.append(item)
        item = deepcopy(base); item['body']['request']['additional_storage_bytes'] = 0; variants.append(item)
        for item in variants:
            item['id'] = digest({key: value for key, value in item.items() if key != 'id'})
            self.artifacts[item['id']] = item
            self.rejected(lambda item=item: self.apply(self.event('native_calibration_continued', artifact_id=item['id'])))

    def test_native_grant_chain_keeps_previous_owned_decision_and_operational_progress(self):
        self.reset(charged_compute_ms=3600001)
        self.bind(count=2, execution_deadline_ms=3595000, attempt_compute_ms=3600000)
        first = self.grant()
        reservation = self.reserve()
        self.settle(reservation, compute=3600000)
        second = self.grant(index=1)
        self.assertEqual(second['body']['terms']['previous_continuation_id'], first['id'])
        self.assertEqual(second['source_refs'], sorted([self.pool['id'], first['id']]))
        self.assertEqual(second['body']['terms']['progress_units_before'], 20)
        self.assertEqual(second['body']['terms']['no_progress_grants'], 0)
        self.assertEqual(self.h.budget()['grants_used'], 3)
        self.assertEqual(self.h.budget()['charged_compute_ms'], 7200001)
        self.assertEqual(self.h.budget()['charged_storage_bytes'], CARRY['charged_storage_bytes'] + 3 * MIB + 1234)


if __name__ == '__main__':
    unittest.main()
