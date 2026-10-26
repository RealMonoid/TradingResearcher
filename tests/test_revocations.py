"""Technical use follows typed dependencies, never all historical ancestry."""
import tempfile
import unittest
from trading_researcher.coordination import Broker


class RevocationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.broker=Broker(self.temp.name);self.addCleanup(self.broker.close)
        self.token=self.broker.admin_token

    def op(self,name,**args):return self.broker.call(self.token,name,**args)

    def owned(self,body,origin='controller',exposure=()):
        with self.broker._transaction():
            return self.broker._save_artifact({'version':'local-artifact/1','creator':'controller',
                'origin':origin,'data_class':'development','body':body,'source_refs':list(exposure),
                'exposure':list(exposure),'authority':'synthetic_metadata_fixture'})

    def test_known_version_revocation_preserves_history_and_changes_only_current_use(self):
        target=self.owned({'schema':'data-snapshot/1'},origin='source')
        evidence=self.op('add_source',body={'defect':'Synthetic check only'},data_class='development')
        self.assertEqual(self.op('inspect_dependency_use',artifact_id=target['id'])['status'],'NOT_REVOKED')
        saved=self.op('revoke_dependency',key='defect',dependency_id=target['id'],reason='Synthetic defect',evidence_refs=[evidence['id']])
        self.assertEqual(saved['body']['schema'],'dependency-revocation/1')
        self.assertEqual(self.op('inspect_dependency_use',artifact_id=target['id'])['status'],'INVALIDATED_BY_DEPENDENCY')
        self.assertEqual(self.op('get_artifact',artifact_id=target['id']),target)

    def test_source_package_identity_cannot_be_reset_by_a_new_artifact_timestamp(self):
        package={'schema':'binding-source-package/1','footprint':{'binding.py':'a'*64},'created_at':1}
        original=self.owned(package)
        evidence=self.op('add_source',body={'defect':'fixture'},data_class='development')
        self.op('revoke_dependency',key='package',dependency_id=original['id'],reason='Synthetic defect',evidence_refs=[evidence['id']])
        alias=self.owned({**package,'created_at':2})
        changed=self.owned({**package,'footprint':{'binding.py':'b'*64},'created_at':2})
        self.assertEqual(self.op('inspect_dependency_use',artifact_id=alias['id'])['status'],'INVALIDATED_BY_DEPENDENCY')
        self.assertEqual(self.op('inspect_dependency_use',artifact_id=changed['id'])['status'],'NOT_REVOKED')

    def test_shared_dependency_across_typed_fields_is_checked_once(self):
        target=self.owned({'schema':'data-snapshot/1'},origin='source')
        consumer=self.owned({'schema':'evaluation-plan/1','request':{
            'compiled_id':target['id'],'dependence':{'development_refs':[target['id']]}}})
        current=self.op('inspect_dependency_use',artifact_id=consumer['id'])
        self.assertEqual(current['status'],'NOT_REVOKED')
        self.assertEqual(current['checked_versions'],sorted([consumer['id'],target['id']]))
        evidence=self.op('add_source',body={'defect':'Synthetic graph fixture'},data_class='development')
        revoked=self.op('revoke_dependency',key='shared',dependency_id=target['id'],
            reason='Synthetic defect',evidence_refs=[evidence['id']])
        current=self.op('inspect_dependency_use',artifact_id=consumer['id'])
        self.assertEqual(current['status'],'INVALIDATED_BY_DEPENDENCY')
        self.assertEqual(len(current['invalidations']),1)
        self.assertIn(consumer['id'],revoked['body']['affected_artifact_ids'])


if __name__=='__main__':unittest.main()
