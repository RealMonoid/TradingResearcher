"""Independent exact-order reuse checks; no change to scientific acceptance.

Fixed arithmetic expectations precede implementation. The preserved package is
loaded under a separate name so comparisons execute its original relative imports.
"""
from contextlib import contextmanager
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from trading_researcher import evaluation_policy as policy, monte_carlo as mc
from trading_researcher.codec import Invalid
from trading_researcher.outcomes import _rational as q


ARCHIVE = Path(__file__).parent / 'fixtures/study-source-dc3e6fc.zip'
ARCHIVE_SHA256 = '7b6ae8230d46af0e072736be9f905310d9b8936d2cdff3fde2becc3fd92cc014'


@contextmanager
def retained_modules():
    assert hashlib.sha256(ARCHIVE.read_bytes()).hexdigest() == ARCHIVE_SHA256
    package = '_retained_ordered_replicates_reference'
    assert not any(name == package or name.startswith(package + '.') for name in sys.modules)
    with tempfile.TemporaryDirectory() as directory:
        destination = Path(directory) / 'trading_researcher'; destination.mkdir()
        with zipfile.ZipFile(ARCHIVE) as archive:
            names = archive.namelist()
            assert len(names) == 57 and len(set(names)) == 57
            for name in names:
                parts = Path(name).parts
                assert len(parts) == 2 and parts[0] == 'trading_researcher' and parts[1].endswith('.py')
                (destination / parts[1]).write_bytes(archive.read(name))
        spec = importlib.util.spec_from_file_location(package, destination / '__init__.py',
            submodule_search_locations=[str(destination)])
        module = importlib.util.module_from_spec(spec); sys.modules[package] = module
        try:
            spec.loader.exec_module(module)
            yield (importlib.import_module(package + '.evaluation_policy'),
                   importlib.import_module(package + '.monte_carlo'))
        finally:
            for name in list(sys.modules):
                if name == package or name.startswith(package + '.'): del sys.modules[name]


def config(direction='positive'):
    return {'schema':'mc-boundary-policy/1', 'noncoverage':q(Fraction(1, 100)),
            'delta':q(Fraction(1, 20)), 'direction':direction}


def outcome(function, *args):
    try:
        return {'value':function(*deepcopy(args))}
    except Exception as error:
        return {'error':type(error).__name__, 'code':getattr(error, 'code', None), 'message':str(error)}


class OrderedReplicatesIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference_context = retained_modules()
        cls.old_policy, cls.old_mc = cls.reference_context.__enter__()
        cls.addClassCleanup(cls.reference_context.__exit__, None, None, None)

    def test_hand_derived_negative_ties_and_type_seven_interpolation(self):
        values = list(map(q, (5, -3, -3, 1)))
        expected = [(0, -3), (Fraction(1, 4), -3), (Fraction(1, 2), -1), (Fraction(3, 4), 2), (1, 5)]
        for probability, value in expected:
            with self.subTest(p=probability):
                self.assertEqual(policy.quantile(values, q(probability)), q(value))
        self.assertEqual(policy.basic_interval(q(1), values, q(Fraction(1, 2))), {'lower':q(0), 'upper':q(5)})
        self.assertEqual(policy.basic_interval(q(-4), list(map(q, (-1, -7, -3))), q(Fraction(1, 2))),
                         {'lower':q(-6), 'upper':q(-3)})

    def test_two_hundred_bit_near_ties_remain_exact(self):
        epsilon = Fraction(1, 2**200)
        values = [q(1 + epsilon), q(1 - epsilon)]
        self.assertEqual(policy.quantile(values, q(Fraction(1, 4))), q(1 - epsilon / 2))
        self.assertEqual(policy.basic_interval(q(1), values, q(Fraction(1, 2))),
            {'lower':q(1 - epsilon / 2), 'upper':q(1 + epsilon / 2)})

    def test_singleton_and_closed_quantile_endpoints(self):
        for probability in (0, Fraction(1, 7), 1):
            self.assertEqual(policy.quantile([q(-8)], q(probability)), q(-8))
        self.assertEqual(policy.basic_interval(q(-8), [q(-8)], q(Fraction(1, 20))),
                         {'lower':q(-8), 'upper':q(-8)})

    def test_ordered_helper_reads_all_values_once_and_detaches_input(self):
        values = [q(5), q(-3), q(1), q(-3)]; before = deepcopy(values)
        with patch.object(policy, '_read_rational', wraps=policy._read_rational) as reader:
            ordered = policy._ordered_replicates(values)
        self.assertIs(type(ordered), tuple)
        self.assertEqual(ordered, (Fraction(-3), Fraction(-3), Fraction(1), Fraction(5)))
        self.assertEqual(reader.call_count, 4)
        self.assertEqual(values, before)
        values[0]['numerator'] = '999'
        self.assertEqual(ordered[-1], 5)

    def test_public_basic_interval_orders_only_once(self):
        values = list(map(q, (5, -3, -3, 1)))
        with patch.object(policy, '_ordered_replicates', wraps=policy._ordered_replicates) as ordered:
            result = policy.basic_interval(q(1), values, q(Fraction(1, 2)))
        self.assertEqual(result, {'lower':q(0), 'upper':q(5)})
        self.assertEqual(ordered.call_count, 1)
        self.assertEqual(ordered.call_args.args[0], values)

    def test_diagnose_orders_once_per_length_and_matches_full_baseline(self):
        values = [q(Fraction((index * 17) % 11 - 5, 80)) for index in range(19999)]
        draws = {8:list(reversed(values)), 4:values}; before = deepcopy(draws)
        expected = self.old_mc.diagnose(q(Fraction(1, 20)), draws, q(Fraction(1, 40)), config())
        with patch.object(mc, '_ordered_replicates', wraps=policy._ordered_replicates) as ordered:
            result = mc.diagnose(q(Fraction(1, 20)), draws, q(Fraction(1, 40)), config())
        self.assertEqual(result, expected)
        self.assertEqual(ordered.call_count, 2)
        self.assertEqual([len(call.args[0]) for call in ordered.call_args_list], [19999, 19999])
        self.assertEqual(draws, before)

    def test_private_ordered_quantile_retains_public_probability_validation(self):
        ordered = policy._ordered_replicates(list(map(q, (5, -3, -3, 1))))
        for probability in (q(0), q(Fraction(1, 2)), q(1), q(-1), q(2), None,
                            {'numerator':'2', 'denominator':'2'}):
            self.assertEqual(outcome(policy._quantile_ordered, ordered, probability),
                             outcome(self.old_policy.quantile, list(map(q, (5, -3, -3, 1))), probability))

    def test_late_invalid_and_noncanonical_replicates_are_not_skipped(self):
        bad_values = [None, q(2**8192), {'numerator':'2', 'denominator':'2'},
            {'numerator':'-0', 'denominator':'1'}, {'numerator':'01', 'denominator':'1'},
            {'numerator':True, 'denominator':'1'}, {'numerator':'1', 'denominator':'0'}]
        for bad in bad_values:
            values = [q(0)] * 32 + [bad]
            with self.subTest(bad=bad):
                for current, old, args in (
                    (policy.quantile, self.old_policy.quantile, (values, q(0))),
                    (policy.basic_interval, self.old_policy.basic_interval, (q(0), values, q(Fraction(1, 20)))),
                    (mc.quantile_band, self.old_mc.quantile_band, (values, q(Fraction(1, 2)), q(Fraction(1, 20))))):
                    observed = outcome(current, *args)
                    self.assertIn('error', observed)
                    self.assertEqual(observed, outcome(old, *args))

    def test_shape_and_probability_bounds_match_baseline(self):
        for values in ([], (), [q(0)] * 20000, None):
            for current, old, args in (
                (policy.quantile, self.old_policy.quantile, (values, q(Fraction(1, 2)))),
                (policy.basic_interval, self.old_policy.basic_interval, (q(0), values, q(Fraction(1, 20)))),
                (mc.quantile_band, self.old_mc.quantile_band, (values, q(Fraction(1, 2)), q(Fraction(1, 20))))):
                self.assertEqual(outcome(current, *args), outcome(old, *args))
        for alpha in (q(0), q(1), q(-1), None, {'numerator':'2', 'denominator':'2'}):
            self.assertEqual(outcome(policy.basic_interval, q(0), [q(0)], alpha),
                             outcome(self.old_policy.basic_interval, q(0), [q(0)], alpha))

    def test_numeric_envelope_includes_intermediate_tail_probability(self):
        alpha = q(Fraction(1, 2**8191))
        expected = outcome(self.old_policy.basic_interval, q(0), [q(0)], alpha)
        self.assertEqual(expected['error'], 'Invalid')
        self.assertIn('RESOURCE_GAP', expected['message'])
        self.assertEqual(outcome(policy.basic_interval, q(0), [q(0)], alpha), expected)

    def test_tail_numeric_failure_precedes_invalid_replicate_failure(self):
        alpha = q(Fraction(1, 2**8191))
        for values in ([], [None], [q(0)] * 20000):
            with self.subTest(shape=type(values).__name__, count=len(values)):
                expected = outcome(self.old_policy.basic_interval, q(0), values, alpha)
                self.assertEqual(expected['error'], 'Invalid')
                self.assertIn('RESOURCE_GAP', expected['message'])
                self.assertEqual(outcome(policy.basic_interval, q(0), values, alpha), expected)

    def test_numeric_envelope_includes_interpolated_quantile_and_reflection(self):
        large = 2**8191
        self.assertEqual(policy.quantile([q(large)], q(1)), q(large))
        requests = [(policy.quantile, self.old_policy.quantile,
                     ([q(0), q(Fraction(1, large))], q(Fraction(1, 2)))),
                    (policy.basic_interval, self.old_policy.basic_interval,
                     (q(large), [q(-large)], q(Fraction(1, 2))))]
        for current, old, args in requests:
            expected = outcome(old, *args)
            self.assertIn('RESOURCE_GAP', expected['message'])
            self.assertEqual(outcome(current, *args), expected)

    def test_quantile_bands_keep_exact_ranks_unbounded_ends_and_atoms(self):
        values = list(map(q, (7, -2, -2, 1, 4)))
        self.assertEqual(mc.quantile_band(values, q(Fraction(1, 2)), q(Fraction(1, 32))),
                         {'ranks':[1, 5], 'lower':q(-2), 'upper':q(7)})
        self.assertEqual(mc.quantile_band(values, q(Fraction(1, 2)), q(Fraction(1, 100))),
                         {'ranks':[0, 6], 'lower':None, 'upper':None})
        for p in (Fraction(1, 4), Fraction(1, 2), Fraction(3, 4)):
            self.assertEqual(mc.quantile_band(values, q(p), q(Fraction(1, 20))),
                             self.old_mc.quantile_band(values, q(p), q(Fraction(1, 20))))

    def test_complete_diagnostic_equality_for_boundary_negative_and_nondirectional(self):
        for direction, point in (('positive', Fraction(1, 20)), ('negative', Fraction(-1, 10)),
                                 ('nondirectional', Fraction(1, 20))):
            draws = {4:[q(point)] * 19999}
            with self.subTest(direction=direction):
                self.assertEqual(mc.diagnose(q(point), draws, q(Fraction(1, 20)), config(direction)),
                                 self.old_mc.diagnose(q(point), draws, q(Fraction(1, 20)), config(direction)))

    def test_undefined_and_incomplete_precheck_semantics_are_preserved(self):
        invalid = {'numerator':'2', 'denominator':'2'}
        for values in ([invalid], [q(0)] * 19997 + [None, invalid], [q(0)] * 19998 + [None]):
            args = (q(0), {4:values}, q(Fraction(1, 20)), config())
            observed = mc.diagnose(*args)
            self.assertEqual(observed, self.old_mc.diagnose(*args))
            self.assertEqual(observed['status'], 'NOT_ASSESSED')
            self.assertEqual(observed['reason'], 'incomplete_or_undefined_draws')
        values = [q(0)] * 19998 + [invalid]
        self.assertEqual(outcome(mc.diagnose, q(0), {4:values}, q(Fraction(1, 20)), config()),
                         outcome(self.old_mc.diagnose, q(0), {4:values}, q(Fraction(1, 20)), config()))

    def test_repeated_calls_do_not_cache_mutated_inputs_or_results(self):
        values = [q(0), q(1)]; before = deepcopy(values)
        first = policy.basic_interval(q(Fraction(1, 2)), values, q(Fraction(1, 2)))
        self.assertEqual(values, before)
        first['lower']['numerator'] = '999'
        repeated = policy.basic_interval(q(Fraction(1, 2)), values, q(Fraction(1, 2)))
        self.assertEqual(repeated, {'lower':q(Fraction(1, 4)), 'upper':q(Fraction(3, 4))})
        values[1] = q(2)
        self.assertEqual(policy.quantile(values, q(Fraction(1, 2))), q(1))


if __name__ == '__main__':
    unittest.main()
