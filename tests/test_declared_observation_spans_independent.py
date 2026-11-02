"""Hand-fixed conservative scalar observation envelopes, never actual read sets.

No row expansion, evaluation, world, scientific admission or protected data use
is authorized by these spans. Literal coordinates retain the legacy engine's
observation-presence envelope. The genuine caller uses existing owned synthetic
compile/plan fixtures and must retain all scientific admission gaps.
"""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import test_evaluation_plans as plan_support
from trading_researcher.codec import Invalid
from trading_researcher import codec, expressions, outcomes
from trading_researcher import outcome_reservations as owner


CATALOG = {'x@1': {'type': 'real', 'unit': 'USD'},
           'y@1': {'type': 'real', 'unit': 'USD'}}
STATIC_OWNERS = {'trading_researcher/expressions.py': expressions,
                 'trading_researcher/outcomes.py': outcomes,
                 'trading_researcher/codec.py': codec}


def independent_hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def program(expression, catalog=CATALOG):
    return {'schema': 'research-ast/1', 'catalog_hash': independent_hash(catalog),
            'expression': deepcopy(expression)}


def literal(value=True):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def nested_request():
    # Scope: lag2(mean3(x)) =>4 bars; condition: mean2(lag1(x))=>2 bars.
    scope = {'op': 'lag', 'bars': 2, 'arg': {'op': 'trailing_mean', 'bars': 3,
             'arg': {'op': 'feature', 'ref': 'x@1'}}}
    condition = {'op': 'trailing_mean', 'bars': 2,
                 'arg': {'op': 'lag', 'bars': 1, 'arg': {'op': 'feature', 'ref': 'x@1'}}}
    zero = {'op': 'literal', 'type': 'real', 'unit': 'USD', 'value': '0'}
    # Outcome: mean3(lag2(mean2(y))) =>(2+2+1)=5 bars.
    outcome = {'op': 'trailing_mean', 'bars': 3,
        'arg': {'op': 'lag', 'bars': 2, 'arg': {'op': 'trailing_mean', 'bars': 2,
        'arg': {'op': 'feature', 'ref': 'y@1'}}}}
    return {'schema': 'reference-case-request/1', 'candidate_ref': 'synthetic-original-claim',
        'data_snapshot_ref': 'synthetic-source-revision',
        'scope_program': program({'op': 'gt', 'left': scope, 'right': zero}),
        'condition_program': program({'op': 'gt', 'left': condition, 'right': zero}),
        'outcome_program': program(outcome), 'outcome_scale': 'quantity', 'horizon_bars': 2,
        'universe': {'start': '2020-01-01T01:00:00Z', 'end': '2020-01-01T02:00:00Z',
                     'instruments': ['BTCUSDT']},
        'as_of': '2020-01-01T02:00:00Z', 'max_steps': 100000}


def positions(start, end, instrument='BTCUSDT'):
    return {'instrument': instrument, 'start': start, 'end': end}


def required(start, end, unavailable=0, instrument='BTCUSDT'):
    return {'instrument': instrument, 'start': start, 'end': end,
            'unavailable_before_epoch_seconds': unavailable}


def expected_program(lookback, refs, evaluation_positions, observations):
    return {'expression_profile': 'research-ast/1', 'lookback_seconds': lookback,
            'feature_refs': refs, 'positions': evaluation_positions,
            'required_observations': observations}


def expected(universe, horizon, programs):
    return {'schema': 'declared-observation-spans/1', 'profile': 'outcome-reservation/1.0',
        'market_domain': 'binance-spot', 'grid_seconds': 900, 'universe': deepcopy(universe),
        'horizon_bars': horizon, 'programs': programs, 'conservative': True,
        'raw_input_membership': 'NOT_QUALIFIED', 'actual_inputs_and_publication': 'NOT_OBSERVED',
        'dependence_exposure_prior_use': 'NOT_QUALIFIED', 'scientific_readiness': False}


