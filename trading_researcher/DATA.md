# Bound normalized data snapshots

This implements the data-binding portion of IF-01 under [research-contract/1.0 sections 6 and 8](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md). It binds an exact supplied catalog, normalized row files, retained raw sources and acquisition assertions. It does not certify those assertions, reconstruct historical vintages, establish feature meaning, allocate confirmation data or grant scientific execution authority.

The host operation `register_data_snapshot(catalog_id, row_source_ids, manifest)` is available through the existing authenticated operator RPC. The catalog must be a retained `feature-catalog/1` source with exactly `schema` and `features`, using the [reference expression types](EXPRESSIONS.md). Ordered row source IDs must resolve to owned `blob-source/1` files imported through [external storage](STORAGE.md). A filename or an uncommitted digest cannot substitute for an artifact reference. Models cannot register snapshots or read their bytes through this operation.

The manifest has these exact fields:

| Field | Required value or structure |
|---|---|
| `schema` | `reference-data-request/1` |
| `profile` | `historical-spot-pilot/1`, the adopted initial engineering/data profile |
| `partition` | `development` (2020-2023), `assessment` (2024), or `corroboration` (2025) |
| `grid_seconds`, `timestamp_unit` | Integer `900`, and `seconds`; units are never guessed or converted |
| `universe` | Exact UTC `start`/`end` strings, inclusive/exclusive, plus a unique nonempty `instruments` list drawn from BTCUSDT and ETHUSDT |
| `observation_time_definition` | Explicit text distinguishing what the observation timestamp denotes; it is not proof of bar-close or publication timing |
| `provenance` | `provider`, `revision`, exact UTC `retrieved_at`, nonempty `source_uris`, nonempty `raw_source_refs`, and `checksum_evidence_refs` |
| `availability` | `basis` (`unknown`, `assumed`, `documented`), `description`, and `evidence_refs`; documented assertions require references |
| `rights` | `basis` (`unknown`, `documented`), `description`, and `evidence_refs`; documented assertions require references |
| `transformation` | `description` and `code_refs` describing the normalized data's production |
| `supersedes` | Zero or more earlier owned data snapshot IDs; original records and exposure remain |

Every referenced source must exist. Raw input references resolve to owned blob sources. Known provenance ancestry is traversed, including through wrappers. Assessment ancestry cannot become development data, operations cannot silently become research inputs, and unreleased work products cannot be relabeled raw inputs. Assessment/corroboration snapshots retain the protected assessment class. The original sources' known availability and the host snapshot creation time propagate to later context admission. Historical row time, claimed publication time, retrieval time and host registration time remain distinct.

`reference-rows-jsonl/1` is UTF-8 JSON Lines, with one complete [reference row](EXPRESSIONS.md) per line; blank lines are rejected. Each row has exactly `time`, `instrument` and `features`; each supplied sample has exactly `value` and `available_at`. Duplicate JSON keys, floating-point JSON numbers, unknown feature versions, invalid scalar types and off-grid/undeclared observations fail. Keys `(time, instrument)` must increase strictly across all shard boundaries. A final newline is optional. Files are retained exactly; validation does not rewrite source bytes.

Observation seconds must lie on the declared grid within the selected partition and universe. Availability is an integer in the representable UTC domain, 0 through 253402300799 (`9999-12-31T23:59:59Z`). This rejects unrepresentable/misdeclared values without imposing a latency rule or silently guessing timestamp units. A future availability time is permitted and counted as late. An integer supplied for `available_at` never establishes that the value was actually published then; unknown/assumed provenance remains qualified. The checker cannot identify every possible unit or timestamp mistake that happens to fall within the allowed numeric range.

Coverage reports aggregate expected rows across every declared instrument/time, observed rows, missing grid rows, absent feature keys, explicit nulls and samples supplied with availability later than their observation. It never fills gaps or substitutes zero or the nearest row. Empty complete input is rejected as a data gap and creates no snapshot. An instrument with no supplied rows remains in the declared universe and aggregate expected/missing counts; there is no separate per-instrument coverage table. The host checks every row file before commitment and verifies all committed blob ancestry again in the final transaction. A malformed last shard or changed source leaves no partial snapshot. Normalized row streaming runs outside the registry lock; final blob hashing holds the lock and can delay worker heartbeats.

A successful immutable `data-snapshot/1` records `STRUCTURE_VERIFIED`, the complete manifest, catalog ID/hash, row source IDs, coverage, provenance/exposure and `scientific_readiness: false`. Its remaining gates explicitly include availability, rights, provider checksum authenticity, transformation fidelity, feature certification and scientific exposure/plan review. Retaining a supplied checksum document is not verification of a provider checksum. The operation does not perform Binance ZIP/CSV acquisition, OHLCV invariants, source-to-row normalization comparison or an independent provenance review. A later accepted acquisition/feature record must bind the same exact versions rather than rewrite this structural record.

The private host seam `_load_reference_data(snapshot_id, start, end, instruments, max_rows)` verifies the complete retained snapshot and its source ancestry, then returns only the exact requested window. It is not exposed through RPC, is not itself an authorization check for scientific execution, and must be called only after the future caller has enforced context/partition/freeze permissions. Out-of-snapshot windows fail. A row limit causes an explicit failure rather than truncation. Returned values remain qualified and immutable registry records are unaffected by caller edits.

Resource limits are 500,000 declared/observed rows per snapshot, 256 row-source IDs and at most 256 entries per other reference list, 512 MiB total normalized row bytes, 1 MiB per line, and at most 100,000 rows per reference-calculation window. Total transitive ancestry can exceed 256 references, subject to the retained envelope's existing size bound. These are software envelopes, not statistical stopping rules. They cover the declared six-year/two-instrument pilot by separate partition snapshots; they do not justify dropping observations from a scientific request. Maximum-size throughput and memory usage have not been benchmarked. Complete runtime backups preserve manifests, source relationships and bytes; corrupt or missing ancestry prevents loading after restoration.

Run `python -B -m unittest discover -s tests -p test_data.py` for focused tests. They use synthetic hand-written rows, real SQLite files, authenticated HTTP and complete backup/restore. They do not supply market evidence or certify the truth of provider provenance.
