# Provider-neutral research loop

This implements bounded controller/adapter mechanics under D077/D079, not evidence of model invention or scientific validity. It extends the existing [runtime](README.md) and [memory](MEMORY.md). Its fixture demo uses no external SDK, model API, credential, paid call, service, or additional software installation.

Run from the repository root with a new or empty target directory:

```powershell
python -B -m trading_researcher research-demo --directory .trf-runtime/research-demo
```

The command uses real authenticated loopback RPC, SQLite, two sequential discovery identities, and isolated child processes for scripted provider output. Both identities receive the same immutable base context and separate prompts. The first fixture performs a memory lookup and stores an idea; the second retains a capability gap without reading the first transcript. The complete operational batch is released into a later epoch. A JSON report is saved in the target directory and the demo closes its server. Fixture token counts are synthetic byte counts, not any provider's tokenizer or pricing model.

## Owned interface and frozen inputs

`create_research_epoch` binds exactly two registered discovery identities, their base context, exact model identifier, prompt version and per-perspective prompts, tool definitions, generation parameters, output limit, call timeout, transport retry count, currency, and total call/token/time/cost limits. Limits cannot exceed the adopted 12 calls, 80,000 input-plus-output tokens and 1,800 seconds. The adapter must supply conservative input-token and cost reservations before dispatch; no real provider estimator is implemented yet. A live profile requires a positive currency cap, but declaring that profile does not install or authorize a live adapter.

The trusted adapter implements `reservation(request, output_limit)` and `complete(request, ordinal, timeout)`. It receives the normalized public request, not the worker RPC client or its credential. Returned public output and provider/request identifiers are retained with reported usage. This interface does not request private reasoning traces. A real adapter still needs provider-specific encoding, token/cost accounting, identifier handling, cancellation limits, and safe credential provisioning. Local child termination cannot prove cancellation of a remotely accepted paid request.

`reserve_research_call` durably commits a unique call intent before dispatch. Retrying the same key cannot dispatch twice; changing its request conflicts. Both perspectives share the durable epoch budget, including across restarts. An unresolved intent blocks further dispatch and successful job completion until its outcome is reconciled. A timeout or absent usage keeps the worst-case reservation charged. A reported overrun, or malformed usage, retains the response and halts the epoch; malformed usage stays unknown rather than becoming zero. A late response from the original owner is retained for accounting but cannot grant authority to a later attempt.

The installed wrapper executes an adapter in a bounded child process and maintains the job heartbeat. It terminates the local child on cancellation, timeout or lost lease. Configured transport retries use distinct counted calls, with at most two retries and no bypass of the total budget. Adapter reservation failures become a durable blocked attempt with a sanitized exception class, excluding potentially secret-bearing exception text.

## Optional distinct discovery models

The [direct Claude Messages adapter](ANTHROPIC.md) now implements the same trusted interface with vendor-specific native tool replay and inclusive cache-token accounting. A mixed OpenAI/Claude controller test uses mocked HTTPS and one shared ledger; live Claude compatibility and actual model quality remain unverified. Direct APIs preserve controller ownership; OpenCode is not activated.

An epoch may add `perspective_profiles`, mapping exactly both discovery worker names to `{model, prompt_version, generation_parameters, max_output_tokens, call_timeout_seconds, max_retries}`. Each entry is explicit and immutable. The host selects the matching entry before request validation and adapter matching. Prompts, permitted snapshot, tools, source presentation, mode, currency and aggregate budgets remain shared epoch settings. No per-job discovery override or automatic fallback is added. Per-role output and timeout limits are bounded by the epoch token/time ceilings; retries cannot exceed its retry ceiling. Omitting the map preserves legacy behavior exactly.

Formalization and meaning review continue to use their existing independent `research_call_profile`; their settings take precedence over discovery selections while charging the original epoch. A different model label proves neither provider support nor quality. The [multi-model first-run note](../docs/reviews/implementation-2026-10-25/MULTI_MODEL_FIRST_RUN_2026-10-25.md) records the user request, OpenCode assessment, implementation and remaining live-provider work.

## Model-visible tools

| Tool | Authority |
|---|---|
| `read_source` | Read an artifact authorized by the frozen context/current private attempt |
| `search_memory` | Permission-first text retrieval; preserve the returned bundle |
| `record_research` | Retain unverified ideas, observations, gaps and research interpretations |
| `capabilities` | Describe implemented tools and remaining evaluation capabilities |
| `measure_development` | Optional explicitly frozen development tool: causal expressions and descriptive values, never a scientific verdict |
| `read_source_section` | Optional exact ordered page of five fixed provenance/reference lists, after the original artifact read is authorized |

Every public tool request and result, including denials, is retained as an immutable artifact. The model cannot name an arbitrary RPC operation or supply a different worker/lease credential. No shell, filesystem, network-fetch or evaluator-storage tool is exposed. Model-supplied text is data. The operator, local OS account and installed adapter code remain trusted; this is not OS sandboxing of hostile Python code.

