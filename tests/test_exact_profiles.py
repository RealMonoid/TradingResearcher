"""Actual generic role migration; no actual model, counting or admission call."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest

from trading_researcher.auxiliary import reporting_contract,request_for
from trading_researcher.codec import Invalid,canonical,decode
from trading_researcher.exact_profiles import build,request_candidate,VERSION
from trading_researcher.exact_research import contract_packet
from trading_researcher.openai_provider import wire_request

PATH=Path(__file__).parent/'fixtures/exact_formalizer_base_v3.json'
FIXTURE_SHA256='fb572a9246847b4f29f34850524d7dc3cacadd0348d16d71c4280c1e03c82362'
def fixture():
    raw=PATH.read_bytes();assert hashlib.sha256(raw).hexdigest()==FIXTURE_SHA256
    return json.loads(raw)


def packet():
    return {'schema':'formalization-input/1','context_id':'synthetic-profile-context-not-admitted',
        'inputs':{'expression_contract':'bounded-exact-compositions/1.0','reporting_contract':'case-diagnostics/2'},
        'idea':{'body':{'schema':'synthetic-role-input/1','text':'Untrusted synthetic original; no research result.'}},
        'sources':[],'catalog':{'body':{'features':{}}},'definitions':[],
        **contract_packet(),**reporting_contract({'reporting_contract':'case-diagnostics/2'})}


class ExactProfileTests(unittest.TestCase):
    def test_actual_roles_and_non_prompt_settings_are_preserved(self):
        source=fixture();before=canonical(source)
        made=build(source['formalization_profile'],source['review_profile'])
        self.assertEqual(canonical(source),before)
        formal=made['formalization_profile'];self.assertEqual(formal['prompt_version'],VERSION)
        for key in source['formalization_profile']:
            if key not in ('prompt','prompt_version'):self.assertEqual(formal[key],source['formalization_profile'][key])
        self.assertEqual(made['review_profile'],source['review_profile'])
        self.assertEqual(made['prompt_characters'],8186)
        self.assertEqual(made['formalizer_prompt_sha256'],'5d203c4ff5942b11f4b5a30350326a94c4caf0c6eaedcd85a5fc0aae4e5656ca')
        self.assertIs(made['native_admission'],False);self.assertIs(made['resource_limit_change'],False)
        self.assertEqual(made['configuration_freshness'],'NOT_CHECKED')

    def test_full_request_contracts_and_provider_wire_are_lossless(self):
        source=fixture();made=build(source['formalization_profile'],source['review_profile']);complete=packet()
        request=request_candidate(made,complete)
        self.assertEqual(request,request_for({'research_call_profile':made['formalization_profile']},complete))
        self.assertEqual(decode(request['messages'][1]['content']),complete)
        self.assertEqual(request['messages'][0]['content'],made['formalization_profile']['prompt'])
        wire=wire_request(request,made['formalization_profile']['generation_parameters']['openai_responses'])
        self.assertEqual(wire['model'],made['formalization_profile']['model'])
        self.assertEqual(wire['max_output_tokens'],32000)
        self.assertEqual(wire['reasoning']['effort'],source['formalization_profile']['generation_parameters']['openai_responses']['reasoning_effort'])

    def test_modified_source_prompt_or_independent_review_is_rejected(self):
        source=fixture()
        for field in ('prompt','prompt_version'):
            altered=deepcopy(source);altered['formalization_profile'][field]+=' modified'
            with self.subTest(field=field),self.assertRaises(Invalid):
                build(altered['formalization_profile'],altered['review_profile'])
        altered=deepcopy(source);altered['review_profile']['prompt']+=' omitted comparison obligations'
        with self.assertRaises(Invalid):build(altered['formalization_profile'],altered['review_profile'])

    def test_actual_complete_contract_bytes_are_required_without_scope_upgrade(self):
        source=fixture();made=build(source['formalization_profile'],source['review_profile'])
        for change in ('document','reporting','paired','construction','shape'):
            complete=packet();construction=deepcopy(made)
            if change=='document':complete['expression_contract']['documents'][0]['text']+=' changed'
            elif change=='reporting':complete.pop('reporting_contract')
            elif change=='paired':complete['paired_contract']={'schema':'paired-development/1.0'}
            elif change=='construction':construction['formalization_profile']['max_output_tokens']=1000
            else:construction={}
            with self.subTest(change=change),self.assertRaises(Invalid):request_candidate(construction,complete)


if __name__=='__main__':unittest.main()
