# Technical dependency revocation integration

Date: October 26, 2026. Starting revision: `f7072ee7d33dfaa03b09612c74613e8b9eff929d`. Scope: existing D083 and IF-09 technical usability semantics, within the continuing seven-package objective.

## Investigation and implementation

The initial question was how to connect data and exposure prerequisites to scientific admission. Source inspection showed that acquisition integrity, quality checks, full normalization replay and raw-feature implementation checks already exist. Historical availability, rights and model exposure remain qualified; combining those facts into a new unconditional scientific data-acceptance rule would not be justified. A separate concrete gap was found: no production revocation operation could prevent future use of a known defective technical version, although contract section 13 already requires that behavior.

The new [revocation module](../../../trading_researcher/REVOCATIONS.md) records an operator's exact version, reason and retained evidence. It captures currently affected objects and derives fresh usability through explicit technical fields. Package identity is based on the complete retained file-hash footprint; a new artifact timestamp cannot reset it. Generic source ancestry, supersession, exposure and scientific genealogy remain separate and do not cause automatic invalidation.

Enforcement connects data scans, package validation, compilation, descriptive execution, all declared plan diagnostics, worker measurement delivery, downstream computations, development studies and their reuse for final calibration. Historical artifacts remain readable. A revoked dependency prevents newly valid output; completed or interrupted work retains its accounting and diagnostic evidence. Current plan inspection reports dependency usability separately from meaning-review currency and the remaining scientific gates.

No new scientific status rule, numerical estimator, provider or software dependency was adopted. No API inference was performed; the prior measured 145,641 tokens and USD 0.404925 conservative cost bound remain the latest provider-usage checkpoint.

## Evidence and retained failures

The [verification manifest](revocation-verification-2026-10-26.json) records exact check commands, outcomes, source hashes and changed files. The [independent review](revocation-independent-2026-10-26.json) records adversarial findings and their resolution. New checks cover authorization, pre-upgrade namespace impersonation, request identity, real backup/restore, package aliases, supersession versus technical use, historical preservation, a separate diagnostic's compiler, data/measurement races and revocation before commit.

Independent review reproduced two measurement failures: a revoked snapshot could still deliver an in-flight or cached tool result. Both were fixed by checking current snapshot usability in the existing authorization gate, including its final delivery check. Review also found missing prelaunch package checks and a reference-certification exception path that could leave an attempt unresolved; the existing failure-retention path now handles revocation.

The initial new API tests failed before implementation. One full integration setup correctly failed with `INPUT_OR_REPORT_CHANGED_DURING_VALIDATION` when the measurement fix changed sources during the retained feature validation. Its output remains retained; the integration was rerun after source edits stopped. No expected numerical values or scientific thresholds were changed to obtain a pass.

The later plan-review regression exposed an internal graph-validation error: one dependency referenced by two typed fields was incorrectly rejected as a duplicate. The traversal now validates each identity and deduplicates edges. A focused regression reproduced the failure before the fix; the original failed run and the subsequent successful checks are retained. The original independent report predates this correction; its [supplement](revocation-independent-addendum-2026-10-26.json) reviews the final source revision.

## Limits and next action

This implements explicitly supported version and consumer schemas. Non-package revocation targets an exact immutable version record; it does not infer aliases or semantic clones of data. A new data version still needs normal admission. Unknown consumer bindings remain unknown, and `NOT_REVOKED` does not mean valid. Operator defect assertions are not independently proven by storing them.

The operation does not grant scientific data/PIT/rights/exposure acceptance, establish statistical adequacy or calibrated coverage/power, issue market evidence, establish profitability, or complete policy applicability/reporting. The full repository suite was not rerun. Future consumers and atomic scientific freeze must recheck current technical usability under their own authorization and transaction boundary.

Next: complete the remaining composition and data/exposure admission prerequisites under the accepted definitions, then calibrated information/evaluation and atomic family allocation/freeze. Keep the first genuine mixed-provider research cycle, AmiBroker policy adapter and domain reporting within the unchanged overall objective. No user decision is needed to finish this technical revocation step.
