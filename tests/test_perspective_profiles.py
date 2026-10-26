"""Frozen per-perspective models; fixture transport only, no paid requests."""
from copy import deepcopy
import unittest

import test_research_calls as call_support
import test_researcher as loop_support
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.researcher import ScriptedProvider, run_research_once


def profiles(output_limit=64):
    return {name: {'model': model, 'prompt_version': name + '/1',
                   'generation_parameters': {'reasoning': name},
                   'max_output_tokens': output_limit, 'call_timeout_seconds': 5,
                   'max_retries': 0}
            for name, model in [('first', 'fixture-a/1'), ('second', 'fixture-b/2')]}


class PerspectiveProfileTests(unittest.TestCase):
    setUp = call_support.ResearchCallTests.setUp
    tearDown = call_support.ResearchCallTests.tearDown
    op = call_support.ResearchCallTests.op
    setup_epoch = call_support.ResearchCallTests.setup_epoch
    reserve = call_support.ResearchCallTests.reserve
    finish = call_support.ResearchCallTests.finish
    complete_job = call_support.ResearchCallTests.complete_job

    def request_for(self, name):
        selected = profiles()[name]
        return {**self.request, **{key: selected[key] for key in
                ('model', 'prompt_version', 'generation_parameters')},
                'messages': [{'role': 'system', 'content': self.profile['prompts'][name]}]}

    def test_models_are_frozen_isolated_and_share_original_budget(self):
        selected = profiles()
        epoch, first = self.setup_epoch(perspective_profiles=selected)
        selected['first']['model'] = 'caller-mutation'
        state = self.broker.call(self.tokens['first'], 'research_call_state', lease=first)
        self.assertEqual(state['profile']['model'], 'fixture-a/1')
        self.assertEqual(state['profile']['max_calls'], 2)
        with self.assertRaises(Invalid):
            self.reserve(first)  # Root default cannot override the selected model.
        call = self.reserve(first, request=self.request_for('first'))
        receipt = self.finish(first, call['call_id'], usage={'input_tokens': 10, 'output_tokens': 20, 'cost_units': 0})
        self.complete_job(first)
        second = self.broker.call(self.tokens['second'], 'claim')['lease']
        state = self.broker.call(self.tokens['second'], 'research_call_state', lease=second)
        self.assertEqual(state['profile']['model'], 'fixture-b/2')
        self.assertEqual(state['calls'], [])
        with self.assertRaises(Denied):
            self.broker.call(self.tokens['second'], 'read_artifact', lease=second,
                             artifact_id=receipt['response_id'])
        call = self.reserve(second, name='second', request=self.request_for('second'))
        self.finish(second, call['call_id'], name='second',
                    usage={'input_tokens': 10, 'output_tokens': 20, 'cost_units': 0})
        with self.assertRaises(Denied):
            self.reserve(second, name='second', key='third', request=self.request_for('second'))
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['tokens'], 60)

    def test_identity_and_unknown_reservations_survive_restart(self):
        epoch, lease = self.setup_epoch(perspective_profiles=profiles())
        call = self.reserve(lease, request=self.request_for('first'))
        self.finish(lease, call['call_id'], response={'status': 'timeout'})
        self.broker.close()
        self.broker = Broker(self.tmp.name, clock=lambda: self.now)
        state = self.broker.call(self.tokens['first'], 'research_call_state', lease=lease)
        self.assertEqual(state['profile']['model'], 'fixture-a/1')
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['tokens'], 1088)
        with self.assertRaises(Denied):
            self.reserve(lease, key='again', request=self.request_for('first'))
        changed = profiles()
        changed['first']['model'] = 'replacement'
        with self.assertRaises(Conflict):
            self.op('create_research_epoch', key='epoch', context_id=self.context,
                    workers=['first', 'second'], profile={**self.profile, 'perspective_profiles': changed})

    def test_missing_extra_and_budget_overrides_are_rejected(self):
        invalid = [None, {}, {'first': profiles()['first']},
                   {**profiles(), 'third': profiles()['first']}]
        for key, value in [('max_calls', 12), ('mode', 'live'), ('tools', []), ('prompt', 'other'),
                           ('max_tokens', 80000), ('currency', 'USD'), ('model', ''),
                           ('generation_parameters', []), ('max_output_tokens', True),
                           ('max_output_tokens', 2001), ('call_timeout_seconds', 61), ('max_retries', 1)]:
            bad = deepcopy(profiles())
            bad['first'][key] = value
            invalid.append(bad)
        for index, selected in enumerate(invalid):
            with self.subTest(index=index), self.assertRaises(Invalid):
                self.op('create_research_epoch', key='invalid-' + str(index), context_id=self.context,
                        workers=['first', 'second'], profile={**self.profile, 'perspective_profiles': selected})

    def test_omission_preserves_legacy_profile_exactly(self):
        _, lease = self.setup_epoch()
        self.assertEqual(self.broker.call(self.tokens['first'], 'research_call_state', lease=lease)['profile'],
                         self.profile)


class PerspectiveLoopTests(unittest.TestCase):
    setUp = loop_support.ResearcherTests.setUp
    tearDown = loop_support.ResearcherTests.tearDown
    setup_epoch = loop_support.ResearcherTests.setup_epoch
    calls = loop_support.ResearcherTests.calls

    def test_two_different_adapters_complete_without_peer_transcript(self):
        self.setup_epoch(perspective_profiles=profiles(4096))
        first = run_research_once(self.clients['first'], ScriptedProvider(
            [loop_support.final('Private model A idea')], model='fixture-a/1'))
        second = run_research_once(self.clients['second'], ScriptedProvider(
            [loop_support.final('Independent model B idea')], model='fixture-b/2'))
        self.assertTrue(first['accepted'] and second['accepted'])
        calls = self.calls()
        self.assertEqual([call['request']['model'] for call in calls], ['fixture-a/1', 'fixture-b/2'])
        self.assertEqual([call['request']['prompt_version'] for call in calls], ['first/1', 'second/1'])
        self.assertNotIn('Private model A idea', str(calls[1]['request']))
        self.assertIn('Base observation', str(calls[1]['request']))
        self.assertEqual(self.admin.call('verify')['status'], 'PASS')

    def test_wrong_adapter_blocks_before_dispatch(self):
        self.setup_epoch(perspective_profiles=profiles(4096))
        result = run_research_once(self.clients['first'], ScriptedProvider([loop_support.final()]))
        self.assertFalse(result['accepted'])
        self.assertEqual(self.calls(), [])


if __name__ == '__main__':
    unittest.main()
