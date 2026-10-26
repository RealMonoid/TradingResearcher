"""Bounded syntactic time identities; never a population adequacy decision.

This describes values under valid, exactly bound reference-program semantics.
It neither compiles programs nor rewrites executable ASTs or their missingness.
"""
import hashlib

from .codec import Invalid, canonical, digest
from .evaluation_policy import require
from .expressions import REFERENCE, scalar
from .outcomes import _read_rational, reference_contrast


SCHEMA = 'source-process-scope/1'
_BINARY = frozenset(('add', 'sub', 'mul', 'div', 'lt', 'le', 'gt', 'ge', 'eq', 'and', 'or'))


def _shape(program):
    """Keep exact ordered syntax, except lag; collect each feature's time shift.

    A lag can change intermediate-row availability even when its mathematical
    value is unchanged. Removing it here is only for a shared-observed-value
    comparison, never an optimization or executable program transformation.
    """
    require(type(program) is dict and set(program) == {'schema', 'catalog_hash', 'expression'}
            and program['schema'] == 'research-ast/1', 'Unsupported program envelope')
    catalog = program['catalog_hash']
    require(type(catalog) is str and len(catalog) == 64
            and all(c in '0123456789abcdef' for c in catalog), 'Exact catalog hash required')
    offsets = []; count = 0

    def walk(node, offset, depth):
        nonlocal count
        count += 1
        require(depth < 32 and count <= 256, 'Expression diagnostic envelope exceeded')
        require(type(node) is dict and type(node.get('op')) is str, 'Named expression required')
        op = node['op']
        if op == 'feature':
            require(set(node) == {'op', 'ref'} and type(node['ref']) is str
                    and REFERENCE.fullmatch(node['ref']) is not None, 'Exact feature version required')
            offsets.append(offset)
            return ['feature', node['ref']]
        if op == 'literal':
            require(set(node) == {'op', 'type', 'unit', 'value'}, 'Exact literal required')
            scalar(node['type'], node['unit'], node['value'])
            return ['literal', node['type'], node['unit'], node['value']]
        if op == 'lag':
            require(set(node) == {'op', 'arg', 'bars'} and type(node['bars']) is int
                    and 0 <= node['bars'] <= 1000000, 'Bounded integer lag required')
            return walk(node['arg'], offset-node['bars'], depth+1)
        if op == 'not':
            require(set(node) == {'op', 'arg'}, 'Exact unary expression required')
            return [op, walk(node['arg'], offset, depth+1)]
        require(op in _BINARY and set(node) == {'op', 'left', 'right'}, 'Unsupported diagnostic syntax')
        return [op, walk(node['left'], offset, depth+1), walk(node['right'], offset, depth+1)]

    return catalog, canonical(walk(program['expression'], 0, 0)), offsets


def _observations(cases, offset):
    values = {}
    for case in cases:
        condition = case.get('condition')
        require(condition is None or type(condition) is bool, 'Observed condition must be Boolean or missing')
        outcome = case.get('outcome')
        outcome = None if outcome is None else _read_rational(outcome)
        require(outcome is None or outcome in (0, 1), 'Observed binary outcome must be zero, one or missing')
        values[case['decision_time'], case['instrument']] = (condition, outcome, case['status'])
    counts = dict.fromkeys(('target_rows', 'partner_absent', 'both_unobserved', 'condition_unobserved',
                           'outcome_unobserved', 'compared', 'equal', 'unequal', 'both_eligible_compared'), 0)
    counts['target_rows'] = len(cases)
    for (when, instrument), (condition, _, status) in values.items():
        partner = values.get((when+offset*900, instrument))
        if partner is None:
            counts['partner_absent'] += 1
            continue
        outcome = partner[1]
        if condition is None or outcome is None:
            missing = ('both_unobserved' if condition is None and outcome is None
                       else 'condition_unobserved' if condition is None else 'outcome_unobserved')
            counts[missing] += 1
            continue
        counts['compared'] += 1
        counts['equal' if int(condition) == outcome else 'unequal'] += 1
        counts['both_eligible_compared'] += int(status == partner[2] == 'ELIGIBLE')
    return counts


def diagnose_source_process(report):
    """Inspect one source condition/outcome pair, including explicit gaps.

    A match is conditional on valid reference-program semantics and the same
    immutable feature/catalog binding. It is not independent certification.
    No match says nothing about independence or other structural relationships.
    """
    reference_contrast(report)  # Validate the case grid; its scientific gaps remain gaps.
    request = report['request']
    checksum = hashlib.sha256()
    for case in report['cases']:
        checksum.update((canonical(case)+'\n').encode())
    result = {'schema': SCHEMA, 'source_request_hash': digest(request),
        'case_stream_sha256': checksum.hexdigest(), 'processing_complete': report['processing_complete'],
        'status': 'NOT_ASSESSED', 'reason': 'binary_probability_required',
        'identity': None, 'observations': None, 'original_process_adequacy': 'NOT_ASSESSED',
        'scientific_readiness': False, 'classification_permitted': False,
        'qualifications': ['conditional_on_valid_exactly_bound_reference_programs',
            'program_compilation_and_feature_semantics_not_certified_here',
            'value_identity_only_on_jointly_observable_support',
            'no_equality_of_missingness_eligibility_or_availability_traces',
            'no_AST_rewrite_or_requirement_on_bootstrap_draws',
            'absence_of_a_match_does_not_establish_independence_or_adequacy',
            'observed_pairs_are_descriptive_not_population_evidence']}
    if request['outcome_scale'] != 'binary_probability':
        return result
    try:
        cc, cs, co = _shape(request['condition_program'])
        yc, ys, yo = _shape(request['outcome_program'])
    except Invalid:
        result['reason'] = 'unsupported_or_invalid_diagnostic_syntax'
        return result
    if cc != yc:
        result['reason'] = 'distinct_catalog_bindings'
        return result
    shifts = {c-y for c, y in zip(co, yo)}
    if cs != ys or len(co) != len(yo) or len(shifts) != 1:
        result['reason'] = 'no_unique_uniform_feature_shift'
        return result
    offset = shifts.pop()-request['horizon_bars']
    result.update(status='SHIFTED_VALUE_IDENTITY', reason='exact_ordered_syntax_with_uniform_feature_shift',
        identity={'condition_equals_outcome_at_offset_bars': offset,
                  'catalog_hash': cc, 'grid_seconds': 900},
        observations=_observations(report['cases'], offset))
    return result
