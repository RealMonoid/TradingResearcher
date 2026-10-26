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

## Next integration boundary

The generated reference-shaped case report can be consumed by the actual joint bootstrap and MC arithmetic. Such compatibility is not evidence of power or a calibrated information target. A complete study still must precommit the finite target/scenario/world/seed family, aggregate resource/storage budget, all failure denominators and candidate selection rule; retain every result; and keep final calibration draws distinct. Return models and coherent joint claim-family worlds remain separate capabilities. No scientific acceptance, atomic freeze or genuine LLM research cycle is supplied by this generator alone.
