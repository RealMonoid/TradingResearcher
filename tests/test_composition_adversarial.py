"""Independent static composition oracles; no market rows or heavy registry setup."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher import binding, composition
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied


class CompositionAdversarialTests(unittest.TestCase):
    def fixed(self, name):
        values = json.loads((composition.ROOT / composition.FIXTURE).read_text())['cases']
        return next(c for c in values if c['name'] == name)

    def test_self_consistent_underreported_warmup_passes_transport_but_not_conformance(self):
        original = composition.compile_payload
        def underreported(payload):
            result = deepcopy(original(payload))
            if result['warmup_seconds']:
                result['warmup_seconds'] = 0
                result['unavailable_warmup_seconds'] = 0
                result['row_window']['start'] = result['request']['universe']['start']
                result['maximum_input_rows'] = result['expected_case_count']
            return result
        case = self.fixed('nested_decision_lag_window')
        fabricated = underreported(case['payload'])
        self.assertNotEqual(fabricated, case['expected'])
        binding.validate_compilation(fabricated, case['payload'])
        with patch.object(composition, 'compile_payload', side_effect=underreported):
            with self.assertRaisesRegex(Invalid, 'nested_decision_lag_window'):
                composition.fixed_checks()

    def test_swapped_per_program_closures_cannot_hide_in_the_correct_global_union(self):
        original = composition.compile_payload
        def swapped(payload):
            result = deepcopy(original(payload))
            programs = result['programs']
            scope = programs['scope_program']['feature_refs']
            condition = programs['condition_program']['feature_refs']
            if scope and condition and scope != condition:
                programs['scope_program']['feature_refs'], programs['condition_program']['feature_refs'] = condition, scope
            return result
        case = self.fixed('per_program_feature_units_and_parameter_paths')
        fabricated = swapped(case['payload'])
        self.assertEqual(fabricated['feature_refs'], case['expected']['feature_refs'])
        self.assertNotEqual(fabricated['programs'], case['expected']['programs'])
        binding.validate_compilation(fabricated, case['payload'])
        with patch.object(composition, 'compile_payload', side_effect=swapped):
            with self.assertRaisesRegex(Invalid, 'per_program_feature_units_and_parameter_paths'):
                composition.fixed_checks()

    def test_plausible_parameter_pointer_is_not_an_exact_parameter_pointer(self):
        original = composition.compile_payload
        def wrong_pointer(payload):
            result = deepcopy(original(payload))
            result['programs']['condition_program']['parameter_paths'] = ['/expression/left/value']
            return result
        case = self.fixed('direct_price_quantity')
        fabricated = wrong_pointer(case['payload'])
        binding.validate_compilation(fabricated, case['payload'])
        with patch.object(composition, 'compile_payload', side_effect=wrong_pointer):
            with self.assertRaisesRegex(Invalid, 'direct_price_quantity'):
                composition.fixed_checks()

    def test_expected_gap_type_cannot_be_replaced_with_generic_rejection(self):
        original = composition.compile_payload
        def wrong_rejection(payload):
            if payload['max_steps'] is True:
                raise Invalid('Generic failure cannot stand in for the prescribed resource gap')
            return original(payload)
        with patch.object(composition, 'compile_payload', side_effect=wrong_rejection):
            with self.assertRaisesRegex(Invalid, 'boolean_step_budget_is_not_integer_budget'):
                composition.fixed_checks()

    def test_unexpected_runtime_failure_is_not_a_successful_negative_fixture(self):
        original = composition.compile_payload
        def crashed(payload):
            if payload['max_steps'] is True:
                raise RuntimeError('Independent crash counterexample')
            return original(payload)
        with patch.object(composition, 'compile_payload', side_effect=crashed):
            with self.assertRaisesRegex(RuntimeError, 'Independent crash counterexample'):
                composition.fixed_checks()

    def test_worker_is_denied_before_any_composition_dependency_access(self):
        with tempfile.TemporaryDirectory() as directory:
            broker = Broker(directory)
            try:
                worker = broker.call(broker.admin_token, 'register_worker', name='untrusted-composition',
                                     role='executor', capabilities=[])['token']
                with patch.object(broker, '_artifact', side_effect=AssertionError('Unauthorized artifact read')):
                    for operation, request in (
                        ('certify_composition', {'compiled_id': 'not-an-authorized-compiled-id'}),
                        ('composition_certificate_status', {'certificate_id': 'not-an-authorized-certificate'})):
                        with self.subTest(operation=operation), self.assertRaises(Denied):
                            broker.call(worker, operation, **request)
            finally:
                broker.close()


if __name__ == '__main__':
    unittest.main()
