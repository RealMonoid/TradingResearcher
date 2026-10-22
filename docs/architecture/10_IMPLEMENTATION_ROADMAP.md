# Proposed Implementation Roadmap

The phase map below remains an engineering recommendation for review. The user has approved the planning principles below and designated the future experiment as the highest priority; its concrete scientific protocol and implementation remain to be settled. Execution is deferred because the user currently lacks the required data. This does not convert M0246's deferred implementation advice into an accepted historical decision. Preserve independent target roles even when a smaller engineering test exercises them sequentially.

## Adopted planning principles

On October 22, 2026, the user approved the following five consequences of the critique assessment. This approval concerns planning and prioritization within existing architecture constraints; it does not adopt Claude's entire analysis or prototype protocol, change scientific definitions, or resolve open decisions.

1. **Prioritize the first informative experiment.** Justify each prerequisite by its contribution to that experiment; do not require complete P1-P4 implementation by default.
2. **Specify the evidence budget before broad infrastructure work.** Make data availability, exposure, relevant effects, achievable precision and confirmation allocation explicit. Distinguish processing time from waiting for fresh outcomes; a model cutoff alone does not establish clean evidence.
3. **Assess formalization as an early bottleneck.** Track faithful H_idea-to-H_exec coverage, retained unsupported ideas, failure reasons and effort, rather than judging only successfully compiled hypotheses.
4. **Separate success and stopping criteria by question.** Distinguish technical validity, false-support control, planted-signal detection, economic usefulness and accelerated discovery/testing. Numeric thresholds and comparison designs still require the relevant scientific decisions.
5. **Use the smallest coherent implementation.** Reuse the Blueprint's modules and simple persistence approach where it satisfies the contracts. Logical roles do not require separate agents, services or databases; simplicity must preserve complete freezing, exposure history and traceability.

## Highest priority: bounded feasibility experiment

**Specification integration completed:** D069-D070 and [document 13](13_GENERATOR_FEEDBACK_AND_EVALUATION.md) now define the feedback/assessment/diagnostic contracts and TEST-28 through TEST-30. This completes the binding specification requested after the generator critique; the pilot-specific values, implementation and execution below remain pending. The economic question is profitable usefulness after realistic costs, not beating quantitative firms. A positive result or comparator superiority is not an entry requirement.

**Status: highest-priority future empirical milestone; execution deferred, with required market data currently unavailable to the user.** On October 22, 2026, after reviewing the [Claude critique assessment](../reviews/CLAUDE_CRITIQUE_ASSESSMENT_2026-10-22.md), the user instructed that an experiment should be done later and become the most important item in the actionable roadmap, then approved the planning principles above and reported the missing data. These are current-session instructions, outside the immutable conversation archive. They do not accept Claude's proposed protocol or resolve any open scientific contract.

**Preparation possible without market data:** draft the bounded research question and outcome interpretations; specify data fields, point-in-time availability/provenance and exposure requirements; outline formalization coverage/cost reporting and separate success criteria; identify the minimum implementation dependencies and synthetic-check design. Such preparation can proceed before data acquisition, but cannot establish attainable precision, calibration or market usefulness. No synthetic check or market experiment has been run.

**Data prerequisite before a market run:** identify and obtain a suitable versioned dataset, then verify its coverage, quality, access rights, point-in-time properties and exposure against the chosen protocol. The provider, acquisition route and any purchase remain unspecified. Data availability alone does not close the remaining protocol and implementation prerequisites.

The milestone should obtain informative evidence about the research process before broad infrastructure expansion. Its scope must preserve the distinction between technical feasibility, faithful formalization, false-support control, ability to detect relevant effects, economic usefulness and accelerated discovery/testing. A small pilot may assess only a declared subset; it cannot establish all framework goals or refute capabilities it does not exercise.

The following worklist makes the prerequisites visible. Its planning principles are approved; the deliverables remain pending. Preparation without data is distinguished above from later acquisition, implementation and execution; listing an open scientific question does not select its answer.

| Order within this milestone | Work item | Reviewable completion evidence |
|---|---|---|
| 1 | Define the pilot's question, scope, information target and resource limit | A short protocol outline states what positive, negative, inconclusive and technically invalid results would mean; identifies omitted target capabilities and forbids generalizing beyond them. Both framework goals remain visible; any acceleration claim needs its own comparison. OPEN-11. |
| 2 | Resolve the pilot's actual data and evidence requirements | Named market/instruments, data/version/availability rules, model and exposure boundary, relevant costs/execution assumptions, minimum relevant effect, dependence/precision, selection/stopping rules and confirmation allocation. Separate processing time from waiting for fresh outcomes. OPEN-05/06/11/12. |
| 3 | Specify the smallest faithful implementation and its checks | Identify only the P1-P4 capabilities needed for this protocol, including the relevant lifecycle and certification decisions. Preserve H_idea, typed gaps, independent evaluation, complete freeze and necessary access isolation. Include formalization coverage/cost and suitable null plus planted-signal checks. OPEN-01/04/14 and any required runtime/storage choices remain unresolved until explicitly settled. |
| 4 | Implement and run after the experiment receives a concrete scope and authorization | Retained inputs, candidates, failures, selection history, costs and reproducible evaluation with uncertainty; report only the capabilities actually exercised. |
| 5 | Decide whether and where to continue | Compare results with the predeclared criteria and budget. Distinguish an investment decision to stop from scientific rejection; justify additional infrastructure by observed needs. |

