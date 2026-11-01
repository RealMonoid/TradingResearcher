"""D098 role construction and full transport; no native/model admission."""
from copy import deepcopy
import unittest

from test_exact_profiles import fixture, packet
from trading_researcher.codec import Invalid, canonical, decode
from trading_researcher.auxiliary_views import restore
from trading_researcher.exact_profiles import build as build_v4
from trading_researcher.exact_profiles_v2 import build, request_candidate, resource_packet, review_request_candidate
from trading_researcher.openai_provider import wire_request


def complete_packet(kind='formalization-input/1'):
    result=packet()
    result['schema']=kind
    result['inputs']['resource_contract']='exact-computation-resources/2.0'
    result['resource_contract']=resource_packet()
    if kind=='semantic-review-input/1':
        result['formalization']={'id':'a'*64,'body':{'schema':'synthetic-review-target/1'},
            'source_refs':['b'*64],'exposure':['c'*64]}
        result['catalog']={'id':'b'*64,'body':{'features':{}},'source_refs':[],'exposure':[]}
        result['definitions']=[]
        result['inputs']['formalization_id']='a'*64
    return result


class ExactResourceProfileTests(unittest.TestCase):
    def test_only_approved_limit_and_version_change_from_complete_v4(self):
        source=fixture(); before=canonical(source)
        old=build_v4(source['formalization_profile'],source['review_profile'])
        made=build(source['formalization_profile'],source['review_profile'])
        self.assertEqual(made['formalization_profile']['prompt_version'],'faithful-exact-formalization/5')
        self.assertEqual(made['formalization_profile']['prompt'],
            old['formalization_profile']['prompt'].replace('10000000','20000000',1))
        self.assertEqual(made['review_profile'],old['review_profile'])
        self.assertEqual(made['prompt_characters'],8186)
        self.assertIs(made['native_admission'],False)
        self.assertEqual(canonical(source),before)

    def test_formalizer_and_reviewer_full_packets_restore_with_unchanged_settings(self):
        source=fixture(); made=build(source['formalization_profile'],source['review_profile'])
        for kind,builder,role in (('formalization-input/1',request_candidate,'formalization_profile'),
                ('semantic-review-input/1',review_request_candidate,'review_profile')):
            complete=complete_packet(kind); before=canonical(complete)
            request=builder(made,complete)
            self.assertEqual(decode(request['messages'][1]['content']),complete)
            self.assertEqual(request['messages'][0]['content'],made[role]['prompt'])
            config=made[role]['generation_parameters']['openai_responses']
            wire=wire_request(request,config)
            self.assertEqual(wire['model'],made[role]['model'])
            self.assertEqual(wire['max_output_tokens'],made[role]['max_output_tokens'])
            self.assertEqual(wire['reasoning']['effort'],config['reasoning_effort'])
            self.assertEqual(restore(decode(wire['input'][1]['content'])),complete)
            self.assertEqual(canonical(complete),before)

    def test_old_packets_and_changed_resource_contract_or_construction_reject(self):
        source=fixture(); made=build(source['formalization_profile'],source['review_profile'])
        for label in ('old_packet','resource_text','resource_limit','construction'):
            complete=complete_packet(); candidate=deepcopy(made)
            if label=='old_packet':complete=packet()
            elif label=='resource_text':complete['resource_contract']['documents'][0]['text']+=' changed'
            elif label=='resource_limit':complete['resource_contract']['per_child_primitive_steps']=10000000
            else:candidate['formalization_profile']['max_output_tokens']=1000
            with self.subTest(label=label), self.assertRaises(Invalid):request_candidate(candidate,complete)


if __name__=='__main__':unittest.main()
