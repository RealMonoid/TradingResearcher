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
