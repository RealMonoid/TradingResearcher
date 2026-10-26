"""Reference AST conformance against separately authored, fixed expected cases."""
import copy
import json
from pathlib import Path
import unittest

from trading_researcher.codec import digest
from trading_researcher.expressions import ExpressionGap, ReferenceEngine


class ExpressionTests(unittest.TestCase):
    def test_independent_golden_cases(self):
        bundle = json.loads((Path(__file__).parent / 'fixtures/reference_expression_cases.json').read_text(encoding='utf-8'))
        self.assertEqual(bundle['schema'], 'reference-expression-cases/1')
        self.assertGreaterEqual(len(bundle['cases']), 20)
        for case in bundle['cases']:
            with self.subTest(case=case['name']):
                original = copy.deepcopy(case)
                program = {'schema': 'research-ast/1', 'catalog_hash': digest(case['catalog']),
                           'expression': case['expression']}
                if 'error_code' in case:
                    with self.assertRaises(ExpressionGap) as failure:
                        ReferenceEngine(case['catalog'], case['rows']).evaluate(program, case['index'])
                    self.assertEqual(failure.exception.code, case['error_code'])
                else:
                    result = ReferenceEngine(case['catalog'], case['rows']).evaluate(program, case['index'])
                    self.assertEqual(result, case['expected'])
                self.assertEqual(case, original)

    def test_program_cannot_substitute_a_different_catalog_version(self):
        engine = ReferenceEngine({}, [{'time': 0, 'instrument': 'A', 'features': {}}])
        with self.assertRaises(ExpressionGap) as failure:
            engine.evaluate({'schema': 'research-ast/1', 'catalog_hash': 'wrong',
                             'expression': {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}}, 0)
        self.assertEqual(failure.exception.code, 'FEATURE_GAP')

    def test_finite_resource_budget_is_enforced(self):
        engine = ReferenceEngine({}, [{'time': 0, 'instrument': 'A', 'features': {}}])
        expression = {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '1'}
        for _ in range(33):
            expression = {'op': 'lag', 'arg': expression, 'bars': 0}
        with self.assertRaises(ExpressionGap) as failure:
            engine.evaluate({'schema': 'research-ast/1', 'catalog_hash': digest({}), 'expression': expression}, 0)
        self.assertEqual(failure.exception.code, 'RESOURCE_GAP')

    def test_depth_limit_counts_node_levels_including_the_root(self):
        engine = ReferenceEngine({}, [{'time': 0, 'instrument': 'A', 'features': {}}])
        expression = {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '1'}
        for _ in range(31):
            expression = {'op': 'lag', 'arg': expression, 'bars': 0}
        program = {'schema': 'research-ast/1', 'catalog_hash': digest({}), 'expression': expression}
        self.assertEqual(engine.evaluate(program, 0)['value'], {'numerator': '1', 'denominator': '1'})
        program['expression'] = {'op': 'lag', 'arg': expression, 'bars': 0}
        with self.assertRaises(ExpressionGap) as failure:
            engine.evaluate(program, 0)
        self.assertEqual(failure.exception.code, 'RESOURCE_GAP')


if __name__ == '__main__':
    unittest.main()
