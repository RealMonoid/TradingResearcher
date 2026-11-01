"""Six independent D089 integration checks through actual owned child paths.

The reused input is an invented three-bar fixture. Formalizer assertions are
not independent meaning approval. No provider or protected market data is used.
"""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher import binding, certification
from trading_researcher.codec import Invalid, decode, digest
from trading_researcher.coordination import Broker, Denied
from trading_researcher.storage import restore_bundle
from binding_support import BindingFixture


BOUNDED_PROFILE = 'reference-computation/2'
CLOSE = 'BTCUSDT.close@binance-spot-15m-v1'
PINNED_TESTS = {
    'tests/test_bounded_math.py': '18ef315b989c908fb3d48f001a19fb7ba678db597d4cce120ed0b28a1af15392',
    'tests/test_bounded_outcomes.py': '45448d44f7c4cafe2d6ce1c053bb0fb1915bbecda0216862c80c32c24506de94',
}
IDEA = ('Compare the next 15-minute close-to-current-close logarithmic return in basis points '
        'against the whole scope when the median of the current and previous closes exceeds '
        '101 USDT per BTC. Missing complete-window inputs leave the condition unknown.')


def bounded_candidate(candidate):
    for program in (candidate['scope_ast'], candidate['condition_ast'], candidate['outcome']['program']):
        program['schema'] = 'research-ast/2'
    close = {'op': 'feature', 'ref': CLOSE}
    candidate['condition_ast']['expression'] = {
        'op': 'gt', 'left': {'op': 'trailing_median', 'bars': 2, 'arg': deepcopy(close)},
        'right': {'op': 'literal', 'type': 'real', 'unit': 'USDT/BTC', 'value': '101'}}
    candidate['outcome']['program']['expression'] = {
        'op': 'mul', 'left': {'op': 'literal', 'type': 'real', 'unit': 'basis_points', 'value': '10000'},
        'right': {'op': 'ln', 'arg': {'op': 'div', 'left': deepcopy(close),
                  'right': {'op': 'lag', 'bars': 1, 'arg': deepcopy(close)}}}}
    candidate['estimand']['unit'] = 'basis_points'
    paths = ['/scope_ast/expression/value', '/condition_ast/expression/left/bars',
             '/condition_ast/expression/right/value', '/outcome/program/expression/left/value',
             '/outcome/program/expression/right/arg/right/bars', '/horizons/outcome_bars']
    candidate['parameter_origins'] = [
        {'path': path, 'basis': 'preexisting_specification', 'source_refs': [],
         'rationale': 'Fixed independent synthetic D089 integration expectation.'} for path in paths]


def expected_log_ratio(numerator, denominator):
    with localcontext() as context:
        context.prec = 120
        return 10000 * Fraction((Decimal(numerator) / Decimal(denominator)).ln())


class BoundedBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = BindingFixture()
        cls.reference = cls.setup.broker.call(cls.setup.token, 'certify_reference', profile=BOUNDED_PROFILE)
        if cls.reference['body']['status'] != 'CERTIFIED':
            cls.setup.close()
            raise AssertionError(cls.reference['body'])

    @classmethod
    def tearDownClass(cls):
        cls.setup.close()

    def formalization(self):
        return self.setup.create_formalization(
            {'change': {'original_idea_text': IDEA}}, candidate_transform=bounded_candidate)

    def compile(self, formalization=None):
        formalization = formalization or self.formalization()
        compiled = self.setup.compile(formalization, reference_certificate_id=self.reference['id'])
        self.assertEqual(compiled['body']['status'], 'COMPILED', compiled['body'])
        self.assertEqual(compiled['body']['profile'], 'bound-reference/2')
        self.assertEqual(compiled['body']['compilation']['request']['schema'], 'bounded-reference-case-request/1')
        self.assertFalse(compiled['body']['scientific_readiness'])
        return compiled

    def assert_contains(self, enclosure, expected, width=Fraction(1, 10**12)):
        self.assertEqual(set(enclosure), {'schema', 'lower', 'upper'})
        self.assertEqual(enclosure['schema'], 'bounded-real/1')
        lower, upper = [Fraction(int(enclosure[side]['numerator']), int(enclosure[side]['denominator']))
                        for side in ('lower', 'upper')]
        self.assertLessEqual(lower, expected)
        self.assertLessEqual(expected, upper)
        self.assertLessEqual(upper - lower, width)

    def assert_execution(self, broker, execution):
        body = execution['body']
        self.assertEqual(body['status'], 'DESCRIPTIVE_EXECUTION', body)
        self.assertEqual(body['profile'], 'bound-reference/2')
        self.assertEqual(body['case_format'], 'bounded-reference-cases-jsonl/1')
        self.assertEqual(execution['authority'], 'descriptive_reference_computation_only')
        self.assertFalse(body['scientific_readiness'])
        result = body['result']
        self.assertFalse(result['scientific_readiness'])
        self.assertFalse(result['report']['scientific_readiness'])
        self.assertFalse(result['contrast']['scientific_readiness'])
        self.assertEqual(result['report']['schema'], 'bounded-reference-cases/1')
        self.assertEqual(result['contrast']['schema'], 'bounded-reference-contrast/1')
        raw = broker._read_blob_bytes(result['case_blob']['sha256'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), result['case_blob']['sha256'])
        self.assertEqual(len(raw), result['case_blob']['size'])
        cases = [decode(line) for line in raw.splitlines()]
        self.assertEqual([case['status'] for case in cases], ['ELIGIBLE', 'ELIGIBLE', 'PARTITION_BOUNDARY'])
        self.assertEqual([case['condition'] for case in cases], [None, True, True])
        a, b = expected_log_ratio(102, 101), expected_log_ratio(103, 102)
        self.assert_contains(cases[0]['outcome'], a)
        self.assert_contains(cases[1]['outcome'], b)
        self.assertEqual((result['contrast']['scope_count'], result['contrast']['condition_count']), (2, 1))
        self.assert_contains(result['contrast']['scope_mean'], (a + b) / 2)
        self.assert_contains(result['contrast']['condition_mean'], b)
        self.assert_contains(result['contrast']['effect'], (b - a) / 2, 2 * Fraction(1, 10**12))
        verification = body['verification']
        self.assertEqual(verification['mode'], 'verify')
        self.assertEqual(verification['result']['result_hash'], digest(result))
        self.assertEqual(verification['result']['case_blob'], result['case_blob'])
        self.assertEqual(verification['result']['checked_cases'], 3)
        self.assertFalse(verification['result']['scientific_readiness'])
        return raw

    def test_explicit_v2_certificate_binds_independent_fixed_expectations(self):
        certificate = self.reference
        body = certificate['body']
        self.assertEqual(body['profile'], BOUNDED_PROFILE)
        self.assertEqual(body['checks']['supplemental_tests'], 62)
        for field in ('skipped', 'failures', 'errors', 'unexpected_successes'):
            self.assertEqual(body['checks'][field], 0)
        self.assertEqual(certificate['authority'], 'implementation_conformance_only')
        self.assertEqual(body['scope']['numerical_contract'], 'bounded-math/1.0')
        self.assertIn('research-ast/2', body['scope']['interfaces'])
        self.assertIn('semantic_equivalence', body['scope']['not_certified'])
        self.assertFalse(body['scientific_readiness'])
        package = self.setup.broker.call(self.setup.token, 'get_artifact',
                                        artifact_id=body['source_package_id'])
        self.assertEqual(package['body']['profile'], BOUNDED_PROFILE)
        for path, expected_hash in PINNED_TESTS.items():
            self.assertEqual(body['footprint'][path], expected_hash)
            blob = package['body']['files'][path]['sha256']
            self.assertEqual(hashlib.sha256(self.setup.broker._read_blob_bytes(blob)).hexdigest(), expected_hash)

    def test_old_certificate_cannot_authorize_bounded_candidate(self):
        formalization = self.formalization()
        self.assertEqual(formalization['body']['assessment']['status'], 'STRUCTURE_CHECKED')
        self.assertEqual(self.setup.reference['body']['profile'], 'reference-computation/1')
        with patch.object(binding, 'run_child', wraps=binding.run_child) as child:
            with self.assertRaises(Invalid):
                self.setup.compile(formalization)
            child.assert_not_called()
        self.assertFalse(formalization['body']['scientific_readiness'])

    def test_owned_execution_uses_separate_replay_and_preserves_interval_bytes(self):
        formalization = self.formalization()
        with patch.object(binding, 'run_child', wraps=binding.run_child) as child:
            compiled = self.compile(formalization)
            execution = self.setup.broker.call(self.setup.token, 'execute_development', compiled_id=compiled['id'])
        modes = [call.args[1] for call in child.call_args_list]
        self.assertEqual(modes, ['compile', 'execute', 'verify'])
        self.assertNotEqual(Path(child.call_args_list[1].args[3]), Path(child.call_args_list[2].args[3]))
        self.assert_execution(self.setup.broker, execution)
        self.assertIn(formalization['id'], execution['exposure'])
        self.assertIn(self.setup.snapshot['id'], execution['exposure'])
        actions = [decode(row[0])['action'] for row in
                   self.setup.broker._db.execute('SELECT envelope FROM events')]
        self.assertNotIn('EligibleOutcomeBatchCommitted', actions)
        self.assertEqual(self.setup.broker.call(self.setup.token, 'inspect_bound_computations')['pending'], 0)

    def test_overrides_and_changed_bounded_expectations_cannot_receive_a_certificate(self):
        with patch.object(certification, 'run_reference_validation', wraps=certification.run_reference_validation) as validator:
            for arguments in [{'profile': 'reference-computation/arbitrary'},
                              {'profile': BOUNDED_PROFILE, 'expected': {}},
                              {'profile': BOUNDED_PROFILE, 'root': 'arbitrary'},
                              {'profile': BOUNDED_PROFILE, 'report': {'status': 'CERTIFIED'}}]:
                with self.subTest(arguments=arguments), self.assertRaises(Invalid):
                    self.setup.broker.call(self.setup.token, 'certify_reference', **arguments)
            with self.assertRaises(Denied):
                self.setup.broker.call(self.setup.worker, 'certify_reference', profile=BOUNDED_PROFILE)
            validator.assert_not_called()
        original = certification.read_bundle(BOUNDED_PROFILE)
        for path in PINNED_TESTS:
            with self.subTest(path=path):
                changed = dict(original)
                changed[path] += b'\n# altered independent expectation\n'
                with patch.object(certification, 'read_bundle', return_value=changed), \
                        patch.object(certification.subprocess, 'run') as child:
                    failed = self.setup.broker.call(self.setup.token, 'certify_reference', profile=BOUNDED_PROFILE)
                    child.assert_not_called()
                self.assertEqual(failed['body']['status'], 'CERTIFICATION_GAP')
                self.assertEqual(failed['body']['reason'], 'PINNED_INPUT_CHANGED')
                self.assertEqual(failed['body']['profile'], BOUNDED_PROFILE)
                self.assertFalse(failed['body']['scientific_readiness'])

    def test_retained_v2_source_revalidates_without_reading_installed_workspace(self):
        package_id = self.reference['body']['source_package_id']
        with patch.object(certification, 'read_bundle', side_effect=OSError('Synthetic workspace unavailable')):
            replay = self.setup.broker.call(self.setup.token, 'revalidate_reference', source_package_id=package_id)
        self.assertEqual(replay['body']['status'], 'CERTIFIED', replay['body'])
        self.assertEqual(replay['body']['profile'], BOUNDED_PROFILE)
        self.assertEqual(replay['body']['validation_mode'], 'retained_package')
        self.assertEqual(replay['body']['source_package_id'], package_id)
        self.assertEqual(replay['body']['footprint'], self.reference['body']['footprint'])
        self.assertFalse(replay['body']['scientific_readiness'])

    def test_backup_restore_reexecutes_v2_retained_source_with_identical_bounds(self):
        compiled = self.compile()
        execution = self.setup.broker.call(self.setup.token, 'execute_development', compiled_id=compiled['id'])
        original_raw = self.assert_execution(self.setup.broker, execution)
        backup, restored = self.setup.root / 'bounded-backup', self.setup.root / 'bounded-restored'
        self.setup.broker.call(self.setup.token, 'backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, self.setup.broker.directory / 'operator.key')
        other = Broker(restored)
        try:
            self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=compiled['id']), compiled)
            self.assertEqual(other.call(other.admin_token, 'get_artifact', artifact_id=execution['id']), execution)
            with patch.object(certification, 'read_bundle', side_effect=OSError('Synthetic workspace unavailable')):
                again = other.call(other.admin_token, 'execute_development', compiled_id=compiled['id'])
            self.assertEqual(again['body']['result'], execution['body']['result'])
            self.assertEqual(self.assert_execution(other, again), original_raw)
            package = other.call(other.admin_token, 'get_artifact', artifact_id=compiled['body']['source_package_id'])
            self.assertEqual(package['body']['profile'], 'bound-reference/2')
        finally:
            other.close()


if __name__ == '__main__':
    unittest.main()
