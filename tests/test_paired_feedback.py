"""Independent paired-feedback publication boundaries.

Ordinary tests use temporary synthetic registries. The optional retained-result
integration fixture requires TRF_PAIRED_FEEDBACK_SOURCE and always copies that
read-only source to a separate temporary registry before any mutation.
Its inherited D092 budget fence is intentionally registry-location-bound: after
proving relocation denial, only that inspector is simulated with the exact
retained closed grant. This does not certify relocated live budget authority.
"""
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timezone
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
from trading_researcher.feedback import paired
from trading_researcher.features import read_bundle as feature_bundle
from trading_researcher import development_feedback as legacy
from trading_researcher import review_continuation as legacy_review
from trading_researcher.paired_computation import PairedComputation
from trading_researcher.storage import restore_bundle

REJECTIONS = (Invalid, Conflict, Denied)


def save_copy(broker, artifact, *, body=None, **changes):
    """Synthetic owned metadata for hostile tests, never an accepted model result."""
    envelope = deepcopy({key: value for key, value in artifact.items() if key != 'id'})
    if body is not None:
        envelope['body'] = body
    envelope.update(changes)
    with broker._transaction():
        return broker._save_artifact(envelope)


class PairedFeedbackBoundaries(unittest.TestCase):
    def test_schema2_timestamp_uses_the_retained_utc_string(self):
        with tempfile.TemporaryDirectory() as root, closing(paired.PairedFeedbackBroker(Path(root) / 'registry')) as broker:
            created = '2026-10-30T13:41:38Z'
            artifact = {'id': 'synthetic', 'creator': 'controller', 'origin': 'controller',
                'data_class': 'development', 'authority': 'synthetic_timestamp_test_only',
                'body': {'schema': 'formalization-record/2', 'created_at': created},
                'source_refs': [], 'exposure': []}
            expected = int(datetime(2026, 10, 30, 13, 41, 38, tzinfo=timezone.utc).timestamp())
            self.assertEqual(broker._artifact_availability(artifact), expected)

    def test_operator_only_reserved_sources_and_source_identity(self):
        with tempfile.TemporaryDirectory() as root, closing(paired.PairedFeedbackBroker(Path(root) / 'registry')) as broker:
            worker = broker.call(broker.admin_token, 'register_worker', name='fixture', role='discovery', capabilities=[])
            request = dict(root_epoch_id='root', execution_id='execution', composition_id='composition',
                meaning_review_assessment_id='review', target_epoch=2)
            with self.assertRaises(Denied):
                broker.publish_paired_feedback(worker['token'], **request)
            for schema in (paired.MANIFEST, paired.RELEASE):
                with self.subTest(schema=schema), self.assertRaises(REJECTIONS):
                    broker.call(broker.admin_token, 'add_source', body={'schema': schema}, data_class='development')
            with patch.object(paired, 'LOADED_SELF', '0' * 64), self.assertRaises(Invalid):
                broker._feedback_source_current()
            self.assertNotIn('trading_researcher/feedback/paired.py', feature_bundle())

    def test_unaffected_data_use_delegates_exactly(self):
        with tempfile.TemporaryDirectory() as root, closing(paired.PairedFeedbackBroker(Path(root) / 'registry')) as broker:
            retained = {'status': 'QUALIFIED', 'gaps': [], 'sentinel': 'exact legacy result'}
            with patch.object(PairedComputation, '_paired_data_use', return_value=retained) as original:
                dependencies = {'formalization': {'exposure': []}}
                self.assertIs(broker._paired_data_use(dependencies), retained)
                original.assert_called_once_with(dependencies)


