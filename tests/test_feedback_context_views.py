"""Explicit feedback context profile, retained exact pages and unchanged budgets."""
from copy import deepcopy
import unittest
from unittest.mock import patch

import test_researcher as support
import test_measurement_context_views_adversarial as measurement_support
from trading_researcher.codec import canonical, decode
from trading_researcher import context_views as views
from trading_researcher import researcher


def feedback_artifact(identity):
    refs = [format(i, '064x') for i in range(32)]
    return {'id': identity, 'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'data_class': 'development',
            'authority': 'descriptive_development_feedback_only', 'source_refs': refs,
            'exposure': refs, 'body': {'schema': 'development-feedback-manifest/1',
                'cohort': {'artifact_ids': refs, 'jobs': [{'state': 'blocked', 'reason': 'Retained original failure'}]},
                'retained_research_records': [{'id': 'idea', 'source_refs': refs, 'exposure': refs,
                    'body': {'kind': 'idea', 'content': {'text': 'Exact original idea; scientifically untested.'}}}],
                'scientific_readiness': False, 'qualification': 'Descriptive only; exposed history.'}}


class FeedbackContextLoopTests(unittest.TestCase):
    setUp = support.ResearcherTests.setUp
    tearDown = support.ResearcherTests.tearDown
    setup_epoch = support.ResearcherTests.setup_epoch
    calls = support.ResearcherTests.calls

    def test_profile_transmits_exact_feedback_body_pages_and_complete_private_transcript(self):
        self.setup_epoch(source_presentation=views.FEEDBACK_VIEW_PROFILE,
                         tools=researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS)
        # Only the owned envelope is supplied by this fixture. Real publication
        # authority/freshness is exercised separately on the retained registry.
        original = feedback_artifact(self.source)
        call = self.clients['first'].call
        def read_override(op, **kwargs):
            if op == 'read_artifact' and kwargs['artifact_id'] == self.source:
                call(op, **kwargs)  # Authenticate before returning fixture data.
                return deepcopy(original)
            return call(op, **kwargs)
        page_call = {'id': 'page', 'name': 'read_feedback_references', 'arguments': {
            'artifact_id': self.source, 'path': ['body', 'retained_research_records', '0', 'exposure'],
            'offset': 3, 'limit': 4}}
        with patch.object(self.clients['first'], 'call', side_effect=read_override):
            result = researcher.run_research_once(self.clients['first'], researcher.ScriptedProvider([
                {'status': 'tools', 'calls': [page_call]}, support.final()]))
        self.assertTrue(result['accepted'], result)
        calls = self.calls()
        initial = decode(calls[0]['request']['messages'][1]['content'])['sources'][0]
        self.assertEqual(initial['schema'], 'discovery-source-view/3')
        self.assertEqual(initial['content']['body']['cohort']['jobs'], original['body']['cohort']['jobs'])
        record = initial['content']['body']['retained_research_records'][0]
        self.assertEqual(record['body'], original['body']['retained_research_records'][0]['body'])
        self.assertEqual(record['exposure']['count'], 32)
        tool = decode(next(m['content'] for m in calls[1]['request']['messages'] if m['role'] == 'tool'))
        self.assertEqual(tool['result']['value']['values'], original['exposure'][3:7])
        stored = [self.admin.call('get_artifact', artifact_id=i)['body'] for i in result['transcript_ids']]
        self.assertIn(tool, stored)
        self.assertEqual(self.admin.call('verify')['status'], 'PASS')

    def test_new_page_does_not_reset_call_budget(self):
        self.setup_epoch(source_presentation=views.FEEDBACK_VIEW_PROFILE,
                         tools=researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS, max_calls=1)
        result = researcher.run_research_once(self.clients['first'], researcher.ScriptedProvider([
            {'status': 'tools', 'calls': [{'id': 'page', 'name': 'read_feedback_references', 'arguments': {
                'artifact_id': self.source, 'path': ['body', 'cohort', 'artifact_ids'], 'offset': 0, 'limit': 1}}]},
            support.final()]))
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(result['record_ids'], [])


class FeedbackMeasurementTests(unittest.TestCase):
    def test_new_profile_preserves_measurement_body_and_sends_only_retained_view(self):
        client = measurement_support.LoopClient(presentation=views.FEEDBACK_VIEW_PROFILE)
        client.profile['tools'] = deepcopy(researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS)
        result, invocations = measurement_support.run(client)
        self.assertTrue(result['accepted'])
        self.assertEqual(invocations, 2)
        raw, = measurement_support.bodies(client, 'provider-tool-result/1')
        view, = measurement_support.bodies(client, 'provider-tool-view/1')
        self.assertEqual(raw['body']['result']['value'], client.measurement)
        self.assertEqual(view['body']['presentation_profile'], views.FEEDBACK_VIEW_PROFILE)
        self.assertEqual(view['body']['source_tool_result_id'], raw['id'])
        visible = view['body']['model_visible_body']
        self.assertEqual(visible['result']['value']['content']['body'], client.measurement['body'])
        message, = [m for m in client.requests[1]['messages'] if m['role'] == 'tool']
        self.assertEqual(message['content'], canonical(visible))

    def test_failed_retention_does_not_send_unrecorded_view_or_repeat_measurement(self):
        client = measurement_support.LoopClient(presentation=views.FEEDBACK_VIEW_PROFILE,
                                                fail_store='provider-tool-view/1')
        client.profile['tools'] = deepcopy(researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS)
        result, invocations = measurement_support.run(client)
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(invocations, 1)
        self.assertEqual(sum(op == 'measure_development' for op, _ in client.operations), 1)


if __name__ == '__main__':
    unittest.main()
