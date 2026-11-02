"""Independent bounded directory publication and caller accounting checks.

All files are invented temporary data. Real Windows handle denial is exercised
where available; deterministic errors preserve the same fixed retry envelope.
No native binary, provider, scientific series or historical registry is used.
"""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import errno
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import Mock, patch

from test_native_runtime_independent import archive, manifest, MEMBERS, cache_identity
from trading_researcher import native_runtime, storage
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict


DELAYS = [0.05, 0.1, 0.2, 0.4]


def lock_error(code=5):
    error = PermissionError(errno.EACCES, 'Invented publication lock')
    error.winerror = code
    return error


class AtomicPublicationIndependentTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='trf-publication-independent-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.rename = Path.rename

    def tree(self, name='stage'):
        stage = self.root / name
        (stage / 'nested').mkdir(parents=True)
        (stage / 'nested' / 'payload.bin').write_bytes(b'Independent fixed bytes.\x00\xff')
        (stage / 'notice.txt').write_bytes(b'Invented data only.\n')
        return stage

    def contents(self, path):
        return {item.relative_to(path).as_posix(): item.read_bytes()
                for item in path.rglob('*') if item.is_file()}

    @contextmanager
    def policy(self, *, windows=True, sleeper=None):
        # Do not patch the global os.name: pathlib must keep the actual platform.
        proxy = types.SimpleNamespace(**vars(os))
        proxy.name = 'nt' if windows else 'posix'
        if sleeper is None:
            sleeper = Mock()
        with patch.object(storage, 'os', proxy), patch.object(storage.time, 'sleep', sleeper):
            yield sleeper

    def publish(self, stage, destination):
        return storage._publish_staging(stage, destination)

    def test_actual_same_parent_rename_preserves_complete_tree_and_file_identity(self):
        stage = self.tree()
        destination = self.root / 'published'
        before = self.contents(stage)
        directory_identity = stage.stat().st_ino
        file_identity = (stage / 'nested' / 'payload.bin').stat().st_ino
        with self.policy() as sleep, patch.object(Path, 'rename', autospec=True,
                side_effect=self.rename) as rename, \
                patch.object(storage.shutil, 'copyfile', side_effect=AssertionError('Publication copied bytes')), \
                patch.object(storage.shutil, 'copytree', side_effect=AssertionError('Publication copied a tree')), \
                patch.object(storage.shutil, 'rmtree', side_effect=AssertionError('Publication deleted a tree')):
            self.publish(stage, destination)
        self.assertEqual(rename.call_count, 1)
        sleep.assert_not_called()
        self.assertFalse(stage.exists())
        self.assertEqual(self.contents(destination), before)
        self.assertEqual(destination.stat().st_ino, directory_identity)
        self.assertEqual((destination / 'nested' / 'payload.bin').stat().st_ino, file_identity)

    def test_existing_file_empty_directory_or_nonempty_directory_is_never_replaced(self):
        for kind in ('file', 'empty', 'nonempty'):
            with self.subTest(kind=kind):
                stage = self.tree('stage-' + kind)
                destination = self.root / ('destination-' + kind)
                if kind == 'file':
                    destination.write_bytes(b'Existing unrelated file.')
                else:
                    destination.mkdir()
                    if kind == 'nonempty':
                        (destination / 'winner.txt').write_bytes(b'Existing winner.')
                before = destination.read_bytes() if kind == 'file' else self.contents(destination)
                stage_before = self.contents(stage)
                with self.policy() as sleep, patch.object(Path, 'rename',
                        side_effect=AssertionError('Existing destination reached rename')):
                    with self.assertRaises((OSError, Conflict)):
                        self.publish(stage, destination)
                sleep.assert_not_called()
                self.assertEqual(self.contents(stage), stage_before)
                after = destination.read_bytes() if kind == 'file' else self.contents(destination)
                self.assertEqual(after, before)

    def test_different_parent_is_refused_before_any_rename_or_copy(self):
        stage = self.tree()
        other = self.root / 'other-parent'
        other.mkdir()
        with self.policy() as sleep, patch.object(Path, 'rename',
                side_effect=AssertionError('Different parent reached rename')):
            with self.assertRaises((OSError, Conflict)):
                self.publish(stage, other / 'published')
        sleep.assert_not_called()
        self.assertTrue(stage.exists())
        self.assertFalse((other / 'published').exists())

    def test_same_source_and_destination_is_refused_without_mutation(self):
        stage = self.tree()
        before = self.contents(stage)
        with self.policy(), patch.object(Path, 'rename', side_effect=AssertionError('Self rename')):
            with self.assertRaises((OSError, Conflict)):
                self.publish(stage, stage)
        self.assertEqual(self.contents(stage), before)

    def test_each_allowed_windows_lock_gets_only_the_four_fixed_delays(self):
        for code in (5, 32, 33):
            with self.subTest(code=code):
                stage = self.tree('stage-' + str(code))
                destination = self.root / ('published-' + str(code))
                attempts = []

                def rename(source, target):
                    attempts.append((source, target))
                    if len(attempts) < 5:
                        raise lock_error(code)
                    return self.rename(source, target)

                with self.policy() as sleep, patch.object(Path, 'rename', rename):
                    self.publish(stage, destination)
                self.assertEqual(attempts, [(stage, destination)] * 5)
                self.assertEqual([call.args[0] for call in sleep.call_args_list], DELAYS)
                self.assertFalse(stage.exists())
                self.assertTrue(destination.exists())

    def test_exhaustion_propagates_last_error_without_sixth_attempt_or_extra_delay(self):
        stage = self.tree()
        destination = self.root / 'published'
        errors = [lock_error(5), lock_error(32), lock_error(33), lock_error(5), lock_error(32)]
        with self.policy() as sleep, patch.object(Path, 'rename', side_effect=errors) as rename:
            with self.assertRaises(PermissionError) as raised:
                self.publish(stage, destination)
        self.assertIs(raised.exception, errors[-1])
        self.assertEqual(rename.call_count, 5)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], DELAYS)
        self.assertTrue(stage.exists())
        self.assertFalse(destination.exists())

    def test_nonwindows_permission_denial_has_no_retry(self):
        stage = self.tree()
        error = lock_error(5)
        with self.policy(windows=False) as sleep, patch.object(Path, 'rename', side_effect=error) as rename:
            with self.assertRaises(PermissionError) as raised:
                self.publish(stage, self.root / 'published')
        self.assertIs(raised.exception, error)
        self.assertEqual(rename.call_count, 1)
        sleep.assert_not_called()

    def test_other_permission_codes_and_missing_code_have_no_retry(self):
        errors = [PermissionError(errno.EACCES, 'No Windows lock code'),
                  lock_error(2), lock_error(13), lock_error(183)]
        for index, error in enumerate(errors):
            with self.subTest(error=index):
                stage = self.tree('stage-' + str(index))
                with self.policy() as sleep, patch.object(Path, 'rename', side_effect=error) as rename:
                    with self.assertRaises(PermissionError) as raised:
                        self.publish(stage, self.root / ('published-' + str(index)))
                self.assertIs(raised.exception, error)
                self.assertEqual(rename.call_count, 1)
                sleep.assert_not_called()

    def test_nonpermission_errors_and_cancellation_have_no_retry(self):
        synthetic_io = OSError(errno.EIO, 'Invented I/O error')
        synthetic_io.winerror = 5
        for index, error in enumerate((synthetic_io, FileNotFoundError('Missing stage'),
                                       RuntimeError('Unexpected application error'), KeyboardInterrupt())):
            with self.subTest(error=index):
                stage = self.tree('stage-' + str(index))
                with self.policy() as sleep, patch.object(Path, 'rename', side_effect=error) as rename:
                    with self.assertRaises(type(error)) as raised:
                        self.publish(stage, self.root / ('published-' + str(index)))
                self.assertIs(raised.exception, error)
                self.assertEqual(rename.call_count, 1)
                sleep.assert_not_called()

    def test_cancelled_delay_does_not_publish_or_continue(self):
        stage = self.tree()
        sleeper = Mock(side_effect=KeyboardInterrupt())
        with self.policy(sleeper=sleeper), patch.object(Path, 'rename', side_effect=lock_error()) as rename:
            with self.assertRaises(KeyboardInterrupt):
                self.publish(stage, self.root / 'published')
        self.assertEqual(rename.call_count, 1)
        self.assertEqual([call.args[0] for call in sleeper.call_args_list], [0.05])
        self.assertTrue(stage.exists())
        self.assertFalse((self.root / 'published').exists())

    def test_destination_appearing_after_denial_is_never_overwritten_on_retry(self):
        stage = self.tree()
        destination = self.root / 'published'

        def race(source, target):
            destination.mkdir()
            (destination / 'winner.txt').write_bytes(b'Concurrent independent winner.')
            raise lock_error(5)

        with self.policy(), patch.object(Path, 'rename', autospec=True, side_effect=race) as rename:
            with self.assertRaises(OSError):
                self.publish(stage, destination)
        self.assertEqual(rename.call_count, 1)
        self.assertTrue(stage.exists())
        self.assertEqual(self.contents(destination), {'winner.txt': b'Concurrent independent winner.'})

    @unittest.skipUnless(os.name == 'nt', 'Windows CreateFileW sharing semantics required')
    def test_actual_child_file_handle_denial_succeeds_after_release_on_first_delay(self):
        stage = self.tree()
        destination = self.root / 'published'
        library = ctypes.WinDLL('kernel32', use_last_error=True)
        library.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                       wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        library.CreateFileW.restype = wintypes.HANDLE
        library.CloseHandle.argtypes = [wintypes.HANDLE]
        library.CloseHandle.restype = wintypes.BOOL
        handle = library.CreateFileW(str(stage / 'nested' / 'payload.bin'), 0x80000000, 3,
                                     None, 3, 0x80, None)
        if handle == wintypes.HANDLE(-1).value:
            self.fail('Unable to create the required invented child-file handle: ' + str(ctypes.get_last_error()))
        attempts, observed_errors, delays = [], [], []

        def release(seconds):
            nonlocal handle
            delays.append(seconds)
            self.assertTrue(library.CloseHandle(handle))
            handle = None

        def rename(source, target):
            attempts.append((source, target))
            try:
                return self.rename(source, target)
            except PermissionError as error:
                observed_errors.append(error.winerror)
                raise

        try:
            with self.policy(sleeper=release), patch.object(Path, 'rename', rename):
                self.publish(stage, destination)
        finally:
            if handle is not None:
                library.CloseHandle(handle)
        self.assertEqual(len(attempts), 2)
        self.assertEqual(len(observed_errors), 1)
        self.assertIn(observed_errors[0], (5, 32, 33))
        self.assertEqual(delays, [0.05])
        self.assertFalse(stage.exists())
        self.assertEqual((destination / 'nested' / 'payload.bin').read_bytes(), b'Independent fixed bytes.\x00\xff')

    def test_actual_tiny_materialization_retries_publication_without_rewriting_or_double_charge(self):
        raw, specification = archive(), manifest()
        cache = self.root / 'native-cache'
        charges, calls = [], []

        def rename(source, target):
            calls.append((source, target))
            if len(calls) < 3:
                raise lock_error(32)
            return self.rename(source, target)

        with self.policy() as sleep, patch.object(Path, 'rename', rename):
            directory = native_runtime.materialize(raw, specification, cache, on_bytes=charges.append)
        self.assertEqual(len(calls), 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [0.05, 0.1])
        self.assertEqual(charges, [len(value) for value in MEMBERS.values()])
        self.assertEqual(self.contents(directory), MEMBERS)
        self.assertEqual(list(cache.glob('runtime-pending-*')), [])
        hit_charges = []
        with patch.object(storage, '_publish_staging', side_effect=AssertionError('Verified cache hit republished')):
            self.assertEqual(native_runtime.materialize(raw, specification, cache, on_bytes=hit_charges.append), directory)
        self.assertEqual(hit_charges, [])

    def test_tiny_materialization_exhaustion_cleans_only_owned_stage_and_keeps_once_only_charge(self):
        raw, specification = archive(), manifest()
        cache = self.root / 'native-cache'
        cache.mkdir()
        unrelated = cache / 'unrelated-sentinel'
        unrelated.write_bytes(b'Keep unrelated bytes.')
        charges = []
        with self.policy() as sleep, patch.object(Path, 'rename', side_effect=lock_error(33)) as rename:
            with self.assertRaises(PermissionError):
                native_runtime.materialize(raw, specification, cache, on_bytes=charges.append)
        self.assertEqual(rename.call_count, 5)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], DELAYS)
        self.assertEqual(charges, [len(value) for value in MEMBERS.values()])
        self.assertFalse((cache / cache_identity(raw, specification)).exists())
        self.assertEqual(list(cache.glob('runtime-pending-*')), [])
        self.assertEqual(unrelated.read_bytes(), b'Keep unrelated bytes.')

    def test_native_caller_alone_accepts_exact_concurrent_winner_and_rejects_changed_winner(self):
        raw, specification = archive(), manifest()
        for changed in (False, True):
            with self.subTest(changed=changed):
                cache = self.root / ('native-cache-' + str(changed))
                destination = cache / cache_identity(raw, specification)
                charges = []

                def race(source, target):
                    self.assertEqual(target, destination)
                    for name, value in MEMBERS.items():
                        path = destination / name
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_bytes(value)
                    if changed:
                        (destination / 'example' / 'data.bin').write_bytes(b'Changed concurrent bytes.')
                    raise lock_error(5)

                with self.policy(), patch.object(Path, 'rename', autospec=True, side_effect=race) as rename:
                    if changed:
                        with self.assertRaises(Conflict):
                            native_runtime.materialize(raw, specification, cache, on_bytes=charges.append)
                    else:
                        self.assertEqual(native_runtime.materialize(raw, specification, cache,
                            on_bytes=charges.append), destination)
                self.assertEqual(rename.call_count, 1)
                self.assertEqual(charges, [len(value) for value in MEMBERS.values()])
                self.assertEqual(list(cache.glob('runtime-pending-*')), [])
                expected = {**MEMBERS, **({'example/data.bin': b'Changed concurrent bytes.'} if changed else {})}
                self.assertEqual(self.contents(destination), expected)

    def test_actual_backup_and_restore_use_the_same_atomic_publication_owner(self):
        broker = Broker(self.root / 'empty-registry')
        try:
            backup = self.root / 'backup'
            with patch.object(storage, '_publish_staging', wraps=storage._publish_staging) as publish:
                result = broker.call(broker.admin_token, 'backup_bundle', destination=str(backup))
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(publish.call_count, 1)
            self.assertTrue(publish.call_args.args[0].name.startswith('backup-pending-'))
            self.assertEqual(publish.call_args.args[1], backup)
            restored = self.root / 'restored'
            with patch.object(storage, '_publish_staging', wraps=storage._publish_staging) as publish:
                result = storage.restore_bundle(backup, restored, broker.directory / 'operator.key')
            self.assertEqual(result['status'], 'PASS')
            self.assertEqual(publish.call_count, 1)
            self.assertTrue(publish.call_args.args[0].name.startswith('restore-pending-'))
            self.assertEqual(publish.call_args.args[1], restored)
            self.assertEqual(list(self.root.glob('backup-pending-*')), [])
            self.assertEqual(list(self.root.glob('restore-pending-*')), [])
        finally:
            broker.close()


if __name__ == '__main__':
    unittest.main()
