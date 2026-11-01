# Retained breakout idea: independent composition checks

This optional package implements the original-specific deterministic checks for
idea `4abce1d5187d7fd229b52dd9a00e0beca8ee3947e9a1470dbc5351ff78c8872a`.
It uses the approved [fixed-pair semantics](../../docs/architecture/23_PAIRED_DEVELOPMENT.md)
and [independent certification boundary](../../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#14-open-14-automatic-certification-within-an-approved-envelope).
It adds no operator, model permission, new mathematical meaning or scientific
classification. The existing numerical modules and earlier qualifications are
unchanged.

The original asks whether an ETH breakout over all sixteen preceding highs,
with a rising signal bar and low quote turnover, while BTC stays below its own
preceding maximum, precedes a positive ETH-minus-BTC log-return contrast. All
52 required condition values must be available on their exact grid positions;
one missing required value makes the whole condition unknown. The signal and
baseline-mean quote volumes must be positive. One zero baseline volume is
permitted when the full baseline mean remains positive.

`composition.qualify(payload)` checks a separately supplied candidate against
the independently authored, hash-pinned [direct-formula oracle](../../tests/paired_breakout_oracle.py).
The oracle calculates maxima and means directly, without importing an AST,
compiler or framework evaluator. Synthetic fixtures exercise the exact
thresholds, every required input, all possible maximum positions, missingness,
availability, units, outcome timing and independent logarithm calculations.
Only the synthetic interval is shortened to thirty timestamps; candidate
expressions are unchanged. The public population fields must remain the original
Q1 2023 fixed pair and five-bar outcome anchor.

`composition.audit(payload, rows, cases)` compares all original quarterly
timestamps to the independent formulas, including neutral missingness categories
and each observed bounded outcome. Decimal100 is a cross-check, not the proof of
the evaluator's outward numerical bounds. A finite fixture suite does not prove
general semantic equivalence; independent meaning review remains required.

`runtime.run_child` supports only `composition` and `audit`. It uses an exact
retained source closure in an isolated Python process, binds input/source/result
hashes and bounds row/case streams. Audit requires a complete result. Numerical
execution and separate replay remain the existing paired runtime's responsibility.
These functions do not load a registry, dispatch a model or select market data.

The optional [BreakoutBroker](host.py) connects these checks to the owned
controller. Its `certify_paired_composition` and `execute_paired` methods route
only the exact second original idea to this profile; earlier ideas retain their
existing paths. The separately callable `certify_breakout_composition`,
`inspect_breakout_composition` and `execute_breakout` methods require operator
authentication and the exact compiled original.

Source packages and certificates use the existing owned paired record types
with a distinct profile. Certificates bind the candidate, full independently
fixed scenario inventory, retained source bytes, runtime environment and host
source identity. Technical dependency edges connect source package to
certificate, then to execution and input capsule; existing typed revocation
applies. Current compilation, meaning and source checks precede data loading and
are repeated before a success record is committed. The original numerical
execution and separate replay remain unchanged. A stopped calculation retains
its verified prefix; a failed replay retains the exact generated case bytes
without becoming successful evidence.

The [host tests](../../tests/test_paired_breakout_host.py) use real temporary
registries, immutable blobs, compilation, retained-source children and
revocation. Their old source/data-use, meaning-review and row-loading boundaries
are explicit synthetic substitutes. They do not certify an actual market source
or model judgment. A separately admitted model continuation is still required;
this adapter adds no provider or spending authorization and does not yet publish
the second result as feedback.

The analysis fixture in the [composition tests](../../tests/test_paired_breakout_composition.py)
is never an accepted `H_exec`. A model must author its own candidate; all
previous ideas, failed attempts, budget fences and the first pair's
empty-condition result remain.

## Optional bounded model continuation

`BreakoutResearchBroker` in [research.py](research.py) adds the separately
qualified [resource disposition](CONTINUATION.md) under the user's delegated
spending authority. The unchanged `BreakoutBroker` above adds no spending.
The new broker admits only the exact second original idea, one formalization
and its separate meaning review. It retains the full prompts and sources,
high formalizer reasoning, low reviewer reasoning, exact model and no retries.

The two nonrecyclable slots reserve 48,000 input / 32,000 output and 76,000 input /
4,000 output tokens: 160,000 total, USD 0.670 at the existing conservative tariff,
under a USD 0.70 cap inside the original shared USD 5 ledger. Three earlier grants
must remain consumed and revoked. A complete actual input must fit its slot;
an oversized review remains a gap. The unused smaller allocation and the sizing
evidence are retained separately. Extra output space does not guarantee success.

The [independent budget tests](../../tests/test_paired_breakout_budget.py) exercise
concurrent one-use admission, registry rollback, stale inventory, source drift,
unknown spending, exact roles/packets, revocation and preserved legacy routing.
The controller retains the added nested source identities before dispatch and
checks them before making a response usable; a failed post-response source check
still settles accounting. Mocked network tests prove these engineering controls,
not actual model judgment or market efficacy. See the
[qualification record](../../docs/reviews/implementation-2026-10-25/paired-breakout-continuation-qualification-2026-10-30.json).
