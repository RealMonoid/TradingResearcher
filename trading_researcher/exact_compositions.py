"""Opt-in D097 scalar AST4; old engines and language versions are unchanged."""
from fractions import Fraction

from .bounded_math import Enclosure, _contains_log, _exact, _step
from .expressions import Node, gap
from .required_inputs import RequiredInputEngine

SCHEMA = 'research-ast/4'
CONTRACT = 'bounded-exact-compositions/1.0'
MAX_INTEGER = 1000000
OPERATORS = {'integer_power', 'trailing_product', 'trailing_all', 'abs'}


def _multiply(left, right, remaining):
    """One attempted multiplication; check reduced operands and result."""
    _step(remaining)
    left, right = _exact(left), _exact(right)
    return _exact(left * right)


class ExactCompositionEngine(RequiredInputEngine):
    """Explicit AST4 capability using existing required-input/outcome modes."""

    def __init__(self, catalog, rows, *, allow_log=False):
        super().__init__(catalog, rows, allow_log=allow_log)
        self._exact_version = False

    def _program_node(self, program):
        if type(program) is not dict:
            return super()._program_node(program)
        previous = self._exact_version
        self._exact_version = program.get('schema') == SCHEMA
        try:
            inherited = {**program, 'schema': 'research-ast/2'} if self._exact_version else program
            return super()._program_node(inherited)
        finally:
            self._exact_version = previous

    def _compile(self, expression, depth, count):
        if (type(expression) is not dict or type(expression.get('op')) is not str
                or expression['op'] not in OPERATORS):
            return super()._compile(expression, depth, count)
        if not self._exact_version:
            gap('LANGUAGE_GAP', 'Exact compositions require the opt-in research-ast/4 version')
        op = expression['op']
        expected = {'op', 'arg'} | ({'exponent'} if op == 'integer_power' else
                                    {'bars'} if op in ('trailing_product', 'trailing_all') else set())
        if set(expression) != expected:
            gap('LANGUAGE_GAP', 'Exact composition has unexpected or missing fields')
        count[0] += 1
        if depth >= 32 or count[0] > 256:
            gap('RESOURCE_GAP', 'Expression exceeds its fixed node/depth limit')
        if op == 'abs' and not self.allow_log:
            gap('LANGUAGE_GAP', 'Absolute value requires explicit outcome capability')
        parameter = None
        if op != 'abs':
            name = 'exponent' if op == 'integer_power' else 'bars'
            parameter = expression[name]
            if type(parameter) is not int or parameter < 1:
                gap('TYPE_GAP', 'Exact composition needs an explicit positive integer parameter')
            if parameter > MAX_INTEGER:
                gap('RESOURCE_GAP', 'Exact composition parameter exceeds the fixed integer envelope')
        child = self._compile(expression['arg'], depth + 1, count)
        if op == 'trailing_all':
            if child.kind != 'boolean':
                gap('TYPE_GAP', 'Complete Boolean aggregation requires Boolean operands')
            return Node(op, 'boolean', None, (child,), parameter)
        if child.kind != 'real':
            gap('TYPE_GAP', 'Exact numeric compositions require real operands')
        if op in ('integer_power', 'trailing_product'):
            if child.unit != 'ratio':
                gap('TYPE_GAP', 'Power and product require dimensionless ratios')
            if _contains_log(child):
                gap('NUMERICAL_GAP', 'Power and product require exact rational operands')
        return Node(op, child.kind, child.unit, (child,), parameter)

    def describe(self, program):
        result = super().describe(program)
        paths = []
        def visit(node, path):
            if node['op'] == 'literal':
                paths.append(path + '/value')
            if node['op'] in ('lag', 'trailing_mean', 'trailing_median', 'trailing_product', 'trailing_all'):
                paths.append(path + '/bars')
            if node['op'] == 'integer_power':
                paths.append(path + '/exponent')
            for key in ('arg', 'left', 'right'):
                if key in node:
                    visit(node[key], path + '/' + key)
        visit(program['expression'], '/expression')
        return {**result, 'parameter_paths': paths}

    def _calculate(self, node, when, instrument, cutoff, remaining, trace=None):
        if node.op not in OPERATORS:
            return super()._calculate(node, when, instrument, cutoff, remaining, trace)
        _step(remaining)
        child = node.children[0]
        if node.op in ('trailing_product', 'trailing_all'):
            product, unknown, false = Fraction(1), False, False
            for offset in range(node.parameter - 1, -1, -1):
                _step(remaining)
                value = self._calculate(child, when - 900 * offset, instrument, cutoff, remaining, trace)
                if value.missing or value.value is None:
                    unknown = True
                elif node.op == 'trailing_product':
                    product = _multiply(product, value.value, remaining)
                elif value.value is False:
                    false = True
            if node.op == 'trailing_all':
                if false:
                    return self._present(node, False)
                return self._missing(node, 'unknown_boolean') if unknown else self._present(node, True)
            return self._missing(node, 'incomplete_window') if unknown else self._present(node, product)
        value = self._calculate(child, when, instrument, cutoff, remaining, trace)
        if value.missing or value.value is None:
            return self._missing(node, value.missing or 'missing_value')
        if node.op == 'abs':
            if isinstance(value.value, Enclosure):
                lo, hi = value.value.lower, value.value.upper
                result = (value.value if lo >= 0 else Enclosure(-hi, -lo) if hi <= 0
                          else Enclosure(Fraction(0), max(-lo, hi)))
            else:
                result = abs(_exact(value.value))
            return self._present(node, result)
        factor, result, exponent = _exact(value.value), Fraction(1), node.parameter
        while exponent:
            _step(remaining)
            if exponent & 1:
                result = _multiply(result, factor, remaining)
            exponent //= 2
            if exponent:
                factor = _multiply(factor, factor, remaining)
        return self._present(node, result)
