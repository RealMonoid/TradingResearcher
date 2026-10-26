# TradingResearcher

Source-backed architecture for an autonomous market-research framework: an LLM independently develops hypotheses, freezes executable claims before confirmation, and submits them to independent code for evaluation.

The framework must substantially accelerate both hypothesis discovery and testing while preserving scientific decision quality. The [Problem Definition](docs/architecture/01_PROBLEM_DEFINITION.md) states both goals; the [Master Architecture](docs/architecture/06_MASTER_ARCHITECTURE.md) connects research, early exits, feedback and decision authority.

The economic objective is profitably usable hypotheses after realistic costs, not beating quantitative firms or proving LLM superiority. Whether the framework achieves that objective is an empirical question, not a prerequisite for building it. The [Generator Feedback and Evaluation Contract](docs/architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md) specifies feedback use, later evaluation and discovery diagnostics.

**Status:** framework specifications, preserved sources, a runnable [local coordination runtime](trading_researcher/README.md), and a bounded [AmiBroker CLI utility](tools/amibroker/README.md) with a verified Binance import/exploration/export smoke test. The coordination runtime provides a SQLite queue, scoped immutable artifacts, fenced leases, operational completion checks and generic triggers. The autonomous research framework, scientific evaluator and live deployment are not implemented; no trading edge is demonstrated.

## Start here

The [technical revocation path](trading_researcher/REVOCATIONS.md) now prevents new use of explicitly revoked data, certificates and retained implementation versions. It follows actual typed dependencies, preserves historical results and exposure, and retains failures when revocation arrives during computation. It grants no scientific validity or empirical verdict.

The [meaning-review plan integration](docs/reviews/implementation-2026-10-25/PLAN_MEANING_INTEGRATION_2026-10-26.md) now binds review evidence to the exact compiled formalization and feature definitions. Current inspection reopens the semantic prerequisite when review history or policy changes. Historical plan bytes and all other scientific gates remain intact.

The [latest meaning-review observation](docs/reviews/implementation-2026-10-25/MEANING_REVIEW_OBSERVATION_2026-10-26.md) records a corrected complete comparison: all eight actual model judgments match the independently fixed expectations, with earlier incomplete attempts retained. Two exact targets satisfy only the independent-review process prerequisite; scientific admission remains unfinished. Aggregate framework usage is now 145,641 tokens and a conservative USD 0.404925.

The [October 26 publication checkpoint](docs/reviews/implementation-2026-10-25/GITHUB_PUBLICATION_2026-10-26.md) publishes the complete implementation work in progress, including the newly added independent meaning-review assessment. Its offline process checks are separate from actual model-quality validation and scientific admission. Credentials, private registries and market-data downloads remain local.

The [controller-owned direct provider path](trading_researcher/CONTROLLER_PROVIDERS.md) retains genuine auxiliary invocation provenance independently of worker-submitted replies. Two actual OpenAI calls exercised an unsupported-idea handoff and a separate review. At that earlier checkpoint, recorded framework usage was 37,372 tokens and a conservative USD 0.1022725; scientific admission remains unfinished.

The [direct Claude adapter](trading_researcher/ANTHROPIC.md) now prepares the user-requested mixed-model research run. A controller test exercises OpenAI and Claude native tool loops with mocked HTTPS, shared accounting and isolated contexts. This is offline protocol evidence; live Claude compatibility and mixed-model research quality remain unverified.

The October 25 implementation adds a [research memory foundation](trading_researcher/MEMORY.md): typed immutable inquiry records, scoped search, host-observed attempt history, projection replay, and verified migration/backup paths. Scientific publication into the Market Model and the rest of the [execution plan](docs/reviews/integration-research-2026-10-24/IMPLEMENTATION_SEQUENCE_2026-10-25.md) remain work in progress. A deterministic fixture demonstrates memory behavior; it is not an autonomous research result.

The [provider-neutral researcher loop](trading_researcher/RESEARCHER.md) adds durable shared call budgets, frozen prompts/tools, isolated perspective transcripts, bounded tools, retained provider responses, timeout/cancellation handling and a runnable `research-demo`. The [OpenAI adapter and persistent usage report](trading_researcher/OPENAI.md) now pass a four-call live integration test with two isolated perspectives on synthetic input. Its 2,172 reported tokens are a technical smoke-test observation, not typical research consumption or scientific evidence. Full-context research, scientific formalization and evaluation remain unfinished.

