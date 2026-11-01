"""Independent historical-reader boundaries; all registries are disposable.

Raw conformance uses the existing genuine normalization/certification fixture.
Synthetic release/record seams below establish protocol behavior only, never
qualification of an actual historical result or relocated spending authority.
"""
from contextlib import closing, contextmanager
from copy import deepcopy
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import Mock, patch

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.feedback import historical, paired, breakout
from trading_researcher.paired_computation import PairedComputation
import test_features as raw_fixtures
from trading_researcher import features
from trading_researcher import review_continuation as legacy_continuation
from trading_researcher import epoch_budget
from trading_researcher.openai_provider import MODEL


REJECT = (Invalid, Conflict, Denied)


class HistoricalViewReview(unittest.TestCase):
    def test_private_reader_preserves_the_inherited_read_clock(self):
        with tempfile.TemporaryDirectory() as root, closing(
                historical.HistoricalFeedbackBroker(Path(root) / 'registry', clock=lambda: 123456)) as broker:
            with broker._historical_view(provisional=[]) as view:
                self.assertEqual(view._now(), 123456)
                self.assertEqual(view._db.execute('PRAGMA query_only').fetchone()[0], 1)

    def test_read_view_denies_public_writes_sql_and_blob_staging(self):
        with tempfile.TemporaryDirectory() as root, closing(historical.HistoricalFeedbackBroker(root)) as broker:
            before = broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]
            with broker._historical_view(provisional=[]) as view:
                self.assertEqual(view._provider_routes, {})
                self.assertNotIn('admin_token', view.__dict__)
                for name in ('call', 'compile_exact', 'execute_exact', 'compile_paired',
                             'publish_paired_feedback', 'publish_breakout_feedback',
                             'qualify_historical_feedback', 'certify_paired'):
                    with self.subTest(name=name), self.assertRaises(Denied):
                        getattr(view, name)
                with self.assertRaises(Denied):
                    view._transaction()
                with self.assertRaises(Denied):
                    view._stage_blob_bytes(b'forbidden')
                with self.assertRaises(sqlite3.OperationalError):
                    view._db.execute('DELETE FROM artifacts')
                with self.assertRaises(REJECT):
                    view._paired_compiled('unbound')
            self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0], before)

    def test_admin_authentication_precedes_release_or_qualification_lookup(self):
        with tempfile.TemporaryDirectory() as root, closing(historical.HistoricalFeedbackBroker(root)) as broker:
            token = broker.call(broker.admin_token, 'register_worker', name='reader',
                                role='discovery', capabilities=[])['token']
            with patch.object(broker, '_historical_bindings', side_effect=AssertionError('Unauthorized lookup')), \
                    patch.object(broker, '_historical_qualification', side_effect=AssertionError('Unauthorized status')):
                for op, args in [('qualify_historical_feedback', {'release_ids': ['unread']}),
                                 ('historical_feedback_status', {'qualification_id': 'unread'})]:
                    with self.subTest(op=op), self.assertRaises(Denied):
                        broker.call(token, op, **args)
            for schema in (historical.SCHEMA, 'historical-feedback-qualification/99'):
                with self.subTest(schema=schema), self.assertRaises(Denied):
                    broker.call(broker.admin_token, 'add_source', body={'schema': schema}, data_class='operations')
                with self.assertRaises(Denied):
                    broker._put_artifact({'role': 'worker'}, {}, {'schema': schema}, [])

    def test_unlisted_compilations_keep_current_only_checks_even_for_a_listed_pair(self):
        binding = {'compiled_id': 'listed', 'formalization_id': 'same-form',
                   'feature_certificate_id': 'same-cert'}
        with tempfile.TemporaryDirectory() as root, closing(historical.HistoricalFeedbackBroker(root)) as broker:
            with broker._historical_view(provisional=[binding]) as view:
                def inherited_compile(reader, identity):
                    return reader._paired_dependencies('same-form', 'same-cert')
                for current in (True, False):
                    with self.subTest(current=current), \
                            patch.object(PairedComputation, '_paired_compiled', autospec=True,
                                         side_effect=inherited_compile) as compile_call:
                        def current_only(reader, formalization_id, certificate_id):
                            if not current:
                                raise Invalid('Original CURRENT raw certificate required')
                            return {'unchanged': 'current-only path'}
                        with patch.object(PairedComputation, '_paired_dependencies', autospec=True,
                                          side_effect=current_only) as dependencies:
                            if current:
                                self.assertEqual(view._paired_compiled('unlisted'), {'unchanged': 'current-only path'})
                            else:
                                with self.assertRaisesRegex(Invalid, 'Original CURRENT'):
                                    view._paired_compiled('unlisted')
                            compile_call.assert_called_once_with(view, 'unlisted')
                            dependencies.assert_called_once_with(view, 'same-form', 'same-cert')

    def test_listed_exception_cannot_leave_permission_for_direct_dependency_calls(self):
        binding = {'compiled_id': 'listed', 'formalization_id': 'same-form',
                   'feature_certificate_id': 'same-cert'}
        with tempfile.TemporaryDirectory() as root, closing(historical.HistoricalFeedbackBroker(root)) as broker:
            with broker._historical_view(provisional=[binding]) as view:
                with patch.object(PairedComputation, '_paired_compiled', side_effect=RuntimeError('Scope exit')):
                    with self.assertRaisesRegex(RuntimeError, 'Scope exit'):
                        view._paired_compiled('listed')
                with patch.object(PairedComputation, '_paired_dependencies',
                                  side_effect=Invalid('Original CURRENT required')) as inherited:
                    with self.assertRaises(REJECT):
                        view._paired_dependencies('same-form', 'same-cert')
                    inherited.assert_called_once_with(view, 'same-form', 'same-cert')


