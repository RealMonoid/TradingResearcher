"""Independent fixed native reference corpus controls; no actual acceptance run.

Genuine disposable Registry/input/resource/transport owners are exercised in
domain cases. Numerical responses and native qualification remain labelled
synthetic seams; they provide no empirical or scientific admission evidence.
"""
from copy import deepcopy
from contextlib import closing
import hashlib
from pathlib import Path
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

import test_native_study_independent as native_support
import test_native_runtime_independent as runtime_support
import test_native_reserved_attempts_independent as reserved_support
import test_native_calibration_resource_owner_independent as financial_support

from trading_researcher import native_calibration_runs, native_study_runs, study_runs, native_study_pipeline as pipeline, family_study
from trading_researcher import study_process_control as process
from trading_researcher.calibration_runs import CalibrationStudies
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.evaluation_plans import source_bundle, footprint
from trading_researcher.family_study_runs import FamilyStudies
from trading_researcher.native_qualification import NativeQualifications
from trading_researcher import native_qualification as qualification_owner
from trading_researcher.native_runtime import NativeRuntimes
from trading_researcher.storage import restore_bundle
from trading_researcher.study_stream import EncodedStream


MIB = 1048576
ERRORS = (Invalid, Conflict, Denied)
INPUT = 'native-calibration-reference-input/1'
AUTHORITY = 'bounded_native_calibration_resources_not_scientific_admission'
POLICY = {'schema': 'native-study-process-control/1', 'library_threads': 1, 'priority': 'BELOW_NORMAL'}


class ReferenceWireFixture:
    """Invented numeric responses, genuine source/case/encoded-stream protocol.

    Both old Scalar development and later controlled native response use the
    same independently authored family-result oracle from the prior caller
    controls. No calculator, native binary or statistical draw runs here.
    """
    def __init__(self, support):
        self.support = support
        self.mode = 'healthy'
        self.calls = []
        self.cancel = None

    def child(self, command, directory, timeout, **options):
        s = self.support; directory = Path(directory)
        request = decode((directory / 'request.json').read_bytes())
        native = 'native' in request
        if native:
            s.assertIs(type(options['_control']), process.ProcessControl)
            s.assertIs(options['_cancel'], self.cancel)
            s.assertEqual(request['process_control'], POLICY)
        else:
            s.assertNotIn('_control', options); s.assertNotIn('_cancel', options)
            s.assertNotIn('process_control', request)
        s.assertNotIn('cancel', request); s.assertNotIn('_cancel', request)
        s.assertGreater(timeout, 0)
        s.assertEqual(footprint({name: (directory / name).read_bytes() for name in s.project}), footprint(s.project))
        s.assertEqual((directory / 'cases.jsonl').read_bytes(), s.broker._read_blob_bytes(request['payload']['case_blob']['sha256']))
        phase = 'generate' if request['verify'] is None else 'replay'
        self.calls.append((phase, deepcopy(request), native))
        s.clock[0] += 0.001
        (directory / 'child-errors.txt').write_bytes(b'Invented numerical reference transport only.\n')
        if native and self.mode in ('cancel', 'cleanup', 'preack_clock'):
            kind = {'cancel': process.StudyProcessCancelled, 'cleanup': process.ChildCleanupFailed,
                    'preack_clock': process.ChildDeadlineExceeded}[self.mode]
            raise kind('Explicit simulated reference failure, no acceptance evidence')
        result = reserved_support.NativeReservedAttemptsIndependentTests.calculation(
            types.SimpleNamespace(mode='healthy'), request)
        if native and self.mode == 'result': result['model']['fixture'] = 'changed full numerical result'
        path = directory / ('stream.jsonl.gz' if phase == 'generate' else 'expected-stream.jsonl.gz')
        raw_record = (canonical({'kind': 'invented-reference-vector', 'world_id': request['world']['id']}) + '\n').encode()
        if native and self.mode == 'stream': raw_record += b'{"kind":"changed-full-stream"}\n'
        with path.open('xb' if phase == 'generate' else 'rb') as stream:
            encoded = EncodedStream(stream, encoded_limit=request['stream_limit'], verify=phase == 'replay')
            encoded.write(raw_record); encoding = encoded.finish()
        raw = path.read_bytes()
        response = {'result': result if phase == 'generate' else {'verified_result_hash': digest(result)},
            'request_hash': digest(request), 'footprint': footprint(s.project),
            'stream_blob': {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)},
            'stream_encoding': encoding, 'environment': {'invented_environment': 'current' if native else 'old-reference'}}
        if native:
            response.update(environment_before={'invented_environment': 'current'},
                native_binding=digest(request['native']['binding']), draw_engines=[{'length': 1, 'native': True}],
                process_control={'before': deepcopy(reserved_support.CONTROL_OBSERVATION),
                                 'after': deepcopy(reserved_support.CONTROL_OBSERVATION)})
            (directory / 'computed-result.json').write_text(canonical(result), encoding='utf-8')
        (directory / 'child-output.json').write_text(canonical(response), encoding='utf-8')
        if native and phase == 'replay' and self.mode in ('replay_clock', 'late_revoke'):
            if self.mode == 'late_revoke':
                evidence = s.op('add_source', data_class='development', body={'invented_reference_defect': True})
                s.op('revoke_dependency', key='reference-mid-replay-withdrawal',
                    dependency_id=s.qualified['certificate']['id'], reason='Synthetic late native qualification defect.',
                    evidence_refs=[evidence['id']])
            raise process.ChildDeadlineExceeded('Explicit simulated owned replay deadline')
        return response


