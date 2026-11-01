"""D094 fixed-pair reference semantics, opt-in and descriptive only.

No synthetic market instrument is constructed. Source definitions supplied here
are checked for exact semantics; their certification/authorization is a separate
host prerequisite. This pure calculator cannot issue that prerequisite.
"""
from collections import Counter
from copy import deepcopy
from fractions import Fraction

from .bounded_math import BoundedReferenceEngine, Enclosure
from .bounded_outcomes import _decode, _encode, lookback
from .codec import canonical, digest
from .expressions import ExpressionGap, Node, REFERENCE, gap, scalar
from .outcomes import _instant, PENDING, STATES


PAIR = ('BTCUSDT', 'ETHUSDT')
CONTRACT = 'paired-development/1.0'
PROGRAM = 'research-ast/3'
REQUEST = 'paired-reference-case-request/1'
CASES = 'paired-reference-cases/1'
CONTRAST = 'paired-reference-contrast/1'
PROFILE = 'paired-reference-computation/1'
MAX_EVENTS = 1024


def validate_pair(pair):
    if type(pair) is not list or pair != list(PAIR):
        gap('DATA_GAP', 'Declare exactly the canonical fixed BTCUSDT/ETHUSDT pair')
    return tuple(pair)


def expected_definitions():
    """Exact adopted raw meanings, independent of model-proposed metadata."""
    columns = {'open': 1, 'high': 2, 'low': 3, 'close': 4, 'volume': 5,
               'quote_volume': 7, 'trades': 8, 'taker_base_volume': 9, 'taker_quote_volume': 10}
    result = {}
    for instrument in PAIR:
        base = instrument.removesuffix('USDT')
        for name, column in columns.items():
            price = name in ('open', 'high', 'low', 'close')
            unit = 'USDT/'+base if price else ('count' if name == 'trades' else
                    'USDT' if name in ('quote_volume', 'taker_quote_volume') else base)
            ref = instrument+'.'+name+'@binance-spot-15m-v1'
            result[ref] = {'schema': 'raw-binance-feature-definition/1',
                'feature_ref': ref, 'instrument': instrument, 'source_field': name,
                'csv_column_index': column, 'type': 'real', 'unit': unit,
                'source_scalar': 'positive_decimal' if price else
                    'nonnegative_integer' if name == 'trades' else 'nonnegative_decimal',
                'transformation': 'EXACT_DECIMAL_FIELD_PROJECTION',
                'time': {'grid_seconds': 900, 'row_anchor': 'EXPECTED_EXCLUSIVE_BAR_END',
                    'source_open_column': 0, 'source_close_column': 6,
                    'timestamp_unit_rule': 'milliseconds_before_2025_microseconds_from_2025'},
                'missingness': {'invalid_keyed_bar': 'NULL_ALL_SYMBOL_FIELDS',
                    'absent_bar': 'NO_ROW', 'other_instrument_fields': 'ABSENT'},
                'availability': {'basis': 'assumed', 'rule': 'row_time + delay_seconds',
                    'parameter': 'EXPLICIT_NONNEGATIVE_INTEGER_SECONDS_NO_DEFAULT',
                    'historical_publication_time': None}, 'fitted_state': None}
    return result


class _TraceAdapter:
    def __init__(self, callback, pair):
        self.callback, self.pair = callback, pair

    def __call__(self, when, available, reason, instrument=None, ref=None):
        self.callback({'observation_time': when, 'available_at': available, 'reason': reason,
                       'instrument': instrument, 'feature_ref': ref, 'pair': list(self.pair)})


