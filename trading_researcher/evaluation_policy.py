"""Exact historical-batch-v1 policy arithmetic; not an inference or release authority."""
from copy import deepcopy
from fractions import Fraction

from .codec import Invalid, integer, text
from .outcomes import _read_rational, _rational as _encode_rational


PROFILE = 'historical-batch-v1'
CONTRACT = 'research-contract/1.0'
MAX_RESAMPLES = 19999


def require(condition, message):
    if not condition:
        raise Invalid(message)


def _rational(value):
    value=Fraction(value)
    require(max(value.numerator.bit_length(),value.denominator.bit_length()) <= 8192,
        'RESOURCE_GAP: exact policy arithmetic exceeds the numeric envelope')
    return _encode_rational(value)


def family_budget(primary_count):
    integer(primary_count,'primary count',1)
    require(primary_count <= 8,'The adopted primary family contains at most eight claims')
    return {'profile':PROFILE,'primary_count':primary_count,'family_noncoverage':_rational(Fraction(1,20)),
        'marginal_noncoverage':_rational(Fraction(1,20*primary_count)),
        'interval_sides':2,'allocation':'union_bound','fixed_releases':1,
        'independence_between_claims_required':False,'valid_marginal_coverage_required':True}


def classify_interval(lower, upper, delta, direction):
    """Classify a supplied interval under its frozen direction, without certifying it."""
    low,high,target = map(_read_rational,(lower,upper,delta))
    require(low <= high and target > 0,'Ordered interval and positive relevant effect required')
    require(direction in ('positive','negative','nondirectional'),'Unsupported frozen direction')
    if direction == 'nondirectional':
        # The adopted nondirectional region is explicitly closed; the directional
        # equality clause does not replace this separately specified set rule.
        support = low > target or high < -target
        negative = low >= -target and high <= target
    else:
        if direction == 'negative':
            low,high = -high,-low
        support,negative = low > target,high < target
    return 'SUPPORTED_INITIAL' if support else 'TESTED_NEGATIVE' if negative else 'TESTED_INCONCLUSIVE'


