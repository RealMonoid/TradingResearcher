"""D099 potential events and declared spans, without scientific authority.

Ranges describe immutable metadata, including positions whose observed scope or
missingness is not known. Raw-input membership, actual publication endpoints and
dependence/exposure/prior use remain separate, unqualified questions.
"""
from copy import deepcopy
import hashlib
from pathlib import Path

from . import binding
from .certification import _environment_current
from .codec import Invalid, canonical, digest, integer, strings, text
from .data import MAX_UTC_SECOND, window
from .expressions import ReferenceEngine
from .outcomes import _lookback, _validate


PROFILE = 'outcome-reservation/1.0'
EVENT = 'potential-outcome-event/1'
GRID = 'potential-outcome-grid/1'
DOMAIN = 'binance-spot'
GRID_SECONDS = 900
INSTRUMENTS = ('BTCUSDT', 'ETHUSDT')
MAX_HORIZON_BARS = 1000000
MAX_PLANS = 8
MAX_RANGES = MAX_PLANS * len(INSTRUMENTS)
RANGE_FIELDS = {'instrument', 'decision_start', 'decision_end', 'horizon_bars'}
GRID_FIELDS = {'schema', 'profile', 'market_domain', 'grid_seconds', 'ranges',
               'boundary_ranges', 'event_count', 'boundary_count'}
COMPILED_PROFILES = ('bound-reference/1', 'bound-reference/2',
                     'bound-reference/3', 'bound-reference/4')
DECLARED_STATIC_SOURCES = ('trading_researcher/expressions.py',
                          'trading_researcher/outcomes.py',
                          'trading_researcher/codec.py')
LOADED_DECLARED_STATIC = {
    name: hashlib.sha256((binding.ROOT / name).read_bytes()).hexdigest()
    for name in DECLARED_STATIC_SOURCES
}


def require(condition, message):
    if not condition:
        raise Invalid(message)


def _instrument(value):
    require(type(value) is str and value in INSTRUMENTS,
            'Outcome reservation requires an adopted Binance spot instrument')
    return value


def _time(value, name):
    integer(value, name)
    require(value <= MAX_UTC_SECOND and value % GRID_SECONDS == 0,
            'Outcome reservation times must be aligned bounded UTC seconds')
    return value


def _horizon(value):
    integer(value, 'outcome horizon', 1)
    require(value <= MAX_HORIZON_BARS, 'Outcome horizon exceeds the reference envelope')
    return value


def event_identity(instrument, decision_time, outcome_anchor):
    """Hash only the approved event schema and source-neutral coordinates."""
    _instrument(instrument)
    _time(decision_time, 'decision time')
    _time(outcome_anchor, 'outcome anchor')
    require(outcome_anchor > decision_time, 'Outcome anchor must follow the decision')
    return digest({'schema': EVENT, 'market_domain': DOMAIN,
                   'grid_seconds': GRID_SECONDS, 'instrument': instrument,
                   'decision_time': decision_time, 'outcome_anchor': outcome_anchor})


def _range(instrument, start, end, horizon):
    return {'instrument': instrument, 'decision_start': start,
            'decision_end': end, 'horizon_bars': horizon}


def _normalise_ranges(values):
    groups = {}
    for value in values:
        key = value['instrument'], value['horizon_bars']
        groups.setdefault(key, []).append((value['decision_start'], value['decision_end']))
    result = []
    for (instrument, horizon), intervals in sorted(groups.items()):
        current = None
        for start, end in sorted(intervals):
            if current is None:
                current = [start, end]
            elif start <= current[1]:
                current[1] = max(current[1], end)
            else:
                result.append(_range(instrument, *current, horizon))
                current = [start, end]
        if current is not None:
            result.append(_range(instrument, *current, horizon))
    require(len(result) <= MAX_RANGES, 'Potential family grid exceeds its compact range envelope')
    return result


def _count(ranges):
    return sum((value['decision_end'] - value['decision_start']) // GRID_SECONDS
               for value in ranges)


