"""INACTIVE engineering candidate; no broker, source selector or spending grant.

The proposed 20M allowance is NOT approved by importing this module. All native
runtime profiles retain their existing source bytes and 10M ceiling. This
offline implementation preserves plain calculation, observed comparison and
base-byte binding, to make a specific resource decision reviewable.
"""
from collections import Counter
from copy import deepcopy

from .bounded_outcomes import CASES as BOUNDED_CASES, REQUEST as BOUNDED_REQUEST, _encode, bounded_contrast, legacy_request
from .case_diagnostics import CATEGORIES, MAX_CASE_BYTES, MAX_EVENTS, _Observation, _base_hash, _guard, _stream_hash
from .codec import canonical
from .exact_compositions import CONTRACT, ExactCompositionEngine
from .exact_outcomes import _DiagnosticEngine, lookback
from .expressions import ExpressionGap, gap
from .outcomes import PENDING, STATES, _case, _instant, _validate

PROFILE='engineering-exact-resource-proposal/1'
REQUEST='engineering-exact-case-request/1'
CASES='engineering-exact-cases/1'
DIAGNOSTICS='engineering-diagnostic-exact-cases/1'
CONTRAST='engineering-exact-contrast/1'
ACTIVATION='PENDING_SPECIFIC_RESOURCE_DECISION'
MAX_STEPS=20000000
AUTHORITY='offline_engineering_only'


def structural_projection(request):
    """Validate the proposed budget FIRST; reuse only old structural semantics.

    The legacy cap is projected solely for date/grid/identity/order checks and
    contrast arithmetic. The actual request, work, source/result identity and
    reported consumption retain the new explicit budget. No old-profile
    certificate or admission can be inferred from this projection.
    """
    if (type(request) is not dict or request.get('schema')!=REQUEST
            or type(request.get('max_steps')) is not int or not 1<=request['max_steps']<=MAX_STEPS):
        gap('RESOURCE_GAP','Explicit inactive engineering request with at most20M steps required')
    projected={**request,'schema':BOUNDED_REQUEST,'max_steps':min(request['max_steps'],10000000)}
    _validate(legacy_request(projected))
    if len(request['universe']['instruments'])!=1:
        gap('TYPE_GAP','The resource candidate remains single-instrument only')
    if any(type(request[key]) is not dict or request[key].get('schema')!='research-ast/4'
            for key in ('scope_program','condition_program','outcome_program')):
        gap('LANGUAGE_GAP','The resource candidate requires explicit AST4 programs')
    return projected


def guard_path(expression):
    """Neutral syntax only; recognition never certifies scientific validity."""
    if type(expression) is not dict:return None
    path='/expression'
    while expression.get('op')=='lag':
        if (set(expression)!={'op','arg','bars'} or type(expression['arg']) is not dict
                or type(expression['bars']) is not int or not 0<=expression['bars']<=1000000):return None
        expression=expression['arg'];path+='/arg'
    if (set(expression)!={'op','left','right'}
            or any(type(expression[key]) is not dict for key in ('left','right'))):return None
    try:original=_guard(expression)
    except (KeyError,TypeError,AttributeError):original=None
    if original is not None:return path+original[len('/expression'):]
    unknown={'op':'literal','type':'boolean','unit':None,'value':None}
    if (expression.get('op')=='eq' and expression['left'].get('op')=='or'
            and set(expression['left'])=={'op','left','right'}
            and type(expression['left']['left']) is dict and type(expression['left']['left'].get('op')) is str
            and type(expression['right'].get('op')) is str
            and canonical(expression['left']['right'])==canonical(unknown)):
        return path+'/left/left'
    return None


def materialize(request,catalog,rows):
    start,end,as_of,first,expected,instruments=_validate(legacy_request(structural_projection(request)))
    decision=ExactCompositionEngine(catalog,rows);outcomes=ExactCompositionEngine(catalog,rows,allow_log=True)
    scope=decision._program_node(request['scope_program']);condition=decision._program_node(request['condition_program'])
    outcome=outcomes._program_node(request['outcome_program'])
    if scope.kind!=condition.kind or scope.kind!='boolean' or outcome.kind!='real' or outcome.unit!='basis_points':
        gap('TYPE_GAP','Existing Boolean decisions and basis-point quantity required')
    if not outcomes.describe(request['outcome_program'])['feature_refs']:
        gap('LANGUAGE_GAP','An actual raw-feature outcome is required')
    remaining=[request['max_steps']];cases=[];reason=None
    for when in range(first,end,900):
        for instrument in instruments:
            try:
                case=_case(outcomes,scope,condition,outcome,when,instrument,start,end,as_of,
                    request['horizon_bars'],remaining,lookback(outcome),serialize=_encode,require_container_rows=False)
            except ExpressionGap as error:
                if error.code!='RESOURCE_GAP':raise
                reason=str(error);break
            cases.append(case)
        if reason is not None:break
    counts=Counter(case['status'] for case in cases);complete=len(cases)==expected and reason is None
    return {'schema':CASES,'profile':PROFILE,'activation':ACTIVATION,'authority':AUTHORITY,
        'request':deepcopy(request),'outcome_unit':outcome.unit,'cases':cases,'expected_case_count':expected,
        'processed_case_count':len(cases),'state_counts':{state:counts[state] for state in sorted(STATES)},
        'processing_complete':complete,'outcomes_complete':complete and not any(counts[state] for state in PENDING),
        'review_required':bool(counts['REVIEW_REQUIRED']),'status':'PROCESSED' if complete else 'RESOURCE_STOP',
        'resource_reason':reason,'primitive_steps':min(request['max_steps'],request['max_steps']-remaining[0]),
        'numerical_contract':'bounded-math/1.0','evaluation_contract':'required-inputs/1',
        'expression_contract':CONTRACT,'scientific_readiness':False}


