"""Independent finite-controller controls, not native numerical admission.

Forecast expectations below are hand-derived engineering arithmetic. Scheduler
cases use real temporary Registry/resource owners and an explicitly synthetic
caller settlement seam; the ledger and scheduler are never replaced.
"""
from copy import deepcopy
from contextlib import closing
from fractions import Fraction
import hashlib
import importlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import time
import types
import unittest
from unittest.mock import patch

import test_native_calibration_resource_owner_independent as financial_support
from trading_researcher import native_calibration_runs, study_runs
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.native_runtime import NativeRuntimes
from trading_researcher.storage import restore_bundle


MIB = 1048576
GIB = 1024 ** 3
ERRORS = (Invalid, Conflict, Denied, OSError)
DRIVER = b'# Explicit trusted scheduler fixture driver; never executed.\n'


def controller_module():
    return importlib.import_module('trading_researcher.native_calibration_controller')


def worlds(count):
    return [{'id': format(i + 1, '064x'), 'time_rows': 4096,
             'spec_index': 0, 'pattern_index': 0, 'replicate': i} for i in range(count)]


def observed(world, ordinal, state='COMPLETE', *, compute=1000, storage=5 * MIB, outputs=None):
    return {'world_id': world['id'], 'attempt_id': format(ordinal, '032x'), 'resource_state': state,
            'settlement': {'compute_ms': compute, 'storage_bytes': storage, 'usage_known': True},
            'output_blobs': {} if outputs is None else outputs}


def forecast_args():
    return {'fallback': {'0/0': {'compute_ms': 1000, 'storage_bytes': 5 * MIB, 'retained_bytes': 3 * MIB}},
            'elapsed_ms': 100, 'final_elapsed_ms': 0, 'deadline_ms': 2000,
            'charged_storage_bytes': 0, 'copy_overhead_ms': 50, 'primary_bytes': 10 * MIB,
            'prepared_copies': 0, 'terminal_copies': 2}