A subsequent [six-call provider/measurement check](docs/reviews/implementation-2026-10-25/OPENAI_MEASUREMENT_INTEGRATION_2026-10-25.md) exercises real retained Binance development data, exact source paging and original-versus-presented response retention. Both perspectives completed; an independent exact-value comparison passed. The optional presentation remains a development capability without demonstrated research-quality equivalence. At that checkpoint cumulative provider usage was 35,084 tokens, recorded by model/version and UTC time.

A bounded [reference expression calculator](trading_researcher/EXPRESSIONS.md) now implements exact arithmetic, typed missingness, Boolean logic and causal grid lookups. Independently authored cases verify that interface. Feature certification, complete H_idea/H_exec mapping, scientific freeze and evaluation are still pending.

[Development measurement tools](trading_researcher/MEASUREMENTS.md) now connect retained provider requests to authorized causal expressions, exact descriptive results, explicit gaps and private exposure. Source retention and release checks prevent a stopped epoch from receiving results through a secondary artifact-read path. A direct HTTP probe on retained Binance data passed; the separate full-context scripted loop hit its input budget before dispatch and remains an integration limitation.

The [formalization draft boundary](trading_researcher/FORMALIZATION.md) preserves original ideas separately from executable candidates, records semantic mapping assertions, checks the canonical contrast's typed structure and parameter origins, and retains unsupported forms as explicit gaps. It cannot issue scientific readiness or evidence.

The [reference outcome calculator](trading_researcher/OUTCOMES.md) adds exact future anchors, decision-time availability, explicit pending/missing/boundary cases and the descriptive condition-minus-whole-scope contrast. Independently fixed fixtures exercise this interface. Uncertain outcome dependencies remain review gaps; no scientific certificate or completed-outcome monitoring event follows.

The [implementation certification gate](trading_researcher/CERTIFICATION.md) runs fixed independent expectations in a fresh isolated Python snapshot, retains host-issued certificates or gaps, and detects changed code/runtime versions. It certifies the exercised reference implementation only; data/feature validity, faithful semantic mapping, calibrated inference and scientific freeze remain separate work.

[Immutable external storage](trading_researcher/STORAGE.md) now retains larger supplied files and exact reference source packages, verifies committed bytes, and supports complete database/blob backup and restoration. Retained source packages can be revalidated independently of the working checkout; interrupted checks remain visible. Byte integrity and implementation replay do not establish market-data quality, historical availability or scientific validity.

[Bound data snapshots](trading_researcher/DATA.md) now bind exact normalized row files, catalogs, raw sources and qualified acquisition metadata. The host checks ordered grid coverage, types, protected ancestry and source integrity; missing rows and unknown availability remain explicit. Acquisition acceptance, feature certification and scientific execution remain separate gates.

The [Binance archive adapter](trading_researcher/BINANCE.md) now preserves exact public archive/checksum files, validates declared timestamp units and OHLCV structure, retains data gaps, and constructs explicitly assumed availability scenarios. Independent fixtures and real downloads exercise this boundary. Archive integrity does not establish historical vintage, complete-bar validity for every source row or scientific suitability.

The same adapter now retains keyed invalid bars separately from absent bars, emits only null measurements for unusable keyed observations, and imports exact sources and quality records into owned registry storage. All 144 adopted archives, provider documents and the processing source checkout survive a verified full backup/restore. Legacy failed receipts retain an explicit unverified file/time binding.

The [partition normalizer](trading_researcher/BINANCE_NORMALIZATION.md) executes a fresh retained Python source snapshot and has produced the three real calendar datasets with explicit boundary counts and a separately recorded assumed delay. Original receipt validation and ancestry remain intact. This supplies qualified structural data snapshots; feature certification, scientific data acceptance and inference remain pending.

The [raw measurement certification gate](trading_researcher/FEATURES.md) binds the existing symbol-specific Binance fields to an owned snapshot through independent fixed expectations and complete source replay. Host-controlled definitions and certificates preserve assumed availability, invalid/absent rows and exposure. This bounded implementation does not establish historical PIT, scientific acceptance, arbitrary composition certification or scientific execution.

