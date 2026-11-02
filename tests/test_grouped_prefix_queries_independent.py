"""Hand-fixed exact segment-query expectations, before grouped implementation.

The arithmetic-probe facts were independently fixed in
test_stationary_bootstrap_adversarial.py: t0 contains (0,true),(10,unknown),
t1 contains (4,true), and t2 has no eligible contribution. Other rows below
are explicit invented cumulative statistics. No expected answer is obtained
from either the new grouped helper or the old scalar segment helper.

Only valid private inputs are exercised. Numeric bounds remain the caller's
responsibility at its original accumulation points.
"""
from copy import deepcopy
from fractions import Fraction as F
import unittest

from trading_researcher import stationary_bootstrap as bootstrap
from test_stationary_bootstrap_adversarial import arithmetic_probe


class GroupedPrefixQueriesIndependentTests(unittest.TestCase):
    def helper(self):
        # Resolve inside each test so the preimplementation run reports the
        # missing capability explicitly without preventing test discovery.
        return getattr(bootstrap, '_segment_sums')

    def assert_query(self, helper, rows, start, count, expected):
        before = deepcopy(rows)
        actual = tuple(helper(rows, start, count))
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 4)
        self.assertTrue(all(type(value) in (int, F) for value in actual),
                        'Exact Python integer/Fraction statistics must not narrow to floats or fixed dtypes')
        self.assertEqual(rows, before)

    def test_hand_unknown_baseline_empty_bucket_and_every_complete_cycle(self):
        helper = self.helper()
        rows = [(0, 0, 0, 0), (2, 10, 1, 0), (3, 14, 2, 4), (3, 14, 2, 4)]
        cases = [
            (0, 1, (2, 10, 1, 0)), (1, 1, (1, 4, 1, 4)), (2, 1, (0, 0, 0, 0)),
            (0, 2, (3, 14, 2, 4)), (1, 2, (1, 4, 1, 4)), (2, 2, (2, 10, 1, 0)),
            (0, 3, (3, 14, 2, 4)), (1, 3, (3, 14, 2, 4)), (2, 3, (3, 14, 2, 4)),
        ]
        for start, count, expected in cases:
            with self.subTest(start=start, count=count):
                self.assert_query(helper, rows, start, count, expected)

    def test_signed_fractional_quantities_wrap_in_original_grid_positions(self):
        helper = self.helper()
        # Bucket facts: (2,1/3,1,-2/3), (1,-5/4,1,-5/4), zero,
        # (2,7/6,1,5/6). An unknown condition can add to total alone.
        rows = [(0, 0, 0, 0), (2, F(1, 3), 1, F(-2, 3)),
                (3, F(-11, 12), 2, F(-23, 12)),
                (3, F(-11, 12), 2, F(-23, 12)), (5, F(1, 4), 3, F(-13, 12))]
        cases = [
            (0, 1, (2, F(1, 3), 1, F(-2, 3))),
            (1, 1, (1, F(-5, 4), 1, F(-5, 4))),
            (2, 1, (0, 0, 0, 0)),
            (3, 1, (2, F(7, 6), 1, F(5, 6))),
            (1, 2, (1, F(-5, 4), 1, F(-5, 4))),
            (2, 2, (2, F(7, 6), 1, F(5, 6))),
            (3, 2, (4, F(3, 2), 2, F(1, 6))),
            (2, 3, (4, F(3, 2), 2, F(1, 6))),
            (3, 3, (5, F(1, 4), 3, F(-13, 12))),
        ]
        for start, count, expected in cases:
            with self.subTest(start=start, count=count):
                self.assert_query(helper, rows, start, count, expected)
        for start in range(4):
            with self.subTest(complete_cycle_start=start):
                self.assert_query(helper, rows, start, 4, (5, F(1, 4), 3, F(-13, 12)))

    def test_one_grid_position_can_be_empty_or_have_no_true_condition(self):
        helper = self.helper()
        for rows, expected in (
            ([(0, 0, 0, 0), (0, 0, 0, 0)], (0, 0, 0, 0)),
            ([(0, 0, 0, 0), (1, -7, 0, 0)], (1, -7, 0, 0)),
            ([(0, 0, 0, 0), (2, F(-1, 7), 1, F(2, 7))], (2, F(-1, 7), 1, F(2, 7))),
        ):
            with self.subTest(rows=rows):
                self.assert_query(helper, rows, 0, 1, expected)

    def test_large_signed_integer_units_above_binary_float_resolution(self):
        helper = self.helper()
        large = 2 ** 53
        # Individual buckets have totals large+1, -large, 3. The third
        # bucket has no true condition, preserving separate count channels.
        rows = [(0, 0, 0, 0), (1, large + 1, 1, large + 1),
                (2, 1, 2, 1), (3, 4, 2, 1)]
        cases = [(0, 1, (1, large + 1, 1, large + 1)),
                 (1, 2, (2, 3 - large, 1, -large)),
                 (2, 2, (2, large + 4, 1, large + 1)),
                 (1, 3, (3, 4, 2, 1))]
        for start, count, expected in cases:
            with self.subTest(start=start, count=count):
                self.assert_query(helper, rows, start, count, expected)

    def test_large_denominator_fractions_retain_sub_float_unit_differences(self):
        helper = self.helper()
        tiny = F(1, 2 ** 53 + 1)
        rows = [(0, 0, 0, 0), (1, tiny, 1, tiny), (2, 0, 2, 0)]
        self.assert_query(helper, rows, 0, 1, (1, tiny, 1, tiny))
        self.assert_query(helper, rows, 1, 1, (1, -tiny, 1, -tiny))
        self.assert_query(helper, rows, 0, 2, (2, 0, 2, 0))
        self.assert_query(helper, rows, 1, 2, (2, 0, 2, 0))

    def test_8192_bit_prefixes_allow_wrap_intermediate_then_exact_cancellation(self):
        helper = self.helper()
        edge = 1 << 8191
        self.assertEqual(edge.bit_length(), 8192)
        rows = [(0, 0, 0, 0), (1, -edge, 1, -edge),
                (2, 0, 2, 0), (3, edge, 3, edge)]
        # A wrapped full cycle first forms edge-(-edge), then adds -edge.
        # Bounding that temporary would reject an otherwise admitted sum.
        self.assert_query(helper, rows, 1, 3, (3, edge, 3, edge))
        self.assert_query(helper, rows, 2, 2, (2, 0, 2, 0))
        # This exact segment itself exceeds the bound: return it untouched.
        # The calculator owns its original later total/conditional guards.
        self.assert_query(helper, rows, 1, 2, (2, 2 * edge, 2, 2 * edge))

    def test_8192_bit_fraction_numerators_keep_the_same_cancellation_boundary(self):
        helper = self.helper()
        edge = F(1 << 8191, 3)
        self.assertEqual(edge.numerator.bit_length(), 8192)
        rows = [(0, 0, 0, 0), (1, -edge, 1, -edge),
                (2, 0, 2, 0), (3, edge, 3, edge)]
        self.assert_query(helper, rows, 1, 3, (3, edge, 3, edge))
        self.assert_query(helper, rows, 2, 2, (2, 0, 2, 0))
        self.assert_query(helper, rows, 1, 2, (2, 2 * edge, 2, 2 * edge))

    def test_existing_prefix_owner_contract_transposes_without_mutation(self):
        source = arithmetic_probe()
        before = deepcopy(source)
        prefixes = bootstrap._prefixes(source)
        self.assertEqual(prefixes, [[0, 2, 3, 3], [0, 10, 14, 14],
                                    [0, 1, 2, 2], [0, 0, 4, 4]])
        rows = list(zip(*prefixes))
        helper = self.helper()
        self.assert_query(helper, rows, 2, 2, (2, 10, 1, 0))
        self.assert_query(helper, rows, 1, 3, (3, 14, 2, 4))
        self.assertEqual(prefixes, [[0, 2, 3, 3], [0, 10, 14, 14],
                                    [0, 1, 2, 2], [0, 0, 4, 4]])
        self.assertEqual(source, before)


if __name__ == '__main__':
    unittest.main()
