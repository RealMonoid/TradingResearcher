# Research memory foundation

Implemented October 25, 2026 as the first package of the [execution plan](../docs/reviews/integration-research-2026-10-24/IMPLEMENTATION_SEQUENCE_2026-10-25.md). This extends the existing authenticated broker and its SQLite registry. It introduces no model provider or scientific decision rule.

## Run the synthetic demonstration

```powershell
python -B -m trading_researcher memory-demo --directory .trf-runtime/memory-demo
```

The directory must be new or empty. The command starts its own loopback server, records a fixture source, an idea, a retained gap, a correction, and the controller's completion observation. It searches through an authenticated worker, releases the completed operational batch, replays the index, restores a backup into a separate directory, and closes both the server and registries. `memory-demo-result.json` contains the outcome. This is not LLM invention or market evidence.

## Records and authority

`research-record/1` has exact fields: `schema`, `kind`, `content`, `scope`, `relations`, `created_at`, and `available_at`. The enclosing immutable artifact supplies identity, creator, source ancestry, exposure, and authority. Content hashes, duplicate-key rejection, explicit decimal strings, and the existing one-MiB envelope limit remain in force.

Kinds are `source`, `idea`, `observation`, `gap`, `attempt`, `research_experience`, and `policy_experience`. Each has an explicit field allowlist; gaps require a reason and reopening condition. Relations may express `supersedes`, `contradicts`, and `depends_on`. Both ends remain in history. Recording a relation does not establish that either claim is true.

Idea `content.text` now accepts up to 65,536 Unicode code points, preserving the exact string without trimming, normalization or truncation. Other text fields, scope values and queries retain their 8,192-character limits, and the aggregate one-MiB envelope limit still applies. This compatible admission extension retains `research-record/1` bytes and adds no migration or automatic reprocessing of old blocked jobs. A build predating this extension can reject a newly retained long idea during replay; rollback must preserve those records and use a compatible reader. Independent tests cover the actual 8,255-character boundary, complete formalization handoff, replay, restart and backup/restore on isolated registries.

The Journal contains all typed records. Research Experience and Policy Experience are separate projections of their own record kinds. The Market Model query surface exists but remains empty: no memory RPC can issue scientific evidence. Its qualified publication path is a later evaluator integration requirement, not completed work. Likewise, generic trial/plan references can be retained as dependency links, but complete executable scientific schemas belong to the formalization package.

Workers have role-specific write allowlists. Their records carry `unverified_work_product`; source imports carry `supplied_source_not_certified`. Actual completed, rejected, blocked, and expired attempt transitions are recorded by the host with `observed_operational_event`. A model's claimed completion cannot become an observed host transition. Operational completion of a `research-record/v1` job checks record structure only and returns `scientific_authority: false`.

## Query and information boundaries

The operator supplies an explicit frozen context. New contexts use `local-context/2`, adding `research_time`; existing v1 context bytes remain unchanged. A typed record must be available by that time, satisfy the role/data boundary, and meet any inherited release epoch. Memory `available_at` is the time the record is available to this application, not a certification of the underlying market data's historical publication time.

The formalization integration also checks draft creation times and known transitive record-availability bounds through generic wrappers. Derived typed sources inherit those bounds. This closes backdating through a wrapped idea/draft; unknown legacy/raw-source availability remains unverified. Traversal currently repeats shared ancestry for separate roots; a measured 256-root synthetic wrapper chain took about 0.733 seconds on this host, without establishing a general latency guarantee.

`search_memory` first limits candidates to the frozen context and the current worker's current-attempt scratch. It then applies view, kind, exact scope filters, and case-insensitive text matching under `metadata-text/1`. Denied records do not affect returned counts, snippets, or pagination. Later host imports do not enter an existing snapshot. A retry does not silently recover a previous attempt's private scratch.

The base context stays immutable. Same-attempt observations and corrections form a separate append-only chain. New work products conservatively inherit the entire base plus prior current-attempt artifacts, rather than allowing a worker to omit inconvenient information. Every retrieval records the query, context, policy version, returned bundle, attempt, and generation in the host audit chain. This is lineage accounting, not proof that the model comprehended a record.

Only the operator can release a completed operational batch. The release includes its result artifacts, typed inquiry/terminal history from earlier attempts, and retained formalization drafts, including drafts that ended in gaps. Incomplete batches cannot release favorable partial results. Permanently failed batches are retained for operator inspection; their eventual scientific terminal-batch release policy belongs to the freeze/evaluation integration and is not implemented here.

