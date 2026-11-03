"""Independent Registry resource-owner controls, not series admission.

Retired financial metadata is synthetic and disclosed. Its actual unchanged
history parser, immutable Registry, blobs and transaction owners must run; the
only authority substitution is an explicitly trusted test-authority seam.
"""
from copy import deepcopy
import hashlib
import importlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_information_study as scalar_support
from trading_researcher import calibration_recovery, family_study, native_runtime, study_runs
from trading_researcher.calibration_recovery import CalibrationRecovery
from trading_researcher.certification import _runtime_identity
from trading_researcher.codec import canonical, decode, digest
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.evaluation_plans import footprint, source_bundle
from trading_researcher.family_study_runs import FamilyCalibrationStudies
from trading_researcher.storage import restore_bundle


MIB, GIB = 1048576, 1073741824
AUTHORITY = 'bounded_native_calibration_resources_not_scientific_admission'
POOL = 'native-calibration-resource-pool/1'
ERRORS = (Invalid, Conflict, Denied)
PROJECT = Path(__file__).resolve().parents[1]
SETUP_TASKS = {'controller_source', 'runtime_retain', 'runtime_qualification',
               'acceptance_summary', 'prepare_reference_input', 'prepare_final_input', 'prepared_copies', 'terminal_copies'}


class RetiredFinancialFixture:
    """Synthetic financial rows; actual immutable Broker and old parser.

    No provider/certification/empirical proof is claimed. The19 VERIFIED labels
    and two tiny proof placeholders exist only to exercise historical accounting
    authentication. No Scalar operation or private input resolver is invoked.
    """
    def __init__(self, directory):
        self.root = Path(directory)
        self.broker = Broker(self.root / 'registry')
        self.token = self.broker.admin_token
        self.profile = scalar_support.profile()
        self.profile.update(targets=[16], worlds_per_cell=256, seed=714,
                            responses=['a', 'b'], patterns=[[0, 0], [0, 1], [1, 1], [2, 2]])
        self.profile['budget'].update(max_compute_ms=3600000, attempt_compute_ms=300000,
            max_storage_bytes=4 * GIB, attempt_storage_bytes=256 * MIB, max_attempts=1)
        assigned = scalar_support.assigned(); assigned['primary_count'] = 2
        manifest = family_study.make_final_manifest(assigned, self.profile)
        self.source = {'trading_researcher/financial_fixture.py': b'# Retained financial fixture; never executed.\n'}
        source_files = {name: self.blob(raw) for name, raw in self.source.items()}
        cases = self.blob(b'{"synthetic_financial_case":true}\n')
        transcript = self.blob(b'Explicit synthetic retired financial evidence, not a numerical result.\n')
        request = {'key': 'synthetic-retired-financial-study', 'development_study_id': 'd' * 64,
                   'time_rows': 16, 'seed': 714, 'budget': deepcopy(self.profile['budget']),
                   'cost_estimate': deepcopy(self.profile['cost_estimate']),
                   'applicability': {name: {'status': 'not_applicable', 'cohort_ids': [],
                       'reason': 'Synthetic retired financial fixture only.'}
                       for name in ('heavy_tail', 'overlap', 'common_shock')}}
        initial = 2 * sum(map(len, self.source.values())) + cases['size'] + MIB
        self.study = self.save({'schema': 'family-calibration-input/1', 'created_at': 1,
            'request': request, 'manifest': manifest, 'payload': {'case_blob': cases},
            'source_files': source_files, 'source_footprint': footprint(self.source),
            'assessment_source_footprint': footprint(self.source), 'runtime_identity': _runtime_identity(),
            'initial_storage_bytes': initial, 'scientific_readiness': False},
            authority='conditional_joint_family_calibration_not_scientific_admission',
            blobs=[*source_files.values(), cases])
        self.attempts = []
        for index, world in enumerate(manifest['worlds'][:20]):
            if index == 14:
                history = self.old_history()
                grant_request = {'key': 'synthetic-retired-grant', 'study_id': self.study['id'],
                    'expected_checkpoint': history.checkpoint, 'additional_compute_ms': 3600000,
                    'additional_storage_bytes': 4 * GIB, 'rationale': 'Retained financial fixture.',
                    'expected_progress': 'Retain the next fixed world.', 'stop_reason': 'Stop at the frozen boundary.'}
                refs, exposure = history.references()
                self.old_grant = self.save({'schema': 'study-resource-continuation/1', 'created_at': 2,
                    'request': grant_request, **history.terms(grant_request), 'scientific_readiness': False},
                    refs=refs, exposure=exposure, authority='bounded_resource_continuation_not_scientific_admission')
                self.event('information_study_continued', artifact_id=self.old_grant['id'])
            attempt_id = format(index + 1, '032x')
            self.event('information_study_reserved', reservation={'attempt_id': attempt_id,
                'world_id': world['id'], 'compute_ms': 300000, 'storage_bytes': 256 * MIB})
            failed = index == 19
            values = [{'id': item['id'], 'truth': manifest['effects'][item['scenario']],
                       'state': 'VERIFIED', 'decision': 'TESTED_NEGATIVE', 'covered': True}
                      for item in family_study.components(manifest, world)]
            outcome = family_study.outcome_record(manifest, world, failed=failed,
                                                 outcomes=None if failed else values)
            compute = 300226 if failed else 229571 if index == 18 else 250000
            settlement = {'attempt_id': attempt_id, 'compute_ms': compute,
                          'storage_bytes': 5000 if failed else 4000, 'usage_known': True}
            attempt = self.save({'schema': 'family-calibration-attempt/1', 'created_at': index + 3,
                'study_id': self.study['id'], 'world_id': world['id'], 'attempt_id': attempt_id,
                'settlement': settlement, 'outcome': outcome,
                'failure': {'type': 'ResourceOverrun', 'message': 'Synthetic known parent overrun'} if failed else None,
                'proofs': [] if failed else [{'phase': 'generate', 'synthetic_financial_only': True},
                                            {'phase': 'replay', 'synthetic_financial_only': True}],
                'output_blobs': {'synthetic-financial.txt': transcript}, 'scientific_readiness': False},
                refs=[self.study['id']], authority='conditional_joint_family_calibration_not_scientific_admission', blobs=[transcript])
            self.attempts.append(attempt)
            self.event('information_study_settled', settlement=settlement, outcome=outcome,
                       artifact_id=attempt['id'], orphan_uncertain=False)
        history = self.old_history(); budget = history.budget()
        assert budget['charged_compute_ms'] == 5029797 and history.last_completed == 14
        self.original_checkpoint = history.checkpoint
        q = {'schema': 'conditional-scalar-calibration-recovery-approval/1',
            'approved_exception': deepcopy(calibration_recovery.TERMS), 'study_id': self.study['id'],
            'terminal_checkpoint': history.checkpoint, 'failed_attempt_id': self.attempts[-1]['body']['attempt_id'],
            'failed_attempt_artifact_id': self.attempts[-1]['id'], 'failed_world_id': self.attempts[-1]['body']['world_id'],
            'fixed_identity': {'planned_worlds': 1024, 'known_compute_ms_retained': 5029797,
                'known_logical_bytes_retained': budget['charged_storage_bytes'], 'actual_grants_retained': 1,
                'verified_worlds_retained': 19, 'failed_attempt_retained': True,
                'all_original_world_and_seed_ids_unchanged': True, 'request_hash': digest(request),
                'manifest_hash': digest(manifest), 'recipe_hash': manifest['recipe_hash'],
                'calculation_source_footprint': digest(footprint(self.source))}}
        self.original_raw = (PROJECT / 'docs/reviews/implementation-2026-10-25/calibration-resource-approval-2026-11-02.json').read_bytes()
        approval_raw = canonical(q).encode()
        controller = {'trading_researcher/retired_controller_fixture.py': b'# Synthetic retired controller bytes; never imported.\n'}
        controller_files = {name: self.blob(raw) for name, raw in controller.items()}
        approvals = {'recovery': self.blob(approval_raw), 'original': self.blob(self.original_raw)}
        self.fee = 2 * (sum(len(raw) for raw in controller.values()) + sum(map(len, self.source.values()))
                        + len(approval_raw) + len(self.original_raw)) + 3 * MIB
        binding_scope = {'schema': 'calibration-recovery-authority-binding/1', 'calibration_id': self.study['id'],
            'assessment_host': str(self.root.resolve()), 'approval_path': str((self.root / 'retired-approval.json').resolve()),
            'approval_sha256': hashlib.sha256(approval_raw).hexdigest(),
            'original_approval_path': str((self.root / 'original-approval.json').resolve()),
            'original_approval_sha256': hashlib.sha256(self.original_raw).hexdigest()}
        self.input = self.recovery_save('calibration-recovery-input/1', {'key': 'retired-financial-setup',
            'study_id': self.study['id'], 'binding_scope': binding_scope,
            'registry_path': str(self.broker.directory), 'original_checkpoint': history.checkpoint,
            'original_attempt_ids': [item['id'] for item in self.attempts],
            'original_continuation_ids': [self.old_grant['id']], 'failed_attempt_artifact_id': self.attempts[-1]['id'],
            'failed_world_id': self.attempts[-1]['body']['world_id'], 'controller_files': controller_files,
            'controller_footprint': footprint(controller), 'assessment_source_files': source_files,
            'assessment_source_footprint': footprint(self.source), 'approval_blobs': approvals,
            'approval': q, 'setup_storage_bytes': self.fee, 'custody': 'PLANNED_NOT_REGISTERED'}, refs=[self.study['id']])
        self.event('calibration_recovery_setup_reserved', input_id=self.input['id'], storage_bytes=self.fee)
        self.recovery_source = self.recovery_save('calibration-recovery-source/1', {
            'input_id': self.input['id'], 'files': controller_files, 'footprint': footprint(controller)},
            refs=[self.input['id']], blobs=list(controller_files.values()))
        self.amendment = self.recovery_save('calibration-recovery-amendment/1', {
            'input_id': self.input['id'], 'study_id': self.study['id'], 'source_id': self.recovery_source['id'],
            'original_checkpoint': history.checkpoint, 'exception': deepcopy(calibration_recovery.TERMS),
            'assessment_source_files': source_files, 'assessment_source_footprint': footprint(self.source),
            'approval_blobs': approvals}, refs=[self.input['id'], self.recovery_source['id'], self.study['id']],
            blobs=[*source_files.values(), *approvals.values()])
        self.event('calibration_recovery_amended', input_id=self.input['id'], artifact_id=self.amendment['id'])
        self.event('calibration_recovery_setup_settled', input_id=self.input['id'], usage_known=True,
                   complete=True, failure=None, partial_blobs=[], unavailable_blobs=[])
        self.binding = {**binding_scope, 'registry_path': str(self.broker.directory)}
        self.recovery = CalibrationRecovery(self.broker, self.binding)
        self.state = self.recovery._history(self.input, self.amendment)
        assert self.state['setup_complete'] and not self.state['unknown'] and not self.state['pending']
        self.authority = self.authority_fixture()

    def blob(self, raw):
        return self.broker._stage_blob_bytes(raw)

    def save(self, body, *, refs=(), exposure=(), authority=AUTHORITY, blobs=()):
        with self.broker._transaction():
            for descriptor in blobs: self.broker._register_blob(descriptor)
            return self.broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'operations', 'authority': authority,
                'source_refs': sorted(set(refs)), 'exposure': sorted(set(exposure) | set(refs)),
                'blob_refs': sorted({descriptor['sha256'] for descriptor in blobs}), 'body': deepcopy(body)})

    def recovery_save(self, schema, body, **options):
        return self.save({'schema': schema, 'profile': 'scalar-calibration-recovery/1', 'created_at': 1,
                          **body, 'scientific_readiness': False, 'n_min': None},
                         authority='bounded_scalar_recovery_not_scientific_admission', **options)

    def event(self, action, **details):
        with self.broker._transaction():
            self.broker._event('controller', action, study_id=self.study['id'], **details)

    def old_history(self):
        return FamilyCalibrationStudies(self.broker)._study_resources(self.study)

    def authority_fixture(self):
        native = decode((PROJECT / 'docs/reviews/implementation-2026-10-25/native-parallel-calibration-approval-2026-11-03.json').read_bytes())
        # Trusted fixture authority transport only, not the actual2048 approval.
        native['scope']['worlds_total'] = 1024
        native['retired_scalar_state'].update(study_id=self.study['id'], prepared_amendment_id=self.amendment['id'],
            old_attempts=20, verified_worlds=19, old_grants=1, known_compute_ms=5029797,
            known_logical_bytes_after_setup=self.state['storage'], setup_fee_bytes_retained=self.fee)
        proposal = (PROJECT / 'docs/reviews/implementation-2026-10-25/native-calibration-proposal-revision-5-2026-11-03.source').read_text(encoding='utf-8')
        texts = {'native': canonical(native), 'original': self.original_raw.decode(), 'proposal': proposal}
        return {'native': native, 'original': decode(self.original_raw), 'texts': texts,
                'hashes': {name: hashlib.sha256(raw.encode()).hexdigest() for name, raw in texts.items()}}


