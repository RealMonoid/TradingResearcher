# Direct Claude Messages transport

The bounded `AnthropicMessagesProvider` implements the existing researcher and auxiliary-role adapter interface. Its first profile is **Claude Sonnet 5.5**, model ID `claude-sonnet-5-5`, API version `2026-10-21`. This is an integration profile, not a finding of model suitability or superiority for research. No actual Anthropic request, key provisioning or paid authorization has occurred in this checkpoint.

## Frozen requests and native continuation

Configuration freezes the model, API version, input/output limits, effort, dated tariff/expiry, optional workspace ID, aggregate ledger cap and an operator-supplied budget-scope reference. There is no default monetary authorization. A scope string records a reference; it cannot grant permission to spend. The original USD 5 OpenAI allowance does not authorize Anthropic charges. If the user later approves mixed-provider tests, both adapters must use the same aggregate ledger and cap so earlier OpenAI spending remains charged; a new database is not a budget reset.

The adapter uses only `https://api.anthropic.com`, with TLS, a bounded response body and deadline, the explicit API-version header and bearer authentication. It reads one `ANTHROPIC_API_KEY` from an explicitly supplied local file, never from chat, prompts, browser sessions, OpenCode credentials or automatic environment fallback. The optional workspace header is frozen because some API keys are not scoped to a single workspace. Configuration provides no arbitrary endpoint, proxy, redirect or transport-retry option. Existing controller retries remain counted and bounded.

The same exact normalized system/user text and permitted tool definitions become the native Messages request. Adaptive thinking uses `display: omitted` and default high effort; this hides returned reasoning text without disabling reasoning or removing its billed tokens. Returned opaque signatures and redacted blocks are retained and replayed unchanged within the existing 1 MiB canonical envelope. Larger envelopes stop explicitly; they are not shortened. No automatic compaction, cached-answer substitution, hosted tools or model fallback is enabled.

Native `tool_use` blocks become controller tool requests only under the matching stop reason. Every call needs exactly one matching result; results are grouped into the immediately following user message. Unknown tools remain subject to the frozen host capability boundary. Text pretending to be a tool call is rejected. An `end_turn` response must be a valid JSON object with `status: final`; there is no fence stripping, guessed repair or hidden model retry. Refusals, truncation, pauses and unknown stop reasons supply no final result or scientific verdict. Supported public content and usage are retained even when a response cannot be used.

## Accounting and time

The free count endpoint is a preflight **estimate**, not consumed inference tokens or a guaranteed bound. The adapter reserves the entire frozen input/output monetary allowance before inference, then checks actual reported usage. For Anthropic, inclusive input is the sum of ordinary, cache-creation and cache-read input tokens. Reported thinking tokens are a subset of output and are never added a second time. Missing or malformed base usage remains unknown; unknown cost retains the reservation and blocks further inference. Even token overruns below the monetary reservation halt the ledger.

The dated standard/global tariff uses a conservative **4,000 nanoUSD per inclusive input token** (the one-hour cache-write price) and **10,000 nanoUSD per output token**. The request explicitly selects global inference and standard capacity. Fast/priority/other geography receipts, unexpected provider iterations or hosted work do not receive an invented price. No caching is requested; the conservative rate covers cache inputs should the API report them. This is an accounting bound, not an invoice, savings measurement or provider-enforced hard spending guarantee. Token-count estimation error, a remotely accepted request after local termination and provider billing reconciliation remain operational limitations.

The existing durable `SpendLedger` is reused; it remains located in `openai_provider.py` for compatibility. Added optional provider/scope metadata does not rewrite earlier rows or reset reservations. Usage report schema `framework-provider-usage-report/3` separates providers in every call/run/model group, including colliding model labels, and retains one total cap. Rows from the earlier OpenAI-only writer without provider metadata keep their documented OpenAI provenance. Unknown model revisions and historical timestamps remain unknown. New records retain catalog version, requested/reported model, prompt version, UTC admission and local settlement times. Those times do not claim to be provider execution start/end.

Read a ledger without network or credential access:

```powershell
python -B -m trading_researcher provider-usage --ledger .trf-runtime/openai-integration-budget.sqlite3
```

The earlier `openai-usage` command remains an alias. Reading the real existing ledger does not add Anthropic access or charges.

## Evidence and remaining work

The later [role-handoff supplement](../docs/reviews/implementation-2026-10-25/MULTI_MODEL_ROLE_HANDOFF_2026-10-25.md) extends the offline flow through formalization and a separate meaning reviewer in both provider assignments. It also checks that the reviewer cannot reset an exhausted discovery/formalization call budget. These are synthetic integration checks, not actual model judgments.

The [implementation report](../docs/reviews/implementation-2026-10-25/ANTHROPIC_TRANSPORT_2026-10-25.md) and [verification](../docs/reviews/implementation-2026-10-25/anthropic-provider-verification.json) record deterministic response, accounting, wire and mixed-controller tests. The mixed test runs both actual adapter implementations in isolated child processes with mocked HTTPS responses: four inference-shaped dispatches, 680 fixture tokens and 2,900,000 fixture nanoUSD charges share one ledger. Native tool round trips, provider/model/version/time records and private transcripts are checked. These numbers are fixtures, not observed provider consumption.

Actual Claude availability, credential/billing setup, provider response compatibility and mixed-model research quality remain unverified. The original data/semantic, nuisance-model, information/calibration and scientific-freeze gates remain required. No library or service installation was needed; the implementation uses the Python standard library.

## Primary sources checked on October 25, 2026

- [Model profile](https://platform.claude.com/docs/en/models/sonnet-5-5/overview) and [pricing](https://platform.claude.com/docs/en/about-claude/pricing): model ID, effort and dated rates. The model's advertised capabilities are not our research-quality evidence.
- [Messages API](https://platform.claude.com/docs/en/api/messages/create), [API migration](https://platform.claude.com/docs/en/api/migration-2026-10-21), and [authentication](https://platform.claude.com/docs/en/manage-claude/authentication): wire fields, version, credentials and workspace selection.
- [Token counting](https://platform.claude.com/docs/en/build-with-claude/token-counting): preflight estimates and free counting.
- [Thinking](https://platform.claude.com/docs/en/build-with-claude/thinking) and [tool-result handling](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls): opaque continuation and one-to-one native tool results.
- [Data residency](https://platform.claude.com/docs/en/manage-claude/data-residency) and [threshold compaction](https://platform.claude.com/docs/en/build-with-claude/compaction-threshold): explicit geography and separate iteration accounting. This adapter does not enable compaction.
