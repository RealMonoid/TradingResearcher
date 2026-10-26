"""Real retained-source compatibility plus parent-side transport fault checks."""
from copy import deepcopy
import hashlib
import json
import time
import unittest
from unittest.mock import patch

import study_stream_support as fixed
from trading_researcher import study_runs
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.evaluation_plans import source_bundle
from trading_researcher.study_stream import decode_stream


class StudyStreamTransportTests(unittest.TestCase):
    def test_real_old_source_and_new_source_have_identical_results_and_all_decoded_bytes(self):
        payload, manifest, world, cases = fixed.inputs()
        values = []; observations = []
        for label, source in [('retained_raw_0f1bf36', fixed.legacy_source()), ('encoded_current', source_bundle())]:
            meter = {'materialized_bytes':0}; outputs = []; start = time.monotonic()
            result, proofs = study_runs.execute_attempt(source, payload, manifest, world, cases,
                lambda:180, meter, outputs)
            seconds = time.monotonic()-start
            self.assertEqual(len(proofs), 2)
            self.assertEqual(result['outcome']['state'], 'VERIFIED')
            values.append((result, proofs, dict(outputs)))
            observations.append({'label':label, 'seconds':seconds, 'proof_count':len(proofs),
                'stream_bytes':proofs[0]['stream_blob']['size'],
                'materialized_bytes':meter['materialized_bytes'],
                'retained_bytes':sum(len(raw) for _,raw in outputs),
                'charged_bytes':meter['materialized_bytes']+sum(len(raw) for _,raw in outputs)+study_runs.METADATA_BYTES})
        old, new = values
        self.assertEqual(old[0], new[0])
        self.assertNotIn('stream_encoding', old[1][0])
        raw = old[2]['generate/stream.jsonl']
        encoded = new[2]['generate/stream.jsonl.gz']
        self.assertEqual(decode_stream(encoded, new[1][0]['stream_encoding']), raw)
        self.assertEqual(new[2]['replay/expected-stream.jsonl.gz'], encoded)
        self.assertEqual(new[1][0]['stream_encoding'], new[1][1]['stream_encoding'])
        self.assertEqual(sum(1 for line in raw.splitlines() if b'"kind":"draw"' in line), 79996)
        self.assertLess(len(encoded), len(raw))
        print(json.dumps({'benchmark':'same_fixed_mixed_family_actual_generate_and_replay',
            'observations':observations, 'result_sha256':digest(new[0]),
            'decoded_sha256':hashlib.sha256(raw).hexdigest(), 'decoded_bytes':len(raw),
            'draws':79996, 'complete_result_and_stream_equal':True,
            'qualification':'One paired synthetic observation; not full-series feasibility or market calibration.'}))

    def test_parent_rejects_format_switch_and_retains_both_prefix_types(self):
        payload, manifest, world, cases = fixed.inputs()
        source = {'trading_researcher/__init__.py':b''}; outputs=[]; meter={'materialized_bytes':0}
        import io
        from trading_researcher.study_stream import EncodedStream
        buffer=io.BytesIO(); stream=EncodedStream(buffer,encoded_limit=1024)
        stream.write(b'{}\n'); encoding=stream.finish(); encoded=buffer.getvalue()
        def child(command, directory, timeout):
            request=decode((directory/'request.json').read_bytes())
            generated=request['verify'] is None
            value=encoded if generated else b'{}\n'
            name='stream.jsonl.gz' if generated else 'expected-stream.jsonl'
            (directory/name).write_bytes(value)
            response={'result':{'outcome':{'state':'VERIFIED'}} if generated else {'verified_result_hash':request['verify']},
                'stream_blob':{'sha256':hashlib.sha256(value).hexdigest(),'size':len(value)},
                'request_hash':digest(request),'footprint':request['footprint'],'environment':{}}
            if generated:response['stream_encoding']=encoding
            return response
        with patch.object(study_runs,'_run_child',side_effect=child), \
                patch.object(study_runs,'_environment_current',return_value=True), \
                self.assertRaisesRegex(Invalid,'encoding differs'):
            study_runs.execute_attempt(source,payload,manifest,world,cases,lambda:10,meter,outputs)
        names=dict(outputs)
        self.assertEqual(names['generate/stream.jsonl.gz'],encoded)
        self.assertEqual(names['replay/expected-stream.jsonl.gz'],encoded)
        self.assertEqual(names['replay/expected-stream.jsonl'],b'{}\n')
        self.assertTrue(meter['accounting_complete'])
        self.assertGreaterEqual(meter['materialized_bytes'],2*len(encoded)+3)


if __name__=='__main__':unittest.main()
