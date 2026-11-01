"""Exact formatting supplement at the frozen API boundary, never a source edit."""
from copy import deepcopy
import hashlib
import unittest
from trading_researcher import openai_provider as api
from trading_researcher.auxiliary_views import PROFILE, REUSE_SCOPE, restore
from trading_researcher.codec import Invalid, canonical, decode, text

SUFFIX = ('\nOutput serialization only: emit the entire final JSON object compactly, '
    'with no indentation, line breaks or whitespace outside JSON strings. '
    'Preserve every required key, complete AST, parameter origin, source reference, '
    'feature reference and semantic-report mapping. Do not abbreviate, omit, '
    'summarize, repair or change any scientific content. Whitespace inside strings '
    'must keep its intended content. If a faithful candidate is unavailable, retain '
    'the full required explicit gap report using the existing schema. '
    'This instruction changes formatting only; all earlier requirements still apply.')

def setup():
    cfg=api.configuration();cfg.update(source_presentation=PROFILE,bounded_math_scope=REUSE_SCOPE,
        output_formatting='compact-json/1')
    packet={'schema':'formalization-input/1','sources':[]}
    req={'model':api.MODEL,'prompt_version':'fixture','tools':[],
        'generation_parameters':{'openai_responses':deepcopy(cfg)},
        'messages':[{'role':'system','content':'x'*8012},{'role':'user','content':canonical(packet)}]}
    return cfg,req,packet

class CompactOutputTests(unittest.TestCase):
    def test_exact_append_at_wire_preserves_original_and_all_input(self):
        cfg,req,packet=setup();before=deepcopy(req)
        text(req['messages'][0]['content'],'original prompt')
        with self.assertRaises(Invalid):text(req['messages'][0]['content']+SUFFIX,'combined stored prompt')
        wire=api.wire_request(req,cfg)
        self.assertEqual(wire['input'][0]['content'],before['messages'][0]['content']+SUFFIX)
        self.assertEqual(restore(decode(wire['input'][1]['content'])),packet)
        self.assertEqual(req,before)

    def test_opt_in_cannot_be_injected_by_source_or_route_mismatch(self):
        cfg,req,packet=setup();del cfg['output_formatting']
        with self.assertRaises(Invalid):api.wire_request(req,cfg)
        req['generation_parameters']['openai_responses']=deepcopy(cfg)
        req['messages'][1]['content']=canonical({**packet,'output_formatting':'compact-json/1'})
        self.assertEqual(api.wire_request(req,cfg)['input'][0]['content'],req['messages'][0]['content'])

    def test_invalid_format_scope_or_tool_shape_is_denied(self):
        for name,value in [('output_formatting','compact-json/2'),('output_formatting',True),
                           ('bounded_math_scope',None),('source_presentation',None)]:
            cfg,req,_=setup();cfg[name]=value;req['generation_parameters']['openai_responses']=deepcopy(cfg)
            with self.subTest(name=name,value=value),self.assertRaises(Invalid):api.wire_request(req,cfg)
        cfg,req,_=setup();req['tools']=[{'name':'bad'}]
        with self.assertRaises(Invalid):api.wire_request(req,cfg)

if __name__=='__main__':unittest.main()
