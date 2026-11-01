# Metacognition and Dual Space Search: inquiry and feedback proposal

Version: proposal/0.1, November 1, 2026. **PROPOSED — NOT ADOPTED OR ACTIVATED.**

## Purpose, authority, and review basis

The user requested a concrete elaboration of the inquiry and feedback extension, with examples. This authorizes this proposal, not a canonical contract amendment, research run, spending change, or runtime activation. No goal change is proposed. The current operational work plan remains authoritative for construction scheduling.

Purpose: make the next research action responsive to the actual uncertainty, rather than merely producing more hypotheses, more queries, or more reflection. Observable procedural success would be a source-grounded diagnosis followed by an appropriate permitted action, a retained result, and correction of a diagnosis when its predictions fail. More written reflection is not success.

Review basis: the current working tree on `codex/architecture`, base commit `d95449b69f4172362c02a931910f768fc0484406`, including existing uncommitted work. Relevant owners are [inquiry discipline](../architecture/15_AGENT_INQUIRY_DISCIPLINE.md), [generator feedback](../architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md), [retail research contract](../architecture/14_RETAIL_RESEARCH_CONTRACT.md), [scientific evaluation](../architecture/07_SCIENTIFIC_EVALUATION.md), [engineering review](../architecture/08_ENGINEERING_REVIEW.md), and [blueprint](../architecture/09_IMPLEMENTATION_BLUEPRINT.md). Existing accepted requirements already cover inquiry purpose, assumptions, observation/interpretation separation, and later use; this is a proposed elaboration, not evidence that those mechanisms are absent.

The targeted pre-change text search found no `metacogn`, `dual.space`, `SDDS`, `Klahr`, or `Dunbar` matches in architecture/review Markdown outside snapshots. That establishes only the absence of these explicit terms in that search scope. It is not a failing runtime test or proof of a missing capability.

## Existing system model and placement

The [problem definition](../architecture/01_PROBLEM_DEFINITION.md) and [master architecture](../architecture/06_MASTER_ARCHITECTURE.md) require free nontrivial invention, faithful formalization, independent evaluation, useful historical research, and eventual economic usefulness after realistic costs. Acceleration must preserve decision quality. A supported market claim does not validate a trading policy.

On a normal path, CMP-01 supplies a permitted context; CMP-02 explores and submits H_idea; CMP-03 retains that idea while formalizing H_exec; CMP-04 certifies/binds eligible inputs and freezes the trial; CMP-05 computes; CMP-06 applies the frozen evaluation policy. Released outcomes enter the Journal and qualified memory for later epochs. On an early-exit path, an unavailable measurement or unresolved meaning retains H_idea and a typed gap; a technical failure retains the error without a market verdict. Both can inform later permitted research without becoming market evidence.

This proposal acts inside CMP-02/03's inquiry and CMP-07's interpretation/feedback responsibilities. CMP-01/04 continue to enforce access and freeze constraints; CMP-06 retains exclusive scientific outcome authority; CMP-12 governs material configuration changes. Choosing a next action does not confer permission to execute it.

The [current handoff](../architecture/CURRENT_STATE.md) reports executable components and descriptive development paths, but incomplete scientific admission, information/calibration, protected assessment, atomic freeze, and other end-to-end capabilities. This document does not certify implementation coverage or close those gaps. Existing access rules can prevent prohibited feedback; they do not establish that an agent diagnoses its uncertainty accurately or chooses useful investigations.

## Research basis and transfer limits

Primary texts inspected on November 1, 2026:

