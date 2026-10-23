# Retail research contract: closure proposal

Version: **0.1, PROPOSED CHANGE — USER APPROVAL REQUIRED**. Date: October 23, 2026.

Owner: user for scientific adoption; deterministic code for execution of an adopted contract. Authority: D008/D026. Companion: [system reconstruction and literature review](OPEN_DECISION_RESEARCH_2026-10-23.md). The canonical register still governs; nothing in this proposal is an accepted decision or implemented runtime.

## Approval scope and intended outcome

Approve a historical-first, resource-bounded research contract that makes a useful decision from available evidence without mandatory forward waiting. Keep free invention, independent evaluation, inherited exposure, separate policy testing and the operational firewall. No goal change is proposed. Clean forward confirmation remains a distinct optional evidence track; it is not a prerequisite for a historical research decision.

This proposal closes **design choices** for a bounded v1 and names the inputs required at run time. It cannot close missing-source facts, certify unacquired data, supply private fee schedules or demonstrate statistical calibration. A run missing one of those inputs returns a typed readiness failure. This is not permission to silently manufacture an input.

The numeric choices below are proposed engineering/research budgets and scoped statistical policies, not values dictated by academic literature. Changing a scientific policy after seeing assessment outcomes requires a new version and retained exposure.

## 1. OPEN-01: versioned lifecycle and evidence axes

**Decision:** introduce `research-contract/1.0` as a separately versioned extension; preserve reconstruction-1 and the exact M0072 quotation. Use this execution path:

```text
IDEA_CREATED -> FORMALIZING -> EXECUTABLE -> EVALUATION_POLICY_ASSIGNED
-> FROZEN -> EXECUTING_HISTORY | COLLECTING_PROSPECTIVE_CASES
-> READY_FOR_EVALUATION -> EVALUATED
```

The branch is fixed in the manifest. History is ready when its frozen sample has been processed and the declared evaluation trigger is satisfied; no wall-clock collection delay is added. Gaps, queue states, abandonment and technical errors are separate retained events. A fixed-sample run that does not meet its information requirement ends with a retained inconclusive/readiness reason, not indefinite collection or a fabricated negative.

Store distinct fields:

| Axis | v1 meaning |
|---|---|
| Execution stage | Where the request is in the path above; an attempt can fail without scientific evaluation |
| Technical validity | `UNCHECKED`, `VALID`, `INVALID`; invalid attempts cannot issue market outcomes |
| Primary outcome | No outcome until evaluation; then existing `TESTED_NEGATIVE`, `TESTED_INCONCLUSIVE`, `SUPPORTED_INITIAL` |
| Evidence origin | Existing TRAINING_EXPOSED_HISTORY, MODEL_UNSEEN_HISTORY or TRUE_FORWARD; unresolved origin is explicitly null with an uncertainty reason |
| Historical qualification | Direct/ancestral exposure, unknown training exposure, procedural holdout and method assumptions are separately recorded |
| Replication | Not planned, pending, supported, failed or inconclusive, with its own trial and plan; no automatic upgrade from re-execution |
| Evidence usability | Usable under recorded limits, quarantined or invalidated by a named dependency |
| Current applicability | `NOT_ASSESSED`, `IN_SCOPE_AS_OF`, `REVIEW_REQUIRED`, `OUT_OF_SCOPE`, with assessment time and rule |
| Action authority | Research-only unless a separately approved deployment contract exists |

Unknown training exposure is not positive proof of training exposure, nor certification of model-unseen history. Historical results with unknown exposure remain visible as qualified historical findings. An interval or nominal p-value does not supply a calibrated full-process error guarantee in that case.

Migration: legacy records are retained verbatim and projected only where their fields establish the meaning. Unresolvable fields stay unknown with a migration issue. Do not fabricate origin, applicability or independent replication from a legacy support label. Store the old record hash and mapping version. Reversal selects the old projection; it never deletes new events or exposure.

**Alternative not selected:** replace the legacy enum in place or force all historical trials through simulated future collection. **Affected:** D008/D013/D020/D053/D067, DEF-014–024/027, REQ-005/006/007/012/017. **Acceptance:** historical readiness without elapsed calendar time; invalid run with no scientific verdict; legacy supported record with unknown origin remains unknown; retry cannot add replication.

## 2. OPEN-02: subset membership is not evidence transport

**Decision:** IN_SCOPE/SCOPE_SUBSET/EXTRAPOLATION/INCOMPATIBLE describe a scope relation only. Mark a rule EVIDENCE_BACKED for its particular use only when a referenced EvidenceRecord directly evaluates that target or a separately approved transport contract justifies the target estimand, overlap, effect modifiers and uncertainty. V1 provides no automatic transport estimator. Otherwise record UNTESTED_ASSUMPTION and a candidate claim, without blocking policy research itself.

