# Owned binary population stress worlds

`run_population_world` supplies the response-model generation prerequisite for the information study in research-contract/1.0 section 5.4. It consumes an owned development plan, its declared execution and matching information diagnostics. It does not run a power grid, select N_min, fit dependence parameters or calibrate the evaluator.

## Population and assumptions

The model takes `q` from the pooled eligible event rate and `w` from the fraction of all eligible instrument rows with a true condition. Unknown conditions remain in the baseline. For a declared signed effect `e`, it sets `p_true = q + e` and `p_other = q - w*e/(1-w)`. Consequently `w*p_true + (1-w)*p_other = q` and the conditional-minus-scope population contrast is exactly `e`. These identities refer to the hypothetical population, not each finite sample's observed ratio.

The controller derives scenarios from the owned effect profile: zero, delta and twice delta in the declared direction; nondirectional plans include both signs. It cannot accept an easier caller-supplied delta. Infeasible probabilities, missing groups, degenerate empirical rates and existing model-identification gaps remain `MODEL_OR_INFORMATION_GAP`. No clipping, deletion of unfavorable scenarios or adjustment of realized means occurs.

Dependence parameters are **explicit stress assumptions**, not fitted nuisance parameters or an empirical adequacy certificate:

- Joint categorical masks follow a stationary circular transition on the full source grid. At each step an exact Bernoulli draw with probability `1 / mask_mean_block` restarts at a uniform source index; otherwise the index advances. Instruments, unknown conditions and zero-eligible timestamps stay together.
- Common and instrument-specific latent states start uniformly on a shared integer lattice whose size is the least common multiple of all scenario probability denominators. Each persists with the declared probability or refreshes uniformly. Persistence must be below one.
- Each instrument/time independently selects the common latent with probability `common_share`. Thresholds are exact integer counts. Python's domain-separated MT19937 streams and integer rejection draws avoid binary-float threshold substitution; a finite PRNG is not proof of an ideal stochastic law.
- Latents and masks evolve at every timestamp, including entirely ineligible timestamps. The uniform marginals are independent of the mask, preserving the declared group probabilities under this model.

The homogeneous pooled rates do not preserve arbitrary instrument heterogeneity, raw-price dynamics, endogenous missingness or outcome overlap implied by an original AST. The nonnegative latent-persistence family does not cover general dependence laws. Empirical negative pair products are retained explicitly: they are neither clipped nor treated as proof of negative population dependence. Model adequacy and any later fitting/selection procedure require their own assessment before a scientific information target can be admitted.

## Synthetic cases and calendar

New model reports include `source_process_scope` (`source-process-scope/1`) and `source_identity_preservation`. The diagnostic compares exact ordered condition/outcome syntax, feature versions, literal spellings/units and catalog bindings with a uniform feature-time shift. For a match, `condition_equals_outcome_at_offset_bars = k` means `C_t = Y_(t+k)` on jointly observable values under valid bound reference-program semantics; the outcome horizon is included in `k`. This is conditional structural evidence, not independent program compilation or feature certification. Positive, zero and negative offsets are supported. Literal, feature, lag, NOT and existing binary operators are inspected; windows and other unsupported syntax conservatively remain NOT_ASSESSED. No algebraic rearrangement, commutation or feature alias is inferred.

The case request and exact case stream are hashed. Observations join the same instrument and exact 900-second timestamp, including known values on rows whose current outcome is not eligible. `partner_absent` means absent from the retained case grid, which can be a partial prefix; it does not establish absence from the original data. Present pairs fall into disjoint both-unobserved, condition-unobserved, outcome-unobserved or compared counts; compared pairs retain equal/unequal counts, with both-eligible comparisons separately counted. Zero observed comparisons supply no empirical confirmation. Neither a syntax match nor its absence establishes population adequacy. Missingness, availability cutoffs and intermediate-node row requirements can differ despite a shared mathematical value; no executable AST is rewritten.

When an identity is recognized, the current independent-mask response generator records its preservation as NOT_GUARANTEED. Otherwise preservation remains NOT_ASSESSED. The diagnostic does not change MODEL_SPECIFIED, rates, effects, draws, seeds, scientific readiness or the admissibility of declared estimator-only stress studies. It imposes no original-process identity requirement on individual stationary-bootstrap resamples. New report hashes and derived synthetic identifiers change; previous results continue to replay through their exact retained source, without rewriting old capsules. [Verification and the real development observation](../docs/reviews/implementation-2026-10-25/SOURCE_PROCESS_SCOPE_2026-10-26.md) distinguish this interpretation safeguard from a fitted market-process model.

Generated cases are explicitly **estimator-level synthetic responses and masks**. They use new synthetic candidate/data identities and synthetic feature programs, and record that the source AST was not executed. No market observations, certified raw features or faithful H_exec execution are claimed.

Every case retains the sampled source time index and categorical state in `simulation_mask`. A sampled source partition boundary becomes a missing response at an interior synthetic timestamp. A source outcome-data gap is also a missing response; a missing decision observation remains a data gap. At the actual final horizon, true-scope cases receive the synthetic calendar's partition-boundary state. This separates source missingness provenance from current maturity metadata.

`terminal_censored_cases` counts all true-scope cases relabeled by that artificial terminal calendar, including cases whose source outcome was already missing. It is not the count of otherwise eligible observations lost.

