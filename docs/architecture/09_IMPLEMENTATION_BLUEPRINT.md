# Implementation Blueprint

Status: documentation proposal, not implemented code. Source-backed behavior is mandatory as recorded in the decision register; implementation choices below are recommendations. Resolve the blocking open decisions before executing the affected milestone. Do not interpret this blueprint as user authorization for live trading or material framework self-modification.

## Minimal coherent implementation shape

Use a modular application with explicit ownership of context, discovery, formalization, registry/freeze, backend execution and evidence. Keep immutable artifact bodies in content-addressed storage and an indexed transaction-capable registry for identities, events and dependency edges. A local database plus files is a candidate starting point, not an accepted product choice. A separate graph database, message broker, vector store and service mesh are not initially justified.

Use one orchestrator that routes artifacts and enforces permissions, not one that selects scientific conclusions. Roles can be sequential in an engineering smoke test. Target independent discovery perspectives must later be demonstrated with separate state and identical allowed context; a one-agent smoke test is not proof of that requirement.

## Interface contracts

Names below are proposed contract identifiers, not promises about third-party APIs.

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
| EvidenceRecord | trial_ref, result_hash, evaluation_version, effect/interval/statistics, primary_outcome, origin, validity, replication_ref, limitations | Status representation depends on OPEN-01; do not flatten distinct axes |
| PolicySpec | rules, basis_refs, assumptions, scope_relations, parameter_origins, conflicts, update_rules, operational_constraints, own_plan | Assumptions can create research candidates, not silent facts |

These field lists are contract requirements, not complete JSON Schemas. Concrete scalar types, enumerations, timestamp/decimal encodings and migration rules must be specified together with executable validation fixtures in Phase P1. A cosmetic schema that accepts arbitrary prose in the estimand field is not sufficient.

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

The valid result may be negative, inconclusive or supported; each is retained with its evidence origin and limits. Primary research uses historical data, while genuinely fresh/forward confirmation has distinct eligibility and allocation rules. The [Master Architecture](06_MASTER_ARCHITECTURE.md#freeze-and-state-transitions) explains the current intent versus the preserved prospective lifecycle. OPEN-01/05/12 must resolve executable transitions, evaluation/stopping policy and allocation before affected operations; these examples introduce no new status enum or universal early-stop rule.

If a feature is later revoked, dependent results become unusable according to the canonical invalidation rule. Recalculation creates a new execution/evidence record using certified dependencies and the appropriate retained or new scientific contract; it must not erase the old failure. If a result inspires a narrower claim, that claim is a new descendant and inherits all relevant exposure.

## Capability probes before dependency adoption

For vectorbt, specify synthetic paths with known entries, exits, fees, slippage, no trades, multiple instruments, same-bar ambiguities and evolving state. Compare outputs with independently calculated expected results. Verify whether required path dependence, cash/leverage/contract accounting and edition capabilities are supported. Do not infer support from fast array sweeps.

For Hermes, verify permitted-tool-only operation, immutable session context, profile isolation, provenance-preserving retrieval and suppression/routing of material automatic skill or memory changes. For Harness2 patterns, demonstrate that proposer/composer cannot reach final validation data or scores through files, tools or network. All probes remain unexecuted in this task.

## Build boundaries

### Binding generator feedback and assessment extension

D069-D070 adopt [document 13](13_GENERATOR_FEEDBACK_AND_EVALUATION.md) as the semantic contract for the existing modules and interfaces. Extend IF-08's Journal/Experience records with separate feedback observations, interpretations, use records and review outcomes; IF-01/02 must include the retrieval policy/version and inherited exposure. Use the existing artifact envelope and registry, not another memory database or new service.

IF-12 carries the purpose-specific assessment plan for a candidate improvement, including the reference only when the claim is comparative, tuning/assessment separation, budget and planned result interpretation. IF-13 exposes versioned diagnostic cohorts with pending cases, formalization gaps, costs and uncertainty. Discovery diagnostics distinguish unsearched analogues from unsuccessful retrieval and do not assign scientific support. The field contracts and future TEST-28/29/30 fixtures in document 13 are required for affected implementations; concrete schemas and numerical policies remain subject to the relevant open decisions.

An absolute-economic investigation must not fail readiness merely because no competitor generator or prior profitable result exists. It still needs the applicable claim, data, execution and evaluation contracts before a real confirmatory run. This extension is implemented in the specification only.

No application code, packages, dependencies, agent runtime, database, live API connection or deployment is created by this deliverable. The next authorized implementation task should select one phase and its explicit acceptance criteria, resolve its blocking decisions, and retain the same source-backed invariants.
