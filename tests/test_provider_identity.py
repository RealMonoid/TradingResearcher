"""Explicit provider identity and host-clock attribution, never inferred snapshots."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher import openai_provider as api
from test_openai_provider import request,response


class ProviderIdentityTests(unittest.TestCase):
    def test_actual_adapter_persists_catalog_and_reported_identifier(self):
        with tempfile.TemporaryDirectory() as directory:
            provider=api.OpenAIResponsesProvider('unused.env',Path(directory)/'budget.sqlite3',api.configuration())
            with patch.object(api,'_key',return_value='sk-synthetic-only'),patch.object(api,'_post',side_effect=[
                ({'object':'response.input_tokens','input_tokens':100},'req_count'),(response(),'req_result')]):
                provider.complete(request(provider.config),0,10)
            call=api.SpendLedger(provider.budget_file,5000000000).report()['calls'][0]
            identity=call['model_identity']
            self.assertEqual(identity['catalog_name'],'GPT-6.1 Sol')
            self.assertEqual(identity['catalog_version'],'6.1')
            self.assertEqual(identity['requested_model'],'gpt-6.1-sol')
            self.assertEqual(identity['reported_model'],'gpt-6.1-sol')
            self.assertIsNone(identity['immutable_snapshot_id'])
            self.assertEqual(identity['immutable_snapshot_status'],'UNKNOWN')
            self.assertNotEqual(call['metadata']['prompt_version'],identity['catalog_version'])
            self.assertTrue(call['admitted_at_utc'].endswith('Z'))
            self.assertTrue(call['settled_at_utc'].endswith('Z'))

    def test_admission_and_settlement_times_are_distinct_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=api.SpendLedger(Path(directory)/'budget.sqlite3',1000)
            with patch.object(api.time,'time',return_value=100):
                identity=ledger.reserve('synthetic',500,key='one')
            with patch.object(api.time,'time',return_value=200):ledger.settle(identity,100)
            with patch.object(api.time,'time',return_value=300):ledger.settle(identity,100)
            call=ledger.report()['calls'][0]
            self.assertEqual(call['admitted_at_utc'],'1970-01-01T00:01:40Z')
            self.assertEqual(call['settled_at_utc'],'1970-01-01T00:03:20Z')
            self.assertEqual(call['created_at'],100)


if __name__=='__main__':unittest.main()
