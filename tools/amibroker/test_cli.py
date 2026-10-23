"""Data-boundary tests; no AmiBroker process or network required."""
import csv
import io
import unittest
import zipfile
from hashlib import sha256

from cli import parse_klines, unpack_verified, verify_export


def source_rows():
    rows = []
    for i in range(96):
        t = 1577836800000 + i * 900000
        rows.append([str(t), '100', '102', '99', '101', '5', str(t+899999),
                     '505', '3', '2', '202', '0'])
    return rows


def render(rows):
    output = io.StringIO()
    csv.writer(output).writerows(rows)
    return output.getvalue()


class DataBoundaryTests(unittest.TestCase):
    def test_exact_utc_day_and_closed_bar_timestamps(self):
        rows = parse_klines(render(source_rows()))
        self.assertEqual(len(rows), 96)
        self.assertEqual(rows[0]['date'], '2020-01-01')
        self.assertEqual(rows[0]['time'], '00:15:00')
        self.assertEqual(rows[-1]['date'], '2020-01-02')
        self.assertEqual(rows[-1]['time'], '00:00:00')

    def test_gaps_and_duplicates_rejected(self):
        for rows in (source_rows()[:-1], source_rows()[:95]+[source_rows()[94]]):
            with self.assertRaises(ValueError):
                parse_klines(render(rows))

    def test_unknown_units_and_bad_ohlc_rejected(self):
        for field, value in ((0, '1577836800000000'), (2, '98'), (4, 'NaN')):
            rows = source_rows()
            rows[0][field] = value
            with self.assertRaises(ValueError):
                parse_klines(render(rows))

    def test_checksum_and_member_name_enforced(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as z:
            z.writestr('fixture.csv', b'test\r\nnext\n')
        payload = output.getvalue()
        checksum = sha256(payload).hexdigest() + '  fixture.zip'
        self.assertEqual(unpack_verified(payload, checksum, 'fixture.zip'), b'test\r\nnext\n')
        with self.assertRaises(ValueError):
            unpack_verified(payload, '0'*64+'  fixture.zip', 'fixture.zip')
        with self.assertRaises(ValueError):
            unpack_verified(payload, checksum, 'different.zip')

    def test_export_requires_exact_timestamps_and_calculations(self):
        rows = parse_klines(render(source_rows()))
        data = [['Day', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume', 'LagClose', 'MA3', 'Interval']]
        for i, row in enumerate(rows):
            day = 1200101 if i < 95 else 1200102
            hhmmss = int(row['time'].replace(':', ''))
            data.append([day, hhmmss, 100, 102, 99, 101, 5,
                         '' if i == 0 else 101, '' if i < 2 else 101, 900])
        self.assertEqual(verify_export(render(data), rows)['rows'], 96)
        for column, wrong in ((0, 1200102), (5, 999), (7, 100), (8, 100), (9, 86400)):
            altered = [r[:] for r in data]
            altered[4][column] = wrong
            with self.assertRaises(ValueError):
                verify_export(render(altered), rows)

    def test_export_missing_or_extra_rows_rejected(self):
        with self.assertRaises(ValueError):
            verify_export('Day,Time,Open,High,Low,Close,Volume,LagClose,MA3,Interval\n',
                          parse_klines(render(source_rows())))

    def test_empty_export_rejected_with_validation_error(self):
        with self.assertRaises(ValueError):
            verify_export('', parse_klines(render(source_rows())))


if __name__ == '__main__':
    unittest.main()
