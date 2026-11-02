"""Independent historical native-provenance metadata and ancestry fixtures.

The artifact map below substitutes only trusted lookup. Its literal identities
are fixture labels, not minted registry records or native certificates. The real
typed closure/profile validators and prior_knowledge traversal remain in use.
Only pinned ZIP metadata is read; no binary, cache, protected data, or study runs.
"""
from contextlib import ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from trading_researcher import native_environment, native_qualification as owner, native_runtime
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.data_use import prior_knowledge, protected_knowledge_gaps
from trading_researcher.errors import Denied


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = '1' * 64
RUNTIME = '2' * 64
SOURCE = '3' * 64
INPUT = '4' * 64
CERTIFICATE = '5' * 64
WRAPPER = '6' * 64
OPERATIONS = '7' * 64
ASSESSMENT = '8' * 64
FINAL_INPUT = '9' * 64
FINAL_ATTEMPT = 'a' * 64
UNRESOLVED = 'e' * 64
CORE = {ARCHIVE, RUNTIME, SOURCE, INPUT, CERTIFICATE}
PROFILE = 'stationary-native-runtime/1'
AUTHORITY = 'native_bootstrap_conformance_only'
BOOTSTRAP = ('import sys;sys.path.insert(0,sys.argv[1]);'
             'from trading_researcher.native_qualification_profile import child_entry;'
             'child_entry(sys.argv[2])')
ARCHIVE_SHA = '8c0458b745399a3bc92f912bb129ea1c6969466a0cad3239d5c361c23746dc21'
STREAM_SHA = '76c3fb49b827455afaf488104f0ee88788254446e4bcf1fad07f73b42cb4f533'
META = 1048576
LIMITS = {'max_compute_ms': 300000, 'max_storage_bytes': 268435456}
SOURCE_FILE = 'trading_researcher/native_backend.py'
SOURCE_BYTES = b'# Invented historical source bytes; never imported or certified.\n'
OPAQUE = 'opaque:prior-observation'


