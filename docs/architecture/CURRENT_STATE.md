# Current state

Verified October 22, 2026. This is a descriptive handoff, not an additional source of architectural authority. The [Decision Register](02_DECISION_REGISTER.md), [Rejected Decisions](03_REJECTED_DECISIONS.md) and versioned [Definitions](04_DEFINITIONS.md) retain their existing authority and qualifications.

## Repository and existing artifacts

- Repository: [RealMonoid/TradingResearcher](https://github.com/RealMonoid/TradingResearcher). Verified working branch: `codex/architecture`; `origin` is `https://github.com/RealMonoid/TradingResearcher.git`.
- Architecture baseline before the original repository preparation: commit `d818dc0ded5d224932638795845071d2f24ce115`. That preparation added root [AGENTS.md](../../AGENTS.md) and this handoff. The earlier session-understanding intervention is preserved in its review artifacts. The subsequently approved system-model revision records D068, completes the existing goal/feedback explanation and simplifies entry instructions; it does not resolve open scientific contracts or authorize framework implementation.
- The [README](../../README.md) indexes architecture documents 00–12: source audit, problem definition, decisions, rejections, definitions, requirements, master architecture, scientific evaluation, engineering review, blueprint, proposed roadmap, open decisions and traceability.
- [ARCHITECTURE_REGISTER.json](ARCHITECTURE_REGISTER.json) is a structured documentation companion. [SOURCE_REVIEW_INDEX.md](SOURCE_REVIEW_INDEX.md), [SOURCE_VERIFICATION.json](SOURCE_VERIFICATION.json) and [DOCUMENTATION_VERIFICATION.json](DOCUMENTATION_VERIFICATION.json) preserve review and verification evidence from the reconstruction. Those reports do not automatically cover later changes or these two preparation files.
- [sources/](../../sources/) contains the original captured [conversation](../../sources/full_conversation.md), recovered DOM, message index, structured content, source inventory and [capture manifest](../../sources/capture_manifest.json). The capture records 304 numbered turns and 305 message blocks. It is not a verified complete original export. Missing images/files, incomplete M0302 and other provenance limits remain in the [Source Audit](00_SOURCE_AUDIT.md), SRC-001 through SRC-008. Continuing with documented gaps was explicitly authorized; the archive remains unchanged.

## Actual capabilities versus target design

The repository currently provides a readable, source-linked architecture, decision and rejection history, canonical definitions, requirements, proposed interfaces and acceptance specifications. It supports architectural discussion and traceability to the preserved source.

There is no implemented framework, application test suite, build/package configuration or CI workflow. No discovery agent, compiler, feature certification service, runtime registry, freeze transaction, data connector, simulator, evidence engine, memory system, Column Library, dashboard or deployment capability exists here. The `TEST-01` through `TEST-27` entries in the [Traceability Matrix](12_TRACEABILITY_MATRIX.md) are future acceptance specifications, not executed tests. Record-field tables in the [Blueprint](09_IMPLEMENTATION_BLUEPRINT.md) are not complete executable schemas. Repository-instruction checks are separate from these future application tests.

As recorded in the [Engineering Review](08_ENGINEERING_REVIEW.md), vectorbt is the accepted primary backend candidate; Hermes is a runtime candidate; Harness2 provides conditionally accepted improvement patterns. None is integrated or conformance-tested in this repository. That review is a documented critical pass, not an independent-person audit or application-code audit. Research performance, scientific calibration and profitability are unverified.

## Approved boundaries and unresolved work

The [Problem Definition](01_PROBLEM_DEFINITION.md) and [Master Architecture](06_MASTER_ARCHITECTURE.md) preserve free LLM invention, faithful H_idea-to-H_exec formalization, independent code judgment, point-in-time context and inherited exposure, frozen evaluation and selection rules, retained technical failures, separately evaluated policies and governed improvement. Unsupported ideas remain recorded with their gaps. Historical-first research and the 15-minute v1 observation minimum remain accepted; forward confirmation retains its distinct evidence origin. Logical component boundaries do not select a service topology or agent count.

The user clarification that substantially accelerating hypothesis discovery **and** testing is a framework-level success objective is now recorded as D068, REQ-027 and future TEST-27. Its current-session source is separate from the immutable archive. The Problem Definition states both goals; the Master Architecture and Blueprint connect early exits, retained gaps/errors, qualified results and the distinct feedback loops. [AGENTS.md](../../AGENTS.md) points to this whole instead of duplicating incident-specific reminders. Numeric targets and comparison design remain OPEN-11; no lifecycle migration, evidence upgrade or certification policy is approved.

The [System Model Review](../reviews/SYSTEM_MODEL_REVIEW.md) describes the pre-change findings and approved remedy. The earlier [session-understanding experiment](../reviews/session-understanding/README.md) applies only to its frozen instruction versions; its checker intentionally compares against those old hashes and is not a gate for this revision. Its incomplete efficacy result is retained. This revision has documentation integrity and consistency checks, not a new behavioral efficacy experiment; reliable comprehension across new sessions or compaction remains unverified.

The current [documentation checker](../reviews/verify_system_model.py) runs with `python docs/reviews/verify_system_model.py`; the [revision verification result](../reviews/SYSTEM_MODEL_UPDATE_VERIFICATION.json) records the executed checks and exact file hashes. Supplying its optional pre-edit inventory also checks preservation of all previously present review artifacts. Diagram routing checks do not verify rendering or executable scientific semantics.

[REVIEWING.md](../../REVIEWING.md), linked from README and AGENTS.md, now gives external LLM reviewers the same reconstruction-before-critique protocol. It requires an observable source-linked system model and bounded conclusions when context is incomplete. It changes review procedure, not scientific authority; cross-model compliance is unverified. Earlier verification snapshots retain their original scope and hashes.

[review/README.md](../../review/) is a generated, uncompressed reading copy of 17 source documents for GitHub-only readers. Its GitHub directory page displays the README directly; ordinary blob pages can defer content to embedded page data, and plain source views can truncate long files. It includes the review instructions and full architecture documents 00-12, with source hashes and relocated links. It is not a new canonical summary and does not include the original conversation archive or structured companions. `python scripts/build_review_document.py --check` checks exact regeneration. Successful public delivery does not establish that a particular LLM fetcher ingests the complete file.

Consult the complete [Open Decisions](11_OPEN_DECISIONS.md) register before affected work:

| Open items | Unresolved boundary |
|---|---|
| OPEN-01 | Historical/forward lifecycle and separate validity, evidence, replication and applicability dimensions; proposed migration requires user approval. |
| OPEN-02–03 | Subgroup evidence transport and interpretation of family success rates; proposed semantic changes require user approval. |
| OPEN-04–06 | Executable language semantics, statistical confirmation rules, initial market/data authority and execution conventions. |
| OPEN-07–09 | Runtime adoption, persistence/recovery and discovery models, agent count and budgets. |
| OPEN-10–12 | Live-capital authority, framework success/stop criteria and confirmation allocation. |
| OPEN-13–15 | Applicability/dependency propagation, routine certification versus material-change approval, and source recovery. |

The [Roadmap](10_IMPLEMENTATION_ROADMAP.md) recommends P1 semantic contracts followed by a technical vertical slice and later calibration. It is a proposal, not an authorized implementation phase. Earlier preparation and session-understanding tasks concern repository instructions and documentation; their scope statements do not override a later explicit user request. A framework implementation request must identify a bounded scope and acceptance evidence, with the relevant open decisions resolved before dependent work. No live trading or material self-modification is authorized by these documents.

## Maintaining this handoff and recording decisions

1. Identify affected decision, definition, requirement and open-item IDs. Consult rejection reasons and scope before revisiting an approach; inspect targeted source messages when provenance matters.
2. Record a proposed decision with rationale, alternatives, impacts and approval status. Obtain explicit user approval before applying material goal, semantic or scientific-contract changes. A discussion, example or engineering recommendation is not acceptance.
3. After approval where required, update the [Decision Register](02_DECISION_REGISTER.md) and its [structured companion](ARCHITECTURE_REGISTER.json). Preserve history and distinguish acceptance, rejection, supersession, proposal and unresolved status. Update the [Rejected Decisions](03_REJECTED_DECISIONS.md) when an alternative's disposition changes; version affected [Definitions](04_DEFINITIONS.md) rather than silently rewriting meaning.
4. Update affected requirements, architecture, blueprint, open decisions and traceability; verify the corresponding acceptance criteria and tests. Ordinary implementation details need not become new scientific decisions. Preserve the original source archive; later source recovery gets separate provenance.
5. Refresh this snapshot when verified capabilities or repository context change. State what exists, what remains conceptual and what was actually checked. Keep canonical decisions in their registers rather than resolving them in this handoff.
