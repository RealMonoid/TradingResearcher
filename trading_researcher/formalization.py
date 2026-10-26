"""Retained IF-03/04 drafts; structural checks do not issue scientific authority."""
from datetime import datetime, timezone
import re

from .codec import Invalid, canonical, strings, text
from .errors import Denied
from .expressions import ExpressionGap, ReferenceEngine, gap
from .memory import SCHEMA as MEMORY_SCHEMA


SCHEMA = 'formalization-record/1'
CANDIDATE_FIELDS = {'schema', 'idea_ref', 'claim_kind', 'estimand', 'scope_ast', 'condition_ast',
                    'outcome', 'comparator', 'horizons', 'test_universe', 'parameter_origins', 'feature_refs'}
REQUIRED_BEFORE_FREEZE = ['independent_semantic_review', 'feature_certification', 'data_and_exposure_review',
                          'calibrated_evaluation_profile', 'complete_evaluation_plan', 'atomic_allocation_and_freeze']


def fields(value, expected, code='LANGUAGE_GAP'):
    if type(value) is not dict or set(value) != set(expected):
        gap(code, 'Required fields are absent or unexpected')


def utc(value):
    if type(value) is not str or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', value):
        gap('DATA_GAP', 'Use an exact UTC instant ending in Z')
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        gap('DATA_GAP', 'UTC instant is invalid')


def pointer(document, path):
    if type(path) is not str or not path.startswith('/') or len(path) > 2048:
        gap('SEMANTIC_AMBIGUITY', 'A mapping requires an existing candidate JSON-pointer path')
    current = document
    for component in path[1:].split('/'):
        if re.search(r'~(?![01])', component):
            gap('SEMANTIC_AMBIGUITY', 'Malformed JSON-pointer escape')
        component = component.replace('~1', '/').replace('~0', '~')
        if type(current) is dict and component in current:
            current = current[component]
        elif type(current) is list and re.fullmatch(r'0|[1-9][0-9]*', component) and int(component) < len(current):
            current = current[int(component)]
        else:
            gap('SEMANTIC_AMBIGUITY', 'Mapping path is absent from the retained candidate')
    return current


def semantic_check(report, original_text, candidate):
    fields(report, {'status', 'segments', 'differences'}, 'SEMANTIC_AMBIGUITY')
    if report['status'] not in ('equivalent', 'ambiguous', 'different'):
        gap('SEMANTIC_AMBIGUITY', 'Unknown semantic mapping status')
    strings(report['differences'], 'semantic differences')
    if type(report['segments']) is not list or not 1 <= len(report['segments']) <= 128:
        gap('SEMANTIC_AMBIGUITY', 'Original text requires an explicit bounded mapping')
    retained = []
    for segment in report['segments']:
        fields(segment, {'text', 'path', 'interpretation'}, 'SEMANTIC_AMBIGUITY')
        retained.append(text(segment['text'], 'original segment'))
        text(segment['interpretation'], 'mapping interpretation')
        pointer(candidate, segment['path'])
    if ''.join(retained) != original_text:
        gap('SEMANTIC_AMBIGUITY', 'Mapping does not preserve the exact original idea text')
    if report['status'] != 'equivalent' or report['differences']:
        gap('SEMANTIC_AMBIGUITY', 'Declared semantic differences or ambiguity require resolution')