For items 1-3, apply document 13 to produce: (a) a feedback inventory with observation/interpretation/use boundaries and latency; (b) the selected assessment purpose, budget, unknown-effect assumptions/ranges and result interpretation; (c) diagnostic fixtures covering retained gaps, conflicting heuristics, pending outcomes and failed novelty searches. These can be specified without market data. Name the data/resource checkpoint for revisiting a deferred generator-improvement study; until then its benefit remains unverified. Do not require a comprehensive D059 meta-study before the first valid feasibility investigation.

Before using P0-P7 as a literal execution order, the pilot plan must explain which prerequisites are necessary and which broader capabilities can wait. Early calibration of a narrow pilot does not count as completion of full-framework P4. The smallest valid implementation may use ordinary modules, files and a transaction-capable registry as already proposed in the [Blueprint](09_IMPLEMENTATION_BLUEPRINT.md#minimal-coherent-implementation-shape); no storage product, agent count or new scientific policy is selected here.

## Proposed capability phases

| Phase | Deliverable and purpose | Entry dependencies | Exit evidence | Explicitly outside this phase |
|---|---|---|---|---|
| P0 — Source and authority | Source-limited architecture, decisions, rejections, definitions and open issues | Current continuation authorization; immutable archive | All required documents, valid internal references and archive integrity checks | Application implementation; claim of complete original sources |
| P1 — Semantic contracts | Executable artifact schemas, definition versions, expression semantics, state/validity model and independent fixtures | OPEN-01, OPEN-04; scope/authority subset of OPEN-05/06 resolved | TEST-02/03/05/07/08 and invalid examples reject for the correct reasons | Broad runtime stack, real-market support claims |
| P2 — Technical vertical slice | One genuine LLM idea through preserved formalization, atomic freeze, controlled backend and evidence report | P1; selected data/cost contract, backend version and exact evaluation protocol | TEST-01/06/11/12/15/18; a reproducible report without manual scientific repair | Profitability gate; full dashboards; live deployment |
| P3 — Isolation and exposure | Independent discovery perspectives, scoped tools, complete ancestry, four memory views and robust recovery | P2; OPEN-07/08/09 decisions relevant to trial | TEST-04/13/14/16/21; injected unauthorized access and crash/duplicate attempts fail safely | Automatic material self-improvement |
| P4 — End-to-end scientific calibration | Null worlds, planted signals and matched adaptive search calibration; finite confirmation queue | P3; statistical and success thresholds preregistered under OPEN-05/11/12 | TEST-19/20/24 with uncertainty, power and selected-null symmetry; negative outcomes retained | Declaring real-market alpha from synthetic calibration |
| P5 — Qualified historical research and Column Library | Historical campaigns, event/path diagnostics and genuinely future confirmation track | P4 gates pass; approved data authority and evidence budget | TEST-22/26; PIT event/path joins verified, fresh data lineage and evidence origin reported | Recycling spent history as new confirmation |
| P6 — Policy synthesis and optional controlled operation | Separate policy trials, provenance, evidence-to-decision and feedback firewall | Research validity established; OPEN-02/03 resolved for affected use; OPEN-10 before any real operation | TEST-09/10/17/25; combined-policy validation and bounded authority with withdrawal conditions | Automatic capital permissions, live evidence upgrades |
| P7 — Governed improvement and measured expansion | Candidate runtime reuse, generator improvement probes, richer diagnostics and additional domains only when justified | Specific observed deficiency, approved proposal and isolated evaluation | TEST-18/21/23/27 plus required regression suite; OPEN-11 comparison protocol before an acceleration claim; rollback preserves exposure | General self-modification or platform expansion for hypothetical reuse |

## Earlier technical-slice recommendation

The earlier recommendation was to start with P1 contract fixtures and the unresolved lifecycle representation, then exercise the P2 slice on a small, versioned dataset and a predefined evaluation plan. Retain this as a technical building block for the highest-priority experiment; the pilot plan must justify the amount of prerequisite work rather than automatically requiring every phase in full. Use an actual free LLM hypothesis in the integrated slice; separately use synthetic fixtures to verify the deterministic machinery. A hardcoded test hypothesis is useful for engineering but does not demonstrate the core invention requirement.

Do not select a profitable historical result as the software acceptance criterion. Accept only a traceable, reproducible, semantically faithful run with appropriate negative/error handling. A valid TESTED_NEGATIVE result can pass the engineering gate.

## Stop and restart rules

Every implementation iteration must name the current requirement, expected observable improvement and verification. Two consecutive iterations without meaningful improvement stop autonomous iteration and produce a concise cause/next-decision record. Material budget overruns, unsupported dependencies, ambiguous scientific semantics and failed isolation checks stop the affected work until resolved.

Files above 1,000 lines trigger decomposition review, not automatic splitting. Token cost, execution latency and UI render time are measured only where relevant. No latency SLO or currency budget is invented here. These are engineering stop rules; they are distinct from the framework's preregistered scientific/economic success or abandonment criteria.

Rollback restores an earlier approved configuration. It never restores pristine evidence or removes unsuccessful trials. A failed phase does not license loosening its acceptance conditions after seeing results.
