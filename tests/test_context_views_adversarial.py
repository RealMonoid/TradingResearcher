"""Independent fixed source-presentation oracles; no provider or credential access."""
from copy import deepcopy
import hashlib
import json
import tempfile
import unittest

from trading_researcher import context_views as api
from trading_researcher import researcher
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied


VERSION = 'discovery-source-view/1'
PATHS = (('exposure',), ('source_refs',),
         ('body', 'manifest', 'provenance', 'checksum_evidence_refs'),
         ('body', 'manifest', 'provenance', 'raw_source_refs'),
         ('body', 'manifest', 'provenance', 'source_uris'))


def encoded(value):
    # Independent canonical-byte/hash oracle, not the implementation's helpers.
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def at(obj, path):
    for key in path:
        obj = obj[key]
    return obj


def put(obj, path, value):
    at(obj, path[:-1])[path[-1]] = value


def artifact():
    value = {'id': '5' * 64, 'version': 'local-artifact/1', 'creator': 'controller',
             'origin': 'source', 'data_class': 'development',
             'authority': 'data_structure_not_scientific_acceptance',
             'exposure': [], 'source_refs': [], 'blob_refs': ['b' * 64],
             'body': {'schema': 'data-snapshot/1', 'scientific_readiness': False,
                      'remaining_gates': ['AVAILABILITY_UNVERIFIED', 'FEATURE_CERTIFICATION_REQUIRED'],
                      'coverage': {'expected_rows': 12, 'observed_rows': 9, 'missing_rows': 3},
                      'manifest': {'universe': {'instruments': ['BTCUSDT', 'ETHUSDT'],
                                              'start': '2020-01-01', 'end': '2024-01-01'},
                                   'grid_seconds': 900,
                                   'availability': {'basis': 'assumed', 'delay_seconds': 900},
                                   'rights': {'qualification': 'Personal research only'},
                                   'transformation': {'qualification': 'Missing rows remain missing'},
                                   'provenance': {'provider': 'fixture', 'revision': 'fixed/1'}}}}
    for index, path in enumerate(PATHS):
        put(value, path, [str(index) + '-' + str(i).zfill(2) + '-' + 'x' * 64 for i in range(18)])
    return value


