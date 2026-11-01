"""Independent D094 host/slot boundaries on synthetic metadata only.

Budget-unit fixtures use a real temporary spend ledger and SQLite inventory;
their source qualifier and packet loader are explicit stubs, not source or
scientific qualification. Separate real Broker checks exercise owned records.
"""
from copy import deepcopy
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from trading_researcher import openai_provider as openai
from trading_researcher import paired_budget as budget
from trading_researcher.auxiliary import request_for
from trading_researcher.auxiliary_views import PROFILE as VIEW
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.errors import Denied, Conflict
from trading_researcher.meaning_reviews import PROMPT, PROTOCOL
from trading_researcher.paired_broker import PairedBroker
from trading_researcher.paired_development import CONTRACT
from trading_researcher.paired_research import availability_packet, PairedResearch
from trading_researcher.research_calls import ResearchCalls
from trading_researcher.features import PROFILE as FEATURE_PROFILE, SCOPE
from test_paired_development_adversarial import boundary_rows


REJECTIONS = (Invalid, Denied, Conflict)


def role_profile(kind):
    review = kind == 'semantic-review/v1'
    config = openai.configuration(input_token_limit=76000 if review else 62000,
                                  output_token_limit=4000 if review else 18000)
    config.update(reasoning_effort='low' if review else 'high', source_presentation=VIEW)
    return {'model': openai.MODEL, 'prompt_version': PROTOCOL if review else 'paired-host-fixture/1',
        'prompt': PROMPT if review else 'Preserve the full original idea.' + openai.COMPACT_OUTPUT_SUFFIX,
        'generation_parameters': {'openai_responses': config},
        'max_output_tokens': 4000 if review else 18000,
        'call_timeout_seconds': 360, 'max_retries': 0}


class BudgetHost:
    PAIRED_RUNTIME = True
    _effective_research_profile = ResearchCalls._effective_research_profile

    def __init__(self, root):
        self.directory = Path(root) / 'registry'
        self.directory.mkdir()
        self.now = 1700000000
        self.ledger = openai.SpendLedger(Path(root) / 'ledger.sqlite3', 5000000000)
        config = role_profile('formalization/v1')['generation_parameters']['openai_responses']
        self._provider_routes = {openai.MODEL: {'provider': 'openai', 'config': config,
            'budget_file': str(Path(root) / 'ledger.sqlite3'), 'key_file': str(Path(root) / 'absent-key')}}
        self._db = sqlite3.connect(':memory:')
        self._db.execute('CREATE TABLE research_calls(id TEXT,epoch_id TEXT)')
        self._db.execute('CREATE TABLE job_specs(id TEXT,envelope TEXT)')
        self._db.execute('CREATE TABLE jobs(id TEXT,state TEXT,result_id TEXT)')
        self._paired_require_qualification = Mock(return_value=None)
        self._paired_source_identity = Mock(return_value={'synthetic.py': 'a' * 64})
        self._deny_final_calibration_ancestry = Mock()
        self._artifact = Mock(return_value={'id': budget.IDEA})
        self.context = {'artifact_ids': [budget.IDEA]}
        self.profile = {'model': openai.MODEL, 'prompt_version': 'paired-epoch-fixture/1',
            'mode': 'live', 'currency': 'USD', 'max_calls': 2, 'max_tokens': 160000,
            'max_cost_units': 600000000, 'max_seconds': 1800, 'call_timeout_seconds': 360,
            'max_output_tokens': 18000, 'max_retries': 0, 'tools': [],
            'prompts': {'first': 'Unused registered perspective one.', 'second': 'Unused perspective two.'},
            'generation_parameters': {'openai_responses': deepcopy(config)}}
        self.epoch = {'id': 'epoch', 'request_key': 'paired-once', 'created_at': self.now,
            'request': {'profile': self.profile, 'budget_overlay': budget.POLICY,
                        'context_id': 'context', 'workers': ['first', 'second']}}

    def _epoch(self, identity):
        assert identity == self.epoch['id']
        return self.epoch

    def _now(self):
        return self.now

    def _auxiliary_packet_for_spec(self, spec):
        return {'schema': 'formalization-input/1' if spec['kind'] == 'formalization/v1'
                else 'semantic-review-input/1', 'synthetic_complete_packet': spec['kind']}

    def job(self, kind='formalization/v1'):
        return {'id': kind, 'spec': {'kind': kind, 'research_epoch_id': self.epoch['id'],
            'allowed_workers': ['formalizer' if kind == 'formalization/v1' else 'independent-reviewer'],
            'max_attempts': 1, 'research_call_profile': role_profile(kind),
            'research_inputs': {'paired_contract': CONTRACT, 'feature_certificate_id': 'certificate',
                               'idea_id': budget.IDEA}}}

    def claim(self):
        budget.validate(self, self.context, self.profile, budget.POLICY)
        budget.claim(self, self.epoch)

    def reserve(self, kind='formalization/v1', identity='first-call', input_bound=None, **changes):
        job = self.job(kind)
        inputs, outputs = (62000, 18000) if kind == 'formalization/v1' else (76000, 4000)
        inputs = inputs if input_bound is None else input_bound
        args = {'input_bound': inputs, 'output_bound': outputs, 'cost': openai.cost_bound(inputs, outputs),
                'request': request_for(job['spec'], self._auxiliary_packet_for_spec(job['spec']))}
        return budget.reserve(self, self.epoch, job, identity, **{**args, **changes})

    def committed(self, identity):
        # Explicit simulation of the later registry commit, never a real registry.
        self._db.execute('INSERT INTO research_calls VALUES(?,?)', (identity, self.epoch['id']))


class PairedBudgetBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.host = BudgetHost(self.temp.name)
        self.addCleanup(self.host._db.close)

    def test_valid_roles_use_the_actual_effective_profile_prompt_representation(self):
        for kind in ('formalization/v1', 'semantic-review/v1'):
            job = self.host.job(kind)
            effective = self.host._effective_research_profile(job)
            self.assertNotIn('prompt', effective)
            self.assertEqual(effective['prompts'][job['spec']['allowed_workers'][0]],
                             job['spec']['research_call_profile']['prompt'])
            self.host.claim() if kind == 'formalization/v1' else None
            self.host.reserve(kind, identity=kind)
            self.host.committed(kind)

    def test_exact_slots_are_nonrefundable_and_no_third_stage_exists(self):
        self.host.claim()
        self.host.reserve(input_bound=1)
        self.host.committed('first-call')
        state = budget.inspect(self.host, self.host.epoch)
        self.assertEqual(state['calls'][0]['allocated_tokens'], 80000)
        self.assertEqual(state['calls'][0]['allocated_cost'], 335000000)
        with self.assertRaises(REJECTIONS):
            self.host.reserve(identity='formalization-retry')
        self.host.reserve('semantic-review/v1', identity='review-call', input_bound=1)
        self.host.committed('review-call')
        state = budget.inspect(self.host, self.host.epoch)
        self.assertEqual(sum(item['allocated_tokens'] for item in state['calls']), 160000)
        self.assertEqual(sum(item['allocated_cost'] for item in state['calls']), 565000000)
        with self.assertRaises(REJECTIONS):
            self.host.reserve('semantic-review/v1', identity='review-retry')
        with self.assertRaises(REJECTIONS):
            budget._slot(self.host.epoch, self.host.job('research-record/v1'), state['calls'])

    def test_wrong_allocation_or_packet_cannot_consume_a_slot(self):
        self.host.claim()
        for changes in ({'input_bound': 62001}, {'output_bound': 17999}, {'cost': 0},
                        {'request': {'synthetic_incomplete_packet': True}}):
            with self.subTest(changes=changes), self.assertRaises(REJECTIONS):
                self.host.reserve(**changes)
        for changes in ({'model': 'another-model'}, {'max_retries': 1},
                        {'prompt_version': 'wrong-review-version'}, {'max_output_tokens': 3999}):
            profile = self.host._effective_research_profile(self.host.job('semantic-review/v1'))
            profile.update(changes)
            with self.subTest(changes=changes), self.assertRaises(REJECTIONS):
                budget._call_settings(profile, 'semantic-review/v1')
        self.assertEqual(budget.inspect(self.host, self.host.epoch)['calls'], [])

    def test_external_fence_survives_registry_rollback_restart_and_revocation(self):
        self.host.claim()
        self.host.reserve()
        # No registry commit: an external slot cannot be recovered by restoring
        # an earlier inventory or by returning a lower reported usage.
        with self.assertRaises(REJECTIONS):
            self.host.reserve('semantic-review/v1', identity='after-rollback')
        with self.assertRaises(REJECTIONS):
            budget.claim(self.host, self.host.epoch)
        self.host.committed('first-call')
        self.host.ledger = openai.SpendLedger(Path(self.temp.name) / 'ledger.sqlite3', 5000000000)
        self.assertEqual(len(budget.inspect(self.host, self.host.epoch)['calls']), 1)
        result = budget.revoke(self.host, self.host.epoch)
        self.assertTrue(result['pending_calls_still_require_settlement'])
        with self.assertRaises(REJECTIONS):
            self.host.reserve('semantic-review/v1', identity='after-revoke')
        self.assertTrue(budget.inspect(self.host, self.host.epoch)['revoked'])
        self.assertEqual(len(budget.inspect(self.host, self.host.epoch)['calls']), 1)

    def test_cross_registry_source_change_and_pending_spending_fail_closed(self):
        self.host.claim()
        original = self.host.directory
        self.host.directory = Path(self.temp.name) / 'other-registry'
        with self.assertRaises(REJECTIONS):
            budget.inspect(self.host, self.host.epoch)
        self.host.directory = original
        self.host._paired_source_identity.return_value = {'synthetic.py': 'b' * 64}
        with self.assertRaises(REJECTIONS):
            self.host.reserve()
        self.host._paired_source_identity.return_value = {'synthetic.py': 'a' * 64}
        self.host.ledger.reserve('f' * 64, 1, key='unsettled-external-request')
        with self.assertRaises(REJECTIONS):
            self.host.reserve()
        self.assertEqual(budget.inspect(self.host, self.host.epoch)['calls'], [])

    def test_epoch_bounds_original_selection_and_remaining_time_are_immutable(self):
        for changes in ({'max_tokens': 160001}, {'max_cost_units': 600000001}, {'max_calls': 3},
                        {'max_seconds': 1801}, {'max_retries': 1}, {'mode': 'fixture'},
                        {'model': 'different-model'}, {'tools': [{}]}):
            with self.subTest(changes=changes), self.assertRaises(REJECTIONS):
                budget.validate(self.host, self.host.context, {**self.host.profile, **changes}, budget.POLICY)
        with self.assertRaises(REJECTIONS):
            budget.validate(self.host, {'artifact_ids': ['other-idea']}, self.host.profile, budget.POLICY)
        self.host.claim()
        self.host.now += 1441
        with self.assertRaises(REJECTIONS):
            self.host.reserve()
        self.assertEqual(budget.inspect(self.host, self.host.epoch)['calls'], [])

    def test_null_or_incomplete_result_cannot_open_reviewer_stage(self):
        self.host.claim()
        job = self.host.job('formalization/v1')
        self.host._db.execute('INSERT INTO job_specs VALUES(?,?)', ('formal-job', canonical(job['spec'])))
        self.host._db.execute('INSERT INTO jobs VALUES(?,?,?)', ('formal-job', 'completed', 'target'))
        review = self.host.job('semantic-review/v1')['spec']
        review['research_inputs']['formalization_id'] = 'target'
        for candidate, state in ((None, 'STRUCTURE_CHECKED'), ({}, 'RETAINED_GAP')):
            self.host._artifact.return_value = {'body': {'candidate': candidate, 'assessment': {'status': state}}}
            with self.subTest(candidate=candidate, state=state), self.assertRaises(REJECTIONS):
                budget.validate_job(self.host, self.host.epoch, review)


