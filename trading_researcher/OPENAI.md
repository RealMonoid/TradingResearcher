# OpenAI transport and usage records

The later [provider/measurement integration](../docs/reviews/implementation-2026-10-25/OPENAI_MEASUREMENT_INTEGRATION_2026-10-25.md) completed six actual calls on qualified retained development data, including exact measurement/page round trips. Cumulative consumption is 35,084 tokens across ten calls, with a conservative USD 0.095105 rate bound; this is not an invoice or representative discovery workload. The six new calls exercised model/catalog-version and UTC admission/settlement records. Earlier missing fields remain unchanged.

This API-key Responses adapter implements the existing bounded researcher interface.
It does not grant scientific authority. The first integration-test authorization is
**USD 5 total across every epoch and retry**, recorded separately from the research
epoch limits. The operator must reuse `.trf-runtime/openai-integration-budget.sqlite3`.
Creating a different ledger would create a different accounting scope, not renew
the user's authorization. No automatic funding, retry, provider or billing fallback exists.

The current `gpt-6.1-sol` standard-tier profile freezes input/output bounds, reasoning
effort, tariff and expiry. Host reservation precedes network access; a full-input
token-count request precedes inference. An aggregate monetary reservation commits
before the inference POST. Unknown usage retains the full reservation and prevents
later inference. The API receives the frozen output limit. Local cancellation does
not prove remote cancellation. Replay preserves opaque reasoning continuation and
matching native tool IDs without requesting private chain-of-thought.

The dated conservative tariff uses USD 2.50 per million input tokens (the worst
permitted 30-minute cache-write rate) and USD 10 per million output tokens. It does
not apply cache discounts. `cost_units` are integer nanoUSD: one USD is 1,000,000,000
units. These are published-rate upper bounds, not actual invoices. Recheck the
[model tariff](https://developers.openai.com/api/docs/models/gpt-6.1-sol) and
[cache rules](https://developers.openai.com/api/docs/guides/prompt-caching) before
renewing an expired configuration. Unpriced model/tier changes and token overruns
make responses unusable and halt further inference.

## Persistent consumption documentation

Every admitted inference dispatch stores its timestamp, run and epoch identity,
worker perspective, model, prompt version, request hash and preflight input count.
Settlement atomically retains the reported input/output usage and conservative
currency charge. Missing usage and interrupted pending reservations remain visible;
restarting the application cannot reset the cap or overwrite a settled receipt.
The existing research registry also retains call requests, responses, refusals,
zero-inference preflight failures and their relationship to jobs and artifacts.

Read the current aggregate report without a key or network access:

```powershell
python -B -m trading_researcher openai-usage --ledger .trf-runtime/openai-integration-budget.sqlite3
```

The report contains per-call records, per-run/perspective totals and aggregate totals.
`known_total_tokens` sums reported input plus output. `exact_total_tokens` is null
when any admitted call lacks a usable usage receipt. Cached input and reasoning
output are subsets, never extra tokens; known sums, coverage counts and nullable
exact subset totals preserve missing details. A preflight count measures a proposed
input and is not added to inference consumption. Older ledger rows without token
receipts remain unknown. The report excludes Codex chat usage and synthetic fixture
byte counters. It does not allocate shared call costs among multiple hypotheses.

Report schema `framework-provider-usage-report/3` retains model identity and
readable UTC timestamps. New dispatch metadata records the requested model and frozen
catalog name, public version and source. The actual response separately records the
provider-reported model identifier. For this adapter the public catalog identifies
**GPT-6.1 Sol / 6.1**; this is not an immutable served snapshot. The API's alias alone
does not establish an exact backend revision, so `immutable_snapshot_id` remains null
with status `UNKNOWN`. Prompt and tariff versions are independent fields. Run and
model summaries do not merge distinct identity records.

Schema 3 additionally separates providers in call/run/model summaries and supports
the [Claude adapter](ANTHROPIC.md). Earlier stored reports remain unchanged; the
read-only renderer does not migrate ledger rows. Historical rows from the original
OpenAI-only writer retain their OpenAI attribution. `provider-usage` is the neutral
CLI name; `openai-usage` remains an alias. The original OpenAI spending authorization
does not authorize another provider by itself.

`admitted_at_utc` renders the original host admission timestamp as ISO 8601 UTC.
`settled_at_utc` records the local accounting transaction time; neither field claims
the provider's actual execution start or completion time. New settlement timestamps
commit atomically with usage and survive idempotent replay. Historical records missing
these new fields remain explicitly unknown. The read-only report never backfills
them from today's configuration or clock. The [historical identity/time supplement](../docs/reviews/implementation-2026-10-25/OPENAI_USAGE_IDENTITY_2026-10-25.md)
links the original four calls to their retained responses without rewriting receipts.

Provider credentials stay in the confirmed, Git-ignored `.env.local`; reports never
include credentials, authorization headers or key-file contents. API-key usage has
[separate Platform billing](https://learn.chatgpt.com/docs/auth). The currently reviewed
ChatGPT-plan preview lacks the required remote output-token cap; see the
[compatibility review](../docs/reviews/implementation-2026-10-25/CHATGPT_PLAN_INTEGRATION_REVIEW.md).

The [first retained live usage observation](../docs/reviews/implementation-2026-10-25/OPENAI_USAGE_2026-10-25.md)
records four completed model calls and 2,172 tokens. Recording occurs automatically
inside this adapter; the read-only command renders the latest ledger whenever needed.
Future adapters must preserve the existing normalized input/output usage contract.
This aggregate reader currently covers OpenAI; automatic weekly delivery belongs to
the still-pending reporting work package.

## Trust boundary and remaining checks

The local operator and installed provider code are trusted. A model controls only
public output and proposed tool arguments; the controller checks roles, ownership,
frozen tools, leases and exposure. Credentials are read privately by the transport
and sent only to the fixed TLS `api.openai.com` destination. Redirects, environment
base-URL overrides, raw error-body logging and unpriced nested cache options are not
accepted. Provider usage and metadata are validated before becoming accounting or
actionable output. Reports are operational records, not scientific evidence.

Offline tests exercise monetary admission, restart/race handling, immutable receipts,
known/unknown token accounting, optional subset coverage, native tool replay and
malformed responses. Actual account access, wire compatibility and end-to-end model
behavior require separately retained live results. A small synthetic integration
test cannot establish typical research costs, complete real-data context handling,
novel discovery, statistical calibration or profitability.
