"""Opt-in native development studies over the existing reserved lifecycle."""
import hashlib

from .binding import require
from .codec import canonical, digest, text
from .data_use import prior_knowledge, protected_knowledge_gaps
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .family_study_runs import FamilyStudies
from .native_qualification import NativeQualifications
from .native_qualification_profile import PROFILE
from .native_runtime import NativeRuntimes, _identity
from .native_study_pipeline import SCHEMA, BOOTSTRAP
from .study_runs import InformationStudies, LOADED_SOURCE
from . import study_runs


def _project_source(qualified):
    return {name: raw for name, raw in qualified['source'].items()
            if name.startswith('trading_researcher/') and name.endswith('.py')}


class NativeStudyInputs:
    _study_request_fields = InformationStudies._study_request_fields | {'native_qualification_id'}

    def __init__(self, broker):
        self.broker = broker

    def __getattr__(self, name):
        return getattr(self.broker, name)

    def _study_identity(self, request):
        # A repeated implementation certificate cannot reset the same study's
        # world/attempt/resource inventory. Its original binding stays immutable.
        return digest({key: value for key, value in request.items()
                       if key not in ('key', 'native_qualification_id')})

    def _study_existing_request(self, existing, request):
        qualified = self._qualified(request)
        incoming = self._binding(qualified)
        original = existing['body']['native_binding']
        fields = set(incoming) - {'qualification_id', 'runtime_id'}
        if any(incoming[key] != original[key] for key in fields):
            raise Conflict('Native study already binds its original source/runtime inputs')

    def _qualified(self, request, *, runtime_directory=None):
        identity = text(request['native_qualification_id'], 'Native study qualification')
        qualified = NativeQualifications(self.broker)._require_inputs(identity, runtime_directory=runtime_directory)
        if protected_knowledge_gaps(prior_knowledge(self.broker, qualified['certificate'])):
            raise Denied('Native runtime ancestry contains protected, operational or unresolved knowledge')
        source = _project_source(qualified)
        require(footprint(source) == LOADED_SOURCE and source == source_bundle(),
                'Native study host/project source differs from its qualification; restart and requalify')
        return qualified

    def _binding(self, qualified):
        return {'schema': SCHEMA, 'profile': PROFILE, 'qualification_id': qualified['certificate']['id'],
                'runtime_id': qualified['runtime']['id'], 'runtime_manifest': qualified['runtime']['body']['manifest'],
                'host_images': qualified['capsule']['body']['host_images'],
                'source_footprint': footprint(_project_source(qualified))}

    def _study_inputs(self, actor, request):
        payload, manifest, refs, exposure = super()._study_inputs(actor, request)
        qualified = self._qualified(request)
        certificate = qualified['certificate']
        refs = sorted(set(refs) | {certificate['id']})
        exposure = sorted(set(exposure) | set(certificate['exposure']) | {certificate['id']})
        return payload, manifest, refs, exposure

    def _study_capture_source(self, request):
        return _project_source(self._qualified(request))

    def _study_extra_input(self, request, manifest):
        qualified = self._qualified(request)
        source = _project_source(qualified)
        common = set(footprint(source).values())
        common.add(self._artifact(request['execution_id'])['body']['result']['case_blob']['sha256'])
        descriptors = [qualified['runtime']['body']['archive'],
                       *qualified['source_package']['body']['files'].values(),
                       *qualified['certificate']['body']['output_blobs'].values()]
        sizes = {}
        for value in descriptors:
            checksum, size = value['sha256'], value['size']
            require(checksum not in sizes or sizes[checksum] == size, 'Native input descriptor sizes conflict')
            sizes[checksum] = size
        metadata = sum(len(canonical({key: value for key, value in qualified[name].items()
                                     if key != 'id'}).encode()) for name in
                       ('certificate', 'capsule', 'source_package', 'runtime', 'archive_source'))
        retained = metadata + sum(size for checksum, size in sizes.items() if checksum not in common)
        return {**super()._study_extra_input(request, manifest), 'native_binding': self._binding(qualified),
                'native_bootstrap_sha256': hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),
                'native_input_storage_bytes': retained}

    def _study_initial_storage(self, source, payload, extra):
        return super()._study_initial_storage(source, payload, extra) + extra['native_input_storage_bytes']

    def _study_before_execute(self, study):
        super()._study_before_execute(study)
        qualified = self._qualified(study['body']['request'])
        require(study['body']['native_binding'] == self._binding(qualified)
                and study['body']['native_bootstrap_sha256'] == hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),
                'Native study retained runtime or entrypoint differs')

    def _load_study_source(self, study):
        require(study['body']['native_bootstrap_sha256'] == hashlib.sha256(BOOTSTRAP.encode()).hexdigest(),
                'Native study retained entrypoint differs')
        return super()._load_study_source(study)

    def _execute_study_attempt(self, study, source, payload, manifest, world, cases, remaining, meter, outputs):
        request = study['body']['request']
        qualified = self._qualified(request)
        remaining()
        cold_bytes = sum(value['size'] for value in qualified['runtime']['body']['manifest']['files'].values())
        study_runs.attempt_stream_limit(source, manifest, cases, runtime_bytes=cold_bytes)
        directory = NativeRuntimes(self.broker)._materialize(qualified['runtime']['id'], meter)
        remaining()
        self._qualified(request, runtime_directory=directory)
        selected = {'binding': study['body']['native_binding'], 'directory': str(directory)}
        return study_runs.execute_attempt(source, payload, manifest, world, cases, remaining,
                                          meter, outputs, _native=selected)

    def _study_after_execute(self, study):
        # The common caller retains the returned result/proofs before checking
        # post-use currency, so revocation cannot discard available computation.
        runtime = NativeRuntimes(self.broker)._package(study['body']['native_binding']['runtime_id'])
        body = runtime['body']
        directory = self.broker.directory / 'native-runtime-cache' / _identity(
            self._read_blob_bytes(body['archive']['sha256']), body['manifest'])
        self._qualified(study['body']['request'], runtime_directory=directory)


class NativeInformationStudies(NativeStudyInputs, InformationStudies):
    _study_input_schema = 'native-information-study-input/1'
    _study_result_schema = 'native-information-study-attempt/1'
    _study_authority = 'native_development_study_not_scientific_admission'


class NativeFamilyStudies(NativeStudyInputs, FamilyStudies):
    _study_input_schema = 'native-family-study-input/1'
    _study_result_schema = 'native-family-study-attempt/1'
    _study_authority = 'native_development_joint_family_study_not_scientific_admission'
