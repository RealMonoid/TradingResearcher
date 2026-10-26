"""Uncalibrated, explicit-budget Monte Carlo quantile/boundary diagnostics.

Binomial rank arithmetic is exact. Its probability interpretation assumes iid
replicates of the conditional bootstrap law; it is not market-data coverage.
"""
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache

from .codec import integer
from .evaluation_policy import (MAX_RESAMPLES, _rational, basic_interval,
                                classify_interval, enclosing_interval, require)
from .outcomes import _read_rational


METHOD='binomial-order-statistic-boundary/1'


def _probability(value, name):
    probability=_read_rational(value)
    require(0<probability<1 and probability.denominator<=2**32,
            name+' must be strictly between zero and one with denominator at most 2^32')
    return probability


def validate_config(config):
    require(type(config) is dict and set(config)=={'schema','noncoverage','delta','direction'},
            'Explicit Monte Carlo policy, noncoverage, delta and direction required')
    require(config['schema']=='mc-boundary-policy/1','Unsupported Monte Carlo policy')
    beta=_probability(config['noncoverage'],'Monte Carlo noncoverage')
    require(beta.denominator<=1000000,'Monte Carlo policy exceeds the rational budget envelope')
    require(_read_rational(config['delta'])>0,'Positive bound effect required')
    require(config['direction'] in ('positive','negative','nondirectional'),'Unsupported bound direction')
    return deepcopy(config)


@lru_cache(maxsize=128)
def _rank_core(n, a, d, numerator, denominator):
    # Reflect the upper quantile to avoid traversing the high-probability tail.
    if 2*a>d:
        low,high=_rank_core(n,d-a,d,numerator,denominator)
        return n+1-high,n+1-low
    total=pow(d,n); term=pow(d-a,n); cumulative=0
    threshold=total*numerator
    low,high=0,n+1
    for k in range(n+1):
        cumulative+=term
        if cumulative*denominator<=threshold:low=k+1
        if (total-cumulative)*denominator<=threshold:
            high=k+1
            break
        if k<n:
            term=term*(n-k)*a//((k+1)*(d-a))
    return low,high


def rank_bounds(n, probability, tail_noncoverage):
    """One-based order ranks; 0 and n+1 mean unbounded, never sample extrema.

Choose largest k with P[Bin(n,p)<k]<=tail and smallest l with
P[Bin(n,p)>=l]<=tail. Inclusive quantile bands remain conservative at atoms.
"""
    integer(n,'replicate count',1)
    require(n<=MAX_RESAMPLES,'Replicate count exceeds the fixed candidate envelope')
    p=_probability(probability,'Quantile probability')
    tail=_probability(tail_noncoverage,'Tail noncoverage')
    require(tail<Fraction(1,2),'Tail noncoverage must be less than one half')
    return list(_rank_core(n,p.numerator,p.denominator,tail.numerator,tail.denominator))


def quantile_band(values, probability, tail_noncoverage):
    require(type(values) is list and 1<=len(values)<=MAX_RESAMPLES,'Bounded defined draw list required')
    ordered=sorted(_read_rational(value) for value in values)
    low,high=rank_bounds(len(values),probability,tail_noncoverage)
    return {'ranks':[low,high],'lower':None if low==0 else _rational(ordered[low-1]),
            'upper':None if high==len(values)+1 else _rational(ordered[high-1])}


def unassessed(config, reason):
    return {'schema':'mc-boundary-diagnostic/1','method':METHOD,'config':validate_config(config),
            'status':'NOT_ASSESSED','reason':reason,'boundary_stable':None,
            'scientific_readiness':False,'classification_permitted':False,
            'selective_reseeding_permitted':False}


