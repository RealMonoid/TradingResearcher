"""Owned child isolation/replay boundary checks on synthetic paired fixtures."""
from copy import deepcopy
from pathlib import Path
import shutil
import tempfile
import unittest

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.paired_runtime import read_bundle, run_child, compile_payload, _stream
from test_paired_development_adversarial import boundary_rows


def payload():
    request,catalog,rows,definitions=boundary_rows()
    candidate={'schema':'hypothesis-exec/2','test_universe':{
        **request['universe'],'data_snapshot_ref':request['data_snapshot_ref']},
        'scope_ast':request['scope_program'],'condition_ast':request['condition_program'],
        'outcome':{'program':request['outcome_program'],'scale':'quantity'},
        'estimand':{'unit':'basis_points'},'horizons':{'grid_seconds':900,'outcome_bars':request['horizon_bars']},
        'feature_refs':sorted(catalog)}
    return {'formalization_id':request['candidate_ref'],'candidate':candidate,'catalog':catalog,
        'feature_definitions':definitions,'data_manifest':{'partition':'development','universe':{
            'start':request['universe']['start'],'end':request['universe']['end'],'instruments':request['universe']['pair']}},
        'as_of':request['as_of'],'max_steps':request['max_steps']}, rows


class PairedRuntimeTests(unittest.TestCase):
    def test_actual_retained_source_compile_execute_fresh_replay_and_tamper(self):
        inputs,rows=payload()
        bundle=read_bundle()
        with tempfile.TemporaryDirectory() as root:
            root=Path(root)
            for name in ('compile','execute','verify','tamper'):
                (root/name).mkdir()
            compilation=run_child(bundle,'compile',inputs,root/'compile')
            self.assertEqual(compilation['result'],compile_payload(inputs))
            self.assertEqual(compilation['result']['expected_case_count'],8)
            rows_path=root/'execute'/'rows.jsonl'
            rows_path.write_bytes(b''.join((canonical(row)+'\n').encode() for row in rows))
            request={'compilation_input':inputs,'compilation_hash':digest(compilation['result']),'rows':_stream(rows_path)}
            executed=run_child(bundle,'execute',request,root/'execute')
            self.assertEqual(executed['result']['report']['processed_case_count'],8)
            self.assertEqual(executed['result']['contrast']['scope_count'],3)
            for name in ('verify','tamper'):
                for file in ('rows.jsonl','cases.jsonl'):
                    shutil.copyfile(root/'execute'/file,root/name/file)
            verified=run_child(bundle,'verify',{'execution_input':request,'result':executed['result']},root/'verify')
            self.assertEqual(verified['result']['checked_cases'],8)
            self.assertEqual(verified['result']['case_blob'],executed['result']['case_blob'])
            with (root/'tamper'/'cases.jsonl').open('ab') as stream:
                stream.write(b'{}\n')
            with self.assertRaises(Invalid):
                run_child(bundle,'verify',{'execution_input':request,'result':executed['result']},root/'tamper')

    def test_protected_compile_and_changed_raw_row_bytes_fail_before_calculation(self):
        inputs,rows=payload()
        changed=deepcopy(inputs)
        changed['data_manifest']['partition']='assessment'
        with self.assertRaises(Invalid):
            compile_payload(changed)
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary)
            (directory/'rows.jsonl').write_bytes(b'{}\n')
            request={'compilation_input':inputs,'compilation_hash':digest(compile_payload(inputs)),
                     'rows':{'sha256':'0'*64,'size':3}}
            with self.assertRaises(Invalid):
                run_child(read_bundle(),'execute',request,directory)

    def test_retained_source_certification_executes_independent_expectations(self):
        from trading_researcher.paired_development import PROFILE
        with tempfile.TemporaryDirectory() as temporary:
            result=run_child(read_bundle(),'certify',{'profile':PROFILE},temporary)
        self.assertGreaterEqual(result['result']['tests'],19)
        self.assertEqual(result['result']['failures'],0)
        self.assertEqual(result['environment']['isolation'],{
            'isolated':1,'no_site':1,'ignore_environment':1,'no_bytecode_writes':1})


if __name__=='__main__':
    unittest.main()
