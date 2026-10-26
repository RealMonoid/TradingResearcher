"""One joint stress world through the existing fixed-draw estimator."""
import time

from .codec import canonical, digest
from .evaluation_policy import require
from .family_models import generate_family, family_events
from .population_models import build_model
from .outcomes import _read_rational
from .stationary_bootstrap import calculate, randomness


RESULT = 'development-family-computation/1'


def calculate_family(payload, cases, retain, *, retain_draw_bytes=None):
    started = time.monotonic()
    report = {**payload['report'], 'cases': cases}
    model = build_model(report, payload['diagnostics'], payload['specification'], payload['effects'])
    design = payload['design']
    require(design['primary_count'] == len(payload['components']), 'Family size differs from owned plan')
    outcomes = [{'id': item['id'], 'truth': payload['effects'][item['scenario']], 'state': 'MODEL_GAP',
                 'decision': None, 'covered': None} for item in payload['components']]
    result = {'schema': RESULT, 'status': 'MODEL_OR_INFORMATION_GAP', 'model': model, 'world': None,
        'bootstraps': [], 'outcomes': outcomes, 'events': None, 'outer_world_count': 1,
        'n_min': None, 'scientific_readiness': False, 'classification_permitted': False}
    if model['status'] == 'MODEL_SPECIFIED':
        generated = generate_family(report, model, payload['components'], payload['time_rows'], payload['seed'])
        result['world'] = generated
        by_id = {item['id']: item for item in outcomes}
        for component in generated['components']:
            identity = component['id']; outcome = by_id[identity]
            for case in component['report']['cases']: retain({'kind': 'case', 'response_id': identity, 'value': case})
            prefix = b'{"kind":"draw","response_id":' + canonical(identity).encode() + b',"value":'
            bootstrap = calculate(component['report'], {**design, 'randomness': randomness(payload['bootstrap_seed'])},
                {'max_seconds': payload['limits']['max_seconds'], 'max_segments': 100000000},
                stop=lambda: time.monotonic()-started >= payload['limits']['max_seconds'],
                on_draw=(lambda draw: retain({'kind': 'draw', 'response_id': identity, 'value': draw}))
                    if retain_draw_bytes is None else None,
                on_draw_bytes=(lambda encoded: retain_draw_bytes(prefix + encoded + b'}\n'))
                    if retain_draw_bytes is not None else None)
            component['report'].pop('cases')
            result['bootstraps'].append({'id': identity, 'result': bootstrap})
            if bootstrap['status'] == 'COMPUTED_UNCALIBRATED':
                interval, diagnostic = bootstrap['interval'], bootstrap['monte_carlo']
                truth = _read_rational(outcome['truth'])
                outcome.update(state='VERIFIED', decision=diagnostic['nominal_classification']
                    if diagnostic['boundary_stable'] else 'TESTED_INCONCLUSIVE',
                    covered=_read_rational(interval['lower']) <= truth <= _read_rational(interval['upper']))
            elif (bootstrap['status'] == 'INFORMATION_GAP' or bootstrap['status'] == 'INPUT_GAP'
                    and bootstrap['reason'] in ('no_scope_cases', 'no_conditioned_cases')):
                outcome['state'] = 'INFORMATION_GAP'
            else: outcome['state'] = 'TECHNICAL_FAILURE'
        result['status'] = 'COMPUTED_UNCALIBRATED' if all(x['state'] == 'VERIFIED' for x in outcomes) else 'INCOMPLETE'
    result['events'] = family_events(outcomes, design['mc_policy']['delta'], design['mc_policy']['direction'])
    result['input_hash'] = digest(payload)
    return result