class PairedReferenceEngine(BoundedReferenceEngine):
    def __init__(self, catalog, rows, feature_definitions, *, pair, allow_log=False):
        self.pair = validate_pair(pair)
        if type(allow_log) is not bool or type(catalog) is not dict or len(catalog) > 256:
            gap('FEATURE_GAP', 'Exact bounded catalog and outcome capability required')
        if type(feature_definitions) is not list or len(feature_definitions) > 256:
            gap('FEATURE_GAP', 'Exact retained raw feature definitions required')
        fixed, definitions = expected_definitions(), {}
        for item in feature_definitions:
            if type(item) is not dict or type(item.get('feature_ref')) is not str:
                gap('FEATURE_GAP', 'Malformed raw definition')
            ref = item['feature_ref']
            if ref in definitions or ref not in fixed or canonical(item) != canonical(fixed[ref]):
                gap('FEATURE_GAP', 'Duplicate, altered or unadopted raw definition')
            definitions[ref] = deepcopy(item)
        for ref, spec in catalog.items():
            if (type(ref) is not str or not REFERENCE.fullmatch(ref) or ref not in definitions
                    or type(spec) is not dict or set(spec) != {'type', 'unit'}
                    or spec != {key: definitions[ref][key] for key in ('type', 'unit')}):
                gap('FEATURE_GAP', 'Catalog must match exact member-specific raw definitions')
        if type(rows) is not list or len(rows) > 100000:
            gap('DATA_GAP', 'A bounded row snapshot is required; an empty pair grid is allowed')
        self.catalog, self.definitions = deepcopy(catalog), definitions
        self.rows, self.lookup = [], {}
        previous = None
        for row in rows:
            if (type(row) is not dict or set(row) != {'time', 'instrument', 'features'}
                    or type(row['time']) is not int or row['time'] < 0 or row['time'] % 900
                    or row['instrument'] not in self.pair or type(row['features']) is not dict):
                gap('DATA_GAP', 'Rows require an exact UTC grid, declared member and feature map')
            key = row['time'], row['instrument']
            if previous is not None and key <= previous:
                gap('DATA_GAP', 'Rows must have unique increasing time/member keys')
            previous = key
            samples = {}
            for ref, sample in row['features'].items():
                if ref not in catalog or definitions[ref]['instrument'] != row['instrument']:
                    gap('FEATURE_GAP', 'A raw sample cannot impersonate the other member')
                if (type(sample) is not dict or set(sample) != {'value', 'available_at'}
                        or type(sample['available_at']) is not int or sample['available_at'] < row['time']):
                    gap('DATA_GAP', 'Exact raw value and per-member availability required')
                spec = catalog[ref]
                value = scalar(spec['type'], spec['unit'], sample['value'], 'DATA_GAP')
                domain = definitions[ref]['source_scalar']
                if value is not None and (value < 0 or (domain == 'positive_decimal' and value <= 0)
                        or (domain == 'nonnegative_integer' and value.denominator != 1)):
                    gap('DATA_GAP', 'Canonical source contradicts its certified raw domain')
                samples[ref] = value, sample['available_at']
            self.rows.append(key)
            self.lookup[key] = samples
        self.allow_log, self._new_operators = allow_log, False
        self.window = None

    def _program_node(self, program):
        if (type(program) is not dict or set(program) != {'schema', 'catalog_hash', 'expression'}
                or program['schema'] != PROGRAM):
            gap('LANGUAGE_GAP', 'Paired calculation requires explicit research-ast/3')
        if program['catalog_hash'] != digest(self.catalog):
            gap('FEATURE_GAP', 'Program must bind the exact catalog')
        self._new_operators = True
        try:
            return self._compile(program['expression'], 0, [0])
        finally:
            self._new_operators = False

    def _compile(self, expression, depth, count):
        if type(expression) is dict and expression.get('op') == 'feature':
            gap('LANGUAGE_GAP', 'Paired programs cannot use an implicit instrument')
        if type(expression) is not dict or expression.get('op') != 'feature_at':
            return super()._compile(expression, depth, count)
        count[0] += 1
        if depth >= 32 or count[0] > 256:
            gap('RESOURCE_GAP', 'Expression exceeds its fixed node/depth limit')
        if set(expression) != {'op', 'instrument', 'ref'}:
            gap('LANGUAGE_GAP', 'A fixed selector requires exactly instrument and versioned ref')
        member, ref = expression['instrument'], expression['ref']
        if (type(member) is not str or member not in self.pair or type(ref) is not str
                or ref not in self.catalog or self.definitions[ref]['instrument'] != member):
            gap('FEATURE_GAP', 'Selector must match its exact declared certified member')
        spec = self.catalog[ref]
        return Node('feature_at', spec['type'], spec['unit'], parameter=(member, ref))

    def describe(self, program):
        node = self._program_node(program)
        references, parameters = set(), []
        def visit(expression, path):
            if expression['op'] == 'feature_at':
                references.add(expression['ref'])
            if expression['op'] == 'literal':
                parameters.append(path+'/value')
            if expression['op'] in ('lag', 'trailing_mean', 'trailing_median'):
                parameters.append(path+'/bars')
            for key in ('arg', 'left', 'right'):
                if key in expression:
                    visit(expression[key], path+'/'+key)
        visit(program['expression'], '/expression')
        return {'type': node.kind, 'unit': node.unit, 'feature_refs': sorted(references),
                'parameter_paths': parameters}

    def _requires_observation(self, node):
        return False

    def _traces_observation(self, node):
        return False

    def _calculate(self, node, when, instrument, cutoff, remaining, trace=None):
        if node.op != 'feature_at':
            return super()._calculate(node, when, instrument, cutoff, remaining, trace)
        remaining[0] -= 1
        if remaining[0] < 0:
            gap('RESOURCE_GAP', 'Expression exhausted its primitive-step budget')
        member, ref = node.parameter
        samples = self.lookup.get((when, member))
        if self.window is not None and not self.window[0] <= when < self.window[1]:
            samples = None
        value, available = None, None
        if samples is None:
            reason = 'missing_observation'
        elif ref not in samples:
            reason = 'missing_feature_value'
        else:
            value, available = samples[ref]
            reason = 'not_yet_available' if available > cutoff else 'missing_value' if value is None else 'available'
        if trace is not None:
            trace(when, available, reason, member, ref)
        return self._present(node, value) if reason == 'available' else self._missing(node, reason)

    def evaluate_at(self, program, when, cutoff, remaining=None, trace=None):
        if (type(when) is not int or when < 0 or when % 900
                or type(cutoff) is not int or cutoff < 0):
            gap('TEMPORAL_GAP', 'Explicit decision/anchor coordinate and cutoff required')
        if remaining is None:
            remaining = [1000000]
        if (type(remaining) is not list or len(remaining) != 1
                or type(remaining[0]) is not int or not 0 <= remaining[0] <= 10000000):
            gap('RESOURCE_GAP', 'Expected a bounded shared step counter')
        callback = _TraceAdapter(trace, self.pair) if trace is not None else None
        return self._calculate(self._program_node(program), when, None, cutoff, remaining, callback)


