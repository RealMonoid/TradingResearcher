# Exact ordered-replicate reuse

Status: exact-output comparison and repeated pipeline timing passed. The linked verification record governs final regression/documentation outcomes and scope.

## Purpose and measured bottleneck

Continue the full implementation after `dc3e6fc`, which reduced retained storage but did not demonstrate a speed gain. The preceding hook-only turn reran checks without implementation progress. The remaining full-series budget problem requires measured improvements while preserving every case, draw, failure and scientific rule.

Profiling the existing preselected 64-row, two-response mixed synthetic family showed 180,283,485 calls and 40.090 seconds under instrumentation. `sorted` accumulated 13.387 seconds, including repeated exact parsing/sorting of the same 19,999 values for basic intervals and Monte Carlo bands. Profiled time is diagnostic overhead, not an uninstrumented performance benchmark. This observation selects redundant ordering as the current target; it does not establish complete-series feasibility.

## Bounded implementation

Only `evaluation_policy.py` and `monte_carlo.py` change runtime behavior. The public basic interval parses and sorts all supplied replicates once, then uses the exact immutable ordered tuple for both type-7 quantiles. Each Monte Carlo sensitivity similarly shares one ordered tuple between its two rank bands and basic interval. The enclosing interval, binomial rank arithmetic, classifications, all required counts and undefined-draw handling remain unchanged.

Reuse stays within one function call and one exact list. There is no cross-input cache, floating-point ordering, approximate quantile, skipped invalid record or weakened validation. Original intermediate rational bounds are retained, including encoding `alpha/2` before draw validation. That preflight preserves the original resource-failure precedence even when the draw list is also invalid. Public signatures and numerical result schemas remain unchanged; source provenance changes normally.

Independent tests retain a complete original source package under a separate import namespace. Fixed negative/tied/interpolated and 200-bit near-tie expectations, late invalid values, unchanged error precedence, unbounded rank endpoints, all three classification directions, input mutation and full old/new diagnostics check exact behavior. Instrumentation separately verifies one parse/sort per relevant list. Initial missing-helper and failure-precedence red checks remain retained.

## Measured pipeline comparison

The six actual cold pipeline executions used the predeclared AB BA AB order. Each retained and separately replayed the entire same fixed world: 79,996 draws and 256 generated case records. These are repeated timings of one synthetic world, not six independent calibration observations. All complete results and all encoded stream bytes were identical; the unchanged decoded stream contains 22,787,327 bytes.

| Pair | Before, seconds | After, seconds |
|---|---:|---:|
| 1 (AB) | 21.628 | 17.381 |
| 2 (BA) | 21.928 | 17.395 |
| 3 (AB) | 22.289 | 16.886 |
| Median | 21.928 | 17.381 |

The median reduction is **20.74%**. The slowest new execution (17.395 seconds) is faster than the fastest baseline (21.628 seconds). This passes the predeclared engineering gate of more than 5% improvement with disjoint observed ranges and identical complete results/streams. The gate is not a scientific threshold or a general hardware/workload guarantee. The encoded stream stays 4,079,481 bytes; logical per-attempt charge changes from 19,148,378 to 19,150,036 bytes because the retained source grows. No storage saving is claimed by this step.

## Verification and continuation

The [verification record](ordered-replicates-verification-2026-10-26.json) binds exact source/test hashes, commands, UTC timestamps, exits, [benchmark observations](ordered-replicates-benchmark-2026-10-26.json) and [independent review](ordered-replicates-independent-2026-10-26.json). The original implementations remain in the pinned source archive. Sampler/population-model sources, contracts and prior fixtures remain unchanged and hash-checked. Reproduction procedures in the evidence archive use the repository's `.trf-runtime/calibration-cost-checks-2026-10-26` directory.

The remaining resource path must respect document 14 section 9: additional computation requires a recorded continuation decision and cannot replace missing independent observations. Its 60-minute calibration cap does not by itself prohibit such a documented continuation. The current implementation still caps aggregate compute at 60 minutes and logical storage at 4 GiB; this optimization changes neither limit and implements no continuation mechanism. Inspect that consuming path next, retaining original worlds, seeds, failures and complete denominators instead of silently resetting or replacing an exhausted series.

Full repository tests, broad hardware/workload performance, complete-series feasibility, nuisance/stress adequacy, justified information targets and actual final calibration remain separate. Continue the original campaign/reservation, scientific admission/freeze, genuine mixed-provider research, policy/AmiBroker and domain-reporting objective after those dependencies. No paid provider call, protected market evaluation or scientific readiness is claimed here.
