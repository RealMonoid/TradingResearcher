"""Independent role-profile, shared-budget and auxiliary-interaction checks."""
from copy import deepcopy
import unittest

import test_auxiliary_research as auxiliary_support
import test_research_calls as call_support
import test_researcher as loop_support
from trading_researcher import auxiliary
from trading_researcher.codec import canonical, decode
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.researcher import CONTEXT_TOOL_DEFINITIONS, ScriptedProvider, run_research_once


def settings():
    return {
        'first': {'model': 'fixture-vendor-alpha/model-a-202610', 'prompt_version': 'alpha-prompt/3',
                  'generation_parameters': {'seed': 17, 'reasoning': 'alpha'},
                  'max_output_tokens': 40, 'call_timeout_seconds': 3, 'max_retries': 1},
        'second': {'model': 'fixture-vendor-beta/model-b-202610', 'prompt_version': 'beta-prompt/5',
                   'generation_parameters': {'seed': 23, 'reasoning': 'beta'},
                   'max_output_tokens': 30, 'call_timeout_seconds': 8, 'max_retries': 0},
    }


class PerspectiveProfileAdversarialTests(unittest.TestCase):
    tearDown = call_support.ResearchCallTests.tearDown
    op = call_support.ResearchCallTests.op
    setup_epoch = call_support.ResearchCallTests.setup_epoch
    finish = call_support.ResearchCallTests.finish
    complete_job = call_support.ResearchCallTests.complete_job
    auxiliary = auxiliary_support.AuxiliaryBudgetTests.auxiliary

    def setUp(self):
        call_support.ResearchCallTests.setUp(self)
        # These are synthetic fixture units, not a vendor-price model.
        self.profile.update(max_calls=4, max_tokens=500, max_cost_units=90,
                            currency='FIXTURE_UNITS', max_retries=1)

    def start(self, **changes):
        self.selected = settings()
        self.epoch, first = self.setup_epoch(perspective_profiles=self.selected, **changes)
        return first

    def role_request(self, name):
        selected = settings()[name]
        return {'model': selected['model'], 'prompt_version': selected['prompt_version'],
                'generation_parameters': deepcopy(selected['generation_parameters']),
                'tools': [], 'messages': [{'role': 'system', 'content': self.profile['prompts'][name]}]}

    def reserve(self, lease, name='first', key='call', tokens=200, cost=60, **changes):
        args = {'lease': lease, 'key': key, 'request': self.role_request(name),
                'input_token_bound': tokens, 'output_token_limit': settings()[name]['max_output_tokens'],
                'cost_bound_units': cost, **changes}
        return self.broker.call(self.tokens[name], 'reserve_research_call', **args)

    def known_first(self, **changes):
        first = self.start(**changes)
        call = self.reserve(first)
        receipt = self.finish(first, call['call_id'],
                              usage={'input_tokens': 120, 'output_tokens': 20, 'cost_units': 35})
        self.complete_job(first)
        second = self.broker.call(self.tokens['second'], 'claim')['lease']
        return first, second, receipt

    def test_cross_vendor_token_and_money_bounds_remain_one_exact_epoch_total(self):
        _, second, _ = self.known_first()
        # 35 + 55 = 90: the second reservation exactly fills the shared money cap.
        call = self.reserve(second, name='second', tokens=250, cost=55)
        self.finish(second, call['call_id'], name='second',
                    usage={'input_tokens': 200, 'output_tokens': 15, 'cost_units': 45})
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage'],
                         {'calls': 2, 'tokens': 355, 'cost_units': 80})
        # 355 + 116 + 30 = 501 exceeds the one shared 500-token cap.
        with self.assertRaises(Denied):
            self.reserve(second, name='second', key='too-many-tokens', tokens=116, cost=0)
        # Token bound fits, but 80 + 11 = 91 exceeds the shared currency cap.
        with self.assertRaises(Denied):
            self.reserve(second, name='second', key='too-much-cost', tokens=1, cost=11)
        third = self.reserve(second, name='second', key='exact-cost-bound', tokens=1, cost=10)
        self.finish(second, third['call_id'], name='second',
                    usage={'input_tokens': 1, 'output_tokens': 30, 'cost_units': 10})
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage'],
                         {'calls': 3, 'tokens': 386, 'cost_units': 90})

    def test_profile_substitution_cannot_change_the_other_role_or_root_authority(self):
        first = self.start()
        self.assertIsNone(self.broker.call(self.tokens['second'], 'claim'))
        public = self.broker.call(self.tokens['first'], 'research_call_state', lease=first)
        public['profile']['max_tokens'] = 99999
        public['profile']['perspective_profiles']['second']['model'] = 'caller-mutation'
        public['profile']['tools'].append({'name': 'shell'})
        fresh = self.broker.call(self.tokens['first'], 'research_call_state', lease=first)
        self.assertEqual(fresh['profile']['perspective_profiles']['second']['model'], settings()['second']['model'])
        self.assertEqual(fresh['profile']['max_tokens'], 500)
        self.assertEqual(fresh['profile']['tools'], [])
        self.assertEqual(fresh['calls'], [])
        with self.assertRaises(Denied):
            self.broker.call(self.tokens['second'], 'research_call_state', lease=first)
        for changed in ({'model': settings()['second']['model']},
                        {'prompt_version': settings()['second']['prompt_version']},
                        {'generation_parameters': settings()['second']['generation_parameters']},
                        {'messages': [{'role': 'system', 'content': self.profile['prompts']['second']}]},
                        {'tools': [{'name': 'shell'}]}):
            with self.subTest(changed=changed), self.assertRaises(Invalid):
                self.reserve(first, request={**self.role_request('first'), **changed})
        with self.assertRaises(Invalid):
            self.reserve(first, output_token_limit=self.profile['max_output_tokens'])
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage']['calls'], 0)
        self.complete_job(first)
        second = self.broker.call(self.tokens['second'], 'claim')['lease']
        fresh = self.broker.call(self.tokens['second'], 'research_call_state', lease=second)
        self.assertEqual(fresh['profile']['model'], settings()['second']['model'])
        self.assertEqual(fresh['calls'], [])

    def test_settled_peer_reply_and_request_remain_private_under_distinct_profiles(self):
        _, second, receipt = self.known_first()
        response = self.op('get_artifact', artifact_id=receipt['response_id'])
        request_id, = response['source_refs']
        for artifact_id in (receipt['response_id'], request_id):
            with self.subTest(artifact_id=artifact_id), self.assertRaises(Denied):
                self.broker.call(self.tokens['second'], 'read_artifact', lease=second, artifact_id=artifact_id)
        state = self.broker.call(self.tokens['second'], 'research_call_state', lease=second)
        self.assertEqual(state['calls'], [])
        self.assertEqual(state['profile']['model'], settings()['second']['model'])

    def test_pending_and_unknown_charges_survive_restart_without_role_budget_reset(self):
        first = self.start()
        call = self.reserve(first)
        self.assertIsNone(self.broker.call(self.tokens['second'], 'claim'))
        self.broker.close()
        self.broker = Broker(self.tmp.name, clock=lambda: self.now)
        replay = self.reserve(first)
        self.assertEqual(replay['call_id'], call['call_id'])
        self.assertFalse(replay['dispatch'])
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage'],
                         {'calls': 1, 'tokens': 240, 'cost_units': 60})
        with self.assertRaises(Denied):
            self.reserve(first, key='while-unresolved', tokens=1, cost=0)
        with self.assertRaises(Denied):
            self.complete_job(first)
        self.finish(first, call['call_id'], response={'status': 'failed'})
        self.complete_job(first)
        second = self.broker.call(self.tokens['second'], 'claim')['lease']
        # Settled unknown usage still charges 240 tokens and 60 currency units.
        with self.assertRaises(Denied):
            self.reserve(second, name='second', tokens=230, cost=31)
        admitted = self.reserve(second, name='second', tokens=230, cost=30)
        self.assertTrue(admitted['dispatch'])
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage'],
                         {'calls': 2, 'tokens': 500, 'cost_units': 90})
        self.assertEqual(self.broker.call(self.tokens['second'], 'research_call_state', lease=second)['profile']['model'],
                         settings()['second']['model'])

    def test_later_vendor_call_is_clamped_to_original_epoch_deadline(self):
        first = self.start(max_seconds=10)
        call = self.reserve(first)
        self.assertEqual(call['deadline'], 1003)
        self.finish(first, call['call_id'], usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
        self.complete_job(first)
        self.now = 1009
        second = self.broker.call(self.tokens['second'], 'claim')['lease']
        call = self.reserve(second, name='second', tokens=1, cost=1)
        self.assertEqual(call['deadline'], 1010)
        self.now = 1010
        receipt = self.finish(second, call['call_id'], name='second',
                              usage={'input_tokens': 1, 'output_tokens': 1, 'cost_units': 1})
        self.assertTrue(receipt['late'])
        with self.assertRaises(Denied):
            self.reserve(second, name='second', key='after-epoch', tokens=1, cost=0)

    def test_auxiliary_profile_precedes_discovery_map_and_shares_the_same_money(self):
        _, second, _ = self.known_first()
        self.complete_job(second, 'second')
        token, spec = self.auxiliary(self.epoch, key='formalizer-third')
        selected = spec['research_call_profile']
        selected.update(model='fixture-vendor-gamma/formalizer-9', prompt_version='formalizer/9',
                        generation_parameters={'seed': 31}, max_output_tokens=25,
                        call_timeout_seconds=6, max_retries=1)
        self.op('enqueue', key='formalizer-job', spec=spec)
        lease = self.broker.call(token, 'claim')['lease']
        state = self.broker.call(token, 'research_call_state', lease=lease)
        self.assertEqual(state['profile']['model'], selected['model'])
        self.assertEqual(state['profile']['prompts'], {'formalizer-third': selected['prompt']})
        self.assertEqual(state['profile']['tools'], [])
        self.assertEqual(state['profile']['max_cost_units'], 90)
        packet = self.broker.call(token, 'auxiliary_input', lease=lease)
        request = auxiliary.request_for(spec, packet)
        args = {'lease': lease, 'request': request, 'input_token_bound': 100,
                'output_token_limit': 25, 'cost_bound_units': 55}
        call = self.broker.call(token, 'reserve_research_call', key='formalize', **args)
        self.broker.call(token, 'finish_research_call', lease=lease, call_id=call['call_id'],
                         response={'status': 'failed'}, usage={'input_tokens': 100, 'output_tokens': 25, 'cost_units': 55})
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage'],
                         {'calls': 2, 'tokens': 265, 'cost_units': 90})
        with self.assertRaises(Denied):
            self.broker.call(token, 'reserve_research_call', key='retry',
                             **{**args, 'input_token_bound': 1, 'cost_bound_units': 1})
        with self.assertRaises(Invalid):
            self.broker.call(token, 'reserve_research_call', key='discovery-substitution',
                             **{**args, 'request': {**request, 'model': settings()['first']['model']}})

    def test_auxiliary_cannot_bypass_an_unresolved_other_vendor_dispatch(self):
        first = self.start()
        self.reserve(first)
        self.broker.call(self.tokens['first'], 'block', lease=first, reason='Fixture unresolved dispatch',
                         needs=['Explicit reconciliation'], retry_when='Retained dispatch is reconciled')
        second = self.broker.call(self.tokens['second'], 'claim')['lease']
        with self.assertRaises(Denied):
            self.reserve(second, name='second', tokens=1, cost=0)
        self.broker.call(self.tokens['second'], 'block', lease=second, reason='Fixture prior dispatch unresolved',
                         needs=['Explicit reconciliation'], retry_when='Original dispatch is reconciled')
        token, spec = self.auxiliary(self.epoch, key='formalizer-pending')
        self.op('enqueue', key='formalizer-pending', spec=spec)
        lease = self.broker.call(token, 'claim')['lease']
        packet = self.broker.call(token, 'auxiliary_input', lease=lease)
        with self.assertRaises(Denied):
            self.broker.call(token, 'reserve_research_call', lease=lease, key='blocked',
                             request=auxiliary.request_for(spec, packet), input_token_bound=1,
                             output_token_limit=64, cost_bound_units=0)
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage'],
                         {'calls': 1, 'tokens': 240, 'cost_units': 60})

    def test_explicit_per_call_values_can_exceed_root_defaults_but_not_total_caps(self):
        selected = settings()
        selected['first'].update(max_output_tokens=65, call_timeout_seconds=6)
        epoch, lease = self.setup_epoch(perspective_profiles=selected)
        effective = self.broker.call(self.tokens['first'], 'research_call_state', lease=lease)['profile']
        self.assertEqual(effective['max_output_tokens'], 65)
        self.assertEqual(effective['call_timeout_seconds'], 6)
        self.assertEqual(effective['max_tokens'], 500)
        self.assertEqual(effective['max_seconds'], 60)
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['request']['profile']['max_output_tokens'], 64)
        for field, value in [('max_output_tokens', 501), ('call_timeout_seconds', 61),
                             ('max_calls', 999), ('max_cost_units', 999), ('context_id', 'other'),
                             ('source_presentation', 'discovery-source-view/2')]:
            bad = deepcopy(selected)
            bad['first'][field] = value
            with self.subTest(field=field), self.assertRaises(Invalid):
                self.op('create_research_epoch', key='bad-' + field, context_id=self.context,
                        workers=['first', 'second'], profile={**self.profile, 'perspective_profiles': bad})


