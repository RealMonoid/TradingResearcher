# Decision Register

Version: reconstruction-1 + generator-contract/1.0 + research-contract/1.0 + agent-inquiry/1.0 + temporal-diagnostic-invocation/1.0 + monitoring-visibility/1.0 (October 24, 2026). D086 adopts the agent working discipline; D087 adopts automatic invocation of a predeclared temporal diagnostic plan; D088 adopts background orchestration and user-visible reporting for authorized temporal work. Earlier scientific contracts remain versioned and unchanged in their stated scope. D001-D070 retain their historical wording and statuses; D071-D085 record the approved scoped resolutions. Counts include historical dispositions; an older OPEN/AMBIGUOUS/DEFERRED record is not a current blocker where the explicit resolution below applies. This revision implements binding specification changes, not application code.

## Reading authority and counts

Statuses describe recovered decisions, not implementation completion. A quoted proposal is not acceptance; an explicit acceptance refers to the immediately preceding qualified reply. Contextual consolidation is labeled and has weaker attribution than a direct user instruction. The final master prompt is not used as retrospective acceptance. Counts use the atomic decision units below and are not counts of approval messages.

| Status | Count |
|---|---:|
| NON_NEGOTIABLE | 1 |
| ACCEPTED | 66 |
| REJECTED | 1 |
| CONDITIONALLY_ACCEPTED | 5 |
| SUPERSEDED | 6 |
| DEFERRED | 6 |
| PROPOSED_ONLY | 1 |
| AMBIGUOUS | 1 |
| OPEN | 1 |

Rejection records in [03_REJECTED_DECISIONS.md](03_REJECTED_DECISIONS.md) record rejected alternatives at finer granularity. Do not add their count to this table as if these were disjoint decisions. Components and requirement IDs resolve in documents 05 and 06. Dependencies mean the referenced requirement and components must hold; D001 and D008 constrain every normative decision.

## Chronological decisions

### D001 — Free LLM invention, executable freeze, independent code judgment

**Status:** NON_NEGOTIABLE. **Normative:** true.

**Problem:** A template selector or self-scoring narrator cannot answer the original research problem.

**Decision, reason and alternative:** Retain freedom before confirmation and prevent outcome-driven claim repair; closed rule catalogs and LLM verdicts are excluded.

**Affected components / dependencies:** CMP-02, CMP-03, CMP-04, CMP-06; REQ-001; D001 and D008.

