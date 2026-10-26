# Technical dependency revocation

This implements the supported technical-version portion of D083, [research-contract/1.0 section 13](../docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md#13-open-13-dependency-effects-and-applicability) and IF-09. A technical defect can prevent new use without erasing historical records or declaring an empirical claim false. It does not decide whether the supplied defect evidence is scientifically correct.

## Operator interface

```text
revoke_dependency(key, dependency_id, reason, evidence_refs)
inspect_dependency_use(artifact_id)
```

Only the authenticated operator can issue or inspect revocations. A request needs a nonempty defect reason and one through 32 existing evidence references. The host creates an immutable `dependency-revocation/1` operations record with the exact request, version selector, inherited exposure, creation time and affected artifact IDs under the supported typed bindings at that event. Same key and exact request returns the same record; a changed request conflicts. Generic source and worker writes cannot mint this namespace. Pre-upgrade operator sources using the same schema label are not controller-issued revocations.

Supported targets are owned `data-snapshot/1`, `feature-definitions/1`, `feature-certificate/1`, `implementation-certificate/1`, and reference/feature/binding source packages. Non-package targets identify the exact immutable version record. A package selector identifies its schema and complete file-hash footprint. New timestamps, package IDs or certificates cannot reset an explicitly revoked package with identical retained bytes. Different package bytes are a different version; this is not semantic similarity detection. New data versions are not invalidated merely because they supersede an older snapshot, and still require all normal admission checks.

Inspection reports `INVALIDATED_BY_DEPENDENCY`, `NOT_REVOKED` or `UNKNOWN_BINDING`. `NOT_REVOKED` means only that no matching recorded revocation was found in the supported technical closure. It does not mean valid, scientifically accepted or suitable for deployment. Unknown consumer schemas remain `UNKNOWN_BINDING`. The retained affected set describes the event time; fresh inspection also covers later objects that use the revoked version. There is no silent un-revoke or deletion operation.

## Actual use versus provenance

The dependency walker follows explicit technical fields: compiled snapshot/certificate/package identities; executed compiled identity; plan compiled identity and every declared development diagnostic; certificate package/definition/snapshot identities; feature-definition snapshot input references; measurement snapshot input; and the existing bootstrap, diagnostic, population, study and final-calibration input/result links.

Generic `source_refs`, `exposure`, `supersedes`, scientific genealogy and conflict notes do not become hard invalidation edges. They retain their original provenance/exposure meaning. In particular, a plan can depend on another diagnostic's compiler even when its own compiled hypothesis is unaffected. A single final-calibration series also depends on its actual retained development study.

This is a bounded mapping of existing schemas, not a new contradiction ontology. It does not infer aliases of data snapshots, certify an arbitrary user schema, or implement future economic-policy applicability and evidence publication. Those future consumers must explicitly bind and check their technical versions.

## Enforcement and history

Data loading checks before scanning and again before returning rows. Certification and compilation check retained package versions before launching validation/calculation and again before commitment. Certificate status can report `INVALIDATED_BY_DEPENDENCY`. Bound execution, every plan diagnostic and the shared downstream plan/execution boundary check their actual dependencies. Final calibration checks the retained development study before new use.

Worker measurement authorization checks the snapshot before computation, before delivery and before replaying a cached tool result. A revocation during measurement retains the completed calculation as undelivered rather than leaking a new result into discovery. Revocation during a study retains and charges completed work, but settles the world as a technical failure with no permitted decision. It cannot silently refund the work or count it as a valid calibration world.

`get_artifact` and historical inspection remain available. Completed plan request keys still return their original historical plan; `inspect_evaluation_plan` now includes separate fresh `dependency_use`. A historical result is not permission to consume it again. Future scientific freeze must recheck dependency usability within its own atomic transaction. Original evidence outcomes are never rewritten by this operation.

The [implementation checkpoint](../docs/reviews/implementation-2026-10-25/REVOCATION_INTEGRATION_2026-10-26.md) records independent tests, integration checks and remaining limits. Unknown historical availability, rights, model-training exposure, statistical adequacy, calibration and the first genuine research cycle remain separate work.
