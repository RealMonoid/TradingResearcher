"""D098 retained20M execute/replay version; native ownership remains separate."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import io
import math
import os
from pathlib import Path
import shutil
import sys
import time
import unittest

from . import exact_runtime as legacy, exact_resources_v2 as resources
from .binding import environment, hashes, require, write_file
from .certification import _environment_current
from .codec import canonical, decode, digest, integer
from .storage import blob_identity

ROOT = Path(__file__).resolve().parents[1]
PROFILE = resources.PROFILE
RESOURCE_CONTRACT = resources.RESOURCE_CONTRACT
MAX_STEPS = 20000000
AGGREGATE_STEPS = 40000000
MAX_SECONDS = 1800
MAX_STREAM = legacy.MAX_STREAM
TESTS = (*legacy.TESTS, 'tests/test_exact_resources_v2.py', 'tests/test_exact_resources_v2_review.py')
EXPECTED_TESTS = 72
DOCS = (*legacy.DOCS, 'docs/architecture/27_EXACT_COMPUTATION_RESOURCES.md',
        'trading_researcher/EXACT_RESOURCES_V2.md', 'trading_researcher/EXACT_RUNTIME_V2.md')
FILES = tuple(sorted(set(legacy.FILES) | set(TESTS) | set(DOCS) | {
    'trading_researcher/exact_resources_v2.py', 'trading_researcher/exact_runtime_v2.py',
    'trading_researcher/exact_resource_candidate.py', 'trading_researcher/storage.py'}))
BOOTSTRAP = 'import sys;sys.path.insert(0,sys.argv[1]);from trading_researcher.exact_runtime_v2 import child_entry;child_entry(sys.argv[2])'


def read_bundle():
    bundle = {name: (ROOT / name).read_bytes() for name in FILES}
    legacy._document_pins(bundle)
    require(hashlib.sha256(bundle['docs/architecture/27_EXACT_COMPUTATION_RESOURCES.md']).hexdigest()
        == '92ee9fd3d32964390e0ae6aeeb449c31d51a7dbf545d8db2feb48a8f14ff7e57',
        'D098 resource contract differs from approved source')
    return bundle


def compile_payload(payload):
    # Validate the actual v2 budget before the old structural compiler sees a
    # bounded compatibility projection. No actual work/counter is projected.
    require(type(payload) is dict and set(payload) == {
        'formalization_id', 'candidate', 'catalog', 'data_manifest', 'as_of', 'max_steps'})
    limit = integer(payload['max_steps'], 'D098 primitive budget', 1)
    require(limit <= MAX_STEPS, 'D098 request exceeds20M')
    compiled = deepcopy(legacy.compile_payload({**payload, 'max_steps': min(limit, 10000000)}))
    compiled.update(schema='exact-compilation/2', resource_contract=RESOURCE_CONTRACT)
    compiled['request'].update(schema=resources.REQUEST, max_steps=limit)
    resources.structural_projection(compiled['request'])
    return compiled


def primitive_steps(report):
    require(type(report) is dict and type(report.get('diagnostics')) is dict and type(report.get('request')) is dict,
        'Complete numerical and diagnostic counters required')
    numerical = integer(report.get('primitive_steps'), 'numerical primitive steps')
    diagnostic = integer(report['diagnostics'].get('primitive_steps'), 'diagnostic primitive steps')
    budget = integer(report.get('request', {}).get('max_steps'), 'actual request primitive budget', 1)
    require(budget <= MAX_STEPS and numerical + diagnostic <= budget,
        'D098 shared per-child allowance exceeded')
    return numerical + diagnostic


def _row_descriptor(value):
    require(type(value) is dict and set(value) == {'sha256', 'size'}, 'Exact row descriptor required')
    blob_identity(value['sha256'])
    require(integer(value['size'], 'retained row bytes') <= MAX_STREAM, 'Row stream exceeds512MiB')
    return value


def _calculate(payload, directory):
    require(type(payload) is dict and set(payload) == {'compilation_input', 'compilation_hash', 'rows'})
    compiled = compile_payload(payload['compilation_input'])
    require(digest(compiled) == payload['compilation_hash'], 'D098 compilation identity changed')
    rows = legacy._read_rows(directory, _row_descriptor(payload['rows']), compiled)
    catalog = payload['compilation_input']['catalog']
    base = resources.materialize(compiled['request'], catalog, rows)
    report = resources.add_diagnostics(base, catalog, rows, compiled['request']['max_steps'] - base['primitive_steps'])
    projected = resources.base_projection(report)
    require(canonical({key: value for key, value in projected.items() if key != 'cases'})
        == canonical({key: value for key, value in base.items() if key != 'cases'}),
        'D098 diagnostics changed numerical metadata')
    require(len(projected['cases']) == len(base['cases']) and all(canonical(left) == canonical(right)
        for left, right in zip(projected['cases'], base['cases'])),
        'D098 diagnostics changed the complete numerical cases')
    primitive_steps(report)
    return report, resources.contrast(base)


def _execute(payload, directory):
    report, contrast = _calculate(payload, directory)
    checksum, size = hashlib.sha256(), 0
    with (directory / 'cases.jsonl').open('xb') as stream:
        for case in report['cases']:
            raw = (canonical(case) + '\n').encode('utf-8')
            size += len(raw)
            require(size <= MAX_STREAM, 'D098 case stream exceeds512MiB')
            stream.write(raw); checksum.update(raw)
        stream.flush(); os.fsync(stream.fileno())
    return {'schema': 'exact-execution-result/2', 'resource_contract': RESOURCE_CONTRACT,
        'report': {key: value for key, value in report.items() if key != 'cases'}, 'contrast': contrast,
        'case_blob': {'sha256': checksum.hexdigest(), 'size': size}, 'rows': deepcopy(payload['rows']),
        'compilation_hash': payload['compilation_hash'], 'scientific_readiness': False}


def _verify(payload, directory):
    require(type(payload) is dict and set(payload) == {'execution_input', 'result'})
    original, execution = payload['result'], payload['execution_input']
    require(type(execution) is dict and set(execution) == {'compilation_input', 'compilation_hash', 'rows'})
    require(type(original) is dict and set(original) == {'schema', 'resource_contract', 'report', 'contrast',
        'case_blob', 'rows', 'compilation_hash', 'scientific_readiness'})
    require(original['schema'] == 'exact-execution-result/2' and original['resource_contract'] == RESOURCE_CONTRACT
        and original['scientific_readiness'] is False and original['compilation_hash'] == execution['compilation_hash']
        and canonical(original['rows']) == canonical(execution['rows']))
    report, contrast = _calculate(execution, directory)
    require(canonical(original['report']) == canonical({key: value for key, value in report.items() if key != 'cases'}))
    require(canonical(original['contrast']) == canonical(contrast))
    checksum, size = hashlib.sha256(), 0
    with (directory / 'cases.jsonl').open('rb') as stream:
        for case in report['cases']:
            raw = (canonical(case) + '\n').encode('utf-8')
            require(stream.read(len(raw)) == raw, 'D098 case bytes differ from fresh replay')
            size += len(raw); checksum.update(raw)
            require(size <= MAX_STREAM)
        require(stream.read(1) == b'', 'D098 case stream has an unexpected suffix')
    require(canonical(original['case_blob']) == canonical({'sha256': checksum.hexdigest(), 'size': size}))
    return {'schema': 'exact-case-verification/2', 'resource_contract': RESOURCE_CONTRACT,
        'result_hash': digest(original), 'compilation_hash': execution['compilation_hash'],
        'case_blob': original['case_blob'], 'checked_cases': len(report['cases']),
        'primitive_steps': primitive_steps(report), 'scientific_readiness': False}


def child_entry(request_path):
    path = Path(request_path)
    request = decode(path.read_bytes())
    require(type(request) is dict and set(request) == {'mode', 'payload', 'footprint'})
    require(set(request['footprint']) == set(FILES) and hashes(read_bundle()) == request['footprint'])
    mode, payload = request['mode'], request['payload']
    if mode == 'compile': result = compile_payload(payload)
    elif mode == 'execute': result = _execute(payload, path.parent)
    elif mode == 'verify': result = _verify(payload, path.parent)
    elif mode == 'certify':
        require(payload == {'profile': PROFILE})
        suite = unittest.TestSuite()
        for name in TESTS:
            suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=Path(name).name))
        output = io.StringIO()
        checked = unittest.TextTestRunner(stream=output).run(suite)
        require(checked.testsRun == EXPECTED_TESTS and checked.wasSuccessful() and not checked.skipped
            and not checked.expectedFailures and not checked.unexpectedSuccesses, output.getvalue())
        result = {'schema': 'exact-conformance-result/2', 'profile': PROFILE, 'resource_contract': RESOURCE_CONTRACT,
            'tests': EXPECTED_TESTS, 'failures': 0, 'errors': 0, 'skipped': 0, 'scientific_readiness': False}
    else: raise ValueError('Unknown D098 runtime child mode')
    require(hashes(read_bundle()) == request['footprint'])
    print(canonical({'mode': mode, 'request_hash': digest(payload), 'footprint': request['footprint'],
        'result': result, 'environment': environment(request['footprint'])}))


def _run_retained(bundle, mode, payload, directory, timeout):
    from .binance_normalize import _run_child
    require(type(timeout) in (int, float) and math.isfinite(timeout) and 0 < timeout <= MAX_SECONDS)
    require(mode in ('compile', 'execute', 'verify', 'certify'))
    require(type(bundle) is dict and set(bundle) == set(FILES) and all(type(raw) is bytes for raw in bundle.values()))
    require(hashes(bundle) == hashes(read_bundle()), 'D098 retained source differs from installed current version')
    directory = Path(directory)
    for name, raw in bundle.items():
        destination = directory / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_file(destination, raw)
    footprint = hashes(bundle)
    write_file(directory / 'request.json', canonical({'mode': mode, 'payload': payload, 'footprint': footprint}).encode('utf-8'))
    report = _run_child([sys.executable, '-I', '-S', '-B', '-c', BOOTSTRAP, str(directory), str(directory / 'request.json')],
        directory, timeout=timeout)
    require(type(report) is dict and set(report) == {'mode', 'request_hash', 'footprint', 'result', 'environment'}
        and report['mode'] == mode and report['request_hash'] == digest(payload)
        and report['footprint'] == footprint and _environment_current(report['environment']))
    require(hashes({name: (directory / name).read_bytes() for name in bundle}) == footprint)
    require(hashes(read_bundle()) == footprint, 'D098 installed source changed during execution')
    return report


def run_child(bundle, mode, payload, directory, *, timeout=MAX_SECONDS):
    require(type(timeout) is int and 1 <= timeout <= MAX_SECONDS)
    return _run_retained(bundle, mode, payload, directory, timeout)


def run_operation(bundle, payload, directory, *, timeout=MAX_SECONDS):
    """Retain execute bytes before replay; one monotonic deadline for both phases."""
    require(type(timeout) is int and 1 <= timeout <= MAX_SECONDS)
    require(type(payload) is dict and set(payload) == {'compilation_input', 'compilation_hash', 'rows'})
    started = time.monotonic_ns(); deadline = started + timeout * 1000000000
    utc = lambda: datetime.now(timezone.utc).isoformat()
    start_utc = utc()
    directory = Path(directory)
    compiled = compile_payload(payload['compilation_input'])
    require(digest(compiled) == payload['compilation_hash'])
    rows = directory / 'rows.jsonl'
    require(canonical(legacy._stream(rows)) == canonical(_row_descriptor(payload['rows'])))
    first, second = directory / 'execute', directory / 'replay'
    first.mkdir(); second.mkdir()
    shutil.copyfile(rows, first / 'rows.jsonl')
    def remaining():
        available = deadline - time.monotonic_ns()
        require(available > 0, 'D098 shared whole-operation deadline exhausted')
        return available / 1000000000
    execution = _run_retained(bundle, 'execute', payload, first, remaining())
    execute_end = time.monotonic_ns(); execute_end_utc = utc()
    require(execute_end <= deadline, 'D098 execution exceeded the shared deadline')
    result = execution['result']
    require(type(result) is dict and result.get('schema') == 'exact-execution-result/2'
        and result.get('resource_contract') == RESOURCE_CONTRACT and result.get('scientific_readiness') is False
        and {'report', 'case_blob'} <= set(result))
    used = primitive_steps(result['report'])
    require(canonical(legacy._stream(first / 'cases.jsonl')) == canonical(result['case_blob']))
    shutil.copyfile(rows, second / 'rows.jsonl')
    shutil.copyfile(first / 'cases.jsonl', second / 'cases.jsonl')
    verification = _run_retained(bundle, 'verify', {'execution_input': payload, 'result': result}, second, remaining())
    finished = time.monotonic_ns(); finish_utc = utc()
    require(type(verification.get('result')) is dict
        and verification['result'].get('schema') == 'exact-case-verification/2'
        and verification['result'].get('resource_contract') == RESOURCE_CONTRACT)
    expected = {'schema': 'exact-case-verification/2', 'resource_contract': RESOURCE_CONTRACT,
        'result_hash': digest(result), 'compilation_hash': payload['compilation_hash'],
        'case_blob': result['case_blob'], 'checked_cases': integer(result['report'].get('processed_case_count'), 'retained case count'),
        'primitive_steps': used, 'scientific_readiness': False}
    require(canonical(verification['result']) == canonical(expected), 'D098 complete verifier body differs from execution')
    replayed = integer(verification['result'].get('primitive_steps'), 'fresh replay primitive steps')
    require(finished <= deadline and replayed == used and used + replayed <= AGGREGATE_STEPS,
        'D098 aggregate steps or shared deadline exceeded')
    return {'profile': PROFILE, 'resource_contract': RESOURCE_CONTRACT, 'execution': execution,
        'verification': verification, 'aggregate_primitive_steps': used + replayed,
        'timing': {'started_at_utc': start_utc, 'execute_completed_at_utc': execute_end_utc,
            'completed_at_utc': finish_utc, 'execute_elapsed_ns': execute_end - started,
            'replay_elapsed_ns': finished - execute_end, 'total_elapsed_ns': finished - started,
            'shared_timeout_seconds': timeout,
            'qualification': 'Operational execute/replay phase timing only, outside numerical result identity; not complete idea-to-checked-report duration.'}}
