# Canonical Definitions: Version Resolution

Active extension: **research-contract/1.0**, adopted by D071-D085 on October 23, 2026. The [Retail Research Contract](14_RETAIL_RESEARCH_CONTRACT.md) supplies the full normative meaning and acceptance cases. The complete reconstruction-1 text below is preserved as a legacy version, including the verbatim M0072 quotation and formulas; its open-status annotations describe that earlier version.

For a new scoped manifest, resolve the following existing definition IDs as `(definition_id, research-contract/1.0)`. Other IDs keep reconstruction-1 meaning. A frozen legacy manifest retains its original version. No ambiguous legacy field is silently inferred. The prior bytes are also retained in the [preapproval archive](../reviews/adoption-2026-10-23/preapproval-documents.zip).

| Definition IDs | research-contract/1.0 extension | Authority |
|---|---|---|
| DEF-003 through DEF-008, DEF-013, DEF-023, DEF-031/032 | Typed JSON AST, explicit estimand/units/time/missingness; all five forms remain representable; unsupported evaluation stays a gap. Condition-versus-whole-scope means are resampled jointly | D074; contract section 4 |
| DEF-007/008/012/018/021/022 | Fixed historical-batch-v1 interval and minimum-effect rules; negative concerns the claimed relevant effect, not exact zero; resource STOP is separate from a scientific negative | D075; section 5 |
| DEF-011/012/026 | Explicit descriptive cohort denominators/cutoff; no replicated/tested truth prior or posterior. Outcome base rates remain possible power inputs | D073; section 3 |
| DEF-014 through DEF-024, DEF-027 | Separate execution stage, technical validity, primary outcome, origin, historical qualification, replication, usability, current applicability and action authority. Historical readiness does not require calendar waiting | D071; section 1 |
| DEF-024 | Unknown exposure is null plus reason, not proof of exposed or unseen origin; procedural holdout does not erase ancestry | D071/D076/D082; sections 1/6/12 |
| DEF-015/027 | Dependency invalidation changes usability, not historical outcome; current applicability is timestamped and defaults to NOT_ASSESSED | D083; section 13 |
| DEF-028/029 | Scope membership alone supplies no subgroup evidence; direct target evaluation or separately approved transport contract is required for EVIDENCE_BACKED | D072; section 2 |
| DEF-013/024/031/033 | Scoped data profile and next-eligible-bar execution with explicit cost/PIT uncertainties; unknown costs are not zero | D076; section 6 |
| Certification of all affected definitions | Independent automatic conformance within approved semantics; new meaning or uncertain envelope membership requires material-change review | D084; section 14 |

The scoped overlay does not replace a definition's unrelated fields. Section 1 owns migration/projection and section 13 owns applicability consequences. Unknown origin/replication/applicability remains unknown; retries do not create replication. No runtime records have been migrated.

## Preserved reconstruction-1 (historical version)

# Canonical Definitions and Formula Preservation

Version: reconstruction-1. Semantic governance: D008, M0071–M0072 and M0241–M0243. English explanations do not replace original mathematical definitions. Material changes require user approval. Ambiguity blocks affected future operations, not the present source-limited documentation work.

## Definition registry

