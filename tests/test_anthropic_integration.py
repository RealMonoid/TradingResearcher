"""Actual controller/adapter machinery with mocked HTTPS; not actual vendor calls."""
from pathlib import Path
import unittest
from unittest.mock import patch

import test_researcher as support
from test_anthropic_provider import raw_response
from trading_researcher import anthropic_provider as claude
from trading_researcher import openai_provider as openai
from trading_researcher.codec import canonical
from trading_researcher.researcher import run_research_once


class OfflineOpenAI(openai.OpenAIResponsesProvider):
    def complete(self, request, ordinal, timeout):
        def post(endpoint, payload, secret, deadline):
            if endpoint.endswith('/input_tokens'):
                return {'object': 'response.input_tokens', 'input_tokens': 100}, 'req_count'
            if ordinal == 0:
                items = [{'type': 'function_call', 'id': 'fc_fixture', 'call_id': 'call_fixture',
                          'name': 'capabilities', 'arguments': '{}', 'status': 'completed'}]
            else:
                items = [{'type': 'message', 'role': 'assistant', 'content': [
                    {'type': 'output_text', 'text': canonical(support.final('Private OpenAI fixture idea'))}]}]
            return {'id': 'resp_fixture', 'model': openai.MODEL, 'status': 'completed', 'service_tier': 'default',
                    'usage': {'input_tokens': 100, 'output_tokens': 20}, 'output': items}, 'req_openai'
        with patch.object(openai, '_key', return_value='synthetic-openai'), patch.object(openai, '_post', side_effect=post):
            return super().complete(request, ordinal, timeout)


class OfflineAnthropic(claude.AnthropicMessagesProvider):
    def complete(self, request, ordinal, timeout):
        def post(endpoint, payload, secret, deadline, workspace_id):
            if endpoint.endswith('/count_tokens'):
                return {'input_tokens': 200}, 'req_count'
            if ordinal == 0:
                content = [{'type': 'thinking', 'thinking': '', 'signature': 'opaque-fixture-signature'},
                           {'type': 'tool_use', 'id': 'toolu_fixture', 'name': 'capabilities', 'input': {}}]
                return raw_response(content, 'tool_use'), 'req_claude'
            return raw_response(), 'req_claude'
        with patch.object(claude, '_key', return_value='synthetic-anthropic'), patch.object(claude, '_post', side_effect=post):
            return super().complete(request, ordinal, timeout)


class MixedAdapterIntegrationTests(unittest.TestCase):
    setUp = support.ResearcherTests.setUp
    tearDown = support.ResearcherTests.tearDown
    setup_epoch = support.ResearcherTests.setup_epoch
    calls = support.ResearcherTests.calls

    def test_mixed_native_tool_loops_share_budget_retain_versions_and_keep_isolation(self):
        path = Path(self.tmp.name) / 'shared-spend.sqlite3'
        first_config = openai.configuration(input_token_limit=5000, output_token_limit=1024)
        second_config = claude.configuration(aggregate_budget_nano=5000000000,
            budget_scope_ref='fixture-only', input_token_limit=5000, output_token_limit=1024)
        selections = {name: {'model': model, 'prompt_version': name + '/1',
                            'generation_parameters': {key: config}, 'max_output_tokens': 1024,
                            'call_timeout_seconds': 10, 'max_retries': 0}
                      for name, model, key, config in [
                          ('first', openai.MODEL, 'openai_responses', first_config),
                          ('second', claude.MODEL, 'anthropic_messages', second_config)]}
        self.setup_epoch(mode='live', model=openai.MODEL, currency='USD',
                         max_cost_units=5000000000, max_calls=4, max_output_tokens=1024,
                         perspective_profiles=selections)
        first = run_research_once(self.clients['first'], OfflineOpenAI('unused', path, first_config,
            epoch_id=self.epoch, worker='first'))
        second = run_research_once(self.clients['second'], OfflineAnthropic('unused', path, second_config,
            epoch_id=self.epoch, worker='second'))
        self.assertTrue(first['accepted'] and second['accepted'])
        self.assertFalse(first['scientific_authority'] or second['scientific_authority'])
        calls = self.calls()
        self.assertEqual([c['request']['model'] for c in calls], [openai.MODEL] * 2 + [claude.MODEL] * 2)
        self.assertNotIn('Private OpenAI fixture idea', canonical(calls[2]['request']))
        self.assertIn('Base observation', canonical(calls[2]['request']))
        self.assertIn('opaque-fixture-signature', canonical(calls[3]['request']))
        report = claude.SpendLedger(path, 5000000000).report()
        self.assertEqual(report['totals']['exact_total_tokens'], 680)
        self.assertEqual(report['money']['charged_nano'], 2900000)
        self.assertEqual(report['provider'], 'mixed')
        self.assertEqual(len(report['models']), 2)
        self.assertEqual({item['model_identity']['catalog_version'] for item in report['models']}, {'6.1', '5.5'})
        self.assertTrue(all(call['admitted_at_utc'] and call['settled_at_utc'] for call in report['calls']))
        self.assertEqual(self.admin.call('inspect_research_epoch', epoch_id=self.epoch)['usage'],
                         {'calls': 4, 'tokens': 680, 'cost_units': 2900000})
        self.assertEqual(self.admin.call('verify')['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
