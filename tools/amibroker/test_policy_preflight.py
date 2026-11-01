"""Independent fixed synthetic portfolio expectations; no native launch/network.

Expected trades and cash/close-mark curves were hand fixed before the native
run. These tests validate the input/verifier boundary; they do not certify
AmiBroker defaults, real costs, market success or scientific evidence.
"""
from copy import deepcopy
import csv
import codecs
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import subprocess
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import Mock, patch

import policy_preflight as policy

HERE = Path(__file__).resolve().parent
EXPECTED = json.loads((HERE / 'fixtures/policy_expected.json').read_text(encoding='utf-8'))
CLOSES = {'TRF_A': [101, 112, 118, 132, 139, 151, 161, 171],
          'TRF_B': [51, 56, 59, 66, 69, 76, 81, 86]}
OPENS = {'TRF_A': [100, 110, 120, 130, 140, 150, 160, 170],
         'TRF_B': [50, 55, 60, 65, 70, 75, 80, 85]}


def cases():
    return {item['id']: item for item in policy.load_cases()}


class FixedExpectedArithmetic(unittest.TestCase):
    def test_exact_five_cases_and_fixed_tolerances(self):
        self.assertEqual(set(EXPECTED['cases']), {'timing', 'costs', 'shared_cash', 'exit_then_entry', 'last_signal'})
        self.assertEqual(EXPECTED['tolerances'], {'currency_absolute': '0.001', 'price_absolute': '0.00001',
            'timestamps_symbols_indices_quantities_counts': 'exact'})
        start = datetime(2023, 1, 1, tzinfo=timezone.utc)
        for name, expected in EXPECTED['cases'].items():
            with self.subTest(case=name):
                self.assertEqual(len(expected['rows']), 8)
                for index, row in enumerate(expected['rows']):
                    self.assertEqual(row['timestamp'], (start + timedelta(seconds=900 * index)).strftime('%Y-%m-%dT%H:%M:%SZ'))
                    mark = sum(Decimal(CLOSES[symbol][index]) * quantity for symbol, quantity in row['positions'].items())
                    self.assertEqual(Decimal(row['equity']), Decimal(row['cash']) + mark)
                    self.assertTrue(all(type(q) is int and q >= 0 for q in row['positions'].values()))
                self.assertTrue(all(q == 0 for q in expected['rows'][-1]['positions'].values()))

    def test_independent_fee_notional_and_net_cash_arithmetic(self):
        expected = EXPECTED['cases']['costs']
        trade = expected['trades'][0]
        d = Decimal
        entry = d(110) * (1 + d(10) / 10000)
        exit_price = d(130) * (1 - d(10) / 10000)
        entry_fee = 2 * entry * d(10) / 10000
        exit_fee = 2 * exit_price * d(10) / 10000
        self.assertEqual(entry, d(trade['entry_price']))
        self.assertEqual(exit_price, d(trade['exit_price']))
        self.assertEqual((entry_fee, exit_fee), (d('0.22022'), d('0.25974')))
        self.assertEqual(d(trade['entry_fee']), entry_fee)
        self.assertEqual(d(trade['exit_fee']), exit_fee)
        self.assertEqual(d(expected['rows'][1]['cash']), d(1000) - 2 * entry - entry_fee)
        net = 2 * (exit_price - entry) - entry_fee - exit_fee
        self.assertEqual(net, d('39.04004'))
        self.assertEqual(d(trade['pnl']), net)
        self.assertEqual(d(expected['rows'][-1]['cash']), d(1000) + net)

    def test_ranked_cash_and_exit_before_entry_are_distinct_fixed_cases(self):
        shared = EXPECTED['cases']['shared_cash']
        self.assertEqual([(t['symbol'], t['quantity'], t['entry_index'], t['exit_index']) for t in shared['trades']],
                         [('TRF_B', 2, 1, 3)])
        self.assertEqual(Decimal(shared['rows'][1]['cash']), Decimal(150) - 2 * 55)
        self.assertLess(Decimal(shared['rows'][1]['cash']), Decimal(110))
        rotation = EXPECTED['cases']['exit_then_entry']
        self.assertEqual([(t['symbol'], t['entry_index'], t['exit_index']) for t in rotation['trades']],
                         [('TRF_A', 1, 3), ('TRF_B', 3, 5)])
        self.assertEqual(Decimal(rotation['rows'][3]['cash']), Decimal(40) + 130 - 2 * 65)
        self.assertEqual(Decimal(rotation['rows'][-1]['cash']), Decimal(150) + 20 + 20)
        self.assertEqual(EXPECTED['cases']['last_signal']['trades'], [])


