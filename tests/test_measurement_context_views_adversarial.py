"""Independent measurement-view retention and failure-order tests; no live API."""
from copy import deepcopy
import json
import time
import unittest
from unittest.mock import patch

import test_context_views_adversarial as fixed
from trading_researcher import context_views, researcher
from trading_researcher.codec import Invalid
from trading_researcher.errors import Conflict, Denied


PROFILE = 'discovery-source-view/2'
ABSENT = object()


def measurement(gap=False):
    value = fixed.artifact()
    value['id'] = '6' * 64
    value['authority'] = 'development_measurement_not_scientific_evidence'
    value['body'] = {
        'schema': 'development-measurement/1', 'delivered': True, 'scientific_readiness': False,
        'call_id': 'fixture-call-0', 'tool_id': 'measure-1',
        'availability': {'basis': 'assumed', 'delay_seconds': 900},
        'remaining_gates': ['AVAILABILITY_UNVERIFIED', 'FEATURE_CERTIFICATION_REQUIRED'],
        'result': {'status': 'MEASUREMENT_GAP' if gap else 'MEASURED_DEVELOPMENT',
                   'scientific_readiness': False, 'classification_permitted': False,
                   'expected_positions': 3, 'processed_positions': 0 if gap else 3,
                   'uncomputed_positions': 3 if gap else 0, 'processing_complete': not gap,
                   'reason': {'code': 'DATA_GAP'} if gap else None,
                   'summary': None if gap else {'defined': 1, 'mean': {'numerator': '10', 'denominator': '1'}},
                   'values': [] if gap else [
                       {'time': 100, 'value': {'numerator': '10', 'denominator': '1'}, 'missing': None},
                       {'time': 1000, 'value': None, 'missing': 'missing_observation'},
                       {'time': 1900, 'value': None, 'missing': 'not_yet_available'}]}}
    return value


def final():
    return {'status': 'final', 'record': {'kind': 'idea', 'content': {'text': 'Unverified fixture idea'},
                                        'scope': {}, 'source_refs': []}}


class LoopClient:
    """Deterministic RPC fixture for delivery ordering, not an authority substitute."""
    timeout = 1

    def __init__(self, presentation=PROFILE, gap=False, deny_measure=False,
                 fail_store=None, reject_second_reservation=False):
        self.source = fixed.artifact()
        self.measurement = measurement(gap)
        self.profile = {'model': 'fixture/1', 'mode': 'fixture', 'prompt_version': 'fixed-view/2',
                        'tools': deepcopy(researcher.CONTEXT_TOOL_DEFINITIONS),
                        'generation_parameters': {}, 'prompts': {'first': 'Explore with explicit gaps'},
                        'max_output_tokens': 4096, 'max_retries': 0}
        if presentation is not ABSENT:
            self.profile['source_presentation'] = presentation
        self.deny_measure, self.fail_store = deny_measure, fail_store
        self.reject_second_reservation = reject_second_reservation
        self.requests, self.stored, self.operations = [], [], []

    def call(self, op, **args):
        self.operations.append((op, deepcopy(args)))
        if op == 'claim':
            return {'lease': {'job_id': 'fixture-job', 'generation': 1},
                    'spec': {'kind': 'research-record/v1', 'allowed_workers': ['first'],
                             'lease_seconds': 30, 'purpose': 'Fixed measurement presentation'},
                    'context': {'artifact_ids': [self.source['id']]}}
        if op == 'research_call_state':
            return {'profile': deepcopy(self.profile), 'calls': []}
        if op == 'read_artifact':
            return deepcopy(self.measurement if args['artifact_id'] == self.measurement['id'] else self.source)
        if op == 'reserve_research_call':
            if self.requests and self.reject_second_reservation:
                raise Conflict('Fixture original budget exhausted')
            self.requests.append(deepcopy(args['request']))
            return {'dispatch': True, 'call_id': 'fixture-call-' + str(len(self.requests)-1),
                    'deadline': int(time.time()) + 30}
        if op == 'finish_research_call':
            return {'response_id': 'response-' + str(len(self.requests)), 'late': False,
                    'within_reservation': True}
        if op == 'measure_development':
            if self.deny_measure:
                raise Denied('Fixture denied or stale original measurement')
            return deepcopy(self.measurement)
        if op == 'put_artifact':
            if args['body']['schema'] == self.fail_store:
                raise Invalid('Fixture retention failure')
            item = {'id': 'stored-' + str(len(self.stored)), 'body': deepcopy(args['body']),
                    'source_refs': deepcopy(args['source_refs'])}
            self.stored.append(item)
            return {'id': item['id']}
        if op == 'search_memory':
            return {'matches': [deepcopy(self.measurement)]}
        if op == 'record_research':
            return {'id': 'final-fixture-idea'}
        if op == 'submit':
            return {'accepted': True, 'state': 'succeeded'}
        if op == 'block':
            return {'state': 'blocked'}
        if op == 'heartbeat':
            return {}
        raise AssertionError('Unexpected fixture RPC: ' + op)


