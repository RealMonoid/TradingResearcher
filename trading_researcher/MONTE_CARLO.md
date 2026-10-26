# Development Monte Carlo boundary diagnostic

The optional diagnostic in [monte_carlo.py](monte_carlo.py) advances the boundary-instability requirement in [research-contract/1.0 section 5.3](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#53-dependence-and-uncertainty-dispatch). It is an **uncalibrated implementation candidate**. It does not activate an evidence rule, certify a bootstrap law, change delta, satisfy N_min, or issue scientific readiness.

## Explicit inputs before execution

The existing operator operation accepts an optional argument:

```json
{"mc_policy":{"schema":"mc-boundary-policy/1","noncoverage":{"numerator":"1","denominator":"100"}}}
```

This is an illustrative development setting, not an adopted default or a market-error budget. The operator must provide the exact noncoverage. The host obtains delta and direction from the owned evaluation plan; a caller cannot replace them in this argument. The request and enriched policy enter the protected bootstrap input capsule before any resampling child starts. Interrupted retries keep the original policy, case bytes, seeds and source version. A changed policy requires another exploratory request and retains its exposure; it cannot be represented as an untouched scientific assessment.

Calls without the optional policy retain the version-1 calculation and unassessed boundary gate. Configured calls emit `joint-bootstrap-computation/2` and a `mc-boundary-diagnostic/1`. Neither route changes the fixed 19,999 draws, seeds, sensitivity lengths, basic intervals or scientific authority. The candidate method and the chosen development setting remain subject to independent conformance and calibration before any scientific use.

## Computation and interpretation

Order-statistic confidence bands use binomial counts to describe uncertainty in a population quantile. [NTIA Technical Report 09-458, section 4.2](https://its.ntia.gov/publications/download/TR-09-458.pdf) describes that relationship. The following exact implementation, tie handling, resource envelope and composition into a boundary diagnostic are project-specific deductions; that source does not validate them for market inference.

For each deduplicated sensitivity length, the diagnostic targets the two population quantiles of its conditional bootstrap distribution. With K lengths and supplied per-claim MC noncoverage beta, each of the four one-sided rank failures per length receives beta/(4K). This union bound does not require independence between lengths. Its probability interpretation does require iid draws from each fixed conditional bootstrap law; deterministic PRNG execution and replay alone cannot establish that assumption. This is not a simultaneous bound across research claims and does not establish market-interval coverage.

For B draws at quantile probability p, choose the largest lower rank k with `P(Binomial(B,p) < k) <= tail` and smallest upper rank l with `P(Binomial(B,p) >= l) <= tail`. Ranks are one-based. Rank zero means minus infinity; rank B+1 means plus infinity. They are never silently clipped to the observed extrema. Exact integer binomial recurrences avoid floating-point tail decisions. Inclusive order bounds are conservative at atoms under the lower population-quantile convention; exact coverage equality is not asserted.

The application reflects each quantile band through the basic-interval formula and then encloses all sensitivity cases. The population-quantile target differs from the prescribed finite-sample linear quantile interpolation. Therefore each endpoint range is also enlarged to contain its actual finite-draw endpoint. The diagnostic checks whether the existing directional or nondirectional classification remains the same throughout these conservative endpoint ranges, preserving strict directional boundaries and the closed nondirectional negative region. Any unbounded endpoint conservatively declines stability in this candidate.

`ASSESSED_UNCALIBRATED` reports the calculation and `boundary_stable`. Its nominal classification is a description of the supplied development interval, never an EvidenceRecord. An unstable boundary must not be promoted through this diagnostic. Undefined or incomplete required draws return `NOT_ASSESSED`, with stability null. No draw is filtered, replaced, added or selectively reseeded. Scientific readiness and classification permission remain false even for a stable boundary.

## Binding, limits and verification

The [owned bootstrap runner](bootstrap_runs.py) recomputes the diagnostic from the retained draw stream and exact bound policy before committing the result. Completed computations also receive the existing separate-process retained-source replay. Resource-stopped runs retain an unassessed diagnostic; computation limits include the diagnostic and replay. The inherited stopped-prefix limitation remains: numeric paths and values are not fully replayed after a resource stop.

The rank kernel accepts at most 19,999 draws and probability denominators at most 2^32. Supplied beta has denominator at most one million. These bounds limit intermediate exact-integer work; they are implementation resource limits, not statistical defaults. Existing rational-result limits still apply. The host's child deadline remains the outer execution limit.

The [checkpoint report](../docs/reviews/implementation-2026-10-25/mc-stability-verification.json) records tests, independent review, preservation and exact outcomes. The [baseline](../docs/reviews/implementation-2026-10-25/mc-stability-baseline.json) preserves the preceding implementation. Still required are development nuisance/dependence and N_min derivation, independent statistical calibration and assumption checks, scientific data/exposure acceptance, genuine provider/semantic provenance, and atomic scientific allocation/freeze. Software conformance does not establish statistical coverage or economic usefulness.
