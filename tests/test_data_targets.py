"""Public target declarations cannot impersonate private data binding."""
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import patch
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker


class TargetAdmissionTests(unittest.TestCase):
    def test_target_namespaces_require_owned_operations(self):
        with tempfile.TemporaryDirectory() as directory:
            broker=Broker(directory)
            try:
                for schema in ('research-data-target/1','protected-data-binding/1'):
                    with self.subTest(schema=schema),self.assertRaises(Invalid):
                        broker.call(broker.admin_token,'add_source',body={'schema':schema},data_class='development')
            finally:broker.close()

    def test_retained_gap_review_does_not_resolve_an_unauthorized_candidate_reference(self):
        import meaning_review_support as support
        from trading_researcher.auxiliary import run_auxiliary_once
        fixture=support.Fixture();self.addCleanup(fixture.close)
        good=fixture.formalize();case=fixture.case()
        candidate=deepcopy(good['target']['body']['candidate'])
        candidate['idea_ref']=case['spec']['research_inputs']['idea_id']
        candidate['test_universe']['data_snapshot_ref']='unauthorized-private-reference'
        case['output']={'status':'final','candidate':candidate,
            'semantic_report':deepcopy(good['target']['body']['semantic_report'])}
        with patch('trading_researcher.controller_providers._invoke',return_value=fixture.result(case)):
            outcome=run_auxiliary_once(case['client'])
        self.assertTrue(outcome['accepted'],outcome)
        case['target']=fixture.op('get_artifact',artifact_id=outcome['artifact_id'])
        self.assertEqual(case['target']['body']['assessment']['status'],'RETAINED_GAP')
        original=fixture.broker._artifact
        def guarded(identity):
            self.assertNotEqual(identity,'unauthorized-private-reference','Untrusted candidate escaped its authorized snapshot')
            return original(identity)
        with patch.object(fixture.broker,'_artifact',side_effect=guarded):
            target=case['target'];body=target['body']
            fixture.op('release_batch',batch_id=fixture.op('inspect',job_id=case['job'])['batch_id'],target_epoch=3)
            context=fixture.op('create_context',role='formalizer',epoch=3,
                artifact_ids=[target['id'],body['idea_id'],body['catalog_id']])
            fixture.op('register_worker',name='gap-reviewer',role='formalizer',capabilities=['semantic-review/v1'])
            spec={**case['spec'],'kind':'semantic-review/v1','context_id':context['id'],'allowed_workers':['gap-reviewer'],
                'research_inputs':{'formalization_id':target['id'],'definition_ids':[]},'dependencies':[case['job']]}
            fixture.op('enqueue',key='gap-reviewer',spec=spec)
            packet=fixture.broker._auxiliary_packet_for_spec(spec)
        self.assertEqual(packet['formalization']['body']['candidate']['test_universe']['data_snapshot_ref'],'unauthorized-private-reference')


if __name__=='__main__':unittest.main()
