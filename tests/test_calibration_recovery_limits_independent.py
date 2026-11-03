"""Pure lower-helper resource controls, not consuming recovery qualification.

These small synthetic internal states exercise integer policy arithmetic only.
They contain no Broker, Registry, authority binding, owned grant, world execution
or numerical result. The production caller must derive its state from genuine
owned history; these cases do not certify that derivation or permit dispatch.

Expected continuation amounts follow the retained finite_family.py policy:
at a resource stop, allocate both bounded tranches while global capacity remains.
"""
from dataclasses import dataclass
import unittest

from trading_researcher.calibration_recovery import CalibrationRecovery
from trading_researcher.codec import Invalid


MIB = 1_048_576
GIB = 1_073_741_824
HOUR_MS = 3_600_000
ATTEMPT_MS = 600_000
ATTEMPT_BYTES = 256 * MIB
GLOBAL_MS = 180 * HOUR_MS
GLOBAL_BYTES = 100 * GIB


@dataclass(frozen=True)
class SyntheticGrantCardinality:
    """Only len() is consumed here; these are counts, never owned artifacts."""

    original: int = 1
    recovery: int = 0

    def __len__(self):
        return self.original + self.recovery


class CalibrationRecoveryLimitsIndependentTests(unittest.TestCase):
    def setUp(self):
        # Avoid constructor authority/Broker setup. Only _capacity_terms and its
        # actual _next_world dependency are exercised, without substituting them.
        self.kernel = CalibrationRecovery.__new__(CalibrationRecovery)

    def state(self, **changes):
        state = {
            'base': {'study': {'body': {'manifest': {'worlds': [
                {'id': 'synthetic-completed'}, {'id': 'synthetic-next'},
                {'id': 'synthetic-later'}]}}}},
            'records': {'synthetic-completed': {'state': 'VERIFIED'}},
            'grants': SyntheticGrantCardinality(),
            'pending': {}, 'unknown': False, 'orphan': False,
            'overrun': False, 'failure': False, 'setup_complete': True,
            'compute': HOUR_MS, 'max_compute': HOUR_MS,
            'storage': 64 * MIB, 'max_storage': 4 * GIB,
            'last_completed': 0, 'no_progress': 0,
        }
        state.update(changes)
        # Every supplied budget is feasible before requesting the next slot.
        self.assertLessEqual(state['compute'], state['max_compute'])
        self.assertLessEqual(state['max_compute'], GLOBAL_MS)
        self.assertLessEqual(state['storage'], state['max_storage'])
        self.assertLessEqual(state['max_storage'], GLOBAL_BYTES)
        return state

    def terms(self, state):
        return self.kernel._capacity_terms(state)

    def assert_denied(self, state, reason):
        with self.assertRaisesRegex(Invalid, reason):
            self.terms(state)

    def test_combined_original_and_recovery_178_can_allocate_final_179th_grant(self):
        # Initial1h plus178 previous1h grants can reach179h. The next grant
        # reaches the unchanged180h cap; no list of fake owned grants is built.
        for original, recovery in ((1, 177), (2, 176), (178, 0)):
            with self.subTest(original=original, recovery=recovery):
                state = self.state(grants=SyntheticGrantCardinality(original, recovery),
                    max_compute=179 * HOUR_MS,
                    compute=179 * HOUR_MS - ATTEMPT_MS + 1)
                terms = self.terms(state)
                self.assertEqual(179, len(state['grants']) + 1)
                self.assertEqual(HOUR_MS, terms['additional_compute_ms'])
                self.assertEqual(4 * GIB, terms['additional_storage_bytes'])
                self.assertEqual(GLOBAL_MS,
                    state['max_compute'] + terms['additional_compute_ms'])

    def test_combined_original_and_recovery_179_cannot_allocate_180th_grant(self):
        for original, recovery in ((1, 178), (2, 177), (179, 0)):
            with self.subTest(original=original, recovery=recovery):
                self.assert_denied(self.state(
                    grants=SyntheticGrantCardinality(original, recovery),
                    max_compute=179 * HOUR_MS,
                    compute=179 * HOUR_MS - ATTEMPT_MS + 1),
                    'continuation allowance')

    def test_each_needed_tranche_is_at_most_one_hour_and_four_gib(self):
        state = self.state(max_compute=HOUR_MS,
            compute=HOUR_MS - ATTEMPT_MS + 1,
            storage=4 * GIB - ATTEMPT_BYTES + 1)
        self.assertEqual({
            'additional_compute_ms': HOUR_MS,
            'additional_storage_bytes': 4 * GIB,
            'charged_compute_ms_before': HOUR_MS - ATTEMPT_MS + 1,
            'charged_storage_bytes_before': 4 * GIB - ATTEMPT_BYTES + 1,
            'completed_worlds_before': 1,
            'no_progress_continuations': 0,
        }, self.terms(state))

    def test_storage_only_grant_funds_full_next_slot_and_its_metadata(self):
        available = ATTEMPT_BYTES + MIB
        # A zero-compute tranche is possible only when global compute allowance
        # is already allocated; the next full compute slot must still fit.
        state = self.state(compute=GLOBAL_MS - ATTEMPT_MS, max_compute=GLOBAL_MS,
            max_storage=GLOBAL_BYTES - available,
            storage=GLOBAL_BYTES - available)
        before = dict(state)
        terms = self.terms(state)
        self.assertEqual(0, terms['additional_compute_ms'])
        self.assertEqual(available, terms['additional_storage_bytes'])
        self.assertEqual(GLOBAL_BYTES, state['storage'] + ATTEMPT_BYTES + MIB)
        self.assertEqual(GLOBAL_BYTES,
            state['max_storage'] + terms['additional_storage_bytes'])
        self.assertEqual(state['storage'], terms['charged_storage_bytes_before'])
        self.assertEqual(before, state, 'Pure terms must not settle or spend a grant')

    def test_exact_remaining_global_600000_ms_funds_full_next_attempt(self):
        state = self.state(compute=GLOBAL_MS - ATTEMPT_MS,
            max_compute=GLOBAL_MS - ATTEMPT_MS, max_storage=GLOBAL_BYTES)
        terms = self.terms(state)
        self.assertEqual(ATTEMPT_MS, terms['additional_compute_ms'])
        self.assertEqual(0, terms['additional_storage_bytes'])
        self.assertEqual(GLOBAL_MS, state['compute'] + ATTEMPT_MS)
        self.assertEqual(GLOBAL_MS,
            state['max_compute'] + terms['additional_compute_ms'])

    def test_compute_only_stop_still_allocates_four_gib_while_storage_capacity_remains(self):
        state = self.state(compute=HOUR_MS, max_compute=HOUR_MS,
            storage=64 * MIB, max_storage=4 * GIB)
        self.assertLessEqual(state['storage'] + ATTEMPT_BYTES, state['max_storage'])
        terms = self.terms(state)
        self.assertEqual(HOUR_MS, terms['additional_compute_ms'])
        self.assertEqual(4 * GIB, terms['additional_storage_bytes'])

    def test_storage_triggered_stop_still_allocates_one_hour_while_compute_capacity_remains(self):
        state = self.state(compute=0, max_compute=HOUR_MS,
            storage=4 * GIB - ATTEMPT_BYTES + 1, max_storage=4 * GIB)
        self.assertLessEqual(state['compute'] + ATTEMPT_MS, state['max_compute'])
        terms = self.terms(state)
        self.assertEqual(HOUR_MS, terms['additional_compute_ms'])
        self.assertEqual(4 * GIB, terms['additional_storage_bytes'])

    def test_one_ms_less_remaining_global_capacity_cannot_fund_next_attempt(self):
        remaining = ATTEMPT_MS - 1
        self.assert_denied(self.state(compute=GLOBAL_MS - remaining,
            max_compute=GLOBAL_MS - remaining), 'next full attempt')

    def test_one_byte_less_global_storage_cannot_fund_next_slot_and_metadata(self):
        remaining = ATTEMPT_BYTES + MIB - 1
        self.assert_denied(self.state(compute=0,
            max_storage=GLOBAL_BYTES - remaining,
            storage=GLOBAL_BYTES - remaining), 'next full attempt and grant metadata')

    def test_exact_allocated_full_next_attempt_requires_no_grant(self):
        self.assert_denied(self.state(compute=HOUR_MS - ATTEMPT_MS,
            storage=4 * GIB - ATTEMPT_BYTES), 'real resource stop')

    def test_compute_grant_can_add_exact_one_mib_only_for_grant_metadata(self):
        state = self.state(max_storage=GLOBAL_BYTES - MIB,
            storage=GLOBAL_BYTES - MIB - ATTEMPT_BYTES)
        terms = self.terms(state)
        self.assertEqual(HOUR_MS, terms['additional_compute_ms'])
        self.assertEqual(MIB, terms['additional_storage_bytes'])
        self.assertEqual(GLOBAL_BYTES, state['storage'] + ATTEMPT_BYTES + MIB)

    def test_one_byte_short_metadata_capacity_denies_even_when_next_storage_fits(self):
        max_storage = GLOBAL_BYTES - (MIB - 1)
        self.assert_denied(self.state(max_storage=max_storage,
            storage=max_storage - ATTEMPT_BYTES), 'next full attempt and grant metadata')

    def test_exhausted_global_compute_cannot_be_repaired_by_storage_allowance(self):
        self.assert_denied(self.state(compute=GLOBAL_MS, max_compute=GLOBAL_MS,
            storage=4 * GIB - ATTEMPT_BYTES + 1), 'next full attempt')

    def test_completed_inventory_cannot_buy_another_grant(self):
        records = {name: {'state': 'INFORMATION_GAP'} for name in (
            'synthetic-completed', 'synthetic-next', 'synthetic-later')}
        self.assert_denied(self.state(records=records), 'No unfinished inventory')

    def test_every_uncertain_failed_or_incomplete_state_denies_before_capacity(self):
        for flag, value in (
                ('pending', {'synthetic-reservation': {}}), ('unknown', True),
                ('orphan', True), ('overrun', True), ('failure', True),
                ('setup_complete', False)):
            with self.subTest(flag=flag):
                self.assert_denied(self.state(**{flag: value}),
                    'failed or uncertain recovery work')

    def test_second_no_progress_continuation_is_allowed_but_third_is_denied(self):
        state = self.state(last_completed=1, no_progress=1)
        self.assertEqual(2, self.terms(state)['no_progress_continuations'])
        self.assert_denied(self.state(last_completed=1, no_progress=2),
            'no completed-world progress')

    def test_valid_information_gap_progress_resets_no_progress_counter(self):
        records = {'synthetic-completed': {'state': 'VERIFIED'},
                   'synthetic-next': {'state': 'INFORMATION_GAP'}}
        state = self.state(records=records, last_completed=1, no_progress=2)
        terms = self.terms(state)
        self.assertEqual(2, terms['completed_worlds_before'])
        self.assertEqual(0, terms['no_progress_continuations'])
        self.assertEqual('synthetic-later', self.kernel._next_world(state)['id'])


if __name__ == '__main__':
    unittest.main()
