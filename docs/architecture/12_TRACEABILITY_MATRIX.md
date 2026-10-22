# Traceability Matrix

Archived source references resolve through [SOURCE_REVIEW_INDEX.md](SOURCE_REVIEW_INDEX.md) and `sources/message_index.json`. SESSION-2026-10-22 is a later source recorded separately in D068 and the structured register. Tests below are specified future acceptance tests, not executed application tests. Implementation phases are proposals.

## Forward trace: problem to implementation evidence

| Problem | Requirement | Decisions | Components | Interfaces | Test | Phase |
|---|---|---|---|---|---|---|
| PROB-01 | REQ-001 | D001, D015 | CMP-02, CMP-03, CMP-04, CMP-06 | IF-03, IF-07 | TEST-01 | P2 |
| PROB-01 | REQ-002 | D002, D003, D055 | CMP-02, CMP-03, CMP-04 | IF-03, IF-04 | TEST-02 | P1 |
| PROB-01 | REQ-003 | D004 | CMP-03, CMP-04, CMP-08 | IF-04, IF-09 | TEST-03 | P1 |
| PROB-02 | REQ-004 | D005, D034, D061 | CMP-01, CMP-02, CMP-03, CMP-04, CMP-06, CMP-07 | IF-01, IF-02 | TEST-04 | P3 |
| PROB-03 | REQ-005 | D006, D024, D027, D033, D062 | CMP-03, CMP-04, CMP-06, CMP-08, CMP-09 | IF-05, IF-07 | TEST-05 | P1/P4 |
| PROB-04 | REQ-006 | D007, D052 | CMP-01, CMP-03, CMP-04, CMP-05, CMP-06, CMP-11 | IF-06, IF-07, IF-13 | TEST-06 | P2 |
| PROB-04 | REQ-007 | D008, D043, D067 | CMP-04, CMP-06, CMP-08, CMP-12 | IF-04, IF-12 | TEST-07 | P1 |
| PROB-04 | REQ-008 | D009, D056 | CMP-03, CMP-07, CMP-08 | IF-08, IF-09 | TEST-08 | P1/P3 |
| PROB-05 | REQ-009 | D010, D017, D021, D048, D050, D066 | CMP-03, CMP-05, CMP-06, CMP-08, CMP-09 | IF-10, IF-07 | TEST-09 | P6 |
| PROB-05 | REQ-010 | D011, D032, D036 | CMP-02, CMP-03, CMP-06 | IF-03, IF-07 | TEST-10 | P2/P6 |
| PROB-07 | REQ-011 | D012, D058 | CMP-01, CMP-03 | IF-01, IF-04 | TEST-11 | P2 |
| PROB-02 | REQ-012 | D013, D042, D053 | CMP-01, CMP-05, CMP-06 | IF-06, IF-07 | TEST-12 | P2 |
| PROB-02 | REQ-013 | D014 | CMP-01, CMP-02, CMP-07, CMP-08 | IF-01, IF-02, IF-08 | TEST-13 | P3 |
| PROB-02 | REQ-014 | D016, D029, D039, D054 | CMP-01, CMP-02, CMP-07, CMP-11 | IF-02, IF-03 | TEST-14 | P3 |
| PROB-07 | REQ-015 | D018 | CMP-01, CMP-03, CMP-05 | IF-01, IF-06 | TEST-15 | P2/P5 |
| PROB-02 | REQ-016 | D019 | CMP-07, CMP-08, CMP-09 | IF-08 | TEST-16 | P3 |
| PROB-05 | REQ-017 | D020, D057, D064 | CMP-06, CMP-08, CMP-09, CMP-10 | IF-11 | TEST-17 | P6 |
| PROB-06 | REQ-018 | D022, D041, D063 | CMP-01, CMP-02, CMP-05, CMP-07, CMP-12 | IF-02, IF-06, IF-12 | TEST-18 | P2/P7 |
| PROB-03 | REQ-019 | D023 | CMP-02, CMP-04, CMP-06 | IF-05 | TEST-19 | P4 |
| PROB-03 | REQ-020 | D025, D038, D049 | CMP-02, CMP-05, CMP-06, CMP-09 | IF-06, IF-07 | TEST-20 | P4 |
| PROB-04 | REQ-021 | D026, D040 | CMP-02, CMP-07, CMP-12 | IF-12 | TEST-21 | P3/P7 |
| PROB-06 | REQ-022 | D028, D059, D060 | CMP-11, CMP-12 | IF-13 | TEST-22 | P5 |
| PROB-06 | REQ-023 | D030, D065 | CMP-02, CMP-04, CMP-05, CMP-06, CMP-11, CMP-12 | IF-12, IF-13 | TEST-23 | P1/P7 |
| PROB-03 | REQ-024 | D031, D035, D047, D051 | CMP-02, CMP-04, CMP-05, CMP-06, CMP-09 | IF-05, IF-06, IF-07 | TEST-24 | P4 |
| PROB-05 | REQ-025 | D037 | CMP-08, CMP-09, CMP-10, CMP-11 | IF-11, IF-08 | TEST-25 | P6 |
| PROB-05 | REQ-026 | D044, D045, D046 | CMP-01, CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07 | IF-01, IF-06 | TEST-26 | P5 |
| PROB-08 | REQ-027 | D068, D013, D019, D025, D028, D036 | CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07, CMP-11, CMP-12 | IF-03, IF-06, IF-08, IF-13 | TEST-27 | P7; before framework success claim |

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
| D068 | ACCEPTED | SESSION-2026-10-22 | REQ-027 | Accepted acceleration objective; measurement choices remain OPEN-11. |

## Coverage and orphan rules

Every requirement must map to at least one source-backed decision, component, interface, acceptance test and phase. Every rejection must reference source messages and at least one decision. Every important proposed departure must reference an open decision. A referenced ID existing does not establish that its scientific interpretation is correct; semantic review remains necessary.

Source gaps affect confidence rather than being filled by generated requirements: SRC-001 and SRC-003 through SRC-005 particularly affect early chart/project context; SRC-002 affects the missing pipeline image, but D037 has independent textual user approval; SRC-006 through SRC-008 limit completeness of the overall source record.

## Present verification versus future verification

DOCUMENTATION_VERIFICATION.json records checks actually executed on these documents and the immutable archive. TEST-01 through TEST-27 are not executed. D068/REQ-027/TEST-27 were added after the reconstruction verification report; that report does not validate this later revision. No application, backtest, live data, runtime, schema compiler or statistical calibration was implemented or tested.
