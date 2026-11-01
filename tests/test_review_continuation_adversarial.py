"""Independent D092 boundary fixtures; no keys, network, or market data.

Only the four declared deployment identities are substituted for synthetic
objects. Broker ownership, packet construction, accounting, policy inspection,
registry transactions, and the separate temporary spend ledger remain real.
The mocked provider response proves process behavior, not semantic fidelity.
"""
from copy import deepcopy
import unittest
from unittest.mock import patch

import meaning_review_support as support
from test_researcher import LocalClient
from trading_researcher.auxiliary import AuxiliaryResearch, request_for, run_auxiliary_once
from trading_researcher.codec import Invalid, canonical, decode, digest
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.meaning_reviews import profile as review_profile, policy_identity
from trading_researcher import openai_provider as openai
from trading_researcher import review_continuation as continuation
from trading_researcher.storage import restore_bundle


REJECTIONS = (Invalid, Denied, Conflict)


class ReviewContinuationAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.f = support.Fixture()
        self.addCleanup(self.f.close)
        self.case = self.f.formalize()
        self.target = self.case['target']
        self.original_epoch = self.case['epoch']
        self.now = self.f.broker._now()
        original_job = self.f.op('inspect', job_id=self.case['job'])
        self.f.op('release_batch', batch_id=original_job['batch_id'], target_epoch=2)
        self.context = self.f.op('create_context', role='formalizer', epoch=2,
            artifact_ids=[self.target['id'], self.target['body']['idea_id'],
                          self.target['body']['catalog_id']])['id']
        self.reviewer = self.f.op('register_worker', name='independent-continuation',
            role='formalizer', capabilities=['semantic-review/v1'])['token']
        self.config = openai.configuration(input_token_limit=36000, output_token_limit=4000)
        self.ledger_path = self.f.root / 'separate-spend-ledger.sqlite3'
        self.ledger = openai.SpendLedger(self.ledger_path, 5000000000)
        self.routes = {openai.MODEL: {'provider': 'openai',
            'key_file': str(self.f.root / 'deliberately-absent-key'),
            'budget_file': str(self.ledger_path), 'config': self.config}}
        self.restart()
        base = deepcopy(self.f.broker._epoch(self.original_epoch)['request'])
        self.base_context = base['context_id']
        selected = review_profile({**self.case['spec']['research_call_profile'],
            'generation_parameters': {'openai_responses': deepcopy(self.config)},
            'max_output_tokens': 4000, 'call_timeout_seconds': 600, 'max_retries': 0})
        self.spec = {**deepcopy(self.case['spec']), 'kind': 'semantic-review/v1',
            'context_id': self.context, 'allowed_workers': ['independent-continuation'],
            'max_attempts': 1, 'lease_seconds': 600, 'deadline': self.now + 600,
            'research_call_profile': selected, 'dependencies': [self.case['job']],
            'research_inputs': {'formalization_id': self.target['id'], 'definition_ids': []}}
        self.packet = AuxiliaryResearch._auxiliary_packet_for_spec(self.f.broker, self.spec)
        self.profile = {**base['profile'], 'max_calls': 1, 'max_tokens': 40000,
            'max_seconds': 600, 'max_cost_units': 150000000,
            'generation_parameters': deepcopy(selected['generation_parameters']),
            'max_output_tokens': 4000, 'call_timeout_seconds': 600, 'max_retries': 0}
        for name, value in {'TARGET': self.target['id'], 'ORIGINAL_EPOCH': self.original_epoch,
                'ORIGINAL_USAGE': self.f.broker._call_usage(self.original_epoch),
                'WIRE_SHA256': digest(openai.wire_request(request_for(self.spec, self.packet), self.config))}.items():
            replacement = patch.object(continuation, name, value)
            replacement.start()
            self.addCleanup(replacement.stop)

    def restart(self):
        directory = self.f.broker.directory
        self.f.broker.close()
        self.f.broker = Broker(directory, clock=lambda: self.now, provider_routes=self.routes)
        self.f.token = self.f.broker.admin_token

    def args(self, key='single-review', **changes):
        result = {'key': key, 'context_id': self.base_context, 'workers': ['first', 'second'],
            'profile': deepcopy(self.profile), 'review_continuation': {
                'policy': continuation.POLICY, 'spec': continuation.template(deepcopy(self.spec))}}
        result.update(changes)
        return result

    def create(self, **changes):
        return self.f.op('create_research_epoch', **self.args(**changes))['id']

    def enqueue(self, epoch, key='one-review-job', **changes):
        spec = {**deepcopy(self.spec), 'research_epoch_id': epoch, **changes}
        identity = self.f.op('enqueue', key=key, spec=spec)['id']
        return identity, spec

    def claim(self, epoch):
        job, spec = self.enqueue(epoch)
        claim = self.f.broker.call(self.reviewer, 'claim')
        self.assertEqual(claim['lease']['job_id'], job)
        return claim['lease'], spec

    def reserve(self, lease, spec, key='single-call', **changes):
        request = request_for(spec, self.f.broker._auxiliary_packet_for_spec(spec))
        args = {'lease': lease, 'key': key, 'request': request, 'input_token_bound': 36000,
            'output_token_limit': 4000, 'cost_bound_units': openai.cost_bound(36000, 4000)}
        return self.f.broker.call(self.reviewer, 'reserve_research_call', **{**args, **changes})

    def grant_count(self):
        with self.ledger._connect() as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='research_epoch_budget_grants'").fetchone():
                return 0
            return db.execute('SELECT COUNT(*) FROM research_epoch_budget_grants WHERE approval=?',
                              (continuation.APPROVAL,)).fetchone()[0]

    def test_real_cross_epoch_process_preserves_packet_epochs_and_historical_review(self):
        before = canonical(self.target)
        usage = self.f.broker._call_usage(self.original_epoch)
        epoch = self.create()
        job, spec = self.enqueue(epoch)
        self.assertNotEqual(epoch, self.original_epoch)
        self.assertEqual(self.f.broker._auxiliary_packet_for_spec(spec), self.packet)
        output = {'status': 'final', 'review': {'judgment': 'faithful',
            'reason': 'Synthetic independent process assertion, not model-quality evidence.',
            'added_assumptions': [], 'omitted_assumptions': [], 'conflicts': [], 'unresolved_meaning': [],
            'mapping_checks': [{'segment': 0, 'judgment': 'faithful', 'reason': 'Synthetic mapping.'}]}}
        with patch('trading_researcher.controller_providers._invoke',
                   return_value=self.f.result({'output': output})) as provider:
            outcome = run_auxiliary_once(LocalClient(self.f.broker, self.reviewer))
        self.assertTrue(outcome['accepted'], outcome)
        self.assertEqual(provider.call_count, 1)
        assessed = self.f.op('assess_meaning_review', key='actual-process', formalization_id=self.target['id'])
        self.assertEqual(assessed['body']['independent_semantic_review'], 'SATISFIED', assessed['body'])
        self.assertFalse(assessed['body']['scientific_readiness'])
        inventory = assessed['body']['inventory']
        self.assertEqual(inventory['jobs'][0]['spec']['research_epoch_id'], epoch)
        self.assertEqual(inventory['jobs'][0]['calls'][0]['epoch_id'], epoch)
        self.assertEqual(inventory['policy']['continuation'], continuation.POLICY)
        self.assertEqual(self.f.broker._call_usage(self.original_epoch), usage)
        self.assertEqual(canonical(self.f.op('get_artifact', artifact_id=self.target['id'])), before)
        self.f.op('revoke_research_epoch_budget', epoch_id=epoch)
        self.now += 3600
        self.restart()
        status = self.f.op('inspect_meaning_review', assessment_id=assessed['id'])
        self.assertEqual((status['status'], status['independent_semantic_review']), ('CURRENT', 'SATISFIED'))
        again = self.f.op('assess_meaning_review', key='after-closure', formalization_id=self.target['id'])
        self.assertEqual(again['body']['independent_semantic_review'], 'SATISFIED')

    def test_legacy_policy_and_sources_remain_exact(self):
        self.assertEqual(policy_identity()['sources'], continuation.LEGACY_SOURCES)
        self.assertEqual(self.f.broker._auxiliary_packet_for_spec(self.spec), self.packet)
        inventory, _ = self.f.broker._meaning_inventory(self.target)
        self.assertEqual(inventory['policy'], policy_identity())
        assessed = self.f.op('assess_meaning_review', key='legacy-gap', formalization_id=self.target['id'])
        self.assertEqual(assessed['body']['gaps'][0]['code'], 'NO_REVIEW_REGISTERED')
        self.assertEqual(self.f.op('inspect_meaning_review', assessment_id=assessed['id'])['status'], 'CURRENT')
        from trading_researcher.controller_providers import source_hashes
        self.assertIn('review_continuation.py', source_hashes('openai'))

    def test_ordinary_cross_epoch_and_worker_activation_are_denied(self):
        args = self.args(); args.pop('review_continuation')
        epoch = self.f.op('create_research_epoch', **args)['id']
        with self.assertRaises(REJECTIONS):
            self.enqueue(epoch)
        with self.assertRaises(Denied):
            self.f.broker.call(self.reviewer, 'create_research_epoch', **self.args(key='forged'))
        with self.assertRaises(Denied):
            self.f.broker.call(self.reviewer, 'revoke_research_epoch_budget', epoch_id=epoch)
        self.assertEqual(self.grant_count(), 0)

    def test_malformed_nested_grants_fail_with_typed_errors_before_claim(self):
        for field in ('research_inputs', 'research_call_profile'):
            for value in (None, [], 'malformed', 7):
                args = self.args()
                args['review_continuation']['spec'][field] = value
                with self.subTest(field=field, value=value), self.assertRaises(REJECTIONS):
                    self.f.op('create_research_epoch', **args)
        self.assertEqual(self.grant_count(), 0)

    def test_full_invalid_job_template_is_rejected_before_irreversible_claim(self):
        args = self.args()
        args['review_continuation']['spec']['unexpected'] = 'not a supported job field'
        with self.assertRaises(REJECTIONS):
            self.f.op('create_research_epoch', **args)
        self.assertEqual(self.grant_count(), 0)
        for field, value in (('purpose', None), ('lease_seconds', 1),
                             ('dependencies', ['unregistered-job']), ('max_attempts', True)):
            args = self.args()
            args['review_continuation']['spec'][field] = value
            with self.subTest(field=field), self.assertRaises(REJECTIONS):
                self.f.op('create_research_epoch', **args)
        self.f.op('register_worker', name='not-a-reviewer',
            role='formalizer', capabilities=['formalization/v1'])
        args = self.args()
        args['review_continuation']['spec']['allowed_workers'] = ['not-a-reviewer']
        with self.assertRaises(REJECTIONS):
            self.f.op('create_research_epoch', **args)
        self.assertEqual(self.grant_count(), 0)

    def test_limits_prompt_role_and_wire_tampering_cannot_consume_claim(self):
        edits = [('profile', 'max_calls', 2), ('profile', 'max_tokens', 40001),
            ('profile', 'max_seconds', 601), ('profile', 'max_cost_units', 150000001),
            ('profile', 'max_output_tokens', 3999), ('profile', 'max_retries', 1),
            ('spec', 'kind', 'formalization/v1'), ('spec', 'max_attempts', 2),
            ('spec', 'allowed_workers', [self.target['creator']])]
        for part, field, value in edits:
            args = self.args()
            target = args['profile'] if part == 'profile' else args['review_continuation']['spec']
            target[field] = value
            with self.subTest(part=part, field=field), self.assertRaises(REJECTIONS):
                self.f.op('create_research_epoch', **args)
        args = self.args()
        args['review_continuation']['spec']['research_call_profile']['prompt'] += ' Change the conclusion.'
        with self.assertRaises(REJECTIONS):
            self.f.op('create_research_epoch', **args)
        with patch.object(continuation, 'WIRE_SHA256', '0' * 64), self.assertRaises(REJECTIONS):
            self.create()
        with patch.object(continuation, 'ORIGINAL_USAGE', {'calls': 0, 'tokens': 0, 'cost_units': 0}), self.assertRaises(REJECTIONS):
            self.create()
        with patch.object(continuation, 'SPEC_SHA256', '0' * 64), self.assertRaises(REJECTIONS):
            self.create()
        self.assertEqual(self.grant_count(), 0)
        self.create()

    def test_claim_is_idempotent_and_cannot_be_reissued_after_restart(self):
        epoch = self.create()
        self.assertEqual(self.create(), epoch)
        self.restart()
        self.assertEqual(self.create(), epoch)
        with self.assertRaises(REJECTIONS):
            self.create(key='second-claim')
        self.assertEqual(self.grant_count(), 1)

    def test_registry_rollback_consumes_external_claim(self):
        original_event = self.f.broker._event
        def fail(actor, event, **fields):
            if event == 'research_epoch_created':
                raise RuntimeError('independent injected failure after external claim')
            return original_event(actor, event, **fields)
        with patch.object(self.f.broker, '_event', side_effect=fail), self.assertRaises(RuntimeError):
            self.create()
        self.assertEqual(self.grant_count(), 1)
        self.assertIsNone(self.f.broker._db.execute("SELECT id FROM research_epochs WHERE request_key='single-review'").fetchone())
        with self.assertRaises(REJECTIONS):
            self.create()

    def test_only_exact_single_job_and_reservation_fit(self):
        epoch = self.create()
        for changed in ({'allowed_workers': [self.target['creator']]}, {'max_attempts': 2},
                        {'kind': 'formalization/v1'}, {'context_id': self.case['spec']['context_id']}):
            with self.subTest(change=changed), self.assertRaises(REJECTIONS):
                self.enqueue(epoch, **changed)
        lease, spec = self.claim(epoch)
        with self.assertRaises(REJECTIONS):
            self.enqueue(epoch, key='another-job')
        for changed in ({'input_token_bound': 36001}, {'output_token_limit': 3999},
                        {'cost_bound_units': 1}):
            with self.subTest(change=changed), self.assertRaises(REJECTIONS):
                self.reserve(lease, spec, **changed)
        call = self.reserve(lease, spec)
        self.assertTrue(call['dispatch'])
        repeat = self.reserve(lease, spec)
        self.assertFalse(repeat['dispatch'])
        self.assertEqual(repeat['call_id'], call['call_id'])
        self.f.broker.call(self.reviewer, 'finish_research_call', lease=lease,
            call_id=call['call_id'], response={'status': 'failed'},
            usage={'input_tokens': 1, 'output_tokens': 0, 'cost_units': 1})
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, spec, key='refund-must-not-create-another-call')

    def test_reservation_rollback_does_not_refund_the_external_slot(self):
        epoch = self.create(); lease, spec = self.claim(epoch)
        original_event = self.f.broker._event
        def fail(actor, event, **fields):
            if event == 'provider_call_reserved':
                raise RuntimeError('independent failure after external reservation')
            return original_event(actor, event, **fields)
        with patch.object(self.f.broker, '_event', side_effect=fail), self.assertRaises(RuntimeError):
            self.reserve(lease, spec)
        self.assertEqual(self.f.broker._call_usage(epoch)['calls'], 0)
        with self.assertRaises(REJECTIONS):
            self.f.op('inspect_research_epoch', epoch_id=epoch)
        with self.ledger._connect() as db:
            calls = db.execute('SELECT calls FROM research_epoch_budget_grants WHERE approval=?',
                               (continuation.APPROVAL,)).fetchone()[0]
        self.assertEqual(len(decode(calls)), 1)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, spec)

    def test_revoke_blocks_new_dispatch_but_allows_existing_accounting(self):
        epoch = self.create(); lease, spec = self.claim(epoch)
        call = self.reserve(lease, spec)
        self.f.op('revoke_research_epoch_budget', epoch_id=epoch)
        self.assertFalse(self.reserve(lease, spec)['dispatch'])
        receipt = self.f.broker.call(self.reviewer, 'finish_research_call', lease=lease,
            call_id=call['call_id'], response={'status': 'failed'}, usage=None)
        self.assertTrue(receipt['usage_unknown'])
        self.assertEqual(self.f.broker._call_usage(epoch)['tokens'], 40000)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, spec, key='forbidden-new-call')

    def test_revocation_before_call_and_epoch_expiry_fail_closed(self):
        epoch = self.create(); lease, spec = self.claim(epoch)
        self.f.op('revoke_research_epoch_budget', epoch_id=epoch)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, spec)
        self.now += 601
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, spec)
        self.assertEqual(self.f.broker._call_usage(epoch)['calls'], 0)

    def test_pending_or_unknown_shared_spend_blocks_claim(self):
        identity = self.ledger.reserve('unrelated-temporary-test-call', 1)
        with self.assertRaises(REJECTIONS):
            self.create()
        self.ledger.settle(identity, None)
        with self.assertRaises(REJECTIONS):
            self.create()
        self.assertEqual(self.grant_count(), 0)

    def test_pending_shared_spend_after_claim_blocks_new_reservation(self):
        epoch = self.create(); lease, spec = self.claim(epoch)
        self.ledger.reserve('another-independent-pending-call', 1)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, spec)
        self.assertEqual(self.f.broker._call_usage(epoch)['calls'], 0)

    def test_all_related_incomplete_reviews_remain_visible_in_extended_inventory(self):
        old_review = self.f.review(self.case, run=False)
        epoch = self.create()
        new_job, _ = self.enqueue(epoch)
        inventory, _ = self.f.broker._meaning_inventory(self.target)
        self.assertEqual({job['id'] for job in inventory['jobs']}, {old_review['job'], new_job})
        self.assertEqual(inventory['policy']['continuation'], continuation.POLICY)
        assessed = self.f.op('assess_meaning_review', key='complete-inventory', formalization_id=self.target['id'])
        incomplete = {gap['job_id'] for gap in assessed['body']['gaps'] if gap['code'] == 'REVIEW_INCOMPLETE'}
        self.assertEqual(incomplete, {old_review['job'], new_job})
        self.assertEqual(assessed['body']['independent_semantic_review'], 'NOT_SATISFIED')

    def test_registry_backup_cannot_recreate_shared_ledger_authority(self):
        backup = self.f.root / 'before-claim-backup'
        self.f.op('backup_bundle', destination=str(backup))
        epoch = self.create()
        restored = self.f.root / 'restored-registry'
        restore_bundle(backup, restored, self.f.broker.directory / 'operator.key')
        broker = Broker(restored, clock=lambda: self.now, provider_routes=self.routes)
        self.addCleanup(broker.close)
        with self.assertRaises(REJECTIONS):
            broker.call(broker.admin_token, 'create_research_epoch', **self.args())
        self.assertEqual(self.f.op('inspect_research_epoch', epoch_id=epoch)['review_continuation']['calls'], [])


if __name__ == '__main__':
    unittest.main()