@contextmanager
def static_only(broker=None):
    with ExitStack() as stack:
        for target in ('trading_researcher.expressions.ReferenceEngine._calculate',
                       'trading_researcher.outcomes.materialize_reference',
                       'trading_researcher.binding.run_child'):
            stack.enter_context(patch(target,
                side_effect=AssertionError('Declared spans evaluated or materialized outcomes')))
        if broker is not None:
            for name in ('_load_reference_data', '_scan_data'):
                stack.enter_context(patch.object(broker, name,
                    side_effect=AssertionError('Declared spans loaded observation rows')))
            stack.enter_context(patch('trading_researcher.evaluation_plans.run_plan_child',
                side_effect=AssertionError('Freeze launched plan computation')))
        yield


class DeclaredObservationSpansIndependentTests(unittest.TestCase):
    def test_nested_lookbacks_are_complete_unclipped_and_end_includes_last_observation(self):
        request = nested_request()
        original = deepcopy(request)
        fixed = expected(request['universe'], 2, {
            'scope_program': expected_program(3600, ['x@1'],
                [positions(1577840400, 1577844000)], [required(1577836800, 1577844000)]),
            'condition_program': expected_program(1800, ['x@1'],
                [positions(1577840400, 1577844000)], [required(1577838600, 1577844000)]),
            'outcome_program': expected_program(4500, ['y@1'],
                [positions(1577842200, 1577844000)], [required(1577837700, 1577844000)])})
        with static_only():
            result = owner.declared_spans(request, CATALOG)
        self.assertEqual(fixed, result)
        self.assertEqual(original, request)
        self.assertEqual({'x@1': {'type': 'real', 'unit': 'USD'},
                          'y@1': {'type': 'real', 'unit': 'USD'}}, CATALOG)

    def test_epoch_warmup_stays_negative_and_explicitly_unavailable(self):
        request = nested_request()
        request['universe'].update(start='1970-01-01T00:00:00Z', end='1970-01-01T01:00:00Z')
        request['horizon_bars'] = 1
        with static_only():
            result = owner.declared_spans(request, CATALOG)
        self.assertEqual(expected(request['universe'], 1, {
            'scope_program': expected_program(3600, ['x@1'], [positions(0, 3600)],
                [required(-3600, 3600, 3600)]),
            'condition_program': expected_program(1800, ['x@1'], [positions(0, 3600)],
                [required(-1800, 3600, 1800)]),
            'outcome_program': expected_program(4500, ['y@1'], [positions(900, 3600)],
                [required(-3600, 3600, 3600)])}), result)

    def test_boundary_decisions_remain_declared_when_no_valid_outcome_anchor_exists(self):
        request = nested_request()
        for horizon in (4, 5):
            request['horizon_bars'] = horizon
            with self.subTest(horizon=horizon), static_only():
                result = owner.declared_spans(request, CATALOG)
            self.assertEqual([positions(1577840400, 1577844000)],
                             result['programs']['scope_program']['positions'])
            self.assertEqual([positions(1577840400, 1577844000)],
                             result['programs']['condition_program']['positions'])
            self.assertEqual(expected_program(4500, ['y@1'], [], []),
                             result['programs']['outcome_program'])

    def test_literal_only_keeps_conservative_observation_presence_coordinates(self):
        request = nested_request()
        request.update(scope_program=program(literal(False)), condition_program=program(literal()),
                       outcome_program=program(literal()), outcome_scale='binary_probability')
        with static_only():
            result = owner.declared_spans(request, CATALOG)
        decision = expected_program(0, [], [positions(1577840400, 1577844000)],
                                   [required(1577840400, 1577844000)])
        outcome = expected_program(0, [], [positions(1577842200, 1577844000)],
                                  [required(1577842200, 1577844000)])
        self.assertEqual(expected(request['universe'], 2, {
            'scope_program': decision, 'condition_program': deepcopy(decision),
            'outcome_program': outcome}), result)

    def test_pending_asof_and_provenance_aliases_cannot_clip_declared_ranges_or_create_identity(self):
        request = nested_request()
        with static_only():
            initial = owner.declared_spans(request, CATALOG)
            for as_of in ('1970-01-01T00:00:00Z', '2020-01-01T01:00:00Z',
                          '2020-01-01T01:15:00Z', '2020-01-02T00:00:00Z'):
                changed = {**deepcopy(request), 'as_of': as_of,
                           'candidate_ref': 'another-claim', 'data_snapshot_ref': 'another-revision'}
                with self.subTest(as_of=as_of):
                    self.assertEqual(initial, owner.declared_spans(changed, CATALOG))
        for key in ('rows', 'actual_inputs', 'event_ids', 'outcome_record_ids', 'label_information_interval'):
            self.assertNotIn(key, initial)
        self.assertEqual('NOT_OBSERVED', initial['actual_inputs_and_publication'])
        self.assertEqual('NOT_QUALIFIED', initial['raw_input_membership'])

    def test_false_scope_does_not_make_condition_envelope_an_exact_observed_read_set(self):
        request = nested_request()
        request['scope_program'] = program(literal(False))
        with static_only():
            result = owner.declared_spans(request, CATALOG)
        self.assertEqual(expected_program(1800, ['x@1'],
            [positions(1577840400, 1577844000)], [required(1577838600, 1577844000)]),
            result['programs']['condition_program'])
        self.assertIs(result['conservative'], True)
        self.assertIs(result['scientific_readiness'], False)
        # Different horizon pairs can have overlapping conservative operands;
        # neither an overlap nor a declared span is the stable event identity.
        self.assertNotEqual(owner.event_identity('BTCUSDT', 1577840400, 1577841300),
                            owner.event_identity('BTCUSDT', 1577841300, 1577842200))

    def test_multiple_instruments_and_year_grid_stay_compact_and_canonical(self):
        request = nested_request()
        request['universe'] = {'start': '2020-01-01T00:00:00Z', 'end': '2021-01-01T00:00:00Z',
                               'instruments': ['ETHUSDT', 'BTCUSDT']}
        with static_only():
            result = owner.declared_spans(request, CATALOG)
        self.assertEqual(['BTCUSDT', 'ETHUSDT'], result['universe']['instruments'])
        self.assertEqual([positions(1577836800, 1609459200),
                          positions(1577836800, 1609459200, 'ETHUSDT')],
                         result['programs']['scope_program']['positions'])
        self.assertEqual([required(1577833200, 1609459200),
                          required(1577833200, 1609459200, instrument='ETHUSDT')],
                         result['programs']['scope_program']['required_observations'])
        self.assertEqual([positions(1577838600, 1609459200),
                          positions(1577838600, 1609459200, 'ETHUSDT')],
                         result['programs']['outcome_program']['positions'])
        self.assertLess(len(encoded_result := json.dumps(result)), 8000)
        self.assertNotIn('actual_rows', encoded_result)

    def test_unknown_request_ast_profiles_bad_catalog_and_invalid_types_fail_closed(self):
        mutations = [
            {'schema': 'bounded-reference-case-request/1'},
            {'schema': 'required-input-reference-case-request/1'},
            {'schema': 'paired-reference-case-request/1'},
            {'horizon_bars': True}, {'horizon_bars': 0}, {'horizon_bars': 1000001},
            {'max_steps': False}, {'as_of': 'not-UTC'}, {'outcome_scale': 'basis_points'},
        ]
        for change in mutations:
            with self.subTest(change=change), static_only(), self.assertRaises(Invalid):
                owner.declared_spans({**nested_request(), **change}, CATALOG)
        for schema in ('research-ast/2', 'research-ast/4', 'research-ast/999'):
            request = nested_request()
            request['outcome_program']['schema'] = schema
            with self.subTest(schema=schema), static_only(), self.assertRaises(Invalid):
                owner.declared_spans(request, CATALOG)
        for catalog in ({}, {'x@1': {'type': 'real', 'unit': None}}, [],
                        {'x@1': {'type': 'real', 'unit': 'USD', 'future_metadata': True}}):
            with self.subTest(catalog=catalog), static_only(), self.assertRaises(Invalid):
                owner.declared_spans(nested_request(), catalog)
        for field in ('as_of', 'scope_program', 'universe'):
            request = nested_request()
            del request[field]
            with self.subTest(missing=field), static_only(), self.assertRaises(Invalid):
                owner.declared_spans(request, CATALOG)

    def test_wrong_program_types_unknown_features_and_unaligned_universes_fail_closed(self):
        requests = []
        for field in ('scope_program', 'condition_program'):
            request = nested_request()
            request[field] = program({'op': 'feature', 'ref': 'x@1'})
            requests.append(request)
        request = nested_request()
        request['outcome_program'] = program(literal())
        requests.append(request)
        request = nested_request()
        request['condition_program'] = program({'op': 'feature', 'ref': 'missing@1'})
        requests.append(request)
        request = nested_request()
        request['universe']['start'] = '2020-01-01T01:00:01Z'
        requests.append(request)
        request = nested_request()
        request['universe']['instruments'] = ['UNKNOWN']
        requests.append(request)
        for index, request in enumerate(requests):
            with self.subTest(case=index), static_only(), self.assertRaises(Invalid):
                owner.declared_spans(request, CATALOG)


