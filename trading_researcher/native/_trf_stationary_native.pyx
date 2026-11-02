# cython: language_level=3
"""Exact owned native draw engine; use requires independently bound qualification."""
from cpython.pycapsule cimport PyCapsule_GetPointer, PyCapsule_IsValid
from cython cimport boundscheck, wraparound
from libc.stdint cimport uint32_t
import hashlib
import numpy as np

cdef extern from "numpy/random/bitgen.h":
    ctypedef struct bitgen_t:
        void *state
        uint32_t (*next_uint32)(void *) noexcept
        double (*next_double)(void *) noexcept

cdef class Candidate:
    cdef object _owner
    cdef object _lock
    cdef bitgen_t *_core
    cdef object _prefix_array
    cdef const long long[:, ::1] _prefixes
    cdef unsigned int _size

    def __cinit__(self, owner):
        if np.__version__ != '2.3.4' or type(owner) is not np.random.MT19937:
            raise TypeError('Qualification requires the selected NumPy MT19937')
        self._owner = owner
        self._lock = owner.lock
        capsule = owner.capsule
        if not PyCapsule_IsValid(capsule, b'BitGenerator'):
            raise ValueError('Invalid selected bit-generator capsule')
        self._core = <bitgen_t *>PyCapsule_GetPointer(capsule, b'BitGenerator')

    def randrange(self, size):
        cdef uint32_t value, bound
        cdef unsigned int bits
        if type(size) is not int:
            raise TypeError('Exact integer fixture size required')
        if not 1 <= size <= 100000:
            raise ValueError('Outside this qualification domain')
        bound = size
        bits = size.bit_length()
        with self._lock:
            value = self._core.next_uint32(self._core.state) >> (32 - bits)
            while value >= bound:
                value = self._core.next_uint32(self._core.state) >> (32 - bits)
        return value

    def random(self):
        cdef double value
        with self._lock:
            value = self._core.next_double(self._core.state)
        return value

    def configure_prefixes(self, rows):
        """Detach a conservatively proven int64 subset; otherwise keep no config."""
        self._size = 0
        self._prefixes = None
        self._prefix_array = None
        detached = tuple(tuple(row) for row in rows)
        size = len(detached) - 1
        if not 1 <= size <= 100000 or any(len(row) != 4 for row in detached):
            raise ValueError('Outside the fixed prefix shape')
        if any(type(value) is not int for row in detached for value in row):
            return False
        if detached[0] != (0, 0, 0, 0):
            raise ValueError('Prefixes must start at zero')
        # Any accepted partial sample visits at most size buckets. Thus each
        # field, prefix query and accumulator stays in [-MAX, MAX], including
        # wrap subtraction/addition. No original 8192-bit guard can fire here.
        maximum = (1 << 63) - 1
        for field in range(4):
            delta = max(abs(detached[index][field] - detached[index - 1][field])
                        for index in range(1, size + 1))
            if size * delta > maximum:
                return False
        array = np.array(detached, dtype=np.int64, copy=True, order='C')
        array.flags.writeable = False
        self._prefix_array = array
        self._prefixes = array
        self._size = size
        return True

    @boundscheck(False)
    @wraparound(False)
    def draw(self, length, logarithm, checker, log1p, floor):
        """One complete/partial draw, preserving generator-before-check order."""
        cdef unsigned int size = self._size
        cdef unsigned int bits, start, count, end, remaining, segments = 0
        cdef unsigned int sampled = 0, offset = 0, field, number, shift
        cdef uint32_t value
        cdef double uniform
        cdef long long sums[4]
        cdef const long long[:, ::1] rows
        cdef unsigned char[::1] path
        if size == 0:
            raise RuntimeError('No supported prefix configuration')
        if type(length) is not int or not 1 <= length <= 100000:
            raise ValueError('Outside the fixed length envelope')
        rows = self._prefixes
        path_bytes = bytearray(size * 8)
        path = path_bytes
        for field in range(4):
            sums[field] = 0
        bits = int(size).bit_length()
        remaining = size
        reason = None
        while remaining:
            with self._lock:
                value = self._core.next_uint32(self._core.state) >> (32 - bits)
                while value >= size:
                    value = self._core.next_uint32(self._core.state) >> (32 - bits)
                start = value
                if length != 1:
                    uniform = self._core.next_double(self._core.state)
            if length == 1:
                count = 1
            else:
                # Use the actual Python callbacks/division as the scalar law,
                # including before a stop. Never replace log1p with native libm.
                proposed = floor(log1p(-uniform) / logarithm) + 1
                count = min(proposed, remaining)
            reason = checker(True, int(segments))
            if reason:
                break
            segments += 1
            sampled += count
            # Same >II bytes as struct.pack, kept in a bounded private buffer.
            path[offset] = <unsigned char>(start >> 24)
            path[offset + 1] = <unsigned char>(start >> 16)
            path[offset + 2] = <unsigned char>(start >> 8)
            path[offset + 3] = <unsigned char>start
            path[offset + 4] = <unsigned char>(count >> 24)
            path[offset + 5] = <unsigned char>(count >> 16)
            path[offset + 6] = <unsigned char>(count >> 8)
            path[offset + 7] = <unsigned char>count
            offset += 8
            end = start + count
            for field in range(4):
                if end <= size:
                    sums[field] += rows[end, field] - rows[start, field]
                else:
                    sums[field] += ((rows[size, field] - rows[start, field])
                                    + rows[end - size, field])
            remaining -= count
        return {'scope_count': sums[0], 'scope_sum': sums[1],
                'condition_count': sums[2], 'condition_sum': sums[3],
                'sampled_times': sampled, 'segments': segments,
                'path_sha256': hashlib.sha256(memoryview(path_bytes)[:offset]).hexdigest(),
                'reason': reason}

def implementation_info():
    return {'abi': 'stationary-native-int64/1', 'max_time_rows': 100000,
            'max_mean_length': 100000, 'numpy': np.__version__,
            'bitgen_struct_bytes': sizeof(bitgen_t)}
