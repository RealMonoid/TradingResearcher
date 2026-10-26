"""Retained synthetic world plus actual estimator; never a market execution."""
import hashlib
from pathlib import Path

from .binding import environment, require
from .codec import canonical, decode, digest
from .evaluation_plans import source_bundle, footprint
from .population_models import build_model, generate_world
from .stationary_bootstrap import calculate, randomness
from .outcomes import _read_rational


BOOTSTRAP=('import sys;sys.path.insert(0,sys.argv[1]);'
    'from trading_researcher.study_pipeline import child_entry;child_entry(sys.argv[2])')


def calculate_world(payload, manifest, world, cases, retain, *, retain_draw_bytes=None):
    """Complete deterministic pipeline with an exact ordered case/draw sink."""
    report={**payload['report'],'cases':cases}
    model=build_model(report,payload['diagnostics'],
        manifest['profile']['specifications'][world['spec_index']],manifest['effects'])
    outcome={'world_id':world['id'],'state':'MODEL_GAP','decision':None,
        'scope_count':None,'condition_count':None,'covered':None}
    result={'schema':'development-study-world-computation/1','world_id':world['id'],
        'model':model,'world':None,'bootstrap':None,'outcome':outcome,
        'n_min':None,'scientific_readiness':False,'classification_permitted':False}
    if model['status']!='MODEL_SPECIFIED':return result
    generated=generate_world(report,model,world['scenario'],world['time_rows'],world['population_seed'])
    for case in generated['report']['cases']:retain({'kind':'case','value':case})
    design={'base_length':manifest['assigned']['base_length'],
        'primary_count':manifest['assigned']['primary_count'],'randomness':randomness(world['bootstrap_seed']),
        'mc_policy':manifest['mc_policy']}
    limits={'max_seconds':max(1,manifest['profile']['budget']['attempt_compute_ms']//1000),
        'max_segments':100000000}
    bootstrap=calculate(generated['report'],design,limits,
        on_draw=(lambda draw:retain({'kind':'draw','value':draw})) if retain_draw_bytes is None else None,
        on_draw_bytes=retain_draw_bytes)
    generated['report'].pop('cases')
    result.update(world=generated,bootstrap=bootstrap)
    descriptive=bootstrap['descriptive']
    outcome.update(scope_count=descriptive['scope_count'],condition_count=descriptive['condition_count'])
    if bootstrap['status']=='COMPUTED_UNCALIBRATED':
        diagnostic=bootstrap['monte_carlo'];interval=bootstrap['interval']
        truth=_read_rational(generated['truth']['effect'])
        outcome.update(state='VERIFIED',decision=(diagnostic['nominal_classification']
            if diagnostic['boundary_stable'] else 'TESTED_INCONCLUSIVE'),
            covered=_read_rational(interval['lower'])<=truth<=_read_rational(interval['upper']))
    elif (bootstrap['status']=='INFORMATION_GAP' or bootstrap['status']=='INPUT_GAP'
            and bootstrap['reason'] in ('no_scope_cases','no_conditioned_cases')):
        outcome['state']='INFORMATION_GAP'
    else:outcome['state']='TECHNICAL_FAILURE'
    return result


def child_entry(request_path):
    directory=Path(request_path).parent;request=decode(Path(request_path).read_bytes())
    expected=request['footprint'];payload=request['payload'];verify=request['verify']
    require(footprint(source_bundle())==expected,'Retained study source differs')
    observed_environment=environment(expected)
    raw=(directory/'cases.jsonl').read_bytes()
    require({'sha256':hashlib.sha256(raw).hexdigest(),'size':len(raw)}==payload['case_blob'],
        'Retained study input cases differ')
    cases=[decode(line) for line in raw.splitlines()]
    require(len(cases)<=100000,'Study case count exceeds its envelope')
    checksum=hashlib.sha256();total=0
    path=directory/('expected-stream.jsonl' if verify is not None else 'stream.jsonl')
    with path.open('rb' if verify is not None else 'xb') as stream:
        def retain_line(line):
            nonlocal total
            total+=len(line)
            require(total<=request['stream_limit'],'Study output exceeds its reserved storage')
            checksum.update(line)
            if verify is None:stream.write(line)
            else:require(stream.read(len(line))==line,'Study case/draw replay differs')
        def retain(record):retain_line((canonical(record)+'\n').encode())
        # The calculator already validated and serialized this immutable draw.
        # Static sorted framing exactly matches canonical({kind, value}).
        def retain_draw(encoded):retain_line(b'{"kind":"draw","value":'+encoded+b'}\n')
        result=calculate_world(payload,request['manifest'],request['world'],cases,retain,
            retain_draw_bytes=retain_draw)
        if verify is not None:
            require(stream.read(1)==b'' and digest(result)==verify,'Study replay differs')
    require(footprint(source_bundle())==expected,'Study source changed during computation')
    print(canonical({'result':result if verify is None else {'verified_result_hash':verify},
        'stream_blob':{'sha256':checksum.hexdigest(),'size':total},'request_hash':digest(request),
        'footprint':expected,'environment':observed_environment}),flush=True)
