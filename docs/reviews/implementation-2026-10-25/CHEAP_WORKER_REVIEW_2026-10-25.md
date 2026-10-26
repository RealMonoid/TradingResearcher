# Bounded use of cheaper models: coworker repository review

Date: October 25, 2026. User source: [claude-coworker-model](https://github.com/imkunal007219/claude-coworker-model), inspected commit `6dffb4adc2e8a73bf50e5c1dd3e3c641ecf14e23`. The user permits cheaper models for suitable work only if framework quality is protected. This review proposes boundaries; it does not activate a new model, routing policy or provider.

## Finding from actual source

The repository is a small MIT-licensed set of Python CLI wrappers with a Bash installer. It is not intrinsically limited to Claude: its API wrappers accept an OpenAI-compatible endpoint and a configured model. Its Claude-specific template teaches the primary coding assistant when to delegate.

[`ask-kimi`](https://github.com/imkunal007219/claude-coworker-model/blob/6dffb4adc2e8a73bf50e5c1dd3e3c641ecf14e23/tools/ask-kimi) reads the selected files and asks a model for a summary under 800 words. It requests source locations but does not verify them or completeness. Invalid text decoding is replaced. Reading and summarizing are materially different: a plausible summary can omit a constraint that the primary model never sees.

[`kimi-write`](https://github.com/imkunal007219/claude-coworker-model/blob/6dffb4adc2e8a73bf50e5c1dd3e3c641ecf14e23/tools/kimi-write) writes any nonempty returned content directly to the selected target with write mode, after removing possible Markdown fences. It prints the finish reason afterwards but does not reject a nonempty token-truncated response before writing. There is no independent correctness gate or protected output namespace in that script. Token counts printed to stderr do not provide our persistent aggregate currency reservations, immutable request/source binding or model/version/UTC records.

[`extract-chat`](https://github.com/imkunal007219/claude-coworker-model/blob/6dffb4adc2e8a73bf50e5c1dd3e3c641ecf14e23/tools/extract-chat) is deterministic, but deliberately excludes tool calls/results and other message classes. That may serve a reading convenience; it cannot replace this project's complete provenance archive. The [delegation template](https://github.com/imkunal007219/claude-coworker-model/blob/6dffb4adc2e8a73bf50e5c1dd3e3c641ecf14e23/CLAUDE.md.template) asks the assistant to use summaries instead of original reading and mandates delegated documentation. Those instructions are not adopted.

No repository script was executed, no dependency installed, no credential supplied and no new API inference performed for this investigation. These are bounded static findings, not a complete security audit.

## Existing framework fit

D034 favors deterministic workflows for specified operations and bounded tools for open reasoning. D079 freezes model/prompt choices and shared call/token/time limits. The current auxiliary task profiles already carry an explicit model identifier, but the installed live OpenAI adapter currently supports one fixed model/tariff. A generic profile field is not evidence that arbitrary cheaper models are compatible or validated.

Our scientific evaluator remains deterministic and independent of any LLM. Changing the model that invents or formalizes hypotheses can change the research process; it cannot be introduced as an invisible cost optimization. A cheap model must never prune scientific sources, declare empirical success, adjust evidence thresholds, select away failed attempts or rewrite canonical commitments automatically. Expensive models have no exemption from those boundaries.

## Recommended order

| Work | Preferred mechanism | Acceptance boundary |
|---|---|---|
| Exact arithmetic, usage totals, fixed status fields, manifest/link checks, source slicing | Existing deterministic code/templates | Exact expected outputs and retained source identity; no model call needed. |
| Optional wording of an operational report or other non-authoritative draft | A cheaper model may be evaluated later | Fixed input facts remain separately displayed; output is a draft until appropriate validation. No autonomous scientific claims or canonical writes. |
| Source-location or documentation suggestions | Optional cheaper-model candidate generation | Check proposed locations/quotations against original bytes. A matching quotation does not prove that all relevant evidence was found. |
| Hypothesis invention, faithful semantic mapping, independent substantive review | Explicitly selected and qualified role model | Preserve the current approved process; evaluate any material routing/generator change before activation. |
| Backtests, estimates, scientific classifications | Deterministic certified implementation | Never delegated to a language model as the numerical/evidential authority. |

Do not classify work as low-risk merely because it is called reading, documentation or boilerplate. A generated test can encode the same mistaken assumption as the implementation. A polished report can silently change a qualification. Checks must match the actual claim; schema validity and another model's approval do not establish semantic correctness.

A future narrow trial should freeze the task/model/source profile, retain failures and full originals, compare with fixed independent expectations, count review/retry/escalation cost, and default to a retained gap when validation fails. Escalation is another counted call, not permission to reset the budget. All calls retain requested/reported model identity, public version versus unknown immutable snapshot, timestamps, input/output counts and cost basis. There is no promise of zero model errors; protection comes from limiting what unverified output may change.

## Academic evidence and its limits

[RouteLLM (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/5503a7c69d48a2f86fc00b3dc09de686-Abstract-Conference.html) evaluates learned routing between stronger and weaker models. Its [Berkeley project page](https://sky.cs.berkeley.edu/project/routellm/) reports particular cost reductions at 95% of a reference model's benchmark performance. That is an explicit performance target, not a guarantee of no quality reduction for every request or this framework.

[FrugalGPT (TMLR 2024)](https://lingjiaochen.com/papers/2024_FrugalGPT_TMLR.pdf) demonstrates adaptive model selection/cascades on evaluated tasks. It supports investigating task-specific economical routing, not assuming that one cheap worker plus one stronger reviewer will preserve all scientific information. Neither paper validates our market-research process or a universal switching threshold.

Conclusion: preserve the ability to configure cheaper models for qualified helper roles, use deterministic code first, and adopt no automatic cheap-worker routing now. This repository provides a useful pattern but its direct summary/write workflow does not satisfy our current evidence and accounting boundaries. No user decision is required to retain this conclusion; a concrete model/role trial can be proposed when a measured need exists.
