"""Optional native inquiry route; fixture providers prove machinery only."""
from copy import deepcopy
from pathlib import Path
import tempfile
import time
import unittest

from trading_researcher.codec import canonical, decode, Invalid
from trading_researcher.errors import Denied
from trading_researcher.inquiry.host import InquiryBroker
from trading_researcher.inquiry.profiles import build_profile
from trading_researcher.inquiry.presentation import SCHEMA, TOOLS, initial_messages
from trading_researcher.inquiry.worker import run_research_once
from trading_researcher.researcher import ScriptedProvider


class LocalClient:
    timeout = 2

    def __init__(self, broker, token):
        self.broker, self.token = broker, token

    def call(self, operation, **arguments):
        return self.broker.call(self.token, operation, **arguments)


def profile():
    return {'model': 'fixture/1', 'prompt_version': 'prior/1', 'mode': 'fixture',
            'max_calls': 8, 'max_tokens': 80000, 'max_seconds': 120,
            'currency': 'NONE', 'max_cost_units': 0,
            'prompts': {'first': 'Invent freely.', 'second': 'Independently explore.'},
            'source_presentation': SCHEMA, 'tools': deepcopy(TOOLS),
            'generation_parameters': {}, 'max_output_tokens': 4096,
            'call_timeout_seconds': 10, 'max_retries': 0}


def final(text):
    return {'status': 'final', 'record': {'kind': 'idea', 'content': {'text': text},
            'scope': {}, 'source_refs': []}}


class InquiryRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.broker = InquiryBroker(self.tmp.name)
        self.admin = LocalClient(self.broker, self.broker.admin_token)
        self.clients = {}
        for worker in ('first', 'second'):
            token = self.admin.call('register_worker', name=worker, role='discovery',
                capabilities=['research-record/v1'])['token']
            self.clients[worker] = LocalClient(self.broker, token)
        self.source = self.admin.call('add_research', kind='source',
            content={'text': 'A fixed permitted development source.', 'uri': 'fixture:inquiry'},
            scope={}, source_refs=[])['id']
        self.context = self.admin.call('create_context', role='discovery', epoch=1,
                                      artifact_ids=[self.source])['id']

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def setup_epoch(self, **changes):
        base = profile()
        base.update(changes)
        self.bundle = build_profile(base, Path('docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md').read_bytes())
        self.binding = self.broker.prepare_inquiry_binding(self.broker.admin_token,
                                                         base_profile=base, bundle=self.bundle)
        self.epoch = self.admin.call('create_research_epoch', key='new-route', context_id=self.context,
            workers=['first', 'second'], profile=self.bundle['profile'], inquiry_binding=self.binding)['id']
        batch = self.admin.call('create_batch', key='new-route-batch', epoch=1)['id']
        for worker in ('first', 'second'):
            self.admin.call('enqueue', key='job-' + worker, spec={
                'kind': 'research-record/v1', 'context_id': self.context, 'purpose': 'Free permitted inquiry.',
                'allowed_workers': [worker], 'max_attempts': 1, 'lease_seconds': 8,
                'deadline': int(time.time()) + 180, 'dependencies': [], 'batch_id': batch,
                'research_epoch_id': self.epoch})
        self.admin.call('seal_batch', batch_id=batch)

    def calls(self):
        return self.admin.call('inspect_research_epoch', epoch_id=self.epoch)['calls']

    def test_native_route_retains_exact_visible_packet_and_private_perspectives(self):
        self.setup_epoch()
        one = run_research_once(self.clients['first'], ScriptedProvider([final('FIRST_PRIVATE_IDEA')]))
        two = run_research_once(self.clients['second'], ScriptedProvider([final('SECOND_INDEPENDENT_IDEA')]))
        self.assertTrue(one['accepted'] and two['accepted'])
        self.assertFalse(one['genuine_discovery'])
        calls = self.calls()
        self.assertEqual(len(calls), 2)
        source = self.admin.call('get_artifact', artifact_id=self.source)
        self.assertEqual(calls[0]['request']['messages'],
                         initial_messages(self.bundle['profile'], 'first', 'Free permitted inquiry.', [source]))
        self.assertEqual(decode(calls[0]['request']['messages'][2]['content'])['schema'], SCHEMA)
        self.assertNotIn('FIRST_PRIVATE_IDEA', canonical(calls[1]['request']))
        self.assertEqual(self.admin.call('verify')['status'], 'PASS')

    def test_continuation_is_built_from_retained_actual_tool_results(self):
        self.setup_epoch()
        tools = {'status': 'tools', 'calls': [
            {'id': 'capabilities', 'name': 'capabilities', 'arguments': {}},
            {'id': 'read', 'name': 'read_source', 'arguments': {'artifact_id': self.source}}]}
        result = run_research_once(self.clients['first'], ScriptedProvider([tools, final('Untested original')]))
        self.assertTrue(result['accepted'])
        calls = self.calls()
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(calls[1]['request']['messages']), 6)
        self.assertIn('paired_reference_sections', canonical(calls[1]['request']['messages']))

    def test_ordinary_caps_and_legacy_grants_do_not_expand(self):
        base = profile()
        base['max_tokens'] = 80001
        bundle = build_profile(base, Path('docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md').read_bytes())
        binding = self.broker.prepare_inquiry_binding(self.broker.admin_token, base_profile=base, bundle=bundle)
        with self.assertRaises(Invalid):
            self.admin.call('create_research_epoch', key='too-large', context_id=self.context,
                workers=['first', 'second'], profile=bundle['profile'], inquiry_binding=binding)
        for field in ('budget_overlay', 'review_continuation'):
            with self.subTest(field=field), self.assertRaises(Denied):
                self.admin.call('create_research_epoch', key='old-budget', context_id=self.context,
                    workers=['first', 'second'], profile=bundle['profile'], inquiry_binding=binding,
                    **{field: 'old-policy'})


if __name__ == '__main__':
    unittest.main()
