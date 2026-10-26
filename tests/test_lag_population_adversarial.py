"""Independent exact finite-state oracles for the lag-linked population solver.

State index uses bit i for coordinate i. The common channel is selected
independently for each coordinate, so pairwise common-U covariance is multiplied
by share**2, not share. These finite algebra checks establish neither market
adequacy nor a completed calibration. They do not import production helpers to
derive the expected stationary distributions.
"""
from copy import deepcopy
from fractions import Fraction
import importlib
import itertools
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid


def solve(transitions, share):
    return importlib.import_module('trading_researcher.lag_population').stationary_joint(transitions, share)


def read(value):
    if type(value) is not dict or set(value) != {'numerator', 'denominator'}:
        raise AssertionError('Expected an explicit exact rational object')
    if type(value['numerator']) is not str or type(value['denominator']) is not str:
        raise AssertionError('Rational components must be strings')
    result = Fraction(int(value['numerator']), int(value['denominator']))
    if str(result.numerator) != value['numerator'] or str(result.denominator) != value['denominator']:
        raise AssertionError('Rational output is not reduced and canonical')
    return result


def marginal(transition):
    p0, p1 = map(Fraction, transition)
    return p0 / (1 - p1 + p0)


class LagPopulationAdversarialTests(unittest.TestCase):
    def assert_stationary(self, result, transitions):
        n = len(transitions)
        size = 1 << n
        self.assertEqual(result['schema'], 'binary-joint-stationary/1')
        self.assertEqual(result['coordinate_count'], n)
        self.assertEqual(len(result['matrix']), size)
        matrix = [[read(value) for value in row] for row in result['matrix']]
        probabilities = [read(value) for value in result['probabilities']]
        self.assertEqual(len(probabilities), size)
        self.assertEqual(sum(probabilities), 1)
        self.assertTrue(all(value >= 0 for value in probabilities))
        for index, row in enumerate(matrix):
            self.assertEqual(len(row), size)
            self.assertEqual(sum(row), 1)
            self.assertTrue(all(value >= 0 for value in row))
            for coordinate, transition in enumerate(transitions):
                expected = transition[(index >> coordinate) & 1]
                self.assertEqual(sum(value for target, value in enumerate(row)
                                     if (target >> coordinate) & 1), expected)
        for target in range(size):
            self.assertEqual(sum(probabilities[source] * matrix[source][target]
                                 for source in range(size)), probabilities[target])
        for coordinate, transition in enumerate(transitions):
            self.assertEqual(sum(value for state, value in enumerate(probabilities)
                                 if (state >> coordinate) & 1), marginal(transition))
        lattice = result['lattice_size']
        self.assertIs(type(lattice), str)
        self.assertEqual(str(int(lattice)), lattice)
        self.assertGreater(int(lattice), 0)
        counts = result['counts']
        self.assertEqual(len(counts), size)
        self.assertTrue(all(type(value) is str and str(int(value)) == value and int(value) >= 0
                            for value in counts))
        self.assertEqual(sum(map(int, counts)), int(lattice))
        self.assertEqual([Fraction(int(value), int(lattice)) for value in counts], probabilities)
        return matrix, probabilities

    def test_single_coordinate_positive_and_negative_effect_exact_marginal(self):
        for transition, expected in [((Fraction(2, 5), Fraction(3, 5)), Fraction(1, 2)),
                                     ((Fraction(7, 15), Fraction(3, 10)), Fraction(2, 5))]:
            for share in (0, Fraction(1, 3), 1):
                with self.subTest(transition=transition, share=share):
                    matrix, probabilities = self.assert_stationary(solve([transition], share), [transition])
                    self.assertEqual(matrix, [[1-transition[0], transition[0]],
                                              [1-transition[1], transition[1]]])
                    self.assertEqual(probabilities, [1-expected, expected])

    def test_full_common_channel_fixed_mixed_truth_matrix_and_stationary_oracle(self):
        transitions = [(Fraction(1, 2), Fraction(1, 2)), (Fraction(2, 5), Fraction(3, 5))]
        matrix, probabilities = self.assert_stationary(solve(transitions, 1), transitions)
        low = [Fraction(1, 2), Fraction(1, 10), Fraction(0), Fraction(2, 5)]
        high = [Fraction(2, 5), Fraction(0), Fraction(1, 10), Fraction(1, 2)]
        self.assertEqual(matrix, [low, low, high, high])
        self.assertEqual(probabilities, [Fraction(9, 20), Fraction(1, 20),
                                         Fraction(1, 20), Fraction(9, 20)])
        self.assertNotEqual(probabilities, [Fraction(1, 2), Fraction(0), Fraction(0), Fraction(1, 2)])

    def test_partial_common_channel_uses_independent_coordinate_choices(self):
        transitions = [(Fraction(1, 2), Fraction(1, 2)), (Fraction(2, 5), Fraction(3, 5))]
        matrix, probabilities = self.assert_stationary(solve(transitions, Fraction(1, 2)), transitions)
        low = [Fraction(7, 20), Fraction(1, 4), Fraction(3, 20), Fraction(1, 4)]
        high = [Fraction(1, 4), Fraction(3, 20), Fraction(1, 4), Fraction(7, 20)]
        self.assertEqual(matrix, [low, low, high, high])
        self.assertEqual(probabilities, [Fraction(3, 10), Fraction(1, 5),
                                         Fraction(1, 5), Fraction(3, 10)])

    def test_zero_common_share_product_law_with_distinct_marginals(self):
        transitions = [(Fraction(1, 6), Fraction(2, 3)),
                       (Fraction(3, 5), Fraction(4, 5)),
                       (Fraction(7, 15), Fraction(3, 10))]
        matrix, probabilities = self.assert_stationary(solve(transitions, 0), transitions)
        qs = [Fraction(1, 3), Fraction(3, 4), Fraction(2, 5)]
        expected = []
        for state in range(8):
            value = Fraction(1)
            for coordinate, q in enumerate(qs):
                value *= q if (state >> coordinate) & 1 else 1-q
            expected.append(value)
        self.assertEqual(probabilities, expected)
        for source, row in enumerate(matrix):
            for target, observed in enumerate(row):
                expected_transition = Fraction(1)
                for coordinate, transition in enumerate(transitions):
                    p = transition[(source >> coordinate) & 1]
                    expected_transition *= p if (target >> coordinate) & 1 else 1-p
                self.assertEqual(observed, expected_transition)

    def test_perfect_common_iid_thresholds_preserve_asymmetric_coordinate_order(self):
        transitions = [(Fraction(1, 4), Fraction(1, 4)), (Fraction(3, 4), Fraction(3, 4))]
        matrix, probabilities = self.assert_stationary(solve(transitions, 1), transitions)
        expected = [Fraction(1, 4), Fraction(0), Fraction(1, 2), Fraction(1, 4)]
        self.assertEqual(probabilities, expected)
        self.assertEqual(matrix, [expected]*4)

    def test_four_coordinates_allow_zero_probability_joint_states(self):
        transitions = [(Fraction(1, 3), Fraction(1, 3))]*4
        matrix, probabilities = self.assert_stationary(solve(transitions, 1), transitions)
        expected = [Fraction(2, 3)] + [Fraction(0)]*14 + [Fraction(1, 3)]
        self.assertEqual(probabilities, expected)
        self.assertEqual(matrix, [expected]*16)

    def test_permutation_changes_only_explicit_coordinate_order(self):
        transitions = [(Fraction(1, 6), Fraction(2, 3)), (Fraction(3, 5), Fraction(4, 5))]
        first, pfirst = self.assert_stationary(solve(transitions, Fraction(2, 3)), transitions)
        second, psecond = self.assert_stationary(solve(list(reversed(transitions)), Fraction(2, 3)),
                                                list(reversed(transitions)))
        swap = [0, 2, 1, 3]
        self.assertEqual(psecond, [pfirst[index] for index in swap])
        self.assertEqual(second, [[first[source][target] for target in swap] for source in swap])

    def test_all_rows_exact_residual_and_marginals_with_negative_and_positive_dependence(self):
        transitions = [(Fraction(7, 15), Fraction(3, 10)),
                       (Fraction(1, 6), Fraction(2, 3)),
                       (Fraction(3, 5), Fraction(4, 5))]
        for share in (0, Fraction(2, 3), 1):
            with self.subTest(share=share):
                self.assert_stationary(solve(transitions, share), transitions)

    def test_input_is_not_mutated_and_results_are_reproducible_detached_values(self):
        transitions = [[Fraction(2, 5), Fraction(3, 5)], [Fraction(1, 4), Fraction(1, 4)]]
        before = deepcopy(transitions)
        first = solve(transitions, Fraction(1, 3))
        second = solve(transitions, Fraction(1, 3))
        self.assertEqual(first, second)
        self.assertEqual(transitions, before)
        first['probabilities'][0]['numerator'] = '999'
        self.assertNotEqual(first, second)
        transitions[0][0] = Fraction(1, 5)
        self.assertEqual(second, solve(before, Fraction(1, 3)))

    def test_small_high_denominator_inputs_retain_exact_integer_sampling_inventory(self):
        transitions = [(Fraction(1, 257), Fraction(2, 257)),
                       (Fraction(7, 259), Fraction(8, 259))]
        self.assert_stationary(solve(transitions, Fraction(1, 3)), transitions)

    def test_dimension_and_outer_container_bounds(self):
        pair = (Fraction(2, 5), Fraction(3, 5))
        for transitions in ([], [pair]*5, None, {}, (pair,)):
            with self.subTest(transitions=transitions), self.assertRaises(Invalid):
                solve(transitions, Fraction(1, 2))

    def test_transition_shapes_and_unrequested_fields_are_not_coerced(self):
        for item in ([], [Fraction(1, 2)], [Fraction(1, 2)]*3,
                     {'p0': Fraction(2, 5), 'p1': Fraction(3, 5)}, '1/2', None):
            with self.subTest(item=item), self.assertRaises(Invalid):
                solve([item], Fraction(1, 2))

    def test_probability_types_and_values_are_strict(self):
        for invalid in (False, True, 0.5, '1/2', None, Fraction(-1, 10), Fraction(11, 10)):
            for coordinate in (0, 1):
                pair = [Fraction(2, 5), Fraction(3, 5)]
                pair[coordinate] = invalid
                with self.subTest(invalid=invalid, coordinate=coordinate), self.assertRaises(Invalid):
                    solve([pair], Fraction(1, 2))

    def test_common_share_type_and_range_are_strict(self):
        transitions = [(Fraction(2, 5), Fraction(3, 5))]
        for share in (False, True, 0.5, '1/2', None, Fraction(-1, 10), Fraction(11, 10)):
            with self.subTest(share=share), self.assertRaises(Invalid):
                solve(transitions, share)

    def test_transition_boundary_excluded_as_capability_without_clipping(self):
        for p0, p1 in itertools.product((Fraction(0), Fraction(1, 2), Fraction(1)), repeat=2):
            if p0 == p1 == Fraction(1, 2):
                continue
            with self.subTest(p0=p0, p1=p1), self.assertRaises(Invalid):
                solve([(p0, p1)], Fraction(1, 2))

    def test_numeric_resource_envelope_rejects_before_large_solver_work(self):
        too_large = Fraction(1, 1 << 4096)
        for transitions, share in [([(too_large, Fraction(1, 2))], Fraction(1, 2)),
                                   ([(Fraction(1, 2), Fraction(1, 2))], too_large)]:
            with self.subTest(share=share), self.assertRaises(Invalid):
                solve(transitions, share)


