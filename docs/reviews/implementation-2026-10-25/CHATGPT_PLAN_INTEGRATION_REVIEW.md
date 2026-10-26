# ChatGPT plan integration: bounded independent review

Date: 2026-10-25. Status: design review; no implementation or account verification.

Purpose: determine whether the supported Sign in with ChatGPT route can power the independent external researcher while preserving the adopted epoch budget, separate perspectives, frozen requests, exposure controls, and durable accounting. The user has authorized USD 5 in aggregate across initial API integration tests; this is not a per-run allowance or authorization to buy credits.

## Recommendation and decisive evidence

Keep the API-key Responses route for the current bounded integration. Reconsider ChatGPT plan usage when its documented remote output bound and quota accounting can satisfy the existing contract. This is a compatibility finding, not a claim that local research tools cannot use a ChatGPT subscription.

OpenAI explicitly supports eligible Plus/Pro users bringing their plan to open-source projects and local personal projects, including research tools. The supported route uses a separately authorized OAuth registration; it does not grant access to ChatGPT conversations. Account-specific eligibility remains unverified. [Official cookbook](https://developers.openai.com/cookbook/articles/sign-in-with-chatgpt)

The present preview rejects `max_output_tokens`. It also requires `store:false`, `stream:true`, and a complete input array; HTTP `previous_response_id` is unavailable. Explicit typed system messages are rejected; instructions/developer messages are supported. Function/custom tools need namespaces or `additional_tools`; hosted MCP and `tool_search` are unsupported. These restrictions apply to both direct HTTP and Codex app-server. [Preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations)

Project inference: counting streamed text or closing a socket cannot establish a cap on all remotely generated tokens. Hidden reasoning and formatting also count as output. A prompt asking for brevity is not an enforceable reservation. The reviewed sources provide no substitute remote bound compatible with our 80,000-token epoch ceiling. A proven model-wide maximum fitting the remaining budget could be considered, but was not established here. [Output accounting](https://developers.openai.com/api/docs/guides/token-counting)

Local evidence: contract 14 section 9 caps all perspectives together at 12 calls, 80,000 input-plus-output tokens, and 1,800 seconds. `research_calls.py:75-89` enforces these ceilings and requires a positive currency cap for live profiles; `:150-202` binds exact request fields and reserves input, output, cost, and deadline before dispatch. `researcher.py:175-205` enforces the frozen model/tools and calls the installed adapter. Relabeling subscription quota as USD, or using a fictitious currency to bypass that guard, would not solve the mismatch.

## Supported reuse and state boundaries

Registration uses a persistent host ID, PKCE, fresh state/nonce, and the issued client ID returned by the dynamic registration flow. It needs neither an API key nor a client secret. Identity validation and the granted `chatgpt.tokens.use.direct` permission are separate checks. Credentials must remain outside retained research inputs, provider-visible context, and audit transcripts. [Registration](https://developers.openai.com/siwc/token-sharing-open-source/sign-in)

The official Python OpenAI SDK can send the OAuth bearer token to public `/v1/responses` with automatic retries disabled. Current account-specific discovery uses `/v1/models`, whose plan-route response has a `models` array with `slug`, `display_name`, and visibility. Freeze the selected slug, account/registration reference, catalog evidence, adapter version, and actual request transformation before an epoch; an unavailable model must stop that epoch rather than trigger a fallback. Success requires `response.completed`, not partial text. [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)

The official DevKit provides local Node workspace packages, not a ready Python researcher. Its current `streamResponse` accepts simple text messages and returns only `{text}`: it is not a drop-in tool-call, full-output, or usage adapter. The example app targets macOS; the storage SDK requires an application-supplied encryption provider. Its current license limits reuse to noncommercial purposes; resolve applicability before importing it. These facts do not prohibit an independently implemented supported protocol integration. [DevKit](https://github.com/openai/sign-in-with-chatgpt-devkit), [stream wrapper](https://github.com/openai/sign-in-with-chatgpt-devkit/blob/main/packages/local/src/responses.ts), [storage boundary](https://github.com/openai/sign-in-with-chatgpt-devkit/blob/main/docs/security.md), [license](https://github.com/openai/sign-in-with-chatgpt-devkit/blob/main/LICENSE)

For stateless reasoning/tool turns, retain and replay the complete response output items, including call IDs, encrypted reasoning, and assistant phase, alongside authorized tool outputs. Text-only conversion loses this state. Encrypted reasoning stays opaque and confined to its perspective; it is not independent research evidence. General Responses documentation describes this behavior; model/route compatibility still needs validation. [Reasoning state](https://developers.openai.com/api/docs/guides/reasoning)

## Budget and billing distinctions

Plan usage has app/account limits and optional credit access in ChatGPT settings. The documented shared five-hour limit applies to Plus, not Pro; this does not establish unlimited app usage or an available allowance for this account. Refreshes must be serialized, registrations kept separate, and tokens protected. [Accounts and sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions)

Plan-route errors stop inference rather than silently changing billing. A usage-limit error can occur after streaming starts. Preserve a sanitized error code/status/request ID, retain the attempted charge, and stop or apply the frozen bounded recovery policy. The docs do not establish plan-route permission for `/responses/input_tokens`; generic API support must not be treated as that permission. [Errors and recovery](https://developers.openai.com/siwc/token-sharing-open-source/errors-and-recovery)

For the API-key path, the documented input-count endpoint accepts the actual Responses payload, including tools and structural overhead. Count the same frozen wire payload that will be sent; bound this preflight by the existing deadline and retain its provenance. An estimate based only on characters or message text is insufficient. [Input counting](https://developers.openai.com/api/docs/guides/token-counting)

Current API cost reservations must include cache writes. On GPT-5.6 and later, default 30-minute writes cost 1.25 times ordinary input; optional 12-hour writes cost 2.5 times. Reads and writes are disjoint portions of input, and the two TTL write counts sum to `cache_write_tokens`. Therefore charging all input at ordinary price is not necessarily conservative. Freeze supported cache options and model prices; reserve the worst permitted write rate, and settle from validated usage with integer monetary units rounded upward. Do not subtract reasoning from output billing or double-count write totals and their components. [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)

## Required adversarial checks before a live adapter

1. Missing/invalid permissions, wrong account/workspace, revoked tokens, refresh races, and callback/nonce mismatches never enable inference or overwrite another registration.
2. Wire requests preserve frozen instructions, model, tools, parameters, and history. Reject unsupported fields before dispatch; no model, endpoint, credential, or billing fallback.
3. Two perspectives retain distinct tool/reasoning histories. Stale, interrupted, or undelivered results remain auditable without becoming worker-readable.
4. Partial SSE, duplicate/malformed terminal events, usage-limit failure after text, incomplete responses, and connection loss cannot become completed tool calls. Unknown usage retains the reservation.
5. Full-input counting and inference bind the same payload. No SDK retries, authentication replay of uncertain inference, or new dispatch after an unresolved attempt.
6. Cost fixtures cover cold cache writes, reads, mixed TTLs, missing/inconsistent usage details, hidden reasoning, and rounding. All initial test epochs and restarts share the USD 5 aggregate ledger.
7. Synthetic secrets in SDK exceptions, headers, redirects, authorization URLs, and process environment never enter retained records or model context. Network targets and credential selection are host-controlled.

Reopening requires documented/enforced remote output limits fitting the epoch budget, an adequate input-bound mechanism, explicit subscription quota/credit policy distinct from money, validated tool/state handling, and user consent for the selected account. None requires changing scientific meaning, granting Codex the researcher role, or exposing assessment data.

## Verification and limits

Only public documentation/source inspection and bounded local source reads were performed. No credentials were read, provider inference/counting/model APIs called, software installed, or production/tests/prior reports changed. Account eligibility, remaining quota, OAuth login, Windows encrypted storage, model access, and end-to-end inference remain unverified. No scientific validity or economic usefulness is established.

The prior `measurement-review.json` remains frozen at SHA-256 `b3477a873c0b4967152176d998ffcbf20c218ace9dd970ca1cba88698b0e51c6`. Documentation whitespace and local-link checks are recorded in the review handoff; this note is the only new project file authored by this review.