class NativeReferenceEntrypointIndependentTests(unittest.TestCase):
    def test_host_owned_fixed_reference_preparation_entrypoint_exists(self):
        self.assertTrue(callable(getattr(native_calibration_runs, 'NativeCalibrationReferences', None)),
                        'Fixed reference owner absent; zero reference domain-flow coverage')


class NativeReferenceClockBoundaryIndependentTests(unittest.TestCase):
    def test_outer_and_inner_acceptance_clock_stop_scheduling_before_postcurrency_callback(self):
        # NEGATIVE ordering seam only: real resource Registry/settlement but
        # typed reference metadata and source/input/executor transport seams.
        # It cannot qualify a reference corpus, a native runtime, or a world.
        for clock in ('outer', 'inner'):
            with self.subTest(clock=clock), tempfile.TemporaryDirectory(prefix='trf-reference-clock-order-') as temporary:
                f = financial_support.RetiredFinancialFixture(Path(temporary))
                try:
                    with patch.object(native_calibration_runs.NativeCalibrationResources, '_read_authority',
                                      return_value=deepcopy(f.authority)):
                        manager = native_calibration_runs.NativeCalibrationResources(f.broker)
                        pool = manager.prepare(f.token, {'key': 'negative-reference-clock-order'})
                        profile = deepcopy(f.study['body']['manifest']['profile'])
                        profile['worlds_per_cell'] = 1
                        manifest = family_study.make_manifest(f.study['body']['manifest']['assigned'], profile)
                        source = source_bundle(); payload = deepcopy(f.study['body']['payload'])
                        reference = f.save({'schema': INPUT, 'created_at': 1, 'scientific_readiness': False,
                            'request': {'key': 'negative-only-reference',
                            'development_study_id': f.recovery_source['id'], 'native_qualification_id': f.recovery_source['id']},
                            'payload': payload, 'manifest': manifest, 'references': {}, 'process_control': POLICY,
                            'source_footprint': footprint(source), 'native_binding': {'negative_ordering_fixture': True}},
                            refs=[f.recovery_source['id']], authority=AUTHORITY)
                        tasks = native_calibration_runs.NativeCalibrationReferences.tasks(reference)
                        inventory = manager.bind_inventory(f.token, {'pool_id': pool['id'], 'key': 'negative-ordering-inventory',
                            'phase': 'acceptance', 'task_ids': sorted(tasks), 'execution_deadline_ms': 10000,
                            'attempt_compute_ms': 15000, 'attempt_storage_bytes': 256 * MIB, 'max_attempts': 1,
                            'expected_checkpoint': manager.inspect(f.token, pool['id'])['resource_checkpoint']}, input_id=reference['id'])
                        task_id = sorted(tasks)[0]
                        reservation = manager.reserve(f.token, {'pool_id': pool['id'], 'phase': 'acceptance',
                            'task_id': task_id, 'attempt_id': 'a' * 32,
                            'expected_checkpoint': manager.inspect(f.token, pool['id'])['resource_checkpoint']})
                        caller = native_calibration_runs.NativeCalibrationAttempts(f.broker)
                        runner = caller.reference_runner; cancel = threading.Event(); observed = []
                        def execute(study, src, pld, original, world, cases, remaining, meter, outputs, **options):
                            prefix = b'Available output from explicit negative executor seam.\n'
                            meter['materialized_bytes'] += len(prefix); outputs.append(('generate/negative-prefix.txt', prefix))
                            if clock == 'outer': raise process.ChildDeadlineExceeded('Explicit owned outer-clock seam')
                            result = reserved_support.NativeReservedAttemptsIndependentTests.calculation(
                                types.SimpleNamespace(mode='inner_clock'), {'payload': pld, 'manifest': original, 'world': world})
                            proof = {'scope': 'negative metadata executor seam only; not transport authentication'}
                            custody = options['_custody']
                            custody._begin({'source_footprint': footprint(src), 'payload_hash': digest(pld),
                                'manifest_hash': digest(original), 'world_id': world['id'],
                                'native_binding': digest(study['body']['native_binding']), 'process_control': POLICY})
                            custody._record('generate', result, proof)
                            return result, [proof]
                        def after(study):
                            observed.append({'cancel': cancel.is_set(),
                                'halted': manager.inspect(f.token, pool['id'])['budget']['halted']})
                        with patch.object(runner, '_study_before_execute', return_value=None), \
                                patch.object(runner, '_study_inputs', return_value=(payload, manifest, reference['source_refs'], reference['exposure'])), \
                                patch.object(runner, '_load_study_source', return_value=source), \
                                patch.object(runner, 'compare', return_value='NO_FULL_CURRENT_GENERATION'), \
                                patch.object(runner, '_execute_study_attempt', side_effect=execute), \
                                patch.object(runner, '_study_after_execute', side_effect=after):
                            saved = caller.execute(f.token, pool['id'], reservation['attempt_id'], _cancel=cancel)
                        self.assertEqual(saved['body']['resource_state'], 'FAILED')
                        self.assertEqual(saved['body']['failure']['type'], 'ChildDeadlineExceeded' if clock == 'outer' else 'AuthenticatedCalculatorDeadline')
                        self.assertTrue(saved['body']['output_blobs'])
                        self.assertEqual(observed, [{'cancel': True, 'halted': True}])
                finally:
                    f.broker.close()


