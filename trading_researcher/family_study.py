"""Fixed joint-family inventories and compact exact calibration count reports."""
from collections import Counter
from copy import deepcopy

from .codec import canonical, digest, integer, strings, text
from .evaluation_policy import require
from .family_models import family_events
from .information_study import make_manifest as single_manifest, outer_interval, STATES
from .outcomes import _read_rational


MANIFEST = 'family-information-study-manifest/1'
FINAL_MANIFEST = 'family-evaluator-calibration-manifest/1'
SCHEMAS = (MANIFEST, FINAL_MANIFEST)
UNAVAILABLE_REASON = 'Joint world did not produce an authenticated observed event.'


def make_manifest(assigned, profile, *, purpose='development'):
    require(purpose in ('development', 'final_calibration'), 'Unknown family study purpose')
    require(type(profile) is dict and {'responses', 'patterns'} <= set(profile), 'Explicit family responses and patterns required')
    base = single_manifest(assigned, {k:v for k,v in profile.items() if k not in ('responses', 'patterns')})
    responses = strings(profile['responses'], 'synthetic response identities')
    require(2 <= len(responses) <= 8 and len(responses) == assigned['primary_count']
        and responses == sorted(responses) and all(len(value) <= 80 for value in responses),
        'Sorted distinct responses must match the assigned family count')
    patterns = profile['patterns']
    require(type(patterns) is list and 1 <= len(patterns) <= 8, 'One through eight complete family patterns required')
    for pattern in patterns:
        require(type(pattern) is list and len(pattern) == len(responses), 'Every pattern must include every response')
        for scenario in pattern:
            integer(scenario, 'effect scenario', 0)
            require(scenario < len(base['effects']), 'Undeclared family effect scenario')
    require(patterns == sorted(patterns) and len({tuple(p) for p in patterns}) == len(patterns),
        'Distinct patterns in lexicographic order required')
    require(all([scenario]*len(responses) in patterns for scenario in range(len(base['effects'])))
        and any(len(set(pattern)) > 1 for pattern in patterns),
        'All homogeneous effects and at least one mixed-truth pattern are required')
    require(max(profile['targets'])*assigned['instruments']*len(responses) <= 100000,
        'Family target exceeds aggregate generated case envelope')
    if purpose == 'final_calibration':
        require(profile['worlds_per_cell'] == 256 and len(profile['targets']) == 1,
            'Final family calibration requires 256 worlds at one fixed target')
    require(len(profile['specifications'])*len(profile['targets'])*len(patterns)*profile['worlds_per_cell'] <= 2048,
        'Complete family world inventory exceeds its envelope')
    recipe = {k:v for k,v in base.items() if k not in ('worlds', 'recipe_hash')}
    recipe.update(schema=FINAL_MANIFEST if purpose == 'final_calibration' else MANIFEST,
        profile=deepcopy(profile), selection='fixed_final_target_no_selection' if purpose == 'final_calibration'
            else 'smallest_complete_tested_point_all_declared_alternative_components_at_least_four_fifths',
        seed_namespace='reserved-final-family-calibration/1' if purpose == 'final_calibration' else 'development-family-study/1')
    recipe_hash = digest(recipe); worlds = []; seeds = set()
    for target in profile['targets']:
        for spec_index in range(len(profile['specifications'])):
            for pattern_index in range(len(patterns)):
                for replicate in range(profile['worlds_per_cell']):
                    identity = {'recipe_hash':recipe_hash, 'time_rows':target, 'spec_index':spec_index,
                                'pattern_index':pattern_index, 'replicate':replicate}
                    streams = {key:int(digest({'namespace':recipe['seed_namespace'], 'world':identity, 'stream':key}),16)
                               for key in ('population_seed', 'bootstrap_seed')}
                    require(not seeds.intersection(streams.values()) and len(set(streams.values())) == 2, 'Family seed collision')
                    seeds.update(streams.values())
                    worlds.append({'id':digest(identity), **{k:v for k,v in identity.items() if k != 'recipe_hash'}, **streams})
    result = {**recipe, 'recipe_hash':recipe_hash, 'worlds':worlds}
    canonical(result)
    return result


def make_final_manifest(assigned, profile):
    return make_manifest(assigned, profile, purpose='final_calibration')


def validate_manifest(manifest):
    require(type(manifest) is dict and manifest.get('schema') in SCHEMAS, 'Owned family manifest required')
    expected = make_manifest(manifest.get('assigned'), manifest.get('profile'),
        purpose='final_calibration' if manifest['schema'] == FINAL_MANIFEST else 'development')
    require(digest(expected) == digest(manifest), 'Family inventory differs from its fixed recipe')


