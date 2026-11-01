"""Native exact development execution; synthetic replies are not model evidence."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.codec import canonical, decode, digest, Invalid
from trading_researcher import exact_composition as composition, exact_runtime as runtime
from trading_researcher.errors import Denied
from exact_execution_support import ExactExecutionFixture
from test_exact_runtime import payload


class ExactCompositionChecks(unittest.TestCase):
    def test_retained_checker_binds_candidate_and_independent_compiler_goldens(self):
        supplied=payload();before=canonical(supplied)
        compiled=runtime.compile_payload(supplied)
        with tempfile.TemporaryDirectory() as directory:
            checked=composition.run_child(composition.read_bundle(),supplied,digest(compiled),directory)
            self.assertEqual(checked['result'],composition.expected(supplied,digest(compiled)))
            self.assertEqual(len(checked['footprint']),28)
            self.assertFalse(list(Path(directory).rglob('*.pyc')))
        self.assertEqual(canonical(supplied),before)
        self.assertIs(checked['result']['scientific_readiness'],False)

    def test_changed_compilation_and_independent_goldens_are_rejected(self):
        supplied=payload();bundle=composition.read_bundle()
        with tempfile.TemporaryDirectory() as directory,self.assertRaises(Invalid):
            composition.run_child(bundle,supplied,'0'*64,directory)
        changed=dict(bundle);changed[composition.TEST]+=b'\n# changed independently fixed expectations\n'
        with tempfile.TemporaryDirectory() as directory,self.assertRaises(Invalid):
            composition.run_child(changed,supplied,digest(runtime.compile_payload(supplied)),directory)
        for timeout in (0,True,1801):
            with tempfile.TemporaryDirectory() as directory,self.assertRaises(Invalid):
                composition.run_child(bundle,supplied,digest(runtime.compile_payload(supplied)),directory,timeout=timeout)


class ExactNativeExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Roles, snapshot and meanings are immutable across these cases. Each
        # test creates its own compilation/certificate/execution; no authority
        # or spent resource is reset to reuse this expensive genuine setup.
        cls.f=ExactExecutionFixture()
        cls.addClassCleanup(cls.f.close)

    def prepared(self,max_steps=100_000):
        compiled=self.f.compile(max_steps)
        self.assertEqual(compiled['body']['status'],'COMPILED',compiled['body'])
        certificate=self.f.composition(compiled['id'])
        self.assertEqual(certificate['body']['status'],'CONFORMANT',certificate['body'])
        return compiled,certificate

    def test_complete_native_route_uses_certified_inputs_and_independent_replay(self):
        f=self.f;compiled,certificate=self.prepared()
        actual=f.execute(compiled['id'],certificate['id'])
        body=actual['body']
        self.assertEqual(body['status'],'DESCRIPTIVE_EXECUTION',body)
        self.assertTrue(body['complete_required_report'])
        self.assertIs(body['scientific_readiness'],False)
        self.assertEqual(body['verification']['result']['result_hash'],digest(body['result']))
        descriptor=body['result']['case_blob']
        self.assertEqual(actual['blob_refs'],[descriptor['sha256']])
        cases=[decode(line) for line in f.broker._read_blob_bytes(descriptor['sha256']).splitlines()]
        self.assertEqual(len(cases),3)
        self.assertEqual(body['result']['report']['processed_case_count'],3)
        self.assertTrue(body['result']['report']['diagnostics']['processing_complete'])
        self.assertEqual(body['verification']['result']['checked_cases'],3)
        capsule=f.broker._artifact(compiled['body']['input_id'])
        self.assertEqual(capsule['body']['dependencies'],{'data_snapshot_id':f.snapshot['id'],
            'feature_certificate_id':f.feature['id'],'reference_certificate_id':f.runtime['id']})
        self.assertEqual(capsule['body']['data_use']['status'],'QUALIFIED')
        self.assertFalse(capsule['body']['data_use']['independent_confirmation'])

    def test_meaning_gap_fences_row_loader_and_child(self):
        f=self.f;compiled,certificate=self.prepared()
        with patch.object(f.broker,'_load_reference_data',side_effect=AssertionError('outcome loader reached')) as loader,\
                patch.object(runtime,'run_child',side_effect=AssertionError('child reached')) as child,\
                self.assertRaises((Denied,Invalid)):
            f.execute(compiled['id'],certificate['id'],f.early_meaning['id'])
        loader.assert_not_called();child.assert_not_called()

    def test_generated_case_bytes_survive_failed_independent_replay(self):
        f=self.f;compiled,certificate=self.prepared();original=runtime.run_child
        def fail_verify(bundle,mode,*args,**kwargs):
            if mode=='verify':raise Invalid('controlled independent replay failure')
            return original(bundle,mode,*args,**kwargs)
        with patch.object(runtime,'run_child',side_effect=fail_verify):
            actual=f.execute(compiled['id'],certificate['id'])
        body=actual['body'];self.assertEqual(body['status'],'EXECUTION_GAP')
        self.assertFalse(body['complete_required_report'])
        self.assertIn('controlled independent replay failure',body['error']['reason'])
        self.assertIsNone(body['verification'])
        descriptor=body['result']['case_blob']
        self.assertEqual(actual['blob_refs'],[descriptor['sha256']])
        self.assertEqual(len(f.broker._read_blob_bytes(descriptor['sha256'])),descriptor['size'])


if __name__=='__main__':unittest.main()
