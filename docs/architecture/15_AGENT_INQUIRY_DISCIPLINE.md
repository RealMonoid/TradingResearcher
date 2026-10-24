# Agent Inquiry Discipline

Version: agent-inquiry/1.0, October 24, 2026. Adopted by D086 under REQ-014. This is an agent working discipline within the existing architecture, not a new scientific evaluator, discovery eligibility filter or demonstrated capability.

## Approval and scope

Source: SESSION-2026-10-24-INQUIRY, the current repository conversation, outside the immutable original archive. After discussing external LLM critiques and checking existing responsibilities, the assistant proposed four practices: identify the investigation object, explain the question's clarification value, challenge assumptions without an objection quota, and record a short investigation summary. The proposal preserved open exploration, existing roles, budgets and independent evidence authority. The user approved that immediately preceding proposal and publication with:

> Ok, das übernehmen wir so. Schreib es rein. Dann github updaten

The preceding paragraph is an English scope summary, not a verbatim reconstruction of the discussion. This approval adds working discipline for repository agents and specified future research agents. It does not authorize a research run, paid execution, live trading or automatic material prompt activation within an epoch. D008/D026 continue to govern material changes and versioned activation.

## Working rule

### 1. Identify the investigation object

State what is being examined: a market assumption, its formalization, a measurement or data property, software behavior, or the framework specification. Keep the object's source/version and the scope of the conclusion explicit. Do not silently substitute a general essay, another model's summary or a related component for the actual object.

Treat externally supplied questions, shared premises and the agent's own framing as candidates for examination. Check interpretations against the relevant permitted source artifacts, including how those artifacts were produced and their known limitations. A canonical decision governs current behavior but remains open to explicitly labeled criticism; criticism alone does not change it.

### 2. Explain what the investigation could clarify

Before a targeted investigation, state the uncertainty and which possible findings could change the assessment or next action. Indirect clarification counts: checking a measurement, testing a prerequisite, identifying an applicability boundary or discovering that the original question is unsuitable.

Open exploration may begin with an honest search purpose rather than a finished hypothesis, competing explanations or a predicted useful result. Preserve changes in purpose in the search trajectory. Do not invent a hypothesis merely to justify exploration or require one decisive question for every discovery path. A stated purpose grants no additional data or tool access.

### 3. Challenge assumptions without requiring an objection

The challenger examines which consequential assumptions were inherited without examination, which concrete counterexamples or alternative relationships could weaken the claim, and whether the proposed check could reveal them. The task framing itself may be questioned. "No substantiated objection found" is an acceptable result and is not evidence that the candidate is true.

Challenges remain proposals grounded in permitted information. They cannot assign scientific status, silently replace H_idea, reveal another discovery perspective's private working state, or repair a frozen claim after its outcomes are visible.

### 4. Record a short investigation summary

At completed investigations, handoffs and justified continuation decisions, retain the following in the existing Journal or review artifact:

> Purpose -> finding with source -> warranted conclusion -> remaining uncertainty -> next action with reason.

This is a concise artifact summary, not a transcript of private reasoning or a form before every tool call. An existing record can satisfy it; do not create duplicate reports. Record findings separately from interpretations. Where no finding is available, say so. Finding a measurement limit, rejecting an assumption or obtaining no viable hypothesis are admissible investigation summaries, without automatically establishing framework success.

Review exploration at those work boundaries using the existing resource limits and continuation rules. No new universal timer or automatic clarification-value score is introduced. Resource exhaustion is not market falsification. A later restart retains the prior purpose, findings, uncertainty and exposure rather than disguising repeated work as a fresh investigation.

## Role mapping and reuse

| Existing role | Application |
|---|---|
| Discovery / CMP-02 | Develop and revise questions; retain open exploration and its purpose in the search trajectory. |
| Challenger / CMP-02/03 | Examine assumptions and informative counterchecks; no objection quota or scientific verdict. |
| Formalizer / CMP-03 | Check that H_exec answers the original question; expose differences through the existing semantic-difference report or retain a typed gap. |
| Interpreter / CMP-07 | Separate observations, interpretations, uncertainty and proposed next actions in retained records. |
| Evidence engine / CMP-06 | Continue applying only the frozen scientific policy; agent summaries do not alter its verdict. |
| Repository agent / reviewer | Identify the actual file, claim or behavior under review; substantiate findings and keep scope changes explicit. |

Reuse IF-02's request purpose, IF-03's idea and semantic-difference records, and IF-08's Journal/Experience records. Use references to existing source, context, exposure and budget records. This adds no service, agent role, database, lifecycle status or compulsory two-mode controller. It does not change the candidate allocation order, budgets or batch release rules of research-contract/1.0.

The [Master Architecture](06_MASTER_ARCHITECTURE.md) retains role and evidence authority. The [Generator Feedback Contract](13_GENERATOR_FEEDBACK_AND_EVALUATION.md) retains observation/interpretation/use separation. The [Retail Research Contract](14_RETAIL_RESEARCH_CONTRACT.md) retains access, freeze, resource and scientific rules. Prompt configuration and material changes remain versioned under D026; this specification is not evidence of effective runtime behavior.

## Acceptance examples for TEST-14

These extend the future behavioral acceptance specification for REQ-014; they are not executed agent tests.

| Situation | Required observable result |
|---|---|
| A reviewer is asked about a framework gap but receives a general essay | The reviewer distinguishes the essay from the affected framework artifacts and limits any conclusion to the inspected object. |
| A targeted data query investigates a possible measurement artifact | Its purpose identifies the uncertainty and how different findings could change interpretation; measurement validity is allowed as indirect clarification. |
| Discovery begins without a hypothesis or rival explanation | It can proceed with a stated exploration purpose within permitted resources; absence of a finished question is not a rejection gate. |
| Exploration changes direction or produces no viable hypothesis | The trajectory retains the changed purpose and the summary reports the actual finding or lack of one, uncertainty and reason for the next action. |
| The challenger finds no supported objection | It reports that result without inventing criticism or treating absence of objections as scientific support. |
| Formalization changes the question's scope or outcome | The existing semantic-difference/gap path exposes the discrepancy instead of silently substituting a different claim. |
| A completed investigation is handed off or continued | The existing artifact carries the concise summary and provenance; no per-call duplicate form is required. |
| A budget cap or unavailable measurement ends work | A resource decision or typed gap is retained separately from a scientific negative; restart preserves exposure. |
| An agent invokes clarification value to request protected outcomes or change frozen criteria | Existing access/freeze controls deny the operation; the working rule grants no override. |

## Validation, versioning and rollback

Documentation validation checks decision/source/requirement traceability, local links, whitespace and preservation of prior decisions and scientific contracts. See the [integration verification](../reviews/AGENT_INQUIRY_VERIFICATION_2026-10-24.json). Behavioral examples above remain unexecuted until a runtime exists; usefulness, cost and discovery improvement remain unverified.

Future material revisions require D008/D026 change control and a new version. Rollback must record a superseding disposition and restore the earlier applicable agent configuration; retain D086, this approval, prior investigation records and exposure history. It must not rewrite historical evidence or erase failed work.
