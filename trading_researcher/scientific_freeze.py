"""Atomic scientific commitments with a deliberately fail-closed admission owner.

Operator inputs are references, never scientific verdicts. Synthetic transaction
tests replace the private admission resolver, not any public scientific policy.
"""
import hashlib
from copy import deepcopy
from pathlib import Path
import re
import uuid

from .codec import Invalid, canonical, decode, digest, integer, strings, text
from .errors import Conflict, Denied
from .evaluation_plans import source_bundle, footprint
from .evaluation_policy import family_budget
from .outcome_reservations import (PROFILE as RESERVATION_PROFILE, merge_grids,
                                   overlapping_events, reservation_for_plans)
from .certification import _runtime_identity
from .data import PARTITIONS, window
from .outcomes import _instant

INPUT = 'scientific-freeze-input/1'
ATTEMPT = 'scientific-freeze-attempt/1'
MANIFEST = 'frozen-manifest/1'
TRIAL = 'scientific-trial/1'
ALLOCATION = 'scientific-allocation/1'
FAMILY_BINDING = 'scientific-family-policy-binding/1'
AUTHORITY = 'scientific_commitment_not_execution_or_release_permission'
PREREQUISITE_CLOSURE = 'scientific-prerequisite-closure/1'
PREREQUISITE_LIMITS = {'transitive_items': 4094, 'retained_exposure_items': 4096,
                       'successful_commit_items': 256}
LOADED_SELF = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
LOADED_PACKAGE = footprint(source_bundle())


def require(condition, message):
    if not condition:
        raise Invalid(message)


def closure_strings(value, name, maximum):
    """Bound complete private provenance without changing public reference lists."""
    require(type(value) is list and len(value) <= maximum,
            f'{name} exceeds its complete provenance envelope')
    for identity in value:
        text(identity, name)
    require(len(set(value)) == len(value), f'{name} contains duplicates')
    canonical(value)  # The existing 1 MiB bound also applies to each complete set.
    return value


