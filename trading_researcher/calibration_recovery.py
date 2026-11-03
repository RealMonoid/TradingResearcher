"""Host-local, source-bound recovery of one retained scalar final inventory.

The trusted finite adapter supplies operational authority. This owner has no RPC
or model entry point, creates no replacement study, and grants no scientific
authority. Original study resources and events remain untouched.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import re
import time
import math
import uuid

from .binding import require
from .certification import _environment_current, _runtime_identity
from .codec import canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .family_study_runs import FamilyCalibrationStudies
from . import family_study
from .study_runs import (execute_attempt, attempt_stream_limit,
                         LOADED_SOURCE as STUDY_LOADED_SOURCE)
from .study_resources import METADATA_BYTES


PROFILE = 'scalar-calibration-recovery/1'
INPUT = 'calibration-recovery-input/1'
SOURCE = 'calibration-recovery-source/1'
AMENDMENT = 'calibration-recovery-amendment/1'
RESULT = 'calibration-recovery-attempt/1'
GRANT = 'calibration-recovery-continuation/1'
AUTHORITY = 'bounded_scalar_recovery_not_scientific_admission'
BINDING = 'calibration-recovery-authority-binding/1'
BINDING_FIELDS = {'schema', 'calibration_id', 'registry_path', 'assessment_host',
                  'approval_path', 'approval_sha256', 'original_approval_path',
                  'original_approval_sha256'}
TERMS = {'additional_attempts_for_named_failed_world': 1,
         'attempt_compute_ms_for_retry_and_remaining_original_worlds': 600000,
         'other_worlds_max_attempts': 1, 'attempt_storage_bytes': 268435456,
         'aggregate_compute_ms': 648000000,
         'aggregate_logical_bytes': 107374182400, 'additional_grants_max': 179}
ATTEMPT_MS = TERMS['attempt_compute_ms_for_retry_and_remaining_original_worlds']
ATTEMPT_BYTES = TERMS['attempt_storage_bytes']
EVENTS = {'calibration_recovery_setup_reserved', 'calibration_recovery_setup_settled',
          'calibration_recovery_amended', 'calibration_recovery_reserved',
          'calibration_recovery_settled', 'calibration_recovery_continued'}
OWNERS = ('study_runs.py', 'study_resources.py', 'calibration_runs.py',
          'family_study_runs.py', 'family_study.py', 'calibration_study.py',
          'information_study.py', 'study_pipeline.py', 'family_pipeline.py',
          'study_stream.py', 'codec.py', 'evaluation_policy.py',
          'stationary_bootstrap.py', 'population_models.py', 'family_models.py',
          'binance_normalize.py', 'certification.py', 'evaluation_plans.py')
LOADED_SELF = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
LOADED_SOURCE = footprint(source_bundle())


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _path(value):
    text(value, 'owned absolute path')
    path = Path(value)
    require(path.is_absolute(), 'An absolute owned path is required')
    for node in (path, *path.parents):
        require(not node.is_symlink() and not node.is_junction(),
                'Linked recovery custody paths are unsupported')
    require(path.resolve() == path, 'Recovery custody path must be resolved')
    return path


def _descriptors(files):
    return {name: {'sha256': _sha(raw), 'size': len(raw)} for name, raw in files.items()}


def _package(files):
    require(type(files) is dict and 1 <= len(files) <= 128,
            'A complete bounded source bundle is required')
    require(all(re.fullmatch(r'trading_researcher/[A-Za-z_][A-Za-z0-9_]*\.py', name)
                and type(raw) is bytes for name, raw in files.items()),
            'Only the original flat Python package paths are supported')
    require(sum(map(len, files.values())) <= 16 * 1024 * 1024,
            'Recovery source bundle exceeds the existing source envelope')
    return files


def _failure(exc):
    return {'type': type(exc).__name__, 'message': str(exc)[:2000]}


class CalibrationRecovery:
    """Trusted operator implementation; public callers cannot supply verdicts."""

    def __init__(self, broker, authority_binding):
        self.broker = broker
        self.binding = decode(canonical(authority_binding))
        require(set(self.binding) == BINDING_FIELDS and self.binding['schema'] == BINDING,
                'Exact trusted recovery authority binding required')
        for key in BINDING_FIELDS - {'schema'}:
            text(self.binding[key], key)
        self.runner = FamilyCalibrationStudies(broker)
        # This set distinguishes an active operation in this Broker from a
        # reservation inherited across a process boundary. Writer custody is
        # still supplied by the existing Broker lock, not this memory set.
        with broker._mutex:
            if not hasattr(broker, '_calibration_recovery_active'):
                broker._calibration_recovery_active = set()

    def _actor(self):
        return self.broker._binding_owner(self.broker.admin_token)

    def _owned(self, identity, schema):
        artifact = self.broker._artifact(identity)
        require(artifact['creator'] == artifact['origin'] == 'controller'
                and artifact['data_class'] == 'operations'
                and artifact['authority'] == AUTHORITY
                and type(artifact['body']) is dict and artifact['body'].get('schema') == schema
                and artifact['body'].get('profile') == PROFILE
                and artifact['body'].get('scientific_readiness') is False
                and artifact['body'].get('n_min') is None
                and artifact['body'].get('classification_permitted', False) is False,
                'An owned supported recovery record is required')
        return artifact

    def _objects(self, schema):
        rows = self.broker._db.execute(
            "SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=? "
            "AND json_extract(envelope,'$.creator')='controller' "
            "AND json_extract(envelope,'$.origin')='controller' ORDER BY rowid", (schema,))
        return [self._owned(row[0], schema) for row in rows]

    def _save(self, schema, body, refs, exposure, blobs=()):
        refs = sorted(set(refs))
        strings(refs, 'direct recovery references')
        return self.broker._save_artifact({'version': 'local-artifact/1',
            'creator': 'controller', 'origin': 'controller', 'data_class': 'operations',
            'authority': AUTHORITY, 'source_refs': refs,
            'exposure': sorted(set(exposure) | set(refs)), 'blob_refs': sorted(set(blobs)),
            'body': {'schema': schema, 'profile': PROFILE, 'created_at': self.broker._now(),
                     **body, 'scientific_readiness': False}})

    def _event(self, action, input_id, **details):
        self.broker._event('controller', action, study_id=self.binding['calibration_id'],
                           input_id=input_id, **details)

    def _events(self):
        result = []
        for row in self.broker._db.execute('SELECT envelope FROM events ORDER BY seq'):
            event = decode(row[0])
            if (event['actor'] == 'controller'
                    and event['details'].get('study_id') == self.binding['calibration_id']
                    and event['action'].startswith('calibration_recovery_')):
                require(event['action'] in EVENTS, 'Unsupported recovery event version')
                result.append(event)
        return result

    def _binding_scope(self):
        # Physical relocation can be inspected after restore, but does not
        # acquire execution authority at the new location.
        return {k: v for k, v in self.binding.items() if k != 'registry_path'}

    def _loaded_current(self):
        require(_sha(Path(__file__).read_bytes()) == LOADED_SELF
                and STUDY_LOADED_SOURCE == LOADED_SOURCE == footprint(source_bundle()),
                'Restart after recovery controller/package source changes')

    def _approval_bytes(self):
        values = {}
        for name, path_key, hash_key in (
                ('recovery', 'approval_path', 'approval_sha256'),
                ('original', 'original_approval_path', 'original_approval_sha256')):
            path = _path(self.binding[path_key])
            require(path.stat().st_size <= 1048576, 'Approval exceeds the canonical envelope')
            raw = path.read_bytes()
            require(_sha(raw) == self.binding[hash_key], 'Pinned recovery approval bytes differ')
            values[name] = raw
        return values

    def _original(self, approvals, *, capture=False):
        """Authenticate the exact old prefix, never amend its representation."""
        self._actor()
        self._loaded_current()
        require(_path(self.binding['registry_path']) == self.broker.directory.resolve(),
                'Trusted primary Registry differs')
        q = decode(approvals['recovery'].decode('utf-8'))
        original_approval = decode(approvals['original'].decode('utf-8'))
        require(q.get('schema') == 'conditional-scalar-calibration-recovery-approval/1'
                and canonical(q.get('approved_exception')) == canonical(TERMS)
                and q['original_approval']['sha256'] == self.binding['original_approval_sha256']
                and original_approval.get('schema') == 'conditional-calibration-resource-approval/1',
                'Exact supported operational recovery authority required')
        original_limits = original_approval['limits']
        require(canonical(original_limits) == canonical({'aggregate_compute_ms': TERMS['aggregate_compute_ms'],
            'aggregate_logical_bytes': TERMS['aggregate_logical_bytes'],
            'additional_grants_max': 179, 'attempt_compute_ms': 300000,
            'attempt_storage_bytes': ATTEMPT_BYTES, 'max_attempts': 1}),
            'Original authority or unchanged aggregate limits differ')
        base = self._base(q)
        study = base['study']; body = study['body']; manifest = body['manifest']
        self.broker._require_usable_dependencies(study['id'])
        for grant in base['history'].grants:
            self.broker._require_usable_dependencies(grant['id'])
        expected = body['assessment_source_footprint']
        require(type(expected) is dict and 1 <= len(expected) <= 128,
                'Original assessment footprint is unavailable')
        root = _path(self.binding['assessment_host'])
        assessment = {}
        for name, checksum in expected.items():
            require(re.fullmatch(r'trading_researcher/[A-Za-z_][A-Za-z0-9_]*\.py', name),
                    'Invalid original assessment source path')
            path = _path(str(root / name))
            require(path.is_relative_to(root) and path.stat().st_size <= 16 * 1024 * 1024,
                    'Original assessment source escapes its envelope')
            raw = path.read_bytes()
            require(_sha(raw) == checksum, 'Original assessment source bytes differ')
            assessment[name] = raw
        _package(assessment)
        for name in OWNERS:
            qualified = 'trading_researcher/' + name
            require(qualified in expected and LOADED_SOURCE.get(qualified) == expected[qualified],
                    'Reused original metadata/count owner differs')
        inputs = self.runner._study_inputs(self._actor(), body['request'])
        require(digest(list(inputs)) == digest([body['payload'], manifest,
                                               study['source_refs'], study['exposure']]),
                'Recomputed original inputs differ')
        source = self.runner._load_study_source(study)
        case = body['payload']['case_blob']; cases = self.broker._read_blob_bytes(case['sha256'])
        require(len(cases) == case['size'], 'Original case bytes differ')
        generation = self._generation(study, base['failed'], source, cases)
        controller = _package(source_bundle()) if capture else None
        if controller is not None:
            require(footprint(controller) == LOADED_SOURCE, 'Controller changed during capture')
        return {**base, 'approval': q, 'assessment': assessment,
                'source': source, 'cases': cases, 'generation': generation,
                'controller': controller}

    def _base(self, q):
        require(q.get('schema') == 'conditional-scalar-calibration-recovery-approval/1'
                and canonical(q.get('approved_exception')) == canonical(TERMS),
                'Supported immutable recovery terms required')
        study = self.runner._study(self.binding['calibration_id'])
        body = study['body']; manifest = body['manifest']
        history = self.runner._study_resources(study); budget = history.budget()
        require(q['study_id'] == study['id'] and q['terminal_checkpoint'] == history.checkpoint,
                'Original study/checkpoint differs from the approved stopped prefix')
        require(not history.pending and not history.orphan and not history.unknown
                and budget['overrun'], 'Only the known resolved original overrun is supported')
        limits = manifest['profile']['budget']
        require(limits['attempt_compute_ms'] == 300000
                and limits['attempt_storage_bytes'] == ATTEMPT_BYTES and limits['max_attempts'] == 1,
                'Original immutable attempt policy differs')
        require(1 <= len(manifest['worlds']) <= 2048 and len(history.grants) <= 179,
                'Original bounded inventory or grant count differs')
        fixed = q['fixed_identity']
        for field in ('planned_worlds', 'known_compute_ms_retained', 'known_logical_bytes_retained',
                      'actual_grants_retained', 'verified_worlds_retained'):
            integer(fixed[field], field)
        require(fixed['failed_attempt_retained'] is True
                and fixed['all_original_world_and_seed_ids_unchanged'] is True,
                'Original failures, worlds and seeds must be retained')
        require(fixed['planned_worlds'] == len(manifest['worlds'])
                and fixed['known_compute_ms_retained'] == budget['charged_compute_ms']
                and fixed['known_logical_bytes_retained'] == budget['charged_storage_bytes']
                and fixed['actual_grants_retained'] == len(history.grants)
                and fixed['request_hash'] == digest(body['request'])
                and fixed['manifest_hash'] == digest(manifest)
                and fixed['recipe_hash'] == manifest['recipe_hash']
                and fixed['calculation_source_footprint'] == digest(body['source_footprint']),
                'Approved original input/accounting identity differs')
        known = {r['attempt_id']: r for r in history.reservations}
        breaches = []
        for settled in history.settlements:
            reserved = known[settled['attempt_id']]
            require(settled['usage_known'], 'Original usage is not known')
            for field in ('compute_ms', 'storage_bytes'):
                if settled[field] > reserved[field]:
                    breaches.append((settled['attempt_id'], field))
        require(breaches == [(q['failed_attempt_id'], 'compute_ms')],
                'The approval covers only its named original compute breach')
        old_attempts = []
        for identity in history.results:
            artifact = self.broker._artifact(identity); attempt = artifact['body']
            require(artifact['creator'] == artifact['origin'] == 'controller'
                    and artifact['data_class'] == 'operations'
                    and artifact['authority'] == self.runner._study_authority
                    and attempt['schema'] == self.runner._study_result_schema
                    and attempt['study_id'] == study['id'], 'Original owned attempt differs')
            matching = next(s for s in history.settlements if s['attempt_id'] == attempt['attempt_id'])
            require(matching == attempt['settlement']
                    and history.records[attempt['world_id']] == attempt['outcome'],
                    'Original result/event binding differs')
            old_attempts.append(artifact)
        failed = self.broker._artifact(q['failed_attempt_artifact_id'])
        require(old_attempts and old_attempts[-1] == failed
                and failed['body']['attempt_id'] == q['failed_attempt_id']
                and failed['body']['world_id'] == q['failed_world_id']
                and failed['body']['outcome']['state'] == 'TECHNICAL_FAILURE'
                and failed['body']['failure']['type'] == 'ResourceOverrun',
                'The exact last failed original world is required')
        good = [a for a in old_attempts if a['id'] != failed['id']]
        require(all(a['body']['outcome']['state'] in ('VERIFIED', 'INFORMATION_GAP')
                    and len(a['body']['proofs']) == 2 for a in good)
                and fixed['verified_worlds_retained'] == sum(
                    a['body']['outcome']['state'] == 'VERIFIED' for a in good),
                'Original completed inventory differs')
        require(all(value == 1 for value in budget['attempts_per_world'].values()),
                'Original max-one attempt history differs')
        return {'study': study, 'history': history, 'budget': budget, 'approval': q,
                'attempts': old_attempts, 'failed': failed}

    def _generation(self, study, failed, source, cases):
        outputs = failed['body']['output_blobs']
        descriptor = outputs['generate/child-output.json']
        raw = self.broker._read_blob_bytes(descriptor['sha256'])
        require(len(raw) == descriptor['size'], 'Original generation acknowledgement differs')
        response = decode(raw.decode('utf-8'))
        required = {'result', 'stream_blob', 'request_hash', 'footprint', 'environment'}
        require(type(response) is dict and set(response) in
                (required, required | {'stream_encoding'}), 'Original scalar generation framing differs')
        body = study['body']; manifest = body['manifest']
        world = next(w for w in manifest['worlds'] if w['id'] == failed['body']['world_id'])
        request = {'payload': body['payload'], 'manifest': manifest, 'world': world,
                   'footprint': body['source_footprint'], 'verify': None,
                   'stream_limit': attempt_stream_limit(source, manifest, cases)}
        require(response['request_hash'] == digest(request)
                and response['footprint'] == body['source_footprint']
                and _environment_current(response['environment'])
                and response['result']['world_id'] == world['id']
                and response['result']['outcome']['state'] in ('VERIFIED', 'INFORMATION_GAP'),
                'Original generation input/source/result differs')
        name = 'generate/stream.jsonl' + ('.gz' if 'stream_encoding' in response else '')
        stream = outputs[name]
        require(response['stream_blob'] == stream, 'Original generated stream binding differs')
        require(len(self.broker._read_blob_bytes(stream['sha256'])) == stream['size'],
                'Original generated stream bytes differ')
        return response

    def prepare(self, key):
        key = text(key, 'recovery key')
        with self.broker._mutex:
            self._actor()
            inputs = [a for a in self._objects(INPUT)
                      if a['body']['study_id'] == self.binding['calibration_id']]
            if inputs:
                require(len(inputs) == 1, 'Duplicate recovery input history')
                previous = inputs[0]
                if (previous['body']['key'] != key
                        or previous['body']['binding_scope'] != self._binding_scope()):
                    raise Conflict('This original series already has its one recovery setup')
                amendments = [a for a in self._objects(AMENDMENT)
                              if a['body']['input_id'] == previous['id']]
                require(len(amendments) <= 1, 'Duplicate recovery amendments')
                if amendments:
                    return amendments[0]  # Historical identity, never permission to execute.
                raise Denied('Incomplete or failed setup cannot be restarted under any key')
            approvals = self._approval_bytes()
            original = self._original(approvals, capture=True)
            study = original['study']; old = original['history']; budget = original['budget']
            controller = original['controller']; assessment = original['assessment']
            fee = 2 * (sum(map(len, controller.values())) + sum(map(len, assessment.values()))
                       + sum(map(len, approvals.values()))) + 3 * METADATA_BYTES
            require(budget['charged_storage_bytes'] + fee <= budget['max_storage_bytes']
                    <= TERMS['aggregate_logical_bytes']
                    and budget['max_compute_ms'] <= TERMS['aggregate_compute_ms'],
                    'Existing allocated capacity cannot hold the complete recovery setup')
            body = {'key': key, 'study_id': study['id'], 'binding_scope': self._binding_scope(),
                'registry_path': str(self.broker.directory.resolve()),
                'original_checkpoint': old.checkpoint,
                'original_attempt_ids': [a['id'] for a in original['attempts']],
                'original_continuation_ids': [a['id'] for a in old.grants],
                'failed_attempt_artifact_id': original['failed']['id'],
                'failed_world_id': original['failed']['body']['world_id'],
                'controller_files': _descriptors(controller), 'controller_footprint': LOADED_SOURCE,
                'assessment_source_files': _descriptors(assessment),
                'assessment_source_footprint': study['body']['assessment_source_footprint'],
                'approval_blobs': {name: {'sha256': _sha(raw), 'size': len(raw)}
                                   for name, raw in approvals.items()},
                'approval': original['approval'], 'runtime_identity': _runtime_identity(),
                'setup_storage_bytes': fee, 'custody': 'PLANNED_NOT_REGISTERED',
                'n_min': None}
            refs = [study['id'], original['failed']['id'], *body['original_continuation_ids']]
            with self.broker._transaction():
                saved = self._save(INPUT, body, refs, study['exposure'])
                self._event('calibration_recovery_setup_reserved', saved['id'], storage_bytes=fee)
                self.broker._event('controller', 'bound_computation_started', attempt_id=saved['id'],
                    kind='calibration_recovery_setup', input_ref=study['id'], retained_input_id=saved['id'])
            self.broker._calibration_recovery_active.add(saved['id'])
            staged = {}
            try:
                for category, values in (('controller', controller), ('assessment', assessment),
                                         ('approvals', approvals)):
                    staged[category] = {}
                    for name, raw in values.items():
                        staged[category][name] = self.broker._stage_blob_bytes(raw)
                require(self._approval_bytes() == approvals, 'Authority changed during setup')
                self._loaded_current()
                require(footprint(source_bundle()) == footprint(controller),
                        'Controller changed before source commitment')
                with self.broker._transaction():
                    for values in staged.values():
                        for descriptor in values.values():
                            self.broker._register_blob(descriptor)
                    source = self._save(SOURCE, {'files': staged['controller'],
                        'footprint': footprint(controller), 'runtime_identity': _runtime_identity(),
                        'input_id': saved['id']}, [saved['id']], study['exposure'],
                        [x['sha256'] for x in staged['controller'].values()])
                    amendment = self._save(AMENDMENT, {'input_id': saved['id'],
                        'study_id': study['id'], 'source_id': source['id'],
                        'original_checkpoint': old.checkpoint, 'exception': deepcopy(TERMS),
                        'assessment_source_files': staged['assessment'],
                        'assessment_source_footprint': footprint(assessment),
                        'approval_blobs': staged['approvals'], 'runtime_identity': _runtime_identity(),
                        'n_min': None}, [saved['id'], source['id'], *refs], study['exposure'],
                        [x['sha256'] for group in ('assessment', 'approvals')
                         for x in staged[group].values()])
                    self._event('calibration_recovery_amended', saved['id'], artifact_id=amendment['id'])
                    self._event('calibration_recovery_setup_settled', saved['id'], usage_known=True,
                        complete=True, failure=None, partial_blobs=[], unavailable_blobs=[])
                    self.broker._event('controller', 'bound_computation_checked', attempt_id=saved['id'],
                        artifact_id=amendment['id'], status='RECOVERY_PREPARED')
                    self._history(saved, amendment)
                return amendment
            except BaseException as exc:
                with self.broker._transaction():
                    partial = []
                    unavailable = []
                    for group in staged.values():
                        for descriptor in group.values():
                            try:
                                self.broker._register_blob(descriptor)
                            except (ValueError, Denied, Conflict, OSError) as custody_failure:
                                unavailable.append({'descriptor': descriptor,
                                                    'failure': _failure(custody_failure)})
                            else:
                                partial.append(descriptor)
                    self._event('calibration_recovery_setup_settled', saved['id'], usage_known=False,
                        complete=False, failure=_failure(exc), partial_blobs=partial,
                        unavailable_blobs=unavailable)
                    self.broker._event('controller', 'bound_computation_checked', attempt_id=saved['id'],
                        status='FAILED_SETUP', reason=str(exc)[:2000])
                raise
            finally:
                self.broker._calibration_recovery_active.discard(saved['id'])

    def _resolve(self, identity):
        artifact = self.broker._artifact(identity)
        schema = artifact['body'].get('schema')
        if schema == INPUT:
            input_record = self._owned(identity, INPUT)
            matches = [a for a in self._objects(AMENDMENT)
                       if a['body']['input_id'] == identity]
            require(len(matches) <= 1, 'Duplicate amendments for the same recovery input')
            amendment = matches[0] if matches else None
        else:
            amendment = self._owned(identity, AMENDMENT)
            input_record = self._owned(amendment['body']['input_id'], INPUT)
        require(input_record['body']['study_id'] == self.binding['calibration_id']
                and input_record['body']['binding_scope'] == self._binding_scope(),
                'Recovery belongs to a different original study or authority binding')
        return input_record, amendment

    def _history(self, input_record, amendment):
        """Replay the new exact ledger on the unchanged authenticated old prefix."""
        ib = input_record['body']; base = self._base(ib['approval'])
        old = base['history']; old_budget = base['budget']
        require(ib['original_checkpoint'] == old.checkpoint
                and ib['original_attempt_ids'] == [a['id'] for a in base['attempts']]
                and ib['original_continuation_ids'] == [a['id'] for a in old.grants]
                and ib['failed_attempt_artifact_id'] == base['failed']['id'],
                'Original recovery prefix changed')
        inputs = [a for a in self._objects(INPUT) if a['body']['study_id'] == base['study']['id']]
        require(len(inputs) == 1 and inputs[0]['id'] == input_record['id'],
                'Multiple recovery setup authorities cannot share one original series')
        state = {'input': input_record, 'amendment': amendment, 'base': base,
            'compute': old_budget['charged_compute_ms'], 'storage': old_budget['charged_storage_bytes'],
            'max_compute': old_budget['max_compute_ms'], 'max_storage': old_budget['max_storage_bytes'],
            'records': deepcopy(old.records),
            'sources': {a['body']['world_id']: a['id'] for a in base['attempts']},
            'results': list(ib['original_attempt_ids']), 'grants': list(old.grants),
            'attempts': dict(old_budget['attempts_per_world']), 'pending': {}, 'closed': set(),
            'setup_reserved': False, 'setup_settled': False, 'setup_complete': False,
            'unknown': False, 'orphan': False, 'overrun': False, 'failure': False,
            'amended': False, 'last_completed': old.last_completed,
            'no_progress': old.no_progress, 'prepared_checkpoint': None}
        hasher = hashlib.sha256(canonical({'schema': PROFILE, 'study_id': base['study']['id'],
            'original_checkpoint': old.checkpoint, 'input_id': input_record['id']}).encode())
        seen = set()
        for event in self._events():
            details = event['details']; action = event['action']
            require(details.get('input_id') == input_record['id'], 'Foreign recovery event input')
            if action == 'calibration_recovery_setup_reserved':
                require(not state['setup_reserved'] and not state['amended']
                        and details['storage_bytes'] == ib['setup_storage_bytes'],
                        'Duplicate or inconsistent recovery setup reservation')
                integer(details['storage_bytes'], 'setup reservation', 1)
                planned = sum(descriptor['size'] for group in ('controller_files', 'assessment_source_files',
                    'approval_blobs') for descriptor in ib[group].values())
                require(details['storage_bytes'] == 2 * planned + 3 * METADATA_BYTES
                        and state['storage'] + details['storage_bytes'] <= state['max_storage'],
                        'Complete setup tariff or allocated capacity differs')
                state['storage'] += details['storage_bytes']; state['setup_reserved'] = True
            elif action == 'calibration_recovery_amended':
                require(state['setup_reserved'] and not state['amended']
                        and not state['setup_settled'] and amendment is not None
                        and details['artifact_id'] == amendment['id'],
                        'Unreserved, duplicate or mismatched amendment')
                ab = amendment['body']
                require(ab['input_id'] == input_record['id'] and ab['study_id'] == base['study']['id']
                        and ab['original_checkpoint'] == old.checkpoint
                        and canonical(ab['exception']) == canonical(TERMS), 'Amendment terms differ')
                source = self._owned(ab['source_id'], SOURCE)
                require(source['body']['input_id'] == input_record['id']
                        and source['body']['files'] == ib['controller_files']
                        and source['body']['footprint'] == ib['controller_footprint']
                        and ab['assessment_source_files'] == ib['assessment_source_files']
                        and ab['assessment_source_footprint'] == ib['assessment_source_footprint']
                        and ab['approval_blobs'] == ib['approval_blobs'],
                        'Controller or original source custody differs')
                require(set(source['blob_refs']) == {d['sha256'] for d in ib['controller_files'].values()}
                        and set(amendment['blob_refs']) == {d['sha256']
                            for group in ('assessment_source_files', 'approval_blobs')
                            for d in ib[group].values()}, 'Recovery source blob ownership differs')
                state['amended'] = True
            elif action == 'calibration_recovery_setup_settled':
                require(state['setup_reserved'] and not state['setup_settled']
                        and type(details['usage_known']) is bool and type(details['complete']) is bool,
                        'Duplicate or unreserved setup settlement')
                require(not details['complete'] or state['amended'] and details['usage_known']
                        and details['failure'] is None and not details['unavailable_blobs'],
                        'Incomplete custody cannot become a prepared amendment')
                for descriptor in details['partial_blobs']:
                    require(type(descriptor) is dict and set(descriptor) == {'sha256', 'size'},
                            'Malformed partial setup custody')
                    row = self.broker._db.execute('SELECT size FROM blobs WHERE sha256=?',
                                                 (descriptor['sha256'],)).fetchone()
                    require(row is not None and row[0] == descriptor['size'],
                            'Unregistered partial setup files cannot claim backup custody')
                state['setup_settled'] = True; state['setup_complete'] = details['complete']
                state['unknown'] |= not details['usage_known']
                state['failure'] |= not details['complete'] or details['failure'] is not None
                if details['failure'] and details['failure']['type'] == 'OrphanUncertain':
                    state['orphan'] = True
            elif action == 'calibration_recovery_reserved':
                require(state['setup_complete'] and not state['failure'] and not state['unknown']
                        and not state['orphan'] and not state['overrun'] and not state['pending'],
                        'Recovery cannot reserve after a failure or outstanding use')
                reservation = details['reservation']; attempt = reservation['attempt_id']
                require(set(reservation) == {'attempt_id', 'world_id', 'compute_ms', 'storage_bytes'}
                        and attempt not in seen and details['expected_checkpoint'] == hasher.hexdigest(),
                        'Duplicate or stale recovery reservation')
                require(type(reservation['compute_ms']) is int and reservation['compute_ms'] == ATTEMPT_MS
                        and type(reservation['storage_bytes']) is int
                        and reservation['storage_bytes'] == ATTEMPT_BYTES,
                        'Recovery reservation differs from its fixed envelope')
                world = self._next_world(state)
                require(world is not None and reservation['world_id'] == world['id'],
                        'Recovery changed the next original world')
                count = state['attempts'].get(world['id'], 0)
                maximum = 2 if world['id'] == ib['failed_world_id'] else 1
                require(count < maximum, 'Recovery attempt allowance is exhausted')
                require(state['compute'] + ATTEMPT_MS <= state['max_compute']
                        and state['storage'] + ATTEMPT_BYTES <= state['max_storage'],
                        'The full next recovery envelope does not fit')
                seen.add(attempt); state['attempts'][world['id']] = count + 1
                state['pending'][attempt] = reservation
                state['compute'] += ATTEMPT_MS; state['storage'] += ATTEMPT_BYTES
            elif action == 'calibration_recovery_settled':
                settlement = details['settlement']; attempt = settlement['attempt_id']
                require(attempt in state['pending'] and attempt not in state['closed'],
                        'Unreserved or duplicate recovery settlement')
                reserved = state['pending'].pop(attempt); state['closed'].add(attempt)
                require(details['outcome']['world_id'] == reserved['world_id']
                        and type(settlement['usage_known']) is bool and type(details['orphan_uncertain']) is bool,
                        'Recovery settlement world or usage framing differs')
                for field, target in (('compute_ms', 'compute'), ('storage_bytes', 'storage')):
                    observed = integer(settlement[field], field)
                    charged = observed if settlement['usage_known'] else max(observed, reserved[field])
                    state[target] += charged - reserved[field]
                    state['overrun'] |= observed > reserved[field]
                state['unknown'] |= not settlement['usage_known']
                state['orphan'] |= details['orphan_uncertain']
                identity = details['artifact_id']
                outcome = details['outcome']
                if identity is None:
                    require(details['orphan_uncertain'] and outcome['state'] == 'TECHNICAL_FAILURE',
                            'Only unavailable interrupted work can lack a retained result')
                    source_id = input_record['id']
                else:
                    result = self._owned(identity, RESULT); rb = result['body']
                    require(rb['input_id'] == input_record['id'] and rb['recovery_id'] == amendment['id']
                            and rb['study_id'] == base['study']['id']
                            and rb['attempt_id'] == attempt and rb['world_id'] == reserved['world_id']
                            and rb['settlement'] == settlement and rb['outcome'] == outcome,
                            'Owned recovery result differs from its event')
                    eligible = (settlement['usage_known'] and not rb['failure']
                        and not rb['resource_violations'] and not rb['dependency_failure']
                        and len(rb['proofs']) == 2 and outcome['state'] in ('VERIFIED', 'INFORMATION_GAP'))
                    require(type(rb['eligible']) is bool and rb['eligible'] == eligible,
                            'Recovery outcome eligibility differs')
                    state['failure'] |= not eligible
                    state['results'].append(identity); source_id = identity
                family_study.summarize(base['study']['body']['manifest'], [outcome])
                state['records'][outcome['world_id']] = outcome
                state['sources'][outcome['world_id']] = source_id
                state['failure'] |= outcome['state'] not in ('VERIFIED', 'INFORMATION_GAP')
            else:
                require(state['setup_complete'] and not state['pending'] and not state['failure']
                        and not state['overrun'] and not state['unknown'] and not state['orphan'],
                        'A new grant cannot repair a recovery failure')
                grant = self._owned(details['artifact_id'], GRANT); gb = grant['body']
                require(gb['input_id'] == input_record['id'] and gb['recovery_id'] == amendment['id']
                        and gb['study_id'] == base['study']['id']
                        and gb['previous_continuation_id'] ==
                            (state['grants'][-1]['id'] if state['grants'] else None)
                        and gb['expected_checkpoint'] == hasher.hexdigest(),
                        'Recovery grant input or checkpoint differs')
                terms = self._capacity_terms(state)
                require({k: gb[k] for k in terms} == terms, 'Recovery grant capacity or metadata differs')
                state['max_compute'] += terms['additional_compute_ms']
                state['max_storage'] += terms['additional_storage_bytes']
                state['storage'] += METADATA_BYTES
                state['grants'].append(grant)
                state['last_completed'] = terms['completed_worlds_before']
                state['no_progress'] = terms['no_progress_continuations']
            require(state['max_compute'] <= TERMS['aggregate_compute_ms']
                    and state['max_storage'] <= TERMS['aggregate_logical_bytes'],
                    'Recovery allocation exceeds aggregate authority')
            # Actual known excess cannot be rolled back or hidden. Preserve its
            # charge and fence every future action, as the original owner does.
            state['overrun'] |= state['compute'] > state['max_compute'] or state['storage'] > state['max_storage']
            hasher.update(b'\n' + canonical(event).encode())
            if action == 'calibration_recovery_setup_settled' and details['complete']:
                # The immutable pre-run backup can bind this prefix without
                # claiming that a later live checkpoint is still the initial one.
                state['prepared_checkpoint'] = hasher.hexdigest()
        require(state['setup_reserved'], 'Recovery input lacks its durable setup reservation')
        require(not state['amended'] or state['setup_complete'], 'Incomplete atomic amendment commitment')
        state['checkpoint'] = hasher.hexdigest()
        return state

    def _next_world(self, state):
        return next((w for w in state['base']['study']['body']['manifest']['worlds']
            if w['id'] not in state['records'] or state['records'][w['id']]['state'] == 'TECHNICAL_FAILURE'), None)

    def _capacity_terms(self, state):
        require(not state['pending'] and not state['unknown'] and not state['orphan']
                and not state['overrun'] and not state['failure'] and state['setup_complete'],
                'Capacity cannot forgive failed or uncertain recovery work')
        require(self._next_world(state) is not None and len(state['grants']) < 179,
                'No unfinished inventory or continuation allowance remains')
        compute = state['compute'] + ATTEMPT_MS
        storage = state['storage'] + METADATA_BYTES + ATTEMPT_BYTES
        require(compute > state['max_compute'] or state['storage'] + ATTEMPT_BYTES > state['max_storage'],
                'A recovery continuation requires a real resource stop')
        # Preserve the existing finite operator's paired tranches. A resource
        # already allocated to its aggregate ceiling receives zero, not a reset.
        additional_compute = min(3600000, TERMS['aggregate_compute_ms'] - state['max_compute'])
        additional_storage = min(4 * 1024**3, TERMS['aggregate_logical_bytes'] - state['max_storage'])
        require(additional_compute + additional_storage > 0
                and compute <= state['max_compute'] + additional_compute
                and storage <= state['max_storage'] + additional_storage,
                'Finite remaining authority cannot hold the next full attempt and grant metadata')
        completed = sum(r['state'] in ('VERIFIED', 'INFORMATION_GAP') for r in state['records'].values())
        no_progress = 0 if completed > state['last_completed'] else state['no_progress'] + 1
        require(no_progress <= 2, 'Recovery made no completed-world progress under D030')
        return {'additional_compute_ms': additional_compute,
            'additional_storage_bytes': additional_storage,
            'charged_compute_ms_before': state['compute'], 'charged_storage_bytes_before': state['storage'],
            'completed_worlds_before': completed, 'no_progress_continuations': no_progress}

    def _source_guard(self, state, *, execution=True):
        self._actor(); self._loaded_current()
        input_record = state['input']; ib = input_record['body']; amendment = state['amendment']
        require(state['setup_complete'] and amendment is not None, 'Recovery setup is incomplete')
        require(str(self.broker.directory.resolve()) == str(_path(self.binding['registry_path'])),
                'Recovery reader belongs to another Registry')
        if execution:
            require(ib['registry_path'] == str(self.broker.directory.resolve()),
                    'A restored copy has descriptive history, not live execution authority')
        ab = amendment['body']; source = self._owned(ab['source_id'], SOURCE)
        require(source['body']['footprint'] == LOADED_SOURCE
                and source['body']['runtime_identity'] == ab['runtime_identity']
                == ib['runtime_identity'] == _runtime_identity(),
                'Recovery controller source or runtime is stale')
        controller = {}
        for name, descriptor in source['body']['files'].items():
            raw = self.broker._read_blob_bytes(descriptor['sha256'])
            require(len(raw) == descriptor['size'], 'Retained controller size differs')
            controller[name] = raw
        require(footprint(_package(controller)) == LOADED_SOURCE,
                'Retained controller source bytes differ')
        assessment = {}
        for name, descriptor in ab['assessment_source_files'].items():
            raw = self.broker._read_blob_bytes(descriptor['sha256'])
            require(len(raw) == descriptor['size'], 'Retained assessment source size differs')
            assessment[name] = raw
        expected = state['base']['study']['body']['assessment_source_footprint']
        require(footprint(_package(assessment)) == expected == ab['assessment_source_footprint'],
                'Original retained assessment source differs')
        for name in OWNERS:
            path = 'trading_researcher/' + name
            require(LOADED_SOURCE.get(path) == expected.get(path),
                    'Reused original metadata/count owner changed')
        authority = self._approval_bytes()
        for name, descriptor in ab['approval_blobs'].items():
            raw = self.broker._read_blob_bytes(descriptor['sha256'])
            require(raw == authority[name] and len(raw) == descriptor['size'],
                    'Retained operational authority bytes differ')
        require(decode(authority['recovery'].decode('utf-8')) == ib['approval'],
                'Operational approval body differs')
        for identity in (state['base']['study']['id'], input_record['id'], source['id'], amendment['id'],
                         *(grant['id'] for grant in state['grants'])):
            self.broker._require_usable_dependencies(identity)
        study = state['base']['study']; body = study['body']
        inputs = self.runner._study_inputs(self._actor(), body['request'])
        require(digest(list(inputs)) == digest([body['payload'], body['manifest'],
                                               study['source_refs'], study['exposure']]),
                'Recomputed frozen inputs differ at recovery use')
        original_source = self.runner._load_study_source(study)
        case = body['payload']['case_blob']; cases = self.broker._read_blob_bytes(case['sha256'])
        require(len(cases) == case['size'], 'Frozen case input size differs')
        generation = self._generation(study, state['base']['failed'], original_source, cases)
        return original_source, cases, generation

    def _view(self, state, *, check_source=True):
        ib = state['input']['body']; study = state['base']['study']; manifest = study['body']['manifest']
        records = list(state['records'].values())
        summary = family_study.summarize(manifest, records)
        summary['candidate_qualification'] = 'fixed_studied_target_not_n_min'
        source_failure = None
        restored = ib['registry_path'] != str(self.broker.directory.resolve())
        if check_source and state['setup_complete']:
            try:
                self._source_guard(state, execution=False)
            except (ValueError, Denied, Conflict, OSError, KeyError, TypeError) as exc:
                source_failure = _failure(exc)
        if source_failure or not state['setup_complete']:
            summary['count_assessment'] = {'status': 'NOT_ASSESSED',
                'reason': 'recovery_source_or_custody_not_current', 'scientific_readiness': False, 'n_min': None}
        else:
            assessment = family_study.count_assessment(manifest, records, state['sources'],
                                                       study['body']['request']['applicability'])
            require(assessment['plan_hash'] == study['body']['count_plan_hash'],
                    'Original fixed count plan changed')
            assessment.update(input_authentication='OWNED_ORIGINAL_AND_RECOVERY_REPLAYED_ATTEMPTS',
                freshness='RECORDED_SEED_DISJOINTNESS_ONLY',
                event_semantics='FIXED_JOINT_WORLD_UNIONS_AND_PER_RESPONSE_DETECTION')
            summary['count_assessment'] = assessment
        fits = (state['compute'] + ATTEMPT_MS <= state['max_compute']
                and state['storage'] + ATTEMPT_BYTES <= state['max_storage'])
        world = self._next_world(state)
        status = ('ORPHAN_UNCERTAIN' if state['orphan'] else
            'USAGE_UNCERTAIN' if state['unknown'] else
            'SETUP_PENDING' if not state['setup_settled'] else
            'TECHNICAL_FAILURE' if not state['setup_complete'] or state['failure'] else
            'RUNNING' if state['pending'] else
            'RESOURCE_STOP' if state['overrun'] else
            'COMPLETE' if summary['complete'] else
            'MODEL_GAP' if any(r['state'] == 'MODEL_GAP' for r in records) else
            'RESOURCE_STOP' if not fits else 'READY')
        if restored:
            status = 'RESTORED_COPY'
        elif source_failure:
            status = 'INVALIDATED' if source_failure['type'] == 'Denied' else 'SOURCE_STALE'
        if status != 'READY':
            world = None
        result = {'recovery_id': state['amendment']['id'] if state['amendment'] else state['input']['id'],
            'input_id': state['input']['id'], 'study_id': study['id'], 'status': status,
            'original_checkpoint': ib['original_checkpoint'], 'recovery_checkpoint': state['checkpoint'],
            'prepared_checkpoint': state['prepared_checkpoint'],
            'historical_overrun': True, 'approved_historical_exception': {
                'attempt_artifact_id': ib['failed_attempt_artifact_id'], 'world_id': ib['failed_world_id'],
                'settlement': state['base']['failed']['body']['settlement']},
            'budget': {'charged_compute_ms': state['compute'], 'charged_storage_bytes': state['storage'],
                'max_compute_ms': state['max_compute'], 'max_storage_bytes': state['max_storage'],
                'global_max_compute_ms': TERMS['aggregate_compute_ms'],
                'global_max_storage_bytes': TERMS['aggregate_logical_bytes'],
                'continuation_count': len(state['grants']), 'outstanding_attempts': sorted(state['pending']),
                'attempts_per_world': state['attempts'], 'usage_uncertain': state['unknown'],
                'current_overrun': state['overrun'], 'setup_storage_bytes': ib['setup_storage_bytes'],
                'next_reservation_fits': fits and state['setup_complete']
                    and not state['pending'] and not state['unknown'] and not state['orphan']
                    and not state['overrun'] and not state['failure']},
            'attempt_artifact_ids': state['results'],
            'continuation_ids': [g['id'] for g in state['grants']],
            'next_world_id': None if world is None else world['id'], 'summary': summary,
            'source_failure': source_failure, 'scientific_readiness': False, 'n_min': None}
        canonical(result)
        return result

    def inspect(self, recovery_id):
        with self.broker._mutex:
            self._actor()
            input_record, amendment = self._resolve(recovery_id)
            return self._view(self._history(input_record, amendment))

    def continue_capacity(self, recovery_id, expected_checkpoint):
        with self.broker._transaction():
            self._actor()
            input_record, amendment = self._resolve(recovery_id)
            state = self._history(input_record, amendment)
            if expected_checkpoint != state['checkpoint']:
                raise Conflict('Recovery continuation checkpoint is stale')
            self._source_guard(state)
            require(self._view(state, check_source=False)['status'] == 'RESOURCE_STOP',
                    'A recovery continuation requires a genuine resource stop')
            terms = self._capacity_terms(state)
            previous = state['grants'][-1]['id'] if state['grants'] else None
            refs = [amendment['id'], *([previous] if previous else [])]
            grant = self._save(GRANT, {'input_id': input_record['id'], 'recovery_id': amendment['id'],
                'study_id': self.binding['calibration_id'], 'expected_checkpoint': state['checkpoint'],
                'previous_continuation_id': previous, **terms}, refs, amendment['exposure'])
            self._event('calibration_recovery_continued', input_record['id'], artifact_id=grant['id'])
            self._history(input_record, amendment)
            return grant

    def advance(self, recovery_id, expected_checkpoint):
        started = time.monotonic()
        with self.broker._transaction():
            self._actor()
            input_record, amendment = self._resolve(recovery_id)
            state = self._history(input_record, amendment)
            if expected_checkpoint != state['checkpoint']:
                raise Conflict('Recovery attempt checkpoint is stale')
            self._source_guard(state)
            view = self._view(state, check_source=False)
            require(view['status'] == 'READY', 'Recovery is not ready for another original world')
            study = state['base']['study']; manifest = study['body']['manifest']
            world = next(w for w in manifest['worlds'] if w['id'] == view['next_world_id'])
            attempt = uuid.uuid4().hex
            self._event('calibration_recovery_reserved', input_record['id'],
                expected_checkpoint=state['checkpoint'], reservation={'attempt_id': attempt,
                    'world_id': world['id'], 'compute_ms': ATTEMPT_MS, 'storage_bytes': ATTEMPT_BYTES})
            self.broker._event('controller', 'bound_computation_started', attempt_id=attempt,
                kind='calibration_recovery', input_ref=study['id'], retained_input_id=amendment['id'])
            self.broker._calibration_recovery_active.add(attempt)

        def remaining():
            seconds = ATTEMPT_MS / 1000 - (time.monotonic() - started)
            require(seconds > 0, 'Recovery exhausted its approved attempt deadline')
            return seconds

        meter = {'materialized_bytes': 0, 'accounting_complete': True}
        outputs = []; calculated = None; proofs = []; failure = None; dependency_failure = None
        cancelled = None
        outcome = self.runner._study_failed_outcome(manifest, world)
        try:
            with self.broker._mutex:
                current = self._history(input_record, amendment)
                source, cases, generation = self._source_guard(current)
            calculated, proofs = execute_attempt(source, study['body']['payload'], manifest, world,
                                                 cases, remaining, meter, outputs)
            require(calculated['world_id'] == world['id'] and calculated['scientific_readiness'] is False
                    and calculated['classification_permitted'] is False and calculated['n_min'] is None,
                    'Recovery result claims forbidden identity or authority')
            outcome = calculated['outcome']
            family_study.summarize(manifest, [outcome])
            if outcome['state'] != 'TECHNICAL_FAILURE':
                require(len(proofs) == 2, 'Completed recovery requires full separate replay')
            if world['id'] == input_record['body']['failed_world_id']:
                require(calculated == generation['result'] and len(proofs) == 2
                        and proofs[0]['request_hash'] == generation['request_hash']
                        and proofs[0]['stream_blob'] == generation['stream_blob'],
                        'Retry generation differs from the complete retained original generation')
                generated = dict(outputs)
                name = 'generate/stream.jsonl' + ('.gz' if 'stream_encoding' in generation else '')
                require(name in generated and _sha(generated[name]) == generation['stream_blob']['sha256']
                        and len(generated[name]) == generation['stream_blob']['size'],
                        'Retry full encoded generation bytes differ')
            remaining()
        except BaseException as exc:
            failure = _failure(exc)
            outcome = self.runner._study_failed_outcome(manifest, world)
            if not isinstance(exc, Exception):
                cancelled = exc
        try:
            with self.broker._mutex:
                current = self._history(input_record, amendment)
                try:
                    self._source_guard(current)
                except (ValueError, Denied, Conflict, OSError, KeyError, TypeError) as exc:
                    dependency_failure = _failure(exc)
                    outcome = self.runner._study_failed_outcome(manifest, world)
                # A staging failure leaves the full reservation outstanding;
                # startup reconciliation charges it conservatively and fences use.
                descriptors = {name: self.broker._stage_blob_bytes(raw) for name, raw in outputs}
                compute = math.ceil((time.monotonic() - started) * 1000)
                storage = integer(meter['materialized_bytes'], 'materialized recovery bytes') \
                    + sum(len(raw) for _, raw in outputs) + METADATA_BYTES
                settlement = {'attempt_id': attempt, 'compute_ms': compute, 'storage_bytes': storage,
                              'usage_known': meter['accounting_complete']}
                require(type(settlement['usage_known']) is bool, 'Exact recovery metering state required')
                violations = [{'field': field, 'observed': observed, 'reserved': maximum}
                    for field, observed, maximum in (('compute_ms', compute, ATTEMPT_MS),
                                                     ('storage_bytes', storage, ATTEMPT_BYTES))
                    if observed > maximum]
                if violations or not settlement['usage_known']:
                    outcome = self.runner._study_failed_outcome(manifest, world)
                eligible = (not failure and not dependency_failure and not violations
                    and settlement['usage_known'] and len(proofs) == 2
                    and outcome['state'] in ('VERIFIED', 'INFORMATION_GAP'))
                with self.broker._transaction():
                    retained = self._history(input_record, amendment)
                    require(attempt in retained['pending'], 'Recovery attempt is already settled')
                    for descriptor in descriptors.values():
                        self.broker._register_blob(descriptor)
                    latest = retained['grants'][-1]['id'] if retained['grants'] else None
                    result = self._save(RESULT, {'input_id': input_record['id'],
                        'recovery_id': amendment['id'], 'study_id': study['id'], 'attempt_id': attempt,
                        'world_id': world['id'], 'outcome': outcome, 'result': calculated, 'proofs': proofs,
                        'output_blobs': descriptors, 'settlement': settlement, 'failure': failure,
                        'resource_violations': violations, 'dependency_failure': dependency_failure,
                        'eligible': bool(eligible), 'continuation_id': latest, 'n_min': None},
                        [amendment['id'], *([latest] if latest else [])], amendment['exposure'],
                        [d['sha256'] for d in descriptors.values()])
                    self._event('calibration_recovery_settled', input_record['id'], settlement=settlement,
                        outcome=outcome, artifact_id=result['id'], orphan_uncertain=False)
                    self.broker._event('controller', 'bound_computation_checked', attempt_id=attempt,
                        artifact_id=result['id'], status=outcome['state'])
                    final = self._history(input_record, amendment)
                view = self._view(final)
            if cancelled is not None:
                raise cancelled
            return view
        finally:
            self.broker._calibration_recovery_active.discard(attempt)

    def recover_incomplete(self):
        """Explicit startup reconciliation; never reexecute an interrupted slot."""
        with self.broker._transaction():
            self._actor()
            changed = []
            for input_record in self._objects(INPUT):
                if input_record['body']['study_id'] != self.binding['calibration_id']:
                    continue
                require(input_record['body']['binding_scope'] == self._binding_scope(),
                        'Recovery authority binding differs after restart')
                matches = [a for a in self._objects(AMENDMENT)
                           if a['body']['input_id'] == input_record['id']]
                require(len(matches) <= 1, 'Duplicate recovery amendments after restart')
                amendment = matches[0] if matches else None
                state = self._history(input_record, amendment)
                if not state['setup_settled']:
                    require(input_record['id'] not in self.broker._calibration_recovery_active,
                            'Recovery setup is active in this Broker')
                    self._event('calibration_recovery_setup_settled', input_record['id'],
                        usage_known=False, complete=False, failure={'type': 'OrphanUncertain',
                            'message': 'Interrupted setup; full tariff retained, no automatic restart'},
                        partial_blobs=[], unavailable_blobs=[])
                    changed.append(input_record['id'])
                for attempt, reservation in state['pending'].items():
                    require(attempt not in self.broker._calibration_recovery_active,
                            'Recovery attempt is active in this Broker')
                    manifest = state['base']['study']['body']['manifest']
                    world = next(w for w in manifest['worlds'] if w['id'] == reservation['world_id'])
                    outcome = self.runner._study_failed_outcome(manifest, world)
                    self._event('calibration_recovery_settled', input_record['id'],
                        settlement={'attempt_id': attempt, 'compute_ms': 0, 'storage_bytes': 0,
                                    'usage_known': False}, outcome=outcome, artifact_id=None,
                        orphan_uncertain=True)
                    changed.append(attempt)
                self._history(input_record, amendment)
            return {'reconciled': changed, 'scientific_readiness': False, 'n_min': None}
