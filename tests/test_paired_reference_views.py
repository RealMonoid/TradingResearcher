"""Exact paired projection, preservation, bounds and access-first primitives."""
from copy import deepcopy
import hashlib
import json
import unittest

from trading_researcher.codec import Invalid, canonical
from trading_researcher.context_views import FEEDBACK_VIEW_PROFILE, source_view as old_view
from trading_researcher.errors import Denied
from trading_researcher.feedback import reference_views as api


def fixture(second=False):
    refs = [format(index, '064x') for index in range(34)]
    refs[9] = refs[2]
    return {'id': 'a'*64, 'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'data_class': 'development',
            'authority': 'paired_breakout_descriptive_feedback_only' if second else 'paired_descriptive_feedback_only',
            'source_refs': list(refs), 'exposure': list(refs),
            'body': {'schema': 'paired-breakout-development-feedback-manifest/1' if second else 'paired-development-feedback-manifest/1',
                     'cohort': {'artifact_ids': list(refs), 'jobs': [{'state': 'blocked', 'reason': 'Exact retained failure'}]},
                     'retained_research_records': [{'source_refs': list(refs), 'exposure': list(reversed(refs)),
                         'body': {'kind': 'gap', 'text': 'Original idea and unresolved meaning; '+('é,雪; '*900),
                                  'reason': 'Missing observations; not market falsification', 'nested_refs': list(refs)}}],
                     'scientific_readiness': False, 'qualification': 'Exposed descriptive development only.'}}


def at(value, path):
    for key in path:
        value = value[int(key)] if type(value) is list else value[key]
    return value


class Client:
    def __init__(self, source, denied=False):
        self.source, self.denied, self.calls = source, denied, []
    def call(self, operation, **arguments):
        self.calls.append((operation, arguments))
        if self.denied:
            raise Denied('Revoked source or invalid context/lease')
        return deepcopy(self.source)


class PairedReferenceViewTests(unittest.TestCase):
    def test_both_owned_schemas_preserve_all_substantive_content_and_source_bytes(self):
        for second in (False, True):
            source = fixture(second)
            before = canonical(source)
            result = api.source_view(source)
            self.assertEqual(result['schema'], 'discovery-paired-feedback-view/1')
            self.assertEqual(result['content']['body']['retained_research_records'][0]['body'], source['body']['retained_research_records'][0]['body'])
            self.assertEqual(result['content']['body']['cohort']['jobs'], source['body']['cohort']['jobs'])
            self.assertEqual(result['content']['body']['qualification'], source['body']['qualification'])
            self.assertIn('unread evidence', result['qualification'])
            self.assertIn('no additional access', result['qualification'])
            self.assertEqual(canonical(source), before)
            marker = result['content']['body']['cohort']['artifact_ids']
            self.assertEqual(marker['tool'], 'read_paired_feedback_references')
            expected_sha = hashlib.sha256(json.dumps(source['body']['cohort']['artifact_ids'], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
            self.assertEqual(marker['sha256'], expected_sha)
            self.assertEqual(marker['count'], 34)

    def test_exact_pages_reconstruct_duplicates_order_and_empty_end_without_aliasing(self):
        source = fixture()
        for path in (['body', 'cohort', 'artifact_ids'], ['body', 'retained_research_records', '0', 'source_refs'], ['body', 'retained_research_records', '0', 'exposure']):
            values = []
            for offset in (0, 13, 26, 34):
                page = api.reference_section(source, path, offset, 13)
                self.assertEqual(page['offset'], offset)
                self.assertEqual(page['count'], 34)
                self.assertLessEqual(len(canonical(page).encode()), 16384)
                values.extend(page['values'])
                page['values'].append('caller mutation')
            self.assertEqual(values, at(source, path))

    def test_only_exact_owner_schema_pairs_enable_new_paging(self):
        changes = [('creator', 'worker'), ('origin', 'external'), ('data_class', 'assessment'),
                   ('version', 'local-artifact/2'), ('authority', 'paired_breakout_descriptive_feedback_only')]
        for key, value in changes:
            source = fixture(); source[key] = value
            self.assertEqual(api.source_view(source)['content'], old_view(source, FEEDBACK_VIEW_PROFILE)['content'])
            with self.assertRaises(Invalid):
                api.reference_section(source, ['body', 'cohort', 'artifact_ids'], 0, 1)

    def test_no_arbitrary_nested_paths_or_noncanonical_indices(self):
        source = fixture()
        paths = [None, [], ['__class__'], ['body', 'cohort', 'jobs'],
                 ['body', 'retained_research_records', '0', 'body', 'nested_refs']]
        paths += [['body', 'retained_research_records', index, 'exposure'] for index in ('00', '-1', '+0', ' 0', '٠', '1', 0, True)]
        for path in paths:
            with self.subTest(path=path), self.assertRaises(Invalid):
                api.reference_section(source, path, 0, 1)

    def test_bounded_integer_controls_and_byte_limit_never_truncate(self):
        source = fixture(); path = ['body', 'cohort', 'artifact_ids']
        for offset, limit in ((True, 1), (-1, 1), (35, 1), (0, False), (0, 65), (0, 0), (0, '1')):
            with self.subTest(offset=offset, limit=limit), self.assertRaises(Invalid):
                api.reference_section(source, path, offset, limit)
        source['body']['cohort']['artifact_ids'] = ['雪'*6000]
        with self.assertRaises(Invalid):
            api.reference_section(source, path, 0, 1)
        self.assertEqual(source['body']['cohort']['artifact_ids'], ['雪'*6000])

    def test_nonstring_lists_remain_visible_and_are_not_pageable(self):
        for value in ([None, 'x'*1200], ['x'*1200, 2], {'id': 'x'}, None):
            source = fixture(); source['body']['cohort']['artifact_ids'] = value
            self.assertEqual(api.source_view(source)['content']['body']['cohort']['artifact_ids'], value)
            with self.assertRaises(Invalid):
                api.reference_section(source, ['body', 'cohort', 'artifact_ids'], 0, 1)

    def test_authentication_precedes_path_inspection_and_never_follows_reference_ids(self):
        arguments = {'artifact_id': 'a'*64, 'path': [['malformed']], 'offset': True, 'limit': -1}
        client = Client(None, denied=True)
        with self.assertRaises(Denied):
            api.read_references(client, {'lease': 'revoked'}, arguments)
        self.assertEqual(client.calls, [('read_artifact', {'lease': {'lease': 'revoked'}, 'artifact_id': 'a'*64})])
        client = Client(fixture())
        arguments.update(path=['body', 'cohort', 'artifact_ids'], offset=3, limit=2)
        page = api.read_references(client, {'lease': 'valid'}, arguments)
        self.assertEqual(page['values'], fixture()['body']['cohort']['artifact_ids'][3:5])
        self.assertEqual(len(client.calls), 1)
        with self.assertRaises(Invalid):
            api.read_references(client, {}, {**arguments, 'follow_id': True})
        self.assertEqual(len(client.calls), 1)


if __name__ == '__main__':
    unittest.main()
