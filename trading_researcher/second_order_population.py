"""Declared second-order lag stress; dependence varies at a fixed contrast."""
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import random

from .codec import canonical, digest, integer, text
from .evaluation_policy import require
from .outcomes import _rational, _read_rational
from .stationary_bootstrap import randomness
from . import lag_population as first


SPEC='lag-linked-second-order-spec/1'
MODEL='lag-linked-second-order-model/1'
WORLD='lag-linked-second-order-world/1'
FAMILY='lag-linked-second-order-family-world/1'


def specification(mask_mean_block,beta,common_share,rationale):
    return validate_specification({'schema':SPEC,'mask_mean_block':mask_mean_block,
        'beta':_rational(first._exact(beta)),'common_share':_rational(first._exact(common_share)),
        'rationale':rationale})


def validate_specification(spec):
    require(type(spec) is dict and set(spec)=={'schema','mask_mean_block','beta','common_share','rationale'}
            and spec['schema']==SPEC,'Exact second-order lag specification required')
    first.validate_specification({key:value for key,value in spec.items() if key!='beta'}|{'schema':first.SPEC})
    beta=first._exact(_read_rational(spec['beta']))
    require(-1<beta<1 and beta.denominator<=1000000,'Bounded signed second-order dependence required')
    return deepcopy(spec)


def stationary_joint(transitions,common_share):
    """Exact joint stationary histories, with old bits below recent bits.

    Four rates per coordinate are indexed old+2*recent. Two consecutive all-zero
    innovations reset every history, establishing a unique stationary class even
    if fully shared innovations make some states transient. No finite burn-in.
    """
    require(type(transitions) is list and 1<=len(transitions)<=2,
            'Second-order stationary solver supports one or two coordinates')
    share=first._exact(common_share)
    require(0<=share<=1,'Common innovation share outside [0,1]')
    rates=[]
    for values in transitions:
        require(type(values) in (tuple,list) and len(values)==4,'Four exact history probabilities required')
        row=[first._exact(p) for p in values]
        require(all(0<p<1 for p in row),'Strict-interior history transition capability required')
        rates.append(row)
    width=len(rates);size=1<<(2*width);matrix=[]
    for prior in range(size):
        thresholds=[rates[i][((prior>>i)&1)+2*((prior>>(i+width))&1)] for i in range(width)]
        innovation=first._innovation_probabilities(thresholds,share)
        row=[F(0)]*size;recent=prior>>width
        for value,p in enumerate(innovation):row[recent|(value<<width)]=p
        matrix.append(row)
    result={'schema':'binary-second-order-joint-stationary/1','coordinate_count':width,
        'history_order':2,'state_order':'old_coordinate_i_bit_i_recent_coordinate_i_bit_i_plus_width',
        **first._stationary_solution(matrix)}
    canonical(result)
    return result


def build_model(report,diagnostics,spec,effects):
    spec=validate_specification(spec)
    base_spec=first.specification(spec['mask_mean_block'],_read_rational(spec['common_share']),spec['rationale'])
    result=first.build_model(report,diagnostics,base_spec,effects)
    result['schema']=MODEL;result['specification']=spec;result['history_order']=2
    result['status']='MODEL_OR_INFORMATION_GAP';result['source_identity_preservation']='NOT_ASSESSED'
    replaced={'lag_d_markov_law_effect_also_determines_serial_dependence',
              'at_most_four_joint_response_instrument_coordinates'}
    result['limitations']=[x for x in result['limitations'] if x not in replaced]+[
        'second_order_affine_law_not_arbitrary_dependence',
        'at_most_two_joint_response_instrument_coordinates_with_two_bit_histories',
        'signed_beta_is_declared_stress_not_a_fitted_nuisance_parameter']
    if result['population'] is None:return result
    q=_read_rational(result['population']['q']);beta=_read_rational(spec['beta'])
    if not 0<q<1:return result
    for row in result['scenarios']:
        effect=_read_rational(row['effect']);alpha=first._exact((1-beta)*effect/(1-q))
        rates=[first._exact(q+alpha*(recent-q)+beta*(old-q)) for recent in (0,1) for old in (0,1)]
        pair=[first._exact(x) for x in ((1-q)**2+q*effect,q*(1-q-effect),
                                       q*(1-q-effect),q*(q+effect))]
        row.pop('transition_p_zero');row.pop('transition_p_one')
        row.update({'alpha':_rational(alpha),'history_transitions':[_rational(p) for p in rates],
            'history_index':'old_plus_two_recent','lag_pair_probabilities':[_rational(p) for p in pair],
            'feasible':all(0<=p<=1 for p in rates+pair),
            'within_transition_capability':all(0<p<1 for p in rates+pair)})
        if not row['feasible']:result['gaps'].append('infeasible_second_order_transition')
        elif not row['within_transition_capability']:result['gaps'].append('second_order_boundary_outside_current_capability')
    result['gaps']=sorted(set(result['gaps']))
    if result['scenarios'] and not result['gaps']:
        result['status']='MODEL_SPECIFIED'
        result['source_identity_preservation']='PRESERVED_ON_JOINTLY_OBSERVED_SYNTHETIC_VALUES'
    canonical(result)
    return result


def _rng(seed,key):
    return random.Random(int.from_bytes(hashlib.sha256(canonical(
        {'schema':WORLD,'seed':seed,'stream':key}).encode()).digest(),'big'))


def generate_world(report,model,scenario,time_rows,seed):
    integer(scenario,'scenario',0)
    require(type(model) is dict and type(model.get('scenarios')) is list and scenario<len(model['scenarios']),
            'Undeclared second-order scenario')
    output,initialization=first._generate(report,model,[{'id':'response','scenario':scenario}],time_rows,seed)
    return {'schema':WORLD,'status':'GENERATED_UNCALIBRATED','model_hash':digest(model),
        **{key:value for key,value in output[0].items() if key!='id'},
        'time_rows':time_rows,'randomness':randomness(seed),'initialization':initialization,
        'randomness_law':'exact_joint_stationary_histories_and_fresh_shared_threshold_innovations',
        'n_min':None,'scientific_readiness':False,'classification_permitted':False}


def generate_family(report,model,components,time_rows,seed):
    from .family_models import validate_components
    require(type(model) is dict and type(model.get('scenarios')) is list,'Second-order model required')
    components=validate_components(components,len(model['scenarios']))
    output,initialization=first._generate(report,model,components,time_rows,seed)
    return {'schema':FAMILY,'status':'GENERATED_UNCALIBRATED','model_hash':digest(model),
        'components':output,'time_rows':time_rows,'randomness':randomness(seed),'initialization':initialization,
        'randomness_law':'exact_joint_stationary_histories_and_fresh_shared_threshold_innovations',
        'limitations':list(model['limitations'])+['response_specific_lagged_conditions_shared_exogenous_masks',
            'distinct_synthetic_responses_not_different_real_ASTs_on_one_price_process'],
        'outer_world_count':1,'n_min':None,'scientific_readiness':False,'classification_permitted':False}
