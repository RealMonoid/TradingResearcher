"""Independent transport invariants; fixed hashes come from retained OLD source.

Authored after the optimization appeared, not claimed as pre-implementation TDD.
The old calculator SHA was c37b316304739004abaa822f0c460363db34ca86b000c18081cdb688df9d8881.
No randomness, draw count, undefined-value or statistical-policy substitution.
"""
from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bootstrap_support import report
import test_information_study as study_fixture
from trading_researcher import stationary_bootstrap as bootstrap
from trading_researcher import study_pipeline as pipeline
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.information_study import make_manifest


def design():
    return {'base_length':1,'primary_count':1,'randomness':bootstrap.randomness(713)}


def limits():
    return {'max_seconds':60,'max_segments':2000000}


class DrawTransportAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=[];cls.raw=[]
        cls.result=bootstrap.calculate(report(times=4,rare=True),design(),limits(),
            on_draw=cls.rows.append,on_draw_bytes=cls.raw.append)

    def test_fixed_old_hashes_counts_and_undefined_draws(self):
        self.assertEqual(len(self.rows),39998)
        self.assertEqual(self.result['status'],'INFORMATION_GAP')
        self.assertEqual(self.result['reason'],'undefined_resampled_mean')
        self.assertIsNone(self.result['interval'])
        expected=[(1,13681,6318,'44890712739ec3fb70ded193186b99e2d46afed087dcca40daa5e20bba018c06'),
                  (2,15636,4363,'65ee524c8a67bc99411c23861df64a0e2323e2de66f343790e0f741766d3f730')]
        self.assertEqual([(x['length'],x['defined'],x['undefined'],x['replicate_sha256'])
            for x in self.result['cases']],expected)
        self.assertEqual(hashlib.sha256(b''.join(x+b'\n' for x in self.raw)).hexdigest(),
            '81df56509ede327ff35d4c13fd46e919feeed35bd037b2a93c7e3d314a12b938')
        self.assertEqual([x['value'] for x in self.rows[:3]],
            [None,None,{'numerator':'0','denominator':'1'}])
        self.assertEqual([x['condition_count'] for x in self.rows[:3]],[0,0,2])
        self.assertFalse(self.result['scientific_readiness'])
        self.assertFalse(self.result['classification_permitted'])

    def test_bytes_are_exact_canonical_values_without_newline(self):
        self.assertEqual(self.raw,[canonical(row).encode('utf-8') for row in self.rows])
        self.assertTrue(all(type(raw) is bytes and not raw.endswith(b'\n') for raw in self.raw))
        for case in self.result['cases']:
            subset=[raw for raw,row in zip(self.raw,self.rows) if row['length']==case['length']]
            self.assertEqual(len(subset),19999)
            self.assertEqual(case['replicate_sha256'],hashlib.sha256(b''.join(x+b'\n' for x in subset)).hexdigest())

    def test_legacy_nested_mutation_cannot_change_bytes_or_result(self):
        source=report(times=4,rare=True);before=deepcopy(source);raw=[]
        def mutate(row):
            if row['value'] is not None:row['value']['numerator']='999'
            row.clear();row['injected']=['not a retained draw']
        result=bootstrap.calculate(source,design(),limits(),on_draw=mutate,on_draw_bytes=raw.append)
        self.assertEqual(raw,self.raw)
        self.assertEqual(result,self.result)
        self.assertEqual(source,before)

    def test_bytes_only_and_no_sink_leave_numerical_output_identical(self):
        raw=[]
        self.assertEqual(bootstrap.calculate(report(times=4,rare=True),design(),limits(),
            on_draw_bytes=raw.append),self.result)
        self.assertEqual(raw,self.raw)
        self.assertEqual(bootstrap.calculate(report(times=4,rare=True),design(),limits()),self.result)

    def test_callback_type_validation_precedes_draws_and_input_gap(self):
        for name in ('on_draw','on_draw_bytes'):
            for invalid in (False,0,'callable',[],{}):
                with self.subTest(name=name,invalid=invalid),self.assertRaises(Invalid):
                    bootstrap.calculate(report(as_of=900),design(),limits(),**{name:invalid})

    def test_exceptions_from_either_sink_propagate_unchanged(self):
        for name in ('on_draw','on_draw_bytes'):
            failure=OSError('synthetic retained-stream write failure');seen=[]
            def fail(value):
                seen.append(value)
                raise failure
            with self.subTest(name=name),self.assertRaises(OSError) as caught:
                bootstrap.calculate(report(times=4,rare=True),design(),limits(),**{name:fail})
            self.assertIs(caught.exception,failure)
            self.assertEqual(len(seen),1)

    def test_cancelled_prefix_keeps_identical_completed_draws(self):
        results=[];streams=[]
        for name in ('on_draw','on_draw_bytes'):
            raw=[]
            def retain(value):raw.append(value if type(value) is bytes else canonical(value).encode())
            result=bootstrap.calculate(report(times=4,rare=True),design(),limits(),
                stop=lambda:len(raw)>=3,**{name:retain})
            self.assertEqual(result['status'],'RESOURCE_STOP')
            self.assertEqual(result['reason'],'caller_cancelled')
            self.assertEqual(raw,self.raw[:3])
            self.assertEqual(result['cases'][0]['replicate_sha256'],
                hashlib.sha256(b''.join(x+b'\n' for x in raw)).hexdigest())
            results.append(result);streams.append(raw)
        self.assertEqual(results[0],results[1])
        self.assertEqual(streams[0],streams[1])

    def test_partial_draw_and_pending_input_do_not_emit_completed_draw(self):
        rows=[];raw=[]
        result=bootstrap.calculate(report(times=4,rare=True),design(),
            {'max_seconds':60,'max_segments':1},on_draw=rows.append,on_draw_bytes=raw.append)
        self.assertEqual(result['status'],'RESOURCE_STOP')
        self.assertEqual(result['cases'][0]['interrupted'],1)
        self.assertEqual(result['cases'][0]['interrupted_draw']['sampled_times'],1)
        self.assertEqual((rows,raw),([],[]))
        pending=bootstrap.calculate(report(as_of=900),design(),limits(),
            on_draw=rows.append,on_draw_bytes=raw.append)
        self.assertEqual(pending['status'],'INPUT_GAP')
        self.assertEqual((rows,raw),([],[]))

    def test_real_population_pipeline_keeps_all_ordered_stream_and_result_bytes(self):
        source=json.loads((Path(__file__).parent/'fixtures/information_diagnostics_cases.json').read_text())['fixtures'][0]['report']
        payload={'report':{k:v for k,v in source.items() if k!='cases'},'diagnostics':diagnose(source,[1,2])}
        assigned={**study_fixture.assigned(),'base_length':1,'instruments':2}
        profile=study_fixture.profile();profile['targets']=[16]
        profile['budget']['attempt_compute_ms']=60000
        manifest=make_manifest(assigned,profile);world=manifest['worlds'][0]
        before=deepcopy((payload,manifest,world,source));legacy=[];fast=[]
        first=pipeline.calculate_world(payload,manifest,world,source['cases'],
            lambda record:legacy.append((canonical(record)+'\n').encode()))
        second=pipeline.calculate_world(payload,manifest,world,source['cases'],
            lambda record:fast.append((canonical(record)+'\n').encode()),
            retain_draw_bytes=lambda raw:fast.append(b'{"kind":"draw","value":'+raw+b'}\n'))
        self.assertEqual(canonical(first),canonical(second))
        self.assertEqual(legacy,fast)
        self.assertEqual(sum(decode(line)['kind']=='draw' for line in fast),39998)
        self.assertEqual((payload,manifest,world,source),before)


