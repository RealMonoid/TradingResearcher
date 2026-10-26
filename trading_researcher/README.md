# Local coordination runtime

This standard-library Python implementation provides a local task queue, immutable context/artifact storage, authenticated worker capabilities, deterministic operational completion checks, and bounded time/event triggers. It needs Python with SQLite support; no broker, vector database, agent framework, package installation or paid model account is required for the included demo.

The user approved this bounded implementation on October 24, 2026 with the exact instruction **"freigabe, implementiere das so"** after the local Python/SQLite controller proposal. Source identifier: `SESSION-2026-10-24-LOCAL-COORDINATION`. This implements part of D005/D014/D019/D030/D078/D079/D082/D084. It changes no scientific contract, decision status, evidence threshold or deployment authority. The historical source archive is unchanged.

## Run the working example

Run from the repository root in PowerShell:

```powershell
python -B -m trading_researcher demo --directory .trf-runtime/demo
python -B -m trading_researcher verify --directory .trf-runtime/demo
python -B -m unittest discover -s tests -v
```

The demo requires a new or empty directory. It starts a temporary loopback controller, registers a calculator worker, freezes synthetic decimal inputs, queues a job, executes it over HTTP, verifies the submitted sum, writes `demo-result.json`, and stops the server. Its values are synthetic infrastructure fixtures, not market observations. Repeated demos need a different directory. Runtime data under `.trf-runtime/` is ignored by Git.

The runnable entry point is [__main__.py](__main__.py). [coordination.py](coordination.py) owns transactions, [server.py](server.py) exposes loopback RPC, [worker.py](worker.py) runs trusted handlers, [checks.py](checks.py) validates submissions, and [codec.py](codec.py) defines bounded canonical JSON. [Verification evidence](../docs/reviews/LOCAL_COORDINATION_VERIFICATION_2026-10-24.json) records the tested environment, exact commands, file hashes and limitations.

## Keep a controller running

```powershell
python -B -m trading_researcher init --directory .trf-runtime/local
python -B -m trading_researcher serve --directory .trf-runtime/local --port 8765
```

`serve` remains in the foreground until Ctrl+C. The controller alone opens the registry for writing. A second controller for the same directory fails. Its service loop advances due time triggers and expires abandoned leases; after restart it catches up missed occurrences within each schedule's declared limit. This change installs no Windows service, Codex reminder or automatic startup entry. No process must remain running after the demo.

The operator key is stored in `.trf-runtime/local/operator.key`, never printed by initialization. The local operator is trusted and may inspect all records. Keep keys and the registry out of model tool access. Worker registration returns its secret once to the trusted wrapper; save it in an operator-managed file, not a prompt or shared memory. Preserve keys separately when making a database backup. Missing or mismatched keys fail closed; no silent replacement grants new authority.

Use the Python API from another trusted process to provision real queue entries. This example contains no model/API calls:

```python
from pathlib import Path
import os
import time
from trading_researcher.server import Client

directory = Path('.trf-runtime/local')
admin = Client('http://127.0.0.1:8765', (directory / 'operator.key').read_text().strip())
worker = admin.call('register_worker', name='calculator', role='executor',
                    capabilities=['decimal-sum/v1'])
fd = os.open(directory / 'calculator.key', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as stream:
    stream.write(worker['token'])
source = admin.call('add_source', body={'values': ['0.1', '0.2']},
                    data_class='development', exposure=['synthetic-example'])
context = admin.call('create_context', role='executor', epoch=1, artifact_ids=[source['id']])
spec = dict(kind='decimal-sum/v1', context_id=context['id'], purpose='Synthetic sum',
            allowed_workers=['calculator'], max_attempts=2, lease_seconds=10,
            deadline=int(time.time()) + 300, dependencies=[])
job = admin.call('enqueue', key='sum-example', spec=spec)
print(job)  # Job identity only; never print the credential.
```

Then run a bounded worker in a separate terminal:

```powershell
python -B -m trading_researcher worker --url http://127.0.0.1:8765 --token-file .trf-runtime/local/calculator.key --max-jobs 1 --idle-seconds 10
```

