"""Independent finite-state oracles for the existing second-order stress law.

All rows and raw inputs below are invented fixed numbers. The exact Q1 rate is
an algebraic fixture parameter, never a read of market or protected data. These
checks establish bounded implementation conformance, not population adequacy,
calibration, information sufficiency or scientific admission.
"""
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction as F
import math
import unittest

from trading_researcher.codec import Invalid, digest
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.outcomes import materialize_reference
from trading_researcher.population_models import build_model, generate_world
from trading_researcher.family_models import generate_family
from trading_researcher.second_order_population import specification, stationary_joint, validate_specification


Q = F(1462, 2877)
EFFECTS = (F(0), F(1, 20), F(1, 10))
BETAS = (F(-1, 2), F(0), F(1, 2))
SHARES = (F(0), F(1, 2), F(1))


def rational(value):
    value = F(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def fraction(value):
    """Decode the fixed transport without using the production rational reader."""
    if type(value) is not dict or set(value) != {'numerator', 'denominator'}:
        raise AssertionError('Unexpected exact-rational transport')
    if any(type(item) is not str for item in value.values()):
        raise AssertionError('Rational components must be decimal strings')
    parsed = F(int(value['numerator']), int(value['denominator']))
    if rational(parsed) != value:
        raise AssertionError('Rational output is not normalized')
    return parsed


def transition_rates(q, effect, beta):
    alpha = (1 - beta) * effect / (1 - q)
    return [q + alpha * (F(history >> 1) - q) + beta * (F(history & 1) - q)
            for history in range(4)]


def pair_law(q, effect):
    return [(1 - q) ** 2 + q * effect, q * (1 - q - effect),
            q * (1 - q - effect), q * (q + effect)]


def coupled_innovation(p, share):
    """Two independent channel choices share U only when both choose it.

    P(11) = share^2 min(p0,p1) + (1-share^2) p0 p1.
    Subtracting this intersection from the two marginals determines every other
    cell. This is a separate closed-form oracle, not the implementation's
    integration over uniform-threshold intervals.
    """
    if len(p) == 1:
        return [1 - p[0], p[0]]
    both = share ** 2 * min(p) + (1 - share ** 2) * p[0] * p[1]
    return [1 - p[0] - p[1] + both, p[0] - both, p[1] - both, both]


def transition_matrix(rates, share):
    width = len(rates)
    matrix = []
    for state in range(4 ** width):
        history = [((state >> coordinate) & 1) +
                   2 * ((state >> (coordinate + width)) & 1)
                   for coordinate in range(width)]
        innovations = coupled_innovation([rates[i][history[i]] for i in range(width)], share)
        row = [F(0)] * (4 ** width)
        for new_bits, mass in enumerate(innovations):
            next_state = (state >> width) + (new_bits << width)
            row[next_state] = mass
        matrix.append(row)
    return matrix


def instant(index):
    return datetime.fromtimestamp(index * 900, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def invented_source(count=12, successes=6):
    """A permutation of fixed Boolean values, with two unknown conditions.

    Full-period marginal counts are fixed analytically. The supplied raw up flag
    is not a market measurement. The existing materializer provides report
    transport and temporal bookkeeping; expected model probabilities come only
    from the equations above.
    """
    multiplier, offset = (37, 5000) if count == 8631 else (5, 7)
    assert math.gcd(multiplier, count) == 1
    catalog = {'up@1': {'type': 'boolean', 'unit': None}}

    def program(expression):
        return {'schema': 'research-ast/1', 'catalog_hash': digest(catalog), 'expression': expression}

    feature = {'op': 'feature', 'ref': 'up@1'}
    request = {'schema': 'reference-case-request/1', 'candidate_ref': 'independent-invented-second-order',
               'data_snapshot_ref': 'invented-raw-Boolean-period',
               'scope_program': program({'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}),
               'condition_program': program({'op': 'lag', 'arg': feature, 'bars': 1}),
               'outcome_program': program(feature), 'outcome_scale': 'binary_probability',
               'horizon_bars': 1, 'universe': {'start': instant(1), 'end': instant(count + 2),
                                               'instruments': ['SYNTHETIC']},
               'as_of': instant(count + 3), 'max_steps': 1_000_000}
    rows = [{'time': index * 900, 'instrument': 'SYNTHETIC',
             'features': {} if index < 2 else {'up@1': {
                 'value': (index * multiplier + offset) % count < successes,
                 'available_at': index * 900}}} for index in range(count + 3)]
    return materialize_reference(request, catalog, rows)


class SecondOrderIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.small = invented_source()
        cls.small_diagnostics = diagnose(cls.small, [1, 2, 4])
        cls.q1_numbers = invented_source(8631, 4386)
        cls.q1_diagnostics = diagnose(cls.q1_numbers, [1, 2, 4])

    def model(self, beta=F(1, 2), share=F(1, 2), *, source=None, effects=EFFECTS):
        source = self.small if source is None else source
        diagnostics = self.small_diagnostics if source is self.small else diagnose(source, [1, 2, 4])
        return build_model(source, diagnostics,
                           specification(8, beta, share, 'Fixed independent engineering stress; no market fit.'),
                           [rational(value) for value in effects])

    def assert_stationary(self, result, rates, share, effects, q=Q):
        width = len(rates)
        actual = [[fraction(value) for value in row] for row in result['matrix']]
        expected = transition_matrix(rates, share)
        self.assertEqual(actual, expected)
        pi = [fraction(value) for value in result['probabilities']]
        self.assertEqual(len(pi), 4 ** width)
        self.assertEqual(sum(pi), 1)
        self.assertTrue(all(value >= 0 for value in pi))
        self.assertTrue(all(sum(row) == 1 for row in actual))
        for target in range(len(pi)):
            self.assertEqual(sum(pi[state] * expected[state][target] for state in range(len(pi))), pi[target])
        for coordinate, effect in enumerate(effects):
            marginal = [sum(pi[state] for state in range(len(pi))
                            if ((state >> coordinate) & 1) +
                            2 * ((state >> (coordinate + width)) & 1) == history)
                        for history in range(4)]
            self.assertEqual(marginal, pair_law(q, effect))
            self.assertEqual(marginal[1] + marginal[3], q)
            self.assertEqual(marginal[2] + marginal[3], q)
            self.assertEqual(marginal[3] / q - q, effect)
        lattice = int(result['lattice_size'])
        counts = [int(value) for value in result['counts']]
        self.assertEqual(sum(counts), lattice)
        self.assertEqual([F(value, lattice) for value in counts], pi)
        self.assertEqual(result['coordinate_count'], width)
        self.assertEqual(result['history_order'], 2)
        return pi

    def test_single_coordinate_q1_rate_has_exact_pair_truth_for_all_fixed_cells(self):
        for beta in BETAS:
            for effect in EFFECTS:
                rates = transition_rates(Q, effect, beta)
                self.assertTrue(all(0 < value < 1 for value in rates))
                for share in SHARES:
                    with self.subTest(beta=beta, effect=effect, share=share):
                        result = stationary_joint([rates], share)
                        self.assertEqual(self.assert_stationary(result, [rates], share, [effect]),
                                         pair_law(Q, effect))

    def test_mixed_joint_truth_and_residual_use_independent_coupling_oracle(self):
        for beta in BETAS:
            for effects in ((F(0), F(1, 10)), (F(1, 20), F(1, 10))):
                rates = [transition_rates(Q, effect, beta) for effect in effects]
                for share in SHARES:
                    with self.subTest(beta=beta, effects=effects, share=share):
                        result = stationary_joint(rates, share)
                        pi = self.assert_stationary(result, rates, share, effects)
                        if share == 0:
                            pairs = [pair_law(Q, effect) for effect in effects]
                            independent = [pairs[0][(state & 1) + 2 * ((state >> 2) & 1)] *
                                           pairs[1][((state >> 1) & 1) + 2 * ((state >> 3) & 1)]
                                           for state in range(16)]
                            self.assertEqual(pi, independent)

    def test_common_channel_spot_entries_and_full_iid_history_law(self):
        # Coordinates have unequal marginals, making bit reversal observable.
        rates = [[F(1, 4)] * 4, [F(3, 4)] * 4]
        fixed = {F(0): [F(3, 16), F(1, 16), F(9, 16), F(3, 16)],
                 F(1, 2): [F(13, 64), F(3, 64), F(35, 64), F(13, 64)],
                 F(1): [F(1, 4), F(0), F(1, 2), F(1, 4)]}
        for share, innovation in fixed.items():
            with self.subTest(share=share):
                result = stationary_joint(rates, share)
                matrix = [[fraction(value) for value in row] for row in result['matrix']]
                for prior in range(16):
                    self.assertEqual([matrix[prior][(prior >> 2) + (new << 2)] for new in range(4)], innovation)
                pi = [fraction(value) for value in result['probabilities']]
                self.assertEqual(pi, [innovation[state & 3] * innovation[state >> 2] for state in range(16)])

    def test_fully_shared_identical_laws_retain_transient_zero_mass(self):
        rates = transition_rates(Q, F(1, 10), F(1, 2))
        result = stationary_joint([rates, rates], F(1))
        pi = self.assert_stationary(result, [rates, rates], F(1), [F(1, 10)] * 2)
        expected = [F(0)] * 16
        for old in (0, 1):
            for recent in (0, 1):
                expected[(3 * old) + (12 * recent)] = pair_law(Q, F(1, 10))[old + 2 * recent]
        self.assertEqual(pi, expected)

    def test_model_binds_q1_number_fixture_without_reshaping_source_truth(self):
        totals = self.q1_diagnostics['totals']
        self.assertEqual(totals['scope']['count'], 8631)
        self.assertEqual(totals['scope']['successes'], 4386)
        self.assertEqual(totals['true']['count'], 4386)
        self.assertEqual(totals['unknown']['count'], 2)
        self.assertEqual(totals['unknown']['successes'], 0)
        before = deepcopy(self.q1_numbers)
        for beta in BETAS:
            with self.subTest(beta=beta):
                bound = build_model(self.q1_numbers, self.q1_diagnostics,
                                    specification(8, beta, F(1, 2), 'Fixed invented-number fixture.'),
                                    [rational(value) for value in EFFECTS])
                self.assertEqual(bound['status'], 'MODEL_SPECIFIED', bound['gaps'])
                self.assertEqual(fraction(bound['population']['q']), Q)
                self.assertEqual(fraction(bound['population']['w']), Q * F(8629, 8631))
                self.assertEqual(fraction(bound['population']['source_condition_fraction']), Q)
                self.assertEqual(bound['lag_bars'], 2)
                for row, effect in zip(bound['scenarios'], EFFECTS):
                    self.assertEqual(fraction(row['alpha']), (1 - beta) * effect / (1 - Q))
                    self.assertEqual([fraction(value) for value in row['history_transitions']],
                                     transition_rates(Q, effect, beta))
                    self.assertEqual([fraction(value) for value in row['lag_pair_probabilities']], pair_law(Q, effect))
                    self.assertTrue(row['feasible'])
                    self.assertTrue(row['within_transition_capability'])
                self.assertFalse(bound['scientific_readiness'])
                self.assertFalse(bound['classification_permitted'])
                self.assertIsNone(bound['n_min'])
        self.assertEqual(self.q1_numbers, before)

    def test_generation_mixed_vectors_preserves_observed_lag_and_shared_masks(self):
        components = [{'id': 'null', 'scenario': 0}, {'id': 'alternative', 'scenario': 2}]
        for share in SHARES:
            with self.subTest(share=share):
                bound = self.model(beta=F(-1, 2), share=share)
                original = digest(bound)
                result = generate_family(self.small, bound, components, 96, 2026110201)
                self.assertEqual(result, generate_family(self.small, bound, list(reversed(components)), 96, 2026110201))
                reports = [item['report'] for item in result['components']]
                self.assertEqual([[row['simulation_mask']['source_time_index'] for row in report['cases']]
                                  for report in reports][0],
                                 [row['simulation_mask']['source_time_index'] for row in reports[1]['cases']])
                for report in reports:
                    rows = {row['decision_time']: row for row in report['cases']}
                    comparisons = 0
                    for row in report['cases']:
                        earlier = rows.get(row['decision_time'] - 1800)
                        if earlier and earlier['outcome'] is not None and row['condition'] is not None:
                            self.assertEqual(F(int(row['condition'])), fraction(earlier['outcome']))
                            comparisons += 1
                    self.assertGreater(comparisons, 0)
                    self.assertTrue(report['simulation']['terminal_horizon_censor'])
                    self.assertFalse(report['simulation']['raw_AST_executed'])
                self.assertEqual(result['initialization']['history_order'], 2)
                self.assertEqual(result['initialization']['independent_phase_count'], 2)
                self.assertEqual(len(result['initialization']['law']['matrix']), 16)
                self.assertEqual(result['outer_world_count'], 1)
                self.assertFalse(result['scientific_readiness'])
                self.assertFalse(result['classification_permitted'])
                self.assertIsNone(result['n_min'])
                self.assertEqual(digest(bound), original)

    def test_boundary_and_infeasible_laws_remain_gaps_without_clipping(self):
        source = invented_source(12, 4)
        boundary = self.model(beta=F(-1, 2), source=source, effects=(F(0),))
        self.assertEqual(fraction(boundary['population']['q']), F(1, 3))
        self.assertEqual(boundary['status'], 'MODEL_OR_INFORMATION_GAP')
        self.assertIn('second_order_boundary_outside_current_capability', boundary['gaps'])
        self.assertIn(F(0), [fraction(value) for value in boundary['scenarios'][0]['history_transitions']])
        self.assertTrue(boundary['scenarios'][0]['feasible'])
        self.assertFalse(boundary['scenarios'][0]['within_transition_capability'])
        with self.assertRaises(Invalid):
            generate_world(source, boundary, 0, 24, 1)
        infeasible = self.model(beta=F(-9, 10))
        self.assertEqual(infeasible['status'], 'MODEL_OR_INFORMATION_GAP')
        self.assertEqual(len(infeasible['scenarios']), 3)
        self.assertIn('infeasible_second_order_transition', infeasible['gaps'])
        rates = [fraction(value) for value in infeasible['scenarios'][2]['history_transitions']]
        self.assertTrue(any(value < 0 or value > 1 for value in rates))
        with self.assertRaises(Invalid):
            generate_world(self.small, infeasible, 2, 24, 1)

    def test_solver_rejects_invalid_dimensions_boundaries_and_exact_types(self):
        row = [F(1, 2)] * 4
        invalid = [([], F(0)), ([row] * 3, F(0)), ((row,), F(0)),
                   ([[F(1, 2)] * 3], F(0)), ([[F(1, 2)] * 5], F(0)),
                   ([[F(0), *row[1:]]], F(0)), ([[F(1), *row[1:]]], F(0)),
                   ([row], F(-1, 2)), ([row], F(3, 2))]
        for value in (True, 0.5, '1/2', Decimal('0.5'), None):
            invalid.extend([([[value, *row[1:]]], F(0)), ([row], value)])
        for rates, share in invalid:
            with self.subTest(rates=rates, share=share), self.assertRaises(Invalid):
                stationary_joint(rates, share)

    def test_exact_numeric_envelope_rejects_inputs_and_intermediate_growth(self):
        with self.assertRaises(Invalid):
            stationary_joint([[F(1, 1 << 4096)] * 4], F(0))
        # This probability is admitted by the per-input bit limit, but its
        # stationary two-history mass p^2 needs more than 4096 denominator bits.
        tiny = F(1, 1 << 2200)
        self.assertLessEqual(tiny.denominator.bit_length(), 4096)
        with self.assertRaises(Invalid):
            stationary_joint([[tiny] * 4], F(0))

    def test_specification_boundaries_exact_types_and_detachment(self):
        valid = specification(1_000_000, F(-1, 2), F(1), 'Fixed limit fixture.')
        parsed = validate_specification(valid)
        parsed['rationale'] = 'Changed detached result'
        self.assertEqual(valid['rationale'], 'Fixed limit fixture.')
        for beta in (F(-1), F(1), F(1, 1_000_001), True, 0.5, Decimal('0.5')):
            with self.subTest(beta=beta), self.assertRaises(Invalid):
                specification(8, beta, F(1, 2), 'Invalid fixed beta.')
        for share in (F(-1, 2), F(3, 2), F(1, 1_000_001), True, 0.5):
            with self.subTest(share=share), self.assertRaises(Invalid):
                specification(8, F(0), share, 'Invalid fixed share.')
        for size in (0, -1, True, 1_000_001):
            with self.subTest(size=size), self.assertRaises(Invalid):
                specification(size, F(0), F(0), 'Invalid fixed mask size.')
        for changes in ({'extra': True}, {'beta': {'numerator': '2', 'denominator': '4'}},
                        {'beta': {'numerator': True, 'denominator': '2'}}, {'rationale': ''}):
            with self.subTest(changes=changes), self.assertRaises(Invalid):
                validate_specification({**valid, **changes})

    def test_generation_rejects_capacity_size_and_claim_mismatch(self):
        bound = self.model()
        three = [{'id': str(index), 'scenario': index} for index in range(3)]
        with self.assertRaises(Invalid):
            generate_family(self.small, bound, three, 24, 1)
        for size in (1, 0, True, 50_001):
            with self.subTest(size=size), self.assertRaises(Invalid):
                generate_family(self.small, bound, [{'id': 'a', 'scenario': 0},
                                                    {'id': 'b', 'scenario': 2}], size, 1)
        for scenario in (True, -1, 3):
            with self.subTest(scenario=scenario), self.assertRaises(Invalid):
                generate_world(self.small, bound, scenario, 24, 1)
        altered = deepcopy(bound)
        altered['scenarios'][2]['history_transitions'][0] = rational(F(1, 2))
        with self.assertRaises(Invalid):
            generate_world(self.small, altered, 2, 24, 1)
        disagree = deepcopy(self.small)
        disagree['cases'][5]['condition'] = not disagree['cases'][5]['condition']
        mismatch = self.model(source=disagree)
        self.assertIn('observed_source_value_identity_mismatch', mismatch['gaps'])
        self.assertEqual(mismatch['status'], 'MODEL_OR_INFORMATION_GAP')


if __name__ == '__main__':
    unittest.main()
