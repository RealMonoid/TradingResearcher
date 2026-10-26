# Independent information diagnostic expectations

Authored October 25, 2026 by the independent information reviewer before reading the new diagnostic implementation. The adjacent JSON fixture has SHA-256 `e2b8233b7b8ed1917f9392eb0c989279837f88219843371f35740908ccbb6b6f`. Expected values are fixed arithmetic oracles, not outputs copied from the new implementation. Do not revise them to make an implementation pass.

## Scope and construction

The six-time, two-instrument hand report tests report-layer statistics. Its eligible cases preserve valid outcome-anchor, availability and interval metadata from the existing reference materializer. Its `DATA_GAP`, `OUTCOME_MISSING` and `PARTITION_BOUNDARY` cases retain those actual materializer states. The combined hand table is not a claim that one raw history generates it: removing the decision row at t2 also makes the preceding horizon-1 outcome unavailable. A separate `six_time_raw_coherent` fixture supplies the actual catalog/rows and complete, unedited materializer output for that case. Neither fixture certifies source truth or market behavior.

| Time | A condition/outcome | B condition/outcome |
|---|---|---|
| 0 | true / 1 | false / 0 |
| 1 | unknown / 1 | true / 0 |
| 2 | DATA_GAP | DATA_GAP |
| 3 | false / 0 | true / 1 |
| 4 | true / 0 | OUTCOME_MISSING |
| 5 | PARTITION_BOUNDARY | PARTITION_BOUNDARY |

The hand case has seven eligible observations and three events: `q=3/7`, `w=4/7`, conditioned mean `1/2`, contrast `1/14`. True, false and unknown counts are 4, 2 and 1, with event sums 2, 0 and 1. Unknown C stays in the scope baseline. A has rate `1/2`; B has rate `1/3`. Per-instrument effects are 0 and `1/6`; their unweighted mean `1/12` is not the pooled contrast `1/14`.

## Exact full-grid diagnostics

Use integer time contributions `(N,S,C,Z)` for eligible count, outcome sum, true-condition count and true-condition outcome sum. The sequences are `N=[2,2,0,2,1,0]`, `S=[1,1,0,1,0,0]`, `C=[1,1,0,1,1,0]`, and `Z=[1,0,0,1,0,0]`. Empty times remain grid positions. No unobserved outcome is replaced with an observed zero.

With T=6, the plug-in contrast-score contribution is `g_t=T*(Z_t-muC*C_t)/totalC-T*(S_t-q*N_t)/totalN`. Its exact values are `[123,-171,0,123,-75,0]/196`, summing to zero. For a full-grid series x, lag k uses the global full-grid mean and exactly T-k noncircular products. The score moments at lags 0, 1 and 2 are `5427/19208`, `-15129/96040` and `-21033/153664`. Lag 6 has no pairs and therefore null, not zero. This score is a descriptive diagnostic, not a normal-power substitute or calibrated information bound.

## Observed-outcome paired products

Per-instrument outcome products use only pairs with eligible observed outcomes at both grid positions. Center each factor at that instrument's full eligible-outcome marginal rate. Report pair counts and pair means; these are fixed-marginal-centered products, not generally pairwise-centered covariances or certified correlations.

For A, lag 1 has two pairs and product `1/4`; lag 2 has one pair and product `-1/4`. Compressing the missing grid slot would incorrectly give lag-1 product `1/12`. B lag 1 has one pair and product `1/9`; compressing its eligible sequence would incorrectly give `-1/18`. At common time A/B have three pairs, pair means `2/3` and `1/3`, and centered product `-2/9`. These observations do not identify a latent common-shock parameter or prove stationarity/independence.

The coherent raw-row case has five eligible rows, `q=2/5`, `w=3/5`, conditioned mean `2/3` and contrast `4/15`. Its score is `[32,0,0,32,-64,0]/75`. A lag 1 has one pair and product `1/9`; B lag 1 has no pairs. The A/B common-time product is `-1/4` from two pairs.

## Gaps and degeneracy

The no-true-condition variant keeps the available seven scope observations, rates, masks and outcome diagnostics, but has no conditioned score. It does not invent a denominator or return a scientific negative. The all-zero binary variant has observed rate and score zero; this does not identify a degenerate population or adequate information. Noneligible runs must remain labeled separately from missing-data runs because partition boundaries and scope exclusions have different causes.

These fixtures establish exact arithmetic expectations only. They do not provide a model-adequacy judgment, automatic block length, minimum sample target, simulation power, calibration result, independent-market evidence or deployment authority.