def independent_model(source, *, share=Fraction(0), effects=(Fraction(0), Fraction(1, 10))):
    from trading_researcher.information_diagnostics import diagnose
    from trading_researcher.population_models import build_model
    module = importlib.import_module('trading_researcher.lag_population')
    encoded = [{'numerator': str(value.numerator), 'denominator': str(value.denominator)} for value in effects]
    return build_model(source, diagnose(source, [1]),
        module.specification(1, share, 'Independent fixed algebra/mask oracle, not a market fit.'), encoded)


class LagPopulationProcessAdversarialTests(unittest.TestCase):
    def test_pooled_knownness_uses_eligible_rows_and_preserves_other_group_meaning(self):
        from test_source_process_scope_adversarial import fixture
        source = fixture(instruments=('A', 'B'))
        source['cases'][0]['condition'] = None
        bound = independent_model(source)
        self.assertEqual(bound['status'], 'MODEL_SPECIFIED')
        population = bound['population']
        self.assertEqual(read(population['q']), Fraction(1, 2))
        self.assertEqual(read(population['source_condition_fraction']), Fraction(1, 2))
        self.assertEqual(read(population['known_condition_fraction']), Fraction(13, 14))
        self.assertEqual(read(population['w']), Fraction(13, 28))
        rates = bound['scenarios'][1]
        self.assertEqual(read(rates['p_true']), Fraction(3, 5))
        self.assertEqual(read(rates['transition_p_zero']), Fraction(2, 5))
        self.assertEqual(read(rates['p_other']), Fraction(31, 75))
        w = read(population['w'])
        self.assertEqual(w*read(rates['p_true'])+(1-w)*read(rates['p_other']), Fraction(1, 2))
        self.assertEqual(read(rates['p_true'])-read(population['q']), Fraction(1, 10))

    def test_latent_phase_advances_through_wholly_missing_rows_with_generated_conditions(self):
        from test_source_process_scope_adversarial import fixture
        from trading_researcher.population_models import generate_world
        module = importlib.import_module('trading_researcher.lag_population')
        source = fixture(missing_rows=((7, 'A'),))
        bound = independent_model(source)
        self.assertEqual(bound['status'], 'MODEL_SPECIFIED')
        before = deepcopy((source, bound))
        mask_positions = iter([0, 0, 3, 3, 0, 0, 0, 0, 0])
        latent_bits = iter([1, 0, 0, 1, 1, 0, 0, 1])
        initial_bits = iter([0, 1])
        calls = {}

        def streams(seed, key):
            name = repr(key)
            if name in calls:
                raise AssertionError('Stream recreated: ' + name)
            calls[name] = 0

            class Stream:
                def randrange(self, limit):
                    calls[name] += 1
                    if key == 'stationary-phase-states':
                        return 0 if next(initial_bits) == 0 else limit-1
                    if key == 'joint-mask':
                        return 0 if limit == 1 else next(mask_positions)
                    if type(key) is list and key[0] == 'individual-innovation':
                        return 0 if next(latent_bits) else limit-1
                    if key == 'common-innovation' or type(key) is list and key[0] == 'common-choice':
                        return 0
                    raise AssertionError('Unexpected random stream')

            return Stream()

        with patch.object(module, '_rng', side_effect=streams):
            world = generate_world(source, bound, 0, 8, 2026102609)
        cases = world['report']['cases']
        self.assertEqual(world['initialization']['initial_states'], [0, 1])
        self.assertEqual([case['condition'] for case in cases],
                         [False, True, None, None, False, True, True, False])
        self.assertEqual([case['simulation_mask']['source_time_index'] for case in cases],
                         [0, 0, 3, 3, 0, 0, 0, 0])
        self.assertEqual([case['status'] for case in cases],
                         ['ELIGIBLE', 'ELIGIBLE', 'DATA_GAP', 'DATA_GAP',
                          'ELIGIBLE', 'ELIGIBLE', 'ELIGIBLE', 'PARTITION_BOUNDARY'])
        self.assertEqual([None if case['outcome'] is None else read(case['outcome']) for case in cases],
                         [1, 0, None, None, 1, 0, 0, None])
        self.assertEqual(calls[repr(['individual-innovation', 'response', 'A'])], 8)
        self.assertEqual(calls[repr('common-innovation')], 8)
        self.assertEqual((source, bound), before)
        self.assertFalse(world['report']['simulation']['source_condition_values_resampled'])

    def test_modified_bound_transition_is_rejected_before_any_random_draw(self):
        from test_source_process_scope_adversarial import fixture
        from trading_researcher.population_models import generate_world
        module = importlib.import_module('trading_researcher.lag_population')
        source = fixture()
        bound = independent_model(source)
        bound['scenarios'][0]['transition_p_zero'] = {'numerator': '1', 'denominator': '2'}
        with patch.object(module, '_rng') as rng, self.assertRaises(Invalid):
            generate_world(source, bound, 0, 8, 7)
        rng.assert_not_called()


if __name__ == '__main__':
    unittest.main()