The example lease, timeout and attempt counts are operational demonstration settings, not scientific defaults. Leases require at least three seconds because the controller clock uses integer seconds; their initial effective duration can be less than the declared value by under one second. Registration of an existing identity fails instead of overwriting it. Job keys are idempotent only for identical specifications. A changed purpose, context or budget under the same key is a conflict. The worker stops after its job count or idle limit; an installed handler must itself return or implement a provider timeout. A stuck handler does not retain write authority beyond the task deadline. External side effects are not made exactly-once by a queue lease.

## Task and authority rules

| Mechanism | Implemented behavior |
|---|---|
| Identity | Controller resolves the actor from a secret bearer capability. Workers cannot supply another creator, invoke operator methods, inspect the queue or enumerate other workers' artifacts. |
| Claim | One running job globally in this initial sequential implementation. The first eligible job keeps the host's order; later jobs cannot bypass it merely because another worker polls first. Required capabilities and explicit worker allowlists are checked before enqueue. |
| Ownership | Every worker read/write checks identity, job, attempt generation, state, lease and deadline in the same SQLite transaction. Heartbeats never extend the deadline. An old attempt cannot write after reassignment even to the same identity. |
| Context | Immutable content-addressed input snapshots. Adding an artifact later does not expand an existing snapshot. Worker results inherit the entire supplied context, including metadata ancestry, regardless of which citations the worker selects. |
| Block | `block` retains reason, needs and retry condition; it is not successful completion. An operator may `resume` the same job after resolution, within the original budget, allowing another preauthorized worker to claim it. |
| Completion | `submit` invokes an installed, versioned check in the controller. A worker's `done` field is insufficient. Rejected output and failed/expired attempts remain inspectable. Repeated submission of the identical terminal result returns its prior outcome. |
| Release | Operator-created multi-job batches must be sealed before execution. `release_batch` succeeds atomically only after all jobs complete and only for a later epoch. A blocked batch remains unavailable to discovery. This is an operational barrier, not the scientific allocation/release engine. |
| Evidence | Every response declaring completion has `scientific_authority: false`. A negative or inconclusive source record may be copied correctly and complete a reporting job without becoming positive evidence. |
| Persistence | SQLite transactions, foreign keys, FULL synchronization, immutable envelope tables and a hash-chained event log; checked startup, idempotent job creation, same-job retries and SQLite backup. The hash chain detects inconsistencies; it is not protection from a local administrator who can rewrite the database. |

Current completion checks are deliberately explicit:

- `draft/v1`: validates the presence of `finding`, `interpretation`, `uncertainty` and `next_action`. This certifies a structured draft only; its claims may still be wrong. There is no built-in model worker for this kind.
- `source-report/v1`: requires exact copies of all referenced input record bodies, with source IDs. It rejects invented or omitted values; it does not establish that the supplied sources are true.
- `decimal-sum/v1`: computes a sum from finite decimal strings and independently checks the result using exact rational arithmetic. It verifies the submitted total and count. This is a narrow numeric reference handler, not a universal verifier for numbers in natural-language reports.

Unknown checks create a visible blocked job. New checks and handlers are installed trusted code, not arbitrary worker-supplied programs. New scientific meanings still require D008/D026 review. No LLM judge has authority to mark a market hypothesis successful. Free-text drafts are retained as unverified drafts; unsupported text is not silently deleted from the audit history.

## Operator calls and triggers

`Client.call(op, **args)` is the public Python seam. Alternatively, write `{"op":"status","args":{}}` to a UTF-8 JSON file and run:

```powershell
python -B -m trading_researcher rpc --url http://127.0.0.1:8765 --token-file .trf-runtime/local/operator.key --request status.json
```

`status` lists compact job summaries. `inspect(job_id=...)` returns one specification and attempt history. Both accept `limit` (1 to 50, default 50) and `after` (initially 0); use the returned `next_cursor` as `after` until it is null. `get_artifact(artifact_id=...)` gives the operator original source/output bodies, including rejected ones. Worker capabilities cannot call those methods. `verify` checks registry integrity. Offline `verify --directory ...` requires stopping the controller first, because it takes the same writer lock. Requests and responses are limited to 1 MiB; a response that cannot be serialized rolls back its transaction rather than committing an undeliverable mutation. Smaller page sizes can be used for unusually large attempt details.

