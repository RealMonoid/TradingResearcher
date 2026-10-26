"""Owned scientific-plan preparation retains gaps and cannot grant outcome access."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.coordination import Broker, Invalid, Denied, Conflict
from binding_support import BindingFixture


class PlanAdmissionTests(unittest.TestCase):
    def test_admission_requires_owned_operation_and_complete_request(self):
        with tempfile.TemporaryDirectory() as directory:
            broker=Broker(directory)
            try:
                with self.assertRaises(Invalid):
                    broker.call(broker.admin_token,'prepare_evaluation_plan',key='missing')
                with self.assertRaises(Invalid):
                    broker.call(broker.admin_token,'add_source',body={'schema':'evaluation-plan/1'},data_class='development')
            finally:broker.close()


class EvaluationPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=BindingFixture()
        cls.broker,cls.token=cls.fixture.broker,cls.fixture.token
        candidate=deepcopy(cls.fixture.base['candidate'])
        candidate['estimand']['unit']='ratio'
        candidate['outcome']['scale']='binary_probability'
        candidate['outcome']['program']['expression']={'op':'literal','type':'boolean','unit':None,'value':True}
        candidate['parameter_origins'].append({'path':'/outcome/program/expression/value',
            'basis':'preexisting_specification','source_refs':[],'rationale':'Synthetic infrastructure input only'})
        case={'change':{'candidate':candidate,'original_idea_text':'Synthetic Boolean outcome fixture; not a discovered market claim.'}}
        formalization=cls.fixture.create_formalization(case)
        cls.compiled=cls.fixture.compile(formalization,case)
        assert cls.compiled['body']['status']=='COMPILED',cls.compiled['body']
        cls.execution=cls.broker.call(cls.token,'execute_development',compiled_id=cls.compiled['id'])
        assert cls.execution['body']['status']=='DESCRIPTIVE_EXECUTION',cls.execution['body']

    @classmethod
    def tearDownClass(cls):cls.fixture.close()

    def arguments(self,key='plan'):
        return {'key':key,'compiled_id':self.compiled['id'],'primary_count':2,
            'dependence':{'base_length':4,'rationale':'Synthetic declared dependence design; scientific adequacy remains pending.',
                'development_refs':[self.execution['id']],
                'randomness':{'algorithm':'fixture-generator','version':'1','seed':17}}}

    def test_bound_plan_is_durable_idempotent_and_retains_incomplete_gates(self):
        args=self.arguments()
        with patch.object(self.broker,'_load_reference_data',side_effect=AssertionError('Plan preparation read outcomes')):
            plan=self.broker.call(self.token,'prepare_evaluation_plan',**args)
        self.assertEqual(plan['body']['status'],'POLICY_DRAFT',plan['body'])
        draft=plan['body']['plan']
        self.assertEqual(draft['effect_criterion']['delta'],{'numerator':'1','denominator':'20'})
        self.assertEqual(draft['family_policy']['marginal_noncoverage'],{'numerator':'1','denominator':'40'})
        self.assertEqual(draft['dependence_design']['sensitivity_lengths'],[2,4,8])
        self.assertIsNone(draft['sample_precision_plan']['n_min'])
        self.assertFalse(plan['body']['scientific_readiness'])
        self.assertFalse(draft['scientific_readiness'])
        self.assertIn('atomic_allocation_and_freeze',draft['remaining_gates'])
        self.assertIn(self.execution['id'],plan['exposure'])
        self.assertEqual(self.broker.call(self.token,'prepare_evaluation_plan',**args),plan)
        with self.assertRaises(Conflict):
            self.broker.call(self.token,'prepare_evaluation_plan',**{**args,'primary_count':3})
        for descriptor in plan['body']['source_files'].values():
            self.assertEqual(len(self.broker._read_blob_bytes(descriptor['sha256'])),descriptor['size'])
        self.assertEqual(self.broker.call(self.token,'get_artifact',artifact_id=plan['id']),plan)

    def test_unsupported_original_keeps_evaluation_gap_without_changing_target(self):
        compiled=self.fixture.compile()
        result=self.broker.call(self.token,'prepare_evaluation_plan',**{**self.arguments('unsupported'),'compiled_id':compiled['id']})
        self.assertEqual(result['body']['status'],'EVALUATION_GAP')
        self.assertIsNone(result['body']['plan'])
        self.assertFalse(result['body']['scientific_readiness'])
        self.assertEqual(result['body']['request']['compiled_id'],compiled['id'])

    def test_assessment_or_forged_diagnostic_cannot_supply_development_basis(self):
        for data_class in ('development','assessment'):
            source=self.broker.call(self.token,'add_source',body={'arbitrary':'diagnostic'},data_class=data_class)
            args=self.arguments('bad-'+data_class)
            args['dependence']['development_refs']=[source['id']]
            with patch.object(self.broker,'_bound_dependencies',side_effect=AssertionError('Untrusted diagnostic reached dependencies')):
                with self.assertRaises((Invalid,Denied)):
                    self.broker.call(self.token,'prepare_evaluation_plan',**args)

    def test_worker_cannot_assign_policy_or_override_effect(self):
        with self.assertRaises(Denied):
            self.broker.call(self.fixture.worker,'prepare_evaluation_plan',**self.arguments('worker'))
        with self.assertRaises(Invalid):
            self.broker.call(self.token,'prepare_evaluation_plan',**self.arguments('override'),delta='0.00001')


if __name__=='__main__':unittest.main()
