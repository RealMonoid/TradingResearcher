# First live OpenAI usage observation

Date: October 25, 2026. This is a frozen observation, not a live counter.

The actual API-key integration passed four model calls, two isolated perspectives,
authenticated tool round trips and registry integrity checks. Both perspectives
retained an explicit gap because this test supplied synthetic context only.
It is not a representative research workload or evidence of scientific discovery.

| Perspective | Calls | Input tokens | Output tokens | Total tokens |
|---|---:|---:|---:|---:|
| First | 2 | 1,019 | 67 | 1,086 |
| Second | 2 | 1,019 | 67 | 1,086 |
| Total | 4 | 2,038 | 134 | 2,172 |

All four calls have reported usage. Cached input and reasoning output were reported
as zero. Preflight counts are retained separately and are not added to these totals.
The conservative published-rate charge is USD 0.006435; USD 4.993565 remains in the
user-authorized USD 5 aggregate test allowance. This is not a provider invoice or
account balance. The API accepted these calls without any top-up performed by us.

Each subsequent admitted OpenAI inference automatically records its run, perspective,
model, prompt version, timestamp, request hash and usage in the same durable ledger.
Unknown usage remains visible; token subsets are never double-counted. See the
[exact snapshot](openai-initial-usage.json), [implementation verification](openai-verification.json)
and [adapter/report documentation](../../../trading_researcher/OPENAI.md).

Read current totals without sending a model request:

```powershell
python -B -m trading_researcher openai-usage --ledger .trf-runtime/openai-integration-budget.sqlite3
```

This covers framework inference, not this Codex development chat. Additional vendors
and automatic weekly report delivery remain future integrations. Actual invoices,
account balance, typical research cost, the large real-data context and scientific
validity remain unverified.
