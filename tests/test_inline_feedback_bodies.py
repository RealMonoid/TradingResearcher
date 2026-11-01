"""Initial full-body visibility, exact expansion and typed ancestry transport."""
from copy import deepcopy
import hashlib
import json
import unittest

from trading_researcher.codec import Invalid, canonical
from trading_researcher.context_views import source_section, feedback_source_section
from trading_researcher.errors import Denied
from trading_researcher.feedback import inline_bodies as api
from trading_researcher.feedback import reference_views


def identity(value):
    return format(value, '064x')


def hash_value(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def record(value, kind='idea'):
    refs = [identity(index+100) for index in range(20)]
    return {'id': identity(value), 'creator': 'original-worker', 'authority': 'unverified_research_assertion',
        'source_refs': refs, 'exposure': list(reversed(refs)),
        'body': {'schema': 'research-record/1', 'kind': kind, 'content': {'text': 'Full original é 雪\n'*100,
            'reason': 'No missing observation may be replaced'}, 'scope': {'instrument': 'ETHUSDT'},
            'created_at': 1700, 'available_at': 1700}}


def source(value, family, records):
    schema, authority = api.MANIFESTS[family]
    refs = [identity(index+100) for index in range(20)]
    return {'id': identity(value), 'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
        'data_class': 'development', 'authority': authority, 'source_refs': refs, 'exposure': refs,
        'body': {'schema': schema, 'retained_research_records': deepcopy(records),
            'cohort': {'artifact_ids': refs, 'jobs': [{'state': 'blocked', 'detail': {'reason': 'Retain this older failure'}}]},
            'evidence_at_publication': {'data_use': {'schema': 'paired-data-use-assessment/1',
                'rights': {'status': 'permitted_development'}, 'model_training_exposure': 'UNKNOWN',
                'gaps': ['No independent confirmation'], 'prior_knowledge': {
                    'artifact_ids': refs, 'context_ids': list(reversed(refs)),
                    'protected_knowledge_ids': [], 'unresolved_exposure_refs': ['opaque:unknown']}}},
            'scientific_readiness': False, 'qualification': 'Descriptive, not scientific evidence.'}}


def restore(value, original):
    if type(value) is dict and value.get('schema') == 'deferred-source-list/1':
        section = {'read_source_section': source_section, 'read_feedback_references': feedback_source_section,
                   'read_paired_feedback_references': reference_views.reference_section,
                   'read_feedback_ancestry_references': api.ancestry_section}[value['tool']]
        result = []; offset = 0
        while True:
            page = section(original, value['path'], offset, 7)
            result.extend(page['values'])
            if page['next_offset'] is None:
                return result
            offset = page['next_offset']
    if type(value) is dict:
        return {key: restore(item, original) for key, item in value.items()}
    if type(value) is list:
        return [restore(item, original) for item in value]
    return value


class InlineBodyTests(unittest.TestCase):
    def fixtures(self):
        first, second = record(1), record(2, 'gap')
        return [source(10, 0, [first, second]), source(11, 2, [second, first])]

    def test_every_full_body_is_initially_inline_once_with_ordered_occurrences_and_bindings(self):
        originals = self.fixtures(); before = canonical(originals)
        packet = api.build('Original purpose', originals)
        self.assertEqual(packet['schema'], 'discovery-feedback-inline-bodies/1')
        self.assertEqual(set(packet['inline_record_bodies']), {identity(1), identity(2)})
        for original in originals:
            for original_record in original['body']['retained_research_records']:
                entry = packet['inline_record_bodies'][original_record['id']]
                self.assertEqual(entry, {'body': original_record['body'], 'body_sha256': hash_value(original_record['body'])})
        for original, view in zip(originals, packet['sources']):
            base = reference_views.source_view(original)
            for actual, prior in zip(view['content']['body']['retained_research_records'], base['content']['body']['retained_research_records']):
                self.assertEqual({key: value for key, value in actual.items() if key != 'body'},
                                 {key: value for key, value in prior.items() if key != 'body'})
                self.assertEqual(actual['body'], {'schema': 'inline-feedback-body-ref/1', 'record_id': prior['id'], 'body_sha256': hash_value(prior['body'])})
            self.assertEqual(view['content']['body']['cohort'], base['content']['body']['cohort'])
        self.assertEqual(canonical(originals), before)

    def test_expand_then_exact_pages_reconstruct_complete_original_envelopes(self):
        originals = self.fixtures()
        packet = api.build('Purpose', originals)
        expanded = api.verify(packet, 'Purpose', originals)
        for original, view in zip(originals, expanded['sources']):
            self.assertEqual(canonical(restore(view['content'], original)), canonical(original))
        data_use = expanded['sources'][1]['content']['body']['evidence_at_publication']['data_use']
        self.assertEqual(data_use['model_training_exposure'], 'UNKNOWN')
        self.assertEqual(data_use['gaps'], ['No independent confirmation'])
        self.assertEqual(data_use['prior_knowledge']['artifact_ids']['path'], list(api.ANCESTRY_PATHS[0]))

    def test_conflicting_body_or_immutable_binding_is_never_preferred(self):
        for key, value in (('body', record(3)['body'] | {'changed': True}), ('creator', 'other'),
                           ('authority', 'certified'), ('source_refs', []), ('exposure', [])):
            originals = self.fixtures()
            originals[1]['body']['retained_research_records'][1][key] = value
            with self.subTest(key=key), self.assertRaises(Invalid):
                api.build('Purpose', originals)

    def test_missing_extra_and_mismatched_targets_fail_closed(self):
        packet = api.build('Purpose', self.fixtures())
        for kind in ('missing', 'extra', 'hash', 'pointer', 'extra_field'):
            changed = deepcopy(packet)
            if kind == 'missing':
                del changed['inline_record_bodies'][identity(1)]
            elif kind == 'extra':
                changed['inline_record_bodies'][identity(99)] = deepcopy(changed['inline_record_bodies'][identity(1)])
            elif kind == 'hash':
                changed['inline_record_bodies'][identity(1)]['body_sha256'] = identity(0)
            elif kind == 'pointer':
                changed['sources'][0]['content']['body']['retained_research_records'][0]['body']['record_id'] = identity(2)
            else:
                changed['sources'][0]['content']['body']['retained_research_records'][0]['body']['extra'] = True
            with self.subTest(kind=kind), self.assertRaises(Invalid):
                api.expand(changed)

    def test_self_consistent_body_tampering_still_fails_binding_to_originals(self):
        originals = self.fixtures(); changed = api.build('Purpose', originals)
        entry = changed['inline_record_bodies'][identity(1)]
        entry['body']['content']['text'] = 'Tampered but self-consistent'
        entry['body_sha256'] = hash_value(entry['body'])
        for view in changed['sources']:
            for item in view['content']['body']['retained_research_records']:
                if item['id'] == identity(1):
                    item['body']['body_sha256'] = entry['body_sha256']
        api.expand(changed)  # Structure alone grants no source authenticity.
        with self.assertRaises(Invalid):
            api.verify(changed, 'Purpose', originals)

    def test_unknown_record_shapes_stay_inline_and_outputs_do_not_alias(self):
        originals = self.fixtures()
        unknown = record(3); unknown['body']['kind'] = 'observation'
        originals[0]['body']['retained_research_records'].append(unknown)
        packet = api.build('Purpose', originals)
        self.assertEqual(packet['sources'][0]['content']['body']['retained_research_records'][2]['body'], unknown['body'])
        expanded = api.expand(packet)
        expanded['sources'][0]['content']['body']['retained_research_records'][0]['body']['content']['text'] = 'Changed occurrence'
        self.assertNotEqual(expanded['sources'][1]['content']['body']['retained_research_records'][1]['body']['content']['text'], 'Changed occurrence')
        packet['inline_record_bodies'][identity(1)]['body']['content']['text'] = 'Caller mutation'
        self.assertNotEqual(originals[0]['body']['retained_research_records'][0]['body']['content']['text'], 'Caller mutation')

    def test_ancestry_paths_types_owners_and_bounds_are_exact(self):
        original = self.fixtures()[1]
        page = api.ancestry_section(original, list(api.ANCESTRY_PATHS[0]), 3, 4)
        self.assertEqual(page['values'], original['body']['evidence_at_publication']['data_use']['prior_knowledge']['artifact_ids'][3:7])
        for path, offset, limit in ((['body'], 0, 1), (list(api.ANCESTRY_PATHS[0]), True, 1),
                                    (list(api.ANCESTRY_PATHS[0]), 0, 65)):
            with self.assertRaises(Invalid):
                api.ancestry_section(original, path, offset, limit)
        with self.assertRaises(Invalid):
            api.ancestry_section(self.fixtures()[0], list(api.ANCESTRY_PATHS[0]), 0, 1)

    def test_parent_authorization_precedes_path_inspection(self):
        class Client:
            def __init__(self): self.calls = []
            def call(self, op, **args):
                self.calls.append((op, args)); raise Denied('Revoked')
        client = Client()
        with self.assertRaises(Denied):
            api.read_ancestry(client, {'lease': 'old'}, {'artifact_id': identity(11), 'path': [False], 'offset': True, 'limit': -1})
        self.assertEqual(client.calls, [('read_artifact', {'lease': {'lease': 'old'}, 'artifact_id': identity(11)})])


if __name__ == '__main__':
    unittest.main()