The [measurement-enabled tool set](MEASUREMENTS.md) is selected explicitly through `DEVELOPMENT_TOOL_DEFINITIONS`; legacy frozen tools are not silently expanded. Measurement arguments come only from a timely retained provider tool call. Its exact request and source precede execution, and a result outside the original lease/epoch authority is retained without worker read access. A full real-data scripted loop currently exceeds the fixture's byte-based input budget when serializing the entire source context; direct HTTP measurement and small synthetic loop checks cover narrower boundaries.

The model may submit unrestricted idea text. Unsupported ideas can end as retained gaps with a reason and reopening condition. Structural acceptance means an operational record was retained; it never issues scientific evidence. A live provider flag alone would not prove genuinely novel or faithful discovery, so that result remains unverified until the real research milestone.

## Optional bounded source presentation

New discovery profiles may explicitly set `source_presentation` to `discovery-source-view/1` with `CONTEXT_TOOL_DEFINITIONS`. Omission preserves the original full-source payload and tool behavior. The version is frozen in the epoch; earlier profiles and transcripts are not rewritten. Auxiliary formalization/review packets remain full and unchanged.

The view defers only arrays of at least 1,024 canonical UTF-8 bytes at `exposure`, `source_refs`, and `body.manifest.provenance.{checksum_evidence_refs,raw_source_refs,source_uris}`. A distinct view schema and visible deferred marker retain the original artifact ID, ordered-list count, canonical SHA-256 digest and exact path. All other fields remain verbatim JSON values, including scientific qualifications, availability assumptions, coverage, units and gates. A view is not the hash-identical original artifact. Deferred evidence is unread, not empty or irrelevant.

`read_source_section` authenticates the original `read_artifact` before inspecting its path or slice controls. It returns exact ordered values with duplicates, list hash/count and next offset, bounded to 64 items and 16,384 canonical UTF-8 bytes. Invalid or oversized requests receive the existing retained denial; values are never silently shortened. Only the five list paths are supported. It cannot follow a referenced ID or fetch a URL. Every request/result remains in the private transcript, and the controller retains the complete inherited exposure.

Full `read_source` remains available. Full reads, accumulated pages and repeated prompts still count against the same limits; they may exceed the input or epoch budget. Needed unread material must remain an access/resource gap. The measured real-data initial input falls from 43,730 to 3,456 tokens, including the new tool schema. This count-only observation proves neither whole-epoch savings nor unchanged research quality. The option is not promoted to a quality-equivalent scientific default. See the [research note](../docs/reviews/implementation-2026-10-25/TOKEN_EFFICIENCY_RESEARCH_2026-10-25.md) and [verification record](../docs/reviews/implementation-2026-10-25/context-efficiency-verification.json).

The separately frozen `discovery-source-view/2` profile reuses those exact schema/1 views for initial sources and successful `measure_development` responses. The entire measurement body, including values, missingness, gaps and scientific limitations, remains unchanged. The wrapper commits the original `provider-tool-result/1` first, then a separate `provider-tool-view/1` containing its source ID and the exact model-visible body. Only that retained body is sent. A failed view write stops the attempt without repeating the measurement or sending an unrecorded fallback. Denials, malformed requests, full source reads, section pages and other tools retain their prior behavior. Omitted profiles and version 1 preserve their earlier full measurement replies. This adds no model downgrade, semantic summarization or numerical change.

## Verification and remaining boundary

The [auxiliary research handoff](AUXILIARY_RESEARCH.md) now reuses this ledger and isolated adapter invocation for formalization and separate meaning-review tasks. Each role has an explicit immutable model/prompt profile, but shares the original epoch caps and clock. New reservations retain an explicit dispatch deadline; late replies remain accounting records without result authority. Actual independent model judgment remains unverified, including when a fixture is labeled live.

`tests/test_research_calls.py` covers durable intent/idempotency, shared budgets, private transcripts, unknown usage after restart, overruns, late responses, exact profile freezing, pending-dispatch blocking, and malformed-usage retention. `tests/test_researcher.py` covers sequential perspectives, tool execution/denial, gaps, refusal and malformed output, hard timeout, cancellation before/during dispatch, bounded retry, call exhaustion, and sanitized adapter failure. The CLI test exercises the same loop through authenticated RPC. These are software checks with synthetic responses.

The [OpenAI adapter](OPENAI.md) now passes a small actual provider/tool-loop integration through this controller and retains cumulative token usage. Its first four calls used 2,172 reported tokens on synthetic context. Account balance and invoice reconciliation, representative full-context research behavior, semantic formalization/certification, atomic scientific freeze/allocation, calibrated evaluation, scientific terminal-batch release, Market Model publication and market-data validity remain separate work. The [implementation evidence](../docs/reviews/implementation-2026-10-25/progress.json) records fresh outcomes. The registry's general integrity check verifies SQLite, content hashes, audit chain and memory projection; it is not a proof of provider billing or scientific conformance.