def _grid(ranges, boundaries):
    ranges = _normalise_ranges(ranges)
    boundaries = _normalise_ranges(boundaries)
    return {'schema': GRID, 'profile': PROFILE, 'market_domain': DOMAIN,
            'grid_seconds': GRID_SECONDS, 'ranges': ranges,
            'boundary_ranges': boundaries, 'event_count': _count(ranges),
            'boundary_count': _count(boundaries)}


def _checked_grid(value):
    require(type(value) is dict and set(value) == GRID_FIELDS,
            'Exact owned potential-grid fields required')
    require(value['schema'] == GRID and value['profile'] == PROFILE
            and value['market_domain'] == DOMAIN
            and type(value['grid_seconds']) is int and value['grid_seconds'] == GRID_SECONDS,
            'Unsupported potential-event namespace, profile or grid')
    for field in ('ranges', 'boundary_ranges'):
        values = value[field]
        require(type(values) is list and len(values) <= MAX_RANGES,
                'Bounded potential-grid ranges required')
        for item in values:
            require(type(item) is dict and set(item) == RANGE_FIELDS,
                    'Exact potential-event range fields required')
            _instrument(item['instrument'])
            start = _time(item['decision_start'], 'range start')
            end = _time(item['decision_end'], 'range end')
            horizon = _horizon(item['horizon_bars'])
            require(start < end, 'Potential ranges must be nonempty half-open intervals')
            if field == 'ranges':
                require(end - GRID_SECONDS + horizon * GRID_SECONDS <= MAX_UTC_SECOND,
                        'Potential outcome anchor exceeds the UTC envelope')
        require(values == _normalise_ranges(values),
                'Potential ranges must be sorted, distinct and maximally merged')
    for field, count in (('event_count', 'ranges'), ('boundary_count', 'boundary_ranges')):
        integer(value[field], field)
        require(value[field] == _count(value[count]), 'Potential-grid count differs from its ranges')
    canonical(value)
    return value


def potential_grid(universe, horizon_bars):
    """Retain evaluable and structural boundary positions without reading rows.

    The source universe is half open. A strictly interior outcome anchor is
    required, so the evaluable decision end is ``end - horizon * 900``.
    """
    horizon = _horizon(horizon_bars)
    start, end, instruments = window(universe)
    evaluable_end = max(start, end - horizon * GRID_SECONDS)
    ranges, boundaries = [], []
    for instrument in sorted(instruments):
        if start < evaluable_end:
            ranges.append(_range(instrument, start, evaluable_end, horizon))
        if evaluable_end < end:
            boundaries.append(_range(instrument, evaluable_end, end, horizon))
    return _checked_grid(_grid(ranges, boundaries))


def merge_grids(grids):
    """Union a predeclared family's event sets without splitting its budget.

    Boundary ranges retain the union of *source* structural exclusions. They
    can coincide with a potential event from another source universe; they are
    not a new family-wide exclusion. Per-plan grids retain that distinction.
    """
    require(type(grids) is list and 1 <= len(grids) <= MAX_PLANS,
            'One through eight predeclared potential grids required')
    ranges, boundaries = [], []
    for value in grids:
        value = _checked_grid(value)
        ranges.extend(value['ranges'])
        boundaries.extend(value['boundary_ranges'])
    return _checked_grid(_grid(ranges, boundaries))


def overlapping_events(left, right):
    """Detect exact same-event intersection, not raw overlap or dependence."""
    left, right = _checked_grid(left), _checked_grid(right)
    for first in left['ranges']:
        for second in right['ranges']:
            if (first['instrument'] == second['instrument']
                    and first['horizon_bars'] == second['horizon_bars']
                    and max(first['decision_start'], second['decision_start'])
                    < min(first['decision_end'], second['decision_end'])):
                return True
    return False


