"""Owned raw sources become explicitly qualified decision-time partition snapshots."""
import json
import hashlib
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest
from unittest.mock import patch

from trading_researcher.binance_archive import acquire_month, archive_spec, capture_provider_docs
from trading_researcher.binance_ingest import retain_acquisition, retain_provider_documents
from trading_researcher.binance_normalize import normalize_partition, normalize_retained_partition, _run_child
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker, Denied, Conflict
from trading_researcher.storage import restore_bundle
from test_binance_archive import zipped
from test_binance_quality import row


class NormalizeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.broker = Broker(self.root/'registry')
        self.token = self.broker.admin_token
        docs = self.root/'docs'
        capture_provider_docs(docs,downloader=lambda url,limit:(b'Synthetic provider-document fixture\n',{}))
        self.docs = retain_provider_documents(self.broker,self.token,docs)['id']

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def source(self, raw, month='2020-01', symbol='BTCUSDT'):
        spec=archive_spec(symbol,month)
        payload,checksum=zipped(spec['name'],raw)
        path=self.root/(symbol+'-'+month+'-'+str(len(list(self.root.iterdir()))))
        try:
            acquire_month(symbol,month,path,downloader=lambda url,limit:(checksum if url.endswith('.CHECKSUM') else payload,{}))
        except Invalid:
            pass
        return retain_acquisition(self.broker,self.token,path)

    def run_normalize(self, sources, start='2020-01-01T00:00:00Z',end='2020-01-01T00:45:00Z',partition='development',instruments=None,delay=5):
        self.broker.close()
        try:
            return normalize_retained_partition(self.root/'registry',[s['id'] for s in sources],self.docs,
                partition=partition, universe={'start':start,'end':end,'instruments':instruments or ['BTCUSDT']},delay_seconds=delay)
        finally:
            self.broker=Broker(self.root/'registry')

    def test_independent_partition_expectations_in_fresh_bound_children(self):
        raw=(Path(__file__).parent/'fixtures/reference_binance_partition_cases.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'7921f6119c8f23ef4bb0c366624d1a4fda01baf98dd5531b6733e6c2ed373ae0')
        cases=json.loads(raw)['cases']
        self.assertEqual(len(cases),22)
        for case in cases:
            with self.subTest(case=case['name']):
                expected=case['expected']
                def execute():
                    sources=[self.source(source['raw_csv'].encode(),source['month'],source['symbol']) for source in case['sources']]
                    universe=case['universe']
                    return self.run_normalize(sources,universe['start'],universe['end'],case['partition'],universe['instruments'],case['delay_seconds'])
                if not expected['accepted']:
                    with self.assertRaises((Invalid,Denied,Conflict)):
                        execute()
                    continue
                result=execute()
                universe=case['universe']
                loaded=self.broker._load_reference_data(result['snapshot']['id'],universe['start'],universe['end'],universe['instruments'])
                self.assertEqual(loaded['rows'],expected['rows'])
                self.assertEqual(result['normalization']['body']['selection_counts'],expected['selection_counts'])
                self.assertEqual(loaded['availability']['basis'],'assumed')
                self.assertIs(loaded['scientific_readiness'],False)

    def test_missing_initial_and_invalid_present_rows_survive_snapshot_and_restore(self):
        source=self.source(row()+row(1577837700000,close=1577838000000))
        result=self.run_normalize([source])
        snapshot=result['snapshot']
        self.assertEqual(snapshot['body']['coverage']['expected_rows'],3)
        self.assertEqual(snapshot['body']['coverage']['observed_rows'],2)
        self.assertEqual(snapshot['body']['coverage']['missing_rows'],1)
        self.assertTrue(all(value==1 for value in snapshot['body']['coverage']['null_values'].values()))
        record=result['normalization']['body']
        self.assertEqual(record['selection_counts'],[{'symbol':'BTCUSDT','month':'2020-01','selected':2,'before':0,'after':0}])
        self.assertEqual(record['outside_profile_source_months'],['2019-12'])
        self.assertEqual(record['selected_invalid_rows'],1)
        self.assertIs(snapshot['body']['scientific_readiness'],False)
        self.assertEqual(snapshot['body']['manifest']['availability']['basis'],'assumed')
        self.assertIn(source['id'],snapshot['exposure'])
        loaded=self.broker._load_reference_data(snapshot['id'],'2020-01-01T00:00:00Z','2020-01-01T00:45:00Z',['BTCUSDT'])
        self.assertEqual([r['time'] for r in loaded['rows']],[1577837700,1577838600])
        self.assertTrue(all(v['value'] is None for v in loaded['rows'][1]['features'].values()))
        self.broker.call(self.token,'backup_bundle',destination=str(self.root/'backup'))
        restore_bundle(self.root/'backup',self.root/'restored',self.root/'registry/operator.key')
        restored=Broker(self.root/'restored')
        try:
            actual=restored._load_reference_data(snapshot['id'],'2020-01-01T00:00:00Z','2020-01-01T00:45:00Z',['BTCUSDT'])
            self.assertEqual(actual,loaded)
        finally:
            restored.close()

    def test_year_boundary_uses_previous_month_without_relabeling_times(self):
        december=self.source(row(1704066300000),'2023-12')
        january=self.source(row(1704067200000),'2024-01')
        result=self.run_normalize([january,december],'2024-01-01T00:00:00Z','2024-01-01T00:30:00Z','assessment')
        loaded=self.broker._load_reference_data(result['snapshot']['id'],'2024-01-01T00:00:00Z','2024-01-01T00:30:00Z',['BTCUSDT'])
        self.assertEqual([r['time'] for r in loaded['rows']],[1704067200,1704068100])
        self.assertEqual(result['snapshot']['data_class'],'assessment')
        self.assertIn(december['id'],result['snapshot']['exposure'])
        self.assertIn(january['id'],result['snapshot']['exposure'])

    def test_protected_and_missing_duplicate_irrelevant_sources_fail_before_blob_reads(self):
        good=self.source(row())
        protected=self.source(row(1704067200000),'2024-01')
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('Unexpected raw read')):
            for sources in ([],[good,good],[protected],[good,protected]):
                with self.subTest(sources=[s['id'] for s in sources]), self.assertRaises((Invalid,Denied)):
                    normalize_partition(self.broker,self.token,[s['id'] for s in sources],self.docs,
                        partition='development',universe={'start':'2020-01-01T00:00:00Z','end':'2020-01-01T00:45:00Z','instruments':['BTCUSDT']},delay_seconds=5)

    def test_worker_cannot_trigger_raw_reads_or_registration(self):
        source=self.source(row())
        worker=self.broker.call(self.token,'register_worker',name='discover',role='discovery',capabilities=['draft/v1'])['token']
        with patch.object(self.broker,'_read_blob_bytes',side_effect=AssertionError('Unexpected raw read')):
            with self.assertRaises(Denied):
                normalize_partition(self.broker,worker,[source['id']],self.docs,partition='development',
                    universe={'start':'2020-01-01T00:00:00Z','end':'2020-01-01T00:30:00Z','instruments':['BTCUSDT']},delay_seconds=5)

    def test_supplied_bundle_cannot_launder_invalid_original_receipt_semantics(self):
        source=self.source(row())
        body=json.loads(json.dumps(source['body']))
        receipt_source=self.broker.call(self.token,'get_artifact',artifact_id=body['original_receipt_ref'])
        receipt=json.loads(self.broker._read_blob_bytes(receipt_source['body']['blob']['sha256']))
        receipt.update(schema='unrelated/99',scientific_readiness=True,purpose='live trading',retrieved_at='invented')
        path=self.root/'forged-receipt.json'
        path.write_text(json.dumps(receipt))
        replacement=self.broker.call(self.token,'add_blob_source',path=str(path),data_class='development',description='Deliberately invalid fixture receipt')
        body['files']['acquisition.json']={**replacement['body']['blob'],'artifact_ref':replacement['id']}
        body['original_receipt_ref']=replacement['id']
        body['original_receipt_retrieved_at']=body['retrieved_at']='invented'
        forged=self.broker.call(self.token,'add_source',body=body,data_class='development',exposure=source['exposure']+[replacement['id']])
        with self.assertRaises(Invalid):
            self.run_normalize([forged])

    def test_provider_document_wrapper_cannot_launder_a_future_receipt_time(self):
        source=self.source(row())
        original=self.broker.call(self.token,'get_artifact',artifact_id=self.docs)
        body=json.loads(json.dumps(original['body']))
        receipt=json.loads(self.broker._read_blob_bytes(body['files']['documents.json']['sha256']))
        receipt['retrieved_at']='2999-01-01T00:00:00Z'
        path=self.root/'future-document-receipt.json'
        path.write_text(json.dumps(receipt))
        replacement=self.broker.call(self.token,'add_blob_source',path=str(path),data_class='development',description='Deliberately invalid future document time')
        body['files']['documents.json']={**replacement['body']['blob'],'artifact_ref':replacement['id']}
        body['retrieved_at']=receipt['retrieved_at']
        self.docs=self.broker.call(self.token,'add_source',body=body,data_class='development',exposure=original['exposure']+[replacement['id']])['id']
        with self.assertRaises(Invalid):
            self.run_normalize([source])

    def test_stale_parent_import_is_not_the_transformation_implementation(self):
        source=self.source(row())
        with patch('trading_researcher.binance_normalize._month',side_effect=AssertionError('Stale parent code executed')):
            result=self.run_normalize([source])
        code=result['code_snapshot']['body']
        self.assertEqual(code['execution_binding'],'FRESH_ISOLATED_SOURCE_SNAPSHOT')
        self.assertEqual(code['environment']['isolation'],{'isolated':1,'no_site':1,'ignore_environment':1,'no_bytecode_writes':1})
        with self.assertRaises(Invalid):
            normalize_partition(self.broker,self.token,[source['id']],self.docs,partition='development',
                universe={'start':'2020-01-01T00:00:00Z','end':'2020-01-01T00:30:00Z','instruments':['BTCUSDT']},delay_seconds=5)

    def test_corrupt_retained_csv_does_not_create_data_snapshot(self):
        source=self.source(row())
        csv_name='BTCUSDT-15m-2020-01.csv'
        self.broker._blob_path(source['body']['files'][csv_name]['sha256']).write_bytes(b'corrupt')
        with self.assertRaises((Invalid,Denied,Conflict)):
            self.run_normalize([source])
        self.assertEqual(self.broker._db.execute("SELECT count(*) FROM artifacts WHERE json_extract(envelope,'$.body.schema')='data-snapshot/1'").fetchone()[0],0)

    def test_owned_child_timeout_and_output_overflow_are_reaped(self):
        real_popen=subprocess.Popen
        for label,code,timeout in [('timeout','import time;time.sleep(30)',0.1),
                                   ('overflow',"print('x'*1100000)",10)]:
            with self.subTest(label=label):
                stage=self.root/label
                stage.mkdir()
                created=[]
                def spawn(*args,**kwargs):
                    process=real_popen(*args,**kwargs)
                    created.append(process)
                    return process
                with patch('trading_researcher.binance_normalize.subprocess.Popen',side_effect=spawn), patch('trading_researcher.binance_normalize.NORMALIZATION_TIMEOUT',timeout):
                    with self.assertRaises(Invalid):
                        _run_child([sys.executable,'-I','-S','-B','-c',code],stage)
                self.assertIsNotNone(created[0].poll())

    def test_caller_cancellation_reaps_the_owned_child(self):
        real_popen=subprocess.Popen
        created=[]
        def spawn(*args,**kwargs):
            process=real_popen(*args,**kwargs)
            created.append(process)
            original_wait=process.wait
            calls=[]
            def interrupted_wait(*arguments,**options):
                calls.append(1)
                if len(calls)==1:
                    raise KeyboardInterrupt()
                return original_wait(*arguments,**options)
            process.wait=interrupted_wait
            return process
        stage=self.root/'cancelled-child'
        stage.mkdir()
        with patch('trading_researcher.binance_normalize.subprocess.Popen',side_effect=spawn):
            with self.assertRaises(KeyboardInterrupt):
                _run_child([sys.executable,'-I','-S','-B','-c','import time;time.sleep(30)'],stage)
        self.assertIsNotNone(created[0].poll())

    def test_cli_normalizes_an_existing_registry_without_double_locking(self):
        source=self.source(row())
        request=self.root/'request.json'
        request.write_text(json.dumps({'source_bundle_refs':[source['id']],'provider_documents_ref':self.docs,
            'partition':'development','universe':{'start':'2020-01-01T00:00:00Z','end':'2020-01-01T00:30:00Z','instruments':['BTCUSDT']},'delay_seconds':5}))
        self.broker.close()
        try:
            result=subprocess.run([sys.executable,'-B','-m','trading_researcher','normalize-binance-partition',
                '--directory',str(self.root/'registry'),'--request',str(request)],capture_output=True,text=True,timeout=60)
        finally:
            self.broker=Broker(self.root/'registry')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['snapshot']['body']['coverage']['observed_rows'],1)


if __name__=='__main__':
    unittest.main()
