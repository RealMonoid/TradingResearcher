"""Joint synthetic responses on one shared development mask; no market authority."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import random

from .codec import canonical, digest, integer, text
from .evaluation_policy import require
from .outcomes import _rational, _read_rational, reference_contrast, STATES
from .population_models import build_model, _bernoulli, _instant
from .stationary_bootstrap import randomness


WORLD = 'binary-population-family-world/1'


def validate_components(components, scenario_count):
    require(type(components) is list and 2 <= len(components) <= 8,
            'Two through eight distinct synthetic responses required')
    for item in components:
        require(type(item) is dict and set(item) == {'id', 'scenario'}, 'Exact response identity and scenario required')
        text(item['id'], 'synthetic response identity')
        require(len(item['id']) <= 80, 'Synthetic response identity exceeds its envelope')
        integer(item['scenario'], 'scenario', 0)
        require(item['scenario'] < scenario_count, 'Undeclared response scenario')
    require(len({item['id'] for item in components}) == len(components), 'Duplicate synthetic response identity')
    return sorted(deepcopy(components), key=lambda item: item['id'])


def _rng(seed, component):
    return random.Random(int.from_bytes(hashlib.sha256(canonical(
        {'schema': WORLD, 'seed': seed, 'component': component}).encode()).digest(), 'big'))


def generate_family(report, model, components, time_rows, seed):
    if type(model) is dict and model.get('schema') == 'lag-linked-binary-model/1':
        from .lag_population import generate_family as generate_linked
        return generate_linked(report, model, components, time_rows, seed)
    expected = build_model(report, model.get('diagnostics'), model.get('specification'), model.get('effects'))
    require(digest(expected) == digest(model), 'Family model differs from its exact source and recipe')
    require(model['status'] == 'MODEL_SPECIFIED', 'Unresolved family model cannot generate a world')
    components = validate_components(components, len(model['scenarios']))
    integer(time_rows, 'joint time rows', 1)
    randomness(seed)
    instruments = sorted(report['request']['universe']['instruments'])
    width, horizon = len(instruments), report['request']['horizon_bars']
    require(horizon < time_rows and len(components)*time_rows*width <= 100000,
            'Family target exceeds its aggregate case/horizon envelope')
    lattice = int(model['lattice_size'])
    spec = model['specification']
    persistence, share = (_read_rational(spec[key]) for key in ('persistence', 'common_share'))
    mask_rng, common_rng = _rng(seed, 'joint-mask'), _rng(seed, 'common-latent')
    common = common_rng.randrange(lattice)
    source_rows = len(report['cases']) // width
    mask_index = mask_rng.randrange(source_rows)
    restart = Fraction(1, spec['mask_mean_block'])
    responses = []
    for item in components:
        identity = item['id']; rates = model['scenarios'][item['scenario']]
        latent_rngs = [_rng(seed, ['response-latent', identity, symbol]) for symbol in instruments]
        responses.append({'id': identity, 'scenario': item['scenario'], 'truth': deepcopy(rates),
            'thresholds': [int(_read_rational(rates[key])*lattice) for key in ('p_other', 'p_true')],
            'latent_rngs': latent_rngs,
            'choice_rngs': [_rng(seed, ['common-choice', identity, symbol]) for symbol in instruments],
            'individual': [rng.randrange(lattice) for rng in latent_rngs], 'cases': [], 'forced': 0})
    for t in range(time_rows):
        when, anchor = t*900, (t+horizon)*900
        for response in responses:
            for i, symbol in enumerate(instruments):
                source = report['cases'][mask_index*width+i]
                status = source['status']
                if status == 'PARTITION_BOUNDARY' or (status == 'DATA_GAP' and source.get('scope') is True):
                    status = 'OUTCOME_MISSING'
                terminal = source.get('scope') is True and t+horizon >= time_rows
                if terminal:
                    status = 'PARTITION_BOUNDARY'; response['forced'] += 1
                case = {'decision_time': when, 'instrument': symbol, 'outcome_anchor': anchor,
                    'scope': source.get('scope'), 'condition': source.get('condition'), 'status': status,
                    'outcome': None, 'trace': None, 'label_information_interval': None,
                    'reason': 'synthetic_terminal_censor' if terminal else 'sampled_joint_mask:'+source['status'],
                    'simulation_mask': {'source_time_index': mask_index, 'source_status': source['status'],
                                        'terminal_censor': terminal}}
                use_common = _bernoulli(response['choice_rngs'][i], share)
                latent = common if use_common else response['individual'][i]
                if status == 'ELIGIBLE':
                    case['outcome'] = _rational(int(latent < response['thresholds'][int(source['condition'] is True)]))
                    case['trace'] = {'earliest_observation': anchor, 'declared_earliest_observation': anchor,
                        'latest_available_at': anchor, 'unknown_input': False, 'admissible_pending_publication': False,
                        'predecision_input_published_late': False, 'outcome_lookback_before_universe': False, 'reasons': []}
                    case['label_information_interval'] = {'start': when, 'end': anchor}
                response['cases'].append(case)
        # One common transition per full timestamp, including ineligible times.
        if not _bernoulli(common_rng, persistence): common = common_rng.randrange(lattice)
        for response in responses:
            for i, rng in enumerate(response['latent_rngs']):
                if not _bernoulli(rng, persistence): response['individual'][i] = rng.randrange(lattice)
        mask_index = mask_rng.randrange(source_rows) if _bernoulli(mask_rng, restart) else (mask_index+1) % source_rows
    family_hash = digest([digest(model), components, time_rows, seed])
    catalog = {name+'@1': {'type': 'boolean', 'unit': None}
               for name in ('synthetic_scope', 'synthetic_condition', 'synthetic_outcome')}
    def program(name):
        return {'schema': 'research-ast/1', 'catalog_hash': digest(catalog),
                'expression': {'op': 'feature', 'ref': name+'@1'}}
    output = []
    for response in responses:
        cases = response['cases']; counts = Counter(row['status'] for row in cases)
        request = {'schema': 'reference-case-request/1',
            'candidate_ref': 'synthetic-response:'+digest([digest(model), response['id']]),
            'data_snapshot_ref': 'synthetic-family:'+family_hash,
            'scope_program': program('synthetic_scope'), 'condition_program': program('synthetic_condition'),
            'outcome_program': program('synthetic_outcome'), 'outcome_scale': 'binary_probability',
            'horizon_bars': horizon, 'universe': {'start': _instant(0), 'end': _instant(time_rows*900),
                'instruments': instruments}, 'as_of': _instant(time_rows*900), 'max_steps': 10000000}
        synthetic = {'schema': 'reference-cases/1', 'request': request, 'outcome_unit': 'ratio', 'cases': cases,
            'expected_case_count': len(cases), 'processed_case_count': len(cases),
            'state_counts': {state: counts[state] for state in sorted(STATES)},
            'processing_complete': True, 'outcomes_complete': True, 'review_required': False,
            'status': 'PROCESSED', 'resource_reason': None, 'primitive_steps': 0, 'scientific_readiness': False,
            'simulation': {'kind': 'distinct_response_shared_template_mask', 'raw_AST_executed': False,
                'response_id': response['id'], 'calendar': 'artificial_900_second_grid', 'terminal_horizon_censor': True}}
        output.append({'id': response['id'], 'scenario': response['scenario'], 'truth': response['truth'],
            'terminal_censored_cases': response['forced'], 'report': synthetic, 'descriptive': reference_contrast(synthetic)})
    return {'schema': WORLD, 'status': 'GENERATED_UNCALIBRATED', 'model_hash': digest(model),
        'components': output, 'time_rows': time_rows, 'randomness': randomness(seed),
        'randomness_law': 'shared_stationary_mask_and_common_latent_with_response_instrument_specific_latents',
        'limitations': ['same_template_q_w_and_masks', 'distinct_synthetic_responses_not_original_AST_truths',
            'zero_common_share_does_not_imply_independence', 'not_market_model_adequacy_or_full_process_calibration'],
        'outer_world_count': 1, 'n_min': None, 'scientific_readiness': False, 'classification_permitted': False}


def family_events(outcomes, delta, direction):
    """One joint event per world; unknown required members never become success."""
    delta = _read_rational(delta)
    require(delta > 0 and direction in ('positive', 'negative', 'nondirectional'), 'Exact assigned effect profile required')
    require(type(outcomes) is list and 2 <= len(outcomes) <= 8, 'Bounded family outcomes required')
    require(len({item['id'] for item in outcomes}) == len(outcomes), 'Duplicate response outcome')
    coverage, nulls, boundaries, detections = [], [], [], {}
    for item in outcomes:
        text(item['id'], 'response identity')
        truth = _read_rational(item['truth'])
        state = item['state']; decision = item['decision']; covered = item['covered']
        require(state in ('VERIFIED', 'INFORMATION_GAP', 'MODEL_GAP', 'TECHNICAL_FAILURE'), 'Invalid response state')
        if state == 'VERIFIED':
            require(type(covered) is bool and decision in ('SUPPORTED_INITIAL', 'TESTED_NEGATIVE', 'TESTED_INCONCLUSIVE'),
                    'Verified response needs its interval coverage and decision')
        else:
            require(covered is None and decision is None, 'Unavailable response cannot supply coverage or a decision')
        known = state in ('VERIFIED', 'INFORMATION_GAP')
        support = decision == 'SUPPORTED_INITIAL' if known else None
        decisive = decision in ('SUPPORTED_INITIAL', 'TESTED_NEGATIVE') if known else None
        coverage.append(not covered if type(covered) is bool else None)
        signed = -truth if direction == 'negative' else abs(truth) if direction == 'nondirectional' else truth
        if truth == 0: nulls.append(support)
        if signed == delta: boundaries.append(decisive)
        if signed == 2*delta: detections[item['id']] = support
    def union(values):
        return True if True in values else None if not values or None in values else False
    return {'joint_miscoverage': union(coverage), 'false_support': union(nulls),
            'boundary_decisive': union(boundaries), 'detections': detections}
