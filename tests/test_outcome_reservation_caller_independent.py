"""D099 caller cases with explicit separation of genuine metadata and judgments.

The small transaction fixture substitutes the private admission judgment with
invented owned records and hand-fixed grids. Its positive commits qualify only
binding/conflict machinery, never scientific admission or raw-input membership.
The genuine plan fixture uses the existing public normalization, certification,
compile, development and plan owners on three synthetic rows; its actual public
freeze caller must stay ADMISSION_GAP and must not load outcomes during freeze.
"""
from contextlib import contextmanager, ExitStack
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_evaluation_plans as plan_support
import test_scientific_freeze_independent as freeze_support
import test_outcome_reservations_independent as fixed
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.storage import restore_bundle


COMMITTED = ('scientific-allocation/1', 'scientific-trial/1', 'frozen-manifest/1')


def independent_hash(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def fixed_reservation(grid, artifact_ids, bindings=None):
    return {'profile': 'outcome-reservation/1.0', 'status': 'POTENTIAL_GRID_BOUND',
            'grid': deepcopy(grid), 'plan_bindings': deepcopy(bindings or []),
            'artifact_ids': sorted(artifact_ids), 'raw_input_membership': 'NOT_QUALIFIED',
            'actual_inputs_and_publication': 'NOT_OBSERVED',
            'dependence_exposure_prior_use': 'NOT_QUALIFIED',
            'scientific_readiness': False}


class OutcomeReservationTransactionIndependentTests(unittest.TestCase):
    """Synthetic private judgment only; no actual scientific prerequisite passes."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = freeze_support.FreezeFixture(self.root / 'registry')
        self.addCleanup(self.fixture.broker.close)

    def grid(self, start=1577836800):
        return fixed.expected_grid([fixed.span(start, start + 900)],
                                   [fixed.span(start + 900, start + 1800)], 1, 1)

    def evidence(self, grid, request=None, records=None):
        evidence = self.fixture.admission(request)
        bindings = [{'plan_id': claim['plan_id'], 'compiled_id': claim['compiled_id'],
                     'grid': deepcopy(grid)} for claim in evidence['claims']]
        evidence['outcome_reservation'] = fixed_reservation(grid, evidence['artifact_ids'], bindings)
        if records is not None:
            evidence['outcome_record_ids'] = records
        return evidence

    def another_family(self, label):
        fixture = self.fixture
        compiled = fixture.source('synthetic new compiled alias ' + label)
        plan = fixture.source('synthetic new plan alias ' + label, exposure=[compiled['id']])
        fixture.compiled, fixture.plans = [compiled], [plan]
        fixture.claims = [{'claim_id': hashlib.sha256(label.encode()).hexdigest(),
                           'plan_id': plan['id'], 'compiled_id': compiled['id']}]
        return fixture.request(key='batch-' + label,
            campaign_id=fixture.source('different campaign ' + label)['id'],
            selection_record_ref=fixture.source('different selection ' + label)['id'],
            reservation_spec_ref=fixture.source('different reservation ' + label)['id'])

    def assert_no_commit(self):
        self.assertEqual([0, 0, 0],
                         [len(self.fixture.artifacts(schema)) for schema in COMMITTED])

    def assert_bound(self, manifest, reservation):
        fixture = self.fixture
        allocation = fixture.op('get_artifact', artifact_id=manifest['body']['allocation_id'])
        self.assertEqual(reservation, allocation['body']['signature']['outcome_reservation'])
        for artifact in (allocation, manifest):
            self.assertEqual(reservation, artifact['body']['outcome_reservation'])
        expected = independent_hash(reservation)
        trials = [fixture.op('get_artifact', artifact_id=identity)
                  for identity in manifest['body']['trial_ids']]
        for artifact in (allocation, manifest, *trials):
            self.assertEqual(expected, artifact['body']['outcome_reservation_hash'])
            self.assertIs(artifact['body'].get('assessment_access_authority', False), False)

    def test_versioned_metadata_and_hash_bind_atomic_records_without_rewriting_drafts(self):
        originals = deepcopy([*self.fixture.plans, *self.fixture.compiled])
        evidence = self.evidence(self.grid())
        manifest = self.fixture.freeze(admission=evidence)
        self.assert_bound(manifest, evidence['outcome_reservation'])
        for original in originals:
            self.assertEqual(original,
                self.fixture.op('get_artifact', artifact_id=original['id']))

    def test_complete_family_shares_events_but_omitted_or_reordered_bindings_are_denied(self):
        self.fixture = freeze_support.FreezeFixture(self.root / 'two-member-registry', count=2)
        self.addCleanup(self.fixture.broker.close)
        evidence = self.evidence(self.grid())
        for corrupt in ('omitted', 'reordered', 'other-compiled', 'other-grid'):
            changed = deepcopy(evidence)
            bindings = changed['outcome_reservation']['plan_bindings']
            if corrupt == 'omitted':
                bindings.pop()
            elif corrupt == 'reordered':
                bindings.reverse()
            elif corrupt == 'other-compiled':
                bindings[0]['compiled_id'] = bindings[1]['compiled_id']
            else:
                bindings[1]['grid'] = self.grid(1577923200)
            with self.subTest(corrupt=corrupt), self.assertRaises((Invalid, Denied, Conflict)):
                self.fixture.freeze(admission=changed)
            self.assert_no_commit()
        manifest = self.fixture.freeze(admission=evidence)
        self.assertEqual(2, manifest['body']['primary_count'])
        self.assertEqual(1, evidence['outcome_reservation']['grid']['event_count'])
        self.assert_bound(manifest, evidence['outcome_reservation'])

    def test_same_event_cannot_reset_prior_use_with_other_claim_campaign_or_record_aliases(self):
        grid = self.grid()
        original = self.fixture.freeze(admission=self.evidence(grid, records=['invented-old-label']))
        request = self.another_family('new-snapshot-revision-program-claim')
        with self.assertRaises(Conflict):
            self.fixture.freeze(request, self.evidence(grid, request, records=['invented-new-label']))
        self.assertEqual([1, 1, 1],
                         [len(self.fixture.artifacts(schema)) for schema in COMMITTED])
        self.assertEqual(original, self.fixture.op('get_artifact', artifact_id=original['id']))
        self.assertEqual('FAILED', self.fixture.artifacts('scientific-freeze-attempt/1')[-1]['body']['status'])

    def test_disjoint_event_grids_cannot_reuse_a_qualified_completed_record(self):
        records = ['synthetic-qualified-completed-record-shared-by-two-resolutions']
        original = self.fixture.freeze(admission=self.evidence(self.grid(), records=records))
        request = self.another_family('disjoint-events-same-completed-record')
        later = self.evidence(self.grid(1577923200), request, records=records)
        # Both grids are explicitly fixed and a full day apart. A second,
        # independent completed-record collision rule must still reject reuse.
        self.assertEqual(1577836800,
            original['body']['outcome_reservation']['grid']['ranges'][0]['decision_start'])
        self.assertEqual(1577923200,
            later['outcome_reservation']['grid']['ranges'][0]['decision_start'])
        with self.assertRaises(Conflict):
            self.fixture.freeze(request, later)
        self.assertEqual([1, 1, 1],
                         [len(self.fixture.artifacts(schema)) for schema in COMMITTED])
        self.assertEqual(original, self.fixture.op('get_artifact', artifact_id=original['id']))
        attempt = self.fixture.artifacts('scientific-freeze-attempt/1')[-1]
        self.assertEqual('FAILED', attempt['body']['status'])
        self.assertEqual('Conflict', attempt['body']['failure_type'])

    def test_adjacent_distinct_events_are_not_unconditionally_banned_for_raw_overlap(self):
        first = self.fixture.freeze(admission=self.evidence(self.grid(), records=['invented-first']))
        request = self.another_family('adjacent-return')
        second_evidence = self.evidence(self.grid(1577837700), request,
                                        records=['invented-second'])
        # Hand-fixed one-bar prices share 00:15, despite different event pairs.
        self.assertEqual({1577837700}, {1577836800, 1577837700} & {1577837700, 1577838600})
        self.assertEqual('NOT_QUALIFIED',
            second_evidence['outcome_reservation']['dependence_exposure_prior_use'])
        second = self.fixture.freeze(request, second_evidence)
        self.assertNotEqual(first['id'], second['id'])
        self.assert_bound(second, second_evidence['outcome_reservation'])
        self.assertEqual([2, 2, 2],
                         [len(self.fixture.artifacts(schema)) for schema in COMMITTED])

    def test_zero_potential_event_grid_cannot_allocate(self):
        boundary_only = fixed.expected_grid([], [fixed.span(1577836800, 1577838600, 2)], 0, 2)
        with self.assertRaises((Invalid, Denied, Conflict)):
            self.fixture.freeze(admission=self.evidence(boundary_only))
        self.assert_no_commit()

    def test_midcommit_failure_retains_failed_attempt_without_partial_reservation(self):
        evidence = self.evidence(self.grid())
        saved = self.fixture.broker._freeze_save
        attempted = []

        def interrupt(schema, body, *args, **kwargs):
            if schema == 'scientific-trial/1':
                attempted.append(deepcopy(body))
                raise RuntimeError('Independent D099 interruption after allocation before trial')
            return saved(schema, body, *args, **kwargs)

        with patch.object(self.fixture.broker, '_freeze_save', side_effect=interrupt):
            with self.assertRaises(RuntimeError):
                self.fixture.freeze(admission=evidence)
        self.assertEqual(1, len(attempted))
        self.assert_no_commit()
        self.assertEqual('FAILED', self.fixture.artifacts('scientific-freeze-attempt/1')[-1]['body']['status'])
        manifest = self.fixture.freeze(admission=evidence)
        self.assert_bound(manifest, evidence['outcome_reservation'])
        self.assertEqual([1, 1, 1],
                         [len(self.fixture.artifacts(schema)) for schema in COMMITTED])

    def test_duplicate_restart_and_restore_preserve_exact_reservation_and_budget_identity(self):
        evidence = self.evidence(self.grid())
        request = self.fixture.request()
        manifest = self.fixture.freeze(admission=evidence)
        retained = [*self.fixture.artifacts('scientific-allocation/1'),
                    *self.fixture.artifacts('scientific-trial/1'), manifest]
        self.assertEqual(manifest, self.fixture.op('freeze_scientific_batch', **request))
        directory = self.fixture.broker.directory
        self.fixture.broker.close()
        restarted = Broker(directory)
        self.addCleanup(restarted.close)
        self.assertEqual(manifest,
            restarted.call(restarted.admin_token, 'freeze_scientific_batch', **request))
        backup = self.root / 'backup'
        self.assertEqual('PASS', restarted.call(restarted.admin_token, 'backup_bundle',
                                               destination=str(backup))['status'])
        restored_path = self.root / 'restored'
        self.assertEqual('PASS', restore_bundle(backup, restored_path,
                                               directory / 'operator.key')['status'])
        restored = Broker(restored_path)
        self.addCleanup(restored.close)
        self.assertEqual(manifest,
            restored.call(restored.admin_token, 'freeze_scientific_batch', **request))
        for original in retained:
            self.assertEqual(original, restored.call(restored.admin_token, 'get_artifact',
                                                     artifact_id=original['id']))
        for schema in COMMITTED:
            self.assertEqual(1, len(restored._freeze_objects(schema)))

    def test_legacy_unknown_is_exact_history_and_cannot_be_inferred_disjoint(self):
        request = self.fixture.request()
        historical = self.fixture.freeze()  # Existing explicitly synthetic pre-D099 private seam.
        allocation = self.fixture.op('get_artifact', artifact_id=historical['body']['allocation_id'])
        self.assertNotIn('outcome_reservation', historical['body'])
        self.assertNotIn('outcome_reservation', allocation['body'])
        self.assertEqual(historical, self.fixture.op('freeze_scientific_batch', **request))
        later_request = self.another_family('unknown-history')
        with self.assertRaises(Conflict):
            self.fixture.freeze(later_request,
                self.evidence(self.grid(1577923200), later_request, records=['different-label']))
        self.assertEqual(historical, self.fixture.op('get_artifact', artifact_id=historical['id']))
        self.assertEqual(allocation, self.fixture.op('get_artifact', artifact_id=allocation['id']))
        self.assertEqual([1, 1, 1],
                         [len(self.fixture.artifacts(schema)) for schema in COMMITTED])

    def test_new_version_cannot_be_bypassed_by_later_unmapped_legacy_resolution(self):
        original = self.fixture.freeze(admission=self.evidence(self.grid()))
        request = self.another_family('later-legacy-mode')
        legacy = self.fixture.admission(request)
        legacy['outcome_record_ids'] = ['a-different-unmapped-legacy-label']
        with self.assertRaises(Conflict):
            self.fixture.freeze(request, legacy)
        self.assertEqual(original, self.fixture.op('get_artifact', artifact_id=original['id']))
        self.assertEqual([1, 1, 1],
                         [len(self.fixture.artifacts(schema)) for schema in COMMITTED])

    def test_public_reservation_override_is_rejected_before_private_judgment(self):
        forged = fixed_reservation(self.grid(), [])
        with patch.object(self.fixture.broker, '_scientific_freeze_admission',
                          side_effect=AssertionError('Public override reached private judgment')) as admission:
            for change in ({'outcome_reservation': forged}, {'event_ids': ['invented']},
                           {'grid': self.grid()}, {'market_domain': 'binance-spot'}):
                with self.subTest(change=change), self.assertRaises((Invalid, Denied, Conflict)):
                    self.fixture.op('freeze_scientific_batch', **self.fixture.request(**change))
        admission.assert_not_called()
        self.assert_no_commit()

    def test_unowned_legacy_plan_is_unknown_without_fabricated_grid_or_outcome_reads(self):
        originals = deepcopy([*self.fixture.plans, *self.fixture.compiled])
        with patch.object(self.fixture.broker, '_load_reference_data',
                          side_effect=AssertionError('Legacy metadata caused outcome read')):
            result = self.fixture.op('freeze_scientific_batch', **self.fixture.request())
        self.assertEqual('ADMISSION_GAP', result['body']['status'])
        resolution = result['body']['admission']
        self.assertIn('OUTCOME_RESERVATION_METADATA_NOT_QUALIFIED', resolution['gaps'])
        self.assertEqual({'profile': 'outcome-reservation/1.0', 'status': 'RESERVATION_GAP',
            'identity_version': 'UNKNOWN', 'failure_type': 'Invalid',
            'raw_input_membership': 'NOT_QUALIFIED',
            'dependence_exposure_prior_use': 'NOT_QUALIFIED',
            'scientific_readiness': False}, resolution['admission']['outcome_reservation'])
        for original in originals:
            self.assertEqual(original,
                self.fixture.op('get_artifact', artifact_id=original['id']))
        self.assertEqual([], resolution['claims'])
        self.assertEqual([], resolution['outcome_record_ids'])
        self.assert_no_commit()


class OutcomeReservationOwnedCallerIndependentTests(unittest.TestCase):
    """Real owned metadata path; no private admission judgment substitution."""

    setUpClass = classmethod(plan_support.EvaluationPlanTests.setUpClass.__func__)
    tearDownClass = classmethod(plan_support.EvaluationPlanTests.tearDownClass.__func__)
    arguments = plan_support.EvaluationPlanTests.arguments

    @contextmanager
    def guarded_freeze(self, broker):
        """Custody hashes may run; no row expansion or outcome calculation may."""
        with ExitStack() as stack:
            for name in ('_load_reference_data', '_scan_data'):
                stack.enter_context(patch.object(broker, name,
                    side_effect=AssertionError('Potential reservation inspected outcome rows')))
            for target in ('trading_researcher.binding.run_child',
                           'trading_researcher.evaluation_plans.run_plan_child',
                           'trading_researcher.outcomes.materialize_reference',
                           'trading_researcher.outcomes._lookback'):
                stack.enter_context(patch(target,
                    side_effect=AssertionError('Potential reservation computed outcomes')))
            yield

    def owned_clone(self, label):
        """Each destructive case gets fresh copied blobs, never a hardlink alias."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        backup = root / 'preserved-backup'
        self.assertEqual('PASS', self.broker.call(self.token, 'backup_bundle',
                                                 destination=str(backup))['status'])
        restored = root / 'working-copy'
        self.assertEqual('PASS', restore_bundle(backup, restored,
            self.broker.directory / 'operator.key')['status'])
        clone = Broker(restored)
        self.addCleanup(clone.close)
        inherited_attempts = deepcopy(clone._freeze_objects('scientific-freeze-attempt/1'))
        plan = clone.call(clone.admin_token, 'prepare_evaluation_plan',
                         **self.arguments('d099-isolated-' + label))
        self.assertEqual('POLICY_DRAFT', plan['body']['status'])
        anchor = clone.call(clone.admin_token, 'add_source',
            body={'purpose': 'Owned synthetic D099 isolation case ' + label},
            data_class='development')
        request = {'key': 'd099-isolated-freeze-' + label, 'campaign_id': anchor['id'],
                   'role': 'primary', 'plan_ids': [plan['id']],
                   'selection_record_ref': anchor['id'], 'reservation_spec_ref': anchor['id']}
        with self.guarded_freeze(clone):
            before = clone.call(clone.admin_token, 'freeze_scientific_batch', **request)
        self.assertEqual('ADMISSION_GAP', before['body']['status'])
        metadata = before['body']['admission']['admission']['outcome_reservation']
        self.assertEqual('POTENTIAL_GRID_BOUND', metadata['status'],
                         'The negative case must begin with genuinely bound metadata')
        self.assertEqual(fixed.expected_grid([fixed.span(1577837700, 1577839500)],
            [fixed.span(1577839500, 1577840400)], 2, 1), metadata['grid'])
        self.assertIs(metadata['scientific_readiness'], False)
        attempts = clone._freeze_objects('scientific-freeze-attempt/1')
        self.assertEqual(inherited_attempts, attempts[:-1])
        self.assertEqual(len(inherited_attempts) + 1, len(attempts))
        self.assertEqual(before, attempts[-1])
        return clone, request, plan, backup, before, inherited_attempts

    def assert_public_metadata_gap(self, broker, result, failure_type, before, inherited_attempts):
        self.assertEqual('ADMISSION_GAP', result['body']['status'])
        for flag in ('scientific_readiness', 'frozen', 'allocation_reserved'):
            self.assertIs(result['body'][flag], False)
        resolution = result['body']['admission']
        self.assertIn('OUTCOME_RESERVATION_METADATA_NOT_QUALIFIED', resolution['gaps'])
        for gap in ('SCIENTIFIC_SELECTION_AND_RESERVATION_NOT_QUALIFIED',
                    'SCIENTIFIC_DATA_AND_EXPOSURE_NOT_ADMITTED',
                    'CALIBRATED_ESTIMATOR_AND_INFORMATION_PLAN_NOT_ADMITTED'):
            self.assertIn(gap, resolution['gaps'])
        expected = {'profile': 'outcome-reservation/1.0', 'status': 'RESERVATION_GAP',
                    'identity_version': 'UNKNOWN', 'failure_type': failure_type,
                    'raw_input_membership': 'NOT_QUALIFIED',
                    'dependence_exposure_prior_use': 'NOT_QUALIFIED',
                    'scientific_readiness': False}
        self.assertEqual(expected, resolution['admission']['outcome_reservation'])
        self.assertEqual(expected, resolution['outcome_reservation'])
        self.assertEqual([], resolution['claims'])
        self.assertEqual([], resolution['outcome_record_ids'])
        for schema in COMMITTED:
            self.assertEqual([], broker._freeze_objects(schema))
        attempts = broker._freeze_objects('scientific-freeze-attempt/1')
        self.assertEqual(len(inherited_attempts) + 2, len(attempts))
        self.assertEqual(inherited_attempts, attempts[:-2])
        self.assertEqual([before, result], attempts[-2:])

    def assert_baseline_records_unchanged(self):
        for original in (self.compiled, self.fixture.snapshot,
                         self.fixture.reference, self.fixture.feature):
            self.assertEqual(original, self.broker.call(self.token, 'get_artifact',
                                                       artifact_id=original['id']))

    def test_public_revoked_dependency_rechecks_metadata_without_granting_admission(self):
        clone, request, plan, _, before, inherited = self.owned_clone('revoked-feature')
        original = deepcopy(clone.call(clone.admin_token, 'get_artifact',
                                       artifact_id=self.fixture.feature['id']))
        evidence = clone.call(clone.admin_token, 'add_source',
            body={'defect': 'Synthetic fixture revocation for the D099 consuming caller'},
            data_class='operations')
        clone.call(clone.admin_token, 'revoke_dependency', key='d099-revoke-feature',
            dependency_id=original['id'], reason='Independent synthetic dependency revocation',
            evidence_refs=[evidence['id']])
        self.assertEqual('INVALIDATED_BY_DEPENDENCY',
            clone.call(clone.admin_token, 'inspect_dependency_use', artifact_id=plan['id'])['status'])
        with self.guarded_freeze(clone):
            result = clone.call(clone.admin_token, 'freeze_scientific_batch', **request)
        self.assert_public_metadata_gap(clone, result, 'Denied', before, inherited)
        self.assertEqual(before['body']['input_id'], result['body']['input_id'])
        self.assertEqual(original, clone.call(clone.admin_token, 'get_artifact',
                                              artifact_id=original['id']))
        self.assertEqual(plan, clone.call(clone.admin_token, 'get_artifact', artifact_id=plan['id']))
        self.assertEqual('NOT_REVOKED', self.broker.call(self.token,
            'inspect_dependency_use', artifact_id=original['id'])['status'])
        self.assert_baseline_records_unchanged()

    def test_public_retained_runtime_currentness_failure_remains_unknown_metadata(self):
        clone, request, plan, _, before, inherited = self.owned_clone('runtime-currentness')
        # This narrowly substitutes the existing currentness predicate's verdict;
        # no runtime/source file or admission resolver is modified or replaced.
        with self.guarded_freeze(clone), patch(
                'trading_researcher.outcome_reservations._environment_current',
                return_value=False) as current:
            result = clone.call(clone.admin_token, 'freeze_scientific_batch', **request)
        current.assert_called_once_with(self.compiled['body']['environment'])
        self.assert_public_metadata_gap(clone, result, 'Invalid', before, inherited)
        self.assertEqual(before['body']['input_id'], result['body']['input_id'])
        self.assertEqual(plan, clone.call(clone.admin_token, 'get_artifact', artifact_id=plan['id']))
        self.assert_baseline_records_unchanged()

    def test_public_corrupt_copied_row_blob_is_unknown_and_preserved_copies_stay_intact(self):
        clone, request, plan, backup, before, inherited = self.owned_clone('corrupt-normalized-rows')
        self.assertEqual(1, len(self.fixture.snapshot['blob_refs']))
        identity = self.fixture.snapshot['blob_refs'][0]
        original_path = self.broker._blob_path(identity)
        copied_path = clone._blob_path(identity)
        backup_path = backup / copied_path.relative_to(clone.directory)
        self.assertTrue(copied_path.resolve().is_relative_to(clone.directory.resolve()))
        self.assertTrue(backup_path.resolve().is_relative_to(backup.resolve()))
        self.assertFalse(copied_path.samefile(original_path))
        self.assertFalse(copied_path.samefile(backup_path))
        self.assertEqual(identity, hashlib.sha256(original_path.read_bytes()).hexdigest())
        self.assertEqual(identity, hashlib.sha256(backup_path.read_bytes()).hexdigest())
        copied_path.write_bytes(b'Independent corrupted owned synthetic normalized row blob\n')
        self.assertNotEqual(identity, hashlib.sha256(copied_path.read_bytes()).hexdigest())
        with self.guarded_freeze(clone):
            result = clone.call(clone.admin_token, 'freeze_scientific_batch', **request)
        self.assert_public_metadata_gap(clone, result, 'Invalid', before, inherited)
        self.assertEqual(before['body']['input_id'], result['body']['input_id'])
        self.assertEqual(plan, clone.call(clone.admin_token, 'get_artifact', artifact_id=plan['id']))
        self.assertEqual(identity, hashlib.sha256(original_path.read_bytes()).hexdigest())
        self.assertEqual(identity, hashlib.sha256(backup_path.read_bytes()).hexdigest())
        self.assert_baseline_records_unchanged()

    def test_genuine_owned_plan_retains_grid_sources_and_all_scientific_gaps_without_outcome_reads(self):
        plan = self.broker.call(self.token, 'prepare_evaluation_plan',
                                **self.arguments('d099-real-owned-plan'))
        source = self.broker.call(self.token, 'add_source',
            body={'purpose': 'Invented engineering campaign/selection; no scientific qualification'},
            data_class='development')
        expected = fixed.expected_grid([fixed.span(1577837700, 1577839500)],
                                       [fixed.span(1577839500, 1577840400)], 2, 1)
        guards = ('trading_researcher.binding.run_child',
                  'trading_researcher.evaluation_plans.run_plan_child',
                  'trading_researcher.outcomes.materialize_reference',
                  'trading_researcher.outcomes._lookback')
        with ExitStack() as stack:
            stack.enter_context(patch.object(self.broker, '_load_reference_data',
                side_effect=AssertionError('Potential reservation loaded outcome rows')))
            stack.enter_context(patch.object(self.broker, '_scan_data',
                side_effect=AssertionError('Potential reservation scanned outcome rows')))
            for path in guards:
                stack.enter_context(patch(path,
                    side_effect=AssertionError('Potential reservation invoked outcome computation')))
            result = self.broker.call(self.token, 'freeze_scientific_batch',
                key='d099-real-gapped-freeze', campaign_id=source['id'], role='primary',
                plan_ids=[plan['id']], selection_record_ref=source['id'],
                reservation_spec_ref=source['id'])
        self.assertEqual('ADMISSION_GAP', result['body']['status'])
        for flag in ('scientific_readiness', 'frozen', 'allocation_reserved'):
            self.assertIs(result['body'][flag], False)
        resolution = result['body']['admission']
        for gap in ('SCIENTIFIC_SELECTION_AND_RESERVATION_NOT_QUALIFIED',
                    'SCIENTIFIC_DATA_AND_EXPOSURE_NOT_ADMITTED',
                    'CALIBRATED_ESTIMATOR_AND_INFORMATION_PLAN_NOT_ADMITTED'):
            self.assertIn(gap, resolution['gaps'])
        metadata = resolution['admission']['outcome_reservation']
        self.assertEqual('outcome-reservation/1.0', metadata['profile'])
        self.assertEqual('POTENTIAL_GRID_BOUND', metadata['status'])
        self.assertEqual(expected, metadata['grid'])
        self.assertEqual('NOT_QUALIFIED', metadata['raw_input_membership'])
        self.assertEqual('NOT_OBSERVED', metadata['actual_inputs_and_publication'])
        self.assertEqual('NOT_QUALIFIED', metadata['dependence_exposure_prior_use'])
        self.assertIs(metadata['scientific_readiness'], False)
        self.assertEqual(1, len(metadata['plan_bindings']))
        binding = metadata['plan_bindings'][0]
        body = self.compiled['body']
        self.assertEqual(plan['id'], binding['plan_id'])
        self.assertEqual(self.compiled['id'], binding['compiled_id'])
        self.assertEqual(self.fixture.snapshot['id'], binding['data_snapshot_id'])
        self.assertEqual('bound-reference/1', binding['compilation_profile'])
        self.assertEqual(body['source_package_id'], binding['compilation_source_package_id'])
        package = self.broker.call(self.token, 'get_artifact', artifact_id=body['source_package_id'])
        self.assertEqual(package['body']['footprint'], binding['compilation_source_footprint'])
        self.assertEqual(self.fixture.reference['id'], binding['reference_certificate_id'])
        self.assertEqual(self.fixture.feature['id'], binding['feature_certificate_id'])
        self.assertEqual(self.fixture.feature['body']['definitions_id'], binding['feature_definitions_id'])
        self.assertEqual(self.fixture.normalization['id'], binding['normalization_id'])
        self.assertEqual(independent_hash(self.fixture.snapshot['body']['manifest']),
                         binding['snapshot_manifest_hash'])
        self.assertEqual(independent_hash(body['compilation_input']['candidate']),
                         binding['compiled_candidate_hash'])
        self.assertEqual(independent_hash(body['compilation']['request']),
                         binding['compilation_request_hash'])
        self.assertEqual(expected, binding['grid'])
        self.assertEqual(sorted(set(binding['source_refs'])), binding['source_refs'])
        for identity in (plan['id'], self.compiled['id'], self.fixture.snapshot['id'],
                         self.fixture.reference['id'], self.fixture.feature['id'],
                         self.fixture.normalization['id'], body['source_package_id']):
            self.assertIn(identity, binding['source_refs'])
        self.assertEqual(binding['source_refs'], metadata['artifact_ids'])
        self.assertEqual([], resolution['claims'])
        self.assertEqual([], resolution['outcome_record_ids'])
        for schema in COMMITTED:
            self.assertEqual([], self.broker._freeze_objects(schema))
        self.assertEqual(plan, self.broker.call(self.token, 'get_artifact', artifact_id=plan['id']))

    def test_scope_program_claim_label_and_asof_do_not_manufacture_other_potential_events(self):
        first = self.broker.call(self.token, 'prepare_evaluation_plan',
                                 **self.arguments('d099-scope-original'))
        candidate = deepcopy(self.fixture.base['candidate'])
        candidate['estimand']['unit'] = 'ratio'
        candidate['outcome']['scale'] = 'binary_probability'
        candidate['outcome']['program']['expression'] = {
            'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}
        candidate['scope_ast']['expression']['value'] = False
        candidate['parameter_origins'].append({
            'path': '/outcome/program/expression/value', 'basis': 'preexisting_specification',
            'source_refs': [], 'rationale': 'Invented infrastructure fixture, no market claim.'})
        case = {'change': {'candidate': candidate, 'original_idea_text':
            'A separately labelled synthetic scope-false Boolean fixture; no discovered market claim.'}}
        formalization = self.fixture.create_formalization(case)
        compiled = self.fixture.compile(formalization, case, as_of='2020-01-01T00:15:00Z')
        self.assertEqual('COMPILED', compiled['body']['status'])
        second = self.broker.call(self.token, 'prepare_evaluation_plan',
            **{**self.arguments('d099-scope-other'), 'compiled_id': compiled['id']})
        self.assertEqual('POLICY_DRAFT', second['body']['status'])
        source = self.broker.call(self.token, 'add_source',
            body={'purpose': 'Synthetic family with different scope/as-of metadata only'},
            data_class='development')
        with ExitStack() as stack:
            for name in ('_load_reference_data', '_scan_data'):
                stack.enter_context(patch.object(self.broker, name,
                    side_effect=AssertionError('Metadata identity inspected outcome rows')))
            for target in ('trading_researcher.binding.run_child',
                           'trading_researcher.evaluation_plans.run_plan_child',
                           'trading_researcher.outcomes.materialize_reference',
                           'trading_researcher.outcomes._lookback'):
                stack.enter_context(patch(target,
                    side_effect=AssertionError('Metadata identity computed outcomes')))
            result = self.broker.call(self.token, 'freeze_scientific_batch',
                key='d099-scope-metadata-family', campaign_id=source['id'], role='primary',
                plan_ids=[first['id'], second['id']], selection_record_ref=source['id'],
                reservation_spec_ref=source['id'])
        self.assertEqual('ADMISSION_GAP', result['body']['status'])
        metadata = result['body']['admission']['admission']['outcome_reservation']
        self.assertEqual('POTENTIAL_GRID_BOUND', metadata['status'])
        expected = fixed.expected_grid([fixed.span(1577837700, 1577839500)],
                                       [fixed.span(1577839500, 1577840400)], 2, 1)
        self.assertEqual(expected, metadata['grid'])
        self.assertEqual([first['id'], second['id']],
                         [binding['plan_id'] for binding in metadata['plan_bindings']])
        left, right = metadata['plan_bindings']
        self.assertEqual(expected, left['grid'])
        self.assertEqual(expected, right['grid'])
        self.assertNotEqual(left['compiled_id'], right['compiled_id'])
        self.assertNotEqual(left['compiled_candidate_hash'], right['compiled_candidate_hash'])
        self.assertNotEqual(left['compilation_request_hash'], right['compilation_request_hash'])
        self.assertEqual('NOT_OBSERVED', metadata['actual_inputs_and_publication'])
        self.assertEqual('NOT_QUALIFIED', metadata['dependence_exposure_prior_use'])
        self.assertIs(metadata['scientific_readiness'], False)


if __name__ == '__main__':
    unittest.main()
