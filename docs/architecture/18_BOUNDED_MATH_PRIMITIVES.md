# Bounded Math Primitives / bounded-math/1.0

Status: **ACCEPTED specification**, D089, October 29, 2026. Implementation, independent certification and faithful research execution are separate prerequisites. This optional extension preserves research-contract/1.0 and every legacy `research-ast/1` record.

## Approval and scope

Source **SESSION-2026-10-29-BOUNDED-MATH** is the current repository chat, separate from the immutable conversation archive. After the [concrete proposal](../reviews/integration-research-2026-10-24/INTEGRATION_PROPOSAL.md#october-29-proposal-faithful-execution-of-the-retained-single-instrument-eth-idea) defined median semantics, logarithmic outcomes, numerical bounds, validation and rollback, the user selected verbatim:

> Begrenzte Erweiterung freigeben (empfohlen)

The approved purpose is faithful execution of retained single-instrument ETH idea `e579e41eb2adf198a16c3cf4c3a23ae28da41ef35472200b85ea2205cb1074e5`, rather than substituting a mean or simple return. The other original idea remains retained with its cross-instrument gap. This approval changes no market universe, delta, evidence rule, protected-data permission, spending authorization or live-capital authority. It does not authorize an open-ended language program.

## Mathematical and temporal meaning

1. **Trailing median.** `trailing_median(arg, bars)` uses exactly a positive integer number of same-instrument grid observations, including the expression anchor. Every input must be finite, present, causally available and have the same units. Sort their real values; for odd windows use the middle value, and for even windows the exact arithmetic mean of the two middle values. Missing/unavailable observations make the window missing. Existing explicit lag places the original idea's window before its event. No shortened window, nearest-row substitution, interpolation convention or fitted state is permitted. Existing grid, unit, resource and causal rules apply.
2. **Natural logarithm.** `ln(arg)` takes a dimensionless strictly positive finite real ratio, and returns its dimensionless natural logarithm. Initially it is allowed only inside an outcome expression, not decision-time scope/condition/measurement indicators. Nonpositive, missing or unavailable inputs produce a named domain/missing result; no clipping or replacement. The outcome keeps its original price keys, future anchor and information interval.
3. **Bounded numerical outcome.** Logarithms are generally irrational. Retain proven outward rational lower and upper bounds containing the mathematical value, identified as an enclosure rather than an exact observed rational. The initial basis-point outcome must have enclosure width at most `10^-12` basis points for each observed case. Failure to establish that bound is a numerical gap. This is computational accuracy, not a change to delta or a scientific decision threshold. Exact arithmetic propagates bounds conservatively through arithmetic, conditional/scope means and their difference; do not discard bounds for later inference.
4. **Unchanged missingness.** Existing three-valued Boolean semantics remain intact. The formalizer must demonstrate the original complete-input/invalid-input unknown rule using admitted composition, or retain a further gap. Unknown C remains in the observed whole-scope denominator and outside the conditioned group as already specified. No approximate value may determine a new Boolean decision by silently choosing its midpoint.

## Versioning and implementation boundary

Use an explicit opt-in expression/execution version, initially `research-ast/2` for the new operators and separately versioned bounded case/contrast records. `research-ast/1` rejects these new meanings and retains its exact rational outputs. An implementation may use a smaller explicitly reported executable subset; unsupported composition is a retained capability gap. Original ideas, old capsules, failures, numerical bounds and exposure survive every retry and rollback.

The original single-instrument idea still needs independently reviewed formalization, qualified development data and an owned retained-source calculation/replay. The initial extension supplies descriptive computation only. Existing scalar-only inference must reject bounded outcomes until a separately applicable estimator/calibration path preserves their uncertainty. Operator approval does not grant scientific classification.

## Acceptance and rollback

Independent fixed expectations cover median odd/even windows and ties; lag/alignment, missing/late samples, units and boundaries; log zero/negative/one and ratios above/below one; rigorous numerical containment and width; arithmetic/aggregate bound propagation; resource exhaustion, dependency closure and separate replay. Existing scalar/Boolean behavior and legacy result bytes remain unchanged for their old source/version. Implementer-authored expectations alone cannot issue a certificate.

Successful extension acceptance requires independent implementation conformance, the original idea passing faithful meaning review, and a reproducible bounded-error descriptive calculation. A remaining gap is an honest stopping outcome, not successful extension or research-milestone completion. Rollback disables the optional new profile for future work and restores the applicable old profile without deleting trials, bounds or exposure.

Affected: D002–D004/D008/D026/D074/D084; DEF-003–008/013/023/031–032; REQ-002/003/005/011/026; CMP-02/03/04/05/06/07 and IF-03/04/08/09. D089 extends the admitted primitive envelope only in the scope above. Material changes still require D008/D026 approval.
