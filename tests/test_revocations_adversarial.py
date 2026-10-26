"""Independent D083 boundaries using real lightweight snapshots and retained packages.

The tests exercise controller ownership, exact-version identity, history retention
and operational denial. Synthetic rows do not establish scientific data acceptance.
No mock model, empirical result or production-readiness assertion is involved.
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_data as data_support
import test_measurements as measurement_support
from trading_researcher import certification, measurements
from trading_researcher.codec import canonical
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.codec import Invalid
from trading_researcher.storage import restore_bundle


class RevocationAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.f = data_support.DataTests()
        self.f.setUp()
        self.addCleanup(self.f.tearDown)
        self.broker = self.f.broker
        self.source = self.f.source([data_support.row()])
        self.snapshot = self.f.register([self.source])
        self.evidence = self.op('add_source', data_class='operations',
            body={'schema': 'synthetic-defect-evidence/1',
                  'description': 'Independent test assertion, not a real detected scientific defect.'})

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def revoke(self, identity=None, key='revoke', **overrides):
        return self.op('revoke_dependency', **{
            'key': key, 'dependency_id': identity or self.snapshot['id'],
            'reason': 'Independent synthetic dependency defect fixture.',
            'evidence_refs': [self.evidence['id']], **overrides})

    def inspect(self, identity):
        return self.op('inspect_dependency_use', artifact_id=identity)

    def test_worker_denied_before_target_or_evidence_read(self):
        worker = self.op('register_worker', name='review-worker', role='formalizer',
                         capabilities=['draft/v1'])['token']
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Unauthorized dependent read')):
            for operation, args in (
                ('revoke_dependency', {'key': 'unauthorized', 'dependency_id': self.snapshot['id'],
                    'reason': 'Unauthorized fixture', 'evidence_refs': [self.evidence['id']]}),
                ('inspect_dependency_use', {'artifact_id': self.snapshot['id']})):
                with self.subTest(operation=operation), self.assertRaises(Denied):
                    self.broker.call(worker, operation, **args)

    def test_revocation_is_idempotent_but_key_cannot_change_target_or_reason(self):
        first = self.revoke()
        self.assertEqual(self.revoke(), first)
        for override in ({'reason': 'A different retained defect assertion.'},
                         {'dependency_id': self.evidence['id']}, {'evidence_refs': []}):
            with self.subTest(override=override), self.assertRaises((Conflict, Invalid, Denied)):
                self.revoke(**override)
        self.assertEqual(self.op('get_artifact', artifact_id=first['id']), first)

    def test_unknown_evidence_or_unsupported_target_cannot_issue_revocation(self):
        for override in ({'evidence_refs': ['nonexistent-evidence']},
                         {'dependency_id': self.evidence['id']}, {'reason': ''}):
            with self.subTest(override=override), self.assertRaises((Invalid, Denied, Conflict)):
                self.revoke(**override)
        self.assertEqual(self.inspect(self.snapshot['id'])['status'], 'NOT_REVOKED')

    def test_revocation_namespace_cannot_be_forged_by_source_or_worker(self):
        authentic = self.revoke()
        with self.assertRaises((Invalid, Denied)):
            self.op('add_source', body=deepcopy(authentic['body']), data_class='operations')
        worker = self.op('register_worker', name='namespace-writer', role='formalizer',
                         capabilities=['draft/v1'])['token']
        context = self.op('create_context', role='formalizer', epoch=1,
                          artifact_ids=[self.source['id']])
        self.op('enqueue', key='namespace-writer', spec={'kind': 'draft/v1',
            'context_id': context['id'], 'purpose': 'Independent namespace denial fixture',
            'allowed_workers': ['namespace-writer'], 'max_attempts': 1,
            'lease_seconds': 30, 'deadline': self.f.now + 300, 'dependencies': []})
        lease = self.broker.call(worker, 'claim')['lease']
        with self.assertRaises((Invalid, Denied)):
            self.broker.call(worker, 'put_artifact', lease=lease,
                             body=deepcopy(authentic['body']), source_refs=[self.source['id']])

    def test_revoked_data_denied_before_row_scan_but_history_is_unchanged(self):
        original = canonical(self.snapshot)
        self.revoke()
        self.assertEqual(self.inspect(self.snapshot['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
        with patch.object(self.broker, '_scan_data', side_effect=AssertionError('Revoked rows scanned')) as scan:
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.broker._load_reference_data(self.snapshot['id'], data_support.iso(data_support.START),
                    data_support.iso(data_support.START + 2700), ['BTCUSDT'])
        self.assertFalse(scan.called)
        retained = self.op('get_artifact', artifact_id=self.snapshot['id'])
        self.assertEqual(canonical(retained), original)
        self.assertEqual(retained['body']['status'], 'STRUCTURE_VERIFIED')
        self.assertFalse(retained['body']['scientific_readiness'])

    def test_supersedes_and_exposure_do_not_turn_replacement_into_hard_dependency(self):
        self.revoke()
        replacement_source = self.f.source([data_support.row(value='11')])
        manifest = self.f.manifest([replacement_source])
        manifest['provenance']['revision'] = 'independent-corrected-fixture/2'
        manifest['supersedes'] = [self.snapshot['id']]
        replacement = self.f.register([replacement_source], manifest)
        self.assertIn(self.snapshot['id'], replacement['exposure'])
        self.assertEqual(self.inspect(replacement['id'])['status'], 'NOT_REVOKED')
        loaded = self.broker._load_reference_data(replacement['id'], data_support.iso(data_support.START),
            data_support.iso(data_support.START + 2700), ['BTCUSDT'])
        self.assertEqual(loaded['rows'][0]['features']['close@1']['value'], '11')
        self.assertFalse(loaded['scientific_readiness'])
        self.assertIn('EXPOSURE_AND_SCIENTIFIC_PLAN_REQUIRED', loaded['remaining_gates'])

    def test_revocation_during_unlocked_scan_prevents_returning_new_rows(self):
        original_scan = self.broker._scan_data
        def revoked_while_scanning(*args, **kwargs):
            scanned = original_scan(*args, **kwargs)
            self.revoke(key='during-scan')
            return scanned
        with patch.object(self.broker, '_scan_data', side_effect=revoked_while_scanning) as scan:
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.broker._load_reference_data(self.snapshot['id'], data_support.iso(data_support.START),
                    data_support.iso(data_support.START + 2700), ['BTCUSDT'])
        self.assertEqual(scan.call_count, 1)
        self.assertEqual(self.inspect(self.snapshot['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
        self.assertEqual(self.op('get_artifact', artifact_id=self.snapshot['id']), self.snapshot)

    def test_unknown_consumer_is_neither_valid_nor_inferred_from_exposure(self):
        self.revoke()
        wrapper = self.op('add_source', data_class='development', exposure=[self.snapshot['id']],
            body={'schema': 'unknown-research-wrapper/1', 'record': self.snapshot['body']})
        view = self.inspect(wrapper['id'])
        self.assertEqual(view['status'], 'UNKNOWN_BINDING')
        self.assertNotEqual(view['status'], 'NOT_REVOKED')

    def test_preupgrade_operator_source_cannot_impersonate_owned_revocation(self):
        # Before this namespace was reserved, add_source allowed arbitrary bodies.
        # Reproduce that historical shape without bypassing any current RPC gate.
        body = {'schema': 'dependency-revocation/1', 'created_at': self.f.now,
            'selector': {'schema': 'data-snapshot/1', 'artifact_id': self.snapshot['id']},
            'request': {'key': 'legacy-forgery', 'dependency_id': self.snapshot['id'],
                'reason': 'Untrusted pre-upgrade source fixture.', 'evidence_refs': [self.evidence['id']]},
            'status': 'REVOKED', 'scientific_readiness': False}
        with self.broker._transaction():
            forged = self.broker._save_artifact({'version': 'local-artifact/1',
                'creator': 'operator', 'origin': 'source', 'data_class': 'operations',
                'body': body, 'source_refs': [], 'exposure': [], 'authority': 'supplied_source_not_certified'})
        self.assertEqual(self.inspect(self.snapshot['id'])['status'], 'NOT_REVOKED')
        self.assertEqual(self.op('get_artifact', artifact_id=forged['id']), forged)
        authentic = self.revoke(key='legacy-forgery')
        self.assertNotEqual(authentic['id'], forged['id'])
        self.assertEqual(self.inspect(self.snapshot['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')

    def test_same_package_bytes_under_later_artifact_id_remain_revoked(self):
        bundle = certification.read_bundle()
        original = self.broker._retain_reference_package(bundle)
        self.revoke(original, key='package')
        self.f.now += 1
        later = self.broker._retain_reference_package(bundle)
        self.assertNotEqual(original, later)
        self.assertEqual(self.inspect(later)['status'], 'INVALIDATED_BY_DEPENDENCY')
        with self.assertRaises((Invalid, Denied, Conflict)):
            self.broker._load_reference_package(later)
        retained = self.op('get_artifact', artifact_id=later)
        self.assertEqual(retained['body']['footprint'],
                         self.op('get_artifact', artifact_id=original)['body']['footprint'])

    def test_different_package_bytes_are_not_semantically_revoked_by_similarity(self):
        bundle = certification.read_bundle()
        original = self.broker._retain_reference_package(bundle)
        self.revoke(original, key='package')
        changed = deepcopy(bundle)
        changed['trading_researcher/expressions.py'] += b'\n# Distinct independent test version.\n'
        other = self.broker._retain_reference_package(changed)
        self.assertEqual(self.inspect(other)['status'], 'NOT_REVOKED')
        self.assertEqual(self.broker._load_reference_package(other), changed)
        self.assertEqual(self.op('get_artifact', artifact_id=other)['authority'], 'retained_source_not_certified')

    def test_revocation_during_real_reference_validation_retains_closed_gap(self):
        package = self.broker._retain_reference_package(certification.read_bundle())
        validate = certification.run_reference_validation
        def revoke_after_validation(*a, **kw):
            report = validate(*a, **kw)
            self.assertEqual(report['status'], 'CERTIFIED', report)
            self.revoke(package, key='during-reference-validation')
            return report
        with patch.object(certification, 'run_reference_validation', side_effect=revoke_after_validation):
            certificate = self.op('certify_reference')
        self.assertEqual(certificate['body']['status'], 'CERTIFICATION_GAP')
        self.assertEqual(self.inspect(certificate['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
        attempts = self.op('inspect_reference_checks')['attempts']
        matching = [a for a in attempts if a['attempt_id'] == certificate['body']['attempt_id']]
        self.assertEqual(len(matching), 1)
        self.assertNotEqual(matching[0]['state'], 'STARTED')
        self.assertEqual(matching[0]['certificate_id'], certificate['id'])

    def test_backup_restore_keeps_revocation_and_original_evidence(self):
        revocation = self.revoke()
        destination = self.f.root / 'revocation-backup'
        self.op('backup_bundle', destination=str(destination))
        restored_path = self.f.root / 'revocation-restored'
        report = restore_bundle(destination, restored_path, self.broker.directory / 'operator.key')
        self.assertEqual(report['status'], 'PASS')
        restored = Broker(restored_path, clock=lambda: self.f.now)
        try:
            self.assertEqual(restored.call(restored.admin_token, 'inspect_dependency_use',
                artifact_id=self.snapshot['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
            self.assertEqual(restored.call(restored.admin_token, 'get_artifact', artifact_id=revocation['id']), revocation)
            self.assertEqual(restored.call(restored.admin_token, 'get_artifact', artifact_id=self.snapshot['id']), self.snapshot)
            self.assertEqual(restored.call(restored.admin_token, 'verify')['status'], 'PASS')
        finally:
            restored.close()


class RevocationMeasurementAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.f = measurement_support.MeasurementRunTests()
        self.f.setUp()
        self.addCleanup(self.f.tearDown)
        self.evidence = self.f.op('add_source', data_class='operations',
            body={'text': 'Independent synthetic measurement revocation fixture.'})

    def revoke(self):
        return self.f.op('revoke_dependency', key='measurement-revocation',
            dependency_id=self.f.snapshot['id'], reason='Synthetic snapshot defect during measurement.',
            evidence_refs=[self.evidence['id']])

    def test_revocation_during_measurement_retains_but_cannot_deliver_new_values(self):
        args = self.f.record_call()
        original_measure = measurements.measure
        def revoke_after_calculation(*a, **kw):
            result = original_measure(*a, **kw)
            self.revoke()
            return result
        with patch.object(measurements, 'measure', side_effect=revoke_after_calculation):
            with self.assertRaises(Denied):
                self.f.clients['first'].call('measure_development', **args)
        saved = self.f.broker._measurement_find(measurements.RESULT, args['call_id'], args['tool_id'])
        self.assertIsNotNone(saved)
        self.assertFalse(saved['body']['delivered'])
        self.assertEqual(saved['body']['result']['status'], 'MEASURED_DEVELOPMENT')
        self.assertEqual(self.f.op('inspect_dependency_use', artifact_id=saved['id'])['status'],
                         'INVALIDATED_BY_DEPENDENCY')

    def test_cached_measurement_does_not_authorize_delivery_after_revocation(self):
        args = self.f.record_call()
        saved = self.f.clients['first'].call('measure_development', **args)
        self.revoke()
        with patch.object(measurements, 'measure', side_effect=AssertionError('Revoked measurement recomputed')) as compute:
            with self.assertRaises(Denied):
                self.f.clients['first'].call('measure_development', **args)
        self.assertFalse(compute.called)
        self.assertEqual(self.f.op('get_artifact', artifact_id=saved['id']), saved)
        self.assertEqual(self.f.op('inspect_dependency_use', artifact_id=saved['id'])['status'],
                         'INVALIDATED_BY_DEPENDENCY')


if __name__ == '__main__':
    unittest.main()
