"""Owned raw measurement certification must bind values and semantics to exact sources."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker, Denied
import test_binance_normalize as normalization_tests
from test_binance_quality import row


class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = normalization_tests.NormalizeTests()
        self.fixture.setUp()
        source = self.fixture.source(row()+row(1577837700000, close=1577838000000))
        self.result = self.fixture.run_normalize([source])
        self.broker = self.fixture.broker
        self.token = self.broker.admin_token

    def tearDown(self):
        self.fixture.tearDown()

    def certify(self, snapshot=None):
        return self.broker.call(self.token, 'certify_features',
            data_snapshot_id=(snapshot or self.result['snapshot'])['id'])

    def test_owned_full_replay_certificate_and_qualified_definitions(self):
        certificate = self.certify()
        body = certificate['body']
        self.assertEqual(body['status'], 'CERTIFIED')
        self.assertEqual(body['data_snapshot_id'], self.result['snapshot']['id'])
        self.assertIs(body['scientific_readiness'], False)
        definitions = self.broker.call(self.token, 'get_artifact', artifact_id=body['definitions_id'])
        self.assertEqual(definitions['data_class'], 'development')
        self.assertEqual(len(definitions['body']['definitions']), 9)
        self.assertEqual(definitions['body']['parameters'], {'delay_seconds': 5})
        self.assertIn(self.result['snapshot']['id'], definitions['exposure'])
        self.assertEqual(body['checks']['partition_cases'], 22)
        self.assertEqual(body['checks']['definition_cases'], 18)
        self.assertEqual(body['replay']['coverage']['null_values'], self.result['snapshot']['body']['coverage']['null_values'])
        status = self.broker.call(self.token, 'feature_certificate_status', certificate_id=certificate['id'])
        self.assertEqual(status['status'], 'CURRENT')
        with patch('trading_researcher.features.read_bundle', return_value={}):
            self.assertEqual(self.broker.call(self.token, 'feature_certificate_status', certificate_id=certificate['id'])['status'], 'STALE')

    def test_catalog_semantic_mutation_cannot_reuse_original_rows(self):
        snapshot = self.result['snapshot']['body']
        original = self.broker.call(self.token, 'get_artifact', artifact_id=snapshot['catalog_id'])
        catalog = deepcopy(original['body'])
        catalog['features']['BTCUSDT.close@binance-spot-15m-v1']['unit'] = 'count'
        replacement = self.broker.call(self.token, 'add_source', body=catalog, data_class='development')
        altered = self.broker.call(self.token, 'register_data_snapshot', catalog_id=replacement['id'],
            row_source_ids=snapshot['row_source_ids'], manifest=snapshot['manifest'])
        certificate = self.certify(altered)
        self.assertEqual(certificate['body']['status'], 'CERTIFICATION_GAP')
        self.assertIsNone(certificate['body']['definitions_id'])
        self.assertEqual(self.broker.call(self.token, 'inspect_feature_checks')['pending'], 0)

    def test_namespaces_and_worker_requests_are_denied_before_backup(self):
        for schema in ('feature-certificate/1', 'feature-definitions/1', 'feature-source-package/1'):
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                self.broker.call(self.token, 'add_source', body={'schema': schema}, data_class='development')
        worker = self.broker.call(self.token, 'register_worker', name='discover', role='discovery', capabilities=[])['token']
        with patch.object(self.broker, '_backup_bundle_external', side_effect=AssertionError('Unauthorized data access')):
            with self.assertRaises(Denied):
                self.broker.call(worker, 'certify_features', data_snapshot_id=self.result['snapshot']['id'])
        with self.assertRaises(Invalid):
            self.broker.call(self.token, 'certify_features', data_snapshot_id=self.result['snapshot']['id'], expected={})

    def test_cancellation_retains_interrupted_attempt_and_no_certificate(self):
        with patch('trading_researcher.features.run_validation', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.certify()
        view = self.broker.call(self.token, 'inspect_feature_checks')
        self.assertEqual(view['attempts'][0]['state'], 'INTERRUPTED')
        self.assertIsNone(view['attempts'][0]['certificate_id'])
        self.assertEqual(view['pending'], 0)


if __name__ == '__main__':
    unittest.main()
