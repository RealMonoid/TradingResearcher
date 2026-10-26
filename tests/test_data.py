"""Bound data snapshots preserve qualified provenance and protected ancestry."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from trading_researcher.codec import canonical
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.storage import restore_bundle


START = 1577836800  # 2020-01-01T00:00:00Z


def iso(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def row(when=START, instrument='BTCUSDT', value='10', available_at=None):
    return {'time': when, 'instrument': instrument, 'features': {
        'close@1': {'value': value, 'available_at': when if available_at is None else available_at}}}


class DataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now = 1792900000
        self.broker = Broker(self.root / 'runtime', clock=lambda: self.now)
        self.admin = self.broker.admin_token
        self.catalog = self.op('add_source', body={'schema': 'feature-catalog/1',
            'features': {'close@1': {'type': 'real', 'unit': 'USDT'}}}, data_class='development')

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def op(self, operation, **args):
        return self.broker.call(self.admin, operation, **args)

    def source(self, rows=None, raw=None, data_class='development'):
        path = self.root / 'rows.jsonl'
        path.write_bytes(raw if raw is not None else ''.join(canonical(r)+'\n' for r in rows).encode())
        return self.op('add_blob_source', path=str(path), data_class=data_class,
                       description='Synthetic normalized rows; no historical availability proof')

    def manifest(self, sources):
        return {'schema': 'reference-data-request/1', 'profile': 'historical-spot-pilot/1',
            'partition': 'development', 'grid_seconds': 900, 'timestamp_unit': 'seconds',
            'universe': {'start': iso(START), 'end': iso(START+2700), 'instruments': ['BTCUSDT', 'ETHUSDT']},
            'observation_time_definition': 'Synthetic observation instants, not provider release times',
            'provenance': {'provider': 'synthetic', 'revision': 'fixture/1',
                'retrieved_at': iso(self.now), 'source_uris': ['fixture://hand-written'],
                'raw_source_refs': [s['id'] for s in sources], 'checksum_evidence_refs': []},
            'availability': {'basis': 'unknown', 'description': 'Supplied integers are unverified', 'evidence_refs': []},
            'rights': {'basis': 'unknown', 'description': 'Fixture; production rights not established', 'evidence_refs': []},
            'transformation': {'description': 'Hand-written test rows', 'code_refs': []}, 'supersedes': []}

    def register(self, sources, manifest=None, catalog=None):
        return self.op('register_data_snapshot', catalog_id=(catalog or self.catalog)['id'],
            row_source_ids=[s['id'] for s in sources], manifest=manifest or self.manifest(sources))

    def test_snapshot_retains_exact_sources_and_separate_missingness(self):
        first = self.source([row(), row(START+900, value=None),
                             {'time': START+1800, 'instrument': 'BTCUSDT', 'features': {}}])
        snap = self.register([first])
        body = snap['body']
        self.assertEqual(body['status'], 'STRUCTURE_VERIFIED')
        self.assertIs(body['scientific_readiness'], False)
        self.assertEqual(body['coverage'], {'expected_rows': 6, 'observed_rows': 3, 'missing_rows': 3,
            'missing_features': {'close@1': 1}, 'null_values': {'close@1': 1},
            'late_samples': {'close@1': 0}})
        self.assertEqual(body['manifest']['availability']['basis'], 'unknown')
        self.assertIn('AVAILABILITY_UNVERIFIED', body['remaining_gates'])
        self.assertIn(first['id'], snap['exposure'])
        loaded = self.broker._load_reference_data(snap['id'], iso(START), iso(START+2700), ['BTCUSDT'])
        self.assertEqual(len(loaded['rows']), 3)
        self.assertIsNone(loaded['rows'][1]['features']['close@1']['value'])
        self.assertEqual(loaded['rows'][2]['features'], {})
        self.assertEqual(loaded['data_snapshot_ref'], snap['id'])

    def test_cross_shard_duplicate_or_reversed_rows_fail_without_partial_snapshot(self):
        first = self.source([row(START+900)])
        for second_rows in ([row(START+900)], [row()]):
            second = self.source(second_rows)
            before = self.broker._db.execute('SELECT count(*) FROM artifacts').fetchone()[0]
            with self.assertRaises(Invalid):
                self.register([first, second])
            self.assertEqual(self.broker._db.execute('SELECT count(*) FROM artifacts').fetchone()[0], before)

    def test_worker_registration_and_generic_namespace_forgery_are_denied(self):
        token = self.op('register_worker', name='discovery', role='discovery', capabilities=['draft/v1'])['token']
        with self.assertRaises(Denied):
            self.broker.call(token, 'register_data_snapshot', catalog_id='unknown', row_source_ids=[], manifest={})
        with self.assertRaises(Invalid):
            self.op('add_source', body={'schema': 'data-snapshot/1'}, data_class='development')

    def test_arbitrary_source_body_is_rejected_as_a_row_source(self):
        source = self.op('add_source', body=['not a blob descriptor'], data_class='development')
        with self.assertRaises(Denied):
            self.register([source])

    def test_registration_freezes_caller_arguments_before_unlocked_scan(self):
        source = self.source([row()])
        manifest = self.manifest([source])
        original_scan = self.broker._scan_data

        def mutate_caller(inputs, selection=None):
            report = original_scan(inputs, selection)
            manifest['provenance']['revision'] = 'changed-after-validation'
            return report

        with patch.object(self.broker, '_scan_data', side_effect=mutate_caller):
            snap = self.register([source], manifest)
        self.assertEqual(snap['body']['manifest']['provenance']['revision'], 'fixture/1')

    def test_protected_ancestry_cannot_be_laundered_through_a_catalog(self):
        source = self.source([row()])
        for kind in ('assessment', 'operations'):
            with self.subTest(kind=kind):
                protected = self.op('add_source', body={'text': 'protected'}, data_class=kind)
                wrapper = self.op('add_source', body={'text': 'wrapper'}, data_class='development',
                                  exposure=[protected['id']])
                catalog = self.op('add_source', body=self.catalog['body'], data_class='development',
                                  exposure=[wrapper['id']])
                with self.assertRaises(Denied):
                    self.register([source], catalog=catalog)

    def test_availability_assumptions_and_record_time_remain_explicit(self):
        source = self.source([row(available_at=START+900)])
        manifest = self.manifest([source])
        manifest['availability']['basis'] = 'assumed'
        snap = self.register([source], manifest)
        self.assertEqual(snap['body']['coverage']['late_samples']['close@1'], 1)
        self.assertIn('AVAILABILITY_UNVERIFIED', snap['body']['remaining_gates'])
        with self.assertRaises(Denied):
            self.op('create_context', role='discovery', epoch=1, artifact_ids=[snap['id']], research_time=self.now-1)
        derived = self.op('add_source', body={'text': 'wrapper'}, data_class='development', exposure=[snap['id']])
        with self.assertRaises(Denied):
            self.op('create_context', role='discovery', epoch=1, artifact_ids=[derived['id']], research_time=self.now-1)
        self.op('create_context', role='discovery', epoch=1, artifact_ids=[snap['id']])

    def test_assessment_snapshot_is_metadata_protected_and_partition_bound(self):
        assessment_start = 1704067200
        source = self.source([row(assessment_start)], data_class='assessment')
        manifest = self.manifest([source])
        manifest['partition'] = 'assessment'
        manifest['universe'] = {'start': iso(assessment_start), 'end': iso(assessment_start+900),
                                'instruments': ['BTCUSDT']}
        snap = self.register([source], manifest)
        self.assertEqual(snap['data_class'], 'assessment')
        for role in ('discovery', 'formalizer'):
            with self.subTest(role=role), self.assertRaises(Denied):
                self.op('create_context', role=role, epoch=1, artifact_ids=[snap['id']])
        manifest['partition'] = 'development'
        with self.assertRaises(Invalid):
            self.register([source], manifest)

    def test_malformed_rows_and_timestamp_units_do_not_receive_snapshots(self):
        values = []
        for field, value in (('time', True), ('time', START+1), ('time', START*1000),
                             ('instrument', 'UNKNOWN')):
            bad = row()
            bad[field] = value
            values.append((field, canonical(bad).encode()))
        for value in (True, 'NaN', '1e2', 10):
            values.append(('invalid scalar', canonical(row(value=value)).encode()))
        unknown = row()
        unknown['features']['unknown@1'] = unknown['features'].pop('close@1')
        values.extend([('unknown feature', canonical(unknown).encode()), ('blank line', b'\n'),
                       ('duplicate key', b'{"time":1,"time":2}'), ('bad UTF8', b'\xff'),
                       ('oversized line', b' ' * 1048577)])
        for reason, raw in values:
            with self.subTest(reason=reason):
                source = self.source(raw=raw)
                with self.assertRaises(Invalid):
                    self.register([source])
        source = self.source([row()])
        manifest = self.manifest([source])
        manifest['timestamp_unit'] = 'milliseconds'
        with self.assertRaises(Invalid):
            self.register([source], manifest)

    def test_changed_provenance_and_rows_create_distinct_retained_versions(self):
        source = self.source([row()])
        first = self.register([source])
        revision = self.manifest([source])
        revision['provenance']['revision'] = 'fixture/2'
        revision['supersedes'] = [first['id']]
        second = self.register([source], revision)
        self.assertNotEqual(first['id'], second['id'])
        self.assertEqual(self.op('get_artifact', artifact_id=first['id']), first)
        self.assertIn(first['id'], second['exposure'])
        new_source = self.source([row(value='20')])
        third = self.register([new_source])
        self.assertNotEqual(first['id'], third['id'])
        self.assertEqual(self.broker._load_reference_data(first['id'], iso(START), iso(START+900),
                         ['BTCUSDT'])['rows'][0]['features']['close@1']['value'], '10')

    def test_corruption_during_registration_and_before_load_prevents_use(self):
        source = self.source([row()])
        original_scan = self.broker._scan_data
        path = self.broker._blob_path(source['body']['blob']['sha256'])
        original_bytes = path.read_bytes()

        def corrupt_after_scan(inputs, selection=None):
            result = original_scan(inputs, selection)
            path.write_bytes(b'corrupt')
            return result

        before = self.broker._db.execute('SELECT count(*) FROM artifacts').fetchone()[0]
        with patch.object(self.broker, '_scan_data', side_effect=corrupt_after_scan), self.assertRaises(Conflict):
            self.register([source])
        self.assertEqual(self.broker._db.execute('SELECT count(*) FROM artifacts').fetchone()[0], before)
        path.write_bytes(original_bytes)
        snap = self.register([source])
        path.unlink()
        with self.assertRaises(Conflict):
            self.broker._load_reference_data(snap['id'], iso(START), iso(START+900), ['BTCUSDT'])

    def test_loading_bounds_reject_excess_rows_without_silent_crop(self):
        source = self.source([row(), row(START+900)])
        snap = self.register([source])
        with self.assertRaises(Invalid):
            self.broker._load_reference_data(snap['id'], iso(START), iso(START+1800), ['BTCUSDT'], max_rows=1)
        with self.assertRaises(Denied):
            self.broker._load_reference_data(snap['id'], iso(START-900), iso(START+900), ['BTCUSDT'])
        loaded = self.broker._load_reference_data(snap['id'], iso(START+900), iso(START+1800), ['BTCUSDT'])
        self.assertEqual([r['time'] for r in loaded['rows']], [START+900])

    def test_complete_backup_restores_snapshot_and_bound_source_bytes(self):
        snap = self.register([self.source([row(), row(START+900, value='11')])])
        target = self.root / 'backup'
        self.op('backup_bundle', destination=str(target))
        restored = self.root / 'restored'
        restore_bundle(target, restored, self.broker.directory / 'operator.key')
        other = Broker(restored, clock=lambda: self.now)
        try:
            loaded = other._load_reference_data(snap['id'], iso(START), iso(START+1800), ['BTCUSDT'])
            self.assertEqual([r['features']['close@1']['value'] for r in loaded['rows']], ['10', '11'])
            self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=snap['id']), snap)
        finally:
            other.close()

    def test_mutating_a_returned_snapshot_cannot_remove_future_acceptance_gates(self):
        source = self.source([row()])
        first = self.register([source])
        first['body']['remaining_gates'].clear()
        second = self.register([source])
        self.assertIn('AVAILABILITY_UNVERIFIED', second['body']['remaining_gates'])
        retained = self.op('get_artifact', artifact_id=first['id'])
        self.assertIn('AVAILABILITY_UNVERIFIED', retained['body']['remaining_gates'])

    def test_catalog_identity_must_be_a_scalar_reference(self):
        source = self.source([row()])
        for bad in ([], {}, 0, None, True):
            with self.subTest(identity=bad), self.assertRaises(Invalid):
                self.op('register_data_snapshot', catalog_id=bad, row_source_ids=[source['id']],
                        manifest=self.manifest([source]))

    def test_availability_instants_require_representable_utc_seconds(self):
        for value in (START*1000, START*1000000, 10**100, 253402300800, True):
            with self.subTest(value=value):
                source = self.source([row(available_at=value)])
                with self.assertRaises(Invalid):
                    self.register([source])
        source = self.source([row(available_at=1800000000)])
        snap = self.register([source])
        self.assertEqual(snap['body']['coverage']['late_samples']['close@1'], 1)

    def test_real_rpc_registers_metadata_but_exposes_no_row_read_operation(self):
        from trading_researcher.server import Client, LocalServer, RemoteError
        source = self.source([row()])
        server = LocalServer(self.broker, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = Client(server.url, self.admin)
            snap = client.call('register_data_snapshot', catalog_id=self.catalog['id'],
                row_source_ids=[source['id']], manifest=self.manifest([source]))
            self.assertEqual(snap['body']['coverage']['observed_rows'], 1)
            self.assertNotIn('rows', snap['body'])
            with self.assertRaises(RemoteError) as denied:
                client.call('load_reference_data', snapshot_id=snap['id'])
            self.assertEqual(denied.exception.status, 403)
            with self.assertRaises(RemoteError) as invalid:
                client.call('register_data_snapshot', catalog_id=[], row_source_ids=[source['id']],
                            manifest=self.manifest([source]))
            self.assertEqual(invalid.exception.status, 400)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