Schedules reuse a frozen spec and an absolute deadline; they never create a fresh resource budget implicitly:

```python
# Choose one trigger type per schedule; examples use the spec already created above.
admin.call('add_schedule', key='once', spec=spec, at=int(time.time()) + 30, max_fires=1)
admin.call('add_schedule', key='event-example', spec=spec,
           event_type='synthetic.ready', max_fires=2)
admin.call('emit', event_type='synthetic.ready', event_id='fixture-revision-1')
```

Repeat delivery of that event ID under the same schedule returns the original job. Time schedules may set a positive integer `interval`; a bounded `max_fires` is mandatory. One tick catches up at most 64 due occurrences; subsequent ticks continue. These are UTC Unix-second operational triggers. They do not infer completed market outcomes, select a diagnostic method, implement local-calendar weekly reports, deliver messages or fulfill D087/D088. Their future event producers and delivery adapters must enforce those contracts.

For a complete batch, call `create_batch(key=..., epoch=...)`, include its ID as `spec['batch_id']` when enqueueing all members, and then call `seal_batch(batch_id=...)`. After all members complete, `release_batch(batch_id=..., target_epoch=...)` enables their artifacts in later explicitly created contexts. Timer/event schedules cannot append jobs to a frozen batch.

For a complete backup, use `backup_bundle(destination=absolute_new_directory)` or the CLI `backup-bundle` command. The bundle includes a consistent database snapshot and all committed external blobs with a verified manifest. Restore with `restore-bundle --bundle <backup> --directory <new-registry> --operator-key-file <preserved-key>`; the destination must be new and the separately preserved key must match. The database-only `backup(destination=absolute_new_database_path)` remains available only when no blobs are committed. Worker token files are also separate from backups. Restored pending work retains attempts, deadlines and exposure; restore does not reset research history. Supported schema migrations preserve a database checkpoint; unknown versions are refused. See [storage and recovery](STORAGE.md) for commands and boundaries.

## Verified boundary and remaining work

The tests use temporary real SQLite files, concurrency, HTTP requests, a real subprocess crash, recovery and backup restoration. They cover expired ownership, forged identity, frozen input access, inherited exposure, incomplete-batch release denial, incorrect completions, duplicate delivery, deadlines, trigger restart and an end-to-end synthetic CLI run. They are partial infrastructure support for the [acceptance matrix](../docs/architecture/12_TRACEABILITY_MATRIX.md), not completion of TEST-01 through TEST-30.

The trusted local operator, OS account and installed Python code can access the filesystem. Loopback authentication restricts the exposed tool surface; it does not isolate a worker that also has an unrestricted shell or filesystem access under that account. The original coordination demo launches no model. The later [OpenAI adapter](OPENAI.md) exposes only authorized RPC tools, freezes model/prompt versions and retains cumulative tokens and conservative cost accounting. Direct agent messages are not required by this implementation and are not prohibited as an architecture rule; any added channel must preserve the same information boundaries.

The October 25 continuation adds the [memory foundation](MEMORY.md), [provider-neutral researcher loop](RESEARCHER.md), [formalization drafts](FORMALIZATION.md), [reference calculations](OUTCOMES.md), [implementation certification and retained replay](CERTIFICATION.md), and [immutable external storage](STORAGE.md). Small envelopes remain in SQLite; larger payloads use verified content-addressed files. Tests cover process exits around blob commitment, corruption quarantine, complete backups and restoration, and interrupted certificate recovery. [Current implementation evidence](../docs/reviews/implementation-2026-10-25/progress.json) distinguishes these additions from the original coordination checkpoint.

[Data snapshots](DATA.md) bind normalized row bytes, catalogs and qualified acquisition assertions. The operator can register them through RPC; the window loader is a trusted-host seam with no worker-facing byte-read operation. Grid/type/coverage checks and source integrity do not establish historical publication truth or scientific readiness.

The [Binance acquisition commands](BINANCE.md) retain exact monthly source bytes and provider checksum files in separate acquisition directories. They verify container, time and quantity structure, preserve failed sources and expose qualified availability scenarios. Source ingestion into bound scientific manifests and feature certification still require the corresponding downstream checks.

