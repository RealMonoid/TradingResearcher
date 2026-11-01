"""Independent ancestry adversaries for an unauthenticated study-cost claim.

Technical envelopes in these temporary registries are metadata fixtures only.
Admitting their provenance must neither validate nor execute a certificate,
package, plan or worker claim. No real registry, market data or provider is used.
"""
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.coordination import Broker, Denied, Invalid


class StudyCostProvenanceIndependentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.broker = Broker(temporary.name, clock=lambda: 1000)
        self.addCleanup(self.broker.close)
        self.token = self.broker.admin_token
        self.base = self.source({'invented': 'development provenance'})

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def source(self, body, data_class='development', exposure=()):
        return self.op('add_source', body=body, data_class=data_class, exposure=list(exposure))

    def retained(self, body, *, data_class='operations', source_refs=(), exposure=(),
                 creator='controller', origin='controller', authority='retained_source_not_certified'):
        # Deliberately seed host-side malformed/typed metadata to exercise the
        # ancestry boundary. This does not issue a genuine implementation proof.
        with self.broker._transaction():
            return self.broker._save_artifact({'version': 'local-artifact/1', 'creator': creator,
                'origin': origin, 'data_class': data_class, 'source_refs': sorted(source_refs),
                'exposure': sorted(exposure), 'authority': authority, 'body': deepcopy(body)})

    def cost(self, exposure=(), data_class='development'):
        body = {'schema': 'development-study-cost-estimate/1', 'world_time_rows': 24,
                'observed_compute_ms': 137, 'observed_storage_bytes': 4096,
                'qualification': 'Invented operator estimate; not an authenticated benchmark.'}
        artifact = self.source(body, data_class=data_class, exposure=exposure)
        estimate = {'source_ref': artifact['id'], **{key: value for key, value in body.items() if key != 'schema'}}
        return artifact, estimate

    def product(self):
        worker = self.op('register_worker', name='independent-worker', role='formalizer',
                         capabilities=['draft/v1'])['token']
        context = self.op('create_context', role='formalizer', epoch=1,
                          artifact_ids=[self.base['id']])['id']
        job = self.op('enqueue', key='independent-context-job', spec={
            'kind': 'draft/v1', 'context_id': context, 'purpose': 'Invented cost-provenance work product',
            'allowed_workers': ['independent-worker'], 'max_attempts': 1,
            'lease_seconds': 10, 'deadline': 1100, 'dependencies': []})['id']
        claim = self.broker.call(worker, 'claim')
        identity = self.broker.call(worker, 'put_artifact', lease=claim['lease'],
            body={'invented': 'unverified worker text, never an empirical verdict'},
            source_refs=[self.base['id']])['id']
        return self.op('get_artifact', artifact_id=identity), context, job

    def clone(self, artifact, **changes):
        envelope = {key: deepcopy(value) for key, value in artifact.items() if key != 'id'}
        envelope.update(changes)
        with self.broker._transaction():
            return self.broker._save_artifact(envelope)

    def counts(self):
        return tuple(self.broker._db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                     for table in ('artifacts', 'events', 'contexts', 'job_specs'))

    def test_complete_bound_worker_and_historical_technical_ancestry_is_read_only(self):
        product, _, _ = self.product()
        package = self.retained({'schema': 'reference-source-package/1', 'historical_fixture': True},
                                source_refs=[self.base['id']])
        certificate = self.retained({'schema': 'implementation-certificate/1', 'status': 'STALE',
                                     'source_package_id': package['id']}, source_refs=[package['id']],
                                    authority='implementation_conformance_only')
        wrapper = self.source({'invented': 'complete wrapper'}, exposure=[product['id'], certificate['id']])
        root, estimate = self.cost([wrapper['id']])
        before = self.counts()
        with patch.object(self.broker, '_reference_certificate_status',
                          side_effect=AssertionError('Provenance was promoted to certificate use')):
            actual, ancestry = self.broker._study_cost_source(estimate)
        self.assertEqual(actual, root)
        self.assertEqual(ancestry, {root['id'], wrapper['id'], product['id'], certificate['id'],
                                   package['id'], self.base['id']})
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.op('get_artifact', artifact_id=certificate['id']), certificate)
        self.assertEqual(certificate['body']['status'], 'STALE')
        self.assertEqual(actual['authority'], 'supplied_source_not_certified')
        self.assertNotIn('scientific_readiness', actual['body'])
        self.assertNotIn('classification_permitted', actual['body'])

    def test_worker_job_and_context_mismatch_is_not_eligible_cost_ancestry(self):
        product, _, _ = self.product()
        other_context = self.op('create_context', role='formalizer', epoch=2,
                                artifact_ids=[self.base['id']])['id']
        for changes in ({'context_id': other_context}, {'context_id': '0' * 64}, {'job_id': '0' * 64}):
            with self.subTest(changes=changes):
                malformed = self.clone(product, **changes)
                _, estimate = self.cost([malformed['id']])
                with self.assertRaises((Denied, Invalid)):
                    self.broker._study_cost_source(estimate)

    def test_worker_cannot_omit_an_authorized_context_source_or_exposure(self):
        product, _, _ = self.product()
        for changes in ({'source_refs': []}, {'exposure': []}):
            with self.subTest(changes=changes):
                malformed = self.clone(product, **changes)
                _, estimate = self.cost([malformed['id']])
                with self.assertRaises((Denied, Invalid)):
                    self.broker._study_cost_source(estimate)

    def test_forged_technical_schema_authority_or_ownership_stays_operational(self):
        variants = [
            {'creator': 'operator', 'origin': 'source', 'authority': 'retained_source_not_certified'},
            {'creator': 'controller', 'origin': 'controller', 'authority': 'arbitrary_authority'},
            {'creator': 'controller', 'origin': 'source', 'authority': 'retained_source_not_certified'},
        ]
        for fields in variants:
            with self.subTest(fields=fields):
                forged = self.retained({'schema': 'reference-source-package/1'}, **fields)
                wrapper = self.source({'invented': 'development wrapper'}, exposure=[forged['id']])
                _, estimate = self.cost([wrapper['id']])
                with self.assertRaises(Denied):
                    self.broker._study_cost_source(estimate)

    def test_owned_technical_wrapper_cannot_hide_operational_observations(self):
        fills = self.source({'invented_fills': 'not research evidence'}, data_class='operations')
        for linkage in ('source_refs', 'exposure'):
            with self.subTest(linkage=linkage):
                package = self.retained({'schema': 'binding-source-package/1'}, **{linkage: [fills['id']]})
                _, estimate = self.cost([package['id']])
                with self.assertRaises(Denied):
                    self.broker._study_cost_source(estimate)

    def test_assessment_hidden_behind_development_wrappers_remains_denied(self):
        assessment = self.source({'invented': 'protected outcome metadata'}, data_class='assessment')
        inner = self.source({'invented': 'inner wrapper'}, exposure=[assessment['id']])
        outer = self.source({'invented': 'outer wrapper'}, exposure=[inner['id']])
        _, estimate = self.cost([outer['id']])
        before = self.counts()
        with self.assertRaises(Denied):
            self.broker._study_cost_source(estimate)
        self.assertEqual(self.counts(), before)

    def test_final_and_private_namespaces_cannot_hide_behind_development_labels(self):
        for schema in ('evaluator-calibration-input/1', 'evaluator-calibration-attempt/9',
                       'family-calibration-input/1', 'family-calibration-attempt/1',
                       'protected-data-binding/1'):
            with self.subTest(schema=schema):
                hidden = self.retained({'schema': schema}, data_class='development')
                wrapper = self.source({'invented': 'misleading development label'}, exposure=[hidden['id']])
                _, estimate = self.cost([wrapper['id']])
                with self.assertRaises(Denied):
                    self.broker._study_cost_source(estimate)

    def test_unresolved_exposure_and_missing_required_source_remain_denied(self):
        _, estimate = self.cost(['opaque:unresolved-historical-observation'])
        with self.assertRaises(Denied):
            self.broker._study_cost_source(estimate)
        wrapper = self.retained({'invented': 'missing mandatory dependency'}, data_class='development',
                                source_refs=['0' * 64], authority='supplied_source_not_certified')
        _, estimate = self.cost([wrapper['id']])
        with self.assertRaises(Invalid):
            self.broker._study_cost_source(estimate)

    def test_cost_root_class_exact_body_and_complete_request_are_preserved(self):
        for data_class in ('operations', 'assessment'):
            with self.subTest(data_class=data_class):
                _, estimate = self.cost(data_class=data_class)
                with self.assertRaises(Denied):
                    self.broker._study_cost_source(estimate)
        root, estimate = self.cost([self.base['id']])
        for changes in ({'observed_compute_ms': 138}, {'qualification': 'Different operator qualification'},
                        {'unexpected': True}, {'source_ref': False}):
            with self.subTest(changes=changes), self.assertRaises(Invalid):
                self.broker._study_cost_source({**estimate, **changes})
        incomplete = dict(estimate)
        del incomplete['observed_storage_bytes']
        with self.assertRaises(Invalid):
            self.broker._study_cost_source(incomplete)
        self.assertEqual(self.op('get_artifact', artifact_id=root['id']), root)

    def preparation_inputs(self, estimate):
        plan = self.source({'invented': 'not an owned scientific plan'})
        execution = self.source({'invented': 'not an owned computation'})
        diagnostic = self.retained({'schema': 'development-information-diagnostics/1',
            'request': {'plan_id': plan['id'], 'execution_id': execution['id']}},
            data_class='development', source_refs=[plan['id'], execution['id']],
            authority='development_diagnostics_not_scientific_admission')
        return {'key': 'independent-public-cost-gate', 'plan_id': plan['id'],
                'execution_id': execution['id'], 'diagnostics_id': diagnostic['id'],
                'profile': {'cost_estimate': estimate}}

    def test_public_preparation_keeps_actual_plan_use_guard_after_cost_eligibility(self):
        package = self.retained({'schema': 'reference-source-package/1', 'historical_fixture': True})
        _, estimate = self.cost([package['id']])
        request = self.preparation_inputs(estimate)
        before = self.counts()
        with patch.object(self.broker, '_development_plan_execution',
                          wraps=self.broker._development_plan_execution) as use_guard:
            with self.assertRaises(Denied):
                self.op('prepare_information_study', **request)
        use_guard.assert_called_once()
        self.assertEqual(use_guard.call_args.args[1:], (request['plan_id'], request['execution_id']))
        self.assertEqual(self.counts(), before)

    def test_public_preparation_rejects_forbidden_cost_before_plan_or_source_work(self):
        operations = self.source({'invented': 'operational knowledge'}, data_class='operations')
        _, estimate = self.cost([operations['id']])
        request = self.preparation_inputs(estimate)
        before = self.counts()
        with patch.object(self.broker, '_development_plan_execution',
                          side_effect=AssertionError('Forbidden cost reached plan use')), \
                patch.object(self.broker, '_study_capture_source',
                             side_effect=AssertionError('Forbidden cost reached source capture')):
            with self.assertRaises(Denied):
                self.op('prepare_information_study', **request)
        self.assertEqual(self.counts(), before)


if __name__ == '__main__':
    unittest.main()