class PolicyInputBoundary(unittest.TestCase):
    def test_exact_invented_prices_signals_and_costs_are_frozen(self):
        inventory = cases()
        self.assertEqual(set(inventory), set(EXPECTED['cases']))
        specifications = {
            'timing': ('1000', [('TRF_A', 2, 10, [0], [2])]),
            'costs': ('1000', [('TRF_A', 2, 10, [0], [2])]),
            'shared_cash': ('150', [('TRF_A', 1, 10, [0], [2]), ('TRF_B', 2, 20, [0], [2])]),
            'exit_then_entry': ('150', [('TRF_A', 1, 10, [0], [2]), ('TRF_B', 2, 20, [2], [4])]),
            'last_signal': ('1000', [('TRF_A', 1, 10, [7], [])])}
        for name, case in inventory.items():
            with self.subTest(case=name):
                before = deepcopy(case)
                self.assertEqual(policy.validate_case(case), case)
                self.assertEqual(case, before)
                self.assertTrue(case['synthetic'])
                self.assertEqual(case['schema'], 'synthetic-long-flat/1')
                self.assertEqual(case['start_utc'], '2023-01-01T00:00:00Z')
                self.assertEqual(case['bar_seconds'], 900)
                cash, assets = specifications[name]
                self.assertEqual(case['initial_cash'], cash)
                self.assertEqual([(a['symbol'], a['quantity'], a['rank'], a['buy'], a['sell']) for a in case['assets']], assets)
                for asset in case['assets']:
                    self.assertEqual(len(asset['bars']), 8)
                    for index, bar in enumerate(asset['bars']):
                        opening, close = OPENS[asset['symbol']][index], CLOSES[asset['symbol']][index]
                        self.assertEqual(bar, {'open': str(opening), 'close': str(close),
                            'high': str(max(opening, close) + 3), 'low': str(min(opening, close) - 3)})
                self.assertEqual(case['costs'], {
                    'commission_bps': '10' if name == 'costs' else '0',
                    'spread_bps': '5' if name == 'costs' else '0',
                    'slippage_bps': '5' if name == 'costs' else '0', 'impact_bps': '0',
                    'basis': 'synthetic_per_fill_notional', 'valid_for': 'fixture_only'})

    def test_unknown_semantics_fields_short_stop_and_leverage_are_rejected(self):
        for level, key, value in [('case', 'short', True), ('case', 'leverage', '2'),
                ('case', 'stop_loss', '5'), ('asset', 'short', [0]), ('asset', 'stop', '95'),
                ('cost', 'real_account_fees', 'verified'), ('bar', 'future_signal', True)]:
            case = deepcopy(cases()['timing'])
            target = {'case': case, 'asset': case['assets'][0], 'cost': case['costs'], 'bar': case['assets'][0]['bars'][0]}[level]
            target[key] = value
            with self.subTest(level=level, key=key), self.assertRaises(ValueError):
                policy.validate_case(case)

    def test_malformed_profile_grid_costs_quantities_and_ranks_are_rejected(self):
        mutations = [
            lambda c: c.update(schema='unapproved/1'), lambda c: c.update(synthetic=False),
            lambda c: c.update(start_utc='2023-01-01T00:00:00+01:00'), lambda c: c.update(bar_seconds=60),
            lambda c: c.update(initial_cash='NaN'), lambda c: c.update(initial_cash='-1'),
            lambda c: c['costs'].update(commission_bps='-1'), lambda c: c['costs'].update(spread_bps='Infinity'),
            lambda c: c['costs'].update(basis='unknown'), lambda c: c['costs'].update(valid_for='real_account'),
            lambda c: c['assets'][0].update(quantity=1.5), lambda c: c['assets'][0].update(quantity=True),
            lambda c: c['assets'][0].update(rank=0), lambda c: c['assets'][0].update(rank=-1),
            lambda c: c['assets'][0].update(buy=[8]), lambda c: c['assets'][0].update(buy=[True]),
            lambda c: c['assets'][0].update(sell=[0]), lambda c: c['assets'][0]['bars'].pop(),
            lambda c: c['assets'][0]['bars'][1].update(close='NaN'),
            lambda c: c['assets'][0]['bars'][1].update(low='999')]
        for index, mutate in enumerate(mutations):
            case = deepcopy(cases()['timing'])
            mutate(case)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                policy.validate_case(case)
        tied = deepcopy(cases()['shared_cash'])
        tied['assets'][1]['rank'] = tied['assets'][0]['rank']
        with self.assertRaises(ValueError):
            policy.validate_case(tied)


