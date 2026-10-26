"""Independent fixed arithmetic, selection, and accounting counterexamples.

The hand oracles were sent before reading the implementation. These tests
exercise a development study; they are not estimator or market calibration.
"""
from copy import deepcopy
from fractions import Fraction as F
from math import comb
import unittest

from trading_researcher.codec import Invalid
from trading_researcher.information_study import (
    budget_state, make_manifest, outer_interval, summarize,
)


def rational(value):
    value = F(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def number(value):
    return F(int(value['numerator']), int(value['denominator']))


def assigned(direction='positive'):
    return {'input_binding': 'b' * 64, 'base_length': 2, 'primary_count': 1,
            'delta': rational(F(1, 20)), 'direction': direction, 'horizon_bars': 1,
            'available_time_rows': 16, 'instruments': 1}


def profile():
    return {
        'specifications': [{'schema': 'binary-population-spec/1',
                            'mask_mean_block': 2, 'persistence': rational(0),
                            'common_share': rational(0),
                            'rationale': 'Fixed independent review assumption.'}],
        'targets': [8, 12, 16], 'worlds_per_cell': 5, 'seed': 13,
        'mc_noncoverage': rational(F(1, 100)),
        'outer_noncoverage': rational(F(1, 20)),
        'budget': {'max_compute_ms': 1000, 'attempt_compute_ms': 400,
                   'max_storage_bytes': 1000, 'attempt_storage_bytes': 300,
                   'max_attempts': 3},
        'cost_estimate': {'source_ref': 'independent-arithmetic-fixture-not-a-benchmark',
                          'world_time_rows': 8, 'observed_compute_ms': 1,
                          'observed_storage_bytes': 1,
                          'qualification': 'Synthetic unit-test input; no runtime fit claim.'}}


def records(manifest, detections):
    result = []
    for world in manifest['worlds']:
        effect = number(world['effect'])
        target = world['time_rows']
        amount = detections.get((target, world['spec_index'], effect), 0)
        decision = ('SUPPORTED_INITIAL' if world['replicate'] < amount
                    else 'TESTED_NEGATIVE' if effect == 0
                    else 'TESTED_INCONCLUSIVE')
        result.append({'world_id': world['id'], 'state': 'VERIFIED',
                       'decision': decision, 'scope_count': 6,
                       'condition_count': 3, 'covered': True})
    return result


def reservation(manifest, attempt, world=0):
    return {'attempt_id': attempt, 'world_id': manifest['worlds'][world]['id'],
            'compute_ms': 400, 'storage_bytes': 300}


def settlement(attempt, compute, storage, known=True):
    return {'attempt_id': attempt, 'compute_ms': compute,
            'storage_bytes': storage, 'usage_known': known}


class InformationStudyAdversarialTests(unittest.TestCase):
    def test_closed_form_cp_roots_have_fixed_outward_grid_endpoints(self):
        # Independent n<=2 roots: alpha/2, 1-alpha/2, sqrt(alpha/2),
        # 1-sqrt(alpha/2), 1-sqrt(1-alpha/2), sqrt(1-alpha/2).
        expected = {
            (0, 1): (F(0), F(125, 128)),
            (1, 1): (F(3, 128), F(1)),
            (0, 2): (F(0), F(27, 32)),
            (1, 2): (F(3, 256), F(253, 256)),
            (2, 2): (F(5, 32), F(1)),
        }
        for (k, n), bounds in expected.items():
            with self.subTest(k=k, n=n):
                result = outer_interval(k, n, rational(F(1, 20)), bits=8)
                self.assertEqual(tuple(number(result[x]) for x in ('lower', 'upper')), bounds)
                self.assertEqual(number(result['point']), F(k, n))
                self.assertTrue(result['pointwise_only'])
        exact = outer_interval(0, 1, rational(F(1, 2)), bits=8)
        self.assertEqual([number(x) for x in exact['upper_root_bracket']], [F(3, 4)] * 2)
        # Fixed 40-bit oracle derived with integer square bounds before source read.
        precise = outer_interval(1, 2, rational(F(1, 20)))
        self.assertEqual(number(precise['lower']), F(13830885511, 1099511627776))
        self.assertEqual(number(precise['upper']), F(1085680742265, 1099511627776))

    def test_small_binomial_exhaustion_has_at_least_declared_pointwise_coverage(self):
        for n in range(1, 9):
            bounds = [outer_interval(k, n, rational(F(1, 20)), bits=8) for k in range(n + 1)]
            for numerator in range(17):
                p = F(numerator, 16)
                covered = sum((F(comb(n, k)) * p**k * (1-p)**(n-k)
                               for k, value in enumerate(bounds)
                               if number(value['lower']) <= p <= number(value['upper'])), F(0))
                self.assertGreaterEqual(covered, F(19, 20), (n, p, covered))
            for k, value in enumerate(bounds):
                reflected = bounds[n-k]
                self.assertEqual(number(value['lower']), 1-number(reflected['upper']))
                for key in ('lower_root_bracket', 'upper_root_bracket'):
                    low, high = map(number, value[key])
                    self.assertLessEqual(high-low, F(1, 256))
        changed = outer_interval(1, 2, rational(F(1, 20)), bits=8)
        changed['lower']['numerator'] = '999'
        self.assertEqual(number(outer_interval(1, 2, rational(F(1, 20)), bits=8)['lower']), F(3, 256))

    def test_contract_one_sided_threshold_counts_are_not_point_power_counts(self):
        # A two-sided 90% interval has the separate one-sided 95% endpoints.
        # This checks arithmetic only; these are not completed calibration trials.
        upper17 = outer_interval(17, 256, rational(F(1, 10)))
        upper18 = outer_interval(18, 256, rational(F(1, 10)))
        lower191 = outer_interval(191, 256, rational(F(1, 10)))
        lower192 = outer_interval(192, 256, rational(F(1, 10)))
        self.assertLessEqual(number(upper17['upper']), F(1, 10))
        self.assertGreater(number(upper18['upper']), F(1, 10))
        self.assertLess(number(lower191['lower']), F(7, 10))
        self.assertGreaterEqual(number(lower192['lower']), F(7, 10))
        self.assertLess(F(204, 256), F(4, 5))
        self.assertGreaterEqual(F(205, 256), F(4, 5))

    def test_complete_nonmonotone_grid_selects_smallest_tested_target_only(self):
        manifest = make_manifest(assigned(), profile())
        outcomes = records(manifest, {(8, 0, F(1, 10)): 4,
                                      (12, 0, F(1, 10)): 3,
                                      (16, 0, F(1, 10)): 5})
        before = deepcopy([manifest, outcomes])
        partial = summarize(manifest, outcomes[:-1])
        self.assertFalse(partial['complete'])
        self.assertIsNone(partial['candidate_time_rows'])
        summary = summarize(manifest, outcomes)
        self.assertTrue(summary['complete'])
        self.assertEqual(summary['candidate_time_rows'], 8)
        self.assertIsNone(summary['n_min'])
        self.assertFalse(summary['scientific_readiness'])
        self.assertFalse(summary['classification_permitted'])
        self.assertEqual([manifest, outcomes], before)

    def test_nondirectional_selection_requires_every_sign_and_stress(self):
        config = profile()
        second = deepcopy(config['specifications'][0])
        second['common_share'] = rational(F(1, 2))
        config['specifications'].append(second)
        manifest = make_manifest(assigned('nondirectional'), config)
        counts = {}
        for target, positive, negative in ((8, 4, 3), (12, 4, 4), (16, 5, 5)):
            for spec in range(2):
                counts[target, spec, F(1, 10)] = positive
                counts[target, spec, F(-1, 10)] = negative
        outcomes = records(manifest, counts)
        self.assertEqual(summarize(manifest, outcomes)['candidate_time_rows'], 12)
        counts[12, 1, F(-1, 10)] = 3
        self.assertEqual(summarize(manifest, records(manifest, counts))['candidate_time_rows'], 16)
        counts[16, 0, F(1, 10)] = 3
        self.assertIsNone(summarize(manifest, records(manifest, counts))['candidate_time_rows'])

    def test_information_gap_stays_in_denominator_but_technical_failure_blocks_selection(self):
        manifest = make_manifest(assigned(), profile())
        outcomes = records(manifest, {(8, 0, F(1, 10)): 4})
        world = next(x for x in manifest['worlds'] if x['time_rows'] == 8 and x['scenario'] == 2 and x['replicate'] == 4)
        index = next(i for i, value in enumerate(outcomes) if value['world_id'] == world['id'])
        outcomes[index].update(state='INFORMATION_GAP', decision=None,
                               covered=None, scope_count=0, condition_count=0)
        summary = summarize(manifest, outcomes)
        self.assertTrue(summary['complete'])
        self.assertEqual(summary['candidate_time_rows'], 8)
        cell = next(x for x in summary['cells'] if x['time_rows'] == 8 and x['scenario'] == 2)
        self.assertEqual((cell['planned'], cell['detections'], cell['interval_undefined']), (5, 4, 1))
        self.assertEqual(number(cell['power']['point']), F(4, 5))
        for state in ('TECHNICAL_FAILURE', 'MODEL_GAP'):
            failed = deepcopy(outcomes)
            failed[index]['state'] = state
            with self.subTest(state=state):
                summary = summarize(manifest, failed)
                self.assertFalse(summary['complete'])
                self.assertIsNone(summary['candidate_time_rows'])

    def test_missing_duplicate_unplanned_and_contradictory_results_are_not_hidden(self):
        manifest = make_manifest(assigned(), profile())
        outcomes = records(manifest, {})
        self.assertFalse(summarize(manifest, [])['complete'])
        self.assertEqual(summarize(manifest, [])['recorded_worlds'], 0)
        with self.assertRaises(Invalid):
            summarize(manifest, [outcomes[0], outcomes[0]])
        changes = [
            {'world_id': 'c' * 64}, {'state': 'UNKNOWN'},
            {'state': 'INFORMATION_GAP'}, {'decision': None}, {'covered': None},
            {'scope_count': None}, {'condition_count': None}, {'scope_count': True},
            {'condition_count': 0}, {'scope_count': 0, 'condition_count': 0},
            {'condition_count': 7}, {'scope_count': 8},
        ]
        for change in changes:
            with self.subTest(change=change), self.assertRaises(Invalid):
                summarize(manifest, [{**outcomes[0], **change}])

    def test_inventory_is_detached_and_every_population_bootstrap_seed_is_distinct(self):
        source, config = assigned('negative'), profile()
        before = deepcopy([source, config])
        manifest = make_manifest(source, config)
        self.assertEqual([source, config], before)
        self.assertEqual(manifest, make_manifest(source, config))
        self.assertEqual([number(x) for x in manifest['effects']], [0, F(-1, 20), F(-1, 10)])
        self.assertEqual(len(manifest['worlds']), 45)
        self.assertEqual(len({x['id'] for x in manifest['worlds']}), 45)
        seeds = [world[key] for world in manifest['worlds'] for key in ('population_seed', 'bootstrap_seed')]
        self.assertEqual(len(set(seeds)), 90)
        self.assertTrue(all(type(value) is int and 0 <= value < 2**256 for value in seeds))
        manifest['profile']['targets'][0] = 9
        self.assertEqual([source, config], before)
        with self.assertRaises(Invalid):
            summarize(manifest, [])
        original = make_manifest(source, config)
        for change in ('population_seed', 'effect', 'id'):
            altered = deepcopy(original)
            altered['worlds'][0][change] = 0
            with self.subTest(change=change), self.assertRaises(Invalid):
                summarize(altered, [])

    def test_manifest_rejects_unassigned_effects_noninteger_fields_and_resource_expansion(self):
        for key, value in [('targets', [8, 8]), ('targets', [16, 8]), ('targets', [1]),
                           ('targets', [17]), ('targets', [True]), ('worlds_per_cell', True),
                           ('worlds_per_cell', 257), ('seed', True), ('seed', -1), ('seed', 2**256),
                           ('outer_noncoverage', rational(0)), ('outer_noncoverage', rational(1))]:
            with self.subTest(key=key, value=value), self.assertRaises(Invalid):
                make_manifest(assigned(), {**profile(), key: value})
        for key, value in [('delta', rational(F(1, 10))), ('direction', 'either'),
                           ('horizon_bars', True), ('primary_count', True),
                           ('instruments', 17), ('input_binding', 'wrong')]:
            with self.subTest(key=key, value=value), self.assertRaises(Invalid):
                make_manifest({**assigned(), key: value}, profile())
        for key in profile()['budget']:
            changed = profile()
            changed['budget'][key] = True
            with self.subTest(key=key), self.assertRaises(Invalid):
                make_manifest(assigned(), changed)
        changed = profile()
        changed['budget']['max_compute_ms'] = 3600001
        with self.assertRaises(Invalid):
            make_manifest(assigned(), changed)
        changed = profile()
        changed['worlds_per_cell'] = 256
        with self.assertRaises(Invalid):
            make_manifest(assigned('nondirectional'), changed)

    def test_outer_interval_rejects_invalid_types_counts_and_numeric_envelopes(self):
        for k, n, bits in [(True, 1, 8), (0, True, 8), (0, 1, True),
                           (-1, 1, 8), (2, 1, 8), (0, 0, 8),
                           (0, 257, 8), (0, 1, 7), (0, 1, 65)]:
            with self.subTest(k=k, n=n, bits=bits), self.assertRaises(Invalid):
                outer_interval(k, n, rational(F(1, 20)), bits=bits)
        for probability in (0, 1, -1, F(1, 1000001)):
            with self.subTest(probability=probability), self.assertRaises(Invalid):
                outer_interval(0, 1, rational(probability))

    def test_fixed_accounting_charges_unknown_use_and_all_retries_without_reset(self):
        manifest = make_manifest(assigned(), profile())
        r1, r2, r3 = [reservation(manifest, value) for value in ('a1', 'a2', 'a3')]
        pending = budget_state(manifest, [r1], [])
        self.assertEqual((pending['charged_compute_ms'], pending['charged_storage_bytes']), (400, 300))
        self.assertEqual(pending['outstanding_attempts'], ['a1'])
        self.assertFalse(pending['next_reservation_fits'])
        s1 = settlement('a1', 125, 90)
        known = budget_state(manifest, [r1], [s1])
        self.assertEqual((known['charged_compute_ms'], known['charged_storage_bytes']), (125, 90))
        s2 = settlement('a2', 0, 0, False)
        uncertain = budget_state(manifest, [r1, r2], [s1, s2])
        self.assertEqual((uncertain['charged_compute_ms'], uncertain['charged_storage_bytes']), (525, 390))
        s3 = settlement('a3', 100, 50)
        before = deepcopy([manifest, [r1, r2, r3], [s1, s2, s3]])
        final = budget_state(manifest, [r1, r2, r3], [s1, s2, s3])
        self.assertEqual((final['charged_compute_ms'], final['charged_storage_bytes']), (625, 440))
        self.assertEqual(final['attempts_per_world'][r1['world_id']], 3)
        self.assertEqual([manifest, [r1, r2, r3], [s1, s2, s3]], before)
        with self.assertRaises(Invalid):
            budget_state(manifest, [r1, r2, r3, reservation(manifest, 'a4')], [s1, s2, s3])

    def test_overrun_is_never_truncated_to_a_cap_or_refunded(self):
        manifest = make_manifest(assigned(), profile())
        r1 = reservation(manifest, 'a1')
        for known in (False, True):
            state = budget_state(manifest, [r1], [settlement('a1', 450, 350, known)])
            self.assertEqual((state['charged_compute_ms'], state['charged_storage_bytes']), (450, 350))
            self.assertTrue(state['overrun'])
            self.assertFalse(state['next_reservation_fits'])
        rs = [reservation(manifest, 'a' + str(i), world=i) for i in range(3)]
        # The replay helper must expose an impossible aggregate history; admission
        # order/fencing are additionally enforced by the owned transaction.
        state = budget_state(manifest, rs, [])
        self.assertEqual(state['charged_compute_ms'], 1200)
        self.assertTrue(state['overrun'])
        self.assertFalse(state['next_reservation_fits'])

    def test_accounting_rejects_duplicate_unplanned_unreserved_and_boolean_history(self):
        manifest = make_manifest(assigned(), profile())
        r1, s1 = reservation(manifest, 'a1'), settlement('a1', 20, 10)
        bad = [([r1, r1], []), ([], [s1]), ([r1], [s1, s1]),
               ([{**r1, 'world_id': 'd' * 64}], []),
               ([{**r1, 'compute_ms': 399}], []),
               ([{**r1, 'storage_bytes': True}], []),
               ([r1], [{**s1, 'compute_ms': True}]),
               ([r1], [{**s1, 'storage_bytes': -1}]),
               ([r1], [{**s1, 'usage_known': 1}])]
        for reserves, settles in bad:
            with self.subTest(reservations=reserves, settlements=settles), self.assertRaises(Invalid):
                budget_state(manifest, reserves, settles)

    def test_malformed_json_identity_and_enum_values_raise_controlled_validation(self):
        manifest = make_manifest(assigned(), profile())
        outcome = records(manifest, {})[0]
        for key in ('world_id', 'state', 'decision'):
            with self.subTest(record_key=key), self.assertRaises(Invalid):
                summarize(manifest, [{**outcome, key: []}])
        r1, s1 = reservation(manifest, 'a1'), settlement('a1', 20, 10)
        with self.assertRaises(Invalid):
            budget_state(manifest, [{**r1, 'world_id': []}], [])
        with self.assertRaises(Invalid):
            budget_state(manifest, [r1], [{**s1, 'attempt_id': []}])


if __name__ == '__main__':
    unittest.main()
