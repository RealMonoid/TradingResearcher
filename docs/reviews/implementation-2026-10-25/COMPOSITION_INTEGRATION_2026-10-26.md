# Composition conformance integration

Date: October 26, 2026. Base revision: `b57638bcab0c3cdde7d8ceda92d4764a7fa9f55f`. This continues the full seven-package objective; it does not complete it.

## Purpose and finding

Data/exposure acceptance and composition conformance remain separate scientific preparation prerequisites. Contract sections 1 and 6 preserve uncertain historical availability and training exposure; acquisition checks do not establish unconditional data acceptance. Section 14.1 explicitly allows automatic certification of compositions under unchanged primitive semantics.

Inspection of `binding.py`, `BINDING.md` and the reference certificate found that the certified expression engine checks the AST, while the additional binding driver is outside its certificate. Host transport checks alone cannot independently establish its per-program metadata or required warmup. An independent reviewer identified self-consistent metadata errors those checks could admit. All 26 newly fixed expectations match the existing compiler; this does not imply that earlier real compilations were incorrect.

The [composition certificate](../../../trading_researcher/COMPOSITION.md) adds independent compiler expectations, exact candidate replay, retained issuance and plan integration. It reuses existing exposure, backup, interruption and revocation boundaries without changing scientific meaning or other gates.

## Verification and limits

The [verification manifest](composition-verification-2026-10-26.json) and [independent review](composition-independent-2026-10-26.json) record actual checks for this revision. They cover namespace protection, exact identities, full data/feature/reference bindings, expectation integrity, malformed responses, backup/replay, cancellation, concurrent revocation and plan gates. An initial test mistakenly assumed Broker supported a context-manager interface; it was corrected before observing the meaningful missing-namespace failure. A later test-helper name collision was also corrected. These outputs remain retained.

Independent review identified that checking only the imported validator identity could leave a certificate current after its installed source or fixture changed in a long-running process. A focused test reproduced both cases. Current inspection now also checks the installed bytes; changed versions retain the original certificate but return `STALE_VALIDATOR` and reopen the prerequisite. Unreadable files remain quarantined. Frozen expectations and numerical meanings were not changed.

No provider call, new data acquisition or scientific outcome belongs to this step. Latest measured usage remains 145,641 tokens and USD 0.404925 conservative bound, with no added paid calls.

Data/PIT/rights/exposure acceptance, calibrated information and inference, atomic allocation/freeze, the genuine mixed-provider research cycle, AmiBroker policy evaluation and domain reporting remain required. Replay is implementation evidence, not independent scientific confirmation. Conservative outcome dependency gaps remain unchanged.

Next: connect remaining data/exposure qualifications and calibrated information requirements, then atomic scientific freeze and fixed release. Actual Anthropic access/spending remains required before its live calls; it does not block other implementation.
