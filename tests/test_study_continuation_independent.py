"""Independent resource-continuation boundaries with explicit synthetic metadata.

Only numerical input resolution is replaced. Source retention, authentication,
grant accounting, event history, private ancestry and backup/restore are real.
Injected host observations are lifecycle fixtures, not executed scientific worlds.
The separate family lifecycle integration supplies genuine child/replay evidence.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_information_study as scalar
from trading_researcher import study_runs
from trading_researcher.calibration_runs import CalibrationStudies
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.information_study import make_manifest
from trading_researcher.storage import restore_bundle


ERRORS = (Invalid, Conflict, Denied)
MIB = 1024 ** 2


class StudyContinuationIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name) / 'registry'
        self.broker = Broker(self.directory)
        self.addCleanup(lambda: self.broker.close())
        self.token = self.broker.admin_token
        self.serial = 0
        self.input_by_key = {}
        resolver = patch.object(self.broker, '_study_inputs',
            side_effect=lambda actor, request:deepcopy(self.input_by_key[request['key']]))
        resolver.start(); self.addCleanup(resolver.stop)

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def owned(self, body, *, origin='controller', data_class='development', refs=(), exposure=()):
        with self.broker._transaction():
            return self.broker._save_artifact({'version':'local-artifact/1', 'creator':'controller',
                'origin':origin, 'data_class':data_class, 'source_refs':list(refs), 'exposure':list(exposure),
                'authority':'synthetic_resource_boundary_fixture_only', 'body':body})

    def prepared(self, *, attempts=3, compute=10000, storage=1024 ** 3, attempt_storage=64 * MIB):
        self.serial += 1
        source = self.owned({'schema':'data-snapshot/1', 'synthetic_fixture':self.serial}, origin='source')
        config = scalar.profile()
        config.update(targets=[16], worlds_per_cell=2, seed=self.serial)
        config['budget'].update(max_compute_ms=compute, attempt_compute_ms=10000,
            max_storage_bytes=storage, attempt_storage_bytes=attempt_storage, max_attempts=attempts)
        manifest = make_manifest(scalar.assigned(), config)
        payload = {'case_blob':self.broker._stage_blob_bytes(b'')}
        request = {'key':'fixture-' + str(self.serial), 'plan_id':source['id'],
            'execution_id':source['id'], 'diagnostics_id':source['id'], 'profile':config}
        inputs = (payload, manifest, [source['id']], [source['id']])
        self.input_by_key[request['key']] = inputs
        study = self.op('prepare_information_study', **request)
        return study, source

    def observation(self, study, *, index=0, state='INFORMATION_GAP', compute=10000,
                    storage=MIB, known=True, settled=True, orphan=False):
        """Inject an explicit host history to isolate admission arithmetic."""
        self.serial += 1
        attempt = 'synthetic-attempt-' + str(self.serial)
        manifest = study['body']['manifest']; world = manifest['worlds'][index]
        limits = manifest['profile']['budget']
        outcome = {'world_id':world['id'], 'state':state, 'decision':None,
            'scope_count':None, 'condition_count':None, 'covered':None}
        reservation = {'attempt_id':attempt, 'world_id':world['id'],
            'compute_ms':limits['attempt_compute_ms'], 'storage_bytes':limits['attempt_storage_bytes']}
        settlement = {'attempt_id':attempt, 'compute_ms':compute, 'storage_bytes':storage, 'usage_known':known}
        with self.broker._transaction():
            self.broker._event('controller', 'information_study_reserved', study_id=study['id'], reservation=reservation)
            if settled:
                result = self.broker._save_artifact({'version':'local-artifact/1', 'creator':'controller',
                    'origin':'controller', 'data_class':'development', 'source_refs':[study['id']],
                    'exposure':study['exposure'], 'authority':'synthetic_resource_boundary_fixture_only',
                    'body':{'schema':'development-information-study-attempt/1', 'study_id':study['id'],
                        'attempt_id':attempt, 'world_id':world['id'], 'outcome':outcome, 'settlement':settlement,
                        'scientific_readiness':False}})
                self.broker._event('controller', 'information_study_settled', study_id=study['id'],
                    settlement=settlement, outcome=outcome, artifact_id=result['id'], orphan_uncertain=orphan)
        return attempt

    def view(self, study):
        return self.op('inspect_information_study', study_id=study['id'])

    def request(self, study, **changes):
        view = self.view(study)
        result = {'key':'grant-' + str(self.serial), 'study_id':study['id'],
            'expected_checkpoint':view['resource_checkpoint'], 'additional_compute_ms':10000,
            'additional_storage_bytes':MIB, 'rationale':'Continue the exact fixed synthetic inventory.',
            'expected_progress':'Complete the next predeclared world without replacing any observations.',
            'stop_reason':'Stop again at the next frozen reservation or terminal failure boundary.'}
        result.update(changes)
        return result

    def stopped(self, **kwargs):
        study, source = self.prepared(**kwargs)
        self.observation(study)
        self.assertEqual(self.view(study)['status'], 'RESOURCE_STOP')
        return study, source

    def event_count(self):
        return self.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0]

    def test_exact_grant_extends_only_effective_limits_and_keeps_manifest(self):
        study, _ = self.stopped(); before = self.view(study); original = deepcopy(study)
        args = self.request(study)
        grant = self.op('continue_study', **args); after = self.view(study)
        self.assertEqual(grant['body']['schema'], 'study-resource-continuation/1')
        self.assertEqual(grant['body']['request'], args)
        self.assertEqual(grant['data_class'], 'operations')
        self.assertEqual(grant['origin'], grant['creator'])
        self.assertEqual(grant['creator'], 'controller')
        self.assertFalse(grant['body']['scientific_readiness'])
        self.assertIsNone(grant['body']['previous_continuation_id'])
        self.assertEqual(grant['body']['charged_compute_ms_before'], before['budget']['charged_compute_ms'])
        self.assertEqual(grant['body']['charged_storage_bytes_before'], before['budget']['charged_storage_bytes'])
        self.assertEqual(grant['body']['completed_worlds_before'], 1)
        self.assertEqual(after['status'], 'READY')
        self.assertEqual(after['continuation_ids'], [grant['id']])
        self.assertNotEqual(after['resource_checkpoint'], before['resource_checkpoint'])
        self.assertEqual(after['budget']['max_compute_ms'], 20000)
        self.assertEqual(after['budget']['original_max_compute_ms'], 10000)
        self.assertEqual(after['budget']['max_storage_bytes'], 1024 ** 3 + MIB)
        self.assertEqual(after['budget']['original_max_storage_bytes'], 1024 ** 3)
        self.assertEqual(after['budget']['continuation_storage_bytes'], MIB)
        self.assertEqual(after['budget']['charged_storage_bytes'], before['budget']['charged_storage_bytes'] + MIB)
        self.assertEqual(self.broker._artifact(study['id']), original)

    def test_same_key_retry_returns_original_after_history_changes_without_second_charge(self):
        study, _ = self.stopped(); args = self.request(study)
        grant = self.op('continue_study', **args)
        self.observation(study, index=1)
        before = self.view(study); events = self.event_count()
        self.assertEqual(self.op('continue_study', **args), grant)
        self.assertEqual(self.event_count(), events)
        self.assertEqual(self.view(study), before)

    def test_key_conflict_alias_and_consumed_checkpoint_cannot_stack_allowances(self):
        study, _ = self.stopped(); args = self.request(study)
        self.op('continue_study', **args)
        self.observation(study, index=1)
        events = self.event_count()
        for changed in ({**args, 'key':'new-alias'}, {**args, 'additional_compute_ms':20000}):
            with self.subTest(key=changed['key']), self.assertRaises(Conflict):
                self.op('continue_study', **changed)
        self.assertEqual(self.event_count(), events)
        self.assertEqual(len(self.view(study)['continuation_ids']), 1)

    def test_new_known_settlement_stales_a_previously_observed_checkpoint(self):
        study, _ = self.stopped(); args = self.request(study)
        # A zero-cost known failure still changes attempt history and retry state.
        self.observation(study, index=1, state='TECHNICAL_FAILURE', compute=0, storage=0)
        with self.assertRaises(ERRORS):
            self.op('continue_study', **args)

    def test_increment_types_bounds_empty_and_insufficient_next_reservation_are_atomic(self):
        study, _ = self.stopped(); args = self.request(study)
        mutations = [dict(additional_compute_ms=-1), dict(additional_compute_ms=True),
            dict(additional_compute_ms='10000'), dict(additional_compute_ms=3600001),
            dict(additional_storage_bytes=4 * 1024 ** 3 + 1), dict(additional_storage_bytes=False),
            dict(additional_compute_ms=0, additional_storage_bytes=0),
            dict(additional_compute_ms=9999), dict(rationale=''), dict(expected_progress=''), dict(stop_reason='')]
        for index, fields in enumerate(mutations):
            events = self.event_count()
            with self.subTest(fields=fields), self.assertRaises(ERRORS):
                self.op('continue_study', **{**args, 'key':'invalid-' + str(index), **fields})
            self.assertEqual(self.event_count(), events)

    def test_ready_complete_model_gap_and_running_are_not_grantable(self):
        for state in ('READY', 'COMPLETE', 'MODEL_GAP', 'RUNNING'):
            study, _ = self.prepared(compute=60000)
            if state == 'COMPLETE':
                for index in range(6):self.observation(study, index=index)
            elif state == 'MODEL_GAP':self.observation(study, state='MODEL_GAP')
            elif state == 'RUNNING':self.observation(study, settled=False)
            self.assertEqual(self.view(study)['status'], state)
            with self.subTest(state=state), self.assertRaises(ERRORS):
                self.op('continue_study', **self.request(study))

    def test_unknown_settlement_and_orphan_cannot_be_forgiven_by_extra_budget(self):
        for orphan in (False, True):
            study, _ = self.prepared()
            self.observation(study, state='TECHNICAL_FAILURE', known=False, orphan=orphan)
            with self.subTest(orphan=orphan), self.assertRaises(ERRORS):
                self.op('continue_study', **self.request(study))

    def test_attempt_and_aggregate_overruns_are_not_repaired_by_a_grant(self):
        for mode in ('attempt', 'aggregate', 'storage'):
            study, _ = self.prepared()
            self.observation(study, compute=10001 if mode == 'attempt' else 10000,
                storage=64 * MIB + 1 if mode == 'storage' else MIB)
            if mode == 'aggregate':self.observation(study, index=1, compute=1)
            self.assertTrue(self.view(study)['budget']['overrun'])
            with self.subTest(mode=mode), self.assertRaises(ERRORS):
                self.op('continue_study', **self.request(study,
                    additional_compute_ms=3600000, additional_storage_bytes=4 * 1024 ** 3))

    def test_temporary_reservation_overrun_survives_a_smaller_known_settlement(self):
        study, _ = self.prepared(compute=15000)
        self.observation(study, compute=6000)
        # A full second 10000ms reservation exceeds the original 15000ms
        # aggregate. Its later 1000ms use must not erase the historical breach.
        self.observation(study, index=1, compute=1000)
        view = self.view(study)
        self.assertEqual(view['budget']['charged_compute_ms'], 7000)
        self.assertTrue(view['budget']['overrun'])
        self.assertEqual(view['status'], 'RESOURCE_STOP')
        with self.assertRaises(ERRORS):
            self.op('continue_study', **self.request(study, additional_compute_ms=3600000))

    def test_dependency_resolution_is_rechecked_before_a_grant_is_retained(self):
        study, _ = self.stopped(); args = self.request(study)
        key = study['body']['request']['key']
        payload, manifest, refs, exposure = deepcopy(self.input_by_key[key])
        payload['changed_after_preparation'] = True
        self.input_by_key[key] = payload, manifest, refs, exposure
        events = self.event_count()
        with self.assertRaises(ERRORS):self.op('continue_study', **args)
        self.assertEqual(self.event_count(), events)

    def test_retry_cap_does_not_reset_after_a_valid_grant(self):
        study, _ = self.prepared(attempts=2)
        self.observation(study, state='TECHNICAL_FAILURE')
        self.op('continue_study', **self.request(study))
        self.observation(study, state='TECHNICAL_FAILURE')
        view = self.view(study)
        self.assertEqual(view['status'], 'TECHNICAL_FAILURE')
        self.assertEqual(view['budget']['attempts_per_world'][study['body']['manifest']['worlds'][0]['id']], 2)
        with self.assertRaises(ERRORS):self.op('continue_study', **self.request(study))

    def test_third_no_progress_grant_is_denied_before_the_retry_cap(self):
        # Input retention alone leaves too little room for the first full
        # attempt. This makes the first zero-progress grant legitimate.
        study, _ = self.prepared(attempts=3, storage=64 * MIB)
        self.assertEqual(self.view(study)['status'], 'RESOURCE_STOP')
        first = self.op('continue_study', **self.request(study,
            additional_compute_ms=0, additional_storage_bytes=64 * MIB))
        self.assertEqual(first['body']['no_progress_continuations'], 1)
        self.observation(study, state='TECHNICAL_FAILURE', storage=64 * MIB)
        second = self.op('continue_study', **self.request(study,
            key='second-no-progress', additional_storage_bytes=64 * MIB))
        self.assertEqual(second['body']['no_progress_continuations'], 2)
        self.observation(study, state='TECHNICAL_FAILURE', storage=64 * MIB)
        view = self.view(study)
        world_id = study['body']['manifest']['worlds'][0]['id']
        self.assertEqual(view['budget']['attempts_per_world'][world_id], 2)
        self.assertEqual(view['status'], 'RESOURCE_STOP')
        with self.assertRaises(ERRORS):
            self.op('continue_study', **self.request(study,
                key='third-no-progress', additional_storage_bytes=64 * MIB))

    def test_worker_is_denied_before_any_private_study_read(self):
        worker = self.op('register_worker', name='untrusted-resource-worker', role='discovery',
            capabilities=['research-record/v1'])['token']
        args = {'key':'forged', 'study_id':'private-unavailable', 'expected_checkpoint':'not-owned',
            'additional_compute_ms':10000, 'additional_storage_bytes':MIB,
            'rationale':'x', 'expected_progress':'x', 'stop_reason':'x'}
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Private read before authentication')):
            with self.assertRaises(Denied):self.broker.call(worker, 'continue_study', **args)

    def test_reserved_namespace_and_final_ancestry_are_scoped_without_hiding_development(self):
        with self.assertRaises(Invalid):
            self.op('add_source', body={'schema':'study-resource-continuation/1'}, data_class='development')
        study, _ = self.stopped(); grant = self.op('continue_study', **self.request(study))
        # Operations classification is not a blanket ancestry prohibition.
        # Existing release/context policy still governs a development grant.
        self.broker._deny_final_calibration_ancestry(grant)
        final = self.owned({'schema':'evaluator-calibration-input/1'}, data_class='operations')
        final_grant = self.owned({'schema':'study-resource-continuation/1'},
            data_class='operations', refs=[final['id']])
        for edge in ('refs', 'exposure'):
            wrapper = self.owned({'schema':'ordinary-wrapper/1'}, **{edge:[final_grant['id']]})
            for allow in (False, True):
                with self.subTest(edge=edge, allow=allow), self.assertRaises(Denied):
                    self.broker._deny_final_calibration_ancestry(wrapper, allow_private_targets=allow)

    def test_revoked_dependency_denies_grant_and_is_inherited_by_existing_grant(self):
        study, source = self.stopped(); grant = self.op('continue_study', **self.request(study))
        self.observation(study, index=1)
        evidence = self.op('add_source', body={'schema':'fixture-defect/1'}, data_class='development')
        self.op('revoke_dependency', key='fixture-revocation', dependency_id=source['id'],
            reason='Synthetic dependency defect.', evidence_refs=[evidence['id']])
        with self.assertRaises(ERRORS):self.op('continue_study', **self.request(study, key='after-revocation'))
        inspection = self.op('inspect_dependency_use', artifact_id=grant['id'])
        self.assertEqual(inspection['status'], 'INVALIDATED_BY_DEPENDENCY')

    def test_retained_source_corruption_and_runtime_drift_block_before_commit(self):
        study, _ = self.stopped(); args = self.request(study)
        for target, replacement in (('_load_study_source', Invalid('Corrupt retained source')),
                                    ('runtime', {'not':'the retained runtime'})):
            events = self.event_count()
            context = (patch.object(self.broker, target, side_effect=replacement) if target != 'runtime'
                else patch.object(study_runs, '_runtime_identity', return_value=replacement))
            with self.subTest(target=target), context, self.assertRaises(ERRORS):
                self.op('continue_study', **args)
            self.assertEqual(self.event_count(), events)

    def test_second_grant_chains_to_first_and_retains_cumulative_charges(self):
        study, _ = self.stopped()
        first = self.op('continue_study', **self.request(study))
        self.observation(study, index=1)
        second = self.op('continue_study', **self.request(study, key='second-grant'))
        view = self.view(study)
        self.assertEqual(second['body']['previous_continuation_id'], first['id'])
        self.assertEqual(set(second['source_refs']), {study['id'], first['id']})
        self.assertTrue(set(study['exposure']) <= set(second['exposure']))
        self.assertEqual(view['continuation_ids'], [first['id'], second['id']])
        self.assertEqual(view['budget']['charged_compute_ms'], 20000)
        self.assertEqual(view['budget']['max_compute_ms'], 30000)
        self.assertEqual(view['budget']['continuation_storage_bytes'], 2 * MIB)
        self.assertEqual(view['budget']['charged_storage_bytes'], study['body']['initial_storage_bytes'] + 4 * MIB)

    def test_continued_attempt_retains_the_full_inherited_grant_exposure(self):
        study, _ = self.stopped()
        first = self.op('continue_study', **self.request(study))
        self.observation(study, index=1)
        second = self.op('continue_study', **self.request(study, key='second-for-attempt'))
        world = study['body']['manifest']['worlds'][2]
        outcome = {'world_id':world['id'], 'state':'INFORMATION_GAP', 'decision':None,
            'scope_count':None, 'condition_count':None, 'covered':None}
        calculation = {'world_id':world['id'], 'outcome':outcome,
            'scientific_readiness':False, 'classification_permitted':False, 'n_min':None}
        with patch.object(study_runs, 'execute_attempt', return_value=(calculation, [{}, {}])):
            view = self.op('advance_information_study', study_id=study['id'])
        attempt = self.broker._artifact(view['attempt_artifact_ids'][-1])
        self.assertEqual(attempt['body']['continuation_id'], second['id'])
        self.assertEqual(set(attempt['source_refs']), {study['id'], second['id']})
        self.assertTrue(set(second['exposure']) <= set(attempt['exposure']))
        self.assertIn(first['id'], attempt['exposure'])

    def test_final_setup_rejects_revoked_completed_development_attempt_dependency(self):
        study, _ = self.prepared(compute=50000)
        for index in range(5):self.observation(study, index=index)
        self.assertEqual(self.view(study)['status'], 'RESOURCE_STOP')
        grant = self.op('continue_study', **self.request(study))
        world = study['body']['manifest']['worlds'][5]
        outcome = {'world_id':world['id'], 'state':'INFORMATION_GAP', 'decision':None,
            'scope_count':None, 'condition_count':None, 'covered':None}
        calculation = {'world_id':world['id'], 'outcome':outcome,
            'scientific_readiness':False, 'classification_permitted':False, 'n_min':None}
        with patch.object(study_runs, 'execute_attempt', return_value=(calculation, [{}, {}])):
            view = self.op('advance_information_study', study_id=study['id'])
        self.assertEqual(view['status'], 'COMPLETE')
        runner = CalibrationStudies(self.broker)
        request = {'development_study_id':study['id'], 'time_rows':16}
        self.assertEqual(runner._development(request)[0]['id'], study['id'])
        evidence = self.op('add_source', body={'schema':'resource-defect-fixture/1'}, data_class='development')
        self.op('revoke_dependency', key='revoke-consumed-grant', dependency_id=grant['id'],
            reason='Synthetic defect in the resource decision.', evidence_refs=[evidence['id']])
        last = self.op('inspect_dependency_use', artifact_id=view['attempt_artifact_ids'][-1])
        self.assertEqual(last['status'], 'INVALIDATED_BY_DEPENDENCY')
        with self.assertRaises(ERRORS):runner._development(request)

    def test_forged_later_grant_cannot_hide_a_past_prefix_overrun(self):
        legitimate, _ = self.stopped()
        template = self.op('continue_study', **self.request(legitimate))
        invalid, _ = self.prepared(compute=15000)
        self.observation(invalid, compute=6000)
        self.observation(invalid, index=1, compute=1000)
        before = self.view(invalid)
        request = self.request(invalid, key='injected-forgery', additional_compute_ms=10000)
        body = {**deepcopy(template['body']), 'request':request, 'previous_continuation_id':None,
            'charged_compute_ms_before':before['budget']['charged_compute_ms'],
            'charged_storage_bytes_before':before['budget']['charged_storage_bytes'],
            'completed_worlds_before':2, 'no_progress_continuations':0}
        # This bypasses public API ownership deliberately to challenge event
        # replay itself; a later sum would fit but its historical prefix did not.
        with self.broker._transaction():
            forged = self.broker._save_artifact({**{k:v for k,v in template.items() if k != 'id'},
                'body':body, 'source_refs':[invalid['id']],
                'exposure':sorted(set(invalid['exposure']) | {invalid['id']})})
            self.broker._event('controller', 'information_study_continued',
                study_id=invalid['id'], artifact_id=forged['id'])
        with self.assertRaises(ERRORS):self.view(invalid)

    def test_duplicate_owned_grant_event_is_rejected_during_replay(self):
        study, _ = self.stopped(); grant = self.op('continue_study', **self.request(study))
        with self.broker._transaction():
            self.broker._event('controller', 'information_study_continued', study_id=study['id'], artifact_id=grant['id'])
        with self.assertRaises(ERRORS):self.view(study)

    def test_failure_after_artifact_and_event_insert_rolls_back_both(self):
        study, _ = self.stopped(); request = self.request(study)
        before = self.view(study); events = self.event_count()
        artifacts = self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]
        original = self.broker._event
        def fail_after_insert(actor, action, **details):
            result = original(actor, action, **details)
            if action == 'information_study_continued':
                raise RuntimeError('Injected failure after continuation event insertion')
            return result
        with patch.object(self.broker, '_event', side_effect=fail_after_insert), self.assertRaises(RuntimeError):
            self.op('continue_study', **request)
        self.assertEqual(self.event_count(), events)
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], artifacts)
        self.assertEqual(self.view(study), before)
        grant = self.op('continue_study', **request)
        self.assertEqual(self.view(study)['continuation_ids'], [grant['id']])

    def test_backup_restore_preserves_grant_identity_checkpoint_and_accounting(self):
        study, _ = self.stopped(); args = self.request(study)
        grant = self.op('continue_study', **args); before = self.view(study)
        backup = Path(self.temp.name) / 'backup'; restored = Path(self.temp.name) / 'restored'
        self.op('backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, self.directory / 'operator.key')
        other = Broker(restored)
        try:
            self.assertEqual(other.call(other.admin_token, 'inspect_information_study', study_id=study['id']), before)
            self.assertEqual(other.call(other.admin_token, 'continue_study', **args), grant)
            self.assertEqual(other.call(other.admin_token, 'inspect_information_study', study_id=study['id']), before)
        finally:other.close()


if __name__ == '__main__':
    unittest.main()
