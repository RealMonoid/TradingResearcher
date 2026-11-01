"""Independent candidate-specific composition boundaries on invented data only.

The expression tree below is an explicit analysis fixture, never a formalizer
response or registry candidate. It does not authorize production activation.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tempfile
import unittest

import paired_breakout_oracle as original
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.expressions import ExpressionGap
from trading_researcher.paired_development import PairedReferenceEngine, expected_definitions, materialize_paired, paired_contrast
from trading_researcher.paired_runtime import compile_payload, _stream
from trading_researcher.paired_breakout import composition, runtime

ERRORS = (Invalid, ExpressionGap)
EXPECTED_ORACLE_SHA256 = '97e9288a835441ea5e039619b12782972d980eec50861b7b58dfcfe02e32d7d2'
EXPECTED_SCENARIOS = 299


def fixture_payload():
    """Portable analysis-only input; exact Q1 scope, no accepted model meaning."""
    definitions = expected_definitions()
    names = [('ETHUSDT', value) for value in ('open', 'close', 'high', 'quote_volume')]
    names += [('BTCUSDT', value) for value in ('close', 'high')]
    refs = [original.ref(symbol, name) for symbol, name in names]
    catalog = {ref: {key: definitions[ref][key] for key in ('type', 'unit')} for ref in refs}
    def feature(symbol, name):
        return {'op': 'feature_at', 'instrument': symbol, 'ref': original.ref(symbol, name)}
    def literal(value, unit='ratio'):
        return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': value}
    def binary(op, left, right):
        return {'op': op, 'left': left, 'right': right}
    def lag(arg, bars):
        return {'op': 'lag', 'arg': arg, 'bars': bars}
    def mean(symbol, name):
        return lag({'op': 'trailing_mean', 'arg': feature(symbol, name), 'bars': 16}, 1)
    def combine(op, values):
        if len(values) == 1: return values[0]
        middle = len(values)//2
        return binary(op, combine(op, values[:middle]), combine(op, values[middle:]))
    clauses = [combine('and', [binary('ge', feature('ETHUSDT', 'close'),
        binary('mul', literal('1.001'), lag(feature('ETHUSDT', 'high'), k))) for k in range(1,17)]),
        binary('ge', feature('ETHUSDT', 'close'), binary('mul', literal('1.001'), feature('ETHUSDT', 'open'))),
        binary('le', feature('ETHUSDT', 'quote_volume'), binary('mul', literal('0.75'), mean('ETHUSDT', 'quote_volume'))),
        combine('or', [binary('le', feature('BTCUSDT', 'close'), lag(feature('BTCUSDT', 'high'), k)) for k in range(1,17)])]
    marker = binary('gt', combine('add', [
        binary('div', mean('ETHUSDT', 'high'), binary('add', feature('ETHUSDT', 'close'), feature('ETHUSDT', 'open'))),
        binary('div', mean('BTCUSDT', 'high'), feature('BTCUSDT', 'close')),
        binary('div', literal('1'), binary('div', mean('ETHUSDT', 'quote_volume'), feature('ETHUSDT', 'quote_volume')))
    ]), literal('0'))
    condition = lag(binary('eq', combine('and', clauses), marker), 1)
    logs = [{'op': 'ln', 'arg': binary('div', lag(feature(symbol, 'close'), 1), lag(feature(symbol, 'close'), 5))}
        for symbol in ('ETHUSDT', 'BTCUSDT')]
    outcome = binary('mul', literal('10000', 'basis_points'), binary('sub', *logs))
    program = lambda tree: {'schema': 'research-ast/3', 'catalog_hash': digest(catalog), 'expression': tree}
    candidate = {'schema': 'hypothesis-exec/2', 'idea_ref': original.IDEA_ID, 'claim_kind': 'difference',
        'test_universe': {'start': composition.START, 'end': composition.END,
            'pair': list(original.PAIR), 'data_snapshot_ref': 'SYNTHETIC_UNREGISTERED_SNAPSHOT'},
        'scope_ast': program({'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}),
        'condition_ast': program(condition), 'outcome': {'program': program(outcome), 'scale': 'quantity'},
        'comparator': {'kind': 'whole_scope'}, 'horizons': {'grid_seconds': 900, 'outcome_bars': 5},
        'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'basis_points', 'weighting': 'equal_rows',
            'missingness': 'scope-true-outcome-observed/1', 'condition_unknown': 'exclude-from-condition-retain-in-scope',
            'nuisance_fit': 'none', 'direction': 'positive'}, 'feature_refs': sorted(refs),
        'parameter_origins': []}
    return {'formalization_id': 'ANALYSIS_ONLY_NOT_A_MODEL_FORMALIZATION', 'candidate': candidate,
        'catalog': catalog, 'feature_definitions': [definitions[ref] for ref in sorted(refs)],
        'data_manifest': {'partition': 'development', 'universe': {'start': composition.START, 'end': composition.END,
            'instruments': list(original.PAIR)}}, 'as_of': composition.END, 'max_steps': 10000000}


def nodes(tree):
    yield tree
    for field in ('left', 'right', 'arg'):
        if field in tree: yield from nodes(tree[field])


def fixture_metadata(inputs=None):
    inputs = fixture_payload() if inputs is None else inputs
    def shape(tree):
        queue = [(tree, 1)]; count = depth = 0
        while queue:
            node, level = queue.pop(); count += 1; depth = max(depth, level)
            queue.extend((node[key], level+1) for key in ('arg', 'left', 'right') if key in node)
        return {'nodes': count, 'depth_levels': depth}
    return {'authority': 'ANALYSIS_FIXTURE_NOT_H_EXEC',
        'condition': shape(inputs['candidate']['condition_ast']['expression']),
        'outcome': shape(inputs['candidate']['outcome']['program']['expression']),
        'original_unique_condition_inputs': len(set(original.required(original.ORIGINAL_START+original.FOCAL_INDEX*original.STEP)))}


class BreakoutCompositionTests(unittest.TestCase):
    def test_fixture_capacity_and_exact_actual_52_read_closure(self):
        inputs = fixture_payload()
        meta = fixture_metadata(inputs)
        self.assertEqual(meta['condition'], {'nodes': 230, 'depth_levels': 12})
        self.assertEqual(meta['outcome'], {'nodes': 15, 'depth_levels': 6})
        self.assertEqual(meta['original_unique_condition_inputs'], 52)
        engine = PairedReferenceEngine(inputs['catalog'], original.synthetic(), inputs['feature_definitions'],
            pair=list(original.PAIR))
        engine.window = original.ORIGINAL_START, original.ORIGINAL_END
        when = original.ORIGINAL_START+original.FOCAL_INDEX*original.STEP
        trace = []
        self.assertIs(engine.evaluate_at(inputs['candidate']['condition_ast'], when, when, trace=trace.append).value, True)
        actual = {(item['observation_time'], item['instrument'], item['feature_ref']) for item in trace if item['feature_ref'] is not None}
        expected = {(instant, member, original.ref(member, field)) for instant, member, field in original.required(when)}
        self.assertEqual(actual, expected)
        self.assertLess(max(item[0] for item in actual), when)

    def test_fixed_oracle_and_full_scenarios_in_separate_retained_process(self):
        source = Path(original.__file__)
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), EXPECTED_ORACLE_SHA256)
        inputs = fixture_payload()
        before = deepcopy(inputs)
        with tempfile.TemporaryDirectory() as directory:
            result = runtime.run_child(runtime.read_bundle(), 'composition', inputs, directory)
        checked = result['result']
        self.assertEqual(checked['scenario_count'], EXPECTED_SCENARIOS)
        self.assertEqual(checked['checked_cases'], EXPECTED_SCENARIOS*30)
        self.assertEqual(checked['candidate_hash'], digest(inputs['candidate']))
        self.assertEqual(checked['oracle_sha256'], EXPECTED_ORACLE_SHA256)
        self.assertFalse(checked['scientific_readiness'])
        self.assertEqual(result['environment']['isolation'],
            {'isolated': 1, 'no_site': 1, 'ignore_environment': 1, 'no_bytecode_writes': 1})
        self.assertEqual(inputs, before)

    def test_changed_threshold_window_guard_member_or_outcome_never_certifies(self):
        for mutation in ('threshold', 'window15', 'window17', 'guard', 'member', 'outcome_lag',
                'outcome_sign', 'outcome_scale', 'eth_max_mean', 'btc_max_mean', 'eth_omit_extremum', 'btc_omit_extremum'):
            inputs = fixture_payload()
            tree = inputs['candidate']['condition_ast']['expression']
            if mutation == 'threshold':
                for node in nodes(tree):
                    if node.get('op') == 'literal' and node.get('value') == '0.75': node['value'] = '0.76'
            elif mutation.startswith('window'):
                for node in nodes(tree):
                    if node['op'] == 'trailing_mean': node['bars'] = int(mutation[6:])
            elif mutation == 'guard': tree['arg'] = tree['arg']['left']
            elif mutation == 'member':
                leaf = next(node for node in nodes(tree) if node['op'] == 'feature_at' and node['instrument'] == 'ETHUSDT')
                leaf['instrument'] = 'BTCUSDT'
            elif mutation == 'outcome_lag':
                for node in nodes(inputs['candidate']['outcome']['program']['expression']):
                    if node['op'] == 'lag' and node['bars'] == 5: node['bars'] = 4
            elif mutation == 'outcome_sign':
                subtraction = inputs['candidate']['outcome']['program']['expression']['right']
                subtraction['left'], subtraction['right'] = subtraction['right'], subtraction['left']
            elif mutation == 'outcome_scale':
                inputs['candidate']['outcome']['program']['expression']['left']['value'] = '1000'
            elif mutation.endswith('_max_mean'):
                member = 'ETHUSDT' if mutation.startswith('eth') else 'BTCUSDT'
                closing = {'op': 'feature_at', 'instrument': member, 'ref': original.ref(member, 'close')}
                mean = {'op': 'lag', 'bars': 1, 'arg': {'op': 'trailing_mean', 'bars': 16,
                    'arg': {'op': 'feature_at', 'instrument': member, 'ref': original.ref(member, 'high')}}}
                predicate = {'op': 'ge' if member == 'ETHUSDT' else 'le', 'left': closing, 'right': mean}
                if member == 'ETHUSDT':
                    predicate['right'] = {'op': 'mul', 'left': {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '1.001'}, 'right': mean}
                    tree['arg']['left']['left']['left'] = predicate
                else: tree['arg']['left']['right']['right'] = predicate
            else:
                eth = mutation.startswith('eth')
                branch = tree['arg']['left']['left']['left'] if eth else tree['arg']['left']['right']['right']
                target = next(node for node in nodes(branch) if node['op'] == ('ge' if eth else 'le')
                    and (node['right']['right'] if eth else node['right']).get('bars') == 16)
                target.clear(); target.update(op='literal', type='boolean', unit=None, value=eth)
            with self.subTest(mutation=mutation), self.assertRaises(ERRORS): composition.qualify(inputs)

    def test_wrong_idea_population_estimand_scope_or_resource_cannot_pass(self):
        mutations = [lambda p: p['candidate'].update(idea_ref='wrong-original'),
            lambda p: p['candidate']['test_universe'].update(end='2023-03-31T23:45:00Z'),
            lambda p: p['candidate']['comparator'].update(kind='condition_false_only'),
            lambda p: p['candidate']['estimand'].update(condition_unknown='drop_from_scope'),
            lambda p: p['candidate']['scope_ast']['expression'].update(value=False),
            lambda p: p.update(max_steps=1),
            lambda p: p['data_manifest'].update(partition='assessment')]
        for index, mutate in enumerate(mutations):
            inputs = fixture_payload(); mutate(inputs)
            with self.subTest(case=index), self.assertRaises(ERRORS): composition.qualify(inputs)

    def test_missing_changed_oracle_package_and_unbound_audit_are_denied(self):
        inputs = fixture_payload()
        for kind in ('missing', 'changed'):
            bundle = runtime.read_bundle()
            if kind == 'missing': del bundle[composition.ORACLE]
            else: bundle[composition.ORACLE] += b'\n# independently injected tamper\n'
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory, self.assertRaises(ERRORS):
                runtime.run_child(bundle, 'composition', inputs, directory)
        compiled = compile_payload(inputs)
        request = {'execution_input': {'compilation_input': inputs, 'compilation_hash': '0'*64,
            'rows': {'sha256': hashlib.sha256(b'').hexdigest(), 'size': 0}},
            'result': {'compilation_hash': digest(compiled), 'rows': {'sha256': hashlib.sha256(b'').hexdigest(), 'size': 0}}}
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ERRORS):
            runtime.run_child(runtime.read_bundle(), 'audit', request, directory)

    def test_actual_full_original_grid_audit_detects_missing_changed_and_diagnostic_results(self):
        # Empty invented canonical input tests the real full-calendar audit
        # without any market data or claim of completed positive observations.
        inputs = fixture_payload()
        report = materialize_paired(compile_payload(inputs)['request'], inputs['catalog'], [], inputs['feature_definitions'])
        self.assertTrue(report['processing_complete'])
        self.assertEqual(len(report['cases']), 8640)
        checked = composition.audit(inputs, [], report['cases'])
        self.assertEqual(checked['checked_cases'], 8640)
        self.assertEqual(checked['observed_outcomes'], 0)
        self.assertEqual(checked['candidate_hash'], digest(inputs['candidate']))
        self.assertFalse(checked['scientific_readiness'])
        # Reuse the just-materialized cases. This successful child audit tests
        # retained-file loading/binding, not independent aggregate-contrast proof.
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            (directory/'rows.jsonl').write_bytes(b'')
            with (directory/'cases.jsonl').open('wb') as stream:
                for case in report['cases']: stream.write((canonical(case)+'\n').encode())
            compiled = compile_payload(inputs)
            source = {'compilation_input': inputs, 'compilation_hash': digest(compiled),
                'rows': _stream(directory/'rows.jsonl')}
            result = {'report': {key: value for key, value in report.items() if key != 'cases'},
                'contrast': paired_contrast(report), 'case_blob': _stream(directory/'cases.jsonl'),
                'compilation_hash': source['compilation_hash'], 'rows': source['rows'], 'scientific_readiness': False}
            child = runtime.run_child(runtime.read_bundle(), 'audit', {'execution_input': source, 'result': result}, directory)
            self.assertEqual(child['result'], checked)
            self.assertEqual(child['environment']['isolation'],
                {'isolated': 1, 'no_site': 1, 'ignore_environment': 1, 'no_bytecode_writes': 1})
        with self.assertRaises(ERRORS): composition.audit(inputs, [], report['cases'][:-1])
        # Copy only the first changed case; avoid duplicating the entire large
        # trace graph merely to establish the original-field comparison gate.
        for field, value in (('condition', False), ('scope', False)):
            changed = list(report['cases']); changed[20] = {**changed[20], field: value}
            with self.subTest(field=field), self.assertRaises(ERRORS): composition.audit(inputs, [], changed)
        changed = list(report['cases'])
        changed[20] = {**changed[20], 'diagnostics': {**changed[20]['diagnostics'], 'reason_categories': []}}
        with self.assertRaises(ERRORS): composition.audit(inputs, [], changed)


if __name__ == '__main__': unittest.main()
