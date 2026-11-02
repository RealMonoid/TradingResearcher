"""Independent metadata-only native environment checks; no binary is loaded.

Invented module/image bytes live only in temporary directories. Process-loader
observations are injected, while trusted manifest/host membership and current
disk bytes remain separate. This is neither a runtime qualification nor a
scientific certificate. Legacy environment behavior is checked independently.
"""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import types
import unittest
from unittest.mock import patch

from trading_researcher import binding, native_environment as native
from trading_researcher.certification import _environment_current, _runtime_identity
from trading_researcher.codec import Invalid, digest
from trading_researcher.errors import Conflict


SUFFIX = sysconfig.get_config_var('EXT_SUFFIX')
assert type(SUFFIX) is str and SUFFIX
KERNEL = '_trf_stationary_native' + SUFFIX
CORE = 'numpy/_core/_fixture' + SUFFIX
RUNTIME_ID = hashlib.sha256(b'independently qualified fictional runtime').hexdigest()
IDENTITY = _runtime_identity()
ISOLATION = {'isolated': 1, 'no_site': 1, 'ignore_environment': 1, 'no_bytecode_writes': 1}
BASE = {'identity': IDENTITY, 'standard_library': {'metadata-only-fixture.py': 'a' * 64},
        'isolation': ISOLATION}
FILES = {'numpy/__init__.py': b'# fictional package bytes, never executed\n',
         CORE: b'fictional extension bytes, never loaded',
         'numpy.libs/fixture.dll': b'fictional vendor image, never loaded',
         KERNEL: b'fictional selected kernel, never loaded',
         'numpy/LICENSE.txt': b'Fictional fixture notice.\n',
         'numpy/_core/data.bin': b'not a module or image',
         'numpy/_core/old.cp313-win_amd64.pyd': b'wrong interpreter suffix',
         'provenance/extra.dll': b'not an allowed runtime image',
         'other.py': b'not an allowed runtime module'}
REJECTED = (Invalid, Conflict)


