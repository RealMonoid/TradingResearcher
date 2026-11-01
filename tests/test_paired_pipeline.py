"""Genuine temporary D094 jobs with offline deterministic model transport.

Acquisition bytes, normalized rows, feature qualification, source qualification,
budgets, contexts, jobs, provider receipts, submission and meaning inventory are
real local implementations. Only the provider invocation output and the fixed
production idea ID are substituted for synthetic fixtures. A passing process
assessment in this test is not actual independent model judgment.
"""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from trading_researcher import openai_provider as openai
from trading_researcher import paired_budget as budget
from trading_researcher import paired_composition
from trading_researcher.binance_archive import capture_provider_docs
from trading_researcher.binance_ingest import retain_provider_documents
from trading_researcher.auxiliary import run_auxiliary_once, request_for
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.errors import Denied, Conflict
from trading_researcher.paired_broker import PairedBroker
from trading_researcher.paired_development import CONTRACT
from trading_researcher.paired_formalization import assess_candidate
from trading_researcher.formalization import assess_candidate as legacy_assess
import test_binance_normalize as normalization_tests
from test_binance_quality import row
from test_paired_development_adversarial import boundary_rows
from test_paired_host_adversarial import role_profile
from test_researcher import LocalClient


REJECTIONS = (Invalid, Denied, Conflict)
ORIGINAL = ('Synthetic paired lifecycle fixture. Preserve the complete paired shock/recovery condition, '
            'five-bar anchor, four-close log spread, required-input unknown semantics and equal timestamp weights. '
            'This fixture supplies process expectations only and asserts no market result or actual model fidelity.')


class PairedProviderDocumentTests(unittest.TestCase):
    def test_exact_reviewed_public_source_bytes(self):
        documents = Path(__file__).parent / 'fixtures' / 'paired_provider_documents'
        pinned = {'README.md': '2e133d9945a9263a02781369078e72805eff074680f305cd5460016471c6caad',
            'TERMS_AND_CONDITIONS.md': '99c4921dbe023cd68c1a447775707d621453cc78aec6ac0bfe2e6c06a5114ee0'}
        for name, expected in pinned.items():
            with self.subTest(document=name):
                self.assertFalse((documents / name).exists())
                self.assertEqual(hashlib.sha256((documents / (name + '.source')).read_bytes()).hexdigest(), expected)


