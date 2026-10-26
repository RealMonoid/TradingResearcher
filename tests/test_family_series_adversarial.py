"""Independent family-series boundary tests; synthetic host metadata is explicit.

Mocked calculators isolate orchestration. They are not genuine retained-source
replay or scientific evidence; the separate owned lifecycle fixture covers that.
"""
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import patch

import test_family_study_oracles as oracle
from trading_researcher import calibration_runs, study_runs
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.family_study import make_manifest, make_final_manifest, outcome_record, count_assessment
from trading_researcher.family_study_runs import FamilyStudies, FamilyCalibrationStudies


def partial_record(manifest, world):
    result = oracle.record(manifest, world)
    result['components'][0].update(covered=False, decision='SUPPORTED_INITIAL')
    result['components'][1].update(state='TECHNICAL_FAILURE', covered=None, decision=None)
    result['state'] = 'TECHNICAL_FAILURE'
    result['events'] = oracle.expected_events(result['components'], oracle._read_rational(manifest['assigned']['delta']))
    return result


class FamilySeriesAdversarialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.broker = Broker(temporary.name); self.addCleanup(self.broker.close)

    def owned(self, schema, data_class='development', *, refs=(), exposure=(), **body):
        with self.broker._transaction():
            return self.broker._save_artifact({'version':'local-artifact/1', 'creator':'controller',
                'origin':'controller', 'data_class':data_class, 'source_refs':list(refs), 'exposure':list(exposure),
                'authority':'synthetic_boundary_fixture_only', 'body':{'schema':schema, **body}})

    def test_known_union_event_survives_partial_sibling_in_pure_count_mapping(self):
        assigned, profile = oracle.family_inputs(final=True)
        manifest = make_final_manifest(assigned, profile); world = manifest['worlds'][0]
        record = partial_record(manifest, world)
        self.assertTrue(record['events']['joint_miscoverage'])
        self.assertTrue(record['events']['false_support'])
        result = count_assessment(manifest, [record], oracle.sources([record]), oracle.applicability())
        for criterion in ('joint_miscoverage', 'false_support'):
            cohort = next(c for c in result['cohorts'] if c['cohort_id'] == 'spec-0/pattern-0/' + criterion)
            self.assertEqual(cohort['observed'], 1)
            self.assertEqual(cohort['observed_events'], 1)
            self.assertEqual(cohort['unavailable_indices'], [])
        self.assertEqual(result['status'], 'NOT_ASSESSED')
        self.assertEqual(result['input_authentication'], 'UNVERIFIED')

    def test_collision_inventory_preserves_real_ids_of_all_retained_input_kinds(self):
        records = []
        for index, schema in enumerate(('information-study-input/1', 'evaluator-calibration-input/1',
                                       'family-study-input/1', 'family-calibration-input/1')):
            records.append(self.owned(schema, manifest={'worlds':[{'id':str(index),
                'population_seed':index + 1, 'bootstrap_seed':index + 11}]}))
        records.append(self.owned('population-world-input/1', payload={'seed':101}))
        records.append(self.owned('population-family-input/1', payload={'seed':201, 'bootstrap_seed':202}))
        found = list(FamilyCalibrationStudies(self.broker)._recorded_calibration_worlds())
        self.assertEqual({item['id'] for item, _ in found}, {item['id'] for item in records})
        standalone = {item['id']: worlds for item, worlds in found if item['id'] in {r['id'] for r in records[-2:]}}
        self.assertEqual(standalone[records[-2]['id']][0]['population_seed'], 101)
        self.assertEqual(standalone[records[-1]['id']][0]['bootstrap_seed'], 202)

    def test_unreplayed_partial_calculation_is_retained_but_settled_all_unavailable(self):
        assigned, profile = oracle.family_inputs()
        manifest = make_manifest(assigned, profile); world = manifest['worlds'][0]
        payload = {'case_blob':{'sha256':'a' * 64, 'size':0}}
        request = {'key':'synthetic-partial', 'execution_id':'synthetic-execution'}
        study = self.owned('family-study-input/1', manifest=manifest, payload=payload,
            request=request, initial_storage_bytes=0)
        runner = FamilyStudies(self.broker)
        partial = partial_record(manifest, world)
        calculation = {'world_id':world['id'], 'outcome':partial, 'scientific_readiness':False,
                       'classification_permitted':False, 'n_min':None}
        with patch.object(runner, '_study_inputs', return_value=(payload, manifest, [], [])), \
                patch.object(runner, '_load_study_source', return_value={}), \
                patch.object(self.broker, '_read_blob_bytes', return_value=b''), \
                patch.object(self.broker, '_require_usable_dependencies', return_value=None), \
                patch.object(study_runs, 'execute_attempt', return_value=(calculation, [{'kind':'first-child-only'}])):
            view = runner._advance_information_study_external(self.broker.admin_token, {'study_id':study['id']})
        attempt = self.broker._artifact(view['attempt_artifact_ids'][0])['body']
        self.assertEqual(attempt['result'], calculation)
        self.assertEqual(len(attempt['proofs']), 1)
        self.assertTrue(all(c['state'] == 'TECHNICAL_FAILURE' for c in attempt['outcome']['components']))
        self.assertIsNone(attempt['outcome']['events']['joint_miscoverage'])
        self.assertIsNone(attempt['outcome']['events']['false_support'])
        self.assertEqual(view['summary']['recorded_worlds'], 1)
        self.assertFalse(view['summary']['complete'])

    def test_final_schemas_and_both_ancestry_edges_are_denied_even_private_exception(self):
        for schema in ('family-calibration-input/1', 'family-calibration-attempt/1'):
            final = self.owned(schema, 'operations')
            for edge in ('refs', 'exposure'):
                wrapper = self.owned('ordinary-wrapper/1', **{edge:[final['id']]})
                for private_exception in (False, True):
                    with self.subTest(schema=schema, edge=edge, private=private_exception), self.assertRaises(Denied):
                        self.broker._deny_final_calibration_ancestry(wrapper, allow_private_targets=private_exception)

    def test_all_family_series_schemas_are_reserved_from_supplied_sources(self):
        for schema in ('family-study-input/1', 'family-study-attempt/1',
                       'family-calibration-input/1', 'family-calibration-attempt/1'):
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                self.broker.call(self.broker.admin_token, 'add_source', body={'schema':schema}, data_class='development')

    def test_worker_denied_all_six_series_operations_before_artifact_reads(self):
        worker = self.broker.call(self.broker.admin_token, 'register_worker', name='family-research-worker',
            role='discovery', capabilities=['research-record/v1'])['token']
        with patch.object(self.broker, '_artifact', side_effect=AssertionError('Worker reached private artifact read')):
            for final in (False, True):
                suffix = 'calibration' if final else 'study'; key = 'calibration_id' if final else 'study_id'
                for verb in ('prepare', 'advance', 'inspect'):
                    args = {} if verb == 'prepare' else {key:'not-authorized'}
                    with self.subTest(op=verb + suffix), self.assertRaises(Denied):
                        self.broker.call(worker, verb + '_family_' + suffix, **args)

    def test_failure_factory_preserves_frozen_truths_and_invalidates_every_response(self):
        assigned, profile = oracle.family_inputs()
        manifest = make_manifest(assigned, profile); world = manifest['worlds'][-1]
        prior = oracle.record(manifest, world); before = deepcopy(prior)
        for runner in (FamilyStudies(self.broker), FamilyCalibrationStudies(self.broker)):
            failed = runner._study_failed_outcome(manifest, world, prior)
            self.assertEqual([c['truth'] for c in failed['components']], [c['truth'] for c in prior['components']])
            self.assertTrue(all(c['state'] == 'TECHNICAL_FAILURE' for c in failed['components']))
            self.assertTrue(all(value is None for value in failed['events']['detections'].values()))
        self.assertEqual(prior, before)

    def test_family_identity_ignores_response_relabel_but_keeps_numerical_patterns(self):
        assigned, profile = oracle.family_inputs(3)
        manifest = make_manifest(assigned, profile)
        runner = FamilyCalibrationStudies(self.broker)
        before = deepcopy(manifest)
        renamed = deepcopy(manifest)
        renamed['profile']['responses'] = ['alpha', 'beta', 'gamma']
        renamed['profile']['patterns'] = sorted([[p[i] for i in (2, 0, 1)] for p in profile['patterns']])
        self.assertEqual(runner._calibration_identity_extra(manifest), runner._calibration_identity_extra(renamed))
        changed = deepcopy(manifest)
        changed['profile']['patterns'][1] = [0, 2, 2]
        self.assertNotEqual(runner._calibration_identity_extra(manifest), runner._calibration_identity_extra(changed))
        self.assertEqual(manifest, before)

    def test_final_request_alias_cannot_reset_seed_budget_cost_or_applicability(self):
        runner = FamilyCalibrationStudies(self.broker)
        request = {'key':'original', 'development_study_id':'original-development', 'seed':12,
                   'budget':{'max_attempts':2}, 'cost_estimate':{'source_ref':'estimate'},
                   'time_rows':16, 'applicability':oracle.applicability()}
        existing = {'body':{'request':request}}
        alias = {**request, 'key':'alias', 'development_study_id':'equivalent-development'}
        runner._study_existing_request(existing, alias)
        for name, value in [('seed', 13), ('budget', {'max_attempts':3}),
                            ('cost_estimate', {'source_ref':'new-estimate'}), ('applicability', {})]:
            with self.subTest(field=name), self.assertRaises(Conflict):
                runner._study_existing_request(existing, {**alias, name:value})

    def test_stale_assessment_source_refuses_new_execution_and_new_count_interpretation(self):
        assigned, profile = oracle.family_inputs(final=True)
        manifest = make_final_manifest(assigned, profile)
        study = {'body':{'manifest':manifest, 'target_basis':'studied_fixture',
                         'assessment_source_footprint':calibration_runs.LOADED_SOURCE}}
        runner = FamilyCalibrationStudies(self.broker)
        with patch.object(calibration_runs, 'source_bundle', return_value={}):
            with self.assertRaises(Invalid):
                runner._study_before_execute(study)
            summary = runner._study_summary(study, [], [])
        self.assertEqual(summary['count_assessment']['status'], 'NOT_ASSESSED')
        self.assertEqual(summary['count_assessment']['reason'], 'assessment_source_changed')


if __name__ == '__main__':
    unittest.main()
