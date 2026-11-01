"""Independent checks of a proposed OFFLINE engineering allowance only.

No native selector, certificate, resource grant, market input or paid call is
used. The 20M request is explicit; projecting its structure through an old
validator never establishes old-profile admission. Malformed guard probes
exercise the standalone recognizer, not an execution-admission bypass.
"""
from copy import deepcopy
from collections import Counter
import unittest
from unittest.mock import patch

from exact_mapping_support import supplied, programs
from test_exact_compositions import FIXTURE
from test_exact_runtime import history
import trading_researcher.exact_resource_candidate as proposed
from trading_researcher.codec import Invalid, canonical
from trading_researcher.exact_outcomes import REQUEST as OLD_REQUEST, materialize_exact
from trading_researcher.exact_runtime import compile_payload


def literal(value, kind='boolean', unit=None):
    return {'op': 'literal', 'type': kind, 'unit': unit, 'value': value}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def request(max_steps=20_000_000):
    old = compile_payload(supplied())['request']
    return {**old, 'schema': proposed.REQUEST, 'max_steps': max_steps}


def guarded(predicate):
    return binary('eq', binary('or', predicate, literal(None)), literal(True))


def window_request(bars, zero_lags=0):
    selected = request()
    predicate = {'op': 'trailing_all', 'bars': bars,
        'arg': binary('gt', {'op': 'feature', 'ref': 'Q@1'}, literal('0', 'real', 'quote_USDT'))}
    for _ in range(zero_lags):
        predicate = {'op': 'lag', 'arg': predicate, 'bars': 0}
    selected['condition_program'] = {**selected['condition_program'], 'expression': guarded(predicate)}
    return selected


class ExactResourceCandidateReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.request = request()
        cls.rows = history()
        cls.base = proposed.materialize(cls.request, FIXTURE['catalog'], cls.rows)
        cls.remaining = cls.request['max_steps'] - cls.base['primitive_steps']
        cls.diagnostic = proposed.add_diagnostics(cls.base, FIXTURE['catalog'], cls.rows, cls.remaining)

    def test_explicit_20m_actual_request_and_counters_are_not_structurally_clamped(self):
        selected = request(); before = canonical(selected)
        projection = proposed.structural_projection(selected)
        self.assertEqual(projection['max_steps'], 10_000_000)
        self.assertEqual(canonical(selected), before)
        seen = []
        actual_case = proposed._case
        def observe_counter(*args, **kwargs):
            seen.append(args[10][0])
            return actual_case(*args, **kwargs)
        with patch.object(proposed, '_case', side_effect=observe_counter):
            base = proposed.materialize(selected, FIXTURE['catalog'], self.rows)
        self.assertEqual(seen[0], 20_000_000)
        self.assertEqual(base['request']['max_steps'], 20_000_000)
        self.assertEqual(canonical(base), canonical(self.base))
        self.assertGreater(self.remaining, 10_000_000)
        self.assertEqual(self.diagnostic['diagnostics']['limits']['remaining_steps'], self.remaining)
        self.assertLessEqual(base['primitive_steps'] + self.diagnostic['diagnostics']['primitive_steps'], 20_000_000)
        self.assertEqual(base['activation'], 'PENDING_SPECIFIC_RESOURCE_DECISION')
        self.assertEqual(base['authority'], 'offline_engineering_only')
        self.assertIs(base['scientific_readiness'], False)

    def test_budget_bounds_types_and_report_consumption_validate_before_projection(self):
        for amount in (0, -1, True, False, 20_000_001, 20_000_000.0, '20000000', None):
            with self.subTest(amount=amount), self.assertRaises(Invalid):
                proposed.structural_projection(request(amount))
        for amount in (1, 10_000_001, 19_999_999, 20_000_000):
            selected = request(amount)
            proposed.structural_projection(selected)
            self.assertEqual(selected['max_steps'], amount)
        for amount in (-1, False, self.request['max_steps'] + 1):
            altered = deepcopy(self.base); altered['primitive_steps'] = amount
            with self.subTest(consumption=amount), self.assertRaises(Invalid):
                proposed.contrast(altered)
        altered = deepcopy(self.base); altered['request']['max_steps'] = 20_000_001
        with self.assertRaises(Invalid):
            proposed.contrast(altered)

    def test_only_remaining_shared_allowance_can_fund_observation(self):
        before = canonical(self.base)
        for amount in (-1, False, self.remaining + 1, 20_000_001):
            with self.subTest(allocation=amount), self.assertRaises(Invalid):
                proposed.add_diagnostics(self.base, FIXTURE['catalog'], self.rows, amount)
        stopped = proposed.add_diagnostics(self.base, FIXTURE['catalog'], self.rows, 0)
        self.assertFalse(stopped['diagnostics']['processing_complete'])
        self.assertEqual(stopped['diagnostics']['processed_cases'], 0)
        self.assertEqual(stopped['diagnostics']['primitive_steps'], 0)
        self.assertEqual(canonical(proposed.base_projection(stopped)), before)
        self.assertEqual(canonical(self.base), before)

    def test_exact_guard_shapes_and_false_positives_remain_unrecognized(self):
        strict = programs()['condition']['expression']
        original = FIXTURE['programs']['condition']['expression']
        self.assertEqual(proposed.guard_path(strict), '/expression/arg/left/left')
        self.assertEqual(proposed.guard_path(original), '/expression/arg/left/left')
        changed = deepcopy(strict); changed['arg']['left']['right']['value'] = False
        self.assertIsNone(proposed.guard_path(changed))
        changed = deepcopy(strict); changed['arg']['op'] = 'and'
        self.assertIsNone(proposed.guard_path(changed))
        changed = deepcopy(strict)
        changed['arg']['left'], changed['arg']['right'] = changed['arg']['right'], changed['arg']['left']
        self.assertIsNone(proposed.guard_path(changed))
        # A recognizer is not the typed parser, but it must not describe an
        # incomplete/malformed object as the exact accepted syntactic shape.
        v = literal(True); null = literal(None)
        malformed = [None, [], {'op': 'eq'}, {'op': 'eq', 'left': binary('or', v, null)},
            {'op': 'eq', 'left': {'op': 'or'}, 'right': literal(True)},
            {'op': 'lag', 'arg': None, 'bars': 1}]
        for index, value in enumerate(malformed):
            with self.subTest(malformed=index):
                self.assertIsNone(proposed.guard_path(value))
        extra = binary('eq', binary('or', v, null), literal(False)); extra['unexpected'] = True
        self.assertIsNone(proposed.guard_path(extra))

    def test_whole_case_comparison_preserves_json_types_and_exclusion_metadata(self):
        mutations = [
            lambda value: value['cases'][40].update(condition=1),
            lambda value: value['cases'][40].update(scope=1),
            lambda value: value['cases'][40].update(outcome_anchor=float(value['cases'][40]['outcome_anchor'])),
            lambda value: value['cases'][40].update(reason='different unverified reason'),
            lambda value: value['cases'][40]['label_information_interval'].update(
                start=float(value['cases'][40]['label_information_interval']['start'])),
        ]
        for index, mutate in enumerate(mutations):
            altered = deepcopy(self.base); mutate(altered)
            with self.subTest(mutation=index), self.assertRaises(Invalid):
                proposed.add_diagnostics(altered, FIXTURE['catalog'], self.rows, self.remaining)
        altered = deepcopy(self.base)
        altered['cases'][40]['status'] = 'OUTCOME_MISSING'
        counts = Counter(case['status'] for case in altered['cases'])
        altered['state_counts'] = {key: counts[key] for key in altered['state_counts']}
        with self.assertRaises(Invalid):
            proposed.add_diagnostics(altered, FIXTURE['catalog'], self.rows, self.remaining)

    def test_base_binding_restores_bytes_and_rejects_tampered_projection(self):
        self.assertTrue(self.diagnostic['diagnostics']['processing_complete'])
        self.assertEqual(canonical(proposed.base_projection(self.diagnostic)), canonical(self.base))
        self.assertEqual(self.diagnostic['diagnostics']['guard_counts']['unrecognized'], 0)
        for change in (lambda item: item['cases'][40].update(scope=1),
                       lambda item: item.update(base_case_stream_sha256='0' * 64),
                       lambda item: item.update(base_report_hash='0' * 64)):
            altered = deepcopy(self.diagnostic); change(altered)
            with self.assertRaises(Invalid): proposed.base_projection(altered)

    def test_actual_event_overflow_retains_complete_plain_result(self):
        selected = window_request(3000)
        plain = proposed.materialize(selected, FIXTURE['catalog'], self.rows)
        before = canonical(plain)
        self.assertTrue(plain['processing_complete'])
        diagnostic = proposed.add_diagnostics(plain, FIXTURE['catalog'], self.rows,
                                              selected['max_steps'] - plain['primitive_steps'])
        self.assertEqual(diagnostic['diagnostics']['status'], 'RESOURCE_STOP')
        self.assertIn('retained-event limit', diagnostic['diagnostics']['reason'])
        self.assertEqual(diagnostic['diagnostics']['processed_cases'], 0)
        self.assertTrue(all(case['diagnostics'] is None for case in diagnostic['cases']))
        self.assertEqual(canonical(proposed.base_projection(diagnostic)), before)
        self.assertEqual(canonical(plain), before)

    def test_actual_encoded_byte_overflow_keeps_numeric_cases(self):
        # 2000 unique feature events remain below2048, while the exact deep
        # right-branch pointers make the canonical case exceed512KiB. Existing
        # AND(true,V) identities preserve the predicate and read every input.
        selected = window_request(2000)
        predicate = selected['condition_program']['expression']['left']['left']
        for _ in range(27):
            predicate = binary('and', literal(True), predicate)
        selected['condition_program']['expression'] = guarded(predicate)
        plain = proposed.materialize(selected, FIXTURE['catalog'], self.rows)
        self.assertTrue(plain['processing_complete'])
        diagnostic = proposed.add_diagnostics(plain, FIXTURE['catalog'], self.rows,
                                              selected['max_steps'] - plain['primitive_steps'])
        self.assertEqual(diagnostic['diagnostics']['status'], 'RESOURCE_STOP')
        self.assertIn('encoded-size limit', diagnostic['diagnostics']['reason'])
        self.assertEqual(diagnostic['diagnostics']['processed_cases'], 0)
        self.assertEqual(canonical(proposed.base_projection(diagnostic)), canonical(plain))

    def test_stopped_base_is_an_exact_prefix_with_no_aggregate_effect(self):
        selected = request(5000)
        partial = proposed.materialize(selected, FIXTURE['catalog'], self.rows)
        count = partial['processed_case_count']
        self.assertGreater(count, 0); self.assertLess(count, 55)
        self.assertEqual(partial['cases'], self.base['cases'][:count])
        self.assertEqual(partial['primitive_steps'], 5000)
        self.assertEqual(proposed.contrast(partial)['status'], 'RESOURCE_STOP')
        self.assertIsNone(proposed.contrast(partial)['effect'])
        diagnostic = proposed.add_diagnostics(partial, FIXTURE['catalog'], self.rows, 0)
        self.assertFalse(diagnostic['diagnostics']['processing_complete'])
        self.assertEqual(canonical(proposed.base_projection(diagnostic)), canonical(partial))

    def test_scope_false_does_not_evaluate_condition_or_outcome_for_diagnostics(self):
        selected = request()
        selected['scope_program'] = {**selected['scope_program'], 'expression': literal(False)}
        rows = deepcopy(self.rows)
        for row in rows:
            for sample in row['features'].values(): sample['available_at'] += 100_000_000
        plain = proposed.materialize(selected, FIXTURE['catalog'], rows)
        diagnostic = proposed.add_diagnostics(plain, FIXTURE['catalog'], rows,
                                              selected['max_steps'] - plain['primitive_steps'])
        self.assertTrue(diagnostic['diagnostics']['processing_complete'])
        self.assertEqual(diagnostic['diagnostics']['guard_counts']['not_evaluated'], 55)
        self.assertTrue(all(case['condition'] is None and case['outcome'] is None for case in plain['cases']))
        self.assertTrue(all(not case['diagnostics']['events'] for case in diagnostic['cases']))

    def test_new_budget_remains_unavailable_to_old_api_and_invalid_program_scope(self):
        old = {**self.request, 'schema': OLD_REQUEST}
        with self.assertRaises(Invalid): materialize_exact(old, FIXTURE['catalog'], self.rows)
        for mutate in (lambda value: value['universe'].update(instruments=['BTCUSDT', 'ETHUSDT']),
                       lambda value: value['condition_program'].update(schema='research-ast/2'),
                       lambda value: value.update(outcome_scale='binary_probability')):
            altered = request(); mutate(altered)
            with self.assertRaises(Invalid): proposed.structural_projection(altered)
        altered = request(); altered['outcome_program']['expression'] = literal('1', 'real', 'ratio')
        with self.assertRaises(Invalid): proposed.materialize(altered, FIXTURE['catalog'], self.rows)


if __name__ == '__main__':
    unittest.main()
