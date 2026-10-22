# Session-understanding repair

Date: October 22, 2026. Review base: `2ab0cbedbec47b5bdef5a520b8aa9490baa7ac63`.
Scope: repository instructions and their behavioral verification. This is not a scientific-contract change, framework implementation, or approval of unresolved semantics.

## Observed failure and diagnosis

The current conversation provides an observed failure: the assistant read the entry documents and relevant decisions, but repeatedly gave fresh forward confirmation too much weight when assessing the usefulness of the entire research loop. The user had to restore two distinctions: framework-level acceleration versus individual hypothesis support, and useful early elimination versus eventual confirmation. The information was available, including D013 (historical-first), D019 (experience can guide search), D025 (framework-level evaluation), and the problem definition's statement that a failed hypothesis can be useful research.

This establishes a synthesis failure in this conversation. It does not establish how frequently other sessions fail, prove a particular internal model mechanism, or show that context compaction caused this incident. No desktop session-loading trace or cross-model measurement was available.

The following repository-level contributors are supported by inspection of the baseline:

1. `AGENTS.md` sent every task first to README and Current State, but reserved the master-architecture reading rule for design/implementation. An external critique could be handled through local decision lookups without first rebuilding the whole information flow.
2. The entry instructions emphasized restrictions, evidence boundaries and unresolved work. They did not explicitly keep research acceleration and useful negative outcomes beside those restrictions. The original problem definition already allowed useful failed hypotheses, but the entry route did not require integrating that fact with D013 and D019.
3. There was a reading checklist but no observable synthesis step: no requirement to connect a recommendation to the project goal, affected research stage, existing mechanism and evidence/success level. Finding a correct decision was too easily substituted for assessing its system-level consequence.
4. The handoff contained a task-specific statement about what the earlier preparation task authorized. In a new task, that wording could be misread as a continuing ban on otherwise explicitly authorized work. This is a plausible adjacent entry-point problem, not the demonstrated cause of the critique error.

The proposed mechanism is therefore selective retrieval plus loss of relationships between known facts, reinforced by the external critic's framing. The assistant remains responsible for the error; the documentation's existence did not excuse failing to integrate it. Adding more exhaustive architecture prose would not directly fix this mechanism.

## Current-session source clarification

These are exact user quotations from the current conversation, recorded separately from the original 304-turn archive. No original archive bytes were edited. The current session has not been captured as a complete transcript; no original message IDs are asserted here.

> Warte mal, das Framework soll nicht JAHRE damit zubringen etwas zu testen. Eine Anforderung bei der Idee zu diesem Framework war es, die Hypothesensuche UND Tests massiv zu beschleunigen, Das ist, das zweite Ziel was das framework leisten soll

> Das wäre ein Erfolgskriterium für das framework selbst. Hypothesen dürfen schnell sterben, und es gibt im Framework mechanismen dafür

These clarify the user's success objective and the intended interpretation of existing mechanisms. They do not approve numerical speed targets, evidence upgrades, lifecycle changes, or resolutions of OPEN-01 through OPEN-03/OPEN-14. Recording the clarification in repository instructions is within the user's explicit request to implement those instructions. Canonical scientific contracts and their structured register remain unchanged.

## Smallest practical intervention

The operative change is in root [AGENTS.md](../../../AGENTS.md), where new sessions already receive repository guidance. No new runtime, memory service, mandatory skill, agent topology or duplicate architecture document is introduced.

- Keep both project objectives and the end-to-end research loop next to the existing invariants.
- State the relationships most likely to be lost: rapid justified elimination is useful; historical observation duration differs from elapsed testing time; experience can guide search without upgrading evidence; bounded execution need not restrict invention; framework, hypothesis and policy success are separate.
- Require the complete short Problem Definition and Master Architecture once before a system-level critique/design/implementation, then targeted authoritative lookups. Reconstruct that model after context loss; do not pretend truncated output is a complete read.
- Require a short, task-relevant connection between outcome, loop stage, existing mechanism and evidence level before a system-level conclusion. Verify absence claims and the exact scope of rejection records.
- Exempt wording-only tasks from the full reading/synthesis pass. Preserve current user authorization and existing change control.