def availability_fixture():
    request, catalog, rows, definitions = boundary_rows()
    universe = {**request['universe'], 'instruments': request['universe']['pair']}
    universe.pop('pair')
    definition = {'id': 'definitions', 'creator': 'controller', 'origin': 'source',
        'data_class': 'development', 'body': {'schema': 'feature-definitions/1',
        'input_refs': ['snapshot', 'catalog'], 'definitions': definitions, 'parameters': {'delay_seconds': 900}}}
    records = {
        'certificate': {'id': 'certificate', 'creator': 'controller', 'origin': 'controller',
            'data_class': 'development', 'authority': SCOPE['authority'], 'body': {
            'schema': 'feature-certificate/1', 'profile': FEATURE_PROFILE, 'status': 'CERTIFIED',
            'data_snapshot_id': 'snapshot', 'definitions_id': 'definitions', 'footprint': {},
            'replay': {'row_blobs': []}}},
        'snapshot': {'id': 'snapshot', 'creator': 'controller', 'origin': 'source', 'data_class': 'development',
            'body': {'schema': 'data-snapshot/1', 'catalog_id': 'catalog', 'catalog_hash': digest(catalog),
                'manifest': {'partition': 'development', 'availability': {'basis': 'assumed'}, 'universe': universe}}}}
    ids = ['certificate', 'snapshot', 'catalog', 'definitions', 'idea']
    target = {'id': 'target', 'job_id': 'original-job', 'source_refs': ids, 'body': {
        'idea_id': 'idea', 'authorization_snapshot': ids, 'candidate': {'test_universe': {
            **request['universe'], 'data_snapshot_ref': 'snapshot'}, 'feature_refs': sorted(catalog)}}}
    host = SimpleNamespace(_artifact=lambda identity: deepcopy(records[identity]),
        _context=lambda identity: {'artifact_ids': ids}, _job=lambda identity: {'spec': {'context_id': 'original'}},
        _feature_certificate_status=Mock(return_value={'status': 'CURRENT'}),
        _load_reference_data=Mock(return_value={'data_snapshot_ref': 'snapshot', 'catalog': catalog, 'rows': rows}),
        _require_usable_dependencies=Mock())
    return host, {'artifact_ids': ids}, {'feature_certificate_id': 'certificate'}, definition, records, target


