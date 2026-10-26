"""Research memory acceptance through the authenticated broker, using real SQLite."""
import shutil
from contextlib import closing
import sqlite3
import tempfile
import unittest
import json
import subprocess
import sys
from pathlib import Path

from trading_researcher.coordination import Broker, Conflict, Denied, Invalid, SCHEMA as COORDINATION_SCHEMA
from trading_researcher.codec import canonical, digest


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.directory = Path(self.tmp.name) / 'registry'
        self.now = 1000
        self.broker = Broker(self.directory, clock=lambda: self.now)
        self.admin = self.broker.admin_token
        self.worker = self.op('register_worker', name='researcher', role='discovery',
                              capabilities=['draft/v1', 'research-record/v1'])['token']

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def op(self, operation, **args):
        return self.broker.call(self.admin, operation, **args)

    def source(self, text='Fixture source', **args):
        return self.op('add_research', kind='source',
                       content={'text': text, 'uri': 'fixture:source'},
                       scope={'instrument': 'fixture'}, source_refs=[], **args)['id']

    def start(self, ids, job_kind='draft/v1', **args):
        context = self.op('create_context', role='discovery', epoch=1,
                          artifact_ids=ids, **args)
        self.op('enqueue', key='research', spec={
            'kind': job_kind, 'context_id': context['id'], 'purpose': 'Memory fixture',
            'allowed_workers': ['researcher'], 'max_attempts': 2, 'lease_seconds': 10,
            'deadline': 1100, 'dependencies': []})
        return self.broker.call(self.worker, 'claim')['lease']

    def search(self, lease, **args):
        return self.broker.call(self.worker, 'search_memory', lease=lease, **args)

    def test_history_preserves_correction_conflict_and_provenance(self):
        first = self.source('original observation')
        second = self.op('add_research', kind='observation',
                         content={'text': 'corrected observation'}, scope={'instrument': 'fixture'},
                         source_refs=[first], relations={'supersedes': [first]})['id']
        third = self.op('add_research', kind='observation',
                        content={'text': 'conflicting observation'}, scope={'instrument': 'fixture'},
                        source_refs=[first], relations={'contradicts': [second]})['id']
        rows = self.op('inspect_memory', view='journal')['records']
        self.assertEqual([r['id'] for r in rows], [first, second, third])
        self.assertEqual(rows[1]['record']['relations']['supersedes'], [first])
        self.assertIn(second, rows[2]['exposure'])
        with closing(sqlite3.connect(self.directory / 'registry.sqlite3')) as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('UPDATE artifacts SET envelope=? WHERE id=?', ('{}', first))
        self.assertEqual(self.op('get_artifact', artifact_id=first)['body']['content']['text'],
                         'original observation')

    def test_search_filters_before_counts_and_uses_frozen_snapshot(self):
        visible = self.source('allowed needle')
        hidden = self.source('protected needle', data_class='assessment')
        lease = self.start([visible])
        self.source('later needle')
        result = self.search(lease, query='needle')
        self.assertEqual([r['id'] for r in result['records']], [visible])
        self.assertEqual(result['total'], 1)
        self.assertNotIn(hidden, str(result))
        self.assertEqual(self.search(lease, query='protected')['total'], 0)
        with self.assertRaises(Denied):
            self.op('create_context', role='discovery', epoch=2, artifact_ids=[hidden])

    def test_available_at_and_context_time_are_enforced(self):
        future = self.source('future', available_at=1001)
        with self.assertRaises(Denied):
            self.start([future])
        self.now = 1002
        with self.assertRaises(Denied):
            self.op('create_context', role='discovery', epoch=1,
                    artifact_ids=[future], research_time=1000)
        context = self.op('create_context', role='discovery', epoch=1,
                          artifact_ids=[future], research_time=1002)
        self.assertEqual(context['research_time'], 1002)

    def test_worker_drafts_inherit_context_and_cannot_self_certify(self):
        a, b = self.source('first'), self.source('second')
        lease = self.start([a, b])
        result = self.broker.call(self.worker, 'record_research', lease=lease, kind='idea',
                                  content={'text': 'An unusual new claim'}, scope={}, source_refs=[a])
        record = self.op('get_artifact', artifact_id=result['id'])
        self.assertEqual(record['source_refs'], sorted([a, b]))
        self.assertEqual(record['authority'], 'unverified_work_product')
        for kind in ('evidence', 'market_finding'):
            with self.assertRaises(Invalid):
                self.broker.call(self.worker, 'record_research', lease=lease, kind=kind,
                                 content={'text': 'I have proven it'}, scope={}, source_refs=[])
        with self.assertRaises(Invalid):
            self.broker.call(self.worker, 'record_research', lease=lease, kind='idea',
                             content={'text': 'claim', 'scientific_status': 'SUPPORTED'},
                             scope={}, source_refs=[])
        self.assertEqual(self.op('inspect_memory', view='market_model')['records'], [])

    def test_four_views_distinguish_heuristics_and_policy_observations(self):
        source = self.source()
        self.op('add_research', kind='research_experience', scope={}, source_refs=[source],
                content={'text': 'Try a different diagnostic', 'interpretation': 'Untested heuristic'})
        self.op('add_research', kind='policy_experience', scope={}, source_refs=[source],
                content={'text': 'Execution fixture failed', 'interpretation': 'Operational observation'})
        self.assertEqual(len(self.op('inspect_memory', view='journal')['records']), 3)
        self.assertEqual(len(self.op('inspect_memory', view='research_experience')['records']), 1)
        self.assertEqual(len(self.op('inspect_memory', view='policy_experience')['records']), 1)
        self.assertEqual(self.op('inspect_memory', view='market_model')['records'], [])

    def test_scope_query_pagination_and_logged_retrieval(self):
        ids = [self.source('same needle ' + str(i)) for i in range(3)]
        lease = self.start(ids)
        first = self.search(lease, query='NEEDLE', scope={'instrument': 'fixture'}, limit=2)
        second = self.search(lease, query='NEEDLE', limit=2, after=first['next_cursor'])
        self.assertEqual([r['id'] for r in first['records'] + second['records']], ids)
        self.assertEqual(self.search(lease, scope={'instrument': 'different'})['total'], 0)
        with closing(sqlite3.connect(self.directory / 'registry.sqlite3')) as db:
            reads = db.execute("SELECT envelope FROM events WHERE envelope LIKE '%memory_retrieved%'").fetchall()
        self.assertEqual(len(reads), 3)
        self.assertIn(ids[0], reads[0][0])
        self.assertIn('metadata-text/1', reads[0][0])

    def test_replay_restart_and_backup_preserve_records(self):
        first = self.source()
        before = self.op('inspect_memory', view='journal')
        self.assertEqual(self.op('rebuild_memory')['records'], 1)
        self.assertEqual(self.op('inspect_memory', view='journal'), before)
        target = Path(self.tmp.name) / 'backup.sqlite3'
        self.op('backup', destination=str(target))
        self.broker.close()
        self.broker = Broker(self.directory, clock=lambda: self.now)
        self.assertEqual(self.op('inspect_memory', view='journal'), before)
        restored = Path(self.tmp.name) / 'restored'
        restored.mkdir()
        shutil.copy2(target, restored / 'registry.sqlite3')
        shutil.copy2(self.directory / 'operator.key', restored / 'operator.key')
        with self.assertRaises(Denied):
            self.broker.call(self.worker, 'inspect_memory')
        other = Broker(restored, clock=lambda: self.now)
        try:
            self.assertEqual(other.call(other.admin_token, 'inspect_memory')['records'][0]['id'], first)
            self.assertEqual(other.call(other.admin_token, 'verify')['research_memory']['records'], 1)
        finally:
            other.close()

    def test_rejected_record_rolls_back_and_relations_cannot_probe_hidden_records(self):
        visible, secret = self.source(), self.source('secret', data_class='assessment')
        lease = self.start([visible])
        before = self.op('inspect_memory')
        for ref in (secret, 'nonexistent'):
            with self.assertRaises(Denied):
                self.broker.call(self.worker, 'record_research', lease=lease, kind='observation',
                                 content={'text': 'probe'}, scope={}, source_refs=[],
                                 relations={'contradicts': [ref]})
        self.assertEqual(self.op('inspect_memory'), before)
        with self.assertRaises(Invalid):
            self.op('add_research', kind='gap', content={'text': 'unsupported'},
                    scope={}, source_refs=[])

    def test_assessment_ancestry_cannot_be_laundered_into_source(self):
        secret = self.source('assessment source', data_class='assessment')
        derived = self.op('add_research', kind='observation', content={'text': 'summary'},
                          scope={}, source_refs=[secret], data_class='development')['id']
        with self.assertRaises(Denied):
            self.op('create_context', role='discovery', epoch=1, artifact_ids=[derived])

    def test_generic_artifact_api_cannot_inject_typed_memory(self):
        source = self.source()
        body = self.op('get_artifact', artifact_id=source)['body']
        with self.assertRaises(Invalid):
            self.op('add_source', body=body, data_class='development')
        lease = self.start([source])
        with self.assertRaises(Invalid):
            self.broker.call(self.worker, 'put_artifact', lease=lease, body=body, source_refs=[])
        self.assertEqual(self.op('verify')['research_memory']['records'], 1)

    def test_writer_roles_and_invalid_search_shapes(self):
        lease = self.start([])
        with self.assertRaises(Denied):
            self.broker.call(self.worker, 'record_research', lease=lease, kind='policy_experience',
                             content={'text': 'Operational claim', 'interpretation': 'Hypothesis'},
                             scope={}, source_refs=[])
        for bad_scope in ([], '', False):
            with self.assertRaises(Invalid):
                self.search(lease, scope=bad_scope)
        for kind in ([], {}, False):
            with self.assertRaises(Invalid):
                self.search(lease, kind=kind)

    def test_typed_completion_releases_retained_history_only_with_batch(self):
        source = self.source()
        lease = self.start([source], job_kind='research-record/v1')
        args = dict(lease=lease, scope={}, source_refs=[source])
        gap = self.broker.call(self.worker, 'record_research', kind='gap',
                              content={'text': 'First idea needs another measure',
                                       'reason': 'Unavailable feature', 'reopen_condition': 'Feature certified'},
                              **args)['id']
        idea = self.broker.call(self.worker, 'record_research', kind='idea',
                               content={'text': 'Another free idea'}, **args)['id']
        with self.assertRaises(Denied):
            self.op('add_research', kind='observation', content={'text': 'Premature summary'},
                    scope={}, source_refs=[gap])
        completion = self.broker.call(self.worker, 'submit', lease=lease, artifact_id=idea)
        self.assertTrue(completion['accepted'])
        self.assertFalse(completion['scientific_authority'])
        with self.assertRaises(Denied):
            self.op('create_context', role='discovery', epoch=2, artifact_ids=[gap])
        job = self.op('inspect', job_id=lease['job_id'])
        self.op('seal_batch', batch_id=job['batch_id'])
        released = self.op('release_batch', batch_id=job['batch_id'], target_epoch=2)
        self.assertTrue({gap, idea} <= set(released['artifact_ids']))
        terminals = self.op('inspect_memory', kind='attempt')['records']
        self.assertEqual(len(terminals), 1)
        self.assertEqual(terminals[0]['authority'], 'observed_operational_event')
        self.assertEqual(terminals[0]['record']['content']['outcome'], 'completed')
        self.assertIn(terminals[0]['id'], released['artifact_ids'])
        self.op('create_context', role='discovery', epoch=2, artifact_ids=[gap, idea])
        derived = self.op('add_research', kind='research_experience',
                          content={'text': 'A heuristic', 'interpretation': 'Not validated'},
                          scope={}, source_refs=[gap])['id']
        with self.assertRaises(Denied):
            self.op('create_context', role='discovery', epoch=1, artifact_ids=[derived])

    def test_legacy_migration_preserves_bytes_and_makes_backup(self):
        legacy = Path(self.tmp.name) / 'legacy'
        legacy.mkdir()
        token = 'fixture-operator-token-with-at-least-32-characters'
        (legacy / 'operator.key').write_text(token, encoding='utf-8')
        envelope = {'version': 'local-artifact/1', 'creator': 'operator', 'origin': 'source',
                    'data_class': 'development', 'body': {'text': 'old source'},
                    'source_refs': [], 'exposure': [], 'authority': 'supplied_source_not_certified'}
        identity = digest(envelope)
        with closing(sqlite3.connect(legacy / 'registry.sqlite3')) as db:
            db.executescript(COORDINATION_SCHEMA)
            db.execute('PRAGMA user_version=1')
            db.execute('INSERT INTO principals VALUES(?,?,?,?)',
                       ('operator', Broker._token_hash(token), 'operator', '[]'))
            db.execute('INSERT INTO artifacts VALUES(?,?)', (identity, canonical(envelope)))
            db.commit()
        migrated = Broker(legacy, clock=lambda: self.now)
        try:
            self.assertEqual(migrated.call(token, 'get_artifact', artifact_id=identity),
                             {'id': identity, **envelope})
            backup = legacy / 'before-research-memory-v1.sqlite3'
            self.assertTrue(backup.is_file())
            with closing(sqlite3.connect(backup)) as db:
                self.assertIsNone(db.execute("SELECT 1 FROM sqlite_master WHERE name='research_meta'").fetchone())
                self.assertEqual(db.execute('SELECT envelope FROM artifacts').fetchone()[0], canonical(envelope))
        finally:
            migrated.close()

    def test_crash_keeps_committed_memory_and_discards_uncommitted_record(self):
        self.broker.close()
        code = '''from trading_researcher.coordination import Broker
import os,sys
b=Broker(sys.argv[1], clock=lambda: 1000)
b.call(b.admin_token, 'add_research', kind='observation', content={'text':'committed'}, scope={}, source_refs=[])
b._db.execute('BEGIN IMMEDIATE')
b._add_research({'name':'operator'}, 'observation', {'text':'uncommitted'}, {}, [])
os._exit(23)
'''
        result = subprocess.run([sys.executable, '-B', '-c', code, str(self.directory)],
                                capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 23, result.stderr)
        self.broker = Broker(self.directory, clock=lambda: self.now)
        rows = self.op('inspect_memory')['records']
        self.assertEqual([r['record']['content']['text'] for r in rows], ['committed'])
        self.assertEqual(self.op('verify')['research_memory']['records'], 1)

    def test_worker_can_link_own_observations_without_accessing_another_attempt(self):
        lease = self.start([])
        first = self.broker.call(self.worker, 'record_research', lease=lease, kind='observation',
                                 content={'text': 'Earlier observation'}, scope={}, source_refs=[])['id']
        second = self.broker.call(self.worker, 'record_research', lease=lease, kind='idea',
                                  content={'text': 'An idea from that observation'}, scope={},
                                  source_refs=[first], relations={'depends_on': [first]})['id']
        self.assertIn(first, self.op('get_artifact', artifact_id=second)['exposure'])
        self.assertEqual(self.search(lease)['total'], 2)
        self.now = 1011
        fresh = self.broker.call(self.worker, 'claim')['lease']
        self.assertEqual(self.search(fresh)['total'], 0)
        with self.assertRaises(Denied):
            self.broker.call(self.worker, 'record_research', lease=fresh, kind='idea',
                             content={'text': 'Cannot silently reuse prior attempt'}, scope={},
                             source_refs=[first])

    def test_invalid_existing_migration_backup_does_not_allow_migration(self):
        self.broker.close()
        with closing(sqlite3.connect(self.directory / 'registry.sqlite3')) as db:
            db.execute('DROP TABLE research_records')
            db.execute('DROP TABLE research_meta')
            db.commit()
        backup = self.directory / 'before-research-memory-v1.sqlite3'
        backup.write_bytes(b'partial backup')
        try:
            with self.assertRaises(Conflict):
                invalid = Broker(self.directory, clock=lambda: self.now)
                invalid.close()
            with closing(sqlite3.connect(self.directory / 'registry.sqlite3')) as db:
                self.assertIsNone(db.execute("SELECT 1 FROM sqlite_master WHERE name='research_meta'").fetchone())
        finally:
            # Remove only this deliberately corrupt test fixture, not user data.
            backup.unlink()
            self.broker = Broker(self.directory, clock=lambda: self.now)

    def test_expiration_and_worker_claim_are_separate_journal_authorities(self):
        lease = self.start([])
        self.broker.call(self.worker, 'record_research', lease=lease, kind='attempt',
                         content={'text': 'The model claims completion', 'outcome': 'completed'},
                         scope={}, source_refs=[])
        self.now = 1011
        self.broker.call(self.worker, 'claim')
        records = self.op('inspect_memory', kind='attempt')['records']
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['authority'], 'unverified_work_product')
        actual = records[1]
        self.assertEqual(actual['authority'], 'observed_operational_event')
        self.assertEqual(actual['record']['content']['outcome'], 'expired')
        self.assertEqual(actual['record']['content']['details']['reason'], 'Lease expired')
        self.assertEqual(actual['record']['content']['generation'], lease['generation'])


if __name__ == '__main__':
    unittest.main()
