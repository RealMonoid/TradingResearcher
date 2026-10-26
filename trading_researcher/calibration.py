"""Adopted narrow-calibration count checks, not an authenticated certificate.

The caller must separately establish frozen estimator/population identity, correct
event definitions, fresh independent worlds and genuine retained execution. This
module neither generates worlds nor turns supplied booleans into that evidence.
"""
from copy import deepcopy
from fractions import Fraction

from .codec import canonical, decode, digest, strings, text
from .evaluation_policy import require
from .information_study import _tail_compare, outer_interval
from .outcomes import _rational


PLAN = 'narrow-calibration-assessment-plan/1'
CRITERIA = frozenset({'false_support', 'boundary_decisive', 'joint_miscoverage', 'detection'})
APPLICABILITY = frozenset({'heavy_tail', 'overlap', 'common_shock'})
WORLDS = 256
TAIL = Fraction(1, 20)


def one_sided_bound(k, n, side, bits=40):
    """Outward exact-binomial endpoint; its finite dyadic bracket is explicit."""
    require(type(side) is str and side in ('lower', 'upper'), 'Unknown bound side')
    # A central 90% interval has the same two endpoints as separate one-sided
    # 95% bounds. Expose only the requested side; do not label their union 95%.
    interval = outer_interval(k, n, _rational(2 * TAIL), bits=bits)
    return {'method': 'clopper-pearson-one-sided-dyadic-outward/1', 'side': side,
            'noncoverage': _rational(TAIL), 'bits': bits, 'bound': interval[side],
            'root_bracket': interval[side + '_root_bracket'],
            'maximum_bracket_width': interval['maximum_bracket_width']}


def _worlds(world_ids):
    strings(world_ids, 'planned world IDs')
    require(len(world_ids) == WORLDS, 'Exactly 256 distinct predeclared worlds are required per cohort')


def _observation(record):
    require(type(record) is dict and set(record) == {
        'cohort_id', 'world_id', 'state', 'event', 'source_ref', 'reason'}, 'Exact calibration observation required')
    for name in ('cohort_id', 'world_id', 'source_ref'):
        text(record[name], name)
    require(type(record['state']) is str and record['state'] in ('observed', 'unavailable'),
            'Unknown observation state')
    if record['state'] == 'observed':
        require(type(record['event']) is bool and record['reason'] is None,
                'Observed events require an exact Boolean and no unavailable reason')
    else:
        require(record['event'] is None, 'Unavailable events cannot be counted as false')
        text(record['reason'], 'unavailable reason')


def evaluate_cohort(criterion, world_ids, observations):
    """Assess one fixed world law without pooling or dropping unknown outcomes."""
    detached = decode(canonical({'world_ids': world_ids, 'observations': observations}))
    world_ids, observations = detached['world_ids'], detached['observations']
    require(type(criterion) is str and criterion in CRITERIA, 'Unknown calibration criterion')
    _worlds(world_ids)
    require(type(observations) is list and len(observations) <= WORLDS, 'Bounded cohort observations required')
    planned = set(world_ids)
    seen = {}
    cohorts = set()
    for record in observations:
        _observation(record)
        world = record['world_id']
        require(world in planned and world not in seen, 'Unplanned or duplicate world observation')
        seen[world] = record
        cohorts.add(record['cohort_id'])
    require(len(cohorts) <= 1, 'Different cohorts cannot share a count denominator')
    observed = [record for record in observations if record['state'] == 'observed']
    unavailable = [record['world_id'] for record in observations if record['state'] == 'unavailable']
    missing = [world for world in world_ids if world not in seen]
    count = sum(record['event'] for record in observed)
    complete = len(observed) == WORLDS
    detection = criterion == 'detection'
    threshold = Fraction(7, 10) if detection else Fraction(1, 10)
    result = {'criterion': criterion, 'status': 'NOT_ASSESSED', 'complete': complete,
              'planned': WORLDS, 'observed': len(observed), 'observed_events': count,
              'unavailable_world_ids': unavailable, 'missing_world_ids': missing,
              'source_refs': sorted({record['source_ref'] for record in observations}),
              'point': None, 'bound': None, 'threshold': _rational(threshold),
              'threshold_relation': 'lower_at_least' if detection else 'upper_at_most',
              'threshold_met': None, 'design_target_met': None,
              'input_authentication': 'UNVERIFIED', 'scientific_readiness': False}
    if not complete:
        return result
    # Compare the exact binomial polynomial at the adopted threshold. Rounding
    # the displayed confidence endpoint must not decide admission at equality.
    met = _tail_compare(count, WORLDS, threshold, TAIL, survival=detection) <= 0
    result.update(status='PASS_COUNTS_ONLY' if met else 'FAIL_COUNTS_ONLY',
                  point=_rational(Fraction(count, WORLDS)),
                  bound=one_sided_bound(count, WORLDS, 'lower' if detection else 'upper'),
                  threshold_met=met,
                  design_target_met=(5 * count >= 4 * WORLDS) if detection else None)
    return result


