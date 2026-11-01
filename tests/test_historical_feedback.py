"""Genuine small raw fixture and the historical reader's bounded seams."""
from contextlib import closing
from copy import deepcopy
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid, canonical
from trading_researcher.errors import Denied
from trading_researcher.feedback import historical
from trading_researcher.features import read_bundle
import test_features as raw_fixtures


class HistoricalReaderBoundaries(unittest.TestCase):
    def test_no_worker_operation_or_generic_qualification_namespace(self):
        with tempfile.TemporaryDirectory() as root, closing(historical.HistoricalFeedbackBroker(root)) as broker:
            worker = broker.call(broker.admin_token,'register_worker',name='test',role='discovery',capabilities=[])
            with patch.object(broker,'_historical_bindings',side_effect=AssertionError('Must authenticate first')):
                with self.assertRaises(Denied):
                    broker.call(worker['token'],'qualify_historical_feedback',release_ids=['unread'])
            for schema in (historical.SCHEMA,'historical-feedback-qualification/999'):
                with self.subTest(schema=schema), self.assertRaises(Denied):
                    broker.call(broker.admin_token,'add_source',body={'schema':schema},data_class='development')
            with self.assertRaises(Invalid):
                broker.call(broker.admin_token,'qualify_historical_feedback',release_ids=[],status='CURRENT')

    def test_reader_has_no_public_operation_writes_or_provider_routes(self):
        with tempfile.TemporaryDirectory() as root, closing(historical.HistoricalFeedbackBroker(root)) as broker:
            before = broker._db.execute('SELECT count(*) FROM artifacts').fetchone()[0]
            with broker._historical_view(provisional=[]) as view:
                self.assertEqual(view._provider_routes,{})
                self.assertNotIn('admin_token',view.__dict__)
                for name in ('call','compile_exact','execute_exact','publish_paired_feedback',
                             'publish_breakout_feedback','qualify_historical_feedback','close'):
                    with self.subTest(name=name), self.assertRaises(Denied):
                        getattr(view,name)
                with self.assertRaises(Denied):view._transaction()
                with self.assertRaises(Denied):view._stage_blob_bytes(b'never stage')
                with self.assertRaises(sqlite3.OperationalError):
                    view._db.execute("INSERT INTO events(envelope) VALUES('{}')")
                with self.assertRaises(Denied):view._paired_compiled('unbound')
            self.assertEqual(broker._db.execute('SELECT count(*) FROM artifacts').fetchone()[0],before)


class HistoricalRawSeams(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = raw_fixtures.FeatureTests()
        cls.fixture.setUp()
        cls.certificate = cls.fixture.certify()
        assert cls.certificate['body']['status'] == 'CERTIFIED'
        directory = cls.fixture.broker.directory
        cls.fixture.broker.close()
        cls.broker = historical.HistoricalFeedbackBroker(directory)
        cls.fixture.fixture.broker = cls.broker
        cls.old = canonical(cls.broker._artifact(cls.certificate['id']))
        cls.bindings = [{'feature_certificate_id':cls.certificate['id'],
            'data_snapshot_id':cls.certificate['body']['data_snapshot_id']}]
        cls.bundle = read_bundle()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.tearDown()

    def test_addition_only_raw_check_keeps_old_status_and_bytes(self):
        added = {**self.bundle,'trading_researcher/historical_synthetic_addition.py':b'# Unexecuted addition\n'}
        with patch('trading_researcher.features.read_bundle',return_value=added), \
             patch.object(historical,'read_bundle',return_value=added):
            old, retained, current, original = self.broker._historical_raw(self.bindings)
            self.assertEqual(retained,self.bundle)
            self.assertEqual(current,added)
            self.assertEqual(original['snapshot']['id'],self.bindings[0]['data_snapshot_id'])
            self.assertEqual(self.broker._feature_certificate_status(None,old['id'])['status'],'STALE')
            self.assertEqual(canonical(self.broker._artifact(old['id'])),self.old)

    def test_changed_or_missing_original_source_is_not_addition_only(self):
        name = 'trading_researcher/features.py'
        changed = {**self.bundle,name:self.bundle[name]+b'\n# changed\n'}
        removed = {k:v for k,v in self.bundle.items() if k != name}
        for bundle in (changed,removed):
            with self.subTest(files=len(bundle)), patch.object(historical,'read_bundle',return_value=bundle), \
                 self.assertRaises(Invalid):
                self.broker._historical_raw(self.bindings)

    def test_protected_snapshot_is_denied_before_retained_source_or_rows(self):
        snapshot = deepcopy(self.broker._artifact(self.bindings[0]['data_snapshot_id']))
        snapshot['data_class'] = 'assessment'
        original = self.broker._artifact
        def altered(identity):
            return snapshot if identity == snapshot['id'] else original(identity)
        with patch.object(self.broker,'_artifact',side_effect=altered), \
             patch.object(self.broker,'_load_feature_package',side_effect=AssertionError('Protected source access')), \
             self.assertRaises(Invalid):
            self.broker._historical_raw(self.bindings)


if __name__ == '__main__':
    unittest.main()