def descriptor(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def record(identity, body, *, authority=AUTHORITY, creator='controller', origin='controller',
           data_class='operations', sources=(), exposure=(), blobs=()):
    return {'id': identity, 'version': 'local-artifact/1', 'creator': creator, 'origin': origin,
            'data_class': data_class, 'authority': authority, 'source_refs': list(sources),
            'exposure': sorted(exposure), 'blob_refs': sorted(blobs), 'body': deepcopy(body)}


class MetadataBroker:
    """Lookup-only map and SQLite ID index; this cannot mint or execute anything."""
    def __init__(self, artifacts):
        self._db = sqlite3.connect(':memory:')
        self._db.execute('CREATE TABLE artifacts (id TEXT PRIMARY KEY, envelope TEXT NOT NULL)')
        self.replace(artifacts)

    def replace(self, artifacts):
        self.artifacts = deepcopy(artifacts)
        self._db.execute('DELETE FROM artifacts')
        self._db.executemany('INSERT INTO artifacts VALUES (?, ?)',
            [(identity, canonical({key: value for key, value in item.items() if key != 'id'}))
             for identity, item in self.artifacts.items()])

    def _artifact(self, identity):
        if identity not in self.artifacts:
            raise Denied('Fixture artifact unavailable')
        return deepcopy(self.artifacts[identity])

    def _read_blob_bytes(self, *args, **kwargs):
        raise AssertionError('Historical metadata classification read source/archive/output bytes')

    def _require_usable_dependencies(self, *args, **kwargs):
        raise AssertionError('Historical metadata classification requested execution usability')

    def _dependency_use(self, *args, **kwargs):
        raise AssertionError('Historical metadata classification requested revocation/currentness status')


class NativeStudyProvenanceIndependentTests(unittest.TestCase):
    def setUp(self):
        fixture = ROOT / 'tests/fixtures/native-environment-checks-2026-11-02.zip'
        self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(),
                         'fda1c157fbf365f5a8826a9ba0e9f7d19fae5f36f7299bf7a770a9764524fd30')
        prefix = '.trf-runtime/native-runtime-2026-11-02/'
        with ZipFile(fixture) as archive:
            self.manifest = json.loads(archive.read(prefix + 'canonical-native-runtime-manifest.json'))
            preparation = json.loads(archive.read(prefix + 'canonical-runtime-preparation.json'))
            observed = json.loads(archive.read(prefix + 'environment-reference-observation.json'))
        self.assertEqual(digest(self.manifest),
                         '384f70b80d41878c3b7a35c7e3b7b981ea891aa6dabe5df79e9893ead707ee33')
        self.archive_size = preparation['archive_bytes']
        self.hosts = observed['host_images']
        self.graph = self.chain()
        self.broker = MetadataBroker(self.graph)
        self.addCleanup(self.broker._db.close)

    def chain(self, *, inherited=(), archive_sha=ARCHIVE_SHA, manifest=None):
        """Construct immutable metadata inputs; expected classifications are literal."""
        manifest = deepcopy(self.manifest if manifest is None else manifest)
        archive = {'sha256': archive_sha, 'size': self.archive_size}
        files = {SOURCE_FILE: descriptor(SOURCE_BYTES)}
        source_footprint = {SOURCE_FILE: descriptor(SOURCE_BYTES)['sha256']}
        archive_exposure = set(inherited)
        runtime_exposure = archive_exposure | {ARCHIVE}
        input_exposure = runtime_exposure | {RUNTIME, SOURCE}
        certificate_exposure = input_exposure | {INPUT}
        request = {'key': 'independent-historical-native-conformance', 'runtime_id': RUNTIME}
        initial_storage = self.archive_size + 2 * len(SOURCE_BYTES) + META
        capsule = {
            'schema': 'native-runtime-qualification-input/1', 'profile': PROFILE,
            'created_at': 1000, 'request': request, 'attempt_id': '0123456789abcdef' * 2,
            'runtime_id': RUNTIME, 'runtime_manifest': manifest, 'source_package_id': SOURCE,
            'source_footprint': source_footprint, 'runtime_identity': manifest['runtime_identity'],
            'host_images': self.hosts, 'limits': LIMITS, 'initial_storage_bytes': initial_storage,
            'scientific_readiness': False,
        }
        gold = {'schema': 'native-runtime-conformance-result/1', 'profile': PROFILE,
                'tests': 13, 'failures': 0, 'errors': 0, 'skipped': 0, 'draws': 59997,
                'native_lengths': [4, 8, 16], 'scientific_readiness': False,
                'complete_result_sha256': '720ac237f2ad3e29a5a9d94191af68a90a549f476c6e0f2d5bae36b537901b09',
                'complete_stream_sha256': STREAM_SHA}
        proofs = []
        for phase in ('generate', 'replay'):
            proof_request = {
                'profile': PROFILE, 'input_id': INPUT, 'runtime_id': RUNTIME,
                'runtime_manifest': manifest, 'host_images': self.hosts,
                'runtime_directory': str(ROOT / '.metadata-fixture-cache-never-created'),
                'phase': phase, 'stream_limit': 33554432, 'source_footprint': source_footprint,
            }
            proofs.append({'request': proof_request, 'request_hash': digest(proof_request),
                'result': gold, 'stream_blob': {'sha256': STREAM_SHA, 'size': 15143319},
                'environment_before': {'metadata_fixture_no_child_execution': True},
                'environment_after': {'metadata_fixture_no_child_execution': True}})
        outputs = {'generate/stream.jsonl': {'sha256': STREAM_SHA, 'size': 15143319},
                   'replay/expected-stream.jsonl': {'sha256': STREAM_SHA, 'size': 15143319}}
        return {
            ARCHIVE: record(ARCHIVE, {'schema': 'blob-source/1', 'created_at': 1000,
                'source_name': 'canonical-native-runtime.zip',
                'description': 'Metadata fixture; no native certificate was minted.', 'blob': archive},
                creator='operator', origin='source', authority='supplied_source_not_certified',
                exposure=archive_exposure, blobs=[archive_sha]),
            RUNTIME: record(RUNTIME, {'schema': 'native-runtime-package/1', 'created_at': 1000,
                'request': {'key': 'independent-runtime-fixture', 'archive_id': ARCHIVE, 'manifest': manifest},
                'manifest': manifest, 'archive': archive,
                'footprint': {'runtime_archive': archive_sha, 'runtime_manifest': digest(manifest)},
                'scientific_readiness': False}, authority='retained_native_runtime_not_certified',
                sources=[ARCHIVE], exposure=runtime_exposure, blobs=[archive_sha]),
            SOURCE: record(SOURCE, {'schema': 'native-qualification-source/1', 'profile': PROFILE,
                'created_at': 1000, 'files': files, 'footprint': source_footprint,
                'bootstrap_sha256': hashlib.sha256(BOOTSTRAP.encode()).hexdigest()},
                authority='retained_source_not_certified', blobs=[files[SOURCE_FILE]['sha256']]),
            INPUT: record(INPUT, capsule, sources=sorted([RUNTIME, SOURCE]), exposure=input_exposure),
            CERTIFICATE: record(CERTIFICATE, {'schema': 'native-runtime-qualification/1',
                'profile': PROFILE, 'created_at': 1000, 'request': request,
                'input_id': INPUT, 'attempt_id': capsule['attempt_id'], 'runtime_id': RUNTIME,
                'source_package_id': SOURCE, 'status': 'CERTIFIED',
                'report': {'profile': PROFILE, 'input_id': INPUT,
                           'source_footprint': source_footprint, 'proofs': proofs},
                'settlement': {'compute_ms': 1000, 'storage_bytes': initial_storage + 2 * 15143319 + META,
                               'usage_known': True},
                'failure': None, 'failures': [], 'output_blobs': outputs, 'scientific_readiness': False},
                sources=[INPUT], exposure=certificate_exposure, blobs=[STREAM_SHA]),
        }

    def recognize(self, graph=None, identity=CERTIFICATE):
        if graph is not None:
            self.broker.replace(graph)
        return owner.technical_provenance(self.broker, self.broker._artifact(identity))

    def assert_not_recognized(self, graph):
        self.broker.replace(graph)
        self.assertEqual(owner.technical_provenance(self.broker, graph[CERTIFICATE]), set())

    def wrapper(self, graph, *, sources=(), exposure=()):
        graph = deepcopy(graph)
        graph[WRAPPER] = record(WRAPPER, {'schema': 'synthetic-candidate-ancestry/1'},
            data_class='development', origin='source', authority='supplied_source_not_certified',
            sources=sources, exposure=exposure)
        self.broker.replace(graph)
        return prior_knowledge(self.broker, self.broker._artifact(WRAPPER))

    def test_owned_success_recognizes_exactly_the_five_bound_technical_metadata_ids(self):
        before = deepcopy(self.graph)
        self.assertEqual(self.recognize(), CORE)
        self.assertEqual(self.broker.artifacts, before)

    def test_historical_recognition_never_requires_currentness_rebuild_or_revocation_usability(self):
        forbidden = [
            (owner.NativeQualifications, '_require_inputs'),
            (owner.NativeQualifications, 'inspect'),
            (owner.NativeQualifications, '_source'),
            (owner.profile, 'capture_source'),
            (owner.profile, 'validate_report'),
            (owner.profile, 'execute'),
            (owner, '_runtime_identity'),
            (native_environment, 'current'),
            (native_environment, 'inputs_current'),
            (native_runtime.NativeRuntimes, '_raw'),
            (native_runtime.NativeRuntimes, '_materialize'),
            (native_runtime, 'materialize'),
        ]
        with ExitStack() as stack:
            for target, name in forbidden:
                stack.enter_context(patch.object(target, name,
                    side_effect=AssertionError(f'Historical provenance requested {name}')))
            self.assertEqual(self.recognize(), CORE)
            result = self.wrapper(self.graph, sources=[CERTIFICATE])
        self.assertEqual(set(result['technical_provenance_ids']), CORE)
        self.assertEqual(result['operations_knowledge_ids'], [])

    def test_runtime_retention_source_input_and_compatibility_info_alone_exempt_nothing(self):
        for identity in (ARCHIVE, RUNTIME, SOURCE, INPUT):
            with self.subTest(root=identity):
                self.assertEqual(self.recognize(identity=identity), set())
        graph = deepcopy(self.graph)
        graph[CERTIFICATE]['body'] = {'schema': 'native-implementation-info/1',
                                     'profile': PROFILE, 'status': 'CERTIFIED'}
        self.assert_not_recognized(graph)
        graph = {identity: item for identity, item in self.graph.items() if identity != CERTIFICATE}
        result = self.wrapper(graph, sources=[RUNTIME])
        self.assertEqual(result['technical_provenance_ids'], [])
        self.assertEqual(set(result['operations_knowledge_ids']), {ARCHIVE, RUNTIME})

    def test_gap_nonowned_generic_worker_and_malformed_results_exempt_no_archive(self):
        mutations = [
            lambda a: a['body'].update(status='CERTIFICATION_GAP'),
            lambda a: a.update(creator='untrusted-worker', origin='worker'),
            lambda a: a.update(authority='implementation_conformance_only'),
            lambda a: a['body'].update(schema='implementation-certificate/1'),
            lambda a: a['body'].update(profile='stationary-native-runtime/2'),
            lambda a: a.update(body=None),
            lambda a: a.update(body=[]),
            lambda a: a['body'].pop('input_id'),
        ]
        for index, mutate in enumerate(mutations):
            graph = deepcopy(self.graph)
            mutate(graph[CERTIFICATE])
            with self.subTest(case=index):
                self.assert_not_recognized(graph)

    def test_every_owned_core_record_and_genuine_archive_owner_are_required(self):
        for identity in (RUNTIME, SOURCE, INPUT, CERTIFICATE):
            for field, value in (('creator', 'operator'), ('origin', 'source'),
                                 ('data_class', 'development'), ('authority', 'unrelated_authority')):
                graph = deepcopy(self.graph)
                graph[identity][field] = value
                with self.subTest(identity=identity, field=field):
                    self.assert_not_recognized(graph)
        for field, value in (('creator', 'controller'), ('origin', 'controller'),
                             ('data_class', 'assessment'), ('authority', AUTHORITY)):
            graph = deepcopy(self.graph)
            graph[ARCHIVE][field] = value
            with self.subTest(archive_field=field):
                self.assert_not_recognized(graph)

    def test_missing_typed_closure_records_or_wrong_schemas_and_profiles_are_rejected(self):
        for identity in (ARCHIVE, RUNTIME, SOURCE, INPUT):
            graph = deepcopy(self.graph)
            del graph[identity]
            with self.subTest(missing=identity):
                self.assert_not_recognized(graph)
        for identity in (ARCHIVE, RUNTIME, SOURCE, INPUT, CERTIFICATE):
            graph = deepcopy(self.graph)
            graph[identity]['body']['schema'] += '-forged'
            with self.subTest(schema=identity):
                self.assert_not_recognized(graph)
        for identity in (SOURCE, INPUT, CERTIFICATE):
            graph = deepcopy(self.graph)
            graph[identity]['body']['profile'] = 'arbitrary-native-profile/1'
            with self.subTest(profile=identity):
                self.assert_not_recognized(graph)

    def test_certificate_exact_source_exposure_request_attempt_and_runtime_bindings_are_required(self):
        mutations = [
            lambda a: a.update(source_refs=[]),
            lambda a: a.update(source_refs=[SOURCE]),
            lambda a: a.update(exposure=[]),
            lambda a: a['body'].update(input_id=UNRESOLVED),
            lambda a: a['body'].update(attempt_id='fedcba9876543210' * 2),
            lambda a: a['body'].update(runtime_id=UNRESOLVED),
            lambda a: a['body'].update(source_package_id=UNRESOLVED),
            lambda a: a['body']['request'].update(key='different-original-request'),
            lambda a: a['body'].update(scientific_readiness=True),
            lambda a: a.update(blob_refs=[]),
        ]
        for index, mutate in enumerate(mutations):
            graph = deepcopy(self.graph)
            mutate(graph[CERTIFICATE])
            with self.subTest(case=index):
                self.assert_not_recognized(graph)

    def test_input_exact_source_runtime_manifest_exposure_limits_and_request_closure_are_required(self):
        mutations = [
            lambda a: a.update(source_refs=[]),
            lambda a: a.update(exposure=[]),
            lambda a: a.update(blob_refs=['f' * 64]),
            lambda a: a['body'].update(runtime_id=UNRESOLVED),
            lambda a: a['body'].update(source_package_id=UNRESOLVED),
            lambda a: a['body'].update(runtime_manifest={}),
            lambda a: a['body'].update(source_footprint={SOURCE_FILE: '0' * 64}),
            lambda a: a['body']['request'].update(runtime_id=UNRESOLVED),
            lambda a: a['body']['limits'].update(max_compute_ms=300001),
            lambda a: a['body'].update(scientific_readiness=0),
        ]
        for index, mutate in enumerate(mutations):
            graph = deepcopy(self.graph)
            mutate(graph[INPUT])
            with self.subTest(case=index):
                self.assert_not_recognized(graph)

    def test_retained_source_metadata_cannot_forge_descriptor_footprint_or_bootstrap_closure(self):
        mutations = [
            lambda a: a.update(source_refs=[OPERATIONS]),
            lambda a: a.update(exposure=[OPERATIONS]),
            lambda a: a.update(blob_refs=[]),
            lambda a: a['body'].update(files={}),
            lambda a: a['body']['files'][SOURCE_FILE].update(size=True),
            lambda a: a['body']['files'][SOURCE_FILE].update(sha256='A' * 64),
            lambda a: a['body']['files'][SOURCE_FILE].update(extra=1),
            lambda a: a['body'].update(footprint={SOURCE_FILE: '0' * 64}),
            lambda a: a['body'].update(bootstrap_sha256='0' * 64),
        ]
        for index, mutate in enumerate(mutations):
            graph = deepcopy(self.graph)
            mutate(graph[SOURCE])
            with self.subTest(case=index):
                self.assert_not_recognized(graph)

    def test_canonical_archive_and_manifest_membership_are_required_even_with_consistent_graph_edges(self):
        self.assert_not_recognized(self.chain(archive_sha='b' * 64))
        changed = deepcopy(self.manifest)
        first_dependency = next(iter(changed['dependencies']))
        changed['dependencies'][first_dependency]['version'] += '-unqualified'
        self.assert_not_recognized(self.chain(manifest=changed))
        changed = deepcopy(self.manifest)
        kernel = next(name for name in changed['files'] if name.startswith('_trf_stationary_native'))
        changed['files'][kernel]['sha256'] = '0' * 64
        self.assert_not_recognized(self.chain(manifest=changed))

    def test_runtime_and_archive_reference_closure_cannot_be_relabelled(self):
        mutations = [
            (RUNTIME, lambda a: a.update(source_refs=[])),
            (RUNTIME, lambda a: a.update(exposure=[])),
            (RUNTIME, lambda a: a.update(blob_refs=[])),
            (RUNTIME, lambda a: a['body']['request'].update(archive_id=UNRESOLVED)),
            (RUNTIME, lambda a: a['body'].update(footprint={})),
            (RUNTIME, lambda a: a['body']['archive'].update(size=1)),
            (ARCHIVE, lambda a: a.update(blob_refs=[])),
            (ARCHIVE, lambda a: a['body']['blob'].update(sha256='b' * 64)),
        ]
        for index, (identity, mutate) in enumerate(mutations):
            graph = deepcopy(self.graph)
            mutate(graph[identity])
            with self.subTest(case=index):
                self.assert_not_recognized(graph)

    def test_prior_knowledge_moves_seen_core_ids_to_technical_independently_of_traversal_order(self):
        orders = [sorted(CORE), sorted(CORE, reverse=True),
                  [SOURCE, INPUT, CERTIFICATE, ARCHIVE, RUNTIME]]
        for order in orders:
            with self.subTest(order=order):
                result = self.wrapper(self.graph, sources=order)
                self.assertEqual(set(result['artifact_ids']), CORE | {WRAPPER})
                self.assertEqual(set(result['technical_provenance_ids']), CORE)
                self.assertEqual(result['operations_knowledge_ids'], [])
                self.assertEqual(result['protected_knowledge_ids'], [])
                self.assertEqual(protected_knowledge_gaps(result), [])

    def test_technical_closure_preserves_unrelated_operations_protected_final_and_unresolved_ancestry(self):
        inherited = {OPERATIONS, ASSESSMENT, FINAL_INPUT, FINAL_ATTEMPT, UNRESOLVED, OPAQUE}
        graph = self.chain(inherited=inherited)
        graph[OPERATIONS] = record(OPERATIONS, {'schema': 'execution-observations/1', 'text': 'Invented fills'},
                                   creator='operator', origin='source', authority='supplied_source_not_certified')
        graph[ASSESSMENT] = record(ASSESSMENT, {'schema': 'synthetic-reserved-observations/1'},
                                   data_class='assessment', creator='operator', origin='source')
        graph[FINAL_INPUT] = record(FINAL_INPUT, {'schema': 'evaluator-calibration-input/1'})
        graph[FINAL_ATTEMPT] = record(FINAL_ATTEMPT, {'schema': 'evaluator-calibration-attempt/1'})
        self.assertEqual(self.recognize(graph), CORE)
        result = self.wrapper(graph, sources=[CERTIFICATE])
        self.assertEqual(set(result['artifact_ids']), CORE | {WRAPPER, OPERATIONS, ASSESSMENT,
                                                            FINAL_INPUT, FINAL_ATTEMPT})
        self.assertEqual(set(result['technical_provenance_ids']), CORE)
        self.assertEqual(set(result['operations_knowledge_ids']), {OPERATIONS, FINAL_INPUT, FINAL_ATTEMPT})
        self.assertEqual(set(result['protected_knowledge_ids']), {ASSESSMENT, FINAL_INPUT, FINAL_ATTEMPT})
        self.assertEqual(set(result['unresolved_exposure_refs']), {UNRESOLVED, OPAQUE})
        self.assertEqual(protected_knowledge_gaps(result), [
            'PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY',
            'OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT',
            'UNRESOLVED_CANDIDATE_EXPOSURE',
        ])

    def test_bad_or_missing_successful_certificate_cannot_exempt_its_archive_in_real_traversal(self):
        graph = deepcopy(self.graph)
        graph[CERTIFICATE]['body']['status'] = 'CERTIFICATION_GAP'
        result = self.wrapper(graph, sources=[CERTIFICATE])
        self.assertEqual(result['technical_provenance_ids'], [])
        self.assertEqual(set(result['operations_knowledge_ids']), CORE)
        for root in (RUNTIME, SOURCE, INPUT):
            with self.subTest(root=root):
                without_certificate = {identity: item for identity, item in self.graph.items()
                                       if identity != CERTIFICATE}
                result = self.wrapper(without_certificate, sources=[root])
                self.assertEqual(result['technical_provenance_ids'], [])
                self.assertIn(root, result['operations_knowledge_ids'])

    def test_every_source_edge_is_still_required_and_opaque_exposures_remain_unresolved(self):
        graph = deepcopy(self.graph)
        graph[ARCHIVE]['source_refs'] = [UNRESOLVED]
        with self.assertRaises(Invalid):
            self.wrapper(graph, sources=[CERTIFICATE])
        result = self.wrapper(self.graph, sources=[CERTIFICATE], exposure=[UNRESOLVED, OPAQUE])
        self.assertEqual(set(result['technical_provenance_ids']), CORE)
        self.assertEqual(set(result['unresolved_exposure_refs']), {UNRESOLVED, OPAQUE})


if __name__ == '__main__':
    unittest.main()
