"""Actual owned execution across explicit resource checkpoints."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from family_run_support import FamilyFixture
from trading_researcher import calibration_runs
from trading_researcher.codec import digest, Invalid
from trading_researcher.errors import Conflict, Denied


class StudyContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=FamilyFixture();cls.addClassCleanup(cls.fixture.close)
        cls.broker=cls.fixture.broker;cls.token=cls.fixture.token

    @classmethod
    def op(cls,operation,**args):return cls.broker.call(cls.token,operation,**args)

    def test_actual_development_and_final_continue_original_worlds(self):
        estimate={'world_time_rows':3,'observed_compute_ms':10000,'observed_storage_bytes':32*1024**2,
            'qualification':'Synthetic fixture only; not a complete calibration cost guarantee.'}
        cost=self.op('add_source',body={'schema':'development-study-cost-estimate/1',**estimate},data_class='development')
        profile={'specifications':[self.fixture.args('unused')['specification']],'targets':[3],
            'worlds_per_cell':1,'seed':818,'mc_noncoverage':{'numerator':'1','denominator':'100'},
            'outer_noncoverage':{'numerator':'1','denominator':'20'},'responses':['a','b'],
            'patterns':[[0,0],[0,1],[1,1],[2,2]],
            'budget':{'max_compute_ms':90000,'attempt_compute_ms':90000,'max_storage_bytes':1024**3,
                'attempt_storage_bytes':256*1024**2,'max_attempts':2},'cost_estimate':{'source_ref':cost['id'],**estimate}}
        study=self.op('prepare_family_study',key='continuation-development',plan_id=self.fixture.plan['id'],
            execution_id=self.fixture.execution['id'],diagnostics_id=self.fixture.diagnostics['id'],profile=profile)
        before_hash=digest(study)
        stopped=self.op('advance_family_study',study_id=study['id'])
        self.assertEqual(stopped['status'],'RESOURCE_STOP')
        request={'key':'development-resources','study_id':study['id'],'expected_checkpoint':stopped['resource_checkpoint'],
            'additional_compute_ms':90000,'additional_storage_bytes':0,
            'rationale':'Continue the same retained synthetic inventory after its initial resource stop.',
            'expected_progress':'Complete the remaining three fixed worlds.',
            'stop_reason':'Stop at this tranche, a failed attempt cap, or another existing guard.'}
        grant=self.op('continue_study',**request)
        self.assertEqual(grant['data_class'],'operations')
        self.assertEqual(self.op('continue_study',**request),grant)
        with self.assertRaises(Conflict):self.op('continue_study',**{**request,'key':'stale-alias'})
        for _ in range(3):view=self.op('advance_family_study',study_id=study['id'])
        self.assertEqual(view['status'],'COMPLETE')
        self.assertEqual(view['budget']['continuation_storage_bytes'],1024**2)
        self.assertEqual(digest(self.op('get_artifact',artifact_id=study['id'])),before_hash)
        self.assertEqual(view['continuation_ids'],[grant['id']])
        self.assertEqual(self.op('continue_study',**request),grant)
        final=self.op('prepare_family_calibration',key='continuation-final',development_study_id=study['id'],
            time_rows=3,seed=819,budget=deepcopy(profile['budget']),cost_estimate=profile['cost_estimate'],
            applicability={name:{'status':'not_applicable','cohort_ids':[],
                'reason':'Synthetic continuation fixture; not an applicability claim.'}
                for name in ('heavy_tail','overlap','common_shock')})
        final_hash=digest(final)
        first=self.op('advance_family_calibration',calibration_id=final['id'])
        self.assertEqual(first['status'],'RESOURCE_STOP')
        final_request={**request,'key':'final-resources','study_id':final['id'],
            'expected_checkpoint':first['resource_checkpoint'],'expected_progress':'Execute the next fixed final world.'}
        with patch.object(calibration_runs,'source_bundle',return_value={}):
            with self.assertRaises((Invalid,Conflict)):self.op('continue_study',**final_request)
        self.assertEqual(self.op('inspect_family_calibration',calibration_id=final['id']),first)
        grant2=self.op('continue_study',**final_request)
        second=self.op('advance_family_calibration',calibration_id=final['id'])
        self.assertEqual(second['summary']['recorded_worlds'],2)
        self.assertEqual(second['summary']['count_assessment']['status'],'NOT_ASSESSED')
        self.assertEqual(digest(self.op('get_artifact',artifact_id=final['id'])),final_hash)
        for current,observed,expected_count in ((study,view,4),(final,second,2)):
            records=[self.op('get_artifact',artifact_id=i) for i in observed['attempt_artifact_ids']]
            self.assertEqual(len(records),expected_count)
            self.assertEqual([r['body']['world_id'] for r in records],
                [w['id'] for w in current['body']['manifest']['worlds'][:expected_count]])
            self.assertTrue(all(len(r['body']['proofs'])==2 for r in records))
            self.assertEqual(records[-1]['body']['continuation_id'],observed['continuation_ids'][-1])
            self.assertIn(observed['continuation_ids'][-1],records[-1]['source_refs'])
            self.assertFalse(observed['scientific_readiness']);self.assertIsNone(observed['n_min'])
        self.assertEqual(grant2['source_refs'],[final['id']])
        self.assertEqual(final['body']['development_continuation_ids'],[grant['id']])
        evidence=self.op('add_source',body={'defect':'Synthetic resource decision revocation fixture.'},data_class='development')
        self.op('revoke_dependency',key='development-resource-defect',dependency_id=grant['id'],
            reason='Synthetic technical revocation; no scientific conclusion.',evidence_refs=[evidence['id']])
        self.assertEqual(self.op('inspect_dependency_use',artifact_id=final['id'])['status'],'INVALIDATED_BY_DEPENDENCY')
        with self.assertRaises((Invalid,Conflict,Denied)):
            self.op('advance_family_calibration',calibration_id=final['id'])
        print(json.dumps({'actual_development_worlds':4,'actual_final_worlds':2,
            'development_budget':view['budget'],'final_budget':second['budget'],
            'final_planned_worlds':len(final['body']['manifest']['worlds']),
            'final_count_status':second['summary']['count_assessment']['status']}))


if __name__=='__main__':unittest.main()
