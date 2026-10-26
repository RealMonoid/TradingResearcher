"""Independent fault injection at the study pipeline and durable owner boundary."""
from copy import deepcopy
import hashlib
import io
from pathlib import Path
import unittest
from unittest.mock import patch

import test_information_study_adversarial as fixed
import test_study_runs as setup_support
from trading_researcher import study_pipeline, study_runs
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict
from trading_researcher.information_study import make_manifest
from trading_researcher.study_stream import EncodedStream, decode_stream


class StudyPipelineAdversarialTests(unittest.TestCase):
    def manifest(self):
        config = fixed.profile()
        config['targets'] = [8]
        config['budget'].update(attempt_compute_ms=1000)
        return make_manifest(fixed.assigned(), config)

    def test_resource_stops_are_technical_while_completed_abstentions_are_statistical(self):
        manifest = self.manifest()
        world = manifest['worlds'][0]
        cases = [
            ('RESOURCE_STOP', 'computation_time_limit', 'TECHNICAL_FAILURE'),
            ('RESOURCE_STOP', 'computation_segment_limit', 'TECHNICAL_FAILURE'),
            ('RESOURCE_STOP', 'monte_carlo_numeric_envelope', 'TECHNICAL_FAILURE'),
            ('INFORMATION_GAP', 'undefined_resampled_mean', 'INFORMATION_GAP'),
            ('INPUT_GAP', 'no_scope_cases', 'INFORMATION_GAP'),
            ('INPUT_GAP', 'no_conditioned_cases', 'INFORMATION_GAP'),
            ('INPUT_GAP', 'outcomes_pending', 'TECHNICAL_FAILURE'),
        ]
        for status, reason, expected in cases:
            generated = {'report': {'cases': [{'independent': 'case'}]},
                         'truth': {'effect': fixed.rational(0)}}
            calculated = {'status': status, 'reason': reason,
                          'descriptive': {'scope_count': 0, 'condition_count': 0}}
            sink = []
            with self.subTest(status=status, reason=reason), \
                    patch.object(study_pipeline, 'build_model', return_value={'status': 'MODEL_SPECIFIED'}), \
                    patch.object(study_pipeline, 'generate_world', return_value=generated), \
                    patch.object(study_pipeline, 'calculate', return_value=calculated):
                result = study_pipeline.calculate_world({'report': {}, 'diagnostics': {}},
                                                        manifest, world, [], sink.append)
                self.assertEqual(result['outcome']['state'], expected)
                self.assertIsNone(result['outcome']['decision'])
                self.assertIsNone(result['outcome']['covered'])
                self.assertEqual(sink, [{'kind': 'case', 'value': {'independent': 'case'}}])

    def test_completed_mc_instability_is_inconclusive_and_coverage_uses_population_truth(self):
        manifest = self.manifest()
        world = next(w for w in manifest['worlds'] if w['scenario'] == 2)
        generated = {'report': {'cases': []}, 'truth': {'effect': fixed.rational(fixed.F(1, 10))}}
        calculated = {'status': 'COMPUTED_UNCALIBRATED',
                      'descriptive': {'scope_count': 6, 'condition_count': 3, 'effect': fixed.rational(0)},
                      'interval': {'lower': fixed.rational(fixed.F(1, 20)),
                                   'upper': fixed.rational(fixed.F(3, 20))},
                      'monte_carlo': {'nominal_classification': 'SUPPORTED_INITIAL', 'boundary_stable': False}}
        with patch.object(study_pipeline, 'build_model', return_value={'status': 'MODEL_SPECIFIED'}), \
                patch.object(study_pipeline, 'generate_world', return_value=generated), \
                patch.object(study_pipeline, 'calculate', return_value=calculated):
            result = study_pipeline.calculate_world({'report': {}, 'diagnostics': {}},
                                                    manifest, world, [], lambda value: None)
        self.assertEqual(result['outcome']['state'], 'VERIFIED')
        self.assertEqual(result['outcome']['decision'], 'TESTED_INCONCLUSIVE')
        self.assertTrue(result['outcome']['covered'])
        self.assertFalse(result['scientific_readiness'])
        self.assertIsNone(result['n_min'])

    def test_stream_reservation_covers_four_logical_copies(self):
        config = fixed.profile()
        config['budget'].update(max_storage_bytes=32*1024**2, attempt_storage_bytes=16*1024**2)
        manifest = make_manifest(fixed.assigned(), config)
        source = {'trading_researcher/__init__.py': b'# fixed source\n'}
        cases = b'{}\n'
        class Inspected(Exception):
            pass
        def inspect(command, directory, timeout):
            request = decode(Path(command[-1]).read_bytes())
            # Generation/replay each materialize the stream and each output
            # is retained: four S-byte copies, plus the declared fixed envelope.
            fixed_bytes = 2*(sum(map(len, source.values()))+len(cases)+3*1024**2)+1024**2
            self.assertLessEqual(4*request['stream_limit']+fixed_bytes,
                                 manifest['profile']['budget']['attempt_storage_bytes'])
            raise Inspected()
        with patch.object(study_runs, '_run_child', side_effect=inspect), self.assertRaises(Inspected):
            study_runs.execute_attempt(source, {}, manifest, manifest['worlds'][0], cases,
                                       lambda: 10, {'materialized_bytes': 0}, [])


class StudyRunAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse setup only; do not import or inherit another unittest class.
        setup_support.StudyRunTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.close()

    @classmethod
    def op(cls, operation, **args):
        return cls.broker.call(cls.token, operation, **args)

    def args(self, key):
        return setup_support.StudyRunTests.args(self, 'independent-' + key)

    def test_all_known_failed_attempts_remain_charged_and_exhausted_world_is_not_reseeded(self):
        args = self.args('retry-cap')
        args['profile']['budget']['max_attempts'] = 2
        study = self.op('prepare_information_study', **args)
        observed = []
        def fail(source, payload, manifest, world, cases, remaining, meter, outputs):
            observed.append(deepcopy(world))
            outputs.append(('fault/prefix', b'independent retained failed prefix'))
            meter['materialized_bytes'] += 37
            raise RuntimeError('Independent known child failure')
        with patch.object(study_runs, 'execute_attempt', side_effect=fail) as child:
            first = self.op('advance_information_study', study_id=study['id'])
            final = self.op('advance_information_study', study_id=study['id'])
            self.assertEqual(self.op('advance_information_study', study_id=study['id']), final)
        self.assertEqual(child.call_count, 2)
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(final['status'], 'TECHNICAL_FAILURE')
        self.assertFalse(final['summary']['complete'])
        self.assertEqual(final['summary']['recorded_worlds'], 1)
        self.assertEqual(len(final['attempt_artifact_ids']), 2)
        attempts = [self.op('get_artifact', artifact_id=identity)['body']
                    for identity in final['attempt_artifact_ids']]
        self.assertEqual(final['budget']['charged_compute_ms'],
                         sum(x['settlement']['compute_ms'] for x in attempts))
        self.assertEqual(final['budget']['charged_storage_bytes'], study['body']['initial_storage_bytes'] +
                         sum(x['settlement']['storage_bytes'] for x in attempts))
        self.assertTrue(all(x['failure']['type'] == 'RuntimeError' for x in attempts))
        self.assertTrue(all('fault/prefix' in x['output_blobs'] for x in attempts))
        alias = self.op('prepare_information_study', **{**args, 'key': 'independent-retry-alias'})
        self.assertEqual(alias['id'], study['id'])
        self.assertEqual(self.op('inspect_information_study', study_id=alias['id']), final)
        self.assertGreater(final['budget']['charged_storage_bytes'], first['budget']['charged_storage_bytes'])

    def test_settlement_cannot_reuse_an_already_closed_attempt(self):
        study = self.op('prepare_information_study', **self.args('stale'))
        with patch.object(study_runs, 'execute_attempt', side_effect=RuntimeError('Known closed failure')):
            before = self.op('advance_information_study', study_id=study['id'])
        attempt = self.op('get_artifact', artifact_id=before['attempt_artifact_ids'][0])['body']
        with self.assertRaisesRegex(Invalid, 'Stale|settled'), self.broker._transaction():
            self.broker._settle_study(study, attempt['attempt_id'], attempt['settlement'],
                                      attempt['outcome'], before['attempt_artifact_ids'][0])
        self.assertEqual(self.op('inspect_information_study', study_id=study['id']), before)

    def test_staging_failure_leaves_reservation_and_recovery_never_refunds_or_restarts(self):
        study = self.op('prepare_information_study', **self.args('staging'))
        def failed_output(source, payload, manifest, world, cases, remaining, meter, outputs):
            outputs.append(('fault/retained-prefix', b'partial output'))
            raise RuntimeError('Known pipeline failure before staging')
        with patch.object(study_runs, 'execute_attempt', side_effect=failed_output), \
                patch.object(self.broker, '_stage_blob_bytes', side_effect=RuntimeError('Staging interrupted')):
            with self.assertRaisesRegex(RuntimeError, 'Staging interrupted'):
                self.op('advance_information_study', study_id=study['id'])
        pending = self.op('inspect_information_study', study_id=study['id'])
        self.assertEqual(pending['status'], 'RUNNING')
        with self.assertRaises(Conflict):
            self.op('advance_information_study', study_id=study['id'])
        self.broker._recover_information_studies()
        recovered = self.op('inspect_information_study', study_id=study['id'])
        self.assertEqual(recovered['status'], 'ORPHAN_UNCERTAIN')
        budget = study['body']['manifest']['profile']['budget']
        self.assertEqual(recovered['budget']['charged_compute_ms'], budget['attempt_compute_ms'])
        self.assertEqual(recovered['budget']['charged_storage_bytes'],
                         budget['attempt_storage_bytes'] + study['body']['initial_storage_bytes'])
        self.broker._recover_information_studies()
        with patch.object(study_runs, 'execute_attempt', side_effect=AssertionError('Orphan retry')):
            self.assertEqual(self.op('advance_information_study', study_id=study['id']), recovered)

    def test_unreadable_materialization_metadata_never_refunds_unknown_usage(self):
        study = self.op('prepare_information_study', **self.args('unknown-meter'))
        real_stat = Path.stat
        faults = []
        def inaccessible(path, *args, **kwargs):
            if path.name == '__init__.py' and any(part.startswith('trf-study-') for part in path.parts):
                faults.append(str(path))
                raise OSError('Independent materialization accounting failure')
            return real_stat(path, *args, **kwargs)
        with patch.object(study_runs, '_run_child', side_effect=RuntimeError('Known child did not start')), \
                patch.object(Path, 'stat', inaccessible):
            view = self.op('advance_information_study', study_id=study['id'])
        self.assertTrue(faults)
        attempt = self.op('get_artifact', artifact_id=view['attempt_artifact_ids'][0])['body']
        self.assertFalse(attempt['settlement']['usage_known'])
        budget = study['body']['manifest']['profile']['budget']
        self.assertGreaterEqual(view['budget']['charged_compute_ms'], budget['attempt_compute_ms'])
        self.assertGreaterEqual(view['budget']['charged_storage_bytes'],
                                budget['attempt_storage_bytes'] + study['body']['initial_storage_bytes'])

    def test_completed_information_gap_advances_without_retrying_the_same_world(self):
        study = self.op('prepare_information_study', **self.args('information-gap'))
        world = study['body']['manifest']['worlds'][0]
        outcome = {'world_id': world['id'], 'state': 'INFORMATION_GAP', 'decision': None,
                   'scope_count': 0, 'condition_count': 0, 'covered': None}
        result = {'world_id': world['id'], 'outcome': outcome, 'scientific_readiness': False,
                  'classification_permitted': False, 'n_min': None}
        # Dispatcher fault fixture only; fake proofs are not replay evidence.
        with patch.object(study_runs, 'execute_attempt', return_value=(result, [{}, {}])):
            view = self.op('advance_information_study', study_id=study['id'])
        self.assertEqual(view['summary']['recorded_worlds'], 1)
        self.assertEqual(view['summary']['cells'][0]['states']['INFORMATION_GAP'], 1)
        self.assertNotEqual(view['next_world_id'], world['id'])
        self.assertEqual(view['budget']['attempts_per_world'][world['id']], 1)

    def test_consistently_rehashed_generation_stream_fails_real_separate_replay(self):
        study = self.op('prepare_information_study', **self.args('replay-corruption'))
        real = study_runs._run_child
        calls = []
        def corrupt(command, directory, timeout):
            request = decode(Path(command[-1]).read_bytes())
            response = real(command, directory, timeout=timeout)
            calls.append(request['verify'])
            if request['verify'] is None:
                path = directory / 'stream.jsonl.gz'
                rows = decode_stream(path.read_bytes(), response['stream_encoding']).splitlines()
                first = decode(rows[0])
                self.assertEqual(first['kind'], 'case')
                first['value']['reason'] = 'independent_consistently_rehashed_corruption'
                rows[0] = canonical(first).encode()
                decoded = b'\n'.join(rows) + b'\n'
                buffer = io.BytesIO()
                stream = EncodedStream(buffer, encoded_limit=request['stream_limit'])
                stream.write(decoded)
                response['stream_encoding'] = stream.finish()
                raw = buffer.getvalue()
                path.write_bytes(raw)
                response['stream_blob'] = {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
                (directory / 'child-output.json').write_text(canonical(response), encoding='utf-8')
            return response
        with patch.object(study_runs, '_run_child', side_effect=corrupt):
            view = self.op('advance_information_study', study_id=study['id'])
        self.assertEqual(len(calls), 1)  # Replay child raises before returning.
        self.assertFalse(view['summary']['complete'])
        self.assertEqual(view['summary']['cells'][0]['states']['TECHNICAL_FAILURE'], 1)
        self.assertIsNone(view['summary']['candidate_time_rows'])
        attempt = self.op('get_artifact', artifact_id=view['attempt_artifact_ids'][0])['body']
        self.assertIn('replay', attempt['failure']['message'])
        self.assertIn('generate/stream.jsonl.gz', attempt['output_blobs'])
        self.assertIn('replay/expected-stream.jsonl.gz', attempt['output_blobs'])
        self.assertIn('replay/child-errors.txt', attempt['output_blobs'])


if __name__ == '__main__':
    unittest.main()