class PairedAvailabilityBoundaryTests(unittest.TestCase):
    def test_both_roles_receive_identical_exact_evidence_without_sample_values(self):
        host, context, inputs, definition, records, target = availability_fixture()
        formal = availability_packet(host, context, inputs, 'catalog', [definition])
        review = availability_packet(host, {'artifact_ids': [*context['artifact_ids'], 'target']},
                                     inputs, 'catalog', [definition], target)
        self.assertEqual(canonical(formal), canonical(review))
        evidence = formal['availability_evidence']
        self.assertEqual(evidence['universe']['instruments'], ['BTCUSDT', 'ETHUSDT'])
        self.assertEqual(evidence['summary']['checked_rows'], 16)
        self.assertFalse(evidence['scientific_readiness'])
        self.assertNotIn('rows', evidence)

    def test_wrong_owner_protected_missing_context_and_unrelated_review_deny_before_reads(self):
        for mutation in ('creator', 'authority', 'protected', 'missing_context', 'unrelated_review', 'snapshot'):
            host, context, inputs, definition, records, target = availability_fixture()
            if mutation == 'creator': records['certificate']['creator'] = 'model-worker'
            if mutation == 'authority': records['certificate']['authority'] = 'asserted_by_model'
            if mutation == 'protected': records['snapshot']['body']['manifest']['partition'] = 'assessment'
            if mutation == 'missing_context': context['artifact_ids'].remove('snapshot')
            if mutation == 'unrelated_review': context['artifact_ids'].append('private-extra')
            if mutation == 'snapshot': target['body']['candidate']['test_universe']['data_snapshot_ref'] = 'hidden'
            with self.subTest(mutation=mutation), self.assertRaises(REJECTIONS):
                availability_packet(host, context, inputs, 'catalog', [definition], target)
            host._feature_certificate_status.assert_not_called()
            host._load_reference_data.assert_not_called()

    def test_member_timing_identity_and_revocation_gaps_are_not_nominal_delay_proofs(self):
        for mutation in ('late', 'catalog', 'revoked', 'candidate_members', 'candidate_refs'):
            host, context, inputs, definition, records, target = availability_fixture()
            if mutation == 'late':
                row = host._load_reference_data.return_value['rows'][1]
                next(iter(row['features'].values()))['available_at'] += 1
            if mutation == 'catalog': host._load_reference_data.return_value['catalog'] = {}
            if mutation == 'revoked': host._feature_certificate_status.return_value = {'status': 'REVOKED'}
            if mutation == 'candidate_members': target['body']['candidate']['test_universe']['pair'].append('SOLUSDT')
            if mutation == 'candidate_refs': target['body']['candidate']['feature_refs'].append('SOLUSDT.close@1')
            with self.subTest(mutation=mutation), self.assertRaises(REJECTIONS):
                availability_packet(host, context, inputs, 'catalog', [definition], target)


