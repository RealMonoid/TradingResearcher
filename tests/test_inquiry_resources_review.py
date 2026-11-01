"""Independent finite-slot/accounting adversaries; no real provider or model claim."""
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch

from inquiry_resource_support import Fixture, LedgerProvider, fake_post
from trading_researcher.codec import canonical, decode, digest, Invalid
from trading_researcher.auxiliary import request_for
from trading_researcher.errors import Denied
from trading_researcher.inquiry import resources, presentation
from trading_researcher.inquiry.resource_host import FiniteInquiryBroker
from trading_researcher.inquiry.worker import run_research_once
from trading_researcher.openai_provider import CountedOpenAIResponsesProvider, cost_bound, wire_request


class InquiryResourceIndependentReviewTests(unittest.TestCase):
    def setUp(self):
        # Every test fails closed if it accidentally reaches a real HTTP path.
        guard = patch('trading_researcher.openai_provider._post',
                      side_effect=AssertionError('Real HTTP forbidden in independent review'))
        guard.start(); self.addCleanup(guard.stop)

    def fixture(self, **options):
        value = Fixture(**options)
        self.addCleanup(value.close)
        return value

    def claim(self, f, name='first'):
        client = f.clients[name]
        claimed = client.call('claim'); self.assertIsNotNone(claimed)
        lease = claimed['lease']
        profile = client.call('research_call_state', lease=lease)['profile']
        sources = [client.call('read_artifact', lease=lease, artifact_id=n)
                   for n in claimed['context']['artifact_ids']]
        request = {k: profile[k] for k in ('model', 'prompt_version', 'tools', 'generation_parameters')}
        request['messages'] = presentation.initial_messages(profile, name, claimed['spec']['purpose'], sources)
        return client, lease, request

    def reserve(self, client, lease, request, bound=1128, key='review-call'):
        return client.call('reserve_research_call', lease=lease, key=key, request=request,
            input_token_bound=bound, output_token_limit=6000, cost_bound_units=cost_bound(bound, 6000))

    def native(self, f):
        return [dict(row) for row in f.broker._db.execute(
            'SELECT * FROM research_calls WHERE epoch_id=? ORDER BY rowid', (f.epoch,))]

    def fence(self, f):
        return f.op('inspect_research_epoch', epoch_id=f.epoch)['resource_disposition']

    def attempts(self, f):
        return [dict(id=row['id'], **decode(row['envelope'])) for row in f.broker._db.execute(
            "SELECT id,envelope FROM artifacts WHERE "
            "json_extract(envelope,'$.body.schema')='inquiry-input-count-attempt/1' ORDER BY rowid")]

    def verify_attempt_binding(self, f, attempts, spec):
        expected = request_for(spec, f.broker._auxiliary_packet_for_spec(spec))
        config = spec['research_call_profile']['generation_parameters']['openai_responses']
        previous = None
        for index, artifact in enumerate(attempts):
            body = artifact['body']
            self.assertEqual(artifact['creator'], 'controller')
            self.assertEqual(artifact['origin'], 'controller')
            self.assertEqual(artifact['authority'], 'operational_count_attempt_not_inference_or_scientific_evidence')
            self.assertEqual(body['request_sha256'], digest(expected))
            self.assertEqual(body['wire_sha256'], digest(wire_request(expected, config)))
            self.assertEqual(body['epoch_id'], f.epoch)
            self.assertFalse(body['inference_dispatched'])
            self.assertFalse(body['scientific_readiness'])
            self.assertEqual(body['billing'], 'UNVERIFIED_COUNT_SERVICE_NOT_INFERENCE_USAGE')
            now = datetime.fromisoformat(body['at_utc'])
            self.assertEqual(now.utcoffset().total_seconds(), 0)
            if previous is not None: self.assertGreaterEqual(now, previous)
            previous = now
            if index == 0:
                self.assertEqual(body['request'], expected)
                self.assertIsNone(body['attempt_id'])
            else:
                self.assertEqual(body['attempt_id'], attempts[0]['id'])
                self.assertIn(attempts[0]['id'], artifact['source_refs'])

    def finish_first(self, f, intermediate=False):
        f.enqueue_discovery()
        client, lease, request = self.claim(f)
        old = None
        if intermediate:
            old = client.call('record_research', lease=lease, kind='idea',
                content={'text': 'A intermediate, not its accepted final original.'},
                scope={}, source_refs=[])['id']
        intent = self.reserve(client, lease, request)
        output = LedgerProvider(f, 'first').complete(request, 0, 240)
        receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'], **output)
        self.assertTrue(receipt['resource_settlement_verified'])
        saved = client.call('record_research', lease=lease, **output['response']['output']['record'])
        submitted = client.call('submit', lease=lease, artifact_id=saved['id'])
        self.assertTrue(submitted['accepted'])
        f.idea = saved['id']
        return old

    def run_second(self, f):
        with patch('trading_researcher.inquiry.worker._invoke',
                   side_effect=lambda p, r, o, t, c: p.complete(r, o, t)):
            result = run_research_once(f.clients['second'], LedgerProvider(f, 'second'))
        self.assertTrue(result['accepted'], result)
        f.op('release_batch', batch_id=f.batch, target_epoch=2)
        return result['record_ids'][-1]

    def test_native_reservation_rollback_does_not_refund_external_slot(self):
        f = self.fixture(); f.enqueue_discovery()
        client, lease, request = self.claim(f)
        original = resources.reserve
        def after_external_commit(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError('Fixed crash after external slot commit, before registry commit')
        with patch.object(resources, 'reserve', side_effect=after_external_commit), self.assertRaises(RuntimeError):
            self.reserve(client, lease, request)
        self.assertEqual(self.native(f), [])
        self.assertEqual(len(self.fence(f)['calls']), 1)
        with self.assertRaises(Denied): self.reserve(client, lease, request, key='replacement')
        self.assertEqual(self.native(f), [])
        self.assertEqual(len(self.fence(f)['calls']), 1)
        self.assertEqual(f.ledger.snapshot()['charged_nano'], 3956722500)

    def test_copied_registry_cannot_replay_the_external_grant_at_another_path(self):
        f = self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            db = sqlite3.connect(target / 'registry.sqlite3')
            try:
                f.broker._db.backup(db)
            finally:
                db.close()
            shutil.copyfile(f.broker.directory / 'operator.key', target / 'operator.key')
            other = FiniteInquiryBroker(target, provider_routes=f.route)
            try:
                with self.assertRaises(Denied):
                    other.call(other.admin_token, 'inspect_research_epoch', epoch_id=f.epoch)
            finally:
                other.close()
        self.assertFalse(self.fence(f)['revoked'])

    def test_protected_future_holds_accept_exact_cash_boundary_and_reject_one_nano_over(self):
        # Fixed independent arithmetic: 230905000 current + 772002500 later.
        self.assertEqual(cost_bound(68362, 6000), 230905000)
        self.assertEqual(68372*2500+6000*10000 + 29083*2500+32000*10000
                         + 43346*2500+4000*10000, 772002500)
        for extra, accepted in ((40370000, True), (40370001, False)):
            with self.subTest(other_spend=extra):
                f = self.fixture(); f.enqueue_discovery()
                dispatch = f.ledger.reserve('other-authenticated-work', extra, key='other')
                f.ledger.settle(dispatch, extra)
                client, lease, request = self.claim(f)
                if accepted:
                    self.assertTrue(self.reserve(client, lease, request, bound=68362)['dispatch'])
                    self.assertEqual(len(self.fence(f)['calls']), 1)
                else:
                    with self.assertRaises(Denied): self.reserve(client, lease, request, bound=68362)
                    self.assertEqual(self.fence(f)['calls'], [])
                    self.assertEqual(self.native(f), [])

    def test_shared_receipt_identity_and_usage_mismatches_never_release(self):
        for defect in ('native-usage', 'wire-hash', 'foreign-epoch', 'foreign-worker'):
            with self.subTest(defect=defect):
                f = self.fixture(); f.enqueue_discovery()
                client, lease, request = self.claim(f)
                intent = self.reserve(client, lease, request)
                output = LedgerProvider(f, 'first').complete(request, 0, 240)
                dispatch_id = output['response']['aggregate_dispatch_id']
                if defect == 'native-usage':
                    output['usage'] = {'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0}
                elif defect == 'wire-hash':
                    with f.ledger._connect() as db:
                        db.execute('UPDATE dispatches SET request_hash=? WHERE id=?', ('0'*64, dispatch_id))
                else:
                    with f.ledger._connect() as db:
                        meta = decode(db.execute('SELECT body FROM token_metadata WHERE id=?', (dispatch_id,)).fetchone()[0])
                        meta['epoch_id' if defect == 'foreign-epoch' else 'worker'] = 'unrelated'
                        db.execute('UPDATE token_metadata SET body=? WHERE id=?', (canonical(meta), dispatch_id))
                receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'], **output)
                self.assertFalse(receipt['resource_settlement_verified'])
                self.assertEqual(f.op('inspect_research_epoch', epoch_id=f.epoch)['state'], 'halted')
                self.assertEqual(f.ledger.snapshot()['charged_nano'], 3959422500)
                self.assertIsNotNone(self.native(f)[0]['response_id'])
                self.assertEqual(len(self.fence(f)['calls']), 1)

    def test_unknown_shared_charge_keeps_reservation_and_halts(self):
        f = self.fixture(); f.enqueue_discovery()
        client, lease, request = self.claim(f)
        intent = self.reserve(client, lease, request)
        output = LedgerProvider(f, 'first', ledger=False).complete(request, 0, 240)
        output['usage'] = None
        output['response']['token_usage_details'] = {'cached_input_tokens': None, 'reasoning_output_tokens': None}
        public = output['response']; run = f.policy['discovery_run_ids']['first']
        dispatch = f.ledger.reserve(public['wire_request_sha256'], 62820000, key=run+':0', metadata={
            'run_id': run, 'ordinal': 0, 'epoch_id': f.epoch, 'worker': 'first', 'model': public['model_identity']['requested_model'],
            'prompt_version': request['prompt_version'], 'counted_input_tokens': 1000})
        f.ledger.settle(dispatch, None, receipt={'usage': None,
            'token_details': public['token_usage_details']})
        receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'], **output)
        self.assertTrue(receipt['usage_unknown'])
        self.assertFalse(receipt['resource_settlement_verified'])
        self.assertEqual(f.ledger.snapshot()['charged_nano'], 4019542500)
        self.assertEqual(f.ledger.snapshot()['uncertain'], 1)
        self.assertEqual(f.op('inspect_research_epoch', epoch_id=f.epoch)['state'], 'halted')

    def test_only_A_accepted_final_not_intermediate_or_B_is_formalized(self):
        f = self.fixture()
        intermediate = self.finish_first(f, intermediate=True)
        a_final = f.idea; b_final = self.run_second(f)
        for target in (intermediate, b_final):
            f.idea = target
            with self.subTest(target=target), self.assertRaises(Denied):
                f.auxiliary('formalization/v1')
        f.idea = a_final
        spec, _ = f.auxiliary('formalization/v1')
        self.assertEqual(spec['research_inputs']['idea_id'], a_final)
        self.assertEqual(len(self.fence(f)['calls']), 2)

    def test_distinct_reviewer_exact_protocol_and_permanent_revocation(self):
        for defect in ('same-worker', 'changed-review-prompt'):
            f = self.fixture(create=False)
            roles = deepcopy(f.role_profiles)
            if defect == 'same-worker': roles['semantic-review/v1']['worker'] = 'formal'
            else: roles['semantic-review/v1']['profile']['prompt'] += '\nUnbound instruction'
            f.policy = resources.disposition(roles, f.policy['discovery_run_ids'])
            with self.subTest(defect=defect), self.assertRaises(Denied): f.create_epoch()
        f = self.fixture()
        f.op('revoke_research_epoch_budget', epoch_id=f.epoch)
        with self.assertRaises(Denied): f.create_epoch()
        with f.ledger._connect() as db, self.assertRaises(sqlite3.IntegrityError):
            db.execute('UPDATE research_epoch_budget_grants SET revoked=0 WHERE approval=?', (resources.APPROVAL,))
        self.assertTrue(self.fence(f)['revoked'])

    def test_revoked_or_access_denied_auxiliary_never_counts_the_packet(self):
        for reason in ('revoked', 'context-denied'):
            with self.subTest(reason=reason):
                f = self.fixture(); f.discover(); f.auxiliary('formalization/v1')
                lease = f.clients['formal'].call('claim')['lease']
                if reason == 'revoked': f.op('revoke_research_epoch_budget', epoch_id=f.epoch)
                gate = patch.object(f.broker, '_check_feedback_context', side_effect=Denied('Context no longer usable'))
                with patch('trading_researcher.inquiry.dispatch.CountedOpenAIResponsesProvider.reservation') as count:
                    if reason == 'context-denied':
                        with gate, self.assertRaises(Denied):
                            f.clients['formal'].call('invoke_auxiliary_provider', lease=lease, key='denied-count')
                    else:
                        with self.assertRaises(Denied):
                            f.clients['formal'].call('invoke_auxiliary_provider', lease=lease, key='denied-count')
                    count.assert_not_called()
                self.assertEqual(len(self.native(f)), 2)

    def test_revocation_while_counting_stops_before_native_or_provider_dispatch(self):
        f = self.fixture(); f.discover(); f.auxiliary('formalization/v1')
        lease = f.clients['formal'].call('claim')['lease']
        def count_then_revoke(*args):
            f.op('revoke_research_epoch_budget', epoch_id=f.epoch)
            return {'input_token_bound': 1128, 'output_token_limit': 32000,
                    'cost_bound_units': cost_bound(1128, 32000)}
        with patch('trading_researcher.inquiry.dispatch.CountedOpenAIResponsesProvider.reservation',
                   side_effect=count_then_revoke), patch('trading_researcher.inquiry.dispatch._invoke') as invoke:
            with self.assertRaises(Denied):
                f.clients['formal'].call('invoke_auxiliary_provider', lease=lease, key='count-race')
            invoke.assert_not_called()
        self.assertEqual(len(self.native(f)), 2)
        self.assertEqual(len(self.fence(f)['calls']), 2)

    def test_single_use_discovery_stops_before_any_successor_count(self):
        f = self.fixture(); f.enqueue_discovery()
        provider = LedgerProvider(f, 'first')
        complete = provider.complete
        def tools_once(request, ordinal, timeout):
            output = complete(request, ordinal, timeout)
            output['response']['output'] = {'status': 'tools', 'calls': [
                {'id': 'capability', 'name': 'capabilities', 'arguments': {}}]}
            return output
        with patch.object(provider, 'complete', side_effect=tools_once), \
                patch.object(provider, 'reservation', wraps=provider.reservation) as count, \
                patch('trading_researcher.inquiry.worker._invoke', side_effect=lambda p, r, o, t, c: p.complete(r, o, t)):
            result = run_research_once(f.clients['first'], provider)
        self.assertFalse(result['accepted'])
        self.assertEqual(count.call_count, 1)
        self.assertEqual(len(self.native(f)), 1)
        self.assertEqual(len(self.fence(f)['calls']), 1)
        self.assertIn('no successor count or call', f.op('inspect', job_id=f.jobs['first'])['detail']['reason'])
        # Scripted capabilities can be retained, but this is no model F1/DQ pass.

    def test_counted_controller_uses_frozen_formal_role_not_discovery_route_config(self):
        f = self.fixture(); f.discover(); f.auxiliary('formalization/v1')
        lease = f.clients['formal'].call('claim')['lease']
        post, sent = fake_post({'status': 'final', 'candidate': None, 'semantic_report': {}})
        with patch('trading_researcher.openai_provider._post', side_effect=post), \
                patch('trading_researcher.inquiry.dispatch._invoke', side_effect=lambda p, r, o, t, c: p.complete(r, o, t)):
            result = f.clients['formal'].call('invoke_auxiliary_provider', lease=lease, key='formal-counted')
        self.assertEqual(result['state'], 'recorded')
        self.assertTrue(result['receipt']['resource_settlement_verified'])
        self.assertEqual([name for name, _ in sent], ['/v1/responses/input_tokens', '/v1/responses/input_tokens', '/v1/responses'])
        for _, payload in sent:
            self.assertEqual(payload['reasoning'], {'effort': 'high'})
        self.assertEqual(sent[-1][1]['max_output_tokens'], 32000)
        row = self.native(f)[-1]
        request = f.op('get_artifact', artifact_id=row['request_id'])['body']['request']
        self.assertEqual(request['messages'][0]['content'], f.role_profiles['formalization/v1']['profile']['prompt'])
        self.assertEqual(sent[0][1]['input'], sent[-1][1]['input'])
        self.assertIn(f.idea, canonical(sent[-1][1]['input']))
        attempts = self.attempts(f)
        self.assertEqual([a['body']['state'] for a in attempts], ['STARTED', 'OBSERVED'])
        inputs = f.broker._db.execute('SELECT input_id FROM provider_invocations WHERE call_id=?', (row['id'],)).fetchone()
        invocation = f.op('get_artifact', artifact_id=inputs['input_id'])
        self.assertEqual(invocation['body']['input_count_attempt_id'], attempts[0]['id'])
        self.assertEqual(invocation['body']['input_count_observation_id'], attempts[1]['id'])
        self.assertTrue({a['id'] for a in attempts} <= set(invocation['source_refs']))
        # This retains a synthetic null output solely to qualify transport/accounting;
        # no formalization was submitted, accepted, or given scientific authority.

    def test_count_observation_survives_revocation_source_or_lease_denial(self):
        for mode in ('revoked', 'source-drift', 'lease-expired'):
            with self.subTest(mode=mode):
                f = self.fixture(); f.discover()
                spec, _ = f.auxiliary('formalization/v1')
                lease = f.clients['formal'].call('claim')['lease']
                original_sources = presentation.source_identity()
                changed = False; posts = []
                original_clock = f.broker.clock
                def source_identity():
                    return {**original_sources, 'trading_researcher/after_count.py': '0'*64} \
                        if changed and mode == 'source-drift' else original_sources
                def clock():
                    return int(time.time()) + 601 if changed and mode == 'lease-expired' else original_clock()
                def counted(endpoint, payload, key, deadline):
                    nonlocal changed
                    posts.append(endpoint)
                    self.assertEqual(endpoint, '/v1/responses/input_tokens')
                    if mode == 'revoked': f.op('revoke_research_epoch_budget', epoch_id=f.epoch)
                    changed = True
                    return {'object': 'response.input_tokens', 'input_tokens': 1000}, 'synthetic-retained-count'
                with patch.object(presentation, 'source_identity', side_effect=source_identity), \
                        patch.object(f.broker, 'clock', side_effect=clock), \
                        patch('trading_researcher.openai_provider._post', side_effect=counted), \
                        patch('trading_researcher.inquiry.dispatch._invoke') as invoke:
                    with self.assertRaises(Denied):
                        f.clients['formal'].call('invoke_auxiliary_provider', lease=lease, key='denied-after-count')
                    invoke.assert_not_called()
                attempts = self.attempts(f)
                self.assertEqual([a['body']['state'] for a in attempts], ['STARTED', 'OBSERVED', 'FAILED'])
                self.verify_attempt_binding(f, attempts, spec)
                for artifact in attempts[1:]:
                    receipt = artifact['body']['count_receipts'][0]
                    self.assertEqual(receipt['counted_input_tokens'], 1000)
                    self.assertEqual(receipt['input_token_bound'], 1128)
                    self.assertEqual(receipt['wire_request_sha256'], artifact['body']['wire_sha256'])
                    self.assertEqual(receipt['transport_request_id'], 'synthetic-retained-count')
                self.assertEqual(posts, ['/v1/responses/input_tokens'])
                self.assertEqual(len(self.native(f)), 2)
                self.assertEqual(len(self.fence(f)['calls']), 2)
                self.assertEqual(f.op('inspect_research_epoch', epoch_id=f.epoch)['state'], 'halted')
                self.assertEqual(f.ledger.snapshot()['charged_nano'], 3962122500)
                with patch('trading_researcher.openai_provider._post') as repeated:
                    with self.assertRaises(Denied):
                        f.clients['formal'].call('invoke_auxiliary_provider', lease=lease, key='no-count-retry')
                    repeated.assert_not_called()
                self.assertEqual(len(self.attempts(f)), 3)

    def test_unknown_count_failure_retains_start_error_and_halt_without_retry(self):
        f = self.fixture(); f.discover()
        spec, _ = f.auxiliary('formalization/v1')
        lease = f.clients['formal'].call('claim')['lease']
        with patch('trading_researcher.openai_provider._post', side_effect=TimeoutError('Synthetic unknown count')), \
                patch('trading_researcher.inquiry.dispatch._invoke') as invoke:
            with self.assertRaises(TimeoutError):
                f.clients['formal'].call('invoke_auxiliary_provider', lease=lease, key='unknown-count')
            invoke.assert_not_called()
        attempts = self.attempts(f)
        self.assertEqual([a['body']['state'] for a in attempts], ['STARTED', 'FAILED'])
        self.verify_attempt_binding(f, attempts, spec)
        self.assertEqual(attempts[1]['body']['error_type'], 'TimeoutError')
        self.assertEqual(attempts[1]['body']['count_receipts'], [])
        self.assertEqual(len(self.native(f)), 2)
        self.assertEqual(len(self.fence(f)['calls']), 2)
        self.assertEqual(f.op('inspect_research_epoch', epoch_id=f.epoch)['state'], 'halted')
        self.assertEqual(f.ledger.snapshot()['charged_nano'], 3962122500)
        with patch('trading_researcher.openai_provider._post') as repeated:
            with self.assertRaises(Denied):
                f.clients['formal'].call('invoke_auxiliary_provider', lease=lease, key='no-unknown-count-retry')
            repeated.assert_not_called()

    def test_discovery_count_lease_loss_returns_receipt_without_stale_block_exception(self):
        f = self.fixture(); f.enqueue_discovery()
        provider = CountedOpenAIResponsesProvider(f.key, f.ledger.path, f.config,
            run_id=f.policy['discovery_run_ids']['first'], epoch_id=f.epoch, worker='first')
        clock = f.broker.clock; counted = False
        def host_clock():
            return clock() + 601 if counted else clock()
        def count(endpoint, payload, key, deadline):
            nonlocal counted
            self.assertEqual(endpoint, '/v1/responses/input_tokens')
            counted = True
            return {'object': 'response.input_tokens', 'input_tokens': 1000}, 'synthetic-discovery-late-count'
        with patch.object(f.broker, 'clock', side_effect=host_clock), \
                patch('trading_researcher.openai_provider._post', side_effect=count), \
                patch('trading_researcher.inquiry.worker._invoke') as invoke:
            result = run_research_once(f.clients['first'], provider)
            invoke.assert_not_called()
        self.assertFalse(result['accepted'])
        self.assertEqual(result['input_count_receipts'][0]['transport_request_id'], 'synthetic-discovery-late-count')
        self.assertEqual(self.native(f), [])
        self.assertEqual(self.fence(f)['calls'], [])
        self.assertEqual(f.ledger.snapshot()['charged_nano'], 3956722500)


if __name__ == '__main__':
    unittest.main()
