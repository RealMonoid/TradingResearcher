"""Qualified native study transport; owned calculator semantics stay unchanged."""
import hashlib
import importlib
from pathlib import Path
import sys

from .binding import environment, require, write_file
from .codec import canonical, decode, digest, integer
from .evaluation_plans import source_bundle, footprint
from .native_backend import INFO, make_draw_factory
from .native_environment import NativeContext, KERNEL_FILE, current
from .native_qualification_profile import PROFILE, MANIFEST_SHA, KERNEL_SHA
from .native_runtime import verify_tree
from .storage import blob_identity
from .study_pipeline import calculate_world
from .study_stream import EncodedStream


SCHEMA = 'qualified-native-study-runtime/1'
BOOTSTRAP = ('import sys;sys.path.insert(0,sys.argv[1]);'
             'from trading_researcher.native_study_pipeline import child_entry;child_entry(sys.argv[2])')
FIELDS = {'schema', 'profile', 'qualification_id', 'runtime_id', 'runtime_manifest',
          'host_images', 'source_footprint'}
EXTRA_FIELDS = {'environment_before', 'native_binding', 'draw_engines'}


class ParentContext:
    """Private selected input data, never a request-supplied Python factory."""
    def __init__(self, source, selected, *, _control=None):
        if _control is not None:
            from .study_process_control import ProcessControl
            require(type(_control) is ProcessControl, 'Owned native study process control required')
        self.control = _control
        require(type(selected) is dict and set(selected) == {'binding', 'directory'},
                'Exact selected native study input required')
        selected = decode(canonical(selected))
        binding = selected['binding']
        require(type(binding) is dict and set(binding) == FIELDS
                and binding['schema'] == SCHEMA and binding['profile'] == PROFILE
                and binding['source_footprint'] == footprint(source), 'Selected native study source binding differs')
        for key in ('qualification_id', 'runtime_id'):
            blob_identity(binding[key])
        require(type(selected['directory']) is str and Path(selected['directory']).is_absolute(),
                'Owned native cache location must be absolute')
        manifest = binding['runtime_manifest']
        require(digest(manifest) == MANIFEST_SHA and manifest['files'][KERNEL_FILE]['sha256'] == KERNEL_SHA,
                'Selected native study runtime is outside its qualified profile')
        self.binding = binding
        self.directory = Path(selected['directory'])
        self.context = NativeContext(binding['runtime_id'], manifest, self.directory, binding['host_images'])
        verify_tree(self.directory, manifest)
        self.cold_bytes = sum(value['size'] for value in manifest['files'].values())
        self.bootstrap = BOOTSTRAP

    def request(self):
        return {'binding': self.binding, 'directory': str(self.directory)}

    def validate_response(self, response):
        if self.control is not None:
            from .study_process_control import validate_observation
            controls = response.get('process_control')
            require(type(controls) is dict and set(controls) == {'before', 'after'},
                    'Both native study process-control observations required')
            for value in controls.values():
                validate_observation(value)
        require(response['native_binding'] == digest(self.binding), 'Native study input identity differs')
        engines = response['draw_engines']
        require(type(engines) is list and len(engines) <= 128, 'Bounded native engine observations required')
        for value in engines:
            require(type(value) is dict and set(value) == {'length', 'native'}
                    and type(value['native']) is bool, 'Exact native engine observation required')
            integer(value['length'], 'Native observed mean length', 1)
        for key in ('environment_before', 'environment'):
            require(current(response[key], self.binding['runtime_id'], self.binding['runtime_manifest'],
                            self.directory, self.binding['host_images']), 'Native study environment is not current')
        return True


def child_entry(request_path):
    request_path = Path(request_path)
    directory = request_path.parent
    request = decode(request_path.read_bytes())
    fields = {'payload', 'manifest', 'world', 'footprint', 'verify', 'stream_limit', 'native'}
    controlled = 'process_control' in request
    if controlled:fields.add('process_control')
    require(set(request) == fields,
            'Exact native study child request required')
    expected = request['footprint']
    source = source_bundle()
    require(footprint(source) == expected, 'Retained native study source differs')
    if controlled:
        from .study_process_control import observe_control
        control_before = observe_control(request['process_control'])
    selected = ParentContext(source, request['native'])
    sys.path.insert(1, str(selected.directory))
    numpy = importlib.import_module('numpy')
    core = importlib.import_module('_trf_stationary_native')
    require(core.implementation_info() == INFO, 'Selected native kernel ABI differs')
    before = environment(expected, _native=selected.context)
    raw = (directory / 'cases.jsonl').read_bytes()
    payload = request['payload']
    require({'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)} == payload['case_blob'],
            'Retained native study input cases differ')
    cases = [decode(line) for line in raw.splitlines()]
    require(len(cases) <= 100000, 'Native study case count exceeds its envelope')
    factory = make_draw_factory(core, numpy)
    engines = []
    def selected_factory(rng, rows, length):
        initial = rng.getstate()
        engine = factory(rng, rows, length)
        require(rng.getstate() == initial, 'Native engine selection consumed caller randomness')
        engines.append({'length': length, 'native': engine is not None})
        return engine
    verify = request['verify']
    path = directory / ('expected-stream.jsonl.gz' if verify is not None else 'stream.jsonl.gz')
    with path.open('rb' if verify is not None else 'xb') as stream:
        encoded = EncodedStream(stream, encoded_limit=request['stream_limit'], verify=verify is not None)
        def retain(record):
            encoded.write((canonical(record) + '\n').encode())
        def retain_draw(draw):
            encoded.write(b'{"kind":"draw","value":' + draw + b'}\n')
        result = calculate_world(payload, request['manifest'], request['world'], cases, retain,
                                 retain_draw_bytes=retain_draw, retain_family_draw_bytes=encoded.write,
                                 _draw_factory=selected_factory)
        # Keep complete available computations even if post-use validation or
        # replay later fails. Failure authority is settled by the owning caller.
        write_file(directory / 'computed-result.json', canonical(result).encode())
        encoding = encoded.finish()
        if verify is not None:
            require(digest(result) == verify, 'Native study result replay differs')
    if controlled:
        control_after = observe_control(request['process_control'])
    after = environment(expected, _native=selected.context)
    require(footprint(source_bundle()) == expected, 'Native study source changed during computation')
    raw = path.read_bytes()
    print(canonical({'result': result if verify is None else {'verified_result_hash': verify},
                     'stream_blob': {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)},
                     'stream_encoding': encoding, 'request_hash': digest(request), 'footprint': expected,
                     'environment_before': before, 'environment': after,
                     **({'process_control': {'before': control_before, 'after': control_after}}
                        if controlled else {}),
                     'native_binding': digest(selected.binding), 'draw_engines': engines}), flush=True)