class NativeControllerForecastIndependentTests(unittest.TestCase):
    def test_round_robin_uses_replicate_then_target_spec_pattern_id_without_mutation(self):
        rows = worlds(8)
        coordinates = [(1, 2, 0, 0), (0, 3, 1, 0), (0, 2, 1, 1), (0, 2, 0, 2),
                       (1, 3, 0, 0), (0, 2, 0, 1), (0, 2, 0, 1), (0, 2, 0, 1)]
        for row, (rep, size, spec, pattern) in zip(rows, coordinates):
            row.update(replicate=rep, time_rows=size, spec_index=spec, pattern_index=pattern)
        before = deepcopy(rows)
        expected = [rows[i]['id'] for i in (5, 6, 7, 3, 2, 1, 0, 4)]
        self.assertEqual(controller_module().round_robin(list(reversed(rows))), expected)
        self.assertEqual(rows, before)

    def test_unmeasured_forecast_has_explicit_six_way_plan_one_retry_floor_and_full_copy_growth(self):
        rows = worlds(4); args = forecast_args()
        result = controller_module().forecast({'worlds': rows}, [], [], **args)
        # Work=(4*1000 + 32000)/6=6000ms. G=5*3.75MiB=18.75MiB.
        self.assertEqual(result['total_wall_ms'], 6150)
        self.assertEqual(result['logical_forecast_bytes'], 276 * MIB)
        self.assertEqual(result['required_free_bytes'], 20 * GIB + 1628 * MIB + MIB // 4)
        self.assertEqual(result['future_retry_reserve_worlds'], 1)
        self.assertEqual(result['terminal_worlds'], 0); self.assertEqual(result['unavailable_worlds'], 0)
        self.assertIs(result['effective_parallelism_measured'], False)
        self.assertEqual(Fraction(**{'numerator': result['effective_parallelism']['num'],
                                    'denominator': result['effective_parallelism']['den']}), 6)
        self.assertIs(result['time_exceeds_24h'], False)

    def test_measured_half_parallelism_and_same_hash_output_dedup_use_hand_fixed_bytes(self):
        rows = worlds(4); args = forecast_args()
        outputs = {'generate': {'sha256': 'a' * 64, 'size': 2 * MIB},
                   'replay': {'sha256': 'a' * 64, 'size': 2 * MIB},
                   'wire': {'sha256': 'b' * 64, 'size': MIB}}
        attempts = [observed(rows[0], 1, outputs=outputs)]
        args.update(elapsed_ms=1000, final_elapsed_ms=2000, charged_storage_bytes=7 * MIB,
                    prepared_copies=1, terminal_copies=2)
        result = controller_module().forecast({'worlds': rows}, attempts, [], **args)
        # P=1000/2000=1/2. Retained=2+1+1=4MiB; inflated5MiB, G=20MiB.
        self.assertEqual(result['effective_parallelism'], {'num': 1, 'den': 2})
        self.assertIs(result['effective_parallelism_measured'], True)
        self.assertEqual(result['total_wall_ms'], 71050)
        self.assertEqual(result['logical_forecast_bytes'], 278 * MIB)
        self.assertEqual(result['required_free_bytes'], 20 * GIB + 1642 * MIB)
        self.assertEqual(result['terminal_worlds'], 1)
        # Actual whole-call observations replace planning duration only. They
        # cannot rewrite the independently retained financial settlement.
        attempts[0]['whole_call_ms'] = 2000
        whole = controller_module().forecast({'worlds': rows}, attempts, [], **args)
        self.assertEqual(whole['effective_parallelism'], {'num': 1, 'den': 1})
        self.assertEqual(whole['total_wall_ms'], 39050)
        self.assertEqual(whole['logical_forecast_bytes'], 278 * MIB)
        self.assertEqual(attempts[0]['settlement']['compute_ms'], 1000)
        attempts[0].update(whole_call_ms=32000, timing_measured=False)
        missing = controller_module().forecast({'worlds': rows}, attempts, [], **args)
        self.assertIs(missing['effective_parallelism_measured'], False)
        self.assertEqual(missing['effective_parallelism'], {'num': 1, 'den': 1})
        self.assertEqual(missing['timing_missing_attempts'], 1)
        self.assertEqual(missing['total_wall_ms'], 129050)
        measured = observed(rows[1], 2, outputs=outputs); measured['whole_call_ms'] = 1000
        args['charged_storage_bytes'] = 12 * MIB
        mixed = controller_module().forecast({'worlds': rows}, [attempts[0], measured], [], **args)
        self.assertEqual(mixed['effective_parallelism'], {'num': 1, 'den': 2})
        self.assertIs(mixed['effective_parallelism_measured'], True)
        self.assertEqual(mixed['timing_missing_attempts'], 1)
        self.assertEqual(mixed['total_wall_ms'], 131050)

    def test_retry_rate_counts_first_attempt_worlds_and_mean_includes_all_settled_retries(self):
        rows = worlds(9); args = forecast_args()
        def output(size): return {'stream': {'sha256': 'c' * 64, 'size': size}}
        attempts = [observed(rows[0], 1, 'KNOWN_TIMEOUT', compute=2000, storage=10 * MIB, outputs=output(2 * MIB)),
                    observed(rows[1], 2, 'KNOWN_TIMEOUT', compute=1000, storage=8 * MIB, outputs=output(MIB)),
                    observed(rows[1], 3, 'KNOWN_TIMEOUT', compute=3000, storage=12 * MIB, outputs=output(5 * MIB)),
                    observed(rows[2], 4, compute=1000, storage=6 * MIB, outputs=output(2 * MIB))]
        args.update(elapsed_ms=10000, final_elapsed_ms=3500, charged_storage_bytes=400 * MIB,
                    copy_overhead_ms=100, terminal_copies=1)
        result = controller_module().forecast({'worlds': rows}, attempts, [], **args)
        # dMean=7000/4=1750; p=2/3, F=6 =>4contingent retries plus1due.
        # Work=6*1750+5*32000=170500; P=2. G=11*7.5MiB=82.5MiB.
        self.assertEqual(result['total_wall_ms'], 95350)
        self.assertEqual(result['logical_forecast_bytes'], 1752 * MIB)
        self.assertEqual(result['required_free_bytes'], 20 * GIB + 1727 * MIB)
        self.assertEqual(result['future_retry_reserve_worlds'], 4)
        self.assertEqual(result['terminal_worlds'], 2); self.assertEqual(result['unavailable_worlds'], 1)
        self.assertEqual(result['effective_parallelism'], {'num': 2, 'den': 1})

    def test_inflight_retry_keeps_full_existing_charge_without_future_double_count(self):
        rows = worlds(2); args = forecast_args()
        attempts = [observed(rows[0], 1, 'KNOWN_TIMEOUT', storage=3 * MIB), observed(rows[1], 2)]
        pending = [{'phase': 'final', 'task_id': rows[0]['id'], 'attempt_id': 'f' * 32,
                    'compute_ms': 5000, 'storage_bytes': 256 * MIB}]
        args.update(elapsed_ms=5000, final_elapsed_ms=2000, charged_storage_bytes=300 * MIB,
                    copy_overhead_ms=20, terminal_copies=0)
        result = controller_module().forecast({'worlds': rows}, attempts, pending, **args)
        self.assertEqual(result['total_wall_ms'], 37020)
        self.assertEqual(result['logical_forecast_bytes'], 300 * MIB)
        self.assertEqual(result['required_free_bytes'], 20 * GIB + 1555 * MIB + 3 * MIB // 4)
        self.assertEqual(result['future_retry_reserve_worlds'], 0)
        self.assertEqual(result['terminal_worlds'], 1); self.assertEqual(result['unavailable_worlds'], 0)

    def test_measured_parallelism_caps_at_six_and_wall_limit_is_strictly_greater_than_24h(self):
        rows = worlds(2); args = forecast_args()
        args.update(elapsed_ms=100000, final_elapsed_ms=1000, deadline_ms=20000, copy_overhead_ms=0)
        result = controller_module().forecast({'worlds': rows}, [observed(rows[0], 1, compute=12000)], [], **args)
        self.assertEqual(result['effective_parallelism'], {'num': 6, 'den': 1})
        self.assertEqual(result['total_wall_ms'], 110334)  # ceil((12000+50000)/6)+100000.
        one = worlds(1); args = forecast_args(); args.update(final_elapsed_ms=1000, copy_overhead_ms=1)
        for elapsed, exceeds in ((86400000 - 1, False), (86400000, True)):
            args['elapsed_ms'] = elapsed
            with self.subTest(elapsed=elapsed):
                result = controller_module().forecast({'worlds': one}, [observed(one[0], 1)], [], **args)
                self.assertEqual(result['total_wall_ms'], elapsed + 1)
                self.assertIs(result['time_exceeds_24h'], exceeds)

    def test_missing_unknown_inconsistent_or_zero_denominator_forecast_inputs_fail_closed(self):
        rows = worlds(2)
        for fault in ('missing_cell', 'unknown_usage', 'failed_state', 'duplicate_attempt', 'bad_retry',
                      'terminal_pending', 'zero_compute', 'zero_wall', 'conflicting_descriptors'):
            args = forecast_args(); args['final_elapsed_ms'] = 1000
            attempts = [observed(rows[0], 1)]; pending = []
            if fault == 'missing_cell': args['fallback'] = {}
            elif fault == 'unknown_usage': attempts[0]['settlement']['usage_known'] = False
            elif fault == 'failed_state': attempts[0]['resource_state'] = 'FAILED'
            elif fault == 'duplicate_attempt': attempts.append(deepcopy(attempts[0]))
            elif fault == 'bad_retry': attempts.append(observed(rows[0], 2))
            elif fault == 'terminal_pending': pending = [{'phase': 'final', 'task_id': rows[0]['id'], 'attempt_id': 'f' * 32}]
            elif fault == 'zero_compute': attempts[0]['settlement']['compute_ms'] = 0
            elif fault == 'zero_wall': args['final_elapsed_ms'] = 0
            else: attempts[0]['output_blobs'] = {'one': {'sha256': 'a' * 64, 'size': 1},
                                                  'two': {'sha256': 'a' * 64, 'size': 2}}
            with self.subTest(fault=fault), self.assertRaises(Invalid):
                controller_module().forecast({'worlds': rows}, attempts, pending, **args)


class NativeControllerMonitorIndependentTests(unittest.TestCase):
    def test_actual_final_monitor_rechecks_larger_complete_cost_before_sixty_four_worlds(self):
        # Public run_final's actual closure and pure forecast/admission logic.
        # Admission/copy/private executor and artifact transport are explicit
        # metadata seams; this proves no Registry, corpus or scientific admission.
        m = controller_module()
        with tempfile.TemporaryDirectory(prefix='trf-controller-monitor-') as temporary:
            root = Path(temporary); directory = root / 'controller'; directory.mkdir()
            receipt = root / 'prepared.json'; receipt.write_text('{}')
            rows = worlds(2048)
            for i, row in enumerate(rows):
                row.update(spec_index=(i // 256) // 4, pattern_index=(i // 256) % 4, replicate=i % 256)
            first = observed(rows[0], 1, storage=37 * MIB,
                outputs={'stream': {'sha256': 'a' * 64, 'size': 15 * MIB}})
            later = observed(rows[1], 2, storage=200 * MIB,
                outputs={'stream': {'sha256': 'b' * 64, 'size': 20 * MIB}})
            bodies = {'c' * 64: {'body': first}, 'd' * 64: {'body': later}}
            h1 = types.SimpleNamespace(records={('final', rows[0]['id']): {'state': 'COMPLETE', 'artifact_id': 'c' * 64}},
                attempts={('final', rows[0]['id']): [first['attempt_id']]}, pending={}, grants=[],
                storage=5 * GIB, checkpoint='1' * 64)
            h2 = types.SimpleNamespace(records={**h1.records, ('final', rows[1]['id']): {'state': 'COMPLETE', 'artifact_id': 'd' * 64}},
                attempts={**h1.attempts, ('final', rows[1]['id']): [later['attempt_id']]}, pending={}, grants=[],
                storage=5 * GIB + 200 * MIB, checkpoint='2' * 64)
            current = [h1]; reasons = []; reports = []
            ctl = m.NativeCalibrationController.__new__(m.NativeCalibrationController)
            ctl.directory = directory; ctl.cancel = threading.Event()
            ctl.broker = types.SimpleNamespace(directory=root, _artifact=lambda identity: bodies[identity])
            ctl.resources = types.SimpleNamespace(stop=lambda token, pool_id, reason: reasons.append(reason),
                _history=lambda pool: current[0])
            ctl.copies = types.SimpleNamespace(receipt_path=lambda *args: receipt,
                require=lambda *args: {'event_prefix': {'seq': 1, 'hash': 'a' * 64}, 'wall_elapsed_ms': 0})
            manifest = {'worlds': rows}; study = {'id': 'b' * 64, 'body': {'manifest': manifest}}
            (directory / 'final-start.json').write_text(canonical({
                'at_utc': '2026-11-03T03:32:10+00:00', 'study_id': study['id'],
                'acceptance_hash': digest({}), 'prepared_prefix': {'seq': 1, 'hash': 'a' * 64},
                'scientific_readiness': False}), encoding='utf-8')
            fallback = {f'{spec}/{pattern}': {'compute_ms': 1000, 'storage_bytes': 37 * MIB, 'retained_bytes': 16 * MIB}
                for spec in range(2) for pattern in range(4)}
            def actual_forecast(token, pool_id, item, acceptance, **unused):
                samples = [bodies[row['artifact_id']]['body'] for row in current[0].records.values()]
                result = m.forecast(manifest, samples, [], fallback=fallback, elapsed_ms=1000,
                    final_elapsed_ms=1000, deadline_ms=2000, charged_storage_bytes=current[0].storage,
                    copy_overhead_ms=0, primary_bytes=0, prepared_copies=0, terminal_copies=2)
                result.update(free_bytes=999 * GIB, free_C_bytes=999 * GIB)
                reports.append(result); return result
            class ProbeFinished(Exception): pass
            def actual_callbacks(token, pool_id, phase, task_ids, *, workers, on_checkpoint):
                current[0] = h1; on_checkpoint(h1, 1)
                current[0] = h2; on_checkpoint(h2, 2)
                raise ProbeFinished('Both pre64callbacks returned without required A3 stop')
            stopped = False
            with patch.object(m.NativeFamilyCalibrationStudies, '_study_before_execute', return_value=None), \
                    patch.object(ctl, '_forecast', side_effect=actual_forecast), \
                    patch.object(ctl, '_run', side_effect=actual_callbacks), \
                    patch.object(m.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=999 * GIB)):
                try: ctl.run_final('operator-fixture', 'a' * 64, study, {})
                except Invalid as exc:
                    self.assertIn('NATIVE_A3_LOGICAL_FORECAST', str(exc)); stopped = True
                except ProbeFinished: pass
            self.assertTrue(stopped, 'A larger actual completed cost remained hidden behind the pre64 forecast cache')
            # A fresh pre-start guard may also forecast. The invariant is that
            # the larger completed cost is actually evaluated and stops use.
            self.assertGreaterEqual(len(reports), 2)
            self.assertLessEqual(reports[0]['logical_forecast_bytes'], 100 * GIB)
            self.assertGreater(reports[-1]['logical_forecast_bytes'], 100 * GIB)
            self.assertEqual(reasons, ['NATIVE_A3_LOGICAL_FORECAST'])
            self.assertTrue(ctl.cancel.is_set())


class NativeControllerSchedulerIndependentTests(unittest.TestCase):
    """Real finite ledger/scheduler, explicitly synthetic calculator results.

    Small acceptance metadata inventories and a typed private final1024 input
    exercise scheduling only. They do not substitute for the actual native
    caller's source/input/classifier/provenance checks or D100full2048 admission.
    """
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='trf-controller-financial-base-')
        cls.addClassCleanup(temporary.cleanup); root = Path(temporary.name)
        f = financial_support.RetiredFinancialFixture(root)
        try:
            cls.authority = deepcopy(f.authority); cls.retired_storage = f.state['storage']
            cls.study = deepcopy(f.study); cls.recovery_source = deepcopy(f.recovery_source)
            cls.backup = root / 'financial-only-backup'
            assert f.broker.call(f.token, 'backup_bundle', destination=str(cls.backup))['status'] == 'PASS'
            cls.operator_key = root / 'operator.key'
            cls.operator_key.write_bytes((f.broker.directory / 'operator.key').read_bytes())
        finally:
            f.broker.close()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-controller-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name)
        authority = patch.object(native_calibration_runs.NativeCalibrationResources, '_read_authority',
            side_effect=lambda: deepcopy(self.authority))
        authority.start(); self.addCleanup(authority.stop)
        self.directory = self.root / 'registry'
        self.assertEqual(restore_bundle(self.backup, self.directory, self.operator_key)['status'], 'PASS')
        self.broker = financial_support.Broker(self.directory); self.token = self.broker.admin_token
        self.addCleanup(lambda: self.broker.close())
        self.driver = self.root / 'trusted-driver.py'; self.driver.write_bytes(DRIVER)
        self.run_directory = self.root / 'controller'
        self.ctl = controller_module().NativeCalibrationController(self.broker, self.run_directory, driver_file=self.driver)
        self.pool = self.ctl.prepare(self.token, 'scheduler-only-fixture')
        self.financial = financial_support.RetiredFinancialFixture.__new__(financial_support.RetiredFinancialFixture)
        self.financial.root = self.root; self.financial.broker = self.broker; self.financial.token = self.token
        self.plans = {}; self.calls = []; self.call_lock = threading.Lock()
        self.compute = 5; self.storage = MIB; self.before_settlement = None
        executor = patch.object(self.ctl.caller, 'execute', side_effect=self.synthetic_execute)
        self.executor_mock = executor.start(); self.addCleanup(executor.stop)
        numerical = patch.object(study_runs, 'execute_attempt', side_effect=AssertionError('Scheduler used numerical transport'))
        numerical.start(); self.addCleanup(numerical.stop)
        cache = patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Scheduler used native cache'))
        cache.start(); self.addCleanup(cache.stop)

    def view(self): return self.ctl.resources.inspect(self.token, self.pool['id'])

    def journal(self):
        return [decode(line) for line in (self.run_directory / 'observations.jsonl').read_bytes().splitlines()]

    def rewrite_journal(self, records):
        (self.run_directory / 'observations.jsonl').write_bytes(b''.join((canonical(record) + '\n').encode() for record in records))

    def bind(self, phase='acceptance', count=8, *, attempt_compute_ms=35000):
        input_id = None
        if phase == 'final':
            typed = self.financial.save({'schema': 'native-family-calibration-input/1', 'created_at': 1,
                'request': {'development_study_id': self.recovery_source['id'],
                            'native_qualification_id': self.recovery_source['id']},
                'manifest': self.study['body']['manifest'], 'payload': self.study['body']['payload'],
                'scientific_readiness': False}, refs=[self.recovery_source['id']],
                authority='conditional_native_joint_family_calibration_not_scientific_admission')
            input_id = typed['id']; all_tasks = sorted(w['id'] for w in typed['body']['manifest']['worlds'])
        else:
            all_tasks = sorted(digest({'scheduler_metadata_task': i}) for i in range(count))
        self.inventory = self.ctl.resources.bind_inventory(self.token, {'pool_id': self.pool['id'],
            'key': 'scheduler-fixture-' + phase, 'phase': phase, 'task_ids': all_tasks,
            'execution_deadline_ms': attempt_compute_ms - 30000, 'attempt_compute_ms': attempt_compute_ms,
            'attempt_storage_bytes': 256 * MIB, 'max_attempts': 2 if phase == 'final' else 1,
            'expected_checkpoint': self.view()['resource_checkpoint']}, input_id=input_id)
        return all_tasks[:count]

    def synthetic_execute(self, token, pool_id, attempt_id, *, _cancel=None):
        self.assertIs(_cancel, self.ctl.cancel)
        with self.broker._mutex:
            history = self.ctl.resources._history(self.pool); reservation = deepcopy(history.pending[attempt_id])
            count = len(history.attempts[(reservation['phase'], reservation['task_id'])])
        with self.call_lock: self.calls.append((reservation['task_id'], attempt_id, count))
        if self.before_settlement is not None: self.before_settlement(reservation, count, _cancel)
        plan = self.plans.get(reservation['task_id'], ['COMPLETE'])
        state = plan[min(count - 1, len(plan) - 1)]
        if _cancel.is_set() and state == 'COMPLETE': state = 'FAILED'
        if state == 'RAISE': raise RuntimeError('Explicit scheduler executor failed without settlement')
        known = state != 'UNKNOWN'
        if state == 'UNKNOWN': state = 'FAILED'
        failure = (None if state == 'COMPLETE' else {'type': 'ChildDeadlineExceeded' if state == 'KNOWN_TIMEOUT'
            else 'SyntheticSchedulerFailure', 'message': 'Synthetic metadata result, not native classification.'})
        body = {'resource_pool_id': pool_id, 'phase': reservation['phase'], 'task_id': reservation['task_id'],
            'attempt_id': attempt_id, 'resource_state': state, 'currency_checked': True,
            'failure': failure, 'failures': [] if failure is None else [failure], 'output_blobs': {},
            'settlement': {'attempt_id': attempt_id, 'compute_ms': self.compute,
                           'storage_bytes': self.storage, 'usage_known': known}}
        if reservation['phase'] == 'final':
            body.update(study_id=self.inventory['body']['input_id'], world_id=reservation['task_id'])
        return self.ctl.resources.settle(token, pool_id, body)

    def async_run(self, phase, tasks, *, workers, on_checkpoint=None):
        box = {}; done = threading.Event()
        def run():
            try: box['report'] = self.ctl._run(self.token, self.pool['id'], phase, tasks,
                workers=workers, on_checkpoint=on_checkpoint)
            except BaseException as exc: box['exception'] = exc
            finally: done.set()
        thread = threading.Thread(target=run); thread.start()
        return thread, done, box

    def assert_done(self, thread, done, box):
        self.assertTrue(done.wait(10), 'Bounded scheduler fixture did not drain')
        thread.join(1); self.assertFalse(thread.is_alive())
        if 'exception' in box: raise box['exception']
        return box['report']

    def test_prepare_is_source_bound_idempotent_and_prepays_external_metadata_exactly_once(self):
        binding = self.ctl.validate(self.token, self.pool['id'])
        self.assertEqual(binding['schema'], 'native-calibration-controller-binding/1')
        self.assertEqual(binding['registry_path'], str(self.directory))
        self.assertEqual(binding['run_directory'], str(self.run_directory))
        self.assertEqual(binding['driver_path'], str(self.driver))
        self.assertEqual(binding['driver_sha256'], hashlib.sha256(DRIVER).hexdigest())
        self.assertEqual(binding['policy']['metadata_bytes_prepaid'], 16 * MIB)
        self.assertEqual(binding['policy']['max_workers'], 6); self.assertIs(binding['scientific_readiness'], False)
        source = self.broker._artifact(binding['source_result_id'])
        self.assertEqual(source['body']['settlement']['storage_bytes'], 2 * len(DRIVER) + 17 * MIB)
        self.assertEqual(self.view()['budget']['charged_storage_bytes'], self.retired_storage + 18 * MIB + 2 * len(DRIVER))
        before = self.view(); self.assertEqual(self.ctl.prepare(self.token, 'another-alias-key'), self.pool)
        self.assertEqual(self.view(), before)
        self.assertEqual(self.broker._read_blob_bytes(source['body']['output_blobs']['driver']['sha256']), DRIVER)

    def test_driver_corruption_missing_or_relocation_and_worker_authority_cannot_rebind(self):
        original = self.driver.read_bytes()
        self.driver.write_bytes(original + b'# changed\n')
        with self.assertRaises(ERRORS): self.ctl.validate(self.token, self.pool['id'])
        self.driver.write_bytes(original); self.assertEqual(self.ctl.validate(self.token, self.pool['id']), self.ctl.binding)
        moved = self.root / 'relocated-driver.py'; self.driver.rename(moved)
        with self.assertRaises(ERRORS): self.ctl.validate(self.token, self.pool['id'])
        other = controller_module().NativeCalibrationController(self.broker, self.run_directory, driver_file=moved)
        with self.assertRaises(ERRORS): other.prepare(self.token, 'cannot-retarget-driver')
        moved.rename(self.driver)
        worker = self.broker.call(self.token, 'register_worker', name='controller-no-authority', role='discovery', capabilities=[])['token']
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Unauthorized private lookup')):
            with self.assertRaises(Denied): self.ctl.validate(worker, self.pool['id'])
            with self.assertRaises(Denied): self.ctl.prepare(worker, 'no-worker-setup')
        self.assertEqual(self.calls, [])

    def test_six_real_pending_slots_finish_out_of_order_without_a_seventh_inflight_task(self):
        tasks = self.bind(count=8); entered = threading.Event(); release = threading.Event()
        release_first = threading.Event(); lock = threading.Lock()
        active = 0; maximum = 0; seen_pending = []
        def wait_first_six(reservation, count, cancel):
            nonlocal active, maximum
            with lock:
                active += 1; maximum = max(maximum, active)
                seen_pending.append(len(self.view()['budget']['outstanding_attempts']))
                if active == 6: entered.set()
            self.assertTrue(release.wait(5))
            # The first dispatched task cannot finish until another genuine
            # result has already been appended and acknowledged by scheduler.
            if reservation['task_id'] == tasks[0]: self.assertTrue(release_first.wait(5))
            with lock: active -= 1
        def checkpoint(history, terminal):
            if any(item['kind'] == 'execute' and item['state'] == 'ACK' for item in self.journal()):
                release_first.set()
        self.before_settlement = wait_first_six
        thread, done, box = self.async_run('acceptance', tasks, workers=6, on_checkpoint=checkpoint)
        try:
            self.assertTrue(entered.wait(5)); self.assertEqual(len(self.calls), 6)
            self.assertEqual(len(self.view()['budget']['outstanding_attempts']), 6)
        finally: release.set()
        report = self.assert_done(thread, done, box)
        self.assertEqual(report['status'], 'COMPLETE'); self.assertEqual(set(report['terminal_tasks']), set(tasks))
        self.assertEqual(len(report['attempts']), 8); self.assertEqual(maximum, 6)
        self.assertLessEqual(max(seen_pending), 6); self.assertEqual(self.view()['budget']['outstanding_attempts'], [])
        completed = [self.broker._artifact(identity)['body']['task_id'] for identity in report['attempts']]
        self.assertNotEqual(completed, [task for task, _, _ in self.calls])

    def test_final_known_clock_retries_once_and_live_retry_is_not_yet_terminal(self):
        tasks = self.bind('final', count=3)
        self.plans = {tasks[0]: ['KNOWN_TIMEOUT', 'COMPLETE'], tasks[1]: ['KNOWN_TIMEOUT', 'KNOWN_TIMEOUT']}
        retry_live = threading.Event(); seen_checkpoint = threading.Event(); release = threading.Event(); counts = []
        def pause_retry(reservation, count, cancel):
            if reservation['task_id'] == tasks[0] and count == 2:
                retry_live.set(); self.assertTrue(release.wait(5))
        def checkpoint(history, terminal):
            if any(r['task_id'] == tasks[0] for r in history.pending.values()) and len(history.attempts.get(('final', tasks[0]), [])) == 2:
                counts.append(terminal); seen_checkpoint.set()
        self.before_settlement = pause_retry
        thread, done, box = self.async_run('final', tasks, workers=1, on_checkpoint=checkpoint)
        try:
            self.assertTrue(retry_live.wait(5)); self.assertTrue(seen_checkpoint.wait(4))
            self.assertTrue(counts); self.assertEqual(set(counts), {0})
        finally: release.set()
        report = self.assert_done(thread, done, box)
        self.assertEqual(report['status'], 'INCOMPLETE_UNAVAILABLE'); self.assertEqual(report['unavailable_tasks'], [tasks[1]])
        self.assertEqual([task for task, _, _ in self.calls], [tasks[0], tasks[0], tasks[1], tasks[1], tasks[2]])
        self.assertEqual(len(report['attempts']), 5); self.assertFalse(self.ctl.cancel.is_set())
        self.assertIs(self.view()['budget']['halted'], False)

    def test_full_envelope_stop_drains_pending_before_exact_paired_grant(self):
        tasks = self.bind(count=2, attempt_compute_ms=2000000); self.compute = 1300000
        entered = threading.Event(); release = threading.Event(); grants = []
        actual = self.ctl.resources.continue_pool
        def pause(reservation, count, cancel):
            if reservation['task_id'] == tasks[0]: entered.set(); self.assertTrue(release.wait(5))
        def grant(token, request):
            self.assertEqual(self.view()['budget']['outstanding_attempts'], [])
            self.assertEqual(self.journal()[-1]['kind'], 'grant'); self.assertEqual(self.journal()[-1]['state'], 'INTENT')
            grants.append(deepcopy(request)); return actual(token, request)
        self.before_settlement = pause; before = self.view()['budget']
        with patch.object(self.ctl.resources, 'continue_pool', side_effect=grant):
            thread, done, box = self.async_run('acceptance', tasks, workers=6)
            try:
                self.assertTrue(entered.wait(5)); self.assertEqual(grants, [])
                self.assertEqual(len(self.view()['budget']['outstanding_attempts']), 1)
            finally: release.set()
            report = self.assert_done(thread, done, box)
        self.assertEqual(report['status'], 'COMPLETE'); self.assertEqual(len(grants), 1)
        self.assertEqual(grants[0]['additional_compute_ms'], 3600000)
        self.assertEqual(grants[0]['additional_storage_bytes'], 4 * GIB)
        self.assertEqual(self.view()['budget']['grants_used'], before['grants_used'] + 1)
        self.assertEqual(self.view()['budget']['charged_storage_bytes'], before['charged_storage_bytes'] + 3 * MIB)

    def test_unknown_usage_stops_new_dispatch_drains_and_keeps_full_conservative_charge(self):
        tasks = self.bind(count=7); first_six = threading.Barrier(6)
        self.plans[tasks[0]] = ['UNKNOWN']; before = self.view()['budget']
        def drain(reservation, count, cancel):
            first_six.wait(timeout=5)
            if reservation['task_id'] != tasks[0]: self.assertTrue(cancel.wait(5))
        self.before_settlement = drain
        report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=6)
        self.assertEqual(report['status'], 'STOPPED'); self.assertEqual(len(self.calls), 6)
        self.assertTrue(self.ctl.cancel.is_set()); self.assertEqual(self.view()['budget']['outstanding_attempts'], [])
        self.assertIs(self.view()['budget']['halted'], True)
        self.assertIs(self.view()['budget']['usage_uncertain'], True)
        self.assertEqual(self.view()['budget']['charged_compute_ms'], before['charged_compute_ms'] + 35000 + 5 * self.compute)
        self.assertEqual(self.view()['budget']['charged_storage_bytes'], before['charged_storage_bytes'] + 256 * MIB + 5 * MIB)

    def test_pool_revocation_during_six_active_slots_stops_dispatch_and_retains_late_failures(self):
        tasks = self.bind(count=7); first_six = threading.Barrier(6)
        def revoke_and_drain(reservation, ordinal, cancel):
            first_six.wait(timeout=5)
            if reservation['task_id'] == tasks[0]:
                evidence = self.broker.call(self.token, 'add_source', data_class='development', body={'scheduler_defect': True})
                self.broker.call(self.token, 'revoke_dependency', key='active-controller-pool-defect',
                    dependency_id=self.pool['id'], reason='Synthetic active pool withdrawal.', evidence_refs=[evidence['id']])
            else: self.assertTrue(cancel.wait(5))
        self.before_settlement = revoke_and_drain
        report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=6)
        self.assertEqual(report['status'], 'STOPPED'); self.assertEqual(len(self.calls), 6)
        self.assertTrue(self.ctl.cancel.is_set()); self.assertEqual(self.view()['budget']['outstanding_attempts'], [])
        self.assertEqual(len(report['attempts']), 6)
        for identity in report['attempts']:
            body = self.broker._artifact(identity)['body']
            self.assertEqual(body['resource_state'], 'FAILED'); self.assertIs(body['currency_checked'], False)
            self.assertTrue(any(failure['type'] == 'Denied' for failure in body['failures']))

    def test_callback_error_cancels_active_workers_before_joining_and_retains_their_settlements(self):
        tasks = self.bind(count=7); active = threading.Event(); lock = threading.Lock(); count = 0
        def wait_cancel(reservation, ordinal, cancel):
            nonlocal count
            with lock:
                count += 1
                if count == 6: active.set()
            self.assertTrue(cancel.wait(5))
        def checkpoint(history, terminal):
            if history.pending and active.is_set(): raise RuntimeError('Explicit checkpoint failure with six live metadata workers')
        self.before_settlement = wait_cancel
        report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=6, on_checkpoint=checkpoint)
        self.assertEqual(report['status'], 'STOPPED'); self.assertEqual(len(self.calls), 6)
        self.assertTrue(self.ctl.cancel.is_set()); self.assertEqual(len(report['attempts']), 6)
        self.assertEqual(self.view()['budget']['outstanding_attempts'], [])

    def test_primary_callback_failure_survives_failed_durable_stop_and_still_cancels_before_join(self):
        tasks = self.bind(count=7); active = threading.Event(); lock = threading.Lock(); count = 0
        def wait_cancel(reservation, ordinal, cancel):
            nonlocal count
            with lock:
                count += 1
                if count == 6: active.set()
            self.assertTrue(cancel.wait(5))
        def checkpoint(history, terminal):
            if history.pending and active.is_set(): raise ValueError('Original independent callback failure')
        self.before_settlement = wait_cancel
        with patch.object(self.ctl.resources, 'stop', side_effect=OSError('Synthetic durable stop write failure')):
            report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=6, on_checkpoint=checkpoint)
        self.assertEqual(report['status'], 'STOPPED')
        self.assertEqual(report['failure']['type'], 'ValueError')
        self.assertEqual(report['failure']['message'], 'Original independent callback failure')
        self.assertTrue(report['failure']['notes'])
        self.assertTrue(all(type(note) is str and len(note) <= 2000 for note in report['failure']['notes']))
        self.assertTrue(report['stop_failures']); self.assertTrue(self.ctl.cancel.is_set())
        self.assertEqual(len(self.calls), 6); self.assertEqual(self.view()['budget']['outstanding_attempts'], [])

    def test_guard_after_full_reservation_stops_before_child_and_settles_known_control_only_cost(self):
        tasks = self.bind(count=2); before = self.view()['budget']
        def checkpoint(history, terminal):
            if history.pending:
                self.ctl._stop(self.token, self.pool['id'], 'Explicit post-reservation A3 guard stop')
                raise Invalid('Explicit full-pending-envelope guard denial before any child')
        report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=6, on_checkpoint=checkpoint)
        self.assertEqual(report['status'], 'STOPPED'); self.assertEqual(self.calls, [])
        budget = self.view()['budget']; self.assertEqual(budget['outstanding_attempts'], [])
        self.assertIs(budget['usage_uncertain'], False); self.assertIs(budget['halted'], True)
        history = self.ctl.resources._history(self.pool)
        record = history.records[('acceptance', tasks[0])]; body = self.broker._artifact(record['artifact_id'])['body']
        self.assertEqual(body['resource_state'], 'FAILED'); self.assertIs(body['settlement']['usage_known'], True)
        self.assertEqual(body['settlement']['storage_bytes'], MIB)
        self.assertLess(body['settlement']['compute_ms'], 35000)
        self.assertEqual(budget['charged_compute_ms'], before['charged_compute_ms'] + body['settlement']['compute_ms'])
        self.assertEqual(budget['charged_storage_bytes'], before['charged_storage_bytes'] + MIB)

    def test_unsettled_executor_error_becomes_conservative_orphan_and_never_redispatches(self):
        tasks = self.bind(count=2); self.plans[tasks[0]] = ['RAISE']; before = self.view()['budget']
        report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=1)
        self.assertEqual(report['status'], 'STOPPED'); self.assertEqual(len(self.calls), 1)
        budget = self.view()['budget']; self.assertIs(budget['usage_uncertain'], True)
        self.assertEqual(budget['charged_compute_ms'], before['charged_compute_ms'] + 35000)
        self.assertEqual(budget['charged_storage_bytes'], before['charged_storage_bytes'] + 256 * MIB)
        self.assertEqual(budget['outstanding_attempts'], [])
        with self.assertRaises(ERRORS): self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=1)
        self.assertEqual(len(self.calls), 1)

    def test_intents_precede_actual_mutations_and_missing_ack_reconciles_without_heavy_repeat(self):
        tasks = self.bind(count=1); actual_reserve = self.ctl.resources.reserve
        def reserve(token, request):
            last = self.journal()[-1]; self.assertEqual((last['kind'], last['state']), ('reserve', 'INTENT'))
            self.assertEqual(last['request_hash'], digest(request)); return actual_reserve(token, request)
        def before(reservation, ordinal, cancel):
            last = self.journal()[-1]; self.assertEqual((last['kind'], last['state']), ('execute', 'INTENT'))
            self.assertEqual(last['request_hash'], digest({'attempt_id': reservation['attempt_id']}))
        self.before_settlement = before
        with patch.object(self.ctl.resources, 'reserve', side_effect=reserve):
            report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=1)
        self.assertEqual(report['status'], 'COMPLETE')
        records = self.journal(); self.assertEqual((records[-1]['kind'], records[-1]['state']), ('execute', 'ACK'))
        self.assertIs(type(records[-1]['whole_call_ms']), int); self.assertGreaterEqual(records[-1]['whole_call_ms'], 0)
        self.rewrite_journal(records[:-1]); before_view = self.view(); prior_calls = len(self.calls)
        with patch.object(self.ctl.caller, 'execute', side_effect=AssertionError('Reconciliation repeated heavy work')):
            self.ctl.validate(self.token, self.pool['id'])
        repaired = self.journal()[-1]
        self.assertEqual(repaired['state'], 'ACK'); self.assertEqual(repaired['result_id'], report['attempts'][0])
        self.assertIsNone(repaired['whole_call_ms']); self.assertEqual(self.view(), before_view)
        self.assertEqual(len(self.calls), prior_calls)

    def test_unresolved_intent_and_forged_ack_or_request_digest_never_create_authority(self):
        tasks = self.bind(count=1)
        report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=1)
        self.assertEqual(report['status'], 'COMPLETE'); original = self.journal()
        for fault in ('ack_result', 'paired_request_hash', 'unresolved'):
            records = deepcopy(original)
            if fault == 'ack_result': records[-1]['result_id'] = self.recovery_source['id']
            elif fault == 'paired_request_hash':
                for record in records:
                    if record['kind'] == 'execute': record['request_hash'] = 'e' * 64
            else:
                record = deepcopy(records[-2]); record.update(operation='f' * 32, attempt_id='f' * 32,
                    result_id=None, state='INTENT', request_hash=digest({'attempt_id': 'f' * 32}), whole_call_ms=None)
                records.append(record)
            self.rewrite_journal(records)
            with self.subTest(fault=fault), self.assertRaises(ERRORS): self.ctl.validate(self.token, self.pool['id'])
        self.assertEqual(len(self.calls), 1)

    def test_observed_prefix_prevents_stale_primary_rollback_from_reauthorizing_work(self):
        tasks = self.bind(count=1); early = self.root / 'earlier-owned-primary.sqlite3'
        with closing(sqlite3.connect(early)) as target: self.broker._db.backup(target)
        self.assertEqual(self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=1)['status'], 'COMPLETE')
        self.broker.close()
        # Controlled rollback of the owned test primary only, retaining all
        # external observations/blobs; no actual Registry path is touched.
        with closing(sqlite3.connect(early.as_uri() + '?mode=ro', uri=True)) as source:
            with closing(sqlite3.connect(self.directory / 'registry.sqlite3')) as target: source.backup(target)
        self.broker = financial_support.Broker(self.directory); self.token = self.broker.admin_token
        restored = controller_module().NativeCalibrationController(self.broker, self.run_directory, driver_file=self.driver)
        with patch.object(restored.caller, 'execute', side_effect=AssertionError('Stale restore dispatched work')):
            with self.assertRaises(ERRORS): restored.prepare(self.token, 'scheduler-only-fixture')
        self.assertEqual(len(self.calls), 1)

    def test_stop_sentinel_unsupported_parallelism_and_prepaid_metadata_exhaustion_never_dispatch(self):
        tasks = self.bind(count=2)
        for workers in (True, 2, 7):
            with self.subTest(workers=workers), self.assertRaises(Invalid):
                self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=workers)
        (self.run_directory / 'stop.request').write_text('Explicit owned test operator stop.\n')
        report = self.ctl._run(self.token, self.pool['id'], 'acceptance', tasks, workers=1)
        self.assertEqual(report['status'], 'STOPPED'); self.assertEqual(self.calls, [])
        (self.run_directory / 'oversized-metadata.bin').write_bytes(b'x' * (16 * MIB))
        before = self.view()
        with self.assertRaises(Invalid): self.ctl.validate(self.token, self.pool['id'])
        self.assertEqual(self.view(), before)


if __name__ == '__main__':
    unittest.main()