| ID | Term | Meaning / boundary | Source |
|---|---|---|---|
| DEF-001 | PIT context | Allowed data, certified features, knowledge and history snapshots at t; event time alone is insufficient | M0072 §6.1 |
| DEF-002 | Generator version | Concrete model, prompt/protocol and allowed context/runtime configuration; material changes create a new version | M0072 §6.2 |
| DEF-003 | H_idea / H_exec | Free possibly incomplete idea versus operationalized machine-readable claim; an executable draft is not yet frozen | M0072 §6.3 |
| DEF-004 | Relationship forms | Difference, association, change, boundary and interaction are expression capabilities, not a closed idea catalog | M0072 §6.4 |
| DEF-005 | General/state/episode | Population claim, current-state assertion and case-specific expectation; one successful episode does not confirm a general claim | M0072 §6.5 |
| DEF-006 | Feature | Versioned function/composition with all inputs and parameters specified; add units, missingness and time semantics to its execution contract | M0072 §6.6; M0067 |
| DEF-007 | Scope baseline | Binary outcome rate over all eligible cases in the frozen scope, not only cases satisfying the hypothesis condition | M0072 §6.7 |
| DEF-008 | Delta | Conditional rate minus scope rate; a raw contrast, not significance, causality or economic edge | M0072 §6.8 |
| DEF-009 | Q_H_pre / V_H_OOS | Ex-ante quality frozen before outcome versus empirical validation result with evidence-origin qualification | M0072 §6.9; M0102; M0154 |
| DEF-010 | Non-executable rate | NOT_TESTABLE_YET ideas divided by registered ideas in a declared cohort/version, by reason; zero denominator is undefined | M0072 §6.10 |
| DEF-011 | Trial counts | Generated, frozen, evaluated and supported are different stages; negatives and failures remain in history | M0072 §6.11 |
| DEF-012 | N_min | Policy-determined required sample using outcome type, relevant effect, outcome base rate, power where relevant, error control and dependence | M0072 §6.12; M0158 |
| DEF-013 | Feature availability | All required information must actually have been available before use; bar label is insufficient | M0072 §6.13 |
| DEF-014 | Replication | New evidence not used for initial support is necessary; overlap, ancestry and dependence still need assessment | M0072 §6.14; M0092 |
| DEF-015 | Dependency invalidation | Revoked relevant infrastructure removes usability of dependent evidence; retain old record and append invalidation | M0072 §6.15 |
| DEF-016 | Primary lifecycle | The original prospective lifecycle is preserved below; historical execution needs an explicit versioned extension | M0072 §6.16; M0101–M0102 |
| DEF-017 | Not testable | Preserve the idea and typed missing capability; retry on relevant infrastructure change; no empirical negative result | M0072 §6.17 |
| DEF-018 | Primary outcomes | TESTED_NEGATIVE, TESTED_INCONCLUSIVE and SUPPORTED_INITIAL follow the frozen rule; non-significance is not automatically negative | M0072 §6.18 |
| DEF-019 | Replication lifecycle | Separate replication plan and result; failure does not automatically prove a zero effect | M0072 §6.19 |
| DEF-020 | Technical error | Affected execution provides no support or falsification of the market claim | M0072 §6.20 |
| DEF-021 | Fixed horizon | Evaluate primary result only at frozen trigger; no opportunistic early success | M0072 §6.21 |
| DEF-022 | Sequential evaluation | A valid sequential policy must be frozen before testing; repeated peeking alone is not valid | M0072 §6.22 |
| DEF-023 | Hypothesis / policy | Empirical claim versus action prescription; a combination has its own evidence | M0084; M0138; M0144 |
| DEF-024 | Evidence origin | TRAINING_EXPOSED_HISTORY, MODEL_UNSEEN_HISTORY and TRUE_FORWARD retain different provenance; unknown exposure cannot be certified unseen | M0154–M0156 |
| DEF-025 | Exposure | Information influencing an idea or any used ancestor, including queries, sources, memory and selection feedback | M0106; M0112; M0166–M0168 |
| DEF-026 | SUPPORTED_INITIAL | Passed predefined primary test; not a probability that the hypothesis is true | M0158–M0160 |
| DEF-027 | Current applicability | Whether prior supported knowledge applies under current monitored conditions; distinct from historical evidence | M0138; M0146; M0216 |
| DEF-028 | Rule basis / parameter origin | EVIDENCE_BACKED, UNTESTED_ASSUMPTION or OPERATIONAL_CONSTRAINT; separately FIXED_EX_ANTE, DERIVED or FITTED | M0142; M0144 |
| DEF-029 | Scope relation | IN_SCOPE, SCOPE_SUBSET, EXTRAPOLATION or INCOMPATIBLE; automatic subset transport is disputed in OPEN-02 | M0144 |
| DEF-030 | Memory classes | Journal: events; Market Model: qualified claims; Research Experience: heuristics; Policy Experience: operational/policy learning | M0166–M0168 |
| DEF-031 | Time coordinates | Observation timeframe, event/effective time, available_at, processing latency, outcome and invalidation horizons are distinct | M0098; M0116; M0162 |
| DEF-032 | Column classes | Entry-known values, evolving decision-time state, completed full-path diagnostics | M0260; M0262 |
| DEF-033 | Derived availability | Maximum required-input availability plus relevant processing latency strengthens the original availability predicate | M0162–M0164 |
| DEF-034 | Selection trial | Outcome-dependent choice among claims, features, parameters, policies or generator versions; retain candidates, data and selector | M0190; M0220; M0276 |
| DEF-035 | Null contract | Exact null, target relationship destroyed, nuisance structure preserved, benchmark and validity assumptions | M0276–M0278 |
| DEF-036 | Meaningful improvement | Acceptance criterion met, reproducible defect fixed, measured risk reduced, required function completed or relevant cost/performance improvement without regression | M0187–M0188; M0224 |
| DEF-037 | Nontrivial novelty | Useful new relation, boundary, transfer or consequence; no promise of global originality and no mandatory novelty score | M0048; M0110; M0150 |
| DEF-038 | State / effect persistence | Continued state membership versus duration of a relevant relationship; neither implies the other | M0082 |

