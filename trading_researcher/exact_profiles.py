"""Construct future AST4 role requests; no provider, epoch or native admission."""
from copy import deepcopy
import hashlib

from .auxiliary import PROFILE_FIELDS, reporting_contract, request_for, require
from .codec import canonical, digest, integer, text
from .exact_research import contract_packet
from .meaning_reviews import PROMPT, PROTOCOL

BASE_VERSION='faithful-native-formalization/3'
BASE_PROMPT_SHA256='8752022153d1291a684eee9535224937ced3c4f1b01518411f8ee01f2593389b'
VERSION='faithful-exact-formalization/4'
SCHEMA='exact-role-profile-construction/1'
STATUS='PREPARED_NOT_ADMITTED'

# Replace only language-specific paragraphs. Every shared faithfulness, gap,
# source, enclosure, reporting and compact-output instruction remains inherited.
PARAGRAPHS={
1: '''Require expression_contract.schema="bounded-exact-compositions/1.0" with all verbatim host contracts. Use hypothesis-exec/3 and research-ast/4 for all programs; formalization-record/3 is host-owned. No paired/legacy branch. An incompatible packet or unrepresentable original is a gap, never permission to change either. Historical examples/ideas, proposals and consumed allocations neither replace this original nor reopen grants or authorize operators/limits. No historical horizon,date,threshold or episode is a default.''',
2: '''Candidate has exactly schema="hypothesis-exec/3", idea_ref, claim_kind, estimand, scope_ast, condition_ast, outcome, comparator, horizons, test_universe, parameter_origins, feature_refs. test_universe={start,end,instruments,data_snapshot_ref}, with exactly the original single instrument; end is exclusive, instants exact UTC Z strings. Each program={schema:"research-ast/4",catalog_hash,expression}. catalog_hash=digest(catalog.body.features), not the body, envelope or artifact ID; feature_refs the sorted exact versioned feature closure. Scope/condition must be Boolean.''',
3: '''Installed claim_kind="difference", comparator={kind:"whole_scope"}; estimand has exactly kind="conditional-minus-scope-mean/1", unit="basis_points", weighting="equal_rows", missingness="scope-true-outcome-observed/1", condition_unknown="exclude-from-condition-retain-in-scope", nuisance_fit="none", direction=positive|negative|nondirectional. It computes mean(Y|C,S)-mean(Y|S), not condition versus complement. All S=true observed Y enter the baseline, including C=unknown; only C=true enters the conditional mean. Do not substitute this for another original question; other relationships, units or estimators are gaps. outcome={program,scale:"quantity"} requires real Y/basis_points.''',
4: '''Expression nodes, exact fields: literal {op,type,unit,value}; feature {op,ref}; add/sub/mul/div/lt/le/gt/ge/eq/and/or {op,left,right}; not/ln/abs {op,arg}; lag/trailing_mean/trailing_median/trailing_product/trailing_all {op,arg,bars}; integer_power {op,arg,exponent}. Real literals use type="real", explicit unit and decimal-string/null value, never JSON floats; Boolean literals use type="boolean",unit=null,value=true|false|null. Add/sub require matching real units; comparisons matching scalar types/units; mul needs a ratio; matching-unit div yields ratio, a ratio denominator preserves numerator units. Zero denominators/missing arithmetic are missing; Boolean logic is three-valued. No if, quantile, stddev, feature_at or dynamic traversal. Preserve 256 nodes/32 levels,8192-bit rationals and10000000 shared numerical/diagnostic primitive steps; do not change the original to fit.''',
5: '''lag is a nonnegative same-instrument 900-second shift; complete causal windows include their anchor. No nearest rows,shortened windows,interpolation or fitted replacements. Lag/window/exponent integers are at most1000000; windows/exponents positive,never Boolean. Explicit lag places windows before events. Median:middle sorted value if odd,exact mean of two central values if even. Power/product:exact real dimensionless ratios,no log/enclosed child. Power:LSB binary exponentiation,charge every bit/attempted multiply,check reduced intermediates before/after multiplication. Product/all:every slot oldest to newest even after zero,false,unknown;charge folds/children/known multiplications,retain unknowns,never reorder cancellation. trailing_all is Kleene AND,not a whole-condition guard. ln:outcome-only strictly positive finite ratio;missing/nonpositive stays missing,no clipping. abs:outcome-only,preserving units,missingness and outward bounds,including zero-crossing. No decision abs/log or bounded comparison. Positive ratio does not prove both endpoints positive. Preserve every original finite/valid-input rule and whole-condition unknown if any required input fails,even when another predicate is false. G(V,P)=(V AND P) OR ((NOT V) AND unknown):derive/justify V from the original;recognition is not validity proof. No hypothesis/threshold replacement.''',
6: '''horizons={grid_seconds:900,outcome_bars:h},never an array;h is the original positive integer,not a supplied constant. Outcomes run at t+h*900;lags are relative to that future anchor. Scope/condition obey the original decision cutoff. Required-inputs/1 outcome cutoff is min(as_of,end-1second),not an implicit anchor cutoff. Derive original endpoint/availability equivalence from complete evidence,not a delay assumption. Unused expression/anchor coordinates need no market row;every required raw feature/window read must exist and be available. Keep all grid coordinates and original unknown/missing rules. Read complete mathematical,reuse,reporting and availability contracts;missing contract/uncertain membership is a gap. Availability evidence has no outcomes or equivalence authority.'''}


