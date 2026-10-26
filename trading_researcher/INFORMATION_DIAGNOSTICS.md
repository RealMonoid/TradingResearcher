# Owned development information diagnostics

`prepare_information_diagnostics` measures the development data needed to build an information-study model under research-contract/1.0 section 5.4. It does not estimate power, select a sample target, fit a response model, choose a block length, calibrate the evaluator or grant scientific readiness.

## Position in the research flow

The operation consumes an existing controller-owned development `evaluation-plan/1` and its declared `reference-execution/1`. The shared plan/execution binding checks the exact compiled hypothesis, data snapshot, certified dependencies and committed case bytes. Assessment and corroboration inputs remain inaccessible through this route. Deterministic measurement does not require the plan's bootstrap PRNG to be executable.

Before calculation, the controller commits `information-diagnostics-input/1` with the exact request, case descriptor, source bytes, Python runtime identity and inherited exposure. A separate isolated process calculates the diagnostics; a second process replays the retained version and compares the result and every contribution byte. Completion creates a new immutable `development-information-diagnostics/1`. It does not edit the old plan or create an EvidenceRecord. These records retain their creation time for later context admission and exposure propagation into the four memory views.

The [population-world operation](POPULATION_MODELS.md) now provides a versioned response/mask stress generator from these owned inputs. A fixed, finite power-study profile using the actual prescribed bootstrap and MC procedure remains the next integration step. Diagnosing the data or generating hypothetical worlds does not complete that study, scientific allocation/freeze or narrow/final calibration. A genuine LLM research cycle and separate AmiBroker policy evaluation remain downstream work.

## Request and retention

Use the existing operator RPC interface with these exact arguments:

```json
{
  "key": "development-diagnostics-001",
  "plan_id": "<owned evaluation-plan artifact id>",
  "execution_id": "<declared development execution artifact id>",
  "lags": [1, 2, 4, 8],
  "limits": {"max_seconds": 120}
}
```

The lag list is explicit, strictly increasing, contains 1–16 integers from 1 through 100,000, and is retained before results. Lag zero is also reported. The total calculation/replay time cap is an explicit integer from 1 through 1,800 seconds. These are computation bounds, not additional independent observations or a scientific stopping policy.

The diagnostic candidate supports complete binary reference reports with at most 100,000 cases and 16 instruments. Larger instrument universes receive a resource gap, without truncation. Other outcome types receive an evaluation gap preserving their original meaning. Pending, incomplete or review-required observations remain input gaps. Empty scope/condition groups and observed rates of zero or one retain available measurements and explicit model-identification gaps.

Repeat the same key and unchanged arguments to retrieve the completed result or retry retained inputs after interruption. A changed request needs a new key. Failed attempts remain visible through `inspect_bound_computations`. The source capsule and contribution blob participate in the existing complete backup/restore closure. Installed Python remains a fingerprinted dependency; it is not archived by this operation.

## Exact measurements

All results use rational arithmetic. Counts must be actual nonnegative integers; Boolean aliases are rejected.

- Scope, true-condition, false-condition and unknown-condition counts, event counts and rates are reported jointly and per instrument. Unknown conditions remain in the scope denominator. Missing outcomes never become observed zero events.
- Every aligned timestamp is retained, including timestamps with no eligible instrument. A JSONL blob stores scope count `N_t`, scope successes `S_t`, true-condition count `C_t`, true-condition successes `Z_t`, and false/unknown counts. State/run summaries distinguish data gaps, missing outcomes, scope exclusion and partition boundaries.
- With totals `N`, `S`, `C`, `Z` and `T` grid timestamps, the empirical contrast-score contribution is `T*(Z_t - (Z/C)*C_t)/C - T*(S_t - (S/N)*N_t)/N`. It is undefined when either denominator is zero. Its sum is zero on the complete grid. This is a descriptive dependence diagnostic, not an influence-function power substitute.
- Count, centered outcome and contrast-score lag moments use the global full-grid mean and the actual noncircular `T-lag` pair divisor. Unsupported lags have zero pairs and a null moment. Empty slots keep their original separation.
- Outcome serial and contemporaneous cross-instrument products use only pairs with both outcomes observed, centered at each instrument's full eligible-sample event rate. Pair counts, possible grid pairs and paired-sample marginal means are explicit. Serial pairs are ordered **left earlier, right later**. These fixed-center products are not automatically covariances or correlations of the paired population when paired marginals differ.

No empirical moment certifies independence, stationarity, missingness assumptions or the adequacy of a fitted simulation model. Positive-only response models cannot silently absorb observed negative dependence. Scientific classification remains forbidden and `n_min` remains null in every diagnostic result.

## Verification scope

The fixed independent fixtures distinguish a hand-computed report-layer example from a coherent raw-row materialization; deleting a row can also invalidate an earlier overlapping outcome. Expected bytes are frozen separately from implementation. Tests cover exact moments, denominator and pair-order conventions, gaps, resource bounds, ownership, namespace protection, immutable requests, interruption and separate replay.

[Checkpoint verification](../docs/reviews/implementation-2026-10-25/nuisance-diagnostics-verification.json) records exact checks and unverified boundaries. Software tests do not establish model adequacy, calibrated power, market usefulness or live trading authority.
