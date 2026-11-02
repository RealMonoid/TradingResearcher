"""Independent private-engine checks against the retained complete calculator.

Standard-library only: no NumPy, compiler, ignored runtime files or registry.
The synthetic engine clones the caller RNG and reuses the exact archived scalar
segments/queries. It defines no new sampler, scientific profile or expectation.
Full B stays 19,999, including cases crossing a sensitivity-length boundary.
"""
from copy import deepcopy
import hashlib
import importlib
import importlib.util
from pathlib import Path
import random
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import zipfile

import bootstrap_support
from test_stationary_bootstrap_adversarial import arithmetic_probe, quantity_report
from trading_researcher import family_pipeline, family_study, stationary_bootstrap as current
from trading_researcher import study_pipeline
from trading_researcher.codec import Invalid, canonical


ARCHIVE = Path(__file__).parent / 'fixtures/study-source-0f1bf36.zip'
ARCHIVE_SHA = 'ee335215005ce138a058ea3499c5424ac929003a9243e80c139ed0c18dc96e2f'
SAMPLER_SHA = '010810c61cbe9fc880aafb19a2c1b16ccedd4912ce8e7dd57e3a9e449dbae6d7'
MAXIMUM = (1 << 63) - 1


class ScalarEngine:
    def __init__(self, frozen, rng, rows):
        self.frozen = frozen
        self.rng = random.Random(0)
        self.rng.setstate(rng.getstate())
        self.columns = tuple(zip(*(tuple(row) for row in rows)))

    def draw(self, length, checker):
        sums = [0, 0, 0, 0]
        sampled = segments = 0
        checksum = hashlib.sha256()
        reason = None
        for start, count in self.frozen._segments(len(self.columns[0]) - 1, length, self.rng):
            reason = checker(True, segments)
            if reason:
                break
            segments += 1
            sampled += count
            checksum.update(struct.pack('>II', start, count))
            for field in range(4):
                sums[field] += self.frozen._segment_sum(self.columns[field], start, count)
        return {'scope_count': sums[0], 'scope_sum': sums[1],
                'condition_count': sums[2], 'condition_sum': sums[3],
                'sampled_times': sampled, 'segments': segments,
                'path_sha256': checksum.hexdigest(), 'reason': reason}


class Factory:
    def __init__(self, frozen, decline=False):
        self.frozen, self.decline = frozen, decline
        self.calls = []

    def __call__(self, rng, rows, length):
        initial = rng.getstate()
        rows = tuple(tuple(row) for row in rows)
        size = len(rows) - 1
        supported = (not self.decline and 1 <= size <= 100000 and 1 <= length <= 100000
                     and all(type(value) is int for row in rows for value in row))
        if supported:
            supported = all(size * max(abs(rows[i][field] - rows[i - 1][field])
                                       for i in range(1, size + 1)) <= MAXIMUM
                            for field in range(4))
        engine = ScalarEngine(self.frozen, rng, rows) if supported else None
        self.calls.append({'length': length, 'rows': rows, 'supported': supported,
                           'before': initial, 'after': rng.getstate()})
        assert rng.getstate() == initial
        return engine


class SinkFailure(RuntimeError):
    pass


