# Problem Definition

Version: reconstruction-1 with approved clarifications D068-D069 (October 22, 2026). Original source limits remain in [00_SOURCE_AUDIT.md](00_SOURCE_AUDIT.md); later user clarifications are recorded separately from the archive.

## Fundamental problem

Build an autonomous market-research workflow in which an LLM independently develops nontrivial hypotheses from market observations and available knowledge, turns them into executable specifications before testing, and submits them to independent code for evaluation on appropriately separated evidence. Preserve what was learned, what failed, what was exposed and what remains uncertain. Use that knowledge to research adaptive trading policies without confusing a good historical strategy with a supported market claim.

The decisive user constitution is M0057, reinforced by M0059 and M0107. The exact source statement is:

> Ein Agent-Workflow, in dem ein LLM aus Marktdaten und vorhandenem Wissen selbstständig nichttriviale Hypothesen entwickelt, sie vor dem Test in ausführbare Form bringt, und in dem Code sie anschließend unabhängig an neuen Daten prüft.

Source: [M0057](../../sources/full_conversation.md#m0057--user). D001 records its non-negotiable status.

The framework has two linked goals: autonomous nontrivial invention with faithful independent evaluation, and substantial acceleration of **both hypothesis discovery and testing** (D068). Acceleration concerns the complete research process, including useful early elimination and retained failures. It must preserve scientific decision quality and evidence boundaries; more generated or rejected ideas alone do not demonstrate success.

## Why this problem matters

The conversation starts with a chart-specific hypothesis, but quickly distinguishes noticing a pattern, forming a scientific claim and knowing whether that claim survives testing. It then asks how the generator itself can become a better researcher without merely learning to explain historical winners. An autonomous system amplifies both discovery capacity and selection bias: it can inspect many features, ask outcome-dependent questions, revise explanations, synthesize policies and recycle those results through memory. A frozen backtest alone does not control this whole process.

The desired output is therefore an auditable chain from question to evidence and decision. Profitable backtests are neither sufficient proof of the research process nor the sole definition of useful knowledge. Economic usefulness remains an eventual project gate, alongside technical validity and calibration; profitability has not been demonstrated.

## Problem-to-requirement map

| Problem | Consequence to prevent | Required response |
|---|---|---|
| PROB-01: Free invention versus controlled execution | A rule catalog or expressive bottleneck replaces discovery | REQ-001 through REQ-003 |
| PROB-02: Information contamination | Historical outcomes return through queries, papers, memory or ancestors | REQ-004, REQ-012 through REQ-016 |
| PROB-03: Selection and weak evidence | Best historical survivor is labeled scientific truth | REQ-005, REQ-019, REQ-020, REQ-024 |
| PROB-04: Meaning and dependency drift | The same name or status silently means something different | REQ-006 through REQ-008, REQ-021 |
| PROB-05: Knowledge-to-action gap | Evidence for components is treated as evidence for a policy | REQ-009, REQ-010, REQ-017, REQ-025, REQ-026 |
| PROB-06: Unbuildable scope and unmeasured quality | More agents, services and metrics substitute for useful research | REQ-018, REQ-022, REQ-023 |
| PROB-07: Scope mismatch | Five-minute examples or OHLCV-only adapters constrain the actual mandate | REQ-011, REQ-015, REQ-026 |
| PROB-08: Research speed detached from purpose | A valid research process does not materially accelerate discovery and testing, or buys speed by weakening decisions | REQ-027, with REQ-005, REQ-006, REQ-016 and REQ-020 |

## Scope evolution that must survive reconstruction

| Source interval | Change in understanding | Final consequence |
|---|---|---|
| M0001–M0028 | Chart hypothesis becomes a question about the research process; introspection and composite scores are challenged | Observe artifacts and preserve ex-ante quality separately from outcomes |
| M0029–M0056 | Variation, causal uncertainty and multiple discovery routes | Controlled diversity; no mandatory mechanism or SPC chart |
| M0057–M0074 | User constitution, autonomous roles, compiler, certification, formulas and errors | Strict confirmation boundary; free ideas and retained language gaps |
| M0075–M0100 | Adaptive policies, hypothesis relationships and revised time scope | Minimal dependency graph; 15-minute minimum discovery; swing allowed |
| M0101–M0138 | Historical-first, no simple generator, queries, multimodal data, problem finding and second policy search | Exposure lineage and distinct research/policy trials |
| M0139–M0174 | Reuse, provenance, evidence budget, base rates, calibration, memory and governed improvement | Own scientific core; no automatic evidence upgrade or self-modification |
| M0175–M0208 | Quantitative claims, dashboards, web research, scope governance and robustness | Explicit universes, costs, fitted-parameter tests; no universal statistical recipe |
| M0209–M0248 | Adversarial checks, operational firewall, placebos and infrastructure candidates | Narrow external adapters; implementation priorities still deferred |
| M0249–M0290 | Column Library, paths, null design, component analysis, bounded computation and sanity | Reusable diagnostics without leakage or free confirmations |
| M0291–M0304 | Request for original-source reconstruction and explicit rejected decisions | The handoff must preserve chronology and rationale, not summarize only the endpoint |
| Later user clarification, October 22, 2026 (D068) | Accelerating discovery and testing is an explicit framework success objective | Trace it to REQ-027 and TEST-27; apply scoped D081 targets; freeze the actual comparison before measurement |

## Success and non-goals

The economic objective is to generate hypotheses that can be used profitably under realistic costs and execution constraints (D069). The project need not beat quantitative firms or prove superiority over another hypothesis generator. Profitability is to be discovered and evaluated; it is not assumed or required before building the system. A supported relationship does not by itself establish a profitable policy, so economic evaluation retains the separate policy contract and uncertainty requirements.

Success requires a freely generated claim to pass through formalization, provenance, freeze, independent execution and reproducible evidence classification without manual scientific repair. The complete pipeline must behave acceptably under null and planted-signal calibration, then meet a predefined economic-usefulness gate within an evidence budget. Numeric budgets and thresholds are open, not silently supplied here.

Framework success also requires a measured substantial acceleration of discovery and testing under a predefined comparison with matched task scope, decision quality and evidence access (REQ-027). D081 adopts a scoped 50% reduction target for both median discovery-to-freeze and freeze-to-report time, with paired uncertainty and failures retained. The named reference workflow, matched tasks and assessment execution remain required pre-outcome inputs; D015's rejected comparator generator is not authorized by this requirement. Distinguish processing existing observations from waiting for new outcomes. Historical-first research can reject or refine candidates quickly while stronger independent confirmation remains a separate constraint.

A hypothesis succeeds or fails under its own frozen evaluation policy. A policy needs its own evidence and operational assessment. The framework is evaluated on the quality, efficiency, calibration and usefulness of the whole process: a valid negative hypothesis result can be useful progress without proving framework success, and a supported hypothesis does not by itself validate a policy. The [Master Architecture](06_MASTER_ARCHITECTURE.md) connects these levels and their feedback paths.

Entry criteria require a valid scoped investigation and the relevant resolved contracts, not advance proof of economic success or superiority. Absolute usefulness, procedural improvement, version improvement and acceleration answer different questions under the [Generator Feedback and Evaluation Contract](13_GENERATOR_FEEDBACK_AND_EVALUATION.md). D068's reference is for process acceleration; it does not impose investment outperformance or override D015. Exploratory/technical work may be informative before a confirmatory economic study is possible.

The framework is not a fixed strategy generator, an LLM judge of truth, a mandatory ontology, an unconstrained historical optimizer, or an automatic capital-allocation mandate. It may use known effects, data-first observations and cross-domain analogies, but must not require one discovery route. A failed hypothesis can be useful research; a technically invalid run is neither support nor falsification.

This deliverable is documentation, not implementation. It does not recover the missing chart or original project-file bodies, demonstrate an edge, verify a live strategy, or establish that a candidate dependency is production-ready.

## Approved retail research scope

D071-D085 adopt [research-contract/1.0](14_RETAIL_RESEARCH_CONTRACT.md) without changing the goals. Its finite historical work unit returns a scientific outcome and a separate resource decision; an information gap or inconclusive result can stop work without mandatory days of forward observation. Clean forward confirmation remains a distinct optional track, with inherited exposure preserved.

The two-instrument 15-minute profile is an initial bounded study, not a permanent restriction on free invention or broad data domains. No profitable-policy, calibration or acceleration result has been demonstrated. The [current dispositions](11_OPEN_DECISIONS.md) distinguish completed design choices from missing inputs and future capabilities.
