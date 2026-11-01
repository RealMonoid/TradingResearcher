"""Independent owned-certificate checks using temporary native registries.

One real retained-source 51-method conformance run supplies a closed read
fixture, cloned per test. No rows, features, provider, API key, research epoch,
scientific mapping, or spending authority is supplied. Direct stored-record
fault injection checks validator invariants; it is not an assertion that a
public caller can mint controller artifacts.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
import trading_researcher.exact_certification as owned
from trading_researcher.exact_certification import ExactRuntimeBroker
from trading_researcher import exact_runtime as runtime


REJECTIONS = (Invalid, Denied, Conflict)
# Independently matched against the qualified public core/outcome records.
GOLDEN = {
    'tests/test_exact_compositions.py': 'd8fd47254458f3f070e3c06046d669f3b3be92f9d6cf4f309ad4657df812e522',
    'tests/test_exact_compositions_review.py': '3fea890dbf601386c59f8e1142d6386c385d6ce39b2bcf320e628f66d3bc350d',
    'tests/test_exact_outcomes.py': '051bcc7f5400c0c2531caec56bf16ce63dcf7f8bb1c1c3d6d6fc6fcf77e85637',
    'tests/test_exact_outcomes_review.py': 'da064fd250b454a9ba016b463e622a2f6a0732780d7b0b060099c5a67567f4da',
    'tests/fixtures/exact_composition_shape_2026-11-01.json': 'd66f100e4eedc1a7e11894e6a0ad9777b5fc6298c9affea7686e583263fda88e',
}


class ExactCertificationReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture_temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.fixture_temp.cleanup)
        cls.fixture_path = Path(cls.fixture_temp.name) / 'qualified'
        broker = ExactRuntimeBroker(cls.fixture_path)
        checked = []
        real_child = runtime.run_child

        def forward_after_staging(bundle, mode, payload, directory, **kwargs):
            # Observe actual committed native blobs before forwarding the one
            # genuine child conformance run. No synthetic passing result.
            packages = broker._db.execute("SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=? ORDER BY rowid",
                                          ('exact-source-package/1',)).fetchall()
            if not packages:
                raise AssertionError('The child started before its owned source package was committed')
            package = broker._artifact(packages[-1]['id'])
            retained = broker._exact_package(package['id'])
            if retained != bundle or set(retained) != set(runtime.FILES):
                raise AssertionError('The staged source capsule differs from the dispatched child closure')
            for name, descriptor in package['body']['files'].items():
                if set(descriptor) != {'sha256', 'size'} or broker._read_blob_bytes(descriptor['sha256']) != bundle[name]:
                    raise AssertionError('A source descriptor/blob was not committed before dispatch')
            checked.append((mode, deepcopy(payload), package['id']))
            return real_child(bundle, mode, payload, directory, **kwargs)

        try:
            with patch.object(runtime, 'run_child', side_effect=forward_after_staging):
                cls.certificate = broker.certify_exact_runtime(broker.admin_token)
            if cls.certificate['body']['status'] != 'CERTIFIED':
                raise AssertionError(cls.certificate['body'])
            cls.certificate_id = cls.certificate['id']
            cls.package = broker._artifact(cls.certificate['body']['source_package_id'])
            cls.bundle = broker._exact_package(cls.package['id'])
            cls.before_child = checked
        finally:
            broker.close()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / 'registry'
        shutil.copytree(self.fixture_path, self.directory)
        self.broker = ExactRuntimeBroker(self.directory, exact_certificate_id=self.certificate_id)
        self.addCleanup(lambda: self.broker.close())

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def injected(self, original, mutate):
        envelope = deepcopy(original)
        envelope.pop('id')
        mutate(envelope)
        with self.broker._transaction():
            return self.broker._save_artifact(envelope)

    def revoke(self, identity, key):
        evidence = self.op('add_source', body={'synthetic_defect_evidence': key}, data_class='operations')['id']
        return self.op('revoke_dependency', key=key, dependency_id=identity,
                       reason='Synthetic technical-defect fixture; no market conclusion.', evidence_refs=[evidence])

    def test_actual_owned_certificate_commits_complete_sources_before_real_child(self):
        certificate, bundle = self.broker._require_exact_qualification()
        self.assertEqual(certificate, self.certificate)
        self.assertEqual(bundle, self.bundle)
        self.assertEqual(self.before_child, [('certify', {'profile': runtime.PROFILE}, self.package['id'])])
        self.assertEqual(certificate['creator'], 'controller')
        self.assertEqual(certificate['origin'], 'controller')
        self.assertEqual(certificate['data_class'], 'operations')
        self.assertEqual(certificate['authority'], 'exact_implementation_conformance_only')
        self.assertEqual(certificate['body']['schema'], 'exact-reference-certificate/1')
        self.assertEqual(certificate['body']['profile'], 'exact-reference-computation/1')
        self.assertFalse(certificate['body']['scientific_readiness'])
        self.assertEqual(certificate['source_refs'], [self.package['id']])
        child = certificate['body']['result']
        self.assertEqual(child['mode'], 'certify')
        self.assertEqual(child['result']['tests'], 51)
        self.assertEqual(child['result']['failures'], 0)
        self.assertFalse(child['result']['scientific_readiness'])
        self.assertEqual(child['environment']['isolation'], {
            'isolated': 1, 'no_site': 1, 'ignore_environment': 1, 'no_bytecode_writes': 1})
        self.assertEqual(len(bundle), 26)
        self.assertEqual(set(bundle), set(runtime.FILES))
        self.assertEqual({name: hashlib.sha256(bundle[name]).hexdigest() for name in GOLDEN}, GOLDEN)
        self.assertEqual(self.op('verify')['status'], 'PASS')
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM research_calls').fetchone()[0], 0)

    def test_explicit_same_id_restart_revalidates_and_storage_does_not_auto_select(self):
        self.broker.close()
        self.broker = ExactRuntimeBroker(self.directory)
        with self.assertRaises(Denied):
            self.broker._require_exact_qualification()
        self.broker.close()
        self.broker = ExactRuntimeBroker(self.directory, exact_certificate_id=self.certificate_id)
        certificate, bundle = self.broker._require_exact_qualification()
        self.assertEqual(certificate['id'], self.certificate_id)
        self.assertEqual(bundle, self.bundle)

    def test_only_operator_can_certify_without_staging_an_unauthorized_attempt(self):
        worker = self.op('register_worker', name='readonly-worker', role='reporter', capabilities=['draft/v1'])['token']
        before = self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]
        for token in (worker, 'not-a-capability'):
            with self.subTest(token_kind='worker' if token == worker else 'unknown'), self.assertRaises(Denied):
                self.broker.certify_exact_runtime(token)
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], before)
        self.assertEqual(self.broker._exact_certificate_id, self.certificate_id)

    def test_new_broker_reserves_package_and_certificate_namespaces(self):
        for schema in ('exact-source-package/1', 'exact-reference-certificate/1'):
            with self.subTest(schema=schema), self.assertRaises(Denied):
                self.op('add_source', body={'schema': schema}, data_class='operations')
        token = self.op('register_worker', name='writer', role='reporter', capabilities=['draft/v1'])['token']
        context = self.op('create_context', role='reporter', epoch=1, artifact_ids=[])['id']
        self.op('enqueue', key='namespace-only', spec={
            'kind': 'draft/v1', 'context_id': context, 'purpose': 'Reserved namespace guard only; no model.',
            'allowed_workers': ['writer'], 'max_attempts': 1, 'lease_seconds': 30,
            'deadline': int(time.time()) + 60, 'dependencies': []})
        lease = self.broker.call(token, 'claim')['lease']
        for schema in ('exact-source-package/1', 'exact-reference-certificate/1'):
            with self.subTest(schema=schema), self.assertRaises(Denied):
                self.broker.call(token, 'put_artifact', lease=lease, body={'schema': schema}, source_refs=[])

    def test_source_lookalikes_supplied_through_old_broker_never_qualify(self):
        self.broker.close()
        other = Broker(self.directory)
        try:
            fake_package = other.call(other.admin_token, 'add_source', body=deepcopy(self.package['body']), data_class='operations')['id']
            fake_certificate = other.call(other.admin_token, 'add_source', body=deepcopy(self.certificate['body']), data_class='operations')['id']
        finally:
            other.close()
        self.broker = ExactRuntimeBroker(self.directory, exact_certificate_id=fake_certificate)
        with self.assertRaises(REJECTIONS):
            self.broker._exact_package(fake_package)
        with self.assertRaises(REJECTIONS):
            self.broker._require_exact_qualification()

    def test_bad_package_metadata_and_descriptors_fail_with_typed_rejection(self):
        name = next(iter(self.package['body']['files']))
        changes = [
            lambda item: item['body'].update(bootstrap_sha256='0' * 64),
            lambda item: item['body']['footprint'].update({name: '0' * 64}),
            lambda item: item['body']['files'].pop(name),
            lambda item: item['body']['files'][name].update(size=item['body']['files'][name]['size'] + 1),
            lambda item: item['body']['files'][name].pop('size'),
            lambda item: item['body']['files'][name].update(unexpected='not in the native descriptor'),
            lambda item: item['body']['files'].update({name: None}),
            lambda item: item['body']['files'].update({name: []}),
            lambda item: item['body']['files'].update({'../outside.py': {'sha256': '0' * 64, 'size': 0}}),
        ]
        for index, change in enumerate(changes):
            injected = self.injected(self.package, change)
            with self.subTest(mutation=index), self.assertRaises(REJECTIONS):
                self.broker._exact_package(injected['id'])

    def test_certificate_status_identity_child_environment_and_result_are_checked(self):
        changes = [
            lambda item: item['body'].update(status='CERTIFICATION_GAP'),
            lambda item: item.update(origin='source'),
            lambda item: item.update(data_class='development'),
            lambda item: item.update(authority='supplied_source_not_certified'),
            lambda item: item['body'].update(scientific_readiness=True),
            lambda item: item['body']['result'].update(mode='compile'),
            lambda item: item['body']['result'].update(request_hash='0' * 64),
            lambda item: item['body']['result']['result'].update(tests=50),
            lambda item: item['body']['result'].update(environment={}),
            lambda item: item['body'].update(host_sources={}),
        ]
        for index, change in enumerate(changes):
            injected = self.injected(self.certificate, change)
            self.broker._exact_certificate_id = injected['id']
            with self.subTest(mutation=index), self.assertRaises(REJECTIONS):
                self.broker._require_exact_qualification()

    def test_corrupt_native_blob_cannot_be_read_as_a_source_capsule(self):
        descriptor = next(iter(self.package['body']['files'].values()))
        path = self.broker._blob_path(descriptor['sha256'])
        path.write_bytes(path.read_bytes() + b'\ncorruption in owned temporary copy\n')
        with self.assertRaises(Conflict):
            self.broker._exact_package(self.package['id'])

    def test_loaded_host_and_golden_expectation_mismatches_deny_current_use(self):
        with patch.dict(owned.LOADED, {owned.HOST_FILES[0]: '0' * 64}):
            with self.assertRaises(Invalid):
                self.broker._require_exact_qualification()
        name = next(iter(GOLDEN))
        with patch.dict(owned.GOLDEN_PINS, {name: '0' * 64}):
            with self.assertRaises(Invalid):
                self.broker._require_exact_qualification()
        self.assertEqual(self.broker._require_exact_qualification()[0]['id'], self.certificate_id)

    def test_child_failure_retains_owned_package_gap_and_does_not_select_it(self):
        self.broker._exact_certificate_id = None
        with patch.object(runtime, 'run_child', side_effect=RuntimeError('Explicit synthetic child failure')):
            failed = self.broker.certify_exact_runtime(self.broker.admin_token)
        self.assertEqual(failed['body']['status'], 'CERTIFICATION_GAP')
        self.assertIsNone(self.broker._exact_certificate_id)
        self.assertFalse(failed['body']['scientific_readiness'])
        self.assertIsNone(failed['body']['result'])
        self.assertEqual(failed['body']['error']['type'], 'RuntimeError')
        package = self.broker._exact_package(failed['body']['source_package_id'])
        self.assertEqual(package, self.bundle)
        with self.assertRaises(Denied):
            self.broker._require_exact_qualification()

    def test_package_revocation_covers_same_footprint_clones_and_typed_cert_descendants(self):
        clone = self.injected(self.package, lambda item: item['body'].update(created_at=item['body']['created_at'] + 1))
        revoked = self.revoke(self.package['id'], 'same-footprint')
        self.assertTrue({self.package['id'], clone['id'], self.certificate_id} <= set(revoked['body']['affected_artifact_ids']))
        for identity in (self.package['id'], clone['id'], self.certificate_id):
            with self.subTest(identity=identity), self.assertRaises(Denied):
                self.broker._require_usable_dependencies(identity)
        with self.assertRaises(Denied):
            self.broker._require_exact_qualification()
        self.assertEqual(self.op('get_artifact', artifact_id=self.certificate_id), self.certificate)

    def test_certificate_revocation_does_not_propagate_through_generic_provenance(self):
        self.revoke(self.certificate_id, 'certificate-only')
        self.assertEqual(self.broker._exact_package(self.package['id']), self.bundle)
        def provenance_only(item):
            item['body']['created_at'] += 1
            item['source_refs'] = sorted(set(item['source_refs']) | {self.certificate_id})
            item['exposure'] = sorted(set(item['exposure']) | {self.certificate_id})
        clone = self.injected(self.package, provenance_only)
        # Packages have no typed edge to an envelope's generic exposure. This
        # checks D083 propagation only; it does not issue a new certificate.
        self.broker._require_usable_dependencies(clone['id'])
        with self.assertRaises(Denied):
            self.broker._require_exact_qualification()

    def test_old_typed_package_revocation_delegates_without_revoking_exact_schema(self):
        legacy = self.injected(self.package, lambda item: item['body'].update(schema='reference-source-package/1'))
        revoked = self.revoke(legacy['id'], 'delegated-legacy-type')
        self.assertEqual(revoked['body']['selector']['schema'], 'reference-source-package/1')
        with self.assertRaises(Denied):
            self.broker._require_usable_dependencies(legacy['id'])
        # Equal footprints in a different versioned schema are not the same
        # revocation selector. This is typed propagation, not global tainting.
        self.assertEqual(self.broker._require_exact_qualification()[0]['id'], self.certificate_id)


if __name__ == '__main__':
    unittest.main()
