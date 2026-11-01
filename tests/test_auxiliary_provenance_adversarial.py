"""Independent adapter-only provenance boundaries, without network/API calls.

Authentic Broker jobs, reservations and synthetic recorded replies are used.
No reply or structural check is evidence of a genuine independent model review.
The archived packet-level approach and its additional cross-role presentation-
equality rule were discarded. Each role keeps its full normalized source packet
and its own exact frozen route/configuration; only the API wire is transformed.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.auxiliary import request_for
from trading_researcher.auxiliary_views import PROFILE, restore
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied
from trading_researcher import openai_provider as api


class AuxiliaryProvenanceAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = {**api.configuration(input_token_limit=12000, output_token_limit=64),
            'source_presentation': PROFILE}
        self.routes = {api.MODEL: {'provider': 'openai', 'config': deepcopy(self.config),
            'key_file': str(Path(self.temp.name) / 'absent-key'),
            'budget_file': str(Path(self.temp.name) / 'unused-ledger')}}
        self.broker = Broker(Path(self.temp.name) / 'registry', clock=lambda: 1000, provider_routes=self.routes)
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(self.broker.close)
        for name in ('first', 'second'):
            self.op('register_worker', name=name, role='discovery', capabilities=['research-record/v1'])
        self.hidden = self.op('add_source', body={'text': 'PRIVATE SOURCE BODY SENTINEL'}, data_class='development')['id']
        self.idea = self.op('add_research', kind='idea', content={'text': '  Exact synthetic idea.\n'},
            scope={}, source_refs=[self.hidden])['id']
        self.catalog = self.op('add_source', body={'schema': 'feature-catalog/1', 'features': {}}, data_class='development')['id']
        discovery = self.op('create_context', role='discovery', epoch=1, artifact_ids=[self.idea, self.catalog])['id']
        self.epoch = self.op('create_research_epoch', key='bounded-offline-epoch', context_id=discovery,
            workers=['first', 'second'], profile={
                'model': api.MODEL, 'prompt_version': 'fixture/1', 'mode': 'live', 'currency': 'USD',
                'max_calls': 12, 'max_tokens': 80000, 'max_seconds': 1800, 'max_cost_units': 1000000000,
                'prompts': {'first': 'First synthetic perspective.', 'second': 'Second synthetic perspective.'},
                'tools': [], 'generation_parameters': {'openai_responses': deepcopy(self.config)}, 'max_output_tokens': 64,
                'call_timeout_seconds': 5, 'max_retries': 0})['id']
        self.context = self.op('create_context', role='formalizer', epoch=1, artifact_ids=[self.idea, self.catalog])['id']
        self.formalizer = self.op('register_worker', name='formalizer', role='formalizer', capabilities=['formalization/v1'])['token']
        self.reviewer = self.op('register_worker', name='reviewer', role='formalizer', capabilities=['semantic-review/v1'])['token']
        self.profile = {'model': api.MODEL, 'prompt_version': 'synthetic-meaning/1',
            'prompt': 'Retain exact original meaning; unsupported meaning stays a gap.',
            'generation_parameters': {'openai_responses': deepcopy(self.config)},
            'max_output_tokens': 64, 'call_timeout_seconds': 5, 'max_retries': 0}

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def formal_spec(self):
        inputs = {'idea_id': self.idea, 'catalog_id': self.catalog, 'definition_ids': []}
        return {'kind': 'formalization/v1', 'context_id': self.context, 'purpose': 'Independent transport fixture.',
            'allowed_workers': ['formalizer'], 'max_attempts': 1, 'lease_seconds': 30,
            'deadline': 1200, 'dependencies': [], 'research_epoch_id': self.epoch,
            'research_call_profile': deepcopy(self.profile), 'research_inputs': inputs}

    def start(self):
        spec = self.formal_spec()
        job = self.op('enqueue', key='formalize', spec=spec)['id']
        lease = self.broker.call(self.formalizer, 'claim')['lease']
        packet = self.broker.call(self.formalizer, 'auxiliary_input', lease=lease)
        return spec, job, lease, packet

    def reserve(self, token, lease, request, key='call'):
        return self.broker.call(token, 'reserve_research_call', lease=lease, key=key, request=request,
            input_token_bound=12000, output_token_limit=64, cost_bound_units=api.cost_bound(12000, 64))

    def formalize_gap(self):
        spec, job, lease, packet = self.start()
        call = self.reserve(self.formalizer, lease, request_for(spec, packet))
        self.broker.call(self.formalizer, 'finish_research_call', lease=lease, call_id=call['call_id'],
            response={'status': 'completed', 'output': {'status': 'final', 'candidate': None, 'semantic_report': None}},
            usage={'input_tokens': 10, 'output_tokens': 10, 'cost_units': 0})
        record = self.broker.call(self.formalizer, 'record_formalization', lease=lease,
            idea_id=self.idea, catalog_id=self.catalog, candidate=None, semantic_report=None, provider_call_id=call['call_id'])
        self.assertTrue(self.broker.call(self.formalizer, 'submit', lease=lease, artifact_id=record['id'])['accepted'])
        batch = self.op('inspect', job_id=job)['batch_id']
        self.op('release_batch', batch_id=batch, target_epoch=2)
        context = self.op('create_context', role='formalizer', epoch=2,
            artifact_ids=[record['id'], self.idea, self.catalog])['id']
        review = {**spec, 'kind': 'semantic-review/v1', 'context_id': context, 'allowed_workers': ['reviewer'],
            'dependencies': [job], 'research_inputs': {'formalization_id': record['id'], 'definition_ids': []}}
        return review, record['id']

    def assert_exact_wire(self, spec, packet):
        request = request_for(spec, packet)
        before = canonical(request)
        config = request['generation_parameters']['openai_responses']
        wire = api.wire_request(request, config)
        self.assertEqual(request['messages'][1]['content'], canonical(packet))
        self.assertEqual(canonical(restore(decode(wire['input'][1]['content']))), canonical(packet))
        self.assertEqual(canonical(request), before)
        self.assertEqual(wire['input'][0], request['messages'][0])
        legacy_config = {key: value for key, value in config.items() if key != 'source_presentation'}
        legacy_request = deepcopy(request)
        legacy_request['generation_parameters'] = {'openai_responses': legacy_config}
        legacy_wire = api.wire_request(legacy_request, legacy_config)
        self.assertEqual(legacy_wire['input'], legacy_request['messages'])
        expanded_wire = deepcopy(wire)
        expanded_wire['input'][1]['content'] = canonical(restore(decode(wire['input'][1]['content'])))
        self.assertEqual(canonical(expanded_wire), canonical(legacy_wire))

    def test_formalizer_and_reviewer_keep_full_original_packets_and_lossless_wire(self):
        spec = self.formal_spec()
        packet = self.broker._auxiliary_packet_for_spec(spec)
        self.assert_exact_wire(spec, packet)
        spec, target = self.formalize_gap()
        self.op('enqueue', key='actual-independent-review', spec=spec)
        lease = self.broker.call(self.reviewer, 'claim')['lease']
        packet = self.broker.call(self.reviewer, 'auxiliary_input', lease=lease)
        self.assert_exact_wire(spec, packet)
        self.assertEqual(packet['formalization']['id'], target)
        self.assertEqual(packet['formalization']['body']['original_idea']['content']['text'], '  Exact synthetic idea.\n')
        self.assertTrue(self.reserve(self.reviewer, lease, request_for(spec, packet))['dispatch'])

    def test_config_and_wire_whitelist_and_normalized_packet_are_frozen(self):
        spec, _, lease, packet = self.start()
        request = request_for(spec, packet)
        for value in (None, True, {}, [], 'unsupported'):
            with self.subTest(profile=value), self.assertRaises(Invalid):
                api.OpenAIResponsesProvider('absent-key', 'unused-ledger', {**self.config, 'source_presentation': value})
        changes = [
            {'messages': request['messages'][:1]},
            {'messages': list(reversed(request['messages']))},
            {'messages': [*request['messages'], {'role': 'assistant', 'content': '{}'}]},
            {'tools': [{'name': 'unexpected', 'description': 'No tools permitted.', 'parameters': {}}]},
            {'messages': [request['messages'][0], {'role': 'user', 'content': '{"schema":"unrelated/1"}'}]},
            {'messages': [request['messages'][0], {'role': 'user', 'content': 'not JSON'}]}]
        for number, change in enumerate(changes):
            with self.subTest(number=number), self.assertRaises(Invalid):
                api.wire_request({**request, **change}, self.config)
        for number, field in enumerate(('body', 'exposure', 'config')):
            changed = deepcopy(request)
            if field == 'config':
                changed['generation_parameters']['openai_responses'].pop('source_presentation')
            else:
                forged = deepcopy(packet)
                if field == 'body':
                    forged['sources'][0]['body']['tampered'] = 'Not an authorized original source body.'
                else:
                    forged['sources'][0]['exposure'].append('forged-unrelated-identity')
                changed['messages'][1]['content'] = canonical(forged)
            with self.subTest(field=field), self.assertRaises(Invalid):
                self.reserve(self.formalizer, lease, changed, key='tamper-' + str(number))
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage']['calls'], 0)
        call = self.reserve(self.formalizer, lease, request)
        saved = self.op('inspect_research_epoch', epoch_id=self.epoch)['calls'][0]
        self.assertEqual(saved['id'], call['call_id'])
        self.assertEqual(saved['request'], request)

    def test_controller_rejects_route_drift_before_backend_and_retains_full_request(self):
        spec, _, lease, packet = self.start()
        expected = request_for(spec, packet)
        directory = self.broker.directory
        changed_routes = deepcopy(self.routes)
        changed_routes[api.MODEL]['config'].pop('source_presentation')
        self.broker.close()
        self.broker = Broker(directory, clock=lambda: 1000, provider_routes=changed_routes)
        self.addCleanup(self.broker.close)
        with patch('trading_researcher.controller_providers.backend') as backend, \
                patch('trading_researcher.controller_providers._invoke') as invoke:
            with self.assertRaises(Invalid):
                self.broker.call(self.formalizer, 'invoke_auxiliary_provider', lease=lease, key='route-drift')
            backend.assert_not_called()
            invoke.assert_not_called()
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=self.epoch)['usage']['calls'], 0)
        self.broker.close()
        self.broker = Broker(directory, clock=lambda: 1000, provider_routes=self.routes)
        self.addCleanup(self.broker.close)
        captured = {}
        def offline_invoke(adapter, request, *args, **kwargs):
            captured.update(request=deepcopy(request), wire=api.wire_request(request, adapter.config))
            return {'response': {'status': 'completed', 'provider_id': 'explicit-offline-test',
                'wire_request_sha256': digest(captured['wire']),
                'output': {'status': 'final', 'candidate': None, 'semantic_report': None}},
                'usage': {'input_tokens': 10, 'output_tokens': 10, 'cost_units': 0}}
        with patch('trading_researcher.controller_providers._invoke', side_effect=offline_invoke) as invoke:
            result = self.broker.call(self.formalizer, 'invoke_auxiliary_provider', lease=lease, key='owned-offline')
        self.assertEqual(invoke.call_count, 1)
        self.assertEqual(captured['request'], expected)
        self.assertEqual(restore(decode(captured['wire']['input'][1]['content'])), packet)
        self.assertEqual(result['response']['wire_request_sha256'], digest(captured['wire']))
        retained = self.op('inspect_research_epoch', epoch_id=self.epoch)['calls'][0]
        self.assertEqual(retained['request'], expected)
        self.assertFalse((Path(self.temp.name) / 'unused-ledger').exists())

    def test_dictionary_does_not_fetch_or_authorize_out_of_context_reference_bodies(self):
        spec, _, lease, _ = self.start()
        original_lookup = self.broker._artifact
        with patch.object(self.broker, '_artifact', wraps=original_lookup) as lookup:
            packet = self.broker.call(self.formalizer, 'auxiliary_input', lease=lease)
            request = request_for(spec, packet)
        self.assertNotIn(self.hidden, [call.args[0] for call in lookup.call_args_list])
        self.assertEqual(request['messages'][1]['content'], canonical(packet))
        packed = decode(api.wire_request(request, self.config)['input'][1]['content'])
        self.assertIn(self.hidden, packed['reference_dictionary'])
        self.assertNotIn('PRIVATE SOURCE BODY SENTINEL', canonical(packed))
        self.assertEqual(restore(packed), packet)
        with self.assertRaises(Denied):
            self.broker.call(self.formalizer, 'read_artifact', lease=lease, artifact_id=self.hidden)
        self.assertNotIn(self.hidden, self.broker._context(self.context)['artifact_ids'])


if __name__ == '__main__':
    unittest.main()
