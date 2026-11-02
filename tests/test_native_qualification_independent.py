"""Independent qualifier orchestration adversaries using temporary fake inputs.

The five explicitly trusted profile seams are substituted. No native binary,
NumPy, actual study or protected data is executed or qualified by these tests.
The tiny runtime archive reuses the independently fixed runtime-owner fixture.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from test_native_runtime_independent import archive, manifest, MEMBERS
from trading_researcher import native_qualification as owner
from trading_researcher.codec import canonical, digest
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.native_runtime import NativeRuntimes, verify_tree
from trading_researcher.server import Client, LocalServer, RemoteError
from trading_researcher.storage import restore_bundle


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCHEMA = 'native-qualification-source/1'
INPUT_SCHEMA = 'native-runtime-qualification-input/1'
RESULT_SCHEMA = 'native-runtime-qualification/1'
LIMITS = {'max_compute_ms': 300000, 'max_storage_bytes': 268435456}
META = 1048576
SOURCES = {'trading_researcher/native_backend.py': b'# synthetic trusted profile input, never executed\n',
           'trading_researcher/native_environment.py': b'# synthetic metadata checker input, never executed\n'}
LOG = b'Retained synthetic conformance transcript; not binary qualification.\n'
CHILD_BYTES = b'actual tiny child scratch bytes'


def footprint(source):
    return {name: hashlib.sha256(raw).hexdigest() for name, raw in source.items()}


class NativeQualificationIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / 'registry'
        self.broker = Broker(self.directory, clock=lambda: 1000)
        self.addCleanup(self.broker.close)
        self.token = self.broker.admin_token
        self.raw, self.manifest = archive(), manifest()
        path = self.root / 'tiny-runtime.zip'; path.write_bytes(self.raw)
        self.archive = self.op('add_blob_source', path=str(path), data_class='operations',
                               description='Independent invented input, never a native certificate')
        self.runtime = self.op('retain_native_runtime', key='retained-fixture',
                               archive_id=self.archive['id'], manifest=self.manifest)
        self.profile = owner.profile
        self.production_runtime_validator = self.profile.validate_runtime
        self.source = dict(SOURCES)
        self.executions = []
        self.cache = None
        self.capture = self.start_patch('capture_source', side_effect=lambda: dict(self.source))
        self.runtime_gate = self.start_patch('validate_runtime', return_value=None)
        self.hosts = self.start_patch('host_inputs', return_value=[])
        self.runner = self.start_patch('execute', side_effect=self.execute)
        self.validator = self.start_patch('validate_report', side_effect=self.validate)

    def start_patch(self, name, **kwargs):
        replacement = patch.object(self.profile, name, **kwargs)
        value = replacement.start()
        self.addCleanup(replacement.stop)
        return value

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def qualify(self, key='qualification', runtime_id=None):
        return self.op('qualify_native_runtime', key=key,
                       runtime_id=self.runtime['id'] if runtime_id is None else runtime_id)

    def inspect(self, identity):
        return self.op('inspect_native_runtime_qualification', qualification_id=identity)

    def artifacts(self, schema):
        return [self.broker._artifact(row[0]) for row in self.broker._db.execute(
            "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?", (schema,))]

    def report(self, source, capsule):
        return {'scope': 'trusted_synthetic_runner_no_binary_qualification',
                'input_id': capsule['id'], 'runtime_id': capsule['body']['runtime_id'],
                'source_footprint': footprint(source), 'host_images': capsule['body']['host_images']}

    def execute(self, source, capsule, directory, remaining, meter, outputs):
        self.assertEqual(source, SOURCES)
        self.assertEqual(capsule['body']['limits'], LIMITS)
        self.assertGreater(remaining(), 0)
        self.cache = directory
        self.executions.append(capsule['id'])
        scratch = self.root / 'synthetic-child-scratch.bin'; scratch.write_bytes(CHILD_BYTES)
        meter['materialized_bytes'] += len(CHILD_BYTES)
        outputs.append(('synthetic/transcript.txt', LOG))
        return self.report(source, capsule)

    def validate(self, report, source, capsule, directory):
        if report != self.report(source, capsule):
            raise Invalid('Independent synthetic report identity differs')
        verify_tree(directory, capsule['body']['runtime_manifest'])

    def assert_gap(self, certificate, failure_type=None):
        self.assertEqual(certificate['body']['status'], 'CERTIFICATION_GAP')
        self.assertIs(certificate['body']['scientific_readiness'], False)
        self.assertIsNotNone(certificate['body']['failure'])
        if failure_type is not None:
            self.assertIn(failure_type, [failure['type'] for failure in certificate['body']['failures']])
        view = self.inspect(certificate['id'])
        self.assertEqual(view['status'], 'CERTIFICATION_GAP')
        self.assertEqual(view['certificate_id'], certificate['id'])
        self.assertIs(view['scientific_readiness'], False)
        return view

    def evidence(self):
        return self.op('add_source', data_class='operations',
                       body={'synthetic_technical_defect': 'fixture only; no empirical result'})

    def revoke(self, identity, key='synthetic-defect'):
        return self.op('revoke_dependency', key=key, dependency_id=identity,
                       reason='Independent synthetic dependency defect', evidence_refs=[self.evidence()['id']])

    def reopen(self):
        self.broker.close()
        self.broker = Broker(self.directory, clock=lambda: 1000)
        self.addCleanup(self.broker.close)
        self.token = self.broker.admin_token

    def test_success_retains_exact_detached_closure_and_all_actual_byte_charges(self):
        certificate = self.qualify()
        body = certificate['body']
        capsule = self.broker._artifact(body['input_id'])
        source = self.broker._artifact(body['source_package_id'])
        request = {'key': 'qualification', 'runtime_id': self.runtime['id']}
        for artifact, schema in ((certificate, RESULT_SCHEMA), (capsule, INPUT_SCHEMA), (source, SOURCE_SCHEMA)):
            self.assertEqual((artifact['creator'], artifact['origin'], artifact['data_class']),
                             ('controller', 'controller', 'operations'))
            self.assertEqual(artifact['body']['schema'], schema)
        self.assertEqual(body['status'], 'CERTIFIED')
        self.assertIs(body['scientific_readiness'], False)
        self.assertIsNone(body['failure'])
        self.assertEqual(body['request'], request)
        self.assertEqual(capsule['body']['request'], request)
        self.assertEqual(capsule['body']['runtime_manifest'], self.manifest)
        self.assertEqual(capsule['body']['source_footprint'], footprint(SOURCES))
        self.assertEqual(capsule['body']['host_images'], [])
        self.assertEqual(capsule['body']['limits'], LIMITS)
        self.assertEqual(source['body']['footprint'], footprint(SOURCES))
        self.assertEqual(set(source['blob_refs']), set(footprint(SOURCES).values()))
        for name, raw in SOURCES.items():
            self.assertEqual(self.broker._read_blob_bytes(source['body']['files'][name]['sha256']), raw)
        self.assertEqual(capsule['source_refs'], sorted([self.runtime['id'], source['id']]))
        self.assertEqual(certificate['source_refs'], [capsule['id']])
        for identity in (capsule['id'], source['id'], self.runtime['id'], self.archive['id']):
            self.assertIn(identity, certificate['exposure'])
        initial = len(self.raw) + 2 * sum(map(len, SOURCES.values())) + META
        self.assertEqual(capsule['body']['initial_storage_bytes'], initial)
        expected_storage = initial + sum(map(len, MEMBERS.values())) + len(CHILD_BYTES) + len(LOG) + META
        self.assertEqual(body['settlement']['storage_bytes'], expected_storage)
        self.assertIs(body['settlement']['usage_known'], True)
        self.assertGreaterEqual(body['settlement']['compute_ms'], 0)
        self.assertIn(hashlib.sha256(LOG).hexdigest(), certificate['blob_refs'])
        self.assertEqual(self.broker._read_blob_bytes(hashlib.sha256(LOG).hexdigest()), LOG)
        self.assertEqual(body['report'], self.report(SOURCES, capsule))
        view = self.inspect(certificate['id'])
        self.assertEqual(view['status'], 'CURRENT')
        self.assertEqual(self.inspect(capsule['id']), view)
        self.assertEqual((view['input_id'], view['certificate_id']), (capsule['id'], certificate['id']))
        self.assertEqual([attempt['state'] for attempt in view['attempts']], ['COMPLETED'])
        dependency = self.op('inspect_dependency_use', artifact_id=certificate['id'])
        self.assertEqual(dependency['status'], 'NOT_REVOKED')
        self.assertEqual(set(dependency['checked_versions']),
                         {certificate['id'], capsule['id'], source['id'], self.runtime['id']})
        body['request']['key'] = 'caller mutation'
        self.assertEqual(self.broker._artifact(certificate['id'])['body']['request'], request)
        with self.assertRaises(sqlite3.IntegrityError):
            self.broker._db.execute('UPDATE artifacts SET envelope=? WHERE id=?',
                                    (canonical({'forged': True}), certificate['id']))
        self.assertEqual(self.op('verify')['status'], 'PASS')

    def test_capsule_and_started_are_durable_before_materialization_or_execution(self):
        original = NativeRuntimes._materialize
        observed = []

        def materialize(runtimes, identity, meter):
            with closing(sqlite3.connect((self.directory / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
                rows = db.execute("SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?",
                                  (INPUT_SCHEMA,)).fetchall()
                self.assertEqual(len(rows), 1)
                events = [json.loads(raw) for raw, in db.execute('SELECT envelope FROM events ORDER BY seq')]
                started = [event for event in events if event['action'] == 'bound_computation_started'
                           and event['details'].get('retained_input_id') == rows[0][0]]
                self.assertEqual(len(started), 1)
                observed.append(rows[0][0])
            return original(runtimes, identity, meter)

        with patch.object(NativeRuntimes, '_materialize', materialize):
            certificate = self.qualify()
        self.assertEqual(observed, [certificate['body']['input_id']])
        self.assertEqual(self.executions, observed)

    def test_exact_key_replay_is_original_history_and_changed_runtime_conflicts(self):
        certificate = self.qualify()
        other = self.op('retain_native_runtime', key='runtime-alias', archive_id=self.archive['id'], manifest=self.manifest)
        with patch.object(self.profile, 'capture_source', side_effect=AssertionError('Replayed key recaptured source')), \
                patch.object(self.profile, 'execute', side_effect=AssertionError('Replayed key executed again')):
            self.assertEqual(self.qualify(), certificate)
            with self.assertRaises(Conflict): self.qualify(runtime_id=other['id'])
        self.assertEqual(len(self.artifacts(INPUT_SCHEMA)), 1)
        self.assertEqual(len(self.artifacts(RESULT_SCHEMA)), 1)

    def test_live_same_key_conflicts_and_inspection_does_not_start_another_attempt(self):
        entered, release = threading.Event(), threading.Event()

        def blocked(*args):
            entered.set()
            self.assertTrue(release.wait(timeout=5))
            return self.execute(*args)

        with patch.object(self.profile, 'execute', side_effect=blocked), ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(self.qualify)
            try:
                self.assertTrue(entered.wait(timeout=5))
                capsule = self.artifacts(INPUT_SCHEMA)[0]
                view = self.inspect(capsule['id'])
                self.assertEqual(view['status'], 'RUNNING')
                self.assertIsNone(view['certificate_id'])
                with self.assertRaises(Conflict): self.qualify()
            finally:
                release.set()
            certificate = future.result(timeout=10)
        self.assertEqual(certificate['body']['status'], 'CERTIFIED')
        self.assertEqual(len(self.artifacts(INPUT_SCHEMA)), 1)

    def test_operator_http_and_workers_enforce_authority_before_lookup(self):
        worker = self.op('register_worker', name='qualifier-reader', role='discovery', capabilities=[])['token']
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Unauthorized lookup')):
            for operation, args in (
                ('qualify_native_runtime', {'key': 'denied', 'runtime_id': '0' * 64}),
                ('inspect_native_runtime_qualification', {'qualification_id': '0' * 64})):
                with self.subTest(operation=operation), self.assertRaises(Denied):
                    self.broker.call(worker, operation, **args)
        server = LocalServer(self.broker)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            operator, researcher = Client(server.url, self.token), Client(server.url, worker)
            with self.assertRaises(RemoteError) as error:
                researcher.call('qualify_native_runtime', key='http-denied', runtime_id=self.runtime['id'])
            self.assertEqual(error.exception.status, 403)
            certificate = operator.call('qualify_native_runtime', key='http', runtime_id=self.runtime['id'])
            view = operator.call('inspect_native_runtime_qualification', qualification_id=certificate['id'])
            self.assertEqual(view['status'], 'CURRENT')
            self.assertIs(view['scientific_readiness'], False)
        finally:
            server.shutdown(); thread.join(timeout=5); server.server_close()

    def test_all_owned_namespaces_reject_generic_and_valid_worker_forgery(self):
        worker = self.op('register_worker', name='forger', role='discovery', capabilities=['draft/v1'])['token']
        source = self.op('add_source', data_class='development', body={'synthetic': 'worker context'})
        context = self.op('create_context', role='discovery', epoch=1, artifact_ids=[source['id']])
        self.op('enqueue', key='forgery-job', spec={
            'kind': 'draft/v1', 'context_id': context['id'], 'purpose': 'Synthetic forgery rejection fixture',
            'allowed_workers': ['forger'], 'max_attempts': 1, 'lease_seconds': 10,
            'deadline': 1100, 'dependencies': []})
        lease = self.broker.call(worker, 'claim')['lease']
        for schema in (SOURCE_SCHEMA, INPUT_SCHEMA, RESULT_SCHEMA):
            with self.subTest(schema=schema):
                with self.assertRaises(Invalid):
                    self.op('add_source', data_class='operations', body={'schema': schema, 'status': 'CERTIFIED'})
                with self.assertRaises(Invalid):
                    self.broker.call(worker, 'put_artifact', lease=lease,
                                     body={'schema': schema, 'status': 'CERTIFIED'}, source_refs=[source['id']])
        self.assertEqual(self.artifacts(RESULT_SCHEMA), [])

    def test_production_runtime_pin_gate_does_not_accept_arbitrary_compatible_metadata(self):
        with patch.object(self.profile, 'validate_runtime', side_effect=self.production_runtime_validator), \
                patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Unqualified runtime materialized')), \
                patch.object(self.profile, 'execute', side_effect=AssertionError('Unqualified runtime executed')):
            certificate = self.qualify(key='unqualified-tiny-runtime')
        self.assert_gap(certificate, 'Invalid')
        self.assertIsNone(certificate['body']['report'])
        self.assertEqual(len(self.artifacts(RESULT_SCHEMA)), 1)
        self.assertEqual(len(self.artifacts(INPUT_SCHEMA)), 1)
        view = self.inspect(certificate['id'])
        self.assertEqual([attempt['state'] for attempt in view['attempts']], ['COMPLETED'])
        self.assertFalse((self.directory / 'native-runtime-cache').exists())

    def test_ordinary_runner_exception_retains_failure_outputs_usage_and_original_key(self):
        def fail(source, capsule, directory, remaining, meter, outputs):
            self.execute(source, capsule, directory, remaining, meter, outputs)
            raise RuntimeError('Independent synthetic runner error')

        with patch.object(self.profile, 'execute', side_effect=fail): certificate = self.qualify()
        self.assert_gap(certificate, 'RuntimeError')
        self.assertIn(hashlib.sha256(LOG).hexdigest(), certificate['blob_refs'])
        self.assertIs(certificate['body']['settlement']['usage_known'], True)
        with patch.object(self.profile, 'execute', side_effect=AssertionError('Failed key retried')):
            self.assertEqual(self.qualify(), certificate)

    def test_base_exception_is_retained_then_reraised_without_erasing_actual_output(self):
        def cancel(source, capsule, directory, remaining, meter, outputs):
            self.execute(source, capsule, directory, remaining, meter, outputs)
            raise SystemExit(23)

        with patch.object(self.profile, 'execute', side_effect=cancel), self.assertRaises(SystemExit) as caught:
            self.qualify()
        self.assertEqual(caught.exception.code, 23)
        certificate = self.artifacts(RESULT_SCHEMA)[0]
        self.assert_gap(certificate, 'SystemExit')
        self.assertEqual(self.broker._read_blob_bytes(hashlib.sha256(LOG).hexdigest()), LOG)
        self.assertEqual(self.inspect(certificate['id'])['attempts'][0]['state'], 'COMPLETED')

    def test_unknown_usage_and_multiple_errors_preserve_full_caps_and_reported_overrun(self):
        reported_bytes = LIMITS['max_storage_bytes'] + 77

        def fail(source, capsule, directory, remaining, meter, outputs):
            outputs.append(('synthetic/error.txt', LOG))
            # Trusted runner seam simulates counted usage; no large file or
            # actual workload is allocated to manufacture an overrun.
            meter['materialized_bytes'] = reported_bytes
            meter['accounting_complete'] = False
            self.revoke(self.runtime['id'])
            raise RuntimeError('Independent original error must survive later failures')

        with patch.object(self.profile, 'execute', side_effect=fail): certificate = self.qualify()
        self.assert_gap(certificate, 'RuntimeError')
        types_seen = {failure['type'] for failure in certificate['body']['failures']}
        self.assertTrue({'RuntimeError', 'ResourceOverrun', 'Denied'} <= types_seen)
        self.assertEqual(certificate['body']['failure'], certificate['body']['failures'][-1])
        usage = certificate['body']['settlement']
        self.assertIs(usage['usage_known'], False)
        self.assertGreaterEqual(usage['compute_ms'], LIMITS['max_compute_ms'])
        self.assertGreater(usage['storage_bytes'], reported_bytes)
        self.assertEqual(self.broker._read_blob_bytes(hashlib.sha256(LOG).hexdigest()), LOG)

    def test_elapsed_overrun_is_retained_without_waiting_for_a_real_deadline(self):
        clock = [0]

        def overrun(*args):
            report = self.execute(*args)
            clock[0] = 301
            return report

        with patch.object(owner, 'time', types.SimpleNamespace(monotonic=lambda: clock[0])), \
                patch.object(self.profile, 'execute', side_effect=overrun):
            certificate = self.qualify()
        self.assert_gap(certificate, 'ResourceOverrun')
        self.assertGreaterEqual(certificate['body']['settlement']['compute_ms'], 301000)

    def test_changed_source_mid_execution_and_later_currentness_do_not_promote_old_proof(self):
        def changed(*args):
            report = self.execute(*args)
            self.source = {**SOURCES, 'trading_researcher/native_backend.py': b'# changed synthetic checker\n'}
            return report

        with patch.object(self.profile, 'execute', side_effect=changed): certificate = self.qualify()
        self.assert_gap(certificate, 'Invalid')
        self.assertEqual(certificate['body']['report']['source_footprint'], footprint(SOURCES))

    def test_inspection_is_read_only_and_source_host_report_or_cache_drift_is_stale(self):
        certificate = self.qualify()
        with patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Inspection materialized cache')):
            self.assertEqual(self.inspect(certificate['id'])['status'], 'CURRENT')
        with patch.object(self.profile, 'capture_source', return_value={**SOURCES,
                          'trading_researcher/native_backend.py': b'# later checker\n'}):
            self.assertEqual(self.inspect(certificate['id'])['status'], 'STALE')
        with patch.object(self.profile, 'host_inputs', return_value=[{'synthetic_new_host_binding': True}]):
            self.assertEqual(self.inspect(certificate['id'])['status'], 'STALE')
        with patch.object(self.profile, 'validate_report', side_effect=Invalid('Synthetic old environment is stale')):
            self.assertEqual(self.inspect(certificate['id'])['status'], 'STALE')
        member = self.cache / 'example/data.bin'; member.write_bytes(b'cache mutation')
        self.assertEqual(self.inspect(certificate['id'])['status'], 'STALE')
        self.assertEqual(self.broker._artifact(certificate['id']), certificate)

    def test_runtime_and_validator_source_revocations_block_completed_and_new_use(self):
        certificate = self.qualify()
        source_id = certificate['body']['source_package_id']
        self.revoke(source_id)
        self.assertEqual(self.inspect(certificate['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
        with self.assertRaises(Denied): self.qualify(key='new-key-same-revoked-source')
        self.assertEqual(len(self.artifacts(INPUT_SCHEMA)), 1)
        self.assertEqual(self.qualify(), certificate)

    def test_input_and_certificate_are_individually_revocable_typed_versions(self):
        for target in ('input_id', 'certificate'):
            with self.subTest(target=target):
                certificate = self.qualify(key=target)
                identity = certificate['id'] if target == 'certificate' else certificate['body'][target]
                self.revoke(identity, key='defect-' + target)
                self.assertEqual(self.inspect(certificate['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
                self.assertEqual(self.broker._artifact(certificate['id']), certificate)

    def test_mid_execution_runtime_revocation_keeps_outputs_and_denies_certification(self):
        def invalidated(*args):
            report = self.execute(*args)
            self.revoke(self.runtime['id'])
            return report

        with patch.object(self.profile, 'execute', side_effect=invalidated): certificate = self.qualify()
        self.assert_gap(certificate, 'Denied')
        self.assertIsNotNone(certificate['body']['report'])
        self.assertEqual(self.broker._read_blob_bytes(hashlib.sha256(LOG).hexdigest()), LOG)

    def test_terminal_event_rollback_leaves_one_started_input_and_restart_fences_retry(self):
        original = self.broker._event

        def fail(actor, action, **details):
            if action == 'native_runtime_qualified': raise RuntimeError('Independent terminal transaction failure')
            return original(actor, action, **details)

        with patch.object(self.broker, '_event', side_effect=fail), self.assertRaises(RuntimeError):
            self.qualify()
        self.assertEqual(self.artifacts(RESULT_SCHEMA), [])
        capsule = self.artifacts(INPUT_SCHEMA)[0]
        self.assertEqual(self.inspect(capsule['id'])['status'], 'RUNNING')
        self.reopen()
        view = self.inspect(capsule['id'])
        self.assertEqual(view['status'], 'INTERRUPTED')
        self.assertEqual(view['settlement'], {'compute_ms': 300000, 'storage_bytes': 268435456, 'usage_known': False})
        self.assertEqual([attempt['state'] for attempt in view['attempts']], ['INTERRUPTED'])
        with patch.object(self.profile, 'execute', side_effect=AssertionError('Interrupted key retried')):
            with self.assertRaises(Conflict): self.qualify()
        self.assertEqual(len(self.artifacts(INPUT_SCHEMA)), 1)

    def test_actual_process_crash_after_started_recovers_unknown_full_reservation(self):
        self.broker.close()
        code = ('import os,sys\nfrom pathlib import Path\n'
                'sys.path.insert(0,str(Path(sys.argv[2])/"tests"))\n'
                'from test_native_qualification_independent import SOURCES\n'
                'from trading_researcher import native_qualification_profile as p\n'
                'from trading_researcher.coordination import Broker\n'
                'p.capture_source=lambda:dict(SOURCES)\np.validate_runtime=lambda runtime:None\n'
                'p.host_inputs=lambda source:[]\np.validate_report=lambda *args:None\n'
                'p.execute=lambda *args:os._exit(31)\n'
                'broker=Broker(sys.argv[1])\n'
                'broker.call(broker.admin_token,"qualify_native_runtime",key="qualification",runtime_id=sys.argv[3])\n')
        process = subprocess.run([sys.executable, '-B', '-c', code, str(self.directory), str(ROOT), self.runtime['id']],
                                 cwd=ROOT, capture_output=True, timeout=30)
        self.assertEqual(process.returncode, 31, process.stderr)
        self.reopen()
        capsule = self.artifacts(INPUT_SCHEMA)[0]
        view = self.inspect(capsule['id'])
        self.assertEqual(view['status'], 'INTERRUPTED')
        self.assertIsNone(view['certificate_id'])
        self.assertEqual(view['settlement'], {'compute_ms': 300000, 'storage_bytes': 268435456, 'usage_known': False})
        self.assertEqual(len(view['attempts']), 1)
        with patch.object(self.profile, 'execute', side_effect=AssertionError('Crashed input reran')):
            with self.assertRaises(Conflict): self.qualify()

    def test_cache_free_backup_restore_preserves_certificate_and_requires_read_only_currency(self):
        certificate = self.qualify()
        backup = self.root / 'backup'
        self.assertEqual(self.op('backup_bundle', destination=str(backup))['status'], 'PASS')
        self.assertFalse(any(path.is_dir() and path.name == self.cache.name for path in backup.rglob('*')))
        restored = self.root / 'restored'
        self.assertEqual(restore_bundle(backup, restored, self.directory / 'operator.key')['status'], 'PASS')
        other = Broker(restored, clock=lambda: 1000)
        try:
            self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=certificate['id']), certificate)
            self.assertEqual(other.call(other.admin_token, 'inspect_native_runtime_qualification',
                                       qualification_id=certificate['id'])['status'], 'STALE')
            meter = {'materialized_bytes': 0}
            NativeRuntimes(other)._materialize(self.runtime['id'], meter)
            self.assertEqual(meter['materialized_bytes'], sum(map(len, MEMBERS.values())))
            self.assertEqual(other.call(other.admin_token, 'inspect_native_runtime_qualification',
                                       qualification_id=certificate['id'])['status'], 'CURRENT')
            self.assertEqual(other.call(other.admin_token, 'verify')['status'], 'PASS')
        finally:
            other.close()

    def test_lost_or_corrupt_retained_output_is_stale_without_repair_or_history_rewrite(self):
        certificate = self.qualify()
        path = self.broker._blob_path(hashlib.sha256(LOG).hexdigest())
        for kind in ('corrupt', 'missing'):
            with self.subTest(kind=kind):
                if kind == 'corrupt': path.write_bytes(b'corrupt retained transcript')
                else: path.unlink()
                with patch.object(self.profile, 'execute', side_effect=AssertionError('Inspection dispatched work')), \
                        patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Inspection repaired cache')):
                    self.assertEqual(self.inspect(certificate['id'])['status'], 'STALE')
                    self.assertEqual(self.qualify(), certificate)
                self.assertEqual(self.broker._artifact(certificate['id']), certificate)
                if kind == 'missing': self.assertFalse(path.exists())
                else: self.assertEqual(path.read_bytes(), b'corrupt retained transcript')
                path.write_bytes(LOG)

    def test_source_blob_changed_during_execution_retains_gap_and_computed_evidence(self):
        def corrupt(*args):
            report = self.execute(*args)
            capsule = args[1]
            package = self.broker._artifact(capsule['body']['source_package_id'])
            identity = package['body']['files']['trading_researcher/native_backend.py']['sha256']
            self.broker._blob_path(identity).write_bytes(b'corrupt retained source during execution')
            return report

        with patch.object(self.profile, 'execute', side_effect=corrupt): certificate = self.qualify()
        self.assert_gap(certificate, 'Conflict')
        self.assertIsNotNone(certificate['body']['report'])
        self.assertEqual(self.broker._read_blob_bytes(hashlib.sha256(LOG).hexdigest()), LOG)
        self.assertIs(certificate['body']['settlement']['usage_known'], True)

    def test_runtime_archive_changed_during_execution_retains_gap_and_computed_evidence(self):
        def corrupt(*args):
            report = self.execute(*args)
            self.broker._blob_path(self.runtime['blob_refs'][0]).write_bytes(b'corrupt retained archive during execution')
            return report

        with patch.object(self.profile, 'execute', side_effect=corrupt): certificate = self.qualify()
        self.assert_gap(certificate, 'Conflict')
        self.assertIsNotNone(certificate['body']['report'])
        self.assertEqual(self.broker._read_blob_bytes(hashlib.sha256(LOG).hexdigest()), LOG)
        self.assertIs(certificate['body']['settlement']['usage_known'], True)


class NativeQualificationProfileMetadataIndependentTests(unittest.TestCase):
    """Real pinned-profile validators; only environment currentness is mocked.

