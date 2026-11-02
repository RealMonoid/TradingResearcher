# Joint stationary-bootstrap computation candidate

This implementation advances [research-contract/1.0 section 5.3](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#53-dependence-and-uncertainty-dispatch). It computes the prescribed joint resampling distribution for the canonical conditional-minus-whole-scope mean. It does not supply estimator calibration, an information target, a scientific freeze or an EvidenceRecord.

## Computation and retained uncertainty

[stationary_bootstrap.py](stationary_bootstrap.py) consumes a complete `reference-cases/1` report. It uses the existing exact descriptive validator before resampling. Every original timestamp remains in the aligned 15-minute grid, including timestamps with no eligible observation. All instruments at a sampled timestamp share the same multiplicity. Missing outcomes contribute nothing; an eligible observation with unknown condition still contributes to the whole-scope baseline. Counts remain observation-weighted, rather than giving each timestamp an equal statistical weight regardless of its eligible instrument count.

The calculator aggregates exact scope and conditional sums/counts at each timestamp. Circular prefix sums then recompute both means jointly from each resampled index path. It resamples the already materialized condition/outcome cases; it does not refit a signal or evaluate an artificial outcome across joined blocks.

The stationary construction uses a uniform starting timestamp and geometric block lengths whose **mean** is the specified length. Realized blocks can be shorter than the outcome horizon. The last segment is truncated so that every completed replicate contains exactly the original number of timestamps. The horizon lower bound applies to the prespecified mean lengths, not to each random realization. The algorithm follows the stationary construction described by [Politis and Romano](https://users.ssc.wisc.edu/~behansen/718/Politis%20Romano.pdf); that source does not establish validity for this implementation or these market inputs.

The explicit design supplies the base length, provisional primary-family size and PRNG identity/seed. The application uses the adopted horizon-bounded half/base/double lengths, rounds half upward, deduplicates lengths, and attempts all 19,999 draws per required case. An undefined conditional or scope mean retains its original draw ordinal and prevents a combined interval. It is never discarded or replaced. The existing exact basic-bootstrap quantiles and enclosing-interval rules apply only when all required intervals can be constructed.

`randomness(seed)` identifies the installed Python MT19937 implementation and state version. Each sensitivity derives its stream seed from the versioned sampler domain, master seed and mean block length. The [Python random documentation](https://docs.python.org/3.14/library/random.html) explains its finite-precision uniform output and version limits. The geometric inverse transform uses those 53-bit uniforms and `log1p`; it is explicitly a finite-precision probability-law approximation. Rational sums and interval arithmetic are exact within the bounded numeric envelope. Exact rational arithmetic does not turn the geometric transform into an exact probability law. Source/runtime identity and the numeric policy accompany each result; cross-version or cross-host numerical equivalence is not assumed.

The result retains all per-length counts, seed identities, draw-stream digests and any interrupted draw. It never assigns a supported or negative scientific outcome. `COMPUTED_UNCALIBRATED` means the arithmetic completed. `INFORMATION_GAP`, `INPUT_GAP` and `RESOURCE_STOP` preserve distinct reasons why an interval was not available. An optional [Monte Carlo boundary diagnostic](MONTE_CARLO.md) now computes an explicitly uncalibrated stability assessment when its settings are supplied before execution. Its scientific admission remains a separate gate; no selective reseeding or scientific classification is permitted.

## Owned development operation

The operator RPC is `run_development_bootstrap(key, plan_id, execution_id, limits)`. The plan and execution must be genuine controller-owned development records. The execution must belong to the plan's exact compiled hypothesis and be one of its declared development diagnostics. The plan supplies the frozen preparation design; the caller cannot replace the effect, family or randomness through this operation. A preparation plan remains unfrozen scientifically.

The limits explicitly name `max_seconds` and `max_segments`; the installed upper envelopes are 1,800 seconds and 100 million sampled segments. These are resource limits, not an information target or an allowance to finish fewer than 19,999 draws. The host's post-admission time cap includes calculation and replay together. A future scientific batch must also enforce its aggregate budget across claims; this development operation is not that batch controller.

Before starting a child, the registry atomically retains a protected `bootstrap-input/1` capsule and STARTED event. The capsule binds the exact request, plan/case metadata, committed case blob, source bytes, runtime identity and inherited exposure. An interrupted key cannot be rebound to different inputs; same-key continuation uses the captured source. The case data are read only after development ownership and scope checks.

The child runs with isolated Python flags and emits a bounded canonical JSONL draw stream. Each completed draw, including an undefined draw, retains its ordinal, exact value, denominator counts and path digest. A completed calculation is repeated in a separate process using the same retained source and compared against the exact draw bytes and result. This is reproducibility checking, not an independent statistical method or calibration experiment. A resource-stopped prefix is retained without claiming a complete replay.

Before commitment, every returned result receives exact schema, bound-input, seed, counter, ordinal, stream-hash and interval-arithmetic checks. This includes resource stops: a missing/contradictory result or rehashed malformed draw suffix is rejected. A pending input cannot be relabeled as a resource stop, and segment exhaustion must agree with the retained work count. Stopped prefixes explicitly record that their paths and draw values were not numerically replayed; their combined interval remains absent.

The protected `development-bootstrap/1` record stores the result, draw blob, input capsule and replay/validation provenance. Generic source/worker writes cannot mint these records. The operation grants no protected-partition access, assessment release, N_min, scientific allocation or capital authority.

## Verification and remaining work

The [verification record](../docs/reviews/implementation-2026-10-25/bootstrap-verification.json) records exact exercised tests, source preservation and unverified limits. The [baseline](../docs/reviews/implementation-2026-10-25/bootstrap-baseline.json) preserves the preceding auxiliary-role checkpoint. Independent arithmetic/adversarial checks, synthetic executions and reproducible sampling are separate from the contract's fresh-world calibration requirements.

Two fixed synthetic workload probes completed all 59,997 draws: 2,048 timestamps with two instruments and constant Boolean outcomes took 9.004 seconds; 35,136 timestamps with two instruments and periodic Boolean conditions/outcomes took 154.350 seconds. The second probe ran alongside the full regression suite. These observations measure the exercised computational workloads on this machine, not statistical calibration, actual return-data throughput or discovery-to-report acceleration.

### Exact arithmetic acceleration for simulation work

The later [information-planning checkpoint](../docs/reviews/implementation-2026-10-25/information-planning-verification.json) addresses the cost of repeatedly applying this actual estimator. Integer-valued sufficient statistics now use Python's exact unbounded integers within the unchanged 8,192-bit numeric envelope. Fractional observations keep rational arithmetic. Each draw still constructs both means as exact `Fraction` values before subtraction; integer division never introduces a floating-point decision. Overflow checks, full-grid sampling, seeds, all required draws, undefined values, stream ordinals/digests and Monte Carlo diagnostics are preserved.

The [retained pre-change source](../docs/reviews/implementation-2026-10-25/information-planning-baseline.json) supplies a comparison oracle for complete calculations and stopped prefixes. Paired benchmarks use the same fixed inputs and draw counts and require equal result hashes, including the per-length draw-stream digests. Their local workload target is separate from D081's end-to-end research acceleration criterion. This arithmetic change cannot establish an attainable simulation-study budget or statistical power by itself.

On the declared machine, two alternating pairs of the 2,048-timestamp periodic Boolean workload gave median calculation times of 4.005 seconds for the accelerated path and 8.633 seconds for the retained path (2.16x). A single 35,136-timestamp pair took 48.595 versus 134.584 seconds (2.77x). Each calculation completed 59,997 draws with an identical full result hash. No project test process intentionally ran concurrently during these comparisons; ordinary system background load was not controlled. These are synthetic calculation measurements, not a confidence interval for speed, a result for fractional return data, a calibrated study-budget guarantee or an end-to-end research-speed claim.

The accompanying [planning assessment](../docs/reviews/implementation-2026-10-25/information-planning-assessment.json) separates a future faithful binary population model from finite-sample realized contrasts, identifies return-process and heterogeneity limits, and retains the approved calibration thresholds. It is methodology guidance, not an implemented information study or an adopted new scientific contract.

Still required are development-only dependence/information derivation, justified stationarity and denominator adequacy, calibration/admission of the optional predeclared Monte Carlo diagnostic, the section-11 null/boundary/heavy-tail/overlap/common-shock calibration and planted alternatives, and atomic scientific allocation/freeze. Actual LLM discovery, historical data/rights/PIT acceptance, full-process calibration and economic usefulness remain unverified.

### Reusing canonical draw bytes

The optional keyword-only `on_draw_bytes` callback receives each completed draw as immutable canonical UTF-8 JSON without a newline. These are the same bytes used by the draw-stream hash (which includes a newline). The existing `on_draw` callback keeps its independently copied dictionary; either or both sinks may be supplied. Undefined draws, callback failures and cancellation/resource limits retain their previous treatment. No replicate, random-number, statistic or decision rule changes.

The owned study child uses this byte sink to frame the already serialized draw as `{"kind":"draw","value":...}`. Case records still use the generic canonical encoder. Generation and replay share the same size-limited, hash-checked line writer. The complete retained stream remains byte-identical to the original dictionary path, while avoiding a second validation/serialization and dictionary copy for every draw. Previously retained source capsules continue to execute their original code.

An actual retained development-world comparison, with 16 timestamps and all 59,997 draws, ran three alternating generation/replay pairs per source version. Median time fell from 5.828025 to 4.829184 seconds (17.14% lower). Every numerical result and the entire 15,699,508-byte stream matched the prior version exactly. These unprofiled child comparisons are distinct from the earlier instrumented bottleneck profile; [Python's profiler documentation](https://docs.python.org/3.14/library/profile.html) explains why profiler timings are not benchmarks. Background system load was not controlled. This small workload does not establish large-sample speed, scientific calibration, complete budget feasibility or end-to-end research acceleration. [Verification](../docs/reviews/implementation-2026-10-25/draw-transport-verification.json) records checks and the independent review.

### Grouped circular sufficient-statistic queries

Following the November 2 existing-limits/exact-acceleration decision, the current
calculator queries its four cumulative statistics together with the bound Python
standard-library `operator.add` and `operator.sub`. It retains exact Python
integers and fractions. Circular subtraction then addition keeps its original
association; an oversized intermediate difference may cancel before the existing
caller checks its accumulated total and conditional sum. No new intermediate
bound or fixed-width conversion is introduced. Grid positions, including empty
buckets and unknown-condition baseline observations, remain aligned.

Transposing the four existing prefix lists adds one tuple of four references per
grid position, plus the containing tuple. Numeric objects are reused. This linear
memory and setup cost belongs in whole-calculation timing. PRNG consumption,
geometric lengths, path hashing, full draw counts, callbacks and the existing
segment/cancellation/deadline checks retain their original behavior; this change
establishes no hard instantaneous memory or time quota.

The [existing source archive](../tests/fixtures/study-source-0f1bf36.zip) already
contains the exact pregrouped sampler, SHA-256
`010810c61cbe9fc880aafb19a2c1b16ccedd4912ce8e7dd57e3a9e449dbae6d7`.
Independent hand-fixed cases exercise wrapping, large integers/fractions and the
8,192-bit cancellation boundary. The controlled child comparison retains full
historical replay and all decoded bytes while holding model-record semantics
fixed for complete raw/encoded/pre/post result equality. It preserves the later
source-process diagnostic fields and their documented identity changes rather
than stripping metadata from results.

Old source capsules remain unchanged. In particular, the completed 32-world
development grid and any final series derived by the existing controller retain
that grid's original calculator; a faster installed source cannot retarget them.
Future eligible execution needs its own valid source/runtime binding. The
[existing work record](../docs/reviews/implementation-2026-10-25/progress.json)
retains exact checks, paired timing and the remaining calibration/resource gaps.

Four fixed unprofiled calculations on the existing 4,096-row binary fixture ran
in BEFORE/AFTER/AFTER/BEFORE order, with all three 19,999-draw cases and the same
predeclared Monte Carlo settings. Median time was 54.348309 seconds before and
52.331552 seconds after (3.71% lower elapsed time). Complete result and combined
draw-byte hashes matched in every observation. Setup, transposition, validation,
interval/MC and byte-sink work are included. No project tests intentionally ran
concurrently; background system load was uncontrolled. Two observations per
version supply no paired uncertainty estimate, full-series resource guarantee,
market calibration or D081 acceleration claim.

### Retained native runtime inputs

The operator may import an `operations` archive with the existing
`add_blob_source` operation, then call `retain_native_runtime` with exactly
`key`, `archive_id` and `manifest`. `inspect_native_runtime(runtime_id=...)`
verifies the owned package and every archive member. A retained package has
authority `retained_native_runtime_not_certified`; it starts no native code and
does not select a calculator, qualify dependencies or grant scientific use.
Workers cannot invoke either operation or forge the reserved package schema.

The versioned `native-runtime-files/1` manifest binds the exact current Python
runtime, dependency versions/distribution hashes/license files and a complete
file-size/hash table. ZIP decoding uses the bound standard library. The archive
and decoded total are each bounded to 512 MiB, with at most 4,096 files and the
existing canonical 1 MiB envelope. Relative names, parent spellings, regular file
types and decoded bytes must match exactly; path aliases, normalized names,
encryption and unsupported compression fail before cache writes. These are
separate runtime-input bounds; the old 128-file/16-MiB project-source and
256-blob-reference contracts remain intact. One registered archive reference and
two compact version fingerprints use the existing Blob/backup/revocation owners.
Re-registering identical runtime inputs under another key cannot escape a
recorded technical-version revocation.

The internal materializer publishes a verified complete tree from a unique
owned staging directory. It shares an exact cache, refuses a changed published
tree, retains unrelated interrupted staging and never repairs a cache in place.
Missing caches rebuild only from the retained archive, including after backup
restoration. Every new or partially written byte is passed to the caller's
meter; a cache hit writes no bytes. A future reserved study caller must include
input retention, these writes, CPU, outputs and recovery in its existing budget.
No scientific quota or OS tamper-proof filesystem guarantee follows from this
helper. The child must verify its selected environment and the tree after use.

The [retained input checks](../tests/fixtures/native-runtime-input-checks-2026-11-02.zip)
preserve pinned upstream acquisition, own build inputs and receipts. Synthetic
HTTP/concurrency/crash/restore cases and a real NumPy/adapter archive passed.
The isolated `-I -S -B` child reran the same 13 fixed loop cases from the selected
cache; all 98 imported NumPy/adapter module files matched it. This is not proof
of transitive OS/native DLL paths or loaded binary identity. Real Windows
junctions were checked; the separate symlink case remains skipped on this host
because creation is denied. The numeric adapter and exact fallback below are
checked; actual study selection, full native environment qualification and
scientific admission remain open.

### Explicit qualified draw engine

`calculate` accepts a private `_draw_factory(rng, prefix_rows, length)` from a
separately qualified owned caller. It runs once per sensitivity length. `None`
retains the same original scalar RNG and all its numeric guards. The world and
family calculator functions forward an explicit factory; their default calls
add no new keyword to legacy callees. This private hook authenticates no factory
and no Registry operation selects one yet.

The versioned `stationary-native-int64/1` kernel reuses the qualified NumPy
MT19937 core. The adapter copies the exact Python state-v3 words and position
without advancing that RNG and uses the actual Python `log1p` and `floor` per
draw. Integer prefixes enter the native subset only after the conservative
`N * max_abs_bucket_delta <= 2**63-1` proof for every sufficient statistic.
Fractions, larger integers, unsupported row counts or mean lengths return to
Python before consuming RNG. The native 100,000-row/length envelope does not
restrict the original public length or 8,192-bit exact-number envelope.

The engine preserves candidate-generation-before-check order, partial counts and
path bytes, and passes current-draw segment offsets to the existing global
resource checks. Pre/post-draw and interval checks, callbacks, exact mean/effect
guards, full draw counts and classification prohibitions remain in place.
Compatibility metadata and the pinned kernel source do not issue a certificate.

The [numeric integration evidence](../tests/fixtures/native-calculator-integration-2026-11-02.zip)
retains the independent frozen-oracle checks, canonical build and complete
4,096-row result/draw-byte gold comparison. Its loader observations include
current Python, Windows and preexisting vendor images; those observations still
need a qualified immutable host-image binding before actual native study use.

### Selected native environment observations

The private `binding.environment(..., _native=NativeContext(...))` collector
checks imported NumPy/kernel files against the selected retained cache. It
records `native-bootstrap-environment/1` alongside the original Python runtime,
standard-library hashes and isolation flags. Default callers retain the exact
three-key interface; the original validator still rejects extended records.
Only the selected namespaces are handled. Unknown modules, missing file bindings,
wrong suffixes, linked cache files and unqualified host paths fail closed.

The collector uses bound `ctypes` and the documented Windows loader APIs. Each
loaded runtime image must match the manifest; each host image must match an
explicit trusted path, size and hash supplied by a future independent qualifier.
Legitimate OS component-store hardlinks are allowed only for these host files;
runtime cache files still require one link. Module files are rechecked when the
observation is emitted. The parent `native_environment.current` verifies the
extended record and the complete cache without importing NumPy or enumerating
the parent's images. Capture before and after use is the owning caller's duty.

The [component evidence](../tests/fixtures/native-environment-checks-2026-11-02.zip)
retains independent mutation/alias/namespace cases and an actual separate-child
pre/post probe. Its reference host inventory is provisional input, not a
certificate. Loaded paths and current file bytes do not prove relocated memory
identity or absence of hidden mappings. Actual study selection, independently
issued runtime qualification, reserved accounting, replay and scientific
admission remain open.

### Owned runtime qualification

The operator can call `qualify_native_runtime(key=..., runtime_id=...)` and
`inspect_native_runtime_qualification(qualification_id=...)` through the existing
Broker/HTTP interface. The latter accepts the retained input or result identity.
Workers cannot invoke them or forge their reserved records. Generic retention
and compatibility metadata grant no qualification.

`stationary-native-runtime/1` accepts only the pinned canonical archive,
manifest, kernel and prior independent fixtures. It fixes the observed host
paths/hashes before work, preserves the original assertions and complete golden
result/stream, and records the complete current source closure. The owned input
and `STARTED` event commit before cache materialization or child execution.
Two fresh isolated children each run the same 13 independent loop cases and all
59,997 calculator draws; replay compares every retained draw byte. Both phases
must pass pre/post environment, source, cache and fixed-result checks.

The implementation-qualification attempt is bounded to 300 seconds and 256 MiB
of logical retention/materialization/output accounting. Unknown usage preserves
at least that full reservation; known overruns and failures cannot certify.
Input blobs are rechecked after execution, output bytes at intended use. Exact
key replay returns immutable history. A changed request conflicts; an unfinished
or interrupted attempt needs an explicit new key, retaining its prior cost.
Typed source/runtime/input/result revocation blocks use without deleting history.

Inspection is read-only. `CURRENT` requires intact source, archive, cache,
retained output and environment bindings. A missing restored cache is `STALE`;
the same certificate can become current at a new cache location after exact
reconstruction. The [qualification evidence](../tests/fixtures/native-qualification-checks-2026-11-02.zip)
retains fixed-case, lifecycle, integrity, actual operator and real restore checks.
This is implementation conformance only. Actual reserved study selection,
aggregate study accounting, old-source transfer, calibration, scientific
admission and protected-data authority remain separate prerequisites.
