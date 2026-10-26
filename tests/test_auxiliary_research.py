"""Shared auxiliary-role budgets and independent review transport, not semantic certification."""
from copy import deepcopy
import unittest

from trading_researcher.coordination import Denied, Invalid, Conflict
from trading_researcher.auxiliary import validate_judgment, validate_review_record
from trading_researcher.codec import canonical
import test_research_calls as call_support


class AuxiliaryBudgetTests(unittest.TestCase):
    setUp = call_support.ResearchCallTests.setUp
    tearDown = call_support.ResearchCallTests.tearDown
    op = call_support.ResearchCallTests.op
    setup_epoch = call_support.ResearchCallTests.setup_epoch
    reserve = call_support.ResearchCallTests.reserve
    finish = call_support.ResearchCallTests.finish
    complete_job = call_support.ResearchCallTests.complete_job

    def auxiliary(self, epoch, key='aux'):
        token=self.op('register_worker',name=key,role='formalizer',capabilities=['formalization/v1'])['token']
        idea=self.op('add_research',kind='idea',content={'text':'A preserved fixture idea'},scope={},source_refs=[])['id']
        catalog=self.op('add_source',body={'schema':'feature-catalog/1','features':{}},data_class='development')['id']
        context=self.op('create_context',role='formalizer',epoch=2,artifact_ids=[idea,catalog])['id']
        profile={'model':'fixture/1','prompt_version':'auxiliary-fixture/1','prompt':'Formalize this exact idea or retain its gap.',
            'generation_parameters':{},'max_output_tokens':64,'call_timeout_seconds':5,'max_retries':0}
        spec={'kind':'formalization/v1','context_id':context,'purpose':'Bounded fixture formalization',
            'allowed_workers':[key],'max_attempts':2,'lease_seconds':10,'deadline':1200,'dependencies':[],
            'research_epoch_id':epoch,'research_call_profile':profile,
            'research_inputs':{'idea_id':idea,'catalog_id':catalog,'definition_ids':[]}}
        return token,spec

    def first_done(self):
        epoch,lease=self.setup_epoch(max_tokens=80000)
        call=self.reserve(lease)
        self.finish(lease,call['call_id'],usage={'input_tokens':10,'output_tokens':20,'cost_units':0})
        self.complete_job(lease)
        # Complete the other discovery job without an adapter call: this tests
        # accounting transport only, not a genuine two-model discovery result.
        second=self.broker.call(self.tokens['second'],'claim')['lease']
        self.complete_job(second,'second')
        return epoch

    def test_auxiliary_call_uses_original_budget_and_private_profile(self):
        epoch=self.first_done()
        token,spec=self.auxiliary(epoch)
        self.op('enqueue',key='aux',spec=spec)
        lease=self.broker.call(token,'claim')['lease']
        state=self.broker.call(token,'research_call_state',lease=lease)
        self.assertEqual(state['calls'],[])
        self.assertEqual(state['profile']['prompts'],{'aux':spec['research_call_profile']['prompt']})
        packet=self.broker.call(token,'auxiliary_input',lease=lease)
        request={'model':'fixture/1','prompt_version':'auxiliary-fixture/1','generation_parameters':{},'tools':[],
            'messages':[{'role':'system','content':spec['research_call_profile']['prompt']},
                        {'role':'user','content':canonical(packet)}]}
        args={'lease':lease,'request':request,'input_token_bound':4096,'output_token_limit':64,'cost_bound_units':0}
        call=self.broker.call(token,'reserve_research_call',key='aux-call',**args)
        self.broker.call(token,'finish_research_call',lease=lease,call_id=call['call_id'],
            response={'status':'failed'},usage=None)
        with self.assertRaises(Denied):self.broker.call(token,'reserve_research_call',key='third',**args)
        self.assertEqual(self.op('inspect_research_epoch',epoch_id=epoch)['usage']['calls'],2)

    def test_auxiliary_creation_does_not_reset_expired_epoch(self):
        epoch=self.first_done()
        token,spec=self.auxiliary(epoch)
        self.now=1061
        self.op('enqueue',key='aux',spec=spec)
        lease=self.broker.call(token,'claim')['lease']
        packet=self.broker.call(token,'auxiliary_input',lease=lease)
        request={'model':'fixture/1','prompt_version':'auxiliary-fixture/1','generation_parameters':{},'tools':[],
            'messages':[{'role':'system','content':spec['research_call_profile']['prompt']},
                        {'role':'user','content':canonical(packet)}]}
        with self.assertRaises(Denied):
            self.broker.call(token,'reserve_research_call',lease=lease,key='expired',request=request,
                input_token_bound=4096,output_token_limit=64,cost_bound_units=0)
        self.assertEqual(self.op('inspect_research_epoch',epoch_id=epoch)['usage']['calls'],1)

    def test_auxiliary_profile_cannot_add_budget_or_bypass_epoch(self):
        epoch=self.first_done()
        _,spec=self.auxiliary(epoch)
        for variant in ('budget','no-epoch'):
            changed=deepcopy(spec)
            if variant=='budget':changed['research_call_profile']['max_calls']=999
            else:del changed['research_epoch_id']
            with self.assertRaises(Invalid):self.op('enqueue',key=variant,spec=changed)

    def test_recorded_response_identity_distinguishes_boolean_and_integer(self):
        _,lease=self.setup_epoch()
        call=self.reserve(lease)
        self.finish(lease,call['call_id'],response={'status':'completed','output':{'value':1}})
        with self.assertRaises(Conflict):
            self.finish(lease,call['call_id'],response={'status':'completed','output':{'value':True}})


class ReviewShapeTests(unittest.TestCase):
    def review(self):
        return {'judgment':'uncertain','reason':'There is no executable representation to assess.',
            'added_assumptions':[],'omitted_assumptions':[],'conflicts':[],'unresolved_meaning':['Candidate unavailable.'],
            'mapping_checks':[]}

    def test_missing_representation_still_allows_a_retained_uncertainty_report(self):
        record={'schema':'semantic-review-record/1','formalization_id':'target','formalizer_id':'author','reviewer_id':'reviewer',
            'scientific_readiness':False,'actual_independent_model_review':'UNVERIFIED','review':self.review()}
        validate_review_record(record,[{'id':'target','creator':'author','body':{'semantic_report':None}}])

    def test_malformed_judgment_has_a_typed_failure(self):
        for value in ([],{},True,None):
            with self.subTest(value=value), self.assertRaises(Invalid):
                validate_judgment({**self.review(),'judgment':value},0)


if __name__=='__main__':unittest.main()
