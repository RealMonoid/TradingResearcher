# Scientific Evaluation: Current Adoption

D071-D085 adopt [research-contract/1.0](14_RETAIL_RESEARCH_CONTRACT.md), including historical-batch-v1, finite information/resource decisions, independent target evidence and descriptive cohorts. The [literature review](../reviews/OPEN_DECISION_RESEARCH_2026-10-23.md) records the primary sources and transfer limits. The retained reviews below describe the earlier state; their OPEN/proposed annotations are historical, resolved for the bounded v1 scope by document 14. They do not override the adopted contract.

In particular, subgroup membership is not transport (D072), replication yield is not a truth prior (D073), and fixed historical evaluation does not require forward waiting (D071/D075). Simultaneous coverage relies on valid marginal intervals; the bootstrap candidate remains conditional/asymptotic and must pass conformance/calibration before runtime adoption. Full-process error under unknown model exposure is not established. A missing information target can yield inconclusive plus STOP. Technical invalidity never supplies market falsification.

Narrow evaluator calibration and full-process calibration remain separate. The approved 256-world, exact-bound tolerances and boundary cases are specified in contract section 11; no such experiment has been executed. Effect targets, budgets and acceleration thresholds are scoped user-approved policies, not empirical laws. No scientific validity or profitability is established by this specification update.

## Preserved earlier scientific reviews

# Scientific Evaluation

This is an independent critical assessment of the reconstructed design, not a report of completed market experiments. No profitability, calibration, power or independence claim has been empirically verified. Source decisions remain separate from the recommendations below.

## What is scientifically strong

The design treats discovery as adaptive and confirmation as constrained. It tracks selection beyond the final strategy, preserves failures and separates market claims from policy decisions. Transitive exposure, independent code, policy search accounting, genuine forward evidence and end-to-end process placebos address important failure channels that an isolated backtest does not see (D001, D014, D023–D025, D031, D038, D049).

None of those controls establishes that the LLM will generate valuable hypotheses. They make that question testable. The framework must retain technical-validity, calibration and economic-usefulness gates with fixed budgets and explicit failure criteria; their numeric values remain OPEN-05.

## Evaluation contract before confirmation

1. State the actual claim and estimand, units, direction and minimum relevant effect. Separate an association from a causal mechanism and a market effect from policy value.
2. Define claim scope, primary universe, justified negative controls and any planned replication universe. Record achievable coverage and limits to generalization.
3. Define event eligibility, duplicate/overlapping cases, horizon, missingness, censoring and permissible exclusions before observing confirmatory outcomes.
4. Declare data and model exposure, source availability, all used ancestry and evidence origin. Unknown model training exposure is not proof of independence.
5. Assign the statistical method, dependence assumptions, effect/interval reporting, power or precision design, family/selection rule and stopping policy independently of the generator.
6. Define the exact support, negative and inconclusive criteria. Failing to reject a null is not automatically evidence against a materially relevant effect.
7. Freeze costs, execution conventions and realistic alternatives for policy claims. Record parameter fitting and every outcome-dependent selection.
8. Specify replication independence, selection-aware controls and invalidity handling. Technical errors quarantine affected execution and require investigation, not a market verdict.

## Evidence origin and freshness

Historical backtests remain the primary development environment. They support exploration, falsification, operationalization and qualified evaluation. MODEL_UNSEEN_HISTORY requires credible model/version and information-boundary evidence, including retrieved sources and memory. A commercial model's advertised cutoff alone cannot certify complete ignorance.

TRUE_FORWARD means the relevant outcomes did not exist at freeze. It protects against prior knowledge of those outcomes, but does not by itself solve optional stopping, correlated cases, execution errors, selection over many claims or later feedback reuse. Once outcomes inform a new claim or its ancestors, they are not fresh evidence for that descendant.

Use sample IDs and interval provenance to measure overlap; different hypothesis IDs, instruments or calendar partitions do not imply independent evidence. Common market shocks and overlapping holding windows can reduce effective information. No universal sample count or one-year rule is imposed.

## Scope baseline and claim interpretation

