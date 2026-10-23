# Open-decision research and system assessment

Date: October 23, 2026. Status: **REVIEW AND PROPOSAL, NOT ADOPTED SCIENTIFIC POLICY**.

This assessment supports the [concrete closure proposal](RETAIL_RESEARCH_CONTRACT_PROPOSAL_2026-10-23.md). It does not declare the framework implemented or the open decisions approved.

## Task, review basis and acceptance criteria

The current user requested a systematic understanding of the entire framework, identification of missing decisions, scientific literature research, solutions, documentation and complete implementation. The user emphasized retail economics and decisions without days, weeks or months of mandatory forward observation. This instruction is separate from the immutable original conversation. Whether implementation means specification integration or application code was asked explicitly; it does not change the research findings below.

Review basis: branch `codex/architecture`, HEAD `395aa375dd645c3191726f0b27a1da079d1e5904`, plus the working-tree changes already present at task entry. Those changes include the October 23 overfitting revision and the Mabe research report. HEAD alone is not the reviewed version. A pre-edit inventory records all 60 existing project files; the final verification report identifies the files changed by this task.

Observable acceptance for the work before scientific approval:

1. Reconstruct goals, ordinary and failure paths, feedback, authority and actual capability from the owning documents.
2. Account for every OPEN-01 through OPEN-15, including narrower blockers and unresolved external facts.
3. Link methodological recommendations to inspected primary literature and state transfer limits.
4. Supply concrete choices, alternatives, consequences, checks, versioning and rollback, rather than another list of questions.
5. Preserve accepted decisions, definitions, source bytes and pre-existing edits until an explicit approval authorizes their semantic revision.
6. Verify document links, consistency, coverage, arithmetic examples and preservation. These checks are not scientific calibration or application tests.

Implementation acceptance after approval is specified in the companion proposal. The current task is not complete merely because this review exists.

## Reconstructed system before assessment

### Goals and distinct success questions

The [Problem Definition](../architecture/01_PROBLEM_DEFINITION.md) and D001 require autonomous, nontrivial LLM invention, faithful formalization before confirmation and independent code judgment. D068 additionally requires substantial acceleration of discovery **and** testing without weakening decision quality. D069 seeks profitably usable hypotheses after realistic costs; outperforming quantitative firms or another generator is unnecessary. D015 rejects a competing rule-catalog hypothesis generator, not statistical references or null controls.

A technically valid negative result can be useful research. It does not establish overall framework success. Support for a market claim does not establish a profitable policy. A positive policy result does not calibrate the generator. These are separate assessment questions under [document 13](../architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md).

### Ordinary path and information boundaries

The [Master Architecture](../architecture/06_MASTER_ARCHITECTURE.md) and [Blueprint](../architecture/09_IMPLEMENTATION_BLUEPRINT.md) connect the following flow:

1. CMP-01 assembles a versioned context from available data, sources, certified features and permitted knowledge/experience. Event time is insufficient: availability, revisions, fitted state and all used ancestry matter.
2. CMP-02 finds questions, queries permitted data, consults sources and submits free H_idea. Discovery can be theory-first, data-first or recombination. V1 observations start at 15 minutes; outcome horizons may extend into swing research.
3. CMP-03 formalizes without quietly changing the claim. Independent feature certification and compiler checks establish measurement and execution semantics, not predictive value.
4. CMP-04 assigns a predefined evaluation policy, checks exposure and allocation, and freezes the exact request, versions and trial identity before confirmatory outcomes are released.
5. CMP-05 computes cases or simulates the policy. CMP-06 applies the frozen rule and retains effect, uncertainty, validity and evidence origin. The LLM cannot select the verdict.
6. The Journal retains the trajectory; qualified evidence enters the Market Model. Later epochs may retrieve both knowledge and experience with exposure intact.
7. A policy assembled from claims or explicit untested assumptions has its own provenance, freeze and evaluation. Deployment requires separate authority; an evidence label grants no capital.

Historical-first execution is already accepted under D013/D053. It is not blocked on future data as a universal prerequisite. Unknown model exposure prevents certifying history as model-unseen. Historical evaluation can still answer qualified questions and help decide what to abandon or research next.

### Failure path and subsequent learning

An idea requiring unavailable order-book depth is retained with a data/feature gap. It produces no empirical negative and needs no speculative proxy. The Journal records the attempted formalization and retry condition; Research Experience may suggest a later data-acquisition or measurement improvement. A later epoch can use that lesson while inheriting its sources and exposure.

