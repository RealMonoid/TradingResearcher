"""Independent synthetic expectations for explicit AST4 formalization.

The portable original-A expression fixture is engineering-only. The short
synthetic text and mapping below are not the actual A, an independent meaning
review, feature certification, or research admission. No private artifact,
registry, key, provider, or empirical data is used.
"""
from copy import deepcopy
import json
from pathlib import Path
import unittest

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.errors import Denied
from trading_researcher.exact_formalization import (
    SCHEMA, CONTRACT, assess_candidate, validate_record,
)
from trading_researcher.formalization import (
    assess_candidate as legacy_assess, validate_record as legacy_validate,
)
from trading_researcher.paired_formalization import assess_candidate as paired_assess


FIXTURE = json.loads((Path(__file__).parent / 'fixtures' /
                      'exact_composition_shape_2026-11-01.json').read_text(encoding='utf-8'))
IDEA, CATALOG_ID, SNAPSHOT, UNKNOWN = ('a' * 64, 'b' * 64, 'c' * 64, 'd' * 64)
ALLOWED = {IDEA, CATALOG_ID, SNAPSHOT}
TEXT = ('Synthetic engineering idea only: heavy balanced volume with a compressed '
        '32-bar BTC log range; compare absolute one-hour endpoint log displacement '
        'against the whole eligible scope. Preserve complete validity and unknowns.')
FIELDS = {'schema', 'idea_ref', 'claim_kind', 'estimand', 'scope_ast', 'condition_ast',
          'outcome', 'comparator', 'horizons', 'test_universe', 'parameter_origins', 'feature_refs'}
FREEZE_REQUIREMENTS = {'independent_semantic_review', 'feature_certification',
                       'data_and_exposure_review', 'calibrated_evaluation_profile',
                       'complete_evaluation_plan', 'atomic_allocation_and_freeze'}


def parameter_paths(expression, path):
    """Independent syntax inventory; never obtain expectations from describe()."""
    result = []
    if expression['op'] == 'literal':
        result.append(path + '/value')
    if expression['op'] in ('lag', 'trailing_mean', 'trailing_median', 'trailing_product', 'trailing_all'):
        result.append(path + '/bars')
    if expression['op'] == 'integer_power':
        result.append(path + '/exponent')
    for field in ('arg', 'left', 'right'):
        if field in expression:
            result.extend(parameter_paths(expression[field], path + '/' + field))
    return result


def candidate():
    value = {'schema': 'hypothesis-exec/3', 'idea_ref': IDEA, 'claim_kind': 'difference',
             'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'basis_points',
                          'weighting': 'equal_rows', 'missingness': 'scope-true-outcome-observed/1',
                          'condition_unknown': 'exclude-from-condition-retain-in-scope',
                          'nuisance_fit': 'none', 'direction': 'positive'},
             'scope_ast': deepcopy(FIXTURE['programs']['scope']),
             'condition_ast': deepcopy(FIXTURE['programs']['condition']),
             'outcome': {'program': deepcopy(FIXTURE['programs']['outcome']), 'scale': 'quantity'},
             'comparator': {'kind': 'whole_scope'},
             'horizons': {'grid_seconds': 900, 'outcome_bars': 5},
             'test_universe': {'instruments': ['BTCUSDT'], 'start': '2023-01-01T00:00:00Z',
                               'end': '2023-04-01T00:00:00Z', 'data_snapshot_ref': SNAPSHOT},
             'parameter_origins': [], 'feature_refs': sorted(FIXTURE['catalog'])}
    paths = ['/horizons/outcome_bars']
    for root, expression in (
        ('/scope_ast/expression', value['scope_ast']['expression']),
        ('/condition_ast/expression', value['condition_ast']['expression']),
        ('/outcome/program/expression', value['outcome']['program']['expression']),
    ):
        paths.extend(parameter_paths(expression, root))
    value['parameter_origins'] = [
        {'path': path, 'basis': 'preexisting_specification', 'source_refs': [IDEA],
         'rationale': 'Synthetic declared commitment or exact technical composition identity; not optimized.'}
        for path in paths]
    return value


def mapping():
    return {'status': 'equivalent', 'segments': [
        {'text': TEXT, 'path': '/condition_ast/expression',
         'interpretation': 'Synthetic manual assertion only; complete independent meaning review remains required.'}],
        'differences': []}


def sources():
    idea = {'schema': 'research-record/1', 'kind': 'idea', 'content': {'text': TEXT},
            'scope': {'instrument': 'BTCUSDT', 'partition': 'development'}, 'relations': {},
            'created_at': 1, 'available_at': 1}
    return [{'id': IDEA, 'body': idea},
            {'id': CATALOG_ID, 'body': {'schema': 'feature-catalog/1', 'features': deepcopy(FIXTURE['catalog'])}},
            {'id': SNAPSHOT, 'body': {'schema': 'synthetic-source/1', 'purpose': 'No market data'}}]


