"""Pure reference case computation. No data rights or scientific authority.

See OUTCOMES.md for the exercised envelope and explicit certification gaps.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import re

from .expressions import ExpressionGap, ReferenceEngine, gap


UTC_INSTANT = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z\Z')
PENDING = frozenset({'NOT_YET_OBSERVED', 'OUTCOME_PENDING'})
STATES = PENDING | {'ELIGIBLE', 'SCOPE_FALSE', 'SCOPE_UNKNOWN', 'OUTCOME_MISSING',
                    'DATA_GAP', 'PARTITION_BOUNDARY', 'REVIEW_REQUIRED'}


def _instant(value):
    if type(value) is not str or not UTC_INSTANT.fullmatch(value):
        gap('TEMPORAL_GAP', 'Expected an exact UTC instant ending in Z')
    try:
        result = int((datetime.fromisoformat(value) - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds())
    except ValueError:
        gap('TEMPORAL_GAP', 'Invalid calendar instant')
    if result < 0:
        gap('TEMPORAL_GAP', 'Pre-epoch observations are outside this reference envelope')
    return result


def _rational(value):
    if value is None:
        return None
    value = Fraction(value)
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}


def _read_rational(value):
    if (type(value) is not dict or set(value) != {'numerator', 'denominator'}
            or any(type(value[key]) is not str or not 1 <= len(value[key]) <= 2468
                   for key in ('numerator', 'denominator'))
            or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)', value['numerator'])
            or not re.fullmatch(r'[1-9][0-9]*', value['denominator'])):
        gap('EVALUATION_GAP', 'Eligible case requires a bounded canonical exact rational')
    result = Fraction(int(value['numerator']), int(value['denominator']))
    if max(result.numerator.bit_length(), result.denominator.bit_length()) > 8192:
        gap('RESOURCE_GAP', 'Exact outcome exceeds the numeric resource envelope')
    if _rational(result) != value:
        gap('EVALUATION_GAP', 'Outcome rational must be normalized')
    return result


def _lookback(node):
    """Maximum declared lookback, including paths skipped by missing arithmetic."""
    child_span = max((_lookback(child) for child in node.children), default=0)
    if node.op == 'lag':
        return child_span + 900 * node.parameter
    if node.op == 'trailing_mean':
        return child_span + 900 * (node.parameter - 1)
    return child_span


class _Trace:
    """Bounded metadata only; unavailable sample values never enter this object."""
    def __init__(self, decision, start, end, declared_earliest):
        self.decision, self.start, self.end = decision, start, end
        self.earliest = None
        self.latest_available = None
        self.unknown = False
        self.pending = False
        self.late_warmup = False
        self.declared_earliest = declared_earliest
        self.prior_partition = declared_earliest < start
        self.reasons = set()

    def __call__(self, when, available_at, reason):
        self.earliest = when if self.earliest is None else min(self.earliest, when)
        self.prior_partition |= when < self.start
        if available_at is not None:
            self.late_warmup |= when < self.decision and available_at > self.decision
            if reason != 'not_yet_available':
                self.latest_available = (available_at if self.latest_available is None else
                                         max(self.latest_available, available_at))
        if reason not in ('available', 'observation'):
            self.unknown = True
            self.reasons.add(reason)
        if reason == 'not_yet_available' and available_at < self.end:
            self.pending = True

    def public(self):
        return {'earliest_observation': self.earliest, 'declared_earliest_observation': self.declared_earliest,
                'latest_available_at': self.latest_available,
                'unknown_input': self.unknown, 'admissible_pending_publication': self.pending,
                'predecision_input_published_late': self.late_warmup,
                'outcome_lookback_before_universe': self.prior_partition,
                'reasons': sorted(self.reasons)}


def _validate(request):
    required = {'schema', 'candidate_ref', 'data_snapshot_ref', 'scope_program',
                'condition_program', 'outcome_program', 'outcome_scale', 'horizon_bars',
                'universe', 'as_of', 'max_steps'}
    if (type(request) is not dict or set(request) != required
            or request['schema'] != 'reference-case-request/1'):
        gap('LANGUAGE_GAP', 'Unsupported or incomplete reference case request')
    for key in ('candidate_ref', 'data_snapshot_ref'):
        if type(request[key]) is not str or not request[key].strip() or len(request[key]) > 256:
            gap('DATA_GAP', 'Expected bounded candidate and data references')
    if (type(request['horizon_bars']) is not int or not 1 <= request['horizon_bars'] <= 1000000
            or type(request['max_steps']) is not int or not 1 <= request['max_steps'] <= 10000000):
        gap('RESOURCE_GAP', 'Expected bounded positive horizon and primitive-step budget')
    if request['outcome_scale'] not in ('binary_probability', 'quantity'):
        gap('TYPE_GAP', 'Outcome scale is not supported')
    universe = request['universe']
    if type(universe) is not dict or set(universe) != {'start', 'end', 'instruments'}:
        gap('DATA_GAP', 'Expected an explicit bounded test universe')
    instruments = universe['instruments']
    if (type(instruments) is not list or not 1 <= len(instruments) <= 256
            or any(type(x) is not str or not x.strip() or len(x) > 128 for x in instruments)
            or len(set(instruments)) != len(instruments)):
        gap('DATA_GAP', 'Expected unique bounded instrument keys')
    start, end, as_of = _instant(universe['start']), _instant(universe['end']), _instant(request['as_of'])
    if start >= end:
        gap('TEMPORAL_GAP', 'Test universe must be a nonempty half-open interval')
    first = ((start + 899) // 900) * 900
    count = max(0, (end - first + 899) // 900) * len(instruments)
    if not 1 <= count <= 100000:
        gap('RESOURCE_GAP', 'Test universe requires one to 100000 grid cases')
    return start, end, as_of, first, count, sorted(instruments)


def materialize_reference(request, catalog, rows):
    """Materialize exact future-anchor cases without publishing research evidence."""
    start, end, as_of, first, expected, instruments = _validate(request)
    engine = ReferenceEngine(catalog, rows)
    scope, condition, outcome = [engine._program_node(request[key]) for key in
                                 ('scope_program', 'condition_program', 'outcome_program')]
    if scope.kind != 'boolean' or condition.kind != 'boolean':
        gap('TYPE_GAP', 'Scope and condition must be Boolean programs')
    kind = 'boolean' if request['outcome_scale'] == 'binary_probability' else 'real'
    if outcome.kind != kind:
        gap('TYPE_GAP', 'Outcome type must match the explicit scale')
    remaining = [request['max_steps']]
    lookback = _lookback(outcome)
    cases = []
    resource_reason = None
    for when in range(first, end, 900):
        for instrument in instruments:
            try:
                case = _case(engine, scope, condition, outcome, when, instrument,
                             start, end, as_of, request['horizon_bars'], remaining, lookback)
            except ExpressionGap as error:
                if error.code != 'RESOURCE_GAP':
                    raise
                resource_reason = str(error)
                break
            cases.append(case)
        if resource_reason is not None:
            break
    counts = Counter(case['status'] for case in cases)
    complete = len(cases) == expected and resource_reason is None
    return {
        'schema': 'reference-cases/1', 'request': deepcopy(request),
        'outcome_unit': 'ratio' if outcome.kind == 'boolean' else outcome.unit,
        'cases': cases, 'expected_case_count': expected, 'processed_case_count': len(cases),
        'state_counts': {state: counts[state] for state in sorted(STATES)},
        'processing_complete': complete,
        'outcomes_complete': complete and not any(counts[state] for state in PENDING),
        'review_required': bool(counts['REVIEW_REQUIRED']),
        'status': 'PROCESSED' if complete else 'RESOURCE_STOP', 'resource_reason': resource_reason,
        'primitive_steps': min(request['max_steps'], request['max_steps'] - remaining[0]),
        'scientific_readiness': False,
    }


def _case(engine, scope, condition, outcome, when, instrument, start, end, as_of, horizon, remaining, lookback):
    anchor = when + horizon * 900
    case = {'decision_time': when, 'instrument': instrument, 'outcome_anchor': anchor,
            'scope': None, 'condition': None, 'outcome': None, 'label_information_interval': None,
            'trace': None, 'status': None, 'reason': None}

    def finish(status, reason):
        case['status'], case['reason'] = status, reason
        return case

    if when > as_of:
        return finish('NOT_YET_OBSERVED', 'decision_in_future')
    if (when, instrument) not in engine.lookup:
        return finish('DATA_GAP', 'missing_decision_observation')
    value = engine._calculate(scope, when, instrument, when, remaining)
    case['scope'] = value.value
    if value.missing:
        return finish('SCOPE_UNKNOWN', value.missing)
    if value.value is False:
        return finish('SCOPE_FALSE', 'scope_false')
    conditioned = engine._calculate(condition, when, instrument, when, remaining)
    case['condition'] = conditioned.value
    if anchor >= end:
        return finish('PARTITION_BOUNDARY', 'anchor_at_or_after_exclusive_end')
    if anchor > as_of:
        return finish('OUTCOME_PENDING', 'horizon_not_elapsed')
    if (anchor, instrument) not in engine.lookup:
        return finish('DATA_GAP', 'missing_exact_outcome_observation')
    trace = _Trace(when, start, end, anchor - lookback)
    value = engine._calculate(outcome, anchor, instrument, min(as_of, end - 1), remaining, trace)
    case['trace'] = trace.public()
    case['outcome'] = _rational(value.value)
    if trace.late_warmup or trace.prior_partition or (not value.missing and trace.unknown):
        return finish('REVIEW_REQUIRED', 'outcome_dependency_membership_uncertified')
    if value.missing:
        if trace.pending:
            return finish('OUTCOME_PENDING', 'required_publication_not_available')
        return finish('OUTCOME_MISSING', value.missing)
    case['label_information_interval'] = {
        'start': when, 'end': max(anchor, trace.latest_available or anchor)}
    return finish('ELIGIBLE', 'reference_inputs_observed')


def reference_contrast(report):
    """Exact descriptive condition-minus-whole-scope contrast; no inferential claim."""
    if type(report) is not dict or report.get('schema') != 'reference-cases/1':
        gap('EVALUATION_GAP', 'Expected a reference case report')
    cases = report.get('cases')
    if (type(cases) is not list or len(cases) > 100000
            or any(type(case) is not dict or type(case.get('status')) is not str
                   or case['status'] not in STATES for case in cases)):
        gap('EVALUATION_GAP', 'Invalid reference case list')
    start, end, as_of, first, expected, instruments = _validate(report.get('request'))
    binary = report['request']['outcome_scale'] == 'binary_probability'
    if binary and report.get('outcome_unit') != 'ratio':
        gap('EVALUATION_GAP', 'Binary probability results require the ratio unit')
    if (type(report.get('expected_case_count')) is not int
            or report['expected_case_count'] != expected or len(cases) > expected):
        gap('EVALUATION_GAP', 'Report count does not match its declared universe')
    for index, case in enumerate(cases):
        if (type(case.get('decision_time')) is not int
                or case['decision_time'] != first + (index // len(instruments)) * 900
                or case.get('instrument') != instruments[index % len(instruments)]):
            gap('EVALUATION_GAP', 'Report cases must cover the ordered universe prefix exactly')
    counts = Counter(case['status'] for case in cases)
    complete = len(cases) == expected
    if (type(report.get('processed_case_count')) is not int or report['processed_case_count'] != len(cases)
            or report.get('processing_complete') is not complete
            or report.get('outcomes_complete') is not (complete and not any(counts[state] for state in PENDING))
            or report.get('review_required') is not bool(counts['REVIEW_REQUIRED'])
            or report.get('state_counts') != {state: counts[state] for state in sorted(STATES)}):
        gap('EVALUATION_GAP', 'Report completion, review and count metadata must match its cases')
    result = {'schema': 'reference-contrast/1', 'kind': 'conditional-minus-scope-mean/1',
              'status': 'INFORMATION_GAP', 'reason': None, 'scope_count': None,
              'condition_count': None, 'scope_mean': None, 'condition_mean': None,
              'effect': None, 'scientific_readiness': False}
    if report.get('processing_complete') is not True or len(cases) != report.get('expected_case_count'):
        result['reason'] = 'incomplete_processing'
        return result
    if any(case['status'] in PENDING for case in cases):
        result['reason'] = 'outcomes_pending'
        return result
    if any(case['status'] == 'REVIEW_REQUIRED' for case in cases):
        result['reason'] = 'dependency_review_required'
        return result
    total, conditioned_total = Fraction(0), Fraction(0)
    n, nc = 0, 0
    for case in cases:
        if case['status'] != 'ELIGIBLE':
            continue
        if case.get('scope') is not True or (case.get('condition') is not None
                                           and type(case['condition']) is not bool):
            gap('EVALUATION_GAP', 'Eligible cases require true scope and Boolean/unknown condition')
        anchor = case['decision_time'] + report['request']['horizon_bars'] * 900
        trace = case.get('trace')
        if (type(trace) is not dict or set(trace) != {
                'earliest_observation', 'declared_earliest_observation', 'latest_available_at', 'unknown_input',
                'admissible_pending_publication', 'predecision_input_published_late',
                'outcome_lookback_before_universe', 'reasons'}
                or any(trace[key] is not False for key in ('unknown_input', 'admissible_pending_publication',
                       'predecision_input_published_late', 'outcome_lookback_before_universe'))
                or trace['reasons'] != [] or type(trace['earliest_observation']) is not int
                or type(trace['declared_earliest_observation']) is not int
                or not start <= trace['declared_earliest_observation'] <= trace['earliest_observation'] <= anchor
                or (trace['latest_available_at'] is not None and
                    (type(trace['latest_available_at']) is not int
                     or not 0 <= trace['latest_available_at'] <= min(as_of, end - 1)))
                or type(case.get('outcome_anchor')) is not int or case['outcome_anchor'] != anchor
                or anchor >= end or anchor > as_of or case['decision_time'] > as_of
                or case.get('label_information_interval') != {
                    'start': case['decision_time'], 'end': max(anchor, trace['latest_available_at'] or anchor)}):
            gap('EVALUATION_GAP', 'Eligible case has contradictory or incomplete outcome maturity metadata')
        number = _read_rational(case.get('outcome'))
        if binary and number not in (0, 1):
            gap('EVALUATION_GAP', 'A materialized binary observation must be exactly zero or one')
        total += number
        n += 1
        if case.get('condition') is True:
            conditioned_total += number
            nc += 1
        if any(max(value.numerator.bit_length(), value.denominator.bit_length()) > 8192
               for value in (total, conditioned_total)):
            result.update(status='RESOURCE_STOP', reason='exact_sum_exceeds_numeric_envelope')
            return result
    scope_mean = total / n if n else None
    condition_mean = conditioned_total / nc if nc else None
    effect = condition_mean - scope_mean if n and nc else None
    if any(max(value.numerator.bit_length(), value.denominator.bit_length()) > 8192
           for value in (scope_mean, condition_mean, effect) if value is not None):
        result.update(status='RESOURCE_STOP', reason='exact_contrast_exceeds_numeric_envelope')
        return result
    result['scope_count'], result['condition_count'] = n, nc
    result['scope_mean'] = _rational(scope_mean)
    result['condition_mean'] = _rational(condition_mean)
    if not n or not nc:
        result['reason'] = 'no_scope_cases' if not n else 'no_conditioned_cases'
        return result
    result.update(status='DESCRIPTIVE_ONLY', reason='reference_calculation_complete',
                  effect=_rational(effect))
    return result
