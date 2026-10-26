# Reference expression contract: research-ast/1

Implementation scope: the approved arithmetic, Boolean, versioned feature, lag and trailing-window semantics in [research-contract/1.0 section 4](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#4-open-04-typed-expressions-and-explicit-estimands). This is a bounded reference calculator for independently supplied values. It is not a hypothesis catalog, feature certification, faithful natural-language translation, scientific freeze, estimator, or evidence classification. Unsupported meaning remains a typed gap.

The input program has exactly `schema` (`research-ast/1`), `catalog_hash` (the existing canonical JSON SHA-256 of the supplied catalog), and `expression`. A catalog maps explicit versioned identifiers such as `close@1` to exactly `type` and `unit`. This slice supports `real` with a nonempty unit string, and `boolean` with null unit. `ratio` denotes dimensionless numbers. Other scalar/series types remain capability gaps.

Rows are ordered strictly by `(time, instrument)`, with unique keys. `time` is an observation instant in UTC epoch seconds, aligned to the pilot 900-second grid; it is not a claimed source-availability timestamp. A row contains exactly `time`, `instrument`, and `features`. Each feature sample contains exactly `value` and `available_at`. Real inputs are bounded plain decimal strings; Boolean inputs are true/false. A null value is missing. `available_at` is UTC epoch seconds; a sample unavailable at the current decision instant becomes missing. Supplied timestamps/values are not thereby validated as truthful market provenance. Revisions must be supplied as separate snapshots; this calculator cannot reconstruct omitted vintage history.

`ReferenceEngine(catalog, rows).evaluate(program, index)` returns exactly `type`, `unit`, `value`, and `missing`. A present real is an exact rational pair of decimal integer strings (`numerator`, positive `denominator`); no binary-float or rounding default is introduced. A present Boolean remains Boolean. Missing has null value and a reason string. Type errors, unknown semantics and invalid data raise `ExpressionGap` with a stable `code` and message. Existing input programs and rows are not changed.

| Node | Exact fields beyond `op` | Meaning |
|---|---|---|
| `literal` | `type`, `unit`, `value` | Real plain decimal or Boolean, including typed null |
| `feature` | `ref` | Supplied versioned feature at this instrument/time |
| `add`, `sub` | `left`, `right` | Real operands with identical units |
| `mul` | `left`, `right` | At least one operand dimensionless; preserve the other's unit |
| `div` | `left`, `right` | Same units yield ratio; dimensionless denominator preserves numerator unit; zero yields missing |
| `lt`, `le`, `gt`, `ge`, `eq` | `left`, `right` | Identical scalar types/units; ordered comparisons require real operands |
| `and`, `or` | `left`, `right` | Three-valued Boolean logic: false AND unknown is false; true OR unknown is true |
| `not` | `arg` | Negate Boolean; unknown stays unknown |
| `lag` | `arg`, `bars` | Nonnegative integer grid lag within the same instrument; absent exact timestamp is missing |
| `trailing_mean` | `arg`, `bars` | Positive integer number of grid observations including the current one; require the complete window and all values |

Every node is checked before calculation, including branches whose Boolean value would allow short circuiting. Negative lags, future/outcome nodes as decision inputs, unknown operators, invalid units and missing feature definitions cannot hide in an unused branch. Time selection never substitutes the previous available row for a missing grid observation. Feature availability is checked against the original decision instant, including for historical lookups. There is no cross-instrument lag/window traversal.

Ordinary arithmetic and comparisons preserve the first missing operand's reason, left before right. Logical AND/OR/NOT use `unknown_boolean` when their truth value is undetermined. An incomplete trailing window uses `incomplete_window`. Unsupported unit combinations produce `TYPE_GAP`, while future/outcome access produces `TEMPORAL_GAP` even in an unused branch. These codes explain an unavailable calculation; none is an empirical negative.

General compound-unit algebra, forward-outcome calculation, estimators, UTC/duration/event-set nodes and adaptive state machines are not executable in this slice. Their absence does not reject the original idea. There is no generated code execution, file/network access or plug-in callback in an expression. Programs are limited to 256 nodes/32 levels, shifts/windows to 1,000,000 bars, datasets to 100,000 rows, and evaluation to 1,000,000 primitive steps. Rational numerators and denominators are bounded to 8,192 bits. Resource failure is a gap, never a market conclusion.

Independent hand-calculated fixtures must be fixed separately from the implementation before claiming conformance. Passing them can establish only this arithmetic/time/missingness interface. Activation as a certified research feature, integration with H_idea/H_exec and allocation/freeze, and use of any resulting measurement in scientific inference remain separate gates.