def validate_request(request):
    required = {'schema','candidate_ref','data_snapshot_ref','scope_program','condition_program',
                'outcome_program','outcome_scale','horizon_bars','universe','as_of','max_steps'}
    if type(request) is not dict or set(request) != required or request['schema'] != REQUEST:
        gap('LANGUAGE_GAP', 'Exact paired request required')
    for key in ('candidate_ref', 'data_snapshot_ref'):
        if type(request[key]) is not str or not request[key].strip() or len(request[key]) > 256:
            gap('DATA_GAP', 'Exact retained reference required')
    if (type(request['horizon_bars']) is not int or not 1 <= request['horizon_bars'] <= 1000000
            or type(request['max_steps']) is not int or not 1 <= request['max_steps'] <= 10000000):
        gap('RESOURCE_GAP', 'Bounded positive horizon and step budget required')
    if request['outcome_scale'] != 'quantity':
        gap('TYPE_GAP', 'Paired bounded quantities require the adopted basis_points profile')
    universe = request['universe']
    if type(universe) is not dict or set(universe) != {'start', 'end', 'pair'}:
        gap('DATA_GAP', 'Exact declared paired universe required')
    validate_pair(universe['pair'])
    start, end, as_of = (_instant(value) for value in (universe['start'], universe['end'], request['as_of']))
    if start < 0 or start % 900 or end % 900 or start >= end:
        gap('TEMPORAL_GAP', 'Paired universe requires a nonempty 900-second interval')
    expected = (end-start)//900
    if expected > 50000:
        gap('RESOURCE_GAP', 'Paired universe exceeds 100000 possible raw input rows')
    return start, end, as_of, expected


def _category(event, start):
    if event['feature_ref'] is None:
        return 'numeric_domain' if event['reason'] in ('division_by_zero', 'log_domain') else None
    if event['observation_time'] < start:
        return 'missing_warmup'
    return {'missing_observation':'absent_row','missing_feature_value':'missing_feature',
            'missing_value':'missing_value','not_yet_available':'unavailable_data'}.get(event['reason'])