class ChildDrawFramingAdversarialTests(unittest.TestCase):
    """Actual child writer/replay logic with a deterministic synthetic calculator.

    Source/environment discovery is mocked only to avoid a second archive build.
    The parent separately runs real isolated generation and replay children.
    """
    records=[{'kind':'case','value':{'note':'escaped " quote, newline\n and unicode ä'}},
        {'kind':'draw','value':{'index':0,'value':None,'condition_count':0}},
        {'kind':'draw','value':{'index':1,'value':{'numerator':'0','denominator':'1'}}}]
    result={'schema':'synthetic-child-result/1','scientific_readiness':False}

    def run_child(self,directory,*,verify=None,stream_limit=None,expected=None):
        root=Path(directory);case_raw=b'{}\n';(root/'cases.jsonl').write_bytes(case_raw)
        if expected is not None:(root/'expected-stream.jsonl').write_bytes(expected)
        request={'footprint':'fixed-test-footprint','payload':{'case_blob':{
            'sha256':hashlib.sha256(case_raw).hexdigest(),'size':len(case_raw)}},
            'verify':verify,'manifest':{},'world':{},
            'stream_limit':len(self.expected()) if stream_limit is None else stream_limit}
        path=root/'request.json';path.write_text(canonical(request),encoding='utf8')
        def calculate(payload,manifest,world,cases,retain,*,retain_draw_bytes):
            retain(deepcopy(self.records[0]))
            for record in self.records[1:]:retain_draw_bytes(canonical(record['value']).encode())
            return deepcopy(self.result)
        output=io.StringIO()
        with patch.object(pipeline,'source_bundle',return_value={}),\
                patch.object(pipeline,'footprint',return_value='fixed-test-footprint'),\
                patch.object(pipeline,'environment',return_value={'test':True}),\
                patch.object(pipeline,'calculate_world',side_effect=calculate),redirect_stdout(output):
            pipeline.child_entry(path)
        return decode(output.getvalue())

    def expected(self):
        return b''.join((canonical(record)+'\n').encode() for record in self.records)

    def test_actual_child_writer_exact_utf8_framing_digest_limit_and_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            result=self.run_child(directory)
            self.assertEqual((Path(directory)/'stream.jsonl').read_bytes(),self.expected())
            self.assertEqual(result['stream_blob'],{'size':len(self.expected()),
                'sha256':hashlib.sha256(self.expected()).hexdigest()})
            replay=self.run_child(directory,verify=digest(self.result),expected=self.expected())
            self.assertEqual(replay['stream_blob'],result['stream_blob'])
            self.assertEqual(replay['result'],{'verified_result_hash':digest(self.result)})

    def test_actual_child_rejects_first_byte_over_limit_retaining_only_complete_prefix(self):
        prefix=b''.join((canonical(record)+'\n').encode() for record in self.records[:-1])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(Invalid,'reserved storage'):
                self.run_child(directory,stream_limit=len(self.expected())-1)
            self.assertEqual((Path(directory)/'stream.jsonl').read_bytes(),prefix)
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(Invalid,'reserved storage'):
                self.run_child(directory,verify=digest(self.result),expected=self.expected(),
                    stream_limit=len(self.expected())-1)

    def test_actual_child_replay_rejects_tampered_missing_extra_bytes_and_result(self):
        for expected,verify in ((b'!'+self.expected()[1:],digest(self.result)),
                (self.expected()[:-1],digest(self.result)),(self.expected()+b'\n',digest(self.result)),
                (self.expected(),'0'*64)):
            with self.subTest(size=len(expected),verify=verify),tempfile.TemporaryDirectory() as directory:
                with self.assertRaisesRegex(Invalid,'replay differs'):
                    self.run_child(directory,verify=verify,expected=expected)


if __name__=='__main__':unittest.main()
