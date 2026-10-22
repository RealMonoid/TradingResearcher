# Requirements and Observable Acceptance

These requirements consolidate the source-backed decisions; they do not select still-open numeric thresholds or infrastructure products. Each acceptance condition below is a future implementation test specification, not a test reported as executed. Decision/source provenance is in [02_DECISION_REGISTER.md](02_DECISION_REGISTER.md).

| ID | Required behavior | Observable acceptance condition | Verification |
|---|---|---|---|
| REQ-001 | LLM invents hypotheses; code independently evaluates | A novel free-form idea is retained and operationalized; neither a closed rule menu nor the LLM can assign empirical support | TEST-01 |
| REQ-002 | Separate idea and executable claim; expressive extensible language | Fixtures cover difference, association, change, boundary and interaction with binary/continuous outcomes and AND/OR/NOT; unsupported concepts retain a typed gap | TEST-02 |
| REQ-003 | Versioned certified features and primitives | Independent golden cases, temporal causality, units, missing data and dependency revocation pass; implementer cannot self-approve | TEST-03 |
| REQ-004 | Frozen PIT contexts and isolated roles | Two discovery runs see the same allowed epoch input and cannot access each other's scratch state, future data or evaluator-owned outputs | TEST-04 |
| REQ-005 | Complete claim, universe and evaluation contract before freeze | Missing comparator, estimand, horizon, effect criterion, family policy, stopping rule or required versions rejects freeze with exact reason | TEST-05 |
| REQ-006 | Technical failure is distinct from negative evidence | Injected data/compiler/backend failure creates an error record and quarantines the affected run without assigning TESTED_NEGATIVE | TEST-06 |
| REQ-007 | Canonical definitions and English project artifacts | Every experiment resolves exact definition versions; incompatible reinterpretation is rejected; quotations keep source language | TEST-07 |
| REQ-008 | Minimal provenance and typed dependency semantics | Cycles/unknown versions are detected; hard infrastructure revocation propagates; genealogy or a proposed contradiction does not automatically invalidate evidence | TEST-08 |
| REQ-009 | Policies are separately tested claims with rule provenance | Every rule identifies basis, scope relation, parameter origin and conflicts; combined policy has its own freeze, trials and evidence | TEST-09 |
| REQ-010 | Mechanisms and adversarial checks produce testable implications | A causal claim has premises, observable consequences, alternative explanation and predicted boundaries; survival of critique grants no evidence status | TEST-10 |
| REQ-011 | V1 discovery observation timeframe at least 15 minutes | Five-minute discovery input is rejected by configured scope while an hours/days outcome on 15-minute inputs is accepted | TEST-11 |
| REQ-012 | Separate backtest adapter, historical and forward evidence | Identical frozen request can be replayed; result includes data/cost/fill/execution versions; backend cannot write evidence status | TEST-12 |
| REQ-013 | Exposure propagates through all used ancestry | A hypothesis using a memory derived from an old holdout cannot use that holdout as independent confirmation; rollback does not clear exposure | TEST-13 |
| REQ-014 | Adaptive pre-freeze search with sourced queries and tools | Search actions, responses, parameters, timestamps, permissions and costs are logged; external instructions cannot mutate scientific policy | TEST-14 |
| REQ-015 | Broad data domains with availability/vintage semantics | Revised fundamental/on-chain data are unavailable before actual release/confirmation/provider availability and processing time | TEST-15 |
| REQ-016 | Four memories with distinct authority | Experience can influence search but cannot upgrade market evidence; negative, conflicting and retired entries remain retrievable | TEST-16 |
| REQ-017 | Evidence-to-decision separate from evidence status | A deployment policy can restrict action without changing scientific evidence; no status implicitly authorizes a capital amount | TEST-17 |
| REQ-018 | External runtime/backend behind narrow owned contracts | Candidate capability, version and license review recorded; conformance fixtures run before adoption; unsupported operations fail explicitly | TEST-18 |
| REQ-019 | Confirmation queue allocates finite fresh evidence | Selected and nonselected ideas remain recorded; allocation is frozen before confirmatory outcomes; insufficient evidence remains inconclusive | TEST-19 |
| REQ-020 | End-to-end null/signal/process calibration | Same selection opportunities are exercised on real and null processes; outcomes include uncertainty and power, with fresh evaluation data | TEST-20 |
| REQ-021 | Material improvements need approval and rollback | Unapproved activation is denied; rejected/failed probes remain registered; rollback restores configuration but not evidence freshness | TEST-21 |
| REQ-022 | Diagnostic dashboards with stable denominators | Metrics identify version, cohort, censoring and sample count; technical and research outcomes cannot be merged into a single success score | TEST-22 |
| REQ-023 | Small bounded implementation and measured stopping | Each change maps to current acceptance criteria; two no-improvement iterations stop; oversized components and cost overruns trigger review | TEST-23 |
| REQ-024 | Full selection provenance and suitable robustness tests | Winning filter/parameter is traceable to all evaluated alternatives; sensitivity/null design is preregistered and method-specific | TEST-24 |
| REQ-025 | Operational feedback firewall | Raw fills/PnL cannot modify claims, protocols or evidence; registered observations enter a later research epoch through controlled interfaces | TEST-25 |
| REQ-026 | Event/trade Column Library with three timing classes | Full-path extrema cannot be joined into entry features; evolving state is truncated at decision time; exploratory reuse is not independent confirmation | TEST-26 |
| REQ-027 | Substantially accelerate both hypothesis discovery and testing while preserving decision quality | A preregistered comparison with a named workflow or prior version measures discovery and test-cycle time/cost under matched scope, decision quality and evidence access; reports early exits, gaps, errors, inconclusive results and completed tests separately; meets the improvement threshold without weakening technical/scientific gates | TEST-27 |
| REQ-028 | Feedback observations, interpretations and later uses remain distinct and auditable | Source/check versions, availability, validity, exposure, uncertainty, intended influence and heuristic review triggers are retained; use precedes downstream outcome; technical failure or reflection cannot assign market evidence | TEST-28 |
| REQ-029 | Assessment readiness and claims match their actual purpose | Absolute usefulness can be investigated without prior profit or competitor superiority; comparison claims require an appropriate reference and matched resources/information; plans retain pending/failing cohorts and distinguish uncertainty from equivalence or falsification | TEST-29 |
| REQ-030 | Diagnostic discovery coverage without a novelty gate | Known analogues, not-searched and none-found outcomes remain distinguishable; method-versioned similarity and H_idea/H_exec coverage are reported without automatic evidence, originality certification or diversity rewards | TEST-30 |