class PairedMetadataBoundaries(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.broker = paired.PairedFeedbackBroker(Path(cls.temporary.name) / 'registry')
        cls.certificate = cls.broker.certify_paired(cls.broker.admin_token)
        if cls.certificate['body']['status'] != 'CERTIFIED':
            raise AssertionError('Actual isolated qualification failed')
        cls.package = cls.broker._artifact(cls.certificate['body']['source_package_id'])

    @classmethod
    def tearDownClass(cls):
        cls.broker.close()
        cls.temporary.cleanup()

    def test_actual_owned_metadata_is_technical_and_ancestry_is_not_removed(self):
        knowledge = paired.prior_knowledge(self.broker, self.certificate)
        expected = {self.certificate['id'], self.package['id']}
        self.assertEqual(set(knowledge['technical_provenance_ids']), expected)
        self.assertEqual(set(knowledge['artifact_ids']), expected)
        self.assertEqual(knowledge['operations_knowledge_ids'], [])
        arbitrary = self.broker.call(self.broker.admin_token, 'add_source',
            body={'fixture': 'uncontrolled operations'}, data_class='operations')
        protected = self.broker.call(self.broker.admin_token, 'add_source',
            body={'fixture': 'protected synthetic source'}, data_class='assessment')
        inherited = save_copy(self.broker, self.certificate,
            exposure=sorted([self.package['id'], arbitrary['id'], protected['id'], 'unresolved-fixture']))
        knowledge = paired.prior_knowledge(self.broker, inherited)
        self.assertIn(arbitrary['id'], knowledge['operations_knowledge_ids'])
        self.assertIn(protected['id'], knowledge['protected_knowledge_ids'])
        self.assertIn('unresolved-fixture', knowledge['unresolved_exposure_refs'])
        self.assertTrue({arbitrary['id'], protected['id']} <= set(knowledge['artifact_ids']))

    def test_wrong_package_or_certificate_profile_cannot_be_exempted(self):
        for artifact in (self.package, self.certificate):
            for key, value in (('profile', 'unapproved-profile/1'), ('schema', 'unknown-owned-type/1')):
                with self.subTest(schema=artifact['body']['schema'], key=key):
                    fake = save_copy(self.broker, artifact, body={**artifact['body'], key: value})
                    self.assertIn(fake['id'], paired.prior_knowledge(self.broker, fake)['operations_knowledge_ids'])
        fake = save_copy(self.broker, self.package,
            body={**self.package['body'], 'bootstrap_sha256': '0' * 64})
        self.assertIn(fake['id'], paired.prior_knowledge(self.broker, fake)['operations_knowledge_ids'])

    def test_malformed_metadata_is_typed_or_remains_operations(self):
        for artifact, key, values in ((self.package, 'files', (None, [], 'bad')),
                (self.certificate, 'result', (None, [], 'bad'))):
            for value in values:
                with self.subTest(schema=artifact['body']['schema'], key=key, value=value):
                    fake = save_copy(self.broker, artifact, body={**artifact['body'], key: value})
                    try:
                        result = paired.prior_knowledge(self.broker, fake)
                    except REJECTIONS:
                        continue
                    self.assertIn(fake['id'], result['operations_knowledge_ids'])

    def test_descendant_import_preserves_other_gaps_and_uncontrolled_ancestry(self):
        # The superclass assessment and current-grant check are explicit component
        # fixtures here. The retained-result lifecycle below exercises them intact.
        grant = self.broker.call(self.broker.admin_token, 'add_source',
            body={'schema': 'fixture-grant-holder/1'}, data_class='development')
        grant = save_copy(self.broker, grant, body={'schema': paired.RELEASE},
            creator='controller', origin='controller', authority=paired.AUTHORITY)
        target = save_copy(self.broker, self.certificate,
            body={'schema': 'fixture-descendant/1'}, data_class='development', authority='fixture_only',
            source_refs=[self.certificate['id']],
            exposure=sorted([grant['id'], self.certificate['id'], self.package['id']]), context_id='fixture-context')
        context = {'exposure': target['exposure']}
        original = {'status': 'DATA_USE_GAP', 'gaps': ['OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT',
            'PROVIDER_DOCUMENT_REVIEW_REQUIRED'], 'rights': {'reviewed_bytes_match': False},
            'scientific_readiness': False, 'prior_knowledge': {'fixture': True}}
        with patch.object(PairedComputation, '_paired_data_use', return_value=original), \
                patch.object(self.broker, '_context', return_value=context), \
                patch.object(self.broker, '_check_feedback_context') as checked:
            result = self.broker._paired_data_use({'formalization': target})
            checked.assert_called_once_with(context)
            self.assertEqual(result['gaps'], ['PROVIDER_DOCUMENT_REVIEW_REQUIRED'])
            self.assertEqual(result['status'], 'DATA_USE_GAP')
            self.assertEqual(result['rights'], original['rights'])
            self.assertFalse(result['scientific_readiness'])
            self.assertEqual(result['paired_feedback_import']['release_ids'], [grant['id']])
            operation = self.broker.call(self.broker.admin_token, 'add_source',
                body={'fixture': 'uncontrolled observation'}, data_class='operations')
            altered = save_copy(self.broker, target,
                exposure=sorted([*target['exposure'], operation['id']]))
            result = self.broker._paired_data_use({'formalization': altered})
            self.assertIn('OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT', result['gaps'])
            self.assertIn(operation['id'], result['prior_knowledge']['operations_knowledge_ids'])
        with patch.object(PairedComputation, '_paired_data_use', return_value=original), \
                patch.object(self.broker, '_context', return_value={'exposure': []}), \
                patch.object(self.broker, '_check_feedback_context') as checked, self.assertRaises(Invalid):
            self.broker._paired_data_use({'formalization': target})
        checked.assert_not_called()


class PairedAtomicPublicationBoundary(unittest.TestCase):
    def test_transaction_rollback_and_immutable_duplicate_release(self):
        # Explicit small evidence/closure fixtures isolate transaction behavior;
        # no claim that these metadata are a genuine execution is made.
        with tempfile.TemporaryDirectory() as root, closing(paired.PairedFeedbackBroker(Path(root) / 'registry')) as broker:
            inputs = [broker.call(broker.admin_token, 'add_source', body={'fixture': n},
                data_class='development') for n in range(3)]
            execution = deepcopy(inputs[0])
            execution['body'] = {'result': {'report': {'processed_case_count': 1},
                'contrast': {'status': 'INFORMATION_GAP', 'scientific_readiness': False},
                'case_blob': {'sha256': '0' * 64, 'size': 0}}}
            cohort = {'artifact_ids': sorted(x['id'] for x in inputs), 'unresolved_exposure_refs': [],
                'batches': [{'epoch': 1}], 'jobs': [], 'calls': []}
            request = {'root_epoch_id': 'fixture-root', 'execution_id': inputs[0]['id'],
                'composition_id': inputs[1]['id'], 'meaning_review_assessment_id': inputs[2]['id'], 'target_epoch': 2}
            def counts():
                return {table: broker._db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                    for table in ('artifacts', 'research_records', 'events', 'releases', 'contexts')}
            before = counts()
            with patch.object(paired, 'collect_cohort', return_value=cohort), \
                    patch.object(paired, '_evidence', return_value=(execution, {'fixture_only': True})):
                with patch.object(broker, '_event', side_effect=OSError('Synthetic final event interruption')), \
                        self.assertRaises(OSError):
                    broker.publish_paired_feedback(broker.admin_token, **request)
                self.assertEqual(counts(), before)
                result = broker.publish_paired_feedback(broker.admin_token, **request)
                after = counts()
                self.assertEqual(after['artifacts'] - before['artifacts'], 4)
                self.assertEqual(after['research_records'] - before['research_records'], 2)
                self.assertEqual(after['releases'], before['releases'])
                self.assertEqual(broker.publish_paired_feedback(broker.admin_token, **request), result)
                self.assertEqual(counts(), after)
                with self.assertRaises(Conflict):
                    broker.publish_paired_feedback(broker.admin_token, **{**request, 'target_epoch': 3})
                grant = broker._artifact(result['grant_id'])
                for epoch, when in ((1, broker._now()), (2, grant['body']['created_at'] - 1)):
                    with self.subTest(epoch=epoch, when=when), self.assertRaises(Denied):
                        paired._check_grant(broker, grant, epoch, when)
                for field, value in (('creator', 'forged'), ('authority', 'forged'), ('source_refs', [])):
                    fake = save_copy(broker, broker._artifact(result['observation_id']), **{field: value})
                    try:
                        access = paired.released_feedback(broker, fake, 2, broker._now())
                    except REJECTIONS:
                        continue
                    self.assertIsNone(access)
                defect = broker.call(broker.admin_token, 'add_source',
                    body={'fixture': 'Synthetic grant defect'}, data_class='development')
                revoked = broker.call(broker.admin_token, 'revoke_dependency', key='fixture-paired-grant',
                    dependency_id=result['grant_id'], reason='Synthetic direct grant revocation',
                    evidence_refs=[defect['id']])
                self.assertEqual(revoked['body']['status'], 'REVOKED')
                with self.assertRaises(Denied):
                    paired._check_grant(broker, grant, 2, broker._now())


@unittest.skipUnless(os.environ.get('TRF_PAIRED_FEEDBACK_SOURCE'),
    'Opt-in retained-result fixture requires an explicitly selected read-only source registry')
class PairedRetainedResultLifecycle(unittest.TestCase):
    def test_actual_evidence_publish_context_restore_and_revocation_on_private_clone(self):
        source = Path(os.environ['TRF_PAIRED_FEEDBACK_SOURCE']).resolve(strict=True)
        ledger = Path(os.environ['TRF_PAIRED_FEEDBACK_LEDGER']).resolve(strict=True)
        with closing(sqlite3.connect(ledger.as_uri() + '?mode=ro', uri=True)) as external:
            row = external.execute('SELECT binding,calls,revoked FROM research_epoch_budget_grants WHERE approval=?',
                (legacy_review.APPROVAL,)).fetchone()
        self.assertIsNotNone(row)
        closed_fence = {'binding': json.loads(row[0]), 'calls': json.loads(row[1]), 'revoked': bool(row[2])}
        self.assertTrue(closed_fence['revoked'])

        def simulated_closed_fence(host, epoch):
            # Sole explicit integration stub: permit the test's relocated DB to
            # inspect this already-closed D092 grant, without rewriting ledger,
            # registry identity or any retained model/evidence artifact. Every
            # non-location field and the full external call inventory must match.
            actual_binding = legacy_review.binding(host, epoch)
            actual_binding['registry_identity'] = digest(str(source))
            self.assertEqual(actual_binding, closed_fence['binding'])
            actual_calls = [value[0] for value in host._db.execute(
                'SELECT id FROM research_calls WHERE epoch_id=? ORDER BY rowid', (epoch['id'],))]
            self.assertEqual(actual_calls, [value['call_id'] for value in closed_fence['calls']])
            return deepcopy(closed_fence)

        execution_id = os.environ.get('TRF_PAIRED_FEEDBACK_EXECUTION',
            'e77f9f3f8966203d51cf676de394fa9b4bccf6cd4992e1654987ed3815221fb6')
        with tempfile.TemporaryDirectory(prefix='trf-paired-feedback-independent-') as temporary:
            root = Path(temporary).resolve()
            clone = root / 'clone'
            clone.mkdir()
            self.assertNotEqual(source, clone)
            # SQLite's read-only backup yields a coherent snapshot. Physical
            # copies, never hardlinks, isolate every later test mutation.
            with closing(sqlite3.connect((source / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as original, \
                    closing(sqlite3.connect(clone / 'registry.sqlite3')) as target:
                original.execute('PRAGMA query_only=ON')
                original.backup(target)
                source_counts = {table: original.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                    for table in ('artifacts', 'events', 'contexts', 'research_calls')}
            shutil.copytree(source / 'blobs', clone / 'blobs')
            shutil.copyfile(source / 'operator.key', clone / 'operator.key')
            print('Independent paired feedback: physical clone ready; no provider routes.', flush=True)
            with closing(paired.PairedFeedbackBroker(clone)) as broker:
                execution = broker._artifact(execution_id)
                compiled = broker._artifact(execution['body']['compiled_id'])
                certificate_id = compiled['body']['reference_certificate_id']
                broker._paired_certificate_id = certificate_id
                formalization = broker._artifact(compiled['body']['formalization_id'])
                idea = broker._artifact(formalization['body']['idea_id'])
                root_epoch = broker._job(idea['job_id'])['spec']['research_epoch_id']
                evidence = [broker._artifact(ref) for ref in execution['source_refs']]
                composition = [x for x in evidence if x['body'].get('schema') == 'paired-composition-certificate/1']
                meaning = [x for x in evidence if x['body'].get('schema') == 'semantic-review-assessment/1']
                self.assertEqual(len(composition), 1)
                self.assertEqual(len(meaning), 1)
                cohort = paired.collect_cohort(broker, root_epoch)
                target_epoch = max(batch['epoch'] for batch in cohort['batches']) + 1
                request = dict(root_epoch_id=root_epoch, execution_id=execution_id,
                    composition_id=composition[0]['id'], meaning_review_assessment_id=meaning[0]['id'],
                    target_epoch=target_epoch)
                jobs_before = [tuple(row) for row in broker._db.execute('SELECT * FROM jobs ORDER BY id')]
                call_count = broker._db.execute('SELECT COUNT(*) FROM research_calls').fetchone()[0]
                generic_releases = broker._db.execute('SELECT COUNT(*) FROM releases').fetchone()[0]
                old_feedback = {row[0]: row[1] for row in broker._db.execute("SELECT id,envelope FROM artifacts WHERE json_extract(envelope,'$.body.schema') IN ('development-feedback-manifest/1','development-feedback-release/1')")}
                started = time.monotonic()
                published = broker.publish_paired_feedback(broker.admin_token, **request)
                print('Independent paired feedback: genuine publication and current evidence passed in %.3fs.' % (time.monotonic() - started), flush=True)
                saved = {key: broker._artifact(identity) for key, identity in published.items()}
                manifest = saved['manifest_id']
                self.assertEqual(manifest['body']['cohort'], cohort)
                self.assertEqual(manifest['body']['request'], request)
                self.assertEqual(manifest['body']['publisher_sha256'], paired.LOADED_SELF)
                retained = []
                for identity in cohort['artifact_ids']:
                    item = broker._artifact(identity)
                    if isinstance(item['body'], dict) and item['body'].get('schema') == 'research-record/1' and item['body'].get('kind') in ('idea', 'gap'):
                        retained.append({key: item[key] for key in ('id', 'creator', 'authority', 'body', 'source_refs', 'exposure')})
                self.assertEqual(manifest['body']['retained_research_records'], retained)
                self.assertIn(idea['id'], {item['id'] for item in retained})
                self.assertTrue(any(item['body']['kind'] == 'gap' for item in retained))
                for artifact in saved.values():
                    self.assertTrue(set(cohort['artifact_ids']) <= set(artifact['exposure']))
                    self.assertEqual(artifact['authority'], paired.AUTHORITY)
                self.assertFalse(manifest['body']['scientific_readiness'])
                self.assertEqual(broker.publish_paired_feedback(broker.admin_token, **request), published)
                with self.assertRaises(Conflict):
                    broker.publish_paired_feedback(broker.admin_token, **{**request, 'target_epoch': target_epoch + 1})
                self.assertEqual([tuple(row) for row in broker._db.execute('SELECT * FROM jobs ORDER BY id')], jobs_before)
                self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM research_calls').fetchone()[0], call_count)
                self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM releases').fetchone()[0], generic_releases)
                self.assertEqual({identity: canonical({key: value for key, value in broker._artifact(identity).items() if key != 'id'}) for identity in old_feedback}, old_feedback)
                journal = broker.call(broker.admin_token, 'inspect_memory', view='journal', scope={'manifest_id': manifest['id']})['records']
                self.assertEqual({x['id'] for x in journal}, {published['observation_id'], published['experience_id']})
                with self.assertRaisesRegex(Invalid, 'current qualified data use and independent meaning review'):
                    broker.call(broker.admin_token, 'create_context', role='discovery', epoch=target_epoch,
                        artifact_ids=[manifest['id']])
                fence_simulation = patch.object(legacy_review, 'inspect', side_effect=simulated_closed_fence)
                fence_simulation.start()
                self.addCleanup(fence_simulation.stop)
                print('Independent paired feedback: relocation denied; sole D092 closed-fence simulation begins.', flush=True)
                context = broker.call(broker.admin_token, 'create_context', role='discovery', epoch=target_epoch,
                    artifact_ids=[manifest['id']])
                self.assertEqual(context['artifact_ids'], [manifest['id']])
                self.assertIn(published['grant_id'], context['exposure'])
                token = broker.call(broker.admin_token, 'register_worker', name='paired-feedback-fixture-reader',
                    role='discovery', capabilities=['draft/v1'])['token']
                broker.call(broker.admin_token, 'enqueue', key='paired-feedback-fixture-reader', spec={
                    'kind': 'draft/v1', 'context_id': context['id'], 'purpose': 'Independent clone feedback access test',
                    'allowed_workers': ['paired-feedback-fixture-reader'], 'max_attempts': 1,
                    'lease_seconds': 3600, 'deadline': broker._now() + 7200, 'dependencies': []})
                lease = broker.call(token, 'claim')['lease']
                actual = broker.call(token, 'read_artifact', lease=lease, artifact_id=manifest['id'])
                self.assertEqual(actual, manifest)
                with self.assertRaises(Denied):
                    broker.call(token, 'read_artifact', lease=lease, artifact_id=execution_id)
                backup = root / 'backup'
                broker.call(broker.admin_token, 'backup_bundle', destination=str(backup))
                print('Independent paired feedback: exact manifest access and isolated backup passed.', flush=True)
            # The default broker must not silently acquire the optional grant.
            with closing(Broker(clone)) as default:
                with self.assertRaises(Denied):
                    default.call(default.admin_token, 'create_context', role='discovery', epoch=target_epoch,
                        artifact_ids=[published['manifest_id']])
            restored = root / 'restored'
            restore_bundle(backup, restored, clone / 'operator.key')
            with closing(paired.PairedFeedbackBroker(restored, paired_certificate_id=certificate_id)) as other:
                for key, artifact in saved.items():
                    self.assertEqual(other._artifact(published[key]), artifact)
                restored_context = other.call(other.admin_token, 'create_context', role='discovery',
                    epoch=target_epoch, artifact_ids=[published['experience_id']])
                self.assertIn(published['grant_id'], restored_context['exposure'])
                defect = other.call(other.admin_token, 'add_source', body={'fixture': 'Synthetic technical revocation evidence'},
                    data_class='development')
                other.call(other.admin_token, 'revoke_dependency', key='paired-feedback-fixture-revocation',
                    dependency_id=published['grant_id'], reason='Synthetic isolated publication revocation test',
                    evidence_refs=[defect['id']])
                with self.assertRaises(Denied):
                    other._check_feedback_context(restored_context)
                with self.assertRaises(Denied):
                    other.call(other.admin_token, 'create_context', role='discovery', epoch=target_epoch,
                        artifact_ids=[published['observation_id']])
                self.assertEqual(other._artifact(execution_id), execution)
            with closing(sqlite3.connect((source / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as original:
                after = {table: original.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                    for table in source_counts}
                self.assertEqual(after, source_counts)
            print('Independent paired feedback: restore, revocation and unchanged source counts passed.', flush=True)


if __name__ == '__main__':
    unittest.main()
