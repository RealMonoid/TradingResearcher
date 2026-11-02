"""Independent D099 potential identities, not outcome/dependence qualification.

Expected coordinates/counts are fixed before the implementation. No market data,
outcome loader, calibration, numerical world, or production registry is used.
Adjacent raw-input overlap below is a counterexample to treating event identity
as independence; it is not a substitute dependence model or admission judgment.
"""
from copy import deepcopy
import hashlib
import json
import unittest

from trading_researcher.codec import Invalid
from trading_researcher import outcome_reservations as owner


START = 1577836800  # 2020-01-01T00:00:00Z, an invented engineering grid.
EVENT_BYTES = (
    b'{"decision_time":1577836800,"grid_seconds":900,"instrument":"BTCUSDT",'
    b'"market_domain":"binance-spot","outcome_anchor":1577837700,'
    b'"schema":"potential-outcome-event/1"}'
)


def universe(start='2020-01-01T00:00:00Z', end='2020-01-01T00:45:00Z',
             instruments=None):
    return {'start': start, 'end': end,
            'instruments': ['BTCUSDT'] if instruments is None else instruments}


def span(start, end, horizon=1, instrument='BTCUSDT'):
    return {'instrument': instrument, 'decision_start': start,
            'decision_end': end, 'horizon_bars': horizon}


def expected_grid(ranges, boundaries, events, excluded):
    return {'schema': 'potential-outcome-grid/1', 'profile': 'outcome-reservation/1.0',
            'market_domain': 'binance-spot', 'grid_seconds': 900,
            'ranges': ranges, 'boundary_ranges': boundaries,
            'event_count': events, 'boundary_count': excluded}


