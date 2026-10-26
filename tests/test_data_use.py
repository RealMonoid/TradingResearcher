"""Data-use admission is owned, scoped and cannot erase candidate knowledge."""
import tempfile
import unittest
from unittest.mock import patch
from copy import deepcopy
from trading_researcher.data_use import prior_knowledge, checker_current, LOADED_SELF
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker


class DataUseAdmissionTests(unittest.TestCase):
    def test_data_use_namespace_is_reserved(self):
        with tempfile.TemporaryDirectory() as directory:
            broker=Broker(directory)
            try:
                with self.assertRaises(Invalid):
                    broker.call(broker.admin_token,'add_source',body={'schema':'data-use-assessment/1'},data_class='development')
            finally:broker.close()


class KnowledgeTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.broker=Broker(temp.name);self.addCleanup(self.broker.close)

    def source(self,label='root',data_class='development',exposure=()):
        return self.broker.call(self.broker.admin_token,'add_source',body={'label':label},data_class=data_class,exposure=list(exposure))

    def test_opaque_annotations_remain_unresolved_and_do_not_become_known_training(self):
        root=self.source(exposure=['opaque:prior-session'])
        result=prior_knowledge(self.broker,root)
        self.assertEqual(result['unresolved_exposure_refs'],['opaque:prior-session'])
        self.assertEqual(result['artifact_ids'],[root['id']])

    def test_assessment_hidden_behind_development_wrapper_is_visible(self):
        protected=self.source('protected','assessment')
        wrapper=self.source('wrapper',exposure=[protected['id']])
        root=self.source(exposure=[wrapper['id']])
        self.assertEqual(prior_knowledge(self.broker,root)['protected_knowledge_ids'],[protected['id']])

    def test_required_source_cannot_be_downgraded_to_opaque_exposure(self):
        root=self.source(exposure=['missing-source'])
        envelope=deepcopy(root);envelope.pop('id');envelope['source_refs']=['missing-source']
        with self.broker._transaction():root=self.broker._save_artifact(envelope)
        with self.assertRaises(Invalid):prior_knowledge(self.broker,root)

    def test_source_edges_are_followed_even_without_duplicate_exposure(self):
        protected=self.source('protected','assessment')
        envelope=deepcopy(self.source());envelope.pop('id');envelope['source_refs']=[protected['id']]
        with self.broker._transaction():root=self.broker._save_artifact(envelope)
        self.assertEqual(prior_knowledge(self.broker,root)['protected_knowledge_ids'],[protected['id']])

    def test_post_formalization_technical_dependency_is_not_prior_knowledge(self):
        prior=self.source('prior')
        later=self.source('later','operations')
        self.source('compiled-like',exposure=[prior['id'],later['id']])
        self.assertEqual(prior_knowledge(self.broker,prior)['artifact_ids'],[prior['id']])

    def test_operational_observations_behind_development_wrapper_are_visible(self):
        operational=self.source('fills','operations')
        wrapper=self.source('wrapper',exposure=[operational['id']])
        self.assertEqual(prior_knowledge(self.broker,wrapper)['operations_knowledge_ids'],[operational['id']])

    def test_owned_technical_package_is_distinct_but_does_not_hide_its_ancestry(self):
        operational=self.source('fills','operations')
        envelope={'version':'local-artifact/1','creator':'controller','origin':'controller','data_class':'operations',
            'authority':'retained_source_not_certified','source_refs':[operational['id']],'exposure':[],
            'body':{'schema':'binding-source-package/1'}}
        with self.broker._transaction():package=self.broker._save_artifact(envelope)
        result=prior_knowledge(self.broker,package)
        self.assertEqual(result['technical_provenance_ids'],[package['id']])
        self.assertEqual(result['operations_knowledge_ids'],[operational['id']])

    def test_schema_string_alone_cannot_make_operational_source_technical(self):
        envelope={'version':'local-artifact/1','creator':'operator','origin':'source','data_class':'operations',
            'authority':'retained_source_not_certified','source_refs':[],'exposure':[],
            'body':{'schema':'binding-source-package/1'}}
        with self.broker._transaction():forged=self.broker._save_artifact(envelope)
        result=prior_knowledge(self.broker,forged)
        self.assertEqual(result['technical_provenance_ids'],[])
        self.assertEqual(result['operations_knowledge_ids'],[forged['id']])

    def test_unreadable_installed_checker_fails_closed(self):
        with patch('trading_researcher.data_use.Path.read_bytes',side_effect=OSError):
            self.assertFalse(checker_current(LOADED_SELF))


if __name__=='__main__':unittest.main()
