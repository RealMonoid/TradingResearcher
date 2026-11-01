"""Finite original-specific D094 composition probes and independent row audit.

The oracle is separately authored and cannot become a candidate. Synthetic
windows shorten only the declared test interval, never candidate expressions.
This certifies the retained original only; other pair hypotheses require their
own independent composition expectations.
"""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import importlib.util
from pathlib import Path
import random

from .binding import require
from .codec import canonical, digest
from .outcomes import _instant
from .paired_development import materialize_paired, paired_contrast

ORACLE='tests/paired_original_oracle.py'
ORACLE_SHA256='b18059528214cde32429d10a7f1adb50b217c79ec40dd31ae5cc49e7ee5a1e85'
IDEA_ID='94cf7b732406785e98d1c5a42daccce4c43685fbf0471f517d2a960311c8e6c3'
PROFILE='paired-original-composition/1'


def oracle_module():
    import hashlib
    path=Path(__file__).resolve().parents[1]/ORACLE
    require(hashlib.sha256(path.read_bytes()).hexdigest()==ORACLE_SHA256)
    spec=importlib.util.spec_from_file_location('independent_paired_original',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def compare_cases(cases, expected):
    require(len(cases)==len(expected),'Independent original case count differs')
    observed=0
    for actual,wanted in zip(cases,expected):
        for key in ('decision_time','scope','condition','status'):
            require(canonical(actual[key])==canonical(wanted[key]),
                'Independent original differs at '+str(wanted['decision_time'])+' / '+key)
        neutral={'missing_warmup','absent_row','missing_feature','missing_value',
                 'unavailable_data','boundary_censoring','condition_unknown'}
        require(set(actual['diagnostics']['reason_categories'])&neutral==set(wanted['reason_categories'])&neutral,
                'Independent original neutral missingness categories differ')
        if wanted['outcome'] is None:
            require(actual['outcome'] is None,'Independent missing outcome differs')
        else:
            value=actual['outcome']
            require(type(value) is dict and value.get('schema')=='bounded-real/1')
            fraction=lambda part:Fraction(int(part['numerator']),int(part['denominator']))
            lo,hi=fraction(value['lower']),fraction(value['upper'])
            require(0<=hi-lo<=Fraction(1,10**12))
            # Decimal80 is an independent cross-check, not the interval proof.
            # A declared rounding allowance is far below the adopted bound.
            center=Fraction(wanted['outcome'])
            require(lo-Fraction(1,10**65)<=center<=hi+Fraction(1,10**65),
                    'Independent original outcome is outside the enclosure')
            observed+=1
    return {'checked_cases':len(cases),'observed_outcomes':observed}


def scenarios():
    oracle=oracle_module()
    rows=oracle._synthetic(12)
    yield 'inclusive_thresholds',rows,None
    # Individually perturb every original threshold on each side.
    edits=[(0,'close','99.5999','99.6001'),(1,'close','199.1999','199.2001'),
        (0,'taker_quote_volume','39.9999','40.0001'),(1,'taker_quote_volume','39.9999','40.0001'),
        (2,'close','100.1999','100.2001'),(2,'taker_quote_volume','54.9999','55.0001'),
        (3,'close','199.9999','200.0001'),(3,'taker_quote_volume','44.9999','45.0001')]
    for index,field,below,above in edits:
        for value in (below,above):
            changed=deepcopy(rows)
            changed[index]['features'][oracle._ref(changed[index]['instrument'],field)]['value']=value
            yield 'threshold/'+str(index)+'/'+field+'/'+value,changed,None
    for index in range(4):
        for field in oracle.FIELDS:
            for kind in ('null','absent','late'):
                changed=deepcopy(rows)
                ref=oracle._ref(changed[index]['instrument'],field)
                if kind=='absent':del changed[index]['features'][ref]
                elif kind=='null':changed[index]['features'][ref]['value']=None
                else:changed[index]['features'][ref]['available_at']+=1800
                yield 'required/'+str(index)+'/'+field+'/'+kind,changed,None
    for index in (0,1,4,5,12,13):
        changed=deepcopy(rows)
        del changed[index]
        yield 'absent_member/'+str(index),changed,None
    for index in (0,1,2,3):
        for field,value in (('quote_volume','0'),('taker_quote_volume','101')):
            changed=deepcopy(rows)
            changed[index]['features'][oracle._ref(changed[index]['instrument'],field)]['value']=value
            yield 'undefined_condition/'+str(index)+'/'+field,changed,None
    for index in (4,5,12,13):
        for kind in ('null','late'):
            changed=deepcopy(rows)
            sample=changed[index]['features'][oracle._ref(changed[index]['instrument'],'close')]
            if kind=='null':sample['value']=None
            else:sample['available_at']+=3600
            yield 'outcome_endpoint/'+str(index)+'/'+kind,changed,None
    yield 'as_of_boundary',deepcopy(rows),oracle.ORIGINAL_START+6*900
    for seed in range(3):
        changed=deepcopy(rows)
        generator=random.Random(seed)
        for row in changed:
            for ref,sample in row['features'].items():
                if '.open@' in ref or '.close@' in ref:
                    sample['value']=str(generator.randrange(10000,200000)/100)
                elif '.taker_quote_volume@' in ref:sample['value']=str(generator.randrange(101))
        yield 'independent_values/'+str(seed),changed,None


def qualify(payload):
    from .paired_runtime import compile_payload
    compiled=compile_payload(payload)
    oracle=oracle_module()
    require(payload['candidate']['horizons']['outcome_bars']==5)
    results=[]
    stamp=lambda value:datetime.fromtimestamp(value,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    for name,rows,as_of in scenarios():
        start,end=oracle.ORIGINAL_START,oracle.ORIGINAL_START+12*900
        request=deepcopy(compiled['request'])
        request['universe']['start'],request['universe']['end']=stamp(start),stamp(end)
        request['as_of']=stamp(end if as_of is None else as_of)
        report=materialize_paired(request,payload['catalog'],rows,payload['feature_definitions'])
        require(report['status']=='PROCESSED','Synthetic composition did not complete')
        paired_contrast(report)
        expected=oracle.oracle(rows,start,end,end if as_of is None else as_of)
        results.append({'name':name,**compare_cases(report['cases'],expected)})
    return {'schema':'paired-composition-result/1','profile':PROFILE,'candidate_hash':digest(payload['candidate']),
        'oracle_sha256':ORACLE_SHA256,'scenarios':results,'scenario_count':len(results),
        'checked_cases':sum(item['checked_cases'] for item in results),'scientific_readiness':False}


def audit(payload,rows,cases):
    universe=payload['candidate']['test_universe']
    expected=oracle_module().oracle(rows,_instant(universe['start']),_instant(universe['end']),_instant(payload['as_of']))
    return {'schema':'paired-original-row-audit/1','oracle_sha256':ORACLE_SHA256,
        'candidate_hash':digest(payload['candidate']),**compare_cases(cases,expected),
        'scientific_readiness':False,'qualification':'Independent Decimal80 cross-check; rigorous bounds belong to the certified evaluator.'}
