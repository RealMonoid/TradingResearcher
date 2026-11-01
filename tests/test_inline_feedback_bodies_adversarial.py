"""Independent exact inline-body, ancestry, and authorized-expansion probes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from trading_researcher import context_views, researcher, research_calls
from trading_researcher.codec import Invalid
from trading_researcher.errors import Denied
from trading_researcher.feedback import inline_bodies as api, reference_views


FAMILIES = (
    ('development-feedback-manifest/1', 'descriptive_development_feedback_only'),
    ('paired-development-feedback-manifest/1', 'paired_descriptive_feedback_only'),
    ('paired-breakout-development-feedback-manifest/1', 'paired_breakout_descriptive_feedback_only'),
)
PATHS = (('body', 'evidence_at_publication', 'data_use', 'prior_knowledge', 'artifact_ids'),
         ('body', 'evidence_at_publication', 'data_use', 'prior_knowledge', 'context_ids'))
TOOL = 'read_feedback_ancestry_references'
ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / '.trf-runtime/development-admission-2026-10-31/prepared.json'
PRIOR = ROOT / '.trf-runtime/paired-reference-paging-2026-10-31/candidate.json'


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


def records(source):
    return source['body']['retained_research_records']


def fixture():
    refs = [format(index, '064x') for index in range(36)]
    refs[19] = refs[2]
    original_records = []
    for index, kind in enumerate(('idea', 'gap')):
        original_records.append({'id': str(index + 7) * 64, 'creator': 'original-worker',
            'authority': 'unverified_research_assertion', 'source_refs': list(refs),
            'exposure': list(reversed(refs)), 'body': {'schema': 'research-record/1',
                'kind': kind, 'created_at': 100, 'available_at': 110,
                'content': {'text': 'Exact original é e\u0301 雪\n' * 90,
                    'reason': 'Missing meaning is retained; not empirical falsification.',
                    'reopen_condition': 'Resolve the original gap, never substitute an easier claim.'},
                'scope': {'interval': 'development-only', 'delay': 900},
                'relations': {'source_refs': list(refs)}}})
    result = []
    for index, (schema, authority) in enumerate(FAMILIES):
        result.append({'id': str(index + 1) * 64, 'version': 'local-artifact/1',
            'creator': 'controller', 'origin': 'controller', 'data_class': 'development',
            'authority': authority, 'source_refs': list(refs), 'exposure': list(refs),
            'body': {'schema': schema, 'created_at': 120, 'scientific_readiness': False,
                'qualification': 'Historical development, not present scientific authority.',
                'request': {'target_epoch': 7, 'meaning_review_assessment_id': 'original-review'},
                'cohort': {'artifact_ids': list(refs), 'jobs': [{'state': 'blocked',
                    'detail': {'reason': 'Provider ended without a final auxiliary result',
                        'retry_when': 'Within the original budget'},
                    'attempts': [{'detail': {'reason': 'Original unique failure'}, 'ended_at': 115}]}],
                    'epochs': [{'state': 'active', 'usage': {'charged_tokens': 33}}]},
                'evidence_at_publication': {'data_use': {'schema': 'paired-data-use-assessment/1',
                    'rights': {'purpose': 'Personal non-production historical research'},
                    'availability': {'basis': 'assumed', 'delay_seconds': 900},
                    'model_training_exposure': 'UNKNOWN',
                    'prior_knowledge': {'artifact_ids': list(refs), 'context_ids': list(reversed(refs)),
                        'basis': 'Original ancestry, before compiler dependencies',
                        'protected_knowledge_ids': [], 'operations_knowledge_ids': [],
                        'unresolved_exposure_refs': []}}},
                'retained_research_records': deepcopy(original_records)}})
    return result


def expected_views(sources):
    """Independent expected overlay on the separately qualified base renderer."""
    result = [reference_views.source_view(source) for source in sources]
    for view, source in zip(result, sources):
        if (source.get('version'), source.get('creator'), source.get('origin'), source.get('data_class'),
            source.get('authority'), source['body'].get('schema')) != (
                'local-artifact/1', 'controller', 'controller', 'development',
                FAMILIES[2][1], FAMILIES[2][0]):
            continue
        data_use = source['body'].get('evidence_at_publication', {}).get('data_use', {})
        if data_use.get('schema') != 'paired-data-use-assessment/1':
            continue
        for path in PATHS:
            try:
                values = at(source, path)
            except (KeyError, TypeError):
                continue
            if (type(values) is list and all(type(x) is str and len(x) == 64
                    and set(x) <= set('0123456789abcdef') for x in values)
                    and len(encoded(values)) >= 1024):
                put(view['content'], path, {'schema': 'deferred-source-list/1',
                    'path': list(path), 'count': len(values), 'sha256': sha(values), 'tool': TOOL})
    return result


def expected_page(source, path, offset, limit):
    values = at(source, path)
    end = min(len(values), offset + limit)
    return {'schema': 'source-section/1', 'artifact_id': source['id'], 'path': list(path),
        'list_sha256': sha(values), 'count': len(values), 'offset': offset,
        'next_offset': end if end < len(values) else None, 'values': values[offset:end]}


def restore_markers(value, original):
    if type(value) is dict and value.get('schema') == 'deferred-source-list/1':
        readers = {'read_source_section': context_views.source_section,
            'read_feedback_references': context_views.feedback_source_section,
            'read_paired_feedback_references': reference_views.reference_section,
            TOOL: api.ancestry_section}
        recovered, offset = [], 0
        while True:
            page = readers[value['tool']](original, value['path'], offset, 13)
            if page != expected_page(original, value['path'], offset, 13):
                raise AssertionError('Page differs from independent expected values')
            if page['count'] != value['count'] or page['list_sha256'] != value['sha256']:
                raise AssertionError('Marker binding changed')
            recovered.extend(page['values'])
            if page['next_offset'] is None:
                break
            offset = page['next_offset']
        return recovered
    if type(value) is dict:
        return {key: restore_markers(child, original) for key, child in value.items()}
    if type(value) is list:
        return [restore_markers(child, original) for child in value]
    return value


class RecordingClient:
    def __init__(self, source=None, denied=False):
        self.source, self.denied, self.calls = source, denied, []

    def call(self, operation, **arguments):
        self.calls.append((operation, arguments))
        if self.denied:
            raise Denied('Revoked source/context/lease')
        return deepcopy(self.source)


class InlineBodiesAdversarialTests(unittest.TestCase):
    def test_exact_schema_paths_and_tool_contract(self):
        self.assertEqual(api.SCHEMA, 'discovery-feedback-inline-bodies/1')
        self.assertEqual(api.BODY_REF, 'inline-feedback-body-ref/1')
        self.assertEqual(api.MANIFESTS, FAMILIES)
        self.assertEqual(api.ANCESTRY_PATHS, PATHS)
        self.assertEqual(api.ANCESTRY_TOOL['name'], TOOL)
        parameters = api.ANCESTRY_TOOL['parameters']
        self.assertEqual(parameters['properties']['path'], {'type': 'array', 'items': {'type': 'string'},
                         'minItems': 5, 'maxItems': 5})
        self.assertEqual(parameters['properties']['limit'], {'type': 'integer', 'minimum': 1, 'maximum': 64})
        self.assertIs(parameters['additionalProperties'], False)

    def test_hand_fixed_table_and_only_body_replacement_preserve_occurrence_bindings(self):
        sources = fixture()
        before = encoded(sources)
        expected = {'schema': 'discovery-feedback-inline-bodies/1', 'purpose': 'fixed purpose',
                    'sources': expected_views(sources), 'inline_record_bodies': {}}
        for view, source in zip(expected['sources'], sources):
            for index, original in enumerate(records(source)):
                identity = original['id']
                expected['inline_record_bodies'][identity] = {
                    'body_sha256': sha(original['body']), 'body': deepcopy(original['body'])}
                view['content']['body']['retained_research_records'][index]['body'] = {
                    'schema': 'inline-feedback-body-ref/1', 'record_id': identity,
                    'body_sha256': sha(original['body'])}
        actual = api.build('fixed purpose', sources)
        self.assertEqual(encoded(actual), encoded(expected))
        self.assertEqual(encoded(sources), before)
        self.assertEqual(len(actual['inline_record_bodies']), 2)
        self.assertEqual(api.verify(actual, 'fixed purpose', sources),
                         {'purpose': 'fixed purpose', 'sources': expected_views(sources)})

    def test_duplicate_occurrences_and_source_order_remain_exact(self):
        sources = fixture()
        records(sources[0]).insert(1, deepcopy(records(sources[0])[0]))
        sources.reverse()
        packet = api.build('purpose', sources)
        self.assertEqual(len(packet['inline_record_bodies']), 2)
        self.assertEqual([x['artifact_id'] for x in packet['sources']], [x['id'] for x in sources])
        expanded = api.verify(packet, 'purpose', sources)
        self.assertEqual([r['id'] for r in records(expanded['sources'][2]['content'])],
                         [r['id'] for r in records(sources[2])])

    def test_conflicting_body_or_immutable_metadata_never_selects_a_preferred_variant(self):
        for field, value in (('creator', 'other-worker'), ('authority', 'other-authority'),
                             ('source_refs', ['different']), ('exposure', ['different']),
                             ('body', {'schema': 'research-record/1', 'kind': 'idea', 'content': {'text': 'changed'}})):
            sources = fixture()
            records(sources[1])[0][field] = value
            before = encoded(sources)
            with self.subTest(field=field), self.assertRaises(Invalid):
                api.build('purpose', sources)
            self.assertEqual(encoded(sources), before)

    def test_unknown_record_shapes_and_nonowners_remain_inline_without_factoring(self):
        for mutation in ('extra_record_field', 'unknown_body', 'invalid_id', 'wrong_owner'):
            sources = [fixture()[0]]
            original = records(sources[0])[0]
            if mutation == 'extra_record_field':
                original['unknown'] = 'keep this whole record'
            elif mutation == 'unknown_body':
                original['body'] = {'schema': 'future-body/1', 'text': 'Unknown full original meaning'}
            elif mutation == 'invalid_id':
                original['id'] = 'not-an-immutable-id'
            else:
                sources[0]['creator'] = 'worker'
            packet = api.build('purpose', sources)
            self.assertEqual(packet['sources'][0]['content']['body']['retained_research_records'][0]['body'],
                             original['body'])
            self.assertEqual(api.verify(packet, 'purpose', sources)['sources'], expected_views(sources))

    def test_reserved_pointer_tag_collision_stops_representation_before_emitting_a_packet(self):
        for extra in ({}, {'unknown_original_text': 'Keep the original; do not deny the idea'}):
            sources = [fixture()[0]]
            records(sources[0])[0]['body'] = {'schema': api.BODY_REF,
                'record_id': '7' * 64, 'body_sha256': 'c' * 64, **extra}
            before = encoded(sources)
            with self.assertRaises(Invalid):
                api.build('purpose', sources)
            self.assertEqual(encoded(sources), before)
        # The tag is only reserved where the owned transformation would inspect it.
        sources[0]['creator'] = 'worker'
        api.verify(api.build('purpose', sources), 'purpose', sources)

    def test_missing_extra_malformed_or_mismatched_targets_fail_closed(self):
        packet = api.build('purpose', fixture())
        mutations = []
        value = deepcopy(packet); del value['inline_record_bodies']['7' * 64]; mutations.append(value)
        value = deepcopy(packet); value['inline_record_bodies']['a' * 64] = deepcopy(value['inline_record_bodies']['7' * 64]); mutations.append(value)
        value = deepcopy(packet); value['inline_record_bodies']['7' * 64]['extra'] = True; mutations.append(value)
        value = deepcopy(packet); value['inline_record_bodies']['7' * 64]['body_sha256'] = '0' * 64; mutations.append(value)
        value = deepcopy(packet); value['inline_record_bodies']['7' * 64]['body']['content']['text'] = 'tampered'; mutations.append(value)
        value = deepcopy(packet); value['sources'][0]['content']['body']['retained_research_records'][0]['body']['extra'] = True; mutations.append(value)
        value = deepcopy(packet); value['sources'][0]['content']['body']['retained_research_records'][0]['body']['record_id'] = '8' * 64; mutations.append(value)
        value = deepcopy(packet); value['sources'][0]['content']['body']['retained_research_records'][0]['extra'] = True; mutations.append(value)
        value = deepcopy(packet); value['extra'] = True; mutations.append(value)
        for index, value in enumerate(mutations):
            with self.subTest(index=index), self.assertRaises(Invalid):
                api.expand(value)

    def test_structural_self_consistency_does_not_authenticate_changed_body_or_metadata(self):
        sources = fixture()
        packet = api.build('purpose', sources)
        entry = packet['inline_record_bodies']['7' * 64]
        entry['body']['content']['text'] = 'Self-consistent unauthorized replacement'
        entry['body_sha256'] = sha(entry['body'])
        for view in packet['sources']:
            records(view['content'])[0]['body']['body_sha256'] = entry['body_sha256']
        api.expand(packet)  # Structural consistency alone is deliberately weaker.
        with self.assertRaises(Invalid):
            api.verify(packet, 'purpose', sources)
        for field, replacement in (('creator', 'changed'), ('authority', 'changed'), ('exposure', [])):
            changed = api.build('purpose', sources)
            records(changed['sources'][0]['content'])[0][field] = replacement
            api.expand(changed)
            with self.subTest(field=field), self.assertRaises(Invalid):
                api.verify(changed, 'purpose', sources)

    def test_literal_body_bypass_cannot_remove_a_required_table_target(self):
        sources = fixture()
        packet = api.build('purpose', sources)
        body = packet['inline_record_bodies'].pop('7' * 64)['body']
        for view in packet['sources']:
            records(view['content'])[0]['body'] = deepcopy(body)
        api.expand(packet)  # Expanded values are exact, but the representation is not canonical.
        with self.assertRaises(Invalid):
            api.verify(packet, 'purpose', sources)

    def test_views_tables_pages_and_every_expanded_occurrence_are_detached(self):
        sources = fixture(); before = encoded(sources)
        packet = api.build('purpose', sources); packet_before = encoded(packet)
        expanded = api.expand(packet)
        records(expanded['sources'][0]['content'])[0]['body']['content']['text'] = 'caller mutation'
        self.assertEqual(records(expanded['sources'][1]['content'])[0]['body'], records(sources[1])[0]['body'])
        self.assertEqual(encoded(packet), packet_before)
        packet['inline_record_bodies']['7' * 64]['body']['content']['text'] = 'table mutation'
        self.assertEqual(encoded(sources), before)

    def test_source_id_and_purpose_controls_are_strict(self):
        sources = fixture()
        for value in (None, {}, [sources[0], sources[0]]):
            with self.subTest(value=type(value).__name__), self.assertRaises(Invalid):
                api.build('purpose', value)
        for purpose in ('', ' ' * 4, None, 'x' * 8193):
            with self.assertRaises(Invalid):
                api.build(purpose, sources)
        with self.assertRaises(Invalid):
            api.verify(api.build('purpose', sources), 'different purpose', sources)

    def test_only_exact_breakout_owner_and_data_use_schema_enable_ancestry_pages(self):
        for key, value in (('version', 'local-artifact/2'), ('creator', 'worker'), ('origin', 'external'),
                           ('data_class', 'assessment'), ('authority', FAMILIES[1][1])):
            source = fixture()[2]; source[key] = value
            for path in PATHS:
                with self.subTest(key=key), self.assertRaises(Invalid):
                    api.ancestry_section(source, list(path), 0, 1)
        for family in range(2):
            with self.assertRaises(Invalid):
                api.ancestry_section(fixture()[family], list(PATHS[0]), 0, 1)
        source = fixture()[2]
        source['body']['evidence_at_publication']['data_use']['schema'] = 'paired-data-use-assessment/2'
        self.assertEqual(api.expand(api.build('purpose', [source]))['sources'][0],
                         reference_views.source_view(source))
        with self.assertRaises(Invalid):
            api.ancestry_section(source, list(PATHS[0]), 0, 1)

    def test_ancestry_lists_are_strict_hex_id_lists_with_order_and_duplicates(self):
        for path in PATHS:
            for value in (None, {}, ['f' * 64, 1], ['F' * 64] * 20, ['z' * 64] * 20,
                          ['f' * 63] * 20, ['f' * 65] * 20, ['opaque-context'] * 20):
                source = fixture()[2]; put(source, path, value)
                self.assertEqual(at(api.build('purpose', [source])['sources'][0]['content'], path), value)
                with self.assertRaises(Invalid):
                    api.ancestry_section(source, list(path), 0, 1)
            source = fixture()[2]
            recovered = []
            for offset in (0, 13, 26, 36):
                page = api.ancestry_section(source, list(path), offset, 13)
                self.assertEqual(page, expected_page(source, path, offset, 13))
                self.assertLessEqual(len(encoded(page)), 16384)
                recovered.extend(page['values'])
            self.assertEqual(recovered, at(source, path))

    def test_ancestry_threshold_and_bounded_integer_path_grammar(self):
        source = fixture()[2]
        for count in (0, 15, 16):
            values = [format(i, '064x') for i in range(count)]
            put(source, PATHS[0], values)
            actual = at(api.build('purpose', [source])['sources'][0]['content'], PATHS[0])
            self.assertEqual(type(actual), dict if count == 16 else list)
        path = list(PATHS[1])
        for offset, limit in ((True, 1), (-1, 1), (37, 1), ('0', 1), (0.0, 1),
                              (0, True), (0, 0), (0, 65), (0, -1), (0, '1')):
            with self.subTest(offset=offset, limit=limit), self.assertRaises(Invalid):
                api.ancestry_section(source, path, offset, limit)
        invalid = [None, [], tuple(path), path[:-1], ['content', *path], [*path, '0'],
            ['body', 'evidence_at_publication', 'data_use', 'rights', 'document_sha256'],
            ['body', 'evidence_at_publication', 'data_use', 'prior_knowledge', 'technical_provenance_ids']]
        for value in invalid:
            with self.subTest(path=value), self.assertRaises(Invalid):
                api.ancestry_section(source, value, 0, 1)
        values = [format(i, '064x') for i in range(65)]; put(source, PATHS[1], values)
        self.assertEqual(len(api.ancestry_section(source, path, 0, 64)['values']), 64)
        self.assertEqual(api.ancestry_section(source, path, 0, 64)['next_offset'], 64)

    def test_authorization_first_repeated_read_revocation_and_no_id_following(self):
        arguments = {'artifact_id': '3' * 64, 'path': [['hostile']], 'offset': True, 'limit': -1}
        client = RecordingClient(None, denied=True); lease = {'owner': 'current-context'}
        with self.assertRaises(Denied):
            api.read_ancestry(client, lease, arguments)
        self.assertEqual(client.calls, [('read_artifact', {'lease': lease, 'artifact_id': '3' * 64})])
        client = RecordingClient(fixture()[2])
        arguments.update(path=list(PATHS[0]), offset=0, limit=2)
        page = api.read_ancestry(client, lease, arguments)
        self.assertEqual(page, expected_page(fixture()[2], PATHS[0], 0, 2))
        page['values'][0] = 'caller mutation'
        client.denied = True
        with self.assertRaises(Denied):
            api.read_ancestry(client, lease, {**arguments, 'offset': 2})
        self.assertEqual(len(client.calls), 2)
        self.assertTrue(all(x == ('read_artifact', {'lease': lease, 'artifact_id': '3' * 64}) for x in client.calls))
        for value in (None, {}, {**arguments, 'follow_id': True}):
            with self.assertRaises(Invalid):
                api.read_ancestry(client, lease, value)
        self.assertEqual(len(client.calls), 2)

    def test_old_reader_worker_and_epoch_profile_cannot_gain_new_presentation_on_import(self):
        source = fixture()[2]
        with self.assertRaises(Invalid):
            context_views.source_view(source, api.SCHEMA)
        with self.assertRaises(Invalid):
            reference_views.reference_section(source, list(PATHS[0]), 0, 1)
        call = {'id': 'ancestry', 'name': TOOL, 'arguments': {'artifact_id': source['id'],
            'path': list(PATHS[0]), 'offset': 0, 'limit': 1}}
        client = RecordingClient(source)
        for tools in (None, researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS,
                      [*researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS, api.ANCESTRY_TOOL]):
            with self.assertRaises(Denied):
                researcher._tool(client, {}, call, tools=tools)
        self.assertEqual(client.calls, [])
        host = SimpleNamespace(_context=Mock(return_value={'role': 'discovery'}), _db=Mock())
        host._db.execute.return_value.fetchone.return_value = {'role': 'discovery'}
        profile = {key: 1 for key in research_calls.PROFILE_FIELDS}
        profile.update(prompts={'left': 'left', 'right': 'right'}, generation_parameters={},
                       tools=researcher.FEEDBACK_CONTEXT_TOOL_DEFINITIONS, source_presentation=api.SCHEMA)
        with self.assertRaisesRegex(Invalid, 'Source presentation requires'):
            research_calls.ResearchCalls._create_research_epoch(host, {}, 'probe', 'context',
                                                              ['left', 'right'], profile)

    @unittest.skipUnless(PREPARED.exists() and PRIOR.exists(), 'Local immutable packet not present')
    def test_actual_13_sources_layered_reconstruction_and_unique_failure_preservation(self):
        self.assertEqual(hashlib.sha256(PREPARED.read_bytes()).hexdigest(),
                         '4c92dac5cc3cc35ed69f862fea392c84b2c2dcdbc59eccecc305310f50e3059d')
        self.assertEqual(hashlib.sha256(PRIOR.read_bytes()).hexdigest(),
                         '1f46efe447e28de2873cfc3b1c9afaac88b242350ca2eedb16bf863c18bb6ef2')
        prepared = json.loads(PREPARED.read_text(encoding='utf-8'))
        prior = json.loads(PRIOR.read_text(encoding='utf-8'))
        sources = prepared['sources']; before = encoded(sources)
        purpose = json.loads(prior['requests'][0]['request']['messages'][1]['content'])['purpose']
        packet = api.build(purpose, sources)
        self.assertEqual(len(sources), 13)
        self.assertEqual(len(packet['inline_record_bodies']), 12)
        occurrences, jobs = 0, 0
        for index in (3, 4, 11):
            old = prior['views'][index]['content']; new = packet['sources'][index]['content']
            self.assertEqual(new['body']['cohort'], old['body']['cohort'])
            jobs += len(old['body']['cohort']['jobs'])
            for original, rendered in zip(records(old), records(new), strict=True):
                occurrences += 1
                self.assertEqual({k: v for k, v in original.items() if k != 'body'},
                                 {k: v for k, v in rendered.items() if k != 'body'})
                self.assertEqual(packet['inline_record_bodies'][original['id']]['body'], original['body'])
        self.assertEqual((occurrences, jobs), (27, 30))
        for index in (0, 1, 2, 6, 7, 8, 9, 10):
            self.assertEqual(packet['sources'][index], prior['views'][index])
        expanded = api.verify(packet, purpose, sources)
        self.assertNotIn('inline_record_bodies', expanded)
        for path in PATHS:
            self.assertEqual(at(expanded['sources'][11]['content'], path)['tool'], TOOL)
            recovered, offset = [], 0
            while True:
                page = api.ancestry_section(sources[11], list(path), offset, 13)
                self.assertEqual(page, expected_page(sources[11], path, offset, 13))
                recovered.extend(page['values'])
                if page['next_offset'] is None:
                    break
                offset = page['next_offset']
            put(expanded['sources'][11]['content'], path, recovered)
        self.assertEqual(encoded(expanded['sources']), encoded(prior['views']))
        for source, view in zip(sources, expanded['sources'], strict=True):
            self.assertEqual(encoded(restore_markers(view['content'], source)), encoded(source))
        self.assertEqual(encoded(sources), before)


if __name__ == '__main__':
    unittest.main()