class ContextViewPureAdversarialTests(unittest.TestCase):
    def test_version_and_exact_five_path_allowlist(self):
        self.assertEqual(api.VIEW_VERSION, VERSION)
        self.assertEqual(api.DEFER_PATHS, PATHS)

    def test_only_declared_large_arrays_change_and_all_qualifications_survive(self):
        original = artifact()
        before = encoded(original)
        expected = deepcopy(original)
        for path in PATHS:
            values = at(original, path)
            self.assertGreaterEqual(len(encoded(values)), 1024)
            put(expected, path, {'schema': 'deferred-source-list/1', 'path': list(path),
                                 'count': 18, 'sha256': sha(values), 'tool': 'read_source_section'})
        view = api.source_view(original)
        self.assertEqual(set(view), {'schema', 'artifact_id', 'content', 'qualification'})
        self.assertEqual(view['schema'], VERSION)
        self.assertEqual(view['artifact_id'], '5' * 64)
        self.assertEqual(view['content'], expected)
        self.assertIn('projection', view['qualification'].lower())
        self.assertEqual(encoded(original), before)

    def test_threshold_uses_canonical_utf8_bytes_and_is_inclusive(self):
        for values, size, deferred in [(['x' * 1019], 1023, False),
                                       (['x' * 1020], 1024, True),
                                       (['\u00e9' * 510], 1024, True)]:
            with self.subTest(size=size, unicode=values[0][0] == '\u00e9'):
                source = artifact()
                source['exposure'] = values
                self.assertEqual(len(encoded(values)), size)
                actual = api.source_view(source)['content']['exposure']
                if deferred:
                    self.assertEqual(actual['sha256'], sha(values))
                    self.assertEqual(actual['count'], 1)
                else:
                    self.assertEqual(actual, values)

    def test_small_lists_and_same_named_unapproved_paths_remain_exact(self):
        source = artifact()
        source['exposure'] = []
        source['source_refs'] = ['r2', 'r1', 'r1', 'r0']
        source['body']['source_refs'] = ['never-drop-' + 'y' * 80] * 20
        source['body']['manifest']['provenance']['other_refs'] = ['keep-' + 'z' * 80] * 20
        result = api.source_view(source)['content']
        for path in [('exposure',), ('source_refs',), ('body', 'source_refs'),
                     ('body', 'manifest', 'provenance', 'other_refs')]:
            self.assertEqual(at(result, path), at(source, path))

    def test_missing_paths_and_nonlists_are_not_silently_rewritten(self):
        source = artifact()
        del source['body']['manifest']['provenance']['source_uris']
        source['source_refs'] = {'unexpected': ['retain-this']}
        result = api.source_view(source)['content']
        self.assertNotIn('source_uris', result['body']['manifest']['provenance'])
        self.assertEqual(result['source_refs'], source['source_refs'])

    def test_view_output_is_detached_from_all_input_subtrees(self):
        source = artifact()
        source['source_refs'] = [{'small': ['unchanged']}]
        before = encoded(source)
        result = api.source_view(source)
        result['content']['body']['manifest']['universe']['instruments'].append('NEW')
        result['content']['source_refs'][0]['small'].append('mutation')
        result['content']['exposure']['path'].append('mutation')
        self.assertEqual(encoded(source), before)

    def test_exact_order_duplicates_and_section_metadata_at_all_five_paths(self):
        source = artifact()
        values = ['r2', 'r1', 'r1', 'r0']
        for path in PATHS:
            put(source, path, deepcopy(values))
            first = api.source_section(source, list(path), 0, 2)
            second = api.source_section(source, list(path), 2, 2)
            base = {'schema': 'source-section/1', 'artifact_id': source['id'],
                    'path': list(path), 'list_sha256': sha(values), 'count': 4}
            self.assertEqual(first, {**base, 'offset': 0, 'next_offset': 2, 'values': ['r2', 'r1']})
            self.assertEqual(second, {**base, 'offset': 2, 'next_offset': None, 'values': ['r1', 'r0']})
            self.assertEqual(sha(first['values'] + second['values']), sha(values))

    def test_64_item_pages_reconstruct_full_ordered_array(self):
        source = artifact()
        source['exposure'] = ['r2', 'r1', 'r1', 'r0'] * 32 + ['tail', 'tail']
        pages = [api.source_section(source, ['exposure'], offset, 64) for offset in (0, 64, 128)]
        self.assertEqual([len(p['values']) for p in pages], [64, 64, 2])
        self.assertEqual([p['next_offset'] for p in pages], [64, 128, None])
        reconstructed = sum([p['values'] for p in pages], [])
        self.assertEqual(reconstructed, source['exposure'])
        self.assertEqual({p['list_sha256'] for p in pages}, {sha(reconstructed)})

    def test_empty_list_and_end_offset_have_explicit_empty_final_page(self):
        source = artifact()
        for values in ([], ['one']):
            source['exposure'] = values
            page = api.source_section(source, ['exposure'], len(values), 64)
            self.assertEqual(page['values'], [])
            self.assertIsNone(page['next_offset'])
            self.assertEqual(page['count'], len(values))
            self.assertEqual(page['list_sha256'], sha(values))

    def test_malformed_offsets_and_limits_raise_typed_invalid(self):
        source = artifact()
        for offset in (True, False, -1, 19, 0.0, '0', None, [], {}):
            with self.subTest(offset=offset), self.assertRaises(Invalid):
                api.source_section(source, ['exposure'], offset, 1)
        for limit in (True, False, 0, -1, 65, 1.0, '1', None, [], {}):
            with self.subTest(limit=limit), self.assertRaises(Invalid):
                api.source_section(source, ['exposure'], 0, limit)

    def test_paths_are_an_exact_typed_allowlist_not_generic_object_access(self):
        source = artifact()
        for path in ('exposure', ('exposure',), [], ['id'], ['body', 'coverage'],
                     ['exposure', 0], [True], [None], [['exposure']], [{'key': 'exposure'}],
                     ['__class__'], ['..', 'exposure'], ['https://example.invalid/a']):
            with self.subTest(path=path), self.assertRaises(Invalid):
                api.source_section(source, path, 0, 1)
        for value in (None, 'not-a-list', {'0': 'not-a-list'}):
            source['exposure'] = value
            with self.subTest(value=value), self.assertRaises(Invalid):
                api.source_section(source, ['exposure'], 0, 1)
        del source['exposure']
        with self.assertRaises(Invalid):
            api.source_section(source, ['exposure'], 0, 1)

    def test_section_total_utf8_bytes_are_bounded_without_silent_truncation(self):
        source = artifact()
        source['exposure'] = ['x' * 16000]
        page = api.source_section(source, ['exposure'], 0, 1)
        self.assertLessEqual(len(encoded(page)), 16384)
        self.assertEqual(page['values'], source['exposure'])
        for values in (['x' * 16300], ['\u00e9' * 8200], ['x' * 500] * 64):
            source['exposure'] = values
            with self.subTest(characters=len(values[0]), count=len(values)), self.assertRaises(Invalid):
                api.source_section(source, ['exposure'], 0, 64)

    def test_section_output_and_path_are_detached_and_source_unchanged(self):
        source = artifact()
        source['source_refs'] = [{'nested': ['r2', 'r1']}, {'nested': ['r1']}]
        before = encoded(source)
        path = ['source_refs']
        page = api.source_section(source, path, 0, 2)
        page['values'][0]['nested'].append('mutation')
        page['path'].append('mutation')
        self.assertEqual(path, ['source_refs'])
        self.assertEqual(encoded(source), before)