class PolicyExportVerifier(unittest.TestCase):
    def test_fixed_expected_outputs_and_declared_tolerance_are_accepted(self):
        for name, expected in EXPECTED['cases'].items():
            with self.subTest(case=name):
                self.assertEqual(policy.verify_result(deepcopy(expected), expected)['status'], 'PASS')
        expected = EXPECTED['cases']['costs']
        close = deepcopy(expected)
        close['rows'][1]['cash'] = str(Decimal(close['rows'][1]['cash']) + Decimal('0.0005'))
        close['trades'][0]['entry_price'] = str(Decimal(close['trades'][0]['entry_price']) + Decimal('0.000005'))
        self.assertEqual(policy.verify_result(close, expected)['status'], 'PASS')

    def test_wrong_timing_quantity_cash_count_and_nonfinite_exports_are_rejected(self):
        expected = EXPECTED['cases']['timing']
        mutations = [
            lambda a: a['trades'][0].update(entry_index=0), lambda a: a['trades'][0].update(exit_index=2),
            lambda a: a['trades'][0].update(quantity=1), lambda a: a['trades'][0].update(quantity='2.00001'),
            lambda a: a['trades'][0].update(symbol='TRF_B'), lambda a: a['trades'][0].update(entry_price='110.00002'),
            lambda a: a['trades'][0].update(entry_fee='0.002'), lambda a: a['trades'][0].update(pnl='40.002'),
            lambda a: a['rows'][1].update(cash='780.002'), lambda a: a['rows'][1].update(equity='NaN'),
            lambda a: a['rows'][1].update(timestamp='2023-01-01T00:00:00Z'),
            lambda a: a['rows'][1]['positions'].update(TRF_A=1), lambda a: a['rows'].pop(),
            lambda a: a['trades'].clear(), lambda a: a['trades'].append(deepcopy(a['trades'][0])),
            lambda a: a.update(ignored_extra='unsafe'), lambda a: a['trades'][0].update(ignored_extra='unsafe')]
        for index, mutate in enumerate(mutations):
            actual = deepcopy(expected)
            mutate(actual)
            with self.subTest(mutation=index), self.assertRaises(ValueError):
                policy.verify_result(actual, expected)

    def test_formula_build_is_deterministic_and_rejects_unapproved_requests(self):
        # This checks bounded pure generation only, not native behavior.
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for case in cases().values():
                self.assertEqual(policy.build_formula(case, output), policy.build_formula(deepcopy(case), output))
            wrong = deepcopy(cases()['timing'])
            wrong['stop'] = '95'
            with self.assertRaises(ValueError):
                policy.build_formula(wrong, output)

    def test_boolean_integer_confusion_and_malformed_containers_fail_typed(self):
        expected = EXPECTED['cases']['exit_then_entry']
        for mutate in (lambda a: a['trades'][0].update(quantity=True),
                       lambda a: a['trades'][0].update(entry_index=True),
                       lambda a: a['rows'][1]['positions'].update(TRF_A=True),
                       lambda a: a.update(rows=None), lambda a: a.update(trades=None)):
            actual = deepcopy(expected)
            mutate(actual)
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                policy.verify_result(actual, expected)


def native_tables(expected):
    states = [['index', 'timestamp', 'cash', 'equity']]
    positions = [['index', 'symbol', 'quantity']]
    trades = [['symbol', 'entry_timestamp', 'exit_timestamp', 'quantity', 'entry_price',
               'exit_price', 'entry_fee', 'exit_fee', 'pnl']]
    for index, row in enumerate(expected['rows']):
        states.append([index, row['timestamp'], row['cash'], row['equity']])
        positions.extend([index, symbol, quantity] for symbol, quantity in row['positions'].items() if quantity)
    for trade in expected['trades']:
        trades.append([trade['symbol'], expected['rows'][trade['entry_index']]['timestamp'],
            expected['rows'][trade['exit_index']]['timestamp'], trade['quantity'],
            *[trade[key] for key in ('entry_price', 'exit_price', 'entry_fee', 'exit_fee', 'pnl')]])
    return {'state.csv': states, 'positions.csv': positions, 'trades.csv': trades}


def write_tables(directory, tables):
    for name, rows in tables.items():
        with (directory / name).open('w', newline='', encoding='utf-8') as stream:
            csv.writer(stream).writerows(rows)


