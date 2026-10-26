# Independent decision-time partition expectations

The adjacent `reference_binance_partition_cases.json` fixes 22 synthetic cases before any partition-normalization implementation was inspected. It builds on the unchanged strict archive and keyed-quality contracts. Its accepted cases establish expected row placement and explicit missingness, not scientific acceptance or unseen assessment data.

## Meaning of the boundary

An archive bar is identified by its source opening instant. Its normalized observation instant is the expected exclusive end, 900 seconds later. The snapshot universe is a half-open interval of those decision-time observations, entirely inside one canonical partition. Thus a December 31 bar opened at 23:45 has its normalized observation at January 1 00:00. This changes its container's decision-time assignment; it does not erase source ancestry, exposure, receipt history or the distinction between an expected and observed close for an invalid bar.

The assessment window starting January 1, 2024 may therefore require both December 2023 and January 2024 archives. The corroboration window starting January 1, 2025 requires December 2024 timestamps interpreted as milliseconds and January 2025 timestamps interpreted as microseconds. Units follow each named source month, not the selected snapshot's year. The final December 2025 bar ends at January 1, 2026; it remains an explicitly counted after-window row when the requested universe ends there.

This is decision-time data organization under the existing calendar contract. It does not claim that a row in an assessment container is independent, model-unseen or eligible for confirmation. Earlier source exposure persists. The outcome evaluator retains responsibility for label-information intervals, warmup review, maturity and boundary eligibility; this adapter must not preempt those checks or invent a new outcome exclusion policy.

## Required sources and selection

For every requested instrument and 900-second decision instant, determine the source month containing that instant minus 900 seconds. Require exactly those distinct symbol/month sources within the adopted 2020-2025 archive profile. Reject missing, duplicated or irrelevant sources, rather than substituting another month or instrument. Required pre-2020 source time is unavailable by the adopted profile and is not fabricated.

Consequently, a universe starting January 1, 2020 00:00 and ending 00:30 can use January 2020 to supply the 00:15 observation while preserving the absent 00:00 observation. A universe containing only the unavailable 00:00 observation has no rows and fails explicitly with `NO_OBSERVATIONS`; it creates no snapshot. A present invalid keyed bar is different: it produces an all-null row and remains present even if every selected observation is invalid.

Re-audit every supplied required source before selection. Ambiguous keys or layout anywhere in a required source remain a whole-source failure even if that physical row lies outside the requested window. Validly keyed records outside the window may be counted without being delivered as rows. The normalizer must never filter before checking source ambiguity to obtain a convenient subset.

For every supplied symbol/month, retain counts `{symbol, month, selected, before, after}`. These counts include valid and invalid keyed records. `before` means expected end less than universe start; `after` means expected end greater than or equal to the exclusive universe end. Counts sort by `(symbol, month)`. Output rows sort strictly by `(time, instrument)`, independently of input source order or instrument-list order. An absent row is never synthesized or borrowed from another instrument.

## Values, availability and authority

Use the existing symbol-qualified nine-feature mapping and units. Selected valid bars retain exact normalized values; selected invalid keyed bars retain nine explicit nulls for their instrument. Missing instrument/time observations remain absent. The fixture's delays 0, 5 and 1800 seconds are explicit test parameters, not factual or recommended publication latency. Availability is expected end plus delay, basis assumed, and scientific readiness remains false. A delay can extend beyond the snapshot universe without shifting the row or silently dropping it; later permitted calculations enforce their actual cutoff.

Protected source ancestry must be checked before blob reads. Development cannot read assessment or operational inputs merely because their wrapper or requested partition is labeled development. Authentication, provider-document validation, committed-byte hashes, complete exposure closure and backup recovery require integration tests because these format-neutral fixtures contain raw synthetic sources rather than broker capabilities.

Current verification/retrieval from retained local copies must be distinguished from original provider receipts and historical publication. Legacy unbound failure-receipt times remain unknown for the captured source bytes. Retain exact original records rather than replacing their timestamps. Code provenance must identify the transform actually executed: copying today's workspace files while running older imported code does not establish that binding. A fresh bound execution or explicit stale-code refusal is necessary before claiming exact executed-code provenance.

## Fixture interface

Each case contains `sources` with `symbol`, `month`, exact UTF-8 `raw_csv`; `partition`; `universe` with exact UTC start/end and instruments; explicit `delay_seconds`; and `expected`. Accepted expectations contain exact rows and per-source selection counts, assumed availability and false scientific readiness. Rejected expectations contain no rows or counts; reason strings are explanatory labels that can map to existing typed errors.

The fixtures do not authorize automatic data acceptance, inferential missingness assumptions, hypothesis freeze, monitoring events or live use. Passing them only checks this bounded transformation and its failure behavior.
