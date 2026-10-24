# Implementation Blueprint

Status: binding semantic specification with scoped implementation choices adopted in D071-D085; no application code is implemented. Source-backed behavior and research-contract/1.0 govern their stated scopes. Complete the remaining run inputs and conformance prerequisites before affected operations. Do not interpret this blueprint as user authorization for live trading or material framework self-modification.

## Minimal coherent implementation shape

Use a modular application with explicit ownership of context, discovery, formalization, registry/freeze, backend execution and evidence. Keep immutable artifact bodies in content-addressed storage and an indexed transaction-capable registry for identities, events and dependency edges. D078 selects one local SQLite writer plus content-addressed external blobs for v1; conformance and recovery remain unimplemented. A separate graph database, message broker, vector store and service mesh are not initially justified.

Use one orchestrator that routes artifacts and enforces permissions, not one that selects scientific conclusions. Roles can be sequential in an engineering smoke test. Target independent discovery perspectives must later be demonstrated with separate state and identical allowed context; a one-agent smoke test is not proof of that requirement.

## Interface contracts

Names below identify owned contracts; they are not promises about third-party APIs.

| ID | Interface / caller → owner | Request | Response and failure behavior |
|---|---|---|---|
| IF-01 | BuildContext: orchestrator → CMP-01 | Research time, data/knowledge/experience versions, scope and permission profile | Immutable snapshot and exposure closure; deny unresolved availability or unauthorized ancestry |
| IF-02 | DiscoveryTools: CMP-02 → CMP-01/CMP-07 | Bounded query or source/retrieval request with snapshot and purpose | Referenced response plus exposure event, availability, trust label and cost; no evaluator/holdout access |
| IF-03 | SubmitIdea / Formalize: CMP-02 → CMP-03 | H_idea, parent/source references and snapshot | H_exec draft with semantic-difference report, or typed gap retaining original idea |
| IF-04 | CertifyFeature / Compile: CMP-03 → CMP-04 | Feature spec or H_exec, definition/compiler versions, certified dependencies | Certificate or typed validation error; deterministic compiled representation with hash |
| IF-05 | FreezeTrial: orchestrator → CMP-04 | Complete executable artifact, assigned policy, selected allocation and exposure assessment | Durable FrozenManifest and TrialRecord atomically; same idempotency key returns same result, conflicting payload rejected |
| IF-06 | Execute: CMP-04 → CMP-05 | FrozenManifest, authorized evaluation partition, cost/fill/execution versions and seed if needed | ExecutionResult with raw case/path references, accounting checks and environment; typed unsupported/invalid/transient failure |
| IF-07 | Evaluate: CMP-05 → CMP-06 | Verified result hash and frozen EvaluationPlan | Immutable EvidenceRecord with effect/uncertainty and policy-determined outcome; invalid run cannot become empirical negative |
| IF-08 | RecordResearch / PublishKnowledge / Experience: producing roles → CMP-07; CMP-06 → CMP-08 | Search trajectories, abandonment, gaps, queue decisions, errors, policy results or qualified evidence, with event type and full ancestry | Append journal events regardless of evaluation completion; derive labeled heuristics separately; only valid qualified evidence updates market evidence; new context snapshots only for future epochs |
| IF-09 | RevokeDependency: validator → CMP-08 | Version, defect evidence and authority | Append invalidation event and affected-object set; no deletion; preserve distinction from scientific contradiction |
| IF-10 | SubmitPolicy: CMP-09 → CMP-04 | PolicySpec, rule basis/scope/parameters/conflicts, own EvaluationPlan | Separate registered policy trial or explicit gap; no inherited whole-policy support |
| IF-11 | Authorize / Observe: CMP-10 ↔ CMP-11 | Evidence/applicability/risk authority or operational event | Bounded deployment decision or registered surveillance observation; no direct generator/evidence mutation |
| IF-12 | Propose / Approve / Rollback: CMP-12 | Current/new versions, reason, impact, probes, independent validation and rollback plan | Proposal state and explicitly authorized activation event; retain failed changes and all exposure |
| IF-13 | ReadDiagnostics: reviewer → CMP-11 | Cohort, artifact, version and metric definition | Counts, costs, gaps and evidence/operations views with denominators; read-only projection |

