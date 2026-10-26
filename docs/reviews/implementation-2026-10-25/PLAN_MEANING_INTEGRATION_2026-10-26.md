# Meaning-review integration with evaluation plans

Date: October 26, 2026. Scope: ordinary prerequisite integration under D002, D074 and D084, following the requested GitHub publication at `32eccc2` and the actual-review observation update at `bdc6254`.

## Purpose and finding

The existing meaning-review assessment could establish a current process prerequisite, but evaluation-plan preparation always retained the semantic-review gate with no way to bind that evidence. The relevant uncertainty was whether the exact formalization, feature meaning, complete review history and inherited exposure could be connected without changing the scientific policy or rewriting historical plans.

The implementation now accepts optional `meaning_review_id`, retains `meaning_review_at_preparation` in both the admitted input capsule and completed plan, and rechecks the current inventory before commitment. The evidence must target the exact formalization. For feature-dependent candidates every assessment review must contain the exact definition artifact used by the feature certificate. Matching feature names and units do not establish identical parameters or timing. The new reference contributes its source ancestry and exposure.

`inspect_evaluation_plan(plan_id)` returns the historical draft/gap status, fresh meaning-review currency and a derived `current_remaining_gates` list. It removes only `independent_semantic_review` when the scoped assessment is current and satisfied. New reviews, unresolved opinions or changed review-policy sources reopen that prerequisite. Legacy plans retain all gates; an unsupported policy remains an evaluation gap with a null gate list. Raw calculator output and historical plan bytes are unchanged.

An interrupted request cannot silently retry with a changed review inventory. Completed same-key requests return the original historical record, so intended use must inspect currency separately. Inspection is instantaneous, not a durable admission token; future freeze must recheck in its own atomic transaction. No new table, provider, framework, numerical policy or scientific authority was introduced.

## Verification and qualifications

The final [verification manifest](plan-meaning-verification-2026-10-26.json) records exact commands, outcomes, changed files, source identities and retained failures. The [independent review](plan-meaning-independent-2026-10-26.json) separates source review and adversarial checks from scientific evidence. Small boundary fixtures run real review provenance, input retention and isolated calculation/replay while explicitly stubbing data dependency resolution. Separate integration tests run synthetic normalization, feature/reference certification, compilation, descriptive execution and plan preparation without that stub. Provider responses remain mocked in all new tests.

Initial three new API tests failed before implementation, then passed. Independent test development exposed two fixture errors: a method/attribute naming collision and an invalid repeated release epoch; these were corrected without weakening production checks. The first two full-integration negative fixtures were rejected earlier by existing auxiliary input checks, so they did not exercise the intended plan boundary. The final counterexample supplies matching feature names/types/units with a different declared availability delay and checks exact definition identity at plan admission. Earlier failed runs remain in the verification record.

No paid call or real-data research run was performed. The previous measured provider usage remains 22 calls, 145,641 tokens and USD 0.404925 conservative cost bound under the USD 5 authorization. These software checks do not prove natural-language equivalence, historical data/PIT acceptance, calibrated coverage or power, an adequate information target, atomic allocation/freeze, a genuine research cycle, multi-provider quality or profitability. The full repository suite was not rerun.

## Next action

Connect the remaining data/exposure and composition prerequisites to explicit owned admission evidence, then complete calibrated information/evaluation and atomic family allocation/freeze under the existing contract. Retain unsupported scientific meanings and missing calibration as gaps. Actual Anthropic access and spending still need their own authorization before the requested mixed-model live cycle; other authorized work can continue.