def _stable(bounds, delta, direction):
    # None is an unbounded end. Decline stability conservatively in this candidate.
    if any(value is None for pair in bounds.values() for value in pair):return False
    ll,lu=map(_read_rational,bounds['lower']); ul,uu=map(_read_rational,bounds['upper'])
    if direction=='negative':ll,lu,ul,uu=-uu,-ul,-lu,-ll
    if direction!='nondirectional':
        return ll>delta or uu<delta or (lu<=delta and ul>=delta)
    support=ll>delta or uu<-delta
    negative=ll>=-delta and uu<=delta
    inconclusive=lu<=delta and ul>=-delta and (lu<-delta or ul>delta)
    return support or negative or inconclusive


def diagnose(estimate, replicates_by_length, marginal_noncoverage, config):
    """Assess a fixed complete sensitivity set; never acquire or replace draws."""
    config=validate_config(config)
    point=_read_rational(estimate); alpha=_probability(marginal_noncoverage,'Marginal noncoverage')
    require(type(replicates_by_length) is dict and 1<=len(replicates_by_length)<=3
            and all(type(k) is int and k>0 for k in replicates_by_length),'Explicit sensitivity draw lists required')
    require(all(type(v) is list and len(v)<=MAX_RESAMPLES for v in replicates_by_length.values()),
            'Invalid sensitivity draw envelope')
    if any(len(v)!=MAX_RESAMPLES or any(x is None for x in v) for v in replicates_by_length.values()):
        return unassessed(config,'incomplete_or_undefined_draws')
    tail=_read_rational(config['noncoverage'])/(4*len(replicates_by_length))
    cases=[]
    def reflected(value):return None if value is None else _rational(2*point-_read_rational(value))
    for length,values in sorted(replicates_by_length.items()):
        low=quantile_band(values,_rational(alpha/2),_rational(tail))
        high=quantile_band(values,_rational(1-alpha/2),_rational(tail))
        interval=basic_interval(estimate,values,marginal_noncoverage)
        bounds={'lower':[reflected(high['upper']),reflected(high['lower'])],
                'upper':[reflected(low['upper']),reflected(low['lower'])]}
        # Include the observed type-7 endpoints even in an extreme MC realization.
        for endpoint in ('lower','upper'):
            actual=_read_rational(interval[endpoint])
            if bounds[endpoint][0] is not None:
                bounds[endpoint][0]=_rational(min(_read_rational(bounds[endpoint][0]),actual))
            if bounds[endpoint][1] is not None:
                bounds[endpoint][1]=_rational(max(_read_rational(bounds[endpoint][1]),actual))
        cases.append({'length':length,'quantiles':{'lower':low,'upper':high},'interval':interval,'endpoint_bounds':bounds})
    combined={}
    for endpoint,operation in (('lower',min),('upper',max)):
        combined[endpoint]=[]
        for side in (0,1):
            values=[case['endpoint_bounds'][endpoint][side] for case in cases]
            # For a min lower endpoint only -inf dominates; for max only +inf.
            unbounded_dominates=(endpoint=='lower' and side==0) or (endpoint=='upper' and side==1)
            finite=[_read_rational(value) for value in values if value is not None]
            combined[endpoint].append(None if not finite or (unbounded_dominates and len(finite)!=len(values))
                                      else _rational(operation(finite)))
    interval=enclosing_interval([case['interval'] for case in cases])
    stable=_stable(combined,_read_rational(config['delta']),config['direction'])
    return {'schema':'mc-boundary-diagnostic/1','method':METHOD,'config':config,
            'status':'ASSESSED_UNCALIBRATED','reason':'classification_invariant' if stable else 'boundary_instability_or_unbounded_rank',
            'boundary_stable':stable,'nominal_classification':classify_interval(interval['lower'],interval['upper'],
                config['delta'],config['direction']),
            'tail_noncoverage':_rational(tail),'allocation':'per_claim_union_bound_over_two_quantiles_two_sides_all_lengths',
            'replicates_per_length':MAX_RESAMPLES,'cases':cases,'interval':interval,'endpoint_bounds':combined,
            'probability_scope':'conditional_bootstrap_law_under_iid_replicates_not_market_or_family_coverage',
            'scientific_readiness':False,'classification_permitted':False,'selective_reseeding_permitted':False}
