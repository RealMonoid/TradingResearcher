"""Acceptance tests for the public broker seam, with real temporary SQLite files."""
import tempfile
import unittest
import sqlite3
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from trading_researcher.coordination import Broker, Denied, Conflict, Invalid


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = 1000
        self.broker = Broker(Path(self.tmp.name), clock=lambda: self.now)
        self.admin = self.broker.admin_token
        self.alice = self.admin_call('register_worker', name='alice', role='discovery',
                                     capabilities=['draft/v1'])['token']
        self.bob = self.admin_call('register_worker', name='bob', role='discovery',
                                   capabilities=['draft/v1'])['token']
        self.source = self.admin_call('add_source', body={'observation': 'synthetic fixture'},
                                      data_class='development', exposure=['fixture:exposed'])['id']
        self.context = self.admin_call('create_context', role='discovery', epoch=1,
                                       artifact_ids=[self.source])['id']

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def admin_call(self, op, **args):
        return self.broker.call(self.admin, op, **args)

    def call(self, token, op, **args):
        return self.broker.call(token, op, **args)

    def job(self, key='job', **overrides):
        spec = dict(kind='draft/v1', context_id=self.context, purpose='Investigate the fixture',
                    allowed_workers=['alice', 'bob'], max_attempts=2, lease_seconds=10,
                    deadline=1100, dependencies=[])
        spec.update(overrides)
        return self.admin_call('enqueue', key=key, spec=spec)

    def claim(self, token=None):
        return self.call(token or self.alice, 'claim')

    def put(self, lease, token=None, body=None):
        return self.call(token or self.alice, 'put_artifact', lease=lease['lease'],
                         body=body or {'finding': 'An untested idea', 'interpretation': 'Hypothesis only',
                                      'uncertainty': 'Not empirically tested', 'next_action': 'Formalize'},
                         source_refs=[self.source])

    def test_stale_attempt_cannot_publish_after_same_identity_reclaims(self):
        self.job()
        old = self.claim()
        self.now += 11
        new = self.claim()
        self.assertGreater(new['lease']['generation'], old['lease']['generation'])
        with self.assertRaises(Denied):
            self.put(old)
        with self.assertRaises(Denied):
            self.call(self.alice, 'heartbeat', lease=old['lease'])
        with self.assertRaises(Denied):
            self.call(self.alice, 'block', lease=old['lease'], reason='late', needs=['data'], retry_when='later')
        result = self.put(new)
        accepted = self.call(self.alice, 'submit', lease=new['lease'], artifact_id=result['id'])
        self.assertEqual(accepted['state'], 'completed')

    def test_done_claim_fails_declared_completion_check_and_is_retained(self):
        job = self.job()
        lease = self.claim()
        result = self.put(lease, body={'done': True})
        outcome = self.call(self.alice, 'submit', lease=lease['lease'], artifact_id=result['id'])
        self.assertEqual(outcome['state'], 'blocked')
        self.assertFalse(outcome['accepted'])
        self.assertEqual(self.admin_call('inspect', job_id=job['id'])['attempts'][0]['result_id'], result['id'])

    def test_identity_metadata_and_frozen_context_are_protected(self):
        self.job(allowed_workers=['alice'])
        lease = self.claim()
        secret = self.admin_call('add_source', body={'secret': 'assessment'}, data_class='assessment')['id']
        later = self.admin_call('add_source', body={'later': True}, data_class='development')['id']
        for ref in [secret, later]:
            with self.assertRaises(Denied):
                self.call(self.alice, 'read_artifact', lease=lease['lease'], artifact_id=ref)
        with self.assertRaises(Denied):
            self.call(self.bob, 'read_artifact', lease=lease['lease'], artifact_id=self.source)
        with self.assertRaises(Denied):
            self.call(self.bob, 'status')
        with self.assertRaises(Invalid):
            self.call(self.alice, 'put_artifact', lease=lease['lease'], body={}, source_refs=[], creator='bob')
        with self.assertRaises(Denied):
            self.admin_call('create_context', role='discovery', epoch=2, artifact_ids=[secret])

    def test_claim_is_exclusive_and_completion_delivery_is_idempotent(self):
        self.job()
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(self.claim, [self.alice, self.bob]))
        self.assertEqual(sum(c is not None for c in claims), 1)
        token, lease = next((t, c) for t, c in zip([self.alice, self.bob], claims) if c)
        result = self.put(lease, token=token)
        first = self.call(token, 'submit', lease=lease['lease'], artifact_id=result['id'])
        self.assertEqual(first, self.call(token, 'submit', lease=lease['lease'], artifact_id=result['id']))
        self.assertEqual(len(self.admin_call('inspect', job_id=lease['lease']['job_id'])['attempts']), 1)

    def test_block_is_not_completion_and_retry_retains_attempt(self):
        job = self.job()
        lease = self.claim()
        self.call(self.alice, 'block', lease=lease['lease'], reason='Missing capability',
                  needs=['approved primitive'], retry_when='Primitive is certified')
        self.assertIsNone(self.claim(self.bob))
        self.admin_call('resume', job_id=job['id'], reason='Required primitive now available')
        second = self.claim(self.bob)
        self.assertEqual(second['lease']['generation'], 2)
        history = self.admin_call('inspect', job_id=job['id'])
        self.assertEqual(history['attempts'][0]['state'], 'blocked')
        self.assertEqual(history['attempts'][0]['detail']['needs'], ['approved primitive'])

    def test_release_is_atomic_after_batch_and_only_visible_in_later_context(self):
        batch = self.admin_call('create_batch', key='epoch', epoch=1)['id']
        one = self.job('one', batch_id=batch)
        self.job('two', batch_id=batch)
        self.assertIsNone(self.claim())
        self.admin_call('seal_batch', batch_id=batch)
        lease = self.claim()
        result = self.put(lease)
        self.call(self.alice, 'submit', lease=lease['lease'], artifact_id=result['id'])
        with self.assertRaises(Conflict):
            self.admin_call('release_batch', batch_id=batch, target_epoch=2)
        with self.assertRaises(Denied):
            self.admin_call('create_context', role='discovery', epoch=2, artifact_ids=[result['id']])
        lease2 = self.claim(self.bob)
        with self.assertRaises(Denied):
            self.call(self.bob, 'read_artifact', lease=lease2['lease'], artifact_id=result['id'])
        result2 = self.put(lease2, token=self.bob)
        self.call(self.bob, 'submit', lease=lease2['lease'], artifact_id=result2['id'])
        self.admin_call('release_batch', batch_id=batch, target_epoch=2)
        future = self.admin_call('create_context', role='discovery', epoch=2, artifact_ids=[result['id']])
        self.assertIn('fixture:exposed', future['exposure'])
        with self.assertRaises(Denied):
            self.admin_call('create_context', role='discovery', epoch=1, artifact_ids=[result['id']])

    def test_idempotency_conflict_restart_and_backup(self):
        job = self.job()
        self.assertEqual(job, self.job())
        with self.assertRaises(Conflict):
            self.job(purpose='Different request')
        lease = self.claim()
        self.broker.close()
        self.now += 11
        self.broker = Broker(Path(self.tmp.name), clock=lambda: self.now)
        self.assertEqual(self.claim(self.bob)['lease']['generation'], 2)
        self.assertEqual(self.admin_call('verify')['status'], 'PASS')
        backup = Path(self.tmp.name) / 'backup.sqlite3'
        self.admin_call('backup', destination=str(backup))
        self.assertTrue(backup.exists())
        restored_dir = Path(self.tmp.name) / 'restored'
        restored_dir.mkdir()
        shutil.copyfile(backup, restored_dir / 'registry.sqlite3')
        shutil.copyfile(Path(self.tmp.name) / 'operator.key', restored_dir / 'operator.key')
        restored = Broker(restored_dir, clock=lambda: self.now)
        try:
            actual = restored.call(self.admin, 'inspect', job_id=job['id'])
            self.assertEqual(actual, self.admin_call('inspect', job_id=job['id']))
            self.assertEqual(restored.call(self.admin, 'verify')['status'], 'PASS')
        finally:
            restored.close()

    def test_interrupted_first_initialization_recovers_persisted_operator_key(self):
        directory = Path(self.tmp.name) / 'interrupted-init'
        directory.mkdir()
        token = 'persisted-before-the-first-principal-commit'
        (directory / 'operator.key').write_text(token, encoding='utf-8')
        recovered = Broker(directory)
        try:
            self.assertEqual(recovered.admin_token, token)
            self.assertEqual(recovered.call(token, 'verify')['status'], 'PASS')
        finally:
            recovered.close()

    def test_operator_can_inspect_retained_evidence_without_exposing_it_to_workers(self):
        self.job()
        lease = self.claim()
        artifact = self.put(lease, body={'unsupported': 'retained for investigation'})
        self.call(self.alice, 'submit', lease=lease['lease'], artifact_id=artifact['id'])
        self.assertEqual(self.admin_call('get_artifact', artifact_id=artifact['id'])['body'],
                         {'unsupported': 'retained for investigation'})
        with self.assertRaises(Denied):
            self.call(self.bob, 'get_artifact', artifact_id=artifact['id'])

    def test_budgets_heartbeats_and_dependencies(self):
        first = self.job('first', max_attempts=1, deadline=1020)
        second = self.job('second', dependencies=[first['id']])
        lease = self.claim()
        self.now = 1009
        self.assertEqual(self.call(self.alice, 'heartbeat', lease=lease['lease'])['lease_until'], 1019)
        self.now = 1018
        self.assertEqual(self.call(self.alice, 'heartbeat', lease=lease['lease'])['lease_until'], 1020)
        self.now = 1020
        self.assertIsNone(self.claim())
        self.assertEqual(self.admin_call('inspect', job_id=first['id'])['state'], 'failed')
        self.assertEqual(self.admin_call('inspect', job_id=second['id'])['state'], 'ready')
        with self.assertRaises(Conflict):
            self.admin_call('resume', job_id=first['id'], reason='Ignore limit')

    def test_single_writer_and_immutable_storage(self):
        with self.assertRaises(Conflict):
            Broker(Path(self.tmp.name))
        with sqlite3.connect(Path(self.tmp.name) / 'registry.sqlite3') as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute('UPDATE artifacts SET envelope=?', ('{}',))
        connection.close()

    def test_negative_source_report_completes_without_evidence_authority(self):
        worker = self.admin_call('register_worker', name='reporter', role='reporter',
                                capabilities=['source-report/v1'])['token']
        record = self.admin_call('add_source', body={'outcome': 'NEGATIVE', 'fixture': True},
                                data_class='assessment')
        ctx = self.admin_call('create_context', role='reporter', epoch=1, artifact_ids=[record['id']])
        self.job(kind='source-report/v1', context_id=ctx['id'], allowed_workers=['reporter'])
        lease = self.claim(worker)
        body = {'records': [{'source_id': record['id'], 'body': record['body']}]}
        result = self.call(worker, 'put_artifact', lease=lease['lease'], body=body, source_refs=[record['id']])
        completion = self.call(worker, 'submit', lease=lease['lease'], artifact_id=result['id'])
        self.assertEqual(completion['state'], 'completed')
        self.assertFalse(completion['scientific_authority'])

    def test_numerical_check_rejects_wrong_total_and_accepts_exact_decimal(self):
        worker = self.admin_call('register_worker', name='calculator', role='executor',
                                capabilities=['decimal-sum/v1'])['token']
        source = self.admin_call('add_source', body={'values': ['0.1', '0.2', '-0.05']},
                                data_class='development')['id']
        ctx = self.admin_call('create_context', role='executor', epoch=1, artifact_ids=[source])
        job = self.job(kind='decimal-sum/v1', context_id=ctx['id'], allowed_workers=['calculator'])
        lease = self.claim(worker)
        wrong = self.call(worker, 'put_artifact', lease=lease['lease'],
                          body={'count': 3, 'total': '0.30'}, source_refs=[source])
        self.assertFalse(self.call(worker, 'submit', lease=lease['lease'], artifact_id=wrong['id'])['accepted'])
        self.admin_call('resume', job_id=job['id'], reason='Correct arithmetic')
        lease = self.claim(worker)
        correct = self.call(worker, 'put_artifact', lease=lease['lease'],
                            body={'count': 3, 'total': '0.25'}, source_refs=[source])
        self.assertTrue(self.call(worker, 'submit', lease=lease['lease'], artifact_id=correct['id'])['accepted'])

    def test_schedules_are_durable_idempotent_and_do_not_change_evidence(self):
        spec = dict(kind='draft/v1', context_id=self.context, purpose='Scheduled fixture',
                    allowed_workers=['alice'], max_attempts=1, lease_seconds=10,
                    deadline=1200, dependencies=[])
        self.admin_call('add_schedule', key='timer', spec=spec, at=1005, interval=5, max_fires=2)
        self.admin_call('add_schedule', key='event', spec=spec, event_type='fixture-ready', max_fires=2)
        self.assertEqual(self.admin_call('tick')['enqueued'], [])
        event = self.admin_call('emit', event_type='fixture-ready', event_id='immutable-source-1')
        self.assertEqual(event, self.admin_call('emit', event_type='fixture-ready', event_id='immutable-source-1'))
        self.broker.close()
        self.now = 1010
        self.broker = Broker(Path(self.tmp.name), clock=lambda: self.now)
        self.assertEqual(len(self.admin_call('tick')['enqueued']), 2)
        self.assertEqual(self.admin_call('tick')['enqueued'], [])
        self.assertEqual(len(self.admin_call('status')['jobs']), 3)
        self.assertFalse(self.admin_call('status')['scientific_authority'])

    def test_invalid_json_and_unknown_checker_cannot_succeed(self):
        from trading_researcher.codec import decode
        for raw in ['{"a":1,"a":2}', '{"value":NaN}', '{"value":0.1}']:
            with self.assertRaises(Invalid):
                decode(raw)
        self.admin_call('register_worker', name='future', role='discovery', capabilities=['missing/v1'])
        task = self.job(kind='missing/v1', allowed_workers=['future'])
        self.assertEqual(self.admin_call('inspect', job_id=task['id'])['state'], 'blocked')

    def test_boolean_substitution_cannot_pass_source_or_numeric_checks(self):
        from trading_researcher.checks import validate
        source = [{'id': 'fixture', 'body': {'nested': [1, 0]}}]
        changed = {'records': [{'source_id': 'fixture', 'body': {'nested': [True, False]}}]}
        with self.assertRaises(Invalid):
            validate('source-report/v1', changed, source)
        with self.assertRaises(Invalid):
            validate('decimal-sum/v1', {'total': '1', 'count': True}, [{'body': {'values': ['1']}}])

    def test_idempotency_does_not_conflate_boolean_and_integer(self):
        self.job(max_attempts=1)
        with self.assertRaises((Conflict, Invalid)):
            self.job(max_attempts=True)

    def test_large_retained_history_remains_pageable(self):
        from trading_researcher.codec import canonical, MAX_BYTES
        for index in range(140):
            self.job(key='history-' + str(index), purpose='x' * 8000)
        cursor, identities = 0, []
        while True:
            page = self.admin_call('status', after=cursor, limit=50)
            self.assertLess(len(canonical(page).encode()), MAX_BYTES)
            self.assertLessEqual(len(page['jobs']), 50)
            self.assertNotIn('spec', page['jobs'][0])
            identities.extend(job['id'] for job in page['jobs'])
            cursor = page['next_cursor']
            if cursor is None:
                break
        self.assertEqual(len(set(identities)), 140)

    def test_subsecond_effective_lease_configuration_is_rejected(self):
        for duration in (1, 2):
            with self.assertRaises(Invalid):
                self.job(key='short-' + str(duration), lease_seconds=duration)

    def test_unserializable_response_does_not_commit_a_claim(self):
        from unittest.mock import patch
        job = self.job()
        original = self.broker._claim
        def oversized(actor):
            result = original(actor)
            result['unexpected_oversized_response'] = 'x' * 1_048_576
            return result
        with patch.object(self.broker, '_claim', side_effect=oversized):
            with self.assertRaises(Invalid):
                self.claim()
        self.assertEqual(self.admin_call('inspect', job_id=job['id'])['attempts'], [])

    def test_internal_controller_identity_and_implicit_batch_are_separate(self):
        with self.assertRaises(Invalid):
            self.admin_call('register_worker', name='controller', role='discovery', capabilities=['draft/v1'])
        batch = self.admin_call('create_batch', key='standalone:job', epoch=1)['id']
        self.job('predeclared', batch_id=batch)
        self.admin_call('seal_batch', batch_id=batch)
        implicit = self.job('job')
        self.assertNotEqual(self.admin_call('inspect', job_id=implicit['id'])['batch_id'], batch)


if __name__ == '__main__':
    unittest.main()
