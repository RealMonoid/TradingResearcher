"""Independent narrow second-original feedback access/retention boundaries.

Small fixtures explicitly isolate metadata and transaction behavior. The opt-in
actual-result test physically clones the selected source before all mutations.
Only inherited D092 location-bound inspection is simulated after proving its
relocation denial. No live budget portability or new scientific claim follows.
"""
from contextlib import closing
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.coordination import Broker
from trading_researcher.feedback import breakout, paired
from trading_researcher.paired_breakout import composition, runtime
from trading_researcher.paired_breakout.research import BreakoutResearchBroker
from trading_researcher import review_continuation
from trading_researcher.features import read_bundle as feature_bundle
from trading_researcher.storage import restore_bundle
from test_paired_feedback import save_copy

REJECT = (Invalid, Conflict, Denied)
ACTUAL_EXECUTION = '8456955e281d7e4f9c50c33ba7763597d87a06ee24c66bd6f1a09bed82003980'


class BreakoutFeedbackBoundaries(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.broker = breakout.BreakoutFeedbackBroker(Path(self.temp.name) / 'registry')

    def tearDown(self):
        self.broker.close()
        self.temp.cleanup()

    def test_operator_namespaces_and_inherited_source_identity_preserved(self):
        broker = self.broker
        token = broker.call(broker.admin_token, 'register_worker', name='fixture', role='discovery', capabilities=[])['token']
        with self.assertRaises(Denied):
            broker.publish_breakout_feedback(token, root_epoch_id='root', execution_id='execution',
                composition_id='composition', meaning_review_assessment_id='review', target_epoch=2)
        self.assertNotEqual(breakout.MANIFEST, paired.MANIFEST)
        self.assertNotEqual(breakout.RELEASE, paired.RELEASE)
        self.assertNotEqual(breakout.AUTHORITY, paired.AUTHORITY)
        for schema in (breakout.MANIFEST, breakout.RELEASE, paired.MANIFEST, paired.RELEASE):
            with self.subTest(schema=schema), self.assertRaises(REJECT):
                broker.call(broker.admin_token, 'add_source', body={'schema': schema}, data_class='development')
        self.assertEqual(broker._feedback_source_current(), paired.LOADED_SELF)
        self.assertEqual(broker._breakout_feedback_source_current(), breakout.LOADED_SELF)
        with patch.object(breakout, 'LOADED_SELF', '0' * 64):
            with self.assertRaises(Invalid):
                broker._breakout_feedback_source_current()
            self.assertEqual(broker._feedback_source_current(), paired.LOADED_SELF)
        self.assertNotIn('trading_researcher/feedback/breakout.py', feature_bundle())

    def test_current_owned_package_only_is_technical_and_ancestry_is_preserved(self):
        broker = self.broker
        package = broker._breakout_retain_package(runtime.read_bundle())
        knowledge = breakout.prior_knowledge(broker, package)
        self.assertIn(package['id'], knowledge['technical_provenance_ids'])
        self.assertEqual(knowledge['operations_knowledge_ids'], [])
        self.assertIn(package['id'], knowledge['artifact_ids'])
        for key, value in [('profile', 'unapproved/1'), ('bootstrap_sha256', '0' * 64),
                           ('files', None), ('files', []), ('footprint', {})]:
            with self.subTest(key=key, value=value):
                fake = save_copy(broker, package, body={**package['body'], key: value})
                try:
                    result = breakout.prior_knowledge(broker, fake)
                except REJECT:
                    continue
                self.assertIn(fake['id'], result['operations_knowledge_ids'])
        for key, value in [('creator', 'forged'), ('origin', 'source'), ('authority', 'forged'), ('blob_refs', [])]:
            with self.subTest(field=key):
                fake = save_copy(broker, package, **{key: value})
                self.assertIn(fake['id'], breakout.prior_knowledge(broker, fake)['operations_knowledge_ids'])
        uncontrolled = broker.call(broker.admin_token, 'add_source', body={'fixture': 'operations'}, data_class='operations')
        protected = broker.call(broker.admin_token, 'add_source', body={'fixture': 'protected'}, data_class='assessment')
        inherited = save_copy(broker, package, exposure=sorted([uncontrolled['id'], protected['id'], 'unresolved-fixture']))
        knowledge = breakout.prior_knowledge(broker, inherited)
        self.assertIn(uncontrolled['id'], knowledge['operations_knowledge_ids'])
        self.assertIn(protected['id'], knowledge['protected_knowledge_ids'])
        self.assertIn('unresolved-fixture', knowledge['unresolved_exposure_refs'])
        self.assertIn(inherited['id'], knowledge['operations_knowledge_ids'])

    def test_unaffected_descendant_data_use_delegates_exactly(self):
        # No grant means exact preexisting result; no blanket removal of gaps.
        value = {'status': 'DATA_USE_GAP', 'gaps': ['PRESERVE_ME'], 'sentinel': object()}
        with patch.object(BreakoutResearchBroker, '_paired_data_use', return_value=value) as previous:
            dependencies = {'formalization': {'exposure': []}}
            self.assertIs(self.broker._paired_data_use(dependencies), value)
            previous.assert_called_once_with(dependencies)

    def test_wrong_execution_profile_is_denied_before_dependency_or_blob_load(self):
        broker = self.broker
        source = broker.call(broker.admin_token, 'add_source', body={'fixture': 'execution holder'}, data_class='development')
        forged = save_copy(broker, source, creator='controller', origin='controller',
            authority='paired_descriptive_development_only', body={
                'schema': 'paired-reference-execution/1', 'profile': 'paired-development/1',
                'status': 'DESCRIPTIVE_EXECUTION', 'error': None, 'scientific_readiness': False,
                'compiled_id': 'unreachable'})
        request = {'execution_id': forged['id'], 'composition_id': 'unreachable', 'meaning_review_assessment_id': 'unreachable'}
        with patch.object(broker, '_breakout_compiled', side_effect=AssertionError('Dependency loader reached')) as dependencies, \
                patch.object(broker, '_read_blob_bytes', side_effect=AssertionError('Case blob reached')) as blobs, \
                self.assertRaises(REJECT):
            breakout._evidence(broker, {'role': 'operator'}, request, read_cases=True)
        dependencies.assert_not_called()
        blobs.assert_not_called()

    def test_atomic_publication_rollback_time_fencing_and_single_case_qualification(self):
        broker = self.broker
        inputs = [broker.call(broker.admin_token, 'add_source', body={'fixture': n}, data_class='development') for n in range(3)]
        execution = deepcopy(inputs[0])
        execution['body'] = {'result': {'report': {'processed_case_count': 2},
            'contrast': {'status': 'DESCRIPTIVE_ONLY', 'condition_count': 1, 'scope_count': 2, 'scientific_readiness': False},
            'case_blob': {'sha256': '0' * 64, 'size': 0}}}
        cohort = {'artifact_ids': sorted(x['id'] for x in inputs), 'unresolved_exposure_refs': [],
            'batches': [{'epoch': 1}], 'jobs': [], 'calls': []}
        request = dict(root_epoch_id='synthetic-root', execution_id=inputs[0]['id'], composition_id=inputs[1]['id'],
            meaning_review_assessment_id=inputs[2]['id'], target_epoch=2)
        def counts():
            return {table: broker._db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                    for table in ('artifacts', 'research_records', 'events', 'releases', 'contexts')}
        before = counts()
        # Only collector/evidence are isolated fixtures; real save/index/grant,
        # transaction, authority, clock and revocation behavior remain intact.
        with patch.object(breakout, 'collect_cohort', return_value=cohort), \
                patch.object(breakout, '_evidence', return_value=(execution, {'fixture_only': True})):
            with patch.object(broker, '_event', side_effect=OSError('Synthetic final-event interruption')), self.assertRaises(OSError):
                broker.publish_breakout_feedback(broker.admin_token, **request)
            self.assertEqual(counts(), before)
            saved_ids = broker.publish_breakout_feedback(broker.admin_token, **request)
            after = counts()
            self.assertEqual(after['artifacts'] - before['artifacts'], 4)
            self.assertEqual(after['research_records'] - before['research_records'], 2)
            self.assertEqual(after['releases'], before['releases'])
            self.assertEqual(broker.publish_breakout_feedback(broker.admin_token, **request), saved_ids)
            self.assertEqual(counts(), after)
            with self.assertRaises(Conflict):
                broker.publish_breakout_feedback(broker.admin_token, **{**request, 'target_epoch': 3})
            saved = {key: broker._artifact(identity) for key, identity in saved_ids.items()}
            observation = saved['observation_id']['body']['content']
            experience = saved['experience_id']['body']['content']
            self.assertEqual(json.loads(observation['measurement'])['contrast']['condition_count'], 1)
            for content in (observation, experience):
                wording = canonical(content).lower()
                self.assertTrue('single' in wording or 'only one qualifying observed case' in wording)
                self.assertIn('statistical', wording)
                self.assertIn('numerical', wording)
                self.assertIn('economic', wording)
            grant = saved['grant_id']
            for epoch, when in ((1, broker._now()), (2, grant['body']['created_at'] - 1)):
                with self.subTest(epoch=epoch), self.assertRaises(Denied):
                    breakout._check_grant(broker, grant, epoch, when)
            with patch.object(breakout, 'LOADED_SELF', '0' * 64), self.assertRaises(Invalid):
                breakout._check_grant(broker, grant, 2, broker._now())
            for field, value in [('creator', 'forged'), ('authority', 'forged'), ('source_refs', [])]:
                fake = save_copy(broker, saved['observation_id'], **{field: value})
                try:
                    found = breakout.released_feedback(broker, fake, 2, broker._now())
                except REJECT:
                    continue
                self.assertIsNone(found)
            defect = broker.call(broker.admin_token, 'add_source', body={'fixture': 'defect'}, data_class='development')
            revoked = broker.call(broker.admin_token, 'revoke_dependency', key='breakout-feedback-defect',
                dependency_id=saved_ids['manifest_id'], reason='Synthetic direct manifest revocation', evidence_refs=[defect['id']])
            self.assertEqual(revoked['body']['status'], 'REVOKED')
            with self.assertRaises(Denied):
                breakout._check_grant(broker, grant, 2, broker._now())


@unittest.skipUnless(os.environ.get('TRF_BREAKOUT_FEEDBACK_SOURCE'),
    'An explicitly selected read-only source registry is required for the physical-clone lifecycle')
class BreakoutRetainedFeedbackLifecycle(unittest.TestCase):
    def test_actual_closed_result_publish_read_restore_revoke_on_physical_clone(self):
        source = Path(os.environ['TRF_BREAKOUT_FEEDBACK_SOURCE']).resolve(strict=True)
        ledger = Path(os.environ['TRF_BREAKOUT_FEEDBACK_LEDGER']).resolve(strict=True)
        with closing(sqlite3.connect(ledger.as_uri() + '?mode=ro', uri=True)) as external:
            external.execute('PRAGMA query_only=ON')
            row = external.execute('SELECT binding,calls,revoked FROM research_epoch_budget_grants WHERE approval=?',
                (review_continuation.APPROVAL,)).fetchone()
        self.assertIsNotNone(row)
        closed = {'binding': json.loads(row[0]), 'calls': json.loads(row[1]), 'revoked': bool(row[2])}
        self.assertTrue(closed['revoked'])

        def simulated_closed_fence(host, epoch):
            bound = review_continuation.binding(host, epoch)
            bound['registry_identity'] = digest(str(source))
            self.assertEqual(bound, closed['binding'])
            calls = [item[0] for item in host._db.execute('SELECT id FROM research_calls WHERE epoch_id=? ORDER BY rowid', (epoch['id'],))]
            self.assertEqual(calls, [item['call_id'] for item in closed['calls']])
            return deepcopy(closed)

        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix='trf-breakout-feedback-independent-') as directory:
            root = Path(directory).resolve()
            clone = root / 'clone'
            clone.mkdir()
            self.assertNotEqual(clone, source)
            with closing(sqlite3.connect((source / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as original, \
                    closing(sqlite3.connect(clone / 'registry.sqlite3')) as target:
                original.execute('PRAGMA query_only=ON')
                original.backup(target)
                source_counts = {table: original.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                    for table in ('artifacts', 'events', 'contexts', 'research_calls')}
            shutil.copytree(source / 'blobs', clone / 'blobs')
            shutil.copyfile(source / 'operator.key', clone / 'operator.key')
            print('Breakout feedback: physical clone ready; no provider routes.', flush=True)
            with closing(breakout.BreakoutFeedbackBroker(clone)) as host:
                execution = host._artifact(ACTUAL_EXECUTION)
                compiled = host._artifact(execution['body']['compiled_id'])
                certificate_id = compiled['body']['reference_certificate_id']
                host._paired_certificate_id = certificate_id
                formal = host._artifact(compiled['body']['formalization_id'])
                idea = host._artifact(formal['body']['idea_id'])
                self.assertEqual(idea['id'], composition.IDEA_ID)
                root_epoch = host._job(idea['job_id'])['spec']['research_epoch_id']
                cohort = breakout.collect_cohort(host, root_epoch)
                target_epoch = max(item['epoch'] for item in cohort['batches']) + 1
                request = dict(root_epoch_id=root_epoch, execution_id=execution['id'],
                    composition_id=execution['body']['composition_id'],
                    meaning_review_assessment_id=execution['body']['meaning_assessment_id'], target_epoch=target_epoch)
                jobs_before = [tuple(row) for row in host._db.execute('SELECT * FROM jobs ORDER BY id')]
                calls_before = [tuple(row) for row in host._db.execute('SELECT * FROM research_calls ORDER BY rowid')]
                generic_before = [tuple(row) for row in host._db.execute('SELECT * FROM releases ORDER BY artifact_id')]
                old_feedback = {row[0]: row[1] for row in host._db.execute(
                    "SELECT id,envelope FROM artifacts WHERE json_extract(envelope,'$.body.schema') IN "
                    "('development-feedback-manifest/1','development-feedback-release/1','paired-development-feedback-manifest/1','paired-development-feedback-release/1')")}
                published = host.publish_breakout_feedback(host.admin_token, **request)
                saved = {key: host._artifact(identity) for key, identity in published.items()}
                manifest = saved['manifest_id']
                self.assertEqual(manifest['body']['request'], request)
                self.assertEqual(manifest['body']['cohort'], cohort)
                self.assertEqual(manifest['body']['publisher_sha256'], breakout.LOADED_SELF)
                retained = []
                for identity in cohort['artifact_ids']:
                    artifact = host._artifact(identity)
                    body = artifact['body']
                    if isinstance(body, dict) and body.get('schema') == 'research-record/1' and body.get('kind') in ('idea', 'gap'):
                        retained.append({key: artifact[key] for key in ('id', 'creator', 'authority', 'body', 'source_refs', 'exposure')})
                self.assertEqual(manifest['body']['retained_research_records'], retained)
                self.assertIn(idea['id'], {item['id'] for item in retained})
                self.assertTrue(any(item['body']['kind'] == 'gap' for item in retained))
                self.assertEqual(len(cohort['idea_ids']), 2)
                for item in saved.values():
                    self.assertEqual(item['authority'], breakout.AUTHORITY)
                    self.assertTrue(set(cohort['artifact_ids']) <= set(item['exposure']))
                self.assertEqual(host.publish_breakout_feedback(host.admin_token, **request), published)
                self.assertEqual([tuple(row) for row in host._db.execute('SELECT * FROM jobs ORDER BY id')], jobs_before)
                self.assertEqual([tuple(row) for row in host._db.execute('SELECT * FROM research_calls ORDER BY rowid')], calls_before)
                self.assertEqual([tuple(row) for row in host._db.execute('SELECT * FROM releases ORDER BY artifact_id')], generic_before)
                for identity, envelope in old_feedback.items():
                    self.assertEqual(canonical({key: value for key, value in host._artifact(identity).items() if key != 'id'}), envelope)
                print('Breakout feedback: current actual evidence, exact cohort and atomic publication passed.', flush=True)
                # The external D092 fence is deliberately tied to its original
                # registry path; there is no claim of portable live authority.
                with self.assertRaises(REJECT):
                    host.call(host.admin_token, 'create_context', role='discovery', epoch=target_epoch,
                        artifact_ids=[manifest['id']])
                simulation = patch.object(review_continuation, 'inspect', side_effect=simulated_closed_fence)
                simulation.start()
                self.addCleanup(simulation.stop)
                context = host.call(host.admin_token, 'create_context', role='discovery', epoch=target_epoch,
                    artifact_ids=[manifest['id'], published['observation_id'], published['experience_id']])
                self.assertIn(published['grant_id'], context['exposure'])
                host._check_feedback_context(context)
                reader = host.call(host.admin_token, 'register_worker', name='breakout-feedback-reader', role='discovery', capabilities=['draft/v1'])
                host.call(host.admin_token, 'enqueue', key='breakout-feedback-reader', spec={
                    'kind': 'draft/v1', 'context_id': context['id'], 'purpose': 'Independent isolated feedback access',
                    'allowed_workers': ['breakout-feedback-reader'], 'max_attempts': 1, 'lease_seconds': 3600,
                    'deadline': host._now() + 7200, 'dependencies': []})
                lease = host.call(reader['token'], 'claim')['lease']
                self.assertEqual(host.call(reader['token'], 'read_artifact', lease=lease, artifact_id=manifest['id']), manifest)
                with self.assertRaises(Denied):
                    host.call(reader['token'], 'read_artifact', lease=lease, artifact_id=execution['id'])
                backup = root / 'backup'
                host.call(host.admin_token, 'backup_bundle', destination=str(backup))
                print('Breakout feedback: explicit trio access and complete backup passed.', flush=True)
            with closing(Broker(clone)) as plain:
                with self.assertRaises(Denied):
                    plain.call(plain.admin_token, 'create_context', role='discovery', epoch=target_epoch, artifact_ids=[manifest['id']])
            restored = root / 'restored'
            restore_bundle(backup, restored, clone / 'operator.key')
            with closing(breakout.BreakoutFeedbackBroker(restored, paired_certificate_id=certificate_id)) as other:
                for key, item in saved.items():
                    self.assertEqual(other._artifact(published[key]), item)
                context2 = other.call(other.admin_token, 'create_context', role='discovery', epoch=target_epoch,
                    artifact_ids=[published['experience_id']])
                other._check_feedback_context(context2)
                defect = other.call(other.admin_token, 'add_source', body={'fixture': 'technical defect'}, data_class='development')
                other.call(other.admin_token, 'revoke_dependency', key='breakout-feedback-grant-revoke',
                    dependency_id=published['grant_id'], reason='Synthetic direct grant revocation', evidence_refs=[defect['id']])
                with self.assertRaises(Denied):
                    other._check_feedback_context(context2)
                with self.assertRaises(Denied):
                    other.call(other.admin_token, 'create_context', role='discovery', epoch=target_epoch,
                        artifact_ids=[published['observation_id']])
                self.assertEqual(other._artifact(ACTUAL_EXECUTION), execution)
            with closing(sqlite3.connect((source / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as original:
                original.execute('PRAGMA query_only=ON')
                self.assertEqual({table: original.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                    for table in source_counts}, source_counts)
            print('Breakout feedback: restore, direct revocation and unchanged production counts passed (%.3fs).' % (time.monotonic() - started), flush=True)


if __name__ == '__main__':
    unittest.main()
