# Bound reference computations

`bound-reference/1` connects a completed formalization draft, its exact data snapshot and feature catalog, a data-bound raw measurement certificate, and a retained reference calculator. It implements bounded compilation and exploratory development execution. It does not complete semantic approval, composition certification, scientific plan/allocation/freeze or calibrated inference.

## Owned operations

The separate [composition certificate](COMPOSITION.md) checks the retained driver and exact candidate. Compilation by itself still grants no composition certification or scientific readiness. This addition does not change the bound-reference/1 request, warmup, outcome or execution semantics below.

The operator calls `compile_hypothesis(formalization_id, feature_certificate_id, reference_certificate_id, as_of, max_steps)`. Every argument is mandatory. The original formalization must be the accepted result of a completed `formalization/v1` job. The host verifies immutable identities, the original idea and authorized sources. The candidate, catalog and data identities must match exactly. A supplied source or a worker-created success claim cannot substitute for these records.

The reference certificate must retain its exact verified package, fixed expectations and compatible Python runtime. An intact older package can remain usable after the installed source changes: `STALE` installed currency alone does not revoke retained conformance. A missing or corrupt package cannot use this exception. Raw feature certificates must bind the intended snapshot and exact catalog. Their historical availability qualifications remain unchanged.

Compilation retains the certified calculator files unchanged plus a separately versioned binding driver. One fresh isolated Python process validates AST types, catalog identity, feature-reference closure, units and the explicit request. Parameter origins remain bound to the prior validated completed formalization assessment. The parent checks returned identities and resource bounds without interpreting the AST using a newer in-memory calculator. Neither compilation nor the formalizer's equivalence assertion independently establishes faithful natural-language meaning.

`execute_development(compiled_id)` accepts only that identity, with no candidate, time, budget or data override. It denies assessment and corroboration before loading dependencies, blobs or rows. Compilation itself does not grant a formalizer new protected source access. Data admission preserves the existing prohibition against laundering protected raw ancestry through a development wrapper. Legitimately released assessment feedback remains inherited exposure; it is not erased or treated as unseen history.

The CLI uses the exclusive registry writer lock, like the existing certification commands:

```powershell
python -B -m trading_researcher compile-hypothesis --directory <registry> --formalization-id <id> --feature-certificate-id <id> --reference-certificate-id <id> --as-of 2020-01-01T00:59:59Z --max-steps 10000
python -B -m trading_researcher execute-development --directory <registry> --compiled-id <id>
```

These dates and limits illustrate the synthetic fixture, not a default scientific plan. Successful commands return JSON and exit zero; retained compilation/execution gaps exit two. Initial invalid requests exit nonzero without a success record. When a server already owns the registry, use the corresponding operator RPC operations.

## Data, results and retained versions

The row selection includes decision-time lookback and any outcome lookback extending before the first decision after accounting for its horizon. It is clamped to the same snapshot and partition. Missing warmup stays explicit. The loader never substitutes a later bar or silently truncates a required window to fit its 100,000-row bound. Prior inputs needed by an outcome remain available even when the existing dependency rule correctly returns `REVIEW_REQUIRED`.

An owned fresh child executes the retained calculator with hash-bound rows and request. It writes ordered cases to a bounded external JSONL blob. A separate sequential fresh child repeats the deterministic computation from the same hash-bound selected rows and compares every canonical case byte, the complete header and the descriptive contrast. This also rejects internally consistent but fabricated changes to non-eligible states or values. It grants no additional data access and deliberately adds a second bounded computation. The parent checks both response identities and environments and rechecks retained dependencies before committing the blob reference and immutable result. This exact replay verifies the returned result against the retained implementation; it is neither an independent market-data source nor a second scientific estimator.

The binding driver is retained and independently tested; the earlier reference certificate does not certify newly added broker or driver code. Source packages contain the reference certificate's exact files plus this driver. Python and its imported standard library are fingerprinted rather than archived. The existing owned-child timeout, bounded stdout/stderr, cancellation, kill and reap behavior applies to each child. Parent input selection/copying and final integrity checks are outside the child timeout. The trusted host code and OS account remain outside this boundary; process isolation is not an OS sandbox.

`compiled-hypothesis/1`, `reference-execution/1` and `binding-source-package/1` are protected namespaces. Attempts and interruptions are durable and visible through `inspect_bound_computations(limit=...)`. Complete backups preserve the data, cases and source packages needed by this path. Results inherit the candidate's and data's exposure, have descriptive authority only, and set `scientific_readiness` to false. No completed-outcome monitoring event, assessment release, evidence judgment or capital authority follows.

## Verification and remaining work

The independent [fixture](../tests/fixtures/reference_binding_cases.json) and [authorship note](../tests/fixtures/reference_binding_expectations.md) were fixed before implementation review. Six numerical cases cover the exact baseline contrast, delayed availability, absent and invalid rows, a resource stop and causal decision warmup. Twenty-six admission/lifecycle expectations cover identity, authorization, retained versions, protected data and subprocess failures. Additional adversarial regressions cover stale parent code, outcome warmup and malformed execution responses. CLI and complete-backup tests exercise an actual owned synthetic registry.

Current commands, outcomes, source hashes and limitations are recorded in [binding verification](../docs/reviews/implementation-2026-10-25/binding-verification.json). Synthetic verification establishes only this exercised infrastructure behavior. Scientific data/rights/PIT acceptance, independent semantic mapping, broader composition/dependency certification, calibrated inference, atomic scientific freeze, real LLM research and full monitoring remain pending.
