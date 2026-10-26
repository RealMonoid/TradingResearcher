"""Actual fixed-draw family computation, retained inputs and fresh process replay."""
from copy import deepcopy
import hashlib
import json
import unittest
from unittest.mock import patch

from family_run_support import FamilyFixture
from trading_researcher.codec import Invalid, decode
from trading_researcher.errors import Conflict, Denied
from trading_researcher import population_runs


class FamilyRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.fixture = FamilyFixture()
    @classmethod
    def tearDownClass(cls): cls.fixture.close()

    def test_owned_family_retains_interruption_and_replays_actual_draws(self):
        fixture = self.fixture; args = fixture.args('actual')
        with patch.object(population_runs, 'run_child', side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError): fixture.op('run_population_family', **args)
        with self.assertRaises(Conflict): fixture.op('run_population_family', **{**args, 'seed': 103})
        captured = []
        real = population_runs.run_child
        def capture(*pos, **kw):
            result = real(*pos, **kw)
            if kw.get('verify') is None: captured.append(result)
            return result
        with patch.object(population_runs, 'source_bundle', side_effect=AssertionError('retry used fresh source')):
            with patch.object(population_runs, 'run_child', side_effect=capture):
                saved = fixture.op('run_population_family', **args)
        body = saved['body']; result = body['result']
        self.assertEqual(body['schema'], 'development-population-family/1')
        self.assertFalse(result['scientific_readiness'])
        self.assertIsNone(result['n_min'])
        self.assertEqual(result['outer_world_count'], 1)
        self.assertEqual(result['status'], 'COMPUTED_UNCALIBRATED')
        self.assertEqual([item['state'] for item in result['outcomes']], ['VERIFIED', 'VERIFIED'])
        self.assertEqual(len(result['outcomes']), 2)
        self.assertEqual({item['truth']['denominator'] for item in result['outcomes']}, {'10', '20'})
        for item in result['bootstraps']:
            computation = item['result']
            self.assertEqual(computation['design']['primary_count'], 2)
            self.assertEqual(computation['marginal_noncoverage'], {'numerator': '1', 'denominator': '40'})
            self.assertEqual(computation['required_lengths'], [1, 2])
            self.assertEqual([x['attempted'] for x in computation['cases']], [19999]*2)
        capsule = fixture.op('get_artifact', artifact_id=body['input_capsule_id'])
        self.assertEqual(capsule['body']['request'], args)
        self.assertIn(fixture.diagnostics['id'], capsule['source_refs'])
        raw = fixture.broker._read_blob_bytes(body['world_blob']['sha256'])
        self.assertEqual(len(raw), body['world_blob']['size'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), body['world_blob']['sha256'])
        paths = {}; case_count = 0
        for line in raw.splitlines():
            record = decode(line)
            if record['kind'] == 'case': case_count += 1
            else:
                value = record['value']; key = (value['length'], value['index'])
                if key in paths: self.assertEqual(paths[key], value['path_sha256'])
                else: paths[key] = value['path_sha256']
        self.assertEqual(case_count, 128)
        self.assertEqual(len(paths), 39998)
        print(json.dumps({'family_status': result['status'], 'outcomes': result['outcomes'],
            'events': result['events'], 'outer_world_count': 1, 'case_count': case_count,
            'draw_count': 2*len(paths), 'retained_stream_bytes': len(raw)}))
        self.assertEqual(fixture.op('run_population_family', **args), saved)
        # A committed output replayed from another key cannot authenticate changed bytes.
        calculated, original = captured[0]
        forged = original.replace(b'"source_time_index":', b'"source_time_index":9', 1)
        response = deepcopy(calculated)
        response['world_blob'] = {'sha256': hashlib.sha256(forged).hexdigest(), 'size': len(forged)}
        def corrupt(*pos, **kw):
            return (response, forged) if kw.get('verify') is None else real(*pos, **kw)
        with patch.object(population_runs, 'run_child', side_effect=corrupt):
            with self.assertRaises(Invalid): fixture.op('run_population_family', **fixture.args('tampered'))

    def test_family_admission_binds_size_effects_and_operator(self):
        fixture = self.fixture
        worker = fixture.op('register_worker', name='family-denied', role='discovery', capabilities=['research-record/v1'])['token']
        with self.assertRaises(Denied): fixture.broker.call(worker, 'run_population_family', **fixture.args('worker'))
        source = fixture.op('add_source', body={'unowned': 'diagnostics'}, data_class='development')
        with patch.object(fixture.broker, '_read_blob_bytes', side_effect=AssertionError('premature read')):
            with self.assertRaises(Denied): fixture.op('run_population_family', **{**fixture.args('unowned'), 'diagnostics_id': source['id']})
        for schema in ('population-family-input/1', 'development-population-family/1'):
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                fixture.op('add_source', body={'schema': schema}, data_class='development')
        for changes in ({'components': [{'id': str(i), 'scenario': 0} for i in range(3)]},
                        {'components': [{'id': 'a', 'scenario': 0}, {'id': 'b', 'scenario': 3}]},
                        {'time_rows': 50001}, {'bootstrap_seed': 101}, {'mc_noncoverage': {'numerator': '0', 'denominator': '1'}},
                        {'delta': {'numerator': '1', 'denominator': '1000'}}):
            with self.subTest(changes=changes), self.assertRaises(Invalid):
                fixture.op('run_population_family', **{**fixture.args('bad'), **changes})


if __name__ == '__main__': unittest.main()