A nonsignificant heterogeneity test does not prove homogeneous effects. A narrower scope selected after results is a descendant, not a free relabeling. A policy's independent evaluation can establish its own outcome while its individual premises remain qualified.

Hand-checkable counterexample: conditional versus complement success is 0.8 versus 0.5 in subgroup A and 0.2 versus 0.3 in subgroup B. With equally sized subgroups and equal condition prevalence, the aggregate conditional rate is 0.5 and the aggregate scope rate 0.45, so delta is +0.05. In B the scope rate is 0.25 and delta is -0.05. Positive aggregate delta cannot certify B. This is arithmetic, not market evidence.

**Rationale:** LIT-08; direct subgroup arithmetic does not require adopting a causal graph framework. **Alternative not selected:** automatic inheritance or a compulsory new transport service. **Affected:** D010/D021/D066, DEF-028/029, REQ-009. **Acceptance:** the counterexample rejects inherited subgroup support while retaining the assumption and permitting a separate policy trial.

## 3. OPEN-03: descriptive cohorts, no invented truth priors

**Decision:** report generated, executable, frozen, valid-evaluated, initially supported, replication-selected, replication-completed, replicated, failed and pending counts by version/cohort and observation cutoff. Keep explicit denominators and time at risk. Undefined rates remain null, not zero. A selected replication yield is labeled as selected.

V1 does not calculate `prior_effect_probability`, individual posterior truth or false-discovery probability from replicated/tested counts. Family identity can guide descriptive retrieval and resource review; it does not alter scientific thresholds through an invented prior. Outcome base rates can still enter power calculations under DEF-012.

Example: 8 replications among 200 tested claims gives a 4% observed replicated/tested fraction. It is compatible with many combinations of effect prevalence, test power, replication selection and pending follow-up. None identifies a 4% probability that the next claim is true. A future estimator needs its own generative assumptions, selection/censoring model and calibration.

**Rationale:** LIT-09 plus the source ambiguity in M0158. **Alternative not selected:** LLM priors or an unvalidated empirical-Bayes layer. **Affected:** D024/D028, DEF-011/012/026, REQ-005/022/029. **Acceptance:** the 8/200 example produces a descriptive rate and no truth prior; immature cohorts retain pending cases.

## 4. OPEN-04: typed expressions and explicit estimands

**Decision:** use a versioned JSON AST, not generated evaluator code. The expression language is extensible; the currently certified operator set is an execution capability boundary, not a hypothesis catalog. Preserve the original H_idea and a semantic-difference report. Unrepresented meaning produces LANGUAGE_GAP or SEMANTIC_AMBIGUITY.

Core types: Boolean, integer, finite real, decimal quantity with unit, UTC instant, duration, instrument key, event set and aligned series of a scalar type. A missing value is distinct from false, zero and nonfinite arithmetic. AND/OR/NOT use declared three-valued logic; final eligibility admits true only and records false/unknown exclusions separately. Division by zero returns a typed invalid/missing result under the frozen operator rule, never infinity used as a signal.

Core nodes: literal; versioned feature reference; arithmetic with unit checking; comparison; AND/OR/NOT; nonnegative lag; trailing window; event condition; outcome at a declared horizon; versioned estimator invocation. Negative lags, centered windows as decision inputs and full-path outcomes as entry features are inadmissible. Interactions and changes require explicit alignment and comparator definitions. Functions cannot read files, network, secrets or evaluator outputs.

Every estimator node binds its target, units, weighting, eligible population, horizon, direction or equivalence region, nuisance fit, missingness/censoring and dependency design. No free-text estimand can pass the scientific freeze boundary.

| Relationship form | Required executable meaning; no automatic causal interpretation |
|---|---|
| Difference | Mean/rate contrast between explicit populations, including the canonical condition-versus-whole-scope contrast |
| Association | Named statistic, e.g. Pearson correlation with specified transformations and missing pairs; nonlinear dependence needs its own certified statistic |
| Change | Explicit before/after windows, paired units and change statistic; an event alone is not a causal identification strategy |
| Boundary | A declared contrast conditional on a predeclared region; subgroup coverage and selection recorded |
| Interaction | A defined difference of contrasts or specified interaction coefficient; coding, scaling and fitted terms fixed |

