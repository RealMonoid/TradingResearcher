# Bounded exact compositions

Version: `bounded-exact-compositions/1.0`. Status: ACCEPTED November 1, 2026 (D097). This specifies the approved opt-in scalar `research-ast/4`; implementation qualification and actual research admission are separate.

## Approval and preserved source

Source: SESSION-2026-11-01-EXACT-COMPOSITIONS. The user answered question `call_8b9787d357e24ae6b8f5917b22cac043`:

> Vier Bausteine freigeben (empfohlen)

The question explicitly requested exact power, complete window product, complete window Boolean aggregation and outcome-only absolute value, with independent tests/review, unchanged original meaning and no additional budget. The [approval-time proposal](../reviews/adoption-exact-compositions-2026-11-01/approved-proposal.txt) retains the complete source bytes (SHA-256 `0c8a7a8963bfe3fd657798eb9a5478e9715b9ab7073a5b31a57eaa32d94420a6`). This direct reply approves that concrete proposal, not an automatic goal continuation.

## Scope and unchanged boundaries

Four reusable primitives extend the existing scalar reference language for independently qualified single-instrument development hypotheses. AST1/2 and fixed-pair AST3 keep their existing versions, meanings, source capsules and results. No cross-instrument selector, decision-time logarithm, bounded-real comparison, implicit unit algebra, numerical Boolean cast, fitted parameter, catalog of hypotheses, scientific classification, assessment access or capital authority is added.

Every hypothesis still requires its own faithful original-to-executable mapping, availability/feature/data/exposure qualification, independent meaning review and existing evaluation gates. A proposed shape is not an accepted H_exec. The [static shape check](../reviews/implementation-2026-10-25/inquiry-proposal-shape-check-2026-11-01.json) counted 130 condition nodes and 25 outcome nodes and tested only existing guards; it did not implement or certify these operators.

## Exact language

The program envelope remains exactly `schema`, `catalog_hash`, `expression`; the schema is `research-ast/4`. Preserve exact catalog binding, existing types/units, 900-second grid and required-input semantics. New operator fields are exact:

| Operator | Fields in addition to `op` | Meaning |
| --- | --- | --- |
| `integer_power` | `arg`, `exponent` | Exact rational power of a real dimensionless ratio. Exponent is an explicit integer from 1 through 1,000,000; Boolean, zero, negative and noninteger exponents are excluded. |
| `trailing_product` | `arg`, `bars` | Exact rational product over every slot of the complete declared positive causal window, including its evaluation slot. Real dimensionless ratio operands only; zero/negative factors retain ordinary product meaning. |
| `trailing_all` | `arg`, `bars` | Kleene Boolean AND over every slot of the complete declared positive causal window. False plus unknown is false; no implicit whole-condition unknown override. |
| `abs` | `arg` | Outcome-only absolute value of a real rational or rigorously enclosed real; preserve unit and missingness. |

Power/product operands must be exact rational expressions, not logarithmic/enclosed expressions. Only an explicit outcome caller may enable `abs` (the same outcome capability used for `ln`); decision callers cannot use either. Window/lag limits, 256-node/32-level limits, primitive budgets, 8,192-bit rational bounds and computation deadlines remain unchanged. Unsupported type/shape/meaning is a gap; a resource overrun is a retained `RESOURCE_GAP`, never a market result.

## Deterministic resource and window behavior

Power uses least-significant-bit binary exponentiation: start `result=1`, `factor=arg`; multiply result by factor on an odd remaining exponent, halve the remaining integer, and square factor only while bits remain. Charge the operator-node step, one primitive step before each bit iteration and one before each attempted multiplication, in addition to operand evaluation. Check reduced rational numerator/denominator sizes before and after every multiplication.

Both windows traverse oldest to newest and evaluate every required child, including after a known false, zero or unknown. Charge the operator-node step, one traversal/fold step before each slot and existing child evaluation charges. Product additionally charges every attempted multiplication of a known factor and checks each reduced intermediate; remember unknown factors while continuing the remaining traversal. A completed product with an unknown required factor is missing. Boolean aggregation preserves Kleene folding and records all dependencies even if the result is already false.

Do not reorder products to exploit later cancellation, skip a multiplication after zero or defer size checks until the final result. An excessive intermediate or exhausted budget stops before condition/outcome classification, even if an uncomputed final value might cancel to a smaller rational. No binary floating approximation replaces an exact decision comparison.

For an enclosure `[lo,hi]`, `abs` retains it when nonnegative, negates/reverses it when nonpositive, and returns `[0,max(-lo,hi)]` when it crosses zero. Preserve outward rational bounds and charge its node plus child evaluation. No interval can be silently collapsed to a midpoint.

## Required-input and mapping obligations

Coordinates do not require fabricated observations; raw feature reads require their exact rows and recorded availability. No skipped slot, filling, shortened window or data-dependent selection is permitted. Unknown/invalid dominance required by an original idea must be expressed in its complete mapped guard, such as `G(V,P)=(V AND P) OR ((NOT V) AND unknown)`. Temporal Boolean aggregation does not supply that guard automatically.

For the retained BTC idea, on every original valid positive high/low input, `ln(R0)<=sum(ln(Rk),k=1..32)/64` is exactly `R0**64<=product(Rk,k=1..32)`; the separate positive mean-log-range requirement is `product>1`. Preserve every original H/L/Q/B validity check, whole-condition unknown rule, Q1 boundary, cutoff, origin and complete baseline. Its outcome remains the original absolute endpoint log displacement at h=5. The static engineering tree or a signed/proxy outcome cannot substitute for independent actual formalization/review.

## Acceptance, actual use and rollback

Before dependent runtime use, independently check fixed/random rational cases, equality/domain boundaries, complete missing/invalid/late windows, false-plus-unknown guards, causal traces, parameter/type/unit/version rejection, numerical/step/node/depth bounds and deterministic cancellation/resource behavior. Check absolute log enclosures against an independent adequate-precision reference. Verify a complete original-idea mapping on synthetic histories and run affected legacy access/exposure/formalization/certification/replay checks. Preserve failed cases and expected results. These are qualification requirements, not executed-test claims.

Use a separately versioned opt-in implementation and complete contract transport to both formalizer and unchanged independent reviewer; never mutate a frozen epoch/profile. Preserve model, reasoning, full outputs and actual complete-input counting. Any future paid call requires its own actual native/source/grant/accounting admission inside the original shared USD5 limit; USD0.574585 remained at approval. This adoption creates no grant, retry, successor or additional money and promises no complete-cycle fit.

Rollback disables this version for future admission and revokes unused new allocations. Preserve original ideas, null formalization, all source/contracts/profiles, failed tests, outputs, exposure and charges; restore neither unseen history nor spent slots. Scientific classification, protected assessment, calibrated information/evaluation, atomic freeze and realistic policy economics retain their existing prerequisites.

Affected: D008/D026/D084/D089/D091/D094; research-contract sections 6/9/14; REQ-002/003/004/005/011/014/022/023/026/030; existing CMP-02/03/04/05/06/07/12. Approval is specification authority only, not implementation, model comprehension, scientific validity or economic usefulness.
