"""Retained source views in the actual research loop, with no paid API calls."""
import unittest

import test_researcher as support
from trading_researcher.codec import canonical, decode, digest
from trading_researcher.context_views import VIEW_VERSION
from trading_researcher.researcher import CONTEXT_TOOL_DEFINITIONS, ScriptedProvider, run_research_once


class ContextLoopTests(unittest.TestCase):
    setUp = support.ResearcherTests.setUp
    tearDown = support.ResearcherTests.tearDown
    setup_epoch = support.ResearcherTests.setup_epoch
    calls = support.ResearcherTests.calls

    def large_source(self):
        refs = [self.admin.call('add_research', kind='source', content={
            'text': 'Uncertified source ' + str(i), 'uri': 'fixture:source/' + str(i)},
            scope={}, source_refs=[])['id'] for i in range(18)]
        self.source = self.admin.call('add_research', kind='source', content={
            'text': 'Availability unknown. No scientific authority.', 'uri': 'fixture:combined'},
            scope={'instrument': 'BTCUSDT', 'resolution_seconds': '900'}, source_refs=refs)['id']
        self.context = self.admin.call('create_context', role='discovery', epoch=1,
                                      artifact_ids=[self.source])['id']
        return self.admin.call('get_artifact', artifact_id=self.source), refs

    def test_views_sections_denials_and_original_exposure_survive_the_real_loop(self):
        original, refs = self.large_source()
        self.setup_epoch(tools=CONTEXT_TOOL_DEFINITIONS, source_presentation=VIEW_VERSION)
        calls = {'status': 'tools', 'calls': [
            {'id': 'page', 'name': 'read_source_section', 'arguments': {
                'artifact_id': self.source, 'path': ['source_refs'], 'offset': 3, 'limit': 5}},
            {'id': 'reference-is-not-permission', 'name': 'read_source_section', 'arguments': {
                'artifact_id': refs[0], 'path': ['source_refs'], 'offset': 0, 'limit': 1}}]}
        first = run_research_once(self.clients['first'], ScriptedProvider([
            calls, support.final('Private partial-access hypothesis; no evidence')]))
        second = run_research_once(self.clients['second'], ScriptedProvider([support.final()]))
        self.assertTrue(first['accepted'] and second['accepted'])
        kept = self.calls()
        view = decode(kept[0]['request']['messages'][1]['content'])['sources'][0]
        self.assertEqual(view['schema'], VIEW_VERSION)
        self.assertEqual(view['content']['source_refs']['count'], 18)
        self.assertEqual(view['content']['body'], original['body'])
        second_input = canonical(kept[2]['request'])
        self.assertNotIn('Private partial-access hypothesis', second_input)
        self.assertNotIn('reference-is-not-permission', second_input)
        bodies = [self.admin.call('get_artifact', artifact_id=i)['body'] for i in first['transcript_ids']]
        pages = [body for body in bodies if body.get('schema') == 'provider-tool-result/1']
        self.assertEqual(pages[0]['result']['value']['values'], original['source_refs'][3:8])
        self.assertEqual(pages[0]['result']['value']['list_sha256'], digest(original['source_refs']))
        self.assertEqual(pages[1]['result'], {'status': 'tool_denied', 'reason': 'Unavailable or invalid request'})
        for identity in first['transcript_ids'] + first['record_ids']:
            artifact = self.admin.call('get_artifact', artifact_id=identity)
            self.assertTrue(set(original['exposure']) <= set(artifact['exposure']))
        self.assertEqual(self.admin.call('get_artifact', artifact_id=self.source), original)
        self.assertEqual(self.admin.call('verify')['status'], 'PASS')

    def test_original_profile_still_sends_the_exact_full_source(self):
        original, _ = self.large_source()
        self.setup_epoch()
        result = run_research_once(self.clients['first'], ScriptedProvider([support.final()]))
        self.assertTrue(result['accepted'])
        message = self.calls()[0]['request']['messages'][1]
        self.assertEqual(message, {'role': 'user', 'content': canonical({
            'purpose': 'Free inquiry', 'sources': [original]})})

    def test_a_section_does_not_reset_the_call_budget(self):
        self.large_source()
        self.setup_epoch(tools=CONTEXT_TOOL_DEFINITIONS, source_presentation=VIEW_VERSION, max_calls=1)
        result = run_research_once(self.clients['first'], ScriptedProvider([
            {'status': 'tools', 'calls': [{'id': 'page', 'name': 'read_source_section', 'arguments': {
                'artifact_id': self.source, 'path': ['exposure'], 'offset': 0, 'limit': 1}}]},
            support.final()]))
        self.assertEqual(result['state'], 'blocked')
        self.assertEqual(len(self.calls()), 1)
        self.assertGreaterEqual(len(result['transcript_ids']), 2)
        self.assertEqual(result['record_ids'], [])


if __name__ == '__main__':
    unittest.main()
