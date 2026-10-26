"""Independent fixed family-inventory/count oracles, before implementation review.

These synthetic count records isolate inventory and event accounting. They are
not authenticated simulations and do not establish population-model adequacy.
"""
from copy import deepcopy
from fractions import Fraction
import unittest

import test_information_study as single
from trading_researcher.codec import Invalid, canonical
from trading_researcher.outcomes import _rational, _read_rational
from trading_researcher.family_study import (
    make_manifest, make_final_manifest, summarize, count_plan,
    count_assessment, validate_count_envelope,
)


def family_inputs(size=2, *, final=False, direction='positive'):
    assigned = single.assigned()
    assigned.update(primary_count=size, direction=direction)
    profile = single.profile()
    effects = 5 if direction == 'nondirectional' else 3
    profile['responses'] = ['response-' + str(index) for index in range(size)]
    mixed = [0, 1] + [2] * (size - 2)
    profile['patterns'] = sorted([[index] * size for index in range(effects)] + [mixed])
    if final:
        profile.update(targets=[16], worlds_per_cell=256)
    return assigned, profile


def applicability():
    return {name: {'status': 'not_applicable', 'cohort_ids': [],
                   'reason': 'Fixed synthetic accounting fixture, not applicability evidence.'}
            for name in ('heavy_tail', 'overlap', 'common_shock')}


def union(values):
    """Three-valued event union fixed independently of the production mapper."""
    return True if True in values else None if not values or None in values else False


def expected_events(components, delta):
    errors = [None if item['covered'] is None else not item['covered'] for item in components]
    nulls, boundary, detection = [], [], {}
    for item in components:
        magnitude = abs(_read_rational(item['truth']))
        if item['state'] == 'VERIFIED':
            supported = item['decision'] == 'SUPPORTED_INITIAL'
            decisive = item['decision'] in ('SUPPORTED_INITIAL', 'TESTED_NEGATIVE')
        elif item['state'] == 'INFORMATION_GAP':
            supported = decisive = False
        else:
            supported = decisive = None
        if magnitude == 0:
            nulls.append(supported)
        if magnitude == delta:
            boundary.append(decisive)
        if magnitude == 2 * delta:
            detection[item['id']] = supported
    return {'joint_miscoverage': union(errors), 'false_support': union(nulls),
            'boundary_decisive': union(boundary), 'detections': detection}


def record(manifest, world, *, state='VERIFIED', overrides=None):
    """Deterministic synthetic outcomes; no generator/estimator is called."""
    overrides = overrides or {}
    delta = _read_rational(manifest['assigned']['delta'])
    pattern = manifest['profile']['patterns'][world['pattern_index']]
    components = []
    for identity, scenario in zip(manifest['profile']['responses'], pattern):
        truth = manifest['effects'][scenario]
        item = {'id': identity, 'truth': deepcopy(truth), 'state': state,
                'decision': ('SUPPORTED_INITIAL' if abs(_read_rational(truth)) == 2 * delta
                             else 'TESTED_INCONCLUSIVE') if state == 'VERIFIED' else None,
                'covered': True if state == 'VERIFIED' else None}
        item.update(overrides.get(identity, {}))
        components.append(item)
    return {'world_id': world['id'], 'state': state, 'decision': None,
            'scope_count': None, 'condition_count': None, 'covered': None,
            'components': components, 'events': expected_events(components, delta)}


def fixed_records(manifest, *, state='VERIFIED'):
    return [record(manifest, world, state=state) for world in manifest['worlds']]


def sources(records):
    return {item['world_id']: 'a' * 64 for item in records}


