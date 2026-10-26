# Retained formalization records

The [independent meaning-review assessment](MEANING_REVIEWS.md) separately records whether a complete controller-observed comparison process satisfies that prerequisite for an exact target. Model judgment remains fallible and does not authorize scientific execution.

This implements the draft boundary of IF-03/04 under D002/D074. The worker operation `record_formalization` requires a current formalizer lease and an idea plus catalog already authorized to that attempt. The original idea artifact and its exact text remain separate from the candidate. Candidates admitted under the retained-envelope size/depth bounds are retained, including unsupported expressions or ambiguous meaning. Neither a draft nor an accepted operational submission grants scientific readiness.

A `formalization-record/1` contains its idea/catalog references, the exact original idea body, the exact submitted candidate, a semantic report, UTC creation time, a deterministic structural assessment, and `scientific_readiness: false`. It is immutable and inherits the complete attempt/base exposure. The controller also journals an observation or a typed gap, linked to the retained draft. Generic artifact writes cannot impersonate this record namespace. No new registry table or scientific state migration is needed for drafts.

The complete retained envelope, including original text, assessment and ancestry, must fit the existing 1 MiB/40-level serialization bound. A request that fits the transport limit may still exceed this retained-envelope bound. Such a request returns `RESOURCE_GAP` without committing a partial draft; its candidate payload has not been retained, and the caller must keep it for a supported larger-content path or resubmit within the bound. Existing idea records remain untouched. [External storage](STORAGE.md) now retains host-imported files; direct large candidate submission through this formalizer operation remains unimplemented.

Context admission enforces the draft's host creation time and all known ancestor record-availability bounds, including through generic wrappers. A derived typed source inherits that bound. Unknown availability of legacy/raw sources is still unverified; this rule does not reconstruct historical market vintages.

The semantic report has `status` (`equivalent`, `ambiguous`, or `different`), `segments` and `differences`. Each segment retains `text`, a candidate JSON-pointer `path`, and an `interpretation`. Concatenating segment text must reproduce the original idea text exactly; each path must exist. An equivalence assertion cannot carry declared differences. Ambiguity or difference prevents structural advancement. Matching these fields records a traceable formalizer assertion; it does not prove natural-language fidelity or independent review.

## Executable-candidate structure

`hypothesis-exec/1` requires exactly: `schema`, `idea_ref`, `claim_kind`, `estimand`, `scope_ast`, `condition_ast`, `outcome`, `comparator`, `horizons`, `test_universe`, `parameter_origins`, and `feature_refs`.

All five adopted claim kinds (`difference`, `association`, `change`, `boundary`, `interaction`) remain representable as retained candidates. This first structural implementation supports the canonical difference only. Other estimators are retained as `EVALUATION_GAP`; they are not translated into a difference or rejected as market claims.

For the supported difference:

- `scope_ast` and `condition_ast` are complete `research-ast/1` programs of Boolean type. Their catalog hash binds the supplied `feature-catalog/1` source, whose `features` map contains the versioned type/unit definitions.
- `outcome` contains exactly `program` and `scale`. The program is a `research-ast/1` expression to be evaluated at the separately declared future observation anchor. Scale `binary_probability` requires Boolean output and unit `ratio`; scale `quantity` requires real output. Forward outcome construction and maturity checks are not performed by this draft validator.
- `estimand` contains exactly `kind` (`conditional-minus-scope-mean/1`), `unit`, `weighting` (`equal_rows`), `missingness` (`scope-true-outcome-observed/1`), `condition_unknown` (`exclude-from-condition-retain-in-scope`), `nuisance_fit` (`none`) and `direction` (`positive`, `negative`, `nondirectional`). This encodes mean(Y where C and S) minus mean(Y where S), including both terms' common eligible scope. Unknown C is not true; it does not silently remove an otherwise eligible S row from the whole-scope baseline.
- `comparator` is exactly `{"kind":"whole_scope"}`. A condition-versus-complement request is a different meaning and remains a gap.
- `horizons` contains `grid_seconds: 900` and positive integer `outcome_bars`. `test_universe` contains a nonempty unique instrument list plus exact UTC `start`/`end` instants (inclusive start, exclusive end), and an explicit `data_snapshot_ref`. These are requested scope, not verified data rights/availability or an allocation grant.
- `feature_refs` exactly enumerates the programs' versioned feature references. It is not a list of certificates.
- Each `parameter_origins` entry contains `path`, `basis`, `source_refs`, and `rationale`. Basis is `preexisting_specification` or `development_observation`. Every literal value, lag/window length and declared outcome horizon must have exactly one origin, pointing to an existing candidate path. Source references must be authorized to the attempt. The host preserves all additional exposure regardless of selective citations.

The result is `STRUCTURE_CHECKED` or `RETAINED_GAP` with code, reason and reopening condition. Missing feature definitions, type/time/resource errors, unsupported estimators and semantic uncertainty remain distinct. Even `STRUCTURE_CHECKED` is still at FORMALIZING: it needs independent meaning/feature certification, actual data/provenance and exposure review, a compatible calibrated evaluator, complete plan/allocation and atomic scientific freeze before execution authority exists.

This draft boundary does not assign effect thresholds, approve a monitoring method, classify market evidence or issue a scientific certificate. It preserves the candidate's requested horizon and unit; a missing evaluation profile cannot be repaired by silently changing them.

The [auxiliary research path](AUXILIARY_RESEARCH.md) adds optional epoch-bound model formalization. Its frozen job names the original idea, catalog and definitions; `record_formalization` requires `provider_call_id` and exact agreement with that attempt's timely retained public response. A separate reviewer can assess the accepted draft or its retained uncertainty under the same total budget. Neither role's output establishes scientific readiness, and synthetic/manual/provider-label assertions cannot establish actual independent model judgment.
