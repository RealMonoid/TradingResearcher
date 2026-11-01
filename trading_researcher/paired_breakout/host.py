"""Owned second-original composition and execution on the frozen paired engine.

Only the separately qualified composition/audit profile is new. This adapter
adds no provider dispatch, spending grant, source access or scientific meaning.
Existing first-original compilation, feedback and revocation remain inherited.
"""
import hashlib
from pathlib import Path
import shutil
import tempfile
import time

from ..binding import hashes, require
from ..certification import _environment_current
from ..codec import canonical, digest, text
from ..feedback.paired import PairedFeedbackBroker
from ..paired_computation import AUTHORITY
from .. import paired_runtime
from . import composition, runtime

ROOT = Path(__file__).resolve().parents[2]
EXECUTION_PROFILE = 'paired-breakout-development/1'
HOST_FILE = 'trading_researcher/paired_breakout/host.py'
LOADED_SELF = hashlib.sha256((ROOT / HOST_FILE).read_bytes()).hexdigest()
LOADED_RUNTIME = hashes(runtime.read_bundle())
SCENARIOS = 299
CHECKED_CASES = 8970


class BreakoutBroker(PairedFeedbackBroker):
    """Optional operator entry point; ordinary Broker capabilities are unchanged."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._breakout_loaded_sources = self._breakout_source_identity()

    def _breakout_source_identity(self):
        own = hashlib.sha256((ROOT / HOST_FILE).read_bytes()).hexdigest()
        bundle = hashes(runtime.read_bundle())
        require(own == LOADED_SELF and bundle == LOADED_RUNTIME,
                'Breakout installed sources changed; restart and requalify')
        result = {**self._paired_source_identity(), **bundle, HOST_FILE: own,
            'trading_researcher/feedback/paired.py': self._feedback_source_current()}
        if hasattr(self, '_breakout_loaded_sources'):
            require(result == self._breakout_loaded_sources, 'Breakout loaded source identity changed')
        return result

    def _breakout_retain_package(self, bundle):
        require(set(bundle) == set(runtime.FILES) and hashes(bundle) == hashes(runtime.read_bundle())
                and sum(map(len, bundle.values())) <= 16*1024*1024)
        files = {name: self._stage_blob_bytes(raw) for name, raw in sorted(bundle.items())}
        with self._transaction():
            for descriptor in files.values(): self._register_blob(descriptor)
            return self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'operations', 'source_refs': [], 'exposure': [],
                'blob_refs': sorted({item['sha256'] for item in files.values()}),
                'authority': 'retained_source_not_certified', 'body': {
                    'schema': 'paired-source-package/1', 'profile': composition.PROFILE,
                    'created_at': self._now(), 'files': files, 'footprint': hashes(bundle),
                    'bootstrap_sha256': hashlib.sha256(runtime.BOOTSTRAP.encode()).hexdigest()}})

    def _breakout_package(self, identity):
        item = self._artifact(text(identity, 'breakout source package'))
        body = item['body']
        require(item['creator'] == item['origin'] == 'controller'
                and item['data_class'] == 'operations' and item['authority'] == 'retained_source_not_certified'
                and type(body) is dict and set(body) == {
                    'schema', 'profile', 'created_at', 'files', 'footprint', 'bootstrap_sha256'}
                and body['schema'] == 'paired-source-package/1' and body['profile'] == composition.PROFILE
                and type(body['files']) is dict and set(body['files']) == set(runtime.FILES),
                'Owned exact breakout retained package required')
        self._require_usable_dependencies(identity)
        require(body['bootstrap_sha256'] == hashlib.sha256(runtime.BOOTSTRAP.encode()).hexdigest())
        bundle, size = {}, 0
        for name, descriptor in body['files'].items():
            require(type(descriptor) is dict and set(descriptor) == {'sha256', 'size'}
                    and type(descriptor['size']) is int and descriptor['size'] >= 0)
            size += descriptor['size']
            require(size <= 16*1024*1024, 'Breakout package exceeds its retained-source bound')
            raw = self._read_blob_bytes(descriptor['sha256'])
            require(len(raw) == descriptor['size'])
            bundle[name] = raw
        require(hashes(bundle) == body['footprint']
                and set(item['blob_refs']) == {value['sha256'] for value in body['files'].values()})
        return bundle

    def _breakout_compiled(self, identity):
        self._breakout_source_identity()
        compiled, dependencies, payload = self._paired_compiled(identity)
        require(dependencies['formalization']['body']['idea_id'] == composition.IDEA_ID,
                'Breakout composition requires its exact retained original idea')
        require(composition.original_compilation(payload) == compiled['body']['compilation'])
        return compiled, dependencies, payload

    def certify_paired_composition(self, token, *, compiled_id):
        with self._mutex:
            self._binding_owner(token)
            _, dependencies, _ = self._paired_compiled(compiled_id)
            breakout = dependencies['formalization']['body']['idea_id'] == composition.IDEA_ID
        if not breakout:
            return super().certify_paired_composition(token, compiled_id=compiled_id)
        return self.certify_breakout_composition(token, compiled_id=compiled_id)

    def certify_breakout_composition(self, token, *, compiled_id):
        with self._mutex:
            self._binding_owner(token)
            compiled, _, payload = self._breakout_compiled(compiled_id)
            source_identity = self._breakout_source_identity()
            bundle = runtime.read_bundle()
        package = self._breakout_retain_package(bundle)
        attempt = self._bound_start('paired_breakout_composition', compiled_id)
        report, error = None, None
        try:
            with tempfile.TemporaryDirectory(prefix='trf-breakout-composition-') as directory:
                report = runtime.run_child(bundle, 'composition', payload, directory)
            self._breakout_report(report, payload, bundle)
        except Exception as exc:
            error = {'type': type(exc).__name__, 'reason': str(exc)}
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            self._binding_owner(token)
            if error is None:
                try:
                    self._breakout_compiled(compiled_id)
                    require(self._breakout_source_identity() == source_identity
                            and hashes(self._breakout_package(package['id'])) == hashes(bundle))
                except Exception as exc:
                    error = {'type': type(exc).__name__, 'reason': str(exc)}
            record = self._paired_save({'schema': 'paired-composition-certificate/1',
                'profile': composition.PROFILE, 'created_at': self._now(), 'attempt_id': attempt,
                'compiled_id': compiled_id, 'candidate_hash': digest(payload['candidate']),
                'source_package_id': package['id'], 'host_sources': source_identity,
                'status': 'CERTIFIED' if error is None else 'COMPOSITION_GAP', 'error': error,
                'report': report, 'scientific_readiness': False}, [compiled_id, package['id']])
            self._event('controller', 'bound_computation_checked', attempt_id=attempt,
                artifact_id=record['id'], status=record['body']['status'])
            return record

    def _breakout_report(self, report, payload, bundle):
        require(type(report) is dict and report.get('mode') == 'composition'
                and report.get('request_hash') == digest(payload) and report.get('footprint') == hashes(bundle)
                and _environment_current(report.get('environment')), 'Breakout child binding differs')
        result = report['result']
        require(result['schema'] == 'paired-breakout-composition-result/1'
                and result['profile'] == composition.PROFILE and result['idea_id'] == composition.IDEA_ID
                and result['candidate_hash'] == digest(payload['candidate'])
                and result['oracle_sha256'] == composition.ORACLE_SHA256
                and result['scenario_count'] == SCENARIOS and result['checked_cases'] == CHECKED_CASES
                and result['scientific_readiness'] is False and len(result['scenarios']) == SCENARIOS
                and len({item['name'] for item in result['scenarios']}) == SCENARIOS
                and all(item['checked_cases'] == composition.SYNTHETIC_BARS for item in result['scenarios']),
                'The complete independently fixed breakout inventory must pass')

    def _paired_composition_status(self, identity, compiled):
        item = self._artifact(identity)
        if item['body'].get('profile') != composition.PROFILE:
            return super()._paired_composition_status(identity, compiled)
        return self._breakout_composition_status(identity, compiled)

    def _breakout_composition_status(self, identity, compiled):
        source_identity = self._breakout_source_identity()
        item = self._artifact(text(identity, 'breakout composition certificate'))
        body = item['body']
        require(item['creator'] == item['origin'] == 'controller' and item['data_class'] == 'development'
                and item['authority'] == AUTHORITY and type(body) is dict
                and body.get('schema') == 'paired-composition-certificate/1'
                and body.get('profile') == composition.PROFILE and body.get('status') == 'CERTIFIED'
                and body.get('error') is None and body.get('compiled_id') == compiled['id']
                and body.get('candidate_hash') == compiled['body']['compilation']['candidate_hash']
                and body.get('host_sources') == source_identity and body.get('scientific_readiness') is False,
                'Current candidate-bound breakout composition required')
        self._require_usable_dependencies(identity)
        _, _, payload = self._breakout_compiled(compiled['id'])
        bundle = self._breakout_package(body['source_package_id'])
        require(hashes(bundle) == hashes(runtime.read_bundle()), 'Breakout retained source is stale')
        require({compiled['id'], body['source_package_id']} <= set(item['source_refs']))
        self._breakout_report(body['report'], payload, bundle)
        return item

    def inspect_breakout_composition(self, token, *, composition_id):
        with self._mutex:
            self._binding_owner(token)
            record = self._artifact(composition_id)
            compiled, _, _ = self._breakout_compiled(record['body']['compiled_id'])
            self._breakout_composition_status(composition_id, compiled)
            return {'composition_id': composition_id, 'status': 'CURRENT', 'scientific_readiness': False}

    def _technical_dependencies(self, artifact):
        body = artifact['body']
        if type(body) is dict and artifact['creator'] == artifact['origin'] == 'controller':
            if body.get('schema') == 'paired-composition-certificate/1' and body.get('profile') == composition.PROFILE:
                return [body['compiled_id'], body['source_package_id']]
            if body.get('schema') in ('paired-reference-execution/1', 'paired-execution-input/1') and body.get('profile') == EXECUTION_PROFILE:
                return [body['compiled_id'], body['composition_id']]
        return super()._technical_dependencies(artifact)

    def execute_paired(self, token, *, compiled_id, meaning_assessment_id, composition_id):
        with self._mutex:
            self._binding_owner(token)
            _, dependencies, _ = self._paired_compiled(compiled_id)
            breakout = dependencies['formalization']['body']['idea_id'] == composition.IDEA_ID
        if not breakout:
            return super().execute_paired(token, compiled_id=compiled_id,
                meaning_assessment_id=meaning_assessment_id, composition_id=composition_id)
        return self.execute_breakout(token, compiled_id=compiled_id,
            meaning_assessment_id=meaning_assessment_id, composition_id=composition_id)

    def execute_breakout(self, token, *, compiled_id, meaning_assessment_id, composition_id):
        started = time.monotonic()
        with self._mutex:
            actor = self._binding_owner(token)
            compiled, dependencies, payload = self._breakout_compiled(compiled_id)
            assessment = self._artifact(meaning_assessment_id)
            require(assessment['body']['formalization_id'] == compiled['body']['formalization_id'])
            meaning = self._inspect_meaning_review(actor, meaning_assessment_id)
            require(meaning['current'] and meaning['independent_semantic_review'] == 'SATISFIED')
            composition_record = self._breakout_composition_status(composition_id, compiled)
            bundle = self._paired_package(compiled['body']['source_package_id'])
            require(hashes(bundle) == hashes(dependencies['bundle']))
            audit_bundle = self._breakout_package(composition_record['body']['source_package_id'])
            source_identity = self._breakout_source_identity()
        attempt = self._bound_start('paired_breakout_execution', compiled_id)
        report, verification, audit, descriptor, error = None, None, None, None, None
        try:
            selection = compiled['body']['compilation']['row_window']
            loaded = self._load_reference_data(compiled['body']['data_snapshot_id'],
                selection['start'], selection['end'], selection['instruments'])
            require(digest(loaded['catalog']) == digest(payload['catalog']))
            with tempfile.TemporaryDirectory(prefix='trf-breakout-execute-') as temporary:
                directory = Path(temporary)
                with (directory / 'rows.jsonl').open('xb') as stream:
                    size = 0
                    for row in loaded['rows']:
                        raw = (canonical(row) + '\n').encode()
                        size += len(raw)
                        require(size <= paired_runtime.MAX_STREAM)
                        stream.write(raw)
                execution_input = {'compilation_input': payload,
                    'compilation_hash': digest(compiled['body']['compilation']),
                    'rows': paired_runtime._stream(directory / 'rows.jsonl')}
                with self._transaction():
                    capsule = self._paired_save({'schema': 'paired-execution-input/1',
                        'profile': EXECUTION_PROFILE, 'created_at': self._now(), 'compiled_id': compiled_id,
                        'composition_id': composition_id, 'input': execution_input,
                        'scientific_readiness': False}, [compiled_id, meaning_assessment_id, composition_id])
                report = paired_runtime.run_child(bundle, 'execute', execution_input, directory,
                    timeout=int(1800 - (time.monotonic() - started)))
                # Preserve the exact produced bytes even if replay subsequently
                # fails. Retention is not a successful verification or verdict.
                with (directory / 'cases.jsonl').open('rb') as stream:
                    descriptor = self._stage_blob_stream(stream)
                require(descriptor == report['result']['case_blob'])
                with tempfile.TemporaryDirectory(prefix='trf-breakout-replay-') as second:
                    for name in ('rows.jsonl', 'cases.jsonl'):
                        shutil.copyfile(directory / name, Path(second) / name)
                    verification = paired_runtime.run_child(bundle, 'verify', {
                        'execution_input': execution_input, 'result': report['result']}, second,
                        timeout=int(1800 - (time.monotonic() - started)))
                result = report['result']
                require(verification['result'] == {'schema': 'paired-case-verification/1',
                    'result_hash': digest(result), 'case_blob': result['case_blob'],
                    'checked_cases': result['report']['processed_case_count'], 'scientific_readiness': False})
                if result['report']['processing_complete']:
                    with tempfile.TemporaryDirectory(prefix='trf-breakout-audit-') as third:
                        for name in ('rows.jsonl', 'cases.jsonl'):
                            shutil.copyfile(directory / name, Path(third) / name)
                        audit = runtime.run_child(audit_bundle, 'audit', {
                            'execution_input': execution_input, 'result': result}, third,
                            timeout=int(1800 - (time.monotonic() - started)))
                    checked = audit['result']
                    require(checked['schema'] == 'paired-breakout-row-audit/1'
                        and checked['profile'] == composition.PROFILE and checked['idea_id'] == composition.IDEA_ID
                        and checked['candidate_hash'] == digest(payload['candidate'])
                        and checked['oracle_sha256'] == composition.ORACLE_SHA256
                        and checked['checked_cases'] == result['report']['processed_case_count']
                        and checked['observed_outcomes'] == sum(item['observed']
                            for item in result['report']['diagnostics']['condition_outcome_counts'].values())
                        and checked['scientific_readiness'] is False)
        except Exception as exc:
            error = {'type': type(exc).__name__, 'reason': str(exc)}
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            actor = self._binding_owner(token)
            if error is None:
                try:
                    self._breakout_compiled(compiled_id)
                    require(self._inspect_meaning_review(actor, meaning_assessment_id) == meaning
                            and self._breakout_source_identity() == source_identity)
                    self._breakout_composition_status(composition_id, compiled)
                except Exception as exc:
                    error = {'type': type(exc).__name__, 'reason': str(exc)}
            if descriptor is not None: self._register_blob(descriptor)
            refs = [compiled_id, meaning_assessment_id, composition_id]
            if 'capsule' in locals(): refs.append(capsule['id'])
            record = self._paired_save({'schema': 'paired-reference-execution/1', 'profile': EXECUTION_PROFILE,
                'created_at': self._now(), 'status': ('EXECUTION_GAP' if error is not None else
                    'DESCRIPTIVE_EXECUTION' if report['result']['report']['processing_complete'] else 'RESOURCE_STOP'),
                'attempt_id': attempt, 'error': error, 'compiled_id': compiled_id,
                'composition_id': composition_id, 'meaning_assessment_id': meaning_assessment_id,
                'data_snapshot_id': compiled['body']['data_snapshot_id'],
                'elapsed_ms': int(1000 * (time.monotonic() - started)), 'host_sources': source_identity,
                'result': report['result'] if report is not None else None,
                'environment': report['environment'] if report is not None else None,
                'verification': verification, 'independent_original_audit': audit,
                'scientific_readiness': False,
                'qualification': 'COMPUTED_UNCALIBRATED development calculation; no scientific classification or policy return.'},
                refs, blobs=[descriptor['sha256']] if descriptor is not None else [])
            self._event('controller', 'bound_computation_checked', attempt_id=attempt,
                artifact_id=record['id'], status=record['body']['status'])
            return record
