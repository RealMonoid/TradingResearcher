"""Mixed-vendor role handoff through real adapters; all HTTPS is synthetic.

These checks exercise transport, isolation and shared limits, never model quality.
"""
from copy import deepcopy
from pathlib import Path
import time
import unittest
from unittest.mock import patch

from binding_support import BindingFixture, resolve
from test_anthropic_provider import raw_response
import test_researcher as support
from trading_researcher import anthropic_provider as claude
from trading_researcher import openai_provider as openai
from trading_researcher.auxiliary import run_auxiliary_once
from trading_researcher.codec import canonical
from trading_researcher.researcher import run_research_once


class FixedOpenAI(openai.OpenAIResponsesProvider):
    """Patch transport inside the spawned child, retaining actual adapter code."""

    def complete(self, request, ordinal, timeout):
        def post(endpoint, payload, secret, deadline):
            if endpoint.endswith('/input_tokens'):
                return {'object': 'response.input_tokens', 'input_tokens': 100}, 'req_count'
            return {'id': 'resp_role_fixture', 'model': openai.MODEL,
                    'status': 'completed', 'service_tier': 'default',
                    'usage': {'input_tokens': 100, 'output_tokens': 20},
                    'output': [{'type': 'message', 'role': 'assistant', 'content': [
                        {'type': 'output_text', 'text': canonical(self.fixed_output)}]}]}, 'req_openai'
        with patch.object(openai, '_key', return_value='synthetic-openai'), \
                patch.object(openai, '_post', side_effect=post):
            return super().complete(request, ordinal, timeout)


class FixedClaude(claude.AnthropicMessagesProvider):
    def complete(self, request, ordinal, timeout):
        def post(endpoint, payload, secret, deadline, workspace_id):
            if endpoint.endswith('/count_tokens'):
                return {'input_tokens': 200}, 'req_count'
            return raw_response([{'type': 'text', 'text': canonical(self.fixed_output)}]), 'req_claude'
        with patch.object(claude, '_key', return_value='synthetic-anthropic'), \
                patch.object(claude, '_post', side_effect=post):
            return super().complete(request, ordinal, timeout)


