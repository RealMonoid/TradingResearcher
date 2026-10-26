"""Host-owned conformance records, pinned expectations and stale-version rejection."""
import copy
import json
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher import certification
from trading_researcher.codec import MAX_BYTES
from trading_researcher.coordination import Broker, Denied, Invalid


class CertificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.broker = Broker(self.tmp.name, clock=lambda: 1000)
        self.admin = self.broker.admin_token

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def op(self, op, **args):
        return self.broker.call(self.admin, op, **args)

    def test_real_fresh_child_certifies_only_the_exercised_implementation(self):
        result = self.op('certify_reference')
        body = result['body']
        self.assertEqual(body['status'], 'CERTIFIED')
        self.assertEqual(body['checks']['expression_cases'], 112)
        self.assertEqual(body['checks']['outcome_cases'], 31)
        self.assertEqual(body['checks']['supplemental_tests'], 16)
        self.assertFalse(body['scientific_readiness'])
        self.assertEqual(result['creator'], 'controller')
        self.assertEqual(result['authority'], 'implementation_conformance_only')
        self.assertEqual(self.op('reference_certificate_status', certificate_id=result['id'])['status'], 'CURRENT')
        self.assertEqual(self.op('get_artifact', artifact_id=result['id']), result)
        self.assertEqual(self.op('verify')['status'], 'PASS')

    def test_workers_and_generic_records_cannot_mint_a_certificate(self):
        token = self.op('register_worker', name='writer', role='formalizer', capabilities=['draft/v1'])['token']
        with patch.object(certification, 'run_reference_validation') as validator:
            with self.assertRaises(Denied):
                self.broker.call(token, 'certify_reference')
            validator.assert_not_called()
        with self.assertRaises(Invalid):
            self.op('add_source', body={'schema': 'implementation-certificate/1'}, data_class='development')
        source = self.op('add_source', body={'text': 'fixture'}, data_class='development')['id']
        context = self.op('create_context', role='formalizer', epoch=1, artifact_ids=[source])['id']
        self.op('enqueue', key='writer', spec={'kind': 'draft/v1', 'context_id': context,
                'purpose': 'Test certificate namespace protection', 'allowed_workers': ['writer'],
                'max_attempts': 1, 'lease_seconds': 30, 'deadline': 2000, 'dependencies': []})
        lease = self.broker.call(token, 'claim')['lease']
        with self.assertRaises(Invalid):
            self.broker.call(token, 'put_artifact', lease=lease,
                             body={'schema': 'implementation-certificate/99'}, source_refs=[source])

    def test_no_caller_can_override_the_profile_or_expected_values(self):
        with patch.object(certification, 'run_reference_validation') as validator:
            for key in ('root', 'expected', 'report', 'profile'):
                with self.subTest(key=key), self.assertRaises(Invalid):
                    self.op('certify_reference', **{key: 'override'})
            validator.assert_not_called()

    def test_fixture_or_specification_mutation_fails_before_candidate_import(self):
        original = certification.read_bundle()
        for name in ('tests/fixtures/reference_expression_cases.json',
                     'tests/fixtures/reference_outcome_cases.json',
                     'docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md'):
            with self.subTest(name=name):
                bundle = copy.deepcopy(original)
                bundle[name] += b'\n'
                with patch.object(certification, 'read_bundle', return_value=bundle):
                    result = self.op('certify_reference')
                self.assertEqual(result['body']['status'], 'CERTIFICATION_GAP')
                self.assertEqual(result['body']['reason'], 'PINNED_INPUT_CHANGED')
                self.assertEqual(self.op('reference_certificate_status', certificate_id=result['id'])['status'],
                                 'CERTIFICATION_GAP')

    def test_changed_implementation_is_tested_and_failed_attempt_retained(self):
        bundle = certification.read_bundle()
        bundle['trading_researcher/expressions.py'] += (
            b'\nReferenceEngine.evaluate = lambda *args, **kwargs: None\n')
        with patch.object(certification, 'read_bundle', return_value=bundle):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['status'], 'CERTIFICATION_GAP')
        self.assertEqual(result['body']['reason'], 'CONFORMANCE_FAILED')
        self.assertEqual(self.op('get_artifact', artifact_id=result['id']), result)

    def test_source_change_during_validation_cannot_receive_a_current_certificate(self):
        original = certification.read_bundle()
        changed = copy.deepcopy(original)
        changed['trading_researcher/expressions.py'] += b'\n# changed during validation\n'
        with patch.object(certification, 'read_bundle', side_effect=[original, changed]):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['status'], 'CERTIFICATION_GAP')
        self.assertEqual(result['body']['reason'], 'SOURCE_CHANGED_DURING_VALIDATION')

    def test_installed_source_change_makes_an_existing_certificate_stale(self):
        result = self.op('certify_reference')
        original = self.op('get_artifact', artifact_id=result['id'])
        bundle = certification.read_bundle()
        bundle['trading_researcher/outcomes.py'] += b'\n# later revision\n'
        with patch.object(certification, 'read_bundle', return_value=bundle):
            status = self.op('reference_certificate_status', certificate_id=result['id'])
        self.assertEqual(status['status'], 'STALE')
        self.assertEqual(self.op('get_artifact', artifact_id=result['id']), original)

    def test_only_owned_certificates_can_be_inspected_as_certificates(self):
        source = self.op('add_source', body={'status': 'CERTIFIED'}, data_class='development')
        with self.assertRaises(Invalid):
            self.op('reference_certificate_status', certificate_id=source['id'])

    def test_cli_creates_a_real_host_record(self):
        result = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'certify-reference',
                                 '--directory', str(Path(self.tmp.name) / 'cli')],
                                capture_output=True, text=True, timeout=40)
        self.assertEqual(result.returncode, 0, result.stderr)
        body = json.loads(result.stdout)
        self.assertEqual(body['body']['status'], 'CERTIFIED')
        self.assertFalse(body['body']['scientific_readiness'])

    def test_timeouts_and_malformed_or_skipped_checks_are_retained_gaps(self):
        with patch.object(certification.subprocess, 'run', side_effect=subprocess.TimeoutExpired('fixture', 30)):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['reason'], 'VALIDATOR_TIMEOUT')
        with patch.object(certification.subprocess, 'run', return_value=subprocess.CompletedProcess(
                [], 0, stdout=b'{truncated', stderr=b'')):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['reason'], 'INVALID_VALIDATOR_RESPONSE')
        passed = self.op('certify_reference')['body']
        passed.pop('schema')
        passed.pop('created_at')
        for name in ('attempt_id', 'source_package_id', 'validation_mode'):
            passed.pop(name)
        passed['checks']['skipped'] = 1
        with patch.object(certification.subprocess, 'run', return_value=subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(passed).encode(), stderr=b'')):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['reason'], 'INVALID_VALIDATOR_RESPONSE')

    def test_parent_detects_mutation_of_copied_expectations(self):
        real_run = certification.subprocess.run
        def mutate_copy(*args, **kwargs):
            result = real_run(*args, **kwargs)
            path = Path(kwargs['cwd']) / 'tests/fixtures/reference_expression_cases.json'
            path.write_bytes(path.read_bytes() + b'\n')
            return result
        with patch.object(certification.subprocess, 'run', side_effect=mutate_copy):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['status'], 'CERTIFICATION_GAP')
        self.assertEqual(result['body']['reason'], 'VALIDATION_SNAPSHOT_CHANGED')

    def test_validation_does_not_hold_the_registry_write_lock(self):
        started, resume = threading.Event(), threading.Event()
        results = []
        def waiting_validator(bundle=None):
            started.set()
            if not resume.wait(10):
                raise RuntimeError('Test coordination timed out')
            return certification._report('CERTIFICATION_GAP', 'TEST_WAIT')
        def certify():
            results.append(self.op('certify_reference'))
        with patch.object(certification, 'run_reference_validation', side_effect=waiting_validator):
            thread = threading.Thread(target=certify)
            thread.start()
            try:
                self.assertTrue(started.wait(5))
                acquired = self.broker._mutex.acquire(timeout=1)
                self.assertTrue(acquired, 'Validation must release registry lock before child work')
                if acquired:
                    self.broker._mutex.release()
                self.assertEqual(self.op('status')['scientific_authority'], False)
            finally:
                resume.set()
                thread.join(10)
            self.assertFalse(thread.is_alive())
            self.assertEqual(results[0]['body']['reason'], 'TEST_WAIT')

    def test_fresh_child_does_not_certify_long_lived_imports(self):
        from trading_researcher.expressions import ReferenceEngine
        with patch.object(ReferenceEngine, 'evaluate', return_value=None):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['status'], 'CERTIFIED')
        status = self.op('reference_certificate_status', certificate_id=result['id'])
        self.assertIn('fresh bound snapshot', status['scope'])

    def test_an_executed_module_outside_the_snapshot_invalidates_dependency_closure(self):
        outside = Path(self.tmp.name) / 'outside_module.py'
        outside.write_text('VALUE = 1\n', encoding='utf-8')
        bundle = certification.read_bundle()
        extra = (
            '\nimport importlib.util, sys\n'
            '_extra_spec = importlib.util.spec_from_file_location("outside_dependency", ' + repr(str(outside)) + ')\n'
            '_extra_module = importlib.util.module_from_spec(_extra_spec)\n'
            '_extra_spec.loader.exec_module(_extra_module)\n'
            'sys.modules["outside_dependency"] = _extra_module\n')
        bundle['trading_researcher/expressions.py'] += extra.encode('utf-8')
        with patch.object(certification, 'read_bundle', return_value=bundle):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['status'], 'CERTIFICATION_GAP')
        self.assertEqual(result['body']['reason'], 'CONFORMANCE_FAILED')

    def test_changed_runtime_makes_existing_certificate_stale(self):
        result = self.op('certify_reference')
        with patch.object(certification, '_environment_current', return_value=False):
            status = self.op('reference_certificate_status', certificate_id=result['id'])
        self.assertEqual(status['status'], 'STALE')

    def test_oversized_gap_reply_cannot_escape_failed_attempt_retention(self):
        report = certification._report('CERTIFICATION_GAP', '',
                                        certification._footprint(certification.read_bundle()))
        size = len(json.dumps(report).encode('utf-8'))
        report['reason'] = 'x' * (MAX_BYTES - 100 - size)
        reply = json.dumps(report).encode('utf-8')
        self.assertEqual(len(reply), MAX_BYTES - 100)
        with patch.object(certification.subprocess, 'run', return_value=subprocess.CompletedProcess(
                [], 0, stdout=reply, stderr=b'')):
            result = self.op('certify_reference')
        self.assertEqual(result['body']['reason'], 'INVALID_VALIDATOR_RESPONSE')
        self.assertEqual(self.op('get_artifact', artifact_id=result['id']), result)

    def test_site_package_paths_are_outside_the_runtime_profile(self):
        base = Path(sys.base_prefix)
        self.assertFalse(certification._runtime_path_allowed(base / 'Lib/site-packages/pkg/__init__.py'))
        self.assertFalse(certification._runtime_path_allowed(base / 'lib/dist-packages/pkg/__init__.py'))

    def test_certificate_retains_exact_source_package_and_replays_without_workspace_reads(self):
        certificate = self.op('certify_reference')
        package_id = certificate['body']['source_package_id']
        package = self.op('get_artifact', artifact_id=package_id)
        self.assertEqual(package['body']['schema'], 'reference-source-package/1')
        self.assertEqual(set(package['body']['files']), set(certification.FILES))
        for name, raw in certification.read_bundle().items():
            descriptor = package['body']['files'][name]
            self.assertEqual(self.broker._read_blob_bytes(descriptor['sha256']), raw)
        with patch.object(certification, 'read_bundle', side_effect=OSError('Workspace unavailable')):
            replay = self.op('revalidate_reference', source_package_id=package_id)
        self.assertEqual(replay['body']['status'], 'CERTIFIED')
        self.assertEqual(replay['body']['validation_mode'], 'retained_package')
        self.assertEqual(replay['body']['source_package_id'], package_id)
        self.assertEqual(replay['body']['footprint'], certificate['body']['footprint'])

    def test_corrupt_package_prevents_current_status_and_replay(self):
        certificate = self.op('certify_reference')
        package_id = certificate['body']['source_package_id']
        package = self.op('get_artifact', artifact_id=package_id)
        identity = package['body']['files']['trading_researcher/expressions.py']['sha256']
        self.broker._blob_path(identity).write_bytes(b'corrupted retained code')
        self.assertEqual(self.op('reference_certificate_status', certificate_id=certificate['id'])['status'],
                         'QUARANTINED')
        replay = self.op('revalidate_reference', source_package_id=package_id)
        self.assertEqual(replay['body']['status'], 'CERTIFICATION_GAP')
        self.assertEqual(replay['body']['reason'], 'RETAINED_SOURCE_UNAVAILABLE')

    def test_complete_backup_restores_replayable_source_and_certificate(self):
        from trading_researcher.storage import restore_bundle
        certificate = self.op('certify_reference')
        package_id = certificate['body']['source_package_id']
        destination = Path(self.tmp.name) / 'complete-backup'
        self.op('backup_bundle', destination=str(destination))
        restored = Path(self.tmp.name) / 'restored-copy'
        restore_bundle(destination, restored, Path(self.tmp.name) / 'operator.key')
        other = Broker(restored, clock=lambda: 1000)
        try:
            status = other.call(other.admin_token, 'reference_certificate_status', certificate_id=certificate['id'])
            self.assertEqual(status['status'], 'CURRENT')
            replay = other.call(other.admin_token, 'revalidate_reference', source_package_id=package_id)
            self.assertEqual(replay['body']['status'], 'CERTIFIED')
            self.assertEqual(replay['body']['footprint'], certificate['body']['footprint'])
        finally:
            other.close()

    def test_process_exit_preserves_source_and_marks_unfinished_validation_interrupted(self):
        directory = Path(self.tmp.name) / 'crashed-validation'
        script = (
            'import os,sys\nfrom trading_researcher.coordination import Broker\n'
            'from trading_researcher import certification\n'
            'certification.run_reference_validation = lambda bundle=None: os._exit(29)\n'
            'broker = Broker(sys.argv[1], clock=lambda:1000)\n'
            'broker.call(broker.admin_token,"certify_reference")\n')
        child = subprocess.run([sys.executable, '-B', '-c', script, str(directory)],
                               capture_output=True, timeout=40)
        self.assertEqual(child.returncode, 29, child.stderr)
        other = Broker(directory, clock=lambda: 1000)
        try:
            attempts = other.call(other.admin_token, 'inspect_reference_checks')['attempts']
            self.assertEqual(len(attempts), 1)
            self.assertEqual(attempts[0]['state'], 'INTERRUPTED')
            self.assertIsNone(attempts[0]['certificate_id'])
            replay = other.call(other.admin_token, 'revalidate_reference',
                                source_package_id=attempts[0]['source_package_id'])
            self.assertEqual(replay['body']['status'], 'CERTIFIED')
        finally:
            other.close()


if __name__ == '__main__':
    unittest.main()
