# Review of four user-supplied token-efficiency candidates

Reviewed October 25, 2026. The user requires that research quality and the backtest must not be damaged. Scope: inspect public documentation and relevant source, identify reusable mechanisms, and distinguish development assistance from changes to the research runtime. Nothing from these four projects was installed, executed, given credentials or connected to the framework during this review.

Acceptance requires preserved scientific authority, exact source access, unchanged calculations, visible omissions/failures, accurate model/version/time accounting, and no silent model substitution. A repository's benchmark or a recoverable original is not proof that our model will make equally good decisions.

## Versioned observations

| Project | Inspected commit | Relevant role | Current disposition |
|---|---|---|---|
| [OmniRoute](https://github.com/cheaper-inference/OmniRoute/tree/81e48878b90fb309ede580bca8b97c6953a2fc62) | `81e48878b90fb309ede580bca8b97c6953a2fc62` | Provider gateway, routing, usage and optional compression | Consider later for an actual multi-provider need; do not insert into current research calls. |
| [Codesight](https://github.com/Houseofmvps/codesight/tree/f9a43d70f0a6538c845884242894d6c0c02f0950) | `f9a43d70f0a6538c845884242894d6c0c02f0950` | Generated code map, dependency navigation and wiki | Lowest-complexity development-only evaluation candidate. |
| [JFrog Boost](https://github.com/jfrog/boost/tree/3cb645ffcef0d369d155056cd4238c952dcc67d2) | `3cb645ffcef0d369d155056cd4238c952dcc67d2` | Filtering coding-agent command/tool output | Potential narrow terminal-output trial; no global hooks or research-output filtering now. |
| [Code Context Engine](https://github.com/elara-labs/code-context-engine/tree/75071156e08a145fab17c8ce30bb5f418286f434) | `75071156e08a145fab17c8ce30bb5f418286f434` | Local semantic code search and indexing | Interesting Python-navigation alternative, but its default compression needs substantial restriction. |

## OmniRoute

The gateway could eventually consolidate several provider adapters and operational usage views. It is not a scientific research memory or backtest engine. Its README describes automatic fallback, response caching and multiple compression engines. These features require separate treatment: an alternative model is a different frozen model identity, a reused answer is not a fresh independent perspective, and natural-language pruning is not exact prompt preservation.

The inspected [strategy selector](https://github.com/cheaper-inference/OmniRoute/blob/81e48878b90fb309ede580bca8b97c6953a2fc62/open-sse/services/compression/strategySelector.ts) returns the input body unchanged for compression mode `off`. The [plan derivation](https://github.com/cheaper-inference/OmniRoute/blob/81e48878b90fb309ede580bca8b97c6953a2fc62/open-sse/services/compression/deriveDefaultPlan.ts) also supports disabling engines. Therefore lossy compression is avoidable in principle; it is not inherent to every use of this gateway.

There is documentation drift: the [compression guide](https://github.com/cheaper-inference/OmniRoute/blob/81e48878b90fb309ede580bca8b97c6953a2fc62/docs/compression/COMPRESSION_ENGINES.md) describes different default stacks in different sections. Do not infer the active deployment configuration from the headline. A future adapter would need a pinned provider/model, compression and semantic response caching disabled, native usage/request identity preservation, counted retries, and exact request/response parity tests. The existing fixed-destination OpenAI adapter cannot simply be repointed at an OpenAI-compatible gateway without that work. Current benefit does not justify another routing layer.

## Codesight

Codesight supplies a navigational map and dependency information. That could reduce repeated repository exploration while keeping original source reads available. The [README](https://github.com/Houseofmvps/codesight/blob/f9a43d70f0a6538c845884242894d6c0c02f0950/README.md) distinguishes TypeScript AST extraction from the ordinary regex fallback and optional native AST plugins for other languages. Our custom Python/SQLite runtime is not the same workload as a TypeScript web application; detector coverage and dependency accuracy need a local comparison with known code paths.

The [configuration generator](https://github.com/Houseofmvps/codesight/blob/f9a43d70f0a6538c845884242894d6c0c02f0950/src/generators/ai-config.ts) has two materially different paths: ordinary generation skips an existing `AGENTS.md`, but the explicit `agents` profile writer writes that file directly. A future evaluation should emit a separate map in a disposable source copy and leave our canonical instructions untouched. Generated architecture text is an index, not authority over the Decision Register or accepted contracts. The candidate is MIT-licensed; this review did not execute or validate its scanner.

## JFrog Boost

Boost's useful mechanism is bounded presentation of noisy build/test/log output while retaining the original for `boost retrieve`. Its [documentation](https://boost.jfrog.com/docs/en/features/token-reduction/) describes preservation of failures and summaries. For this project, the safe evaluation target would be progress/ANSI repetition in development commands, with complete original stdout/stderr, exit status, failing case identities and numerical results retained outside the filtered view. Scientific artifacts and evaluator outputs must remain exact.

The [vendor benchmark](https://boost.jfrog.com/benchmarks/terminal-bench-2/) uses 89 Terminal-Bench tasks with Claude Code/Haiku 4.5 and reports lower aggregate cost. That is evidence about that experiment, not proof of equal framework research quality. Raw job views require a separate Harbor login and were not inspected here.

The public tree contains distribution/integration material, not the complete filter-engine source needed for an implementation audit. Its [license](https://github.com/jfrog/boost/blob/3cb645ffcef0d369d155056cd4238c952dcc67d2/LICENSE) is All Rights Reserved under an Online Preview Agreement, unlike the other three MIT candidates. Its README describes global agent integrations and outgoing usage metadata. Those are concrete deployment considerations; local filtering does not mean no metadata transmission. No installer, terms acceptance, global integration or telemetry configuration was performed.

## Code Context Engine

Tree-sitter, local embeddings and hybrid keyword/vector search are potentially helpful for Python navigation. The [README benchmark](https://github.com/elara-labs/code-context-engine/blob/75071156e08a145fab17c8ce30bb5f418286f434/README.md) explicitly compares its headline 94% saving against full-file reads, not normal targeted coding-agent exploration. Its FastAPI Recall@10 is 0.90; other language/repository results vary. Retrieval savings do not mean perfect recall or unchanged coding quality.

The inspected [configuration](https://github.com/elara-labs/code-context-engine/blob/75071156e08a145fab17c8ce30bb5f418286f434/src/context_engine/config.py) defaults both chunk and output compression to `standard`. The [compressor](https://github.com/elara-labs/code-context-engine/blob/75071156e08a145fab17c8ce30bb5f418286f434/src/context_engine/compression/compressor.py) may use an Ollama summary or fall back to signatures/truncation. Even `full` is a conditional pass-through, not an unconditional promise for every retrieved chunk. The summary quality check is not a proof of semantic equivalence.

The [MCP implementation](https://github.com/elara-labs/code-context-engine/blob/75071156e08a145fab17c8ce30bb5f418286f434/src/context_engine/integration/mcp_server.py) also performs retrieval filtering, session capture and output-directive insertion. Its convenience init changes editor/instruction configuration. A useful restricted evaluation would expose search results as source locations, obtain complete original code independently, disable output rewriting, and avoid adding a competing decision-memory authority. Index freshness, omitted relevant files and allowed-path boundaries need explicit checks. The name `full` alone is insufficient to authorize direct research use.

## Decision and next action

There are useful development mechanisms here, especially navigational indexing and selective treatment of repetitive terminal output. None of the four is adopted as a transparent research-quality-preserving middleware. No current requirement needs another installed package: the existing exact source-section implementation already addresses a measured runtime context bottleneck without adopting semantic summarization.

If repeated code navigation remains costly, compare a separate Codesight map first against fixed known module relationships; use CCE as a second candidate if semantic retrieval adds measurable value. Keep `rg` and exact source reads as the comparison baseline. Advance only if complete relevant code remains available, protected instructions/artifacts remain byte-identical, failures are visible and the total cost of retrieval plus follow-up reads improves. A limited trial may reject a candidate without changing framework behavior.

Unverified: installation/runtime behavior on this machine, security of release binaries and dependencies, all vendor savings claims, complete source-level audits, and quality equivalence for this framework. No backtest or research-profile behavior was changed by this four-project review. The separate ongoing context-view implementation is documented in [its verification record](context-efficiency-verification.json).
