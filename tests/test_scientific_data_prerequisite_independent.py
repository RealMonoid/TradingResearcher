"""Independent freeze-consumed data prerequisites, never full admission.

Existing owned synthetic protected fixtures supply real normalization, feature
and reference certification, target binding, compilation, data-use and plan
operations. ONLY reviewed provider-document pins are substituted for invented
fixture text: this is not actual legal acceptance, verified PIT or unseen data.

Each method starts from an independently restored temporary Registry. Host-local
plan/assessment clones below are explicitly malformed future-consumer metadata
fixtures; they are not public preparation, certificates or admission judgments.
No private scientific admission resolver is replaced and no study is advanced.
"""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_protected_plan_binding as protected_support
from trading_researcher import data_use
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.storage import restore_bundle


COMPONENT_KEYS = {'schema', 'status', 'gaps', 'plan_bindings', 'artifact_ids',
    'campaign_selection_and_prior_use', 'unused_reservation_and_dependence',
    'evidence_origin', 'protected_target_admission', 'scientific_readiness',
    'assessment_access_authority'}
COMMITTED = ('scientific-allocation/1', 'scientific-trial/1', 'frozen-manifest/1')


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def independent_hash(value):
    return hashlib.sha256(encoded(value)).hexdigest()


@contextmanager
def metadata_only(broker):
    with ExitStack() as stack:
        for name in ('_load_reference_data', '_scan_data'):
            stack.enter_context(patch.object(broker, name,
                side_effect=AssertionError('Data prerequisite expanded protected observations')))
        for target in ('trading_researcher.expressions.ReferenceEngine._calculate',
                       'trading_researcher.outcomes.materialize_reference',
                       'trading_researcher.binding.run_child',
                       'trading_researcher.evaluation_plans.run_plan_child',
                       'trading_researcher.features.run_validation',
                       'trading_researcher.certification.run_reference_validation',
                       'trading_researcher.binance_normalize._run_child'):
            stack.enter_context(patch(target,
                side_effect=AssertionError('Data prerequisite calculated outcomes or replayed certification')))
        yield