def record(value=None, *, null=False):
    value = None if null else candidate() if value is None else value
    report = mapping() if value is not None else {
        'status': 'ambiguous', 'segments': [], 'differences': ['Retained synthetic expression gap.']}
    return {'schema': SCHEMA, 'idea_id': IDEA, 'catalog_id': CATALOG_ID,
            'original_idea': deepcopy(sources()[0]['body']), 'candidate': value,
            'semantic_report': report, 'authorization_snapshot': sorted(ALLOWED),
            'created_at': '2026-11-01T12:00:00Z',
            'assessment': assess_candidate(IDEA, TEXT, value, report, FIXTURE['catalog'], ALLOWED),
            'scientific_readiness': False, 'expression_contract': CONTRACT,
            'evaluation_contract': 'required-inputs/1', 'reporting_contract': 'case-diagnostics/2'}


class ExactFormalizationReview(unittest.TestCase):
    def assess(self, value=None, report=None, *, original=TEXT, catalog=None, allowed=ALLOWED):
        return assess_candidate(IDEA, original, candidate() if value is None else value,
                                mapping() if report is None else report,
                                FIXTURE['catalog'] if catalog is None else catalog, allowed)

    def assert_gap(self, result, code=None):
        self.assertEqual(result['status'], 'RETAINED_GAP')
        self.assertEqual(result['stage'], 'FORMALIZING')
        self.assertTrue(result['gap']['reason'])
        self.assertTrue(result['gap']['reopen_condition'])
        if code is not None:
            self.assertEqual(result['gap']['code'], code)
        self.assertEqual(set(result['required_before_freeze']), FREEZE_REQUIREMENTS)
        self.assertIs(result.get('scientific_readiness', False), False)

    def assert_record_rejected(self, value, supplied=None):
        with self.assertRaises((Invalid, Denied)):
            validate_record(value, sources() if supplied is None else supplied)

    def test_portable_complete_shape_is_only_structurally_checked(self):
        value, report = candidate(), mapping()
        before = canonical([value, report, FIXTURE['catalog']])
        self.assertEqual(set(value), FIELDS)
        self.assertEqual(SCHEMA, 'formalization-record/3')
        self.assertEqual(CONTRACT, 'bounded-exact-compositions/1.0')
        result = self.assess(value, report)
        self.assertEqual(result['status'], 'STRUCTURE_CHECKED')
        self.assertIsNone(result['gap'])
        self.assertEqual(result['mapping_authority'], 'formalizer_assertion_not_independent_semantic_certification')
        self.assertEqual(set(result['required_before_freeze']), FREEZE_REQUIREMENTS)
        self.assertEqual(result['programs']['/condition_ast']['type'], 'boolean')
        self.assertEqual(result['programs']['/outcome/program']['unit'], 'basis_points')
        self.assertEqual(before, canonical([value, report, FIXTURE['catalog']]))
        expected = {origin['path'] for origin in value['parameter_origins']}
        observed = {'/horizons/outcome_bars'}
        for prefix, description in result['programs'].items():
            observed.update(prefix + path for path in description['parameter_paths'])
        self.assertEqual(observed, expected)
        self.assertTrue(any(path.endswith('/exponent') for path in expected))

    def test_every_literal_window_exponent_and_horizon_origin_is_required(self):
        pristine = candidate()
        # Independent omission of every path also covers duplicate V copies,
        # the outer lag, unit-one/zero domain guards and power64.
        for index, origin in enumerate(pristine['parameter_origins']):
            changed = deepcopy(pristine)
            changed['parameter_origins'].pop(index)
            with self.subTest(path=origin['path']):
                self.assert_gap(self.assess(changed), 'SEMANTIC_AMBIGUITY')

    def test_unknown_snapshot_or_origin_source_is_not_authorized(self):
        changed = candidate()
        changed['test_universe']['data_snapshot_ref'] = UNKNOWN
        self.assert_gap(self.assess(changed), 'DATA_GAP')
        changed = candidate()
        changed['parameter_origins'][0]['source_refs'] = [UNKNOWN]
        self.assert_gap(self.assess(changed), 'DATA_GAP')
        changed = candidate()
        changed['parameter_origins'][0].update(basis='development_observation', source_refs=[])
        self.assert_gap(self.assess(changed), 'DATA_GAP')

    def test_duplicate_unsupported_and_nonexistent_origins_are_retained_gaps(self):
        for mutate in (
            lambda value: value['parameter_origins'].append(deepcopy(value['parameter_origins'][0])),
            lambda value: value['parameter_origins'][0].update(basis='selected_after_outcome'),
            lambda value: value['parameter_origins'][0].update(path='/missing/parameter'),
        ):
            changed = candidate()
            mutate(changed)
            self.assert_gap(self.assess(changed), 'SEMANTIC_AMBIGUITY')

    def test_original_text_identity_segmentation_and_json_pointer_are_exact(self):
        self.assert_gap(self.assess(original=TEXT + ' '), 'SEMANTIC_AMBIGUITY')
        changed = candidate()
        changed['idea_ref'] = UNKNOWN
        self.assert_gap(self.assess(changed), 'SEMANTIC_AMBIGUITY')
        report = mapping()
        midpoint = len(TEXT) // 2
        report['segments'] = [
            {'text': TEXT[:midpoint], 'path': '/condition_ast', 'interpretation': 'Synthetic first segment'},
            {'text': TEXT[midpoint:], 'path': '/outcome', 'interpretation': 'Synthetic second segment'}]
        self.assertEqual(self.assess(report=report)['status'], 'STRUCTURE_CHECKED')
        for path in ('/absent', '/condition_ast/~2broken', 'condition_ast'):
            altered = mapping()
            altered['segments'][0]['path'] = path
            with self.subTest(path=path):
                self.assert_gap(self.assess(report=altered), 'SEMANTIC_AMBIGUITY')

    def test_declared_ambiguity_or_difference_never_becomes_structural_acceptance(self):
        for status, differences in (('ambiguous', []), ('different', ['Different meaning']),
                                    ('equivalent', ['An unresolved mismatch remains'])):
            report = mapping()
            report.update(status=status, differences=differences)
            with self.subTest(status=status, differences=differences):
                self.assert_gap(self.assess(report=report), 'SEMANTIC_AMBIGUITY')

    def test_all_three_programs_require_explicit_ast4(self):
        for field in ('scope_ast', 'condition_ast', 'outcome'):
            for schema in ('research-ast/1', 'research-ast/2', 'research-ast/3'):
                changed = candidate()
                target = changed['outcome']['program'] if field == 'outcome' else changed[field]
                target['schema'] = schema
                with self.subTest(field=field, schema=schema):
                    self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')

    def test_old_candidate_and_parser_versions_do_not_gain_ast4(self):
        for schema in ('hypothesis-exec/1', 'hypothesis-exec/2', 'hypothesis-exec/99'):
            changed = candidate()
            changed['schema'] = schema
            with self.subTest(schema=schema):
                self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')
        args = (IDEA, TEXT, candidate(), mapping(), FIXTURE['catalog'], ALLOWED)
        self.assertEqual(legacy_assess(*args)['status'], 'RETAINED_GAP')
        self.assertEqual(paired_assess(*args, [])['status'], 'RETAINED_GAP')
        with self.assertRaises(Invalid):
            legacy_validate(record(), sources())

    def test_unsupported_estimands_are_gaps_not_reinterpreted(self):
        mutations = [
            lambda c: c.update(claim_kind='association'),
            lambda c: c.update(claim_kind='interaction'),
            lambda c: c.update(comparator={'kind': 'condition_false'}),
            lambda c: c['estimand'].update(weighting='volume'),
            lambda c: c['estimand'].update(condition_unknown='drop_from_scope'),
            lambda c: c['estimand'].update(missingness='impute_zero'),
            lambda c: c['estimand'].update(nuisance_fit='fit_from_outcomes'),
            lambda c: c['estimand'].update(direction='nonnegative'),
        ]
        for mutate in mutations:
            changed = candidate()
            mutate(changed)
            self.assert_gap(self.assess(changed), 'EVALUATION_GAP')

    def test_only_quantity_basis_points_and_real_outcomes_are_accepted(self):
        mutations = [
            lambda c: c['outcome'].update(scale='binary_probability'),
            lambda c: c['estimand'].update(unit='ratio'),
            lambda c: c['outcome'].update(program=deepcopy(c['scope_ast'])),
        ]
        for mutate in mutations:
            changed = candidate()
            mutate(changed)
            self.assert_gap(self.assess(changed))

    def test_single_instrument_universe_and_fixed_grid_remain_explicit(self):
        for instruments in ([], ['BTCUSDT', 'ETHUSDT']):
            changed = candidate()
            changed['test_universe']['instruments'] = instruments
            self.assert_gap(self.assess(changed))
        for horizon in (0, -1, True, 1_000_001):
            changed = candidate()
            changed['horizons']['outcome_bars'] = horizon
            self.assert_gap(self.assess(changed), 'TEMPORAL_GAP')
        changed = candidate()
        changed['horizons']['grid_seconds'] = 60
        self.assert_gap(self.assess(changed), 'TEMPORAL_GAP')
        changed = candidate()
        changed['test_universe']['end'] = changed['test_universe']['start']
        self.assert_gap(self.assess(changed), 'DATA_GAP')

    def test_feature_closure_catalog_binding_and_no_cross_instrument_operator(self):
        changed = candidate()
        changed['feature_refs'].pop()
        self.assert_gap(self.assess(changed), 'FEATURE_GAP')
        changed = candidate()
        changed['scope_ast']['catalog_hash'] = '0' * 64
        self.assert_gap(self.assess(changed), 'FEATURE_GAP')
        changed = candidate()
        changed['condition_ast']['expression'] = {'op': 'feature_at', 'instrument': 'ETHUSDT', 'ref': 'C@1'}
        self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')

    def test_decision_abs_or_log_cannot_hide_inside_boolean_predicates(self):
        for op in ('abs', 'ln'):
            changed = candidate()
            changed['condition_ast']['expression'] = {
                'op': 'gt', 'left': {'op': op, 'arg': {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '1'}},
                'right': {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '0'}}
            self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')

    def test_null_and_malformed_candidates_are_retained_without_replacement(self):
        for value in (None, [], {}, 'not-a-candidate'):
            result = assess_candidate(IDEA, TEXT, value, mapping(), FIXTURE['catalog'], ALLOWED)
            self.assert_gap(result, 'LANGUAGE_GAP')
        for expression in ({'op': []}, {'op': {}}, {'op': 'integer_power', 'arg': None, 'exponent': 64}):
            changed = candidate()
            changed['condition_ast']['expression'] = expression
            self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')
        changed = candidate()
        changed['scope_ast'] = []
        self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')

    def test_candidate_envelope_fields_are_exact(self):
        changed = candidate()
        changed['extra'] = 'not part of this version'
        self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')
        for key in FIELDS:
            changed = candidate()
            del changed[key]
            with self.subTest(missing=key):
                self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')

    def test_compile_limits_and_required_outcome_feature_are_not_bypassed(self):
        changed = candidate()
        expression = changed['condition_ast']['expression']
        for _ in range(33):
            expression = {'op': 'not', 'arg': expression}
        changed['condition_ast']['expression'] = expression
        self.assert_gap(self.assess(changed), 'RESOURCE_GAP')
        changed = candidate()
        changed['outcome']['program']['expression'] = {
            'op': 'literal', 'type': 'real', 'unit': 'basis_points', 'value': '1'}
        self.assert_gap(self.assess(changed), 'LANGUAGE_GAP')

    def test_record_binds_full_original_authorization_contracts_and_recalculation(self):
        value = record()
        before = canonical([value, sources()])
        validate_record(value, sources())
        self.assertEqual(before, canonical([value, sources()]))
        self.assertEqual(value['schema'], 'formalization-record/3')
        self.assertEqual(value['original_idea'], sources()[0]['body'])
        self.assertFalse(value['scientific_readiness'])
        for field, replacement in (
            ('expression_contract', 'different/1'), ('evaluation_contract', 'different/1'),
            ('reporting_contract', 'different/1'), ('schema', 'formalization-record/1'),
            ('scientific_readiness', True), ('created_at', '2026-11-01T12:00:00+00:00'),
        ):
            changed = deepcopy(value)
            changed[field] = replacement
            with self.subTest(field=field):
                self.assert_record_rejected(changed)
        changed = deepcopy(value)
        changed['original_idea']['content']['text'] += ' Modified.'
        self.assert_record_rejected(changed)
        changed = deepcopy(value)
        changed['original_idea']['scope']['partition'] = 'assessment'
        self.assert_record_rejected(changed)
        changed = deepcopy(value)
        changed['assessment']['mapping_authority'] = 'independent_semantic_certification'
        self.assert_record_rejected(changed)

    def test_authorization_snapshot_cannot_drop_add_or_reorder_sources(self):
        for identities in (sorted(ALLOWED - {SNAPSHOT}), sorted(ALLOWED | {UNKNOWN}), list(reversed(sorted(ALLOWED)))):
            changed = record()
            changed['authorization_snapshot'] = identities
            self.assert_record_rejected(changed)
        for missing in (IDEA, CATALOG_ID, SNAPSHOT):
            self.assert_record_rejected(record(), [source for source in sources() if source['id'] != missing])

    def test_valid_null_record_preserves_gap_and_rejects_forged_success(self):
        value = record(null=True)
        self.assertIsNone(value['candidate'])
        self.assert_gap(value['assessment'], 'LANGUAGE_GAP')
        validate_record(value, sources())
        changed = deepcopy(value)
        changed['assessment'] = deepcopy(record()['assessment'])
        self.assert_record_rejected(changed)

    def test_record_validator_uses_catalog_features_not_catalog_wrapper(self):
        validate_record(record(), sources())
        self.assert_gap(self.assess(catalog=sources()[1]['body']))
        changed_sources = sources()
        changed_sources[1]['body']['features']['C@1']['unit'] = 'different_unit'
        self.assert_record_rejected(record(), changed_sources)


if __name__ == '__main__':
    unittest.main()
