# Partition-bound Binance normalization

This operator utility turns [committed archive source bundles](BINANCE.md#keyed-quality-audit-and-registry-retention) into [bound data snapshots](DATA.md). It implements calendar organization and exact source transformation under research-contract/1.0 section 6. A structurally verified snapshot remains scientifically unaccepted: historical publication, feature meaning, eligibility, inference and exposure admissibility are separate gates.

## Request and execution

Run against an existing local registry that is not open in another process:

```powershell
python -B -m trading_researcher normalize-binance-partition --directory .trf-runtime/research --request normalization-request.json
```

The request is JSON with exactly `source_bundle_refs`, `provider_documents_ref`, `partition`, `universe` and `delay_seconds`. `source_bundle_refs` names retained `binance-source-bundle/1` artifacts; the document reference names retained provider documentation. The universe contains UTC `start`/`end` and a nonempty unique subset of BTCUSDT/ETHUSDT. Start is inclusive and end exclusive, both on the 900-second grid, wholly within the selected development, assessment or corroboration calendar partition. The nonnegative integer delay is required; there is no default. It defines a separate assumed scenario, not measured publication latency or a scientific policy.

The Python host interface is `normalize_retained_partition(directory, source_bundle_refs, provider_documents_ref, *, partition, universe, delay_seconds)`. It copies the entire application Python package into a fresh temporary source snapshot, retains a hash manifest and launches `python -I -S -B`. The snapshot has no cached bytecode. The child checks its source manifest, import closure and isolation, owns the registry for the operation and authenticates its existing local operator credential. This is not a worker/model tool and exposes no raw-blob RPC.

The child retains the exact copied application sources, Python executable/library identity and loaded standard-library file fingerprints. The parent checks the copied sources after execution and compares the returned source/runtime binding. A stale module already imported in the parent is not used for the transformation. Direct calls to the internal Broker-based normalizer refuse unbound execution. `FRESH_ISOLATED_SOURCE_SNAPSHOT` describes source execution provenance; it is not scientific transformation or feature certification. Runtime distributions are fingerprinted rather than archived. The local OS account and installed runtime remain trusted.

The owned child has a 600-second lifetime, a 1 MiB result-output bound and an 8 KiB error-output bound. Timeout or caller cancellation kills and reaps it. These are infrastructure envelopes, not scientific stopping rules. Required sources are processed month by month; normalized bytes are staged, flushed and limited to 512 MiB before import. Existing snapshot limits, including 500,000 declared observations, still apply. An interrupted compound operation can leave committed source or normalization records without a returned final result. Inspect the registry before retrying; retries do not erase records or promise idempotent attempt identity.

## Time, coverage and protected ancestry

Every requested decision instant requires the source month containing that instant minus 900 seconds. Supply exactly those symbol/month bundles within the adopted 2020-2025 archive profile. Missing, duplicate or irrelevant bundles fail. Required pre-2020 source time remains outside the profile and is recorded explicitly. A wholly empty requested window fails with `NO_OBSERVATIONS` rather than producing a snapshot.

Rows retain the exact exclusive bar end. A December 31 23:45 source open ending January 1 00:00 belongs to the later decision-time container. It does not become unseen or independent by moving containers. The final December 2025 source bar ends in 2026 and falls outside the adopted corroboration universe. At the beginning of 2020, the initial 00:00 observation has no preceding source bar within the profile and remains absent.

All known source ancestry is checked before raw reads. Development cannot consume assessment, operational or unreleased ancestry hidden behind another source wrapper. Registry blob integrity, exact archive/checksum/CSV agreement, full original success/failure receipt semantics, provider-document receipt semantics and the retained quality audit are checked again. The same receipt validators are used for initial retention and later normalization; a caller-created source wrapper cannot substitute a weaker receipt policy. Ambiguous source rows fail even if they would lie outside the selected window. No row is selected before its full required source has been audited.

Each source retains counts of selected, before-start and at-or-after-end records. Counts include valid and invalid keyed observations. Output ordering is strictly `(time, instrument)`, independent of supplied source order. Invalid keyed bars supply nine null features; absent bars supply no row; genuine zero activity remains zero. An explicit assumed delay may extend beyond the universe without moving or dropping the row. Later calculations apply their actual information cutoff.

Catalog entries retain symbol-qualified identifiers and units. A joint BTC/ETH snapshot contains both catalogs; a BTC row has only BTC fields and an ETH row only ETH fields. The generic structural coverage table therefore counts the other instrument's feature keys as absent. Those counts do not mean the source supplied defective cross-instrument measurements. Applicable feature definitions and scientific missingness/eligibility remain separate requirements.

## Retained records and remaining authority

The utility retains an immutable `binance-normalization/1` source record with the exact request, source references, selected/excluded counts, invalid-row count, explicit delay, code snapshot, row file and unavailable pre-profile source months. Its ancestry binds the original source bundles, original failure receipts, complete quality rows and provider documentation. The final data snapshot binds that record and the exact normalized file and catalog; it stays `STRUCTURE_VERIFIED` with `scientific_readiness: false` and the existing unresolved scientific gates.

The data manifest's retrieval time describes this operation's retrieval of verified retained local copies. It is not substituted for a provider publication time or an original network receipt. Original source receipt times remain in their source bundles, including null retrieval claims for legacy failures without file/time binding. A declared latency scenario cannot repair those historical uncertainties.

Outcome label-information intervals, boundary exclusions, warmup eligibility, missingness assumptions, evidence allocation and scientific freeze are not decided here. The output can be used only through a later caller that enforces its permitted context and scientific plan. Existing protected data-window loading and complete registry backup/restoration continue to apply.

The [22 independent partition cases](../tests/fixtures/reference_binance_partition_cases.json) and their [expectations](../tests/fixtures/reference_binance_partition_expectations.md) were fixed before implementation inspection. They cover year/unit boundaries, null and absent observations, counts, ordering and invalid source selections. Integration tests additionally exercise authentication, committed-byte corruption, receipt validation, isolated source execution, cancellation/timeout, output bounds and backup/restoration. Run `python -B -m unittest discover -s tests -p test_binance_normalize.py` for this boundary.
