"""Retained AST4 compile/case-stream/replay child; no registry/provider access."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import os
from pathlib import Path
import sys
import unittest

from .binding import environment, hashes, require, write_file
from .bounded_outcomes import legacy_request
from .certification import _environment_current
from .codec import canonical, decode, digest, strings
from .exact_compositions import CONTRACT, ExactCompositionEngine
from .exact_outcomes import (REQUEST, add_exact_diagnostics, exact_base_projection,
                             exact_contrast, lookback, materialize_exact)
from .outcomes import _instant, _validate

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'exact-reference-computation/1'
MAX_STREAM = 512 * 1024 * 1024
TESTS = ('tests/test_exact_compositions.py','tests/test_exact_compositions_review.py',
         'tests/test_exact_outcomes.py','tests/test_exact_outcomes_review.py')
DOCS = ('docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md',
        'docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md','docs/architecture/20_BOUNDED_MATH_REUSE.md',
        'docs/architecture/26_BOUNDED_EXACT_COMPOSITIONS.md','trading_researcher/EXACT_COMPOSITIONS.md',
        'trading_researcher/REQUIRED_INPUTS.md','trading_researcher/EXACT_RUNTIME.md')
FILES = tuple(sorted((*TESTS,*DOCS,'tests/fixtures/exact_composition_shape_2026-11-01.json',
    *('trading_researcher/'+name+'.py' for name in ('__init__','codec','errors','expressions','outcomes',
        'bounded_math','bounded_outcomes','case_diagnostics','required_inputs','exact_compositions',
        'exact_outcomes','binding','certification','exact_runtime')))))
BOOTSTRAP = 'import sys;sys.path.insert(0,sys.argv[1]);from trading_researcher.exact_runtime import child_entry;child_entry(sys.argv[2])'
CANDIDATE_FIELDS = {'schema','idea_ref','claim_kind','estimand','scope_ast','condition_ast','outcome',
                    'comparator','horizons','test_universe','parameter_origins','feature_refs'}


def read_bundle():
    bundle = {name:(ROOT/name).read_bytes() for name in FILES}
    _document_pins(bundle)
    return bundle


def _document_pins(bundle):
    from .certification import PINS, BOUNDED_PINS, REQUIRED_PINS
    pins = {**PINS,**BOUNDED_PINS,**REQUIRED_PINS,
        'docs/architecture/20_BOUNDED_MATH_REUSE.md':'62cdb38908176ef91fe3368a8c41cdbd10a3f808499aa316e1ed863cf161a569',
        'docs/architecture/26_BOUNDED_EXACT_COMPOSITIONS.md':'fcff34f14878773bd817155121a62212f934a07ba9cba57c3a7864777420418f'}
    for path in DOCS:
        if path in pins:
            require(hashlib.sha256(bundle[path]).hexdigest() == pins[path],
                    'The retained exact runtime contract differs from its approved source')


def compile_payload(payload):
    require(type(payload) is dict and set(payload) == {
        'formalization_id','candidate','catalog','data_manifest','as_of','max_steps'})
    candidate = payload['candidate']
    require(type(candidate) is dict and set(candidate) == CANDIDATE_FIELDS
        and candidate['schema'] == 'hypothesis-exec/3', 'Explicit exact-composition H_exec version required')
    require(candidate['claim_kind'] == 'difference' and candidate['comparator'] == {'kind':'whole_scope'},
            'Compilation cannot substitute a different relationship or comparator')
    estimand = candidate['estimand']
    expected = {'kind':'conditional-minus-scope-mean/1','weighting':'equal_rows',
        'missingness':'scope-true-outcome-observed/1',
        'condition_unknown':'exclude-from-condition-retain-in-scope','nuisance_fit':'none'}
    require(type(estimand) is dict and set(estimand) == set(expected)|{'unit','direction'}
        and all(estimand[key] == value for key,value in expected.items())
        and estimand['direction'] in ('positive','negative','nondirectional'),
        'Compilation requires the existing declared quantity estimand')
    universe = candidate['test_universe']
    require(type(universe) is dict and set(universe) == {'start','end','instruments','data_snapshot_ref'})
    require(type(universe['instruments']) is list and len(universe['instruments']) == 1,
            'This exact-composition profile requires one instrument')
    require(type(candidate['outcome']) is dict and set(candidate['outcome']) == {'program','scale'})
    require(type(candidate['horizons']) is dict and set(candidate['horizons']) == {'grid_seconds','outcome_bars'}
        and type(candidate['horizons']['grid_seconds']) is int and candidate['horizons']['grid_seconds'] == 900)
    request = {'schema':REQUEST,'candidate_ref':payload['formalization_id'],
        'data_snapshot_ref':universe['data_snapshot_ref'],'scope_program':candidate['scope_ast'],
        'condition_program':candidate['condition_ast'],'outcome_program':candidate['outcome']['program'],
        'outcome_scale':candidate['outcome']['scale'],'horizon_bars':candidate['horizons']['outcome_bars'],
        'universe':{key:universe[key] for key in ('start','end','instruments')},
        'as_of':payload['as_of'],'max_steps':payload['max_steps']}
    projected = {**request,'schema':'bounded-reference-case-request/1'}
    start,end,_,_,count,instruments = _validate(legacy_request(projected))
    require(start % 900 == 0 and end % 900 == 0, 'Bound data loading requires the exact 900-second grid')
    manifest = payload['data_manifest']
    require(type(manifest) is dict and manifest.get('partition') == 'development',
            'Exact development cannot compile protected outcome use')
    declared = manifest.get('universe')
    require(type(declared) is dict and {'start','end','instruments'} <= set(declared))
    lower,upper = (_instant(declared[key]) for key in ('start','end'))
    strings(declared['instruments'],'manifest instruments')
    require(lower % 900 == upper % 900 == 0 and lower <= start < end <= upper
        and set(instruments) <= set(declared['instruments']), 'Candidate exceeds the supplied development manifest')
    static = [{'time':start,'instrument':instruments[0],'features':{}}]
    engine = ExactCompositionEngine(payload['catalog'],static)
    outcome = ExactCompositionEngine(payload['catalog'],static,allow_log=True)
    keys = ('scope_program','condition_program','outcome_program')
    require(all(type(request[key]) is dict and request[key].get('schema') == 'research-ast/4' for key in keys))
    programs = {key:(outcome if key == 'outcome_program' else engine).describe(request[key]) for key in keys}
    require(programs['scope_program']['type'] == programs['condition_program']['type'] == 'boolean')
    require(programs['outcome_program']['type'] == 'real' and programs['outcome_program']['unit'] == 'basis_points'
        and estimand['unit'] == 'basis_points' and programs['outcome_program']['feature_refs'],
        'Required raw-feature basis-point quantity outcome expected')
    refs = sorted({ref for program in programs.values() for ref in program['feature_refs']})
    strings(candidate['feature_refs'],'candidate feature references')
    require(refs == sorted(candidate['feature_refs']))
    decision_span = max(lookback(engine._program_node(request[key])) for key in keys[:2])
    outcome_span = lookback(outcome._program_node(request['outcome_program']))
    span = max(decision_span,max(0,outcome_span-request['horizon_bars']*900))
    row_start = max(lower,start-span)
    maximum_rows = ((end-row_start)//900)*len(instruments)
    require(maximum_rows <= 100000, 'RESOURCE_GAP: selected inputs plus warmup exceed the row bound')
    stamp = lambda value:datetime.fromtimestamp(value,timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    return {'schema':'exact-compilation/1','request':deepcopy(request),'candidate_hash':digest(candidate),
        'programs':programs,'feature_refs':refs,
        'row_window':{'start':stamp(row_start),'end':stamp(end),'instruments':instruments},
        'warmup_seconds':span,'unavailable_warmup_seconds':max(0,lower-(start-span)),
        'maximum_input_rows':maximum_rows,'expected_case_count':count,'outcome_unit':'basis_points',
        'scientific_readiness':False}


def _stream(path):
    checksum,size = hashlib.sha256(),0
    with Path(path).open('rb') as stream:
        for raw in iter(lambda:stream.read(1024*1024),b''):
            size += len(raw)
            require(size <= MAX_STREAM, 'Exact stream exceeds the existing storage envelope')
            checksum.update(raw)
    return {'sha256':checksum.hexdigest(),'size':size}


def _read_rows(directory, expected, compiled):
    require(type(expected) is dict and set(expected) == {'sha256','size'})
    checksum,size,rows = hashlib.sha256(),0,[]
    selection = compiled['row_window']
    start,end = (_instant(selection[key]) for key in ('start','end'))
    with (directory/'rows.jsonl').open('rb') as stream:
        while raw := stream.readline(1048577):
            size += len(raw)
            require(len(raw) <= 1048576 and size <= MAX_STREAM and len(rows) < compiled['maximum_input_rows'])
            checksum.update(raw)
            row = decode(raw)
            require(type(row) is dict and type(row.get('time')) is int and start <= row['time'] < end
                and row.get('instrument') in selection['instruments'], 'Input row exceeds its declared selection')
            rows.append(row)
    require({'sha256':checksum.hexdigest(),'size':size} == expected, 'Retained row bytes changed')
    return rows


def _calculate(payload, directory):
    require(type(payload) is dict and set(payload) == {'compilation_input','compilation_hash','rows'})
    compiled = compile_payload(payload['compilation_input'])
    require(digest(compiled) == payload['compilation_hash'], 'Compilation identity changed')
    catalog = payload['compilation_input']['catalog']
    rows = _read_rows(directory,payload['rows'],compiled)
    base = materialize_exact(compiled['request'],catalog,rows)
    report = add_exact_diagnostics(base,catalog,rows,compiled['request']['max_steps']-base['primitive_steps'])
    require(exact_base_projection(report) == base, 'Diagnostic projection changed the numerical base')
    return report,exact_contrast(base)


def _execute(payload, directory):
    report,contrast = _calculate(payload,directory)
    checksum,size = hashlib.sha256(),0
    with (directory/'cases.jsonl').open('xb') as stream:
        for case in report['cases']:
            raw = (canonical(case)+'\n').encode('utf-8')
            size += len(raw)
            require(size <= MAX_STREAM, 'Exact cases exceed the existing output envelope')
            checksum.update(raw);stream.write(raw)
        stream.flush();os.fsync(stream.fileno())
    return {'report':{key:value for key,value in report.items() if key != 'cases'},'contrast':contrast,
        'case_blob':{'sha256':checksum.hexdigest(),'size':size},'rows':deepcopy(payload['rows']),
        'compilation_hash':payload['compilation_hash'],'scientific_readiness':False}


def _verify(payload, directory):
    require(type(payload) is dict and set(payload) == {'execution_input','result'})
    original,execution = payload['result'],payload['execution_input']
    require(type(original) is dict and set(original) == {
        'report','contrast','case_blob','rows','compilation_hash','scientific_readiness'})
    require(original['scientific_readiness'] is False and original['compilation_hash'] == execution['compilation_hash']
        and original['rows'] == execution['rows'])
    report,contrast = _calculate(execution,directory)
    require(canonical(original['report']) == canonical({key:value for key,value in report.items() if key != 'cases'}))
    require(canonical(original['contrast']) == canonical(contrast))
    checksum,size = hashlib.sha256(),0
    with (directory/'cases.jsonl').open('rb') as stream:
        for case in report['cases']:
            raw = (canonical(case)+'\n').encode('utf-8')
            require(stream.read(len(raw)) == raw, 'Returned cases differ from exact retained replay')
            size += len(raw);checksum.update(raw)
            require(size <= MAX_STREAM)
        require(stream.read(1) == b'', 'Returned cases contain an unexpected suffix')
    require(original['case_blob'] == {'sha256':checksum.hexdigest(),'size':size})
    return {'schema':'exact-case-verification/1','result_hash':digest(original),
        'compilation_hash':execution['compilation_hash'],'case_blob':original['case_blob'],
        'checked_cases':len(report['cases']),'scientific_readiness':False}


def child_entry(request_path):
    path = Path(request_path)
    request = decode(path.read_bytes())
    require(type(request) is dict and set(request) == {'mode','payload','footprint'})
    require(set(request['footprint']) == set(FILES) and hashes(read_bundle()) == request['footprint'])
    mode,payload = request['mode'],request['payload']
    if mode == 'compile':result = compile_payload(payload)
    elif mode == 'execute':result = _execute(payload,path.parent)
    elif mode == 'verify':result = _verify(payload,path.parent)
    elif mode == 'certify':
        require(payload == {'profile':PROFILE})
        suite = unittest.TestSuite()
        for name in TESTS:
            suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=Path(name).name))
        output = io.StringIO()
        checked = unittest.TextTestRunner(stream=output).run(suite)
        require(checked.testsRun == 51 and checked.wasSuccessful() and not checked.skipped
            and not checked.expectedFailures and not checked.unexpectedSuccesses, output.getvalue())
        result = {'schema':'exact-conformance-result/1','profile':PROFILE,'tests':51,
            'failures':0,'errors':0,'skipped':0,'scientific_readiness':False}
    else:raise ValueError('Unknown exact runtime child mode')
    require(hashes(read_bundle()) == request['footprint'])
    print(canonical({'mode':mode,'request_hash':digest(payload),'footprint':request['footprint'],
                     'result':result,'environment':environment(request['footprint'])}))


def run_child(bundle, mode, payload, directory, *, timeout=1800):
    from .binance_normalize import _run_child
    require(type(timeout) is int and 1 <= timeout <= 1800 and mode in ('compile','execute','verify','certify'))
    require(type(bundle) is dict and set(bundle) == set(FILES) and all(type(raw) is bytes for raw in bundle.values()))
    _document_pins(bundle)
    directory = Path(directory)
    for name,raw in bundle.items():
        destination = directory/name
        destination.parent.mkdir(parents=True,exist_ok=True)
        write_file(destination,raw)
    footprint = hashes(bundle)
    write_file(directory/'request.json',canonical({'mode':mode,'payload':payload,'footprint':footprint}).encode('utf-8'))
    report = _run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],directory,timeout=timeout)
    require(type(report) is dict and set(report) == {'mode','request_hash','footprint','result','environment'}
        and report['mode'] == mode and report['request_hash'] == digest(payload)
        and report['footprint'] == footprint and _environment_current(report['environment']))
    require(hashes({name:(directory/name).read_bytes() for name in bundle}) == footprint)
    return report
