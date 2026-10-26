"""Independent durable token accounting examples, with only mocked transport."""
from copy import deepcopy
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import test_openai_provider_adversarial as fixed
from trading_researcher import openai_provider as api
from trading_researcher import provider_usage
from trading_researcher.codec import Invalid
from trading_researcher.errors import Conflict


def receipt(input_tokens=500, output_tokens=4, charge=1290000,
            cached=300, reasoning=3):
    return {'usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens,
                      'cost_units': charge},
            'token_details': {'cached_input_tokens': cached,
                              'reasoning_output_tokens': reasoning}}


class IndependentProviderUsageTests(unittest.TestCase):
    def test_fixed_two_receipts_total624_and_subsets_are_partial_not_additional(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = api.OpenAIResponsesProvider('never-read.env', Path(directory) / 'spend.sqlite3',
                                                   fixed.config(), epoch_id='epoch-fixed', worker='first')
            first = fixed.raw_response()
            first['usage'].update(input_tokens_details={'cached_tokens': 300},
                                  output_tokens_details={'reasoning_tokens': 3})
            second = fixed.raw_response(usage={'input_tokens': 100, 'output_tokens': 20})
            operations = []
            def post(endpoint, payload, secret, deadline):
                operations.append(endpoint)
                if endpoint.endswith('/input_tokens'):
                    return {'object': 'response.input_tokens', 'input_tokens': 777}, 'req_count'
                return (first if operations.count('/v1/responses') == 1 else second), 'req_result'
            with patch.object(api, '_key', return_value='sk-independent-unused'), \
                    patch.object(api, '_post', side_effect=post):
                provider.complete(fixed.request(provider.config), 0, 10)
                provider.complete(fixed.request(provider.config), 1, 10)
            report = provider_usage.read_usage_report(provider.budget_file)
            totals = report['totals']
            self.assertEqual(totals['calls'], 2)
            self.assertEqual(totals['known_input_tokens'], 600)
            self.assertEqual(totals['known_output_tokens'], 24)
            self.assertEqual(totals['known_total_tokens'], 624)
            self.assertEqual(totals['exact_total_tokens'], 624)
            self.assertEqual(totals['known_cached_input_tokens'], 300)
            self.assertEqual(totals['known_reasoning_output_tokens'], 3)
            self.assertEqual(totals['cached_detail_calls'], 1)
            self.assertEqual(totals['reasoning_detail_calls'], 1)
            self.assertIsNone(totals['exact_cached_input_tokens'])
            self.assertIsNone(totals['exact_reasoning_output_tokens'])
            self.assertEqual(report['money']['charged_nano'], 1740000)
            self.assertEqual(report['runs'][0]['exact_total_tokens'], 624)
            self.assertEqual(report['runs'][0]['epoch_id'], 'epoch-fixed')
            self.assertEqual(report['runs'][0]['worker'], 'first')
            self.assertEqual([c['metadata']['counted_input_tokens'] for c in report['calls']], [777, 777])
            self.assertNotIn('sk-independent', str(report))
            self.assertNotIn('Independent synthetic perspective.', str(report))

    def test_unknown_admitted_call_preserves_known_sums_without_claiming_exact_total(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'spend.sqlite3'
            ledger = api.SpendLedger(path, 5000000000)
            first = ledger.reserve('first', 90960000, key='first')
            ledger.settle(first, 1290000, receipt=receipt())
            second = ledger.reserve('second', 90960000, key='second')
            ledger.settle(second, 450000, receipt=receipt(100, 20, 450000, None, None))
            third = ledger.reserve('third', 90960000, key='third')
            pending = provider_usage.read_usage_report(path)
            ledger.settle(third, None)
            unknown = provider_usage.read_usage_report(path)
            for report in (pending, unknown):
                self.assertEqual(report['totals']['known_input_tokens'], 600)
                self.assertEqual(report['totals']['known_output_tokens'], 24)
                self.assertEqual(report['totals']['known_total_tokens'], 624)
                self.assertEqual(report['totals']['unknown_usage_calls'], 1)
                self.assertIsNone(report['totals']['exact_total_tokens'])
                self.assertEqual(report['money']['charged_nano'], 92700000)
                self.assertTrue(report['money']['halted'])

    def test_identical_settlement_replays_but_same_money_different_tokens_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = api.SpendLedger(Path(directory) / 'spend.sqlite3', 5000000000)
            identity = ledger.reserve('same', 90960000, key='same')
            original = receipt()
            ledger.settle(identity, 1290000, receipt=original)
            ledger.settle(identity, 1290000, receipt=deepcopy(original))
            different = receipt(496, 5, 1290000)
            self.assertEqual(api.cost_bound(496, 5), 1290000)
            with self.assertRaises(Conflict):
                ledger.settle(identity, 1290000, receipt=different)
            self.assertEqual(ledger.report()['totals']['exact_total_tokens'], 504)

    def test_legacy_ledger_without_receipt_tables_is_read_only_and_usage_unknown(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'legacy.sqlite3'
            db = sqlite3.connect(path)
            try:
                db.execute('CREATE TABLE budget(singleton INTEGER PRIMARY KEY,cap INTEGER NOT NULL)')
                db.execute('CREATE TABLE dispatches(id TEXT PRIMARY KEY,request_hash TEXT NOT NULL,reserved INTEGER NOT NULL,charged INTEGER,state TEXT NOT NULL)')
                db.execute('INSERT INTO budget VALUES(1,5000000000)')
                db.execute("INSERT INTO dispatches VALUES('legacy','payload',90960000,1290000,'settled')")
                db.commit()
            finally:
                db.close()
            before = hashlib.sha256(path.read_bytes()).hexdigest()
            report = provider_usage.read_usage_report(path)
            self.assertEqual(report['totals']['known_usage_calls'], 0)
            self.assertEqual(report['totals']['unknown_usage_calls'], 1)
            self.assertIsNone(report['totals']['exact_total_tokens'])
            self.assertEqual(report['money']['charged_nano'], 1290000)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)

    def test_optional_subset_errors_do_not_erase_base_counts_and_zero_is_known(self):
        for cached, reasoning in ((True, False), (-1, -1), (501, 5), ('300', 3.0), (None, None), (0, 0)):
            raw = fixed.raw_response()
            raw['usage'].update(input_tokens_details={'cached_tokens': cached},
                                output_tokens_details={'reasoning_tokens': reasoning})
            with self.subTest(cached=cached, reasoning=reasoning):
                parsed = api.parse_response(raw, 'req_fixture', fixed.config())
                self.assertEqual(parsed['usage'], {'input_tokens': 500, 'output_tokens': 4, 'cost_units': 1290000})
                known_zero = type(cached) is int and type(reasoning) is int and cached == reasoning == 0
                self.assertEqual(parsed['response']['token_usage_details'], {
                    'cached_input_tokens': 0 if known_zero else None,
                    'reasoning_output_tokens': 0 if known_zero else None})

    def test_receipt_insert_failure_rolls_back_charge_and_preserves_pending_reservation(self):
        class ReceiptFailure(sqlite3.Connection):
            def execute(self, statement, *args, **kwargs):
                if statement.lstrip().upper().startswith('INSERT INTO USAGE_RECEIPTS'):
                    raise sqlite3.OperationalError('independent injected receipt-write fault')
                return super().execute(statement, *args, **kwargs)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'spend.sqlite3'
            ledger = api.SpendLedger(path, 5000000000)
            identity = ledger.reserve('receipt-fault', 90960000, key='receipt-fault')
            original_connect = sqlite3.connect
            def connect(*args, **kwargs):
                return original_connect(*args, **kwargs, factory=ReceiptFailure)
            with patch.object(api.sqlite3, 'connect', side_effect=connect), \
                    self.assertRaises(sqlite3.OperationalError):
                ledger.settle(identity, 1290000, receipt=receipt())
            report = provider_usage.read_usage_report(path)
            self.assertEqual(report['calls'][0]['state'], 'pending')
            self.assertIsNone(report['calls'][0]['receipt'])
            self.assertEqual(report['money']['charged_nano'], 90960000)
            self.assertEqual(report['totals']['unknown_usage_calls'], 1)
            with self.assertRaises(Conflict):
                ledger.reserve('other', 1, key='other')

    def test_unapproved_metadata_is_rejected_before_creating_a_dispatch(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = api.SpendLedger(Path(directory) / 'spend.sqlite3', 5000000000)
            for metadata in ({'raw_prompt': 'synthetic prompt'}, {'headers': {'Authorization': 'synthetic'}},
                             {'ordinal': True}, {'counted_input_tokens': -1}):
                with self.subTest(metadata=metadata), self.assertRaises(Invalid):
                    ledger.reserve('invalid', 90960000, key='invalid', metadata=metadata)
            self.assertEqual(ledger.snapshot()['dispatches'], 0)


if __name__ == '__main__':
    unittest.main()