class NativeExportParser(unittest.TestCase):
    def test_apx_string_decoding_preserves_exact_external_formula_and_path(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            policy.write_inputs(cases()['timing'], output)
            raw = (output / 'policy.afl').read_bytes()
            project = ET.parse(output / 'policy.apx')
            embedded = project.findtext('General/FormulaContent')
            self.assertNotIn('\n', embedded)
            self.assertIn(r'\r\nSetOption(', embedded)
            self.assertEqual(raw, codecs.decode(embedded, 'unicode_escape').encode('ascii'))
            self.assertEqual(str(output / 'policy.afl'),
                codecs.decode(project.findtext('General/FormulaPath'), 'unicode_escape'))
            self.assertIn(b'\\n', raw)  # AFL string escape remains literal in the external formula.

    def test_exact_raw_exports_preserved_and_flat_positions_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name, expected in EXPECTED['cases'].items():
                with self.subTest(case=name):
                    write_tables(output, native_tables(expected))
                    self.assertEqual(policy.parse_native(cases()[name], output), expected)

    def test_wrong_native_time_quantity_cash_and_duplicates_are_not_repaired(self):
        expected = EXPECTED['cases']['timing']
        changes = [
            lambda t: t['state.csv'][2].__setitem__(1, '2023-01-01T00:00:00Z'),
            lambda t: t['state.csv'].pop(),
            lambda t: t['positions.csv'].append(deepcopy(t['positions.csv'][1])),
            lambda t: t['positions.csv'][1].__setitem__(2, 1),
            lambda t: t['trades.csv'][1].__setitem__(1, '2023-01-01T00:00:00Z'),
            lambda t: t['trades.csv'][1].__setitem__(2, '2023-01-01T02:00:00Z'),
            lambda t: t['trades.csv'][1].__setitem__(3, 1),
            lambda t: t['state.csv'][2].__setitem__(2, '999')]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for index, change in enumerate(changes):
                tables = native_tables(expected)
                change(tables)
                write_tables(output, tables)
                with self.subTest(mutation=index), self.assertRaises(ValueError):
                    policy.verify_result(policy.parse_native(cases()['timing'], output), expected)


class NativeProcessOwnership(unittest.TestCase):
    def test_existing_instance_blocks_before_process_or_output_creation(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(policy, 'ROOT', Path(directory)), \
                patch.object(policy, 'running_brokers', return_value=[12345]), \
                patch.object(policy.subprocess, 'Popen') as start, \
                patch.object(policy, 'host_call') as com:
            with self.assertRaisesRegex(RuntimeError, 'Existing AmiBroker'):
                policy.execute_case(cases()['timing'], EXPECTED['cases']['timing'], 1)
            start.assert_not_called()
            com.assert_not_called()
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_worker_timeout_and_cleanup_failure_kill_only_owned_process(self):
        # Every native/process entry point is replaced; only temporary request/
        # result files are real. This proves controller ownership logic, not COM.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / 'synthetic-Broker.exe'
            executable.write_bytes(b'non-executable mock fixture')
            owned = Mock()
            owned.poll.return_value = None
            def host_call(action, *args):
                if action == 'probe':
                    return {'version': '6.20.1'}
                if action == 'quit':
                    raise RuntimeError('Synthetic COM cleanup failure')
                raise AssertionError('Unexpected COM action')
            with patch.object(policy, 'ROOT', root), patch.object(policy, 'EXE', executable), \
                    patch.object(policy, 'running_brokers', return_value=[]), \
                    patch.object(policy.subprocess, 'Popen', return_value=owned) as start, \
                    patch.object(policy.subprocess, 'run', side_effect=subprocess.TimeoutExpired('synthetic-worker', 80,
                        output=b'stage=opening_analysis', stderr=b'synthetic timeout diagnostic')), \
                    patch.object(policy, 'host_call', side_effect=host_call), patch.object(policy.time, 'sleep'):
                result = policy.execute_case(cases()['timing'], EXPECTED['cases']['timing'], 1)
            self.assertEqual(result['status'], 'FAIL')
            self.assertIn('timed out', result['error'])
            self.assertTrue(result['timeout_output_retained'])
            diagnostic = (Path(result['run_directory']) / 'worker-output.txt').read_text()
            self.assertIn('stage=opening_analysis', diagnostic)
            self.assertIn('synthetic timeout diagnostic', diagnostic)
            self.assertIn('Synthetic COM cleanup failure', result['cleanup_error'])
            self.assertFalse(result['scientific_readiness'])
            owned.kill.assert_called_once_with()
            owned.wait.assert_called_once_with(timeout=10)
            args, kwargs = start.call_args
            self.assertEqual(args[0][:2], [str(executable), '/database'])
            self.assertTrue(Path(args[0][2]).resolve().is_relative_to(root.resolve()))
            self.assertEqual(kwargs['startupinfo'].wShowWindow, 0)
            saved = Path(result['run_directory']) / 'result.json'
            self.assertEqual(json.loads(saved.read_text()), result)


if __name__ == '__main__':
    unittest.main()
