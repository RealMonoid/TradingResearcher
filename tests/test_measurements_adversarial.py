"""Independent predeclared temporal oracles and provider-capability faults."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as F
import unittest
from unittest.mock import patch

import test_measurements as setup_support
from trading_researcher import measurements
from trading_researcher.codec import digest, Invalid
from trading_researcher.errors import Conflict, Denied
from trading_researcher.measurements import measure, validate_request


BASE = 1640995200
CATALOG = {'price@1': {'type': 'real', 'unit': 'ratio'},
           'flag@1': {'type': 'boolean', 'unit': None}}
PRICE = {'op': 'feature', 'ref': 'price@1'}


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def request(expression=None, start=1, stop=7, warmup=1, instruments=None, catalog=None):
    return {'snapshot_id': 'independent-temporal-fixture',
            'universe': {'start': iso(BASE+900*start), 'end': iso(BASE+900*stop),
                         'instruments': ['BTCUSDT', 'ETHUSDT'] if instruments is None else instruments},
            'warmup_bars': warmup,
            'program': {'schema': 'research-ast/1', 'catalog_hash': digest(CATALOG if catalog is None else catalog),
                        'expression': deepcopy(PRICE if expression is None else expression)}}


def fixture_rows():
    rows = []
    for index in range(7):
        when = BASE+900*index
        if index != 2:
            price = {0: '10', 1: '20', 3: None, 4: '40', 5: '50', 6: '60'}[index]
            available = BASE+900*(index+1 if index in (1, 5) else index)
            features = {'price@1': {'value': price, 'available_at': available}}
            if index != 4:
                features['flag@1'] = {'value': index != 3, 'available_at': when}
            rows.append({'time': when, 'instrument': 'BTCUSDT', 'features': features})
        rows.append({'time': when, 'instrument': 'ETHUSDT',
                     'features': {'price@1': {'value': str(100+10*index), 'available_at': when},
                                  'flag@1': {'value': True, 'available_at': when}}})
    return rows


def number(value):
    return F(int(value['numerator']), int(value['denominator']))


def projected(result, instrument):
    return [row['missing'] if row['missing'] else number(row['value'])
            for row in result['values'] if row['instrument'] == instrument]


class MeasurementAdversarialTests(unittest.TestCase):
    def test_fixed_raw_lag_and_window_oracles_preserve_missing_current_grid(self):
        cases = [
            (PRICE, ['not_yet_available', 'missing_observation', 'missing_value', 40, 'not_yet_available', 60]),
            ({'op': 'lag', 'bars': 1, 'arg': PRICE},
             [10, 'missing_observation', 'missing_observation', 'missing_value', 40, 50]),
            ({'op': 'lag', 'bars': 2, 'arg': PRICE},
             ['missing_observation', 'missing_observation', 20, 'missing_observation', 'missing_value', 40]),
            ({'op': 'trailing_mean', 'bars': 2, 'arg': PRICE},
             ['incomplete_window', 'missing_observation', 'incomplete_window', 'incomplete_window', 'incomplete_window', 55]),
        ]
        for expression, expected in cases:
            query = request(expression)
            rows = fixture_rows()
            before = deepcopy([CATALOG, rows, query])
            with self.subTest(expression=expression):
                result = measure(CATALOG, rows, query)
                self.assertEqual(result['status'], 'MEASURED_DEVELOPMENT')
                self.assertEqual(projected(result, 'BTCUSDT'), expected)
                self.assertEqual(result['expected_positions'], 12)
                self.assertEqual(result['processed_positions'], 12)
                self.assertEqual(result['uncomputed_positions'], 0)
                self.assertTrue(result['processing_complete'])
                self.assertFalse(result['scientific_readiness'])
                self.assertFalse(result['classification_permitted'])
                self.assertEqual([CATALOG, rows, query], before)
        raw = measure(CATALOG, fixture_rows(), request())
        self.assertEqual(number(raw['summary']['mean']), F(455, 4))
        self.assertEqual(raw['summary']['defined'], 8)
        lag = measure(CATALOG, fixture_rows(), request({'op': 'lag', 'bars': 1, 'arg': PRICE}))
        self.assertEqual(projected(lag, 'ETHUSDT'), [100, 110, 120, 130, 140, 150])

    def test_exact_returns_use_same_instrument_and_original_decision_cutoff(self):
        expression = {'op': 'sub', 'left': {'op': 'div', 'left': PRICE,
                      'right': {'op': 'lag', 'bars': 1, 'arg': PRICE}},
                      'right': {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '1'}}
        result = measure(CATALOG, fixture_rows(), request(expression))
        self.assertEqual(projected(result, 'ETHUSDT'), [F(1, n) for n in range(10, 16)])
        self.assertEqual(projected(result, 'BTCUSDT')[-1], F(1, 5))
        last = next(row for row in result['values'] if row['instrument'] == 'BTCUSDT' and row['time'] == BASE+5400)
        self.assertEqual(last['trace']['latest_available_at'], BASE+5400)

    def test_warmup_does_not_silently_expand_and_absent_current_row_is_not_padded(self):
        lag = {'op': 'lag', 'bars': 1, 'arg': PRICE}
        result = measure(CATALOG, fixture_rows(), request(lag, warmup=0))
        self.assertEqual(projected(result, 'BTCUSDT')[0], 'missing_observation')
        self.assertEqual(projected(result, 'ETHUSDT')[0], 'missing_observation')
        literal = {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '1'}
        result = measure(CATALOG, fixture_rows(), request(literal, start=2, stop=3, instruments=['BTCUSDT']))
        self.assertEqual(projected(result, 'BTCUSDT'), ['missing_observation'])
        empty = measure(CATALOG, [], request(literal))
        self.assertEqual(empty['status'], 'MEASUREMENT_GAP')
        self.assertEqual(empty['reason']['code'], 'DATA_GAP')
        self.assertEqual(empty['expected_positions'], 12)
        self.assertEqual(empty['uncomputed_positions'], 12)
        self.assertFalse(empty['processing_complete'])

    def test_decisive_boolean_retains_hidden_missing_and_late_dependency_traces(self):
        false = {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': False}
        true = {**false, 'value': True}
        query = request({'op': 'and', 'left': false, 'right': {'op': 'feature', 'ref': 'flag@1'}},
                        start=4, stop=5, warmup=0, instruments=['BTCUSDT'])
        result = measure(CATALOG, fixture_rows(), query)
        self.assertIs(result['values'][0]['value'], False)
        self.assertIsNone(result['values'][0]['missing'])
        self.assertEqual(result['values'][0]['trace']['events']['missing_feature_value'], 1)
        self.assertEqual(result['summary']['false'], 1)
        query = request({'op': 'or', 'left': true, 'right': {'op': 'gt', 'left': PRICE,
                        'right': {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '0'}}},
                        start=5, stop=6, warmup=0, instruments=['BTCUSDT'])
        result = measure(CATALOG, fixture_rows(), query)
        self.assertIs(result['values'][0]['value'], True)
        self.assertEqual(result['values'][0]['trace']['events']['not_yet_available'], 1)
        self.assertEqual(result['values'][0]['trace']['latest_available_at'], BASE+5400)

    def test_shared_step_budget_stops_after_194_complete_mean512_cells(self):
        catalog = {'price@1': {'type': 'real', 'unit': 'ratio'}}
        rows = [{'time': BASE+900*i, 'instrument': 'BTCUSDT',
                 'features': {'price@1': {'value': '1', 'available_at': BASE+900*i}}} for i in range(768)]
        query = request({'op': 'trailing_mean', 'bars': 512, 'arg': PRICE},
                        start=512, stop=768, warmup=512, instruments=['BTCUSDT'], catalog=catalog)
        result = measure(catalog, rows, query)
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertEqual(result['reason']['code'], 'RESOURCE_GAP')
        self.assertEqual((result['processed_positions'], result['uncomputed_positions']), (194, 62))
        self.assertEqual(result['primitive_steps'], 100000)
        self.assertEqual(result['interrupted_position'], {'time': BASE+900*(512+194), 'instrument': 'BTCUSDT'})
        self.assertEqual(result['summary']['scope'], 'completed_prefix_only')
        self.assertEqual(number(result['summary']['mean']), 1)

    def test_unreachable_future_nodes_and_mismatched_catalog_are_typed_gaps(self):
        expression = {'op': 'and', 'left': {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': False},
                      'right': {'op': 'future', 'arg': PRICE, 'bars': 1}}
        result = measure(CATALOG, fixture_rows(), request(expression))
        self.assertEqual(result['reason']['code'], 'TEMPORAL_GAP')
        self.assertEqual(result['processed_positions'], 0)
        query = request()
        query['program']['catalog_hash'] = 'wrong'
        result = measure(CATALOG, fixture_rows(), query)
        self.assertEqual(result['reason']['code'], 'FEATURE_GAP')
        for change in ({'warmup_bars': True}, {'warmup_bars': 513}):
            with self.subTest(change=change), self.assertRaises(Invalid):
                validate_request({**request(), **change})
        validate_request(request(start=0, stop=128, warmup=0))
        with self.assertRaises(Invalid):
            validate_request(request(start=0, stop=129, warmup=0))


class MeasurementOwnerAdversarialTests(unittest.TestCase):
    def setUp(self):
        setup_support.MeasurementRunTests.setUp(self)

    def tearDown(self):
        self.fixture.tearDown()

    def op(self, operation, **args):
        return self.broker.call(self.admin, operation, **args)

    def record_call(self, request=None, tool_id='independent-measurement'):
        return setup_support.MeasurementRunTests.record_call(self, request, tool_id)

    def retained_response(self, *, usage=None, late=False, duplicate=False):
        client = self.clients['first']
        lease = client.call('claim')['lease']
        intent = client.call('reserve_research_call', lease=lease, key='independent-response', request={
            'model': self.profile['model'], 'prompt_version': self.profile['prompt_version'],
            'messages': [{'role': 'system', 'content': 'Explore'}], 'tools': self.profile['tools'],
            'generation_parameters': {}}, input_token_bound=10000, output_token_limit=4096, cost_bound_units=0)
        if late:
            self.fixture.now += 16
        tool = {'id': 'independent-tool', 'name': 'measure_development',
                'arguments': setup_support.query(self.snapshot['id'])}
        client.call('finish_research_call', lease=lease, call_id=intent['call_id'], response={
            'status': 'completed', 'output': {'status': 'tools', 'calls': [tool, tool] if duplicate else [tool]}},
            usage={'input_tokens': 1, 'output_tokens': 1, 'cost_units': 0} if usage is None else usage)
        return {'lease': lease, 'call_id': intent['call_id'], 'tool_id': tool['id']}

    def test_halting_epoch_during_compute_retains_audit_but_denies_every_worker_read(self):
        args = self.record_call()
        original = self.broker._load_reference_data
        def halt(*values, **options):
            loaded = original(*values, **options)
            with self.broker._transaction():
                self.broker._db.execute("UPDATE research_epochs SET state='halted' WHERE id=?", (self.epoch['id'],))
            return loaded
        with patch.object(self.broker, '_load_reference_data', side_effect=halt), self.assertRaises(Denied):
            self.clients['first'].call('measure_development', **args)
        saved = self.broker._measurement_find(measurements.RESULT, args['call_id'], args['tool_id'])
        self.assertFalse(saved['body']['delivered'])
        self.assertEqual(saved['body']['result']['status'], 'MEASURED_DEVELOPMENT')
        # The lease is still live. Secrecy of the artifact ID is not authorization.
        with self.assertRaises(Denied):
            self.clients['first'].call('read_artifact', lease=args['lease'], artifact_id=saved['id'])
        self.assertEqual(self.op('get_artifact', artifact_id=saved['id']), saved)

    def test_peer_with_its_own_live_lease_cannot_read_or_reexecute_private_measurement(self):
        args = self.record_call()
        saved = self.clients['first'].call('measure_development', **args)
        # The adopted broker runs perspectives sequentially. End the first
        # active attempt without releasing its private work to the second.
        self.clients['first'].call('block', lease=args['lease'], reason='Independent isolation fixture',
                                   needs=['retained review'], retry_when='Separate explicit continuation')
        other = self.clients['second'].call('claim')['lease']
        with self.assertRaises(Denied):
            self.clients['second'].call('read_artifact', lease=other, artifact_id=saved['id'])
        with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Peer data read')):
            with self.assertRaises(Denied):
                self.clients['second'].call('measure_development', **{**args, 'lease': other})

    def test_unknown_tool_or_unlisted_snapshot_is_denied_before_raw_access(self):
        query = setup_support.query('not-in-frozen-context')
        args = self.record_call(query)
        with patch.object(self.broker, '_read_blob_bytes', side_effect=AssertionError('Unauthorized raw access')), \
                patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Unauthorized loader')):
            with self.assertRaises(Denied):
                self.clients['first'].call('measure_development', **args)
            with self.assertRaises(Denied):
                self.clients['first'].call('measure_development', **{**args, 'tool_id': 'invented'})

    def test_duplicate_tool_ids_are_rejected_before_loading(self):
        args = self.retained_response(duplicate=True)
        with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Ambiguous request read')):
            with self.assertRaises(Invalid):
                self.clients['first'].call('measure_development', **args)

    def test_late_response_with_live_lease_cannot_trigger_measurement(self):
        args = self.retained_response(late=True)
        with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Late response read')):
            with self.assertRaises(Denied):
                self.clients['first'].call('measure_development', **args)

    def test_provider_accounting_overrun_cannot_trigger_measurement(self):
        args = self.retained_response(usage={'input_tokens': 10001, 'output_tokens': 1, 'cost_units': 0})
        with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Overrun read')):
            with self.assertRaises(Denied):
                self.clients['first'].call('measure_development', **args)

    def test_unresolved_computation_is_not_reexecuted_and_next_generation_cannot_read_it(self):
        args = self.record_call()
        with patch.object(measurements, 'measure', side_effect=KeyboardInterrupt('Independent interrupted calculation')):
            with self.assertRaises(KeyboardInterrupt):
                self.clients['first'].call('measure_development', **args)
        capsule = self.broker._measurement_find(measurements.INPUT, args['call_id'], args['tool_id'])
        self.assertIsNotNone(capsule)
        with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Unresolved repeat')):
            with self.assertRaises(Conflict):
                self.clients['first'].call('measure_development', **args)
        self.fixture.now += 31
        fresh = self.clients['first'].call('claim')['lease']
        self.assertNotEqual(fresh['generation'], args['lease']['generation'])
        with self.assertRaises(Denied):
            self.clients['first'].call('read_artifact', lease=fresh, artifact_id=capsule['id'])
        with self.assertRaises(Denied):
            self.clients['first'].call('measure_development', **{**args, 'lease': fresh})

    def test_source_capsule_precedes_calculation_and_duplicate_result_needs_no_new_load(self):
        args = self.record_call()
        original = measurements.measure
        def inspect(*values, **options):
            capsule = self.broker._measurement_find(measurements.INPUT, args['call_id'], args['tool_id'])
            self.assertEqual(capsule['body']['request'], self.request)
            self.assertIn('trading_researcher/expressions.py', capsule['body']['source_files'])
            return original(*values, **options)
        with patch.object(measurements, 'measure', side_effect=inspect):
            saved = self.clients['first'].call('measure_development', **args)
        with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Duplicate load')):
            self.assertEqual(self.clients['first'].call('measure_development', **args), saved)


if __name__ == '__main__':
    unittest.main()
