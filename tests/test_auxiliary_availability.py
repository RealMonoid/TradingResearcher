"""Independent exact-data timing evidence handoff; no model or market calls."""
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from trading_researcher.auxiliary import AuxiliaryResearch
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.features import definitions as raw_definitions
from test_bounded_auxiliary_contract import review_inputs
import test_binance_normalize as normalization_tests
from test_binance_quality import row


REJECTIONS = (Invalid, Denied, Conflict)


class AvailabilitySummaryTests(unittest.TestCase):
    def fixture(self):
        definitions = raw_definitions(['BTCUSDT'])
        universe = {'start': '2020-01-01T00:00:00Z', 'end': '2020-01-01T00:45:00Z', 'instruments': ['BTCUSDT']}
        rows = [{'time': when, 'instrument': 'BTCUSDT', 'features': {
            item['feature_ref']: {'value': None if index else '10.123456789', 'available_at': when + 900}
            for item in definitions}} for index, when in enumerate((1577837700, 1577838600))]
        return rows, definitions, universe

    def summary(self, rows, definitions, universe):
        from trading_researcher.auxiliary_availability import availability_summary
        return availability_summary(rows, definitions, 900, universe)

    def test_exact_timing_preserves_absent_and_null_without_values_or_mutation(self):
        rows, definitions, universe = self.fixture()
        before = deepcopy((rows, definitions, universe))
        self.assertEqual(self.summary(rows, definitions, universe), {
            'status': 'MATCHED_EXACT_FIXED_DELAY', 'checked_rows': 2,
            'checked_feature_samples': 18, 'null_feature_samples': 9,
            'missing_feature_samples': 0, 'absent_grid_rows': 1})
        self.assertEqual((rows, definitions, universe), before)

    def test_missing_feature_is_counted_without_imputation(self):
        rows, definitions, universe = self.fixture()
        del rows[0]['features'][definitions[0]['feature_ref']]
        result = self.summary(rows, definitions, universe)
        self.assertEqual(result['checked_feature_samples'], 17)
        self.assertEqual(result['missing_feature_samples'], 1)
        self.assertEqual(result['null_feature_samples'], 9)
        self.assertEqual(result['absent_grid_rows'], 1)

    def test_other_instrument_fields_are_not_missing_required_features(self):
        rows, definitions, universe = self.fixture()
        definitions += raw_definitions(['ETHUSDT'])
        universe['instruments'].append('ETHUSDT')
        rows[1]['instrument'] = 'ETHUSDT'
        rows[1]['features'] = {item['feature_ref']: {'value': None, 'available_at': rows[1]['time'] + 900}
                              for item in definitions if item['instrument'] == 'ETHUSDT'}
        self.assertEqual(self.summary(rows, definitions, universe), {
            'status': 'MATCHED_EXACT_FIXED_DELAY', 'checked_rows': 2,
            'checked_feature_samples': 18, 'null_feature_samples': 9,
            'missing_feature_samples': 0, 'absent_grid_rows': 4})

    def test_earlier_or_later_availability_is_not_a_nominal_delay_proof(self):
        for index in (0, 1):
            for delta in (-1, 1, 900):
                rows, definitions, universe = self.fixture()
                rows[index]['features'][definitions[0]['feature_ref']]['available_at'] += delta
                with self.subTest(null=index == 1, delta=delta), self.assertRaises(REJECTIONS):
                    self.summary(rows, definitions, universe)

    def test_malformed_availability_never_passes_by_coercion(self):
        for malformed in (None, True, '1577838600', 1577838600.0):
            rows, definitions, universe = self.fixture()
            rows[0]['features'][definitions[0]['feature_ref']]['available_at'] = malformed
            with self.subTest(value=malformed), self.assertRaises(REJECTIONS):
                self.summary(rows, definitions, universe)

    def test_out_of_scope_duplicate_and_unknown_feature_rows_are_rejected(self):
        for change in ('time', 'instrument', 'duplicate', 'feature'):
            rows, definitions, universe = self.fixture()
            if change == 'time':
                rows[1]['time'] = 1577839500
                for sample in rows[1]['features'].values():
                    sample['available_at'] = rows[1]['time'] + 900
            elif change == 'instrument':
                rows[0]['instrument'] = 'ETHUSDT'
            elif change == 'duplicate':
                rows.append(deepcopy(rows[1]))
            else:
                rows[0]['features']['UNKNOWN@1'] = {'value': None, 'available_at': rows[0]['time'] + 900}
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                self.summary(rows, definitions, universe)


