"""Pinned existing-semantic native conformance; no scientific authority.

Independent cases and expected complete outputs predate this runner. Generic
runtime retention and compatibility metadata cannot add members to this profile.
"""
import hashlib
import importlib
import importlib.util
import io
from pathlib import Path
import random
import sys
import tempfile
import unittest
from zipfile import ZipFile

from .binding import environment, require, write_file
from .codec import canonical, decode, digest, integer
from .errors import Conflict
from .evaluation_plans import source_bundle, footprint
from .native_backend import INFO, make_draw_factory
from .native_environment import NativeContext, KERNEL_FILE, current
from .native_runtime import verify_tree


ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'stationary-native-runtime/1'
BOOTSTRAP = ('import sys;sys.path.insert(0,sys.argv[1]);'
             'from trading_researcher.native_qualification_profile import child_entry;'
             'child_entry(sys.argv[2])')
MANIFEST_SHA = '384f70b80d41878c3b7a35c7e3b7b981ea891aa6dabe5df79e9893ead707ee33'
ARCHIVE_SHA = '8c0458b745399a3bc92f912bb129ea1c6969466a0cad3239d5c361c23746dc21'
KERNEL_SHA = '46d1c2efc66e8cd3546e72027970f7951360e6f18dd1f868d82efbe83e78d509'
RESULT_SHA = '720ac237f2ad3e29a5a9d94191af68a90a549f476c6e0f2d5bae36b537901b09'
STREAM_SHA = '76c3fb49b827455afaf488104f0ee88788254446e4bcf1fad07f73b42cb4f533'
STREAM_SIZE = 15143319
NUMERIC_PINS = {
    'trading_researcher/stationary_bootstrap.py': 'f6f1b27ca43acde60972caa3af2fbec082e324180b13cb60f4fb64142dfd8d57',
    'trading_researcher/native_backend.py': '415c59d6e9be6a21bb29b0679fac806e2a35d1fd055784d44b2a3c28f34122ca',
    'trading_researcher/family_pipeline.py': 'c082918d76595f15a89c4607578c526eb5354619deccf7e991d9319d9095c0bb',
    'trading_researcher/study_pipeline.py': '2d8b00d6f4f3c5e52ae0f1569b0ad4f7bfef628943dab0e5107385ed73fbb8de',
}
FIXED = {
    'tests/fixtures/native-calculator-integration-2026-11-02.zip': '39907b38a6e91a7bdf30b2101d93e0a17cba134f9dffe949631abd02cc6b6008',
    'tests/fixtures/native-environment-checks-2026-11-02.zip': 'fda1c157fbf365f5a8826a9ba0e9f7d19fae5f36f7299bf7a770a9764524fd30',
    'tests/fixtures/study-source-0f1bf36.zip': 'ee335215005ce138a058ea3499c5424ac929003a9243e80c139ed0c18dc96e2f',
    'tests/bootstrap_oracle.py': '83b9c8422b6ba061c2cf5240541ae00d3cee3417f4589b9e0e1d4273a82b1286',
    'tests/bootstrap_support.py': 'b2639c98d7acbfddfd25a29f9202a1bbd7f66082d3e22dd19c99a98ac3e02540',
}
LOOP_FILE = '.trf-runtime/native-runtime-2026-11-02/canonical_draw_independent_cases.py'
LOOP_SHA = 'a2569b97280dbf88a0b10560f0c31f19193718f12a83d7e3261a64f42653ced3'
LOADED = footprint(source_bundle())
META = 1024 * 1024


def capture_source():
    bundle = source_bundle()
    if footprint(bundle) != LOADED:
        raise Conflict('Native qualification source changed since import; restart')
    require(all(footprint(bundle).get(name) == checksum for name, checksum in NUMERIC_PINS.items()),
            'Native profile numeric implementation differs from the checked version')
    for name, checksum in FIXED.items():
        raw = (ROOT / name).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == checksum, 'Independent native fixture changed')
        bundle[name] = raw
    with ZipFile(io.BytesIO(bundle['tests/fixtures/native-calculator-integration-2026-11-02.zip'])) as archive:
        bundle[LOOP_FILE] = archive.read(LOOP_FILE)
    require(hashlib.sha256(bundle[LOOP_FILE]).hexdigest() == LOOP_SHA, 'Independent loop assertions changed')
    return bundle


def host_inputs(source):
    name = 'tests/fixtures/native-environment-checks-2026-11-02.zip'
    require(hashlib.sha256(source[name]).hexdigest() == FIXED[name], 'Host reference source changed')
    with ZipFile(io.BytesIO(source[name])) as archive:
        observed = decode(archive.read('.trf-runtime/native-runtime-2026-11-02/environment-reference-observation.json'))
    return observed['host_images']


def validate_runtime(runtime):
    body = runtime['body']
    require(digest(body['manifest']) == MANIFEST_SHA and body['archive']['sha256'] == ARCHIVE_SHA
            and body['manifest']['files'][KERNEL_FILE]['sha256'] == KERNEL_SHA,
            'Runtime is not a member of the independently checked native profile')