def assess_candidate(idea_id, original_text, candidate, semantic_report, catalog, allowed_refs):
    """Deterministic draft analysis, retaining unsupported candidates without coercion."""
    try:
        fields(candidate, CANDIDATE_FIELDS)
        if candidate['schema'] != 'hypothesis-exec/1':
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
        fields(universe, {'instruments', 'start', 'end', 'data_snapshot_ref'})
        strings(universe['instruments'], 'instruments')
        if not universe['instruments'] or utc(universe['start']) >= utc(universe['end']):
            gap('DATA_GAP', 'Requested universe is empty or has an invalid interval')
        if type(universe['data_snapshot_ref']) is not str or universe['data_snapshot_ref'] not in allowed_refs:
            gap('DATA_GAP', 'Requested data snapshot is not authorized in this attempt')
        engine = ReferenceEngine(catalog, [{'time': 0, 'instrument': 'static-validation', 'features': {}}])
        descriptions = {path: engine.describe(program) for path, program in (
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


def validate_record(record, sources):
    required = {'schema', 'idea_id', 'catalog_id', 'original_idea', 'candidate', 'semantic_report',
                'authorization_snapshot', 'created_at', 'assessment', 'scientific_readiness'}
    fields(record, required)
    if record['schema'] != SCHEMA or record['scientific_readiness'] is not False:
        raise Invalid('A formalization draft cannot confer scientific readiness')
    utc(record['created_at'])
    lookup = {source['id']: source for source in sources}
    if record['authorization_snapshot'] != sorted(lookup):
        raise Invalid('Formalization authorization snapshot differs from artifact ancestry')
    if record['idea_id'] not in lookup or record['catalog_id'] not in lookup:
        raise Invalid('Original idea/catalog is absent from retained provenance')
    idea, catalog = lookup[record['idea_id']]['body'], lookup[record['catalog_id']]['body']
    validate_inputs(idea, catalog)
    if idea != record['original_idea']:
        raise Invalid('Original idea bytes/meaning were replaced in the retained record')
    expected = assess_candidate(record['idea_id'], idea['content']['text'], record['candidate'],
                                record['semantic_report'], catalog['features'], set(lookup))
    if canonical(record['assessment']) != canonical(expected):
        raise Invalid('Formalization assessment does not match independent structural recalculation')


def validate_inputs(idea, catalog):
    if type(idea) is not dict or idea.get('schema') != MEMORY_SCHEMA or idea.get('kind') != 'idea':
        raise Invalid('Formalization requires an original typed idea record')
    if type(catalog) is not dict or set(catalog) != {'schema', 'features'} or catalog['schema'] != 'feature-catalog/1':
        raise Invalid('A versioned feature catalog source is required')


class FormalizationRecords:
    def _record_formalization(self, actor, lease, idea_id, catalog_id, candidate, semantic_report, provider_call_id=None):
        job = self._owned(actor, lease)
        if actor['role'] != 'formalizer' or job['spec']['kind'] != 'formalization/v1':
            raise Denied('Formalization requires its own formalizer capability')
        if 'research_call_profile' in job['spec']:
            _,_,output=self._auxiliary_response(actor,job,provider_call_id)
            inputs=job['spec']['research_inputs']
            if (idea_id!=inputs['idea_id'] or catalog_id!=inputs['catalog_id'] or set(output)!={'status','candidate','semantic_report'}
                    or canonical(output['candidate'])!=canonical(candidate)
                    or canonical(output['semantic_report'])!=canonical(semantic_report)):
                raise Invalid('Formalization must preserve the exact task and recorded provider output')
        elif provider_call_id is not None:
            raise Invalid('Provider provenance requires an epoch-bound auxiliary job')
        text(idea_id, 'idea_id')
        text(catalog_id, 'catalog_id')
        context = self._context(job['spec']['context_id'])
        allowed = self._attempt_sources(actor, job, context)
        if idea_id not in allowed or catalog_id not in allowed:
            raise Denied('Idea or catalog unavailable to this frozen capability')
        idea, catalog = self._artifact(idea_id)['body'], self._artifact(catalog_id)['body']
        validate_inputs(idea, catalog)
        assessment = assess_candidate(idea_id, idea['content']['text'], candidate,
                                      semantic_report, catalog['features'], allowed)
        body = {'schema': SCHEMA, 'idea_id': idea_id, 'catalog_id': catalog_id,
                'original_idea': idea, 'candidate': candidate, 'semantic_report': semantic_report,
                'authorization_snapshot': sorted(allowed),
                'created_at': datetime.fromtimestamp(self._now(), timezone.utc).isoformat().replace('+00:00', 'Z'),
                'assessment': assessment, 'scientific_readiness': False}
        try:
            saved = self._worker_artifact(actor, job, context, body, [idea_id, catalog_id])
        except Invalid as exc:
            if str(exc).startswith(('Payload exceeds', 'JSON nesting exceeds')):
                raise Invalid('RESOURCE_GAP: retained formalization envelope exceeds the local size/depth admission bound; no draft committed') from exc
            raise
        issue = assessment['gap']
        if issue:
            content = {'text': 'Retained formalization draft ' + saved['id'],
                       'reason': issue['code'] + ': ' + issue['reason'],
                       'reopen_condition': issue['reopen_condition']}
        else:
            content = {'text': 'Structurally checked formalization draft ' + saved['id'],
                       'uncertainty': 'Semantic fidelity, certification and scientific readiness remain unverified',
                       'measurement': saved['id']}
        journal = self._record_research(actor, lease, 'gap' if issue else 'observation', content,
                                        {}, [saved['id'], idea_id, catalog_id])
        self._event(actor['name'], 'formalization_recorded', artifact_id=saved['id'],
                    idea_id=idea_id, assessment=assessment, job_id=job['id'], generation=job['generation'])
        return {**saved, 'journal_id': journal['id'], 'assessment': assessment, 'scientific_readiness': False}
