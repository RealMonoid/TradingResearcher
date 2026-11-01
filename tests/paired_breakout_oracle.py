"""Independent direct-formula oracle for the second retained D093 idea.

Original source: 4abce1d5187d7fd229b52dd9a00e0beca8ee3947e9a1470dbc5351ff78c8872a.
No framework, evaluator, compiler, AST or prior oracle is imported. The original
maxima and mean are calculated directly over all sixteen exact prior slots.
The output is an expectation for a separately authored candidate, never H_exec.
Decimal100 is an independent numerical check, not a formal interval certificate.

Contradictory canonical prices/nonfinite values are classified invalid_value.
The host must separately enforce the certified raw domain / invalid-to-null
boundary; valid qualification scenarios use canonical values and retained nulls.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation, localcontext
from fractions import Fraction
import random
import unittest

IDEA_ID = '4abce1d5187d7fd229b52dd9a00e0beca8ee3947e9a1470dbc5351ff78c8872a'
ORIGINAL_START = 1672531200
ORIGINAL_END = 1680307200
STEP = 900
PAIR = ('BTCUSDT', 'ETHUSDT')
SCENARIO_LENGTH = 30
FOCAL_INDEX = 20
FIELDS = {'ETHUSDT': ('open', 'high', 'close', 'quote_volume'), 'BTCUSDT': ('high', 'close')}


def ref(symbol, field):
    return symbol + '.' + field + '@binance-spot-15m-v1'


def required(when):
    signal = when - STEP
    values = [(signal, 'ETHUSDT', field) for field in ('close', 'open', 'quote_volume')]
    values.append((signal, 'BTCUSDT', 'close'))
    values.extend((signal - k*STEP, symbol, field) for k in range(1, 17)
        for symbol, field in (('ETHUSDT', 'high'), ('BTCUSDT', 'high'), ('ETHUSDT', 'quote_volume')))
    return tuple(values)


def oracle(rows, start, end, as_of):
    if (any(type(value) is not int for value in (start, end, as_of)) or start < 0 or as_of < 0
            or start % STEP or end % STEP or not start < end or (end-start)//STEP > 50000
            or type(rows) is not list or len(rows) > 100000):
        raise ValueError('Explicit bounded integer grid and canonical rows required')
    observations = {}
    for row in rows:
        if (type(row) is not dict or set(row) != {'time', 'instrument', 'features'}
                or type(row['time']) is not int or row['time'] % STEP
                or not start <= row['time'] < end or row['instrument'] not in PAIR
                or type(row['features']) is not dict):
            raise ValueError('Invalid pair member, row coordinate or feature map')
        key = row['time'], row['instrument']
        if key in observations:
            raise ValueError('Duplicate source observation')
        observations[key] = row['features']

    def read(when, symbol, field, cutoff, reasons):
        if when < start:
            reasons.add('missing_warmup')
            return None
        if when >= end:
            reasons.add('boundary_censoring')
            return None
        values = observations.get((when, symbol))
        if values is None:
            reasons.add('absent_row')
            return None
        entry = values.get(ref(symbol, field))
        if entry is None:
            reasons.add('missing_feature')
            return None
        if (type(entry) is not dict or set(entry) != {'value', 'available_at'}
                or type(entry['available_at']) is not int or entry['available_at'] < when):
            raise ValueError('Malformed explicit per-value availability')
        if max(when + STEP, entry['available_at']) > cutoff:
            reasons.add('unavailable_data')
            return None
        if entry['value'] is None:
            reasons.add('missing_value')
            return None
        if type(entry['value']) is not str:
            reasons.add('invalid_value')
            return None
        try:
            number = Decimal(entry['value'])
            if not number.is_finite():
                raise ValueError('Nonfinite value')
            value = Fraction(number)
        except (InvalidOperation, ValueError, OverflowError):
            reasons.add('invalid_value')
            return None
        if value < 0 or (field != 'quote_volume' and value == 0):
            reasons.add('invalid_value')
            return None
        return value

    output = []
    for when in range(start, end, STEP):
        causes = set()
        case = {'decision_time': when, 'scope': True, 'condition': None,
            'outcome': None, 'status': None, 'reason_categories': []}
        if when > as_of:
            case.update(scope=None, status='NOT_YET_OBSERVED')
            output.append(case)
            continue
        inputs = {key: read(*key, when, causes) for key in required(when)}
        if all(value is not None for value in inputs.values()):
            signal = when - STEP
            eth_close, eth_open, signal_quote = (inputs[(signal, 'ETHUSDT', field)]
                for field in ('close', 'open', 'quote_volume'))
            btc_close = inputs[(signal, 'BTCUSDT', 'close')]
            eth_high = max(inputs[(signal-k*STEP, 'ETHUSDT', 'high')] for k in range(1, 17))
            btc_high = max(inputs[(signal-k*STEP, 'BTCUSDT', 'high')] for k in range(1, 17))
            mean_quote = sum((inputs[(signal-k*STEP, 'ETHUSDT', 'quote_volume')]
                for k in range(1, 17)), Fraction(0)) / 16
            if signal_quote == 0 or mean_quote == 0:
                causes.add('invalid_value')
            else:
                case['condition'] = all((eth_close/eth_high-1 >= Fraction(1, 1000),
                    eth_close/eth_open-1 >= Fraction(1, 1000),
                    signal_quote <= Fraction(3, 4)*mean_quote, btc_close <= btc_high))
        if case['condition'] is None:
            causes.add('condition_unknown')
        anchor = when + 5*STEP
        if anchor >= end:
            case['status'] = 'PARTITION_BOUNDARY'
            causes.add('boundary_censoring')
        elif anchor > as_of:
            case['status'] = 'OUTCOME_PENDING'
        else:
            outcome_causes = set()
            prices = {symbol: (read(when, symbol, 'close', min(anchor, end-1, as_of), outcome_causes),
                read(when+4*STEP, symbol, 'close', min(anchor, end-1, as_of), outcome_causes)) for symbol in PAIR}
            if any(value is None for pair in prices.values() for value in pair):
                case['status'] = 'OUTCOME_PENDING' if 'unavailable_data' in outcome_causes else 'OUTCOME_MISSING'
            else:
                with localcontext() as context:
                    context.prec = 100
                    eth = prices['ETHUSDT'][1] / prices['ETHUSDT'][0]
                    btc = prices['BTCUSDT'][1] / prices['BTCUSDT'][0]
                    case['outcome'] = Decimal(10000) * ((Decimal(eth.numerator)/Decimal(eth.denominator)).ln()
                        - (Decimal(btc.numerator)/Decimal(btc.denominator)).ln())
                case['status'] = 'ELIGIBLE'
            causes.update(outcome_causes)
        case['reason_categories'] = sorted(causes)
        output.append(case)
    return output


def synthetic():
    rows = []
    for index in range(SCENARIO_LENGTH):
        when = ORIGINAL_START + index*STEP
        for symbol in PAIR:
            values = ({'open': '100', 'high': '100', 'close': '100', 'quote_volume': '100'}
                if symbol == 'ETHUSDT' else {'high': '200', 'close': '200'})
            if index == FOCAL_INDEX-1 and symbol == 'ETHUSDT':
                values.update(close='100.1', high='101', quote_volume='75')
            if index == FOCAL_INDEX+4:
                values.update(close='102' if symbol == 'ETHUSDT' else '202',
                    high='103' if symbol == 'ETHUSDT' else '203')
            rows.append({'time': when, 'instrument': symbol, 'features': {
                ref(symbol, field): {'value': value, 'available_at': when+STEP} for field, value in values.items()}})
    return rows


def sample(rows, index, symbol, field):
    row = next(row for row in rows if (row['time'], row['instrument']) == (ORIGINAL_START+index*STEP, symbol))
    return row['features'][ref(symbol, field)]


def scenarios():
    """Finite independently fixed inventory; no outcome-dependent selection."""
    base = synthetic()
    yield 'inclusive_four_thresholds', base, None
    for kind in ('eth_breakout', 'eth_signal_rise', 'quote_shortfall', 'btc_nonbreakout'):
        for side in ('below', 'equal', 'above'):
            rows = deepcopy(base)
            index, symbol, field = FOCAL_INDEX-1, 'ETHUSDT', 'close'
            if kind == 'eth_breakout':
                sample(rows, index, symbol, 'open')['value'] = '99'
                values = {'below': '100.0999', 'equal': '100.1', 'above': '100.1001'}
            elif kind == 'eth_signal_rise':
                for i in range(FOCAL_INDEX-17, FOCAL_INDEX-1):
                    for f in ('open', 'close'): sample(rows, i, symbol, f)['value'] = '98'
                    sample(rows, i, symbol, 'high')['value'] = '99'
                values = {'below': '100.0999', 'equal': '100.1', 'above': '100.1001'}
            elif kind == 'quote_shortfall':
                field = 'quote_volume'
                values = {'below': '74.9999', 'equal': '75', 'above': '75.0001'}
            else:
                symbol = 'BTCUSDT'
                values = {'below': '199.9999', 'equal': '200', 'above': '200.0001'}
            sample(rows, index, symbol, field)['value'] = values[side]
            yield 'threshold/'+kind+'/'+side, rows, None
    for symbol in PAIR:
        for offset in range(1, 17):
            for eth_blocker in ((False, True) if symbol == 'ETHUSDT' else (False,)):
                rows = deepcopy(base)
                for index in range(FOCAL_INDEX-17, FOCAL_INDEX-1):
                    sample(rows, index, symbol, 'high')['value'] = '99' if symbol == 'ETHUSDT' else '199'
                    sample(rows, index, symbol, 'close')['value'] = '98' if symbol == 'ETHUSDT' else '198'
                    if symbol == 'ETHUSDT': sample(rows, index, symbol, 'open')['value'] = '98'
                sample(rows, FOCAL_INDEX-1-offset, symbol, 'high')['value'] = (
                    '100.1' if eth_blocker else '100') if symbol == 'ETHUSDT' else '200'
                yield 'unique_max/'+symbol+'/'+str(offset)+'/'+str(eth_blocker), rows, None
    when = ORIGINAL_START + FOCAL_INDEX*STEP
    for instant, symbol, field in required(when):
        index = (instant-ORIGINAL_START)//STEP
        for mode in ('null', 'missing_feature', 'late'):
            rows = deepcopy(base)
            # A known false independent clause must not mask incomplete inputs.
            sample(rows, FOCAL_INDEX-1, 'ETHUSDT', 'quote_volume')['value'] = '101'
            entry = sample(rows, index, symbol, field)
            if mode == 'null': entry['value'] = None
            elif mode == 'late': entry['available_at'] = when+1
            else:
                next(row for row in rows if (row['time'], row['instrument']) == (instant, symbol))['features'].pop(ref(symbol, field))
            yield 'required/'+str(index)+'/'+symbol+'/'+field+'/'+mode, rows, None
    for instant, symbol in sorted({(s, symbol) for s, symbol, field in required(when)}):
        rows = [deepcopy(row) for row in base if (row['time'], row['instrument']) != (instant, symbol)]
        yield 'missing_container/'+str((instant-ORIGINAL_START)//STEP)+'/'+symbol, rows, None
    for offset in range(1, 17):
        rows = deepcopy(base)
        sample(rows, FOCAL_INDEX-1-offset, 'ETHUSDT', 'quote_volume')['value'] = '0'
        sample(rows, FOCAL_INDEX-1, 'ETHUSDT', 'quote_volume')['value'] = '50'
        yield 'valid_zero_baseline/'+str(offset), rows, None
    for kind in ('signal', 'mean', 'both'):
        rows = deepcopy(base)
        if kind in ('signal', 'both'): sample(rows, FOCAL_INDEX-1, 'ETHUSDT', 'quote_volume')['value'] = '0'
        if kind in ('mean', 'both'):
            for offset in range(1, 17): sample(rows, FOCAL_INDEX-1-offset, 'ETHUSDT', 'quote_volume')['value'] = '0'
        yield 'undefined_volume/'+kind, rows, None
    for symbol, mode in (('BTCUSDT', 'or_true_other_missing'), ('ETHUSDT', 'and_false_other_missing')):
        rows = deepcopy(base)
        sample(rows, FOCAL_INDEX-2, symbol, 'high')['value'] = None
        if symbol == 'ETHUSDT': sample(rows, FOCAL_INDEX-1, symbol, 'close')['value'] = '99'
        yield mode, rows, None
    for symbol in PAIR:
        for index in (FOCAL_INDEX, FOCAL_INDEX+4):
            for mode in ('null', 'late', 'missing_feature'):
                rows = deepcopy(base)
                entry = sample(rows, index, symbol, 'close')
                if mode == 'null': entry['value'] = None
                elif mode == 'late': entry['available_at'] = when+5*STEP+1
                else:
                    next(row for row in rows if (row['time'], row['instrument']) == (ORIGINAL_START+index*STEP, symbol))['features'].pop(ref(symbol, 'close'))
                yield 'endpoint/'+symbol+'/'+str(index)+'/'+mode, rows, None
        for index in (FOCAL_INDEX, FOCAL_INDEX+5):
            rows = [deepcopy(row) for row in base if (row['time'], row['instrument']) != (ORIGINAL_START+index*STEP, symbol)]
            yield 'unused_condition_or_anchor/'+symbol+'/'+str(index), rows, None
    for numerator in ('50', '100', '200'):
        rows = deepcopy(base)
        sample(rows, FOCAL_INDEX+4, 'ETHUSDT', 'close')['value'] = numerator
        sample(rows, FOCAL_INDEX+4, 'BTCUSDT', 'close')['value'] = '200'
        yield 'log_sign/'+numerator, rows, None
    for offset in (0, FOCAL_INDEX, FOCAL_INDEX+5):
        yield 'as_of/'+str(offset), deepcopy(base), ORIGINAL_START+offset*STEP
    for seed in range(5):
        rows = deepcopy(base)
        randomizer = random.Random(1000+seed)
        for row in rows:
            symbol = row['instrument']
            prices = [randomizer.randrange(100, 100000) for _ in range(2)]
            index = (row['time']-ORIGINAL_START)//STEP
            sample(rows, index, symbol, 'close')['value'] = str(Decimal(prices[0])/100)
            sample(rows, index, symbol, 'high')['value'] = str(Decimal(max(prices))/100+1)
            if symbol == 'ETHUSDT':
                sample(rows, index, symbol, 'open')['value'] = str(Decimal(prices[1])/100)
                sample(rows, index, symbol, 'quote_volume')['value'] = str(randomizer.randrange(1, 1001))
        yield 'independent_complete_values/'+str(seed), rows, None


def checked(rows, as_of=None):
    end = ORIGINAL_START + SCENARIO_LENGTH*STEP
    return oracle(rows, ORIGINAL_START, end, end if as_of is None else as_of)


class BreakoutOracleTests(unittest.TestCase):
    def test_four_exact_thresholds_and_independent_sides(self):
        for name, rows, as_of in scenarios():
            if name.startswith('threshold/'):
                kind, side = name.split('/')[1:]
                expected = side != ('below' if kind.startswith('eth_') else 'above')
                with self.subTest(name=name): self.assertIs(checked(rows)[FOCAL_INDEX]['condition'], expected)
        self.assertIs(checked(synthetic())[FOCAL_INDEX]['condition'], True)

    def test_each_of_52_required_values_is_unknown_even_with_another_false_clause(self):
        self.assertEqual(len(set(required(ORIGINAL_START+FOCAL_INDEX*STEP))), 52)
        count = 0
        for name, rows, as_of in scenarios():
            if name.startswith('required/'):
                with self.subTest(name=name):
                    case = checked(rows)[FOCAL_INDEX]
                    self.assertIsNone(case['condition'])
                    self.assertIn('condition_unknown', case['reason_categories'])
                count += 1
        self.assertEqual(count, 156)

    def test_unique_max_at_each_exact_position_is_not_mean_or_first_observation(self):
        count = 0
        for name, rows, as_of in scenarios():
            if name.startswith('unique_max/'):
                with self.subTest(name=name):
                    self.assertIs(checked(rows)[FOCAL_INDEX]['condition'], not name.endswith('/True'))
                count += 1
        self.assertEqual(count, 48)

    def test_zero_baseline_is_valid_but_zero_signal_or_entire_mean_is_unknown(self):
        for name, rows, as_of in scenarios():
            if name.startswith(('valid_zero_baseline/', 'undefined_volume/')):
                with self.subTest(name=name):
                    self.assertIs(checked(rows)[FOCAL_INDEX]['condition'], True if name.startswith('valid_') else None)

    def test_short_circuit_counterexamples_and_missing_unused_containers(self):
        for name, rows, as_of in scenarios():
            if name in ('or_true_other_missing', 'and_false_other_missing'):
                self.assertIsNone(checked(rows)[FOCAL_INDEX]['condition'])
            if name.startswith('unused_condition_or_anchor/'):
                case = checked(rows)[FOCAL_INDEX]
                self.assertIs(case['condition'], True)
                self.assertEqual(case['status'], 'ELIGIBLE' if name.endswith('/25') else 'OUTCOME_MISSING')

    def test_calendar_full_grid_and_complete_warmup_without_thinning(self):
        cases = checked(synthetic())
        self.assertEqual(len(cases), 30)
        self.assertEqual([case['condition'] for case in cases[:17]], [None]*17)
        self.assertIsNotNone(cases[17]['condition'])
        self.assertEqual(sum(case['status'] == 'PARTITION_BOUNDARY' for case in cases), 5)
        self.assertEqual(sum(case['status'] == 'ELIGIBLE' for case in cases), 25)
        self.assertEqual((ORIGINAL_END-ORIGINAL_START)//STEP, 8640)
        self.assertTrue(all(case['scope'] is True for case in cases))

    def test_every_endpoint_has_own_positivity_and_availability_not_ratio_only(self):
        for symbol in PAIR:
            for index in (FOCAL_INDEX, FOCAL_INDEX+4):
                for value in ('0', '-1', 'NaN', 'Infinity', None):
                    rows = synthetic()
                    sample(rows, index, symbol, 'close')['value'] = value
                    with self.subTest(symbol=symbol, index=index, value=value):
                        self.assertIsNone(checked(rows)[FOCAL_INDEX]['outcome'])
                rows = synthetic()
                sample(rows, index, symbol, 'close')['available_at'] = ORIGINAL_START+(FOCAL_INDEX+5)*STEP+1
                case = checked(rows)[FOCAL_INDEX]
                self.assertEqual(case['status'], 'OUTCOME_PENDING')
                self.assertIn('unavailable_data', case['reason_categories'])
            rows = synthetic()
            for index in (FOCAL_INDEX, FOCAL_INDEX+4): sample(rows, index, symbol, 'close')['value'] = '-100'
            self.assertIsNone(checked(rows)[FOCAL_INDEX]['outcome'])

    def test_log_sign_scale_and_deterministic_complete_scenarios(self):
        for name, rows, as_of in scenarios():
            if name.startswith('log_sign/'):
                with localcontext() as context:
                    context.prec = 100
                    expected = Decimal(10000)*(Decimal(name.split('/')[-1])/Decimal(100)).ln()
                self.assertEqual(checked(rows)[FOCAL_INDEX]['outcome'], expected)
        first, second = list(scenarios()), list(scenarios())
        self.assertEqual(first, second)
        self.assertEqual(len({name for name, _, _ in first}), len(first))
        self.assertTrue(all(len(checked(rows, as_of)) == 30 for name, rows, as_of in first))

    def test_absent_null_invalid_sources_are_distinct_and_inputs_immutable(self):
        rows = synthetic(); before = deepcopy(rows)
        checked(rows)
        self.assertEqual(rows, before)
        for value in ('-1', 'NaN', 'Infinity', True, 2):
            rows = synthetic()
            sample(rows, FOCAL_INDEX-1, 'ETHUSDT', 'quote_volume')['value'] = value
            case = checked(rows)[FOCAL_INDEX]
            self.assertIsNone(case['condition'])
            self.assertIn('invalid_value', case['reason_categories'])

    def test_duplicate_outside_or_malformed_availability_is_not_normalized(self):
        for kind in ('duplicate', 'before', 'after', 'availability'):
            rows = synthetic()
            if kind == 'duplicate': rows.append(deepcopy(rows[0]))
            elif kind == 'before': rows[0]['time'] -= STEP
            elif kind == 'after': rows[-1]['time'] += STEP
            else: next(iter(rows[0]['features'].values()))['available_at'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError): checked(rows)


if __name__ == '__main__': unittest.main()