## Later formulas and qualifications

FORM-001 through FORM-022 identify subsections 6.1 through 6.22 of the exact quotation below, including symbolic definitions and transitions. Later expressions are separately attributed; examples do not establish universal estimators or thresholds.

| ID | Expression in ASCII | Meaning / limit | Source |
|---|---|---|---|
| FORM-023 | `effect_H = E(Y given Conditions_H, Scope_H) - E(Y given Scope_H)` | Editorial rendering of continuous outcome contrast; not causal identification | M0080 |
| FORM-024 | `net_edge = gross_edge - fees - spread - slippage - market_impact` | Original expression; model components must avoid double counting | M0080 |
| FORM-025 | `PPV = (power * pi) / ((power * pi) + (alpha * (1 - pi)))` | ASCII rendering of idealized mixture; not automatically an individual posterior after adaptive selection | M0158 |
| FORM-026 | `feature_available_at = max(required_input_available_at) + required_processing_latency` | Later explicit availability refinement | M0162 |
| FORM-027 | `delta_R(h) = E[R(t,t+h) given Signal_t] - E[R(t,t+h) given Scope_t]` | Editorial rendering of event-study contrast; choosing the winning horizon is another selection | M0272 |
| FORM-028 | `variance_P = w1^2*variance_1 + w2^2*variance_2 + 2*w1*w2*rho12*sigma1*sigma2` | ASCII rendering of two-strategy covariance formula; historical correlation is not a future guarantee | M0280 |

Exact TeX annotations for M0280 remain in `sources/structured_content.json`. For FORM-025, pi=0.01, power=0.8 and alpha=0.05 gives approximately 13.91%; pi=0.05 gives 45.71%. These are arithmetic illustrations, not measured research success rates.

## Unresolved semantics

- OPEN-01: Historical branch and orthogonal evidence/validity/applicability dimensions must not rewrite the original state machine.
- OPEN-02: A supported aggregate does not guarantee support in every scope subset.
- OPEN-03: Replication frequency is not an unbiased estimate of true-effect prevalence.
- OPEN-04: Corr notation alone does not specify nonlinear dependence, weighting, missingness or the estimator.
- The scope baseline includes conditioned cases. Independent-sample uncertainty formulas are inappropriate unless justified by the actual design.
- A probabilistic claim is not falsified by every single nonoccurrence. Counterexamples must target the actual population or distributional assertion.

