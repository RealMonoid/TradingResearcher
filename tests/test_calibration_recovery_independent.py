"""Independent one-off recovery kernel cases; no real-series authorization.

Genuine owned FamilyFixture inputs/certificates and input recomputation are kept.
Historical failure observations, clock faults and substituted final transports
are explicitly synthetic transaction fixtures. The live2048-world study and its
Registry are never opened. New module absence is0 recovery-flow coverage; the
preimplementation check separately demonstrates the correct old300s/max1 fence.
"""
from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

import family_run_support as family_support
import test_information_study as scalar_support
from trading_researcher import family_study, study_runs
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.evaluation_plans import source_bundle
from trading_researcher.family_study_runs import FamilyCalibrationStudies
from trading_researcher.information_study import budget_state
from trading_researcher.storage import restore_bundle


MIB = 1048576
GIB = 1073741824
MODULE = 'trading_researcher.calibration_recovery'
PROFILE = 'scalar-calibration-recovery/1'
INPUT = 'calibration-recovery-input/1'
SOURCE = 'calibration-recovery-source/1'
AMENDMENT = 'calibration-recovery-amendment/1'
RESULT = 'calibration-recovery-attempt/1'
GRANT = 'calibration-recovery-continuation/1'
ERRORS = (Invalid, Denied, Conflict, OSError)
BINDING_FIELDS = {'schema', 'calibration_id', 'registry_path', 'assessment_host',
    'approval_path', 'approval_sha256', 'original_approval_path', 'original_approval_sha256'}
