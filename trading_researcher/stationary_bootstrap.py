"""Joint stationary resampling candidate; conformance is not calibration or admission."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import math
import platform
import random
import struct
import time

from .codec import Invalid, canonical, digest, integer
from .evaluation_policy import (MAX_RESAMPLES, basic_interval, block_lengths,
                                enclosing_interval, family_budget, require)
from .outcomes import reference_contrast, _read_rational, _rational
from .monte_carlo import diagnose, unassessed, validate_config


ALGORITHM = 'python-random-mt19937'
VERSION = platform.python_implementation()+'/'+platform.python_version()+'/state-'+str(random.Random.VERSION)
SAMPLER = 'joint-stationary-segments/1'
NUMERICS = {
    'statistics': 'exact_rational_8192_bit_envelope',
    'quantile': 'linear_at_(B-1)*p',
    'uniform': 'Python Random.random 53-bit binary float',
    'geometric': 'floor(log1p(-U)/log1p(-1/L))+1; L=1 gives one',
    'geometric_law': 'finite_uniform_and_libm_approximation_not_exact_probability_arithmetic',
    'mean_block_length': 'L; not a lower bound on realized lengths',
    'numeric_tolerance': 'zero for rational statistics; no probability-law accuracy certificate',
    'time_axis': 'full_aligned_grid_including_zero_contribution_timestamps',
    'seed_derivation': 'SHA256(canonical({sampler,seed,length})), big-endian integer',
    'boundary_instability': 'not_assessed_no_classification',
}


def randomness(seed):
    integer(seed,'seed',0)
    require(seed.bit_length()<=256,'Seed exceeds the declared 256-bit envelope')
    return {'algorithm':ALGORITHM,'version':VERSION,'seed':seed}


def _configuration(design,limits,horizon):
    fields={'base_length','primary_count','randomness'}
    require(type(design) is dict and set(design) in (fields,fields|{'mc_policy'}),
            'Exact bootstrap design required')
    if 'mc_policy' in design:validate_config(design['mc_policy'])
    configured=design['randomness']
    require(type(configured) is dict and set(configured)=={'algorithm','version','seed'},'Explicit randomness identity required')
    require(configured==randomness(configured['seed']),'Unsupported PRNG or runtime version; no substitution')
    lengths=block_lengths(horizon,design['base_length'])
    alpha=family_budget(design['primary_count'])['marginal_noncoverage']
    require(type(limits) is dict and set(limits)=={'max_seconds','max_segments'},'Explicit computation limits required')
    integer(limits['max_seconds'],'max seconds',1)
    integer(limits['max_segments'],'max segments',1)
    require(limits['max_seconds']<=1800 and limits['max_segments']<=100000000,
            'Resource limits exceed the installed computation envelope')
    return lengths,alpha


def _numerics(design):
    result=deepcopy(NUMERICS)
    if 'mc_policy' in design:result['boundary_instability']='explicit_uncalibrated_mc_diagnostic'
    return result


def _bounded(value):
    # Integer sufficient statistics need no Fraction allocation. Python integers
    # remain exact and retain the same bit envelope, including negative values.
    if type(value) is int:
        if value.bit_length()>8192:
            raise ArithmeticError('exact_arithmetic_exceeds_numeric_envelope')
        return value
    value=Fraction(value)
    if max(value.numerator.bit_length(),value.denominator.bit_length())>8192:
        raise ArithmeticError('exact_arithmetic_exceeds_numeric_envelope')
    return value


def _segments(size,length,rng):
    """Circular stationary blocks with geometric MEAN length; final block truncated."""
    remaining=size
    logarithm=None if length==1 else math.log1p(-1.0/length)
    while remaining:
        start=rng.randrange(size)
        count=1 if length==1 else math.floor(math.log1p(-rng.random())/logarithm)+1
        count=min(count,remaining)
        yield start,count
        remaining-=count


def _segment_sum(prefix,start,count):
    size=len(prefix)-1
    end=start+count
    return prefix[end]-prefix[start] if end<=size else prefix[size]-prefix[start]+prefix[end-size]


def _prefixes(report,check_stop=None):
    instruments=len(report['request']['universe']['instruments'])
    prefixes=[[0],[0],[0],[0]]
    for index in range(0,len(report['cases']),instruments):
        if check_stop is not None and index%512==0:
            reason=check_stop()
            if reason:raise ArithmeticError(reason)
        n,total,nc,conditional=0,0,0,0
        for case in report['cases'][index:index+instruments]:
            if case['status']!='ELIGIBLE':continue
            value=_read_rational(case['outcome'])
            if value.denominator==1:value=value.numerator
            n+=1; total=_bounded(total+value)
            if case['condition'] is True:
                nc+=1; conditional=_bounded(conditional+value)
        # A time bucket with no eligible row still occupies its original grid slot.
        for field,value in zip(prefixes,(n,total,nc,conditional)):
            field.append(field[-1]+value)
        _bounded(prefixes[1][-1]); _bounded(prefixes[3][-1])
    return prefixes


def calculate(report,design,limits,stop=None,on_draw=None,*,on_draw_bytes=None):
    """Compute every prescribed draw or retain a resource/input gap, never a verdict.

    on_draw receives each completed draw in order, including undefined values.
    on_draw_bytes receives that same canonical UTF-8 JSON without a newline;
    its immutable bytes are reused from the draw hash. Both sinks are optional.
    Its canonical JSON plus newline is the exact retained draw-stream format.
    No callback failure is swallowed or represented as completed computation.
    """
    started=time.monotonic()
    report,design,limits=deepcopy(report),deepcopy(design),deepcopy(limits)
    require(type(report) is dict and type(report.get('request')) is dict,'Reference case report required')
    lengths,alpha=_configuration(design,limits,report['request'].get('horizon_bars'))
    require(stop is None or callable(stop),'Stop predicate must be callable')
    require(on_draw is None or callable(on_draw),'Draw sink must be callable')
    require(on_draw_bytes is None or callable(on_draw_bytes),'Byte draw sink must be callable')
    counts=report.get('state_counts')
    require(type(counts) is dict and all(type(value) is int and value>=0 for value in counts.values()),
            'State counts must be nonnegative integer metadata')
    used_segments=0
    def interrupted(need_segment=False):
        if stop is not None and stop():return 'caller_cancelled'
        if time.monotonic()-started>=limits['max_seconds']:return 'computation_time_limit'
        if need_segment and used_segments>=limits['max_segments']:return 'computation_segment_limit'
        return None
    descriptive=reference_contrast(report)
    source_hash=hashlib.sha256()
    for case in report['cases']:source_hash.update((canonical(case)+'\n').encode())
    header={k:v for k,v in report.items() if k!='cases'}
    result={'schema':'joint-bootstrap-computation/2' if 'mc_policy' in design else 'joint-bootstrap-computation/1',
        'sampler':SAMPLER,'design':design,'limits':limits,
        'numerics':_numerics(design),'case_report_hash':digest(header),'case_stream_sha256':source_hash.hexdigest(),
        'required_lengths':lengths,'marginal_noncoverage':alpha,'descriptive':descriptive,
        'time_rows':len(report['cases'])//len(report['request']['universe']['instruments']),
        'cases':[],'interval':None,'status':'INPUT_GAP','reason':descriptive['reason'],
        'scientific_readiness':False,'classification_permitted':False,
        'remaining_gates':['calibration','assumption_and_information_assessment','monte_carlo_boundary_stability',
                           'owned_scientific_inputs','atomic_allocation_and_freeze']}
    if 'mc_policy' in design:
        result['monte_carlo']=unassessed(design['mc_policy'],'bootstrap_not_complete_and_defined')
    if descriptive['status']!='DESCRIPTIVE_ONLY':return result
    reason=interrupted()
    if reason:
        result.update(status='RESOURCE_STOP',reason=reason)
        return result
    try:prefixes=_prefixes(report,interrupted)
    except ArithmeticError as exc:
        result.update(status='RESOURCE_STOP',reason=str(exc))
        return result
    size=result['time_rows']
    mc_values={}
    for length in lengths:
        seed=int(hashlib.sha256(canonical({'sampler':SAMPLER,'seed':design['randomness']['seed'],
                                          'length':length}).encode()).hexdigest(),16)
        rng=random.Random(seed)
        current={'length':length,'derived_seed':str(seed),'attempted':0,'defined':0,'undefined':0,'interrupted':0,
                 'interval':None,'replicate_sha256':None,'interrupted_draw':None}
        result['cases'].append(current)
        values=[]; stream_hash=hashlib.sha256()
        reason=None
        for draw in range(MAX_RESAMPLES):
            reason=interrupted(need_segment=True)
            if reason:break
            current['attempted']+=1
            n,total,nc,conditional=0,0,0,0
            path_hash=hashlib.sha256(); segments=sampled=0
            for start,count in _segments(size,length,rng):
                reason=interrupted(need_segment=True)
                if reason:break
                used_segments+=1; segments+=1; sampled+=count
                path_hash.update(struct.pack('>II',start,count))
                try:
                    n+=_segment_sum(prefixes[0],start,count)
                    total=_bounded(total+_segment_sum(prefixes[1],start,count))
                    nc+=_segment_sum(prefixes[2],start,count)
                    conditional=_bounded(conditional+_segment_sum(prefixes[3],start,count))
                except ArithmeticError as exc:
                    reason=str(exc); break
            value=None
            if reason is None and n and nc:
                try:value=_rational(_bounded(_bounded(Fraction(conditional,nc))-_bounded(Fraction(total,n))))
                except ArithmeticError as exc:reason=str(exc)
            if reason is not None:
                current['interrupted']=1
                current['interrupted_draw']={'index':draw,'sampled_times':sampled,'segments':segments,
                                             'path_sha256':path_hash.hexdigest()}
                break
            assert sampled==size
            record={'schema':'joint-bootstrap-draw/1','length':length,'index':draw,'value':value,
                    'scope_count':n,'condition_count':nc,'segments':segments,'path_sha256':path_hash.hexdigest()}
            encoded=canonical(record).encode()
            stream_hash.update(encoded+b'\n')
            if on_draw is not None:on_draw(deepcopy(record))
            if on_draw_bytes is not None:on_draw_bytes(encoded)
            current['defined' if value is not None else 'undefined']+=1
            if value is not None:values.append(value)
            reason=interrupted()
            if reason:break
        current['replicate_sha256']=stream_hash.hexdigest()
        if reason is not None:
            result.update(status='RESOURCE_STOP',reason=reason)
            return result
        if current['undefined']==0:
            try:current['interval']=basic_interval(descriptive['effect'],values,alpha)
            except (ArithmeticError,Invalid) as exc:
                result.update(status='RESOURCE_STOP',reason='interval_numeric_envelope')
                return result
            if 'mc_policy' in design:mc_values[length]=values
        reason=interrupted()
        if reason:
            current['interval']=None
            result.update(status='RESOURCE_STOP',reason=reason)
            return result
    result['interval']=enclosing_interval([item['interval'] for item in result['cases']])
    if result['interval'] is not None and 'mc_policy' in design:
        try:result['monte_carlo']=diagnose(descriptive['effect'],mc_values,alpha,design['mc_policy'])
        except (ArithmeticError,Invalid):
            result.update(interval=None,status='RESOURCE_STOP',reason='monte_carlo_numeric_envelope')
            return result
    reason=interrupted()
    if reason:
        result.update(interval=None,status='RESOURCE_STOP',reason=reason)
        if 'mc_policy' in design:
            result['monte_carlo']=unassessed(design['mc_policy'],'bootstrap_not_complete_and_defined')
        return result
    result.update(status='COMPUTED_UNCALIBRATED' if result['interval'] is not None else 'INFORMATION_GAP',
                  reason='prespecified_draws_completed' if result['interval'] is not None else 'undefined_resampled_mean')
    return result