class MixedRoleHandoffTests(unittest.TestCase):
    setup_epoch = support.ResearcherTests.setup_epoch
    calls = support.ResearcherTests.calls

    def setUp(self):
        self.base = BindingFixture()
        self.admin = support.LocalClient(self.base.broker, self.base.token)
        self.clients = {}
        for name in ('first', 'second'):
            token = self.admin.call('register_worker', name=name, role='discovery',
                                    capabilities=['research-record/v1'])['token']
            self.clients[name] = support.LocalClient(self.base.broker, token)
        self.catalog = self.base.snapshot['body']['catalog_id']
        self.definitions = self.base.feature['body']['definitions_id']
        self.context = self.admin.call('create_context', role='discovery', epoch=1,
            artifact_ids=[self.catalog, self.definitions, self.base.snapshot['id']])['id']
        self.ledger = Path(self.base.root) / 'mixed-role-spend.sqlite3'
        self.settings = {
            'openai': openai.configuration(input_token_limit=5000, output_token_limit=1024),
            'claude': claude.configuration(aggregate_budget_nano=5000000000,
                budget_scope_ref='offline-role-fixture', input_token_limit=5000, output_token_limit=1024),
        }

    def tearDown(self):
        self.base.close()

    def role_profile(self, vendor, role):
        model, key = (openai.MODEL, 'openai_responses') if vendor == 'openai' else (claude.MODEL, 'anthropic_messages')
        return {'model': model, 'prompt_version': 'mixed-role-fixture/' + role,
                'generation_parameters': {key: self.settings[vendor]},
                'max_output_tokens': 1024, 'call_timeout_seconds': 10, 'max_retries': 0}

    def provider(self, vendor, worker, output):
        cls = FixedOpenAI if vendor == 'openai' else FixedClaude
        adapter = cls('unused', self.ledger, self.settings[vendor], epoch_id=self.epoch, worker=worker)
        adapter.fixed_output = deepcopy(output)
        return adapter

    def auxiliary_job(self, kind, worker, vendor, context, inputs, dependencies):
        token = self.admin.call('register_worker', name=worker, role='formalizer', capabilities=[kind])['token']
        profile = {**self.role_profile(vendor, kind), 'prompt':
            'Preserve the supplied meaning and explain uncertainty. Synthetic transport fixture; no empirical verdict.'}
        job = self.admin.call('enqueue', key=worker, spec={
            'kind': kind, 'context_id': context, 'purpose': 'Mixed-vendor handoff fixture',
            'allowed_workers': [worker], 'max_attempts': 1, 'lease_seconds': 30,
            'deadline': int(time.time()) + 120, 'dependencies': dependencies,
            'research_epoch_id': self.epoch, 'research_call_profile': profile,
            'research_inputs': inputs})['id']
        return job, support.LocalClient(self.base.broker, token)

    def run_handoff(self, formalizer_vendor, max_calls=4):
        reviewer_vendor = 'claude' if formalizer_vendor == 'openai' else 'openai'
        batch = self.setup_epoch(mode='live', model=openai.MODEL, currency='USD',
            max_calls=max_calls, max_seconds=120, max_cost_units=5000000000,
            max_output_tokens=1024, perspective_profiles={
                'first': self.role_profile('openai', 'discovery-first'),
                'second': self.role_profile('claude', 'discovery-second')})
        idea_text = self.base.base['original_idea_text']
        first = run_research_once(self.clients['first'], self.provider('openai', 'first', support.final(idea_text)))
        peer_text = 'Private alternative gap from second discovery perspective'
        second = run_research_once(self.clients['second'], self.provider('claude', 'second', support.final(peer_text, 'gap')))
        self.assertTrue(first['accepted'] and second['accepted'], (first, second))
        self.assertNotIn(idea_text, canonical(self.calls()[1]['request']))
        self.admin.call('release_batch', batch_id=batch, target_epoch=2)
        idea_id = first['record_ids'][-1]
        original = self.admin.call('get_artifact', artifact_id=idea_id)
        context = self.admin.call('create_context', role='formalizer', epoch=2,
            artifact_ids=[idea_id, self.catalog, self.definitions, self.base.snapshot['id']])['id']
        job, client = self.auxiliary_job('formalization/v1', 'mixed-formalizer', formalizer_vendor,
            context, {'idea_id': idea_id, 'catalog_id': self.catalog, 'definition_ids': [self.definitions]}, [])
        candidate = resolve(deepcopy(self.base.base['candidate']),
            {'fixture:idea': idea_id, 'fixture:data_snapshot': self.base.snapshot['id']})
        output = {'status': 'final', 'candidate': candidate, 'semantic_report': deepcopy(self.base.base['semantic_report'])}
        result = run_auxiliary_once(client, self.provider(formalizer_vendor, 'mixed-formalizer', output))
        self.assertTrue(result['accepted'], result)
        target = self.admin.call('get_artifact', artifact_id=result['artifact_id'])
        self.assertEqual(target['body']['candidate'], candidate)
        self.assertEqual(self.admin.call('get_artifact', artifact_id=idea_id), original)
        self.admin.call('release_batch', batch_id=self.admin.call('inspect', job_id=job)['batch_id'], target_epoch=3)
        context = self.admin.call('create_context', role='formalizer', epoch=3,
            artifact_ids=[target['id'], idea_id, self.catalog, self.definitions])['id']
        _, client = self.auxiliary_job('semantic-review/v1', 'mixed-reviewer', reviewer_vendor,
            context, {'formalization_id': target['id'], 'definition_ids': [self.definitions]}, [job])
        review = {'judgment': 'uncertain', 'reason': 'This fixture supplies no actual model judgment.',
            'added_assumptions': [], 'omitted_assumptions': [], 'conflicts': [],
            'unresolved_meaning': ['Substantive independent judgment remains unverified.'],
            'mapping_checks': [{'segment': i, 'judgment': 'uncertain', 'reason': 'Synthetic response only.'}
                for i in range(len(target['body']['semantic_report']['segments']))]}
        outcome = run_auxiliary_once(client, self.provider(reviewer_vendor, 'mixed-reviewer',
            {'status': 'final', 'review': review}))
        self.assertFalse(outcome['scientific_authority'])
        calls = self.calls()
        self.assertEqual(len(calls), max_calls)
        for call in calls[2:]:
            self.assertEqual(call['request']['tools'], [])
            self.assertNotIn(peer_text, canonical(call['request']))
        report = openai.SpendLedger(self.ledger, 5000000000).report()
        self.assertEqual(report['provider'], 'mixed')
        self.assertEqual(report['totals']['calls'], max_calls)
        self.assertTrue(all(c['admitted_at_utc'] and c['settled_at_utc'] for c in report['calls']))
        self.assertEqual({m['model_identity']['catalog_version'] for m in report['models']}, {'6.1', '5.5'})
        self.assertEqual(self.admin.call('get_artifact', artifact_id=target['id']), target)
        self.assertEqual(self.admin.call('verify')['status'], 'PASS')
        if max_calls == 3:
            self.assertFalse(outcome['accepted'])
            self.assertEqual(outcome['state'], 'blocked')
            self.assertEqual(report['totals']['exact_total_tokens'], 460)
            self.assertEqual(report['money']['charged_nano'], 1900000)
            return
        self.assertTrue(outcome['accepted'], outcome)
        saved = self.admin.call('get_artifact', artifact_id=outcome['artifact_id'])
        body = saved['body']
        self.assertEqual(body['formalization_id'], target['id'])
        self.assertNotEqual(body['formalizer_id'], body['reviewer_id'])
        self.assertEqual(body['review'], review)
        self.assertEqual(body['actual_independent_model_review'], 'UNVERIFIED')
        self.assertFalse(body['scientific_readiness'])
        self.assertEqual([c['request']['model'] for c in calls],
            [openai.MODEL, claude.MODEL, self.role_profile(formalizer_vendor, 'x')['model'],
             self.role_profile(reviewer_vendor, 'x')['model']])
        self.assertEqual(report['totals']['exact_total_tokens'], 680)
        self.assertEqual(report['money']['charged_nano'], 2900000)
        self.assertEqual(self.admin.call('inspect_research_epoch', epoch_id=self.epoch)['usage'],
            {'calls': 4, 'tokens': 680, 'cost_units': 2900000})

    def test_openai_formalizes_claude_reviews_after_mixed_discovery(self):
        self.run_handoff('openai')

    def test_claude_formalizes_openai_reviews_after_mixed_discovery(self):
        self.run_handoff('claude')

    def test_reviewer_cannot_reset_exhausted_discovery_and_formalization_budget(self):
        self.run_handoff('openai', max_calls=3)


if __name__ == '__main__':
    unittest.main()
