"""Independent negative probes against the fixed raw-feature contract.

Golden bytes are never rewritten. Child-response mocks test the host boundary;
they do not establish that scientific or conformance checks actually ran.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from trading_researcher import features
from trading_researcher.certification import _runtime_identity
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.errors import Conflict, Denied
import test_binance_normalize as normalization_tests


class FeatureAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = normalization_tests.NormalizeTests()
        cls.fixture.setUp()
        fixture = json.loads((Path(__file__).parent / 'fixtures/reference_feature_cases.json').read_text())
        cls.cases = {case['name']: case for case in fixture['cases']}
        cls.definitions = fixture['definitions']
        cls.results = {}
        bases = {case['base_case'] for case in fixture['cases'] if case['kind'] == 'admission_probe'}
        for name in sorted(bases):
            case = cls.cases[name]
            sources = [cls.fixture.source(source['raw_csv'].encode(), source['month'], source['symbol'])
                       for source in case['sources']]
            cls.results[name] = cls.fixture.run_normalize(sources,
                start=case['universe']['start'], end=case['universe']['end'], partition=case['partition'],
                instruments=case['universe']['instruments'], delay=case['delay_seconds'])
        cls.broker = cls.fixture.broker
        cls.token = cls.broker.admin_token

    @classmethod
    def tearDownClass(cls):
        cls.fixture.tearDown()

    def source(self, body, exposure=(), data_class='development'):
        return self.broker.call(self.token, 'add_source', body=body,
                                data_class=data_class, exposure=list(exposure))

    def blob(self, rows):
        path = self.fixture.root / 'adversarial-rows.jsonl'
        path.write_text(''.join(canonical(row) + '\n' for row in rows), encoding='utf-8')
        return self.broker.call(self.token, 'add_blob_source', path=str(path),
            data_class='development', description='Independent negative fixture rows')

    def alter(self, base_name, change):
        base = self.results[base_name]
        snapshot = base['snapshot']['body']
        row_source = self.broker.call(self.token, 'get_artifact', artifact_id=snapshot['row_source_ids'][0])
        rows = [json.loads(line) for line in self.broker._read_blob_bytes(row_source['body']['blob']['sha256']).splitlines()]
        original = {'rows': deepcopy(rows), 'catalog': features.binding(self.broker, base['snapshot']['id'])['catalog']}
        state = {'rows': rows, 'catalog': deepcopy(original['catalog']),
                 'manifest': deepcopy(snapshot['manifest']), 'normalization': deepcopy(base['normalization']['body'])}
        change(state)
        catalog_id = snapshot['catalog_id']
        if state['catalog'] != original['catalog']:
            catalog_id = self.source({'schema': 'feature-catalog/1', 'features': state['catalog']})['id']
        row_id = row_source['id']
        exposure = list(base['normalization']['exposure'])
        if state['rows'] != original['rows']:
            row_id = self.blob(state['rows'])['id']
            state['normalization']['row_source_ref'] = row_id
            exposure = [ref for ref in exposure if ref != row_source['id']] + [row_id]
        if state['normalization'] != base['normalization']['body']:
            normalization = self.source(state['normalization'], exposure)
            state['manifest']['availability']['evidence_refs'] = [normalization['id']]
        return self.broker.call(self.token, 'register_data_snapshot', catalog_id=catalog_id,
            row_source_ids=[row_id], manifest=state['manifest'])

    @staticmethod
    def assign(value, path, replacement):
        for key in path[:-1]:
            value = value[key]
        value[path[-1]] = deepcopy(replacement)

    def test_thirteen_owned_snapshot_mutations_cannot_pass_replay(self):
        names = [
            'catalog_cannot_change_asset_unit', 'catalog_cannot_change_output_type',
            'unknown_feature_version_is_not_implicitly_certified', 'row_value_must_match_raw_projection',
            'available_at_must_match_explicit_scenario', 'metadata_cannot_promote_assumption_to_publication',
            'metadata_delay_cannot_disagree_with_rows', 'row_anchor_cannot_move_to_source_open',
            'invalid_bar_values_cannot_be_salvaged', 'missing_observation_cannot_be_filled',
            'opposite_symbol_field_cannot_be_injected', 'selection_counts_cannot_be_rewritten',
            'scientific_readiness_cannot_be_promoted',
        ]
        for name in names:
            case = self.cases[name]
            mutation = case['change']
            def change(state):
                target = mutation['object']
                if target in ('catalog', 'rows') and 'path' in mutation:
                    self.assign(state[target], mutation['path'], mutation['value'])
                elif mutation.get('operation') == 'rename_key':
                    state['catalog'][mutation['to']] = state['catalog'].pop(mutation['from'])
                elif mutation.get('operation') == 'insert_all_null_symbol_row':
                    model = state['rows'][0]
                    state['rows'].append({'time': mutation['time'], 'instrument': mutation['instrument'],
                        'features': {ref: {'value': None, 'available_at': mutation['available_at']}
                                     for ref in model['features']}})
                    state['rows'].sort(key=lambda row: (row['time'], row['instrument']))
                elif target == 'manifest':
                    self.assign(state['manifest'], mutation['field'].split('.'), mutation['value'])
                elif target == 'normalization_request':
                    state['normalization'][mutation['field']] = mutation['value']
                elif target == 'normalization_metadata':
                    state['normalization']['selection_counts'][0]['selected'] = mutation['value']
                else:
                    self.fail('Unexecuted fixture mutation: ' + name)
            with self.subTest(name=name), self.assertRaises((Invalid, Denied, Conflict)):
                changed = self.alter(case['base_case'], change)
                features.replay_equal(features.binding(self.broker, changed['id']),
                    features.binding(self.broker, self.results[case['base_case']]['snapshot']['id']))

    def test_protected_wrapper_rejected_before_blob_reads(self):
        base = self.results['btc_ms_exact_fields_and_integer_count']
        protected = self.source({'fixture': 'protected'}, data_class='assessment')
        wrapper = self.source({'fixture': 'wrapper'}, [protected['id']])
        normalization = self.source(base['normalization']['body'],
                                    base['normalization']['exposure'] + [wrapper['id']])
        manifest = deepcopy(base['snapshot']['body']['manifest'])
        manifest['availability']['evidence_refs'] = [normalization['id']]
        with patch.object(self.broker, '_check_data_blobs', side_effect=AssertionError('Raw read before admission')):
            with self.assertRaises(Denied):
                self.broker.call(self.token, 'register_data_snapshot',
                    catalog_id=base['snapshot']['body']['catalog_id'],
                    row_source_ids=base['snapshot']['body']['row_source_ids'], manifest=manifest)

    def test_missing_normalization_field_is_a_typed_rejection(self):
        def remove_delay(state):
            del state['normalization']['delay_seconds']
        changed = self.alter('btc_ms_exact_fields_and_integer_count', remove_delay)
        with self.assertRaises((Invalid, Denied, Conflict)):
            self.broker.call(self.token, 'certify_features', data_snapshot_id=changed['id'])

    def test_worker_and_generic_certificate_namespace_are_denied(self):
        identity = self.results['btc_ms_exact_fields_and_integer_count']['snapshot']['id']
        worker = self.broker.call(self.token, 'register_worker', name='negative-probe',
                                 role='discovery', capabilities=[])['token']
        with patch.object(self.broker, '_backup_bundle_external', side_effect=AssertionError('Unauthorized read')):
            with self.assertRaises(Denied):
                self.broker.call(worker, 'certify_features', data_snapshot_id=identity)
        for schema in ('feature-certificate/1', 'feature-definitions/1', 'feature-source-package/1'):
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                self.source({'schema': schema, 'status': 'CERTIFIED'})

    def test_corrupt_committed_raw_blob_rejected_before_child(self):
        base = self.results['btc_ms_exact_fields_and_integer_count']
        ref = base['snapshot']['body']['manifest']['provenance']['raw_source_refs'][0]
        blob = self.broker.call(self.token, 'get_artifact', artifact_id=ref)['body']['blob']
        path = self.broker._blob_path(blob['sha256'])
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'!')
            with patch('trading_researcher.features.run_validation', side_effect=AssertionError('Child ran')):
                with self.assertRaises((Denied, Conflict)):
                    self.broker.call(self.token, 'certify_features', data_snapshot_id=base['snapshot']['id'])
        finally:
            path.write_bytes(original)

    def report(self, directory):
        base = self.results['btc_ms_exact_fields_and_integer_count']
        bound = features.binding(self.broker, base['snapshot']['id'])
        stdlib = Path(sys.base_prefix) / 'Lib/json/__init__.py'
        return {'status': 'CERTIFIED', 'reason': 'FIXED_CASES_AND_FULL_SOURCE_REPLAY_PASSED',
            'checks': dict(features.CHECKS), 'replay': features.replay_summary(bound),
            'definitions': [deepcopy(entry) for entry in self.definitions if entry['instrument'] == 'BTCUSDT'],
            'binding_hash': digest(bound),
            'environment': {'identity': _runtime_identity(),
                'standard_library': {'Lib/json/__init__.py': hashlib.sha256(stdlib.read_bytes()).hexdigest()},
                'isolation': {'isolated': 1, 'no_site': 1, 'ignore_environment': 1, 'no_bytecode_writes': 1}},
            'footprint': json.loads((Path(directory) / 'source-manifest.json').read_text())}

    def test_malformed_child_outputs_cannot_mint_definitions_or_authority(self):
        mutations = {
            'extra_authority': lambda r: r.update(scientific_readiness=True, scope={'authority': 'scientific_evidence'}),
            'empty_definitions': lambda r: r.update(definitions=[]),
            'empty_replay': lambda r: r.update(replay={}),
            'fitted_state': lambda r: r['definitions'][0].update(fitted_state={'fit_partition': 'assessment'}),
            'boolean_column_is_not_integer_one': lambda r: r['definitions'][0].update(csv_column_index=True),
            'missing_case': lambda r: r['checks'].update(partition_cases=21),
        }
        identity = self.results['btc_ms_exact_fields_and_integer_count']['snapshot']['id']
        for name, mutation in mutations.items():
            def child(command, directory):
                result = self.report(directory)
                mutation(result)
                return result
            with self.subTest(name=name), patch('trading_researcher.binance_normalize._run_child', side_effect=child):
                artifact = self.broker.call(self.token, 'certify_features', data_snapshot_id=identity)
                self.assertEqual(artifact['body']['status'], 'CERTIFICATION_GAP')
                self.assertIsNone(artifact['body']['definitions_id'])
                self.assertIs(artifact['body']['scientific_readiness'], False)

    def test_parent_rejects_copied_source_mutation(self):
        identity = self.results['btc_ms_exact_fields_and_integer_count']['snapshot']['id']
        def child(command, directory):
            report = self.report(directory)
            path = Path(directory) / 'trading_researcher/features.py'
            path.write_bytes(path.read_bytes() + b'\n# deliberate copied-source mutation\n')
            return report
        with patch('trading_researcher.binance_normalize._run_child', side_effect=child):
            artifact = self.broker.call(self.token, 'certify_features', data_snapshot_id=identity)
        self.assertEqual(artifact['body']['status'], 'CERTIFICATION_GAP')
        self.assertIsNone(artifact['body']['definitions_id'])

    def test_real_certificate_binds_snapshot_and_returned_scope_is_detached(self):
        identity = self.results['btc_ms_exact_fields_and_integer_count']['snapshot']['id']
        certificate = self.broker.call(self.token, 'certify_features', data_snapshot_id=identity)
        self.assertEqual(certificate['body']['status'], 'CERTIFIED')
        other = self.results['both_symbols_keep_separate_fields_and_units']['snapshot']['id']
        with self.assertRaises(Denied):
            self.broker.call(self.token, 'feature_certificate_status',
                             certificate_id=certificate['id'], data_snapshot_id=other)
        expected = deepcopy(features.SCOPE)
        try:
            status = self.broker.call(self.token, 'feature_certificate_status',
                                     certificate_id=certificate['id'], data_snapshot_id=identity)
            self.assertEqual(status['status'], 'CURRENT')
            status['scope']['not_certified'].clear()
            self.assertEqual(features.SCOPE, expected)
            certificate['body']['scope']['authority'] = 'scientific_evidence'
            self.assertEqual(features.SCOPE, expected)
        finally:
            features.SCOPE.clear()
            features.SCOPE.update(expected)


if __name__ == '__main__':
    unittest.main()