def _manifest(manifest):
    require(type(manifest) is dict and set(manifest) == {
        'schema', 'estimator_ref', 'population_ref', 'cohorts', 'applicability'}, 'Exact count-assessment plan required')
    require(manifest['schema'] == PLAN, 'Unknown count-assessment plan version')
    for name in ('estimator_ref', 'population_ref'):
        text(manifest[name], name)
    cohorts = manifest['cohorts']
    require(type(cohorts) is list and 1 <= len(cohorts) <= 16, 'One through sixteen predeclared cohorts required')
    ids = set()
    criteria = set()
    for cohort in cohorts:
        require(type(cohort) is dict and set(cohort) == {'id', 'criterion', 'world_ids', 'rationale'},
                'Exact cohort definition required')
        text(cohort['id'], 'cohort ID')
        text(cohort['rationale'], 'cohort rationale')
        require(cohort['id'] not in ids, 'Duplicate cohort ID')
        require(type(cohort['criterion']) is str and cohort['criterion'] in CRITERIA, 'Unknown cohort criterion')
        ids.add(cohort['id'])
        criteria.add(cohort['criterion'])
        _worlds(cohort['world_ids'])
    require(criteria == CRITERIA, 'Zero, boundary, joint-coverage and alternative criteria are all required')
    applicability = manifest['applicability']
    require(type(applicability) is dict and set(applicability) == APPLICABILITY,
            'Explicit heavy-tail, overlap and common-shock applicability required')
    for issue, declaration in applicability.items():
        require(type(declaration) is dict and set(declaration) == {'status', 'cohort_ids', 'reason'},
                'Exact applicability declaration required')
        text(declaration['reason'], issue + ' applicability reason')
        refs = strings(declaration['cohort_ids'], 'applicability cohort IDs')
        require(set(refs) <= ids, 'Applicability references an undeclared cohort')
        require(type(declaration['status']) is str and declaration['status'] in ('included', 'not_applicable'),
                'Unknown applicability status')
        require(bool(refs) == (declaration['status'] == 'included'), 'Applicability status and cohort references disagree')


def assess_calibration(manifest, observations):
    """Retain complete count decisions while leaving scientific admission external."""
    request = decode(canonical({'manifest': manifest, 'observations': observations}))
    manifest, observations = request['manifest'], request['observations']
    _manifest(manifest)
    require(type(observations) is list and len(observations) <= len(manifest['cohorts']) * WORLDS,
            'Bounded complete-cohort observation list required')
    grouped = {cohort['id']: [] for cohort in manifest['cohorts']}
    for record in observations:
        _observation(record)
        require(record['cohort_id'] in grouped, 'Observation belongs to an undeclared cohort')
        grouped[record['cohort_id']].append(record)
    reports = [{'cohort_id': cohort['id'], **evaluate_cohort(
        cohort['criterion'], cohort['world_ids'], grouped[cohort['id']])} for cohort in manifest['cohorts']]
    complete = all(report['complete'] for report in reports)
    status = ('NOT_ASSESSED' if not complete else 'PASS_COUNTS_ONLY'
              if all(report['threshold_met'] for report in reports) else 'FAIL_COUNTS_ONLY')
    return {'schema': 'narrow-calibration-count-assessment/1', 'status': status, 'complete': complete,
            'input_hash': digest(request), 'plan_hash': digest(manifest),
            'estimator_ref': manifest['estimator_ref'], 'population_ref': manifest['population_ref'],
            'cohorts': reports, 'applicability': deepcopy(manifest['applicability']),
            'input_authentication': 'UNVERIFIED', 'freshness': 'UNVERIFIED',
            'event_semantics': 'UNVERIFIED', 'applicability_evidence': 'UNVERIFIED',
            'scientific_readiness': False, 'n_min': None,
            'qualification': 'Exact adopted count thresholds only. Source references and declarations do not '
                'authenticate real executions, event meanings, independent fresh worlds, model adequacy, '
                'estimator conformance or full-process calibration.'}
