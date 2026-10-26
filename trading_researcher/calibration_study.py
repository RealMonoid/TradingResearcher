"""Final-world manifests and deterministic events for the supported m=1 scope."""
from .calibration import assess_calibration
from .codec import canonical, digest
from .evaluation_policy import require
from .information_study import FINAL_MANIFEST, make_manifest, summarize
from .outcomes import _read_rational


UNAVAILABLE_REASON='World did not produce an authenticated observed event.'


def make_final_manifest(assigned,profile):
    return make_manifest(assigned,profile,purpose='final_calibration')


def count_plan(manifest,applicability):
    require(manifest['schema']==FINAL_MANIFEST,'Reserved final manifest required')
    require(manifest['assigned']['primary_count']==1,'Coherent multi-claim calibration is unavailable')
    cohorts=[]
    for index in range(len(manifest['profile']['specifications'])):
        for scenario,effect in enumerate(manifest['effects']):
            magnitude=abs(_read_rational(effect));delta=_read_rational(manifest['assigned']['delta'])
            criterion='false_support' if magnitude==0 else 'boundary_decisive' if magnitude==delta else 'detection'
            require(magnitude in (0,delta,2*delta),'Unassigned calibration effect')
            worlds=[w['id'] for w in manifest['worlds'] if w['spec_index']==index and w['scenario']==scenario]
            for kind in (criterion,'joint_miscoverage'):
                cohorts.append({'id':f'spec-{index}/scenario-{scenario}/{kind}','criterion':kind,
                    'world_ids':worlds,'rationale':'Frozen effect/stress cell; one jointly simulated world per observation.'})
    plan={'schema':'narrow-calibration-assessment-plan/1',
        'estimator_ref':'manifest:'+digest(manifest),'population_ref':'specifications:'+digest(manifest['profile']['specifications']),
        'cohorts':cohorts,'applicability':applicability}
    # The same strict gate validates cohort count, all criteria and applicability
    # before any final world is executed. No subset may be silently discarded.
    assess_calibration(plan,[])
    return plan


def count_assessment(manifest,records,sources,applicability):
    summarize(manifest,records)  # Existing exact outcome/inventory validation.
    plan=count_plan(manifest,applicability)
    known={record['world_id']:record for record in records}
    require(set(sources)==set(known),'Every recorded world needs its retained attempt source')
    observations=[]
    for cohort in plan['cohorts']:
        kind=cohort['criterion']
        for world in cohort['world_ids']:
            if world not in known:continue
            record=known[world];event=None;reason=UNAVAILABLE_REASON
            if record['state']=='VERIFIED':
                event=(not record['covered'] if kind=='joint_miscoverage' else
                    record['decision'] in ('SUPPORTED_INITIAL','TESTED_NEGATIVE') if kind=='boundary_decisive'
                    else record['decision']=='SUPPORTED_INITIAL')
            elif record['state']=='INFORMATION_GAP' and kind!='joint_miscoverage':
                event=False
            if event is not None:reason=None
            observations.append({'cohort_id':cohort['id'],'world_id':world,
                'state':'unavailable' if event is None else 'observed','event':event,
                'source_ref':sources[world],'reason':reason})
    report=assess_calibration(plan,observations)
    report['calibration_scope']='one_primary_binary_claim_estimator_only'
    report['multi_claim_mixed_truth_calibration']='UNAVAILABLE'
    return report


def validate_count_envelope(manifest,applicability):
    """Reserve room for every unavailable event before any final draw occurs."""
    plan=count_plan(manifest,applicability)
    observations=[{'cohort_id':cohort['id'],'world_id':world,'state':'unavailable',
        'event':None,'source_ref':'0'*64,'reason':UNAVAILABLE_REASON}
        for cohort in plan['cohorts'] for world in cohort['world_ids']]
    # Owned sources are 64-byte SHA identities. This representation is larger
    # than an observed Boolean event, including when every attempt fails.
    canonical({'manifest':plan,'observations':observations})
