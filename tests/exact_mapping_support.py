"""Inactive engineering representations; never an accepted original-A repair."""
from copy import deepcopy

from test_exact_compositions import FIXTURE
from test_exact_runtime import payload
from test_exact_formalization_review import parameter_paths


def programs():
    result=deepcopy(FIXTURE['programs'])
    condition=result['condition']['expression']
    canonical=condition['arg']
    validity=canonical['left']['left']
    predicate=canonical['left']['right']
    unknown=canonical['right']['right']
    # Same V-first evaluation order, all children remain eager. Strict Boolean
    # equality propagates unknown; V OR unknown is True only when V is True.
    condition['arg']={'op':'eq','left':{'op':'or','left':validity,'right':unknown},'right':predicate}
    changed=[0]
    def domain(node):
        if node['op']=='ln' and node['arg']['op']=='div':
            denominator=node['arg']['right']
            if denominator.get('op')=='literal' and denominator.get('unit')=='price:BTCUSDT':
                endpoint=node['arg']['left']
                node['arg']['right']={'op':'abs','arg':deepcopy(endpoint)}
                changed[0]+=1
                return
        for key in ('arg','left','right'):
            if key in node:domain(node[key])
    domain(result['outcome']['expression'])
    assert changed[0]==2
    return result


def supplied(count=55,max_steps=1000000):
    result=payload(count,max_steps=max_steps)
    candidate=result['candidate'];selected=programs()
    candidate['scope_ast']=selected['scope'];candidate['condition_ast']=selected['condition']
    candidate['outcome']['program']=selected['outcome']
    paths=['/horizons/outcome_bars']
    for path,program in (('/scope_ast',selected['scope']),('/condition_ast',selected['condition']),
                         ('/outcome/program',selected['outcome'])):
        paths.extend(parameter_paths(program['expression'],path+'/expression'))
    candidate['parameter_origins']=[{'path':path,'basis':'preexisting_specification',
        'source_refs':[candidate['idea_ref']],
        'rationale':'Inactive synthetic representation of unchanged original commitments or exact domain identity; not an accepted H_exec.'}
        for path in paths]
    return result
