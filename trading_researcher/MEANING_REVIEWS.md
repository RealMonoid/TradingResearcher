# Independent meaning-review assessment

The [meaning-review module](meaning_reviews.py) implements the existing independent semantic-review process prerequisite under D002/D074. It binds a review to an exact immutable formalization, its preserved original idea, catalog, owned feature definitions and original epoch. It does not give an LLM authority to judge empirical market success.

Use `meaning_reviews.profile(existing_settings)` to freeze the substantive `meaning-comparison/1` protocol with the selected model and bounded generation settings. Register a separate `semantic-review/v1` worker and job in the formalization's original epoch, then use the existing controller-owned provider path. A provider label or an arbitrary prompt demanding a favorable answer does not qualify.

The protocol compares direction, scope, condition, comparator, outcome, units, timing, weighting, missingness, unknown-condition behavior and parameter origins. Formalizer assertions and instructions embedded in source artifacts are untrusted material. Equal answers on one dataset do not establish equivalent meanings; unspecified meaning remains uncertain.

After the declared jobs finish, the operator calls:

```python
assessment = operator.call(
    'assess_meaning_review', key='comparison-v1', formalization_id=target_id)
current = operator.call(
    'inspect_meaning_review', assessment_id=assessment['id'])
```

The controller includes every registered review job for that exact target, all attempt generations and their recorded responses. A later favorable answer cannot erase an earlier critical opinion. Pending jobs, unverified provenance, accounting failures, missing completion, different meanings and uncertainty retain typed gaps. Transport failures remain visible under the existing bounded retry policy.

`independent_semantic_review: SATISFIED` requires a structurally admitted candidate, the fixed protocol, authenticated role separation and completed controller-owned review without unresolved gaps. A faithfully retained unsupported idea remains nonexecutable. Historical timely calls can be assessed after epoch expiry without renewing the epoch or authorizing another call.

The immutable assessment stores its complete review inventory and policy source hashes. `inspect_meaning_review` checks currency before use. New review jobs, attempts or changed policy sources make old assessments stale; stale results report `NOT_SATISFIED`. Reusing a key with changed inputs is rejected. Earlier `semantic-review-record/1` artifacts retain their original `UNVERIFIED` field and are not rewritten.

The positive result establishes an observed review process for one exact target. The model's judgment remains fallible. It is not a proof of natural-language equivalence, approval of new scientific meaning, feature certificate, data acceptance, evaluator calibration or scientific freeze. This module does not detect semantic clones across arbitrary newly registered formalizations. Trusted operator and OS boundaries remain in force.

The [focused tests](../tests/test_meaning_reviews.py) and [independent adversarial tests](../tests/test_meaning_reviews_adversarial.py) cover missing/conflicting reviews, stale inventories and sources, prior attempts, epoch separation, forged provenance, unsupported targets, historical completion and backup/restart. Their replies are mocked. The separately frozen [eight-case fixture](../tests/fixtures/meaning_review_cases.md) specifies a bounded live comparison: retain every planned case and failure, without changing expected answers. Actual observations have separate dated evidence.

The [October 26 live observation](../docs/reviews/implementation-2026-10-25/MEANING_REVIEW_OBSERVATION_2026-10-26.md) records all eight expected judgments in the corrected complete comparison, with earlier incomplete attempts retained. Only two structurally admitted faithful mappings satisfy this process prerequisite. General model quality and downstream scientific admission remain unverified.
