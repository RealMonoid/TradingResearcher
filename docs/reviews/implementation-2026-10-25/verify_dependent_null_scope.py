"""Exact finite-state counterexamples for model scope; no runtime or market access."""
import hashlib
import itertools
import json
from fractions import Fraction
from pathlib import Path


def encoded(value):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def assess(q, rho):
    # Chronological state: (Y[t-3], Y[t-2], Y[t-1], Y[t]).
    # Four independent stationary chains, each advanced once every four timestamps.
    states = list(itertools.product((0, 1), repeat=4))
    a = q + (1 - q) * rho
    b = q * (1 - rho)
    assert 0 < q < 1 and -1 < rho < 1 and 0 < a < 1 and 0 < b < 1
    masses = [q ** sum(s) * (1 - q) ** (4 - sum(s)) for s in states]
    matrix = []
    for s in states:
        p = a if s[0] else b
        matrix.append([Fraction(0) if t[:3] != s[1:] else p if t[3] else 1 - p
                       for t in states])
    assert sum(masses) == 1 and all(sum(row) == 1 for row in matrix)
    assert all(sum(masses[i] * matrix[i][j] for i in range(16)) == masses[j]
               for j in range(16))

    def expect(values):
        return sum(p * v for p, v in zip(masses, values))

    def advance(values):
        return [sum(p * v for p, v in zip(row, values)) for row in matrix]

    condition = [Fraction(s[1]) for s in states]
    outcome = [Fraction(s[3]) for s in states]
    effect = expect([c * y for c, y in zip(condition, outcome)]) / expect(condition) - expect(outcome)
    assert expect(condition) == expect(outcome) == q and effect == 0
    # At the null, the contrast's population linearization score is (C-q)*(Y-q)/q.
    score = [(c - q) * (y - q) / q for c, y in zip(condition, outcome)]
    centered = [y - q for y in outcome]
    assert expect(score) == 0
    variance = expect([s * s for s in score])
    assert variance == (1 - q) ** 2
    assert advance(advance(score)) == [rho * s for s in score]
    assert expect([s * t for s, t in zip(score, advance(score))]) == 0
    assert advance(advance(advance(advance(centered)))) == [rho * y for y in centered]

    moments = []
    shifted_score, shifted_outcome = score, centered
    for lag in range(13):
        score_cov = expect([s * t for s, t in zip(score, shifted_score)])
        outcome_cov = expect([s * t for s, t in zip(centered, shifted_outcome)])
        expected_score = Fraction(0) if lag % 2 else variance * rho ** (lag // 2)
        expected_outcome = Fraction(0) if lag % 4 else q * (1 - q) * rho ** (lag // 4)
        assert score_cov == expected_score and outcome_cov == expected_outcome
        moments.append({'lag': lag, 'score_covariance': encoded(score_cov),
                        'outcome_covariance': encoded(outcome_cov)})
        shifted_score, shifted_outcome = advance(shifted_score), advance(shifted_outcome)
    multiplier = (1 + rho) / (1 - rho)
    return {'q': encoded(q), 'rho': encoded(rho), 'transition_from_one': encoded(a),
            'transition_from_zero': encoded(b), 'true_condition_minus_scope_effect': encoded(effect),
            'states': len(states), 'stationary_mass': [encoded(p) for p in masses],
            'score_variance': encoded(variance), 'score_lrv_multiplier_vs_iid': encoded(multiplier),
            'score_long_run_variance': encoded(variance * multiplier), 'moments': moments,
            'stationarity_residuals_exact_zero': True, 'score_two_step_eigen_identity': True}


def assess_proposed_extension(q, effect, beta):
    """Check a proposed second-order law; this does not add a production generator."""
    r = effect / (1 - q)
    alpha = (1 - beta) * r
    states = list(itertools.product((0, 1), repeat=4))
    pair = {(1, 1): q * (q + effect), (1, 0): q * (1 - q - effect),
            (0, 1): q * (1 - q - effect), (0, 0): (1 - q) ** 2 + q * effect}
    masses = [pair[s[0], s[2]] * pair[s[1], s[3]] for s in states]
    rates = [q + alpha * (s[2] - q) + beta * (s[0] - q) for s in states]
    assert all(0 < p < 1 for p in rates) and all(p > 0 for p in masses)
    matrix = [[Fraction(0) if t[:3] != s[1:] else p if t[3] else 1 - p
               for t in states] for s, p in zip(states, rates)]
    assert sum(masses) == 1 and all(sum(row) == 1 for row in matrix)
    assert all(sum(masses[i] * matrix[i][j] for i in range(16)) == masses[j]
               for j in range(16))
    c = sum(p * s[1] for s, p in zip(states, masses))
    y = sum(p * s[3] for s, p in zip(states, masses))
    cy = sum(p * s[1] * s[3] for s, p in zip(states, masses))
    assert c == y == q and cy / c - y == effect
    if beta == 0:
        assert all(p == (q + effect if s[2] else q - q * effect / (1 - q))
                   for s, p in zip(states, rates))
    return {'q': encoded(q), 'effect': encoded(effect), 'beta': encoded(beta),
            'alpha': encoded(alpha), 'minimum_transition': encoded(min(rates)),
            'maximum_transition': encoded(max(rates)),
            'stationarity_and_target_exact': True, 'production_implemented': False}


def check():
    cases = [assess(q, rho) for q in (Fraction(1, 2), Fraction(19, 47))
             for rho in (Fraction(-1, 2), Fraction(0), Fraction(1, 2))]
    extension = [assess_proposed_extension(q, effect, beta)
                 for q in (Fraction(1, 2), Fraction(19, 47))
                 for effect in (Fraction(0), Fraction(1, 20), Fraction(1, 10))
                 for beta in (Fraction(-1, 2), Fraction(0), Fraction(1, 2))]
    return {'schema': 'dependent-null-scope-counterexample/1', 'status': 'PASS',
            'cases': cases, 'exact_states_per_case': 16, 'checked_lags_per_case': 13,
            'proposed_affine_extension_cases': extension,
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'qualification': 'Project-derived population counterexamples, not a fitted market law, '
                             'simulation performance result, bootstrap miscoverage claim or admitted profile. '
                             'The variance multiplier applies to the linearization score, not an exact '
                             'finite-sample variance ratio for the random-denominator estimator.',
            'simulated_worlds': 0, 'provider_calls': 0, 'market_data_read': False,
            'scientific_readiness': False, 'full_objective_complete': False}


if __name__ == '__main__':
    print(json.dumps(check(), indent=2))