## Exact original quotation: M0072 section 6

The following German source quotation is retained under the English-language policy's quotation exception. Its original expressions and explanatory text are unchanged. The registry above interprets them but does not override them.

Source block SHA-256: `67090081ba1ed08f025ac36cff300cd9550e51d5907edeb6f928b6a8fd6de647`.

~~~~text
6. Verbindliche Formeln und Definitionen
6.1 Point-in-Time-Kontext
C_t = { D_<=t, F_t, K_t, R_t }

C_t ist der vollständige zulässige Informationskontext eines Generatoraufrufs zum Zeitpunkt t.

D_<=t sind sämtliche zulässigen Marktdaten, die zum Zeitpunkt t bereits verfügbar waren.

F_t ist die zum Zeitpunkt t zertifizierte Feature-Bibliothek.

K_t ist der zu diesem Zeitpunkt gültige Snapshot der Wissensbasis.

R_t ist die zulässige Research-Historie, soweit sie keine verbotenen zukünftigen Informationen enthält.

D_>t not_in C_t

D_>t bezeichnet alle Markt- oder Outcome-Daten, die zeitlich nach dem Point-in-Time-Snapshot t liegen.

not_in bedeutet, dass diese Informationen dem Generator vor Freeze und prospektiver Prüfung technisch nicht zugänglich sein dürfen.

6.2 Generatorparameter
G = G(D_t; M, P, C)

G ist eine konkrete Hypothesengenerator-Instanz.

D_t ist der zulässige Point-in-Time-Datenstand.

M ist die konkrete Modellversion.

P ist das verwendete Prompt-/Generierungsprotokoll.

C ist der zusätzliche zugelassene Kontext einschließlich Wissensbasis, Featurekatalog und Runtime-Konfiguration.

Eine materielle Änderung an M, P oder C erzeugt eine neue Generatorversion.

6.3 Zwei Hypothesenrepräsentationen
H_idea != H_exec

H_idea ist die freie, noch nicht zwingend ausführbare Hypothesenidee.

H_exec ist die vollständig operationalisierte, maschinenlesbare Hypothese für Compiler und Testengine.

Die Ungleichheit bedeutet, dass beide Artefakte unterschiedliche Funktionen besitzen und nicht zusammengelegt werden dürfen.

6.4 Hypothesenklassen
Unterschiedshypothese
mu_1 != mu_2

mu_1 ist der Erwartungswert bzw. die zentrale Zielgröße der ersten definierten Gruppe oder Bedingung.

mu_2 ist die entsprechende Zielgröße der zweiten Gruppe oder Bedingung.

!= bezeichnet eine ungerichtete Unterschiedshypothese.

Eine gerichtete Fassung kann entsprechend als mu_1 > mu_2 oder mu_1 < mu_2 spezifiziert werden.

Zusammenhangshypothese
Corr(X, Y) != 0

X und Y sind zwei definierte Merkmale oder Größen.

Corr(X, Y) bezeichnet ein vorab festgelegtes Zusammenhangsmaß; die konkrete Auswertungsmethode muss zum behaupteten Zusammenhang passen.

!= 0 bedeutet, dass ein systematischer Zusammenhang behauptet wird.

Veränderungshypothese
mu_after != mu_before

mu_before ist die definierte Zielgröße vor einem Ereignis oder Zustandswechsel.

mu_after ist dieselbe Zielgröße nach dem definierten Ereignis oder Zustandswechsel.

!= bezeichnet eine behauptete Veränderung.

Randbedingung
effect(A, B | C)

A und B sind die Größen, zwischen denen eine Beziehung behauptet wird.

C ist eine Bedingung oder ein Geltungsbereich, unter dem die Beziehung untersucht wird.

Die konkrete Effektdefinition wird in H_exec spezifiziert.

Interaktion / Moderator
effect(A, B) depends_on C

A und B definieren die primäre Beziehung.