[Raw measurement certification](FEATURES.md) now binds the existing Binance fields to exact owned source replay with qualified definitions and host-issued certificates. General composition/dependency certification, point-in-time market-data validation, complete FrozenManifest/TrialRecord schema, bound scientific execution, calibrated evaluation, scientific memory publication, temporal monitoring, user-facing delivery and live trading remain incomplete. Python distributions are fingerprinted rather than archived. Power-loss durability, hostile same-account isolation, maximum-size throughput, representative live research behavior and economic usefulness have not been tested. A bounded four-call OpenAI transport/tool-loop probe on synthetic context passed; its usage reporting is documented in [OPENAI.md](OPENAI.md).

## Bound development computation

[Bound reference computations](BINDING.md) provide operator-only compile-hypothesis and execute-development commands and equivalent RPCs. They preserve exact completed formalization/data/certificate identities and retained calculator versions, load required warmup, validate returned cases and keep descriptive results outside scientific authority. Assessment execution, semantic approval and scientific freeze remain pending.

## Historical policy preparation

The [auxiliary research handoff](AUXILIARY_RESEARCH.md) connects formalization and a separate meaning-review worker to the same epoch call, token, time and currency budgets. `run_auxiliary_once` uses the existing trusted adapter boundary and exact retained inputs. Reviews keep actual independent model judgment unverified; simulated or relabeled live responses cannot supply scientific approval.

[Historical evaluation policy](EVALUATION_POLICY.md) provides exact rational policy helpers and the operator RPC `prepare_evaluation_plan`. Drafts bind actual compiled/data/feature versions and intact development diagnostics, retain an executed source capsule and expose pending scientific gates. The existing RPC CLI can invoke this operation. The [joint stationary-bootstrap candidate](STATIONARY_BOOTSTRAP.md) adds `run_development_bootstrap` for exact plan/case-bound exploratory resampling, retained inputs/draws and separate process replay. Statistical calibration, information targets, actual independent semantic review, scientific batch allocation and freeze remain unfinished.

Admitted plan requests now retain their exact inputs and source bytes before any calculation child starts. After an interruption, reuse the same key and unchanged arguments to retry the retained version; use a new key to request changed arguments or a new calculation version. `inspect_bound_computations` returns `retained_input_id`, retrievable through `get_artifact`. Failed attempts survive restart and complete backup/restore without becoming scientific results.

`run_development_bootstrap` also accepts the explicit optional `mc_policy` described in [Monte Carlo boundary diagnostics](MONTE_CARLO.md). The host binds its settings before resampling and supplies effect/direction from the owned plan. The resulting stability assessment remains an uncalibrated development diagnostic with no scientific classification permission.

The same operation uses the [exact integer acceleration](STATIONARY_BOOTSTRAP.md#exact-arithmetic-acceleration-for-simulation-work) for integral sufficient statistics without changing its public interface or sampling law. Nonintegral values keep rational arithmetic. Equality checks and paired workload measurements are prerequisites for the planned repeated simulations, not evidence that information planning or calibration is complete.

`prepare_information_diagnostics` adds [owned development nuisance measurements](INFORMATION_DIAGNOSTICS.md). Exact plan/execution references, explicit lags and a total time cap are retained before isolated calculation and separate replay. Full-grid contributions are stored as a blob; summaries retain unknown conditions, unavailable outcome pairs and degenerate-rate gaps. The result is a development artifact with no fitted world, N_min or scientific authority.

`run_population_world` adds [owned binary response/mask worlds](POPULATION_MODELS.md) using the matching diagnostics and plan-assigned effect scenarios. Exact rational rates and random choices, explicit stress assumptions, source-mask provenance and an artificial calendar are retained before generation and separately replayed. This is an estimator-level simulation input; fitted model adequacy, the complete power grid, N_min, final calibration and scientific admission remain outstanding.

`prepare_information_study`, `advance_information_study` and `inspect_information_study` connect those components into an [owned finite development study](INFORMATION_STUDIES.md). All world identities/seeds are retained before calculation; an atomic event ledger reserves and settles a shared compute/storage budget. Technical failures remain separate from completed information abstentions. Retained source and separate replay support resumption between settled worlds; uncertain orphan work blocks replacement. Complete-grid candidate reporting still grants no N_min, scientific readiness or calibration authority.
