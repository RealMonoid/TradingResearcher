"""Independent native-final INPUT controls, not final execution qualification.

The shared fixture uses genuine normalization/certification/compile owners,
then explicitly substitutes qualification membership and tiny development
numerical transport. No final numerical world is executed or admitted here.
"""
from contextlib import closing
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

import test_native_study_independent as native_support
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher import native_study_runs, study_runs
from trading_researcher.calibration_runs import CalibrationStudies
from trading_researcher.codec import canonical, digest
from trading_researcher.native_qualification import NativeQualifications
from trading_researcher import native_qualification as qualification_owner
from trading_researcher.native_runtime import NativeRuntimes
from trading_researcher.storage import restore_bundle


INPUT = 'native-family-calibration-input/1'
RESULT = 'native-family-calibration-attempt/1'
MIB = 1048576
ERRORS = (Invalid, Conflict, Denied)
PROCESS_POLICY = {'schema': 'native-study-process-control/1',
                  'library_threads': 1, 'priority': 'BELOW_NORMAL'}


def hashes(source):
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in source.items()}


class NativeCalibrationPublicBoundaryIndependentTests(unittest.TestCase):
    def test_public_prepare_dispatches_owned_request_validation(self):
        with tempfile.TemporaryDirectory(prefix='trf-native-final-api-') as temporary:
            with closing(Broker(Path(temporary) / 'registry')) as broker:
                with self.assertRaises(Invalid):
                    broker.call(broker.admin_token, 'prepare_native_family_calibration')

    def test_public_advance_is_denied_before_inputs_cache_child_or_reservation(self):
        with tempfile.TemporaryDirectory(prefix='trf-native-final-boundary-') as temporary:
            with closing(Broker(Path(temporary) / 'registry')) as broker:
                before = list(broker._db.execute('SELECT seq,hash FROM events'))
                with patch.object(study_runs, 'execute_attempt', side_effect=AssertionError('Final world executed')), \
                        patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Runtime materialized')):
                    with self.assertRaises(Denied):
                        broker.call(broker.admin_token, 'advance_native_family_calibration',
                                    calibration_id='1' * 64)
                self.assertEqual(list(broker._db.execute('SELECT seq,hash FROM events')), before)


class NativeCalibrationInputsIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Composition: no inherited native-development test methods. Exactly
        # one genuine base chain, then four explicitly synthetic scalar worlds.
        native_support.NativeStudyIndependentTests.setUpClass()
        cls.addClassCleanup(native_support.NativeStudyIndependentTests.doClassCleanups)
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-final-input-base-')
        cls.addClassCleanup(temporary.cleanup)
        cls.base_root = Path(temporary.name)
        builder = native_support.NativeStudyIndependentTests('runTest')
        builder.setUp()
        try:
            args = builder.args('native-final-input-development', 'family', native=False,
                                budget={'max_compute_ms': 10000}, seed=713)
            cls.development = builder.op('prepare_family_study', **args)
            assert len(cls.development['body']['manifest']['worlds']) == 4
            stopped = builder.op('advance_family_study', study_id=cls.development['id'])
            assert stopped['status'] == 'RESOURCE_STOP'
            cls.old_grant = builder.op('continue_study', **builder.grant(cls.development, stopped,
                                                   key='native-final-input-development-grant'))
            for _ in range(3):
                completed = builder.op('advance_family_study', study_id=cls.development['id'])
            assert completed['status'] == 'COMPLETE', completed
            assert len(completed['attempt_artifact_ids']) == 4
            assert len(completed['continuation_ids']) == 1
            assert len(builder.backend_calls) == 4
            assert all(selected is None for _, selected in builder.backend_calls)
            cls.development_view = deepcopy(completed)
            cls.retained = {name: deepcopy(getattr(builder, name)) for name in (
                'project', 'raw', 'runtime_manifest', 'archive_source', 'runtime',
                'qualified', 'cost', 'estimate', 'plans', 'execution', 'diagnostics')}
            cls.backup = cls.base_root / 'completed-development-backup'
            assert builder.op('backup_bundle', destination=str(cls.backup))['status'] == 'PASS'
            cls.operator_key = cls.base_root / 'operator.key'
            cls.operator_key.write_bytes((builder.directory / 'operator.key').read_bytes())
        finally:
            builder.doCleanups()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-final-input-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.s = native_support.NativeStudyIndependentTests('runTest')
        self.s.root = self.root
        self.s.directory = self.root / 'registry'
        self.assertEqual(restore_bundle(self.backup, self.s.directory, self.operator_key)['status'], 'PASS')
        self.s.broker = Broker(self.s.directory)
        self.addCleanup(lambda: self.s.broker.close())
        self.s.token = self.s.broker.admin_token
        for name, value in self.retained.items():
            setattr(self.s, name, deepcopy(value))
        self.s.clock = [0]
        self.s.qualification_aliases = {}
        self.s.current = True
        self.s.resolve_calls = []
        self.s.backend_calls = []
        self.s.backend_options = {}
        resolver = patch.object(NativeQualifications, '_require_inputs', autospec=True,
            side_effect=lambda instance, identity, **kwargs: self.s.resolve(instance, identity, **kwargs))
        resolver.start(); self.addCleanup(resolver.stop)
        membership = patch.object(qualification_owner.profile, 'validate_runtime', return_value=None)
        membership.start(); self.addCleanup(membership.stop)
        clock = patch.object(study_runs, 'time', types.SimpleNamespace(monotonic=lambda: self.s.clock[0]))
        clock.start(); self.addCleanup(clock.stop)
        backend = patch.object(study_runs, 'execute_attempt', side_effect=AssertionError('Final numerical dispatch forbidden'))
        self.backend = backend.start(); self.addCleanup(backend.stop)
        cache = patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Input preparation materialized runtime'))
        self.cache = cache.start(); self.addCleanup(cache.stop)

    def op(self, operation, **args):
        return self.s.op(operation, **args)

    def args(self, key='native-final-input', seed=714):
        profile = self.development['body']['manifest']['profile']
        budget = deepcopy(profile['budget'])
        budget.update(max_compute_ms=300000, attempt_compute_ms=300000,
                      max_storage_bytes=4 * 1024**3, attempt_storage_bytes=256 * MIB, max_attempts=1)
        return {'key': key, 'development_study_id': self.development['id'], 'time_rows': 3,
                'seed': seed, 'budget': budget, 'cost_estimate': deepcopy(self.s.estimate),
                'applicability': {name: {'status': 'not_applicable', 'cohort_ids': [],
                    'reason': 'Synthetic INPUT fixture only; no applicability certification.'}
                    for name in ('heavy_tail', 'overlap', 'common_shock')},
                'native_qualification_id': self.s.qualified['certificate']['id']}

    def prepare(self, **changes):
        return self.op('prepare_native_family_calibration', **{**self.args(), **changes})

    def view(self, artifact):
        return self.op('inspect_native_family_calibration', calibration_id=artifact['id'])

    def count(self):
        return self.s.broker._db.execute(
            "SELECT COUNT(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?", (INPUT,)).fetchone()[0]

    def artifact_bytes(self, artifact):
        return self.s.broker._db.execute('SELECT envelope FROM artifacts WHERE id=?', (artifact['id'],)).fetchone()[0]

    def test_prepared_input_binds_cases_current_native_source_policy_and_fixed_count_inventory(self):
        from trading_researcher.native_study_pipeline import BOOTSTRAP
        original = self.artifact_bytes(self.development)
        final = self.prepare()
        body = final['body']; manifest = body['manifest']; view = self.view(final)
        self.assertEqual(body['schema'], INPUT)
        self.assertEqual(final['creator'], 'controller'); self.assertEqual(final['origin'], 'controller')
        self.assertEqual(final['data_class'], 'operations')
        self.assertEqual(set(body['request']), {'key', 'development_study_id', 'time_rows', 'seed',
                         'budget', 'cost_estimate', 'applicability', 'native_qualification_id'})
        self.assertEqual(body['payload'], self.development['body']['payload'])
        raw = self.s.broker._read_blob_bytes(body['payload']['case_blob']['sha256'])
        self.assertEqual(len(raw.splitlines()), 3)
        self.assertEqual({'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}, body['payload']['case_blob'])
        self.assertEqual(body['source_footprint'], hashes(self.s.project))
        self.assertEqual(body['assessment_source_footprint'], hashes(self.s.project))
        self.assertEqual(body['process_control'], PROCESS_POLICY)
        self.assertEqual(body['native_bootstrap_sha256'], hashlib.sha256(BOOTSTRAP.encode()).hexdigest())
        self.assertEqual(body['native_binding'], {'schema': 'qualified-native-study-runtime/1',
            'profile': 'stationary-native-runtime/2', 'qualification_id': self.s.qualified['certificate']['id'],
            'runtime_id': self.s.runtime['id'], 'runtime_manifest': self.s.runtime_manifest,
            'host_images': [], 'source_footprint': hashes(self.s.project)})
        self.assertEqual(manifest['schema'], 'family-evaluator-calibration-manifest/1')
        self.assertEqual(manifest['profile']['targets'], [3])
        self.assertEqual(manifest['profile']['responses'], ['a', 'b'])
        self.assertEqual(manifest['profile']['patterns'], [[0, 0], [0, 1], [1, 1], [2, 2]])
        self.assertEqual(manifest['profile']['worlds_per_cell'], 256)
        self.assertEqual(len(manifest['profile']['specifications']), 1)
        self.assertEqual(len(manifest['worlds']), 1024)
        self.assertEqual(len({world['id'] for world in manifest['worlds']}), 1024)
        for pattern in range(4):
            self.assertEqual([world['replicate'] for world in manifest['worlds']
                              if world['pattern_index'] == pattern], list(range(256)))
        seeds = [world[role] for world in manifest['worlds'] for role in ('population_seed', 'bootstrap_seed')]
        self.assertEqual(len(set(seeds)), 2048)
        self.assertEqual(view['attempt_artifact_ids'], []); self.assertEqual(view['continuation_ids'], [])
        self.assertEqual(view['budget']['charged_compute_ms'], 0)
        self.assertEqual(view['budget']['charged_storage_bytes'], body['initial_storage_bytes'])
        assessment = view['summary']['count_assessment']
        self.assertEqual(assessment['status'], 'NOT_ASSESSED')
        self.assertEqual(len(assessment['cohorts']), 10)
        self.assertEqual(len(assessment['world_groups']), 4)
        self.assertTrue(all(len(group) == 256 for group in assessment['world_groups'].values()))
        self.assertIs(view['scientific_readiness'], False); self.assertIsNone(view['n_min'])
        self.assertEqual(self.artifact_bytes(self.development), original)
        self.assertEqual(self.op('inspect_family_study', study_id=self.development['id']), self.development_view)
        self.backend.assert_not_called(); self.cache.assert_not_called()
        self.assertFalse((self.s.directory / 'native-runtime-cache').exists())

    def test_native_final_semantic_identity_has_its_own_version_and_uses_development_meaning(self):
        final = self.prepare()
        body = self.development['body']; manifest = body['manifest']; payload = deepcopy(body['payload'])
        for key in ('candidate_ref', 'data_snapshot_ref'):
            payload['report']['request'].pop(key, None)
        payload['diagnostics'].pop('case_report_hash', None)
        specs = [{key: value for key, value in item.items() if key != 'rationale'}
                 for item in manifest['profile']['specifications']]
        expected = {'schema': 'native-joint-family-final-identity/1', 'payload': payload,
            'calculation_source': body['source_footprint'],
            'assigned': {key: value for key, value in manifest['assigned'].items() if key != 'input_binding'},
            'specifications': sorted(specs, key=canonical), 'time_rows': 3,
            'mc_policy': manifest['mc_policy'], 'family_patterns': [[0, 0], [0, 1], [1, 1], [2, 2]]}
        self.assertEqual(final['body']['identity'], digest(expected))
        self.assertNotEqual(final['body']['identity'], digest({**expected, 'schema': 'joint-family-final-identity/1'}))

    def test_input_logical_retention_counts_qualification_custody_and_excludes_duplicate_case_source_bytes(self):
        final = self.prepare(); body = final['body']
        records = [self.s.qualified[name] for name in ('certificate', 'capsule', 'source_package', 'runtime', 'archive_source')]
        common = {descriptor['sha256'] for descriptor in body['source_files'].values()}
        common.add(body['payload']['case_blob']['sha256'])
        unique = {identity for record in records for identity in record['blob_refs']} - common
        expected = sum(self.s.broker._db.execute('SELECT size FROM blobs WHERE sha256=?', (identity,)).fetchone()[0]
                       for identity in unique)
        expected += sum(len(self.artifact_bytes(record).encode()) for record in records)
        self.assertEqual(body['native_input_storage_bytes'], expected)
        self.assertEqual(body['initial_storage_bytes'], 2 * sum(map(len, self.s.project.values()))
                         + body['payload']['case_blob']['size'] + MIB + expected)
        self.assertLessEqual(len(final['blob_refs']), 256)
        self.assertLessEqual(len(canonical({key: value for key, value in final.items() if key != 'id'}).encode()), MIB)

    def test_same_key_and_alias_cannot_reset_seed_budget_cost_or_applicability(self):
        args = self.args(); final = self.op('prepare_native_family_calibration', **args)
        original = self.artifact_bytes(final); view = self.view(final)
        self.assertEqual(self.op('prepare_native_family_calibration', **args), final)
        self.assertEqual(self.prepare(key='native-final-alias'), final)
        variants = [{'seed': 715}, {'budget': {**args['budget'], 'max_compute_ms': 600000}},
                    {'cost_estimate': {**args['cost_estimate'], 'observed_compute_ms': 2}},
                    {'applicability': {**args['applicability'], 'heavy_tail': {
                        **args['applicability']['heavy_tail'], 'reason': 'Changed declaration remains a change.'}}}]
        for index, change in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(Conflict):
                self.prepare(key='changed-' + str(index), **change)
        args['budget']['max_compute_ms'] = 1
        self.assertEqual(self.artifact_bytes(final), original)
        self.assertEqual(self.view(final), view); self.assertEqual(self.count(), 1)

    def test_development_provenance_and_equivalent_qualification_runtime_aliases_keep_original_input(self):
        final = self.prepare(); original = self.artifact_bytes(final); view = self.view(final)
        args = self.s.args('equivalent-development-provenance', 'family', native=False, seed=719)
        alternative = self.op('prepare_family_study', **args)
        with patch.object(study_runs, 'execute_attempt', side_effect=self.s.backend):
            for _ in range(4):
                completed = self.op('advance_family_study', study_id=alternative['id'])
        self.assertEqual(completed['status'], 'COMPLETE')
        self.assertNotEqual(alternative['id'], self.development['id'])
        self.assertEqual(self.prepare(key='development-reference-alias', development_study_id=alternative['id']), final)
        self.s.runtime = self.op('retain_native_runtime', key='equivalent-native-final-runtime',
            archive_id=self.s.archive_source['id'], manifest=deepcopy(self.s.runtime_manifest))
        alias = self.s.qualification(key='equivalent-native-final-qualification')
        self.s.qualification_aliases[alias['certificate']['id']] = alias
        self.assertNotEqual(alias['runtime']['id'], final['body']['native_binding']['runtime_id'])
        self.assertEqual(self.prepare(key='qualification-runtime-alias', native_qualification_id=alias['certificate']['id']), final)
        self.assertEqual(self.artifact_bytes(final), original); self.assertEqual(self.view(final), view)
        self.assertEqual(self.count(), 1)

    def test_changed_native_host_manifest_or_source_cannot_rebind_existing_final(self):
        final = self.prepare(); original = self.artifact_bytes(final)
        retained = {name: deepcopy(getattr(self.s, name)) for name in ('runtime', 'runtime_manifest', 'project')}
        for kind in ('host', 'manifest', 'source'):
            for name, value in retained.items(): setattr(self.s, name, deepcopy(value))
            options = {}
            if kind == 'host':
                options['host_images'] = [{'path': str(self.root / 'invented-new-host.dll'), 'sha256': 'a' * 64, 'size': 1}]
            elif kind == 'manifest':
                self.s.runtime_manifest['dependencies']['fictional-fixture']['version'] = '2.0'
                self.s.runtime = self.op('retain_native_runtime', key='changed-native-final-runtime',
                    archive_id=self.s.archive_source['id'], manifest=self.s.runtime_manifest)
            else:
                name = next(iter(self.s.project)); self.s.project[name] += b'\n# independent changed source\n'
            alias = self.s.qualification(key='changed-native-final-' + kind, **options)
            self.s.qualification_aliases[alias['certificate']['id']] = alias
            with self.subTest(kind=kind), self.assertRaises(ERRORS):
                self.prepare(key='different-input-' + kind, native_qualification_id=alias['certificate']['id'])
            self.assertEqual(self.artifact_bytes(final), original); self.assertEqual(self.count(), 1)
        self.cache.assert_not_called(); self.backend.assert_not_called()

    def test_unexecuted_native_final_inventory_is_reserved_against_later_scalar_final(self):
        native = self.prepare()
        recorded = {artifact['id']: worlds for artifact, worlds in CalibrationStudies(self.s.broker)._recorded_calibration_worlds()}
        self.assertEqual(recorded[native['id']], native['body']['manifest']['worlds'])
        scalar_args = self.args('scalar-collision'); scalar_args.pop('native_qualification_id')
        with self.assertRaises(ERRORS): self.op('prepare_family_calibration', **scalar_args)
        self.assertEqual(self.view(native)['attempt_artifact_ids'], [])
        self.backend.assert_not_called()

    def test_preexisting_scalar_final_inventory_blocks_same_native_final_draws(self):
        args = self.args('earlier-scalar-final'); args.pop('native_qualification_id')
        scalar = self.op('prepare_family_calibration', **args); original = self.artifact_bytes(scalar)
        with self.assertRaises(ERRORS): self.prepare()
        native = self.prepare(key='fresh-native-final', seed=715)
        self.assertNotEqual(native['body']['identity'], scalar['body']['identity'])
        self.assertIn(scalar['id'], native['body']['seed_disjoint_from_recorded_study_ids'])
        self.assertEqual(self.artifact_bytes(scalar), original)
        for action in ('inspect_family_calibration', 'advance_family_calibration'):
            with self.subTest(action=action), self.assertRaises(ERRORS):
                self.op(action, calibration_id=native['id'])

    def test_population_inputs_block_cross_role_seed_reuse_before_final_input_commit(self):
        from trading_researcher.family_study import make_final_manifest
        profile = deepcopy(self.development['body']['manifest']['profile'])
        args = self.args(); profile.update(targets=[3], worlds_per_cell=256, seed=714,
                                           budget=args['budget'], cost_estimate=args['cost_estimate'])
        world = make_final_manifest(self.development['body']['manifest']['assigned'], profile)['worlds'][-1]
        for index, (schema, old_role, new_role) in enumerate((
                ('population-world-input/1', 'seed', 'bootstrap_seed'),
                ('population-world-input/1', 'bootstrap_seed', 'population_seed'),
                ('population-family-input/1', 'seed', 'bootstrap_seed'),
                ('population-family-input/1', 'bootstrap_seed', 'population_seed'))):
            # Private metadata-only reserved-input fixture; no population result
            # or qualification is fabricated. Tests collector identity, not law.
            payload = {'seed': 800 + index, 'bootstrap_seed': 900 + index}
            payload[old_role] = world[new_role]
            prior = self.s.owned({'schema': schema, 'payload': payload,
                                  'fixture': 'synthetic reserved seed inventory only'})
            self.assertIn(prior['id'], {artifact['id'] for artifact, _ in CalibrationStudies(self.s.broker)._recorded_calibration_worlds()})
            with self.subTest(schema=schema, old_role=old_role, new_role=new_role), self.assertRaises(ERRORS):
                self.prepare(key='cross-role-' + str(index))
            self.assertEqual(self.count(), 0)

    def test_input_and_synthetic_attempt_have_typed_development_grant_qualification_edges(self):
        final = self.prepare(); qid = self.s.qualified['certificate']['id']
        self.assertEqual(final['body']['development_continuation_ids'], [self.old_grant['id']])
        self.assertEqual(self.s.broker._technical_dependencies(final),
                         [self.development['id'], self.old_grant['id'], qid])
        for identity in (self.development['id'], self.old_grant['id'], qid):
            self.assertIn(identity, final['source_refs'])
        # Only a typed dependency-edge fixture; advance is still forbidden and
        # this record has no result/settlement/event or numerical authority.
        attempt = self.s.owned({'schema': RESULT, 'created_at': self.s.broker._now(),
            'study_id': final['id'], 'continuation_id': self.old_grant['id']},
            refs=[final['id'], self.old_grant['id']], authority='synthetic_typed_edge_not_executed')
        self.assertEqual(self.s.broker._technical_dependencies(attempt), [final['id'], self.old_grant['id']])
        evidence = self.op('add_source', data_class='development', body={'synthetic_dependency_defect': True})
        self.op('revoke_dependency', key='old-development-grant-defect', dependency_id=self.old_grant['id'],
                reason='Synthetic technical defect, not an empirical outcome.', evidence_refs=[evidence['id']])
        for artifact in (final, attempt):
            self.assertEqual(self.op('inspect_dependency_use', artifact_id=artifact['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
        self.assertEqual(self.s.broker._artifact(final['id']), final)

    def test_revoked_qualification_denies_new_preparation_but_preserves_exact_historical_inspection(self):
        final = self.prepare(); original = self.artifact_bytes(final); view = self.view(final)
        qid = self.s.qualified['certificate']['id']
        evidence = self.op('add_source', data_class='development', body={'synthetic_qualification_defect': True})
        self.op('revoke_dependency', key='native-final-qualification-defect', dependency_id=qid,
                reason='Synthetic native implementation defect.', evidence_refs=[evidence['id']])
        self.assertEqual(self.op('inspect_dependency_use', artifact_id=final['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
        self.assertEqual(self.view(final), view)
        self.assertEqual(self.prepare(), final)  # Exact historical key lookup.
        with self.assertRaises(ERRORS): self.prepare(key='new-use-after-revocation')
        self.assertEqual(self.artifact_bytes(final), original); self.assertEqual(self.count(), 1)
        self.cache.assert_not_called(); self.backend.assert_not_called()

    def test_missing_incomplete_wrong_target_or_stale_qualification_cannot_prepare(self):
        fake = self.op('add_source', data_class='development', body={'not': 'completed owned development'})
        incomplete = self.op('prepare_family_study', **self.s.args('incomplete-native-final-development', 'family', native=False))
        for index, change in enumerate(({'development_study_id': fake['id']},
                {'development_study_id': incomplete['id']}, {'time_rows': 4},
                {'native_qualification_id': fake['id']})):
            with self.subTest(index=index), self.assertRaises(ERRORS):
                self.prepare(key='not-admitted-' + str(index), **change)
        self.s.current = False
        with self.assertRaises(ERRORS): self.prepare(key='stale-qualification')
        self.assertEqual(self.count(), 0)
        self.cache.assert_not_called(); self.backend.assert_not_called()

    def test_worker_and_caller_overrides_are_denied_before_lookup_or_final_dispatch(self):
        worker = self.op('register_worker', name='native-final-input-worker', role='discovery', capabilities=[])['token']
        args = self.args()
        with patch.object(self.s.broker, '_artifact', side_effect=AssertionError('Worker looked up private final inputs')):
            for operation, request in (('prepare_native_family_calibration', args),
                    ('inspect_native_family_calibration', {'calibration_id': '1' * 64}),
                    ('advance_native_family_calibration', {'calibration_id': '1' * 64})):
                with self.subTest(operation=operation), self.assertRaises(Denied):
                    self.s.broker.call(worker, operation, **request)
        for extra in ({'execution_id': self.s.execution['id']}, {'profile': {}}, {'ready': True},
                      {'process_control': PROCESS_POLICY}, {'runtime_id': self.s.runtime['id']}):
            with self.subTest(extra=extra), self.assertRaises(Invalid):
                self.op('prepare_native_family_calibration', **{**args, **extra})
        final = self.prepare()
        with self.assertRaises(Invalid): self.op('inspect_native_family_calibration', study_id=final['id'])
        original = self.view(final)
        with self.assertRaises(Denied): self.op('advance_native_family_calibration', calibration_id=final['id'])
        with self.assertRaises(Denied): self.op('continue_study', **self.s.grant(final, original))
        self.assertEqual(self.view(final), original)
        self.cache.assert_not_called(); self.backend.assert_not_called()

    def test_reserved_schemas_and_wrapped_final_ancestry_are_not_research_inputs(self):
        final = self.prepare()
        synthetic_attempt = self.s.owned({'schema': RESULT, 'created_at': self.s.broker._now(),
            'study_id': final['id'], 'continuation_id': None}, refs=[final['id']],
            authority='synthetic_typed_edge_not_executed')
        for schema in (INPUT, RESULT):
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                self.op('add_source', data_class='development', body={'schema': schema})
        benign = self.op('add_source', data_class='development', body={'unrelated_development': True})
        for parent in (final, synthetic_attempt):
            wrapper = self.op('add_source', data_class='development', body={'laundered_final': 'still protected'},
                              exposure=[parent['id']])
            for role in ('discovery', 'formalizer'):
                self.op('create_context', role=role, epoch=0, artifact_ids=[benign['id']])
                for identity in (parent['id'], wrapper['id']):
                    with self.subTest(role=role, identity=identity), self.assertRaises(Denied):
                        self.op('create_context', role=role, epoch=0, artifact_ids=[identity])

    def test_failed_prepare_is_atomic_and_full_backup_restore_preserves_all_input_custody(self):
        event = self.s.broker._event
        before = self.s.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        def fail(actor, action, **details):
            if action == 'information_study_key': raise RuntimeError('Synthetic native final input commit failure')
            return event(actor, action, **details)
        with patch.object(self.s.broker, '_event', side_effect=fail), self.assertRaises(RuntimeError): self.prepare()
        self.assertEqual(self.count(), 0)
        self.assertEqual(self.s.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0], before)
        final = self.prepare(); original = self.artifact_bytes(final); view = self.view(final)
        backup = self.root / 'native-final-input-backup'
        self.assertEqual(self.op('backup_bundle', destination=str(backup))['status'], 'PASS')
        self.s.broker.close()
        restored = self.root / 'restored-registry'
        self.assertEqual(restore_bundle(backup, restored, self.operator_key)['status'], 'PASS')
        self.s.broker = Broker(restored); self.s.token = self.s.broker.admin_token
        self.assertEqual(self.artifact_bytes(final), original)
        self.assertEqual(self.view(final), view)
        self.assertEqual(self.op('inspect_family_study', study_id=self.development['id']), self.development_view)
        runner = native_study_runs.NativeFamilyCalibrationStudies(self.s.broker)
        self.assertEqual(runner._load_study_source(final), self.s.project)
        for identity in final['blob_refs']:
            self.s.broker._read_blob_bytes(identity)
        self.assertEqual(self.prepare(), final)
        with self.assertRaises(Denied): self.op('advance_native_family_calibration', calibration_id=final['id'])
        self.assertFalse((restored / 'native-runtime-cache').exists())
        self.assertEqual(self.op('verify')['status'], 'PASS')

    def test_retained_source_and_case_blob_corruption_remain_integrity_failures(self):
        final = self.prepare()
        runner = native_study_runs.NativeFamilyCalibrationStudies(self.s.broker)
        self.assertEqual(runner._load_study_source(final), self.s.project)
        source_id = next(iter(final['body']['source_files'].values()))['sha256']
        source_path = self.s.directory / 'blobs' / source_id[:2] / source_id
        source_path.write_bytes(b'Corrupted owned clone source')
        with self.assertRaises(ERRORS): runner._load_study_source(final)
        case_id = final['body']['payload']['case_blob']['sha256']
        case_path = self.s.directory / 'blobs' / case_id[:2] / case_id
        case_path.write_bytes(b'Corrupted owned clone cases')
        with self.assertRaises(ERRORS): self.s.broker._read_blob_bytes(case_id)
        self.assertEqual(self.s.broker._artifact(final['id']), final)
        self.assertEqual(self.view(final)['attempt_artifact_ids'], [])
        self.backend.assert_not_called(); self.cache.assert_not_called()


if __name__ == '__main__':
    unittest.main()
