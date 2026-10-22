# Generator Feedback and Evaluation Contract

Version: 1.0, October 22, 2026. Normative specification under D069-D070 and REQ-028 through REQ-030; no runtime implementation or executed scientific experiment. This contract operationalizes existing memory, exposure, diagnostics and evaluation responsibilities. It does not replace the canonical lifecycle, definitions or open statistical policies.

## Purpose and authority

The economic objective is to generate hypotheses that can be used profitably after realistic costs and execution constraints. Beating quantitative firms, demonstrating universal superiority, and outperforming a systematic feature-search generator are not acceptance requirements. Statistical references within a claim, null calibration and realistic policy alternatives retain their existing roles. A supported market relationship is not automatically a profitable policy; the economic gate requires the separate policy evaluation already required by D010/D025.

Research starts with an unknown answer. A build or experiment entry gate checks whether the intended question can be investigated validly with the available resources; it must not require a prior positive result. D068's acceleration objective concerns research time/cost at preserved decision quality, not investment outperformance. Preparation and technical work can proceed without a positive economic result. Confirmatory use still requires the affected unresolved contracts to be settled.

The user authorized binding integration of the reviewed improvements into the specification, and explicitly selected specification work rather than runtime code. [D069-D070](02_DECISION_REGISTER.md#d069--economic-usefulness-without-a-superiority-prerequisite) record that current-session authority. Academic sources motivate the design below; they do not supply user authority, a market result or a universal statistical default.

## Feedback contract

CMP-07 owns the retained feedback record and heuristic interpretation; CMP-01 enforces availability, exposure closure and later-epoch retrieval. CMP-03/04 own technical specification/certification outcomes. CMP-06 alone assigns scientific outcomes under the frozen evaluation policy. CMP-11 reports diagnostics. CMP-12 governs material changes. These are logical responsibilities within the existing modules, not new services.

| Feedback input | Permitted use | Required qualification |
|---|---|---|
| Independent technical check, formalization gap or execution error | Diagnose repeat errors and capability needs; guide later search or repair | Reference the check/specification, actual result and validity. Technical failure is neither market falsification nor support. |
| Known analogue, duplicate indication or structural concentration | Inspect search coverage and redundant effort | Record method, corpus/version and uncertainty; resemblance is not proof of equivalence or uselessness. |
| Exploratory query or exposed historical result | Develop hypotheses and qualified search heuristics | Preserve complete source/exposure ancestry; do not promote it to independent confirmation. |
| Valid qualified primary or replication evidence | Update qualified market knowledge and inform later search | Preserve evidence origin, scope, uncertainty, frozen policy and dependencies; later descendants inherit exposure. |
| LLM reflection or causal interpretation | Propose a heuristic, counterexample or research question | Label as an interpretation, identify its supporting observations or absence thereof, and retain alternative explanations. Self-confidence grants no evidence or demonstrated-improvement status. |
| Registered operational observation | Enter Policy Experience or a later research question | Preserve the operations firewall; no direct change to research truth or protocols. |

Feedback availability, changed search behavior, procedural improvement and improved economic discovery are four distinct observations. A useful training/development input need not be an individually significant market finding. Conversely, accumulating feedback or changing behavior does not establish improvement. A later evaluation must measure the particular improvement claimed.

### Minimum retained information

Extend the existing immutable artifact envelope, Journal/Experience records and interfaces IF-02/08/12/13. The following are semantic requirements, not new lifecycle enums or completed JSON schemas:

- **Feedback observation:** source artifact/check/trial IDs; producer and evaluator versions; creation and available-at times; observed result including invalid, pending or missing status; exact scope; data/exposure references; latency and relevant resource cost. Unknown values are explicit, not silently zero.
- **Heuristic interpretation:** separate observation references and interpretation text; intended search behavior; applicability and known limitations; counterevidence/conflicting or stale entries; author/version; permitted influence; review/retirement trigger. When no external observation exists, retain that limitation rather than inventing feedback.
- **Retrieval/use:** epoch/context ID, retrieval policy/version, selected entry IDs, selection reason or reproducible selection record, exposure closure and affected idea/proposal IDs. Record use before the downstream outcome becomes available; avoid hindsight attribution of successful ideas to preferred heuristics.
- **Review outcome:** retain, revise or retire a heuristic with reason and supporting observations; append a new version and preserve prior uses. These are descriptive review actions, not replacements for the market-evidence state machine.

Retrieval must permit relevant failures, conflicts and stale lessons, not just successes. It need not inject every record into every prompt. A heuristic has a defined review trigger, such as new contradictory evidence, changed source/definition or a planned assessment checkpoint; no universal expiry or automatic truth score is introduced. Material prompt, retrieval-policy, language or evidence changes follow D026; routine use within an already approved policy does not create a new approval gate for every retrieval. OPEN-14 still governs the unresolved certification boundary.

Exposed validation outcomes may inform a later development epoch, but they are then development exposure for that descendant and cannot simultaneously serve as its independent confirmation. Isolate the information used to tune a candidate from the information used to assess that candidate. A new label, compressed memory, model name or rollback does not reset exposure. No reusable-holdout algorithm is adopted by this contract.

## Evaluation contract: specify the question, discover the answer

| Assessment purpose | Necessary reference and result | What it does not establish |
|---|---|---|
| Absolute economic usefulness | A frozen net economic criterion for a defined scope and separately tested policy, with costs, execution assumptions, risk constraints and uncertainty | Superiority over another generator or a quantitative firm |
| Procedural capability | Independently checkable criteria for faithful formalization, repeat-error avoidance, completion or relevant resource use | Profitable hypotheses merely because more artifacts compile or fewer errors occur |
| Generator-version or memory improvement | A named prior version/configuration and the specific claimed change; comparable information, tasks and resources; estimated difference and uncertainty | Universal superiority, or a causal effect if other relevant components changed |
| Discovery/testing acceleration | D068's defined reference workflow or prior version, task scope, decision quality and time/cost measures | Greater trading returns than a competitor |
| Optional competing-method superiority | A separately scoped and authorized method comparison | A prerequisite for absolute usefulness; D015's rejected generator is not authorized here |

For an absolute-usefulness assessment, the method-comparator field may explicitly be not applicable. A claim's statistical comparator/estimand remains required under REQ-005. Acceptance must not confuse these two fields.

### Required assessment plan and report

Before inspecting assessment outcomes, register the purpose, target claim, scope and versions, resource limit, outcome measures, minimum practically relevant effect or precision target with rationale, and the interpretation of positive, negative, inconclusive and technically invalid results. For feasibility/exploratory work, declare the narrower inferential purpose instead of promising a confirmatory answer. Effect expectations are assumptions with sources or ranges, not facts the builder must already know.

For comparisons, also specify the reference, permitted input snapshots, search/tuning opportunities, total relevant model/compute/human/data costs, repeated-run plan and sampling unit. Pair tasks/windows where appropriate; justify any matching and dependence assumptions. A shared seed or time window does not create independent market observations. Separate repeated LLM sampling from independent market cases. Prefer analysis of the actual difference when it answers the claim; no universal paired t-test, bootstrap or sample count is selected.

Record all candidate versions, probes and outcome-dependent selections. Fix the final-assessment release/access rules before outcomes. CMP-12 cannot approve an improvement by selecting its best observed probe as if it were untouched validation. When continual adaptation is the object of study, freeze the adaptation rule and evaluate the whole evolving procedure under that rule; do not pretend it is an unchanged static generator.

Reports retain all registered cohort members and show generated, formalized, queued, evaluated, negative, inconclusive, supported, invalid and still-pending cases separately, using the existing lifecycle meanings. Include follow-up time and denominators; slower hypotheses must not disappear from the denominator merely because they have not finished. Report technical quality, formalization fidelity/coverage, economic outcomes and research cost separately. No aggregate novelty, Sharpe or throughput reward replaces these dimensions.

A non-significant difference is not equivalence; an incomplete or low-information evaluation does not establish no benefit. Rejecting an economic hypothesis requires the frozen rule, not just an absent significance flag. A budget decision to stop is permissible but must remain distinguishable from scientific falsification. Reassess a deferred study at its named data/resource checkpoint; until performed, an improvement claim remains unverified. D059 remains staged: this contract prepares bounded evaluation, not an immediate comprehensive causal meta-study.

## Evidence availability and pilot scope

For each proposed real-data study, record the data source/version, access rights and actual availability, point-in-time/revision behavior, known and unknown model/source exposure, coverage, event/outcome definition, outcome delay, overlap/clustering, missingness and relevant cost/fill assumptions. Explain which attainable effects or precision the resource budget can inform; use justified ranges or a sensitivity analysis when the effect is unknown. Freeze the chosen analysis before confirmatory outcomes under OPEN-05/06/11/12.

Separate computation time, data-acquisition time and waiting for new outcomes. Raw bar/trade counts do not equal independent information; resampling does not create new confirmation. Predeclared concurrent claims can share observations only under an appropriate joint dependence/error policy. No fixed years-per-hypothesis rule is introduced.

Compare candidate pilot domains by actual data access, effective information, outcome delay, semantic opportunities, formalization coverage, execution realism and cost. Do not presume that funding, expiry, rebalancing, short horizons or heterogeneous inputs are uncrowded or superior. A bounded pilot records its exclusions and limits; it does not permanently restrict free discovery or remove swing research. Known useful effects can contribute; global originality is not required.

The current user lacks the necessary market data. A data-requirements inventory, feedback mapping, assessment outline and technical acceptance fixtures can be specified now. Real market execution remains deferred. Data availability and protocol readiness are run prerequisites; demonstrated profitability or comparative superiority is an outcome, not a run prerequisite.

## Discovery diagnostics without a novelty gate

Record available known analogues, the claimed difference and its basis. Distinguish not searched, searched with none found, known related work and uncertain relation in the diagnostic record; these descriptions do not redefine scientific statuses. If literature retrieval is used, retain query, corpus/source coverage, timestamps, returned references and exposure consequences. Do not interpret retrieval failure as proof of originality. Literature retrieval is available under D029, not a compulsory precondition for every idea.

Observe H_idea coverage as well as H_exec structure so that ideas lost at formalization are visible. Version any feature/condition/outcome/horizon overlap measure or semantic similarity method and report its denominator and uncertainty. Structural similarity does not establish semantic identity; language similarity does not establish equivalent executable claims. No distance threshold is adopted from another paper as a default, and diagnostic scores cannot veto an unusual hypothesis or automatically alter evidence.

Complementary semantic, neutral and open-discovery perspectives remain options under M0110-M0112/D005/D016; record which representation was used and what information it contained. Neutral labeling is not removal of pretraining exposure. Open discovery may omit the current Market Model while retaining necessary definitions; it does not require semantic amnesia. Persistent convergence prompts review of concrete examples, source access and downstream utility, not automatic pursuit of maximal diversity or extra agents.

## Acceptance specifications

These are future behavioral tests, not tests executed by the documentation checker. They require runtime fixtures when the relevant implementation is built.

| Test | Required cases and observable outcome |
|---|---|
| TEST-28 / REQ-028 | A missing feature and an independent technical failure create retained observations and optional qualified heuristics without market-negative labels. An unsupported reflection cannot create evidence. A retrieved lesson carries source exposure into a descendant; a conflicting or retired lesson remains auditable. A use record precedes the downstream outcome. No unavailable observation is fabricated. |
| TEST-29 / REQ-029 | An absolute-usefulness plan with the applicable complete contracts passes readiness without a positive prior result or competing-generator field. A comparison claim lacking its reference/matching/access plan is rejected for that claim only. A planning document may retain explicit unresolved fields but cannot authorize confirmation. Pending outcomes and failed probes remain in reports; non-significance alone cannot become equivalence or confirmed absence. Exposure used for tuning fails independent-validation eligibility for its descendant. |
| TEST-30 / REQ-030 | A known useful analogue is retained; not searched and searched-with-none-found are distinguishable. A missing literature match does not certify novelty. Equivalent wording variants and a similar-looking but materially different claim can be inspected without automatic evidence decisions. Formalization failures remain in the idea cohort. High similarity alone neither deletes ideas nor triggers new agents; optional neutral/open modes preserve their declared information boundaries. |

TEST-28 composes with TEST-06/13/16/21, TEST-29 with TEST-05/19/20/24/27, and TEST-30 with TEST-01/02/14/22. Documentation checks verify consistency and traceability only, not these behaviors.

## Academic basis and transfer limits

Primary academic texts were inspected on October 22, 2026, including the indicated method/limitations sections. The operational rules above are project-specific design deductions aligned with existing decisions; these studies do not validate this financial framework. No numerical experimental setting is imported as a default.

| Source | Relevant evidence inspected | Adopted consequence and boundary |
|---|---|---|
| [Shinn et al., Reflexion, NeurIPS 2023](https://arxiv.org/html/2303.11366v4), sections 3 and 5 | Separates acting, evaluation and verbal feedback; uses several evaluator types and reports limitations of reflection/memory | Retain feedback and interpretation separately. Its LLM evaluators and reward optimization are not adopted as market-evidence authority; benchmark gains do not prove financial learning. |
| [Huang et al., ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/8b4add8b0aa8749d80a34ca5d941c355-Paper-Conference.pdf), sections 2 and 6-7 | Distinguishes intrinsic correction from external feedback; studies misleading comparisons and inference cost; limits conclusions to investigated reasoning settings | Record feedback source and verification, and account for extra work when assessing a change. Do not equate reflection with verified improvement or universal failure. |
| [Patterson et al., JMLR 2024](https://jmlr.org/papers/volume25/23-0183/23-0183.pdf), sections 4.4-4.5 | Examines paired differences, experiment design and sources of variability; motivates insight rather than universal state-of-the-art claims | Match a comparison to the question and report uncertainty. Market dependence and nonstationarity require separate justification; their task distribution and estimators are not imported. |
| [Dwork et al., NeurIPS 2015](https://proceedings.neurips.cc/paper_files/paper/2015/file/bad5f33780c42f2588878a9d07405083-Paper.pdf), sections 1 and 3 | Shows why adaptive holdout reuse matters and gives specific mechanisms with explicit assumptions | Treat feedback used for selection as exposure. Logging alone is insufficient. Thresholdout and its guarantees are not adopted for dependent market data. |
| [Lakens, Collabra: Psychology 2022](https://doi.org/10.1525/collabra.33267), resource constraints and sensitivity/precision sections; [author-institution full text](https://pure.tue.nl/ws/portalfiles/portal/214011492/collabra_2022_8_1_33267.pdf) | Discusses sample-size justification by inferential aim, resources, power and accuracy | An unknown effect does not prevent planning; justify what the available budget can resolve and retain inconclusive outcomes. No universal power target or sample size is imposed. |
| [Si, Yang and Hashimoto, ICLR 2025](https://arxiv.org/html/2409.04109v1), sections 3, 6.3 and 7 | NLP idea generation exhibits duplication and imperfect idea-ranking agreement under specific operational measures | Track coverage and similarity with method provenance; do not turn a novelty judgment into usefulness or copy the study's similarity threshold. This is not evidence about market returns. |

## Versioning and rollback

This contract adds detail to existing responsibilities; it creates no automatic approval policy, new evidence state or competing generator. Definitions remain reconstruction-1, and OPEN-01 through OPEN-03 remain unresolved. Change this contract through D008/D026 when scientific meaning is affected. Preserve version 1.0 and all observation/use/evaluation records when superseded; rolling back a configuration does not erase exposure, failed probes or this approval history.
