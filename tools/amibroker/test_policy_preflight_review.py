"""Independent accounting and APX regression checks; no native application launch."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

import policy_preflight as policy


HERE = Path(__file__).resolve().parent
FROZEN = {
    'policy_cases.json': '81bd3aee784ab2fc2eed6080a16f61053b5582c8e1e81f52c7da4aa8d5068fd7',
    'policy_expected.json': 'ed8a5d46d275f6d436708775f6f9290947de2f675411476293cc78ef1ddfec83',
}


class IndependentPreflightReview(unittest.TestCase):
    def test_original_fixed_files_and_all_expected_cash_paths(self):
        # Reconstruct the tiny declared convention from requests. This is an
        # independent check on fixed expectations, never replacement native data.
        for name, wanted in FROZEN.items():
            self.assertEqual(hashlib.sha256((HERE / 'fixtures' / name).read_bytes()).hexdigest(), wanted)
        requests = json.loads((HERE / 'fixtures/policy_cases.json').read_text())['cases']
        fixed = json.loads((HERE / 'fixtures/policy_expected.json').read_text())['cases']
        for case in requests:
            with self.subTest(case=case['id']):
                d = Decimal
                cash = d(case['initial_cash'])
                opened, trades = {}, []
                holdings = {asset['symbol']: 0 for asset in case['assets']}
                rate = d(case['costs']['commission_bps']) / 10000
                adverse = sum(d(case['costs'][name]) for name in
                    ('spread_bps', 'slippage_bps', 'impact_bps')) / 10000
                for index, row in enumerate(fixed[case['id']]['rows']):
                    # All signals belong to the preceding bar close. No signal
                    # at index seven has an available next bar in this fixture.
                    for asset in case['assets']:
                        symbol = asset['symbol']
                        if index - 1 in asset['sell'] and symbol in opened:
                            entry_index, entry_price, entry_fee = opened.pop(symbol)
                            price = d(asset['bars'][index]['open']) * (1 - adverse)
                            notional = price * asset['quantity']
                            fee = notional * rate
                            cash += notional - fee
                            holdings[symbol] = 0
                            trades.append({'symbol': symbol, 'entry_index': entry_index,
                                'exit_index': index, 'quantity': asset['quantity'],
                                'entry_price': entry_price, 'exit_price': price,
                                'entry_fee': entry_fee, 'exit_fee': fee,
                                'pnl': (price - entry_price) * asset['quantity'] - entry_fee - fee})
                    for asset in sorted(case['assets'], key=lambda item: -item['rank']):
                        symbol = asset['symbol']
                        if index - 1 in asset['buy'] and symbol not in opened:
                            price = d(asset['bars'][index]['open']) * (1 + adverse)
                            notional = price * asset['quantity']
                            fee = notional * rate
                            if notional + fee <= cash:
                                cash -= notional + fee
                                holdings[symbol] = asset['quantity']
                                opened[symbol] = (index, price, fee)
                    equity = cash + sum(d(asset['bars'][index]['close']) * holdings[asset['symbol']]
                        for asset in case['assets'])
                    self.assertEqual((cash, equity, holdings),
                        (d(row['cash']), d(row['equity']), row['positions']))
                self.assertEqual(len(trades), len(fixed[case['id']]['trades']))
                for observed, wanted in zip(trades, fixed[case['id']]['trades']):
                    self.assertEqual(set(observed), set(wanted))
                    for key, value in observed.items():
                        self.assertEqual(value, d(wanted[key]) if isinstance(value, Decimal) else wanted[key])
                self.assertEqual(opened, {})

    def test_apx_settings_preserve_observed_native_reader_order(self):
        # Native 061054 (Periodicity before TradeFlags) produced one daily bar;
        # 061149 with these same values reordered produced eight 900s bars and
        # the fixed native trade. The APXCreator DATA template uses this order.
        case = next(case for case in policy.load_cases() if case['id'] == 'timing')
        with tempfile.TemporaryDirectory() as directory:
            policy.write_inputs(case, Path(directory))
            settings = ET.parse(Path(directory) / 'policy.apx').find('BacktestSettings')
            self.assertEqual([(node.tag, node.text) for node in settings], [
                ('TradeFlags', '1'), ('Periodicity', '3'), ('UseConstantPriceArrays', '0'),
                ('AlignToReferenceSymbol', '0'), ('AddFutureBars', '0'),
                ('LimitTradeSizeAsPctVol', '0')])


if __name__ == '__main__':
    unittest.main()