TERMS = {'additional_attempts_for_named_failed_world': 1,
    'attempt_compute_ms_for_retry_and_remaining_original_worlds': 600000,
    'other_worlds_max_attempts': 1, 'attempt_storage_bytes': 268435456,
    'aggregate_compute_ms': 648000000, 'aggregate_logical_bytes': 107374182400,
    'additional_grants_max': 179}


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def identity(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def crash_after_committed_reservation(binding_file, mode, recovery_id=None, checkpoint=None):
    """Child-only hard exit after a real owned SQL commit, before any numerical work."""
    binding = json.loads(Path(binding_file).read_text(encoding='utf-8'))
    owner = importlib.import_module(MODULE)
    broker = Broker(binding['registry_path'])
    kernel = owner.CalibrationRecovery(broker, binding)
    action = 'calibration_recovery_setup_reserved' if mode == 'setup' else 'calibration_recovery_reserved'
    original_transaction = broker._transaction
    @contextmanager
    def committed_then_exit():
        before = broker._db.execute("SELECT COUNT(*) FROM events WHERE json_extract(envelope,'$.action')=?",
                                    (action,)).fetchone()[0]
        with original_transaction():
            yield
        after = broker._db.execute("SELECT COUNT(*) FROM events WHERE json_extract(envelope,'$.action')=?",
                                   (action,)).fetchone()[0]
        if after > before:
            os._exit(91)
    broker._transaction = committed_then_exit
    with patch.object(owner, 'execute_attempt', side_effect=AssertionError('Crash fixture reached numerical transport')):
        if mode == 'setup':
            kernel.prepare('one-owned-synthetic-recovery')
        else:
            kernel.advance(recovery_id, checkpoint)
    raise AssertionError('The selected durable reservation boundary was not reached')


class RecoveryPreimplementationIndependentTests(unittest.TestCase):
    def test_original300_fence_and_required_recovery_entrypoint(self):
        config = scalar_support.profile()
        config.update(targets=[16], worlds_per_cell=256,
            responses=['a', 'b'], patterns=[[0, 0], [0, 1], [1, 1], [2, 2]])
        config['budget'].update(max_compute_ms=3600000, attempt_compute_ms=300000,
            max_storage_bytes=4 * GIB, attempt_storage_bytes=256 * MIB, max_attempts=1)
        manifest = family_study.make_final_manifest(
            {**scalar_support.assigned(), 'primary_count': 2}, config)
        original = deepcopy(manifest)
        reservation = {'attempt_id': 'synthetic-old-failed', 'world_id': manifest['worlds'][0]['id'],
                       'compute_ms': 300000, 'storage_bytes': 256 * MIB}
        settlement = {'attempt_id': reservation['attempt_id'], 'compute_ms': 300226,
                      'storage_bytes': MIB, 'usage_known': True}
        historical = budget_state(manifest, [reservation], [settlement])
        self.assertEqual(300226, historical['charged_compute_ms'])
        self.assertIs(historical['overrun'], True)
        self.assertIs(historical['next_reservation_fits'], False)
        for compute in (300000, 600000):
            with self.subTest(new_reserved_compute_ms=compute), self.assertRaises(Invalid):
                budget_state(manifest, [reservation, {**reservation,
                    'attempt_id': 'synthetic-approved-retry', 'compute_ms': compute}], [settlement])
        self.assertEqual(original, manifest)
        self.assertIsNotNone(importlib.util.find_spec(MODULE),
            'Approved recovery owner absent; old fence verified,0 new recovery-flow coverage')
        owner = importlib.import_module(MODULE)
        self.assertEqual(['broker', 'authority_binding'], list(inspect.signature(owner.CalibrationRecovery).parameters))
        for name, expected in (('PROFILE', PROFILE), ('INPUT', INPUT), ('SOURCE', SOURCE),
                               ('AMENDMENT', AMENDMENT), ('RESULT', RESULT), ('GRANT', GRANT)):
            self.assertEqual(expected, getattr(owner, name))


class RecoveryKernelFixture:
    """Genuine inputs and tiny child bytes; only old overrun timing is invented."""
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.family = family_support.FamilyFixture()
        broker, token = self.family.broker, self.family.token
        estimate = {'world_time_rows': 3, 'observed_compute_ms': 10000,
            'observed_storage_bytes': 32 * MIB,
            'qualification': 'Tiny synthetic recovery fixture; no live-series timing or validity claim.'}
        cost = broker.call(token, 'add_source', data_class='development',
            body={'schema': 'development-study-cost-estimate/1', **estimate})
        profile = {'specifications': [self.family.args('unused')['specification']],
            'targets': [3], 'worlds_per_cell': 1, 'seed': 713,
            'mc_noncoverage': {'numerator': '1', 'denominator': '100'},
            'outer_noncoverage': {'numerator': '1', 'denominator': '20'},
            'responses': ['a', 'b'], 'patterns': [[0, 0], [0, 1], [1, 1], [2, 2]],
            'budget': {'max_compute_ms': 3600000, 'attempt_compute_ms': 300000,
                'max_storage_bytes': 4 * GIB, 'attempt_storage_bytes': 256 * MIB,
                'max_attempts': 1}, 'cost_estimate': {'source_ref': cost['id'], **estimate}}
        development = broker.call(token, 'prepare_family_study', key='recovery-kernel-development',
            plan_id=self.family.plan['id'], execution_id=self.family.execution['id'],
            diagnostics_id=self.family.diagnostics['id'], profile=profile)
        for _ in range(4):
            view = broker.call(token, 'advance_family_study', study_id=development['id'])
        assert view['status'] == 'COMPLETE', view
        self.study = broker.call(token, 'prepare_family_calibration',
            key='recovery-kernel-original-final', development_study_id=development['id'],
            time_rows=3, seed=714, budget={**profile['budget'],
                'max_compute_ms': 300000, 'max_storage_bytes': 256 * MIB},
            cost_estimate=profile['cost_estimate'],
            applicability={name: {'status': 'not_applicable', 'cohort_ids': [],
                'reason': 'Synthetic tiny recovery fixture; no actual applicability claim.'}
                for name in ('heavy_tail', 'overlap', 'common_shock')})
        assert len(self.study['body']['manifest']['worlds']) == 1024
        stopped = broker.call(token, 'inspect_family_calibration', calibration_id=self.study['id'])
        assert stopped['status'] == 'RESOURCE_STOP' and not stopped['attempt_artifact_ids']
        broker.call(token, 'continue_study', key='genuine-original-grant-before-failure',
            study_id=self.study['id'], expected_checkpoint=stopped['resource_checkpoint'],
            additional_compute_ms=3600000, additional_storage_bytes=4 * GIB,
            rationale='Continue this exact temporary synthetic inventory within its fixed aggregate authority.',
            expected_progress='Execute its first unchanged original world with full replay.',
            stop_reason='Stop at any failure or the next full-reservation resource boundary.')
        # Real tiny generation AND replay provide source-qualified output bytes.
        # A controlled parent clock then makes this an owned known-overrun failure.
        # This represents no observed live timeout and no accepted final world.
        clock = [0]
        actual = study_runs.execute_attempt
        def actual_tiny_then_synthetic_clock(*args, **kwargs):
            result = actual(*args, **kwargs)
            clock[0] = Fraction(300226, 1000)
            return result
        with patch.object(study_runs, 'time', types.SimpleNamespace(monotonic=lambda: clock[0])), \
                patch.object(study_runs, 'execute_attempt', side_effect=actual_tiny_then_synthetic_clock):
            self.original_view = broker.call(token, 'advance_family_calibration', calibration_id=self.study['id'])
        assert self.original_view['status'] == 'RESOURCE_STOP', self.original_view
        assert self.original_view['budget']['charged_compute_ms'] == 300226
        assert len(self.original_view['continuation_ids']) == 1
        self.failed = broker.call(token, 'get_artifact', artifact_id=self.original_view['attempt_artifact_ids'][0])
        assert self.failed['body']['outcome']['state'] == 'TECHNICAL_FAILURE'
        assert self.failed['body']['failure']['type'] == 'ResourceOverrun'
        self.output_bytes = {name: broker._read_blob_bytes(value['sha256'])
                             for name, value in self.failed['body']['output_blobs'].items()}
        self.generation = json.loads(self.output_bytes['generate/child-output.json'])
        self.result = self.generation['result']
        assert self.result == self.failed['body']['result']
        self.proofs = deepcopy(self.failed['body']['proofs'])
        assert len(self.proofs) == 2
        project = Path(__file__).resolve().parents[1]
        self.assessment_bytes = {name: (project / name).read_bytes()
                                 for name in self.study['body']['assessment_source_footprint']}
        assert {name: hashlib.sha256(raw).hexdigest() for name, raw in self.assessment_bytes.items()} \
            == self.study['body']['assessment_source_footprint']
        self.original_template = json.loads((project / 'docs/reviews/implementation-2026-10-25/'
            'calibration-resource-approval-2026-11-02.json').read_text(encoding='utf-8'))
        self.recovery_template = json.loads((project / 'docs/reviews/implementation-2026-10-25/'
            'calibration-recovery-approval-2026-11-03.json').read_text(encoding='utf-8'))
        self.backup = self.root / 'owned-failed-prefix-backup'
        assert broker.call(token, 'backup_bundle', destination=str(self.backup))['status'] == 'PASS'

    def close(self):
        self.family.close()
        self.temporary.cleanup()


class CalibrationRecoveryIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = RecoveryKernelFixture()
        cls.addClassCleanup(cls.baseline.close)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.directory = self.root / 'registry'
        original_broker = self.baseline.family.broker
        self.assertEqual('PASS', restore_bundle(self.baseline.backup, self.directory,
            original_broker.directory / 'operator.key')['status'])
        self.broker = Broker(self.directory)
        self.addCleanup(self.broker.close)
        self.token = self.broker.admin_token
        self.study = self.baseline.study
        self.failed = self.baseline.failed
        self.owner = importlib.import_module(MODULE)
        self.assessment_host = self.root / 'old-assessment-host'
        for name, raw in self.baseline.assessment_bytes.items():
            path = self.assessment_host / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.original_approval = self.root / 'synthetic-original-approval.json'
        original = deepcopy(self.baseline.original_template)
        original.update(source='SYNTHETIC_TEMPORARY_KERNEL_FIXTURE_NOT_LIVE_APPROVAL',
            scope='Exactly this owned tiny synthetic1024-world kernel fixture, not a real research approval.')
        self.original_approval.write_bytes(encoded(original))
        self.approval = self.root / 'synthetic-recovery-approval.json'
        self.approval_body = self.approval_for_current_history()
        self.approval.write_bytes(encoded(self.approval_body))
        self.bound = {'schema': 'calibration-recovery-authority-binding/1',
            'calibration_id': self.study['id'], 'registry_path': str(self.directory.resolve()),
            'assessment_host': str(self.assessment_host.resolve()),
            'approval_path': str(self.approval.resolve()), 'approval_sha256': file_hash(self.approval),
            'original_approval_path': str(self.original_approval.resolve()),
            'original_approval_sha256': file_hash(self.original_approval)}
        self.kernel = self.owner.CalibrationRecovery(self.broker, self.bound)
        self.serial = 0

    def original_view(self):
        return self.broker.call(self.token, 'inspect_family_calibration', calibration_id=self.study['id'])

    def approval_for_current_history(self):
        view = self.original_view()
        body = self.study['body']
        approval = deepcopy(self.baseline.recovery_template)
        approval.update(source='SYNTHETIC_TEMPORARY_KERNEL_FIXTURE_NOT_LIVE_APPROVAL',
            study_id=self.study['id'], terminal_checkpoint=view['resource_checkpoint'],
            failed_attempt_artifact_id=self.failed['id'], failed_attempt_id=self.failed['body']['attempt_id'],
            failed_world_id=self.failed['body']['world_id'], approved_exception=deepcopy(TERMS),
            original_approval={'path': str(self.original_approval.resolve()),
                               'sha256': file_hash(self.original_approval)})
        approval['fixed_identity'] = {'planned_worlds': 1024, 'verified_worlds_retained': 0,
            'failed_attempt_retained': True,
            'known_compute_ms_retained': view['budget']['charged_compute_ms'],
            'known_logical_bytes_retained': view['budget']['charged_storage_bytes'],
            'actual_grants_retained': len(view['continuation_ids']),
            'calculation_source_footprint': identity(body['source_footprint']),
            'request_hash': identity(body['request']), 'manifest_hash': identity(body['manifest']),
            'recipe_hash': body['manifest']['recipe_hash'], 'all_original_world_and_seed_ids_unchanged': True}
        return approval

    def artifacts(self, schema):
        return [self.broker._artifact(row[0]) for row in self.broker._db.execute(
            "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=? ORDER BY rowid", (schema,))]

    def events(self, action=None):
        events = [json.loads(row[0]) for row in self.broker._db.execute('SELECT envelope FROM events ORDER BY seq')]
        return [event for event in events if action is None or event['action'] == action]

    def setup_charge(self):
        return 2 * (sum(map(len, source_bundle().values())) +
                    sum(map(len, self.baseline.assessment_bytes.values())) +
                    self.approval.stat().st_size + self.original_approval.stat().st_size) + 3 * MIB

    def prepare(self):
        return self.kernel.prepare('one-owned-synthetic-recovery')

    def assert_study_unchanged(self):
        self.assertEqual(self.study, self.broker.call(self.token, 'get_artifact', artifact_id=self.study['id']))
        self.assertEqual(self.failed, self.broker.call(self.token, 'get_artifact', artifact_id=self.failed['id']))
        self.assertEqual('RESOURCE_STOP', self.original_view()['status'])
        self.assertEqual(1, len(self.original_view()['attempt_artifact_ids']))
        self.assertIs(self.original_view()['budget']['overrun'], True)

    def assert_no_new_attempt(self):
        self.assertEqual([], self.artifacts(RESULT))
        self.assertEqual([], self.events('calibration_recovery_reserved'))

    @contextmanager
    def transport(self, *, index=0, change=None, error=None, elapsed=Fraction(1, 100), revoke=None):
        """Synthetic transport/clock only; genuine owner inputs remain in force."""
        clock = [0]
        def synthetic(source, payload, manifest, world, cases, remaining, meter, outputs, **kwargs):
            self.assertEqual(self.study['body']['manifest'], manifest)
            self.assertEqual(300000, manifest['profile']['budget']['attempt_compute_ms'])
            self.assertEqual(self.study['body']['payload'], payload)
            self.assertEqual(self.study['body']['manifest']['worlds'][index], world)
            self.assertGreater(remaining(), 0)
            self.assertLessEqual(remaining(), 600)
            self.assertEqual(self.study['body']['source_footprint'],
                             {name: hashlib.sha256(raw).hexdigest() for name, raw in source.items()})
            self.assertEqual(self.study['body']['payload']['case_blob'],
                             {'sha256': hashlib.sha256(cases).hexdigest(), 'size': len(cases)})
            result, proofs = deepcopy(self.baseline.result), deepcopy(self.baseline.proofs)
            values = deepcopy(self.baseline.output_bytes)
            if index:
                # Later worlds are synthetic INFORMATION_GAP protocol fixtures,
                # not freshly computed numerical outcomes or replay evidence.
                components = [{'id': item['id'], 'truth': manifest['effects'][item['scenario']],
                    'state': 'INFORMATION_GAP', 'decision': None, 'covered': None}
                    for item in family_study.components(manifest, world)]
                result.update(world_id=world['id'],
                    outcome=family_study.outcome_record(manifest, world, components))
                result.update(status='INCOMPLETE', outcomes=deepcopy(components),
                              events=deepcopy(result['outcome']['events']))
                request = {'payload': payload, 'manifest': manifest, 'world': world,
                    'footprint': {name: hashlib.sha256(raw).hexdigest() for name, raw in source.items()},
                    'verify': None, 'stream_limit': study_runs.attempt_stream_limit(source, manifest, cases)}
                proofs[0]['request_hash'] = identity(request)
                proofs[1]['request_hash'] = identity({**request, 'verify': identity(result)})
                response = deepcopy(self.baseline.generation)
                response.update(result=result, request_hash=proofs[0]['request_hash'])
                values['generate/child-output.json'] = encoded(response)
                values['replay/child-output.json'] = encoded({**response,
                    'result': {'verified_result_hash': identity(result)},
                    'request_hash': proofs[1]['request_hash']})
            outputs.extend(values.items())
            meter['materialized_bytes'] += 1234  # Explicit synthetic host measurement.
            if revoke is not None:
                revoke()
            clock[0] += elapsed
            if error is not None:
                raise error
            if change is not None:
                change(result, proofs, outputs, meter)
            return result, proofs
        with patch.object(self.owner, 'time', types.SimpleNamespace(monotonic=lambda: clock[0])), \
                patch.object(self.owner, 'execute_attempt', side_effect=synthetic) as call:
            yield call

    def assert_fenced(self, amendment):
        view = self.kernel.inspect(amendment['id'])
        with self.transport() as transport:
            with self.assertRaises(ERRORS):
                self.kernel.advance(amendment['id'], view['recovery_checkpoint'])
            with self.assertRaises(ERRORS):
                self.kernel.continue_capacity(amendment['id'], view['recovery_checkpoint'])
        transport.assert_not_called()
        self.assert_study_unchanged()

    def test_prepare_preserves_original_and_commits_three_bounded_owned_custodies(self):
        self.assertEqual(BINDING_FIELDS, set(self.bound))
        before = self.original_view()
        expected_charge = self.setup_charge()
        original_resolver = FamilyCalibrationStudies._study_inputs
        with patch.object(FamilyCalibrationStudies, '_study_inputs', autospec=True,
                          side_effect=original_resolver) as recompute:
            amendment = self.prepare()
        self.assertTrue(recompute.called, 'Preparation silently skipped genuine input recomputation')
        self.assertEqual([1, 1, 1], [len(self.artifacts(schema)) for schema in (INPUT, SOURCE, AMENDMENT)])
        source = self.artifacts(SOURCE)[0]
        expected_new = {hashlib.sha256(raw).hexdigest() for raw in source_bundle().values()}
        expected_old = {hashlib.sha256(raw).hexdigest() for raw in self.baseline.assessment_bytes.values()}
        expected_old.update((file_hash(self.approval), file_hash(self.original_approval)))
        self.assertEqual(sorted(expected_new), source['blob_refs'])
        self.assertEqual(sorted(expected_old), amendment['blob_refs'])
        self.assertEqual({name: {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
                          for name, raw in source_bundle().items()}, source['body']['files'])
        self.assertEqual({name: hashlib.sha256(raw).hexdigest() for name, raw in source_bundle().items()},
                         source['body']['footprint'])
        self.assertEqual({name: {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
                          for name, raw in self.baseline.assessment_bytes.items()},
                         amendment['body']['assessment_source_files'])
        self.assertEqual(self.study['body']['assessment_source_footprint'],
                         amendment['body']['assessment_source_footprint'])
        self.assertEqual({'recovery': {'sha256': file_hash(self.approval), 'size': self.approval.stat().st_size},
                          'original': {'sha256': file_hash(self.original_approval),
                                       'size': self.original_approval.stat().st_size}},
                         amendment['body']['approval_blobs'])
        self.assertEqual([], self.artifacts(INPUT)[0].get('blob_refs', []))
        self.assertLessEqual(len(source['blob_refs']), 128)
        self.assertLessEqual(len(amendment['blob_refs']), 256)
        view = self.kernel.inspect(amendment['id'])
        self.assertEqual(self.study['id'], view['study_id'])
        self.assertEqual(amendment['id'], view['recovery_id'])
        self.assertEqual(before['resource_checkpoint'], view['original_checkpoint'])
        self.assertEqual('READY', view['status'])
        self.assertIs(view['historical_overrun'], True)
        self.assertIs(view['budget']['current_overrun'], False)
        self.assertIs(view['budget']['usage_uncertain'], False)
        self.assertEqual([], view['budget']['outstanding_attempts'])
        self.assertEqual(300226, view['budget']['charged_compute_ms'])
        self.assertEqual(before['budget']['charged_storage_bytes'] + expected_charge,
                         view['budget']['charged_storage_bytes'])
        self.assertEqual(expected_charge, view['budget']['setup_storage_bytes'])
        self.assertEqual(648000000, view['budget']['global_max_compute_ms'])
        self.assertEqual(107374182400, view['budget']['global_max_storage_bytes'])
        self.assertEqual(1, view['budget']['continuation_count'])
        self.assertEqual(before['attempt_artifact_ids'], view['attempt_artifact_ids'])
        self.assertEqual(before['continuation_ids'], view['continuation_ids'])
        self.assertEqual(self.failed['body']['world_id'], view['next_world_id'])
        self.assertIs(view['scientific_readiness'], False)
        self.assertIsNone(view['n_min'])
        self.assert_no_new_attempt()
        self.assert_study_unchanged()

    def test_exact_key_is_history_and_other_key_cannot_buy_another_amendment_or_setup(self):
        amendment = self.prepare()
        view = self.kernel.inspect(amendment['id'])
        count = len(self.events())
        self.assertEqual(amendment, self.prepare())
        with self.assertRaises(Conflict):
            self.kernel.prepare('different-key-same-old-study')
        self.assertEqual(count, len(self.events()))
        self.assertEqual(view, self.kernel.inspect(amendment['id']))
        self.assert_no_new_attempt()

    def test_fixed_binding_and_approval_terms_cannot_be_forged_as_caller_flags(self):
        for field in sorted(BINDING_FIELDS):
            with self.subTest(missing=field), self.assertRaises(ERRORS):
                self.owner.CalibrationRecovery(self.broker,
                    {key: value for key, value in self.bound.items() if key != field}).prepare('missing-' + field)
        for field, value in (('approved', True), ('attempt_compute_ms', 600001),
                             ('additional_attempts', 2), ('view', {}), ('profile', PROFILE)):
            with self.subTest(field=field), self.assertRaises(ERRORS):
                self.owner.CalibrationRecovery(self.broker, {**self.bound, field: value}).prepare('forged-' + field)
        for name, value in (('additional_attempts_for_named_failed_world', 2),
                            ('attempt_compute_ms_for_retry_and_remaining_original_worlds', 600001),
                            ('other_worlds_max_attempts', 2), ('aggregate_compute_ms', 648000001),
                            ('aggregate_logical_bytes', 107374182401), ('additional_grants_max', 180),
                            ('attempt_storage_bytes', True)):
            body = deepcopy(self.approval_body)
            body['approved_exception'][name] = value
            path = self.root / ('forged-' + name + '.json')
            path.write_bytes(encoded(body))
            binding = {**self.bound, 'approval_path': str(path), 'approval_sha256': file_hash(path)}
            with self.subTest(term=name), self.assertRaises(ERRORS):
                self.owner.CalibrationRecovery(self.broker, binding).prepare('forged-term-' + name)
        self.assertEqual([], self.artifacts(INPUT))
        self.assert_no_new_attempt()

    def test_wrong_identity_or_pinned_authority_cannot_begin_setup(self):
        for name, value in (('study_id', 'f' * 64), ('terminal_checkpoint', 'e' * 64),
                            ('failed_world_id', self.study['body']['manifest']['worlds'][1]['id']),
                            ('failed_attempt_artifact_id', self.study['id']),
                            ('failed_attempt_id', 'not-the-original-attempt')):
            body = {**deepcopy(self.approval_body), name: value}
            path = self.root / ('wrong-' + name + '.json')
            path.write_bytes(encoded(body))
            binding = {**self.bound, 'approval_path': str(path), 'approval_sha256': file_hash(path)}
            with self.subTest(field=name), self.assertRaises(ERRORS):
                self.owner.CalibrationRecovery(self.broker, binding).prepare('wrong-' + name)
        for changes in ({'approval_sha256': '0' * 64}, {'original_approval_sha256': '0' * 64},
                        {'approval_sha256': True}, {'approval_path': 'relative-approval.json'},
                        {'registry_path': str(self.root)}, {'assessment_host': str(self.root / 'missing-host')}):
            with self.subTest(changes=changes), self.assertRaises(ERRORS):
                self.owner.CalibrationRecovery(self.broker, {**self.bound, **changes}).prepare('wrong-binding')
        self.assertEqual([], self.artifacts(INPUT))
        self.assert_no_new_attempt()

    def test_setup_reservation_precedes_staging_and_failure_cannot_restart_under_any_key(self):
        expected = self.setup_charge()
        original_stage = self.broker._stage_blob_bytes
        calls = []
        def fail_second(raw):
            self.assertEqual(1, len(self.artifacts(INPUT)))
            self.assertEqual(1, len(self.events('calibration_recovery_setup_reserved')))
            calls.append(len(raw))
            if len(calls) == 2:
                raise RuntimeError('Synthetic setup staging failure after one published blob')
            return original_stage(raw)
        with patch.object(self.broker, '_stage_blob_bytes', side_effect=fail_second), self.assertRaises(RuntimeError):
            self.prepare()
        self.assertEqual(2, len(calls))
        self.assertEqual([1, 0, 0], [len(self.artifacts(schema)) for schema in (INPUT, SOURCE, AMENDMENT)])
        reserved = self.events('calibration_recovery_setup_reserved')
        self.assertEqual(1, len(reserved))
        failure = self.kernel.inspect(self.artifacts(INPUT)[0]['id'])
        self.assertEqual(expected, failure['budget']['setup_storage_bytes'])
        self.assertEqual(300226, failure['budget']['charged_compute_ms'])
        self.assertEqual(self.original_view()['budget']['charged_storage_bytes'] + expected,
                         failure['budget']['charged_storage_bytes'])
        with patch.object(self.broker, '_stage_blob_bytes', side_effect=AssertionError('Failed setup restarted')):
            for key in ('one-owned-synthetic-recovery', 'different-key-after-failure'):
                with self.subTest(key=key), self.assertRaises(ERRORS):
                    self.kernel.prepare(key)
        self.assert_no_new_attempt()
        self.assert_study_unchanged()

    def test_setup_cannot_publish_source_or_amendment_when_final_transaction_fails(self):
        original_event = self.broker._event
        def fail_amendment(actor, action, **details):
            if action == 'calibration_recovery_amended':
                raise RuntimeError('Synthetic amendment-commit interruption')
            return original_event(actor, action, **details)
        with patch.object(self.broker, '_event', side_effect=fail_amendment), self.assertRaises(RuntimeError):
            self.prepare()
        self.assertEqual([1, 0, 0], [len(self.artifacts(schema)) for schema in (INPUT, SOURCE, AMENDMENT)])
        self.assertEqual(1, len(self.events('calibration_recovery_setup_reserved')))
        self.assertEqual([], self.events('calibration_recovery_amended'))
        # Agreed setup failures retain their checked partial custody and full
        # charge after rolling back SOURCE+AMENDMENT. An empty event list would
        # incorrectly require the controller to discard this failure evidence.
        settlements = self.events('calibration_recovery_setup_settled')
        self.assertEqual(1, len(settlements))
        details = settlements[0]['details']
        self.assertIs(details['complete'], False)
        self.assertIs(details['usage_known'], False)
        self.assertEqual({'type': 'RuntimeError', 'message': 'Synthetic amendment-commit interruption'},
                         details['failure'])
        self.assertEqual([], details['unavailable_blobs'])
        self.assertEqual(self.study['id'], details['study_id'])
        capsule = self.artifacts(INPUT)[0]
        self.assertEqual(capsule['id'], details['input_id'])
        self.assertEqual([], capsule.get('blob_refs', []))
        self.assertTrue(details['partial_blobs'])
        checked = set()
        for descriptor in details['partial_blobs']:
            self.assertEqual({'sha256', 'size'}, set(descriptor))
            if descriptor['sha256'] in checked:
                continue
            raw = self.broker._read_blob_bytes(descriptor['sha256'])
            self.assertEqual(descriptor, {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)})
            checked.add(descriptor['sha256'])
        view = self.kernel.inspect(capsule['id'])
        self.assertEqual(self.setup_charge(), view['budget']['setup_storage_bytes'])
        original = self.original_view()
        self.assertEqual(original['budget']['charged_storage_bytes'] + self.setup_charge(),
                         view['budget']['charged_storage_bytes'])
        self.assertEqual(300226, view['budget']['charged_compute_ms'])
        self.assertEqual(original['budget']['attempts_per_world'], view['budget']['attempts_per_world'])
        self.assertIs(view['budget']['usage_uncertain'], True)
        self.assertNotEqual('READY', view['status'])
        self.assertIsNone(view['next_world_id'])
        self.assertIs(view['scientific_readiness'], False)
        with patch.object(self.broker, '_stage_blob_bytes', side_effect=AssertionError('Failed setup restarted')):
            for key in ('one-owned-synthetic-recovery', 'another-key-cannot-forget-setup'):
                with self.subTest(key=key), self.assertRaises(ERRORS):
                    self.kernel.prepare(key)
        with self.transport() as transport:
            with self.assertRaises(ERRORS):
                self.kernel.advance(capsule['id'], view['recovery_checkpoint'])
            with self.assertRaises(ERRORS):
                self.kernel.continue_capacity(capsule['id'], view['recovery_checkpoint'])
        transport.assert_not_called()
        self.assert_no_new_attempt()

    def test_actual_tiny_recovery_runs_fresh_generation_and_separate_replay_with_original_bytes(self):
        """Genuine small new-owner execution; no transport or clock substitution."""
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        self.assertEqual(300000, self.study['body']['manifest']['profile']['budget']['attempt_compute_ms'])
        after = self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, len(self.artifacts(RESULT)))
        saved = self.artifacts(RESULT)[0]
        body = saved['body']
        self.assertEqual(self.failed['body']['world_id'], body['world_id'])
        self.assertEqual(self.baseline.generation['result'], body['result'])
        self.assertEqual(2, len(body['proofs']))
        self.assertIsNone(body['failure'])
        self.assertEqual([], body['resource_violations'])
        self.assertIsNone(body['dependency_failure'])
        self.assertIs(body['settlement']['usage_known'], True)
        self.assertGreater(body['settlement']['compute_ms'], 0)
        self.assertLessEqual(body['settlement']['compute_ms'], 600000)
        self.assertEqual(self.failed['body']['outcome']['world_id'], body['outcome']['world_id'])
        self.assertIn(body['outcome']['state'], ('VERIFIED', 'INFORMATION_GAP'))
        response = json.loads(self.broker._read_blob_bytes(
            body['output_blobs']['generate/child-output.json']['sha256']))
        self.assertEqual(self.baseline.generation['result'], response['result'])
        self.assertEqual(self.baseline.generation['request_hash'], response['request_hash'])
        self.assertEqual(self.baseline.generation['stream_blob'], response['stream_blob'])
        for name in ('generate/stream.jsonl.gz', 'replay/expected-stream.jsonl.gz'):
            self.assertEqual(self.baseline.output_bytes['generate/stream.jsonl.gz'],
                self.broker._read_blob_bytes(body['output_blobs'][name]['sha256']))
        self.assertEqual(self.baseline.proofs[0]['request_hash'], body['proofs'][0]['request_hash'])
        self.assertEqual(self.baseline.proofs[1]['request_hash'], body['proofs'][1]['request_hash'])
        reserved = self.events('calibration_recovery_reserved')
        self.assertEqual(1, len(reserved))
        # The public method accepts no amount; its fixed parent envelope is
        # derived by the owner. Its reservation must retain600000ms/256MiB.
        def contains_envelope(value):
            if isinstance(value, dict):
                if value.get('compute_ms') == 600000 and value.get('storage_bytes') == 256 * MIB:
                    return True
                return any(contains_envelope(child) for child in value.values())
            if isinstance(value, list):
                return any(contains_envelope(child) for child in value)
            return False
        self.assertTrue(contains_envelope(reserved[0]['details']))
        self.assertEqual(2, after['budget']['attempts_per_world'][body['world_id']])
        self.assertEqual(before['attempt_artifact_ids'] + [saved['id']], after['attempt_artifact_ids'])
        self.assertEqual(before['budget']['charged_compute_ms'] + body['settlement']['compute_ms'],
                         after['budget']['charged_compute_ms'])
        self.assertEqual(before['budget']['charged_storage_bytes'] + body['settlement']['storage_bytes'],
                         after['budget']['charged_storage_bytes'])
        self.assertEqual(self.study['body']['manifest']['worlds'][1]['id'], after['next_world_id'])
        with self.assertRaises(Conflict):
            self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, len(self.artifacts(RESULT)))
        self.assert_study_unchanged()

    def test_named_retry_keeps_inputs_full_parent_envelope_and_full_denominators(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        with self.transport() as transport:
            after = self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, transport.call_count)
        self.assertEqual(before['attempt_artifact_ids'], after['attempt_artifact_ids'][:-1])
        self.assertEqual(2, after['budget']['attempts_per_world'][self.failed['body']['world_id']])
        self.assertEqual(1, len(self.artifacts(RESULT)))
        saved = self.artifacts(RESULT)[0]
        self.assertEqual(self.failed['body']['world_id'], saved['body']['world_id'])
        self.assertEqual(self.baseline.result, saved['body']['result'])
        self.assertEqual(2, len(saved['body']['proofs']))
        self.assertEqual(1024, after['summary']['planned_worlds'])
        self.assertEqual(1, after['summary']['recorded_worlds'])
        self.assertTrue(all(cohort['planned'] == 256 for cohort in after['summary']['count_assessment']['cohorts']))
        self.assertIs(after['scientific_readiness'], False)
        self.assertIsNone(after['n_min'])
        self.assertEqual('READY', after['status'])
        self.assertEqual(self.study['body']['manifest']['worlds'][1]['id'], after['next_world_id'])
        self.assert_study_unchanged()

    def test_stale_checkpoint_cannot_reserve_or_settle_a_second_retry(self):
        amendment = self.prepare()
        initial = self.kernel.inspect(amendment['id'])
        with self.transport() as transport:
            current = self.kernel.advance(amendment['id'], initial['recovery_checkpoint'])
            with self.assertRaises(Conflict):
                self.kernel.advance(amendment['id'], initial['recovery_checkpoint'])
        self.assertEqual(1, transport.call_count)
        self.assertEqual(current, self.kernel.inspect(amendment['id']))
        self.assertEqual(2, current['budget']['attempts_per_world'][self.failed['body']['world_id']])
        self.assertEqual(1, len(self.events('calibration_recovery_reserved')))
        self.assertEqual(1, len(self.events('calibration_recovery_settled')))

    def test_new_failure_retains_first_exception_and_observed_overrun_without_retry(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        with self.transport(error=RuntimeError('Retained first synthetic transport exception'),
                            elapsed=Fraction(600001, 1000)) as transport:
            self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, transport.call_count)
        saved = self.artifacts(RESULT)[0]
        self.assertEqual('RuntimeError', saved['body']['failure']['type'])
        self.assertIn('Retained first synthetic transport exception', saved['body']['failure']['message'])
        self.assertTrue(saved['body']['resource_violations'])
        view = self.kernel.inspect(amendment['id'])
        self.assertGreaterEqual(view['budget']['charged_compute_ms'], 300226 + 600001)
        self.assertIs(view['budget']['current_overrun'], True)
        self.assertTrue(saved['body']['output_blobs'])
        self.assert_fenced(amendment)

    def test_full_result_drift_with_unchanged_outcome_is_quarantined(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        def drift(result, proofs, outputs, meter):
            result['input_hash'] = 'f' * 64
            for index, (name, raw) in enumerate(outputs):
                if name == 'generate/child-output.json':
                    response = json.loads(raw)
                    response['result'] = deepcopy(result)
                    outputs[index] = (name, encoded(response))
        with self.transport(change=drift) as transport:
            self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, transport.call_count)
        self.assertEqual('TECHNICAL_FAILURE', self.artifacts(RESULT)[0]['body']['outcome']['state'])
        self.assert_fenced(amendment)

    def test_encoded_generation_stream_drift_cannot_match_old_acknowledgement(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        def drift(result, proofs, outputs, meter):
            for index, (name, raw) in enumerate(outputs):
                if name == 'generate/stream.jsonl.gz':
                    outputs[index] = (name, raw + b'changed-encoded-stream')
        with self.transport(change=drift) as transport:
            self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, transport.call_count)
        self.assertEqual('TECHNICAL_FAILURE', self.artifacts(RESULT)[0]['body']['outcome']['state'])
        self.assert_fenced(amendment)

    def test_one_generation_proof_is_not_a_complete_separate_replay(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        with self.transport(change=lambda result, proofs, outputs, meter: proofs.pop()) as transport:
            self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, transport.call_count)
        self.assertEqual('TECHNICAL_FAILURE', self.artifacts(RESULT)[0]['body']['outcome']['state'])
        self.assert_fenced(amendment)

    def test_old_assessment_corruption_cannot_create_amendment(self):
        name = sorted(self.baseline.assessment_bytes)[0]
        path = self.assessment_host / name
        original = path.read_bytes()
        path.write_bytes(original + b'\n# Owned cloned source corruption\n')
        with self.assertRaises(ERRORS):
            self.prepare()
        self.assertEqual([], self.artifacts(AMENDMENT))
        self.assert_no_new_attempt()

    def test_old_failed_generation_acknowledgement_corruption_cannot_authorize_recovery(self):
        descriptor = self.failed['body']['output_blobs']['generate/child-output.json']
        path = self.broker._blob_path(descriptor['sha256'])
        self.assertTrue(path.resolve().is_relative_to(self.directory.resolve()))
        path.write_bytes(b'Corrupted retained acknowledgement in owned clone only.\n')
        with self.assertRaises(ERRORS):
            self.prepare()
        self.assertEqual([], self.artifacts(AMENDMENT))
        self.assert_no_new_attempt()

    def test_required_owned_case_blob_corruption_is_not_hidden_by_source_custody(self):
        descriptor = self.study['body']['payload']['case_blob']
        path = self.broker._blob_path(descriptor['sha256'])
        self.assertTrue(path.resolve().is_relative_to(self.directory.resolve()))
        path.write_bytes(b'Owned cloned case-byte corruption, not a scientific input.\n')
        with self.assertRaises(ERRORS):
            self.prepare()
        self.assertEqual([], self.artifacts(AMENDMENT))
        self.assert_no_new_attempt()

    def revoke(self, dependency):
        evidence = self.broker.call(self.token, 'add_source', data_class='development',
            body={'synthetic_fixture': 'Retained technical defect evidence only'})
        return self.broker.call(self.token, 'revoke_dependency',
            key='recovery-test-revocation-' + dependency, dependency_id=dependency,
            reason='Synthetic test revocation, not scientific falsification.', evidence_refs=[evidence['id']])

    def test_revoked_amendment_stops_use_but_exact_key_retains_immutable_history(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        self.revoke(amendment['id'])
        self.assertEqual(amendment, self.prepare())
        with self.transport() as transport:
            with self.assertRaises(ERRORS):
                self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
            with self.assertRaises(ERRORS):
                self.kernel.continue_capacity(amendment['id'], before['recovery_checkpoint'])
        transport.assert_not_called()
        self.assert_no_new_attempt()

    def test_revoked_new_source_propagates_through_typed_amendment_binding(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        self.revoke(self.artifacts(SOURCE)[0]['id'])
        status = self.broker.call(self.token, 'inspect_dependency_use', artifact_id=amendment['id'])
        self.assertEqual('INVALIDATED_BY_DEPENDENCY', status['status'])
        with self.transport() as transport, self.assertRaises(ERRORS):
            self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        transport.assert_not_called()
        self.assert_no_new_attempt()

    def test_midwork_revocation_keeps_output_charge_and_separate_dependency_failure(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        with self.transport(revoke=lambda: self.revoke(amendment['id'])) as transport:
            self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, transport.call_count)
        saved = self.artifacts(RESULT)[0]
        self.assertEqual('TECHNICAL_FAILURE', saved['body']['outcome']['state'])
        self.assertEqual('Denied', saved['body']['dependency_failure']['type'])
        self.assertEqual([], saved['body']['resource_violations'])
        self.assertTrue(saved['body']['output_blobs'])
        self.assertGreater(saved['body']['settlement']['storage_bytes'], MIB)
        with self.transport() as transport, self.assertRaises(ERRORS):
            self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        transport.assert_not_called()

    def run_hard_crash(self, mode, amendment=None, checkpoint=None):
        binding_file = self.root / ('hard-crash-' + mode + '-binding.json')
        binding_file.write_bytes(encoded(self.bound))
        self.broker.close()
        tests = str(Path(__file__).resolve().parent)
        project = str(Path(__file__).resolve().parents[1])
        code = ('import sys;sys.path[:0]=[sys.argv[1],sys.argv[2]];'
            'from test_calibration_recovery_independent import crash_after_committed_reservation;'
            'crash_after_committed_reservation(sys.argv[3],sys.argv[4],'
            'None if sys.argv[5]=="-" else sys.argv[5],None if sys.argv[6]=="-" else sys.argv[6])')
        result = subprocess.run([sys.executable, '-I', '-B', '-c', code, tests, project,
            str(binding_file), mode, amendment['id'] if amendment else '-', checkpoint or '-'],
            cwd=project, capture_output=True, timeout=60)
        self.assertEqual(91, result.returncode, result.stderr.decode(errors='replace'))
        self.broker = Broker(self.directory)
        self.addCleanup(self.broker.close)
        self.token = self.broker.admin_token
        self.kernel = self.owner.CalibrationRecovery(self.broker, self.bound)

    def test_hard_setup_crash_preserves_full_reservation_and_blocks_every_key_after_restart(self):
        expected = self.setup_charge()
        before = self.original_view()['budget']['charged_storage_bytes']
        self.run_hard_crash('setup')
        self.assertEqual([1, 0, 0], [len(self.artifacts(schema)) for schema in (INPUT, SOURCE, AMENDMENT)])
        input_id = self.artifacts(INPUT)[0]['id']
        self.kernel.recover_incomplete()
        first = self.kernel.inspect(input_id)
        self.kernel.recover_incomplete()
        self.assertEqual(first, self.kernel.inspect(input_id))
        self.assertEqual(expected, first['budget']['setup_storage_bytes'])
        self.assertEqual(before + expected, first['budget']['charged_storage_bytes'])
        self.assertEqual(300226, first['budget']['charged_compute_ms'])
        self.assertIs(first['budget']['usage_uncertain'], True)
        self.assertEqual({self.failed['body']['world_id']: 1}, first['budget']['attempts_per_world'])
        with patch.object(self.broker, '_stage_blob_bytes', side_effect=AssertionError('Crash setup restarted')):
            for key in ('one-owned-synthetic-recovery', 'new-key-after-hard-crash'):
                with self.subTest(key=key), self.assertRaises(ERRORS):
                    self.kernel.prepare(key)
        self.assert_no_new_attempt()

    def test_hard_attempt_crash_charges_full_reservation_spends_retry_and_never_auto_executes(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        self.run_hard_crash('attempt', amendment, before['recovery_checkpoint'])
        with self.transport() as transport:
            self.kernel.recover_incomplete()
            first = self.kernel.inspect(amendment['id'])
            self.kernel.recover_incomplete()
            self.assertEqual(first, self.kernel.inspect(amendment['id']))
        transport.assert_not_called()
        self.assertEqual(300226 + 600000, first['budget']['charged_compute_ms'])
        self.assertEqual(before['budget']['charged_storage_bytes'] + 256 * MIB,
                         first['budget']['charged_storage_bytes'])
        self.assertEqual(2, first['budget']['attempts_per_world'][self.failed['body']['world_id']])
        self.assertIs(first['budget']['usage_uncertain'], True)
        self.assert_fenced(amendment)

    def test_cache_free_full_restore_keeps_complete_custody_accounting_and_old_history(self):
        amendment = self.prepare()
        expected = self.kernel.inspect(amendment['id'])
        backup, restored_path = self.root / 'amended-backup', self.root / 'amended-restore'
        self.assertEqual('PASS', self.broker.call(self.token, 'backup_bundle', destination=str(backup))['status'])
        self.assertEqual('PASS', restore_bundle(backup, restored_path,
            self.directory / 'operator.key')['status'])
        restored = Broker(restored_path)
        try:
            binding = {**self.bound, 'registry_path': str(restored_path.resolve())}
            reader = self.owner.CalibrationRecovery(restored, binding)
            original_read = Path.read_bytes
            def no_external_assessment(path):
                if path.resolve().is_relative_to(self.assessment_host.resolve()):
                    raise FileNotFoundError('External old assessment host unavailable in restore fixture')
                return original_read(path)
            with patch.object(Path, 'read_bytes', no_external_assessment):
                actual = reader.inspect(amendment['id'])
            for name in ('study_id', 'recovery_id', 'recovery_checkpoint', 'original_checkpoint',
                         'historical_overrun', 'budget', 'attempt_artifact_ids', 'continuation_ids', 'summary'):
                self.assertEqual(expected[name], actual[name], name)
            for artifact in [self.study, self.failed, *self.artifacts(INPUT),
                             *self.artifacts(SOURCE), amendment]:
                self.assertEqual(artifact, restored.call(restored.admin_token, 'get_artifact', artifact_id=artifact['id']))
                for blob in artifact.get('blob_refs', []):
                    self.assertEqual(self.broker._read_blob_bytes(blob), restored._read_blob_bytes(blob))
            self.assertEqual('PASS', restored.call(restored.admin_token, 'verify')['status'])
            with self.transport() as transport:
                with self.assertRaises(ERRORS):
                    reader.advance(amendment['id'], actual['recovery_checkpoint'])
                with self.assertRaises(ERRORS):
                    reader.continue_capacity(amendment['id'], actual['recovery_checkpoint'])
                with self.assertRaises(ERRORS):
                    reader.prepare('new-key-cannot-activate-restored-copy')
            transport.assert_not_called()
        finally:
            restored.close()

    def test_valid_information_gap_completes_once_and_real_grant_keeps_old_grant_and_all_fees(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        original_grants = before['continuation_ids']
        self.assertEqual(1, len(original_grants))
        for index in range(5):
            before_world = self.kernel.inspect(amendment['id'])
            self.assertEqual('READY', before_world['status'])
            # Rounded elapsed is600000ms while the completion check still sees
            # a positive deadline; this is an explicit host clock fixture.
            with self.transport(index=index, elapsed=Fraction(5999999, 10000)) as transport:
                stopped = self.kernel.advance(amendment['id'], before_world['recovery_checkpoint'])
            self.assertEqual(1, transport.call_count)
            self.assertEqual(index + 1, stopped['summary']['recorded_worlds'])
            if index:
                latest = self.artifacts(RESULT)[-1]
                self.assertEqual('INFORMATION_GAP', latest['body']['outcome']['state'])
                self.assertEqual(1, stopped['budget']['attempts_per_world'][latest['body']['world_id']])
        self.assertEqual('RESOURCE_STOP', stopped['status'])
        self.assertEqual(300226 + 5 * 600000, stopped['budget']['charged_compute_ms'])
        self.assertIs(stopped['budget']['next_reservation_fits'], False)
        self.assertIs(stopped['budget']['current_overrun'], False)
        with self.transport() as transport:
            grant = self.kernel.continue_capacity(amendment['id'], stopped['recovery_checkpoint'])
        transport.assert_not_called()
        after = self.kernel.inspect(amendment['id'])
        self.assertEqual(GRANT, grant['body']['schema'])
        self.assertEqual(original_grants + [grant['id']], after['continuation_ids'])
        self.assertEqual(2, after['budget']['continuation_count'])
        self.assertEqual(stopped['budget']['charged_compute_ms'], after['budget']['charged_compute_ms'])
        self.assertEqual(stopped['budget']['charged_storage_bytes'] + MIB,
                         after['budget']['charged_storage_bytes'])
        self.assertEqual(stopped['budget']['max_compute_ms'] + 3600000, after['budget']['max_compute_ms'])
        self.assertEqual(stopped['budget']['max_storage_bytes'] + 4 * GIB, after['budget']['max_storage_bytes'])
        self.assertEqual('READY', after['status'])
        try:
            historical = self.kernel.continue_capacity(amendment['id'], stopped['recovery_checkpoint'])
        except Conflict:
            pass  # A stale rejection is also safe; neither path may allocate again.
        else:
            self.assertEqual(grant, historical)
        self.assertEqual(after, self.kernel.inspect(amendment['id']))
        self.assertEqual(1, len(self.artifacts(GRANT)))
        self.assertEqual(1, len(self.events('calibration_recovery_continued')))
        self.assert_study_unchanged()

    def append_original_fault(self, *, known=True, settled=True, orphan=False, compute=1):
        """Explicit synthetic unsafe old-prefix metadata, never positive admission."""
        manifest = self.study['body']['manifest']
        world = manifest['worlds'][1]
        attempt = 'synthetic-original-prefix-fault'
        grant = self.original_view()['continuation_ids'][-1]
        reservation = {'attempt_id': attempt, 'world_id': world['id'],
                       'compute_ms': 300000, 'storage_bytes': 256 * MIB}
        settlement = {'attempt_id': attempt, 'compute_ms': compute,
                      'storage_bytes': MIB, 'usage_known': known}
        outcome = family_study.outcome_record(manifest, world, failed=True)
        with self.broker._transaction():
            self.broker._event('controller', 'information_study_reserved',
                               study_id=self.study['id'], reservation=reservation)
            self.broker._event('controller', 'bound_computation_started', attempt_id=attempt,
                kind='information_study', input_ref=self.study['body']['request']['development_study_id'],
                retained_input_id=self.study['id'])
            if settled:
                artifact = self.broker._save_artifact({'version': 'local-artifact/1',
                    'creator': 'controller', 'origin': 'controller', 'data_class': 'operations',
                    'source_refs': sorted([self.study['id'], grant]),
                    'exposure': sorted(set(self.study['exposure']) | {self.study['id'], grant}),
                    'blob_refs': [], 'authority': FamilyCalibrationStudies._study_authority,
                    'body': {'schema': 'family-calibration-attempt/1', 'created_at': self.broker._now(),
                        'study_id': self.study['id'], 'continuation_id': grant, 'attempt_id': attempt,
                        'world_id': world['id'], 'outcome': outcome, 'result': None, 'proofs': [],
                        'output_blobs': {}, 'settlement': settlement,
                        'failure': {'type': 'SyntheticPrefixFault', 'message': 'Negative metadata fixture only'},
                        'scientific_readiness': False}})
                FamilyCalibrationStudies(self.broker)._settle_study(
                    self.study, attempt, settlement, outcome, artifact['id'], orphan=orphan)
        self.approval_body = self.approval_for_current_history()
        self.approval.write_bytes(encoded(self.approval_body))
        self.bound['approval_sha256'] = file_hash(self.approval)
        self.kernel = self.owner.CalibrationRecovery(self.broker, self.bound)

    def test_unknown_original_usage_is_not_covered_by_named_known_overrun_exception(self):
        self.append_original_fault(known=False)
        self.assertIs(self.original_view()['budget']['usage_uncertain'], True)
        with self.assertRaises(ERRORS):
            self.prepare()
        self.assertEqual([], self.artifacts(AMENDMENT))
        self.assert_no_new_attempt()

    def test_original_orphan_is_not_covered_by_named_known_overrun_exception(self):
        self.append_original_fault(known=False, orphan=True)
        self.assertEqual('ORPHAN_UNCERTAIN', self.original_view()['status'])
        with self.assertRaises(ERRORS):
            self.prepare()
        self.assertEqual([], self.artifacts(AMENDMENT))
        self.assert_no_new_attempt()

    def test_original_outstanding_attempt_cannot_be_replaced_with_recovery(self):
        self.append_original_fault(settled=False)
        self.assertEqual(['synthetic-original-prefix-fault'],
                         self.original_view()['budget']['outstanding_attempts'])
        with self.assertRaises(ERRORS):
            self.prepare()
        self.assertEqual([], self.artifacts(AMENDMENT))
        self.assert_no_new_attempt()

    def test_other_original_overrun_is_not_forgiven_by_matching_approval_prefix(self):
        self.append_original_fault(compute=300001)
        self.assertEqual(300226 + 300001, self.original_view()['budget']['charged_compute_ms'])
        with self.assertRaises(ERRORS):
            self.prepare()
        self.assertEqual([], self.artifacts(AMENDMENT))
        self.assert_no_new_attempt()

    def test_loaded_controller_disk_mismatch_is_fail_closed_without_workspace_edit(self):
        original_read = Path.read_bytes
        target = Path(self.owner.__file__).resolve()
        def different_loaded_file(path):
            raw = original_read(path)
            return raw + b'\n# Simulated disk-only mismatch; real workspace bytes unchanged.\n' \
                if path.resolve() == target else raw
        with patch.object(Path, 'read_bytes', different_loaded_file), self.assertRaises(ERRORS):
            self.prepare()
        self.assertEqual([], self.artifacts(AMENDMENT))
        self.assert_no_new_attempt()

    def test_reconcile_cannot_orphan_a_live_owned_attempt(self):
        amendment = self.prepare()
        before = self.kernel.inspect(amendment['id'])
        def reconcile_inside_live_transport():
            live = self.kernel.inspect(amendment['id'])
            self.assertEqual(1, len(live['budget']['outstanding_attempts']))
            for controller in (self.kernel, self.owner.CalibrationRecovery(self.broker, self.bound)):
                try:
                    controller.recover_incomplete()
                except ERRORS:
                    pass  # Explicit refusal or an unchanged live prefix is safe.
                current = self.kernel.inspect(amendment['id'])
                self.assertEqual(live['budget']['outstanding_attempts'], current['budget']['outstanding_attempts'])
                self.assertIs(current['budget']['usage_uncertain'], False)
                self.assertEqual([], self.events('calibration_recovery_settled'))
        with self.transport(revoke=reconcile_inside_live_transport) as transport:
            after = self.kernel.advance(amendment['id'], before['recovery_checkpoint'])
        self.assertEqual(1, transport.call_count)
        self.assertEqual([], after['budget']['outstanding_attempts'])
        self.assertIs(after['budget']['usage_uncertain'], False)
        self.assertEqual('READY', after['status'])


if __name__ == '__main__':
    unittest.main()
