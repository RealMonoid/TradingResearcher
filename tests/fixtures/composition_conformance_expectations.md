# Independent static composition expectations

The fixed `composition-conformance-cases/1` bundle contains twelve accepted static
compilations and fourteen explicit rejections. It covers the extra binding driver;
it does not replace the already pinned expression, outcome or raw-feature cases.
All expected program types, units, feature closures, parameter-pointer lists and
window counts were assigned from the existing specifications and simple grid
arithmetic. No compiler, calculator, validator or existing TestCase was invoked
to produce an expected value. The author had already read the current binding
implementation while identifying the missing certification boundary; that prior
inspection is disclosed, not described as a blind implementation review.

## Fixed derivation

The ordinary universe [01:00,02:00) has four 15-minute decision instants per
instrument. A lag of L bars adds L prior bars; a trailing window of W bars adds
W-1 prior bars. Nested operators add along their path; alternative branches need
the maximum span, not the sum. A future outcome anchor H bars after the decision
offsets H bars of the outcome expression's lookback when choosing pre-decision
input rows. Therefore required warmup is the maximum of decision span and the
nonnegative outcome span minus H, multiplied by 900 seconds.

Lag 2 around a trailing mean of 3 needs four prior bars. At 01:00 this reaches
00:00, hence eight input rows through 02:00. If the snapshot begins at 00:30,
required warmup remains 3600 seconds, unavailable warmup is 1800 seconds, and six
rows may be loaded. Outcome lag 4 around a window of 4 needs seven bars before its
anchor. Horizon two leaves five pre-decision bars. At 01:30 this reaches 00:15;
nine rows reach the 02:30 exclusive end. Combining that outcome with four-bar
decision warmup still needs five bars, not nine. A horizon of nine leaves no
pre-decision outcome warmup. These calculations do not remove existing outcome
`REVIEW_REQUIRED`, partition-boundary or missing-value behavior.

Per-program feature sets are distinct from their combined union. The volume-scope
and price-condition case verifies their separate attribution. Program Boolean
units are null; a binary-probability contrast nevertheless uses `ratio`. Price
divided by same-unit lagged price yields ratio, and subtracting ratio one preserves
that unit. Literal and shift/window pointers name their exact positions in each
program. The explicit false-AND branch retains both its declared feature and lag:
static validation cannot drop branches based on potentially nondecisive values.

The typed-null literal has a known real/ratio type but no feature dependency; this
does not convert a missing outcome into an eligible observation. Two-instrument
cases preserve request ordering but sort the row-loader universe and multiply
grid counts by two. Exactly 50000 decision instants for two instruments meet the
100000-row bound; adding one pre-decision warmup instant requires 100002 rows and
must reject without truncation. Calendar strings are formatted using standard
UTC date arithmetic, not an implementation calculation.

## Harness and identity contract

Each case has a complete six-field `compile_payload` input. The synthetic
`data_manifest` contains the static universe projection consumed by that compiler;
it is not an admitted data snapshot or a claim about source rights/availability.
Candidates retain the existing H_exec field shape. Accepted-case parameter
origins are populated from the separately assigned expected pointer lists; the
bundle does not assert natural-language equivalence or genuine registry ownership.
Artifact aliases are fixed input strings for pure compilation only. A controller
integration must separately bind genuine immutable owned records.

Catalog/program/candidate hashes use the documented sorted compact JSON identity
encoding. Those hashes only bind inputs. The expected request maps the declared
input fields directly and copies the original programs without rewriting them.
The rest of each accepted expected object is a fixed independent oracle. Compare
all listed fields, including every program's complete metadata; checking only a
global feature union or self-consistent row count is insufficient.

Rejection cases name `Invalid` or `ExpressionGap` and, where fixed by the existing
expression/outcome interface, its exact gap code. Arbitrary exceptions, crashes,
timeouts or missing cases are not successful expected rejections. Validations must
exercise every named case and preserve the fixture bytes. These cases supplement
rather than weaken the existing fixed primitive resource and temporal checks.

## Certification boundary

A passing fixed driver suite establishes only its exercised static composition
contract under research-contract/1.0 section 14. Separately recompiling the exact
candidate with that same retained package checks binding/replay, not an independent
oracle. A genuine host certificate must also bind the original compiled object,
the exact feature definitions/certificate, reference certificate, binding package,
validator and this unchanged fixture; check their current usable dependencies and
retain interrupted/failing attempts. No row or outcome access is needed here.

Composition conformance must not infer H_idea/H_exec meaning equivalence, data/PIT
truth, rights, training exposure, dependence adequacy, empirical support, complete
scientific readiness or capital authority. Unknown/new primitive meanings stay a
gap for review. Existing numerical, time, missingness and estimator definitions
are unchanged. Unsupported original ideas and all historical failures remain.