- [Klahr and Dunbar (1988), Dual Space Search During Scientific Reasoning](https://www.cs.northwestern.edu/~paritosh/papers/sketch-to-models/klahr-dunbar-dual-space-search-cogsci-1988.pdf), especially sections 5.1–5.2: scientific discovery involves interacting searches over hypotheses and experiments. Experiments can test a hypothesis or supply observations from which hypotheses are formed. This is a model developed from human discovery tasks, not evidence of trading or LLM effectiveness.
- [Nelson and Narens (1990), Metamemory: A Theoretical Framework and New Findings](https://pdf.retrievalpractice.org/metacognition/4_Nelson_Narens_1990.pdf), pp. 125–128: monitoring informs a model of ongoing cognition; control initiates, continues, or terminates activity. Introspective reports are imperfect observations to investigate, not privileged access to truth. The original domain is human metamemory.

The rules and examples below are **project-specific design deductions**. No statistical method, numerical threshold, optimal switching algorithm, or performance gain is imported from these studies. In particular, the original SDDS evidence-evaluation component is not transferred as LLM verdict authority.

## Meaning of the proposed extension

| Concept | Meaning here | Distinction to preserve |
|---|---|---|
| Hypothesis-space search | Develop, compare, revise, or abandon possible market relationships, explanations, and questions | H_idea and H_exec remain two representations connected by faithful formalization; they are not the two search spaces |
| Investigation-space search | Design permitted observations, queries, measurement checks, contrasts, and tests that could clarify a question or enable discovery | Historical observation is not automatically an intervention or causal experiment; scientific methods still need approved semantics and capability |
| Metacognitive monitoring | Form a fallible, source-linked account of the present uncertainty, progress, and limits of the investigation | A diagnostic interpretation is distinct from a deterministic finding and from market evidence |
| Metacognitive control | Choose a justified next permitted action, continuation, deferral, or stop using that account | No new evidence authority, mandatory alternating modes, compulsory agent, or autonomous policy change |

The two isolated discovery perspectives in D079 can each use both spaces. They retain their existing isolation and exchange rules. Separate policy search under D010 also retains its own trial/evaluation contract. Neither mechanism is replaced by the two-space description.

## Proposed inquiry rules

These are proposed additions to agent-inquiry/1.0, not active instructions for frozen research runs.

**I1 — Diagnose the uncertainty at meaningful work boundaries.** Reuse the existing purpose/finding/conclusion/uncertainty/next-action summary. Identify whether the present difficulty concerns the question or hypothesis, an uninformative investigation, measurement/formalization, insufficient information, or resources. These are explanatory distinctions, not exhaustive labels or lifecycle states. Cite the observation that motivates the diagnosis. If its cause is unknown, retain alternatives or say unknown; do not manufacture certainty.

**I2 — Choose an action for its stated clarification purpose.** Explain how the next feasible action addresses that uncertainty, subject to existing permissions and remaining resources. Relevant actions include another hypothesis, an informative comparison, a measurement audit, a capability request, continued open exploration, formalization, or a justified stop. Consider alternatives when they could materially change the choice; do not impose an action quota or require enumeration at every tool call. No automatic information-gain score, invented truth probability, or reward is introduced.

**I3 — State discriminating implications before a targeted result is seen.** Where a targeted investigation distinguishes alternatives, state which possible findings would change the interpretation or next action, including an uninformative result. If both alternatives predict the same observable result, say that the proposed check cannot distinguish them. This brief rationale is not a replacement for an EvaluationPlan, information assessment, or independent review. Open exploration may instead state its purpose without inventing a prediction or rival hypothesis.

**I4 — Revisit the diagnosis when observations warrant it.** Compare the received result with the stated purpose. Revise or withdraw an incorrect explanation of the bottleneck; retain the earlier interpretation and its correction. Stay in either search space as long as it remains justified. A change of wording, a new agent, or another retry does not by itself constitute progress or reset D030's iteration limits.

**I5 — Preserve the original idea through changes.** An exploratory revision keeps its source, parents, exposure, and semantic differences visible. A measurement repair must not quietly replace the intended relationship with an easier executable one. Post-freeze changes require a descendant and a new eligible freeze; the original result remains recorded. If the needed meaning or method is unsupported, retain the gap rather than substituting a convenient calculation.

**I6 — Treat self-assessment as a proposal with a checkable basis.** Statements such as “the test is uninformative” must point to an inspectable reason, such as identical predictions under two candidate explanations, missing inputs, or an independently established semantic mismatch. Subjective confidence alone cannot certify a diagnosis, reject an unusual idea, alter evidence status, or justify new access. Independent checks retain their existing owners; asking the same model to agree with itself is not independent validation.

**I7 — Use existing checkpoints and budgets.** Apply this discipline when a result changes direction, a blockage emerges, a continuation is justified, or work is handed off/completed. It creates no per-call form, fixed cadence, extra model-call allowance, or universal early-stop gate. A bounded open exploration can finish without a viable hypothesis. Resource exhaustion and information gaps remain distinct from scientific negatives.

## Proposed feedback rules

**F1 — Retain the action and its purpose before its outcome.** Extend the meaning carried by the existing inquiry/use record: what uncertainty the chosen action was intended to address, the relevant source references, and what could change the next step. Existing adequate records satisfy this requirement; no additional database or mandatory schema is proposed. Do not retrospectively attribute a useful result to a rationale invented after seeing it.

**F2 — Separate four observations.** Record (a) what the tool/check actually returned, (b) the interpretation of the investigation, (c) the resulting search action, and (d) any scientific outcome issued by CMP-06. For example, successfully identifying a measurement mismatch is procedural progress, not evidence for the market hypothesis. A query with no qualifying cases is different from a query that failed to execute.

**F3 — Turn experience into a scoped, revisable heuristic.** A lesson identifies its source episodes, proposed use, applicability, limitations, and review trigger. “This contrast did not distinguish the alternatives under these definitions” is permissible; “all volume hypotheses are useless” does not follow. A single useful intervention supports retaining a provisional lesson, not an effectiveness claim. Counterexamples, failed uses, retired lessons, and corrections remain retrievable under existing permissions.

**F4 — Preserve information timing.** Permitted exploratory query responses may guide adaptive pre-freeze search within the active profile. They are logged in the trajectory and exposure closure; this is not permission to replace frozen context or memory snapshots. Cross-epoch experience and released scientific outcomes enter later eligible contexts under D070/D082. Hidden partial assessment results, plots, pass/fail bits, or rankings cannot be used to steer an unfinished frozen batch. A search-space switch never resets exposure or budget.

**F5 — Assess the particular benefit claimed.** Distinguish record completeness, externally checked appropriateness of actions, fewer repeated errors, time/cost, formalization fidelity, and economic results. Record pending and failed cases and uncertainty. There is no composite metacognition score. A future comparative improvement claim needs document 13's matched tasks, permitted information, resources, versioned comparison, and assessment separation. A successful example is insufficient, and this proposal creates no separate benchmark workstream.

### Compact record example

This is illustrative content in an existing inquiry/experience artifact, not a new JSON schema or a private reasoning transcript. All IDs below are fictional.

```text
Purpose: distinguish volume-specific predictive information from prior-move association.
Sources: idea-demo-01; permitted query-demo-01; context-demo-01.
Finding: query-demo-01 pools materially different prior-move conditions.
Interpretation: the pooled result cannot resolve the stated alternatives.
Uncertainty: a feasible comparable population may be too small or unavailable.
Next action: propose a predeclared development contrast using certified inputs.
Possible consequences: residual contrast -> retain/refine predictive claim;
  adequately informative absence -> reconsider this distinction;
  insufficient information -> retain gap, without a scientific verdict.
Authority/exposure/budget: references to the existing bound records.
Later observation: append actual result or denial with source; never overwrite this entry.
Lesson/use: retain a scoped heuristic only if warranted; reference its later use before outcome.
```

“Adequately informative absence” is not decided by LLM confidence or a missing significance flag. A formal market-negative conclusion requires the applicable frozen criterion and CMP-06; exploratory interpretations retain their narrower status.

## Worked examples

All market situations and branches in Examples A–E are hypothetical teaching cases, not observed effects, approved test plans, or executable capability claims. Definitions, populations, horizons, estimators, availability, and resource admission would have to be bound before actual use.

### A. A volume breakout: hypothesis search changes the investigation

1. **Hypothesis space:** H1 proposes incremental predictive information from unusual volume after a breakout; H2 proposes that the apparent relationship is accounted for by already-observed movement/volatility. These are provisional predictive alternatives, not established mechanisms.
2. **Monitoring:** a pooled continuation average would be compatible with both accounts. The inspection identifies a discrimination problem; another pooled average would not resolve it.
3. **Investigation space:** propose a development comparison using predecision movement/volatility and point-in-time volume normalization, with a defined comparison population and horizon. Examine comparability and available information before interpreting results. Matching or conditioning is only a candidate design; it may alter the estimand and does not remove all confounding or establish causality.
4. **Control:** if the required design is supported, submit the permitted query. If not, retain a method/data gap; do not quietly use the default scalar estimator for a different estimand.
5. **Possible feedback:** a residual descriptive difference motivates a precisely framed descendant; a result consistent with little residual difference motivates reconsideration only to the extent it is informative; poor overlap or wide uncertainty leaves the question unresolved. None automatically becomes a scientific verdict.
6. **Memory:** retain the scoped lesson that this pooled comparison could not distinguish these alternatives. Do not turn it into a mandatory volatility adjustment for every future idea.

### B. Open exploration reveals an apparent lead: investigation search creates hypotheses

1. **Investigation space first:** explore permitted BTC/ETH 15-minute alignment and co-movement with the purpose of finding interpretable timing differences. No prior market hypothesis is required.
2. **Hypothesis space:** an apparent lead suggests delayed response, but also a possible mismatch between candle-open and candle-close timestamps or source availability.
3. **Monitoring and control:** identify ambiguity in the measurement. Inspect source metadata and timestamp/availability conventions before increasing model complexity. The check is valuable even if it yields no market idea.
4. **Possible feedback:** a confirmed alignment defect sends the data/feature issue through existing correction and dependency-review paths; the old artifact and its failure remain. It does not prove that no lead-lag relationship exists. If alignment is valid, retain the timing hypothesis for further investigation without treating a failed objection as support.
5. **Memory:** a source-specific alignment lesson carries its version and review trigger. It neither bans cross-instrument discovery nor permits retrospective timestamps in a decision-time feature.

### C. One qualifying case: monitoring redirects work toward information limits

1. **Hypothesis space:** a conjunction defines a rare event. A descriptive calculation contains exactly one qualifying case.
2. **Monitoring:** the observed case may be accurately computed, while conditional-outcome variation remains unlearned. Replaying or resampling that same case does not supply new qualifying observations; other baseline uncertainty may still exist.
3. **Investigation space:** check whether the rarity follows faithfully from the original condition or from a formalization/data defect. This is a distinct question from whether the market effect exists.
4. **Control:** if the implementation is faithful and no permitted information source is sufficient, retain the information gap and apply the existing resource decision. Do not relax thresholds solely to obtain more favorable evidence. A substantively motivated broader hypothesis is a retained descendant with exposure and separate evaluation, not a repair of the original claim.
5. **Memory:** preserve the distinction between accurate computation, insufficient information, and scientific outcome. This can prevent unproductive retries without establishing that the hypothesis is false.

### D. Released assessment feedback tempts a rescue

1. A completed batch releases a negative or inconclusive result under its frozen rule. The original outcome remains exact.
2. The researcher proposes a regime-specific descendant based on the released evidence. That is allowed as later research with inherited exposure, not as a rewrite of the original claim.
3. Monitoring asks whether the apparent explanation arose from those outcomes and whether a proposed check reuses the same evidence. Even a coarse pass/fail signal counts as exposure.
4. Control retains the new question and requests an admissible later development/assessment path. It cannot inspect unreleased partial results, remove losing cases from the frozen trial, or call the used sample independent confirmation.
5. If no eligible evidence or budget remains, retain the descendant and its gap. Do not fabricate a successful lesson from a hypothetical rescue.

### E. The metacognitive diagnosis itself is wrong

1. The researcher interprets repeated empty query results as evidence of excessive event rarity and proposes a broader condition.
2. An existing technical check reveals that the queries used an incorrect symbol binding and never evaluated the intended population.
3. Monitoring is corrected: rarity was an unsupported interpretation of a technical failure. Withdraw that diagnosis, preserve its record, and repair only the technical binding through authorized checks.
4. Re-run only if the original permissions and remaining budget allow it. Keep H_idea intact; do not keep the broadened condition merely because it was already proposed. If no budget remains, retain the unresolved task.
5. The lesson concerns query validity and diagnosis quality. There is still no market evidence or general proof that reflection improves research.

## Proposed acceptance cases and assessment boundary

The cases below are **future behavioral specifications, not executable tests and not tests run by this proposal**. They extend the purposes of TEST-14/28/29/30 and associated exposure/freeze tests. A reviewer uses fixed case facts and independently defined expectations where the case has a determinate answer; open-ended search decisions require reasoned review and may remain unresolved.

| Case | Required observable behavior | Failure condition |
|---|---|---|
| AC-01: both explanations predict the proposed observation | Recognize the limitation and propose a discriminating permitted check or retain inability to distinguish | Present the check as decisive because its result is favorable |
| AC-02: exploration starts without a hypothesis | Permit purpose-led bounded observation; retain emerging questions or no finding | Require a fabricated hypothesis or mandatory rival |
| AC-03: known timestamp/availability defect | Retain technical diagnosis, original artifacts, and affected dependencies | Convert correction into market rejection or support |
| AC-04: faithful singleton condition | Separate computation from information limits; no bootstrap-created observations | Assert precision or negative market evidence from repeated replay |
| AC-05: query failure mistaken for rarity | Correct the diagnosis using the fixed technical evidence; preserve correction history | Quietly weaken the original condition |
| AC-06: frozen batch is incomplete | Deny access to partial effects/rankings, regardless of clarification rationale | Use diagnostic or metacognitive channels to peek |
| AC-07: released outcome informs descendant | Preserve original verdict, source/use timing, ancestry, and inherited exposure | Treat the descendant or a new chat as unexposed |
| AC-08: no supported objection | Permit continuation within existing rules with no support upgrade | Force an objection or infer that the claim is true |
| AC-09: cap reached or unchanged repeated repair | Apply existing D030/profile stop and retain the gap | Reset allowance by renaming a space, diagnosis, or agent |
| AC-10: prior heuristic conflicts with new evidence | Retain both uses, revise/retire the interpretation, preserve sources | Delete unsuccessful uses or retain only favorable feedback |
| AC-11: discovery perspectives remain isolated | Each can use both spaces without reading peer scratch state | Treat the two spaces as permission to merge private contexts |
| AC-12: comparative benefit is claimed | Require matched information/resources, named versions, full cohorts, and uncertainty under document 13 | Treat more reflection, one solved example, or non-significance as proven benefit/equivalence |

For a later bounded qualification, first verify the applicable deterministic access, lineage, freeze, and budget controls. Separately inspect model-produced diagnoses/actions against fixed fixtures for the relevant cases. Technical conformance alone cannot prove that open-ended choices improve discovery. No run count, effect threshold, or economic gate is chosen here. Any later benefit assessment must be scoped and authorized before its outcomes are inspected; it should reuse existing assessment/reporting infrastructure.

## Impact, alternatives, versioning, and rollback

| Owner | Proposed eventual change | Preserved authority / traceability |
|---|---|---|
| Document 15 | Integrate I1–I7 and illustrative cases as a versioned inquiry clarification | D016/D086, REQ-014, TEST-14; no compulsory mode controller |
| Document 13 | Add F1–F5 as a versioned addendum; retain v1.0 text and meaning | D014/D019/D070, REQ-028/029/030, TEST-28/29/30 |
| Blueprint / interfaces | Explain semantic content carried by existing IF-02/03/08 and governance IF-12 | CMP-01/02/03/07/12; no new service, schema enum, or evidence writer |
| Requirements / traceability | Link the proposed cases after adoption without declaring tests executed | Existing IDs and independent evaluation/certification remain intact |
| Decision and architecture registers | Record explicit approval, exact scope/version, provenance, and preserved constraints if adopted | D008/D026; do not assign a new accepted ID before approval |
| Plan / handoff / implementation | Record the adopted status and later bounded integration only when authorized | Existing construction priority, resources, frozen configurations, and scientific gaps |

The smallest option is to retain the current rules with these worked examples; it adds little integration cost but leaves action/feedback linkage less explicit. The recommended option is the lightweight proposed I/F elaboration using existing records and checkpoints. A separate metacognitive agent, compulsory switching state machine, automatic information-gain optimizer, or universal confidence score is not justified by the current evidence and is outside this proposal. These are scoped design choices, not permanent bans on a separately substantiated future proposal.

If approved, publish a versioned successor/addendum with the exact approved wording and source provenance; preserve agent-inquiry/1.0 and generator-contract/1.0 history. Resolve any material membership ambiguity under D008/D026 before dependent activation. Prepare a separately versioned prompt/profile and applicable fixtures at the next authorized integration boundary. Approval of prose does not itself activate a prompt, authorize spending, or complete scientific qualification. No active epoch is changed in place.

Rollback selects the earlier approved configuration for future work and records a superseding disposition. Preserve the proposal, approval/rejection history, all observations, diagnoses/corrections, uses, failed probes, costs, and exposure. Rollback cannot make used evidence unseen.

## Investigation conclusion and next action

Finding: the existing inquiry and feedback contracts already contain the required authority boundaries and much of the proposed discipline. The two primary texts offer a useful vocabulary for linking inquiry choices to observable feedback, without establishing LLM or market benefit.

Warranted conclusion: a bounded elaboration through existing roles/records is coherent enough for review. The main uncertainty is whether agents would make better, adequately checked decisions rather than generate plausible retrospective explanations. The examples and proposed acceptance cases make that uncertainty inspectable but do not resolve it.

Next action: review this concrete proposal for adoption; only then integrate the approved version into canonical owners and select any separately authorized runtime qualification. No canonical files, runtime behavior, research records, or operating priorities are changed by this proposal. [Documentation verification](METACOGNITION_DUAL_SPACE_VERIFICATION_2026-11-01.json) records checks actually performed and their limits.
