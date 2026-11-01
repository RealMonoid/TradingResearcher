"""Independent exact feedback-reference paging checks; no live calls or data."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from trading_researcher import context_views as api, researcher
from trading_researcher.codec import Invalid
from trading_researcher.errors import Conflict, Denied
import test_context_views_adversarial as fixed
import test_measurement_context_views_adversarial as measurement


PROFILE = 'discovery-source-view/3'
TOOL = 'read_feedback_references'
PATHS = (('body', 'cohort', 'artifact_ids'),
         ('body', 'retained_research_records', '0', 'source_refs'),
         ('body', 'retained_research_records', '0', 'exposure'),
         ('body', 'retained_research_records', '1', 'source_refs'),
         ('body', 'retained_research_records', '1', 'exposure'))
LEGACY_QUALIFICATION = (
    'Content is a projection, not the hash-identical original envelope. '
    'Deferred lists are unread evidence, not empty or irrelevant evidence. '
    'Read required entries with read_source_section; preserve gaps if budgets prevent access. '
    'Original source and inherited exposure remain retained; referenced IDs grant no additional access.')


def at(value, path):
    for key in path:
        value = value[int(key)] if type(value) is list else value[key]
    return value


def put(value, path, replacement):
    parent = at(value, path[:-1])
    parent[int(path[-1]) if type(parent) is list else path[-1]] = replacement


def manifest():
    refs = ['z-' + str(i).zfill(3) + '-' + 'x' * 64 for i in range(18)]
    refs[8] = refs[3]  # Recovery must preserve order and duplicates.
    source = {'id': '7' * 64, 'version': 'local-artifact/1', 'creator': 'controller',
        'origin': 'controller', 'data_class': 'development',
        'authority': 'descriptive_development_feedback_only', 'source_refs': list(refs), 'exposure': list(refs),
        'body': {'schema': 'development-feedback-manifest/1', 'created_at': 2701,
            'scientific_readiness': False, 'qualification': 'Historical descriptive feedback. No calibrated result.',
            'request': {'root_epoch_id': 'root', 'execution_id': 'execution', 'target_epoch': 7},
            'cohort': {'artifact_ids': list(refs), 'idea_ids': ['original-idea'],
                'jobs': [{'id': 'failed-attempt', 'state': 'blocked', 'reason': 'Unsupported exact original meaning'}],
                'calls': [{'state': 'recorded', 'charged_tokens': 33}],
                'unresolved_exposure_refs': ['opaque:unresolved']},
            'retained_research_records': []}}
    for index, kind in enumerate(('idea', 'gap')):
        source['body']['retained_research_records'].append({'id': str(index) * 64,
            'creator': 'original-author', 'authority': 'unverified_research_assertion',
            'body': {'schema': 'research-record/1', 'kind': kind,
                'content': {'text': 'Keep the original text exactly; ' + 'meaning ' * 200,
                    'reason': 'Missing input must remain a gap', 'reopen_condition': 'No silent substitution'},
                'scope': {'instrument': 'ETHUSDT'}, 'relations': {'depends_on': list(refs)},
                'created_at': 1000, 'available_at': 1000},
            'source_refs': list(refs), 'exposure': list(reversed(refs))})
    return source


def marker(values, path, tool):
    return {'schema': 'deferred-source-list/1', 'path': list(path), 'count': len(values),
        'sha256': fixed.sha(values), 'tool': tool}


def legacy_expected(source):
    projected = deepcopy(source)
    for path in fixed.PATHS:
        try:
            values = at(source, path)
        except (KeyError, TypeError):
            continue
        if type(values) is list and len(fixed.encoded(values)) >= 1024:
            put(projected, path, marker(values, path, 'read_source_section'))
    return {'schema': 'discovery-source-view/1', 'artifact_id': source['id'],
        'content': projected, 'qualification': LEGACY_QUALIFICATION}


def tools():
    return researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS


def call(**changes):
    return {'id': 'feedback-page', 'name': TOOL, 'arguments': {
        'artifact_id': '7' * 64, 'path': list(PATHS[0]), 'offset': 0, 'limit': 2, **changes}}


class FeedbackViewPureAdversarialTests(unittest.TestCase):
    def test_profile_tool_contract_and_legacy_inventory_are_explicit(self):
        self.assertEqual(api.FEEDBACK_VIEW_PROFILE, PROFILE)
        tool = api.FEEDBACK_SECTION_TOOL
        self.assertEqual(tool['name'], TOOL)
        properties = tool['parameters']['properties']
        self.assertEqual(properties['path'], {'type': 'array', 'items': {'type': 'string'}, 'minItems': 3, 'maxItems': 4})
        self.assertEqual(properties['limit'], {'type': 'integer', 'minimum': 1, 'maximum': 64})
        self.assertEqual(tool['parameters']['required'], ['artifact_id', 'path', 'offset', 'limit'])
        self.assertIs(tool['parameters']['additionalProperties'], False)
        self.assertEqual(tools(), [*researcher.CONTEXT_TOOL_DEFINITIONS, tool])
        self.assertNotIn(TOOL, [value['name'] for value in researcher.CONTEXT_TOOL_DEFINITIONS])

    def test_only_exact_reference_arrays_change_and_all_research_meaning_survives(self):
        source = manifest()
        original = fixed.encoded(source)
        expected = legacy_expected(source)['content']
        for path in PATHS:
            put(expected, path, marker(at(source, path), path, TOOL))
        actual = api.source_view(source, profile=PROFILE)
        self.assertEqual(actual['schema'], PROFILE)
        self.assertEqual(actual['artifact_id'], source['id'])
        self.assertEqual(actual['content'], expected)
        self.assertIn('unread', actual['qualification'].lower())
        self.assertEqual(fixed.encoded(source), original)
        for path in PATHS:
            values = at(source, path)
            pages = [api.feedback_source_section(source, list(path), offset, 7) for offset in (0, 7, 14)]
            self.assertEqual(sum([page['values'] for page in pages], []), values)
            self.assertEqual({page['list_sha256'] for page in pages}, {fixed.sha(values)})
            self.assertEqual([page['next_offset'] for page in pages], [7, 14, None])

    def test_default_and_explicit_legacy_profiles_are_byte_identical(self):
        for source in (manifest(), fixed.artifact()):
            expected = fixed.encoded(legacy_expected(source))
            self.assertEqual(fixed.encoded(api.source_view(source)), expected)
            for profile in ('discovery-source-view/1', 'discovery-source-view/2'):
                with self.subTest(profile=profile):
                    self.assertEqual(fixed.encoded(api.source_view(source, profile=profile)), expected)

    def test_threshold_is_inclusive_canonical_utf8_and_small_arrays_stay_visible(self):
        for path in PATHS:
            for values, size in ((['x' * 1019], 1023), (['x' * 1020], 1024), (['é' * 510], 1024), ([], 2)):
                with self.subTest(path=path, bytes=size):
                    source = manifest()
                    put(source, path, values)
                    self.assertEqual(len(fixed.encoded(values)), size)
                    actual = at(api.source_view(source, profile=PROFILE)['content'], path)
                    self.assertEqual(actual, marker(values, path, TOOL) if size >= 1024 else values)

    def test_schema_owner_authority_version_or_data_class_spoof_cannot_defer_or_page(self):
        mutations = [(key, value) for key, value in (
            ('version', 'local-artifact/2'), ('creator', 'untrusted-worker'), ('origin', 'source'),
            ('data_class', 'assessment'), ('data_class', 'work_product'), ('authority', 'supplied_source_not_certified'))]
        mutations += [('body_schema', value) for value in ('development-feedback-manifest/2', 'research-record/1', None)]
        for key, value in mutations:
            with self.subTest(key=key, value=value):
                source = manifest()
                if key == 'body_schema':
                    source['body']['schema'] = value
                else:
                    source[key] = value
                actual = api.source_view(source, profile=PROFILE)
                self.assertEqual(actual['content'], legacy_expected(source)['content'])
                with self.assertRaises(Invalid):
                    api.feedback_source_section(source, list(PATHS[0]), 0, 1)

    def test_nonstring_reference_lists_never_hide_values_and_section_fails_closed(self):
        for path in PATHS:
            for values in (None, {'0': 'not-a-list'}, ['x' * 1100, 1], ['x' * 1100, False],
                           ['x' * 1100, None], ['x' * 1100, ['nested']], ['x' * 1100, {'ref': 'nested'}]):
                with self.subTest(path=path, values=type(values).__name__):
                    source = manifest()
                    put(source, path, values)
                    actual = api.source_view(source, profile=PROFILE)
                    self.assertEqual(at(actual['content'], path), values)
                    with self.assertRaises(Invalid):
                        api.feedback_source_section(source, list(path), 0, 1)

    def test_paths_are_exact_and_array_indices_are_canonical_bounded_decimals(self):
        source = manifest()
        invalid = [None, 'body.cohort.artifact_ids', (), [], ['exposure'], ['body', 'cohort', 'jobs'],
            ['body', 'retained_research_records', '0', 'body'], ['body', 'cohort', 'artifact_ids', '0'],
            ['body', 'retained_research_records', 0, 'exposure'], ['body', 'retained_research_records', True, 'exposure'],
            ['body', 'retained_research_records', {}, 'exposure'], ['body', 'retained_research_records', ['0'], 'exposure'],
            ['body', 'retained_research_records', '0', 'body', 'source_refs'], ['__class__'], ['..', 'body']]
        invalid += [['body', 'retained_research_records', index, 'exposure'] for index in
            ('-1', '+0', '00', '01', '0.0', ' 0', '0 ', '٠', '2', '9' * 5000)]
        for path in invalid:
            with self.subTest(path=str(path)[:100]), self.assertRaises(Invalid):
                api.feedback_source_section(source, path, 0, 1)
        # A valid two-digit index must address that record, never a dictionary key.
        source['body']['retained_research_records'] *= 6
        page = api.feedback_source_section(source, ['body', 'retained_research_records', '10', 'source_refs'], 0, 1)
        self.assertEqual(page['values'], source['body']['retained_research_records'][10]['source_refs'][:1])

    def test_pages_preserve_exact_duplicates_end_offsets_and_64_item_bound(self):
        source = manifest()
        values = ['second', 'first', 'first', 'last'] * 32 + ['tail', 'tail']
        put(source, PATHS[0], values)
        pages = [api.feedback_source_section(source, list(PATHS[0]), offset, 64) for offset in (0, 64, 128, 130)]
        self.assertEqual([len(page['values']) for page in pages], [64, 64, 2, 0])
        for offset, page in zip((0, 64, 128, 130), pages):
            end = min(offset + 64, len(values))
            self.assertEqual(page, {'schema': 'source-section/1', 'artifact_id': source['id'], 'path': list(PATHS[0]),
                'list_sha256': fixed.sha(values), 'count': len(values), 'offset': offset,
                'next_offset': end if end < len(values) else None, 'values': values[offset:end]})
        self.assertEqual(sum([page['values'] for page in pages], []), values)
        for offset, limit in ((True, 1), (False, 1), (-1, 1), (131, 1), ('0', 1), (0.0, 1),
                              (0, True), (0, False), (0, 0), (0, 65), (0, '1'), (0, None), (None, 1)):
            with self.subTest(offset=offset, limit=limit), self.assertRaises(Invalid):
                api.feedback_source_section(source, list(PATHS[0]), offset, limit)

    def test_page_byte_bound_never_truncates_and_outputs_do_not_alias_sources(self):
        source = manifest()
        put(source, PATHS[0], ['é' * 7900])
        before = fixed.encoded(source)
        page = api.feedback_source_section(source, list(PATHS[0]), 0, 1)
        self.assertLessEqual(len(fixed.encoded(page)), 16384)
        self.assertEqual(page['values'], at(source, PATHS[0]))
        page['values'].append('caller mutation')
        page['path'].append('caller mutation')
        view = api.source_view(source, profile=PROFILE)
        view['content']['body']['retained_research_records'][0]['body']['content']['text'] = 'caller mutation'
        self.assertEqual(fixed.encoded(source), before)
        for values in (['x' * 16384], ['é' * 8200], ['x' * 500] * 64):
            put(source, PATHS[0], values)
            with self.subTest(size=len(fixed.encoded(values))), self.assertRaises(Invalid):
                api.feedback_source_section(source, list(PATHS[0]), 0, 64)


class FeedbackViewAccessAdversarialTests(unittest.TestCase):
    def test_authorization_precedes_path_offset_and_schema_inspection(self):
        for changes in ({}, {'path': [['hostile']], 'offset': True, 'limit': -1}):
            client = fixed.RecordingClient(source=None, denied=True)
            with self.subTest(changes=changes), self.assertRaises(Denied):
                researcher._tool(client, {'lease': 'fixed'}, call(**changes), tools=tools())
            self.assertEqual(client.calls, [('read_artifact', {'lease': {'lease': 'fixed'}, 'artifact_id': '7' * 64})])

    def test_exact_authorized_page_performs_one_read_and_never_follows_ids(self):
        source = manifest()
        client = fixed.RecordingClient(source)
        result = researcher._tool(client, {}, call(), tools=tools())
        self.assertEqual(result['values'], source['body']['cohort']['artifact_ids'][:2])
        self.assertEqual(client.calls, [('read_artifact', {'lease': {}, 'artifact_id': source['id']})])
        self.assertEqual(result['list_sha256'], fixed.sha(source['body']['cohort']['artifact_ids']))

    def test_old_tool_inventories_deny_before_read_and_full_read_remains_full(self):
        for inventory in (None, researcher.TOOL_DEFINITIONS, researcher.DEVELOPMENT_TOOL_DEFINITIONS,
                          researcher.CONTEXT_TOOL_DEFINITIONS):
            client = fixed.RecordingClient(manifest())
            with self.subTest(inventory=None if inventory is None else len(inventory)), self.assertRaises(Denied):
                researcher._tool(client, {}, call(), tools=inventory)
            self.assertEqual(client.calls, [])
        source = manifest()
        actual = researcher._tool(fixed.RecordingClient(source), {},
            {'id': 'full', 'name': 'read_source', 'arguments': {'artifact_id': source['id']}}, tools=tools())
        self.assertEqual(fixed.encoded(actual), fixed.encoded(source))


class FeedbackViewProfileAdversarialTests(unittest.TestCase):
    def fixture(self):
        fixture = fixed.ContextViewProfileAdversarialTests()
        self.addCleanup(fixture.doCleanups)
        fixture.setUp()
        return fixture

    def test_v3_profile_and_both_exact_tool_definitions_are_frozen(self):
        fixture = self.fixture()
        profile = fixture.profile(source_presentation=PROFILE, tools=deepcopy(tools()))
        before = fixed.encoded(profile)
        identity = fixture.create(profile)
        profile['tools'][-1]['description'] = 'Changed after freezing'
        self.assertEqual(fixed.encoded(fixture.broker._epoch(identity)['request']['profile']), before)
        with self.assertRaises(Conflict):
            fixture.create(fixture.profile(source_presentation='discovery-source-view/2', tools=researcher.CONTEXT_TOOL_DEFINITIONS))
        for name in ('read_source_section', TOOL):
            missing = [deepcopy(tool) for tool in tools() if tool['name'] != name]
            with self.subTest(missing=name), self.assertRaises(Invalid):
                fixture.create(fixture.profile(source_presentation=PROFILE, tools=missing), key='missing-' + name)
            modified = deepcopy(tools())
            next(tool for tool in modified if tool['name'] == name)['parameters']['properties']['path']['minItems'] = True
            with self.subTest(altered=name), self.assertRaises(Invalid):
                fixture.create(fixture.profile(source_presentation=PROFILE, tools=modified), key='changed-' + name)

    def test_absent_or_legacy_profile_cannot_gain_feedback_tool(self):
        fixture = self.fixture()
        for profile in ({}, {'source_presentation': 'discovery-source-view/1'},
                        {'source_presentation': 'discovery-source-view/2'}):
            with self.subTest(profile=profile), self.assertRaises(Invalid):
                fixture.create(fixture.profile(tools=deepcopy(tools()), **profile), key='old-' + str(profile))
        for bad in (None, True, 3, [], {}, '', 'discovery-source-view/999'):
            with self.subTest(profile=bad), self.assertRaises(Invalid):
                fixture.create(fixture.profile(source_presentation=bad, tools=deepcopy(tools())), key='bad-' + str(bad))

    def test_v3_keeps_measurement_raw_then_view_retention_and_exact_profile(self):
        client = measurement.LoopClient(presentation=PROFILE)
        client.profile['tools'] = deepcopy(tools())
        client.source = manifest()
        original = fixed.encoded(client.measurement)
        result, calls = measurement.run(client)
        self.assertTrue(result['accepted'])
        self.assertEqual(calls, 2)
        raw, = measurement.bodies(client, 'provider-tool-result/1')
        view, = measurement.bodies(client, 'provider-tool-view/1')
        self.assertEqual(fixed.encoded(raw['body']['result']['value']), original)
        self.assertEqual(view['body']['presentation_profile'], PROFILE)
        self.assertEqual(view['source_refs'], [raw['id']])
        self.assertLess(client.stored.index(raw), client.stored.index(view))
        visible = view['body']['model_visible_body']
        self.assertEqual(visible['result']['value']['content']['body'], client.measurement['body'])
        self.assertEqual(visible['result']['value']['schema'], PROFILE)
        followup, = [message for message in client.requests[1]['messages'] if message['role'] == 'tool']
        self.assertEqual(followup['content'].encode(), fixed.encoded(visible))
        initial = json.loads(client.requests[0]['messages'][1]['content'])['sources'][0]
        self.assertEqual(initial['schema'], PROFILE)
        self.assertEqual(initial['content']['body']['cohort']['artifact_ids']['tool'], TOOL)


if __name__ == '__main__':
    unittest.main()
