"""Explicit development stress worlds for the pooled binary estimator.

These are response/mask worlds, not executions of the source hypothesis AST.
No fitting, power selection, calibration or scientific authority occurs here.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import math
import random

from .codec import canonical, digest, integer, text
from .evaluation_policy import require
from .information_diagnostics import diagnose
from .outcomes import _rational, _read_rational, reference_contrast, STATES
from .stationary_bootstrap import randomness


SPEC = 'binary-population-spec/1'
MODEL = 'binary-population-model/1'
WORLD = 'binary-population-world/1'


def specification(mask_mean_block, persistence, common_share, rationale):
    spec = {'schema': SPEC, 'mask_mean_block': mask_mean_block,
            'persistence': _rational(Fraction(persistence)),
            'common_share': _rational(Fraction(common_share)), 'rationale': rationale}
    return validate_specification(spec)


def validate_specification(spec):
    require(type(spec) is dict and set(spec) == {'schema', 'mask_mean_block', 'persistence',
            'common_share', 'rationale'} and spec['schema'] == SPEC, 'Exact population specification required')
    integer(spec['mask_mean_block'], 'mask mean block', 1)
    require(spec['mask_mean_block'] <= 1000000, 'Mask length exceeds the simulation envelope')
    text(spec['rationale'], 'stress rationale')
    for key in ('persistence', 'common_share'):
        value = _read_rational(spec[key])
        require(0 <= value <= 1 and value.denominator <= 1000000, 'Bounded exact dependence probability required')
    require(_read_rational(spec['persistence']) < 1, 'Perfect persistence is outside this stationary mixing profile')
    return deepcopy(spec)


def build_model(report, diagnostics, spec, effects):
    """Bind empirical q,w and all declared effects; never fit to power outcomes."""
    spec = validate_specification(spec)
    require(type(effects) is list and 1 <= len(effects) <= 5, 'Explicit bounded effect scenarios required')
    parsed = [_read_rational(value) for value in effects]
    require(len(set(parsed)) == len(parsed) and all(abs(value) <= 1 for value in parsed),
            'Distinct binary population contrasts in [-1,1] required')
    require(type(diagnostics) is dict, 'Bound development diagnostics required')
    observed = diagnose(report, diagnostics.get('lags'))
    require(digest(observed) == digest(diagnostics), 'Population diagnostics differ from the exact case inputs')
    model = {'schema': MODEL, 'status': 'MODEL_OR_INFORMATION_GAP', 'specification': spec,
        'diagnostics': deepcopy(diagnostics), 'diagnostics_hash': digest(diagnostics), 'effects': deepcopy(effects),
        'population': None, 'scenarios': [], 'lattice_size': None, 'gaps': [],
        'assumption_status': 'DECLARED_STRESS_NOT_FITTED_OR_VALIDATED',
        'limitations': ['pooled_homogeneous_response_rates', 'exogenous_joint_masks',
            'nonnegative_latent_persistence_and_common_share_only',
            'not_a_raw_price_or_feature_process', 'not_full_H_exec_or_discovery_calibration',
            'empirical_negative_products_are_not_clipped_or_proof_of_negative_population_dependence',
            'finite_PRNG_state_is_not_a_probability_law_certificate'],
        'observed_negative_products': [], 'n_min': None,
        'scientific_readiness': False, 'classification_permitted': False}
    if observed['status'] != 'COMPUTED_DIAGNOSTICS':
        model['gaps'].append(observed['reason'])
        return model
    model['gaps'] = list(observed['model_identification_gaps'])
    for item in observed['instrument_diagnostics']:
        for moment in item['outcome_lag_products']:
            if moment['fixed_center_product'] is not None and _read_rational(moment['fixed_center_product']) < 0:
                model['observed_negative_products'].append({'instrument': item['instrument'], 'lag': moment['lag']})
    for item in observed['cross_instrument_products']:
        if item['fixed_center_product'] is not None and _read_rational(item['fixed_center_product']) < 0:
            model['observed_negative_products'].append({'left': item['left_instrument'], 'right': item['right_instrument']})
    totals = observed['totals']
    if totals['scope']['rate'] is None or totals['condition_fraction'] is None:
        return model
    q, w = _read_rational(totals['scope']['rate']), _read_rational(totals['condition_fraction'])
    model['population'] = {'q': _rational(q), 'w': _rational(w),
        'target': 'pooled_eligible_E_Y_given_true_minus_E_Y',
        'weighting': 'eligible_instrument_rows_in_stationary_joint_mask_law',
        'truth_is_not_realized_sample_contrast': True}
    if not 0 < w < 1 or not 0 < q < 1:
        return model
    lattice = 1
    for effect in parsed:
        pt, po = q + effect, q - w * effect / (1 - w)
        feasible = 0 <= pt <= 1 and 0 <= po <= 1
        model['scenarios'].append({'effect': _rational(effect), 'p_true': _rational(pt),
                                  'p_other': _rational(po), 'feasible': feasible})
        lattice = math.lcm(lattice, pt.denominator, po.denominator)
    if any(not item['feasible'] for item in model['scenarios']):
        model['gaps'].append('infeasible_declared_effect')
    if lattice.bit_length() > 4096:
        model['gaps'].append('exact_lattice_resource_envelope')
    else:
        model['lattice_size'] = str(lattice)
    if not model['gaps']:
        model['status'] = 'MODEL_SPECIFIED'
    canonical(model)
    return model


def _rng(seed, component):
    material = {'schema': WORLD, 'seed': seed, 'component': component}
    return random.Random(int.from_bytes(hashlib.sha256(canonical(material).encode()).digest(), 'big'))


def _bernoulli(rng, probability):
    # randrange uses integer rejection sampling, without floating-point thresholds.
    return rng.randrange(probability.denominator) < probability.numerator


def _instant(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def generate_world(report, model, scenario, time_rows, seed):
    """Generate a replayable estimator-level dataset with a fixed population truth.

    The artificial final horizon censors otherwise eligible rows. All earlier
    rows have the same stationary mask marginal, so this independent calendar
    restriction leaves population q,w unchanged; realized ratios still vary.
    """
    require(type(model) is dict and model.get('schema') == MODEL, 'Population model required')
    expected = build_model(report, model.get('diagnostics'), model.get('specification'), model.get('effects'))
    require(digest(expected) == digest(model), 'Population model differs from its bound source and recipe')
    require(model['status'] == 'MODEL_SPECIFIED', 'Unresolved population model cannot generate a world')
    integer(scenario, 'scenario', 0)
    require(scenario < len(model['scenarios']), 'Undeclared effect scenario')
    integer(time_rows, 'joint time rows', 1)
    randomness(seed)
    instruments = sorted(report['request']['universe']['instruments'])
    width, horizon = len(instruments), report['request']['horizon_bars']
    require(horizon < time_rows and time_rows * width <= 100000, 'World target exceeds its case/horizon envelope')
    spec = model['specification']; rates = model['scenarios'][scenario]
    lattice = int(model['lattice_size'])
    thresholds = [int(_read_rational(rates[key])*lattice) for key in ('p_other', 'p_true')]
    persistence = _read_rational(spec['persistence']); share = _read_rational(spec['common_share'])
    mask_rng = _rng(seed, 'joint-mask'); common_rng = _rng(seed, 'common-latent')
    latent_rngs = [_rng(seed, ['instrument-latent', symbol]) for symbol in instruments]
    choice_rngs = [_rng(seed, ['common-choice', symbol]) for symbol in instruments]
    common = common_rng.randrange(lattice)
    individual = [rng.randrange(lattice) for rng in latent_rngs]
    source_rows = len(report['cases']) // width
    mask_index = mask_rng.randrange(source_rows)
    restart = Fraction(1, spec['mask_mean_block'])
    catalog = {name+'@1': {'type': 'boolean', 'unit': None} for name in ('synthetic_scope', 'synthetic_condition', 'synthetic_outcome')}
    def program(name):
        return {'schema': 'research-ast/1', 'catalog_hash': digest(catalog),
                'expression': {'op': 'feature', 'ref': name+'@1'}}
    request = {'schema': 'reference-case-request/1', 'candidate_ref': 'synthetic-population:'+digest(model),
        'data_snapshot_ref': 'synthetic-world:'+digest([digest(model), scenario, time_rows, seed]),
        'scope_program': program('synthetic_scope'), 'condition_program': program('synthetic_condition'),
        'outcome_program': program('synthetic_outcome'), 'outcome_scale': 'binary_probability',
        'horizon_bars': horizon, 'universe': {'start': _instant(0), 'end': _instant(time_rows*900),
            'instruments': instruments}, 'as_of': _instant(time_rows*900), 'max_steps': 10000000}
    cases = []; forced = 0
    for t in range(time_rows):
        when, anchor = t*900, (t+horizon)*900
        for i, symbol in enumerate(instruments):
            source = report['cases'][mask_index*width+i]
            status = source['status']
            # A sampled source boundary is a missing response in this artificial
            # calendar, not a new calendar boundary. Keep its exact origin below.
            if status == 'PARTITION_BOUNDARY' or (status == 'DATA_GAP' and source.get('scope') is True):
                status = 'OUTCOME_MISSING'
            terminal = source.get('scope') is True and t+horizon >= time_rows
            if terminal:
                status = 'PARTITION_BOUNDARY'; forced += 1
            case = {'decision_time': when, 'instrument': symbol, 'outcome_anchor': anchor,
                'scope': source.get('scope'), 'condition': source.get('condition'), 'status': status,
                'outcome': None, 'trace': None, 'label_information_interval': None,
                'reason': 'synthetic_terminal_censor' if terminal else 'sampled_joint_mask:'+source['status'],
                'simulation_mask': {'source_time_index': mask_index, 'source_status': source['status'],
                                    'terminal_censor': terminal}}
            use_common = _bernoulli(choice_rngs[i], share)
            latent = common if use_common else individual[i]
            if status == 'ELIGIBLE':
                case['outcome'] = _rational(int(latent < thresholds[int(source['condition'] is True)]))
                case['trace'] = {'earliest_observation': anchor, 'declared_earliest_observation': anchor,
                    'latest_available_at': anchor, 'unknown_input': False, 'admissible_pending_publication': False,
                    'predecision_input_published_late': False, 'outcome_lookback_before_universe': False, 'reasons': []}
                case['label_information_interval'] = {'start': when, 'end': anchor}
            cases.append(case)
        # Latents evolve even on entirely ineligible timestamps.
        if not _bernoulli(common_rng, persistence):common = common_rng.randrange(lattice)
        for i, rng in enumerate(latent_rngs):
            if not _bernoulli(rng, persistence):individual[i] = rng.randrange(lattice)
        mask_index = mask_rng.randrange(source_rows) if _bernoulli(mask_rng, restart) else (mask_index+1) % source_rows
    counts = Counter(row['status'] for row in cases)
    synthetic = {'schema': 'reference-cases/1', 'request': request, 'outcome_unit': 'ratio', 'cases': cases,
        'expected_case_count': len(cases), 'processed_case_count': len(cases),
        'state_counts': {state: counts[state] for state in sorted(STATES)},
        'processing_complete': True, 'outcomes_complete': True, 'review_required': False,
        'status': 'PROCESSED', 'resource_reason': None, 'primitive_steps': 0, 'scientific_readiness': False,
        'simulation': {'kind': 'estimator_response_and_mask_only', 'raw_AST_executed': False,
            'calendar': 'artificial_900_second_grid', 'terminal_horizon_censor': True}}
    descriptive = reference_contrast(synthetic)
    return {'schema': WORLD, 'status': 'GENERATED_UNCALIBRATED', 'model_hash': digest(model),
        'scenario': scenario, 'truth': deepcopy(rates), 'time_rows': time_rows, 'randomness': randomness(seed),
        'randomness_law': 'domain_separated_MT19937_integer_rejection_exact_rational_thresholds',
        'terminal_censored_cases': forced, 'report': synthetic, 'descriptive': descriptive,
        'n_min': None, 'scientific_readiness': False, 'classification_permitted': False}