def block_lengths(horizon_bars, base_length):
    integer(horizon_bars,'outcome horizon',1)
    integer(base_length,'base block length',1)
    require(base_length >= horizon_bars,'Base length cannot be shorter than overlapping outcomes')
    require(base_length <= 1000000,'Block length exceeds the admitted reference envelope')
    return sorted({max(horizon_bars,(base_length+1)//2),base_length,2*base_length})


def _ordered_replicates(values):
    """Validate every supplied draw and detach an exact ordered local snapshot."""
    require(type(values) is list and 1 <= len(values) <= MAX_RESAMPLES,'A bounded nonempty replicate list is required')
    return tuple(sorted(_read_rational(item) for item in values))


def _quantile_ordered(ordered, probability):
    """Internal kernel for a fully validated tuple; probability gates stay exact."""
    p = _read_rational(probability)
    require(0 <= p <= 1,'Quantile probability must be between zero and one')
    rank = (len(ordered)-1)*p
    left = rank.numerator//rank.denominator
    remainder = rank-left
    return _rational(ordered[left] if not remainder else ordered[left]*(1-remainder)+ordered[left+1]*remainder)


def quantile(values, probability):
    return _quantile_ordered(_ordered_replicates(values), probability)


def _basic_interval_ordered(point, ordered, alpha):
    # Keep the original intermediate rational envelopes, including alpha/2.
    lower_quantile = _read_rational(_quantile_ordered(ordered,_rational(alpha/2)))
    upper_quantile = _read_rational(_quantile_ordered(ordered,_rational(1-alpha/2)))
    return {'lower':_rational(2*point-upper_quantile),'upper':_rational(2*point-lower_quantile)}


def basic_interval(estimate, replicates, marginal_noncoverage):
    """Small exact arithmetic kernel; caller must separately establish draw validity."""
    point,alpha = _read_rational(estimate),_read_rational(marginal_noncoverage)
    require(0 < alpha < 1,'Marginal noncoverage must be strictly between zero and one')
    _rational(alpha/2)  # Preserve the original tail-envelope failure before draw validation.
    # Undefined replicates fail instead of being discarded and renormalized.
    return _basic_interval_ordered(point,_ordered_replicates(replicates),alpha)


def enclosing_interval(intervals):
    require(type(intervals) is list and 1 <= len(intervals) <= 3,'All prespecified sensitivity intervals are required')
    if any(interval is None for interval in intervals):
        return None
    parsed = []
    for interval in intervals:
        require(type(interval) is dict and set(interval) == {'lower','upper'},'Unexpected interval fields')
        low,high = _read_rational(interval['lower']),_read_rational(interval['upper'])
        require(low <= high,'Interval bounds are reversed')
        parsed.append((low,high))
    return {'lower':_rational(min(pair[0] for pair in parsed)),'upper':_rational(max(pair[1] for pair in parsed))}


def bootstrap_completeness(replicate_count, undefined_count):
    integer(replicate_count,'replicate count',0)
    integer(undefined_count,'undefined count',0)
    require(undefined_count <= replicate_count,'Undefined count exceeds attempted draws')
    return replicate_count == MAX_RESAMPLES and undefined_count == 0


def bootstrap_family_completeness(required_lengths, cases):
    require(type(required_lengths) is list and 1 <= len(required_lengths) <= 3
        and all(type(length) is int and length > 0 for length in required_lengths)
        and len(set(required_lengths)) == len(required_lengths),'Explicit unique sensitivity lengths required')
    require(type(cases) is list and len(cases) <= 3,'Bounded draw accounting required')
    seen,complete = set(),True
    for case in cases:
        require(type(case) is dict and set(case) == {'length','attempted','defined','undefined'},'Unexpected draw accounting fields')
        for key in case:integer(case[key],key,0)
        require(case['length'] not in seen and case['length'] in required_lengths,'Duplicate or unplanned sensitivity')
        seen.add(case['length'])
        require(case['defined']+case['undefined'] == case['attempted'],'Draw accounting is inconsistent')
        complete = complete and bootstrap_completeness(case['attempted'],case['undefined'])
    return {'interval_construction_permitted':complete and seen == set(required_lengths),
        'discard_undefined_draws_permitted':False,'retain_descriptive_results':True,'decisive_classification_permitted':False}


def classification_readiness(valid_interval, direction, delta, monte_carlo_instability_near_boundary):
    require(type(valid_interval) is list and len(valid_interval) == 2,'Exact interval required')
    require(type(monte_carlo_instability_near_boundary) is bool,'Instability must be an explicit diagnostic result')
    outcome = classify_interval(*valid_interval,delta,direction)
    return {'scientific_outcome':'TESTED_INCONCLUSIVE' if monte_carlo_instability_near_boundary else outcome,
        'selective_reseeding_permitted':False}


def release_decision(fixed_trigger_reached, all_primary_claims_complete, technical_termination,
                     technical_failure_policy_frozen, requested_outputs):
    """Policy-only prerequisite; registry access remains separately enforced."""
    require(all(type(flag) is bool for flag in (fixed_trigger_reached,all_primary_claims_complete,
        technical_termination,technical_failure_policy_frozen)),'Release prerequisites must be explicit Boolean facts')
    require(type(requested_outputs) is list and all(value in ('effect','interval','rank','pass_fail') for value in requested_outputs),
        'Unsupported release output')
    return {'scientific_outputs_releasable':fixed_trigger_reached and all_primary_claims_complete and not technical_termination,
        'technical_status_only_releasable':technical_termination and technical_failure_policy_frozen}


def effect_profile(candidate, definitions, outcome_description, requested_delta=None):
    """Recognize the two approved pilot targets without coercing other meanings."""
    require(type(candidate) is dict and candidate.get('schema') == 'hypothesis-exec/1','Expected a bound H_exec')
    require(candidate['claim_kind'] == 'difference'
        and candidate['estimand']['kind'] == 'conditional-minus-scope-mean/1'
        and candidate['estimand']['unit'] == 'ratio'
        and candidate['comparator'] == {'kind':'whole_scope'},'The approved pilot requires the canonical ratio contrast')
    require(requested_delta is None,'Relevant effects are assigned by the approved profile, not the generator')
    require(type(candidate['horizons']['grid_seconds']) is int and candidate['horizons']['grid_seconds'] == 900,
        'The initial profile uses the adopted 900-second grid')
    integer(candidate['horizons']['outcome_bars'],'outcome horizon',1)
    require(type(outcome_description) is dict,'Retained compiler outcome type is required')
    if candidate['outcome']['scale'] == 'binary_probability':
        require(outcome_description.get('type') == 'boolean' and outcome_description.get('unit') is None,
            'The probability profile requires an actual Boolean outcome')
        return {'profile':'binary-probability-five-percentage-points/1','delta':_rational(Fraction(1,20)),
            'unit':'ratio','basis':'research-contract/1.0 section 5.2'}
    require(candidate['outcome']['scale'] == 'quantity'
        and outcome_description.get('type') == 'real' and outcome_description.get('unit') == 'ratio'
        and candidate['horizons'] == {'grid_seconds':900,'outcome_bars':96},
        'Another relevant-effect profile is required for this quantity or horizon')
    node = candidate['outcome']['program']['expression']
    require(type(node) is dict and set(node) == {'op','left','right'} and node['op'] == 'sub',
        'The installed return profile requires an explicit simple return')
    require(node['right'] == {'op':'literal','type':'real','unit':'ratio','value':'1'},
        'Return normalization is not the installed simple-return definition')
    division = node['left']
    require(type(division) is dict and set(division) == {'op','left','right'} and division['op'] == 'div',
        'The installed return requires current close divided by the bound lagged close')
    feature = division['left']
    require(type(feature) is dict and set(feature) == {'op','ref'} and feature['op'] == 'feature','Return needs a bound price feature')
    require(division['right'] == {'op':'lag','bars':96,'arg':feature},'Return denominator must be the same close 24 hours earlier')
    require(type(definitions) is list,'Bound certified field definitions required')
    found = [definition for definition in definitions if definition.get('feature_ref') == feature['ref']]
    require(len(found) == 1,'The return feature definition is absent or duplicated')
    definition = found[0]
    require(definition.get('source_field',definition.get('field')) == 'close' and definition.get('type') == 'real',
        'Ratio units alone cannot establish a price-return estimand')
    symbol=definition.get('instrument',definition.get('symbol'))
    require(symbol in ('BTCUSDT','ETHUSDT') and feature['ref'] == symbol+'.close@binance-spot-15m-v1'
        and definition.get('unit') == 'USDT/'+symbol[:-4],
        'The return profile requires the exact certified symbol-specific raw close unit and identity')
    return {'profile':'simple-24h-return-ten-basis-points/1','delta':_rational(Fraction(1,1000)),
        'unit':'ratio','basis':'research-contract/1.0 section 5.2','price_feature_ref':feature['ref']}


def draft_plan(candidate, definitions, outcome_description, primary_count, dependence):
    require(type(dependence) is dict and set(dependence) == {'base_length','rationale','development_refs','randomness'},
        'Dependence design needs a fixed length, development basis and explicit random generator identity')
    text(dependence['rationale'],'dependence rationale')
    refs = dependence['development_refs']
    require(type(refs) is list and refs and all(type(item) is str and item for item in refs)
        and len(set(refs)) == len(refs),'Development-only diagnostic evidence must be identified')
    randomness = dependence['randomness']
    require(type(randomness) is dict and set(randomness) == {'algorithm','version','seed'},'Explicit PRNG algorithm, version and seed required')
    text(randomness['algorithm'],'PRNG algorithm')
    text(randomness['version'],'PRNG version')
    integer(randomness['seed'],'seed',0)
    profile = effect_profile(candidate,definitions,outcome_description)
    lengths = block_lengths(candidate['horizons']['outcome_bars'],dependence['base_length'])
    return {'schema':'historical-evaluation-plan-draft/1','contract':CONTRACT,'profile':PROFILE,
        'effect_criterion':{**profile,'direction':candidate['estimand']['direction']},
        'family_policy':family_budget(primary_count),'estimand':deepcopy(candidate['estimand']),
        'eligibility':{'scope':'true_only','outcome':'observed_required','unknown_condition':'retain_in_scope_exclude_from_condition',
            'label_boundary':'exclude_cross_partition','overlap':'retain_and_model'},
        'dependence_design':{**deepcopy(dependence),'method':'joint_stationary_block_bootstrap',
            'time_instruments':'joint_aligned_time_blocks','sensitivity_lengths':lengths,
            'assumptions':['stationarity','weak_dependence','adequate_conditioned_denominators']},
        'uncertainty_method':{'interval':'basic_bootstrap','resamples_per_length':MAX_RESAMPLES,
            'quantile':'linear_at_(B-1)*p','sensitivity':'enclosing_interval','undefined_draw':'information_gap_no_discard',
            'boundary_instability':'inconclusive_no_selective_reseeding'},
        'sample_precision_plan':{'n_min':None,'status':'CALIBRATED_INFORMATION_TARGET_REQUIRED',
            'planned_power':_rational(Fraction(4,5)),'alternative':_rational(2*_read_rational(profile['delta'])),
            'required_sensitivities':[_rational(Fraction(0)),profile['delta'],_rational(2*_read_rational(profile['delta']))],
            'finite_sample_shortfall':'inconclusive_with_attainable_precision'},
        'stopping_rule':{'mode':'fixed_historical','trigger':'frozen_sample_processed','interim_inference':False},
        'release_rule':{'fixed_releases':1,'technical_failure':'withhold_all_scientific_results'},
        'scientific_readiness':False,
        'remaining_gates':['independent_semantic_review','scientific_data_and_exposure_acceptance',
            'composition_conformance','calibrated_estimator_and_information_plan','atomic_allocation_and_freeze']}