def descriptor(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def image(path):
    return {'path': str(path.absolute()), **descriptor(path.read_bytes())}


def tree(directory):
    return {path.relative_to(directory).as_posix(): path.read_bytes()
            for path in directory.rglob('*') if path.is_file()}


class EnvironmentFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root / 'runtime'
        for name, raw in FILES.items():
            path = self.directory / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        self.manifest = {'schema': 'native-runtime-files/1', 'runtime_identity': deepcopy(IDENTITY),
            'dependencies': {'fictional-runtime': {'version': '1.0',
                'distribution_sha256': hashlib.sha256(b'fictional acquisition').hexdigest(),
                'license_files': ['numpy/LICENSE.txt']}},
            'files': {name: descriptor(raw) for name, raw in FILES.items()}}
        self.host = self.root / 'host'; self.host.mkdir()
        self.host_a = self.host / 'qualified-a.dll'; self.host_a.write_bytes(b'qualified host A fixture')
        self.host_b = self.host / 'qualified-b.dll'; self.host_b.write_bytes(b'qualified host B fixture')
        self.outside = self.host / 'unqualified.dll'; self.outside.write_bytes(b'never authorize reading me')
        self.host_images = [image(self.host_a), image(self.host_b)]

    def context(self, *, manifest=None, directory=None, hosts=None, runtime_id=RUNTIME_ID):
        return native.NativeContext(runtime_id, self.manifest if manifest is None else manifest,
            self.directory if directory is None else directory,
            self.host_images if hosts is None else hosts)

    def observe(self, context=None, images=None):
        context = self.context() if context is None else context
        images = [image(self.host_a)] if images is None else images
        with patch.object(native, '_loaded_images', return_value=deepcopy(images)):
            return context.observation()

    def environment(self):
        context = self.context()
        self.assertIs(context.accepts('numpy', self.directory / 'numpy/__init__.py'), True)
        self.assertIs(context.accepts('_trf_stationary_native', self.directory / KERNEL), True)
        observation = self.observe(context, [image(self.host_a), image(self.directory / KERNEL),
                                             image(self.directory / 'numpy.libs/fixture.dll')])
        return {**deepcopy(BASE), 'native_runtime': observation}

    def current(self, environment, **changes):
        with patch.object(native, '_environment_current', return_value=True):
            return native.current(environment, changes.get('runtime_id', RUNTIME_ID),
                changes.get('manifest', self.manifest), changes.get('directory', self.directory),
                changes.get('host_images', self.host_images))

    def forbid_outside_read(self):
        original = Path.open
        outside = self.outside.absolute()

        def guarded(path, *args, **kwargs):
            if path.absolute() == outside:
                raise AssertionError('Unqualified child path was opened before membership validation')
            return original(path, *args, **kwargs)
        return patch.object(Path, 'open', guarded)


class NativeEnvironmentIndependentTests(EnvironmentFixture):
    def test_constructor_is_detached_metadata_and_does_not_inventory_or_load(self):
        given, hosts = deepcopy(self.manifest), deepcopy(self.host_images)
        original_import = __import__

        def no_native_import(name, *args, **kwargs):
            if name == 'numpy' or name.startswith('numpy.') or name == '_trf_stationary_native':
                raise AssertionError('Constructor attempted to import a native package')
            return original_import(name, *args, **kwargs)

        with patch.object(native, '_loaded_images', side_effect=AssertionError('Constructor inventoried images')), \
                patch('builtins.__import__', side_effect=no_native_import):
            context = self.context(manifest=given, hosts=hosts)
        given['files'].clear()
        hosts[0]['sha256'] = '0' * 64
        self.assertIs(context.accepts('numpy', self.directory / 'numpy/__init__.py'), True)
        observed = self.observe(context)
        self.assertEqual(observed['manifest_sha256'], digest(self.manifest))
        self.assertEqual(observed['host_images'], [image(self.host_a)])

    def test_runtime_id_host_descriptor_shapes_duplicates_and_bounds_are_exact(self):
        for runtime_id in ('a' * 63, 'A' * 64, True, ''):
            with self.subTest(runtime_id=runtime_id), self.assertRaises(REJECTED):
                self.context(runtime_id=runtime_id)
        variants = []
        for change in ({'size': True}, {'size': -1}, {'sha256': 'A' * 64},
                       {'path': 'relative.dll'}, {'extra': 0}):
            hosts = deepcopy(self.host_images); hosts[0].update(change); variants.append(hosts)
        variants.append([self.host_images[0], {**self.host_images[0], 'path': self.host_images[0]['path'].upper()}])
        variants.append([{**self.host_images[0], 'path': str(self.host / f'unused-{index}.dll')}
                         for index in range(1025)])
        variants.append([{**self.host_images[0], 'path': '/' + 'x' * (1024**2)}])
        variants.append(tuple(self.host_images))
        for index, hosts in enumerate(variants):
            with self.subTest(host_case=index), self.assertRaises(REJECTED):
                self.context(hosts=hosts)

    def test_only_selected_module_names_paths_suffixes_and_declared_bytes_are_handled(self):
        context = self.context()
        self.assertIs(context.accepts('numpy', self.directory / 'numpy/__init__.py'), True)
        self.assertIs(context.accepts('numpy.core.historical_alias', self.directory / CORE), True)
        self.assertIs(context.accepts('numpy._core.alias', self.directory / CORE), True)
        self.assertIs(context.accepts('_trf_stationary_native', self.directory / KERNEL), True)
        observed = self.observe(context)
        self.assertEqual(observed['module_files'], {
            'numpy/__init__.py': descriptor(FILES['numpy/__init__.py']),
            CORE: descriptor(FILES[CORE]), KERNEL: descriptor(FILES[KERNEL])})
        for name in ('numpyish', 'numpy_extra', 'other_plugin', '_trf_stationary_native_extra'):
            with self.subTest(unknown=name), self.forbid_outside_read():
                self.assertIs(context.accepts(name, self.outside), False)
        for name, relative in (('numpy.foo', 'other.py'), ('numpy.foo', 'numpy/_core/data.bin'),
                               ('numpy.foo', 'numpy/_core/old.cp313-win_amd64.pyd'),
                               ('_trf_stationary_native', CORE),
                               ('_trf_stationary_native.child', KERNEL)):
            with self.subTest(name=name, file=relative), self.assertRaises(REJECTED):
                context.accepts(name, self.directory / relative)
        with self.forbid_outside_read(), self.assertRaises(REJECTED):
            context.accepts('numpy.outside', self.outside)

    def test_handled_module_hash_size_and_missing_file_fail_instead_of_falling_through(self):
        for kind in ('changed', 'missing'):
            with self.subTest(kind=kind):
                context = self.context()
                path = self.directory / 'numpy/__init__.py'
                if kind == 'changed': path.write_bytes(b'changed bytes')
                else: path.unlink()
                with self.assertRaises(REJECTED): context.accepts('numpy', path)
                path.write_bytes(FILES['numpy/__init__.py'])

    def test_observation_rechecks_remembered_python_module_after_acceptance(self):
        context = self.context()
        path = self.directory / 'numpy/__init__.py'
        self.assertIs(context.accepts('numpy', path), True)
        path.write_bytes(b'changed Python module after acceptance, before observation')
        # This unchanged loader inventory cannot expose Python source drift;
        # observation must revalidate its remembered module binding itself.
        with patch.object(native, '_loaded_images', return_value=[image(self.host_a)]), \
                self.assertRaises(REJECTED):
            context.observation()

    def test_observation_records_only_exact_runtime_images_and_qualified_host_subset(self):
        context = self.context()
        images = [image(self.directory / CORE), image(self.directory / KERNEL),
                  image(self.directory / 'numpy.libs/fixture.dll'), image(self.host_b)]
        observed = self.observe(context, images)
        self.assertEqual(set(observed), {'schema', 'runtime_id', 'manifest_sha256',
                                        'module_files', 'runtime_images', 'host_images'})
        self.assertEqual(observed['schema'], 'native-bootstrap-environment/1')
        self.assertEqual(observed['runtime_id'], RUNTIME_ID)
        self.assertEqual(observed['manifest_sha256'], digest(self.manifest))
        self.assertEqual(observed['module_files'], {})
        self.assertEqual(observed['runtime_images'], {
            CORE: descriptor(FILES[CORE]), KERNEL: descriptor(FILES[KERNEL]),
            'numpy.libs/fixture.dll': descriptor(FILES['numpy.libs/fixture.dll'])})
        self.assertEqual(observed['host_images'], [image(self.host_b)])
        empty = self.observe(self.context(hosts=[]), [])
        self.assertEqual((empty['module_files'], empty['runtime_images'], empty['host_images']), ({}, {}, []))

    def test_unknown_or_nonimage_runtime_files_and_unqualified_host_images_reject(self):
        bad = [image(self.outside), image(self.directory / 'provenance/extra.dll'),
               image(self.directory / 'numpy/__init__.py'), image(self.directory / 'numpy/_core/data.bin'),
               {**image(self.host_a), 'sha256': '0' * 64},
               {**image(self.host_a), 'size': True}]
        for index, observed in enumerate(bad):
            with self.subTest(image=index), self.assertRaises(REJECTED):
                self.observe(images=[observed])

    def test_changed_host_and_runtime_image_bytes_fail_even_with_unchanged_claimed_descriptors(self):
        for path in (self.host_a, self.directory / 'numpy.libs/fixture.dll'):
            with self.subTest(path=path.name):
                context = self.context()
                claimed = image(path)
                original = path.read_bytes()
                path.write_bytes(b'different current disk bytes')
                with self.assertRaises(REJECTED): self.observe(context, [claimed])
                path.write_bytes(original)

    def test_late_module_imports_produce_a_new_detached_post_phase_observation(self):
        context = self.context()
        context.accepts('numpy', self.directory / 'numpy/__init__.py')
        early = self.observe(context)
        context.accepts('numpy._core.late', self.directory / CORE)
        late = self.observe(context, [image(self.host_a), image(self.directory / CORE)])
        self.assertNotIn(CORE, early['module_files'])
        self.assertNotIn(CORE, early['runtime_images'])
        self.assertEqual(late['module_files'][CORE], descriptor(FILES[CORE]))
        self.assertEqual(late['runtime_images'][CORE], descriptor(FILES[CORE]))
        late['module_files']['numpy/__init__.py']['sha256'] = '0' * 64
        self.assertEqual(self.observe(context)['module_files']['numpy/__init__.py'], descriptor(FILES['numpy/__init__.py']))

    def test_current_delegates_exact_legacy_base_without_inventorying_parent_process(self):
        environment = self.environment()
        with patch.object(native, '_environment_current', return_value=True) as legacy, \
                patch.object(native, '_loaded_images', side_effect=AssertionError('Parent image inventory is unrelated')):
            self.assertIs(native.current(environment, RUNTIME_ID, self.manifest, self.directory, self.host_images), True)
        legacy.assert_called_once_with(BASE)
        with patch.object(native, '_environment_current', return_value=False):
            self.assertIs(native.current(environment, RUNTIME_ID, self.manifest, self.directory, self.host_images), False)
        self.assertIs(self.current(deepcopy(BASE)), False)

    def test_current_rejects_changed_fields_boolean_sizes_and_untrusted_member_paths(self):
        original = self.environment()
        variants = []
        changed = deepcopy(original); changed['extra'] = True; variants.append(changed)
        changed = deepcopy(original); changed['native_runtime']['extra'] = True; variants.append(changed)
        for key, value in (('schema', 'native-bootstrap-environment/2'), ('runtime_id', 'b' * 64),
                           ('manifest_sha256', '0' * 64)):
            changed = deepcopy(original); changed['native_runtime'][key] = value; variants.append(changed)
        for field in ('module_files', 'runtime_images'):
            name = next(iter(original['native_runtime'][field]))
            for change in ({'size': True}, {'size': -1}, {'sha256': 'A' * 64}, {'extra': 1}):
                changed = deepcopy(original); changed['native_runtime'][field][name].update(change); variants.append(changed)
            for name in ('../unqualified.dll', '/absolute.dll', 'provenance/extra.dll', 'other.py'):
                changed = deepcopy(original)
                changed['native_runtime'][field][name] = descriptor(b'unknown')
                variants.append(changed)
        changed = deepcopy(original); changed['native_runtime']['host_images'].append(image(self.outside)); variants.append(changed)
        changed = deepcopy(original); changed['native_runtime']['host_images'][0]['size'] = True; variants.append(changed)
        for index, changed in enumerate(variants):
            with self.subTest(case=index), self.forbid_outside_read():
                self.assertIs(self.current(changed), False)
        with self.forbid_outside_read():
            changed = deepcopy(original)
            changed['native_runtime']['host_images'] = [image(self.host_a) | {'path': str(self.outside)}]
            self.assertIs(self.current(changed), False)

    def test_current_uses_complete_manifest_fingerprint_and_rechecks_every_cache_file(self):
        environment = self.environment()
        self.assertIs(self.current(environment), True)
        changed_manifest = deepcopy(self.manifest)
        changed_manifest['dependencies']['fictional-runtime']['version'] = '2.0'
        self.assertIs(self.current(environment, manifest=changed_manifest), False)
        self.assertIs(self.current(environment, runtime_id='b' * 64), False)
        for name in ('numpy/__init__.py', 'other.py'):
            with self.subTest(changed_file=name):
                path = self.directory / name
                path.write_bytes(b'changed after use, unchanged supplied fingerprint')
                self.assertIs(self.current(environment), False)
                path.write_bytes(FILES[name])
        (self.directory / 'unexpected.bin').write_bytes(b'undeclared post-use bytes')
        self.assertIs(self.current(environment), False)

    def test_same_runtime_bytes_can_be_checked_at_a_new_explicit_owned_directory(self):
        environment = self.environment()
        alternate = self.root / 'restored-runtime'
        shutil.copytree(self.directory, alternate)
        self.assertIs(self.current(environment, directory=alternate), True)

    def test_module_and_complete_cache_checks_reject_real_hardlinks(self):
        environment = self.environment()
        path = self.directory / CORE
        outside = self.root / 'hardlink-target.pyd'; outside.write_bytes(FILES[CORE])
        path.unlink(); os.link(outside, path)
        self.assertGreater(path.stat().st_nlink, 1)
        with self.assertRaises(REJECTED): self.context().accepts('numpy._core.fixture', path)
        self.assertIs(self.current(environment), False)
        self.assertEqual(outside.read_bytes(), FILES[CORE])

    def test_explicit_qualified_host_hardlink_is_allowed_but_alias_mutation_is_not(self):
        alias = self.host / 'qualified-a-hardlink-alias.dll'
        os.link(self.host_a, alias)
        self.assertGreater(self.host_a.stat().st_nlink, 1)
        self.assertEqual(alias.stat().st_ino, self.host_a.stat().st_ino)
        qualified = image(self.host_a)
        context = self.context()
        observed = self.observe(context, [qualified])
        self.assertEqual(observed['host_images'], [qualified])
        environment = {**deepcopy(BASE), 'native_runtime': observed}
        self.assertIs(self.current(environment), True)
        # All paths are invented owned temporary files. This models a legitimate
        # OS component-store hardlink without touching an actual system image.
        alias.write_bytes(b'changed through the second hardlink name')
        self.assertEqual(self.host_a.read_bytes(), b'changed through the second hardlink name')
        with self.assertRaises(REJECTED):
            self.observe(context, [qualified])
        self.assertIs(self.current(environment), False)

    @unittest.skipUnless(os.name == 'nt', 'Real Windows parent-junction qualification')
    def test_module_parent_and_runtime_root_junctions_are_rejected_without_target_changes(self):
        environment = self.environment()

        def junction(link, target):
            def literal(path):
                self.assertTrue(path.absolute().is_relative_to(self.root.absolute()))
                return "'" + str(path.absolute()).replace("'", "''") + "'"
            command = ("$ErrorActionPreference = 'Stop'; New-Item -ItemType Junction -Path "
                       + literal(link) + ' -Target ' + literal(target) + ' | Out-Null')
            result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(link.is_junction())

            def remove_link():
                self.assertTrue(link.absolute().is_relative_to(self.root.absolute()))
                if link.is_junction(): link.rmdir()
            self.addCleanup(remove_link)

        target = self.root / 'junction-parent-target'
        shutil.copytree(self.directory / 'numpy', target)
        before = tree(target)
        shutil.rmtree(self.directory / 'numpy')
        junction(self.directory / 'numpy', target)
        with self.assertRaises(REJECTED):
            self.context().accepts('numpy', self.directory / 'numpy/__init__.py')
        self.assertIs(self.current(environment), False)
        self.assertEqual(tree(target), before)
        normal = self.root / 'junction-root-target'
        for name, raw in FILES.items():
            path = normal / name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        alias = self.root / 'runtime-root-alias'; junction(alias, normal)
        before = tree(normal)
        try:
            context = self.context(directory=alias)
        except REJECTED:
            pass
        else:
            with self.assertRaises(REJECTED): context.accepts('numpy', alias / 'numpy/__init__.py')
        self.assertIs(self.current(environment, directory=alias), False)
        self.assertEqual(tree(normal), before)


class BindingNativeEnvironmentIndependentTests(EnvironmentFixture):
    """Exercise the existing binding owner with a small controlled module view."""
    def module_view(self, extra=None):
        stdlib = Path(sys.modules['pathlib'].__file__).resolve()
        expected = {binding.DRIVER: hashlib.sha256(Path(binding.__file__).read_bytes()).hexdigest()}
        modules = {'trading_researcher.binding': types.SimpleNamespace(__file__=binding.__file__),
                   'pathlib': types.SimpleNamespace(__file__=str(stdlib)),
                   'builtins': types.SimpleNamespace()}
        modules.update(extra or {})
        fake_sys = types.SimpleNamespace(base_prefix=sys.base_prefix, modules=modules,
            stdlib_module_names=sys.stdlib_module_names,
            flags=types.SimpleNamespace(isolated=1, no_site=1, ignore_environment=1), dont_write_bytecode=True)
        return expected, fake_sys

    def test_legacy_three_key_behavior_and_old_validator_remain_separate(self):
        expected, fake_sys = self.module_view()
        with patch.object(binding, 'sys', fake_sys):
            legacy = binding.environment(expected)
            explicit_none = binding.environment(expected, _native=None)
        self.assertEqual(legacy, explicit_none)
        self.assertEqual(set(legacy), {'identity', 'standard_library', 'isolation'})
        self.assertTrue(_environment_current(legacy))
        with patch.object(binding, 'sys', fake_sys), patch.object(native, '_loaded_images', return_value=[]):
            extended = binding.environment(expected, _native=self.context())
        self.assertEqual({key: value for key, value in extended.items() if key != 'native_runtime'}, legacy)
        self.assertFalse(_environment_current(extended))

    def test_explicit_context_handles_numpy_and_kernel_before_generic_paths(self):
        context = self.context()
        expected, fake_sys = self.module_view({
            'numpy': types.SimpleNamespace(__file__=str(self.directory / 'numpy/__init__.py')),
            'numpy._core.fixture': types.SimpleNamespace(__file__=str(self.directory / CORE)),
            '_trf_stationary_native': types.SimpleNamespace(__file__=str(self.directory / KERNEL))})
        with patch.object(binding, 'sys', fake_sys), \
                patch.object(native, '_loaded_images', return_value=[image(self.host_a), image(self.directory / CORE),
                                                                    image(self.directory / KERNEL)]):
            environment = binding.environment(expected, _native=context)
        self.assertEqual(set(environment), {'identity', 'standard_library', 'isolation', 'native_runtime'})
        self.assertEqual(set(environment['native_runtime']['module_files']), {'numpy/__init__.py', CORE, KERNEL})
        self.assertIs(self.current(environment), True)

    def test_known_missing_file_unknown_plugins_and_fake_context_are_not_exempted(self):
        for name in ('numpy', 'numpy._core.fixture', '_trf_stationary_native', '_trf_stationary_native.child'):
            with self.subTest(missing=name):
                expected, fake_sys = self.module_view({name: types.SimpleNamespace()})
                with patch.object(binding, 'sys', fake_sys), \
                        patch.object(native, '_loaded_images', return_value=[]), self.assertRaises(REJECTED):
                    binding.environment(expected, _native=self.context())
        expected, fake_sys = self.module_view({'unqualified_plugin': types.SimpleNamespace(__file__=str(self.outside))})
        for context in (None, self.context()):
            with patch.object(binding, 'sys', fake_sys), self.assertRaises(REJECTED):
                binding.environment(expected, _native=context)
        expected, fake_sys = self.module_view()
        forged = types.SimpleNamespace(accepts=lambda *args: True, observation=lambda: {'forged': True})
        with patch.object(binding, 'sys', fake_sys), self.assertRaises(REJECTED):
            binding.environment(expected, _native=forged)


if __name__ == '__main__':
    unittest.main()
