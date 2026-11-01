"""Independent optional breakout-host boundaries, invented data only.

The legacy model/source/data-use gates below are explicit synthetic substitutes.
They do NOT qualify a production formalization, market source or model meaning.
Real registry, immutable blobs, compilation, source packages, isolated children,
new host guards, and typed dependency/revocation logic are never substituted.
"""
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

import paired_breakout_oracle as original
from test_paired_breakout_composition import fixture_payload
from trading_researcher.binding import require
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.paired_computation import PairedComputation
from trading_researcher import paired_runtime
from trading_researcher.paired_breakout.host import BreakoutBroker
from trading_researcher.paired_breakout import host as implementation, composition, runtime

REJECTIONS = (Invalid, Denied, Conflict)


def owned(broker, body, refs=(), **header):
    with broker._transaction():
        return broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'data_class': 'development', 'source_refs': sorted(set(refs)),
            'exposure': sorted(set(refs)), 'authority': 'SYNTHETIC_TEST_ONLY',
            'body': body, **header})


def attach_synthetic_gates(broker, ids):
    """Exact acknowledged substitutions at existing, already-tested boundaries."""
    def dependencies(formalization_id, feature_certificate_id):
        require(formalization_id == ids['formalization'] and feature_certificate_id == ids['feature'])
        reference, bundle = broker._paired_require_qualification()
        target, snapshot, feature, definitions = [broker._artifact(ids[key])
            for key in ('formalization', 'snapshot', 'feature', 'definitions')]
        require(snapshot['body']['manifest']['partition'] == 'development')
        return {'formalization': target, 'snapshot': snapshot, 'feature_certificate': feature,
            'definition': definitions, 'catalog': broker._artifact(ids['catalog'])['body']['features'],
            'reference': reference, 'bundle': bundle,
            'refs': sorted([ids[key] for key in ('formalization', 'snapshot', 'feature', 'definitions', 'catalog', 'reference')])}
    broker._paired_dependencies = Mock(side_effect=dependencies)
    broker._paired_data_use = Mock(return_value={'status': 'QUALIFIED', 'fixture': 'SYNTHETIC_ONLY'})
    def meaning(actor, identity):
        require(actor['role'] == 'operator' and identity == ids['meaning'])
        record = broker._artifact(identity)
        require(record['creator'] == record['origin'] == 'controller'
                and record['body']['formalization_id'] == ids['formalization'])
        return {'current': True, 'independent_semantic_review': 'SATISFIED', 'fixture': 'SYNTHETIC_ONLY'}
    broker._inspect_meaning_review = Mock(side_effect=meaning)
    def load(snapshot_id, start, end, instruments):
        require(snapshot_id == ids['snapshot'] and start == composition.START and end == composition.END
                and instruments == list(original.PAIR))
        return {'catalog': broker._artifact(ids['catalog'])['body']['features'], 'rows': original.synthetic()}
    broker._load_reference_data = Mock(side_effect=load)


def prepare_registry(path):
    broker = BreakoutBroker(path, clock=lambda: 1800000000)
    try:
        reference = broker.certify_paired(broker.admin_token)
        require(reference['body']['status'] == 'CERTIFIED')
        inputs = fixture_payload()
        catalog = owned(broker, {'schema': 'feature-catalog/1', 'features': inputs['catalog']})
        snapshot = owned(broker, {'schema': 'data-snapshot/1', 'manifest': inputs['data_manifest']}, origin='source')
        definitions = owned(broker, {'schema': 'feature-definitions/1', 'input_refs': [snapshot['id']],
            'definitions': inputs['feature_definitions']}, [snapshot['id']], origin='source')
        feature = owned(broker, {'schema': 'feature-certificate/1', 'data_snapshot_id': snapshot['id'],
            'definitions_id': definitions['id'], 'fixture': 'NOT_A_REAL_SOURCE_CERTIFICATE'},
            [snapshot['id'], definitions['id']])
        inputs['candidate']['test_universe']['data_snapshot_ref'] = snapshot['id']
        formalization = owned(broker, {'schema': 'formalization/2', 'idea_id': composition.IDEA_ID,
            'candidate': inputs['candidate'], 'fixture': 'ANALYSIS_FIXTURE_NOT_H_EXEC'})
        meaning = owned(broker, {'schema': 'semantic-review-assessment/1', 'formalization_id': formalization['id'],
            'fixture': 'NOT_A_REAL_MODEL_REVIEW'}, [formalization['id']])
        ids = {name: item['id'] for name, item in [('reference', reference), ('catalog', catalog),
            ('snapshot', snapshot), ('definitions', definitions), ('feature', feature),
            ('formalization', formalization), ('meaning', meaning)]}
        attach_synthetic_gates(broker, ids)
        for name, max_steps in [('complete', 10000000), ('partial', 100000)]:
            compiled = broker.compile_paired(broker.admin_token, formalization_id=ids['formalization'],
                feature_certificate_id=ids['feature'], as_of=composition.END, max_steps=max_steps)
            require(compiled['body']['status'] == 'COMPILED', str(compiled['body'].get('error')))
            certificate = broker.certify_paired_composition(broker.admin_token, compiled_id=compiled['id'])
            require(certificate['body']['status'] == 'CERTIFIED', str(certificate['body'].get('error')))
            ids[name], ids[name+'_certificate'] = compiled['id'], certificate['id']
        return ids
    finally:
        broker.close()


class BreakoutHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory(prefix='trf-breakout-host-base-')
        cls.addClassCleanup(cls.base.cleanup)
        cls.ids = prepare_registry(Path(cls.base.name)/'registry')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='trf-breakout-host-case-')
        self.addCleanup(self.temp.cleanup)
        path = Path(self.temp.name)/'registry'
        shutil.copytree(Path(self.base.name)/'registry', path)
        self.broker = BreakoutBroker(path, clock=lambda: 1800000000, paired_certificate_id=self.ids['reference'])
        self.addCleanup(self.broker.close)
        attach_synthetic_gates(self.broker, self.ids)

    def execute(self, name='complete', **changes):
        return self.broker.execute_paired(self.broker.admin_token, **{
            'compiled_id': self.ids[name], 'meaning_assessment_id': self.ids['meaning'],
            'composition_id': self.ids[name+'_certificate'], **changes})

    def certificate(self, name='complete'):
        return self.broker._artifact(self.ids[name+'_certificate'])

    def altered(self, artifact, **changes):
        envelope = deepcopy(artifact)
        envelope.pop('id')
        for path, value in changes.items():
            destination = envelope
            fields = path.split('__')
            for field in fields[:-1]: destination = destination[field]
            destination[fields[-1]] = value
        with self.broker._transaction(): return self.broker._save_artifact(envelope)

    def test_real_owned_composition_execute_separate_replay_and_original_audit(self):
        certificate = self.certificate()
        self.assertEqual(self.broker.inspect_breakout_composition(self.broker.admin_token,
            composition_id=certificate['id'])['status'], 'CURRENT')
        self.assertEqual(certificate['body']['report']['result']['scenario_count'], 299)
        self.assertEqual(certificate['body']['report']['result']['checked_cases'], 8970)
        record = self.execute()
        body = record['body']
        self.assertEqual(body['status'], 'DESCRIPTIVE_EXECUTION', body.get('error'))
        self.assertEqual(body['profile'], implementation.EXECUTION_PROFILE)
        self.assertEqual(body['composition_id'], certificate['id'])
        self.assertEqual(body['meaning_assessment_id'], self.ids['meaning'])
        self.assertFalse(body['scientific_readiness'])
        self.assertEqual(body['verification']['mode'], 'verify')
        self.assertEqual(body['verification']['result']['checked_cases'], 8640)
        self.assertEqual(body['verification']['result']['result_hash'], digest(body['result']))
        audit = body['independent_original_audit']
        self.assertEqual(audit['mode'], 'audit')
        self.assertEqual(audit['result']['checked_cases'], 8640)
        self.assertEqual(audit['result']['oracle_sha256'], composition.ORACLE_SHA256)
        raw = self.broker._read_blob_bytes(body['result']['case_blob']['sha256'])
        cases = [decode(line) for line in raw.splitlines()]
        self.assertEqual(len(cases), 8640)
        self.assertEqual(cases[20]['condition'], True)
        self.assertEqual(cases[20]['status'], 'ELIGIBLE')
        self.assertEqual(self.broker._load_reference_data.call_count, 1)
        self.assertGreaterEqual(self.broker._inspect_meaning_review.call_count, 2)
        self.assertEqual(self.broker._dependency_use(record['id'])['status'], 'NOT_REVOKED')

    def test_resource_stop_retains_verified_prefix_without_full_audit(self):
        record = self.execute('partial')
        body = record['body']
        self.assertEqual(body['status'], 'RESOURCE_STOP', body.get('error'))
        self.assertIsNone(body['error'])
        self.assertFalse(body['result']['report']['processing_complete'])
        count = body['result']['report']['processed_case_count']
        self.assertGreater(count, 0)
        self.assertLess(count, 8640)
        self.assertEqual(body['verification']['result']['checked_cases'], count)
        self.assertIsNone(body['independent_original_audit'])
        raw = self.broker._read_blob_bytes(body['result']['case_blob']['sha256'])
        self.assertEqual(len(raw.splitlines()), count)

    def test_replay_failure_preserves_exact_generated_case_blob_as_failure(self):
        child = paired_runtime.run_child
        def fail_replay(bundle, mode, payload, directory, **kwargs):
            if mode == 'verify':
                raise Invalid('Independently injected replay failure after actual computation')
            return child(bundle, mode, payload, directory, **kwargs)
        with patch.object(paired_runtime, 'run_child', side_effect=fail_replay):
            record = self.execute('partial')
        body = record['body']
        self.assertEqual(body['status'], 'EXECUTION_GAP')
        self.assertIn('injected replay failure', body['error']['reason'])
        self.assertIsNone(body['verification'])
        self.assertIsNone(body['independent_original_audit'])
        descriptor = body['result']['case_blob']
        self.assertIn(descriptor['sha256'], record['blob_refs'])
        raw = self.broker._read_blob_bytes(descriptor['sha256'])
        self.assertEqual(len(raw), descriptor['size'])
        self.assertEqual(len(raw.splitlines()), body['result']['report']['processed_case_count'])
        self.assertFalse(body['scientific_readiness'])

    def test_source_change_after_real_replay_prevents_successful_commit(self):
        child, read_bundle = paired_runtime.run_child, runtime.read_bundle
        replay_finished = [False]
        def child_then_drift(bundle, mode, payload, directory, **kwargs):
            result = child(bundle, mode, payload, directory, **kwargs)
            if mode == 'verify': replay_finished[0] = True
            return result
        def installed():
            bundle = read_bundle()
            if replay_finished[0]: bundle[composition.ORACLE] += b'\n# source changed during computation\n'
            return bundle
        with patch.object(paired_runtime, 'run_child', side_effect=child_then_drift), \
                patch.object(runtime, 'read_bundle', side_effect=installed):
            record = self.execute('partial')
        body = record['body']
        self.assertTrue(replay_finished[0])
        self.assertEqual(body['status'], 'EXECUTION_GAP')
        self.assertIn('sources changed', body['error']['reason'])
        self.assertEqual(body['verification']['mode'], 'verify')
        self.assertIn(body['result']['case_blob']['sha256'], record['blob_refs'])
        self.assertFalse(body['scientific_readiness'])

    def test_worker_and_generic_source_cannot_forge_or_invoke_owned_paths(self):
        token = self.broker.call(self.broker.admin_token, 'register_worker', name='worker',
            role='discovery', capabilities=['research-record/v1'])['token']
        for method, args in [(self.broker.certify_breakout_composition, {'compiled_id': self.ids['complete']}),
                (self.broker.inspect_breakout_composition, {'composition_id': self.ids['complete_certificate']}),
                (self.broker.execute_breakout, {'compiled_id': self.ids['complete'],
                    'meaning_assessment_id': self.ids['meaning'], 'composition_id': self.ids['complete_certificate']})]:
            with self.subTest(method=method.__name__), self.assertRaises(REJECTIONS): method(token, **args)
        for schema in ('paired-source-package/1', 'paired-composition-certificate/1', 'paired-reference-execution/1'):
            with self.subTest(schema=schema), self.assertRaises(REJECTIONS):
                self.broker.call(self.broker.admin_token, 'add_source', data_class='development',
                    body={'schema': schema, 'profile': composition.PROFILE})
        self.broker._load_reference_data.assert_not_called()

    def test_wrong_candidate_package_owner_and_meaning_stop_before_loader(self):
        base = self.certificate()
        for change in ({'body__candidate_hash': 'a'*64}, {'body__compiled_id': self.ids['partial']},
                {'body__source_package_id': self.broker._artifact(self.ids['reference'])['body']['source_package_id']},
                {'creator': 'invented-worker', 'origin': 'worker'}, {'body__host_sources': {}},
                {'body__status': 'COMPOSITION_GAP'}, {'body__report__result__checked_cases': 8969}):
            changed = self.altered(base, **change)
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                self.execute(composition_id=changed['id'])
        wrong_meaning = owned(self.broker, {'schema': 'semantic-review-assessment/1',
            'formalization_id': 'b'*64})
        with self.assertRaises(REJECTIONS): self.execute(meaning_assessment_id=wrong_meaning['id'])
        for status in ({'current': False, 'independent_semantic_review': 'SATISFIED'},
                       {'current': True, 'independent_semantic_review': 'UNCERTAIN'}):
            with patch.object(self.broker, '_inspect_meaning_review', return_value=status), self.assertRaises(REJECTIONS):
                self.execute()
        self.broker._load_reference_data.assert_not_called()

    def test_wrong_original_and_protected_dependency_stop_before_loader(self):
        original_dependencies = self.broker._paired_dependencies.side_effect
        def wrong_idea(*args):
            result = original_dependencies(*args)
            result['formalization'] = deepcopy(result['formalization'])
            result['formalization']['body']['idea_id'] = 'b'*64
            return result
        with patch.object(self.broker, '_paired_dependencies', side_effect=wrong_idea), self.assertRaises(REJECTIONS):
            self.broker.execute_breakout(self.broker.admin_token, compiled_id=self.ids['complete'],
                meaning_assessment_id=self.ids['meaning'], composition_id=self.ids['complete_certificate'])
        with patch.object(self.broker, '_paired_dependencies', side_effect=Denied('Synthetic protected-source gate')), self.assertRaises(REJECTIONS):
            self.execute()
        self.broker._load_reference_data.assert_not_called()

    def test_retained_package_tamper_and_installed_source_drift_fail_closed(self):
        package = self.broker._artifact(self.certificate()['body']['source_package_id'])
        altered = self.altered(package, body__bootstrap_sha256='0'*64)
        with self.assertRaises(REJECTIONS): self.broker._breakout_package(altered['id'])
        altered = self.altered(package, body__footprint={})
        with self.assertRaises(REJECTIONS): self.broker._breakout_package(altered['id'])
        altered = deepcopy(runtime.read_bundle())
        altered[composition.ORACLE] += b'\n# unapproved source drift\n'
        with patch.object(runtime, 'read_bundle', return_value=altered), self.assertRaises(REJECTIONS): self.execute()
        self.broker._load_reference_data.assert_not_called()

    def test_revoked_package_and_certificate_propagate_to_typed_dependents(self):
        certificate = self.certificate()
        package_id = certificate['body']['source_package_id']
        capsule = self.broker._paired_save({'schema': 'paired-execution-input/1',
            'profile': implementation.EXECUTION_PROFILE, 'compiled_id': self.ids['complete'],
            'composition_id': certificate['id']}, [self.ids['complete'], certificate['id']])
        evidence = self.broker.call(self.broker.admin_token, 'add_source',
            body={'defect': 'Invented technical defect for boundary testing.'}, data_class='development')
        for index, identity in enumerate((package_id, certificate['id'])):
            revoked = self.broker.call(self.broker.admin_token, 'revoke_dependency', key='test-'+str(index),
                dependency_id=identity, reason='Synthetic test only', evidence_refs=[evidence['id']])
            self.assertIn(certificate['id'], revoked['body']['affected_artifact_ids'])
            self.assertIn(capsule['id'], revoked['body']['affected_artifact_ids'])
            self.assertEqual(self.broker._dependency_use(capsule['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
            with self.assertRaises(REJECTIONS): self.execute()
        self.broker._load_reference_data.assert_not_called()

    def test_old_idea_routes_unchanged_without_acquiring_breakout_authority(self):
        triple = self.broker._paired_compiled(self.ids['complete'])
        changed = deepcopy(triple)
        changed[1]['formalization']['body']['idea_id'] = 'OLD_OR_OTHER_IDEA'
        with patch.object(self.broker, '_paired_compiled', return_value=changed), \
                patch.object(PairedComputation, 'certify_paired_composition', return_value='legacy-cert') as certify, \
                patch.object(PairedComputation, 'execute_paired', return_value='legacy-execution') as execute:
            self.assertEqual(self.broker.certify_paired_composition(self.broker.admin_token,
                compiled_id=self.ids['complete']), 'legacy-cert')
            self.assertEqual(self.execute(), 'legacy-execution')
            certify.assert_called_once_with(self.broker.admin_token, compiled_id=self.ids['complete'])
            execute.assert_called_once_with(self.broker.admin_token, compiled_id=self.ids['complete'],
                meaning_assessment_id=self.ids['meaning'], composition_id=self.ids['complete_certificate'])
        self.broker._load_reference_data.assert_not_called()


if __name__ == '__main__': unittest.main()
