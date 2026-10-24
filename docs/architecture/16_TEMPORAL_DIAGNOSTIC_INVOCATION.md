# Temporal Diagnostic Invocation Contract

Version: **temporal-diagnostic-invocation/1.0 — ACCEPTED**, October 24, 2026. Authority: D087 under D008/D026. This is a versioned extension of the applicability and operational-feedback rules in [research-contract/1.0 section 13](14_RETAIL_RESEARCH_CONTRACT.md#13-open-13-dependency-effects-and-applicability), not a replacement of that contract or a tested runtime capability.

## Approval and scope

The reviewable [proposal v0.2](../reviews/TEMPORAL_DIAGNOSTIC_AUTOMATION_PROPOSAL_2026-10-24.md) specified a concrete data event after the user asked which event would trigger the future diagnostic. The user then replied **"freigegeben"** in the same conversation. Source ID: SESSION-2026-10-24-TEMPORAL-DIAGNOSTIC, outside the immutable original conversation archive. Approval covers automatic invocation and visible failure under the conditions below. It does not approve a statistical decay method, numeric threshold, universal cadence, live deployment or capital authority.

## Binding invocation rule

1. A frozen claim or separately evaluated policy registered for intended current use binds a versioned `DiagnosticPlanRef` before monitored outcomes are inspected. The plan identifies its object and applicability scope, eligible inputs and `available_at` rule, outcome horizon, target and benchmark or economic criterion where relevant, predeclared review checkpoints, minimum effective information, method and assumptions, resource ceiling, repeated-look/false-alarm policy, and permitted applicability consequence. A research result with no intended use may remain unmonitored. An absent or unsupported plan cannot imply current applicability.
2. The data event is `EligibleOutcomeBatchCommitted`: CMP-01 immutably commits a new versioned, quality-checked batch adding at least one observation relevant to the bound object, with its full outcome horizon elapsed and all required inputs available by the recorded cutoff. A new 15-minute bar alone is not a completed longer-horizon outcome. Record object, batch/data version, availability cutoff and newly eligible observation IDs. Corrections and late data retain their own version and provenance. Newly committed history is not automatically independent or model-unseen; evidence origin and inherited exposure remain qualified.
3. Each event automatically checks whether the next plan-frozen checkpoint and information requirement have been met. Only then may the approved quantitative diagnostic run within its budget. A checkpoint can use a predeclared eligible-outcome increment, observation-time boundary or both; dependence and repeated looks must be covered by the approved method. No universal interval or minimum count is imposed. At each intended use, CMP-10 also requests a scope and freshness check through IF-11 and invokes any already-due diagnostic. No mandatory wait for new outcomes follows from this rule.
4. The checkpoint identity binds the object, plan version and checkpoint. Attempts also record data version and cutoff. Duplicate delivery is idempotent. Corrected data append a linked reassessment of the same checkpoint, not a new independent trial. Before calculation, verify input rights and quality, point-in-time availability, dependency certification and exposure lineage. Missing plan, unavailable or stale inputs, uncertified dependencies, insufficient information, failed execution or exhausted resources produce a recorded `NOT_ASSESSED` or `REVIEW_REQUIRED` with reason and visible follow-up; none silently produces `IN_SCOPE_AS_OF`.
5. A completed diagnostic records plan/data versions, cutoff, result, uncertainty, alarm and any qualified explanation. An unresolved cause remains `UNRESOLVED` as a diagnostic description, not a new evidence status. CMP-06 alone applies an approved scientific rule; CMP-08 records a permitted time-scoped applicability consequence; CMP-07/11 retain attempts, gaps and alerts. An alarm may register a later research question under D037. Neither raw operational results nor an LLM interpretation rewrites prior EvidenceRecords or frozen claims.

V1 remains research-only with zero authorized capital under D080. Any operational pause, reactivation or capital action requires a separately approved deployment contract. This extension creates no new agent, evidence outcome, universal window or automatic `EDGE_DEAD` decision.

## Future acceptance cases

These extend TEST-17 and TEST-25 and are **specified, not executed**:

| Case | Required result |
|---|---|
| New eligible completed outcome batch reaches a frozen checkpoint | One automatic diagnostic invocation and timestamped record without a manual reminder. |
| Bar arrives before the outcome horizon, or batch does not reach the checkpoint | No quantitative diagnosis or completed-outcome count; pending horizon and checkpoint remain visible. |
| Intended use occurs before a quantitative checkpoint | Scope and freshness are checked; the latest assessment is presented with its time and validity, or `NOT_ASSESSED` / `REVIEW_REQUIRED`. |
| Event is duplicated or a corrected batch arrives | Duplicate is idempotent; correction appends a linked reassessment, not independent evidence. |
| Plan or input is missing, execution fails, or budget is exhausted | Reason and visible follow-up are retained; no silent current-validity claim. |
| Alarm is present but attribution or live risk policy is absent | Cause stays unresolved when warranted; no EvidenceRecord rewrite, order or capital action. |

Before a quantitative method is activated, its separate version must specify and calibrate the estimand, point-in-time regime or cost inputs if used, dependence, information/checkpoint schedule and repeated-look false-alarm behavior. Stable-loss, regime-prevalence-change, within-regime-effect-change and cost-only-change cases are useful planned calibration scenarios, not empirical findings or a universal method mandate. New scientific meaning remains subject to D008/D026 and D084.

## Versioning and rollback

Preserve this approval, proposal, prior research-contract/1.0, every plan, attempt, correction, alert, outcome and inherited exposure. A future supersession or rollback selects an earlier applicable configuration without erasing historical records. No monitoring runtime, behavioral TEST-17/25 execution, statistical calibration or economic benefit is claimed by this documentation change.
