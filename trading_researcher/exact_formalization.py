"""Opt-in D097 structural drafts; no semantic or scientific certificate."""
from .codec import Invalid, canonical, strings, text
from .exact_compositions import CONTRACT, SCHEMA as AST, ExactCompositionEngine
from .expressions import gap
from .formalization import (CANDIDATE_FIELDS, REQUIRED_BEFORE_FREEZE, fields,
                            pointer, semantic_check, utc, validate_inputs)

SCHEMA = 'formalization-record/3'
EXEC = 'hypothesis-exec/3'
EVALUATION = 'required-inputs/1'
REPORTING = 'case-diagnostics/2'


def assess_candidate(idea_id, original_text, candidate, semantic_report, catalog, allowed_refs):
    """Preserve the scalar assessment backbone with explicit new schema/engine."""
    try:
        fields(candidate, CANDIDATE_FIELDS)
        if candidate['schema'] != EXEC:
            gap('LANGUAGE_GAP', 'Exact compositions require the explicit H_exec version')
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
        if any(estimand[key] != value for key,value in expected.items()):
            gap('EVALUATION_GAP', 'Estimator semantics are not the installed canonical contrast')
        if estimand['direction'] not in ('positive', 'negative', 'nondirectional'):
            gap('EVALUATION_GAP', 'A different effect contract requires an explicit evaluation profile')
        fields(candidate['outcome'], {'program', 'scale'})
        fields(candidate['horizons'], {'grid_seconds', 'outcome_bars'})
        horizon = candidate['horizons']['outcome_bars']
        if type(candidate['horizons']['grid_seconds']) is not int or candidate['horizons']['grid_seconds'] != 900:
            gap('TEMPORAL_GAP', 'This expression slice uses the adopted 900-second grid')
        if type(horizon) is not int or not 1 <= horizon <= 1000000:
            gap('TEMPORAL_GAP', 'An explicit positive bounded outcome horizon is required')
        universe = candidate['test_universe']
        fields(universe, {'instruments', 'start', 'end', 'data_snapshot_ref'})
        strings(universe['instruments'], 'instruments')
        if len(universe['instruments']) != 1:
            gap('EVALUATION_GAP', 'This opt-in D097 adapter requires a single instrument')
        if utc(universe['start']) >= utc(universe['end']):
            gap('DATA_GAP', 'Requested universe has an invalid interval')
        if type(universe['data_snapshot_ref']) is not str or universe['data_snapshot_ref'] not in allowed_refs:
            gap('DATA_GAP', 'Requested data snapshot is not authorized in this attempt')
        # Compilation has no market input. Preserve the inherited engine's
        # nonempty row-shape prerequisite with the same static coordinate used
        # by legacy formalization; no feature is evaluated or synthesized.
        static = [{'time':0,'instrument':'static-validation','features':{}}]
        engine = ExactCompositionEngine(catalog, static)
        outcome_engine = ExactCompositionEngine(catalog, static, allow_log=True)
        programs = (('/scope_ast', candidate['scope_ast']), ('/condition_ast', candidate['condition_ast']),
                    ('/outcome/program', candidate['outcome']['program']))
        if any(type(program) is not dict or program.get('schema') != AST for _,program in programs):
            gap('LANGUAGE_GAP', 'Each program requires the explicit research-ast/4 version')
        descriptions = {path:(outcome_engine if path == '/outcome/program' else engine).describe(program)
                        for path,program in programs}
        if any(descriptions[path]['type'] != 'boolean' for path in ('/scope_ast','/condition_ast')):
            gap('TYPE_GAP', 'Scope and condition require Boolean programs')
        outcome = descriptions['/outcome/program']
        if candidate['outcome']['scale'] != 'quantity':
            gap('EVALUATION_GAP', 'This descriptive exact-composition adapter supports the existing quantity estimator')
        if outcome['type'] != 'real' or outcome['unit'] != 'basis_points' or estimand['unit'] != outcome['unit']:
            gap('TYPE_GAP', 'This bounded quantity adapter requires matching basis_points units')
        if not outcome['feature_refs']:
            gap('LANGUAGE_GAP', 'The required-input profile needs an actual raw outcome feature')
        references, required_paths = set(), {'/horizons/outcome_bars'}
        for path,description in descriptions.items():
            references.update(description['feature_refs'])
            required_paths.update(path+suffix for suffix in description['parameter_paths'])
        strings(candidate['feature_refs'], 'feature_refs')
        if set(candidate['feature_refs']) != references:
            gap('FEATURE_GAP', 'Declared feature closure does not match the programs')
        origins = candidate['parameter_origins']
        if type(origins) is not list or len(origins) > 256:
            gap('SEMANTIC_AMBIGUITY', 'Parameter origins require a bounded list')
        observed_paths = set()
        for origin in origins:
            fields(origin, {'path','basis','source_refs','rationale'}, 'SEMANTIC_AMBIGUITY')
            pointer(candidate, origin['path'])
            if origin['path'] in observed_paths:
                gap('SEMANTIC_AMBIGUITY', 'A parameter has conflicting duplicate origin records')
            observed_paths.add(origin['path'])
            if origin['basis'] not in ('preexisting_specification','development_observation'):
                gap('SEMANTIC_AMBIGUITY', 'Parameter origin is not assigned to a permitted basis')
            strings(origin['source_refs'], 'parameter source_refs')
            text(origin['rationale'], 'parameter rationale')
            if not set(origin['source_refs']) <= set(allowed_refs):
                gap('DATA_GAP', 'A parameter source is outside the authorized snapshot')
            if origin['basis'] == 'development_observation' and not origin['source_refs']:
                gap('DATA_GAP', 'Development-derived parameters require retained source references')
        if not required_paths <= observed_paths:
            gap('SEMANTIC_AMBIGUITY', 'Literal, window, exponent or horizon parameter origins are incomplete')
        return {'status':'STRUCTURE_CHECKED','stage':'FORMALIZING','gap':None,
            'mapping_authority':'formalizer_assertion_not_independent_semantic_certification',
            'required_before_freeze':REQUIRED_BEFORE_FREEZE,'programs':descriptions}
    except Invalid as exc:
        return {'status':'RETAINED_GAP','stage':'FORMALIZING',
            'gap':{'code':getattr(exc,'code','LANGUAGE_GAP'),'reason':str(exc),
                'reopen_condition':'Resolve the named meaning/capability/input gap under approved semantics'},
            'mapping_authority':'unverified_formalizer_assertion','required_before_freeze':REQUIRED_BEFORE_FREEZE}


