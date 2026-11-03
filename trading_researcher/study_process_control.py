"""Owned native-study launch controls, without retry or admission authority.

The marker belongs to the controller, not the retained JSON request. A deadline
cause proves only that this supervisor observed its clock and reaped its child;
the consuming ledger must still establish known use, integrity and retry terms.
"""
import ctypes
from ctypes import wintypes
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from types import MappingProxyType

from .binding import require
from .codec import Invalid, MAX_BYTES, canonical, decode


POLICY = MappingProxyType({'schema': 'native-study-process-control/1',
                          'library_threads': 1, 'priority': 'BELOW_NORMAL'})
THREAD_ENVIRON = MappingProxyType({name: '1' for name in (
    'OMP_NUM_THREADS', 'OMP_THREAD_LIMIT', 'OPENBLAS_NUM_THREADS',
    'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS',
    'BLIS_NUM_THREADS')})
PRIORITY_CLASS = 0x4000  # Windows BELOW_NORMAL_PRIORITY_CLASS.
REAP_TIMEOUT_SECONDS = 5
STDERR_LIMIT = 8192


class ProcessControl:
    """Immutable, exact-type marker for this one fixed launch policy."""
    __slots__ = ()

    def request(self):
        return dict(POLICY)


class ChildDeadlineExceeded(Invalid):
    """Owned supervisor deadline, bounded outputs and successful child reap."""


class ChildCleanupFailed(Invalid):
    """The child could still consume resources; a file scan cannot settle use."""


class StudyProcessCancelled(Invalid):
    """Parent-requested cancellation; never an owned clock or retry allowance."""


class NativeAttemptCustody:
    """One-use parent custody of authenticated transport phases, not admission.

    Numerical completion, currency and resource settlement remain the caller's
    responsibility. Copies prevent later response/result mutations from changing
    the retained acknowledgement, including when a later replay raises.
    """
    __slots__ = ('_binding', '_phases')

    def __init__(self):
        self._binding = None
        self._phases = []

    def _begin(self, binding):
        require(self._binding is None and type(binding) is dict,
                'Fresh owned native attempt custody required')
        self._binding = decode(canonical(binding).encode())

    def _record(self, phase, result, proof):
        expected = 'generate' if not self._phases else 'replay'
        require(self._binding is not None and len(self._phases) < 2 and phase == expected
                and type(result) is dict and type(proof) is dict,
                'Ordered authenticated native phase required')
        self._phases.append(decode(canonical(
            {'phase': phase, 'result': result, 'proof': proof}).encode()))

    def snapshot(self):
        return decode(canonical({'schema': 'native-attempt-custody/1',
            'binding': self._binding or {}, 'phases': self._phases}).encode())


def validate_cancellation(cancel):
    # Parent-only import: observing controls in the numerical child must not
    # import additional libraries merely to accept an Event it never receives.
    if cancel is not None:
        from threading import Event
        require(type(cancel) is Event, 'Owned parent cancellation Event required')


class _DeadlineObserved(Exception):
    """Private control flow; not an externally admissible failure cause."""


def validate_observation(observation):
    expected = {'policy': dict(POLICY),
                'thread_environment': dict(THREAD_ENVIRON),
                'priority_class': PRIORITY_CLASS}
    require(type(observation) is dict and canonical(observation) == canonical(expected),
            'Native study process controls differ from the fixed policy')
    return True


def observe_control(policy):
    """Observe this child before numerical imports and again at completion."""
    require(type(policy) is dict and canonical(policy) == canonical(dict(POLICY)),
            'Exact native study process policy required')
    require(sys.platform == 'win32', 'Native study process controls require Windows')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    kernel.GetPriorityClass.argtypes = [wintypes.HANDLE]
    kernel.GetPriorityClass.restype = wintypes.DWORD
    priority = kernel.GetPriorityClass(kernel.GetCurrentProcess())
    observed = {'policy': dict(POLICY),
                'thread_environment': {name: os.environ.get(name) for name in THREAD_ENVIRON},
                'priority_class': priority}
    validate_observation(observed)
    return observed


def run_controlled_child(command, directory, timeout, control, *, _cancel=None):
    """Reuse Popen with explicit controls; retain every output/error prefix.

    Creation, kill and filesystem work are not hard OS quotas. Their actual
    elapsed time remains chargeable by the caller. Failed kill/reap never earns
    the known deadline cause; the ledger must stop on uncertain resource use.
    """
    require(type(control) is ProcessControl, 'Owned native study process control required')
    validate_cancellation(_cancel)
    require(type(timeout) in (int, float), 'Finite positive child timeout required')
    try:
        valid_timeout = math.isfinite(timeout) and timeout > 0
    except OverflowError:
        valid_timeout = False
    require(valid_timeout, 'Finite positive child timeout required')
    require(sys.platform == 'win32', 'Native study process controls require Windows')
    if _cancel is not None and _cancel.is_set():
        raise StudyProcessCancelled('Native study cancelled before child launch')
    directory = Path(directory)
    output, errors = directory / 'child-output.json', directory / 'child-errors.txt'
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRON)
    deadline = time.monotonic() + timeout

    def bounded_outputs():
        require(output.stat().st_size <= MAX_BYTES and errors.stat().st_size <= STDERR_LIMIT,
                'Controlled study child output exceeds its envelope')

    with output.open('xb') as stdout, errors.open('xb') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=environment,
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        try:
            while process.poll() is None:
                # A simultaneous output-cap failure has priority over the clock.
                bounded_outputs()
                if _cancel is not None and _cancel.is_set():
                    raise StudyProcessCancelled('Native study parent requested cancellation')
                seconds = deadline - time.monotonic()
                if seconds <= 0:
                    raise _DeadlineObserved()
                try:
                    process.wait(timeout=min(0.2, seconds))
                except subprocess.TimeoutExpired:
                    pass
        except BaseException as exc:
            try:
                process.kill()
                process.wait(timeout=REAP_TIMEOUT_SECONDS)
            except BaseException as cleanup:
                raise ChildCleanupFailed('Controlled study child termination/reap is unconfirmed') from cleanup
            if isinstance(exc, _DeadlineObserved):
                # The child may have written more while termination was pending.
                bounded_outputs()
                raise ChildDeadlineExceeded('Owned study child deadline elapsed; child reaped') from exc
            raise
    bounded_outputs()
    require(process.returncode == 0,
            'Controlled study child failed: ' + errors.read_text(encoding='utf-8', errors='replace'))
    return decode(output.read_bytes())
