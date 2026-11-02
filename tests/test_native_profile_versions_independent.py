"""Independent profile-version boundaries; no native binary or numerical world.

Historical metadata comes from the unchanged v1 provenance fixture. Tiny real
Registry lifecycle cases reuse the existing five trusted qualifier seams. They
exercise version ownership/accounting, never claim binary conformance. The source
capture cases read pinned case bytes; they do not run those numerical cases.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import sqlite3
import threading
import unittest
from unittest.mock import patch

import test_native_qualification_independent as qualification_cases
import test_native_study_provenance_independent as provenance_cases
from test_native_qualification_independent import (
    SOURCES, LOG, LIMITS, META,
)
from test_native_study_provenance_independent import (
    SOURCE, INPUT, CERTIFICATE, RUNTIME, CORE, BOOTSTRAP,
)
from trading_researcher import native_qualification as owner
from trading_researcher import native_qualification_profile as profile
from trading_researcher.codec import canonical, digest, Invalid
from trading_researcher.errors import Conflict, Denied
from trading_researcher.evaluation_plans import footprint
from trading_researcher.native_runtime import NativeRuntimes
from trading_researcher.native_study_runs import NativeFamilyStudies


LEGACY = 'stationary-native-runtime/1'
CURRENT = 'stationary-native-runtime/2'
REJECTED = (Invalid, Conflict, Denied)
OLD_LOOP = '.trf-runtime/native-runtime-2026-11-02/canonical_draw_independent_cases.py'
OLD_LOOP_SHA = 'a2569b97280dbf88a0b10560f0c31f19193718f12a83d7e3261a64f42653ced3'
PACKING_SHA = '013a4061cbe0ef3588f6c30ad2f675baafafaaab9c42fd0b7195ad5dfc27e1a0'
ORIGINAL_CASES_SHA = '342dd443823df5015109768428e15a425b5fba113d5abee8f27bf94ac9dcc0a9'


class NativeProfileMetadataVersionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = provenance_cases.NativeStudyProvenanceIndependentTests('test_owned_success_recognizes_exactly_the_five_bound_technical_metadata_ids')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.broker = self.fixture.broker
        self.reader = owner.NativeQualifications(self.broker)

    def chain(self, source=LEGACY, capsule=LEGACY, certificate=LEGACY):
        graph = deepcopy(self.fixture.graph)
        for identity, version in ((SOURCE, source), (INPUT, capsule), (CERTIFICATE, certificate)):
            graph[identity]['body']['profile'] = version
        return graph

    def install(self, graph):
        self.broker.replace(graph)
        return self.reader

    def test_current_profile_is_explicit_v2_and_legacy_name_stays_explicit_v1(self):
        self.assertEqual(profile.PROFILE, CURRENT)
        self.assertEqual(profile.LEGACY_PROFILE, LEGACY)

    def test_structural_read_accepts_each_homogeneous_known_version_without_currentness(self):
        # A homogeneous v2 metadata chain with the old invented runtime does NOT
        # certify that runtime. Runtime membership is a separate test below.
        for version in (LEGACY, CURRENT):
            graph = self.chain(version, version, version)
            self.install(graph)
            with self.subTest(version=version):
                self.assertEqual(self.reader._source_metadata(SOURCE), graph[SOURCE])
                self.assertEqual(self.reader._input(INPUT), graph[INPUT])
                self.assertEqual(self.reader._certificate(CERTIFICATE), graph[CERTIFICATE])
                self.assertEqual(self.broker.artifacts, graph)

    def test_unknown_profile_is_never_read_as_known_version(self):
        for version in ('stationary-native-runtime/0', 'stationary-native-runtime/3',
                        'stationary-native-runtime/999', 'arbitrary-native/1', '', None):
            graph = self.chain(version, version, version)
            self.install(graph)
            with self.subTest(version=version), self.assertRaises(REJECTED):
                self.reader._certificate(CERTIFICATE)
            self.assertEqual(owner.technical_provenance(self.broker, graph[CERTIFICATE]), set())

    def test_all_cross_version_source_input_certificate_combinations_are_rejected(self):
        for source in (LEGACY, CURRENT):
            for capsule in (LEGACY, CURRENT):
                for certificate in (LEGACY, CURRENT):
                    if source == capsule == certificate: continue
                    graph = self.chain(source, capsule, certificate)
                    self.install(graph)
                    with self.subTest(source=source, capsule=capsule, certificate=certificate), self.assertRaises(REJECTED):
                        self.reader._certificate(CERTIFICATE)
                    self.assertEqual(owner.technical_provenance(self.broker, graph[CERTIFICATE]), set())
                    self.assertEqual(self.broker.artifacts, graph)

    def test_v1_retained_source_accepts_its_exact_old_loop_path_without_rebinding(self):
        graph = self.chain()
        body = graph[SOURCE]['body']
        body['files'][OLD_LOOP] = {'sha256': OLD_LOOP_SHA, 'size': 18146}
        body['footprint'][OLD_LOOP] = OLD_LOOP_SHA
        graph[SOURCE]['blob_refs'] = sorted({value['sha256'] for value in body['files'].values()})
        graph[INPUT]['body']['source_footprint'] = deepcopy(body['footprint'])
        self.install(graph)
        self.assertEqual(self.reader._source_metadata(SOURCE), graph[SOURCE])
        self.assertEqual(self.reader._input(INPUT), graph[INPUT])
        self.assertEqual(self.broker.artifacts, graph)
        changed = deepcopy(graph)
        value = changed[SOURCE]['body']['files'].pop(OLD_LOOP)
        wrong_path = '.trf-runtime/arbitrary-runtime-2026-11-02/canonical_draw_independent_cases.py'
        changed[SOURCE]['body']['files'][wrong_path] = value
        changed[SOURCE]['body']['footprint'].pop(OLD_LOOP)
        changed[SOURCE]['body']['footprint'][wrong_path] = OLD_LOOP_SHA
        self.install(changed)
        with self.assertRaises(REJECTED): self.reader._source_metadata(SOURCE)

    def test_v1_technical_provenance_remains_historical_and_old_runtime_is_not_current_member(self):
        graph = self.chain()
        self.install(graph)
        # The existing MetadataBroker forbids source/archive/cache/currentness
        # reads. Recognizing old technical ancestry grants no executable use.
        self.assertEqual(owner.technical_provenance(self.broker, graph[CERTIFICATE]), CORE)
        with self.assertRaises(REJECTED): profile.validate_runtime(graph[RUNTIME])
        self.assertEqual(self.broker.artifacts, graph)


class NativeProfileSourceVersionTests(unittest.TestCase):
    def test_current_capture_binds_exact_preexisting_21_cases_and_original_numerical_gold(self):
        source = profile.capture_source()
        checksums = {hashlib.sha256(raw).hexdigest() for raw in source.values()}
        self.assertIn(PACKING_SHA, checksums)
        self.assertIn(ORIGINAL_CASES_SHA, checksums)
        self.assertLessEqual(len(source), 128)
        self.assertLessEqual(sum(map(len, source.values())), 16 * META)
        expected = profile._expected_result()
        self.assertEqual((expected['profile'], expected['tests'], expected['draws']), (CURRENT, 21, 59997))
        self.assertEqual((expected['failures'], expected['errors'], expected['skipped']), (0, 0, 0))
        self.assertEqual(expected['complete_result_sha256'],
                         '720ac237f2ad3e29a5a9d94191af68a90a549f476c6e0f2d5bae36b537901b09')
        self.assertEqual(expected['complete_stream_sha256'],
                         '76c3fb49b827455afaf488104f0ee88788254446e4bcf1fad07f73b42cb4f533')

    def test_changed_packing_or_original_case_bytes_cannot_enter_current_capture(self):
        # Intercept either direct source reads or ZIP extraction. No fixture is
        # changed on disk, and each mutation must actually reach the capture.
        real_read = Path.read_bytes
        real_zip = profile.ZipFile
        for target in (PACKING_SHA, ORIGINAL_CASES_SHA):
            reached = []
            def replace(raw):
                if hashlib.sha256(raw).hexdigest() == target:
                    reached.append(target)
                    return raw + b'\n# Independently injected case-source drift\n'
                return raw
            def read(path): return replace(real_read(path))
            class Archive:
                def __init__(self, *args, **kwargs): self.inner = real_zip(*args, **kwargs)
                def __enter__(self): self.inner.__enter__(); return self
                def __exit__(self, *args): return self.inner.__exit__(*args)
                def read(self, *args, **kwargs): return replace(self.inner.read(*args, **kwargs))
                def __getattr__(self, name): return getattr(self.inner, name)
            with self.subTest(target=target), patch.object(Path, 'read_bytes', read), patch.object(profile, 'ZipFile', Archive):
                with self.assertRaises(REJECTED): profile.capture_source()
            self.assertTrue(reached, 'No assertion coverage: selected case-source mutation was never read')


class NativeProfileRegistryVersionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = qualification_cases.NativeQualificationIndependentTests('test_exact_key_replay_is_original_history_and_changed_runtime_conflicts')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.broker = self.fixture.broker
        self.reader = owner.NativeQualifications(self.broker)

    def seed_legacy(self, *, complete=True):
        """Trusted host-only historical fixture, not a newly issued certificate.

        Old schema/source/capsule/events are retained through the same Registry
        primitives as the existing independent fixture. No profile execution or
        binary claim occurs. The five profile seams remain deliberately synthetic.
        """
        broker, fixture = self.broker, self.fixture
        files = {name: broker._stage_blob_bytes(raw) for name, raw in SOURCES.items()}
        with broker._transaction():
            for value in files.values(): broker._register_blob(value)
            def save(body, *, refs=(), exposure=(), blobs=(), authority=owner.AUTHORITY):
                return broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
                    'data_class': 'operations', 'source_refs': sorted(refs), 'exposure': sorted(exposure),
                    'blob_refs': sorted(blobs), 'authority': authority, 'body': body})
            package = save({'schema': owner.SOURCE, 'profile': LEGACY, 'created_at': 999,
                'files': files, 'footprint': footprint(SOURCES),
                'bootstrap_sha256': hashlib.sha256(BOOTSTRAP.encode()).hexdigest()},
                blobs={value['sha256'] for value in files.values()}, authority=owner.SOURCE_AUTHORITY)
            request = {'key': 'retained-legacy-key', 'runtime_id': fixture.runtime['id']}
            refs = [fixture.runtime['id'], package['id']]
            capsule = save({'schema': owner.INPUT, 'profile': LEGACY, 'created_at': 999,
                'request': request, 'attempt_id': 'legacy-attempt-before-adoption',
                'runtime_id': fixture.runtime['id'], 'runtime_manifest': fixture.manifest,
                'source_package_id': package['id'], 'source_footprint': footprint(SOURCES),
                'runtime_identity': fixture.manifest['runtime_identity'], 'host_images': [],
                'limits': deepcopy(LIMITS), 'initial_storage_bytes': len(fixture.raw) + 2 * sum(map(len, SOURCES.values())) + META,
                'scientific_readiness': False}, refs=refs, exposure=set(refs) | set(fixture.runtime['exposure']))
            broker._event('controller', 'bound_computation_started', attempt_id=capsule['body']['attempt_id'],
                kind='native_runtime_qualification', input_ref=capsule['id'], retained_input_id=capsule['id'])
            certificate = None
            if complete:
                output = broker._stage_blob_bytes(LOG)
                broker._register_blob(output)
                certificate = save({'schema': owner.RESULT, 'profile': LEGACY, 'created_at': 999,
                    'request': request, 'attempt_id': capsule['body']['attempt_id'], 'input_id': capsule['id'],
                    'runtime_id': fixture.runtime['id'], 'source_package_id': package['id'], 'status': 'CERTIFIED',
                    'report': fixture.report(SOURCES, capsule),
                    'settlement': {'compute_ms': 1000, 'storage_bytes': 2 * META, 'usage_known': True},
                    'failure': None, 'failures': [], 'output_blobs': {'synthetic/transcript.txt': output},
                    'scientific_readiness': False}, refs=[capsule['id']],
                    exposure=set(capsule['exposure']) | {capsule['id']}, blobs=[output['sha256']])
                broker._event('controller', 'bound_computation_checked', attempt_id=capsule['body']['attempt_id'],
                              artifact_id=certificate['id'], status='CERTIFIED')
        return package, capsule, certificate

    def test_old_key_returns_immutable_original_certificate_without_new_dispatch(self):
        package, capsule, certificate = self.seed_legacy()
        with patch.object(profile, 'capture_source', side_effect=AssertionError('Old key captured current source')), \
                patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Old key rebuilt cache')), \
                patch.object(profile, 'execute', side_effect=AssertionError('Old key dispatched child')):
            returned = self.fixture.qualify(key='retained-legacy-key')
        self.assertEqual(returned, certificate)
        for item in (package, capsule, certificate): self.assertEqual(self.broker._artifact(item['id']), item)
        self.assertEqual(self.fixture.executions, [])
        self.assertEqual(len(self.fixture.artifacts(owner.INPUT)), 1)

    def test_v1_use_denies_before_source_capture_cache_or_child_even_with_all_trusted_seams(self):
        package, capsule, certificate = self.seed_legacy()
        with patch.object(profile, 'capture_source', side_effect=AssertionError('Legacy use captured source')), \
                patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Legacy use rebuilt cache')), \
                patch.object(profile, 'execute', side_effect=AssertionError('Legacy use dispatched child')):
            with self.assertRaises(REJECTED): self.reader._require_inputs(certificate['id'])
        self.assertEqual(self.broker._artifact(certificate['id']), certificate)
        self.assertEqual(self.fixture.executions, [])

    def test_v1_inspection_cannot_claim_current_even_when_synthetic_validator_accepts_everything(self):
        package, capsule, certificate = self.seed_legacy()
        first = self.fixture.inspect(certificate['id'])
        second = self.fixture.inspect(capsule['id'])
        self.assertEqual(first, second)
        self.assertEqual(first['status'], 'STALE')
        self.assertEqual(first['settlement'], certificate['body']['settlement'])
        self.assertEqual(first['certificate_id'], certificate['id'])
        self.assertFalse((self.fixture.directory / 'native-runtime-cache').exists())
        self.assertEqual(self.fixture.executions, [])
        for item in (package, capsule, certificate): self.assertEqual(self.broker._artifact(item['id']), item)

    def test_current_qualification_keeps_new_source_owner_when_old_bytes_are_identical(self):
        package, capsule, certificate = self.seed_legacy()
        current = self.fixture.qualify(key='explicit-current-key')
        new_capsule = self.broker._artifact(current['body']['input_id'])
        new_package = self.broker._artifact(current['body']['source_package_id'])
        self.assertEqual([item['body']['profile'] for item in (new_package, new_capsule, current)], [CURRENT] * 3)
        self.assertNotEqual(new_package['id'], package['id'])
        self.assertEqual(new_package['body']['files'], package['body']['files'])
        self.assertEqual(self.fixture.executions, [new_capsule['id']])
        self.assertEqual(self.fixture.qualify(key='retained-legacy-key'), certificate)
        for item in (package, capsule, certificate): self.assertEqual(self.broker._artifact(item['id']), item)

    def test_old_runtime_new_key_retains_current_gap_before_cache_or_child(self):
        package, capsule, certificate = self.seed_legacy()
        # Substitute only the current runtime-membership decision. Unsupported
        # input retains STARTED + GAP and charges; it is not a pre-input denial.
        self.fixture.runtime_gate.side_effect = Invalid('Old implementation is outside the current profile')
        with patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Unsupported old runtime materialized')) as materialize:
            current = self.fixture.qualify(key='new-key-old-implementation')
        self.assertEqual(current['body']['profile'], CURRENT)
        self.assertEqual(current['body']['status'], 'CERTIFICATION_GAP')
        self.assertIsNotNone(current['body']['failure'])
        self.assertTrue(current['body']['settlement']['usage_known'])
        self.assertGreaterEqual(current['body']['settlement']['storage_bytes'], META)
        materialize.assert_not_called()
        self.fixture.runner.assert_not_called()
        self.assertEqual(self.fixture.executions, [])
        self.assertEqual(len(self.fixture.artifacts(owner.INPUT)), 2)
        self.assertEqual(self.fixture.qualify(key='retained-legacy-key'), certificate)

    def test_legacy_interrupted_input_recovers_full_unknown_caps_without_retry_or_upgrade(self):
        package, capsule, certificate = self.seed_legacy(complete=False)
        self.fixture.reopen()
        self.broker = self.fixture.broker
        view = self.fixture.inspect(capsule['id'])
        self.assertEqual(view['status'], 'INTERRUPTED')
        self.assertIsNone(view['certificate_id'])
        self.assertEqual(view['settlement'], {'compute_ms': 300000, 'storage_bytes': 268435456, 'usage_known': False})
        self.assertEqual(len(view['attempts']), 1)
        with self.assertRaises(Conflict): self.fixture.qualify(key='retained-legacy-key')
        self.assertEqual(self.fixture.artifacts(owner.RESULT), [])
        self.assertEqual(self.broker._artifact(capsule['id']), capsule)
        self.assertEqual(self.broker._artifact(package['id']), package)
        self.assertEqual(self.fixture.executions, [])


class NativeStudyVersionAliasTests(unittest.TestCase):
    """Public prepare seam with an immutable historical input and no backend.

    The trusted v2 qualification resolver is explicitly substituted. Existing
    full Registry alias/resource tests own numerical and aggregate bookkeeping.
    This fixture isolates profile transition before any new event/input exists.
    """
    def setUp(self):
        self.old_id = '1' * 64
        self.current_id = '2' * 64
        source = {'trading_researcher/native_backend.py': b'# version-alias source only\n'}
        self.qualified = {'certificate': {'id': self.current_id}, 'runtime': {'id': '3' * 64,
            'body': {'manifest': {'synthetic_metadata_only': True}}},
            'capsule': {'body': {'host_images': []}}, 'source': source}
        self.request = {'key': 'original-v1-study', 'native_qualification_id': self.old_id,
            'plan_id': '4' * 64, 'execution_id': '5' * 64, 'diagnostics_id': '6' * 64,
            'profile': {'synthetic_original_inventory': 'unchanged', 'seed': 713}}
        self.db = sqlite3.connect(':memory:')
        self.addCleanup(self.db.close)
        self.db.row_factory = sqlite3.Row
        self.db.execute('CREATE TABLE artifacts(id TEXT PRIMARY KEY,envelope TEXT NOT NULL)')
        self.db.execute('CREATE TABLE events(seq INTEGER PRIMARY KEY,envelope TEXT NOT NULL)')
        test = self
        class Broker:
            _mutex = threading.RLock()
            _db = test.db
            def _binding_owner(self, token): return {'name': 'operator', 'role': 'operator'}
            def _artifact(self, identity):
                test.assertEqual(identity, test.study['id'])
                return deepcopy(test.study)
            def _event(self, *args, **kwargs): raise AssertionError('Version alias created a new event')
            def _save_artifact(self, *args, **kwargs): raise AssertionError('Version alias created a new capsule')
        self.runner = NativeFamilyStudies(Broker())
        current_binding = self.runner._binding(self.qualified)
        old_binding = {**current_binding, 'profile': LEGACY, 'qualification_id': self.old_id}
        # Independently preserve the original identity fields, rather than using
        # the implementation under test to author its own historical expected ID.
        old_identity = digest({name: self.request[name] for name in
                               ('plan_id', 'execution_id', 'diagnostics_id', 'profile')})
        body = {'schema': 'native-family-study-input/1', 'identity': old_identity,
            'request': deepcopy(self.request), 'native_binding': old_binding,
            'initial_storage_bytes': 1234, 'manifest': {'original_budget': {'max_compute_ms': 10000},
                'original_worlds': ['fixed-world'], 'spent_attempts': 1, 'charged_compute_ms': 10000}}
        envelope = {'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
            'data_class': 'development', 'authority': 'native_development_joint_family_study_not_scientific_admission',
            'body': body, 'source_refs': [self.old_id], 'exposure': [self.old_id], 'blob_refs': []}
        self.study = {'id': digest(envelope), **envelope}
        self.db.execute('INSERT INTO artifacts VALUES (?,?)', (self.study['id'], canonical(envelope)))
        event = {'actor': 'controller', 'action': 'information_study_key', 'details': {
            'key': self.request['key'], 'request_hash': digest(self.request), 'study_id': self.study['id']}}
        self.db.execute('INSERT INTO events VALUES (1,?)', (canonical(event),))

    def test_exact_old_study_key_returns_immutable_history_without_current_use(self):
        with patch.object(self.runner, '_qualified', side_effect=AssertionError('Historical key requested current use')):
            saved = self.runner._prepare_information_study_external('fixture-operator', deepcopy(self.request))
        self.assertEqual(saved, self.study)
        self.assertEqual(saved['body']['manifest']['charged_compute_ms'], 10000)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0], 1)

    def test_current_certificate_alias_cannot_retarget_old_profile_or_reset_spent_inventory(self):
        incoming = {**deepcopy(self.request), 'key': 'new-v2-alias', 'native_qualification_id': self.current_id}
        self.assertEqual(self.runner._study_identity(incoming), self.study['body']['identity'])
        with patch.object(self.runner, '_qualified', return_value=self.qualified):
            with self.assertRaises(Conflict): self.runner._prepare_information_study_external('fixture-operator', incoming)
        self.assertEqual(self.runner._study(self.study['id']), self.study)
        self.assertEqual(self.study['body']['native_binding']['profile'], LEGACY)
        self.assertEqual(self.study['body']['manifest']['charged_compute_ms'], 10000)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], 1)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM events').fetchone()[0], 1)


if __name__ == '__main__':
    unittest.main()
