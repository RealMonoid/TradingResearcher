# Independent Engineering Review

Review basis: the preserved conversation, reconstructed decisions and the current documentation-only workspace. This is a fresh critical engineering pass independent of the source assistant's recommendations. It is not an independent-person audit, an application-code review or an executed integration assessment.

## Assessment

The scientific responsibilities are coherent, but the design is not implementation-ready until a few contracts are resolved. The largest practical risk is treating prose about isolation, freeze and provenance as if those boundaries were already enforced. The smallest useful implementation needs a real LLM idea, a typed formalization boundary, a deterministic executor, an atomic freeze and a reconstructable evidence record. Agent/runtime breadth should follow measured need.

M0246 recommended a vertical slice; M0247 deferred that implementation discussion. The roadmap here is therefore a reviewable recommendation under the current documentation task, not a recovered approval to implement or to replace the multi-perspective target.

## Findings

| ID / priority | Finding and consequence | Required resolution / verification | Authority |
|---|---|---|---|
| ENG-01 / critical | Flat example schemas cannot express all accepted claim forms; a narrow compiler could quietly become a rule catalog | Typed expression/estimand contract; fixtures for all five forms and typed gaps; TEST-02 | D002–D003; OPEN-04 |
| ENG-02 / critical | Model prompts alone cannot protect holdout data or evaluator output | Host-enforced capabilities, isolated contexts and separate result-writing authority; TEST-04/13/14 | D005, D014, D034 |
| ENG-03 / critical | Freeze, trial registration and artifact storage can diverge after a crash | Atomic manifest/registry transaction or explicit recovery protocol; deterministic idempotency; TEST-05 | Implementation recommendation supporting D006 |
| ENG-04 / critical | Exposure is not just a list of time ranges attached to one H | Maintain transitive artifact-level lineage including query answers, external sources and memories; preserve contamination on rollback; TEST-13 | D014, D019, D026 |
| ENG-05 / critical | One mutable status conflates execution, evidence, applicability and deployment | Versioned state model; retain original M0072 semantics; OPEN-01 must resolve before affected implementation | D008, D020, D067 |
| ENG-06 / high | Feature certification can be circular if generated expected values share implementation bugs | Separate author/spec fixtures from implementation; hand-checkable cases, causality and metamorphic tests; TEST-03 | D004 |
| ENG-07 / high | Policy subset transport and family prevalence can create false confidence | Resolve OPEN-02 and OPEN-03; do not encode disputed interpretations as facts | D066, D024 |
| ENG-08 / high | Backend speed does not establish faithful fills or arbitrary path-dependent management | Capability matrix and synthetic accounting/path cases; unsupported behavior returns explicit failure; TEST-12/18 | D013, D042 |
| ENG-09 / high | Automatic runtime memory/skills can mutate the effective generator version mid-epoch | Freeze runtime profile; route material changes to proposals; provenance-preserving retrieval/compression; TEST-16/21 | D005, D019, D026, D041 |
| ENG-10 / high | Score-blind improvement in a library does not guarantee protected network/file access | Independent final evaluation authority and capability tests; no final score to proposer/composer | D040; current Harness2 README caveat below |
| ENG-11 / high | Source chronology contains multiple shorthand status names and later qualifications | Preserve aliases as historical records, bind canonical versions and prohibit unsupported migrations; TEST-07 | D008 |
| ENG-12 / medium | Many logical roles could become unnecessary services | Start with owned modules and narrow interfaces; add deployment boundaries only for proven isolation/scale need | D030 |
| ENG-13 / medium | Repeated failures and negative research could disappear into retry behavior | Append-only error and trial history, bounded retries, no duplicate scientific trials; TEST-06/23 | D007, D030 |
| ENG-14 / medium | Dashboard ratios can compare immature cohorts or different metric definitions | Version definitions and expose denominators, pending replications and time-to-outcome; TEST-22 | D028 |

## External integration review

Read-only primary-source verification performed October 22, 2026. This refresh confirms only the stated repository/documentation observations. It does not confirm installation, pinned versions, security, performance, legal suitability or API compatibility. Historical source claims of a detailed code audit are not adopted as evidence that this reconstruction performed one.

| Candidate | Recovered role / decision | Current primary-source observation | Recommendation and boundary |
|---|---|---|---|
| vectorbt | Primary backend candidate, accepted in M0237–M0238; D042 | [README](https://github.com/polakowo/vectorbt/blob/master/README.md) describes vectorized pandas/NumPy/Numba research, portfolio statistics and random signals; it distinguishes PRO capabilities including limit orders and leverage. [License](https://github.com/polakowo/vectorbt/blob/master/LICENSE.md) includes Apache 2.0 with Commons Clause | Keep the selected candidate behind VectorBTAdapter. Pin release and edition; test exact cost/fill/path behavior. Review intended use against full license before distribution; no legal conclusion is asserted |
| Hermes Agent | Serious runtime candidate, not selected scientific core; M0232–M0234; D041 | [README](https://github.com/NousResearch/hermes-agent/blob/main/README.md) presents provider/tool/session/memory functionality, automatic skill learning and MIT licensing | Candidate for generic runtime. Its automatic learning cannot silently change the frozen researcher; isolate or disable incompatible mutation paths and verify conformance |
| Harness2 | Role-limited improvement patterns; M0228–M0230; D040 | [README](https://github.com/google-research/harness2/blob/main/README.md) describes Propose–Probe–Compose with fixed model weights and Apache 2.0; setup targets Linux/Python 3.12. It explicitly warns that executor network access is unrestricted and Codex sandboxing disabled by default | Use as a pattern/source candidate only after isolation adaptation. Default setup is not evidence separation; Windows compatibility and restricted execution are unverified |
| RD-Agent(Q) | Workflow/provenance patterns; source comparison M0132/M0140 | Not independently re-audited in this pass | Do not inherit factor/model fitness optimization or a mandatory dependency; inspect exact source/version/license before copying code |
| OpenEvolve | Worker/provider/checkpoint ideas; M0132/M0134/M0140 | Not independently re-audited in this pass | Generic patterns only; reject population fitness as scientific truth. No requirement to install alongside Hermes |
| AI Scientist / AlphaEvolve | Architecture comparisons and inspiration; M0134/M0140 | Not independently re-audited in this pass | No selected core dependency. Do not reproduce historic publication/availability claims as verified current facts |
| POPPER | Implication/falsification reference; M0136/M0140 | Original [ICML paper](https://proceedings.mlr.press/v267/huang25n.html) describes agentic sequential falsification | Methodological reference, not plug-in evidence authority; financial dependence and test validity still need independent justification |

## Recommendation categories

**Keep:** scientific ownership, free discovery, expression-gap preservation, immutable evidence lineage, policy separation, operational firewall and the accepted scope.

**Simplify without changing goals:** logical modules in one application where permissions remain enforceable; one append-only event store with typed projections rather than one database per registry; one narrow runtime adapter and one test backend candidate. These are engineering proposals, not historical database decisions.

**Resolve before encoding:** lifecycle/status migration, subset transportability, family prevalence interpretation, executable language semantics, statistical rules and source/data authority. These are concrete open decisions in document 11.

**Defer:** full runtime integration, live deployment, rich dashboards, semantic relation inference, elaborate generator meta-learning and broad source-domain expansion until each has a demonstrated milestone need. Deferred capability remains in the target architecture.

No recommendation changes the fundamental goal. Any future replacement of free LLM invention, independent evaluation or confirmation separation must be labeled **GOAL CHANGE — USER APPROVAL REQUIRED**. No such goal change is proposed here.
