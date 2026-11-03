"""Read-only prerequisite provenance is larger than successful commitments.

All graphs/bytes are invented in owned temporary Registries. Generic metadata
plans must remain production ADMISSION_GAP. Only explicitly labelled small
transaction cases substitute FreezeFixture's private host judgment; those cases
prove no actual scientific admission. No protected-data fixture/world is used.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_scientific_freeze_independent as support
from trading_researcher import codec, scientific_freeze as owner
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict
from trading_researcher.storage import restore_bundle


PROFILE = 'scientific-prerequisite-closure/1'
LIMITS = {'transitive_items': 4094, 'retained_exposure_items': 4096,
          'successful_commit_items': 256}
COMMITTED = ('scientific-allocation/1', 'scientific-trial/1', 'frozen-manifest/1')


def wire_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


class ScientificPrerequisiteClosureIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = support.FreezeFixture(self.root / 'registry')
        self.addCleanup(self.fixture.broker.close)
        self.serial = 0

    def owned(self, label, *, refs=(), exposure=(), blobs=()):
        return self.fixture.broker._save_artifact({'version': 'local-artifact/1',
            'creator': 'operator', 'origin': 'source', 'data_class': 'development',
            'source_refs': sorted(refs), 'exposure': sorted(exposure), 'blob_refs': sorted(blobs),
            'authority': 'synthetic_metadata_provenance_not_qualification',
            'body': {'fixture': label}})

    def chain(self, count, *, children=(), exposure=()):
        self.serial += 1
        nodes = []
        with self.fixture.broker._transaction():
            for index in range(count):
                refs = [nodes[-1]['id']] if nodes else [item['id'] for item in children]
                nodes.append(self.owned('chain-' + str(self.serial) + '-' + str(index),
                    refs=refs, exposure=exposure if index == count - 1 else ()))
        return nodes

    def blob_leaves(self, count):
        self.serial += 1
        leaves, identities = [], []
        with self.fixture.broker._transaction():
            for index in range(count):
                descriptor = self.fixture.broker._stage_blob_bytes(
                    ('Independent tiny closure blob ' + str(self.serial) + ':' + str(index)).encode())
                self.fixture.broker._register_blob(descriptor)
                identities.append(descriptor['sha256'])
            for offset in range(0, count, 256):
                leaves.append(self.owned('blob-leaf-' + str(self.serial) + '-' + str(offset),
                                          blobs=identities[offset:offset + 256]))
        return leaves, identities

    def roots(self, request):
        return [request[name] for name in ('campaign_id', 'selection_record_ref', 'reservation_spec_ref')] + request['plan_ids']

    def large(self, count=300, *, blobs=0, label='large'):
        leaves, identities = self.blob_leaves(blobs) if blobs else ([], [])
        tokens = ['opaque:prerequisite-' + label + '-one', 'opaque:prerequisite-' + label + '-two']
        nodes = self.chain(count, children=leaves, exposure=tokens)
        request = self.fixture.request(key=label, campaign_id=nodes[-1]['id'])
        # Expected graph membership is fixed by this fixture's construction,
        # not recomputed by a second copy of the production graph traversal.
        artifacts = {item['id'] for item in [*nodes, *leaves, self.fixture.selection,
            self.fixture.reservation, *self.fixture.plans, *self.fixture.compiled, self.fixture.ancestor]}
        exposure = artifacts | set(tokens) | {self.fixture.marker}
        return request, sorted(artifacts), sorted(exposure), sorted(identities), nodes, leaves

    def production_gap(self, request):
        with patch.object(self.fixture.broker, '_load_reference_data',
                          side_effect=AssertionError('Metadata closure loaded outcomes')):
            result = self.fixture.op('freeze_scientific_batch', **request)
        self.assertEqual('ADMISSION_GAP', result['body']['status'])
        self.assertIs(result['body']['scientific_readiness'], False)
        self.assertIs(result['body']['allocation_reserved'], False)
        self.assert_no_commit()
        return result

    def assert_no_commit(self):
        self.assertEqual([0, 0, 0], [len(self.fixture.artifacts(schema)) for schema in COMMITTED])

    def assert_versioned(self, artifact):
        self.assertEqual(PROFILE, artifact['body']['prerequisite_closure_profile'])
        self.assertEqual(LIMITS, artifact['body']['prerequisite_closure_limits'])
        self.assertLessEqual(len(artifact['source_refs']), 256)
        self.assertLessEqual(len(artifact.get('blob_refs', [])), 256)
        self.assertLessEqual(len(artifact['exposure']), 4096)
        self.assertLessEqual(len(wire_bytes(artifact)), 1048576)

    def test_large_production_gap_retains_complete_provenance_blobs_and_versioned_envelopes(self):
        request, artifacts, exposure, blobs, nodes, leaves = self.large(blobs=300)
        actual = self.fixture.broker._freeze_closure(self.roots(request), prerequisite=True)
        self.assertEqual((artifacts, exposure, blobs), actual)
        with self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_closure(self.roots(request))
        result = self.production_gap(request)
        capsule = self.fixture.artifacts('scientific-freeze-input/1')[0]
        for artifact in (capsule, result):
            self.assert_versioned(artifact)
        self.assertEqual(exposure, capsule['exposure'])
        self.assertEqual(sorted(set(exposure) | {capsule['id']}), result['exposure'])
        self.assertEqual(artifacts, result['body']['admission']['artifact_ids'])
        self.assertGreater(len(blobs), 256)
        self.assertEqual([], result.get('blob_refs', []))
        for leaf in leaves:
            self.assertLessEqual(len(leaf['blob_refs']), 256)
            self.assertEqual(leaf, self.fixture.op('get_artifact', artifact_id=leaf['id']))
        self.assertEqual(nodes[-1], self.fixture.op('get_artifact', artifact_id=nodes[-1]['id']))

    def test_exact_artifact_and_exposure_collection_limits_are_independent(self):
        nodes = self.chain(4094)
        expected_ids = sorted(item['id'] for item in nodes)
        self.assertEqual((expected_ids, expected_ids, []),
            self.fixture.broker._freeze_closure([nodes[-1]['id']], prerequisite=True))
        extra = self.chain(1, children=[nodes[-1]])
        with self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_closure([extra[-1]['id']], prerequisite=True)
        # Sixteen ordinary leaves plus one root:17known artifacts+4077opaque
        # tokens=4094exposure entries. No leaf exceeds the old256edge envelope.
        tokens = ['opaque:exact-exposure-' + str(index) for index in range(4077)]
        leaves = []
        with self.fixture.broker._transaction():
            for offset in range(0, len(tokens), 256):
                leaves.append(self.owned('exposure-leaf-' + str(offset), exposure=tokens[offset:offset + 256]))
        branch = self.chain(1, children=leaves)[0]
        all_ids = sorted([branch['id'], *(item['id'] for item in leaves)])
        self.assertEqual(17, len(all_ids))
        self.assertEqual((all_ids, sorted(set(all_ids) | set(tokens)), []),
            self.fixture.broker._freeze_closure([branch['id']], prerequisite=True))
        wrapper = self.chain(1, children=[branch])[0]
        with self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_closure([wrapper['id']], prerequisite=True)
        with self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_closure([branch['id']])

    def test_exact_transitive_blob_limit_keeps_individual_leaf_ownership_bounded(self):
        leaves, identities = self.blob_leaves(4094)
        branch = self.chain(1, children=leaves)[0]
        artifacts, exposure, blobs = self.fixture.broker._freeze_closure([branch['id']], prerequisite=True)
        self.assertEqual(sorted(identities), blobs)
        self.assertEqual(sorted([branch['id'], *(item['id'] for item in leaves)]), artifacts)
        self.assertEqual(artifacts, exposure)
        additional, _ = self.blob_leaves(1)
        overflow = self.chain(1, children=[*leaves, *additional])[0]
        with self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_closure([overflow['id']], prerequisite=True)
        with self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_closure([branch['id']])
        self.assertTrue(all(len(item['blob_refs']) <= 256 for item in leaves))
        with self.fixture.broker._transaction(), self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_save('independent-closure-envelope/1', {}, [], [],
                                             blobs=identities[:257])

    def test_collection_overflow_precedes_input_source_staging_and_started_event(self):
        nodes = self.chain(4095)
        request = self.fixture.request(campaign_id=nodes[-1]['id'])
        before = self.fixture.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        with patch.object(self.fixture.broker, '_stage_blob_bytes',
                side_effect=AssertionError('Overflow staged an input source')), self.assertRaises(codec.Invalid):
            self.fixture.op('freeze_scientific_batch', **request)
        self.assertEqual([], self.fixture.artifacts('scientific-freeze-input/1'))
        self.assertEqual([], self.fixture.artifacts('scientific-freeze-attempt/1'))
        self.assertEqual(before, self.fixture.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0])
        self.assert_no_commit()

    def test_complete_canonical_graph_over_1mib_is_denied_without_truncating_any_token(self):
        tokens = []
        for index in range(140):
            prefix = 'opaque:long-exposure-' + str(index) + ':'
            tokens.append(prefix + 'x' * (8192 - len(prefix)))
        with self.fixture.broker._transaction():
            leaves = [self.owned('long-token-half-' + str(offset), exposure=tokens[offset:offset + 70])
                      for offset in (0, 70)]
        branch = self.chain(1, children=leaves)[0]
        request = self.fixture.request(campaign_id=branch['id'])
        self.assertGreater(len(wire_bytes(tokens)), 1048576)
        before = self.fixture.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        with self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_closure([branch['id']], prerequisite=True)
        with patch.object(self.fixture.broker, '_stage_blob_bytes',
                side_effect=AssertionError('Oversized complete graph staged source')), self.assertRaises(codec.Invalid):
            self.fixture.op('freeze_scientific_batch', **request)
        self.assertEqual(before, self.fixture.broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0])
        self.assertEqual([], self.fixture.artifacts('scientific-freeze-input/1'))
        self.assertEqual([], self.fixture.artifacts('scientific-freeze-attempt/1'))
        for leaf in leaves:
            self.assertEqual(leaf, self.fixture.op('get_artifact', artifact_id=leaf['id']))

    def test_rejected_conflicting_request_retains_both_full_graphs_and_exposure_tokens(self):
        first, _, first_exposure, _, _, _ = self.large(label='same-key')
        original = self.production_gap(first)
        second_nodes = self.chain(300, exposure=['opaque:rejected-request-history'])
        rejected = {**first, 'selection_record_ref': second_nodes[-1]['id']}
        with self.assertRaises(Conflict):
            self.fixture.op('freeze_scientific_batch', **rejected)
        attempts = self.fixture.artifacts('scientific-freeze-attempt/1')
        self.assertEqual(2, len(attempts))
        failure = attempts[-1]
        self.assertEqual('FAILED', failure['body']['status'])
        self.assertEqual('Conflict', failure['body']['failure_type'])
        self.assertEqual(rejected, failure['body']['rejected_request'])
        expected = set(first_exposure) | {item['id'] for item in second_nodes} | {
            'opaque:rejected-request-history', failure['body']['input_id']}
        self.assertEqual(sorted(expected), failure['exposure'])
        self.assert_versioned(failure)
        self.assertEqual(original, self.fixture.op('get_artifact', artifact_id=original['id']))
        self.assertEqual(1, len(self.fixture.artifacts('scientific-freeze-input/1')))
        self.assert_no_commit()

    def assert_failed_retention_is_complete_operational_history(self, first, rejected, original, label):
        """Overflow retains the exact rejected roots, never a truncated artifact."""
        broker = self.fixture.broker
        before_artifacts = broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]
        before_seq = broker._db.execute('SELECT MAX(seq) FROM events').fetchone()[0]
        before_attempts = deepcopy(self.fixture.artifacts('scientific-freeze-attempt/1'))
        with self.assertRaises(Conflict):
            self.fixture.op('freeze_scientific_batch', **rejected)
        self.assertEqual(before_artifacts, broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0])
        self.assertEqual(before_attempts, self.fixture.artifacts('scientific-freeze-attempt/1'))
        events = [json.loads(row[0]) for row in broker._db.execute(
            'SELECT envelope FROM events WHERE seq>? ORDER BY seq', (before_seq,))]
        self.assertEqual(['bound_computation_started', 'bound_computation_checked'],
                         [item['action'] for item in events])
        started, checked = (item['details'] for item in events)
        capsule = self.fixture.artifacts('scientific-freeze-input/1')[0]
        self.assertEqual(capsule['id'], started['input_ref'])
        self.assertEqual(capsule['id'], started['retained_input_id'])
        self.assertEqual(started['attempt_id'], checked['attempt_id'])
        self.assertEqual('FAILED_RETENTION', checked['status'])
        self.assertEqual('Invalid', checked['failure_type'])
        self.assertIs(checked['artifact_retained'], False)
        self.assertNotIn('artifact_id', checked)
        self.assertEqual(rejected, checked['rejected_request'])
        self.assertEqual(hashlib.sha256(wire_bytes(rejected)).hexdigest(), checked['rejected_request_hash'])
        self.assertEqual(first, capsule['body']['request'])
        self.assertEqual(original, self.fixture.op('get_artifact', artifact_id=original['id']))
        ledger = [item for item in broker._bound_attempts() if item['attempt_id'] == started['attempt_id']]
        self.assertEqual(1, len(ledger))
        self.assertEqual('COMPLETED', ledger[0]['state'])
        self.assertIsNone(ledger[0]['artifact_id'])
        self.assertEqual(0, self.fixture.op('inspect_bound_computations')['pending'])
        self.assertEqual([], self.fixture.op('inspect_scientific_freezes')['incomplete_attempts'])
        self.assert_no_commit()
        # Full owner backup/restore must preserve the event-only failure exactly;
        # the current source cannot synthesize an artifact for this old event.
        event_prefix = [tuple(row) for row in broker._db.execute(
            'SELECT seq,previous_hash,envelope,hash FROM events ORDER BY seq')]
        backup, restored_path = self.root / ('backup-' + label), self.root / ('restored-' + label)
        self.assertEqual('PASS', self.fixture.op('backup_bundle', destination=str(backup))['status'])
        self.assertEqual('PASS', restore_bundle(backup, restored_path,
            broker.directory / 'operator.key')['status'])
        restored = Broker(restored_path)
        try:
            self.assertEqual(event_prefix, [tuple(row) for row in restored._db.execute(
                'SELECT seq,previous_hash,envelope,hash FROM events WHERE seq<=? ORDER BY seq',
                (event_prefix[-1][0],))])
            self.assertEqual(original, restored.call(restored.admin_token, 'get_artifact', artifact_id=original['id']))
            self.assertEqual(capsule, restored.call(restored.admin_token, 'get_artifact', artifact_id=capsule['id']))
            self.assertEqual(before_attempts, restored._freeze_objects('scientific-freeze-attempt/1'))
            self.assertEqual('PASS', restored.call(restored.admin_token, 'verify')['status'])
            self.assertEqual(0, restored.call(restored.admin_token, 'inspect_bound_computations')['pending'])
            self.assertEqual([], restored.call(restored.admin_token, 'inspect_scientific_freezes')['incomplete_attempts'])
        finally:
            restored.close()

    def test_disjoint_exact_4094_exposures_cannot_truncate_conflict_union_or_leave_started_orphan(self):
        #4086 chain nodes+5 ordinary fixture dependencies+3 opaque tokens=4094.
        first, artifacts, exposure, _, _, _ = self.large(count=4086, label='union-collection-limit')
        self.assertEqual(4091, len(artifacts))
        self.assertEqual(4094, len(exposure))
        original = self.production_gap(first)
        other = self.chain(4086, exposure=['opaque:other-union-one', 'opaque:other-union-two'])
        rejected = {**first, 'campaign_id': other[-1]['id']}
        second_exposure = self.fixture.broker._freeze_closure(self.roots(rejected), prerequisite=True)[1]
        self.assertEqual(4094, len(second_exposure))
        self.assertGreater(len(set(exposure) | set(second_exposure)), 4096)
        self.assert_failed_retention_is_complete_operational_history(first, rejected, original, 'collection')

    def test_individually_canonical_requests_cannot_truncate_oversized_conflict_union(self):
        def token_branch(prefix):
            tokens = []
            for index in range(80):
                start = 'opaque:' + prefix + ':' + str(index) + ':'
                tokens.append(start + 'z' * (8192 - len(start)))
            with self.fixture.broker._transaction():
                leaves = [self.owned(prefix + '-half-' + str(offset), exposure=tokens[offset:offset + 40])
                          for offset in (0, 40)]
            return self.chain(1, children=leaves)[0], tokens
        initial, first_tokens = token_branch('canonical-first')
        first = self.fixture.request(key='canonical-union', campaign_id=initial['id'])
        original = self.production_gap(first)
        other, other_tokens = token_branch('canonical-other')
        rejected = {**first, 'campaign_id': other['id']}
        for request in (first, rejected):
            exposure = self.fixture.broker._freeze_closure(self.roots(request), prerequisite=True)[1]
            self.assertLess(len(wire_bytes(exposure)), 1048576)
        self.assertLess(len(first_tokens + other_tokens), 4096)
        self.assertGreater(len(wire_bytes(first_tokens + other_tokens)), 1048576)
        self.assert_failed_retention_is_complete_operational_history(first, rejected, original, 'canonical')

    def test_pending_large_input_cannot_renew_under_a_different_runtime(self):
        request, _, _, _, _, _ = self.large(label='pending-runtime')
        original = self.production_gap(request)
        capsule = self.fixture.artifacts('scientific-freeze-input/1')[0]
        runtime = deepcopy(capsule['body']['runtime_identity'])
        runtime['version'] += ' independent simulated mismatch'
        with patch.object(owner, '_runtime_identity', return_value=runtime), \
                patch.object(self.fixture.broker, '_scientific_freeze_admission',
                             side_effect=AssertionError('Pending input renewed source/runtime authority')):
            with self.assertRaises((codec.Invalid, Conflict)):
                self.fixture.op('freeze_scientific_batch', **request)
        failure = self.fixture.artifacts('scientific-freeze-attempt/1')[-1]
        self.assertEqual('FAILED', failure['body']['status'])
        self.assert_versioned(failure)
        self.assertEqual(capsule, self.fixture.op('get_artifact', artifact_id=capsule['id']))
        self.assertEqual(original, self.fixture.op('get_artifact', artifact_id=original['id']))
        self.assert_no_commit()

    def test_corrupt_retained_large_input_source_is_denied_before_admission(self):
        request, _, _, _, _, _ = self.large(label='corrupt-input-source')
        self.production_gap(request)
        capsule = self.fixture.artifacts('scientific-freeze-input/1')[0]
        descriptor = capsule['body']['source_files']['trading_researcher/scientific_freeze.py']
        path = self.fixture.broker._blob_path(descriptor['sha256'])
        self.assertTrue(path.resolve().is_relative_to(self.fixture.broker.directory.resolve()))
        path.write_bytes(b'Corrupted copied retained input source; workspace source unchanged.\n')
        with patch.object(self.fixture.broker, '_scientific_freeze_admission',
                side_effect=AssertionError('Corrupt retained source reached admission')), self.assertRaises((codec.Invalid, Conflict)):
            self.fixture.op('freeze_scientific_batch', **request)
        failure = self.fixture.artifacts('scientific-freeze-attempt/1')[-1]
        self.assertEqual('FAILED', failure['body']['status'])
        self.assert_versioned(failure)
        self.assertEqual(capsule, self.fixture.op('get_artifact', artifact_id=capsule['id']))
        self.assert_no_commit()

    def test_save_exposure_limit_does_not_expand_direct_reference_or_global_codec_limits(self):
        tokens = ['opaque:retained-' + str(index) for index in range(4096)]
        with self.fixture.broker._transaction():
            saved = self.fixture.broker._freeze_save('independent-closure-envelope/1', {}, [], tokens)
        self.assertEqual(sorted(tokens), saved['exposure'])
        with self.fixture.broker._transaction(), self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_save('independent-closure-envelope/1', {}, [], tokens + ['extra'])
        refs = self.chain(257)
        with self.fixture.broker._transaction(), self.assertRaises(codec.Invalid):
            self.fixture.broker._freeze_save('independent-closure-envelope/1', {},
                [item['id'] for item in refs], [])
        with self.assertRaises(codec.Invalid):
            codec.strings(['independent-' + str(index) for index in range(257)], 'unchanged global bound')

    def test_small_synthetic_commit_and_completed_history_keep_existing_semantics(self):
        manifest = self.fixture.freeze()  # Private transaction judgment only.
        self.assertEqual('frozen-manifest/1', manifest['body']['schema'])
        self.assertEqual(1, len(manifest['body']['trial_ids']))
        self.assertIs(manifest['body']['assessment_access_authority'], False)
        before = deepcopy(self.fixture.artifacts('scientific-freeze-attempt/1'))
        with patch.object(owner, '_runtime_identity', return_value={'not': 'original'}), \
                patch.object(self.fixture.broker, '_scientific_freeze_admission',
                             side_effect=AssertionError('Completed history was renewed')):
            self.assertEqual(manifest, self.fixture.op('freeze_scientific_batch', **self.fixture.request()))
        self.assertEqual(before, self.fixture.artifacts('scientific-freeze-attempt/1'))
        for artifact in [*self.fixture.artifacts('scientific-freeze-input/1'), *before]:
            self.assert_versioned(artifact)

    def test_large_substituted_positive_cannot_use_read_only_cap_to_commit(self):
        request, _, _, _, _, _ = self.large(label='never-large-positive')
        # The original small-root host substitution exposes a >256 transitive
        # graph. Successful _freeze_commit must still use its original limit.
        with self.assertRaises(codec.Invalid):
            self.fixture.freeze(request)
        self.assert_no_commit()
        self.assertEqual(1, len(self.fixture.artifacts('scientific-freeze-input/1')))
        failure = self.fixture.artifacts('scientific-freeze-attempt/1')[-1]
        self.assertEqual('FAILED', failure['body']['status'])
        self.assert_versioned(failure)

    def test_small_commit_still_hashes_original_owned_transitive_blob_bytes(self):
        leaves, identities = self.blob_leaves(1)
        self.fixture.extra = leaves
        self.fixture.broker._blob_path(identities[0]).write_bytes(b'Corrupt owned tiny fixture blob\n')
        with self.assertRaises((codec.Invalid, Conflict)):
            self.fixture.freeze()  # No real admission; old commit integrity gate.
        self.assert_no_commit()
        self.assertEqual('FAILED', self.fixture.artifacts('scientific-freeze-attempt/1')[-1]['body']['status'])

    def test_complete_gapped_backup_restore_preserves_all_bytes_and_original_blob_owners(self):
        request, _, exposure, blobs, nodes, leaves = self.large(blobs=300, label='restored-gap')
        result = self.production_gap(request)
        capsule = self.fixture.artifacts('scientific-freeze-input/1')[0]
        backup, restored_path = self.root / 'backup', self.root / 'restored'
        self.assertEqual('PASS', self.fixture.op('backup_bundle', destination=str(backup))['status'])
        self.assertEqual('PASS', restore_bundle(backup, restored_path,
            self.fixture.broker.directory / 'operator.key')['status'])
        restored = Broker(restored_path)
        try:
            for artifact in [capsule, result, *nodes, *leaves]:
                self.assertEqual(artifact, restored.call(restored.admin_token, 'get_artifact', artifact_id=artifact['id']))
            self.assertEqual((sorted([item['id'] for item in nodes + leaves] + [
                self.fixture.selection['id'], self.fixture.reservation['id'], self.fixture.plans[0]['id'],
                self.fixture.compiled[0]['id'], self.fixture.ancestor['id']]), exposure, blobs),
                restored._freeze_closure(self.roots(request), prerequisite=True))
            self.assertEqual('PASS', restored.call(restored.admin_token, 'verify')['status'])
        finally:
            restored.close()


if __name__ == '__main__':
    unittest.main()