class AvailabilityProtocolBaselineTests(unittest.TestCase):
    def test_legacy_packet_is_exactly_preserved_without_evidence_reads(self):
        host, spec, expected = review_inputs('research-ast/1')
        host._feature_certificate_status = Mock(side_effect=AssertionError('Legacy certificate read'))
        host._load_reference_data = Mock(side_effect=AssertionError('Legacy row read'))
        actual = AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)
        self.assertEqual(canonical(actual), canonical(expected))
        self.assertNotIn('availability_evidence', actual)
        host._feature_certificate_status.assert_not_called()
        host._load_reference_data.assert_not_called()


class AuxiliaryAvailabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = normalization_tests.NormalizeTests()
        cls.fixture.setUp()
        try:
            # Three scheduled grid points: an absent first bar, a valid bar,
            # then an invalid keyed bar retained as nine null samples.
            source = cls.fixture.source(row(price='10.123456789') + row(1577837700000, close=1577838000000))
            cls.result = cls.fixture.run_normalize([source], delay=900)
            cls.broker = cls.fixture.broker
            cls.certificate = cls.broker.call(cls.broker.admin_token, 'certify_features',
                data_snapshot_id=cls.result['snapshot']['id'])
            if cls.certificate['body']['status'] != 'CERTIFIED':
                raise AssertionError(cls.certificate['body'])
            cls.snapshot = cls.result['snapshot']
            cls.catalog_id = cls.snapshot['body']['catalog_id']
            cls.definition_id = cls.certificate['body']['definitions_id']
            cls.definition = cls.broker._artifact(cls.definition_id)
            cls.idea = cls.broker.call(cls.broker.admin_token, 'add_research', kind='idea',
                content={'text': 'Synthetic timing-only protocol fixture.'}, scope={}, source_refs=[])
        except BaseException:
            cls.fixture.tearDown()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.fixture.tearDown()

    def harness(self, kind='formalization/v1'):
        """Use actual retained data/certificate; fake only already-completed job metadata."""
        ids = [self.idea['id'], self.catalog_id, self.definition_id, self.snapshot['id'], self.certificate['id']]
        original_inputs = {'idea_id': self.idea['id'], 'catalog_id': self.catalog_id,
                           'definition_ids': [self.definition_id], 'feature_certificate_id': self.certificate['id']}
        target = {'id': 'synthetic-retained-target', 'creator': 'formalizer', 'origin': 'worker',
                  'job_id': 'synthetic-completed-job', 'source_refs': sorted(ids),
                  'body': {'schema': 'formalization-record/1', 'idea_id': self.idea['id'],
                           'catalog_id': self.catalog_id, 'authorization_snapshot': sorted(ids),
                           'candidate': {'scope_ast': {}, 'condition_ast': {}, 'outcome': {'program': {}},
                               'feature_refs': ['BTCUSDT.close@binance-spot-15m-v1'],
                               'test_universe': {**self.snapshot['body']['manifest']['universe'],
                                                 'data_snapshot_ref': self.snapshot['id']}}}}
        formal_context = {'id': 'formal-context', 'role': 'formalizer', 'artifact_ids': sorted(ids)}
        context = deepcopy(formal_context)
        if kind == 'semantic-review/v1':
            context['id'] = 'review-context'
            context['artifact_ids'].append(target['id'])
            inputs = {'formalization_id': target['id'], 'definition_ids': [self.definition_id],
                      'feature_certificate_id': self.certificate['id']}
        else:
            inputs = deepcopy(original_inputs)
        job = {'state': 'completed', 'result_id': target['id'], 'spec': {
            'kind': 'formalization/v1', 'context_id': formal_context['id'],
            'research_epoch_id': 'synthetic-epoch', 'research_inputs': original_inputs}}
        records = {target['id']: target}
        host = SimpleNamespace()
        host._artifact = lambda identity: deepcopy(records[identity]) if identity in records else self.broker._artifact(identity)
        host._context = lambda identity: deepcopy(formal_context if identity == 'formal-context' else context)
        host._job = lambda identity: deepcopy(job)
        # Retained dependencies, source identities, hashes and scan use the real
        # broker. Pre-read tests instrument these explicit host seams.
        for name in ('_feature_certificate_status', '_data_snapshot', '_require_usable_dependencies',
                     '_data_inputs', '_check_data_blobs', '_load_reference_data', '_scan_data',
                     '_blob_path', '_read_blob_bytes', '_dependency_use'):
            setattr(host, name, getattr(self.broker, name))
        host._db = self.broker._db
        host._mutex = self.broker._mutex
        host._now = self.broker._now
        host._declared_definition_origins = self.broker._declared_definition_origins
        host._public_data_target = self.broker._public_data_target
        spec = {'kind': kind, 'context_id': context['id'], 'research_epoch_id': 'synthetic-epoch',
                'allowed_workers': ['reviewer' if kind == 'semantic-review/v1' else 'formalizer'],
                'research_inputs': inputs}
        return host, spec, context, formal_context, records, target, job

    def packet(self, harness):
        return AuxiliaryResearch._auxiliary_packet_for_spec(harness[0], harness[1])

    def test_owned_evidence_is_present_and_identical_for_both_roles(self):
        formalizer = self.packet(self.harness())
        first = formalizer['availability_evidence']
        second = self.packet(self.harness('semantic-review/v1'))['availability_evidence']
        self.assertEqual(first, second)
        self.assertEqual(first['schema'], 'development-availability-evidence/1')
        serialized = canonical(first)
        self.assertIn(self.certificate['id'], serialized)
        self.assertIn(self.snapshot['id'], serialized)
        self.assertIn(self.catalog_id, serialized)
        self.assertIn(self.definition_id, serialized)
        self.assertNotIn('10.123456789', serialized)
        self.assertNotIn('"value":', serialized)
        self.assertEqual(first['certificate_id'], self.certificate['id'])
        self.assertEqual(first['data_snapshot_id'], self.snapshot['id'])
        self.assertEqual(first['catalog_id'], self.catalog_id)
        self.assertEqual(first['definitions_id'], self.definition_id)
        self.assertEqual(first['universe'], self.snapshot['body']['manifest']['universe'])
        self.assertEqual(first['delay_seconds'], 900)
        self.assertEqual(first['certificate_body_sha256'], digest(self.certificate['body']))
        self.assertEqual(first['source_footprint_sha256'], digest(self.certificate['body']['footprint']))
        self.assertEqual(first['row_blobs'], self.certificate['body']['replay']['row_blobs'])
        self.assertNotIn(self.certificate['id'], [source['id'] for source in formalizer['sources']])

    def test_out_of_context_certificate_snapshot_or_definition_fails_before_source_reads(self):
        for identity in (self.certificate['id'], self.snapshot['id'], self.definition_id):
            for kind in ('formalization/v1', 'semantic-review/v1'):
                harness = self.harness(kind)
                host, spec, context, formal_context = harness[:4]
                context['artifact_ids'].remove(identity)
                if kind == 'formalization/v1':
                    formal_context['artifact_ids'].remove(identity)
                host._feature_certificate_status = Mock(side_effect=AssertionError('Premature certificate source read'))
                host._load_reference_data = Mock(side_effect=AssertionError('Premature rows read'))
                with self.subTest(identity=identity, kind=kind), self.assertRaises(REJECTIONS):
                    self.packet(harness)
                host._feature_certificate_status.assert_not_called()
                host._load_reference_data.assert_not_called()

    def test_review_cannot_drop_swap_or_add_evidence_identity(self):
        for change in ('drop', 'swap', 'add'):
            harness = self.harness('semantic-review/v1')
            host, spec, _, _, _, _, job = harness
            if change == 'drop':
                del spec['research_inputs']['feature_certificate_id']
            elif change == 'swap':
                spec['research_inputs']['feature_certificate_id'] = self.snapshot['id']
            else:
                del job['spec']['research_inputs']['feature_certificate_id']
            host._feature_certificate_status = Mock(side_effect=AssertionError('Mismatched handoff read'))
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                self.packet(harness)
            host._feature_certificate_status.assert_not_called()

    def test_forgery_protected_data_and_identity_mismatches_fail_before_source_reads(self):
        mutations = [
            (self.certificate['id'], lambda a: a.update(creator='worker')),
            (self.certificate['id'], lambda a: a.update(origin='source')),
            (self.certificate['id'], lambda a: a.update(data_class='assessment')),
            (self.certificate['id'], lambda a: a.update(authority='supplied_source_not_certified')),
            (self.certificate['id'], lambda a: a['body'].update(data_snapshot_id=self.catalog_id)),
            (self.certificate['id'], lambda a: a['body'].update(definitions_id=self.catalog_id)),
            (self.snapshot['id'], lambda a: a.update(data_class='assessment')),
            (self.snapshot['id'], lambda a: a['body']['manifest'].update(partition='assessment')),
            (self.snapshot['id'], lambda a: a['body'].update(catalog_id=self.definition_id)),
        ]
        for index, (identity, mutate) in enumerate(mutations):
            harness = self.harness()
            host, _, _, _, records = harness[:5]
            records[identity] = self.broker._artifact(identity)
            mutate(records[identity])
            host._data_snapshot = lambda identity: host._artifact(identity)
            host._feature_certificate_status = Mock(side_effect=AssertionError('Forged/protected source read'))
            with self.subTest(index=index), self.assertRaises(REJECTIONS):
                self.packet(harness)
            host._feature_certificate_status.assert_not_called()

    def test_intact_stale_certificate_is_distinct_from_revoked_or_quarantined(self):
        harness = self.harness()
        with patch('trading_researcher.features.read_bundle', return_value={}):
            evidence = self.packet(harness)['availability_evidence']
        self.assertEqual(evidence['schema'], 'development-availability-evidence/1')
        for status in ('INVALIDATED_BY_DEPENDENCY', 'QUARANTINED', 'CERTIFICATION_GAP'):
            harness = self.harness()
            harness[0]._feature_certificate_status = Mock(return_value={'status': status})
            harness[0]._load_reference_data = Mock(side_effect=AssertionError('Invalid certificate row scan'))
            with self.subTest(status=status), self.assertRaises(REJECTIONS):
                self.packet(harness)
            harness[0]._load_reference_data.assert_not_called()

    def test_changed_retained_row_bytes_cannot_reuse_certificate(self):
        descriptor = self.broker._artifact(self.snapshot['body']['row_source_ids'][0])['body']['blob']
        path = self.broker._blob_path(descriptor['sha256'])
        original = path.read_bytes()
        try:
            path.write_bytes(original + b' ')
            with self.assertRaises(REJECTIONS):
                self.packet(self.harness())
        finally:
            path.write_bytes(original)

    def test_review_cannot_change_snapshot_dependencies_or_original_authorization(self):
        for change in ('snapshot', 'feature', 'universe', 'original_context', 'authorization'):
            harness = self.harness('semantic-review/v1')
            host, _, _, formal_context, _, target, _ = harness
            if change == 'snapshot':
                target['body']['candidate']['test_universe']['data_snapshot_ref'] = self.catalog_id
            elif change == 'feature':
                target['body']['candidate']['feature_refs'].append('UNKNOWN.close@unapproved')
            elif change == 'universe':
                target['body']['candidate']['test_universe']['end'] = '2021-01-01T00:00:00Z'
            elif change == 'original_context':
                formal_context['artifact_ids'].remove(self.certificate['id'])
            else:
                target['body']['authorization_snapshot'].remove(self.certificate['id'])
            host._feature_certificate_status = Mock(side_effect=AssertionError('Changed candidate source read'))
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                self.packet(harness)
            host._feature_certificate_status.assert_not_called()

    def test_z_actual_revocation_denies_without_loading_retained_package_or_rows(self):
        evidence = self.broker.call(self.broker.admin_token, 'add_source',
            body={'schema': 'synthetic-test-defect/1', 'reason': 'Intentional fixture revocation'}, data_class='development')
        self.broker.call(self.broker.admin_token, 'revoke_dependency', key='availability-test-revocation',
            dependency_id=self.certificate['id'], reason='Synthetic protocol boundary test', evidence_refs=[evidence['id']])
        harness = self.harness()
        harness[0]._load_reference_data = Mock(side_effect=AssertionError('Revoked row access'))
        with patch.object(self.broker, '_load_feature_package', side_effect=AssertionError('Revoked source package access')) as load:
            with self.assertRaises(REJECTIONS):
                self.packet(harness)
        load.assert_not_called()
        harness[0]._load_reference_data.assert_not_called()


if __name__ == '__main__':
    unittest.main()
