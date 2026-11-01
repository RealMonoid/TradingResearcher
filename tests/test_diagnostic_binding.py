"""Independent diagnostic-profile lifecycle checks on invented three-bar data.

The numerical oracle is the separately executed fixed /2 profile. Neither a
formalizer assertion nor diagnostic completion confers scientific readiness.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher import binding, certification
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.coordination import Broker, Denied
from trading_researcher.storage import restore_bundle
from binding_support import BindingFixture
from test_bounded_binding import IDEA, PINNED_TESTS, bounded_candidate


PROFILE = 'reference-computation/3'
DIAGNOSTIC_PINS = {
    'trading_researcher/CASE_DIAGNOSTICS.md': '54917962e900cc637cbe8e78b193f82842929078d65ca5e243f74a7dc855eed5',
    'tests/test_case_diagnostics.py': '423b1ae4449a9098dc8ba4d671f42d90560ec3dd9649ad8b5f106a7d36a6347a',
}
V2_FILES = {
    'docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md',
    'trading_researcher/EXPRESSIONS.md', 'trading_researcher/OUTCOMES.md',
    'tests/fixtures/reference_expression_cases.json',
    'tests/fixtures/reference_outcome_cases.json',
    'tests/test_expressions.py', 'tests/test_outcomes.py',
    'trading_researcher/__init__.py', 'trading_researcher/codec.py',
    'trading_researcher/errors.py', 'trading_researcher/expressions.py',
    'trading_researcher/outcomes.py', 'trading_researcher/certification.py',
    'docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md',
    'tests/test_bounded_math.py', 'tests/test_bounded_outcomes.py',
    'trading_researcher/bounded_math.py', 'trading_researcher/bounded_outcomes.py',
}


class DiagnosticBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = BindingFixture()
        try:
            cls.v2 = cls.setup.broker.call(cls.setup.token, 'certify_reference', profile='reference-computation/2')
            cls.v3 = cls.setup.broker.call(cls.setup.token, 'certify_reference', profile=PROFILE)
            for certificate in (cls.v2, cls.v3):
                if certificate['body']['status'] != 'CERTIFIED':
                    raise AssertionError(certificate['body'])
            cls.formalization = cls.setup.create_formalization(
                {'change': {'original_idea_text': IDEA}}, candidate_transform=bounded_candidate)
            cls.compiled2 = cls.setup.compile(cls.formalization, reference_certificate_id=cls.v2['id'])
            cls.execution2 = cls.setup.broker.call(cls.setup.token, 'execute_development', compiled_id=cls.compiled2['id'])
            with patch.object(binding, 'run_child', wraps=binding.run_child) as child:
                cls.compiled3 = cls.setup.compile(cls.formalization, reference_certificate_id=cls.v3['id'])
                cls.execution3 = cls.setup.broker.call(cls.setup.token, 'execute_development', compiled_id=cls.compiled3['id'])
            cls.child_calls = child.call_args_list
        except BaseException:
            cls.setup.close()
            raise

    @classmethod
    def tearDownClass(cls):
        cls.setup.close()

    def cases(self, execution, broker=None):
        broker = broker or self.setup.broker
        descriptor = execution['body']['result']['case_blob']
        raw = broker._read_blob_bytes(descriptor['sha256'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), descriptor['sha256'])
        self.assertEqual(len(raw), descriptor['size'])
        return [decode(line) for line in raw.splitlines()], raw

    def assert_diagnostic_execution(self, execution, broker=None):
        body = execution['body']
        self.assertEqual(body['status'], 'DESCRIPTIVE_EXECUTION', body)
        self.assertEqual(body['profile'], 'bound-reference/3')
        self.assertEqual(body['case_format'], 'diagnostic-bounded-reference-cases-jsonl/1')
        self.assertEqual(execution['authority'], 'descriptive_reference_computation_only')
        result = body['result']
        self.assertEqual(result['report']['schema'], 'diagnostic-bounded-reference-cases/1')
        self.assertEqual(result['report']['diagnostics']['schema'], 'case-diagnostics/1')
        self.assertEqual(result['contrast']['schema'], 'bounded-reference-contrast/1')
        for record in (body, result, result['report'], result['report']['diagnostics'], result['contrast']):
            self.assertFalse(record['scientific_readiness'])
        verification = body['verification']
        self.assertEqual(verification['mode'], 'verify')
        self.assertEqual(verification['result']['result_hash'], digest(result))
        self.assertEqual(verification['result']['case_blob'], result['case_blob'])
        self.assertEqual(verification['result']['checked_cases'], 3)
        self.assertFalse(verification['result']['scientific_readiness'])
        return self.cases(execution, broker)

    def test_explicit_profile_pins_new_expectations_and_preserves_v2_closure(self):
        self.assertEqual(set(self.v2['body']['footprint']), V2_FILES)
        self.assertEqual(self.v2['body']['checks']['supplemental_tests'], 62)
        self.assertEqual(set(self.v3['body']['footprint']),
                         V2_FILES | set(DIAGNOSTIC_PINS) | {'trading_researcher/case_diagnostics.py'})
        for certificate, count in ((self.v2, 62), (self.v3, 71)):
            body = certificate['body']
            self.assertEqual(body['checks'], {'expression_cases': 112, 'outcome_cases': 31,
                'supplemental_tests': count, 'capability_probes': 9,
                'skipped': 0, 'failures': 0, 'errors': 0, 'unexpected_successes': 0})
            self.assertEqual(certificate['authority'], 'implementation_conformance_only')
            self.assertFalse(body['scientific_readiness'])
        self.assertEqual(self.v3['body']['profile'], PROFILE)
        self.assertEqual(self.v3['body']['scope']['reporting_contract'], 'case-diagnostics/1')
        self.assertIn('semantic_equivalence', self.v3['body']['scope']['not_certified'])
        package = self.setup.broker.call(self.setup.token, 'get_artifact',
                                        artifact_id=self.v3['body']['source_package_id'])
        self.assertEqual(package['body']['profile'], PROFILE)
        for path, expected in {**PINNED_TESTS, **DIAGNOSTIC_PINS}.items():
            self.assertEqual(self.v3['body']['footprint'][path], expected)
            raw = self.setup.broker._read_blob_bytes(package['body']['files'][path]['sha256'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)

    def test_owned_replay_preserves_exact_v2_numerical_projection(self):
        self.assertEqual([call.args[1] for call in self.child_calls], ['compile', 'execute', 'verify'])
        self.assertNotEqual(Path(self.child_calls[1].args[3]), Path(self.child_calls[2].args[3]))
        self.assertEqual(self.compiled3['body']['profile'], 'bound-reference/3')
        cases, _ = self.assert_diagnostic_execution(self.execution3)
        base_cases, base_raw = self.cases(self.execution2)
        projection = [{key: value for key, value in case.items() if key != 'diagnostics'} for case in cases]
        self.assertEqual(projection, base_cases)
        self.assertEqual(''.join(canonical(case) + '\n' for case in projection).encode(), base_raw)
        result, base = self.execution3['body']['result'], self.execution2['body']['result']
        metadata = {key: value for key, value in result['report'].items()
                    if key not in ('diagnostics', 'base_report_hash', 'base_case_stream_sha256')}
        metadata['schema'] = 'bounded-reference-cases/1'
        self.assertEqual(metadata, base['report'])
        self.assertEqual(result['contrast'], base['contrast'])
        self.assertEqual(result['rows'], base['rows'])
        self.assertEqual(result['report']['base_case_stream_sha256'], base['case_blob']['sha256'])
        self.assertEqual(result['report']['base_report_hash'], digest({
            'report': base['report'], 'case_stream_sha256': base['case_blob']['sha256']}))
        diagnostic = result['report']['diagnostics']
        self.assertEqual((diagnostic['status'], diagnostic['processing_complete'], diagnostic['processed_cases']),
                         ('COMPLETE', True, 3))
        self.assertEqual(diagnostic['reason_counts']['condition_unknown'], 1)
        self.assertEqual(diagnostic['reason_counts']['absent_row'], 0)
        self.assertEqual(diagnostic['reason_counts']['missing_warmup'], 1)
        self.assertEqual(diagnostic['reason_counts']['boundary_censoring'], 1)
        self.assertEqual(diagnostic['guard_counts']['unrecognized'], 3)
        self.assertTrue(diagnostic['categories_overlap'])
        actions = [decode(row[0])['action'] for row in self.setup.broker._db.execute('SELECT envelope FROM events')]
        self.assertNotIn('EligibleOutcomeBatchCommitted', actions)

    def test_diagnostic_budget_stop_keeps_completed_numerical_result(self):
        numerical_steps = self.execution2['body']['result']['report']['primitive_steps']
        compiled = self.setup.compile(self.formalization, reference_certificate_id=self.v3['id'],
                                      max_steps=numerical_steps)
        execution = self.setup.broker.call(self.setup.token, 'execute_development', compiled_id=compiled['id'])
        cases, _ = self.assert_diagnostic_execution(execution)
        report = execution['body']['result']['report']
        self.assertTrue(report['processing_complete'])
        self.assertEqual(report['diagnostics']['status'], 'RESOURCE_STOP')
        self.assertFalse(report['diagnostics']['processing_complete'])
        self.assertEqual(report['diagnostics']['processed_cases'], 0)
        self.assertTrue(all(case['diagnostics'] is None for case in cases))
        projected = [{key: value for key, value in case.items() if key != 'diagnostics'} for case in cases]
        self.assertEqual(projected, self.cases(self.execution2)[0])
        self.assertEqual(execution['body']['result']['contrast'], self.execution2['body']['result']['contrast'])

    def test_fixed_profile_override_or_changed_reporting_contract_fails_closed(self):
        with patch.object(certification, 'run_reference_validation', wraps=certification.run_reference_validation) as runner:
            for override in ({'expected': {}}, {'root': 'arbitrary'}, {'report': {'status': 'CERTIFIED'}}):
                with self.subTest(override=override), self.assertRaises(Invalid):
                    self.setup.broker.call(self.setup.token, 'certify_reference', profile=PROFILE, **override)
            with self.assertRaises(Denied):
                self.setup.broker.call(self.setup.worker, 'certify_reference', profile=PROFILE)
            runner.assert_not_called()
        original = certification.read_bundle(PROFILE)
        for path in DIAGNOSTIC_PINS:
            changed = {**original, path: original[path] + b'\n# modified independent contract\n'}
            with self.subTest(path=path), patch.object(certification, 'read_bundle', return_value=changed), \
                    patch.object(certification.subprocess, 'run') as runner:
                failed = self.setup.broker.call(self.setup.token, 'certify_reference', profile=PROFILE)
                runner.assert_not_called()
                self.assertEqual(failed['body']['status'], 'CERTIFICATION_GAP')
                self.assertEqual(failed['body']['reason'], 'PINNED_INPUT_CHANGED')

    def test_requested_reporting_contract_cannot_downgrade_to_numerical_profile(self):
        broker, token = self.setup.broker, self.setup.token
        workers = ['diagnostic-fixture-first', 'diagnostic-fixture-second']
        for name in workers:
            broker.call(token, 'register_worker', name=name, role='discovery', capabilities=['research-record/v1'])
        discovery = broker.call(token, 'create_context', role='discovery', epoch=20, artifact_ids=[])
        profile = {'model': 'fixture/1', 'prompt_version': 'diagnostic-fixture/1',
            'max_calls': 2, 'max_tokens': 80000, 'max_seconds': 1800,
            'max_cost_units': 0, 'currency': 'NONE', 'mode': 'fixture',
            'prompts': {name: 'Synthetic transport fixture only.' for name in workers},
            'tools': [], 'generation_parameters': {}, 'max_output_tokens': 64,
            'call_timeout_seconds': 5, 'max_retries': 0}
        epoch = broker.call(token, 'create_research_epoch', key='diagnostic-contract-fixture',
                            context_id=discovery['id'], workers=workers, profile=profile)
        source = self.formalization['body']
        context = broker.call(token, 'create_context', role='formalizer', epoch=21,
            artifact_ids=[source['idea_id'], source['catalog_id'], self.setup.snapshot['id']])
        call_profile = {'model': 'fixture/1', 'prompt_version': 'diagnostic-fixture/1',
            'prompt': 'Synthetic transport fixture only; no model is invoked.',
            'generation_parameters': {}, 'max_output_tokens': 64, 'call_timeout_seconds': 5, 'max_retries': 0}
        broker.call(token, 'enqueue', key='diagnostic-contract-formalization', spec={
            'kind': 'formalization/v1', 'context_id': context['id'], 'purpose': 'Synthetic reporting requirement gate',
            'allowed_workers': ['binding-formalizer'], 'max_attempts': 1, 'lease_seconds': 300,
            'deadline': broker._now() + 1800, 'dependencies': [], 'research_epoch_id': epoch['id'],
            'research_call_profile': call_profile, 'research_inputs': {'idea_id': source['idea_id'],
                'catalog_id': source['catalog_id'], 'definition_ids': [], 'reporting_contract': 'case-diagnostics/1'}})
        lease = broker.call(self.setup.worker, 'claim')['lease']
        packet = broker.call(self.setup.worker, 'auxiliary_input', lease=lease)
        self.assertEqual(packet['reporting_contract']['schema'], 'case-diagnostics/1')
        self.assertEqual(packet['reporting_contract']['sha256'], DIAGNOSTIC_PINS['trading_researcher/CASE_DIAGNOSTICS.md'])
        # Exercise the real provenance transport with a synthetic fixture reply;
        # no provider invocation is created or dispatched.
        request = {'model': call_profile['model'], 'prompt_version': call_profile['prompt_version'],
            'generation_parameters': {}, 'tools': [], 'messages': [
                {'role': 'system', 'content': call_profile['prompt']},
                {'role': 'user', 'content': canonical(packet)}]}
        reserved = broker.call(self.setup.worker, 'reserve_research_call', lease=lease,
            key='diagnostic-fixture-reply', request=request,
            input_token_bound=len(canonical(request).encode('utf-8')), output_token_limit=64, cost_bound_units=0)
        broker.call(self.setup.worker, 'finish_research_call', lease=lease, call_id=reserved['call_id'],
            response={'status': 'completed', 'output': {'status': 'final',
                'candidate': deepcopy(source['candidate']), 'semantic_report': deepcopy(source['semantic_report'])}},
            usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
        formalization = broker.call(self.setup.worker, 'record_formalization', lease=lease,
            idea_id=source['idea_id'], catalog_id=source['catalog_id'],
            candidate=deepcopy(source['candidate']), semantic_report=deepcopy(source['semantic_report']),
            provider_call_id=reserved['call_id'])
        accepted = broker.call(self.setup.worker, 'submit', lease=lease, artifact_id=formalization['id'])
        self.assertTrue(accepted['accepted'], accepted)
        with patch.object(binding, 'run_child', wraps=binding.run_child) as child:
            with self.assertRaisesRegex(Invalid, 'exact diagnostic certificate'):
                self.setup.compile(formalization, reference_certificate_id=self.v2['id'])
            child.assert_not_called()
        compiled = self.setup.compile(formalization, reference_certificate_id=self.v3['id'])
        self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'])
        self.assertEqual(compiled['body']['profile'], 'bound-reference/3')
        self.assertFalse(compiled['body']['scientific_readiness'])
        self.assertEqual(broker.call(token, 'inspect_research_epoch', epoch_id=epoch['id'])['usage'],
                         {'calls': 1, 'tokens': 0, 'cost_units': 0})
        self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM provider_invocations').fetchone()[0], 0)

    def test_backup_restore_replays_retained_diagnostics_without_workspace_sources(self):
        backup, restored = self.setup.root / 'diagnostic-backup', self.setup.root / 'diagnostic-restored'
        self.setup.broker.call(self.setup.token, 'backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, self.setup.broker.directory / 'operator.key')
        other = Broker(restored)
        try:
            self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=self.execution3['id']),
                             self.execution3)
            with patch.object(certification, 'read_bundle', side_effect=OSError('Synthetic workspace unavailable')):
                certificate = other.call(other.admin_token, 'revalidate_reference',
                                         source_package_id=self.v3['body']['source_package_id'])
                replay = other.call(other.admin_token, 'execute_development', compiled_id=self.compiled3['id'])
            self.assertEqual(certificate['body']['status'], 'CERTIFIED', certificate['body'])
            self.assertEqual(certificate['body']['profile'], PROFILE)
            self.assertEqual(certificate['body']['validation_mode'], 'retained_package')
            self.assertEqual(certificate['body']['footprint'], self.v3['body']['footprint'])
            self.assertEqual(replay['body']['result'], self.execution3['body']['result'])
            self.assertEqual(self.assert_diagnostic_execution(replay, other)[1], self.cases(self.execution3)[1])
            package = other.call(other.admin_token, 'get_artifact',
                                 artifact_id=self.compiled3['body']['source_package_id'])
            self.assertEqual(package['body']['profile'], 'bound-reference/3')
        finally:
            other.close()


if __name__ == '__main__':
    unittest.main()
