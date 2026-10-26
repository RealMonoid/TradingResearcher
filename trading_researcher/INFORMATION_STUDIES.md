# Owned development information studies

New source snapshots retain complete case/draw streams using versioned bounded gzip, with encoded and decoded SHA-256/size and separate exact-byte replay. Old retained raw source snapshots remain supported. Physical encoded files enter the existing logical accounting; the independent decoded computation cap is 256 MiB. No draw or failed prefix is dropped. [Implementation and measured limits](../docs/reviews/implementation-2026-10-25/STREAM_RETENTION_2026-10-26.md) include a real old/new pipeline comparison. Compression alone does not establish full-series budget feasibility.

Status: implemented and verified within the bounded engineering scope. This is a development simulation facility, not scientific admission, calibrated power, an accepted market model, or a frozen N_min.

The corresponding joint-family operations are `prepare_family_study`, `advance_family_study` and `inspect_family_study`. They use the same ownership, retention and budget machinery with `family-study-input/1` and `family-study-attempt/1`. Preparation takes the same fields, adding `responses` and `patterns` inside `profile`. Responses are sorted distinct synthetic IDs matching the owned plan's family count (two through eight). Patterns are sorted distinct complete vectors of effect-scenario indices, aligned with those IDs. Every homogeneous allowed effect vector and at least one genuinely mixed vector are mandatory; at most eight vectors and 2,048 total worlds are admitted. Every response runs the actual fixed-draw estimator on one shared template law. Target candidacy requires a complete development inventory and the 80% point target separately for every declared 2*delta response/stress/vector; it remains a tested-grid candidate, not N_min. See [final family series](CALIBRATION.md#owned-joint-family-series) for the protected assessment boundary.

`prepare_information_study` binds an owned development evaluation plan, its declared execution, matching nuisance diagnostics, and a finite operator-supplied profile. It retains the exact source/runtime, case bytes, inherited exposure, complete ordered world inventory and all generation/bootstrap seeds before starting a simulation. Protected or unowned diagnostic/cost ancestry fails before source-package reads.

`advance_information_study` reserves one full attempt envelope and advances the next fixed world. It generates synthetic binary responses/masks, executes all prescribed 19,999 bootstrap draws at each distinct required length, applies the plan-bound MC diagnostic, and repeats the complete pipeline in a separate isolated process. The exact ordered case/draw stream and failed prefixes are retained as immutable blobs. This repeats installed deterministic code; it is not an independent statistical method or proof of model adequacy.

`inspect_information_study` returns the fixed-grid summary, retained attempt artifact IDs, aggregate charges, next world and pending/terminal state. Only operator capabilities can invoke these three operations. Workers cannot manufacture their reserved artifact namespaces. Research-memory visibility also respects the artifacts' creation times and inherited exposure.

## Inputs and execution

The preparation arguments are `key`, `plan_id`, `execution_id`, `diagnostics_id`, and `profile`. The profile requires:

- One to four distinct population stress specifications, one to eight increasing historical-grid targets, one to 256 worlds per cell, and a fixed seed. The total inventory is bounded to 2,048 worlds and the canonical 1 MiB input limit still applies.
- Exact rational `mc_noncoverage` and `outer_noncoverage`. The existing plan assigns delta, direction, primary-family count and block lengths; callers cannot replace them.
- Positive integer aggregate/per-attempt compute milliseconds and logical storage bytes, plus at most three attempts per world. Limits remain fixed for the study.
- A retained `cost_estimate` with `source_ref`, `world_time_rows`, `observed_compute_ms`, `observed_storage_bytes`, and `qualification`. Its source must have the exact body `{"schema":"development-study-cost-estimate/1", ...estimate_without_source_ref}` and development-only ancestry. This preserves the operator's measurement claim and qualification; the controller explicitly does **not** authenticate it as a benchmark.

Targets count joint calendar positions within the bound historical window. They do not count independent observations. Effects include zero, delta and twice delta, with both signs for nondirectional claims. Retries keep the same world and seeds. Completed information gaps and MC abstentions are not retried to obtain more favorable outcomes.