def _neutral_categories(case):
    result = set()
    if case['scope'] is True and case['condition'] is None:
        result.add('condition_unknown')
    if case['status'] == 'PARTITION_BOUNDARY':
        result.add('boundary_censoring')
    return result


def _cross_counts(cases):
    result = {name:{'observed':0,'missing':0} for name in ('true','false','unknown')}
    for case in cases:
        if case['scope'] is True:
            name = 'unknown' if case['condition'] is None else 'true' if case['condition'] else 'false'
            result[name]['observed' if case['status']=='ELIGIBLE' else 'missing'] += 1
    return result


def _read_offsets(node, budget, offset=0):
    budget[0] -= 1
    if budget[0] < 0:
        gap('RESOURCE_GAP','Dependency closure exceeds the primitive-step envelope')
    if node.op == 'feature_at':
        return {(offset,*node.parameter)}
    if node.op == 'lag':
        return _read_offsets(node.children[0],budget,offset-node.parameter*900)
    if node.op in ('trailing_mean','trailing_median'):
        result = set()
        for index in range(node.parameter):
            result.update(_read_offsets(node.children[0],budget,offset-index*900))
            if len(result)>MAX_EVENTS:
                gap('RESOURCE_GAP','Dependency closure exceeds the retained-event bound')
        return result
    result = set()
    for child in node.children:
        result.update(_read_offsets(child,budget,offset))
    return result


def _case(engine, nodes, when, start, end, as_of, request, remaining):
    anchor = when+900*request['horizon_bars']
    case = {'pair':list(PAIR),'decision_time':when,'outcome_anchor':anchor,
            'scope':None,'condition':None,'outcome':None,'status':None,'reason':None,
            'label_information_interval':None,'dependencies':[],
            'diagnostics':{'reason_categories':[],'events':[]}}
    events = {}
    def calculate(name, coordinate, cutoff):
        def observe(event):
            event = {'program':name, **event}
            events[canonical(event)] = event
            if len(events) > MAX_EVENTS:
                gap('RESOURCE_GAP', 'Paired case exceeds its retained-event bound')
        return engine._calculate(nodes[name], coordinate, None, cutoff, remaining,
                                 _TraceAdapter(observe, PAIR))
    def finish(status, reason):
        case.update(status=status, reason=reason)
        ordered = sorted(events.values(), key=canonical)
        case['dependencies'] = [event for event in ordered if event['feature_ref'] is not None]
        case['diagnostics']['events'] = [event for event in ordered if _category(event, start) is not None]
        case['diagnostics']['reason_categories'] = sorted({_category(event,start)
            for event in ordered if _category(event,start) is not None} | _neutral_categories(case))
        return case
    if when > as_of:
        return finish('NOT_YET_OBSERVED','decision_in_future')
    scope = calculate('scope_program', when, when)
    case['scope'] = scope.value
    if scope.missing:
        return finish('SCOPE_UNKNOWN',scope.missing)
    if scope.value is False:
        return finish('SCOPE_FALSE','scope_false')
    condition = calculate('condition_program', when, when)
    case['condition'] = condition.value
    if anchor >= end:
        return finish('PARTITION_BOUNDARY','anchor_at_or_after_exclusive_end')
    if anchor > as_of:
        return finish('OUTCOME_PENDING','horizon_not_elapsed')
    outcome = calculate('outcome_program', anchor, min(anchor,as_of,end-1))
    if outcome.missing:
        pending = any(event['program']=='outcome_program' and event['reason']=='not_yet_available'
                      for event in events.values())
        return finish('OUTCOME_PENDING' if pending else 'OUTCOME_MISSING',outcome.missing)
    case['outcome'] = _encode(outcome.value)
    case['label_information_interval'] = {'start':when,'end':anchor}
    return finish('ELIGIBLE','paired_reference_inputs_observed')


