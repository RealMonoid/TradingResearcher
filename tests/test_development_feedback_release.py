"""Independent publication boundary tests, not model-review/certification evidence.

Discovery, formalization, storage, publication, grants and context access use the
real Broker. Compiled/execution/assessment envelopes are explicit synthetic
owned metadata; only the two pre-existing assessment inspectors are mocked.
"""
from copy import deepcopy
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.outcomes import materialize_reference, reference_contrast
from trading_researcher.storage import restore_bundle
import test_development_feedback as cohort_tests
import test_outcomes as outcome_tests


REJECTIONS = (Invalid, Conflict, Denied)
AUTHORITY = 'descriptive_development_feedback_only'
COMPUTATION = 'descriptive_reference_computation_only'


class DevelopmentFeedbackReleaseTests(unittest.TestCase):
    def setUp(self):
        self.case = cohort_tests.DevelopmentFeedbackCohortTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.broker = self.case.broker
        self.fixture = self.case.fixture
        self.op = self.fixture.op
        self.op('release_batch', batch_id=self.case.batch, target_epoch=2)
        request, catalog, rows = outcome_tests.OutcomeTests.example()
        request['condition_program']['expression']['value'] = False
        self.catalog = self.op('add_source', body={'schema': 'feature-catalog/1', 'features': catalog},
            data_class='development')
        self.snapshot = self.save({'schema': 'data-snapshot/1', 'catalog_id': self.catalog['id'],
            'manifest': {'partition': 'development', 'universe': request['universe']},
            'scientific_readiness': False}, origin='source', refs=[self.catalog['id']])
        idea = self.case.root_results[0]
        context = self.op('create_context', role='formalizer', epoch=2,
            artifact_ids=[idea, self.catalog['id'], self.snapshot['id']])['id']
        auxiliary_epoch = self.op('create_research_epoch', key='feedback-formalizer',
            context_id=self.fixture.context, workers=['first', 'second'],
            profile={**self.fixture.profile, 'max_calls': 4, 'max_tokens': 80000})['id']
        token, job, lease = self.case.auxiliary_job('feedback-formalizer', auxiliary_epoch, context,
            {'idea_id': idea, 'catalog_id': self.catalog['id'], 'definition_ids': []})
        paths = ['/scope_ast/expression/value', '/condition_ast/expression/value', '/horizons/outcome_bars']
        candidate = {'schema': 'hypothesis-exec/1', 'idea_ref': idea, 'claim_kind': 'difference',
            'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'USD', 'weighting': 'equal_rows',
                'missingness': 'scope-true-outcome-observed/1',
                'condition_unknown': 'exclude-from-condition-retain-in-scope', 'nuisance_fit': 'none',
                'direction': 'positive'},
            'scope_ast': request['scope_program'], 'condition_ast': request['condition_program'],
            'outcome': {'program': request['outcome_program'], 'scale': 'quantity'},
            'comparator': {'kind': 'whole_scope'}, 'horizons': {'grid_seconds': 900, 'outcome_bars': 1},
            'test_universe': {**request['universe'], 'data_snapshot_ref': self.snapshot['id']},
            'parameter_origins': [{'path': path, 'basis': 'preexisting_specification', 'source_refs': [],
                'rationale': 'Synthetic publication boundary input; no actual research meaning claim.'} for path in paths],
            'feature_refs': ['price@1']}
        semantic = {'status': 'equivalent', 'segments': [{'text': self.broker._artifact(idea)['body']['content']['text'],
            'path': '/estimand', 'interpretation': 'Synthetic test assertion, not an actual model meaning review.'}],
            'differences': []}
        packet = self.broker.call(token, 'auxiliary_input', lease=lease)
        profile = self.broker._job(job)['spec']['research_call_profile']
        wire = {key: profile[key] for key in ('model', 'prompt_version', 'generation_parameters')}
        wire.update(tools=[], messages=[{'role': 'system', 'content': profile['prompt']},
            {'role': 'user', 'content': canonical(packet)}])
        call = self.broker.call(token, 'reserve_research_call', lease=lease, key='synthetic-formalization',
            request=wire, input_token_bound=16000, output_token_limit=64, cost_bound_units=0)
        self.broker.call(token, 'finish_research_call', lease=lease, call_id=call['call_id'],
            response={'status': 'completed', 'output': {'status': 'final', 'candidate': candidate, 'semantic_report': semantic}},
            usage={'input_tokens': 10, 'output_tokens': 20, 'cost_units': 0})
        saved = self.broker.call(token, 'record_formalization', lease=lease, idea_id=idea,
            catalog_id=self.catalog['id'], candidate=candidate, semantic_report=semantic, provider_call_id=call['call_id'])
        self.assertEqual(saved['assessment']['status'], 'STRUCTURE_CHECKED')
        self.assertTrue(self.broker.call(token, 'submit', lease=lease, artifact_id=saved['id'])['accepted'])
        self.formalization = self.broker._artifact(saved['id'])
        self.fixture.now = 2701
        package = self.save({'schema': 'binding-source-package/1', 'footprint': {'fixture.py': '1' * 64}},
            data_class='operations', authority='retained_source_not_certified')
        reference_package = self.save({'schema': 'reference-source-package/1', 'footprint': {'fixture.py': '2' * 64}},
            data_class='operations', authority='retained_source_not_certified')
        reference = self.save({'schema': 'implementation-certificate/1', 'source_package_id': reference_package['id']},
            data_class='operations', authority='implementation_conformance_only', refs=[reference_package['id']])
        definition = self.save({'schema': 'feature-definitions/1',
            'input_refs': [self.snapshot['id'], self.catalog['id']]}, origin='source',
            refs=[self.snapshot['id'], self.catalog['id']])
        feature = self.save({'schema': 'feature-certificate/1', 'data_snapshot_id': self.snapshot['id'],
            'definitions_id': definition['id']}, refs=[self.snapshot['id'], definition['id']])
        request.update(candidate_ref=self.formalization['id'], data_snapshot_ref=self.snapshot['id'])
        compilation = {'request': request, 'row_window': request['universe']}
        self.compiled = self.save({'schema': 'compiled-hypothesis/1', 'status': 'COMPILED',
            'data_snapshot_id': self.snapshot['id'], 'source_package_id': package['id'],
            'dependency_arguments': {'formalization_id': self.formalization['id'],
                'feature_certificate_id': feature['id'], 'reference_certificate_id': reference['id']},
            'compilation': compilation, 'scientific_readiness': False}, authority=COMPUTATION,
            refs=[self.formalization['id'], self.snapshot['id'], package['id'], reference['id'], feature['id']])
        report = materialize_reference(request, catalog, rows)
        case_bytes = ''.join(canonical(case) + '\n' for case in report['cases']).encode()
        with self.broker._transaction():
            descriptor = self.broker._stage_blob_stream(BytesIO(case_bytes))
            self.broker._register_blob(descriptor)
        result = {'report': {key: value for key, value in report.items() if key != 'cases'},
            'contrast': reference_contrast(report), 'case_blob': descriptor,
            'rows': {'sha256': '3' * 64, 'size': 1}, 'compilation_hash': digest(compilation), 'scientific_readiness': False}
        verification = {'mode': 'verify', 'result': {'schema': 'bound-case-verification/1',
            'result_hash': digest(result), 'compilation_hash': result['compilation_hash'], 'case_blob': descriptor,
            'checked_cases': report['processed_case_count'], 'scientific_readiness': False}}
        self.execution = self.save({'schema': 'reference-execution/1', 'status': 'DESCRIPTIVE_EXECUTION',
            'compiled_id': self.compiled['id'], 'data_snapshot_id': self.snapshot['id'],
            'result': result, 'verification': verification, 'scientific_readiness': False}, authority=COMPUTATION,
            refs=[self.compiled['id']], blobs=[descriptor['sha256']])
        self.meaning = self.save({'schema': 'semantic-review-assessment/1', 'formalization_id': self.formalization['id'],
            'status': 'INDEPENDENT_REVIEW_SATISFIED', 'independent_semantic_review': 'SATISFIED',
            'scientific_readiness': False}, data_class='work_product', refs=[self.formalization['id']],
            authority='meaning_review_process_not_scientific_evidence')
        self.data_use = self.save({'schema': 'data-use-assessment/1', 'compiled_id': self.compiled['id'],
            'status': 'QUALIFIED_EXPLORATION', 'scientific_readiness': False}, refs=[self.compiled['id']],
            authority='qualified_exploration_not_scientific_evidence')
        self.request = {'root_epoch_id': self.case.epoch, 'execution_id': self.execution['id'],
            'data_use_assessment_id': self.data_use['id'], 'meaning_review_assessment_id': self.meaning['id'], 'target_epoch': 7}
        self.data_patch = patch.object(self.broker, '_inspect_data_use', return_value={
            'assessment_id': self.data_use['id'], 'compiled_id': self.compiled['id'],
            'status': 'QUALIFIED_EXPLORATION', 'qualified_exploration_data_use': 'SATISFIED', 'scientific_readiness': False})
        self.meaning_patch = patch.object(self.broker, '_inspect_meaning_review', return_value={
            'assessment_id': self.meaning['id'], 'current': True, 'status': 'CURRENT',
            'independent_semantic_review': 'SATISFIED', 'scientific_readiness': False})
        self.data_inspector = self.data_patch.start()
        self.meaning_inspector = self.meaning_patch.start()
        self.addCleanup(self.data_patch.stop)
        self.addCleanup(self.meaning_patch.stop)

    def save(self, body, *, origin='controller', data_class='development', authority='synthetic-boundary-fixture-only',
             refs=(), blobs=()):
        exposure = set(refs)
        for ref in refs:
            exposure.update(self.broker._artifact(ref)['exposure'])
        with self.broker._transaction():
            return self.broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': origin, 'data_class': data_class, 'authority': authority, 'source_refs': sorted(refs),
                'exposure': sorted(exposure), 'blob_refs': list(blobs),
                'body': {'created_at': self.broker._now(), **deepcopy(body)}})

    def publish(self, **changes):
        return self.op('publish_development_feedback', **{**self.request, **changes})

    def snapshot_counts(self):
        return {table: self.broker._db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
            for table in ('artifacts', 'research_records', 'events', 'releases', 'contexts')}

    def context(self, identities, epoch=7, research_time=None):
        args = {'role': 'discovery', 'epoch': epoch, 'artifact_ids': identities}
        if research_time is not None:
            args['research_time'] = research_time
        return self.op('create_context', **args)

    def test_exact_atomic_snapshot_indexing_and_explicit_manifest_access(self):
        from trading_researcher.development_feedback import collect_cohort
        before = collect_cohort(self.broker, self.case.epoch)
        job_states = self.case.job_states()
        generic_releases = self.broker._db.execute('SELECT COUNT(*) FROM releases').fetchone()[0]
        result = self.publish()
        self.assertEqual(set(result), {'manifest_id', 'observation_id', 'experience_id', 'grant_id'})
        self.assertEqual(len(set(result.values())), 4)
        records = {name: self.broker._artifact(identity) for name, identity in result.items()}
        manifest = records['manifest_id']
        self.assertEqual(manifest['body']['schema'], 'development-feedback-manifest/1')
        self.assertEqual(manifest['body']['request'], self.request)
        self.assertEqual(manifest['body']['cohort'], before)
        for record in records.values():
            self.assertEqual((record['creator'], record['origin'], record['data_class'], record['authority']),
                ('controller', 'controller', 'development', AUTHORITY))
            self.assertTrue(set(before['artifact_ids']) <= set(record['exposure']))
        self.assertFalse(manifest['body']['scientific_readiness'])
        self.assertEqual(records['observation_id']['body']['kind'], 'observation')
        self.assertEqual(records['experience_id']['body']['kind'], 'research_experience')
        journal = self.op('inspect_memory', view='journal', scope={'manifest_id': manifest['id']})['records']
        experience = self.op('inspect_memory', view='research_experience', scope={'manifest_id': manifest['id']})['records']
        self.assertEqual({value['id'] for value in journal}, {result['observation_id'], result['experience_id']})
        self.assertEqual([value['id'] for value in experience], [result['experience_id']])
        self.assertEqual(self.op('inspect_memory', view='market_model')['records'], [])
        selected = [result[key] for key in ('manifest_id', 'observation_id', 'experience_id')]
        context = self.context(selected)
        self.assertEqual(set(context['artifact_ids']), set(selected))
        self.assertIn(result['grant_id'], context['exposure'])
        for identity in (self.execution['id'], self.compiled['id'], result['grant_id']):
            with self.subTest(identity=identity), self.assertRaises(Denied):
                self.context([identity])
        self.assertEqual(self.case.job_states(), job_states)
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM releases').fetchone()[0], generic_releases)

    def test_idempotency_input_binding_and_time_epoch_fences(self):
        published = self.publish()
        before = self.snapshot_counts()
        self.assertEqual(self.publish(), published)
        self.assertEqual(self.snapshot_counts(), before)
        with self.assertRaises(Conflict):
            self.publish(target_epoch=8)
        for epoch, when in ((6, 2701), (7, 2700)):
            with self.subTest(epoch=epoch, when=when), self.assertRaises(Denied):
                self.context([published['observation_id']], epoch=epoch, research_time=when)
        self.context([published['manifest_id']], epoch=7, research_time=2701)

    def test_operator_only_and_reserved_namespaces(self):
        with self.assertRaises(Denied):
            self.broker.call(self.fixture.tokens['first'], 'publish_development_feedback', **self.request)
        for schema in ('development-feedback-manifest/1', 'development-feedback-release/1'):
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                self.op('add_source', body={'schema': schema}, data_class='development')
        with self.assertRaises(REJECTIONS):
            self.publish(target_epoch=2)

    def test_stale_or_unqualified_assessments_and_altered_verification_fail_before_writes(self):
        before = self.snapshot_counts()
        for inspector, field, value in ((self.data_inspector, 'qualified_exploration_data_use', 'NOT_SATISFIED'),
                (self.meaning_inspector, 'current', False),
                (self.meaning_inspector, 'independent_semantic_review', 'NOT_SATISFIED')):
            original = deepcopy(inspector.return_value)
            inspector.return_value[field] = value
            with self.subTest(field=field), self.assertRaises(REJECTIONS):
                self.publish()
            self.assertEqual(self.snapshot_counts(), before)
            inspector.return_value = original
        original_lookup = self.broker._artifact
        def changed(identity):
            value = original_lookup(identity)
            if identity == self.execution['id']:
                value['body']['verification']['result']['result_hash'] = '0' * 64
            return value
        with patch.object(self.broker, '_artifact', side_effect=changed), self.assertRaises(REJECTIONS):
            self.publish()
        self.assertEqual(self.snapshot_counts(), before)

    def test_publication_failure_rolls_back_all_artifacts_indexes_and_event(self):
        before = self.snapshot_counts()
        save = self.broker._save_artifact
        count = [0]
        def fail_after_manifest(envelope):
            if envelope.get('authority') == AUTHORITY:
                count[0] += 1
                if count[0] == 3:
                    raise OSError('Synthetic interruption after manifest and indexed observation')
            return save(envelope)
        with patch.object(self.broker, '_save_artifact', side_effect=fail_after_manifest), self.assertRaises(OSError):
            self.publish()
        self.assertEqual(count[0], 3)
        self.assertEqual(self.snapshot_counts(), before)
        self.publish()

    def test_unowned_protected_operational_and_malformed_evidence_is_typed_and_not_read(self):
        operational = self.op('add_source', body={'text': 'Synthetic uncontrolled operations observation'},
            data_class='operations')
        before = self.snapshot_counts()
        mutations = [
            lambda value: value.update(creator='unowned'),
            lambda value: value.update(data_class='assessment'),
            lambda value: value['exposure'].append(operational['id']),
            lambda value: value['body'].update(result=None),
            lambda value: value['body'].update(verification=None),
            lambda value: value['body']['verification'].update(result=[]),
        ]
        original_lookup = self.broker._artifact
        for index, mutate in enumerate(mutations):
            def changed(identity):
                value = original_lookup(identity)
                if identity == self.execution['id']:
                    mutate(value)
                return value
            with self.subTest(case=index), patch.object(self.broker, '_artifact', side_effect=changed), \
                    patch.object(self.broker, '_read_blob_bytes', side_effect=AssertionError('Rejected evidence read cases')) as read, \
                    self.assertRaises(REJECTIONS):
                self.publish()
            read.assert_not_called()
            self.assertEqual(self.snapshot_counts(), before)

    def test_revocation_stops_new_contexts_and_already_claimed_worker_reads(self):
        published = self.publish()
        context = self.context([published['manifest_id'], published['observation_id']])
        token = self.op('register_worker', name='feedback-reader', role='discovery', capabilities=['draft/v1'])['token']
        self.op('enqueue', key='feedback-reader', spec={'kind': 'draft/v1', 'context_id': context['id'],
            'purpose': 'Read explicitly authorized development feedback', 'allowed_workers': ['feedback-reader'],
            'max_attempts': 1, 'lease_seconds': 10, 'deadline': 2800, 'dependencies': []})
        lease = self.broker.call(token, 'claim')['lease']
        self.assertEqual(self.broker.call(token, 'read_artifact', lease=lease,
            artifact_id=published['manifest_id'])['id'], published['manifest_id'])
        defect = self.op('add_source', body={'text': 'Synthetic technical revocation evidence'}, data_class='development')
        self.op('revoke_dependency', key='feedback-defect', dependency_id=published['grant_id'],
            reason='Independent synthetic technical defect', evidence_refs=[defect['id']])
        with self.assertRaises(Denied):
            self.context([published['experience_id']])
        with self.assertRaises(Denied):
            self.broker.call(token, 'read_artifact', lease=lease, artifact_id=published['observation_id'])
        with self.assertRaises(Denied):
            self.broker.call(token, 'search_memory', lease=lease)
        self.assertEqual(self.broker._artifact(published['grant_id'])['body']['schema'], 'development-feedback-release/1')

    def test_unrelated_or_forged_records_never_obtain_the_feedback_grant(self):
        from trading_researcher.development_feedback import released_feedback
        result = self.publish()
        for body in (None, [], 'untyped'):
            unrelated = self.op('add_source', body=body, data_class='development')
            self.assertIsNone(released_feedback(self.broker, unrelated, 7, 2701))
        record = self.broker._artifact(result['observation_id'])
        for mutation in ('creator', 'authority', 'source_refs'):
            altered = deepcopy(record)
            altered.pop('id')
            altered[mutation] = [] if mutation == 'source_refs' else 'forged'
            with self.broker._transaction():
                forged = self.broker._save_artifact(altered)
            try:
                grant = released_feedback(self.broker, forged, 7, 2701)
            except REJECTIONS:
                continue
            self.assertIsNone(grant)

    def test_backup_restore_preserves_exact_feedback_and_narrow_context_grant(self):
        result = self.publish()
        root = Path(self.fixture.tmp.name)
        backup, restored = root / 'feedback-backup', root / 'feedback-restored'
        self.op('backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, self.broker.directory / 'operator.key')
        other = Broker(restored, clock=lambda: 2701)
        self.addCleanup(other.close)
        with patch.object(other, '_inspect_data_use', return_value=deepcopy(self.data_inspector.return_value)), \
                patch.object(other, '_inspect_meaning_review', return_value=deepcopy(self.meaning_inspector.return_value)):
            for identity in result.values():
                self.assertEqual(other._artifact(identity), self.broker._artifact(identity))
            context = other.call(other.admin_token, 'create_context', role='discovery', epoch=7,
                artifact_ids=[result['manifest_id'], result['experience_id']])
            self.assertIn(result['grant_id'], context['exposure'])
            with self.assertRaises(Denied):
                other.call(other.admin_token, 'create_context', role='discovery', epoch=7,
                    artifact_ids=[self.execution['id']])

    def test_manifest_exposes_exact_all_idea_gap_texts_including_blocked_attempt(self):
        from trading_researcher.development_feedback import collect_cohort
        context = self.op('create_context', role='formalizer', epoch=3,
            artifact_ids=[self.case.root_results[0], self.catalog['id'], self.snapshot['id']])['id']
        epoch = self.op('create_research_epoch', key='later-blocked-feedback-attempt',
            context_id=self.fixture.context, workers=['first', 'second'],
            profile={**self.fixture.profile, 'max_calls': 4, 'max_tokens': 80000})['id']
        token = self.op('register_worker', name='blocked-feedback-formalizer', role='formalizer',
            capabilities=['formalization/v1'])['token']
        spec = deepcopy(self.broker._job(self.formalization['job_id'])['spec'])
        spec.update(context_id=context, research_epoch_id=epoch, deadline=2800,
            allowed_workers=['blocked-feedback-formalizer'])
        self.op('enqueue', key='blocked-feedback-formalizer', spec=spec)
        lease = self.broker.call(token, 'claim')['lease']
        gap = self.case.retain_gap_and_block(token, lease)
        self.fixture.now = 2762
        cohort = collect_cohort(self.broker, self.case.epoch)
        expected = []
        for identity in cohort['artifact_ids']:
            artifact = self.broker._artifact(identity)
            body = artifact['body']
            if type(body) is dict and body.get('schema') == 'research-record/1' and body.get('kind') in ('idea', 'gap'):
                expected.append({key: artifact[key] for key in ('id', 'creator', 'authority', 'body', 'source_refs', 'exposure')})
        self.assertIn(gap, {value['id'] for value in expected})
        self.assertTrue(set(self.case.root_results) <= {value['id'] for value in expected})
        result = self.publish()
        manifest = self.broker._artifact(result['manifest_id'])
        self.assertEqual(manifest['body']['retained_research_records'], expected)
        reader_context = self.context([manifest['id']])
        reader = self.op('register_worker', name='manifest-text-reader', role='discovery', capabilities=['draft/v1'])['token']
        self.op('enqueue', key='manifest-text-reader', spec={'kind': 'draft/v1', 'context_id': reader_context['id'],
            'purpose': 'Read both original ideas and all retained gaps', 'allowed_workers': ['manifest-text-reader'],
            'max_attempts': 1, 'lease_seconds': 10, 'deadline': 2900, 'dependencies': []})
        read_lease = self.broker.call(reader, 'claim')['lease']
        actual = self.broker.call(reader, 'read_artifact', lease=read_lease, artifact_id=manifest['id'])
        self.assertEqual(actual['body']['retained_research_records'], expected)
        with self.assertRaises(Denied):
            self.broker.call(reader, 'read_artifact', lease=read_lease, artifact_id=gap)

    def test_revoked_feedback_denies_direct_provider_before_backend_or_reservation(self):
        result = self.publish()
        context = self.op('create_context', role='formalizer', epoch=7,
            artifact_ids=[result['manifest_id'], self.case.root_results[0], self.catalog['id'], self.snapshot['id']])['id']
        # This is a declared live-mode boundary fixture with an unreachable
        # backend sentinel, never a credential, adapter, network or charged call.
        epoch = self.op('create_research_epoch', key='revocation-dispatch-boundary',
            context_id=self.fixture.context, workers=['first', 'second'],
            profile={**self.fixture.profile, 'mode': 'live', 'currency': 'USD', 'max_cost_units': 1,
                'max_tokens': 80000, 'generation_parameters': {'openai_responses': {}}})['id']
        token = self.op('register_worker', name='revoked-feedback-formalizer', role='formalizer',
            capabilities=['formalization/v1'])['token']
        spec = deepcopy(self.broker._job(self.formalization['job_id'])['spec'])
        spec.update(context_id=context, research_epoch_id=epoch, deadline=2800,
            allowed_workers=['revoked-feedback-formalizer'])
        spec['research_call_profile']['generation_parameters'] = {'openai_responses': {}}
        self.op('enqueue', key='revoked-feedback-formalizer', spec=spec)
        lease = self.broker.call(token, 'claim')['lease']
        defect = self.op('add_source', body={'text': 'Synthetic technical dispatch revocation'}, data_class='development')
        self.op('revoke_dependency', key='feedback-dispatch-defect', dependency_id=result['grant_id'],
            reason='Prevent a new provider dispatch using invalidated feedback', evidence_refs=[defect['id']])
        calls_before = self.broker._db.execute('SELECT COUNT(*) FROM research_calls').fetchone()[0]
        with patch.dict(self.broker._provider_routes, {'fixture/1': {'provider': 'openai', 'config': {}}}), \
                patch('trading_researcher.controller_providers.backend',
                    side_effect=AssertionError('Revoked context reached provider backend')) as backend, \
                patch.object(self.broker, '_reserve_research_call',
                    side_effect=AssertionError('Revoked context reached new reservation')) as reserve:
            with self.assertRaises(Denied):
                self.broker.call(token, 'invoke_auxiliary_provider', lease=lease, key='must-not-dispatch')
            backend.assert_not_called()
            reserve.assert_not_called()
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM research_calls').fetchone()[0], calls_before)

    def test_advancing_clock_never_backdates_records_or_their_release(self):
        tick = [self.fixture.now]
        def advancing_clock():
            tick[0] += 1
            return tick[0]
        self.broker.clock = advancing_clock
        result = self.publish()
        manifest = self.broker._artifact(result['manifest_id'])['body']
        grant = self.broker._artifact(result['grant_id'])['body']
        records = [self.broker._artifact(result[key])['body'] for key in ('observation_id', 'experience_id')]
        for record in records:
            self.assertGreater(record['created_at'], manifest['created_at'])
            self.assertGreaterEqual(record['available_at'], record['created_at'])
            self.assertGreaterEqual(grant['created_at'], record['created_at'])
            self.assertGreaterEqual(grant['created_at'], record['available_at'])
        self.assertGreater(records[1]['created_at'], records[0]['created_at'])


if __name__ == '__main__':
    unittest.main()
