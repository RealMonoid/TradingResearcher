"""Independent pre-materialization binding checks using invented native bytes.

Input currency checks retained metadata and current trusted host/Python inputs.
It cannot prove that a runtime cache exists or is fit for execution. The strict
current-use interface must independently keep checking every physical member.
No fixture binary is executable, imported, compiled, or loaded by this module.
"""
from contextlib import contextmanager, ExitStack
from copy import deepcopy
import builtins
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from test_native_environment_independent import (
    BASE, CORE, FILES, IDENTITY, KERNEL, REJECTED, RUNTIME_ID,
    EnvironmentFixture, descriptor, image, tree,
)
from trading_researcher import native_environment as native, native_runtime
from trading_researcher.codec import digest


class NativeInputBindingIndependentTests(EnvironmentFixture):
    def input_environment(self):
        """Author the observation directly, independently of the collector."""
        return {
            **deepcopy(BASE),
            'native_runtime': {
                'schema': 'native-bootstrap-environment/1',
                'runtime_id': RUNTIME_ID,
                'manifest_sha256': digest(self.manifest),
                'module_files': {
                    name: descriptor(FILES[name])
                    for name in ('numpy/__init__.py', CORE, KERNEL)
                },
                'runtime_images': {
                    name: descriptor(FILES[name])
                    for name in (CORE, KERNEL, 'numpy.libs/fixture.dll')
                },
                'host_images': [deepcopy(self.host_images[0])],
            },
        }

    def inputs(self, environment, **changes):
        # Shape/path cases isolate this existing legacy seam. A separate test
        # below exercises its actual Python/stdlib/isolation implementation.
        with patch.object(native, '_environment_current', return_value=True):
            return native.inputs_current(
                environment, changes.get('runtime_id', RUNTIME_ID),
                changes.get('manifest', self.manifest),
                changes.get('directory', self.directory),
                changes.get('host_images', self.host_images),
            )

    def reject_observation(self, observation):
        with self.assertRaises(REJECTED):
            self.context().validate_bindings(observation)
        environment = {**deepcopy(BASE), 'native_runtime': observation}
        self.assertIs(self.inputs(environment), False)

    @contextmanager
    def binding_effects_only(self, *cache_roots):
        """Permit current trusted hosts/Python files, deny cache I/O/effects."""
        roots = [self.directory.absolute(), *(Path(path).absolute() for path in cache_roots)]
        allowed = {Path(value['path']).absolute() for value in self.host_images}
        allowed.add(Path(sys.executable).absolute())
        allowed.update(Path(sys.base_prefix).absolute() / name
                       for name in IDENTITY['runtime_libraries'])
        original_open, original_builtin_open = Path.open, builtins.open
        original_scandir, original_walk, original_import = os.scandir, os.walk, builtins.__import__

        def checked_path(value):
            path = Path(value).absolute()
            self.assertFalse(any(path.is_relative_to(root) for root in roots),
                             f'Input binding accessed a physical runtime cache: {path}')
            return path

        def checked_open(path, *args, **kwargs):
            path = checked_path(path)
            self.assertIn(path, allowed, 'Only independently trusted host/Python bytes may be read')
            mode = args[0] if args else kwargs.get('mode', 'r')
            self.assertFalse(set(mode) & set('wax+'), 'Input validation attempted a write')
            return original_open(path, *args, **kwargs)

        def checked_builtin_open(path, *args, **kwargs):
            checked = checked_path(path)
            self.assertIn(checked, allowed, 'Unknown child path was opened')
            mode = args[0] if args else kwargs.get('mode', 'r')
            self.assertFalse(set(mode) & set('wax+'), 'Input validation attempted a write')
            return original_builtin_open(path, *args, **kwargs)

        def checked_scandir(path):
            checked_path(path)
            return original_scandir(path)

        def checked_walk(path, *args, **kwargs):
            checked_path(path)
            return original_walk(path, *args, **kwargs)

        def checked_import(name, *args, **kwargs):
            self.assertFalse(name == 'numpy' or name.startswith('numpy.')
                             or name == '_trf_stationary_native'
                             or name.startswith('_trf_stationary_native.'),
                             'Controller imported native runtime code')
            return original_import(name, *args, **kwargs)

        with ExitStack() as stack:
            stack.enter_context(patch.object(Path, 'open', checked_open))
            stack.enter_context(patch('builtins.open', checked_builtin_open))
            stack.enter_context(patch.object(os, 'scandir', checked_scandir))
            stack.enter_context(patch.object(os, 'walk', checked_walk))
            stack.enter_context(patch('builtins.__import__', side_effect=checked_import))
            for name in ('mkdir', 'touch', 'write_bytes', 'write_text', 'unlink', 'rmdir', 'rename', 'replace'):
                stack.enter_context(patch.object(Path, name, side_effect=AssertionError('Input check wrote a path')))
            for target, name in ((native, '_loaded_images'), (native, 'verify_tree'),
                                 (native.NativeContext, '_file'), (native_runtime, 'materialize')):
                stack.enter_context(patch.object(target, name,
                    side_effect=AssertionError(f'Input check invoked runtime operation {name}')))
            yield

    def test_absent_cache_allows_input_currency_but_never_full_currentness(self):
        environment = self.input_environment()
        absent = self.root / 'restored-cache-not-materialized' / RUNTIME_ID
        self.assertFalse(absent.exists())
        with self.binding_effects_only(absent):
            self.assertIs(self.inputs(environment, directory=absent), True)
            self.assertIs(self.context(directory=absent).validate_bindings(environment['native_runtime']), None)
        self.assertFalse(absent.exists())
        self.assertIs(self.current(environment, directory=absent), False)
        with self.assertRaises(REJECTED):
            self.context(directory=absent).validate(environment['native_runtime'])

    def test_input_check_neither_reads_cache_nor_loads_builds_enumerates_or_writes_it(self):
        environment = self.input_environment()
        absent = self.root / 'absent-runtime'
        before = tree(self.root)
        modules = set(sys.modules)
        with self.binding_effects_only(absent):
            self.assertIs(self.inputs(environment), True)
            self.assertIs(self.inputs(environment, directory=absent), True)
            self.assertIs(self.context().validate_bindings(environment['native_runtime']), None)
        self.assertEqual(tree(self.root), before)
        self.assertEqual({name for name in sys.modules if name not in modules
                          and (name == 'numpy' or name.startswith('numpy.')
                               or name.startswith('_trf_stationary_native'))}, set())

    def test_corrupt_missing_unobserved_and_extra_cache_bytes_are_not_execution_current(self):
        environment = self.input_environment()
        self.assertIs(self.current(environment), True)
        for name in ('numpy/__init__.py', CORE, 'numpy/_core/data.bin', 'other.py'):
            path = self.directory / name
            for missing in (False, True):
                with self.subTest(name=name, missing=missing):
                    if missing:
                        path.unlink()
                    else:
                        path.write_bytes(b'changed physical cache bytes')
                    with self.binding_effects_only():
                        self.assertIs(self.inputs(environment), True)
                        self.assertIs(self.context().validate_bindings(environment['native_runtime']), None)
                    self.assertIs(self.current(environment), False)
                    with self.assertRaises(REJECTED):
                        self.context().validate(environment['native_runtime'])
                    path.write_bytes(FILES[name])
        (self.directory / 'unexpected.bin').write_bytes(b'undeclared cache member')
        self.assertIs(self.inputs(environment), True)
        self.assertIs(self.current(environment), False)

    def test_bindings_keep_detached_constructor_inputs_and_recheck_observations(self):
        manifest, hosts = deepcopy(self.manifest), deepcopy(self.host_images)
        environment = self.input_environment()
        original = deepcopy(environment)
        context = self.context(manifest=manifest, hosts=hosts)
        manifest['files'].clear()
        hosts[0]['sha256'] = '0' * 64
        with self.binding_effects_only():
            self.assertIs(context.validate_bindings(environment['native_runtime']), None)
        self.assertEqual(environment, original)
        environment['native_runtime']['module_files'][CORE]['sha256'] = '0' * 64
        with self.assertRaises(REJECTED):
            context.validate_bindings(environment['native_runtime'])
        self.assertIs(context.validate_bindings(original['native_runtime']), None)

    def test_inputs_delegate_exact_legacy_base_and_stop_before_native_reads_on_failure(self):
        environment = self.input_environment()
        absent = self.root / 'absent-runtime'
        with patch.object(native, '_environment_current', return_value=True) as legacy:
            self.assertIs(native.inputs_current(environment, RUNTIME_ID, self.manifest, absent, self.host_images), True)
        legacy.assert_called_once_with(BASE)
        with patch.object(native, '_environment_current', return_value=False) as legacy, \
                patch.object(native, '_read', side_effect=AssertionError('Legacy failure read native files')):
            self.assertIs(native.inputs_current(environment, RUNTIME_ID, self.manifest, absent, self.host_images), False)
        legacy.assert_called_once_with(BASE)

    def test_real_legacy_runtime_stdlib_and_isolation_currency_remain_required(self):
        environment = self.input_environment()
        library = Path(sys.modules['pathlib'].__file__).resolve()
        library_name = library.relative_to(Path(sys.base_prefix).resolve()).as_posix()
        environment['standard_library'] = {library_name: descriptor(library.read_bytes())['sha256']}
        absent = self.root / 'absent-runtime'

        def actual(value):
            return native.inputs_current(value, RUNTIME_ID, self.manifest, absent, self.host_images)

        self.assertIs(actual(environment), True)
        variants = []
        bad = deepcopy(environment)
        bad['identity']['version'] += ' changed runtime identity'
        variants.append(bad)
        for libraries in ({}, {library_name: '0' * 64}, {'../unknown.dll': 'a' * 64},
                          {str(self.outside.absolute()): 'a' * 64},
                          {'Lib/site-packages/unknown.py': 'a' * 64}, []):
            bad = deepcopy(environment)
            bad['standard_library'] = libraries
            variants.append(bad)
        for flag in environment['isolation']:
            bad = deepcopy(environment)
            bad['isolation'][flag] = 0
            variants.append(bad)
        bad = deepcopy(environment)
        bad['isolation']['extra'] = 1
        variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(case=index), self.forbid_outside_read():
                self.assertIs(actual(bad), False)

    def test_extended_environment_requires_exact_four_key_plain_dictionary(self):
        environment = self.input_environment()

        class Mapping(dict):
            pass

        variants = [None, [], Mapping(environment), deepcopy(BASE)]
        for name in environment:
            bad = deepcopy(environment)
            del bad[name]
            variants.append(bad)
        variants.append({**environment, 'input_only': True})
        for index, bad in enumerate(variants):
            with self.subTest(case=index):
                self.assertIs(self.inputs(bad), False)

    def test_observation_schema_ids_fields_and_json_types_are_exact(self):
        original = self.input_environment()['native_runtime']
        variants = [None, [], 'native-bootstrap-environment/1']
        for name in original:
            bad = deepcopy(original)
            del bad[name]
            variants.append(bad)
        variants.append({**deepcopy(original), 'cache_optional': True})
        for field, values in (
            ('schema', ('native-bootstrap-environment/2', None, True)),
            ('runtime_id', ('b' * 64, 'A' * 64, 'a' * 63, None, True)),
            ('manifest_sha256', ('0' * 64, 'A' * 64, None, True)),
            ('module_files', ([], None, True)),
            ('runtime_images', ([], None, True)),
            ('host_images', ({}, None, True, tuple(original['host_images']))),
        ):
            for value in values:
                bad = deepcopy(original)
                bad[field] = value
                variants.append(bad)
        for index, bad in enumerate(variants):
            with self.subTest(case=index), self.forbid_outside_read():
                self.reject_observation(bad)

    def test_caller_runtime_manifest_identity_and_complete_manifest_fingerprint_are_bound(self):
        environment = self.input_environment()
        for runtime_id in ('b' * 64, 'a' * 63, 'A' * 64, True, None):
            with self.subTest(runtime_id=runtime_id):
                self.assertIs(self.inputs(environment, runtime_id=runtime_id), False)
        manifests = []
        for field, value in (('schema', 'native-runtime-files/2'), ('extra', 0)):
            bad = deepcopy(self.manifest)
            bad[field] = value
            manifests.append(bad)
        bad = deepcopy(self.manifest)
        bad['runtime_identity']['version'] += ' changed runtime identity'
        manifests.append(bad)
        bad = deepcopy(self.manifest)
        bad['dependencies']['fictional-runtime']['version'] = '2.0'
        manifests.append(bad)
        bad = deepcopy(self.manifest)
        bad['files']['other.py'] = descriptor(b'changed unobserved retained bytes')
        manifests.append(bad)
        bad = deepcopy(self.manifest)
        bad['files'][CORE]['size'] = True
        manifests.append(bad)
        for index, bad in enumerate(manifests):
            with self.subTest(manifest=index):
                self.assertIs(self.inputs(environment, manifest=bad), False)

    def test_selected_file_descriptors_require_exact_types_shapes_hashes_and_sizes(self):
        original = self.input_environment()['native_runtime']
        for field in ('module_files', 'runtime_images'):
            for value in (None, [], True,
                          {'sha256': descriptor(FILES[CORE])['sha256']},
                          {'size': len(FILES[CORE])},
                          {**descriptor(FILES[CORE]), 'extra': 0},
                          {'sha256': 'A' * 64, 'size': len(FILES[CORE])},
                          {'sha256': '0' * 64, 'size': len(FILES[CORE])},
                          {'sha256': True, 'size': len(FILES[CORE])},
                          {'sha256': descriptor(FILES[CORE])['sha256'], 'size': True},
                          {'sha256': descriptor(FILES[CORE])['sha256'], 'size': -1},
                          {'sha256': descriptor(FILES[CORE])['sha256'], 'size': '1'},
                          {'sha256': descriptor(FILES[CORE])['sha256'], 'size': 1.0},
                          {'sha256': descriptor(FILES[CORE])['sha256'], 'size': len(FILES[CORE]) + 1}):
                bad = deepcopy(original)
                bad[field][CORE] = value
                with self.subTest(field=field, descriptor=value):
                    self.reject_observation(bad)

    def test_manifest_membership_does_not_expand_allowed_module_or_image_namespaces(self):
        original = self.input_environment()['native_runtime']
        invalid = {
            'module_files': ('other.py', 'numpy/LICENSE.txt', 'numpy/_core/data.bin',
                             'numpy.libs/fixture.dll', 'numpy/_core/old.cp313-win_amd64.pyd',
                             'provenance/extra.dll'),
            'runtime_images': ('other.py', 'numpy/__init__.py', 'numpy/LICENSE.txt',
                               'numpy/_core/data.bin', 'provenance/extra.dll'),
        }
        for field, names in invalid.items():
            for name in names:
                bad = deepcopy(original)
                bad[field] = {name: descriptor(FILES[name])}
                with self.subTest(field=field, member=name), self.binding_effects_only():
                    self.reject_observation(bad)

    def test_arbitrary_child_paths_are_rejected_before_any_unknown_file_is_opened(self):
        original = self.input_environment()['native_runtime']
        for field in ('module_files', 'runtime_images'):
            for name in ('../host/unqualified.dll', str(self.outside.absolute()),
                         '/absolute.dll', 'numpy/../outside.py', 'numpy/undeclared.py',
                         'numpy//__init__.py', 'numpy\\__init__.py'):
                bad = deepcopy(original)
                bad[field] = {name: descriptor(b'unknown child file')}
                with self.subTest(field=field, path=name), self.binding_effects_only():
                    self.reject_observation(bad)
        bad = deepcopy(original)
        bad['host_images'] = [{**deepcopy(self.host_images[0]), 'path': str(self.outside.absolute())}]
        with self.binding_effects_only():
            self.reject_observation(bad)

    def test_host_observations_keep_exact_descriptor_membership_alias_and_bound_checks(self):
        original = self.input_environment()['native_runtime']
        invalid = []
        for change in ({'size': True}, {'size': -1}, {'size': '1'}, {'sha256': 'A' * 64},
                       {'sha256': '0' * 64}, {'path': 'relative.dll'}, {'extra': 0}):
            bad = deepcopy(original)
            bad['host_images'][0].update(change)
            invalid.append(bad)
        for hosts in ([self.host_images[0], self.host_images[0]],
                      [self.host_images[0], {**self.host_images[0], 'path': self.host_images[0]['path'].upper()}],
                      [deepcopy(self.host_images[0]) for _ in range(1025)]):
            bad = deepcopy(original)
            bad['host_images'] = hosts
            invalid.append(bad)
        for index, bad in enumerate(invalid):
            with self.subTest(case=index), self.binding_effects_only():
                self.reject_observation(bad)
        environment = self.input_environment()
        self.assertIs(self.inputs(environment, host_images=[]), False)
        self.assertIs(self.inputs(environment, host_images=[self.host_images[1]]), False)

    def test_actual_host_mutation_and_removal_invalidate_unchanged_claims_each_time(self):
        environment = self.input_environment()
        raw = self.host_a.read_bytes()
        for replacement in (b'x' * len(raw), b'different size', None):
            with self.subTest(replacement=replacement):
                if replacement is None:
                    self.host_a.unlink()
                else:
                    self.host_a.write_bytes(replacement)
                self.assertIs(self.inputs(environment), False)
                with self.assertRaises(REJECTED):
                    self.context().validate_bindings(environment['native_runtime'])
                self.host_a.write_bytes(raw)
                self.assertIs(self.inputs(environment), True)

    def test_explicit_qualified_host_hardlink_keeps_currency_and_alias_mutation_invalidates_it(self):
        environment = self.input_environment()
        alias = self.host / 'qualified-hardlink.dll'
        os.link(self.host_a, alias)
        self.assertGreater(self.host_a.stat().st_nlink, 1)
        self.assertIs(self.inputs(environment), True)
        alias.write_bytes(b'changed trusted host bytes through another link')
        self.assertIs(self.inputs(environment), False)
        with self.assertRaises(REJECTED):
            self.context().validate_bindings(environment['native_runtime'])

    def test_empty_selected_observations_and_qualified_host_subsets_keep_existing_meaning(self):
        environment = self.input_environment()
        environment['native_runtime']['module_files'] = {}
        environment['native_runtime']['runtime_images'] = {}
        for hosts in ([], [self.host_images[0]], [self.host_images[1]], self.host_images):
            environment['native_runtime']['host_images'] = deepcopy(hosts)
            with self.subTest(hosts=hosts), self.binding_effects_only():
                self.assertIs(self.inputs(environment), True)
                self.assertIs(self.context().validate_bindings(environment['native_runtime']), None)


if __name__ == '__main__':
    unittest.main()