**Source and acceptance:** [M0057](../../sources/full_conversation.md#m0057--user) (L5598-L5606); [M0059](../../sources/full_conversation.md#m0059--user) (L5690-L5690); [M0107](../../sources/full_conversation.md#m0107--user) (L12455-L12455). Direct user constitution and reinforcement.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D002 — Separate H_idea and H_exec; retain unexecutable ideas

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A compiler can silently narrow discovery.

**Decision, reason and alternative:** Formalize without changing the claim; retain DATA_GAP, LANGUAGE_GAP and evaluation gaps for retry, rather than deleting unusual ideas.

**Affected components / dependencies:** CMP-02, CMP-03; REQ-002; D001 and D008.

**Source and acceptance:** [M0061](../../sources/full_conversation.md#m0061--user) (L5817-L5825); [M0062](../../sources/full_conversation.md#m0062--assistant) (L5835-L6396); [M0067](../../sources/full_conversation.md#m0067--user) (L7383-L7392); [M0071](../../sources/full_conversation.md#m0071--user) (L8730-L8737); [M0074](../../sources/full_conversation.md#m0074--assistant) (L9306-L9395). User instruction plus requested handoff.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D003 — Express differences, associations, changes, boundaries and interactions

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A flat rule schema cannot represent the permitted research space.

**Decision, reason and alternative:** Support binary and continuous outcomes and extensible semantics; mechanisms produce testable consequences. No closed hypothesis menu.

**Affected components / dependencies:** CMP-03, CMP-04; REQ-002; D001 and D008.

**Source and acceptance:** [M0067](../../sources/full_conversation.md#m0067--user) (L7383-L7392); [M0068](../../sources/full_conversation.md#m0068--assistant) (L7402-L8546); [M0071](../../sources/full_conversation.md#m0071--user) (L8730-L8737); [M0088](../../sources/full_conversation.md#m0088--assistant) (L10833-L10961); [M0090](../../sources/full_conversation.md#m0090--assistant) (L10981-L11135). Direct requested specification; later clarification.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D004 — Certified feature compositions and separately certified new primitives

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Unreviewed computations can introduce leakage or semantic errors.

**Decision, reason and alternative:** Spec author supplies independent golden cases; implementation cannot certify itself. Revoked versions invalidate dependent evidence.

**Affected components / dependencies:** CMP-03, CMP-04, CMP-08; REQ-003; D001 and D008.

**Source and acceptance:** [M0061](../../sources/full_conversation.md#m0061--user) (L5817-L5825); [M0062](../../sources/full_conversation.md#m0062--assistant) (L5835-L6396); [M0065](../../sources/full_conversation.md#m0065--user) (L7144-L7188); [M0066](../../sources/full_conversation.md#m0066--assistant) (L7198-L7373); [M0067](../../sources/full_conversation.md#m0067--user) (L7383-L7392); [M0068](../../sources/full_conversation.md#m0068--assistant) (L7402-L8546). Direct user specification in M0067.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D005 — Point-in-time context and immutable research epochs

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Shared mutable context contaminates independent search.

**Decision, reason and alternative:** Same permitted snapshot, isolated discovery perspectives, artifact exchange and next-epoch knowledge updates; no shared live brainstorming state.

**Affected components / dependencies:** CMP-01, CMP-02, CMP-07; REQ-004; D001 and D008.

**Source and acceptance:** [M0063](../../sources/full_conversation.md#m0063--user) (L6406-L6406); [M0064](../../sources/full_conversation.md#m0064--assistant) (L6416-L7134); [M0068](../../sources/full_conversation.md#m0068--assistant) (L7402-L8546); [M0071](../../sources/full_conversation.md#m0071--user) (L8730-L8737); [M0110](../../sources/full_conversation.md#m0110--assistant) (L12547-L12633); [M0111](../../sources/full_conversation.md#m0111--user) (L12643-L12662); [M0112](../../sources/full_conversation.md#m0112--assistant) (L12672-L12794). User autonomy request and retained design.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D006 — Code assigns evaluation policy, family and evidence status

**Status:** ACCEPTED. **Normative:** true.

**Problem:** The generator could choose easy sample sizes or declare success.

**Decision, reason and alternative:** Freeze policy and dependencies before evaluation; N_min and family assignment follow predefined rules independent of the generator.

**Affected components / dependencies:** CMP-04, CMP-06; REQ-005; D001 and D008.

**Source and acceptance:** [M0065](../../sources/full_conversation.md#m0065--user) (L7144-L7188); [M0066](../../sources/full_conversation.md#m0066--assistant) (L7198-L7373); [M0067](../../sources/full_conversation.md#m0067--user) (L7383-L7392); [M0068](../../sources/full_conversation.md#m0068--assistant) (L7402-L8546); [M0071](../../sources/full_conversation.md#m0071--user) (L8730-L8737); [M0072](../../sources/full_conversation.md#m0072--assistant) (L8747-L9286). Direct requested specification.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D007 — Append-only error tracking distinct from negative evidence

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Technical failures can be mistaken for falsification.

**Decision, reason and alternative:** Separate ErrorEvent/Incident/Defect, quarantine by severity, retain resolution history; errors provide no evidence for or against H.

**Affected components / dependencies:** CMP-04, CMP-05, CMP-06, CMP-11; REQ-006; D001 and D008.

**Source and acceptance:** [M0069](../../sources/full_conversation.md#m0069--user) (L8556-L8556); [M0070](../../sources/full_conversation.md#m0070--assistant) (L8566-L8720); [M0071](../../sources/full_conversation.md#m0071--user) (L8730-L8737); [M0072](../../sources/full_conversation.md#m0072--assistant) (L8747-L9286); [M0288](../../sources/full_conversation.md#m0288--assistant) (L26682-L26842); [M0289](../../sources/full_conversation.md#m0289--user) (L26852-L26852). Direct user request and later acceptance.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D008 — Canonical versioned definitions and formulas

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Stable names can conceal semantic changes.

**Decision, reason and alternative:** Preserve M0072 section 6 formulas; changes to meaning need proposal, impact analysis and approval; editorial corrections may preserve meaning.

**Affected components / dependencies:** CMP-04, CMP-06, CMP-12; REQ-007; D001 and D008.

**Source and acceptance:** [M0071](../../sources/full_conversation.md#m0071--user) (L8730-L8737); [M0072](../../sources/full_conversation.md#m0072--assistant) (L8747-L9286); [M0241](../../sources/full_conversation.md#m0241--user) (L23913-L23913); [M0242](../../sources/full_conversation.md#m0242--assistant) (L23923-L23972); [M0243](../../sources/full_conversation.md#m0243--user) (L23982-L23982). Direct instruction and explicit acceptance.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D009 — Minimal provenance and dependency graph

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A broad epistemic ontology turns interpretations into facts.

**Decision, reason and alternative:** Boolean logic belongs inside a hypothesis; retain genealogy, REQUIRES, evidence overlap and joint testing. Broad semantic relations remain proposals.

**Affected components / dependencies:** CMP-03, CMP-07, CMP-08; REQ-008; D001 and D008.

**Source and acceptance:** [M0085](../../sources/full_conversation.md#m0085--user) (L10586-L10586); [M0086](../../sources/full_conversation.md#m0086--assistant) (L10596-L10813); [M0089](../../sources/full_conversation.md#m0089--user) (L10971-L10971); [M0090](../../sources/full_conversation.md#m0090--assistant) (L10981-L11135); [M0091](../../sources/full_conversation.md#m0091--user) (L11145-L11153); [M0092](../../sources/full_conversation.md#m0092--assistant) (L11163-L11299). Contextual consolidation; no standalone acceptance turn.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D010 — Hypotheses and policies have separate evidence

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A useful claim does not validate a strategy assembled from it.

**Decision, reason and alternative:** Policy synthesis is a second search with separate trials, provenance and validation; composite success does not prove each component.

**Affected components / dependencies:** CMP-06, CMP-09; REQ-009; D001 and D008.

**Source and acceptance:** [M0083](../../sources/full_conversation.md#m0083--user) (L10333-L10333); [M0084](../../sources/full_conversation.md#m0084--assistant) (L10343-L10576); [M0113](../../sources/full_conversation.md#m0113--user) (L12804-L12804); [M0114](../../sources/full_conversation.md#m0114--assistant) (L12814-L13085); [M0137](../../sources/full_conversation.md#m0137--user) (L15763-L15766); [M0138](../../sources/full_conversation.md#m0138--assistant) (L15776-L16032); [M0139](../../sources/full_conversation.md#m0139--user) (L16042-L16042); [M0141](../../sources/full_conversation.md#m0141--user) (L16275-L16277). User additions and explicit continuation.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D011 — Mechanisms are optional discovery routes, testable when claimed

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Narrative plausibility can masquerade as causal evidence.

**Decision, reason and alternative:** Allow theory-first, data-first and recombination; causal claims require premises, competing explanations and independent consequences.

**Affected components / dependencies:** CMP-02, CMP-03, CMP-06; REQ-010; D001 and D008.

**Source and acceptance:** [M0093](../../sources/full_conversation.md#m0093--user) (L11309-L11309); [M0094](../../sources/full_conversation.md#m0094--assistant) (L11319-L11491); [M0095](../../sources/full_conversation.md#m0095--user) (L11501-L11510); [M0096](../../sources/full_conversation.md#m0096--assistant) (L11520-L11684); [M0111](../../sources/full_conversation.md#m0111--user) (L12643-L12662); [M0112](../../sources/full_conversation.md#m0112--assistant) (L12672-L12794); [M0193](../../sources/full_conversation.md#m0193--user) (L20788-L20788); [M0194](../../sources/full_conversation.md#m0194--assistant) (L20798-L20910); [M0195](../../sources/full_conversation.md#m0195--user) (L20920-L20920). Later explicit acceptance in M0195.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D012 — V1 discovery starts at 15 minutes; swing horizons allowed

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Earlier 5-minute examples overconstrain the goal.

**Decision, reason and alternative:** Observation timeframe differs from outcome and invalidation horizons. Exclude 5-minute discovery in v1, not all future execution uses.

**Affected components / dependencies:** CMP-01, CMP-03; REQ-011; D001 and D008.

**Source and acceptance:** [M0097](../../sources/full_conversation.md#m0097--user) (L11694-L11694); [M0098](../../sources/full_conversation.md#m0098--assistant) (L11704-L11790). Direct user scope change.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D013 — Historical backtest-first with separate test backend

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Duplicating execution logic obscures scientific responsibility.

**Decision, reason and alternative:** Research owns exposure, freeze and evidence; backend owns calculations and simulation. Historical OOS, walk-forward and forward remain distinct.

**Affected components / dependencies:** CMP-01, CMP-05, CMP-06; REQ-012; D001 and D008.

**Source and acceptance:** [M0101](../../sources/full_conversation.md#m0101--user) (L11978-L11978); [M0102](../../sources/full_conversation.md#m0102--assistant) (L11988-L12157); [M0105](../../sources/full_conversation.md#m0105--user) (L12189-L12262); [M0106](../../sources/full_conversation.md#m0106--assistant) (L12272-L12445); [M0153](../../sources/full_conversation.md#m0153--user) (L17440-L17441); [M0154](../../sources/full_conversation.md#m0154--assistant) (L17451-L17643); [M0155](../../sources/full_conversation.md#m0155--user) (L17653-L17653). Direct user change plus later evidence qualification.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D014 — Transitive data exposure inheritance

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Knowledge and memory can launder previously seen outcomes.

**Decision, reason and alternative:** A descendant inherits exposure of all used artifacts and queries; rollback never restores freshness. Unknown model exposure is not clean holdout.

**Affected components / dependencies:** CMP-01, CMP-02, CMP-07, CMP-08; REQ-013; D001 and D008.

**Source and acceptance:** [M0102](../../sources/full_conversation.md#m0102--assistant) (L11988-L12157); [M0106](../../sources/full_conversation.md#m0106--assistant) (L12272-L12445); [M0112](../../sources/full_conversation.md#m0112--assistant) (L12672-L12794); [M0153](../../sources/full_conversation.md#m0153--user) (L17440-L17441); [M0154](../../sources/full_conversation.md#m0154--assistant) (L17451-L17643); [M0155](../../sources/full_conversation.md#m0155--user) (L17653-L17653); [M0166](../../sources/full_conversation.md#m0166--assistant) (L18223-L18400); [M0167](../../sources/full_conversation.md#m0167--user) (L18410-L18410). Retained principle explicitly accepted with memory.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D015 — Rule-based or combinatorial baseline generator

**Status:** REJECTED. **Normative:** false.

**Problem:** A competing generator changes the research question and adds machinery.

**Decision, reason and alternative:** Keep statistical comparators and process placebos; do not build a baseline hypothesis agent.

**Affected components / dependencies:** CMP-02, CMP-06; REQ-001; D001 and D008.

**Source and acceptance:** [M0107](../../sources/full_conversation.md#m0107--user) (L12455-L12455); [M0108](../../sources/full_conversation.md#m0108--assistant) (L12465-L12501); [M0190](../../sources/full_conversation.md#m0190--assistant) (L20585-L20739); [M0191](../../sources/full_conversation.md#m0191--user) (L20749-L20749); [M0220](../../sources/full_conversation.md#m0220--assistant) (L22551-L22716); [M0221](../../sources/full_conversation.md#m0221--user) (L22726-L22726). Direct user rejection.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D016 — Research reasoner performs problem finding and adaptive pre-freeze search

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Prompting for a fixed number of ideas invites superficial variations.

**Decision, reason and alternative:** Use tensions, question formation, deterministic queries, counterexamples and bounded reasoning budgets; do not prescribe answers.

**Affected components / dependencies:** CMP-01, CMP-02; REQ-014; D001 and D008.

**Source and acceptance:** [M0109](../../sources/full_conversation.md#m0109--user) (L12511-L12537); [M0110](../../sources/full_conversation.md#m0110--assistant) (L12547-L12633); [M0111](../../sources/full_conversation.md#m0111--user) (L12643-L12662); [M0112](../../sources/full_conversation.md#m0112--assistant) (L12672-L12794); [M0119](../../sources/full_conversation.md#m0119--user) (L13471-L13473); [M0121](../../sources/full_conversation.md#m0121--user) (L13878-L13878); [M0122](../../sources/full_conversation.md#m0122--assistant) (L13888-L14078); [M0129](../../sources/full_conversation.md#m0129--user) (L14827-L14827); [M0130](../../sources/full_conversation.md#m0130--assistant) (L14837-L15103); [M0223](../../sources/full_conversation.md#m0223--user) (L22769-L22769); [M0224](../../sources/full_conversation.md#m0224--assistant) (L22779-L22997); [M0225](../../sources/full_conversation.md#m0225--user) (L23007-L23007). Direct user emphasis; explicit acceptance of adaptive search.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D017 — Entry, exit, sizing, management and adaptive updates are research objects

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Static downstream rules can erase the value of adaptive research.

**Decision, reason and alternative:** Freeze state reactions and update rules; do not rewrite policy after losses. No mandatory linear progression through all claim roles.

**Affected components / dependencies:** CMP-03, CMP-09; REQ-009; D001 and D008.

**Source and acceptance:** [M0113](../../sources/full_conversation.md#m0113--user) (L12804-L12804); [M0114](../../sources/full_conversation.md#m0114--assistant) (L12814-L13085). Direct user scope expansion.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D018 — Technical, fundamental, on-chain and other financial information permitted

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Predetermined weights or OHLCV-only inputs constrain invention.

**Decision, reason and alternative:** The generator hypothesizes relevance and integration; model release times, revisions, confirmation and processing latency.

**Affected components / dependencies:** CMP-01, CMP-03, CMP-05; REQ-015; D001 and D008.

**Source and acceptance:** [M0115](../../sources/full_conversation.md#m0115--user) (L13095-L13095); [M0116](../../sources/full_conversation.md#m0116--assistant) (L13105-L13255); [M0161](../../sources/full_conversation.md#m0161--user) (L17939-L17947); [M0162](../../sources/full_conversation.md#m0162--assistant) (L17957-L18158); [M0163](../../sources/full_conversation.md#m0163--user) (L18168-L18168). Direct user instruction and PIT acceptance.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D019 — Four distinct memories with inherited provenance

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Experience, observations and established market claims can be conflated.

**Decision, reason and alternative:** Separate Research Journal, Market Model, Research Experience Memory and Policy Experience; heuristics guide search, never upgrade evidence.

**Affected components / dependencies:** CMP-07, CMP-08, CMP-09; REQ-016; D001 and D008.

**Source and acceptance:** [M0125](../../sources/full_conversation.md#m0125--user) (L14382-L14382); [M0126](../../sources/full_conversation.md#m0126--assistant) (L14392-L14575); [M0165](../../sources/full_conversation.md#m0165--user) (L18212-L18213); [M0166](../../sources/full_conversation.md#m0166--assistant) (L18223-L18400); [M0167](../../sources/full_conversation.md#m0167--user) (L18410-L18410); [M0168](../../sources/full_conversation.md#m0168--assistant) (L18420-L18458). Explicit acceptance in M0167.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D020 — Evidence, current applicability and deployment permission are different axes

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Replicated knowledge may degrade; uncertain action is not scientific proof.

**Decision, reason and alternative:** Use evidence-to-decision with explicit risk, confirmation and withdrawal conditions; no automatic status-to-capital ladder.

**Affected components / dependencies:** CMP-06, CMP-08, CMP-09, CMP-10; REQ-017; D001 and D008.

**Source and acceptance:** [M0137](../../sources/full_conversation.md#m0137--user) (L15763-L15766); [M0138](../../sources/full_conversation.md#m0138--assistant) (L15776-L16032); [M0141](../../sources/full_conversation.md#m0141--user) (L16275-L16277); [M0142](../../sources/full_conversation.md#m0142--assistant) (L16287-L16439); [M0145](../../sources/full_conversation.md#m0145--user) (L16690-L16691); [M0146](../../sources/full_conversation.md#m0146--assistant) (L16701-L16868); [M0147](../../sources/full_conversation.md#m0147--user) (L16878-L16893); [M0148](../../sources/full_conversation.md#m0148--assistant) (L16903-L17083); [M0185](../../sources/full_conversation.md#m0185--user) (L19995-L19995); [M0186](../../sources/full_conversation.md#m0186--assistant) (L20005-L20327). Contextual retained design; capital thresholds not accepted.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D021 — Every policy rule has a basis and scope/parameter provenance

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A policy can smuggle pretrained trading folklore into supposedly tested rules.

**Decision, reason and alternative:** Record EVIDENCE_BACKED, UNTESTED_ASSUMPTION or OPERATIONAL_CONSTRAINT; also scope relation, parameter origin and conflicts. Register new assumptions.

**Affected components / dependencies:** CMP-09, CMP-08; REQ-009; D001 and D008.

**Source and acceptance:** [M0141](../../sources/full_conversation.md#m0141--user) (L16275-L16277); [M0142](../../sources/full_conversation.md#m0142--assistant) (L16287-L16439); [M0143](../../sources/full_conversation.md#m0143--user) (L16449-L16460); [M0144](../../sources/full_conversation.md#m0144--assistant) (L16470-L16680); [M0185](../../sources/full_conversation.md#m0185--user) (L19995-L19995); [M0186](../../sources/full_conversation.md#m0186--assistant) (L20005-L20327). Direct user basis rule; dimensional refinements retained.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D022 — Selective reuse of external infrastructure

**Status:** CONDITIONALLY_ACCEPTED. **Normative:** true.

**Problem:** Rebuilding generic plumbing wastes effort; importing fitness logic changes the goal.

**Decision, reason and alternative:** Own scientific core; reuse only isolated components after interface, license and conformance checks. RD-Agent/OpenEvolve are references, not chosen foundations.

**Affected components / dependencies:** CMP-02, CMP-05, CMP-12; REQ-018; D001 and D008.

**Source and acceptance:** [M0139](../../sources/full_conversation.md#m0139--user) (L16042-L16042); [M0140](../../sources/full_conversation.md#m0140--assistant) (L16052-L16265); [M0229](../../sources/full_conversation.md#m0229--user) (L23324-L23324); [M0231](../../sources/full_conversation.md#m0231--user) (L23378-L23378); [M0232](../../sources/full_conversation.md#m0232--assistant) (L23388-L23680); [M0233](../../sources/full_conversation.md#m0233--user) (L23690-L23690); [M0235](../../sources/full_conversation.md#m0235--user) (L23736-L23736); [M0236](../../sources/full_conversation.md#m0236--assistant) (L23746-L23805); [M0237](../../sources/full_conversation.md#m0237--user) (L23815-L23815). User asks reuse; later candidate-specific acceptance.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D023 — Evidence budget and confirmation queue

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Cheap hypotheses can exhaust finite independent information.

**Decision, reason and alternative:** Prioritize ex-ante quality, testability, nonredundancy and decision relevance; preserve nonselected ideas. Forward evidence remains necessary for clean confirmation.

**Affected components / dependencies:** CMP-02, CMP-04, CMP-06; REQ-019; D001 and D008.

**Source and acceptance:** [M0153](../../sources/full_conversation.md#m0153--user) (L17440-L17441); [M0154](../../sources/full_conversation.md#m0154--assistant) (L17451-L17643); [M0155](../../sources/full_conversation.md#m0155--user) (L17653-L17653); [M0156](../../sources/full_conversation.md#m0156--assistant) (L17663-L17681). Explicit acceptance in M0155.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D024 — Primary support is not truth; base-rate interpretation is separate from power

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Rare real effects can produce many false positive discoveries.

**Decision, reason and alternative:** N_min uses outcome base rate, not subjective probability that H is true. Family evidence informs interpretation with uncertainty; replication remains separate.

**Affected components / dependencies:** CMP-06, CMP-08; REQ-005; D001 and D008.

**Source and acceptance:** [M0157](../../sources/full_conversation.md#m0157--user) (L17691-L17692); [M0158](../../sources/full_conversation.md#m0158--assistant) (L17702-L17883); [M0159](../../sources/full_conversation.md#m0159--user) (L17893-L17893); [M0160](../../sources/full_conversation.md#m0160--assistant) (L17903-L17929). Explicit acceptance in M0159.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D025 — Framework itself must be falsifiable and calibrated end to end

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A pipeline could document nonsense indefinitely.

**Decision, reason and alternative:** Freeze technical, calibration and economic gates; test null worlds and planted effects through discovery and policy selection, not only the statistics code.

**Affected components / dependencies:** CMP-02, CMP-05, CMP-06, CMP-09; REQ-020; D001 and D008.

**Source and acceptance:** [M0161](../../sources/full_conversation.md#m0161--user) (L17939-L17947); [M0162](../../sources/full_conversation.md#m0162--assistant) (L17957-L18158); [M0163](../../sources/full_conversation.md#m0163--user) (L18168-L18168); [M0164](../../sources/full_conversation.md#m0164--assistant) (L18178-L18202). Explicit acceptance in M0163.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D026 — Material self-improvement requires proposals, approval, validation and rollback

**Status:** ACCEPTED. **Normative:** true.

**Problem:** An agent can improve apparent results by changing its scientific rules.

**Decision, reason and alternative:** Version every change, preserve failed probes and exposure, restore earlier versions; no in-place material self-modification.

**Affected components / dependencies:** CMP-12, CMP-02, CMP-07; REQ-021; D001 and D008.

**Source and acceptance:** [M0169](../../sources/full_conversation.md#m0169--user) (L18468-L18600); [M0170](../../sources/full_conversation.md#m0170--assistant) (L18610-L18868); [M0171](../../sources/full_conversation.md#m0171--user) (L18878-L18878); [M0172](../../sources/full_conversation.md#m0172--assistant) (L18888-L19083); [M0173](../../sources/full_conversation.md#m0173--user) (L19093-L19093); [M0174](../../sources/full_conversation.md#m0174--assistant) (L19103-L19114). Direct instruction and explicit acceptance.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D027 — Quantitatively disappointable claims; EV and downside for policies

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Correct direction alone can hide economically irrelevant effects.

**Decision, reason and alternative:** Specify comparator, estimand, horizon, relevant effect and falsifier; policy claims add net EV, downside and execution conditions.

**Affected components / dependencies:** CMP-03, CMP-06, CMP-09; REQ-005; D001 and D008.

**Source and acceptance:** [M0175](../../sources/full_conversation.md#m0175--user) (L19124-L19124); [M0176](../../sources/full_conversation.md#m0176--assistant) (L19134-L19244); [M0177](../../sources/full_conversation.md#m0177--user) (L19254-L19254); [M0178](../../sources/full_conversation.md#m0178--assistant) (L19264-L19515). Direct user correction; retained in final architecture.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D028 — Diagnostic versioned dashboards, no single agent success score

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Metric optimization can corrupt research behavior.

**Decision, reason and alternative:** Show technical reliability, cost, gaps, diversity, trials, evidence maturity and policy health with denominators; no automatic Sharpe or novelty reward.

**Affected components / dependencies:** CMP-11; REQ-022; D001 and D008.

**Source and acceptance:** [M0179](../../sources/full_conversation.md#m0179--user) (L19525-L19525); [M0180](../../sources/full_conversation.md#m0180--assistant) (L19535-L19798); [M0185](../../sources/full_conversation.md#m0185--user) (L19995-L19995); [M0186](../../sources/full_conversation.md#m0186--assistant) (L20005-L20327). Direct user dashboard requirement.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D029 — Targeted external research allowed with provenance and time boundaries

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Pretrained knowledge is incomplete and can reinforce confirmation bias.

**Decision, reason and alternative:** Prefer claim-appropriate academic/primary sources; seek counterevidence; external evidence never becomes internal replication automatically.

**Affected components / dependencies:** CMP-01, CMP-02, CMP-07; REQ-014; D001 and D008.

**Source and acceptance:** [M0181](../../sources/full_conversation.md#m0181--user) (L19808-L19808); [M0182](../../sources/full_conversation.md#m0182--assistant) (L19818-L19949); [M0183](../../sources/full_conversation.md#m0183--user) (L19959-L19959); [M0184](../../sources/full_conversation.md#m0184--assistant) (L19969-L19985). Direct instruction and explicit acceptance.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D030 — Implementation anti-bloat and two-iteration stop

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A research design can expand into an unbuildable platform.

**Decision, reason and alternative:** Current-scope work only; simplest sufficient design; review files over 1,000 lines; monitor costs/runtime; stop after two iterations without meaningful improvement.

**Affected components / dependencies:** CMP-11, CMP-12; REQ-023; D001 and D008.

**Source and acceptance:** [M0187](../../sources/full_conversation.md#m0187--user) (L20337-L20343); [M0188](../../sources/full_conversation.md#m0188--assistant) (L20353-L20544); [M0223](../../sources/full_conversation.md#m0223--user) (L22769-L22769); [M0224](../../sources/full_conversation.md#m0224--assistant) (L22779-L22997); [M0225](../../sources/full_conversation.md#m0225--user) (L23007-L23007). Direct user instruction; reinforced acceptance.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D031 — Causal time-series evaluation and full selection accounting

**Status:** ACCEPTED. **Normative:** true.

**Problem:** End-model parameter counts hide actual search freedom.

**Decision, reason and alternative:** Register outcome-driven feature, threshold, policy and generator choices; use sensible policy comparators and costs. No universal walk-forward method.

**Affected components / dependencies:** CMP-04, CMP-05, CMP-06; REQ-024; D001 and D008.

**Source and acceptance:** [M0189](../../sources/full_conversation.md#m0189--user) (L20554-L20575); [M0190](../../sources/full_conversation.md#m0190--assistant) (L20585-L20739); [M0191](../../sources/full_conversation.md#m0191--user) (L20749-L20749); [M0192](../../sources/full_conversation.md#m0192--assistant) (L20759-L20778). Explicit acceptance in M0191.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D032 — Mechanisms predict applicability and negative cases before test

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A story fitted only to winners cannot discriminate explanations.

**Decision, reason and alternative:** Derive stronger/weaker/absent regions from structural premises; keep UNKNOWN mechanisms legitimate for empirical discovery.

**Affected components / dependencies:** CMP-02, CMP-03, CMP-06; REQ-010; D001 and D008.

**Source and acceptance:** [M0193](../../sources/full_conversation.md#m0193--user) (L20788-L20788); [M0194](../../sources/full_conversation.md#m0194--assistant) (L20798-L20910); [M0195](../../sources/full_conversation.md#m0195--user) (L20920-L20920); [M0196](../../sources/full_conversation.md#m0196--assistant) (L20930-L20957). Explicit acceptance in M0195.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D033 — Freeze claim scope and test universe separately

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Successful selected instruments can be generalized beyond tested coverage.

**Decision, reason and alternative:** Specify primary, suitable negative-control and optional replication universes; additions after results are new exploration.

**Affected components / dependencies:** CMP-03, CMP-04, CMP-06; REQ-005; D001 and D008.

**Source and acceptance:** [M0197](../../sources/full_conversation.md#m0197--user) (L20967-L20967); [M0198](../../sources/full_conversation.md#m0198--assistant) (L20977-L21102); [M0199](../../sources/full_conversation.md#m0199--user) (L21112-L21112); [M0200](../../sources/full_conversation.md#m0200--assistant) (L21122-L21144). Explicit acceptance in M0199.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D034 — Agents for open reasoning; deterministic workflows for specified operations

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Agent discretion at scientific boundaries undermines reproducibility.

**Decision, reason and alternative:** Use narrow tools, just-in-time retrieval, brain/hands separation and untrusted-content boundaries; LLM formalization is schema-checked, not an evidential judge.

**Affected components / dependencies:** CMP-01, CMP-02, CMP-03, CMP-04, CMP-06; REQ-004; D001 and D008.

**Source and acceptance:** [M0201](../../sources/full_conversation.md#m0201--user) (L21154-L21154); [M0202](../../sources/full_conversation.md#m0202--assistant) (L21164-L21430); [M0203](../../sources/full_conversation.md#m0203--user) (L21440-L21440); [M0204](../../sources/full_conversation.md#m0204--assistant) (L21450-L21470). Explicit acceptance in M0203.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D035 — Fitted parameters need sensitivity checks; ensembles are new claims

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A sharp winning optimum may reflect search luck.

**Decision, reason and alternative:** Predefine neighborhoods and stress parameter, tail, regime and cost dependence. DSR/PBO are conditional methods, not universal gates.

**Affected components / dependencies:** CMP-05, CMP-06, CMP-09; REQ-024; D001 and D008.

**Source and acceptance:** [M0205](../../sources/full_conversation.md#m0205--user) (L21480-L21540); [M0206](../../sources/full_conversation.md#m0206--assistant) (L21550-L21727); [M0207](../../sources/full_conversation.md#m0207--user) (L21737-L21737); [M0208](../../sources/full_conversation.md#m0208--assistant) (L21747-L21768). Explicit acceptance of qualified M0206.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D036 — Adversarial falsification before freeze is not validation

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A plausible narrative or model consensus is weak assurance.

**Decision, reason and alternative:** LLMs propose concrete attacks; code checks available cases. Surviving criticism is ex-ante information only; post-freeze repair creates a new version.

**Affected components / dependencies:** CMP-02, CMP-03, CMP-06; REQ-010; D001 and D008.

**Source and acceptance:** [M0209](../../sources/full_conversation.md#m0209--user) (L21778-L21779); [M0210](../../sources/full_conversation.md#m0210--assistant) (L21789-L21968); [M0211](../../sources/full_conversation.md#m0211--user) (L21978-L21978); [M0212](../../sources/full_conversation.md#m0212--assistant) (L21988-L22015). Explicit acceptance in M0211.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D037 — Operational feedback firewall

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Bad fills or short PnL spells must not rewrite market evidence.

**Decision, reason and alternative:** Route operations to policy experience/deployment; registered anomalies enter future research epochs; applicability changes use predefined monitoring rules.

**Affected components / dependencies:** CMP-08, CMP-09, CMP-10, CMP-11; REQ-025; D001 and D008.

**Source and acceptance:** [M0213](../../sources/full_conversation.md#m0213--user) (L22025-L22026); [M0214](../../sources/full_conversation.md#m0214--assistant) (L22036-L22263); [M0215](../../sources/full_conversation.md#m0215--user) (L22273-L22273); [M0216](../../sources/full_conversation.md#m0216--assistant) (L22283-L22451); [M0217](../../sources/full_conversation.md#m0217--user) (L22461-L22461); [M0218](../../sources/full_conversation.md#m0218--assistant) (L22471-L22508). Direct restriction and explicit acceptance; missing image not reconstructed.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D038 — Best-of-N symmetry and process-matched placebo calibration

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A selected real winner is unfairly compared with one unselected null candidate.

**Decision, reason and alternative:** Reproduce selection freedom, nuisance exposure and execution constraints; compare on evidence fresh to both sides.

**Affected components / dependencies:** CMP-05, CMP-06, CMP-09; REQ-020; D001 and D008.

**Source and acceptance:** [M0219](../../sources/full_conversation.md#m0219--user) (L22518-L22541); [M0220](../../sources/full_conversation.md#m0220--assistant) (L22551-L22716); [M0221](../../sources/full_conversation.md#m0221--user) (L22726-L22726); [M0222](../../sources/full_conversation.md#m0222--assistant) (L22736-L22759). Explicit acceptance in M0221.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D039 — Adaptive compute and failure diagnosis before repetition

**Status:** ACCEPTED. **Normative:** true.

**Problem:** More tokens do not solve missing data, premises or representation.

**Decision, reason and alternative:** Distinguish knowledge, premise, data, search, representation and evaluation gaps; log trajectory and budget; diagnoses remain hypotheses.

**Affected components / dependencies:** CMP-02, CMP-11; REQ-014; D001 and D008.

**Source and acceptance:** [M0223](../../sources/full_conversation.md#m0223--user) (L22769-L22769); [M0224](../../sources/full_conversation.md#m0224--assistant) (L22779-L22997); [M0225](../../sources/full_conversation.md#m0225--user) (L23007-L23007); [M0226](../../sources/full_conversation.md#m0226--assistant) (L23017-L23046). Explicit acceptance in M0225.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D040 — Harness2 principles for controlled generator improvement

**Status:** CONDITIONALLY_ACCEPTED. **Normative:** true.

**Problem:** An improver with final evaluation access can overfit its own acceptance test.

**Decision, reason and alternative:** Propose/probe/compose only behind protected evaluation and approval; adapt selected patterns, not an uncontrolled recursion foundation.

**Affected components / dependencies:** CMP-12; REQ-021; D001 and D008.

**Source and acceptance:** [M0227](../../sources/full_conversation.md#m0227--user) (L23056-L23056); [M0228](../../sources/full_conversation.md#m0228--assistant) (L23066-L23314); [M0229](../../sources/full_conversation.md#m0229--user) (L23324-L23324); [M0230](../../sources/full_conversation.md#m0230--assistant) (L23334-L23368). Explicit acceptance of role-limited recommendation.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D041 — Hermes as agent-runtime candidate

**Status:** CONDITIONALLY_ACCEPTED. **Normative:** true.

**Problem:** Generic provider/tool/session infrastructure need not be rebuilt.

**Decision, reason and alternative:** Keep evidence/knowledge ownership outside runtime; isolate profiles, memory and tools. Candidate selection is not proof of integration.

**Affected components / dependencies:** CMP-02, CMP-07; REQ-018; D001 and D008.

**Source and acceptance:** [M0231](../../sources/full_conversation.md#m0231--user) (L23378-L23378); [M0232](../../sources/full_conversation.md#m0232--assistant) (L23388-L23680); [M0233](../../sources/full_conversation.md#m0233--user) (L23690-L23690); [M0234](../../sources/full_conversation.md#m0234--assistant) (L23700-L23726). Explicit acceptance of candidate role, not unconditional dependency.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D042 — vectorbt as primary backtest backend candidate

**Status:** CONDITIONALLY_ACCEPTED. **Normative:** true.

**Problem:** A concrete fast calculation backend is needed behind a stable contract.

**Decision, reason and alternative:** Own adapter and scientific semantics; validate path-dependent execution and edition/license suitability before adoption.

**Affected components / dependencies:** CMP-05; REQ-012; D001 and D008.

**Source and acceptance:** [M0235](../../sources/full_conversation.md#m0235--user) (L23736-L23736); [M0236](../../sources/full_conversation.md#m0236--assistant) (L23746-L23805); [M0237](../../sources/full_conversation.md#m0237--user) (L23815-L23815); [M0238](../../sources/full_conversation.md#m0238--assistant) (L23825-L23843). Explicit acceptance as primary candidate.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D043 — English en-US project language

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Mixed terms and languages create avoidable semantic drift.

**Decision, reason and alternative:** All project artifacts use English; source quotations retain language; user conversation language is independent.

**Affected components / dependencies:** CMP-12; REQ-007; D001 and D008.

**Source and acceptance:** [M0239-A](../../sources/full_conversation.md#m0239-a--user) (L23853-L23853); [M0239-B](../../sources/full_conversation.md#m0239-b--user) (L23863-L23863); [M0240](../../sources/full_conversation.md#m0240--assistant) (L23873-L23903). Direct user language policy; duplicate blocks preserved.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D044 — Column Library includes event and trade diagnostics

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Feature inputs alone miss why and when trade paths differ.

**Decision, reason and alternative:** Reusable columns need semantic/PIT definitions; broad candidate-event research is an option, not a mandatory discovery route.

**Affected components / dependencies:** CMP-01, CMP-05, CMP-07; REQ-026; D001 and D008.

**Source and acceptance:** [M0251](../../sources/full_conversation.md#m0251--user) (L24512-L24512); [M0255](../../sources/full_conversation.md#m0255--user) (L24776-L24776); [M0256](../../sources/full_conversation.md#m0256--assistant) (L24786-L24852); [M0257](../../sources/full_conversation.md#m0257--user) (L24862-L24862); [M0258](../../sources/full_conversation.md#m0258--assistant) (L24872-L24894). Direct request plus accepted corrected podcast interpretation.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D045 — Entry, evolving intra-trade and full-path columns stay separate

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Full-trade MAE/MFE leak future information into earlier decisions.

**Decision, reason and alternative:** Decision-time values use only accumulated observations; one path can support exploration of many ideas but not independent confirmations.

**Affected components / dependencies:** CMP-01, CMP-03, CMP-05; REQ-026; D001 and D008.

**Source and acceptance:** [M0259](../../sources/full_conversation.md#m0259--user) (L24904-L24904); [M0260](../../sources/full_conversation.md#m0260--assistant) (L24914-L25021); [M0261](../../sources/full_conversation.md#m0261--user) (L25031-L25037); [M0262](../../sources/full_conversation.md#m0262--assistant) (L25047-L25121); [M0263](../../sources/full_conversation.md#m0263--user) (L25131-L25131). Direct intra-trade request and accepted consolidation.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D046 — Broad discovery and controlled confirmation

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A rich column library can become unregistered filter optimization.

**Decision, reason and alternative:** Preserve continuous information where meaningful; register every selected filter and combination; confirm new claims independently.

**Affected components / dependencies:** CMP-02, CMP-04, CMP-05, CMP-06; REQ-026; D001 and D008.

**Source and acceptance:** [M0261](../../sources/full_conversation.md#m0261--user) (L25031-L25037); [M0262](../../sources/full_conversation.md#m0262--assistant) (L25047-L25121); [M0263](../../sources/full_conversation.md#m0263--user) (L25131-L25131); [M0264](../../sources/full_conversation.md#m0264--assistant) (L25141-L25149). Explicit acceptance in M0263.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D047 — Column relationship robustness, not mandatory monotonicity

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A winning threshold can hide unstable or nonlinear structure.

**Decision, reason and alternative:** Inspect distribution and time stability; match filter selection rate and relevant exposure; count the complete search.

**Affected components / dependencies:** CMP-05, CMP-06; REQ-024; D001 and D008.

**Source and acceptance:** [M0265](../../sources/full_conversation.md#m0265--user) (L25159-L25165); [M0266](../../sources/full_conversation.md#m0266--assistant) (L25175-L25372); [M0267](../../sources/full_conversation.md#m0267--user) (L25382-L25382); [M0268](../../sources/full_conversation.md#m0268--assistant) (L25392-L25400). Explicit acceptance in M0267.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D048 — Signal and policy decomposition where suitable

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Net PnL obscures whether entry, exit, sizing or market effect contributes.

**Decision, reason and alternative:** Use event studies and component diagnostics; choosing a decay peak exit is a new selection. No mandatory positive entry edge before exit research.

**Affected components / dependencies:** CMP-05, CMP-06, CMP-09; REQ-009; D001 and D008.

**Source and acceptance:** [M0271](../../sources/full_conversation.md#m0271--user) (L25637-L25643); [M0272](../../sources/full_conversation.md#m0272--assistant) (L25653-L25771); [M0273](../../sources/full_conversation.md#m0273--user) (L25781-L25781); [M0274](../../sources/full_conversation.md#m0274--assistant) (L25791-L25797). Explicit acceptance in M0273.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D049 — Hypothesis-specific null contract and selection-aware tests

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A correct test can still answer the wrong question.

**Decision, reason and alternative:** State destroyed relationships, preserved structure, benchmark and assumptions; fixed-family max-statistics differ from rerunning adaptive search.

**Affected components / dependencies:** CMP-05, CMP-06; REQ-020; D001 and D008.

**Source and acceptance:** [M0275](../../sources/full_conversation.md#m0275--user) (L25807-L25810); [M0276](../../sources/full_conversation.md#m0276--assistant) (L25820-L25964); [M0277](../../sources/full_conversation.md#m0277--user) (L25974-L25974); [M0278](../../sources/full_conversation.md#m0278--assistant) (L25984-L25994). Explicit acceptance in M0277.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D050 — Diversification, meta-labeling and resampling as optional policy methods

**Status:** CONDITIONALLY_ACCEPTED. **Normative:** true.

**Problem:** Combining strategies or shuffled trades can be mistaken for new evidence.

**Decision, reason and alternative:** Evaluate combined policies independently; preserve attribution; dependence-aware path-risk diagnostics do not establish future risk.

**Affected components / dependencies:** CMP-05, CMP-06, CMP-09; REQ-009; D001 and D008.

**Source and acceptance:** [M0279](../../sources/full_conversation.md#m0279--user) (L26004-L26008); [M0280](../../sources/full_conversation.md#m0280--assistant) (L26018-L26248); [M0281](../../sources/full_conversation.md#m0281--user) (L26258-L26258); [M0282](../../sources/full_conversation.md#m0282--assistant) (L26268-L26278). Explicit acceptance of qualified methods.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D051 — Bounded exhaustive computation allowed; no generator replacement

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Calculation scale can hide enormous data mining freedom.

**Decision, reason and alternative:** Use brute force for columns, diagnostics, sensitivity, attacks and calibration; record outcome selection and independent confirmation.

**Affected components / dependencies:** CMP-02, CMP-05, CMP-06; REQ-024; D001 and D008.

**Source and acceptance:** [M0283](../../sources/full_conversation.md#m0283--user) (L26288-L26288); [M0284](../../sources/full_conversation.md#m0284--assistant) (L26298-L26615); [M0285](../../sources/full_conversation.md#m0285--user) (L26625-L26625); [M0286](../../sources/full_conversation.md#m0286--assistant) (L26635-L26662). User asks to add qualified M0284.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D052 — Deterministic sanity gates at critical transitions

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Simple data, timing or accounting mistakes can dominate results.

**Decision, reason and alternative:** Check data, claim and simulation invariants; technical failure quarantines execution, never disproves H; no plausibility score veto.

**Affected components / dependencies:** CMP-01, CMP-03, CMP-05, CMP-06; REQ-006; D001 and D008.

**Source and acceptance:** [M0287](../../sources/full_conversation.md#m0287--user) (L26672-L26672); [M0288](../../sources/full_conversation.md#m0288--assistant) (L26682-L26842); [M0289](../../sources/full_conversation.md#m0289--user) (L26852-L26852); [M0290](../../sources/full_conversation.md#m0290--assistant) (L26862-L26874). Explicit acceptance in M0289.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D053 — Future-only primary evaluation environment

**Status:** SUPERSEDED. **Normative:** false.

**Problem:** Earlier prospective-only flow does not represent later backtest-first scope.

**Decision, reason and alternative:** Replace primary execution mode with historical-first plus separately labeled forward confirmation; preserve original formulas as historical versions.

**Affected components / dependencies:** CMP-05, CMP-06; REQ-012; D001 and D008.

**Source and acceptance:** [M0062](../../sources/full_conversation.md#m0062--assistant) (L5835-L6396); [M0068](../../sources/full_conversation.md#m0068--assistant) (L7402-L8546); [M0072](../../sources/full_conversation.md#m0072--assistant) (L8747-L9286); [M0101](../../sources/full_conversation.md#m0101--user) (L11978-L11978); [M0102](../../sources/full_conversation.md#m0102--assistant) (L11988-L12157); [M0153](../../sources/full_conversation.md#m0153--user) (L17440-L17441); [M0154](../../sources/full_conversation.md#m0154--assistant) (L17451-L17643); [M0155](../../sources/full_conversation.md#m0155--user) (L17653-L17653). Superseded explicitly by user M0101.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D054 — Generator receives context but cannot use tools

**Status:** SUPERSEDED. **Normative:** false.

**Problem:** No-tools simplification prevents later approved measurement and literature research.

**Decision, reason and alternative:** Permit scoped deterministic queries and targeted web research with exposure/provenance controls.

**Affected components / dependencies:** CMP-01, CMP-02; REQ-014; D001 and D008.

**Source and acceptance:** [M0061](../../sources/full_conversation.md#m0061--user) (L5817-L5825); [M0062](../../sources/full_conversation.md#m0062--assistant) (L5835-L6396); [M0110](../../sources/full_conversation.md#m0110--assistant) (L12547-L12633); [M0112](../../sources/full_conversation.md#m0112--assistant) (L12672-L12794); [M0181](../../sources/full_conversation.md#m0181--user) (L19808-L19808); [M0182](../../sources/full_conversation.md#m0182--assistant) (L19818-L19949); [M0183](../../sources/full_conversation.md#m0183--user) (L19959-L19959). Superseded by direct user M0181.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D055 — Per-hypothesis generated test code as default

**Status:** SUPERSEDED. **Normative:** false.

**Problem:** Generator-produced statistics can change semantics or judge its own claim.

**Decision, reason and alternative:** Declarative H_exec and deterministic compiler replace it; new feature implementation remains a separately certified infrastructure path.

**Affected components / dependencies:** CMP-03, CMP-04; REQ-002; D001 and D008.

**Source and acceptance:** [M0058](../../sources/full_conversation.md#m0058--assistant) (L5616-L5680); [M0065](../../sources/full_conversation.md#m0065--user) (L7144-L7188); [M0066](../../sources/full_conversation.md#m0066--assistant) (L7198-L7373); [M0067](../../sources/full_conversation.md#m0067--user) (L7383-L7392); [M0068](../../sources/full_conversation.md#m0068--assistant) (L7402-L8546); [M0074](../../sources/full_conversation.md#m0074--assistant) (L9306-L9395). Later user-requested compiler specification.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D056 — Broad semantic epistemic graph as mandatory core

**Status:** SUPERSEDED. **Normative:** false.

**Problem:** Interpreted contradictions/refinements were presented too confidently.

**Decision, reason and alternative:** Replace with provenance, hard dependencies and evidence overlap; optional proposed relations are not facts.

**Affected components / dependencies:** CMP-08; REQ-008; D001 and D008.

**Source and acceptance:** [M0086](../../sources/full_conversation.md#m0086--assistant) (L10596-L10813); [M0089](../../sources/full_conversation.md#m0089--user) (L10971-L10971); [M0090](../../sources/full_conversation.md#m0090--assistant) (L10981-L11135); [M0092](../../sources/full_conversation.md#m0092--assistant) (L11163-L11299). Assistant retracts under user challenge.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D057 — Rigid evidence-status-to-capital ladder

**Status:** SUPERSEDED. **Normative:** false.

**Problem:** Evidence alone does not determine benefit, downside or operational readiness.

**Decision, reason and alternative:** Use separate evidence-to-decision policy with bounded uncertainty and explicit withdrawal conditions.

**Affected components / dependencies:** CMP-10; REQ-017; D001 and D008.

**Source and acceptance:** [M0145](../../sources/full_conversation.md#m0145--user) (L16690-L16691); [M0146](../../sources/full_conversation.md#m0146--assistant) (L16701-L16868); [M0147](../../sources/full_conversation.md#m0147--user) (L16878-L16893); [M0148](../../sources/full_conversation.md#m0148--assistant) (L16903-L17083). Later contextual revision, no numerical limits accepted.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D058 — 5-minute discovery examples as current scope

**Status:** SUPERSEDED. **Normative:** false.

**Problem:** Early examples conflict with later explicit minimum timeframe.

**Decision, reason and alternative:** V1 minimum 15 minutes; lower-timeframe execution may be reconsidered separately.

**Affected components / dependencies:** CMP-01, CMP-03; REQ-011; D001 and D008.

**Source and acceptance:** [M0050](../../sources/full_conversation.md#m0050--assistant) (L4710-L4801); [M0072](../../sources/full_conversation.md#m0072--assistant) (L8747-L9286); [M0097](../../sources/full_conversation.md#m0097--user) (L11694-L11694); [M0098](../../sources/full_conversation.md#m0098--assistant) (L11704-L11790). Direct user scope change.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D059 — Full causal meta-evaluation of generator quality

**Status:** DEFERRED. **Normative:** false.

**Problem:** Heavy methodology can precede basic instrumentation and evidence.

**Decision, reason and alternative:** Instrument first; consider paired generator-version studies when enough data exist. Never reintroduce rejected rule-based baseline.

**Affected components / dependencies:** CMP-11, CMP-12; REQ-022; D001 and D008.

**Source and acceptance:** [M0016](../../sources/full_conversation.md#m0016--assistant) (L691-L953); [M0017](../../sources/full_conversation.md#m0017--user) (L963-L976); [M0018](../../sources/full_conversation.md#m0018--assistant) (L986-L1097); [M0020](../../sources/full_conversation.md#m0020--assistant) (L1125-L1273); [M0022](../../sources/full_conversation.md#m0022--assistant) (L1311-L1436); [M0044](../../sources/full_conversation.md#m0044--assistant) (L3468-L3731); [M0107](../../sources/full_conversation.md#m0107--user) (L12455-L12455); [M0108](../../sources/full_conversation.md#m0108--assistant) (L12465-L12501). Explicitly staged in source; no deadline committed.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D060 — Universal SPC control charts and thresholds

**Status:** DEFERRED. **Normative:** false.

**Problem:** No stable per-version distribution is established.

**Decision, reason and alternative:** Freeze metric definitions, collect observations and assess assumptions before choosing charts. No causal attribution from chart alarms alone.

**Affected components / dependencies:** CMP-11; REQ-022; D001 and D008.

**Source and acceptance:** [M0041](../../sources/full_conversation.md#m0041--user) (L3116-L3131); [M0042](../../sources/full_conversation.md#m0042--assistant) (L3141-L3423); [M0043](../../sources/full_conversation.md#m0043--user) (L3433-L3458); [M0044](../../sources/full_conversation.md#m0044--assistant) (L3468-L3731). Not chosen in source.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D061 — Exact initial agent count and provider diversity

**Status:** DEFERRED. **Normative:** false.

**Problem:** Logical independence does not specify deployment topology.

**Decision, reason and alternative:** Keep multiple independent perspectives in target design; choose count and cost after a conformance experiment.

**Affected components / dependencies:** CMP-02; REQ-004; D001 and D008.

**Source and acceptance:** [M0064](../../sources/full_conversation.md#m0064--assistant) (L6416-L7134); [M0068](../../sources/full_conversation.md#m0068--assistant) (L7402-L8546); [M0072](../../sources/full_conversation.md#m0072--assistant) (L8747-L9286); [M0110](../../sources/full_conversation.md#m0110--assistant) (L12547-L12633); [M0186](../../sources/full_conversation.md#m0186--assistant) (L20005-L20327); [M0246](../../sources/full_conversation.md#m0246--assistant) (L24018-L24339); [M0247](../../sources/full_conversation.md#m0247--user) (L24349-L24349). Open in handoff; implementation discussion deferred.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D062 — Exact statistical policies, family taxonomy and sample targets

**Status:** DEFERRED. **Normative:** false.

**Problem:** Examples are not a validated numerical protocol.

**Decision, reason and alternative:** Resolve before affected confirmation runs; do not invent alpha, N_min, calendars or replication count.

**Affected components / dependencies:** CMP-04, CMP-06; REQ-005; D001 and D008.

**Source and acceptance:** [M0068](../../sources/full_conversation.md#m0068--assistant) (L7402-L8546); [M0072](../../sources/full_conversation.md#m0072--assistant) (L8747-L9286); [M0186](../../sources/full_conversation.md#m0186--assistant) (L20005-L20327); [M0246](../../sources/full_conversation.md#m0246--assistant) (L24018-L24339); [M0247](../../sources/full_conversation.md#m0247--user) (L24349-L24349). Explicit open technical specification.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D063 — Exact storage, retrieval, schemas and runtime versions

**Status:** DEFERRED. **Normative:** false.

**Problem:** Architecture roles do not select a database or tested release.

**Decision, reason and alternative:** Propose small implementations and contracts in blueprint; no silent dependency adoption.

**Affected components / dependencies:** CMP-01, CMP-02, CMP-07; REQ-018; D001 and D008.

**Source and acceptance:** [M0186](../../sources/full_conversation.md#m0186--assistant) (L20005-L20327); [M0232](../../sources/full_conversation.md#m0232--assistant) (L23388-L23680); [M0246](../../sources/full_conversation.md#m0246--assistant) (L24018-L24339); [M0247](../../sources/full_conversation.md#m0247--user) (L24349-L24349). Open/deferred technical choices.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D064 — Capital amounts and live deployment thresholds

**Status:** DEFERRED. **Normative:** false.

**Problem:** Scientific architecture cannot determine personal risk authority.

**Decision, reason and alternative:** Keep live execution out of initial research implementation; require explicit deployment policy before real capital.

**Affected components / dependencies:** CMP-10; REQ-017; D001 and D008.

**Source and acceptance:** [M0146](../../sources/full_conversation.md#m0146--assistant) (L16701-L16868); [M0148](../../sources/full_conversation.md#m0148--assistant) (L16903-L17083); [M0186](../../sources/full_conversation.md#m0186--assistant) (L20005-L20327). Explicitly not fixed.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D065 — Single-agent vertical slice implementation order

**Status:** PROPOSED_ONLY. **Normative:** false.

**Problem:** Feasibility is unproven and large initial scope is risky.

**Decision, reason and alternative:** Useful engineering recommendation, not a replacement for independent target roles; user deferred prioritization at M0247.

**Affected components / dependencies:** CMP-02, CMP-04, CMP-05, CMP-06; REQ-023; D001 and D008.

**Source and acceptance:** [M0245](../../sources/full_conversation.md#m0245--user) (L24008-L24008); [M0246](../../sources/full_conversation.md#m0246--assistant) (L24018-L24339); [M0247](../../sources/full_conversation.md#m0247--user) (L24349-L24349). Recommendation explicitly not implemented.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D066 — Scope subset automatically inherits evidence

**Status:** AMBIGUOUS. **Normative:** false.

**Problem:** A subgroup can differ from the average effect in its parent population.

**Decision, reason and alternative:** Preserve M0144 statement but flag transportability conditions; do not silently treat subset evidence as confirmed.

**Affected components / dependencies:** CMP-06, CMP-09; REQ-009; D001 and D008.

**Source and acceptance:** [M0143](../../sources/full_conversation.md#m0143--user) (L16449-L16460); [M0144](../../sources/full_conversation.md#m0144--assistant) (L16470-L16680). Scientific contradiction requiring resolution.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D067 — Historical state machine and status-axis migration

**Status:** OPEN. **Normative:** false.

**Problem:** M0072 prospective lifecycle and one status field do not cover later multi-axis evidence.

**Decision, reason and alternative:** Preserve old definitions; propose a versioned historical branch and orthogonal status dimensions for approval.

**Affected components / dependencies:** CMP-04, CMP-06, CMP-08; REQ-007; D001 and D008.

**Source and acceptance:** [M0071](../../sources/full_conversation.md#m0071--user) (L8730-L8737); [M0072](../../sources/full_conversation.md#m0072--assistant) (L8747-L9286); [M0101](../../sources/full_conversation.md#m0101--user) (L11978-L11978); [M0102](../../sources/full_conversation.md#m0102--assistant) (L11988-L12157); [M0138](../../sources/full_conversation.md#m0138--assistant) (L15776-L16032); [M0146](../../sources/full_conversation.md#m0146--assistant) (L16701-L16868); [M0148](../../sources/full_conversation.md#m0148--assistant) (L16903-L17083); [M0241](../../sources/full_conversation.md#m0241--user) (L23913-L23913); [M0242](../../sources/full_conversation.md#m0242--assistant) (L23923-L23972); [M0243](../../sources/full_conversation.md#m0243--user) (L23982-L23982). Unresolved implementation semantics.

**Change control:** User approval for semantic or goal changes; unresolved implementation choices remain proposals.

### D068 — Accelerate hypothesis discovery and testing as framework success

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Scientific evaluation requirements can obscure the purpose of accelerating the whole research process, including useful early elimination and learning from unsuccessful work.

**Decision, reason and alternative:** Substantially accelerate both hypothesis discovery and testing while preserving free invention, independent evaluation and decision quality. Evaluate this as framework success alongside technical validity, calibration and economic usefulness; neither idea throughput, rejection count nor supported-claim count alone is sufficient. A predefined comparable workflow or prior version must match task scope, decision quality and evidence access. The reference, measures, substantial-improvement threshold and experiment design remain OPEN-11; no rejected comparator generator or relaxed evidence rule is authorized.

**Affected components / dependencies:** CMP-02, CMP-03, CMP-04, CMP-05, CMP-06, CMP-07, CMP-11, CMP-12; REQ-027; D001, D008, D013, D019, D025, D028 and D036.

**Source and acceptance:** SESSION-2026-10-22, direct user clarification in the current repository conversation, outside the immutable M0001-M0304 archive. Verbatim excerpts:

> Eine Anforderung bei der Idee zu diesem Framework war es, die Hypothesensuche UND Tests massiv zu beschleunigen, Das ist, das zweite Ziel was das framework leisten soll

> Das wäre ein Erfolgskriterium für das framework selbst. Hypothesen dürfen schnell sterben, und es gibt im Framework mechanismen dafür

The user subsequently approved the documentation remedy in the [System Model Review](../reviews/SYSTEM_MODEL_REVIEW.md#smallest-proposed-remedy) with "ja mach das". That approval covers canonical propagation, complete feedback presentation and simpler entry instructions; it does not approve the still-open scientific semantics. This entry records the clarified goal rather than asserting that the original archive contains these later messages.

**Change control:** Preserve the original D001-D067 records, canonical definitions and source bytes. Numerical acceptance and affected scientific contracts require their own review before use. The clarification is versioned here and in the structured register; its implementation can be rolled back as a documentation revision without erasing this source/approval history.

### D069 — Economic usefulness without a superiority prerequisite

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Comparing to competitors or demanding an advance benefit demonstration can replace the user's empirical objective with an unrequested superiority contest or prevent the research that would answer it.

**Decision, reason and alternative:** Generate profitably usable hypotheses after realistic costs and execution constraints; beating quantitative firms or another generator is not required. Unknown benefit is a reason to investigate, not a failed entry gate. Distinguish absolute economic usefulness, procedural capability, version improvement and research acceleration. D068 remains a process objective; statistical references and separate policy evaluation remain necessary. A competing-method comparison is optional and requires its own scope; D015 is not reversed.

**Affected components / dependencies:** CMP-02, CMP-06, CMP-09, CMP-11, CMP-12; REQ-029; D001, D010, D015, D025, D059, D068; OPEN-05/06/11/12.

**Source and acceptance:** SESSION-2026-10-22-GENERATOR, current direct user instructions, outside the immutable archive. The user requested academic research and implementation of the reviewed improvements, then explicitly selected specification integration. Verbatim excerpts:

> Ich weiß nicht ob das besser als irgendwas ist. Ich baue es ja, um das rauszufinden. Wie soll das gehen, das schon im vornherein zu sagen?

> Bezüglich Deiner verbesserungsideen auf Claudes kritik, recherchiere das nochmal ordentlich und dann implementiere es tatsächlich in das framework. Halte dich an akademische Forschung

> Verbindlich in die Framework-Spezifikation integrieren

> Überhaupt, das Framework muss vielleicht nicht besser als irgendwas sein. Es muss profitable Hypothesen generieren und keine Quantfirmen schlagen

**Change control:** This clarification and D070 implement that authorized scope. No claimed profitability, chosen market/threshold, rejected comparator or live authority is introduced. Preserve prior decisions and this instruction when superseded; comparison-specific performance claims still require suitable evidence.

### D070 — Operational feedback, assessment and discovery diagnostics

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Memory availability, changed behavior and more generated ideas can be mistaken for beneficial learning without actionable records, valid assessment or diagnostic coverage.

**Decision, reason and alternative:** Adopt version 1.0 of the [Generator Feedback and Evaluation Contract](13_GENERATOR_FEEDBACK_AND_EVALUATION.md). Separate observations from interpretations, record later-epoch use with inherited exposure, retain counterevidence and heuristic reviews, and assess only the improvement actually claimed. Require purpose-specific assessment plans and uncertainty; separate procedural from economic feedback. Observe novelty/structural diversity and formalization coverage without creating an originality veto, mandatory literature gate, fixed discovery modes or autonomous reward. Scope pilots by actual data/information constraints without permanently excluding swing or semantic discovery.

**Affected components / dependencies:** CMP-01, CMP-02, CMP-03, CMP-04, CMP-06, CMP-07, CMP-11, CMP-12; REQ-028/029/030; D005, D014, D016, D019, D026, D028, D059, D069; OPEN-04/05/06/09/11/12/14.

**Source and acceptance:** SESSION-2026-10-22-GENERATOR, the explicit research-and-specification instruction quoted in D069, following the [generator critique assessment](../reviews/CLAUDE_GENERATOR_CRITIQUE_ASSESSMENT_2026-10-22.md). The contract's academic basis and transfer limits are recorded in document 13. This is current authorized specification work, not retrospective archival acceptance or evidence of working software.

**Change control:** Preserve definitions, source bytes, prior versions and all exposure. This contract does not resolve OPEN-01 through OPEN-03 or the numerical policies, authorize an experiment while required data are absent, or create a routine-certification approval rule. Material changes follow D008/D026; rollback retains this source history and superseded contract versions.


### D071 — Versioned lifecycle and separate evidence axes

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-01 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** introduce `research-contract/1.0` as a separately versioned extension; preserve reconstruction-1 and the exact M0072 quotation. Use this execution path: Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 1](14_RETAIL_RESEARCH_CONTRACT.md#1-open-01-versioned-lifecycle-and-evidence-axes); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-04, CMP-06, CMP-08, CMP-12; REQ-007; D008/D026; OPEN-01. Additional affected records: D008/D013/D020/D053/D067, DEF-014–024/027, REQ-005/006/007/012/017.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D072 — Scope membership without automatic evidence transport

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-02 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** IN_SCOPE/SCOPE_SUBSET/EXTRAPOLATION/INCOMPATIBLE describe a scope relation only. Mark a rule EVIDENCE_BACKED for its particular use only when a referenced EvidenceRecord directly evaluates that target or a separately approved transport contract justifies the target estimand, overlap, effect modifiers and uncertainty. V1 provides no automatic transport estimator. Otherwise record UNTESTED_ASSUMPTION and a candidate claim, without blocking policy research itself. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 2](14_RETAIL_RESEARCH_CONTRACT.md#2-open-02-subset-membership-is-not-evidence-transport); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-03, CMP-05, CMP-06, CMP-08, CMP-09; REQ-009; D008/D026; OPEN-02. Additional affected records: D010/D021/D066, DEF-028/029, REQ-009.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D073 — Descriptive cohorts without invented truth priors

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-03 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** report generated, executable, frozen, valid-evaluated, initially supported, replication-selected, replication-completed, replicated, failed and pending counts by version/cohort and observation cutoff. Keep explicit denominators and time at risk. Undefined rates remain null, not zero. A selected replication yield is labeled as selected. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 3](14_RETAIL_RESEARCH_CONTRACT.md#3-open-03-descriptive-cohorts-no-invented-truth-priors); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-11, CMP-12; REQ-022; D008/D026; OPEN-03. Additional affected records: D024/D028, DEF-011/012/026, REQ-005/022/029.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D074 — Typed expressions and explicit estimands

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-04 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** use a versioned JSON AST, not generated evaluator code. The expression language is extensible; the currently certified operator set is an execution capability boundary, not a hypothesis catalog. Preserve the original H_idea and a semantic-difference report. Unrepresented meaning produces LANGUAGE_GAP or SEMANTIC_AMBIGUITY. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 4](14_RETAIL_RESEARCH_CONTRACT.md#4-open-04-typed-expressions-and-explicit-estimands); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-02, CMP-03, CMP-04; REQ-002; D008/D026; OPEN-04. Additional affected records: D002–004/D008/D017/D027/D031, DEF-003–008/013/023/031/032, REQ-002/003/005/011/024/026.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D075 — Fixed historical inference and finite information decisions

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-05 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** use a fixed historical assessment for the initial profile. Discovery can stop cheaply for a concrete contradiction, unaffordable requirement or missing representation, but such abandonment is not a frozen empirical negative. After freeze, evaluate once at the declared fixed trigger. Do not repeatedly inspect nominal intervals for early success. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 5](14_RETAIL_RESEARCH_CONTRACT.md#5-open-05-test-policy-useful-negatives-and-information-limits); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-03, CMP-04, CMP-06, CMP-08, CMP-09; REQ-005; D008/D026; OPEN-05. Additional affected records: D006/D024/D027/D031/D035/D062, DEF-007/008/012/018/021/022, REQ-005/019/020/024/029.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D076 — Bounded initial data and execution profile

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-06 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** adopt a first research profile using BTCUSDT and ETHUSDT spot 15-minute data, UTC, January 1, 2020 through December 31, 2025, from the public Binance archive or verified local copies of those exact artifacts. This is a bounded liquid-market engineering/evidence profile, not an assertion of uncrowded alpha, an investment recommendation or a permanent restriction to crypto/OHLCV. Other domains remain first-class extension requests under D018. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 6](14_RETAIL_RESEARCH_CONTRACT.md#6-open-06-data-and-execution-authority); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-01, CMP-03, CMP-05; REQ-015; D008/D026; OPEN-06. Additional affected records: D012/D013/D018/D033/D042/D069, DEF-013/024/031/033, REQ-011/012/015/018/029.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D077 — Owned runtime adapter and host isolation

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-07 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** define the owned adapter interface now; do not require Hermes for v1. Use the already available provider/runtime only through bounded calls and artifacts, recording its exact model identifier and generation parameters. If only a mutable alias is exposed, record that limitation and reject claims requiring an immutable model snapshot. Never claim that changing model names proves independence. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 7](14_RETAIL_RESEARCH_CONTRACT.md#7-open-07-runtime-choice-and-isolation); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-01, CMP-02, CMP-05, CMP-07, CMP-12; REQ-018; D008/D026; OPEN-07. Additional affected records: D022/D034/D040–042/D063, REQ-004/012/018/021.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D078 — Transactional persistence and canonical serialization

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-08 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** start with one local SQLite registry, one writer and immutable artifact payloads. Store small JSON envelopes/bodies, events, dependency edges, trial identities and freeze manifests in the same database transaction. Use foreign keys, uniqueness constraints, append-only application APIs and `synchronous=FULL`; verify actual settings on connection. Large data/result blobs are external, content-addressed files staged, flushed and hash-verified before registry reference commitment. An uncommitted staged blob grants no authority. Recovery checks committed references and quarantines missing/corrupt blobs; harmless orphan staging files can be reclaimed under a separate retention policy. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 8](14_RETAIL_RESEARCH_CONTRACT.md#8-open-08-persistence-serialization-and-recovery); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-04, CMP-06, CMP-08, CMP-12; REQ-007; D008/D026; OPEN-08. Additional affected records: D006/D007/D008/D009/D030/D063, REQ-005/006/007/008/012/023.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D079 — Bounded discovery perspectives and compute budgets

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-09 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** initial research epoch has two isolated discovery perspectives on the same snapshot, run sequentially to limit resource use; they exchange completed artifacts only after submission. One may use semantic context and another an alternative reasoning prompt, but modes are not mandatory scientific filters. Same provider/model is allowed; differing labels are not evidence of diverse thought. Exact model and prompt versions are run-profile fields. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 9](14_RETAIL_RESEARCH_CONTRACT.md#9-open-09-perspectives-models-and-compute-budget); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-02, CMP-04, CMP-05, CMP-06, CMP-11, CMP-12; REQ-023; D008/D026; OPEN-09. Additional affected records: D005/D016/D028/D030/D039/D061/D070, REQ-004/014/022/023/030.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D080 — Research-only authority and zero authorized capital

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-10 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** v1 has no order-submission capability, authorized capital is zero, and every output is a research or simulation artifact. This settles the current operating mode. A later live-capital capability requires a separate reviewed deployment contract specifying owner, loss/exposure limits, venue/account, costs, withdrawal and rollback. Those personal choices cannot be inferred from a p-value or research result. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 10](14_RETAIL_RESEARCH_CONTRACT.md#10-open-10-explicit-research-only-authority); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-06, CMP-08, CMP-09, CMP-10; REQ-017; D008/D026; OPEN-10. Additional affected records: D020/D057/D064, REQ-017/025.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D081 — Separate finite success and continuation gates

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-11 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** report separate gates. Passing an earlier gate permits only its named inference, never a profitable-framework claim. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 11](14_RETAIL_RESEARCH_CONTRACT.md#11-open-11-finite-success-and-continuation-criteria); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-02, CMP-06, CMP-09, CMP-11, CMP-12; REQ-029; D008/D026; OPEN-11. Additional affected records: D025/D030/D038/D059/D068–070, REQ-020/022/023/027/029.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D082 — Frozen batch allocation and controlled feedback release

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-12 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** one predeclared batch of at most eight primary estimands per initial campaign. Selection uses development information only. First admit semantically complete, testable candidates with available information; then order by explicit decision relevance, lower estimated test cost and nonredundant coverage, with stable registration order as the final tie-break. Preserve criterion values and reasons; do not create a weighted LLM truth score. Untested critical policy assumptions can receive a documented priority flag. Unselected ideas remain queued. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 12](14_RETAIL_RESEARCH_CONTRACT.md#12-open-12-confirmation-allocation-and-feedback-release); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-02, CMP-04, CMP-06; REQ-019; D008/D026; OPEN-12. Additional affected records: D014/D023/D031/D038/D046/D049/D070, REQ-005/013/019/020/024/028/029.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D083 — Typed dependency consequences and current applicability

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-13 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** use the existing minimal typed graph with this consequence table. No general scientific-contradiction ontology is introduced. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 13](14_RETAIL_RESEARCH_CONTRACT.md#13-open-13-dependency-effects-and-applicability); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-03, CMP-07, CMP-08; REQ-008; D008/D026; OPEN-13. Additional affected records: D009/D020/D037, DEF-015/027, REQ-008/017/025.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D084 — Independent certification within approved semantics

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-14 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** distinguish certification of an implementation from approval of scientific meaning. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 14](14_RETAIL_RESEARCH_CONTRACT.md#14-open-14-automatic-certification-within-an-approved-envelope); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-03, CMP-04, CMP-08; REQ-003; D008/D026; OPEN-14. Additional affected records: D004/D008/D026/D034/D052, REQ-003/006/007/021.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.


### D085 — Source-gap continuation and versioned recovery

**Status:** ACCEPTED. **Normative:** true.

**Problem:** OPEN-15 requires an explicit scoped policy before affected operations.

**Decision, reason and alternative:** retain the current archive and SRC-001 through SRC-008 exactly. Continue using the already authorized source-limited reconstruction. New recovery is a separately versioned evidence set with checksums, provenance comparison and an affected-decision audit. Never synthesize a missing image, file body or acceptance message. Adopt the complete policy, rationale, alternatives, limits and acceptance cases in [contract section 15](14_RETAIL_RESEARCH_CONTRACT.md#15-open-15-source-gap-policy); the short entry does not replace that contract.

**Affected components / dependencies:** CMP-04, CMP-06, CMP-08, CMP-12; REQ-007; D008/D026; OPEN-15. Additional affected records: D008/D043, source audit and all source-qualified decisions.

**Source and acceptance:** SESSION-2026-10-23-CLOSURE; the user's verbatim "Freigabe" adopts proposal v0.1 for binding specification integration, as recorded in [the approval record](14_RETAIL_RESEARCH_CONTRACT.md#approval-and-version-resolution). This is new approval, not retrospective archival attribution.

**Change control:** D008/D026; research-contract/1.0. Preserve historical versions, original outcomes and exposure; material changes require a new approved version. Runtime implementation and empirical verification are not asserted.

### D086 — Purposeful inquiry and assumption checking for agents

**Status:** ACCEPTED. **Normative:** true.

**Problem:** Agents can inherit a misleading question, substitute a different investigation object, or collect information without explaining what it clarifies.

**Decision, reason and alternative:** Adopt [Agent Inquiry Discipline / agent-inquiry/1.0](15_AGENT_INQUIRY_DISCIPLINE.md): identify the object, explain targeted clarification value while permitting open exploration, challenge assumptions without an objection quota, and retain a concise purpose/finding/conclusion/uncertainty/next-action summary at work boundaries. Reuse existing roles and records. No single decisive-question requirement, automatic score, compulsory mode controller or added scientific authority.

**Affected components / dependencies:** CMP-01, CMP-02, CMP-03, CMP-06, CMP-07, CMP-11, CMP-12; REQ-014 and future TEST-14 extensions; IF-02/03/08; D001/D002/D008/D014/D016/D026/D028/D030/D070/D079/D082. Repository instructions and review discipline apply the same scoped practice.

**Source and acceptance:** SESSION-2026-10-24-INQUIRY. The user explicitly approved the preceding reviewed proposal and GitHub publication: "Ok, das übernehmen wir so. Schreib es rein. Dann github updaten". See [approval and scope](15_AGENT_INQUIRY_DISCIPLINE.md#approval-and-scope). This is a new session source, not an attribution to the original archive.

**Change control:** D008/D026; agent-inquiry/1.0. Preserve prior decisions, scientific contracts, source bytes and exposure history. Future rollback records supersession and restores the previous applicable configuration without deleting history. Runtime behavior and effectiveness are unverified.

### D087 — Automatic invocation of temporal diagnostics for intended use

**Status:** ACCEPTED. **Normative:** true.

**Problem:** A predeclared applicability diagnostic can be forgotten or silently skipped when newly eligible outcomes arrive or a policy is considered for use.

**Decision, reason and alternative:** Adopt [Temporal Diagnostic Invocation / temporal-diagnostic-invocation/1.0](16_TEMPORAL_DIAGNOSTIC_INVOCATION.md). A versioned plan binds the object, inputs and future checkpoints before monitored outcomes are inspected. A committed batch of complete, eligible outcomes automatically checks whether the next checkpoint is due; intended use always checks scope and freshness. A due approved diagnostic runs without a manual reminder, while missing inputs or capability remain visible as NOT_ASSESSED/REVIEW_REQUIRED. Duplicate deliveries and corrected data retain trial identity and provenance. This does not select a statistical method or grant live authority; a generic rolling-profit alarm for every idea is not adopted.

**Affected components / dependencies:** CMP-01, CMP-06, CMP-07, CMP-08, CMP-10, CMP-11; REQ-008/017/025 and future TEST-17/25 extensions; IF-11; D008/D020/D026/D037/D080/D083/D084, DEF-027.

**Source and acceptance:** SESSION-2026-10-24-TEMPORAL-DIAGNOSTIC. After the [reviewable proposal v0.2](../reviews/TEMPORAL_DIAGNOSTIC_AUTOMATION_PROPOSAL_2026-10-24.md) defined the eligible-outcome event in response to the user's clarification, the user explicitly replied "freigegeben". See [approval and scope](16_TEMPORAL_DIAGNOSTIC_INVOCATION.md#approval-and-scope). This later session is separate from the original source archive.

**Change control:** D008/D026; temporal-diagnostic-invocation/1.0 extends research-contract/1.0 section 13. Preserve earlier contracts and all plans, attempts, outcomes and exposure. A changed scientific method or live action rule requires separate approval. Runtime behavior, false-alarm calibration and economic benefit remain unverified.

### D088 — Background temporal work and visible user reporting

**Status:** ACCEPTED. **Normative:** true.

**Problem:** An authorized diagnostic or method comparison can remain blocked, overdue or completed without the user noticing; an absent data event can leave stale information unseen.

**Decision, reason and alternative:** Adopt [Monitoring Visibility and Reporting / monitoring-visibility/1.0](17_MONITORING_VISIBILITY_AND_REPORTING.md). Run a bounded, authorized temporal-method comparison automatically once its predeclared plan and inputs are ready, while D087 continues to invoke approved diagnostics at their own checkpoints. Retain pending work and delivery state; send a weekly status report and prompt notice for new actionable events. A reporting tick never creates a quantitative look. The LLM summarizes source-bound records but cannot select a method, change evidence or authorize capital. Reuse existing monitoring, dashboard and improvement roles; no new edge status, service or generic profit alarm is adopted.

**Affected components / dependencies:** CMP-01/06/07/08/10/11/12; REQ-017/022/025 and future TEST-17/22/25 extensions; IF-11/13; D008/D020/D026/D037/D080/D083/D084/D087.

**Source and acceptance:** SESSION-2026-10-24-MONITORING-VISIBILITY. The user accepted the preceding bounded method-comparison direction and requested background execution, prompt contact and status reports; a follow-up clarification selected the future Framework function, weekly reports and immediate actionable notices, without a separate Codex reminder. See [approval and scope](17_MONITORING_VISIBILITY_AND_REPORTING.md#approval-and-scope). This is a later current-session source, not an addition to the original archive.

**Change control:** monitoring-visibility/1.0 specifies operational orchestration and reporting. Scientific method activation remains under D008/D026/D084 and live authority under D080. Preserve prior contracts and all plans, attempts, reports, notices, delivery failures and exposure. Runtime scheduling, message delivery, behavioral tests and economic usefulness are unverified.
