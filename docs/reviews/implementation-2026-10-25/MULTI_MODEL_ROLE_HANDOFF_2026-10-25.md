# Mixed-model role handoff

Date: October 25, 2026. Scope: the user's request to test different model families across the first research cycle's roles. This supplements the [direct adapter checkpoint](ANTHROPIC_TRANSPORT_2026-10-25.md); it does not replace its frozen evidence.

## Purpose and exercised flow

The earlier mixed-controller fixture exercised two discovery perspectives. The remaining integration question was whether their accepted records could pass into formalization and a separate meaning reviewer with different providers while retaining the original epoch's budget and source boundaries. A failure would require a transport or orchestration correction before attempting a real mixed-model cycle.

The new [role-handoff suite](../../../tests/test_anthropic_role_handoff.py) uses the actual OpenAI and Claude adapter implementations, isolated provider children, the controller, retained synthetic market data, feature definitions, formalization records and meaning-review records. HTTPS and key reads are replaced inside each child with explicit fixture responses. The controller client is local; this supplement does not test HTTP RPC delivery.

The three cases exercise:

1. OpenAI and Claude discovery, followed by OpenAI formalization and Claude meaning review.
2. The same discovery assignment, followed by Claude formalization and OpenAI meaning review.
3. A three-call epoch whose discovery and formalization consume the allowance; the reviewer must be blocked before a fourth dispatch.

Both discovery perspectives see the same permitted base context and submit separately. After release, the selected original idea passes unchanged into formalization. The reviewer receives the accepted formalization, original idea, catalog and required definitions; the other perspective's private gap is absent. Auxiliary requests have no tools. The reviewer has a different authenticated identity. Its deliberately uncertain fixture judgment remains uncertain and cannot grant scientific readiness.

Each complete fixture has four dispatches, 680 inclusive synthetic tokens and 2,900,000 synthetic nanoUSD charges in one ledger. The exhaustion fixture expects three dispatches, 460 synthetic tokens and 1,900,000 synthetic nanoUSD charges. These independently fixed expectations are engineering test values, not measured model consumption, typical research costs or spending authorization. Provider/model/catalog version and UTC admission/settlement are checked.

## Checks and limits

The [verification record](anthropic-role-handoff-verification.json) supplies final observed results, source hashes and documentation checks. The first run failed in the new test harness: the reused epoch setup's `profile` attribute shadowed a helper method. Renaming that helper fixed the collision. Importing the support module instead of its test class also removed ten accidentally discovered existing tests. Neither correction changes production behavior or weakens an assertion. The original failed run remains identified in the verification record.

No production source, scientific contract, provider credential or live ledger is changed by this supplement. Existing adapter evidence and archives remain preserved. No new independent review is claimed for these three primary-agent integration tests; the earlier 23-case independent adapter review retains its original scope.

Warranted conclusion: the exercised roles can share one controlled epoch and retain separate provider identities through the existing handoff. This does not establish actual Claude compatibility, substantive independent model judgment, research quality, calibrated evaluation, policy/backtest quality or a completed historical cycle. Gemini, Chinese-model transports and an OpenCode bridge remain unimplemented. Different model labels cannot establish independent errors or empirical success.

Next action: continue semantic/data admission and the information/calibration and scientific-freeze prerequisites. Actual mixed-provider calls require separately authorized Anthropic access and spending; the existing OpenAI allowance remains unchanged.
