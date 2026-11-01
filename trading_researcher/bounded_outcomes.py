"""D089 descriptive-only case/contrast enclosures; no scalar inference bridge."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction

from .bounded_math import BoundedReferenceEngine, Enclosure
from .expressions import ExpressionGap, gap
from .outcomes import _case, _read_rational, _validate, reference_contrast, PENDING, STATES


REQUEST = 'bounded-reference-case-request/1'
CASES = 'bounded-reference-cases/1'
CONTRAST = 'bounded-reference-contrast/1'
MAX_WIDTH = Fraction(1, 10**12)


def legacy_request(request):
    if type(request) is not dict or request.get('schema') != REQUEST:
        gap('LANGUAGE_GAP', 'Expected the optional bounded outcome request version')
    if request.get('outcome_scale') != 'quantity':
        gap('TYPE_GAP', 'The bounded outcome profile supports quantities only')
    return {**request, 'schema': 'reference-case-request/1'}


def lookback(node):
    children = max((lookback(child) for child in node.children), default=0)
    if node.op == 'lag':
        return children + 900 * node.parameter
    if node.op in ('trailing_mean', 'trailing_median'):
        return children + 900 * (node.parameter - 1)
    return children


def _encode(value):
    if value is None:
        return None
    enclosure = Enclosure.of(value)
    if enclosure.upper - enclosure.lower > MAX_WIDTH:
        gap('NUMERICAL_GAP', 'Outcome enclosure exceeds the approved 1e-12 basis-point width')
    return enclosure.public()


def _decode(value):
    if type(value) is not dict or set(value) != {'schema', 'lower', 'upper'} or value['schema'] != 'bounded-real/1':
        gap('EVALUATION_GAP', 'Observed bounded outcome requires an explicit rational enclosure')
    enclosure = Enclosure(_read_rational(value['lower']), _read_rational(value['upper']))
    if enclosure.upper - enclosure.lower > MAX_WIDTH:
        gap('NUMERICAL_GAP', 'Observed outcome exceeds the approved enclosure width')
    return enclosure


def materialize_bounded(request, catalog, rows, *, _engine_type=BoundedReferenceEngine,
                        _require_container_rows=True):
    start, end, as_of, first, expected, instruments = _validate(legacy_request(request))
    decision_engine = _engine_type(catalog, rows)
    outcome_engine = _engine_type(catalog, rows, allow_log=True)
    scope = decision_engine._program_node(request['scope_program'])
    condition = decision_engine._program_node(request['condition_program'])
    outcome = outcome_engine._program_node(request['outcome_program'])
    if scope.kind != 'boolean' or condition.kind != 'boolean':
        gap('TYPE_GAP', 'Scope and condition must be Boolean programs')
    if outcome.kind != 'real' or outcome.unit != 'basis_points':
        gap('TYPE_GAP', 'Initial bounded outcome profile requires explicit basis_points units')
    # Scope/condition were compiled by the capability-restricted decision engine.
    # Their node graphs contain no logarithms; the common owned row map is equal.
    remaining, cases, resource_reason = [request['max_steps']], [], None
    for when in range(first, end, 900):
        for instrument in instruments:
            try:
                case = _case(outcome_engine, scope, condition, outcome, when, instrument,
                    start, end, as_of, request['horizon_bars'], remaining, lookback(outcome), serialize=_encode,
                    require_container_rows=_require_container_rows)
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
    return {'schema': CASES, 'request': deepcopy(request), 'outcome_unit': outcome.unit,
        'cases': cases, 'expected_case_count': expected, 'processed_case_count': len(cases),
        'state_counts': {state: counts[state] for state in sorted(STATES)}, 'processing_complete': complete,
        'outcomes_complete': complete and not any(counts[state] for state in PENDING),
        'review_required': bool(counts['REVIEW_REQUIRED']), 'status': 'PROCESSED' if complete else 'RESOURCE_STOP',
        'resource_reason': resource_reason,
        'primitive_steps': min(request['max_steps'], request['max_steps'] - remaining[0]),
        'numerical_contract': 'bounded-math/1.0', 'scientific_readiness': False}


def bounded_contrast(report):
    """Conservative interval arithmetic preserves the complete shared-scope mean."""
    if type(report) is not dict or report.get('schema') != CASES:
        gap('EVALUATION_GAP', 'Expected a bounded reference case report')
    if report.get('outcome_unit') != 'basis_points' or report.get('numerical_contract') != 'bounded-math/1.0':
        gap('EVALUATION_GAP', 'Bounded report units or numerical contract differ')
    if type(report.get('cases')) is not list:
        gap('EVALUATION_GAP', 'Expected a bounded case list')
    projections = []
    for side in ('lower', 'upper'):
        projected = {**report, 'schema': 'reference-cases/1', 'request': legacy_request(report.get('request'))}
        projected['cases'] = []
        for case in report['cases']:
            if type(case) is not dict:
                gap('EVALUATION_GAP', 'Expected a bounded case object')
            value = case.get('outcome')
            if value is not None:
                _decode(value)
                value = value[side]
            projected['cases'].append({**case, 'outcome': value})
        # Reuse the mature strict universe/order/missingness/trace validators.
        projections.append(reference_contrast(projected))
    lower, upper = projections
    if any(lower[key] != upper[key] for key in ('status', 'reason', 'scope_count', 'condition_count')):
        gap('NUMERICAL_GAP', 'Enclosure endpoint computations disagree on eligibility')
    result = {**lower, 'schema': CONTRAST, 'numerical_contract': 'bounded-math/1.0',
        'scope_mean': None, 'condition_mean': None, 'effect': None}
    for field in ('scope_mean', 'condition_mean'):
        if lower[field] is not None and upper[field] is not None:
            result[field] = Enclosure(_read_rational(lower[field]), _read_rational(upper[field])).public()
    if lower['status'] == 'DESCRIPTIVE_ONLY':
        # Conservative despite overlap: no independent-sample or midpoint claim.
        result['effect'] = Enclosure(
            _read_rational(lower['condition_mean']) - _read_rational(upper['scope_mean']),
            _read_rational(upper['condition_mean']) - _read_rational(lower['scope_mean'])).public()
        result['reason'] = 'bounded_reference_calculation_complete'
    return result