def _profile(value):
    require(type(value) is dict and set(value)==PROFILE_FIELDS,'Complete auxiliary role profile required')
    for key in ('model','prompt_version','prompt'):text(value[key],key)
    require(type(value['generation_parameters']) is dict,'Explicit unchanged generation settings required')
    integer(value['max_output_tokens'],'max_output_tokens',1)
    integer(value['call_timeout_seconds'],'call_timeout_seconds',1)
    integer(value['max_retries'],'max_retries')
    canonical(value)


def build(base,review):
    _profile(base);_profile(review)
    require(base['prompt_version']==BASE_VERSION
        and hashlib.sha256(base['prompt'].encode()).hexdigest()==BASE_PROMPT_SHA256,
        'Only the retained actual generic v3 prompt is a supported source')
    require(review['prompt_version']==PROTOCOL and review['prompt']==PROMPT,'Preserve the complete independent comparison protocol')
    paragraphs=base['prompt'].split('\n\n');require(len(paragraphs)==9,'Unexpected retained v3 structure')
    for index,replacement in PARAGRAPHS.items():paragraphs[index]=replacement
    prompt='\n\n'.join(paragraphs)
    for old,new in (
        ('every literal value, lag/window bars and horizon once','every literal value, lag/window bars, power exponent and horizon once'),
        ('lag/window /bars and /horizons/outcome_bars once','lag/window /bars, integer_power /exponent and /horizons/outcome_bars once')):
        require(prompt.count(old)==1,'Retained origin instruction differs');prompt=prompt.replace(old,new,1)
    prompt=text(prompt,'complete exact formalizer prompt')
    profile=deepcopy(base);profile.update(prompt_version=VERSION,prompt=prompt)
    _profile(profile)
    retained={key:deepcopy(value) for key,value in base.items() if key not in ('prompt','prompt_version')}
    require(canonical(retained)==canonical({key:value for key,value in profile.items() if key not in ('prompt','prompt_version')}),
        'Profile construction changed non-prompt settings')
    contracts={**contract_packet(),**reporting_contract({'reporting_contract':'case-diagnostics/2'})}
    return {'schema':SCHEMA,'status':STATUS,'base_profile':deepcopy(base),'base_profile_sha256':digest(base),
        'base_prompt_sha256':BASE_PROMPT_SHA256,'formalization_profile':profile,'review_profile':deepcopy(review),
        'formalizer_prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),'unchanged_settings_sha256':digest(retained),
        'contracts_sha256':digest(contracts),'prompt_characters':len(prompt),
        'configuration_freshness':'NOT_CHECKED','native_admission':False,'model_behavior_verified':False,
        'resource_limit_change':False,'scientific_readiness':False}


def request_candidate(construction,packet):
    require(type(construction) is dict and {'base_profile','review_profile'}<=set(construction),
        'Complete role construction required')
    require(canonical(construction)==canonical(build(
        construction['base_profile'],construction['review_profile'])),'Modified or stale role construction')
    require(type(packet) is dict and packet.get('schema')=='formalization-input/1'
        and 'paired_contract' not in packet,'Exact scalar formalization packet required')
    expected={**contract_packet(),**reporting_contract({'reporting_contract':'case-diagnostics/2'})}
    require(all(canonical(packet.get(key))==canonical(value) for key,value in expected.items()),
        'The actual full exact/reporting contracts must match their current owner bytes')
    return request_for({'research_call_profile':construction['formalization_profile']},packet)
