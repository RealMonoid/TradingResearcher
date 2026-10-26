"""Additional fixed overrun/metadata regressions; synthetic offline transport only."""
import tempfile
import unittest
from unittest.mock import patch

import test_openai_provider_adversarial as fixed
from trading_researcher import openai_provider as api


class IndependentOpenAIMetadataTests(unittest.TestCase):
    def run_receipt(self, changes, *, exact_charge, expected_input=500, expected_output=4):
        with tempfile.TemporaryDirectory() as directory:
            provider = fixed.IndependentOpenAIProviderTests().provider(directory)
            endpoints = []
            def post(endpoint, payload, secret, deadline):
                endpoints.append(endpoint)
                if endpoint.endswith('/input_tokens'):
                    return {'object': 'response.input_tokens', 'input_tokens': 500}, 'req_count'
                return fixed.raw_response(fixed.tool_items(), **changes), 'req_independent'
            with patch.object(api, '_post', side_effect=post):
                first = provider.complete(fixed.request(provider.config), 0, 10)
                second = provider.complete(fixed.request(provider.config), 1, 10)
            self.assertEqual(endpoints.count('/v1/responses'), 1,
                             'An invalid receipt must halt subsequent inference')
            self.assertNotEqual(first['response']['status'], 'completed')
            self.assertIsNone(first['response'].get('output'))
            self.assertEqual(first['usage'], {'input_tokens': expected_input,
                'output_tokens': expected_output, 'cost_units': exact_charge})
            self.assertEqual(second['response']['status'], 'failed')
            state = api.SpendLedger(provider.budget_file, 5000000000).snapshot()
            self.assertTrue(state['halted'])
            self.assertEqual(state['charged_nano'], exact_charge)
            self.assertEqual(state['uncertain'], 0)
            self.assertEqual(state['dispatches'], 1)

    def test_input_token_overrun_halts_even_below_currency_reservation(self):
        self.assertEqual(api.cost_bound(20001, 0), 50002500)
        self.assertLess(50002500, 90960000)
        self.run_receipt({'usage': {'input_tokens': 20001, 'output_tokens': 0}},
                         exact_charge=50002500, expected_input=20001, expected_output=0)

    def test_output_token_overrun_halts_even_below_currency_reservation(self):
        self.assertEqual(api.cost_bound(0, 4097), 40970000)
        self.assertLess(40970000, 90960000)
        self.run_receipt({'usage': {'input_tokens': 0, 'output_tokens': 4097}},
                         exact_charge=40970000, expected_input=0, expected_output=4097)

    def test_json_valid_but_protocol_invalid_metadata_cannot_authorize_tools(self):
        for changes in ({'id': {'unexpected': 'synthetic metadata'}}, {'status': []}):
            with self.subTest(changes=changes):
                self.run_receipt(changes, exact_charge=1290000)

    def test_noncanonical_metadata_never_loses_the_known_usage_charge(self):
        self.run_receipt({'id': float('nan')}, exact_charge=1290000)


if __name__ == '__main__':
    unittest.main()