The target must contain more timestamps than the outcome horizon. All nonterminal positions have the same stationary mask marginal; calendar censoring is independent of masks and responses. Thus population q/w remain the declared row-weighted quantities, while finite realized counts and contrasts fluctuate. Calendar positions, instruments and resamples are not independent outer replications. This construction does not certify a raw process with the original horizon's overlap.

## Owned request and retention

The operator-only RPC accepts exactly `key`, `plan_id`, `execution_id`, `diagnostics_id`, `specification`, `scenario`, `time_rows`, `seed` and `limits`:

```json
{
  "key": "population-world-001",
  "plan_id": "<owned development plan>",
  "execution_id": "<declared development execution>",
  "diagnostics_id": "<matching owned diagnostics>",
  "specification": {
    "schema": "binary-population-spec/1",
    "mask_mean_block": 4,
    "persistence": {"numerator": "1", "denominator": "2"},
    "common_share": {"numerator": "1", "denominator": "2"},
    "rationale": "Explicit development stress assumptions; not fitted or validated."
  },
  "scenario": 2,
  "time_rows": 128,
  "seed": 2026102501,
  "limits": {"max_seconds": 120}
}
```

These example numbers are engineering inputs, not universal model defaults. A target has at most 100,000 instrument/time cases; the retained case stream is capped at 128 MiB. The generation plus verification deadline is explicitly bounded by 1,800 seconds. This per-operation bound is not the aggregate budget or continuation policy for a future multi-world study.

Before simulation, `population-world-input/1` retains the exact recipe, assigned effects, source/runtime, original case descriptor and inherited exposure. A separate isolated process generates the world; a second process recomputes the model and compares every generated case byte and result. `development-population-world/1` retains either the declared model gap or generated world, its case blob and replay identity. Same-key retries preserve the original request/source. Failures remain visible through existing bound-computation inspection. Reserved namespaces and creation-time checks prevent generic source writes or backdated context admission.

The model and world always carry `scientific_readiness: false`, `classification_permitted: false` and `n_min: null`. Assessment and corroboration data remain excluded. Existing full backup/restore includes their dependency/blob closure.

## Joint synthetic response families

`run_population_family` consumes the same owned development plan/execution/diagnostics and stress specification. Replace `scenario` with `components`, a list of two through eight `{id, scenario}` objects, and add a separate integer `bootstrap_seed` and exact rational `mc_noncoverage`. All other fields above remain required. Component IDs are distinct synthetic response identities, not different truths for the same original hypothesis. The number of components must equal the owned plan's `primary_count`; base block length, delta and direction also come from that plan. The request cannot override those settings. Effect indices refer to the full model's owned zero/boundary/alternative scenarios; infeasibility anywhere in that declared model remains a gap.

The bounded initial family profile uses one exact source report, hence one shared q, w, horizon, instrument grid and condition/missingness template. Each response can have its own declared effect. It generates one joint mask index and one common latent per timestamp, with response/instrument-specific individual latents and channel choices. Every latent advances on ineligible timestamps. Sorting response IDs and domain-separating their streams preserves trajectories when the input component order changes. Zero common share removes the common latent channel; shared masks can still induce dependence. Original ASTs, heterogeneous claim templates and price paths are not simulated.

Every component is consumed by the unchanged stationary-bootstrap calculator, with the actual family count and all 19,999 resamples per required block length. The same bootstrap seed on the identical grid yields the same sampled index paths across responses; it does not create additional outer replications. Cases and draws are retained with response IDs. One entire family vector counts as one outer world. Joint miscoverage is the union of misses; false support and boundary decisive errors inspect only the actual null and boundary components respectively. Detection remains separate per 2*delta component. An established error remains true if another member is unavailable; otherwise any required unknown member makes the union unavailable. No applicable component yields null. Information gaps give no decisive result and no coverage; model/technical failures remain unavailable.

Controller-owned `population-family-input/1` and `development-population-family/1` use the existing pre-computation source/input retention, interrupted retry, dependency recheck and fresh-process replay machinery. A retry keeps the original source. The aggregate generated case count across responses is at most 100,000 and the complete case/draw stream is capped at 128 MiB. Generation, all estimator calls and replay share the requested parent deadline, at most 1,800 seconds. Resource limits never shorten the required resample count. They are per-operation bounds, not a final-series aggregate budget. Private assessment/corroboration inputs remain denied. All results retain false scientific authority and null N_min.

## Next integration boundary

An additional [lag-linked binary law](LAG_LINKED_POPULATION.md) now preserves a recognized shifted source value identity through generated response histories. It has separate versioned model/specification schemas and exact finite-state joint initialization. Existing source/mask response behavior remains unchanged. The added law is another explicitly limited stress scenario, not automatic original-process adequacy or a replacement for unsupported free hypotheses.

The generated reference-shaped reports are consumed by the actual joint bootstrap and MC arithmetic. Such execution is not evidence of power or a calibrated information target. The [owned family-series controller](CALIBRATION.md#owned-joint-family-series) now precommits complete inventories and fresh final seed namespaces, applies aggregate resource/storage budgets, retains attempts and authenticates complete-denominator counts. The standalone family operation does not itself satisfy those series controls. Full actual calibration, practical resource feasibility, return models, heterogeneous claim-template laws and empirical model adequacy remain unfinished. No scientific acceptance, atomic freeze or genuine LLM research cycle is supplied by this generator alone.
