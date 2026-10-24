# Instructions for LLM reviewers

Reconstruct the system before judging it. Apply this protocol to a framework-wide critique, including a critique supplied by another model. It also applies when reading this repository through a browser rather than a coding agent. It does not require a full architecture review for a bounded wording edit or a clearly scoped local finding.

## Establish the review basis

Apply [Agent Inquiry Discipline](docs/architecture/15_AGENT_INQUIRY_DISCIPLINE.md) (D086). Identify the actual object and the uncertainty under review; do not substitute an external critique's framing for the framework's behavior. Shared premises and the reviewer's own interpretation can also require examination. State which findings could change the assessment, allowing open exploration when the question is not yet formed. At a completed investigation or handoff, retain purpose, sourced finding, warranted conclusion, remaining uncertainty and the next action with reason. No objection quota or additional scientific authority follows from this discipline.

Record the branch or commit and the scope of the assessment. Read actual file contents, not just the repository page, search snippets, filenames or another model's summary. The current default branch is `codex/architecture`; verify it rather than assuming `main`. If GitHub page extraction fails, try direct Raw files or the public contents API. Report failed or truncated reads; they do not count as completed reading.

Read the [README](README.md) and [Current State](docs/architecture/CURRENT_STATE.md), then the complete [Problem Definition](docs/architecture/01_PROBLEM_DEFINITION.md) and [Master Architecture](docs/architecture/06_MASTER_ARCHITECTURE.md). Use their references to check the [Definitions](docs/architecture/04_DEFINITIONS.md), [Decision Register](docs/architecture/02_DECISION_REGISTER.md), [Rejected Decisions](docs/architecture/03_REJECTED_DECISIONS.md) and [Open Decisions](docs/architecture/11_OPEN_DECISIONS.md). For a whole-framework review, cover the [Requirements](docs/architecture/05_REQUIREMENTS.md), [Scientific Evaluation](docs/architecture/07_SCIENTIFIC_EVALUATION.md), [Engineering Review](docs/architecture/08_ENGINEERING_REVIEW.md), [Blueprint](docs/architecture/09_IMPLEMENTATION_BLUEPRINT.md), [Roadmap](docs/architecture/10_IMPLEMENTATION_ROADMAP.md) and [Traceability](docs/architecture/12_TRACEABILITY_MATRIX.md) as well. Read long documents in bounded sections without dropping the middle.

Check provenance disputes against the [Source Audit](docs/architecture/00_SOURCE_AUDIT.md) and its source index, then the relevant original messages. A later decision can supersede an earlier example. Preserve the distinction between accepted, conditional, rejected, superseded, proposed and open positions. A review recommendation is not an accepted scientific rule.

## Demonstrate the system model before the critique

Begin the assessment with a concise, source-linked reconstruction explaining:

- The goals, success criteria and non-goals, distinguishing framework success from individual research outcomes and policy success.
- The research flow from permitted inputs through discovery, formalization, evaluation and retained outcomes, including exits and deferred work.
- The feedback loops: what can be learned from which outcomes, where it is stored, and when it may influence later work.
- Decision authority: who proposes, computes, evaluates, changes rules and authorizes action, and which boundaries connect them.
- The current implementation state and unresolved decisions, including which operations those decisions actually block.

Explain how these parts interact; a component list or statement that you "understand the framework" is insufficient. Trace one ordinary research path and one failure or early-exit path across components into their subsequent feedback. For the concern being assessed, explain what the existing safeguard does and what would remain unresolved even if it worked as specified.

There is no reliable self-certification of "complete understanding." The observable prerequisite is a coherent reconstruction with supporting references and explicit gaps. If missing access, unresolved contradictions or context loss prevents that reconstruction, withhold the overall verdict and state the limitation. Report any independently established local finding with its exact scope; do not generalize it to the whole framework. If the documentation itself cannot support a coherent model, show the conflicting passages and their consequences rather than inventing a reconciliation. No additional user approval is needed to proceed from a supported reconstruction to critique.

## Critique the reconstructed design

For each material finding, give the claim and source, the triggering condition, the existing mechanism and why it is insufficient, the resulting consequence, and the smallest relevant remedy or discriminating test. Before claiming something is absent, inspect the document that owns it and its linked decisions. Distinguish absent, specified but unimplemented, explicitly open, and empirically unverified.

Do not substitute your preferred project goals or infer that a safeguard works merely because it is specified. Accepted decisions remain legitimate subjects of criticism; identify any proposed change to them explicitly. Do not manufacture a finding to fill a checklist. Keep demonstrated contradictions, implementation gaps and empirical risks separate, and state what was not verified.

This is a review discipline, not a guarantee of model comprehension or a reason to suppress substantive criticism. Reconstruct the model again after material context loss; do not claim that an earlier reading remains available when it does not.
