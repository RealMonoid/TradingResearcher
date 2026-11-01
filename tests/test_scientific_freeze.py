"""Scientific caller must retain a gap rather than grant unqualified authority."""
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.coordination import Broker, Denied
import test_evaluation_plans as plan_support


class ScientificFreezeCallerTests(unittest.TestCase):
    def test_typed_commitment_dependency_revocation_preserves_original_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            broker = Broker(directory)
            try:
                with broker._transaction():
                    target = broker._save_artifact({'version': 'local-artifact/1',
                        'creator': 'controller', 'origin': 'source', 'data_class': 'assessment',
                        'source_refs': [], 'exposure': [], 'authority': 'synthetic_metadata_fixture',
                        'body': {'schema': 'data-snapshot/1'}})
                    manifest = broker._freeze_save('frozen-manifest/1',
                        {'qualification': 'Dependency graph fixture only; no actual trial'},
                        [target['id']], [target['id']])
                self.assertEqual(broker.call(broker.admin_token, 'inspect_dependency_use',
                    artifact_id=manifest['id'])['status'], 'NOT_REVOKED')
                evidence = broker.call(broker.admin_token, 'add_source',
                    body={'defect': 'Synthetic graph test'}, data_class='operations')
                broker.call(broker.admin_token, 'revoke_dependency', key='synthetic-defect',
                    dependency_id=target['id'], reason='Synthetic graph defect',
                    evidence_refs=[evidence['id']])
                self.assertEqual(broker.call(broker.admin_token, 'inspect_dependency_use',
                    artifact_id=manifest['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
                self.assertEqual(broker.call(broker.admin_token, 'get_artifact',
                    artifact_id=manifest['id']), manifest)
            finally:
                broker.close()

    def test_missing_owned_plan_becomes_retained_admission_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            with_broker = Broker(directory, clock=lambda: 1000)
            try:
                source = with_broker.call(with_broker.admin_token, 'add_source',
                    body={'fixture': 'unqualified input'}, data_class='development')
                try:
                    result = with_broker.call(with_broker.admin_token, 'freeze_scientific_batch',
                        key='gap', campaign_id=source['id'], role='primary',
                        plan_ids=[source['id']], selection_record_ref=source['id'],
                        reservation_spec_ref=source['id'])
                except Denied:
                    result = None
                self.assertIsNotNone(result, 'Operator freeze caller is missing')
                self.assertEqual(result['body']['status'], 'ADMISSION_GAP')
                self.assertFalse(result['body']['frozen'])
                self.assertFalse(result['body']['allocation_reserved'])
                self.assertFalse(result['body']['scientific_readiness'])
                self.assertEqual(with_broker._db.execute("SELECT count(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')='frozen-manifest/1'").fetchone()[0], 0)
            finally:
                with_broker.close()


class ScientificPlanAdmissionTests(unittest.TestCase):
    setUpClass = classmethod(plan_support.EvaluationPlanTests.setUpClass.__func__)
    tearDownClass = classmethod(plan_support.EvaluationPlanTests.tearDownClass.__func__)
    arguments = plan_support.EvaluationPlanTests.arguments

    def test_owned_plan_caller_retains_missing_scientific_prerequisites(self):
        plan = self.broker.call(self.token, 'prepare_evaluation_plan', **self.arguments('freeze-plan'))
        source = self.broker.call(self.token, 'add_source',
            body={'purpose': 'Synthetic campaign/selection/reservation anchor only'},
            data_class='development')
        with patch.object(self.broker, '_load_reference_data',
                          side_effect=AssertionError('Freeze admission accessed outcome data')):
            result = self.broker.call(self.token, 'freeze_scientific_batch',
                key='owned-plan-freeze', campaign_id=source['id'], role='primary',
                plan_ids=[plan['id']], selection_record_ref=source['id'],
                reservation_spec_ref=source['id'])
        self.assertEqual(result['body']['status'], 'ADMISSION_GAP')
        admission = result['body']['admission']
        self.assertIn('CALIBRATED_ESTIMATOR_AND_INFORMATION_PLAN_NOT_ADMITTED', admission['gaps'])
        self.assertIn('SCIENTIFIC_DATA_AND_EXPOSURE_NOT_ADMITTED', admission['gaps'])
        observation = admission['admission']['plan_observations'][0]
        self.assertEqual(observation['plan_id'], plan['id'])
        self.assertEqual(observation['status'], 'POLICY_DRAFT')
        self.assertFalse(observation['protected_target_admission'])
        self.assertIn(plan['id'], result['exposure'])


if __name__ == '__main__':
    unittest.main()
