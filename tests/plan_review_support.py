"""Light plan-review boundary fixture; source-data resolution is explicitly stubbed.

Actual owned review calls, historical assessments, retained plan capsules and child
policy calculation/replay run normally. Synthetic compiled metadata below does not
constitute a data/feature/compiler integration test.
"""
from copy import deepcopy
from unittest.mock import patch

import meaning_review_support as meaning_support


class Fixture(meaning_support.Fixture):
    def setup_plan(self, judgment='faithful'):
        self.target_case=self.formalize()
        self.review_result=self.review(self.target_case,judgment)
        self.assessment=self.op('assess_meaning_review',key='meaning',formalization_id=self.target_case['target']['id'])
        self.compiled=self.owned({'schema':'compiled-hypothesis/1','status':'COMPILED',
            'dependency_arguments':{'formalization_id':self.target_case['target']['id'],
                'feature_certificate_id':'unused-literal-feature-certificate','reference_certificate_id':'unused-reference'},
            'scientific_readiness':False},[self.target_case['target']['id']])
        self.payload={'candidate':deepcopy(self.target_case['target']['body']['candidate']),
            'definitions':[],'outcome_description':{'type':'boolean','unit':None},'primary_count':1,
            'dependence':{'base_length':4,'rationale':'Synthetic metadata boundary fixture, not a scientific dependence fit.',
                'development_refs':[self.compiled['id']],
                'randomness':{'algorithm':'fixture','version':'1','seed':17}}}
        return self

    def owned(self, body, refs=()):
        with self.broker._transaction():
            return self.broker._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'development','body':body,'source_refs':list(refs),'exposure':list(refs),
                'authority':'synthetic_test_metadata_not_a_real_data_binding'})

    def arguments(self,key='plan',with_review=True):
        args={'key':key,'compiled_id':self.compiled['id'],'primary_count':1,'dependence':deepcopy(self.payload['dependence'])}
        if with_review:args['meaning_review_id']=self.assessment['id']
        return args

    def numeric_inputs(self,actor,request):
        return deepcopy(self.payload),[self.compiled['id'],self.target_case['target']['id']],[self.compiled['id'],self.target_case['target']['id']]

    def prepare(self,key='plan',with_review=True,**overrides):
        with patch.object(self.broker,'_plan_inputs',side_effect=self.numeric_inputs):
            return self.op('prepare_evaluation_plan',**{**self.arguments(key,with_review),**overrides})
