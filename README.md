# TradingResearcher

Source-backed architecture for an autonomous market-research framework: an LLM independently develops hypotheses, freezes executable claims before confirmation, and submits them to independent code for evaluation.

The framework must substantially accelerate both hypothesis discovery and testing while preserving scientific decision quality. The [Problem Definition](docs/architecture/01_PROBLEM_DEFINITION.md) states both goals; the [Master Architecture](docs/architecture/06_MASTER_ARCHITECTURE.md) connects research, early exits, feedback and decision authority.

**Status:** documentation and preserved conversation sources only. No application implementation, demonstrated trading edge or live deployment is included.

## Start here

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