C ist ein Moderator bzw. eine Variable, von deren Ausprägung sich Stärke oder Richtung der primären Beziehung ändern soll.

depends_on muss in der Hypothesensprache in eine konkrete ausführbare Interaktion übersetzt werden.

6.5 Allgemeine, State- und Episodenhypothese
H_general
H_state
H_episode

H_general ist eine allgemeine Behauptung über eine wiederkehrende Klasse von Marktfällen.

H_state ist eine Hypothese über den aktuellen Zustand eines konkreten Marktes zu einem bestimmten Zeitpunkt.

H_episode ist eine bedingte Erwartung über die weitere Entwicklung eines konkreten aktuellen Falls.

Diese drei Klassen dürfen nicht als Evidenzebenen miteinander verwechselt werden. Ein korrektes einzelnes H_episode bestätigt nicht automatisch H_general.

6.6 Feature-Definition
F = f(X_1, X_2, ..., X_n; theta)

F ist ein berechenbares Feature.

f ist die versionierte Berechnungsfunktion bzw. Komposition zertifizierter Primitive.

X_1 ... X_n sind die benötigten Eingangsgrößen.

theta sind sämtliche Parameter der Feature-Berechnung.

Alle Inputs und Parameter müssen vor Verwendung in einer eingefrorenen Hypothese eindeutig spezifiziert sein.

6.7 Basisrate und bedingtes Outcome
base_rate_H = P(Y | Scope_H)

base_rate_H ist die Basisrate des Outcomes für Hypothese H.

Y ist das definierte Outcome.

Scope_H ist der vor Freeze definierte Geltungsbereich von H.

Alle prospektiv auftretenden Fälle in Scope_H werden zur Basisrate gezählt, unabhängig davon, ob die Hypothesenbedingungen erfüllt sind.

conditional_rate_H = P(Y | Conditions_H, Scope_H)

conditional_rate_H ist die Outcome-Rate für Fälle, die sowohl zum Scope gehören als auch die eingefrorenen Bedingungen der Hypothese erfüllen.

Conditions_H sind die in H_exec festgelegten Bedingungen.

Scope_H ist derselbe Geltungsbereich wie bei base_rate_H.

6.8 Baseline-relative Hypothesenabweichung
delta_H = P(Y | Conditions_H, Scope_H) - P(Y | Scope_H)

delta_H ist die rohe bedingte Abweichung der Hypothese von ihrer Basisrate.

Y ist das definierte Outcome.

Conditions_H sind die eingefrorenen Hypothesenbedingungen.

Scope_H ist der eingefrorene Geltungsbereich.

Ein positives delta_H bedeutet bei einem positiv definierten Outcome eine höhere Rate unter den Hypothesenbedingungen als in der gesamten Scope-Population. Es ist noch kein Signifikanz- oder Evidenzmaß.

6.9 Ex-ante-Hypothesenqualität und OOS-Validierung
Q_H_pre

Q_H_pre bezeichnet die vor Kenntnis des Validierungs-Outcomes festgehaltene Qualität einer Hypothese nach den definierten Prozesskriterien.

Diese Größe darf nicht rückwirkend aufgrund des Testergebnisses verändert werden.

V_H_OOS

V_H_OOS bezeichnet das empirische Validierungsergebnis einer Hypothese auf den dafür vorgesehenen unabhängigen bzw. prospektiven Daten.

Q_H_pre und V_H_OOS sind getrennte Größen.

6.10 Nicht-Ausführbarkeitsrate
non_executable_rate = N_not_testable / N_H_idea

non_executable_rate ist der Anteil registrierter Hypothesenideen, die mit der aktuellen Infrastruktur nicht ausführbar sind.

N_not_testable ist die Anzahl der H_idea, die den Status NOT_TESTABLE_YET erhalten.

N_H_idea ist die Gesamtzahl registrierter Hypothesenideen im betrachteten Zeitraum bzw. in der betrachteten Version.

