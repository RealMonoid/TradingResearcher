"""Exact reference calculator for research-ast/1; no scientific authority.

Only approved scalar/Boolean/lag/window meanings are executable. Supplied data
availability is enforced, not independently established. See EXPRESSIONS.md.
"""
from copy import deepcopy
from dataclasses import dataclass
from fractions import Fraction
import re

from .codec import Invalid, digest


class ExpressionGap(Invalid):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def gap(code, message):
    raise ExpressionGap(code, message)


DECIMAL = re.compile(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z')
REFERENCE = re.compile(r'[A-Za-z_][A-Za-z0-9_.-]*@[A-Za-z0-9_.-]+\Z')


@dataclass(frozen=True)
class Node:
    op: str
    kind: str
    unit: str | None
    children: tuple = ()
    parameter: object = None


@dataclass(frozen=True)
class Value:
    kind: str
    unit: str | None
    value: object = None
    missing: str | None = None

    def public(self):
        value = self.value
        if isinstance(value, Fraction):
            value = {'numerator': str(value.numerator), 'denominator': str(value.denominator)}
        return {'type': self.kind, 'unit': self.unit, 'value': value, 'missing': self.missing}


def scalar(kind, unit, value, error_code='TYPE_GAP'):
    if kind not in ('real', 'boolean'):
        gap('LANGUAGE_GAP', 'Scalar type is not supported by this reference slice')
    if kind == 'boolean':
        if unit is not None or (value is not None and type(value) is not bool):
            gap(error_code, 'Boolean requires null unit and Boolean or missing value')
        return value
    if type(unit) is not str or not unit.strip() or len(unit) > 64:
        gap(error_code, 'Real values require an explicit bounded unit')
    if value is None:
        return None
    if type(value) is not str or len(value) > 100 or not DECIMAL.fullmatch(value):
        gap(error_code, 'Real values require bounded finite plain decimal strings')
    return Fraction(value)


class ReferenceEngine:
    def __init__(self, catalog, rows):
        if type(catalog) is not dict or len(catalog) > 256:
            gap('FEATURE_GAP', 'Invalid or oversized feature catalog')
        for ref, spec in catalog.items():
            if (type(ref) is not str or len(ref) > 128 or not REFERENCE.fullmatch(ref) or type(spec) is not dict
                    or set(spec) != {'type', 'unit'}):
                gap('FEATURE_GAP', 'Feature references require exact versioned type specifications')
            scalar(spec['type'], spec['unit'], None)
        if type(rows) is not list or not 1 <= len(rows) <= 100000:
            gap('DATA_GAP', 'A bounded nonempty row snapshot is required')
        self.catalog = deepcopy(catalog)
        self.rows = []
        self.lookup = {}
        previous = None
        for row in rows:
            if (type(row) is not dict or set(row) != {'time', 'instrument', 'features'}
                    or type(row['time']) is not int or row['time'] < 0 or row['time'] % 900
                    or type(row['instrument']) is not str or not row['instrument'].strip()
                    or len(row['instrument']) > 128 or type(row['features']) is not dict):
                gap('DATA_GAP', 'Rows require exact UTC-grid, instrument and feature fields')
            key = row['time'], row['instrument']
            if previous is not None and key <= previous:
                gap('DATA_GAP', 'Rows must have strictly ordered unique time/instrument keys')
            previous = key
            samples = {}
            for ref, sample in row['features'].items():
                if ref not in self.catalog:
                    gap('FEATURE_GAP', 'Row uses an unregistered feature version')
                if (type(sample) is not dict or set(sample) != {'value', 'available_at'}
                        or type(sample['available_at']) is not int or sample['available_at'] < 0):
                    gap('DATA_GAP', 'Feature samples require value and availability instant')
                spec = self.catalog[ref]
                samples[ref] = (scalar(spec['type'], spec['unit'], sample['value'], 'DATA_GAP'),
                                sample['available_at'])
            self.rows.append(key)
            self.lookup[key] = samples

    def evaluate(self, program, index):
        node = self._program_node(program)
        if type(index) is not int or not 0 <= index < len(self.rows):
            gap('DATA_GAP', 'Evaluation row is unavailable')
        when, instrument = self.rows[index]
        return self._calculate(node, when, instrument, when, [1000000]).public()

    def describe(self, program):
        """Static closure/type description; neither data evaluation nor certification."""
        node = self._program_node(program)
        references, parameters = set(), []

        def visit(expression, path):
            if expression['op'] == 'feature':
                references.add(expression['ref'])
            if expression['op'] == 'literal':
                parameters.append(path + '/value')
            if expression['op'] in ('lag', 'trailing_mean'):
                parameters.append(path + '/bars')
            for key in ('arg', 'left', 'right'):
                if key in expression:
                    visit(expression[key], path + '/' + key)

        visit(program['expression'], '/expression')
        return {'type': node.kind, 'unit': node.unit, 'feature_refs': sorted(references),
                'parameter_paths': parameters}

    def _program_node(self, program):
        if (type(program) is not dict or set(program) != {'schema', 'catalog_hash', 'expression'}
                or program['schema'] != 'research-ast/1'):
            gap('LANGUAGE_GAP', 'Unsupported or incomplete program envelope')
        if program['catalog_hash'] != digest(self.catalog):
            gap('FEATURE_GAP', 'Program does not bind the exact feature catalog')
        return self._compile(program['expression'], 0, [0])

    def _compile(self, expression, depth, count):
        count[0] += 1
        if depth >= 32 or count[0] > 256:
            gap('RESOURCE_GAP', 'Expression exceeds its fixed node/depth limit')
        if type(expression) is not dict or type(expression.get('op')) is not str:
            gap('LANGUAGE_GAP', 'Every expression needs a named operator')
        op = expression['op']
        if op in ('outcome', 'future', 'lead', 'centered_window'):
            gap('TEMPORAL_GAP', 'Future/full-path information is unavailable to decision inputs')
        fields = {
            'literal': {'type', 'unit', 'value'}, 'feature': {'ref'},
            'not': {'arg'}, 'lag': {'arg', 'bars'}, 'trailing_mean': {'arg', 'bars'},
            **{name: {'left', 'right'} for name in ('add', 'sub', 'mul', 'div', 'lt', 'le', 'gt', 'ge', 'eq', 'and', 'or')},
        }
        if op not in fields or set(expression) != fields[op] | {'op'}:
            gap('LANGUAGE_GAP', 'Unknown operator or unexpected/missing fields')
        if op == 'literal':
            kind, unit = expression['type'], expression['unit']
            value = scalar(kind, unit, expression['value'])
            return Node(op, kind, unit, parameter=value)
        if op == 'feature':
            ref = expression['ref']
            if type(ref) is not str or ref not in self.catalog:
                gap('FEATURE_GAP', 'Feature version is not present in the bound catalog')
            spec = self.catalog[ref]
            return Node(op, spec['type'], spec['unit'], parameter=ref)
        if op in ('not', 'lag', 'trailing_mean'):
            child = self._compile(expression['arg'], depth + 1, count)
            if op == 'not':
                if child.kind != 'boolean':
                    gap('TYPE_GAP', 'NOT requires a Boolean expression')
                return Node(op, 'boolean', None, (child,))
            bars = expression['bars']
            if type(bars) is not int or bars < 0:
                gap('TEMPORAL_GAP', 'A grid shift/window requires a nonnegative integer')
            if bars > 1000000:
                gap('RESOURCE_GAP', 'Grid shift/window exceeds the resource envelope')
            if op == 'trailing_mean' and (bars == 0 or child.kind != 'real'):
                gap('TYPE_GAP', 'Trailing mean requires a positive window and real input')
            return Node(op, child.kind, child.unit, (child,), bars)
        left = self._compile(expression['left'], depth + 1, count)
        right = self._compile(expression['right'], depth + 1, count)
        children = left, right
        if op in ('and', 'or'):
            if left.kind != 'boolean' or right.kind != 'boolean':
                gap('TYPE_GAP', 'Boolean operators require Boolean operands')
            return Node(op, 'boolean', None, children)
        if op in ('lt', 'le', 'gt', 'ge', 'eq'):
            if ((left.kind, left.unit) != (right.kind, right.unit)
                    or (op != 'eq' and left.kind != 'real')):
                gap('TYPE_GAP', 'Comparison operands have incompatible types or units')
            return Node(op, 'boolean', None, children)
        if left.kind != 'real' or right.kind != 'real':
            gap('TYPE_GAP', 'Arithmetic requires real operands')
        if op in ('add', 'sub'):
            if left.unit != right.unit:
                gap('TYPE_GAP', 'Addition/subtraction require identical units')
            unit = left.unit
        elif op == 'mul':
            if left.unit != 'ratio' and right.unit != 'ratio':
                gap('TYPE_GAP', 'General compound-unit algebra is not installed')
            unit = right.unit if left.unit == 'ratio' else left.unit
        else:
            if left.unit == right.unit:
                unit = 'ratio'
            elif right.unit == 'ratio':
                unit = left.unit
            else:
                gap('TYPE_GAP', 'General compound-unit division is not installed')
        return Node(op, 'real', unit, children)

    @staticmethod
    def _present(node, value):
        if isinstance(value, Fraction) and max(value.numerator.bit_length(), value.denominator.bit_length()) > 8192:
            gap('RESOURCE_GAP', 'Exact rational exceeds the numeric resource envelope')
        return Value(node.kind, node.unit, value)

    @staticmethod
    def _missing(node, reason):
        return Value(node.kind, node.unit, None, reason)

    def _calculate(self, node, when, instrument, cutoff, remaining, trace=None):
        remaining[0] -= 1
        if remaining[0] < 0:
            gap('RESOURCE_GAP', 'Expression exhausted its primitive-step budget')
        samples = self.lookup.get((when, instrument))
        if trace is not None:
            trace(when, None, 'observation' if samples is not None else 'missing_observation')
        if samples is None:
            if trace is not None:
                # Missing arithmetic cannot conceal another declared dependency's
                # publication time. Trace the remaining tree under the same budget.
                if node.op == 'lag':
                    self._calculate(node.children[0], when - 900 * node.parameter,
                                    instrument, cutoff, remaining, trace)
                elif node.op == 'trailing_mean':
                    for offset in range(node.parameter):
                        self._calculate(node.children[0], when - 900 * offset,
                                        instrument, cutoff, remaining, trace)
                else:
                    for child in node.children:
                        self._calculate(child, when, instrument, cutoff, remaining, trace)
            return self._missing(node, 'missing_observation')
        if node.op == 'literal':
            if trace is not None and node.parameter is None:
                trace(when, None, 'missing_value')
            return self._missing(node, 'missing_value') if node.parameter is None else self._present(node, node.parameter)
        if node.op == 'feature':
            sample = samples.get(node.parameter)
            if sample is None:
                if trace is not None:
                    trace(when, None, 'missing_feature_value')
                return self._missing(node, 'missing_feature_value')
            value, available_at = sample
            if trace is not None:
                reason = ('not_yet_available' if available_at > cutoff else
                          'missing_value' if value is None else 'available')
                trace(when, available_at, reason)
            if available_at > cutoff:
                return self._missing(node, 'not_yet_available')
            return self._missing(node, 'missing_value') if value is None else self._present(node, value)
        if node.op == 'lag':
            return self._calculate(node.children[0], when - 900 * node.parameter, instrument, cutoff, remaining, trace)
        if node.op == 'trailing_mean':
            total = Fraction(0)
            incomplete = False
            for offset in range(node.parameter):
                value = self._calculate(node.children[0], when - 900 * offset, instrument, cutoff, remaining, trace)
                if value.missing:
                    if trace is None:
                        return self._missing(node, 'incomplete_window')
                    incomplete = True
                elif not incomplete:
                    total += value.value
                    self._present(node, total)
            if incomplete:
                return self._missing(node, 'incomplete_window')
            return self._present(node, total / node.parameter)
        values = [self._calculate(child, when, instrument, cutoff, remaining, trace) for child in node.children]
        if node.op == 'not':
            return self._missing(node, 'unknown_boolean') if values[0].missing else self._present(node, not values[0].value)
        left, right = values
        a, b = left.value, right.value
        if node.op == 'and':
            if a is False or b is False:
                return self._present(node, False)
            return self._missing(node, 'unknown_boolean') if left.missing or right.missing else self._present(node, True)
        if node.op == 'or':
            if a is True or b is True:
                return self._present(node, True)
            return self._missing(node, 'unknown_boolean') if left.missing or right.missing else self._present(node, False)
        if left.missing or right.missing:
            return self._missing(node, left.missing or right.missing)
        if node.op == 'div' and b == 0:
            if trace is not None:
                trace(when, None, 'division_by_zero')
            return self._missing(node, 'division_by_zero')
        operations = {'add': lambda: a + b, 'sub': lambda: a - b, 'mul': lambda: a * b,
                      'div': lambda: a / b, 'lt': lambda: a < b, 'le': lambda: a <= b,
                      'gt': lambda: a > b, 'ge': lambda: a >= b, 'eq': lambda: a == b}
        return self._present(node, operations[node.op]())
