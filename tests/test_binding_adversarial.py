"""Independent binding admission, malformed-response and process-lifecycle probes.

Protected metadata is injected only to reach an otherwise inaccessible denial seam.
No fixed fixture bytes or production runtime files are modified by these tests.
"""
from copy import deepcopy
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher import binding, binance_normalize
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.coordination import Broker
from binding_support import BindingFixture, fixture


class BindingAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = BindingFixture()
        cls.broker, cls.token = cls.setup.broker, cls.setup.token
        cls.formalization = cls.setup.create_formalization()
        cls.compiled = cls.setup.compile(cls.formalization)
        assert cls.compiled['body']['status'] == 'COMPILED', cls.compiled['body'].get('failure_type')

    @classmethod
    def tearDownClass(cls):
        cls.setup.close()

    def execute(self, **extra):
        return self.broker.call(self.token, 'execute_development', compiled_id=self.compiled['id'], **extra)

    def assert_gap(self, artifact):
        self.assertEqual(artifact['body']['status'], 'EXECUTION_GAP', artifact['body'].get('failure_type'))
        self.assertIsNone(artifact['body']['result'])
        self.assertIs(artifact['body']['scientific_readiness'], False)
        self.assertEqual(artifact['blob_refs'], [])

    def block_fixture_attempt(self, record):
        self.broker.call(self.setup.worker, 'block',
            lease={'job_id': record['job_id'], 'generation': record['generation']},
            reason='Independent incomplete-draft probe finished', needs=[],
            retry_when='No retry requested by this fixture')

    def test_uncompleted_and_counterfeit_records_cannot_bind(self):
        unfinished = self.setup.create_formalization(submit=False)
        try:
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.setup.compile(unfinished)
        finally:
            self.block_fixture_attempt(unfinished)
        supplied = self.broker.call(self.token, 'add_source', body={'schema': 'supplied-claim/1',
            'status': 'CERTIFIED'}, data_class='development')
        for field in ('formalization_id', 'feature_certificate_id', 'reference_certificate_id'):
            with self.subTest(field=field), self.assertRaises((Invalid, Denied, Conflict)):
                self.setup.compile(self.formalization, **{field: supplied['id']})

    def test_mutated_original_or_compiled_bytes_fail_identity_check(self):
        for artifact, mutation, operation in (
            (self.formalization, lambda body: body['original_idea']['content'].update(text='Substituted idea'),
             lambda: self.setup.compile(self.formalization)),
            (self.compiled, lambda body: body['compilation']['request'].update(horizon_bars=2), self.execute),
        ):
            stored = self.broker._db.execute('SELECT envelope FROM artifacts WHERE id=?', (artifact['id'],)).fetchone()[0]
            changed = decode(stored)
            mutation(changed['body'])
            with self.assertRaises(sqlite3.IntegrityError):
                self.broker._db.execute('UPDATE artifacts SET envelope=? WHERE id=?', (canonical(changed), artifact['id']))
            self.assertEqual(self.broker._db.execute('SELECT envelope FROM artifacts WHERE id=?',
                                                    (artifact['id'],)).fetchone()[0], stored)

    def test_unsupported_and_wrong_program_catalog_are_retained_gaps(self):
        mutations = [lambda c: c.update(claim_kind='association'),
                     lambda c: c['condition_ast'].update(catalog_hash='0' * 64)]
        for mutation in mutations:
            retained = self.setup.create_formalization(submit=False, candidate_transform=mutation)
            try:
                self.assertEqual(retained['body']['assessment']['status'], 'RETAINED_GAP')
                with self.assertRaises((Invalid, Denied, Conflict)):
                    self.setup.compile(retained)
            finally:
                self.block_fixture_attempt(retained)
        original = self.broker._record_formalization
        def ambiguous(actor, lease, idea_id, catalog_id, candidate, semantic_report):
            semantic_report = {**semantic_report, 'status': 'ambiguous',
                               'differences': ['Unresolved fixture interpretation']}
            return original(actor, lease, idea_id, catalog_id, candidate, semantic_report)
        with patch.object(self.broker, '_record_formalization', side_effect=ambiguous):
            retained = self.setup.create_formalization(submit=False)
        try:
            self.assertEqual(retained['body']['assessment']['status'], 'RETAINED_GAP')
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.setup.compile(retained)
        finally:
            self.block_fixture_attempt(retained)

    def test_snapshot_and_catalog_identities_are_exact(self):
        other = self.broker.call(self.token, 'add_source', body={'fixture': 'another-identity'}, data_class='development')
        altered = self.setup.create_formalization(candidate_transform=lambda c:
            c['test_universe'].update(data_snapshot_ref=other['id']))
        with self.assertRaises((Invalid, Denied, Conflict)):
            self.setup.compile(altered)
        old_snapshot = self.setup.snapshot
        catalog = self.broker.call(self.token, 'get_artifact', artifact_id=old_snapshot['body']['catalog_id'])
        equivalent = self.broker.call(self.token, 'add_source', body=catalog['body'],
                                      data_class='development', exposure=[other['id']])
        try:
            self.setup.snapshot = deepcopy(old_snapshot)
            self.setup.snapshot['body']['catalog_id'] = equivalent['id']
            altered = self.setup.create_formalization()
        finally:
            self.setup.snapshot = old_snapshot
        with self.assertRaises((Invalid, Denied, Conflict)):
            self.setup.compile(altered)
        with self.assertRaises(Denied):
            self.broker.call(self.token, 'feature_certificate_status',
                certificate_id=self.setup.feature['id'], data_snapshot_id=other['id'])

    def test_intact_retained_versions_allow_stale_installed_currency(self):
        with patch('trading_researcher.features.read_bundle', return_value={}):
            feature_status = self.broker.call(self.token, 'feature_certificate_status',
                                            certificate_id=self.setup.feature['id'])
            self.assertEqual(feature_status['status'], 'STALE')
            compiled = self.setup.compile(self.formalization)
            self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'].get('failure_type'))
        with patch('trading_researcher.certification.read_bundle', return_value={}):
            reference_status = self.broker.call(self.token, 'reference_certificate_status',
                                              certificate_id=self.setup.reference['id'])
            self.assertEqual(reference_status['status'], 'STALE')
            result = self.execute()
            self.assertEqual(result['body']['status'], 'DESCRIPTIVE_EXECUTION', result['body'].get('failure_type'))

    def test_corrupt_feature_source_missing_reference_and_runtime_mismatch_fail(self):
        package = self.broker.call(self.token, 'get_artifact', artifact_id=self.setup.feature['body']['source_package_id'])
        path = self.broker._blob_path(package['body']['files']['trading_researcher/features.py']['sha256'])
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'\n# corrupt fixture\n')
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.setup.compile(self.formalization)
        finally:
            path.write_bytes(original)
        with patch.object(self.broker, '_load_reference_package', side_effect=Denied('Missing retained package')):
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.execute()
        with patch('trading_researcher.binding._environment_current', return_value=False):
            with self.assertRaises((Invalid, Denied, Conflict)):
                self.execute()

    def test_metadata_compilation_and_stale_parent_function_do_not_execute_parent_calculator(self):
        with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Compile loaded rows')):
            with patch('trading_researcher.binding.compile_payload', side_effect=AssertionError('Stale parent calculator')):
                compiled = self.setup.compile(self.formalization)
        self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'].get('failure_type'))

    def test_protected_execution_denied_before_any_dependency_or_blob_loader(self):
        for partition in ('assessment', 'corroboration'):
            # Trusted setup only: actual formalizer permissions do not grant this route.
            with self.broker._transaction():
                snapshot = self.broker._save_artifact({'creator': 'controller', 'origin': 'source',
                    'data_class': 'assessment', 'exposure': [], 'source_refs': [],
                    'body': {'schema': 'data-snapshot/1', 'manifest': {'partition': partition}}})
                body = deepcopy(self.compiled['body'])
                body['data_snapshot_id'] = snapshot['id']
                record = self.broker._save_artifact({'creator': 'controller', 'origin': 'controller',
                    'data_class': 'assessment', 'authority': binding.AUTHORITY, 'exposure': [],
                    'source_refs': [], 'body': body})
            with self.subTest(partition=partition), patch.object(self.broker, '_bound_dependencies',
                    side_effect=AssertionError('Protected dependency read')):
                with patch.object(self.broker, '_read_blob_bytes', side_effect=AssertionError('Protected blob read')):
                    with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('Protected row read')):
                        with self.assertRaises(Denied):
                            self.broker.call(self.token, 'execute_development', compiled_id=record['id'])

    def test_development_data_wrapper_does_not_launder_protected_input(self):
        protected = self.broker.call(self.token, 'add_source', body={'fixture': 'protected'}, data_class='assessment')
        wrapper = self.broker.call(self.token, 'add_source', body={'fixture': 'development-wrapper'},
                                   data_class='development', exposure=[protected['id']])
        norm = self.setup.normalization
        replacement = self.broker.call(self.token, 'add_source', body=norm['body'], data_class='development',
                                       exposure=norm['exposure'] + [wrapper['id']])
        data = self.setup.snapshot['body']
        manifest = deepcopy(data['manifest'])
        manifest['availability']['evidence_refs'] = [replacement['id']]
        with patch.object(self.broker, '_check_data_blobs', side_effect=AssertionError('Protected blob read')):
            with self.assertRaises(Denied):
                self.broker.call(self.token, 'register_data_snapshot', catalog_id=data['catalog_id'],
                                 row_source_ids=data['row_source_ids'], manifest=manifest)

    def test_workers_overrides_and_missing_or_invalid_controls_are_rejected(self):
        for op, args in [('compile_hypothesis', {}), ('execute_development', {'compiled_id': self.compiled['id']})]:
            with self.subTest(op=op), self.assertRaises(Denied):
                self.broker.call(self.setup.worker, op, **args)
        for key, value in {'candidate': {}, 'data_snapshot_id': 'other', 'as_of': '2020-01-01T00:30:00Z', 'max_steps': 1}.items():
            with self.subTest(override=key), self.assertRaises(Invalid):
                self.execute(**{key: value})
        arguments = deepcopy(self.compiled['body']['dependency_arguments'])
        for key in ('as_of', 'max_steps'):
            changed = {k: v for k, v in arguments.items() if k != key}
            with self.subTest(missing=key), self.assertRaises(Invalid):
                self.broker.call(self.token, 'compile_hypothesis', **changed)
        for budget in (True, 10000001):
            with self.subTest(budget=budget), self.assertRaises(Invalid):
                self.setup.compile(self.formalization, max_steps=budget)

    def test_malformed_execution_response_cannot_publish_success(self):
        original = binance_normalize._run_child
        variants = ('request_hash', 'candidate_ref', 'data_snapshot_ref', 'source_footprint',
                    'scientific_readiness', 'contrast_effect', 'partial_cases')
        for variant in variants:
            def child(command, directory):
                report = original(command, directory)
                if report['mode'] != 'execute':
                    return report
                result = report['result']
                if variant == 'request_hash':
                    report['request_hash'] = '0' * 64
                elif variant in ('candidate_ref', 'data_snapshot_ref'):
                    result['report']['request'][variant] = 'substituted'
                elif variant == 'source_footprint':
                    report['footprint'][binding.DRIVER] = '0' * 64
                elif variant == 'scientific_readiness':
                    result['scientific_readiness'] = True
                elif variant == 'contrast_effect':
                    result['contrast']['effect'] = {'numerator': '999', 'denominator': '1'}
                else:
                    path = Path(directory) / 'cases.jsonl'
                    raw = path.read_bytes().splitlines(keepends=True)[0]
                    path.write_bytes(raw)
                    result['case_blob'] = {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
                return report
            with self.subTest(variant=variant), patch('trading_researcher.binance_normalize._run_child', side_effect=child):
                self.assert_gap(self.execute())

    def test_real_owned_child_timeout_overflow_and_cancellation_are_reaped(self):
        real_popen = subprocess.Popen
        variants = [('timeout', 'import time;time.sleep(30)', 0.1),
                    ('stdout', "print('x'*1100000)", 10),
                    ('stderr', "import sys;sys.stderr.write('x'*9000)", 10),
                    ('cancel', 'import time;time.sleep(30)', 10)]
        for label, code, timeout in variants:
            processes = []
            def start(command, **kwargs):
                process = real_popen([sys.executable, '-I', '-S', '-B', '-c', code], **kwargs)
                processes.append(process)
                if label == 'cancel':
                    wait = process.wait
                    first = [True]
                    def interrupt_wait(*args, **options):
                        if first[0]:
                            first[0] = False
                            raise KeyboardInterrupt
                        return wait(*args, **options)
                    process.wait = interrupt_wait
                return process
            with self.subTest(label=label), patch('trading_researcher.binance_normalize.subprocess.Popen', side_effect=start):
                with patch('trading_researcher.binance_normalize.NORMALIZATION_TIMEOUT', timeout):
                    if label == 'cancel':
                        with self.assertRaises(KeyboardInterrupt):
                            self.execute()
                    else:
                        self.assert_gap(self.execute())
            self.assertTrue(processes)
            self.assertTrue(all(process.poll() is not None for process in processes))
            view = self.broker.call(self.token, 'inspect_bound_computations')
            self.assertEqual(view['pending'], 0)
            if label == 'cancel':
                self.assertEqual(view['attempts'][0]['state'], 'INTERRUPTED')


class BindingInputWindowTests(unittest.TestCase):
    def test_outcome_review_gap_keeps_available_prior_input(self):
        base = fixture()['baseline']
        candidate = deepcopy(base['candidate'])
        candidate['test_universe']['start'] = '2020-01-01T00:30:00Z'
        candidate['outcome']['program']['expression'] = {'op': 'lag', 'bars': 2,
            'arg': {'op': 'feature', 'ref': 'BTCUSDT.close@binance-spot-15m-v1'}}
        payload = {'formalization_id': 'fixture:formalization', 'candidate': candidate,
            'catalog': base['catalog'], 'data_manifest': {'universe': base['expected_compiled_request']['universe']},
            **base['compile_options']}
        compiled = binding.compile_payload(payload)
        self.assertEqual(compiled['row_window']['start'], '2020-01-01T00:15:00Z')
        # This preserves an available value; it must not upgrade the existing review gap.
        from trading_researcher.outcomes import materialize_reference
        report = materialize_reference(compiled['request'], base['catalog'], base['rows'])
        self.assertEqual(report['cases'][0]['status'], 'REVIEW_REQUIRED')
        self.assertEqual(report['cases'][0]['outcome'], {'numerator': '101', 'denominator': '1'})

    def test_verifier_rejects_self_consistent_contrast_with_impossible_scope_state(self):
        from trading_researcher.outcomes import reference_contrast, STATES
        base = fixture()['baseline']
        payload = {'formalization_id': 'fixture:formalization', 'candidate': base['candidate'],
            'catalog': base['catalog'], 'data_manifest': {'universe': base['expected_compiled_request']['universe']},
            **base['compile_options']}
        compiled = binding.compile_payload(payload)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            raw = ''.join(canonical(row) + '\n' for row in base['rows']).encode()
            (directory / 'rows.jsonl').write_bytes(raw)
            execution_input = {'compilation_input': payload, 'compilation_hash': digest(compiled),
                'rows': {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}}
            result = binding._execute(execution_input, directory)
            cases = [decode(line) for line in (directory / 'cases.jsonl').read_bytes().splitlines()]
            cases[0]['status'] = 'SCOPE_FALSE'  # Impossible: scope remains true and outcome/trace still exist.
            counts = Counter(case['status'] for case in cases)
            result['report']['state_counts'] = {state: counts[state] for state in sorted(STATES)}
            result['contrast'] = reference_contrast({**result['report'], 'cases': cases})
            raw = ''.join(canonical(case) + '\n' for case in cases).encode()
            (directory / 'cases.jsonl').write_bytes(raw)
            result['case_blob'] = {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
            with self.assertRaises((Invalid, Denied, Conflict)):
                binding._verify_execution({'execution_input': execution_input, 'result': result}, directory)


if __name__ == '__main__':
    unittest.main()