[Current State](../../architecture/CURRENT_STATE.md) is maintained descriptively. Scientific decisions, definitions, source archives, future application tests and actual framework capabilities are unchanged.

## Verification design

The [protocol](protocol.json) was written and hashed before any behavioral runs and before instruction edits. [The manifest](manifest.json) records the baseline commit, pre-edit file hashes, deterministic shuffled schedule, isolated snapshot inputs and instruction hashes. There are five paired tasks: external criticism, first-slice planning, mixed-result interpretation, a one-label local edit, and pressure to misuse historical evidence for speed. Each condition/task gets a fresh subagent without parent conversation or personal memory; test agents cannot read the rubric, other runs or this report. Only the local-edit task can modify its own snapshot. No test agent changes the live project.

The ten runs use the inherited model configuration with no model override. Condition order is shuffled with seed `221026`; execution is bounded to three concurrent workers. One run per task/condition provides a behavioral smoke test, not a statistical reliability estimate. The package combines orientation content with procedural instructions; their separate effects are not identified. This is a pragmatic application of the experimental-design skill's control, blocking and predeclared-outcome guidance, not a powered scientific trial.

Scoring uses the frozen task-specific criteria and critical-error list. Responses are retained before a fresh reviewer scores anonymized run IDs; the coordinator checks the judgments against response excerpts. The reviewer can infer some conditions from response content, so this is label masking, not guaranteed blinding. Failures will remain recorded, not be replaced by favorable reruns.

## Results and limits

The first ten responses were frozen and independently scored against all 38 task criteria. The baseline passed 3/5 tasks (17/19 criteria); the first revised instructions passed 4/5 tasks (18/19 criteria). No critical error was identified. Both versions passed the original forward-waiting critique task: the central conversational failure was **not reproduced** in that fresh-context probe.

The failures were narrow response-completeness findings, not demonstrated scientific-boundary violations:

- Both triage responses required speed/cost/quality measurements but did not explicitly require a suitable comparative workflow for an acceleration claim. The revised response's unspecified "predefined expectations" did not meet the frozen criterion.
- The baseline slice response retained capability gaps but did not explicitly require typed gaps or distinguish gap categories. The revised slice response did.

The coordinator agrees with these judgments under the predeclared conjunctive criteria; all three failed answers were otherwise substantially sound. The initial 3/5 versus 4/5 difference is not evidence of a reliable effect size or of preventing the original framing error.

A single repair added an explicit named comparable-workflow/prior-version requirement for acceleration claims, while preserving the prohibition on introducing a rejected comparator generator without authorization. [Protocol v2](protocol-v2.json) was frozen before this edit and before its five fresh runs. The same five tasks and criteria were repeated; original failures and both v1 conditions remain retained. These are repair/regression checks against the final wording, not a new concurrent controlled trial or independent held-out validation.

| Task | Baseline | Revised v1 | Final revised v2 |
|---|---|---|---|
| External critique / forward-waiting inference | Pass | Pass | Pass |
| First-slice planning | Fail: typed gaps not explicit | Pass | Fail: typed gaps not explicit |
| Mixed-result interpretation | Fail: comparative reference missing | Fail: comparative reference missing | Pass |
| Bounded README edit | Pass | Pass | Pass |
| Pressure to misuse historical evidence | Pass | Pass | Pass |
| All criteria satisfied per task | 3/5 | 4/5 | 4/5 |
| Individual criteria satisfied | 17/19 | 18/19 | 18/19 |
| Observed critical errors | 0 | 0 | 0 |