## Required record fields before the first real evaluation

| Record | Minimum semantic fields | Constraint |
|---|---|---|
| Artifact envelope | artifact_id, artifact_type, schema_version, definition_refs, created_at, creator_version, content_hash, source_refs, dependency_refs | Immutable payload; unknown version is an error |
| ContextSnapshot | research_time, data_snapshot_refs, knowledge_snapshot, experience_snapshot, feature_catalog_version, permissions, exposure_refs | Snapshot closure determines permitted tools and data |
| H_idea | claim_text, question_ref, generator_version, context_ref, parents, source_refs, causal_assertions, gaps | No requirement that a new idea already fits the language |
| H_exec | idea_ref, claim_kind, estimand, scope, test_universe, condition_ast, outcome, comparator, horizons, parameter_origins, feature_refs | Each semantic choice is explicit; missing meaning prevents freeze |
| FeatureDefinition | input_refs, units, output_type, algorithm/composition, parameters, availability_rule, missingness_rule, specification_version, golden_case_refs | New primitive needs independent certification |
| EvaluationPlan | claim_ref, effect_criterion, family_policy, eligibility, dependence_design, sample/precision_plan, stopping_rule, null/control_contract, uncertainty_method, status_rules, replication_plan, code_version | Values assigned before confirmation; no universal hardcoded alpha or N_min |
| FrozenManifest | h_exec_hash, compiler_version, policy_hash, dependency_closure_hash, data_access_manifest, trial_id, frozen_at, allocation_ref, definition_refs | Atomic durable commitment before outcome access |
| ExecutionResult | request_hash, data_snapshot, case_ids, raw_output_refs, data/feature/cost/fill/execution_versions, seed/environment, checks, errors | Backend does not assign evidence status |
| EvidenceRecord | trial_ref, result_hash, evaluation_version, effect/interval/statistics, primary_outcome, origin, validity, replication_ref, limitations | D071 / research-contract/1.0 supplies separate axes; do not flatten them |
| PolicySpec | rules, basis_refs, assumptions, scope_relations, parameter_origins, conflicts, update_rules, operational_constraints, own_plan | Assumptions can create research candidates, not silent facts |

These field lists are contract requirements, not complete JSON Schemas. Concrete scalar types, enumerations, timestamp/decimal encodings and migration rules must be specified together with executable validation fixtures in Phase P1. A cosmetic schema that accepts arbitrary prose in the estimand field is not sufficient.

## Selection and assessment through existing interfaces

Apply D014/D031/D045-D049/D070 through the records above. The following mapping explains existing semantic fields; it does not add a separate ledger service, prescribe physical schemas or replace document 13 version 1.0.

| Existing boundary | Information that must remain reconstructable | Failure or qualification |
|---|---|---|
| IF-02/03/08: query, idea and Journal lineage | Candidates/alternatives, selector/version, queried data/results, chosen columns/thresholds/horizons, revisions and abandonment, linked through existing artifact IDs | A winning rule without its selection ancestry cannot support a claim of independently assessed selection. Retain the idea and the gap. |
| IF-04: feature certification and compilation | Input availability, fitted transformation state/version, fitting sample and parameters through FeatureDefinition and dependency references | A valid formula with fitting state learned from prohibited outcomes still fails the applicable availability/exposure boundary. Certification is not evidence of predictive value. |
| IF-05/07: plan, freeze and evaluation | Whether the target is a frozen candidate or a selection/adaptation procedure; permitted training/fitting and assessment inputs, family/dependence/stopping rules, and the inference supported | Reject incomplete confirmation contracts. Do not describe globally selected features followed by outer refits as a wholly independent procedure evaluation. |
| IF-08/12/13: feedback use and assessment release | Released artifact/result, recipient context/version, access timing and any subsequent selection/use, including aggregate ranks or pass/fail feedback | Used assessment feedback becomes descendant exposure even without raw-data access. Preserve the original frozen result; deny unsupported freshness claims for later work. |
| IF-06/10: execution and policy selection | Eligible population, exclusions, original execution constraints, changed rules and whether saved paths still represent the requested policy | If removing a trade frees a position slot or cash for an absent opportunity, filtering the old rows is only a subset diagnostic. Resimulate affected interactions or return an explicit capability gap. |

