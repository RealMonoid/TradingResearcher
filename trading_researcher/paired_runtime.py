"""Owned retained-source paired calculation/replay, no registry or provider access.

The host supplies qualified immutable inputs. Every child runs the exact retained
closure in an isolated Python process; replay is operational evidence only.
"""
from copy import deepcopy
import hashlib
import io
import os
from pathlib import Path
import sys
import unittest

from .binding import environment, hashes, require, write_file
from .certification import _environment_current
from .codec import canonical, decode, digest
from .paired_development import (PAIR, CONTRACT, PROFILE, REQUEST, PairedReferenceEngine,
                                 materialize_paired, paired_contrast, validate_request)
from .outcomes import _instant

ROOT=Path(__file__).resolve().parents[1]
TEST='tests/test_paired_development_adversarial.py'
SPEC='docs/architecture/23_PAIRED_DEVELOPMENT.md'
FILES=tuple(sorted([TEST,SPEC,'tests/paired_original_oracle.py','trading_researcher/PAIRED_DEVELOPMENT.md',*[
    'trading_researcher/'+name+'.py' for name in ('__init__','codec','errors','expressions',
       'outcomes','bounded_math','bounded_outcomes','certification','binding',
       'paired_development','paired_runtime','paired_composition')]]))
BOOTSTRAP='import sys;sys.path.insert(0,sys.argv[1]);from trading_researcher.paired_runtime import child_entry;child_entry(sys.argv[2])'
MAX_STREAM=512*1024*1024


def read_bundle():
    return {name:(ROOT/name).read_bytes() for name in FILES}


def compile_payload(payload):
    require(type(payload) is dict and set(payload)=={'formalization_id','candidate','catalog',
        'feature_definitions','data_manifest','as_of','max_steps'})
    candidate=payload['candidate']
    require(type(candidate) is dict and candidate.get('schema')=='hypothesis-exec/2')
    universe=candidate['test_universe']
    request={'schema':REQUEST,'candidate_ref':payload['formalization_id'],
        'data_snapshot_ref':universe['data_snapshot_ref'],'scope_program':candidate['scope_ast'],
        'condition_program':candidate['condition_ast'],'outcome_program':candidate['outcome']['program'],
        'outcome_scale':candidate['outcome']['scale'],'horizon_bars':candidate['horizons']['outcome_bars'],
        'universe':{key:universe[key] for key in ('start','end','pair')},
        'as_of':payload['as_of'],'max_steps':payload['max_steps']}
    start,end,_,expected=validate_request(request)
    require(candidate['horizons']['grid_seconds']==900 and type(candidate['horizons']['grid_seconds']) is int)
    manifest=payload['data_manifest']
    require(manifest['partition']=='development','Paired profile cannot compile protected outcome use')
    lower,upper=(_instant(manifest['universe'][key]) for key in ('start','end'))
    require(lower<=start<end<=upper and sorted(manifest['universe']['instruments'])==list(PAIR))
    engine=PairedReferenceEngine(payload['catalog'],[],payload['feature_definitions'],pair=list(PAIR))
    outcome=PairedReferenceEngine(payload['catalog'],[],payload['feature_definitions'],pair=list(PAIR),allow_log=True)
    programs={name:(outcome if name=='outcome_program' else engine).describe(request[name])
              for name in ('scope_program','condition_program','outcome_program')}
    require(programs['scope_program']['type']==programs['condition_program']['type']=='boolean')
    require(programs['outcome_program']['type']=='real' and programs['outcome_program']['unit']=='basis_points'
            and candidate['estimand']['unit']=='basis_points')
    refs=sorted({ref for value in programs.values() for ref in value['feature_refs']})
    require(refs==sorted(candidate['feature_refs']) and programs['outcome_program']['feature_refs'])
    return {'schema':'paired-compilation/1','request':request,'candidate_hash':digest(candidate),
        'programs':programs,'feature_refs':refs,'expected_case_count':expected,'maximum_input_rows':expected*2,
        'row_window':{'start':universe['start'],'end':universe['end'],'instruments':list(PAIR)},
        'outcome_unit':'basis_points','scientific_readiness':False}


def _stream(path):
    checksum,size=hashlib.sha256(),0
    with Path(path).open('rb') as stream:
        for raw in iter(lambda:stream.read(1024*1024),b''):
            size+=len(raw)
            require(size<=MAX_STREAM,'Paired stream exceeds its storage envelope')
            checksum.update(raw)
    return {'sha256':checksum.hexdigest(),'size':size}