The current v2 metadata fixture binds the separately retained packing runtime
and 21 independent loop methods. Numerical result/stream literals and the
15,143,319-byte stream remain the original gold; nothing is regenerated here.
The exact preceding 30-method v1 test source is archived bytewise in the new
fixture. Active historical v1 checks remain in the provenance/version suites.
Invented capsule/source metadata issue no runtime or scientific certificate.
"""
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / 'explicit-current-cache'
        self.profile = owner.profile
        self.source = dict(SOURCES)
        fixture = ROOT / 'tests/fixtures/native-environment-checks-2026-11-02.zip'
        self.assertEqual(hashlib.sha256(fixture.read_bytes()).hexdigest(),
                         'fda1c157fbf365f5a8826a9ba0e9f7d19fae5f36f7299bf7a770a9764524fd30')
        prefix = '.trf-runtime/native-runtime-2026-11-02/'
        with ZipFile(fixture) as archive:
            observed = json.loads(archive.read(prefix + 'environment-reference-observation.json'))
        current_fixture = ROOT / 'tests/fixtures/native-packing-runtime-binding-2026-11-02.zip'
        self.assertEqual(hashlib.sha256(current_fixture.read_bytes()).hexdigest(),
                         '2c245ff010379a53d946fa6aed8e5b5b3a8a6a4870bff4feed09ecb079bf7398')
        with ZipFile(current_fixture) as archive:
            manifest = json.loads(archive.read('runtime-v2-manifest.json'))
            preparation = json.loads(archive.read('runtime-v2-preparation.json'))
            build = json.loads(archive.read('runtime-v2-build.json'))
            historical_tests = archive.read('qualification-tests-before-v2-fixture.py')
        self.assertEqual(hashlib.sha256(historical_tests).hexdigest(),
                         '681a2d682cf4bf5efef868feff0bc60b9072737ab5461859e4f91ef5b5ed9bec')
        self.assertEqual(digest(manifest), '20151908bc9fd2b09ac407caebc5d7bbc2f79016315b8b59d736d2427297c848')
        self.assertEqual(preparation['manifest_sha256'], digest(manifest))
        self.assertEqual(preparation['archive_sha256'],
                         '4d379ab0dc5d689445c1f720b967b923b8106af4184de1576418837c23853976')
        self.assertEqual(preparation['archive_bytes'], 26258151)
        kernel = manifest['files']['_trf_stationary_native.cp314-win_amd64.pyd']
        self.assertEqual(kernel, {'sha256': '318b5a84c357902af965c154bd0652c837503e5783a156f506c13872e1639a36',
                                  'size': 369152})
        self.assertEqual(preparation['new_kernel_sha256'], kernel['sha256'])
        self.assertEqual(build['binary']['sha256'], kernel['sha256'])
        self.assertEqual(build['binary']['size'], kernel['size'])
        self.assertEqual(build['source_sha256'],
                         'b4fb9106bb2b2e7715a5b7e34a2d468d4f950cc5e60dc1571531397ea3a8f5b6')
        self.capsule = {'id': 'b' * 64, 'body': {
            'runtime_id': 'a' * 64, 'runtime_manifest': manifest,
            'source_footprint': footprint(self.source), 'host_images': observed['host_images'],
            'limits': dict(LIMITS), 'initial_storage_bytes': META}}
        self.runtime = {'body': {'manifest': deepcopy(manifest),
            'archive': {'sha256': '4d379ab0dc5d689445c1f720b967b923b8106af4184de1576418837c23853976',
                        'size': preparation['archive_bytes']}}}
        self.gold = {'schema': 'native-runtime-conformance-result/1',
            'profile': 'stationary-native-runtime/2', 'tests': 21, 'failures': 0,
            'errors': 0, 'skipped': 0, 'draws': 59997, 'native_lengths': [4, 8, 16],
            'complete_result_sha256': '720ac237f2ad3e29a5a9d94191af68a90a549f476c6e0f2d5bae36b537901b09',
            'complete_stream_sha256': '76c3fb49b827455afaf488104f0ee88788254446e4bcf1fad07f73b42cb4f533',
            'scientific_readiness': False}
        proofs = []
        for phase in ('generate', 'replay'):
            request = {'profile': 'stationary-native-runtime/2', 'input_id': self.capsule['id'],
                'runtime_id': self.capsule['body']['runtime_id'], 'runtime_manifest': deepcopy(manifest),
                'host_images': deepcopy(observed['host_images']), 'runtime_directory': str(self.directory),
                'phase': phase, 'stream_limit': 32 * META, 'source_footprint': footprint(self.source)}
            proofs.append({'request': request, 'request_hash': digest(request), 'result': deepcopy(self.gold),
                'environment_before': {'explicit_environment_currentness_test_seam': 'before'},
                'environment_after': {'explicit_environment_currentness_test_seam': 'after'},
                'stream_blob': {'sha256': self.gold['complete_stream_sha256'], 'size': 15143319}})
        self.report = {'profile': 'stationary-native-runtime/2', 'input_id': self.capsule['id'],
                       'source_footprint': footprint(self.source), 'proofs': proofs}

    def validate(self, report=None, capsule=None, is_current=True):
        with patch.object(self.profile, 'current', return_value=is_current) as current:
            value = self.profile.validate_report(self.report if report is None else report,
                self.source, self.capsule if capsule is None else capsule, self.directory)
        return value, current

    def reject(self, report, capsule=None):
        with self.assertRaises((Invalid, Conflict)):
            self.validate(report, capsule)

    def test_complete_metadata_delegates_four_phase_checks_to_trusted_environment_inputs(self):
        result, current = self.validate()
        self.assertIsNone(result)
        self.assertEqual(current.call_count, 4)
        expected = []
        for proof in self.report['proofs']:
            for field in ('environment_before', 'environment_after'):
                expected.append((proof[field], self.capsule['body']['runtime_id'],
                    self.capsule['body']['runtime_manifest'], self.directory, self.capsule['body']['host_images']))
        self.assertEqual([call.args for call in current.call_args_list], expected)

    def test_missing_duplicate_reordered_and_wrong_phase_proofs_cannot_replace_separate_replay(self):
        for proofs in ([], self.report['proofs'][:1], self.report['proofs'] * 2,
                       [self.report['proofs'][0]] * 2, list(reversed(self.report['proofs']))):
            with self.subTest(proof_count=len(proofs)):
                changed = deepcopy(self.report); changed['proofs'] = deepcopy(proofs); self.reject(changed)
        for phase in ('generate', 'replay', 'unknown'):
            changed = deepcopy(self.report)
            changed['proofs'][1]['request']['phase'] = phase
            changed['proofs'][1]['request_hash'] = digest(changed['proofs'][1]['request'])
            if phase != 'replay': self.reject(changed)

    def test_full_gold_counts_results_stream_hashes_and_native_selection_are_exact(self):
        changes = {'tests': 12, 'failures': 1, 'errors': 1, 'skipped': 1,
                   'draws': 59996, 'native_lengths': [4, 8], 'scientific_readiness': True,
                   'complete_result_sha256': '0' * 64, 'complete_stream_sha256': '0' * 64}
        for field, value in changes.items():
            for phase in (0, 1):
                with self.subTest(field=field, phase=phase):
                    changed = deepcopy(self.report); changed['proofs'][phase]['result'][field] = value
                    self.reject(changed)
        for field in ('tests', 'failures', 'errors', 'skipped', 'draws'):
            changed = deepcopy(self.report); changed['proofs'][0]['result'][field] = False
            self.reject(changed)

    def test_legacy_thirteen_case_count_cannot_be_relabelled_as_current_packing_proof(self):
        for phases in ((0,), (1,), (0, 1)):
            with self.subTest(phases=phases):
                changed = deepcopy(self.report)
                for phase in phases:
                    changed['proofs'][phase]['result']['tests'] = 13
                self.reject(changed)

    def test_report_request_and_capsule_source_runtime_host_identity_are_bound(self):
        for field, value in (('profile', 'other/1'), ('input_id', 'c' * 64),
                              ('source_footprint', {'wrong.py': '0' * 64})):
            changed = deepcopy(self.report); changed[field] = value; self.reject(changed)
        for field, value in (('profile', 'other/1'), ('input_id', 'c' * 64),
                           ('runtime_id', 'c' * 64), ('runtime_manifest', {}),
                           ('host_images', []), ('source_footprint', {'wrong.py': '0' * 64})):
            changed = deepcopy(self.report)
            changed['proofs'][0]['request'][field] = value
            changed['proofs'][0]['request_hash'] = digest(changed['proofs'][0]['request'])
            self.reject(changed)
        changed = deepcopy(self.report); changed['proofs'][0]['request_hash'] = '0' * 64; self.reject(changed)
        capsule = deepcopy(self.capsule)
        capsule['body']['source_footprint'] = {'other-source.py': '0' * 64}
        self.reject(self.report, capsule)

    def test_original_request_directory_requires_an_absolute_string_without_retargeting_history(self):
        for value in (None, True, 7, [], {}, 'relative-cache', './relative-cache'):
            with self.subTest(directory=value):
                changed = deepcopy(self.report)
                changed['proofs'][0]['request']['runtime_directory'] = value
                changed['proofs'][0]['request_hash'] = digest(changed['proofs'][0]['request'])
                self.reject(changed)
        # An independently selected restored cache can have another current
        # location; the retained proof keeps its original absolute path.
        restored = self.directory.parent / 'new-current-cache'
        with patch.object(self.profile, 'current', return_value=True):
            self.assertIsNone(self.profile.validate_report(self.report, self.source, self.capsule, restored))

    def test_stream_bounds_types_equal_phase_bytes_and_extra_fields_are_rejected(self):
        for field, values in (('size', (0, -1, True, '15143319', 32 * META + 1)),
                              ('sha256', ('0' * 64, True))):
            for value in values:
                changed = deepcopy(self.report); changed['proofs'][0]['stream_blob'][field] = value
                self.reject(changed)
        for value in (0, True, '33554432', 64 * META + 1):
            changed = deepcopy(self.report)
            changed['proofs'][0]['request']['stream_limit'] = value
            changed['proofs'][0]['request_hash'] = digest(changed['proofs'][0]['request'])
            self.reject(changed)
        changed = deepcopy(self.report); changed['proofs'][1]['stream_blob']['size'] -= 1; self.reject(changed)
        changed = deepcopy(self.report)
        for proof in changed['proofs']: proof['stream_blob']['size'] = 15143318
        self.reject(changed)
        for target in ('report', 'proof', 'request', 'result', 'stream_blob'):
            changed = deepcopy(self.report)
            node = (changed if target == 'report' else changed['proofs'][0] if target == 'proof'
                    else changed['proofs'][0][target])
            node['extra'] = True
            if target == 'request': changed['proofs'][0]['request_hash'] = digest(node)
            self.reject(changed)

    def test_compatibility_and_complete_gold_do_not_waive_environment_currentness(self):
        with self.assertRaises((Invalid, Conflict)):
            self.validate(is_current=False)

    def test_real_runtime_membership_uses_committed_manifest_archive_and_kernel_pins(self):
        self.assertIsNone(self.profile.validate_runtime(self.runtime))
        for target in ('manifest', 'archive', 'kernel'):
            with self.subTest(target=target):
                changed = deepcopy(self.runtime)
                if target == 'manifest': changed['body']['manifest']['dependencies']['numpy']['version'] = 'other'
                elif target == 'archive': changed['body']['archive']['sha256'] = '0' * 64
                else: changed['body']['manifest']['files']['_trf_stationary_native.cp314-win_amd64.pyd']['sha256'] = '0' * 64
                with self.assertRaises((Invalid, Conflict)): self.profile.validate_runtime(changed)
        compatibility_only = {'body': {'manifest': {'implementation_info': {
            'abi': 'stationary-native-int64/1', 'numpy': '2.3.4', 'max_time_rows': 100000,
            'max_mean_length': 100000, 'bitgen_struct_bytes': 40}},
            'archive': {'sha256': self.runtime['body']['archive']['sha256']}}}
        with self.assertRaises((Invalid, Conflict)):
            self.profile.validate_runtime(compatibility_only)


if __name__ == '__main__':
    unittest.main()
