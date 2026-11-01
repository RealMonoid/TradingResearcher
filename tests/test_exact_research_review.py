"""Independent adversaries at the temporary native exact-research boundary.

Uses the declared NativeFixtureBroker/real SQLite/auth/lease fixture. Its owned
definition metadata is a synthetic seed, not a feature certificate. This does
not qualify finite funding, production admission, or actual model behavior.
"""
from copy import deepcopy
import re
import unittest
from unittest.mock import patch

import test_exact_research as native
from trading_researcher.codec import Invalid, canonical
from trading_researcher.errors import Denied
from trading_researcher.exact_research import LOADED


class ExactResearchReview(unittest.TestCase):
    def setUp(self):
        self.fixture = native.ExactResearchTests('test_native_commit_submit_idempotence_and_separate_original')
        self.addCleanup(self.fixture.doCleanups)
        self.fixture.setUp()

    def record(self, lease, call, *, candidate=None, mapping=None):
        f = self.fixture
        return f.broker.call(f.tokens['author'], 'record_formalization', lease=lease,
            idea_id=f.idea, catalog_id=f.catalog_id,
            candidate=f.candidate if candidate is None else candidate,
            semantic_report=f.mapping if mapping is None else mapping, provider_call_id=call)

    def count_artifacts(self):
        return self.fixture.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]

    def test_mapping_change_after_retained_response_is_rejected_atomically(self):
        f = self.fixture
        lease, call, _ = f.provider_response(f.formal_spec, 'author',
            {'status': 'final', 'candidate': f.candidate, 'semantic_report': f.mapping}, 'mapping-binding')
        changed = deepcopy(f.mapping)
        changed['segments'][0]['interpretation'] += ' Altered after provider settlement.'
        before = self.count_artifacts()
        with self.assertRaises(Invalid):
            self.record(lease, call, mapping=changed)
        self.assertEqual(self.count_artifacts(), before)
        saved = self.record(lease, call)
        body = f.op('get_artifact', artifact_id=saved['id'])['body']
        self.assertEqual(body['semantic_report'], f.mapping)
        self.assertEqual(body['original_idea']['content']['text'], f.original)

    def test_same_worker_call_from_another_job_cannot_supply_this_attempt(self):
        f = self.fixture
        _, _, _ = f.accepted()
        old_call = f.op('inspect_research_epoch', epoch_id=f.epoch)['calls'][0]['id']
        lease, call, _ = f.provider_response(f.formal_spec, 'author',
            {'status': 'final', 'candidate': f.candidate, 'semantic_report': f.mapping}, 'second-job')
        before = self.count_artifacts()
        with self.assertRaises(Denied):
            self.record(lease, old_call)
        self.assertEqual(self.count_artifacts(), before)
        saved = self.record(lease, call)
        self.assertEqual(f.op('get_artifact', artifact_id=saved['id'])['body']['candidate'], f.candidate)

    def test_extra_provider_output_fields_do_not_authorize_a_draft(self):
        f = self.fixture
        lease, call, _ = f.provider_response(f.formal_spec, 'author', {
            'status': 'final', 'candidate': f.candidate, 'semantic_report': f.mapping,
            'scientific_readiness': True}, 'extra-fields')
        before = self.count_artifacts()
        with self.assertRaises(Invalid):
            self.record(lease, call)
        self.assertEqual(self.count_artifacts(), before)
        calls = f.op('inspect_research_epoch', epoch_id=f.epoch)['calls']
        self.assertEqual(calls[0]['state'], 'recorded')
        self.assertIsNotNone(calls[0]['reply'])

    def test_source_mismatch_prohibits_use_without_erasing_recorded_reply(self):
        f = self.fixture
        lease, call, _ = f.provider_response(f.formal_spec, 'author',
            {'status': 'final', 'candidate': f.candidate, 'semantic_report': f.mapping}, 'source-binding')
        before = self.count_artifacts()
        # Inject only a wrong expected hash; production source files stay intact.
        # This tests deny-use/retention, not in-flight finite ledger settlement.
        with patch.dict(LOADED, {'trading_researcher/exact_formalization.py': '0' * 64}):
            with self.assertRaises(Invalid):
                self.record(lease, call)
        self.assertEqual(self.count_artifacts(), before)
        calls = f.op('inspect_research_epoch', epoch_id=f.epoch)['calls']
        self.assertEqual(calls[0]['state'], 'recorded')
        self.assertEqual(calls[0]['reply']['response']['output']['candidate'], f.candidate)

    def test_later_import_does_not_enter_frozen_review_packet_or_read_capability(self):
        f = self.fixture
        saved, _, _ = f.accepted()
        spec = f.spec('semantic-review/v1', 'reviewer',
            [saved['id'], f.idea, f.catalog_id, f.definition],
            {'formalization_id': saved['id'], 'definition_ids': [f.definition]})
        late = f.op('add_source', body={'unrelated_later_source': True}, data_class='development')['id']
        f.op('enqueue', key='frozen-review', spec=spec)
        lease = f.broker.call(f.tokens['reviewer'], 'claim')['lease']
        packet = f.broker.call(f.tokens['reviewer'], 'auxiliary_input', lease=lease)
        self.assertNotIn(late, f.broker._context(spec['context_id'])['artifact_ids'])
        self.assertNotIn(late, canonical(packet))
        with self.assertRaises(Denied):
            f.broker.call(f.tokens['reviewer'], 'read_artifact', lease=lease, artifact_id=late)

    def test_untrusted_snapshot_text_does_not_trigger_hidden_artifact_lookup(self):
        f = self.fixture
        hidden = f.op('add_source', body={'schema': 'synthetic-assessment-only/1'}, data_class='assessment')['id']
        failures = []
        for index, untrusted in enumerate(('f' * 64, hidden)):
            changed = deepcopy(f.candidate)
            changed['test_universe']['data_snapshot_ref'] = untrusted
            saved, lease, _ = f.formalize(candidate=changed, key='gap-' + str(index))
            body = f.op('get_artifact', artifact_id=saved['id'])['body']
            self.assertEqual(body['assessment']['status'], 'RETAINED_GAP')
            result = f.broker.call(f.tokens['author'], 'submit', lease=lease, artifact_id=saved['id'])
            self.assertTrue(result['accepted'])
            batch = f.op('inspect', job_id=lease['job_id'])['batch_id']
            f.op('release_batch', batch_id=batch, target_epoch=3)
            spec = f.spec('semantic-review/v1', 'reviewer',
                [saved['id'], f.idea, f.catalog_id, f.definition],
                {'formalization_id': saved['id'], 'definition_ids': [f.definition]})
            queries = []
            f.broker._db.set_trace_callback(queries.append)
            try:
                with self.assertRaises((Invalid, Denied)) as caught:
                    f.op('enqueue', key='unknown-target-' + str(index), spec=spec)
            finally:
                f.broker._db.set_trace_callback(None)
            failures.append(str(caught.exception))
            # Inspect real temporary SQL, without replacing an access check or
            # source lookup. A known/unknown private ID must not be followed.
            followed = [sql for sql in queries if re.search(
                r'FROM\s+artifacts\s+WHERE\s+id\s*=\s*\x27' + re.escape(untrusted) + r'\x27', sql, re.I)]
            self.assertEqual(followed, [])
        self.assertEqual(failures[0], failures[1])

    def test_review_cannot_substitute_feature_meaning_with_same_type_and_unit(self):
        f = self.fixture
        saved, _, _ = f.accepted()
        replacement = deepcopy(f.op('get_artifact', artifact_id=f.definition))
        replacement.pop('id')
        replacement['body']['definitions'][0]['meaning'] = 'A different synthetic meaning with the same type and unit.'
        # Same explicitly declared prior-metadata seed boundary as the native
        # fixture; this is not a feature certificate or a qualification bypass.
        with f.broker._transaction():
            substitute = f.broker._save_artifact(replacement)['id']
        spec = f.spec('semantic-review/v1', 'reviewer',
            [saved['id'], f.idea, f.catalog_id, substitute],
            {'formalization_id': saved['id'], 'definition_ids': [substitute]})
        with self.assertRaises((Invalid, Denied)):
            f.op('enqueue', key='substituted-meaning', spec=spec)


if __name__ == '__main__':
    unittest.main()