class OwnedPairedFixture:
    def __init__(self, grid_bars=8):
        self.normalization = normalization_tests.NormalizeTests()
        self.normalization.setUp()
        self.broker = self.normalization.broker
        self.idea_patch = None
        self.grid_bars = grid_bars
        self.end = (datetime(2020, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=grid_bars * 900)).strftime('%Y-%m-%dT%H:%M:%SZ')
        # Each configuration includes a tariff-expiry timestamp. Freeze once;
        # recreating it after real certification changes the exact route bytes.
        self.role_profiles = {kind: role_profile(kind) for kind in ('formalization/v1', 'semantic-review/v1')}
        try:
            # Exact already-reviewed public bytes, copied without rewriting from
            # the retained October25 acquisition. No network or market source.
            documents = Path(__file__).parent / 'fixtures' / 'paired_provider_documents'
            pinned = {'README.md': '2e133d9945a9263a02781369078e72805eff074680f305cd5460016471c6caad',
                'TERMS_AND_CONDITIONS.md': '99c4921dbe023cd68c1a447775707d621453cc78aec6ac0bfe2e6c06a5114ee0'}
            values = {name: (documents / (name + '.source')).read_bytes() for name in pinned}
            if {name: hashlib.sha256(raw).hexdigest() for name, raw in values.items()} != pinned:
                raise AssertionError('Reviewed public document fixture differs')
            captured = self.normalization.root / 'reviewed-provider-documents'
            capture_provider_docs(captured, downloader=lambda url, limit: (values[url.rsplit('/', 1)[-1]], {}))
            self.normalization.docs = retain_provider_documents(self.broker, self.broker.admin_token, captured)['id']
            sources = [self.normalization.source(b''.join(row(1577836800000 + index * 900000)
                for index in range(7)), symbol=member) for member in ('BTCUSDT', 'ETHUSDT')]
            result = self.normalization.run_normalize(sources, end=self.end,
                instruments=['BTCUSDT', 'ETHUSDT'], delay=900)
            self.broker = self.normalization.broker
            self.snapshot = result['snapshot']
            self.feature = self.op('certify_features', data_snapshot_id=self.snapshot['id'])
            if self.feature['body']['status'] != 'CERTIFIED':
                raise AssertionError(self.feature['body'])
            self.definition_id = self.feature['body']['definitions_id']
            self.catalog_id = self.snapshot['body']['catalog_id']
            idea_id = self.op('add_research', kind='idea', content={'text': ORIGINAL}, scope={}, source_refs=[])['id']
            self.idea = self.op('get_artifact', artifact_id=idea_id)
            self.idea_patch = patch.object(budget, 'IDEA', self.idea['id'])
            self.idea_patch.start()
            self.ledger_path = self.normalization.root / 'paired-spend.sqlite3'
            openai.SpendLedger(self.ledger_path, 5000000000)
            self.certificate_id = None
            self.restart('formalization/v1')
            reference = self.broker.certify_paired(self.broker.admin_token)
            if reference['body']['status'] != 'CERTIFIED':
                raise AssertionError(reference['body'])
            self.certificate_id = reference['id']
            self.op('release_feature_evidence', certificate_id=self.feature['id'], target_epoch=1)
            self.ids = sorted([self.idea['id'], self.catalog_id, self.definition_id,
                               self.snapshot['id'], self.feature['id']])
            self.tokens = {}
            for name, role, capabilities in (('first', 'discovery', ['research-record/v1']),
                    ('second', 'discovery', ['research-record/v1']),
                    ('formalizer', 'formalizer', ['formalization/v1', 'semantic-review/v1']),
                    ('reviewer', 'formalizer', ['semantic-review/v1'])):
                self.tokens[name] = self.op('register_worker', name=name, role=role, capabilities=capabilities)['token']
            base_context = self.op('create_context', role='discovery', epoch=1, artifact_ids=self.ids)['id']
            selected = self.role_profiles['formalization/v1']
            profile = {'model': openai.MODEL, 'prompt_version': 'paired-pipeline/1', 'mode': 'live',
                'currency': 'USD', 'max_calls': 2, 'max_tokens': 160000, 'max_cost_units': 600000000,
                'max_seconds': 1800, 'call_timeout_seconds': 360, 'max_output_tokens': 18000,
                'max_retries': 0, 'tools': [], 'prompts': {'first': 'Unused perspective one.', 'second': 'Unused perspective two.'},
                'generation_parameters': deepcopy(selected['generation_parameters'])}
            self.epoch = self.op('create_research_epoch', key='paired-pipeline-once', context_id=base_context,
                workers=['first', 'second'], profile=profile, budget_overlay=budget.POLICY)['id']
            self.formal_context = self.op('create_context', role='formalizer', epoch=1, artifact_ids=self.ids)['id']
            self.batch = self.op('create_batch', key='formalizer-batch', epoch=1)['id']
            self.formal_spec = self.spec('formalization/v1', self.formal_context, 'formalizer', self.batch,
                {'idea_id': self.idea['id'], 'catalog_id': self.catalog_id})
            self.formal_job = self.op('enqueue', key='formalization', spec=self.formal_spec)['id']
            self.op('seal_batch', batch_id=self.batch)
        except BaseException:
            self.close()
            raise

    def close(self):
        self.broker.close()
        if self.idea_patch is not None:
            self.idea_patch.stop()
        self.normalization.tmp.cleanup()

    def restart(self, kind):
        self.broker.close()
        config = deepcopy(self.role_profiles[kind]['generation_parameters']['openai_responses'])
        route = {openai.MODEL: {'provider': 'openai', 'key_file': str(self.normalization.root / 'absent-api-key'),
            'budget_file': str(self.ledger_path), 'config': config}}
        self.broker = PairedBroker(self.normalization.root / 'registry', provider_routes=route,
                                   paired_certificate_id=self.certificate_id)
        self.normalization.broker = self.broker

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def spec(self, kind, context, worker, batch, inputs):
        return {'kind': kind, 'context_id': context, 'purpose': 'Independent synthetic paired process fixture.',
            'allowed_workers': [worker], 'max_attempts': 1, 'lease_seconds': 600,
            'deadline': int(time.time()) + 1800, 'dependencies': [], 'batch_id': batch,
            'research_epoch_id': self.epoch, 'research_call_profile': deepcopy(self.role_profiles[kind]),
            'research_inputs': {**inputs, 'definition_ids': [self.definition_id],
                'feature_certificate_id': self.feature['id'], 'paired_contract': CONTRACT}}

    def candidate(self):
        request, _, _, _ = boundary_rows()
        catalog = self.broker._artifact(self.catalog_id)['body']['features']
        candidate = {'schema': 'hypothesis-exec/2', 'idea_ref': self.idea['id'], 'claim_kind': 'difference',
            'scope_ast': deepcopy(request['scope_program']), 'condition_ast': deepcopy(request['condition_program']),
            'outcome': {'program': deepcopy(request['outcome_program']), 'scale': 'quantity'},
            'horizons': {'grid_seconds': 900, 'outcome_bars': 5}, 'comparator': {'kind': 'whole_scope'},
            'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'basis_points', 'weighting': 'equal_rows',
                'missingness': 'scope-true-outcome-observed/1', 'condition_unknown': 'exclude-from-condition-retain-in-scope',
                'nuisance_fit': 'none', 'direction': 'positive'},
            'test_universe': {'start': '2020-01-01T00:00:00Z', 'end': self.end,
                'pair': ['BTCUSDT', 'ETHUSDT'], 'data_snapshot_ref': self.snapshot['id']},
            'feature_refs': [], 'parameter_origins': []}
        refs, paths = set(), ['/horizons/outcome_bars']
        def visit(node, path):
            if node['op'] == 'feature_at': refs.add(node['ref'])
            if node['op'] == 'literal': paths.append(path + '/value')
            if node['op'] in ('lag', 'trailing_mean', 'trailing_median'): paths.append(path + '/bars')
            for name in ('arg', 'left', 'right'):
                if name in node: visit(node[name], path + '/' + name)
        for path, program in (('/scope_ast', candidate['scope_ast']), ('/condition_ast', candidate['condition_ast']),
                              ('/outcome/program', candidate['outcome']['program'])):
            program['catalog_hash'] = digest(catalog)
            visit(program['expression'], path + '/expression')
        candidate['feature_refs'] = sorted(refs)
        candidate['parameter_origins'] = [{'path': path, 'basis': 'preexisting_specification',
            'source_refs': [self.idea['id']], 'rationale': 'Fixed synthetic protocol fixture, not market selection.'} for path in paths]
        mapping = {'status': 'equivalent', 'differences': [], 'segments': [
            {'text': ORIGINAL, 'path': '/condition_ast', 'interpretation': 'Deterministic test response, not independent model reasoning.'}]}
        return candidate, mapping

    def invoke(self, worker, output):
        reply = {'response': {'status': 'completed', 'provider_id': 'offline-test', 'output': output},
                 'usage': {'input_tokens': 100, 'output_tokens': 100, 'cost_units': 1}}
        with patch('trading_researcher.controller_providers._invoke', return_value=reply) as invoked:
            result = run_auxiliary_once(LocalClient(self.broker, self.tokens[worker]))
        if invoked.call_count != 1:
            retained = [dict(item) for item in self.broker._db.execute(
                'SELECT id,state,detail FROM jobs WHERE owner=?', (worker,))]
            raise AssertionError({'invocation_count': invoked.call_count, 'result': result, 'retained_job_details': retained})
        return result