def owner():
    return importlib.import_module('trading_researcher.native_calibration_runs')


class NativeResourceOwnerEntrypointIndependentTests(unittest.TestCase):
    def test_private_registry_owner_exists_before_domain_cases_can_run(self):
        self.assertIsNotNone(importlib.util.find_spec('trading_researcher.native_calibration_runs'),
                             'Registry resource owner absent; zero domain-flow coverage')
        self.assertTrue(callable(getattr(owner(), 'NativeCalibrationResources', None)))

    def test_default_authority_reads_exact_approved_documents_without_preparing_a_pool(self):
        with tempfile.TemporaryDirectory(prefix='trf-native-authority-read-') as temporary:
            broker = Broker(Path(temporary) / 'registry')
            try:
                authority = owner().NativeCalibrationResources(broker)._read_authority()
                self.assertEqual(authority['hashes'], {
                    'native': '9c28969e7078bba1dbd22b30d6746b3c1c7badb71d5ad36fa88a5076760123c3',
                    'original': '0b0475cab83f5d0c839ee2de9afba67a3b83eb5eb933ca583e251ceead20647a',
                    'proposal': '0995cf21a7278a8f72cfc05fa12b16160327b2ee27c5b3206aa9bd6ef7ad2b05'})
                self.assertEqual(authority['native']['scope']['worlds_total'], 2048)
                self.assertEqual(authority['native']['scope']['max_parallel_world_workers'], 6)
                self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], 0)
            finally:
                broker.close()


class NativeCalibrationResourceOwnerIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-financial-base-')
        cls.addClassCleanup(temporary.cleanup)
        root = Path(temporary.name)
        financial = RetiredFinancialFixture(root)
        try:
            cls.facts = {name: deepcopy(getattr(financial, name)) for name in (
                'study', 'attempts', 'old_grant', 'input', 'amendment', 'recovery_source',
                'fee', 'binding', 'source', 'original_checkpoint', 'authority')}
            cls.expected_storage = financial.state['storage']
            cls.prepared_checkpoint = financial.state['checkpoint']
            cls.backup = root / 'retired-financial-backup'
            assert financial.broker.call(financial.token, 'backup_bundle', destination=str(cls.backup))['status'] == 'PASS'
            cls.operator_key = root / 'operator.key'
            cls.operator_key.write_bytes((financial.broker.directory / 'operator.key').read_bytes())
        finally:
            financial.broker.close()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-resource-owner-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.authority = deepcopy(self.facts['authority'])
        seam = patch.object(owner().NativeCalibrationResources, '_read_authority',
                            side_effect=lambda: deepcopy(self.authority))
        seam.start(); self.addCleanup(seam.stop)
        self.directory = self.root / 'registry'
        self.assertEqual(restore_bundle(self.backup, self.directory, self.operator_key)['status'], 'PASS')
        self.broker = Broker(self.directory)
        self.addCleanup(lambda: self.broker.close())
        self.token = self.broker.admin_token
        self.manager = owner().NativeCalibrationResources(self.broker)
        self.f = RetiredFinancialFixture.__new__(RetiredFinancialFixture)
        for name, value in self.facts.items(): setattr(self.f, name, deepcopy(value))
        self.f.root, self.f.broker, self.f.token = self.root, self.broker, self.token
        self.f.binding = {**self.f.input['body']['binding_scope'], 'registry_path': str(self.directory)}
        self.f.recovery = CalibrationRecovery(self.broker, self.f.binding)
        numerical = patch.object(study_runs, 'execute_attempt', side_effect=AssertionError('Numerical dispatch forbidden'))
        self.numerical = numerical.start(); self.addCleanup(numerical.stop)
        materialize = patch.object(native_runtime.NativeRuntimes, '_materialize', side_effect=AssertionError('Cache work forbidden'))
        self.materialize = materialize.start(); self.addCleanup(materialize.stop)

    def prepare(self, key='native-resource-owner'):
        self.pool = self.manager.prepare(self.token, {'key': key})
        return self.pool

    def view(self):
        return self.manager.inspect(self.token, self.pool['id'])

    def inventory_request(self, count=7, **changes):
        return {'pool_id': self.pool['id'], 'key': 'fixed-acceptance-inventory', 'phase': 'acceptance',
            'task_ids': [format(index + 1, '064x') for index in range(count)],
            'execution_deadline_ms': 60000, 'attempt_compute_ms': 65000,
            'attempt_storage_bytes': 8 * MIB, 'max_attempts': 1,
            'expected_checkpoint': self.view()['resource_checkpoint'], **changes}

    def inventory(self, **changes):
        self.inventory_args = self.inventory_request(**changes)
        self.inv = self.manager.bind_inventory(self.token, self.inventory_args)
        return self.inv

    def reserve_request(self, index=0, **changes):
        return {'pool_id': self.pool['id'], 'phase': 'acceptance', 'task_id': format(index + 1, '064x'),
                'attempt_id': format(index + 1, '032x'),
                'expected_checkpoint': self.view()['resource_checkpoint'], **changes}

    def reserve(self, index=0):
        return self.manager.reserve(self.token, self.reserve_request(index))

    def body(self, reservation, *, failure=None, state='COMPLETE', known=True, storage=MIB + 4):
        return {'resource_pool_id': self.pool['id'], 'phase': 'acceptance',
            'task_id': reservation['task_id'], 'attempt_id': reservation['attempt_id'],
            'settlement': {'attempt_id': reservation['attempt_id'], 'compute_ms': 123,
                           'storage_bytes': storage, 'usage_known': known},
            'resource_state': state, 'currency_checked': True, 'failure': failure,
            'failures': [] if failure is None else [deepcopy(failure)], 'technical_refs': []}

    def settle(self, reservation, **changes):
        return self.manager.settle(self.token, self.pool['id'], self.body(reservation, **changes))

    def events(self, action=None):
        events = [decode(row[0]) for row in self.broker._db.execute('SELECT envelope FROM events ORDER BY seq')]
        return events if action is None else [event for event in events if event['action'] == action]

    def artifact_count(self, schema=POOL):
        return self.broker._db.execute("SELECT COUNT(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?", (schema,)).fetchone()[0]

    def test_prepare_derives_exact_retired_carry_through_unchanged_history_only(self):
        calls = []
        actual = CalibrationRecovery._history
        def history(instance, input_record, amendment):
            calls.append((input_record['id'], amendment['id']))
            return actual(instance, input_record, amendment)
        with patch.object(CalibrationRecovery, '_history', autospec=True, side_effect=history), \
                patch.object(CalibrationRecovery, '_original', side_effect=AssertionError('Old scientific inputs reactivated')), \
                patch.object(CalibrationRecovery, '_loaded_current', side_effect=AssertionError('Old host reactivated')), \
                patch.object(CalibrationRecovery, 'advance', side_effect=AssertionError('Scalar retry dispatched')):
            prepared = self.prepare()
        self.assertTrue(calls)
        self.assertTrue(all(pair == (self.f.input['id'], self.f.amendment['id']) for pair in calls))
        self.assertEqual(prepared['body']['carry'], {'schema': 'native-calibration-resource-carry/1',
            'basis_id': self.f.amendment['id'], 'charged_compute_ms': 5029797,
            'charged_storage_bytes': self.expected_storage, 'allocated_compute_ms': 7200000,
            'allocated_storage_bytes': 8 * GIB, 'grants_used': 1, 'progress_units': 19,
            'last_grant_progress': 14, 'no_progress_grants': 0})
        view = self.view()
        self.assertEqual(view['budget']['charged_compute_ms'], 5029797)
        self.assertEqual(view['budget']['charged_storage_bytes'], self.expected_storage + MIB)
        self.assertEqual(view['budget']['grants_used'], 1)
        self.assertEqual(view['budget']['grants_remaining'], 178)
        self.assertEqual(set(prepared['body']['setup_tasks']), SETUP_TASKS)
        self.assertEqual(set(view['inventories']), {'setup'})
        self.assertEqual(prepared['body']['source_footprint'], footprint(source_bundle()))
        self.assertEqual(prepared['body']['approval_texts'], self.authority['texts'])
        self.assertEqual(prepared['body']['approval_hashes'], self.authority['hashes'])
        self.assertEqual(self.broker._technical_dependencies(prepared), [])
        self.assertIs(view['scientific_readiness'], False)
        self.numerical.assert_not_called(); self.materialize.assert_not_called()

    def test_prepare_key_alias_and_inspection_cannot_reset_capacity_or_retained_objects(self):
        prepared = self.prepare(); before = self.view()
        self.assertEqual(self.prepare(), prepared)
        self.assertEqual(self.prepare('another-pool-key'), prepared)
        self.assertEqual(self.view(), before); self.assertEqual(self.artifact_count(), 1)
        for item in (self.f.study, self.f.input, self.f.amendment, self.f.old_grant):
            self.assertEqual(self.broker._artifact(item['id']), item)
        self.assertEqual(self.broker._dependency_use(prepared['id'])['status'], 'NOT_REVOKED')

    def test_refaked_authority_carry_or_missing_amendment_is_rejected_without_pool(self):
        original = deepcopy(self.authority)
        changes = [{'known_compute_ms': 5029798}, {'known_logical_bytes_after_setup': self.expected_storage + 1},
                   {'setup_fee_bytes_retained': self.f.fee + 1}, {'prepared_amendment_id': 'f' * 64}]
        for index, change in enumerate(changes):
            self.authority = deepcopy(original)
            self.authority['native']['retired_scalar_state'].update(change)
            # This is the trusted authorization transport seam, not a forged
            # public request. It still cannot replace actual financial evidence.
            self.authority['texts']['native'] = canonical(self.authority['native'])
            self.authority['hashes']['native'] = hashlib.sha256(self.authority['texts']['native'].encode()).hexdigest()
            with self.subTest(index=index), self.assertRaises(ERRORS): self.prepare('bad-carry-' + str(index))
            self.assertEqual(self.artifact_count(), 0)

    def test_duplicate_retired_setup_and_post_setup_scalar_reservation_cannot_be_imported(self):
        # First prove the actual parser sees any post-setup recovery work.
        state = self.f.recovery._history(self.f.input, self.f.amendment)
        self.f.event('calibration_recovery_reserved', input_id=self.f.input['id'],
            expected_checkpoint=state['checkpoint'], reservation={'attempt_id': 'e' * 32,
                'world_id': self.f.attempts[-1]['body']['world_id'], 'compute_ms': 600000, 'storage_bytes': 256 * MIB})
        with self.assertRaises(ERRORS): self.prepare()
        self.assertEqual(self.artifact_count(), 0)

    def test_worker_authentication_precedes_all_private_artifact_lookups(self):
        worker = self.broker.call(self.token, 'register_worker', name='native-resource-worker', role='discovery', capabilities=[])['token']
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Worker private lookup')):
            operations = [lambda: self.manager.prepare(worker, {'key': 'forbidden'}),
                lambda: self.manager.inspect(worker, 'f' * 64),
                lambda: self.manager.bind_inventory(worker, {}), lambda: self.manager.reserve(worker, {}),
                lambda: self.manager.settle(worker, 'f' * 64, {}), lambda: self.manager.continue_pool(worker, {}),
                lambda: self.manager.stop(worker, 'f' * 64, 'no authority')]
            for index, operation in enumerate(operations):
                with self.subTest(index=index), self.assertRaises(Denied): operation()

    def test_inventory_idempotent_key_and_six_reservations_are_durable_and_seventh_denied(self):
        self.prepare(); inv = self.inventory(); original_request = deepcopy(self.inventory_args)
        self.assertEqual(self.manager.bind_inventory(self.token, original_request), inv)
        with self.assertRaises(Conflict):
            self.manager.bind_inventory(self.token, {**original_request, 'task_ids': [format(55, '064x')]})
        reservations = [self.reserve(index) for index in range(6)]
        view = self.view()
        self.assertEqual(len(view['budget']['outstanding_attempts']), 6)
        self.assertEqual(view['budget']['charged_compute_ms'], 5029797 + 6 * 65000)
        self.assertEqual(view['budget']['charged_storage_bytes'], self.expected_storage + 2 * MIB + 6 * 8 * MIB)
        before = len(self.events())
        with self.assertRaises(ERRORS): self.reserve(6)
        self.assertEqual(len(self.events()), before)
        self.assertEqual(len(self.events('native_calibration_reserved')), 6)
        starts = [event for event in self.events('bound_computation_started')
                  if event['details'].get('attempt_id') in {item['attempt_id'] for item in reservations}]
        self.assertEqual(len(starts), 6)
        self.assertEqual(self.broker._technical_dependencies(inv), [self.pool['id']])

    def test_reservation_and_started_event_rollback_together_without_staging_or_dispatch(self):
        self.prepare(); self.inventory(); request = self.reserve_request(); original = self.view()
        event = self.broker._event
        def fail(actor, action, **details):
            if action == 'bound_computation_started': raise RuntimeError('Synthetic reservation publication failure')
            return event(actor, action, **details)
        with patch.object(self.broker, '_event', side_effect=fail), \
                patch.object(self.broker, '_stage_blob_bytes', side_effect=AssertionError('Reservation staged bytes')):
            with self.assertRaises(RuntimeError): self.manager.reserve(self.token, request)
        self.assertEqual(self.view(), original)
        self.assertEqual(self.events('native_calibration_reserved'), [])
        self.assertEqual(self.manager.reserve(self.token, request)['attempt_id'], request['attempt_id'])

    def test_source_capture_failure_leaves_no_pool_or_metadata_charge(self):
        before = len(self.events())
        with patch.object(owner(), 'source_bundle', side_effect=RuntimeError('Synthetic source capture unavailable')):
            with self.assertRaises((Invalid, Conflict, RuntimeError)): self.prepare()
        self.assertEqual(self.artifact_count(), 0); self.assertEqual(len(self.events()), before)

    def test_duplicate_retired_input_fences_import_without_rewriting_original_financial_rows(self):
        duplicate = self.f.recovery_save('calibration-recovery-input/1', {
            **self.f.input['body'], 'key': 'second-retired-setup-metadata'}, refs=[self.f.study['id']])
        self.assertNotEqual(duplicate['id'], self.f.input['id'])
        with self.assertRaises(ERRORS): self.prepare()
        self.assertEqual(self.artifact_count(), 0)
        self.assertEqual(self.broker._artifact(self.f.input['id']), self.f.input)

    def test_unknown_retired_recovery_settlement_cannot_be_imported_as_known_carry(self):
        state = self.f.recovery._history(self.f.input, self.f.amendment)
        attempt_id = 'e' * 32; world_id = self.f.attempts[-1]['body']['world_id']
        self.f.event('calibration_recovery_reserved', input_id=self.f.input['id'],
            expected_checkpoint=state['checkpoint'], reservation={'attempt_id': attempt_id,
                'world_id': world_id, 'compute_ms': 600000, 'storage_bytes': 256 * MIB})
        manifest = self.f.study['body']['manifest']
        world = next(world for world in manifest['worlds'] if world['id'] == world_id)
        self.f.event('calibration_recovery_settled', input_id=self.f.input['id'],
            settlement={'attempt_id': attempt_id, 'compute_ms': 0, 'storage_bytes': 0, 'usage_known': False},
            outcome=family_study.outcome_record(manifest, world, failed=True),
            artifact_id=None, orphan_uncertain=True)
        parsed = self.f.recovery._history(self.f.input, self.f.amendment)
        self.assertIs(parsed['unknown'], True); self.assertIs(parsed['orphan'], True)
        with self.assertRaises(ERRORS): self.prepare()
        self.assertEqual(self.artifact_count(), 0)

    def test_stale_checkpoint_race_commits_only_one_reservation_then_still_enforces_six_slots(self):
        import concurrent.futures
        import threading
        self.prepare(); self.inventory(); checkpoint = self.view()['resource_checkpoint']
        requests = [self.reserve_request(index, expected_checkpoint=checkpoint) for index in range(7)]
        barrier = threading.Barrier(7)
        def attempt(request):
            barrier.wait(timeout=10)
            try:
                return self.manager.reserve(self.token, request)
            except ERRORS as exc:
                return exc
        with concurrent.futures.ThreadPoolExecutor(max_workers=7) as workers:
            outcomes = list(workers.map(attempt, requests))
        accepted = [item for item in outcomes if type(item) is dict]
        self.assertEqual(len(accepted), 1)
        self.assertEqual(sum(isinstance(item, Conflict) for item in outcomes), 6)
        self.assertEqual(len(self.view()['budget']['outstanding_attempts']), 1)
        self.assertEqual(len(self.events('native_calibration_reserved')), 1)

    def test_owned_settlement_commits_output_blob_and_exact_observed_usage_once(self):
        self.prepare(); inv = self.inventory(); reservation = self.reserve()
        raw = b'Genuine owned synthetic acceptance output bytes.\n'
        descriptor = self.broker._stage_blob_bytes(raw)
        body = self.body(reservation, storage=MIB + len(raw)); body['output_blobs'] = {'retained.txt': descriptor}
        result = self.manager.settle(self.token, self.pool['id'], body, blob_refs=(descriptor,))
        self.assertEqual(result['body']['schema'], 'native-calibration-acceptance-attempt/1')
        self.assertEqual(result['body']['resource_inventory_id'], inv['id'])
        self.assertEqual(result['body']['resource_state'], 'COMPLETE')
        self.assertEqual(result['blob_refs'], [descriptor['sha256']])
        self.assertEqual(self.broker._read_blob_bytes(descriptor['sha256']), raw)
        self.assertEqual(self.broker._technical_dependencies(result), [self.pool['id'], inv['id']])
        view = self.view()
        self.assertEqual(view['budget']['charged_compute_ms'], 5029797 + 123)
        self.assertEqual(view['budget']['charged_storage_bytes'], self.expected_storage + 3 * MIB + len(raw))
        self.assertEqual(view['budget']['outstanding_attempts'], [])
        with self.assertRaises(ERRORS): self.manager.settle(self.token, self.pool['id'], body, blob_refs=(descriptor,))
        self.assertEqual(self.view(), view)

    def test_settlement_sql_failure_retains_pending_reservation_and_unregistered_physical_prefix(self):
        self.prepare(); self.inventory(); reservation = self.reserve()
        raw = b'Available output before synthetic settlement rollback.\n'
        descriptor = self.broker._stage_blob_bytes(raw)
        body = self.body(reservation); body['output_blobs'] = {'retained.txt': descriptor}
        before = self.view(); event = self.broker._event
        def fail(actor, action, **details):
            if action == 'native_calibration_settled': raise RuntimeError('Synthetic settlement publication failure')
            return event(actor, action, **details)
        with patch.object(self.broker, '_event', side_effect=fail), self.assertRaises(RuntimeError):
            self.manager.settle(self.token, self.pool['id'], body, blob_refs=(descriptor,))
        self.assertEqual(self.view(), before)
        self.assertEqual(self.artifact_count('native-calibration-acceptance-attempt/1'), 0)
        self.assertIsNone(self.broker._db.execute('SELECT size FROM blobs WHERE sha256=?', (descriptor['sha256'],)).fetchone())
        self.assertEqual(self.broker._blob_path(descriptor['sha256']).read_bytes(), raw)
        self.broker.close(); self.broker = Broker(self.directory)
        self.token = self.broker.admin_token; self.manager = owner().NativeCalibrationResources(self.broker)
        budget = self.view()['budget']
        self.assertIs(budget['usage_uncertain'], True); self.assertIs(budget['halted'], True)
        self.assertEqual(budget['charged_compute_ms'], 5029797 + 65000)
        self.assertEqual(budget['charged_storage_bytes'], self.expected_storage + 2 * MIB + 8 * MIB)

    def test_pool_revocation_stops_new_work_but_late_settlement_retains_outputs_and_original_cause(self):
        self.prepare(); self.inventory(); reservation = self.reserve()
        evidence = self.broker.call(self.token, 'add_source', data_class='development', body={'synthetic_pool_defect': True})
        self.broker.call(self.token, 'revoke_dependency', key='native-resource-pool-defect',
            dependency_id=self.pool['id'], reason='Synthetic current-use defect.', evidence_refs=[evidence['id']])
        with self.assertRaises(ERRORS): self.reserve(1)
        raw = b'Retained result despite pool revocation.\n'; descriptor = self.broker._stage_blob_bytes(raw)
        primary = {'type': 'OriginalComputationFailure', 'message': 'Original cause must survive late currency failure.'}
        body = self.body(reservation, failure=primary, state='FAILED'); body['output_blobs'] = {'retained.txt': descriptor}
        result = self.manager.settle(self.token, self.pool['id'], body, blob_refs=(descriptor,))
        self.assertEqual(result['body']['failure'], primary)
        self.assertEqual(result['body']['failures'][0], primary)
        self.assertGreaterEqual(len(result['body']['failures']), 2)
        self.assertIs(result['body']['currency_checked'], False)
        self.assertEqual(result['body']['resource_state'], 'FAILED')
        self.assertEqual(self.broker._read_blob_bytes(descriptor['sha256']), raw)
        self.assertIs(self.view()['budget']['halted'], True)
        self.assertEqual(self.view()['budget']['outstanding_attempts'], [])

    def test_changed_current_source_denies_new_work_and_forces_late_result_failed_without_losing_bytes(self):
        self.prepare(); self.inventory(); reservation = self.reserve()
        changed = source_bundle(); name = next(iter(changed)); changed[name] += b'\n# Synthetic loaded/disk drift seam\n'
        raw = b'Retained after current source drift.\n'; descriptor = self.broker._stage_blob_bytes(raw)
        body = self.body(reservation); body['output_blobs'] = {'retained.txt': descriptor}
        with patch.object(owner(), 'source_bundle', return_value=changed):
            self.assertEqual(self.view()['pool_id'], self.pool['id'])
            with self.assertRaises(ERRORS): self.reserve(1)
            result = self.manager.settle(self.token, self.pool['id'], body, blob_refs=(descriptor,))
        self.assertEqual(result['body']['resource_state'], 'FAILED')
        self.assertIs(result['body']['currency_checked'], False)
        self.assertTrue(result['body']['failures'])
        self.assertEqual(self.broker._read_blob_bytes(descriptor['sha256']), raw)
        self.assertIs(self.view()['budget']['halted'], True)

    def test_real_paired_grant_and_key_replay_keep_carry_fees_and_one_owned_chain(self):
        self.prepare(); self.inventory(count=2, execution_deadline_ms=3595000, attempt_compute_ms=3600000)
        view = self.view()
        request = {'key': 'owned-native-resource-grant', 'pool_id': self.pool['id'], 'phase': 'acceptance',
            'task_id': format(1, '064x'), 'expected_checkpoint': view['resource_checkpoint'],
            'additional_compute_ms': 3600000, 'additional_storage_bytes': 4 * GIB,
            'rationale': 'Continue the fixed metadata acceptance inventory.',
            'expected_progress': 'Complete the next owned fixed task.', 'stop_reason': 'Stop at every unresolved failure.'}
        grant = self.manager.continue_pool(self.token, request)
        self.assertEqual(self.manager.continue_pool(self.token, request), grant)
        with self.assertRaises(Conflict):
            self.manager.continue_pool(self.token, {**request, 'additional_storage_bytes': 4 * GIB - 1})
        with self.assertRaises(ERRORS): self.manager.continue_pool(self.token, {**request, 'key': 'stale-checkpoint'})
        budget = self.view()['budget']
        self.assertEqual(budget['allocated_compute_ms'], 10800000)
        self.assertEqual(budget['allocated_storage_bytes'], 12 * GIB)
        self.assertEqual(budget['charged_compute_ms'], 5029797)
        self.assertEqual(budget['charged_storage_bytes'], self.expected_storage + 3 * MIB)
        self.assertEqual(budget['grants_used'], 2)
        self.assertEqual(self.broker._technical_dependencies(grant), [self.pool['id']])

    def test_recover_skips_this_brokers_active_reservations_and_restart_charges_inherited_orphans(self):
        self.prepare(); self.inventory(); self.reserve(); self.reserve(1)
        before = self.view(); self.manager.recover()
        self.assertEqual(self.view(), before)
        self.broker.close(); self.broker = Broker(self.directory)
        self.token = self.broker.admin_token; self.manager = owner().NativeCalibrationResources(self.broker)
        view = self.view()
        self.assertEqual(view['budget']['outstanding_attempts'], [])
        self.assertIs(view['budget']['usage_uncertain'], True); self.assertIs(view['budget']['halted'], True)
        self.assertEqual(view['budget']['charged_compute_ms'], 5029797 + 2 * 65000)
        self.assertEqual(view['budget']['charged_storage_bytes'], self.expected_storage + 2 * MIB + 2 * 8 * MIB)
        self.assertEqual(self.artifact_count('native-calibration-acceptance-attempt/1'), 2)
        for row in self.broker._db.execute("SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')='native-calibration-acceptance-attempt/1'"):
            item = self.broker._artifact(row[0]); self.assertEqual(item['body']['resource_state'], 'ORPHAN_UNCERTAIN')
            self.assertIs(item['body']['settlement']['usage_known'], False)
        with self.assertRaises(ERRORS): self.reserve(2)

    def test_full_backup_restore_preserves_pool_all_output_bytes_financial_history_and_research_firewall(self):
        self.prepare(); self.inventory(); reservation = self.reserve()
        raw = b'Full owned output custody for preserved restore.\n'; descriptor = self.broker._stage_blob_bytes(raw)
        body = self.body(reservation); body['output_blobs'] = {'retained.txt': descriptor}
        result = self.manager.settle(self.token, self.pool['id'], body, blob_refs=(descriptor,))
        before = self.view(); pool = deepcopy(self.pool)
        backup = self.root / 'native-resource-owner-backup'
        self.assertEqual(self.broker.call(self.token, 'backup_bundle', destination=str(backup))['status'], 'PASS')
        self.broker.close(); restored = self.root / 'restored-registry'
        self.assertEqual(restore_bundle(backup, restored, self.operator_key)['status'], 'PASS')
        self.broker = Broker(restored); self.token = self.broker.admin_token
        self.manager = owner().NativeCalibrationResources(self.broker)
        self.assertEqual(self.view(), before); self.assertEqual(self.broker._artifact(pool['id']), pool)
        self.assertEqual(self.broker._artifact(result['id']), result)
        self.assertEqual(self.broker._read_blob_bytes(descriptor['sha256']), raw)
        for row in self.broker._db.execute('SELECT sha256 FROM blobs'): self.broker._read_blob_bytes(row[0])
        self.assertEqual(FamilyCalibrationStudies(self.broker)._study_resources(self.f.study).budget()['charged_compute_ms'], 5029797)
        self.assertEqual(self.broker.call(self.token, 'verify')['status'], 'PASS')
        wrapper = self.broker.call(self.token, 'add_source', data_class='development',
            body={'laundered_retired_financial_ancestry': True}, exposure=[pool['id']])
        for role in ('discovery', 'formalizer'):
            for identity in (pool['id'], wrapper['id']):
                with self.subTest(role=role, identity=identity), self.assertRaises(Denied):
                    self.broker.call(self.token, 'create_context', role=role, epoch=0, artifact_ids=[identity])

    def test_no_public_rpc_or_ready_override_can_supply_a_settlement_or_final_inventory(self):
        self.prepare()
        for operation in ('prepare_native_calibration_resources', 'settle_native_calibration_resources'):
            with self.subTest(operation=operation), self.assertRaises(Denied):
                self.broker.call(self.token, operation, approved=True)
        with self.assertRaises(Invalid): self.manager.prepare(self.token, {'key': 'caller-ready', 'ready': True})
        request = self.inventory_request(phase='final', max_attempts=2)
        with self.assertRaises(ERRORS): self.manager.bind_inventory(self.token, request)
        with self.assertRaises(ERRORS): self.manager.bind_inventory(self.token, request, input_id='f' * 64)
        self.assertEqual(set(self.view()['inventories']), {'setup'})

    def test_revoked_explicit_technical_dependency_forces_late_result_failed_and_retains_bytes(self):
        self.prepare(); self.inventory(); reservation = self.reserve()
        source_raw = b'# Supported technical-package fixture; never executed.\n'
        source_descriptor = self.broker._stage_blob_bytes(source_raw)
        source_name = 'trading_researcher/revoked_source_fixture.py'
        package = self.f.save({'schema': 'reference-source-package/1', 'created_at': 1,
            'footprint': {source_name: source_descriptor['sha256']},
            'files': {source_name: source_descriptor}}, authority='retained_source_not_certified',
            blobs=[source_descriptor])
        evidence = self.broker.call(self.token, 'add_source', data_class='development',
                                    body={'synthetic_technical_source_defect': True})
        self.broker.call(self.token, 'revoke_dependency', key='explicit-technical-input-defect',
            dependency_id=package['id'], reason='Synthetic technical source defect during outstanding work.',
            evidence_refs=[evidence['id']])
        raw = b'Available output from revoked explicit technical input.\n'
        descriptor = self.broker._stage_blob_bytes(raw)
        body = self.body(reservation, storage=MIB + len(raw) + len(source_raw))
        body['technical_refs'] = [package['id']]
        body['output_blobs'] = {'retained.txt': descriptor}
        result = self.manager.settle(self.token, self.pool['id'], body, blob_refs=(descriptor,))
        self.assertEqual(self.broker._read_blob_bytes(descriptor['sha256']), raw)
        self.assertEqual(self.broker._dependency_use(result['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
        self.assertEqual(result['body']['resource_state'], 'FAILED')
        self.assertIs(result['body']['currency_checked'], False)
        self.assertTrue(any(failure['type'] == 'Denied' for failure in result['body']['failures']))
        budget = self.view()['budget']
        self.assertEqual(budget['charged_compute_ms'], 5029797 + 123)
        self.assertEqual(budget['charged_storage_bytes'], self.expected_storage + 3 * MIB + len(raw) + len(source_raw))
        self.assertEqual(budget['progress_units'], 19)
        self.assertIs(budget['halted'], True)


if __name__ == '__main__':
    unittest.main()
