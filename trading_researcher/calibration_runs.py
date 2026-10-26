"""Owned, protected final draws for the implemented single-claim estimator scope."""
from copy import deepcopy

from . import calibration_study
from .codec import canonical, decode, digest, integer, text
from .errors import Conflict
from .evaluation_policy import require
from .information_study import summarize
from .study_runs import InformationStudies, LOADED_SOURCE, source_bundle, footprint


INPUT='evaluator-calibration-input/1'
RESULT='evaluator-calibration-attempt/1'


class CalibrationStudies(InformationStudies):
    _study_input_schema=INPUT
    _study_result_schema=RESULT
    _study_data_class='operations'
    _study_authority='conditional_single_claim_calibration_not_scientific_admission'
    _study_request_fields={'key','development_study_id','time_rows','seed','budget','cost_estimate','applicability'}
    _calibration_policy=calibration_study
    _calibration_identity_schema='single-claim-final-identity/1'
    _calibration_scope='one_primary_binary_claim_estimator_only'
    _mixed_truth_status='UNAVAILABLE'
    _calibration_summary_schema='single-claim-final-calibration-summary/1'
    _event_semantics='FIXED_SINGLE_CLAIM_OUTCOME_MAPPING'
    _calibration_qualification=('Owned retained attempts and fixed event mapping. PRNG independence, population adequacy, '
        'stress applicability, mixed-truth multi-claim coverage and scientific admission remain unverified.')

    def __init__(self,broker):self.broker=broker
    def __getattr__(self,name):return getattr(self.broker,name)

    def _development_runner(self):return self.broker

    def _validate_development_family(self,manifest):
        require(manifest['assigned']['primary_count']==1,
            'Coherent mixed-truth multi-claim calibration is unavailable on the single-claim route')

    def _calibration_identity_extra(self,manifest):return {}

    def _development(self,request):
        text(request['development_study_id'],'development study')
        runner=self._development_runner()
        study=runner._study(request['development_study_id'])
        self.broker._require_usable_dependencies(study['id'])
        view=runner._study_view(study)
        require(view['status']=='COMPLETE','Final calibration requires a complete owned development study')
        integer(request['time_rows'],'fixed target',1)
        require(request['time_rows'] in study['body']['manifest']['profile']['targets'],
            'Final target must have been studied in development')
        self._validate_development_family(study['body']['manifest'])
        return study,view

    def _study_identity(self,request):
        study,_=self._development(request);body=study['body'];manifest=body['manifest']
        payload=deepcopy(body['payload'])
        # Only provenance aliases are removed. Exact case bytes, expressions,
        # universe, time window, diagnostics and scientific settings remain.
        for key in ('candidate_ref','data_snapshot_ref'):payload['report']['request'].pop(key,None)
        payload['diagnostics'].pop('case_report_hash',None)
        specs=[{k:v for k,v in spec.items() if k!='rationale'} for spec in manifest['profile']['specifications']]
        require(len({digest(spec) for spec in specs})==len(specs),'Duplicate numerical stress specifications')
        return digest({'schema':self._calibration_identity_schema,'payload':payload,
            'calculation_source':body['source_footprint'],
            'assigned':{k:v for k,v in manifest['assigned'].items() if k!='input_binding'},
            'specifications':sorted(specs,key=canonical),'time_rows':request['time_rows'],
            'mc_policy':manifest['mc_policy'],**self._calibration_identity_extra(manifest)})

    def _study_existing_request(self,existing,request):
        fixed=lambda value:{k:v for k,v in value.items() if k not in ('key','development_study_id')}
        if digest(fixed(existing['body']['request']))!=digest(fixed(request)):
            raise Conflict('Final series already binds its seed, budget, cost and applicability; no reset')

    def _study_inputs(self,actor,request):
        development,_=self._development(request);body=development['body']
        cost,ancestry=self._study_cost_source(request['cost_estimate'])
        profile=deepcopy(body['manifest']['profile'])
        profile.update(targets=[request['time_rows']],worlds_per_cell=256,seed=request['seed'],
            budget=request['budget'],cost_estimate=request['cost_estimate'])
        manifest=self._calibration_policy.make_final_manifest(body['manifest']['assigned'],profile)
        self._calibration_policy.validate_count_envelope(manifest,request['applicability'])
        refs=sorted(set(development['source_refs'])|{development['id'],cost['id']}|ancestry)
        exposure=sorted(set(development['exposure'])|set(refs))
        return body['payload'],manifest,refs,exposure

    def _study_capture_source(self,request):
        require(footprint(source_bundle())==LOADED_SOURCE,'Calibration host source changed since import; restart')
        development,_=self._development(request)
        return self.broker._load_study_source(development)

    def _study_extra_input(self,request,manifest):
        development,view=self._development(request)
        seeds={w[key] for w in manifest['worlds'] for key in ('population_seed','bootstrap_seed')}
        ids={w['id'] for w in manifest['worlds']}
        compared=[]
        for prior,old in self._recorded_calibration_worlds():
            require(not seeds.intersection(w[key] for w in old for key in ('population_seed','bootstrap_seed'))
                and not ids.intersection(w['id'] for w in old),'Recorded development/final seed or world collision')
            compared.append(prior['id'])
        return {'assessment_source_footprint':LOADED_SOURCE,
            'count_plan_hash':digest(self._calibration_policy.count_plan(manifest,request['applicability'])),
            'target_basis':'development_candidate' if view['summary']['candidate_time_rows']==request['time_rows']
                else 'studied_sensitivity_cutoff_not_n_min',
            'seed_disjoint_from_recorded_study_ids':sorted(compared),
            'freshness_qualification':'Distinct recorded PRNG seeds and world IDs; independent sampling law not certified.',
            'calibration_scope':self._calibration_scope,
            'multi_claim_mixed_truth_calibration':self._mixed_truth_status}

    def _recorded_calibration_worlds(self):
        # Retained inputs include failed and not-yet-executed reservations.
        study_schemas={'information-study-input/1','evaluator-calibration-input/1',
            'family-study-input/1','family-calibration-input/1'}
        for row in self._db.execute('SELECT id,envelope FROM artifacts'):
            artifact=self._artifact(row['id']);body=artifact.get('body')
            if artifact['creator']!=artifact['origin'] or artifact['creator']!='controller' or type(body) is not dict:continue
            if body.get('schema') in study_schemas:yield artifact,body['manifest']['worlds']
            elif body.get('schema') in ('population-world-input/1','population-family-input/1'):
                payload=body['payload']
                yield artifact,[{'id':artifact['id'],'population_seed':payload['seed'],
                    'bootstrap_seed':payload.get('bootstrap_seed',payload['seed'])}]

    def _study_input_ref(self,study):return study['body']['request']['development_study_id']

    def _assessment_current(self,study):
        return study['body']['assessment_source_footprint']==LOADED_SOURCE==footprint(source_bundle())

    def _study_before_execute(self,study):
        require(self._assessment_current(study),'Retained calibration assessment source differs; no new execution')

    def _study_summary(self,study,records,results):
        body=study['body'];manifest=body['manifest'];summary=summarize(manifest,records)
        summary.update(schema=self._calibration_summary_schema,
            candidate_qualification='fixed_studied_target_not_n_min',target_basis=body['target_basis'])
        # Inspection and orphan recovery must still work after a host update.
        # Refuse a new count interpretation instead of silently changing it.
        if not self._assessment_current(study):
            summary['count_assessment']={'status':'NOT_ASSESSED','reason':'assessment_source_changed',
                'scientific_readiness':False,'n_min':None}
            return summary
        sources={};outcomes={}
        for row in self._db.execute('SELECT envelope FROM events ORDER BY seq'):
            event=decode(row[0]);details=event['details']
            if (event['actor']!='controller' or event['action']!='information_study_settled'
                    or details.get('study_id')!=study['id']):continue
            outcome=details['outcome'];identity=details['artifact_id']
            if identity is None:
                require(details['orphan_uncertain'] and outcome['state']=='TECHNICAL_FAILURE',
                    'Only unavailable orphan outcomes may lack an owned attempt')
                sources[outcome['world_id']]=study['id']
            else:
                artifact=self._artifact(identity);attempt=artifact['body']
                require(artifact['origin']==artifact['creator']=='controller' and artifact['data_class']=='operations'
                    and attempt['schema']==self._study_result_schema and attempt['study_id']==study['id']
                    and attempt['outcome']==outcome and attempt['settlement']==details['settlement'],
                    'Final event differs from its owned attempt')
                sources[outcome['world_id']]=identity
            outcomes[outcome['world_id']]=outcome
        require(outcomes=={r['world_id']:r for r in records},'Final event inventory differs')
        assessment=self._calibration_policy.count_assessment(manifest,records,sources,body['request']['applicability'])
        require(assessment['plan_hash']==body['count_plan_hash'],'Frozen count plan differs')
        assessment.update(input_authentication='OWNED_REPLAYED_ATTEMPTS',
            freshness='RECORDED_SEED_DISJOINTNESS_ONLY',event_semantics=self._event_semantics,
            qualification=self._calibration_qualification)
        summary['count_assessment']=assessment
        return summary