def _read_rows(directory,expected):
    path=directory/'rows.jsonl'
    require(_stream(path)==expected,'Retained raw row bytes changed')
    rows=[]
    with path.open('rb') as stream:
        for line in stream:
            require(len(line)<=1048576 and len(rows)<100000)
            rows.append(decode(line))
    return rows


def _calculate(payload,directory,case_path):
    require(type(payload) is dict and set(payload)=={'compilation_input','compilation_hash','rows'})
    compiled=compile_payload(payload['compilation_input'])
    require(digest(compiled)==payload['compilation_hash'])
    inputs=payload['compilation_input']
    report=materialize_paired(compiled['request'],inputs['catalog'],_read_rows(directory,payload['rows']),inputs['feature_definitions'])
    contrast=paired_contrast(report)
    size=0
    with case_path.open('xb') as stream:
        for case in report.pop('cases'):
            raw=(canonical(case)+'\n').encode('utf-8')
            size+=len(raw)
            require(size<=MAX_STREAM,'Paired case stream exceeds its storage envelope')
            stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {'report':report,'contrast':contrast,'case_blob':_stream(case_path),
        'rows':deepcopy(payload['rows']),'compilation_hash':payload['compilation_hash'],'scientific_readiness':False}


def child_entry(request_path):
    path=Path(request_path)
    request=decode(path.read_bytes())
    require(type(request) is dict and set(request)=={'mode','payload','footprint'})
    require(set(request['footprint'])==set(FILES) and hashes(read_bundle())==request['footprint'])
    mode,payload=request['mode'],request['payload']
    if mode=='certify':
        require(payload=={'profile':PROFILE})
        suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=Path(TEST).name)
        output=io.StringIO()
        outcome=unittest.TextTestRunner(stream=output).run(suite)
        require(outcome.testsRun>0 and outcome.wasSuccessful() and not outcome.skipped
                and not outcome.expectedFailures and not outcome.unexpectedSuccesses,output.getvalue())
        result={'schema':'paired-conformance-result/1','profile':PROFILE,'tests':outcome.testsRun,
            'failures':0,'errors':0,'skipped':0,'scientific_readiness':False}
    elif mode=='compile':
        result=compile_payload(payload)
    elif mode=='composition':
        from .paired_composition import qualify
        result=qualify(payload)
    elif mode=='audit':
        from .paired_composition import audit
        require(set(payload)=={'execution_input','result'})
        require(_stream(path.parent/'cases.jsonl')==payload['result']['case_blob'])
        with (path.parent/'cases.jsonl').open('rb') as stream:
            cases=[decode(line) for line in stream]
        result=audit(payload['execution_input']['compilation_input'],
            _read_rows(path.parent,payload['execution_input']['rows']),cases)
    elif mode=='execute':
        result=_calculate(payload,path.parent,path.parent/'cases.jsonl')
    elif mode=='verify':
        require(type(payload) is dict and set(payload)=={'execution_input','result'})
        original=payload['result']
        require(_stream(path.parent/'cases.jsonl')==original['case_blob'])
        actual=_calculate(payload['execution_input'],path.parent,path.parent/'replayed-cases.jsonl')
        require(canonical(actual)==canonical(original),'Paired replay differs from the complete original result')
        result={'schema':'paired-case-verification/1','result_hash':digest(original),
            'case_blob':actual['case_blob'],'checked_cases':actual['report']['processed_case_count'],
            'scientific_readiness':False}
    else:
        raise ValueError('Unknown paired child mode')
    require(hashes(read_bundle())==request['footprint'])
    print(canonical({'mode':mode,'request_hash':digest(payload),'footprint':request['footprint'],
                     'result':result,'environment':environment(request['footprint'])}))


def run_child(bundle,mode,payload,directory,*,timeout=1800):
    from .binance_normalize import _run_child
    require(type(timeout) is int and 1<=timeout<=1800 and set(bundle)==set(FILES))
    directory=Path(directory)
    for name,raw in bundle.items():
        destination=directory/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        write_file(destination,raw)
    expected=hashes(bundle)
    write_file(directory/'request.json',canonical({'mode':mode,'payload':payload,'footprint':expected}).encode())
    report=_run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],directory,timeout=timeout)
    require(type(report) is dict and set(report)=={'mode','request_hash','footprint','result','environment'}
        and report['mode']==mode and report['request_hash']==digest(payload)
        and report['footprint']==expected and _environment_current(report['environment']))
    require(hashes({name:(directory/name).read_bytes() for name in bundle})==expected)
    return report