Alternatively, an executable trial can fail because a feature includes late information. The run is quarantined with an ErrorEvent. Revocation follows relevant hard dependencies; a repaired computation creates a new version and does not erase the error or restore freshness. An inconclusive valid test is a third outcome and must not be collapsed into either failure path.

### Four feedback loops and authority

| Loop | What travels | Permitted effect |
|---|---|---|
| Market knowledge | Qualified positive, negative and conflicting evidence | Inform later hypotheses within origin, scope and uncertainty limits |
| Research experience | Trajectories, abandoned ideas, gaps, errors and interpreted lessons | Guide later search; never manufacture empirical support |
| Policy experience | Separate policy tests, fills, costs and registered operating observations | Diagnose policies; research receives registered questions in later epochs |
| Governed improvement | Proposed prompt, retrieval, compiler or policy changes and validation | Activate only the approved version; rollback retains exposure and failed probes |

The [Decision Register](../architecture/02_DECISION_REGISTER.md), versioned [Definitions](../architecture/04_DEFINITIONS.md) and scope-sensitive [Rejected Decisions](../architecture/03_REJECTED_DECISIONS.md) govern. The runtime, LLM, backend and this review have no independent authority to redefine evidence. OPEN-14 is a real unresolved policy boundary, not a blanket requirement for manual approval of every feature.

### Actual state and limits of reconstruction

The repository has architecture documents, source records and documentation-checking scripts. It has no application runtime, executable scientific contracts, market-data acquisition, tested backend adapter or demonstrated trading edge. TEST-01 through TEST-30 are acceptance specifications, not tests executed by this review.

All architecture documents 00–13, the entry documents and the current open register were inspected. Long reads that were truncated were repeated in bounded sections. The disputed subset and prevalence statements were checked against M0144 and M0158 through the [Source Review Index](../architecture/SOURCE_REVIEW_INDEX.md). The [Source Audit](../architecture/00_SOURCE_AUDIT.md) still records missing images, cited file bodies, an original export and incomplete M0302. This is a coherent reconstruction of the available specification, not a claim of exhaustive access to the private original conversation.

## Findings and complete gap disposition

The central problem is not missing scientific aspirations. It is that several transitions still lack executable decision rules. Adding more warnings about overfitting would not close them.

| Item | Observed gap and trigger | Existing safeguard and why it is insufficient | Proposed disposition |
|---|---|---|---|
| OPEN-01 | Historical execution must leave FROZEN, but DEF-016 specifies prospective collection; one status mixes incompatible axes | D013/D020 state the intended separation but do not provide a versioned transition contract | Separate execution, outcome, origin, replication, usability and applicability; preserve legacy definitions. Proposal §1 |
| OPEN-02 | A policy narrows a supported population | M0144's subset statement checks set inclusion, not subgroup effect; D010 protects the whole policy but does not validate the narrower premise | Require direct target evidence or an approved transport contract; otherwise explicit assumption. §2 |
| OPEN-03 | Dashboard success rates become numerical truth priors | D024 separates power from credibility; the M0158 replicated/tested example lacks selection and power modeling | Descriptive cohort rates only; no numerical truth prior in v1. §3 |
| OPEN-04 | A free idea reaches the compiler | Five relationship names do not define units, missingness, estimands, temporal operations or policy updates | Typed language with explicit estimator dispatch and retained unsupported expressions. §4 |
| OPEN-05 | A result must become supported, negative or inconclusive | Complete EvaluationPlan fields are required, but method selection, interval rules and information sufficiency are absent | Fixed historical batch profile, meaningful-effect intervals and calibrated method eligibility. §5 |
| OPEN-06 | A real-data run is requested | PIT and cost requirements do not identify a usable acquisition profile or treatment of unverified availability | Named research pilot, versioned acquisition acceptance, conditional cost results until verified. §6 |
| OPEN-07 | A runtime is adopted | Hermes is a conditional candidate; automatic memory/skill behavior can alter a frozen generator | Narrow adapter contract; no mandatory Hermes dependency; adoption only after isolation probes. §7 |
| OPEN-08 | Freeze or recovery spans artifacts and registry | The blueprint requests atomicity but leaves serialization, transaction and recovery choices open | SQLite-owned immutable small payloads plus verified external blobs; versioned serialization and restore tests. §8 |
| OPEN-09 | Discovery expands | Target perspectives and cost monitoring lack a bounded initial execution profile | Two isolated sequential perspectives, shared snapshot, fixed call/token/time caps, measured expansion. §9 |
| OPEN-10 | Research output is interpreted as deployable | Evidence-to-decision is separate but no active operating mode is specified | Research-only v1, zero capital and no order API; future live specification is a separate capability. §10 |
| OPEN-11 | The project claims success or stops investing | D025/D068/D070 distinguish questions but give no concrete pilot continuation gates | Separate technical, information, calibration, economics and acceleration decisions. §11 |
| OPEN-12 | Many candidates compete for finite evidence | Exposure is logged, but family assignment, queue and feedback release remain unspecified | Small predeclared batch, joint error budget, no outcome-informed additions, qualified reuse. §12 |
| OPEN-13 | Dependencies or operating conditions change | Typed dependencies are specified without a consequence table or default applicability policy | Hard invalidation, review and operational suspension separated; unknown applicability cannot become current by default. §13 |
| OPEN-14 | A feature or language implementation is added | Independent certification and material approval coexist without a routing rule | Automated certification within an approved semantic envelope; explicit approval for changes to that envelope. §14 |
| OPEN-15 | Missing source material may contain relevant context | The audit permits source-limited continuation but cannot recover missing facts | Close the handling policy, retain the factual source gaps and version any later recovery. §15 |