For the canonical contrast, compute `mean(Y where C and S) - mean(Y where S)`. Both terms must be recomputed on the same resampled scope rows. Never substitute condition-versus-complement or independent-sample uncertainty. Zero eligible or zero conditioned cases produce an explicit information failure.

Adaptive policies use a deterministic state-transition expression with declared observations, allowed actions, position/cash state and frozen parameter-update rule. A fitted update has a retraining schedule, permitted fitting window and seed/version; newly matured information alone may enter it. If the backend cannot represent it, preserve an execution gap rather than approximate silently.

**Alternative not selected:** flat template fields that narrow invention or arbitrary per-hypothesis Python verdicts. **Affected:** D002–004/D008/D017/D027/D031, DEF-003–008/013/023/031/032, REQ-002/003/005/011/024/026. **Acceptance:** independently calculated binary and continuous fixtures for all five forms, Boolean unknown cases, unit mismatches, future access, interactions without a main effect, and a path-dependent policy gap.

## 5. OPEN-05: test policy, useful negatives and information limits

### 5.1 Default work-unit decision

**Decision:** use a fixed historical assessment for the initial profile. Discovery can stop cheaply for a concrete contradiction, unaffordable requirement or missing representation, but such abandonment is not a frozen empirical negative. After freeze, evaluate once at the declared fixed trigger. Do not repeatedly inspect nominal intervals for early success.

The final report always separates two decisions: the scientific outcome allowed by the plan, and the resource action `STOP`, `RETAIN_GAP`, `CONTINUE_WITHIN_BUDGET` or `QUEUE_FURTHER_EVIDENCE`. An inconclusive scientific result can therefore lead immediately to STOP without claiming falsification. No work unit automatically waits for new market observations.

### 5.2 Concrete initial interval profile

Propose `historical-batch-v1`: at most eight primary claims, one predeclared primary estimand per claim, a family error budget of 0.05 and one fixed release. Use simultaneous two-sided intervals with marginal noncoverage `0.05 / m`, where m is the frozen number of primary claims. The union-bound policy applies to both support and negative classifications; it does not assume independence between claims. It depends on valid marginal coverage. Asymptotic bootstrap intervals support only an asymptotic/conditional error claim, not exact finite-sample control. Unknown model exposure further limits process-level interpretation.

For a directional claim define `theta = direction * effect` and a pre-frozen minimum relevant effect `delta > 0`:

- lower bound greater than delta: SUPPORTED_INITIAL under the recorded origin and assumptions;
- upper bound less than delta: TESTED_NEGATIVE **for the claimed practically relevant effect**, not proof of exactly zero;
- otherwise, including equality at the boundary: TESTED_INCONCLUSIVE.

For an explicitly nondirectional claim, support requires the interval wholly outside `[-delta, delta]`; a negative requires it wholly inside that region. Other overlap is inconclusive. Claim-specific superiority, noninferiority or equivalence contracts must say which set of effects they assert. Do not reinterpret one kind after outcomes.

Meaningful effects are assigned by an approved evaluation profile, not chosen by the generator to make its test easier. Proposed demonstration profiles are: five percentage points for a binary probability contrast, and ten basis points for a 24-hour return contrast. These are **limited pilot targets**, not universal economic truths. Different claims keep their meanings and request another effect profile instead of being coerced. A policy's primary economic target is net value above its separately frozen opportunity-cost hurdle; rate improvements alone do not establish that value.

### 5.3 Dependence and uncertainty dispatch

Use the simplest certified estimator that matches the claim. Initial market candidate: joint stationary-block bootstrap of aligned scope rows for a mean/rate contrast, with all instruments at each time kept together. Recompute condition and scope means jointly. Preserve event outcomes and their overlap; fitting and signal selection must already be confined to development. No independent-trade bootstrap default.

Development selects the dependence profile before assessment. For the pilot, predeclare a base block length at least the maximum overlapping outcome horizon, supplemented by development-only dependence diagnostics. Freeze the exact integer length and rationale; missing justification blocks inferential classification. Run lengths of half, base and double that length, with the half length bounded below by the outcome-overlap horizon. Use the enclosing interval across these prespecified sensitivity cases; never select the narrowest. Budget 19,999 resamples per case. Record quantile interpolation, PRNG/version and numerical tolerance. Monte Carlo instability near a decision boundary produces inconclusive, not selective reseeding.

