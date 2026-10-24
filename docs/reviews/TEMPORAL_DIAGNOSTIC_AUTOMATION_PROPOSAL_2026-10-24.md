# Automatic invocation of temporal diagnostics: review proposal

Version: **0.2, PROPOSED ONLY — USER APPROVAL REQUIRED FOR SCIENTIFIC ACTIVATION**. Date: October 24, 2026.

## Purpose and scope

The user wants a future diagnostic plan to run automatically when its declared conditions are met, so that a person does not have to remember to start it. This proposal specifies the invocation boundary. It does not select a decay estimator, alarm threshold, monitoring frequency, deployment rule or new evidence status. No monitoring runtime or empirical calibration exists today.

This concerns a frozen claim or separately evaluated policy that is registered for an intended use. A supported research result may remain in the Market Model without continuous monitoring. Registering it for current-applicability assessment must bind a versioned diagnostic plan or explicitly return `NOT_ASSESSED` / `REVIEW_REQUIRED`; it must not silently imply current validity.

## Proposed invocation rule

1. Before the first intended use, bind a `DiagnosticPlanRef` to the claim or policy and its versioned applicability scope. The referenced plan specifies its object, eligible input stream and `available_at` rule, target quantity, comparator and absolute economic criterion where relevant, outcome horizon, predeclared review checkpoints, minimum effective information, method and assumptions, resource ceiling, false-alarm policy, and the permitted applicability consequence. A method absent from the approved evaluator envelope remains a capability gap. The plan is frozen before the outcomes it will monitor are inspected.
2. The concrete data event is `EligibleOutcomeBatchCommitted`: CMP-01 has immutably committed a new, versioned and quality-checked batch that adds at least one observation relevant to the bound claim or policy, with its full declared outcome horizon elapsed and every required input actually available by the batch cutoff. A new 15-minute bar by itself is not a completed outcome for a longer-horizon claim. The event records the object, batch/data version, availability cutoff and newly eligible observation IDs. A corrected or late batch gets a new version and its own provenance; it does not silently replace an earlier assessment.
3. Each such event automatically checks whether the plan's next predeclared review checkpoint and information requirement are satisfied. Only then does the workflow invoke the quantitative diagnostic within its budget. The checkpoint may be based on a specified number of new eligible outcomes, an observation-time boundary, or both; it is fixed for that plan, with dependence and repeated looks accounted for. No universal 15-minute, daily or weekly diagnostic frequency is adopted. On each intended use, CMP-10 also requests a current scope/freshness check through IF-11 and runs any already-due diagnostic. The checkpoint identity binds object, plan version and checkpoint; an attempt additionally records the data version and cutoff. Duplicate deliveries are idempotent. Corrected data cause a linked reassessment of the same checkpoint, not a new independent trial. No continuous polling or mandatory wait for new observations is implied.
4. Before calculation, verify plan version, input rights and quality, point-in-time availability, dependency certification, exposure lineage and required information. Missing or stale inputs produce a recorded `NOT_ASSESSED` or `REVIEW_REQUIRED` with a reason and a visible work item. They never produce `IN_SCOPE_AS_OF` by default. A missed, failed or resource-stopped invocation remains visible and retryable under the same identity.
5. A certified diagnostic produces a timestamped record containing the plan and data versions, observation cutoff, target/comparator values, uncertainty and alarm result. If supported by the plan and inputs, it may distinguish regime-prevalence, within-regime effect, risk-exposure and cost/execution observations. `UNRESOLVED` is an acceptable diagnosis; an alarm is not a causal attribution or an `EDGE_DEAD` verdict. New outcome-guided analyses are registered as descendants with inherited exposure.
6. CMP-06 alone applies any approved scientific evaluation rule. CMP-08 records the allowed, time-scoped applicability consequence; CMP-07/11 retain the run, gaps and alerts. CMP-10 may request a later research question under D037. No raw operational PnL, diagnostic result or LLM interpretation directly rewrites an earlier EvidenceRecord, changes a frozen claim or authorizes capital.

In research-contract/1.0, all actions remain research or simulation artifacts and authorized capital remains zero. A future live deployment contract must separately specify whether an operational risk alarm can pause a policy, how reactivation works and who owns that authority. Automatic invocation here grants none of those permissions.

## Why this is the smallest change

D020, D037 and D083 already separate evidence, applicability and deployment and require predefined monitoring. Contract section 13 already calls for reassessment at intended use and versioned quantitative alarms. The missing commitment is reliable invocation and visible failure when a bound plan becomes due. Reuse CMP-06/07/08/10/11 and IF-11; do not add an agent, evidence enum or universal window. The plan's statistical contents remain a later, separately reviewable method profile.

Alternative considered: run a generic rolling-profit alarm for every supported idea. It has no hypothesis-specific target or false-alarm control, consumes resources for ideas with no intended use and risks confusing normal losses with loss of a market relationship. This proposal limits automatic work to a registered plan and declared trigger.

## Acceptance cases to implement later

| Case | Required observable behavior |
|---|---|
| A new complete, eligible outcome batch reaches a predeclared checkpoint | One automatic invocation and a timestamped assessment record; the user need not start it manually. |
| A 15-minute bar arrives before a longer outcome horizon has elapsed, or a batch does not reach the next checkpoint | No quantitative diagnostic or false completed-outcome count; the pending horizon and next due checkpoint remain visible. |
| Intended use occurs before a quantitative checkpoint | Recheck scope and freshness; report the latest assessment with its time and plan validity, or `NOT_ASSESSED` / `REVIEW_REQUIRED` if it cannot support the intended use. |
| The same trigger is delivered twice or a run is retried | One trial identity and no invented independent evidence; attempts remain auditable. |
| No plan, unavailable inputs, insufficient cases or exhausted budget | `NOT_ASSESSED` / `REVIEW_REQUIRED` with a reason and visible follow-up; no current-validity claim or silent skip. |
| A plan detects a local loss but cannot identify its cause | Retain the alarm and `UNRESOLVED`; preserve prior evidence and register any new investigation. |
| A retrospective regime label or later data enters a past decision | Reject point-in-time use; retain the invalid attempt without a scientific verdict. |
| A future deployment rule is absent | No position change, order or capital authorization, even if an alarm is present. |

These are future behavioral acceptance cases, not executed tests. Before activation, a specific method profile must also be checked against stable-loss, regime-frequency-change, within-regime-effect-change and cost-only-change cases with dependence and repeated-look stress. Its false-alarm and detection properties must be reported with uncertainty; passing synthetic cases would not establish live-market benefit.

## Change control and rollback

Affected authority: D008/D020/D026/D037/D083, REQ-008/017/021/025, DEF-027, research-contract/1.0 section 13, CMP-06/07/08/10/11 and IF-11. This file is a proposal, not a canonical amendment. Approval would add the invocation requirement and future acceptance mapping to the canonical documents while leaving method choice and live deployment separately unresolved.

Version every activated plan and invocation rule. A later supersession or rollback restores the previous applicable configuration but retains plans, attempts, alerts, outcomes, failures and exposure history. No previous EvidenceRecord is erased.