Additional cross-cutting gaps belong in these existing items, not another registry: confounding of computation time with information maturity (01/05/11); joint uncertainty for the overlapping scope baseline (04/05); censoring of slow or failed hypotheses (03/11); hidden selection through pass/fail feedback (12); and undocumented limits of runtime permissions and reproducibility (07/08/09). The proposal makes these observable.

## Literature method and evidence ledger

This was a targeted primary-source review, not a systematic review with exhaustive database coverage. Searches covered multiple testing, dependent time-series resampling, equivalence/minimum relevant effects, sequential inference, adaptive data reuse, transportability, family prevalence and trading costs. Publication pages, author-hosted texts and research repositories were preferred. Sources below were inspected on October 23, 2026. The project choices are deductions and tradeoffs, not results experimentally established for this framework.

| ID and primary source | Inspected evidence | Design implication and transfer limit |
|---|---|---|
| LIT-01: [Cawley and Talbot, JMLR 2010](https://jmlr.org/papers/v11/cawley10a.html) | Publisher abstract, selection-criterion variance and evaluation bias | Selecting a protocol on its own assessment outcomes is another optimization. Separate development and final assessment. This paper does not quantify LLM trading bias. |
| LIT-02: [Dwork et al., NeurIPS 2015](https://proceedings.neurips.cc/paper_files/paper/2015/file/bad5f33780c42f2588878a9d07405083-Paper.pdf) | Abstract and introduction, pp. 1–2 | Adaptive feedback can overfit a holdout. Record release/use and restrict descendant confirmation. Thresholdout is not adopted: its guarantees are not automatically available for market dependence. |
| LIT-03: [Goeman and Solari, Annals of Statistics 2010](https://arxiv.org/html/1211.3313) | Section 3, valid marginal tests, Bonferroni inequality and Holm | A simple family correction can tolerate dependence between valid marginal tests. It cannot fix invalid marginal inference or hidden adaptive use. Its sequential rejection concerns hypotheses, not time-series peeking. |
| LIT-04: [Politis and Romano, JASA 1994](https://doi.org/10.1080/01621459.1994.10476870) | Publisher abstract and extracted introduction from the [paper](https://users.ssc.wisc.edu/~behansen/718/Politis%20Romano.pdf); PDF text extraction was incomplete | Stationary bootstrap is a candidate for weakly dependent stationary data. It is not a finite-sample or regime-change guarantee. Block design and calibration remain substantive. |
| LIT-05: [Lakens, 2017](https://pure.tue.nl/ws/portalfiles/portal/80918653/lakeequi2017.pdf) | Introduction, equivalence/inferiority discussion and dependence qualification | A nonsignificant result cannot establish absence of a useful effect. Prespecify meaningful bounds. Psychological t-test formulas are not copied into market tests. |
| LIT-06: [Lakens, 2022](https://pure.tue.nl/ws/portalfiles/portal/214011492/collabra_2022_8_1_33267.pdf) | Introduction and resource-constraint discussion | Justify attainable information under finite resources. Report sensitivity/precision rather than inventing a universal trade count. A detectable effect is not automatically economically worthwhile. |
| LIT-07: [Howard et al., Annals of Statistics 2021, author v9](https://arxiv.org/html/1810.08240v9) | Introduction and §2, filtration, conditional expectations and sub-psi conditions | Valid confidence sequences permit flexible stopping under assumptions. They do not create observations, repair exposure or automatically cover overlapping financial outcomes. No universal sequential gate is selected. |
| LIT-08: [Pearl and Bareinboim, Statistical Science 2014](https://arxiv.org/pdf/1503.01603) | Introduction and §3 examples of transport assumptions | Population transfer needs substantive conditions. Causal transport mathematics is not proof that observational subgroup associations transfer; v1 uses direct target evidence unless a separate transport method is approved. |
| LIT-09: [Storey and Tibshirani, PNAS 2003](https://genomics.princeton.edu/storeylab/papers/Storey_Tibs_PNAS_2003.pdf) | Introduction and discussion of estimating q-values under weak dependence | Prevalence/FDR estimation has an explicit statistical model. A raw replication fraction is not such an estimator. Genomic q-value machinery is not adopted as an LLM family truth score. |
| LIT-10: [White, Econometrica 2000](https://users.ssc.wisc.edu/~behansen/718/White2000.pdf) | Abstract and introduction | Search-aware benchmark testing motivates retaining the searched alternatives. A fixed-family analysis cannot stand in for an unrecorded adaptive research process. |
| LIT-11: [Novy-Marx and Velikov, RFS 2016; August 2015 author manuscript](https://mysimon.rochester.edu/novy-marx/research/ToAatTC.pdf) | Abstract; [publisher metadata](https://doi.org/10.1093/rfs/hhv063) | Costs can change economic and statistical conclusions. Use actual execution conventions and cost sensitivity. Stock-anomaly estimates do not supply retail crypto fees, tax assumptions or capacity guarantees. |

Access limits: Holm's original PDF timed out twice; the recommendation uses Goeman–Solari's accessible treatment. PMC returned a browser challenge for Lakens 2017; the author-institution PDF was accessible. NBER's direct full-text request returned 403; the author manuscript was accessible. No unavailable text is represented as inspected. This was not a proof audit of the listed papers.

Engineering sources were also inspected: [SQLite atomic commit](https://sqlite.org/atomiccommit.html), [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html), [Binance public-data README](https://github.com/binance/binance-public-data/blob/master/README.md), [vectorbt license](https://github.com/polakowo/vectorbt/blob/master/LICENSE.md) and [Hermes README](https://github.com/NousResearch/hermes-agent/blob/main/README.md). SQLite documents transaction durability assumptions; RFC 8785 explains invariant serialization. Binance documents checksums and later archive corrections. vectorbt lists Apache 2.0 with Commons Clause; Hermes describes automatic memory/skill learning. These observations do not establish legal suitability, dataset completeness, safe runtime isolation or adapter conformance. No dependency or dataset was installed or acquired.

## What the retail constraint changes

The fastest defensible answer is often a resource-allocation decision: abandon, retain a gap, continue bounded historical research, or retain qualified support. It need not be a claim of clean forward confirmation. Fixed historical batches can be computed immediately once the data and contracts are ready. There is no scientific reason to add calendar waiting merely because a conventional example used a prospective trial.

There is also no defensible method that guarantees a conclusive answer about every small or rare effect within minutes. If the available evidence cannot distinguish relevant effects, the framework should end that work unit with an explicit unresolved result and cost, rather than wait indefinitely or weaken the threshold. This preserves speed and epistemic honesty simultaneously.

Avoid spending the entire budget validating statistically small findings that cannot survive costs. Conversely, do not require a positive entry effect before researching exits, sizing or interactions. Prioritize actual decision relevance and capability, without turning an LLM's expected-profit story into a numerical truth prior.

## Recommendation and next authority boundary

Adopt the companion proposal as one reviewed specification package, with the stated scoped defaults and external prerequisites. It gives each open item a disposition and preserves broader capabilities through explicit extension contracts. It does not promise profitable outcomes or completion of unavailable source recovery.

Before activation, D008/D026 and the current AGENTS.md require explicit user approval of the concrete scientific changes. Literature review is evidence for the rationale, not approval. The proposal includes exact propagation and rollback work so approval can be followed by integration without another architecture-design round.
