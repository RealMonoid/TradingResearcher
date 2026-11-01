"""Separate operator entry point for the single finite inquiry allocation."""
import hashlib
import sqlite3

from ..codec import Invalid, canonical
from ..errors import Conflict, Denied
from .host import InquiryBroker
from . import resources, presentation


class FiniteInquiryBroker(InquiryBroker):
    def _finite_inquiry_spec(self, spec):
        identity = spec.get('research_epoch_id')
        return bool(identity and self._epoch(identity)['request'].get(
            'resource_disposition', {}).get('policy') == resources.POLICY)

    def _require_finite_paired(self, spec):
        from ..paired_development import CONTRACT
        if spec.get('research_inputs', {}).get('paired_contract') == CONTRACT:
            if 'feature_certificate_id' not in spec['research_inputs']:
                raise Denied('Finite paired work requires its exact feature availability evidence')
            self._paired_require_qualification()

    def _scalar_expression_contract(self):
        from ..certification import BOUNDED_PINS
        path = 'docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md'
        raw = (presentation.ROOT / path).read_bytes()
        checksum = hashlib.sha256(raw).hexdigest()
        if checksum != BOUNDED_PINS[path]:
            raise Denied('The approved bounded mathematical source changed')
        return {'schema': 'bounded-math/1.0', 'path': path, 'sha256': checksum,
                'text': raw.decode('utf-8')}

    def _breakout_research_sources(self):
        from ..auxiliary_views import activation_contract, REUSE_SCOPE
        mathematical = self._scalar_expression_contract()
        activation = activation_contract(REUSE_SCOPE)
        return {**super()._breakout_research_sources(), resources.SPEC:
                hashlib.sha256((presentation.ROOT / resources.SPEC).read_bytes()).hexdigest(),
                mathematical['path']: mathematical['sha256'], activation['path']: activation['sha256']}

    def _auxiliary_packet_for_spec(self, spec):
        finite = self._finite_inquiry_spec(spec)
        if finite:
            self._require_finite_paired(spec)
        packet = super()._auxiliary_packet_for_spec(spec)
        parameters = spec.get('research_call_profile', {}).get('generation_parameters', {})
        config = parameters.get('openai_responses', {}) if type(parameters) is dict else {}
        if finite and type(config) is dict and 'bounded_math_scope' in config and 'paired_contract' not in packet:
            from ..auxiliary_views import activation_contract
            activation_contract(config['bounded_math_scope'])
            contract = self._scalar_expression_contract()
            if 'expression_contract' in packet and packet['expression_contract'] != contract:
                raise Invalid('Scalar packet mathematical contract differs from its approved source')
            packet = {**packet, 'expression_contract': contract}
        return packet

    def prepare_resource_disposition(self, token, *, role_profiles, discovery_run_ids):
        with self._mutex:
            self._binding_owner(token)
            return resources.disposition(role_profiles, discovery_run_ids)

    def _inquiry_resource_ceiling(self, context, workers, profile, disposition):
        return resources.validate(self, context, workers, profile, disposition)

    def _inquiry_resource_claim(self, epoch):
        resources.claim(self, epoch)

    def _inquiry_resource_existing(self, epoch):
        if resources.inspect(self, epoch)['revoked']:
            raise Denied('The single finite allocation is permanently revoked')

    def _research_spec_check(self, spec):
        from ..paired_development import CONTRACT
        if self._finite_inquiry_spec(spec) and spec.get('research_inputs', {}).get('paired_contract') == CONTRACT:
            # The legacy paired broker whitelists its historical one-use overlays.
            # Keep its ordinary/native checks while this separate entry point
            # enforces the new finite grant and unchanged paired qualification.
            from ..feedback_budget_broker import FeedbackBudgetBroker
            FeedbackBudgetBroker._research_spec_check(self, spec)
            self._inquiry_epoch_current(self._epoch(spec['research_epoch_id']))
            self._require_finite_paired(spec)
        else:
            super()._research_spec_check(spec)
        if 'research_epoch_id' in spec:
            resources.validate_job(self, self._epoch(spec['research_epoch_id']), spec)

    def _research_call_state(self, actor, lease):
        state = super()._research_call_state(actor, lease)
        job = self._owned(actor, lease)
        epoch = self._epoch(job['spec']['research_epoch_id'])
        resources.preflight(self, epoch, job)
        run = epoch['request']['resource_disposition']['discovery_run_ids'].get(actor['name'])
        return {**state, 'finite_resource': {'policy': resources.POLICY, 'max_calls_per_job': 1,
                                           'discovery_run_id': run}}

    def _reserve_research_call(self, actor, lease, key, request, input_token_bound,
                               output_token_limit, cost_bound_units):
        intent = super()._reserve_research_call(actor, lease, key, request, input_token_bound,
                                               output_token_limit, cost_bound_units)
        job = self._owned(actor, lease)
        epoch = self._epoch(job['spec']['research_epoch_id'])
        if intent['dispatch']:
            resources.reserve(self, epoch, job, intent['call_id'], request,
                              input_token_bound, output_token_limit, cost_bound_units)
        else:
            self._inquiry_resource_existing(epoch)
        return intent

    def _settle_research_call(self, actor, lease, call_id, response, usage=None):
        prior = self._db.execute('SELECT state FROM research_calls WHERE id=?', (call_id,)).fetchone()
        receipt = super()._settle_research_call(actor, lease, call_id, response, usage)
        if prior['state'] != 'reserved':
            return receipt
        call = self._db.execute('SELECT epoch_id FROM research_calls WHERE id=?', (call_id,)).fetchone()
        epoch = self._epoch(call['epoch_id'])
        try:
            state = resources.inspect(self, epoch)
            entry = next(item for item in state['calls'] if item['call_id'] == call_id)
            if state['revoked']:
                raise Denied('The allocation was revoked during dispatch')
            with resources._ledger(self)._connect() as db:
                resources.authenticate(self, epoch, entry, db)
            valid, reason = True, None
        except (OSError, sqlite3.Error, ValueError, KeyError, TypeError, StopIteration, Denied, Conflict) as exc:
            valid, reason = False, type(exc).__name__ + ': ' + str(exc)[:240]
        receipt = {**receipt, 'resource_settlement_verified': valid, 'resource_gap': reason}
        self._db.execute('UPDATE research_calls SET receipt=? WHERE id=?', (canonical(receipt), call_id))
        if not valid:
            self._db.execute("UPDATE research_epochs SET state='halted' WHERE id=?", (epoch['id'],))
        self._event('controller', 'inquiry_resource_settlement_checked', call_id=call_id,
                    verified=valid, retained_gap=reason)
        return receipt

    def _research_completion_check(self, job):
        super()._research_completion_check(job)
        if 'research_epoch_id' not in job['spec']:
            return
        epoch = self._epoch(job['spec']['research_epoch_id'])
        state = resources.inspect(self, epoch)
        if state['revoked']:
            raise Denied('Revoked finite allocation cannot complete a research stage')
        calls = [entry for entry in state['calls'] if entry['job_id'] == job['id']]
        if len(calls) != 1:
            raise Denied('One retained authenticated dispatch is required for finite stage completion')
        with resources._ledger(self)._connect() as db:
            resources.authenticate(self, epoch, calls[0], db)

    def _inspect_research_epoch(self, actor, epoch_id):
        result = super()._inspect_research_epoch(actor, epoch_id)
        return {**result, 'resource_disposition': resources.inspect(self, self._epoch(epoch_id))}

    def _revoke_research_epoch_budget(self, actor, epoch_id):
        result = resources.revoke(self, self._epoch(epoch_id))
        self._event(actor['name'], 'inquiry_resource_disposition_revoked', epoch_id=epoch_id)
        return result

    def _invoke_auxiliary_provider_external(self, token, args):
        from .dispatch import invoke_auxiliary
        return invoke_auxiliary(self, token, args)