class RecordingClient:
    def __init__(self, source=None, denied=False):
        self.source, self.denied, self.calls = source, denied, []

    def call(self, op, **args):
        self.calls.append((op, args))
        if self.denied:
            raise Denied('Fixture unauthorized or stale attempt')
        return self.source


def tool_call(**changes):
    return {'id': 'section-1', 'name': 'read_source_section',
            'arguments': {'artifact_id': '5' * 64, 'path': ['exposure'], 'offset': 0, 'limit': 2,
                          **changes}}


class ContextViewToolAdversarialTests(unittest.TestCase):
    def test_unauthorized_artifact_is_rejected_before_path_or_slice_inspection(self):
        for changes in ({}, {'path': [['invalid']], 'offset': False, 'limit': -1}):
            client = RecordingClient(denied=True)
            with self.subTest(changes=changes), self.assertRaises(Denied):
                researcher._tool(client, {'lease': 'fixture'}, tool_call(**changes),
                                 tools=researcher.CONTEXT_TOOL_DEFINITIONS)
            self.assertEqual(client.calls, [('read_artifact', {'lease': {'lease': 'fixture'},
                                                             'artifact_id': '5' * 64})])

    def test_success_uses_the_exact_authorized_source_and_only_one_rpc(self):
        source = artifact()
        source['exposure'] = ['r2', 'r1', 'r1', 'r0']
        client = RecordingClient(source)
        result = researcher._tool(client, {'lease': 'fixture'}, tool_call(),
                                  tools=researcher.CONTEXT_TOOL_DEFINITIONS)
        self.assertEqual(result['values'], ['r2', 'r1'])
        self.assertEqual(result['list_sha256'], sha(source['exposure']))
        self.assertEqual(len(client.calls), 1)
        self.assertEqual(client.calls[0][0], 'read_artifact')

    def test_legacy_tool_inventory_cannot_dispatch_sections(self):
        for inventory in (researcher.TOOL_DEFINITIONS, researcher.DEVELOPMENT_TOOL_DEFINITIONS):
            client = RecordingClient(artifact())
            with self.subTest(inventory=len(inventory)), self.assertRaises(Denied):
                researcher._tool(client, {}, tool_call(), tools=inventory)
            self.assertEqual(client.calls, [])

    def test_full_read_source_remains_full_and_exact(self):
        source = artifact()
        client = RecordingClient(source)
        result = researcher._tool(client, {}, {'id': 'full', 'name': 'read_source',
                                  'arguments': {'artifact_id': source['id']}},
                                  tools=researcher.CONTEXT_TOOL_DEFINITIONS)
        self.assertEqual(result, source)
        self.assertIsInstance(result['exposure'], list)


class ContextViewProfileAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.broker = Broker(self.tmp.name)
        self.addCleanup(self.broker.close)
        for name in ('first', 'second'):
            self.admin('register_worker', name=name, role='discovery', capabilities=['research-record/v1'])
        source = self.admin('add_research', kind='source', content={'text': 'Fixed source', 'uri': 'fixture:context-view'},
                            scope={}, source_refs=[])['id']
        self.context = self.admin('create_context', role='discovery', epoch=1, artifact_ids=[source])['id']

    def admin(self, op, **args):
        return self.broker.call(self.broker.admin_token, op, **args)

    def profile(self, **changes):
        return {'model': 'fixture/1', 'prompt_version': 'fixed-context/1', 'max_calls': 4,
                'max_tokens': 80000, 'max_seconds': 60, 'max_cost_units': 0, 'currency': 'NONE',
                'mode': 'fixture', 'prompts': {'first': 'Independent first', 'second': 'Independent second'},
                'tools': deepcopy(researcher.TOOL_DEFINITIONS), 'generation_parameters': {},
                'max_output_tokens': 100, 'call_timeout_seconds': 5, 'max_retries': 0, **changes}

    def create(self, profile, key='fixed'):
        return self.admin('create_research_epoch', key=key, context_id=self.context,
                          workers=['first', 'second'], profile=profile)['id']

    def test_legacy_profile_is_retained_exactly_without_injected_presentation(self):
        profile = self.profile()
        before = encoded(profile)
        identity = self.create(profile)
        retained = self.broker._epoch(identity)['request']['profile']
        self.assertEqual(encoded(retained), before)
        self.assertNotIn('source_presentation', retained)

    def test_optin_is_frozen_and_requires_the_exact_section_definition(self):
        profile = self.profile(source_presentation=VERSION,
                               tools=deepcopy(researcher.CONTEXT_TOOL_DEFINITIONS))
        before = encoded(profile)
        identity = self.create(profile)
        profile['tools'][-1]['description'] = 'Caller mutation'
        self.assertEqual(encoded(self.broker._epoch(identity)['request']['profile']), before)
        with self.assertRaises(Conflict):
            self.create(self.profile())
        for tools in (deepcopy(researcher.TOOL_DEFINITIONS), deepcopy(researcher.CONTEXT_TOOL_DEFINITIONS)):
            if len(tools) == len(researcher.CONTEXT_TOOL_DEFINITIONS):
                tools[-1]['parameters']['additionalProperties'] = True
            with self.subTest(tool_count=len(tools)), self.assertRaises(Invalid):
                self.create(self.profile(source_presentation=VERSION, tools=tools), key='invalid')

    def test_unknown_or_malformed_presentation_version_is_rejected(self):
        for version in ('discovery-source-view/999', '', None, True, 1, [], {}):
            with self.subTest(version=version), self.assertRaises(Invalid):
                self.create(self.profile(source_presentation=version,
                                         tools=deepcopy(researcher.CONTEXT_TOOL_DEFINITIONS)))

    def test_boolean_schema_integer_is_not_an_exact_frozen_tool_definition(self):
        tools = deepcopy(researcher.CONTEXT_TOOL_DEFINITIONS)
        tools[-1]['parameters']['properties']['path']['minItems'] = True
        # Python container equality conflates True with 1; the wire definition must not.
        self.assertEqual(tools[-1], researcher.SECTION_TOOL)
        self.assertNotEqual(encoded(tools[-1]), encoded(researcher.SECTION_TOOL))
        with self.assertRaises(Invalid):
            self.create(self.profile(source_presentation=VERSION, tools=tools))


if __name__ == '__main__':
    unittest.main()
