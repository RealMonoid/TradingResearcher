# Descriptive case diagnostics / case-diagnostics/1

This optional reporting adapter preserves the accepted expression, missingness and numerical contracts. It adds observations about an existing computation, not operators, eligibility rules, a new estimand or scientific classification. The concrete need is the original retained ETH idea's requirement for separate reason counts. The [implementation sequence](../docs/reviews/integration-research-2026-10-24/IMPLEMENTATION_SEQUENCE_2026-10-25.md) remains the work plan.

## Inputs and unchanged calculation

The optional `reference-computation/3` certificate and `bound-reference/3` execution select this adapter explicitly. Profiles /1 and /2 preserve their source closures, fixed expectations and output formats. The original bounded calculation completes first. Its exact numerical report, cases and contrast are not repaired by diagnostics. The adapter re-evaluates only the same scope/condition/outcome computations that the base path actually reached, on the same retained rows and cutoffs. It requires exact agreement with observed base values. It does not inspect an outcome skipped by the base path, load additional observations or access protected data.

The output uses `diagnostic-bounded-reference-cases/1`. Each original case acquires a separate `diagnostics` member; removing these members and the diagnostic metadata reconstructs the base report exactly. `base_case_stream_sha256` hashes each original canonical case plus newline, in original order. `base_report_hash` is the canonical digest of `{report: original metadata without cases, case_stream_sha256: base_case_stream_sha256}`. This fixed-size binding avoids serializing the whole case list through the transport envelope. Existing owned source retention, child replay and backup/restore apply to the new case bytes.

## Observations and counts

Each processed diagnostic case retains unique events with program name, exact expression JSON pointer, observation time, availability time and the existing engine reason. Program names are `scope_program`, `condition_program` and `outcome_program`. An expression pointer starts at `/expression`. Repeated events at the same program/path/time are deduplicated, not treated as additional observations.

Each reason category counts decision rows once; categories can overlap and must not be summed as a partition:

- `boundary_censoring`: the base case has `PARTITION_BOUNDARY` status.
- `absent_row`: a required in-universe observation is absent.
- `missing_warmup`: a required observation before the declared universe start is absent.
- `input_before_universe`: a traversed dependency precedes that start, whether present or absent. This observation does not authorize its use.
- `missing_value`: a supplied feature value is null.
- `missing_feature`: the required feature entry is absent.
- `unavailable_data`: an actual feature sample is not available at the original evaluation cutoff.
- `numeric_domain`: the existing calculator reports division by zero or a logarithm-domain failure.
- `condition_unknown`: the base path evaluated a scope-true condition and its value is unknown.

A literal null is retained as a syntactic event, not counted as a missing market value. In particular, the null in a complete-validity guard may be evaluated even when the condition result is true or false. No raw trace count is an automatic invalid-data classification.

The adapter recognizes only the exact existing composition `G(V,P) = (V AND P) OR ((NOT V) AND unknown)`, optionally under explicit outer lag nodes. Both copies of V must be structurally identical and `unknown` must be a Boolean null literal. It records the first V path and its observed value. Guard counts distinguish true, false, unknown, unrecognized composition and a recognized guard not evaluated by the base path. This is a neutral Boolean observation: recognition does not prove that V expresses validity. Interpreting `guard=false` as the original idea's invalid inputs requires the formalizer to map that exact V path to the original validity checks and the independent meaning reviewer to accept the mapping. An arbitrary scientific threshold cannot silently become an invalid-data rule.

For the original ETH report, a faithful mapping must explain which retained raw/domain reasons and reviewed guard-false cases represent each requested missing/invalid category. Unknown conditions remain in the observed whole-scope denominator. Diagnostics neither discard rows nor substitute a new treatment for a missingness requirement.

## Resources and incomplete reports

Diagnostic work consumes the primitive steps remaining from the existing explicit computation cap after the original case calculation. It cannot increase that cap. Per-case event and encoded-size limits prevent an unbounded trace; exceeding either returns `RESOURCE_STOP`. Previously completed diagnostic cases remain, later cases have `diagnostics: null`, and exact processed/unprocessed counts are retained. A stop never becomes a complete reason-count report. Base numerical results remain available with their original qualifications.

Nonfinite source strings fail the existing row-admission contract; the adapter does not convert that global failure into a row-level unknown. Feature certification, historical data rights/availability, meaning fidelity, inference/calibration, scientific freeze and economic usefulness remain separate. An execution record or a passing software test does not establish any of them.
