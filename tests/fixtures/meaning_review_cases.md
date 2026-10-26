# Independent meaning-review fixtures

Authored by the independent reviewer on October 25, 2026, before any model was
shown these eight cases. This is a fixed test oracle, not a provider evaluation
result, natural-language proof, feature certificate, or scientific approval.

The frozen [JSON fixture](meaning_review_cases.json) has SHA-256:

`be419900653305eb986cccb8c40ff4e1779bef1cf6d478e0b8ea49c166a88d09`

The candidate shape, catalog and identity aliases reuse
[reference_binding_cases.json](reference_binding_cases.json). Its short original
and synthetic formalizer equivalence assertion are **not** used as evidence of
semantic fidelity. The new complete original independently specifies direction,
instrument, inclusive start and exclusive end, literal-true scope, current-close
threshold, exact future anchor, quantity and units, whole-scope denominator,
equal-row weighting, unknown conditions, missing outcomes, maturity,
availability assumptions and preexisting parameter origins.

The supplied close meaning describes the existing raw Binance spot feature:
exact decimal close-field projection, anchored at the expected exclusive bar
end. Zero publication delay is an explicit scenario assumption. Historical
publication times remain unknown. These descriptions do not certify data or
grant access to a real snapshot. The `fixture:*` references are aliases to be
bound explicitly to retained owned artifacts by a future test harness.

| Case | Predetermined judgment | Essential reason |
|---|---|---|
| complete-faithful | faithful | Every candidate semantic choice is stated in the original. |
| double-negation-equivalent | faithful | NOT NOT preserves true, false and unknown. |
| changed-horizon | different | Two bars contradict the stated one-bar anchor. |
| changed-comparator | different | A complement is not the stated whole scope. |
| changed-direction | different | Negative contradicts the stated positive direction. |
| unknown-condition-denominator-exclusion | different | Unknown conditions must remain in the whole-scope denominator. |
| underspecified-original | uncertain | The original does not determine several added choices. |
| unsupported-question-retained-gap | faithful | The original expressly requests retaining no executable proxy until missing data and definitions exist. |

The last case is faithful **gap retention**, not verified equivalence of an
executable hypothesis. Its target remains `RETAINED_GAP`; the independent-review
prerequisite for a structurally executable candidate is not satisfied.

The deliberately supplied formalizer reports claim equivalence even in mutated
cases. Their job is to test independent comparison, not to provide ground truth.
The underspecified original can pass the existing structural assertion checker
while still requiring an uncertain meaning judgment. Conversely, complement
and missingness mutations can already produce structural capability gaps; the
review should still identify their explicit changes in meaning.

## Exact counterexample

The JSON includes an independent abstract table of eligible outcome quantities
in USDT/BTC. It is not a replay of the reference snapshot's three decision rows.

| Condition | Outcome |
|---|---:|
| true | 102 |
| true | 104 |
| false | 97 |
| unknown | 101 |

The conditional mean is `(102 + 104) / 2 = 103`. The required whole-scope mean is
`404 / 4 = 101`. Incorrectly dropping the unknown-condition row gives
`303 / 3 = 101` as well. Both observed contrasts are exactly `2`, although the
denominators and policy meanings differ.

Change only the unknown-condition outcome to `109`: the required whole-scope
mean is now `412 / 4 = 103`, so the original contrast is `0`; the mutant still
returns `2`. Both examples were computed and asserted with Python's exact
`fractions.Fraction`, independently of the project estimator. Agreement on one
observed answer is not evidence that two meanings are equivalent.

## Use and preservation

Freeze and record the fixture hashes before model execution. Supply the model
only the original, candidate or retained gap, applicable feature descriptions
and the versioned substantive review protocol. Withhold expected labels,
expected reasons, case IDs, mutation descriptions and counterexample answer
keys. Keep all planned cases, refusals, malformed responses, failures and
disagreements in the evaluation report. Do not alter these expectations after
seeing a response or report only favorable retries.

This finite set establishes no universal accuracy threshold. It does not
authorize inference spending. A later actual-model check is a separate retained
observation and must preserve original epoch budgets and invocation provenance.

Authority: [D002 and the decision register](../../docs/architecture/02_DECISION_REGISTER.md#d002--separate-h_idea-and-h_exec-retain-unexecutable-ideas),
[contract section 4](../../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#4-open-04-typed-expressions-and-explicit-estimands),
[section 11](../../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#11-open-11-finite-success-and-continuation-criteria)
and [section 14](../../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#14-open-14-automatic-certification-within-an-approved-envelope).
These fixtures implement checks within existing meanings; they do not approve
new meanings or weaken any remaining freeze prerequisite.
