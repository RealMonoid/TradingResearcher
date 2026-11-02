"""Atomic scientific commitments with a deliberately fail-closed admission owner.

Operator inputs are references, never scientific verdicts. Synthetic transaction
tests replace the private admission resolver, not any public scientific policy.
"""
import hashlib
from pathlib import Path
import re
import uuid

from .codec import Invalid, canonical, decode, integer, strings, text
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .evaluation_policy import family_budget
from .certification import _runtime_identity

INPUT = 'scientific-freeze-input/1'
ATTEMPT = 'scientific-freeze-attempt/1'
MANIFEST = 'frozen-manifest/1'
TRIAL = 'scientific-trial/1'
ALLOCATION = 'scientific-allocation/1'
FAMILY_BINDING = 'scientific-family-policy-binding/1'
AUTHORITY = 'scientific_commitment_not_execution_or_release_permission'
LOADED_SELF = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
LOADED_PACKAGE = footprint(source_bundle())


def require(condition, message):
    if not condition:
        raise Invalid(message)


class ScientificFreeze:
    def _freeze_objects(self, schema):
        return [self._artifact(row[0]) for row in self._db.execute(
            """SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?
            AND json_extract(envelope,'$.creator')='controller'
            AND json_extract(envelope,'$.origin')='controller' ORDER BY rowid""", (schema,))]

    def _freeze_closure(self, roots):
        pending, artifacts, exposure, blobs = list(roots), {}, set(roots), set()
        while pending:
            identity = pending.pop()
            if identity in artifacts:
                continue
            require(len(artifacts) < 256, 'Freeze closure exceeds the existing reference envelope')
            artifact = self._artifact(identity)
            artifacts[identity] = artifact
            exposure.update(artifact['exposure'])
            blobs.update(artifact.get('blob_refs', []))
            pending.extend(artifact['source_refs'])
            dependencies = self._technical_dependencies(artifact)
            if dependencies is not None:
                pending.extend(dependencies)
            for ref in artifact['exposure']:
                if self._db.execute('SELECT 1 FROM artifacts WHERE id=?', (ref,)).fetchone():
                    pending.append(ref)
        exposure.update(artifacts)
        strings(sorted(exposure), 'inherited freeze exposure')
        strings(sorted(blobs), 'freeze blob references')
        return sorted(artifacts), sorted(exposure), sorted(blobs)

    def _scientific_freeze_admission(self, actor, request):
        """Current preparation/count checks cannot issue scientific admission.

        Complete this owner against actual calibration/information and scientific
        data/selection prerequisites before any real batch can freeze. No caller
        flag, source schema or private-plan qualification substitutes for them.
        """
        gaps = ['SCIENTIFIC_SELECTION_AND_RESERVATION_NOT_QUALIFIED',
                'SCIENTIFIC_DATA_AND_EXPOSURE_NOT_ADMITTED',
                'CALIBRATED_ESTIMATOR_AND_INFORMATION_PLAN_NOT_ADMITTED']
        observations = []
        roots = [request[name] for name in
                 ('campaign_id', 'selection_record_ref', 'reservation_spec_ref')]
        roots.extend(request['plan_ids'])
        for plan_id in request['plan_ids']:
            try:
                current = self._inspect_evaluation_plan(actor, plan_id)
                self._require_usable_dependencies(plan_id)
                observations.append(current)
                if current['status'] != 'POLICY_DRAFT':
                    gaps.append('EVALUATION_PLAN_GAP:' + plan_id)
                for gate in current.get('current_remaining_gates') or []:
                    if gate != 'atomic_allocation_and_freeze':
                        gaps.append(gate + ':' + plan_id)
            except (Invalid, Denied, Conflict, KeyError, TypeError, OSError) as exc:
                observations.append({'plan_id': plan_id, 'failure_type': type(exc).__name__})
                gaps.append('UNQUALIFIED_PLAN:' + plan_id)
        if request['role'] == 'corroboration':
            gaps.append('CORROBORATION_PRERESERVATION_AND_DEPENDENCE_NOT_QUALIFIED')
        closure, _, _ = self._freeze_closure(roots)
        return {'gaps': sorted(set(gaps)), 'artifact_ids': closure, 'claims': [],
                'outcome_record_ids': [], 'admission': {'plan_observations': observations,
                    'qualification': 'Existing preparation checks grant no scientific admission.'}}

    def _freeze_save(self, schema, body, refs, exposure, *, blobs=None):
        refs = sorted(set(refs))
        exposure = sorted(set(exposure) | set(refs))
        strings(refs, 'freeze references')
        strings(exposure, 'freeze exposure')
        return self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
            'origin': 'controller', 'data_class': 'assessment', 'source_refs': refs,
            'exposure': exposure, 'blob_refs': blobs or [], 'authority': AUTHORITY,
            'body': {'schema': schema, **body}})

    def _freeze_attempt(self, attempt, capsule, status, *, manifest=None, admission=None, failure=None,
                        rejected_request=None):
        exposure = set(capsule['exposure'])
        if rejected_request is not None:
            requested = [rejected_request[name] for name in
                         ('campaign_id', 'selection_record_ref', 'reservation_spec_ref')]
            requested.extend(rejected_request['plan_ids'])
            exposure.update(requested)
            known = [ref for ref in requested if self._db.execute(
                'SELECT 1 FROM artifacts WHERE id=?', (ref,)).fetchone()]
            _, inherited, _ = self._freeze_closure(known)
            exposure.update(inherited)
        saved = self._freeze_save(ATTEMPT, {'attempt_id': attempt, 'created_at': self._now(),
            'input_id': capsule['id'], 'status': status, 'manifest_id': manifest,
            'admission': admission, 'failure_type': failure, 'rejected_request': rejected_request,
            'scientific_readiness': False,
            'frozen': False, 'allocation_reserved': False},
            [capsule['id'], *([manifest] if manifest else [])], exposure)
        self._event('controller', 'bound_computation_checked', attempt_id=attempt,
                    artifact_id=saved['id'], status=status)
        return saved

    def _freeze_existing(self, request):
        for capsule in self._freeze_objects(INPUT):
            previous = capsule['body']['request']
            if previous['key'] != request['key']:
                continue
            if previous != request:
                raise Conflict('Freeze key already binds different immutable request content')
            for attempt in reversed(self._freeze_objects(ATTEMPT)):
                if attempt['body']['input_id'] == capsule['id'] and attempt['body']['manifest_id']:
                    return capsule, self._artifact(attempt['body']['manifest_id'])
            return capsule, None
        return None, None

    def _freeze_commit(self, actor, request, capsule, resolution):
        require(type(resolution) is dict and set(resolution) ==
            {'gaps', 'artifact_ids', 'claims', 'outcome_record_ids', 'admission'},
            'Malformed host admission resolution')
        strings(resolution['gaps'], 'admission gaps')
        if resolution['gaps']:
            return None
        require(type(resolution['admission']) is dict, 'Sourced host admission findings required')
        roots = strings(resolution['artifact_ids'], 'admitted artifact identities')
        require(set(capsule['source_refs']) <= set(roots), 'Admission omitted request dependencies')
        claims = resolution['claims']
        require(type(claims) is list and len(claims) == len(request['plan_ids']),
                'Full predeclared family is required')
        for claim in claims:
            require(type(claim) is dict and set(claim) == {'claim_id', 'plan_id', 'compiled_id'},
                    'Malformed admitted scientific claim')
            require(type(claim['claim_id']) is str and re.fullmatch('[0-9a-f]{64}', claim['claim_id']),
                    'Exact semantic claim identity required')
            require(claim['plan_id'] in roots and claim['compiled_id'] in roots,
                    'Claim dependencies omitted from closure')
        require([claim['plan_id'] for claim in claims] == request['plan_ids'] and
                len({claim['claim_id'] for claim in claims}) == len(claims),
                'Duplicate claims or changed family membership')
        # Preparation counts are provisional. Bind the complete admitted family
        # without rewriting its draft plans or trusting a caller's allocation.
        policy_binding = {'family_policy_binding_version': FAMILY_BINDING,
                          'family_policy': family_budget(len(claims))}
        records = strings(resolution['outcome_record_ids'], 'qualified outcome records')
        require(bool(records), 'Exact qualified outcome records required')
        closure, exposure, blobs = self._freeze_closure(roots)
        for identity in blobs:
            self._read_blob_bytes(identity)
        exposure = sorted(set(exposure) | set(capsule['exposure']) | {capsule['id']})
        strings(exposure, 'complete freeze exposure')
        signature = {'campaign_id': request['campaign_id'], 'role': request['role'],
            'claims': claims, **policy_binding,
            'selection_record_ref': request['selection_record_ref'],
            'reservation_spec_ref': request['reservation_spec_ref'],
            'outcome_record_ids': sorted(records), 'closure': closure,
            'admission': resolution['admission']}
        for allocation in self._freeze_objects(ALLOCATION):
            old = allocation['body']
            if old['signature'] == signature:
                manifests = [item for item in self._freeze_objects(MANIFEST)
                             if item['body']['allocation_id'] == allocation['id']]
                require(len(manifests) == 1, 'Incomplete existing atomic commitment')
                return manifests[0]
            if old['campaign_id'] == request['campaign_id'] and old['role'] == request['role']:
                raise Conflict('Campaign batch is already frozen; no late membership or budget refund')
            if set(old['outcome_record_ids']) & set(records):
                raise Conflict('Qualified outcome records are already reserved by another batch')
        old_claims = {item['body']['claim_id'] for item in self._freeze_objects(TRIAL)}
        if old_claims & {claim['claim_id'] for claim in claims}:
            raise Conflict('Exact duplicate claim must link its existing frozen batch')
        require(request['role'] == 'primary', 'Qualified corroboration pre-reservation is not implemented')
        allocation = self._freeze_save(ALLOCATION, {'created_at': self._now(),
            'contract': 'research-contract/1.0', 'campaign_id': request['campaign_id'],
            'role': request['role'], 'signature': signature, 'outcome_record_ids': sorted(records),
            'primary_count': len(claims), **policy_binding, 'refund_permitted': False},
            [capsule['id'], *closure], exposure, blobs=blobs)
        trials = [self._freeze_save(TRIAL, {'created_at': self._now(), **claim,
            'allocation_id': allocation['id'], 'contract': 'research-contract/1.0',
            **policy_binding,
            'scientific_readiness': True, 'frozen': True, 'assessment_access_authority': False},
            [allocation['id'], *closure], exposure)['id'] for claim in claims]
        manifest = self._freeze_save(MANIFEST, {'created_at': self._now(), 'request': request,
            'contract': 'research-contract/1.0', 'input_id': capsule['id'],
            'allocation_id': allocation['id'], 'trial_ids': trials, 'primary_count': len(claims),
            **policy_binding,
            'closure': closure, 'admission': resolution['admission'], 'scientific_readiness': True,
            'frozen': True, 'allocation_reserved': True, 'assessment_access_authority': False},
            [allocation['id'], *trials, *closure], exposure, blobs=blobs)
        self._event(actor['name'], 'scientific_batch_frozen', manifest_id=manifest['id'],
                    allocation_id=allocation['id'], trial_ids=trials)
        return manifest

    def _freeze_scientific_batch_external(self, token, args):
        request = decode(canonical(args))
        with self._mutex:
            actor = self._binding_owner(token)
            require(set(request) == {'key', 'campaign_id', 'role', 'plan_ids',
                'selection_record_ref', 'reservation_spec_ref'}, 'Exact freeze request fields required')
            for name in ('key', 'campaign_id', 'selection_record_ref', 'reservation_spec_ref'):
                text(request[name], name)
            require(request['role'] in ('primary', 'corroboration'), 'Unknown scientific batch role')
            require(1 <= len(strings(request['plan_ids'], 'plan identities')) <= 8,
                    'One through eight unique predeclared plans required')
            try:
                capsule, existing = self._freeze_existing(request)
            except Conflict:
                original = next(item for item in self._freeze_objects(INPUT)
                                if item['body']['request']['key'] == request['key'])
                attempt = uuid.uuid4().hex
                with self._transaction():
                    self._event('controller', 'bound_computation_started', attempt_id=attempt,
                        kind='scientific_freeze', input_ref=original['id'], retained_input_id=original['id'])
                    self._freeze_attempt(attempt, original, 'FAILED', failure='Conflict',
                                         rejected_request=request)
                raise
            if existing is not None:
                return existing  # Immutable history, never renewed execution/access authority.
            require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == LOADED_SELF,
                    'Restart after scientific freeze source changes')
            require(footprint(source_bundle()) == LOADED_PACKAGE,
                    'Restart after scientific freeze package changes')
            roots = [request[name] for name in
                     ('campaign_id', 'selection_record_ref', 'reservation_spec_ref')]
            roots.extend(request['plan_ids'])
            _, exposure, _ = self._freeze_closure(roots)
            attempt = uuid.uuid4().hex
            with self._transaction():
                if capsule is None:
                    bundle = source_bundle()
                    require(footprint(bundle) == LOADED_PACKAGE, 'Freeze source changed during capture')
                    sources = {name: self._stage_blob_bytes(raw) for name, raw in bundle.items()}
                    for descriptor in sources.values():
                        self._register_blob(descriptor)
                    capsule = self._freeze_save(INPUT, {'request': request,
                        'created_at': self._now(), 'checker_sha256': LOADED_SELF,
                        'source_files': sources, 'source_footprint': LOADED_PACKAGE,
                        'runtime_identity': _runtime_identity(),
                        'scientific_readiness': False, 'frozen': False, 'allocation_reserved': False},
                        roots, exposure, blobs=sorted({item['sha256'] for item in sources.values()}))
                self._event('controller', 'bound_computation_started', attempt_id=attempt,
                    kind='scientific_freeze', input_ref=capsule['id'], retained_input_id=capsule['id'])
            try:
                with self._transaction():
                    actor = self._binding_owner(token)
                    require(hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == LOADED_SELF,
                            'Scientific freeze checker changed before commitment')
                    require(capsule['body']['checker_sha256'] == LOADED_SELF and
                            capsule['body']['source_footprint'] == LOADED_PACKAGE and
                            footprint(source_bundle()) == LOADED_PACKAGE and
                            capsule['body']['runtime_identity'] == _runtime_identity(),
                            'Retained freeze checker differs; use a new key for a new source version')
                    files = capsule['body']['source_files']
                    require(set(files) == set(LOADED_PACKAGE) and
                            set(capsule['blob_refs']) == {item['sha256'] for item in files.values()},
                            'Retained freeze source closure differs')
                    for name, descriptor in files.items():
                        raw = self._read_blob_bytes(descriptor['sha256'])
                        require(len(raw) == descriptor['size'] and
                                hashlib.sha256(raw).hexdigest() == LOADED_PACKAGE[name],
                                'Retained freeze source bytes differ')
                    resolution = decode(canonical(self._scientific_freeze_admission(actor, request)))
                    manifest = self._freeze_commit(actor, request, capsule, resolution)
                    if manifest is None:
                        result = self._freeze_attempt(attempt, capsule, 'ADMISSION_GAP', admission=resolution)
                    else:
                        reused = manifest['body']['request']['key'] != request['key']
                        self._freeze_attempt(attempt, capsule, 'REUSED' if reused else 'COMMITTED',
                                             manifest=manifest['id'])
                        result = manifest
                    canonical(result)
                return result
            except BaseException as exc:
                with self._transaction():
                    self._freeze_attempt(attempt, capsule, 'FAILED', failure=type(exc).__name__)
                raise

    def _inspect_scientific_freezes(self, actor, limit=50):
        integer(limit, 'limit', 1)
        require(limit <= 100, 'Freeze inspection limit exceeds 100')
        attempts = self._freeze_objects(ATTEMPT)
        terminal = {item['body']['attempt_id'] for item in attempts}
        incomplete = [item for item in self._bound_attempts()
                      if item['kind'] == 'scientific_freeze' and item['attempt_id'] not in terminal]
        return {'attempts': list(reversed(attempts[-limit:])), 'total': len(attempts),
                'incomplete_attempts': list(reversed(incomplete[-limit:])),
                'scientific_authority': False}
