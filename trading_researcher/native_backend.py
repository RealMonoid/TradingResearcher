"""Exact numeric adapter for an independently qualified retained native module.

This module does not import NumPy, load a binary, select a runtime or issue a
certificate. The owning isolated caller must establish those bindings first.
"""
import math

from .binding import require


ABI = 'stationary-native-int64/1'
NUMPY = '2.3.4'
SOURCE_SHA256 = 'b4fb9106bb2b2e7715a5b7e34a2d468d4f950cc5e60dc1571531397ea3a8f5b6'
MAX_TIME_ROWS = 100000
MAX_MEAN_LENGTH = 100000
INFO = {'abi': ABI, 'max_time_rows': MAX_TIME_ROWS, 'max_mean_length': MAX_MEAN_LENGTH,
        'numpy': NUMPY, 'bitgen_struct_bytes': 40}


class _Draw:
    def __init__(self, candidate, length):
        self.candidate = candidate
        self.length = length

    def draw(self, length, checker):
        require(type(length) is int and length == self.length,
                'Native engine used for a different sensitivity length')
        logarithm = None if length == 1 else math.log1p(-1.0 / length)
        return self.candidate.draw(length, logarithm, checker, math.log1p, math.floor)


def make_draw_factory(module, numpy):
    """Adapt an already qualified module; metadata alone establishes no trust.

    The original seeded Python RNG is never advanced here. Unsupported lengths
    or numeric prefixes return None so the original Python implementation runs.
    """
    require(numpy.__version__ == NUMPY and module.implementation_info() == INFO,
            'Unsupported selected native implementation')

    def factory(rng, rows, length):
        require(type(length) is int, 'Exact sensitivity length required')
        if not 1 <= length <= MAX_MEAN_LENGTH or not 1 <= len(rows) - 1 <= MAX_TIME_ROWS:
            return None
        owner = numpy.random.MT19937(0)
        candidate = module.Candidate(owner)
        if not candidate.configure_prefixes(rows):
            return None
        state = rng.getstate()
        require(type(state) is tuple and len(state) == 3 and state[0] == 3
                and type(state[1]) is tuple and len(state[1]) == 625,
                'Exact Python MT19937 state required')
        internal = state[1]
        require(all(type(value) is int and 0 <= value < 2**32 for value in internal[:-1])
                and type(internal[-1]) is int and 0 <= internal[-1] <= 624,
                'Python MT19937 state is outside the bound envelope')
        owner.state = {'bit_generator': 'MT19937',
                       'state': {'key': numpy.array(internal[:-1], dtype=numpy.uint32, copy=True),
                                 'pos': internal[-1]}}
        return _Draw(candidate, length)

    return factory
