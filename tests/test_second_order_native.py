"""Existing second-order law through the actual owned synthetic family caller.

This is source/caller conformance. It neither fits market dependence nor grants
scientific admission. The fixed raw fixture is distinct from the Q1 diagnostics.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import unittest

from binding_support import BindingFixture
from trading_researcher.codec import decode, digest
from trading_researcher.second_order_population import specification


class SecondOrderNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = ''.join(
            f'{1577836800000 + index * 900000},100,101,99,{101 if index % 2 == 0 else 99},0,'
            f'{1577837699999 + index * 900000},0,0,0,0,0\n'
            for index in range(4))
        cls.fixture = BindingFixture({'change': {'source_raw_csv': raw, 'delay_seconds': 0}})
        cls.addClassCleanup(cls.fixture.close)
        cls.broker, cls.token = cls.fixture.broker, cls.fixture.token
        candidate = deepcopy(cls.fixture.base['candidate'])
        candidate['estimand']['unit'] = 'ratio'
        candidate['feature_refs'] = ['BTCUSDT.close@binance-spot-15m-v1',
                                     'BTCUSDT.open@binance-spot-15m-v1']
        comparison = {'op': 'gt',
            'left': {'op': 'feature', 'ref': candidate['feature_refs'][0]},
            'right': {'op': 'feature', 'ref': candidate['feature_refs'][1]}}
        candidate['condition_ast']['expression'] = {'op': 'gt',
            'left': {'op': 'lag', 'bars': 1, 'arg': deepcopy(comparison['left'])},
            'right': {'op': 'lag', 'bars': 1, 'arg': deepcopy(comparison['right'])}}
        candidate['outcome']['scale'] = 'binary_probability'
        candidate['outcome']['program']['expression'] = comparison
        candidate['parameter_origins'] = [item for item in candidate['parameter_origins']
            if item['path'] != '/condition_ast/expression/right/value']
        for side in ('left', 'right'):
            candidate['parameter_origins'].append({
                'path': '/condition_ast/expression/' + side + '/bars',
                'basis': 'preexisting_specification', 'source_refs': [],
                'rationale': 'Fixed synthetic source identity; no empirical lag selection.'})
        change = {'change': {'candidate': candidate,
            'original_idea_text': 'Synthetic native lag-law fixture: previous-bar up versus next-bar up. '
                                  'Equal rows, literal-true scope, retained unknowns; no market claim.'}}
        formalization = cls.fixture.create_formalization(change)
        cls.compiled = cls.fixture.compile(formalization, change)
        if cls.compiled['body']['status'] != 'COMPILED':
            raise AssertionError(cls.compiled['body'])
        cls.execution = cls.op('execute_development', compiled_id=cls.compiled['id'])
        cls.plan = cls.op('prepare_evaluation_plan', key='second-order-native-plan',
            compiled_id=cls.compiled['id'], primary_count=2,
            dependence={'base_length': 2, 'rationale': 'Fixed synthetic conformance design, not fitted.',
                'development_refs': [cls.execution['id']],
                'randomness': {'algorithm': 'python-random-mt19937',
                    'version': 'CPython/3.14.2/state-3', 'seed': 2026110200}})
        cls.diagnostics = cls.op('prepare_information_diagnostics', key='second-order-native-diagnostics',
            plan_id=cls.plan['id'], execution_id=cls.execution['id'],
            lags=[1, 2, 4], limits={'max_seconds': 60})

    @classmethod
    def op(cls, operation, **arguments):
        return cls.broker.call(cls.token, operation, **arguments)

    def request(self, key, beta=Fraction(1, 2)):
        return {'key': key, 'plan_id': self.plan['id'], 'execution_id': self.execution['id'],
            'diagnostics_id': self.diagnostics['id'],
            'specification': specification(2, beta, Fraction(1, 2),
                'Fixed second-order native conformance stress; no market fit.'),
            'components': [{'id': 'null', 'scenario': 0}, {'id': 'alternative', 'scenario': 2}],
            'time_rows': 64, 'seed': 2026110201, 'bootstrap_seed': 2026110202,
            'mc_noncoverage': {'numerator': '1', 'denominator': '100'},
            'limits': {'max_seconds': 180}}

    def test_owned_generation_full_calculation_and_separate_replay(self):
        request = self.request('second-order-native-mixed')
        saved = self.op('run_population_family', **request)
        body = saved['body']
        result = body['result']
        self.assertEqual(result['model']['schema'], 'lag-linked-second-order-model/1')
        self.assertEqual(result['model']['status'], 'MODEL_SPECIFIED')
        self.assertEqual(result['model']['source_process_scope']['identity']
                         ['condition_equals_outcome_at_offset_bars'], -2)
        self.assertEqual(result['world']['initialization']['history_order'], 2)
        self.assertEqual(result['world']['initialization']['law']['coordinate_count'], 2)
        self.assertFalse(result['scientific_readiness'])
        self.assertIsNone(result['n_min'])
        self.assertEqual(body['verification']['result'], {'verified_result_hash':
            digest(result)})
        raw = self.broker._read_blob_bytes(body['world_blob']['sha256'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), body['world_blob']['sha256'])
        records = [decode(line) for line in raw.splitlines()]
        self.assertEqual(sum(item['kind'] == 'case' for item in records), 128)
        self.assertTrue(any(item['kind'] != 'case' for item in records))
        for component in result['bootstraps']:
            self.assertEqual([item['attempted'] for item in component['result']['cases']],
                             [19999, 19999, 19999])
        self.assertEqual(self.op('run_population_family', **request), saved)

    def test_infeasible_history_keeps_owned_gap_without_draws_or_rescue(self):
        request = self.request('second-order-native-infeasible', Fraction(-9, 10))
        saved = self.op('run_population_family', **request)
        result = saved['body']['result']
        self.assertEqual(result['status'], 'MODEL_OR_INFORMATION_GAP')
        self.assertIn('infeasible_second_order_transition', result['model']['gaps'])
        self.assertIsNone(result['world'])
        self.assertFalse(result['scientific_readiness'])
        self.assertEqual(saved['body']['world_blob']['size'], 0)
        self.assertEqual(saved['body']['request'], request)


if __name__ == '__main__':
    unittest.main()
