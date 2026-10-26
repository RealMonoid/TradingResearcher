"""Real retained bindings and calculations cannot outrun technical revocation."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_study_runs as study_support
from trading_researcher import binding, evaluation_plans, study_runs
from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied
from trading_researcher.storage import restore_bundle


class RevocationBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        study_support.StudyRunTests.setUpClass()
        cls.base=study_support.StudyRunTests
        cls.addClassCleanup(cls.base.tearDownClass)
        cls.backup=cls.base.fixture.root/'revocation-test-baseline'
        assert cls.base.op('backup_bundle',destination=str(cls.backup))['status']=='PASS'

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        restored=self.root/'registry'
        self.assertEqual(restore_bundle(self.backup,restored,self.base.broker.directory/'operator.key')['status'],'PASS')
        self.broker=Broker(restored);self.addCleanup(self.broker.close)
        self.token=self.broker.admin_token
        self.plan,self.execution,self.diagnostics,self.cost=self.base.plan,self.base.execution,self.base.diagnostics,self.base.cost
        self.compiled=self.op('get_artifact',artifact_id=self.plan['body']['request']['compiled_id'])
        self.evidence=self.op('add_source',body={'defect':'Synthetic revocation integration test'},data_class='operations')

    def op(self,name,**args):return self.broker.call(self.token,name,**args)
    args=study_support.StudyRunTests.args

    def revoke(self,identity):
        return self.op('revoke_dependency',key='defect-'+identity,dependency_id=identity,
            reason='Synthetic defect; not a real scientific finding',evidence_refs=[self.evidence['id']])

    def test_revoked_compiler_cannot_run_under_a_new_package_or_certificate_date(self):
        self.revoke(self.compiled['body']['source_package_id'])
        with patch.object(binding,'run_child',side_effect=AssertionError('Revoked compiler executed')) as child:
            result=self.op('compile_hypothesis',**self.compiled['body']['dependency_arguments'])
        self.assertFalse(child.called)
        self.assertEqual(result['body']['status'],'COMPILATION_GAP')
        self.assertEqual(self.op('get_artifact',artifact_id=self.compiled['id']),self.compiled)

    def test_other_declared_diagnostic_has_its_own_compiler_dependency(self):
        alternate=self.root/'alternate';(alternate/'trading_researcher').mkdir(parents=True)
        (alternate/binding.DRIVER).write_bytes((binding.ROOT/binding.DRIVER).read_bytes()+b'\n# Synthetic alternate version.\n')
        with patch.object(binding,'ROOT',alternate):
            compiled=self.op('compile_hypothesis',**self.compiled['body']['dependency_arguments'])
        self.assertEqual(compiled['body']['status'],'COMPILED',compiled['body'])
        execution=self.op('execute_development',compiled_id=compiled['id'])
        self.assertEqual(execution['body']['status'],'DESCRIPTIVE_EXECUTION')
        request={**self.plan['body']['request'],'key':'two-diagnostics',
            'dependence':{**self.plan['body']['request']['dependence'],
                'development_refs':[self.execution['id'],execution['id']]}}
        plan=self.op('prepare_evaluation_plan',**request)
        revoked=self.revoke(compiled['body']['source_package_id'])
        self.assertIn(plan['id'],revoked['body']['affected_artifact_ids'])
        self.assertNotIn(self.compiled['id'],revoked['body']['affected_artifact_ids'])
        self.assertEqual(self.op('inspect_dependency_use',artifact_id=self.compiled['id'])['status'],'NOT_REVOKED')
        self.assertEqual(self.op('inspect_evaluation_plan',plan_id=plan['id'])['dependency_use']['status'],'INVALIDATED_BY_DEPENDENCY')
        self.assertEqual(self.op('prepare_evaluation_plan',**request),plan)
        with patch.object(evaluation_plans,'run_plan_child',side_effect=AssertionError('Invalid diagnostic launched')) as child:
            with self.assertRaises(Denied):self.op('prepare_evaluation_plan',**{**request,'key':'new-use'})
        self.assertFalse(child.called)

    def test_revocation_during_plan_calculation_preserves_only_interrupted_input(self):
        original=evaluation_plans.run_plan_child;calls=0
        def revoke_during(*args,**kwargs):
            nonlocal calls
            result=original(*args,**kwargs);calls+=1
            if calls==1:self.revoke(self.compiled['body']['data_snapshot_id'])
            return result
        with patch.object(evaluation_plans,'run_plan_child',side_effect=revoke_during):
            with self.assertRaises(Denied):
                self.op('prepare_evaluation_plan',**{**self.plan['body']['request'],'key':'race'})
        attempt=self.op('inspect_bound_computations')['attempts'][0]
        self.assertEqual(attempt['state'],'INTERRUPTED')
        self.assertIsNotNone(attempt['retained_input_id'])
        self.assertIsNone(attempt['artifact_id'])

    def test_revocation_during_execution_prevents_completed_result_commit(self):
        original=binding.run_child
        def revoke_during(bundle,mode,*args,**kwargs):
            result=original(bundle,mode,*args,**kwargs)
            if mode=='execute':self.revoke(self.compiled['body']['dependency_arguments']['feature_certificate_id'])
            return result
        with patch.object(binding,'run_child',side_effect=revoke_during):
            result=self.op('execute_development',compiled_id=self.compiled['id'])
        self.assertNotEqual(result['body']['status'],'DESCRIPTIVE_EXECUTION')
        self.assertFalse(result['body']['scientific_readiness'])
        self.assertEqual(self.op('get_artifact',artifact_id=self.execution['id']),self.execution)

    def test_revocation_during_real_study_retains_charged_failure_not_valid_world(self):
        study=self.op('prepare_information_study',**self.args('revocation-race'))
        original=study_runs.execute_attempt
        def revoke_during(*args,**kwargs):
            result=original(*args,**kwargs)
            self.revoke(self.compiled['body']['data_snapshot_id'])
            return result
        with patch.object(study_runs,'execute_attempt',side_effect=revoke_during):
            view=self.op('advance_information_study',study_id=study['id'])
        attempt=self.op('get_artifact',artifact_id=view['attempt_artifact_ids'][-1])['body']
        self.assertEqual(attempt['outcome']['state'],'TECHNICAL_FAILURE')
        self.assertIsNone(attempt['outcome']['decision'])
        self.assertGreater(attempt['settlement']['compute_ms'],0)
        self.assertIsNotNone(attempt['result'])
        self.assertEqual(self.op('inspect_dependency_use',artifact_id=study['id'])['status'],'INVALIDATED_BY_DEPENDENCY')


if __name__=='__main__':unittest.main()