class OutcomeReservationIdentityIndependentTests(unittest.TestCase):
    def test_event_hash_uses_exact_fixed_coordinates_without_provenance_aliases(self):
        literal = {'schema': 'potential-outcome-event/1', 'market_domain': 'binance-spot',
                   'grid_seconds': 900, 'instrument': 'BTCUSDT',
                   'decision_time': 1577836800, 'outcome_anchor': 1577837700}
        encoded = json.dumps(literal, sort_keys=True, ensure_ascii=False,
                             separators=(',', ':')).encode('utf-8')
        self.assertEqual(EVENT_BYTES, encoded)
        expected = hashlib.sha256(EVENT_BYTES).hexdigest()
        self.assertEqual(expected, owner.event_identity('BTCUSDT', START, START + 900))
        # Provenance belongs in its separate binding, not this identity API.
        for label in ('snapshot', 'revision', 'program', 'claim', 'partition'):
            with self.subTest(label=label), self.assertRaises(TypeError):
                owner.event_identity('BTCUSDT', START, START + 900, **{label: 'another-alias'})

    def test_instrument_decision_and_anchor_each_distinguish_events(self):
        identities = [
            owner.event_identity('BTCUSDT', START, START + 900),
            owner.event_identity('ETHUSDT', START, START + 900),
            owner.event_identity('BTCUSDT', START + 900, START + 1800),
            owner.event_identity('BTCUSDT', START, START + 1800),
            owner.event_identity('BTCUSDT', START + 900, START + 2700),
        ]
        self.assertEqual(5, len(set(identities)))
        # The same completion price is not the same decision/anchor pair.
        self.assertNotEqual(identities[2], identities[3])

    def test_event_coordinates_are_exact_nonnegative_aligned_integer_seconds(self):
        invalid = [
            ('BTCUSDT', True, 900), ('BTCUSDT', 0, True),
            ('BTCUSDT', 0.0, 900), ('BTCUSDT', '0', 900),
            ('BTCUSDT', -900, 0), ('BTCUSDT', 1, 900),
            ('BTCUSDT', 0, 901), ('BTCUSDT', 900, 900),
            ('BTCUSDT', 1800, 900), ('btcusdt', 0, 900),
            ('BTC/USDT', 0, 900), ('UNKNOWN', 0, 900),
            (None, 0, 900),
        ]
        for arguments in invalid:
            with self.subTest(arguments=arguments), self.assertRaises(Invalid):
                owner.event_identity(*arguments)
        self.assertEqual(64, len(owner.event_identity('BTCUSDT', 0, 900)))

    def test_half_open_grid_retains_exact_anchor_boundary_positions(self):
        value = universe()
        retained = deepcopy(value)
        self.assertEqual(
            expected_grid([span(START, START + 1800)],
                          [span(START + 1800, START + 2700)], 2, 1),
            owner.potential_grid(value, 1))
        self.assertEqual(
            expected_grid([span(START, START + 900, 2)],
                          [span(START + 900, START + 2700, 2)], 1, 2),
            owner.potential_grid(value, 2))
        self.assertEqual(
            expected_grid([], [span(START, START + 2700, 3)], 0, 3),
            owner.potential_grid(value, 3))
        self.assertEqual(
            expected_grid([], [span(START, START + 2700, 4)], 0, 3),
            owner.potential_grid(value, 4))
        self.assertEqual(retained, value, 'Metadata input must remain unchanged')

    def test_grid_requires_utc_aligned_nonempty_bounded_scope_and_positive_horizon(self):
        for horizon in (True, False, 0, -1, 1.0, '1'):
            with self.subTest(horizon=horizon), self.assertRaises(Invalid):
                owner.potential_grid(universe(), horizon)
        invalid = [
            universe(start='2020-01-01T00:00:00+00:00'),
            universe(start='2020-01-01T00:00:01Z'),
            universe(end='2020-01-01T00:45:01Z'),
            universe(start='2020-02-30T00:00:00Z'),
            universe(start='1969-12-31T23:45:00Z'),
            universe(end='2020-01-01T00:00:00Z'),
            universe(end='2019-12-31T23:45:00Z'),
            universe(instruments=[]), universe(instruments=['BTCUSDT', 'BTCUSDT']),
            universe(instruments=['BTCUSDT', 'UNKNOWN']),
            universe(instruments='BTCUSDT'),
        ]
        for value in invalid:
            with self.subTest(universe=value), self.assertRaises(Invalid):
                owner.potential_grid(value, 1)

    def test_multiple_instruments_are_canonical_and_counted_separately(self):
        self.assertEqual(
            expected_grid(
                [span(START, START + 1800), span(START, START + 1800, instrument='ETHUSDT')],
                [span(START + 1800, START + 2700),
                 span(START + 1800, START + 2700, instrument='ETHUSDT')], 4, 2),
            owner.potential_grid(universe(instruments=['ETHUSDT', 'BTCUSDT']), 1))

    def test_family_union_is_order_independent_and_retains_source_boundaries(self):
        first = owner.potential_grid(universe(), 1)
        second = owner.potential_grid(
            universe(start='2020-01-01T00:15:00Z', end='2020-01-01T01:00:00Z'), 1)
        expected = expected_grid([span(START, START + 2700)],
                                 [span(START + 1800, START + 3600)], 3, 2)
        self.assertEqual(expected, owner.merge_grids([first, second]))
        self.assertEqual(expected, owner.merge_grids([second, first, first]))
        self.assertTrue(owner.overlapping_events(first, second))
        # First's excluded 00:30 decision is a valid potential event in second.
        # Retaining source exclusions must not subtract it from the union.
        self.assertEqual(3, expected['event_count'])
        self.assertEqual(first, owner.merge_grids([first, first]))

    def test_adjacent_returns_and_shared_anchor_are_distinct_but_not_independence(self):
        first = owner.potential_grid(universe(end='2020-01-01T00:30:00Z'), 1)
        adjacent = owner.potential_grid(
            universe(start='2020-01-01T00:15:00Z', end='2020-01-01T00:45:00Z'), 1)
        same_anchor = owner.potential_grid(universe(), 2)
        self.assertFalse(owner.overlapping_events(first, adjacent))
        self.assertFalse(owner.overlapping_events(same_anchor, adjacent))
        self.assertFalse(owner.overlapping_events(first, same_anchor))
        # Independently fixed one-bar return operands include the final price.
        first_raw_positions = {1577836800, 1577837700}
        adjacent_raw_positions = {1577837700, 1577838600}
        self.assertEqual({1577837700}, first_raw_positions & adjacent_raw_positions)
        self.assertNotEqual(owner.event_identity('BTCUSDT', 1577836800, 1577837700),
                            owner.event_identity('BTCUSDT', 1577837700, 1577838600))
        merged = owner.merge_grids([first, adjacent])
        self.assertEqual(2, merged['event_count'])
        self.assertNotIn('independent', merged)
        self.assertNotIn('scientific_readiness', merged)

    def test_same_events_intersect_despite_grid_partitioning_and_instrument_separation(self):
        full = owner.potential_grid(universe(end='2020-01-01T01:00:00Z'), 1)
        tail = owner.potential_grid(
            universe(start='2020-01-01T00:30:00Z', end='2020-01-01T01:00:00Z'), 1)
        ether = owner.potential_grid(
            universe(end='2020-01-01T01:00:00Z', instruments=['ETHUSDT']), 1)
        self.assertTrue(owner.overlapping_events(full, tail))
        self.assertTrue(owner.overlapping_events(tail, full))
        self.assertFalse(owner.overlapping_events(full, ether))
        self.assertEqual(full, owner.merge_grids([full, tail]))

    def test_membership_helpers_reject_corrupt_or_unknown_grid_claims(self):
        valid = expected_grid([span(START, START + 1800)],
                              [span(START + 1800, START + 2700)], 2, 1)
        mutations = [
            {'schema': 'potential-outcome-grid/999'},
            {'profile': 'outcome-reservation/999'},
            {'market_domain': 'another-spot-market'},
            {'grid_seconds': True}, {'event_count': 3}, {'boundary_count': 0},
            {'ranges': [span(START + 1, START + 1800)]},
            {'ranges': [span(START, START + 1800), span(START, START + 1800)]},
            {'ranges': [span(START, START + 1800, instrument='UNKNOWN')]},
        ]
        for change in mutations:
            corrupted = {**deepcopy(valid), **change}
            with self.subTest(change=change):
                with self.assertRaises(Invalid):
                    owner.merge_grids([corrupted])
                with self.assertRaises(Invalid):
                    owner.overlapping_events(valid, corrupted)
        for legacy in ({}, {'outcome_record_ids': ['old-unmapped-record']}):
            with self.subTest(legacy=legacy), self.assertRaises(Invalid):
                owner.merge_grids([legacy])

    def test_4096_and_leap_year_grids_remain_compact_without_event_artifact_expansion(self):
        fixed = [
            (universe(end='2020-02-12T16:15:00Z'), 4096, 1581523200, 1581524100),
            (universe(end='2021-01-01T00:00:00Z'), 35135, 1609458300, 1609459200),
        ]
        for value, count, decision_end, universe_end in fixed:
            with self.subTest(end=value['end']):
                result = owner.potential_grid(value, 1)
                self.assertEqual(expected_grid([span(START, decision_end)],
                    [span(decision_end, universe_end)], count, 1), result)
                self.assertLess(len(json.dumps(result, sort_keys=True)), 1024)
                self.assertNotIn('event_ids', result)
                self.assertNotIn('outcome_record_ids', result)


if __name__ == '__main__':
    unittest.main()
