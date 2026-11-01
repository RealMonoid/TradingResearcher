"""Independent D098 pure-library checks on invented, fully declared inputs.

Literal arithmetic and truth tables supply the expectations. These tests do
not enroll a native profile, certify source ownership, authenticate a report,
read a registry, or establish original-idea/model/scientific correctness.
"""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import unittest
from unittest.mock import patch

from trading_researcher import exact_resources_v2 as v2
from trading_researcher import exact_resource_candidate as engineering
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.exact_outcomes import materialize_exact


T, D = 1672531200, 900
CATALOG = {'x@1': {'type': 'real', 'unit': 'ratio'},
           'flag@1': {'type': 'boolean', 'unit': None}}


def stamp(when):
    return datetime.fromtimestamp(when, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def boolean(value):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def real(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': str(value)}


def feature(ref):
    return {'op': 'feature', 'ref': ref}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def guard(validity, predicate):
    return binary('eq', binary('or', validity, boolean(None)), predicate)


def program(expression):
    return {'schema': 'research-ast/4', 'catalog_hash': digest(CATALOG), 'expression': expression}


def request(steps=20_000_000, count=8):
    valid = {'op': 'trailing_all', 'bars': 3, 'arg': feature('flag@1')}
    return {'schema': 'exact-resource-case-request/2',
            'candidate_ref': 'invented-d098-review-only', 'data_snapshot_ref': 'no-native-data',
            'scope_program': program(boolean(True)),
            'condition_program': program(guard(valid, binary('gt', feature('x@1'), real(1)))),
            'outcome_program': program(binary('mul', real(1, 'basis_points'), feature('x@1'))),
            'outcome_scale': 'quantity', 'horizon_bars': 1,
            'universe': {'start': stamp(T), 'end': stamp(T + count * D), 'instruments': ['SYNTHETIC']},
            'as_of': stamp(T + count * D), 'max_steps': steps}


def rows(count=8):
    return [{'time': T + i * D, 'instrument': 'SYNTHETIC', 'features': {
                'x@1': {'value': str(i + 1), 'available_at': T + i * D},
                'flag@1': {'value': True, 'available_at': T + i * D}}}
            for i in range(count)]


def number(pair):
    return Fraction(int(pair['numerator']), int(pair['denominator']))


def exact_value(enclosure):
    low, high = number(enclosure['lower']), number(enclosure['upper'])
    if low != high:
        raise AssertionError('Invented rational outcome must have an exact singleton enclosure')
    return low


class ExactResourcesV2Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selected = request()
        cls.data = rows()
        cls.base = v2.materialize(cls.selected, CATALOG, cls.data)
        cls.remaining = cls.selected['max_steps'] - cls.base['primitive_steps']
        cls.observed = v2.add_diagnostics(cls.base, CATALOG, cls.data, cls.remaining)

    def test_literal_cases_contrast_and_counts_preserve_descriptive_scope(self):
        self.assertEqual(self.base['schema'], 'exact-resource-cases/2')
        self.assertEqual(self.base['profile'], 'exact-reference-computation/2')
        self.assertEqual(self.base['resource_contract'], 'exact-computation-resources/2.0')
        self.assertEqual(self.base['authority'], 'descriptive_calculation_only')
        self.assertNotIn('activation', self.base)
        self.assertIs(self.base['scientific_readiness'], False)
        self.assertEqual([case['decision_time'] for case in self.base['cases']],
                         [T + i * D for i in range(8)])
        self.assertEqual([case['condition'] for case in self.base['cases']],
                         [None, None, True, True, True, True, True, True])
        self.assertEqual([case['status'] for case in self.base['cases']],
                         ['ELIGIBLE'] * 7 + ['PARTITION_BOUNDARY'])
        self.assertEqual([exact_value(case['outcome']) for case in self.base['cases'][:7]],
                         list(map(Fraction, range(2, 9))))
        # Per decision: scope1 + strict guard13; seven reached outcomes cost3.
        # Observations additionally charge one replay step per case.
        self.assertEqual(self.base['primitive_steps'], 8 * 14 + 7 * 3)
        self.assertEqual(self.observed['diagnostics']['primitive_steps'], 8 * 15 + 7 * 3)
        comparison = v2.contrast(self.base)
        self.assertEqual(comparison['schema'], 'exact-resource-contrast/2')
        self.assertEqual((comparison['scope_count'], comparison['condition_count']), (7, 5))
        self.assertEqual(exact_value(comparison['scope_mean']), 5)
        self.assertEqual(exact_value(comparison['condition_mean']), 6)
        self.assertEqual(exact_value(comparison['effect']), 1)
        self.assertIs(comparison['scientific_readiness'], False)
        self.assertEqual(self.observed['diagnostics']['guard_counts'],
                         {'true': 6, 'false': 0, 'unknown': 2, 'unrecognized': 0, 'not_evaluated': 0})

    def test_real_twenty_million_counter_is_not_the_legacy_projection(self):
        selected, data = request(), rows()
        before = canonical([selected, data])
        seen = []
        actual_case = v2._case

        def record_counter(*args, **kwargs):
            seen.append(args[10][0])
            return actual_case(*args, **kwargs)

        projected = v2.structural_projection(selected)
        self.assertEqual(projected['max_steps'], 10_000_000)
        with patch.object(v2, '_case', side_effect=record_counter):
            base = v2.materialize(selected, CATALOG, data)
            observed = v2.add_diagnostics(base, CATALOG, data, self.remaining)
        self.assertEqual(seen[0], 20_000_000)
        self.assertEqual(seen[8], self.remaining - 1)
        self.assertEqual(base['request']['max_steps'], 20_000_000)
        self.assertEqual(observed['diagnostics']['limits']['remaining_steps'], 19_999_867)
        self.assertEqual(canonical([selected, data]), before)
        selected['max_steps'] = 1
        self.assertEqual(base['request']['max_steps'], 20_000_000)

    def test_request_and_record_budget_types_are_checked_before_projection(self):
        for budget in (None, False, True, 0, -1, 20_000_001, '20000000', 20_000_000.0):
            with self.subTest(budget=budget), self.assertRaises(Invalid):
                v2.structural_projection(request(budget))
        for budget in (1, 9_999_999, 10_000_000, 10_000_001, 19_999_999, 20_000_000):
            with self.subTest(valid_budget=budget):
                selected = request(budget)
                v2.structural_projection(selected)
                self.assertEqual(selected['max_steps'], budget)
        for consumed in (True, False, -1, 20_000_001, 133.0):
            bad = deepcopy(self.base); bad['primitive_steps'] = consumed
            with self.subTest(consumed=consumed), self.assertRaises(Invalid):
                v2.contrast(bad)

    def test_remaining_allocation_fences_and_partial_observation_keep_entire_base(self):
        original = canonical(self.base)
        for allocation in (False, True, -1, 1.0, self.remaining + 1, 20_000_001):
            with self.subTest(allocation=allocation), self.assertRaises(Invalid):
                v2.add_diagnostics(self.base, CATALOG, self.data, allocation)
        for allocation, reached in ((0, 0), (17, 0), (18, 1)):
            with self.subTest(allocation=allocation):
                stopped = v2.add_diagnostics(self.base, CATALOG, self.data, allocation)
                summary = stopped['diagnostics']
                self.assertEqual(summary['processed_cases'], reached)
                self.assertEqual(summary['primitive_steps'], allocation)
                self.assertEqual(summary['status'], 'RESOURCE_STOP')
                self.assertFalse(summary['processing_complete'])
                self.assertEqual(sum(case['diagnostics'] is not None for case in stopped['cases']), reached)
                self.assertEqual(canonical(v2.base_projection(stopped)), original)
                self.assertEqual(canonical(self.base), original)

    def test_old_and_engineering_namespaces_cannot_admit_or_relabel_v2(self):
        for other in ('exact-composition-case-request/1', engineering.REQUEST,
                      'bounded-reference-case-request/1', 'exact-resource-case-request/3'):
            bad = request(); bad['schema'] = other
            with self.subTest(schema=other), self.assertRaises(Invalid):
                v2.materialize(bad, CATALOG, self.data)
        for action in (materialize_exact, engineering.materialize):
            with self.subTest(action=action.__name__), self.assertRaises(Invalid):
                action(request(), CATALOG, self.data)
        with self.assertRaises(Invalid):
            materialize_exact({**request(), 'schema': 'exact-composition-case-request/1'}, CATALOG, self.data)
        for tag in ('exact-composition-cases/1', engineering.CASES):
            bad = deepcopy(self.base); bad['schema'] = tag
            with self.subTest(report=tag), self.assertRaises(Invalid): v2.contrast(bad)
        self.assertEqual(engineering.ACTIVATION, 'PENDING_SPECIFIC_RESOURCE_DECISION')

    def test_wrong_contract_authority_units_and_shape_do_not_become_a_v2_report(self):
        fields = {'resource_contract': 'exact-computation-resources/1.0',
                  'profile': engineering.PROFILE, 'authority': 'scientifically_certified',
                  'expression_contract': 'bounded-exact-compositions/999',
                  'evaluation_contract': 'required-inputs/999', 'numerical_contract': 'bounded-math/999',
                  'outcome_unit': 'ratio', 'scientific_readiness': 0,
                  'cases': None, 'state_counts': {}}
        for key, value in fields.items():
            bad = deepcopy(self.base); bad[key] = value
            for operation in ('contrast', 'observe'):
                with self.subTest(key=key, operation=operation), self.assertRaises(Invalid):
                    if operation == 'contrast': v2.contrast(bad)
                    else: v2.add_diagnostics(bad, CATALOG, self.data, self.remaining)
        bad = deepcopy(self.base); del bad['resource_contract']; bad['activation'] = 'ACCEPTED'
        with self.assertRaises(Invalid): v2.contrast(bad)

    def test_replay_compares_complete_case_json_types_and_source_values(self):
        mutations = [('scope_boolean', lambda case: case.update(scope=1)),
                     ('anchor_type', lambda case: case.update(outcome_anchor=float(case['outcome_anchor']))),
                     ('reason', lambda case: case.update(reason='plausible-but-unobserved')),
                     ('trace', lambda case: case['trace'].update(latest_available_at=0)),
                     ('interval', lambda case: case['label_information_interval'].update(start=0))]
        for label, mutate in mutations:
            changed = deepcopy(self.base); mutate(changed['cases'][3])
            with self.subTest(label=label), self.assertRaises(Invalid):
                v2.add_diagnostics(changed, CATALOG, self.data, self.remaining)
        altered_rows = deepcopy(self.data)
        altered_rows[4]['features']['x@1']['value'] = '99'
        with self.assertRaises(Invalid):
            v2.add_diagnostics(self.base, CATALOG, altered_rows, self.remaining)

    def test_base_hashes_bind_canonical_stream_and_metadata_independently(self):
        stream = ''.join(canonical(case) + '\n' for case in self.base['cases']).encode('utf-8')
        stream_hash = hashlib.sha256(stream).hexdigest()
        metadata = {key: value for key, value in self.base.items() if key != 'cases'}
        base_hash = hashlib.sha256(canonical({'report': metadata,
                    'case_stream_sha256': stream_hash}).encode('utf-8')).hexdigest()
        self.assertEqual(self.observed['base_case_stream_sha256'], stream_hash)
        self.assertEqual(self.observed['base_report_hash'], base_hash)
        self.assertEqual(canonical(v2.base_projection(self.observed)), canonical(self.base))
        for field in ('base_case_stream_sha256', 'base_report_hash', 'resource_contract'):
            bad = deepcopy(self.observed); bad[field] = '0' * 64
            with self.subTest(field=field), self.assertRaises(Invalid): v2.base_projection(bad)
        bad = deepcopy(self.observed); bad['cases'][3]['scope'] = 1
        with self.assertRaises(Invalid): v2.base_projection(bad)
        # Projection checks its bound numerical base. Authentication of a
        # diagnostic narrative or source ownership belongs to retained replay.
        narrative = deepcopy(self.observed)
        narrative['cases'][3]['diagnostics']['reason_categories'] = ['not_source_authenticated']
        self.assertEqual(canonical(v2.base_projection(narrative)), canonical(self.base))

    def test_malformed_diagnostic_base_containers_fail_as_typed_gaps(self):
        for replacement in (None, False, {}, [None], [False]):
            bad = deepcopy(self.observed); bad['cases'] = replacement
            with self.subTest(cases=replacement), self.assertRaises(Invalid): v2.base_projection(bad)
        bad = deepcopy(self.observed); del bad['cases']
        with self.assertRaises(Invalid): v2.base_projection(bad)

    def test_strict_guard_all_nine_truths_remain_neutral_observations(self):
        for valid in (True, False, None):
            for predicate in (True, False, None):
                with self.subTest(validity=valid, predicate=predicate):
                    selected = request(count=2)
                    selected['condition_program'] = program(guard(boolean(valid), boolean(predicate)))
                    base = v2.materialize(selected, CATALOG, rows(2))
                    observed = v2.add_diagnostics(base, CATALOG, rows(2),
                                                  selected['max_steps'] - base['primitive_steps'])
                    self.assertEqual([case['condition'] for case in base['cases']],
                                     [predicate if valid is True else None] * 2)
                    for case in observed['cases']:
                        self.assertEqual(case['diagnostics']['validity_guard'],
                            {'recognized': True, 'path': '/expression/left/left',
                             'evaluated': True, 'value': valid})
                    self.assertEqual(observed['diagnostics']['invalidity_interpretation'],
                                     'REQUIRES_INDEPENDENT_MEANING_REVIEW')

    def test_guard_false_positives_and_outer_lag_boolean_parameters_are_rejected(self):
        accepted = guard(boolean(True), boolean(False))
        self.assertEqual(v2.guard_path(accepted), '/expression/left/left')
        malformed = []
        item = deepcopy(accepted); item['left']['left'], item['left']['right'] = item['left']['right'], item['left']['left']; malformed.append(item)
        item = deepcopy(accepted); item['left'], item['right'] = item['right'], item['left']; malformed.append(item)
        item = deepcopy(accepted); item['left']['right']['type'] = 'real'; malformed.append(item)
        item = deepcopy(accepted); item['left']['right']['value'] = False; malformed.append(item)
        item = deepcopy(accepted); item['left']['extra'] = None; malformed.append(item)
        item = deepcopy(accepted); item['extra'] = None; malformed.append(item)
        malformed.extend([None, [], {'op': 'eq'}, {'op': 'eq', 'left': {'op': 'or'}, 'right': boolean(True)}])
        for index, item in enumerate(malformed):
            with self.subTest(malformed=index): self.assertIsNone(v2.guard_path(item))
        for bars in (True, False, -1, 0.0, 1_000_001):
            with self.subTest(bars=bars):
                self.assertIsNone(v2.guard_path({'op': 'lag', 'arg': accepted, 'bars': bars}))
        self.assertEqual(v2.guard_path({'op': 'lag', 'arg': accepted, 'bars': 0}),
                         '/expression/arg/left/left')

    def test_complete_windows_keep_missing_domain_and_later_unavailable_reasons(self):
        selected, data = request(), rows()
        reciprocal = binary('div', real(1), feature('x@1'))
        predicate = binary('gt', {'op': 'trailing_product', 'bars': 3, 'arg': reciprocal}, real(0))
        selected['condition_program'] = program(guard(boolean(True), predicate))
        data[1]['features']['x@1']['value'] = None
        data[2]['features']['x@1']['value'] = '0'
        data[3]['features']['x@1']['available_at'] = T + 4 * D
        plain = v2.materialize(selected, CATALOG, data)
        observed = v2.add_diagnostics(plain, CATALOG, data, selected['max_steps'] - plain['primitive_steps'])
        case = observed['cases'][3]
        self.assertEqual(case['status'], 'ELIGIBLE')
        self.assertIsNone(case['condition'])
        self.assertEqual(exact_value(case['outcome']), 5)
        events = case['diagnostics']['events']
        self.assertTrue({'missing_value', 'division_by_zero', 'not_yet_available'} <=
                        {event['reason'] for event in events})
        self.assertTrue({T + D, T + 2 * D, T + 3 * D} <= {event['observation_time'] for event in events})
        self.assertTrue({'missing_value', 'numeric_domain', 'unavailable_data'} <=
                        set(case['diagnostics']['reason_categories']))
        self.assertEqual(canonical(v2.base_projection(observed)), canonical(plain))

    def test_false_after_unknown_is_kleene_false_before_explicit_guard_override(self):
        selected, data = request(), rows()
        data[0]['features']['flag@1']['value'] = None
        data[1]['features']['flag@1']['value'] = False
        plain = v2.materialize(selected, CATALOG, data)
        observed = v2.add_diagnostics(plain, CATALOG, data, selected['max_steps'] - plain['primitive_steps'])
        case = observed['cases'][2]
        self.assertIs(case['diagnostics']['validity_guard']['value'], False)
        self.assertIsNone(case['condition'])
        self.assertEqual(case['status'], 'ELIGIBLE')
        self.assertEqual(exact_value(case['outcome']), 4)

    def test_plain_resource_stop_is_exact_prefix_without_aggregate_effect(self):
        partial = v2.materialize(request(75), CATALOG, self.data)
        self.assertEqual(partial['processed_case_count'], 4)
        self.assertEqual(partial['primitive_steps'], 75)
        self.assertEqual(canonical(partial['cases']), canonical(self.base['cases'][:4]))
        self.assertEqual(partial['status'], 'RESOURCE_STOP')
        self.assertIsNone(v2.contrast(partial)['effect'])
        observed = v2.add_diagnostics(partial, CATALOG, self.data, 0)
        self.assertFalse(observed['diagnostics']['processing_complete'])
        self.assertEqual(canonical(v2.base_projection(observed)), canonical(partial))

    def test_scope_exclusion_does_not_probe_unavailable_outcomes(self):
        selected, data = request(), rows()
        selected['scope_program'] = program(boolean(False))
        for row in data:
            for sample in row['features'].values(): sample['available_at'] += 100_000
        plain = v2.materialize(selected, CATALOG, data)
        observed = v2.add_diagnostics(plain, CATALOG, data, selected['max_steps'] - plain['primitive_steps'])
        self.assertEqual(plain['primitive_steps'], 8)
        self.assertTrue(all(case['status'] == 'SCOPE_FALSE' for case in plain['cases']))
        self.assertEqual(observed['diagnostics']['guard_counts']['not_evaluated'], 8)
        self.assertTrue(all(case['condition'] is None and case['outcome'] is None for case in plain['cases']))
        self.assertTrue(all(not case['diagnostics']['events'] for case in observed['cases']))

    def test_actual_event_cap_retains_all_plain_numeric_cases(self):
        selected = request()
        selected['condition_program']['expression']['left']['left']['bars'] = 3000
        plain = v2.materialize(selected, CATALOG, self.data)
        before = canonical(plain)
        observed = v2.add_diagnostics(plain, CATALOG, self.data, selected['max_steps'] - plain['primitive_steps'])
        self.assertTrue(plain['processing_complete'])
        self.assertEqual(observed['diagnostics']['processed_cases'], 0)
        self.assertIn('retained-event limit', observed['diagnostics']['reason'])
        self.assertEqual(canonical(v2.base_projection(observed)), before)
        self.assertEqual(canonical(plain), before)

    def test_actual_encoded_case_cap_preserves_plain_result_under_event_limit(self):
        selected = request()
        valid = selected['condition_program']['expression']['left']['left']
        valid['bars'] = 2000
        for _ in range(27): valid = binary('and', boolean(True), valid)
        selected['condition_program']['expression'] = guard(valid, boolean(True))
        plain = v2.materialize(selected, CATALOG, self.data)
        observed = v2.add_diagnostics(plain, CATALOG, self.data, selected['max_steps'] - plain['primitive_steps'])
        self.assertTrue(plain['processing_complete'])
        self.assertEqual(observed['diagnostics']['processed_cases'], 0)
        self.assertIn('encoded-size limit', observed['diagnostics']['reason'])
        self.assertEqual(canonical(v2.base_projection(observed)), canonical(plain))


if __name__ == '__main__':
    unittest.main()
