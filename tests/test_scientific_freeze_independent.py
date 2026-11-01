"""Independent atomic-freeze adversaries using only temporary synthetic records.

The successful paths replace the private scientific admission judgment, never a
public capability or provider. They qualify transaction machinery only. The
unmodified production resolver must retain its scientific admission gap.
"""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from trading_researcher.codec import canonical, digest
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher import scientific_freeze as freeze_owner
from trading_researcher.server import Client, LocalServer
from trading_researcher.storage import restore_bundle


FIXED_CASES = Path(__file__).parent / 'fixtures/reference_evaluation_policy_cases.json'
FIXED_CASES_PIN = 'a65153fd2e7d2f647f4ddc2860d957f937c761dfe7f376e9a2289e72f6c92960'
COMMITTED_SCHEMAS = ('scientific-allocation/1', 'frozen-manifest/1', 'scientific-trial/1')


class FreezeFixture:
    """No real plans, certificates, outcome records, market files or models."""

    def __init__(self, directory, count=1):
        self.broker = Broker(directory)
        self.token = self.broker.admin_token
        self.marker = 'synthetic-inherited-exposure-not-unseen-history'
        self.ancestor = self.source('retained failed development attempt')
        self.campaign = self.source('synthetic campaign anchor')
        self.selection = self.source('development-only selection with retained reasons')
        self.reservation = self.source('synthetic fixed primary reservation')
        unselected_id = self.op('add_research', kind='idea',
                                content={'text': 'Independent synthetic unselected idea; no market verdict.'},
                                scope={'fixture': 'independent-scientific-freeze'},
                                source_refs=[self.ancestor['id']])['id']
        self.unselected = self.op('get_artifact', artifact_id=unselected_id)
        self.plans = []
        self.compiled = []
        self.claims = []
        for index in range(count):
            compiled = self.source('compiled synthetic claim', index=index,
                                   exposure=[self.ancestor['id'], self.marker])
            plan = self.source('synthetic predeclared plan', index=index,
                               exposure=[compiled['id']])
            self.compiled.append(compiled)
            self.plans.append(plan)
            self.claims.append({'claim_id': digest({'synthetic_claim': index, 'horizon': 1}),
                                'plan_id': plan['id'], 'compiled_id': compiled['id']})
        self.extra = []

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def source(self, purpose, index=None, exposure=None):
        return self.op('add_source', body={'synthetic_fixture_purpose': purpose, 'index': index},
                       data_class='development', exposure=exposure or [])

    def request(self, key='freeze', **changes):
        return {'key': key, 'campaign_id': self.campaign['id'], 'role': 'primary',
                'plan_ids': [item['id'] for item in self.plans],
                'selection_record_ref': self.selection['id'],
                'reservation_spec_ref': self.reservation['id'], **changes}

    def admission(self, request=None):
        request = request or self.request()
        members = [item for item in self.claims if item['plan_id'] in request['plan_ids']]
        identities = {self.ancestor['id'], request['campaign_id'],
                      request['selection_record_ref'], request['reservation_spec_ref'],
                      self.unselected['id'], *request['plan_ids'],
                      *(item['compiled_id'] for item in members), *(item['id'] for item in self.extra)}
        return {'gaps': [], 'artifact_ids': sorted(identities), 'claims': deepcopy(members),
                'outcome_record_ids': ['synthetic-outcome-0', 'synthetic-outcome-1'],
                'admission': {'scope': 'synthetic private host judgment for atomic tests only',
                              'calibration_proven': False, 'real_assessment_authorized': False}}

    def freeze(self, request=None, admission=None):
        request = self.request() if request is None else request
        evidence = self.admission(request) if admission is None else admission
        with patch.object(self.broker, '_scientific_freeze_admission', return_value=evidence):
            return self.op('freeze_scientific_batch', **request)

    def artifacts(self, schema):
        rows = self.broker._db.execute('SELECT id,envelope FROM artifacts').fetchall()
        return [self.broker._artifact(row['id']) for row in rows
                if json.loads(row['envelope']).get('body', {}).get('schema') == schema]


class ScientificFreezeIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.fixture = FreezeFixture(self.root / 'registry')
        self.addCleanup(self.fixture.broker.close)

    def assert_no_committed_freeze(self, fixture=None):
        fixture = fixture or self.fixture
        for schema in COMMITTED_SCHEMAS:
            self.assertEqual(fixture.artifacts(schema), [], schema)

    def assert_success(self, manifest, count=1):
        self.assertEqual(manifest['body']['schema'], 'frozen-manifest/1')
        self.assertEqual(manifest['body']['primary_count'], count)
        self.assertEqual(len(manifest['body']['trial_ids']), count)
        for flag in ('scientific_readiness', 'frozen', 'allocation_reserved'):
            self.assertIs(manifest['body'][flag], True)
        self.assertIs(manifest['body']['assessment_access_authority'], False)
        self.assertEqual(digest({key: value for key, value in manifest.items() if key != 'id'}),
                         manifest['id'])

    def test_worker_cannot_freeze_or_inspect_before_any_artifact_lookup(self):
        token = self.fixture.op('register_worker', name='researcher', role='discovery',
                                capabilities=[])['token']
        with patch.object(self.fixture.broker, '_artifact', side_effect=AssertionError('Unauthorized read')):
            with self.assertRaises(Denied):
                self.fixture.broker.call(token, 'freeze_scientific_batch', **self.fixture.request())
            with self.assertRaises(Denied):
                self.fixture.broker.call(token, 'inspect_scientific_freezes')
        self.assert_no_committed_freeze()

    def test_generic_sources_cannot_forge_scientific_namespaces(self):
        for schema in (*COMMITTED_SCHEMAS, 'scientific-freeze-attempt/1', 'scientific-freeze-input/1'):
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                self.fixture.op('add_source', body={'schema': schema, 'scientific_readiness': True},
                                data_class='assessment')
        self.assert_no_committed_freeze()

    def test_unmodified_admission_retains_gap_and_never_reads_outcomes(self):
        with patch.object(self.fixture.broker, '_load_reference_data',
                          side_effect=AssertionError('Scientific admission read outcome rows')):
            result = self.fixture.op('freeze_scientific_batch', **self.fixture.request())
        self.assertEqual(result['body']['schema'], 'scientific-freeze-attempt/1')
        self.assertEqual(result['body']['status'], 'ADMISSION_GAP')
        for flag in ('scientific_readiness', 'frozen', 'allocation_reserved'):
            self.assertIs(result['body'][flag], False)
        self.assert_no_committed_freeze()
        report = self.fixture.op('inspect_scientific_freezes')
        self.assertEqual(report['total'], 1)
        self.assertFalse(report['scientific_authority'])
        self.assertEqual(report['attempts'][0], result)

    def test_atomic_success_binds_exact_members_exposure_and_immutable_bytes(self):
        manifest = self.fixture.freeze()
        self.assert_success(manifest)
        self.assertEqual(len(self.fixture.artifacts('scientific-allocation/1')), 1)
        self.assertEqual(len(self.fixture.artifacts('scientific-trial/1')), 1)
        self.assertEqual(self.fixture.op('get_artifact', artifact_id=manifest['id']), manifest)
        for identity in self.fixture.admission()['artifact_ids']:
            self.assertIn(identity, manifest['source_refs'])
        self.assertIn(self.fixture.marker, manifest['exposure'])
        self.assertIn(self.fixture.ancestor['id'], manifest['exposure'])
        self.assertEqual(self.fixture.op('get_artifact', artifact_id=self.fixture.unselected['id']),
                         self.fixture.unselected)
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.broker._db.execute('UPDATE artifacts SET envelope=? WHERE id=?',
                                            (canonical({'tampered': True}), manifest['id']))
        self.assertEqual(self.fixture.op('verify')['status'], 'PASS')

    def test_same_key_retries_original_identity_and_changed_request_conflicts(self):
        request = self.fixture.request()
        manifest = self.fixture.freeze(request)
        with patch.object(self.fixture.broker, '_scientific_freeze_admission',
                          side_effect=AssertionError('Historical identity retried admission')):
            self.assertEqual(self.fixture.op('freeze_scientific_batch', **request), manifest)
        changed = self.fixture.source('a different retained selection record')
        with self.assertRaises(Conflict):
            self.fixture.freeze({**request, 'selection_record_ref': changed['id']})
        self.assertEqual(len(self.fixture.artifacts('scientific-trial/1')), 1)
        attempts = self.fixture.op('inspect_scientific_freezes')['attempts']
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]['body']['status'], 'FAILED')
        self.assertEqual(attempts[0]['body']['failure_type'], 'Conflict')
        self.assertEqual(attempts[0]['body']['rejected_request'],
                         {**request, 'selection_record_ref': changed['id']})

    def test_existing_input_cannot_silently_use_a_replacement_checker_version(self):
        evidence = self.fixture.admission()
        evidence['gaps'] = ['SYNTHETIC_PREREQUISITE_PENDING']
        self.assertEqual(self.fixture.freeze(admission=evidence)['body']['status'], 'ADMISSION_GAP')
        replacement = b'Independent simulated later checker source; no workspace file is modified.\n'
        replacement_hash = hashlib.sha256(replacement).hexdigest()
        replacement_package = {**freeze_owner.LOADED_PACKAGE,
                               'trading_researcher/scientific_freeze.py': replacement_hash}
        original_read = Path.read_bytes
        owner_path = Path(freeze_owner.__file__).resolve()

        def changed_source_read(path):
            return replacement if path.resolve() == owner_path else original_read(path)

        with patch.object(freeze_owner, 'LOADED_SELF', replacement_hash), \
                patch.object(freeze_owner, 'LOADED_PACKAGE', replacement_package), \
                patch.object(Path, 'read_bytes', new=changed_source_read), \
                patch.object(self.fixture.broker, '_scientific_freeze_admission',
                             side_effect=AssertionError('Changed checker reused retained old source')):
            with self.assertRaises((Invalid, Conflict)):
                self.fixture.op('freeze_scientific_batch', **self.fixture.request())
        self.assert_no_committed_freeze()
        attempts = self.fixture.op('inspect_scientific_freezes')['attempts']
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]['body']['status'], 'FAILED')

    def test_current_package_change_is_denied_before_private_admission(self):
        changed = freeze_owner.source_bundle()
        changed['trading_researcher/codec.py'] += b'\n# Simulated source change; never written.\n'
        with patch.object(freeze_owner, 'source_bundle', return_value=changed), \
                patch.object(self.fixture.broker, '_scientific_freeze_admission',
                             side_effect=AssertionError('Changed package reached admission')):
            with self.assertRaises((Invalid, Conflict)):
                self.fixture.op('freeze_scientific_batch', **self.fixture.request())
        self.assert_no_committed_freeze()

    def test_retained_runtime_mismatch_denies_retry_and_retains_original_input(self):
        evidence = self.fixture.admission()
        evidence['gaps'] = ['SYNTHETIC_PREREQUISITE_PENDING']
        self.fixture.freeze(admission=evidence)
        capsule = self.fixture.artifacts('scientific-freeze-input/1')[0]
        replacement = deepcopy(capsule['body']['runtime_identity'])
        replacement['version'] += ' independent simulated different runtime'
        with patch.object(freeze_owner, '_runtime_identity', return_value=replacement), \
                patch.object(self.fixture.broker, '_scientific_freeze_admission',
                             side_effect=AssertionError('Changed runtime reached admission')):
            with self.assertRaises((Invalid, Conflict)):
                self.fixture.op('freeze_scientific_batch', **self.fixture.request())
        self.assertEqual(self.fixture.op('get_artifact', artifact_id=capsule['id']), capsule)
        self.assert_no_committed_freeze()
        attempts = self.fixture.op('inspect_scientific_freezes')['attempts']
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]['body']['status'], 'FAILED')

    def test_malformed_retained_source_closure_denies_before_private_admission(self):
        evidence = self.fixture.admission()
        evidence['gaps'] = ['SYNTHETIC_PREREQUISITE_PENDING']
        self.fixture.freeze(admission=evidence)
        capsule = self.fixture.artifacts('scientific-freeze-input/1')[0]
        missing_file = deepcopy(capsule)
        del missing_file['body']['source_files']['trading_researcher/codec.py']
        missing_blob = deepcopy(capsule)
        missing_blob['blob_refs'] = missing_blob['blob_refs'][:-1]
        wrong_size = deepcopy(capsule)
        wrong_size['body']['source_files']['trading_researcher/codec.py']['size'] += 1
        for index, malformed in enumerate((missing_file, missing_blob, wrong_size)):
            with self.subTest(index=index), \
                    patch.object(self.fixture.broker, '_freeze_existing', return_value=(malformed, None)), \
                    patch.object(self.fixture.broker, '_scientific_freeze_admission',
                                 side_effect=AssertionError('Malformed source closure reached admission')):
                with self.assertRaises((Invalid, Conflict)):
                    self.fixture.op('freeze_scientific_batch', **self.fixture.request())
            self.assert_no_committed_freeze()
            self.assertEqual(self.fixture.op('get_artifact', artifact_id=capsule['id']), capsule)
        attempts = self.fixture.op('inspect_scientific_freezes')['attempts']
        self.assertEqual(len(attempts), 4)
        self.assertEqual([item['body']['status'] for item in attempts[:3]], ['FAILED'] * 3)

    def test_caller_mutation_during_admission_cannot_change_retained_request(self):
        request = self.fixture.request()
        original = deepcopy(request)
        evidence = self.fixture.admission(request)

        def mutate_external_request(actor, admitted_request):
            request['plan_ids'].clear()
            request['campaign_id'] = 'changed-after-call-start'
            self.assertEqual(admitted_request, original)
            return evidence

        with patch.object(self.fixture.broker, '_scientific_freeze_admission',
                          side_effect=mutate_external_request):
            manifest = self.fixture.op('freeze_scientific_batch', **request)
        self.assert_success(manifest)
        self.assertEqual(manifest['body']['request'], original)
        self.assertEqual(self.fixture.op('get_artifact', artifact_id=manifest['id']), manifest)

    def test_new_key_exact_duplicate_links_trial_and_retains_alias_attempt(self):
        manifest = self.fixture.freeze()
        duplicate = self.fixture.freeze(self.fixture.request(key='duplicate-delivery'))
        self.assertEqual(duplicate, manifest)
        self.assertEqual(len(self.fixture.artifacts('scientific-allocation/1')), 1)
        self.assertEqual(len(self.fixture.artifacts('scientific-trial/1')), 1)
        report = self.fixture.op('inspect_scientific_freezes')
        self.assertEqual(report['total'], 2)
        self.assertEqual({item['body']['status'] for item in report['attempts']}, {'COMMITTED', 'REUSED'})

    def test_public_request_has_no_override_or_implicit_member_coercions(self):
        invalid_changes = [
            {'plan_ids': []}, {'plan_ids': [self.fixture.plans[0]['id']] * 2},
            {'plan_ids': True}, {'campaign_id': True}, {'role': 'replicated'},
            {'key': False}, {'scientific_readiness': True}, {'admission': self.fixture.admission()},
        ]
        for changes in invalid_changes:
            with self.subTest(changes=changes), self.assertRaises((Invalid, Denied, Conflict)):
                self.fixture.freeze(self.fixture.request(**changes), self.fixture.admission())
        self.assert_no_committed_freeze()

    def test_host_resolution_requires_matching_unique_claims_and_retained_ids(self):
        malformed = []
        evidence = self.fixture.admission()
        malformed.append({**evidence, 'claims': []})
        malformed.append({**evidence, 'artifact_ids': [*evidence['artifact_ids'], '0' * 64]})
        malformed.append({**evidence, 'claims': [{**evidence['claims'][0], 'plan_id': self.fixture.selection['id']}]})
        malformed.append({**evidence, 'claims': [{**evidence['claims'][0], 'claim_id': 'not-a-sha256'}]})
        malformed.append({**evidence, 'gaps': [True]})
        malformed.append({**evidence, 'admission': True})
        for index, candidate in enumerate(malformed):
            with self.subTest(index=index), self.assertRaises((Invalid, Denied, Conflict)):
                self.fixture.freeze(self.fixture.request(key='malformed-' + str(index)), candidate)
            self.assert_no_committed_freeze()

    def test_predeclared_members_share_one_family_and_late_member_cannot_join(self):
        fixture = FreezeFixture(self.root / 'two-members', count=2)
        self.addCleanup(fixture.broker.close)
        manifest = fixture.freeze()
        self.assert_success(manifest, count=2)
        self.assertEqual(len(fixture.artifacts('scientific-allocation/1')), 1)
        with self.assertRaises(Conflict):
            fixture.freeze(fixture.request(key='changed-membership', plan_ids=[fixture.plans[0]['id']]))
        self.assertEqual(len(fixture.artifacts('scientific-trial/1')), 2)

    def test_duplicate_claim_and_more_than_eight_members_cannot_reserve(self):
        fixture = FreezeFixture(self.root / 'duplicate-claims', count=2)
        self.addCleanup(fixture.broker.close)
        evidence = fixture.admission()
        evidence['claims'][1]['claim_id'] = evidence['claims'][0]['claim_id']
        with self.assertRaises((Invalid, Conflict, Denied)):
            fixture.freeze(admission=evidence)
        self.assert_no_committed_freeze(fixture)
        oversized = FreezeFixture(self.root / 'oversized', count=9)
        self.addCleanup(oversized.broker.close)
        with self.assertRaises((Invalid, Conflict, Denied)):
            oversized.freeze()
        self.assert_no_committed_freeze(oversized)

    def test_concurrent_same_key_converges_and_conflicting_slot_cannot_partially_commit(self):
        barrier = threading.Barrier(4)

        def deliver():
            barrier.wait(timeout=5)
            return self.fixture.op('freeze_scientific_batch', **self.fixture.request())

        with patch.object(self.fixture.broker, '_scientific_freeze_admission',
                          return_value=self.fixture.admission()), ThreadPoolExecutor(max_workers=4) as pool:
            replies = list(pool.map(lambda _: deliver(), range(4)))
        self.assertTrue(all(item == replies[0] for item in replies))
        self.assertEqual(len(self.fixture.artifacts('scientific-allocation/1')), 1)
        self.assertEqual(len(self.fixture.artifacts('scientific-trial/1')), 1)

        other = FreezeFixture(self.root / 'slot-race', count=2)
        self.addCleanup(other.broker.close)
        barrier = threading.Barrier(2)

        def reserve(index):
            request = other.request(key='racer-' + str(index), plan_ids=[other.plans[index]['id']])
            barrier.wait(timeout=5)
            try:
                return other.op('freeze_scientific_batch', **request)
            except Conflict:
                return 'CONFLICT'

        with patch.object(other.broker, '_scientific_freeze_admission',
                          side_effect=lambda actor, request: other.admission(request)), \
                ThreadPoolExecutor(max_workers=2) as pool:
            replies = list(pool.map(reserve, range(2)))
        self.assertEqual(replies.count('CONFLICT'), 1)
        self.assertEqual(len(other.artifacts('frozen-manifest/1')), 1)
        self.assertEqual(len(other.artifacts('scientific-trial/1')), 1)
        self.assertEqual(other.op('verify')['status'], 'PASS')

    def test_failed_final_event_rolls_back_whole_freeze_and_retains_failure(self):
        original = self.fixture.broker._event

        def interrupt(actor, action, **details):
            if action == 'scientific_batch_frozen':
                raise RuntimeError('Independent injected precommit failure')
            return original(actor, action, **details)

        with patch.object(self.fixture.broker, '_event', side_effect=interrupt):
            with self.assertRaises(RuntimeError):
                self.fixture.freeze()
        self.assert_no_committed_freeze()
        attempts = self.fixture.op('inspect_scientific_freezes')['attempts']
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]['body']['status'], 'FAILED')
        self.assertEqual(attempts[0]['body']['failure_type'], 'RuntimeError')
        manifest = self.fixture.freeze()
        self.assert_success(manifest)
        self.assertEqual(self.fixture.op('inspect_scientific_freezes')['total'], 2)

    def test_committed_blob_is_checked_before_any_reservation(self):
        source = self.root / 'synthetic-source.bin'
        source.write_bytes(b'Independent synthetic closure blob; no financial data.\n')
        artifact = self.fixture.op('add_blob_source', path=str(source), data_class='development',
                                   description='Independent synthetic source closure')
        self.fixture.extra.append(artifact)
        self.assertEqual(len(artifact['blob_refs']), 1)
        self.fixture.broker._blob_path(artifact['blob_refs'][0]).write_bytes(b'corrupted retained bytes')
        with self.assertRaises((Invalid, Conflict, Denied)):
            self.fixture.freeze()
        self.assert_no_committed_freeze()

    def test_same_outcomes_cannot_be_reserved_again_in_a_different_allocation(self):
        manifest = self.fixture.freeze()
        campaign = self.fixture.source('different synthetic campaign anchor')
        with self.assertRaises(Conflict):
            self.fixture.freeze(self.fixture.request(key='new-campaign', campaign_id=campaign['id']))
        self.assertEqual(self.fixture.artifacts('frozen-manifest/1'), [manifest])

    def test_unimplemented_corroboration_admission_cannot_use_synthetic_primary_success(self):
        try:
            result = self.fixture.freeze(self.fixture.request(role='corroboration'))
        except (Denied, Invalid):
            result = None
        if result is not None:
            self.assertEqual(result['body']['status'], 'ADMISSION_GAP')
            self.assertFalse(result['body']['frozen'])
            self.assertFalse(result['body']['allocation_reserved'])
        self.assert_no_committed_freeze()

    def test_real_loopback_operator_transport_reaches_atomic_freeze(self):
        server = LocalServer(self.fixture.broker, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = Client(server.url, self.fixture.token)
            with patch.object(self.fixture.broker, '_scientific_freeze_admission',
                              return_value=self.fixture.admission()):
                manifest = client.call('freeze_scientific_batch', **self.fixture.request())
            self.assert_success(manifest)
            self.assertEqual(client.call('get_artifact', artifact_id=manifest['id']), manifest)
            report = client.call('inspect_scientific_freezes')
            self.assertEqual(report['total'], 1)
            self.assertEqual(report['attempts'][0]['body']['status'], 'COMMITTED')
        finally:
            server.shutdown()
            server.server_close()
            thread.join(5)
        self.assertFalse(thread.is_alive())

    def test_host_reported_gap_is_retained_without_partial_scientific_authority(self):
        evidence = self.fixture.admission()
        evidence['gaps'] = ['SYNTHETIC_INFORMATION_TARGET_UNAVAILABLE']
        result = self.fixture.freeze(admission=evidence)
        self.assertEqual(result['body']['status'], 'ADMISSION_GAP')
        self.assertFalse(result['body']['scientific_readiness'])
        self.assertFalse(result['body']['frozen'])
        self.assertFalse(result['body']['allocation_reserved'])
        self.assert_no_committed_freeze()
        self.assertEqual(self.fixture.op('inspect_scientific_freezes')['attempts'], [result])

    def test_backup_restore_preserves_exact_trial_manifest_and_attempt_projection(self):
        manifest = self.fixture.freeze()
        attempts = self.fixture.op('inspect_scientific_freezes')
        backup = self.root / 'backup'
        self.assertEqual(self.fixture.op('backup_bundle', destination=str(backup))['status'], 'PASS')
        restored = self.root / 'restored'
        self.assertEqual(restore_bundle(backup, restored, self.fixture.broker.directory / 'operator.key')['status'], 'PASS')
        other = Broker(restored)
        self.addCleanup(other.close)
        self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=manifest['id']), manifest)
        self.assertEqual(other.call(other.admin_token, 'inspect_scientific_freezes'), attempts)
        self.assertEqual(other.call(other.admin_token, 'verify')['status'], 'PASS')

    def test_fixed_policy_cases_are_preserved_and_state_assertions_are_exercised(self):
        raw = FIXED_CASES.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXED_CASES_PIN)
        cases = {item['name']: item for item in json.loads(raw)['cases']}
        duplicate = cases['allocation_exact_duplicate_links_trial']['expected']
        first = self.fixture.freeze()
        again = self.fixture.freeze(self.fixture.request(key='fixed-exact-duplicate'))
        self.assertEqual(first['body']['trial_ids'] == again['body']['trial_ids'], duplicate['link_existing_trial'])
        self.assertEqual(len(self.fixture.artifacts('scientific-trial/1')) > 1, duplicate['new_independent_trial'])
        retained = cases['allocation_unselected_retained']['expected']
        records = self.fixture.op('inspect_memory', view='journal', kind='idea')['records']
        self.assertEqual(any(item['id'] == self.fixture.unselected['id'] for item in records),
                         retained['retain_in_queue'])
        self.assertEqual(self.fixture.op('get_artifact', artifact_id=self.fixture.unselected['id']),
                         self.fixture.unselected)
        self.assertEqual('scientific_outcome' in self.fixture.unselected['body'], retained['empirical_negative'])
        # The other eight fixed allocation cases are not counted as exercised by
        # this method. Broader result/release behavior remains outside this slice.

    def test_real_process_exit_before_and_after_commit_has_no_partial_trial(self):
        tests_path = str(Path(__file__).resolve().parent)
        for committed in (False, True):
            with self.subTest(committed=committed):
                directory = self.root / ('after-commit' if committed else 'before-commit')
                script = '''import os,sys
from unittest.mock import patch
sys.path.insert(0,sys.argv[2])
from test_scientific_freeze_independent import FreezeFixture
fixture=FreezeFixture(sys.argv[1])
original=fixture.broker._event
def event(actor,action,**details):
    if action=='scientific_batch_frozen' and sys.argv[3]=='before':
        os._exit(29)
    return original(actor,action,**details)
with patch.object(fixture.broker,'_event',side_effect=event):
    fixture.freeze()
os._exit(29)
'''
                process = subprocess.run([sys.executable, '-B', '-c', script, str(directory), tests_path,
                                          'after' if committed else 'before'], capture_output=True, timeout=30)
                self.assertEqual(process.returncode, 29, process.stderr.decode(errors='replace'))
                reopened = Broker(directory)
                try:
                    schemas = {}
                    for row in reopened._db.execute('SELECT envelope FROM artifacts'):
                        schema = json.loads(row[0]).get('body', {}).get('schema')
                        schemas[schema] = schemas.get(schema, 0) + 1
                    for schema in COMMITTED_SCHEMAS:
                        self.assertEqual(schemas.get(schema, 0), int(committed), schema)
                    attempts = [item for item in reopened._bound_attempts() if item['kind'] == 'scientific_freeze']
                    self.assertEqual(len(attempts), 1)
                    self.assertEqual(attempts[0]['state'], 'COMPLETED' if committed else 'INTERRUPTED')
                    report = reopened.call(reopened.admin_token, 'inspect_scientific_freezes')
                    self.assertEqual(report['total'], int(committed))
                    self.assertEqual(len(report['incomplete_attempts']), int(not committed))
                    if not committed:
                        self.assertEqual(report['incomplete_attempts'][0]['state'], 'INTERRUPTED')
                    self.assertEqual(reopened.call(reopened.admin_token, 'verify')['status'], 'PASS')
                finally:
                    reopened.close()


if __name__ == '__main__':
    unittest.main()
