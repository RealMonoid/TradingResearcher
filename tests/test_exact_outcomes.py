"""Compatibility and resource observations for the opt-in D097 case layer."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import json
from pathlib import Path
import unittest

from trading_researcher.bounded_outcomes import REQUEST as OLD_REQUEST
from trading_researcher.codec import digest
from trading_researcher.exact_outcomes import (
    REQUEST, add_exact_diagnostics, exact_base_projection, exact_contrast,
    materialize_exact,
)
from trading_researcher.expressions import ExpressionGap
from trading_researcher.required_inputs import (
    add_required_diagnostics, materialize_required, required_contrast,
)


D = 900
T = 1672531200
CATALOG = {'x@1': {'type': 'real', 'unit': 'ratio'},
           'flag@1': {'type': 'boolean', 'unit': None}}


def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def expression(op, **fields):
    return {'op': op, **fields}


def literal(value, unit='ratio'):
    return expression('literal', type='real', unit=unit, value=str(value))


def program(node, schema='research-ast/4'):
    return {'schema': schema, 'catalog_hash': digest(CATALOG), 'expression': node}


def request():
    return {'schema': REQUEST, 'candidate_ref': 'synthetic-compatibility',
        'data_snapshot_ref': 'synthetic-not-evidence',
        'scope_program': program(expression('literal', type='boolean', unit=None, value=True)),
        'condition_program': program(expression('lag', arg=expression('feature', ref='flag@1'), bars=1)),
        'outcome_program': program(expression('mul', left=literal(1, 'basis_points'),
            right=expression('lag', arg=expression('feature', ref='x@1'), bars=1))),
        'outcome_scale': 'quantity', 'horizon_bars': 2,
        'universe': {'start': utc(T), 'end': utc(T + 9 * D), 'instruments': ['B', 'A']},
        'as_of': utc(T + 9 * D), 'max_steps': 100_000}


def history():
    return [{'time': T + i * D, 'instrument': symbol, 'features': {
        'x@1': {'value': str(i + (1 if symbol == 'A' else 2)), 'available_at': T + (i + 1) * D},
        'flag@1': {'value': (True, False, None)[i % 3], 'available_at': T + (i + 1) * D}}}
        for i in range(9) for symbol in ('A', 'B')]


def old_request(req):
    req = deepcopy(req)
    req['schema'] = OLD_REQUEST
    for key in ('scope_program', 'condition_program', 'outcome_program'):
        req[key]['schema'] = 'research-ast/2'
    return req


class ExactOutcomeCompatibility(unittest.TestCase):
    def test_common_language_case_values_and_diagnostics_match_old_version(self):
        for scenario in ('observed', 'missing', 'late', 'future', 'budget', 'scope_false', 'scope_unknown'):
            req, rows = request(), history()
            if scenario == 'missing':
                rows[4]['features']['x@1']['value'] = None
            elif scenario == 'late':
                rows[4]['features']['x@1']['available_at'] = T + 10 * D
            elif scenario == 'future':
                req['as_of'] = utc(T + 4 * D)
            elif scenario == 'budget':
                req['max_steps'] = 40
            elif scenario.startswith('scope_'):
                req['scope_program']['expression']['value'] = False if scenario == 'scope_false' else None
            with self.subTest(scenario=scenario):
                current = materialize_exact(req, CATALOG, rows)
                previous = materialize_required(old_request(req), CATALOG, rows)
                # Compare every common field, not just a selected outcome.
                current_projection = deepcopy(current)
                current_projection['schema'] = previous['schema']
                current_projection['request'] = old_request(req)
                current_projection.pop('expression_contract')
                self.assertEqual(current_projection, previous)
                current_contrast, previous_contrast = exact_contrast(current), required_contrast(previous)
                current_contrast.pop('expression_contract')
                current_contrast['schema'] = previous_contrast['schema']
                self.assertEqual(current_contrast, previous_contrast)
                remaining = req['max_steps'] - current['primitive_steps']
                current_diagnostic = add_exact_diagnostics(current, CATALOG, rows, remaining)
                previous_diagnostic = add_required_diagnostics(previous, CATALOG, rows, remaining)
                self.assertEqual(current_diagnostic['cases'], previous_diagnostic['cases'])
                self.assertEqual(current_diagnostic['diagnostics'], previous_diagnostic['diagnostics'])
                self.assertEqual(exact_base_projection(current_diagnostic), current)

    def test_multi_instrument_order_is_deterministic_and_unsorted_rows_are_rejected(self):
        req, rows = request(), history()
        baseline = materialize_exact(req, CATALOG, rows)
        self.assertEqual([(c['decision_time'], c['instrument']) for c in baseline['cases']],
                         [(T + i * D, symbol) for i in range(9) for symbol in ('A', 'B')])
        self.assertEqual(materialize_exact(req, CATALOG, rows), baseline)
        remaining = req['max_steps'] - baseline['primitive_steps']
        diagnostic = add_exact_diagnostics(baseline, CATALOG, rows, remaining)
        self.assertEqual(exact_base_projection(diagnostic), baseline)
        self.assertEqual(diagnostic, add_exact_diagnostics(baseline, CATALOG, rows, remaining))
        for callback in (lambda: materialize_exact(req, CATALOG, list(reversed(rows))),
                         lambda: add_exact_diagnostics(baseline, CATALOG, list(reversed(rows)), remaining)):
            with self.assertRaises(ExpressionGap) as caught:
                callback()
            self.assertEqual(caught.exception.code, 'DATA_GAP')

    def test_complete_boolean_window_false_unknown_retains_all_raw_dependencies(self):
        req, rows = request(), history()
        all_flags = expression('trailing_all', bars=3, arg=expression('feature', ref='flag@1'))
        req['condition_program'] = program(expression('lag', bars=1, arg=all_flags))
        rows[5]['features']['flag@1']['value'] = None
        base = materialize_exact(req, CATALOG, rows)
        # At t=3 the complete previous window is true,false,unknown: Kleene false.
        case = next(c for c in base['cases'] if c['decision_time'] == T + 3 * D and c['instrument'] == 'B')
        self.assertIs(case['condition'], False)
        diag = add_exact_diagnostics(base, CATALOG, rows, req['max_steps'] - base['primitive_steps'])
        observed = next(c for c in diag['cases'] if c['decision_time'] == T + 3 * D and c['instrument'] == 'B')
        self.assertIn('missing_value', observed['diagnostics']['reason_categories'])
        self.assertTrue(any(e['observation_time'] == T + 2 * D
                            and e['path'] == '/expression/arg/arg'
                            for e in observed['diagnostics']['events']))
        self.assertEqual(exact_base_projection(diag), base)

    def test_original_shape_shared_budget_is_observed_not_assumed(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures' /
            'exact_composition_shape_2026-11-01.json').read_text(encoding='utf-8'))
        req = request()
        req['universe'].update(end=utc(T + 55 * D), instruments=['BTCUSDT'])
        req.update(horizon_bars=5, as_of=utc(T + 55 * D), max_steps=1_000_000)
        for name in ('scope', 'condition', 'outcome'):
            req[name + '_program'] = deepcopy(fixture['programs'][name])
        rows = []
        for i in range(55):
            values = {'H': '120', 'L': '80', 'C': '100', 'Q': '100', 'B': '50'}
            if i == 39:
                values.update(H='100.5', L='100', Q='250', B='125')
            rows.append({'time': T + i * D, 'instrument': 'BTCUSDT', 'features': {
                ref + '@1': {'value': value, 'available_at': T + (i + 1) * D}
                for ref, value in values.items()}})
        base = materialize_exact(req, fixture['catalog'], rows)
        diagnostic = add_exact_diagnostics(base, fixture['catalog'], rows,
            req['max_steps'] - base['primitive_steps'])
        self.assertTrue(base['processing_complete'])
        self.assertEqual(diagnostic['diagnostics']['status'], 'COMPLETE')
        self.assertEqual(exact_base_projection(diagnostic), base)
        self.assertLessEqual(base['primitive_steps'] + diagnostic['diagnostics']['primitive_steps'], req['max_steps'])
        self.assertEqual(exact_contrast(base)['condition_count'], 1)
        self.assertEqual(exact_contrast(base)['scope_count'], 50)
        effect = exact_contrast(base)['effect']
        self.assertEqual([Fraction(int(effect[side]['numerator']), int(effect[side]['denominator']))
                          for side in ('lower', 'upper')], [0, 0])
        # Replaying under a genuinely insufficient remainder preserves the base.
        stopped = add_exact_diagnostics(base, fixture['catalog'], rows, 1)
        self.assertFalse(stopped['diagnostics']['processing_complete'])
        self.assertEqual(stopped['diagnostics']['processed_cases'], 0)
        self.assertEqual(exact_base_projection(stopped), base)


if __name__ == '__main__':
    unittest.main()
