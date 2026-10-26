"""Fixed identity/time provenance checks; no live model or credential access."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import test_openai_provider_adversarial as fixed
import test_provider_usage_adversarial as usage_fixed
from trading_researcher import openai_provider as api
from trading_researcher import provider_usage
from trading_researcher.codec import canonical
from trading_researcher.errors import Conflict


def identity(*, reported=None):
    return {'requested_model': 'gpt-6.1-sol', 'reported_model': reported,
            'catalog_name': 'GPT-6.1 Sol', 'catalog_version': '6.1',
            'catalog_source': 'https://developers.openai.com/api/docs/models/gpt-6.1-sol',
            'immutable_snapshot_id': None, 'immutable_snapshot_status': 'UNKNOWN'}


def receipt(model_identity):
    result = usage_fixed.receipt()
    result['model_identity'] = deepcopy(model_identity)
    return result


def metadata(model_identity):
    return {'run_id': 'same-run', 'epoch_id': 'same-epoch', 'worker': 'first',
            'ordinal': 0, 'model': model_identity['requested_model'],
            'prompt_version': 'separate-prompt/99', 'counted_input_tokens': 500,
            'model_identity': deepcopy(model_identity)}


def legacy(path):
    old_metadata = {'model': 'gpt-6.1-sol', 'run_id': 'legacy-run',
                    'prompt_version': 'legacy-prompt/99'}
    old_receipt = usage_fixed.receipt()
    db = sqlite3.connect(path)
    try:
        db.execute('CREATE TABLE budget(singleton INTEGER PRIMARY KEY,cap INTEGER NOT NULL)')
        db.execute('CREATE TABLE dispatches(id TEXT PRIMARY KEY,request_hash TEXT NOT NULL,reserved INTEGER NOT NULL,charged INTEGER,state TEXT NOT NULL)')
        db.execute('CREATE TABLE token_metadata(id TEXT PRIMARY KEY,created_at INTEGER NOT NULL,body TEXT NOT NULL)')
        db.execute('CREATE TABLE usage_receipts(id TEXT PRIMARY KEY,body TEXT NOT NULL)')
        db.execute('INSERT INTO budget VALUES(1,5000000000)')
        db.execute("INSERT INTO dispatches VALUES('legacy','payload',90960000,1290000,'settled')")
        db.execute('INSERT INTO token_metadata VALUES(?,?,?)', ('legacy', 100, canonical(old_metadata)))
        db.execute('INSERT INTO usage_receipts VALUES(?,?)', ('legacy', canonical(old_receipt)))
        db.commit()
    finally:
        db.close()
    return old_metadata, old_receipt


class IndependentProviderIdentityTests(unittest.TestCase):
    def test_admission100_settlement200_have_distinct_exact_utc_times(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = api.SpendLedger(Path(directory) / 'spend.sqlite3', 5000000000)
            with patch.object(api.time, 'time', return_value=100):
                dispatch = ledger.reserve('timed', 90960000, key='timed', metadata=metadata(identity()))
            with patch.object(api.time, 'time', return_value=200):
                ledger.settle(dispatch, 1290000, receipt=receipt(identity(reported='gpt-6.1-sol')))
            report = ledger.report(); call = report['calls'][0]
            self.assertEqual(report['schema'], 'framework-provider-usage-report/3')
            self.assertEqual(call['admitted_at_utc'], '1970-01-01T00:01:40Z')
            self.assertEqual(call['settled_at_utc'], '1970-01-01T00:03:20Z')
            self.assertEqual(call['model_identity'], identity(reported='gpt-6.1-sol'))
            self.assertEqual(call['metadata']['prompt_version'], 'separate-prompt/99')
            self.assertNotEqual(call['model_identity']['catalog_version'], 'separate-prompt/99')

    def test_same_run_never_merges_different_reported_or_catalog_version_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = api.SpendLedger(Path(directory) / 'spend.sqlite3', 5000000000)
            identities = []
            for index, (reported, version) in enumerate((('synthetic-a', 'fixture-1'),
                                                       ('synthetic-b', 'fixture-1'),
                                                       ('synthetic-b', 'fixture-2'))):
                declared = identity()
                declared.update(requested_model='synthetic-model', catalog_name='Synthetic model fixture',
                                catalog_version=version, catalog_source='fixture:identity-grouping')
                served = {**declared, 'reported_model': reported}
                dispatch = ledger.reserve('payload', 90960000, key='fixture-' + str(index),
                                          metadata=metadata(declared))
                ledger.settle(dispatch, 1290000, receipt=receipt(served)); identities.append(served)
            report = ledger.report()
            self.assertEqual(len(report['runs']), 3)
            self.assertEqual(len(report['models']), 3)
            self.assertEqual({canonical(row['model_identity']) for row in report['runs']},
                             {canonical(value) for value in identities})
            self.assertTrue(all(row['exact_total_tokens'] == 504 for row in report['runs']))
            self.assertEqual(report['totals']['exact_total_tokens'], 1512)

    def test_legacy_read_never_backfills_catalog_revision_or_settlement_time(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legacy.sqlite3'; old_metadata, old_receipt = legacy(path)
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            call = provider_usage.read_usage_report(path)['calls'][0]
            self.assertEqual(call['model_identity'], {
                'requested_model': 'gpt-6.1-sol', 'reported_model': None,
                'catalog_name': None, 'catalog_version': None, 'catalog_source': None,
                'immutable_snapshot_id': None, 'immutable_snapshot_status': 'UNKNOWN'})
            self.assertEqual(call['admitted_at_utc'], '1970-01-01T00:01:40Z')
            self.assertIsNone(call['settled_at_utc'])
            self.assertEqual(call['metadata'], old_metadata)
            self.assertEqual(call['receipt'], old_receipt)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_additive_ledger_migration_does_not_retimestamp_historical_settlement(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legacy.sqlite3'; old_metadata, old_receipt = legacy(path)
            with patch.object(api.time, 'time', return_value=999999):
                ledger = api.SpendLedger(path, 5000000000)
            call = ledger.report()['calls'][0]
            self.assertIsNone(call['settled_at_utc'])
            self.assertIsNone(call['model_identity']['catalog_version'])
            self.assertEqual(call['metadata'], old_metadata)
            self.assertEqual(call['receipt'], old_receipt)
            self.assertEqual(call['admitted_at_utc'], '1970-01-01T00:01:40Z')

    def test_identical_replay_keeps_first_settlement_time_and_identity_change_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = api.SpendLedger(Path(directory) / 'spend.sqlite3', 5000000000)
            dispatch = ledger.reserve('immutable', 90960000, key='immutable', metadata=metadata(identity()))
            original = receipt(identity(reported='gpt-6.1-sol'))
            with patch.object(api.time, 'time', return_value=200):
                ledger.settle(dispatch, 1290000, receipt=original)
            with patch.object(api.time, 'time', return_value=900):
                ledger.settle(dispatch, 1290000, receipt=deepcopy(original))
                changed = deepcopy(original); changed['model_identity']['catalog_version'] = 'changed-fixture'
                with self.assertRaises(Conflict):
                    ledger.settle(dispatch, 1290000, receipt=changed)
            self.assertEqual(ledger.report()['calls'][0]['settled_at_utc'], '1970-01-01T00:03:20Z')

    def test_live_adapter_shape_retains_requested_before_reported_alias_without_snapshot_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'spend.sqlite3'
            provider = api.OpenAIResponsesProvider('never-read.env', path, fixed.config(),
                                                   epoch_id='identity-epoch', worker='first')
            before_inference = []
            with patch.object(api, '_key', return_value='sk-independent-unused'), \
                    patch.object(api.time, 'time', return_value=100) as clock:
                def post(endpoint, payload, secret, deadline):
                    if endpoint.endswith('/input_tokens'):
                        return {'object': 'response.input_tokens', 'input_tokens': 500}, 'req_count'
                    before_inference.append(provider_usage.read_usage_report(path)['calls'][0])
                    clock.return_value = 200
                    return fixed.raw_response(), 'req_identity'
                with patch.object(api, '_post', side_effect=post):
                    provider.complete(fixed.request(provider.config), 0, 10)
            self.assertEqual(len(before_inference), 1)
            self.assertEqual(before_inference[0]['model_identity'], identity())
            after = provider_usage.read_usage_report(path)['calls'][0]
            self.assertEqual(after['model_identity'], identity(reported='gpt-6.1-sol'))
            self.assertEqual(after['admitted_at_utc'], '1970-01-01T00:01:40Z')
            self.assertEqual(after['settled_at_utc'], '1970-01-01T00:03:20Z')


if __name__ == '__main__':
    unittest.main()