TEST-27 is a future framework-level acceptance specification for D068, not an executed benchmark or a new statistical policy. OPEN-11 must select the reference, measures, quality criteria, improvement threshold and comparison design before results. Historical processing time and waiting for genuinely new outcomes must be distinguished. This does not authorize D015's rejected baseline generator, make the number of rejections a reward, or replace D025's calibration and economic gates.

## Nonfunctional requirements

D069-D070 and the [Generator Feedback and Evaluation Contract](13_GENERATOR_FEEDBACK_AND_EVALUATION.md#acceptance-specifications) specify TEST-28 through TEST-30, including invalid cases. These are future behavioral tests, not executed application tests. Economic usefulness requires profitably usable hypotheses under realistic costs and separate policy validation; competing-generator or quantitative-firm superiority is not required. Positive results are outcomes, not build/run entry prerequisites.

Persist an artifact before acknowledging success. Repeated delivery or retry must not create duplicate primary trials or contradictory freezes. Preserve enough source, code, data and configuration identifiers to reconstruct a deterministic evaluation within declared numeric tolerances. LLM proposal regeneration is not guaranteed to be bit-identical; the stored proposal and its provenance are the reproducibility unit.

Access boundaries must be enforced by the host, not merely described in prompts. Logs must reference secrets without retaining secret values. External text and memory are data, not instructions that grant permissions. Use bounded resource policies with explicit exhaustion states, while preserving the freedom to submit an idea that cannot yet be executed.

Latency, throughput, token budgets, storage retention, availability targets and calibration tolerances are unresolved quantitative requirements (OPEN-05, OPEN-09, OPEN-11). No unmeasured performance claims are made.
