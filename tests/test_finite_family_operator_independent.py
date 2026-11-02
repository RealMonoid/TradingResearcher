"""Independent finite resource arithmetic and real generic continuation custody.

Literal boundary views use the existing _study_view/ResourceHistory shape. They
are deliberately not authenticated manifests or numerical observations. The pure
adapter cannot authenticate a different well-formed study ID; its actual runner
must pin the expected ID, source, frozen manifest and full request separately.

The small Registry integration reuses explicit synthetic host lifecycle records.
Only numerical input resolution is substituted. No advance API, numerical child,
scientific world, production Registry or paid call is executed by these cases.
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_information_study as scalar_support
import test_study_continuation_independent as continuation_support
from tools.calibration import finite_family as owner
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict
from trading_researcher.information_study import make_manifest


HOUR = 3600000
GIB = 1073741824
MIB = 1048576
COMPUTE_CAP = 648000000
STORAGE_CAP = 107374182400
STUDY = 'a' * 64
CHECKPOINT = 'c' * 64
NEXT_WORLD = 'd' * 64


def boundary_view(*, status='READY', grants=0, compute=0, storage=MIB,
                  max_compute=HOUR, max_storage=4 * GIB, fits=True):
    """Existing view keys, with independent hand-set resource boundary values."""
    return {'study_id': STUDY, 'status': status,
        'budget': {'charged_compute_ms': compute, 'charged_storage_bytes': storage,
            'outstanding_attempts': [], 'attempts_per_world': {}, 'overrun': False,
            'next_reservation_fits': fits, 'initial_storage_bytes': MIB,
            'continuation_storage_bytes': grants * MIB,
            'original_max_compute_ms': HOUR, 'original_max_storage_bytes': 4 * GIB,
            'max_compute_ms': max_compute, 'max_storage_bytes': max_storage,
            'usage_uncertain': False},
        'summary': {'schema': 'joint-family-final-calibration-summary/1',
            'complete': status == 'COMPLETE', 'planned_worlds': 2048,
            'recorded_worlds': 2048 if status == 'COMPLETE' else 0,
            'cells': [], 'candidate_time_rows': None,
            'candidate_qualification': 'fixed_studied_target_not_n_min',
            'n_min': None, 'scientific_readiness': False, 'classification_permitted': False},
        'next_world_id': NEXT_WORLD if status == 'READY' else None,
        'attempt_artifact_ids': [], 'resource_checkpoint': CHECKPOINT,
        'continuation_ids': [format(index + 1, '064x') for index in range(grants)],
        'scientific_readiness': False, 'n_min': None}


class FiniteFamilyOperatorIndependentTests(unittest.TestCase):
    def assert_grant(self, view, compute, storage):
        retained = deepcopy(view)
        decision = owner.next_request(view)
        self.assertEqual({'op', 'args'}, set(decision))
        self.assertEqual('continue_study', decision['op'])
        args = decision['args']
        self.assertEqual({'key', 'study_id', 'expected_checkpoint', 'additional_compute_ms',
            'additional_storage_bytes', 'rationale', 'expected_progress', 'stop_reason'}, set(args))
        self.assertEqual(view['study_id'], args['study_id'])
        self.assertEqual(view['resource_checkpoint'], args['expected_checkpoint'])
        self.assertIs(type(args['additional_compute_ms']), int)
        self.assertIs(type(args['additional_storage_bytes']), int)
        self.assertEqual(compute, args['additional_compute_ms'])
        self.assertEqual(storage, args['additional_storage_bytes'])
        for name in ('key', 'rationale', 'expected_progress', 'stop_reason'):
            self.assertIs(type(args[name]), str)
            self.assertTrue(args[name].strip())
            self.assertLessEqual(len(args[name]), 8192)
        self.assertIn('180', args['rationale'])
        self.assertIn('100 GiB', args['rationale'])
        self.assertIn('replay', args['expected_progress'])
        self.assertIn('reset', args['expected_progress'])
        self.assertEqual(retained, view, 'A decision must not mutate retained history')
        return decision

    def test_exact_authorized_constants_are_integers_not_boolean_aliases(self):
        expected = {'MAX_COMPUTE_MS': 648000000, 'MAX_STORAGE_BYTES': 107374182400,
                    'MAX_GRANTS': 179, 'ATTEMPT_COMPUTE_MS': 300000,
                    'ATTEMPT_STORAGE_BYTES': 268435456, 'METADATA_BYTES': 1048576}
        for name, value in expected.items():
            with self.subTest(name=name):
                self.assertIs(type(getattr(owner, name)), int)
                self.assertEqual(value, getattr(owner, name))

    def test_ready_equality_reserves_full_compute_and_logical_storage_before_advance(self):
        view = boundary_view(compute=3300000, storage=4 * GIB - 268435456)
        retained = deepcopy(view)
        self.assertEqual({'op': 'advance_family_calibration', 'args': {'calibration_id': STUDY}},
                         owner.next_request(view))
        self.assertEqual(retained, view)
        for field in ('charged_compute_ms', 'charged_storage_bytes'):
            changed = deepcopy(view)
            changed['budget'][field] += 1
            with self.subTest(field=field), self.assertRaises(Invalid):
                owner.next_request(changed)

    def test_compute_stop_and_storage_only_stop_add_both_bounded_dimensions(self):
        for compute, storage in ((3300001, MIB), (0, 4 * GIB - 268435456 + 1)):
            with self.subTest(compute=compute, storage=storage):
                self.assert_grant(boundary_view(status='RESOURCE_STOP', compute=compute,
                    storage=storage, fits=False), HOUR, 4 * GIB)

    def test_metadata_and_next_full_storage_reservation_fit_at_exact_global_equality(self):
        view = boundary_view(status='RESOURCE_STOP', grants=24, compute=90000000,
            storage=STORAGE_CAP - 268435456 - MIB, max_compute=90000000,
            max_storage=STORAGE_CAP - MIB, fits=False)
        self.assert_grant(view, HOUR, MIB)
        changed = deepcopy(view)
        changed['budget']['charged_storage_bytes'] += 1
        with self.assertRaises(Invalid):
            owner.next_request(changed)

    def test_exhausted_storage_allowance_can_only_extend_compute_if_existing_storage_fits(self):
        view = boundary_view(status='RESOURCE_STOP', grants=24, compute=90000000,
            storage=STORAGE_CAP - 268435456 - MIB, max_compute=90000000,
            max_storage=STORAGE_CAP, fits=False)
        self.assert_grant(view, HOUR, 0)
        changed = deepcopy(view)
        changed['budget']['charged_storage_bytes'] += 1
        with self.assertRaises(Invalid):
            owner.next_request(changed)

    def test_last_grant_and_storage_only_179th_count_boundary_are_finite(self):
        last = boundary_view(status='RESOURCE_STOP', grants=178, compute=644400000,
            storage=4 * GIB + 178 * MIB, max_compute=644400000,
            max_storage=STORAGE_CAP, fits=False)
        self.assert_grant(last, HOUR, 0)
        for compute, storage in ((648000000, 4 * GIB + 179 * MIB),
                                 (0, STORAGE_CAP - 268435456 + 1)):
            view = boundary_view(status='RESOURCE_STOP', grants=179, compute=compute,
                storage=storage, max_compute=COMPUTE_CAP, max_storage=STORAGE_CAP, fits=False)
            with self.subTest(compute=compute, storage=storage), self.assertRaises(Invalid):
                owner.next_request(view)
        # The count limit bans more grants, not work already fully reserved.
        ready = boundary_view(grants=179, max_compute=COMPUTE_CAP,
                              max_storage=STORAGE_CAP, storage=180 * MIB)
        self.assertEqual('advance_family_calibration', owner.next_request(ready)['op'])

    def test_complete_only_returns_none_and_unsafe_terminal_states_never_grant(self):
        self.assertIsNone(owner.next_request(boundary_view(status='COMPLETE')))
        for state in ('RUNNING', 'ORPHAN_UNCERTAIN', 'USAGE_UNCERTAIN', 'MODEL_GAP',
                      'TECHNICAL_FAILURE', 'UNKNOWN', '', None):
            with self.subTest(state=state), self.assertRaises(Invalid):
                owner.next_request(boundary_view(status=state))
        for state in ('READY', 'RESOURCE_STOP', 'COMPLETE'):
            for field, bad in (('usage_uncertain', True), ('overrun', True),
                               ('outstanding_attempts', ['unresolved-owned-attempt'])):
                view = boundary_view(status=state)
                view['budget'][field] = bad
                with self.subTest(state=state, field=field), self.assertRaises(Invalid):
                    owner.next_request(view)

    def test_status_next_fit_and_world_retry_cannot_disagree_with_safe_arithmetic(self):
        values = [boundary_view(fits=False),
                  boundary_view(status='RESOURCE_STOP', fits=True),
                  boundary_view(status='RESOURCE_STOP', fits=False)]
        attempted = boundary_view()
        attempted['budget']['attempts_per_world'] = {NEXT_WORLD: 1}
        values.append(attempted)
        repeated = boundary_view()
        repeated['budget']['attempts_per_world'] = {'e' * 64: 2}
        values.append(repeated)
        missing_world = boundary_view()
        missing_world['next_world_id'] = None
        values.append(missing_world)
        for index, value in enumerate(values):
            with self.subTest(case=index), self.assertRaises(Invalid):
                owner.next_request(value)

    def test_malformed_integer_identity_checkpoint_and_history_fields_are_rejected(self):
        for field in ('charged_compute_ms', 'charged_storage_bytes', 'initial_storage_bytes',
                      'continuation_storage_bytes', 'original_max_compute_ms',
                      'original_max_storage_bytes', 'max_compute_ms', 'max_storage_bytes'):
            for bad in (True, False, -1, '1', 1.0, None):
                changed = boundary_view()
                changed['budget'][field] = bad
                with self.subTest(field=field, bad=bad), self.assertRaises(Invalid):
                    owner.next_request(changed)
        for field in ('study_id', 'resource_checkpoint'):
            for bad in ('', 'x' * 64, 'A' * 64, 'a' * 63, True, None, b'a' * 64):
                changed = boundary_view()
                changed[field] = bad
                with self.subTest(field=field, bad=bad), self.assertRaises(Invalid):
                    owner.next_request(changed)
        for field in ('outstanding_attempts', 'attempts_per_world'):
            changed = boundary_view()
            changed['budget'][field] = None
            with self.subTest(field=field), self.assertRaises(Invalid):
                owner.next_request(changed)

    def test_global_overauthorization_or_false_metadata_history_is_not_healed(self):
        changes = [
            {'max_compute_ms': COMPUTE_CAP + 1}, {'max_storage_bytes': STORAGE_CAP + 1},
            {'original_max_compute_ms': HOUR + 1}, {'original_max_storage_bytes': 4 * GIB + 1},
            {'charged_compute_ms': HOUR + 1}, {'charged_storage_bytes': 4 * GIB + 1},
            {'continuation_storage_bytes': MIB}, {'charged_storage_bytes': MIB - 1},
        ]
        for fields in changes:
            view = boundary_view()
            view['budget'].update(fields)
            with self.subTest(fields=fields), self.assertRaises(Invalid):
                owner.next_request(view)
        for grants in ([None], ['not-a-hash'], ['1' * 64, '1' * 64]):
            view = boundary_view()
            view['continuation_ids'] = grants
            view['budget']['continuation_storage_bytes'] = len(grants) * MIB
            view['budget']['charged_storage_bytes'] += len(grants) * MIB
            with self.subTest(grants=grants), self.assertRaises(Invalid):
                owner.next_request(view)
        view = boundary_view(grants=180, compute=HOUR, max_compute=COMPUTE_CAP,
                             storage=181 * MIB, max_storage=STORAGE_CAP)
        with self.assertRaises(Invalid):
            owner.next_request(view)

    def test_continuation_key_is_stable_for_exact_pair_and_changes_with_either_identity(self):
        view = boundary_view(status='RESOURCE_STOP', compute=HOUR, fits=False)
        first = self.assert_grant(view, HOUR, 4 * GIB)
        self.assertEqual(first, owner.next_request(deepcopy(view)))
        more_usage = deepcopy(view)
        more_usage['budget']['charged_storage_bytes'] += 1
        self.assertEqual(first['args']['key'], owner.next_request(more_usage)['args']['key'])
        keys = {first['args']['key']}
        for field, value in (('study_id', 'b' * 64), ('resource_checkpoint', 'd' * 64)):
            changed = deepcopy(view)
            changed[field] = value
            decision = owner.next_request(changed)
            keys.add(decision['args']['key'])
            self.assertEqual(changed['study_id'], decision['args']['study_id'])
            self.assertEqual(changed['resource_checkpoint'], decision['args']['expected_checkpoint'])
        self.assertEqual(3, len(keys))
        # A different valid ID is only syntactically valid here. Authentication
        # and comparison with the one approved manifest belong to the runner.


class FiniteFamilyBrokerContinuationIndependentTests(unittest.TestCase):
    def setUp(self):
        self.host = continuation_support.StudyContinuationIndependentTests(methodName='runTest')
        self.host.setUp()
        self.addCleanup(self.host.doCleanups)
        guard = patch('trading_researcher.study_runs.execute_attempt',
                      side_effect=AssertionError('Resource fixture executed a numerical world'))
        guard.start()
        self.addCleanup(guard.stop)

    def prepared_stop(self):
        host = self.host
        host.serial += 1
        source = host.owned({'schema': 'data-snapshot/1',
                             'synthetic_finite_operator_fixture': host.serial}, origin='source')
        profile = scalar_support.profile()
        profile.update(targets=[16], worlds_per_cell=2, seed=713)
        profile['budget'] = {'max_compute_ms': 300000, 'attempt_compute_ms': 300000,
            'max_storage_bytes': GIB, 'attempt_storage_bytes': 268435456, 'max_attempts': 1}
        manifest = make_manifest(scalar_support.assigned(), profile)
        payload = {'case_blob': host.broker._stage_blob_bytes(b'')}
        request = {'key': 'synthetic-finite-resource-study', 'plan_id': source['id'],
            'execution_id': source['id'], 'diagnostics_id': source['id'], 'profile': profile}
        host.input_by_key[request['key']] = (payload, manifest, [source['id']], [source['id']])
        study = host.op('prepare_information_study', **request)
        host.observation(study, compute=300000, storage=MIB)
        view = host.view(study)
        self.assertEqual('RESOURCE_STOP', view['status'])
        return study, view

    def test_real_generic_grant_duplicate_stale_alias_restart_and_complete_keep_one_allowance(self):
        host = self.host
        study, stopped = self.prepared_stop()
        original = deepcopy(study)
        decision = owner.next_request(stopped)
        self.assertEqual('continue_study', decision['op'])
        args = decision['args']
        self.assertEqual(HOUR, args['additional_compute_ms'])
        self.assertEqual(4 * GIB, args['additional_storage_bytes'])
        grant = host.op(decision['op'], **args)
        after = host.view(study)
        self.assertEqual('READY', after['status'])
        self.assertEqual(3900000, after['budget']['max_compute_ms'])
        self.assertEqual(5 * GIB, after['budget']['max_storage_bytes'])
        self.assertEqual(MIB, after['budget']['continuation_storage_bytes'])
        self.assertNotEqual(stopped['resource_checkpoint'], after['resource_checkpoint'])
        events = host.event_count()
        self.assertEqual(grant, host.op('continue_study', **args))
        self.assertEqual(events, host.event_count())
        with self.assertRaises(Conflict):
            host.op('continue_study', **{**args, 'key': args['key'] + ':stale-alias'})
        self.assertEqual(after, host.view(study))
        self.assertEqual(events, host.event_count())
        host.broker.close()
        host.broker = Broker(host.directory)
        host.token = host.broker.admin_token
        self.assertEqual(grant, host.op('continue_study', **args))
        self.assertEqual(after, host.view(study))
        for index in range(1, len(study['body']['manifest']['worlds'])):
            host.observation(study, index=index, compute=300000, storage=MIB)
        complete = host.view(study)
        self.assertEqual('COMPLETE', complete['status'])
        self.assertIsNone(owner.next_request(complete))
        self.assertEqual([grant['id']], complete['continuation_ids'])
        self.assertEqual(3900000, complete['budget']['max_compute_ms'])
        self.assertEqual(5 * GIB, complete['budget']['max_storage_bytes'])
        events = host.event_count()
        self.assertEqual(grant, host.op('continue_study', **args))
        self.assertEqual(events, host.event_count())
        self.assertEqual(original, host.op('get_artifact', artifact_id=study['id']))


if __name__ == '__main__':
    unittest.main()
