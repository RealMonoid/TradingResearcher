"""Independent original-idea oracle for D094, not a research candidate.

Source: original retained idea 94cf7b732406785e98d1c5a42daccce4c43685fbf0471f517d2a960311c8e6c3,
with the explicitly adopted paired-development/1.0 as-of cap. This module
imports no framework evaluator, AST, compiler or market data. Exact Fraction
thresholds and independent stdlib Decimal logarithms check an actual candidate;
the oracle must never replace the model's candidate. Decimal(80) is a numerical
cross-check, not a rigorous outward-error certificate or scientific inference.

oracle(rows, start, end, as_of) takes integer UTC seconds and canonical raw
sample dictionaries. It returns every decision timestamp, conditions, outcomes,
status and neutral overlapping cause categories. Invalid raw values are marked
invalid_value; the certified source boundary must separately reject these
contradictions or retain its normalized nulls before framework execution.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
import unittest


IDEA_ID = '94cf7b732406785e98d1c5a42daccce4c43685fbf0471f517d2a960311c8e6c3'
PAIR = ('BTCUSDT', 'ETHUSDT')
STEP = 900
ORIGINAL_START = 1672531200
ORIGINAL_END = 1680307200
FIELDS = ('open', 'close', 'quote_volume', 'taker_quote_volume')


def _ref(member, field):
    return member + '.' + field + '@binance-spot-15m-v1'


def _number(value):
    if type(value) is not str:
        return None
    try:
        parsed = Decimal(value)
        return Fraction(parsed) if parsed.is_finite() else None
    except (InvalidOperation, ValueError, OverflowError):
        return None


def oracle(rows, start, end, as_of):
    if (any(type(value) is not int for value in (start, end, as_of))
            or start < 0 or start % STEP or end % STEP or not start < end
            or as_of < 0 or (end - start) // STEP > 50000
            or type(rows) is not list or len(rows) > 100000):
        raise ValueError('Bounded integer UTC interval and explicit canonical rows required')
    lookup = {}
    for row in rows:
        if (type(row) is not dict or set(row) != {'time', 'instrument', 'features'}
                or type(row['time']) is not int or row['time'] % STEP
                or not start <= row['time'] < end or row['instrument'] not in PAIR
                or type(row['features']) is not dict):
            raise ValueError('A supplied row is outside the declared fixed pair/grid')
        key = row['time'], row['instrument']
        if key in lookup:
            raise ValueError('Duplicate pair member observation')
        lookup[key] = row['features']

    def read(member, field, when, cutoff, reasons):
        if when < start:
            reasons.add('missing_warmup')
            return None
        if when >= end:
            reasons.add('boundary_censoring')
            return None
        samples = lookup.get((when, member))
        if samples is None:
            reasons.add('absent_row')
            return None
        identity = _ref(member, field)
        if identity not in samples:
            reasons.add('missing_feature')
            return None
        sample = samples[identity]
        if (type(sample) is not dict or set(sample) != {'value', 'available_at'}
                or type(sample['available_at']) is not int or sample['available_at'] < when):
            raise ValueError('Malformed per-sample availability evidence')
        if sample['available_at'] > cutoff:
            reasons.add('unavailable_data')
            return None
        if sample['value'] is None:
            reasons.add('missing_value')
            return None
        value = _number(sample['value'])
        if value is None:
            reasons.add('invalid_value')
        return value

    result = []
    for when in range(start, end, STEP):
        reasons = set()
        case = {'decision_time': when, 'scope': True, 'condition': None, 'outcome': None,
                'status': None, 'reason_categories': []}
        if when > as_of:
            # This adopted operational state is not reached in the closed Q1 run.
            case.update(scope=None, status='NOT_YET_OBSERVED')
            result.append(case)
            continue
        bars = {}
        complete = True
        # Read every original required value even if another clause is false.
        for member in PAIR:
            for ago in (2, 1):
                values = [read(member, field, when - ago * STEP, when, reasons) for field in FIELDS]
                bars[member, ago] = values
                if any(value is None for value in values):
                    complete = False
                    continue
                opening, closing, quote, taker = values
                if not (opening > 0 and closing > 0 and quote > 0 and 0 <= taker <= quote):
                    complete = False
                    reasons.add('invalid_value')
        if complete:
            btce, ethe, btcb, ethb = (bars[PAIR[0], 2], bars[PAIR[1], 2],
                                     bars[PAIR[0], 1], bars[PAIR[1], 1])
            case['condition'] = all((
                btce[1] / btce[0] - 1 <= Fraction(-4, 1000),
                ethe[1] / ethe[0] - 1 <= Fraction(-4, 1000),
                btce[3] / btce[2] <= Fraction(40, 100),
                ethe[3] / ethe[2] <= Fraction(40, 100),
                btcb[1] / btcb[0] - 1 >= Fraction(2, 1000),
                btcb[3] / btcb[2] >= Fraction(55, 100),
                ethb[1] / ethb[0] - 1 <= 0,
                ethb[3] / ethb[2] <= Fraction(45, 100),
            ))
        else:
            reasons.add('condition_unknown')
        anchor = when + 5 * STEP
        if anchor >= end:
            case['status'] = 'PARTITION_BOUNDARY'
            reasons.add('boundary_censoring')
        elif anchor > as_of:
            case['status'] = 'OUTCOME_PENDING'
        else:
            outcome_reasons = set()
            endpoints = {member: [read(member, 'close', point, min(anchor, as_of, end - 1), outcome_reasons)
                for point in (when, when + 4 * STEP)] for member in PAIR}
            valid = all(value is not None and value > 0 for values in endpoints.values() for value in values)
            if not valid:
                if any(value is not None and value <= 0 for values in endpoints.values() for value in values):
                    outcome_reasons.add('invalid_value')
                case['status'] = 'OUTCOME_PENDING' if 'unavailable_data' in outcome_reasons else 'OUTCOME_MISSING'
            else:
                with localcontext() as context:
                    context.prec = 80
                    logs = {}
                    for member, (first, last) in endpoints.items():
                        ratio = last / first
                        logs[member] = (Decimal(ratio.numerator) / Decimal(ratio.denominator)).ln()
                    case['outcome'] = Decimal(10000) * (logs['ETHUSDT'] - logs['BTCUSDT'])
                case['status'] = 'ELIGIBLE'
            reasons.update(outcome_reasons)
        case['reason_categories'] = sorted(reasons)
        result.append(case)
    return result


def _synthetic(count=8):
    rows = []
    for index in range(count):
        for member in PAIR:
            price = '100' if member == 'BTCUSDT' else '200'
            values = dict(open=price, close=price, quote_volume='100', taker_quote_volume='50')
            if index == 0:
                values.update(close='99.6' if member == 'BTCUSDT' else '199.2', taker_quote_volume='40')
            elif index == 1:
                values.update(close='100.2' if member == 'BTCUSDT' else '200',
                              taker_quote_volume='55' if member == 'BTCUSDT' else '45')
            when = ORIGINAL_START + index * STEP
            rows.append({'time': when, 'instrument': member,
                'features': {_ref(member, field): {'value': value, 'available_at': when + STEP}
                             for field, value in values.items()}})
    return rows


def _check(rows):
    return oracle(rows, ORIGINAL_START, ORIGINAL_START + 8 * STEP, ORIGINAL_START + 8 * STEP)


class OriginalOracleTests(unittest.TestCase):
    def test_inclusive_eight_boundaries_and_independent_false_sides(self):
        self.assertIs(_check(_synthetic())[2]['condition'], True)
        changes = ((0, 'close', '99.6001'), (1, 'close', '199.2001'),
            (0, 'taker_quote_volume', '40.0001'), (1, 'taker_quote_volume', '40.0001'),
            (2, 'close', '100.1999'), (2, 'taker_quote_volume', '54.9999'),
            (3, 'close', '200.0001'), (3, 'taker_quote_volume', '45.0001'))
        for index, field, value in changes:
            rows = _synthetic()
            rows[index]['features'][_ref(rows[index]['instrument'], field)]['value'] = value
            with self.subTest(index=index, field=field):
                self.assertIs(_check(rows)[2]['condition'], False)

    def test_every_missing_condition_input_overrides_an_independent_false_clause(self):
        for index in range(4):
            for field in FIELDS:
                rows = _synthetic()
                rows[0]['features'][_ref('BTCUSDT', 'close')]['value'] = '100'
                rows[index]['features'][_ref(rows[index]['instrument'], field)]['value'] = None
                case = _check(rows)[2]
                with self.subTest(index=index, field=field):
                    self.assertIsNone(case['condition'])
                    self.assertIn('condition_unknown', case['reason_categories'])
                    self.assertIn('missing_value', case['reason_categories'])

    def test_each_domain_rule_and_late_member_is_independent(self):
        for field, value in (('open', '0'), ('close', '-1'), ('quote_volume', '0'),
                             ('taker_quote_volume', '-1'), ('taker_quote_volume', '101'), ('close', 'NaN')):
            rows = _synthetic()
            rows[1]['features'][_ref('ETHUSDT', field)]['value'] = value
            with self.subTest(field=field, value=value):
                self.assertIsNone(_check(rows)[2]['condition'])
        rows = _synthetic()
        rows[3]['features'][_ref('ETHUSDT', 'close')]['available_at'] += 1
        self.assertIsNone(_check(rows)[2]['condition'])

    def test_full_grid_calendar_missingness_and_whole_scope_are_distinct(self):
        cases = _check(_synthetic())
        self.assertEqual(len(cases), 8)
        self.assertEqual([case['condition'] for case in cases], [None, None, True, False, False, False, False, False])
        self.assertEqual(sum(case['status'] == 'ELIGIBLE' for case in cases), 3)
        self.assertEqual(sum(case['status'] == 'PARTITION_BOUNDARY' for case in cases), 5)
        self.assertEqual(sum(case['condition'] is True and case['outcome'] is not None for case in cases), 1)
        self.assertEqual((ORIGINAL_END - ORIGINAL_START) // STEP, 8640)

    def test_actual_anchor_cutoff_denies_a_late_endpoint_despite_later_asof(self):
        rows = _synthetic()
        rows[13]['features'][_ref('ETHUSDT', 'close')]['available_at'] += 1
        cases = _check(rows)
        self.assertIs(cases[2]['condition'], True)
        self.assertEqual(cases[2]['status'], 'OUTCOME_PENDING')
        self.assertIsNone(cases[2]['outcome'])
        self.assertIn('unavailable_data', cases[2]['reason_categories'])

    def test_log_sign_scale_and_both_negative_endpoint_rejection(self):
        rows = _synthetic()
        rows[13]['features'][_ref('ETHUSDT', 'close')]['value'] = '400'
        with localcontext() as context:
            context.prec = 80
            self.assertEqual(_check(rows)[2]['outcome'], Decimal(10000) * Decimal(2).ln())
        rows[12]['features'][_ref('BTCUSDT', 'close')]['value'] = '200'
        self.assertEqual(_check(rows)[2]['outcome'], 0)
        for index in (5, 13):
            rows[index]['features'][_ref('ETHUSDT', 'close')]['value'] = '-200'
        self.assertIsNone(_check(rows)[2]['outcome'])

    def test_absent_member_never_shrinks_grid_and_source_bytes_are_unchanged(self):
        rows = _synthetic()
        rows = [row for row in rows if not (row['time'] == ORIGINAL_START and row['instrument'] == 'ETHUSDT')]
        before = deepcopy(rows)
        cases = _check(rows)
        self.assertEqual(len(cases), 8)
        self.assertIsNone(cases[2]['condition'])
        self.assertIsNotNone(cases[2]['outcome'])
        self.assertIn('absent_row', cases[2]['reason_categories'])
        self.assertEqual(rows, before)

    def test_duplicate_outside_and_malformed_availability_are_not_silently_normalized(self):
        for kind in ('duplicate', 'before', 'after', 'availability'):
            rows = _synthetic()
            if kind == 'duplicate': rows.append(deepcopy(rows[0]))
            elif kind == 'before': rows[0]['time'] -= STEP
            elif kind == 'after': rows[-1]['time'] += STEP
            else: next(iter(rows[0]['features'].values()))['available_at'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                _check(rows)


if __name__ == '__main__':
    unittest.main()
