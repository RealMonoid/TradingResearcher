"""Fixed token-accounting examples: subsets are never additional consumption."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher import openai_provider as api
from trading_researcher.errors import Conflict
from test_openai_provider import request, response


class ProviderUsageTests(unittest.TestCase):
    def test_provider_receipt_survives_restart_and_subsets_are_not_added(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'spend.sqlite3'
            provider=api.OpenAIResponsesProvider('unused.env',path,api.configuration(),
                epoch_id='epoch-one',worker='first')
            raw=response()
            raw['usage'].update(input_tokens_details={'cached_tokens':40},
                                output_tokens_details={'reasoning_tokens':8})
            with patch.object(api,'_key',return_value='sk-synthetic-only'), \
                    patch.object(api,'_post',side_effect=[
                        ({'object':'response.input_tokens','input_tokens':99},'req_count'),(raw,'req_result')]):
                result=provider.complete(request(provider.config),0,10)
            self.assertEqual(result['usage']['input_tokens'],100)
            report=api.SpendLedger(path,5000000000).report()
            self.assertEqual(report['totals']['known_input_tokens'],100)
            self.assertEqual(report['totals']['known_output_tokens'],20)
            self.assertEqual(report['totals']['exact_total_tokens'],120)
            self.assertEqual(report['totals']['known_cached_input_tokens'],40)
            self.assertEqual(report['totals']['known_reasoning_output_tokens'],8)
            self.assertEqual(report['runs'][0]['epoch_id'],'epoch-one')
            self.assertEqual(report['calls'][0]['metadata']['counted_input_tokens'],99)
            self.assertEqual(report['calls'][0]['receipt']['transport_request_id'],'req_result')
            self.assertNotIn('sk-synthetic',str(report))

    def test_unknown_usage_is_not_zero_and_known_totals_remain_available(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=api.SpendLedger(Path(directory)/'budget.sqlite3',1000)
            first=ledger.reserve('one',500,key='one')
            receipt={'usage':{'input_tokens':10,'output_tokens':3,'cost_units':200},
                     'token_details':{'cached_input_tokens':None,'reasoning_output_tokens':None}}
            ledger.settle(first,200,receipt=receipt)
            second=ledger.reserve('two',500,key='two')
            ledger.settle(second,None)
            report=ledger.report()
            self.assertEqual(report['totals']['known_total_tokens'],13)
            self.assertIsNone(report['totals']['exact_total_tokens'])
            self.assertEqual(report['totals']['unknown_usage_calls'],1)
            self.assertEqual(report['totals']['cached_detail_calls'],0)
            self.assertEqual(report['money']['charged_nano'],700)

    def test_optional_invalid_details_remain_unknown_without_erasing_base_usage(self):
        raw=response()
        raw['usage'].update(input_tokens_details={'cached_tokens':101},
                            output_tokens_details={'reasoning_tokens':True})
        result=api.parse_response(raw,'req_test',api.configuration())
        self.assertEqual(result['usage']['input_tokens'],100)
        self.assertEqual(result['response']['token_usage_details'],
                         {'cached_input_tokens':None,'reasoning_output_tokens':None})

    def test_receipt_cannot_be_backfilled_or_rewritten_after_settlement(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger=api.SpendLedger(Path(directory)/'budget.sqlite3',1000)
            identity=ledger.reserve('one',500,key='one')
            ledger.settle(identity,200)
            with self.assertRaises(Conflict):
                ledger.settle(identity,200,receipt={'usage':None,'token_details':{
                    'cached_input_tokens':None,'reasoning_output_tokens':None}})


if __name__=='__main__':unittest.main()
