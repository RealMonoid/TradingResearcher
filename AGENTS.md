# Repository instructions

## Purpose and boundaries

Build toward autonomous, nontrivial LLM invention of market hypotheses, faithful formalization and freezing, and independent deterministic scientific evaluation. Preserve free discovery rather than replacing it with a closed rule catalog. The LLM must not judge its own empirical success. See the [Problem Definition](docs/architecture/01_PROBLEM_DEFINITION.md) and D001 in the [Decision Register](docs/architecture/02_DECISION_REGISTER.md).

Preserve the [Master Architecture](docs/architecture/06_MASTER_ARCHITECTURE.md) invariants: point-in-time information, inherited exposure, pre-outcome scientific commitments, independent feature certification, retained failures and unsupported ideas, separate policy evaluation, and the firewall between operations and research evidence. Keep evidence, validity, applicability and deployment authority distinct without inventing a resolution to open semantics. Historical-first research does not make exposed history unseen; v1 discovery starts at 15-minute observations (D012–D014).

## Read according to the task

- Start with the [README](README.md) and descriptive [Current State](docs/architecture/CURRENT_STATE.md).
- Before a system-level assessment, follow [REVIEWING.md](REVIEWING.md): reconstruct and substantiate the system model before critique, state gaps, and withhold an overall verdict when the reconstruction is incomplete. Use that same model for design and implementation; reuse it within a session and reconstruct it after context loss or a material change.
- For affected behavior, consult the [Decision Register](docs/architecture/02_DECISION_REGISTER.md), [Rejected Decisions](docs/architecture/03_REJECTED_DECISIONS.md), [Definitions](docs/architecture/04_DEFINITIONS.md) and [Open Decisions](docs/architecture/11_OPEN_DECISIONS.md).
- For design or implementation, read relevant sections of the [Master Architecture](docs/architecture/06_MASTER_ARCHITECTURE.md), [Requirements](docs/architecture/05_REQUIREMENTS.md), [Engineering Review](docs/architecture/08_ENGINEERING_REVIEW.md), [Implementation Blueprint](docs/architecture/09_IMPLEMENTATION_BLUEPRINT.md) and [Traceability Matrix](docs/architecture/12_TRACEABILITY_MATRIX.md). Consult the [Scientific Evaluation](docs/architecture/07_SCIENTIFIC_EVALUATION.md) when scientific validity is affected.
- For provenance disputes, use the [Source Audit](docs/architecture/00_SOURCE_AUDIT.md) and [Source Review Index](docs/architecture/SOURCE_REVIEW_INDEX.md) to locate the relevant archived messages. Do not read the entire conversation for every small change.

For wording-only edits and other bounded tasks with no architectural consequence, use the entry documents and affected files only; skip the full orientation and system recap. Do not expand the task, repeat reads already available, or ask the user to restate documented context. A historical handoff's task authorization describes that earlier task; the current explicit user request determines today's scope, subject to the scientific change-control rules below.

## Authority and change control

Accepted decisions and versioned canonical definitions govern their stated scope; respect source-confidence qualifications. Architecture summaries, examples, reviews and implementation proposals do not override them.

| Status | Treatment |
|---|---|
| NON_NEGOTIABLE / ACCEPTED | Preserve the recorded constraint or decision. |
| CONDITIONALLY_ACCEPTED | Apply only within the recorded conditions. |
| REJECTED | Consult the rejection's reason, exact scope, replacement and reconsideration conditions before proposing or implementing a similar approach. A role-specific rejection is not a blanket ban. |
| SUPERSEDED | Retain historical provenance; follow the recorded replacement. |
| PROPOSED_ONLY / DEFERRED | Neither accepted nor authorized for implementation merely by appearing in documentation; deferral is not permanent rejection. |
| OPEN / AMBIGUOUS | Resolve before affected operations; do not silently choose a scientific interpretation. Unrelated authorized work may continue. |

Never silently change project goals, scientific evidence rules, scientific contracts or canonical definitions. Material changes require explicit user approval of a reviewable proposal with rationale, affected decisions/requirements, validation, versioning and rollback (D008, D026). Label goal changes **GOAL CHANGE — USER APPROVAL REQUIRED**. OPEN-01 through OPEN-03 remain unapproved semantic proposals. Preserve prior versions and exposure history when recording approved changes.

Distinguish scientific logic from ordinary infrastructure. External runtimes, storage and backtest libraries may implement approved contracts; they cannot define evidence or change scientific meaning. Routine infrastructure work within an authorized task does not need repeated approval unless it materially changes those boundaries. Do not invent an automated approval policy for the unresolved certification boundary in OPEN-14.

## Working discipline

- Keep all authored project artifacts in English (en-US), per D043. Preserve original-language verbatim source quotations and the archived source bytes; do not translate or rewrite the original conversation archive. Document source gaps honestly and add later recovery as separately versioned evidence.
- Use the smallest coherent implementation that meets affected requirements. Logical roles do not mandate separate agents, services or databases. Avoid speculative abstractions and follow D030's bounded iteration rules.
- The [Roadmap](docs/architecture/10_IMPLEMENTATION_ROADMAP.md) proposes phases; it does not authorize starting one. Work within the user's current scope and resolve blockers for the selected work.
- Verify changes against affected requirements, acceptance criteria and existing tests. Distinguish specified future tests from executable tests and from tests actually run. For documentation, check consistency, links, whitespace and preservation of unaffected artifacts. Report changed files, exact check outcomes and unverified boundaries; do not claim scientific validity from software checks.
- After approved decisions or verified capability changes, update affected canonical documents and the descriptive handoff using the [Current State maintenance process](docs/architecture/CURRENT_STATE.md#maintaining-this-handoff-and-recording-decisions).
- If a source listed in [review/README.md](review/README.md) changes, regenerate that reading copy with `python scripts/build_review_document.py` and verify it with `python scripts/build_review_document.py --check`.
