"""Cost claims retain permitted development lineage without certifying it."""
import tempfile
import time
import unittest

from trading_researcher.coordination import Broker, Denied, Invalid


class StudyCostProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.broker = Broker(self.temporary.name)
        self.addCleanup(self.broker.close)
        self.token = self.broker.admin_token

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def cost(self, exposure=(), data_class='development'):
        values = {'world_time_rows': 8, 'observed_compute_ms': 1000,
            'observed_storage_bytes': 1048576,
            'qualification': 'Synthetic operator cost claim, not an authenticated benchmark.'}
        source = self.op('add_source', body={'schema': 'development-study-cost-estimate/1', **values},
                         data_class=data_class, exposure=list(exposure))
        return {'source_ref': source['id'], **values}, source

    def product(self):
        source = self.op('add_source', body={'purpose': 'Synthetic permitted development input'},
                         data_class='development')
        worker = self.op('register_worker', name='cost-lineage-worker', role='formalizer',
                         capabilities=['draft/v1'])['token']
        context = self.op('create_context', role='formalizer', epoch=1, artifact_ids=[source['id']])
        self.op('enqueue', key='cost-lineage-job', spec={'kind': 'draft/v1', 'context_id': context['id'],
            'purpose': 'Synthetic worker ancestry conformance', 'allowed_workers': ['cost-lineage-worker'],
            'max_attempts': 1, 'lease_seconds': 60, 'deadline': int(time.time()) + 120,
            'dependencies': []})
        lease = self.broker.call(worker, 'claim')['lease']
        product = self.broker.call(worker, 'put_artifact', lease=lease,
            body={'finding': 'Unverified fixture', 'interpretation': 'No scientific evidence',
                  'uncertainty': 'Synthetic input', 'next_action': 'Retain'},
            source_refs=[source['id']])
        return source, self.op('get_artifact', artifact_id=product['id'])

    def test_owned_reference_provenance_and_bound_worker_context_are_retained(self):
        certificate = self.op('certify_reference')
        self.assertEqual(certificate['body']['status'], 'CERTIFIED')
        source, product = self.product()
        estimate, cost = self.cost([certificate['id'], product['id']])
        retained, ancestry = self.broker._study_cost_source(estimate)
        self.assertEqual(retained, cost)
        self.assertTrue({cost['id'], certificate['id'], certificate['body']['source_package_id'],
                         product['id'], source['id']} <= ancestry)
        self.assertEqual(self.op('get_artifact', artifact_id=product['id']), product)
        self.assertFalse(certificate['body']['scientific_readiness'])

    def test_arbitrary_operations_assessment_and_opaque_exposure_stay_denied(self):
        for data_class in ('operations', 'assessment'):
            with self.subTest(data_class=data_class):
                forbidden = self.op('add_source', body={'fixture': data_class}, data_class=data_class)
                estimate, _ = self.cost([forbidden['id']])
                with self.assertRaises(Denied):
                    self.broker._study_cost_source(estimate)
        estimate, _ = self.cost(['opaque-unknown-ancestry'])
        with self.assertRaises((Denied, Invalid)):
            self.broker._study_cost_source(estimate)

    def test_development_root_and_exact_retained_measurement_are_required(self):
        estimate, _ = self.cost(data_class='operations')
        with self.assertRaises(Denied):
            self.broker._study_cost_source(estimate)
        estimate, _ = self.cost()
        with self.assertRaises((Denied, Invalid)):
            self.broker._study_cost_source({**estimate, 'observed_compute_ms': 999})

    def test_technical_wrapper_does_not_hide_forbidden_ancestry(self):
        forbidden = self.op('add_source', body={'fixture': 'operations knowledge'}, data_class='operations')
        with self.broker._transaction():
            wrapper = self.broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'operations', 'authority': 'retained_source_not_certified',
                'body': {'schema': 'reference-source-package/1'}, 'source_refs': [forbidden['id']],
                'exposure': [forbidden['id']]})
        estimate, _ = self.cost([wrapper['id']])
        with self.assertRaises(Denied):
            self.broker._study_cost_source(estimate)

    def test_final_calibration_namespace_cannot_hide_behind_development_label(self):
        for schema in ('family-calibration-input/1', 'evaluator-calibration-attempt/1'):
            with self.subTest(schema=schema):
                with self.broker._transaction():
                    final = self.broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                        'origin': 'controller', 'data_class': 'development', 'authority': 'synthetic_adversary',
                        'body': {'schema': schema}, 'source_refs': [], 'exposure': []})
                estimate, _ = self.cost([final['id']])
                with self.assertRaises(Denied):
                    self.broker._study_cost_source(estimate)


if __name__ == '__main__':
    unittest.main()
