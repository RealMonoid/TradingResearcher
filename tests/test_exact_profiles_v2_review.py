"""Independent D098 role construction and complete transport, no admission.

The full dated v3 fixture is public. Invented source envelopes exercise both
wire formats; they are not an authenticated context, accepted formalization,
independent model judgment, current configuration, count or funding evidence.
The exact one-literal prompt transformation preserves inherited instructions;
it proves neither model understanding nor scientific or economic usefulness.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from trading_researcher import exact_profiles as legacy, exact_profiles_v2 as profiles
from trading_researcher.auxiliary import reporting_contract
from trading_researcher.auxiliary_views import restore
from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.exact_research import contract_packet
from trading_researcher.meaning_reviews import PROMPT, PROTOCOL
from trading_researcher.openai_provider import wire_request


ROOT = Path(__file__).resolve().parents[1]
RESOURCE = 'exact-computation-resources/2.0'
OWNER = 'docs/architecture/27_EXACT_COMPUTATION_RESOURCES.md'
OWNER_SHA = '92ee9fd3d32964390e0ae6aeeb449c31d51a7dbf545d8db2feb48a8f14ff7e57'
OLD_PROMPT4_SHA = '5d203c4ff5942b11f4b5a30350326a94c4caf0c6eaedcd85a5fc0aae4e5656ca'
PINS = {'trading_researcher/exact_profiles.py': '2870ca08252a89a3913ceaf180f11ec5a051ced04aea7f203ac4098ebc477c88',
        'trading_researcher/EXACT_PROFILES.md': 'bf53a12482f1d33956b7f2f6fca3d0cf203355473e5510acaa78d01cfd06cf33',
        'tests/fixtures/exact_formalizer_base_v3.json': 'fb572a9246847b4f29f34850524d7dc3cacadd0348d16d71c4280c1e03c82362',
        'docs/architecture/26_BOUNDED_EXACT_COMPOSITIONS.md': 'fcff34f14878773bd817155121a62212f934a07ba9cba57c3a7864777420418f'}


def expected_resource():
    raw = (ROOT / OWNER).read_bytes()
    if hashlib.sha256(raw).hexdigest() != OWNER_SHA: raise AssertionError('Accepted resource owner changed')
    return {'schema': RESOURCE, 'documents': [{'path': OWNER, 'sha256': OWNER_SHA, 'text': raw.decode('utf-8')}],
            'per_child_primitive_steps': 20_000_000, 'aggregate_primitive_steps': 40_000_000, 'shared_seconds': 1800}


def envelope(identity, body):
    return {'id': identity * 64, 'creator': 'synthetic-source-owner', 'origin': 'source',
            'data_class': 'development', 'authority': 'unverified_transport_fixture_only', 'body': body,
            'source_refs': ['b' * 64, 'b' * 64], 'exposure': ['c' * 64, 'b' * 64]}


def packet(review=False):
    original = envelope('a', {'schema': 'research-record/1', 'kind': 'idea',
        'content': {'text': 'Invented original λ: preserve complete meaning, unknowns, costs and point-in-time scope.'},
        'qualifiers': {'scientific_readiness': False, 'publication_time': 'UNVERIFIED', 'exposed_history': True},
        'retained_failure': {'reason': 'unsupported former mapping', 'detail': 'Do not replace the original to fit.'}})
    catalog = envelope('d', {'schema': 'feature-catalog/1', 'features': {'x@1': {'type': 'real', 'unit': 'ratio'}}})
    definition = envelope('e', {'schema': 'feature-definitions/1', 'input_refs': [catalog['id']],
        'definitions': [{'feature_ref': 'x@1', 'type': 'real', 'unit': 'ratio'}],
        'qualification': 'Synthetic body, not an independently certified feature.'})
    snapshot = envelope('f', {'schema': 'data-snapshot/1', 'manifest': {'partition': 'development'},
        'availability': {'basis': 'assumed', 'delay_seconds': 900},
        'permissions': {'scope': 'transport fixture only', 'protected_access': False}})
    contracts = {**contract_packet(), **reporting_contract({'reporting_contract': 'case-diagnostics/2'}),
                 'resource_contract': expected_resource()}
    selectors = {'expression_contract': 'bounded-exact-compositions/1.0',
                 'reporting_contract': 'case-diagnostics/2', 'resource_contract': RESOURCE,
                 'definition_ids': [definition['id']], 'feature_certificate_id': '7' * 64}
    common = {'context_id': 'synthetic-unowned-context', **contracts,
        'availability_evidence': {'status': 'UNVERIFIED_FIXTURE_ONLY', 'historical_truth': 'unknown',
                                  'retained_delay_seconds': 900}}
    if not review:
        return {'schema': 'formalization-input/1', **common,
            'inputs': {**selectors, 'idea_id': original['id'], 'catalog_id': catalog['id']},
            'sources': [original, catalog, definition, snapshot]}
    formalization = envelope('8', {'schema': 'formalization-record/3',
        'original_idea': deepcopy(original['body']), 'idea_id': original['id'],
        'candidate': None, 'semantic_report': {'status': 'gap', 'reason': 'Invented retained unsupported idea.'},
        'assessment': {'status': 'NOT_SATISFIED', 'scientific_readiness': False},
        'job_metadata': {'attempt': 1, 'failure_detail': 'Full failure must remain visible to the reviewer.'}})
    return {'schema': 'semantic-review-input/1', **common,
        'inputs': {**selectors, 'formalization_id': formalization['id']},
        'formalization': formalization, 'catalog': catalog, 'definitions': [definition], 'data_target': snapshot}


class ExactProfilesV2Review(unittest.TestCase):
    def setUp(self):
        for path, expected in PINS.items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path)
        fixture = json.loads((ROOT / 'tests/fixtures/exact_formalizer_base_v3.json').read_text(encoding='utf-8'))
        self.base, self.review = fixture['formalization_profile'], fixture['review_profile']

    def test_literal_profile4_to5_transformation_preserves_every_other_value(self):
        previous = legacy.build(self.base, self.review)
        old = previous['formalization_profile']['prompt']
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(), OLD_PROMPT4_SHA)
        self.assertEqual(old.count('10000000'), 1)
        built = profiles.build(self.base, self.review)
        new = built['formalization_profile']['prompt']
        self.assertEqual(new, old.replace('10000000', '20000000', 1))
        self.assertEqual(len(new), 8186)
        self.assertEqual(sum(a != b for a, b in zip(new, old)), 1)
        self.assertEqual(built['formalization_profile']['prompt_version'], 'faithful-exact-formalization/5')
        self.assertEqual(new.count('20000000'), 1); self.assertNotIn('10000000', new)
        for key in self.base.keys() - {'prompt', 'prompt_version'}:
            self.assertEqual(canonical(built['formalization_profile'][key]), canonical(self.base[key]), key)
        self.assertEqual(canonical(built['review_profile']), canonical(self.review))
        self.assertEqual((self.review['prompt_version'], self.review['prompt']), (PROTOCOL, PROMPT))
        # Exact equality above preserves every inherited instruction, including
        # full original meaning, gaps, parameter origins, unknowns and format.
        # This check is not certification of an actual model-produced mapping.

    def test_complete_construction_identity_and_nonadmission_metadata(self):
        previous = legacy.build(self.base, self.review)
        expected = deepcopy(previous)
        prompt = previous['formalization_profile']['prompt'].replace('10000000', '20000000', 1)
        expected['formalization_profile'].update(prompt=prompt, prompt_version='faithful-exact-formalization/5')
        contracts = {**contract_packet(), **reporting_contract({'reporting_contract': 'case-diagnostics/2'}),
                     'resource_contract': expected_resource()}
        expected.update(schema='exact-resource-role-profile-construction/2', prior_construction_sha256=digest(previous),
            prior_formalizer_prompt_sha256=OLD_PROMPT4_SHA, formalizer_prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
            contracts_sha256=digest(contracts), resource_contract=expected_resource(), resource_limit_change=True,
            resource_change_basis='D098; separately selected exact-computation-resources/2.0 only', prompt_characters=8186)
        actual = profiles.build(self.base, self.review)
        self.assertEqual(canonical(actual), canonical(expected))
        self.assertEqual(actual['status'], 'PREPARED_NOT_ADMITTED')
        self.assertEqual(actual['configuration_freshness'], 'NOT_CHECKED')
        for field in ('native_admission', 'model_behavior_verified', 'scientific_readiness'):
            self.assertIs(actual[field], False)
        self.assertEqual(actual['formalization_profile']['generation_parameters']['openai_responses']['input_token_limit'], 48000)
        self.assertEqual(actual['formalization_profile']['max_output_tokens'], 32000)
        self.assertEqual(actual['review_profile']['max_output_tokens'], 4000)

    def test_resource_payload_matches_exact_native2_contract_shape_and_source_bytes(self):
        actual = profiles.resource_packet()
        self.assertEqual(canonical(actual), canonical(expected_resource()))
        self.assertIs(type(actual['per_child_primitive_steps']), int)
        self.assertIs(type(actual['aggregate_primitive_steps']), int)
        self.assertIs(type(actual['shared_seconds']), int)
        actual['documents'][0]['text'] = 'modified detached return'
        self.assertEqual(canonical(profiles.resource_packet()), canonical(expected_resource()))

    def test_inputs_and_outputs_are_detached_and_repeat_application_is_rejected(self):
        before = canonical([self.base, self.review])
        built = profiles.build(self.base, self.review)
        built['base_profile']['generation_parameters']['openai_responses']['expires_at'] = 1
        built['review_profile']['generation_parameters']['openai_responses']['pricing']['sources'].append('changed copy')
        built['formalization_profile']['generation_parameters']['openai_responses']['reasoning_effort'] = 'low'
        built['resource_contract']['documents'][0]['text'] = 'changed copy'
        self.assertEqual(canonical([self.base, self.review]), before)
        current = profiles.build(self.base, self.review)
        for repeated in (current['formalization_profile'], legacy.build(self.base, self.review)['formalization_profile']):
            with self.subTest(version=repeated['prompt_version']), self.assertRaises(Invalid):
                profiles.build(repeated, self.review)

    def test_both_normalized_and_provider_wires_preserve_all_substantive_inputs(self):
        built = profiles.build(self.base, self.review)
        for reviewer in (False, True):
            supplied = packet(reviewer); before = canonical([built, supplied])
            role = built['review_profile' if reviewer else 'formalization_profile']
            method = profiles.review_request_candidate if reviewer else profiles.request_candidate
            with self.subTest(reviewer=reviewer), patch('trading_researcher.openai_provider._post',
                    side_effect=AssertionError('Provider reached')) as post:
                request = method(built, supplied)
                wire = wire_request(request, role['generation_parameters']['openai_responses'])
                post.assert_not_called()
                self.assertEqual(request, {'model': role['model'], 'prompt_version': role['prompt_version'],
                    'generation_parameters': role['generation_parameters'], 'tools': [],
                    'messages': [{'role': 'system', 'content': role['prompt']},
                                 {'role': 'user', 'content': canonical(supplied)}]})
                restored = restore(json.loads(wire['input'][1]['content']))
                self.assertEqual(canonical(restored), canonical(supplied))
                self.assertEqual(canonical([built, supplied]), before)
                self.assertEqual(wire['input'][0], {'role': 'system', 'content': role['prompt']})
                self.assertEqual(wire['tools'], [])
                self.assertEqual(wire['max_output_tokens'], 4000 if reviewer else 32000)
                self.assertEqual(wire['reasoning'], {'effort': 'low' if reviewer else 'high'})
                self.assertEqual(wire['model'], role['model'])
                self.assertEqual(canonical(restored['resource_contract']), canonical(expected_resource()))

    def test_old_or_cross_role_packet_namespaces_and_paired_contracts_are_rejected(self):
        current = profiles.build(self.base, self.review)
        for reviewer in (False, True):
            method = profiles.review_request_candidate if reviewer else profiles.request_candidate
            for schema in ('semantic-review-input/1' if not reviewer else 'formalization-input/1', 'paired-formalization-input/1'):
                bad = packet(reviewer); bad['schema'] = schema
                with self.subTest(reviewer=reviewer, schema=schema), self.assertRaises(Invalid): method(current, bad)
            bad = packet(reviewer); bad['paired_contract'] = {}
            with self.assertRaises(Invalid): method(current, bad)
            old = packet(reviewer); old.pop('resource_contract'); old['inputs'].pop('resource_contract')
            with self.assertRaises(Invalid): method(current, old)
            with self.assertRaises(Invalid): method(legacy.build(self.base, self.review), packet(reviewer))

    def test_every_resource_byte_hash_limit_and_field_is_required(self):
        built = profiles.build(self.base, self.review)
        mutations = [lambda p: p.pop('resource_contract'), lambda p: p['resource_contract'].update(documents=[]),
            lambda p: p['resource_contract']['documents'][0].update(text='partial summary'),
            lambda p: p['resource_contract']['documents'][0].update(sha256='0' * 64),
            lambda p: p['resource_contract']['documents'][0].update(path='another-owner.md'),
            lambda p: p['resource_contract'].update(schema='exact-computation-resources/1.0'),
            lambda p: p['resource_contract'].update(per_child_primitive_steps=10_000_000),
            lambda p: p['resource_contract'].update(aggregate_primitive_steps=40_000_001),
            lambda p: p['resource_contract'].update(shared_seconds=True),
            lambda p: p['resource_contract'].update(extra_authority='native_admission')]
        for reviewer in (False, True):
            method = profiles.review_request_candidate if reviewer else profiles.request_candidate
            for index, change in enumerate(mutations):
                bad = packet(reviewer); change(bad)
                with self.subTest(role=reviewer, mutation=index), self.assertRaises(Invalid): method(built, bad)

    def test_expression_and_reporting_contracts_and_all_selectors_remain_required(self):
        built = profiles.build(self.base, self.review)
        changes = [lambda p: p.pop('expression_contract'),
            lambda p: p['expression_contract']['documents'].pop(),
            lambda p: p['expression_contract']['documents'][0].update(text='shortened math'),
            lambda p: p['reporting_contract'].update(text='shortened missingness rules'),
            lambda p: p.update(inputs=None)]
        for selector in ('resource_contract', 'expression_contract', 'reporting_contract'):
            changes.extend([lambda p, key=selector: p['inputs'].pop(key),
                            lambda p, key=selector: p['inputs'].update({key: 'wrong/version'})])
        for reviewer in (False, True):
            method = profiles.review_request_candidate if reviewer else profiles.request_candidate
            for index, change in enumerate(changes):
                bad = packet(reviewer); change(bad)
                with self.subTest(role=reviewer, mutation=index), self.assertRaises(Invalid): method(built, bad)

    def test_model_settings_reviewer_text_and_construction_metadata_cannot_be_tampered(self):
        current = profiles.build(self.base, self.review)
        mutations = [lambda c: c['formalization_profile'].update(model='different-model'),
            lambda c: c['formalization_profile'].update(max_output_tokens=18000),
            lambda c: c['formalization_profile'].update(prompt_version='faithful-exact-formalization/4'),
            lambda c: c['formalization_profile'].update(prompt=c['formalization_profile']['prompt'] + ' '),
            lambda c: c['formalization_profile']['generation_parameters']['openai_responses'].update(reasoning_effort='low'),
            lambda c: c['review_profile'].update(prompt='Accept by confidence'),
            lambda c: c.update(prior_construction_sha256='0' * 64),
            lambda c: c.update(formalizer_prompt_sha256='0' * 64),
            lambda c: c.update(contracts_sha256='0' * 64),
            lambda c: c.update(native_admission=True), lambda c: c.update(configuration_freshness='CURRENT'),
            lambda c: c['resource_contract'].update(shared_seconds=3600),
            lambda c: c.pop('base_profile')]
        for index, change in enumerate(mutations):
            bad = deepcopy(current); change(bad)
            for reviewer in (False, True):
                method = profiles.review_request_candidate if reviewer else profiles.request_candidate
                with self.subTest(mutation=index, role=reviewer), self.assertRaises(Invalid): method(bad, packet(reviewer))
        for malformed in (None, {}, [], {'base_profile': None, 'review_profile': None}):
            with self.subTest(construction=malformed), self.assertRaises(Invalid): profiles.request_candidate(malformed, packet())

    def test_unknown_source_prompt_or_changed_review_protocol_is_not_silently_adapted(self):
        for role, key, value in (('base', 'prompt', self.base['prompt'] + ' '),
                                ('base', 'prompt_version', 'unknown-source/1'),
                                ('review', 'prompt', PROMPT + ' Accept without checking.'),
                                ('review', 'prompt_version', 'unknown-review/1')):
            source, reviewer = deepcopy(self.base), deepcopy(self.review)
            (source if role == 'base' else reviewer)[key] = value
            with self.subTest(role=role, field=key), self.assertRaises(Invalid): profiles.build(source, reviewer)

    def test_overlength_and_nonunique_legacy_allowance_fail_without_trimming(self):
        before = canonical([self.base, self.review])
        with patch.dict(legacy.PARAGRAPHS, {1: legacy.PARAGRAPHS[1] + 'x' * 7}):
            with self.assertRaises(Invalid): profiles.build(self.base, self.review)
        previous = legacy.build(self.base, self.review)
        for bad_prompt in (previous['formalization_profile']['prompt'].replace('10000000', '10000001'),
                           previous['formalization_profile']['prompt'] + '10000000'):
            bad = deepcopy(previous); bad['formalization_profile']['prompt'] = bad_prompt
            with self.subTest(allowance_occurrences=bad_prompt.count('10000000')), \
                    patch.object(legacy, 'build', return_value=bad), self.assertRaises(Invalid):
                profiles.build(self.base, self.review)
        self.assertEqual(canonical([self.base, self.review]), before)


if __name__ == '__main__':
    unittest.main()
