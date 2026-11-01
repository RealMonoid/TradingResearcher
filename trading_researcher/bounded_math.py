"""Opt-in D089 primitives; legacy ReferenceEngine behavior is unchanged.

Log series: NIST DLMF 4.6.4 (v1.2.8, consulted 2026-10-29).
Range reduction and all rounding/tail bounds below use integer arithmetic.
No binary floating value is represented as the exact mathematical logarithm.
"""
from dataclasses import dataclass
from fractions import Fraction

from .expressions import Node, ReferenceEngine, Value, gap


SCALE = 1 << 128
TERMS = 64


def _step(remaining):
    if (type(remaining) is not list or len(remaining) != 1
            or type(remaining[0]) is not int):
        gap('RESOURCE_GAP', 'Expected one integer primitive-step budget')
    remaining[0] -= 1
    if remaining[0] < 0:
        gap('RESOURCE_GAP', 'Bounded primitive exhausted its step budget')


def _ceil(numerator, denominator):
    return -((-numerator) // denominator)


def _bounds(lower, upper):
    """Outward dyadic rounding prevents denominator growth in later sums."""
    return Enclosure(Fraction(lower.numerator * SCALE // lower.denominator, SCALE),
                     Fraction(_ceil(upper.numerator * SCALE, upper.denominator), SCALE))


def _exact(value):
    if type(value) is int:
        value = Fraction(value)
    if type(value) is not Fraction:
        gap('NUMERICAL_GAP', 'Bounded arithmetic requires exact rational operands')
    if max(value.numerator.bit_length(), value.denominator.bit_length()) > 8192:
        gap('RESOURCE_GAP', 'Bounded arithmetic operand exceeds numeric envelope')
    return value


@dataclass(frozen=True)
class Enclosure:
    lower: Fraction
    upper: Fraction

    def __post_init__(self):
        _exact(self.lower)
        _exact(self.upper)
        if self.lower > self.upper:
            gap('NUMERICAL_GAP', 'Reversed numerical enclosure')

    @staticmethod
    def of(value):
        return value if isinstance(value, Enclosure) else Enclosure(_exact(value), _exact(value))

    def public(self):
        def pair(value):
            return {'numerator': str(value.numerator), 'denominator': str(value.denominator)}
        return {'schema': 'bounded-real/1', 'lower': pair(self.lower), 'upper': pair(self.upper)}

    def __add__(self, other):
        other = self.of(other)
        return _bounds(self.lower + other.lower, self.upper + other.upper)

    __radd__ = __add__

    def __neg__(self):
        return Enclosure(-self.upper, -self.lower)

    def __sub__(self, other):
        return self + -self.of(other)

    def __rsub__(self, other):
        return self.of(other) + -self

    def __mul__(self, other):
        other = self.of(other)
        values = [a * b for a in (self.lower, self.upper) for b in (other.lower, other.upper)]
        return _bounds(min(values), max(values))

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = self.of(other)
        if other.lower <= 0 <= other.upper:
            gap('NUMERICAL_GAP', 'Divisor enclosure contains zero')
        return self * _bounds(1 / other.upper, 1 / other.lower)

    def __rtruediv__(self, other):
        return self.of(other) / self


def _reduced_log(value, remaining):
    """Enclose ln(value), 1<=value<=2, in units of 2^-128.

    z=(value-1)/(value+1) lies in [0,1/3]. The 64-term positive
    series has tail <=2*z^129/(129*(1-z^2)) <=9*z^129/(4*129).
    Every product/division is rounded outwards; the next-power upper bound
    therefore also bounds the omitted tail. This is a derivation for the
    implementation, not an empirical approximation claim.
    """
    if value == 1:
        return 0, 0
    z = (value - 1) / (value + 1)
    lo = z.numerator * SCALE // z.denominator
    hi = _ceil(z.numerator * SCALE, z.denominator)
    square_lo, square_hi = lo * lo // SCALE, _ceil(hi * hi, SCALE)
    power_lo, power_hi, total_lo, total_hi = lo, hi, 0, 0
    for index in range(TERMS):
        _step(remaining)
        odd = 2 * index + 1
        total_lo += power_lo // odd
        total_hi += _ceil(power_hi, odd)
        power_lo = power_lo * square_lo // SCALE
        power_hi = _ceil(power_hi * square_hi, SCALE)
    tail_hi = _ceil(9 * power_hi, 4 * (2 * TERMS + 1))
    return 2 * total_lo, 2 * total_hi + tail_hi


def log_enclosure(value, remaining):
    """Rigorous finite rational enclosure of the real natural logarithm."""
    _step(remaining)
    value = _exact(value)
    if value <= 0:
        gap('NUMERICAL_GAP', 'Natural logarithm requires a strictly positive ratio')
    if value == 1:
        return Enclosure(Fraction(0), Fraction(0))
    exponent = value.numerator.bit_length() - value.denominator.bit_length()
    factor = Fraction(1 << exponent) if exponent >= 0 else Fraction(1, 1 << -exponent)
    reduced = value / factor
    if reduced < 1:
        exponent -= 1
        reduced *= 2
    if not 1 <= reduced < 2:
        gap('NUMERICAL_GAP', 'Logarithm range reduction failed')
    lo, hi = _reduced_log(reduced, remaining)
    two_lo, two_hi = _reduced_log(Fraction(2), remaining)
    lo += exponent * (two_lo if exponent >= 0 else two_hi)
    hi += exponent * (two_hi if exponent >= 0 else two_lo)
    return Enclosure(Fraction(lo, SCALE), Fraction(hi, SCALE))


@dataclass(frozen=True)
class BoundedValue(Value):
    def public(self):
        if isinstance(self.value, Enclosure):
            return {'type': self.kind, 'unit': self.unit,
                    'value': self.value.public(), 'missing': self.missing}
        return super().public()


def _contains_log(node):
    return node.op == 'ln' or any(_contains_log(child) for child in node.children)


class BoundedReferenceEngine(ReferenceEngine):
    """Explicit AST2 capability; only an outcome caller may enable logarithms."""

    def __init__(self, catalog, rows, *, allow_log=False):
        if type(allow_log) is not bool:
            gap('LANGUAGE_GAP', 'Outcome capability must be an explicit Boolean')
        super().__init__(catalog, rows)
        self.allow_log = allow_log
        self._new_operators = False

    def _program_node(self, program):
        if type(program) is not dict:
            return super()._program_node(program)
        previous = self._new_operators
        self._new_operators = program.get('schema') == 'research-ast/2'
        try:
            return super()._program_node({**program, 'schema': 'research-ast/1'}
                                         if self._new_operators else program)
        finally:
            self._new_operators = previous

    def describe(self, program):
        result = super().describe(program)
        result['parameter_paths'] = []
        def visit(node, path):
            if node['op'] == 'literal':
                result['parameter_paths'].append(path + '/value')
            if node['op'] in ('lag', 'trailing_mean', 'trailing_median'):
                result['parameter_paths'].append(path + '/bars')
            for key in ('arg', 'left', 'right'):
                if key in node:
                    visit(node[key], path + '/' + key)
        visit(program['expression'], '/expression')
        return result

    def _compile(self, expression, depth, count):
        if type(expression) is not dict:
            return super()._compile(expression, depth, count)
        op = expression.get('op')
        if op in ('trailing_median', 'ln') and not self._new_operators:
            gap('LANGUAGE_GAP', 'New primitive requires the optional research-ast/2 version')
        if op == 'trailing_median':
            node = super()._compile({**expression, 'op': 'trailing_mean'}, depth, count)
            if _contains_log(node):
                gap('NUMERICAL_GAP', 'Median of bounded inputs is outside this executable subset')
            return Node(op, node.kind, node.unit, node.children, node.parameter)
        if op == 'ln':
            count[0] += 1
            if depth >= 32 or count[0] > 256:
                gap('RESOURCE_GAP', 'Expression exceeds its fixed node/depth limit')
            if not self.allow_log or set(expression) != {'op', 'arg'}:
                gap('LANGUAGE_GAP', 'Logarithm requires an exact outcome-only operator envelope')
            child = self._compile(expression['arg'], depth + 1, count)
            if child.kind != 'real' or child.unit != 'ratio':
                gap('TYPE_GAP', 'Logarithm requires a dimensionless real ratio')
            if _contains_log(child):
                gap('NUMERICAL_GAP', 'Nested logarithms are outside this executable subset')
            return Node(op, 'real', 'ratio', (child,))
        node = super()._compile(expression, depth, count)
        if _contains_log(node) and node.op in ('lt', 'le', 'gt', 'ge', 'eq', 'and', 'or', 'not', 'trailing_mean'):
            gap('NUMERICAL_GAP', 'Decision/window over bounded outcomes is outside this executable subset')
        return node

    @staticmethod
    def _present(node, value):
        if isinstance(value, Enclosure):
            return BoundedValue(node.kind, node.unit, value)
        return ReferenceEngine._present(node, value)

    def _calculate(self, node, when, instrument, cutoff, remaining, trace=None):
        if node.op not in ('ln', 'trailing_median'):
            return super()._calculate(node, when, instrument, cutoff, remaining, trace)
        _step(remaining)
        present = (when, instrument) in self.lookup
        required = self._requires_observation(node)
        if trace is not None and self._traces_observation(node):
            trace(when, None, 'observation' if present else 'missing_observation')
        if not present and required and trace is None:
            return self._missing(node, 'missing_observation')
        if node.op == 'trailing_median':
            values, incomplete = [], not present and required
            for offset in range(node.parameter):
                value = self._calculate(node.children[0], when - 900 * offset,
                                        instrument, cutoff, remaining, trace)
                if value.missing:
                    if trace is None:
                        return self._missing(node, 'incomplete_window')
                    incomplete = True
                else:
                    values.append(_exact(value.value))
            if incomplete:
                return self._missing(node, 'incomplete_window' if present or not required else 'missing_observation')
            values.sort()
            middle = len(values) // 2
            median = values[middle] if len(values) % 2 else (values[middle - 1] + values[middle]) / 2
            return self._present(node, median)
        value = self._calculate(node.children[0], when, instrument, cutoff, remaining, trace)
        if not present and required:
            return self._missing(node, 'missing_observation')
        if value.missing:
            return self._missing(node, value.missing)
        if value.value <= 0:
            if trace is not None:
                trace(when, None, 'log_domain')
            return self._missing(node, 'log_domain')
        return self._present(node, log_enclosure(value.value, remaining))
