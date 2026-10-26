# Independent raw-feature expectations

These expectations were authored before the feature-certificate implementation was inspected. No production calculator, normalization function, or proposed certificate validator was imported to produce expected values. Existing specification and field mappings were read; the expected numbers are hand-assigned decimal strings.

## Authority and interface

The fixture has schema `reference-feature-cases/1`, an exact `definitions` list of 18 entries, and `cases` containing 10 raw projections plus 21 negative admission probes. Each definition uses `raw-binance-feature-definition/1`. Its fields are the exact feature reference, instrument, source field, zero-based CSV column, source scalar domain, existing output type/unit, exact projection rule, time rule, missingness rule, assumed availability rule, and null fitted state. Definitions are ordered BTC then ETH, with source columns 1, 2, 3, 4, 5, 7, 8, 9, 10 within each instrument.

Bound record metadata is separate: exact snapshot/catalog/row/raw-source identities, specification and validator versions, explicit scenario delay, source/runtime fingerprints, fixed golden-case references, and inherited exposure. Static definitions do not contain runtime IDs or retrieval times. A one-symbol snapshot certifies only its nine applicable definitions. A two-symbol catalog has all 18, while each row has only its own symbol's nine features.

`certificate_allowed` means only that exact raw-field conformance may be issued after all independent software, provenance, and host-boundary checks pass. It is never a scientific readiness, historical PIT, source truth, legal permission, independence, calibration, trading, or capital assertion. Synthetic provider/source fixtures do not establish real acquisition facts. Negative probe reasons are semantic expectations, not mandated runtime error-code spellings. A harness must execute every listed probe or explicitly report it unexecuted; enumerating fixture names alone is not coverage.

## Fixed meaning

Source columns 0 and 6 contain open and observed close timestamps. Columns 1/2/3/4 are open/high/low/close, 5 is base volume, 7 quote volume, 8 integer trade count, 9 taker base volume, 10 taker quote volume. Column 11 is validated by the existing complete-bar parser but is not a feature. OHLC use USDT/BTC or USDT/ETH; base and taker-base volume use BTC or ETH; quote and taker-quote volume use USDT; trades use count. No base quantities are collapsed across instruments. All outputs retain the existing `real` catalog type; a trade count remains an exact nonnegative integer-valued decimal string, never a fitted or rounded statistic.

The existing complete-bar gate applies jointly, including OHLC/volume/count/timestamp invariants. A valid source decimal projects exactly, removing only irrelevant decimal formatting; the fixture's `0007` count becomes `7`. The positive OHLC scalar domain and nonnegative volume/count domains describe admitted valid bars, not a salvage rule for invalid rows. No fit, normalization, learned threshold, winsorization, cross-symbol fill, or named derived feature is introduced. Arbitrary later compositions remain explicitly typed expressions with their own applicable checks.

The source unit is milliseconds before January 2025 and microseconds from January 2025. A complete source close is open plus 900 source-unit seconds minus one source tick. The observation anchor is the exclusive expected end, open plus 900 UTC seconds. Invalid keyed bars retain that expected grid end without claiming it was their observed close. Assumed availability is exactly that row time plus the explicitly bound nonnegative integer delay; no default exists. A delay beyond the selected universe does not move or remove an observation. Historical publication remains unknown.

A present invalid keyed bar has all nine symbol values null. An absent source bar creates no row. Genuine zero volume/count remains zero. The other symbol's fields are absent, not null measurements. These distinctions must survive certification and remain available to a later scientific missingness policy; conformance does not license dropping defective or absent observations.

## Hand calculations

At 2020-01-01 00:00 UTC, source open 1577836800000 ms yields observation 1577837700 and, with delay 5, availability 1577837705. At 2025-01-01 00:00 UTC, source open 1735689600000000 us yields observation 1735690500. ETH's 18-decimal values remain exactly those source decimals. A 1800-second delay gives BTC availability 1577839500 without changing any measurement.

For the [00:00, 00:30) one-symbol window there are two expected instants, 00:00 and 00:15. The January source supplies only the latter; the first is absent rather than fabricated from unavailable 2019 source. The two-symbol case has four expected rows, two observed and two absent. The internal-gap case has four expected instants, two observed rows at 00:15 and 00:45, and absent instants at 00:00 and 00:30. The paired future cases change only the later 00:30 observation; the entire earlier 00:15 row remains identical. No previous/future value substitutes for an absent row.

## Admission probes and scope

Each `admission_probe` references a raw-projection base case and describes one deliberate change to its otherwise correctly constructed owned snapshot/dependencies. The harness creates the real registry artifacts needed to exercise that seam; object/path names in these descriptions identify semantic targets rather than requiring an internal class layout. Generic-source certificate forgery and wrong-snapshot reuse exercise verification, not source normalization. No mutation may be repaired silently into the supplied base result.

The probes cover unit/type/version forgery, unequal values or availability, metadata authority promotion, source-open relabeling, invalid-row salvage, absent-row filling, cross-symbol contamination, selection counts, fitted-state injection, transitive protected ancestry, worker/generic-source certificate issuance, wrong-snapshot reuse, corrupt raw bytes, changed validator code, incomplete child check coverage, and scientific-readiness promotion. Wrong-key, corrupt backup, timeout/cancellation, import closure, and same-process stale imports still require runtime integration checks; these declarative fixtures do not claim to execute them.

## Independent validation design

Prefer one fresh `-I -S -B` child directly invoking the already bound normalizer against a private verified registry copy. Establish the same verified package/environment binding before core invocation. Do not recursively launch another normalizer process without an explicit descendant-cleanup design. The caller's long-lived imported calculator is not the certified implementation. Archive the executed application/test/spec/fixture closure and bind the runtime fingerprints; do not describe fingerprints as archived Python binaries.

Replay comparison must include exact row bytes/hash, catalog, universe, partition, assumed delay and basis, invalid/absent coverage, per-source selection counts, original receipt qualifications, and complete protected ancestry. New replay artifact IDs and host execution times are expected to differ and may be matched by semantic role; original source identities/times and applicability assumptions may not be discarded in this matching. Bind the original snapshot and original normalization provenance separately from the new validator execution package. Parent-side rechecks must reject changed data/package/runtime closure before committing a reserved host-issued certificate. Missing or corrupt closure and timeout/malformed response cannot yield a certificate.

This is within the existing raw-field/implementation conformance envelope of research-contract/1.0 section 14, provided those limits remain explicit. It is not approval of a scientific missingness policy or proof that assumed bar-end availability was historically true. New feature meanings, fitted state, or materially different temporal rules require their existing review route.

Sources: `docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md` sections 4, 6, 8, 14; `docs/architecture/04_DEFINITIONS.md` DEF-006/013/033; `docs/architecture/09_IMPLEMENTATION_BLUEPRINT.md` FeatureDefinition and IF-04; `trading_researcher/BINANCE.md`; `trading_researcher/BINANCE_NORMALIZATION.md`; existing independently fixed 43 archive, 32 row-quality, and 22 partition expectations. These references establish scope, not empirical market evidence.
