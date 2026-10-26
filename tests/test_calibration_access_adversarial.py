"""Independent protected-final-calibration access cases using disposable registries."""
from pathlib import Path
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied
from trading_researcher.errors import Conflict
from trading_researcher.calibration_runs import CalibrationStudies


SCHEMAS = ('evaluator-calibration-input/1', 'evaluator-calibration-attempt/1')


class CalibrationAccessIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.broker = Broker(Path(self.temp.name) / 'registry', clock=lambda: 1000)
        self.admin = self.broker.admin_token
        self.serial = 0

    def tearDown(self):
        self.broker.close()
        self.temp.cleanup()

    def op(self, operation, **arguments):
        return self.broker.call(self.admin, operation, **arguments)

    def unique(self, stem):
        self.serial += 1
        return f'{stem}-{self.serial}'

    def protected(self, schema=SCHEMAS[0]):
        # Trusted internal fixture creates only an access-control object, not a
        # valid owned calibration run or numerical evidence.
        with self.broker._transaction():
            descriptor = self.broker._stage_blob_bytes(b'Synthetic final-world bytes, not research evidence.')
            self.broker._register_blob(descriptor)
            return self.broker._save_artifact({
                'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
                'data_class': 'operations', 'source_refs': [], 'exposure': [],
                'blob_refs': [descriptor['sha256']], 'authority': 'synthetic_access_fixture_only',
                'body': {'schema': schema, 'fixture': True, 'created_at': 1000}})

    def wrapper(self, parent):
        return self.op('add_source', body={'text': 'Synthetic derivative', 'fixture': True},
                       data_class='development', exposure=[parent['id']])

    def assert_denied_contexts(self, artifact, epoch=1):
        for role in ('discovery', 'formalizer'):
            before = self.broker._db.execute('SELECT COUNT(*) FROM contexts').fetchone()[0]
            with self.subTest(role=role), patch.object(self.broker, '_read_blob_bytes',
                    side_effect=AssertionError('Protected blob was touched')) as reader:
                with self.assertRaises(Denied):
                    self.op('create_context', role=role, epoch=epoch, artifact_ids=[artifact['id']])
                reader.assert_not_called()
            self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM contexts').fetchone()[0], before)

    def start(self, role, identities, kind='draft/v1', batch=None):
        name = self.unique(role)
        token = self.op('register_worker', name=name, role=role,
                        capabilities=[kind, 'research-record/v1'])['token']
        context = self.op('create_context', role=role, epoch=1, artifact_ids=identities)
        spec = {'kind': kind, 'context_id': context['id'], 'purpose': 'Independent access fixture',
                'allowed_workers': [name], 'max_attempts': 1, 'lease_seconds': 10,
                'deadline': 1100, 'dependencies': []}
        if batch is not None:
            spec['batch_id'] = batch
        self.op('enqueue', key=self.unique('job'), spec=spec)
        if batch is not None:
            self.op('seal_batch', batch_id=batch)
        claimed = self.broker.call(token, 'claim')
        self.assertIsNotNone(claimed)
        return token, claimed['lease']

    def released_report(self, source):
        batch = self.op('create_batch', key=self.unique('batch'), epoch=1)['id']
        token, lease = self.start('reporter', [source['id']], 'source-report/v1', batch)
        observation = self.broker.call(token, 'record_research', lease=lease, kind='observation',
            content={'text': 'Synthetic reporter observation'}, scope={}, source_refs=[source['id']])
        body = {'records': [{'source_id': source['id'], 'body': source['body']}]}
        result = self.broker.call(token, 'put_artifact', lease=lease, body=body, source_refs=[source['id']])
        completion = self.broker.call(token, 'submit', lease=lease, artifact_id=result['id'])
        self.assertTrue(completion['accepted'])
        self.op('seal_batch', batch_id=batch)
        released = self.op('release_batch', batch_id=batch, target_epoch=2)
        self.assertIn(result['id'], released['artifact_ids'])
        self.assertIn(observation['id'], released['artifact_ids'])
        return [self.op('get_artifact', artifact_id=value['id']) for value in (result, observation)]

    def test_reserved_namespaces_cannot_be_minted_by_generic_source_or_worker_writes(self):
        token, lease = self.start('discovery', [])
        for name in SCHEMAS:
            for schema in (name, name.rsplit('/', 1)[0] + '/999'):
                body = {'schema': schema, 'scientific_readiness': True}
                with self.subTest(schema=schema), self.assertRaises(Invalid):
                    self.op('add_source', body=body, data_class='operations')
                with self.subTest(worker_schema=schema), self.assertRaises(Invalid):
                    self.broker.call(token, 'put_artifact', lease=lease, body=body, source_refs=[])

    def test_direct_controller_input_and_attempt_are_denied_without_blob_access(self):
        for schema in SCHEMAS:
            self.assert_denied_contexts(self.protected(schema))

    def test_add_source_exposure_chain_cannot_relabel_final_data_as_development(self):
        for schema in SCHEMAS:
            first = self.wrapper(self.protected(schema))
            second = self.wrapper(first)
            self.assertEqual(second['data_class'], 'development')
            self.assert_denied_contexts(first)
            self.assert_denied_contexts(second)

    def test_add_research_source_and_relationship_wrappers_preserve_protection(self):
        source = self.wrapper(self.protected())
        for field in ('source_refs', 'relations'):
            arguments = {'source_refs': [source['id']]} if field == 'source_refs' else {
                'source_refs': [], 'relations': {'depends_on': [source['id']]}}
            record = self.op('add_research', kind='observation', content={'text': 'Synthetic derived note'},
                             scope={}, **arguments)
            self.assert_denied_contexts(record)

    def test_transitive_source_refs_work_without_flattened_exposure(self):
        root = self.protected(SCHEMAS[1])
        for _ in range(3):
            with self.broker._transaction():
                root = self.broker._save_artifact({
                    'version': 'local-artifact/1', 'creator': 'operator', 'origin': 'source',
                    'data_class': 'development', 'source_refs': [root['id']], 'exposure': [],
                    'body': {'text': 'Source-ref-only trusted fixture'}})
        self.assertEqual(root['exposure'], [])
        self.assert_denied_contexts(root)

    def test_released_reporter_work_product_and_memory_cannot_release_final_ancestry(self):
        source = self.wrapper(self.protected())
        for artifact in self.released_report(source):
            self.assertEqual(artifact['origin'], 'worker')
            self.assertEqual(artifact['data_class'], 'work_product')
            self.assert_denied_contexts(artifact, epoch=2)
            derived = self.op('add_research', kind='observation', content={'text': 'Released report summary'},
                             scope={}, source_refs=[artifact['id']])
            self.assert_denied_contexts(derived, epoch=2)

    def test_benign_released_reporter_outputs_remain_usable(self):
        source = self.op('add_source', body={'text': 'Ordinary development source'}, data_class='development')
        for artifact in self.released_report(source):
            for role in ('discovery', 'formalizer'):
                context = self.op('create_context', role=role, epoch=2, artifact_ids=[artifact['id']])
                self.assertEqual(context['artifact_ids'], [artifact['id']])

    def test_workers_cannot_read_final_artifacts_or_invoke_owned_runner(self):
        protected = self.protected()
        for role in ('discovery', 'formalizer'):
            token, lease = self.start(role, [])
            requests = [('get_artifact', {'artifact_id': protected['id']}),
                        ('read_artifact', {'lease': lease, 'artifact_id': protected['id']}),
                        ('prepare_evaluator_calibration', {}),
                        ('inspect_evaluator_calibration', {'calibration_id': protected['id']}),
                        ('advance_evaluator_calibration', {'calibration_id': protected['id']})]
            with patch.object(self.broker, '_read_blob_bytes', side_effect=AssertionError('Protected blob touched')) as reader:
                for operation, arguments in requests:
                    with self.subTest(role=role, operation=operation), self.assertRaises(Denied):
                        self.broker.call(token, operation, **arguments)
                reader.assert_not_called()
            body = {'finding': 'Fixture complete', 'interpretation': 'No scientific result',
                    'uncertainty': 'Not evaluated', 'next_action': 'Retain fixture'}
            result = self.broker.call(token, 'put_artifact', lease=lease, body=body, source_refs=[])
            self.assertTrue(self.broker.call(token, 'submit', lease=lease, artifact_id=result['id'])['accepted'])


