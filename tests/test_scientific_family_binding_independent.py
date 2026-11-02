"""Independent atomic family-policy binding; temporary synthetic records only.

D075/D082 and research-contract/1.0 sections 5.2/12 assign 0.05/m using the
complete frozen primary family. Topic labels and preparation declarations do not
divide that family. Expected fractions below are literal hand-derived values;
no production arithmetic helper supplies them.

FreezeFixture replaces only the private admission judgment for transaction
checks. Its plans, compiled records and outcomes remain synthetic. One separate
case uses the unchanged real resolver and must retain ADMISSION_GAP. These tests
qualify no calibration, scientific admission, protected access or trading result.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_scientific_freeze_independent as support
from trading_researcher.codec import canonical
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.storage import restore_bundle


BINDING_VERSION = 'scientific-family-policy-binding/1'
PREPARATION_AUTHORITY = 'declared_preparation_only_recompute_from_frozen_batch'
COMMON_POLICY = {'profile': 'historical-batch-v1',
    'family_noncoverage': {'numerator': '1', 'denominator': '20'},
    'interval_sides': 2, 'allocation': 'union_bound', 'fixed_releases': 1,
    'independence_between_claims_required': False, 'valid_marginal_coverage_required': True}
EXPECTED = {
    1: {**COMMON_POLICY, 'primary_count': 1,
        'marginal_noncoverage': {'numerator': '1', 'denominator': '20'}},
    2: {**COMMON_POLICY, 'primary_count': 2,
        'marginal_noncoverage': {'numerator': '1', 'denominator': '40'}},
    8: {**COMMON_POLICY, 'primary_count': 8,
        'marginal_noncoverage': {'numerator': '1', 'denominator': '160'}},
}
COMMITTED = ('scientific-allocation/1', 'scientific-trial/1', 'frozen-manifest/1')


class ScientificFamilyBindingIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='trf-scientific-family-independent-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def fixture(self, name, count=2):
        fixture = support.FreezeFixture(self.root / name, count=count)
        self.addCleanup(lambda: fixture.broker.close())
        # Deliberately conflicting preparation metadata, not certified plans.
        # Retain each source as immutable input; the private admission seam is
        # explicit and cannot turn this into genuine scientific qualification.
        plans = []
        for index, compiled in enumerate(fixture.compiled):
            plans.append(fixture.op('add_source', data_class='development', exposure=[compiled['id']],
                body={'schema': 'independent-family-preparation-fixture/1',
                    'fixture_scope': 'Synthetic preparation declaration; no owned plan or scientific certificate.',
                    'family_count_authority': PREPARATION_AUTHORITY,
                    'plan': {'family_policy': deepcopy(EXPECTED[1]), 'scientific_readiness': False},
                    'descriptive_topic_group': 'separate-topic-' + str(index)}))
            fixture.claims[index]['plan_id'] = plans[-1]['id']
        fixture.plans = plans
        return fixture

    def assert_bound(self, fixture, manifest, count):
        expected = EXPECTED[count]
        allocation = fixture.op('get_artifact', artifact_id=manifest['body']['allocation_id'])
        trials = [fixture.op('get_artifact', artifact_id=identity) for identity in manifest['body']['trial_ids']]
        nodes = [('manifest', manifest['body']), ('allocation', allocation['body']),
                 ('allocation.signature', allocation['body']['signature'])]
        nodes.extend(('trial-' + str(index), trial['body']) for index, trial in enumerate(trials))
        for name, body in nodes:
            self.assertIn('family_policy', body, name + ' omitted the independently assigned frozen-family policy')
            self.assertEqual(body['family_policy'], expected, name)
            self.assertEqual(body.get('family_policy_binding_version'), BINDING_VERSION, name)
        self.assertEqual(manifest['body']['primary_count'], count)
        self.assertEqual(allocation['body']['primary_count'], count)
        self.assertEqual(allocation['body']['signature']['claims'], fixture.claims)
        self.assertEqual([trial['body']['claim_id'] for trial in trials], [claim['claim_id'] for claim in fixture.claims])
        self.assertEqual([trial['body']['plan_id'] for trial in trials], fixture.request()['plan_ids'])
        self.assertIs(allocation['body']['refund_permitted'], False)
        return allocation, trials

    def assert_no_commit(self, fixture):
        for schema in COMMITTED:
            self.assertEqual(fixture.artifacts(schema), [], schema)

    def test_hand_fixed_single_two_and_eight_claim_families_bind_identical_policy_everywhere(self):
        for count in (1, 2, 8):
            with self.subTest(count=count):
                fixture = self.fixture('fixed-' + str(count), count)
                manifest = fixture.freeze()
                self.assert_bound(fixture, manifest, count)

    def test_two_admitted_claims_override_draft_one_and_topic_labels_without_rewriting_inputs(self):
        fixture = self.fixture('actual-two', 2)
        originals = {plan['id']: canonical(plan).encode() for plan in fixture.plans}
        self.assertEqual(len({plan['body']['descriptive_topic_group'] for plan in fixture.plans}), 2)
        for plan in fixture.plans:
            self.assertEqual(plan['body']['family_count_authority'], PREPARATION_AUTHORITY)
            self.assertEqual(plan['body']['plan']['family_policy'], EXPECTED[1])
        manifest = fixture.freeze()
        self.assert_bound(fixture, manifest, 2)
        for identity, original in originals.items():
            self.assertEqual(canonical(fixture.op('get_artifact', artifact_id=identity)).encode(), original)

    def test_exact_duplicate_restart_and_backup_preserve_the_same_policy_and_binding_version(self):
        fixture = self.fixture('durable-two', 2)
        manifest = fixture.freeze()
        allocation, trials = self.assert_bound(fixture, manifest, 2)
        duplicate = fixture.freeze(fixture.request(key='duplicate-new-delivery'))
        self.assertEqual(duplicate, manifest)
        self.assertEqual([len(fixture.artifacts(schema)) for schema in COMMITTED], [1, 2, 1])
        original_plans = deepcopy(fixture.plans)
        fixture.broker.close()
        fixture.broker = Broker(self.root / 'durable-two')
        fixture.token = fixture.broker.admin_token
        with patch.object(fixture.broker, '_scientific_freeze_admission', side_effect=AssertionError('Historical lookup re-admitted science')):
            self.assertEqual(fixture.op('freeze_scientific_batch', **fixture.request()), manifest)
        self.assert_bound(fixture, manifest, 2)
        backup = self.root / 'family-backup'
        self.assertEqual(fixture.op('backup_bundle', destination=str(backup))['status'], 'PASS')
        restored_dir = self.root / 'family-restored'
        self.assertEqual(restore_bundle(backup, restored_dir, fixture.broker.directory / 'operator.key')['status'], 'PASS')
        restored = Broker(restored_dir)
        self.addCleanup(restored.close)
        for artifact in (manifest, allocation, *trials, *original_plans):
            self.assertEqual(restored.call(restored.admin_token, 'get_artifact', artifact_id=artifact['id']), artifact)
        self.assertEqual(restored.call(restored.admin_token, 'freeze_scientific_batch', **fixture.request()), manifest)
        self.assertEqual(restored.call(restored.admin_token, 'verify')['status'], 'PASS')

    def test_midcommit_failure_retains_attempt_without_partial_policy_then_recovers_atomically(self):
        fixture = self.fixture('rollback-two', 2)
        original_save = fixture.broker._freeze_save
        trial_saves = []
        def interrupt(schema, body, *args, **kwargs):
            if schema == 'scientific-trial/1':
                trial_saves.append(deepcopy(body))
                if len(trial_saves) == 2:
                    raise RuntimeError('Independent interruption after allocation and first trial')
            return original_save(schema, body, *args, **kwargs)
        with patch.object(fixture.broker, '_freeze_save', side_effect=interrupt), self.assertRaises(RuntimeError):
            fixture.freeze()
        self.assertEqual(len(trial_saves), 2)
        self.assert_no_commit(fixture)
        attempts = fixture.op('inspect_scientific_freezes')['attempts']
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]['body']['status'], 'FAILED')
        self.assertIs(attempts[0]['body']['allocation_reserved'], False)
        manifest = fixture.freeze()
        self.assert_bound(fixture, manifest, 2)
        self.assertEqual([len(fixture.artifacts(schema)) for schema in COMMITTED], [1, 2, 1])
        self.assertEqual(len(fixture.artifacts('scientific-freeze-input/1')), 1)

    def test_public_policy_count_or_marker_overrides_cannot_reach_private_admission(self):
        fixture = self.fixture('forged-override', 2)
        changes = ({'family_policy': EXPECTED[1]}, {'primary_count': 1},
                   {'family_policy_binding_version': BINDING_VERSION},
                   {'marginal_noncoverage': {'numerator': '1', 'denominator': '20'}},
                   {'family_count_authority': 'caller-assigned'}, {'topic_families': [['first'], ['second']]})
        with patch.object(fixture.broker, '_scientific_freeze_admission', side_effect=AssertionError('Forged policy reached admission')) as admission:
            for change in changes:
                with self.subTest(change=change), self.assertRaises((Invalid, Denied, Conflict)):
                    fixture.op('freeze_scientific_batch', **fixture.request(**change))
        admission.assert_not_called()
        self.assert_no_commit(fixture)

    def test_unmodified_real_resolver_retains_admission_gap_without_policy_commit(self):
        fixture = self.fixture('real-gap', 2)
        result = fixture.op('freeze_scientific_batch', **fixture.request())
        self.assertEqual(result['body']['schema'], 'scientific-freeze-attempt/1')
        self.assertEqual(result['body']['status'], 'ADMISSION_GAP')
        self.assertFalse(result['body']['frozen'])
        self.assertFalse(result['body']['allocation_reserved'])
        self.assert_no_commit(fixture)
        self.assertEqual(result['body']['admission']['claims'], [])

    def seed_legacy_history(self, fixture):
        """Seed prebinding-format history through trusted local fixture owners.

        This artificial old-format transaction is not an actual historical
        scientific certificate. It isolates read/idempotency compatibility; its
        absent policy fields must never be inferred or retrofitted on lookup.
        """
        evidence = fixture.admission()
        fixture.freeze(admission={**deepcopy(evidence), 'gaps': ['SYNTHETIC_HISTORY_SEED_ONLY']})
        capsule = fixture.artifacts('scientific-freeze-input/1')[0]
        broker = fixture.broker
        request = fixture.request()
        closure, exposure, blobs = broker._freeze_closure(evidence['artifact_ids'])
        exposure = sorted(set(exposure) | set(capsule['exposure']) | {capsule['id']})
        signature = {'campaign_id': request['campaign_id'], 'role': request['role'],
            'claims': deepcopy(evidence['claims']), 'selection_record_ref': request['selection_record_ref'],
            'reservation_spec_ref': request['reservation_spec_ref'],
            'outcome_record_ids': sorted(evidence['outcome_record_ids']), 'closure': closure,
            'admission': deepcopy(evidence['admission'])}
        with broker._transaction():
            allocation = broker._freeze_save('scientific-allocation/1', {'created_at': broker._now(),
                'contract': 'research-contract/1.0', 'campaign_id': request['campaign_id'], 'role': request['role'],
                'signature': signature, 'outcome_record_ids': sorted(evidence['outcome_record_ids']),
                'primary_count': 2, 'refund_permitted': False}, [capsule['id'], *closure], exposure, blobs=blobs)
            trials = [broker._freeze_save('scientific-trial/1', {'created_at': broker._now(), **claim,
                'allocation_id': allocation['id'], 'contract': 'research-contract/1.0',
                'scientific_readiness': True, 'frozen': True, 'assessment_access_authority': False},
                [allocation['id'], *closure], exposure) for claim in evidence['claims']]
            manifest = broker._freeze_save('frozen-manifest/1', {'created_at': broker._now(),
                'request': request, 'contract': 'research-contract/1.0', 'input_id': capsule['id'],
                'allocation_id': allocation['id'], 'trial_ids': [trial['id'] for trial in trials], 'primary_count': 2,
                'closure': closure, 'admission': evidence['admission'], 'scientific_readiness': True,
                'frozen': True, 'allocation_reserved': True, 'assessment_access_authority': False},
                [allocation['id'], *(trial['id'] for trial in trials), *closure], exposure, blobs=blobs)
            attempt = 'independent-legacy-history-seed'
            broker._event('controller', 'bound_computation_started', attempt_id=attempt,
                kind='scientific_freeze', input_ref=capsule['id'], retained_input_id=capsule['id'])
            broker._freeze_attempt(attempt, capsule, 'COMMITTED', manifest=manifest['id'])
        return manifest, allocation, trials

    def test_legacy_same_key_returns_exact_history_and_new_key_cannot_infer_or_upgrade_policy(self):
        fixture = self.fixture('legacy-history', 2)
        manifest, allocation, trials = self.seed_legacy_history(fixture)
        before = [deepcopy(item) for item in (manifest, allocation, *trials)]
        for item in before:
            self.assertNotIn('family_policy', item['body'])
            self.assertNotIn('family_policy_binding_version', item['body'])
        self.assertNotIn('family_policy', allocation['body']['signature'])
        self.assertNotIn('family_policy_binding_version', allocation['body']['signature'])
        with patch.object(fixture.broker, '_scientific_freeze_admission', side_effect=AssertionError('Legacy lookup re-admitted science')):
            self.assertEqual(fixture.op('freeze_scientific_batch', **fixture.request()), manifest)
        with self.assertRaises(Conflict): fixture.freeze(fixture.request(key='attempted-legacy-upgrade'))
        for item in before:
            self.assertEqual(fixture.op('get_artifact', artifact_id=item['id']), item)
        self.assertEqual([len(fixture.artifacts(schema)) for schema in COMMITTED], [1, 2, 1])


if __name__ == '__main__':
    unittest.main()