Die Rate ist nach Nicht-Ausführbarkeitsgrund aufzuschlüsseln.

6.11 Trial-Register-Zählgrößen
N_generated
N_frozen
N_evaluated
N_supported

N_generated ist die Anzahl registrierter H_idea.

N_frozen ist die Anzahl der Hypothesen, die mit vollständigem Auswertungsplan eingefroren wurden.

N_evaluated ist die Anzahl abgeschlossener primärer Evaluationen.

N_supported ist die Anzahl der Hypothesen, denen die Status-Engine nach der vorab festgelegten Policy einen Support-Status zugewiesen hat.

Keine dieser Größen darf gescheiterte oder negative Hypothesen aus dem Register entfernen.

6.12 N_min
N_min = EvaluationPolicy(outcome_type, minimum_relevant_effect, pre_freeze_base_rate, power_target, error_control, dependence_design)

N_min ist die minimale für die primäre Evaluation erforderliche Fallzahl.

outcome_type ist der Typ des Outcomes.

minimum_relevant_effect ist die vorab definierte kleinste praktisch relevante Effektgröße.

pre_freeze_base_rate ist die zulässige, vor Freeze bestimmte Basisratenannahme.

power_target ist das vorab definierte Power-Ziel, sofern für das gewählte Evaluationsverfahren relevant.

error_control bezeichnet die vorab festgelegte Fehler- bzw. Multiple-Testing-Policy.

dependence_design beschreibt die für die Stichprobenlogik relevante Abhängigkeitsstruktur.

Die konkrete Funktion EvaluationPolicy ist noch technisch auszuarbeiten; der Generator darf N_min nicht selbst wählen.

6.13 Feature-Verfügbarkeit
feature_available_at(t) only_if all_required_inputs_available_at_or_before(t)

feature_available_at(t) bedeutet, dass ein Feature zum Zeitpunkt t als Input einer Hypothese verwendet werden darf.

all_required_inputs_available_at_or_before(t) bedeutet, dass sämtliche für seine Berechnung verwendeten Informationen spätestens zu diesem Zeitpunkt tatsächlich bekannt waren.

Der Zeitstempel des zugrunde liegenden Marktintervalls allein genügt nicht; maßgeblich ist der tatsächliche Availability-Zeitpunkt.

6.14 Evidenzstatus
SUPPORTED_REPLICATED requires new_evidence_not_used_for SUPPORTED_INITIAL

SUPPORTED_INITIAL ist der erste durch die festgelegte Evaluation Policy vergebene positive Evidenzstatus.

SUPPORTED_REPLICATED ist ein separater höherer Status.

new_evidence_not_used_for SUPPORTED_INITIAL bedeutet, dass die Replikation auf Evidenz beruhen muss, die nicht bereits für den initialen Support verwendet wurde.

6.15 Dependency-Invalidierung
revoked_dependency => dependent_result_status = INVALIDATED_BY_DEPENDENCY

revoked_dependency ist eine widerrufene Feature-, Compiler-, Daten- oder sonstige relevante Infrastrukturversion.

dependent_result_status ist der Evidenzstatus jedes Testergebnisses, das von dieser Dependency abhängt.

INVALIDATED_BY_DEPENDENCY bedeutet, dass das Ergebnis nicht länger als gültige Evidenz verwendet werden darf, bis es mit zulässigen Dependencies neu berechnet wurde.

6.16 Primärer Hypothesen-State-Übergang
IDEA_CREATED
-> FORMALIZING
-> EXECUTABLE
-> EVALUATION_POLICY_ASSIGNED
-> FROZEN
-> COLLECTING_PROSPECTIVE_CASES
-> READY_FOR_EVALUATION
-> EVALUATED

IDEA_CREATED bedeutet, dass eine H_idea registriert wurde.

FORMALIZING bedeutet, dass daraus eine ausführbare Spezifikation erstellt wird.

EXECUTABLE bedeutet, dass Compiler und Dependencies die Ausführung zulassen.

