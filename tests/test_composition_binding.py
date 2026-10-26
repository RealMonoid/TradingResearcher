"""Complete owned composition, plan integration, revocation and recovery paths."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import test_evaluation_plans as plan_support
from trading_researcher import composition, evaluation_plans
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied
from trading_researcher.storage import restore_bundle


class CompositionBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan_support.EvaluationPlanTests.setUpClass()
        cls.base=plan_support.EvaluationPlanTests
        cls.addClassCleanup(cls.base.tearDownClass)
        cls.certificate=cls.base.broker.call(cls.base.token,'certify_composition',compiled_id=cls.base.compiled['id'])
        assert cls.certificate['body']['status']=='CONFORMANT',cls.certificate['body']
        cls.backup=cls.base.fixture.root/'composition-baseline'
        assert cls.base.broker.call(cls.base.token,'backup_bundle',destination=str(cls.backup))['status']=='PASS'

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        restored=Path(self.temp.name)/'registry'
        self.assertEqual(restore_bundle(self.backup,restored,self.base.broker.directory/'operator.key')['status'],'PASS')
        self.broker=Broker(restored);self.addCleanup(self.broker.close)
        self.token=self.broker.admin_token
        self.compiled,self.execution=self.base.compiled,self.base.execution

    def op(self,operation,**args):return self.broker.call(self.token,operation,**args)

    def request(self,key='plan'):
        return {**plan_support.EvaluationPlanTests.arguments(self,key),'composition_certificate_id':self.certificate['id']}

    def revoke(self,identity):
        evidence=self.op('add_source',body={'defect':'Synthetic test only'},data_class='operations')
        return self.op('revoke_dependency',key='revoke-'+identity,dependency_id=identity,
            reason='Synthetic defect',evidence_refs=[evidence['id']])

    def test_real_certificate_closes_only_composition_gate_and_preserves_history(self):
        plan=self.op('prepare_evaluation_plan',**self.request())
        current=self.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertEqual(current['composition']['composition_conformance'],'SATISFIED')
        self.assertNotIn('composition_conformance',current['current_remaining_gates'])
        self.assertEqual(current['current_remaining_gates'],[g for g in plan['body']['plan']['remaining_gates'] if g!='composition_conformance'])
        self.assertIn('composition_conformance',plan['body']['plan']['remaining_gates'])
        self.assertFalse(current['scientific_readiness'])
        capsule=self.op('get_artifact',artifact_id=plan['body']['input_capsule_id'])
        self.assertEqual(capsule['body']['composition_at_preparation'],plan['body']['composition_at_preparation'])
        self.assertIn(self.certificate['id'],plan['exposure'])
        self.assertEqual(self.op('get_artifact',artifact_id=plan['id']),plan)

    def test_worker_cannot_certify_or_inspect(self):
        token=self.op('register_worker',name='untrusted',role='executor',capabilities=[])['token']
        for operation,args in [('certify_composition',{'compiled_id':self.compiled['id']}),
                ('composition_certificate_status',{'certificate_id':self.certificate['id']})]:
            with self.subTest(operation=operation),self.assertRaises(Denied):self.broker.call(token,operation,**args)

    def test_changed_compiled_controls_cannot_reuse_certificate(self):
        changed=self.op('compile_hypothesis',**{**self.compiled['body']['dependency_arguments'],'max_steps':9999})
        self.assertEqual(changed['body']['status'],'COMPILED')
        with self.assertRaises(Invalid):
            self.op('prepare_evaluation_plan',**{**self.request(),'compiled_id':changed['id']})

    def test_revocation_reopens_gate_without_rewriting_certificate_or_plan(self):
        plan=self.op('prepare_evaluation_plan',**self.request())
        revoked=self.revoke(self.certificate['body']['source_package_id'])
        self.assertIn(plan['id'],revoked['body']['affected_artifact_ids'])
        current=self.op('inspect_evaluation_plan',plan_id=plan['id'])
        self.assertEqual(current['composition']['status'],'INVALIDATED_BY_DEPENDENCY')
        self.assertIn('composition_conformance',current['current_remaining_gates'])
        self.assertEqual(self.op('prepare_evaluation_plan',**self.request()),plan)
        self.assertEqual(self.op('get_artifact',artifact_id=self.certificate['id']),self.certificate)
        with patch.object(composition,'run_composition_child',side_effect=AssertionError('Revoked validator launched')) as child:
            result=self.op('certify_composition',compiled_id=self.compiled['id'])
        self.assertFalse(child.called)
        self.assertEqual(result['body']['status'],'CERTIFICATION_GAP')

    def test_cancellation_preserves_exact_input_and_restart_history(self):
        with patch.object(composition,'run_composition_child',side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):self.op('certify_composition',compiled_id=self.compiled['id'])
        attempt=self.op('inspect_bound_computations')['attempts'][0]
        self.assertEqual(attempt['state'],'INTERRUPTED')
        capsule=self.op('get_artifact',artifact_id=attempt['retained_input_id'])
        self.assertEqual(capsule['body']['compiled_id'],self.compiled['id'])
        directory=self.broker.directory;self.broker.close()
        self.broker=Broker(directory);self.addCleanup(self.broker.close);self.token=self.broker.admin_token
        self.assertEqual(self.op('get_artifact',artifact_id=capsule['id']),capsule)
        self.assertEqual(self.op('inspect_bound_computations')['pending'],0)

    def test_revocation_during_check_retains_gap_and_closes_attempt(self):
        original=composition.run_composition_child
        def revoke_during(*args,**kwargs):
            result=original(*args,**kwargs)
            self.revoke(self.compiled['body']['source_package_id'])
            return result
        with patch.object(composition,'run_composition_child',side_effect=revoke_during):
            result=self.op('certify_composition',compiled_id=self.compiled['id'])
        self.assertEqual(result['body']['status'],'CERTIFICATION_GAP')
        self.assertIsNotNone(result['body']['report'])
        self.assertEqual(self.op('inspect_bound_computations')['pending'],0)

    def test_backup_replay_uses_exact_bound_sources_without_loading_market_rows(self):
        self.assertEqual(self.op('get_artifact',artifact_id=self.certificate['id']),self.certificate)
        with patch.object(self.broker,'_load_reference_data',side_effect=AssertionError('Market row access')):
            replay=self.op('certify_composition',compiled_id=self.compiled['id'])
        self.assertEqual(replay['body']['status'],'CONFORMANT')
        self.assertEqual(replay['body']['report']['result'],self.certificate['body']['report']['result'])

    def test_changed_expectations_are_denied_before_child(self):
        with patch.object(composition,'FIXTURE_SHA256','0'*64),patch.object(composition,'run_composition_child') as child:
            with self.assertRaises(Invalid):self.op('certify_composition',compiled_id=self.compiled['id'])
        self.assertFalse(child.called)

    def test_malformed_child_report_cannot_issue_conformance(self):
        with patch.object(composition,'run_composition_child',return_value={'result':{'scientific_readiness':True}}):
            result=self.op('certify_composition',compiled_id=self.compiled['id'])
        self.assertEqual(result['body']['status'],'CERTIFICATION_GAP')
        self.assertFalse(result['body']['scientific_readiness'])

    def test_plan_commit_rechecks_certificate_after_child_and_retains_interruption(self):
        original=evaluation_plans.run_plan_child;calls=0
        def revoke_during(*args,**kwargs):
            nonlocal calls
            result=original(*args,**kwargs);calls+=1
            if calls==1:self.revoke(self.certificate['id'])
            return result
        with patch.object(evaluation_plans,'run_plan_child',side_effect=revoke_during):
            with self.assertRaises(Invalid):self.op('prepare_evaluation_plan',**self.request('race'))
        attempt=self.op('inspect_bound_computations')['attempts'][0]
        self.assertEqual(attempt['state'],'INTERRUPTED')
        self.assertIsNotNone(attempt['retained_input_id'])
        self.assertIsNone(attempt['artifact_id'])


if __name__=='__main__':unittest.main()
