# TradingResearcher

Source-backed architecture for an autonomous market-research framework: an LLM independently develops hypotheses, freezes executable claims before confirmation, and submits them to independent code for evaluation.

The framework must substantially accelerate both hypothesis discovery and testing while preserving scientific decision quality. The [Problem Definition](docs/architecture/01_PROBLEM_DEFINITION.md) states both goals; the [Master Architecture](docs/architecture/06_MASTER_ARCHITECTURE.md) connects research, early exits, feedback and decision authority.

The economic objective is profitably usable hypotheses after realistic costs, not beating quantitative firms or proving LLM superiority. Whether the framework achieves that objective is an empirical question, not a prerequisite for building it. The [Generator Feedback and Evaluation Contract](docs/architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md) specifies feedback use, later evaluation and discovery diagnostics.

**Status:** framework specifications, preserved sources and a bounded [AmiBroker CLI utility](tools/amibroker/README.md) with a verified Binance import/exploration/export smoke test. The autonomous research framework, scientific evaluator and live deployment are not implemented; no trading edge is demonstrated.

## Start here

**For LLM reviewers:** Follow [REVIEWING.md](REVIEWING.md) before a framework-wide critique. First present a source-linked reconstruction of goals, flow, feedback, authority and open boundaries. If access or context is incomplete, state the limits and withhold an overall verdict; do not treat a partial reading as the whole system.

- [Source audit and known gaps](docs/architecture/00_SOURCE_AUDIT.md)
- [Problem definition](docs/architecture/01_PROBLEM_DEFINITION.md)
- [Decision register](docs/architecture/02_DECISION_REGISTER.md)
- [Rejected and replaced alternatives](docs/architecture/03_REJECTED_DECISIONS.md)
- [Canonical definitions and preserved formulas](docs/architecture/04_DEFINITIONS.md)
- [Requirements](docs/architecture/05_REQUIREMENTS.md)
- [Master architecture](docs/architecture/06_MASTER_ARCHITECTURE.md)
- [Scientific evaluation](docs/architecture/07_SCIENTIFIC_EVALUATION.md)
- [Engineering review](docs/architecture/08_ENGINEERING_REVIEW.md)
- [Implementation blueprint](docs/architecture/09_IMPLEMENTATION_BLUEPRINT.md)
- [Proposed roadmap](docs/architecture/10_IMPLEMENTATION_ROADMAP.md)
- [Open decisions](docs/architecture/11_OPEN_DECISIONS.md)
- [Traceability matrix](docs/architecture/12_TRACEABILITY_MATRIX.md)
- [Generator feedback and evaluation contract](docs/architecture/13_GENERATOR_FEEDBACK_AND_EVALUATION.md)
- [Adopted retail research contract](docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md)

For selection bias and overfitting, the [integrated evaluation guidance](docs/architecture/07_SCIENTIFIC_EVALUATION.md#overfitting-controls-across-the-research-process) connects discovery, Columns, policy search and generator feedback. The [October 23 framework review](docs/reviews/OVERFITTING_REVIEW_2026-10-23.md) records the system assessment and documentation changes. These earlier reviews clarify existing decisions. D071-D085 now adopt the scoped statistical and implementation contracts; no runtime protection has been demonstrated.

## Evidence and limits

The archive contains 305 message blocks from 304 numbered turns of the accessible shared conversation. Two original images, three cited document bodies and an original export were unavailable; one captured response is incomplete. Full original-source completeness is not verified. Reconstruction continued with the user's explicit authorization to retain documented source gaps.

The decision register separates accepted decisions, conditional choices, superseded positions, deferred work and new proposals. The roadmap and implementation contracts are not evidence that an application has been built.

- [Exact captured transcript](sources/full_conversation.md)
- [Source manifest and checksums](sources/capture_manifest.json)
- [Message review index](docs/architecture/SOURCE_REVIEW_INDEX.md)
- [Machine-readable architecture register](docs/architecture/ARCHITECTURE_REGISTER.json)
- [Documentation verification results](docs/architecture/DOCUMENTATION_VERIFICATION.json)

Files under `sources/` are preserved byte-for-byte. Git attributes disable text conversion for that directory. Verify their SHA-256 hashes against the capture manifest before using a new checkout for reconstruction or further analysis.

Project documentation is English (en-US); original source quotations retain their language.

## Adopted open-decision resolutions

The [October 23 systematic assessment and literature review](docs/reviews/OPEN_DECISION_RESEARCH_2026-10-23.md) reconstructs the framework and accounts for all 15 open items. Its [retail research contract proposal, version 0.1](docs/reviews/RETAIL_RESEARCH_CONTRACT_PROPOSAL_2026-10-23.md) supplies concrete historical-first resolutions, scoped statistical/resource policies, acceptance cases and an integration/rollback plan. The user approved v0.1 with "Freigabe". D071-D085 now adopt its policies in the [Retail Research Contract, research-contract/1.0](docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md), with versioned definitions and current dispositions. The linked proposal remains the immutable preapproval document. Specification integration is complete; application implementation, data validation and empirical calibration are not established. See the [adoption verification](docs/reviews/adoption-2026-10-23/verification.json) for exact checks and changed files.
