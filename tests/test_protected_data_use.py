"""Concrete ancestry gaps differ from unobservable model-training uncertainty."""
import tempfile
import unittest
from trading_researcher.coordination import Broker
from trading_researcher.data_use import prior_knowledge, protected_knowledge_gaps


class ProtectedKnowledgeTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.broker=Broker(temporary.name);self.addCleanup(self.broker.close)

    def source(self,data_class='development',exposure=()):
        return self.broker.call(self.broker.admin_token,'add_source',body={'text':'Synthetic ancestry'},
            data_class=data_class,exposure=list(exposure))

    def test_no_recorded_private_ancestry_does_not_invent_training_exposure(self):
        knowledge=prior_knowledge(self.broker,self.source())
        self.assertEqual(protected_knowledge_gaps(knowledge),[])

    def test_unresolved_concrete_annotation_blocks_private_preparation(self):
        knowledge=prior_knowledge(self.broker,self.source(exposure=['unresolved:earlier-result']))
        self.assertEqual(protected_knowledge_gaps(knowledge),['UNRESOLVED_CANDIDATE_EXPOSURE'])

    def test_wrapped_protected_and_operational_knowledge_remains_a_gap(self):
        private=self.source('assessment');operational=self.source('operations')
        wrapper=self.source(exposure=[private['id'],operational['id']])
        knowledge=prior_knowledge(self.broker,self.source(exposure=[wrapper['id']]))
        self.assertEqual(protected_knowledge_gaps(knowledge),[
            'PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY','OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT'])


if __name__=='__main__':unittest.main()
