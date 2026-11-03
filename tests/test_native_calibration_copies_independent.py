"""Independent full-copy custody controls, not native/scientific admission.

The retired history/authority is explicitly synthetic financial metadata. Real
Broker, SQL, blob, backup, normal full restore, verification and resource owners
execute. No numerical child, native cache, actual series or protected data runs.
"""
from contextlib import closing
from copy import deepcopy
import hashlib
from pathlib import Path
import re
import sqlite3
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

import test_native_calibration_resource_owner_independent as financial_support
from trading_researcher import native_calibration_runs as owner, native_calibration_resources as resources
from trading_researcher import study_runs
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.evaluation_plans import source_bundle, footprint
from trading_researcher.native_runtime import NativeRuntimes
from trading_researcher.storage import restore_bundle


MIB = 1048576
GIB = 1024 ** 3
ERRORS = (Invalid, Conflict, Denied, OSError)
PAYLOAD = b'Independent complete-blob custody fixture.\x00\n' * 513


def all_sql_rows(db):
    """Independent exact SQL-value comparison; no production fingerprint use."""
    result = {}
    for name, in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        quoted = '"' + name.replace('"', '""') + '"'
        result[name] = sorted([tuple(row) for row in db.execute('SELECT * FROM ' + quoted)], key=repr)
    return result


class NativeCalibrationCopiesIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-copy-base-')
        cls.addClassCleanup(temporary.cleanup)
        root = Path(temporary.name)
        f = financial_support.RetiredFinancialFixture(root)
        try:
            cls.authority = deepcopy(f.authority)
            with patch.object(owner.NativeCalibrationResources, '_read_authority', return_value=deepcopy(cls.authority)):
                manager = owner.NativeCalibrationResources(f.broker)
                cls.pool = manager.prepare(f.token, {'key': 'independent-full-copy-pool'})
            path = root / 'complete-copy-fixture.bin'; path.write_bytes(PAYLOAD)
            cls.extra = f.broker.call(f.token, 'add_blob_source', path=str(path), data_class='operations',
                description='Independent complete copy custody fixture; no empirical evidence.')
            cls.backup = root / 'unbooked-copy-fixture-backup'
            assert f.broker.call(f.token, 'backup_bundle', destination=str(cls.backup))['status'] == 'PASS'
            cls.operator_key = root / 'operator.key'
            cls.operator_key.write_bytes((f.broker.directory / 'operator.key').read_bytes())
        finally:
            f.broker.close()

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='trf-native-copy-')
        self.addCleanup(temporary.cleanup); self.root = Path(temporary.name)
        authority = patch.object(owner.NativeCalibrationResources, '_read_authority',
            side_effect=lambda: deepcopy(self.authority))
        authority.start(); self.addCleanup(authority.stop)
        numerical = patch.object(study_runs, 'execute_attempt', side_effect=AssertionError('Copy invoked numerical work'))
        numerical.start(); self.addCleanup(numerical.stop)
        cache = patch.object(NativeRuntimes, '_materialize', side_effect=AssertionError('Copy invoked native cache'))
        cache.start(); self.addCleanup(cache.stop)
        self.clone_serial = 0; self.clone()
        self.addCleanup(lambda: self.broker.close())

    def clone(self):
        if hasattr(self, 'broker'): self.broker.close()
        self.clone_serial += 1
        self.scenario = self.root / ('scenario-' + str(self.clone_serial))
        self.directory = self.scenario / 'registry'
        self.assertEqual(restore_bundle(self.backup, self.directory, self.operator_key)['status'], 'PASS')
        self.broker = financial_support.Broker(self.directory); self.token = self.broker.admin_token
        self.manager = owner.NativeCalibrationResources(self.broker)
        self.copies = owner.NativeCalibrationCopies(self.broker)

    def view(self): return self.manager.inspect(self.token, self.pool['id'])

    def paths(self, label):
        return {'backup_directory': self.scenario / (label + '-backup'),
                'restore_directory': self.scenario / (label + '-restore'),
                'receipt_path': self.copies.receipt_path(self.pool['id'], label)}

    def bookings(self):
        return {label: self.copies.book(self.token, self.pool['id'], label) for label in ('prepared', 'terminal')}

    def create(self, label='prepared'):
        return self.copies.create(self.token, self.pool['id'], label, **self.paths(label))

    def require(self, label='prepared'):
        return self.copies.require(self.token, self.pool['id'], label, self.paths(label)['receipt_path'])

    def descendant(self):
        return self.broker.call(self.token, 'add_source', data_class='operations',
            body={'copy_fixture_descendant': True})

    def test_two_bookings_charge_once_without_progress_and_remain_distinct_from_copy_proof(self):
        before = self.view()['budget']; booked = self.bookings(); after = self.view()['budget']
        expected_policy = {'schema': 'native-calibration-full-copy-policy/1',
            'metadata_task_ids': {label: self.pool['body']['setup_tasks'][label + '_copies'] for label in ('prepared', 'terminal')},
            'metadata_tariff_bytes': MIB, 'copy_compute': 'outside_attempts_in_wall_forecast'}
        self.assertEqual(self.pool['body']['copy_policy'], expected_policy)
        self.assertEqual(after['charged_storage_bytes'], before['charged_storage_bytes'] + 2 * MIB)
        self.assertEqual(after['charged_compute_ms'], before['charged_compute_ms'] + sum(
            item['body']['settlement']['compute_ms'] for item in booked.values()))
        for key in ('progress_units', 'grants_used', 'no_progress_grants', 'allocated_compute_ms', 'allocated_storage_bytes'):
            self.assertEqual(after[key], before[key])
        for label, artifact in booked.items():
            self.assertEqual(artifact['body']['copy_metadata_booking'], {'schema': 'native-calibration-copy-booking/1',
                'label': label, 'status': 'METADATA_BOOKED', 'external_copy_verified': False,
                'metadata_tariff_bytes': MIB, 'registry_path': str(self.directory),
                'receipt_path': str(self.paths(label)['receipt_path'])})
            self.assertEqual(artifact['body']['resource_state'], 'COMPLETE')
            self.assertEqual(artifact['body']['settlement']['storage_bytes'], MIB)
            self.assertIs(artifact['body']['scientific_readiness'], False)
            self.assertEqual(self.copies.book(self.token, self.pool['id'], label), artifact)
            with self.assertRaises(ERRORS): self.require(label)
        self.assertEqual(self.view()['budget'], after)

    def test_frozen_policy_rejects_wrong_tasks_or_types_and_old_no_policy_keeps_original_progress(self):
        booked = self.bookings()
        for mutate in ('wrong_task', 'extra_label', 'boolean_tariff', 'unknown_schema', 'not_dict'):
            bad = deepcopy(self.pool)
            policy = bad['body']['copy_policy']
            if mutate == 'wrong_task': policy['metadata_task_ids']['prepared'] = self.pool['body']['setup_tasks']['controller_source']
            elif mutate == 'extra_label': policy['metadata_task_ids']['other'] = 'f' * 64
            elif mutate == 'boolean_tariff': policy['metadata_tariff_bytes'] = True
            elif mutate == 'unknown_schema': policy['schema'] += '-unknown'
            else: bad['body']['copy_policy'] = []
            with self.subTest(mutate=mutate), self.assertRaises(Invalid): resources.NativeResourceHistory(bad)
        # Reducer-only historical-model check; no retained DB artifact changes.
        legacy = deepcopy(self.pool); del legacy['body']['copy_policy']
        history = resources.NativeResourceHistory(legacy)
        for row in self.broker._db.execute('SELECT envelope FROM events ORDER BY seq'):
            history.apply(decode(row[0]), self.broker._artifact)
        self.assertEqual(history.budget()['progress_units'], self.pool['body']['carry']['progress_units'] + 2)
        self.assertEqual(self.view()['budget']['progress_units'], self.pool['body']['carry']['progress_units'])

    def test_both_bookings_and_no_pending_work_are_required_before_any_intent_or_copy(self):
        self.copies.book(self.token, self.pool['id'], 'prepared')
        before = self.view()
        with self.assertRaises(ERRORS): self.create()
        self.assertEqual(self.view(), before); self.assertFalse(self.paths('prepared')['receipt_path'].exists())
        self.copies.book(self.token, self.pool['id'], 'terminal')
        task = self.pool['body']['setup_tasks']['controller_source']
        self.manager.reserve(self.token, {'pool_id': self.pool['id'], 'phase': 'setup', 'task_id': task,
            'attempt_id': 'a' * 32, 'expected_checkpoint': self.view()['resource_checkpoint']})
        before = self.view()
        with self.assertRaises(ERRORS): self.create()
        self.assertEqual(self.view(), before)
        self.assertFalse(Path(str(self.paths('prepared')['receipt_path']) + '.intent.json').exists())

    def test_honest_full_copy_preserves_every_sql_row_blob_budget_prefix_and_bounded_external_proof(self):
        booked = self.bookings(); before = self.view(); original_rows = all_sql_rows(self.broker._db)
        original_blob_inventory = {row[0]: row[1] for row in self.broker._db.execute('SELECT sha256,size FROM blobs')}
        row = self.broker._db.execute('SELECT seq,hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        result = self.create(); paths = self.paths('prepared')
        self.assertEqual(result['schema'], 'native-calibration-full-copy-receipt/1')
        self.assertEqual(result['status'], 'COPY_VERIFIED'); self.assertEqual(result['pool_id'], self.pool['id'])
        self.assertEqual(result['source_footprint'], self.pool['body']['source_footprint'])
        self.assertEqual(result['booking_ids'], {label: item['id'] for label, item in booked.items()})
        self.assertEqual(result['event_prefix'], {'seq': row[0], 'hash': row[1]})
        self.assertEqual(result['resource_checkpoint'], before['resource_checkpoint']); self.assertEqual(result['budget'], before['budget'])
        self.assertEqual(result['registry_path'], str(self.directory)); self.assertIs(result['scientific_readiness'], False)
        self.assertIs(type(result['wall_elapsed_ms']), int); self.assertGreater(result['wall_elapsed_ms'], 0)
        for key in ('backup_directory', 'restore_directory'): self.assertEqual(result[key], str(paths[key]))
        self.assertEqual(result['backup_manifest_sha256'], hashlib.sha256((paths['backup_directory'] / 'manifest.json').read_bytes()).hexdigest())
        self.assertEqual(result['restored_database_sha256'], hashlib.sha256((paths['restore_directory'] / 'registry.sqlite3').read_bytes()).hexdigest())
        self.assertEqual(result['blobs'], {'count': len(original_blob_inventory), 'bytes': sum(original_blob_inventory.values()),
            'inventory_sha256': digest(original_blob_inventory)})
        for directory in (paths['backup_directory'], paths['restore_directory']):
            with closing(sqlite3.connect((directory / 'registry.sqlite3').as_uri() + '?mode=ro', uri=True)) as db:
                self.assertEqual(all_sql_rows(db), original_rows)
            for checksum, size in original_blob_inventory.items():
                raw = (directory / 'blobs' / checksum[:2] / checksum).read_bytes()
                self.assertEqual((hashlib.sha256(raw).hexdigest(), len(raw)), (checksum, size))
        self.assertEqual(set(result['sql_fingerprint']['tables']), set(original_rows))
        for name, rows in original_rows.items():
            self.assertEqual(result['sql_fingerprint']['tables'][name]['rows'], len(rows))
            self.assertRegex(result['sql_fingerprint']['tables'][name]['sha256'], '^[0-9a-f]{64}$')
        self.assertEqual(self.require(), result); self.assertEqual(self.view(), before)
        intent = decode(Path(str(paths['receipt_path']) + '.intent.json').read_bytes())
        self.assertLessEqual(len(canonical(booked['prepared']).encode()) + len(canonical(intent).encode())
            + len(canonical(result).encode()) + 16384, MIB)

    def test_copy_io_holds_parent_mutex_but_never_a_primary_sql_transaction(self):
        self.bookings(); actual_backup = self.broker._backup_bundle_external
        actual_restore = owner.restore_bundle; acquired = threading.Event(); workers = []
        def backup(token, args):
            self.assertFalse(self.broker._db.in_transaction)
            def take_mutex():
                with self.broker._mutex: acquired.set()
            worker = threading.Thread(target=take_mutex); workers.append(worker); worker.start()
            self.assertFalse(acquired.wait(0.05))
            return actual_backup(token, args)
        def restore(*args, **kwargs):
            self.assertFalse(self.broker._db.in_transaction)
            return actual_restore(*args, **kwargs)
        try:
            with patch.object(self.broker, '_backup_bundle_external', side_effect=backup), \
                    patch.object(owner, 'restore_bundle', side_effect=restore):
                self.create()
        finally:
            for worker in workers: worker.join(2)
        self.assertTrue(acquired.is_set()); self.assertTrue(all(not worker.is_alive() for worker in workers))

    def test_worker_cannot_lookup_pool_or_read_proofs_for_any_copy_entrypoint(self):
        worker = self.broker.call(self.token, 'register_worker', name='copy-no-authority', role='discovery', capabilities=[])['token']
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Unauthorized pool lookup')):
            with self.assertRaises(Denied): self.copies.book(worker, self.pool['id'], 'prepared')
            with self.assertRaises(Denied): self.copies.create(worker, self.pool['id'], 'prepared', **self.paths('prepared'))
            with self.assertRaises(Denied): self.copies.require(worker, self.pool['id'], 'prepared', self.paths('prepared')['receipt_path'])

    def test_new_disjoint_paths_fixed_receipt_and_no_overwrite_are_preconditions(self):
        self.bookings(); before = self.view(); paths = self.paths('prepared')
        for altered in ({**paths, 'backup_directory': self.directory / 'inside'},
                        {**paths, 'restore_directory': paths['backup_directory'] / 'nested'},
                        {**paths, 'receipt_path': self.scenario / 'caller-selected.json'}):
            with self.subTest(paths=altered), self.assertRaises(ERRORS):
                self.copies.create(self.token, self.pool['id'], 'prepared', **altered)
        self.assertEqual(self.view(), before)
        result = self.create(); receipt_raw = paths['receipt_path'].read_bytes()
        with self.assertRaises(ERRORS): self.create()
        self.assertEqual(paths['receipt_path'].read_bytes(), receipt_raw); self.assertEqual(self.require(), result)

    def test_corrupt_backup_after_actual_backup_retains_intent_and_failure_then_forbids_retry(self):
        self.bookings(); before = self.view()['budget']; actual = self.broker._backup_bundle_external
        def corrupt(token, args):
            report = actual(token, args)
            (Path(args['destination']) / 'manifest.json').write_bytes(b'Corrupt complete-copy manifest.')
            return report
        with patch.object(self.broker, '_backup_bundle_external', side_effect=corrupt):
            with self.assertRaises(ERRORS): self.create()
        paths = self.paths('prepared'); self.assertTrue(paths['backup_directory'].exists())
        self.assertTrue(Path(str(paths['receipt_path']) + '.intent.json').exists())
        self.assertTrue(Path(str(paths['receipt_path']) + '.failure.json').exists())
        self.assertFalse(paths['receipt_path'].exists()); self.assertIs(self.view()['budget']['halted'], True)
        self.assertEqual(self.view()['budget']['charged_storage_bytes'], before['charged_storage_bytes'])
        with self.assertRaises(ERRORS): self.create()

    def test_corrupt_restored_blob_before_verification_is_retained_and_stops_pool(self):
        self.bookings(); actual = owner.restore_bundle
        def corrupt(*args, **kwargs):
            result = actual(*args, **kwargs); target = Path(args[1]); checksum = self.extra['body']['blob']['sha256']
            (target / 'blobs' / checksum[:2] / checksum).write_bytes(b'Corrupt restored bytes, owned fixture only.')
            return result
        with patch.object(owner, 'restore_bundle', side_effect=corrupt):
            with self.assertRaises(ERRORS): self.create()
        self.assertTrue(self.paths('prepared')['restore_directory'].exists())
        self.assertTrue(Path(str(self.paths('prepared')['receipt_path']) + '.failure.json').exists())
        self.assertIs(self.view()['budget']['halted'], True)

    def test_prepared_descendant_is_accepted_but_terminal_requires_exact_current_tip(self):
        self.bookings(); prepared = self.create(); self.descendant()
        self.assertEqual(self.require(), prepared)
        terminal = self.create('terminal'); self.assertEqual(self.require('terminal'), terminal)
        self.descendant()
        with self.assertRaises(ERRORS): self.require('terminal')

    def test_terminal_copy_closes_out_halted_pool_without_changing_its_failure_or_authority(self):
        self.bookings(); self.manager.stop(self.token, self.pool['id'], 'Explicit owned synthetic failure stop')
        before = self.view(); result = self.create('terminal')
        self.assertEqual(self.require('terminal'), result); self.assertEqual(self.view(), before)
        self.assertIs(result['budget']['halted'], True); self.assertIs(result['scientific_readiness'], False)
        with self.assertRaises(ERRORS): self.create('prepared')

    def test_earlier_intact_pair_cannot_be_resealed_as_a_later_terminal_prefix(self):
        self.bookings(); prepared = self.create(); self.descendant(); terminal = self.create('terminal')
        self.assertNotEqual(prepared['event_prefix'], terminal['event_prefix'])
        forged = deepcopy(terminal)
        for key in ('backup_directory', 'restore_directory', 'backup_manifest_sha256',
                    'restored_database_sha256', 'sql_fingerprint', 'blobs'):
            forged[key] = deepcopy(prepared[key])
        paths = self.paths('terminal'); paths['receipt_path'].write_text(canonical(forged), encoding='utf-8')
        intent_path = Path(str(paths['receipt_path']) + '.intent.json'); intent = decode(intent_path.read_bytes())
        for key in ('backup_directory', 'restore_directory'): intent[key] = forged[key]
        intent_path.write_text(canonical(intent), encoding='utf-8')
        with self.assertRaises(ERRORS): self.require('terminal')

    def test_changed_sql_value_with_refreshed_database_hash_still_fails_complete_sql_custody(self):
        self.bookings(); result = self.create(); paths = self.paths('prepared')
        database = paths['restore_directory'] / 'registry.sqlite3'
        with closing(sqlite3.connect(database)) as db:
            db.execute("UPDATE principals SET capabilities=? WHERE name='operator'", ('["copy-drift"]',)); db.commit()
        # Adversary refreshes the obvious byte hash only; immutable backup SQL
        # and full-row fingerprint must independently reject the changed value.
        result['restored_database_sha256'] = hashlib.sha256(database.read_bytes()).hexdigest()
        paths['receipt_path'].write_text(canonical(result), encoding='utf-8')
        with self.assertRaises(ERRORS): self.require()

    def test_current_source_or_revoked_pool_denies_use_of_an_honest_preserved_pair(self):
        for fault in ('source', 'revocation'):
            self.clone(); self.bookings(); self.create(); before = self.view()
            if fault == 'source':
                changed = source_bundle(); changed['trading_researcher/native_calibration_runs.py'] += b'\n# Explicit metadata-read source drift seam.\n'
                with patch.object(owner, 'source_bundle', return_value=changed):
                    with self.assertRaises(ERRORS): self.require()
            else:
                evidence = self.broker.call(self.token, 'add_source', data_class='development', body={'copy_defect': True})
                self.broker.call(self.token, 'revoke_dependency', key='copy-source-defect', dependency_id=self.pool['id'],
                    reason='Synthetic current copy-source defect.', evidence_refs=[evidence['id']])
                with self.assertRaises(Denied): self.require()
            self.assertEqual(self.view()['budget']['charged_storage_bytes'], before['budget']['charged_storage_bytes'])

    def test_missing_or_tampered_external_receipt_never_replaces_actual_copy_verification(self):
        for fault in ('missing', 'budget', 'booking'):
            self.clone(); booked = self.bookings(); result = self.create(); path = self.paths('prepared')['receipt_path']
            if fault == 'missing':
                preserved = path.with_suffix('.preserved.json')
                self.assertTrue(path.resolve().is_relative_to(self.root.resolve()))
                path.rename(preserved)
                with self.assertRaises(ERRORS): self.require()
                self.assertTrue(preserved.exists())
            else:
                changed = deepcopy(result)
                if fault == 'budget': changed['budget']['charged_storage_bytes'] -= 1
                else: changed['booking_ids']['prepared'] = booked['terminal']['id']
                path.write_text(canonical(changed), encoding='utf-8')
                with self.assertRaises(ERRORS): self.require()

    def test_capacity_equality_and_one_byte_short_are_checked_before_intent(self):
        for shortage in (1, 0):
            self.clone(); self.bookings(); before = self.view()
            committed = self.broker._db.execute('SELECT COALESCE(SUM(size),0) FROM blobs').fetchone()[0]
            committed += (self.directory / 'registry.sqlite3').stat().st_size
            threshold = 20 * GIB + 2 * committed + 2 * MIB
            # Physical observation only, never a readiness/verdict substitute.
            with patch.object(owner.shutil, 'disk_usage', return_value=types.SimpleNamespace(free=threshold - shortage)):
                if shortage:
                    with self.assertRaises(ERRORS): self.create()
                    self.assertFalse(Path(str(self.paths('prepared')['receipt_path']) + '.intent.json').exists())
                else: self.assertEqual(self.create()['status'], 'COPY_VERIFIED')
            self.assertEqual(self.view(), before)


if __name__ == '__main__':
    unittest.main()
