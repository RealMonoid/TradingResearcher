"""Independent native-development caller/lifecycle tests, not native science.

Plans/executions/diagnostics come from the existing genuine synthetic fixture.
Only the explicitly trusted qualification resolver, implementation-membership
validator and numerical backend are substituted. Tiny invented runtime bytes
are actually retained/materialized;
no NumPy, full resampling, final calibration or market provider is executed.
"""
from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

from family_run_support import FamilyFixture
from test_information_study import profile as scalar_profile
from test_native_runtime_independent import archive, manifest, MEMBERS
from trading_researcher import family_study, study_runs
from trading_researcher.calibration_runs import CalibrationStudies
from trading_researcher.certification import _runtime_identity
from trading_researcher.codec import canonical, digest
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.evaluation_plans import source_bundle
from trading_researcher.native_qualification import NativeQualifications
from trading_researcher import native_qualification as qualification_owner
from trading_researcher.native_runtime import NativeRuntimes, verify_tree
from trading_researcher.server import Client, LocalServer, RemoteError
from trading_researcher.storage import restore_bundle


MIB = 1024**2
QLOG = b'Synthetic trusted qualification seam, not binary conformance.\n'
OUTPUT = b'Synthetic backend transcript, no simulated observations.\n'
SCRATCH = b'tiny actual backend materialization'
ERRORS = (Invalid, Conflict, Denied)
SCHEMAS = {'single': ('native-information-study-input/1', 'native-information-study-attempt/1'),
           'family': ('native-family-study-input/1', 'native-family-study-attempt/1')}


def hashes(source):
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in source.items()}


class NativeStudyIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # One real fixed raw/feature/reference/formalization/compile/execution
        # path, then the existing verified backup owner isolates each method.
        cls.base = tempfile.TemporaryDirectory(prefix='trf-native-study-base-')
        cls.addClassCleanup(cls.base.cleanup)
        cls.base_root = Path(cls.base.name)
        fixture = FamilyFixture()
        try:
            cls.execution = deepcopy(fixture.execution)
            cls.plans = {'family': deepcopy(fixture.plan)}
            cls.diagnostics = {'family': deepcopy(fixture.diagnostics)}
            cls.plans['single'] = fixture.op('prepare_evaluation_plan', key='native-single-fixture-plan',
                compiled_id=fixture.execution['body']['compiled_id'], primary_count=1,
                dependence=deepcopy(fixture.plan['body']['request']['dependence']))
            cls.diagnostics['single'] = fixture.op('prepare_information_diagnostics',
                key='native-single-fixture-diagnostics', plan_id=cls.plans['single']['id'],
                execution_id=fixture.execution['id'], lags=[1, 2], limits={'max_seconds': 60})
            cls.backup = cls.base_root / 'verified-base'
            fixture.op('backup_bundle', destination=str(cls.backup))
            cls.operator_key = cls.base_root / 'operator.key'
            cls.operator_key.write_bytes((fixture.broker.directory / 'operator.key').read_bytes())
        finally:
            fixture.close()

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='trf-native-study-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / 'registry'
        restore_bundle(self.backup, self.directory, self.operator_key)
        self.broker = Broker(self.directory)
        self.addCleanup(lambda: self.broker.close())
        self.token = self.broker.admin_token
        self.clock = [0]
        clock_patch = patch.object(study_runs, 'time', types.SimpleNamespace(monotonic=lambda: self.clock[0]))
        clock_patch.start(); self.addCleanup(clock_patch.stop)
        self.project = source_bundle()
        self.raw = archive()
        self.runtime_manifest = manifest()
        path = self.root / 'invented-runtime.zip'; path.write_bytes(self.raw)
        self.archive_source = self.op('add_blob_source', path=str(path), data_class='operations',
            description='Invented data/notices only, selected solely by the trusted test seam')
        self.runtime = self.op('retain_native_runtime', key='native-study-fixture-runtime',
            archive_id=self.archive_source['id'], manifest=self.runtime_manifest)
        self.qualified = self.qualification()
        self.qualification_aliases = {}
        self.current = True
        self.resolve_calls = []
        resolver = patch.object(NativeQualifications, '_require_inputs', autospec=True,
            side_effect=lambda instance, identity, **kwargs: self.resolve(instance, identity, **kwargs))
        resolver.start(); self.addCleanup(resolver.stop)
        # Tiny invented runtime bytes are outside the production pinned binary
        # profile. This substitutes technical membership only, leaving the real
        # prior-knowledge/exposure and all scientific input gates in force.
        membership = patch.object(qualification_owner.profile, 'validate_runtime', return_value=None)
        membership.start(); self.addCleanup(membership.stop)
        self.backend_calls = []
        self.backend_options = {}
        backend = patch.object(study_runs, 'execute_attempt', side_effect=self.backend)
        self.backend_mock = backend.start(); self.addCleanup(backend.stop)
        estimate = {'world_time_rows': 3, 'observed_compute_ms': 1, 'observed_storage_bytes': 1,
                    'qualification': 'Synthetic lifecycle cost claim; no native performance estimate.'}
        self.cost = self.op('add_source', data_class='development',
                            body={'schema': 'development-study-cost-estimate/1', **estimate})
        self.estimate = {'source_ref': self.cost['id'], **estimate}

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def operation(self, action, kind, *, native=True):
        return action + ('_native_' if native else '_') + ('information_study' if kind == 'single' else 'family_study')

    def owned(self, body, *, refs=(), exposure=(), blobs=(), authority='native_bootstrap_conformance_only'):
        with self.broker._transaction():
            for value in blobs: self.broker._register_blob(value)
            return self.broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'operations', 'source_refs': sorted(refs),
                'exposure': sorted(exposure), 'blob_refs': sorted({value['sha256'] for value in blobs}),
                'authority': authority, 'body': body})

    def qualification(self, *, exposure=(), key='synthetic-qualification', host_images=None):
        if exposure:
            # Host-private adversarial lineage fixture: retain the genuine
            # imported archive's bytes/ownership/type while adding inherited
            # synthetic knowledge. Keep all five core records' normal exact
            # closure, so rejection must inspect ancestry rather than a broken
            # certificate reference shape. No protected bytes are accessed.
            envelope = deepcopy({key: value for key, value in self.archive_source.items() if key != 'id'})
            envelope['exposure'] = sorted(exposure)
            with self.broker._transaction():
                self.archive_source = self.broker._save_artifact(envelope)
            self.runtime = self.op('retain_native_runtime', key='ancestry-runtime-' + digest(sorted(exposure)),
                                   archive_id=self.archive_source['id'], manifest=self.runtime_manifest)
        source_files = {name: self.broker._stage_blob_bytes(raw) for name, raw in self.project.items()}
        package = self.owned({'schema': 'native-qualification-source/1', 'profile': qualification_owner.profile.PROFILE,
            'created_at': self.broker._now(), 'files': source_files, 'footprint': hashes(self.project),
            'bootstrap_sha256': hashlib.sha256(qualification_owner.profile.BOOTSTRAP.encode()).hexdigest()},
            blobs=list(source_files.values()), authority='retained_source_not_certified')
        request = {'key': key, 'runtime_id': self.runtime['id']}
        attempt_id = key + '-attempt'
        refs = [self.runtime['id'], package['id']]
        capsule = self.owned({'schema': 'native-runtime-qualification-input/1',
            'profile': qualification_owner.profile.PROFILE, 'created_at': self.broker._now(),
            'request': request, 'attempt_id': attempt_id,
            'runtime_id': self.runtime['id'], 'runtime_manifest': self.runtime_manifest,
            'source_package_id': package['id'], 'source_footprint': hashes(self.project),
            'runtime_identity': _runtime_identity(), 'host_images': [] if host_images is None else host_images,
            'limits': {'max_compute_ms': 300000, 'max_storage_bytes': 268435456},
            'initial_storage_bytes': len(self.raw) + 2 * sum(map(len, self.project.values())) + MIB,
            'scientific_readiness': False}, refs=refs, exposure=set(refs) | set(self.runtime['exposure']))
        log = self.broker._stage_blob_bytes(QLOG)
        certificate = self.owned({'schema': 'native-runtime-qualification/1',
            'profile': qualification_owner.profile.PROFILE, 'created_at': self.broker._now(),
            'request': request, 'attempt_id': attempt_id,
            'input_id': capsule['id'], 'runtime_id': self.runtime['id'], 'source_package_id': package['id'],
            'status': 'CERTIFIED', 'report': {'scope': 'trusted synthetic qualification seam only'},
            'settlement': {'compute_ms': 0, 'storage_bytes': len(QLOG), 'usage_known': True},
            'failures': [], 'failure': None, 'output_blobs': {'synthetic.txt': log},
            'scientific_readiness': False}, refs=[capsule['id']],
            exposure=set(capsule['exposure']) | {capsule['id']}, blobs=[log])
        return {'certificate': certificate, 'capsule': capsule, 'source_package': package,
                'runtime': self.runtime, 'archive_source': self.archive_source, 'source': self.project}

    def resolve(self, instance, identity, *, runtime_directory=None):
        qualified = (self.qualified if identity == self.qualified['certificate']['id'] else
                     self.qualification_aliases.get(identity))
        if qualified is None or not self.current:
            raise Denied('Synthetic qualification is not current')
        instance.broker._require_usable_dependencies(identity)
        self.resolve_calls.append(None if runtime_directory is None else str(runtime_directory))
        if runtime_directory is not None:
            verify_tree(Path(runtime_directory), qualified['runtime']['body']['manifest'])
        return deepcopy(qualified)

    def args(self, key, kind='single', *, native=True, budget=None, seed=None):
        profile = scalar_profile()
        # Distinct logical fixtures use distinct prescribed inventories. Alias
        # tests explicitly copy their original profile while changing the key.
        if seed is None:
            seed = 713 + sum(map(ord, key))
        profile.update(targets=[3], worlds_per_cell=1, seed=seed, cost_estimate=deepcopy(self.estimate))
        profile['budget'].update(max_compute_ms=60000, attempt_compute_ms=10000,
            max_storage_bytes=2 * 1024**3, attempt_storage_bytes=256 * MIB, max_attempts=1)
        if budget: profile['budget'].update(budget)
        if kind == 'family':
            profile.update(responses=['a', 'b'], patterns=[[0, 0], [0, 1], [1, 1], [2, 2]])
        result = {'key': key, 'plan_id': self.plans[kind]['id'], 'execution_id': self.execution['id'],
                  'diagnostics_id': self.diagnostics[kind]['id'], 'profile': profile}
        if native: result['native_qualification_id'] = self.qualified['certificate']['id']
        return result

    def prepare(self, key='native', kind='single', **options):
        return self.op(self.operation('prepare', kind, native=options.get('native', True)),
                       **self.args(key, kind, **options))

    def view(self, study, kind='single', *, native=True):
        return self.op(self.operation('inspect', kind, native=native), study_id=study['id'])

    def advance(self, study, kind='single', *, native=True):
        return self.op(self.operation('advance', kind, native=native), study_id=study['id'])

    def backend(self, source, payload, manifest, world, cases, remaining, meter, outputs, *, _native=None):
        remaining()
        self.assertEqual(hashes(source), hashes(self.project))
        if _native is not None:
            self.assertEqual(set(_native), {'binding', 'directory'})
            self.assertEqual(_native['binding']['qualification_id'], self.qualified['certificate']['id'])
            verify_tree(Path(_native['directory']), self.runtime_manifest)
        self.backend_calls.append((world['id'], deepcopy(_native)))
        (self.root / 'backend-scratch.bin').write_bytes(SCRATCH)
        meter['materialized_bytes'] += len(SCRATCH)
        outputs.append(('synthetic/transcript.txt', OUTPUT))
        if self.backend_options.get('unknown'): meter['accounting_complete'] = False
        if self.backend_options.get('storage_overrun'):
            meter['materialized_bytes'] += manifest['profile']['budget']['attempt_storage_bytes']
        if self.backend_options.get('error'): raise RuntimeError('Synthetic backend failure after retained output')
        if self.backend_options.get('revoke'):
            evidence = self.op('add_source', data_class='development', body={'synthetic_defect': True})
            self.op('revoke_dependency', key='native-mid-work-defect', dependency_id=self.qualified['certificate']['id'],
                    reason='Synthetic current-use defect', evidence_refs=[evidence['id']])
        if manifest['schema'].startswith('family-'):
            components = [{'id': item['id'], 'truth': manifest['effects'][item['scenario']],
                           'state': 'INFORMATION_GAP', 'decision': None, 'covered': None}
                          for item in family_study.components(manifest, world)]
            outcome = family_study.outcome_record(manifest, world, components)
        else:
            outcome = {'world_id': world['id'], 'state': 'INFORMATION_GAP', 'decision': None,
                       'scope_count': None, 'condition_count': None, 'covered': None}
        result = {'world_id': world['id'], 'outcome': outcome, 'scientific_readiness': False,
                  'classification_permitted': False, 'n_min': None,
                  'scope': 'synthetic backend fixture, no numerical world execution'}
        proofs = [{'scope': 'synthetic backend proof only', 'phase': phase} for phase in ('generate', 'replay')]
        self.clock[0] += 1
        return result, proofs

    def attempts(self, view):
        return [self.broker._artifact(identity) for identity in view['attempt_artifact_ids']]

    def grant(self, study, view, key='native-continuation'):
        return {'key': key, 'study_id': study['id'], 'expected_checkpoint': view['resource_checkpoint'],
                'additional_compute_ms': 10000, 'additional_storage_bytes': 0,
                'rationale': 'Continue the same synthetic fixed inventory.',
                'expected_progress': 'Retain the next prescribed world.',
                'stop_reason': 'Stop at the next frozen resource or failure boundary.'}

    def test_native_inputs_bind_full_qualification_closure_and_same_scientific_manifests(self):
        from trading_researcher.native_study_pipeline import BOOTSTRAP
        for kind in ('single', 'family'):
            with self.subTest(kind=kind):
                with patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Prepare materialized runtime')):
                    study = self.prepare('binding-' + kind, kind)
                scalar = self.prepare('scalar-binding-' + kind, kind, native=False,
                                      seed=study['body']['request']['profile']['seed'])
                self.assertEqual(study['body']['schema'], SCHEMAS[kind][0])
                self.assertEqual(study['body']['manifest'], scalar['body']['manifest'])
                self.assertEqual(study['body']['source_footprint'], hashes(self.project))
                self.assertEqual(study['body']['native_bootstrap_sha256'], hashlib.sha256(BOOTSTRAP.encode()).hexdigest())
                self.assertEqual(study['body']['native_binding'], {
                    'schema': 'qualified-native-study-runtime/1', 'profile': 'stationary-native-runtime/2',
                    'qualification_id': self.qualified['certificate']['id'], 'runtime_id': self.runtime['id'],
                    'runtime_manifest': self.runtime_manifest, 'host_images': [], 'source_footprint': hashes(self.project)})
                records = [self.qualified[name] for name in ('certificate', 'capsule', 'source_package', 'runtime', 'archive_source')]
                excluded = {value['sha256'] for value in study['body']['source_files'].values()}
                excluded.add(study['body']['payload']['case_blob']['sha256'])
                blobs = {identity for record in records for identity in record['blob_refs']} - excluded
                extra = sum(self.broker._db.execute('SELECT size FROM blobs WHERE sha256=?', (identity,)).fetchone()[0]
                            for identity in blobs)
                extra += sum(len(self.broker._db.execute('SELECT envelope FROM artifacts WHERE id=?',
                             (record['id'],)).fetchone()[0].encode()) for record in records)
                self.assertEqual(study['body']['native_input_storage_bytes'], extra)
                self.assertEqual(study['body']['initial_storage_bytes'], scalar['body']['initial_storage_bytes'] + extra)
                self.assertLessEqual(len(study['blob_refs']), 256)
                self.assertIn(self.qualified['certificate']['id'], study['source_refs'])
                self.assertTrue({record['id'] for record in records} <= set(study['exposure']))
                self.assertFalse((self.directory / 'native-runtime-cache').exists())
                self.assertFalse(study['body']['scientific_readiness'])
                self.assertIsNone(self.view(study, kind)['n_min'])

    def test_request_idempotency_alias_conflicts_and_input_immutability(self):
        for kind in ('single', 'family'):
            with self.subTest(kind=kind):
                args = self.args('idempotent-' + kind, kind)
                study = self.op(self.operation('prepare', kind), **args)
                self.assertEqual(self.op(self.operation('prepare', kind), **args), study)
                self.assertEqual(self.op(self.operation('prepare', kind), **{**args, 'key': 'alias-' + kind}), study)
                changed = deepcopy(args); changed['profile']['seed'] += 1
                with self.assertRaises(Conflict): self.op(self.operation('prepare', kind), **changed)
                args['profile']['budget']['max_compute_ms'] = 1
                self.assertEqual(self.broker._artifact(study['id']), study)
                with self.assertRaises(sqlite3.IntegrityError):
                    self.broker._db.execute('UPDATE artifacts SET envelope=? WHERE id=?', ('{}', study['id']))

    def test_equivalent_qualification_and_runtime_aliases_preserve_original_exhausted_budget(self):
        for mode in ('certificate', 'runtime'):
            for kind in ('single', 'family'):
                with self.subTest(mode=mode, kind=kind):
                    args = self.args('original-' + mode + '-' + kind, kind,
                                     budget={'max_compute_ms': 10000})
                    study = self.op(self.operation('prepare', kind), **args)
                    stopped = self.advance(study, kind)
                    self.assertEqual(stopped['status'], 'RESOURCE_STOP')
                    if mode == 'runtime':
                        self.runtime = self.op('retain_native_runtime', key='equivalent-runtime-' + kind,
                            archive_id=self.archive_source['id'], manifest=deepcopy(self.runtime_manifest))
                        self.assertNotEqual(self.runtime['id'], study['body']['native_binding']['runtime_id'])
                    alias = self.qualification(key='equivalent-qualification-' + mode + '-' + kind)
                    alias_id = alias['certificate']['id']
                    self.assertNotEqual(alias_id, self.qualified['certificate']['id'])
                    self.qualification_aliases[alias_id] = alias
                    incoming = {**deepcopy(args), 'key': 'aliased-study-' + mode + '-' + kind,
                                'native_qualification_id': alias_id}
                    before = self.broker._db.execute(
                        "SELECT COUNT(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?",
                        (SCHEMAS[kind][0],)).fetchone()[0]
                    self.assertEqual(self.op(self.operation('prepare', kind), **incoming), study)
                    self.assertEqual(self.broker._db.execute(
                        "SELECT COUNT(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?",
                        (SCHEMAS[kind][0],)).fetchone()[0], before)
                    self.assertEqual(self.view(study, kind), stopped)
                    self.assertEqual(self.broker._artifact(study['id']), study)
                    self.assertEqual(study['body']['request']['native_qualification_id'],
                                     self.qualified['certificate']['id'])
                    calls = len(self.backend_calls)
                    self.assertEqual(self.advance(study, kind), stopped)
                    self.assertEqual(len(self.backend_calls), calls)

    def test_current_qualification_alias_cannot_replace_revoked_original_binding(self):
        study = self.prepare('original-binding-revocation', 'family')
        alias = self.qualification(key='still-current-qualification-alias')
        alias_id = alias['certificate']['id']
        self.qualification_aliases[alias_id] = alias
        incoming = {**deepcopy(study['body']['request']), 'key': 'alias-of-revoked-study',
                    'native_qualification_id': alias_id}
        self.assertEqual(self.op(self.operation('prepare', 'family'), **incoming), study)
        evidence = self.op('add_source', data_class='development',
                           body={'synthetic_qualification_defect': 'original certificate only'})
        self.op('revoke_dependency', key='revoke-original-qualification',
                dependency_id=self.qualified['certificate']['id'],
                reason='Synthetic certificate-specific defect.', evidence_refs=[evidence['id']])
        self.assertEqual(self.op('inspect_dependency_use', artifact_id=alias_id)['status'], 'NOT_REVOKED')
        self.assertEqual(self.op('inspect_dependency_use', artifact_id=study['id'])['status'],
                         'INVALIDATED_BY_DEPENDENCY')
        with patch.object(NativeRuntimes, '_materialize',
                          side_effect=AssertionError('Revoked original reached native setup')) as materialize:
            view = self.advance(study, 'family')
        materialize.assert_not_called()
        self.assertEqual(self.backend_calls, [])
        self.assertEqual(view['status'], 'TECHNICAL_FAILURE')
        self.assertEqual(self.attempts(view)[-1]['body']['failure']['type'], 'Denied')
        self.assertEqual(self.broker._artifact(study['id']), study)
        self.assertEqual(self.op(self.operation('prepare', 'family'), **incoming), study)

    def test_qualification_alias_cannot_change_bound_host_manifest_or_source(self):
        args = self.args('fixed-runtime-inputs', 'family')
        study = self.op(self.operation('prepare', 'family'), **args)
        original_runtime, original_manifest, original_project = self.runtime, self.runtime_manifest, self.project
        for change in ('host', 'manifest', 'source'):
            with self.subTest(change=change):
                self.runtime, self.runtime_manifest, self.project = original_runtime, original_manifest, original_project
                options = {}
                if change == 'host':
                    options['host_images'] = [{'path': str((self.root / 'different-qualified-host.dll').absolute()),
                                               'sha256': 'a' * 64, 'size': 1}]
                elif change == 'manifest':
                    self.runtime_manifest = deepcopy(original_manifest)
                    self.runtime_manifest['dependencies']['fictional-fixture']['version'] = '2.0'
                    self.runtime = self.op('retain_native_runtime', key='different-qualified-manifest',
                        archive_id=self.archive_source['id'], manifest=self.runtime_manifest)
                else:
                    self.project = dict(original_project)
                    name = next(iter(self.project))
                    self.project[name] += b'\n# Invented changed qualification source.\n'
                alias = self.qualification(key='different-input-qualification-' + change, **options)
                alias_id = alias['certificate']['id']
                self.qualification_aliases[alias_id] = alias
                before = self.broker._db.execute(
                    "SELECT COUNT(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?",
                    (SCHEMAS['family'][0],)).fetchone()[0]
                with self.assertRaises(ERRORS):
                    self.op(self.operation('prepare', 'family'), **{
                        **deepcopy(args), 'key': 'changed-input-study-alias-' + change,
                        'native_qualification_id': alias_id})
                self.assertEqual(self.broker._db.execute(
                    "SELECT COUNT(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?",
                    (SCHEMAS['family'][0],)).fetchone()[0], before)
                self.assertEqual(self.broker._artifact(study['id']), study)
        self.runtime, self.runtime_manifest, self.project = original_runtime, original_manifest, original_project
        self.assertEqual(self.backend_calls, [])

    def test_http_roles_exact_fields_and_reserved_namespaces(self):
        worker = self.op('register_worker', name='native-study-no-authority', role='discovery', capabilities=[])['token']
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Unauthorized lookup')):
            for kind in ('single', 'family'):
                with self.assertRaises(Denied): self.broker.call(worker, self.operation('prepare', kind), **self.args('denied', kind))
                with self.assertRaises(Denied):
                    self.broker.call(worker, self.operation('inspect', kind), study_id='0' * 64)
        server = LocalServer(self.broker)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            operator, researcher = Client(server.url, self.token), Client(server.url, worker)
            for kind in ('single', 'family'):
                with self.subTest(kind=kind):
                    with self.assertRaises(RemoteError) as error:
                        researcher.call(self.operation('prepare', kind), **self.args('http-denied', kind))
                    self.assertEqual(error.exception.status, 403)
                    study = operator.call(self.operation('prepare', kind), **self.args('http-' + kind, kind))
                    self.assertEqual(operator.call(self.operation('inspect', kind), study_id=study['id'])['status'], 'READY')
                    view = operator.call(self.operation('advance', kind), study_id=study['id'])
                    self.assertEqual(view['summary']['recorded_worlds'], 1)
        finally:
            server.shutdown(); thread.join(timeout=5); server.server_close()
        for kind in ('single', 'family'):
            for extra in ({'runtime_id': self.runtime['id']}, {'override': True}, {'directory': str(self.root)}):
                with self.assertRaises(Invalid): self.op(self.operation('prepare', kind), **{**self.args('extra', kind), **extra})
            for schema in SCHEMAS[kind]:
                with self.assertRaises(Invalid): self.op('add_source', data_class='development', body={'schema': schema})

    def test_qualification_currentness_and_genuine_data_gates_are_not_bypassed(self):
        self.current = False
        for kind in ('single', 'family'):
            with self.assertRaises(ERRORS): self.prepare('stale-' + kind, kind)
        self.current = True
        fake = self.op('add_source', data_class='development', body={'not': 'owned diagnostics'})
        for kind in ('single', 'family'):
            args = self.args('bad-diagnostics-' + kind, kind); args['diagnostics_id'] = fake['id']
            with self.assertRaises(Denied): self.op(self.operation('prepare', kind), **args)
            args = self.args('bad-qualification-' + kind, kind); args['native_qualification_id'] = fake['id']
            with self.assertRaises(ERRORS): self.op(self.operation('prepare', kind), **args)
        self.assertEqual(self.backend_calls, [])

    def test_qualification_ancestry_cannot_launder_protected_operational_or_unresolved_knowledge(self):
        protected = self.op('add_source', data_class='assessment',
                            body={'synthetic_protected_identity': 'no protected data content'})
        operational = self.op('add_source', data_class='operations',
                             body={'synthetic_operations_knowledge': 'not a qualified technical input'})
        unresolved = 'f' * 64
        self.assertIsNone(self.broker._db.execute('SELECT 1 FROM artifacts WHERE id=?', (unresolved,)).fetchone())
        for label, identity in (('protected', protected['id']), ('operations', operational['id']),
                                ('unresolved', unresolved)):
            wrapper = self.op('add_source', data_class='development',
                              body={'synthetic_ancestry_wrapper': label}, exposure=[identity])
            self.qualified = self.qualification(exposure=[wrapper['id']])
            for kind in ('single', 'family'):
                with self.subTest(ancestry=label, kind=kind):
                    before = self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]
                    with patch.object(NativeRuntimes, '_materialize',
                                      side_effect=AssertionError('Admission gap materialized runtime')):
                        with self.assertRaises(ERRORS):
                            self.prepare('ancestry-' + label + '-' + kind, kind)
                    self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], before)
        self.assertEqual(self.backend_calls, [])

    def test_legacy_operations_reject_native_schemas_and_final_inventory_still_sees_them(self):
        studies = {kind: self.prepare('inventory-' + kind, kind) for kind in ('single', 'family')}
        recorded = {record['id']: worlds for record, worlds in CalibrationStudies(self.broker)._recorded_calibration_worlds()}
        for kind, study in studies.items():
            self.assertEqual(recorded[study['id']], study['body']['manifest']['worlds'])
            for action in ('inspect', 'advance'):
                with self.assertRaises(ERRORS):
                    self.op(self.operation(action, kind, native=False), study_id=study['id'])
            scalar = self.prepare('legacy-separate-' + kind, kind, native=False)
            with self.assertRaises(ERRORS): self.view(scalar, kind)
            args = self.args('legacy-extra-' + kind, kind)
            with self.assertRaises(Invalid): self.op(self.operation('prepare', kind, native=False), **args)

    def test_materialization_follows_durable_reservation_and_cold_warm_bytes_are_exact(self):
        study = self.prepare()
        original = NativeRuntimes._materialize
        seen = []

        def materialize(instance, identity, meter):
            with closing(sqlite3.connect((self.directory / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
                events = [json.loads(raw) for raw, in db.execute('SELECT envelope FROM events ORDER BY seq')]
                reservations = [e for e in events if e['action'] == 'information_study_reserved'
                                and e['details'].get('study_id') == study['id']]
                starts = [e for e in events if e['action'] == 'bound_computation_started'
                          and e['details'].get('retained_input_id') == study['id']]
                self.assertEqual(len(reservations), len(starts))
                self.assertGreater(len(starts), len(seen))
            before = meter['materialized_bytes']
            path = original(instance, identity, meter)
            seen.append(meter['materialized_bytes'] - before)
            return path

        with patch.object(NativeRuntimes, '_materialize', materialize):
            first = self.advance(study)
            second = self.advance(study)
        self.assertEqual(seen, [sum(map(len, MEMBERS.values())), 0])
        attempts = self.attempts(second)
        self.assertEqual(attempts[0]['body']['settlement']['storage_bytes'] -
                         attempts[1]['body']['settlement']['storage_bytes'], sum(map(len, MEMBERS.values())))
        self.assertTrue(any(path is None for path in self.resolve_calls))
        self.assertTrue(any(path is not None for path in self.resolve_calls))
        self.assertEqual(first['summary']['recorded_worlds'], 1)

    def test_complete_fixed_inventory_retains_one_result_per_world_without_scientific_nomination(self):
        for kind in ('single', 'family'):
            study = self.prepare('complete-' + kind, kind)
            for world in study['body']['manifest']['worlds']:
                view = self.advance(study, kind)
                self.assertEqual(self.attempts(view)[-1]['body']['world_id'], world['id'])
            self.assertEqual(view['status'], 'COMPLETE')
            self.assertEqual(len(view['attempt_artifact_ids']), len(study['body']['manifest']['worlds']))
            self.assertIsNone(view['summary']['candidate_time_rows'])
            self.assertIsNone(view['n_min']); self.assertIs(view['scientific_readiness'], False)
            for attempt in self.attempts(view):
                self.assertEqual(attempt['body']['schema'], SCHEMAS[kind][1])
                self.assertEqual(len(attempt['body']['proofs']), 2)
                self.assertIn(hashlib.sha256(OUTPUT).hexdigest(), attempt['blob_refs'])
                self.assertIs(attempt['body']['scientific_readiness'], False)
            calls = len(self.backend_calls)
            self.assertEqual(self.advance(study, kind), view)
            self.assertEqual(len(self.backend_calls), calls)

    def test_backend_failure_and_midwork_revocation_retain_full_unavailable_outcomes(self):
        for kind in ('single', 'family'):
            study = self.prepare('failure-' + kind, kind)
            self.backend_options = {'error': True}
            view = self.advance(study, kind)
            self.assertEqual(view['status'], 'TECHNICAL_FAILURE')
            attempt = self.attempts(view)[-1]
            self.assertEqual(attempt['body']['failure']['type'], 'RuntimeError')
            self.assertEqual(attempt['body']['outcome']['state'], 'TECHNICAL_FAILURE')
            self.assertEqual(self.broker._read_blob_bytes(hashlib.sha256(OUTPUT).hexdigest()), OUTPUT)
            if kind == 'family':
                self.assertTrue(all(row['state'] == 'TECHNICAL_FAILURE' for row in attempt['body']['outcome']['components']))
        self.backend_options = {'revoke': True}
        study = self.prepare('mid-work-revocation', 'family')
        view = self.advance(study, 'family')
        attempt = self.attempts(view)[-1]
        self.assertEqual(attempt['body']['outcome']['state'], 'TECHNICAL_FAILURE')
        self.assertEqual(attempt['body']['result']['outcome']['state'], 'INFORMATION_GAP')
        self.assertEqual(self.op('inspect_dependency_use', artifact_id=study['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')

    def test_native_unknown_usage_fences_retry_and_grant_with_ample_budget_and_two_attempts(self):
        self.check_unknown_fence(native=True)

    def test_legacy_unknown_usage_fences_retry_and_grant_with_ample_budget_and_two_attempts(self):
        self.check_unknown_fence(native=False)

    def check_unknown_fence(self, *, native):
        for kind in ('single', 'family'):
            with self.subTest(kind=kind, native=native):
                study = self.prepare('unknown-' + str(native) + '-' + kind, kind,
                                     native=native, budget={'max_attempts': 2})
                self.backend_options = {'unknown': True}
                view = self.advance(study, kind, native=native)
                self.assertEqual(view['status'], 'USAGE_UNCERTAIN')
                self.assertIsNone(view['next_world_id'])
                self.assertFalse(view['budget']['next_reservation_fits'])
                self.assertEqual(view['budget']['charged_compute_ms'], 10000)
                self.assertEqual(view['budget']['charged_storage_bytes'],
                                 study['body']['initial_storage_bytes'] + 256 * MIB)
                self.assertIsNone(view['summary']['candidate_time_rows'])
                before = len(self.backend_calls), len(view['attempt_artifact_ids'])
                self.assertEqual(self.advance(study, kind, native=native), view)
                self.assertEqual((len(self.backend_calls), len(self.view(study, kind, native=native)['attempt_artifact_ids'])), before)
                with self.assertRaises(ERRORS): self.op('continue_study', **self.grant(study, view))

    def test_setup_time_and_reported_storage_overrun_remain_resource_failures(self):
        study = self.prepare('setup-deadline')
        original = NativeRuntimes._materialize

        def slow(instance, identity, meter):
            path = original(instance, identity, meter); self.clock[0] += 11; return path

        with patch.object(NativeRuntimes, '_materialize', slow): view = self.advance(study)
        self.assertEqual(view['status'], 'RESOURCE_STOP')
        attempt = self.attempts(view)[-1]
        self.assertEqual(attempt['body']['failure']['type'], 'ResourceOverrun')
        self.assertGreaterEqual(attempt['body']['settlement']['compute_ms'], 11000)
        self.backend_options = {'storage_overrun': True}
        other = self.prepare('storage-overrun')
        view = self.advance(other)
        self.assertEqual(view['status'], 'RESOURCE_STOP')
        self.assertTrue(view['budget']['overrun'])
        self.assertGreater(self.attempts(view)[-1]['body']['settlement']['storage_bytes'], 256 * MIB)

    def test_known_insufficient_setup_storage_is_denied_before_cold_materialization(self):
        # A legal profile may reserve less than the known source/child envelope.
        # Retain admission/reservation/failure, but do not knowingly spend that
        # reservation on native setup before the complete lower bound is checked.
        for kind in ('single', 'family'):
            with self.subTest(kind=kind):
                study = self.prepare('insufficient-setup-' + kind, kind,
                                     budget={'attempt_storage_bytes': 2 * MIB})
                self.assertEqual(self.view(study, kind)['status'], 'READY')
                with patch.object(NativeRuntimes, '_materialize',
                                  side_effect=AssertionError('Insufficient setup budget reached materializer')) as materialize:
                    view = self.advance(study, kind)
                materialize.assert_not_called()
                self.assertEqual(self.backend_calls, [])
                self.assertFalse((self.directory / 'native-runtime-cache').exists())
                self.assertEqual(view['status'], 'TECHNICAL_FAILURE')
                attempt = self.attempts(view)[-1]
                self.assertEqual(attempt['body']['outcome']['state'], 'TECHNICAL_FAILURE')
                self.assertEqual(attempt['body']['failure']['type'], 'Invalid')
                self.assertTrue(attempt['body']['settlement']['usage_known'])
                self.assertLessEqual(attempt['body']['settlement']['storage_bytes'], 2 * MIB)
                self.assertEqual(len(view['attempt_artifact_ids']), 1)

    def test_resource_continuation_preserves_original_native_inventory_and_caps(self):
        study = self.prepare('continuation', 'family', budget={'max_compute_ms': 10000})
        original = deepcopy(study)
        stopped = self.advance(study, 'family')
        self.assertEqual(stopped['status'], 'RESOURCE_STOP')
        request = self.grant(study, stopped)
        grant = self.op('continue_study', **request)
        self.assertEqual(self.op('continue_study', **request), grant)
        self.assertEqual(self.broker._artifact(study['id']), original)
        view = self.view(study, 'family')
        self.assertEqual(view['status'], 'READY')
        self.assertEqual(view['budget']['original_max_compute_ms'], 10000)
        self.assertEqual(view['budget']['max_compute_ms'], 20000)
        view = self.advance(study, 'family')
        self.assertEqual(self.attempts(view)[-1]['body']['continuation_id'], grant['id'])
        self.assertIn(grant['id'], self.attempts(view)[-1]['source_refs'])
        with self.assertRaises(Conflict): self.op('continue_study', **{**request, 'key': 'stale-checkpoint'})

    def test_restart_recovers_native_single_and_family_orphans_at_full_reservation(self):
        studies = {kind: self.prepare('orphan-' + kind, kind) for kind in ('single', 'family')}
        for kind, study in studies.items():
            world = study['body']['manifest']['worlds'][0]
            with self.broker._transaction():
                self.broker._event('controller', 'information_study_reserved', study_id=study['id'], reservation={
                    'attempt_id': 'orphan-' + kind, 'world_id': world['id'], 'compute_ms': 10000, 'storage_bytes': 256 * MIB})
                self.broker._event('controller', 'bound_computation_started', attempt_id='orphan-' + kind,
                    kind='information_study', input_ref=self.execution['id'], retained_input_id=study['id'])
        self.broker.close(); self.broker = Broker(self.directory); self.token = self.broker.admin_token
        for kind, study in studies.items():
            view = self.view(study, kind)
            self.assertEqual(view['status'], 'ORPHAN_UNCERTAIN')
            self.assertEqual(view['budget']['charged_compute_ms'], 10000)
            self.assertEqual(view['budget']['charged_storage_bytes'], study['body']['initial_storage_bytes'] + 256 * MIB)
            self.assertEqual(self.advance(study, kind), view)
            with self.assertRaises(ERRORS): self.op('continue_study', **self.grant(study, view, key='orphan-' + kind))
        self.assertEqual(self.backend_calls, [])

    def test_prepare_transaction_failure_and_backup_restore_do_not_create_partial_native_authority(self):
        original_event = self.broker._event

        def fail(actor, action, **details):
            if action == 'information_study_key': raise RuntimeError('Synthetic final input event failure')
            return original_event(actor, action, **details)

        with patch.object(self.broker, '_event', side_effect=fail), self.assertRaises(RuntimeError): self.prepare('rollback')
        self.assertEqual(self.broker._db.execute("SELECT COUNT(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?",
                                               (SCHEMAS['single'][0],)).fetchone()[0], 0)
        study = self.prepare('rollback')
        self.advance(study)
        backup = self.root / 'native-backup'
        self.op('backup_bundle', destination=str(backup))
        self.broker.close()
        restored = self.root / 'restored'
        restore_bundle(backup, restored, self.directory / 'operator.key')
        self.broker = Broker(restored); self.token = self.broker.admin_token
        view = self.view(study)
        self.assertEqual(view['summary']['recorded_worlds'], 1)
        self.assertFalse((restored / 'native-runtime-cache').exists())
        next_view = self.advance(study)
        self.assertEqual(next_view['summary']['recorded_worlds'], 2)
        self.assertEqual(self.broker._artifact(study['id']), study)
        self.assertEqual(self.op('verify')['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