def _expected_result():
    return {'schema': 'native-runtime-conformance-result/1', 'profile': PROFILE,
            'tests': 13, 'failures': 0, 'errors': 0, 'skipped': 0,
            'complete_result_sha256': RESULT_SHA, 'complete_stream_sha256': STREAM_SHA,
            'draws': 59997, 'native_lengths': [4, 8, 16], 'scientific_readiness': False}


def _request(source, capsule, directory, phase, stream_limit):
    body = capsule['body']
    return {'profile': PROFILE, 'input_id': capsule['id'], 'runtime_id': body['runtime_id'],
            'runtime_manifest': body['runtime_manifest'], 'host_images': body['host_images'],
            'runtime_directory': str(directory), 'phase': phase, 'stream_limit': stream_limit,
            'source_footprint': footprint(source)}


def child_entry(request_path):
    request_path = Path(request_path)
    request = decode(request_path.read_bytes())
    expected = request['source_footprint']
    source = {name: (ROOT / name).read_bytes() for name in expected}
    require(footprint(source) == expected and footprint(capture_source()) == expected,
            'Native conformance source differs')
    require(request['profile'] == PROFILE and request['phase'] in ('generate', 'replay')
            and request['host_images'] == host_inputs(source), 'Native conformance inputs differ')
    integer(request['stream_limit'], 'Native conformance stream bound', 1)
    require(request['stream_limit'] <= 64 * META)
    directory = Path(request['runtime_directory'])
    require(digest(request['runtime_manifest']) == MANIFEST_SHA)
    verify_tree(directory, request['runtime_manifest'])
    sys.path.insert(1, str(directory))
    sys.path.insert(2, str(ROOT / 'tests'))
    numpy = importlib.import_module('numpy')
    core = importlib.import_module('_trf_stationary_native')
    require(core.implementation_info() == INFO)
    # Execute the byte-pinned independent cases with only their already checked
    # explicit binary selection. Assertions and scalar oracle remain unchanged.
    spec = importlib.util.spec_from_file_location('native_loop_cases', ROOT / LOOP_FILE)
    loops = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loops
    previous_argv = sys.argv
    try:
        sys.argv = [str(ROOT / LOOP_FILE), str(directory / KERNEL_FILE)]
        spec.loader.exec_module(loops)
    finally:
        sys.argv = previous_argv
    from bootstrap_oracle import binary_report
    from .stationary_bootstrap import calculate, randomness
    context = NativeContext(request['runtime_id'], request['runtime_manifest'], directory, request['host_images'])
    before = environment(expected, _native=context)
    log = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(loops)
    checked = unittest.TextTestRunner(stream=log).run(suite)
    write_file(request_path.parent / 'conformance.txt', log.getvalue().encode())
    require(checked.testsRun == 13 and checked.wasSuccessful() and not checked.skipped
            and not checked.expectedFailures and not checked.unexpectedSuccesses, log.getvalue())
    factory = make_draw_factory(core, numpy)
    selections = []
    def selected(rng, rows, length):
        initial = rng.getstate()
        engine = factory(rng, rows, length)
        require(rng.getstate() == initial and engine is not None, 'Expected native fixture selection differs')
        selections.append(length)
        return engine
    checksum, draws, size = hashlib.sha256(), 0, 0
    replay = request['phase'] == 'replay'
    stream_path = request_path.parent / ('expected-stream.jsonl' if replay else 'stream.jsonl')
    with stream_path.open('rb' if replay else 'xb') as stream:
        def retain(encoded):
            nonlocal draws, size
            raw = encoded + b'\n'
            size += len(raw)
            require(size <= request['stream_limit'], 'Native conformance stream exceeded its bound')
            if replay:
                require(stream.read(len(raw)) == raw, 'Separate native conformance replay differs')
            else:
                require(stream.write(raw) == len(raw))
            checksum.update(raw)
            draws += 1
        design = {'base_length': 8, 'primary_count': 2, 'randomness': randomness(713),
                  'mc_policy': {'schema': 'mc-boundary-policy/1',
                                'noncoverage': {'numerator': '1', 'denominator': '100'},
                                'delta': {'numerator': '1', 'denominator': '20'}, 'direction': 'positive'}}
        calculated = calculate(binary_report(4096), design,
                               {'max_seconds': 180, 'max_segments': 100000000},
                               on_draw_bytes=retain, _draw_factory=selected)
        write_file(request_path.parent / 'computed-result.json', canonical(calculated).encode())
        if replay:
            require(stream.read(1) == b'', 'Unexpected native conformance replay suffix')
    result = {**_expected_result(), 'draws': draws, 'native_lengths': selections,
              'complete_result_sha256': digest(calculated), 'complete_stream_sha256': checksum.hexdigest()}
    require(canonical(result) == canonical(_expected_result()), 'Independent complete conformance result differs')
    after = environment(expected, _native=context)
    require(footprint({name: (ROOT / name).read_bytes() for name in expected}) == expected)
    print(canonical({'request': request, 'request_hash': digest(request), 'result': result,
                     'environment_before': before, 'environment_after': after,
                     'stream_blob': {'sha256': checksum.hexdigest(), 'size': size}}), flush=True)


