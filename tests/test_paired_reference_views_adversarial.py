"""Independent paired-reference renderer probes; no runtime admission or live I/O."""
from copy import deepcopy
import hashlib
import json
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from trading_researcher import context_views, researcher, research_calls
from trading_researcher.codec import Invalid
from trading_researcher.errors import Denied
from trading_researcher.feedback import reference_views as api


FAMILIES = (
    ('paired-development-feedback-manifest/1', 'paired_descriptive_feedback_only'),
    ('paired-breakout-development-feedback-manifest/1', 'paired_breakout_descriptive_feedback_only'),
)
TOOL = 'read_paired_feedback_references'
PROFILE = 'discovery-paired-feedback-view/1'
LEGACY_PATHS = (('exposure',), ('source_refs',))


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def at(value, path):
    for key in path:
        value = value[int(key)] if type(value) is list else value[key]
    return value


def put(value, path, replacement):
    parent = at(value, path[:-1])
    parent[int(path[-1]) if type(parent) is list else path[-1]] = replacement


def paths(source):
    return [('body', 'cohort', 'artifact_ids')] + [
        ('body', 'retained_research_records', str(index), key)
        for index in range(len(source['body']['retained_research_records']))
        for key in ('source_refs', 'exposure')]


def manifest(family=0):
    schema, authority = FAMILIES[family]
    refs = [str(index).zfill(3) + '-' + 'a' * 64 for index in range(19)]
    refs[11] = refs[2]  # The view must retain order and multiplicity.
    records = []
    for index, kind in enumerate(('idea', 'gap')):
        records.append({
            'id': str(index) * 64, 'creator': 'perspective-' + str(index),
            'authority': 'unverified_research_assertion',
            'source_refs': list(refs), 'exposure': list(reversed(refs)),
            'body': {'schema': 'research-record/1', 'kind': kind,
                'content': {'text': 'Unmodified idea; é e\u0301 雪\n' * 160,
                    'reason': 'Unsupported meaning is retained; no empirical rejection.',
                    'reopen_condition': 'Require the missing observation, not a substitute.'},
                'scope': {'instrument': 'ETHUSDT', 'outcome_delay': 'longer than one bar'},
                'relations': {'source_refs': list(refs)}, 'created_at': 1000}})
    return {'id': 'b' * 64, 'version': 'local-artifact/1', 'creator': 'controller',
        'origin': 'controller', 'authority': authority, 'data_class': 'development',
        'source_refs': list(refs), 'exposure': list(refs), 'not_before_epoch': 9,
        'body': {'schema': schema, 'created_at': 2000,
            'request': {'root_epoch_id': 'root', 'execution_id': 'execution',
                'composition_id': 'composition', 'meaning_review_assessment_id': 'review',
                'target_epoch': 9}, 'publisher_sha256': 'c' * 64,
            'cohort': {'artifact_ids': list(refs), 'idea_ids': list(refs),
                'jobs': [{'state': 'blocked', 'reason': 'Failed original formalization',
                    'metadata': {'artifact_ids': list(refs), 'attempt': 2}}],
                'calls': [{'state': 'failed', 'charged_tokens': 173}],
                'unresolved_exposure_refs': ['opaque:unresolved'],
                'qualification': 'Closed development metadata, no publication authority.'},
            'retained_research_records': records,
            'evidence_at_publication': {'qualified': True, 'source_refs': list(refs),
                'uncertainty': 'Publication-time evidence is not a currentness assertion.'},
            'scientific_readiness': False,
            'qualification': 'Descriptive historical feedback; no scientific or capital authority.'}}


def marker(values, path, tool):
    return {'schema': 'deferred-source-list/1', 'path': list(path),
            'count': len(values), 'sha256': sha(values), 'tool': tool}


def page_expected(source, path, values, offset, limit):
    end = min(len(values), offset + limit)
    return {'schema': 'source-section/1', 'artifact_id': source['id'],
            'path': list(path), 'list_sha256': sha(values), 'count': len(values),
            'offset': offset, 'next_offset': end if end < len(values) else None,
            'values': values[offset:end]}


class RecordingClient:
    def __init__(self, source=None, denied=False):
        self.source, self.denied, self.calls = source, denied, []

    def call(self, operation, **arguments):
        self.calls.append((operation, arguments))
        if self.denied:
            raise Denied('Source/context/lease access revoked')
        return deepcopy(self.source)