class ScientificFreeze:
    def _freeze_objects(self, schema):
        return [self._artifact(row[0]) for row in self._db.execute(
            """SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?
            AND json_extract(envelope,'$.creator')='controller'
            AND json_extract(envelope,'$.origin')='controller' ORDER BY rowid""", (schema,))]

    def _freeze_closure(self, roots, *, prerequisite=False):
        # Read-only prerequisites need the genuine input ancestry, which DATA.md
        # already permits to exceed one direct reference list. Reserve two nodes
        # for the input/attempt. Successful commitments retain their old limit.
        maximum = PREREQUISITE_LIMITS['transitive_items'] if prerequisite else 256
        pending, artifacts, exposure, blobs = set(roots), set(), set(roots), set()
        known_nonartifacts = set()
        while pending:
            identity = pending.pop()
            if identity in artifacts:
                continue
            require(len(artifacts) < maximum, 'Freeze closure exceeds its complete reference envelope')
            artifact = self._artifact(identity)
            artifacts.add(identity)
            exposure.update(artifact['exposure'])
            blobs.update(artifact.get('blob_refs', []))
            require(len(exposure | artifacts) <= maximum and len(blobs) <= maximum,
                    'Freeze provenance collection exceeds its complete reference envelope')
            pending.update(ref for ref in artifact['source_refs'] if ref not in artifacts)
            dependencies = self._technical_dependencies(artifact)
            if dependencies is not None:
                pending.update(ref for ref in dependencies if ref not in artifacts)
            for ref in artifact['exposure']:
                if ref in artifacts or ref in pending or ref in known_nonartifacts:
                    continue
                if self._db.execute('SELECT 1 FROM artifacts WHERE id=?', (ref,)).fetchone():
                    pending.add(ref)
                else:
                    known_nonartifacts.add(ref)
        exposure.update(artifacts)
        closure_strings(sorted(exposure), 'inherited freeze exposure', maximum)
        closure_strings(sorted(blobs), 'freeze blob references', maximum)
        return sorted(artifacts), sorted(exposure), sorted(blobs)

    def _scientific_freeze_admission(self, actor, request):
        """Current preparation/count checks cannot issue scientific admission.

        Complete this owner against actual calibration/information and scientific
        data/selection prerequisites before any real batch can freeze. No caller
        flag, source schema or private-plan qualification substitutes for them.
        """
        gaps = ['SCIENTIFIC_SELECTION_AND_RESERVATION_NOT_QUALIFIED',
                'SCIENTIFIC_EXPOSURE_AND_PRIOR_USE_NOT_QUALIFIED',
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
        try:
            reservation = reservation_for_plans(self, actor, request['plan_ids'])
            roots.extend(reservation['artifact_ids'])
            if reservation['grid']['event_count'] == 0:
                gaps.append('NO_POTENTIAL_OUTCOME_EVENTS')
        except (Invalid, Denied, Conflict, KeyError, TypeError, OSError, ValueError) as exc:
            reservation = {'profile': RESERVATION_PROFILE, 'status': 'RESERVATION_GAP',
                'identity_version': 'UNKNOWN', 'failure_type': type(exc).__name__,
                'raw_input_membership': 'NOT_QUALIFIED',
                'dependence_exposure_prior_use': 'NOT_QUALIFIED',
                'scientific_readiness': False}
            gaps.append('OUTCOME_RESERVATION_METADATA_NOT_QUALIFIED')
        data = self._freeze_data_prerequisite(actor, request)
        roots.extend(data['artifact_ids'])
        if data['gaps']:
            gaps.append('SCIENTIFIC_DATA_PREREQUISITE_NOT_QUALIFIED')
        # Data custody and the declared historical scenario can qualify before
        # selection, prior use and dependence. Their combined admission remains
        # closed until its separate exposure owner is actually implemented.
        if data['gaps'] or 'SCIENTIFIC_EXPOSURE_AND_PRIOR_USE_NOT_QUALIFIED' in gaps:
            gaps.append('SCIENTIFIC_DATA_AND_EXPOSURE_NOT_ADMITTED')
        closure, _, _ = self._freeze_closure(roots, prerequisite=True)
        return {'gaps': sorted(set(gaps)), 'artifact_ids': closure, 'claims': [],
                'outcome_record_ids': [], 'outcome_reservation': reservation,
                'admission': {'plan_observations': observations,
                    'outcome_reservation': reservation,
                    'data_prerequisite': data,
                    'qualification': 'Existing preparation checks grant no scientific admission.'}}

    def _freeze_data_prerequisite(self, actor, request):
        """Resolve the exact pre-outcome data prerequisite through its owners.

        This new intended-use check requires current certificates. It neither
        rewrites intact historical qualifications nor treats private preparation
        as scientific admission. Recorded availability remains an assumption;
        actual publication, eligibility and outcome values are not inspected.
        """
        from . import data_use

        plan_ids = strings(request['plan_ids'], 'scientific data plan identities')
        require(1 <= len(plan_ids) <= 8, 'A complete bounded data family is required')
        bindings, gaps, refs = [], [], set(plan_ids)
        expected_partition = {'primary': 'assessment', 'corroboration': 'corroboration'}.get(request['role'])
        for plan_id in plan_ids:
            try:
                require(expected_partition is not None, 'Unsupported scientific data role')
                plan = self._artifact(plan_id)
                require(self._inspect_evaluation_plan(actor, plan_id)['status'] == 'POLICY_DRAFT',
                        'An owned current plan draft is required')
                self._require_usable_dependencies(plan_id)
                plan_request = plan['body']['request']
                assessment_id = plan_request['data_use_assessment_id']
                current = self._plan_data_use_evidence(actor, plan_request)
                require(current is not None and current['status'] == 'QUALIFIED_PRIVATE_PLAN_DATA'
                        and current.get('qualified_protected_target_data_use') == 'SATISFIED',
                        'Exact current protected data prerequisite required')
                self._require_usable_dependencies(assessment_id)
                assessment = self._artifact(assessment_id)
                require(data_use.checker_current(assessment['body']['checker_sha256']),
                        'Data-use checker changed during intended-use inspection')
                compiled, _ = self._composition_inputs(actor, plan_request['compiled_id'])
                body = compiled['body']
                arguments = body['dependency_arguments']
                private = self._checked_target_binding(actor, arguments['data_target_binding_id'])
                resolved = private['body']['resolved']
                public = self._public_data_target(resolved['target_id'])
                snapshot = self._data_snapshot(resolved['data_snapshot_id'])
                manifest = snapshot['body']['manifest']
                universe = public['body']['request']['universe']
                declared_start, declared_end, instruments = window(universe)
                lower, upper = (_instant(value) for value in PARTITIONS[expected_partition])
                require(public['body']['request']['partition'] == resolved['partition']
                        == manifest['partition'] == expected_partition
                        and snapshot['data_class'] == compiled['data_class'] == plan['data_class'] == 'assessment'
                        and lower <= declared_start < declared_end <= upper,
                        'Scientific role and adopted data partition differ')
                require(body['compilation']['request']['universe'] == universe
                        and resolved['declared_universe'] == universe
                        and body['data_snapshot_id'] == snapshot['id'],
                        'Compiled scope differs from the exact predeclared target')
                left, right, available = window(manifest['universe'])
                require(left <= declared_start < declared_end <= right
                        and set(instruments) <= set(available),
                        'Protected snapshot does not cover the declared scope')
                feature_id = arguments['feature_certificate_id']
                reference_id = arguments['reference_certificate_id']
                feature = self._feature_certificate_status(actor, feature_id, data_snapshot_id=snapshot['id'])
                reference = self._reference_certificate_status(actor, reference_id)
                require(feature['status'] == reference['status'] == 'CURRENT'
                        and reference['retained_source_status'] == 'VERIFIED'
                        and feature_id == resolved['feature_certificate_id'],
                        'Scientific data intended use requires current exact certificates')
                findings = assessment['body']['findings']
                scope = findings['scope']
                require(scope['compiled_id'] == compiled['id']
                        and scope['data_snapshot_id'] == snapshot['id']
                        and scope['feature_certificate_id'] == feature_id
                        and scope['feature_definitions_id'] == resolved['private_definitions_id']
                        and scope['catalog_id'] == resolved['private_catalog_id'] == snapshot['body']['catalog_id']
                        and findings['rights']['reviewed_bytes_match'] is True
                        and not data_use.protected_knowledge_gaps(findings['prior_knowledge']),
                        'Qualified data findings differ from their exact owned inputs')
                member = {'plan_id': plan_id, 'compiled_id': compiled['id'],
                    'data_use_assessment_id': assessment_id, 'data_target_binding_id': private['id'],
                    'public_target_id': public['id'], 'data_snapshot_id': snapshot['id'],
                    'feature_certificate_id': feature_id, 'reference_certificate_id': reference_id,
                    'normalization_id': scope['normalization_id'],
                    'feature_definitions_id': resolved['private_definitions_id'],
                    'public_definitions_id': resolved['public_definitions_id'],
                    'catalog_id': resolved['private_catalog_id'], 'public_catalog_id': resolved['public_catalog_id']}
                # Normalization/catalog records are exact provenance, not D083
                # executable versions. Their owning bindings above remain exact.
                for identity in member.values():
                    self._artifact(identity)
                for name in ('plan_id', 'compiled_id', 'data_use_assessment_id',
                             'data_target_binding_id', 'public_target_id', 'data_snapshot_id',
                             'feature_certificate_id', 'reference_certificate_id',
                             'feature_definitions_id', 'public_definitions_id'):
                    self._require_usable_dependencies(member[name])
                refs.update(member.values())
                member.update(status='QUALIFIED_DATA_PREREQUISITE', role=request['role'],
                    partition=expected_partition, declared_universe=deepcopy(universe),
                    data_use_status=current['status'], feature_status=feature['status'], reference_status=reference['status'],
                    data_use_checker_sha256=assessment['body']['checker_sha256'],
                    snapshot_manifest_hash=digest(manifest), compilation_request_hash=digest(body['compilation']['request']),
                    rights=deepcopy(findings['rights']), availability=deepcopy(findings['availability']),
                    evidence_origin=findings['exposure']['evidence_origin'],
                    origin_reason=findings['exposure']['origin_reason'], prior_knowledge_hash=digest(findings['prior_knowledge']))
                bindings.append(member)
            except (Invalid, Denied, Conflict, KeyError, TypeError, OSError, ValueError) as exc:
                gaps.append('DATA_PREREQUISITE_GAP:' + plan_id)
                bindings.append({'plan_id': plan_id, 'status': 'DATA_PREREQUISITE_GAP',
                                 'failure_type': type(exc).__name__})
        return {'schema': 'scientific-data-prerequisite/1',
            'status': 'DATA_PREREQUISITE_GAP' if gaps else 'QUALIFIED_DATA_PREREQUISITE',
            'gaps': sorted(set(gaps)), 'plan_bindings': bindings, 'artifact_ids': sorted(refs),
            'campaign_selection_and_prior_use': 'NOT_ASSESSED',
            'unused_reservation_and_dependence': 'NOT_QUALIFIED', 'evidence_origin': None,
            'protected_target_admission': False, 'scientific_readiness': False, 'assessment_access_authority': False}

    def _freeze_save(self, schema, body, refs, exposure, *, blobs=None):
        refs = sorted(set(refs))
        exposure = sorted(set(exposure) | set(refs))
        strings(refs, 'freeze references')
        closure_strings(exposure, 'freeze exposure', PREREQUISITE_LIMITS['retained_exposure_items'])
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
            _, inherited, _ = self._freeze_closure(known, prerequisite=True)
            exposure.update(inherited)
        saved = self._freeze_save(ATTEMPT, {'attempt_id': attempt, 'created_at': self._now(),
            'prerequisite_closure_profile': PREREQUISITE_CLOSURE,
            'prerequisite_closure_limits': dict(PREREQUISITE_LIMITS),
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
        required = {'gaps', 'artifact_ids', 'claims', 'outcome_record_ids', 'admission'}
        require(type(resolution) is dict and set(resolution) in
            (required, required | {'outcome_reservation'}),
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
        reservation_binding = {}
        trial_reservation_binding = {}
        if 'outcome_reservation' in resolution:
            reservation = resolution['outcome_reservation']
            require(type(reservation) is dict and reservation.get('profile') == RESERVATION_PROFILE
                and reservation.get('status') == 'POTENTIAL_GRID_BOUND'
                and reservation.get('scientific_readiness') is False,
                'Owned potential metadata required; it cannot issue scientific admission')
            bindings = reservation.get('plan_bindings')
            require(type(bindings) is list and len(bindings) == len(claims)
                and all(type(item) is dict for item in bindings),
                'Every admitted plan must retain its potential-event binding')
            require([item['plan_id'] for item in bindings] == request['plan_ids']
                and [item['compiled_id'] for item in bindings] ==
                    [claim['compiled_id'] for claim in claims],
                'Potential-event bindings differ from admitted membership')
            grid = merge_grids([item['grid'] for item in bindings])
            require(grid == reservation.get('grid') and grid['event_count'] > 0,
                'Complete nonempty potential-event union required')
            require(set(strings(reservation.get('artifact_ids'), 'potential-event sources')) <= set(roots),
                'Admission omitted potential-event source bindings')
            reservation_hash = digest(reservation)
            trial_reservation_binding = {'outcome_reservation_version': RESERVATION_PROFILE,
                                         'outcome_reservation_hash': reservation_hash}
            reservation_binding = {**trial_reservation_binding, 'outcome_reservation': reservation}
        else:
            # Retained finite kernel judgments predate D099. The production
            # resolver never grants them scientific admission or a new version.
            require(bool(records), 'Exact qualified outcome records required')
        closure, exposure, blobs = self._freeze_closure(roots)
        for identity in blobs:
            self._read_blob_bytes(identity)
        exposure = sorted(set(exposure) | set(capsule['exposure']) | {capsule['id']})
        strings(exposure, 'complete freeze exposure')
        signature = {'campaign_id': request['campaign_id'], 'role': request['role'],
            'claims': claims, **policy_binding, **reservation_binding,
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
            old_reservation = old.get('outcome_reservation')
            new_reservation = reservation_binding.get('outcome_reservation')
            if (old_reservation is None) != (new_reservation is None):
                raise Conflict('Legacy outcome identities are UNKNOWN; no disjointness may be inferred')
            if new_reservation is not None:
                if overlapping_events(old_reservation['grid'], new_reservation['grid']):
                    raise Conflict('Stable outcome events are already reserved by another batch')
            if set(old['outcome_record_ids']) & set(records):
                raise Conflict('Qualified outcome records are already reserved by another batch')
        old_claims = {item['body']['claim_id'] for item in self._freeze_objects(TRIAL)}
        if old_claims & {claim['claim_id'] for claim in claims}:
            raise Conflict('Exact duplicate claim must link its existing frozen batch')
        require(request['role'] == 'primary', 'Qualified corroboration pre-reservation is not implemented')
        allocation = self._freeze_save(ALLOCATION, {'created_at': self._now(),
            'contract': 'research-contract/1.0', 'campaign_id': request['campaign_id'],
            'role': request['role'], 'signature': signature, 'outcome_record_ids': sorted(records),
            'primary_count': len(claims), **policy_binding, **reservation_binding,
            'refund_permitted': False},
            [capsule['id'], *closure], exposure, blobs=blobs)
        trials = [self._freeze_save(TRIAL, {'created_at': self._now(), **claim,
            'allocation_id': allocation['id'], 'contract': 'research-contract/1.0',
            **policy_binding, **trial_reservation_binding,
            'scientific_readiness': True, 'frozen': True, 'assessment_access_authority': False},
            [allocation['id'], *closure], exposure)['id'] for claim in claims]
        manifest = self._freeze_save(MANIFEST, {'created_at': self._now(), 'request': request,
            'contract': 'research-contract/1.0', 'input_id': capsule['id'],
            'allocation_id': allocation['id'], 'trial_ids': trials, 'primary_count': len(claims),
            **policy_binding, **reservation_binding,
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
                try:
                    with self._transaction():
                        self._event('controller', 'bound_computation_started', attempt_id=attempt,
                            kind='scientific_freeze', input_ref=original['id'], retained_input_id=original['id'])
                        self._freeze_attempt(attempt, original, 'FAILED', failure='Conflict',
                                             rejected_request=request)
                except (Invalid, Denied, Conflict) as retention_failure:
                    # Two individually bounded ancestries need not fit their
                    # union. Retain the exact rejected roots operationally; never
                    # truncate an artifact's inherited exposure to make it fit.
                    with self._transaction():
                        self._event('controller', 'bound_computation_started', attempt_id=attempt,
                            kind='scientific_freeze', input_ref=original['id'], retained_input_id=original['id'])
                        self._event('controller', 'bound_computation_checked', attempt_id=attempt,
                            status='FAILED_RETENTION', failure_type=type(retention_failure).__name__,
                            reason=str(retention_failure)[:2000], rejected_request=request,
                            rejected_request_hash=digest(request), artifact_retained=False)
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
            _, exposure, _ = self._freeze_closure(roots, prerequisite=True)
            attempt = uuid.uuid4().hex
            with self._transaction():
                if capsule is None:
                    bundle = source_bundle()
                    require(footprint(bundle) == LOADED_PACKAGE, 'Freeze source changed during capture')
                    sources = {name: self._stage_blob_bytes(raw) for name, raw in bundle.items()}
                    for descriptor in sources.values():
                        self._register_blob(descriptor)
                    capsule = self._freeze_save(INPUT, {'request': request,
                        'prerequisite_closure_profile': PREREQUISITE_CLOSURE,
                        'prerequisite_closure_limits': dict(PREREQUISITE_LIMITS),
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
                            capsule['body'].get('prerequisite_closure_profile') == PREREQUISITE_CLOSURE and
                            capsule['body'].get('prerequisite_closure_limits') == PREREQUISITE_LIMITS and
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
                      if item['kind'] == 'scientific_freeze' and item['attempt_id'] not in terminal
                      and item['state'] != 'COMPLETED']
        return {'attempts': list(reversed(attempts[-limit:])), 'total': len(attempts),
                'incomplete_attempts': list(reversed(incomplete[-limit:])),
                'scientific_authority': False}
