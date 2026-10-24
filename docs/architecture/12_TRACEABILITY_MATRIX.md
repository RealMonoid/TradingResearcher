# Traceability Matrix

Archived source references resolve through [SOURCE_REVIEW_INDEX.md](SOURCE_REVIEW_INDEX.md) and `sources/message_index.json`. SESSION-2026-10-22 is a later source recorded separately in D068 and the structured register. Tests below are specified future acceptance tests, not executed application tests. Implementation phases are proposals.

SESSION-2026-10-22-GENERATOR records the later economic clarification and specification authorization in D069-D070. [Document 13](13_GENERATOR_FEEDBACK_AND_EVALUATION.md#acceptance-specifications) supplies the binding contract and future TEST-28 through TEST-30 cases; its integration is not a runtime test result.

## Forward trace: problem to implementation evidence

| Problem | Requirement | Decisions | Components | Interfaces | Test | Phase |
|---|---|---|---|---|---|---|
| PROB-01 | REQ-001 | D001, D015 | CMP-02, CMP-03, CMP-04, CMP-06 | IF-03, IF-07 | TEST-01 | P2 |
| PROB-01 | REQ-002 | D002, D003, D055, D074 | CMP-02, CMP-03, CMP-04 | IF-03, IF-04 | TEST-02 | P1 |
| PROB-01 | REQ-003 | D004, D084 | CMP-03, CMP-04, CMP-08 | IF-04, IF-09 | TEST-03 | P1 |
| PROB-02 | REQ-004 | D005, D034, D061 | CMP-01, CMP-02, CMP-03, CMP-04, CMP-06, CMP-07 | IF-01, IF-02 | TEST-04 | P3 |
| PROB-03 | REQ-005 | D006, D024, D027, D033, D062, D075 | CMP-03, CMP-04, CMP-06, CMP-08, CMP-09 | IF-05, IF-07 | TEST-05 | P1/P4 |
| PROB-04 | REQ-006 | D007, D052 | CMP-01, CMP-03, CMP-04, CMP-05, CMP-06, CMP-11 | IF-06, IF-07, IF-13 | TEST-06 | P2 |
| PROB-04 | REQ-007 | D008, D043, D067, D071, D078, D085 | CMP-04, CMP-06, CMP-08, CMP-12 | IF-04, IF-12 | TEST-07 | P1 |
| PROB-04 | REQ-008 | D009, D056, D083 | CMP-03, CMP-07, CMP-08 | IF-08, IF-09 | TEST-08 | P1/P3 |
| PROB-05 | REQ-009 | D010, D017, D021, D048, D050, D066, D072 | CMP-03, CMP-05, CMP-06, CMP-08, CMP-09 | IF-10, IF-07 | TEST-09 | P6 |
| PROB-05 | REQ-010 | D011, D032, D036 | CMP-02, CMP-03, CMP-06 | IF-03, IF-07 | TEST-10 | P2/P6 |
| PROB-07 | REQ-011 | D012, D058 | CMP-01, CMP-03 | IF-01, IF-04 | TEST-11 | P2 |
| PROB-02 | REQ-012 | D013, D042, D053 | CMP-01, CMP-05, CMP-06 | IF-06, IF-07 | TEST-12 | P2 |
| PROB-02 | REQ-013 | D014 | CMP-01, CMP-02, CMP-07, CMP-08 | IF-01, IF-02, IF-08 | TEST-13 | P3 |
| PROB-02 | REQ-014 | D016, D029, D039, D054, D086 | CMP-01, CMP-02, CMP-03, CMP-06, CMP-07, CMP-11, CMP-12 | IF-02, IF-03, IF-08 | TEST-14; [agent inquiry cases](15_AGENT_INQUIRY_DISCIPLINE.md#acceptance-examples-for-test-14) | P3; repository review discipline now |
| PROB-07 | REQ-015 | D018, D076 | CMP-01, CMP-03, CMP-05 | IF-01, IF-06 | TEST-15 | P2/P5 |
| PROB-02 | REQ-016 | D019 | CMP-07, CMP-08, CMP-09 | IF-08 | TEST-16 | P3 |
| PROB-05 | REQ-017 | D020, D057, D064, D080 | CMP-06, CMP-08, CMP-09, CMP-10 | IF-11 | TEST-17 | P6 |
| PROB-06 | REQ-018 | D022, D041, D063, D077 | CMP-01, CMP-02, CMP-05, CMP-07, CMP-12 | IF-02, IF-06, IF-12 | TEST-18 | P2/P7 |
| PROB-03 | REQ-019 | D023, D082 | CMP-02, CMP-04, CMP-06 | IF-05 | TEST-19 | P4 |
| PROB-03 | REQ-020 | D025, D038, D049 | CMP-02, CMP-05, CMP-06, CMP-09 | IF-06, IF-07 | TEST-20 | P4 |
| PROB-04 | REQ-021 | D026, D040 | CMP-02, CMP-07, CMP-12 | IF-12 | TEST-21 | P3/P7 |
| PROB-06 | REQ-022 | D028, D059, D060, D073 | CMP-11, CMP-12 | IF-13 | TEST-22 | P5 |
| PROB-06 | REQ-023 | D030, D065, D079 | CMP-02, CMP-04, CMP-05, CMP-06, CMP-11, CMP-12 | IF-12, IF-13 | TEST-23 | P1/P7 |
| PROB-03 | REQ-024 | D031, D035, D047, D051 | CMP-02, CMP-04, CMP-05, CMP-06, CMP-09 | IF-05, IF-06, IF-07 | TEST-24 | P4 |
| PROB-05 | REQ-025 | D037 | CMP-08, CMP-09, CMP-10, CMP-11 | IF-11, IF-08 | TEST-25 | P6 |
| PROB-05 | REQ-026 | D044, D045, D046 | CMP-01, CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07 | IF-01, IF-06 | TEST-26 | P5 |
| PROB-08 | REQ-027 | D068, D013, D019, D025, D028, D036 | CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07, CMP-11, CMP-12 | IF-03, IF-06, IF-08, IF-13 | TEST-27 | P7; before framework success claim |
| PROB-02 | REQ-028 | D070, D014, D019, D026 | CMP-01, CMP-03, CMP-04, CMP-06, CMP-07, CMP-12 | IF-01, IF-02, IF-08, IF-12 | TEST-28 | Scoped slice; before feedback reuse |
| PROB-06 | REQ-029 | D069, D070, D025, D059, D068, D081 | CMP-02, CMP-06, CMP-09, CMP-11, CMP-12 | IF-05, IF-07, IF-12, IF-13 | TEST-29 | Pilot planning; before affected assessment |
| PROB-01 | REQ-030 | D070, D005, D016, D028 | CMP-01, CMP-02, CMP-03, CMP-07, CMP-11 | IF-02, IF-03, IF-08, IF-13 | TEST-30 | Scoped slice; before diagnostic claims |

## Reverse trace: every decision has a disposition

| Decision | Status | Source messages | Requirement | Implementation disposition |
|---|---|---|---|---|
| D001 | NON_NEGOTIABLE | M0057, M0059, M0107 | REQ-001 | Implement behavior subject to unresolved semantics and phase approval. |
| D002 | ACCEPTED | M0061, M0062, M0067, M0071, M0074 | REQ-002 | Implement behavior subject to unresolved semantics and phase approval. |
| D003 | ACCEPTED | M0067, M0068, M0071, M0088, M0090 | REQ-002 | Implement behavior subject to unresolved semantics and phase approval. |
| D004 | ACCEPTED | M0061, M0062, M0065, M0066, M0067, M0068 | REQ-003 | Implement behavior subject to unresolved semantics and phase approval. |
| D005 | ACCEPTED | M0063, M0064, M0068, M0071, M0110, M0111, M0112 | REQ-004 | Implement behavior subject to unresolved semantics and phase approval. |
| D006 | ACCEPTED | M0065, M0066, M0067, M0068, M0071, M0072 | REQ-005 | Implement behavior subject to unresolved semantics and phase approval. |
| D007 | ACCEPTED | M0069, M0070, M0071, M0072, M0288, M0289 | REQ-006 | Implement behavior subject to unresolved semantics and phase approval. |
| D008 | ACCEPTED | M0071, M0072, M0241, M0242, M0243 | REQ-007 | Implement behavior subject to unresolved semantics and phase approval. |
| D009 | ACCEPTED | M0085, M0086, M0089, M0090, M0091, M0092 | REQ-008 | Implement behavior subject to unresolved semantics and phase approval. |
| D010 | ACCEPTED | M0083, M0084, M0113, M0114, M0137, M0138, M0139, M0141 | REQ-009 | Implement behavior subject to unresolved semantics and phase approval. |
| D011 | ACCEPTED | M0093, M0094, M0095, M0096, M0111, M0112, M0193, M0194, M0195 | REQ-010 | Implement behavior subject to unresolved semantics and phase approval. |
| D012 | ACCEPTED | M0097, M0098 | REQ-011 | Implement behavior subject to unresolved semantics and phase approval. |
| D013 | ACCEPTED | M0101, M0102, M0105, M0106, M0153, M0154, M0155 | REQ-012 | Implement behavior subject to unresolved semantics and phase approval. |
| D014 | ACCEPTED | M0102, M0106, M0112, M0153, M0154, M0155, M0166, M0167 | REQ-013 | Implement behavior subject to unresolved semantics and phase approval. |
| D015 | REJECTED | M0107, M0108, M0190, M0191, M0220, M0221 | REQ-001 | Exclusion/precedent only; do not implement as current behavior. |
| D016 | ACCEPTED | M0109, M0110, M0111, M0112, M0119, M0121, M0122, M0129, M0130, M0223, M0224, M0225 | REQ-014 | Implement behavior subject to unresolved semantics and phase approval. |
| D017 | ACCEPTED | M0113, M0114 | REQ-009 | Implement behavior subject to unresolved semantics and phase approval. |
| D018 | ACCEPTED | M0115, M0116, M0161, M0162, M0163 | REQ-015 | Implement behavior subject to unresolved semantics and phase approval. |
| D019 | ACCEPTED | M0125, M0126, M0165, M0166, M0167, M0168 | REQ-016 | Implement behavior subject to unresolved semantics and phase approval. |
| D020 | ACCEPTED | M0137, M0138, M0141, M0142, M0145, M0146, M0147, M0148, M0185, M0186 | REQ-017 | Implement behavior subject to unresolved semantics and phase approval. |
| D021 | ACCEPTED | M0141, M0142, M0143, M0144, M0185, M0186 | REQ-009 | Implement behavior subject to unresolved semantics and phase approval. |
| D022 | CONDITIONALLY_ACCEPTED | M0139, M0140, M0229, M0231, M0232, M0233, M0235, M0236, M0237 | REQ-018 | Implement behavior subject to unresolved semantics and phase approval. |
| D023 | ACCEPTED | M0153, M0154, M0155, M0156 | REQ-019 | Implement behavior subject to unresolved semantics and phase approval. |
| D024 | ACCEPTED | M0157, M0158, M0159, M0160 | REQ-005 | Implement behavior subject to unresolved semantics and phase approval. |
| D025 | ACCEPTED | M0161, M0162, M0163, M0164 | REQ-020 | Implement behavior subject to unresolved semantics and phase approval. |
| D026 | ACCEPTED | M0169, M0170, M0171, M0172, M0173, M0174 | REQ-021 | Implement behavior subject to unresolved semantics and phase approval. |
| D027 | ACCEPTED | M0175, M0176, M0177, M0178 | REQ-005 | Implement behavior subject to unresolved semantics and phase approval. |
| D028 | ACCEPTED | M0179, M0180, M0185, M0186 | REQ-022 | Implement behavior subject to unresolved semantics and phase approval. |
| D029 | ACCEPTED | M0181, M0182, M0183, M0184 | REQ-014 | Implement behavior subject to unresolved semantics and phase approval. |
| D030 | ACCEPTED | M0187, M0188, M0223, M0224, M0225 | REQ-023 | Implement behavior subject to unresolved semantics and phase approval. |
| D031 | ACCEPTED | M0189, M0190, M0191, M0192 | REQ-024 | Implement behavior subject to unresolved semantics and phase approval. |
| D032 | ACCEPTED | M0193, M0194, M0195, M0196 | REQ-010 | Implement behavior subject to unresolved semantics and phase approval. |
| D033 | ACCEPTED | M0197, M0198, M0199, M0200 | REQ-005 | Implement behavior subject to unresolved semantics and phase approval. |
| D034 | ACCEPTED | M0201, M0202, M0203, M0204 | REQ-004 | Implement behavior subject to unresolved semantics and phase approval. |
| D035 | ACCEPTED | M0205, M0206, M0207, M0208 | REQ-024 | Implement behavior subject to unresolved semantics and phase approval. |
| D036 | ACCEPTED | M0209, M0210, M0211, M0212 | REQ-010 | Implement behavior subject to unresolved semantics and phase approval. |
| D037 | ACCEPTED | M0213, M0214, M0215, M0216, M0217, M0218 | REQ-025 | Implement behavior subject to unresolved semantics and phase approval. |
| D038 | ACCEPTED | M0219, M0220, M0221, M0222 | REQ-020 | Implement behavior subject to unresolved semantics and phase approval. |
| D039 | ACCEPTED | M0223, M0224, M0225, M0226 | REQ-014 | Implement behavior subject to unresolved semantics and phase approval. |
| D040 | CONDITIONALLY_ACCEPTED | M0227, M0228, M0229, M0230 | REQ-021 | Implement behavior subject to unresolved semantics and phase approval. |
| D041 | CONDITIONALLY_ACCEPTED | M0231, M0232, M0233, M0234 | REQ-018 | Implement behavior subject to unresolved semantics and phase approval. |
| D042 | CONDITIONALLY_ACCEPTED | M0235, M0236, M0237, M0238 | REQ-012 | Implement behavior subject to unresolved semantics and phase approval. |
| D043 | ACCEPTED | M0239-A, M0239-B, M0240 | REQ-007 | Implement behavior subject to unresolved semantics and phase approval. |
| D044 | ACCEPTED | M0251, M0255, M0256, M0257, M0258 | REQ-026 | Implement behavior subject to unresolved semantics and phase approval. |
| D045 | ACCEPTED | M0259, M0260, M0261, M0262, M0263 | REQ-026 | Implement behavior subject to unresolved semantics and phase approval. |
| D046 | ACCEPTED | M0261, M0262, M0263, M0264 | REQ-026 | Implement behavior subject to unresolved semantics and phase approval. |
| D047 | ACCEPTED | M0265, M0266, M0267, M0268 | REQ-024 | Implement behavior subject to unresolved semantics and phase approval. |
| D048 | ACCEPTED | M0271, M0272, M0273, M0274 | REQ-009 | Implement behavior subject to unresolved semantics and phase approval. |
| D049 | ACCEPTED | M0275, M0276, M0277, M0278 | REQ-020 | Implement behavior subject to unresolved semantics and phase approval. |
| D050 | CONDITIONALLY_ACCEPTED | M0279, M0280, M0281, M0282 | REQ-009 | Implement behavior subject to unresolved semantics and phase approval. |
| D051 | ACCEPTED | M0283, M0284, M0285, M0286 | REQ-024 | Implement behavior subject to unresolved semantics and phase approval. |
| D052 | ACCEPTED | M0287, M0288, M0289, M0290 | REQ-006 | Implement behavior subject to unresolved semantics and phase approval. |
| D053 | SUPERSEDED | M0062, M0068, M0072, M0101, M0102, M0153, M0154, M0155 | REQ-012 | Exclusion/precedent only; do not implement as current behavior. |
| D054 | SUPERSEDED | M0061, M0062, M0110, M0112, M0181, M0182, M0183 | REQ-014 | Exclusion/precedent only; do not implement as current behavior. |
| D055 | SUPERSEDED | M0058, M0065, M0066, M0067, M0068, M0074 | REQ-002 | Exclusion/precedent only; do not implement as current behavior. |
| D056 | SUPERSEDED | M0086, M0089, M0090, M0092 | REQ-008 | Exclusion/precedent only; do not implement as current behavior. |
| D057 | SUPERSEDED | M0145, M0146, M0147, M0148 | REQ-017 | Exclusion/precedent only; do not implement as current behavior. |
| D058 | SUPERSEDED | M0050, M0072, M0097, M0098 | REQ-011 | Exclusion/precedent only; do not implement as current behavior. |
| D059 | DEFERRED | M0016, M0017, M0018, M0020, M0022, M0044, M0107, M0108 | REQ-022 | Keep open or deferred; no implied approval. |
| D060 | DEFERRED | M0041, M0042, M0043, M0044 | REQ-022 | Keep open or deferred; no implied approval. |
| D061 | DEFERRED | M0064, M0068, M0072, M0110, M0186, M0246, M0247 | REQ-004 | Keep open or deferred; no implied approval. |
| D062 | DEFERRED | M0068, M0072, M0186, M0246, M0247 | REQ-005 | Keep open or deferred; no implied approval. |
| D063 | DEFERRED | M0186, M0232, M0246, M0247 | REQ-018 | Keep open or deferred; no implied approval. |
| D064 | DEFERRED | M0146, M0148, M0186 | REQ-017 | Keep open or deferred; no implied approval. |
| D065 | PROPOSED_ONLY | M0245, M0246, M0247 | REQ-023 | Keep open or deferred; no implied approval. |
| D066 | AMBIGUOUS | M0143, M0144 | REQ-009 | Keep open or deferred; no implied approval. |
| D067 | OPEN | M0071, M0072, M0101, M0102, M0138, M0146, M0148, M0241, M0242, M0243 | REQ-007 | Keep open or deferred; no implied approval. |
| D068 | ACCEPTED | SESSION-2026-10-22 | REQ-027 | Accepted acceleration objective; scoped targets now D081; named comparison and actual measurement remain prerequisites. |
| D069 | ACCEPTED | SESSION-2026-10-22-GENERATOR | REQ-029 | Absolute profitable usefulness; no advance success or competitor-superiority prerequisite. |
| D070 | ACCEPTED | SESSION-2026-10-22-GENERATOR | REQ-028/029/030 | Binding feedback, assessment and discovery diagnostic contract in document 13; runtime unimplemented. |
| D071 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-007 | OPEN-01: [contract section 1](14_RETAIL_RESEARCH_CONTRACT.md#1-open-01-versioned-lifecycle-and-evidence-axes); specification adopted, runtime acceptance unexecuted. |
| D072 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-009 | OPEN-02: [contract section 2](14_RETAIL_RESEARCH_CONTRACT.md#2-open-02-subset-membership-is-not-evidence-transport); specification adopted, runtime acceptance unexecuted. |
| D073 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-022 | OPEN-03: [contract section 3](14_RETAIL_RESEARCH_CONTRACT.md#3-open-03-descriptive-cohorts-no-invented-truth-priors); specification adopted, runtime acceptance unexecuted. |
| D074 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-002 | OPEN-04: [contract section 4](14_RETAIL_RESEARCH_CONTRACT.md#4-open-04-typed-expressions-and-explicit-estimands); specification adopted, runtime acceptance unexecuted. |
| D075 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-005 | OPEN-05: [contract section 5](14_RETAIL_RESEARCH_CONTRACT.md#5-open-05-test-policy-useful-negatives-and-information-limits); specification adopted, runtime acceptance unexecuted. |
| D076 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-015 | OPEN-06: [contract section 6](14_RETAIL_RESEARCH_CONTRACT.md#6-open-06-data-and-execution-authority); specification adopted, runtime acceptance unexecuted. |
| D077 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-018 | OPEN-07: [contract section 7](14_RETAIL_RESEARCH_CONTRACT.md#7-open-07-runtime-choice-and-isolation); specification adopted, runtime acceptance unexecuted. |
| D078 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-007 | OPEN-08: [contract section 8](14_RETAIL_RESEARCH_CONTRACT.md#8-open-08-persistence-serialization-and-recovery); specification adopted, runtime acceptance unexecuted. |
| D079 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-023 | OPEN-09: [contract section 9](14_RETAIL_RESEARCH_CONTRACT.md#9-open-09-perspectives-models-and-compute-budget); specification adopted, runtime acceptance unexecuted. |
| D080 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-017 | OPEN-10: [contract section 10](14_RETAIL_RESEARCH_CONTRACT.md#10-open-10-explicit-research-only-authority); specification adopted, runtime acceptance unexecuted. |
| D081 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-029 | OPEN-11: [contract section 11](14_RETAIL_RESEARCH_CONTRACT.md#11-open-11-finite-success-and-continuation-criteria); specification adopted, runtime acceptance unexecuted. |
| D082 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-019 | OPEN-12: [contract section 12](14_RETAIL_RESEARCH_CONTRACT.md#12-open-12-confirmation-allocation-and-feedback-release); specification adopted, runtime acceptance unexecuted. |
| D083 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-008 | OPEN-13: [contract section 13](14_RETAIL_RESEARCH_CONTRACT.md#13-open-13-dependency-effects-and-applicability); specification adopted, runtime acceptance unexecuted. |
| D084 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-003 | OPEN-14: [contract section 14](14_RETAIL_RESEARCH_CONTRACT.md#14-open-14-automatic-certification-within-an-approved-envelope); specification adopted, runtime acceptance unexecuted. |
| D085 | ACCEPTED | SESSION-2026-10-23-CLOSURE | REQ-007 | OPEN-15: [contract section 15](14_RETAIL_RESEARCH_CONTRACT.md#15-open-15-source-gap-policy); specification adopted, runtime acceptance unexecuted. |
| D086 | ACCEPTED | SESSION-2026-10-24-INQUIRY | REQ-014 | Apply agent-inquiry/1.0 in repository work and specified future agents; TEST-14 extensions unexecuted. |

## Coverage and orphan rules

Every requirement must map to at least one source-backed decision, component, interface, acceptance test and phase. Every rejection must reference source messages and at least one decision. Every important proposed departure must reference an open decision. A referenced ID existing does not establish that its scientific interpretation is correct; semantic review remains necessary.

Source gaps affect confidence rather than being filled by generated requirements: SRC-001 and SRC-003 through SRC-005 particularly affect early chart/project context; SRC-002 affects the missing pipeline image, but D037 has independent textual user approval; SRC-006 through SRC-008 limit completeness of the overall source record.

## Selection and exposure acceptance cases

October 23 elaboration of existing requirements and tests, grounded in D006/D014/D025/D031/D035/D038/D044-D051/D070. These are **future behavioral specifications, not executed tests**. They do not create new TEST IDs, scientific thresholds or an approved method. Runtime fixtures must instantiate the relevant resolved protocol; documentation checks can only verify these references and distinctions.

| Existing tests / requirements | Triggering case | Required observable behavior under the existing contract |
|---|---|---|
| TEST-03/05/24; REQ-003/005/024 | Select a column using all evaluation outcomes, then fit coefficients inside outer folds; or fit a normalizer on unavailable data | The claimed independent procedure assessment fails its exposure/fit-boundary checks. Retain the exploratory candidate; a different admissible candidate assessment remains possible. A correctly computed feature does not certify its selected relationship. |
| TEST-03/26; REQ-003/026 | Join final MAE/MFE or end-of-day volume into an earlier decision, or retrieve cached values from later fitted state | Reject the inadmissible input/version. The same completed-path statistic remains permitted as a labeled retrospective diagnostic; an evolving value is truncated at its actual decision time. |
| TEST-13/28/29; REQ-013/028/029 | Release only a rank or pass/fail result, use it through a heuristic to revise the candidate, then call the same evidence independent after a new chat or rollback | The descendant retains the released result's ancestry and fails that freshness claim. Preserve the original valid frozen result; do not erase it or label feedback use itself a technical error. |
| TEST-05/19; REQ-005/019 | Submit several predeclared candidates sharing outcomes; contrast with outcome-guided additions after release | The resolved joint dependence/error/allocation policy governs the predeclared batch. Changed candidates inherit selection exposure. Missing policy blocks confirmation, not retention of ideas. Do not impose one dataset per idea. |
| TEST-05/29; REQ-005/029 | Stop a fixed-horizon trial at the first favorable interim score; contrast with a valid pre-frozen sequential policy | The opportunistic result cannot become final support. The applicable sequential procedure can decide at its permitted boundary. Low information, non-significance and budget exhaustion do not silently become scientific negatives. |
| TEST-20/24/29; REQ-020/024/029 | Compare a selected real winner against one unselected null candidate, or tune on calibration outcomes and report them as untouched final assessment | The declared process-calibration claim fails the selection-symmetry or assessment-separation check. A fixed-family analysis remains possible only under its narrower declared claim and assumptions. Retain tuning, failures and uncertainty. |
| TEST-09/26; REQ-009/026 | Remove trade A from a saved table when its absence would permit trade B or change available cash, exits or costs | The subset statistic is labeled as such. A policy-performance claim requires faithful re-execution of affected interactions; an unsupported backend returns a capability gap. Independent path/accounting fixtures verify any implemented result. |
| TEST-13/19/29; REQ-013/019/029 | A scoped claim is frozen before appropriate forward outcomes exist; a later candidate uses those released outcomes | Forward origin is retained for the first trial, with its dependence/multiplicity/stopping checks. The descendant inherits exposure; a new date label or model name cannot reset it. |

The [Scientific Evaluation](07_SCIENTIFIC_EVALUATION.md#overfitting-controls-across-the-research-process) owns the interpretation and method limits; the [Blueprint](09_IMPLEMENTATION_BLUEPRINT.md#selection-and-assessment-through-existing-interfaces) maps the same cases to IF-02 through IF-13. These earlier cases do not themselves select policy. D071-D085 and document 14 now resolve the scoped semantics and numerical policies; the cases must be instantiated against that version.

## Present verification versus future verification

DOCUMENTATION_VERIFICATION.json records checks actually executed on the reconstructed documents and immutable archive. TEST-01 through TEST-30 are not executed. D068-D070 and REQ-027 through REQ-030 were added after that report; it does not validate these later revisions. The current documentation checker checks links, preservation and traceability, not application behavior. No application, backtest, live data, runtime, schema compiler or statistical calibration was implemented or tested.


## Approved closure acceptance mapping

SESSION-2026-10-23-CLOSURE adopts [research-contract/1.0](14_RETAIL_RESEARCH_CONTRACT.md). Each section's acceptance cases are binding future specifications under the existing TEST IDs, not tests executed by documentation validation.

| Contract section / decision | Existing acceptance tests | Required negative or boundary case |
|---|---|---|
| 1 / D071 | TEST-07, TEST-12, TEST-17 | historical readiness without elapsed calendar time; invalid run with no scientific verdict; legacy supported record with unknown origin remains unknown; retry cannot add replication. |
| 2 / D072 | TEST-09 | the counterexample rejects inherited subgroup support while retaining the assumption and permitting a separate policy trial. |
| 3 / D073 | TEST-22, TEST-29 | the 8/200 example produces a descriptive rate and no truth prior; immature cohorts retain pending cases. |
| 4 / D074 | TEST-02, TEST-03, TEST-11, TEST-26 | independently calculated binary and continuous fixtures for all five forms, Boolean unknown cases, unit mismatches, future access, interactions without a main effect, and a path-dependent policy gap. |
| 5 / D075 | TEST-05, TEST-19, TEST-20, TEST-24 | interval boundary fixtures; overlapping baseline fixture; dependent null calibration; insufficient information; no early success; no target switching. |
| 6 / D076 | TEST-11, TEST-12, TEST-15, TEST-29 | revisions and mixed timestamp units fail loudly; next-bar timing and shared cash have independent fixtures; missing fee/rights/PIT information remains explicit. No dataset was acquired by this proposal. |
| 7 / D077 | TEST-04, TEST-13, TEST-18, TEST-21 | denied holdout requests through files, tools and returned metadata; no automatic memory mutation within an epoch; exact adapter request/result provenance. Dependency versions remain acquisition-time inputs, not invented compatibility claims. |
| 8 / D078 | TEST-05, TEST-06, TEST-07, TEST-08 | crash before/after commit, duplicate delivery, concurrent freeze conflict, invalid decimal/duplicate JSON keys, corrupted blob, backup/restore and projection replay. |
| 9 / D079 | TEST-04, TEST-14, TEST-23, TEST-30 | same snapshot, inaccessible peer scratch, complete call costs, retained overflow ideas and budget exhaustion without scientific rejection. |
| 10 / D080 | TEST-17, TEST-25 | no scientific result can emit or authorize a trade; simulated losses cannot mutate evidence. Closing the research-mode decision does not close future live-risk choices. |
| 11 / D081 | TEST-20, TEST-22, TEST-23, TEST-27, TEST-29 | separate gate reports; narrow calibration cannot claim P4; failed/pending cohorts retained; no success reward for producing easy rejections. |
| 12 / D082 | TEST-05, TEST-13, TEST-19, TEST-24, TEST-28 | late candidate denied admission; shared predeclared batch allowed; pass/fail-informed descendant inherits exposure; unused ideas remain retrievable. |
| 13 / D083 | TEST-08, TEST-17, TEST-25 | hard invalidation propagates; genealogy does not; changed costs trigger review without erasing scientific evidence. |
| 14 / D084 | TEST-03, TEST-06, TEST-07, TEST-21 | existing-semantic implementation can pass without a human click; changed expected values or new temporal meaning cannot; unusual but valid ideas are retained. |
| 15 / D085 | TEST-07 | immutable archive hashes match; later recovery can be attached without overwriting prior bytes; confidence qualifications remain visible. |