class PairedReferenceAdversarialTests(unittest.TestCase):
    def test_exact_versioned_tool_contract(self):
        self.assertEqual(api.PROFILE, PROFILE)
        self.assertEqual(api.OWNED_SCHEMAS, FAMILIES)
        self.assertEqual(api.REFERENCE_TOOL['name'], TOOL)
        parameters = api.REFERENCE_TOOL['parameters']
        self.assertEqual(parameters['required'], ['artifact_id', 'path', 'offset', 'limit'])
        self.assertIs(parameters['additionalProperties'], False)
        self.assertEqual(parameters['properties'], {
            'artifact_id': {'type': 'string'},
            'path': {'type': 'array', 'items': {'type': 'string'}, 'minItems': 3, 'maxItems': 4},
            'offset': {'type': 'integer', 'minimum': 0},
            'limit': {'type': 'integer', 'minimum': 1, 'maximum': 64}})

    def test_all_and_only_owned_reference_fields_change(self):
        for family in range(2):
            source = manifest(family)
            before = encoded(source)
            expected = deepcopy(source)
            for path in LEGACY_PATHS:
                put(expected, path, marker(at(source, path), path, 'read_source_section'))
            for path in paths(source):
                put(expected, path, marker(at(source, path), path, TOOL))
            actual = api.source_view(source)
            self.assertEqual(actual['schema'], PROFILE)
            self.assertEqual(actual['artifact_id'], source['id'])
            self.assertEqual(encoded(actual['content']), encoded(expected))
            self.assertEqual(encoded(source), before)
            self.assertIn('unread evidence', actual['qualification'])
            self.assertIn('no additional access', actual['qualification'])

    def test_pages_restore_entire_envelopes_with_exact_order_duplicates_and_metadata(self):
        for family in range(2):
            source = manifest(family)
            reconstructed = api.source_view(source)['content']
            for path in [*LEGACY_PATHS, *paths(source)]:
                deferred = at(reconstructed, path)
                section = (context_views.source_section if deferred['tool'] == 'read_source_section'
                           else api.reference_section)
                recovered, offset = [], 0
                while True:
                    page = section(source, list(path), offset, 7)
                    self.assertEqual(page, page_expected(source, path, at(source, path), offset, 7))
                    self.assertEqual(page['list_sha256'], deferred['sha256'])
                    self.assertEqual(page['count'], deferred['count'])
                    recovered.extend(page['values'])
                    if page['next_offset'] is None:
                        break
                    offset = page['next_offset']
                self.assertEqual(recovered, at(source, path))
                put(reconstructed, path, recovered)
            self.assertEqual(encoded(reconstructed), encoded(source))

    def test_threshold_is_inclusive_and_uses_canonical_utf8_bytes(self):
        for path in paths(manifest()):
            for values, size in ((['x' * 1019], 1023), (['x' * 1020], 1024),
                                 (['é' * 510], 1024), ([], 2), ([''], 4)):
                with self.subTest(path=path, size=size):
                    source = manifest()
                    put(source, path, values)
                    self.assertEqual(len(encoded(values)), size)
                    actual = at(api.source_view(source)['content'], path)
                    self.assertEqual(actual, marker(values, path, TOOL) if size >= 1024 else values)
                    self.assertEqual(api.reference_section(source, list(path), 0, 64),
                                     page_expected(source, path, values, 0, 64))

    def test_cross_family_spoof_and_unsupported_owner_schema_never_enable_new_paths(self):
        changes = [('version', 'local-artifact/2'), ('creator', 'worker'),
                   ('origin', 'external'), ('data_class', 'assessment'),
                   ('data_class', 'work_product'), ('authority', None)]
        for family in range(2):
            family_changes = changes + [('authority', FAMILIES[1 - family][1]),
                ('body_schema', 'development-feedback-manifest/1'),
                ('body_schema', FAMILIES[family][0] + '-changed'),
                ('body_schema', FAMILIES[1 - family][0]), ('body_schema', None)]
            for key, value in family_changes:
                with self.subTest(family=family, key=key, value=value):
                    source = manifest(family)
                    if key == 'body_schema':
                        source['body']['schema'] = value
                    else:
                        source[key] = value
                    legacy = context_views.source_view(source, context_views.FEEDBACK_VIEW_PROFILE)
                    self.assertEqual(api.source_view(source)['content'], legacy['content'])
                    for path in paths(source):
                        with self.assertRaises(Invalid):
                            api.reference_section(source, list(path), 0, 1)

    def test_nonstring_lists_remain_inline_and_unpageable_at_every_owned_path(self):
        for path in paths(manifest()):
            for values in (None, {'0': 'untyped'}, ['x' * 1200, 1], ['x' * 1200, False],
                           ['x' * 1200, None], ['x' * 1200, ['nested']],
                           ['x' * 1200, {'id': 'nested'}]):
                with self.subTest(path=path, type=type(values).__name__):
                    source = manifest()
                    put(source, path, values)
                    self.assertEqual(at(api.source_view(source)['content'], path), values)
                    with self.assertRaises(Invalid):
                        api.reference_section(source, list(path), 0, 1)

    def test_missing_or_malformed_containers_cannot_be_traversed(self):
        for container, value in (('cohort', None), ('cohort', []),
                                 ('retained_research_records', {}),
                                 ('retained_research_records', [None, 'not-a-record'])):
            source = manifest()
            source['body'][container] = value
            self.assertEqual(api.source_view(source)['content']['body'][container], value)
            path = (['body', 'cohort', 'artifact_ids'] if container == 'cohort' else
                    ['body', 'retained_research_records', '0', 'source_refs'])
            with self.assertRaises(Invalid):
                api.reference_section(source, path, 0, 1)

    def test_exact_path_grammar_and_decimal_indices_do_not_follow_arbitrary_objects(self):
        source = manifest()
        invalid = [None, (), [], 'body.cohort.artifact_ids', ['source_refs'], ['exposure'],
            ['body', 'cohort', 'idea_ids'], ['body', 'cohort', 'artifact_ids', '0'],
            ['body', 'retained_research_records', '0', 'body', 'source_refs'],
            ['body', 'retained_research_records', '0', '__class__'], ['__dict__'],
            ['body', 'evidence_at_publication', 'source_refs']]
        invalid += [['body', 'retained_research_records', index, 'source_refs']
                    for index in (0, True, {}, [], '-1', '+0', '00', '01', '0.0',
                                  ' 0', '0 ', '٠', '０', '2', '9' * 5000)]
        for path in invalid:
            with self.subTest(path=path), self.assertRaises(Invalid):
                api.reference_section(source, path, 0, 1)
        source['body']['retained_research_records'].extend(
            deepcopy(source['body']['retained_research_records'][0]) for _ in range(9))
        path = ['body', 'retained_research_records', '10', 'exposure']
        self.assertEqual(api.reference_section(source, path, 1, 2)['values'], at(source, path)[1:3])

    def test_integer_types_count_limit_and_end_offset_are_exact(self):
        source = manifest()
        path = ['body', 'cohort', 'artifact_ids']
        for offset, limit in ((True, 1), (False, 1), (-1, 1), (20, 1), (None, 1),
                              ('0', 1), (0.0, 1), (0, True), (0, False), (0, 0),
                              (0, 65), (0, -1), (0, '1'), (0, None), (0, 1.0)):
            with self.subTest(offset=offset, limit=limit), self.assertRaises(Invalid):
                api.reference_section(source, path, offset, limit)
        self.assertEqual(api.reference_section(source, path, 19, 64),
                         page_expected(source, path, at(source, path), 19, 64))
        source['body']['cohort']['artifact_ids'] = [str(index) for index in range(65)]
        self.assertEqual(len(api.reference_section(source, path, 0, 64)['values']), 64)
        self.assertEqual(api.reference_section(source, path, 0, 64)['next_offset'], 64)

    def test_page_utf8_bound_accepts_exact_limit_and_rejects_one_more_byte(self):
        source = manifest()
        path = ['body', 'cohort', 'artifact_ids']
        initial = ['é']
        padding = 16384 - len(encoded(page_expected(source, path, initial, 0, 1)))
        values = ['é' + 'x' * padding]
        source['body']['cohort']['artifact_ids'] = values
        page = api.reference_section(source, path, 0, 1)
        self.assertEqual(len(encoded(page)), 16384)
        self.assertEqual(page['values'], values)
        source['body']['cohort']['artifact_ids'][0] += 'x'
        with self.assertRaises(Invalid):
            api.reference_section(source, path, 0, 1)
        source['body']['cohort']['artifact_ids'] = ['雪' * 6000]
        with self.assertRaises(Invalid):
            api.reference_section(source, path, 0, 1)
        self.assertEqual(source['body']['cohort']['artifact_ids'], ['雪' * 6000])

    def test_outputs_and_markers_are_fully_detached_from_sources_and_future_calls(self):
        source = manifest()
        before = encoded(source)
        view = api.source_view(source)
        view['content']['body']['cohort']['jobs'][0]['metadata']['attempt'] = -1
        view['content']['body']['retained_research_records'][0]['body']['content']['text'] = 'changed'
        view['content']['body']['cohort']['artifact_ids']['path'].append('changed')
        path = ['body', 'retained_research_records', '0', 'exposure']
        page = api.reference_section(source, path, 0, 2)
        page['values'][0] = 'changed'
        page['path'].append('changed')
        self.assertEqual(encoded(source), before)
        self.assertEqual(path, ['body', 'retained_research_records', '0', 'exposure'])
        self.assertEqual(api.reference_section(source, path, 0, 2),
                         page_expected(source, path, at(source, path), 0, 2))

    def test_access_denial_precedes_selector_control_and_manifest_inspection(self):
        for path, offset, limit in (([], 0, 1), ([['malformed']], True, -1),
                                    (['body', 'cohort', 'artifact_ids'], 0, 2)):
            client = RecordingClient(None, denied=True)
            arguments = {'artifact_id': 'b' * 64, 'path': path, 'offset': offset, 'limit': limit}
            lease = {'identity': 'revoked-attempt'}
            with self.assertRaises(Denied):
                api.read_references(client, lease, arguments)
            self.assertEqual(client.calls, [('read_artifact', {'lease': lease, 'artifact_id': 'b' * 64})])

    def test_reauthorization_for_each_page_and_no_reference_id_following(self):
        source = manifest()
        source['body']['cohort']['artifact_ids'][0] = 'forbidden-artifact-id'
        client = RecordingClient(source)
        arguments = {'artifact_id': source['id'], 'path': ['body', 'cohort', 'artifact_ids'],
                     'offset': 0, 'limit': 2}
        lease = {'identity': 'current-attempt'}
        page = api.read_references(client, lease, arguments)
        self.assertEqual(page['values'], source['body']['cohort']['artifact_ids'][:2])
        self.assertEqual(client.calls, [('read_artifact', {'lease': lease, 'artifact_id': source['id']})])
        client.denied = True
        with self.assertRaises(Denied):
            api.read_references(client, lease, {**arguments, 'offset': 2})
        self.assertEqual(len(client.calls), 2)
        self.assertTrue(all(call[1]['artifact_id'] == source['id'] for call in client.calls))

    def test_malformed_argument_envelopes_fail_before_client_access(self):
        arguments = {'artifact_id': 'b' * 64, 'path': ['body', 'cohort', 'artifact_ids'],
                     'offset': 0, 'limit': 1}
        malformed = [None, [], {**arguments, 'follow_id': True}]
        malformed.extend({key: value for key, value in arguments.items() if key != missing}
                         for missing in arguments)
        client = RecordingClient(manifest())
        for value in malformed:
            with self.subTest(type=type(value).__name__), self.assertRaises(Invalid):
                api.read_references(client, {}, value)
        self.assertEqual(client.calls, [])

    def test_import_cannot_install_handler_or_profile_into_old_worker(self):
        self.assertNotIn(PROFILE, context_views.PRESENTATION_PROFILES)
        call = {'id': 'candidate-page', 'name': TOOL, 'arguments': {
            'artifact_id': 'b' * 64, 'path': ['body', 'cohort', 'artifact_ids'],
            'offset': 0, 'limit': 1}}
        inventories = (None, researcher.TOOL_DEFINITIONS, researcher.DEVELOPMENT_TOOL_DEFINITIONS,
                       researcher.CONTEXT_TOOL_DEFINITIONS, researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS)
        for tools in inventories:
            client = RecordingClient(manifest())
            with self.assertRaises(Denied):
                researcher._tool(client, {}, call, tools=tools)
            self.assertEqual(client.calls, [])
        client = RecordingClient(manifest())
        with self.assertRaises(Denied):
            researcher._tool(client, {}, call,
                             tools=[*researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS, api.REFERENCE_TOOL])
        self.assertEqual(client.calls, [])
        with self.assertRaises(Invalid):
            context_views.source_view(manifest(), profile=PROFILE)
        for family in range(2):
            with self.assertRaises(Invalid):
                context_views.feedback_source_section(
                    manifest(family), ['body', 'cohort', 'artifact_ids'], 0, 1)
        full = researcher._tool(client, {}, {'id': 'full', 'name': 'read_source',
            'arguments': {'artifact_id': 'b' * 64}}, tools=researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS)
        self.assertEqual(encoded(full), encoded(manifest()))

    def test_old_epoch_validator_rejects_candidate_profile_before_any_write(self):
        host = SimpleNamespace(_context=Mock(return_value={'role': 'discovery'}), _db=Mock())
        host._db.execute.return_value.fetchone.return_value = {'role': 'discovery'}
        profile = {key: 1 for key in research_calls.PROFILE_FIELDS}
        profile.update(prompts={'left': 'first perspective', 'right': 'second perspective'},
                       tools=[*researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS, api.REFERENCE_TOOL],
                       generation_parameters={}, source_presentation=PROFILE)
        with self.assertRaisesRegex(Invalid, 'Source presentation requires'):
            research_calls.ResearchCalls._create_research_epoch(
                host, {'role': 'operator'}, 'probe-only', 'context', ['left', 'right'], profile)
        self.assertEqual(len(host._db.execute.call_args_list), 2)
        self.assertTrue(all(call.args[0] == 'SELECT role FROM principals WHERE name=?'
                            for call in host._db.execute.call_args_list))


if __name__ == '__main__':
    unittest.main()
