"""Retained-source child for second-idea composition and original-formula audit.

Execution and exact replay remain in the frozen paired runtime. This child has
no registry, credentials or provider interface. It receives bounded canonical
input files only after the owning host has checked the applicable gates.
"""
from pathlib import Path
import sys

from ..binding import environment, hashes, require, write_file
from ..certification import _environment_current
from ..codec import canonical, decode, digest
from .. import paired_runtime
from . import composition

ROOT = Path(__file__).resolve().parents[2]
FILES = tuple(sorted({*paired_runtime.FILES, composition.ORACLE,
    'trading_researcher/paired_breakout/__init__.py',
    'trading_researcher/paired_breakout/composition.py',
    'trading_researcher/paired_breakout/runtime.py'}))
BOOTSTRAP = ('import sys;sys.path.insert(0,sys.argv[1]);'
    'from trading_researcher.paired_breakout.runtime import child_entry;child_entry(sys.argv[2])')


def read_bundle():
    return {name: (ROOT / name).read_bytes() for name in FILES}


def child_entry(request_path):
    path = Path(request_path)
    request = decode(path.read_bytes())
    require(type(request) is dict and set(request) == {'mode', 'payload', 'footprint'})
    require(set(request['footprint']) == set(FILES) and hashes(read_bundle()) == request['footprint'])
    mode, payload = request['mode'], request['payload']
    if mode == 'composition':
        result = composition.qualify(payload)
    elif mode == 'audit':
        require(type(payload) is dict and set(payload) == {'execution_input', 'result'})
        source, result = payload['execution_input'], payload['result']
        require(type(source) is dict and set(source) == {'compilation_input', 'compilation_hash', 'rows'})
        compiled = composition.original_compilation(source['compilation_input'])
        require(source['compilation_hash'] == result['compilation_hash'] == digest(compiled)
                and source['rows'] == result['rows'], 'Original audit input/result binding differs')
        require(result['report']['processing_complete'] is True,
                'A partial execution cannot become a completed original-formula audit')
        require(paired_runtime._stream(path.parent / 'cases.jsonl') == result['case_blob'])
        rows = paired_runtime._read_rows(path.parent, source['rows'])
        cases = []
        with (path.parent / 'cases.jsonl').open('rb') as stream:
            for line in stream:
                require(len(line) <= 1048576 and len(cases) < 50000,
                        'Original audit case stream exceeds its bounds')
                cases.append(decode(line))
        require(len(cases) == compiled['expected_case_count'] == result['report']['processed_case_count'])
        result = composition.audit(source['compilation_input'], rows, cases)
    else:
        raise ValueError('Unknown breakout child mode')
    require(hashes(read_bundle()) == request['footprint'])
    print(canonical({'mode': mode, 'request_hash': digest(payload), 'footprint': request['footprint'],
        'result': result, 'environment': environment(request['footprint'])}))


def run_child(bundle, mode, payload, directory, *, timeout=1800):
    from ..binance_normalize import _run_child
    require(type(timeout) is int and 1 <= timeout <= 1800 and set(bundle) == set(FILES))
    require(mode in ('composition', 'audit'), 'Unknown breakout child mode')
    directory = Path(directory)
    for name, raw in bundle.items():
        destination = directory / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_file(destination, raw)
    expected = hashes(bundle)
    write_file(directory / 'request.json', canonical({'mode': mode, 'payload': payload,
        'footprint': expected}).encode())
    report = _run_child([sys.executable, '-I', '-S', '-B', '-c', BOOTSTRAP,
        str(directory), str(directory / 'request.json')], directory, timeout=timeout)
    require(type(report) is dict and set(report) == {'mode', 'request_hash', 'footprint', 'result', 'environment'}
            and report['mode'] == mode and report['request_hash'] == digest(payload)
            and report['footprint'] == expected and _environment_current(report['environment']))
    require(hashes({name: (directory / name).read_bytes() for name in bundle}) == expected)
    return report
