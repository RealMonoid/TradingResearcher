"""Independent fault injection at owned diagnostic input and replay boundaries."""
from copy import deepcopy
import hashlib
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid, canonical, decode
from trading_researcher.errors import Denied
from trading_researcher import information_runs
from trading_researcher.information_diagnostics import diagnose
import test_information_runs as setup_support


class InformationRunAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse the owned setup, without inheriting or rerunning its test methods.
        setup_support.InformationRunTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):cls.fixture.close()

    @classmethod
    def op(cls,op,**args):return cls.broker.call(cls.token,op,**args)

    def args(self,key):
        return {'key':key,'plan_id':self.plan['id'],'execution_id':self.execution['id'],
                'lags':[1,2],'limits':{'max_seconds':60}}

    def test_protected_snapshot_is_denied_before_any_case_or_source_blob_read(self):
        protected=deepcopy(self.broker._data_snapshot(self.execution['body']['data_snapshot_id']))
        protected['data_class']='assessment';protected['body']['manifest']['partition']='assessment'
        with patch.object(self.broker,'_data_snapshot',return_value=protected), \
                patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('protected blob read')), \
                patch.object(self.broker,'_plan_inputs',side_effect=AssertionError('protected dependencies read')):
            with self.assertRaises(Denied):
                self.op('prepare_information_diagnostics',**self.args('protected-adversarial'))

    def test_contradictory_retained_claim_or_membership_is_rejected_before_dependencies(self):
        original=self.broker._artifact
        for key,mutate in [('wrong-claim',lambda p:p['body']['request'].update(compiled_id='different-compiled-claim')),
                           ('not-listed',lambda p:p['body']['request']['dependence'].update(development_refs=[]))]:
            altered=deepcopy(self.plan);mutate(altered)
            def replacement(identity):
                return deepcopy(altered) if identity==self.plan['id'] else original(identity)
            with patch.object(self.broker,'_artifact',side_effect=replacement), \
                    patch.object(self.broker,'_plan_inputs',side_effect=AssertionError('unmatched dependencies read')), \
                    patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('unmatched blob read')):
                with self.subTest(key=key),self.assertRaises(Invalid):
                    self.op('prepare_information_diagnostics',**self.args('adversarial-'+key))

    def test_consistently_rehashed_false_contribution_still_fails_independent_replay(self):
        args=self.args('adversarial-contribution');real=information_runs.run_child
        def altered(*values,**options):
            response,raw=real(*values,**options)
            if options.get('verify') is None:
                lines=raw.splitlines(keepends=True);first=decode(lines[0]);first['scope_count']+=1
                lines[0]=(canonical(first)+'\n').encode();raw=b''.join(lines)
                checksum=hashlib.sha256(raw).hexdigest()
                response['contribution_blob']={'sha256':checksum,'size':len(raw)}
                response['result']['contributions_sha256']=checksum
            return response,raw
        with patch.object(information_runs,'run_child',side_effect=altered):
            with self.assertRaises(Invalid):self.op('prepare_information_diagnostics',**args)
        self.assertIsNone(self.broker._find_information_diagnostics(information_runs.RESULT,args))
        capsule=self.broker._find_information_diagnostics(information_runs.INPUT,args)
        self.assertEqual(capsule['body']['request'],args)

    def test_computation_and_replay_share_one_time_budget(self):
        args=self.args('adversarial-common-deadline')
        def completed_first(source,payload,cases,timeout,**kwargs):
            self.assertEqual(timeout,60)
            self.assertIsNone(kwargs.get('verify'))
            rows=[]
            result=diagnose({**payload['report'],'cases':[decode(line) for line in cases.splitlines()]},
                            payload['lags'],on_contribution=rows.append)
            raw=''.join(canonical(row)+'\n' for row in rows).encode()
            return {'result':result,'contribution_blob':{'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}},raw
        with patch.object(information_runs,'run_child',side_effect=completed_first) as child, \
                patch.object(information_runs.time,'monotonic',side_effect=[0,0,61]):
            with self.assertRaisesRegex(Invalid,'time cap'):
                self.op('prepare_information_diagnostics',**args)
        self.assertEqual(child.call_count,1)
        self.assertIsNone(self.broker._find_information_diagnostics(information_runs.RESULT,args))
        self.assertIsNotNone(self.broker._find_information_diagnostics(information_runs.INPUT,args))


if __name__=='__main__':unittest.main()
