# Traceability Matrix

Archived source references resolve through [SOURCE_REVIEW_INDEX.md](SOURCE_REVIEW_INDEX.md) and `sources/message_index.json`. SESSION-2026-10-22 is a later source recorded separately in D068 and the structured register. Tests below are specified future acceptance tests, not executed application tests. Implementation phases are proposals.

SESSION-2026-10-22-GENERATOR records the later economic clarification and specification authorization in D069-D070. [Document 13](13_GENERATOR_FEEDBACK_AND_EVALUATION.md#acceptance-specifications) supplies the binding contract and future TEST-28 through TEST-30 cases; its integration is not a runtime test result.

SESSION-2026-10-24-TEMPORAL-DIAGNOSTIC records the later approval of D087. [Document 16](16_TEMPORAL_DIAGNOSTIC_INVOCATION.md#future-acceptance-cases) extends future TEST-17/25 for automatic invocation, without claiming that a monitoring runtime or quantitative method has been tested.

SESSION-2026-10-24-MONITORING-VISIBILITY records D088's later operational reporting instruction and clarification. [Document 17](17_MONITORING_VISIBILITY_AND_REPORTING.md#future-acceptance-cases) extends future TEST-17/22/25 for background authorized work, weekly reports and actionable notices; those complete behaviors are not implemented or tested. The later local coordination slice supplies generic triggers only; its bounded executable coverage is recorded below.

## Forward trace: problem to implementation evidence

| Problem | Requirement | Decisions | Components | Interfaces | Test | Phase |
|---|---|---|---|---|---|---|
| PROB-01 | REQ-001 | D001, D015 | CMP-02, CMP-03, CMP-04, CMP-06 | IF-03, IF-07 | TEST-01 | P2 |
| PROB-01 | REQ-002 | D002, D003, D055, D074, D089, D091 | CMP-02, CMP-03, CMP-04 | IF-03, IF-04 | TEST-02; [bounded math cases](18_BOUNDED_MATH_PRIMITIVES.md#acceptance-and-rollback) | P1 |
| PROB-01 | REQ-003 | D004, D084, D094, D097 | CMP-03, CMP-04, CMP-08 | IF-04, IF-09 | TEST-03; [paired acceptance](23_PAIRED_DEVELOPMENT.md#integration-exact-gates-and-stopping-rules) | P1 |
| PROB-02 | REQ-004 | D005, D034, D061, D092 | CMP-01, CMP-02, CMP-03, CMP-04, CMP-06, CMP-07 | IF-01, IF-02 | TEST-04; [review continuation](21_INDEPENDENT_REVIEW_CONTINUATION.md#validation-and-rollback) | P3 |
| PROB-03 | REQ-005 | D006, D024, D027, D033, D062, D075 | CMP-03, CMP-04, CMP-06, CMP-08, CMP-09 | IF-05, IF-07 | TEST-05 | P1/P4 |
| PROB-04 | REQ-006 | D007, D052 | CMP-01, CMP-03, CMP-04, CMP-05, CMP-06, CMP-11 | IF-06, IF-07, IF-13 | TEST-06 | P2 |
| PROB-04 | REQ-007 | D008, D043, D067, D071, D078, D085 | CMP-04, CMP-06, CMP-08, CMP-12 | IF-04, IF-12 | TEST-07 | P1 |
| PROB-04 | REQ-008 | D009, D056, D083, D087 | CMP-03, CMP-07, CMP-08 | IF-08, IF-09, IF-11 | TEST-08 | P1/P3/P6 |
| PROB-05 | REQ-009 | D010, D017, D021, D048, D050, D066, D072 | CMP-03, CMP-05, CMP-06, CMP-08, CMP-09 | IF-10, IF-07 | TEST-09 | P6 |
| PROB-05 | REQ-010 | D011, D032, D036 | CMP-02, CMP-03, CMP-06 | IF-03, IF-07 | TEST-10 | P2/P6 |
| PROB-07 | REQ-011 | D012, D058 | CMP-01, CMP-03 | IF-01, IF-04 | TEST-11 | P2 |
| PROB-02 | REQ-012 | D013, D042, D053 | CMP-01, CMP-05, CMP-06 | IF-06, IF-07 | TEST-12 | P2 |
| PROB-02 | REQ-013 | D014 | CMP-01, CMP-02, CMP-07, CMP-08 | IF-01, IF-02, IF-08 | TEST-13 | P3 |
| PROB-02 | REQ-014 | D016, D029, D039, D054, D086, D095, D096 | CMP-01, CMP-02, CMP-03, CMP-06, CMP-07, CMP-11, CMP-12 | IF-02, IF-03, IF-08 | TEST-14; [agent inquiry cases](15_AGENT_INQUIRY_DISCIPLINE.md#acceptance-examples-for-test-14) | P3; repository review discipline now |
| PROB-07 | REQ-015 | D018, D076 | CMP-01, CMP-03, CMP-05 | IF-01, IF-06 | TEST-15 | P2/P5 |
| PROB-02 | REQ-016 | D019 | CMP-07, CMP-08, CMP-09 | IF-08 | TEST-16 | P3 |
| PROB-05 | REQ-017 | D020, D057, D064, D080, D087, D088 | CMP-01, CMP-06, CMP-07, CMP-08, CMP-09, CMP-10, CMP-11 | IF-11 | TEST-17; [D087 invocation cases](16_TEMPORAL_DIAGNOSTIC_INVOCATION.md#future-acceptance-cases); [D088 reporting cases](17_MONITORING_VISIBILITY_AND_REPORTING.md#future-acceptance-cases) | P6 |
| PROB-06 | REQ-018 | D022, D041, D063, D077, D098 | CMP-01, CMP-02, CMP-05, CMP-07, CMP-12 | IF-02, IF-06, IF-12 | TEST-18 | P2/P7 |
| PROB-03 | REQ-019 | D023, D082, D099 | CMP-02, CMP-04, CMP-06 | IF-05 | TEST-19; [outcome reservation cases](28_OUTCOME_RESERVATION.md#acceptance-versioning-and-rollback) | P4 |
| PROB-03 | REQ-020 | D025, D038, D049 | CMP-02, CMP-05, CMP-06, CMP-09 | IF-06, IF-07 | TEST-20 | P4 |
| PROB-04 | REQ-021 | D026, D040 | CMP-02, CMP-07, CMP-12 | IF-12 | TEST-21 | P3/P7 |
| PROB-06 | REQ-022 | D028, D059, D060, D073, D088 | CMP-11, CMP-12 | IF-13 | TEST-22; [D088 reporting cases](17_MONITORING_VISIBILITY_AND_REPORTING.md#future-acceptance-cases) | P5/P6 |
| PROB-06 | REQ-023 | D030, D065, D079, D090, D093 | CMP-02, CMP-04, CMP-05, CMP-06, CMP-11, CMP-12 | IF-12, IF-13 | TEST-23; [complete-feedback exception](22_COMPLETE_FEEDBACK_RESEARCH_EPOCH.md#verification-and-rollback) | P1/P7 |
| PROB-03 | REQ-024 | D031, D035, D047, D051 | CMP-02, CMP-04, CMP-05, CMP-06, CMP-09 | IF-05, IF-06, IF-07 | TEST-24 | P4 |
| PROB-05 | REQ-025 | D037, D087, D088 | CMP-01, CMP-06, CMP-07, CMP-08, CMP-09, CMP-10, CMP-11, CMP-12 | IF-11, IF-08, IF-13 | TEST-25; [D087 invocation cases](16_TEMPORAL_DIAGNOSTIC_INVOCATION.md#future-acceptance-cases); [D088 reporting cases](17_MONITORING_VISIBILITY_AND_REPORTING.md#future-acceptance-cases) | P6 |
| PROB-05 | REQ-026 | D044, D045, D046 | CMP-01, CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07 | IF-01, IF-06 | TEST-26 | P5 |
| PROB-08 | REQ-027 | D068, D013, D019, D025, D028, D036 | CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07, CMP-11, CMP-12 | IF-03, IF-06, IF-08, IF-13 | TEST-27 | P7; before framework success claim |
| PROB-02 | REQ-028 | D070, D014, D019, D026, D096 | CMP-01, CMP-03, CMP-04, CMP-06, CMP-07, CMP-12 | IF-01, IF-02, IF-08, IF-12 | TEST-28 | Scoped slice; before feedback reuse |
| PROB-06 | REQ-029 | D069, D070, D025, D059, D068, D081, D096 | CMP-02, CMP-06, CMP-09, CMP-11, CMP-12 | IF-05, IF-07, IF-12, IF-13 | TEST-29 | Pilot planning; before affected assessment |
| PROB-01 | REQ-030 | D070, D005, D016, D028, D096 | CMP-01, CMP-02, CMP-03, CMP-07, CMP-11 | IF-02, IF-03, IF-08, IF-13 | TEST-30 | Scoped slice; before diagnostic claims |

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
| D070 | ACCEPTED | SESSION-2026-10-22-GENERATOR | REQ-028/029/030 | Binding contract in document 13; scoped closed development feedback is implemented and verified below. Scientific assessment release, measured improvement and full discovery diagnostics remain incomplete. |
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
| D087 | ACCEPTED | SESSION-2026-10-24-TEMPORAL-DIAGNOSTIC | REQ-017/025 | Apply [temporal-diagnostic-invocation/1.0](16_TEMPORAL_DIAGNOSTIC_INVOCATION.md): due eligible batches and intended use invoke bound-plan checks automatically; TEST-17/25 extensions unexecuted. |
| D088 | ACCEPTED | SESSION-2026-10-24-MONITORING-VISIBILITY | REQ-017/022/025 | Apply [monitoring-visibility/1.0](17_MONITORING_VISIBILITY_AND_REPORTING.md): authorized work starts when ready, pending work persists, weekly reports and actionable notices are delivered; TEST-17/22/25 extensions unexecuted. |
| D089 | ACCEPTED | SESSION-2026-10-29-BOUNDED-MATH | REQ-002/003/005/011/026 | Optional [bounded-math/1.0](18_BOUNDED_MATH_PRIMITIVES.md) specifies median/log outcomes and outward bounds. Approval is not certification or completed research execution. |
| D090 | ACCEPTED | SESSION-2026-10-29-FEEDBACK-BUDGET | REQ-004/014/022/023/030 | One-use [resource overlay](19_RESEARCH_EPOCH_FEEDBACK_BUDGET.md); full inputs/review retained, ordinary budgets and scientific gates unchanged. |
| D091 | ACCEPTED | SESSION-2026-10-29-BOUNDED-MATH-REUSE | REQ-002/003/004/005/011/014/022/023/026/030 | Scoped [primitive reuse](20_BOUNDED_MATH_REUSE.md) and one retained-BTC continuation; unchanged mathematical meanings and per-hypothesis gates. |
| D092 | ACCEPTED | SESSION-2026-10-29-INDEPENDENT-BTC-REVIEW | REQ-004/014/022/023 | One exact [independent review continuation](21_INDEPENDENT_REVIEW_CONTINUATION.md), preserving original consumption, actual epoch identities and legacy policies. |
| D093 | ACCEPTED | SESSION-2026-10-30-COMPLETE-FEEDBACK-BUDGET | REQ-004/014/022/023/030 | One [complete-feedback epoch](22_COMPLETE_FEEDBACK_RESEARCH_EPOCH.md) with fixed six-slot resources, unchanged full inputs and independent review; no retry or successor. |

## Coverage and orphan rules

D099 adopts [outcome-reservation/1.0](28_OUTCOME_RESERVATION.md) for the scoped
IF-05/REQ-005/007/013/019/024/028 reservation boundary, extending existing
TEST-05/13/19/24/28 with stable aliases/revisions, potential grids, separate
dependence/exposure review, profile inputs, atomic denial/recovery and legacy
UNKNOWN. These are adoption requirements, not executed implementation coverage.

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
| TEST-09/24; REQ-009/024 | A frozen stock-ranking policy has positive broad-universe RankIC, but outcomes near its actual selection cutoff or its net policy result are poor; after assessment, a different cutoff is proposed | Report the broad diagnostic and the outcomes in the policy's selected decision region with the applicable eligibility, exposure and execution assumptions. Do not infer policy value from broad RankIC. A result-driven cutoff change is a new exposed policy selection requiring its own trial and, where paths interact, resimulation. Do not require monotonic quantiles for unrelated claim types. |
| TEST-09/26; REQ-009/026 | Remove trade A from a saved table when its absence would permit trade B or change available cash, exits or costs | The subset statistic is labeled as such. A policy-performance claim requires faithful re-execution of affected interactions; an unsupported backend returns a capability gap. Independent path/accounting fixtures verify any implemented result. |
| TEST-13/19/29; REQ-013/019/029 | A scoped claim is frozen before appropriate forward outcomes exist; a later candidate uses those released outcomes | Forward origin is retained for the first trial, with its dependence/multiplicity/stopping checks. The descendant inherits exposure; a new date label or model name cannot reset it. |

The stock-ranking decision-region case is motivated by the observed gap between broad ranking skill and selected-portfolio outcomes in [Quant-Arena](https://arxiv.org/html/2610.30113v1#S3.SS3); it illustrates existing D047/D048 and REQ-009/024 rather than adopting its scoring rule or market conclusions. The [Scientific Evaluation](07_SCIENTIFIC_EVALUATION.md#overfitting-controls-across-the-research-process) owns the interpretation and method limits; the [Blueprint](09_IMPLEMENTATION_BLUEPRINT.md#selection-and-assessment-through-existing-interfaces) maps the same cases to IF-02 through IF-13. These earlier cases do not themselves select policy. D071-D085 and document 14 now resolve the scoped semantics and numerical policies; the cases must be instantiated against that version.

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

The later D087 [invocation cases](16_TEMPORAL_DIAGNOSTIC_INVOCATION.md#future-acceptance-cases) extend TEST-17/25: eligible completed-outcome events trigger a due check, duplicate/corrected batches retain identity, intended use checks freshness, and missing information remains visible without altering evidence or authorizing action. Method calibration and runtime behavior remain unverified.

The later D088 [reporting cases](17_MONITORING_VISIBILITY_AND_REPORTING.md#future-acceptance-cases) extend TEST-17/22/25: an authorized comparison starts when ready, a weekly tick reports even without data, actionable events prompt once, and delivery failures persist. A report never advances a scientific checkpoint or activates a method. Scheduling, delivery and user benefit remain unverified.

## Local coordination implementation evidence

`SESSION-2026-10-24-LOCAL-COORDINATION` authorizes the runnable [local controller](../../trading_researcher/README.md). [Current verification](../reviews/LOCAL_COORDINATION_VERIFICATION_2026-10-24.json) records exact executed commands and file hashes. No full TEST-01 through TEST-30 completion is asserted by the following partial mapping.

| Requirement / future acceptance family | Executed infrastructure coverage | Still outside this coverage |
|---|---|---|
| REQ-004/018; TEST-04/18 | [Broker tests](../../tests/test_coordination.py) deny forged identity, stale attempt writes, late context additions and unauthorized artifact/status access; [HTTP tests](../../tests/test_local_runtime.py) exercise the real capability boundary | PIT market-data validation, provider isolation, arbitrary shell access, complete adapter provenance |
| REQ-007; D078 | Exclusive writer, idempotent job keys, retry history, SQLite integrity, real process-crash rollback, preserved commits and restored backup | Scientific FrozenManifest/TrialRecord closure, external blob manifest/quarantine, migration, power failure |
| REQ-013/016; TEST-13/16 | Descendants retain all supplied context ancestry; incomplete operational batches cannot release; later-epoch access is explicit | Full four-memory authority, scientific allocation/dependence and all external/context exposure |
| REQ-013/028; TEST-13/28 | [Development feedback checks](../reviews/implementation-2026-10-25/development-feedback-verification-2026-10-29.json) preserve both ideas and every closed-cohort attempt/gap, atomically publish typed observation/interpretation, deny early or revoked use/new dispatch, and restore the actual complete backup | Scientific/assessment batch release, Market Model authority, actual downstream model improvement and economic usefulness |
| REQ-013/014/023/028; TEST-13/28 | [Feedback reference-paging checks](../reviews/implementation-2026-10-25/feedback-context-verification-2026-10-29.json) retain all idea/gap bodies and attempts, authenticate exact bounded pages, reconstruct complete original envelopes, preserve legacy views and account for unchanged budgets | Model-quality equivalence, complete-path admission, scientific evidence and approval of any larger epoch budget |
| REQ-006/007/018; TEST-06/07/18 | Trusted structural, source-copy and decimal/rational checks reject invalid output; negative source records can complete a technical job without evidence authority | LLM factuality generally, source truth, hypothesis evaluation, statistical calibration |
| REQ-023; TEST-23 | Attempt/deadline bounds, blocked handoff, bounded trigger occurrences, crash catch-up, duplicate events and paginated retained history | Model token/cost accounting, material-improvement iteration policy, measured research acceleration |
| D087/D088 prerequisites | Real HTTP worker dispatch from a generic due timer; durable time/event scheduling and idempotent occurrence identity | Eligible completed-outcome producer, bound-plan readiness/freshness, quantitative diagnostics, weekly local-calendar reports and delivery |

Operational records use their own versioned envelopes. A successful job is not a scientific verdict or a completed research acceptance test. The full requirements and adopted definitions are unchanged.

### Scientific batch transaction substrate (November 1, 2026)

The [operator transaction path](../../trading_researcher/EVALUATION_POLICY.md#atomic-batch-commitment-and-admission-boundary)
advances D078/D082, ENG-03/04/13 and REQ-005/007/019 through IF-05. Independent
synthetic cases cover immutable closure, source/runtime binding, exact duplicate
linkage, retained unselected ideas, family conflicts, concurrent reservation,
actual pre/post-COMMIT process exit, rollback, exposure, HTTP and backup/restore.
The existing fixed policy fixture remains unchanged; only its exact-duplicate and
unselected-retention allocation cases are directly mapped here. The other eight
allocation-policy cases are not claimed complete. Production retains admission
gaps; no real scientific freeze, corroboration, full package exit, calibration or
protected access is established. Exact outcomes are in the existing progress register.

The November 2 bounded extension assigns the actual complete family's existing
D075/D082 error policy at atomic commitment, retaining provisional draft counts
and legacy bytes. Seven new independent cases plus 25 transaction and three
owned-plan/dependency caller methods pass at the recorded source. This advances
the IF-05/REQ-005/019 policy-binding subset; all scientific admission, information,
calibration, execution/release and full package exits remain open.

## D090 scoped resource overlay

[research-epoch-feedback-budget/1.0](19_RESEARCH_EPOCH_FEEDBACK_BUDGET.md) affects REQ-004/014/022/023/030 and D079 only for one explicit development epoch. Verification must cover complete feedback, exact provider configuration, one-use and ordered-call persistence across restart/restore, fixed nonrefundable stage limits, unknown usage and revocation. Approval alone establishes neither implementation nor research quality; ordinary budgets and scientific gates remain unchanged.

Executed [D090 verification](../reviews/implementation-2026-10-25/feedback-budget-verification-2026-10-29.json) passes 79 distinct focused tests, including 16 independently authored adversarial cases. The [actual epoch](../reviews/implementation-2026-10-25/feedback-research-2026-10-29.json) retains two settled calls, exact input counts, model/version/UTC and stage-specific stopping gaps. The consumed grant was revoked without changing its historical run snapshot. This is tested operational enforcement, not completed scientific acceptance or demonstrated research quality.

## D091 scoped primitive reuse

D091 / SESSION-2026-10-29-BOUNDED-MATH-REUSE adopts [bounded-math-reuse/1.0](20_BOUNDED_MATH_REUSE.md), tracing REQ-002/003/004/005/011/014/022/023/026/030 to CMP-02/03/04/05/06/07/12 and IF-02/03/04/08/09. Preserve original primitive tests and add exact activation-handoff, unchanged legacy policy, complete-input reservation and independent BTC meaning/formula checks. Approval is not completed verification or research success.

## D093 complete-feedback resource exception

D093 / SESSION-2026-10-30-COMPLETE-FEEDBACK-BUDGET adopts [research-epoch-feedback-budget/2.0](22_COMPLETE_FEEDBACK_RESEARCH_EPOCH.md), tracing REQ-004/014/022/023/030 to CMP-02/03/04/12. Verify all six fixed slots, exact sources and role profiles, operator authority, durable one-use/restart/restore/revocation boundaries, current legacy feedback and actual per-call model/version/UTC accounting. Approval is not completed implementation or scientific success.

Executed [D093 verification](../reviews/implementation-2026-10-25/complete-feedback-verification-2026-10-30.json) retains 60 focused passing tests, old-source preservation, exact real input admission and both existing feedback qualifications. The actual epoch closes with an explicit expressibility gap; no independent reviewer, market computation or scientific verdict follows.

## D094 fixed-pair development trace

| Decision | Status | Adopted scope | Source |
|---|---|---|---|
| D094 | ACCEPTED | [Fixed-pair development and one continuation](23_PAIRED_DEVELOPMENT.md) | SESSION-2026-10-30-PAIRED-DEVELOPMENT |

[D094](23_PAIRED_DEVELOPMENT.md) / SESSION-2026-10-30-PAIRED-DEVELOPMENT maps REQ-002/003/004/005/011/013/014/022/023/026/028/030 to CMP-02/03/04/05/06/07/12 and IF-02/03/04/05/08/09. Required evidence is exact paired semantics, independent source/domain/case checks, owned replay, current legacy reviews and durable one-use resource accounting. Adoption does not establish implementation or empirical usefulness.

## D095 delegated resource disposition

[D095](24_PAIRED_FORMAT_CORRECTION.md) preserves scientific meaning while binding one original format correction to its separate grant and remaining shared budget.

| Decision | Status | Source | Requirement |
|---|---|---|---|
| D095 | ACCEPTED | SESSION-2026-10-30-DISCRETIONARY-BUDGET | REQ-014 |

The [paired closed-development handoff](../reviews/implementation-2026-10-25/paired-feedback-qualification-2026-10-30.json) implements the D070/D078/D083/D094 feedback portion for REQ-007/008/013/028/030 through CMP-07 and IF-01/08/09. Separate paired types, complete retained cohort, atomic release, current source/meaning/data checks and direct technical revocation preserve descriptive authority. It does not complete scientific evidence publication or the full package exits.

The [second-original composition prerequisite](../reviews/implementation-2026-10-25/paired-breakout-qualification-2026-10-30.json) advances D084/D094 and REQ-003/005/011/026 within CMP-03/04/05 and IF-04: independently fixed direct formulas, exact required-input semantics and retained-source synthetic checks. It is not a new language operator, owned production qualification, actual model meaning review or scientific evidence.

The [owned second-original host](../reviews/implementation-2026-10-25/paired-breakout-host-qualification-2026-10-30.json) extends the same D083/D084/D094 trace to REQ-007/013/022 and IF-09: typed source/certificate revocation, immutable failure/case retention and currentness before commit. Synthetic host qualification does not replace actual source or independent model-meaning gates.

The [second-original resource and dispatch qualification](../reviews/implementation-2026-10-25/paired-breakout-continuation-qualification-2026-10-30.json) advances D083/D084/D094, REQ-007/013/022 and IF-09 through exact roles/packets, source-bound invocations, permanent external spending fences and rollback/revocation tests. The [actual descriptive result](../reviews/implementation-2026-10-25/paired-breakout-result-2026-10-30.json) adds real evidence for the existing semantic/execution handoff: unchanged model-authored candidate, separate review and 8,640 replay/audit agreements. A single qualifying observed case does not establish calibrated inference, economic usefulness or the complete TEST-01 through TEST-30 set.

The [second-original feedback handoff](../reviews/implementation-2026-10-25/paired-breakout-feedback-publication-2026-10-30.json) advances D070/D078/D083/D084/D094 and REQ-007/013/028-030 through CMP-09/10 and IF-08: complete immutable cohort, exact evidence bindings, explicit later-context access and retained limitations. [Independent qualification](../reviews/implementation-2026-10-25/paired-breakout-feedback-qualification-2026-10-30.json) distinguishes real original-registry evidence from the explicitly simulated relocated-budget inspection. No complete scientific test inventory or economic success is asserted.

The [bounded AmiBroker closeout](../reviews/implementation-2026-10-25/amibroker-preflight-2026-10-31.json) advances D022/D042/D076 and REQ-009/012/018 at the native adapter boundary: next-open fills, fixed sizing, shared cash, cost scenarios, raw result retention and exact repeats. It is engineering evidence for the declared five synthetic fixtures, not completion of TEST-09/12/18, full policy evaluation or economic support.

## D096 inquiry, feedback, and observable improvement

| Decision | Status | Source | Requirement | Disposition |
|---|---|---|---|---|
| D096 | ACCEPTED | SESSION-2026-11-01-METACOGNITION | REQ-014 | [Inquiry-feedback/1.0](25_METACOGNITION_DUAL_SPACE_INQUIRY.md) also elaborates REQ-028/029/030 through CMP-01/02/03/04/06/07/11/12 and IF-02/03/08/12/13. Specification adopted; runtime integration, behavioral qualification, and benefit remain unverified. |

The [twelve acceptance cases](25_METACOGNITION_DUAL_SPACE_INQUIRY.md#acceptance-cases-and-assessment-boundary) map AC-01/02/03/04/05/08/09/11 to TEST-14 and associated validity/access/resource tests; AC-05/06/07/10 to TEST-28 and existing exposure/freeze tests; AC-12 to TEST-29; and AC-02/08/11 to TEST-30's free-discovery constraints. They remain future behavioral specifications. The [measurement and improvement loop](25_METACOGNITION_DUAL_SPACE_INQUIRY.md#what-should-improve-and-how-to-measure-it) elaborates existing TEST-21/22/27/28/29 purposes without a new score, empirical conclusion, or before-use benefit gate. [Adoption checks](../reviews/adoption-metacognition-2026-11-01/verification.json) verify documentation only.

D096 [diagnostic-boundary examples DQ-01–DQ-03](25_METACOGNITION_DUAL_SPACE_INQUIRY.md#additional-diagnostic-boundary-acceptance-examples) extend REQ-014/028/029 and TEST-14/28/29: a formally valid false diagnosis, a genuinely unresolved cause, and divergence between correctness and action usefulness. They require separate substantive checking and qualified reporting, not a diagnosis score inferred from controller conformance. These are future behavioral cases, not executed tests.


### November 1 implementation boundary: D096 profile constructor

The [qualified constructor](../reviews/implementation-2026-10-25/inquiry-profile-qualification-2026-11-01.json) builds a separate `discovery-inquiry-feedback/2` profile with exact accepted-owner/provenance bindings, preserved original prompts and unchanged nonprompt role settings. Independent scripted cases check their stated storage/access/resource paths and existing regressions; they do not prove actual model diagnoses/actions, a twelve-case behavioral pass, benefit or scientific/economic validity. The old pinned runtime remains unchanged. Actual future worker/presentation binding, full-wire counts, resource/currentness admission and applicable model-behavior qualification remain pending in the sole plan. No live activation, spending grant or new evidence authority follows.


### November 1 implementation boundary: optional inquiry native route

The [scripted route qualification](../reviews/implementation-2026-10-25/inquiry-runtime-qualification-2026-11-01.json) connects the versioned D096 profile with exact source presentation, native reservations and retained trajectories. Source drift settlement retains charges/responses and halts use; a reproduced memory-read gate defect is corrected. The original brokers/source pins remain unchanged. Model AC/DQ behavior, native currentness, complete future wire counts, finite resource admission and scientific/economic effectiveness remain unverified. This is no live activation or new allowance.


## D097 bounded exact-composition adoption

D097 / [bounded-exact-compositions/1.0](26_BOUNDED_EXACT_COMPOSITIONS.md) maps REQ-002/003/004/005/011/014/022/023/026/030 and existing formalization/feature/causality/missingness/resource/replay acceptance to version-specific power/product/all/absolute conformance. The source-approved static shape is not executable coverage. Record actual independent tests and integration limits separately.

[Exact case-layer qualification](../reviews/implementation-2026-10-25/exact-outcomes-2026-11-01.json) adds library coverage for declared lookback/maturity, required-input missingness, whole-scope denominators, shared resource stops and complete-case diagnostic replay (existing REQ-011/014/022/026 obligations). It reports 23 new case/diagnostic methods, including 19 independently authored methods; 28 core and 61 legacy methods also pass. Native/source authentication, actual original-A mapping and whole-interval execution remain unqualified; a synthetic 8,640-case attempt stopped at the unchanged cap. No scientific or economic conclusion follows.

[Exact formalization/native-adapter qualification](../reviews/implementation-2026-10-25/exact-formalization-2026-11-01.json) adds 37 new methods (27 independently authored) and 44 legacy regressions. These cover explicit versions, original text, parameter/exponent provenance, retained gaps, native response/lease/identity binding, full contract bytes, exact original review definitions, later release and the absence of actual independent-model authority for fixture replies. This is scoped REQ-002/003/004/005/014/026/030 conformance; it does not complete their full acceptance criteria. The native fixture's prior definitions are explicitly seeded. Actual certified-input/finite admission, computation certification, protected assessment, complete original-A execution and scientific/economic validity remain open.

[Retained exact runtime/source qualification](../reviews/implementation-2026-10-25/exact-runtime-2026-11-01.json) adds isolated compile/execute/replay, native immutable source/blob certificates and explicit typed D083 package/certificate dependencies. Verification covers exact stream/source identities, malformed metadata rejection, restart/currentness, operator namespaces, revocation without generic provenance taint and the unchanged-cap resource stop. It runs 17 runtime, 19 native-certificate and 18 legacy-revocation methods; the 19 include three inherited expectations also exercised through the new broker. The child independently executes the existing fixed 51 core/case methods. These scoped REQ-003/011/014/022/026 checks do not establish all requirement exits, actual H_exec composition, scientific validity or protected/native research admission.


| Decision | Status | Source | Requirement | Disposition |
|---|---|---|---|---|
| D097 | ACCEPTED | SESSION-2026-11-01-EXACT-COMPOSITIONS | REQ-003 | [Bounded exact compositions](26_BOUNDED_EXACT_COMPOSITIONS.md): specification adopted; new opt-in core and complete mapping require separately recorded independent qualification. No scientific, capital or new spending authority. |


| D098 | ACCEPTED | SESSION-2026-11-01-EXACT-RESOURCES | REQ-018; existing REQ-003/005/011/013/014/022/026/030 | [Separate exact resource version](27_EXACT_COMPUTATION_RESOURCES.md):20M perchild/40M aggregate/shared1800s; new native/source qualification remains pending. Existing checks, old10M records and independent meaning remain; no new API/grant/scientific authority. |

The [historical-feedback qualification](../reviews/adoption-exact-resources-2026-11-01/verification.json)
advances scoped REQ-007/013/022/028/030 under D070/D078/D083/D084: immutable source
and release retention, exact intended-use currentness, read-only financial-fence
inspection and unchanged independent meaning/data-use checks. Actual full
inherited-context PASS is bound to its source/time; the old raw certificate stays
STALE and all seven spending grants stay revoked. These implementation/access
checks complete no scientific acceptance criterion, new inference allocation or
protected/native original-A admission.

| D099 | ACCEPTED | SESSION-2026-11-02-OUTCOME-RESERVATION | REQ-019 | [Stable outcome identity and separate dependence review](28_OUTCOME_RESERVATION.md): option A is adopted specification; actual implementation/admission and resource qualification remain separate. |

## M1 technical research path acceptance (November 2, 2026)

The user's approved manufacturing sequence retains all TEST-01 through TEST-30
and package exits. Its [bounded M1 acceptance](../reviews/integration-research-2026-10-24/IMPLEMENTATION_SEQUENCE_2026-10-25.md#m1-technical-path-acceptance-november-2-2026)
reconciles the original paired-breakout idea/provider response, unchanged
model-authored formalization, separate meaning review, certificates, immutable
request, execution and descriptive report. Fresh read-only checks cover the
353-artifact cohort, eight recorded calls, two original ideas, seven retained
formalization gaps, typed later feedback and all 8,640 retained case bytes.
Thirty-four existing synthetic host/budget/researcher control methods pass at
their recorded source versions. [Exact sources, receipts and helper corrections](../../tests/fixtures/manufacturing-m1-acceptance-2026-11-02.zip)
are retained with criterion mapping in progress.json.

This advances scoped REQ-001/002/003/004/006/012/013/018/023/028/029 evidence; it
does not complete every corresponding TEST or generalize from one genuine
technical witness. Earlier separate numerical replay/original-formula checks
remain historical; the fresh checker reconciles retained bytes and aggregates.
Original start-to-checked-report elapsed time includes incompletely attributed
wait/repair intervals. Scientific freeze/admission, calibration, protected
assessment, economic value, M2-M5 and future complete-cycle timing remain open.
