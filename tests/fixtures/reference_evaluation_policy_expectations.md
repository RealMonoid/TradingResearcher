# Independent historical-batch policy expectations

Version: reference-evaluation-policy-cases/1. Authored October 25, 2026, before inspecting any implementation of the new plan, allocation, freeze or evaluation-policy slice.

## Purpose and authority

The investigation asks which decisions already follow from the approved contract, which facts remain required run inputs, and where software must preserve a review gap. It does not ask whether a particular market claim is true. The fixed JSON bundle contains 91 format-neutral expectations derived from research-contract/1.0 sections 5, 12 and 14, with interface context from the Implementation Blueprint. The preserved approved proposal was checked where endpoint wording mattered. The bundle records exact source hashes at authoring time; later descriptive blueprint edits do not retroactively alter that provenance.

The existing formalization and binding modules were read only as interface context. No new policy implementation supplied an expected value. Existing expression, outcome, Binance, feature and binding fixtures were not changed. Small rational arithmetic is hand-derived below. These expectations are not a statistical calibration experiment, scientific certificate, market result, freeze authorization, proof of historical availability or natural-language equivalence test.

Authoritative sources:

- [Research contract, section 5](../../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#5-open-05-test-policy-useful-negatives-and-information-limits): fixed inference, interval rules, effect profiles, dependence dispatch and information limits.
- [Research contract, section 12](../../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#12-open-12-confirmation-allocation-and-feedback-release): full-family allocation and batch release.
- [Research contract, section 14](../../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#14-open-14-automatic-certification-within-an-approved-envelope): implementation certification versus scientific meaning.
- [Blueprint record fields](../../docs/architecture/09_IMPLEMENTATION_BLUEPRINT.md#required-record-fields-before-the-first-real-evaluation) and [interface bindings](../../docs/architecture/09_IMPLEMENTATION_BLUEPRINT.md#research-contract10-interface-bindings): immutable plan and manifest closure.
- [Preserved approved proposal](../../docs/reviews/RETAIL_RESEARCH_CONTRACT_PROPOSAL_2026-10-23.md): same directional and nondirectional wording, without a conflicting nondirectional endpoint exception.

## Fixture interface and coverage

Each case contains `name`, `operation`, `input`, `expected`, `source_sections` and `reason`. Every rational is an object with decimal-string `numerator` and positive `denominator`; all expected fractions are reduced. The exact strings are a fixture transport convention, not a new scientific definition. The harness may map these inputs onto a concrete versioned API but may not change expected decisions or arithmetic to fit the implementation. Extra output metadata may be checked separately.

| Operation | Cases | Meaning |
|---|---:|---|
| classify_interval | 26 | Directional sign reversal, strict relevance boundaries, nondirectional containment and invalid inputs |
| family_budget | 12 | All m from one through eight, exact marginal and tail probabilities, invalid family sizes |
| block_lengths | 12 | Half/base/double, ceiling, horizon floor, deduplication and invalid bases |
| profile_membership | 14 | Boolean probability, certified single-symbol 24h simple return, incompatible or mislabeled targets |
| bootstrap_completeness | 6 | Exactly 19,999 attempts for every required length, no undefined-draw discard or replacement |
| basic_interval | 2 | Linear quantile ranks and reflected basic-bootstrap arithmetic |
| enclosing_interval | 2 | Prespecified sensitivity enclosure and a missing required interval |
| classification_readiness | 1 | Established Monte Carlo instability yields inconclusive without selective reseeding |
| release_policy | 6 | Fixed trigger, complete batch and qualified technical termination |
| allocation_invariant | 10 | Frozen membership, full statistical family, no budget refund, exact duplicates and separate resource decisions |

Status names such as `SUPPORTED_INITIAL` are canonical scientific outcomes only under the case's express assumption that an already valid interval and every other admission gate exist. They do not authorize actual classification. Boolean predicates such as `accepted`, `eligible` or `scientific_outputs_releasable` are fixture-local assertions; they are not new lifecycle states or host-issued certificates. An invalid-input case requires rejection rather than a particular Python exception spelling.

## Hand-derived decision boundaries

For a directional claim, the fixture supplies an effect interval `[L,U]`. Positive direction gives theta interval `[L,U]`; negative direction gives `[-U,-L]`, reversing endpoints. With delta = 1/20, `[3/50,2/25]` supports the positive claim, `[1/50,1/25]` is negative for an effect of at least the claimed practical magnitude, and either bound equal to 1/20 is inconclusive under the explicit directional rule. A negative-direction interval `[-2/25,-3/50]` becomes `[3/50,2/25]` and supports the negative claim. No calculation treats a practical negative as proof of exact zero.

For a nondirectional claim, support means the entire interval lies strictly above delta or strictly below -delta. The contract separately names the closed region `[-delta, delta]` for a negative. Thus containment is `L >= -delta` and `U <= delta`, including equality. The full region and singleton endpoints are contained and negative; an interval touching an endpoint from outside is neither contained nor wholly outside, so remains inconclusive. This follows the explicitly closed set in the nondirectional paragraph. The equality-is-inconclusive clause is scoped to the preceding directional paragraph and is not silently extended to a different asserted set of effects. The approved proposal has the same wording. No contradictory authoritative rule was found, so this is a documented derivation rather than a new user decision.

Claim kind must be frozen. The endpoint difference is not permission to switch a directional claim to nondirectional after seeing its interval. Superiority, noninferiority and other equivalence contracts require their own explicit effect-set specification; the invalid `equivalence` direction fixture does not reject such ideas from the framework.

## Error allocation and dependence arithmetic

The family noncoverage is 1/20. For m = 1 through 8 the marginal values are respectively 1/20, 1/40, 1/60, 1/80, 1/100, 1/120, 1/140 and 1/160. Each two-sided tail receives half the marginal value. These values belong to the frozen full batch for the common decision, including its primary subgroups, interactions or policies. Topic labels do not create additional error budgets. Shared observations do not by themselves violate this union-bound policy; valid marginal coverage and the declared dependence design remain prerequisites. Neither asymptotic intervals nor these arithmetic checks establish exact finite-sample family control.

Block lengths are observation-time counts, not independent trade counts. If h is the largest overlapping outcome horizon and b the justified integer base, require b >= h and evaluate the distinct values `max(h, ceil(b/2))`, b and 2b. Examples: h=1,b=5 gives [3,5,10]; h=3,b=3 gives [3,6]; h=96,b=97 gives [96,97,194]; h=96,b=193 gives [97,193,386]. The 96-bar daily horizon follows 96*900=86,400 seconds. Passing these arithmetic cases does not supply a development-derived block-length rationale or verify stationarity.

For the first arithmetic-only bootstrap case, B=5 and marginal noncoverage 1/20 give probabilities 1/40 and 39/40, and zero-based ranks 1/10 and 39/10. Interpolating the sorted replicates [-0.1,0,0.1,0.2,0.3] gives quantiles -0.09 and 0.29. With estimate 0.1, the reflected interval is [0.2-0.29,0.2-(-0.09)] = [-0.09,0.29]. The second case has estimate0.2, quantiles0.01/0.58 and reflected interval[-0.18,0.39], demonstrating why the basic interval is not the percentile interval. These five-replicate examples verify a mathematical primitive only. A real assessment still requires 19,999 resamples per distinct sensitivity case and its separately certified implementation.

Any undefined required conditional mean prevents inferential classification. A run with 19,998 defined draws and one undefined draw cannot delete the latter, refill until 19,999 successes, or claim the remaining empirical distribution as its original procedure. Descriptive estimates and an information gap remain. Successful count checking only permits the next interval-construction check; it is not enough for a decisive outcome. Sensitivity enclosures use the minimum lower and maximum upper endpoint. Missing intervals and an established Monte Carlo instability diagnostic cannot be hidden by selecting a favorable length or reseeding. The fixtures deliberately do not invent an instability threshold or PRNG specification.

## Effect-profile membership is not a label check

Five percentage points is exactly 1/20 of a probability, not five percent of the current base rate. The binary profile requires the already supported Boolean outcome, dimensionless ratio estimand and canonical condition-minus-whole-scope target. The contract imposes no universal 24h horizon on this binary target. A caller cannot relabel real output as Boolean.

Ten basis points is exactly 1/1000 of a return. The bounded implementation target represented here is the same instrument's certified raw close at the 24h future anchor divided by its raw close 96 bars earlier, minus one, under the existing 900-second grid. It must bind the actual feature definition; a string ending in `close` is insufficient. Both BTCUSDT and ETHUSDT have separate symbol-specific price units. A volume ratio with identical AST shape and ratio units is not a price return. A wrong lag, cross-symbol denominator, price level or 23h45m horizon also does not qualify. A generator-selected smaller delta must not be substituted for the assigned profile.

The exact AST recognized in these cases is a bounded capability, not the sole mathematically possible representation of a simple return and not a universal definition of all returns. Algebraically equivalent representations can be supported through independent conformance within unchanged semantics. Unsupported log returns, financing-adjusted returns, policy profit or different economically meaningful targets retain their actual meanings and request an appropriate profile; they are not silently rewritten. Recognition does not prove that this target faithfully formalizes the original natural-language claim.

The fixture field `verified_feature_definitions` stands for an already authenticated, immutable definition binding supplied to a pure predicate. It is not permission for a worker to submit a dictionary and acquire certification. Integration must separately verify certificate ownership, exact snapshot/definition/package identities, retained-source integrity, applicable exposure and authorized data access. Known raw-data availability, assumptions and outcome maturity remain separate; these fixtures do not convert the current explicit delay scenario into historical PIT truth.

## Independent semantic review and freeze boundary

The current formalization boundary checks that a model declares equivalence, maps all original text to existing candidate paths and declares no differences. Those checks preserve claims about meaning; they do not judge whether the interpretations are true. The bound computation path deliberately retains that qualification. Replaying the same formalizer assertions in another operating-system process does not create an independent semantic judgment.

A meaningful independent review must inspect the exact retained H_idea, H_exec, mapping segments and definitions, and record the reviewer's identity/version, sources, own reasoning summary, added or omitted assumptions, conflicts and disposition. The reviewer must actually be distinct from self-certification by the author and have no protected assessment outcomes. Different provider names are not required and would not by themselves establish independence. The host can deterministically authenticate the review, enforce the role/context boundary, bind exact hashes and reject incomplete, ambiguous or mismatched records. Its acceptance represents a qualified independent semantic assertion, not a mathematical proof of arbitrary natural-language equivalence, an empirical verdict or permission to introduce new scientific meaning.

Clear faithful formalizations and compositions within the existing approved envelope do not require a manual user click for each idea. Material new primitive meaning, language/time semantics, estimands, evidence/exposure rules or material generator policy still require D008/D026 approval. Uncertain envelope membership is a retained review gap. An autonomous reviewer can later perform the ordinary semantic review through the bounded model interface; merely implementing its record type cannot count as having run it.

Before real freeze, the host must bind the complete immutable claim/plan/dependency/data/exposure closure, genuine semantic review, applicable feature/composition checks, valid evaluator conformance/calibration, development-only selection and nuisance inputs, justified information/precision plan, exact randomization and numerical policy, fixed trigger, family reservation and release policy. Freeze/trial/allocation commit atomically with idempotency and no partial authority. A syntactically valid plan or reserved draft does not grant scientific readiness or protected-outcome access. Attempts, technical failures, unselected ideas and gaps remain retained.

The release fixtures prohibit effects, intervals, ranks and pass/fail feedback before the declared complete fixed-batch boundary. A pre-frozen technical-failure policy may terminate and report technical status, but may not turn partial successes into opportunistic scientific rankings. A resource STOP can coexist with a scientifically inconclusive precision-limited result. It does not mean falsification and does not force a forward-data wait. Separate primary and corroboration batches do not automatically yield a combined campaign-wide five-percent claim.

## Required choices versus engineering work

No additional user decision was identified for the pure rules covered by these fixtures. The remaining concrete block length, development diagnostics, PRNG/version/seed, information target, calibration worlds and numerical controls are required pre-assessment run inputs and validation work under the adopted contract. They cannot be invented from protected outcomes or replaced by unexplained defaults, but their existence is not a reason to stop ordinary implementation and ask the user to design the estimator.

Actual approval is needed if work introduces scientific meaning outside the envelope, changes the admitted effect set or error policy, or asks for live capital. An unresolved interpretation in a particular H_idea requires review of that idea, rather than a blanket framework halt. Missing cost, data-rights, availability or model-input facts remain factual readiness gaps. Paid-model currency authorization and secret provisioning are separate practical inputs, not evidence rules.

This bundle leaves the bootstrap implementation, final calibration, independent semantic model execution, actual protected data authorization, transaction recovery and real historical research run unverified. Follow-on tests should cover those boundaries against the fixed expectations. No broad whole-framework verdict is implied.