M0072 defines the scope baseline using all eligible scope cases and the conditional rate using a subset. Preserve that definition. Because these estimates overlap, treating them as independent samples is generally inappropriate. If the intended scientific question instead compares conditioned cases with their complement, that is a different estimand and requires a new explicit definition.

M0144's claim that SCOPE_SUBSET is automatically unproblematic is scientifically too strong. An aggregate association can disappear or reverse within a subgroup. **PROPOSED CHANGE — USER APPROVAL REQUIRED (OPEN-02):** a subset relation should certify set membership only; evidence transport must separately satisfy predefined coverage and heterogeneity conditions. Until resolved, affected policy claims cannot be advertised as confirmed merely through subset membership.

M0158 illustrates family prevalence using replicated/tested counts. Those observations depend on power, replication selection, censoring and the truth criterion. **PROPOSED CHANGE — USER APPROVAL REQUIRED (OPEN-03):** preserve family outcome diagnostics but do not label their raw ratio as the probability a new effect is true or compute posterior support without a validated estimator. Low replication rates remain useful diagnostics with uncertainty.

## Multiplicity, adaptive search and controls

The trial ledger records search opportunities, not only successful freezes. It includes feature selection, horizons, filters, policy variants, generator probes and stopping decisions when outcomes influence selection. A total count alone does not describe dependence or adaptive selection sufficiently for every correction.

For a fixed candidate family, a suitable joint statistic or multiplicity method may be specified. For an adaptive research process, calibration may need to rerun the selection mechanism under the null. Match nuisance exposure and execution constraints without conditioning away the claimed mechanism. A null preserving trend asks a different question from a null removing temporal predictability. Store both the destroyed relation and preserved structures.