The initial candidate uses basic bootstrap intervals from joint contrast replicates: `[2*estimate - q(1-a/2), 2*estimate - q(a/2)]`, with marginal noncoverage a. Quantiles use linear interpolation at zero-based rank `(B-1)*p`; fractional block lengths round upward and duplicate sensitivity lengths are evaluated once. Record the implementation's exact PRNG algorithm, version and seed before execution. Decline inferential classification when any required interval cannot be constructed, including resamples with undefined conditional means; do not discard those draws and silently renormalize. Retain descriptive results and an information gap. A more efficient rare-event estimator requires separate validation. This specified candidate still needs passing conformance and calibration before runtime adoption; the name "bootstrap" supplies neither.

Stationarity/weak-dependence assumptions and rare-event denominator adequacy must be documented. A structural break, inadequate effective information or unsupported estimator yields EVALUATION_GAP or a qualified descriptive result. Resampling is not a proof that these assumptions hold. Do not globally fit regime definitions using assessment outcomes and then claim honest within-regime inference.

Association, change, nonlinear and adaptive-policy estimators receive their own conformance and calibration profiles. The AST can represent a claim before a suitable evaluator exists; that is a retained evaluation gap, not permission to apply the mean-contrast method universally.

### 5.4 N_min, attainable precision and stopping

The evaluator determines information sufficiency using development-only nuisance estimates, dependence-aware simulation and the assigned error/effect profile. Freeze the smallest eligible sample target meeting the profile's planned 80% power at a specified alternative **beyond** the decision boundary (initial sensitivity alternative: `theta = 2 * delta`) and report performance at zero, delta and 2*delta. Power at exactly the boundary must not be advertised as 80% for a test requiring a bound to exceed it.

A finite historical dataset remains a permissible sensitivity/precision study when that target is unattainable. Report what effects the available information could distinguish, the declared fixed cutoff and an inconclusive outcome when required precision is missing. Do not change delta to match the observed result. Do not count bootstrap repetitions, correlated bars or repeated LLM calls as additional independent observations.

A sequential profile remains possible only after a particular confidence sequence/e-process, filtration, outcome maturation, dependence/tail assumptions, multiplicity allocation and terminal inconclusive rule are certified. LIT-07 does not justify a generic always-valid test for arbitrary trading returns. It is unnecessary to build this profile before the fixed historical work unit works.

**Rationale:** LIT-03–07. **Alternatives not selected:** universal N=100, fixed calendar waits, zero-null significance as an economic gate, obligatory DSR/PBO or generic sequential peeking. **Affected:** D006/D024/D027/D031/D035/D062, DEF-007/008/012/018/021/022, REQ-005/019/020/024/029. **Acceptance:** interval boundary fixtures; overlapping baseline fixture; dependent null calibration; insufficient information; no early success; no target switching.

## 6. OPEN-06: data and execution authority

**Decision:** propose a first research profile using BTCUSDT and ETHUSDT spot 15-minute data, UTC, January 1, 2020 through December 31, 2025, from the public Binance archive or verified local copies of those exact artifacts. This is a bounded liquid-market engineering/evidence profile, not an assertion of uncrowded alpha, an investment recommendation or a permanent restriction to crypto/OHLCV. Other domains remain first-class extension requests under D018.

Partition by calendar before discovery: 2020–2023 development, 2024 primary assessment, 2025 reserved corroboration. Remove development/assessment boundary cases whose label-information intervals cross the boundary. Development-derived feature state may warm up later periods only with information available at the corresponding decision. The partitions are not independent by name and do not establish model-unseen history. Existing exposure to a partition changes its admissible role.

Acquisition acceptance requires exact files and SHA-256, provider checksum verification, retrieved-at timestamp, timestamp-unit declaration, instrument metadata, duplicate/gap checks, prices/volumes invariants, revisions, rights/use restrictions and available-at evidence. Binance's README explicitly allows later archive corrections. A present download is not an authenticated historical vintage. Store uncertain release/latency as uncertain and qualify results accordingly; a conservative delay assumption is a simulation scenario, not verified PIT truth.

For the initial simulator: spot long/flat, no leverage or short borrow; signals after bar close; execution at the next eligible bar open with adverse cost adjustment; one position per instrument and explicit shared-cash ordering. Intrabar stop/target ordering unsupported by the input must return a capability gap or use a separately frozen conservative scenario, never the favorable ordering. Trade-path changes require resimulation.

Record commissions, spread, slippage, market impact and any product-specific charges separately, with units, time validity and basis, avoiding double counting. An unknown cost is not zero. Before real economic support, obtain the applicable venue/account fee and plausible execution-cost basis. Until then calculate a break-even cost curve and explicitly labeled scenarios; these can support a decision to stop research but cannot certify realistic net profitability. Personal after-tax return is outside this research profile; make no after-tax claim without the applicable inputs.

