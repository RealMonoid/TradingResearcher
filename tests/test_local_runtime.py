"""Real loopback transport, process recovery and bounded worker checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from trading_researcher.coordination import Broker
from trading_researcher.server import LocalServer, Client, RemoteError
from trading_researcher.worker import run_once


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.broker = Broker(self.tmp.name)
        self.server = LocalServer(self.broker, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = self.server.url
        self.admin = Client(self.url, self.broker.admin_token)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)
        self.broker.close()
        self.tmp.cleanup()

    def setup_sum(self):
        token = self.admin.call('register_worker', name='calculator', role='executor',
                                capabilities=['decimal-sum/v1'])['token']
        source = self.admin.call('add_source', body={'values': ['0.1', '0.2']},
                                 data_class='development')['id']
        context = self.admin.call('create_context', role='executor', epoch=1, artifact_ids=[source])['id']
        spec = dict(kind='decimal-sum/v1', context_id=context, purpose='Synthetic arithmetic check',
                    allowed_workers=['calculator'], max_attempts=2, lease_seconds=3,
                    deadline=int(time.time()) + 60, dependencies=[])
        return Client(self.url, token), spec

    def test_real_worker_and_background_time_trigger(self):
        worker, spec = self.setup_sum()
        self.admin.call('add_schedule', key='now', spec=spec, at=int(time.time()), max_fires=1)
        deadline = time.monotonic() + 5
        result = None
        while time.monotonic() < deadline and result is None:
            result = run_once(worker)
            if result is None:
                time.sleep(0.05)
        self.assertTrue(result['accepted'])
        self.assertFalse(result['scientific_authority'])
        jobs = self.admin.call('status')['jobs']
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['state'], 'completed')

    def test_http_rejects_foreign_identity_origin_and_unknown_fields(self):
        worker, spec = self.setup_sum()
        self.admin.call('enqueue', key='job', spec=spec)
        with self.assertRaises(RemoteError) as error:
            worker.call('status')
        self.assertEqual(error.exception.status, 403)
        with self.assertRaises(RemoteError):
            Client(self.url, 'forged').call('claim')
        with self.assertRaises(RemoteError):
            worker.call('claim', actor='operator')
        request = Request(self.url + '/rpc', data=b'{"op":"claim","args":{}}',
                          headers={'Authorization': 'Bearer ' + worker.token,
                                   'Content-Type': 'application/json', 'Origin': 'https://example.invalid'})
        with self.assertRaises(HTTPError) as error:
            urlopen(request, timeout=2)
        self.assertEqual(error.exception.code, 403)
        error.exception.close()

    def test_worker_handler_failure_becomes_visible_block(self):
        worker, spec = self.setup_sum()
        job = self.admin.call('enqueue', key='job', spec=spec)
        def broken(_):
            raise ValueError('Synthetic handler failure')
        outcome = run_once(worker, handlers={'decimal-sum/v1': broken})
        self.assertEqual(outcome['state'], 'blocked')
        self.assertEqual(self.admin.call('inspect', job_id=job['id'])['attempts'][0]['state'], 'blocked')

    def test_cli_demo_and_restart_verify(self):
        directory = Path(self.tmp.name) / 'demo'
        result = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'demo', '--directory', str(directory)],
                                text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report['completion']['accepted'])
        result = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'verify', '--directory', str(directory)],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['status'], 'PASS')

    def test_cli_research_demo_two_isolated_fixture_perspectives(self):
        directory = Path(self.tmp.name) / 'research-demo'
        result = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'research-demo',
                                 '--directory', str(directory)], text=True, capture_output=True, timeout=25)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['perspectives_completed'], 2)
        self.assertFalse(report['genuine_discovery'])
        self.assertTrue(report['same_base_context'])
        self.assertTrue(report['private_transcripts'])
        self.assertEqual(report['integrity']['status'], 'PASS')
        self.assertEqual(report['usage']['calls'], 3)

    def test_research_memory_through_real_authenticated_rpc(self):
        token = self.admin.call('register_worker', name='researcher', role='discovery',
                                capabilities=['research-record/v1'])['token']
        source = self.admin.call('add_research', kind='source',
                                 content={'text': 'Observed fixture', 'uri': 'fixture:rpc'},
                                 scope={}, source_refs=[])['id']
        context = self.admin.call('create_context', role='discovery', epoch=1,
                                  artifact_ids=[source])['id']
        self.admin.call('enqueue', key='research', spec={
            'kind': 'research-record/v1', 'context_id': context, 'purpose': 'RPC memory fixture',
            'allowed_workers': ['researcher'], 'max_attempts': 1, 'lease_seconds': 10,
            'deadline': int(time.time()) + 60, 'dependencies': []})
        worker = Client(self.url, token)
        lease = worker.call('claim')['lease']
        self.assertEqual(worker.call('search_memory', lease=lease)['total'], 1)
        idea = worker.call('record_research', lease=lease, kind='idea',
                           content={'text': 'A free but untested idea'}, scope={}, source_refs=[source])
        result = worker.call('submit', lease=lease, artifact_id=idea['id'])
        self.assertTrue(result['accepted'])
        self.assertFalse(result['scientific_authority'])
        with self.assertRaises(RemoteError):
            worker.call('inspect_memory')
        self.assertEqual(self.admin.call('verify')['research_memory']['records'], 3)

    def test_memory_demo_cli_releases_complete_history_and_stops(self):
        directory = Path(self.tmp.name) / 'memory-demo'
        result = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher', 'memory-demo',
                                 '--directory', str(directory)], text=True, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report['memory_records'], 5)
        self.assertEqual(report['correction_preserved'], True)
        self.assertEqual(report['market_findings'], 0)
        self.assertEqual(report['completion']['accepted'], True)
        self.assertEqual(report['completion']['scientific_authority'], False)
        self.assertEqual(report['restored_projection_matches'], True)
        reopened = Broker(directory)
        reopened.close()

    def test_process_crash_rolls_back_uncommitted_write_and_preserves_committed_write(self):
        directory = Path(self.tmp.name) / 'crash'
        script = '''
import os, sys
from trading_researcher.coordination import Broker
b = Broker(sys.argv[1])
source = b.call(b.admin_token, 'add_source', body={'committed': True}, data_class='development')
print(source['id'], flush=True)
with b._transaction():
    b._add_source({'name': 'operator'}, body={'uncommitted': True}, data_class='development')
    os._exit(73)
'''
        result = subprocess.run([sys.executable, '-B', '-c', script, str(directory)],
                                text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 73, result.stderr)
        recovered = Broker(directory)
        try:
            self.assertEqual(recovered.call(recovered.admin_token, 'verify')['status'], 'PASS')
            self.assertEqual(recovered._db.execute('SELECT count(*) FROM artifacts').fetchone()[0], 1)
            artifact = recovered.call(recovered.admin_token, 'get_artifact', artifact_id=result.stdout.strip())
            self.assertEqual(artifact['body'], {'committed': True})
        finally:
            recovered.close()


if __name__ == '__main__':
    unittest.main()
