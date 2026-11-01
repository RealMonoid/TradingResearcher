"""Lossless reference transport; fixed expectations independent of the decoder."""
from copy import deepcopy
import unittest

from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.auxiliary import request_for
from trading_researcher import auxiliary_views as views
from trading_researcher import openai_provider as api


def packet():
    return {'schema':'formalization-input/1','context_id':'context','inputs':{},'sources':[
        {'id':'first','body':{'text':'Exact original  \nβ','source_refs':['unencoded-body-reference']},
         'source_refs':['z','a'],'exposure':['a','z','a'],'authority':'unverified'},
        {'id':'second','body':{'meaning':'complete definition'},'source_refs':[],'exposure':['z']}],
        'availability_evidence':{'exposure':['not-an-artifact-field'],'qualification':'unchanged'}}

class ExactAuxiliaryViewTests(unittest.TestCase):
    def test_fixed_dictionary_expected_indices_and_complete_bodies(self):
        original=packet();before=canonical(original);view=views.present(original)
        self.assertEqual(view['reference_dictionary'],['a','z'])
        expected=deepcopy(original)
        expected['sources'][0]['source_refs']={'reference_indices':[1,0]}
        expected['sources'][0]['exposure']={'reference_indices':[0,1,0]}
        expected['sources'][1]['source_refs']={'reference_indices':[]}
        expected['sources'][1]['exposure']={'reference_indices':[1]}
        self.assertEqual(view['source_packet'],expected)
        self.assertEqual(view['source_packet_sha256'],digest(original))
        self.assertEqual(canonical(views.restore(view)),before)
        self.assertEqual(canonical(original),before)
    def test_review_roles_and_nested_record_fields_stay_complete(self):
        source=packet()['sources'][0]
        original={'schema':'semantic-review-input/1','formalization':source,'catalog':deepcopy(source),
            'definitions':[deepcopy(source)],'data_target':deepcopy(source),'qualification':'never evidence'}
        view=views.present(original)
        for key in ('formalization','catalog','data_target'):
            self.assertEqual(view['source_packet'][key]['body'],source['body'])
        self.assertEqual(views.restore(view),original)
    def test_malformed_forged_or_ambiguous_encodings_fail(self):
        base=views.present(packet())
        mutations=[]
        for index in (True,-1,2,'0',None):
            changed=deepcopy(base);changed['source_packet']['sources'][0]['source_refs']['reference_indices']=[index];mutations.append(changed)
        for dictionary in (['a','a'],['z','a'],[True],None):
            changed=deepcopy(base);changed['reference_dictionary']=dictionary;mutations.append(changed)
        changed=deepcopy(base);changed['source_packet']['sources'][0]['body']['text']='changed';mutations.append(changed)
        changed=deepcopy(base);changed['source_packet_sha256']='f'*64;mutations.append(changed)
        for changed in mutations:
            with self.subTest(changed=changed),self.assertRaises(Invalid):views.restore(changed)
    def test_legacy_request_is_exact_and_opt_in_is_explicit(self):
        config=api.configuration()
        spec={'research_call_profile':{'model':api.MODEL,'prompt_version':'v1','prompt':'Original prompt','generation_parameters':{'openai_responses':config}},'research_inputs':{}}
        original=packet();expected={'model':api.MODEL,'prompt_version':'v1','generation_parameters':{'openai_responses':config},'tools':[],
            'messages':[{'role':'system','content':'Original prompt'},{'role':'user','content':canonical(original)}]}
        self.assertEqual(request_for(spec,original),expected)
        legacy=api.wire_request(request_for(spec,original),config)
        self.assertEqual(legacy['input'],expected['messages'])
        config['source_presentation']=views.PROFILE
        request=request_for(spec,original)
        normalized=canonical(request)
        wire=api.wire_request(request,config)
        self.assertEqual(views.restore(decode(wire['input'][1]['content'])),original)
        self.assertEqual(canonical(request),normalized)
        self.assertEqual(request['messages'],expected['messages'])
        wire['input'][1]['content']=legacy['input'][1]['content']
        self.assertEqual(wire,legacy)
    def test_profile_cannot_transform_discovery_or_native_tool_history(self):
        config=api.configuration();config['source_presentation']=views.PROFILE
        base={'model':api.MODEL,'prompt_version':'v1','generation_parameters':{'openai_responses':config},'tools':[],
            'messages':[{'role':'system','content':'Original prompt'},{'role':'user','content':canonical(packet())}]}
        changes=[{'tools':[{}]}, {'messages':base['messages']+[{'role':'assistant','content':'{}'}]},
            {'messages':[{'role':'user','content':canonical(packet())}]},
            {'messages':[base['messages'][0],{'role':'user','content':'{"purpose":"discovery","sources":[]}'}]}]
        for change in changes:
            with self.subTest(change=change),self.assertRaises(Invalid):api.wire_request({**base,**change},config)
        for value in (None,True,{},'unsupported'):
            config['source_presentation']=value
            with self.assertRaises(Invalid):api.wire_request(base,config)

if __name__=='__main__':unittest.main()