def run(client, calls=None):
    if calls is None:
        calls = [{'id': 'measure-1', 'name': 'measure_development',
                  'arguments': {'snapshot_id': client.source['id']}}]
    replies = [{'status': 'tools', 'calls': calls}, final()]
    def invoke(provider, request, ordinal, seconds, cancelled):
        return {'response': {'status': 'completed', 'provider_id': 'independent-fixture/1',
                             'output': deepcopy(replies[ordinal])},
                'usage': {'input_tokens': 1, 'output_tokens': 1, 'cost_units': 0}}
    with patch.object(researcher, '_invoke', side_effect=invoke) as invoked:
        result = researcher.run_research_once(client, researcher.ScriptedProvider(replies))
    return result, invoked.call_count


def bodies(client, schema):
    return [item for item in client.stored if item['body']['schema'] == schema]


class MeasurementContextViewAdversarialTests(unittest.TestCase):
    def test_v2_keeps_raw_then_derived_view_and_sends_exact_retained_view(self):
        client = LoopClient()
        original = fixed.encoded(client.measurement)
        result, count = run(client)
        self.assertTrue(result['accepted'])
        self.assertEqual(count, 2)
        raw, = bodies(client, 'provider-tool-result/1')
        view, = bodies(client, 'provider-tool-view/1')
        self.assertEqual(fixed.encoded(raw['body']['result']['value']), original)
        self.assertEqual(set(view['body']), {'schema', 'presentation_profile', 'source_tool_result_id', 'model_visible_body'})
        self.assertEqual(view['body']['presentation_profile'], PROFILE)
        self.assertEqual(view['body']['source_tool_result_id'], raw['id'])
        self.assertEqual(view['source_refs'], [raw['id']])
        self.assertLess(client.stored.index(raw), client.stored.index(view))
        visible = view['body']['model_visible_body']
        self.assertEqual({k: v for k, v in visible.items() if k != 'result'},
                         {k: v for k, v in raw['body'].items() if k != 'result'})
        self.assertEqual(visible['result']['value']['schema'], 'discovery-source-view/1')
        self.assertEqual(visible['result']['value']['content']['body'], client.measurement['body'])
        self.assertEqual(visible['result']['value']['artifact_id'], client.measurement['id'])
        expected = deepcopy(client.measurement)
        for path in (('exposure',), ('source_refs',)):
            values = fixed.at(expected, path)
            fixed.put(expected, path, {'schema': 'deferred-source-list/1', 'path': list(path),
                                       'count': len(values), 'sha256': fixed.sha(values), 'tool': 'read_source_section'})
        self.assertEqual(visible['result']['value']['content'], expected)
        tool_message, = [m for m in client.requests[1]['messages'] if m['role'] == 'tool']
        self.assertEqual(tool_message['content'].encode('utf-8'), fixed.encoded(visible))
        self.assertEqual(fixed.encoded(client.measurement), original)
        self.assertIn(raw['id'], result['transcript_ids'])
        self.assertIn(view['id'], result['transcript_ids'])
        initial = json.loads(client.requests[0]['messages'][1]['content'])['sources'][0]
        self.assertEqual(initial['schema'], 'discovery-source-view/1')

    def test_absent_and_v1_profiles_send_the_exact_old_full_measurement_body(self):
        for profile in (ABSENT, 'discovery-source-view/1'):
            with self.subTest(profile=profile):
                client = LoopClient(presentation=profile)
                result, count = run(client)
                self.assertTrue(result['accepted'])
                self.assertEqual(count, 2)
                raw, = bodies(client, 'provider-tool-result/1')
                self.assertEqual(bodies(client, 'provider-tool-view/1'), [])
                tool, = [m for m in client.requests[1]['messages'] if m['role'] == 'tool']
                self.assertEqual(tool['content'].encode('utf-8'), fixed.encoded(raw['body']))
                self.assertEqual(raw['body']['result']['value'], client.measurement)
                initial = json.loads(client.requests[0]['messages'][1]['content'])['sources'][0]
                self.assertEqual(initial, client.source if profile is ABSENT else context_views.source_view(client.source))

    def test_v2_does_not_project_other_tool_results_even_when_they_contain_measurements(self):
        client = LoopClient()
        calls = [{'id': 'full', 'name': 'read_source', 'arguments': {'artifact_id': client.measurement['id']}},
                 {'id': 'page', 'name': 'read_source_section', 'arguments': {'artifact_id': client.measurement['id'],
                             'path': ['exposure'], 'offset': 0, 'limit': 2}},
                 {'id': 'find', 'name': 'search_memory', 'arguments': {'query': 'fixture'}},
                 {'id': 'capabilities', 'name': 'capabilities', 'arguments': {}}]
        result, _ = run(client, calls)
        self.assertTrue(result['accepted'])
        self.assertEqual(bodies(client, 'provider-tool-view/1'), [])
        raw = bodies(client, 'provider-tool-result/1')
        messages = [m for m in client.requests[1]['messages'] if m['role'] == 'tool']
        self.assertEqual(len(raw), 4)
        self.assertEqual([m['content'].encode('utf-8') for m in messages], [fixed.encoded(r['body']) for r in raw])
        self.assertEqual(raw[0]['body']['result']['value'], client.measurement)
        self.assertEqual(raw[2]['body']['result']['value']['matches'][0], client.measurement)

    def test_denied_measurement_stays_a_denial_without_a_view_or_hidden_value(self):
        client = LoopClient(deny_measure=True)
        result, _ = run(client)
        self.assertTrue(result['accepted'])
        self.assertEqual(bodies(client, 'provider-tool-view/1'), [])
        raw, = bodies(client, 'provider-tool-result/1')
        self.assertEqual(raw['body']['result'], {'status': 'tool_denied', 'reason': 'Unavailable or invalid request'})
        self.assertNotIn(client.measurement['id'], json.dumps(client.requests[1]))

    def test_malformed_provider_calls_are_retained_denials_not_unhandled_view_errors(self):
        for call in (None, ['bad'], {'id': 'malformed'},
                     {'id': 'malformed', 'name': 'measure_development'}):
            with self.subTest(call=call):
                client = LoopClient()
                result, count = run(client, [call])
                self.assertTrue(result['accepted'])
                self.assertEqual(count, 2)
                raw, = bodies(client, 'provider-tool-result/1')
                self.assertEqual(raw['body']['tool_request'], call)
                self.assertEqual(raw['body']['result'], {'status': 'tool_denied', 'reason': 'Unavailable or invalid request'})
                self.assertEqual(bodies(client, 'provider-tool-view/1'), [])
                self.assertEqual(sum(op == 'measure_development' for op, _ in client.operations), 0)

    def test_typed_measurement_gap_is_projected_without_losing_reason_or_readiness(self):
        client = LoopClient(gap=True)
        run(client)
        raw, = bodies(client, 'provider-tool-result/1')
        view, = bodies(client, 'provider-tool-view/1')
        visible_body = view['body']['model_visible_body']['result']['value']['content']['body']
        self.assertEqual(visible_body, raw['body']['result']['value']['body'])
        self.assertEqual(visible_body['result']['reason'], {'code': 'DATA_GAP'})
        self.assertEqual(visible_body['result']['uncomputed_positions'], 3)
        self.assertFalse(visible_body['result']['classification_permitted'])
        self.assertFalse(visible_body['scientific_readiness'])

    def test_failed_view_retention_keeps_raw_without_followup_or_repeated_measurement(self):
        client = LoopClient(fail_store='provider-tool-view/1')
        result, invocations = run(client)
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(invocations, 1)
        raw, = bodies(client, 'provider-tool-result/1')
        self.assertEqual(bodies(client, 'provider-tool-view/1'), [])
        self.assertIn(raw['id'], result['transcript_ids'])
        self.assertEqual(sum(op == 'measure_development' for op, _ in client.operations), 1)
        self.assertEqual(len(client.requests), 1)

    def test_failed_raw_retention_never_creates_a_view_or_dispatches_followup(self):
        client = LoopClient(fail_store='provider-tool-result/1')
        result, invocations = run(client)
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(invocations, 1)
        self.assertEqual(client.stored, [])
        self.assertEqual(sum(op == 'put_artifact' for op, _ in client.operations), 1)

    def test_followup_reservation_failure_does_not_reset_or_repeat_the_measurement(self):
        client = LoopClient(reject_second_reservation=True)
        result, invocations = run(client)
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(invocations, 1)
        self.assertEqual(len(bodies(client, 'provider-tool-result/1')), 1)
        self.assertEqual(len(bodies(client, 'provider-tool-view/1')), 1)
        self.assertEqual(sum(op == 'measure_development' for op, _ in client.operations), 1)
        self.assertEqual(sum(op == 'reserve_research_call' for op, _ in client.operations), 2)

    def test_v2_profile_is_supported_immutable_and_requires_exact_section_tool(self):
        fixture = fixed.ContextViewProfileAdversarialTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        self.assertEqual(context_views.PRESENTATION_PROFILES, ('discovery-source-view/1', PROFILE))
        profile = fixture.profile(source_presentation=PROFILE, tools=deepcopy(researcher.CONTEXT_TOOL_DEFINITIONS))
        before = fixed.encoded(profile)
        identity = fixture.create(profile)
        self.assertEqual(fixed.encoded(fixture.broker._epoch(identity)['request']['profile']), before)
        with self.assertRaises(Conflict):
            fixture.create(fixture.profile(source_presentation='discovery-source-view/1',
                                           tools=deepcopy(researcher.CONTEXT_TOOL_DEFINITIONS)))
        tools = deepcopy(researcher.CONTEXT_TOOL_DEFINITIONS)
        tools[-1]['parameters']['properties']['path']['minItems'] = True
        with self.assertRaises(Invalid):
            fixture.create(fixture.profile(source_presentation=PROFILE, tools=tools), key='bad-bool')
        with self.assertRaises(Invalid):
            fixture.create(fixture.profile(source_presentation=PROFILE), key='missing-section')


if __name__ == '__main__':
    unittest.main()
