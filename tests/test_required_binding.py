"""Independent owned /4 lifecycle checks using one invented 15-minute bar."""
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
import test_diagnostic_binding as diagnostic_support


PROFILE = 'reference-computation/4'
PINS = {
    'trading_researcher/REQUIRED_INPUTS.md': '2a851e4e24804c8623f4e486e3ed6e8c502753bf7b51da035a454e0b3c2e2f9c',
    'tests/test_required_inputs.py': 'aaa9ce55cb52101811b48624ddcd42957ff5050ea53735c407a96194e32a8fc4',
}
CLOSE = 'BTCUSDT.close@binance-spot-15m-v1'
OPEN = 'BTCUSDT.open@binance-spot-15m-v1'
IDEA = ('On every declared 15-minute decision coordinate, compare the log body return '
        'of the bar ending one bar before a two-bar outcome anchor, in basis points. '
        'The condition is that the close exactly one bar before the decision exceeds '
        '101 USDT/BTC. Unknown conditions remain in the observed whole scope. '
        'Unused decision or anchor containers are not additional required prices.')
SOURCE = '1577837700000,102,102,102,102,0,1577838599999,0,0,0,0,0\n'


def required_candidate(candidate):
    for value in (candidate['scope_ast'], candidate['condition_ast'], candidate['outcome']['program']):
        value['schema'] = 'research-ast/2'
    candidate['scope_ast']['expression'] = {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}
    candidate['condition_ast']['expression'] = {'op': 'gt',
        'left': {'op': 'lag', 'bars': 1, 'arg': {'op': 'feature', 'ref': CLOSE}},
        'right': {'op': 'literal', 'type': 'real', 'unit': 'USDT/BTC', 'value': '101'}}
    candidate['outcome']['program']['expression'] = {'op': 'mul',
        'left': {'op': 'literal', 'type': 'real', 'unit': 'basis_points', 'value': '10000'},
        'right': {'op': 'ln', 'arg': {'op': 'div',
            'left': {'op': 'lag', 'bars': 1, 'arg': {'op': 'feature', 'ref': CLOSE}},
            'right': {'op': 'lag', 'bars': 1, 'arg': {'op': 'feature', 'ref': OPEN}}}}}
    candidate['horizons']['outcome_bars'] = 2
    candidate['estimand']['unit'] = 'basis_points'
    candidate['feature_refs'] = sorted([CLOSE, OPEN])
    paths = ['/scope_ast/expression/value', '/condition_ast/expression/left/bars',
             '/condition_ast/expression/right/value', '/outcome/program/expression/left/value',
             '/outcome/program/expression/right/arg/left/bars',
             '/outcome/program/expression/right/arg/right/bars', '/horizons/outcome_bars']
    candidate['parameter_origins'] = [{'path': path, 'basis': 'preexisting_specification', 'source_refs': [],
        'rationale': 'Fixed independent synthetic required-input lifecycle expectation.'} for path in paths]


class RequiredBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = BindingFixture({'change': {'source_raw_csv': SOURCE}})
        try:
            cls.references = {}
            for version in (2, 3, 4):
                certificate = cls.setup.broker.call(cls.setup.token, 'certify_reference',
                                                    profile=f'reference-computation/{version}')
                if certificate['body']['status'] != 'CERTIFIED':
                    raise AssertionError({key: certificate['body'].get(key)
                                          for key in ('profile', 'status', 'reason', 'checks')})
                cls.references[version] = certificate
            cls.formalization = cls.setup.create_formalization(
                {'change': {'original_idea_text': IDEA}}, candidate_transform=required_candidate)
            cls.compiled3 = cls.setup.compile(cls.formalization, reference_certificate_id=cls.references[3]['id'])
            cls.execution3 = cls.setup.broker.call(cls.setup.token, 'execute_development', compiled_id=cls.compiled3['id'])
            with patch.object(binding, 'run_child', wraps=binding.run_child) as child:
                cls.compiled4 = cls.setup.compile(cls.formalization, reference_certificate_id=cls.references[4]['id'])
                cls.execution4 = cls.setup.broker.call(cls.setup.token, 'execute_development', compiled_id=cls.compiled4['id'])
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

    def assert_required_execution(self, execution, broker=None):
        body = execution['body']
        self.assertEqual(body['status'], 'DESCRIPTIVE_EXECUTION', body)
        self.assertEqual(body['profile'], 'bound-reference/4')
        self.assertEqual(body['case_format'], 'diagnostic-required-input-bounded-reference-cases-jsonl/1')
        self.assertEqual(execution['authority'], 'descriptive_reference_computation_only')
        result = body['result']
        self.assertEqual(result['report']['schema'], 'diagnostic-required-input-bounded-reference-cases/1')
        self.assertEqual(result['report']['evaluation_contract'], 'required-inputs/1')
        self.assertEqual(result['report']['diagnostics']['schema'], 'case-diagnostics/2')
        self.assertEqual(result['contrast']['schema'], 'required-input-bounded-reference-contrast/1')
        self.assertEqual((result['contrast']['scope_count'], result['contrast']['condition_count']), (1, 0))
        self.assertIsNone(result['contrast']['effect'])
        for record in (body, result, result['report'], result['report']['diagnostics'], result['contrast']):
            self.assertFalse(record['scientific_readiness'])
        cases, raw = self.cases(execution, broker)
        self.assertEqual([case['status'] for case in cases], ['ELIGIBLE', 'PARTITION_BOUNDARY', 'PARTITION_BOUNDARY'])
        self.assertEqual([case['condition'] for case in cases], [None, None, True])
        self.assertTrue(all(case['scope'] is True for case in cases))
        self.assertEqual(cases[0]['outcome'], {'schema': 'bounded-real/1',
            'lower': {'numerator': '0', 'denominator': '1'}, 'upper': {'numerator': '0', 'denominator': '1'}})
        self.assertEqual(cases[0]['trace']['earliest_observation'], 1577838600)
        self.assertFalse(cases[0]['trace']['unknown_input'])
        self.assertEqual(result['report']['diagnostics']['status'], 'COMPLETE')
        self.assertEqual(result['report']['diagnostics']['reason_counts']['condition_unknown'], 2)
        verification = body['verification']
        self.assertEqual(verification['mode'], 'verify')
        self.assertEqual(verification['result']['result_hash'], digest(result))
        self.assertEqual(verification['result']['case_blob'], result['case_blob'])
        self.assertEqual(verification['result']['checked_cases'], 3)
        self.assertFalse(verification['result']['scientific_readiness'])
        return raw

    def test_fixed_v4_certificate_adds_only_the_required_source_contract(self):
        v2_files = diagnostic_support.V2_FILES
        v3_files = v2_files | set(diagnostic_support.DIAGNOSTIC_PINS) | {'trading_researcher/case_diagnostics.py'}
        self.assertEqual(set(self.references[3]['body']['footprint']), v3_files)
        self.assertEqual(set(self.references[4]['body']['footprint']),
                         v3_files | set(PINS) | {'trading_researcher/required_inputs.py'})
        for version, count in ((2, 62), (3, 71), (4, 87)):
            body = self.references[version]['body']
            self.assertEqual(body['checks'], {'expression_cases': 112, 'outcome_cases': 31,
                'supplemental_tests': count, 'capability_probes': 9,
                'skipped': 0, 'failures': 0, 'errors': 0, 'unexpected_successes': 0})
            self.assertFalse(body['scientific_readiness'])
        certificate = self.references[4]
        self.assertEqual(certificate['authority'], 'implementation_conformance_only')
        package = self.setup.broker.call(self.setup.token, 'get_artifact',
                                        artifact_id=certificate['body']['source_package_id'])
        self.assertEqual(package['body']['profile'], PROFILE)
        for path, expected in PINS.items():
            self.assertEqual(certificate['body']['footprint'][path], expected)
            raw = self.setup.broker._read_blob_bytes(package['body']['files'][path]['sha256'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)

    def test_owned_v4_replay_corrects_population_and_preserves_exact_old_v3_replay(self):
        self.assertEqual([call.args[1] for call in self.child_calls], ['compile', 'execute', 'verify'])
        self.assertNotEqual(Path(self.child_calls[1].args[3]), Path(self.child_calls[2].args[3]))
        self.assertEqual(self.compiled4['body']['profile'], 'bound-reference/4')
        self.assert_required_execution(self.execution4)
        old_cases, old_raw = self.cases(self.execution3)
        self.assertEqual(self.execution3['body']['profile'], 'bound-reference/3')
        self.assertEqual([case['status'] for case in old_cases], ['DATA_GAP', 'PARTITION_BOUNDARY', 'DATA_GAP'])
        self.assertEqual(self.execution3['body']['result']['contrast']['scope_count'], 0)
        self.assertEqual(self.execution3['body']['result']['report']['schema'], 'diagnostic-bounded-reference-cases/1')
        self.assertEqual(self.execution4['body']['result']['rows'], self.execution3['body']['result']['rows'])
        again = self.setup.broker.call(self.setup.token, 'execute_development', compiled_id=self.compiled3['id'])
        self.assertEqual(again['body']['result'], self.execution3['body']['result'])
        self.assertEqual(self.cases(again)[1], old_raw)
        actions = [decode(row[0])['action'] for row in self.setup.broker._db.execute('SELECT envelope FROM events')]
        self.assertNotIn('EligibleOutcomeBatchCommitted', actions)

    def test_overrides_and_altered_required_expectations_cannot_be_certified(self):
        with patch.object(certification, 'run_reference_validation', wraps=certification.run_reference_validation) as runner:
            for override in ({'root': 'arbitrary'}, {'expected': {}}, {'report': {'status': 'CERTIFIED'}}):
                with self.subTest(override=override), self.assertRaises(Invalid):
                    self.setup.broker.call(self.setup.token, 'certify_reference', profile=PROFILE, **override)
            with self.assertRaises(Denied):
                self.setup.broker.call(self.setup.worker, 'certify_reference', profile=PROFILE)
            runner.assert_not_called()
        original = certification.read_bundle(PROFILE)
        for path in PINS:
            changed = {**original, path: original[path] + b'\n# changed independent expectation\n'}
            with self.subTest(path=path), patch.object(certification, 'read_bundle', return_value=changed), \
                    patch.object(certification.subprocess, 'run') as runner:
                failed = self.setup.broker.call(self.setup.token, 'certify_reference', profile=PROFILE)
                runner.assert_not_called()
                self.assertEqual(failed['body']['status'], 'CERTIFICATION_GAP')
                self.assertEqual(failed['body']['reason'], 'PINNED_INPUT_CHANGED')

    def test_backup_restore_reexecutes_v4_from_retained_source_and_case_bytes(self):
        backup, restored = self.setup.root / 'required-backup', self.setup.root / 'required-restored'
        self.setup.broker.call(self.setup.token, 'backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, self.setup.broker.directory / 'operator.key')
        other = Broker(restored)
        try:
            self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=self.execution4['id']), self.execution4)
            with patch.object(certification, 'read_bundle', side_effect=OSError('Synthetic workspace unavailable')):
                checked = other.call(other.admin_token, 'revalidate_reference',
                    source_package_id=self.references[4]['body']['source_package_id'])
                again = other.call(other.admin_token, 'execute_development', compiled_id=self.compiled4['id'])
            self.assertEqual(checked['body']['status'], 'CERTIFIED', checked['body'])
            self.assertEqual(checked['body']['profile'], PROFILE)
            self.assertEqual(checked['body']['validation_mode'], 'retained_package')
            self.assertEqual(checked['body']['footprint'], self.references[4]['body']['footprint'])
            self.assertEqual(again['body']['result'], self.execution4['body']['result'])
            self.assertEqual(self.assert_required_execution(again, other), self.cases(self.execution4)[1])
        finally:
            other.close()

    def test_requested_v2_reporting_contract_rejects_v2_and_v3_execution_profiles(self):
        broker, token = self.setup.broker, self.setup.token
        workers = ['required-fixture-first', 'required-fixture-second']
        for name in workers:
            broker.call(token, 'register_worker', name=name, role='discovery', capabilities=['research-record/v1'])
        discovery = broker.call(token, 'create_context', role='discovery', epoch=30, artifact_ids=[])
        profile = {'model': 'fixture/1', 'prompt_version': 'required-fixture/1',
            'max_calls': 2, 'max_tokens': 80000, 'max_seconds': 1800,
            'max_cost_units': 0, 'currency': 'NONE', 'mode': 'fixture',
            'prompts': {name: 'Synthetic transport fixture only.' for name in workers},
            'tools': [], 'generation_parameters': {}, 'max_output_tokens': 64,
            'call_timeout_seconds': 5, 'max_retries': 0}
        epoch = broker.call(token, 'create_research_epoch', key='required-contract-fixture',
                            context_id=discovery['id'], workers=workers, profile=profile)
        source = self.formalization['body']
        context = broker.call(token, 'create_context', role='formalizer', epoch=31,
            artifact_ids=[source['idea_id'], source['catalog_id'], self.setup.snapshot['id']])
        call_profile = {'model': 'fixture/1', 'prompt_version': 'required-fixture/1',
            'prompt': 'Synthetic contract fixture; no model is invoked.', 'generation_parameters': {},
            'max_output_tokens': 64, 'call_timeout_seconds': 5, 'max_retries': 0}
        broker.call(token, 'enqueue', key='required-contract-formalization', spec={
            'kind': 'formalization/v1', 'context_id': context['id'], 'purpose': 'Synthetic required-input gate',
            'allowed_workers': ['binding-formalizer'], 'max_attempts': 1, 'lease_seconds': 300,
            'deadline': broker._now() + 1800, 'dependencies': [], 'research_epoch_id': epoch['id'],
            'research_call_profile': call_profile, 'research_inputs': {'idea_id': source['idea_id'],
                'catalog_id': source['catalog_id'], 'definition_ids': [], 'reporting_contract': 'case-diagnostics/2'}})
        lease = broker.call(self.setup.worker, 'claim')['lease']
        packet = broker.call(self.setup.worker, 'auxiliary_input', lease=lease)
        self.assertEqual(packet['reporting_contract']['schema'], 'case-diagnostics/2')
        self.assertEqual(packet['reporting_contract']['path'], 'trading_researcher/REQUIRED_INPUTS.md')
        self.assertEqual(packet['reporting_contract']['sha256'], PINS['trading_researcher/REQUIRED_INPUTS.md'])
        request = {'model': call_profile['model'], 'prompt_version': call_profile['prompt_version'],
            'generation_parameters': {}, 'tools': [], 'messages': [
                {'role': 'system', 'content': call_profile['prompt']}, {'role': 'user', 'content': canonical(packet)}]}
        reserved = broker.call(self.setup.worker, 'reserve_research_call', lease=lease, key='required-fixture-reply',
            request=request, input_token_bound=len(canonical(request).encode('utf-8')),
            output_token_limit=64, cost_bound_units=0)
        broker.call(self.setup.worker, 'finish_research_call', lease=lease, call_id=reserved['call_id'],
            response={'status': 'completed', 'output': {'status': 'final',
                'candidate': deepcopy(source['candidate']), 'semantic_report': deepcopy(source['semantic_report'])}},
            usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
        formalization = broker.call(self.setup.worker, 'record_formalization', lease=lease,
            idea_id=source['idea_id'], catalog_id=source['catalog_id'], candidate=deepcopy(source['candidate']),
            semantic_report=deepcopy(source['semantic_report']), provider_call_id=reserved['call_id'])
        accepted = broker.call(self.setup.worker, 'submit', lease=lease, artifact_id=formalization['id'])
        self.assertTrue(accepted['accepted'], accepted)
        for version in (2, 3):
            with self.subTest(version=version), patch.object(binding, 'run_child', wraps=binding.run_child) as child:
                with self.assertRaises(Invalid):
                    self.setup.compile(formalization, reference_certificate_id=self.references[version]['id'])
                child.assert_not_called()
        compiled = self.setup.compile(formalization, reference_certificate_id=self.references[4]['id'])
        self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'])
        self.assertEqual(compiled['body']['profile'], 'bound-reference/4')
        self.assertEqual(broker.call(token, 'inspect_research_epoch', epoch_id=epoch['id'])['usage'],
                         {'calls': 1, 'tokens': 0, 'cost_units': 0})
        self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM provider_invocations').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
