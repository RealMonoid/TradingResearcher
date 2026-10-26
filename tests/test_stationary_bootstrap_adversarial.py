"""Independent stationary-sampler probes; no inference/calibration certificate."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import unittest
from unittest.mock import patch

import bootstrap_support
from trading_researcher import stationary_bootstrap as bootstrap
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.outcomes import materialize_reference, reference_contrast


def quantity_report(values, conditions, scopes, divisor=None):
    """Materialize hand-defined source rows rather than inventing maturity flags."""
    instruments = ['A', 'B'][:len(values[0])]
    catalog = {'scope@1': {'type': 'boolean', 'unit': None},
               'condition@1': {'type': 'boolean', 'unit': None},
               'value@1': {'type': 'real', 'unit': 'ratio'}}
    def program(expression):
        return {'schema': 'research-ast/1', 'catalog_hash': digest(catalog), 'expression': expression}
    def instant(seconds):
        return datetime.fromtimestamp(seconds, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    outcome = {'op': 'feature', 'ref': 'value@1'}
    if divisor is not None:
        outcome = {'op': 'div', 'left': outcome,
                   'right': deepcopy(divisor) if type(divisor) is dict else
                   {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': str(divisor)}}
    request = {'schema': 'reference-case-request/1', 'candidate_ref': 'independent-bootstrap-numeric',
        'data_snapshot_ref': 'independent-synthetic-rows',
        'scope_program': program({'op': 'feature', 'ref': 'scope@1'}),
        'condition_program': program({'op': 'feature', 'ref': 'condition@1'}),
        'outcome_program': program(outcome), 'outcome_scale': 'quantity', 'horizon_bars': 1,
        'universe': {'start': instant(0), 'end': instant(len(values)*900), 'instruments': instruments},
        'as_of': instant(len(values)*900), 'max_steps': 100000}
    rows = []
    for i in range(len(values)):
        for j, instrument in enumerate(instruments):
            rows.append({'time': i*900, 'instrument': instrument, 'features': {
                ref: {'value': value, 'available_at': i*900} for ref, value in (
                    ('scope@1', scopes[i][j]), ('condition@1', conditions[i][j]),
                    ('value@1', values[i][j]))}})
    return materialize_reference(request, catalog, rows)


def arithmetic_probe():
    # Eligible buckets: t0 => (0,true),(10,unknown); t1 => (4,true).
    # t2 is a declared scope-false bucket, retained on the sampling time axis.
    return quantity_report([['0', '0'], ['0', '10'], ['4', None]],
                           [[True, None], [True, False], [True, True]],
                           [[True, True], [True, True], [False, False]])


class StationaryBootstrapAdversarialTests(unittest.TestCase):
    def design(self, base=1, seed=713):
        return {'base_length': base, 'primary_count': 2, 'randomness': bootstrap.randomness(seed)}

    def limits(self, **changes):
        return {'max_seconds': 60, 'max_segments': 2000000, **changes}

    def test_hand_contrast_preserves_row_weight_and_unknown_condition_baseline(self):
        source = arithmetic_probe()
        self.assertEqual(reference_contrast(source)['effect'], {'numerator': '-8', 'denominator': '3'})
        prefixes = bootstrap._prefixes(source)
        self.assertEqual(prefixes[0], [0, 2, 3, 3])
        self.assertEqual(prefixes[1], [0, 10, 14, 14])
        self.assertEqual(prefixes[2], [0, 1, 2, 2])
        self.assertEqual(prefixes[3], [0, 0, 4, 4])
        for indices, expected in (([0, 0], Fraction(-5)), ([1, 1], Fraction(0)),
                                  ([0, 1, 2], Fraction(-8, 3))):
            n, total, nc, conditional = [sum(bootstrap._segment_sum(p, i, 1) for i in indices)
                                          for p in prefixes]
            self.assertEqual(Fraction(conditional,nc)-Fraction(total,n), expected)

    def test_single_index_stream_keeps_joint_instruments_and_empty_grid_slots(self):
        class Fixed:
            def __init__(self, seed): pass
            def randrange(self, size): return 0
            def random(self): return 0
        records = []
        with patch.object(bootstrap.random, 'Random', Fixed):
            result = bootstrap.calculate(arithmetic_probe(), self.design(), self.limits(max_segments=3), on_draw=records.append)
        self.assertEqual(result['time_rows'], 3)
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['scope_count'], 6)  # Both t0 instruments, three times.
        self.assertEqual(records[0]['condition_count'], 3)
        self.assertEqual(records[0]['value'], {'numerator': '-5', 'denominator': '1'})

    def test_mean_one_never_uses_geometric_float_and_large_block_is_clipped_before_wrap(self):
        class Fixed:
            def randrange(self, size): return size-1
            def random(self): raise AssertionError('L=1 must use its exact one-row specialization')
        self.assertEqual(list(bootstrap._segments(3, 1, Fixed())), [(2, 1)]*3)
        class Long(Fixed):
            def random(self): return 1-2.0**-53
        self.assertEqual(list(bootstrap._segments(3, 1000, Long())), [(2, 3)])
        self.assertEqual(bootstrap._segment_sum([0, 2, 7, 18], 2, 3), 18)

    def test_complete_report_metadata_and_case_order_cannot_be_overridden(self):
        source = arithmetic_probe()
        variants = []
        changed = deepcopy(source); changed['processing_complete'] = False; variants.append(changed)
        changed = deepcopy(source); changed['cases'][0], changed['cases'][1] = changed['cases'][1], changed['cases'][0]; variants.append(changed)
        changed = deepcopy(source); changed['cases'][1]['instrument'] = 'A'; variants.append(changed)
        changed = deepcopy(source); changed['state_counts']['ELIGIBLE'] += 1; variants.append(changed)
        changed = deepcopy(source); changed['cases'][0]['outcome'] = {'numerator': '0', 'denominator': '2'}; variants.append(changed)
        for index, variant in enumerate(variants):
            with self.subTest(index=index), self.assertRaises(Invalid):
                bootstrap.calculate(variant, self.design(), self.limits())

    def test_boolean_state_counts_are_not_integer_metadata(self):
        source = quantity_report([['0'], ['1']], [[True], [True]], [[True], [True]])
        self.assertEqual(source['state_counts']['ELIGIBLE'], 1)
        self.assertEqual(source['state_counts']['PARTITION_BOUNDARY'], 1)
        source['state_counts']['ELIGIBLE'] = True
        source['state_counts']['PARTITION_BOUNDARY'] = True
        with self.assertRaises(Invalid):
            bootstrap.calculate(source, self.design(), self.limits(max_segments=1))

    def test_undefined_ordinals_are_retained_and_stream_replays_without_replacement(self):
        records = []
        source = bootstrap_support.report(times=4, rare=True)
        result = bootstrap.calculate(source, self.design(), self.limits(), on_draw=records.append)
        replay = bootstrap.calculate(source, self.design(), self.limits())
        self.assertEqual(result, replay)
        self.assertEqual(result['required_lengths'], [1, 2])
        self.assertEqual(result['status'], 'INFORMATION_GAP')
        self.assertIsNone(result['interval'])
        self.assertEqual(len(records), 19999*2)
        self.assertTrue(any(record['value'] is None for record in records))
        for current in result['cases']:
            stream = [record for record in records if record['length'] == current['length']]
            self.assertEqual([record['index'] for record in stream], list(range(19999)))
            self.assertEqual(current['attempted'], current['defined']+current['undefined'])
            self.assertEqual(current['attempted'], 19999)
            self.assertEqual(current['replicate_sha256'], hashlib.sha256(
                ''.join(canonical(record)+'\n' for record in stream).encode()).hexdigest())
        self.assertIs(result['classification_permitted'], False)
        self.assertIs(result['scientific_readiness'], False)

    def test_partial_draw_and_preexisting_cancellation_do_not_become_undefined_replicates(self):
        records = []
        result = bootstrap.calculate(arithmetic_probe(), self.design(), self.limits(max_segments=1), on_draw=records.append)
        self.assertEqual(records, [])
        current = result['cases'][0]
        self.assertEqual((current['attempted'], current['defined'], current['undefined'], current['interrupted']), (1, 0, 0, 1))
        self.assertEqual(current['interrupted_draw']['index'], 0)
        self.assertEqual(current['interrupted_draw']['sampled_times'], 1)
        self.assertIsNone(result['interval'])
        stopped = bootstrap.calculate(arithmetic_probe(), self.design(), self.limits(), stop=lambda: True)
        self.assertEqual(stopped['status'], 'RESOURCE_STOP')
        self.assertEqual(stopped['reason'], 'caller_cancelled')
        self.assertEqual(sum(c['attempted'] for c in stopped['cases']), 0)

    def test_final_draw_cancellation_is_checked_before_interval_publication(self):
        stopped = [False]
        def record(draw):
            if draw['length'] == 2 and draw['index'] == 19998:
                stopped[0] = True
        result = bootstrap.calculate(bootstrap_support.report(), self.design(), self.limits(),
            stop=lambda: stopped[0], on_draw=record)
        self.assertTrue(stopped[0])
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertEqual(result['reason'], 'caller_cancelled')
        self.assertIsNone(result['interval'])

    def test_deadline_crossed_in_final_interval_cannot_return_completed_result(self):
        clock = [0]
        intervals = [0]
        original = bootstrap.basic_interval
        def interval(*args):
            value = original(*args)
            intervals[0] += 1
            if intervals[0] == 2:
                clock[0] = 2
            return value
        with patch.object(bootstrap.time, 'monotonic', side_effect=lambda: clock[0]), \
                patch.object(bootstrap, 'basic_interval', side_effect=interval):
            result = bootstrap.calculate(bootstrap_support.report(), self.design(), self.limits(max_seconds=1))
        self.assertEqual(intervals[0], 2)
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertEqual(result['reason'], 'computation_time_limit')
        self.assertIsNone(result['interval'])

    def test_equal_oversized_means_cannot_hide_numeric_envelope_failure(self):
        def literal(value):
            return {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': str(value)}
        def product(nodes):
            if len(nodes) == 1:
                return nodes[0]
            middle = len(nodes)//2
            return {'op': 'mul', 'left': product(nodes[:middle]), 'right': product(nodes[middle:])}
        # p=2**8191+1 is an 8192-bit odd denominator. Every input literal
        # remains below the calculator's 100-character scalar limit.
        denominator = {'op': 'add', 'left': product([literal(2**300) for _ in range(27)]+[literal(2**91)]),
                       'right': literal(1)}
        source = quantity_report([['0'], ['1'], ['-1'], ['0']], [[True]]*4,
            [[True], [True], [True], [False]], divisor=denominator)
        self.assertEqual(reference_contrast(source)['effect'], {'numerator': '0', 'denominator': '1'})
        # Four selected events yield identical means 1/(4*p), whose denominator
        # has 8194 bits; subtracting them yields zero but does not bound the means.
        records = []
        with patch.object(bootstrap, '_segments', return_value=iter([(0, 1), (2, 1), (2, 1), (2, 1)])):
            result = bootstrap.calculate(source, self.design(), self.limits(max_segments=4), on_draw=records.append)
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertEqual(result['reason'], 'exact_arithmetic_exceeds_numeric_envelope')
        self.assertEqual(records, [])

    def test_seed_runtime_and_resource_scalars_are_type_strict_and_bounded(self):
        for seed in (True, -1, 2**256, '1', 0.5):
            with self.subTest(seed_type=type(seed).__name__), self.assertRaises(Invalid):
                bootstrap.randomness(seed)
        for key, value in (('algorithm', 'another-algorithm'), ('version', 'another-runtime')):
            design = self.design(); design['randomness'][key] = value
            with self.subTest(key=key), self.assertRaises(Invalid):
                bootstrap.calculate(arithmetic_probe(), design, self.limits())
        for changes in ({'max_seconds': True}, {'max_seconds': 1801}, {'max_segments': True},
                        {'max_segments': 0}, {'max_segments': 100000001}):
            with self.subTest(changes=changes), self.assertRaises(Invalid):
                bootstrap.calculate(arithmetic_probe(), self.design(), self.limits(**changes))

    def test_sink_failure_is_not_swallowed_as_completed_computation(self):
        class SinkFailure(Exception): pass
        calls = []
        def sink(record):
            calls.append(record)
            raise SinkFailure('independent test')
        with self.assertRaises(SinkFailure):
            bootstrap.calculate(arithmetic_probe(), self.design(), self.limits(), on_draw=sink)
        self.assertEqual(len(calls), 1)

    def test_caller_and_callback_mutation_cannot_change_detached_design_or_draw_hash(self):
        source, design, limits = arithmetic_probe(), self.design(), self.limits(max_segments=3)
        frozen = deepcopy((source, design, limits))
        pristine_records = []
        def sink(record):
            pristine_records.append(deepcopy(record))
            source['cases'].clear()
            design['randomness']['seed'] = 999
            limits['max_segments'] = 1
            record['value'] = 'forged callback value'
        result = bootstrap.calculate(source, design, limits, on_draw=sink)
        self.assertEqual(result['design'], frozen[1])
        self.assertEqual(result['limits'], frozen[2])
        self.assertEqual(result['time_rows'], 3)
        self.assertEqual(result['cases'][0]['replicate_sha256'], hashlib.sha256(
            ''.join(canonical(record)+'\n' for record in pristine_records).encode()).hexdigest())


if __name__ == '__main__':
    unittest.main()