class PairedPipelineTests(unittest.TestCase):
    def test_real_owned_formalization_separate_review_and_current_inventory(self):
        self._lifecycle()

    def test_resource_stop_preserves_independently_replayed_case_prefix(self):
        self._lifecycle(grid_bars=64, max_steps=10000, expected_status='RESOURCE_STOP')

    def _lifecycle(self, grid_bars=8, max_steps=10000000, expected_status='DESCRIPTIVE_EXECUTION'):
        fixture = OwnedPairedFixture(grid_bars)
        self.addCleanup(fixture.close)
        candidate, mapping = fixture.candidate()
        definitions = fixture.broker._artifact(fixture.definition_id)['body']['definitions']
        catalog = fixture.broker._artifact(fixture.catalog_id)['body']['features']
        args = (fixture.idea['id'], ORIGINAL, candidate, mapping, catalog, set(fixture.ids))
        self.assertEqual(assess_candidate(*args, definitions)['status'], 'STRUCTURE_CHECKED')
        self.assertEqual(legacy_assess(*args)['status'], 'RETAINED_GAP')
        formal_packet = fixture.broker._auxiliary_packet_for_spec(fixture.formal_spec)
        self.assertEqual(formal_packet['paired_contract']['schema'], CONTRACT)
        self.assertEqual(len(formal_packet['paired_contract']['documents']), 3)
        self.assertEqual({item['id'] for item in formal_packet['sources']}, set(fixture.ids) - {fixture.feature['id']})
        output = {'status': 'final', 'candidate': candidate, 'semantic_report': mapping}
        formal = fixture.invoke('formalizer', output)
        self.assertTrue(formal['accepted'], formal)
        target = fixture.op('get_artifact', artifact_id=formal['artifact_id'])
        self.assertEqual(target['body']['schema'], 'formalization-record/2')
        self.assertEqual(target['body']['candidate'], candidate)
        self.assertEqual(target['body']['original_idea'], fixture.idea['body'])
        self.assertEqual(target['body']['assessment']['status'], 'STRUCTURE_CHECKED')
        fixture.op('release_batch', batch_id=fixture.batch, target_epoch=2)
        context = fixture.op('create_context', role='formalizer', epoch=2,
            artifact_ids=[*fixture.ids, target['id']])['id']
        batch = fixture.op('create_batch', key='review-batch', epoch=2)['id']
        review_spec = fixture.spec('semantic-review/v1', context, 'reviewer', batch,
                                   {'formalization_id': target['id']})
        review_spec['dependencies'] = [fixture.formal_job]
        for mutate in ('same-worker', 'drop-evidence', 'swap-evidence', 'legacy-contract'):
            changed = deepcopy(review_spec)
            if mutate == 'same-worker': changed['allowed_workers'] = ['formalizer']
            elif mutate == 'drop-evidence': del changed['research_inputs']['feature_certificate_id']
            elif mutate == 'swap-evidence': changed['research_inputs']['feature_certificate_id'] = fixture.snapshot['id']
            else: del changed['research_inputs']['paired_contract']
            with self.subTest(mutation=mutate), self.assertRaises(REJECTIONS):
                fixture.op('enqueue', key='denied-' + mutate, spec=changed)
        review_packet = fixture.broker._auxiliary_packet_for_spec(review_spec)
        self.assertEqual(review_packet['paired_contract'], formal_packet['paired_contract'])
        self.assertEqual(review_packet['availability_evidence'], formal_packet['availability_evidence'])
        self.assertEqual(review_packet['formalization'], target)
        self.assertIn(ORIGINAL, canonical(request_for(review_spec, review_packet)))
        review_job = fixture.op('enqueue', key='independent-review', spec=review_spec)['id']
        fixture.op('seal_batch', batch_id=batch)
        fixture.restart('semantic-review/v1')
        judgment = {'judgment': 'faithful', 'reason': 'Synthetic deterministic process fixture only.',
            'added_assumptions': [], 'omitted_assumptions': [], 'conflicts': [], 'unresolved_meaning': [],
            'mapping_checks': [{'segment': 0, 'judgment': 'faithful', 'reason': 'Fixed offline response.'}]}
        review = fixture.invoke('reviewer', {'status': 'final', 'review': judgment})
        self.assertTrue(review['accepted'], review)
        retained = fixture.op('get_artifact', artifact_id=review['artifact_id'])
        self.assertEqual(retained['body']['formalization_id'], target['id'])
        self.assertNotEqual(retained['body']['formalizer_id'], retained['body']['reviewer_id'])
        self.assertEqual(retained['body']['actual_independent_model_review'], 'UNVERIFIED')
        assessment = fixture.op('assess_meaning_review', key='owned-paired-assessment', formalization_id=target['id'])
        self.assertEqual(assessment['body']['independent_semantic_review'], 'SATISFIED', assessment['body'])
        status = fixture.op('inspect_meaning_review', assessment_id=assessment['id'])
        self.assertTrue(status['current'])
        self.assertFalse(status['scientific_readiness'])
        inventory, refs = fixture.broker._meaning_inventory(target)
        self.assertEqual(inventory['policy']['paired_contract'], CONTRACT)
        self.assertEqual([job['id'] for job in inventory['jobs']], [review_job])
        self.assertEqual(len(inventory['jobs'][0]['calls']), 1)
        self.assertIsNotNone(inventory['jobs'][0]['calls'][0]['invocation']['result_id'])
        epoch = fixture.op('inspect_research_epoch', epoch_id=fixture.epoch)
        self.assertEqual(len(epoch['budget_overlay']['calls']), 2)
        self.assertEqual(sum(item['allocated_tokens'] for item in epoch['budget_overlay']['calls']), 160000)
        self.assertEqual(epoch['usage']['calls'], 2)
        # Same real retained target and current independent process assessment;
        # no data-use or source/meaning inspector is mocked for computation.
        compiled = fixture.broker.compile_paired(fixture.broker.admin_token, formalization_id=target['id'],
            feature_certificate_id=fixture.feature['id'], as_of=fixture.end, max_steps=max_steps)
        self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'])
        with patch.object(paired_composition, 'IDEA_ID', fixture.idea['id']):
            composition = fixture.broker.certify_paired_composition(fixture.broker.admin_token, compiled_id=compiled['id'])
        self.assertEqual(composition['body']['status'], 'CERTIFIED', composition['body'])
        executed = fixture.broker.execute_paired(fixture.broker.admin_token, compiled_id=compiled['id'],
            meaning_assessment_id=assessment['id'], composition_id=composition['id'])
        self.assertEqual(executed['body']['status'], expected_status, executed['body'])
        result = executed['body']['result']
        processed = result['report']['processed_case_count']
        self.assertEqual(executed['body']['verification']['result']['checked_cases'], processed)
        case_bytes = fixture.broker._read_blob_bytes(result['case_blob']['sha256'])
        self.assertEqual(len(case_bytes.splitlines()), processed)
        self.assertIn(result['case_blob']['sha256'], executed['blob_refs'])
        if expected_status == 'RESOURCE_STOP':
            self.assertGreater(processed, 0)
            self.assertLess(processed, grid_bars)
            self.assertFalse(result['report']['processing_complete'])
            self.assertEqual(result['report']['primitive_steps'], max_steps)
            self.assertEqual(result['contrast']['status'], 'RESOURCE_STOP')
            self.assertIsNone(executed['body']['independent_original_audit'])
        else:
            self.assertEqual(processed, grid_bars)
            self.assertEqual(executed['body']['independent_original_audit']['result']['checked_cases'], grid_bars)
        self.assertFalse(executed['body']['scientific_readiness'])
        self.assertIn(target['id'], executed['exposure'])
        fixture.op('revoke_research_epoch_budget', epoch_id=fixture.epoch)
        self.assertTrue(fixture.op('inspect_research_epoch', epoch_id=fixture.epoch)['budget_overlay']['revoked'])


if __name__ == '__main__':
    unittest.main()