def _projection(report):
    if (type(report) is not dict or report.get('schema')!=CASES or report.get('profile')!=PROFILE
            or report.get('activation')!=ACTIVATION or report.get('authority')!=AUTHORITY
            or report.get('expression_contract')!=CONTRACT or report.get('evaluation_contract')!='required-inputs/1'
            or report.get('scientific_readiness') is not False):
        gap('EVALUATION_GAP','An inactive engineering report is required')
    projected=structural_projection(report.get('request'))
    if type(report.get('primitive_steps')) is not int or not 0<=report['primitive_steps']<=report['request']['max_steps']:
        gap('RESOURCE_GAP','Actual engineering work exceeds its explicit request budget')
    return {**report,'schema':BOUNDED_CASES,'request':projected}


def contrast(report):
    result=bounded_contrast(_projection(report))
    if not report['processing_complete']:result={**result,'status':'RESOURCE_STOP'}
    return {**result,'schema':CONTRAST,'profile':PROFILE,'activation':ACTIVATION,'authority':AUTHORITY}


def add_diagnostics(report,catalog,rows,max_steps):
    _projection(report);contrast(report)
    if (type(max_steps) is not int or not 0<=max_steps<=MAX_STEPS
            or max_steps>report['request']['max_steps']-report['primitive_steps']):
        gap('RESOURCE_GAP','Diagnostic allocation exceeds the proposed shared request budget')
    request=report['request'];start,end=(_instant(request['universe'][key]) for key in ('start','end'))
    as_of=_instant(request['as_of']);decision=_DiagnosticEngine(catalog,rows);engine=_DiagnosticEngine(catalog,rows,allow_log=True)
    scope=decision.register(request['scope_program'],'scope_program')
    condition=decision.register(request['condition_program'],'condition_program')
    outcome=engine.register(request['outcome_program'],'outcome_program');engine.paths.update(decision.paths)
    selected=guard_path(request['condition_program']['expression']);stream_hash=_stream_hash(report['cases'])
    result=deepcopy(report);result.update(schema=DIAGNOSTICS,base_case_stream_sha256=stream_hash,
        base_report_hash=_base_hash(report,stream_hash))
    for case in result['cases']:case['diagnostics']=None
    remaining=[max_steps];processed=0;reason=None
    counts=Counter(dict.fromkeys(CATEGORIES,0));guards=Counter(dict.fromkeys(('true','false','unknown','unrecognized','not_evaluated'),0))
    for original,case in zip(report['cases'],result['cases']):
        observation=_Observation(start,selected);engine.observation=observation
        try:
            remaining[0]-=1
            if remaining[0]<0:gap('RESOURCE_GAP','Diagnostic replay exhausted its primitive-step budget')
            observed=_case(engine,scope,condition,outcome,case['decision_time'],case['instrument'],start,end,as_of,
                request['horizon_bars'],remaining,lookback(outcome),serialize=_encode,require_container_rows=False)
            if canonical(observed)!=canonical(original):gap('EVALUATION_GAP','Observed replay differs from the complete plain case')
            if observed['status']=='PARTITION_BOUNDARY':observation.categories.add('boundary_censoring')
            if observed['scope'] is True and observed['condition'] is None:observation.categories.add('condition_unknown')
            diagnostic=observation.public()
            if len(canonical({**original,'diagnostics':diagnostic}).encode())>MAX_CASE_BYTES:
                gap('RESOURCE_GAP','Diagnostic case exceeds its encoded-size limit')
        except ExpressionGap as error:
            if error.code!='RESOURCE_GAP':raise
            reason=str(error);break
        case['diagnostics']=diagnostic;counts.update(diagnostic['reason_categories'])
        guard=diagnostic['validity_guard']
        key=('unrecognized' if not guard['recognized'] else 'not_evaluated' if not guard['evaluated']
            else 'unknown' if guard['value'] is None else 'true' if guard['value'] is True else 'false')
        guards[key]+=1;processed+=1
    complete=processed==report['expected_case_count'] and report['processing_complete'] and reason is None
    result['diagnostics']={'schema':'engineering-case-diagnostics/1','status':'COMPLETE' if complete else 'RESOURCE_STOP',
        'processing_complete':complete,'expected_cases':report['expected_case_count'],'processed_cases':processed,
        'primitive_steps':min(max_steps,max_steps-remaining[0]),'reason':reason or (None if complete else 'Base computation is incomplete'),
        'reason_counts':dict(counts),'guard_counts':dict(guards),'categories_overlap':True,
        'invalidity_interpretation':'REQUIRES_INDEPENDENT_MEANING_REVIEW',
        'limits':{'remaining_steps':max_steps,'events_per_case':MAX_EVENTS,'case_bytes':MAX_CASE_BYTES},'scientific_readiness':False}
    return result


def base_projection(report):
    if (type(report) is not dict or report.get('schema')!=DIAGNOSTICS
            or type(report.get('diagnostics')) is not dict or report['diagnostics'].get('schema')!='engineering-case-diagnostics/1'):
        gap('EVALUATION_GAP','Expected proposed engineering diagnostics')
    base={key:deepcopy(value) for key,value in report.items()
        if key not in ('diagnostics','base_report_hash','base_case_stream_sha256','cases')}
    base['schema']=CASES
    base['cases']=[{key:deepcopy(value) for key,value in case.items() if key!='diagnostics'} for case in report['cases']]
    stream_hash=_stream_hash(base['cases'])
    if stream_hash!=report.get('base_case_stream_sha256') or _base_hash(base,stream_hash)!=report.get('base_report_hash'):
        gap('EVALUATION_GAP','Proposed diagnostic projection changed the plain base')
    _projection(base)
    return base
