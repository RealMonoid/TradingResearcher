"""Independent fixed host-input metadata amendment controls, not qualification.

The original47-host ZIP remains the historical golden source. One separately
observed fixed Windows component is prospective source data; neither these
tests nor that source data establish runtime/numerical/scientific admission.
No Registry, numerical child, host mutation or native binary is used here.
"""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from trading_researcher import native_qualification_profile as profile
from trading_researcher import native_environment
from trading_researcher.codec import Invalid


ROOT = Path(__file__).resolve().parents[1]
BASE_FILE = 'tests/fixtures/native-environment-checks-2026-11-02.zip'
BASE_SHA = 'fda1c157fbf365f5a8826a9ba0e9f7d19fae5f36f7299bf7a770a9764524fd30'
BASE_IMAGES_SHA = '6158af593a614efa70c3b3f1ff43ff7c441be34ba0289e5f938fcbf476e85d1c'
AMENDMENT_FILE = 'tests/fixtures/native-host-amendment-2026-11-03.json'
AMENDMENT_SHA = 'c9ff91a14403bf05676857e9d25e9991402a6be004fcac646fd0abc587660988'
ADDITION = {'path': 'C:\\Windows\\System32\\apphelp.dll',
    'sha256': 'b838911cb7279ba34a5092d35037223188c452cf282d03a2e70b7242c9516bb2', 'size': 678520}


class NativeHostAmendmentIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_raw = (ROOT / BASE_FILE).read_bytes()
        assert hashlib.sha256(cls.base_raw).hexdigest() == BASE_SHA
        with ZipFile(io.BytesIO(cls.base_raw)) as archive:
            cls.base_images = json.loads(archive.read(
                '.trf-runtime/native-runtime-2026-11-02/environment-reference-observation.json'))['host_images']
        assert len(cls.base_images) == 47
        cls.amendment_raw = (ROOT / AMENDMENT_FILE).read_bytes()
        assert hashlib.sha256(cls.amendment_raw).hexdigest() == AMENDMENT_SHA

    def test_current_capture_uses_exact_48_hosts_without_changing_the_historical_47(self):
        source = profile.capture_source()
        actual = profile.host_inputs(source)
        self.assertEqual(len(actual), 48)
        self.assertEqual(actual, self.base_images + [ADDITION])
        self.assertEqual(source[BASE_FILE], self.base_raw)
        self.assertEqual(hashlib.sha256(source[AMENDMENT_FILE]).hexdigest(), AMENDMENT_SHA)

    def source(self):
        return {BASE_FILE: self.base_raw, AMENDMENT_FILE: self.amendment_raw}

    def malformed(self, transform):
        value = json.loads(self.amendment_raw)
        transformed = transform(value)
        if transformed is not None: value = transformed
        raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
        source = {BASE_FILE: self.base_raw, AMENDMENT_FILE: raw}
        # Explicit trusted test-source pin substitution ONLY for malformed
        # negative metadata. It prevents the byte-pin guard from making the
        # structural checks vacuous; no candidate is qualified or executed.
        with patch.object(profile, 'FIXED', {**profile.FIXED,
                AMENDMENT_FILE: hashlib.sha256(raw).hexdigest()}):
            with self.assertRaises(Invalid): profile.host_inputs(source)

    def test_historical_source_without_amendment_keeps_exact_old47_and_legacy_paths(self):
        self.assertEqual(profile.host_inputs({BASE_FILE: self.base_raw}), self.base_images)
        independent = json.dumps(self.base_images, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        self.assertEqual(hashlib.sha256(independent).hexdigest(), BASE_IMAGES_SHA)
        self.assertEqual(profile.FIXED[BASE_FILE], BASE_SHA)
        self.assertEqual((ROOT / BASE_FILE).read_bytes(), self.base_raw)
        self.assertNotIn(AMENDMENT_FILE, profile.source_paths('stationary-native-runtime/1'))
        self.assertIn(AMENDMENT_FILE, profile.source_paths('stationary-native-runtime/2'))
        self.assertEqual(profile.KNOWN_PROFILES, frozenset({'stationary-native-runtime/1', 'stationary-native-runtime/2'}))

    def test_fixed_asset_binds_only_reviewed_member_and_independent_provenance(self):
        value = json.loads(self.amendment_raw)
        self.assertEqual(profile.HOST_AMENDMENT_FILE, AMENDMENT_FILE)
        self.assertEqual(profile.HOST_AMENDMENT_SHA, AMENDMENT_SHA)
        self.assertEqual(profile.FIXED[AMENDMENT_FILE], AMENDMENT_SHA)
        self.assertEqual(set(value), {'schema', 'id', 'authority', 'base_archive_sha256',
            'base_host_images_sha256', 'additions', 'provenance'})
        self.assertEqual(value['schema'], 'native-host-input-amendment/1')
        self.assertEqual(value['id'], 'windows-host-inputs/2026-11-03.1')
        self.assertEqual(value['authority'], 'technical_host_inputs_only_not_runtime_or_scientific_admission')
        self.assertEqual(value['base_archive_sha256'], BASE_SHA)
        self.assertEqual(value['base_host_images_sha256'], BASE_IMAGES_SHA)
        self.assertEqual(value['additions'], [ADDITION])
        expected = {'independent_observation_receipt': 'native-host-import-observation-independent.json',
            'independent_observation_sha256': '4446e1e9d4f62e281215fb846ff31f22258488b886703447be68180db054fdfd',
            'independent_proposal_receipt': 'native-host-amendment-independent-proposal.json',
            'independent_proposal_sha256': '1b14cd3e9e3d2c439678595b810946fd81a8b889577a318d3292722d8ba01e29',
            'origin_observation_receipt': 'native-reference-clock-host-signature.json',
            'origin_observation_sha256': 'd2e1773221047671da65a91abff00268b1819bcd9e0ec00b48a2182c3b440809'}
        self.assertEqual(set(value['provenance']), set(expected) | {'scope'})
        for key, expected_value in expected.items(): self.assertEqual(value['provenance'][key], expected_value)
        self.assertIn('not the exact failed-child inventory or a runtime certificate', value['provenance']['scope'])

    def test_byte_mutation_is_denied_without_repinning_and_base_bytes_never_change(self):
        source = self.source(); source[AMENDMENT_FILE] += b' '
        with self.assertRaises(Invalid): profile.host_inputs(source)
        source = self.source(); source[BASE_FILE] += b' '
        with self.assertRaises(Invalid): profile.host_inputs(source)
        self.assertEqual((ROOT / BASE_FILE).read_bytes(), self.base_raw)
        self.assertEqual((ROOT / AMENDMENT_FILE).read_bytes(), self.amendment_raw)

    def test_foreign_base_or_schema_authority_and_provenance_shapes_are_denied(self):
        variants = {
            'schema': lambda value: value.update(schema='native-host-input-amendment/999'),
            'id': lambda value: value.update(id='unreviewed-host-inputs'),
            'authority': lambda value: value.update(authority='scientifically_certified'),
            'archive': lambda value: value.update(base_archive_sha256='f' * 64),
            'host_digest': lambda value: value.update(base_host_images_sha256='f' * 64),
            'extra_verdict': lambda value: value.update(approved=True),
            'missing_provenance': lambda value: value.pop('provenance') and None,
            'extra_provenance': lambda value: value['provenance'].update(certified=True),
            'missing_provenance_key': lambda value: value['provenance'].pop('scope') and None,
            'not_object': lambda value: [],
        }
        for name, mutate in variants.items():
            with self.subTest(name=name): self.malformed(mutate)

    def test_extra_duplicate_alias_relative_or_traversing_host_paths_are_denied(self):
        variants = {
            'empty': lambda value: value.update(additions=[]),
            'duplicate': lambda value: value['additions'].append(deepcopy(ADDITION)),
            'foreign_member': lambda value: value['additions'][0].update(path='C:\\Windows\\System32\\unreviewed.dll'),
            'case_alias': lambda value: value['additions'][0].update(path='C:\\WINDOWS\\system32\\APPHELP.DLL'),
            'slash_alias': lambda value: value['additions'][0].update(path='C:/Windows/System32/apphelp.dll'),
            'relative': lambda value: value['additions'][0].update(path='apphelp.dll'),
            'traversal': lambda value: value['additions'][0].update(path='C:\\Windows\\System32\\..\\System32\\apphelp.dll'),
            'old_member_alias': lambda value: value['additions'][0].update(path=self.base_images[0]['path'].upper()),
            'bool_size': lambda value: value['additions'][0].update(size=True),
            'zero_size': lambda value: value['additions'][0].update(size=0),
            'extra_descriptor': lambda value: value['additions'][0].update(qualified=True),
        }
        for name, mutate in variants.items():
            with self.subTest(name=name): self.malformed(mutate)

    def test_source_reader_never_invents_members_from_process_or_host_files_and_returns_detached_data(self):
        source = self.source()
        with patch.object(native_environment, '_loaded_images', side_effect=AssertionError('No automatic process membership')), \
                patch.object(Path, 'read_bytes', side_effect=AssertionError('No runtime/provenance file read')):
            result = profile.host_inputs(source)
        self.assertEqual(result, self.base_images + [ADDITION])
        result[0]['sha256'] = 'f' * 64; result.append({'untrusted': True})
        self.assertEqual(profile.host_inputs(source), self.base_images + [ADDITION])
        self.assertEqual(source, self.source())

    def test_current_source_fits_existing_caps_and_all_numeric_profile_goldens_remain_fixed(self):
        source = profile.capture_source()
        self.assertEqual(len(source), 128)
        self.assertLessEqual(sum(map(len, source.values())), 16 * 1048576)
        self.assertEqual(profile.PROFILE, 'stationary-native-runtime/2')
        self.assertEqual(profile.MANIFEST_SHA, '20151908bc9fd2b09ac407caebc5d7bbc2f79016315b8b59d736d2427297c848')
        self.assertEqual(profile.ARCHIVE_SHA, '4d379ab0dc5d689445c1f720b967b923b8106af4184de1576418837c23853976')
        self.assertEqual(profile.KERNEL_SHA, '318b5a84c357902af965c154bd0652c837503e5783a156f506c13872e1639a36')
        self.assertEqual(profile.RESULT_SHA, '720ac237f2ad3e29a5a9d94191af68a90a549f476c6e0f2d5bae36b537901b09')
        self.assertEqual(profile.STREAM_SHA, '76c3fb49b827455afaf488104f0ee88788254446e4bcf1fad07f73b42cb4f533')
        self.assertEqual(profile.STREAM_SIZE, 15143319)
        self.assertEqual(profile.NUMERIC_PINS, {
            'trading_researcher/stationary_bootstrap.py': 'f6f1b27ca43acde60972caa3af2fbec082e324180b13cb60f4fb64142dfd8d57',
            'trading_researcher/native_backend.py': 'bae49af0078154886b9ac382505712793699afea8e1a23dc1a7f63c900a6d0ab',
            'trading_researcher/family_pipeline.py': 'c082918d76595f15a89c4607578c526eb5354619deccf7e991d9319d9095c0bb',
            'trading_researcher/study_pipeline.py': '2d8b00d6f4f3c5e52ae0f1569b0ad4f7bfef628943dab0e5107385ed73fbb8de'})


if __name__ == '__main__':
    unittest.main()