## Broker operations

| Operation | Caller | Purpose |
|---|---|---|
| `add_research` | Operator | Import a typed source or unverified record with validated ancestry |
| `record_research` | Worker with current lease | Append a role-permitted unverified record |
| `search_memory` | Worker with current lease | Read only the authorized snapshot and current private scratch |
| `inspect_memory` | Operator | Audit all retained records with view/query/scope/kind filters |
| `rebuild_memory` | Operator | Recreate the disposable index from validated immutable artifacts |
| `create_context` | Operator | Freeze permitted artifacts, epoch, role, and research time |
| `publish_development_feedback` | Operator | Atomically retain and release a closed development checkpoint for a later epoch |

Use the existing `rpc` command and request files described in the [runtime guide](README.md). Generic `add_source` and `put_artifact` reject the reserved research-record namespace, preventing an alternative write path from bypassing typed validation.

## Closed development feedback

`publish_development_feedback(root_epoch_id, execution_id, data_use_assessment_id, meaning_review_assessment_id, target_epoch)` implements the scoped exploratory feedback permitted by [D070](../docs/architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md). The host derives both original perspectives and every linked job, attempt, call, computation and known exposure. Earlier retained ideas still link their later attempts even when they were not a job's final result. Active or resumable work, unsettled calls, unresolved computations, unsealed or partially selected batches, protected ancestry and uncontrolled operations knowledge prevent publication. Exhausted blocked jobs remain blocked; generic `release_batch` rules do not change.

The operation requires an owned, complete development execution, its exact retained separate case-verification receipt and intact case blob, matching current data-use and independent meaning-review assessments, and a target epoch later than every source batch. One transaction writes four immutable artifacts: a `development-feedback-manifest/1`, a typed Journal observation, a separate Research Experience interpretation, and a `development-feedback-release/1`. It indexes the two records and records the publication event. All original artifacts remain unchanged. The manifest includes exact readable idea/gap records, complete cohort metadata and provenance; it does not paraphrase unsupported ideas or turn a technical gap into a negative market result. Oversized envelopes fail atomically under the existing one-MiB limit.

Only the exact manifest and its two typed records may be explicitly selected into later contexts through this grant. It does not release arbitrary controller results or raw source artifacts. Availability, epoch, current assessment status and technical revocation are checked on context admission and use; descendants inherit the complete exposure. New provider reservations also check inherited grants; acknowledgements and settlement of already admitted calls remain possible. A changed review/data-use status or technical revocation is a review trigger. Existing published bytes stay historical and readable to the operator. Identical publication retries return the same snapshot; changed inputs or release epoch for that execution are rejected.

The authority is `descriptive_development_feedback_only`. The Market Model remains empty. Scientific/assessment batch publication, independent confirmation, calibration, economic usefulness and live-capital authority are not supplied by this operation. Tests of this boundary use explicitly synthetic computation metadata and mock only the existing assessment inspectors; actual provider/review/data-use evidence requires a separately recorded integration check.

## Persistence and migration

The coordination schema remains version 1; an independently versioned `research_meta` extension records research-memory version 1. The extension adds a disposable `research_records` index referencing the original artifact table. On an existing registry, initialization stages a complete SQLite backup, verifies integrity and matching database contents, flushes it, and atomically places `before-research-memory-v1.sqlite3` before installing the extension. An existing corrupt or mismatched snapshot fails closed. It is not overwritten or treated as a valid backup by filename alone.

Replay verifies artifact hashes and record schemas before replacing the index inside a transaction. Startup verifies the projection against immutable records. Existing source bytes and frozen contexts are not rewritten. Actual subprocess termination tests cover committed-versus-uncommitted journal writes; restored backups preserve the projection. This does not establish power-loss durability on every filesystem. External large-blob lifecycle and scientific schema migrations remain later requirements.

## Verification scope

The [memory acceptance tests](../tests/test_memory.py) cover corrections and conflicts, ancestry, permissions, time, private scratch, retries, host observations, roles, reserved namespaces, complete operational release, migration backup failure, replay, process termination, and restoration. The [runtime tests](../tests/test_local_runtime.py) additionally exercise authenticated HTTP and the standalone demonstration.

An independent read-only review reproduced the migration-backup and same-attempt reference defects, then rechecked their fixes. No unresolved defect was found within its inspected boundary. This is bounded implementation evidence, not scientific validity, full framework isolation, or a security certification. Test evidence and remaining work are tracked in [implementation progress](../docs/reviews/implementation-2026-10-25/progress.json).