class HistoricalAuthorizationInventoryReview(unittest.TestCase):
    """Cheap read-capability regressions, not a new meaning assessment.

The parent inventory and original-history helper are explicit fixed seams. The
existing legacy binding/row validator and an actual disposable external SQLite
file remain real. Native call-ID reads use a fixed query proxy; no provider,
real grant, scientific result or full raw fixture is created by this class.
"""

    @contextmanager
    def reader(self, *, route_cap=5_000_000_000, ledger_cap=5_000_000_000,
               provider='openai', native_calls=('settled-call',), ledger_calls=('settled-call',),
               bad_binding=False, missing_file=False, no_route=False, revoked=1):
        with tempfile.TemporaryDirectory() as root, closing(
                historical.HistoricalFeedbackBroker(Path(root) / 'registry')) as broker:
            path = Path(root) / 'external-budget.sqlite3'
            epoch = {'id': 'review-epoch', 'request_key': 'fixed-request', 'created_at': 100,
                     'request': {'review_continuation': {'policy': legacy_continuation.POLICY}},
                     'state': 'halted'}
            original = {'target_id': 'fixed-original-target', 'epoch_id': 'original-epoch',
                        'usage': {'fixed': 'retained'}, 'calls_sha256': 'a' * 64}
            with patch.object(legacy_continuation, 'original', return_value=original):
                bound = legacy_continuation.binding(broker, epoch)
                entries = [{'call_id': name, 'job_id': 'independent-review'} for name in ledger_calls]
                if not missing_file:
                    with closing(sqlite3.connect(path)) as db, db:
                        db.execute('CREATE TABLE budget(singleton INTEGER PRIMARY KEY, cap INTEGER NOT NULL)')
                        db.execute('INSERT INTO budget VALUES(1,?)', (ledger_cap,))
                        db.execute('CREATE TABLE research_epoch_budget_grants(approval TEXT PRIMARY KEY, binding TEXT, calls TEXT, revoked INTEGER)')
                        db.execute('INSERT INTO research_epoch_budget_grants VALUES(?,?,?,?)',
                                   (legacy_continuation.APPROVAL,
                                    canonical({**bound, 'request_key': 'wrong'}) if bad_binding else canonical(bound),
                                    canonical(entries), revoked))
                broker._provider_routes = {} if no_route else {MODEL: {
                    'provider': provider, 'budget_file': str(path),
                    'key_file': 'KEY_PATH_MUST_NOT_ENTER_THE_READER',
                    'config': {'test_budget_nano': route_cap, 'secret_extra': 'CONFIG_SECRET_MUST_NOT_ENTER'}}}
                baseline = {'formalization_id': 'target', 'jobs': [
                    {'id': 'independent-review', 'spec': {'research_epoch_id': epoch['id']},
                     'state': 'completed', 'calls': ['unaltered call record'], 'attempts': ['unaltered attempt']}],
                    'policy': {'exact': 'unchanged parent policy'},
                    'other_fields': {'unknowns': [None, False], 'failure': 'must remain verbatim'},
                    'continuation_authorizations': [{'job_id': 'independent-review',
                        'authorization_gap': 'The overlay requires the existing host-selected OpenAI spend ledger'}]}
                expected = deepcopy(baseline)
                expected['continuation_authorizations'] = [{'job_id': 'independent-review',
                                                             'binding': bound, 'calls': entries}]
                refs = {'target', 'old-gap', 'original-source'}
                with broker._historical_view(provisional=[]) as view:
                    connection = view._db
                    class NativeCallList:
                        def execute(self, sql, parameters=()):
                            if 'SELECT id FROM research_calls WHERE epoch_id=' in sql:
                                if tuple(parameters) != (epoch['id'],):
                                    raise AssertionError('Wrong original native epoch inspected')
                                return [(name,) for name in native_calls]
                            return connection.execute(sql, parameters)
                        def close(self):
                            connection.close()
                    view._db = NativeCallList()
                    view._job = Mock(return_value={'spec': {'research_epoch_id': 'original-epoch'}})
                    view._epoch = Mock(return_value=epoch)
                    with patch.object(historical.ExactExecutionBrokerV2, '_meaning_inventory',
                                      return_value=(deepcopy(baseline), set(refs))):
                        yield view, {'id': 'target', 'job_id': 'original-job'}, baseline, expected, refs, path

    def test_readonly_reconstruction_restores_the_entire_original_parent_inventory(self):
        with self.reader() as (view, target, baseline, expected, refs, path):
            before = path.read_bytes()
            inventory, actual_refs = view._meaning_inventory(target)
            self.assertEqual(canonical(inventory), canonical(expected))
            self.assertEqual(actual_refs, refs)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual({k: v for k, v in inventory.items() if k != 'continuation_authorizations'},
                             {k: v for k, v in baseline.items() if k != 'continuation_authorizations'})

    def test_external_reader_is_uri_readonly_query_only_and_never_constructs_a_ledger(self):
        with self.reader() as (view, target, baseline, expected, refs, path):
            connect = sqlite3.connect
            opened = []
            class Watched(sqlite3.Connection):
                def execute(connection, sql, parameters=()):
                    if sql.lstrip().upper().startswith('SELECT'):
                        self.assertEqual(sqlite3.Connection.execute(connection, 'PRAGMA query_only').fetchone()[0], 1)
                    if sql.lstrip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                        raise AssertionError('Historical read attempted external mutation')
                    return sqlite3.Connection.execute(connection, sql, parameters)
            def readonly(database, *args, **kwargs):
                self.assertIn('mode=ro', str(database))
                self.assertIs(kwargs.get('uri'), True)
                opened.append(str(database))
                kwargs['factory'] = Watched
                return connect(database, *args, **kwargs)
            before = path.read_bytes()
            with patch.object(historical.sqlite3, 'connect', side_effect=readonly), \
                    patch.object(epoch_budget, 'SpendLedger', side_effect=AssertionError('Ledger construction')), \
                    patch.object(epoch_budget, '_schema', side_effect=AssertionError('Ledger schema write')):
                inventory, actual_refs = view._meaning_inventory(target)
            self.assertEqual(inventory, expected)
            self.assertEqual(actual_refs, refs)
            self.assertTrue(opened)
            self.assertEqual(path.read_bytes(), before)

    def test_read_capability_copies_no_key_provider_route_or_arbitrary_configuration(self):
        with self.reader() as (view, target, baseline, expected, refs, path):
            self.assertEqual(view._provider_routes, {})
            self.assertNotIn('admin_token', view.__dict__)
            self.assertNotIn('KEY_PATH_MUST_NOT_ENTER_THE_READER', repr(view.__dict__))
            self.assertNotIn('CONFIG_SECRET_MUST_NOT_ENTER', repr(view.__dict__))
            inventory, _ = view._meaning_inventory(target)
            self.assertEqual(inventory, expected)
            with self.assertRaises(Denied):
                view.call

    def test_wrong_route_or_database_cap_retains_the_parent_authorization_gap(self):
        for options in ({'route_cap': 4_999_999_999}, {'route_cap': 5_000_000_000.0},
                        {'ledger_cap': 5_000_000_001}, {'provider': 'other'}, {'no_route': True}):
            with self.subTest(options=options), self.reader(**options) as (view, target, baseline, expected, refs, path):
                inventory, actual_refs = view._meaning_inventory(target)
                entry = inventory['continuation_authorizations'][0]
                self.assertIn('authorization_gap', entry)
                self.assertNotIn('binding', entry)
                self.assertEqual(actual_refs, refs)
                self.assertEqual(inventory['other_fields'], baseline['other_fields'])

    def test_wrong_binding_or_native_call_list_cannot_restore_authorization(self):
        for options in ({'bad_binding': True}, {'native_calls': ()},
                        {'native_calls': ('different-call',)}, {'ledger_calls': ('settled-call', 'extra-call')}):
            with self.subTest(options=options), self.reader(**options) as (view, target, baseline, expected, refs, path):
                inventory, actual_refs = view._meaning_inventory(target)
                self.assertIn('authorization_gap', inventory['continuation_authorizations'][0])
                self.assertNotIn('binding', inventory['continuation_authorizations'][0])
                self.assertEqual(actual_refs, refs)
                self.assertEqual(inventory['policy'], baseline['policy'])

    def test_missing_ledger_is_not_created(self):
        with self.reader(missing_file=True) as (view, target, baseline, expected, refs, path):
            self.assertFalse(path.exists())
            inventory, _ = view._meaning_inventory(target)
            self.assertIn('authorization_gap', inventory['continuation_authorizations'][0])
            self.assertFalse(path.exists())

    def test_revoked_administrative_closure_remains_historically_inspectable(self):
        with self.reader(revoked=1) as (view, target, baseline, expected, refs, path):
            inventory, _ = view._meaning_inventory(target)
            self.assertEqual(inventory, expected)
            with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as db:
                self.assertEqual(db.execute('SELECT revoked FROM research_epoch_budget_grants').fetchone()[0], 1)

    def test_absent_continuation_field_never_opens_the_external_ledger(self):
        with self.reader() as (view, target, baseline, expected, refs, path):
            plain = {k: v for k, v in baseline.items() if k != 'continuation_authorizations'}
            with patch.object(historical.ExactExecutionBrokerV2, '_meaning_inventory', return_value=(plain, refs)), \
                    patch.object(historical.sqlite3, 'connect', side_effect=AssertionError('Unneeded ledger read')):
                inventory, actual_refs = view._meaning_inventory(target)
            self.assertEqual(inventory, plain)
            self.assertEqual(actual_refs, refs)


