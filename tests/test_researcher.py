"""Host-controlled research loop with isolated scripted providers, never live LLMs."""
from pathlib import Path
import tempfile
import threading
import time
import unittest

from trading_researcher.coordination import Broker
from trading_researcher.researcher import TOOL_DEFINITIONS, ScriptedProvider, run_research_once


class LocalClient:
    timeout = 2

    def __init__(self, broker, token):
        self.broker, self.token = broker, token

    def call(self, op, **args):
        return self.broker.call(self.token, op, **args)


def final(text='An unconventional untested hypothesis', kind='idea'):
    content = {'text': text}
    if kind == 'gap':
        content.update(reason='Needed measurement unavailable', reopen_condition='Independent certification')
    return {'status': 'final', 'record': {'kind': kind, 'content': content, 'scope': {}, 'source_refs': []}}


class ResearcherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.broker = Broker(self.tmp.name)
        self.admin = LocalClient(self.broker, self.broker.admin_token)
        self.clients = {}
        for name in ('first', 'second'):
            token = self.admin.call('register_worker', name=name, role='discovery',
                                    capabilities=['research-record/v1'])['token']
            self.clients[name] = LocalClient(self.broker, token)
        self.source = self.admin.call('add_research', kind='source',
                                     content={'text': 'Base observation', 'uri': 'fixture:loop'},
                                     scope={}, source_refs=[])['id']
        self.context = self.admin.call('create_context', role='discovery', epoch=1,
                                      artifact_ids=[self.source])['id']

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def setup_epoch(self, **changes):
        self.profile = {'model': 'fixture/1', 'prompt_version': 'research-loop/1',
                        'max_calls': 8, 'max_tokens': 80000, 'max_seconds': 60,
                        'max_cost_units': 0, 'currency': 'NONE', 'mode': 'fixture',
                        'prompts': {'first': 'Invent freely; record uncertainty.',
                                    'second': 'Independently investigate; record uncertainty.'},
                        'tools': TOOL_DEFINITIONS, 'generation_parameters': {},
                        'max_output_tokens': 4096, 'call_timeout_seconds': 10, 'max_retries': 0,
                        **changes}
        self.epoch = self.admin.call('create_research_epoch', key='epoch', context_id=self.context,
                                    workers=['first', 'second'], profile=self.profile)['id']
        batch = self.admin.call('create_batch', key='loop', epoch=1)['id']
        self.jobs = []
        for name in ('first', 'second'):
            self.jobs.append(self.admin.call('enqueue', key=name, spec={
                'kind': 'research-record/v1', 'context_id': self.context, 'purpose': 'Free inquiry',
                'allowed_workers': [name], 'max_attempts': 2, 'lease_seconds': 6,
                'deadline': int(time.time()) + 90, 'dependencies': [],
                'batch_id': batch, 'research_epoch_id': self.epoch})['id'])
        self.admin.call('seal_batch', batch_id=batch)
        return batch

    def calls(self):
        return self.admin.call('inspect_research_epoch', epoch_id=self.epoch)['calls']

    def test_sequential_perspectives_keep_private_transcripts_and_complete_batch(self):
        batch = self.setup_epoch()
        first = run_research_once(self.clients['first'], ScriptedProvider([final('Private first idea')]))
        second = run_research_once(self.clients['second'], ScriptedProvider([final('Independent second idea')]))
        self.assertTrue(first['accepted'] and second['accepted'])
        self.assertFalse(first['genuine_discovery'])
        calls = self.calls()
        self.assertEqual(len(calls), 2)
        self.assertNotIn('Private first idea', str(calls[1]['request']))
        self.assertIn('Base observation', str(calls[1]['request']))
        released = self.admin.call('release_batch', batch_id=batch, target_epoch=2)['artifact_ids']
        self.assertTrue(set(first['record_ids'] + second['record_ids']) <= set(released))
        self.assertEqual(self.admin.call('verify')['status'], 'PASS')

    def test_tool_requests_results_and_denial_are_retained(self):
        self.setup_epoch()
        tools = {'status': 'tools', 'calls': [
            {'id': 'read', 'name': 'read_source', 'arguments': {'artifact_id': self.source}},
            {'id': 'find', 'name': 'search_memory', 'arguments': {'query': 'observation'}},
            {'id': 'denied', 'name': 'shell', 'arguments': {'command': 'never executed'}}]}
        result = run_research_once(self.clients['first'], ScriptedProvider([tools, final()]))
        self.assertTrue(result['accepted'])
        request = self.calls()[1]['request']
        self.assertIn('tool_denied', str(request))
        self.assertIn('Base observation', str(request))
        transcript = [self.admin.call('get_artifact', artifact_id=identity) for identity in result['transcript_ids']]
        self.assertIn('provider-tool-result/1', str(transcript))

    def test_unsupported_idea_is_retained_as_gap_not_market_failure(self):
        self.setup_epoch()
        result = run_research_once(self.clients['first'], ScriptedProvider([final(kind='gap')]))
        record = self.admin.call('get_artifact', artifact_id=result['record_ids'][-1])
        self.assertEqual(record['body']['kind'], 'gap')
        self.assertFalse(result['scientific_authority'])

    def test_refusal_and_malformed_output_block_with_retained_public_reply(self):
        for reply in ({'status': 'refused', 'text': 'Cannot answer'},
                      {'status': 'final', 'record': {'kind': 'evidence', 'content': {}}}):
            with self.subTest(reply=reply):
                if not hasattr(self, 'epoch'):
                    self.setup_epoch()
                name = 'first' if not self.calls() else 'second'
                result = run_research_once(self.clients[name], ScriptedProvider([reply]))
                self.assertEqual(result['state'], 'blocked')
                self.assertEqual(self.calls()[-1]['reply']['response']['output'], reply)

    def test_timeout_terminates_child_and_keeps_unknown_usage_reserved(self):
        self.setup_epoch(call_timeout_seconds=1)
        start = time.monotonic()
        result = run_research_once(self.clients['first'], ScriptedProvider([final()], delay_seconds=10))
        self.assertEqual(result['state'], 'blocked')
        self.assertLess(time.monotonic() - start, 5)
        call = self.calls()[0]
        self.assertEqual(call['reply']['response']['status'], 'timeout')
        self.assertTrue(call['usage_unknown'])

    def test_cancellation_before_dispatch_costs_no_call(self):
        self.setup_epoch()
        cancel = threading.Event()
        cancel.set()
        result = run_research_once(self.clients['first'], ScriptedProvider([final()]), cancel=cancel)
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(self.calls(), [])

    def test_cancellation_during_dispatch_keeps_receipt_and_cleans_process(self):
        import multiprocessing
        self.setup_epoch()
        cancel = threading.Event()
        before = {p.pid for p in multiprocessing.active_children()}
        timer = threading.Timer(0.4, cancel.set)
        timer.start()
        try:
            result = run_research_once(self.clients['first'], ScriptedProvider([final()], delay_seconds=10),
                                       cancel=cancel)
        finally:
            timer.cancel()
            timer.join()
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(self.calls()[0]['reply']['response']['status'], 'cancelled')
        self.assertEqual({p.pid for p in multiprocessing.active_children()}, before)

    def test_transport_retry_is_new_accounted_call_and_bounded(self):
        self.setup_epoch(max_retries=1)
        provider = ScriptedProvider([{'status': 'failed', 'error': 'fixture network failure'}, final()])
        result = run_research_once(self.clients['first'], provider)
        self.assertTrue(result['accepted'])
        self.assertEqual(len(self.calls()), 2)

    def test_call_cap_stops_tool_loop(self):
        self.setup_epoch(max_calls=1)
        provider = ScriptedProvider([{'status': 'tools', 'calls': [
            {'id': 'capabilities', 'name': 'capabilities', 'arguments': {}}]}, final()])
        result = run_research_once(self.clients['first'], provider)
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(len(self.calls()), 1)

    def test_adapter_reservation_failure_is_sanitized_and_durably_blocked(self):
        self.setup_epoch()
        provider = ScriptedProvider([final()])
        def failed_reservation(*args):
            raise RuntimeError('SECRET test token must never be retained')
        provider.reservation = failed_reservation
        result = run_research_once(self.clients['first'], provider)
        self.assertEqual(result['state'], 'blocked')
        job = self.admin.call('inspect', job_id=self.jobs[0])
        self.assertEqual(job['attempts'][0]['state'], 'blocked')
        self.assertIn('RuntimeError', str(job))
        self.assertNotIn('SECRET', str(job))
        self.assertEqual(self.calls(), [])


if __name__ == '__main__':
    unittest.main()