class CalibrationAliasIndependentTests(unittest.TestCase):
    def request(self):
        return {'key': 'original', 'development_study_id': 'original-development',
                'time_rows': 16, 'seed': 0,
                'budget': {'max_compute_ms': 100000, 'attempt_compute_ms': 1000,
                           'max_storage_bytes': 100000000, 'attempt_storage_bytes': 10000000,
                           'max_attempts': 1},
                'cost_estimate': {'source_ref': 'synthetic-cost', 'world_time_rows': 16,
                                  'observed_compute_ms': 100, 'observed_storage_bytes': 1000,
                                  'qualification': 'Synthetic bounded alias fixture'},
                'applicability': {'heavy_tail': {'status': 'not_applicable', 'cohort_ids': [],
                                                'reason': 'Synthetic bounded binary fixture'}}}

    def test_alias_fixed_fields_use_canonical_types_not_python_bool_integer_equality(self):
        fixed = self.request(); runner = CalibrationStudies(object())
        for field in ('budget', 'seed'):
            changed = deepcopy(fixed); changed['key'] = 'new-alias'
            if field == 'budget': changed['budget']['max_attempts'] = True
            else: changed['seed'] = False
            with self.subTest(field=field), self.assertRaises(Conflict):
                runner._study_existing_request({'body': {'request': fixed}}, changed)

    def test_alias_may_only_change_lookup_ids_after_scientific_identity_has_matched(self):
        fixed = self.request(); runner = CalibrationStudies(object())
        changed = deepcopy(fixed); changed.update(key='new-alias', development_study_id='equivalent-development')
        self.assertIsNone(runner._study_existing_request({'body': {'request': fixed}}, changed))
        changed['budget']['max_attempts'] = 2
        with self.assertRaises(Conflict):
            runner._study_existing_request({'body': {'request': fixed}}, changed)


if __name__ == '__main__':
    unittest.main()