class ScientificDataPrerequisiteIndependentTests(unittest.TestCase):
    # Borrow constructors/helpers without inheriting or discovering old methods.
    setUpClass = classmethod(protected_support.ProtectedPlanTests.setUpClass.__func__)
    setUp = protected_support.ProtectedPlanTests.setUp
    op = protected_support.ProtectedPlanTests.op
    assess = protected_support.ProtectedPlanTests.assess
    plan_request = protected_support.ProtectedPlanTests.request
    clone = protected_support.ProtectedPlanTests.clone
    revoke = protected_support.ProtectedPlanTests.revoke

    def prepared(self, label):
        assessment = self.assess()
        self.assertEqual('QUALIFIED_PRIVATE_PLAN_DATA', assessment['body']['status'])
        plan = self.op('prepare_evaluation_plan', **self.plan_request(label, assessment))
        self.assertEqual('POLICY_DRAFT', plan['body']['status'])
        return assessment, plan

    def freeze_request(self, plans, label, role='primary'):
        anchor = self.op('add_source', body={'purpose': 'Synthetic data-prerequisite campaign ' + label},
                         data_class='development')
        return {'key': 'data-prerequisite-' + label, 'campaign_id': anchor['id'], 'role': role,
                'plan_ids': [plan['id'] for plan in plans],
                'selection_record_ref': anchor['id'], 'reservation_spec_ref': anchor['id']}

    def public_freeze(self, plans, label, role='primary'):
        request = self.freeze_request(plans, label, role)
        with metadata_only(self.f.broker):
            result = self.op('freeze_scientific_batch', **request)
        self.assertEqual('ADMISSION_GAP', result['body']['status'])
        self.assert_no_release(result)
        return result, result['body']['admission']['admission']['data_prerequisite'], request

    def assert_no_release(self, result=None):
        for schema in COMMITTED:
            self.assertEqual([], self.f.broker._freeze_objects(schema))
        if result is not None:
            for flag in ('scientific_readiness', 'frozen', 'allocation_reserved'):
                self.assertIs(result['body'][flag], False)

    def assert_component(self, component, qualified):
        self.assertEqual(COMPONENT_KEYS, set(component))
        self.assertEqual('scientific-data-prerequisite/1', component['schema'])
        self.assertEqual('QUALIFIED_DATA_PREREQUISITE' if qualified else 'DATA_PREREQUISITE_GAP',
                         component['status'])
        self.assertEqual(sorted(set(component['gaps'])), component['gaps'])
        self.assertEqual(not qualified, bool(component['gaps']))
        self.assertEqual(sorted(set(component['artifact_ids'])), component['artifact_ids'])
        self.assertEqual('NOT_ASSESSED', component['campaign_selection_and_prior_use'])
        self.assertEqual('NOT_QUALIFIED', component['unused_reservation_and_dependence'])
        self.assertIsNone(component['evidence_origin'])
        for flag in ('protected_target_admission', 'scientific_readiness', 'assessment_access_authority'):
            self.assertIs(component[flag], False)

    def assert_data_gap(self, result, component, plan):
        self.assert_component(component, False)
        self.assertIn('SCIENTIFIC_DATA_PREREQUISITE_NOT_QUALIFIED', result['body']['admission']['gaps'])
        self.assertEqual([plan['id']], [item['plan_id'] for item in component['plan_bindings']])
        member = component['plan_bindings'][0]
        self.assertEqual({'plan_id', 'status', 'failure_type'}, set(member))
        self.assertEqual('DATA_PREREQUISITE_GAP', member['status'])
        self.assertIn(member['failure_type'], ('Invalid', 'Denied', 'Conflict', 'KeyError',
                                              'TypeError', 'ValueError', 'OSError'))

    def assert_originals(self, *artifacts):
        for artifact in artifacts:
            self.assertEqual(artifact, self.op('get_artifact', artifact_id=artifact['id']))

    def test_real_public_data_branch_qualifies_but_selection_exposure_access_and_calibration_stay_closed(self):
        assessment, plan = self.prepared('qualified')
        packet = encoded(self.f.broker._auxiliary_packet_for_spec(self.case['spec']))
        result, component, _ = self.public_freeze([plan], 'qualified')
        self.assert_component(component, True)
        self.assertEqual([], component['gaps'])
        self.assertEqual(1, len(component['plan_bindings']))
        member = component['plan_bindings'][0]
        self.assertEqual('QUALIFIED_DATA_PREREQUISITE', member['status'])
        private = self.private['body']['resolved']
        snapshot = self.f.versions[0]['snapshot']
        certificate = self.f.versions[0]['certificate']
        findings = assessment['body']['findings']
        ids = {'plan_id': plan['id'], 'compiled_id': self.compiled['id'],
            'data_use_assessment_id': assessment['id'], 'data_target_binding_id': self.private['id'],
            'public_target_id': self.f.target['id'], 'data_snapshot_id': snapshot['id'],
            'feature_certificate_id': certificate['id'], 'reference_certificate_id': self.f.base.reference['id'],
            'normalization_id': findings['scope']['normalization_id'],
            'feature_definitions_id': private['private_definitions_id'],
            'public_definitions_id': private['public_definitions_id'],
            'catalog_id': private['private_catalog_id'], 'public_catalog_id': private['public_catalog_id']}
        for name, expected in ids.items():
            self.assertEqual(expected, member[name], name)
            self.assertIn(expected, component['artifact_ids'], name)
        self.assertEqual('primary', member['role'])
        self.assertEqual('assessment', member['partition'])
        self.assertEqual({'start': '2024-01-01T00:15:00Z', 'end': '2024-01-01T01:00:00Z',
                          'instruments': ['BTCUSDT']}, member['declared_universe'])
        self.assertEqual('QUALIFIED_PRIVATE_PLAN_DATA', member['data_use_status'])
        self.assertEqual('CURRENT', member['feature_status'])
        self.assertEqual('CURRENT', member['reference_status'])
        self.assertEqual(assessment['body']['checker_sha256'], member['data_use_checker_sha256'])
        self.assertEqual(hashlib.sha256(Path(data_use.__file__).read_bytes()).hexdigest(),
                         member['data_use_checker_sha256'])
        self.assertEqual(independent_hash(snapshot['body']['manifest']), member['snapshot_manifest_hash'])
        self.assertEqual(independent_hash(self.compiled['body']['compilation']['request']),
                         member['compilation_request_hash'])
        self.assertEqual(findings['rights'], member['rights'])
        self.assertEqual(findings['availability'], member['availability'])
        self.assertEqual('assumed', member['availability']['basis'])
        self.assertIsNone(member['availability']['historical_publication_time'])
        self.assertIs(member['availability']['historical_vintage_verified'], False)
        self.assertIsNone(member['evidence_origin'])
        self.assertEqual(findings['exposure']['origin_reason'], member['origin_reason'])
        self.assertEqual(independent_hash(findings['prior_knowledge']), member['prior_knowledge_hash'])
        self.assertNotIn(self.private['id'], findings['prior_knowledge']['artifact_ids'])
        self.assertIn(self.f.target['id'], findings['prior_knowledge']['artifact_ids'])
        aggregate = result['body']['admission']['gaps']
        self.assertNotIn('SCIENTIFIC_DATA_PREREQUISITE_NOT_QUALIFIED', aggregate)
        for gap in ('SCIENTIFIC_SELECTION_AND_RESERVATION_NOT_QUALIFIED',
                    'SCIENTIFIC_EXPOSURE_AND_PRIOR_USE_NOT_QUALIFIED',
                    'SCIENTIFIC_DATA_AND_EXPOSURE_NOT_ADMITTED',
                    'CALIBRATED_ESTIMATOR_AND_INFORMATION_PLAN_NOT_ADMITTED'):
            self.assertIn(gap, aggregate)
        self.assertEqual(packet, encoded(self.f.broker._auxiliary_packet_for_spec(self.case['spec'])))
        self.assert_originals(assessment, plan, self.compiled, self.private, certificate)
        self.assertEqual('QUALIFIED_PRIVATE_PLAN_DATA', assessment['body']['status'])
        for role in ('discovery', 'formalizer'):
            with self.subTest(role=role), self.assertRaises(Denied):
                self.op('create_context', role=role, epoch=3, artifact_ids=[result['id']])

    def test_missing_exploration_or_other_compile_assessment_cannot_satisfy_future_consumer(self):
        assessment, plan = self.prepared('malformed-references')
        exploration = self.op('assess_data_use', compiled_id=self.development['id'])
        self.assertEqual('QUALIFIED_EXPLORATION', exploration['body']['status'])
        wrong_compiled = self.op('compile_hypothesis',
            **{**self.compiled['body']['dependency_arguments'], 'max_steps': 9999})
        other = self.op('assess_data_use', compiled_id=wrong_compiled['id'])
        for label, assessment_ref in (('missing', None), ('exploration', exploration['id']),
                                      ('wrong-compile', other['id'])):
            changed = deepcopy(plan['body'])
            if assessment_ref is None:
                changed['request'].pop('data_use_assessment_id')
            else:
                changed['request']['data_use_assessment_id'] = assessment_ref
            malformed = self.clone(plan, body=changed)
            request = self.freeze_request([malformed], 'fault-' + label)
            # Trusted-local malformed plan fixture only, not public preparation.
            with self.subTest(label=label), metadata_only(self.f.broker):
                component = self.f.broker._freeze_data_prerequisite(
                    self.f.broker._binding_owner(self.f.token), request)
            self.assert_component(component, False)
            self.assertEqual(malformed['id'], component['plan_bindings'][0]['plan_id'])
            self.assertEqual('DATA_PREREQUISITE_GAP', component['plan_bindings'][0]['status'])
        self.assert_no_release()
        self.assert_originals(assessment, plan, self.compiled)

    def test_2024_primary_target_cannot_supply_2025_corroboration_role(self):
        assessment, plan = self.prepared('role-partition')
        result, component, _ = self.public_freeze([plan], 'wrong-role', role='corroboration')
        self.assert_data_gap(result, component, plan)
        self.assertIn('CORROBORATION_PRERESERVATION_AND_DEPENDENCE_NOT_QUALIFIED',
                      result['body']['admission']['gaps'])
        self.assert_originals(assessment, plan, self.private)

    def test_stale_checker_and_intact_stale_feature_or_reference_do_not_renew_admission(self):
        assessment, plan = self.prepared('currency')
        with patch.object(data_use, 'LOADED_SELF', '0' * 64):
            result, component, _ = self.public_freeze([plan], 'stale-checker')
        self.assert_data_gap(result, component, plan)
        for kind, method in (('feature', '_feature_certificate_status'),
                              ('reference', '_reference_certificate_status')):
            original = getattr(self.f.broker, method)

            def stale(*args, _original=original, **kwargs):
                return {**_original(*args, **kwargs), 'status': 'STALE'}

            with self.subTest(kind=kind), patch.object(self.f.broker, method, side_effect=stale):
                result, component, _ = self.public_freeze([plan], 'stale-' + kind)
            self.assert_data_gap(result, component, plan)
        self.assert_originals(assessment, plan, self.compiled,
                              self.f.versions[0]['certificate'], self.f.base.reference)

    def test_unreviewed_provider_policy_reopens_data_branch_without_changing_old_qualification(self):
        assessment, plan = self.prepared('rights')
        self.pins.stop()
        result, component, _ = self.public_freeze([plan], 'rights-reopened')
        self.assert_data_gap(result, component, plan)
        self.assert_originals(assessment, plan)
        self.assertEqual('QUALIFIED_PRIVATE_PLAN_DATA', assessment['body']['status'])

    def test_actual_dependency_revocation_reopens_data_branch_and_retains_history(self):
        assessment, plan = self.prepared('revocation')
        self.revoke()
        result, component, _ = self.public_freeze([plan], 'after-revocation')
        self.assert_data_gap(result, component, plan)
        self.assert_originals(assessment, plan, self.private, self.f.versions[0]['certificate'])

    def test_corrupt_normalized_bytes_in_owned_restore_cannot_pass_metadata_prerequisite(self):
        assessment, plan = self.prepared('corrupt-input')
        snapshot = self.f.versions[0]['snapshot']
        self.assertEqual(1, len(snapshot['blob_refs']))
        path = self.f.broker._blob_path(snapshot['blob_refs'][0])
        self.assertTrue(path.resolve().is_relative_to(self.f.broker.directory.resolve()))
        baseline = self.base.broker._blob_path(snapshot['blob_refs'][0])
        self.assertFalse(path.samefile(baseline))
        baseline_hash = hashlib.sha256(baseline.read_bytes()).hexdigest()
        path.write_bytes(b'Independent corrupted copied synthetic normalized data\n')
        result, component, _ = self.public_freeze([plan], 'after-corruption')
        self.assert_data_gap(result, component, plan)
        self.assertEqual(baseline_hash, hashlib.sha256(baseline.read_bytes()).hexdigest())
        self.assert_originals(assessment, plan, snapshot)

    def test_wrapped_final_calibration_ancestry_in_local_fault_record_is_never_private_data_permission(self):
        assessment, plan = self.prepared('wrapped-ancestry')
        # Host-local ancestry marker, no actual calibration input or result.
        with self.f.broker._transaction():
            forbidden = self.f.broker._save_artifact({'version': 'local-artifact/1',
                'creator': 'controller', 'origin': 'controller', 'data_class': 'assessment',
                'source_refs': [], 'exposure': [], 'authority': 'synthetic_ancestry_fault_only',
                'body': {'schema': 'family-calibration-input/1'}})
        wrapper = self.op('add_source', body={'purpose': 'Synthetic hidden ancestry'},
                          data_class='development', exposure=[forbidden['id']])
        wrapped = self.clone(assessment, exposure=sorted(set(assessment['exposure']) | {wrapper['id']}))
        changed = deepcopy(plan['body'])
        changed['request']['data_use_assessment_id'] = wrapped['id']
        malformed = self.clone(plan, body=changed)
        request = self.freeze_request([malformed], 'wrapped-ancestry-fault')
        with metadata_only(self.f.broker):
            component = self.f.broker._freeze_data_prerequisite(
                self.f.broker._binding_owner(self.f.token), request)
        self.assert_component(component, False)
        self.assertEqual('DATA_PREREQUISITE_GAP', component['plan_bindings'][0]['status'])
        self.assert_no_release()
        self.assert_originals(assessment, plan)

    def test_family_order_is_retained_and_one_failed_member_does_not_become_a_smaller_pass(self):
        assessment, plan = self.prepared('family')
        changed = deepcopy(plan['body'])
        changed['request'].pop('data_use_assessment_id')
        malformed = self.clone(plan, body=changed)
        result, component, _ = self.public_freeze([malformed, plan], 'family-order')
        self.assert_component(component, False)
        self.assertEqual([malformed['id'], plan['id']], [item['plan_id'] for item in component['plan_bindings']])
        self.assertEqual(['DATA_PREREQUISITE_GAP', 'QUALIFIED_DATA_PREREQUISITE'],
                         [item['status'] for item in component['plan_bindings']])
        self.assertIn('SCIENTIFIC_DATA_PREREQUISITE_NOT_QUALIFIED', result['body']['admission']['gaps'])
        self.assert_originals(assessment, plan)

    def test_public_caller_flags_cannot_supply_component_or_access_authority(self):
        _, plan = self.prepared('forged-flags')
        request = self.freeze_request([plan], 'forged-flags')
        original = self.f.broker._scientific_freeze_admission
        with patch.object(self.f.broker, '_scientific_freeze_admission', wraps=original) as admission:
            for change in ({'data_prerequisite': {'status': 'QUALIFIED_DATA_PREREQUISITE'}},
                           {'scientific_readiness': True}, {'protected_target_admission': True},
                           {'assessment_access_authority': True}):
                with self.subTest(change=change), self.assertRaises((Invalid, Denied, Conflict)):
                    self.op('freeze_scientific_batch', **{**request, **change})
        admission.assert_not_called()
        self.assert_no_release()

    def test_full_restore_preserves_original_qualification_and_new_gapped_freeze_evidence(self):
        assessment, plan = self.prepared('restore')
        result, component, request = self.public_freeze([plan], 'restore')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            backup, destination = root / 'backup', root / 'restored'
            self.assertEqual('PASS', self.op('backup_bundle', destination=str(backup))['status'])
            self.assertEqual('PASS', restore_bundle(backup, destination,
                self.f.broker.directory / 'operator.key')['status'])
            restored = Broker(destination)
            try:
                for original in (assessment, plan, result, self.compiled, self.private):
                    self.assertEqual(original, restored.call(restored.admin_token, 'get_artifact',
                                                             artifact_id=original['id']))
                with metadata_only(restored):
                    recomputed = restored._freeze_data_prerequisite(
                        restored._binding_owner(restored.admin_token), request)
                self.assertEqual(component, recomputed)
                for schema in COMMITTED:
                    self.assertEqual([], restored._freeze_objects(schema))
            finally:
                restored.close()


if __name__ == '__main__':
    unittest.main()
