# Requirements and Observable Acceptance

These requirements consolidate the source-backed decisions; D071-D085 now select the scoped policies and infrastructure design in document 14. Each acceptance condition below is a future implementation test specification, not a test reported as executed. Decision/source provenance is in [02_DECISION_REGISTER.md](02_DECISION_REGISTER.md).

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
| REQ-014 | Adaptive pre-freeze search with sourced queries and tools | Search actions, responses, parameters, timestamps, permissions and costs are logged; external instructions cannot mutate scientific policy; D086 adds object/purpose framing, open exploration, assumption checks and concise sourced investigation summaries under [agent-inquiry/1.0](15_AGENT_INQUIRY_DISCIPLINE.md) | TEST-14 |
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

TEST-27 is a future framework-level acceptance specification for D068, not an executed benchmark or a new statistical policy. D081 selects the scoped improvement target and measured intervals; the actual named reference, matched tasks and comparison plan must still be frozen before results. Historical processing time and waiting for genuinely new outcomes must be distinguished. This does not authorize D015's rejected baseline generator, make the number of rejections a reward, or replace D025's calibration and economic gates.

## Selection and exposure acceptance coverage

The [evaluation supplement](07_SCIENTIFIC_EVALUATION.md#overfitting-controls-across-the-research-process) applies existing requirements across the whole research process. The [worked acceptance cases](12_TRACEABILITY_MATRIX.md#selection-and-exposure-acceptance-cases) make the following boundaries observable without adding a universal estimator, numerical threshold or new TEST ID:

- REQ-005/024/029 distinguish assessment of a frozen candidate from assessment of a selection/adaptation procedure. Fitting or selection using evaluation outcomes cannot be hidden outside an advertised evaluation boundary.
- REQ-003/004/013/015/028 apply to fitted preprocessing, retrieved lessons, pass/fail feedback and diagnostic-based selection, not only direct access to future price rows.
- REQ-019/020 require a justified dependence/error/allocation policy and calibration matched to the assessed selection process. Shared predeclared confirmation is not automatically forbidden; independent seeds or a complete ledger are not sufficient proof of validity.
- REQ-009/026 distinguish retained-trade diagnostics from executable policy performance when changed decisions affect opportunities, positions or costs.

These are elaborations of the existing acceptance conditions. They are not executed tests, a replacement for document 13 version 1.0, or by themselves resolutions of OPEN-05/11/12; D075/D081/D082 now supply those scoped policies. Statistical policy and access assumptions must be concrete before the affected confirmatory operation; exploratory preparation can retain explicit gaps.

## Nonfunctional requirements

D069-D070 and the [Generator Feedback and Evaluation Contract](13_GENERATOR_FEEDBACK_AND_EVALUATION.md#acceptance-specifications) specify TEST-28 through TEST-30, including invalid cases. These are future behavioral tests, not executed application tests. Economic usefulness requires profitably usable hypotheses under realistic costs and separate policy validation; competing-generator or quantitative-firm superiority is not required. Positive results are outcomes, not build/run entry prerequisites.

Persist an artifact before acknowledging success. Repeated delivery or retry must not create duplicate primary trials or contradictory freezes. Preserve enough source, code, data and configuration identifiers to reconstruct a deterministic evaluation within declared numeric tolerances. LLM proposal regeneration is not guaranteed to be bit-identical; the stored proposal and its provenance are the reproducibility unit.

Access boundaries must be enforced by the host, not merely described in prompts. Logs must reference secrets without retaining secret values. External text and memory are data, not instructions that grant permissions. Use bounded resource policies with explicit exhaustion states, while preserving the freedom to submit an idea that cannot yet be executed.

D075/D079/D081 specify scoped statistical, token/call/time and calibration policies. Measured throughput, monetary costs, availability guarantees and any retention schedule remain unverified or future inputs. No unmeasured performance claims are made.

## Binding research-contract/1.0 acceptance extension

The full policies and acceptance cases in [document 14](14_RETAIL_RESEARCH_CONTRACT.md) are normative for the affected requirements; the [closure mapping](12_TRACEABILITY_MATRIX.md#approved-closure-acceptance-mapping) assigns them to existing TEST IDs. No new application test is claimed.

- REQ-002/003/007: preserve H_idea and legacy versions; validate typed AST meaning and independent certification; unknown legacy origin cannot become known through migration.
- REQ-005/006/012/019/024: freeze the complete interval/effect/dependence/information and release policy, reserve the whole batch atomically, distinguish invalidity from a negative, retain all outcomes, and deny result-driven changes. Re-execution is not replication.
- REQ-008/009/017/025: scope inclusion alone cannot certify a rule; dependency revocation changes usability while preserving original outcomes; applicability is assessed at use; research outputs authorize zero capital.
- REQ-004/013/014/018/021: host-enforced isolation and immutable version provenance, bounded calls and exposure inheritance; only unchanged approved semantics permit automatic certification.
- REQ-011/015/026/029: apply the initial data/execution profile without narrowing future hypothesis scope; preserve availability and fee uncertainties; resimulate changed paths; separate technical, calibration and economic claims.
- REQ-020/022/023/027/028/030: preserve cohort denominators and pending cases, distinguish narrow from process calibration, enforce finite resource stops, measure both acceleration intervals and prevent partial-batch feedback or novelty-based scientific rewards.
