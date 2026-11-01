"""Independent native AST4 gates on genuinely certified synthetic inputs.

The one fixture uses real normalization, retained source/blob certification,
finite reservations, four controller/ledger calls and substantive review
records. HTTP replies/counts are fixed synthetic doubles, not LLM evidence or
actual token-fit evidence. No feature metadata or passing certificate is
seeded. Each adversary restores ONLY the same disposable registry's SQLite
snapshot; its path/epoch are never rebound and the separate settled ledger is
never restored or reused for another call. Controlled owned-record copies and
job-result substitution test corruption boundaries, not public forgery.
"""
from copy import deepcopy
from contextlib import contextmanager
from fractions import Fraction
import sqlite3
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from exact_execution_support import ExactExecutionFixture, ORIGINAL, AS_OF
from trading_researcher import exact_composition as composition, exact_runtime as runtime
import trading_researcher.exact_execution as execution
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.errors import Conflict, Denied
from trading_researcher.exact_formalization import assess_candidate
from trading_researcher.meaning_reviews import PROMPT, PROTOCOL
from trading_researcher.inquiry import resources


REJECTIONS = (Invalid, Denied, Conflict)


class ExactExecutionReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = ExactExecutionFixture()
        cls.addClassCleanup(cls.f.close)
        cls.compiled = cls.f.compile()
        if cls.compiled['body']['status'] != 'COMPILED':
            raise AssertionError(('genuine compile', cls.compiled['body']['error']))
        cls.certificate = cls.f.composition(cls.compiled['id'])
        if cls.certificate['body']['status'] != 'CONFORMANT':
            raise AssertionError(('genuine composition', cls.certificate['body']['error']))
        cls.executed = cls.f.execute(cls.compiled['id'], cls.certificate['id'])
        if cls.executed['body']['status'] != 'DESCRIPTIVE_EXECUTION':
            raise AssertionError(('genuine execution', cls.executed['body']['error']))
        cls.clean = sqlite3.connect(':memory:')
        cls.addClassCleanup(cls.clean.close)
        cls.f.broker._db.backup(cls.clean)
        cls.selected = cls.f.broker._exact_certificate_id
        cls.ledger_before = cls.ledger_dump()

    @classmethod
    def ledger_dump(cls):
        with cls.f.ledger._connect() as database:
            return '\n'.join(database.iterdump())

    def setUp(self):
        self.broker = self.f.broker
        self.clean.backup(self.broker._db)
        self.broker._exact_certificate_id = self.selected

    def tearDown(self):
        # No model/count/dispatch occurs in a test body. Restoring this registry
        # cannot restore any shared-ledger grant, reservation or spent amount.
        self.assertEqual(self.ledger_dump(), self.ledger_before)
        self.clean.backup(self.broker._db)
        self.broker._exact_certificate_id = self.selected

    def injected(self, original, mutate):
        envelope = deepcopy(original)
        envelope.pop('id')
        mutate(envelope)
        with self.broker._transaction():
            return self.broker._save_artifact(envelope)

    def no_outcome_access(self, action):
        with patch.object(self.broker, '_load_reference_data', side_effect=AssertionError('outcome access')) as loader, \
                patch.object(runtime, 'run_child', side_effect=AssertionError('child dispatch')) as child, \
                self.assertRaises(REJECTIONS):
            action()
        loader.assert_not_called()
        child.assert_not_called()

    def checked_composition(self, certificate):
        compiled, _, payload = self.broker._exact_compiled(self.compiled['id'])
        return self.broker._require_exact_composition(certificate['id'], compiled, payload)

    def review_call(self):
        inventory, _ = self.broker._meaning_inventory(self.f.formalization)
        self.assertEqual(len(inventory['jobs']), 1)
        job = inventory['jobs'][0]
        self.assertEqual(len(job['calls']), 1)
        return deepcopy(job), deepcopy(job['calls'][0])

    def rebound_invocation_input(self, call, mutate):
        original = self.broker._artifact(call['invocation']['input_id'])
        incoming = self.injected(original, mutate)
        outgoing = self.broker._artifact(call['invocation']['result_id'])
        def bind_new_input(item):
            item['body']['input_id'] = incoming['id']
            item['source_refs'] = sorted(incoming['id'] if ref == original['id'] else ref
                                         for ref in item['source_refs'])
            item['exposure'] = sorted(set(item['exposure']) | {incoming['id']})
        result = self.injected(outgoing, bind_new_input)
        changed = deepcopy(call)
        changed['invocation'] = {'input_id': incoming['id'], 'result_id': result['id']}
        return changed

    def revoke(self, identity, key):
        evidence = self.f.op('add_source', body={'controlled_exact_defect': key}, data_class='operations')
        return self.f.op('revoke_dependency', key=key, dependency_id=identity,
                         reason='Synthetic technical-boundary adversary; no scientific conclusion.',
                         evidence_refs=[evidence['id']])

    def test_genuine_four_stage_route_and_literal_case_expectations(self):
        f = self.f
        self.assertEqual(f.formalization['body']['schema'], 'formalization-record/3')
        self.assertEqual(f.formalization['body']['original_idea']['content']['text'], ORIGINAL)
        self.assertEqual(f.formalization['creator'], 'formal')
        self.assertEqual(f.review_record['creator'], 'review')
        self.assertEqual((f.review_spec['research_call_profile']['prompt_version'],
                          f.review_spec['research_call_profile']['prompt']), (PROTOCOL, PROMPT))
        self.assertEqual(f.meaning_status['independent_semantic_review'], 'SATISFIED')
        self.assertTrue(f.meaning_status['current'])
        calls = self.broker._db.execute('SELECT state,receipt FROM research_calls').fetchall()
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(row['state'] == 'recorded' for row in calls))
        for row in calls:
            receipt = decode(row['receipt'])
            self.assertIs(receipt['resource_settlement_verified'], True)
            self.assertIsNone(receipt['resource_gap'])
        self.assertEqual(f.runtime['body']['result']['result']['tests'], 51)
        self.assertEqual(self.broker._feature_certificate_status(None, f.feature['id'],
                            data_snapshot_id=f.snapshot['id'])['status'], 'CURRENT')
        capsule = self.broker._artifact(self.compiled['body']['input_id'])['body']
        self.assertEqual(capsule['data_use']['status'], 'QUALIFIED')
        self.assertIs(capsule['data_use']['independent_confirmation'], False)
        self.assertEqual(capsule['data_use']['availability']['basis'], 'assumed')
        self.assertEqual(capsule['data_use']['availability']['delay_seconds'], 900)
        result = self.executed['body']['result']
        raw = self.broker._read_blob_bytes(result['case_blob']['sha256'])
        cases = [decode(line) for line in raw.splitlines()]
        # Literal expectations follow the original/three input bars, not the
        # installed evaluator's reclassification of its own output.
        self.assertEqual([case['status'] for case in cases],
                         ['SCOPE_UNKNOWN', 'ELIGIBLE', 'PARTITION_BOUNDARY'])
        self.assertEqual(len(cases), 3)
        self.assertTrue(all(case['diagnostics'] is not None for case in cases))
        observed = cases[1]['outcome']
        low = Fraction(int(observed['lower']['numerator']), int(observed['lower']['denominator']))
        high = Fraction(int(observed['upper']['numerator']), int(observed['upper']['denominator']))
        # ln(102/101)*10000 is strictly between 98 and 99 basis points.
        self.assertLess(Fraction(98), low)
        self.assertLess(high, Fraction(99))
        self.assertEqual(self.executed['body']['verification']['result']['result_hash'], digest(result))
        self.assertTrue(self.executed['body']['complete_required_report'])
        self.assertIs(self.executed['body']['scientific_readiness'], False)
        self.assertEqual(self.f.op('verify')['status'], 'PASS')

    def test_operator_authentication_precedes_identity_lookup_for_all_operations(self):
        actions = [
            lambda token: self.broker.compile_exact(token, formalization_id='unknown',
                feature_certificate_id='unknown', as_of=AS_OF),
            lambda token: self.broker.certify_exact_composition(token, compiled_id='unknown'),
            lambda token: self.broker.execute_exact(token, compiled_id='unknown',
                meaning_assessment_id='unknown', composition_id='unknown'),
        ]
        for token in ('not-a-capability', self.f.finite.clients['review'].token):
            for index, action in enumerate(actions):
                with self.subTest(operation=index), patch.object(self.broker, '_artifact',
                        side_effect=AssertionError('unauthorized identity following')) as artifact, self.assertRaises(Denied):
                    action(token)
                artifact.assert_not_called()

    def test_reserved_new_namespaces_cannot_be_registered_as_sources(self):
        for schema in ('exact-compilation-input/1', 'exact-compiled-hypothesis/1',
                       'exact-composition-source-package/1', 'exact-composition-certificate/1',
                       'exact-execution-input/1', 'exact-reference-execution/1'):
            with self.subTest(schema=schema), self.assertRaises(Denied):
                self.f.op('add_source', body={'schema': schema}, data_class='development')

    def test_each_complete_finite_receipt_field_and_json_type_is_binding(self):
        job, call = self.review_call()
        self.broker._historical_meaning_call(self.f.formalization, job, call)
        base = decode(call['receipt'])
        mutations = [
            lambda value: value.update(installed_sources_unchanged=False),
            lambda value: value.update(resource_settlement_verified=False),
            lambda value: value.update(resource_settlement_verified=1),
            lambda value: value.update(resource_gap='controlled unresolved shared accounting'),
            lambda value: value.update(late=True),
            lambda value: value.update(within_reservation=1),
            lambda value: value.update(accounting_valid=False),
            lambda value: value.update(usage_unknown=True),
            lambda value: value.pop('installed_sources_unchanged'),
            lambda value: value.update(unexpected='not in the finite protocol'),
        ]
        for index, mutate in enumerate(mutations):
            changed = deepcopy(call)
            receipt = deepcopy(base)
            mutate(receipt)
            changed['receipt'] = canonical(receipt)
            with self.subTest(mutation=index), self.assertRaises(REJECTIONS):
                self.broker._historical_meaning_call(self.f.formalization, job, changed)

    def test_receipt_does_not_override_full_owned_invocation_and_role_binding(self):
        job, call = self.review_call()
        original = self.broker._artifact(call['invocation']['result_id'])
        changes = [
            lambda item: item['body']['receipt'].update(resource_settlement_verified=False),
            lambda item: item['body'].update(execution_path='controller-direct-adapter/1'),
            lambda item: item['body'].update(response_usable=False),
            lambda item: item['body'].update(installed_sources_unchanged=False),
            lambda item: item['body'].update(response_id='0' * 64),
        ]
        for index, change in enumerate(changes):
            injected = self.injected(original, change)
            changed = deepcopy(call)
            changed['invocation']['result_id'] = injected['id']
            with self.subTest(mutation=index), self.assertRaises(REJECTIONS):
                self.broker._historical_meaning_call(self.f.formalization, job, changed)
        changed = deepcopy(call)
        changed['owner'] = self.f.formalization['creator']
        with self.assertRaises(REJECTIONS):
            self.broker._historical_meaning_call(self.f.formalization, job, changed)

    def test_changed_native_receipt_stales_assessment_and_fences_outcome_access(self):
        _, call = self.review_call()
        receipt = decode(call['receipt'])
        receipt['resource_settlement_verified'] = False
        self.broker._db.execute('UPDATE research_calls SET receipt=? WHERE id=?',
                                (canonical(receipt), call['id']))
        status = self.f.op('inspect_meaning_review', assessment_id=self.f.meaning['id'])
        self.assertFalse(status['current'])
        self.assertEqual(status['independent_semantic_review'], 'NOT_SATISFIED')
        self.no_outcome_access(lambda: self.f.execute(self.compiled['id'], self.certificate['id']))

    def test_counted_configuration_and_retained_full_wire_observation_are_binding(self):
        job, call = self.review_call()
        mutations = [
            lambda item: item['body']['configuration'].update(unexpected_configuration=True),
            lambda item: item['body'].update(adapter_run_id='different-unconsumed-controller-run'),
            lambda item: item['body'].update(adapter_ordinal=False),
            lambda item: item['body'].update(input_count_receipts=[]),
        ]
        for index, mutate in enumerate(mutations):
            changed = self.rebound_invocation_input(call, mutate)
            with self.subTest(mutation=index), self.assertRaises(REJECTIONS):
                self.broker._historical_meaning_call(self.f.formalization, job, changed)

        original = self.broker._artifact(call['invocation']['input_id'])
        observed = self.broker._artifact(original['body']['input_count_observation_id'])
        valid_receipt = deepcopy(original['body']['input_count_receipts'])
        alternatives = [[{}], deepcopy(valid_receipt), deepcopy(valid_receipt)]
        alternatives[1][0]['wire_request_sha256'] = '0' * 64
        alternatives[2][0]['input_token_bound'] += 1
        for index, receipts in enumerate(alternatives):
            copied = self.injected(observed, lambda item: item['body'].update(count_receipts=receipts))
            def replace_observation(item):
                item['body']['input_count_receipts'] = receipts
                item['body']['input_count_observation_id'] = copied['id']
                item['source_refs'] = sorted(copied['id'] if ref == observed['id'] else ref
                                             for ref in item['source_refs'])
                item['exposure'] = sorted(set(item['exposure']) | {copied['id']})
            changed = self.rebound_invocation_input(call, replace_observation)
            # Mutual agreement of two controlled owned copies does not bind
            # their count details to the authentic full wire/native slot.
            with self.subTest(observation=index), self.assertRaises(REJECTIONS):
                self.broker._historical_meaning_call(self.f.formalization, job, changed)

    def test_unavailable_or_forged_ledger_read_cannot_supply_historical_review(self):
        job, call = self.review_call()
        real_ledger = self.f.ledger
        # Inject only the read result at the trusted ledger boundary. Its real
        # temporary file is never written/restored; authenticate() still runs.
        for variant in ('missing', 'unknown', 'wrong_usage', 'wrong_ordinal'):
            @contextmanager
            def connection():
                with real_ledger._connect() as database:
                    class ReadFault:
                        def execute(self, sql, args=()):
                            cursor = database.execute(sql, args)
                            if 'FROM dispatches d LEFT JOIN token_metadata' not in sql:
                                return cursor
                            row = cursor.fetchone()
                            if variant == 'missing':
                                changed = None
                            else:
                                changed = list(row)
                                if variant == 'unknown':
                                    changed[3] = 'uncertain'
                                elif variant == 'wrong_usage':
                                    changed[5] = canonical({'controlled': 'not the retained response receipt'})
                                else:
                                    metadata = decode(changed[4])
                                    metadata['ordinal'] = 1
                                    changed[4] = canonical(metadata)
                            return SimpleNamespace(fetchone=lambda: changed)
                    yield ReadFault()
            reader = SimpleNamespace(_connect=connection)
            with self.subTest(ledger_fault=variant), patch.object(resources, '_ledger', return_value=reader):
                with self.assertRaises(REJECTIONS):
                    self.broker._historical_meaning_call(self.f.formalization, job, call)
                status = self.f.op('inspect_meaning_review', assessment_id=self.f.meaning['id'])
                self.assertFalse(status['current'])
                self.no_outcome_access(lambda: self.f.execute(self.compiled['id'], self.certificate['id']))

    def test_early_assessment_cannot_be_promoted_by_later_review(self):
        self.assertEqual(self.f.early_meaning['body']['independent_semantic_review'], 'NOT_SATISFIED')
        self.no_outcome_access(lambda: self.f.execute(self.compiled['id'], self.certificate['id'],
                                                    self.f.early_meaning['id']))

    def test_protected_snapshot_partition_is_denied_before_certificates_or_rows(self):
        # Fault injection creates a content-addressed copy and substitutes its
        # accepted-result pointer only in this disposable registry. It neither
        # qualifies protected data nor asserts a public way to forge the job.
        for index, change in enumerate((lambda value: value.update(data_class='assessment'),
                                        lambda value: value['body']['manifest'].update(partition='final'))):
            snapshot = self.injected(self.f.snapshot, change)
            def replace_snapshot(target):
                target['source_refs'] = sorted(snapshot['id'] if ref == self.f.snapshot['id'] else ref
                                               for ref in target['source_refs'])
                body = target['body']
                body['authorization_snapshot'] = target['source_refs']
                body['candidate']['test_universe']['data_snapshot_ref'] = snapshot['id']
                body['assessment'] = assess_candidate(body['idea_id'], ORIGINAL, body['candidate'],
                    body['semantic_report'], self.f.catalog, set(target['source_refs']))
            target = self.injected(self.f.formalization, replace_snapshot)
            self.assertEqual(target['body']['assessment']['status'], 'STRUCTURE_CHECKED')
            self.broker._db.execute('UPDATE jobs SET result_id=? WHERE id=?',
                                    (target['id'], self.f.formal_job))
            with self.subTest(mutation=index), patch.object(self.broker, '_feature_certificate_status',
                    side_effect=AssertionError('certificate accessed before partition gate')) as feature:
                self.no_outcome_access(lambda: self.broker.compile_exact(self.f.token,
                    formalization_id=target['id'], feature_certificate_id=self.f.feature['id'], as_of=AS_OF))
            feature.assert_not_called()

    def test_compiled_metadata_environment_and_exact_capsule_cannot_be_substituted(self):
        changes = [
            lambda item: item['body'].update(environment={}),
            lambda item: item['body']['compilation'].update(scientific_readiness=0),
            lambda item: item['body']['compilation']['request'].update(max_steps=99999),
            lambda item: item['body'].update(source_package_id='0' * 64),
        ]
        for index, change in enumerate(changes):
            injected = self.injected(self.compiled, change)
            with self.subTest(mutation=index):
                self.no_outcome_access(lambda: self.f.execute(injected['id'], self.certificate['id']))
        capsule = self.broker._artifact(self.compiled['body']['input_id'])
        for index, change in enumerate((lambda item: item['body'].update(input_sha256='0' * 64),
                lambda item: item['body']['data_use'].update(independent_confirmation=True))):
            wrong = self.injected(capsule, change)
            copied = self.injected(self.compiled, lambda item: item['body'].update(input_id=wrong['id']))
            with self.subTest(capsule=index):
                self.no_outcome_access(lambda: self.f.execute(copied['id'], self.certificate['id']))

    def test_composition_whole_envelope_request_result_and_json_types_are_binding(self):
        changes = [
            lambda item: item['body'].update(candidate_hash='0' * 64),
            lambda item: item['body'].update(compilation_hash='0' * 64),
            lambda item: item['body']['report'].update(request_hash='0' * 64),
            lambda item: item['body']['report'].update(mode='execute'),
            lambda item: item['body']['report'].pop('request_hash'),
            lambda item: item['body']['report'].update(environment={}),
            lambda item: item['body']['report']['result'].update(scientific_readiness=0),
        ]
        for index, change in enumerate(changes):
            injected = self.injected(self.certificate, change)
            with self.subTest(mutation=index), self.assertRaises(REJECTIONS):
                self.checked_composition(injected)

    def test_source_drift_and_current_feature_revocation_fence_outcomes(self):
        with patch.dict(execution.LOADED, {execution.HOST_FILES[0]: '0' * 64}):
            self.no_outcome_access(lambda: self.f.execute(self.compiled['id'], self.certificate['id']))
        self.revoke(self.f.feature['id'], 'feature-evidence')
        self.no_outcome_access(lambda: self.f.execute(self.compiled['id'], self.certificate['id']))

    def test_runtime_package_revocation_propagates_only_over_typed_execution_edges(self):
        capsule = self.compiled['body']['input_id']
        package = self.f.runtime['body']['source_package_id']
        revoked = self.revoke(package, 'runtime-package')
        expected = {package, self.f.runtime['id'], capsule, self.compiled['id'],
                    self.certificate['id'], self.executed['id']}
        self.assertTrue(expected <= set(revoked['body']['affected_artifact_ids']))
        for identity in expected:
            with self.subTest(typed=identity), self.assertRaises(Denied):
                self.broker._require_usable_dependencies(identity)
        self.no_outcome_access(lambda: self.f.execute(self.compiled['id'], self.certificate['id']))
        generic = self.f.op('add_source', body={'synthetic_note': 'provenance is not a technical-use edge'},
                            data_class='development', exposure=[self.executed['id']])
        inspected = self.broker._dependency_use(generic['id'])
        self.assertEqual(inspected['status'], 'UNKNOWN_BINDING')
        self.assertEqual(inspected['invalidations'], [])
        self.assertEqual(inspected['checked_versions'], [generic['id']])
        # Unsupported generic provenance acquires neither technical usability
        # nor transitive revocation merely by naming the old execution.

    def test_composition_package_revocation_does_not_revoke_unrelated_runtime_package(self):
        package = self.certificate['body']['source_package_id']
        revoked = self.revoke(package, 'composition-package')
        expected = {package, self.certificate['id'], self.executed['id']}
        self.assertTrue(expected <= set(revoked['body']['affected_artifact_ids']))
        self.assertNotIn(self.compiled['id'], revoked['body']['affected_artifact_ids'])
        self.broker._require_exact_qualification()
        self.broker._require_usable_dependencies(self.compiled['id'])
        self.no_outcome_access(lambda: self.f.execute(self.compiled['id'], self.certificate['id']))

    def test_base_completion_without_required_diagnostics_is_resource_stop(self):
        used = self.executed['body']['result']['report']['primitive_steps']
        compiled = self.f.compile(used)
        self.assertEqual(compiled['body']['status'], 'COMPILED')
        certificate = self.f.composition(compiled['id'])
        self.assertEqual(certificate['body']['status'], 'CONFORMANT')
        actual = self.f.execute(compiled['id'], certificate['id'])
        body = actual['body']
        self.assertEqual(body['status'], 'RESOURCE_STOP', body['error'])
        self.assertTrue(body['result']['report']['processing_complete'])
        self.assertFalse(body['result']['report']['diagnostics']['processing_complete'])
        self.assertFalse(body['complete_required_report'])
        self.assertIs(body['scientific_readiness'], False)
        self.assertEqual(body['verification']['result']['checked_cases'], 3)

    def test_backend_execution_failure_retains_attempt_gap_and_input_capsule(self):
        original = runtime.run_child
        def fail_execution(bundle, mode, *args, **kwargs):
            if mode == 'execute':
                raise RuntimeError('controlled backend execution failure')
            return original(bundle, mode, *args, **kwargs)
        with patch.object(runtime, 'run_child', side_effect=fail_execution):
            failed = self.f.execute(self.compiled['id'], self.certificate['id'])
        body = failed['body']
        self.assertEqual(body['status'], 'EXECUTION_GAP')
        self.assertEqual(body['error']['type'], 'RuntimeError')
        self.assertIn('controlled backend execution failure', body['error']['reason'])
        self.assertIsNone(body['result'])
        self.assertIsNone(body['verification'])
        self.assertFalse(body['complete_required_report'])
        self.assertEqual(failed['blob_refs'], [])
        inputs = [self.broker._artifact(ref) for ref in failed['source_refs']
                  if self.broker._artifact(ref)['body'].get('schema') == 'exact-execution-input/1']
        self.assertEqual(len(inputs), 1)
        self.assertEqual(inputs[0]['body']['compiled_id'], self.compiled['id'])
        self.assertEqual(inputs[0]['body']['meaning_assessment_id'], self.f.meaning['id'])


if __name__ == '__main__':
    unittest.main()
