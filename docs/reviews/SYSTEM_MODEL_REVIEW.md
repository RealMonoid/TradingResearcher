# System model reconstruction and documentation review

Date: October 22, 2026. Status: review and proposed remedies only. No scientific decision, lifecycle, or repository instruction is changed by this report.

## Question, review base, and limits

Can the existing documentation support a coherent model of the framework's goals, research flow, feedback, decision authority, and unresolved boundaries? Where did the assistant's earlier reasoning diverge, and what is the smallest justified remedy?

The fixed Git base is `2ab0cbedbec47b5bdef5a520b8aa9490baa7ac63`. The reviewed working tree also contains the earlier, uncommitted instruction intervention: AGENTS.md, Current State, and the session-understanding experiment. Those additions are evaluated as an intervention, not used as proof that the original documentation already contained their wording. The architecture documents 00-12 are unchanged from the Git base. A pre-review hash inventory covers all 51 existing tracked and nonignored untracked files.

Reviewed: README, repository instructions and Current State; the problem definition, master architecture, definitions, requirements, scientific evaluation, engineering review, blueprint, roadmap and open register; all 67 decision dispositions and all 47 rejection reasons/scopes; requirement traceability; targeted original messages for historical-first research, memory feedback and adversarial elimination. The current user's clarification supplies the explicit dual acceleration objective. The earlier experiment's assessment and retained report were also inspected.

This is a source cross-check by the same assistant, not an independent-person audit, a formal consistency proof, or a new session experiment. It does not re-audit every historical acceptance attribution or the unavailable source material. The [Source Audit](../architecture/00_SOURCE_AUDIT.md) still applies. The inspected code-review skill targets code diffs and issue-tracker specifications; it was not applied to this architecture reconstruction.

## Overall finding

**A coherent conceptual model is reconstructable, provided unresolved boundaries remain explicitly unresolved. A complete, unambiguous executable specification is not yet reconstructable.**

The central design does not require every hypothesis to wait years for forward confirmation. It combines broad, historical-first research with restricted claims about independent evidence. It permits useful rejection, failed attempts, qualified experience and further research before strong confirmation. The documentary problems below make that whole harder to recover, but do not excuse ignoring the clear historical-first and memory decisions.

## Reconstructed whole

### Goals and success

The core goal is autonomous, nontrivial LLM invention, faithful operationalization, and independent deterministic evaluation. The user's October 22 clarification adds an explicit coequal framework success objective: substantially accelerate both hypothesis discovery and testing. It is not satisfied by generating many ideas, rejecting many ideas, or finding a profitable backtest alone. The original documents also require technical validity, end-to-end calibration and eventual economic usefulness. Numeric performance, calibration, budget and abandonment criteria remain open.

The acceleration objective is directly authorized by the current user, not inferred from backend speed. Its missing canonical propagation is finding F1. See the [Problem Definition](../architecture/01_PROBLEM_DEFINITION.md), D001/D025/D028 in the [Decision Register](../architecture/02_DECISION_REGISTER.md), and [OPEN-11](../architecture/11_OPEN_DECISIONS.md).

### Research flow and exits

The researcher receives a permitted, versioned context containing data, qualified knowledge, experience and available capabilities. Independent perspectives use the same allowed epoch snapshot, with isolated reasoning state. Discovery can start from observations, mechanisms, questions, analogies or recombination. Scoped measurements and external research may refine a question; their information exposure follows the idea.

A free H_idea is preserved before attempting H_exec. Formalization must preserve meaning. Adversarial attacks can expose defects and lead to revision or abandonment before freeze. Missing data, language or evaluation capability preserves an unsupported idea for a possible later retry; it is not a negative empirical verdict. New features require certification independent of their implementation.

An executable candidate receives an evaluation policy independent of the generator. The exact claim, dependencies, data permissions, selection context and evaluation plan are committed before confirmatory outcome access. The backend calculates; the evidence engine applies the frozen criteria. A valid negative, inconclusive and supported result are different outcomes. Errors quarantine the affected execution. Post-result changes create descendants with inherited exposure rather than repairing an old claim in place.

Historical backtesting is the principal working environment. A long historical sample can be evaluated without waiting for its calendar duration to elapse again. Fresh confirmation is a separate constrained resource, with allocation among candidates. Historical research does not automatically earn the strongest evidence label. The exact state-machine representation and admissibility/status rules still require OPEN-01/05/12; this description does not approve them.

