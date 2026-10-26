"""Independent failed-plan retention/recovery probes using owned synthetic inputs."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

from trading_researcher import evaluation_plans
from trading_researcher.codec import canonical, decode, digest
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.storage import restore_bundle
import test_evaluation_plans as plan_support


ROOT = Path(__file__).resolve().parents[1]


class PlanRetentionAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan_support.EvaluationPlanTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.close()

    arguments = plan_support.EvaluationPlanTests.arguments

    def records(self, schema, broker=None):
        broker = broker or self.broker
        output = []
        for row in broker._db.execute('SELECT id,envelope FROM artifacts'):
            envelope = decode(row['envelope'])
            if isinstance(envelope.get('body'), dict) and envelope['body'].get('schema') == schema:
                output.append({'id': row['id'], **envelope})
        return output

    def capsule_for(self, key, broker=None):
        found = [record for record in self.records('evaluation-plan-input/1', broker)
                 if record['body']['request']['key'] == key]
        self.assertEqual(len(found), 1, 'One immutable admitted capsule per request key')
        return found[0]

    def interrupt(self, key):
        args = self.arguments(key)
        with patch.object(evaluation_plans, '_run_child', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.broker.call(self.token, 'prepare_evaluation_plan', **args)
        return args, self.capsule_for(key)

    def assert_capsule_bytes(self, capsule, broker=None):
        broker = broker or self.broker
        body = capsule['body']
        self.assertEqual(body['request_hash'], digest(body['request']))
        self.assertEqual(body['payload_hash'], digest(body['payload']))
        self.assertEqual(set(body['source_files']), set(body['source_footprint']))
        self.assertEqual(set(capsule['blob_refs']), {d['sha256'] for d in body['source_files'].values()})
        for name, descriptor in body['source_files'].items():
            raw = broker._read_blob_bytes(descriptor['sha256'])
            self.assertEqual(len(raw), descriptor['size'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), body['source_footprint'][name])
        self.assertFalse(body['scientific_readiness'])
        self.assertFalse(body['allocation_reserved'])
        self.assertFalse(body['frozen'])

    def test_admission_transaction_rollback_launches_nothing(self):
        key = 'retention-independent-prelaunch-rollback'
        before_capsules = len(self.records('evaluation-plan-input/1'))
        before_attempts = self.broker.call(self.token, 'inspect_bound_computations')['total']
        original = self.broker._event

        def interrupt_start(actor, action, **details):
            if action == 'bound_computation_started' and details.get('kind') == 'evaluation_plan':
                raise RuntimeError('Injected failure before admission commit')
            return original(actor, action, **details)

        with patch.object(self.broker, '_event', side_effect=interrupt_start), \
             patch.object(evaluation_plans, '_run_child', side_effect=AssertionError('Uncommitted child launched')):
            with self.assertRaises(RuntimeError):
                self.broker.call(self.token, 'prepare_evaluation_plan', **self.arguments(key))
        self.assertEqual(len(self.records('evaluation-plan-input/1')), before_capsules)
        self.assertEqual(self.broker.call(self.token, 'inspect_bound_computations')['total'], before_attempts)

    def test_real_writer_crash_retains_exact_inputs_and_restart_reason(self):
        key = 'retention-independent-process-crash'
        args = self.arguments(key)
        directory = self.broker.directory
        argument_file = self.fixture.root / 'independent-crash-request.json'
        argument_file.write_text(canonical(args), encoding='utf-8')
        script = (
            'import os,sys\n'
            'from pathlib import Path\n'
            'from trading_researcher.coordination import Broker\n'
            'from trading_researcher.codec import decode\n'
            'from trading_researcher import evaluation_plans\n'
            'broker=Broker(sys.argv[1])\n'
            'evaluation_plans._run_child=lambda *args,**kwargs: os._exit(37)\n'
            'broker.call(broker.admin_token,"prepare_evaluation_plan",**decode(Path(sys.argv[2]).read_bytes()))\n'
        )
        self.broker.close()
        try:
            process = subprocess.run([sys.executable, '-B', '-c', script, str(directory), str(argument_file)],
                                     cwd=ROOT, capture_output=True, timeout=90)
            self.assertEqual(process.returncode, 37, process.stderr.decode(errors='replace'))
        finally:
            reopened = Broker(directory)
            type(self).broker = self.fixture.broker = self.fixture.normalizer.broker = reopened
        capsule = self.capsule_for(key)
        self.assertEqual(capsule['body']['request'], args)
        self.assertEqual(capsule['body']['payload']['dependence'], args['dependence'])
        self.assert_capsule_bytes(capsule)
        attempts = self.broker.call(self.token, 'inspect_bound_computations')
        recovered = [item for item in attempts['attempts'] if item.get('retained_input_id') == capsule['id']]
        self.assertEqual(len(recovered), 1)
        self.assertEqual(recovered[0]['state'], 'INTERRUPTED')
        self.assertEqual(recovered[0]['reason'], 'previous_writer_ended')
        self.assertEqual(attempts['pending'], 0)
        self.assertFalse(any(item['body']['request']['key'] == key for item in self.records('evaluation-plan/1')))

    def test_missing_or_corrupt_retained_source_never_uses_checkout_fallback(self):
        args, capsule = self.interrupt('retention-independent-corrupt-source')
        descriptor = capsule['body']['source_files']['trading_researcher/evaluation_policy.py']
        path = self.broker._blob_path(descriptor['sha256'])
        original = path.read_bytes()
        for missing in (False, True):
            with self.subTest(missing=missing):
                try:
                    if missing:
                        path.unlink()
                    else:
                        path.write_bytes(b'corrupt retained policy source\n')
                    with patch.object(evaluation_plans, 'source_bundle', side_effect=AssertionError('Checkout fallback')), \
                         patch.object(evaluation_plans, '_run_child', side_effect=AssertionError('Corrupt source executed')):
                        with self.assertRaises((Conflict, Invalid, Denied, OSError)):
                            self.broker.call(self.token, 'prepare_evaluation_plan', **args)
                finally:
                    path.write_bytes(original)

    def test_interrupted_capsule_backup_restore_and_retry_use_retained_bytes(self):
        args, capsule = self.interrupt('retention-independent-backup')
        backup = self.fixture.root / 'independent-plan-retention-backup'
        restored = self.fixture.root / 'independent-plan-retention-restored'
        self.assertEqual(self.broker.call(self.token, 'backup_bundle', destination=str(backup))['status'], 'PASS')
        self.assertEqual(restore_bundle(backup, restored, self.broker.directory / 'operator.key')['status'], 'PASS')
        other = Broker(restored)
        try:
            self.assertEqual(self.capsule_for(args['key'], other), capsule)
            self.assert_capsule_bytes(capsule, other)
            with patch.object(evaluation_plans, 'source_bundle', side_effect=AssertionError('Replay consulted checkout')):
                result = other.call(other.admin_token, 'prepare_evaluation_plan', **args)
            self.assertEqual(result['body']['input_capsule_id'], capsule['id'])
            self.assertIn(capsule['id'], result['source_refs'])
            self.assertIn(capsule['id'], result['exposure'])
            self.assertFalse(result['body']['scientific_readiness'])
            self.assertEqual(other.call(other.admin_token, 'inspect_bound_computations')['pending'], 0)
        finally:
            other.close()

    def test_incomplete_backup_cannot_omit_committed_capsule_source(self):
        _, capsule = self.interrupt('retention-independent-backup-corruption')
        descriptor = capsule['body']['source_files']['trading_researcher/evaluation_policy.py']
        path = self.broker._blob_path(descriptor['sha256'])
        original = path.read_bytes()
        destination = self.fixture.root / 'independent-refused-retention-backup'
        try:
            path.unlink()
            with self.assertRaises((Conflict, Invalid, OSError)):
                self.broker.call(self.token, 'backup_bundle', destination=str(destination))
            self.assertFalse(destination.exists())
        finally:
            path.write_bytes(original)

    def test_request_namespace_worker_and_earlier_context_boundaries(self):
        with self.assertRaises(Invalid):
            self.broker.call(self.token, 'add_source', data_class='development',
                             body={'schema': 'evaluation-plan-input/1', 'scientific_readiness': False})
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Worker read retained inputs')):
            with self.assertRaises(Denied):
                self.broker.call(self.fixture.worker, 'prepare_evaluation_plan',
                                 **self.arguments('retention-independent-worker'))
        future = int(time.time()) + 100
        with patch.object(self.broker, 'clock', return_value=future):
            _, capsule = self.interrupt('retention-independent-availability')
            wrapper = self.broker.call(self.token, 'add_source', data_class='development',
                                       body={'text': 'Derived capsule metadata'}, exposure=[capsule['id']])
            with self.assertRaises(Denied):
                self.broker.call(self.token, 'create_context', role='formalizer', epoch=100,
                                 research_time=future - 1, artifact_ids=[wrapper['id']])
        self.assertIn(self.compiled['id'], capsule['source_refs'])
        self.assertIn(self.execution['id'], capsule['source_refs'])
        self.assertTrue(set(self.compiled['exposure']) <= set(capsule['exposure']))
        self.assertTrue(set(self.execution['exposure']) <= set(capsule['exposure']))

    def test_conflicting_retry_cannot_replace_admitted_request(self):
        args, capsule = self.interrupt('retention-independent-conflicting-retry')
        changed = deepcopy(args)
        changed['dependence']['randomness']['seed'] += 1
        with patch.object(evaluation_plans, '_run_child', side_effect=AssertionError('Conflicting request launched')):
            with self.assertRaises(Conflict):
                self.broker.call(self.token, 'prepare_evaluation_plan', **changed)
        self.assertEqual(self.capsule_for(args['key']), capsule)

    def test_concurrent_identical_retries_share_capsule_and_final_identity(self):
        args = self.arguments('retention-independent-concurrent')
        barrier = threading.Barrier(2, timeout=30)
        original = evaluation_plans._run_child

        def synchronize_calculations(command, directory):
            request = decode((Path(directory) / 'request.json').read_bytes())
            if request['verify_hash'] is None:
                barrier.wait()
            return original(command, directory)

        with patch.object(evaluation_plans, '_run_child', side_effect=synchronize_calculations):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(self.broker.call, self.token, 'prepare_evaluation_plan', **deepcopy(args))
                           for _ in range(2)]
                results = [future.result(timeout=90) for future in futures]
        self.assertEqual(results[0]['id'], results[1]['id'])
        capsule = self.capsule_for(args['key'])
        self.assertEqual(results[0]['body']['input_capsule_id'], capsule['id'])
        attempts = self.broker.call(self.token, 'inspect_bound_computations')
        related = [item for item in attempts['attempts'] if item.get('retained_input_id') == capsule['id']]
        self.assertEqual(len(related), 2)
        self.assertTrue(all(item['state'] == 'COMPLETED' for item in related))
        self.assertEqual(attempts['pending'], 0)


if __name__ == '__main__':
    unittest.main()
