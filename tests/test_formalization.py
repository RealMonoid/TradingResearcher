"""Retained ideas, explicit semantic differences and deterministic draft checks."""
import copy
import tempfile
import unittest

from trading_researcher.codec import MAX_BYTES, canonical, digest
from trading_researcher.coordination import Broker, Denied, Invalid


class FormalizationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.broker = Broker(self.tmp.name, clock=lambda: 1000)
        self.admin = self.broker.admin_token
        self.token = self.op('register_worker', name='formalizer', role='formalizer',
                             capabilities=['formalization/v1'])['token']
        self.idea = self.op('add_research', kind='idea', content={'text': 'An unrestricted original idea.'},
                            scope={}, source_refs=[])['id']
        self.catalog = {'x@1': {'type': 'real', 'unit': 'USDT'},
                        'up@1': {'type': 'boolean', 'unit': None}}
        self.catalog_id = self.op('add_source', body={'schema': 'feature-catalog/1', 'features': self.catalog},
                                  data_class='development')['id']
        context = self.op('create_context', role='formalizer', epoch=1,
                          artifact_ids=[self.idea, self.catalog_id])['id']
        self.job = self.op('enqueue', key='draft', spec={
            'kind': 'formalization/v1', 'context_id': context, 'purpose': 'Retain a faithful candidate or explicit gap',
            'allowed_workers': ['formalizer'], 'max_attempts': 1, 'lease_seconds': 30,
            'deadline': 2000, 'dependencies': []})['id']
        claimed = self.broker.call(self.token, 'claim')
        self.lease = None if claimed is None else claimed['lease']
        self.candidate = self.make_candidate()
        self.semantic = {'status': 'equivalent', 'segments': [{
            'text': 'An unrestricted original idea.', 'path': '/estimand',
            'interpretation': 'Fixture mapping assertion; not a proof of natural-language meaning.'}],
            'differences': []}

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def op(self, op, **args):
        return self.broker.call(self.admin, op, **args)

    def program(self, expression):
        return {'schema': 'research-ast/1', 'catalog_hash': digest(self.catalog), 'expression': expression}

    def make_candidate(self):
        paths = ['/scope_ast/expression/value', '/condition_ast/expression/right/value', '/horizons/outcome_bars']
        return {'schema': 'hypothesis-exec/1', 'idea_ref': self.idea, 'claim_kind': 'difference',
            'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'ratio', 'weighting': 'equal_rows',
                        'missingness': 'scope-true-outcome-observed/1',
                        'condition_unknown': 'exclude-from-condition-retain-in-scope',
                        'nuisance_fit': 'none', 'direction': 'positive'},
            'scope_ast': self.program({'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}),
            'condition_ast': self.program({'op': 'gt', 'left': {'op': 'feature', 'ref': 'x@1'},
                                          'right': {'op': 'literal', 'type': 'real', 'unit': 'USDT', 'value': '100'}}),
            'outcome': {'program': self.program({'op': 'feature', 'ref': 'up@1'}), 'scale': 'binary_probability'},
            'comparator': {'kind': 'whole_scope'}, 'horizons': {'grid_seconds': 900, 'outcome_bars': 4},
            'test_universe': {'instruments': ['BTCUSDT'], 'start': '2024-01-01T00:00:00Z',
                              'end': '2025-01-01T00:00:00Z', 'data_snapshot_ref': self.catalog_id},
            'parameter_origins': [{'path': path, 'basis': 'preexisting_specification', 'source_refs': [],
                                   'rationale': 'Independently stated fixture input'} for path in paths],
            'feature_refs': ['up@1', 'x@1']}

    def record(self, **changes):
        return self.broker.call(self.token, 'record_formalization', lease=self.lease,
                                idea_id=self.idea, catalog_id=self.catalog_id,
                                candidate=changes.get('candidate', self.candidate),
                                semantic_report=changes.get('semantic_report', self.semantic))

    def test_original_idea_separate_from_structurally_checked_candidate(self):
        original = self.op('get_artifact', artifact_id=self.idea)
        saved = self.record()
        artifact = self.op('get_artifact', artifact_id=saved['id'])
        self.assertEqual(artifact['body']['original_idea'], original['body'])
        self.assertEqual(artifact['body']['candidate'], self.candidate)
        self.assertEqual(artifact['body']['assessment']['status'], 'STRUCTURE_CHECKED')
        self.assertFalse(artifact['body']['scientific_readiness'])
        self.assertTrue({self.idea, self.catalog_id} <= set(artifact['exposure']))
        self.assertEqual(self.op('get_artifact', artifact_id=self.idea), original)
        result = self.broker.call(self.token, 'submit', lease=self.lease, artifact_id=saved['id'])
        self.assertTrue(result['accepted'])
        self.assertFalse(result['scientific_authority'])

    def test_unsupported_forms_remain_exact_candidates_and_gaps(self):
        for kind in ('association', 'change', 'boundary', 'interaction'):
            candidate = {**self.candidate, 'claim_kind': kind, 'estimand': {'kind': 'not-yet-installed/1'}}
            saved = self.record(candidate=candidate)
            body = self.op('get_artifact', artifact_id=saved['id'])['body']
            self.assertEqual(body['candidate'], candidate)
            self.assertEqual(body['assessment']['gap']['code'], 'EVALUATION_GAP')
            journal = self.op('get_artifact', artifact_id=saved['journal_id'])['body']
            self.assertEqual(journal['kind'], 'gap')
            self.assertIn(saved['id'], journal['content']['text'])

    def test_semantic_difference_ambiguity_and_original_text_mutation_cannot_advance(self):
        for status in ('different', 'ambiguous'):
            report = {**self.semantic, 'status': status, 'differences': ['The requested horizon is not represented']}
            saved = self.record(semantic_report=report)
            self.assertEqual(saved['assessment']['gap']['code'], 'SEMANTIC_AMBIGUITY')
        report = copy.deepcopy(self.semantic)
        report['segments'][0]['text'] = 'Silently rewritten meaning'
        saved = self.record(semantic_report=report)
        self.assertEqual(saved['assessment']['gap']['code'], 'SEMANTIC_AMBIGUITY')

    def test_meaning_units_future_inputs_and_unaccounted_parameters_become_gaps(self):
        variants = []
        for field, value, code in [('comparator', {'kind': 'condition_complement'}, 'EVALUATION_GAP'),
                                   ('feature_refs', ['x@1'], 'FEATURE_GAP'),
                                   ('parameter_origins', [], 'SEMANTIC_AMBIGUITY')]:
            variants.append(({**self.candidate, field: value}, code))
        bad_unit = copy.deepcopy(self.candidate)
        bad_unit['estimand']['unit'] = 'USD'
        variants.append((bad_unit, 'TYPE_GAP'))
        future = copy.deepcopy(self.candidate)
        future['condition_ast']['expression'] = {'op': 'lag', 'bars': -1,
                                                'arg': {'op': 'feature', 'ref': 'up@1'}}
        variants.append((future, 'TEMPORAL_GAP'))
        for candidate, code in variants:
            saved = self.record(candidate=candidate)
            self.assertEqual(saved['assessment']['status'], 'RETAINED_GAP')
            self.assertEqual(saved['assessment']['gap']['code'], code)

    def test_unknown_source_references_are_retained_without_granting_access(self):
        hidden = self.op('add_source', body={'secret': 'not exposed'}, data_class='assessment')['id']
        candidate = copy.deepcopy(self.candidate)
        candidate['parameter_origins'][0]['source_refs'] = [hidden]
        saved = self.record(candidate=candidate)
        self.assertEqual(saved['assessment']['gap']['code'], 'DATA_GAP')
        artifact = self.op('get_artifact', artifact_id=saved['id'])
        self.assertNotIn(hidden, artifact['source_refs'])
        self.assertNotIn('not exposed', str(artifact))

    def test_generic_writes_cannot_forge_formalization_namespace(self):
        with self.assertRaises(Invalid):
            self.broker.call(self.token, 'put_artifact', lease=self.lease,
                             body={'schema': 'formalization-record/1', 'scientific_readiness': True}, source_refs=[])
        with self.assertRaises(Invalid):
            self.op('add_source', body={'schema': 'formalization-record/1'}, data_class='development')

    def test_invalid_reference_types_fail_without_unhandled_exception(self):
        for identity in ([], {}, None, True):
            with self.assertRaises(Invalid):
                self.broker.call(self.token, 'record_formalization', lease=self.lease,
                                 idea_id=identity, catalog_id=self.catalog_id,
                                 candidate=self.candidate, semantic_report=self.semantic)

    def test_oversized_retained_envelope_is_rejected_without_partial_draft(self):
        args = {'lease': self.lease, 'idea_id': self.idea, 'catalog_id': self.catalog_id,
                'candidate': [''], 'semantic_report': self.semantic}
        overhead = len(canonical(args).encode('utf-8'))
        args['candidate'] = ['x' * (MAX_BYTES - overhead - 100)]
        self.assertLess(len(canonical(args).encode('utf-8')), MAX_BYTES)
        before = self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]
        with self.assertRaisesRegex(Invalid, '^RESOURCE_GAP:'):
            self.broker.call(self.token, 'record_formalization', **args)
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], before)
        self.assertEqual(self.op('get_artifact', artifact_id=self.idea)['body']['content']['text'],
                         'An unrestricted original idea.')

    def test_draft_submission_through_authenticated_rpc(self):
        import threading
        from trading_researcher.server import Client, LocalServer
        server = LocalServer(self.broker, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = Client(server.url, self.token)
            saved = client.call('record_formalization', lease=self.lease, idea_id=self.idea,
                                 catalog_id=self.catalog_id, candidate=self.candidate, semantic_report=self.semantic)
            outcome = client.call('submit', lease=self.lease, artifact_id=saved['id'])
            self.assertTrue(outcome['accepted'])
            self.assertFalse(outcome['scientific_authority'])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(5)

    def test_complete_batch_releases_prior_gap_drafts_and_preserves_replay(self):
        gap = self.record(candidate={**self.candidate, 'claim_kind': 'interaction'})
        good = self.record()
        self.broker.call(self.token, 'submit', lease=self.lease, artifact_id=good['id'])
        batch = self.op('inspect', job_id=self.job)['batch_id']
        release = self.op('release_batch', batch_id=batch, target_epoch=2)
        self.assertIn(gap['id'], release['artifact_ids'])
        self.assertIn(good['id'], release['artifact_ids'])
        before = self.op('inspect_memory')
        self.op('rebuild_memory')
        self.assertEqual(self.op('inspect_memory'), before)
        self.assertEqual(self.op('verify')['status'], 'PASS')

    def test_formalization_and_derived_source_cannot_enter_an_earlier_snapshot(self):
        draft = self.record()
        self.broker.call(self.token, 'submit', lease=self.lease, artifact_id=draft['id'])
        batch = self.op('inspect', job_id=self.job)['batch_id']
        self.op('release_batch', batch_id=batch, target_epoch=2)
        with self.assertRaises(Denied):
            self.op('create_context', role='formalizer', epoch=2, research_time=0, artifact_ids=[draft['id']])
        self.broker.clock = lambda: 500
        derived = self.op('add_research', kind='source', content={'text': 'Derived draft summary', 'uri': 'fixture:derived'},
                          scope={}, source_refs=[draft['id']])['id']
        self.assertEqual(self.op('get_artifact', artifact_id=derived)['body']['available_at'], 1000)
        with self.assertRaises(Denied):
            self.op('create_context', role='formalizer', epoch=2, research_time=500, artifact_ids=[derived])

    def test_generic_descendant_cannot_launder_known_source_availability(self):
        copied = self.op('add_source', body={'text': 'A derived prose copy'}, data_class='development',
                         exposure=[self.idea])['id']
        with self.assertRaises(Denied):
            self.op('create_context', role='formalizer', epoch=2, research_time=0, artifact_ids=[copied])


if __name__ == '__main__':
    unittest.main()