def declared_spans(request, catalog):
    """Conservative static envelopes for the current scalar-plan owner.

    Reuse AST1's compiler and complete nested lag/mean lookback. This is neither
    an exact read set nor a claim about observed rows or publication. Decision
    envelopes include structural boundary positions, because the case owner
    can inspect scope/condition before rejecting their outcome anchor. Literal
    coordinates conservatively retain the legacy observation-presence rule.
    Unsupported expression/request profiles require their own qualified owner.
    """
    _validate(request)
    start, end, instruments = window(request['universe'])
    horizon = _horizon(request['horizon_bars'])
    # A single empty structural row supports static compilation only. No
    # supplied market observations, row expansion or calculation is performed.
    engine = ReferenceEngine(catalog, [
        {'time': start, 'instrument': instruments[0], 'features': {}}])
    programs = {}
    for name in ('scope_program', 'condition_program', 'outcome_program'):
        program = request[name]
        node = engine._program_node(program)
        expected = ('boolean' if name != 'outcome_program'
                    or request['outcome_scale'] == 'binary_probability' else 'real')
        require(node.kind == expected, 'Declared program type differs from its case role')
        lookback = _lookback(node)
        first = start if name != 'outcome_program' else start + horizon * GRID_SECONDS
        positions, observations = [], []
        if first < end:
            for instrument in sorted(instruments):
                positions.append({'instrument': instrument, 'start': first, 'end': end})
                required_start = first - lookback
                observations.append({'instrument': instrument, 'start': required_start,
                    'end': end, 'unavailable_before_epoch_seconds': max(0, -required_start)})
        programs[name] = {'expression_profile': 'research-ast/1',
            'lookback_seconds': lookback, 'feature_refs': engine.describe(program)['feature_refs'],
            'positions': positions, 'required_observations': observations}
    result = {'schema': 'declared-observation-spans/1', 'profile': PROFILE,
        'market_domain': DOMAIN, 'grid_seconds': GRID_SECONDS,
        'universe': {**deepcopy(request['universe']), 'instruments': sorted(instruments)},
        'horizon_bars': horizon, 'programs': programs, 'conservative': True,
        'raw_input_membership': 'NOT_QUALIFIED',
        'actual_inputs_and_publication': 'NOT_OBSERVED',
        'dependence_exposure_prior_use': 'NOT_QUALIFIED', 'scientific_readiness': False}
    canonical(result)
    return result


def _declared_source_compatibility(source):
    """Never reinterpret a retained AST with changed current static owners."""
    for name, expected in LOADED_DECLARED_STATIC.items():
        retained = source.get(name)
        require(type(retained) is bytes and hashlib.sha256(retained).hexdigest() == expected,
                'Retained declared-span static owner differs from the loaded implementation')
        require(hashlib.sha256((binding.ROOT / name).read_bytes()).hexdigest() == expected,
                'Loaded declared-span static owner changed on disk')
    return deepcopy(LOADED_DECLARED_STATIC)


