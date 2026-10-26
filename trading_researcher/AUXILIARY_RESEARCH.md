# Budget-bound formalization and meaning-review handoff

An optional [controller-owned direct provider path](CONTROLLER_PROVIDERS.md) now
retains invocation provenance independently of worker-supplied replies. It reuses
these frozen jobs, budgets and adapters; semantic judgment remains unverified.

This continuation connects auxiliary model work to the existing research epoch and preserves independent review reports. It implements transport, input binding and accounting. It does not establish that a real model performed an independent semantic assessment, certify semantic fidelity, or grant scientific readiness. [Research-contract/1.0](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md) sections 8, 9 and 14 remain the authority.

## Shared limits and explicit task profiles

An epoch still has two discovery perspectives on the same frozen base context. An auxiliary `formalization/v1` or `semantic-review/v1` job uses the original `research_epoch_id`, original epoch creation time and existing call ledger. The ceiling remains 12 total calls, 80,000 input-plus-output tokens and 1,800 seconds across discovery and auxiliary roles. A role does not receive a fresh budget. The frozen currency cap remains additional and mandatory for paid work; fixture counters are not provider token or price measurements.

An auxiliary job adds two immutable fields to its existing job specification:

- `research_call_profile`: exact model, prompt version, prompt, generation parameters, output-token limit, call timeout and transport retry limit. Tools are fixed to an empty list. Mode, currency and global limits come from the original epoch. The profile cannot introduce separate call, token, time or spending budgets.
- `research_inputs`: `{idea_id, catalog_id, definition_ids}` for formalization, or `{formalization_id, definition_ids}` for review. References must already belong to the job's frozen context. Adding an epoch ID grants no extra source access or peer transcript visibility.

The operator uses the existing `enqueue` RPC. The worker's `auxiliary_input(lease)` operation derives the exact packet from retained records. Reservations require precisely the frozen system message and canonical user packet; no arbitrary tool request or appended conversational context is accepted. Exact canonical comparison distinguishes JSON Boolean values from integers. Job specifications are copied before validation and retained immutably.

All reservations are charged through the original ledger. Unknown usage keeps its conservative reservation; an accounting overrun halts the epoch. An unresolved dispatch blocks another dispatch, including from another role. Each auxiliary worker receives its own effective profile and current job/generation transcript. A new transport retry is a new counted call against the same packet, within the original retry and epoch limits.

New call records retain `dispatch_deadline`, bounded by the job deadline, original epoch end and call timeout. A late response may settle accounting and preserve public output but cannot supply an auxiliary result. Legacy calls without this field do not acquire a fabricated historical timeout; their existing lease/epoch bounds still apply. Completion also checks that the original epoch remains active and within its lifetime.

## Owned input and output handoff

`run_auxiliary_once(client, provider, cancel=None)` in [auxiliary.py](auxiliary.py) uses the existing isolated trusted-adapter invocation, lease heartbeats, reservations and receipts. It never passes the model an RPC credential, shell or arbitrary tool dispatcher. It retains normalized public responses before interpreting their structure. Refusal, malformed output, cancellation and unusable responses leave recorded history and a blocked attempt rather than an empirical negative.

Formalization output has `{status: "final", candidate, semantic_report}`. The existing `record_formalization` operation accepts `provider_call_id` for this path and verifies the exact task, current job/generation, owned timely call and unmodified response. Existing manually supplied formalizations remain explicitly unverified drafts; they do not become observed model calls. An unrepresentable candidate can remain a `RETAINED_GAP` and receive a later uncertainty review without rewriting the original idea.

A review uses a distinct authenticated principal with the `formalizer` role and `semantic-review/v1` capability. Separation is checked against the retained formalization's actual creator. The target must be its completed job's exact accepted result. The dedicated context contains the target, its original idea/catalog and selected owned development feature definitions, with full inherited exposure. Unrelated diagnostics or peer transcripts cannot be attached to that review context. In the implemented measurement scope, definition versions, feature coverage, type/unit and provenance must match the target's catalog and represented data snapshot; names alone are insufficient. This does not implement semantic review for every future feature-composition contract.

The model's final `review` contains a judgment (`faithful`, `different` or `uncertain`), its own reason, added/omitted assumptions, conflicts, unresolved meaning and one reasoned judgment per original mapping segment. Empty conflict lists are valid; there is no objection quota. A declared faithful judgment cannot simultaneously report unresolved differences. These are consistency checks on a public report, not a deterministic evaluation of natural-language truth.

`record_semantic_review(lease, call_id)` derives the report from this attempt's retained final response; callers cannot supply replacement author identities or report content. The protected `semantic-review-record/1` binds the exact target, input hash, actual formalizer/reviewer identities, model/prompt labels and request/response IDs. Generic source/artifact operations cannot mint it. Record time and exposure remain applicable to future contexts and wrappers. Completion rechecks the owned response binding.

## Authority and evidence

The later [mixed-provider role-handoff suite](../docs/reviews/implementation-2026-10-25/MULTI_MODEL_ROLE_HANDOFF_2026-10-25.md) exercises both direct adapter implementations through discovery, formalization and review, with HTTPS mocked in isolated children. Swapping the formalizer/reviewer providers preserves owned inputs, distinct identities, shared accounting and the unverified judgment boundary. Actual API compatibility and semantic quality remain separate checks.

Every review record keeps `actual_independent_model_review: "UNVERIFIED"` and `scientific_readiness: false`; worker outcomes also keep actual model judgment unverified and grant no scientific authority. A scripted adapter relabeled `live`, a supplied provider ID, or a different worker name is not proof of an actual model invocation or independent judgment. Replaying the formalizer's assertion in another process does not close that gate. A real provider adapter, verified invocation provenance and substantive independent assessment remain necessary before any future scientific admission can use such a report.

The [verification report](../docs/reviews/implementation-2026-10-25/auxiliary-research-verification.json) and [independent review](../docs/reviews/implementation-2026-10-25/auxiliary-research-review.json) record exact exercised checks and remaining limits. The integration uses owned synthetic data and isolated scripted provider processes. An additional primary-agent check completed both roles through the authenticated loopback HTTP client/server, charged exactly two calls to the shared epoch and retained the original formalization unchanged. The independent review did not itself exercise that HTTP path. These checks do not establish genuine LLM invention, substantive semantic fidelity, historical data/rights/PIT acceptance, statistical calibration, scientific freeze/allocation, market usefulness or live capital authority. Existing source versions and the preceding checkpoint remain preserved in the [baseline](../docs/reviews/implementation-2026-10-25/auxiliary-research-baseline.json).
