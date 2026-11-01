"""Native controller/mixin fixture; not a funded finite-inquiry qualification."""
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.auxiliary import request_for
from trading_researcher.codec import canonical, digest, Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.exact_formalization import CONTRACT, SCHEMA
from trading_researcher.exact_research import ExactResearch, ExactInquiryBroker, contract_packet, LOADED


class NativeFixtureBroker(ExactResearch, Broker):
    """Exercise actual SQLite/auth/lease methods without simulating live admission."""


class ExactResearchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.now = 1000
        self.broker = NativeFixtureBroker(self.tmp.name, clock=lambda:self.now)
        self.addCleanup(self.broker.close)
        self.admin = self.broker.admin_token
        for name in ('first','second'):
            self.op('register_worker',name=name,role='discovery',capabilities=['research-record/v1'])
        self.tokens = {name:self.op('register_worker',name=name,role='formalizer',
            capabilities=['formalization/v1','semantic-review/v1'])['token'] for name in ('author','reviewer')}
        context = self.op('create_context',role='discovery',epoch=1,artifact_ids=[])['id']
        self.profile = {'model':'fixture/1','prompt_version':'fixture/1','max_calls':6,'max_tokens':80000,
            'max_seconds':120,'max_cost_units':0,'currency':'NONE','mode':'fixture',
            'prompts':{'first':'Independent synthetic fixture','second':'Isolated synthetic fixture'},
            'tools':[],'generation_parameters':{},'max_output_tokens':2048,'call_timeout_seconds':5,'max_retries':0}
        self.epoch = self.op('create_research_epoch',key='fixture-epoch',context_id=context,
            workers=['first','second'],profile=self.profile)['id']
        self.original = 'Synthetic native draft; retain all unknowns and provenance.'
        self.idea = self.op('add_research',kind='idea',content={'text':self.original},scope={},source_refs=[])['id']
        self.catalog = {'x@1':{'type':'real','unit':'ratio'}}
        self.catalog_id = self.op('add_source',body={'schema':'feature-catalog/1','features':self.catalog},data_class='development')['id']
        # This isolated host/mixin test explicitly seeds prior owned definition
        # metadata. It does not qualify feature certification or finite admission.
        with self.broker._transaction():
            self.definition = self.broker._save_artifact({'version':'local-artifact/1',
                'creator':'controller','origin':'source','data_class':'development',
                'body':{'schema':'feature-definitions/1','created_at':self.now,'input_refs':[self.catalog_id],
                    'definitions':[{'feature_ref':'x@1','type':'real','unit':'ratio',
                        'meaning':'Purely synthetic ratio; no market evidence'}]},
                'source_refs':[self.catalog_id],'exposure':[self.catalog_id],
                'authority':'synthetic-test-seed-not-feature-certificate'})['id']
        self.candidate = self.make_candidate()
        self.mapping = {'status':'equivalent','segments':[{'text':self.original,'path':'/condition_ast',
            'interpretation':'Fixture assertion only; independent model review still required.'}],'differences':[]}
        self.formal_spec = self.spec('formalization/v1','author',[self.idea,self.catalog_id,self.definition],
            {'idea_id':self.idea,'catalog_id':self.catalog_id,'definition_ids':[self.definition]})

    def op(self,operation,**args):
        return self.broker.call(self.admin,operation,**args)

    def program(self,node):
        return {'schema':'research-ast/4','catalog_hash':digest(self.catalog),'expression':node}

    def make_candidate(self):
        feature = {'op':'feature','ref':'x@1'}
        lag = {'op':'lag','bars':1,'arg':feature}
        lit = lambda value,unit:{'op':'literal','type':'real','unit':unit,'value':str(value)}
        return {'schema':'hypothesis-exec/3','idea_ref':self.idea,'claim_kind':'difference',
            'scope_ast':self.program({'op':'literal','type':'boolean','unit':None,'value':True}),
            'condition_ast':self.program({'op':'gt','left':{'op':'integer_power','arg':lag,'exponent':2},
                'right':lit(1,'ratio')}),
            'outcome':{'scale':'quantity','program':self.program({'op':'mul','left':lit(1,'basis_points'),
                'right':{'op':'abs','arg':lag}})},
            'comparator':{'kind':'whole_scope'},'horizons':{'grid_seconds':900,'outcome_bars':2},
            'test_universe':{'start':'2023-01-01T00:00:00Z','end':'2023-01-02T00:00:00Z',
                'instruments':['SYNTHETIC'],'data_snapshot_ref':self.catalog_id},
            'estimand':{'kind':'conditional-minus-scope-mean/1','unit':'basis_points','weighting':'equal_rows',
                'missingness':'scope-true-outcome-observed/1','condition_unknown':'exclude-from-condition-retain-in-scope',
                'nuisance_fit':'none','direction':'positive'},'feature_refs':['x@1'],
            'parameter_origins':[{'path':path,'basis':'preexisting_specification','source_refs':[],
                'rationale':'Fixed synthetic interface fixture only.'} for path in (
                    '/scope_ast/expression/value','/condition_ast/expression/left/exponent',
                    '/condition_ast/expression/left/arg/bars','/condition_ast/expression/right/value',
                    '/outcome/program/expression/left/value','/outcome/program/expression/right/arg/bars',
                    '/horizons/outcome_bars')]}

    def spec(self,kind,worker,refs,inputs):
        context = self.op('create_context',role='formalizer',epoch=2 if kind == 'formalization/v1' else 3,artifact_ids=refs)['id']
        return {'kind':kind,'context_id':context,'purpose':'Synthetic native exact interface',
            'allowed_workers':[worker],'max_attempts':1,'lease_seconds':10,'deadline':1200,'dependencies':[],
            'research_epoch_id':self.epoch,'research_call_profile':{'model':'fixture/1','prompt_version':'synthetic-aux/1',
                'prompt':'Retain exact inputs and return a fixture result; no actual independent judgment.',
                'generation_parameters':{},'max_output_tokens':2048,'call_timeout_seconds':5,'max_retries':0},
            'research_inputs':{**inputs,'expression_contract':CONTRACT,'reporting_contract':'case-diagnostics/2'}}

    def provider_response(self,spec,worker,output,key):
        self.op('enqueue',key=key,spec=spec)
        token = self.tokens[worker]
        lease = self.broker.call(token,'claim')['lease']
        packet = self.broker.call(token,'auxiliary_input',lease=lease)
        call = self.broker.call(token,'reserve_research_call',lease=lease,key=key+'-call',
            request=request_for(spec,packet),input_token_bound=65000,output_token_limit=2048,cost_bound_units=0)
        self.broker.call(token,'finish_research_call',lease=lease,call_id=call['call_id'],
            response={'status':'completed','output':output},usage={'input_tokens':100,'output_tokens':100,'cost_units':0})
        return lease,call['call_id'],packet

    def formalize(self,candidate=None,key='formalize'):
        candidate = self.candidate if candidate is None else candidate
        lease,call,packet = self.provider_response(self.formal_spec,'author',
            {'status':'final','candidate':candidate,'semantic_report':self.mapping},key)
        saved = self.broker.call(self.tokens['author'],'record_formalization',lease=lease,
            idea_id=self.idea,catalog_id=self.catalog_id,candidate=candidate,semantic_report=self.mapping,provider_call_id=call)
        return saved,lease,packet

    def accepted(self):
        saved,lease,packet = self.formalize()
        result = self.broker.call(self.tokens['author'],'submit',lease=lease,artifact_id=saved['id'])
        self.assertTrue(result['accepted'])
        batch = self.op('inspect',job_id=lease['job_id'])['batch_id']
        self.op('release_batch',batch_id=batch,target_epoch=3)
        return saved,lease,packet

    def test_native_commit_submit_idempotence_and_separate_original(self):
        saved,lease,_ = self.formalize()
        record = self.op('get_artifact',artifact_id=saved['id'])
        self.assertEqual(record['body']['schema'],SCHEMA)
        self.assertEqual(record['body']['assessment']['status'],'STRUCTURE_CHECKED')
        self.assertEqual(record['body']['candidate'],self.candidate)
        self.assertEqual(record['body']['original_idea']['content']['text'],self.original)
        self.assertFalse(record['body']['scientific_readiness'])
        self.assertTrue({self.idea,self.catalog_id,self.definition} <= set(record['exposure']))
        result = self.broker.call(self.tokens['author'],'submit',lease=lease,artifact_id=saved['id'])
        self.assertTrue(result['accepted']);self.assertFalse(result['scientific_authority'])
        self.assertEqual(self.broker.call(self.tokens['author'],'submit',lease=lease,artifact_id=saved['id']),result)
        with self.assertRaises(Conflict):
            self.broker.call(self.tokens['author'],'submit',lease=lease,artifact_id=self.idea)

    def test_record_cannot_change_authenticated_response_or_use_wrong_worker(self):
        lease,call,_ = self.provider_response(self.formal_spec,'author',
            {'status':'final','candidate':self.candidate,'semantic_report':self.mapping},'exact-response')
        changed = deepcopy(self.candidate);changed['horizons']['outcome_bars'] = 3
        before = self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0]
        with self.assertRaises(Invalid):
            self.broker.call(self.tokens['author'],'record_formalization',lease=lease,
                idea_id=self.idea,catalog_id=self.catalog_id,candidate=changed,semantic_report=self.mapping,provider_call_id=call)
        with self.assertRaises(Denied):
            self.broker.call(self.tokens['reviewer'],'record_formalization',lease=lease,
                idea_id=self.idea,catalog_id=self.catalog_id,candidate=self.candidate,semantic_report=self.mapping,provider_call_id=call)
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM artifacts').fetchone()[0],before)

    def test_both_roles_receive_identical_complete_contract_bytes(self):
        saved,_,first = self.accepted()
        spec = self.spec('semantic-review/v1','reviewer',[saved['id'],self.idea,self.catalog_id,self.definition],
            {'formalization_id':saved['id'],'definition_ids':[self.definition]})
        self.op('enqueue',key='review-contract',spec=spec)
        lease = self.broker.call(self.tokens['reviewer'],'claim')['lease']
        second = self.broker.call(self.tokens['reviewer'],'auxiliary_input',lease=lease)
        self.assertEqual(first['expression_contract'],second['expression_contract'])
        self.assertEqual(second['formalization'],self.op('get_artifact',artifact_id=saved['id']))
        self.assertEqual(second['formalization']['body']['original_idea']['content']['text'],self.original)
        self.assertEqual(second['expression_contract']['candidate_schema'],'hypothesis-exec/3')
        for document in second['expression_contract']['documents']:
            raw = (Path(__file__).resolve().parents[1]/document['path']).read_bytes()
            self.assertEqual(document['text'].encode('utf-8'),raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(),document['sha256'])

    def test_same_worker_contract_change_or_unrelated_review_context_is_denied(self):
        saved,_,_ = self.accepted()
        refs = [saved['id'],self.idea,self.catalog_id,self.definition]
        for variant in ('same-worker','reporting','expression','unrelated'):
            worker = 'author' if variant == 'same-worker' else 'reviewer'
            selected_refs = list(refs)
            if variant == 'unrelated':
                selected_refs.append(self.op('add_source',body={'unrelated':True},data_class='development')['id'])
            spec = self.spec('semantic-review/v1',worker,selected_refs,
                {'formalization_id':saved['id'],'definition_ids':[self.definition]})
            if variant == 'reporting':spec['research_inputs']['reporting_contract'] = 'case-diagnostics/1'
            if variant == 'expression':spec['research_inputs']['expression_contract'] = 'different/1'
            with self.subTest(variant=variant), self.assertRaises((Invalid,Denied)):
                self.op('enqueue',key=variant,spec=spec)

    def test_source_drift_and_generic_namespace_forgery_are_denied(self):
        with patch.dict(LOADED,{'trading_researcher/exact_formalization.py':'0'*64}):
            with self.assertRaises(Invalid):contract_packet()
        for schema in ('formalization-record/3',):
            with self.assertRaises(Invalid):
                self.op('add_source',body={'schema':schema},data_class='development')
        self.op('enqueue',key='namespace',spec=self.formal_spec)
        lease = self.broker.call(self.tokens['author'],'claim')['lease']
        with self.assertRaises(Invalid):
            self.broker.call(self.tokens['author'],'put_artifact',lease=lease,body={'schema':SCHEMA},source_refs=[])

    def test_expired_lease_cannot_commit_even_after_response(self):
        lease,call,_ = self.provider_response(self.formal_spec,'author',
            {'status':'final','candidate':self.candidate,'semantic_report':self.mapping},'expired')
        self.now += 11
        with self.assertRaises(Denied):
            self.broker.call(self.tokens['author'],'record_formalization',lease=lease,
                idea_id=self.idea,catalog_id=self.catalog_id,candidate=self.candidate,semantic_report=self.mapping,provider_call_id=call)

    def test_completed_fixture_review_remains_without_independent_model_authority(self):
        saved,_,_ = self.accepted()
        spec = self.spec('semantic-review/v1','reviewer',[saved['id'],self.idea,self.catalog_id,self.definition],
            {'formalization_id':saved['id'],'definition_ids':[self.definition]})
        from trading_researcher.meaning_reviews import PROMPT, PROTOCOL
        spec['research_call_profile'].update(prompt=PROMPT,prompt_version=PROTOCOL)
        review = {'judgment':'faithful','reason':'Synthetic fixture assertion; no actual model.',
            'added_assumptions':[],'omitted_assumptions':[],'conflicts':[],'unresolved_meaning':[],
            'mapping_checks':[{'segment':0,'judgment':'faithful','reason':'Fixture only.'}]}
        lease,call,_ = self.provider_response(spec,'reviewer',{'status':'final','review':review},'review-fixture')
        recorded = self.broker.call(self.tokens['reviewer'],'record_semantic_review',lease=lease,call_id=call)
        result = self.broker.call(self.tokens['reviewer'],'submit',lease=lease,artifact_id=recorded['id'])
        self.assertTrue(result['accepted']);self.assertFalse(result['scientific_authority'])
        assessment = self.op('assess_meaning_review',key='fixture-meaning',formalization_id=saved['id'])
        self.assertEqual(assessment['body']['independent_semantic_review'],'NOT_SATISFIED')
        self.assertTrue(any(gap['code'] == 'REVIEW_PROVENANCE_GAP' for gap in assessment['body']['gaps']))

    def test_all_retained_gap_drafts_are_released_after_completed_batch(self):
        changed = deepcopy(self.candidate);changed['claim_kind'] = 'association'
        lease,call,_ = self.provider_response(self.formal_spec,'author',
            {'status':'final','candidate':changed,'semantic_report':self.mapping},'gap-drafts')
        token = self.tokens['author']
        gap_draft = self.broker.call(token,'record_formalization',lease=lease,idea_id=self.idea,
            catalog_id=self.catalog_id,candidate=changed,semantic_report=self.mapping,provider_call_id=call)
        self.assertEqual(gap_draft['assessment']['status'],'RETAINED_GAP')
        # Re-staging the same authenticated reply inherits the first retained
        # draft/journal. This is no new call, retry, candidate or claimed repair.
        good = self.broker.call(token,'record_formalization',lease=lease,idea_id=self.idea,
            catalog_id=self.catalog_id,candidate=changed,semantic_report=self.mapping,provider_call_id=call)
        self.assertEqual(good['assessment']['status'],'RETAINED_GAP')
        self.assertNotEqual(gap_draft['id'],good['id'])
        self.broker.call(token,'submit',lease=lease,artifact_id=good['id'])
        batch = self.op('inspect',job_id=lease['job_id'])['batch_id']
        released = self.op('release_batch',batch_id=batch,target_epoch=3)
        self.assertIn(gap_draft['id'],released['artifact_ids'])
        self.assertIn(good['id'],released['artifact_ids'])
        self.op('create_context',role='formalizer',epoch=3,artifact_ids=[gap_draft['id']])
        self.assertEqual(self.op('release_batch',batch_id=batch,target_epoch=3),released)

    def test_contract_text_matches_bound_bytes_with_crlf_source_representation(self):
        guide = 'trading_researcher/EXACT_RESEARCH.md'
        root = Path(__file__).resolve().parents[1]
        read = Path.read_bytes
        altered = read(root/guide).replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')
        def source(path):
            return altered if path == root/guide else read(path)
        # Simulate a fresh loaded closure with a different allowed guide byte
        # representation; the source is still bound and must be sent verbatim.
        with patch.object(Path,'read_bytes',source), patch.dict(LOADED,{guide:hashlib.sha256(altered).hexdigest()}):
            packet = contract_packet()
        doc = next(doc for doc in packet['expression_contract']['documents'] if doc['path'] == guide)
        self.assertEqual(doc['text'].encode('utf-8'),altered)


class ExactEntryPointTests(unittest.TestCase):
    def test_explicit_finite_entry_initializes_and_extends_source_identity(self):
        # This exercises actual constructor/source/currentness composition.
        # No finite epoch, allocation, source certificate or API is created.
        with tempfile.TemporaryDirectory() as temp:
            broker = ExactInquiryBroker(temp,clock=lambda:1000)
            try:
                sources = broker._breakout_research_sources()
                self.assertTrue(set(LOADED) <= set(sources))
                self.assertEqual({path:sources[path] for path in LOADED},LOADED)
                self.assertEqual(broker.call(broker.admin_token,'verify')['status'],'PASS')
                self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM research_epochs').fetchone()[0],0)
            finally:
                broker.close()


if __name__ == '__main__':unittest.main()
