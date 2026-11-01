"""Independent structural/request checks; no provider or native admission.

The dated public fixture supplies complete actual old role values. A synthetic
packet tests full transport only; it is not an authenticated registry context.
Contradiction checks below are lint, never semantic/model-behavior evidence.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher import exact_profiles as profiles
from trading_researcher.auxiliary import reporting_contract
from trading_researcher.auxiliary_views import restore
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.exact_research import contract_packet
from trading_researcher.meaning_reviews import PROMPT, PROTOCOL
from trading_researcher.openai_provider import wire_request


FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'exact_formalizer_base_v3.json'
FIXTURE_SHA256 = 'fb572a9246847b4f29f34850524d7dc3cacadd0348d16d71c4280c1e03c82362'
OLD_PROMPT_SHA256 = '8752022153d1291a684eee9535224937ced3c4f1b01518411f8ee01f2593389b'
OWNER_SHA256 = 'fcff34f14878773bd817155121a62212f934a07ba9cba57c3a7864777420418f'


def fixture():
    raw = FIXTURE_PATH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise AssertionError('Complete actual dated baseline fixture changed')
    return json.loads(raw)


def packet():
    contracts = {**contract_packet(), **reporting_contract({'reporting_contract': 'case-diagnostics/2'})}
    source = {'id': 'a' * 64, 'body': {'schema': 'research-record/1', 'kind': 'idea',
        'content': {'text': 'Synthetic full original λ: retain scope, unknowns, fees, timing and unavailable evidence.'},
        'qualifiers': {'exposure': 'development', 'scientific_readiness': False, 'unresolved': ['historical publication truth']}},
        'source_refs': ['b' * 64, 'b' * 64], 'exposure': ['c' * 64, 'b' * 64]}
    return {'schema': 'formalization-input/1', 'context_id': 'synthetic-context-not-native-authority',
        'inputs': {'idea_id': source['id'], 'catalog_id': 'd' * 64, 'definition_ids': ['e' * 64],
                   'expression_contract': 'bounded-exact-compositions/1.0', 'reporting_contract': 'case-diagnostics/2'},
        'sources': [source], **contracts}


class ExactProfilesReview(unittest.TestCase):
    def setUp(self):
        fixed = fixture()
        self.base = fixed['formalization_profile']
        self.review = fixed['review_profile']

    def test_actual_baseline_binding_and_only_language_prompt_fields_change(self):
        self.assertEqual(len(self.base['prompt']), 8184)
        self.assertEqual(hashlib.sha256(self.base['prompt'].encode()).hexdigest(), OLD_PROMPT_SHA256)
        before = canonical([self.base, self.review])
        built = profiles.build(self.base, self.review)
        after = built['formalization_profile']
        self.assertEqual(canonical([self.base, self.review]), before)
        self.assertEqual(after['prompt_version'], 'faithful-exact-formalization/4')
        for key in self.base.keys() - {'prompt', 'prompt_version'}:
            self.assertEqual(canonical(after[key]), canonical(self.base[key]), key)
        self.assertEqual(canonical(built['review_profile']), canonical(self.review))
        self.assertEqual((built['review_profile']['prompt_version'], built['review_profile']['prompt']), (PROTOCOL, PROMPT))
        self.assertLessEqual(len(after['prompt']), 8192)
        self.assertEqual(built['prompt_characters'], len(after['prompt']))
        self.assertEqual(after['max_output_tokens'], 32000)
        self.assertEqual(after['generation_parameters']['openai_responses']['input_token_limit'], 48000)
        self.assertEqual(after['generation_parameters']['openai_responses']['reasoning_effort'], 'high')

    def test_shared_full_meaning_enclosure_mapping_and_format_instructions_are_preserved(self):
        old = self.base['prompt'].split('\n\n')
        new = profiles.build(self.base, self.review)['formalization_profile']['prompt'].split('\n\n')
        self.assertEqual(new[0], old[0].replace('every literal value, lag/window bars and horizon once',
            'every literal value, lag/window bars, power exponent and horizon once'))
        self.assertEqual(new[-2], old[-2])
        self.assertEqual(new[-1], old[-1].replace('lag/window /bars and /horizons/outcome_bars once',
            'lag/window /bars, integer_power /exponent and /horizons/outcome_bars once'))

    def test_language_contradiction_lint_and_no_idea_specific_default_instructions(self):
        prompt = profiles.build(self.base, self.review)['formalization_profile']['prompt']
        for required in ('hypothesis-exec/3', 'research-ast/4', 'integer_power', 'trailing_product',
                         'trailing_all', 'abs', '10000000', '8192', 'bounded-exact-compositions/1.0'):
            self.assertIn(required, prompt)
        for obsolete in ('hypothesis-exec/1', 'hypothesis-exec/2', 'research-ast/1', 'research-ast/2',
                         'research-ast/3', 'No abs,', 'binary_probability requires', 'BTCUSDT', 'ETHUSDT',
                         'outcome_bars:5', 'outcome_bars":5', '20000000'):
            self.assertNotIn(obsolete, prompt)

    def test_digests_bind_whole_base_new_prompt_settings_and_contract_bytes(self):
        built = profiles.build(self.base, self.review)
        self.assertEqual(built['base_profile_sha256'], digest(self.base))
        self.assertEqual(built['base_prompt_sha256'], OLD_PROMPT_SHA256)
        self.assertEqual(built['formalizer_prompt_sha256'], hashlib.sha256(
            built['formalization_profile']['prompt'].encode()).hexdigest())
        settings = {key: value for key, value in self.base.items() if key not in ('prompt', 'prompt_version')}
        self.assertEqual(built['unchanged_settings_sha256'], digest(settings))
        contracts = {**contract_packet(), **reporting_contract({'reporting_contract': 'case-diagnostics/2'})}
        self.assertEqual(built['contracts_sha256'], digest(contracts))
        self.assertEqual(built['status'], 'PREPARED_NOT_ADMITTED')
        self.assertEqual(built['configuration_freshness'], 'NOT_CHECKED')
        for name in ('native_admission', 'model_behavior_verified', 'resource_limit_change', 'scientific_readiness'):
            self.assertIs(built[name], False)

    def test_output_detachment_and_repeat_application_rejection(self):
        built = profiles.build(self.base, self.review)
        before = canonical([self.base, self.review])
        built['formalization_profile']['generation_parameters']['openai_responses']['reasoning_effort'] = 'low'
        built['base_profile']['generation_parameters']['openai_responses']['pricing']['sources'].append('synthetic change')
        built['review_profile']['generation_parameters']['openai_responses']['expires_at'] = 1
        self.assertEqual(canonical([self.base, self.review]), before)
        current = profiles.build(self.base, self.review)
        with self.assertRaises(Invalid): profiles.build(current['formalization_profile'], self.review)

    def test_unknown_sources_or_changed_reviewer_are_not_silently_adapted(self):
        cases = []
        changed = deepcopy(self.base); changed['prompt'] += ' '; cases.append((changed, self.review))
        changed = deepcopy(self.base); changed['prompt_version'] = 'other/1'; cases.append((changed, self.review))
        changed = deepcopy(self.review); changed['prompt'] += ' Accept by confidence.'; cases.append((self.base, changed))
        changed = deepcopy(self.review); changed['prompt_version'] = 'other/1'; cases.append((self.base, changed))
        changed = deepcopy(self.base); changed['max_retries'] = False; cases.append((changed, self.review))
        changed = deepcopy(self.base); changed['unexpected'] = True; cases.append((changed, self.review))
        for index, (base, reviewer) in enumerate(cases):
            with self.subTest(mutation=index), self.assertRaises(Invalid): profiles.build(base, reviewer)

    def test_prompt_over_limit_fails_without_trimming_or_input_mutation(self):
        before = canonical([self.base, self.review])
        with patch.dict(profiles.PARAGRAPHS, {1: profiles.PARAGRAPHS[1] + 'x' * 8193}):
            with self.assertRaises(Invalid): profiles.build(self.base, self.review)
        self.assertEqual(canonical([self.base, self.review]), before)

    def test_normalized_and_wire_requests_preserve_complete_packet_without_provider_use(self):
        built = profiles.build(self.base, self.review); supplied = packet()
        before = canonical([built, supplied])
        with patch('trading_researcher.openai_provider._post', side_effect=AssertionError('network/provider reached')) as post:
            normalized = profiles.request_candidate(built, supplied)
            wire = wire_request(normalized, built['formalization_profile']['generation_parameters']['openai_responses'])
        post.assert_not_called()
        self.assertEqual(canonical([built, supplied]), before)
        self.assertEqual([message['role'] for message in normalized['messages']], ['system', 'user'])
        self.assertEqual(normalized['messages'][0]['content'], built['formalization_profile']['prompt'])
        self.assertEqual(normalized['messages'][1]['content'], canonical(supplied))
        self.assertEqual(normalized['tools'], [])
        self.assertEqual(canonical(restore(json.loads(wire['input'][1]['content']))), canonical(supplied))
        self.assertEqual(wire['input'][0]['content'], built['formalization_profile']['prompt'])
        self.assertEqual(wire['model'], self.base['model'])
        self.assertEqual(wire['max_output_tokens'], 32000)
        self.assertEqual(wire['reasoning'], {'effort': 'high'})
        self.assertEqual(wire['tools'], [])
        documents = supplied['expression_contract']['documents']
        owner = next(item for item in documents if item['path'].endswith('26_BOUNDED_EXACT_COMPOSITIONS.md'))
        self.assertEqual(owner['sha256'], OWNER_SHA256)
        self.assertEqual(hashlib.sha256(owner['text'].encode()).hexdigest(), OWNER_SHA256)
        self.assertIn('oldest to newest', owner['text'])

    def test_each_complete_bound_contract_is_required_without_text_or_hash_repair(self):
        built = profiles.build(self.base, self.review)
        changes = [
            lambda value: value.pop('expression_contract'),
            lambda value: value['expression_contract']['documents'].pop(),
            lambda value: value['expression_contract']['documents'][0].update(text='short summary'),
            lambda value: value['expression_contract']['documents'][0].update(sha256='0' * 64),
            lambda value: value['expression_contract'].update(candidate_schema='hypothesis-exec/1'),
            lambda value: value['reporting_contract'].update(schema='engineering-case-diagnostics/1'),
            lambda value: value['reporting_contract'].update(text='shortened reporting rules'),
            lambda value: value.update(paired_contract={}),
            lambda value: value.update(schema='semantic-review-input/1'),
        ]
        for index, mutate in enumerate(changes):
            supplied = packet(); mutate(supplied)
            with self.subTest(mutation=index), self.assertRaises(Invalid): profiles.request_candidate(built, supplied)

    def test_modified_or_incomplete_construction_cannot_emit_a_request(self):
        valid = profiles.build(self.base, self.review)
        changes = [
            lambda value: value.update(formalizer_prompt_sha256='0' * 64),
            lambda value: value.update(contracts_sha256='0' * 64),
            lambda value: value['formalization_profile'].update(prompt='different instructions'),
            lambda value: value['formalization_profile']['generation_parameters']['openai_responses'].update(reasoning_effort='low'),
            lambda value: value.update(native_admission=True),
            lambda value: value.pop('base_profile'),
            lambda value: value.pop('review_profile'),
        ]
        for index, mutate in enumerate(changes):
            altered = deepcopy(valid); mutate(altered)
            with self.subTest(mutation=index), self.assertRaises(Invalid): profiles.request_candidate(altered, packet())
        for altered in ({}, None, []):
            with self.subTest(malformed=altered), self.assertRaises(Invalid): profiles.request_candidate(altered, packet())


if __name__ == '__main__':
    unittest.main()