Preparation with the same key/arguments returns the same capsule; changed arguments conflict. A different key with identical arguments also returns the same capsule and budget. This prevents resetting a study merely by changing its request key. A corrected recipe is a separately identified study; it does not replace prior inputs, failures or exposure.

## Resource accounting and recovery

Reservation and start events commit atomically before child launch. Result retention, settlement and attempt closure commit together; stale or already settled attempts cannot publish again. Only one attempt may be outstanding in a study. Every attempt remains in the audit and consumes resources, while summary statistics use at most one completed result per fixed world.

The logical storage convention charges source/input retention, child materializations, retained output copies and a 1 MiB metadata allowance per attempt. The admission calculation covers all four logical copies of a generation/replay stream. Deduplication does not refund this declared charge. Parent-observed compute includes validation, generation, replay, collection and blob staging, but excludes the final settlement transaction and subsequent inspection. These are explicit accounting conventions, not hard OS disk, memory or CPU quotas.

Known use charges the measured amount. Incomplete file accounting or an unsettled attempt after writer loss charges at least the full original reservation. Observed excess is never truncated to the cap; an overrun stops further admission and suppresses candidate selection. Output-staging failure leaves its reservation outstanding.

Between settled worlds, the retained study can continue after registry restart or complete backup/restore. An abrupt writer loss during an outstanding attempt becomes terminal `ORPHAN_UNCERTAIN`: a writer lock or recovered event cannot prove the prior child has terminated. Automatic replacement work is blocked. Reliable OS containment/reclamation remains unimplemented.

## Interpretation

A fully evaluated undefined denominator is an information abstention and stays in the fixed denominator. A resource stop, invalid output, crash or failed replay is a technical failure, not a scientific negative. Failed attempts remain retained even when the same frozen world later succeeds. A model gap or exhausted technical failure keeps the study incomplete.

Only a completed whole grid may nominate the smallest **tested** target reaching the adopted point target of 80% detection at twice delta for every declared stress/sign. Selection does not assume monotonic power or stop at a favorable early crossing. Exact outward dyadic Clopper-Pearson intervals describe pointwise outer uncertainty. They are not simultaneous or selection-adjusted guarantees. Zero/boundary detection is reported separately from power at twice delta.

All outputs retain `n_min: null` and `scientific_readiness: false`. Model adequacy, coherent joint-family/return worlds, data and semantic acceptance, fresh 256-world calibration, and atomic allocation/freeze remain separate gates under [research-contract/1.0](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md). The [implementation design](../docs/reviews/implementation-2026-10-25/INFORMATION_STUDY_IMPLEMENTATION.md) records the original acceptance boundary.

## Verification scope

The later [calibration count assessment](CALIBRATION.md) supplies the separate adopted one-sided exact acceptance arithmetic. It does not convert these development worlds into fresh final-calibration evidence or replace their pointwise two-sided uncertainty reports.

The subsequent owned final-series runner reuses this lifecycle and the exact retained calculator source. It freezes separate protected draws only for the currently implemented single-claim scope and an already studied target. Key aliases, failed attempts and unknown usage preserve the original budget; complete calibration and scientific admission remain separate gates. Development summaries and their original default behavior remain unchanged.

New source versions use the [canonical byte draw sink](STATIONARY_BOOTSTRAP.md#reusing-canonical-draw-bytes) for the owned child stream. It reuses bytes already required by the replicate hash; retained case/draw bytes, all failed prefixes, numerical results and separate replay remain unchanged. Existing study inputs continue using their retained source version. Faster transport is not a new information target or permission to discard draws.

Sixty focused/existing regression tests and nine additional independent owner tests passed with unchanged source hashes. The authenticated HTTP probe completed three fixed worlds at 16 synthetic timestamps, generating and separately replaying 179,991 prescribed bootstrap draws in total. Settled-world restart and complete database/blob backup/restore preserved the study. This tiny engineering profile is not a reliable power estimate. [Verification](../docs/reviews/implementation-2026-10-25/study-verification.json) and [independent review](../docs/reviews/implementation-2026-10-25/study-review.json) retain exact outcomes, source hashes and limitations. The prior 405-test full regression applies to the preceding population checkpoint; it was not rerun in full for this study change.
