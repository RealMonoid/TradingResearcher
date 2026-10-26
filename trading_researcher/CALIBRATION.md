# Narrow calibration count assessment

The [calibration module](calibration.py) implements the numerical acceptance checks adopted in [research-contract/1.0 section 11](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#11-open-11-finite-success-and-continuation-criteria). The read-only CLI accepts supplied observations without authenticating them. A separate [owned runner](calibration_runs.py) connects retained single-claim simulation attempts to these counts. Neither interface authorizes assessment access, freeze, evidence publication or capital.

## Fixed criteria

Each predeclared cohort has exactly 256 distinct outer-world IDs. A joint simulated market/batch is one world; its instruments, claims and bootstrap draws are not additional independent trials. Different stress laws are assessed separately and cannot be pooled to improve a result.

| Criterion | Event counted once per world | Adopted check |
|---|---|---|
| `false_support` | Support under the declared zero world | One-sided exact 95% upper bound at most 0.10 |
| `boundary_decisive` | Support **or** negative at the declared decision boundary | Same upper-bound check on the union event |
| `joint_miscoverage` | Any required interval misses its own known truth in the joint batch | Same upper-bound check |
| `detection` | Support at the declared alternative beyond the boundary, initially 2*delta | One-sided exact 95% lower bound at least 0.70 |

At 256 observed worlds, 17 errors pass and 18 fail; 191 detections fail and 192 pass. The separate 80% point design target needs 205 detections and is reported separately. It is not substituted for the lower-bound criterion or imposed as an additional final-assessment threshold.

The code compares exact integer binomial tails at the adopted thresholds. Displayed endpoints use outward rational brackets on a 2^40 grid; rounded displayed bounds do not control acceptance. It reuses the existing exact binomial implementation: the two endpoints of a central 90% interval equal the respective one-sided 95% endpoints. The report exposes only the requested side and never labels the combined interval 95%. [NIST's exact-binomial reference](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm) supplies the tail-inversion basis; the numeric adoption thresholds come from the project contract, not NIST.

## Input and command

Run:

```powershell
python -B -m trading_researcher assess-calibration-counts --request <count-request.json>
```

The bounded canonical JSON request contains exactly `manifest` and `observations`. It is read without modification. No registry, key, network request or simulation is opened by this command. Exit 0 means `PASS_COUNTS_ONLY`; exit 2 means `FAIL_COUNTS_ONLY` or `NOT_ASSESSED`; malformed input exits 1 without a success report.

The manifest contains `schema: narrow-calibration-assessment-plan/1`, `estimator_ref`, `population_ref`, one through sixteen `cohorts`, and `applicability`. Each cohort contains `id`, `criterion`, 256 unique `world_ids` and a `rationale`. All four criteria above are required. Reusing a world for another criterion is permitted; duplicating it within a cohort is not.

`applicability` explicitly addresses `heavy_tail`, `overlap` and `common_shock`. Each entry contains `status` (`included` or `not_applicable`), `cohort_ids` (nonempty for included, empty otherwise), and a nonempty `reason`. These are retained declarations. A reason string does not demonstrate that a simulation actually includes a stress or justify its adequacy.

Each observation contains `cohort_id`, `world_id`, `state`, `event`, `source_ref` and `reason`. An `observed` record needs an exact Boolean event and null reason. An `unavailable` record needs null event and a retained reason. All source references are explicit, but this pure boundary does not resolve or authenticate them. One retained batch artifact may contain multiple worlds.

Missing or unavailable worlds yield `NOT_ASSESSED`; the code never replaces them with false events or renormalizes to fewer trials. A partial report retains observed event counts and missing/unavailable IDs but supplies no rate, bound or passing criterion. Completed failing cohorts remain visible when another cohort is incomplete. Duplicate, undeclared or mismatched IDs and malformed types fail validation. Input hashes bind the exact supplied request; input lists are detached before assessment and not mutated.

## Owned single-claim execution

The operator RPC `prepare_evaluator_calibration` takes exactly `key`, `development_study_id`, `time_rows`, `seed`, `budget`, `cost_estimate` and `applicability`. It requires a complete owned development study, one primary binary claim and an already studied target. It freezes 256 worlds per declared stress/effect cell, preserving zero, boundary and 2*delta alternatives (both signs when assigned). Required cells are never silently removed to fit storage, world or cohort envelopes.

`advance_evaluator_calibration(calibration_id=...)` executes at most one next world with the exact retained development calculator, followed by separate process replay of the cases, draws and result. `inspect_evaluator_calibration(calibration_id=...)` reports recorded attempts, original budgets, missing worlds and count assessment. The same durable reservation, failure, retry and orphan accounting used by development studies applies. An interrupted unknown attempt charges its full reservation and fences replacement work. This is logical storage and parent elapsed-time accounting, not an OS quota; final commit and read-only inspection overhead are excluded.

The final manifest uses a distinct seed namespace and compares both seed streams and world IDs against every recorded development/final study. This establishes recorded disjointness, not mathematical independence of PRNG streams or absence of external tuning. A new key aliases the same series; changing seed, budget, cost or applicability for the same scientific input conflicts. The identity retains case bytes, scientific request fields, diagnostics, numerical stress parameters, assigned estimator settings and calculator source. Provenance-only report references, development artifact aliases and rationale text do not grant fresh attempts. The original request remains immutable.

Input and attempt schemas are controller-owned `evaluator-calibration-input/1` and `evaluator-calibration-attempt/1`, classified as operations. Discovery/formalizer contexts reject these records and all recorded descendants, including released reporter products, through both source references and exposure. Generic source/worker writes cannot mint these schemas. This is an authenticated tool boundary; the trusted operator, local OS account and arbitrary filesystem access are not sandboxed.

Events come from retained owned attempts, not caller-supplied success flags. At the boundary, support and negative decisions form one union event. Undefined-information outcomes count as no decisive result but cannot provide interval coverage; technical/model failures provide no observed events. Partial or unavailable cohorts cannot pass. Count interpretation is bound to the host source footprint; a changed implementation suppresses counts and blocks further execution while inspection and orphan recovery remain available. Source hashes detect drift; they are not independent proof of loaded machine code.

The selected target is labeled either the development candidate or a studied sensitivity cutoff. It never becomes `N_min` merely because a finite grid was examined. Single-claim interval coverage is the degenerate family case. The separate [development family runner](POPULATION_MODELS.md#joint-synthetic-response-families) now generates coherent shared-template worlds with mixed true effects and executes the actual estimator, but is not integrated into the final inventory/count assessment. This single-claim final runner still cannot close the complete section 11 calibration requirement.

## Remaining work

All reports retain `scientific_readiness: false` and `n_min: null`. Owned attempt authentication and fixed single-claim event extraction do not establish population adequacy, justified stress applicability, independent sampling, substantive semantic review, historical data admission, complete evaluator/full-process calibration or scientific freeze. The actual final series remains incomplete until every required world is present; integration fixtures and individual replayed worlds do not supply that result. These remain in the original seven-package plan.

The independent [numerical fixture](../tests/fixtures/reference_calibration_counts.json) and [authorship note](../tests/fixtures/reference_calibration_counts.md) were fixed before implementation. [Verification](../docs/reviews/implementation-2026-10-25/calibration-count-verification.json) records exact checks and source preservation; [independent review](../docs/reviews/implementation-2026-10-25/calibration-count-review.json) has its own scope. Fixture observations are synthetic and cannot be reported as completed real simulations.
