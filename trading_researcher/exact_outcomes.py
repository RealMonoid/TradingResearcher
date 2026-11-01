"""D097 descriptive quantity cases; shared legacy validators, separate versions."""
from collections import Counter
from copy import deepcopy

from .bounded_outcomes import (CASES as BOUNDED_CASES, REQUEST as BOUNDED_REQUEST,
                               _encode, bounded_contrast, legacy_request)
from .case_diagnostics import (_Engine, _Observation, _base_hash, _guard, _stream_hash,
                               CATEGORIES, MAX_CASE_BYTES, MAX_EVENTS)
from .codec import canonical
from .exact_compositions import CONTRACT, ExactCompositionEngine
from .expressions import ExpressionGap, gap
from .outcomes import PENDING, STATES, _Trace, _case, _instant, _validate

REQUEST = 'exact-composition-case-request/1'
CASES = 'exact-composition-cases/1'
DIAGNOSTICS = 'diagnostic-exact-composition-cases/1'
CONTRAST = 'exact-composition-contrast/1'
EVALUATION = 'required-inputs/1'


def _request_projection(request):
    if type(request) is not dict or request.get('schema') != REQUEST:
        gap('LANGUAGE_GAP', 'Expected the explicit exact-composition case request')
    return {**request, 'schema': BOUNDED_REQUEST}


def lookback(node):
    children = max((lookback(child) for child in node.children), default=0)
    if node.op == 'lag':
        return children + 900 * node.parameter
    if node.op in ('trailing_mean', 'trailing_median', 'trailing_product', 'trailing_all'):
        return children + 900 * (node.parameter - 1)
    return children


def materialize_exact(request, catalog, rows):
    start, end, as_of, first, expected, instruments = _validate(legacy_request(_request_projection(request)))
    decision_engine = ExactCompositionEngine(catalog, rows)
    outcome_engine = ExactCompositionEngine(catalog, rows, allow_log=True)
    scope = decision_engine._program_node(request['scope_program'])
    condition = decision_engine._program_node(request['condition_program'])
    outcome = outcome_engine._program_node(request['outcome_program'])
    if scope.kind != 'boolean' or condition.kind != 'boolean':
        gap('TYPE_GAP', 'Scope and condition must be Boolean programs')
    if outcome.kind != 'real' or outcome.unit != 'basis_points':
        gap('TYPE_GAP', 'The existing bounded quantity profile requires basis_points units')
    if not outcome_engine.describe(request['outcome_program'])['feature_refs']:
        gap('LANGUAGE_GAP', 'The required-input profile needs an actual raw outcome feature')
    remaining, cases, reason = [request['max_steps']], [], None
    for when in range(first, end, 900):
        for instrument in instruments:
            try:
                case = _case(outcome_engine, scope, condition, outcome, when, instrument,
                    start, end, as_of, request['horizon_bars'], remaining, lookback(outcome),
                    serialize=_encode, require_container_rows=False)
            except ExpressionGap as error:
                if error.code != 'RESOURCE_GAP':
                    raise
                reason = str(error)
                break
            cases.append(case)
        if reason is not None:
            break
    counts = Counter(case['status'] for case in cases)
    complete = len(cases) == expected and reason is None
    return {'schema': CASES, 'request': deepcopy(request), 'outcome_unit': outcome.unit,
        'cases': cases, 'expected_case_count': expected, 'processed_case_count': len(cases),
        'state_counts': {state: counts[state] for state in sorted(STATES)},
        'processing_complete': complete, 'outcomes_complete': complete and not any(counts[state] for state in PENDING),
        'review_required': bool(counts['REVIEW_REQUIRED']), 'status': 'PROCESSED' if complete else 'RESOURCE_STOP',
        'resource_reason': reason, 'primitive_steps': min(request['max_steps'], request['max_steps'] - remaining[0]),
        'numerical_contract': 'bounded-math/1.0', 'evaluation_contract': EVALUATION,
        'expression_contract': CONTRACT, 'scientific_readiness': False}


def _projection(report):
    if (type(report) is not dict or report.get('schema') != CASES
            or report.get('evaluation_contract') != EVALUATION
            or report.get('expression_contract') != CONTRACT or report.get('scientific_readiness') is not False):
        gap('EVALUATION_GAP', 'Expected the exact versioned uncalibrated composition report')
    request = _request_projection(report.get('request'))
    if (type(report.get('primitive_steps')) is not int or type(request.get('max_steps')) is not int
            or not 0 <= report['primitive_steps'] <= request['max_steps'] <= 10000000):
        gap('EVALUATION_GAP', 'Base primitive usage must fit its declared shared budget')
    return {**report, 'schema': BOUNDED_CASES, 'request': request}


def exact_contrast(report):
    result = bounded_contrast(_projection(report))
    if not report['processing_complete']:
        result = {**result, 'status': 'RESOURCE_STOP'}
    return {**result, 'schema': CONTRAST, 'evaluation_contract': EVALUATION,
            'expression_contract': CONTRACT}


class _DiagnosticEngine(_Engine, ExactCompositionEngine):
    def _calculate(self, node, when, instrument, cutoff, remaining, trace=None):
        # The shared case kernel supplies no trace for decisions and its own
        # maturity trace for outcomes. Observe both without changing that kernel.
        if trace is None:
            trace = self.observation
        elif isinstance(trace, _Trace):
            self.observation.original_trace = trace
            trace = self.observation
        return super()._calculate(node, when, instrument, cutoff, remaining, trace)


