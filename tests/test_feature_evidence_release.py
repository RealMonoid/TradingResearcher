"""Actual context admission of narrowly released development feature evidence."""
from copy import deepcopy
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from trading_researcher.auxiliary import AuxiliaryResearch
from trading_researcher.codec import canonical
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.features import PROFILE, SCOPE, definitions as raw_definitions
from trading_researcher.storage import restore_bundle
import test_auxiliary_availability as availability_tests


REJECTIONS = availability_tests.REJECTIONS


class AvailabilityShapeTests(unittest.TestCase):
    def test_malformed_retained_candidate_universe_is_a_typed_gap_before_reads(self):
        from trading_researcher.auxiliary_availability import availability_packet
        ids = ['certificate', 'snapshot', 'catalog', 'definitions', 'idea']
        definition = {'id': 'definitions', 'body': {'input_refs': ['snapshot', 'catalog'],
            'definitions': raw_definitions(['BTCUSDT']), 'parameters': {'delay_seconds': 900}}}
        records = {
            'certificate': {'id': 'certificate', 'creator': 'controller', 'origin': 'controller',
                'data_class': 'development', 'authority': SCOPE['authority'],
                'body': {'schema': 'feature-certificate/1', 'profile': PROFILE, 'status': 'CERTIFIED',
                         'data_snapshot_id': 'snapshot', 'definitions_id': 'definitions'}},
            'snapshot': {'id': 'snapshot', 'creator': 'controller', 'origin': 'source', 'data_class': 'development',
                'body': {'schema': 'data-snapshot/1', 'catalog_id': 'catalog', 'manifest': {
                    'partition': 'development', 'availability': {'basis': 'assumed'}, 'universe': {
                        'start': '2020-01-01T00:00:00Z', 'end': '2020-01-01T00:45:00Z', 'instruments': ['BTCUSDT']}}}},
        }
        for malformed in (None, [], 'not a universe', 1):
            target = {'id': 'target', 'job_id': 'job', 'source_refs': ids, 'body': {
                'idea_id': 'idea', 'authorization_snapshot': ids, 'candidate': {'test_universe': malformed}}}
            host = SimpleNamespace(_artifact=lambda identity: deepcopy(records[identity]),
                _context=lambda identity: {'artifact_ids': ids}, _job=lambda identity: {'spec': {'context_id': 'original'}},
                _feature_certificate_status=Mock(side_effect=AssertionError('Malformed candidate source read')))
            with self.subTest(universe=malformed), self.assertRaises(REJECTIONS):
                availability_packet(host, {'artifact_ids': ids + ['target']}, {'feature_certificate_id': 'certificate'},
                                    'catalog', [definition], target)
            host._feature_certificate_status.assert_not_called()


class FeatureEvidenceReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        availability_tests.AuxiliaryAvailabilityTests.setUpClass.__func__(cls)
        cls.base_time = cls.broker._now()
        cls.broker.clock = lambda: cls.base_time + 10

    @classmethod
    def tearDownClass(cls):
        availability_tests.AuxiliaryAvailabilityTests.tearDownClass.__func__(cls)

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def context(self, epoch, research_time=None, certificate_id=None):
        args = {'role': 'formalizer', 'epoch': epoch,
                'artifact_ids': [self.idea['id'], self.catalog_id, self.definition_id,
                                 self.snapshot['id'], certificate_id or self.certificate['id']]}
        if research_time is not None:
            args['research_time'] = research_time
        return self.op('create_context', **args)

    def test_01_actual_release_enables_exact_context_with_time_and_epoch_fences(self):
        original = deepcopy(self.certificate)
        with self.assertRaises(Denied):
            self.context(7)
        release = self.op('release_feature_evidence', certificate_id=self.certificate['id'], target_epoch=7)
        self.assertEqual(release['creator'], 'controller')
        self.assertEqual(release['origin'], 'controller')
        self.assertEqual(release['data_class'], 'operations')
        self.assertEqual(release['authority'], 'development_feature_input_release_only')
        body = release['body']
        self.assertEqual(set(body), {'schema', 'certificate_id', 'data_snapshot_id', 'definitions_id',
                                    'target_epoch', 'created_at', 'scientific_readiness'})
        self.assertEqual(body, {'schema': 'feature-evidence-release/1', 'certificate_id': self.certificate['id'],
            'data_snapshot_id': self.snapshot['id'], 'definitions_id': self.definition_id,
            'target_epoch': 7, 'created_at': self.base_time + 10, 'scientific_readiness': False})
        self.assertEqual(set(release['source_refs']), {self.certificate['id'], self.snapshot['id'], self.definition_id})
        self.assertEqual(release, self.op('release_feature_evidence', certificate_id=self.certificate['id'], target_epoch=7))
        with self.assertRaises(Conflict):
            self.op('release_feature_evidence', certificate_id=self.certificate['id'], target_epoch=8)
        with self.assertRaises(Denied):
            self.context(6)
        with self.assertRaises(Denied):
            self.context(7, research_time=self.base_time + 9)
        admitted = self.context(7, research_time=self.base_time + 10)
        self.assertIn(release['id'], admitted['exposure'])
        self.assertIn(self.certificate['id'], admitted['artifact_ids'])
        self.assertEqual(self.broker._artifact(self.certificate['id']), original)
        packet = AuxiliaryResearch._auxiliary_packet_for_spec(self.broker, {
            'kind': 'formalization/v1', 'context_id': admitted['id'], 'research_epoch_id': 'synthetic-epoch',
            'allowed_workers': ['formalizer'], 'research_inputs': {'idea_id': self.idea['id'],
                'catalog_id': self.catalog_id, 'definition_ids': [self.definition_id],
                'feature_certificate_id': self.certificate['id']}})
        self.assertEqual(packet['availability_evidence']['certificate_id'], self.certificate['id'])
        self.assertNotIn(self.certificate['id'], [source['id'] for source in packet['sources']])
        self.assertFalse(self.broker._db.execute('SELECT 1 FROM releases WHERE artifact_id=?',
                                               (self.certificate['id'],)).fetchall())
        with tempfile.TemporaryDirectory() as directory:
            from pathlib import Path
            root = Path(directory)
            self.op('backup_bundle', destination=str(root / 'backup'))
            restore_bundle(root / 'backup', root / 'restored', self.broker.directory / 'operator.key')
            restored = Broker(root / 'restored', clock=lambda: self.base_time + 10)
            try:
                self.assertEqual(restored._artifact(release['id']), release)
                again = restored.call(restored.admin_token, 'create_context', role='formalizer', epoch=7,
                    artifact_ids=admitted['artifact_ids'], research_time=self.base_time + 10)
                self.assertEqual(canonical(again), canonical(admitted))
            finally:
                restored.close()

    def test_02_worker_generic_and_protected_requests_cannot_gain_a_grant(self):
        worker = self.op('register_worker', name='release-test-worker', role='formalizer', capabilities=[])['token']
        with patch.object(self.broker, '_feature_certificate_status', side_effect=AssertionError('Worker source read')) as status:
            with self.assertRaises(Denied):
                self.broker.call(worker, 'release_feature_evidence', certificate_id=self.certificate['id'], target_epoch=7)
        status.assert_not_called()
        with self.assertRaises(REJECTIONS):
            self.op('add_source', body={'schema': 'feature-evidence-release/1', 'certificate_id': self.certificate['id'],
                                       'target_epoch': 0}, data_class='development')
        generic = self.op('add_source', body={'schema': 'unrelated-work/1'}, data_class='development')
        mutations = [lambda a: a.update(creator='worker'), lambda a: a.update(origin='source'),
                     lambda a: a.update(data_class='assessment'),
                     lambda a: a.update(authority='supplied_source_not_certified')]
        original = self.broker._artifact
        for index, mutate in enumerate(mutations):
            altered = deepcopy(self.certificate)
            altered['id'] = 'unreleased-fixture-alias'
            mutate(altered)
            def artifact(identity):
                return deepcopy(altered) if identity == altered['id'] else original(identity)
            with self.subTest(index=index), patch.object(self.broker, '_artifact', artifact), \
                    patch.object(self.broker, '_feature_certificate_status', side_effect=AssertionError('Denied source read')) as status:
                with self.assertRaises(REJECTIONS):
                    self.op('release_feature_evidence', certificate_id=altered['id'], target_epoch=7)
                status.assert_not_called()
        with patch.object(self.broker, '_feature_certificate_status', side_effect=AssertionError('Non-certificate source read')) as status:
            with self.assertRaises(REJECTIONS):
                self.op('release_feature_evidence', certificate_id=generic['id'], target_epoch=7)
        status.assert_not_called()

    def test_03_revocation_prevents_reuse_of_an_existing_release(self):
        evidence = self.op('add_source', body={'schema': 'synthetic-release-defect/1'}, data_class='development')
        self.op('revoke_dependency', key='release-test-revocation', dependency_id=self.certificate['id'],
                reason='Synthetic actual revocation', evidence_refs=[evidence['id']])
        with self.assertRaises(REJECTIONS):
            self.op('release_feature_evidence', certificate_id=self.certificate['id'], target_epoch=7)
        with self.assertRaises(REJECTIONS):
            self.context(7)


if __name__ == '__main__':
    unittest.main()