class HistoricalProtocolReview(unittest.TestCase):
    """Actual raw certificate; synthetic paired metadata is explicitly a seam.

The trusted test-only saves below do not establish paired meaning/composition.
Only paired._evidence is isolated where stated. The native owner, release time,
publisher, technical dependency graph, stored blobs and qualification validator
remain real. No location-bound financial inspector is bypassed.
"""

    @classmethod
    def setUpClass(cls):
        cls.fixture = raw_fixtures.FeatureTests()
        cls.fixture.setUp()
        cls.certificate = cls.fixture.certify()
        if cls.certificate['body']['status'] != 'CERTIFIED':
            raise AssertionError('Genuine fixed raw checks/full normalization replay did not pass')
        directory = cls.fixture.broker.directory
        cls.fixture.broker.close()
        cls.broker = historical.HistoricalFeedbackBroker(directory)
        cls.fixture.fixture.broker = cls.broker
        cls.original_bytes = canonical(cls.broker._artifact(cls.certificate['id']))
        cls.bundle = features.read_bundle()
        cls.original = features.binding(cls.broker, cls.certificate['body']['data_snapshot_id'])
        cb = cls.certificate['body']
        # Reuse the actually certified raw report fields, not a fabricated PASS
        # count. validate_report independently recomputes their expected values.
        cls.report = {key: deepcopy(cb[key]) for key in ('checks', 'replay', 'binding_hash', 'environment', 'footprint')}
        cls.report.update(status='CERTIFIED', reason='FIXED_CASES_AND_FULL_SOURCE_REPLAY_PASSED',
                          definitions=cls.broker._artifact(cb['definitions_id'])['body']['definitions'])
        features.validate_report(cls.report, cls.original, cls.bundle)
        cls.release = cls._release(paired)
        cls.breakout_release = cls._release(breakout)
        cls.qualification = cls._qualification([cls.release['id'], cls.breakout_release['id']])

    @classmethod
    def tearDownClass(cls):
        cls.fixture.tearDown()

    @classmethod
    def _save(cls, body, *, data_class='development', authority='synthetic_protocol_only', refs=(), **changes):
        refs = sorted(set(refs))
        exposure = sorted({*refs, *[x for ref in refs for x in cls.broker._artifact(ref)['exposure']]})
        envelope = dict(version='local-artifact/1', creator='controller', origin='controller',
                        data_class=data_class, authority=authority, source_refs=refs, exposure=exposure, body=body)
        envelope.update(changes)
        with cls.broker._transaction():
            return cls.broker._save_artifact(envelope)

    @classmethod
    def _release(cls, namespace):
        cb = cls.certificate['body']
        cls.release_serial = getattr(cls, 'release_serial', 0) + 1
        formal = cls._save({'synthetic_formalization': namespace.RELEASE,
                           'fixture_occurrence': cls.release_serial})
        compiled = cls._save({'schema': 'paired-compiled-hypothesis/1', 'formalization_id': formal['id'],
            'data_snapshot_id': cb['data_snapshot_id'], 'feature_certificate_id': cls.certificate['id'],
            'reference_certificate_id': cls.certificate['id'], 'source_package_id': cb['source_package_id']})
        execution = cls._save({'schema': 'paired-reference-execution/1', 'compiled_id': compiled['id']})
        composition = cls._save({'schema': 'paired-composition-certificate/1', 'compiled_id': compiled['id']})
        manifest = cls._save({'schema': namespace.MANIFEST, 'scientific_readiness': False,
            'request': {'execution_id': execution['id'], 'composition_id': composition['id'], 'target_epoch': 2},
            'publisher_sha256': (cls.broker._feedback_source_current() if namespace is paired
                                 else cls.broker._breakout_feedback_source_current())}, authority=namespace.AUTHORITY)
        observation = cls._save({'schema': 'research-record/1', 'kind': 'observation',
            'scope': {'manifest_id': manifest['id']}}, authority=namespace.AUTHORITY, refs=[manifest['id']])
        experience = cls._save({'schema': 'research-record/1', 'kind': 'research_experience',
            'scope': {'manifest_id': manifest['id']}}, authority=namespace.AUTHORITY, refs=[manifest['id']])
        return cls._save({'schema': namespace.RELEASE, 'manifest_id': manifest['id'],
            'observation_id': observation['id'], 'experience_id': experience['id'],
            'target_epoch': 2, 'created_at': cls.broker._now(), 'scientific_readiness': False},
            authority=namespace.AUTHORITY, refs=[manifest['id'], observation['id'], experience['id']])

    @classmethod
    def _qualification(cls, releases):
        bindings = cls.broker._historical_bindings(releases)
        adapter = cls.broker._stage_blob_bytes((historical.ROOT / historical.FILE).read_bytes())
        with cls.broker._transaction():
            cls.broker._register_blob(adapter)
        cb = cls.certificate['body']
        return cls._save({'schema': historical.SCHEMA, 'profile': historical.PROFILE,
            'created_at': cls.broker._now(), 'attempt_id': 'synthetic-owned-protocol-record',
            'status': 'CERTIFIED', 'error': None, 'bindings': bindings,
            'feature_certificate_id': cls.certificate['id'], 'installed_package_id': cb['source_package_id'],
            'installed_footprint': features.footprint(cls.bundle), 'host_sources': cls.broker._execution_sources(),
            'adapter_source': adapter, 'report': deepcopy(cls.report), 'scientific_readiness': False},
            data_class='operations', authority=historical.AUTHORITY,
            refs=[cls.certificate['id'], cb['source_package_id'], *releases], blob_refs=[adapter['sha256']])

    def _copy(self, item, *, body=None, **changes):
        envelope = {k: deepcopy(v) for k, v in item.items() if k != 'id'}
        if body is not None:
            envelope['body'] = body
        envelope.update(changes)
        with self.broker._transaction():
            return self.broker._save_artifact(envelope)

    def test_record_validates_without_changing_or_selecting_the_original_certificate(self):
        item = self.broker._historical_qualification(self.qualification['id'])
        self.assertEqual(item['id'], self.qualification['id'])
        self.assertEqual(self.broker._historical_qualification_ids, ())
        self.assertEqual(canonical(self.broker._artifact(self.certificate['id'])), self.original_bytes)
        self.assertEqual(self.broker._feature_certificate_status(None, self.certificate['id'])['status'], 'CURRENT')

    def test_qualification_rejects_envelope_and_identity_tampering(self):
        for field, value in [('creator', 'worker'), ('origin', 'source'), ('data_class', 'development'),
                             ('authority', 'forged'), ('source_refs', []), ('blob_refs', [])]:
            with self.subTest(field=field), self.assertRaises(REJECT):
                self.broker._historical_qualification(self._copy(self.qualification, **{field: value})['id'])
        for field, value in [('schema', 'historical-feedback-qualification/99'), ('profile', 'unknown'),
                             ('scientific_readiness', 0), ('status', 'CERTIFICATION_GAP'), ('error', {})]:
            body = {**self.qualification['body'], field: value}
            with self.subTest(field=field), self.assertRaises(REJECT):
                self.broker._historical_qualification(self._copy(self.qualification, body=body)['id'])

    def test_full_report_replay_checks_and_definition_tampering_are_rejected(self):
        for field, value in [('checks', {**self.report['checks'], 'projection_cases': 9}),
                             ('binding_hash', '0' * 64), ('footprint', {}), ('definitions', []),
                             ('replay', {**self.report['replay'], 'extra': 'changed'}),
                             ('environment', {})]:
            body = deepcopy(self.qualification['body']); body['report'][field] = value
            with self.subTest(field=field), self.assertRaises(REJECT):
                self.broker._historical_qualification(self._copy(self.qualification, body=body)['id'])

    def test_installed_seal_host_sources_and_adapter_bytes_are_independent_bindings(self):
        for field, value in [('installed_footprint', {}), ('host_sources', {}),
                             ('adapter_source', {'sha256': '0' * 64, 'size': 0})]:
            body = {**self.qualification['body'], field: value}
            with self.subTest(field=field), self.assertRaises(REJECT):
                self.broker._historical_qualification(self._copy(self.qualification, body=body)['id'])
        added = {**self.bundle, 'trading_researcher/independent_unused_addition.py': b'# Not executed\n'}
        with patch.object(historical, 'read_bundle', return_value=added), self.assertRaises(REJECT):
            self.broker._historical_qualification(self.qualification['id'])

    def test_addition_only_does_not_promote_stale_status_or_execute_added_source(self):
        bindings = self.broker._historical_bindings([self.release['id']])
        addition = 'trading_researcher/independent_unused_addition.py'
        added = {**self.bundle, addition: b'raise AssertionError("must never execute")\n'}
        with patch.object(historical, 'read_bundle', return_value=added), \
                patch.object(features, 'read_bundle', return_value=added):
            old, retained, installed, original = self.broker._historical_raw(bindings)
            self.assertEqual(retained, self.bundle)
            self.assertNotIn(addition, retained)
            self.assertEqual(installed, added)
            self.assertEqual(original, self.original)
            self.assertEqual(old['id'], self.certificate['id'])
            self.assertEqual(self.broker._feature_certificate_status(None, old['id'])['status'], 'STALE')
            self.assertEqual(canonical(self.broker._artifact(old['id'])), self.original_bytes)

    def test_invalid_raw_states_and_environment_stop_before_the_retained_loader(self):
        bindings = self.broker._historical_bindings([self.release['id']])
        for status in ('QUARANTINED', 'CERTIFICATION_GAP', 'INVALIDATED_BY_DEPENDENCY'):
            with self.subTest(status=status), patch.object(self.broker, '_feature_certificate_status', return_value={'status': status}), \
                    patch.object(self.broker, '_load_feature_package', side_effect=AssertionError('Invalid raw source read')), \
                    self.assertRaises(REJECT):
                self.broker._historical_raw(bindings)
        with patch.object(historical, '_environment_current', return_value=False), self.assertRaises(REJECT):
            self.broker._historical_raw(bindings)

    def test_binding_lists_reject_bad_ids_and_preserve_exact_raw_identity(self):
        for ids in ([], [self.release['id']] * 2, [self.release['id']] * 33, [False], [self.certificate['id']]):
            with self.subTest(ids=ids[:2]), self.assertRaises(REJECT):
                self.broker._historical_bindings(ids)
        bindings = self.broker._historical_bindings([self.release['id'], self.breakout_release['id']])
        self.assertEqual({x['schema'] for x in bindings}, {paired.RELEASE, breakout.RELEASE})
        self.assertEqual([x['release_id'] for x in bindings], sorted([self.release['id'], self.breakout_release['id']]))
        self.assertEqual({x['feature_certificate_id'] for x in bindings}, {self.certificate['id']})

    def test_full_inherited_grant_checks_keep_time_publisher_and_evidence_gaps(self):
        bindings = self.qualification['body']['bindings']
        with self.broker._historical_view(provisional=bindings) as view:
            for ns, grant in ((paired, self.release), (breakout, self.breakout_release)):
                with self.subTest(namespace=ns.RELEASE):
                    with patch.object(ns, '_evidence', side_effect=AssertionError('Early evidence access')):
                        with self.assertRaises(Denied):
                            ns._check_grant(view, grant, 1, grant['body']['created_at'])
                        with self.assertRaises(Denied):
                            ns._check_grant(view, grant, 2, grant['body']['created_at'] - 1)
                    for gap in ('meaning changed', 'rights changed', 'case bytes changed', 'composition changed'):
                        with patch.object(ns, '_evidence', side_effect=Denied(gap)), self.assertRaisesRegex(Denied, gap):
                            ns.check_context(view, {'exposure': [grant['id']], 'epoch': 2,
                                                    'research_time': grant['body']['created_at']})
            with patch.object(paired, 'LOADED_SELF', '0' * 64), \
                    patch.object(paired, '_evidence', side_effect=AssertionError('Publisher drift reached evidence')), \
                    self.assertRaises(REJECT):
                paired._check_grant(view, self.release, 2, self.release['body']['created_at'])

    def test_provisional_view_preserves_current_only_fallback_for_unlisted_pairs(self):
        bindings = self.qualification['body']['bindings']
        with self.broker._historical_view(provisional=bindings) as view:
            with patch.object(PairedComputation, '_paired_compiled', side_effect=Invalid('Original guard')) as original, \
                    self.assertRaisesRegex(Invalid, 'Original guard'):
                view._paired_compiled('different-compilation')
            original.assert_called_once_with(view, 'different-compilation')
            with patch.object(PairedComputation, '_paired_dependencies', return_value={'exact': 'legacy'}) as inherited:
                self.assertEqual(view._paired_dependencies('other-formalization', self.certificate['id']), {'exact': 'legacy'})
                inherited.assert_called_once_with(view, 'other-formalization', self.certificate['id'])

    def test_revoked_qualification_and_release_fail_but_genealogy_is_not_a_typed_edge(self):
        one = self._qualification([self.release['id']])
        self.broker.call(self.broker.admin_token, 'revoke_dependency', key='independent-historical-revoke',
                         dependency_id=one['id'], reason='Synthetic qualification defect',
                         evidence_refs=[self.certificate['id']])
        with self.assertRaises(Denied):
            self.broker._historical_qualification(one['id'])
        other = self._copy(self.qualification, exposure=sorted({*self.qualification['exposure'], one['id']}))
        self.assertEqual(self.broker._dependency_use(other['id'])['status'], 'NOT_REVOKED')
        self.assertEqual(self.broker._historical_qualification(other['id'])['id'], other['id'])
        grant = self._release(paired)
        q = self._qualification([grant['id']])
        self.broker.call(self.broker.admin_token, 'revoke_dependency', key='independent-release-revoke',
                         dependency_id=grant['id'], reason='Synthetic release defect',
                         evidence_refs=[self.certificate['id']])
        with self.assertRaises(Denied):
            self.broker._historical_qualification(q['id'])

    def test_operator_wrapper_keeps_the_original_bundle_and_never_auto_selects(self):
        seen = []
        def validate(bundle, directory, snapshot_id, root):
            self.assertEqual(bundle, self.bundle)
            self.assertEqual(snapshot_id, self.original['snapshot']['id'])
            seen.append((Path(directory).exists(), Path(root).exists()))
            return deepcopy(self.report)
        with patch.object(historical, 'run_validation', side_effect=validate), \
                patch.object(paired, '_evidence', return_value=({}, {})):
            result = self.broker.qualify_historical_feedback(self.broker.admin_token, release_ids=[self.release['id']])
        self.assertEqual(result['body']['status'], 'CERTIFIED')
        self.assertEqual(seen, [(True, True)])
        self.assertEqual(result['body']['report'], self.report)
        self.assertEqual(self.broker._historical_qualification_ids, ())
        self.assertEqual(canonical(self.broker._artifact(self.certificate['id'])), self.original_bytes)
        self.assertEqual(self.broker._historical_qualification(result['id'])['id'], result['id'])

    def test_validator_failure_retains_gap_and_noncanonical_report_is_explicitly_omitted(self):
        isolation_float = deepcopy(self.report)
        isolation_float['environment']['isolation']['isolated'] = 1.0
        # The inherited environment check accepts Python numeric equality here;
        # the new wrapper must still retain a typed gap when canonical rejects it.
        for label, report in [('wrong-checks', {**self.report, 'checks': {'archive_cases': -1}}),
                              ('noncanonical-hash', {**self.report, 'binding_hash': 1.25}),
                              ('noncanonical-isolation', isolation_float)]:
            with self.subTest(label=label):
                with patch.object(historical, 'run_validation', return_value=deepcopy(report)):
                    result = self.broker.qualify_historical_feedback(self.broker.admin_token, release_ids=[self.release['id']])
                self.assertEqual(result['body']['status'], 'CERTIFICATION_GAP')
                self.assertIsNotNone(result['body']['error'])
                self.assertIs(result['body']['scientific_readiness'], False)
                canonical(result)
                if label.startswith('noncanonical'):
                    self.assertIsNone(result['body']['report'])
                    self.assertIn('omitt', canonical(result['body']['error']).lower())


if __name__ == '__main__':
    unittest.main()
