"""Independent reserved-native caller controls; no actual series execution.

Disposable Registry reservations/accounting/custody run through their owners.
Qualification, native binary membership and numerical responses are explicitly
synthetic seams. No empirical result or scientific admission is asserted.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import test_native_calibration_inputs_independent as input_support
import test_native_calibration_resource_owner_independent as financial_support
import test_native_study_independent as native_support
import test_native_runtime_independent as runtime_support
from trading_researcher import native_calibration_runs, native_study_pipeline as pipeline, study_runs, study_process_control as process
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.evaluation_plans import footprint, source_bundle
from trading_researcher import family_study
from trading_researcher.native_qualification import NativeQualifications
from trading_researcher import native_qualification as qualification_owner
from trading_researcher.native_runtime import NativeRuntimes
from trading_researcher.native_study_runs import NativeFamilyCalibrationStudies
from trading_researcher.storage import restore_bundle
from trading_researcher.study_stream import EncodedStream


MIB = 1048576
ERRORS = (Invalid, Conflict, Denied)
POLICY = {'schema': 'native-study-process-control/1', 'library_threads': 1, 'priority': 'BELOW_NORMAL'}
CONTROL_OBSERVATION = {'policy': POLICY, 'priority_class': 0x4000,
    'thread_environment': {name: '1' for name in ('OMP_NUM_THREADS', 'OMP_THREAD_LIMIT',
        'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
        'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS')}}


class NativeReservedAttemptEntrypointIndependentTests(unittest.TestCase):
    def test_host_only_reserved_attempt_owner_exists_before_domain_cases(self):
        self.assertTrue(callable(getattr(native_calibration_runs, 'NativeCalibrationAttempts', None)),
                        'Reserved native attempt owner absent; zero domain-flow coverage')

    def test_missing_numerical_caller_cannot_authorize_retry_when_previous_generation_is_absent(self):
        # Focused private-method counterexample only: no Broker/ledger or
        # dispatch proof is fabricated by a metadata-only KNOWN_TIMEOUT label.
        caller = native_calibration_runs.NativeCalibrationAttempts.__new__(
            native_calibration_runs.NativeCalibrationAttempts)
        prior = {'body': {'schema': 'native-family-calibration-attempt/1', 'result': None,
                         'resource_state': 'KNOWN_TIMEOUT', 'currency_checked': True,
                         'failure': {'type': 'ChildDeadlineExceeded', 'message': 'Synthetic metadata-only clock'},
                         'settlement': {'usage_known': True}}}
        with self.assertRaises((Invalid, Conflict, Denied)):
            caller._retry_equal(prior, None, [], [], {})


class NativeReservedEarlyHaltIndependentTests(unittest.TestCase):
    def test_halted_pool_cannot_start_pending_final_b_before_any_input_or_cache_work(self):
        # Early negative gate ONLY: this host-private typed final metadata has
        # no input/qualification validity claim. The guard precedes those owners.
        with tempfile.TemporaryDirectory(prefix='trf-native-halted-reservation-') as temporary:
            f = financial_support.RetiredFinancialFixture(Path(temporary))
            try:
                with patch.object(native_calibration_runs.NativeCalibrationResources,
                                  '_read_authority', return_value=deepcopy(f.authority)):
                    manager = native_calibration_runs.NativeCalibrationResources(f.broker)
                    pool = manager.prepare(f.token, {'key': 'early-halt-negative-only'})
                    typed = f.save({'schema': 'native-family-calibration-input/1', 'created_at': 1,
                        'request': {'development_study_id': f.recovery_source['id'],
                                    'native_qualification_id': f.recovery_source['id']},
                        'manifest': f.study['body']['manifest'], 'payload': f.study['body']['payload'],
                        'source_footprint': footprint(source_bundle()), 'scientific_readiness': False,
                        'native_binding': {'fixture': 'typed metadata only; never qualified'}},
                        refs=[f.recovery_source['id']],
                        authority='conditional_native_joint_family_calibration_not_scientific_admission')
                    tasks = sorted(world['id'] for world in typed['body']['manifest']['worlds'])
                    manager.bind_inventory(f.token, {'pool_id': pool['id'], 'key': 'early-halt-final',
                        'phase': 'final', 'task_ids': tasks, 'execution_deadline_ms': 10000,
                        'attempt_compute_ms': 15000, 'attempt_storage_bytes': 256 * 1048576,
                        'max_attempts': 2, 'expected_checkpoint': manager.inspect(f.token, pool['id'])['resource_checkpoint']},
                        input_id=typed['id'])
                    for index in range(2):
                        manager.reserve(f.token, {'pool_id': pool['id'], 'phase': 'final', 'task_id': tasks[index],
                            'attempt_id': format(index + 1, '032x'),
                            'expected_checkpoint': manager.inspect(f.token, pool['id'])['resource_checkpoint']})
                    manager.stop(f.token, pool['id'], 'Independent stop before B dispatch')
                    before = manager.inspect(f.token, pool['id'])
                    caller = native_calibration_runs.NativeCalibrationAttempts(f.broker)
                    with patch.object(NativeFamilyCalibrationStudies, '_study_before_execute',
                                      side_effect=AssertionError('Halted task entered input validation')) as inputs, \
                            patch.object(NativeRuntimes, '_materialize',
                                      side_effect=AssertionError('Halted task entered native cache')) as cache:
                        rejected = False
                        try:
                            caller.execute(f.token, pool['id'], format(2, '032x'), _cancel=None)
                        except (Invalid, Denied):
                            rejected = True
                        self.assertEqual(inputs.call_count, 0)
                        self.assertEqual(cache.call_count, 0)
                        self.assertTrue(rejected)
                    self.assertEqual(manager.inspect(f.token, pool['id']), before)
            finally:
                f.broker.close()


class NativeReservedAttemptsIndependentTests(unittest.TestCase):
    """Genuine prepared input and resource Registry, simulated numeric children.

    Source/rights/certification/compile owners are the existing genuine synthetic
    fixture. Its trusted native qualification and binary membership remain seams.
    No numerical resampling or real2048-series admission is claimed by target3.
    """
    @classmethod
    def setUpClass(cls):
        input_support.NativeCalibrationInputsIndependentTests.setUpClass()
        cls.addClassCleanup(input_support.NativeCalibrationInputsIndependentTests.doClassCleanups)
        temporary = tempfile.TemporaryDirectory(prefix='trf-reserved-native-base-')
        cls.addClassCleanup(temporary.cleanup)
        cls.base_root = Path(temporary.name)
        builder = input_support.NativeCalibrationInputsIndependentTests('runTest')
        builder.setUp()
        try:
            s = builder.s
            members = {'example/LICENSE.txt': b'Invented membership notice.\n',
                       pipeline.KERNEL_FILE: b'Invented kernel membership bytes; never loaded.\n'}
            s.raw = runtime_support.archive(members.items())
            s.runtime_manifest = runtime_support.manifest(members)
            archive_path = builder.root / 'reserved-fixture-runtime.zip'; archive_path.write_bytes(s.raw)
            s.archive_source = s.op('add_blob_source', path=str(archive_path), data_class='operations',
                                   description='Explicit synthetic native membership seam, no binary executed.')
            s.runtime = s.op('retain_native_runtime', key='reserved-native-fixture-runtime',
                            archive_id=s.archive_source['id'], manifest=s.runtime_manifest)
            s.qualified = s.qualification(key='reserved-native-trusted-qualification')
            # Composition injects ONLY the old helper's Broker factory, letting
            # its unchanged financial builder append onto this genuine Broker.
            with patch.object(financial_support, 'Broker', return_value=s.broker):
                financial = financial_support.RetiredFinancialFixture(builder.root)
            cls.authority = deepcopy(financial.authority)
            cls.retired_storage = financial.state['storage']
            with patch.object(native_calibration_runs.NativeCalibrationResources, '_read_authority',
                              return_value=deepcopy(cls.authority)):
                manager = native_calibration_runs.NativeCalibrationResources(s.broker)
                cls.pool = manager.prepare(s.token, {'key': 'reserved-native-test-pool'})
                cls.final = builder.prepare(key='reserved-native-test-input', seed=991)
                cls.tasks = sorted(world['id'] for world in cls.final['body']['manifest']['worlds'])
                assert len(cls.tasks) == 1024
                cls.inventory = manager.bind_inventory(s.token, {'pool_id': cls.pool['id'],
                    'key': 'reserved-native-test-final-inventory', 'phase': 'final', 'task_ids': cls.tasks,
                    'execution_deadline_ms': 10000, 'attempt_compute_ms': 15000,
                    'attempt_storage_bytes': 256 * MIB, 'max_attempts': 2,
                    'expected_checkpoint': manager.inspect(s.token, cls.pool['id'])['resource_checkpoint']},
                    input_id=cls.final['id'])
            cls.facts = {name: deepcopy(getattr(s, name)) for name in ('project', 'raw', 'runtime_manifest',
                'archive_source', 'runtime', 'qualified', 'cost', 'estimate', 'plans', 'execution', 'diagnostics')}
            cls.backup = cls.base_root / 'prepared-native-test-backup'
            assert s.op('backup_bundle', destination=str(cls.backup))['status'] == 'PASS'
            cls.operator_key = cls.base_root / 'operator.key'
            cls.operator_key.write_bytes((s.directory / 'operator.key').read_bytes())
        finally:
            builder.doCleanups()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-reserved-native-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.authority = deepcopy(self.__class__.authority)
        authority = patch.object(native_calibration_runs.NativeCalibrationResources, '_read_authority',
                                 side_effect=lambda: deepcopy(self.authority))
        authority.start(); self.addCleanup(authority.stop)
        self.s = native_support.NativeStudyIndependentTests('runTest')
        for name, value in self.facts.items(): setattr(self.s, name, deepcopy(value))
        self.s.root = self.root
        self.s.qualification_aliases = {}; self.s.current = True; self.s.resolve_calls = []
        resolver = patch.object(NativeQualifications, '_require_inputs', autospec=True,
            side_effect=lambda instance, identity, **options: self.s.resolve(instance, identity, **options))
        resolver.start(); self.addCleanup(resolver.stop)
        membership = patch.object(qualification_owner.profile, 'validate_runtime', return_value=None)
        membership.start(); self.addCleanup(membership.stop)
        profile = patch.object(pipeline, 'MANIFEST_SHA', digest(self.s.runtime_manifest))
        profile.start(); self.addCleanup(profile.stop)
        kernel = patch.object(pipeline, 'KERNEL_SHA', self.s.runtime_manifest['files'][pipeline.KERNEL_FILE]['sha256'])
        kernel.start(); self.addCleanup(kernel.stop)
        environment = patch.object(pipeline, 'current', side_effect=lambda value, *args: value == {'invented_environment': 'current'})
        environment.start(); self.addCleanup(environment.stop)
        self.clone_serial = 0
        self.clone()
        self.addCleanup(lambda: self.s.broker.close())
        self.clock = [0.0]
        clock = patch.object(time, 'monotonic', side_effect=lambda: self.clock[0])
        clock.start(); self.addCleanup(clock.stop)
        self.actual_transport = study_runs.execute_attempt
        self.meters = []
        def transport(source, payload, manifest, world, cases, remaining, meter, outputs, **options):
            self.meters.append(meter)
            return self.actual_transport(source, payload, manifest, world, cases, remaining, meter, outputs, **options)
        tracked = patch.object(study_runs, 'execute_attempt', side_effect=transport)
        tracked.start(); self.addCleanup(tracked.stop)
        child = patch.object(study_runs, '_run_child', side_effect=self.child)
        self.child_mock = child.start(); self.addCleanup(child.stop)

    def clone(self):
        if hasattr(self.s, 'broker'): self.s.broker.close()
        self.clone_serial += 1
        self.s.directory = self.root / ('registry-' + str(self.clone_serial))
        self.assertEqual(restore_bundle(self.backup, self.s.directory, self.operator_key)['status'], 'PASS')
        self.s.broker = financial_support.Broker(self.s.directory); self.s.token = self.s.broker.admin_token
        self.manager = native_calibration_runs.NativeCalibrationResources(self.s.broker)
        self.caller = native_calibration_runs.NativeCalibrationAttempts(self.s.broker)
        self.cancel = threading.Event(); self.mode = 'healthy'; self.variant = None
        self.child_calls = []; self.serial = 0
        if hasattr(self, 'clock'): self.clock[0] = 0.0

    def view(self):
        return self.manager.inspect(self.s.token, self.pool['id'])

    def reserve(self, index=0):
        self.serial += 1
        return self.manager.reserve(self.s.token, {'pool_id': self.pool['id'], 'phase': 'final',
            'task_id': self.tasks[index], 'attempt_id': format(self.serial, '032x'),
            'expected_checkpoint': self.view()['resource_checkpoint']})

    def execute(self, reservation):
        return self.caller.execute(self.s.token, self.pool['id'], reservation['attempt_id'], _cancel=self.cancel)

    def calculation(self, request):
        manifest, world, payload = request['manifest'], request['world'], request['payload']
        components = family_study.components(manifest, world)
        inner = self.mode in ('inner_clock', 'segment')
        outcomes = [{'id': item['id'], 'truth': manifest['effects'][item['scenario']],
            'state': 'TECHNICAL_FAILURE' if inner and index == 0 else 'INFORMATION_GAP',
            'decision': None, 'covered': None} for index, item in enumerate(components)]
        bound = {**payload, 'effects': manifest['effects'],
            'specification': manifest['profile']['specifications'][world['spec_index']], 'components': components,
            'time_rows': world['time_rows'], 'seed': world['population_seed'], 'bootstrap_seed': world['bootstrap_seed'],
            'limits': {'max_seconds': max(1, manifest['profile']['budget']['attempt_compute_ms'] // 1000)},
            'design': {'base_length': manifest['assigned']['base_length'],
                       'primary_count': manifest['assigned']['primary_count'], 'mc_policy': manifest['mc_policy']}}
        bootstraps = [{'id': item['id'], 'result': {'status': 'RESOURCE_STOP',
            'reason': 'computation_segment_limit' if self.mode == 'segment' else 'computation_time_limit'}
            if inner and index == 0 else {'status': 'INFORMATION_GAP'}} for index, item in enumerate(components)]
        outcome = family_study.outcome_record(manifest, world, outcomes)
        return {'schema': 'development-family-computation/1', 'world_id': world['id'],
            'status': 'INCOMPLETE', 'model': {'status': 'MODEL_SPECIFIED', 'fixture': 'simulated numerical engine'},
            'world': None, 'bootstraps': bootstraps, 'outcomes': outcomes, 'events': outcome['events'],
            'outer_world_count': 1, 'input_hash': digest(bound), 'outcome': outcome, 'n_min': None,
            'scientific_readiness': False, 'classification_permitted': False}

    def child(self, command, directory, timeout, **options):
        directory = Path(directory); request = decode((directory / 'request.json').read_bytes())
        self.assertIs(type(options['_control']), process.ProcessControl)
        self.assertIs(options['_cancel'], self.cancel)
        self.assertGreater(timeout, 0)
        self.assertNotIn('_cancel', request); self.assertNotIn('cancel', request)
        self.assertEqual(footprint({name: (directory / name).read_bytes() for name in self.s.project}), footprint(self.s.project))
        self.assertEqual((directory / 'cases.jsonl').read_bytes(), self.s.broker._read_blob_bytes(request['payload']['case_blob']['sha256']))
        phase = 'generate' if request['verify'] is None else 'replay'
        self.clock[0] += 0.001  # Explicit deterministic parent-meter fixture, not a timing measurement.
        self.child_calls.append((phase, request))
        (directory / 'child-errors.txt').write_bytes(b'Simulated numerical transport only.\n')
        if self.mode == 'preack_clock' and phase == 'generate':
            raise process.ChildDeadlineExceeded('Synthetic owned pre-ack clock')
        if self.mode == 'overrun_clock':
            self.clock[0] += 16
            raise process.ChildDeadlineExceeded('Synthetic clock with actual fixture-meter excess')
        if self.mode in ('generic_timeout', 'derived_clock', 'fake_parent_clock', 'fake_inner_clock', 'cancel', 'cleanup'):
            if self.mode == 'derived_clock':
                class Derived(process.ChildDeadlineExceeded): pass
                raise Derived('Derived type is not owned exact clock authority')
            kinds = {'generic_timeout': TimeoutError, 'fake_parent_clock': native_calibration_runs.AttemptDeadlineExceeded,
                'fake_inner_clock': native_calibration_runs.AuthenticatedCalculatorDeadline,
                'cancel': process.StudyProcessCancelled, 'cleanup': process.ChildCleanupFailed}
            raise kinds[self.mode]('Synthetic failure says deadline; strings are not authority')
        result = self.calculation(request)
        if self.variant == 'result': result['model']['fixture'] = 'different numerical result'
        if self.variant == 'authority': result['scientific_readiness'] = True
        if self.variant == 'world': result['world_id'] = 'f' * 64
        if self.variant == 'outcome': result['outcome']['components'][0]['truth'] = {'numerator': '99', 'denominator': '100'}
        path = directory / ('stream.jsonl.gz' if phase == 'generate' else 'expected-stream.jsonl.gz')
        stream_bytes = b'{"kind":"synthetic-engine-record","value":true}\n'
        if self.variant == 'stream': stream_bytes += b'{"kind":"different-retained-stream","value":true}\n'
        with path.open('xb' if phase == 'generate' else 'rb') as stream:
            encoded = EncodedStream(stream, encoded_limit=request['stream_limit'], verify=phase == 'replay')
            encoded.write(stream_bytes); encoding = encoded.finish()
        (directory / 'computed-result.json').write_text(canonical(result), encoding='utf-8')
        raw = path.read_bytes()
        response = {'result': result if phase == 'generate' else {'verified_result_hash': digest(result)},
            'request_hash': digest(request), 'footprint': footprint(self.s.project),
            'stream_blob': {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)},
            'stream_encoding': encoding, 'environment_before': {'invented_environment': 'current'},
            'environment': {'invented_environment': 'current'}, 'native_binding': digest(request['native']['binding']),
            'draw_engines': [{'length': 1, 'native': self.variant != 'engines'}],
            'process_control': {'before': deepcopy(CONTROL_OBSERVATION), 'after': deepcopy(CONTROL_OBSERVATION)}}
        (directory / 'child-output.json').write_text(canonical(response), encoding='utf-8')
        if phase == 'replay' and self.mode in ('replay_clock', 'revoke_replay'):
            if self.mode == 'revoke_replay':
                evidence = self.s.op('add_source', data_class='development', body={'synthetic_runtime_defect': True})
                self.s.op('revoke_dependency', key='reserved-runtime-defect', dependency_id=self.s.qualified['certificate']['id'],
                    reason='Synthetic late qualification withdrawal.', evidence_refs=[evidence['id']])
            raise process.ChildDeadlineExceeded('Synthetic owned replay clock')
        return response

    def test_healthy_reserved_call_uses_real_transport_full_replay_and_exact_owned_cost_custody(self):
        before = self.view()['budget']; reservation = self.reserve(); result = self.execute(reservation)
        body = result['body']
        self.assertEqual(body['schema'], 'native-family-calibration-attempt/1')
        self.assertEqual(body['resource_state'], 'COMPLETE')
        self.assertEqual(body['study_id'], self.final['id']); self.assertEqual(body['world_id'], reservation['task_id'])
        self.assertEqual(body['numerical_caller'], 'native-reserved-calculation/1')
        self.assertEqual(body['result']['outcome']['state'], 'INFORMATION_GAP')
        self.assertEqual(body['outcome'], body['result']['outcome'])
        self.assertEqual(len(body['proofs']), 2)
        self.assertEqual(body['replay_result'], {'verified_result_hash': digest(body['result'])})
        self.assertEqual(body['retry_comparison'], 'NOT_APPLICABLE')
        self.assertEqual(body['custody']['binding'], {'source_footprint': self.final['body']['source_footprint'],
            'payload_hash': digest(self.final['body']['payload']), 'manifest_hash': digest(self.final['body']['manifest']),
            'world_id': reservation['task_id'], 'native_binding': digest(self.final['body']['native_binding']),
            'process_control': POLICY})
        self.assertEqual(body['custody']['phases'], [
            {'phase': 'generate', 'result_hash': digest(body['result']), 'proof_hash': digest(body['proofs'][0])},
            {'phase': 'replay', 'result_hash': digest(body['replay_result']), 'proof_hash': digest(body['proofs'][1])}])
        self.assertEqual([phase for phase, request in self.child_calls], ['generate', 'replay'])
        self.assertIs(body['settlement']['usage_known'], True); self.assertFalse(self.cancel.is_set())
        expected_storage = self.meters[-1]['materialized_bytes'] + sum(item['size'] for item in body['output_blobs'].values()) + MIB
        self.assertEqual(body['settlement']['storage_bytes'], expected_storage)
        self.assertEqual(self.view()['budget']['charged_storage_bytes'], before['charged_storage_bytes'] + expected_storage)
        self.assertEqual(self.view()['budget']['charged_compute_ms'], before['charged_compute_ms'] + body['settlement']['compute_ms'])
        self.assertIs(body['scientific_readiness'], False)
        self.assertIsInstance(body['dispatch_event']['seq'], int)
        row = self.s.broker._db.execute('SELECT hash FROM events WHERE seq=?', (body['dispatch_event']['seq'],)).fetchone()
        self.assertEqual(row[0], body['dispatch_event']['hash'])
        for descriptor in body['output_blobs'].values(): self.s.broker._read_blob_bytes(descriptor['sha256'])

    def test_replay_clock_preserves_full_generation_then_same_world_retry_matches_full_bytes(self):
        self.mode = 'replay_clock'; first_reservation = self.reserve(); first = self.execute(first_reservation)
        self.assertEqual(first['body']['resource_state'], 'KNOWN_TIMEOUT')
        self.assertEqual(first['body']['result']['outcome']['state'], 'INFORMATION_GAP')
        self.assertEqual(first['body']['outcome']['state'], 'TECHNICAL_FAILURE')
        self.assertEqual(len(first['body']['proofs']), 1); self.assertIsNone(first['body']['replay_result'])
        self.assertFalse(self.cancel.is_set())
        self.mode = 'healthy'; retry_reservation = self.reserve(); retry = self.execute(retry_reservation)
        self.assertEqual(retry_reservation['task_id'], first_reservation['task_id'])
        self.assertEqual(retry['body']['resource_state'], 'COMPLETE')
        self.assertEqual(retry['body']['retry_comparison'], 'FULL_GENERATION_MATCH')
        self.assertEqual(retry['body']['result'], first['body']['result'])
        for name in ('generate/stream.jsonl.gz', 'generate/computed-result.json', 'generate/child-output.json'):
            old, new = first['body']['output_blobs'][name], retry['body']['output_blobs'][name]
            self.assertEqual(self.s.broker._read_blob_bytes(old['sha256']), self.s.broker._read_blob_bytes(new['sha256']))
        with self.assertRaises(ERRORS): self.reserve()

    def test_second_replay_clock_exhausts_only_same_task_and_independent_task_can_complete(self):
        self.mode = 'replay_clock'
        first = self.execute(self.reserve()); second = self.execute(self.reserve())
        self.assertEqual(first['body']['resource_state'], 'KNOWN_TIMEOUT')
        self.assertEqual(second['body']['resource_state'], 'KNOWN_TIMEOUT')
        self.assertEqual(second['body']['retry_comparison'], 'FULL_GENERATION_MATCH')
        with self.assertRaises(ERRORS): self.reserve()
        self.assertFalse(self.cancel.is_set()); self.assertIs(self.view()['budget']['halted'], False)
        self.mode = 'healthy'; independent = self.execute(self.reserve(1))
        self.assertEqual(independent['body']['resource_state'], 'COMPLETE')
        self.assertEqual(independent['body']['retry_comparison'], 'NOT_APPLICABLE')

    def test_preack_clock_has_no_fabricated_generation_and_retry_can_keep_missing_previous_scope(self):
        self.mode = 'preack_clock'; first = self.execute(self.reserve())
        self.assertEqual(first['body']['resource_state'], 'KNOWN_TIMEOUT')
        self.assertIsNone(first['body']['result']); self.assertEqual(first['body']['proofs'], [])
        self.assertEqual(first['body']['custody']['phases'], [])
        self.mode = 'healthy'; retry = self.execute(self.reserve())
        self.assertEqual(retry['body']['resource_state'], 'COMPLETE')
        self.assertEqual(retry['body']['retry_comparison'], 'NO_FULL_PREVIOUS_GENERATION')

    def test_authenticated_pinned_inner_clock_is_partial_then_full_retry_without_invented_equality(self):
        self.mode = 'inner_clock'; first = self.execute(self.reserve())
        self.assertEqual(first['body']['resource_state'], 'KNOWN_TIMEOUT')
        self.assertEqual(first['body']['failure']['type'], 'AuthenticatedCalculatorDeadline')
        self.assertEqual(len(first['body']['proofs']), 1)
        self.assertEqual(first['body']['result']['outcome']['state'], 'TECHNICAL_FAILURE')
        self.mode = 'healthy'; retry = self.execute(self.reserve())
        self.assertEqual(retry['body']['resource_state'], 'COMPLETE')
        self.assertEqual(retry['body']['retry_comparison'], 'NO_FULL_PREVIOUS_GENERATION')

    def test_generic_derived_fake_clock_segment_and_cancel_causes_fail_globally(self):
        for mode in ('generic_timeout', 'derived_clock', 'fake_parent_clock', 'fake_inner_clock', 'segment', 'cancel'):
            self.clone(); self.mode = mode
            with self.subTest(mode=mode):
                result = self.execute(self.reserve())
                self.assertEqual(result['body']['resource_state'], 'FAILED')
                self.assertTrue(self.cancel.is_set()); self.assertIs(self.view()['budget']['halted'], True)
                with self.assertRaises(ERRORS): self.reserve(1)

    def test_only_owned_remaining_callback_can_create_parent_deadline_authority(self):
        actual = NativeRuntimes._materialize
        def delayed(instance, identity, meter):
            path = actual(instance, identity, meter); self.clock[0] += 11; return path
        with patch.object(NativeRuntimes, '_materialize', side_effect=delayed, autospec=True):
            result = self.execute(self.reserve())
        self.assertEqual(result['body']['resource_state'], 'KNOWN_TIMEOUT')
        self.assertEqual(result['body']['failure']['type'], 'AttemptDeadlineExceeded')
        self.assertEqual(self.child_calls, []); self.assertFalse(self.cancel.is_set())

    def test_known_clock_with_observed_reservation_excess_is_a_global_resource_failure(self):
        self.mode = 'overrun_clock'; result = self.execute(self.reserve())
        self.assertEqual(result['body']['resource_state'], 'FAILED')
        self.assertGreater(result['body']['settlement']['compute_ms'], 15000)
        self.assertIs(self.view()['budget']['overrun'], True); self.assertTrue(self.cancel.is_set())

    def test_unknown_cleanup_retains_generation_outputs_and_full_conservative_reservation(self):
        self.mode = 'cleanup'; before = self.view()['budget']; result = self.execute(self.reserve())
        self.assertEqual(result['body']['resource_state'], 'FAILED')
        self.assertIs(result['body']['settlement']['usage_known'], False)
        self.assertEqual(self.view()['budget']['charged_compute_ms'], before['charged_compute_ms'] + 15000)
        self.assertEqual(self.view()['budget']['charged_storage_bytes'], before['charged_storage_bytes'] + 256 * MIB)
        self.assertIs(self.view()['budget']['usage_uncertain'], True); self.assertTrue(self.cancel.is_set())

    def test_late_qualification_revocation_during_replay_error_is_checked_and_primary_is_preserved(self):
        self.mode = 'revoke_replay'; result = self.execute(self.reserve())
        body = result['body']
        self.assertEqual(body['resource_state'], 'FAILED'); self.assertIs(body['currency_checked'], False)
        self.assertEqual(body['failure']['type'], 'ChildDeadlineExceeded')
        self.assertTrue(any(item['type'] == 'Denied' for item in body['failures']))
        self.assertEqual(len(body['proofs']), 1)
        self.assertIn('generate/stream.jsonl.gz', body['output_blobs']); self.assertTrue(self.cancel.is_set())

    def test_changed_full_retry_result_stream_or_engine_is_never_hidden_by_another_clock(self):
        for variant in ('result', 'stream', 'engines'):
            self.clone(); self.mode = 'replay_clock'; self.execute(self.reserve())
            self.variant = variant
            with self.subTest(variant=variant):
                result = self.execute(self.reserve())
                self.assertEqual(result['body']['resource_state'], 'FAILED')
                self.assertTrue(self.cancel.is_set()); self.assertIs(self.view()['budget']['halted'], True)

    def test_result_authority_world_or_outcome_forgery_fails_despite_valid_transport_replay(self):
        for variant in ('authority', 'world', 'outcome'):
            self.clone(); self.variant = variant
            with self.subTest(variant=variant):
                result = self.execute(self.reserve())
                self.assertEqual(result['body']['resource_state'], 'FAILED')
                self.assertTrue(self.cancel.is_set())

    def test_metadata_only_private_clock_cannot_buy_an_actual_calculator_retry(self):
        first = self.reserve()
        clock = {'type': 'ChildDeadlineExceeded', 'message': 'Metadata-only private-owner fixture, not actual dispatch'}
        self.manager.settle(self.s.token, self.pool['id'], {
            'resource_pool_id': self.pool['id'], 'phase': 'final', 'task_id': first['task_id'],
            'attempt_id': first['attempt_id'], 'study_id': self.final['id'], 'world_id': first['task_id'],
            'settlement': {'attempt_id': first['attempt_id'], 'compute_ms': 1, 'storage_bytes': MIB, 'usage_known': True},
            'resource_state': 'KNOWN_TIMEOUT', 'currency_checked': True, 'failure': clock, 'failures': [clock]})
        second = self.reserve()
        with patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Unowned retry reached cache')) as cache:
            result = self.execute(second)
        self.assertEqual(cache.call_count, 0); self.assertEqual(self.child_calls, [])
        self.assertEqual(result['body']['resource_state'], 'FAILED'); self.assertTrue(self.cancel.is_set())

    def test_unavailable_combined_custody_snapshot_still_retains_outputs_and_checks_currency(self):
        # Metadata boundary seam ONLY: each phase can be valid while their
        # combined snapshot exceeds codec.MAX_BYTES. No numerical claim follows.
        actual_after = self.caller.runner._study_after_execute
        actual_snapshot = process.NativeAttemptCustody.snapshot
        def combined_snapshot(container):
            snapshot = actual_snapshot(container)
            if len(snapshot['phases']) == 2:
                raise Invalid('Synthetic combined custody envelope exceeds its bound')
            return snapshot
        with patch.object(process.NativeAttemptCustody, 'snapshot',
                          autospec=True, side_effect=combined_snapshot), \
                patch.object(self.caller.runner, '_study_after_execute', wraps=actual_after) as after:
            result = self.execute(self.reserve())
        self.assertEqual(len(self.child_calls), 2)
        self.assertEqual(after.call_count, 1)
        self.assertEqual(result['body']['resource_state'], 'FAILED')
        self.assertTrue(result['body']['output_blobs'])
        self.assertIs(result['body']['settlement']['usage_known'], True)
        self.assertTrue(any(item['type'] == 'Invalid' for item in result['body']['failures']))
        self.assertEqual(self.view()['budget']['outstanding_attempts'], [])
        self.assertTrue(self.cancel.is_set()); self.assertIs(self.view()['budget']['halted'], True)

    def test_staging_failure_keeps_full_pending_cost_and_sticky_dispatch_claim_until_restart(self):
        reservation = self.reserve()
        with patch.object(self.s.broker, '_stage_blob_bytes', side_effect=RuntimeError('Synthetic output staging failure')):
            with self.assertRaises(RuntimeError): self.execute(reservation)
        self.assertTrue(self.cancel.is_set())
        before = len(self.child_calls)
        with self.assertRaises(ERRORS): self.execute(reservation)
        self.assertEqual(len(self.child_calls), before)
        self.assertIn(reservation['attempt_id'], self.view()['budget']['outstanding_attempts'])
        directory = self.s.directory; self.s.broker.close()
        self.s.broker = financial_support.Broker(directory); self.s.token = self.s.broker.admin_token
        self.manager = native_calibration_runs.NativeCalibrationResources(self.s.broker)
        self.assertIs(self.view()['budget']['usage_uncertain'], True)
        self.assertEqual(self.view()['budget']['outstanding_attempts'], [])

    def test_duplicate_unreserved_nonfinal_and_unauthorized_calls_never_dispatch(self):
        worker = self.s.op('register_worker', name='reserved-no-authority', role='discovery', capabilities=[])['token']
        with patch.object(self.s.broker, '_artifact', side_effect=AssertionError('Unauthorized private lookup')):
            with self.assertRaises(Denied): self.caller.execute(worker, self.pool['id'], 'f' * 32)
        with self.assertRaises(ERRORS): self.caller.execute(self.s.token, self.pool['id'], 'f' * 32)
        setup_task = next(iter(self.pool['body']['setup_tasks'].values()))
        setup = self.manager.reserve(self.s.token, {'pool_id': self.pool['id'], 'phase': 'setup',
            'task_id': setup_task, 'attempt_id': 'e' * 32, 'expected_checkpoint': self.view()['resource_checkpoint']})
        with self.assertRaises(ERRORS): self.caller.execute(self.s.token, self.pool['id'], setup['attempt_id'])
        self.assertEqual(self.child_calls, [])
        result = self.execute(self.reserve())
        with self.assertRaises(ERRORS): self.execute({'attempt_id': result['body']['attempt_id']})
        self.assertEqual(len(self.child_calls), 2)
        with self.assertRaises(Denied): self.s.op('advance_native_family_calibration', calibration_id=self.final['id'])


if __name__ == '__main__':
    unittest.main()