def materialize_paired(request, catalog, rows, feature_definitions):
    start,end,as_of,expected = validate_request(request)
    decision = PairedReferenceEngine(catalog, rows, feature_definitions, pair=list(PAIR))
    outcome = PairedReferenceEngine(catalog, rows, feature_definitions, pair=list(PAIR),allow_log=True)
    if any(not start <= when < end for when,_ in decision.rows):
        gap('DATA_GAP', 'Paired inputs must stay inside the declared development universe')
    decision.window = outcome.window = start,end
    nodes = {name:(outcome if name=='outcome_program' else decision)._program_node(request[name])
             for name in ('scope_program','condition_program','outcome_program')}
    if nodes['scope_program'].kind != 'boolean' or nodes['condition_program'].kind != 'boolean':
        gap('TYPE_GAP', 'Scope and condition must be Boolean')
    if nodes['outcome_program'].kind != 'real' or nodes['outcome_program'].unit != 'basis_points':
        gap('TYPE_GAP', 'Paired quantity outcome must declare basis_points')
    if not outcome.describe(request['outcome_program'])['feature_refs']:
        gap('FEATURE_GAP', 'Paired outcome requires a declared raw dependency')
    remaining, cases, reason = [request['max_steps']], [], None
    for when in range(start,end,900):
        try:
            cases.append(_case(outcome,nodes,when,start,end,as_of,request,remaining))
        except ExpressionGap as error:
            if error.code != 'RESOURCE_GAP':
                raise
            reason = str(error)
            break
    counts=Counter(case['status'] for case in cases)
    reasons=Counter(category for case in cases for category in case['diagnostics']['reason_categories'])
    complete=len(cases)==expected and reason is None
    return {'schema':CASES,'evaluation_contract':CONTRACT,'numerical_contract':'bounded-math/1.0',
        'request':deepcopy(request),'pair':list(PAIR),'outcome_unit':'basis_points','cases':cases,
        'expected_case_count':expected,'processed_case_count':len(cases),
        'state_counts':{state:counts[state] for state in sorted(STATES)},
        'processing_complete':complete,'outcomes_complete':complete and not any(counts[state] for state in PENDING),
        'review_required':bool(counts['REVIEW_REQUIRED']), 'status':'PROCESSED' if complete else 'RESOURCE_STOP',
        'resource_reason':reason,'primitive_steps':min(request['max_steps'],request['max_steps']-remaining[0]),
        'diagnostics':{'schema':'paired-case-diagnostics/1','status':'COMPLETE' if complete else 'RESOURCE_STOP',
                       'reason_counts':dict(sorted(reasons.items())),
                       'condition_outcome_counts':_cross_counts(cases)},'scientific_readiness':False}


