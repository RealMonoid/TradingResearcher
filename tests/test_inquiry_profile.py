"""Structural profile checks; these do not exercise model reasoning."""
from copy import deepcopy
from pathlib import Path
import unittest

from trading_researcher.codec import Invalid, digest
from trading_researcher.inquiry.profiles import build_profile, verify_profile
from trading_researcher.researcher import TOOL_DEFINITIONS


OWNER = Path(__file__).resolve().parents[1] / 'docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md'


def base_profile():
    return {'model': 'fixture/1', 'prompt_version': 'previous-discovery/1',
            'max_calls': 8, 'max_tokens': 80000, 'max_seconds': 60,
            'max_cost_units': 0, 'currency': 'NONE', 'mode': 'fixture',
            'prompts': {'first': 'Invent freely. Preserve original \u00e9 and e\u0301.',
                        'second': 'Independently explore; no peer scratch access.'},
            'tools': deepcopy(TOOL_DEFINITIONS), 'generation_parameters': {},
            'max_output_tokens': 4096, 'call_timeout_seconds': 10, 'max_retries': 0}


class InquiryProfileTests(unittest.TestCase):
    def setUp(self):
        self.owner = OWNER.read_bytes()

    def test_original_values_and_source_bytes_survive_without_shared_mutability(self):
        base = base_profile()
        before = deepcopy(base)
        bundle = build_profile(base, self.owner)
        profile = bundle['profile']
        self.assertEqual(base, before)
        self.assertEqual(profile['prompt_version'], 'discovery-inquiry-feedback/2')
        for name, prompt in base['prompts'].items():
            self.assertTrue(profile['prompts'][name].startswith(prompt + '\n\n'))
        for key in base.keys() - {'prompts', 'prompt_version'}:
            self.assertEqual(profile[key], base[key], key)
        self.assertEqual(bundle['manifest']['base_profile_sha256'], digest(base))
        self.assertEqual(bundle['manifest']['profile_sha256'], digest(profile))
        profile['tools'][0]['description'] = 'Changed copy'
        self.assertEqual(base, before)

    def test_both_effective_role_versions_change_without_changing_role_parameters(self):
        base = base_profile()
        base['perspective_profiles'] = {
            name: {'prompt_version': 'old-role/' + name, 'model': 'fixture/1',
                   'generation_parameters': {'reasoning': {'effort': 'low'}}}
            for name in base['prompts']}
        before = deepcopy(base)
        bundle = build_profile(base, self.owner)
        for name, settings in bundle['profile']['perspective_profiles'].items():
            self.assertEqual(settings['prompt_version'], 'discovery-inquiry-feedback/2')
            for key in settings.keys() - {'prompt_version'}:
                self.assertEqual(settings[key], before['perspective_profiles'][name][key])
        self.assertEqual(base, before)

    def test_wrong_contract_bytes_are_not_labeled_as_the_accepted_source(self):
        for raw in (b'', self.owner + b' ', self.owner.decode('utf-8')):
            with self.subTest(kind=type(raw).__name__), self.assertRaises(Invalid):
                build_profile(base_profile(), raw)

    def test_oversized_prompt_fails_instead_of_truncating_original_meaning(self):
        base = base_profile()
        base['prompts']['first'] = 'Original hypothesis instruction. ' * 250
        before = deepcopy(base)
        with self.assertRaises(Invalid):
            build_profile(base, self.owner)
        self.assertEqual(base, before)

    def test_bad_shapes_and_repeated_application_fail(self):
        for prompts in ({'first': 'Only one'}, {'first': 'a', 'second': 'b', 'third': 'c'},
                        {'first': '', 'second': 'b'}):
            base = base_profile()
            base['prompts'] = prompts
            with self.subTest(prompts=prompts), self.assertRaises(Invalid):
                build_profile(base, self.owner)
        bundle = build_profile(base_profile(), self.owner)
        with self.assertRaises(Invalid):
            build_profile(bundle['profile'], self.owner)

    def test_exact_verification_rejects_prompt_manifest_and_budget_substitution(self):
        base = base_profile()
        bundle = build_profile(base, self.owner)
        verify_profile(bundle, base, self.owner)
        for field in ('prompt', 'budget', 'manifest'):
            changed = deepcopy(bundle)
            if field == 'prompt':
                changed['profile']['prompts']['first'] = base['prompts']['first']
            elif field == 'budget':
                changed['profile']['max_calls'] += 1
            else:
                changed['manifest']['behavioral_cases_proven'] = ['AC-01']
            with self.subTest(field=field), self.assertRaises(Invalid):
                verify_profile(changed, base, self.owner)


if __name__ == '__main__':
    unittest.main()