**Alternative not selected:** buy data or connect an account now, assume 15-minute OHLCV reconstructs exact fills, or infer a market-wide claim from two surviving instruments. **Affected:** D012/D013/D018/D033/D042/D069, DEF-013/024/031/033, REQ-011/012/015/018/029. **Acceptance:** revisions and mixed timestamp units fail loudly; next-bar timing and shared cash have independent fixtures; missing fee/rights/PIT information remains explicit. No dataset was acquired by this proposal.

## 7. OPEN-07: runtime choice and isolation

**Decision:** define the owned adapter interface now; do not require Hermes for v1. Use the already available provider/runtime only through bounded calls and artifacts, recording its exact model identifier and generation parameters. If only a mutable alias is exposed, record that limitation and reject claims requiring an immutable model snapshot. Never claim that changing model names proves independence.

The discovery runtime receives only a context capability and allowed tool handlers. It has no arbitrary shell, filesystem, network or evaluator-storage capability. The host broker owns those operations. Running all roles as ordinary functions while exposing unrestricted files to the model is not isolation. The final evaluator and its data are outside the provider-visible workspace/tool surface.

Hermes remains a future adapter candidate under D041. Its documented automatic learning requires disabled or explicitly routed mutation paths and passing access-negative probes. vectorbt remains the primary backend candidate under D042; adopt a pinned edition/version only after synthetic accounting/path conformance and license review for intended use. Until adoption, a minimal independent reference calculator may validate fixtures but cannot claim vectorbt integration or general backtest capability.

**Alternative not selected:** rebuild a provider platform or import an agent framework's scientific status logic. **Affected:** D022/D034/D040–042/D063, REQ-004/012/018/021. **Acceptance:** denied holdout requests through files, tools and returned metadata; no automatic memory mutation within an epoch; exact adapter request/result provenance. Dependency versions remain acquisition-time inputs, not invented compatibility claims.

## 8. OPEN-08: persistence, serialization and recovery

**Decision:** start with one local SQLite registry, one writer and immutable artifact payloads. Store small JSON envelopes/bodies, events, dependency edges, trial identities and freeze manifests in the same database transaction. Use foreign keys, uniqueness constraints, append-only application APIs and `synchronous=FULL`; verify actual settings on connection. Large data/result blobs are external, content-addressed files staged, flushed and hash-verified before registry reference commitment. An uncommitted staged blob grants no authority. Recovery checks committed references and quarantines missing/corrupt blobs; harmless orphan staging files can be reclaimed under a separate retention policy.

For v1 hash the exact retained canonical envelope bytes using SHA-256. Define `canonical-json/1`: UTF-8 without BOM, ASCII schema keys sorted lexically, no duplicate keys, no binary floating-point JSON values, no NaN/Infinity, integer counts, explicit decimal strings with schema-specific canonical normalization, UTC ISO timestamps ending in Z, and ordered arrays. No Unicode normalization of source text. Original source bytes receive separate hashes. This restricted format is not claimed to implement all of RFC 8785; use published test vectors before ever advertising JCS compliance.

Freeze, trial and allocation reservation commit atomically with a caller-supplied idempotency key. Same key/same content returns the committed identity; same key/different content is a conflict. Multiple execution attempts refer to one trial. Contradictory successful result hashes cause quarantine, not selection. Log abandoned/failed attempts.

Back up with SQLite's supported backup mechanism plus a verified blob manifest; restore into a new location and validate hashes, references and replayed projections before use. Never assume copying only a live database file is sufficient. Schema migrations are versioned, tested on a copy and preserve source records. Application append-only behavior is not protection against an administrator rewriting the database.

**Alternative not selected:** independent mutable JSON registries, a graph database or a distributed transaction system for a retail single-user workload. **Affected:** D006/D007/D008/D009/D030/D063, REQ-005/006/007/008/012/023. **Acceptance:** crash before/after commit, duplicate delivery, concurrent freeze conflict, invalid decimal/duplicate JSON keys, corrupted blob, backup/restore and projection replay.

## 9. OPEN-09: perspectives, models and compute budget

**Decision:** initial research epoch has two isolated discovery perspectives on the same snapshot, run sequentially to limit resource use; they exchange completed artifacts only after submission. One may use semantic context and another an alternative reasoning prompt, but modes are not mandatory scientific filters. Same provider/model is allowed; differing labels are not evidence of diverse thought. Exact model and prompt versions are run-profile fields.

Proposed pilot ceiling per epoch: 12 total model calls across discovery, challenge and formalization; 80,000 total input-plus-output tokens; 30 minutes wall time; 8 frozen primary claims. These are caps, not quotas or required hypothesis counts. Preserve every submitted idea, including those never selected. No purchase or external paid run is authorized just by these proposed limits; a paid execution also requires an explicit currency cap and available credentials.