def components(manifest, world):
    pattern = manifest['profile']['patterns'][world['pattern_index']]
    return [{'id':identity, 'scenario':scenario} for identity,scenario in zip(manifest['profile']['responses'],pattern)]


def outcome_record(manifest, world, outcomes=None, *, failed=False):
    if outcomes is None or failed:
        outcomes = [{'id':item['id'], 'truth':manifest['effects'][item['scenario']], 'state':'TECHNICAL_FAILURE',
                     'decision':None, 'covered':None} for item in components(manifest,world)]
    states = {item['state'] for item in outcomes}
    state = ('TECHNICAL_FAILURE' if 'TECHNICAL_FAILURE' in states else 'MODEL_GAP' if 'MODEL_GAP' in states
             else 'INFORMATION_GAP' if 'INFORMATION_GAP' in states else 'VERIFIED')
    return {'world_id':world['id'], 'state':state, 'decision':None, 'scope_count':None, 'condition_count':None,
        'covered':None, 'components':deepcopy(outcomes), 'events':family_events(outcomes,
            manifest['assigned']['delta'], manifest['assigned']['direction'])}


def _records(manifest, records):
    validate_manifest(manifest)
    require(type(records) is list and len(records) <= len(manifest['worlds']), 'Bounded family records required')
    worlds = {world['id']:world for world in manifest['worlds']}; known = {}
    for record in records:
        require(type(record) is dict and record.get('world_id') in worlds
            and record['world_id'] not in known, 'Duplicate or unplanned family outcome')
        world = worlds[record['world_id']]
        values = record.get('components')
        require(type(values) is list and len(values) == len(manifest['profile']['responses']), 'Every response outcome is required')
        for item, expected in zip(values, components(manifest,world)):
            require(type(item) is dict and set(item) == {'id','truth','state','decision','covered'}
                and item['id'] == expected['id'] and item['truth'] == manifest['effects'][expected['scenario']],
                'Response identity or truth differs from the fixed world')
        expected = outcome_record(manifest,world,values)
        require(record == expected, 'Family aggregate differs from its full component outcomes')
        known[record['world_id']] = record
    return worlds, known


def summarize(manifest, records):
    worlds, known = _records(manifest,records)
    cells = []; delta = _read_rational(manifest['assigned']['delta'])
    for target in manifest['profile']['targets']:
        for spec in range(len(manifest['profile']['specifications'])):
            for pattern_index, pattern in enumerate(manifest['profile']['patterns']):
                planned = [w for w in worlds.values() if (w['time_rows'],w['spec_index'],w['pattern_index']) == (target,spec,pattern_index)]
                values = [known[w['id']] for w in planned if w['id'] in known]
                states = Counter(item['state'] for item in values)
                complete = len(values) == len(planned) and not (states['MODEL_GAP'] or states['TECHNICAL_FAILURE'])
                detections = []
                for index, scenario in enumerate(pattern):
                    if abs(_read_rational(manifest['effects'][scenario])) != 2*delta: continue
                    count = sum(item['components'][index]['decision'] == 'SUPPORTED_INITIAL' for item in values
                                if item['state'] not in ('MODEL_GAP','TECHNICAL_FAILURE'))
                    detections.append({'response_index':index, 'detections':count,
                        'interval':outer_interval(count,len(planned),manifest['profile']['outer_noncoverage']) if complete else None,
                        'design_target_met':5*count >= 4*len(planned) if complete else None})
                cells.append({'time_rows':target, 'spec_index':spec, 'pattern_index':pattern_index,
                    'planned':len(planned), 'recorded':len(values), 'states':{k:states[k] for k in sorted(STATES)},
                    'complete':complete, 'detections':detections})
    complete = all(cell['complete'] for cell in cells); candidate = None
    if complete and manifest['schema'] == MANIFEST:
        for target in manifest['profile']['targets']:
            alternatives = [d for c in cells if c['time_rows'] == target for d in c['detections']]
            if alternatives and all(item['design_target_met'] for item in alternatives):
                candidate = target; break
    return {'schema':'family-study-summary/1', 'complete':complete, 'planned_worlds':len(worlds),
        'recorded_worlds':len(records), 'cells':cells, 'candidate_time_rows':candidate,
        'candidate_qualification':'smallest_complete_tested_point_not_n_min', 'n_min':None,
        'scientific_readiness':False, 'classification_permitted':False}


