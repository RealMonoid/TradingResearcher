"""Bound versioned computations cannot acquire scientific or protected-data authority."""
import tempfile
from copy import deepcopy
import hashlib
import subprocess
import sys
from pathlib import Path
import unittest

from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker, Denied
from trading_researcher.codec import canonical, decode, digest
from trading_researcher.binding import run_child, ROOT, DRIVER
from trading_researcher.certification import read_bundle as reference_bundle
from trading_researcher.storage import restore_bundle
from binding_support import BindingFixture, fixture, resolve


class BindingAdmissionTests(unittest.TestCase):
    def test_compilation_and_execution_records_cannot_be_generic_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            broker = Broker(directory)
            try:
                for schema in ('compiled-hypothesis/1', 'reference-execution/1', 'binding-source-package/1'):
                    with self.subTest(schema=schema), self.assertRaises(Invalid):
                        broker.call(broker.admin_token, 'add_source', body={'schema': schema}, data_class='development')
            finally:
                broker.close()


class BoundExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.setup = BindingFixture()

    @classmethod
    def tearDownClass(cls):
        cls.setup.close()

    def check_result(self, result, cases, expected):
        self.assertEqual([case['status'] for case in cases],expected['case_states'])
        self.assertEqual([case['outcome'] for case in cases],expected['outcome_values'])
        if 'condition_values' in expected:
            self.assertEqual([case['condition'] for case in cases],expected['condition_values'])
        for field in ('effect','scope_count','condition_count'):
            self.assertEqual(result['contrast'][field],expected[field])
        self.assertIs(result['scientific_readiness'],False)
        self.assertIs(result['report']['scientific_readiness'],False)
        if 'processing_complete' in expected:
            self.assertEqual(result['report']['processing_complete'],expected['processing_complete'])
            self.assertEqual(result['report']['status'],expected['status'])

    def test_six_independent_numerical_cases_in_fresh_bound_children(self):
        fixed = fixture()
        base = fixed['baseline']
        bundle = {**reference_bundle(),DRIVER:(ROOT/DRIVER).read_bytes()}
        for case in fixed['cases']:
            if case['kind'] != 'development_calculation':continue
            with self.subTest(case=case['name']):
                change = case['change']
                payload = {'formalization_id':base['identity_aliases']['formalization'],
                    'candidate':deepcopy(change.get('candidate',base['candidate'])),'catalog':base['catalog'],
                    'data_manifest':{'universe':{'start':'2020-01-01T00:00:00Z','end':'2020-01-01T01:00:00Z',
                        'instruments':['BTCUSDT']}},**base['compile_options'],**change.get('compile_options',{})}
                with tempfile.TemporaryDirectory() as directory:
                    compiled = run_child(bundle,'compile',payload,directory)['result']
                expected_request = deepcopy(case.get('expected_compiled_request',base['expected_compiled_request']))
                expected_request.update(change.get('compile_options',{}))
                self.assertEqual(compiled['request'],expected_request)
                self.assertEqual(compiled['candidate_hash'],digest(payload['candidate']))
                rows = change.get('rows',base['rows'])
                raw = ''.join(canonical(row)+'\n' for row in rows).encode()
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory)
                    (path/'rows.jsonl').write_bytes(raw)
                    request = {'compilation_input':payload,'compilation_hash':digest(compiled),
                        'rows':{'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}}
                    result = run_child(bundle,'execute',request,path)['result']
                    cases = [decode(line) for line in (path/'cases.jsonl').read_bytes().splitlines()]
                    self.check_result(result,cases,case['expected'])

    def test_owned_completed_formalization_reaches_exact_retained_development_result(self):
        for index in (0,5):
            case = self.setup.fixed['cases'][index]
            with self.subTest(case=case['name']):
                formalization = self.setup.create_formalization(case)
                compiled = self.setup.compile(formalization,case)
                self.assertEqual(compiled['body']['status'],'COMPILED',compiled['body'])
                self.assertEqual(compiled['body']['compilation']['candidate_hash'],digest(formalization['body']['candidate']))
                expected_request = resolve(case.get('expected_compiled_request',self.setup.base['expected_compiled_request']),
                    {'fixture:formalization':formalization['id'],'fixture:data_snapshot':self.setup.snapshot['id']})
                self.assertEqual(compiled['body']['compilation']['request'],expected_request)
                executed = self.setup.broker.call(self.setup.token,'execute_development',compiled_id=compiled['id'])
                self.assertEqual(executed['body']['status'],'DESCRIPTIVE_EXECUTION',executed['body'])
                result = executed['body']['result']
                raw = self.setup.broker._read_blob_bytes(result['case_blob']['sha256'])
                cases = [decode(line) for line in raw.splitlines()]
                self.check_result(result,cases,case['expected'])
                self.assertIn(formalization['id'],executed['exposure'])
                self.assertIn(self.setup.snapshot['id'],executed['exposure'])
                events = [decode(row[0])['action'] for row in self.setup.broker._db.execute('SELECT envelope FROM events')]
                self.assertNotIn('EligibleOutcomeBatchCommitted',events)
        self.assertEqual(self.setup.broker.call(self.setup.token,'inspect_bound_computations')['pending'],0)

    def test_missing_compile_dependencies_are_a_typed_request_rejection(self):
        with tempfile.TemporaryDirectory() as directory:
            broker = Broker(directory)
            try:
                with self.assertRaises(Invalid):
                    broker.call(broker.admin_token, 'compile_hypothesis', formalization_id='unbound')
            finally:
                broker.close()

    def test_cli_and_complete_backup_preserve_executable_bindings(self):
        formalization = self.setup.create_formalization()
        directory = self.setup.broker.directory
        self.setup.broker.close()
        try:
            arguments = [sys.executable,'-B','-m','trading_researcher','compile-hypothesis',
                '--directory',str(directory),'--formalization-id',formalization['id'],
                '--feature-certificate-id',self.setup.feature['id'],
                '--reference-certificate-id',self.setup.reference['id'],
                '--as-of',self.setup.base['compile_options']['as_of'],'--max-steps','10000']
            process = subprocess.run(arguments,cwd=ROOT,capture_output=True,timeout=120)
            self.assertEqual(process.returncode,0,process.stderr.decode())
            compiled = decode(process.stdout)
            process = subprocess.run([sys.executable,'-B','-m','trading_researcher','execute-development',
                '--directory',str(directory),'--compiled-id',compiled['id']],cwd=ROOT,capture_output=True,timeout=120)
            self.assertEqual(process.returncode,0,process.stderr.decode())
            executed = decode(process.stdout)
            self.assertEqual(executed['body']['status'],'DESCRIPTIVE_EXECUTION')
        finally:
            self.setup.broker = self.setup.normalizer.broker = Broker(directory)
        backup,restored = self.setup.root/'binding-backup',self.setup.root/'binding-restored'
        self.setup.broker.call(self.setup.token,'backup_bundle',destination=str(backup))
        restore_bundle(backup,restored,directory/'operator.key')
        replay = Broker(restored)
        try:
            self.assertEqual(replay.call(replay.admin_token,'get_artifact',artifact_id=compiled['id']),compiled)
            self.assertEqual(replay.call(replay.admin_token,'get_artifact',artifact_id=executed['id']),executed)
            again = replay.call(replay.admin_token,'execute_development',compiled_id=compiled['id'])
            self.assertEqual(again['body']['status'],'DESCRIPTIVE_EXECUTION',again['body'])
            self.assertEqual(again['body']['result'],executed['body']['result'])
            for identity in executed['blob_refs']:
                self.assertEqual(replay._read_blob_bytes(identity),self.setup.broker._read_blob_bytes(identity))
        finally:
            replay.close()


if __name__ == '__main__':
    unittest.main()
