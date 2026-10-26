# Lag-linked binary stress worlds

This additional development model preserves a recognized shifted condition/outcome value identity. It does not execute the original AST, fit a market process or confer scientific readiness. The original [response/mask generator](POPULATION_MODELS.md) remains available with unchanged numerical behavior.

## Scope and exact target

The specification is `lag-linked-binary-spec/1`, with exactly `mask_mean_block`, an exact rational `common_share`, and `rationale`. The existing owned scalar/family population and study APIs accept it through the existing `specification` or `profile.specifications` fields. For example:

```python
from fractions import Fraction
from trading_researcher.lag_population import specification

spec = specification(2, Fraction(1, 2), "Declared engineering stress; not fitted or validated.")
```

Those numbers are explicit engineering inputs, not universal defaults. The model requires a literal true source scope and a recognized source identity `C_t = Y_(t-d)` with positive integer `d`. Its exact source request, cases and diagnostics are bound. Unsupported syntax/shift/scope and observed value disagreements remain explicit model gaps. These restrictions limit this model's applicability; they do not restrict invention or rewrite an unsupported hypothesis into the supported form.

Let `q` be the source's pooled eligible outcome rate and `e` an effect assigned by the existing plan. For each synthetic response/instrument, declare:

```
P(Y_t = 1 | Y_(t-d) = 1) = a = q + e
P(Y_t = 1 | Y_(t-d) = 0) = b = q - q*e/(1-q)
```

The stationary marginal is `q`, since `q*a + (1-q)*b = q`. Each time phase modulo `d` is a separate Markov chain. The generated condition value is its own earlier latent response, including when intervening rows are missing. The effect also fixes latent serial dependence: at lag `k*d`, correlation is `(e/(1-q))**k`; other positive lags have zero latent correlation because phases are independent. There is no independent persistence knob. In particular, the zero-effect latent law is IID over time. This is one specific stress law, not every possible dependent null process.

Original joint scope, eligibility and condition-knownness masks are sampled with the declared stationary circular-block law, independently of latent responses. Original true/false condition VALUES are not resampled. If `r` is the eligible condition-known fraction, the generated true-group fraction is `w = r*q`. Its observable complement rate is `p_other = q - w*e/(1-w)`, distinct from the latent transition `b` when some conditions are unknown. The report retains source condition fraction, generated `w`, `r`, latent transitions and observed group rates separately. Under these explicit exogeneity assumptions, the pooled conditional-minus-scope contrast remains `e`. Empirical source rates need not satisfy the stationary law exactly.

## Common innovations and exact stationary initialization

At each actual synthetic timestamp, each coordinate independently chooses a fresh common uniform innovation with probability `common_share`, otherwise its own fresh uniform. Thresholds use its previous state and its assigned effect. Different response/instrument coordinates can therefore share shocks; different time phases do not share an artificial initial state or cross-time innovation. Zero common share still leaves the exogenous mask process shared.

The bounded solver supports one through four response-by-instrument coordinates, hence at most sixteen joint states. Coordinate `i` is integer-state bit `i`. Each transition row integrates the conditional product probabilities over the exact common-uniform threshold intervals. Fraction arithmetic solves `pi P = pi` with total mass one, then independently checks every residual, nonnegative mass and normalization. Strictly interior transitions give a state-independent positive all-zero reset probability, hence a unique stationary class even when some states are transient. This is a project derivation using the standard [stationary-distribution equations](https://www.cs.ox.ac.uk/people/elias.koutsoupias/pc2017-18/lectures.html), not an empirical model-fit result.

One exact integer-CDF sample from that joint distribution initializes each of the `d` independent phases. The matrix, stationary probabilities, CDF counts, coordinate order and actual initial phase states are retained. No finite burn-in, convergence heuristic, successful-initialization selection or floating-point approximation is used. Random streams remain domain-separated MT19937 with integer rejection sampling; finite PRNG behavior is not a certificate of an ideal probability law.

Transition boundaries are outside this implementation's capability even when mathematically feasible. They are distinguished from infeasible probabilities and are never clipped. Other envelopes are four joint coordinates, 100,000 phase-coordinate states, 100,000 generated cases and 4,096-bit exact stationary arithmetic. Unsupported capacity produces an explicit failure/gap; it is not silently split, approximated or dropped from a study inventory. Existing parent deadlines, logical byte accounting and retained-failure rules still apply.

## Retention, compatibility and limits

Nested model/world schemas are `lag-linked-binary-model/1`, `lag-linked-binary-world/1` and `lag-linked-binary-family-world/1`. Existing owned operation envelopes, immutable input capture, fresh-process calculation/replay, complete inventories, attempt accounting, final privacy and source-currency rules are reused. Source boundaries become synthetic missing outcomes and final-horizon censoring remains explicit. Latent states advance on every timestamp regardless of masks.

Family components have distinct synthetic responses and their own generated conditions. They share masks and can share innovations; they are not different real ASTs executed on one price path. One complete family vector is one outer world. The existing estimator, fixed 19,999 draws per required length, multiplicity, failure denominators and classification arithmetic are unchanged. Historical source capsules are not migrated, and older final studies do not gain current-source authority.

All outputs retain `n_min: null`, false scientific readiness and no classification authority. This model does not establish raw-feature dynamics, arbitrary original-AST overlap, heterogeneous instrument rates, endogenous selection/missingness, stationarity of market data, a fitted nuisance law or full-process calibration. It does not explain negative empirical products at other lags merely by preserving one temporal identity. [Actual owned verification](../docs/reviews/implementation-2026-10-25/LAG_LINKED_POPULATION_2026-10-26.md) records the completed bounded probe and remaining work.