def count_plan(manifest, applicability):
    from .calibration import APPLICABILITY
    validate_manifest(manifest)
    require(manifest['schema'] == FINAL_MANIFEST, 'Reserved final family manifest required')
    delta = _read_rational(manifest['assigned']['delta']); cohorts = []
    for spec in range(len(manifest['profile']['specifications'])):
        for index, pattern in enumerate(manifest['profile']['patterns']):
            effects = [abs(_read_rational(manifest['effects'][scenario])) for scenario in pattern]
            kinds = [('joint_miscoverage', None)]
            if 0 in effects: kinds.append(('false_support',None))
            if delta in effects: kinds.append(('boundary_decisive',None))
            kinds.extend(('detection',i) for i,effect in enumerate(effects) if effect == 2*delta)
            for kind, response in kinds:
                identity = f'spec-{spec}/pattern-{index}/{kind}'
                if response is not None: identity += f'/response-{response}'
                cohorts.append({'id':identity, 'criterion':kind, 'spec_index':spec,
                    'pattern_index':index, 'response_index':response})
    require(len(cohorts) <= 128, 'Complete family cohort inventory exceeds its envelope')
    ids = {item['id'] for item in cohorts}
    require(type(applicability) is dict and set(applicability) == APPLICABILITY, 'Explicit stress applicability required')
    for issue, declaration in applicability.items():
        require(type(declaration) is dict and set(declaration) == {'status','cohort_ids','reason'}, 'Exact applicability declaration required')
        text(declaration['reason'], issue+' applicability reason')
        refs = strings(declaration['cohort_ids'],'applicability cohort IDs')
        require(set(refs) <= ids and declaration['status'] in ('included','not_applicable')
            and bool(refs) == (declaration['status'] == 'included'), 'Applicability references or status differ')
    return {'schema':'joint-family-calibration-count-plan/1', 'estimator_ref':'manifest:'+digest(manifest),
        'population_ref':'specifications:'+digest(manifest['profile']['specifications']),
        'cohorts':cohorts, 'applicability':deepcopy(applicability)}


def count_assessment(manifest, records, sources, applicability):
    from .calibration import evaluate_cohort
    worlds, known = _records(manifest,records); plan = count_plan(manifest,applicability)
    require(set(sources) == set(known), 'Every family record needs its retained attempt source')
    for source in sources.values(): text(source,'attempt source')
    groups = {}; reports = []
    for cohort in plan['cohorts']:
        group = f"spec-{cohort['spec_index']}/pattern-{cohort['pattern_index']}"
        ids = [w['id'] for w in worlds.values() if (w['spec_index'],w['pattern_index']) == (cohort['spec_index'],cohort['pattern_index'])]
        groups[group] = ids
        observations = []
        for identity in ids:
            if identity not in known: continue
            record = known[identity]; event = None
            if cohort['criterion'] == 'detection':
                response = manifest['profile']['responses'][cohort['response_index']]
                event = record['events']['detections'][response]
            else: event = record['events'][cohort['criterion']]
            observations.append({'cohort_id':cohort['id'], 'world_id':identity,
                'state':'unavailable' if event is None else 'observed', 'event':event,
                'source_ref':sources[identity], 'reason':UNAVAILABLE_REASON if event is None else None})
        report = evaluate_cohort(cohort['criterion'],ids,observations)
        indices = {identity:index for index,identity in enumerate(ids)}
        report['missing_indices'] = [indices[x] for x in report.pop('missing_world_ids')]
        report['unavailable_indices'] = [indices[x] for x in report.pop('unavailable_world_ids')]
        report.pop('source_refs')
        reports.append({'cohort_id':cohort['id'], 'world_group':group, **report})
    complete = all(report['complete'] for report in reports)
    result = {'schema':'joint-family-calibration-count-assessment/1',
        'status':'NOT_ASSESSED' if not complete else 'PASS_COUNTS_ONLY' if all(r['threshold_met'] for r in reports) else 'FAIL_COUNTS_ONLY',
        'complete':complete, 'plan_hash':digest(plan),
        'input_hash':digest({'plan':digest(plan),'record_hashes':[digest(r) for r in records], 'sources':sources}),
        'cohorts':reports, 'world_groups':groups, 'world_sources':deepcopy(sources), 'applicability':deepcopy(applicability),
        'calibration_scope':'distinct_binary_responses_on_one_shared_development_template',
        'multi_claim_mixed_truth_calibration':'COUNTS_ONLY_NOT_SCIENTIFIC_ADMISSION',
        'input_authentication':'UNVERIFIED', 'freshness':'UNVERIFIED', 'event_semantics':'UNVERIFIED',
        'applicability_evidence':'UNVERIFIED', 'scientific_readiness':False, 'n_min':None}
    canonical(result)
    return result


def validate_count_envelope(manifest, applicability):
    records = [outcome_record(manifest,w,failed=True) for w in manifest['worlds']]
    # All unavailable worlds maximize failure membership; unique sources bound
    # the complete response envelope without duplicating full events per cohort.
    count_assessment(manifest,records,{w['id']:digest(['source',w['id']]) for w in manifest['worlds']},applicability)
