# Versioned discovery inquiry profile

`profiles.build_profile(base_profile, contract_bytes)` constructs
`discovery-inquiry-feedback/2` under accepted D096 /
[inquiry-feedback/1.0](../../docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md).
It returns a separate candidate profile and provenance manifest. It does not
install a worker, activate an epoch or grant spending/access authority.

The original two prompt strings remain exact prefixes. The accepted addendum is
appended to each; top-level and optional per-perspective prompt versions change.
Every other input value, including model, reasoning parameters, source
presentation, tools, output limits and aggregate budgets, is preserved. Returned
objects share no mutable state with the input. A prompt over the existing 8,192
character limit fails before returning a candidate; no original meaning or rule
is truncated. Applying this version twice is rejected.

Version 2 includes the explicitly approved diagnostic-quality clarification:
record completeness, citations or another model's agreement do not establish a
good diagnosis. Evaluate factual fit, substantive support/discrimination,
proportional uncertainty and action relevance separately. Keep a corroborated
diagnosis distinct from a useful action; luck or profit does not validate a
wrong explanation. DQ-01–DQ-03 remain behavioral specifications, not passes
from prompt construction. The unpublished version-1 source and test evidence
remain retained with the source-reconciliation record.

The manifest binds the exact approved owner bytes, appended instructions, base
and derived canonical profile hashes, and original prompt versions.
`verify_profile(bundle, base_profile, contract_bytes)` recomputes that exact
construction. It does not authenticate an externally supplied base, assess
instruction quality or replace controller admission. The caller must authorize
the base and bind the complete installed source closure, actual provider wire,
data/context exposure, tools, resource disposition and independent checks before
an eligible future run. A manifest cannot certify its own behavioral compliance.

## Existing record and control path

No memory schema changes are needed. Allowed `idea` question/uncertainty,
`observation` text/measurement, `gap` reason/reopen condition and
`research_experience` interpretation/next_action fields can carry compact public
purposes, findings, correction/use links, scope and review triggers. Full request,
response and tool-result artifacts preserve chronology; prior content stays
immutable. Existing source references and attempt/context lineage remain
authoritative. This profile requests public investigation summaries, not private
reasoning transcripts or additional mandatory forms.

An explicit source reread may repeat a finding already present in the initial
context. A record before that reread establishes storage order, not a purpose
before first exposure. Qualification must inspect the complete earlier input.

For a targeted action, an adequate already-bound purpose can suffice. Otherwise
a permitted existing record must retain that purpose before the targeted result.
The profile supplies no extra tool or model-call allowance. Missing interface,
information or resources remains a concrete gap. A tool-success fixture cannot
show that a model will select a good investigation or retain a faithful purpose.

| Rule | Profile instruction / existing mechanism | Evidence boundary |
|---|---|---|
| I1/I2/I6 | Fallible sourced diagnosis; feasible clarification; open exploration; inspectable basis | Appropriate model diagnosis/action needs actual model-produced cases |
| I3/F1 | Purpose and possible consequences before targeted result; open exploration may state purpose alone | Controller chronology can be tested separately from rationale quality |
| I4/I5 | Original idea, diagnosis, explicit correction and semantic difference retained | Append-only records/lineage are controls; faithful revisions still need review |
| I7 | Existing caps/checkpoints, no forced reflection/alternation or scientific negative from a resource stop | Existing reservation/stop controls remain authoritative |
| F2 | Actual result, interpretation, next action and independent scientific verdict remain distinct | Typed public records do not grant scientific authority |
| F3/F4 | Scoped provisional heuristic/use before outcome; correction history; release and exposure inheritance; isolated perspectives | No prompt grants forbidden access or changes a frozen snapshot |
| F5 | Conformance, episode usefulness, comparative benefit and economics separate; full failed/pending cohort and burden | No comparative/economic benefit is established by construction or scripted fixtures |

All twelve AC cases remain behavioral specifications. Applicable scripted tests
can establish only their stated storage/control paths. Actual model-produced
diagnosis/action checks, indeterminate judgments and benefit assessments must be
reported separately. Unknown benefit is not a new gate before otherwise valid
bounded work. Scientific methods still serve economically useful opportunities
after realistic costs and risk; neither immediate profit nor narrative rigor is
a substitute for the existing evaluation and policy contracts.

## Qualification and integration status

The user-approved [diagnostic behavior case kit](DIAGNOSTIC_CASES.md) now supplies four DQ-01–DQ-03 base cases and three targeted countervariants through the existing source/context and researcher APIs. Facts and protected expectations are separate; the collector never infers a semantic pass from accepted output. Actual model-produced cases and independent assessment remain necessary. The kit adds no provider dispatch, grant, budget reset or change to this profile's exact source binding.

Focused commands:

```powershell
python -B -m unittest discover -s tests -p 'test_inquiry_profile*.py'
python -B -m unittest discover -s tests -p 'test_research*.py'
python -B -m unittest discover -s tests -p 'test_memory.py'
```

See the dated qualification evidence in the existing implementation record for
checks actually executed and remaining cases. The old worker does not yet admit
the separately qualified inline body-table/ancestry packet. This constructor
does not solve that runtime binding, change old pinned modules or reinterpret
earlier wire counts as counts of the new prompt. Rebuild and count the complete
future packet, independently qualify affected controls/behavior, and complete
resource/currentness admission before dispatch. Prior profiles, failures and
spent allowances remain preserved. Rollback chooses an earlier approved future
configuration through existing governance; it does not erase exposure or costs.
