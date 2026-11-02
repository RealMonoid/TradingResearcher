"""New root-reuse boundaries over the unchanged retained verifier oracle.

These cases supplement the existing tree/cache suites: a root or its enclosing
ancestor becomes a real junction between initial admission and the first walk
entry; Windows-normalized absolute spellings and relative roots through a
junction cwd retain the frozen owner's verdict. Every path/target is invented
inside one owned temporary directory. No Registry, binary or world is involved.

An isolated prototype runner may call make_cases(candidate_module) and run that
class. Assertions, oracle and filesystem mutations remain the same. The public
module name used by unittest selects the canonical implementation by default.
"""
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import unittest
from unittest.mock import patch

import test_native_tree_verification_independent as tree_cases
from test_native_runtime_independent import manifest, snapshot
from trading_researcher import native_runtime as canonical_runtime
from trading_researcher.errors import Conflict


TREE_CASES_SHA = '918cb779a49b05fc31f76ffa7e162dae7e62567d61c3ec3c6cf3a3f07d6ce78f'


def make_cases(selected_runtime):
    """Use only the selected module's verify_tree; never replace expectations."""
    base = tree_cases.NativeTreeVerificationIndependentTests

    class NativeCacheRootIndependentTests(unittest.TestCase):
        observations = []

        @classmethod
        def setUpClass(cls):
            assert hashlib.sha256(Path(tree_cases.__file__).read_bytes()).hexdigest() == TREE_CASES_SHA
            base.setUpClass()
            cls.oracle = staticmethod(base.oracle)
            cls.observations = []

        def setUp(self):
            base.setUp(self)

        tree = base.tree
        junction = base.junction

        def implementations(self):
            return (('historical', self.oracle), ('selected', selected_runtime.verify_tree))

        def verdict(self, verify, directory, specification):
            try:
                result = verify(directory, specification)
            except (Conflict, OSError) as exc:
                return ('REFUSED', type(exc).__name__)
            self.assertIsNone(result)
            return ('ACCEPTED', None)

        @contextmanager
        def cwd(self, directory):
            previous = Path.cwd()
            try:
                os.chdir(directory)
                yield
            finally:
                os.chdir(previous)

        @unittest.skipUnless(os.name == 'nt', 'Actual Windows junction semantics required')
        def test_root_or_enclosing_ancestor_linked_before_first_member_is_not_followed(self):
            # The old suite changes an enclosing ancestor after one hash. Here
            # there are no trusted member observations yet: initial root
            # admission has finished but the first walk entry has not returned.
            for label, verify in self.implementations():
                for kind in ('root', 'ancestor'):
                    with self.subTest(implementation=label, kind=kind):
                        prefix = label + '-' + kind
                        directory = self.tree(prefix + '-ordinary/cache')
                        other = self.tree(prefix + '-target/cache')
                        pivot = directory if kind == 'root' else directory.parent
                        target = other if kind == 'root' else other.parent
                        moved = self.root / (prefix + '-original-moved')
                        before = snapshot(target)
                        mutated = [False]
                        original_walk = os.walk
                        original_open = Path.open

                        def walk(top, *args, **kwargs):
                            self.assertEqual(Path(top), directory)
                            for entry in original_walk(top, *args, **kwargs):
                                if not mutated[0]:
                                    self.assertTrue(pivot.resolve().is_relative_to(self.root))
                                    self.assertTrue(moved.absolute().is_relative_to(self.root))
                                    pivot.rename(moved)
                                    self.junction(pivot, target)
                                    mutated[0] = True
                                yield entry

                        def guarded_open(path, *args, **kwargs):
                            if Path(path).resolve().is_relative_to(target):
                                self.fail('Verifier followed the newly linked root/ancestor into target bytes')
                            return original_open(path, *args, **kwargs)

                        with patch.object(os, 'walk', walk), patch.object(Path, 'open', guarded_open):
                            with self.assertRaises(Conflict): verify(directory, manifest(self.members))
                        self.assertTrue(mutated[0], 'The fixed initial-admission/first-member boundary was not exercised')
                        self.assertEqual(snapshot(target), before)
                        self.observations.append({'case': 'before-first-member', 'kind': kind,
                                                  'implementation': label, 'verdict': 'Conflict_before_target_open'})

        def test_opaque_root_namespace_change_cannot_authorize_member_in_previous_root(self):
            # Model an unsupported reparse/filter boundary using its observable
            # APIs, not an installed filesystem driver: after initial admission
            # the root resolves to R2, while a member still resolves into R1.
            # A fresh generic containment check therefore refuses R1 bytes even
            # though the familiar symlink/junction predicates remain false.
            for label, verify in self.implementations():
                with self.subTest(implementation=label):
                    directory = self.tree(label + '-opaque-R1')
                    current_root = self.tree(label + '-opaque-R2')
                    before = snapshot(directory), snapshot(current_root)
                    changed = [False]
                    attempted_old_read = [False]
                    original_resolve, original_lstat = Path.resolve, Path.lstat
                    original_walk, original_open = os.walk, Path.open

                    def resolve(path, *args, **kwargs):
                        if changed[0] and Path(path) == directory:
                            return current_root
                        return original_resolve(path, *args, **kwargs)

                    def lstat(path, *args, **kwargs):
                        observed = original_lstat(path, *args, **kwargs)
                        if changed[0] and Path(path) == directory:
                            return tree_cases.stat_copy(observed,
                                st_file_attributes=getattr(observed, 'st_file_attributes', 0) | 0x400,
                                st_reparse_tag=0x80004321)
                        return observed

                    def walk(top, *args, **kwargs):
                        self.assertEqual(Path(top), directory)
                        for entry in original_walk(top, *args, **kwargs):
                            changed[0] = True
                            self.assertEqual(directory.resolve(), current_root)
                            self.assertFalse(directory.is_symlink())
                            if hasattr(directory, 'is_junction'):
                                self.assertFalse(directory.is_junction())
                            self.assertNotEqual(directory.lstat().st_file_attributes & 0x400, 0)
                            yield entry

                    def guarded_open(path, *args, **kwargs):
                        if changed[0] and Path(path).is_relative_to(directory):
                            attempted_old_read[0] = True
                            self.fail('Containment opened a member in R1 after the owned root resolved to R2')
                        return original_open(path, *args, **kwargs)

                    with patch.object(Path, 'resolve', resolve), patch.object(Path, 'lstat', lstat), \
                            patch.object(os, 'walk', walk), patch.object(Path, 'open', guarded_open):
                        with self.assertRaises(Conflict): verify(directory, manifest(self.members))
                    self.assertTrue(changed[0], 'The fixed opaque-namespace boundary was not exercised')
                    self.assertFalse(attempted_old_read[0])
                    self.assertEqual((snapshot(directory), snapshot(current_root)), before)
                    self.observations.append({'case': 'opaque-root-namespace-change',
                                              'implementation': label, 'verdict': 'Conflict_before_R1_open'})

        @unittest.skipUnless(os.name == 'nt', 'Windows path normalization semantics required')
        def test_extended_case_and_win32_normalized_root_spellings_keep_frozen_verdict(self):
            directory = self.tree('absolute-spellings')
            self.assertIsNone(self.oracle(directory, manifest(self.members)))
            self.assertTrue(directory.is_absolute() and directory.drive)
            spellings = {
                'extended-prefix': Path('\\\\?\\' + str(directory)),
                'case-varied': Path(str(directory).swapcase()),
                'win32-trailing-dot': Path(str(directory) + '.'),
                'win32-trailing-space': Path(str(directory) + ' '),
            }
            for name, spelling in spellings.items():
                with self.subTest(spelling=name):
                    expected = self.verdict(self.oracle, spelling, manifest(self.members))
                    actual = self.verdict(selected_runtime.verify_tree, spelling, manifest(self.members))
                    self.assertEqual(actual, expected)
                    self.observations.append({'case': 'absolute-spelling', 'spelling': name,
                                              'historical_verdict': expected, 'selected_verdict': actual})
            self.assertEqual(snapshot(directory), self.members)

        @unittest.skipUnless(os.name == 'nt', 'Actual Windows junction/cwd semantics required')
        def test_relative_roots_from_junction_cwd_keep_historical_acceptance_or_refusal(self):
            directory = self.tree('cwd-target/cache')
            (directory.parent / 'wrapper').mkdir()
            portal = self.root / 'cwd-portal'
            self.junction(portal, directory.parent)
            before = snapshot(directory.parent)
            with self.cwd(portal):
                self.assertEqual(Path.cwd().resolve(), directory.parent.resolve())
                drive = directory.drive
                spellings = {'relative': Path('cache'), 'dotdot': Path('wrapper') / '..' / 'cache',
                             'drive-relative': Path(drive + 'cache')}
                for name, spelling in spellings.items():
                    with self.subTest(spelling=name):
                        expected = self.verdict(self.oracle, spelling, manifest(self.members))
                        actual = self.verdict(selected_runtime.verify_tree, spelling, manifest(self.members))
                        self.assertEqual(actual, expected)
                        self.observations.append({'case': 'junction-cwd-relative', 'spelling': name,
                                                  'historical_verdict': expected, 'selected_verdict': actual})
            self.assertEqual(snapshot(directory.parent), before)

    return NativeCacheRootIndependentTests


NativeCacheRootIndependentTests = make_cases(canonical_runtime)


if __name__ == '__main__':
    unittest.main()
