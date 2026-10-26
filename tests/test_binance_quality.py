"""Invalid keyed inputs stay distinct from absent and valid complete bars."""
import hashlib
import json
from pathlib import Path
import unittest

from trading_researcher.codec import Invalid
from trading_researcher.binance_archive import parse_month
from trading_researcher.binance_quality import audit_month, quality_reference_rows


def row(opened=1577836800000, close=None, price='10', ending='\n'):
    closed = opened+899999 if close is None else close
    return f'{opened},{price},12,9,11,5,{closed},52,3,2,21,0{ending}'.encode()


class QualityTests(unittest.TestCase):
    def test_independently_fixed_quality_cases(self):
        raw_fixture = (Path(__file__).parent/'fixtures/reference_binance_quality_cases.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw_fixture).hexdigest(), 'c71da72c766f01a055590b65bf9ddcc84add0bde15a6b114d79007217a34c67a')
        cases = json.loads(raw_fixture)['cases']
        self.assertEqual(len(cases), 32)
        for case in cases:
            with self.subTest(case=case['name']):
                expected = case['expected']
                raw = case['raw_csv'].encode('utf-8')
                args = raw, case['symbol'], case['month']
                if not expected['accepted']:
                    with self.assertRaises(Invalid):
                        audit_month(*args)
                    with self.assertRaises(Invalid):
                        quality_reference_rows(*args, delay_seconds=case['delay_seconds'])
                    continue
                actual = audit_month(*args)
                for key in ('schema', 'source_sha256', 'records', 'coverage', 'expected_end_definition', 'scientific_readiness'):
                    self.assertEqual(actual[key], expected[key])
                self.assertEqual(expected['historical_publication'], 'UNKNOWN')
                self.assertEqual(actual['availability'], 'UNKNOWN_HISTORICAL_PUBLICATION')
                if expected['strict_parser_accepted']:
                    strict = parse_month(*args)
                    self.assertEqual(strict['bars'], [record['bar'] for record in actual['records']])
                else:
                    with self.assertRaises(Invalid):
                        parse_month(*args)
                normalized = quality_reference_rows(*args, delay_seconds=case['delay_seconds'])
                self.assertEqual(normalized['rows'], expected['reference_rows'])
                self.assertEqual(normalized['availability']['basis'], expected['reference_availability_basis'])
                self.assertIsNone(normalized['availability']['historical_publication_time'])
                self.assertIs(normalized['scientific_readiness'], False)

    def test_invalid_present_and_absent_are_distinct_without_repair(self):
        good = row(ending='\r\n')
        bad = row(1577837700000, close=1577838000000)
        later = row(1577839500000)
        raw = good+bad+later
        with self.assertRaises(Invalid):
            parse_month(raw, 'BTCUSDT', '2020-01')
        result = audit_month(raw, 'BTCUSDT', '2020-01')
        self.assertEqual(result['source_sha256'], hashlib.sha256(raw).hexdigest())
        coverage = result['coverage']
        self.assertEqual([coverage[k] for k in ('expected_bars','present_bars','valid_bars','invalid_bars','missing_bars')], [2976,3,2,1,2973])
        record = result['records'][1]
        self.assertEqual(record['status'], 'INVALID_BAR')
        self.assertEqual(record['reason'], 'INVALID_CLOSE_TIME')
        self.assertIsNone(record['bar'])
        self.assertEqual(record['end_time'], 1577838600)
        self.assertEqual(record['raw_line_sha256'], hashlib.sha256(bad).hexdigest())
        self.assertEqual(result['records'][0]['raw_line_sha256'], hashlib.sha256(good).hexdigest())
        self.assertIn('expected grid boundary', result['expected_end_definition'])
        self.assertIs(result['scientific_readiness'], False)

    def test_null_rows_preserve_unavailability_and_explicit_scenario(self):
        raw = row()+row(1577837700000, price='-1')
        result = quality_reference_rows(raw, 'BTCUSDT', '2020-01', delay_seconds=5)
        self.assertEqual(len(result['rows']), 2)
        self.assertEqual(len(result['catalog']), 9)
        bad = result['rows'][1]
        self.assertEqual(bad['time'], 1577838600)
        self.assertTrue(all(sample['value'] is None and sample['available_at']==1577838605 for sample in bad['features'].values()))
        self.assertEqual(result['availability']['basis'], 'assumed')
        self.assertIsNone(result['availability']['historical_publication_time'])
        self.assertIs(result['scientific_readiness'], False)
        with self.assertRaises(TypeError):
            quality_reference_rows(raw, 'BTCUSDT', '2020-01')
        for delay in (True,-1,'0'):
            with self.subTest(delay=delay), self.assertRaises(Invalid):
                quality_reference_rows(raw, 'BTCUSDT', '2020-01', delay_seconds=delay)

    def test_ambiguous_source_is_not_partially_salvaged(self):
        for raw in (row()+row(), row()+row(1577836800001), row()+b'bad,layout\n',
                    row()+b'1577837700000,"1\n0",12,9,11,5,1577838599999,52,3,2,21,0\n',
                    row()+b'\n', b'', b'\xff', row(1577837700000)+row()):
            with self.subTest(raw=raw[-80:]), self.assertRaises(Invalid):
                audit_month(raw, 'BTCUSDT', '2020-01')

    def test_all_invalid_source_stays_non_scientific_and_has_no_zero_imputation(self):
        result = quality_reference_rows(row(price='NaN'), 'ETHUSDT','2020-01',delay_seconds=0)
        self.assertEqual(result['quality']['coverage']['valid_bars'], 0)
        self.assertEqual(result['quality']['coverage']['invalid_bars'], 1)
        self.assertTrue(all(v['value'] is None for v in result['rows'][0]['features'].values()))
        self.assertIs(result['scientific_readiness'], False)


if __name__ == '__main__':
    unittest.main()
