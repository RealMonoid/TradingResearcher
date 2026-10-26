"""Exact development diagnostics, not a fitted world, power estimate or certificate."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib

from .codec import canonical, digest, integer
from .evaluation_policy import require
from .outcomes import reference_contrast, _read_rational, _rational


SCHEMA='binary-nuisance-diagnostics/1'


def validate_lags(lags):
    require(type(lags) is list and 1<=len(lags)<=16,'One through sixteen explicit diagnostic lags required')
    for lag in lags:
        integer(lag,'diagnostic lag',1)
        require(lag<=100000,'Diagnostic lag exceeds the grid envelope')
    require(lags==sorted(set(lags)),'Diagnostic lags must be strictly increasing')
    return list(lags)


def _groups(cases):
    groups={key:{'count':0,'successes':0,'rate':None} for key in ('scope','true','false','unknown')}
    for case in cases:
        if case['status']!='ELIGIBLE':continue
        kind='unknown' if case['condition'] is None else 'true' if case['condition'] else 'false'
        y=int(_read_rational(case['outcome']))
        for key in ('scope',kind):
            groups[key]['count']+=1
            groups[key]['successes']+=y
    for item in groups.values():
        if item['count']:item['rate']=_rational(Fraction(item['successes'],item['count']))
    n,c=groups['scope']['count'],groups['true']['count']
    groups['condition_fraction']=_rational(Fraction(c,n)) if n else None
    groups['observed_contrast']=(_rational(_read_rational(groups['true']['rate'])-
        _read_rational(groups['scope']['rate'])) if c and n else None)
    return groups


def _grid_moments(values,denominator,lags):
    """Global-mean-centered empirical products on every noncircular grid pair.

    Values share an exact integer scale. This avoids allocating Fractions for
    each product while retaining the defined divisor and missing-grid positions.
    """
    size=len(values);total=sum(values)
    result={'mean':_rational(Fraction(total,size*denominator)),
        'centering':'global_full_grid_mean','divisor':'available_grid_pairs','lags':[]}
    for lag in [0,*lags]:
        pairs=max(0,size-lag)
        value=None
        if pairs:
            left,right=values[lag:],values[:pairs]
            product=sum(a*b for a,b in zip(left,right))
            numerator=product*size*size-total*size*(sum(left)+sum(right))+pairs*total*total
            value=_rational(Fraction(numerator,pairs*size*size*denominator*denominator))
        result['lags'].append({'lag':lag,'pairs':pairs,'covariance':value})
    return result


def _paired_product(left,right,left_group,right_group,lag):
    """Pair coverage may have different marginals: do not call this correlation."""
    possible=max(0,len(left)-lag)
    paired=[(a,b) for a,b in zip(left[:possible],right[lag:]) if a is not None and b is not None]
    nl,nr=left_group['count'],right_group['count']
    sl,sr=left_group['successes'],right_group['successes']
    count=len(paired)
    result={'lag':lag,'available_grid_pairs':possible,'eligible_pairs':count,
        'centering':'global_instrument_eligible_rate','pair_order':'left_earlier_right_later','left_center':left_group['rate'],
        'right_center':right_group['rate'],'paired_left_mean':None,'paired_right_mean':None,
        'fixed_center_product':None}
    if count:
        result['paired_left_mean']=_rational(Fraction(sum(a for a,b in paired),count))
        result['paired_right_mean']=_rational(Fraction(sum(b for a,b in paired),count))
        result['fixed_center_product']=_rational(Fraction(
            sum((nl*a-sl)*(nr*b-sr) for a,b in paired),count*nl*nr))
    return result


def _runs(cases):
    histogram=Counter();previous=None;length=0
    for case in cases:
        state=case['status']
        if state=='ELIGIBLE':
            state+='_'+('unknown' if case['condition'] is None else 'true' if case['condition'] else 'false')
        if state==previous:length+=1
        else:
            if previous is not None:histogram[previous,length]+=1
            previous,length=state,1
    if previous is not None:histogram[previous,length]+=1
    return [{'state':state,'length':length,'runs':count} for (state,length),count in sorted(histogram.items())]


def diagnose(report,lags,on_contribution=None):
    """Measure complete binary development cases under fixed diagnostic choices.

    Missing outcomes remain missing in paired outcome products. Ineligible rows
    contribute zero to count/score sums but keep their full grid position.
    No lag choice or empirical moment proves stationarity or model adequacy.
    """
    lags=validate_lags(lags)
    require(on_contribution is None or callable(on_contribution),'Contribution sink must be callable')
    report=deepcopy(report)
    counts=report.get('state_counts') if type(report) is dict else None
    require(type(counts) is dict and all(type(value) is int and value>=0 for value in counts.values()),
        'State counts must be nonnegative integer metadata')
    descriptive=reference_contrast(report)
    header={key:value for key,value in report.items() if key!='cases'}
    checksum=hashlib.sha256()
    for case in report['cases']:checksum.update((canonical(case)+'\n').encode())
    result={'schema':SCHEMA,'status':'INPUT_GAP','reason':descriptive['reason'],'lags':lags,
        'case_report_hash':digest(header),'case_stream_sha256':checksum.hexdigest(),
        'time_rows':len(report['cases'])//len(report['request']['universe']['instruments']),
        'horizon_bars':report['request']['horizon_bars'],'totals':None,'grid_moments':{},
        'instrument_diagnostics':[],'cross_instrument_products':[],
        'contribution_count':0,'contributions_sha256':hashlib.sha256(b'').hexdigest(),
        'model_identification_gaps':[],'n_min':None,'scientific_readiness':False,'classification_permitted':False,
        'unverified':['stationarity','weak_dependence','missingness_assumptions','response_model_adequacy',
            'information_target','calibration','scientific_data_and_semantic_acceptance','atomic_freeze']}
    if report['request']['outcome_scale']!='binary_probability':
        result.update(status='EVALUATION_GAP',reason='binary_population_profile_required')
        return result
    if descriptive['reason'] not in ('reference_calculation_complete','no_scope_cases','no_conditioned_cases'):
        return result
    instruments=sorted(report['request']['universe']['instruments'])
    if len(instruments)>16:
        result.update(status='RESOURCE_GAP',reason='diagnostic_instrument_envelope_exceeded')
        return result
    cases=report['cases'];width=len(instruments);size=result['time_rows']
    totals=_groups(cases);result['totals']=totals
    n,s=totals['scope']['count'],totals['scope']['successes']
    c,z=totals['true']['count'],totals['true']['successes']
    gaps=result['model_identification_gaps']
    if not n:gaps.append('no_scope_cases')
    if not c:gaps.append('no_conditioned_cases')
    if n and c==n:gaps.append('all_scope_conditioned')
    if n and s in (0,n):gaps.append('degenerate_scope_rate')
    columns=[[],[],[],[]];stream=hashlib.sha256()
    for offset in range(0,len(cases),width):
        group=_groups(cases[offset:offset+width])
        row={'schema':'binary-grid-contributions/1','decision_time':cases[offset]['decision_time'],
            'scope_count':group['scope']['count'],'scope_successes':group['scope']['successes'],
            'condition_count':group['true']['count'],'condition_successes':group['true']['successes'],
            'false_count':group['false']['count'],'unknown_count':group['unknown']['count']}
        for target,key in zip(columns,('scope_count','scope_successes','condition_count','condition_successes')):
            target.append(row[key])
        stream.update((canonical(row)+'\n').encode())
        if on_contribution is not None:on_contribution(deepcopy(row))
    counts,successes,conditioned,conditional_successes=columns
    moments={'scope_count':_grid_moments(counts,1,lags),'condition_count':_grid_moments(conditioned,1,lags),
        'scope_residual':None,'condition_residual':None,'contrast_score':None}
    scope_residual=[n*y-s*a for a,y in zip(counts,successes)]
    condition_residual=[c*y-z*a for a,y in zip(conditioned,conditional_successes)]
    if n:moments['scope_residual']=_grid_moments(scope_residual,n,lags)
    if c:moments['condition_residual']=_grid_moments(condition_residual,c,lags)
    if n and c:
        score=[size*(n*n*conditional-c*c*whole) for conditional,whole in zip(condition_residual,scope_residual)]
        moments['contrast_score']=_grid_moments(score,n*n*c*c,lags)
    result['grid_moments']=moments
    outcome_series=[]
    for index,instrument in enumerate(instruments):
        rows=cases[index::width];groups=_groups(rows)
        values=[int(_read_rational(row['outcome'])) if row['status']=='ELIGIBLE' else None for row in rows]
        outcome_series.append(values)
        if not groups['scope']['count']:gaps.append('instrument:'+instrument+':no_scope_cases')
        elif groups['scope']['successes'] in (0,groups['scope']['count']):
            gaps.append('instrument:'+instrument+':degenerate_rate')
        result['instrument_diagnostics'].append({'instrument':instrument,'groups':groups,
            'state_counts':dict(sorted(Counter(row['status'] for row in rows).items())),
            'mask_runs':_runs(rows),'outcome_lag_products':[
                _paired_product(values,values,groups['scope'],groups['scope'],lag) for lag in [0,*lags]]})
    for left in range(width):
        for right in range(left+1,width):
            product=_paired_product(outcome_series[left],outcome_series[right],
                result['instrument_diagnostics'][left]['groups']['scope'],
                result['instrument_diagnostics'][right]['groups']['scope'],0)
            result['cross_instrument_products'].append({'left_instrument':instruments[left],
                'right_instrument':instruments[right],**product})
    result.update(status='COMPUTED_DIAGNOSTICS',reason='diagnostics_complete',
        contribution_count=size,contributions_sha256=stream.hexdigest())
    canonical(result)
    return result