def execute(source, capsule, runtime_directory, remaining, meter, outputs):
    from .binance_normalize import _run_child
    body = capsule['body']
    available = body['limits']['max_storage_bytes'] - body['initial_storage_bytes'] - meter['materialized_bytes']
    overhead = 2 * (sum(map(len, source.values())) + 4 * META) + META
    stream_limit = min(64 * META, (available - overhead) // 4)
    require(stream_limit > 0, 'Native qualification inputs leave no stream headroom')
    proofs, raw = [], None
    for phase in ('generate', 'replay'):
        request = _request(source, capsule, runtime_directory, phase, stream_limit)
        with tempfile.TemporaryDirectory(prefix='trf-native-qualification-') as temporary:
            directory = Path(temporary)
            meter['accounting_complete'] = False
            try:
                for name, value in source.items():
                    path = directory / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    write_file(path, value)
                write_file(directory / 'request.json', canonical(request).encode())
                if raw is not None:
                    write_file(directory / 'expected-stream.jsonl', raw)
                response = _run_child([sys.executable, '-I', '-S', '-B', '-c', BOOTSTRAP,
                                       str(directory), str(directory / 'request.json')],
                                      directory, timeout=remaining())
                require(response.get('request') == request and response.get('request_hash') == digest(request),
                        'Native qualification response identity differs')
                path = directory / ('stream.jsonl' if phase == 'generate' else 'expected-stream.jsonl')
                observed = path.read_bytes()
                require(len(observed) <= stream_limit and response.get('stream_blob') ==
                        {'sha256': hashlib.sha256(observed).hexdigest(), 'size': len(observed)})
                if raw is None:
                    raw = observed
                else:
                    require(observed == raw)
                require(footprint({name: (directory / name).read_bytes() for name in source}) == footprint(source))
                proofs.append(response)
            finally:
                for path in directory.rglob('*'):
                    if path.is_file():
                        meter['materialized_bytes'] += path.stat().st_size
                for name in ('stream.jsonl', 'expected-stream.jsonl', 'computed-result.json',
                             'conformance.txt', 'child-output.json', 'child-errors.txt'):
                    path = directory / name
                    if path.is_file():
                        outputs.append((phase + '/' + name, path.read_bytes()))
                meter['accounting_complete'] = True
    report = {'profile': PROFILE, 'input_id': capsule['id'], 'source_footprint': footprint(source), 'proofs': proofs}
    validate_report(report, source, capsule, runtime_directory)
    return report


def bound_environments(report, source, capsule, runtime_directory):
    """Validate the fixed proof bindings, without asserting cache currency."""
    require(type(report) is dict and set(report) == {'profile', 'input_id', 'source_footprint', 'proofs'}
            and report['profile'] == PROFILE and report['input_id'] == capsule['id']
            and report['source_footprint'] == footprint(source)
            and type(report['proofs']) is list and len(report['proofs']) == 2,
            'Exact complete native conformance report required')
    body = capsule['body']
    require(body['source_footprint'] == footprint(source), 'Native capsule source binding differs')
    environments = []
    for phase, proof in zip(('generate', 'replay'), report['proofs'], strict=True):
        require(type(proof) is dict and set(proof) == {'request', 'request_hash', 'result',
                'environment_before', 'environment_after', 'stream_blob'})
        request = proof['request']
        require(type(request) is dict and set(request) == set(_request(source, capsule, runtime_directory, phase, 1)))
        require(type(request['runtime_directory']) is str and Path(request['runtime_directory']).is_absolute(),
                'Original native runtime location must be an absolute string')
        integer(request['stream_limit'], 'Qualified stream bound', 1)
        require(request['stream_limit'] <= 64 * META
                and request == _request(source, capsule, request['runtime_directory'], phase, request['stream_limit'])
                and proof['request_hash'] == digest(request)
                and canonical(proof['result']) == canonical(_expected_result())
                and type(proof['stream_blob']) is dict and set(proof['stream_blob']) == {'sha256', 'size'}
                and proof['stream_blob']['sha256'] == STREAM_SHA)
        integer(proof['stream_blob']['size'], 'Qualified stream size', 1)
        require(proof['stream_blob']['size'] == STREAM_SIZE <= request['stream_limit'])
        for field in ('environment_before', 'environment_after'):
            environments.append(proof[field])
    require(report['proofs'][0]['stream_blob'] == report['proofs'][1]['stream_blob'])
    return environments


def validate_report(report, source, capsule, runtime_directory):
    body = capsule['body']
    for observed in bound_environments(report, source, capsule, runtime_directory):
        require(current(observed, body['runtime_id'], body['runtime_manifest'],
                        runtime_directory, body['host_images']), 'Native qualification environment is not current')
