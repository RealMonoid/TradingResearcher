"""Independent synthetic expectations for the retained exact runtime.

Real isolated local subprocesses and owned temporary files only. This suite
does not enroll workers, use registries/providers, authenticate real source
artifacts, or qualify an actual research hypothesis or funded native flow.
"""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest

from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.exact_runtime import (
    PROFILE, FILES, MAX_STREAM, read_bundle, compile_payload, run_child, _stream,
)


D = 900
T = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp())
CATALOG = {'x@1': {'type': 'real', 'unit': 'ratio'}}
COMPILE_FIELDS = {'schema', 'request', 'candidate_hash', 'programs', 'feature_refs',
                  'row_window', 'warmup_seconds', 'unavailable_warmup_seconds',
                  'maximum_input_rows', 'expected_case_count', 'outcome_unit', 'scientific_readiness'}
RESULT_FIELDS = {'report', 'contrast', 'case_blob', 'rows', 'compilation_hash', 'scientific_readiness'}


def utc(when):
    return datetime.fromtimestamp(when, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def literal(value, unit='ratio'):
    return {'op': 'literal', 'type': 'real', 'unit': unit, 'value': str(value)}


def window(op, arg, bars):
    return {'op': op, 'arg': arg, 'bars': bars}


def program(expression):
    return {'schema': 'research-ast/4', 'catalog_hash': digest(CATALOG), 'expression': expression}


def payload():
    x = {'op': 'feature', 'ref': 'x@1'}
    positive_square = {'op': 'gt', 'left': {'op': 'integer_power', 'exponent': 2,
                                          'arg': window('lag', x, 1)}, 'right': literal(0)}
    condition = window('lag', window('trailing_all', positive_square, 3), 1)
    outcome = {'op': 'mul', 'left': literal(1, 'basis_points'),
               'right': window('lag', window('trailing_product', window('lag', x, 1), 3), 1)}
    candidate = {'schema': 'hypothesis-exec/3', 'idea_ref': 'synthetic-original', 'claim_kind': 'difference',
        'scope_ast': program({'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}),
        'condition_ast': program(condition), 'outcome': {'program': program(outcome), 'scale': 'quantity'},
        'comparator': {'kind': 'whole_scope'}, 'horizons': {'grid_seconds': 900, 'outcome_bars': 4},
        'test_universe': {'instruments': ['SYNTHETIC'], 'start': utc(T + 10 * D),
                          'end': utc(T + 16 * D), 'data_snapshot_ref': 'synthetic-snapshot'},
        'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'basis_points', 'weighting': 'equal_rows',
            'missingness': 'scope-true-outcome-observed/1',
            'condition_unknown': 'exclude-from-condition-retain-in-scope', 'nuisance_fit': 'none', 'direction': 'positive'},
        'feature_refs': ['x@1'], 'parameter_origins': []}
    def inventory(node, path):
        if node['op'] == 'literal':
            yield path + '/value'
        if node['op'] in ('lag', 'trailing_all', 'trailing_product'):
            yield path + '/bars'
        if node['op'] == 'integer_power':
            yield path + '/exponent'
        for key in ('arg', 'left', 'right'):
            if key in node:
                yield from inventory(node[key], path + '/' + key)
    paths = ['/horizons/outcome_bars']
    for prefix, expression in (('/scope_ast/expression', candidate['scope_ast']['expression']),
                               ('/condition_ast/expression', condition),
                               ('/outcome/program/expression', outcome)):
        paths.extend(inventory(expression, prefix))
    candidate['parameter_origins'] = [{'path': path, 'basis': 'preexisting_specification', 'source_refs': [],
                                     'rationale': 'Fixed invented engineering expectation.'} for path in paths]
    return {'formalization_id': 'synthetic-exact-formalization', 'candidate': candidate, 'catalog': deepcopy(CATALOG),
        'data_manifest': {'partition': 'development', 'universe': {
            'start': utc(T), 'end': utc(T + 20 * D), 'instruments': ['OTHER', 'SYNTHETIC']}},
        'as_of': utc(T + 16 * D), 'max_steps': 100_000}


def rows():
    return [{'time': T + i * D, 'instrument': 'SYNTHETIC',
             'features': {'x@1': {'value': str(i + 1), 'available_at': T + i * D}}}
            for i in range(6, 16)]


def stream_bytes(items):
    return b''.join((canonical(item) + '\n').encode('utf-8') for item in items)


def bound(value):
    return tuple(Fraction(int(value[side]['numerator']), int(value[side]['denominator'])) for side in ('lower', 'upper'))


class ExactRuntimeReview(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.bundle = read_bundle()

    def fresh(self, name):
        directory = self.root / name
        directory.mkdir()
        return directory

    def assert_envelope(self, envelope, mode, value):
        self.assertEqual(set(envelope), {'mode', 'request_hash', 'footprint', 'result', 'environment'})
        self.assertEqual(envelope['mode'], mode)
        self.assertEqual(envelope['request_hash'], digest(value))
        self.assertEqual(envelope['footprint'], {name: hashlib.sha256(raw).hexdigest() for name, raw in self.bundle.items()})
        self.assertEqual(envelope['environment']['isolation'], {
            'isolated': 1, 'no_site': 1, 'ignore_environment': 1, 'no_bytecode_writes': 1})
        self.assertTrue(envelope['environment']['standard_library'])

    def execute(self, name='execute', inputs=None, data=None):
        inputs = payload() if inputs is None else inputs
        directory = self.fresh(name)
        (directory / 'rows.jsonl').write_bytes(stream_bytes(rows() if data is None else data))
        execution = {'compilation_input': inputs, 'compilation_hash': digest(compile_payload(inputs)),
                     'rows': _stream(directory / 'rows.jsonl')}
        result = run_child(self.bundle, 'execute', execution, directory)
        self.assert_envelope(result, 'execute', execution)
        return execution, result['result'], directory

    def replay_directory(self, source, name):
        directory = self.fresh(name)
        for filename in ('rows.jsonl', 'cases.jsonl'):
            shutil.copyfile(source / filename, directory / filename)
        return directory

    def test_compile_new_window_spans_and_exact_mature_metadata(self):
        inputs = payload()
        before = canonical(inputs)
        result = compile_payload(inputs)
        self.assertEqual(set(result), COMPILE_FIELDS)
        self.assertEqual(result['schema'], 'exact-compilation/1')
        self.assertEqual(result['candidate_hash'], digest(inputs['candidate']))
        self.assertEqual(result['request']['schema'], 'exact-composition-case-request/1')
        self.assertEqual(result['request']['candidate_ref'], inputs['formalization_id'])
        self.assertEqual(result['row_window'], {'start': utc(T + 6 * D), 'end': utc(T + 16 * D), 'instruments': ['SYNTHETIC']})
        self.assertEqual(result['warmup_seconds'], 4 * D)
        self.assertEqual(result['unavailable_warmup_seconds'], 0)
        self.assertEqual(result['maximum_input_rows'], 10)
        self.assertEqual(result['expected_case_count'], 6)
        self.assertEqual(result['feature_refs'], ['x@1'])
        self.assertEqual(result['outcome_unit'], 'basis_points')
        self.assertFalse(result['scientific_readiness'])
        self.assertEqual(canonical(inputs), before)
        # Make the product's outcome span6bars exceed h1 by5bars, beyond the
        # condition's four-bar all-window span. No expression is evaluated here.
        inputs['candidate']['outcome']['program']['expression']['right']['bars'] = 3
        inputs['candidate']['horizons']['outcome_bars'] = 1
        inputs['data_manifest']['universe']['start'] = utc(T + 8 * D)
        result = compile_payload(inputs)
        self.assertEqual(result['warmup_seconds'], 5 * D)
        self.assertEqual(result['unavailable_warmup_seconds'], 3 * D)
        self.assertEqual(result['row_window']['start'], utc(T + 8 * D))
        self.assertEqual(result['maximum_input_rows'], 8)

    def test_compile_in_actual_retained_isolated_child_matches_local(self):
        inputs = payload()
        actual = run_child(self.bundle, 'compile', inputs, self.fresh('compile'))
        self.assert_envelope(actual, 'compile', inputs)
        self.assertEqual(actual['result'], compile_payload(inputs))

    def test_protected_outside_manifest_version_unit_and_catalog_changes_reject(self):
        mutations = [
            lambda p: p['data_manifest'].update(partition='assessment'),
            lambda p: p['data_manifest'].update(partition='operations'),
            lambda p: p['data_manifest']['universe'].update(start=utc(T + 11 * D)),
            lambda p: p['data_manifest']['universe'].update(end=utc(T + 15 * D)),
            lambda p: p['data_manifest']['universe'].update(instruments=['OTHER']),
            lambda p: p['candidate'].update(schema='hypothesis-exec/1'),
            lambda p: p['candidate']['scope_ast'].update(schema='research-ast/2'),
            lambda p: p['candidate']['test_universe'].update(instruments=['SYNTHETIC', 'OTHER']),
            lambda p: p['candidate']['outcome'].update(scale='binary_probability'),
            lambda p: p['candidate']['estimand'].update(unit='ratio'),
            lambda p: p['candidate']['condition_ast'].update(catalog_hash='0' * 64),
            lambda p: p.update(max_steps=10_000_001),
            lambda p: p.update(extra='not in the interface'),
        ]
        for index, mutate in enumerate(mutations):
            altered = payload()
            mutate(altered)
            with self.subTest(mutation=index), self.assertRaises(Invalid):
                compile_payload(altered)

    def test_execute_has_complete_diagnostic_stream_and_exact_descriptive_means(self):
        execution, result, directory = self.execute()
        self.assertEqual(set(result), RESULT_FIELDS)
        self.assertNotIn('cases', result['report'])
        self.assertEqual(result['rows'], execution['rows'])
        self.assertEqual(result['compilation_hash'], execution['compilation_hash'])
        self.assertFalse(result['scientific_readiness'])
        report = result['report']
        self.assertEqual(report['schema'], 'diagnostic-exact-composition-cases/1')
        self.assertTrue(report['processing_complete'])
        self.assertEqual(report['diagnostics']['status'], 'COMPLETE')
        self.assertLessEqual(report['primitive_steps'] + report['diagnostics']['primitive_steps'], payload()['max_steps'])
        cases = [decode(line) for line in (directory / 'cases.jsonl').read_bytes().splitlines()]
        self.assertEqual(len(cases), 6)
        self.assertEqual([case['status'] for case in cases], ['ELIGIBLE'] * 2 + ['PARTITION_BOUNDARY'] * 4)
        self.assertEqual([bound(case['outcome']) for case in cases[:2]], [(1716, 1716), (2184, 2184)])
        self.assertTrue(all(isinstance(case['diagnostics'], dict) for case in cases))
        self.assertEqual(bound(result['contrast']['scope_mean']), (1950, 1950))
        self.assertEqual(bound(result['contrast']['effect']), (0, 0))
        self.assertEqual(result['case_blob'], _stream(directory / 'cases.jsonl'))

    def test_fresh_replay_binds_exact_bytes_compilation_and_result(self):
        execution, result, directory = self.execute()
        target = self.replay_directory(directory, 'verify')
        self.assertNotEqual(target, directory)
        inputs = {'execution_input': execution, 'result': result}
        verified = run_child(self.bundle, 'verify', inputs, target)
        self.assert_envelope(verified, 'verify', inputs)
        value = verified['result']
        self.assertEqual(set(value), {'schema', 'result_hash', 'compilation_hash', 'case_blob', 'checked_cases', 'scientific_readiness'})
        self.assertEqual(value['schema'], 'exact-case-verification/1')
        self.assertEqual(value['result_hash'], digest(result))
        self.assertEqual(value['compilation_hash'], execution['compilation_hash'])
        self.assertEqual(value['case_blob'], result['case_blob'])
        self.assertEqual(value['checked_cases'], 6)
        self.assertFalse(value['scientific_readiness'])

    def test_replay_rejects_changed_case_or_suffix_even_with_rebound_blob_hash(self):
        execution, result, directory = self.execute()
        for variant in ('reason', 'suffix', 'truncate'):
            target = self.replay_directory(directory, variant)
            path = target / 'cases.jsonl'
            if variant == 'reason':
                cases = [decode(line) for line in path.read_bytes().splitlines()]
                cases[0]['reason'] = 'different retained result'
                path.write_bytes(stream_bytes(cases))
            elif variant == 'suffix':
                path.write_bytes(path.read_bytes() + b'{}\n')
            else:
                path.write_bytes(path.read_bytes()[:-1])
            altered = deepcopy(result)
            altered['case_blob'] = _stream(path)
            with self.subTest(variant=variant), self.assertRaises(Invalid):
                run_child(self.bundle, 'verify', {'execution_input': execution, 'result': altered}, target)

    def test_replay_rejects_result_metadata_or_raw_row_change(self):
        execution, result, directory = self.execute()
        target = self.replay_directory(directory, 'metadata')
        altered = deepcopy(result)
        altered['contrast']['effect']['upper']['numerator'] = '1'
        with self.assertRaises(Invalid):
            run_child(self.bundle, 'verify', {'execution_input': execution, 'result': altered}, target)
        target = self.replay_directory(directory, 'raw-row')
        (target / 'rows.jsonl').write_bytes((target / 'rows.jsonl').read_bytes() + b'\n')
        with self.assertRaises(Invalid):
            run_child(self.bundle, 'verify', {'execution_input': execution, 'result': result}, target)

    def test_matching_hash_does_not_authorize_rows_outside_compiled_selection(self):
        for variant in ('before', 'after', 'instrument'):
            data = rows()
            if variant == 'before':
                data[0]['time'] -= D
                data[0]['features']['x@1']['available_at'] -= D
            elif variant == 'after':
                data[-1]['time'] = T + 16 * D
            else:
                data[0]['instrument'] = 'OTHER'
            target = self.fresh('rows-' + variant)
            (target / 'rows.jsonl').write_bytes(stream_bytes(data))
            inputs = payload()
            execution = {'compilation_input': inputs, 'compilation_hash': digest(compile_payload(inputs)),
                         'rows': _stream(target / 'rows.jsonl')}
            with self.subTest(variant=variant), self.assertRaises(Invalid):
                run_child(self.bundle, 'execute', execution, target)

    def test_wrong_compilation_hash_or_changed_raw_bytes_fail(self):
        for variant in ('compilation', 'rows'):
            target = self.fresh(variant)
            (target / 'rows.jsonl').write_bytes(stream_bytes(rows()))
            inputs = payload()
            execution = {'compilation_input': inputs, 'compilation_hash': digest(compile_payload(inputs)),
                         'rows': _stream(target / 'rows.jsonl')}
            if variant == 'compilation':
                execution['compilation_hash'] = '0' * 64
            else:
                execution['rows']['sha256'] = '0' * 64
            with self.subTest(variant=variant), self.assertRaises(Invalid):
                run_child(self.bundle, 'execute', execution, target)

    def test_resource_stop_keeps_only_completed_numerical_prefix_and_no_effect(self):
        _, full, full_dir = self.execute('full')
        inputs = payload()
        inputs['max_steps'] = 60
        _, stopped, stopped_dir = self.execute('stopped', inputs)
        self.assertEqual(stopped['report']['status'], 'RESOURCE_STOP')
        self.assertFalse(stopped['report']['processing_complete'])
        self.assertEqual(stopped['report']['processed_case_count'], 1)
        self.assertEqual(stopped['report']['primitive_steps'], 60)
        self.assertEqual(stopped['report']['diagnostics']['status'], 'RESOURCE_STOP')
        self.assertEqual(stopped['report']['diagnostics']['primitive_steps'], 0)
        self.assertEqual(stopped['contrast']['status'], 'RESOURCE_STOP')
        self.assertIsNone(stopped['contrast']['effect'])
        first = decode((full_dir / 'cases.jsonl').read_bytes().splitlines()[0])
        prefix = decode((stopped_dir / 'cases.jsonl').read_bytes().splitlines()[0])
        self.assertEqual({k: v for k, v in prefix.items() if k != 'diagnostics'},
                         {k: v for k, v in first.items() if k != 'diagnostics'})
        self.assertIsNone(prefix['diagnostics'])
        self.assertFalse(full['scientific_readiness'])

    def test_fixed_bundle_time_bounds_and_stream_byte_identity(self):
        self.assertIsInstance(FILES, tuple)
        self.assertEqual(len(FILES), len(set(FILES)))
        self.assertEqual(set(self.bundle), set(FILES))
        self.assertNotIn('tests/test_exact_runtime_review.py', FILES)
        self.assertEqual(PROFILE, 'exact-reference-computation/1')
        self.assertEqual(MAX_STREAM, 512 * 1024 * 1024)
        path = self.root / 'bytes.jsonl'
        path.write_bytes(b'{"synthetic":true}\n')
        self.assertEqual(_stream(path), {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'size': len(path.read_bytes())})
        for timeout in (0, -1, True, 1801):
            with self.subTest(timeout=timeout), self.assertRaises(Invalid):
                run_child(self.bundle, 'compile', payload(), self.fresh('timeout-' + str(timeout)), timeout=timeout)
        for name, altered in (('missing', {key: value for key, value in self.bundle.items() if key != FILES[0]}),
                              ('extra', {**self.bundle, '../outside.py': b'not executable'})):
            with self.subTest(bundle=name), self.assertRaises(Invalid):
                run_child(altered, 'compile', payload(), self.fresh(name))

    def test_certify_runs_only_fixed_retained_core_and_case_methods(self):
        inputs = {'profile': PROFILE}
        result = run_child(self.bundle, 'certify', inputs, self.fresh('certify'))
        self.assert_envelope(result, 'certify', inputs)
        self.assertEqual(result['result']['profile'], PROFILE)
        self.assertEqual(result['result']['tests'], 51)
        self.assertEqual(result['result']['failures'], 0)
        self.assertEqual(result['result']['errors'], 0)
        self.assertEqual(result['result']['skipped'], 0)
        self.assertFalse(result['result']['scientific_readiness'])


if __name__ == '__main__':
    unittest.main()
