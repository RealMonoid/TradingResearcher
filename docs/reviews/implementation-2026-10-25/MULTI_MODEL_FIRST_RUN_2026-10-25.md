# Multiple models in the first research cycle

Date: October 25, 2026. Status: user-requested engineering continuation; no new scientific contract or paid-provider authorization.

## Purpose and authority

The user wants the first genuine research cycle to use different model families in different roles, possibly through OpenCode. The investigation asks whether this can reuse the controller without bypassing isolation, frozen inputs, accounting or independent evaluation. A bridge that hides requests or changes context without retained provenance changes the integration choice.

[Research-contract/1.0 section 9](../../architecture/14_RETAIL_RESEARCH_CONTRACT.md#9-open-09-perspectives-models-and-compute-budget), adopted in D079, already allows different models. Preserve exactly two sequential discovery perspectives on the same permitted snapshot. REJ-025 rejects different data slices as the default for this role. Formalization preserves the original idea; a separate reviewer inspects meaning; independent code evaluates admitted frozen claims. Unsupported ideas and failed transports remain gaps, not negative scientific findings. Later feedback inherits exposure. The [system reconstruction](../integration-research-2026-10-24/SYSTEM_MODEL.md) supplies the wider flow; its historical implementation inventory is supplemented by current code and [progress](progress.json).

Different models may make correlated errors. Agreement, majority voting and vendor names do not establish correctness or independent scientific evidence. A mixed-model cycle exercises integration; it cannot rank model quality because roles and tasks differ. Unvalidated quality tradeoffs for savings remain disallowed.

## First-run arrangement

| Responsibility | Intended arrangement | Authority |
|---|---|---|
| Discovery A | Existing tested OpenAI adapter | Permitted development context and bounded tools |
| Discovery B | Separately tested Claude or Gemini adapter; a conforming Kimi/DeepSeek alternative is eligible | Same snapshot, separate transcript, sequential execution |
| Formalization | Explicit capable model profile, separate job and exact original inputs | Candidate and semantic-difference report |
| Semantic review | Separate principal; prefer a different tested model family from the formalizer | Faithful/different/uncertain report, no empirical success verdict |
| Numerical evaluation and backtest | Deterministic reference/approved backend path | Frozen scientific rules, independent of model confidence |

No family is assigned superior competence without task evidence. At least two actual model identities across roles are the target; four separate agent teams are unnecessary. Cheaper helpers remain optional under the [earlier review](CHEAP_WORKER_REVIEW_2026-10-25.md).

1. Prepare separately frozen discovery profiles using the existing controller, auxiliary validator and call ledger. This checkpoint implements that bounded step.
2. Add one further provider adapter. Check its tool protocol, structured output, identity/version, usage, refusal, timeout and errors before research use. Reuse the provider-neutral interface with vendor-specific translation where required.
3. Freeze exact available model IDs, prompts and generation settings before launch. Preserve requested/reported identity, known version and explicit unknown revision, role, public responses, UTC admission/settlement, token components and monetary accounting. Generic role fields alone do not implement another provider's reporting contract.
4. Complete data/semantic, information/calibration and scientific-freeze prerequisites; then run the mixed-model historical cycle. Model variety does not close these gates.

All discovery, review, formalization and retries share 12 calls, 80,000 input-plus-output tokens and 1,800 seconds. No per-vendor budget reset, silent downgrade, uncounted helper or unavailable-model replacement. Unresolved usage keeps its reservation. Credentials, billing and model availability must be established before paid use. The existing USD 5 OpenAI aggregate authorization does not automatically authorize spending at new vendors. This continuation uses no new credentials or paid calls.

## OpenCode findings

Read-only local inspection found `opencode.ps1` and npm package `opencode-ai` version **1.18.29**. This verifies installed metadata, not a successful launch or configured provider access. No OpenCode configuration, account or service was changed.

Official documentation supports [per-agent models](https://opencode.ai/docs/agents/#model), [multiple providers](https://opencode.ai/docs/providers/) and a [programmatic SDK](https://opencode.ai/docs/sdk/). The provider directory includes Anthropic, Google Vertex AI, DeepSeek and Moonshot. This is not research-protocol compatibility evidence.

The installed-version tag resolves to commit `16747470f976aca3d362ad730bcd3fe82ecc2c9a`. Targeted source inspection found:

- [prompt.ts](https://github.com/anomalyco/opencode/blob/16747470f976aca3d362ad730bcd3fe82ecc2c9a/packages/opencode/src/session/prompt.ts#L193): an eligible first message triggers a separate title-model request, using a configured title model or small-model lookup, with its own retries. A non-default supplied title avoids this branch, but one external prompt cannot generally be counted as one actual provider call.
- [prompt.ts](https://github.com/anomalyco/opencode/blob/16747470f976aca3d362ad730bcd3fe82ecc2c9a/packages/opencode/src/session/prompt.ts#L1255): plugins can transform messages; environment, instructions, skills and MCP instructions contribute to system input. The submitted research packet is not necessarily the entire provider-visible request.
- [processor.ts](https://github.com/anomalyco/opencode/blob/16747470f976aca3d362ad730bcd3fe82ecc2c9a/packages/opencode/src/session/processor.ts#L674) has an outer retry policy; [llm.ts](https://github.com/anomalyco/opencode/blob/16747470f976aca3d362ad730bcd3fe82ecc2c9a/packages/opencode/src/session/llm.ts#L324) separately sets SDK retries. Disabling one layer does not establish complete call accounting.
- Current [configuration documentation](https://opencode.ai/docs/config/#compaction) describes automatic context compaction and optional tool-output pruning. The pinned source also has a dedicated compaction flow. Research inputs require explicit preservation, not an assumption that coding defaults preserve evidence. The site also has v2 documentation; its schemas must not be copied untested into the installed v1 package.

This is a targeted integration review, not a security audit or a finding that OpenCode is unusable. **Prefer direct provider adapters for the first integration.** OpenCode remains an optional bridge, not the research controller. Future admission needs a pinned runtime/configuration, isolated sessions, authorized tools only, exact retained provider-visible inputs/outputs, governed ancillary calls/retries/compaction, pre-dispatch shared budgets for every actual request, and complete usage/model/time records. Reading only the final answer or final cost total is insufficient.

## Bounded implementation and verification

Optional epoch field `perspective_profiles` maps exactly both discovery identities to model, prompt version, generation parameters, output limit, call timeout and retry settings. Prompts, context, tools, mode, currency and aggregate limits remain epoch fields. Output/time limits use the original epoch token/time ceilings; retry counts use its retry ceiling, reusing the auxiliary policy. Root per-call values are defaults, not additional ceilings on explicit role settings.

Omission preserves the prior profile exactly. Incomplete maps and unexpected fields are rejected. The same immutable epoch binds both choices; changing a model under the same key conflicts. Auxiliary profiles retain precedence and exact input validation. This adds profile selection, not a live provider/router, immutable backend-version guarantees or automatic model switching.

Code/tests: `trading_researcher/research_calls.py`, `tests/test_perspective_profiles.py`, and independent `tests/test_perspective_profiles_adversarial.py`. The researcher guide, current-state handoff, execution sequence, progress and implementation summary record this continuation. [Independent review](perspective-profiles-review.json) and [verification](perspective-profiles-verification.json) retain exact checks and their scope.

Initial six tests produced four expected errors because the optional field was absent. After implementation, one test-only lookup of a nonexistent key was corrected; all six then passed. These are fixtures, not live model comparisons. New-provider compatibility, mixed-model research quality, complete cross-provider billing and scientific readiness remain unverified.

Next: add and test one further provider transport while continuing the scientific prerequisites. User involvement is needed when actual provider access or new spending is required. The larger implementation goal remains in progress.