class FamilyStudyOracleTests(unittest.TestCase):
    def test_inventory_is_world_not_component_count_with_distinct_streams(self):
        assigned, profile = family_inputs()
        original = deepcopy((assigned, profile))
        manifest = make_manifest(assigned, profile)
        self.assertEqual(manifest['schema'], 'family-information-study-manifest/1')
        self.assertEqual(len(manifest['worlds']), 16)  # 2 targets * 4 vectors * 2 worlds.
        self.assertEqual(len({item['id'] for item in manifest['worlds']}), 16)
        seeds = [item[key] for item in manifest['worlds'] for key in ('population_seed', 'bootstrap_seed')]
        self.assertEqual(len(set(seeds)), 32)
        self.assertEqual(manifest, make_manifest(assigned, profile))
        self.assertEqual((assigned, profile), original)
        self.assertEqual({item['pattern_index'] for item in manifest['worlds']}, {0, 1, 2, 3})
        self.assertTrue(all('scenario' not in item for item in manifest['worlds']))
        self.assertFalse(manifest['scientific_readiness'])

    def test_final_inventory_has_256_per_vector_and_separate_namespace(self):
        assigned, profile = family_inputs(final=True)
        final = make_final_manifest(assigned, profile)
        development = make_manifest(assigned, profile)
        self.assertEqual(final['schema'], 'family-evaluator-calibration-manifest/1')
        self.assertEqual(len(final['worlds']), 1024)
        for index in range(4):
            self.assertEqual(sum(w['pattern_index'] == index for w in final['worlds']), 256)
        for key in ('id', 'population_seed', 'bootstrap_seed'):
            self.assertFalse({w[key] for w in final['worlds']} & {w[key] for w in development['worlds']})

    def test_twenty_two_required_cohorts_survive_old_sixteen_limit(self):
        assigned, profile = family_inputs(8, final=True)
        manifest = make_final_manifest(assigned, profile)
        before = deepcopy(manifest)
        plan = count_plan(manifest, applicability())
        # Null: 2; mixed [0,1,2,2,2,2,2,2]: 9; boundary: 2; alternatives: 9.
        expected = set()
        for index, kinds in enumerate((['false_support'], ['false_support', 'boundary_decisive'],
                                       ['boundary_decisive'], [])):
            expected.add(f'spec-0/pattern-{index}/joint_miscoverage')
            expected.update(f'spec-0/pattern-{index}/{kind}' for kind in kinds)
        expected.update(f'spec-0/pattern-1/detection/response-{i}' for i in range(2, 8))
        expected.update(f'spec-0/pattern-3/detection/response-{i}' for i in range(8))
        self.assertEqual(len(expected), 22)
        self.assertEqual({item['id'] for item in plan['cohorts']}, expected)
        self.assertEqual(len(manifest['worlds']), 1024)
        self.assertTrue(all('world_ids' not in item for item in plan['cohorts']))
        validate_count_envelope(manifest, applicability())
        self.assertEqual(manifest, before)

    def test_nondirectional_inventory_retains_both_signs(self):
        assigned, profile = family_inputs(8, final=True, direction='nondirectional')
        manifest = make_final_manifest(assigned, profile)
        self.assertEqual(manifest['effects'], list(map(_rational, (0, Fraction(1, 20), Fraction(1, 10),
                                                                 Fraction(-1, 20), Fraction(-1, 10)))))
        self.assertEqual(len(manifest['worlds']), 1536)
        self.assertEqual(len(count_plan(manifest, applicability())['cohorts']), 33)
        validate_count_envelope(manifest, applicability())

    def test_invalid_pattern_or_response_never_silently_changes_inventory(self):
        assigned, profile = family_inputs()
        mutations = [
            {'responses': ['z', 'a']}, {'responses': ['a', 'a']}, {'responses': ['a']},
            {'patterns': [[0, 0], [1, 1], [2, 2]]},  # Missing mixed truth.
            {'patterns': [[0, 0], [0, 1], [2, 2]]},  # Missing homogeneous boundary.
            {'patterns': [[0, 0], [0, 1], [1, 1], [2, 2], [2, 2]]},
            {'patterns': [[0, 0], [0, True], [1, 1], [2, 2]]},
            {'patterns': [[0, 0], [0, 3], [1, 1], [2, 2]]},
            {'patterns': [[0, 0], [0], [1, 1], [2, 2]]},
            {'patterns': [[2, 2], [1, 1], [0, 1], [0, 0]]},
        ]
        for changes in mutations:
            with self.subTest(changes=changes), self.assertRaises(Invalid):
                make_manifest(assigned, {**profile, **changes})

    def test_no_final_repetition_target_or_world_cap_truncation(self):
        assigned, profile = family_inputs(final=True)
        for changes in ({'worlds_per_cell': 255}, {'worlds_per_cell': True}, {'targets': [16, 32]}):
            with self.subTest(changes=changes), self.assertRaises(Invalid):
                make_final_manifest(assigned, {**profile, **changes})
        oversized = deepcopy(profile)
        oversized['specifications'] = [{**profile['specifications'][0], 'mask_mean_block': k} for k in (2, 4, 8)]
        with self.assertRaises(Invalid):
            make_final_manifest(assigned, oversized)  # 3 * 4 * 256 = 3072, not 2048.

    def test_complete_counts_consume_all_twenty_two_cohorts(self):
        assigned, profile = family_inputs(8, final=True)
        manifest = make_final_manifest(assigned, profile)
        records = fixed_records(manifest)
        before = deepcopy(records)
        result = count_assessment(manifest, records, sources(records), applicability())
        self.assertEqual(result['status'], 'PASS_COUNTS_ONLY')
        self.assertEqual(len(result['cohorts']), 22)
        for cohort in result['cohorts']:
            self.assertEqual(cohort['planned'], 256)
            self.assertEqual(cohort['observed'], 256)
            self.assertEqual(cohort['observed_events'], 256 if cohort['criterion'] == 'detection' else 0)
        self.assertFalse(result['scientific_readiness'])
        self.assertLessEqual(len(canonical(result).encode()), 1048576)
        self.assertEqual(records, before)

    def test_boundary_union_counts_both_error_directions_once_per_world(self):
        assigned, profile = family_inputs(final=True)
        manifest = make_final_manifest(assigned, profile)
        records = []
        for world in manifest['worlds']:
            overrides = {}
            if world['pattern_index'] == 2:
                if world['replicate'] < 17:
                    overrides = {identity: {'decision': 'SUPPORTED_INITIAL'} for identity in profile['responses']}
                elif world['replicate'] < 34:
                    overrides = {profile['responses'][1]: {'decision': 'TESTED_NEGATIVE'}}
            records.append(record(manifest, world, overrides=overrides))
        result = count_assessment(manifest, records, sources(records), applicability())
        boundary = next(c for c in result['cohorts'] if c['cohort_id'] == 'spec-0/pattern-2/boundary_decisive')
        self.assertEqual(boundary['observed_events'], 34)  # Not 51 from adding component errors.
        self.assertEqual(boundary['status'], 'FAIL_COUNTS_ONLY')
        self.assertEqual(result['status'], 'FAIL_COUNTS_ONLY')

    def test_information_gap_is_no_decision_but_never_joint_coverage_success(self):
        assigned, profile = family_inputs(final=True)
        manifest = make_final_manifest(assigned, profile)
        records = fixed_records(manifest, state='INFORMATION_GAP')
        result = count_assessment(manifest, records, sources(records), applicability())
        self.assertEqual(result['status'], 'NOT_ASSESSED')
        for cohort in result['cohorts']:
            self.assertEqual(cohort['planned'], 256)
            self.assertEqual(cohort['observed_events'], 0)
            if cohort['criterion'] == 'joint_miscoverage':
                self.assertEqual(cohort['observed'], 0)
                self.assertEqual(cohort['unavailable_indices'], list(range(256)))
                self.assertIsNone(cohort['point'])
            else:
                self.assertEqual(cohort['observed'], 256)

    def test_missing_and_failed_worlds_keep_full_denominator_and_positions(self):
        assigned, profile = family_inputs(final=True)
        manifest = make_final_manifest(assigned, profile)
        records = fixed_records(manifest)
        missing = next(w for w in manifest['worlds'] if w['pattern_index'] == 3 and w['replicate'] == 5)
        failed = next(w for w in manifest['worlds'] if w['pattern_index'] == 3 and w['replicate'] == 7)
        records = [r for r in records if r['world_id'] != missing['id']]
        records = [record(manifest, failed, state='TECHNICAL_FAILURE') if r['world_id'] == failed['id'] else r for r in records]
        result = count_assessment(manifest, records, sources(records), applicability())
        self.assertEqual(result['status'], 'NOT_ASSESSED')
        affected = [c for c in result['cohorts'] if c['cohort_id'].startswith('spec-0/pattern-3/')]
        self.assertEqual(len(affected), 3)
        for cohort in affected:
            self.assertEqual(cohort['planned'], 256)
            self.assertEqual(cohort['observed'], 254)
            self.assertEqual(cohort['missing_indices'], [5])
            self.assertEqual(cohort['unavailable_indices'], [7])
            self.assertIsNone(cohort['point'])

    def test_target_nomination_requires_every_planted_component_on_complete_grid(self):
        assigned, profile = family_inputs()
        manifest = make_manifest(assigned, profile)
        records = []
        for world in manifest['worlds']:
            overrides = {}
            if world['time_rows'] == 16 and world['pattern_index'] == 3 and world['replicate'] == 0:
                overrides = {profile['responses'][1]: {'decision': 'TESTED_INCONCLUSIVE'}}
            records.append(record(manifest, world, overrides=overrides))
        complete = summarize(manifest, records)
        self.assertTrue(complete['complete'])
        self.assertEqual(complete['candidate_time_rows'], 32)
        self.assertIsNone(summarize(manifest, records[:-1])['candidate_time_rows'])
        self.assertFalse(summarize(manifest, records[:-1])['complete'])

    def test_record_event_truth_and_aggregate_are_checked_not_trusted(self):
        assigned, profile = family_inputs()
        manifest = make_manifest(assigned, profile)
        original = record(manifest, manifest['worlds'][0])
        altered = []
        item = deepcopy(original); item['events']['joint_miscoverage'] = True; altered.append(item)
        item = deepcopy(original); item['components'][0]['truth'] = _rational(Fraction(1, 20)); altered.append(item)
        item = deepcopy(original); item['components'][0]['id'] = 'unplanned-response'; altered.append(item)
        item = deepcopy(original); item['components'].pop(); altered.append(item)
        item = deepcopy(original); item['decision'] = 'SUPPORTED_INITIAL'; altered.append(item)
        item = deepcopy(original); item['state'] = 'INFORMATION_GAP'; altered.append(item)
        for item in altered:
            with self.subTest(record=item), self.assertRaises(Invalid):
                summarize(manifest, [item])
        with self.assertRaises(Invalid):
            summarize(manifest, [original, original])

    def test_count_sources_and_applicability_cannot_drop_required_cells(self):
        assigned, profile = family_inputs(final=True)
        manifest = make_final_manifest(assigned, profile)
        records = [record(manifest, manifest['worlds'][0])]
        for refs in ({}, {**sources(records), 'unplanned-world': 'b' * 64}):
            with self.subTest(sources=refs), self.assertRaises(Invalid):
                count_assessment(manifest, records, refs, applicability())
        invalid = applicability()
        invalid['common_shock'] = {'status': 'included', 'cohort_ids': ['absent-cohort'], 'reason': 'Invalid fixture.'}
        with self.assertRaises(Invalid):
            count_plan(manifest, invalid)


if __name__ == '__main__':
    unittest.main()
