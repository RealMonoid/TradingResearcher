# Raw measurement certification

`binance-raw-features/1` binds the existing nine raw fields per instrument to one owned data snapshot. The profile covers BTCUSDT and ETHUSDT spot 15-minute bars and implements a bounded part of IF-04 under [research-contract/1.0 section 14](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#14-open-14-automatic-certification-within-an-approved-envelope). It introduces no new scientific meaning.

The fields are open, high, low, close, base volume, quote volume, trade count, taker base volume and taker quote volume. Definitions retain source columns, scalar domains, symbol-specific units, expected exclusive bar-end anchors, the timestamp-unit transition, explicit assumed availability and missingness rules. Trade count remains an exact integer-valued real/count measurement. There is no fitted state or rounding. One-symbol snapshots bind nine definitions; two-symbol snapshots bind eighteen. General compositions remain typed AST expressions rather than a catalog of allowed hypotheses.

## Operation and evidence

```powershell
python -B -m trading_researcher certify-features --directory <owned-registry> --data-snapshot-id <snapshot-id>
```

The equivalent operator RPC is `certify_features(data_snapshot_id=...)`. No code, path, expected-result or semantic override is accepted. The CLI needs the exclusive registry writer lock; use operator RPC when a server already owns that registry.

The host retains the exact application/specification/fixture package, records a started attempt and makes a complete verified private database/blob copy. One fresh `-I -S -B` child runs the fixed checks and directly invokes the bound normalizer. It launches no descendant normalizer process. Complete source replay compares row hashes, catalogs, coverage, assumed delay, calendar scope, source identities and selection counts. Only new replay artifact IDs and the replay's local-copy read time may differ. Original receipt qualifications and exposure remain bound to the original snapshot.

Before commitment, the parent validates the exact response schema, fixed definitions, check counts and replay summary. It rechecks the original data closure, retained/installed application package and Python/runtime fingerprints. A pass creates immutable `feature-definitions/1` and `feature-certificate/1` records atomically. The host sets authority itself. Execution/report failures retain `CERTIFICATION_GAP` without definitions. Invalid requests, authentication and inadmissible initial bindings reject before an attempt starts. Cancelled or abandoned attempts remain visible.

Definitions inherit data classification, source identities, exposure and creation-time availability. Assessment definitions cannot enter discovery/formalization as development data. Generic source/worker writes cannot mint the reserved namespaces. Certificates are host work products, not automatically released feedback.

`feature_certificate_status(certificate_id=..., data_snapshot_id=...)` optionally requires the intended snapshot and rejects a mismatch. Status is `CURRENT`, `STALE`, `QUARANTINED`, `CERTIFICATION_GAP` or `INVALIDATED_BY_DEPENDENCY` after an applicable [technical revocation](REVOCATIONS.md). Any application source change conservatively makes installed-package currency stale. Currency grants no scientific execution permission. `inspect_feature_checks(limit=...)` returns bounded durable attempt history.

## Independent expectations and limits

The validator pins the adopted contract and independent [archive](../tests/fixtures/reference_binance_cases.json), [quality](../tests/fixtures/reference_binance_quality_cases.json), [partition](../tests/fixtures/reference_binance_partition_cases.json) and [feature](../tests/fixtures/reference_feature_cases.json) fixtures. The feature fixture and [authorship note](../tests/fixtures/reference_feature_expectations.md) were fixed before implementation inspection. Its 18 definitions and ten hand-calculated projections extend 43 archive, 32 quality and 22 partition cases. Host/API admission probes have separately reported coverage; they are not implied by the child counters.

Source packages are bounded to 128 files and 16 MiB. Existing row/file limits apply. The owned child has a 600-second lifetime and bounded stdout/stderr; timeout, overflow and cancellation kill and reap it. Backup creation and final checks fall outside that lifetime. Final checks hold the registry lock. The private copy needs space for all committed blobs, uses no writable hardlinks to live data and retains its credential only locally until cleanup.

The certificate covers exercised raw measurement implementation and exact replay. Invalid keyed bars remain all-null, absent bars remain absent, genuine zero activity remains zero, and other-symbol fields stay absent. An assumed delay remains a scenario, not historical publication evidence. Immutable snapshot gates are not rewritten.

Provider truth, historical PIT/vintage, scientific acquisition/rights acceptance, hypothesis semantics, composition/dependency certification, calibrated inference, scientific execution/freeze and capital authority remain separate. Retained application packages survive complete backups; a public revalidation operation using only a retained feature package is not yet provided. Python distributions are fingerprinted, not archived. The trusted OS account and installed host code remain outside this boundary. This is not an OS sandbox, proof of bug absence or market evidence.
