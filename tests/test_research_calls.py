"""Durable call budgets for the two-perspective research loop; no paid API calls."""
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from trading_researcher.coordination import Broker, Conflict, Denied, Invalid


class ResearchCallTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.now = 1000
        self.broker = Broker(self.tmp.name, clock=lambda: self.now)
        self.admin = self.broker.admin_token
        self.tokens = {name: self.op('register_worker', name=name, role='discovery',
                                    capabilities=['research-record/v1'])['token'] for name in ('first', 'second')}
        self.context = self.op('create_context', role='discovery', epoch=1, artifact_ids=[])['id']
        self.profile = {'model': 'fixture/1', 'prompt_version': 'fixture-prompt/1',
                        'max_calls': 2, 'max_tokens': 2000, 'max_seconds': 60,
                        'max_cost_units': 0, 'currency': 'NONE', 'mode': 'fixture',
                        'prompts': {'first': 'First independent perspective', 'second': 'Second independent perspective'},
                        'tools': [], 'generation_parameters': {},
                        'max_output_tokens': 64, 'call_timeout_seconds': 5, 'max_retries': 0}
        self.request = {'model': 'fixture/1', 'prompt_version': 'fixture-prompt/1',
                        'messages': [{'role': 'system', 'content': self.profile['prompts']['first']}],
                        'tools': [], 'generation_parameters': {}}

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def op(self, op, **args):
        return self.broker.call(self.admin, op, **args)

    def setup_epoch(self, **changes):
        profile = {**self.profile, **changes}
        epoch = self.op('create_research_epoch', key='epoch', context_id=self.context,
                        workers=['first', 'second'], profile=profile)['id']
        batch = self.op('create_batch', key='research-batch', epoch=1)['id']
        for name in self.tokens:
            self.op('enqueue', key=name, spec={
                'kind': 'research-record/v1', 'context_id': self.context, 'purpose': 'Free research',
                'allowed_workers': [name], 'max_attempts': 2, 'lease_seconds': 10,
                'deadline': 1100, 'dependencies': [], 'batch_id': batch, 'research_epoch_id': epoch})
        self.op('seal_batch', batch_id=batch)
        return epoch, self.broker.call(self.tokens['first'], 'claim')['lease']

    def reserve(self, lease, name='first', key='call', **changes):
        args = {'lease': lease, 'key': key, 'request': self.request,
                'input_token_bound': 1024, 'output_token_limit': 64, 'cost_bound_units': 0}
        if name == 'second':
            args['request'] = {**self.request, 'messages': [{'role': 'system', 'content': self.profile['prompts'][name]}]}
        return self.broker.call(self.tokens[name], 'reserve_research_call', **{**args, **changes})

    def finish(self, lease, call_id, name='first', usage=None, response=None):
        return self.broker.call(self.tokens[name], 'finish_research_call', lease=lease, call_id=call_id,
                                response=response or {'status': 'completed', 'output': 'fixture'}, usage=usage)

    def complete_job(self, lease, name='first'):
        idea = self.broker.call(self.tokens[name], 'record_research', lease=lease, kind='idea',
                               content={'text': 'Unrestricted idea fixture'}, scope={}, source_refs=[])['id']
        return self.broker.call(self.tokens[name], 'submit', lease=lease, artifact_id=idea)

    def test_reservation_precedes_dispatch_and_duplicate_cannot_dispatch_twice(self):
        epoch, lease = self.setup_epoch()
        first = self.reserve(lease)
        self.assertTrue(first['dispatch'])
        repeated = self.reserve(lease)
        self.assertEqual(repeated['call_id'], first['call_id'])
        self.assertFalse(repeated['dispatch'])
        with self.assertRaises(Conflict):
            self.reserve(lease, request={**self.request, 'messages': self.request['messages'] + ['changed']})
        calls = self.op('inspect_research_epoch', epoch_id=epoch)['calls']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['state'], 'reserved')
        self.assertEqual(calls[0]['request'], self.request)

    def test_two_perspectives_share_budget_but_not_call_transcripts(self):
        epoch, lease = self.setup_epoch()
        first = self.reserve(lease)
        self.finish(lease, first['call_id'], usage={'input_tokens': 10, 'output_tokens': 20, 'cost_units': 0})
        self.complete_job(lease)
        second = self.broker.call(self.tokens['second'], 'claim')['lease']
        self.assertEqual(self.broker.call(self.tokens['second'], 'research_call_state', lease=second)['calls'], [])
        call = self.reserve(second, name='second')
        self.finish(second, call['call_id'], name='second',
                    usage={'input_tokens': 10, 'output_tokens': 20, 'cost_units': 0})
        with self.assertRaises(Denied):
            self.reserve(second, name='second', key='third')
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['calls'], 2)

    def test_unknown_usage_retains_reservation_across_restart(self):
        epoch, lease = self.setup_epoch()
        call = self.reserve(lease)
        self.finish(lease, call['call_id'], response={'status': 'failed', 'error': 'timeout'})
        self.broker.close()
        self.broker = Broker(self.tmp.name, clock=lambda: self.now)
        state = self.op('inspect_research_epoch', epoch_id=epoch)
        self.assertEqual(state['usage']['tokens'], 1088)
        self.assertTrue(state['calls'][0]['usage_unknown'])
        with self.assertRaises(Denied):
            self.reserve(lease, key='retry')

    def test_reported_overrun_is_retained_and_halts_epoch(self):
        epoch, lease = self.setup_epoch()
        call = self.reserve(lease)
        result = self.finish(lease, call['call_id'],
                             usage={'input_tokens': 1100, 'output_tokens': 20, 'cost_units': 0})
        self.assertFalse(result['within_reservation'])
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['state'], 'halted')
        with self.assertRaises(Denied):
            self.reserve(lease, key='another')

    def test_late_response_is_retained_without_granting_current_attempt_authority(self):
        epoch, lease = self.setup_epoch()
        call = self.reserve(lease)
        self.now = 1011
        self.broker.call(self.tokens['first'], 'claim')
        result = self.finish(lease, call['call_id'], usage={'input_tokens': 10, 'output_tokens': 20, 'cost_units': 0})
        self.assertTrue(result['late'])
        with self.assertRaises(Denied):
            self.finish(lease, call['call_id'], name='second')
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['tokens'], 30)

    def test_approved_caps_and_paid_readiness_are_not_silently_expanded(self):
        for changes in ({'max_calls': 13}, {'max_tokens': 80001}, {'max_seconds': 1801},
                        {'mode': 'live', 'max_cost_units': 0}, {'max_tokens': True}):
            with self.assertRaises(Invalid):
                self.op('create_research_epoch', key=str(changes), context_id=self.context,
                        workers=['first', 'second'], profile={**self.profile, **changes})
        with self.assertRaises(Invalid):
            self.op('create_research_epoch', key='one', context_id=self.context,
                    workers=['first'], profile=self.profile)

    def test_epoch_clock_and_frozen_request_identity(self):
        epoch, lease = self.setup_epoch(max_seconds=5)
        with self.assertRaises(Invalid):
            self.reserve(lease, request={**self.request, 'model': 'different'})
        self.now = 1006
        with self.assertRaises(Denied):
            self.reserve(lease)
        with self.assertRaises(Conflict):
            self.op('create_research_epoch', key='epoch', context_id=self.context,
                    workers=['first', 'second'], profile={**self.profile, 'max_calls': 1})

    def test_prompt_tools_and_generation_configuration_are_frozen(self):
        epoch, lease = self.setup_epoch()
        for change in ({'messages': [{'role': 'system', 'content': 'Unrecorded new policy'}]},
                       {'tools': [{'name': 'shell'}]}, {'generation_parameters': {'temperature': '1'}}):
            with self.assertRaises(Invalid):
                self.reserve(lease, request={**self.request, **change})

    def test_pending_dispatch_survives_restart_and_blocks_completion_and_next_call(self):
        epoch, lease = self.setup_epoch(max_tokens=80000)
        pending = self.reserve(lease)
        self.broker.close()
        self.broker = Broker(self.tmp.name, clock=lambda: self.now)
        with self.assertRaises(Denied):
            self.reserve(lease, key='second-call')
        with self.assertRaises(Denied):
            self.complete_job(lease)
        self.finish(lease, pending['call_id'], response={'status': 'failed', 'error': 'reconciled'})
        self.assertTrue(self.complete_job(lease)['accepted'])

    def test_malformed_usage_retains_public_response_and_halts_unknown_accounting(self):
        epoch, lease = self.setup_epoch()
        pending = self.reserve(lease)
        response = {'status': 'completed', 'output': {'text': 'Retain this public partial output'}}
        receipt = self.finish(lease, pending['call_id'], response=response, usage={'input_tokens': 10})
        self.assertTrue(receipt['usage_unknown'])
        self.assertFalse(receipt['accounting_valid'])
        state = self.op('inspect_research_epoch', epoch_id=epoch)
        self.assertEqual(state['state'], 'halted')
        self.assertEqual(state['calls'][0]['reply']['response'], response)
        self.assertEqual(state['calls'][0]['reply']['usage'], {'input_tokens': 10})
        self.assertEqual(state['usage']['tokens'], 1088)


if __name__ == '__main__':
    unittest.main()
