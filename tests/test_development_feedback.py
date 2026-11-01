"""Independent failure-preserving development cohort checks; no live provider calls."""
from copy import deepcopy
import unittest

from trading_researcher.codec import Invalid, canonical
from trading_researcher.errors import Conflict, Denied
import test_research_calls as call_tests


REJECTIONS = (Invalid, Denied, Conflict)


class DevelopmentFeedbackCohortTests(unittest.TestCase):
    def setUp(self, retain_intermediate=False):
        self.fixture = call_tests.ResearchCallTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.broker = self.fixture.broker
        self.epoch, first_lease = self.fixture.setup_epoch(max_calls=4)
        self.root_results, self.call_ids = [], []
        for name in ('first', 'second'):
            lease = first_lease if name == 'first' else self.broker.call(self.fixture.tokens[name], 'claim')['lease']
            call = self.fixture.reserve(lease, name=name)
            self.call_ids.append(call['call_id'])
            self.fixture.finish(lease, call['call_id'], name=name,
                usage={'input_tokens': 10, 'output_tokens': 20, 'cost_units': 0})
            if retain_intermediate and name == 'first':
                self.earlier_idea = self.broker.call(self.fixture.tokens[name], 'record_research', lease=lease,
                    kind='idea', content={'text': 'Earlier distinct idea retained before the final result'},
                    scope={}, source_refs=[])['id']
            content = {'text': 'Unrestricted first idea'} if name == 'first' else {
                'text': 'Second perspective retained an explicit gap', 'reason': 'Synthetic unsupported requirement',
                'reopen_condition': 'Do not silently substitute a different idea'}
            artifact = self.broker.call(self.fixture.tokens[name], 'record_research', lease=lease,
                kind='idea' if name == 'first' else 'gap', content=content, scope={}, source_refs=[])
            self.root_results.append(artifact['id'])
            outcome = self.broker.call(self.fixture.tokens[name], 'submit', lease=lease, artifact_id=artifact['id'])
            self.assertTrue(outcome['accepted'])
        self.root_jobs = [row['id'] for row in self.broker._db.execute('SELECT id FROM jobs ORDER BY id')]
        self.batch = self.broker._job(self.root_jobs[0])['batch_id']
        self.fixture.now = 1061

    def collect(self):
        from trading_researcher.development_feedback import collect_cohort
        return collect_cohort(self.broker, self.epoch)

    def job_states(self):
        return [dict(row) for row in self.broker._db.execute('SELECT * FROM jobs ORDER BY id')]

    def auxiliary_job(self, name, epoch, context, inputs, kind='formalization/v1'):
        token = self.fixture.op('register_worker', name=name, role='formalizer', capabilities=[kind])['token']
        profile = {'model': 'fixture/1', 'prompt_version': 'feedback-fixture/1',
            'prompt': 'Preserve the exact idea and report unsupported requirements.',
            'generation_parameters': {}, 'max_output_tokens': 64, 'call_timeout_seconds': 5, 'max_retries': 0}
        job = self.fixture.op('enqueue', key=name, spec={
            'kind': kind, 'context_id': context, 'purpose': 'Independent feedback closure fixture',
            'allowed_workers': [name], 'max_attempts': 1, 'lease_seconds': 10, 'deadline': 1200,
            'dependencies': [], 'research_epoch_id': epoch, 'research_call_profile': profile,
            'research_inputs': inputs})['id']
        lease = self.broker.call(token, 'claim')['lease']
        return token, job, lease

    def linked_formalizer(self, name='related-formalizer', idea_id=None):
        idea_id = self.root_results[0] if idea_id is None else idea_id
        self.fixture.op('release_batch', batch_id=self.batch, target_epoch=2)
        catalog = self.fixture.op('add_source', body={'schema': 'feature-catalog/1', 'features': {}},
            data_class='development')['id']
        context = self.fixture.op('create_context', role='formalizer', epoch=2,
            artifact_ids=[idea_id, catalog])['id']
        epoch = self.fixture.op('create_research_epoch', key=name, context_id=self.fixture.context,
            workers=['first', 'second'], profile={**self.fixture.profile, 'max_calls': 4, 'max_tokens': 80000})['id']
        token, job, lease = self.auxiliary_job(name, epoch, context,
            {'idea_id': idea_id, 'catalog_id': catalog, 'definition_ids': []})
        return epoch, catalog, token, job, lease

    def retain_gap_and_block(self, token, lease):
        gap = self.broker.call(token, 'record_research', lease=lease, kind='gap',
            content={'text': 'The exact original idea remains unsupported.',
                'reason': 'The exact frozen semantics have no supported representation.',
                'reopen_condition': 'A separately authorized supported continuation exists'},
            scope={}, source_refs=[])['id']
        self.broker.call(token, 'block', lease=lease, reason='Exact formalization unavailable',
            needs=['Existing original meaning support'], retry_when='A separately authorized supported continuation exists')
        return gap

    def test_complete_two_perspectives_include_gap_calls_and_typed_history(self):
        before = self.job_states()
        result = self.collect()
        self.assertEqual(result['root_epoch_id'], self.epoch)
        self.assertEqual(set(result['root_result_ids']), set(self.root_results))
        self.assertEqual(result['idea_ids'], [self.root_results[0]])
        self.assertEqual(result['epoch_ids'], [self.epoch])
        self.assertEqual(set(result['job_ids']), set(self.root_jobs))
        self.assertEqual(result['batch_ids'], [self.batch])
        self.assertEqual({job['id'] for job in result['jobs']}, set(self.root_jobs))
        self.assertEqual({job['state'] for job in result['jobs']}, {'completed'})
        self.assertEqual({call['id'] for call in result['calls']}, set(self.call_ids))
        self.assertEqual({call['state'] for call in result['calls']}, {'recorded'})
        self.assertEqual(result['bound_attempts'], [])
        self.assertTrue(set(self.root_results) <= set(result['artifact_ids']))
        for call in result['calls']:
            self.assertIn(call['request_id'], result['artifact_ids'])
            self.assertIn(call['response_id'], result['artifact_ids'])
        history = [row['artifact_id'] for row in self.broker._db.execute('SELECT artifact_id FROM research_records')]
        self.assertTrue(set(history) <= set(result['artifact_ids']))
        self.assertEqual(self.job_states(), before)
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM releases').fetchone()[0], 0)

    def test_unrelated_epoch_is_not_swept_in_by_shared_context(self):
        unrelated = self.fixture.op('create_research_epoch', key='unrelated', context_id=self.fixture.context,
            workers=['first', 'second'], profile=self.fixture.profile)['id']
        self.assertNotEqual(unrelated, self.epoch)
        result = self.collect()
        self.assertEqual(result['epoch_ids'], [self.epoch])
        self.assertNotIn(unrelated, canonical(result))

    def test_related_exhausted_blocked_formalization_is_retained_without_completion(self):
        epoch, catalog, token, job, lease = self.linked_formalizer()
        gap = self.retain_gap_and_block(token, lease)
        self.fixture.now = 1122
        before = self.job_states()
        result = self.collect()
        self.assertEqual(set(result['epoch_ids']), {self.epoch, epoch})
        self.assertIn(job, result['job_ids'])
        self.assertIn(self.broker._job(job)['batch_id'], result['batch_ids'])
        self.assertIn(gap, result['artifact_ids'])
        self.assertIn(catalog, result['artifact_ids'])
        self.assertEqual(next(value for value in result['jobs'] if value['id'] == job)['state'], 'blocked')
        self.assertEqual(self.job_states(), before)
        with self.assertRaises(Conflict):
            self.fixture.op('release_batch', batch_id=self.broker._job(job)['batch_id'], target_epoch=3)

    def test_earlier_retained_idea_links_its_later_auxiliary_epoch(self):
        case = DevelopmentFeedbackCohortTests()
        case.setUp(retain_intermediate=True)
        self.addCleanup(case.doCleanups)
        epoch, catalog, token, job, lease = case.linked_formalizer(idea_id=case.earlier_idea)
        gap = case.retain_gap_and_block(token, lease)
        case.fixture.now = 1122
        result = case.collect()
        self.assertEqual(set(result['root_result_ids']), set(case.root_results))
        self.assertEqual(set(result['idea_ids']), {case.root_results[0], case.earlier_idea})
        self.assertIn(epoch, result['epoch_ids'])
        self.assertIn(job, result['job_ids'])
        self.assertTrue({catalog, gap, case.earlier_idea} <= set(result['artifact_ids']))
        self.assertEqual(next(value for value in result['jobs'] if value['id'] == job)['state'], 'blocked')

    def test_review_target_closes_over_retained_null_candidate_and_failed_review(self):
        epoch, catalog, token, job, lease = self.linked_formalizer()
        packet = self.broker.call(token, 'auxiliary_input', lease=lease)
        profile = self.broker._job(job)['spec']['research_call_profile']
        request = {key: profile[key] for key in ('model', 'prompt_version', 'generation_parameters')}
        request.update(tools=[], messages=[{'role': 'system', 'content': profile['prompt']},
            {'role': 'user', 'content': canonical(packet)}])
        call = self.broker.call(token, 'reserve_research_call', lease=lease, key='null-candidate',
            request=request, input_token_bound=16000, output_token_limit=64, cost_bound_units=0)
        self.broker.call(token, 'finish_research_call', lease=lease, call_id=call['call_id'],
            response={'status': 'completed', 'output': {'status': 'final', 'candidate': None, 'semantic_report': None}},
            usage={'input_tokens': 10, 'output_tokens': 20, 'cost_units': 0})
        formalization = self.broker.call(token, 'record_formalization', lease=lease,
            idea_id=self.root_results[0], catalog_id=catalog, candidate=None, semantic_report=None,
            provider_call_id=call['call_id'])['id']
        self.assertTrue(self.broker.call(token, 'submit', lease=lease, artifact_id=formalization)['accepted'])
        self.fixture.op('release_batch', batch_id=self.broker._job(job)['batch_id'], target_epoch=3)
        review_context = self.fixture.op('create_context', role='formalizer', epoch=3,
            artifact_ids=[formalization, catalog])['id']
        review_token, review_job, review_lease = self.auxiliary_job('separate-reviewer', epoch, review_context,
            {'formalization_id': formalization, 'definition_ids': []}, kind='semantic-review/v1')
        review_gap = self.retain_gap_and_block(review_token, review_lease)
        self.fixture.now = 1122
        result = self.collect()
        self.assertTrue({job, review_job} <= set(result['job_ids']))
        self.assertTrue({formalization, review_gap} <= set(result['artifact_ids']))
        self.assertIn(call['call_id'], {value['id'] for value in result['calls']})
        self.assertEqual(self.broker._artifact(formalization)['body']['candidate'], None)
        self.assertEqual(next(value for value in result['jobs'] if value['id'] == review_job)['state'], 'blocked')

    def test_open_epoch_cannot_publish_its_current_partial_inventory(self):
        self.fixture.now = 1000
        with self.assertRaises(REJECTIONS):
            self.collect()

    def test_unsealed_or_ready_running_resumable_jobs_are_rejected_without_relabeling(self):
        self.broker._db.execute('UPDATE batches SET sealed=0 WHERE id=?', (self.batch,))
        with self.assertRaises(REJECTIONS):
            self.collect()
        self.broker._db.execute('UPDATE batches SET sealed=1 WHERE id=?', (self.batch,))
        for state in ('ready', 'running', 'blocked'):
            self.broker._db.execute('UPDATE jobs SET state=? WHERE id=?', (state, self.root_jobs[0]))
            before = self.job_states()
            with self.subTest(state=state), self.assertRaises(REJECTIONS):
                self.collect()
            self.assertEqual(self.job_states(), before)

    def test_unsettled_call_blocks_even_after_epoch_expiration(self):
        self.broker._db.execute("UPDATE research_calls SET state='reserved',response_id=NULL WHERE id=?", (self.call_ids[0],))
        with self.assertRaises(REJECTIONS):
            self.collect()

    def test_started_related_computation_blocks_metadata_publication(self):
        self.broker._bound_start('compile', self.root_results[0])
        with self.assertRaises(REJECTIONS):
            self.collect()

    def test_protected_and_operational_ancestry_cannot_be_imported_as_development(self):
        for data_class in ('assessment', 'operations'):
            source = self.fixture.op('add_source', body={'schema': 'synthetic-observation/1'}, data_class=data_class)
            original = self.broker._artifact
            def artifact(identity):
                value = original(identity)
                if identity == self.root_results[0]:
                    value['exposure'] = [*value['exposure'], source['id']]
                return value
            from unittest.mock import patch
            with self.subTest(data_class=data_class), patch.object(self.broker, '_artifact', artifact), self.assertRaises(REJECTIONS):
                self.collect()


if __name__ == '__main__':
    unittest.main()
