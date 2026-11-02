"""Operator-owned qualification of one pinned native implementation profile."""
import hashlib
import math
from pathlib import Path
import re
import time
import uuid

from .binding import require
from .certification import _runtime_identity
from .codec import canonical, decode, digest, integer, text
from .errors import Conflict, Denied
from .evaluation_plans import footprint
from .native_runtime import NativeRuntimes, _identity
from . import native_qualification_profile as profile


SOURCE = 'native-qualification-source/1'
INPUT = 'native-runtime-qualification-input/1'
RESULT = 'native-runtime-qualification/1'
AUTHORITY = 'native_bootstrap_conformance_only'
SOURCE_AUTHORITY = 'retained_source_not_certified'
LIMITS = {'max_compute_ms': 300000, 'max_storage_bytes': 256 * 1024 * 1024}
META = 1024 * 1024


class NativeQualifications:
    def __init__(self, broker):
        self.broker = broker
        self.runtimes = NativeRuntimes(broker)

    def _owned(self, identity, schema):
        item = self.broker._artifact(text(identity, 'Native qualification identity'))
        body = item.get('body')
        authority = SOURCE_AUTHORITY if schema == SOURCE else AUTHORITY
        if (item['creator'] != item['origin'] or item['creator'] != 'controller'
                or item['data_class'] != 'operations' or item['authority'] != authority
                or type(body) is not dict or body.get('schema') != schema
                or body.get('profile') != profile.PROFILE):
            raise Denied('Owned native qualification record required')
        return item

    def _source(self, identity):
        package = self._owned(identity, SOURCE)
        body = package['body']
        files = body['files']
        allowed = set(profile.FIXED) | {profile.LOOP_FILE}
        require(type(files) is dict and 1 <= len(files) <= 128 and all(
            type(name) is str and (name in allowed or
            re.fullmatch(r'trading_researcher/[A-Za-z_][A-Za-z0-9_]*\.py', name)) for name in files),
            'Bounded native qualification source paths required')
        total = 0
        for value in files.values():
            require(type(value) is dict and set(value) == {'sha256', 'size'})
            from .storage import blob_identity
            blob_identity(value['sha256'])
            integer(value['size'], 'Native source size')
            total += value['size']
        require(total <= 16 * META and package['source_refs'] == [] and package['exposure'] == []
                and set(package['blob_refs']) == {value['sha256'] for value in files.values()}
                and body['bootstrap_sha256'] == hashlib.sha256(profile.BOOTSTRAP.encode()).hexdigest(),
                'Native qualification source closure differs')
        source = {name: self.broker._read_blob_bytes(value['sha256']) for name, value in files.items()}
        require(footprint(source) == body['footprint'] and all(
            len(source[name]) == value['size'] for name, value in files.items()), 'Native qualification source bytes differ')
        return source

    def _input(self, identity):
        item = self._owned(identity, INPUT)
        body = item['body']
        runtime = self.runtimes._package(body['runtime_id'])
        package = self._owned(body['source_package_id'], SOURCE)
        refs = sorted([runtime['id'], package['id']])
        require(body['request']['runtime_id'] == runtime['id']
                and body['runtime_manifest'] == runtime['body']['manifest']
                and body['source_footprint'] == package['body']['footprint']
                and item['source_refs'] == refs and item['blob_refs'] == []
                and set(item['exposure']) == set(refs) | set(runtime['exposure']) | set(package['exposure'])
                and body['limits'] == LIMITS and body['scientific_readiness'] is False,
                'Native qualification input closure differs')
        return item

    def _certificate(self, identity):
        item = self._owned(identity, RESULT)
        body = item['body']
        capsule = self._input(body['input_id'])
        original = capsule['body']
        require(item['source_refs'] == [capsule['id']]
                and set(item['exposure']) == set(capsule['exposure']) | {capsule['id']}
                and body['request'] == original['request'] and body['attempt_id'] == original['attempt_id']
                and body['runtime_id'] == original['runtime_id']
                and body['source_package_id'] == original['source_package_id']
                and body['status'] in ('CERTIFIED', 'CERTIFICATION_GAP')
                and body['scientific_readiness'] is False
                and set(item['blob_refs']) == {value['sha256'] for value in body['output_blobs'].values()},
                'Native qualification certificate closure differs')
        return item

    def _inputs(self):
        for row in self.broker._db.execute(
                "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?", (INPUT,)):
            yield self._input(row[0])

    def _result(self, capsule):
        records = []
        for row in self.broker._db.execute(
                "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=? "
                "AND json_extract(envelope,'$.body.input_id')=?", (RESULT, capsule['id'])):
            records.append(self._certificate(row[0]))
        require(len(records) <= 1, 'Native qualification has conflicting completions')
        return records[0] if records else None

    def _verify_outputs(self, certificate):
        outputs = certificate['body']['output_blobs']
        require(type(outputs) is dict and len(outputs) <= 256, 'Bounded retained qualifier outputs required')
        for value in outputs.values():
            require(type(value) is dict and set(value) == {'sha256', 'size'})
            integer(value['size'], 'Retained qualifier output size')
            raw = self.broker._read_blob_bytes(value['sha256'])
            require(len(raw) == value['size'], 'Retained qualifier output descriptor differs')

    def _prior(self, request):
        for capsule in self._inputs():
            if capsule['body']['request']['key'] != request['key']:
                continue
            if capsule['body']['request'] != request:
                raise Conflict('Native qualification key already binds different inputs')
            result = self._result(capsule)
            if result is None:
                raise Conflict('Native qualification was already started; inspect the retained input ' + capsule['id'])
            return result
        return None

    def _retain_source(self, source, files):
        broker = self.broker
        expected = footprint(source)
        require(1 <= len(files) <= 128 and sum(map(len, source.values())) <= 16 * META,
                'Native qualification source exceeds the existing source envelope')
        for row in broker._db.execute(
                "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?", (SOURCE,)):
            package = self._owned(row[0], SOURCE)
            if package['body']['footprint'] == expected:
                require(self._source(package['id']) == source)
                broker._require_usable_dependencies(package['id'])
                return package
        for value in files.values():
            broker._register_blob(value)
        return broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
            'data_class': 'operations', 'source_refs': [], 'exposure': [],
            'blob_refs': sorted({value['sha256'] for value in files.values()}), 'authority': SOURCE_AUTHORITY,
            'body': {'schema': SOURCE, 'profile': profile.PROFILE, 'created_at': broker._now(),
                     'files': files, 'footprint': expected,
                     'bootstrap_sha256': hashlib.sha256(profile.BOOTSTRAP.encode()).hexdigest()}})

    def qualify(self, token, args):
        broker = self.broker
        started = time.monotonic()
        with broker._mutex:
            actor = broker._binding_owner(token)
            require(set(args) == {'key', 'runtime_id'}, 'Exact native qualification request required')
            request = decode(canonical(args))
            text(request['key'], 'Native qualification key')
            text(request['runtime_id'], 'Native runtime identity')
            previous = self._prior(request)
            if previous is not None:
                return previous
            runtime = self.runtimes._package(request['runtime_id'])
            broker._require_usable_dependencies(runtime['id'])
            source = profile.capture_source()
            initial = runtime['body']['archive']['size'] + 2 * sum(map(len, source.values())) + META
            require(initial <= LIMITS['max_storage_bytes'], 'Native qualification input retention exceeds its bound')
            hosts = profile.host_inputs(source)
            files = {name: broker._stage_blob_bytes(raw) for name, raw in source.items()}
        with broker._transaction():
            broker._binding_owner(token)
            previous = self._prior(request)
            if previous is not None:
                return previous
            broker._require_usable_dependencies(runtime['id'])
            package = self._retain_source(source, files)
            attempt = uuid.uuid4().hex
            refs = sorted([runtime['id'], package['id']])
            capsule = broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
                'data_class': 'operations', 'source_refs': refs,
                'exposure': sorted(set(refs) | set(runtime['exposure']) | set(package['exposure'])),
                'blob_refs': [], 'authority': AUTHORITY,
                'body': {'schema': INPUT, 'profile': profile.PROFILE, 'created_at': broker._now(),
                         'request': request, 'attempt_id': attempt, 'runtime_id': runtime['id'],
                         'runtime_manifest': runtime['body']['manifest'], 'source_package_id': package['id'],
                         'source_footprint': footprint(source), 'runtime_identity': _runtime_identity(),
                         'host_images': hosts, 'limits': dict(LIMITS), 'initial_storage_bytes': initial,
                         'scientific_readiness': False}})
            broker._event(actor['name'], 'native_runtime_qualification_input', input_id=capsule['id'], request_hash=digest(request))
            broker._event('controller', 'bound_computation_started', attempt_id=attempt,
                          kind='native_runtime_qualification', input_ref=capsule['id'], retained_input_id=capsule['id'])
        def remaining():
            seconds = LIMITS['max_compute_ms'] / 1000 - (time.monotonic() - started)
            require(seconds > 0, 'Native qualification exhausted its compute reservation')
            return seconds
        meter = {'materialized_bytes': 0, 'accounting_complete': True}
        outputs, failures = [], []
        report = None
        cancelled = None
        try:
            remaining()
            profile.validate_runtime(runtime)
            directory = self.runtimes._materialize(runtime['id'], meter)
            remaining()
            report = profile.execute(source, capsule, directory, remaining, meter, outputs)
            profile.validate_report(report, source, capsule, directory)
            require(profile.capture_source() == source, 'Qualification source changed during execution')
            with broker._mutex:
                require(self._source(package['id']) == source, 'Retained qualification source changed during execution')
                self.runtimes._raw(runtime)
            require(meter['accounting_complete'], 'Native qualification usage is unknown')
            remaining()
        except BaseException as exc:
            failures.append({'type': type(exc).__name__, 'message': str(exc)[:2000]})
            if not isinstance(exc, Exception):
                cancelled = exc
        with broker._mutex:
            descriptors = {name: broker._stage_blob_bytes(raw) for name, raw in outputs}
            compute = math.ceil((time.monotonic() - started) * 1000)
            storage = initial + meter['materialized_bytes'] + sum(len(raw) for _, raw in outputs) + META
            known = meter['accounting_complete']
            if not known:
                compute = max(compute, LIMITS['max_compute_ms'])
                storage = max(storage, LIMITS['max_storage_bytes'])
            if compute > LIMITS['max_compute_ms'] or storage > LIMITS['max_storage_bytes']:
                failures.append({'type': 'ResourceOverrun', 'message': 'Native qualification exceeded its frozen reservation'})
            settlement = {'compute_ms': compute, 'storage_bytes': storage, 'usage_known': known}
            with broker._transaction():
                broker._binding_owner(token)
                require(self._result(capsule) is None, 'Native qualification was already settled')
                try:
                    broker._require_usable_dependencies(capsule['id'])
                    require(profile.capture_source() == source, 'Native qualification source changed before commit')
                except Exception as exc:
                    failures.append({'type': type(exc).__name__, 'message': str(exc)[:2000]})
                for value in descriptors.values():
                    broker._register_blob(value)
                status = 'CERTIFICATION_GAP' if failures else 'CERTIFIED'
                certificate = broker._save_artifact({'version': 'local-artifact/1', 'creator': 'controller', 'origin': 'controller',
                    'data_class': 'operations', 'source_refs': [capsule['id']],
                    'exposure': sorted(set(capsule['exposure']) | {capsule['id']}),
                    'blob_refs': sorted({value['sha256'] for value in descriptors.values()}), 'authority': AUTHORITY,
                    'body': {'schema': RESULT, 'profile': profile.PROFILE, 'created_at': broker._now(),
                             'request': request, 'input_id': capsule['id'], 'attempt_id': attempt,
                             'runtime_id': runtime['id'], 'source_package_id': package['id'], 'status': status,
                             'report': report, 'settlement': settlement, 'failure': failures[-1] if failures else None,
                             'failures': failures, 'output_blobs': descriptors, 'scientific_readiness': False}})
                broker._event('controller', 'native_runtime_qualified', input_id=capsule['id'],
                              artifact_id=certificate['id'], attempt_id=attempt, status=status)
                broker._event('controller', 'bound_computation_checked', attempt_id=attempt,
                              artifact_id=certificate['id'], status=status)
        if cancelled is not None:
            raise cancelled
        return certificate

    def inspect(self, token, args):
        broker = self.broker
        with broker._mutex:
            broker._binding_owner(token)
            require(set(args) == {'qualification_id'}, 'Exact qualification inspection required')
            item = broker._artifact(text(args['qualification_id'], 'Native qualification identity'))
            if type(item.get('body')) is dict and item['body'].get('schema') == RESULT:
                certificate = self._certificate(item['id'])
                capsule = self._input(certificate['body']['input_id'])
            else:
                capsule = self._input(item['id'])
                certificate = self._result(capsule)
            attempts = [value for value in broker._bound_attempts() if value['input_ref'] == capsule['id']]
            status = ('RUNNING' if attempts and attempts[-1]['state'] == 'STARTED' else 'INTERRUPTED')
            if certificate is not None:
                status = certificate['body']['status']
                if status == 'CERTIFIED':
                    try:
                        broker._require_usable_dependencies(certificate['id'])
                        self._verify_outputs(certificate)
                        source = self._source(capsule['body']['source_package_id'])
                        runtime = self.runtimes._package(capsule['body']['runtime_id'])
                        profile.validate_runtime(runtime)
                        raw = self.runtimes._raw(runtime)
                        directory = broker.directory / 'native-runtime-cache' / _identity(raw, runtime['body']['manifest'])
                        require(source == profile.capture_source()
                                and capsule['body']['runtime_identity'] == _runtime_identity()
                                and capsule['body']['host_images'] == profile.host_inputs(source))
                        profile.validate_report(certificate['body']['report'], source, capsule, directory)
                        status = 'CURRENT'
                    except Exception:
                        dependency = broker._dependency_use(certificate['id'])
                        status = ('INVALIDATED_BY_DEPENDENCY' if dependency['status'] == 'INVALIDATED_BY_DEPENDENCY'
                                  else 'STALE')
            settlement = certificate['body']['settlement'] if certificate else (
                {'compute_ms': LIMITS['max_compute_ms'], 'storage_bytes': LIMITS['max_storage_bytes'],
                 'usage_known': False} if status == 'INTERRUPTED' else None)
            return {'input_id': capsule['id'], 'certificate_id': certificate['id'] if certificate else None,
                    'status': status, 'attempts': attempts, 'settlement': settlement, 'scientific_readiness': False}
