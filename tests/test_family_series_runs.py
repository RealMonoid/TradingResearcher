"""Real owned family development, protected final execution and recovery."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from family_run_support import FamilyFixture
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher import study_runs, calibration_runs


class FamilySeriesRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=FamilyFixture();cls.broker=cls.fixture.broker;cls.token=cls.fixture.token
        cls.addClassCleanup(cls.fixture.close)
        estimate={'world_time_rows':3,'observed_compute_ms':10000,'observed_storage_bytes':32*1024*1024,
            'qualification':'Synthetic lifecycle engineering estimate, not a full-series runtime guarantee.'}
        source=cls.op('add_source',body={'schema':'development-study-cost-estimate/1',**estimate},data_class='development')
        cls.profile={'specifications':[cls.fixture.args('unused')['specification']], 'targets':[3],
            'worlds_per_cell':1,'seed':818,'mc_noncoverage':{'numerator':'1','denominator':'100'},
            'outer_noncoverage':{'numerator':'1','denominator':'20'},
            'responses':['a','b'],'patterns':[[0,0],[0,1],[1,1],[2,2]],
            'budget':{'max_compute_ms':600000,'attempt_compute_ms':90000,'max_storage_bytes':4*1024**3,
                'attempt_storage_bytes':256*1024**2,'max_attempts':2},
            'cost_estimate':{'source_ref':source['id'],**estimate}}
        cls.development=cls.op('prepare_family_study',key='family-series-development',plan_id=cls.fixture.plan['id'],
            execution_id=cls.fixture.execution['id'],diagnostics_id=cls.fixture.diagnostics['id'],profile=cls.profile)
        for _ in range(4):view=cls.op('advance_family_study',study_id=cls.development['id'])
        if view['status']!='COMPLETE':raise AssertionError(view)
        for identity in view['attempt_artifact_ids']:
            attempt=cls.op('get_artifact',artifact_id=identity)['body']
            if len(attempt['proofs'])!=2:raise AssertionError(attempt)
        print(json.dumps({'development_series_status':view['status'],'actual_development_worlds':view['summary']['recorded_worlds'],
            'charged_compute_ms':view['budget']['charged_compute_ms'],'charged_storage_bytes':view['budget']['charged_storage_bytes']}))

    @classmethod
    def op(cls,operation,**args):return cls.broker.call(cls.token,operation,**args)

    def args(self,key):
        return {'key':key,'development_study_id':self.development['id'],'time_rows':3,'seed':819,
            'budget':deepcopy(self.profile['budget']),'cost_estimate':deepcopy(self.profile['cost_estimate']),
            'applicability':{name:{'status':'not_applicable','cohort_ids':[],
                'reason':'Synthetic lifecycle declaration; not actual stress applicability evidence.'}
                for name in ('heavy_tail','overlap','common_shock')}}

    def test_a_actual_final_world_retry_is_owned_and_does_not_reset_inventory(self):
        args=self.args('family-final');final=self.op('prepare_family_calibration',**args)
        self.assertEqual(final['data_class'],'operations')
        self.assertEqual(len(final['body']['manifest']['worlds']),1024)
        self.assertEqual(final['body']['source_footprint'],self.development['body']['source_footprint'])
        with patch.object(study_runs,'execute_attempt',side_effect=RuntimeError('recorded family failure')):
            failed=self.op('advance_family_calibration',calibration_id=final['id'])
        self.assertEqual(failed['status'],'READY')
        failed_record=self.op('get_artifact',artifact_id=failed['attempt_artifact_ids'][-1])['body']['outcome']
        self.assertEqual([x['state'] for x in failed_record['components']],['TECHNICAL_FAILURE']*2)
        self.assertIsNone(failed_record['events']['joint_miscoverage'])
        view=self.op('advance_family_calibration',calibration_id=final['id'])
        self.assertEqual(view['summary']['recorded_worlds'],1)
        attempt=self.op('get_artifact',artifact_id=view['attempt_artifact_ids'][-1])['body']
        self.assertEqual(len(attempt['proofs']),2,attempt['failure'])
        self.assertEqual(len(view['attempt_artifact_ids']),2)
        counts=view['summary']['count_assessment']
        self.assertEqual(counts['status'],'NOT_ASSESSED')
        self.assertEqual(counts['input_authentication'],'OWNED_REPLAYED_ATTEMPTS')
        self.assertTrue(all(c['planned']==256 for c in counts['cohorts']))
        self.assertEqual(self.op('prepare_family_calibration',**{**args,'key':'same-final-alias'}),final)
        for field,value in (('seed',820),('budget',{**args['budget'],'max_compute_ms':610000})):
            with self.subTest(field=field),self.assertRaises(Conflict):
                self.op('prepare_family_calibration',**{**args,'key':'no-reset-'+field,field:value})
        print(json.dumps({'final_planned_worlds':1024,'actual_final_worlds':1,'retained_attempts':2,
            'cohorts':len(counts['cohorts']),'count_status':counts['status'],'outcome':attempt['outcome'],
            'charged_compute_ms':view['budget']['charged_compute_ms'],'charged_storage_bytes':view['budget']['charged_storage_bytes']}))

    def test_b_orphan_recovery_preserves_full_family_failure_and_budget(self):
        final=self.op('prepare_family_calibration',**self.args('recovery-alias'))
        before=self.op('inspect_family_calibration',calibration_id=final['id'])
        limits=final['body']['manifest']['profile']['budget']
        with self.broker._transaction():
            self.broker._event('controller','information_study_reserved',study_id=final['id'],reservation={
                'attempt_id':'family-orphan','world_id':before['next_world_id'],
                'compute_ms':limits['attempt_compute_ms'],'storage_bytes':limits['attempt_storage_bytes']})
        directory=self.broker.directory;clock=self.broker.clock;self.broker.close()
        with patch.object(calibration_runs,'source_bundle',return_value={}):
            reopened=Broker(directory,clock=clock);type(self).broker=reopened;type(self).addClassCleanup(reopened.close)
            changed=self.op('inspect_family_calibration',calibration_id=final['id'])
            self.assertEqual(changed['summary']['count_assessment']['reason'],'assessment_source_changed')
        view=self.op('inspect_family_calibration',calibration_id=final['id'])
        self.assertEqual(view['status'],'ORPHAN_UNCERTAIN')
        self.assertEqual(view['budget']['charged_compute_ms'],before['budget']['charged_compute_ms']+limits['attempt_compute_ms'])
        self.assertEqual(self.op('advance_family_calibration',calibration_id=final['id']),view)
        self.assertEqual(view['summary']['count_assessment']['status'],'NOT_ASSESSED')

    def test_operator_and_owned_development_are_required(self):
        worker=self.op('register_worker',name='family-series-denied',role='discovery',capabilities=['research-record/v1'])['token']
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('premature read')):
            with self.assertRaises(Denied):self.broker.call(worker,'prepare_family_calibration',**self.args('denied'))
            with self.assertRaises(Invalid):self.op('prepare_family_calibration',**{**self.args('bad-target'),'time_rows':4})
        for schema in ('family-study-input/1','family-study-attempt/1','family-calibration-input/1','family-calibration-attempt/1'):
            with self.subTest(schema=schema),self.assertRaises(Invalid):
                self.op('add_source',body={'schema':schema},data_class='development')


if __name__=='__main__':unittest.main()
