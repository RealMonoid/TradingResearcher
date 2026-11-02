"""Independent path/byte equivalence against the retained 028d946 verifier.

The oracle is extracted from the byte-pinned existing evidence archive, not
reimplemented from the candidate. Every tree and mutation is invented locally.
No qualification, Registry, provider or scientific series is executed.
"""
import ast
from collections import Counter
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from test_native_runtime_independent import archive, manifest, MEMBERS
from trading_researcher import native_runtime as runtime
from trading_researcher.codec import Invalid
from trading_researcher.errors import Conflict


EVIDENCE = Path(__file__).parent / 'fixtures/native-study-checks-2026-11-02.zip'
EVIDENCE_SHA = 'a28ae8461a2d13f9350b1d6265dfd570293ee2bc31a7d45812636129d04d0d69'
OLD_RUNTIME_SHA = '4f3a2097380a640c14dfeaa89c9e12a35aee54f7768aba251a795c21e8382e74'
OLD_STORAGE_SHA = 'fde301827d694328760be8571a19a2857a0039df00a3966adb98bc80971a20d6'
REPARSE = 0x400


def frozen_function(raw, name, namespace):
    node = next(item for item in ast.parse(raw).body if isinstance(item, ast.FunctionDef) and item.name == name)
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'retained-028d946/' + name, 'exec'), namespace)
    return namespace[name]


def stat_copy(value, **changes):
    result = {name: getattr(value, name) for name in dir(value) if name.startswith('st_')}
    result.update(changes)
    return types.SimpleNamespace(**result)


class NativeTreeVerificationIndependentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = EVIDENCE.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == EVIDENCE_SHA
        with ZipFile(EVIDENCE) as evidence:
            old_runtime = evidence.read('trading_researcher/native_runtime.py')
            old_storage = evidence.read('trading_researcher/storage.py')
        assert hashlib.sha256(old_runtime).hexdigest() == OLD_RUNTIME_SHA
        assert hashlib.sha256(old_storage).hexdigest() == OLD_STORAGE_SHA
        namespace = {'Path': Path, 'PurePosixPath': PurePosixPath, 'os': os, 'stat': stat,
                     'hashlib': hashlib, 'Conflict': Conflict, 'Invalid': Invalid,
                     'BLOCK': 1024**2, 'MAX_BLOB_BYTES': 512 * 1024**2}
        frozen_function(old_storage, '_contained', namespace)
        frozen_function(old_storage, '_hash_file', namespace)
        cls.oracle = staticmethod(frozen_function(old_runtime, 'verify_tree', namespace))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='trf-native-tree-independent-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.lstat = Path.lstat
        self.is_symlink = Path.is_symlink
        self.members = {**MEMBERS, 'example/deep/other.bin': b'Independent nested member.',
                        'flat.bin': b'Independent top-level member.'}

    def tree(self, name, *, members=None):
        directory = self.root / name
        for relative, raw in (self.members if members is None else members).items():
            path = directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        return directory

    def implementations(self):
        return (('historical', self.oracle), ('current', runtime.verify_tree))

    @contextmanager
    def wrapped_hash(self, verifier, wrapper):
        namespace = verifier.__globals__
        original = namespace['_hash_file']
        with patch.dict(namespace, {'_hash_file': lambda path: wrapper(original, path)}):
            yield

    def junction(self, link, target):
        self.assertTrue(link.absolute().is_relative_to(self.root))
        self.assertTrue(target.resolve().is_relative_to(self.root))
        self.assertTrue(target.is_dir())
        quote = lambda path: "'" + str(path).replace("'", "''") + "'"
        command = ('$ErrorActionPreference = \'Stop\'; New-Item -ItemType Junction -Path '
                   + quote(link) + ' -Target ' + quote(target) + ' | Out-Null')
        result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', command],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(link.is_junction())

        def remove_link():
            self.assertTrue(link.absolute().is_relative_to(self.root))
            if link.is_junction():
                link.rmdir()
        self.addCleanup(remove_link)

    def test_frozen_oracle_and_complete_ordinary_tree_agree(self):
        spec = manifest(self.members)
        for label, verify in self.implementations():
            with self.subTest(implementation=label):
                self.assertIsNone(verify(self.tree(label), spec))

    def test_every_file_is_fully_rehashed_on_every_call(self):
        for label, verify in self.implementations():
            with self.subTest(implementation=label):
                directory = self.tree(label)
                calls = []

                def capture(original, path):
                    calls.append(Path(path).relative_to(directory).as_posix())
                    return original(path)

                with self.wrapped_hash(verify, capture):
                    verify(directory, manifest(self.members))
                    verify(directory, manifest(self.members))
                self.assertEqual(Counter(calls), Counter({name: 2 for name in self.members}))

    @unittest.skipUnless(hasattr(runtime, '_tree_path'),
                         'Unselected candidate archived after inconclusive timing; implementation-specific counter only')
    def test_ordinary_absolute_members_prove_every_ancestor_fresh_without_resolve_per_member(self):
        directory = self.tree('ordinary')
        stats, delegated = Counter(), []
        old_contained = runtime._contained

        def observe(path, *args, **kwargs):
            stats[str(path).casefold()] += 1
            return self.lstat(path, *args, **kwargs)

        def contained(root, path):
            delegated.append((Path(root), Path(path)))
            return old_contained(root, path)

        with patch.object(Path, 'lstat', observe), patch.object(runtime, '_contained', contained):
            runtime.verify_tree(directory, manifest(self.members))
        self.assertEqual(delegated, [(directory.parent, directory)])
        for ancestor in (directory, *directory.parents):
            self.assertGreaterEqual(stats[str(ancestor).casefold()], len(self.members), str(ancestor))
        for relative in self.members:
            self.assertGreaterEqual(stats[str(directory / relative).casefold()], 2,
                                    'Containment metadata cannot replace the existing final leaf lstat')

    def test_relative_and_dotdot_root_spellings_keep_historical_fallback(self):
        directory = self.tree('relative')
        (self.root / 'wrapper').mkdir()
        previous = Path.cwd()
        try:
            os.chdir(self.root)
            for spelling in (Path('relative'), self.root / 'wrapper' / '..' / 'relative'):
                for label, verify in self.implementations():
                    with self.subTest(spelling=str(spelling), implementation=label):
                        if label == 'current':
                            with patch.object(runtime, '_contained', wraps=runtime._contained) as delegated:
                                verify(spelling, manifest(self.members))
                            self.assertGreater(delegated.call_count, 1)
                        else:
                            verify(spelling, manifest(self.members))
        finally:
            os.chdir(previous)
        self.assertTrue(directory.exists())

    def test_nonlexical_walker_member_is_rejected_before_opening_outside_bytes(self):
        directory = self.tree('nonlexical')
        outside = self.root / 'outside.bin'
        outside.write_bytes(b'Never open outside bytes.')
        spec = {'files': {'../outside.bin': {'sha256': hashlib.sha256(outside.read_bytes()).hexdigest(),
                                             'size': outside.stat().st_size}}}
        original_open = Path.open

        def guarded_open(path, *args, **kwargs):
            if path.resolve() == outside:
                self.fail('Containment check opened an outside member')
            return original_open(path, *args, **kwargs)

        for label, verify in self.implementations():
            with self.subTest(implementation=label), patch.object(os, 'walk',
                    return_value=iter([(str(directory), [], ['../outside.bin'])])), \
                    patch.object(Path, 'open', guarded_open):
                with self.assertRaises(Conflict):
                    verify(directory, spec)

    def test_unknown_leaf_reparse_metadata_delegates_without_inventing_new_rejection(self):
        directory = self.tree('unknown-leaf')
        victim = directory / 'example/data.bin'

        def observe(path, *args, **kwargs):
            value = self.lstat(path, *args, **kwargs)
            if path == victim:
                return stat_copy(value, st_file_attributes=getattr(value, 'st_file_attributes', 0) | REPARSE,
                                 st_reparse_tag=0x80001234)
            return value

        with patch.object(Path, 'lstat', observe), \
                patch.object(runtime, '_contained', wraps=runtime._contained) as delegated:
            runtime.verify_tree(directory, manifest(self.members))
        self.assertTrue(any(call.args == (directory, victim) for call in delegated.call_args_list))

    def test_unknown_ancestor_reparse_metadata_is_rechecked_after_directory_acceptance(self):
        directory = self.tree('unknown-ancestor')
        ancestor = directory / 'example'

        def observe(path, *args, **kwargs):
            value = self.lstat(path, *args, **kwargs)
            if path == ancestor:
                return stat_copy(value, st_file_attributes=getattr(value, 'st_file_attributes', 0) | REPARSE,
                                 st_reparse_tag=0x80004321)
            return value

        with patch.object(Path, 'lstat', observe), \
                patch.object(runtime, '_contained', wraps=runtime._contained) as delegated:
            runtime.verify_tree(directory, manifest(self.members))
        paths = [call.args[1] for call in delegated.call_args_list if call.args[0] == directory]
        for name in self.members:
            if name.startswith('example/'):
                self.assertIn(directory / name, paths)

    def test_metadata_error_above_cache_delegates_to_unchanged_historical_owner(self):
        directory = self.tree('ordinary')
        ancestor = self.root.parent

        def observe(path, *args, **kwargs):
            if path == ancestor:
                raise PermissionError('Invented inaccessible ancestor metadata')
            return self.lstat(path, *args, **kwargs)

        with patch.object(Path, 'lstat', observe):
            self.oracle(directory, manifest(self.members))
            with patch.object(runtime, '_contained', wraps=runtime._contained) as delegated:
                runtime.verify_tree(directory, manifest(self.members))
        paths = [call.args[1] for call in delegated.call_args_list if call.args[0] == directory]
        for name in self.members:
            self.assertIn(directory / name, paths)

    def test_leaf_stat_errors_propagate_instead_of_becoming_acceptance(self):
        for label, verify in self.implementations():
            for error in (PermissionError('Invented denial'), FileNotFoundError('Invented disappearance')):
                with self.subTest(implementation=label, error=type(error).__name__):
                    directory = self.tree(label + '-' + type(error).__name__)
                    victim = directory / 'example/data.bin'

                    def observe(path, *args, **kwargs):
                        if path == victim:
                            raise error
                        return self.lstat(path, *args, **kwargs)

                    with patch.object(Path, 'lstat', observe), self.assertRaises(type(error)):
                        verify(directory, manifest(self.members))

    def test_late_hardlink_created_during_ancestor_check_is_seen_by_final_leaf_stat(self):
        for label, verify in self.implementations():
            with self.subTest(implementation=label):
                directory = self.tree(label)
                victim = directory / 'example/data.bin'
                alias = self.root / (label + '-late-hardlink')
                state = {'leaf_seen': False, 'mutated': False}

                def mutate(path, value):
                    if path == victim:
                        state['leaf_seen'] = True
                    elif path == victim.parent and state['leaf_seen'] and not state['mutated']:
                        os.link(victim, alias)
                        state['mutated'] = True
                    return value

                def observe_stat(path, *args, **kwargs):
                    return mutate(path, self.lstat(path, *args, **kwargs))

                def observe_link(path):
                    return mutate(path, self.is_symlink(path))

                # The frozen Windows owner queries Path.is_symlink (which may
                # use native _path_islink); the candidate uses explicit lstat.
                # Mutate at the same boundary in either implementation.
                with patch.object(Path, 'lstat', observe_stat), \
                        patch.object(Path, 'is_symlink', observe_link), self.assertRaises(Conflict):
                    verify(directory, manifest(self.members))
                self.assertTrue(state['mutated'])
                self.assertEqual(self.lstat(victim).st_nlink, 2)

    @unittest.skipUnless(os.name == 'nt', 'Actual Windows junction semantics required')
    def test_real_junction_root_or_member_parent_is_refused_even_with_exact_bytes(self):
        for label, verify in self.implementations():
            for kind in ('root', 'member'):
                with self.subTest(implementation=label, kind=kind):
                    target = self.tree(label + '-' + kind + '-target')
                    if kind == 'root':
                        directory = self.root / (label + '-root-link')
                        self.junction(directory, target)
                    else:
                        directory = self.tree(label + '-member-tree')
                        moved = self.root / (label + '-member-before-link')
                        parent = directory / 'example'
                        self.assertTrue(moved.absolute().is_relative_to(self.root))
                        parent.rename(moved)
                        self.junction(parent, target / 'example')
                    with self.assertRaises(Conflict):
                        verify(directory, manifest(self.members))

    @unittest.skipUnless(os.name == 'nt', 'Actual Windows junction semantics required')
    def test_ancestor_outside_cache_changed_after_first_hash_is_not_cached_as_ordinary(self):
        members = {'example/LICENSE.txt': MEMBERS['example/LICENSE.txt'],
                   'one.bin': b'First ordinary member.', 'two.bin': b'Second unchanged bytes.'}
        for label, verify in self.implementations():
            with self.subTest(implementation=label):
                directory = self.tree(label + '-parent/tree', members=members)
                ancestor = directory.parent
                moved = self.root / (label + '-moved-parent')
                other = self.tree(label + '-other-parent/tree', members=members).parent
                mutated, hashed = [False], []

                def mutate(original, path):
                    result = original(path)
                    hashed.append(Path(path).name)
                    if not mutated[0]:
                        self.assertTrue(ancestor.resolve().is_relative_to(self.root))
                        self.assertTrue(moved.absolute().is_relative_to(self.root))
                        ancestor.rename(moved)
                        self.junction(ancestor, other)
                        mutated[0] = True
                    return result

                with self.wrapped_hash(verify, mutate), self.assertRaises(Conflict):
                    verify(directory, manifest(members))
                self.assertTrue(mutated[0])
                self.assertEqual(len(hashed), 1, 'A later member followed the newly linked ancestor')

    def test_same_size_content_rewrite_with_restored_mtime_is_rejected_on_next_call(self):
        for label, verify in self.implementations():
            with self.subTest(implementation=label):
                directory = self.tree(label)
                spec = manifest(self.members)
                verify(directory, spec)
                victim = directory / 'example/data.bin'
                before = victim.stat()
                victim.write_bytes(b'X' * len(self.members['example/data.bin']))
                os.utime(victim, ns=(before.st_atime_ns, before.st_mtime_ns))
                self.assertEqual(victim.stat().st_mtime_ns, before.st_mtime_ns)
                with self.assertRaises(Conflict):
                    verify(directory, spec)

    def test_missing_extra_wrong_type_wrong_hash_and_wrong_size_remain_failures(self):
        for label, verify in self.implementations():
            for defect in ('missing', 'extra-file', 'extra-directory', 'directory-member', 'hash', 'size'):
                with self.subTest(implementation=label, defect=defect):
                    directory = self.tree(label + '-' + defect)
                    spec = manifest(self.members)
                    member = directory / 'example/data.bin'
                    if defect == 'missing':
                        member.unlink()
                    elif defect == 'extra-file':
                        (directory / 'unknown.bin').write_bytes(b'Unexpected')
                    elif defect == 'extra-directory':
                        (directory / 'unknown-directory').mkdir()
                    elif defect == 'directory-member':
                        member.unlink(); member.mkdir()
                    elif defect == 'hash':
                        spec['files']['example/data.bin']['sha256'] = '0' * 64
                    else:
                        spec['files']['example/data.bin']['size'] += 1
                    with self.assertRaises(Conflict):
                        verify(directory, spec)

    def test_existing_hardlinked_member_is_refused_without_touching_its_alias(self):
        for label, verify in self.implementations():
            with self.subTest(implementation=label):
                directory = self.tree(label)
                victim = directory / 'example/data.bin'
                alias = self.root / (label + '-alias')
                os.link(victim, alias)
                before = alias.read_bytes()
                with self.assertRaises(Conflict):
                    verify(directory, manifest(self.members))
                self.assertEqual(alias.read_bytes(), before)

    def test_actual_materialize_and_cache_hit_keep_all_byte_guards_and_no_extra_writes(self):
        raw, spec = archive(self.members.items()), manifest(self.members)
        charges = []
        directory = runtime.materialize(raw, spec, self.root / 'cache', on_bytes=charges.append)
        self.assertEqual(charges, [len(value) for value in self.members.values()])
        self.oracle(directory, spec)
        hit = []
        self.assertEqual(runtime.materialize(raw, spec, self.root / 'cache', on_bytes=hit.append), directory)
        self.assertEqual(hit, [])
        victim = directory / 'example/data.bin'
        victim.write_bytes(b'X' * len(self.members['example/data.bin']))
        with self.assertRaises(Conflict):
            runtime.materialize(raw, spec, self.root / 'cache', on_bytes=hit.append)
        self.assertEqual(hit, [])
        self.assertEqual(victim.read_bytes(), b'X' * len(self.members['example/data.bin']))


if __name__ == '__main__':
    unittest.main()
