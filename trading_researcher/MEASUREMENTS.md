# Development measurements for discovery

The provider-neutral researcher can request a causal `research-ast/1` expression on an authorized development snapshot. This reuses the [reference calculator](EXPRESSIONS.md), [data boundary](DATA.md), private [research memory](MEMORY.md), and retained [provider-call ledger](RESEARCHER.md). It supplies descriptive observations for free discovery; it does not judge a hypothesis or issue scientific readiness.

## Interface and authority

`DEVELOPMENT_TOOL_DEFINITIONS` adds `measure_development` to the legacy tool set. Existing frozen profiles retain their exact tools. The model supplies `snapshot_id`, an exact 15-minute `universe`, explicit `warmup_bars`, and a catalog-bound expression `program`.

The RPC accepts only `lease`, `call_id`, and `tool_id`. The controller derives all measurement arguments from the already retained provider response, checks its owner and generation, accounting and timeliness, active epoch, frozen tool permission, authorized snapshot and development partition. It rejects replacement arguments, unlisted/protected snapshots and invented or ambiguous tool IDs before loading data.

Installed source bytes and the exact request are retained before calculation. A completed retry returns the same artifact; an interrupted unresolved invocation cannot automatically run again. Ownership and epoch authority are checked again before release. An undelivered result remains available for operator audit without worker exposure, including through ordinary artifact reads. `delivered` records authorization for return, not proof of network receipt. Successfully exposed values and missingness remain inherited discovery exposure.

## Calculation limits

| Limit | Meaning |
|---|---|
| 256 output positions | Time/instrument cells, not 256 timestamps per instrument |
| 512 warmup bars | Explicit, inside the same authorized snapshot; never silently supplied |
| 100,000 primitive steps | Shared across the whole expression request |
| 256 KiB retained-value stop | Checked after each complete bounded value |

Missing current rows, missing feature values and values unavailable at the decision instant remain distinct. Boolean short-circuit decisions retain missing/late dependency traces. Exact rational means and extrema, or Boolean counts, describe defined values only. Partial work reports its completed prefix and uncomputed suffix; missing values are not zeros and resource stops are not negative market findings.

The existing loader still validates and scans the full snapshot for a small selected window. These logical limits are not a hard operating-system deadline, cheap-query guarantee or independent-process replay certificate. Stored availability assumptions and remaining data/scientific gates accompany each result.

## Verification and remaining work

Seven parent tests and fourteen independently authored tests cover arithmetic, causal availability, missingness, warmup, resource limits, recorded-call ownership, private perspectives, interruption and release fencing. Review reproduced an undelivered-result read leak; the retained failing case passes after removing worker exposure from those results. [Review](../docs/reviews/implementation-2026-10-25/measurement-review.json) and [verification](../docs/reviews/implementation-2026-10-25/measurement-verification.json) distinguish original failures from later passes.

A real-data direct HTTP probe evaluated eight lagged Binance close values for each of two isolated perspectives and checked them against exact retained source values. This exercised the authenticated measurement operation, not a real model. A separate full researcher-loop probe stopped before dispatch because the fixture provider's byte-based input accounting exceeded the frozen budget with the full source context. That failed probe remains retained; direct RPC success does not resolve full-context integration. The small synthetic researcher-loop test passes.

Live provider behavior and billing, useful discovery, compact source presentation, historical data truth, feature/semantic certification, calibrated inference and scientific freeze remain separate work. No capital or deployment authority is added.
