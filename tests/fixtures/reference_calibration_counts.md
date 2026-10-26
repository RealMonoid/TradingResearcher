# Independent calibration count expectations

Authored October 25, 2026 by the independent `information_review` agent before
`trading_researcher/calibration.py` existed. The JSON fixture was derived without
importing project code, an implementation test helper, or a probability package.
Keep these expected bytes fixed when testing the later implementation.

The governing policy is [research-contract/1.0, section 11](../../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#11-open-11-finite-success-and-continuation-criteria),
adopted in D081. The existing [information-study implementation note](../../docs/reviews/implementation-2026-10-25/INFORMATION_STUDY_IMPLEMENTATION.md#exact-outer-uncertainty)
distinguishes the one-sided calibration checks from pointwise two-sided reporting
and the separate 80% design target. Its NIST/SciPy references provide background;
this fixture uses direct exact arithmetic, not output copied from those libraries.
A fresh attempt to retrieve those two public reference pages did not return before
the request was terminated. No new external-source verification is claimed here.

For `X ~ Binomial(n, p)`, the lower one-sided 95% endpoint solves
`P_p(X >= k) = 1/20`; the upper endpoint solves `P_p(X <= k) = 1/20`.
The lower endpoint is zero at `k=0`; the upper endpoint is one at `k=n`.
For a rational trial value `p=a/b`, each tail is evaluated directly as
`sum(comb(n,j) * a**j * (b-a)**(n-j)) / b**n`, over its inclusive index range.
Integer comparisons against `1/20` locate adjacent endpoints on the `2**40`
dyadic grid. Both endpoint inequalities are checked after the search. For a lower
bound the outward endpoint is the smaller bracket endpoint; for an upper bound
it is the larger endpoint. Decimal strings are displays only.

Additional checks use exact `n=1` roots `1/20` and `19/20`, complementary
`n=10,k=5` endpoints, and direct integer tail comparisons at `p=1/10` and
`p=7/10`. These comparisons are independent of rounded endpoint displays.

At 256 complete, distinct outer worlds:

| Count | Check | Expected result |
|---|---|---|
| 17 errors | Upper 95% bound <= 0.10 | Pass; bound approximately 0.09794542185 |
| 18 errors | Upper 95% bound <= 0.10 | Fail; bound approximately 0.10248544026 |
| 191 detections | Lower 95% bound >= 0.70 | Fail; bound approximately 0.69738835517 |
| 192 detections | Lower 95% bound >= 0.70 | Pass; bound approximately 0.70148733978 |
| 204 detections | Point rate >= 0.80 | Fail; exact rate 51/64 |
| 205 detections | Point rate >= 0.80 | Pass; exact rate 205/256 |

Both 204 and 205 detections meet the separate lower-bound calibration criterion.
An 80% point design target is not an 80% lower confidence bound.

At the true decision boundary, the event is an erroneous decisive classification:
false support **or** false negative. Seventeen of each on disjoint worlds yields
34 union events and fails the error tolerance even though each tail separately
would pass. For joint miscoverage, any required interval missing its own truth
is one event for that joint simulation; claims and instruments are not separate
outer observations. Do not pool different declared stress-world laws to conceal
a failing cohort.

One missing or unavailable event among 256 planned worlds yields `NOT_ASSESSED`,
including when all 255 known flags are false. The eventual owned runner must
distinguish known scientific abstention from technical or unknown outcomes and
authenticate the supplied event definitions. This arithmetic fixture does not
choose that treatment or certify freshness, independent generation, model
adequacy, a scientific evaluator, or a simultaneous probability guarantee across
all cohorts. Applicability assertions remain declarations requiring later review.

Initial JSON SHA256:
`c1c7d41e24b20c4b3c170e7051fb597c1e6b761712274c287d008c485ac27ae9`.
