"""Exact input reservation preserves full wire bytes and fixed provider ceilings."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_openai_provider import request
from trading_researcher import openai_provider as api
from trading_researcher.codec import Invalid, canonical


class CountedReservationTests(unittest.TestCase):
    def provider(self, path):
        return api.CountedOpenAIResponsesProvider(Path(path) / 'never-read.env', Path(path) / 'budget.sqlite3',
                                                  api.configuration(input_token_limit=40000, output_token_limit=6000))

    def test_whole_wire_is_unchanged_and_count_is_cached_by_exact_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider(directory)
            value = request(provider.config)
            before = canonical(value)
            with patch.object(api, '_key', return_value='synthetic-test-key'), patch.object(api, '_post',
                    return_value=({'object': 'response.input_tokens', 'input_tokens': 28110}, 'count-fixture')) as post:
                bounds = provider.reservation(value, 6000)
                self.assertEqual(bounds, {'input_token_bound': 28238, 'output_token_limit': 6000,
                                         'cost_bound_units': api.cost_bound(28238, 6000)})
                self.assertEqual(provider.reservation(value, 6000), bounds)
                self.assertEqual(post.call_count, 1)
                sent = post.call_args.args[1]
                wire = api.wire_request(value, provider.config)
                self.assertEqual(sent, {k: wire[k] for k in ('model', 'input', 'tools', 'reasoning', 'text', 'parallel_tool_calls')})
                value['messages'][-1]['content'] += ' Additional required source text.'
                provider.reservation(value, 6000)
                self.assertEqual(post.call_count, 2)
            self.assertNotIn('synthetic-test-key', canonical(provider.count_receipts))
            self.assertEqual(canonical(request(provider.config)), before)
            self.assertFalse((Path(directory) / 'budget.sqlite3').exists())

    def test_count_cannot_expand_frozen_input_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider(directory)
            with patch.object(api, '_key', return_value='synthetic-test-key'), patch.object(api, '_post',
                    return_value=({'object': 'response.input_tokens', 'input_tokens': 40001}, 'count-fixture')):
                with self.assertRaises(Invalid): provider.reservation(request(provider.config), 6000)

    def test_malformed_count_boolean_and_expired_configuration_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            for count in (True, -1, '10'):
                provider = self.provider(directory)
                with patch.object(api, '_key', return_value='synthetic-test-key'), patch.object(api, '_post',
                        return_value=({'object': 'response.input_tokens', 'input_tokens': count}, 'count-fixture')):
                    with self.assertRaises(Invalid): provider.reservation(request(provider.config), 6000)
            provider.config['expires_at'] = 1
            with patch.object(api, '_post') as post:
                with self.assertRaises(Invalid): provider.reservation(request(provider.config), 6000)
                post.assert_not_called()

    def test_dispatch_recounts_and_denies_drift_before_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider(directory)
            with patch.object(api, '_key', return_value='synthetic-test-key'), patch.object(api, '_post', side_effect=[
                    ({'object': 'response.input_tokens', 'input_tokens': 100}, 'preflight'),
                    ({'object': 'response.input_tokens', 'input_tokens': 229}, 'dispatch')]) as post:
                provider.reservation(request(provider.config), 6000)
                result = provider.complete(request(provider.config), 0, 10)
            self.assertEqual(result['response']['status'], 'input_limit')
            self.assertEqual(result['usage']['cost_units'], 0)
            self.assertEqual([call.args[0] for call in post.call_args_list], ['/v1/responses/input_tokens'] * 2)
            self.assertEqual(api.SpendLedger(Path(directory) / 'budget.sqlite3', 5000000000).snapshot()['dispatches'], 0)


if __name__ == '__main__': unittest.main()
