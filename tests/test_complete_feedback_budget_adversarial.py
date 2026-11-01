"""Independent one-use complete-feedback budget boundaries; no network calls.

The genuine publication fixture mocks only its expensive existing assessment
inspectors. This suite substitutes one complete synthetic cohort for the two
production cohorts, and pins its complete initial requests. It does not replace
grant, context, accounting, ledger, transaction, or release checks.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from copy import deepcopy
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from trading_researcher import complete_feedback_budget as budget
from trading_researcher import openai_provider as openai
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.auxiliary import request_for
from trading_researcher.auxiliary_views import PROFILE as AUXILIARY_VIEW, REUSE_SCOPE
from trading_researcher.context_views import source_view, FEEDBACK_VIEW_PROFILE
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.feedback_budget_broker import FeedbackBudgetBroker
from trading_researcher.researcher import FEEDBACK_CONTEXT_TOOL_DEFINITIONS
from trading_researcher.storage import restore_bundle
import test_development_feedback_release as feedback_tests


POLICY = 'research-epoch-feedback-budget/2.0'
REJECTIONS = (Invalid, Conflict, Denied)
INITIAL = {'first': 43358, 'second': 43368}
PURPOSE = 'Independent complete-feedback resource boundary; synthetic inputs only.'
ZERO_USAGE = {'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0}
PRODUCTION_SOURCES = frozenset((
    '12b6d0242e48f935559ece31eff19ab35a69e48bb976828bd4f05925185d521d',
    '2b8617908630ef3a8f108407f90fc6262a49ab1cd81495a449c86c0c9e9e328b',
    '2f177872e1fedc0e9205d4b4ad79cd946066109aa2955c2e5bde77e6127d2428',
    '3c199714862409d80df3850a352d439c0ef397767596355cccebff78a8c75938',
    '5d402dfe2f113c2734c6567539e48abe4cb228ce08e252df753f3cb47f055e2d',
    '6b36faab76fb227c0b501661f18d7c0b3b35ef927721421dd6240e460e7ba35e',
    'bc465d2aeefcf5954b3ff155c059bebab6edc34c2644f00cbe028831179f3626',
    'd97d080ba0657d7fb2be67629829ea85ea3346e67a41a0b55c4ccc772d2fb035'))
PRODUCTION_WIRES = (
    '2f40170cb28903af120fe5a6479295a635575898da89d8cdbd571fe2fc2a3103',
    'ff8b731e220845344f12d1f8b41d862e76c321d876055f53f36552b28cc4d355')


class CompleteFeedbackProductionConstantsTests(unittest.TestCase):
    def test_production_authority_and_source_pins_are_not_fixture_defaults(self):
        self.assertEqual(budget.POLICY, POLICY)
        self.assertEqual(budget.APPROVAL, 'SESSION-2026-10-30-COMPLETE-FEEDBACK-BUDGET')
        self.assertEqual(budget.TOKEN_CAP, 420000)
        self.assertEqual(budget.COST_CAP, 1400000000)
        self.assertEqual(budget.FEEDBACK_COHORTS, 2)
        self.assertEqual(frozenset(budget.SOURCE_IDS), PRODUCTION_SOURCES)
        self.assertEqual(tuple(budget.INITIAL_WIRE_HASHES), PRODUCTION_WIRES)


class CompleteFeedbackBudgetAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.feedback = feedback_tests.DevelopmentFeedbackReleaseTests()
        self.feedback.setUp()
        self.addCleanup(self.feedback.doCleanups)
        self.fixture = self.feedback.fixture
        self.published = self.feedback.publish()
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.ledger_path = Path(self.scratch.name) / 'shared-spending.sqlite3'
        openai.SpendLedger(self.ledger_path, 5000000000)
        self.config = openai.configuration(input_token_limit=74000, output_token_limit=6000)
        self.routes = {openai.MODEL: {'provider': 'openai',
            'key_file': str(Path(self.scratch.name) / 'deliberately-absent-key'),
            'budget_file': str(self.ledger_path), 'config': deepcopy(self.config)}}
        self.broker = self.feedback.broker
        self.restart()
        self.sources = sorted([self.feedback.catalog['id'], self.feedback.snapshot['id']] +
            [self.published[key] for key in ('manifest_id', 'observation_id', 'experience_id')])
        self.context = self.op('create_context', role='discovery', epoch=7, artifact_ids=self.sources)['id']
        self.profile = {'model': openai.MODEL, 'prompt_version': 'complete-feedback-boundary-fixture/1',
            'max_calls': 6, 'max_tokens': 420000, 'max_seconds': 1800,
            'max_cost_units': 1400000000, 'currency': 'USD', 'mode': 'live',
            'prompts': {'first': 'First independent perspective.', 'second': 'Second independent perspective.'},
            'tools': deepcopy(FEEDBACK_CONTEXT_TOOL_DEFINITIONS),
            'source_presentation': FEEDBACK_VIEW_PROFILE,
            'generation_parameters': {'openai_responses': deepcopy(self.config)},
            'max_output_tokens': 6000, 'call_timeout_seconds': 240, 'max_retries': 0}
        self.followups = {}
        for name, value in (('SOURCE_IDS', frozenset(self.sources)), ('FEEDBACK_COHORTS', 1),
                ('INITIAL_WIRE_HASHES', tuple(digest(openai.wire_request(self.request(worker), self.config))
                    for worker in ('first', 'second')))):
            p = patch.object(budget, name, value)
            p.start()
            self.addCleanup(p.stop)

    def inspectors(self, host):
        for name, result in (('_inspect_data_use', self.feedback.data_inspector.return_value),
                             ('_inspect_meaning_review', self.feedback.meaning_inspector.return_value)):
            p = patch.object(host, name, return_value=deepcopy(result))
            p.start()
            self.addCleanup(p.stop)

    def restart(self):
        directory = self.broker.directory
        self.broker.close()
        self.broker = FeedbackBudgetBroker(directory, clock=lambda: self.fixture.now, provider_routes=self.routes)
        self.addCleanup(self.broker.close)
        self.inspectors(self.broker)

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def create(self, key='complete-feedback-once', **changes):
        args = {'key': key, 'context_id': self.context, 'workers': ['first', 'second'],
            'profile': deepcopy(self.profile), 'budget_overlay': POLICY}
        return self.op('create_research_epoch', **{**args, **changes})['id']

    def jobs(self, epoch, order=('first', 'second')):
        batch = self.op('create_batch', key='complete-feedback-' + epoch, epoch=7)['id']
        self.discovery_batch = batch
        for worker in order:
            self.op('enqueue', key=worker + '-' + epoch, spec={
                'kind': 'research-record/v1', 'context_id': self.context, 'purpose': PURPOSE,
                'allowed_workers': [worker], 'max_attempts': 1, 'lease_seconds': 1800,
                'deadline': self.fixture.now + 1800, 'dependencies': [],
                'batch_id': batch, 'research_epoch_id': epoch})
        self.op('seal_batch', batch_id=batch)
        return self.broker.call(self.fixture.tokens[order[0]], 'claim')['lease']

    def request(self, worker='first', followup=False):
        sources = [source_view(self.broker._artifact(identity), profile=FEEDBACK_VIEW_PROFILE)
                   for identity in self.broker._context(self.context)['artifact_ids']]
        messages = [{'role': 'system', 'content': self.profile['prompts'][worker]},
                    {'role': 'user', 'content': canonical({'purpose': PURPOSE, 'sources': sources})}]
        if followup:
            messages.extend(deepcopy(self.followups[worker]))
        return {'model': openai.MODEL, 'prompt_version': self.profile['prompt_version'],
            'messages': messages, 'tools': deepcopy(self.profile['tools']),
            'generation_parameters': deepcopy(self.profile['generation_parameters'])}

    def reserve(self, lease, worker='first', key='initial', input_tokens=None, request=None, **changes):
        count = INITIAL[worker] if input_tokens is None else input_tokens
        args = {'lease': lease, 'key': key, 'request': request or self.request(worker, key != 'initial'),
            'input_token_bound': count, 'output_token_limit': 6000,
            'cost_bound_units': openai.cost_bound(count, 6000)}
        return self.broker.call(self.fixture.tokens[worker], 'reserve_research_call', **{**args, **changes})

    def finish(self, lease, call, worker='first', usage=None):
        # A completed tools response with a retained denied tool result gives the
        # second call a genuine, exactly reconstructible transcript.
        request = {'id': 'source-check', 'name': 'read_artifact', 'arguments': {'id': '0' * 64}}
        response = {'status': 'completed', 'output': {'status': 'tools', 'calls': [request]}}
        receipt = self.broker.call(self.fixture.tokens[worker], 'finish_research_call', lease=lease,
            call_id=call['call_id'], response=response, usage=deepcopy(ZERO_USAGE if usage is None else usage))
        body = {'schema': 'provider-tool-result/1', 'call_id': call['call_id'], 'tool_request': request,
            'result': {'status': 'tool_denied', 'reason': 'Unavailable or invalid request'}}
        self.broker.call(self.fixture.tokens[worker], 'put_artifact', lease=lease, body=body, source_refs=[])
        self.followups[worker] = [{'role': 'assistant', 'content': canonical(response)},
                                  {'role': 'tool', 'content': canonical(body)}]
        return receipt

    def inventory(self, epoch):
        return self.op('inspect_research_epoch', epoch_id=epoch)['budget_overlay']['calls']

    def test_explicit_one_use_does_not_expand_ordinary_or_default_broker(self):
        with self.assertRaises(REJECTIONS):
            self.create(key='ordinary-overflow', budget_overlay=None, profile={**self.profile, 'max_tokens': 80001})
        ordinary = self.op('create_research_epoch', key='ordinary', context_id=self.context,
            workers=['first', 'second'], profile={**self.profile, 'max_tokens': 80000})['id']
        self.assertNotIn('budget_overlay', self.op('inspect_research_epoch', epoch_id=ordinary)['request'])
        directory = self.broker.directory
        self.broker.close()
        old = Broker(directory, clock=lambda: self.fixture.now, provider_routes=self.routes)
        self.addCleanup(old.close)
        self.inspectors(old)
        with self.assertRaises(REJECTIONS):
            old.call(old.admin_token, 'create_research_epoch', key='default-cannot-activate-v2',
                context_id=self.context, workers=['first', 'second'], profile=self.profile, budget_overlay=POLICY)
        old.close()
        self.restart()
        epoch = self.create()
        self.assertEqual(self.create(), epoch)
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['request']['budget_overlay'], POLICY)
        with self.assertRaises(REJECTIONS):
            self.create(key='duplicate-grant')

    def test_operator_profile_shape_model_reasoning_and_route_are_bound_before_claim(self):
        with self.assertRaises(Denied):
            self.broker.call(self.fixture.tokens['first'], 'create_research_epoch', key='worker',
                context_id=self.context, workers=['first', 'second'], profile=self.profile, budget_overlay=POLICY)
        for changes in ({'max_tokens': 420001}, {'max_cost_units': 1400000001}, {'max_calls': 7},
                {'max_seconds': 1801}, {'max_output_tokens': 5999}, {'max_retries': 1},
                {'call_timeout_seconds': 241}, {'mode': 'fixture'}, {'currency': 'NONE'},
                {'model': 'cheaper-model'}, {'source_presentation': 'discovery-source-view/2'},
                {'generation_parameters': None}, {'perspective_profiles': []}):
            with self.subTest(change=changes), self.assertRaises(REJECTIONS):
                self.create(key='invalid', profile={**self.profile, **changes})
        for changed in ({**self.config, 'reasoning_effort': 'high'}, {**self.config, 'input_token_limit': 73999}):
            with self.subTest(config=changed), self.assertRaises(REJECTIONS):
                self.create(key='config-drift', profile={**self.profile,
                    'generation_parameters': {'openai_responses': changed}})
        self.assertIsInstance(self.create(), str)

    def test_exact_source_set_complete_trio_and_current_feedback_required_before_claim(self):
        for omitted in self.sources:
            context = self.op('create_context', role='discovery', epoch=7,
                artifact_ids=[identity for identity in self.sources if identity != omitted])['id']
            with self.subTest(omitted=omitted), self.assertRaises(REJECTIONS):
                self.create(key='missing-source', context_id=context)
        for field in ('observation_id', 'experience_id'):
            subset = frozenset(set(self.sources) - {self.published[field]})
            context = self.op('create_context', role='discovery', epoch=7, artifact_ids=sorted(subset))['id']
            with patch.object(budget, 'SOURCE_IDS', subset), self.subTest(field=field), self.assertRaises(REJECTIONS):
                self.create(key='incomplete-trio', context_id=context)
        with patch.object(budget, 'FEEDBACK_COHORTS', 2), self.assertRaises(REJECTIONS):
            self.create(key='missing-second-cohort')
        with patch.object(self.broker, '_inspect_meaning_review', return_value={
                **self.feedback.meaning_inspector.return_value, 'status': 'STALE', 'current': False}), \
                self.assertRaises(REJECTIONS):
            self.create(key='stale-feedback')
        self.assertIsInstance(self.create(), str)

    def test_protected_or_unapproved_additional_sources_never_enter_the_authorized_context(self):
        for data_class in ('assessment', 'operations'):
            artifact = self.op('add_source', body={'text': 'Synthetic excluded source'}, data_class=data_class)
            if data_class == 'assessment':
                with self.assertRaises(REJECTIONS):
                    self.op('create_context', role='discovery', epoch=7, artifact_ids=[*self.sources, artifact['id']])
            else:
                with self.assertRaises(REJECTIONS):
                    context = self.op('create_context', role='discovery', epoch=7,
                        artifact_ids=[*self.sources, artifact['id']])['id']
                    self.create(key='extra-operations', context_id=context)
        extra = self.op('add_source', body={'text': 'Unapproved extra development input'}, data_class='development')
        context = self.op('create_context', role='discovery', epoch=7, artifact_ids=[*self.sources, extra['id']])['id']
        with self.assertRaises(REJECTIONS):
            self.create(key='extra-development', context_id=context)
        self.assertIsInstance(self.create(), str)

    def test_complete_initial_wire_cannot_drop_alter_add_or_reorder_sources(self):
        epoch = self.create()
        lease = self.jobs(epoch)
        original = self.request()
        import json
        payload = json.loads(original['messages'][1]['content'])
        altered = []
        for sources in (payload['sources'][:-1], list(reversed(payload['sources'])), payload['sources'] * 2):
            item = deepcopy(original)
            item['messages'][1]['content'] = canonical({**payload, 'sources': sources})
            altered.append(item)
        item = deepcopy(original)
        item['messages'][1]['content'] = canonical({**payload, 'purpose': 'A different research purpose.'})
        altered.append(item)
        item = deepcopy(original)
        item['messages'].append({'role': 'assistant', 'content': 'Caller-selected hidden history.'})
        altered.append(item)
        altered.append({**original, 'messages': original['messages'][:1]})
        for index, request in enumerate(altered):
            with self.subTest(index=index), self.assertRaises(REJECTIONS):
                self.reserve(lease, request=request)
        with patch.object(budget, 'INITIAL_WIRE_HASHES', ('0' * 64, '1' * 64)), self.assertRaises(REJECTIONS):
            self.reserve(lease)
        self.assertEqual(self.inventory(epoch), [])
        self.assertTrue(self.reserve(lease)['dispatch'])

    def test_followup_requires_exact_retained_transcript_and_cannot_recycle_slot(self):
        epoch = self.create()
        lease = self.jobs(epoch)
        first = self.reserve(lease)
        self.finish(lease, first)
        correct = self.request(followup=True)
        for request in (self.request(), {**correct, 'messages': correct['messages'][:-1]},
                {**correct, 'messages': correct['messages'][:2] + [
                    {'role': 'assistant', 'content': 'Forged response'}, *correct['messages'][3:]]}):
            with self.subTest(request=request['messages'][-1]['role']), self.assertRaises(REJECTIONS):
                self.reserve(lease, key='followup', input_tokens=74000, request=request)
        second = self.reserve(lease, key='followup', input_tokens=74000)
        self.finish(lease, second)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, key='third', input_tokens=1, request=correct)
        calls = self.inventory(epoch)
        self.assertEqual(len(calls), 2)
        self.assertEqual(sum(c['allocated_tokens'] for c in calls), 129358)
        self.assertEqual(sum(c['allocated_cost'] for c in calls), 413395000)

    def test_reverse_dispatch_preserves_worker_specific_initial_slot(self):
        epoch = self.create()
        lease = self.jobs(epoch, order=('second', 'first'))
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, worker='second', input_tokens=43369)
        call = self.reserve(lease, worker='second')
        self.finish(lease, call, worker='second')
        self.assertEqual(self.inventory(epoch)[0]['allocated_tokens'], 49368)

    def test_six_real_slots_preserve_primary_selection_role_settings_and_nonrefundability(self):
        epoch = self.create()
        lease = self.jobs(epoch)
        ideas = {}
        for worker in ('first', 'second'):
            if worker == 'second':
                lease = self.broker.call(self.fixture.tokens[worker], 'claim')['lease']
            first = self.reserve(lease, worker=worker)
            self.finish(lease, first, worker=worker)
            second = self.reserve(lease, worker=worker, key='followup', input_tokens=74000)
            self.finish(lease, second, worker=worker)
            artifact = self.broker.call(self.fixture.tokens[worker], 'record_research', lease=lease,
                kind='idea', content={'text': 'Unrestricted first idea' if worker == 'first' else
                    'Retained alternative perspective, not the selected candidate.'}, scope={}, source_refs=[])
            ideas[worker] = artifact['id']
            self.assertTrue(self.broker.call(self.fixture.tokens[worker], 'submit', lease=lease,
                artifact_id=artifact['id'])['accepted'])
        self.op('release_batch', batch_id=self.discovery_batch, target_epoch=8)
        target = None
        for kind, name, bound, output, reasoning, context_epoch in (
                ('formalization/v1', 'complete-feedback-formalizer', 62000, 18000, 'high', 8),
                ('semantic-review/v1', 'complete-feedback-reviewer', 76000, 4000, 'low', 9)):
            config = openai.configuration(input_token_limit=bound, output_token_limit=output)
            config.update(reasoning_effort=reasoning, source_presentation=AUXILIARY_VIEW,
                bounded_math_scope=REUSE_SCOPE)
            if target is None:
                config['output_formatting'] = 'compact-json/1'
            self.routes[openai.MODEL]['config'] = config
            self.restart()
            token = self.op('register_worker', name=name, role='formalizer', capabilities=[kind])['token']
            refs = [target, ideas['first'], self.feedback.catalog['id']] if target else [*self.sources, *ideas.values()]
            context = self.op('create_context', role='formalizer', epoch=context_epoch, artifact_ids=refs)['id']
            inputs = {'formalization_id': target, 'definition_ids': []} if target else {
                'idea_id': ideas['first'], 'catalog_id': self.feedback.catalog['id'], 'definition_ids': []}
            selected = {'model': openai.MODEL, 'prompt_version': name + '/1',
                'prompt': 'Independent synthetic allocation fixture. No empirical or meaning claim.',
                'generation_parameters': {'openai_responses': config}, 'max_output_tokens': output,
                'call_timeout_seconds': 360, 'max_retries': 0}
            batch = self.op('create_batch', key=name, epoch=context_epoch)['id']
            spec = {'kind': kind, 'context_id': context, 'purpose': PURPOSE,
                'allowed_workers': [name], 'max_attempts': 1, 'lease_seconds': 1800,
                'deadline': self.fixture.now + 1800, 'dependencies': [], 'batch_id': batch,
                'research_epoch_id': epoch, 'research_call_profile': selected, 'research_inputs': inputs}
            if target is None:
                for wrong in (ideas['second'], self.feedback.formalization['body']['idea_id']):
                    with self.subTest(wrong_idea=wrong), self.assertRaises(REJECTIONS):
                        self.op('enqueue', key='wrong-primary', spec={**spec,
                            'research_inputs': {**inputs, 'idea_id': wrong}})
            for changed_config in ({**config, 'reasoning_effort': 'low' if reasoning == 'high' else 'high'},
                                   {**config, 'output_token_limit': output - 1}):
                wrong_profile = {**selected, 'generation_parameters': {'openai_responses': changed_config}}
                with self.subTest(stage=kind, config=changed_config), self.assertRaises(REJECTIONS):
                    self.op('enqueue', key='wrong-role-settings', spec={**spec, 'research_call_profile': wrong_profile})
            self.op('enqueue', key=name, spec=spec)
            with self.assertRaises(REJECTIONS):
                self.op('enqueue', key='duplicate-stage-' + name, spec=spec)
            self.op('seal_batch', batch_id=batch)
            lease = self.broker.call(token, 'claim')['lease']
            packet = self.broker.call(token, 'auxiliary_input', lease=lease)
            request = request_for(spec, packet)
            args = {'lease': lease, 'request': request, 'input_token_bound': bound,
                'output_token_limit': output, 'cost_bound_units': openai.cost_bound(bound, output)}
            with self.assertRaises(REJECTIONS):
                self.broker.call(token, 'reserve_research_call', key='slot-overflow', **{
                    **args, 'input_token_bound': bound + 1, 'cost_bound_units': openai.cost_bound(bound + 1, output)})
            call = self.broker.call(token, 'reserve_research_call', key='single-stage', **args)
            if target is None:
                candidate = deepcopy(self.feedback.formalization['body']['candidate'])
                candidate['idea_ref'] = ideas['first']
                # A literal-only, explicitly synthetic candidate avoids adding
                # feature-definition/certification machinery to a budget test.
                candidate['outcome'] = {'program': deepcopy(candidate['scope_ast']), 'scale': 'binary_probability'}
                candidate['estimand']['unit'] = 'ratio'
                candidate['feature_refs'] = []
                candidate['test_universe']['data_snapshot_ref'] = self.feedback.catalog['id']
                candidate['parameter_origins'].append({'path': '/outcome/program/expression/value',
                    'basis': 'preexisting_specification', 'source_refs': [],
                    'rationale': 'Literal-only allocation fixture, never an empirical research candidate.'})
                semantic = deepcopy(self.feedback.formalization['body']['semantic_report'])
                response = {'status': 'completed', 'output': {'status': 'final',
                    'candidate': candidate, 'semantic_report': semantic}}
            else:
                response = {'status': 'completed', 'output': {'status': 'final', 'review': {
                    'judgment': 'uncertain', 'reason': 'Synthetic budget lifecycle only.',
                    'added_assumptions': [], 'omitted_assumptions': [], 'conflicts': [],
                    'unresolved_meaning': ['No actual model review in this fixture.'], 'mapping_checks': []}}}
            self.broker.call(token, 'finish_research_call', lease=lease, call_id=call['call_id'],
                response=response, usage=ZERO_USAGE)
            with self.assertRaises(REJECTIONS):
                self.broker.call(token, 'reserve_research_call', key='extra-call-after-zero-usage', **args)
            if target is None:
                saved = self.broker.call(token, 'record_formalization', lease=lease, idea_id=ideas['first'],
                    catalog_id=self.feedback.catalog['id'], candidate=candidate, semantic_report=semantic,
                    provider_call_id=call['call_id'])
                self.assertEqual(saved['assessment']['status'], 'STRUCTURE_CHECKED')
                self.assertTrue(self.broker.call(token, 'submit', lease=lease, artifact_id=saved['id'])['accepted'])
                self.op('release_batch', batch_id=batch, target_epoch=9)
                target = saved['id']
        calls = self.inventory(epoch)
        self.assertEqual(len(calls), 6)
        self.assertEqual(sum(c['allocated_tokens'] for c in calls), 418726)
        self.assertEqual(sum(c['allocated_cost'] for c in calls), 1391815000)
        self.assertEqual([c['stage'] for c in calls[-2:]], ['formalization/v1', 'semantic-review/v1'])
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['tokens'], 0)

    def test_cost_per_call_and_unknown_shared_spend_fail_before_consuming_slot(self):
        epoch = self.create()
        lease = self.jobs(epoch)
        for change in ({'cost_bound_units': 0}, {'cost_bound_units': openai.cost_bound(43358, 6000) + 1},
                {'input_token_bound': True}, {'output_token_limit': 6001}, {'input_tokens': 74001}):
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                self.reserve(lease, **change)
        ledger = openai.SpendLedger(self.ledger_path, 5000000000)
        pending = ledger.reserve('a' * 64, 10, key='unsettled-other-call')
        with self.assertRaises(REJECTIONS):
            self.reserve(lease)
        ledger.settle(pending, None)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease)
        self.assertEqual(self.inventory(epoch), [])

    def test_claim_and_reservation_fences_survive_registry_rollback(self):
        original = self.broker._event
        def fail_claim(actor, kind, **fields):
            if kind == 'research_epoch_created':
                raise RuntimeError('Injected registry rollback after durable budget claim')
            return original(actor, kind, **fields)
        with patch.object(self.broker, '_event', side_effect=fail_claim), self.assertRaises(RuntimeError):
            self.create()
        self.restart()
        with self.assertRaises(REJECTIONS):
            self.create()
        with self.assertRaises(REJECTIONS):
            self.create(key='replacement-after-rollback')

    def test_reservation_fence_survives_registry_rollback(self):
        epoch = self.create()
        lease = self.jobs(epoch)
        original = self.broker._event
        def fail_reserve(actor, kind, **fields):
            if kind == 'provider_call_reserved':
                raise RuntimeError('Injected registry rollback after durable reservation')
            return original(actor, kind, **fields)
        with patch.object(self.broker, '_event', side_effect=fail_reserve), self.assertRaises(RuntimeError):
            self.reserve(lease)
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM research_calls WHERE epoch_id=?',
            (epoch,)).fetchone()[0], 0)
        self.restart()
        with self.assertRaises(REJECTIONS):
            self.reserve(lease)

    def test_same_path_stale_restore_cannot_erase_consumed_external_slot(self):
        epoch = self.create()
        lease = self.jobs(epoch)
        stale = Path(self.scratch.name) / 'before-call.sqlite3'
        with closing(sqlite3.connect(stale)) as db:
            self.broker._db.backup(db)
        call = self.reserve(lease)
        self.finish(lease, call)
        registry = self.broker.directory / 'registry.sqlite3'
        self.broker.close()
        with closing(sqlite3.connect(stale)) as source, closing(sqlite3.connect(registry)) as target:
            source.backup(target)
        self.restart()
        with self.assertRaises(REJECTIONS):
            self.reserve(lease)

    def test_restart_and_revocation_preserve_accounting_but_forbid_future_dispatch(self):
        epoch = self.create()
        lease = self.jobs(epoch)
        call = self.reserve(lease)
        with self.assertRaises(Denied):
            self.broker.call(self.fixture.tokens['first'], 'revoke_research_epoch_budget', epoch_id=epoch)
        self.op('revoke_research_epoch_budget', epoch_id=epoch)
        self.restart()
        self.assertTrue(self.op('inspect_research_epoch', epoch_id=epoch)['budget_overlay']['revoked'])
        self.finish(lease, call, usage={'input_tokens': 11, 'output_tokens': 7, 'cost_units': 20000})
        self.assertFalse(self.reserve(lease)['dispatch'])
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['tokens'], 18)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, key='followup', input_tokens=74000)
        with self.assertRaises(REJECTIONS):
            self.create(key='revocation-is-not-reissue')

    def other_registry(self):
        backup, restored = Path(self.scratch.name) / 'backup', Path(self.scratch.name) / 'restored'
        self.op('backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, self.broker.directory / 'operator.key')
        other = FeedbackBudgetBroker(restored, clock=lambda: self.fixture.now, provider_routes=self.routes)
        self.addCleanup(other.close)
        self.inspectors(other)
        return other

    def test_two_registries_compete_for_one_external_claim(self):
        other = self.other_registry()
        barrier = threading.Barrier(2)
        def attempt(host):
            barrier.wait(timeout=10)
            try:
                return host.call(host.admin_token, 'create_research_epoch', key='concurrent',
                    context_id=self.context, workers=['first', 'second'], profile=deepcopy(self.profile),
                    budget_overlay=POLICY)
            except REJECTIONS as exc:
                return exc
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result(timeout=20) for future in
                [pool.submit(attempt, host) for host in (self.broker, other)]]
        self.assertEqual(sum(type(result) is dict and 'id' in result for result in results), 1)
        self.assertEqual(sum(isinstance(result, REJECTIONS) for result in results), 1)

    def test_backup_cannot_move_a_consumed_claim_to_another_registry(self):
        epoch = self.create()
        lease = self.jobs(epoch)
        call = self.reserve(lease)
        self.finish(lease, call)
        other = self.other_registry()
        with self.assertRaises(REJECTIONS):
            other.call(other.admin_token, 'create_research_epoch', key='cross-registry',
                context_id=self.context, workers=['first', 'second'], profile=self.profile, budget_overlay=POLICY)
        with self.assertRaises(REJECTIONS):
            other.call(self.fixture.tokens['first'], 'reserve_research_call', lease=lease, key='followup',
                request=self.request(followup=True), input_token_bound=74000, output_token_limit=6000,
                cost_bound_units=openai.cost_bound(74000, 6000))


if __name__ == '__main__':
    unittest.main()