class PairedActualHostBoundaryTests(unittest.TestCase):
    def test_operator_only_qualification_and_no_generic_source_forgery(self):
        with tempfile.TemporaryDirectory() as root, closing(PairedBroker(Path(root) / 'registry')) as broker:
            worker = broker.call(broker.admin_token, 'register_worker', name='ordinary-worker',
                role='discovery', capabilities=['research-record/v1'])['token']
            with self.assertRaises(REJECTIONS):
                broker.certify_paired(worker)
            for schema in ('paired-reference-certificate/1', 'paired-source-package/1',
                           'paired-compiled-hypothesis/1', 'paired-reference-execution/1'):
                with self.subTest(schema=schema), self.assertRaises(REJECTIONS):
                    broker.call(broker.admin_token, 'add_source', body={'schema': schema}, data_class='development')
            with self.assertRaises(REJECTIONS):
                broker._paired_require_qualification()
            certificate = broker.certify_paired(broker.admin_token)
            self.assertEqual(certificate['body']['status'], 'CERTIFIED')
            selected, bundle = broker._paired_require_qualification()
            self.assertEqual(selected['id'], certificate['id'])
            self.assertFalse(certificate['body']['scientific_readiness'])
            changed = deepcopy(bundle)
            changed['trading_researcher/paired_development.py'] += b'\n# altered retained implementation\n'
            with patch('trading_researcher.paired_runtime.read_bundle', return_value=changed), self.assertRaises(REJECTIONS):
                broker._paired_require_qualification()
            evidence = broker.call(broker.admin_token, 'add_source',
                body={'defect': 'Independent synthetic source revocation fixture.'}, data_class='development')
            package_id = certificate['body']['source_package_id']
            revoked = broker.call(broker.admin_token, 'revoke_dependency', key='paired-package-defect',
                dependency_id=package_id, reason='Synthetic owned-source invalidation.', evidence_refs=[evidence['id']])
            self.assertIn(certificate['id'], revoked['body']['affected_artifact_ids'])
            self.assertEqual(broker.call(broker.admin_token, 'inspect_dependency_use',
                artifact_id=certificate['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
            with self.assertRaises(REJECTIONS):
                broker._paired_require_qualification()
            with self.assertRaises(REJECTIONS):
                broker.call(worker, 'inspect_dependency_use', artifact_id=certificate['id'])
            self.assertEqual(broker.call(broker.admin_token, 'get_artifact', artifact_id=certificate['id']), certificate)

    def test_revocation_tracks_equal_footprints_and_typed_edges_not_generic_exposure(self):
        with tempfile.TemporaryDirectory() as root, closing(PairedBroker(Path(root) / 'registry')) as broker:
            def owned(body, *, origin='controller', refs=()):
                with broker._transaction():
                    return broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                        'origin': origin, 'data_class': 'operations', 'body': body, 'source_refs': list(refs),
                        'exposure': list(refs), 'authority': 'synthetic_typed_graph_fixture_only'})
            body = {'schema': 'paired-source-package/1', 'footprint': {'synthetic.py': 'a' * 64}, 'created_at': 1}
            first = owned(body)
            alias = owned({**body, 'created_at': 2})
            changed = owned({**body, 'created_at': 3, 'footprint': {'synthetic.py': 'b' * 64}})
            certificate = owned({'schema': 'paired-reference-certificate/1', 'source_package_id': alias['id']})
            generic = owned({'schema': 'unrelated-observation/1'}, refs=[first['id']])
            evidence = broker.call(broker.admin_token, 'add_source', body={'defect': 'Synthetic only'}, data_class='development')
            broker.call(broker.admin_token, 'revoke_dependency', key='footprint', dependency_id=first['id'],
                reason='Synthetic equal-footprint revocation', evidence_refs=[evidence['id']])
            for artifact in (first, alias, certificate):
                self.assertEqual(broker.call(broker.admin_token, 'inspect_dependency_use',
                    artifact_id=artifact['id'])['status'], 'INVALIDATED_BY_DEPENDENCY')
            self.assertEqual(broker.call(broker.admin_token, 'inspect_dependency_use',
                artifact_id=changed['id'])['status'], 'NOT_REVOKED')
            self.assertEqual(broker.call(broker.admin_token, 'inspect_dependency_use',
                artifact_id=generic['id'])['status'], 'UNKNOWN_BINDING')


if __name__ == '__main__':
    unittest.main()
