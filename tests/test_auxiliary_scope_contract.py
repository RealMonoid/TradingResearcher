"""D091 handoff is opt-in, exact, and separate from legacy review currency."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from trading_researcher import auxiliary_views as views, openai_provider as api
from trading_researcher.codec import Invalid, canonical, decode
from trading_researcher.meaning_reviews import policy_identity


def source(identity):
    return {'id':identity,'body':{'source_text':'Every original requirement stays present'},
            'source_refs':['a','b','a'],'exposure':['b','a']}


def packets():
    return [{'schema':'formalization-input/1','sources':[source('idea'),source('catalog')]},
            {'schema':'semantic-review-input/1','formalization':source('formalization'),
             'catalog':source('catalog'),'definitions':[source('definition')]}]


def request(packet,config):
    return {'model':api.MODEL,'prompt_version':'scope-handoff-test/1','tools':[],
            'generation_parameters':{'openai_responses':config},
            'messages':[{'role':'system','content':'Preserve independent review'},
                        {'role':'user','content':canonical(packet)}]}


class AuxiliaryScopeContractTests(unittest.TestCase):
    def test_both_roles_receive_same_exact_approved_contract_without_policy_change(self):
        policy=policy_identity();contracts=[]
        for packet in packets():
            config=api.configuration();config['source_presentation']=views.PROFILE
            config['bounded_math_scope']='bounded-math-reuse/1.0'
            original=request(packet,config);saved=deepcopy(original)
            wire=api.wire_request(original,config);view=decode(wire['input'][1]['content'])
            contract=view['activation_contract'];contracts.append(contract)
            self.assertEqual(contract['schema'],'bounded-math-reuse/1.0')
            self.assertEqual(contract['sha256'],'62cdb38908176ef91fe3368a8c41cdbd10a3f808499aa316e1ed863cf161a569')
            self.assertIn('Status: ACCEPTED',contract['text'])
            self.assertIn('> fortsetzen',contract['text'])
            self.assertEqual(views.restore(view),packet)
            self.assertEqual(original,saved)
        self.assertEqual(contracts[0],contracts[1]);self.assertEqual(policy_identity(),policy)

    def test_legacy_view_has_no_implicit_activation(self):
        for packet in packets():
            view=views.present(packet)
            self.assertNotIn('activation_contract',view)
            self.assertEqual(views.restore(view),packet)
            config=api.configuration();config['source_presentation']=views.PROFILE
            actual=decode(api.wire_request(request(packet,config),config)['input'][1]['content'])
            self.assertEqual(actual,view)

    def test_scope_requires_explicit_lossless_profile_and_supported_value(self):
        for scope in ('bounded-math-reuse/2',True,None,{},''):
            config=api.configuration();config['source_presentation']=views.PROFILE;config['bounded_math_scope']=scope
            with self.subTest(scope=scope),self.assertRaises(Invalid):api.wire_request(request(packets()[0],config),config)
        config=api.configuration();config['bounded_math_scope']='bounded-math-reuse/1.0'
        with self.assertRaises(Invalid):api.wire_request(request(packets()[0],config),config)

    def test_scope_document_and_transport_tamper_are_denied(self):
        view=views.present(packets()[0],bounded_math_scope='bounded-math-reuse/1.0')
        for field,value in [('text','forged authority'),('sha256','0'*64),('path','elsewhere'),('schema','invented')]:
            bad=deepcopy(view);bad['activation_contract'][field]=value
            with self.subTest(field=field),self.assertRaises(Invalid):views.restore(bad)
        with patch('pathlib.Path.read_bytes',return_value=b'not the approved contract'):
            with self.assertRaises(Invalid):views.present(packets()[0],bounded_math_scope='bounded-math-reuse/1.0')

    def test_config_mismatch_cannot_add_or_remove_authority(self):
        config=api.configuration();config['source_presentation']=views.PROFILE
        original=request(packets()[0],deepcopy(config));config['bounded_math_scope']='bounded-math-reuse/1.0'
        with self.assertRaises(Invalid):api.wire_request(original,config)
        original=request(packets()[0],deepcopy(config));del config['bounded_math_scope']
        with self.assertRaises(Invalid):api.wire_request(original,config)


if __name__=='__main__':unittest.main()
