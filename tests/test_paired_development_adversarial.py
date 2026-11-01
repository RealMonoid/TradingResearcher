"""Independent D094 expectations on invented rows, never a research candidate.

These pure tests exercise the declared fixed pair, original threshold rules,
source domains, paired population and time cutoffs. They supply no certificate,
provider call, market input, semantic review or scientific authority.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import unittest

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.expressions import ReferenceEngine
from trading_researcher.bounded_math import BoundedReferenceEngine, Enclosure
from trading_researcher.bounded_outcomes import bounded_contrast
from trading_researcher.outcomes import reference_contrast
from trading_researcher.paired_development import (
    PairedReferenceEngine, materialize_paired, paired_contrast,
)


PAIR = ['BTCUSDT', 'ETHUSDT']
START = 1672531200
STEP = 900


def definitions():
    result = []
    for symbol in PAIR:
        base = symbol.removesuffix('USDT')
        for name, column in (('open', 1), ('close', 4), ('quote_volume', 7), ('taker_quote_volume', 10)):
            price = name in ('open', 'close')
            result.append({'schema': 'raw-binance-feature-definition/1',
                'feature_ref': ref(symbol, name), 'instrument': symbol, 'source_field': name,
                'csv_column_index': column, 'type': 'real', 'unit': 'USDT/' + base if price else 'USDT',
                'source_scalar': 'positive_decimal' if price else 'nonnegative_decimal',
                'transformation': 'EXACT_DECIMAL_FIELD_PROJECTION',
                'time': {'grid_seconds': 900, 'row_anchor': 'EXPECTED_EXCLUSIVE_BAR_END',
                    'source_open_column': 0, 'source_close_column': 6,
                    'timestamp_unit_rule': 'milliseconds_before_2025_microseconds_from_2025'},
                'missingness': {'invalid_keyed_bar': 'NULL_ALL_SYMBOL_FIELDS', 'absent_bar': 'NO_ROW',
                    'other_instrument_fields': 'ABSENT'},
                'availability': {'basis': 'assumed', 'rule': 'row_time + delay_seconds',
                    'parameter': 'EXPLICIT_NONNEGATIVE_INTEGER_SECONDS_NO_DEFAULT', 'historical_publication_time': None},
                'fitted_state': None})
    return result


def ref(symbol, name):
    return symbol + '.' + name + '@binance-spot-15m-v1'


def feature(symbol, name):
    return {'op': 'feature_at', 'instrument': symbol, 'ref': ref(symbol, name)}


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': str(value)}


def boolean(value):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def lag(arg, bars):
    return {'op': 'lag', 'arg': arg, 'bars': bars}


def all_of(items):
    if len(items) == 1:
        return items[0]
    split = len(items) // 2
    return binary('and', all_of(items[:split]), all_of(items[split:]))


def guard(validity, predicate):
    return binary('or', binary('and', deepcopy(validity), predicate),
        binary('and', {'op': 'not', 'arg': deepcopy(validity)}, boolean(None)))


def original_condition():
    valid = []
    for symbol in PAIR:
        price_unit = 'USDT/' + symbol.removesuffix('USDT')
        valid.append(all_of([
            binary('gt', feature(symbol, 'open'), literal(0, price_unit)),
            binary('gt', feature(symbol, 'close'), literal(0, price_unit)),
            binary('gt', feature(symbol, 'quote_volume'), literal(0, 'USDT')),
            binary('ge', feature(symbol, 'taker_quote_volume'), literal(0, 'USDT')),
            binary('le', feature(symbol, 'taker_quote_volume'), feature(symbol, 'quote_volume'))]))
    validity = all_of([lag(all_of(deepcopy(valid)), 2), lag(all_of(deepcopy(valid)), 1)])
    def rate(symbol):
        return binary('sub', binary('div', feature(symbol, 'close'), feature(symbol, 'open')), literal(1))
    def flow(symbol):
        return binary('div', feature(symbol, 'taker_quote_volume'), feature(symbol, 'quote_volume'))
    shock = all_of([binary('le', rate(symbol), literal('-0.004')) for symbol in PAIR] +
                  [binary('le', flow(symbol), literal('0.40')) for symbol in PAIR])
    recovery = all_of([binary('ge', rate(PAIR[0]), literal('0.002')),
        binary('ge', flow(PAIR[0]), literal('0.55')),
        binary('le', rate(PAIR[1]), literal(0)), binary('le', flow(PAIR[1]), literal('0.45'))])
    return guard(validity, all_of([lag(shock, 2), lag(recovery, 1)]))


def spread(terminal_lag=1, initial_lag=5):
    def log_return(symbol):
        return {'op': 'ln', 'arg': binary('div', lag(feature(symbol, 'close'), terminal_lag),
                                        lag(feature(symbol, 'close'), initial_lag))}
    return binary('mul', literal(10000, 'basis_points'),
                  binary('sub', log_return('ETHUSDT'), log_return('BTCUSDT')))


def example(count=8, start=START):
    defs = definitions()
    catalog = {d['feature_ref']: {'type': d['type'], 'unit': d['unit']} for d in defs}
    rows = []
    for index in range(count):
        for symbol in PAIR:
            price = '100' if symbol == 'BTCUSDT' else '200'
            values = {'open': price, 'close': price, 'quote_volume': '100', 'taker_quote_volume': '50'}
            rows.append({'time': start + STEP * index, 'instrument': symbol, 'features': {
                ref(symbol, name): {'value': value, 'available_at': start + STEP * (index + 1)}
                for name, value in values.items()}})
    stamp = lambda instant: datetime.fromtimestamp(instant, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    request = {'schema': 'paired-reference-case-request/1', 'candidate_ref': 'synthetic-pair-only',
        'data_snapshot_ref': 'synthetic-never-market-data',
        'scope_program': program(boolean(True), catalog),
        'condition_program': program(original_condition(), catalog),
        'outcome_program': program(spread(), catalog), 'outcome_scale': 'quantity', 'horizon_bars': 5,
        'universe': {'start': stamp(start), 'end': stamp(start + count * STEP), 'pair': deepcopy(PAIR)},
        'as_of': stamp(start + count * STEP), 'max_steps': 10000000}
    return request, catalog, rows, defs


def program(expression, catalog):
    return {'schema': 'research-ast/3', 'catalog_hash': digest(catalog), 'expression': expression}


def sample(rows, index, symbol, name, start=START):
    return next(row for row in rows if row['time'] == start + index * STEP and row['instrument'] == symbol)['features'][ref(symbol, name)]


def boundary_rows():
    request, catalog, rows, defs = example()
    for index, symbol, values in ((0, 'BTCUSDT', ('100', '99.6', '100', '40')),
            (0, 'ETHUSDT', ('200', '199.2', '100', '40')),
            (1, 'BTCUSDT', ('100', '100.2', '100', '55')),
            (1, 'ETHUSDT', ('200', '200', '100', '45'))):
        for name, value in zip(('open', 'close', 'quote_volume', 'taker_quote_volume'), values):
            sample(rows, index, symbol, name)['value'] = value
    return request, catalog, rows, defs


def rational(value):
    return Fraction(int(value['numerator']), int(value['denominator']))


def bounds(value):
    if isinstance(value, Enclosure):
        return value.lower, value.upper
    return rational(value['lower']), rational(value['upper'])


class PairedDevelopmentAdversarialTests(unittest.TestCase):
    def engine(self, catalog, rows, defs, **kw):
        return PairedReferenceEngine(catalog, rows, defs, pair=deepcopy(PAIR), **kw)

    def condition(self, rows, catalog, defs):
        return self.engine(catalog, rows, defs).evaluate_at(program(original_condition(), catalog),
            START + 2 * STEP, START + 2 * STEP).value

    def assert_gap(self, action):
        with self.assertRaises(Invalid):
            action()

    def assert_encloses(self, value, expected):
        low, high = bounds(value)
        self.assertLessEqual(low, expected)
        self.assertLessEqual(expected, high)
        self.assertLessEqual(high - low, Fraction(1, 10**12))

    def test_explicit_selected_feature_and_dependency_closure_preserve_sources(self):
        _, catalog, rows, defs = example()
        before = canonical({'catalog': catalog, 'rows': rows, 'definitions': defs})
        events = []
        engine = self.engine(catalog, rows, defs)
        value = engine.evaluate_at(program(feature('ETHUSDT', 'close'), catalog), START, START + STEP, trace=events.append)
        self.assertEqual(value.value, Fraction(200))
        self.assertEqual(value.unit, 'USDT/ETH')
        self.assertTrue(events)
        self.assertTrue(all(e['instrument'] == 'ETHUSDT' and e['feature_ref'] == ref('ETHUSDT', 'close') for e in events))
        description = engine.describe(program(original_condition(), catalog))
        self.assertEqual(set(description['feature_refs']), set(catalog))
        self.assertEqual(before, canonical({'catalog': catalog, 'rows': rows, 'definitions': defs}))

    def test_ast_versions_unqualified_features_and_selector_forgery_fail_closed(self):
        _, catalog, rows, defs = example()
        engine = self.engine(catalog, rows, defs)
        correct = program(feature('ETHUSDT', 'close'), catalog)
        for schema in ('research-ast/1', 'research-ast/2', 'research-ast/4'):
            self.assert_gap(lambda: engine.evaluate_at({**correct, 'schema': schema}, START, START + STEP))
        for expression in ({'op': 'feature', 'ref': ref('ETHUSDT', 'close')},
                {**feature('ETHUSDT', 'close'), 'instrument': 'BTCUSDT'},
                {**feature('ETHUSDT', 'close'), 'instrument': 'SOLUSDT'},
                {**feature('ETHUSDT', 'close'), 'fallback': 'BTCUSDT'},
                {**feature('ETHUSDT', 'close'), 'instrument': ['ETHUSDT']}):
            with self.subTest(expression=expression):
                self.assert_gap(lambda: engine.evaluate_at(program(expression, catalog), START, START + STEP))
        for old in (ReferenceEngine(catalog, rows), BoundedReferenceEngine(catalog, rows)):
            self.assert_gap(lambda: old.evaluate(correct, 0))

    def test_pair_definitions_and_row_ownership_cannot_be_ambiguous(self):
        _, catalog, rows, defs = example()
        for pair in (['BTCUSDT'], ['BTCUSDT', 'BTCUSDT'], list(reversed(PAIR)), [*PAIR, 'SOLUSDT'], None):
            with self.subTest(pair=pair):
                self.assert_gap(lambda: PairedReferenceEngine(catalog, rows, defs, pair=pair))
        for changed in (defs[:-1], defs + [deepcopy(defs[0])], [{**defs[0], 'instrument': 'ETHUSDT'}, *defs[1:]],
                [{**defs[0], 'unit': 'USDT/ETH'}, *defs[1:]],
                [{**defs[0], 'source_scalar': 'nonnegative_decimal'}, *defs[1:]]):
            self.assert_gap(lambda: self.engine(catalog, rows, changed))
        changed = deepcopy(rows)
        changed[0]['features'][ref('ETHUSDT', 'close')] = {'value': '200', 'available_at': START + STEP}
        self.assert_gap(lambda: self.engine(catalog, changed, defs))

    def test_all_eight_inclusive_thresholds_and_their_false_sides(self):
        _, catalog, rows, defs = boundary_rows()
        self.assertIs(self.condition(rows, catalog, defs), True)
        false_sides = ((0, 'BTCUSDT', 'close', '99.6001'), (0, 'ETHUSDT', 'close', '199.2001'),
            (0, 'BTCUSDT', 'taker_quote_volume', '40.0001'), (0, 'ETHUSDT', 'taker_quote_volume', '40.0001'),
            (1, 'BTCUSDT', 'close', '100.1999'), (1, 'BTCUSDT', 'taker_quote_volume', '54.9999'),
            (1, 'ETHUSDT', 'close', '200.0001'), (1, 'ETHUSDT', 'taker_quote_volume', '45.0001'))
        for index, symbol, name, value in false_sides:
            changed = deepcopy(rows)
            sample(changed, index, symbol, name)['value'] = value
            with self.subTest(index=index, symbol=symbol, name=name):
                self.assertIs(self.condition(changed, catalog, defs), False)

    def test_each_required_condition_sample_is_unknown_even_with_another_false_clause(self):
        _, catalog, rows, defs = boundary_rows()
        for index in (0, 1):
            for symbol in PAIR:
                for name in ('open', 'close', 'quote_volume', 'taker_quote_volume'):
                    changed = deepcopy(rows)
                    sample(changed, 1, 'BTCUSDT', 'close')['value'] = '99'
                    sample(changed, index, symbol, name)['value'] = None
                    with self.subTest(index=index, symbol=symbol, name=name):
                        self.assertIsNone(self.condition(changed, catalog, defs))
        for absent in ({(START, 'BTCUSDT')}, {(START, 'BTCUSDT'), (START, 'ETHUSDT')}):
            changed = [r for r in rows if (r['time'], r['instrument']) not in absent]
            self.assertIsNone(self.condition(changed, catalog, defs))

    def test_source_domains_and_original_validity_are_separate_gates(self):
        _, catalog, rows, defs = boundary_rows()
        for index, symbol, name, value in ((0, 'ETHUSDT', 'quote_volume', '0'),
                (1, 'ETHUSDT', 'taker_quote_volume', '101')):
            changed = deepcopy(rows)
            sample(changed, index, symbol, name)['value'] = value
            self.assertIsNone(self.condition(changed, catalog, defs))
        for value in ('0', '-100', 'NaN', 'Infinity', 100.0):
            changed = deepcopy(rows)
            sample(changed, 2, 'ETHUSDT', 'close')['value'] = value
            sample(changed, 6, 'ETHUSDT', 'close')['value'] = value
            with self.subTest(value=value):
                self.assert_gap(lambda: self.engine(catalog, changed, defs, allow_log=True))

    def test_exact_outcome_units_sign_and_no_interval_decisions(self):
        _, catalog, rows, defs = example()
        anchor = START + 5 * STEP
        sample(rows, 4, 'ETHUSDT', 'close')['value'] = '400'
        engine = self.engine(catalog, rows, defs, allow_log=True)
        value = engine.evaluate_at(program(spread(), catalog), anchor, anchor)
        self.assertEqual(value.unit, 'basis_points')
        with localcontext() as ctx:
            ctx.prec = 100
            expected = Fraction(Decimal(2).ln()) * 10000
        self.assert_encloses(value.value, expected)
        reverse = binary('mul', literal(-1), spread())
        self.assert_encloses(engine.evaluate_at(program(reverse, catalog), anchor, anchor).value, -expected)
        sample(rows, 4, 'ETHUSDT', 'close')['value'] = '200'
        self.assert_encloses(self.engine(catalog, rows, defs, allow_log=True).evaluate_at(
            program(spread(), catalog), anchor, anchor).value, Fraction(0))
        self.assert_gap(lambda: self.engine(catalog, rows, defs).evaluate_at(program(spread(), catalog), anchor, anchor))
        self.assert_gap(lambda: engine.evaluate_at(program(binary('sub', feature('ETHUSDT', 'close'),
            feature('BTCUSDT', 'close')), catalog), START, START + STEP))
        self.assert_gap(lambda: engine.evaluate_at(program(binary('gt', spread(), literal(0, 'basis_points')), catalog), anchor, anchor))

    def test_complete_median_and_mean_use_only_required_selected_samples(self):
        _, catalog, rows, defs = example()
        for index, value in enumerate(('100', '300', '200')):
            sample(rows, index, 'ETHUSDT', 'close')['value'] = value
        rows = [r for r in rows if r['time'] != START + 3 * STEP]
        engine = self.engine(catalog, rows, defs)
        for operation in ('trailing_median', 'trailing_mean'):
            expression = {'op': operation, 'arg': lag(feature('ETHUSDT', 'close'), 1), 'bars': 3}
            self.assertEqual(engine.evaluate_at(program(expression, catalog), START + 3 * STEP, START + 3 * STEP).value, 200)
            missing = [r for r in rows if not (r['time'] == START + STEP and r['instrument'] == 'ETHUSDT')]
            self.assertIsNone(self.engine(catalog, missing, defs).evaluate_at(
                program(expression, catalog), START + 3 * STEP, START + 3 * STEP).value)

    def test_q1_grid_is_one_pair_per_timestamp_with_exact_synthetic_boundaries(self):
        request, catalog, rows, defs = example(8640)
        complete = all_of([binary('gt', lag(feature(symbol, 'close'), 2),
            literal(0, 'USDT/' + symbol.removesuffix('USDT'))) for symbol in PAIR])
        request['condition_program'] = program(guard(complete, boolean(True)), catalog)
        report = materialize_paired(request, catalog, rows, defs)
        self.assertEqual(report['schema'], 'paired-reference-cases/1')
        self.assertEqual(report['expected_case_count'], 8640)
        self.assertEqual(report['processed_case_count'], 8640)
        self.assertEqual([case['decision_time'] for case in report['cases']], [START + STEP * i for i in range(8640)])
        self.assertTrue(all(case['pair'] == PAIR and 'instrument' not in case for case in report['cases']))
        self.assertEqual([case['condition'] for case in report['cases'][:3]], [None, None, True])
        self.assertEqual(sum(case['status'] == 'ELIGIBLE' for case in report['cases']), 8635)
        self.assertEqual([case['status'] for case in report['cases'][-5:]], ['PARTITION_BOUNDARY'] * 5)
        self.assertFalse(report['scientific_readiness'])

    def test_member_publication_after_anchor_cannot_use_later_global_as_of(self):
        request, catalog, rows, defs = example()
        sample(rows, 4, 'ETHUSDT', 'close')['available_at'] = START + 5 * STEP + 1
        report = materialize_paired(request, catalog, rows, defs)
        case = report['cases'][0]
        self.assertEqual(case['status'], 'OUTCOME_PENDING')
        self.assertIsNone(case['outcome'])
        pending = [e for e in case['dependencies'] if e['reason'] == 'not_yet_available']
        self.assertTrue(any(e['instrument'] == 'ETHUSDT' and e['observation_time'] == START + 4 * STEP for e in pending))
        self.assertEqual(paired_contrast(report)['status'], 'INFORMATION_GAP')

    def test_unused_decision_and_anchor_containers_add_no_input_requirement(self):
        request, catalog, rows, defs = example()
        request['condition_program'] = program(boolean(True), catalog)
        request['outcome_program'] = program(spread(terminal_lag=1, initial_lag=2), catalog)
        request['horizon_bars'] = 3
        rows = [r for r in rows if r['time'] not in (START, START + 3 * STEP)]
        case = materialize_paired(request, catalog, rows, defs)['cases'][0]
        self.assertEqual(case['status'], 'ELIGIBLE')
        self.assertIs(case['scope'], True)
        self.assertIs(case['condition'], True)
        self.assert_encloses(case['outcome'], 0)
        self.assertEqual({e['observation_time'] for e in case['dependencies']}, {START + STEP, START + 2 * STEP})

    def test_observed_unknown_conditions_remain_in_whole_scope_denominator(self):
        request, catalog, rows, defs = boundary_rows()
        report = materialize_paired(request, catalog, rows, defs)
        contrast = paired_contrast(report)
        self.assertEqual(contrast['scope_count'], 3)
        self.assertEqual(contrast['condition_count'], 1)
        self.assertEqual(contrast['status'], 'DESCRIPTIVE_ONLY')
        with localcontext() as ctx:
            ctx.prec = 100
            expected = Fraction((Decimal(501) / Decimal(500)).ln()) * 10000 / 3
        self.assert_encloses(contrast['scope_mean'], expected)
        self.assert_encloses(contrast['condition_mean'], 0)
        self.assert_encloses(contrast['effect'], -expected)

    def test_diagnostics_keep_both_members_without_double_counting_or_literal_null_missing(self):
        request, catalog, rows, defs = boundary_rows()
        report = materialize_paired(request, catalog, rows, defs)
        self.assertNotIn('missing_value', report['cases'][2]['diagnostics']['reason_categories'])
        changed = [r for r in rows if r['time'] != START]
        report = materialize_paired(request, catalog, changed, defs)
        case = report['cases'][2]
        self.assertIn('absent_row', case['diagnostics']['reason_categories'])
        events = [e for e in case['diagnostics']['events'] if e['reason'] == 'missing_observation']
        self.assertEqual({e['instrument'] for e in events}, set(PAIR))
        self.assertTrue(all(e['pair'] == PAIR and e['feature_ref'] in catalog for e in events))
        expected = sum('absent_row' in c['diagnostics']['reason_categories'] for c in report['cases'])
        self.assertEqual(report['diagnostics']['reason_counts']['absent_row'], expected)
        self.assertEqual(report['diagnostics']['schema'], 'paired-case-diagnostics/1')

    def test_report_tampering_never_enters_a_scalar_or_paired_contrast(self):
        request, catalog, rows, defs = boundary_rows()
        report = materialize_paired(request, catalog, rows, defs)
        for old in (reference_contrast, bounded_contrast):
            self.assert_gap(lambda: old(report))
        mutators = [lambda r: r['cases'][0].update(pair=['BTCUSDT', 'BTCUSDT']),
            lambda r: r['cases'][0].update(instrument='BTCUSDT'),
            lambda r: r.update(expected_case_count=16),
            lambda r: r['cases'].append(deepcopy(r['cases'][0])),
            lambda r: r['cases'][0].update(outcome_anchor=START + STEP),
            lambda r: r['cases'][0].update(outcome={'schema': 'bounded-real/1',
                'lower': {'numerator': '2', 'denominator': '1'}, 'upper': {'numerator': '1', 'denominator': '1'}}),
            lambda r: r['cases'][0]['dependencies'][0].update(instrument='SOLUSDT'),
            lambda r: r['diagnostics']['reason_counts'].update(absent_row=-1),
            lambda r: r['state_counts'].update(SCOPE_FALSE=False)]
        for number, mutate in enumerate(mutators):
            changed = deepcopy(report)
            mutate(changed)
            with self.subTest(mutation=number):
                self.assert_gap(lambda: paired_contrast(changed))

    def test_complete_ast_dependency_inventory_cannot_omit_or_replace_selected_reads(self):
        request, catalog, rows, defs = boundary_rows()
        report = materialize_paired(request, catalog, rows, defs)
        missing_member = deepcopy(report)
        missing_member['cases'][0]['dependencies'] = [event for event in missing_member['cases'][0]['dependencies']
            if not (event['program'] == 'outcome_program' and event['instrument'] == 'BTCUSDT')]
        substituted = deepcopy(report)
        event = next(event for event in substituted['cases'][0]['dependencies']
                     if event['program'] == 'outcome_program' and event['instrument'] == 'BTCUSDT')
        event['feature_ref'] = ref('BTCUSDT', 'open')
        for changed in (missing_member, substituted):
            with self.subTest(kind='missing_member' if changed is missing_member else 'substituted_ref'):
                self.assert_gap(lambda: paired_contrast(changed))

    def test_neutral_unknown_and_boundary_counts_are_explicit(self):
        request, catalog, rows, defs = boundary_rows()
        report = materialize_paired(request, catalog, rows, defs)
        self.assertEqual(report['diagnostics']['reason_counts'].get('condition_unknown'), 2)
        self.assertEqual(report['diagnostics']['reason_counts'].get('boundary_censoring'), 5)
        self.assertIn('condition_unknown', report['cases'][0]['diagnostics']['reason_categories'])
        self.assertIn('boundary_censoring', report['cases'][-1]['diagnostics']['reason_categories'])
        self.assertNotIn('missing_value', report['cases'][2]['diagnostics']['reason_categories'])
        self.assertEqual(report['diagnostics']['condition_outcome_counts'], {
            'true': {'observed': 1, 'missing': 0},
            'false': {'observed': 0, 'missing': 5},
            'unknown': {'observed': 2, 'missing': 0}})

    def test_unhashable_case_or_feature_identity_fails_with_typed_gap(self):
        request, catalog, rows, defs = boundary_rows()
        report = materialize_paired(request, catalog, rows, defs)
        for field in ('status', 'feature_ref'):
            changed = deepcopy(report)
            if field == 'status':
                changed['cases'][0]['status'] = []
            else:
                changed['cases'][0]['dependencies'][0]['feature_ref'] = []
            with self.subTest(field=field):
                self.assert_gap(lambda: paired_contrast(changed))

    def test_outside_universe_duplicate_and_other_member_rows_fail_admission(self):
        request, catalog, rows, defs = example()
        before = canonical({'request': request, 'catalog': catalog, 'rows': rows, 'definitions': defs})
        for when in (START - STEP, START + 8 * STEP):
            extra = deepcopy(rows[0]); extra['time'] = when
            self.assert_gap(lambda: materialize_paired(request, catalog,
                sorted([*rows, extra], key=lambda r: (r['time'], r['instrument'])), defs))
        self.assert_gap(lambda: materialize_paired(request, catalog, [rows[0], *rows], defs))
        changed = deepcopy(rows); changed[0]['instrument'] = 'SOLUSDT'
        self.assert_gap(lambda: materialize_paired(request, catalog, changed, defs))
        self.assertEqual(before, canonical({'request': request, 'catalog': catalog, 'rows': rows, 'definitions': defs}))

    def test_total_step_stop_preserves_prefix_and_bounds_are_typed(self):
        request, catalog, rows, defs = example()
        report = materialize_paired({**request, 'max_steps': 1}, catalog, rows, defs)
        self.assertEqual(report['status'], 'RESOURCE_STOP')
        self.assertFalse(report['processing_complete'])
        self.assertLess(report['processed_case_count'], report['expected_case_count'])
        self.assertEqual(report['diagnostics']['status'], 'RESOURCE_STOP')
        self.assertEqual(paired_contrast(report)['status'], 'RESOURCE_STOP')
        engine = self.engine(catalog, rows, defs)
        self.assert_gap(lambda: engine.evaluate_at(program(boolean(True), catalog), START, START, remaining=[0]))
        expression = boolean(True)
        for _ in range(33):
            expression = {'op': 'not', 'arg': expression}
        self.assert_gap(lambda: engine.evaluate_at(program(expression, catalog), START, START))
        for changed in ({**request, 'max_steps': True}, {**request, 'horizon_bars': 0},
                {**request, 'schema': 'bounded-reference-case-request/1'}):
            self.assert_gap(lambda: materialize_paired(changed, catalog, rows, defs))


if __name__ == '__main__':
    unittest.main()
