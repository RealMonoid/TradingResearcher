# Diagnosis quality: literature and philosophy of science

Date: 2026-11-01. Status: research synthesis and proposed application, not a new accepted decision, scientific contract, statistical method, or runtime capability.

## Purpose and authority

The user asked what counts as a good diagnosis when the controller can establish record integrity but cannot establish substantive quality from text alone, and requested scientific and philosophical literature. The economic purpose remains useful market research after realistic costs; scientific rigor serves that purpose.

The already approved boundary is in [document 25](../architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md#controller-integrity-and-diagnosis-quality). This review supplies intellectual context and possible operational refinements. It does not change D096, frozen profiles, exposure rules, budgets, or deployment authority. The [sole implementation plan](integration-research-2026-10-24/IMPLEMENTATION_SEQUENCE_2026-10-25.md) remains authoritative for work sequencing.

Method: targeted primary-source reading, including an author's philosophical monograph, formal diagnosis research, and empirical LLM studies. This is not a systematic review, a complete account of current models, or a reproduction of reported experiments. Publication years are distinguished from the access date above. Relevant passages were inspected; no claim is made to have read every cited work cover to cover.

## Source findings and limits

### 1. Explanatory attractiveness does not settle truth

Finnur Dellsén, *Abductive Reasoning in Science* (2024), introduction, section 2 and section 4.1, especially pp. 46–49: accounts of inference to the best explanation differ. The best available explanation might belong to a set that omits a better, as yet unformulated explanation. Dellsén examines competing responses rather than presenting this objection as a settled refutation of abduction.

Project implication: rank plausible diagnoses provisionally without treating the winning narrative as established truth. Preserve an unresolved possibility when evidence does not discriminate. This does not require exhaustive enumeration or artificial objections.

[Publisher's open monograph](https://www.cambridge.org/core/services/aop-cambridge-core/content/view/A380186A1C38650BB9842AF9536D235D/9781009500524AR.pdf/abductive_reasoning_in_science.pdf), DOI 10.1017/9781009353199.

### 2. A passing check matters only for errors it could expose

Deborah G. Mayo, *Critical Rationalism and Its Failure to Withstand Critical Scrutiny* (2006), section 6.2, pp. 81–82: her severity account connects evidential support to a test's capacity to expose a specified flaw. Survival of a check that would also pass under that flaw provides little support against it.

Project implication: ask which diagnostic error an actual check could reveal. An ordering or schema check cannot test an unsupported claim about market rarity. This is a methodological application of one philosophical position, not adoption of Mayo's statistical framework, a universal probability threshold, or a claim of philosophical consensus.

[Author-hosted chapter](https://errorstatistics.com/wp-content/uploads/2020/10/mayo2006_chapter_criticalrationalismanditsfailu.pdf).

### 3. Consistency can leave several diagnoses open

Raymond Reiter, *A Theory of Diagnosis from First Principles*, Artificial Intelligence 32 (1987), 57–95; definitions in sections 2–3 and additional measurements in section 6: a diagnosis is formulated relative to a system description and observations. Multiple diagnoses may be compatible; additional observations can change the set, including revealing new possibilities.

Project implication: separate consistency with observations from identification of the actual cause. Independent fixtures are especially useful for bounded technical faults. Reiter's formal assumptions do not supply a complete model of an open market, and a logically admissible diagnosis is not automatically a causal or economic finding.

[Primary paper](https://www.cs.ru.nl/~peterl/teaching/KeR/reiter.pdf).

### 4. Persistence and retrospective rescue are different

Imre Lakatos, *Science and Pseudoscience* (1973 talk; inspected transcript includes marked additions from later publication), pp. 3–4: he contrasts research programmes that generate empirically successful new predictions with programmes that repeatedly accommodate known failures. He explicitly rejects instant rationality and allows attempts to revive an unsuccessful programme.

Project implication: assess the trajectory of investigations, not just whether the last attempt failed. Further work needs an identifiable prospect of a discriminating result. This is not a requirement that market ideas be academically novel, an excuse for indefinite spending, or a ready-made stopping algorithm. Economic resource limits are a separate project constraint.

[Transcript hosted by Freie Universität Berlin](https://www.inf.fu-berlin.de/lehre/pmo/eng/Lakatos-Science.pdf).

### 5. Reasoning has value through decisions and has its own cost

Stuart Russell's author overview describes rational metareasoning developed with Eric Wefald beginning in 1988: computational steps are selected for their expected contribution to the next external decision. The overview also identifies the computational difficulty of applying this ideal at the metalevel. The inspected *Principles of Metareasoning* archive excerpt contains only its first page; it is not evidence of a full-paper review.

Project implication: use expected decision improvement as a question, not an invented monetary score. A cheap check can be worthwhile without an immediate profit prediction. When outcome probabilities and values are unknown, record that uncertainty rather than claiming an optimal stopping policy.

[Author overview](https://people.eecs.berkeley.edu/~russell/research-bo.html); [one-page primary manuscript excerpt](https://iiif.library.cmu.edu/file/Newell_box00014_fld01011_doc0001/Newell_box00014_fld01011_doc0001.pdf).

### 6. Error detection and correction need separate evaluation

Gladys Tyen et al., *LLMs cannot find reasoning errors, but can correct them given the error location*, Findings of ACL (2024), 13894–13908: experiments distinguish locating an error from revising a solution after receiving its location. Providing correct locations improves correction in the studied tasks. The benchmark covers five reasoning task types; these are not market investigations or a test of every model available today.

Project implication: measure whether the diagnosis identifies the relevant error separately from whether a subsequent answer or action succeeds. A successful correction does not establish that the preceding diagnosis was right.

[Primary paper](https://aclanthology.org/2024.findings-acl.826.pdf).

### 7. Persuasive rationales can omit influences on answers

Miles Turpin et al., *Language Models Don't Always Say What They Think: Unfaithful Explanations in Chain-of-Thought Prompting*, NeurIPS (2023), abstract and experimental setup: manipulated prompt features influenced answers while generated explanations did not faithfully report those influences. The experiments studied particular models and tasks, including GPT-3.5 and Claude 1; they do not quantify the problem for this project's current configuration.

Project implication: the explanation text is an object to check, not privileged access to the actual cause of an answer. This does not require collecting private reasoning transcripts; inspect claims, sources, calculations, and behavior.

[Primary proceedings paper](https://proceedings.neurips.cc/paper_files/paper/2023/file/ed3fea9033a80fea1376299fa7863f4a-Paper-Conference.pdf).

### 8. Self-correction is possible under specific conditions

Aviral Kumar et al., *Training Language Models to Self-Correct via Reinforcement Learning*, arXiv:2409.12917, version 1 (2024-09-19), sections 6–7: SCoRe reports improved intrinsic self-correction after targeted multi-turn reinforcement learning on mathematical and coding tasks. The paper notes that it trained only one round of iterative correction.

Project implication: avoid a blanket claim that self-correction cannot work. Training results do not establish that adding a reflection prompt or controller record improves this framework. Neither repeated correction rounds nor market generalization follows from these experiments.

[Version actually inspected](https://arxiv.org/html/2409.12917v1).

## Synthesis for this framework

The sources do not supply one agreed universal definition, score, or oracle for good diagnosis. They support distinguishing questions that the project can assess separately:

| Assessment | Observable basis | Boundary |
|---|---|---|
| Record integrity | Permitted access, ordering, retained versions and references | Establishes inspectability, not substantive accuracy |
| Diagnostic support | Reproduced facts; predictions distinguishing relevant alternatives; independent checks applicable to the claim | Often partial, conditional, or unresolved |
| Decision usefulness | What warranted action or avoided action followed, with outcomes and complete cost | A useful action does not prove its explanation; one episode does not establish causal improvement |

**Proposed working formulation:** a good diagnosis is a sufficiently supported, appropriately scoped account of a problem or uncertainty that warrants a proportionate next decision. Its evidential support and its practical value remain separate assessments. A truthful finding that the cause is not yet identifiable can be better than a confident causal story.

For a consequential diagnosis, existing inquiry records can answer four short questions without an additional form:

1. What exactly is observed, and what is inferred from it?
2. Which plausible alternative would change the next action, and what observation could distinguish it?
3. What result would weaken or revise this diagnosis, and can the proposed check actually reveal that result?
4. Why is this next check, action, pause, or stop worth its burden now?

These are proposed applications of the reviewed arguments, not quotations or newly adopted mandatory fields. Selecting the relevant question is preferable to manufacturing a full checklist for every tool call.

## Worked example: no qualifying events

Illustrative scenario, not a measured result: a query returns zero events. The model proposes that the market condition is rare. Other consequential possibilities include missing input coverage and an incorrect query binding.

| Candidate | Discriminating observation to seek | Warranted scope |
|---|---|---|
| Missing coverage | Required intervals or fields are absent in the bound input | Explains unavailable observations; does not establish market rarity |
| Binding defect | A qualified known-positive fixture is rejected by the actual query, and a separately checked correction resolves that defect | Supports a technical fault for that binding and fixture |
| No qualifying cases in this sample | Relevant coverage and query behavior check out; independent enumeration finds no qualifying cases | Supports the scoped sample result; not a universal rarity claim or proof that the idea is worthless |

Correcting a demonstrated binding defect preserves the original research question. Relaxing the event definition until results appear changes it and cannot retrospectively vindicate the initial diagnosis. A fixture passing is evidence only for what the fixture covers. Multiple faults may coexist.

Dual space search operates here through candidate explanations and candidate discriminating checks. Metacognition asks whether the current search is reducing the relevant uncertainty, repeatedly telling a more elaborate story, or spending effort that cannot change the decision. This is a project application, not a new empirical result attributed to Klahr and Dunbar.

## Learning whether the rules help

Start within already authorized bounded work. For independently resolvable technical cases, inspect correct and incorrect diagnoses, unsupported certainty, justified abstentions, successful corrections, and total cost. For open market explanations without known truth, retain the separate supporting observations and unresolved alternatives; do not manufacture correctness labels.

An apparent reduction in errors can conceal avoidance of difficult cases. Faster stopping can discard useful ideas; more persistence can waste effort. Retain those competing outcomes and their denominators. For a later comparative claim, use the existing versioned assessment contract with comparable tasks, access, resource accounting and independent assessment. Reusing exposed history does not make it unseen. This review selects no numerical threshold, scoring rule, sample size, or new benchmark project.

Useful progress may be establishing a cause, ruling out a consequential possibility, discovering a measurement defect, or showing that the affordable evidence cannot distinguish the alternatives. More text, model agreement, repeated execution, and a favorable profit realization are insufficient by themselves. Economic usefulness remains the purpose; its absence at an intermediate step is not automatically evidence that further investigation is futile.

## Uncertainty and next action

The reviewed philosophical positions differ and do not mechanically resolve resource allocation. The empirical studies do not establish effectiveness for the current framework, its models, or markets. No experiments were reproduced, no runtime was evaluated, and no profitability or calibration claim follows.

Some initial access routes failed (Lipton author PDF, a full Lakatos collection, and the later SCoRe OpenReview PDF). The synthesis instead uses the accessible Dellsén monograph, Lakatos transcript, and explicitly versioned arXiv paper; it does not claim direct inspection of Lipton's inaccessible text or the later SCoRe version.

Next action: preserve the already accepted controller boundary in the active implementation slice, and observe diagnostic support and action utility separately in ordinary work. Any additional binding assessment method from this review requires a concrete scoped proposal through existing change control. The review itself creates no implementation obligation.
