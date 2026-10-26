"""Frozen final-world identity and extraction of count events from outcomes."""
from copy import deepcopy
import unittest

from test_information_study import assigned, profile
from trading_researcher.calibration_study import make_final_manifest, count_assessment, validate_count_envelope
from trading_researcher.information_study import make_manifest, budget_state
from trading_researcher.codec import Invalid


class FinalCalibrationManifestTests(unittest.TestCase):
    def manifest(self):
        config = profile()
        config.update(targets=[16], worlds_per_cell=256)
        return make_final_manifest(assigned(), config)

    def test_final_worlds_are_fixed_and_disjoint_from_development_namespace(self):
        config = profile()
        config.update(targets=[16], worlds_per_cell=256)
        final = make_final_manifest(assigned(), config)
        development = make_manifest(assigned(), config)
        self.assertEqual(final, make_final_manifest(assigned(), config))
        self.assertEqual(len(final['worlds']), 768)
        for key in ('id', 'population_seed', 'bootstrap_seed'):
            self.assertFalse({w[key] for w in final['worlds']} & {w[key] for w in development['worlds']})
        self.assertEqual(budget_state(final, [], [])['charged_compute_ms'], 0)

    def test_records_produce_boundary_union_and_joint_error_events(self):
        manifest = self.manifest()
        records = []
        sources = {}
        for world in manifest['worlds']:
            scenario = world['scenario']
            decision = 'SUPPORTED_INITIAL' if scenario == 2 or scenario == 1 and world['replicate'] < 17 else 'TESTED_INCONCLUSIVE'
            if scenario == 1 and 17 <= world['replicate'] < 34:
                decision = 'TESTED_NEGATIVE'
            records.append({'world_id': world['id'], 'state': 'VERIFIED', 'decision': decision,
                            'scope_count': 8, 'condition_count': 4, 'covered': True})
            sources[world['id']] = 'owned:attempt-' + world['id']
        before = deepcopy(records)
        result = count_assessment(manifest, records, sources, self.applicability(manifest))
        self.assertEqual(result['status'], 'FAIL_COUNTS_ONLY')
        boundary = next(c for c in result['cohorts'] if c['criterion'] == 'boundary_decisive')
        self.assertEqual(boundary['observed_events'], 34)
        self.assertEqual(records, before)

    def applicability(self, manifest):
        return {name: {'status': 'not_applicable', 'cohort_ids': [],
                      'reason': 'Synthetic fixture declaration; no actual adequacy evidence.'}
                for name in ('heavy_tail', 'overlap', 'common_shock')}

    def test_complete_information_gap_is_no_decision_but_unknown_coverage(self):
        manifest = self.manifest()
        records = [{'world_id': w['id'], 'state': 'INFORMATION_GAP', 'decision': None,
                    'scope_count': 0, 'condition_count': 0, 'covered': None} for w in manifest['worlds']]
        result = count_assessment(manifest, records, {w['id']: 'owned:batch' for w in manifest['worlds']},
                                  self.applicability(manifest))
        self.assertEqual(result['status'], 'NOT_ASSESSED')
        for cohort in result['cohorts']:
            if cohort['criterion'] == 'joint_miscoverage':
                self.assertIsNone(cohort['point'])
            else:
                self.assertEqual(cohort['observed'], 256)
                self.assertEqual(cohort['observed_events'], 0)

    def test_unsupported_family_or_partial_inventory_is_rejected(self):
        config=profile();config.update(targets=[16],worlds_per_cell=256)
        with self.assertRaises(Invalid):make_final_manifest({**assigned(),'primary_count':2},config)
        with self.assertRaises(Invalid):make_final_manifest(assigned(),{**config,'worlds_per_cell':255})
        with self.assertRaises(Invalid):make_final_manifest(assigned(),{**config,'targets':[16,32]})

    def test_technical_failure_is_unavailable_for_every_criterion(self):
        manifest=self.manifest();world=manifest['worlds'][0]
        record={'world_id':world['id'],'state':'TECHNICAL_FAILURE','decision':None,
            'scope_count':None,'condition_count':None,'covered':None}
        result=count_assessment(manifest,[record],{world['id']:'owned:failed-attempt'},self.applicability(manifest))
        self.assertEqual(result['status'],'NOT_ASSESSED')
        for cohort in result['cohorts']:
            self.assertEqual(cohort['observed'],0)
            self.assertIsNone(cohort['point'])

    def test_worst_case_count_envelope_is_checked_without_dropping_stress_cells(self):
        config=profile();config.update(targets=[16],worlds_per_cell=256)
        single=make_final_manifest({**assigned(),'direction':'nondirectional'},config)
        validate_count_envelope(single,self.applicability(single))
        config['specifications'].append({**config['specifications'][0],'mask_mean_block':8})
        double=make_final_manifest(assigned(),config)
        self.assertEqual(len(double['worlds']),1536)
        with self.assertRaises(Invalid):validate_count_envelope(double,self.applicability(double))
        self.assertEqual(len(double['worlds']),1536)


if __name__ == '__main__':
    unittest.main()
