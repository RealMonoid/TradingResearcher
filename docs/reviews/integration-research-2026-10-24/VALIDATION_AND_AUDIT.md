# Validation plan and research-deliverable audit

October 24, 2026. Scope: the [proposal](INTEGRATION_PROPOSAL.md), not implementation approval.

## Future implementation acceptance cases

These cases are **proposed and not executed** in this research task. They instantiate existing boundaries rather than claim full coverage of TEST-01 through TEST-30.

| Case | Counterexample or stimulus | Required observable result | Existing basis |
|---|---|---|---|
| I01 | The second discovery perspective asks for the first perspective's unfinished scratch or a hidden assessment record | Broker denies without leaking record existence/content through search metadata; both receive the same approved base snapshot | D005/D014/D077; TEST-04/13/18 |
| I02 | A search result reveals a failed assessment only as a snippet; a later summary omits that source | Actual returned context and descendants still inherit the assessment exposure; a new epoch/model label cannot reset it | D014/D070; TEST-13/28/29 |
| I03 | A free idea needs a feature or estimator outside certified semantics | Preserve original idea and exact capability gap; no invented measurement, silent approximation or scientific negative | D002/D003/D074/D084; TEST-02/03/26 |
| I04 | Valid JSON changes an outcome horizon, unit, missing-data meaning or decision-time availability | Semantic checks reject or request explicit resolution; schema validity cannot certify faithfulness | D004/D012/D074; TEST-02/03/11 |
| I05 | Model proposes a confident market claim or edits a memory summary to label itself successful | Store only a draft/interpretation; no evidence promotion, evaluator mutation or policy authorization | D001/D019/D080; TEST-01/16/17 |
| I06 | Concurrent freeze attempts reserve overlapping scientific allocation, or crash between manifest and allocation writes | Commit one consistent closure atomically; retain conflicts/attempts; retry cannot create fresh evidence or replication | D006/D078/D082; TEST-05/06/07/19 |
| I07 | Provider times out after acceptance; worker restarts; tokens/cost are uncertain | Attempt history and budget reservation survive; resolve or stop visibly; no claim of exactly-once billing or unknown cost as zero | D030/D077/D079; TEST-18/23 |
| I08 | An archived finding is contradicted, retired, stale or invalidated | Retrieval preserves distinct states and reasons; answer cites appropriate source/scope or abstains; history remains recoverable | D009/D019/D083; TEST-08/16/25 |
| I09 | An interval equals the practical boundary, a resample has an undefined denominator, or a favorable seed is suggested | Apply the frozen boundary and gap rules exactly; no selective reseeding or dropping failed draws | D075; TEST-05/20/24 |
| I10 | Dependent nulls, boundary effects, overlap, common shocks or heavy tails violate the claimed calibration | Report all worlds, error/detection rates and uncertainty; failed/unfinished profiles cannot certify the evaluator | D081; TEST-20/22/29 |
| I11 | Policy changes shared-cash order, exits or fills while using an old trade export | Require faithful resimulation or retain a capability gap; filtering the export cannot establish the counterfactual policy | D017/D021/D048/D076; TEST-09/20/24 |
| I12 | A new bar arrives before a longer outcome matures; duplicate/corrected batches or weekly report ticks occur | Only eligible mature outcomes advance a bound diagnostic checkpoint; corrections retain identity; reporting produces no additional scientific look | D087/D088; TEST-17/22/25 |
| I13 | Notification delivery fails or no diagnostic method is available | Durable pending work and failure reason remain; source-bound weekly status still describes the gap; no invented diagnosis or silent disappearance | D088; TEST-17/22/25 |
| I14 | A model/prompt/retrieval variant is tuned on evaluation results and then called independently validated | Record selection and exposure; evaluate a newly frozen version on an admissible separate assessment; keep all failed/pending variants | D026/D070/D081; TEST-21/28/29/30 |

For memory evaluation, create synthetic histories with known source IDs, contradictory versions, missing answers, time scopes and forbidden records. Score retrieval recall, source/answer fidelity, contamination, abstention, tokens and latency separately. Do not use trading holdout outcomes as a convenient prompt-tuning dataset. Exact acceptance thresholds beyond existing contracts belong in a predeclared development/evaluation plan; no universal percentage is invented here.