class Control:
    def __init__(self, report, design, limits, *, stop_at=None, time_at_stop=None,
                 cancel_after_draw=False, time_after_draw=False, mutate=False,
                 fail_at=None, deadline_interval=None):
        self.report, self.design, self.limits = report, design, limits
        self.stop_at, self.time_at_stop = stop_at, time_at_stop
        self.cancel_after_draw, self.time_after_draw = cancel_after_draw, time_after_draw
        self.mutate, self.fail_at = mutate, fail_at
        self.deadline_interval = deadline_interval
        self.now = self.stops = self.intervals = 0
        self.cancelled = False
        self.trace, self.records = [], []
        self.stream = bytearray()
        self.record_hash = hashlib.sha256()
        self.failure = SinkFailure('fixed independent engine callback failure')

    def monotonic(self):
        self.trace.append(('clock', self.now))
        return self.now

    def stop(self):
        self.stops += 1
        scope = sys._getframe(1).f_locals
        used = scope['used_segments'] + scope.get('additional_segments', 0)
        self.trace.append(('stop', scope['need_segment'], used, len(self.records)))
        if self.time_at_stop == self.stops:
            self.now = 2
        if self.fail_at == ('stop', self.stops):
            raise self.failure
        return self.cancelled or self.stop_at == self.stops

    def draw(self, record):
        self.record_hash.update(canonical(record).encode() + b'\n')
        self.records.append((record['length'], record['index'], record['segments'], record['value'] is None))
        self.trace.append(('draw', record['length'], record['index'], record['segments']))
        if self.cancel_after_draw: self.cancelled = True
        if self.time_after_draw: self.now = 2
        if self.mutate:
            self.report['cases'].clear()
            self.design['randomness']['seed'] = 999
            self.limits['max_segments'] = 1
            record['value'] = 'forged callback value'
            record['path_sha256'] = 'forged callback path'
        if self.fail_at == ('draw', len(self.records)): raise self.failure

    def encoded(self, raw):
        assert type(raw) is bytes
        self.stream.extend(raw + b'\n')
        self.trace.append(('bytes', len(self.records)))
        if self.fail_at == ('bytes', len(self.records)): raise self.failure

    def interval(self, function):
        def apply(*args):
            value = function(*args)
            self.intervals += 1
            self.trace.append(('interval', self.intervals))
            if self.deadline_interval == self.intervals: self.now = 2
            return value
        return apply


def execute(calculator, *, factory_marker=False, factory=None, report_factory=arithmetic_probe,
            base=1, cap=100000000, segment_path=None, **options):
    report = report_factory()
    design = {'base_length': base, 'primary_count': 2, 'randomness': current.randomness(713)}
    limits = {'max_seconds': 1, 'max_segments': cap}
    original = deepcopy((report, design, limits))
    control = Control(report, design, limits, **options)
    extra = {'_draw_factory': factory} if factory_marker else {}
    result = error = None
    with patch.object(calculator, 'time', types.SimpleNamespace(monotonic=control.monotonic)), \
            patch.object(calculator, 'basic_interval', control.interval(calculator.basic_interval)):
        segments = (patch.object(calculator, '_segments', side_effect=lambda *args: iter(segment_path))
                    if segment_path is not None else patch.object(calculator, '_segments', calculator._segments))
        with segments:
            try:
                result = calculator.calculate(report, design, limits, stop=control.stop,
                    on_draw=control.draw, on_draw_bytes=control.encoded, **extra)
            except SinkFailure as caught:
                assert caught is control.failure
                error = (type(caught).__name__, caught.args)
    return {'result': result, 'error': error, 'trace': control.trace,
            'records': control.records, 'stream': bytes(control.stream),
            'record_sha256': control.record_hash.hexdigest(), 'intervals': control.intervals,
            'original': original, 'caller_after': (report, design, limits)}


class BootstrapDrawEngineIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == ARCHIVE_SHA
        cls.temporary = tempfile.TemporaryDirectory(prefix='trf-draw-engine-oracle-')
        cls.addClassCleanup(cls.temporary.cleanup)
        package = '_independent_frozen_draw_engine'
        destination = Path(cls.temporary.name) / package
        destination.mkdir()
        with zipfile.ZipFile(ARCHIVE) as archive:
            assert hashlib.sha256(archive.read('trading_researcher/stationary_bootstrap.py')).hexdigest() == SAMPLER_SHA
            for name in archive.namelist():
                parts = Path(name).parts
                assert len(parts) == 2 and parts[0] == 'trading_researcher' and parts[1].endswith('.py')
                (destination / parts[1]).write_bytes(archive.read(name))
        spec = importlib.util.spec_from_file_location(package, destination / '__init__.py',
                                                     submodule_search_locations=[str(destination)])
        module = importlib.util.module_from_spec(spec)
        sys.modules[package] = module

        def unload():
            for name in list(sys.modules):
                if name == package or name.startswith(package + '.'):
                    del sys.modules[name]
        cls.addClassCleanup(unload)
        spec.loader.exec_module(module)
        cls.frozen = importlib.import_module(package + '.stationary_bootstrap')
        assert cls.frozen.MAX_RESAMPLES == current.MAX_RESAMPLES == 19999

    def compare(self, *, decline=False, **options):
        expected = execute(self.frozen, **options)
        factory = Factory(self.frozen, decline)
        actual = execute(current, factory_marker=True, factory=factory, **options)
        self.assertEqual(actual, expected)
        if actual['result'] is not None:
            self.assertEqual(canonical(actual['result']).encode(), canonical(expected['result']).encode())
            self.assertIs(actual['result']['scientific_readiness'], False)
            self.assertIs(actual['result']['classification_permitted'], False)
        self.assertTrue(all(call['before'] == call['after'] for call in factory.calls))
        return actual, factory.calls

    def assert_stop(self, captured, reason):
        result = captured['result']
        self.assertIsNone(captured['error'])
        self.assertEqual((result['status'], result['reason']), ('RESOURCE_STOP', reason))
        self.assertIsNone(result['interval'])
        return result

    def assert_stream(self, captured):
        self.assertEqual(hashlib.sha256(captured['stream']).hexdigest(), captured['record_sha256'])
        self.assertEqual(captured['stream'].count(b'\n'), len(captured['records']))

    def test_engine_branch_matches_complete_frozen_partial_result_bytes_and_checkpoints(self):
        captured, calls = self.compare(cap=7)
        result = self.assert_stop(captured, 'computation_segment_limit')
        self.assertEqual([record[:3] for record in captured['records']], [(1, 0, 3), (1, 1, 3)])
        self.assertEqual(result['cases'][0]['interrupted_draw']['sampled_times'], 1)
        self.assertEqual([call['length'] for call in calls], [1])
        self.assertEqual(calls[0]['rows'], ((0, 0, 0, 0), (2, 10, 1, 0),
                                          (3, 14, 2, 4), (3, 14, 2, 4)))
        self.assertTrue(calls[0]['supported'])
        self.assertEqual([event for event in captured['trace'] if event[0] == 'stop'][-1][1:3], (True, 7))
        self.assert_stream(captured)

    def test_none_default_and_declined_engine_preserve_exact_scalar_path(self):
        expected = execute(self.frozen, cap=7)
        self.assertEqual(execute(current, cap=7), expected)
        self.assertEqual(execute(current, factory_marker=True, factory=None, cap=7), expected)
        declined, calls = self.compare(decline=True, cap=7)
        self.assertEqual(declined, expected)
        self.assertTrue(calls and all(not call['supported'] for call in calls))

    def test_factory_is_once_per_length_and_global_count_crosses_full_original_B(self):
        captured, calls = self.compare(report_factory=lambda: bootstrap_support.report(times=2), cap=39999)
        result = self.assert_stop(captured, 'computation_segment_limit')
        self.assertEqual(result['cases'][0]['attempted'], 19999)
        self.assertEqual(len([record for record in captured['records'] if record[0] == 1]), 19999)
        self.assertEqual([call['length'] for call in calls], [1, 2])
        accepted = sum(record[2] for record in captured['records'])
        partial = result['cases'][1]['interrupted_draw']
        accepted += 0 if partial is None else partial['segments']
        self.assertEqual(accepted, 39999)
        self.assert_stream(captured)

    def test_earliest_partial_postdraw_and_ordered_deadline_stops_match_frozen_owner(self):
        for checkpoint in (1, 2, 3, 4, 5):
            with self.subTest(cancel_checkpoint=checkpoint):
                captured, _ = self.compare(stop_at=checkpoint)
                self.assert_stop(captured, 'caller_cancelled')
                self.assertEqual(captured['records'], [])
        for options, reason in (({'stop_at': 1, 'time_at_stop': 1}, 'caller_cancelled'),
                                ({'time_at_stop': 2}, 'computation_time_limit'),
                                ({'cap': 1, 'time_at_stop': 5}, 'computation_time_limit'),
                                ({'cancel_after_draw': True}, 'caller_cancelled'),
                                ({'time_after_draw': True}, 'computation_time_limit'),
                                ({'cancel_after_draw': True, 'time_after_draw': True}, 'caller_cancelled')):
            with self.subTest(options=options):
                captured, _ = self.compare(**options)
                self.assert_stop(captured, reason)
                self.assert_stream(captured)

    def test_final_interval_deadline_retains_all_39998_draws_without_publication(self):
        captured, calls = self.compare(report_factory=bootstrap_support.report, deadline_interval=2)
        result = self.assert_stop(captured, 'computation_time_limit')
        self.assertEqual(captured['intervals'], 2)
        self.assertEqual([case['attempted'] for case in result['cases']], [19999, 19999])
        self.assertEqual(len(captured['records']), 39998)
        self.assertEqual([call['length'] for call in calls], [1, 2])
        self.assertIsNone(result['cases'][-1]['interval'])
        self.assert_stream(captured)

    def test_callbacks_propagate_exceptions_and_mutation_cannot_change_detached_bytes(self):
        for failure in (('stop', 1), ('stop', 5), ('draw', 1), ('bytes', 1)):
            with self.subTest(failure=failure):
                captured, _ = self.compare(fail_at=failure)
                self.assertIsNone(captured['result'])
                self.assertEqual(captured['error'],
                                 ('SinkFailure', ('fixed independent engine callback failure',)))
        pristine, _ = self.compare(cap=3)
        changed, _ = self.compare(cap=3, mutate=True)
        for key in ('result', 'trace', 'records', 'stream', 'record_sha256'):
            self.assertEqual(changed[key], pristine[key])
        self.assertEqual(changed['caller_after'][0]['cases'], [])
        self.assertEqual(changed['result']['design'], changed['original'][1])
        self.assertEqual(changed['result']['limits'], changed['original'][2])
        self.assert_stream(changed)

    def test_fraction_and_large_integer_fallback_preserve_rng_and_original_guards(self):
        def fractional():
            return quantity_report([['0'], ['1'], ['-1'], ['0']], [[True]] * 4,
                                   [[True], [True], [True], [False]], divisor=3)
        captured, calls = self.compare(report_factory=fractional, cap=5)
        self.assert_stop(captured, 'computation_segment_limit')
        self.assertTrue(calls and all(not call['supported'] for call in calls))
        self.assert_stream(captured)

        def literal(value): return {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': str(value)}
        def product(nodes):
            if len(nodes) == 1: return nodes[0]
            middle = len(nodes) // 2
            return {'op': 'mul', 'left': product(nodes[:middle]), 'right': product(nodes[middle:])}
        huge = product([literal(2**300)] * 27 + [literal(2**91)])

        def huge_integer():
            return quantity_report([['0'], ['1'], ['-1'], ['0']], [[True]] * 4,
                                   [[True], [True], [True], [False]],
                                   divisor={'op': 'div', 'left': literal(1), 'right': huge})
        captured, calls = self.compare(report_factory=huge_integer, cap=4,
                                       segment_path=[(0, 1), (2, 1), (2, 1), (2, 1)])
        self.assert_stop(captured, 'computation_segment_limit')
        self.assertTrue(calls and all(not call['supported'] for call in calls))
        self.assertTrue(any(type(row[1]) is int and row[1].bit_length() == 8192
                            for call in calls for row in call['rows']))
        self.assert_stream(captured)
        denominator = {'op': 'add', 'left': huge,
                       'right': literal(1)}

        def huge_denominator():
            return quantity_report([['0'], ['1'], ['-1'], ['0']], [[True]] * 4,
                                   [[True], [True], [True], [False]], divisor=denominator)
        captured, calls = self.compare(report_factory=huge_denominator, cap=4,
                                       segment_path=[(0, 1), (2, 1), (2, 1), (2, 1)])
        self.assert_stop(captured, 'exact_arithmetic_exceeds_numeric_envelope')
        self.assertEqual(captured['records'], [])
        self.assertTrue(calls and all(not call['supported'] for call in calls))

    def test_allowed_large_sensitivity_length_declines_without_new_generic_cap(self):
        captured, calls = self.compare(base=300000, cap=1)
        self.assert_stop(captured, 'computation_segment_limit')
        self.assertEqual(captured['result']['required_lengths'], [150000, 300000, 600000])
        self.assertEqual([call['length'] for call in calls], [150000])
        self.assertIs(calls[0]['supported'], False)
        self.assertEqual(calls[0]['before'], calls[0]['after'])
        self.assert_stream(captured)

    def test_noncallable_factory_is_rejected_as_input_not_an_empirical_result(self):
        for factory in (True, 1, 'native', object()):
            with self.subTest(factory_type=type(factory).__name__), self.assertRaises(Invalid):
                current.calculate(arithmetic_probe(),
                    {'base_length': 1, 'primary_count': 2, 'randomness': current.randomness(713)},
                    {'max_seconds': 1, 'max_segments': 1}, _draw_factory=factory)

    def test_direct_world_and_family_callers_forward_only_explicit_optional_factory(self):
        marker = lambda rng, rows, length: None
        model = {'status': 'MODEL_SPECIFIED'}
        zero = {'numerator': '0', 'denominator': '1'}
        raw_report = arithmetic_probe()
        payload = {'report': {key: value for key, value in raw_report.items() if key != 'cases'},
                   'diagnostics': {}}
        manifest = {'schema': 'information-study-manifest/1', 'effects': [zero],
                    'profile': {'specifications': [{}], 'budget': {'attempt_compute_ms': 1000}},
                    'assigned': {'base_length': 1, 'primary_count': 1}, 'mc_policy': {}}
        world = {'id': 'synthetic-forwarding-only', 'spec_index': 0, 'scenario': 0,
                 'time_rows': 3, 'population_seed': 11, 'bootstrap_seed': 22}

        def bootstrap(*args, **kwargs):
            return {'status': 'INPUT_GAP', 'reason': 'no_scope_cases',
                    'descriptive': {'scope_count': 0, 'condition_count': 0}}
        for factory in (None, marker):
            with self.subTest(factory='default' if factory is None else 'explicit'):
                extra = {} if factory is None else {'_draw_factory': factory}
                with patch.object(study_pipeline, 'build_model', return_value=model), \
                        patch.object(study_pipeline, 'generate_world', side_effect=lambda *args:
                                     {'report': deepcopy(raw_report), 'truth': {'effect': zero}}), \
                        patch.object(study_pipeline, 'calculate', side_effect=bootstrap) as calculate:
                    study_pipeline.calculate_world(payload, manifest, world, raw_report['cases'], lambda row: None, **extra)
                self.assertIs(calculate.call_args.kwargs.get('_draw_factory'), factory)

                family_payload = {**payload, 'effects': [zero], 'specification': {},
                    'components': [{'id': 'a', 'scenario': 0}, {'id': 'b', 'scenario': 0}],
                    'time_rows': 3, 'seed': 11, 'bootstrap_seed': 22, 'limits': {'max_seconds': 1},
                    'design': {'base_length': 1, 'primary_count': 2,
                               'mc_policy': {'delta': zero, 'direction': 'positive'}}}
                with patch.object(family_pipeline, 'build_model', return_value=model), \
                        patch.object(family_pipeline, 'generate_family', side_effect=lambda *args: {
                            'components': [{'id': name, 'report': deepcopy(raw_report)} for name in ('a', 'b')]}), \
                        patch.object(family_pipeline, 'family_events', return_value={'synthetic_forwarding_only': True}), \
                        patch.object(family_pipeline, 'calculate', side_effect=bootstrap) as calculate:
                    family_pipeline.calculate_family(family_payload, raw_report['cases'], lambda row: None, **extra)
                self.assertEqual(calculate.call_count, 2)
                self.assertTrue(all(call.kwargs.get('_draw_factory') is factory for call in calculate.call_args_list))

                family_manifest = {**manifest, 'schema': 'family-information-study-manifest/1'}
                with patch.object(family_study, 'components', return_value=[]), \
                        patch.object(family_study, 'outcome_record', return_value={'state': 'INFORMATION_GAP'}), \
                        patch.object(family_pipeline, 'calculate_family', return_value={'outcomes': []}) as family:
                    study_pipeline.calculate_world(payload, family_manifest, world, raw_report['cases'], lambda row: None, **extra)
                self.assertIs(family.call_args.kwargs.get('_draw_factory'), factory)


if __name__ == '__main__':
    unittest.main()
