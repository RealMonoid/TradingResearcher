"""Independent opt-in resource boundaries; no production or provider access.

BudgetHost substitutes only source qualification and complete-packet construction
and uses a real temporary shared ledger and call inventory. Actual Broker tests
retain authentication, dispatch, immutable invocation and settlement machinery;
only network transport is mocked. These are not model-quality/source-cert tests.
"""
import ast
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
import hashlib
import inspect
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import Mock, patch

import controller_provider_support as controller_support
import test_paired_host_adversarial as support
from trading_researcher import epoch_budget as ordinary, complete_feedback_budget as complete
from trading_researcher import paired_budget as previous, paired_correction_budget as correction
from trading_researcher import epoch_budget_dispatch as legacy_dispatch, openai_provider as openai
from trading_researcher.auxiliary import request_for
from trading_researcher.codec import canonical, digest
from trading_researcher.controller_providers import ControllerProviders
from trading_researcher.feedback_budget_broker import FeedbackBudgetBroker
from trading_researcher.paired_broker import PairedBroker
from trading_researcher.paired_breakout import budget, dispatch, research, providers
from trading_researcher.paired_breakout.research import BreakoutResearchBroker

REJECTIONS = support.REJECTIONS
BASE_PROMPT = 'Independent complete synthetic paired prompt.' + openai.COMPACT_OUTPUT_SUFFIX
PROMPT = BASE_PROMPT[:-len(openai.COMPACT_OUTPUT_SUFFIX)] + budget.FORMAT_CLARIFICATION + openai.COMPACT_OUTPUT_SUFFIX


def seed_priors(host, *, omit=None, open_grant=None, empty=None):
    """Explicit synthetic historical grants, never actual provider usage."""
    with host.ledger._connect() as db:
        ordinary._schema(db)
        for identity in budget.PRIOR_APPROVALS:
            if identity == omit: continue
            calls = [] if identity == empty else [{'call_id': 'synthetic-prior-'+identity}]
            db.execute('INSERT INTO research_epoch_budget_grants VALUES(?,?,?,?)',
                (identity, canonical({'fixture': 'SYNTHETIC_PRIOR_ONLY'}), canonical(calls), int(identity != open_grant)))


class BudgetHost(support.BudgetHost):
    BREAKOUT_RESEARCH_RUNTIME = True

    def __init__(self, root):
        super().__init__(root)
        self.context['artifact_ids'] = [budget.IDEA]
        self.epoch['request']['budget_overlay'] = budget.POLICY
        self.epoch['request_key'] = 'separate-second-original-once'
        self.profile['max_cost_units'] = 700000000
        self.profile['max_output_tokens'] = 32000
        config = self.profile['generation_parameters']['openai_responses']
        config.update(input_token_limit=48000,output_token_limit=32000)
        self._provider_routes[openai.MODEL]['config'] = deepcopy(config)
        self._breakout_research_sources = Mock(return_value={'synthetic-nested.py': 'a'*64})

    def job(self, kind='formalization/v1'):
        value = super().job(kind)
        value['spec']['research_inputs']['idea_id'] = budget.IDEA
        if kind == 'formalization/v1':
            profile = value['spec']['research_call_profile']
            profile.update(prompt=PROMPT,max_output_tokens=32000)
            profile['generation_parameters']['openai_responses'].update(input_token_limit=48000,output_token_limit=32000)
        return value

    def claim(self):
        dispatch.validate(self, self.context, self.profile, budget.POLICY)
        dispatch.claim(self, self.epoch)

    def reserve(self, kind='formalization/v1', identity='first-call', input_bound=None, **changes):
        job = self.job(kind)
        inputs, outputs = (48000,32000) if kind == 'formalization/v1' else (76000,4000)
        inputs = inputs if input_bound is None else input_bound
        args = {'input_bound': inputs, 'output_bound': outputs, 'cost': openai.cost_bound(inputs, outputs),
            'request': request_for(job['spec'], self._auxiliary_packet_for_spec(job['spec']))}
        return dispatch.reserve(self, self.epoch, job, identity, **{**args, **changes})


class BreakoutBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.number = 0
        self.host = self.new_host()
        selected = patch.object(budget, 'BASE_PROMPT_SHA256', hashlib.sha256(BASE_PROMPT.encode()).hexdigest())
        selected.start()
        self.addCleanup(selected.stop)

    def new_host(self):
        root = Path(self.temp.name)/str(self.number)
        self.number += 1
        root.mkdir()
        host = BudgetHost(root)
        self.addCleanup(host._db.close)
        return host

    def test_all_three_prior_grants_must_exist_be_consumed_and_revoked(self):
        for approval in budget.PRIOR_APPROVALS:
            for field in ('omit', 'open_grant', 'empty'):
                host = self.new_host()
                seed_priors(host, **{field: approval})
                with self.subTest(approval=approval, field=field), self.assertRaises(REJECTIONS): host.claim()
                with host.ledger._connect() as db:
                    self.assertIsNone(db.execute('SELECT 1 FROM research_epoch_budget_grants WHERE approval=?',
                        (budget.APPROVAL,)).fetchone())
        seed_priors(self.host)
        self.host.claim()
        self.assertEqual(dispatch.inspect(self.host, self.host.epoch)['calls'], [])

    def test_two_exact_sequential_slots_never_refund_and_old_grants_stay_unchanged(self):
        seed_priors(self.host)
        with self.host.ledger._connect() as db:
            before = db.execute('SELECT * FROM research_epoch_budget_grants ORDER BY approval').fetchall()
        self.host.claim()
        with self.assertRaises(REJECTIONS): self.host.reserve('semantic-review/v1', identity='too-early')
        self.host.reserve(input_bound=1)
        self.host.committed('first-call')
        with self.assertRaises(REJECTIONS): self.host.reserve(identity='retry')
        self.host.reserve('semantic-review/v1', identity='second-call', input_bound=1)
        self.host.committed('second-call')
        calls = dispatch.inspect(self.host, self.host.epoch)['calls']
        self.assertEqual([item['stage'] for item in calls], ['formalization/v1','semantic-review/v1'])
        self.assertEqual([item['allocated_tokens'] for item in calls], [80000,80000])
        self.assertEqual([item['allocated_cost'] for item in calls], [440000000,230000000])
        with self.assertRaises(REJECTIONS): self.host.reserve('semantic-review/v1', identity='third-call')
        with self.host.ledger._connect() as db:
            self.assertEqual(db.execute('SELECT * FROM research_epoch_budget_grants WHERE approval<>? ORDER BY approval',
                (budget.APPROVAL,)).fetchall(), before)

    def test_concurrent_claim_has_one_winner_and_survives_reopened_ledger(self):
        seed_priors(self.host)
        def claim_once(_):
            try:
                budget.claim(self.host, self.host.epoch)
                return 'claimed'
            except REJECTIONS:
                return 'denied'
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(claim_once, range(2))), ['claimed','denied'])
        self.host.ledger = openai.SpendLedger(self.host.ledger.path, 5000000000)
        with self.assertRaises(REJECTIONS): self.host.claim()
        self.assertEqual(dispatch.inspect(self.host, self.host.epoch)['calls'], [])

    def test_registry_rollback_cross_registry_and_old_snapshot_cannot_reset_external_fence(self):
        seed_priors(self.host)
        self.host.claim()
        previous_directory = self.host.directory
        self.host.directory = Path(self.temp.name)/'other-registry'
        with self.assertRaises(REJECTIONS): dispatch.inspect(self.host, self.host.epoch)
        with self.assertRaises(REJECTIONS): budget.claim(self.host, self.host.epoch)
        self.host.directory = previous_directory
        self.host.reserve()
        with self.assertRaises(REJECTIONS): self.host.reserve('semantic-review/v1', identity='after-rollback')
        self.host.committed('first-call')
        self.assertEqual(len(dispatch.inspect(self.host,self.host.epoch)['calls']),1)
        self.host._db.execute('DELETE FROM research_calls')  # Only the explicit test inventory, not a Broker registry.
        with self.assertRaises(REJECTIONS): self.host.reserve('semantic-review/v1', identity='after-old-restore')
        self.host.committed('first-call')
        state = dispatch.revoke(self.host,self.host.epoch)
        self.assertTrue(state['pending_calls_still_require_settlement'])
        with self.assertRaises(REJECTIONS): self.host.reserve('semantic-review/v1', identity='after-revoke')
        self.assertEqual(len(dispatch.inspect(self.host,self.host.epoch)['calls']),1)

    def test_unknown_pending_and_insufficient_shared_money_deny_without_replenishment(self):
        for spent, settled in ((1,False),(None,True),(4300000001,True),(4300000000,True)):
            host = self.new_host()
            seed_priors(host)
            identity = host.ledger.reserve('f'*64, 1 if spent is None else spent, key='prior-cost')
            if settled: host.ledger.settle(identity,spent)
            if spent == 4300000000 and settled:
                host.claim()
            else:
                with self.subTest(spent=spent,settled=settled), self.assertRaises(REJECTIONS): host.claim()
        seed_priors(self.host)
        self.host.claim()
        self.host.ledger.reserve('e'*64,1,key='new-pending')
        with self.assertRaises(REJECTIONS): self.host.reserve()
        self.assertEqual(dispatch.inspect(self.host,self.host.epoch)['calls'],[])

    def test_exact_full_prompt_roles_packet_slots_and_epoch_limits_are_required(self):
        for change in ({'max_tokens':160001},{'max_cost_units':700000001},{'max_calls':3},
                       {'max_seconds':1801},{'max_retries':1},{'mode':'fixture'},{'tools':[{}]}):
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                dispatch.validate(self.host,self.host.context,{**self.host.profile,**change},budget.POLICY)
        seed_priors(self.host)
        self.host.claim()
        for change in ({'input_bound':48001},{'output_bound':31999},{'cost':0},{'request':{}}):
            with self.subTest(change=change), self.assertRaises(REJECTIONS): self.host.reserve(**change)
        for kind in ('research-record/v1','discovery/v1'):
            with self.subTest(kind=kind), self.assertRaises(REJECTIONS): self.host.reserve(kind)
        for kind in ('formalization/v1','semantic-review/v1'):
            profile = self.host._effective_research_profile(self.host.job(kind))
            for field,value in (('model','cheap-model'),('max_retries',1),('call_timeout_seconds',359)):
                with self.subTest(kind=kind,field=field), self.assertRaises(REJECTIONS):
                    budget._call_settings({**profile,field:value},kind)
            changed = deepcopy(profile)
            changed['generation_parameters']['openai_responses']['reasoning_effort']='medium'
            with self.assertRaises(REJECTIONS): budget._call_settings(changed,kind)
        formal = self.host._effective_research_profile(self.host.job())
        for value in (BASE_PROMPT,PROMPT+'changed',budget.FORMAT_CLARIFICATION+BASE_PROMPT,
                      PROMPT.replace('complete','shortened'),PROMPT.replace(budget.FORMAT_CLARIFICATION,budget.FORMAT_CLARIFICATION*2)):
            with self.subTest(prompt=value[:40]), self.assertRaises(REJECTIONS):
                budget._call_settings({**formal,'prompts':{'formalizer':value}},'formalization/v1')
        self.assertEqual(dispatch.inspect(self.host,self.host.epoch)['calls'],[])

    def test_wrong_idea_protected_context_and_changed_sources_stop_before_dispatch(self):
        with self.assertRaises(REJECTIONS):
            dispatch.validate(self.host,{'artifact_ids':['different-idea']},self.host.profile,budget.POLICY)
        self.host._deny_final_calibration_ancestry.side_effect = support.Denied('Synthetic protected ancestry')
        with self.assertRaises(REJECTIONS): self.host.claim()
        self.host._paired_require_qualification.assert_not_called()
        self.host._deny_final_calibration_ancestry.side_effect = None
        seed_priors(self.host)
        self.host.claim()
        self.host._breakout_research_sources.return_value={'synthetic-nested.py':'b'*64}
        with self.assertRaises(REJECTIONS): self.host.reserve()
        self.host._breakout_research_sources.return_value={'synthetic-nested.py':'a'*64}
        self.host.now += 1441
        with self.assertRaises(REJECTIONS): self.host.reserve()
        self.assertEqual(dispatch.inspect(self.host,self.host.epoch)['calls'],[])

    def test_review_is_same_epoch_exact_completed_candidate_and_stage_cannot_reopen(self):
        seed_priors(self.host)
        self.host.claim()
        formal = self.host.job()['spec']
        budget.validate_job(self.host,self.host.epoch,formal)
        wrong = deepcopy(formal)
        wrong['research_inputs']['idea_id']='another-idea'
        with self.assertRaises(REJECTIONS): budget.validate_job(self.host,self.host.epoch,wrong)
        self.host._db.execute('INSERT INTO job_specs VALUES(?,?)',('formal',canonical(formal)))
        self.host._db.execute('INSERT INTO jobs VALUES(?,?,?)',('formal','completed','target'))
        review = self.host.job('semantic-review/v1')['spec']
        review['research_inputs']['formalization_id']='target'
        for candidate,status in ((None,'STRUCTURE_CHECKED'),({},'RETAINED_GAP'),({},'STRUCTURE_CHECKED')):
            self.host._artifact.return_value={'body':{'candidate':candidate,'assessment':{'status':status}}}
            if candidate is not None and status=='STRUCTURE_CHECKED': budget.validate_job(self.host,self.host.epoch,review)
            else:
                with self.assertRaises(REJECTIONS): budget.validate_job(self.host,self.host.epoch,review)
        review['research_inputs']['formalization_id']='other-target'
        with self.assertRaises(REJECTIONS): budget.validate_job(self.host,self.host.epoch,review)
        with self.assertRaises(REJECTIONS): budget.validate_job(self.host,self.host.epoch,formal)


