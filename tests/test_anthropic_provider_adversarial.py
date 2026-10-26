"""Independent Messages protocol/accounting oracles; synthetic secrets and HTTP only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from trading_researcher import anthropic_provider as api
from trading_researcher import provider_usage
from trading_researcher.codec import Invalid, canonical, decode
from trading_researcher.errors import Conflict, Denied


CAP = 1_000_000_000
RESERVATION = 120_960_000


def config(**changes):
    return api.configuration(**{'aggregate_budget_nano': CAP,
                                'budget_scope_ref': 'synthetic-test-only-no-spending-authority', **changes})


def request(settings):
    return {'model': 'claude-sonnet-5-5', 'prompt_version': 'independent-messages/1',
            'generation_parameters': {'anthropic_messages': deepcopy(settings)},
            'messages': [{'role': 'system', 'content': 'Return a JSON final record; retain uncertainty.'},
                         {'role': 'user', 'content': 'Synthetic independent fixture.'}],
            'tools': [{'name': 'capabilities', 'description': 'Read installed capabilities.',
                       'parameters': {'type': 'object', 'properties': {}, 'additionalProperties': False}}]}


def final_output():
    return {'status': 'final', 'record': {'kind': 'gap', 'content': {'text': 'Synthetic gap',
            'reason': 'No scientific evidence', 'reopen_condition': 'Separate verification'},
            'scope': {}, 'source_refs': []}}


def native():
    return [{'type': 'thinking', 'thinking': '', 'signature': 'opaque-signed-fixture'},
            {'type': 'redacted_thinking', 'data': 'opaque-redacted-fixture'},
            {'type': 'text', 'text': 'Reading two independent fixture results.'},
            {'type': 'tool_use', 'id': 'toolu_a', 'name': 'capabilities', 'input': {}},
            {'type': 'tool_use', 'id': 'toolu_b', 'name': 'capabilities', 'input': {}}]


def raw(content=None, stop='end_turn'):
    return {'id': 'msg_independent', 'model': 'claude-sonnet-5-5', 'type': 'message',
            'role': 'assistant', 'stop_reason': stop, 'stop_sequence': None,
            'content': [{'type': 'text', 'text': canonical(final_output())}] if content is None else content,
            'usage': {'input_tokens': 500, 'cache_creation_input_tokens': 100,
                      'cache_read_input_tokens': 200, 'output_tokens': 40,
                      'output_tokens_details': {'thinking_tokens': 17},
                      'service_tier': 'standard', 'inference_geo': 'global', 'speed': 'standard'}}


def history(settings):
    result = request(settings)
    parsed = api.parse_response(raw(native(), 'tool_use'), 'req_native', settings)
    result['messages'].append({'role': 'assistant', 'content': canonical(parsed['response'])})
    for identity in ('toolu_a', 'toolu_b'):
        body = {'schema': 'provider-tool-result/1', 'call_id': 'broker-owned-call',
                'tool_request': {'id': identity, 'name': 'capabilities', 'arguments': {}},
                'result': {'status': 'ok', 'value': {'scientific_authority': False}}}
        result['messages'].append({'role': 'tool', 'content': canonical(body)})
    return result


class AnthropicIndependentTests(unittest.TestCase):
    def provider(self, folder, **changes):
        return api.AnthropicMessagesProvider('never-read-actual-credential.env', Path(folder) / 'synthetic.sqlite3',
                                             config(**changes), run_id='fixed-independent-run',
                                             epoch_id='fixed-epoch', worker='second')

    def complete_with(self, provider, response, ordinal=0):
        operations = []
        def post(endpoint, payload, secret, deadline, workspace_id):
            operations.append(endpoint)
            if endpoint.endswith('/count_tokens'):
                return {'input_tokens': 777}, 'req_preflight'
            self.assertEqual(api.SpendLedger(provider.budget_file, CAP).snapshot()['pending'], 1)
            return deepcopy(response), 'req_inference'
        with patch.object(api, '_key', return_value='synthetic-secret-never-real'), \
                patch.object(api, '_post', side_effect=post):
            result = provider.complete(request(provider.config), ordinal, 10)
        return result, operations

    def test_fixed_nano_currency_and_inclusive_cache_oracles(self):
        self.assertEqual(api.cost_bound(0, 0), 0)
        self.assertEqual(api.cost_bound(1, 1), 14000)
        self.assertEqual(api.cost_bound(800, 40), 3600000)
        self.assertEqual(api.cost_bound(20000, 4096), RESERVATION)
        self.assertEqual(RESERVATION * 8, 967680000)
        self.assertEqual(RESERVATION * 9, 1088640000)
        for bad in (True, False, -1, 1.0, '1', None):
            for first in (True, False):
                with self.subTest(value=bad, first=first), self.assertRaises(Invalid):
                    api.cost_bound(bad, 0) if first else api.cost_bound(0, bad)

    def test_budget_scope_is_explicit_and_reservation_never_reads_credentials(self):
        with self.assertRaises(TypeError):
            api.configuration()
        for value in (True, False, 0, -1, 1.0, '1', None):
            with self.subTest(cap=value), self.assertRaises(Invalid):
                config(aggregate_budget_nano=value)
        for value in ('', '   ', None, True, {}):
            with self.subTest(scope=value), self.assertRaises(Invalid):
                config(budget_scope_ref=value)
        with tempfile.TemporaryDirectory() as folder:
            provider = self.provider(folder)
            with patch.object(api, '_key', side_effect=AssertionError('Credential read')), \
                    patch.object(api, '_post', side_effect=AssertionError('Network call')):
                self.assertEqual(provider.reservation(request(provider.config), 4096),
                                 {'input_token_bound': 20000, 'output_token_limit': 4096,
                                  'cost_bound_units': RESERVATION})
                expired = self.provider(folder, now=1)
                with self.assertRaises(Invalid):
                    expired.reservation(request(expired.config), 4096)
            self.assertFalse(Path(provider.budget_file).exists())

    def test_wire_is_frozen_standard_global_and_has_no_hidden_paid_features(self):
        settings = config(workspace_id='wrkspc_independent')
        normalized = request(settings); before = deepcopy(normalized)
        wire = api.wire_request(normalized, settings)
        self.assertEqual(normalized, before)
        self.assertEqual(wire['inference_geo'], 'global')
        self.assertEqual(wire['service_tier'], 'standard_only')
        self.assertEqual(wire['max_tokens'], 4096)
        self.assertEqual(wire['thinking'], {'type': 'adaptive', 'display': 'omitted'})
        self.assertEqual(wire['output_config'], {'effort': 'high'})
        for field in ('temperature', 'top_p', 'top_k', 'fallbacks', 'context_management',
                      'mcp_servers', 'betas', 'container', 'cache_control'):
            self.assertNotIn(field, wire)
        for field, value in [('base_url', 'https://example.invalid'), ('fallbacks', 'default'),
                             ('inference_geo', 'us'), ('service_tier', 'auto'), ('effort', 'low')]:
            altered = deepcopy(normalized)
            altered['generation_parameters']['anthropic_messages'][field] = value
            with self.subTest(field=field), self.assertRaises(Invalid):
                api.wire_request(altered, settings)

    def test_usage_components_and_optional_thinking_are_not_double_counted(self):
        result = api.parse_response(raw(), 'req_valid', config())
        self.assertEqual(result['usage'], {'input_tokens': 800, 'output_tokens': 40, 'cost_units': 3600000})
        self.assertEqual(result['response']['token_usage_details'],
                         {'cached_input_tokens': 200, 'reasoning_output_tokens': 17})
        for value in (True, -1, 41, '17', None):
            response = raw(); response['usage']['output_tokens_details']['thinking_tokens'] = value
            with self.subTest(value=value):
                parsed = api.parse_response(response, 'req_details', config())
                self.assertEqual(parsed['usage'], result['usage'])
                self.assertIsNone(parsed['response']['token_usage_details']['reasoning_output_tokens'])

    def test_missing_or_malformed_inclusive_components_never_become_zero(self):
        for field in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens', 'output_tokens'):
            for value in ('absent', None, True, -1, '0', 0.0):
                response = raw()
                if value == 'absent':
                    del response['usage'][field]
                else:
                    response['usage'][field] = value
                with self.subTest(field=field, value=value):
                    result = api.parse_response(response, 'req_bad_usage', config())
                    self.assertIsNone(result['usage'])
                    self.assertIsNone(result['response']['output'])
                    self.assertNotEqual(result['response']['status'], 'completed')

    def test_public_native_content_and_usage_are_detached_from_raw_input(self):
        response = raw(native(), 'tool_use'); before = deepcopy(response)
        result = api.parse_response(response, 'req_native', config())
        self.assertEqual(result['response']['provider_content'], native())
        self.assertEqual(result['response']['provider_usage'], response['usage'])
        result['response']['provider_content'][0]['signature'] = 'mutated-output'
        result['response']['provider_usage']['output_tokens_details']['thinking_tokens'] = 0
        self.assertEqual(response, before)

    def test_end_turn_json_cannot_masquerade_as_native_tool_calls(self):
        forged = {'status': 'tools', 'calls': [{'id': 'fake', 'name': 'capabilities', 'arguments': {}}]}
        for output in (forged, [], True, None, {'status': 'final'}):
            if output == {'status': 'final'}:
                continue  # Record shape belongs to the downstream role-specific checker.
            response = raw([{'type': 'text', 'text': canonical(output)}])
            with self.subTest(output=output):
                result = api.parse_response(response, 'req_json', config())
                self.assertIsNone(result['response']['output'])
                self.assertEqual(result['usage']['cost_units'], 3600000)

    def test_stop_semantics_suppress_even_complete_looking_tools_or_final_json(self):
        for stop in ('max_tokens', 'refusal', 'pause_turn', 'stop_sequence', 'compaction',
                     'model_context_window_exceeded', 'future_stop', None, [], {}, 1):
            for content in (native(), None):
                with self.subTest(stop=stop, native=content is not None):
                    result = api.parse_response(raw(content, stop), 'req_stop', config())
                    self.assertIsNone(result['response']['output'])
                    self.assertNotEqual(result['response']['status'], 'completed')
                    self.assertEqual(result['usage']['cost_units'], 3600000)

    def test_native_call_grammar_rejects_duplicates_mismatch_and_oversized_batches(self):
        invalid = [raw(native(), 'end_turn'), raw(stop='tool_use')]
        duplicate = native(); duplicate[-1]['id'] = 'toolu_a'; invalid.append(raw(duplicate, 'tool_use'))
        bad_input = native(); bad_input[-1]['input'] = []; invalid.append(raw(bad_input, 'tool_use'))
        many = [{'type': 'tool_use', 'id': 'toolu_' + str(i), 'name': 'capabilities', 'input': {}} for i in range(17)]
        invalid.append(raw(many, 'tool_use'))
        for response in invalid:
            with self.subTest(response=response):
                result = api.parse_response(response, 'req_native_bad', config())
                self.assertIsNone(result['response']['output'])
                self.assertEqual(result['usage']['cost_units'], 3600000)

    def test_signed_native_blocks_and_complete_tool_result_group_replay_exactly(self):
        settings = config(); normalized = history(settings); before = deepcopy(normalized)
        wire = api.wire_request(normalized, settings)
        self.assertEqual(normalized, before)
        self.assertEqual(wire['messages'][1], {'role': 'assistant', 'content': native()})
        self.assertEqual(len(wire['messages']), 3)
        self.assertEqual(wire['messages'][2]['role'], 'user')
        group = wire['messages'][2]['content']
        self.assertEqual([item['type'] for item in group], ['tool_result', 'tool_result'])
        self.assertEqual([item['tool_use_id'] for item in group], ['toolu_a', 'toolu_b'])
        self.assertEqual([decode(item['content']) for item in group],
                         [decode(item['content'])['result'] for item in normalized['messages'][3:]])

    def test_missing_orphan_duplicate_interleaved_and_forged_tool_results_fail_locally(self):
        settings = config(); good = history(settings); bad = []
        missing = deepcopy(good); missing['messages'].pop(); bad.append(missing)
        duplicate = deepcopy(good); duplicate['messages'].append(deepcopy(duplicate['messages'][-1])); bad.append(duplicate)
        interleaved = deepcopy(good); interleaved['messages'].insert(3, {'role': 'user', 'content': 'interleaved'}); bad.append(interleaved)
        for field, value in [('id', 'orphan'), ('name', 'read_source'), ('arguments', {'substituted': True})]:
            changed = deepcopy(good); body = decode(changed['messages'][3]['content'])
            body['tool_request'][field] = value; changed['messages'][3]['content'] = canonical(body); bad.append(changed)
        for index, value in enumerate(bad):
            with self.subTest(index=index), self.assertRaises(Invalid):
                api.wire_request(value, settings)

    def test_foreign_provider_or_model_history_cannot_be_replayed_as_this_role(self):
        settings = config()
        for field, value in [('provider_id', 'openai.responses/1'), ('resolved_model', 'other-model')]:
            req = history(settings); previous = decode(req['messages'][2]['content'])
            previous[field] = value; req['messages'][2]['content'] = canonical(previous)
            with self.subTest(field=field), self.assertRaises(Invalid):
                api.wire_request(req, settings)

    def test_unsupported_hosted_charges_or_iterations_do_not_receive_a_guessed_tariff(self):
        for extra in ({'iterations': [{'type': 'compaction', 'input_tokens': 999, 'output_tokens': 88}]},
                      {'server_tool_use': {'web_search_requests': 1, 'web_fetch_requests': 0}},
                      {'service_tier': 'priority'}, {'inference_geo': 'us'}, {'speed': 'fast'}):
            response = raw(); response['usage'].update(extra)
            with self.subTest(extra=extra):
                parsed = api.parse_response(response, 'req_extra', config())
                self.assertIsNone(parsed['usage'])
                self.assertIsNone(parsed['response']['output'])

    def test_input_or_output_overrun_halts_even_when_charge_is_below_reservation(self):
        cases = [(20001, 0, 80004000), (0, 4097, 40970000)]
        for input_tokens, output_tokens, charge in cases:
            with self.subTest(input=input_tokens, output=output_tokens), tempfile.TemporaryDirectory() as folder:
                provider = self.provider(folder); response = raw()
                response['usage'].update(input_tokens=input_tokens, cache_creation_input_tokens=0,
                                          cache_read_input_tokens=0, output_tokens=output_tokens)
                result, _ = self.complete_with(provider, response)
                self.assertEqual(result['usage'], {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'cost_units': charge})
                self.assertLess(charge, RESERVATION)
                self.assertIsNone(result['response']['output'])
                snapshot = api.SpendLedger(provider.budget_file, CAP).snapshot()
                self.assertEqual(snapshot['charged_nano'], charge)
                self.assertTrue(snapshot['halted'])
                _, operations = self.complete_with(provider, raw(), ordinal=1)
                self.assertNotIn('/v1/messages', operations)

    def assert_unpriced_content_blocks_later_inference(self, content, stop):
        response = raw(content, stop)
        self.assertNotIn('server_tool_use', response['usage'])
        self.assertNotIn('iterations', response['usage'])
        parsed = api.parse_response(response, 'req_unpriced_content', config())
        self.assertIsNone(parsed['response']['output'])
        self.assertIsNone(parsed['usage'], 'Unsupported paid work cannot settle a token-only price')
        with tempfile.TemporaryDirectory() as folder:
            provider = self.provider(folder)
            result, _ = self.complete_with(provider, response)
            self.assertIsNone(result['usage'])
            self.assertIsNone(result['response']['output'])
            snapshot = api.SpendLedger(provider.budget_file, CAP).snapshot()
            self.assertTrue(snapshot['halted'])
            self.assertEqual(snapshot['charged_nano'], RESERVATION)
            self.assertEqual(snapshot['uncertain'], 1)
            _, operations = self.complete_with(provider, raw(), ordinal=1)
            self.assertNotIn('/v1/messages', operations)

    def test_hosted_content_without_hosted_usage_cannot_receive_token_only_price(self):
        self.assert_unpriced_content_blocks_later_inference(
            [{'type': 'server_tool_use', 'id': 'srvtoolu_fixture', 'name': 'web_search',
              'input': {'query': 'synthetic fixture'}}], 'tool_use')

    def test_compaction_content_without_iterations_cannot_receive_token_only_price(self):
        self.assert_unpriced_content_blocks_later_inference(
            [{'type': 'compaction', 'content': 'Synthetic compressed context.'},
             {'type': 'text', 'text': canonical(final_output())}], 'end_turn')

    def test_hosted_caller_without_hosted_usage_cannot_receive_token_only_price(self):
        self.assert_unpriced_content_blocks_later_inference(
            [{'type': 'tool_use', 'id': 'toolu_fixture', 'name': 'capabilities', 'input': {},
              'caller': {'type': 'code_execution_20250825', 'tool_id': 'srvtoolu_fixture'}}], 'tool_use')

    def test_bad_public_metadata_retains_known_charge_and_suppresses_execution(self):
        for malformed_id in (None, [], {'not': 'a-string'}, True):
            with self.subTest(identity=malformed_id), tempfile.TemporaryDirectory() as folder:
                provider = self.provider(folder); response = raw(native(), 'tool_use'); response['id'] = malformed_id
                result, _ = self.complete_with(provider, response)
                self.assertEqual(result['usage'], {'input_tokens': 800, 'output_tokens': 40, 'cost_units': 3600000})
                self.assertIsNone(result['response']['output'])
                self.assertEqual(api.SpendLedger(provider.budget_file, CAP).snapshot()['charged_nano'], 3600000)
                self.assertTrue(api.SpendLedger(provider.budget_file, CAP).snapshot()['halted'])

    def test_duplicate_dispatch_is_not_paid_again_but_equal_new_call_is_distinct(self):
        with tempfile.TemporaryDirectory() as folder:
            provider = self.provider(folder)
            self.complete_with(provider, raw())
            _, duplicate_ops = self.complete_with(provider, raw())
            self.assertNotIn('/v1/messages', duplicate_ops)
            _, second_ops = self.complete_with(provider, raw(), ordinal=1)
            self.assertEqual(second_ops.count('/v1/messages'), 1)
            report = api.SpendLedger(provider.budget_file, CAP).report()
            self.assertEqual(report['totals']['exact_total_tokens'], 1680)
            self.assertEqual(report['money']['charged_nano'], 7200000)
            self.assertEqual(report['calls'][0]['metadata']['budget_scope_ref'], 'synthetic-test-only-no-spending-authority')
            self.assertEqual(report['calls'][0]['metadata']['counted_input_tokens'], 777)
            self.assertEqual(report['totals']['known_input_tokens'], 1600)
            self.assertNotIn('synthetic-secret-never-real', canonical(report))

    def test_explicit_tiny_cap_prevents_inference_and_cannot_be_resized(self):
        with tempfile.TemporaryDirectory() as folder:
            provider = self.provider(folder, aggregate_budget_nano=RESERVATION - 1)
            operations = []
            def post(endpoint, *args):
                operations.append(endpoint)
                if endpoint.endswith('/count_tokens'):
                    return {'input_tokens': 777}, 'req_count'
                self.fail('Unfunded inference')
            with patch.object(api, '_key', return_value='synthetic-secret-never-real'), \
                    patch.object(api, '_post', side_effect=post):
                provider.complete(request(provider.config), 0, 10)
            self.assertNotIn('/v1/messages', operations)
            ledger = api.SpendLedger(provider.budget_file, RESERVATION - 1)
            self.assertEqual(ledger.snapshot()['dispatches'], 0)
            with self.assertRaises(Conflict):
                api.SpendLedger(provider.budget_file, RESERVATION)

    def test_provider_dimension_prevents_same_identity_and_run_from_merging(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = api.SpendLedger(Path(folder) / 'mixed-fixture.sqlite3', CAP)
            parsed = api.parse_response(raw(), 'req_fixture', config())
            receipt = {'usage': parsed['usage'], 'token_details': parsed['response']['token_usage_details'],
                       'model_identity': parsed['response']['model_identity']}
            metadata = {'model': api.MODEL, 'model_identity': api.provider_identity(),
                        'epoch_id': 'same', 'run_id': 'same', 'worker': 'same'}
            for index, provider in enumerate((None, 'anthropic')):
                meta = deepcopy(metadata)
                if provider is not None:
                    meta['provider'] = provider
                identity = ledger.reserve('same-payload', RESERVATION, key=str(index), metadata=meta)
                ledger.settle(identity, 3600000, receipt=receipt)
            before = hashlib.sha256(Path(ledger.path).read_bytes()).hexdigest()
            report = provider_usage.read_usage_report(ledger.path)
            self.assertEqual(hashlib.sha256(Path(ledger.path).read_bytes()).hexdigest(), before)
            self.assertEqual(report['schema'], 'framework-provider-usage-report/3')
            self.assertEqual(report['provider'], 'mixed')
            self.assertEqual(report['providers'], ['anthropic', 'openai'])
            self.assertEqual(len(report['runs']), 2)
            self.assertEqual(len(report['models']), 2)
            self.assertEqual({r['provider'] for r in report['runs']}, {'anthropic', 'openai'})
            self.assertEqual(report['totals']['exact_total_tokens'], 1680)
            self.assertEqual([c['provider'] for c in report['calls']], ['openai', 'anthropic'])


class Response:
    def __init__(self, data, status=200):
        self.data, self.status = data, status
    def getheader(self, name):
        return 'req_independent' if name.lower() == 'request-id' else None
    def read1(self, size):
        value, self.data = self.data[:size], self.data[size:]
        return value


class Connection:
    sock = None
    def __init__(self, response):
        self.response, self.sent, self.closed = response, [], False
    def request(self, *args, **kwargs):
        self.sent.append((args, kwargs))
    def getresponse(self):
        return self.response
    def close(self):
        self.closed = True


class AnthropicWireAdversarialTests(unittest.TestCase):
    def test_tls_host_version_workspace_and_bearer_are_fixed_without_redirects(self):
        response = Response(b'{"input_tokens":777}')
        connection = Connection(response)
        with patch('http.client.HTTPSConnection', return_value=connection) as factory:
            value, _ = api._post('/v1/messages/count_tokens', {'model': api.MODEL},
                                 'synthetic-secret-never-real', time.monotonic()+10, 'wrkspc_independent')
        self.assertEqual(value, {'input_tokens': 777})
        self.assertEqual(factory.call_args.args[:2], ('api.anthropic.com', 443))
        self.assertEqual(connection.sent[0][0], ('POST', '/v1/messages/count_tokens'))
        headers = {k.lower(): v for k, v in connection.sent[0][1]['headers'].items()}
        self.assertEqual(headers['authorization'], 'Bearer synthetic-secret-never-real')
        self.assertEqual(headers['anthropic-version'], '2026-10-21')
        self.assertEqual(headers['anthropic-workspace-id'], 'wrkspc_independent')
        self.assertNotIn(b'synthetic-secret-never-real', connection.sent[0][1]['body'])
        self.assertTrue(connection.closed)
        redirect = Connection(Response(b'secret-echo', 302))
        with patch('http.client.HTTPSConnection', return_value=redirect) as factory:
            with self.assertRaises(Exception) as error:
                api._post('/v1/messages', {}, 'synthetic-secret-never-real', time.monotonic()+10, None)
            self.assertEqual(factory.call_count, 1)
        self.assertNotIn('secret-echo', str(error.exception))
        self.assertNotIn('synthetic-secret-never-real', str(error.exception))
        self.assertTrue(redirect.closed)

    def test_duplicate_wire_json_keys_fail_closed_and_close_connection(self):
        connection = Connection(Response(b'{"input_tokens":1,"input_tokens":777}'))
        with patch('http.client.HTTPSConnection', return_value=connection):
            with self.assertRaises(Exception):
                api._post('/v1/messages/count_tokens', {}, 'synthetic', time.monotonic()+10, None)
        self.assertTrue(connection.closed)


if __name__ == '__main__':
    unittest.main()
