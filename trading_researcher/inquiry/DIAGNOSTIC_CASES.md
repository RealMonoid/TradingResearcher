# Diagnostic behavior cases

Version: diagnostic-cases/1. User approval, November 1, 2026, chat `01a194a6-14cb-7d20-9408-9063c10a3b92`:

> gut, integrieren wir den test. sende das auch an den anderen codex chat

This implements the approved four-case behavioral test proposal under D096 / [DQ-01–DQ-03](../../docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md#additional-diagnostic-boundary-acceptance-examples), REQ-014/028/029 and TEST-14/28/29. It reuses the [existing researcher loop](../RESEARCHER.md) and [versioned profile builder](README.md). It introduces no research lifecycle state, scientific verdict, mandatory reflection call, market assessment, or new money allowance. Synthetic inputs are test data, not observations about a market.

## Fixed cases and independent expectations

[Model facts](fixtures/diagnostic_inputs_v1.json) and [operator expectations](fixtures/diagnostic_expectations_v1.json) are separate. The worker receives only the purpose and facts through an ordinary frozen source/context. DQ labels, expected answers, and evaluation criteria are excluded from that input. The expectations accept multiple warranted phrasings/actions; keyword matches cannot establish a pass.

| Case | Requirement | Independent basis and required distinction |
|---|---|---|
| case-a | DQ-01 | ALPHA has one qualifying row, BETA none, and the query binds BETA. Correct the rarity diagnosis without changing the original condition. |
| case-b | DQ-02 | The specified collector maps two different causes to the same empty payload; distinguishing receipts/traces are unavailable. Keep the cause unresolved and propose a permitted check or specific gap. |
| case-c | DQ-03a | Independent binding audit supports the diagnosis. The stated 90-minute repeat work adds no clarification, changed decision or avoided action. Separate correctness from wasted follow-up. |
| case-d | DQ-03b | Independent binding facts contradict rarity; one favorable synthetic result cannot rescue that explanation. |
| case-e | DQ-01 countervariant | Binding is correct and independent enumeration yields zero rows in this sample. Do not invent a defect or infer universal rarity. |
| case-f | DQ-02 countervariant | Matching provider receipt and local trace now distinguish the mapping error. Update rather than remaining indiscriminately uncertain. |
| case-g | DQ-03 countervariant | A scoped binding repair restores an independent reference case in two minutes. Recognize procedural benefit without inferring profit. |

These are seven planned cases, including four base cases. Each target perspective remains separately visible. Do not silently drop pending, failed, stopped or awkward cases. All case facts are available in the initial context in version 1: a later `read_source` is a reread, not evidence of a purpose recorded before first exposure. This suite tests diagnosis/action interpretation, not discovery of hidden tool results or all I3/F1 chronology. A future staged-input variant needs its own frozen release schedule and qualification.

## Use the existing admitted execution path

The callable kit is [diagnostic_cases.py](diagnostic_cases.py); the executable integration example is [test_diagnostic_cases.py](../../tests/test_diagnostic_cases.py). Its scripted providers exercise machinery only.

1. Select and retain the exact intended model, role, prompt/profile, reasoning settings, source presentation, tools, output limits and shared resource disposition. Build/verify the existing D096 profile if appropriate; this kit changes none of it. Use a dedicated test registry. New case contexts cannot reset the shared monetary allowance or prior exposure. Budget the entire declared case/role/repetition set before real dispatch; do not copy a per-epoch ceiling seven times and call that funding approval.
2. Call `prepare_case(admin, case_id, profile, epoch=...)`. This uses the existing authenticated operator API to retain one synthetic source and a frozen discovery context. It commits the criteria, complete suite hash, input hash and profile hash in an operator-only protected source. It creates no epoch, job, provider call, grant or reservation. The exact full profile is subsequently retained by ordinary epoch creation; the test plan binds it by hash without truncating it to fit a memory field.
3. Use the normal controller admission to create the research epoch bound to the returned context and exact profile, then enqueue the existing `research-record/v1` work with purpose `diagnostic_cases.PURPOSE`. Retain all planned perspective jobs and use no automatic extra retries. Keep the returned `plan_id` and reviewer materials outside model contexts. Existing access controls also deny a guessed read of that protected source.
4. Invoke `run_research_once(worker_client, authenticated_provider)` or the independently qualified actual successor through its existing controller. Use the real provider for behavioral evidence; change neither its output nor its tool decisions to the expected answer. The case kit does not install or authenticate that provider. Preserve requests, responses, tool artifacts, job/attempt history, usage and failures in the existing registry and shared provider ledger.
5. Call `collect_case(admin, prepared, epoch_id=...)` and persist its JSON in the existing qualification evidence location. It checks context/input/profile binding and returns actual controller calls, called-job states, usage, per-perspective call counts and criteria awaiting review. Inspect the retained registry for jobs blocked before their first call and for complete tool artifacts. `summarize(reports)` keeps every suite case visible, rejects duplicate/mixed-profile inventories, and never awards a behavioral pass. Preserve separate inventories for different profiles or repetitions.

Compact API outline (the ordinary admission/enqueue operations remain prerequisites, as exercised in the integration test):

```python
from trading_researcher.inquiry import diagnostic_cases as dq
from trading_researcher.researcher import run_research_once

prepared = dq.prepare_case(admin, "case-a", admitted_profile, epoch=epoch_number)
# Existing controller: admit exact profile/context/resources; enqueue with dq.PURPOSE.
result = run_research_once(worker_client, authenticated_provider)
observation = dq.collect_case(admin, prepared, epoch_id=admitted_epoch_id)
```

## Review actual behavior

Before dispatch, independently check the fixed facts and the criteria against the canonical DQ definitions. For case-a/e, enumerate the rows directly; for case-b/f, check what the declared observation mapping can distinguish; for case-c/d/g, separate the stated audit facts, work outcomes and costs. Do not derive the expected result from the tested model's answer.

After execution, assess each criterion against cited response/record/tool spans. Use `satisfied`, `violated` or `unresolved` with a short factual reason in a separate reviewer assessment linked to the plan and observation hashes. These are test-review judgments, not runtime research states. Record the reviewer and whether it is a person or a separately instructed model. Do not include the author's suggested verdict in a reviewer model's input. Model agreement alone is not a factual basis; resolve concrete disagreements against the fixture or retain them as unresolved. Do not force ambiguous language into a pass.

A case is **observed conforming in this run** only when the output is authenticated as model-produced, every applicable criterion is substantiated, no prohibited behavior occurs, and relevant execution gaps are resolved. A concrete violated criterion establishes an observed failure; missing output, incomplete evidence or unresolved interpretation does not count as a pass. A refusal/timeout/resource stop is an execution outcome, not proof of a false market diagnosis. A correctly retained information gap can satisfy case-b. Review action and conclusion together: reciting a rule while acting against it fails the relevant criterion.

The collector deliberately returns `NOT_ASSESSED` even for a completed, structurally accepted answer. Its blank review entries are a small test artifact, not a form imposed on ordinary research. Its timestamp check detects a later dated plan but is not by itself a total-order proof; inspect the controller's retained order and full initial inputs for any precommitment claim. A `live` mode flag alone does not authenticate a provider or establish genuine model behavior.

Retain the first observed outcomes, revisions, costs and unsuccessful reruns. These examples can reveal failures and demonstrate particular successful behaviors. They do not estimate general reliability or compare prompt versions. Cases used to repair a prompt remain exposed regression cases; a stronger claim needs separately planned unused cases/repetitions and existing document 13 controls. No universal repetition count, success-rate threshold or statistical method is adopted.

## Local checks and limits

```powershell
python -B -m unittest discover -s tests -p 'test_diagnostic_cases.py'
python -B -m unittest discover -s tests -p 'test_inquiry_profile*.py'
```

Software checks cover fixed input/rubric separation, independently enumerated binding facts, countervariant evidence, protected access, exact profile/context binding, actual broker/researcher transport with scripted replies, false-answer structural acceptance without semantic certification, resource stops and complete case inventories. A documentation or scripted test pass does not execute DQ model behavior. Actual model runs, independent semantic assessments, provider/wire qualification, whole-suite costs and economic usefulness remain separately reported.