Set a separate 30-minute computation cap for a frozen historical batch and a 60-minute cap for a narrow calibration assessment on the declared machine. These are resource stops, not promised runtimes or inferential stopping rules. An unfinished batch returns incomplete execution without selectively publishing favorable claims; unfinished calibration cannot certify the estimator. Additional computation requires a recorded continuation decision and cannot replace missing independent observations.

Use at most two repair iterations for the same diagnosed problem without meaningful improvement, per D030. Stop or retain the gap when a cap is reached. Unknown monetary cost remains unknown and blocks a monetary-efficiency claim. Expansion requires observed coverage/latency/cost benefit, not a novelty score or the availability of more agents.

**Alternative not selected:** a fixed many-agent platform or indefinite reasoning. **Affected:** D005/D016/D028/D030/D039/D061/D070, REQ-004/014/022/023/030. **Acceptance:** same snapshot, inaccessible peer scratch, complete call costs, retained overflow ideas and budget exhaustion without scientific rejection.

## 10. OPEN-10: explicit research-only authority

**Decision:** v1 has no order-submission capability, authorized capital is zero, and every output is a research or simulation artifact. This settles the current operating mode. A later live-capital capability requires a separate reviewed deployment contract specifying owner, loss/exposure limits, venue/account, costs, withdrawal and rollback. Those personal choices cannot be inferred from a p-value or research result.

**Alternative not selected:** automatic paper-to-live promotion or evidence-to-capital ladder. **Affected:** D020/D057/D064, REQ-017/025. **Acceptance:** no scientific result can emit or authorize a trade; simulated losses cannot mutate evidence. Closing the research-mode decision does not close future live-risk choices.

## 11. OPEN-11: finite success and continuation criteria

**Decision:** report separate gates. Passing an earlier gate permits only its named inference, never a profitable-framework claim.

| Gate | Proposed observable criterion and interpretation |
|---|---|
| Documentation/contract readiness | Complete versioned fields, linked authority and all applicable executable fixtures once built; missing semantics stop affected operations only |
| Technical slice | One genuine free LLM idea reaches a faithful report without manual scientific repair; valid negative/inconclusive is acceptable; deliberate leakage, manifest mutation and evaluator-access tests must all be denied |
| Formalization | Report all registered ideas, faithful mappings, typed gaps and human effort; zero silently altered meanings. No arbitrary minimum executable percentage forces unusual ideas into convenient templates |
| Narrow evaluator calibration | Frozen estimator assessed on 256 fresh simulated datasets per declared null world; one-sided exact 95% upper bound on false-support probability must be at most 0.10 for a nominal 0.05 profile. Report the observed rate and bound; this is an explicit tolerance, not proof of exact 5% control. Planted alternative at 2*delta: one-sided 95% lower bound on detection at least 0.70, with 0.80 design target. Boundary, heavy-tail, overlap and common-shock cases included where applicable |
| Full-process calibration | A separate plan reruns the actual discovery, selection and policy opportunities. Small end-to-end smoke runs can expose defects but cannot satisfy REQ-020. Choose repetitions from attainable uncertainty and cost before results; do not run hundreds of expensive LLM calls merely to label the fixed evaluator calibrated |
| Economic usefulness | At least one separately assessed policy meets its frozen net-value hurdle and downside/cost constraints on admissible evidence. Missing real costs or weak information leaves this unverified; qualified history cannot become clean forward evidence |
| Acceleration | For a later comparative claim, freeze a named prior workflow, matched task/information scope and quality gate. Proposed substantial-improvement target: at least 50% lower median discovery-to-freeze time and 50% lower median freeze-to-report processing time, with reported paired uncertainty and all failures/pending tasks. No claim until measured; no rejected comparator generator |
| Research investment | End the pilot at its resource cap and publish STOP/CONTINUE/RETAIN_GAP with reasons. Two iterations without meaningful improvement stop further autonomous expansion. Lack of a profitable policy in a small pilot does not falsify all free LLM discovery |

Use distinct development and final calibration draws; reserve the final seed list and ground truth from the generator. Tuning after a failed final assessment creates a new version and needs new final assessment. Joint instruments/time blocks are one calibration world, not independent replicates. The two calibration numeric thresholds are scoped engineering choices requiring approval and must be reported exactly; they are not literature-derived standards.