class NativeReferenceCallerIndependentTests(unittest.TestCase):
    """Genuine eight-world old corpus, sixteen mode tasks, simulated numerics.

    The actual old32/64-task parallel acceptance is not executed or qualified.
    Existing normalized-source/certification/compile owners run, then actual
    generation/replay retention handles independently invented wire results.
    """
    @classmethod
    def setUpClass(cls):
        native_support.NativeStudyIndependentTests.setUpClass()
        cls.addClassCleanup(native_support.NativeStudyIndependentTests.doClassCleanups)
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-reference-base-')
        cls.addClassCleanup(temporary.cleanup)
        cls.base_root = Path(temporary.name)
        actual_transport = study_runs.execute_attempt
        builder = native_support.NativeStudyIndependentTests('runTest'); builder.setUp()
        try:
            wire = ReferenceWireFixture(builder)
            with patch.object(study_runs, 'execute_attempt', side_effect=actual_transport), \
                    patch.object(study_runs, '_run_child', side_effect=wire.child), \
                    patch.object(study_runs, '_environment_current', side_effect=lambda value: value == {'invented_environment': 'old-reference'}):
                args = builder.args('fixed-old-reference-corpus', 'family', native=False,
                    budget={'max_compute_ms': 10000}, seed=713)
                # Two original targets make filtering to max(targets) fail an
                # actual retained-corpus assertion, without numerical expansion.
                args['profile']['targets'] = [2, 3]
                cls.development = builder.op('prepare_family_study', **args)
                assert len(cls.development['body']['manifest']['worlds']) == 8
                stopped = builder.op('advance_family_study', study_id=cls.development['id'])
                assert stopped['status'] == 'RESOURCE_STOP'
                cls.old_grant = builder.op('continue_study', **builder.grant(cls.development, stopped,
                    key='fixed-old-reference-completion-grant'))
                for _ in range(7): complete = builder.op('advance_family_study', study_id=cls.development['id'])
                assert complete['status'] == 'COMPLETE'
                assert len(complete['attempt_artifact_ids']) == 8 and len(wire.calls) == 16
            cls.old_attempts = [builder.broker._artifact(identity) for identity in complete['attempt_artifact_ids']]
            cls.old_vectors = {a['body']['world_id']: deepcopy(a) for a in cls.old_attempts}
            cls.old_bytes = {a['id']: builder.broker._db.execute('SELECT envelope FROM artifacts WHERE id=?',
                (a['id'],)).fetchone()[0] for a in [cls.development, *cls.old_attempts]}
            members = {'example/LICENSE.txt': b'Invented membership notice.\n',
                       pipeline.KERNEL_FILE: b'Invented membership bytes; never executed.\n'}
            builder.raw = runtime_support.archive(members.items()); builder.runtime_manifest = runtime_support.manifest(members)
            path = builder.root / 'reference-runtime.zip'; path.write_bytes(builder.raw)
            builder.archive_source = builder.op('add_blob_source', path=str(path), data_class='operations',
                description='Invented reference runtime membership seam; no numerical binary executed.')
            builder.runtime = builder.op('retain_native_runtime', key='reference-invented-runtime',
                archive_id=builder.archive_source['id'], manifest=builder.runtime_manifest)
            builder.qualified = builder.qualification(key='reference-invented-qualified-source')
            with patch.object(financial_support, 'Broker', return_value=builder.broker):
                financial = financial_support.RetiredFinancialFixture(builder.root)
            cls.authority = deepcopy(financial.authority)
            with patch.object(native_calibration_runs.NativeCalibrationResources, '_read_authority',
                              return_value=deepcopy(cls.authority)):
                manager = native_calibration_runs.NativeCalibrationResources(builder.broker)
                cls.pool = manager.prepare(builder.token, {'key': 'fixed-reference-test-pool'})
                cls.reference = native_calibration_runs.NativeCalibrationReferences(builder.broker).prepare(builder.token,
                    {'key': 'fixed-reference-test-input', 'development_study_id': cls.development['id'],
                     'native_qualification_id': builder.qualified['certificate']['id']})
            cls.facts = {name: deepcopy(getattr(builder, name)) for name in ('project', 'raw', 'runtime_manifest',
                'archive_source', 'runtime', 'qualified', 'cost', 'estimate', 'plans', 'execution', 'diagnostics')}
            cls.backup = cls.base_root / 'fixed-reference-backup'
            assert builder.op('backup_bundle', destination=str(cls.backup))['status'] == 'PASS'
            cls.operator_key = cls.base_root / 'operator.key'
            cls.operator_key.write_bytes((builder.directory / 'operator.key').read_bytes())
        finally:
            builder.doCleanups()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-reference-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name)
        self.s = native_support.NativeStudyIndependentTests('runTest'); self.s.root = self.root
        for name, value in self.facts.items(): setattr(self.s, name, deepcopy(value))
        self.s.current = True; self.s.qualification_aliases = {}; self.s.resolve_calls = []; self.s.clock = [0.0]
        authority = patch.object(native_calibration_runs.NativeCalibrationResources, '_read_authority',
            side_effect=lambda: deepcopy(self.authority)); authority.start(); self.addCleanup(authority.stop)
        resolver = patch.object(NativeQualifications, '_require_inputs', autospec=True,
            side_effect=lambda instance, identity, **options: self.s.resolve(instance, identity, **options))
        resolver.start(); self.addCleanup(resolver.stop)
        membership = patch.object(qualification_owner.profile, 'validate_runtime', return_value=None)
        membership.start(); self.addCleanup(membership.stop)
        for name, value in (('MANIFEST_SHA', digest(self.s.runtime_manifest)),
                            ('KERNEL_SHA', self.s.runtime_manifest['files'][pipeline.KERNEL_FILE]['sha256'])):
            member = patch.object(pipeline, name, value); member.start(); self.addCleanup(member.stop)
        environment = patch.object(pipeline, 'current', side_effect=lambda value, *args: value == {'invented_environment': 'current'})
        environment.start(); self.addCleanup(environment.stop)
        self.clone_serial = 0; self.clone()
        self.addCleanup(lambda: self.s.broker.close())
        clock = patch.object(study_runs.time, 'monotonic', side_effect=lambda: self.s.clock[0])
        clock.start(); self.addCleanup(clock.stop)
        self.wire = ReferenceWireFixture(self.s); self.wire.cancel = self.cancel
        child = patch.object(study_runs, '_run_child', side_effect=lambda *a, **kw: self.wire.child(*a, **kw))
        child.start(); self.addCleanup(child.stop)

    def clone(self):
        if hasattr(self.s, 'broker'): self.s.broker.close()
        self.clone_serial += 1; self.s.directory = self.root / ('registry-' + str(self.clone_serial))
        self.assertEqual(restore_bundle(self.backup, self.s.directory, self.operator_key)['status'], 'PASS')
        self.s.broker = financial_support.Broker(self.s.directory); self.s.token = self.s.broker.admin_token
        self.owner = native_calibration_runs.NativeCalibrationReferences(self.s.broker)
        self.manager = native_calibration_runs.NativeCalibrationResources(self.s.broker)
        self.caller = native_calibration_runs.NativeCalibrationAttempts(self.s.broker)
        self.cancel = threading.Event(); self.serial = 0; self.s.clock[0] = 0.0
        if hasattr(self, 'wire'): self.wire = ReferenceWireFixture(self.s); self.wire.cancel = self.cancel

    def view(self): return self.manager.inspect(self.s.token, self.pool['id'])

    def expected_tasks(self):
        return {digest({'reference_id': self.reference['id'], 'world_id': world['id'], 'mode': mode}):
                {'mode': mode, 'world_id': world['id']}
                for world in self.development['body']['manifest']['worlds'] for mode in ('serial', 'parallel')}

    def bind(self, *, tasks=None, input_id=None):
        return self.manager.bind_inventory(self.s.token, {'pool_id': self.pool['id'], 'key': 'fixed-reference-acceptance',
            'phase': 'acceptance', 'task_ids': sorted(self.expected_tasks() if tasks is None else tasks),
            'execution_deadline_ms': 10000, 'attempt_compute_ms': 15000, 'attempt_storage_bytes': 256 * MIB,
            'max_attempts': 1, 'expected_checkpoint': self.view()['resource_checkpoint']},
            input_id=self.reference['id'] if input_id is None else input_id)

    def reserve(self, task_id):
        self.serial += 1
        return self.manager.reserve(self.s.token, {'pool_id': self.pool['id'], 'phase': 'acceptance',
            'task_id': task_id, 'attempt_id': format(self.serial, '032x'),
            'expected_checkpoint': self.view()['resource_checkpoint']})

    def execute(self, reservation):
        return self.caller.execute(self.s.token, self.pool['id'], reservation['attempt_id'], _cancel=self.cancel)

    def revoke(self, identity):
        evidence = self.s.op('add_source', data_class='development', body={'invented_reference_defect': True})
        return self.s.op('revoke_dependency', key='reference-defect-' + identity, dependency_id=identity,
            reason='Synthetic retained dependency defect.', evidence_refs=[evidence['id']])

    def test_preparation_preserves_entire_old_corpus_vectors_cases_and_current_native_source(self):
        body = self.reference['body']
        self.assertEqual(body['schema'], INPUT); self.assertEqual(self.reference['authority'], AUTHORITY)
        self.assertEqual(self.reference['data_class'], 'operations')
        self.assertEqual(body['manifest'], self.development['body']['manifest'])
        self.assertEqual(body['payload'], self.development['body']['payload'])
        self.assertEqual(body['payload']['case_blob'], self.development['body']['payload']['case_blob'])
        expected = {world_id: {'attempt_id': a['id'], 'result_hash': digest(a['body']['result']),
            'stream_blob': a['body']['proofs'][0]['stream_blob'],
            'stream_encoding': a['body']['proofs'][0]['stream_encoding']} for world_id, a in self.old_vectors.items()}
        self.assertEqual(body['references'], expected)
        self.assertEqual(body['source_footprint'], footprint(self.s.project))
        self.assertEqual(body['process_control'], POLICY)
        self.assertNotIn('reference_tasks', body)
        self.assertIn(self.development['id'], self.reference['source_refs'])
        self.assertIn(self.old_grant['id'], self.reference['source_refs'])
        self.assertTrue({a['id'] for a in self.old_attempts} <= set(self.reference['source_refs']))
        self.assertIn(self.s.qualified['certificate']['id'], self.reference['source_refs'])
        self.assertIs(body['scientific_readiness'], False)
        self.assertFalse((self.s.directory / 'native-runtime-cache').exists())
        for identity, old in self.old_bytes.items():
            self.assertEqual(self.s.broker._db.execute('SELECT envelope FROM artifacts WHERE id=?', (identity,)).fetchone()[0], old)

    def test_mode_task_ids_are_exact_disjoint_fixed_sixteen_and_do_not_retarget_worlds(self):
        tasks = self.owner.tasks(self.reference)
        self.assertEqual(tasks, self.expected_tasks()); self.assertEqual(len(tasks), 16)
        self.assertEqual({task['world_id'] for task in tasks.values()}, set(self.old_vectors))
        for world_id in self.old_vectors:
            ids = [task for task, value in tasks.items() if value['world_id'] == world_id]
            self.assertEqual(len(ids), 2); self.assertTrue(set(ids).isdisjoint(self.old_vectors))

    def test_same_key_qualification_alias_and_new_key_preserve_original_immutable_input(self):
        args = {'key': 'fixed-reference-test-input', 'development_study_id': self.development['id'],
                'native_qualification_id': self.s.qualified['certificate']['id']}
        self.assertEqual(self.owner.prepare(self.s.token, args), self.reference)
        self.assertEqual(self.owner.prepare(self.s.token, {**args, 'key': 'fixed-reference-alias'}), self.reference)
        equivalent = self.s.qualification(key='reference-equivalent-qualification')
        self.s.qualification_aliases[equivalent['certificate']['id']] = equivalent
        self.assertEqual(self.owner.prepare(self.s.token, {**args, 'key': 'fixed-reference-certificate-alias',
            'native_qualification_id': equivalent['certificate']['id']}), self.reference)
        for field in ('seed', 'manifest', 'references', 'ready'):
            with self.subTest(field=field), self.assertRaises(Invalid):
                self.owner.prepare(self.s.token, {**args, field: True})

    def test_worker_and_source_forgery_fail_before_reference_lookup_or_cache(self):
        worker = self.s.op('register_worker', name='reference-no-authority', role='discovery', capabilities=[])['token']
        with patch.object(self.s.broker, '_artifact', side_effect=AssertionError('Unauthorized reference lookup')):
            with self.assertRaises(Denied): self.owner.prepare(worker,
                {'key': 'no-authority', 'development_study_id': '1' * 64, 'native_qualification_id': '2' * 64})
        with self.assertRaises(ERRORS):
            self.s.op('add_source', data_class='operations', body={'schema': INPUT})
        descendant = self.s.op('add_source', data_class='development', body={'fixture': 'laundered reference'},
            exposure=[self.reference['id']])
        for role in ('discovery', 'formalizer'):
            for artifact in (self.reference, descendant):
                with self.subTest(role=role, artifact_id=artifact['id']), self.assertRaises(Denied):
                    self.s.op('create_context', role=role, epoch=0, artifact_ids=[artifact['id']])

    def test_reference_is_typed_dependency_and_reserved_seed_inventory_even_before_execution(self):
        deps = set(self.s.broker._technical_dependencies(self.reference))
        self.assertTrue({self.development['id'], self.s.qualified['certificate']['id'],
                         *[attempt['id'] for attempt in self.old_attempts]} <= deps)
        recorded = {a['id']: worlds for a, worlds in CalibrationStudies(self.s.broker)._recorded_calibration_worlds()}
        self.assertEqual(recorded[self.reference['id']], self.development['body']['manifest']['worlds'])
        self.revoke(self.s.qualified['certificate']['id'])
        with self.assertRaises(Denied): self.s.broker._require_usable_dependencies(self.reference['id'])
        self.assertEqual(self.owner._study(self.reference['id']), self.reference)

    def test_inventory_must_bind_all_modes_exactly_and_correct_owned_reference(self):
        before = self.view()
        tasks = sorted(self.expected_tasks())
        with self.assertRaises(ERRORS): self.bind(tasks=tasks[:-1])
        with self.assertRaises(ERRORS): self.bind(tasks=[*tasks[:-1], 'f' * 64])
        with self.assertRaises(ERRORS): self.bind(input_id=self.development['id'])
        self.assertEqual(self.view(), before)

    def test_serial_and_parallel_each_reproduce_full_old_result_and_encoded_decoded_streams(self):
        inventory = self.bind(); before = self.view()['budget']
        world_id = self.development['body']['manifest']['worlds'][0]['id']
        results = []
        for mode in ('serial', 'parallel'):
            task_id = next(k for k, v in self.expected_tasks().items() if v == {'mode': mode, 'world_id': world_id})
            saved = self.execute(self.reserve(task_id)); body = saved['body']; results.append(saved)
            old = self.old_vectors[world_id]
            self.assertEqual(body['schema'], 'native-calibration-acceptance-attempt/1')
            self.assertEqual(body['resource_state'], 'COMPLETE')
            self.assertEqual(body['task_id'], task_id); self.assertEqual(body['world_id'], world_id)
            self.assertEqual(body['reference_mode'], mode)
            self.assertEqual(body['reference_comparison'], 'FULL_REFERENCE_MATCH')
            for key in ('input_id', 'study_id', 'reference_id'): self.assertEqual(body[key], self.reference['id'])
            self.assertEqual(body['custody']['binding']['world_id'], world_id)
            self.assertEqual(body['result'], old['body']['result']); self.assertEqual(len(body['proofs']), 2)
            self.assertEqual(body['proofs'][0]['stream_blob'], old['body']['proofs'][0]['stream_blob'])
            self.assertEqual(body['proofs'][0]['stream_encoding'], old['body']['proofs'][0]['stream_encoding'])
            self.assertNotEqual(body['proofs'][0]['request_hash'], old['body']['proofs'][0]['request_hash'])
            self.assertNotEqual(body['proofs'][0]['environment'], old['body']['proofs'][0]['environment'])
            new = body['output_blobs']['generate/stream.jsonl.gz']; old_stream = old['body']['proofs'][0]['stream_blob']
            self.assertEqual(self.s.broker._read_blob_bytes(new['sha256']), self.s.broker._read_blob_bytes(old_stream['sha256']))
            self.assertIs(body['scientific_readiness'], False)
            self.assertIn(self.reference['id'], self.s.broker._technical_dependencies(saved))
        self.assertEqual([native for _, _, native in self.wire.calls], [True] * 4)
        self.assertEqual(self.view()['budget']['charged_compute_ms'], before['charged_compute_ms'] + sum(a['body']['settlement']['compute_ms'] for a in results))
        self.assertEqual(self.view()['budget']['charged_storage_bytes'], before['charged_storage_bytes'] + sum(a['body']['settlement']['storage_bytes'] for a in results))
        self.assertFalse(self.cancel.is_set()); self.assertIn(self.reference['id'], self.s.broker._technical_dependencies(inventory))

    def test_changed_full_result_or_stream_is_failed_retained_and_never_clock_retry(self):
        for mode in ('result', 'stream'):
            self.clone(); self.bind(); self.wire.mode = mode
            task_id = next(iter(self.expected_tasks()))
            with self.subTest(mode=mode):
                saved = self.execute(self.reserve(task_id)); body = saved['body']
                self.assertEqual(body['resource_state'], 'FAILED'); self.assertTrue(body['output_blobs'])
                self.assertIs(body['settlement']['usage_known'], True); self.assertTrue(self.cancel.is_set())
                self.assertIs(self.view()['budget']['halted'], True)
                with self.assertRaises(ERRORS): self.reserve(task_id)

    def test_acceptance_owned_replay_clock_retains_generation_but_never_acquires_a1_retry(self):
        self.bind(); self.wire.mode = 'replay_clock'; task_id = next(iter(self.expected_tasks()))
        saved = self.execute(self.reserve(task_id)); body = saved['body']
        self.assertEqual(body['resource_state'], 'FAILED')
        self.assertEqual(body['failure']['type'], 'ChildDeadlineExceeded')
        self.assertEqual(body['result'], self.old_vectors[body['world_id']]['body']['result'])
        self.assertEqual(len(body['proofs']), 1); self.assertIsNone(body['replay_result'])
        self.assertTrue(self.cancel.is_set()); self.assertIs(self.view()['budget']['halted'], True)
        with self.assertRaises(ERRORS): self.reserve(task_id)

    def test_cancel_and_unknown_cleanup_keep_prefixes_and_conservative_charges(self):
        for mode in ('cancel', 'cleanup'):
            self.clone(); self.bind(); self.wire.mode = mode; before = self.view()['budget']
            with self.subTest(mode=mode):
                saved = self.execute(self.reserve(next(iter(self.expected_tasks())))); body = saved['body']
                self.assertEqual(body['resource_state'], 'FAILED'); self.assertTrue(body['output_blobs'])
                self.assertTrue(self.cancel.is_set())
                if mode == 'cleanup':
                    self.assertIs(body['settlement']['usage_known'], False)
                    self.assertEqual(self.view()['budget']['charged_compute_ms'], before['charged_compute_ms'] + 15000)
                    self.assertEqual(self.view()['budget']['charged_storage_bytes'], before['charged_storage_bytes'] + 256 * MIB)

    def test_metadata_only_acceptance_inventory_cannot_gain_a_numerical_dispatch(self):
        task_id = digest({'fixture': 'unqualified acceptance metadata only'})
        self.manager.bind_inventory(self.s.token, {'pool_id': self.pool['id'], 'key': 'metadata-only-acceptance',
            'phase': 'acceptance', 'task_ids': [task_id], 'execution_deadline_ms': 10000,
            'attempt_compute_ms': 15000, 'attempt_storage_bytes': 256 * MIB, 'max_attempts': 1,
            'expected_checkpoint': self.view()['resource_checkpoint']}, input_id=None)
        reservation = self.reserve(task_id); before = self.view()
        with patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Metadata inventory reached cache')):
            with self.assertRaises((Invalid, Denied)): self.execute(reservation)
        self.assertEqual(self.wire.calls, []); self.assertEqual(self.view(), before)
        self.assertNotIn(reservation['attempt_id'], self.s.broker._native_calibration_dispatched)
        count = self.s.broker._db.execute("SELECT COUNT(*) FROM events WHERE "
            "json_extract(envelope,'$.action')='native_calibration_numerical_dispatched' AND "
            "json_extract(envelope,'$.details.attempt_id')=?", (reservation['attempt_id'],)).fetchone()[0]
        self.assertEqual(count, 0); self.assertFalse(self.cancel.is_set())

    def test_late_qualification_withdrawal_preserves_clock_primary_and_forces_failure(self):
        self.bind(); self.wire.mode = 'late_revoke'
        saved = self.execute(self.reserve(next(iter(self.expected_tasks())))); body = saved['body']
        self.assertEqual(body['resource_state'], 'FAILED'); self.assertIs(body['currency_checked'], False)
        self.assertEqual(body['failure']['type'], 'ChildDeadlineExceeded')
        self.assertTrue(any(f['type'] == 'Denied' for f in body['failures']))
        self.assertTrue(body['output_blobs']); self.assertTrue(self.cancel.is_set())

    def test_revoked_old_grant_and_corrupt_old_stream_cannot_start_new_reference_work(self):
        for fault in ('grant', 'stream'):
            self.clone()
            if fault == 'grant':
                revocation = self.revoke(self.old_grant['id'])
                use = self.s.broker._dependency_use(self.reference['id'])
                self.assertEqual(use['status'], 'INVALIDATED_BY_DEPENDENCY')
                self.assertIn(self.old_grant['id'], use['checked_versions'])
                self.assertTrue(any(item['revocation_id'] == revocation['id']
                    and item['dependency_id'] == self.old_grant['id'] for item in use['invalidations']))
            else:
                checksum = next(iter(self.old_vectors.values()))['body']['proofs'][0]['stream_blob']['sha256']
                path = self.s.broker._blob_path(checksum); path.write_bytes(b'Corrupt owned clone only.')
            with self.subTest(fault=fault), patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Bad old reference reached cache')):
                with self.assertRaises(ERRORS): self.owner.prepare(self.s.token,
                    {'key': 'changed-old-input-' + fault, 'development_study_id': self.development['id'],
                     'native_qualification_id': self.s.qualified['certificate']['id']})
            self.assertEqual(self.wire.calls, [])

    def test_incomplete_old_development_cannot_become_a_reference_by_request_labels(self):
        pending = self.s.op('prepare_family_study', **self.s.args('unfinished-reference-source', 'family',
            native=False, seed=990))
        with patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Unfinished corpus reached cache')):
            with self.assertRaises(ERRORS): self.owner.prepare(self.s.token,
                {'key': 'unfinished-reference', 'development_study_id': pending['id'],
                 'native_qualification_id': self.s.qualified['certificate']['id']})
        self.assertEqual(self.wire.calls, [])

    def test_corrupt_cases_and_noncurrent_qualification_or_host_source_fail_before_cache(self):
        for fault in ('cases', 'qualification', 'host_source'):
            self.clone(); self.s.current = True
            changed = deepcopy(self.s.project)
            if fault == 'cases':
                descriptor = self.reference['body']['payload']['case_blob']
                self.s.broker._blob_path(descriptor['sha256']).write_bytes(b'Corrupt cases in this owned clone only.')
            elif fault == 'qualification': self.s.current = False
            else:
                name = 'trading_researcher/native_study_runs.py'
                changed[name] += b'\n# Invented current-disk metadata difference; no workspace file mutation.\n'
            # Host source is an explicit metadata-read seam only. The actual
            # native-input source-equality owner remains unmodified.
            with self.subTest(fault=fault), \
                    patch.object(native_study_runs, 'source_bundle', return_value=changed), \
                    patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Bad current input reached cache')):
                with self.assertRaises(ERRORS): self.owner.prepare(self.s.token,
                    {'key': 'bad-current-reference-' + fault, 'development_study_id': self.development['id'],
                     'native_qualification_id': self.s.qualified['certificate']['id']})
            self.assertEqual(self.wire.calls, [])

    def test_backup_restore_retains_reference_custody_history_and_immutable_originals(self):
        self.bind(); saved = self.execute(self.reserve(next(iter(self.expected_tasks()))))
        expected = self.view(); backup = self.root / 'after-reference-backup'
        self.assertEqual(self.s.op('backup_bundle', destination=str(backup))['status'], 'PASS')
        target = self.root / 'full-preserved-reference-restore'
        self.assertEqual(restore_bundle(backup, target, self.operator_key)['status'], 'PASS')
        with closing(financial_support.Broker(target)) as restored:
            self.assertEqual(restored._artifact(self.reference['id']), self.reference)
            self.assertEqual(restored._artifact(saved['id']), saved)
            actual = native_calibration_runs.NativeCalibrationResources(restored).inspect(restored.admin_token, self.pool['id'])
            self.assertEqual(actual, expected)
            for descriptor in saved['body']['output_blobs'].values(): restored._read_blob_bytes(descriptor['sha256'])
            for identity, old in self.old_bytes.items():
                self.assertEqual(restored._db.execute('SELECT envelope FROM artifacts WHERE id=?', (identity,)).fetchone()[0], old)

    def test_input_bound_acceptance_orphan_keeps_full_charge_and_exact_reference_task_identity(self):
        self.bind()
        task_id = next(k for k, v in self.expected_tasks().items() if v['mode'] == 'parallel')
        selected = self.expected_tasks()[task_id]; reservation = self.reserve(task_id)
        before = self.view()['budget']; directory = self.s.directory
        self.s.broker.close(); self.s.broker = financial_support.Broker(directory)
        self.s.token = self.s.broker.admin_token
        self.manager = native_calibration_runs.NativeCalibrationResources(self.s.broker)
        view = self.view(); budget = view['budget']
        self.assertEqual(budget['charged_compute_ms'], before['charged_compute_ms'])
        self.assertEqual(budget['charged_storage_bytes'], before['charged_storage_bytes'])
        self.assertEqual(budget['outstanding_attempts'], [])
        self.assertIs(budget['usage_uncertain'], True); self.assertIs(budget['halted'], True)
        record = self.manager._history(self.pool).records[('acceptance', task_id)]
        body = self.s.broker._artifact(record['artifact_id'])['body']
        self.assertEqual(body['resource_state'], 'ORPHAN_UNCERTAIN')
        self.assertEqual(body['attempt_id'], reservation['attempt_id']); self.assertEqual(body['task_id'], task_id)
        self.assertEqual(body['world_id'], selected['world_id']); self.assertEqual(body['reference_mode'], 'parallel')
        for key in ('reference_id', 'input_id', 'study_id'): self.assertEqual(body[key], self.reference['id'])
        self.assertIs(body['settlement']['usage_known'], False)
        self.assertEqual(body['settlement']['compute_ms'], 0); self.assertEqual(body['settlement']['storage_bytes'], 0)
        self.assertEqual(self.wire.calls, [])
        with self.assertRaises(ERRORS): self.reserve(next(k for k in self.expected_tasks() if k != task_id))


if __name__ == '__main__':
    unittest.main()
