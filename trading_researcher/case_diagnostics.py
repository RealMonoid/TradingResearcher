"""Add neutral cause evidence without changing the bounded numerical calculation."""
from collections import Counter
from copy import deepcopy
import hashlib

from .bounded_math import BoundedReferenceEngine
from .bounded_outcomes import CASES, _encode, bounded_contrast, lookback
from .codec import canonical, digest
from .expressions import ExpressionGap, gap
from .outcomes import _instant, _Trace


SCHEMA = 'diagnostic-bounded-reference-cases/1'
SUMMARY = 'case-diagnostics/1'
CATEGORIES = ('boundary_censoring', 'absent_row', 'missing_warmup', 'missing_value',
              'missing_feature', 'unavailable_data', 'numeric_domain', 'condition_unknown',
              'input_before_universe')
MAX_EVENTS = 2048
MAX_CASE_BYTES = 512 * 1024


def _stream_hash(cases):
    checksum = hashlib.sha256()
    for case in cases:
        checksum.update((canonical(case) + '\n').encode('utf-8'))
    return checksum.hexdigest()


def _base_hash(report, stream_hash):
    return digest({'report': {k: v for k, v in report.items() if k != 'cases'},
                   'case_stream_sha256': stream_hash})


def base_projection(report):
    if type(report) is not dict or report.get('schema') != SCHEMA:
        gap('EVALUATION_GAP', 'Expected a diagnostic bounded report')
    base = {k: deepcopy(v) for k, v in report.items()
            if k not in ('diagnostics', 'base_report_hash', 'base_case_stream_sha256', 'cases')}
    base['schema'] = CASES
    base['cases'] = [{k: deepcopy(v) for k, v in case.items() if k != 'diagnostics'}
                     for case in report['cases']]
    stream_hash = _stream_hash(base['cases'])
    if (stream_hash != report.get('base_case_stream_sha256')
            or _base_hash(base, stream_hash) != report.get('base_report_hash')):
        gap('EVALUATION_GAP', 'Diagnostic projection differs from its bound base report')
    return base