[Bound reference computations](trading_researcher/BINDING.md) now connect completed formalizations, exact data/feature identities and retained calculator versions. Development execution preserves warmup, missingness and exposure, and checks returned cases and descriptive contrasts in a separate retained process. Protected partitions remain denied; semantic approval, scientific freeze and inference remain pending.

The [historical evaluation policy and plan-preparation path](trading_researcher/EVALUATION_POLICY.md) now implement exact pilot-effect, family-budget, interval and fixed-release rules, plus owned development-bound drafts calculated and replayed from retained source. These drafts explicitly retain missing calibration, semantic review and scientific freeze gates. No assessment access or empirical evidence is issued.

Admitted plan inputs and source versions are retained before calculation, including for interrupted attempts. Same-key retries use the original captured version; restart and complete backup/restore preserve its identity and exposure. [Retention verification](docs/reviews/implementation-2026-10-25/plan-retention-verification.json) distinguishes this recovery capability from unfinished scientific admission.

The [auxiliary research handoff](trading_researcher/AUXILIARY_RESEARCH.md) now connects formalization and a separate meaning-review worker to the original epoch budget. Exact inputs, timely call receipts and independent role identity are retained. Scripted or merely relabeled live responses cannot establish actual independent model judgment or scientific approval.

The [joint stationary-bootstrap candidate](trading_researcher/STATIONARY_BOOTSTRAP.md) now performs the prescribed fixed resamples on aligned timestamp buckets, retains undefined/interrupted draws and binds exploratory development runs to stored plans and case data. Exact integer arithmetic accelerates the exercised integral-outcome workloads while preserving results against the retained Fraction version. Source/draw replay and workload timings are separate from the remaining calibration, information and scientific freeze gates.

The optional [Monte Carlo boundary diagnostic](trading_researcher/MONTE_CARLO.md) now assesses whether finite resampling uncertainty can change the interval's nominal decision. Its exact settings are retained before execution; missing draws remain unassessed. This is an uncalibrated development capability and does not issue scientific readiness.

The [owned information diagnostics](trading_researcher/INFORMATION_DIAGNOSTICS.md) now retain exact development rates, full-grid dependence measurements and missingness coverage against an existing plan and execution. The population model, power study, information target and scientific calibration remain separate work.

The [owned binary population worlds](trading_researcher/POPULATION_MODELS.md) now bind those diagnostics to explicit response/mask stress assumptions, plan-assigned effects and exact rational generation. Their synthetic identity, original missingness provenance, source bytes and separate replay are retained. Dependence fitting/adequacy, complete power studies, N_min and scientific calibration remain outstanding.

The [owned development study](trading_researcher/INFORMATION_STUDIES.md) now connects a complete fixed world/seed inventory to the actual bootstrap/MC pipeline and separate process replay. Shared compute/storage reservations retain failures and prevent a changed request key from resetting the same study. Complete-grid summaries can nominate only a development candidate; model adequacy, N_min, fresh calibration and scientific freeze remain pending.

The [narrow calibration component](trading_researcher/CALIBRATION.md) checks adopted exact acceptance bounds on complete predeclared 256-world cohorts. An owned single-claim runner now binds protected final draws to retained calculator execution, separate replay and durable accounting. The read-only supplied-count CLI remains separate. Complete final calibration, mixed-truth multi-claim worlds, population adequacy and scientific admission remain unresolved.

**For LLM reviewers:** Follow [REVIEWING.md](REVIEWING.md) before a framework-wide critique. First present a source-linked reconstruction of goals, flow, feedback, authority and open boundaries. If access or context is incomplete, state the limits and withhold an overall verdict; do not treat a partial reading as the whole system.