This is a branching research process, not a requirement that every idea become a supported claim, a strategy, or a live position. Sources: [Master Architecture](../architecture/06_MASTER_ARCHITECTURE.md), [Scientific Evaluation](../architecture/07_SCIENTIFIC_EVALUATION.md), D002-D007/D013-D016/D023/D036/D039, and [M0101](../../sources/full_conversation.md#m0101--user), [M0106](../../sources/full_conversation.md#m0106--assistant), [M0210](../../sources/full_conversation.md#m0210--assistant) with acceptance in [M0211](../../sources/full_conversation.md#m0211--user).

### Feedback and learning

Four distinct memories prevent one kind of feedback from acquiring another kind of authority:

| Memory | What it preserves | What its use permits |
|---|---|---|
| Research Journal | Events, attempts, outputs, failures and provenance | Reconstruct what happened, including unsuccessful work |
| Market Model | Qualified claims, their evidence, dependencies and limitations | Use appropriately qualified market knowledge |
| Research Experience | Search heuristics and interpretations of research trajectories | Change future search without upgrading empirical evidence |
| Policy Experience | Policy construction and operational observations | Improve policy research and monitoring within their authority |

Thus lack of fresh confirmation does not imply absence of all learning signals. A failed attempt can inform a search heuristic. Whether that heuristic actually improves future research remains an empirical question; permission to use feedback is not proof of learning efficacy. Retrieved memories carry the exposure of their sources, and new knowledge snapshots enter later epochs. Material changes to the researcher itself use separate proposal, validation, approval and rollback governance.

Sources: D005/D014/D019/D026/D040, [DEF-025/030](../architecture/04_DEFINITIONS.md), and [M0166](../../sources/full_conversation.md#m0166--assistant), explicitly accepted in [M0167](../../sources/full_conversation.md#m0167--user).

### Policies, operations and authority

Policy synthesis is another search, with explicit evidence-backed rules, untested assumptions and operational constraints. Entry, exit, sizing and management can be investigated without a compulsory positive-entry-signal ladder. Their combination requires its own evaluation. Evidence for components does not certify the combination or every subgroup where it might be used.

Scientific support, technical validity, current applicability and permission to deploy are distinct. Operational losses can trigger investigation, restrictions and registered future research; they cannot directly rewrite market evidence or generator prompts. Infrastructure revocation has typed dependency consequences, while genealogy alone does not invalidate a result. Logical roles need not be separate services or models, but the authority boundaries must be enforced.

| Actor | Authority | Boundary |
|---|---|---|
| Discovery / challenger / formalizer | Propose, attack and operationalize claims | Cannot assign empirical success or repair a frozen claim silently |
| Independent feature validation | Certify against approved semantics and independent cases | Cannot let the implementer certify itself |
| Registry, backend and evidence engine | Commit requests, execute, classify under approved rules | Cannot invent favorable criteria or deployment permission |
| Curator / policy builder | Interpret qualified results, propose heuristics and policies | Cannot turn interpretation or component support into new evidence |
| Authorized governance / user | Approve material changes and deployment constraints | Cannot erase prior trials or information exposure |

Sources: [roles and rights](../architecture/06_MASTER_ARCHITECTURE.md#roles-and-rights), D009/D010/D017/D020/D021/D026/D037/D048 and [rejection scopes](../architecture/03_REJECTED_DECISIONS.md), especially REJ-008/010/027/028/030/038/043. Routine certification authority remains OPEN-14; no blanket human approval rule for every research action is inferred.

## Findings and counterchecks

### F1. The stated acceleration goal is not integrated into canonical success and traceability

**Confirmed documentation gap relative to the current explicit user requirement.** The original Problem Definition's success section specifies faithful execution, calibration and economic usefulness. Requirements mention latency and throughput as unresolved nonfunctional quantities, and D028 treats them as diagnostics. Neither makes accelerated discovery AND testing a coequal framework acceptance objective. The new AGENTS/Current State paragraphs do, but those are the instruction intervention and descriptive handoff, not the canonical objective/requirement chain.

Countercheck: performance is not wholly absent. Backend speed, cost monitoring and diagnostic throughput exist. The gap is their relation to overall success, not a missing word or missing numeric target alone. The archive's incomplete provenance prevents asserting that the original private project never contained this goal.

Consequence: a reader can reconstruct a careful scientific validator while underweighting why the research workflow is being built. Evidence: [success and non-goals](../architecture/01_PROBLEM_DEFINITION.md#success-and-non-goals), [requirements](../architecture/05_REQUIREMENTS.md), [traceability](../architecture/12_TRACEABILITY_MATRIX.md), and the current user's clarification.

### F2. The current architecture is a qualified reconstruction, not a single settled lifecycle

**Confirmed, already disclosed semantic incompleteness.** The exact preserved lifecycle includes COLLECTING_PROSPECTIVE_CASES. D013/D053 supersede prospective-only primary research, while DEF-016, D067 and OPEN-01 explicitly leave its versioned replacement unresolved. Reading the old transition list alone produces the wrong operating model; silently translating it into a new executable state machine would also be wrong.

Countercheck: this is not an undisclosed decision to wait for forward data, nor proof of mutually incompatible project goals. The precedence is documented. What is absent is the approved operational reconciliation. Fixed-horizon and sequential evaluation likewise specify boundaries, but do not supply a universal early-stopping algorithm. Evidence: [definitions](../architecture/04_DEFINITIONS.md), D053/D067 and [OPEN-01/05](../architecture/11_OPEN_DECISIONS.md).

The other substantive open semantic boundaries are also already named: subgroup evidence transport (OPEN-02), family-rate interpretation (OPEN-03), applicability propagation (OPEN-13), and routine certification versus material-change approval (OPEN-14). They stop affected claims or automation, not all useful discussion or research design. OPEN-04/06-12 specify further language, data, infrastructure, budget and risk choices. Source completeness remains OPEN-15.

### F3. The central flow underrepresents early exits and their feedback

**Confirmed integration/presentation gap; not an absent architectural capability.** The Master Architecture shows formalization/challenge followed by executable/gap branching, then freeze, execution, evidence and journal. There is no explicit abandonment branch from challenge, and the gap node has no return to the journal/experience path. In the blueprint, IF-08's explicit publisher is CMP-06 with qualified evidence; it does not spell out the corresponding publication path for a pre-freeze abandoned idea or capability failure. The worked lifecycle also emphasizes completed evaluation.

Countercheck: CMP-07 explicitly owns append-only events, D007 retains errors, D019 permits experience, D036 permits pre-freeze attacks, and DEF-011 retains failures. These are sufficient to recover the intended behavior. Missing arrows do not repeal those decisions. The defect is that the principal system explanation does not itself show how these parts complete the loop.

Consequence: a reader can mistakenly equate feedback with completed empirical confirmation, although the individual documents reject that equation. Evidence: [main information flow](../architecture/06_MASTER_ARCHITECTURE.md#main-information-flow), [interface contracts](../architecture/09_IMPLEMENTATION_BLUEPRINT.md#interface-contracts), and M0166/M0210 above. This is a plausible contributor to misunderstanding, not a demonstrated causal explanation of model behavior.

### F4. The earlier instruction intervention did not establish the cause or the remedy

**Confirmed limitation of the prior investigation.** The retained [assessment](session-understanding/assessment.json) states that the original forward-waiting error was not reproduced even in the baseline. Final revised instructions met 4/5 task criteria sets, with narrow omissions and no observed critical errors. They were tested in fresh, task-directed probes, whereas the original failure arose during a continuing critique discussion.

Countercheck: those probes supply evidence about their particular outputs, and the report honestly records partial results. They do not show that the previous AGENTS caused the failure, that documentation was not loaded, or that the new clauses produce a general system model. Adding another incident-specific instruction is therefore not the justified next step. Actual context injection, retention after compaction, and conversational anchoring remain unverified.

## Where the earlier assistant reasoning diverged

| Earlier reasoning problem | Reconstruction-based correction |
|---|---|
| Treating the time needed for strong fresh confirmation as the timescale of hypothesis testing generally | Historical-first exploration, attacks and qualified evaluation can proceed on existing observations. Data span, outcome horizon, compute time and future waiting are different quantities. |
| Letting the fresh-evidence bottleneck imply that the learning loop is broadly blind | Experience may guide future research without certifying market truth. Its efficacy must still be measured, but D019 explicitly permits this feedback. |
| Discussing early death without separating its meanings | Abandonment before freeze, valid empirical rejection, inconclusive evidence, capability gaps and technical failure have different consequences. A probabilistic claim is not universally disproved by one failed episode. |
| Responding to each correction with another local reminder | The missing step was integrating goals, branches, feedback and authority before assessing the criticism. Correct factual fragments did not establish that integration. |

The observable failure is a mismatch between the earlier conclusions and the documented whole. The available evidence cannot determine whether a particular rule was absent from active context, retrieved but underweighted, or displaced by the critic's framing. Claiming a specific internal mechanism would exceed the evidence.

## Manual cross-system consistency walkthrough

These are documentary reasoning checks, not executed framework tests or fresh-agent efficacy results. They test consequences across components, rather than requiring an answer to repeat particular words.

| Scenario | Consequence derived from the model | Governing boundary / result |
|---|---|---|
| A candidate fails a concrete pre-freeze challenge | It may be revised or abandoned; retain trajectory and exposure; no frozen primary verdict is fabricated | D036/D019; coherent intent, F3 records incomplete central routing |
| A new idea cannot be expressed with existing features | Preserve H_idea and gap; request extension/certification; do not substitute an easier claim | D002-D004; exact language/approval policy blocked by OPEN-04/14 |
| Historical execution meets a frozen negative criterion | Record a valid negative with origin and limitations; no requirement to wait the sample's years again | D013/DEF-018; exact status implementation still OPEN-01/05 |
| An interim weak result appears before a fixed-horizon trigger | Do not convert it opportunistically into the primary negative; a valid frozen sequential rule is a different case | DEF-021/022; no universal early-rejection promise |
| A certified feature used by several results is revoked | Append invalidation and trace affected hard dependencies; retain old results and exposure; review dependent policies appropriately | DEF-015/D009; detailed applicability propagation OPEN-13 |
| A supported aggregate is used for a narrower policy population | Set inclusion alone does not settle evidence transport; the whole policy still needs its own trial | D010/D066; affected support claim blocked by OPEN-02 |
| Live policy losses appear | Diagnose operational/policy causes and register future research; do not directly reverse market evidence or rewrite prompts | D020/D037; deployment limits OPEN-10 |
| A new prompt is proposed after disappointing research | Separate experience retrieval from material researcher modification; evaluate and approve the latter; rollback keeps exposure | D019/D026; no automatic improvement authority |
| A completed trade path is reused to select an entry condition | Full-path extrema cannot become entry-known information; exploration reuse is not new confirmation | D045/D046/REQ-026; compatible with efficient reusable computation |

No additional unavoidable conflict was identified in these paths after applying documented precedence and leaving the named open boundaries unresolved. This bounded result is not a proof that every possible path is consistent.

## Smallest proposed remedy

**Repair the existing architectural explanation before changing agent behavior again.** Do not create another permanent competing summary or an expanding list of incident-specific prohibitions.

1. **Complete the existing Problem Definition.** State both goals and distinguish framework, hypothesis and policy success. Record the current user's acceleration clarification in the decision register and structured companion, and trace it to a requirement and future acceptance criterion. Keep numerical targets and the comparison design explicitly open. Update the existing traceability/open-success entries consistently; this is propagation of the user's stated objective, not a request to approve it again. A rejected comparator generator is not implicitly authorized.
2. **Make the existing Master Architecture explain the whole loop.** Show pre-freeze abandonment, retained gaps, valid negative/inconclusive outcomes and errors returning to their appropriate journal/experience destinations. Explain the separate market-knowledge, research-experience, policy and governed-improvement loops. Show where historical research occurs and where stronger confirmation is required. Add a concise current-versus-legacy note at the lifecycle entry point and mark unresolved boundaries where they interrupt the flow. Align the existing blueprint's event-publication description; do not invent executable status values or silently resolve OPEN-01.
3. **Then simplify AGENTS.** Replace the recent incident-specific system-model bullets with a short instruction to reconstruct the current system model from the existing goal/architecture documents before systemic judgments, consult affected authority/open items, and reconnect the requested task to that model. Preserve existing source precedence, change-control and small-edit exceptions. Retain the earlier experiment as historical evidence, including its failures. No extra memory service, mandatory agent topology or new runtime is warranted.

The documentary integration can be proposed independently of resolving every open scientific issue. An approved, implementable historical/sequential lifecycle is a separate OPEN-01/05 decision package: alternatives, transition meanings, evidence-origin rules, versioning, acceptance cases and rollback must be reviewable before adoption. Similar scope-specific decisions are required before implementing OPEN-02/03/14. A summary must not make those choices on the user's behalf.

### How to assess that remedy later

First review the revised existing documents for whether a reader can reconstruct the whole above without consulting incident-specific instructions. Then freeze a small assessment covering causal consequences across discovery, failed formalization, evidence reuse, revocation, policy scope, operational feedback and material improvement. Include unfamiliar tasks and an ongoing-critique setting, not only restatements of the original mistake. Assess source-grounded decisions and propagation consequences rather than mandatory keywords.

Compare the original and revised document sets under the same conditions, preserve all outputs, and distinguish fresh-session loading from long-conversation retention. If the original failure again does not reproduce, report that limitation instead of claiming a cure. This assessment is proposed, not run here. No instruction-only intervention can establish reliable comprehension from a handful of favorable answers.

## Change and verification record

Only this report is added in this review. The earlier AGENTS.md and Current State changes and the session-understanding experiment are left unchanged. No source archive, canonical decision, definition, requirement, application code or scientific policy is modified.

Validation covers local report links/anchors, cited decision identifiers, source-manifest hashes/sizes, byte preservation of the 51 pre-existing files, equality of architecture documents 00-12 to the fixed Git base, and whitespace. These integrity checks do not validate the framework scientifically or prove future-session comprehension. Exact executed outcomes are reported with the delivered review; no application or new behavioral test is claimed.