class DeclaredObservationSpansOwnedCallerIndependentTests(unittest.TestCase):
    setUpClass = classmethod(plan_support.EvaluationPlanTests.setUpClass.__func__)
    tearDownClass = classmethod(plan_support.EvaluationPlanTests.tearDownClass.__func__)
    arguments = plan_support.EvaluationPlanTests.arguments

    def test_actual_public_freeze_retains_declared_spans_catalog_and_existing_source_bindings(self):
        plan = self.broker.call(self.token, 'prepare_evaluation_plan',
                               **self.arguments('declared-spans-owned-plan'))
        source = self.broker.call(self.token, 'add_source',
            body={'scope': 'Synthetic campaign/selection anchor; no qualification'}, data_class='development')
        original_plan, original_compiled = deepcopy(plan), deepcopy(self.compiled)
        with static_only(self.broker):
            result = self.broker.call(self.token, 'freeze_scientific_batch',
                key='declared-spans-public-freeze', campaign_id=source['id'], role='primary',
                plan_ids=[plan['id']], selection_record_ref=source['id'], reservation_spec_ref=source['id'])
        self.assertEqual('ADMISSION_GAP', result['body']['status'])
        for flag in ('scientific_readiness', 'frozen', 'allocation_reserved'):
            self.assertIs(result['body'][flag], False)
        resolution = result['body']['admission']
        for gap in ('SCIENTIFIC_SELECTION_AND_RESERVATION_NOT_QUALIFIED',
                    'SCIENTIFIC_DATA_AND_EXPOSURE_NOT_ADMITTED',
                    'CALIBRATED_ESTIMATOR_AND_INFORMATION_PLAN_NOT_ADMITTED'):
            self.assertIn(gap, resolution['gaps'])
        reservation = resolution['admission']['outcome_reservation']
        self.assertEqual('POTENTIAL_GRID_BOUND', reservation['status'])
        self.assertEqual('NOT_QUALIFIED', reservation['raw_input_membership'])
        self.assertEqual('NOT_OBSERVED', reservation['actual_inputs_and_publication'])
        self.assertEqual('NOT_QUALIFIED', reservation['dependence_exposure_prior_use'])
        binding = reservation['plan_bindings'][0]
        body = self.compiled['body']
        catalog = body['compilation_input']['catalog']
        self.assertEqual(independent_hash(catalog), binding['catalog_hash'])
        self.assertEqual(plan['id'], binding['plan_id'])
        self.assertEqual(self.compiled['id'], binding['compiled_id'])
        self.assertEqual('bound-reference/1', binding['compilation_profile'])
        self.assertEqual(independent_hash(body['compilation']['request']), binding['compilation_request_hash'])
        self.assertEqual({name: hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()
            for name, module in STATIC_OWNERS.items()}, binding['declared_spans_static_source_footprint'])
        package = self.broker.call(self.token, 'get_artifact', artifact_id=body['source_package_id'])
        self.assertEqual(package['body']['footprint'], binding['compilation_source_footprint'])
        universe = {'start': '2020-01-01T00:15:00Z', 'end': '2020-01-01T01:00:00Z',
                    'instruments': ['BTCUSDT']}
        decision_positions = [positions(1577837700, 1577840400)]
        decision_observations = [required(1577837700, 1577840400)]
        self.assertEqual(expected(universe, 1, {
            'scope_program': expected_program(0, [], decision_positions, decision_observations),
            'condition_program': expected_program(0, ['BTCUSDT.close@binance-spot-15m-v1'],
                deepcopy(decision_positions), deepcopy(decision_observations)),
            'outcome_program': expected_program(0, [], [positions(1577838600, 1577840400)],
                [required(1577838600, 1577840400)])}), binding['declared_observation_spans'])
        for schema in ('scientific-allocation/1', 'scientific-trial/1', 'frozen-manifest/1'):
            self.assertEqual([], self.broker._freeze_objects(schema))
        self.assertEqual(original_plan, self.broker.call(self.token, 'get_artifact', artifact_id=plan['id']))
        self.assertEqual(original_compiled,
            self.broker.call(self.token, 'get_artifact', artifact_id=self.compiled['id']))

    def test_direct_metadata_owner_rejects_changed_current_static_bytes_without_any_disk_write(self):
        """Source-observation seam only; no private admission judge is replaced.

        Direct resolution avoids the outer freeze source-capture gate masking
        the independent loaded/current/retained static-owner currency check.
        """
        plan = self.broker.call(self.token, 'prepare_evaluation_plan',
                               **self.arguments('declared-spans-static-currentness'))
        original = Path.read_bytes
        changed_path = Path(expressions.__file__).resolve()

        def changed_observation(path):
            raw = original(path)
            if Path(path).resolve() == changed_path:
                return raw + b'\n# Synthetic observed source drift; no actual file changed.\n'
            return raw

        with patch.object(Path, 'read_bytes', autospec=True, side_effect=changed_observation), \
                static_only(self.broker), self.assertRaises(Invalid):
            owner.reservation_for_plans(self.broker, self.broker._binding_owner(self.token), [plan['id']])
        self.assertEqual(plan, self.broker.call(self.token, 'get_artifact', artifact_id=plan['id']))
        self.assertEqual(self.compiled,
            self.broker.call(self.token, 'get_artifact', artifact_id=self.compiled['id']))

    def test_public_caller_rejects_changed_retained_static_package_bytes_without_rewriting_sources(self):
        """Alter only the existing source transport return, not certificate bytes."""
        plan = self.broker.call(self.token, 'prepare_evaluation_plan',
                               **self.arguments('declared-spans-retained-package'))
        source = self.broker.call(self.token, 'add_source',
            body={'scope': 'Synthetic source-package corruption caller fixture'}, data_class='development')
        original_load = self.broker._load_binding_package
        package_id = self.compiled['body']['source_package_id']

        def changed_package(identity):
            bundle = original_load(identity)
            if identity == package_id:
                bundle = dict(bundle)
                bundle['trading_researcher/outcomes.py'] += b'\n# Synthetic retained transport mismatch.\n'
            return bundle

        with patch.object(self.broker, '_load_binding_package', side_effect=changed_package), \
                static_only(self.broker):
            result = self.broker.call(self.token, 'freeze_scientific_batch',
                key='declared-spans-static-package-gap', campaign_id=source['id'], role='primary',
                plan_ids=[plan['id']], selection_record_ref=source['id'], reservation_spec_ref=source['id'])
        self.assertEqual('ADMISSION_GAP', result['body']['status'])
        resolution = result['body']['admission']
        self.assertIn('OUTCOME_RESERVATION_METADATA_NOT_QUALIFIED', resolution['gaps'])
        self.assertEqual('RESERVATION_GAP', resolution['admission']['outcome_reservation']['status'])
        self.assertNotIn('plan_bindings', resolution['admission']['outcome_reservation'])
        for flag in ('scientific_readiness', 'frozen', 'allocation_reserved'):
            self.assertIs(result['body'][flag], False)
        for schema in ('scientific-allocation/1', 'scientific-trial/1', 'frozen-manifest/1'):
            self.assertEqual([], self.broker._freeze_objects(schema))
        self.assertEqual(plan, self.broker.call(self.token, 'get_artifact', artifact_id=plan['id']))
        self.assertEqual(self.compiled,
            self.broker.call(self.token, 'get_artifact', artifact_id=self.compiled['id']))


if __name__ == '__main__':
    unittest.main()
