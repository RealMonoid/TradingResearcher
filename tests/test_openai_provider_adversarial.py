"""Independent offline oracles; never uses a real key or provider connection.

Numeric expectations were fixed before openai_provider.py existed. The shared
USD 5 allowance, strict per-dispatch identity, and conservative charge basis
are operational constraints, not evidence of scientific model performance.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid, canonical
from trading_researcher.errors import Conflict, Denied
from trading_researcher import openai_provider as api


def config():
    return api.configuration()


def request(settings):
    return {
        'model': 'gpt-6.1-sol', 'prompt_version': 'independent-openai-oracles/1',
        'messages': [{'role': 'system', 'content': 'Return JSON. No empirical authority.'},
                     {'role': 'user', 'content': 'Independent synthetic perspective.'}],
        'tools': [{'name': 'capabilities', 'description': 'Read capabilities.',
                   'parameters': {'type': 'object', 'properties': {},
                                  'additionalProperties': False}}],
        'generation_parameters': {'openai_responses': deepcopy(settings)},
    }


def raw_response(items=None, **changes):
    value = {'id': 'resp_independent', 'model': 'gpt-6.1-sol',
             'service_tier': 'default', 'status': 'completed',
             'usage': {'input_tokens': 500, 'output_tokens': 4},
             'temperature': 1.0,
             'output': items if items is not None else [{
                 'id': 'msg_independent', 'type': 'message', 'role': 'assistant',
                 'status': 'completed', 'phase': 'final_answer', 'content': [{
                     'type': 'output_text', 'annotations': [],
                     'text': canonical({'status': 'final', 'record': {'kind': 'gap',
                         'content': {'reason': 'Synthetic missing capability',
                                     'reopen_condition': 'A separately verified implementation'},
                         'scope': {}, 'source_refs': []}})}]}]}
    value.update(changes)
    return value


def tool_items():
    return [{'id': 'rs_independent', 'type': 'reasoning', 'summary': [],
             'encrypted_content': 'opaque-independent-fixture'},
            {'id': 'msg_before_tool', 'type': 'message', 'role': 'assistant',
             'status': 'completed', 'phase': 'commentary',
             'content': [{'type': 'output_text', 'text': 'Checking capabilities.',
                          'annotations': []}]},
            {'id': 'fc_independent', 'type': 'function_call', 'call_id': 'call_independent',
             'name': 'capabilities', 'arguments': '{}', 'status': 'completed'}]


def tool_history(settings):
    value = request(settings)
    public = api.parse_response(raw_response(tool_items()), 'req_independent', settings)['response']
    value['messages'].append({'role': 'assistant', 'content': canonical(public)})
    result = {'schema': 'provider-tool-result/1', 'call_id': 'owned-broker-call',
              'tool_request': {'id': 'call_independent', 'name': 'capabilities', 'arguments': {}},
              'result': {'status': 'ok', 'value': {'scientific_authority': False}}}
    value['messages'].append({'role': 'tool', 'content': canonical(result)})
    return value


class IndependentOpenAIProviderTests(unittest.TestCase):
    def provider(self, directory):
        key = Path(directory) / 'synthetic.env'
        key.write_text('OPENAI_API_KEY=sk-independent-synthetic-only\n', encoding='utf-8')
        return api.OpenAIResponsesProvider(key, Path(directory) / 'shared.sqlite3', config())

    def test_independent_fixed_nano_currency_oracles(self):
        self.assertEqual(api.cost_bound(0, 0), 0)
        self.assertEqual(api.cost_bound(1, 1), 12500)
        self.assertEqual(api.cost_bound(500, 4), 1290000)
        amount = api.cost_bound(20000, 4096)
        self.assertEqual(amount, 90960000)
        self.assertEqual(amount * 54, 4911840000)
        self.assertEqual(5000000000 - amount * 54, 88160000)
        self.assertEqual(amount * 55, 5002800000)
        for bad in (True, False, -1, 1.0, '1', None):
            with self.subTest(bad=bad), self.assertRaises(Invalid):
                api.cost_bound(1, bad)

    def test_full_reservations_cross_epoch_cap_at_fifty_five(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'all-epochs.sqlite3'
            for ordinal in range(54):
                ledger = api.SpendLedger(path, 5000000000)
                identity = ledger.reserve('same-possible-perspective-payload', 90960000,
                                          key='independent-' + str(ordinal))
                ledger.settle(identity, 90960000)
            last = api.SpendLedger(path, 5000000000)
            self.assertEqual(last.snapshot()['charged_nano'], 4911840000)
            with self.assertRaises(Denied):
                last.reserve('same-possible-perspective-payload', 90960000, key='independent-54')
            self.assertEqual(last.snapshot()['dispatches'], 54)

    def test_known_refund_then_unknown_uses_full_remaining_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.sqlite3'
            ledger = api.SpendLedger(path, 1000)
            first = ledger.reserve('same-hash', 600, key='first')
            ledger.settle(first, 250)
            self.assertEqual(ledger.snapshot()['available_nano'], 750)
            second = api.SpendLedger(path, 1000).reserve('same-hash', 750, key='second')
            ledger.settle(second, None)
            reopened = api.SpendLedger(path, 1000)
            self.assertEqual(reopened.snapshot()['charged_nano'], 1000)
            self.assertEqual(reopened.snapshot()['uncertain'], 1)
            self.assertTrue(reopened.snapshot()['halted'])
            with self.assertRaises(Conflict):
                reopened.reserve('new', 1, key='third')
            with self.assertRaises(Conflict):
                reopened.settle(second, 0)

    def test_settlement_idempotence_and_overrun_cannot_be_erased(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.sqlite3'
            ledger = api.SpendLedger(path, 1000)
            identity = ledger.reserve('payload', 600, key='fixed')
            ledger.settle(identity, 700)
            ledger.settle(identity, 700)
            self.assertEqual(ledger.snapshot()['charged_nano'], 700)
            self.assertTrue(ledger.snapshot()['halted'])
            with self.assertRaises(Conflict):
                ledger.settle(identity, 600)
            with self.assertRaises(Conflict):
                api.SpendLedger(path, 1000).reserve('other', 1)
            with self.assertRaises(Conflict):
                api.SpendLedger(path, 1001)

    def test_concurrent_admissions_cannot_pass_an_outstanding_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ledger.sqlite3'
            api.SpendLedger(path, 1000)
            gate = threading.Barrier(2)
            def reserve(index):
                ledger = api.SpendLedger(path, 1000)
                gate.wait(timeout=5)
                try:
                    return ledger.reserve('equal-content', 600, key='parallel-' + str(index))
                except Conflict:
                    return 'blocked'
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(reserve, (1, 2)))
            self.assertEqual(results.count('blocked'), 1)
            self.assertEqual(api.SpendLedger(path, 1000).snapshot()['charged_nano'], 600)

    def test_reservation_is_local_and_expired_tariff_stops_before_key_or_network(self):
        settings = config()
        provider = api.OpenAIResponsesProvider('never-read.env', 'never-created.sqlite3', settings)
        with patch.object(api, '_key', side_effect=AssertionError('Credential access forbidden')), \
                patch.object(api, '_post', side_effect=AssertionError('Network forbidden')):
            result = provider.reservation(request(settings), 4096)
            self.assertEqual(result, {'input_token_bound': 20000, 'output_token_limit': 4096,
                                      'cost_bound_units': 90960000})
            expired = api.configuration(now=1)
            expired_provider = api.OpenAIResponsesProvider('never-read.env', 'never-created.sqlite3', expired)
            with self.assertRaises(Invalid):
                expired_provider.reservation(request(expired), 4096)

    def test_wire_native_history_preserves_only_matching_tool_result_and_phase(self):
        settings = config(); original = tool_history(settings); before = deepcopy(original)
        payload = api.wire_request(original, settings)
        self.assertEqual(original, before)
        self.assertEqual(payload['input'][2]['encrypted_content'], 'opaque-independent-fixture')
        self.assertEqual(payload['input'][3]['phase'], 'commentary')
        self.assertEqual(payload['input'][-1]['type'], 'function_call_output')
        self.assertEqual(payload['input'][-1]['call_id'], 'call_independent')
        self.assertEqual(payload['prompt_cache_options'], {'ttl': '30m'})
        self.assertNotIn('previous_response_id', payload)
        for mutation in ('missing', 'duplicate', 'wrong_id', 'wrong_arguments'):
            bad = deepcopy(original)
            if mutation == 'missing':
                bad['messages'].pop()
            elif mutation == 'duplicate':
                bad['messages'].append(deepcopy(bad['messages'][-1]))
            else:
                body = json.loads(bad['messages'][-1]['content'])
                body['tool_request']['id' if mutation == 'wrong_id' else 'arguments'] = \
                    'other-call' if mutation == 'wrong_id' else {'unexpected': True}
                bad['messages'][-1]['content'] = canonical(body)
            with self.subTest(mutation=mutation), self.assertRaises(Invalid):
                api.wire_request(bad, settings)

    def test_unpriced_nested_cache_override_is_not_replayed(self):
        settings = config(); value = tool_history(settings)
        public = json.loads(value['messages'][2]['content'])
        public['provider_items'][1]['content'][0]['prompt_cache_breakpoint'] = {
            'mode': 'explicit', 'ttl': '12h'}
        value['messages'][2]['content'] = canonical(public)
        try:
            payload = api.wire_request(value, settings)
        except Invalid:
            return
        self.assertNotIn('12h', canonical(payload), 'Native content must not override the priced 30m request')

    def test_wrong_served_model_or_tier_never_returns_actionable_completed_output(self):
        for changes in ({'model': 'different-model'}, {'service_tier': 'priority'}, {'model': None}):
            with self.subTest(changes=changes):
                result = api.parse_response(raw_response(tool_items(), **changes), 'req_independent', config())
                self.assertIsNone(result['usage'])
                self.assertNotEqual(result['response']['status'], 'completed')
                self.assertIsNone(result['response']['output'])

    def test_incomplete_output_and_invalid_usage_are_never_fabricated_as_success(self):
        settings = config()
        result = api.parse_response(raw_response(tool_items(), status='incomplete'), 'req_independent', settings)
        self.assertIsNone(result['response']['output'])
        self.assertEqual(result['usage']['cost_units'], 1290000)
        for bad in (True, -1, 1.0, '500', None):
            raw = raw_response(); raw['usage']['input_tokens'] = bad
            with self.subTest(bad=bad):
                self.assertIsNone(api.parse_response(raw, 'req_independent', settings)['usage'])

    def test_failed_inference_keeps_full_reservation_across_restart_and_no_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider(directory); endpoints = []
            def post(endpoint, payload, secret, deadline):
                endpoints.append(endpoint)
                if endpoint.endswith('/input_tokens'):
                    return {'object': 'response.input_tokens', 'input_tokens': 500}, 'req_count'
                raise RuntimeError('sk-independent-synthetic-only must not be retained')
            with patch.object(api, '_post', side_effect=post):
                result = provider.complete(request(provider.config), 0, 10)
            self.assertEqual(endpoints, ['/v1/responses/input_tokens', '/v1/responses'])
            self.assertIsNone(result['usage'])
            self.assertNotIn('sk-independent', canonical(result))
            ledger = api.SpendLedger(provider.budget_file, 5000000000)
            self.assertEqual(ledger.snapshot()['charged_nano'], 90960000)
            self.assertTrue(ledger.snapshot()['halted'])

    def test_missing_receipt_keeps_unknown_charge_and_blocks_a_later_inference(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider(directory); endpoints = []
            def post(endpoint, payload, secret, deadline):
                endpoints.append(endpoint)
                if endpoint.endswith('/input_tokens'):
                    return {'object': 'response.input_tokens', 'input_tokens': 500}, 'req_count'
                return raw_response(usage=None), 'req_no_usage'
            with patch.object(api, '_post', side_effect=post):
                first = provider.complete(request(provider.config), 0, 10)
                second = provider.complete(request(provider.config), 1, 10)
            self.assertIsNone(first['usage'])
            self.assertEqual(endpoints.count('/v1/responses'), 1)
            self.assertEqual(second['response']['status'], 'failed')

    def test_repeated_dispatch_key_never_infers_twice_but_equal_payload_can_be_new_call(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = self.provider(directory); inferences = []
            def post(endpoint, payload, secret, deadline):
                if endpoint.endswith('/input_tokens'):
                    return {'object': 'response.input_tokens', 'input_tokens': 500}, 'req_count'
                inferences.append(deepcopy(payload)); return raw_response(), 'req_result'
            with patch.object(api, '_post', side_effect=post):
                provider.complete(request(provider.config), 0, 10)
                provider.complete(request(provider.config), 0, 10)
                provider.complete(request(provider.config), 1, 10)
            self.assertEqual(len(inferences), 2)
            self.assertEqual(inferences[0], inferences[1])
            self.assertEqual(api.SpendLedger(provider.budget_file, 5000000000).snapshot()['charged_nano'], 2580000)

    def test_http_redirect_does_not_follow_location_or_read_secret_error_body(self):
        class Response:
            status = 307
            def getheader(self, name):
                return 'req_redirect' if name == 'x-request-id' else 'https://untrusted.invalid'
            def read1(self, amount):
                raise AssertionError('Redirect body must not be consumed')
        class Connection:
            sock = None
            closed = False
            def request(self, *args, **kwargs): pass
            def getresponse(self): return Response()
            def close(self): self.closed = True
        connection = Connection()
        with patch.object(api.http.client, 'HTTPSConnection', return_value=connection) as factory:
            with self.assertRaises(api.WireFailure) as caught:
                api._post('/v1/responses', {'model': 'synthetic'}, 'sk-synthetic-only', time.monotonic() + 2)
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(factory.call_args.args, ('api.openai.com', 443))
        self.assertEqual(caught.exception.status, 307)
        self.assertTrue(connection.closed)
        self.assertNotIn('sk-synthetic', str(caught.exception))

    def test_ambiguous_json_receipt_and_oversized_body_are_rejected_without_network(self):
        for body, expected in ((b'{"id":"one","id":"two"}', 'duplicate_json_key'),
                               (b'x' * (api.MAX_BYTES + 1), 'response_size')):
            class Response:
                status = 200
                offset = 0
                def getheader(self, name): return 'req_fixture'
                def read1(self, amount):
                    value = body[self.offset:self.offset + amount]
                    self.offset += len(value)
                    return value
            class Connection:
                sock = None
                def request(self, *args, **kwargs): pass
                def getresponse(self): return Response()
                def close(self): pass
            with self.subTest(expected=expected), \
                    patch.object(api.http.client, 'HTTPSConnection', return_value=Connection()), \
                    self.assertRaises(api.WireFailure) as caught:
                api._post('/v1/responses', {}, 'sk-synthetic-only', time.monotonic() + 2)
            self.assertEqual(caught.exception.kind, expected)


if __name__ == '__main__':
    unittest.main()
