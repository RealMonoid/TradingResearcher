"""Fixed development-study inventory, exact uncertainty and conservative accounting."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
import math
import re

from .codec import canonical, digest, integer, text
from .evaluation_policy import block_lengths, family_budget, require
from .monte_carlo import validate_config
from .outcomes import _rational, _read_rational
from .population_models import validate_specification
from .stationary_bootstrap import randomness


MANIFEST='development-information-study-manifest/1'
FINAL_MANIFEST='final-evaluator-calibration-manifest/1'
DECISIONS={'SUPPORTED_INITIAL','TESTED_NEGATIVE','TESTED_INCONCLUSIVE'}
STATES={'VERIFIED','INFORMATION_GAP','MODEL_GAP','TECHNICAL_FAILURE'}


def make_manifest(assigned,profile,*,purpose='development'):
    require(purpose in ('development','final_calibration'),'Unknown study purpose')
    require(type(assigned) is dict and set(assigned)=={'input_binding','base_length','primary_count','delta',
        'direction','horizon_bars','available_time_rows','instruments'},'Exact assigned study inputs required')
    require(type(assigned['input_binding']) is str and re.fullmatch('[0-9a-f]{64}',assigned['input_binding']),
        'Exact input binding digest required')
    for name in ('horizon_bars','available_time_rows','instruments'):integer(assigned[name],name,1)
    require(assigned['instruments']<=16 and assigned['available_time_rows']*assigned['instruments']<=100000,
        'Study source exceeds the implemented case envelope')
    lengths=block_lengths(assigned['horizon_bars'],assigned['base_length'])
    family=family_budget(assigned['primary_count'])
    delta=_read_rational(assigned['delta']);direction=assigned['direction']
    require(delta==Fraction(1,20) and direction in ('positive','negative','nondirectional'),
        'Study requires the assigned binary pilot effect profile')
    fields={'specifications','targets','worlds_per_cell','seed','mc_noncoverage','outer_noncoverage','budget','cost_estimate'}
    require(type(profile) is dict and set(profile)==fields,'Exact finite study profile required')
    specs=profile['specifications']
    require(type(specs) is list and 1<=len(specs)<=4,'One through four explicit stress specifications required')
    for spec in specs:validate_specification(spec)
    require(len({digest(spec) for spec in specs})==len(specs),'Duplicate stress specifications')
    targets=profile['targets']
    require(type(targets) is list and 1<=len(targets)<=8,'One through eight fixed grid targets required')
    for target in targets:
        integer(target,'target',1)
        require(assigned['horizon_bars']<target<=assigned['available_time_rows'],
            'Target exceeds the available historical grid or has no nonterminal positions')
    require(targets==sorted(set(targets)),'Targets must be strictly increasing')
    repetitions=integer(profile['worlds_per_cell'],'worlds per cell',1)
    require(repetitions<=256,'Development repetitions exceed the fixed envelope')
    if purpose=='final_calibration':
        require(repetitions==256 and len(targets)==1 and assigned['primary_count']==1,
            'Final calibration requires 256 worlds at one fixed target; coherent multi-claim worlds are not implemented')
    randomness(profile['seed'])
    mc=validate_config({'schema':'mc-boundary-policy/1','noncoverage':profile['mc_noncoverage'],
        'delta':assigned['delta'],'direction':direction})
    alpha=_read_rational(profile['outer_noncoverage'])
    require(0<alpha<1 and alpha.denominator<=1000000,'Bounded explicit outer noncoverage required')
    budget=profile['budget']
    require(type(budget) is dict and set(budget)=={'max_compute_ms','attempt_compute_ms','max_storage_bytes',
        'attempt_storage_bytes','max_attempts'},'Exact aggregate and attempt budgets required')
    for key in budget:integer(budget[key],key,1)
    require(budget['attempt_compute_ms']<=min(1800000,budget['max_compute_ms'])
        and budget['max_compute_ms']<=3600000,'Study computation budget exceeds its envelope')
    require(budget['attempt_storage_bytes']<=min(1024**3,budget['max_storage_bytes'])
        and budget['max_storage_bytes']<=4*1024**3 and budget['max_attempts']<=3,
        'Study storage/retry budget exceeds its envelope')
    estimate=profile['cost_estimate']
    require(type(estimate) is dict and set(estimate)=={'source_ref','world_time_rows','observed_compute_ms',
        'observed_storage_bytes','qualification'},'Explicit qualified cost estimate required')
    for key in ('source_ref','qualification'):text(estimate[key],key)
    for key in ('world_time_rows','observed_compute_ms','observed_storage_bytes'):integer(estimate[key],key,1)
    effects=([0,delta,2*delta,-delta,-2*delta] if direction=='nondirectional' else
        [0,delta,2*delta] if direction=='positive' else [0,-delta,-2*delta])
    require(len(specs)*len(targets)*len(effects)*repetitions<=2048,'Study world inventory exceeds its envelope')
    recipe={'schema':MANIFEST,'assigned':deepcopy(assigned),'profile':deepcopy(profile),
        'effects':[_rational(value) for value in effects],'required_lengths':lengths,'family':family,'mc_policy':mc,
        'outer_method':'clopper-pearson-dyadic-outward/1','outer_bits':40,
        'selection':'smallest_tested_complete_grid_point_power_at_least_4/5_all_specs_and_signs_at_2delta',
        'seed_namespace':'development-information-study-only/1','scientific_readiness':False,'n_min':None}
    if purpose=='final_calibration':
        recipe.update(schema=FINAL_MANIFEST,selection='fixed_final_target_no_selection',
            seed_namespace='reserved-final-evaluator-calibration/1')
    recipe_hash=digest(recipe);worlds=[];seeds=set()
    for target in targets:
        for spec_index in range(len(specs)):
            for scenario,effect in enumerate(effects):
                for replicate in range(repetitions):
                    identity={'recipe_hash':recipe_hash,'time_rows':target,'spec_index':spec_index,
                        'scenario':scenario,'replicate':replicate}
                    rngs={key:int(digest({'namespace':recipe['seed_namespace'],'world':identity,'stream':key}),16)
                        for key in ('population_seed','bootstrap_seed')}
                    require(not seeds.intersection(rngs.values()) and len(set(rngs.values()))==2,'Study seed collision')
                    seeds.update(rngs.values())
                    worlds.append({'id':digest(identity),**{k:v for k,v in identity.items() if k!='recipe_hash'},
                        'effect':_rational(effect),**rngs})
    result={**recipe,'recipe_hash':recipe_hash,'worlds':worlds}
    canonical(result)
    return result


def _validate_manifest(manifest):
    if type(manifest) is dict and manifest.get('schema') in ('family-information-study-manifest/1','family-evaluator-calibration-manifest/1'):
        from .family_study import validate_manifest
        return validate_manifest(manifest)
    require(type(manifest) is dict and manifest.get('schema') in (MANIFEST,FINAL_MANIFEST),'Owned study manifest required')
    expected=make_manifest(manifest.get('assigned'),manifest.get('profile'),
        purpose='final_calibration' if manifest['schema']==FINAL_MANIFEST else 'development')
    require(digest(expected)==digest(manifest),'Study inventory differs from its fixed recipe')


def _tail_compare(k,n,p,alpha,survival):
    a,b=p.numerator,p.denominator
    terms=range(k,n+1) if survival else range(k+1)
    total=sum(math.comb(n,j)*a**j*(b-a)**(n-j) for j in terms)
    return total*alpha.denominator-alpha.numerator*b**n


@lru_cache(maxsize=1024)
def _outer_core(k,n,alpha,bits):
    grid=1<<bits;tail=alpha/2
    def root(survival):
        if survival and k==0:return [Fraction(0),Fraction(0)]
        if not survival and k==n:return [Fraction(1),Fraction(1)]
        lo,hi=0,grid
        while hi-lo>1:
            mid=(lo+hi)//2;sign=_tail_compare(k,n,Fraction(mid,grid),tail,survival)
            if sign==0:lo=hi=mid
            elif (sign<0 if survival else sign>0):lo=mid
            else:hi=mid
        return [Fraction(lo,grid),Fraction(hi,grid)]
    lower,upper=root(True),root(False)
    return {'method':'clopper-pearson-dyadic-outward/1','noncoverage':_rational(alpha),'bits':bits,
        'point':_rational(Fraction(k,n)),'lower':_rational(lower[0]),'upper':_rational(upper[1]),
        'lower_root_bracket':list(map(_rational,lower)),'upper_root_bracket':list(map(_rational,upper)),
        'maximum_bracket_width':_rational(Fraction(1,grid)),
        'pointwise_only':True,'assumption':'fixed_independent_outer_worlds_under_declared_simulation_law'}


def outer_interval(k,n,noncoverage,bits=40):
    integer(n,'outer trials',1);integer(k,'outer successes',0);integer(bits,'outer bracket bits',1)
    require(k<=n<=256 and 8<=bits<=64,'Outer interval count/precision envelope exceeded')
    alpha=_read_rational(noncoverage)
    require(0<alpha<1 and alpha.denominator<=1000000,'Explicit outer noncoverage required')
    return deepcopy(_outer_core(k,n,alpha,bits))


def summarize(manifest,records):
    if type(manifest) is dict and manifest.get('schema') in ('family-information-study-manifest/1','family-evaluator-calibration-manifest/1'):
        from .family_study import summarize as family_summary
        return family_summary(manifest,records)
    _validate_manifest(manifest)
    require(type(records) is list,'Study results must be a list')
    worlds={world['id']:world for world in manifest['worlds']};seen={}
    for record in records:
        require(type(record) is dict and set(record)=={'world_id','state','decision','scope_count','condition_count','covered'},
            'Exact study outcome record required')
        text(record['world_id'],'world id')
        require(record['world_id'] in worlds and record['world_id'] not in seen,'Unplanned or duplicate study result')
        require(type(record['state']) is str and record['state'] in STATES,'Unknown study result state')
        require(record['decision'] is None or type(record['decision']) is str and record['decision'] in DECISIONS,
            'Unsupported simulated decision')
        require(record['covered'] is None or type(record['covered']) is bool,'Exact coverage observation required')
        if record['state']=='VERIFIED':
            require(record['decision'] in DECISIONS and type(record['covered']) is bool,'Verified outcome needs decision and coverage')
        else:require(record['decision'] is None and record['covered'] is None,'Gaps and failures cannot invent outcomes')
        for key in ('scope_count','condition_count'):
            require(record[key] is None or type(record[key]) is int and record[key]>=0,'Exact world counts required')
        if record['scope_count'] is not None and record['condition_count'] is not None:
            require(record['condition_count']<=record['scope_count'],'Condition exceeds scope')
        if record['state']=='VERIFIED':
            ceiling=(worlds[record['world_id']]['time_rows']-manifest['assigned']['horizon_bars'])*manifest['assigned']['instruments']
            require(type(record['scope_count']) is int and type(record['condition_count']) is int
                and 1<=record['condition_count']<=record['scope_count']<=ceiling,
                'Verified result needs positive counts within the nonterminal world')
        seen[record['world_id']]=record
    cells=[]
    for target in manifest['profile']['targets']:
        for spec_index in range(len(manifest['profile']['specifications'])):
            for scenario,effect in enumerate(manifest['effects']):
                planned=[world for world in worlds.values() if (world['time_rows'],world['spec_index'],world['scenario'])==(target,spec_index,scenario)]
                values=[seen[world['id']] for world in planned if world['id'] in seen]
                counts=Counter(value['state'] for value in values)
                complete=len(values)==len(planned) and not (counts['MODEL_GAP'] or counts['TECHNICAL_FAILURE'])
                detections=sum(value['decision']=='SUPPORTED_INITIAL' for value in values)
                negatives=sum(value['decision']=='TESTED_NEGATIVE' for value in values)
                cell={'time_rows':target,'spec_index':spec_index,'scenario':scenario,'effect':effect,'planned':len(planned),
                    'recorded':len(values),'states':{key:counts[key] for key in sorted(STATES)},'complete':complete,
                    'detections':detections,'negatives':negatives,'coverage_count':sum(value['covered'] is True for value in values),
                    'interval_undefined':sum(value['covered'] is None for value in values),'power':None,'detection_rate':None,
                    'scope_counts':[value['scope_count'] for value in values],
                    'condition_counts':[value['condition_count'] for value in values]}
                if complete:
                    cell['detection_rate']=outer_interval(detections,len(planned),manifest['profile']['outer_noncoverage'])
                    if abs(_read_rational(effect))==2*_read_rational(manifest['assigned']['delta']):
                        cell['power']=deepcopy(cell['detection_rate'])
                cells.append(cell)
    complete=all(cell['complete'] for cell in cells)
    candidate=None;delta=_read_rational(manifest['assigned']['delta'])
    if complete and manifest['schema']==MANIFEST:
        for target in manifest['profile']['targets']:
            alternatives=[cell for cell in cells if cell['time_rows']==target and abs(_read_rational(cell['effect']))==2*delta]
            if alternatives and all(5*cell['detections']>=4*cell['planned'] for cell in alternatives):
                candidate=target;break
    return {'schema':'development-information-study-summary/1','complete':complete,
        'planned_worlds':len(worlds),'recorded_worlds':len(records),'cells':cells,'candidate_time_rows':candidate,
        'candidate_qualification':'smallest_tested_point_power_candidate_not_simultaneous_or_selected_target_proof',
        'n_min':None,'scientific_readiness':False,'classification_permitted':False}


def budget_state(manifest,reservations,settlements):
    """Replay conservative logical-byte/compute charges; unresolved use stays charged."""
    _validate_manifest(manifest)
    require(type(reservations) is list and type(settlements) is list,'Explicit reservation history required')
    budget=manifest['profile']['budget'];world_ids={item['id'] for item in manifest['worlds']}
    reserved={};closed={};counts=Counter()
    for item in reservations:
        require(type(item) is dict and set(item)=={'attempt_id','world_id','compute_ms','storage_bytes'},'Exact reservation required')
        text(item['attempt_id'],'attempt id')
        text(item['world_id'],'world id')
        require(item['attempt_id'] not in reserved and item['world_id'] in world_ids,'Duplicate or unplanned reservation')
        require(type(item['compute_ms']) is int and item['compute_ms']==budget['attempt_compute_ms']
            and type(item['storage_bytes']) is int and item['storage_bytes']==budget['attempt_storage_bytes'],
            'Reservation must use its frozen full attempt envelope')
        counts[item['world_id']]+=1
        require(counts[item['world_id']]<=budget['max_attempts'],'World attempts exceed the frozen cap')
        reserved[item['attempt_id']]=item
    for item in settlements:
        require(type(item) is dict and set(item)=={'attempt_id','compute_ms','storage_bytes','usage_known'},'Exact settlement required')
        text(item['attempt_id'],'attempt id')
        require(item['attempt_id'] in reserved and item['attempt_id'] not in closed,'Unreserved or duplicate settlement')
        integer(item['compute_ms'],'observed compute',0);integer(item['storage_bytes'],'observed storage',0)
        require(type(item['usage_known']) is bool,'Usage certainty must be explicit')
        closed[item['attempt_id']]=item
    compute=storage=0;overrun=False
    for identity,reservation in reserved.items():
        settled=closed.get(identity)
        if settled is None:charged=reservation
        elif settled['usage_known']:charged=settled
        else:charged={key:max(reservation[key],settled[key]) for key in ('compute_ms','storage_bytes')}
        compute+=charged['compute_ms'];storage+=charged['storage_bytes']
        if settled and (settled['compute_ms']>reservation['compute_ms'] or settled['storage_bytes']>reservation['storage_bytes']):overrun=True
    outstanding=[identity for identity in reserved if identity not in closed]
    overrun=overrun or compute>budget['max_compute_ms'] or storage>budget['max_storage_bytes']
    return {'charged_compute_ms':compute,'charged_storage_bytes':storage,'outstanding_attempts':outstanding,
        'attempts_per_world':dict(counts),'overrun':overrun,
        'next_reservation_fits':not outstanding and not overrun
            and compute+budget['attempt_compute_ms']<=budget['max_compute_ms']
            and storage+budget['attempt_storage_bytes']<=budget['max_storage_bytes']}