def add_exact_diagnostics(report, catalog, rows, max_steps):
    """Same required-input observation protocol with AST4-aware lookback."""
    _projection(report)
    if type(max_steps) is not int or not 0 <= max_steps <= 10000000:
        gap('RESOURCE_GAP', 'An explicit remaining diagnostic step budget is required')
    exact_contrast(report)
    request = report['request']
    if max_steps > request['max_steps'] - report['primitive_steps']:
        gap('RESOURCE_GAP', 'Diagnostic allocation exceeds the remaining shared primitive budget')
    start, end = (_instant(request['universe'][key]) for key in ('start', 'end'))
    as_of = _instant(request['as_of'])
    engine = _DiagnosticEngine(catalog, rows)
    outcome_engine = _DiagnosticEngine(catalog, rows, allow_log=True)
    scope = engine.register(request['scope_program'], 'scope_program')
    condition = engine.register(request['condition_program'], 'condition_program')
    outcome = outcome_engine.register(request['outcome_program'], 'outcome_program')
    # Decision graphs were compiled without outcome capability. Reuse those
    # exact nodes with the same owned row map, as the numerical materializer does.
    outcome_engine.paths.update(engine.paths)
    guard_path = _guard(request['condition_program']['expression'])
    stream_hash = _stream_hash(report['cases'])
    result = deepcopy(report)
    result.update(schema=DIAGNOSTICS, base_case_stream_sha256=stream_hash,
                  base_report_hash=_base_hash(report, stream_hash))
    for case in result['cases']:
        case['diagnostics'] = None
    remaining, processed, reason = [max_steps], 0, None
    counts = Counter(dict.fromkeys(CATEGORIES, 0))
    guard_counts = Counter(dict.fromkeys(('true', 'false', 'unknown', 'unrecognized', 'not_evaluated'), 0))
    for original, case in zip(report['cases'], result['cases']):
        observation = _Observation(start, guard_path)
        outcome_engine.observation = observation
        when, instrument = case['decision_time'], case['instrument']
        try:
            remaining[0] -= 1
            if remaining[0] < 0:
                gap('RESOURCE_GAP', 'Diagnostic replay exhausted its primitive-step budget')
            observed = _case(outcome_engine, scope, condition, outcome, when, instrument,
                start, end, as_of, request['horizon_bars'], remaining, lookback(outcome),
                serialize=_encode, require_container_rows=False)
            if observed != original:
                gap('EVALUATION_GAP', 'Diagnostic replay differs from the complete base case')
            if observed['status'] == 'PARTITION_BOUNDARY':
                observation.categories.add('boundary_censoring')
            if observed['scope'] is True and observed['condition'] is None:
                observation.categories.add('condition_unknown')
            diagnostic = observation.public()
            if len(canonical({**original, 'diagnostics': diagnostic}).encode()) > MAX_CASE_BYTES:
                gap('RESOURCE_GAP', 'Diagnostic case exceeds its encoded-size limit')
        except ExpressionGap as error:
            if error.code != 'RESOURCE_GAP':
                raise
            reason = str(error)
            break
        case['diagnostics'] = diagnostic
        counts.update(diagnostic['reason_categories'])
        guard = diagnostic['validity_guard']
        key = ('unrecognized' if not guard['recognized'] else 'not_evaluated' if not guard['evaluated']
               else 'unknown' if guard['value'] is None else 'true' if guard['value'] is True else 'false')
        guard_counts[key] += 1
        processed += 1
    complete = processed == report['expected_case_count'] and report['processing_complete'] and reason is None
    result['diagnostics'] = {'schema': 'case-diagnostics/2', 'status': 'COMPLETE' if complete else 'RESOURCE_STOP',
        'processing_complete': complete, 'expected_cases': report['expected_case_count'],
        'processed_cases': processed, 'primitive_steps': min(max_steps, max_steps - remaining[0]),
        'reason': reason or (None if complete else 'Base computation is incomplete'),
        'reason_counts': dict(counts), 'guard_counts': dict(guard_counts),
        'categories_overlap': True, 'invalidity_interpretation': 'REQUIRES_INDEPENDENT_MEANING_REVIEW',
        'limits': {'remaining_steps': max_steps, 'events_per_case': MAX_EVENTS, 'case_bytes': MAX_CASE_BYTES},
        'scientific_readiness': False}
    return result


def exact_base_projection(report):
    if (type(report) is not dict or report.get('schema') != DIAGNOSTICS
            or report.get('evaluation_contract') != EVALUATION or report.get('expression_contract') != CONTRACT
            or type(report.get('diagnostics')) is not dict
            or report['diagnostics'].get('schema') != 'case-diagnostics/2'
            or type(report.get('cases')) is not list or any(type(case) is not dict for case in report['cases'])):
        gap('EVALUATION_GAP', 'Expected the exact-composition diagnostic version')
    base = {key: deepcopy(value) for key, value in report.items()
            if key not in ('diagnostics', 'base_report_hash', 'base_case_stream_sha256', 'cases')}
    base['schema'] = CASES
    base['cases'] = [{key: deepcopy(value) for key, value in case.items() if key != 'diagnostics'}
                     for case in report['cases']]
    checksum = _stream_hash(base['cases'])
    if (checksum != report.get('base_case_stream_sha256')
            or _base_hash(base, checksum) != report.get('base_report_hash')):
        gap('EVALUATION_GAP', 'Exact diagnostic projection changed its base')
    _projection(base)
    return base