def validate_record(record, sources):
    fields(record, {'schema','idea_id','catalog_id','original_idea','candidate','semantic_report',
        'authorization_snapshot','created_at','assessment','scientific_readiness',
        'expression_contract','evaluation_contract','reporting_contract'})
    if (record['schema'] != SCHEMA or record['expression_contract'] != CONTRACT
            or record['evaluation_contract'] != EVALUATION or record['reporting_contract'] != REPORTING
            or record['scientific_readiness'] is not False):
        raise Invalid('Expected an explicitly versioned descriptive exact-composition draft')
    utc(record['created_at'])
    lookup = {source['id']:source for source in sources}
    if record['authorization_snapshot'] != sorted(lookup):
        raise Invalid('Formalization authorization snapshot differs from artifact ancestry')
    if record['idea_id'] not in lookup or record['catalog_id'] not in lookup:
        raise Invalid('Original idea/catalog is absent from retained provenance')
    idea,catalog = lookup[record['idea_id']]['body'],lookup[record['catalog_id']]['body']
    validate_inputs(idea,catalog)
    if idea != record['original_idea']:
        raise Invalid('Original idea bytes/meaning were replaced in the retained record')
    expected = assess_candidate(record['idea_id'],idea['content']['text'],record['candidate'],
        record['semantic_report'],catalog['features'],set(lookup))
    if canonical(record['assessment']) != canonical(expected):
        raise Invalid('Exact-composition assessment differs from structural recalculation')
