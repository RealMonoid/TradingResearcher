# Dependent-null model scope assessment

Date: October 26, 2026. Baseline: `58780bd58e92b99bcd3dff39176617b1b3a006e3`, published and verified before this continuation. This is a mathematical assessment and a proposed engineering continuation, not a production model or adopted calibration profile.

## Question and finding

Can the recognized identity `C_t = Y_(t-2)` and a zero condition-versus-scope effect justify an IID outcome null for calibration? No. A stationary finite-state counterexample preserves both while changing the long-run variance of the contrast's linearization score. This makes the [lag-linked model's](LAG_LINKED_POPULATION_2026-10-26.md) documented dependence limitation concrete; it does not invalidate that model as a declared limited stress case or demonstrate bootstrap failure.

Construct four independent stationary binary Markov chains, one per time phase modulo four. At its next observation a chain transitions with

```
P(Y_t=1 | Y_(t-4)=1) = q + (1-q)*rho
P(Y_t=1 | Y_(t-4)=0) = q*(1-rho)
C_t = Y_(t-2)
```

Strictly interior transition probabilities give a stationary finite Markov process. The chronological four-bit chain is irreducible and aperiodic: every target four-bit state can be reached in four steps with positive probability, and the all-zero state has a self-loop. Its stationary law is the product of four Bernoulli(q) marginals. C and Y use distinct independent phases, so `E[Y|C=1] - E[Y] = 0` for every allowed rho. The construction has fully known conditions and complete eligible outcomes; it assumes no market-data fit.

At this null, the population linearization score of the ratio contrast is `phi_t = (C_t-q)*(Y_t-q)/q`. Its point variance is `(1-q)^2`, unchanged across rho. Exact finite-state expectation gives `P^2 phi = rho*phi` and `E[phi_t phi_(t+1)] = 0`. Hence

```
Cov(phi_t, phi_(t+2k)) = (1-q)^2 * rho^k
Cov(phi_t, phi_(t+2k+1)) = 0
Long-run variance = (1-q)^2 * (1+rho)/(1-rho)
```

For rho -1/2, 0 and 1/2, the long-run-variance multipliers relative to the IID-outcome null are respectively 1/3, 1 and 3. This is not a finite-sample variance ratio for the estimator, a measured standard-error ratio, or a miscoverage estimate. Even at rho zero, overlapping score values need not be IID when q differs from one-half; here they are uncorrelated.

The [exact checker](verify_dependent_null_scope.py) enumerates all 16 states for q=1/2 and q=19/47 (the earlier development source's retained rate), checks stationary residuals and zero effect, verifies the two-step score identity in every state, and checks outcome/score moments at lags 0 through 12. These six fixed algebraic cases do not reuse market outcomes or simulate new worlds. [Results and check records](dependent-null-verification-2026-10-26.json) and the [independent review](dependent-null-independent-2026-10-26.json) retain the evidence.

## Small proposed continuation

A second-order law can vary dependence at a fixed assigned effect e:

```
r = e/(1-q)
alpha = (1-beta)*r
P(Y_t=1 | history) = q + alpha*(Y_(t-2)-q) + beta*(Y_(t-4)-q)
```

For each of two independent time phases, candidate consecutive-pair masses are `p11=q*(q+e)`, `p10=p01=q*(1-q-e)` and `p00=(1-q)^2+q*e`. Their product over the two phases satisfies the full four-bit stationarity equations whenever the required probabilities and masses are admissible. The conditional-minus-scope target is exactly e. Beta zero reduces to the existing lag-linked transition; e zero gives the dependent-null construction above.

The checker verifies strict-interior transitions, exact stationary residuals and the target across 18 explicitly chosen cells: q in {1/2,19/47}, e in {0,1/20,1/10}, beta in {-1/2,0,1/2}. These are feasibility examples, not a nuisance estimate, selected stress range or required universal defaults. In particular, the small positive transition 121/26320 in one cell warrants explicit treatment rather than silent clipping. Joint multiple-response/instrument initialization, masks, resource limits and integration remain unimplemented for this candidate. The existing solver's coordinate bound must not be silently stretched to a larger history state space.

## Conclusion, limits and next action

Preserving the one recognized temporal identity is insufficient to cover the relevant dependent-null variation. A future finite information/calibration profile should state which such processes it covers and why. Implementing and independently checking the bounded second-order extension is a concrete next engineering step; it does not itself establish market adequacy or admit a sample target. Boundary/alternative cases, masks, common shocks and all fixed final cohorts still require their existing checks. No observed negative moment is clipped or asserted to identify negative population dependence.

The simulation-design principle is supported by Morris, White and Crowther's primary tutorial: define the target, data-generating mechanisms and performance measures, and interpret findings within those mechanisms ([arXiv v3, sections 3 and 6](https://arxiv.org/html/1712.03198v3)). The counterexample and proposed formulas above are project derivations, not claims attributed to that paper. No new estimator, evidence threshold, scientific contract, model call or market interpretation is activated.

Changed files for this continuation are this assessment, its exact checker and evidence/review records, plus Current State and the progress register. The 113 passing runtime tests belong to the preceding implementation checkpoint; they are not counted again as new tests here. Production Python files remain byte-identical to the published baseline. Full calibration, a genuine mixed-provider research cycle, scientific admission/freeze, policy/AmiBroker and reporting remain unfinished.
