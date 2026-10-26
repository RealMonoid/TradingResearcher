"""Declared lag-linked binary stress worlds, not a fitted raw-market process."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import math
import random

from .codec import canonical, digest, integer, text
from .evaluation_policy import require
from .information_diagnostics import diagnose
from .outcomes import _rational, _read_rational, reference_contrast, STATES
from .source_process_scope import diagnose_source_process
from .stationary_bootstrap import randomness


SPEC='lag-linked-binary-spec/1'
MODEL='lag-linked-binary-model/1'
WORLD='lag-linked-binary-world/1'
FAMILY='lag-linked-binary-family-world/1'


def _exact(value):
    require(type(value) in (int,F),'Exact integer or Fraction required')
    value=F(value)
    require(max(value.numerator.bit_length(),value.denominator.bit_length())<=4096,
            'Exact stationary arithmetic exceeds its resource envelope')
    return value


def specification(mask_mean_block,common_share,rationale):
    return validate_specification({'schema':SPEC,'mask_mean_block':mask_mean_block,
        'common_share':_rational(_exact(common_share)),'rationale':rationale})


def validate_specification(spec):
    require(type(spec) is dict and set(spec)=={'schema','mask_mean_block','common_share','rationale'}
            and spec['schema']==SPEC,'Exact lag-linked specification required')
    integer(spec['mask_mean_block'],'mask mean block',1)
    require(spec['mask_mean_block']<=1000000,'Mask length exceeds the simulation envelope')
    share=_read_rational(spec['common_share'])
    require(0<=share<=1 and share.denominator<=1000000,'Bounded exact common innovation share required')
    text(spec['rationale'],'stress rationale')
    return deepcopy(spec)


def stationary_joint(transitions,common_share):
    """Exact joint law for fresh common/individual uniform threshold innovations.

    State bit i belongs to coordinate i. Integrate over common-U intervals,
    then solve pi P=pi with sum(pi)=1. A positive probability of a simultaneous
    all-zero reset under strict interior transitions ensures a unique stationary
    law even when share=1 makes some joint states transient.
    """
    require(type(transitions) is list and 1<=len(transitions)<=4,
            'Joint stationary solver supports one through four coordinates')
    share=_exact(common_share)
    require(0<=share<=1,'Common innovation share outside [0,1]')
    rates=[]
    for pair in transitions:
        require(type(pair) in (tuple,list) and len(pair)==2,'Two exact conditional probabilities required')
        row=[_exact(value) for value in pair]
        require(all(0<value<1 for value in row),'Strict-interior transition capability required')
        rates.append(row)
    width=len(rates);size=1<<width;matrix=[]
    for prior in range(size):
        thresholds=[rates[i][(prior>>i)&1] for i in range(width)]
        edges=sorted({F(0),F(1),*thresholds});row=[F(0)]*size
        for left,right in zip(edges,edges[1:]):
            probabilities=[share*int(left<p)+(1-share)*p for p in thresholds]
            for target in range(size):
                value=right-left
                for i,p in enumerate(probabilities):value*=p if (target>>i)&1 else 1-p
                row[target]=_exact(row[target]+value)
        require(sum(row)==1 and all(value>=0 for value in row),'Invalid joint transition row')
        matrix.append(row)
    equations=[[matrix[i][j]-int(i==j) for i in range(size)]+[F(0)] for j in range(size-1)]
    equations.append([F(1)]*size+[F(1)])
    for column in range(size):
        pivot=next((r for r in range(column,size) if equations[r][column]),None)
        require(pivot is not None,'Unique joint stationary law not established')
        equations[column],equations[pivot]=equations[pivot],equations[column]
        scale=equations[column][column]
        equations[column]=[_exact(x/scale) for x in equations[column]]
        for row in range(size):
            if row==column or not equations[row][column]:continue
            factor=equations[row][column]
            equations[row]=[_exact(x-factor*y) for x,y in zip(equations[row],equations[column])]
    pi=[row[-1] for row in equations]
    require(sum(pi)==1 and all(p>=0 for p in pi),'Invalid joint stationary mass')
    require(all(sum(pi[i]*matrix[i][j] for i in range(size))==pi[j] for j in range(size)),
            'Joint stationary residual is nonzero')
    lattice=math.lcm(*(p.denominator for p in pi))
    require(lattice.bit_length()<=4096,'Stationary sampling lattice exceeds its resource envelope')
    result={'schema':'binary-joint-stationary/1','coordinate_count':width,
        'state_order':'ascending_integer_coordinate_i_is_bit_i',
        'matrix':[[_rational(p) for p in row] for row in matrix],
        'probabilities':[_rational(p) for p in pi],
        'lattice_size':str(lattice),'counts':[str(int(p*lattice)) for p in pi]}
    canonical(result)
    return result


def build_model(report,diagnostics,spec,effects):
    spec=validate_specification(spec)
    require(type(effects) is list and 1<=len(effects)<=5,'Explicit bounded effect scenarios required')
    parsed=[_exact(_read_rational(x)) for x in effects]
    require(len(set(parsed))==len(parsed) and all(abs(x)<=1 for x in parsed),
            'Distinct binary contrasts in [-1,1] required')
    require(type(diagnostics) is dict,'Bound development diagnostics required')
    observed=diagnose(report,diagnostics.get('lags'))
    require(digest(observed)==digest(diagnostics),'Population diagnostics differ from exact source')
    scope=diagnose_source_process(report)
    result={'schema':MODEL,'status':'MODEL_OR_INFORMATION_GAP','specification':spec,
        'diagnostics':deepcopy(diagnostics),'diagnostics_hash':digest(diagnostics),
        'effects':deepcopy(effects),'population':None,'scenarios':[],'lag_bars':None,'gaps':[],
        'source_process_scope':scope,'source_identity_preservation':'NOT_ASSESSED',
        'assumption_status':'DECLARED_STRESS_NOT_FITTED_OR_VALIDATED',
        'limitations':['pooled_homogeneous_binary_response_rate','exogenous_scope_eligibility_and_knownness_masks',
            'lag_d_markov_law_effect_also_determines_serial_dependence',
            'independent_time_phases_and_zero_other_lag_correlations',
            'at_most_four_joint_response_instrument_coordinates',
            'strict_interior_transitions_are_a_capability_limit_not_universal_infeasibility',
            'not_a_raw_price_or_feature_process','not_full_H_exec_or_discovery_calibration',
            'empirical_negative_products_not_clipped_or_proof_of_population_dependence',
            'finite_PRNG_state_is_not_a_probability_law_certificate'],
        'n_min':None,'scientific_readiness':False,'classification_permitted':False}
    gaps=result['gaps']
    if observed['status']!='COMPUTED_DIAGNOSTICS':
        gaps.append(observed['reason']);return result
    gaps.extend(observed['model_identification_gaps'])
    identity=scope['identity']
    if identity is None or identity['condition_equals_outcome_at_offset_bars']>=0:
        gaps.append('negative_shifted_source_identity_required')
    else:
        result['lag_bars']=-identity['condition_equals_outcome_at_offset_bars']
        if result['lag_bars']>100000:gaps.append('lag_state_resource_envelope')
        if scope['observations']['unequal']:gaps.append('observed_source_value_identity_mismatch')
    expression=report['request']['scope_program'].get('expression')
    if canonical(expression)!=canonical({'op':'literal','type':'boolean','unit':None,'value':True}):
        gaps.append('constant_true_scope_required_by_this_model')
    totals=observed['totals'];n=totals['scope']['count']
    if not n or totals['scope']['rate'] is None:return result
    q=_read_rational(totals['scope']['rate']);known=F(n-totals['unknown']['count'],n);w=known*q
    result['population']={'q':_rational(q),'w':_rational(w),
        'source_condition_fraction':totals['condition_fraction'],'known_condition_fraction':_rational(known),
        'target':'pooled_eligible_E_Y_given_true_minus_E_Y',
        'weighting':'eligible_instrument_rows_under_exogenous_mask_law',
        'truth_is_not_realized_sample_contrast':True}
    if not 0<q<1 or not 0<w<1:return result
    for effect in parsed:
        a=_exact(q+effect);b=_exact(q-q*effect/(1-q));other=_exact(q-w*effect/(1-w))
        feasible=0<=a<=1 and 0<=b<=1
        interior=0<a<1 and 0<b<1
        result['scenarios'].append({'effect':_rational(effect),'p_true':_rational(a),
            'p_other':_rational(other),'transition_p_zero':_rational(b),'transition_p_one':_rational(a),
            'feasible':feasible,'within_transition_capability':interior})
        if not feasible:gaps.append('infeasible_declared_transition')
        elif not interior:gaps.append('transition_boundary_outside_current_capability')
    result['gaps']=sorted(set(gaps))
    if not result['gaps']:
        result['status']='MODEL_SPECIFIED'
        result['source_identity_preservation']='PRESERVED_ON_JOINTLY_OBSERVED_SYNTHETIC_VALUES'
    canonical(result)
    return result


def _rng(seed,key):
    return random.Random(int.from_bytes(hashlib.sha256(canonical(
        {'schema':WORLD,'seed':seed,'stream':key}).encode()).digest(),'big'))


def _sample_state(rng,law):
    draw=rng.randrange(int(law['lattice_size']));total=0
    for state,count in enumerate(law['counts']):
        total+=int(count)
        if draw<total:return state
    raise AssertionError('Stationary integer CDF has insufficient mass')


def _generate(report,model,components,time_rows,seed):
    from .population_models import _bernoulli,_instant
    require(type(model) is dict and model.get('schema')==MODEL,'Lag-linked model required')
    require(digest(model)==digest(build_model(report,model.get('diagnostics'),model.get('specification'),model.get('effects'))),
            'Lag-linked model differs from bound source and recipe')
    require(model['status']=='MODEL_SPECIFIED','Unresolved lag-linked model cannot generate')
    integer(time_rows,'joint time rows',1);randomness(seed)
    symbols=sorted(report['request']['universe']['instruments']);horizon=report['request']['horizon_bars']
    dimensions=[(item['id'],symbol) for item in components for symbol in symbols]
    width=len(dimensions);lag=model['lag_bars']
    require(width<=4 and lag*width<=100000,'Joint lag state exceeds exact stationary capability')
    require(horizon<time_rows and time_rows*width<=100000,'Generated cases exceed their envelope')
    rates=[model['scenarios'][item['scenario']] for item in components for _ in symbols]
    transitions=[[_read_rational(row[key]) for key in ('transition_p_zero','transition_p_one')] for row in rates]
    share=_read_rational(model['specification']['common_share'])
    law=stationary_joint(transitions,share)
    initial_rng=_rng(seed,'stationary-phase-states')
    states=[_sample_state(initial_rng,law) for _ in range(lag)]
    initial_states=list(states)
    lattice=math.lcm(*(p.denominator for pair in transitions for p in pair))
    require(lattice.bit_length()<=4096,'Innovation lattice exceeds numeric envelope')
    thresholds=[[int(p*lattice) for p in pair] for pair in transitions]
    common_rng=_rng(seed,'common-innovation');mask_rng=_rng(seed,'joint-mask')
    own=[_rng(seed,['individual-innovation',*coordinate]) for coordinate in dimensions]
    choice=[_rng(seed,['common-choice',*coordinate]) for coordinate in dimensions]
    source_width=len(symbols);source_size=len(report['cases'])//source_width
    mask=mask_rng.randrange(source_size);restart=F(1,model['specification']['mask_mean_block'])
    buffers=[[] for _ in components];forced=[0]*len(components)
    for t in range(time_rows):
        common=common_rng.randrange(lattice);previous=states[t%lag];current=0
        for i,(response,symbol) in enumerate(dimensions):
            prior=(previous>>i)&1
            individual=own[i].randrange(lattice)
            uniform=common if _bernoulli(choice[i],share) else individual
            value=int(uniform<thresholds[i][prior]);current|=value<<i
            source=report['cases'][mask*source_width+i%source_width]
            status=source['status'];terminal=source.get('scope') is True and t+horizon>=time_rows
            if status=='PARTITION_BOUNDARY' or status=='DATA_GAP' and source.get('scope') is True:status='OUTCOME_MISSING'
            if terminal:status='PARTITION_BOUNDARY';forced[i//source_width]+=1
            when=t*900;anchor=(t+horizon)*900
            case={'decision_time':when,'instrument':symbol,'outcome_anchor':anchor,
                'scope':source.get('scope'),'condition':bool(prior) if source.get('condition') is not None else None,
                'status':status,'outcome':None,'trace':None,'label_information_interval':None,
                'reason':'synthetic_terminal_censor' if terminal else 'sampled_exogenous_mask:'+source['status'],
                'simulation_mask':{'source_time_index':mask,'source_status':source['status'],
                    'source_condition_known':source.get('condition') is not None,'terminal_censor':terminal}}
            if status=='ELIGIBLE':
                case['outcome']=_rational(value)
                case['trace']={'earliest_observation':anchor,'declared_earliest_observation':anchor,
                    'latest_available_at':anchor,'unknown_input':False,'admissible_pending_publication':False,
                    'predecision_input_published_late':False,'outcome_lookback_before_universe':False,'reasons':[]}
                case['label_information_interval']={'start':when,'end':anchor}
            buffers[i//source_width].append(case)
        states[t%lag]=current  # Advance latent histories even on wholly missing timestamps.
        mask=mask_rng.randrange(source_size) if _bernoulli(mask_rng,restart) else (mask+1)%source_size
    catalog={name+'@1':{'type':'boolean','unit':None} for name in ('synthetic_scope','synthetic_condition','synthetic_outcome')}
    def program(name):return {'schema':'research-ast/1','catalog_hash':digest(catalog),'expression':{'op':'feature','ref':name+'@1'}}
    output=[];world_id=digest([digest(model),components,time_rows,seed])
    for index,item in enumerate(components):
        cases=buffers[index];counts=Counter(c['status'] for c in cases)
        request={'schema':'reference-case-request/1','candidate_ref':'lag-linked-response:'+digest([digest(model),item['id']]),
            'data_snapshot_ref':'lag-linked-world:'+world_id,'scope_program':program('synthetic_scope'),
            'condition_program':program('synthetic_condition'),'outcome_program':program('synthetic_outcome'),
            'outcome_scale':'binary_probability','horizon_bars':horizon,
            'universe':{'start':_instant(0),'end':_instant(time_rows*900),'instruments':symbols},
            'as_of':_instant(time_rows*900),'max_steps':10000000}
        synthetic={'schema':'reference-cases/1','request':request,'outcome_unit':'ratio','cases':cases,
            'expected_case_count':len(cases),'processed_case_count':len(cases),
            'state_counts':{state:counts[state] for state in sorted(STATES)},
            'processing_complete':True,'outcomes_complete':True,'review_required':False,
            'status':'PROCESSED','resource_reason':None,'primitive_steps':0,'scientific_readiness':False,
            'simulation':{'kind':'lag_linked_binary_response_and_exogenous_masks','raw_AST_executed':False,
                'lag_bars':lag,'response_id':item['id'],'calendar':'artificial_900_second_grid',
                'terminal_horizon_censor':True,'source_condition_values_resampled':False}}
        output.append({'id':item['id'],'scenario':item['scenario'],'truth':deepcopy(model['scenarios'][item['scenario']]),
            'terminal_censored_cases':forced[index],'report':synthetic,'descriptive':reference_contrast(synthetic)})
    return output,{'coordinates':[{'response_id':x,'instrument':y} for x,y in dimensions],
        'independent_phase_count':lag,'law':law,'initial_states':initial_states}


def generate_world(report,model,scenario,time_rows,seed):
    integer(scenario,'scenario',0)
    require(type(model) is dict and type(model.get('scenarios')) is list and scenario<len(model['scenarios']),
            'Undeclared lag-linked scenario')
    output,initialization=_generate(report,model,[{'id':'response','scenario':scenario}],time_rows,seed)
    component=output[0]
    return {'schema':WORLD,'status':'GENERATED_UNCALIBRATED','model_hash':digest(model),
        **{key:value for key,value in component.items() if key!='id'},
        'time_rows':time_rows,'randomness':randomness(seed),'initialization':initialization,
        'randomness_law':'exact_joint_stationary_phase_draws_and_fresh_shared_threshold_innovations',
        'n_min':None,'scientific_readiness':False,'classification_permitted':False}


def generate_family(report,model,components,time_rows,seed):
    from .family_models import validate_components
    require(type(model) is dict and type(model.get('scenarios')) is list,'Lag-linked model required')
    components=validate_components(components,len(model['scenarios']))
    output,initialization=_generate(report,model,components,time_rows,seed)
    return {'schema':FAMILY,'status':'GENERATED_UNCALIBRATED','model_hash':digest(model),
        'components':output,'time_rows':time_rows,'randomness':randomness(seed),'initialization':initialization,
        'randomness_law':'exact_joint_stationary_phase_draws_and_fresh_shared_threshold_innovations',
        'limitations':list(model['limitations'])+['response_specific_lagged_conditions_shared_exogenous_masks',
            'distinct_synthetic_responses_not_different_real_ASTs_on_one_price_process'],
        'outer_world_count':1,'n_min':None,'scientific_readiness':False,'classification_permitted':False}