EVALUATION_POLICY_ASSIGNED bedeutet, dass alle für den Freeze notwendigen Auswertungsregeln feststehen.

FROZEN bedeutet, dass Hypothese, Dependencies und Evaluation Plan unveränderlich versioniert wurden.

COLLECTING_PROSPECTIVE_CASES bedeutet, dass neue Fälle nach dem eingefrorenen Scope gesammelt werden.

READY_FOR_EVALUATION bedeutet, dass die vorab definierte Evaluationsbedingung erreicht wurde.

EVALUATED bedeutet, dass die primäre Code-Evaluation abgeschlossen ist.

6.17 Alternativer State bei fehlender Ausführbarkeit
FORMALIZING -> NOT_TESTABLE_YET

NOT_TESTABLE_YET bedeutet, dass die Idee erhalten bleibt, aber mit der aktuellen Daten-, Feature-, Sprach- oder Evaluationsinfrastruktur noch nicht ausgeführt werden kann.

NOT_TESTABLE_YET -> RETRY_ON_INFRA_CHANGE

RETRY_ON_INFRA_CHANGE bedeutet, dass eine passende Infrastrukturänderung eine erneute automatische Prüfung der Hypothese auslösen darf.

6.18 Ergebnisstatus nach Evaluation
EVALUATED -> TESTED_NEGATIVE
EVALUATED -> TESTED_INCONCLUSIVE
EVALUATED -> SUPPORTED_INITIAL

TESTED_NEGATIVE bedeutet, dass die vorab definierte primäre Evaluation gegen die Hypothese ausfiel.

TESTED_INCONCLUSIVE bedeutet, dass die Evaluation keine ausreichende Entscheidung nach der festgelegten Policy zulässt.

SUPPORTED_INITIAL bedeutet, dass die primäre Evaluation die vorab definierten Support-Kriterien erfüllt.

6.19 Replikationsstatus
SUPPORTED_INITIAL -> REPLICATION_TRACK

REPLICATION_TRACK bedeutet, dass die Hypothese auf neuer, nicht für den initialen Support verwendeter Evidenz weiter geprüft wird.

REPLICATION_TRACK -> SUPPORTED_REPLICATED
REPLICATION_TRACK -> REPLICATION_FAILED

SUPPORTED_REPLICATED bedeutet erfolgreiche Replikation nach der dafür festgelegten Policy.

REPLICATION_FAILED bedeutet, dass die Replikationsprüfung die festgelegten Anforderungen nicht erfüllt hat.

6.20 Fehlerregel
technical_error => no_evidence_for_or_against_H

technical_error ist ein technischer Fehler wie Datenfehler, Look-ahead-Verletzung, Featurefehler, Compilerfehler, Executionfehler, Evaluationfehler oder Isolation Violation.

no_evidence_for_or_against_H bedeutet, dass ein davon betroffener Fall oder Testlauf nicht als empirische Unterstützung oder Widerlegung der Hypothese gewertet werden darf.

6.21 Fixed-Horizon-Evaluation
evaluate_H only_when evaluation_trigger_H is reached

evaluate_H ist die primäre Hypothesenauswertung.

evaluation_trigger_H ist die vor Freeze festgelegte Bedingung, etwa N_min oder ein fixes Datum.

Vor Erreichen des Triggers darf ein Zwischenstand nicht opportunistisch als endgültiges Testergebnis behandelt werden.

6.22 Sequential-Evaluation
sequential_evaluation_allowed only_if sequential_policy_H frozen_before_test

sequential_evaluation_allowed bedeutet, dass eine Hypothese während der Datensammlung formal laufend ausgewertet werden darf.

sequential_policy_H ist das dafür verwendete, vor Freeze spezifizierte sequenzielle Verfahren.

Ohne eine solche eingefrorene Policy ist wiederholtes Nachsehen keine zulässige primäre Evaluation.
~~~~
