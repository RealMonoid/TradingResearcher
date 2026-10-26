# Independent expectations for keyed bar quarantine

The adjacent `reference_binance_quality_cases.json` was fixed before reading any new row-quality implementation. Its 32 synthetic cases distinguish present valid bars, present unusable bars, absent grid bars and a source whose rows cannot be assigned unambiguously. The existing 43 strict Binance expectations remain unchanged. A successful audit is not strict normalization success or scientific data acceptance.

## Bounded interpretation

This is conservative input representation under research-contract/1.0 sections 4, 6 and 14: retain unusable observations as missing values while preserving identity, source bytes and coverage. It does not change an estimand, authorize a new scientific exclusion policy, repair observations or establish historical publication. Subsequent feature/data certification and frozen missingness/eligibility rules remain separate requirements. The implementer cannot turn an audit into an evidence verdict.

A usable row key requires the declared source-unit convention, an exact aligned in-month opening timestamp and unique increasing order. Even an otherwise invalid bar must have that unambiguous key. A malformed layout, broken quoting, multiline field, duplicate/reversed key or invalid key rejects the entire source. No partial successful audit is expected in those cases. This avoids assigning the same observation twice, moving an uncertain row to a neighboring slot, or hiding a skipped ambiguous record.

For an unambiguous keyed row, a malformed close, invalid trade count, invalid quantity or failed OHLC/volume invariant produces `INVALID_BAR`, with `bar: null` and a fixed typed reason. The reason codes are `INVALID_CLOSE_TIME`, `INVALID_TRADE_COUNT`, `INVALID_QUANTITY` and `OHLC_VOLUME_INVARIANT`. Each case with a typed reason isolates that defect, so no cross-defect reason precedence is introduced. Source-level rejection labels are explanatory and may map to the application's existing typed errors.

Every record retains its one-based physical line number and exact raw-line SHA-256. The line hash includes its original LF or CRLF terminator, if present. The source hash covers all original bytes. The fixture supplies those bytes as `raw_csv` text encoded as UTF-8 without newline rewriting. Coverage counts and gap intervals refer to the source's opening-time grid, not the shifted reference-row timestamps.

For an invalid close, `end_time = open_time + 900` identifies the expected grid boundary only. It must not be described as an observed close or a repaired source timestamp. In particular, the final development bar still has an expected end at the assessment boundary; the adapter retains that fact and does not relabel its partition. Original timestamps and rejected values remain recoverable from the retained source bytes.

## Missingness and reference rows

A valid zero-activity bar retains its actual zero volumes and trade count. A present invalid bar produces a reference row whose nine numerical features are all explicitly null. An absent source bar produces no synthetic row. `present_bars = valid_bars + invalid_bars`, and `expected_bars = present_bars + missing_bars`. Invalid rows must not inflate the absent-grid count or disappear from the denominator record.

The reference adapter must operate on retained raw bytes and re-audit them, rather than trusting caller-edited audit dictionaries. It keeps symbol-qualified units and feature versions from the preceding independent fixture. For every valid or invalid keyed row, the fixture explicitly selects a five-second availability scenario: `available_at = expected_end_time + 5`, basis assumed, historical publication unknown and scientific readiness false. The delay is a test parameter, not a proposed real-market latency rule. Null values remain unusable regardless of the assigned scenario timestamp.

## Fixture shape and checks

Each case has `name`, `symbol`, `month`, exact `raw_csv`, explicit `delay_seconds`, and `expected`. Accepted audit expectations include schema `binance-row-quality/1`, source SHA, exact records, coverage, expected-end qualification, historical-publication qualification, false scientific readiness, whether the unchanged strict parser accepts the input, and exact reference rows. Rejected source expectations contain no partial records or reference rows.

Cases cover LF/CRLF/no-final-newline provenance, truncated/malformed/microsecond close times, impossible OHLC ordering, nonpositive prices, negative quantities, excess taker quantities, invalid trade counts, nonfinite quantities, valid zero activity, combined valid/invalid/absent bars, partition boundaries, duplicate/reversed/invalid keys, ambiguous layout/quoting, a blank physical line and empty input.

These fixtures do not choose whether any later inferential analysis may ignore a defective row, whether maintenance-related missingness is ignorable, or how an effect estimate should account for missing outcomes. Those are scientific-plan requirements. No snapshot may be promoted to acquisition-accepted, certified, independent or suitable for live use merely because its keyed audit or all-null adapter passes these checks.
