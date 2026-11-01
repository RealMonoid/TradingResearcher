"""Owned retained-source child execution on the portable engineering shape."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from trading_researcher.codec import canonical, decode, digest, Invalid
from trading_researcher.exact_formalization import CANDIDATE_FIELDS
from trading_researcher import exact_runtime as runtime
import test_exact_formalization_review as shape

T,D=1672531200,900


def stamp(value):return datetime.fromtimestamp(value,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def payload(count=55, *, max_steps=1000000):
    candidate=shape.candidate()
    candidate['test_universe'].update(start=stamp(T),end=stamp(T+count*D))
    return {'formalization_id':'synthetic-engineering-formalization-not-native-acceptance',
        'candidate':candidate,'catalog':deepcopy(shape.FIXTURE['catalog']),
        'data_manifest':{'partition':'development','universe':{'start':stamp(T),
            'end':stamp(T+count*D),'instruments':['BTCUSDT']}},'as_of':stamp(T+count*D),'max_steps':max_steps}


def history(count=55):
    result=[]
    for i in range(count):
        values={'H':'120','L':'80','C':'100','Q':'100','B':'50'}
        if i==39:values.update(H='100.5',L='100',Q='250',B='125')
        result.append({'time':T+i*D,'instrument':'BTCUSDT','features':{
            ref+'@1':{'value':value,'available_at':T+(i+1)*D} for ref,value in values.items()}})
    return result


def write_rows(directory,rows):
    path=Path(directory)/'rows.jsonl'
    with path.open('xb') as stream:
        for row in rows:stream.write((canonical(row)+'\n').encode())
    return runtime._stream(path)


class ExactRuntimeTests(unittest.TestCase):
    def test_child_conformance_is_exact_fixed_suite_and_interpreter_closure(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle=runtime.read_bundle()
            result=runtime.run_child(bundle,'certify',{'profile':runtime.PROFILE},directory)
            self.assertEqual(result['result'],{'schema':'exact-conformance-result/1','profile':runtime.PROFILE,
                'tests':51,'failures':0,'errors':0,'skipped':0,'scientific_readiness':False})
            self.assertEqual(result['footprint'],{path:hashlib.sha256(raw).hexdigest() for path,raw in bundle.items()})
            self.assertEqual(result['environment']['isolation'],{'isolated':1,'no_site':1,
                'ignore_environment':1,'no_bytecode_writes':1})
            self.assertFalse(list(Path(directory).rglob('*.pyc')))

    def test_full_engineering_shape_streams_over_one_mib_and_replays_exactly(self):
        supplied=payload()
        self.assertEqual(runtime.CANDIDATE_FIELDS,CANDIDATE_FIELDS)
        bundle=runtime.read_bundle()
        compiled=runtime.compile_payload(supplied)
        with tempfile.TemporaryDirectory() as first,tempfile.TemporaryDirectory() as second:
            execution={'compilation_input':supplied,'compilation_hash':digest(compiled),
                'rows':write_rows(first,history())}
            actual=runtime.run_child(bundle,'execute',execution,first)['result']
            self.assertEqual(actual['report']['schema'],'diagnostic-exact-composition-cases/1')
            self.assertEqual(actual['report']['processed_case_count'],55)
            self.assertEqual(actual['report']['diagnostics']['processed_cases'],55)
            self.assertEqual(actual['report']['diagnostics']['status'],'COMPLETE')
            self.assertEqual(actual['contrast']['scope_count'],50)
            self.assertEqual(actual['contrast']['condition_count'],1)
            self.assertEqual(actual['contrast']['status'],'DESCRIPTIVE_ONLY')
            self.assertGreater(actual['case_blob']['size'],1048576)
            self.assertEqual(actual['case_blob'],runtime._stream(Path(first)/'cases.jsonl'))
            with (Path(first)/'cases.jsonl').open('rb') as stream:cases=[decode(line) for line in stream]
            self.assertEqual(len(cases),55)
            self.assertIs(cases[40]['condition'],True)
            self.assertTrue(all(case['condition'] is None for case in cases[:33]))
            for name in ('rows.jsonl','cases.jsonl'):shutil.copyfile(Path(first)/name,Path(second)/name)
            verified=runtime.run_child(bundle,'verify',{'execution_input':execution,'result':actual},second)['result']
            self.assertEqual(verified,{'schema':'exact-case-verification/1','result_hash':digest(actual),
                'compilation_hash':execution['compilation_hash'],'case_blob':actual['case_blob'],
                'checked_cases':55,'scientific_readiness':False})
            self.assertFalse(actual['scientific_readiness'])

    def test_child_compiler_preserves_candidate_and_reports_complete_declared_spans(self):
        supplied=payload()
        saved=canonical(supplied)
        expected=runtime.compile_payload(supplied)
        with tempfile.TemporaryDirectory() as directory:
            actual=runtime.run_child(runtime.read_bundle(),'compile',supplied,directory)['result']
        self.assertEqual(actual,expected)
        self.assertEqual(actual['warmup_seconds'],33*D)
        self.assertEqual(actual['unavailable_warmup_seconds'],33*D)
        self.assertEqual(actual['row_window'],supplied['data_manifest']['universe'])
        self.assertEqual(actual['maximum_input_rows'],55)
        self.assertEqual(canonical(supplied),saved)

    def test_source_membership_timeout_and_exclusive_directory_are_bounded(self):
        bundle=runtime.read_bundle()
        for timeout in (0,True,1801):
            with tempfile.TemporaryDirectory() as directory,self.assertRaises(Invalid):
                runtime.run_child(bundle,'compile',payload(),directory,timeout=timeout)
        for change in ('absent','extra'):
            bad=dict(bundle)
            if change=='absent':bad.pop(next(iter(bad)))
            else:bad['../outside.py']=b'Untrusted path'
            with tempfile.TemporaryDirectory() as directory,self.assertRaises(Invalid):
                runtime.run_child(bad,'compile',payload(),directory)
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'request.json'
            target.write_bytes(b'preserve existing input')
            with self.assertRaises(FileExistsError):
                runtime.run_child(bundle,'compile',payload(),directory)
            self.assertEqual(target.read_bytes(),b'preserve existing input')

    def test_approved_owner_bytes_and_declared_estimator_are_not_replaceable(self):
        bundle=runtime.read_bundle()
        for owner in ('docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md',
                      'docs/architecture/26_BOUNDED_EXACT_COMPOSITIONS.md'):
            changed=dict(bundle);changed[owner]+=b'\nUnapproved interpretation\n'
            with tempfile.TemporaryDirectory() as directory,self.assertRaises(Invalid):
                runtime.run_child(changed,'compile',payload(),directory)
        for change in ('comparator','weighting','estimand-type','feature-types','unaligned-manifest'):
            supplied=payload()
            if change=='comparator':supplied['candidate']['comparator']={'kind':'condition_complement'}
            elif change=='weighting':supplied['candidate']['estimand']['weighting']='instrument_weights'
            elif change=='estimand-type':supplied['candidate']['estimand']=None
            elif change=='feature-types':supplied['candidate']['feature_refs']=[None]
            else:supplied['data_manifest']['universe']['start']=stamp(T-1)
            with self.subTest(change=change),self.assertRaises(Invalid):runtime.compile_payload(supplied)


if __name__=='__main__':unittest.main()