def _guard(expression):
    """Recognize syntax, never infer that the selected predicate means validity."""
    path = '/expression'
    while expression.get('op') == 'lag':
        path += '/arg'
        expression = expression['arg']
    try:
        left, right = expression['left'], expression['right']
        first, second = left['left'], right['left']['arg']
        null = right['right']
        if (expression['op'] == 'or' and left['op'] == right['op'] == 'and'
                and right['left']['op'] == 'not' and digest(first) == digest(second)
                and null == {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': None}):
            return path + '/left/left'
    except (KeyError, TypeError):
        pass
    return None


class _Observation:
    def __init__(self, start, guard_path):
        self.start = start
        self.categories = set()
        self.events = {}
        self.node = None
        self.original_trace = None
        self.guard = {'recognized': guard_path is not None, 'path': guard_path,
                      'evaluated': False, 'value': None}

    def __call__(self, when, available, reason):
        program, path, op = self.node
        if self.original_trace is not None and program == 'outcome_program':
            self.original_trace(when, available, reason)
        if when < self.start:
            self.categories.add('input_before_universe')
        if reason == 'missing_observation':
            self.categories.add('missing_warmup' if when < self.start else 'absent_row')
        elif reason == 'missing_feature_value':
            self.categories.add('missing_feature')
        elif reason == 'missing_value' and op == 'feature':
            self.categories.add('missing_value')
        elif reason == 'not_yet_available':
            self.categories.add('unavailable_data')
        elif reason in ('division_by_zero', 'log_domain'):
            self.categories.add('numeric_domain')
        # Available/observation events carry no failure cause. Retain those that
        # demonstrate an earlier-than-universe dependency, plus all other events.
        if reason in ('available', 'observation') and when >= self.start:
            return
        key = (program, path, when, available, reason)
        self.events[key] = {'program': program, 'path': path, 'observation_time': when,
                            'available_at': available, 'reason': reason}
        if len(self.events) > MAX_EVENTS:
            gap('RESOURCE_GAP', 'Diagnostic case exceeds its retained-event limit')

    def public(self):
        return {'reason_categories': sorted(self.categories),
                'events': sorted(self.events.values(), key=canonical),
                'validity_guard': deepcopy(self.guard)}


class _Engine(BoundedReferenceEngine):
    def __init__(self, catalog, rows, *, allow_log=False):
        super().__init__(catalog, rows, allow_log=allow_log)
        self.paths = {}

    def register(self, program, name):
        node = self._program_node(program)
        def visit(current, expression, path):
            self.paths[id(current)] = (name, path, current.op)
            keys = [key for key in ('arg', 'left', 'right') if key in expression]
            for child, key in zip(current.children, keys):
                visit(child, expression[key], path + '/' + key)
        visit(node, program['expression'], '/expression')
        return node

    def _calculate(self, node, when, instrument, cutoff, remaining, trace=None):
        previous = trace.node
        trace.node = self.paths[id(node)]
        try:
            value = super()._calculate(node, when, instrument, cutoff, remaining, trace)
            name, path, _ = trace.node
            if name == 'condition_program' and path == trace.guard['path']:
                trace.guard.update(evaluated=True, value=value.value)
            return value
        finally:
            trace.node = previous


def add_diagnostics(report, catalog, rows, max_steps, *, _engine_type=_Engine,
                    _require_container_rows=True):
    """Observe the completed base prefix; resource stops never alter its cases."""
    if type(report) is not dict or report.get('schema') != CASES:
        gap('EVALUATION_GAP', 'Expected a base bounded report')
    if type(max_steps) is not int or not 0 <= max_steps <= 10000000:
        gap('RESOURCE_GAP', 'An explicit remaining diagnostic step budget is required')
    bounded_contrast(report)  # Reuse existing strict report/eligibility validation.
    request = report['request']
    start, end = (_instant(request['universe'][key]) for key in ('start', 'end'))
    as_of = _instant(request['as_of'])
    engine = _engine_type(catalog, rows)
    outcome_engine = _engine_type(catalog, rows, allow_log=True)
    scope = engine.register(request['scope_program'], 'scope_program')
    condition = engine.register(request['condition_program'], 'condition_program')
    outcome = outcome_engine.register(request['outcome_program'], 'outcome_program')
    guard_path = _guard(request['condition_program']['expression'])
    stream_hash = _stream_hash(report['cases'])
    result = deepcopy(report)
    result.update(schema=SCHEMA, base_case_stream_sha256=stream_hash,
                  base_report_hash=_base_hash(report, stream_hash))
    for case in result['cases']:
        case['diagnostics'] = None
    remaining, processed, reason = [max_steps], 0, None
    counts = Counter(dict.fromkeys(CATEGORIES, 0))
    guard_counts = Counter(dict.fromkeys(('true', 'false', 'unknown', 'unrecognized', 'not_evaluated'), 0))
    for original, case in zip(report['cases'], result['cases']):
        observation = _Observation(start, guard_path)
        when, instrument = case['decision_time'], case['instrument']
        try:
            # Even a metadata-only row must fit the shared diagnostic cap.
            remaining[0] -= 1
            if remaining[0] < 0:
                gap('RESOURCE_GAP', 'Diagnostic replay exhausted its primitive-step budget')
            if case['status'] == 'PARTITION_BOUNDARY':
                observation.categories.add('boundary_censoring')
            if when <= as_of:
                if _require_container_rows and (when, instrument) not in engine.lookup:
                    if (case['status'] != 'DATA_GAP' or case['reason'] != 'missing_decision_observation'
                            or any(case[key] is not None for key in ('scope', 'condition', 'outcome', 'trace'))):
                        gap('EVALUATION_GAP', 'Diagnostic decision observation differs from base calculation')
                    observation.node = ('scope_program', '/expression', 'case')
                    observation(when, None, 'missing_observation')
                else:
                    if case['reason'] == 'missing_decision_observation':
                        gap('EVALUATION_GAP', 'Diagnostic decision observation differs from base calculation')
                    observed = engine._calculate(scope, when, instrument, when, remaining, observation)
                    if observed.value != case['scope']:
                        gap('EVALUATION_GAP', 'Diagnostic scope differs from base calculation')
                    if observed.value is True:
                        observed = engine._calculate(condition, when, instrument, when, remaining, observation)
                        if observed.value != case['condition']:
                            gap('EVALUATION_GAP', 'Diagnostic condition differs from base calculation')
                        if observed.value is None:
                            observation.categories.add('condition_unknown')
                        anchor = case['outcome_anchor']
                        if case['trace'] is not None:
                            observation.original_trace = _Trace(when, start, end, anchor - lookback(outcome))
                            observed = outcome_engine._calculate(outcome, anchor, instrument,
                                min(as_of, end - 1), remaining, observation)
                            if _encode(observed.value) != case['outcome']:
                                gap('EVALUATION_GAP', 'Diagnostic outcome differs from base calculation')
                            if observation.original_trace.public() != case['trace']:
                                gap('EVALUATION_GAP', 'Diagnostic outcome trace differs from base calculation')
                        elif case['reason'] == 'missing_exact_outcome_observation':
                            if (anchor, instrument) in engine.lookup:
                                gap('EVALUATION_GAP', 'Diagnostic outcome observation differs from base calculation')
                            observation.node = ('outcome_program', '/expression', 'case')
                            observation(anchor, None, 'missing_observation')
            diagnostic = observation.public()
            if len(canonical({**original, 'diagnostics': diagnostic}).encode()) > MAX_CASE_BYTES:
                gap('RESOURCE_GAP', 'Diagnostic case exceeds its encoded-size limit')
        except ExpressionGap as exc:
            if exc.code != 'RESOURCE_GAP':
                raise
            reason = str(exc)
            break
        case['diagnostics'] = diagnostic
        counts.update(diagnostic['reason_categories'])
        guard = diagnostic['validity_guard']
        key = ('unrecognized' if not guard['recognized'] else 'not_evaluated' if not guard['evaluated']
               else 'unknown' if guard['value'] is None else 'true' if guard['value'] is True else 'false')
        guard_counts[key] += 1
        processed += 1
    complete = processed == report['expected_case_count'] and report['processing_complete'] and reason is None
    result['diagnostics'] = {'schema': SUMMARY, 'status': 'COMPLETE' if complete else 'RESOURCE_STOP',
        'processing_complete': complete, 'expected_cases': report['expected_case_count'],
        'processed_cases': processed, 'primitive_steps': min(max_steps, max_steps - remaining[0]),
        'reason': reason or (None if complete else 'Base computation is incomplete'),
        'reason_counts': dict(counts), 'guard_counts': dict(guard_counts),
        'categories_overlap': True, 'invalidity_interpretation': 'REQUIRES_INDEPENDENT_MEANING_REVIEW',
        'limits': {'remaining_steps': max_steps, 'events_per_case': MAX_EVENTS, 'case_bytes': MAX_CASE_BYTES},
        'scientific_readiness': False}
    return result
