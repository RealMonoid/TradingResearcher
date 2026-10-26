"""Owned finite study flow, real child replay and durable budget boundaries."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_population_runs as population_tests
from test_information_study import profile
from trading_researcher.codec import Invalid
from trading_researcher.errors import Conflict, Denied


class StudyRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        population_tests.PopulationRunTests.setUpClass()
        cls.fixture=population_tests.PopulationRunTests.fixture;cls.broker=cls.fixture.broker;cls.token=cls.fixture.token
        cls.plan=population_tests.PopulationRunTests.plan;cls.execution=population_tests.PopulationRunTests.execution
        cls.diagnostics=population_tests.PopulationRunTests.diagnostics
        estimate=profile()['cost_estimate']
        cls.cost=cls.op('add_source',body={'schema':'development-study-cost-estimate/1',
            **{k:v for k,v in estimate.items() if k!='source_ref'}},data_class='development')

    @classmethod
    def op(cls,operation,**args):return cls.broker.call(cls.token,operation,**args)
    @classmethod
    def tearDownClass(cls):cls.fixture.close()

    def args(self,key):
        config=profile();config['targets']=[3];config['worlds_per_cell']=1
        config['cost_estimate']['source_ref']=self.cost['id']
        config['budget'].update(max_compute_ms=300000,attempt_compute_ms=60000,
            max_storage_bytes=1024**3,attempt_storage_bytes=128*1024**2)
        # Different tests explicitly bind different profiles; key aliases alone
        # must not reset an already prepared study or its accounting.
        config['seed']=sum(map(ord,key))
        return {'key':key,'plan_id':self.plan['id'],'execution_id':self.execution['id'],
            'diagnostics_id':self.diagnostics['id'],'profile':config}

    def test_complete_owned_grid_uses_real_children_and_reuses_alias_budget(self):
        args=self.args('complete');study=self.op('prepare_information_study',**args)
        self.assertEqual(self.op('prepare_information_study',**args),study)
        self.assertEqual(self.op('prepare_information_study',**{**args,'key':'same-study-alias'}),study)
        with self.assertRaises(Conflict):self.op('prepare_information_study',**{**self.args('changed'),'key':'same-study-alias'})
        manifest=study['body']['manifest'];self.assertEqual(len(manifest['worlds']),3)
        self.assertIsNone(self.op('inspect_information_study',study_id=study['id'])['summary']['candidate_time_rows'])
        for index in range(3):
            view=self.op('advance_information_study',study_id=study['id'])
            failures=[self.op('get_artifact',artifact_id=i)['body']['failure'] for i in view['attempt_artifact_ids']]
            self.assertEqual(view['summary']['recorded_worlds'],index+1,(view['status'],failures))
        self.assertEqual(view['status'],'COMPLETE',view)
        self.assertTrue(view['summary']['complete']);self.assertIsNone(view['n_min'])
        self.assertFalse(view['scientific_readiness'])
        self.assertEqual(self.op('advance_information_study',study_id=study['id']),view)
        for identity in view['attempt_artifact_ids']:
            attempt=self.op('get_artifact',artifact_id=identity)['body']
            self.assertEqual(len(attempt['proofs']),2)
            self.assertGreater(attempt['settlement']['storage_bytes'],0)
            if attempt['result']['bootstrap']['status']!='INPUT_GAP':
                self.assertEqual([case['attempted'] for case in attempt['result']['bootstrap']['cases']],[19999]*3)
            self.assertIn('generate/stream.jsonl',attempt['output_blobs'])

    def test_failure_is_retained_and_retry_reuses_manifest_source_and_seeds(self):
        from trading_researcher import study_runs
        study=self.op('prepare_information_study',**self.args('failure'))
        with patch.object(study_runs,'execute_attempt',side_effect=RuntimeError('fixed failure')):
            view=self.op('advance_information_study',study_id=study['id'])
        self.assertEqual(view['status'],'READY')
        self.assertEqual(view['summary']['cells'][0]['states']['TECHNICAL_FAILURE'],1)
        self.assertFalse(view['summary']['complete'])
        original=view['next_world_id']
        with patch.object(study_runs,'source_bundle',side_effect=AssertionError('fresh source used')):
            view=self.op('advance_information_study',study_id=study['id'])
        self.assertNotEqual(view['next_world_id'],original)
        self.assertEqual(view['budget']['attempts_per_world'][original],2)
        self.assertEqual(len(view['attempt_artifact_ids']),2)

    def test_unowned_protected_cost_and_worker_requests_fail_before_blob_reads(self):
        args=self.args('authority')
        worker=self.op('register_worker',name='study-no-authority',role='discovery',capabilities=['research-record/v1'])['token']
        with self.assertRaises(Denied):self.broker.call(worker,'prepare_information_study',**args)
        source=self.op('add_source',body={'not':'diagnostics'},data_class='development')
        protected=self.op('add_source',body={'cost':'protected'},data_class='assessment')
        contaminated=self.op('add_source',body=self.cost['body'],data_class='development',exposure=[protected['id']])
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('premature read')):
            with self.assertRaises(Denied):self.op('prepare_information_study',**{**args,'diagnostics_id':source['id']})
            args['profile']['cost_estimate']['source_ref']=contaminated['id']
            with self.assertRaises(Denied):self.op('prepare_information_study',**args)
        for schema in ('information-study-input/1','development-information-study-attempt/1'):
            with self.assertRaises(Invalid):self.op('add_source',body={'schema':schema},data_class='development')

    def test_unsettled_recovery_charges_full_reservation_and_blocks_replacement(self):
        study=self.op('prepare_information_study',**self.args('orphan'));world=study['body']['manifest']['worlds'][0]
        limits=study['body']['manifest']['profile']['budget']
        with self.broker._transaction():
            self.broker._event('controller','information_study_reserved',study_id=study['id'],reservation={
                'attempt_id':'orphan-attempt','world_id':world['id'],'compute_ms':limits['attempt_compute_ms'],
                'storage_bytes':limits['attempt_storage_bytes']})
            self.broker._event('controller','bound_computation_started',attempt_id='orphan-attempt',kind='information_study',
                input_ref=self.execution['id'],retained_input_id=study['id'])
        with self.assertRaises(Conflict):self.op('advance_information_study',study_id=study['id'])
        self.broker._recover_bound_computations();self.broker._recover_information_studies()
        view=self.op('inspect_information_study',study_id=study['id'])
        self.assertEqual(view['status'],'ORPHAN_UNCERTAIN')
        self.assertEqual(view['budget']['charged_compute_ms'],limits['attempt_compute_ms'])
        self.assertEqual(view['budget']['charged_storage_bytes'],limits['attempt_storage_bytes']+study['body']['initial_storage_bytes'])
        self.assertEqual(self.op('advance_information_study',study_id=study['id']),view)


if __name__=='__main__':unittest.main()
