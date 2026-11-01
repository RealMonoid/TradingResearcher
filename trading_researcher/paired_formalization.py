"""D094 static paired draft validator; legacy formalization remains byte-identical.

The assessment backbone is copied from the pinned legacy validator with explicit
schema, pair and engine substitutions only. No runtime monkeypatch or eval.
"""
from .codec import Invalid, canonical, strings, text
from .errors import Denied
from .expressions import gap
from .formalization import (fields, utc, pointer, semantic_check, validate_inputs,
                            CANDIDATE_FIELDS, REQUIRED_BEFORE_FREEZE)
from .paired_development import PairedReferenceEngine, validate_pair, CONTRACT

SCHEMA = 'formalization-record/2'

def assess_candidate(idea_id, original_text, candidate, semantic_report, catalog, allowed_refs, feature_definitions):
    """Deterministic draft analysis, retaining unsupported candidates without coercion."""
    try:
        fields(candidate, CANDIDATE_FIELDS)
        if candidate['schema'] != 'hypothesis-exec/2':
            gap('LANGUAGE_GAP', 'Unsupported H_exec schema version')
        if candidate['idea_ref'] != idea_id:
            gap('SEMANTIC_AMBIGUITY', 'Candidate names a different original idea')
        semantic_check(semantic_report, original_text, candidate)
        if candidate['claim_kind'] not in ('difference', 'association', 'change', 'boundary', 'interaction'):
            gap('LANGUAGE_GAP', 'Relationship form is not yet represented')
        if candidate['claim_kind'] != 'difference':
            gap('EVALUATION_GAP', 'This retained relationship requires its own installed estimator')
        if candidate['comparator'] != {'kind': 'whole_scope'}:
            gap('EVALUATION_GAP', 'The canonical contrast cannot substitute a complement comparator')
        estimand = candidate['estimand']
        fields(estimand, {'kind', 'unit', 'weighting', 'missingness', 'condition_unknown', 'nuisance_fit', 'direction'})
        expected = {'kind': 'conditional-minus-scope-mean/1', 'weighting': 'equal_rows',
                    'missingness': 'scope-true-outcome-observed/1',
                    'condition_unknown': 'exclude-from-condition-retain-in-scope', 'nuisance_fit': 'none'}
        if any(estimand[key] != value for key, value in expected.items()):
            gap('EVALUATION_GAP', 'Estimator semantics are not the installed canonical contrast')
        if estimand['direction'] not in ('positive', 'negative', 'nondirectional'):
            gap('EVALUATION_GAP', 'A different effect contract requires an explicit evaluation profile')
        fields(candidate['outcome'], {'program', 'scale'})
        fields(candidate['horizons'], {'grid_seconds', 'outcome_bars'})
        horizon = candidate['horizons']['outcome_bars']
        if candidate['horizons']['grid_seconds'] != 900 or type(candidate['horizons']['grid_seconds']) is not int:
            gap('TEMPORAL_GAP', 'This expression slice uses the adopted 900-second grid')
        if type(horizon) is not int or not 1 <= horizon <= 1000000:
            gap('TEMPORAL_GAP', 'An explicit positive bounded outcome horizon is required')
        universe = candidate['test_universe']
        fields(universe, {'pair', 'start', 'end', 'data_snapshot_ref'})
        validate_pair(universe['pair'])
        if not universe['pair'] or utc(universe['start']) >= utc(universe['end']):
            gap('DATA_GAP', 'Requested universe is empty or has an invalid interval')
        if type(universe['data_snapshot_ref']) is not str or universe['data_snapshot_ref'] not in allowed_refs:
            gap('DATA_GAP', 'Requested data snapshot is not authorized in this attempt')
        engine = PairedReferenceEngine(catalog, [], feature_definitions, pair=universe['pair'])
        outcome_engine = PairedReferenceEngine(catalog, [], feature_definitions, pair=universe['pair'], allow_log=True)
        if candidate['outcome']['scale'] != 'quantity' or candidate['estimand']['unit'] != 'basis_points':
            gap('EVALUATION_GAP', 'Paired development requires the adopted basis-point quantity contrast')
        descriptions = {path: (outcome_engine if path == '/outcome/program' else engine).describe(program) for path, program in (
            ('/scope_ast', candidate['scope_ast']), ('/condition_ast', candidate['condition_ast']),
            ('/outcome/program', candidate['outcome']['program']))}
        if any(descriptions[path]['type'] != 'boolean' for path in ('/scope_ast', '/condition_ast')):
            gap('TYPE_GAP', 'Scope and condition require Boolean programs')
        outcome = descriptions['/outcome/program']
        scale = candidate['outcome']['scale']
        if scale == 'binary_probability':
            if outcome['type'] != 'boolean' or estimand['unit'] != 'ratio':
                gap('TYPE_GAP', 'Binary probability requires Boolean outcomes and dimensionless contrast')
        elif scale == 'quantity':
            if outcome['type'] != 'real' or estimand['unit'] != outcome['unit']:
                gap('TYPE_GAP', 'Quantity outcome and estimand units do not agree')
        else:
            gap('LANGUAGE_GAP', 'Unsupported outcome scale')
        references = set()
        required_paths = {'/horizons/outcome_bars'}
        for path, description in descriptions.items():
            references.update(description['feature_refs'])
            required_paths.update(path + item for item in description['parameter_paths'])
        strings(candidate['feature_refs'], 'feature_refs')
        if set(candidate['feature_refs']) != references:
            gap('FEATURE_GAP', 'Declared feature closure does not match the programs')
        origins = candidate['parameter_origins']
        if type(origins) is not list or len(origins) > 256:
            gap('SEMANTIC_AMBIGUITY', 'Parameter origins require a bounded list')
        observed_paths = set()
        for origin in origins:
            fields(origin, {'path', 'basis', 'source_refs', 'rationale'}, 'SEMANTIC_AMBIGUITY')
            pointer(candidate, origin['path'])
            if origin['path'] in observed_paths:
                gap('SEMANTIC_AMBIGUITY', 'A parameter has conflicting duplicate origin records')
            observed_paths.add(origin['path'])
            if origin['basis'] not in ('preexisting_specification', 'development_observation'):
                gap('SEMANTIC_AMBIGUITY', 'Parameter origin is not assigned to a permitted basis')
            strings(origin['source_refs'], 'parameter source_refs')
            text(origin['rationale'], 'parameter rationale')
            if not set(origin['source_refs']) <= set(allowed_refs):
                gap('DATA_GAP', 'A parameter source is outside the authorized snapshot')
            if origin['basis'] == 'development_observation' and not origin['source_refs']:
                gap('DATA_GAP', 'Development-derived parameters require retained source references')
        if not required_paths <= observed_paths:
            gap('SEMANTIC_AMBIGUITY', 'Literal, window or horizon parameter origins are incomplete')
        return {'status': 'STRUCTURE_CHECKED', 'stage': 'FORMALIZING', 'gap': None,
                'mapping_authority': 'formalizer_assertion_not_independent_semantic_certification',
                'required_before_freeze': REQUIRED_BEFORE_FREEZE, 'programs': descriptions}
    except Invalid as exc:
        return {'status': 'RETAINED_GAP', 'stage': 'FORMALIZING',
                'gap': {'code': getattr(exc, 'code', 'LANGUAGE_GAP'), 'reason': str(exc),
                        'reopen_condition': 'Resolve the named meaning/capability/input gap under approved semantics'},
                'mapping_authority': 'unverified_formalizer_assertion',
                'required_before_freeze': REQUIRED_BEFORE_FREEZE}