For example, discovery selects a distance column and cutoff on permitted historical outcomes. The selected claim retains the alternatives and fitting provenance. It can be frozen for a separate admissible candidate assessment once its open contracts are resolved. If instead the experiment assesses that selection procedure, fitting and choosing the cutoff must occur inside each permitted development portion; outer outcomes cannot influence those choices. In either case, released assessment feedback used to propose the next cutoff creates an exposed descendant. This is information provenance, not a prohibition on learning.

The [worked cases](12_TRACEABILITY_MATRIX.md#selection-and-exposure-acceptance-cases) specify both invalid and permitted uses. D070 already requires final-assessment release/access rules; D075/D081/D082 now supply the scoped policy; bind all required run-specific inputs. The examples supply no reusable-holdout guarantee; adopted batch allocation is specified in document 14 section 12.

## Expression-language requirements

The language needs typed scalar/time-series/event expressions, comparisons, AND/OR/NOT, scope and outcome definitions, lag/window semantics, units and temporal availability. It must express the five accepted relationship forms and both binary and continuous outcomes. Mechanisms are represented through measurable implications rather than a special truth-granting mechanism label.

The compiler validates syntax, types, referenced definitions, temporal eligibility, supported estimators and dependency certification. It must not reject ideas merely because they are unfamiliar. Return DATA_GAP, FEATURE_GAP, LANGUAGE_GAP, SEMANTIC_AMBIGUITY or EVALUATION_GAP as appropriate; preserve the idea, required capability and retry trigger. These exact error-code spellings are proposed API choices.

Language extensions use a versioned proposal, semantics, conformance cases, migration impact and approval where material. Never translate a new claim into a convenient old rule while retaining the same idea ID as if meaning had not changed.

## Transaction, recovery and concurrency design

Persist artifact content and verify its hash before committing the manifest reference. The registry transaction commits freeze, trial identity and data-access authorization together. If external storage cannot participate atomically, use an explicit staged/committed lifecycle and recovery procedure; an uncommitted object grants no evaluation authority.

Use compare-and-set on expected artifact/version state for transitions. A retry key identifies the same execution, not another scientific trial. Backend retries may produce multiple attempts attached to one trial; contradictory successful outputs require investigation, not selection of the better result. Crash recovery must replay safely without duplicate support records.

Exposure edges are monotonic audit facts. Revocation or rollback appends a state change; it does not erase lineage. Dependency cycles in execution closure are invalid. Genealogical relations and shared-evidence links have separate semantics from executable dependency edges.

## Worked lifecycle and failure paths

A discovery agent receives a 15-minute-or-higher snapshot and notices an expectation violation. It asks a deterministic measurement question; the query and answer become discovery exposure. It submits a free H_idea. The formalizer preserves the claim and maps its outcome/conditions to certified features. If a required measurement is unavailable, the original idea is retained as NOT_TESTABLE_YET with a capability request.

A concrete pre-freeze attack may instead lead to revision or abandonment. IF-08 records that trajectory, a retained gap or an unselected candidate without requiring an EvidenceRecord. Research Experience can derive a labeled heuristic for later retrieval; the record does not become a primary negative or supported claim. A gap's retry condition depends on a relevant capability change. Any stage's technical failure is recorded through error tracking and the journal, with the affected execution quarantined.

For an executable candidate, code checks semantics, assigns the frozen evaluation family/plan and checks evidence eligibility. The selected confirmation request is committed atomically. The backend executes the authorized partition and returns raw cases plus versions. The evidence engine verifies the manifest, applies the frozen rule and records a result. Interpretation may explain the result but cannot alter it. A future knowledge snapshot includes the qualified result and its exposure ancestry.

The valid result may be negative, inconclusive or supported; each is retained with its evidence origin and limits. Primary research uses historical data, while genuinely fresh/forward confirmation has distinct eligibility and allocation rules. The [Master Architecture](06_MASTER_ARCHITECTURE.md#freeze-and-state-transitions) explains the current intent versus the preserved prospective lifecycle. D071/D075/D082 now resolve the scoped transitions, evaluation/stopping and allocation contracts. Their required run fields and conformance must be complete before affected operations; no universal early-stop rule is inferred.

If a feature is later revoked, dependent results become unusable according to the canonical invalidation rule. Recalculation creates a new execution/evidence record using certified dependencies and the appropriate retained or new scientific contract; it must not erase the old failure. If a result inspires a narrower claim, that claim is a new descendant and inherits all relevant exposure.

## Capability probes before dependency adoption

For vectorbt, specify synthetic paths with known entries, exits, fees, slippage, no trades, multiple instruments, same-bar ambiguities and evolving state. Compare outputs with independently calculated expected results. Verify whether required path dependence, cash/leverage/contract accounting and edition capabilities are supported. Do not infer support from fast array sweeps.

For Hermes, verify permitted-tool-only operation, immutable session context, profile isolation, provenance-preserving retrieval and suppression/routing of material automatic skill or memory changes. For Harness2 patterns, demonstrate that proposer/composer cannot reach final validation data or scores through files, tools or network. All probes remain unexecuted in this task.

## Build boundaries

### Binding generator feedback and assessment extension

D069-D070 adopt [document 13](13_GENERATOR_FEEDBACK_AND_EVALUATION.md) as the semantic contract for the existing modules and interfaces. Extend IF-08's Journal/Experience records with separate feedback observations, interpretations, use records and review outcomes; IF-01/02 must include the retrieval policy/version and inherited exposure. Use the existing artifact envelope and registry, not another memory database or new service.

IF-12 carries the purpose-specific assessment plan for a candidate improvement, including the reference only when the claim is comparative, tuning/assessment separation, budget and planned result interpretation. IF-13 exposes versioned diagnostic cohorts with pending cases, formalization gaps, costs and uncertainty. Discovery diagnostics distinguish unsearched analogues from unsuccessful retrieval and do not assign scientific support. The field contracts and future TEST-28/29/30 fixtures in document 13 are required for affected implementations; concrete executable schemas remain implementation work, while D071-D085 now supply the scoped numerical and semantic policies.

An absolute-economic investigation must not fail readiness merely because no competitor generator or prior profitable result exists. It still needs the applicable claim, data, execution and evaluation contracts before a real confirmatory run. This extension is implemented in the specification only.

No application code, packages, dependencies, agent runtime, database, live API connection or deployment is created by this deliverable. The next authorized implementation task should select one phase and its explicit acceptance criteria, resolve its blocking decisions, and retain the same source-backed invariants.

## Research-contract/1.0 interface bindings

The [adopted contract](14_RETAIL_RESEARCH_CONTRACT.md) supplies normative meaning. This binding assigns its fields to existing owners; these tables are not executable schemas or a claim that the runtime exists.

| Interface / records | Required extension and invariant |
|---|---|
| IF-01 / ContextSnapshot | Exact source checksums, retrieval/availability times and uncertainty, timestamp units, development/assessment roles, model exposure and transitive ancestry; same allowed snapshot for both perspectives |
| IF-02/03 / HypothesisProposal | Prompt/model versions, bounded tool capability, calls/tokens/time/cost, retained original idea, selection reason and semantic-difference report; no evaluator or peer scratch access |
| IF-04/09 / ExecutableHypothesis, CertificationRecord | Typed AST, five relationship forms, explicit estimand, units/time/missingness, exact primitive specs, independent validator/fixtures and approved-envelope classification; unknown membership is a gap |
| IF-05 / EvaluationPlan | Contract/profile versions; theta/direction/delta; frozen m and 0.05/m marginal noncoverage; dependence/overlap and exact block lengths; 19,999 draws, quantile/PRNG/version/seed; N_min justification and fixed cutoff; origin/limits; selection/reservation/release and separate resource stops |
| IF-05/06 / FrozenManifest, TrialRecord, ExecutionResult | Atomic immutable closure and allocation, canonical-json/1 bytes/hash, idempotency identity, same-trial retries; actual data/cost/fill versions and next-bar/shared-cash conventions; failed or contradictory results retained/quarantined |
| IF-07 / EvidenceRecord | Separate stage, validity, primary outcome, origin/null reason, historical qualification, replication trial, usability, timestamped applicability and action authority; raw references and enclosing interval with assumptions; no scientific verdict on invalid attempts |
| IF-08 / KnowledgeEntry, ExperienceEntry | Whole-batch release provenance, descendants' inherited exposure, original outcome retained on dependency invalidation, explicit descriptive cohort denominators and pending follow-up |
| IF-10 / PolicySpec | Direct target evidence or UNTESTED_ASSUMPTION per rule; no automatic subset transport; independent policy plan, frozen net-value hurdle/risk scenarios, actual cost basis or explicit break-even scenarios |
| IF-11 / operational view | Research-only and zero authorized capital; use-time applicability; cost/fill incidents trigger review, never rewrite scientific outcomes |
| IF-12/13 / ImprovementProposal, diagnostics | Purpose-specific gate, development/final separation, exact calibration bounds, paired acceleration plan when claimed, complete costs/failures, two-no-improvement stopping and D084 change classification |

Persistence uses one SQLite writer with checked foreign keys and FULL synchronization. Small envelopes/events/edges/freezes commit together; external blobs are staged/flushed/hash-verified before reference commitment. Recovery quarantines missing/corrupt committed blobs. Backups include a verified blob manifest and restored projections. Migration keeps old bytes/hashes and versioned mappings; no runtime records currently exist to migrate.

Implementation should proceed through typed schema/fixtures and registry, controlled adapter slice, candidate evaluator conformance/calibration, and then an authorized evidence run with actual inputs. Future schemas must make every field above machine-checkable; free text may explain a gap but cannot substitute for frozen executable meaning.

## Agent inquiry integration

D086 / [agent-inquiry/1.0](15_AGENT_INQUIRY_DISCIPLINE.md) elaborates REQ-014 through existing interfaces. IF-02's purpose identifies the investigation object and uncertainty, with possible implications of targeted findings or an honest open-exploration purpose. IF-03's semantic-difference report preserves the original question through formalization. IF-08 retains concise purpose, sourced finding, warranted conclusion, remaining uncertainty and next action with reason at completed investigations, handoffs and continuation decisions. Reference existing context/exposure and budget records; reuse an adequate existing artifact rather than duplicate it.

The challenger can report no substantiated objection; discovery need not invent a hypothesis to justify exploration. Existing access, allocation, freeze and evidence controls remain authoritative. These are semantic requirements for future implementations, not new fixed JSON field names, lifecycle states or a per-call approval gate. The [TEST-14 examples](15_AGENT_INQUIRY_DISCIPLINE.md#acceptance-examples-for-test-14) remain unexecuted behavioral specifications. Material prompt configurations remain versioned under D026.