def paired_contrast(report):
    """Strict paired-grid validation and outward interval means, no inference."""
    required={'schema','evaluation_contract','numerical_contract','request','pair','outcome_unit','cases',
        'expected_case_count','processed_case_count','state_counts','processing_complete','outcomes_complete',
        'review_required','status','resource_reason','primitive_steps','diagnostics','scientific_readiness'}
    if (type(report) is not dict or set(report)!=required or report['schema']!=CASES
            or report['evaluation_contract']!=CONTRACT or report['numerical_contract']!='bounded-math/1.0'
            or report['outcome_unit']!='basis_points' or report['scientific_readiness'] is not False):
        gap('EVALUATION_GAP','Expected exact descriptive paired report')
    validate_pair(report['pair'])
    start,end,as_of,expected=validate_request(report['request'])
    cases=report['cases']
    if (type(cases) is not list or len(cases)>expected or type(report['expected_case_count']) is not int
            or report['expected_case_count']!=expected or type(report['processed_case_count']) is not int
            or report['processed_case_count']!=len(cases)):
        gap('EVALUATION_GAP','Paired grid counts differ')
    total,conditioned=Enclosure.of(Fraction(0)),Enclosure.of(Fraction(0))
    n,nc=0,0
    counts,reasons=Counter(),Counter()
    definitions=expected_definitions()
    # Validate syntax and raw units independently of the claimed read inventory.
    # Exact original catalog authorization is checked at the owned host boundary.
    catalog={ref:{key:item[key] for key in ('type','unit')} for ref,item in definitions.items()}
    static=PairedReferenceEngine(catalog,[],list(definitions.values()),pair=list(PAIR))
    offsets={}
    hashes=set()
    for name in ('scope_program','condition_program','outcome_program'):
        program=report['request'][name]
        if (type(program) is not dict or set(program)!={'schema','catalog_hash','expression'}
                or program['schema']!=PROGRAM or type(program['catalog_hash']) is not str
                or len(program['catalog_hash'])!=64
                or any(ch not in '0123456789abcdef' for ch in program['catalog_hash'])):
            gap('EVALUATION_GAP','Paired report has an invalid program envelope')
        hashes.add(program['catalog_hash'])
        static.allow_log=name=='outcome_program'
        static._new_operators=True
        node=static._compile(program['expression'],0,[0])
        if (name!='outcome_program' and node.kind!='boolean'
                or name=='outcome_program' and (node.kind,node.unit)!=('real','basis_points')):
            gap('TYPE_GAP','Paired report programs have incompatible types')
        # No processed case means a resource stop has no read inventory to prove.
        offsets[name]=_read_offsets(node,[10000000]) if cases else set()
    if len(hashes)!=1:
        gap('FEATURE_GAP','Paired programs do not bind one exact catalog')
    fields={'pair','decision_time','outcome_anchor','scope','condition','outcome','status','reason',
            'label_information_interval','dependencies','diagnostics'}
    for index,case in enumerate(cases):
        when=start+index*900
        anchor=when+report['request']['horizon_bars']*900
        if (type(case) is not dict or set(case)!=fields or case['pair']!=list(PAIR)
                or type(case['decision_time']) is not int or case['decision_time']!=when
                or type(case['outcome_anchor']) is not int or case['outcome_anchor']!=anchor
                or type(case['status']) is not str or case['status'] not in STATES or type(case['reason']) is not str
                or any(value is not None and type(value) is not bool for value in (case['scope'],case['condition']))):
            gap('EVALUATION_GAP','Paired cases must be the exact declared grid prefix')
        dependencies=case['dependencies']
        diagnostic=case['diagnostics']
        if (type(dependencies) is not list or len(dependencies)>MAX_EVENTS
                or type(diagnostic) is not dict or set(diagnostic)!={'reason_categories','events'}
                or type(diagnostic['events']) is not list or len(diagnostic['events'])>MAX_EVENTS):
            gap('EVALUATION_GAP','Malformed paired dependency trace')
        events=dependencies+diagnostic['events']
        seen=_neutral_categories(case)
        actual_reads=set()
        expected_reads=set()
        phases=[] if when>as_of else ['scope_program']
        if case['scope'] is True:
            phases.append('condition_program')
            if anchor<end and anchor<=as_of:
                phases.append('outcome_program')
        for phase in phases:
            coordinate=anchor if phase=='outcome_program' else when
            expected_reads.update((phase,coordinate+offset,member,ref) for offset,member,ref in offsets[phase])
        if dependencies!=sorted(dependencies,key=canonical) or diagnostic['events']!=sorted(diagnostic['events'],key=canonical):
            gap('EVALUATION_GAP','Paired events require canonical unique ordering')
        for event in events:
            if (type(event) is not dict or set(event)!={'program','observation_time','available_at','reason','instrument','feature_ref','pair'}
                    or event['pair']!=list(PAIR) or event['program'] not in ('scope_program','condition_program','outcome_program')
                    or type(event['observation_time']) is not int or event['observation_time']%900
                    or (event['available_at'] is not None and (type(event['available_at']) is not int or event['available_at']<0))):
                gap('EVALUATION_GAP','Malformed paired read identity')
            if event['feature_ref'] is not None:
                if type(event['feature_ref']) is not str or type(event['instrument']) is not str:
                    gap('EVALUATION_GAP','Raw read identity must be typed strings')
                definition=definitions.get(event['feature_ref'])
                if definition is None or definition['instrument']!=event['instrument']:
                    gap('EVALUATION_GAP','Read identity differs from its member definition')
            elif event['instrument'] is not None:
                gap('EVALUATION_GAP','An arithmetic event cannot assert a source member')
            if type(event['reason']) is not str or event['reason'] not in ('available','missing_observation','missing_feature_value','missing_value',
                                      'not_yet_available','division_by_zero','log_domain'):
                gap('EVALUATION_GAP','Unrecognized paired read reason')
            if event['program']!='outcome_program' and event['observation_time']>when:
                gap('EVALUATION_GAP','Decision read lies after its decision')
            if event['program']=='outcome_program' and event['observation_time']>anchor:
                gap('EVALUATION_GAP','Outcome read lies after its anchor')
            if event['reason']=='available':
                cutoff=when if event['program']!='outcome_program' else min(anchor,as_of,end-1)
                if (event['available_at'] is None or event['available_at']>cutoff
                        or not start<=event['observation_time']<end):
                    gap('EVALUATION_GAP','Read violates its exact availability/partition bound')
            category=_category(event,start)
            if category is not None:
                seen.add(category)
        for event in dependencies:
            if event['feature_ref'] is None:
                gap('EVALUATION_GAP','Raw dependencies cannot contain arithmetic-only events')
            key=(event['program'],event['observation_time'],event['instrument'],event['feature_ref'])
            if key in actual_reads:
                gap('EVALUATION_GAP','A raw paired dependency is duplicated')
            actual_reads.add(key)
        if actual_reads!=expected_reads:
            gap('EVALUATION_GAP','Paired dependencies differ from the complete AST-derived read closure')
        expected_diagnostics=[event for event in dependencies if _category(event,start) is not None]
        actual_diagnostics=[event for event in diagnostic['events'] if event['feature_ref'] is not None]
        if actual_diagnostics!=expected_diagnostics:
            gap('EVALUATION_GAP','Paired diagnostic events omit or substitute raw read evidence')
        if diagnostic['reason_categories']!=sorted(seen):
            gap('EVALUATION_GAP','Paired diagnostic categories differ from observed events')
        reasons.update(seen)
        counts[case['status']]+=1
        if case['status']=='ELIGIBLE':
            outdeps=[event for event in dependencies if event['program']=='outcome_program']
            if (case['scope'] is not True or when>as_of or anchor>=end or anchor>as_of
                    or case['label_information_interval']!={'start':when,'end':anchor}
                    or not outdeps or any(event['reason']!='available' for event in outdeps)):
                gap('EVALUATION_GAP','Eligible paired case has contradictory maturity or dependencies')
            value=_decode(case['outcome'])
            total=total+value
            n+=1
            if case['condition'] is True:
                conditioned=conditioned+value
                nc+=1
        elif case['outcome'] is not None or case['label_information_interval'] is not None:
            gap('EVALUATION_GAP','Unavailable paired outcome cannot carry a value')
    complete=len(cases)==expected
    if (report['processing_complete'] is not complete
            or report['outcomes_complete'] is not (complete and not any(counts[s] for s in PENDING))
            or report['review_required'] is not bool(counts['REVIEW_REQUIRED'])
            or canonical(report['state_counts'])!=canonical({s:counts[s] for s in sorted(STATES)})
            or report['status']!=('PROCESSED' if complete else 'RESOURCE_STOP')
            or (complete and report['resource_reason'] is not None)
            or (not complete and type(report['resource_reason']) is not str)
            or type(report['primitive_steps']) is not int or not 0<=report['primitive_steps']<=report['request']['max_steps']
            or canonical(report['diagnostics'])!=canonical({'schema':'paired-case-diagnostics/1','status':'COMPLETE' if complete else 'RESOURCE_STOP',
                                       'reason_counts':dict(sorted(reasons.items())),
                                       'condition_outcome_counts':_cross_counts(cases)})):
        gap('EVALUATION_GAP','Paired report metadata differs from its complete case stream')
    result={'schema':CONTRAST,'kind':'conditional-minus-scope-mean/1','evaluation_contract':CONTRACT,
            'status':'INFORMATION_GAP','reason':None,'scope_count':None,'condition_count':None,
            'scope_mean':None,'condition_mean':None,'effect':None,'scientific_readiness':False}
    if not complete:
        return {**result,'status':'RESOURCE_STOP','reason':'incomplete_processing'}
    if any(counts[s] for s in PENDING):
        return {**result,'reason':'outcomes_pending'}
    if counts['REVIEW_REQUIRED']:
        return {**result,'reason':'dependency_review_required'}
    a,b=total/Fraction(n) if n else None,conditioned/Fraction(nc) if nc else None
    result.update(scope_count=n,condition_count=nc,scope_mean=a.public() if a else None,
                  condition_mean=b.public() if b else None)
    if not n or not nc:
        return {**result,'reason':'no_scope_cases' if not n else 'no_conditioned_cases'}
    result.update(status='DESCRIPTIVE_ONLY',reason='paired_reference_calculation_complete',effect=(b-a).public())
    return result