For scientific validation, preserve the existing contract's numeric calibration criteria. Narrow estimator calibration and full-process calibration are different scopes. Initial technical fixtures and model-free tests can establish plumbing and arithmetic; only a genuine freely generated idea can satisfy the connected-research slice.

## Concrete loophole review

This is a finite review of mechanisms actually present in the inspected code/proposal, not a claim that hypothetical exploits have occurred.

| Potential shortcut in this integration | Evidence and risk | Detection, rule and recovery |
|---|---|---|
| Rename an operational completed batch as scientific evidence | Current checks explicitly return `scientific_authority: false`; domain allocation/evaluation are absent | Require domain freeze and evaluator records. Keep operational status separate; implement the missing layer rather than changing a Boolean |
| Call a provider-connected demo the completed researcher | Current workers have two deterministic demonstration handlers | Require a free idea, faithful mapping and independent report. Label earlier milestones partial |
| Preserve only cited sources | Current broker ancestry is a useful starting point, but future retrieval/model observations add new exposure | Record every returned bundle and inherited context, including snippets and summaries. Rebuild affected provenance if incomplete; do not claim freshness |
| Treat four tables or an automatic summary as complete memory | Four logical memories have different write authority and retention requirements | Replay and authority tests plus realistic retrieval cases. Keep original records and conflicting versions |
| Treat an agent benchmark or self-critique as scientific validation | Vendor evals and reflection mechanisms serve different questions | Separate operational, statistical and economic reports; use independent scientific code |
| Borrow a paper's guarantee while omitting its assumptions | POPPER's conditional validity and training assumptions do not follow from an API call | Keep the adopted fixed-batch profile; retain unknown exposure. Any different method needs its own review and evidence |

These controls are incorporated into the proposal. No substantiated reason was found to replace the existing controller or require a new general-purpose “Brain.” That is a bounded design conclusion, not proof of global optimality or runtime security.

## Research deliverable completion matrix

| Requirement | Evidence | Completion claim |
|---|---|---|
| R1 System understanding first | [SYSTEM_MODEL.md](SYSTEM_MODEL.md), source-linked roles, normal/failure paths, feedback and code limits; reconstruction preceded external-source synthesis | System-level recommendation grounded in the current working tree; original source gaps remain |
| R2 Academic primary research | [SOURCES.md](SOURCES.md), seven works with inspected sections, claims and transfer limits | Targeted review complete; not an exhaustive literature review or new empirical study |
| R3 Anthropic and OpenAI sources | Four directly inspected sources from each provider, including current 2026 engineering guidance | Relevant provider mechanisms verified as documentation, not runtime compatibility |
| R4 Concrete best-fit options | Proposal sections 1–3: orchestration comparison, loop, memory records/retrieval and scientific pipeline | Reviewable preferred architecture with alternatives and authority boundaries |
| R5 Integration and validation plan | Proposal sections 4–8 and cases I01–I14 | Staging, costs, readiness inputs, affected decisions/requirements, versioning and rollback specified |
| R6 AI Psychiatry | Manifest-derived inventory in [research-state.json](research-state.json), observable evidence and finite loophole review | Applied as a task-control discipline; no claim of validated model or trading improvement |
| R7 Fresh checks and preservation | [verification.json](verification.json), review verifier and baseline hashes | Exact command results and preservation are recorded separately; no inference beyond their scope |

## Checks and unverified boundaries

The machine-readable [verification record](verification.json) is authoritative for commands actually run, exit codes, outputs and timestamps. [verify_review.py](verify_review.py) checks the new review's local links, control/requirement completion, original-file hashes, source inventory and Markdown whitespace. Existing runtime/documentation checks are recorded as bounded regression evidence. They do not execute cases I01–I14 as a complete integrated system.

Only files in this review folder are authored for the task. No canonical decision, runtime, source archive or existing user change is intentionally modified. The recorded baseline contains 94 preexisting files; the final comparison determines preservation rather than relying on Git status alone.

Unverified: actual model behavior and provider compatibility; effective retrieval quality; full data availability/rights and point-in-time validity; feature/backtest equivalence; scientific conformance and calibration; empirical market effects; realistic profitability; monitoring delivery; operational security beyond existing tests; implementation effort and efficiency gains. No credentials, market dataset, paid model experiment, capital action, notification or hosted deployment was initiated.

Next action: review the proposed P1–P4 implementation milestone and its explicit coverage. The current task ends with this researched proposal; implementation is a subsequent scope, not an omitted part of the research request.