def definitions_from_sources(sources, definition_ids, catalog_id):
    lookup={item['id']:item for item in sources}
    strings(definition_ids,'definition identities')
    if not definition_ids or len(definition_ids)>16:
        raise Invalid('Explicit bounded owned feature definitions required')
    result=[]
    for identity in definition_ids:
        item=lookup.get(identity)
        if (item is None or item['creator']!='controller' or item['data_class']!='development'
                or item['body'].get('schema')!='feature-definitions/1'
                or catalog_id not in item['body'].get('input_refs',[])):
            raise Denied('Paired definitions lack exact owned catalog provenance')
        result.extend(item['body']['definitions'])
    return result


def validate_record(record,sources):
    fields(record,{'schema','idea_id','catalog_id','original_idea','candidate','semantic_report',
                   'authorization_snapshot','created_at','assessment','scientific_readiness',
                   'paired_contract','definition_ids'})
    if (record['schema']!=SCHEMA or record['paired_contract']!=CONTRACT
            or record['scientific_readiness'] is not False):
        raise Invalid('Expected a descriptive paired formalization')
    utc(record['created_at'])
    lookup={item['id']:item for item in sources}
    if record['authorization_snapshot']!=sorted(lookup):
        raise Invalid('Paired formalization ancestry differs')
    if record['idea_id'] not in lookup or record['catalog_id'] not in lookup:
        raise Denied('Original paired idea and catalog must be authorized')
    idea,catalog=(lookup[record[key]]['body'] for key in ('idea_id','catalog_id'))
    validate_inputs(idea,catalog)
    if record['original_idea']!=idea:
        raise Invalid('Original paired idea was replaced')
    definitions=definitions_from_sources(sources,record['definition_ids'],record['catalog_id'])
    expected=assess_candidate(record['idea_id'],idea['content']['text'],record['candidate'],
        record['semantic_report'],catalog['features'],set(lookup),definitions)
    if canonical(record['assessment'])!=canonical(expected):
        raise Invalid('Paired formalization assessment differs from structural recalculation')
