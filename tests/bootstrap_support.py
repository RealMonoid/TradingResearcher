"""Synthetic aligned reference reports; no historical/model evidence."""
from datetime import datetime, timezone

from trading_researcher.codec import digest
from trading_researcher.outcomes import materialize_reference


def report(times=12, rare=False, as_of=None):
    catalog={'condition@1':{'type':'boolean','unit':None},'event@1':{'type':'boolean','unit':None}}
    def program(expression):return {'schema':'research-ast/1','catalog_hash':digest(catalog),'expression':expression}
    def instant(value):return datetime.fromtimestamp(value,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    request={'schema':'reference-case-request/1','candidate_ref':'bootstrap-fixture','data_snapshot_ref':'bootstrap-fixture-data',
        'scope_program':program({'op':'literal','type':'boolean','unit':None,'value':True}),
        'condition_program':program({'op':'feature','ref':'condition@1'}),
        'outcome_program':program({'op':'feature','ref':'event@1'}),'outcome_scale':'binary_probability','horizon_bars':1,
        'universe':{'start':instant(0),'end':instant(times*900),'instruments':['A','B']},
        'as_of':instant(times*900 if as_of is None else as_of),'max_steps':10000000}
    rows=[{'time':i*900,'instrument':symbol,'features':{
        'condition@1':{'value':not rare or i==0,'available_at':i*900},
        'event@1':{'value':True,'available_at':i*900}}} for i in range(times) for symbol in ('A','B')]
    return materialize_reference(request,catalog,rows)