class PerspectivePresentationAdversarialTests(unittest.TestCase):
    def test_both_presentation_versions_keep_role_model_prompt_and_isolation(self):
        for version in ('discovery-source-view/1', 'discovery-source-view/2'):
            with self.subTest(version=version):
                fixture = loop_support.ResearcherTests()
                fixture.setUp()
                try:
                    selected = settings()
                    # Fixture provider counts bytes; allow enough output without changing aggregate limits.
                    for profile in selected.values():
                        profile.update(max_output_tokens=4096, call_timeout_seconds=5, max_retries=0)
                    fixture.setup_epoch(perspective_profiles=selected, source_presentation=version,
                                        tools=CONTEXT_TOOL_DEFINITIONS)
                    first = run_research_once(fixture.clients['first'], ScriptedProvider(
                        [loop_support.final('Only alpha has this private fixture idea')], model=selected['first']['model']))
                    second = run_research_once(fixture.clients['second'], ScriptedProvider(
                        [loop_support.final('Separate beta fixture idea')], model=selected['second']['model']))
                    self.assertTrue(first['accepted'] and second['accepted'])
                    calls = fixture.calls()
                    self.assertEqual(len(calls), 2)
                    for call, name in zip(calls, ('first', 'second')):
                        request = call['request']
                        self.assertEqual(request['model'], selected[name]['model'])
                        self.assertEqual(request['prompt_version'], selected[name]['prompt_version'])
                        self.assertEqual(request['generation_parameters'], selected[name]['generation_parameters'])
                        self.assertEqual(request['tools'], CONTEXT_TOOL_DEFINITIONS)
                        source = decode(request['messages'][1]['content'])['sources'][0]
                        self.assertEqual(source['schema'], 'discovery-source-view/1')
                        self.assertEqual(source['artifact_id'], fixture.source)
                    self.assertNotIn('Only alpha has this private fixture idea', canonical(calls[1]['request']))
                    self.assertEqual(fixture.admin.call('verify')['status'], 'PASS')
                finally:
                    fixture.tearDown()


if __name__ == '__main__':
    unittest.main()