Calibration must include the actual decision boundary, not only zero effects: test false support when theta equals delta, false negative when theta equals delta, and joint interval miscoverage across a batch containing mixed true effects. Apply the same 0.10 upper-bound tolerance to an erroneous decisive classification in these boundary worlds. Zero-effect simulations alone would make a minimum-effect test look deceptively safe. Report the number of worlds and all failures; passing the declared worlds does not establish validity for every market regime.

Economic policy targets bind notional/cash convention, return denominator, turnover, gross and net PnL, a practical hurdle and risk scenarios. A positive sample mean alone is insufficient. Do not demand a complete causal generator-improvement experiment before the first informative historical study; D059 remains staged.

**Rationale:** LIT-01/06/10/11. **Affected:** D025/D030/D038/D059/D068–070, REQ-020/022/023/027/029. **Acceptance:** separate gate reports; narrow calibration cannot claim P4; failed/pending cohorts retained; no success reward for producing easy rejections.

## 12. OPEN-12: confirmation allocation and feedback release

**Decision:** one predeclared batch of at most eight primary estimands per initial campaign. Selection uses development information only. First admit semantically complete, testable candidates with available information; then order by explicit decision relevance, lower estimated test cost and nonredundant coverage, with stable registration order as the final tie-break. Preserve criterion values and reasons; do not create a weighted LLM truth score. Untested critical policy assumptions can receive a documented priority flag. Unselected ideas remain queued.

The statistical family is the full batch used for a common decision, including declared primary subgroup/interaction/policy claims. Descriptive topic families do not split the error budget. All frozen claims may use shared assessment observations under the joint interval/dependence policy. An exact duplicate links to its existing trial; a changed horizon, filter or policy is a new claim. No refund of error budget after viewing a result.

No assessment rank, pass/fail, plot or partial effect is released until the batch completes or terminates under its frozen technical-failure policy. A technical failure is reported without opportunistic partial scientific rankings. Outcomes released after the batch enter the Journal and may inform later epochs, with exposure inherited. A descendant cannot reuse those outcomes as independent confirmation. The same historical data may remain useful for explicit exploration and qualified analyses; the original valid result is not erased.

The pilot permits one primary assessment batch and one pre-reserved corroboration batch on disjoint outcome records, with dependence and exposure reviewed. Repeated examination of the reserved period during development disqualifies its reserved role. Each batch's error claim is stated separately; no combined campaign-wide 5% claim is made without a further budget split. If both must support a replication claim, that conjunction and selection rule are frozen before the first release.

Replicated designation requires a separately frozen same-claim test, admissible previously unused evidence and a documented independence/dependence assessment. Different dates or instruments alone are insufficient. Historically exposed corroboration remains historically qualified and cannot acquire TRUE_FORWARD origin.

**Rationale:** LIT-02/03/10. **Alternative not selected:** one dataset per idea, unlimited holdout reuse, guessed effective trial counts or semantic family labels as multiplicity relief. **Affected:** D014/D023/D031/D038/D046/D049/D070, REQ-005/013/019/020/024/028/029. **Acceptance:** late candidate denied admission; shared predeclared batch allowed; pass/fail-informed descendant inherits exposure; unused ideas remain retrievable.

## 13. OPEN-13: dependency effects and applicability

**Decision:** use the existing minimal typed graph with this consequence table. No general scientific-contradiction ontology is introduced.

| Event or edge | Consequence |
|---|---|
| Revoked data/feature/compiler/evaluator version actually used by a result | Append INVALIDATED_BY_DEPENDENCY to evidence usability; retain original outcome and source; recomputation needs valid versions and retained exposure |
| Scientific prerequisite explicitly required by a policy becomes unsupported or inapplicable | REVIEW_REQUIRED for that policy; never assert the dependent empirical claim is automatically false |
| Shared evidence or genealogy | Propagate exposure/provenance; do not automatically invalidate |
| Proposed contradiction | Retained research question/conflict, not a deterministic truth transition |
| Actual current inputs outside a frozen applicability scope | OUT_OF_SCOPE as of that observation; historical result unchanged |
| Cost/fill incident or operating loss | Policy Experience/operations review; no direct research-truth update |

Default applicability is NOT_ASSESSED. An IN_SCOPE_AS_OF record binds a specific assessment time, scope predicate, required certified inputs and version. It is not a timeless CURRENT label. Reassess at each intended use; if required data or the rule is absent, return NOT_ASSESSED/REVIEW_REQUIRED. No universal decay half-life or alarm threshold is invented. Any quantitative monitoring alarm is a versioned, predeclared method with its own false-alarm assumptions.