class BreakoutRoutingAndProviderTests(unittest.TestCase):
    def test_exact_production_identity_source_pins_and_legacy_router_delegation(self):
        root=Path(__file__).resolve().parents[1]
        self.assertEqual(budget.IDEA,'4abce1d5187d7fd229b52dd9a00e0beca8ee3947e9a1470dbc5351ff78c8872a')
        self.assertEqual(budget.PRIOR_APPROVALS,(complete.APPROVAL,previous.APPROVAL,correction.APPROVAL))
        self.assertNotIn(budget.APPROVAL,budget.PRIOR_APPROVALS)
        self.assertEqual((budget.TOKEN_CAP,budget.COST_CAP,budget.AGGREGATE_CAP),(160000,700000000,5000000000))
        self.assertEqual(budget.BASE_PROMPT_SHA256,correction.BASE_PROMPT_SHA256)
        self.assertEqual(budget.FORMAT_CLARIFICATION,correction.FORMAT_CLARIFICATION)
        self.assertEqual(hashlib.sha256((root/budget.SPEC).read_bytes()).hexdigest(),budget.SPEC_SHA256)
        for module in (ordinary,complete,previous,correction):
            epoch={'request':{'budget_overlay':module.POLICY}}
            self.assertIs(dispatch._module(epoch),legacy_dispatch)
            with patch.object(legacy_dispatch,'inspect',return_value='unchanged') as old:
                self.assertEqual(dispatch.inspect('host',epoch),'unchanged')
                old.assert_called_once_with('host',epoch)

    def test_copied_methods_preserve_all_controls_except_declared_import_and_source_changes(self):
        def parse(method): return ast.parse(textwrap.dedent(inspect.getsource(method))).body[0]
        class Imports(ast.NodeTransformer):
            def visit_ImportFrom(self,node):
                if node.module=='dispatch' and node.level==1:
                    node.module='epoch_budget_dispatch'
                else: node.level-=1
                return node
        for name in ('_create_research_epoch','_reserve_research_call','_inspect_research_epoch','_revoke_research_epoch_budget'):
            before=parse(getattr(FeedbackBudgetBroker,name))
            after=Imports().visit(parse(getattr(BreakoutResearchBroker,name)))
            self.assertEqual(ast.dump(before),ast.dump(after),name)
        before=parse(ControllerProviders._invoke_auxiliary_provider_external)
        after=Imports().visit(parse(providers.BreakoutProviders._invoke_auxiliary_provider_external))
        class SourceDelta(ast.NodeTransformer):
            source_count=0
            catch_count=0
            def visit_Dict(self,node):
                if len(node.keys)==2 and node.keys==[None,None] and isinstance(node.values[1],ast.Call) \
                        and isinstance(node.values[1].func,ast.Attribute) and node.values[1].func.attr=='_breakout_research_sources':
                    self.source_count+=1
                    return node.values[0]
                return self.generic_visit(node)
            def visit_ExceptHandler(self,node):
                if isinstance(node.type,ast.Tuple):
                    self.assert_names=[value.id for value in node.type.elts]
                    if self.assert_names==['OSError','Denied','Invalid']:
                        self.catch_count+=1
                        node.type=ast.Name(id='OSError',ctx=ast.Load())
                return self.generic_visit(node)
        delta=SourceDelta()
        after=delta.visit(after)
        self.assertEqual((delta.source_count,delta.catch_count),(2,1))
        self.assertEqual(ast.dump(before),ast.dump(after))

    def test_real_broker_operator_and_new_policy_job_routing(self):
        with tempfile.TemporaryDirectory() as root, closing(BreakoutResearchBroker(Path(root)/'registry')) as broker:
            token=broker.call(broker.admin_token,'register_worker',name='ordinary',role='discovery',capabilities=['research-record/v1'])['token']
            with self.assertRaises(REJECTIONS):
                broker.call(token,'create_research_epoch',key='forged',context_id='absent',workers=[],profile={},budget_overlay=budget.POLICY)
            with self.assertRaises(REJECTIONS): broker.call(token,'revoke_research_epoch_budget',epoch_id='absent')
            epoch={'request':{'budget_overlay':budget.POLICY}}
            spec={'research_epoch_id':'synthetic-epoch'}
            with patch.object(FeedbackBudgetBroker,'_research_spec_check') as generic, \
                    patch.object(broker,'_epoch',return_value=epoch),patch.object(budget,'validate_job') as current:
                broker._research_spec_check(spec)
                generic.assert_called_once_with(broker,spec)
                current.assert_called_once_with(broker,epoch,spec)
            old_epoch={'request':{'budget_overlay':previous.POLICY}}
            with patch.object(PairedBroker,'_research_spec_check') as old, patch.object(broker,'_epoch',return_value=old_epoch):
                broker._research_spec_check(spec)
                old.assert_called_once_with(spec)
            sources=broker._breakout_research_sources()
            for name in research.FILES:
                self.assertEqual(sources[name],hashlib.sha256((research.ROOT/name).read_bytes()).hexdigest())
            self.assertIn('tests/paired_breakout_oracle.py',sources)
            with patch.dict(research.LOADED,{research.FILES[0]:'0'*64}),self.assertRaises(REJECTIONS): broker._breakout_research_sources()

    def test_real_registry_transaction_rollback_does_not_restore_external_grant(self):
        # Real epoch RPC/transaction/ledger; only raw qualification and the
        # selected synthetic idea ID are substituted. No job or call is made.
        with tempfile.TemporaryDirectory() as root:
            template=BudgetHost(root)
            self.addCleanup(template._db.close)
            seed_priors(template)
            with closing(BreakoutResearchBroker(Path(root)/'actual-registry',
                    provider_routes=template._provider_routes)) as broker:
                op=lambda method,**args:broker.call(broker.admin_token,method,**args)
                for name in ('first','second'):
                    op('register_worker',name=name,role='discovery',capabilities=['research-record/v1'])
                idea=op('add_research',kind='idea',content={'text':'Synthetic resource fixture only'},scope={},source_refs=[])['id']
                context=op('create_context',role='discovery',epoch=1,artifact_ids=[idea])['id']
                args={'key':'rollback-once','context_id':context,'workers':['first','second'],
                      'profile':template.profile,'budget_overlay':budget.POLICY}
                with patch.object(budget,'IDEA',idea), patch.object(broker,'_paired_require_qualification'), \
                        patch.object(broker,'_event',side_effect=support.Invalid('Injected registry commit failure')):
                    with self.assertRaises(REJECTIONS):op('create_research_epoch',**args)
                self.assertEqual(broker._db.execute('SELECT count(*) FROM research_epochs').fetchone()[0],0)
                with template.ledger._connect() as db:
                    self.assertIsNotNone(db.execute('SELECT binding FROM research_epoch_budget_grants WHERE approval=?',
                        (budget.APPROVAL,)).fetchone())
                with patch.object(budget,'IDEA',idea),patch.object(broker,'_paired_require_qualification'),self.assertRaises(REJECTIONS):
                    op('create_research_epoch',**args)
                self.assertEqual(broker._db.execute('SELECT count(*) FROM research_epochs').fetchone()[0],0)

    def test_actual_owned_dispatch_captures_nested_sources_and_keeps_duplicate_acknowledgement(self):
        with patch.object(controller_support,'Broker',BreakoutResearchBroker): fixture=controller_support.Fixture()
        self.addCleanup(fixture.close)
        case=fixture.case()
        lease=case['client'].call('claim')['lease']
        with patch.object(providers,'_invoke',return_value=fixture.result(case)) as invoke:
            result=case['client'].call('invoke_auxiliary_provider',lease=lease,key='synthetic-owned')
            again=case['client'].call('invoke_auxiliary_provider',lease=lease,key='synthetic-owned')
        self.assertEqual(result,again)
        invoke.assert_called_once()
        record=fixture.op('get_artifact',artifact_id=result['invocation_id'])
        incoming=fixture.op('get_artifact',artifact_id=record['body']['input_id'])
        self.assertTrue(record['body']['response_usable'])
        for name in research.FILES:
            self.assertEqual(incoming['body']['installed_sources'][name],research.LOADED[name])
        self.assertFalse(record['body']['scientific_readiness'])
        self.assertNotIn('key_file',canonical(incoming))

    def test_post_response_source_failure_settles_accounting_but_response_is_unusable(self):
        for failure in (support.Denied('source drift'),support.Invalid('source mismatch'),OSError('missing source')):
            with self.subTest(failure=type(failure).__name__):
                with patch.object(controller_support,'Broker',BreakoutResearchBroker): fixture=controller_support.Fixture()
                try:
                    case=fixture.case()
                    lease=case['client'].call('claim')['lease']
                    before=fixture.broker._breakout_research_sources()
                    with patch.object(fixture.broker,'_breakout_research_sources',side_effect=[before,failure]), \
                            patch.object(providers,'_invoke',return_value=fixture.result(case)) as invoke:
                        result=case['client'].call('invoke_auxiliary_provider',lease=lease,key='drift')
                    invoke.assert_called_once()
                    self.assertEqual(result['state'],'unusable')
                    record=fixture.op('get_artifact',artifact_id=result['invocation_id'])
                    self.assertFalse(record['body']['installed_sources_unchanged'])
                    self.assertFalse(record['body']['response_usable'])
                    self.assertTrue(record['body']['receipt']['accounting_valid'])
                    call=fixture.broker._db.execute('SELECT state,response_id FROM research_calls WHERE id=?',
                        (result['call_id'],)).fetchone()
                    self.assertEqual(call['state'],'recorded')
                    self.assertIsNotNone(call['response_id'])
                finally: fixture.close()


if __name__ == '__main__': unittest.main()
