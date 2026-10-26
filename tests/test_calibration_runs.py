"""Owned final series: actual child replay, immutable identity and conservative recovery."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_study_runs as support
from trading_researcher.codec import Invalid
from trading_researcher.errors import Conflict, Denied
from trading_researcher.calibration_runs import CalibrationStudies
from trading_researcher.coordination import Broker


class CalibrationRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        support.StudyRunTests.setUpClass.__func__(cls)
        cls.addClassCleanup(cls.fixture.close)
        cls.plan=cls.op('prepare_evaluation_plan',key='calibration-single-plan',
            compiled_id=cls.execution['body']['compiled_id'],primary_count=1,
            dependence=cls.plan['body']['request']['dependence'])
        cls.diagnostics=cls.op('prepare_information_diagnostics',key='calibration-single-diagnostics',
            plan_id=cls.plan['id'],execution_id=cls.execution['id'],lags=[1,2],limits={'max_seconds':60})
        args=support.StudyRunTests.args(cls,'calibration-development')
        cls.development=cls.op('prepare_information_study',**args)
        for _ in range(3):
            view=cls.op('advance_information_study',study_id=cls.development['id'])
        if view['status']!='COMPLETE':raise AssertionError(view)

    @classmethod
    def op(cls,operation,**args):return cls.broker.call(cls.token,operation,**args)

    def args(self,key):
        config=self.development['body']['manifest']['profile']
        return {'key':key,'development_study_id':self.development['id'],'time_rows':3,
            'seed':771,'budget':deepcopy(config['budget']),'cost_estimate':deepcopy(config['cost_estimate']),
            'applicability':{name:{'status':'not_applicable','cohort_ids':[],
                'reason':'Synthetic lifecycle fixture only; no applicability certification.'}
                for name in ('heavy_tail','overlap','common_shock')}}

    def test_a_actual_final_world_replays_retained_calculator_and_alias_keeps_budget(self):
        args=self.args('final-owned')
        final=self.op('prepare_evaluator_calibration',**args)
        self.assertEqual(final['data_class'],'operations')
        self.assertEqual(final['body']['source_footprint'],self.development['body']['source_footprint'])
        self.assertEqual(len(final['body']['manifest']['worlds']),768)
        from trading_researcher import study_runs
        with patch.object(study_runs,'execute_attempt',side_effect=RuntimeError('Retained final failure')):
            failed=self.op('advance_evaluator_calibration',calibration_id=final['id'])
        self.assertEqual(failed['status'],'READY')
        self.assertEqual(failed['summary']['count_assessment']['status'],'NOT_ASSESSED')
        view=self.op('advance_evaluator_calibration',calibration_id=final['id'])
        self.assertEqual(view['summary']['recorded_worlds'],1,view)
        self.assertEqual(len(view['attempt_artifact_ids']),2)
        attempt=self.op('get_artifact',artifact_id=view['attempt_artifact_ids'][-1])['body']
        self.assertEqual(len(attempt['proofs']),2,attempt['failure'])
        self.assertEqual(view['summary']['count_assessment']['status'],'NOT_ASSESSED')
        self.assertEqual(view['summary']['count_assessment']['input_authentication'],'OWNED_REPLAYED_ATTEMPTS')
        self.assertIsNone(view['n_min']);self.assertFalse(view['scientific_readiness'])
        self.assertEqual(self.op('prepare_evaluator_calibration',**{**args,'key':'final-alias'}),final)
        self.assertEqual(self.op('inspect_evaluator_calibration',calibration_id=final['id']),view)
        for key,value in [('seed',772),('budget',{**args['budget'],'max_compute_ms':310000}),
                          ('applicability',{**args['applicability'],'heavy_tail':{
                              **args['applicability']['heavy_tail'],'reason':'Changed wording'}})]:
            with self.subTest(key=key),self.assertRaises(Conflict):
                self.op('prepare_evaluator_calibration',**{**args,'key':'changed-'+key,key:value})

    def test_b_interruption_retains_full_budget_and_reopen_cannot_replace_draws(self):
        final=self.op('prepare_evaluator_calibration',**self.args('final-recovery-alias'))
        manifest=final['body']['manifest'];limits=manifest['profile']['budget']
        before=self.op('inspect_evaluator_calibration',calibration_id=final['id'])
        world=before['next_world_id']
        with self.broker._transaction():
            self.broker._event('controller','information_study_reserved',study_id=final['id'],reservation={
                'attempt_id':'calibration-orphan','world_id':world,'compute_ms':limits['attempt_compute_ms'],
                'storage_bytes':limits['attempt_storage_bytes']})
        from trading_researcher import calibration_runs
        directory=self.broker.directory;clock=self.broker.clock
        self.broker.close()
        with patch.object(calibration_runs,'source_bundle',return_value={}):
            reopened=Broker(directory,clock=clock)
            type(self).broker=reopened
            type(self).addClassCleanup(reopened.close)
            changed=self.op('inspect_evaluator_calibration',calibration_id=final['id'])
            self.assertEqual(changed['summary']['count_assessment']['reason'],'assessment_source_changed')
        view=self.op('inspect_evaluator_calibration',calibration_id=final['id'])
        self.assertEqual(view['status'],'ORPHAN_UNCERTAIN')
        self.assertEqual(view['budget']['charged_compute_ms'],before['budget']['charged_compute_ms']+limits['attempt_compute_ms'])
        self.assertEqual(self.op('advance_evaluator_calibration',calibration_id=final['id']),view)

    def test_reject_unowned_or_incomplete_development_and_worker_before_read(self):
        args=self.args('invalid-final')
        worker=self.op('register_worker',name='no-final-access',role='discovery',capabilities=['research-record/v1'])['token']
        with self.assertRaises(Denied):self.broker.call(worker,'prepare_evaluator_calibration',**args)
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('premature blob read')):
            with self.assertRaises(Invalid):self.op('prepare_evaluator_calibration',**{**args,'time_rows':4})


if __name__=='__main__':unittest.main()
