"""Independent lossless idea storage checks; synthetic text, no provider calls.

Only idea content.text may grow. Authentication, release, immutable records,
formalization gap retention and backup restoration use the real local Broker.
"""
from pathlib import Path
import json
import tempfile
import unittest

from trading_researcher.codec import Invalid, MAX_BYTES, canonical
from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied
from trading_researcher.storage import restore_bundle


def idea_text(length):
    prefix, suffix = '  Original synthetic idea: α🙂\n', '\nExact ending.  '
    return prefix + 'x' * (length - len(prefix) - len(suffix)) + suffix


class LongIdeaTextAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.broker = Broker(self.root / 'registry', clock=lambda: 1000)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.broker.close)
        self.worker = self.op('register_worker', name='discovery', role='discovery',
            capabilities=['research-record/v1'])['token']
        self.context = self.op('create_context', role='discovery', epoch=1, artifact_ids=[])['id']
        self.batch = self.op('create_batch', key='discovery-batch', epoch=1)['id']
        self.job = self.op('enqueue', key='discovery-job', spec={
            'kind': 'research-record/v1', 'context_id': self.context, 'purpose': 'Synthetic lossless storage test.',
            'allowed_workers': ['discovery'], 'max_attempts': 1, 'lease_seconds': 60,
            'deadline': 2000, 'dependencies': [], 'batch_id': self.batch})['id']
        self.op('seal_batch', batch_id=self.batch)
        self.lease = self.broker.call(self.worker, 'claim')['lease']

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def record(self, value, **changes):
        args = {'lease': self.lease, 'kind': 'idea', 'content': {'text': value}, 'scope': {}, 'source_refs': []}
        return self.broker.call(self.worker, 'record_research', **{**args, **changes})

    def counts(self):
        return {table: self.broker._db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
            for table in ('artifacts', 'research_records', 'events', 'releases')}

    def raw(self, identity):
        return self.broker._db.execute('SELECT envelope FROM artifacts WHERE id=?', (identity,)).fetchone()[0]

    def test_long_worker_idea_survives_submission_formalization_and_restore_exactly(self):
        original = idea_text(8255)
        saved = self.record(original)
        identity = saved['id']
        saved = self.op('get_artifact', artifact_id=identity)
        raw = self.raw(identity)
        self.assertEqual(saved['body']['schema'], 'research-record/1')
        self.assertEqual(saved['body']['content']['text'], original)
        self.assertEqual(set(saved['body']), {'schema', 'kind', 'content', 'scope', 'relations', 'created_at', 'available_at'})
        result = self.broker.call(self.worker, 'submit', lease=self.lease, artifact_id=identity)
        self.assertTrue(result['accepted'])
        self.assertFalse(result['scientific_authority'])
        self.op('release_batch', batch_id=self.batch, target_epoch=2)
        catalog = self.op('add_source', body={'schema': 'feature-catalog/1', 'features': {}}, data_class='development')['id']
        formalizer = self.op('register_worker', name='formalizer', role='formalizer', capabilities=['formalization/v1'])['token']
        context = self.op('create_context', role='formalizer', epoch=2, artifact_ids=[identity, catalog])['id']
        self.op('enqueue', key='formalizer-job', spec={'kind': 'formalization/v1', 'context_id': context,
            'purpose': 'Retain synthetic unsupported meaning exactly, without model provenance.',
            'allowed_workers': ['formalizer'], 'max_attempts': 1, 'lease_seconds': 60,
            'deadline': 2000, 'dependencies': []})
        lease = self.broker.call(formalizer, 'claim')['lease']
        draft = self.broker.call(formalizer, 'record_formalization', lease=lease, idea_id=identity,
            catalog_id=catalog, candidate=None, semantic_report=None)
        draft = self.op('get_artifact', artifact_id=draft['id'])
        self.assertEqual(draft['body']['original_idea'], saved['body'])
        self.assertEqual(draft['body']['assessment']['status'], 'RETAINED_GAP')
        self.assertFalse(draft['body']['scientific_readiness'])
        self.assertTrue(self.broker.call(formalizer, 'submit', lease=lease, artifact_id=draft['id'])['accepted'])
        draft_raw = self.raw(draft['id'])
        self.op('rebuild_memory')
        self.assertEqual(self.raw(identity), raw)
        self.assertEqual(self.raw(draft['id']), draft_raw)
        directory = self.broker.directory
        self.broker.close()
        self.broker = Broker(directory, clock=lambda: 1000)
        self.addCleanup(self.broker.close)
        self.assertEqual(self.raw(identity), raw)
        self.assertEqual(self.raw(draft['id']), draft_raw)
        backup, restored = self.root / 'backup', self.root / 'restored'
        self.op('backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, directory / 'operator.key')
        other = Broker(restored, clock=lambda: 1000)
        self.addCleanup(other.close)
        for key, expected in ((identity, raw), (draft['id'], draft_raw)):
            self.assertEqual(other._db.execute('SELECT envelope FROM artifacts WHERE id=?', (key,)).fetchone()[0], expected)
        other.call(other.admin_token, 'rebuild_memory')
        self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=identity)['body']['content']['text'], original)
        self.assertEqual(other.call(other.admin_token, 'verify')['status'], 'PASS')

    def test_exact_character_ceiling_accepts_unicode_without_trimming_or_byte_truncation(self):
        for original in (idea_text(65536), '🙂' * 65536):
            with self.subTest(utf8_bytes=len(original.encode('utf-8'))):
                self.assertEqual(len(original), 65536)
                saved = self.record(original)
                stored = self.op('get_artifact', artifact_id=saved['id'])
                self.assertEqual(stored['body']['content']['text'], original)
                self.assertEqual(stored['body']['content']['text'].encode('utf-8'), original.encode('utf-8'))
                self.assertEqual(stored['authority'], 'unverified_work_product')
        self.assertEqual(self.op('inspect_memory', view='market_model')['records'], [])

    def test_oversized_blank_and_nonstring_ideas_are_rejected_atomically(self):
        before = self.counts()
        for value in (idea_text(65537), '🙂' * 65537, '', ' \t\n ', None, True, 42, [], {}):
            with self.subTest(value_type=type(value).__name__, length=len(value) if type(value) is str else None):
                with self.assertRaises(Invalid):
                    self.record(value)
                self.assertEqual(self.counts(), before)

    def test_other_kinds_and_idea_fields_keep_the_original_text_limit(self):
        too_long = 'x' * 8193
        contents = {
            'source': {'text': too_long, 'uri': 'fixture:unchanged'},
            'observation': {'text': too_long},
            'gap': {'text': too_long, 'reason': 'Synthetic reason.', 'reopen_condition': 'No reopening authorized.'},
            'attempt': {'text': too_long, 'outcome': 'Synthetic only.'},
            'research_experience': {'text': too_long, 'interpretation': 'Unverified.'},
            'policy_experience': {'text': too_long, 'interpretation': 'Unverified.'}}
        before = self.counts()
        for kind, content in contents.items():
            with self.subTest(kind=kind), self.assertRaises(Invalid):
                self.op('add_research', kind=kind, content=content, scope={}, source_refs=[])
            self.assertEqual(self.counts(), before)
        for field, value in (('uncertainty', too_long), ('question', too_long), ('assumptions', [too_long])):
            with self.subTest(field=field), self.assertRaises(Invalid):
                self.record('Small valid idea.', content={'text': 'Small valid idea.', field: value})
            self.assertEqual(self.counts(), before)
        ordinary = self.op('add_research', kind='observation', content={'text': 'x' * 8192}, scope={}, source_refs=[])
        self.assertEqual(self.op('get_artifact', artifact_id=ordinary['id'])['body']['content']['text'], 'x' * 8192)

    def test_scope_queries_and_prompts_keep_8192_limit(self):
        too_long = 'x' * 8193
        before = self.counts()
        for scope in ({too_long: 'small'}, {'scope': too_long}, {'scope': [too_long]}):
            with self.subTest(scope_shape=list(scope)[:1]), self.assertRaises(Invalid):
                self.record('Small valid idea.', scope=scope)
            self.assertEqual(self.counts(), before)
        with self.assertRaises(Invalid):
            self.broker.call(self.worker, 'search_memory', lease=self.lease, query=too_long)
        self.assertEqual(self.counts(), before)
        self.op('register_worker', name='other-discovery', role='discovery', capabilities=['research-record/v1'])
        profile = {'model': 'fixture/1', 'prompt_version': 'unchanged-limits/1', 'mode': 'fixture',
            'currency': 'NONE', 'max_calls': 2, 'max_tokens': 2000, 'max_seconds': 60,
            'max_cost_units': 0, 'prompts': {'discovery': too_long, 'other-discovery': 'Small prompt.'},
            'tools': [], 'generation_parameters': {}, 'max_output_tokens': 64,
            'call_timeout_seconds': 5, 'max_retries': 0}
        with self.assertRaises(Invalid):
            self.op('create_research_epoch', key='invalid-prompt', context_id=self.context,
                workers=['discovery', 'other-discovery'], profile=profile)
        self.assertIsNone(self.broker._db.execute('SELECT id FROM research_epochs WHERE request_key=?',
            ('invalid-prompt',)).fetchone())

    def test_one_mebibyte_envelope_bound_remains_independent_of_character_limit(self):
        self.assertEqual(MAX_BYTES, 1048576)
        scope = {str(number): '🙂' * 8192 for number in range(32)}
        self.assertGreater(len(json.dumps(scope, ensure_ascii=False).encode('utf-8')), MAX_BYTES)
        before = self.counts()
        with self.assertRaises(Invalid):
            self.record(idea_text(65536), scope=scope)
        self.assertEqual(self.counts(), before)

    def test_existing_short_record_envelope_remains_exact_and_no_new_schema_field_appears(self):
        identity = self.op('add_research', kind='idea', content={'text': '  Original short idea.\n'},
            scope={'fixture': 'existing'}, source_refs=[])['id']
        expected = {'version': 'local-artifact/1', 'creator': 'operator', 'origin': 'source',
            'data_class': 'development', 'body': {'schema': 'research-record/1', 'kind': 'idea',
                'content': {'text': '  Original short idea.\n'}, 'scope': {'fixture': 'existing'},
                'relations': {}, 'created_at': 1000, 'available_at': 1000},
            'source_refs': [], 'exposure': [], 'not_before_epoch': 0, 'authority': 'supplied_source_not_certified'}
        self.assertEqual(self.raw(identity), canonical(expected))
        before = self.raw(identity)
        self.record(idea_text(8255))
        self.op('rebuild_memory')
        self.assertEqual(self.raw(identity), before)
        self.assertEqual(self.op('get_artifact', artifact_id=identity), {'id': identity, **expected})

    def test_retained_rejected_response_does_not_reopen_or_authorize_blocked_job(self):
        original = idea_text(8255)
        response = self.broker.call(self.worker, 'put_artifact', lease=self.lease,
            body={'schema': 'synthetic-retained-response/1', 'output': {'record': {
                'kind': 'idea', 'content': {'text': original}, 'scope': {}, 'source_refs': []}}}, source_refs=[])
        raw = self.raw(response['id'])
        self.broker.call(self.worker, 'block', lease=self.lease, reason='Historical bounded-string rejection.',
            needs=['No automatic retrospective admission'], retry_when='Separate explicit work authorization.')
        job_before = self.op('inspect', job_id=self.job)
        self.assertEqual(job_before['state'], 'blocked')
        self.op('rebuild_memory')
        directory = self.broker.directory
        self.broker.close()
        self.broker = Broker(directory, clock=lambda: 1000)
        self.addCleanup(self.broker.close)
        self.assertEqual(self.raw(response['id']), raw)
        self.assertEqual(self.op('inspect', job_id=self.job), job_before)
        with self.assertRaises(Denied):
            self.record(original)
        self.assertIsNone(self.broker.call(self.worker, 'claim'))
        self.assertEqual(self.op('inspect', job_id=self.job)['state'], 'blocked')


if __name__ == '__main__':
    unittest.main()