def _plan_binding(broker, actor, plan_id):
    """Resolve only existing owned compilation/certificate metadata owners.

    Those owners hash retained input blobs to check custody. This function never
    calls a row loader/scanner, child, calculator or outcome materializer.
    """
    broker._require_usable_dependencies(plan_id)
    inspected = broker._inspect_evaluation_plan(actor, plan_id)
    require(inspected['status'] == 'POLICY_DRAFT', 'A retained policy draft is required')
    plan = broker._artifact(plan_id)
    plan_body = plan['body']
    compiled_id = text(plan_body['request']['compiled_id'], 'compiled identity')
    compiled = broker._artifact(compiled_id)
    body = compiled['body']
    require(compiled['creator'] == compiled['origin'] == 'controller'
            and compiled.get('authority') == binding.AUTHORITY
            and compiled['data_class'] in ('development', 'assessment')
            and type(body) is dict and body.get('schema') == 'compiled-hypothesis/1'
            and body.get('status') == 'COMPILED' and body.get('profile') in COMPILED_PROFILES,
            'Owned supported compiled metadata required')
    broker._require_usable_dependencies(compiled_id)
    arguments = body['dependency_arguments']
    dependencies = broker._bound_request_dependencies(actor, arguments)
    snapshot = dependencies['snapshot']
    require(body['data_snapshot_id'] == snapshot['id'], 'Compiled snapshot binding differs')
    payload = {'formalization_id': arguments['formalization_id'],
               'candidate': dependencies['formalization']['body']['candidate'],
               'catalog': dependencies['catalog'], 'data_manifest': snapshot['body']['manifest'],
               'as_of': arguments['as_of'], 'max_steps': arguments['max_steps']}
    require(canonical(body['compilation_input']) == canonical(payload),
            'Immutable compilation inputs differ from their owned dependencies')
    compilation = body['compilation']
    require(compilation['request']['schema'] == 'reference-case-request/1',
            'This scientific-plan owner does not qualify bounded or exact outcome membership')
    binding.validate_compilation(compilation, payload)
    package_id = body['source_package_id']
    source = broker._load_binding_package(package_id)
    require(binding.package_profile(source) == body['profile']
            and all(source.get(name) == raw for name, raw in dependencies['reference_bundle'].items())
            and _environment_current(body['environment']),
            'Retained compiled source or runtime differs from its qualified binding')
    static_sources = _declared_source_compatibility(source)
    feature = dependencies['feature_certificate']
    reference = dependencies['reference_certificate']
    feature_body = feature['body']
    definitions_id = feature_body['definitions_id']
    normalization_id = feature_body['replay']['normalization_id']
    manifest = snapshot['body']['manifest']
    require(type(manifest.get('grid_seconds')) is int
            and manifest['grid_seconds'] == GRID_SECONDS,
            'Snapshot does not use the adopted observation grid')
    # The existing feature-certificate owner checks the exact fixed Binance raw
    # definitions/normalization. A free-form provider string is not a namespace.
    grid = potential_grid(compilation['request']['universe'],
                          compilation['request']['horizon_bars'])
    require(compilation['expected_case_count'] == grid['event_count'] + grid['boundary_count']
            and compilation['expected_case_count'] <= 100000,
            'Potential grid differs from the owned compilation envelope')
    spans = declared_spans(compilation['request'], payload['catalog'])
    require(_declared_source_compatibility(source) == static_sources,
            'Declared-span static source changed during metadata derivation')
    refs = sorted(set(plan['source_refs']) | set(dependencies['refs'])
                  | {plan_id, compiled_id, package_id, definitions_id, normalization_id})
    strings(refs, 'potential-event source bindings')
    return {'plan_id': plan_id, 'compiled_id': compiled_id,
            'data_snapshot_id': snapshot['id'], 'compilation_profile': body['profile'],
            'compilation_source_package_id': package_id,
            'compilation_source_footprint': binding.hashes(source),
            'reference_certificate_id': reference['id'], 'feature_certificate_id': feature['id'],
            'feature_definitions_id': definitions_id, 'normalization_id': normalization_id,
            'snapshot_manifest_hash': digest(manifest),
            'compiled_candidate_hash': compilation['candidate_hash'],
            'compilation_request_hash': digest(compilation['request']),
            'catalog_hash': digest(payload['catalog']),
            'declared_spans_static_source_footprint': static_sources,
            'declared_observation_spans': spans,
            'grid': grid, 'source_refs': refs}


def reservation_for_plans(broker, actor, plan_ids):
    """Bind potential metadata through actual owners; grant no admission.

    Existing owner errors propagate for the consuming caller to retain as a
    component gap. Zero potential events remain explicit and cannot reserve
    scientifically admissible outcomes. In particular, ``row_window`` is never
    relabeled as exact target-operand membership, nor is legacy lookback applied
    to an unsupported exact-composition profile.
    """
    identities = strings(plan_ids, 'predeclared plan identities')
    require(1 <= len(identities) <= MAX_PLANS, 'One through eight unique plans required')
    bindings = [_plan_binding(broker, actor, identity) for identity in identities]
    grid = merge_grids([item['grid'] for item in bindings])
    refs = sorted({identity for item in bindings for identity in item['source_refs']})
    strings(refs, 'potential-event source bindings')
    result = {'profile': PROFILE, 'status': 'POTENTIAL_GRID_BOUND', 'grid': grid,
              'plan_bindings': bindings, 'artifact_ids': refs,
              'raw_input_membership': 'NOT_QUALIFIED',
              'actual_inputs_and_publication': 'NOT_OBSERVED',
              'dependence_exposure_prior_use': 'NOT_QUALIFIED',
              'scientific_readiness': False}
    canonical(result)
    return deepcopy(result)