**Affected:** D009/D020/D037, DEF-015/027, REQ-008/017/025. **Acceptance:** hard invalidation propagates; genealogy does not; changed costs trigger review without erasing scientific evidence.

## 14. OPEN-14: automatic certification within an approved envelope

**Decision:** distinguish certification of an implementation from approval of scientific meaning.

1. Composition of already certified primitives under unchanged units, time, missingness and estimator semantics may be certified automatically by deterministic conformance checks.
2. A new implementation of an already approved mathematical/temporal specification may be certified automatically only by a validator that cannot alter the independent expected results. Require hand-checkable golden cases, causality, units/missingness, metamorphic tests, dependency closure and sandbox/resource checks. No self-issued certificate from the implementing LLM.
3. A genuinely new primitive meaning, language operator, estimand, evidence rule, exposure policy, applicability rule or material generator/retrieval policy requires a reviewable D008/D026 proposal and explicit approval before activation. An implementation labeled routine cannot change that classification.
4. If the classifier cannot establish membership in the approved envelope, retain a certification gap and request review. Do not silently deny the idea or approve the semantics.

The initial envelope is the approved contract and individually versioned primitive specifications, not an open-ended permission for generated Python. Routine certification does not require the user to review every feature; material scientific changes do. Certification proves only the exercised implementation contract, not predictive usefulness or complete absence of bugs.

**Alternative not selected:** manual approval for every routine computation (REJ-004) or automatic activation of new scientific standards (REJ-030). **Affected:** D004/D008/D026/D034/D052, REQ-003/006/007/021. **Acceptance:** existing-semantic implementation can pass without a human click; changed expected values or new temporal meaning cannot; unusual but valid ideas are retained.

## 15. OPEN-15: source-gap policy

**Decision:** retain the current archive and SRC-001 through SRC-008 exactly. Continue using the already authorized source-limited reconstruction. New recovery is a separately versioned evidence set with checksums, provenance comparison and an affected-decision audit. Never synthesize a missing image, file body or acceptance message.

This closes the question of how to proceed with source gaps. It does not label the sources recovered or fully verified. Original recovery remains an external evidence task and is not a prerequisite for implementing independently specified, approved contracts.

**Affected:** D008/D043, source audit and all source-qualified decisions. **Acceptance:** immutable archive hashes match; later recovery can be attached without overwriting prior bytes; confidence qualifications remain visible.

## Integration, implementation and rollback plan

Use existing CMP/IF ownership. Do not create another architecture or duplicate canonical register. After explicit approval:

| Order | Integration work | Completion evidence |
|---|---|---|
| 1 | Record the user's exact approval and append decisions after D070; update structured register and rejection dispositions only where superseded | Decisions, counts, source links and reverse trace agree; old records retained |
| 2 | Add versioned definition extensions for lifecycle, origin uncertainty, outcome rules, transport and certification; retain reconstruction-1 and document 13 v1.0 | Explicit version resolution and legacy mapping; no ambiguous replacement |
| 3 | Propagate to documents 01/05–13 and CURRENT_STATE; mark each OPEN item as design-resolved, scoped/deferred or externally unresolved with exact reasons | No document still describes an adopted rule as undecided; no external fact falsely marked complete |
| 4 | If application code is authorized, build schemas/AST/registry and deterministic fixtures, then a bounded provider/adapter slice | Real executable tests for affected TEST IDs; source-only statements updated to actual capabilities |
| 5 | Acquire/pin the selected inputs and dependencies only for an authorized run; execute technical, calibration and research work separately | Exact versions, costs, access checks, retained failure reports and honest gate-specific outcomes |

The semantic dependency order is lifecycle and certification envelope -> expression/evaluation/data contracts -> atomic freeze/exposure/allocation -> execution/evidence -> feedback and policy use. Storage mechanics can be developed independently, but must not hardcode unapproved scientific outcomes. This proposal does not require a new service for any logical role.

Rollback preserves the approved proposal, old and new definition versions, manifests, all failed probes and exposure history. Select an earlier approved configuration for future runs; never reinterpret a frozen run under another method or delete its result. Unrecoverable ambiguity quarantines the affected projection. A new calibrated estimator is a new policy version, not a retrospective repair of the old inference.

## Decision requested

Approve or amend version 0.1 as the basis for binding specification integration, including the scoped numerical policies and certification boundary. The proposal makes no live-trading authorization, data purchase, proof of profitability or claim that all future claim types already have calibrated estimators.

If application code is also intended, its completion remains a distinct deliverable after scientific adoption, with the acceptance evidence above. Until approval, these are reviewable proposed resolutions; the canonical OPEN statuses and definitions remain unchanged.
