"""Direct Messages protocol checks with synthetic responses and no external requests."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher import anthropic_provider as api
from trading_researcher.codec import Invalid, canonical
from trading_researcher.errors import Conflict


def config():
    return api.configuration(aggregate_budget_nano=5000000000, budget_scope_ref='fixture-only-not-authorization')


def request(settings):
    return {'model': api.MODEL, 'prompt_version': 'anthropic-fixture/1',
            'generation_parameters': {'anthropic_messages': deepcopy(settings)},
            'messages': [{'role': 'system', 'content': 'Return one JSON object; keep uncertainty.'},
                         {'role': 'user', 'content': 'Synthetic research context.'}],
            'tools': [{'name': 'capabilities', 'description': 'Read capabilities',
                       'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}}]}


def raw_response(content=None, stop_reason='end_turn'):
    return {'id': 'msg_fixture', 'model': api.MODEL, 'type': 'message', 'role': 'assistant',
            'stop_reason': stop_reason, 'stop_sequence': None,
            'content': content if content is not None else [{'type': 'text', 'text': canonical(
                {'status': 'final', 'record': {'kind': 'gap', 'content': {'text': 'Fixture gap',
                 'reason': 'No scientific evidence', 'reopen_condition': 'Independent admission'},
                 'scope': {}, 'source_refs': []}})}],
            'usage': {'input_tokens': 100, 'cache_creation_input_tokens': 30,
                      'cache_read_input_tokens': 70, 'output_tokens': 20,
                      'output_tokens_details': {'thinking_tokens': 8},
                      'service_tier': 'standard', 'inference_geo': 'global', 'speed': 'standard'}}


class AnthropicProviderTests(unittest.TestCase):
    def test_large_opaque_signature_is_replayed_without_an_arbitrary_text_limit(self):
        settings = config()
        blocks = [{'type': 'thinking', 'thinking': '', 'signature': 'x' * 9000},
                  {'type': 'tool_use', 'id': 'toolu_large', 'name': 'capabilities', 'input': {}}]
        result = api.parse_response(raw_response(blocks, 'tool_use'), 'req_fixture', settings)
        self.assertEqual(result['response']['status'], 'completed')
        self.assertEqual(result['response']['provider_content'], blocks)

    def test_boolean_hosted_usage_cannot_masquerade_as_zero_cost_requests(self):
        raw = raw_response()
        raw['usage']['server_tool_use'] = {'web_fetch_requests': False, 'web_search_requests': False}
        result = api.parse_response(raw, 'req_fixture', config())
        self.assertIsNone(result['usage'])
        self.assertEqual(result['response']['status'], 'unverified_response')

    def test_frozen_request_uses_native_system_tools_and_omitted_thinking(self):
        settings = config()
        original = request(settings)
        wire = api.wire_request(original, settings)
        self.assertEqual(wire['model'], 'claude-sonnet-5-5')
        self.assertEqual(wire['system'], original['messages'][0]['content'])
        self.assertEqual(wire['thinking'], {'type': 'adaptive', 'display': 'omitted'})
        self.assertEqual(wire['output_config'], {'effort': 'high'})
        self.assertEqual(wire['service_tier'], 'standard_only')
        self.assertEqual(wire['tools'][0]['input_schema'], original['tools'][0]['parameters'])
        self.assertNotIn('temperature', wire)
        self.assertNotIn('cache_control', canonical(wire))
        changed = deepcopy(original)
        changed['generation_parameters']['anthropic_messages']['effort'] = 'low'
        with self.assertRaises(Invalid):
            api.wire_request(changed, settings)

    def test_native_signature_and_tool_response_round_trip(self):
        settings = config()
        req = request(settings)
        blocks = [{'type': 'thinking', 'thinking': '', 'signature': 'opaque-signature'},
                  {'type': 'tool_use', 'id': 'toolu_fixture', 'name': 'capabilities', 'input': {}}]
        result = api.parse_response(raw_response(blocks, 'tool_use'), 'req_fixture', settings)
        self.assertEqual(result['response']['output'], {'status': 'tools', 'calls': [
            {'id': 'toolu_fixture', 'name': 'capabilities', 'arguments': {}}]})
        body = {'schema': 'provider-tool-result/1', 'tool_request': result['response']['output']['calls'][0],
                'result': {'status': 'ok', 'value': {'scientific_authority': False}}}
        req['messages'] += [{'role': 'assistant', 'content': canonical(result['response'])},
                            {'role': 'tool', 'content': canonical(body)}]
        wire = api.wire_request(req, settings)
        self.assertEqual(wire['messages'][1], {'role': 'assistant', 'content': blocks})
        self.assertEqual(wire['messages'][2]['content'][0], {'type': 'tool_result',
            'tool_use_id': 'toolu_fixture', 'content': canonical(body['result'])})
        bad = deepcopy(req)
        bad['messages'].pop()
        with self.assertRaises(Invalid):
            api.wire_request(bad, settings)
        bad = deepcopy(req)
        bad['messages'].append(bad['messages'][-1])
        with self.assertRaises(Invalid):
            api.wire_request(bad, settings)

    def test_cache_components_are_added_once_and_thinking_is_a_subset(self):
        result = api.parse_response(raw_response(), 'req_fixture', config())
        self.assertEqual(result['usage'], {'input_tokens': 200, 'output_tokens': 20, 'cost_units': 1000000})
        self.assertEqual(result['response']['token_usage_details'],
                         {'cached_input_tokens': 70, 'reasoning_output_tokens': 8})
        self.assertEqual(result['response']['provider_usage'], raw_response()['usage'])
        self.assertEqual(result['response']['model_identity']['catalog_version'], '5.5')
        self.assertIsNone(result['response']['model_identity']['immutable_snapshot_id'])

    def test_incomplete_refusal_and_unknown_stops_cannot_supply_a_result(self):
        for reason in ('max_tokens', 'refusal', 'pause_turn', 'stop_sequence',
                       'model_context_window_exceeded', 'future_stop'):
            with self.subTest(reason=reason):
                result = api.parse_response(raw_response(stop_reason=reason), 'req_fixture', config())
                self.assertNotEqual(result['response']['status'], 'completed')
                self.assertIsNone(result['response']['output'])
                self.assertEqual(result['usage']['input_tokens'], 200)
                self.assertEqual(result['response']['provider_content'], raw_response()['content'])

    def test_missing_usage_and_model_or_tariff_changes_do_not_guess_cost(self):
        examples = []
        for key, value in [('cache_creation_input_tokens', None), ('input_tokens', True),
                           ('service_tier', 'priority'), ('inference_geo', 'us'), ('speed', 'fast')]:
            raw = raw_response()
            raw['usage'][key] = value
            examples.append(raw)
        raw = raw_response()
        raw['model'] = 'other-model'
        examples.append(raw)
        for raw in examples:
            with self.subTest(raw=raw):
                result = api.parse_response(raw, 'req_fixture', config())
                self.assertIsNone(result['usage'])
                self.assertEqual(result['response']['status'], 'unverified_response')
                self.assertIsNone(result['response']['output'])

    def test_count_then_durable_reservation_before_one_inference_and_restart_report(self):
        with tempfile.TemporaryDirectory() as folder:
            provider = api.AnthropicMessagesProvider('unused.env', Path(folder) / 'budget.sqlite3', config(),
                                                     epoch_id='epoch', worker='second')
            operations = []
            def post(endpoint, payload, secret, deadline, workspace_id):
                operations.append(endpoint)
                self.assertNotIn('synthetic-key', canonical(payload))
                if endpoint.endswith('/count_tokens'):
                    return {'input_tokens': 200}, 'req_count'
                self.assertEqual(api.SpendLedger(provider.budget_file, 5000000000).snapshot()['pending'], 1)
                return raw_response(), 'req_inference'
            with patch.object(api, '_key', return_value='synthetic-key'), patch.object(api, '_post', side_effect=post):
                result = provider.complete(request(provider.config), 0, 10)
            self.assertEqual(operations, ['/v1/messages/count_tokens', '/v1/messages'])
            self.assertEqual(result['response']['status'], 'completed')
            report = api.SpendLedger(provider.budget_file, 5000000000).report()
            self.assertEqual(report['provider'], 'anthropic')
            self.assertEqual(report['totals']['exact_total_tokens'], 220)
            self.assertEqual(report['money']['charged_nano'], 1000000)
            self.assertEqual(report['calls'][0]['provider'], 'anthropic')
            self.assertTrue(report['calls'][0]['admitted_at_utc'].endswith('Z'))
            self.assertTrue(report['calls'][0]['settled_at_utc'].endswith('Z'))

    def test_count_over_limit_makes_no_inference_or_currency_reservation(self):
        with tempfile.TemporaryDirectory() as folder:
            provider = api.AnthropicMessagesProvider('unused.env', Path(folder) / 'budget.sqlite3', config())
            with patch.object(api, '_key', return_value='synthetic-key'), patch.object(api, '_post',
                    return_value=({'input_tokens': 20001}, 'req_count')) as post:
                result = provider.complete(request(provider.config), 0, 10)
            self.assertEqual(post.call_count, 1)
            self.assertEqual(result['response']['status'], 'input_limit')
            self.assertEqual(result['usage']['cost_units'], 0)
            self.assertEqual(api.SpendLedger(provider.budget_file, 5000000000).snapshot()['dispatches'], 0)

    def test_timeout_keeps_unknown_charge_and_blocks_another_inference(self):
        with tempfile.TemporaryDirectory() as folder:
            provider = api.AnthropicMessagesProvider('unused.env', Path(folder) / 'budget.sqlite3', config())
            operations = []
            def post(endpoint, *args):
                operations.append(endpoint)
                if endpoint.endswith('/count_tokens'):
                    return {'input_tokens': 200}, 'req_count'
                raise RuntimeError('synthetic-key must not appear in a failure artifact')
            with patch.object(api, '_key', return_value='synthetic-key'), patch.object(api, '_post', side_effect=post):
                result = provider.complete(request(provider.config), 0, 10)
                again = provider.complete(request(provider.config), 1, 10)
            self.assertIsNone(result['usage'])
            self.assertEqual(operations.count('/v1/messages'), 1)
            self.assertEqual(again['response']['status'], 'failed')
            self.assertNotIn('synthetic-key', canonical(result))
            ledger = api.SpendLedger(provider.budget_file, 5000000000)
            self.assertTrue(ledger.snapshot()['halted'])
            self.assertEqual(ledger.snapshot()['charged_nano'], 120960000)

    def test_cross_provider_report_keeps_one_cap_and_distinct_model_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = api.SpendLedger(Path(folder) / 'budget.sqlite3', 2000000)
            old = ledger.reserve('legacy-openai', 500000, metadata={'model': 'legacy-openai'})
            ledger.settle(old, 100000)
            other = ledger.reserve('anthropic', 1000000, metadata={
                'provider': 'anthropic', 'model': api.MODEL, 'model_identity': api.provider_identity()})
            parsed = api.parse_response(raw_response(), 'req_fixture', config())
            ledger.settle(other, 1000000, receipt={'usage': parsed['usage'],
                'token_details': parsed['response']['token_usage_details'],
                'model_identity': parsed['response']['model_identity']})
            report = ledger.report()
            self.assertEqual(report['provider'], 'mixed')
            self.assertEqual(report['providers'], ['anthropic', 'openai'])
            self.assertEqual([call['provider'] for call in report['calls']], ['openai', 'anthropic'])
            self.assertEqual(report['money']['available_nano'], 900000)
            with self.assertRaises(Conflict):
                api.SpendLedger(ledger.path, 2000001)


if __name__ == '__main__':
    unittest.main()
