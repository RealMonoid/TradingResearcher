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

Use the existing `rpc` command and request files described in the [runtime guide](README.md). Generic `add_source` and `put_artifact` reject the reserved research-record namespace, preventing an alternative write path from bypassing typed validation.

## Persistence and migration

The coordination schema remains version 1; an independently versioned `research_meta` extension records research-memory version 1. The extension adds a disposable `research_records` index referencing the original artifact table. On an existing registry, initialization stages a complete SQLite backup, verifies integrity and matching database contents, flushes it, and atomically places `before-research-memory-v1.sqlite3` before installing the extension. An existing corrupt or mismatched snapshot fails closed. It is not overwritten or treated as a valid backup by filename alone.

Replay verifies artifact hashes and record schemas before replacing the index inside a transaction. Startup verifies the projection against immutable records. Existing source bytes and frozen contexts are not rewritten. Actual subprocess termination tests cover committed-versus-uncommitted journal writes; restored backups preserve the projection. This does not establish power-loss durability on every filesystem. External large-blob lifecycle and scientific schema migrations remain later requirements.

## Verification scope

The [memory acceptance tests](../tests/test_memory.py) cover corrections and conflicts, ancestry, permissions, time, private scratch, retries, host observations, roles, reserved namespaces, complete operational release, migration backup failure, replay, process termination, and restoration. The [runtime tests](../tests/test_local_runtime.py) additionally exercise authenticated HTTP and the standalone demonstration.

An independent read-only review reproduced the migration-backup and same-attempt reference defects, then rechecked their fixes. No unresolved defect was found within its inspected boundary. This is bounded implementation evidence, not scientific validity, full framework isolation, or a security certification. Test evidence and remaining work are tracked in [implementation progress](../docs/reviews/implementation-2026-10-25/progress.json).