DSR is relevant to selection-biased Sharpe assessment; it is not an all-purpose verdict for binary, mechanism or observability claims. POPPER is a useful methodological reference for sequential falsification, but its validity is not inherited merely by reusing an agent loop. See the original [DSR paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551) and [POPPER paper](https://proceedings.mlr.press/v267/huang25n.html), consulted October 22, 2026. No method from either paper has been implemented or validated here.

## Full-process calibration specification

| Experiment | Required symmetry / ground truth | Report | Failure implication |
|---|---|---|---|
| Null worlds | Defined absence of the target exploitable relation; realistic nuisance structure where relevant | False-support rate with uncertainty across independent worlds/seeds | Scientific control failure if outside preregistered tolerance |
| Planted effects | Known effects spanning basic, boundary, interaction, decay and adaptive cases | Discovery power, effect/scope recovery, invalidation accuracy | Capability limit, or a representation/data defect requiring diagnosis |
| Process placebos | Same candidate and selection opportunities, including policy synthesis and fit depth | Selected real result versus selected placebo distribution on fresh data | Apparent skill may be explained by selection |
| Dependence stress | Overlapping cases, common shocks, regimes and clustered volatility | Sensitivity to dependence and resampling assumptions | Claimed uncertainty or error control may be invalid |
| Technical sentinels | Deliberate unavailable features, late revisions, duplicate trials, mutated manifests | Rejection/quarantine and complete audit trail | Engineering validity failure; no market conclusion |

Use enough independent calibration repetitions to estimate uncertainty; values must be chosen before results. Calibrating only a convenient Gaussian random walk is insufficient for claims about richer null structures. Synthetic success does not prove real-market economic value, and known planted effects must not leak into the discovery instructions as answers.

## Policy and Column Library evaluation

Event studies may separate signal response/decay from entry, exit, sizing and net policy performance. They are diagnostics rather than a compulsory linear hierarchy. Selecting the best decay horizon, filter or sizing rule is a new trial. The full combination needs its own evaluation even if all components look individually useful.

Entry columns must be known at entry. Evolving trade-state values are truncated at the decision time. Final MAE/MFE, time-to-extreme and complete path statistics are outcomes/diagnostics. Reusing one recorded path for many explorations does not multiply independent evidence; changing path-dependent execution or size may require resimulation.

Fitted parameters require predefined sensitivity tests. Broad stable relationships are preferable diagnostics to isolated peaks, but monotonicity, quintiles and continuous variables are not universal requirements. Tail-concentrated profits are not automatically invalid; removing best trades is a labeled stress test, not a universal rejection rule. Trade-order shuffling changes paths without creating new return observations and must preserve relevant dependence when used for risk diagnostics.

## Remaining scientific risks

Unknown model pretraining contamination, finite fresh evidence, low-power rare events, failure to account for all adaptive choices, and transportability dominate the epistemic risk. Economic costs, nonstationarity, execution realism and decision-time observability dominate the gap from supported claims to a useful policy. Neither multiple agents nor better documentation removes these risks; the tests and uncertainty reporting above are how they become observable.

## Adopted generator assessment extension

D069-D070 and the [Generator Feedback and Evaluation Contract](13_GENERATOR_FEEDBACK_AND_EVALUATION.md) add binding detail to the existing evaluation responsibilities. Profitably usable hypotheses are the economic objective; superiority to quantitative firms or another generator is not required. Before outcomes, specify the question, permissible inference, relevant effect/precision and resources, not the answer. Absolute-usefulness studies retain statistical references and separate policy testing without requiring a competing generator.

Feedback observations, interpretations and later uses are recorded separately. Procedural gains and economic improvement need different evidence; tuning feedback cannot simultaneously certify its descendant independently. Version comparisons account for repeated runs, matched information/resources, adaptive selection and pending cohorts. Novelty/diversity diagnostics are not evidence gates or reward functions. The academic basis and transfer limits are in document 13; this additive extension does not resolve OPEN-01 through OPEN-03 or choose numerical policies.

## Overfitting controls across the research process

October 23, 2026 clarification of D006/D014/D025/D031/D035/D038/D044-D051/D070. This supplement applies existing decisions to the complete selection process; it introduces no statistical default or replacement definition. The [framework review](../reviews/OVERFITTING_REVIEW_2026-10-23.md) records its scope. Concrete evaluation, allocation and assessment choices remain OPEN-05/11/12.

Independent execution protects who computes the answer. Honest evaluation additionally concerns which information shaped the question, representation, selection rule and reporting decision. A correctly computed backtest can still be an overfit selection. Feature certification checks measurement semantics and timing, not predictive usefulness. A trial ledger exposes search but is not itself a multiple-testing correction. Larger datasets, fewer final conditions and similar thresholds across periods do not alone establish independence or generalization. Selection-criterion overfitting is documented by [Cawley and Talbot](https://jmlr.org/papers/v11/cawley10a.html); its relevance here is a design deduction, not evidence about this framework's returns.

### Identify the object being evaluated

| Object and question | Evaluation boundary | Invalid interpretation |
|---|---|---|
| A selected, frozen market claim or policy: does this candidate meet its declared criterion? | Develop it on permitted discovery information, then evaluate under its assigned plan on admissible confirmation evidence. Account for concurrent claims and dependence. | The final development score estimates independent performance, or one successful candidate validates the generator. |
| A selection or adaptation procedure: how well does the process perform? | Freeze the procedure, permitted inputs/feedback, budgets and assessment. Selection and fitting belong inside each permitted training/development portion; outer assessment evaluates the procedure. | Select columns globally, refit only final coefficients in folds, and call the outer score independent of selection. |
| A generator version or feedback change: did this intervention improve the specified outcome? | Apply document 13's purpose-specific assessment, including comparable information/resources and a reference for comparison claims. Retain all probes and pending outcomes. | Repeated LLM calls or repeated replay of one market history count as additional independent market evidence. |

Nested evaluation is an option for a specified selection procedure. If used, repeat all data-dependent fitting and selection inside the appropriate inner boundary, including learned normalization, imputation, feature/rule selection and hyperparameters. A genuinely untouched final assessment of an already frozen candidate is another design; it does not require nested CV merely to use that label. Both require admissibility, exposure, dependence and multiplicity checks. [Varma and Simon](https://linus.nci.nih.gov/techreport/Varma-Simon-CrossValid.pdf) demonstrate selection bias and the value of nested assessment in classification simulations, not trading or arbitrary LLM workflows.

An LLM or human who already selected the idea using outer outcomes cannot become unexposed by resetting a chat or replaying the chosen rule in new folds. Process evaluation must represent the information actually used. Unknown pretraining exposure remains qualified under DEF-024/025; even a procedurally held-out historical partition is not automatically MODEL_UNSEEN_HISTORY. For continual adaptation, the frozen object can be an update rule with permitted feedback, rather than fixed parameters. Its evaluation must respect outcome availability and the declared deployment timeline.

### Selection and feedback remain visible

Record outcome-guided choices of columns, transformations, missing-data treatment, filters, horizons, instruments, exclusions, regimes, costs, policy rules and generator configurations under the existing selection provenance. Preserve the evaluated alternatives and the data/results driving each choice, including unsuccessful queries and abandoned branches. Reusing a certified calculation is different from independently confirming a relationship found with it.

Assessment release is an information event. A pass/fail bit, ranking, aggregate score or diagnostic plot can influence the next query even when raw outcomes are hidden. Once used, that feedback enters the descendant's exposure closure through the Journal, memory and context. This does not retroactively erase the original trial's valid frozen result; it changes what later work may claim as independent. Predeclared concurrent claims may share observations under an appropriate joint error/dependence policy; no one-dataset-per-idea rule is imposed. [Dwork et al.](https://proceedings.neurips.cc/paper_files/paper/2015/file/bad5f33780c42f2588878a9d07405083-Paper.pdf) motivate attention to adaptive feedback, but their reusable-holdout mechanisms are not adopted for market data.

A candidate revised after a robustness plot, failed confirmation or cost stress is a descendant with retained exposure. A preregistered diagnostic may legitimately inform the original frozen decision only as specified in that plan. Neither favorable sensitivity nor a simpler final rule converts a development finding into independent confirmation. All material changes and failed probes remain governed by D026; rollback restores configuration, not freshness.

### Choose methods for the declared question

| Method family | Potential role | Required limit or unresolved choice |
|---|---|---|
| Final held-out or forward assessment; nested evaluation of a procedure | Separate selection from assessment | Specify the evaluated object, actual access history and permissible fitting. Forward origin alone does not control many claims or repeated peeking. |
| Time-respecting splits and dependence-aware uncertainty | Match information available at decisions and the intended future-use question | Specify sampling units, outcome maturation, overlapping windows, common shocks, fitted preprocessing and any exclusion/gap rule. No universal gap length or walk-forward method. |
| Joint family tests or selection-aware resampling, including White's Reality Check when applicable | Assess a declared search relative to a benchmark | Define the candidate universe, target statistic and dependence assumptions. A final-model count or incomplete adaptive search is insufficient. |
| Deflated Sharpe Ratio (DSR) | A Sharpe-specific selection/non-normality diagnostic | Justify trial/dependence inputs and the return process. It is not a universal test of a binary, causal or mechanism claim. |
| Probability of Backtest Overfitting (PBO) with CSCV | Diagnose selection instability within a supplied candidate/performance matrix | Its target concerns an in-sample winner ranking below the out-of-sample median of candidates; it is not the probability that a scientific hypothesis is false. CSCV is not automatically a causal deployment simulation or the same procedure as CPCV. |
| Fixed-horizon or valid sequential evaluation | Control when a formal conclusion may be reached | Freeze the trigger or justified sequential procedure under DEF-021/022. Time-uniform intervals require their assumptions; they do not automatically solve selection across claims or create information. |

Time-series dependence does not imply a theorem banning all ordinary k-fold CV: [Bergmeir, Hyndman and Koo](https://robjhyndman.com/papers/cv-wp.pdf) establish a setting for purely autoregressive prediction with uncorrelated errors. That result does not authorize arbitrary shuffled trading-event folds. Select a design matching the project's information flow, estimand and dependence. When outcomes overlap training/evaluation boundaries, justify exclusions or other dependence treatment using actual information intervals; an arbitrary embargo does not certify validity.

Minimum relevant effects, uncertainty and attainable precision belong in the protocol before outcomes. Raw trade/bar counts and resampled paths do not equal independent information. A fixed-horizon non-significant result is not automatically a negative; a sequential decision needs a valid frozen rule. Engineering abandonment, budget exhaustion and scientific rejection retain different meanings. These distinctions permit useful early elimination while preserving inconclusive outcomes.

### Calibrate the selection process and preserve policy semantics

Under D025/D038/D049, distinguish developing the evaluator from assessing it. If null or planted-signal results guide repairs, retain that tuning and separately assess the frozen revision on appropriately separated calibration draws with reported uncertainty. Independent random seeds alone do not establish suitable null coverage or independence from benchmark-design choices. Keep ground truth out of discovery inputs; report which effect classes and nuisance regimes were exercised and which were not.

When claiming calibration of the adaptive process, exercise its relevant selection and feedback opportunities under the declared null, including fitted transformations, policy selection and any assessed generator adaptation. A fixed-family max-statistic answers a narrower question and cannot silently stand in for that process. Compare selected real results with selection-matched null results. [White](https://users.ssc.wisc.edu/~behansen/718/White2000.pdf) motivates search-aware inference; it does not supply a universal correction for unlimited adaptive LLM research. Technical conformance, error control under specified worlds, planted-effect detection and real-market usefulness remain distinct gates.

For Columns research, keep entry-known, evolving decision-time and completed-path data separate. Fit-dependent transformations retain their fitting sample and version as well as their input availability. Preserve the declared eligible population and exclusion reasons; executed trades alone may omit opportunities. Filtering trade A out of an export cannot reconstruct trade B that would have used its position slot. A policy change affecting positions, cash, signals, exits or costs needs faithful re-execution of those interactions; otherwise the result describes a subset of original trades only. An adapter unable to represent the change returns an explicit capability gap, not a tradable-performance claim.

### Academic source scope

Primary texts were inspected in the preceding research and refreshed on October 23, 2026 as indicated below. These sources support methodological distinctions, not proven efficacy of this LLM framework. No paper's numerical settings are adopted as project defaults.

| Primary source | Inspection and relevance | Transfer limit |
|---|---|---|
| [Cawley and Talbot, JMLR 2010](https://jmlr.org/papers/v11/cawley10a.html) | Publisher abstract: finite-sample model-selection criteria can themselves be overfit | Does not quantify this project's selection bias. |
| [Varma and Simon, BMC Bioinformatics 2006](https://linus.nci.nih.gov/techreport/Varma-Simon-CrossValid.pdf) | Abstract and previously inspected methods/results: nested selection and evaluation | Classification simulations are not a market calibration; no sample size or fold count transferred. |
| [Dwork et al., NeurIPS 2015](https://proceedings.neurips.cc/paper_files/paper/2015/file/bad5f33780c42f2588878a9d07405083-Paper.pdf) | Abstract/introduction and previously inspected adaptive-reuse discussion | Formal reusable-holdout algorithms have assumptions; none is implemented or automatically valid here. |
| [White, Econometrica 2000](https://users.ssc.wisc.edu/~behansen/718/White2000.pdf) | Introduction and previously inspected statistical setup: selection-aware benchmark testing | Search coverage and statistical assumptions must be justified for the actual process. |
| [Bergmeir, Hyndman and Koo, CSDA 2018; author preprint 2017](https://robjhyndman.com/papers/cv-wp.pdf) | Abstract/introduction: conditions for CV in autoregressive prediction | Neither a blanket ban on k-fold nor approval for arbitrary trading splits. |
| [Bailey and Lopez de Prado, DSR, 2014 author version](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf) | Abstract/introduction: selection and non-normality in Sharpe assessment | Specialized diagnostic; no universal evidence gate. |
| [Bailey et al., PBO, February 2015 author draft](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) | Abstract and previously inspected rank-based definition/CSCV | A candidate-selection diagnostic, not posterior truth or future-profit probability. |
| [Howard et al., Annals of Statistics 2021; arXiv v9](https://arxiv.org/abs/1810.08240v9) | Abstract and journal metadata: time-uniform confidence sequences under stated conditions | No full proof audit or market-specific sequential policy adopted. |

Ambroise and McLachlan's 2002 feature-selection paper was inspected during the preceding literature discussion, but its author-hosted PDF timed out during this refresh. The nested-selection explanation above uses the accessible Varma-Simon source; this refresh makes no new claim of access to the unavailable PDF.
