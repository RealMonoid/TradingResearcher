"""Independent temporary-metadata/release seams; no provider/production state.

Owned packages and one paired runtime certificate are genuine. Publication's
upstream closed-cohort/numeric evidence and the final numeric data-use findings
are explicit component fixtures; real native records, contexts, release checks,
classifiers, source identities and typed revocation run unchanged. This does
not qualify a scientific publication or a complete inherited-feedback study.
"""
from contextlib import contextmanager, ExitStack
from copy import deepcopy
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.data_use import prior_knowledge as generic_knowledge
from trading_researcher.errors import Conflict, Denied
from trading_researcher.exact_execution import ExactExecutionBroker
import trading_researcher.exact_feedback as adapter
from trading_researcher.feedback import paired, breakout
from trading_researcher.paired_computation import PairedComputation
from trading_researcher.paired_breakout import runtime as breakout_runtime


REJECTIONS = (Invalid, Conflict, Denied)


class ExactFeedbackReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.broker = adapter.ExactFeedbackBroker(Path(cls.temporary.name) / 'registry')
        cls.addClassCleanup(cls.broker.close)
        cls.certificate = cls.broker.certify_paired(cls.broker.admin_token)
        if cls.certificate['body']['status'] != 'CERTIFIED':
            raise AssertionError(cls.certificate['body']['error'])
        cls.paired_package = cls.broker._artifact(cls.certificate['body']['source_package_id'])
        cls.breakout_package = cls.broker._breakout_retain_package(breakout_runtime.read_bundle())
        cls.technical = {cls.certificate['id'], cls.paired_package['id'], cls.breakout_package['id']}
        cls.clean = sqlite3.connect(':memory:')
        cls.addClassCleanup(cls.clean.close)
        cls.broker._db.backup(cls.clean)

    def setUp(self):
        self.clean.backup(self.broker._db)

    def tearDown(self):
        # Only this provider-free disposable registry is isolated. There is no
        # shared spending ledger, research grant, epoch or paid call to reset.
        self.clean.backup(self.broker._db)

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def injected(self, original, **changes):
        item = deepcopy(original); item.pop('id'); item.update(changes)
        with self.broker._transaction(): return self.broker._save_artifact(item)

    @contextmanager
    def publication_fixture(self, families=('paired', 'breakout')):
        refs = sorted(self.technical)
        cohort = {'artifact_ids': refs, 'unresolved_exposure_refs': [],
                  'batches': [{'epoch': 1}], 'jobs': [], 'calls': []}
        execution = deepcopy(self.certificate)
        execution['body'] = {'result': {'report': {'processed_case_count': 2},
            'contrast': {'status': 'DESCRIPTIVE_ONLY', 'condition_count': 1, 'scope_count': 2,
                         'scientific_readiness': False}, 'case_blob': {'sha256': '0' * 64, 'size': 0}}}
        releases = {}
        with ExitStack() as stack:
            for owner in (paired, breakout):
                stack.enter_context(patch.object(owner, 'collect_cohort', return_value=cohort))
                stack.enter_context(patch.object(owner, '_evidence', return_value=(execution, {'explicit_numeric_fixture': True})))
            for family in families:
                method = self.broker.publish_paired_feedback if family == 'paired' else self.broker.publish_breakout_feedback
                releases[family] = method(self.broker.admin_token, root_epoch_id='metadata-' + family,
                    execution_id=self.certificate['id'], composition_id=self.breakout_package['id'],
                    meaning_review_assessment_id=self.paired_package['id'], target_epoch=2)
            yield releases

    def target(self, releases=(), extras=()):
        inherited = sorted({*self.technical, *extras, *(entry['grant_id'] for entry in releases)})
        holder = self.op('add_source', body={'fixture': 'retained complete descendant'},
                         data_class='development', exposure=inherited)
        context = self.op('create_context', role='formalizer', epoch=2, artifact_ids=[holder['id']])
        with self.broker._transaction():
            return self.broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
                'data_class': 'development', 'authority': 'explicit_metadata_fixture_not_formalization',
                'context_id': context['id'], 'source_refs': [holder['id']],
                'exposure': sorted({holder['id'], *context['exposure']}), 'body': {'schema': 'metadata-descendant-fixture/1'}})

    @contextmanager
    def numeric_findings(self, target, extra_gaps=()):
        original = {'schema': 'paired-data-use-assessment/1', 'status': 'DATA_USE_GAP',
            'gaps': ['OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT', *extra_gaps],
            'rights': {'reviewed_bytes_match': False, 'scope': 'unmodified fixture rights'},
            'prior_knowledge': generic_knowledge(self.broker, target),
            'availability': {'basis': 'assumed', 'delay_seconds': 900},
            'independent_confirmation': False, 'model_training_exposure': 'UNKNOWN', 'scientific_readiness': False}
        with patch.object(PairedComputation, '_paired_data_use', side_effect=lambda *args: deepcopy(original)):
            yield original

    def test_existing_exact_and_new_multiple_inheritance_routes_remain_distinct(self):
        mro = adapter.ExactFeedbackBroker.__mro__
        self.assertLess(mro.index(breakout.BreakoutFeedbackBroker), mro.index(paired.PairedFeedbackBroker))
        self.assertFalse(issubclass(ExactExecutionBroker, breakout.BreakoutFeedbackBroker))
        target = self.target()
        with self.numeric_findings(target) as original:
            legacy = ExactExecutionBroker._exact_data_use(self.broker, {'formalization': target})
            current = self.broker._exact_data_use({'formalization': target})
        self.assertEqual(legacy['schema'], 'exact-development-data-use/1')
        self.assertEqual(current['schema'], 'exact-development-data-use/2')
        self.assertEqual(legacy['gaps'], original['gaps'])
        self.assertEqual(current['gaps'], original['gaps'])
        self.assertNotIn('paired_feedback_import', current)
        self.assertNotIn('paired_breakout_feedback_import', current)

    def test_genuine_owned_technical_metadata_is_not_removed_from_ancestry(self):
        target = self.target()
        generic = generic_knowledge(self.broker, target)
        controlled = breakout.prior_knowledge(self.broker, target)
        self.assertEqual(set(generic['operations_knowledge_ids']), self.technical)
        self.assertEqual(set(controlled['technical_provenance_ids']), self.technical)
        self.assertEqual(controlled['operations_knowledge_ids'], [])
        self.assertEqual(controlled['artifact_ids'], generic['artifact_ids'])
        self.assertEqual(controlled['protected_knowledge_ids'], generic['protected_knowledge_ids'])
        self.assertEqual(controlled['unresolved_exposure_refs'], generic['unresolved_exposure_refs'])

    def test_both_real_import_chains_preserve_nonoperations_gaps_and_full_context(self):
        with self.publication_fixture() as releases:
            target = self.target(releases.values())
            before = canonical(target)
            gaps = ['PROVIDER_DOCUMENT_REVIEW_REQUIRED', 'PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY',
                    'UNRESOLVED_CANDIDATE_EXPOSURE']
            with self.numeric_findings(target, gaps) as original:
                current = self.broker._exact_data_use({'formalization': target})
            self.assertEqual(current['gaps'], gaps)
            self.assertEqual(current['status'], 'DATA_USE_GAP')
            for key in ('rights', 'availability', 'independent_confirmation', 'model_training_exposure', 'scientific_readiness'):
                self.assertEqual(canonical(current[key]), canonical(original[key]))
            self.assertEqual(current['prior_knowledge']['artifact_ids'], original['prior_knowledge']['artifact_ids'])
            self.assertEqual(current['prior_knowledge']['operations_knowledge_ids'], [])
            self.assertEqual(current['paired_feedback_import']['release_ids'], [releases['paired']['grant_id']])
            self.assertEqual(current['paired_breakout_feedback_import']['release_ids'], [releases['breakout']['grant_id']])
            self.assertEqual(current['controlled_feedback']['context_id'], target['context_id'])
            self.assertEqual(current['controlled_feedback']['installed_sources'], self.broker._execution_sources())
            self.assertIs(current['controlled_feedback']['scientific_readiness'], False)
            self.assertEqual(canonical(target), before)

    def test_unrelated_operations_protected_and_unresolved_ancestry_are_retained(self):
        arbitrary = self.op('add_source', body={'uncontrolled': 'operational observation'}, data_class='operations')
        protected = self.op('add_source', body={'fixture': 'protected assessment'}, data_class='assessment')
        with self.publication_fixture() as releases:
            target = self.target(releases.values(), [arbitrary['id'], protected['id'], 'opaque-unresolved-annotation'])
            with self.numeric_findings(target, ['PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY']) as original:
                current = self.broker._exact_data_use({'formalization': target})
            knowledge = current['prior_knowledge']
            self.assertIn('OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT', current['gaps'])
            self.assertIn('PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY', current['gaps'])
            self.assertIn(arbitrary['id'], knowledge['operations_knowledge_ids'])
            self.assertIn(protected['id'], knowledge['protected_knowledge_ids'])
            self.assertEqual(knowledge['unresolved_exposure_refs'], ['opaque-unresolved-annotation'])
            self.assertEqual(knowledge['artifact_ids'], original['prior_knowledge']['artifact_ids'])
            self.assertTrue(self.technical <= set(knowledge['technical_provenance_ids']))

    def test_paired_release_does_not_exempt_unrecognized_second_family_metadata(self):
        with self.publication_fixture(('paired',)) as releases:
            target = self.target(releases.values())
            with self.numeric_findings(target): current = self.broker._exact_data_use({'formalization': target})
            self.assertIn(self.breakout_package['id'], current['prior_knowledge']['operations_knowledge_ids'])
            self.assertIn('OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT', current['gaps'])
            self.assertNotIn('paired_breakout_feedback_import', current)

    def test_invalid_or_lookalike_packages_stay_operations(self):
        for change in ({'creator': 'operator'}, {'origin': 'source'}, {'authority': 'wrong'}, {'blob_refs': []}):
            fake = self.injected(self.breakout_package, **change)
            self.assertIn(fake['id'], breakout.prior_knowledge(self.broker, fake)['operations_knowledge_ids'])
        body = deepcopy(self.breakout_package['body']); body['profile'] = 'unknown/1'
        fake = self.injected(self.breakout_package, body=body)
        self.assertIn(fake['id'], breakout.prior_knowledge(self.broker, fake)['operations_knowledge_ids'])

    def test_release_context_failure_precedes_upstream_numeric_findings(self):
        with self.publication_fixture() as releases:
            target = self.target(releases.values())
            context = self.broker._context(target['context_id'])
            for changes in ({'epoch': 1}, {'research_time': 0}):
                value = {key: deepcopy(item) for key, item in context.items() if key != 'id'}; value.update(changes)
                identity = digest(value)
                self.broker._db.execute('INSERT OR IGNORE INTO contexts VALUES(?,?)', (identity, canonical(value)))
                late = self.injected(target, context_id=identity)
                with self.subTest(changes=changes), patch.object(PairedComputation, '_paired_data_use',
                        side_effect=AssertionError('numeric findings reached')) as numeric, self.assertRaises(REJECTIONS):
                    self.broker._exact_data_use({'formalization': late})
                numeric.assert_not_called()

    def test_every_inherited_release_must_be_in_the_authorized_context(self):
        with self.publication_fixture() as releases:
            early = self.target([releases['paired']])
            late = self.injected(early, exposure=sorted({*early['exposure'], releases['breakout']['grant_id']}))
            with self.numeric_findings(late), self.assertRaises(Invalid):
                self.broker._exact_data_use({'formalization': late})

    def test_revoked_release_or_manifest_denies_old_context_before_numeric_work(self):
        with self.publication_fixture() as releases:
            target = self.target(releases.values())
            defect = self.op('add_source', body={'synthetic_defect': 'owner revocation'}, data_class='development')
            revoked = self.op('revoke_dependency', key='second-owner-defect',
                dependency_id=releases['breakout']['manifest_id'], reason='Controlled metadata revocation.',
                evidence_refs=[defect['id']])
            self.assertEqual(revoked['body']['status'], 'REVOKED')
            self.assertIn(releases['breakout']['grant_id'], revoked['body']['affected_artifact_ids'])
            with patch.object(PairedComputation, '_paired_data_use', side_effect=AssertionError('numeric work reached')) as numeric, \
                    self.assertRaises(Denied): self.broker._exact_data_use({'formalization': target})
            numeric.assert_not_called()

    def test_malformed_release_is_not_a_controlled_import(self):
        with self.publication_fixture() as releases:
            target = self.target(releases.values())
            original = self.broker._artifact(releases['breakout']['grant_id'])
            body = deepcopy(original['body']); body.pop('target_epoch')
            invalid = self.injected(original, body=body)
            context = self.broker._context(target['context_id'])
            value = {key: deepcopy(item) for key, item in context.items() if key != 'id'}
            value['exposure'] = sorted({*value['exposure'], invalid['id']}); identity = digest(value)
            self.broker._db.execute('INSERT OR IGNORE INTO contexts VALUES(?,?)', (identity, canonical(value)))
            corrupted = self.injected(target, context_id=identity, exposure=sorted({*target['exposure'], invalid['id']}))
            with patch.object(PairedComputation, '_paired_data_use', side_effect=AssertionError('numeric work reached')) as numeric, \
                    self.assertRaises(REJECTIONS): self.broker._exact_data_use({'formalization': corrupted})
            numeric.assert_not_called()

    def test_source_drift_fences_runtime_identity_and_data_use_without_refresh(self):
        target = self.target(); before = canonical(adapter.LOADED)
        for getter in (self.broker._execution_sources, self.broker._exact_source_identity):
            self.assertTrue(set(adapter.FILES) <= set(getter()))
        with patch.dict(adapter.LOADED, {adapter.FILES[0]: '0' * 64}):
            for getter in (self.broker._execution_sources, self.broker._exact_source_identity):
                with self.assertRaises(Invalid): getter()
            with patch.object(self.broker, '_context', side_effect=AssertionError('context read before source check')) as context, \
                    self.assertRaises(Invalid): self.broker._exact_data_use({'formalization': target})
            context.assert_not_called()
        self.assertEqual(canonical(adapter.LOADED), before)


if __name__ == '__main__':
    unittest.main()