The final triage response explicitly requires a named comparable workflow or prior version with matched scope and evidence access. The targeted repair therefore worked in that probe. However, the final planning response retained unsupported ideas and capability gaps without explicitly typing/classifying the gaps; it failed the same conjunctive criterion as the baseline planning answer. This is an omission in the answer, not evidence that an implemented registry lost gap types. The coordinator accepted the second reviewer's judgment under the same frozen rule.

**The predeclared all-five-tasks behavioral acceptance gate was not fully met.** The final result is partial, not a demonstrated cure for context loss. The small general orientation and synthesis instructions are implemented, and no critical boundary regression was observed, but a statistical reliability improvement has not been established. No further instruction clauses were added merely to force every known prompt to pass. In particular, the moving location of a narrow omission warns against treating one favorable run as a guarantee.

Evidence is retained in [assessment.json](assessment.json), the unmodified independent [v1 grading](grading-v1.json) and [v2 grading](grading-v2.json), and all 15 files in `responses/`. The complete tasks and criteria remain in the protocols. The final instruction hashes match the v2 snapshots; the initial hashes and failed outputs remain in the manifest. All answers met the 450-word response limit (file lists excluded); this brief-answer setting tests explicit synthesis, not a full implementation's behavior.

Static and mutation verification passed using `python docs/reviews/session-understanding/verify.py --snapshots` and `git diff --check`: exactly two pre-existing files changed, the other 25 pre-existing files stayed byte-identical, all five archived source hashes/sizes matched their original manifest, all 15 snapshots had only their authorized changes, and the three local-edit runs changed exactly the requested README label while preserving every other byte. Local Markdown links/anchors and frozen protocols/responses were checked. The final machine-readable output is [verification.json](verification.json); it reports integrity checks separately from manual behavioral assessment. No application tests or market experiments were run.

The test does not cover actual desktop new-chat instruction injection, other model families, repeated stochastic trials, long-session drift or every possible task. File-reading lists are agent-reported, not independently instrumented access traces. The inherited model configuration was not independently pinned to a provider release fingerprint. Passing instruction probes cannot prove scientific validity or framework performance. The original error occurred in an ongoing critique discussion; fresh-context probes are a related test, not an exact replay of that full conversation.

To repeat the integrity checks, run the command above while temporary snapshots still exist, or omit `--snapshots` afterward; omitted snapshot checks are explicitly reported as unverified on that rerun. To repeat behavioral probes, reconstruct the baseline at the manifest's commit, overlay only the two instruction/handoff files for the revised condition, and dispatch each protocol task into its own fresh context using the common prompt. Save outputs before revealing the rubric and score all runs, including failures. Do not reuse test-agent memory or silently replace an unsuccessful response. The manifest records the small run-03 dispatch-path correction and other execution details.

## Maintenance and rollback

Keep the root orientation short and sourced. Update it only when accepted goals/boundaries change or an observed misunderstanding warrants a bounded correction; do not copy every new architecture detail into it. Keep test prompts and criteria fixed for comparisons, retaining failed runs and explicitly versioning new tests. Historical test reports do not automatically validate later instruction edits.

Rollback the AGENTS.md and Current State changes using the retained baseline commit or the pre-edit hashes and Git diff. Retain this report and observed failures as history. No scientific evidence or exposure is erased by an instruction rollback.

## Method attribution

The installed `code-work` skill supplied bounded-change and fresh-verification guidance; `experimental-design` supplied the paired controls and predeclared assessment approach. Neither skill is a dependency of the repository instructions. The experimental-design skill belongs to Kassis, T., Agarwal, V., He, Y., Patel, D., and Brueckner, A. M. (2026), [Scientific Agent Skills: A Library of Procedural Knowledge for Research Agents](https://doi.org/10.48550/arXiv.2609.00065). Bibliographic metadata checked against the arXiv record on October 22, 2026 (latest record: v2). This citation does not supply evidence that the present instruction change works.
