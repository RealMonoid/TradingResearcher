"""Portable independent compiler-metadata goldens for the D098 v2 route.

No child, row history, registry, provider, native fixture, or source bundle is
created. The literal sample is engineering input, not an accepted hypothesis
or independent natural-language meaning review. Static compilation promises
neither sufficient execution budget nor completed scientific evaluation.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid, canonical
from trading_researcher import exact_runtime as legacy, exact_runtime_v2 as runtime
from trading_researcher.exact_compositions import ExactCompositionEngine


T, D = 1672531200, 900
CATALOG = {'x@1': {'type': 'real', 'unit': 'ratio'},
           'flag@1': {'type': 'boolean', 'unit': None}}


def stamp(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def identity(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': str(value)}


def boolean(value):
    return {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': value}


def feature(ref):
    return {'op': 'feature', 'ref': ref}


def binary(op, left, right):
    return {'op': op, 'left': left, 'right': right}


def window(op, arg, bars):
    return {'op': op, 'arg': arg, 'bars': bars}


def program(expression):
    return {'schema': 'research-ast/4', 'catalog_hash': identity(CATALOG), 'expression': expression}


def supplied(max_steps=20_000_000):
    """Return fresh literal metadata; no evaluation or filesystem reads."""
    condition = binary('and',
        window('lag', window('trailing_all', feature('flag@1'), 4), 2),
        binary('gt', {'op': 'integer_power', 'arg': window('trailing_product', feature('x@1'), 3),
                      'exponent': 2}, literal(1)))
    outcome = binary('mul', literal(1, 'basis_points'),
                     window('trailing_product', window('lag', feature('x@1'), 2), 9))
    paths = ['/horizons/outcome_bars', '/scope_ast/expression/value',
        '/condition_ast/expression/left/bars', '/condition_ast/expression/left/arg/bars',
        '/condition_ast/expression/right/left/exponent', '/condition_ast/expression/right/left/arg/bars',
        '/condition_ast/expression/right/right/value', '/outcome/program/expression/left/value',
        '/outcome/program/expression/right/bars', '/outcome/program/expression/right/arg/bars']
    candidate = {'schema': 'hypothesis-exec/3', 'idea_ref': 'fixed-invented-compiler-example',
        'claim_kind': 'difference',
        'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'basis_points',
            'weighting': 'equal_rows', 'missingness': 'scope-true-outcome-observed/1',
            'condition_unknown': 'exclude-from-condition-retain-in-scope', 'nuisance_fit': 'none',
            'direction': 'nondirectional'},
        'scope_ast': program(boolean(True)), 'condition_ast': program(condition),
        'outcome': {'program': program(outcome), 'scale': 'quantity'},
        'comparator': {'kind': 'whole_scope'}, 'horizons': {'grid_seconds': 900, 'outcome_bars': 3},
        'test_universe': {'start': stamp(T + 10 * D), 'end': stamp(T + 20 * D),
            'instruments': ['SYNTHETIC'], 'data_snapshot_ref': 'invented-snapshot-only'},
        'parameter_origins': [{'path': path, 'basis': 'preexisting_specification',
            'source_refs': ['fixed-invented-compiler-example'], 'rationale': 'Literal engineering fixture.'}
            for path in paths],
        'feature_refs': ['flag@1', 'x@1']}
    return {'formalization_id': 'invented-unaccepted-formalization', 'candidate': candidate,
        'catalog': deepcopy(CATALOG), 'data_manifest': {'partition': 'development', 'universe': {
            'start': stamp(T + 5 * D), 'end': stamp(T + 22 * D),
            'instruments': ['UNUSED', 'SYNTHETIC']}},
        'as_of': stamp(T + 22 * D), 'max_steps': max_steps}


class ExactCompositionV2Review(unittest.TestCase):
    def test_literal_full_compilation_metadata(self):
        original = supplied(); before = canonical(original); candidate = original['candidate']
        # Complete Boolean history:2 lag +3 window slots =5 bars. Outcome
        # history:2 lag +8 window slots =10 bars; horizon3 leaves7 warmup
        # bars. Only5 of those7 fit the supplied manifest:15 loaded rows,
        # two unavailable warmup bars,10 declared cases. No rows are fetched.
        expected = {'schema': 'exact-compilation/2', 'resource_contract': 'exact-computation-resources/2.0',
            'request': {'schema': 'exact-resource-case-request/2',
                'candidate_ref': 'invented-unaccepted-formalization', 'data_snapshot_ref': 'invented-snapshot-only',
                'scope_program': candidate['scope_ast'], 'condition_program': candidate['condition_ast'],
                'outcome_program': candidate['outcome']['program'], 'outcome_scale': 'quantity',
                'horizon_bars': 3, 'universe': {'start': stamp(T + 10 * D), 'end': stamp(T + 20 * D),
                    'instruments': ['SYNTHETIC']}, 'as_of': stamp(T + 22 * D), 'max_steps': 20_000_000},
            'candidate_hash': identity(candidate),
            'programs': {
                'scope_program': {'type': 'boolean', 'unit': None, 'feature_refs': [],
                    'parameter_paths': ['/expression/value']},
                'condition_program': {'type': 'boolean', 'unit': None, 'feature_refs': ['flag@1', 'x@1'],
                    'parameter_paths': ['/expression/left/bars', '/expression/left/arg/bars',
                        '/expression/right/left/exponent', '/expression/right/left/arg/bars',
                        '/expression/right/right/value']},
                'outcome_program': {'type': 'real', 'unit': 'basis_points', 'feature_refs': ['x@1'],
                    'parameter_paths': ['/expression/left/value', '/expression/right/bars',
                        '/expression/right/arg/bars']}},
            'feature_refs': ['flag@1', 'x@1'],
            'row_window': {'start': stamp(T + 5 * D), 'end': stamp(T + 20 * D), 'instruments': ['SYNTHETIC']},
            'warmup_seconds': 7 * D, 'unavailable_warmup_seconds': 2 * D,
            'maximum_input_rows': 15, 'expected_case_count': 10, 'outcome_unit': 'basis_points',
            'scientific_readiness': False}
        with patch.object(legacy, '_read_rows') as raw, \
                patch.object(ExactCompositionEngine, '_calculate') as evaluate:
            actual = runtime.compile_payload(original)
            raw.assert_not_called(); evaluate.assert_not_called()
        self.assertEqual(canonical(actual), canonical(expected))
        self.assertEqual(canonical(original), before)
        self.assertNotIn('primitive_steps', actual)
        self.assertNotIn('processing_complete', actual)

    def test_horizon_and_manifest_warmup_have_fixed_expected_windows(self):
        # These are predeclared dependency spans, including every complete
        # window. Neither future end rows nor boundary cases are dropped.
        for horizon, warmup, unavailable in ((1, 9, 4), (3, 7, 2), (12, 5, 0)):
            with self.subTest(horizon=horizon):
                value = supplied(); value['candidate']['horizons']['outcome_bars'] = horizon
                actual = runtime.compile_payload(value)
                self.assertEqual(actual['warmup_seconds'], warmup * D)
                self.assertEqual(actual['unavailable_warmup_seconds'], unavailable * D)
                self.assertEqual(actual['row_window'], {'start': stamp(T + 5 * D),
                    'end': stamp(T + 20 * D), 'instruments': ['SYNTHETIC']})
                self.assertEqual(actual['maximum_input_rows'], 15)
                self.assertEqual(actual['expected_case_count'], 10)
                self.assertEqual(actual['request']['horizon_bars'], horizon)
        value = supplied(); value['data_manifest']['universe']['start'] = stamp(T + 2 * D)
        actual = runtime.compile_payload(value)
        self.assertEqual(actual['row_window']['start'], stamp(T + 3 * D))
        self.assertEqual(actual['warmup_seconds'], 7 * D)
        self.assertEqual(actual['unavailable_warmup_seconds'], 0)
        self.assertEqual(actual['maximum_input_rows'], 17)

    def test_budget_changes_only_explicit_request_allowance(self):
        reference = runtime.compile_payload(supplied())
        for amount in (1, 10_000_000, 10_000_001, 20_000_000):
            with self.subTest(budget=amount):
                actual = runtime.compile_payload(supplied(amount))
                self.assertEqual(actual['request']['max_steps'], amount)
                expected = deepcopy(reference); expected['request']['max_steps'] = amount
                self.assertEqual(canonical(actual), canonical(expected))
        # Metadata compilation is not an assertion that even the one-step
        # allowance can execute this expression; there are no work counters.
        with self.assertRaises(Invalid): legacy.compile_payload(supplied())

    def test_typed_budget_rejection_precedes_legacy_projection(self):
        for amount in (None, True, False, -1, 0, 20_000_001, 20_000_000.0, '20000000'):
            with self.subTest(budget=amount), patch.object(legacy, 'compile_payload') as project:
                with self.assertRaises(Invalid): runtime.compile_payload(supplied(amount))
                project.assert_not_called()

    def test_manifest_version_unit_catalog_rejection_without_rows(self):
        changes = {
            'protected_partition': lambda value: value['data_manifest'].update(partition='assessment'),
            'outside_end': lambda value: value['data_manifest']['universe'].update(end=stamp(T + 19 * D)),
            'outside_start': lambda value: value['data_manifest']['universe'].update(start=stamp(T + 11 * D)),
            'outside_instrument': lambda value: value['data_manifest']['universe'].update(instruments=['UNUSED']),
            'unaligned_manifest': lambda value: value['data_manifest']['universe'].update(start=stamp(T + 5 * D + 1)),
            'candidate_version': lambda value: value['candidate'].update(schema='hypothesis-exec/2'),
            'ast_version': lambda value: value['candidate']['condition_ast'].update(schema='research-ast/2'),
            'wrong_unit': lambda value: value['candidate']['estimand'].update(unit='ratio'),
            'wrong_outcome_unit': lambda value: value['candidate']['outcome']['program']['expression']['left'].update(unit='ratio'),
            'wrong_catalog': lambda value: value['candidate']['outcome']['program'].update(catalog_hash='0' * 64),
            'cross_instrument': lambda value: value['candidate']['test_universe'].update(instruments=['SYNTHETIC', 'UNUSED'])}
        for label, change in changes.items():
            value = supplied(); change(value)
            with self.subTest(change=label), patch.object(legacy, '_read_rows') as raw:
                with self.assertRaises(Invalid): runtime.compile_payload(value)
                raw.assert_not_called()

    def test_fixed_row_case_and_structural_resource_bounds(self):
        for count, accepted in ((99_993, True), (99_996, False), (100_001, False)):
            value = supplied(); end = stamp(T + (10 + count) * D)
            value['candidate']['test_universe']['end'] = end
            value['data_manifest']['universe'].update(start=stamp(T + 3 * D), end=end)
            value['as_of'] = end
            with self.subTest(cases=count):
                if accepted:
                    actual = runtime.compile_payload(value)
                    self.assertEqual(actual['maximum_input_rows'], 100_000)
                    self.assertEqual(actual['expected_case_count'], 99_993)
                else:
                    with self.assertRaises(Invalid): runtime.compile_payload(value)
        for label in ('depth', 'nodes'):
            expression = boolean(True)
            if label == 'depth':
                for _ in range(33): expression = window('lag', expression, 1)
            else:
                for _ in range(8): expression = binary('and', expression, expression)
            value = supplied(); value['candidate']['condition_ast'] = program(expression)
            with self.subTest(bound=label), self.assertRaises(Invalid): runtime.compile_payload(value)


if __name__ == '__main__':
    unittest.main()