- [Source audit and known gaps](docs/architecture/00_SOURCE_AUDIT.md)
- [Problem definition](docs/architecture/01_PROBLEM_DEFINITION.md)
- [Decision register](docs/architecture/02_DECISION_REGISTER.md)
- [Rejected and replaced alternatives](docs/architecture/03_REJECTED_DECISIONS.md)
- [Canonical definitions and preserved formulas](docs/architecture/04_DEFINITIONS.md)
- [Requirements](docs/architecture/05_REQUIREMENTS.md)
- [Master architecture](docs/architecture/06_MASTER_ARCHITECTURE.md)
- [Scientific evaluation](docs/architecture/07_SCIENTIFIC_EVALUATION.md)
- [Engineering review](docs/architecture/08_ENGINEERING_REVIEW.md)
- [Implementation blueprint](docs/architecture/09_IMPLEMENTATION_BLUEPRINT.md)
- [Proposed roadmap](docs/architecture/10_IMPLEMENTATION_ROADMAP.md)
- [Open decisions](docs/architecture/11_OPEN_DECISIONS.md)
- [Traceability matrix](docs/architecture/12_TRACEABILITY_MATRIX.md)
- [Generator feedback and evaluation contract](docs/architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md)
- [Adopted retail research contract](docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md)
- [Agent inquiry discipline](docs/architecture/15_AGENT_INQUIRY_DISCIPLINE.md) (D086; approved working practice, runtime behavior unverified)
- [Temporal diagnostic invocation](docs/architecture/16_TEMPORAL_DIAGNOSTIC_INVOCATION.md) (D087; automatic due checks specified, runtime and statistical method unverified)
- [Monitoring visibility and reporting](docs/architecture/17_MONITORING_VISIBILITY_AND_REPORTING.md) (D088; weekly status and actionable notices specified, runtime and delivery unverified)

For selection bias and overfitting, the [integrated evaluation guidance](docs/architecture/07_SCIENTIFIC_EVALUATION.md#overfitting-controls-across-the-research-process) connects discovery, Columns, policy search and generator feedback. The [October 23 framework review](docs/reviews/OVERFITTING_REVIEW_2026-10-23.md) records the system assessment and documentation changes. These earlier reviews clarify existing decisions. D071-D085 now adopt the scoped statistical and implementation contracts. Bounded coordination controls have executable tests; full research isolation and scientific runtime conformance remain unverified.

D087 adopts a later [automatic temporal diagnostic invocation contract](docs/architecture/16_TEMPORAL_DIAGNOSTIC_INVOCATION.md). It makes a committed batch of eligible completed outcomes and each intended use trigger the appropriate due/scope check for a bound plan. It does not select a universal monitoring interval, decay estimator, alarm threshold or live action rule.

D088 adopts [background temporal work and reporting](docs/architecture/17_MONITORING_VISIBILITY_AND_REPORTING.md): an authorized bounded method comparison starts when ready, open work stays visible, and the future framework sends a weekly status report plus prompt notices when user action is needed. Report timing is separate from scientific checkpoints. Generic bounded time/event triggers now exist; completed-outcome event production, diagnostic execution, weekly report generation and message delivery remain unimplemented.

## Evidence and limits

The archive contains 305 message blocks from 304 numbered turns of the accessible shared conversation. Two original images, three cited document bodies and an original export were unavailable; one captured response is incomplete. Full original-source completeness is not verified. Reconstruction continued with the user's explicit authorization to retain documented source gaps.

The decision register separates accepted decisions, conditional choices, superseded positions, deferred work and new proposals. The roadmap and implementation contracts are not evidence that an application has been built.

- [Exact captured transcript](sources/full_conversation.md)
- [Source manifest and checksums](sources/capture_manifest.json)
- [Message review index](docs/architecture/SOURCE_REVIEW_INDEX.md)
- [Machine-readable architecture register](docs/architecture/ARCHITECTURE_REGISTER.json)
- [Documentation verification results](docs/architecture/DOCUMENTATION_VERIFICATION.json)

Files under `sources/` are preserved byte-for-byte. Git attributes disable text conversion for that directory. Verify their SHA-256 hashes against the capture manifest before using a new checkout for reconstruction or further analysis.

Project documentation is English (en-US); original source quotations retain their language.

## Adopted open-decision resolutions

The [October 23 systematic assessment and literature review](docs/reviews/OPEN_DECISION_RESEARCH_2026-10-23.md) reconstructs the framework and accounts for all 15 open items. Its [retail research contract proposal, version 0.1](docs/reviews/RETAIL_RESEARCH_CONTRACT_PROPOSAL_2026-10-23.md) supplies concrete historical-first resolutions, scoped statistical/resource policies, acceptance cases and an integration/rollback plan. The user approved v0.1 with "Freigabe". D071-D085 now adopt its policies in the [Retail Research Contract, research-contract/1.0](docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md), with versioned definitions and current dispositions. The linked proposal remains the immutable preapproval document. Specification integration is complete; application implementation, data validation and empirical calibration are not established. See the [adoption verification](docs/reviews/adoption-2026-10-23/verification.json) for exact checks and changed files.
