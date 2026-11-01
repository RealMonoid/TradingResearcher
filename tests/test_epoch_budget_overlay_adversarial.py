"""Independent one-use epoch budget boundaries; no credentials or API calls.

The closed-feedback publication and Broker boundaries are real. The reused
publication fixture explicitly supplies synthetic owned computation metadata and
mocks only its two existing expensive assessment inspectors. SpendLedger files
are separate temporary files, never the user's real aggregate ledger.
"""
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher import openai_provider as openai
from trading_researcher.auxiliary import request_for
from trading_researcher.researcher import FEEDBACK_CONTEXT_TOOL_DEFINITIONS
from trading_researcher.storage import restore_bundle
import test_development_feedback_release as feedback_tests


POLICY = 'research-epoch-feedback-budget/1.0'
REJECTIONS = (Invalid, Conflict, Denied)
INITIAL = {'first': 28238, 'second': 28248}


class EpochBudgetOverlayAdversarialTests(unittest.TestCase):
    def setUp(self):
        self.feedback = feedback_tests.DevelopmentFeedbackReleaseTests()
        self.feedback.setUp()
        self.addCleanup(self.feedback.doCleanups)
        self.fixture = self.feedback.fixture
        self.published = self.feedback.publish()
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.ledger_path = Path(self.scratch.name) / 'shared-spending.sqlite3'
        openai.SpendLedger(self.ledger_path, 5000000000)
        self.config = openai.configuration(input_token_limit=40000, output_token_limit=6000)
        self.routes = {openai.MODEL: {'provider': 'openai',
            'key_file': str(Path(self.scratch.name) / 'deliberately-absent-key'),
            'budget_file': str(self.ledger_path), 'config': deepcopy(self.config)}}
        self.broker = self.feedback.broker
        self.restart()
        self.context = self.op('create_context', role='discovery', epoch=7,
            artifact_ids=[self.published[key] for key in ('manifest_id', 'observation_id', 'experience_id')])['id']
        self.profile = {'model': openai.MODEL, 'prompt_version': 'independent-budget-fixture/1',
            'max_calls': 12, 'max_tokens': 240000, 'max_seconds': 1800,
            'max_cost_units': 1000000000, 'currency': 'USD', 'mode': 'live',
            'prompts': {'first': 'First independent perspective.', 'second': 'Second independent perspective.'},
            'tools': deepcopy(FEEDBACK_CONTEXT_TOOL_DEFINITIONS),
            'source_presentation': 'discovery-source-view/3',
            'generation_parameters': {'openai_responses': deepcopy(self.config)},
            'max_output_tokens': 6000, 'call_timeout_seconds': 60, 'max_retries': 0}

    def restart(self):
        directory = self.broker.directory
        self.broker.close()
        self.broker = Broker(directory, clock=lambda: self.fixture.now, provider_routes=self.routes)
        self.addCleanup(self.broker.close)
        for name, result in (('_inspect_data_use', self.feedback.data_inspector.return_value),
                             ('_inspect_meaning_review', self.feedback.meaning_inspector.return_value)):
            replacement = patch.object(self.broker, name, return_value=deepcopy(result))
            replacement.start()
            self.addCleanup(replacement.stop)

    def op(self, operation, **args):
        return self.broker.call(self.broker.admin_token, operation, **args)

    def create(self, key='one-approved-feedback-epoch', **changes):
        args = {'key': key, 'context_id': self.context, 'workers': ['first', 'second'],
            'profile': deepcopy(self.profile), 'budget_overlay': POLICY}
        args.update(changes)
        return self.op('create_research_epoch', **args)['id']

    def jobs(self, epoch, order=('first', 'second')):
        batch = self.op('create_batch', key='overlay-jobs-' + epoch, epoch=7)['id']
        for worker in order:
            self.op('enqueue', key='overlay-' + worker + '-' + epoch, spec={
                'kind': 'research-record/v1', 'context_id': self.context,
                'purpose': 'Independent bounded resource fixture; no model invocation.',
                'allowed_workers': [worker], 'max_attempts': 1, 'lease_seconds': 1800,
                'deadline': self.fixture.now + 1800, 'dependencies': [],
                'batch_id': batch, 'research_epoch_id': epoch})
        self.op('seal_batch', batch_id=batch)
        worker = order[0]
        return {worker: self.broker.call(self.fixture.tokens[worker], 'claim')['lease']}

    def complete_job(self, lease, worker):
        token = self.fixture.tokens[worker]
        artifact = self.broker.call(token, 'record_research', lease=lease, kind='idea',
            content={'text': 'Synthetic independent resource-boundary fixture.'}, scope={}, source_refs=[])
        self.assertTrue(self.broker.call(token, 'submit', lease=lease, artifact_id=artifact['id'])['accepted'])

    def reserve(self, lease, worker='first', key='initial', input_tokens=None, cost=None, **changes):
        count = INITIAL[worker] if input_tokens is None else input_tokens
        wire = {'model': self.profile['model'], 'prompt_version': self.profile['prompt_version'],
            'messages': [{'role': 'system', 'content': self.profile['prompts'][worker]}],
            'tools': deepcopy(self.profile['tools']),
            'generation_parameters': deepcopy(self.profile['generation_parameters'])}
        args = {'lease': lease, 'key': key, 'request': wire, 'input_token_bound': count,
            'output_token_limit': 6000,
            'cost_bound_units': openai.cost_bound(count, 6000) if cost is None else cost}
        return self.broker.call(self.fixture.tokens[worker], 'reserve_research_call', **{**args, **changes})

    def finish(self, lease, call, worker='first', usage=None):
        return self.broker.call(self.fixture.tokens[worker], 'finish_research_call', lease=lease,
            call_id=call['call_id'], response={'status': 'completed', 'output': 'Synthetic accounting only.'},
            usage=usage)

    def test_overlay_request_is_explicit_and_idempotent_without_changing_ordinary_cap(self):
        with self.assertRaises(Invalid):
            self.op('create_research_epoch', key='ordinary-too-large', context_id=self.context,
                workers=['first', 'second'], profile={**self.profile, 'max_tokens': 80001})
        ordinary = self.op('create_research_epoch', key='ordinary', context_id=self.context,
            workers=['first', 'second'], profile={**self.profile, 'max_tokens': 80000})['id']
        self.assertNotIn('budget_overlay', self.op('inspect_research_epoch', epoch_id=ordinary)['request'])
        epoch = self.create()
        saved = self.op('inspect_research_epoch', epoch_id=epoch)
        self.assertEqual(saved['request']['budget_overlay'], POLICY)
        self.assertEqual(saved['request']['profile']['max_tokens'], 240000)
        self.assertEqual(self.create(), epoch)
        with self.assertRaises(REJECTIONS):
            self.op('create_research_epoch', key='one-approved-feedback-epoch', context_id=self.context,
                workers=['first', 'second'], profile={**self.profile, 'max_tokens': 80000})
        with self.assertRaises(REJECTIONS):
            self.create(key='second-overlay')

    def test_worker_forgery_invalid_limits_and_ineligible_context_do_not_consume_claim(self):
        with self.assertRaises(Denied):
            self.broker.call(self.fixture.tokens['first'], 'create_research_epoch',
                key='worker-request', context_id=self.context, workers=['first', 'second'],
                profile=self.profile, budget_overlay=POLICY)
        for value in (None, True, {}, 'research-epoch-feedback-budget/2.0'):
            with self.subTest(overlay=value), self.assertRaises(REJECTIONS):
                self.create(key='invalid-overlay', budget_overlay=value)
        for change in ({'max_tokens': 240001}, {'max_tokens': True}, {'max_cost_units': 1000000001},
                {'max_calls': 13}, {'max_seconds': 1801}, {'max_retries': 1}, {'mode': 'fixture'},
                {'currency': 'NONE'}, {'model': 'unregistered-model'}, {'max_output_tokens': 6001},
                {'source_presentation': 'discovery-source-view/2'}, {'perspective_profiles': {}}):
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                self.create(key='invalid-profile', profile={**self.profile, **change})
        empty = self.op('create_context', role='discovery', epoch=7, artifact_ids=[])['id']
        with self.assertRaises(REJECTIONS):
            self.create(key='missing-feedback', context_id=empty)
        with self.assertRaises(REJECTIONS):
            self.create(key='worker-replacement', workers=['first', 'not-registered'])
        with self.assertRaises(REJECTIONS):
            self.op('create_research_epoch', key='source-selected-ledger', context_id=self.context,
                workers=['first', 'second'], profile=self.profile, budget_overlay=POLICY,
                budget_file=str(Path(self.scratch.name) / 'replacement-ledger'))
        self.assertIsInstance(self.create(), str)

    def test_malformed_perspective_settings_fail_typed_before_consumption(self):
        for malformed in (None, [], 'invalid', {'first': None, 'second': {}}):
            with self.subTest(value=malformed), self.assertRaises(REJECTIONS):
                self.create(key='malformed-perspectives', profile={**self.profile,
                    'perspective_profiles': malformed})
        self.assertIsInstance(self.create(), str)

    def test_complete_feedback_trio_is_required_before_irreversible_claim(self):
        for fields in (('manifest_id',), ('manifest_id', 'experience_id'), ('manifest_id', 'observation_id')):
            context = self.op('create_context', role='discovery', epoch=7,
                artifact_ids=[self.published[field] for field in fields])['id']
            with self.subTest(fields=fields), self.assertRaises(REJECTIONS):
                self.create(key='incomplete-feedback', context_id=context)
        self.assertIsInstance(self.create(), str)

    def test_incompatible_installed_configuration_is_rejected_before_claim(self):
        wrong = {**self.config, 'input_token_limit': 39999}
        selected = {key: deepcopy(self.profile[key]) for key in (
            'model', 'prompt_version', 'generation_parameters', 'max_output_tokens',
            'call_timeout_seconds', 'max_retries')}
        cases = [
            {**self.profile, 'generation_parameters': {}},
            {**self.profile, 'generation_parameters': {'openai_responses': wrong}},
            {**self.profile, 'perspective_profiles': {'first': {**selected,
                'generation_parameters': {'openai_responses': wrong}}, 'second': deepcopy(selected)}}]
        for number, profile in enumerate(cases):
            with self.subTest(case=number), self.assertRaises(REJECTIONS):
                self.create(key='wrong-installed-configuration', profile=profile)
        self.assertIsInstance(self.create(), str)

    def test_both_downstream_slots_remain_single_use_after_zero_usage(self):
        epoch = self.create()
        leases = self.jobs(epoch)
        for worker in ('first', 'second'):
            if worker == 'second':
                leases[worker] = self.broker.call(self.fixture.tokens[worker], 'claim')['lease']
            for ordinal, bound in enumerate((INITIAL[worker], 40000)):
                call = self.reserve(leases[worker], worker=worker, key='slot-' + str(ordinal), input_tokens=bound)
                self.finish(leases[worker], call, worker=worker,
                    usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
            self.complete_job(leases[worker], worker)
        target = None
        idea, catalog = self.feedback.formalization['body']['idea_id'], self.feedback.catalog['id']
        for kind, name, input_bound, output_bound in (
                ('formalization/v1', 'overlay-formalizer', 27015, 18000),
                ('semantic-review/v1', 'overlay-independent-reviewer', 30000, 4000)):
            config = openai.configuration(input_token_limit=input_bound, output_token_limit=output_bound)
            self.routes[openai.MODEL]['config'] = config
            self.restart()
            token = self.op('register_worker', name=name, role='formalizer', capabilities=[kind])['token']
            refs = [idea, catalog] + ([target] if target else [self.published[key]
                for key in ('manifest_id', 'observation_id', 'experience_id')])
            context = self.op('create_context', role='formalizer', epoch=8 if target else 7, artifact_ids=refs)['id']
            inputs = {'formalization_id': target, 'definition_ids': []} if target else {
                'idea_id': idea, 'catalog_id': catalog, 'definition_ids': []}
            selected = {'model': openai.MODEL, 'prompt_version': name + '/1',
                'prompt': 'Retain an unsupported synthetic input as a gap; this is not a model judgment.',
                'generation_parameters': {'openai_responses': config}, 'max_output_tokens': output_bound,
                'call_timeout_seconds': 60, 'max_retries': 0}
            batch = self.op('create_batch', key=name, epoch=8 if target else 7)['id']
            spec = {'kind': kind, 'context_id': context, 'purpose': 'Offline downstream budget boundary.',
                'allowed_workers': [name], 'max_attempts': 1, 'lease_seconds': 1800,
                'deadline': self.fixture.now + 1800, 'dependencies': [], 'batch_id': batch,
                'research_epoch_id': epoch, 'research_call_profile': selected, 'research_inputs': inputs}
            self.op('enqueue', key=name, spec=spec)
            self.op('seal_batch', batch_id=batch)
            lease = self.broker.call(token, 'claim')['lease']
            packet = self.broker.call(token, 'auxiliary_input', lease=lease)
            wire = request_for(spec, packet)
            args = {'lease': lease, 'request': wire, 'input_token_bound': input_bound,
                'output_token_limit': output_bound, 'cost_bound_units': openai.cost_bound(input_bound, output_bound)}
            with self.assertRaises(REJECTIONS):
                self.broker.call(token, 'reserve_research_call', key='oversized', **{
                    **args, 'input_token_bound': input_bound + 1,
                    'cost_bound_units': openai.cost_bound(input_bound + 1, output_bound)})
            call = self.broker.call(token, 'reserve_research_call', key='one-stage', **args)
            output = {'status': 'final', 'candidate': None, 'semantic_report': None} if target is None else {
                'status': 'final', 'review': {'judgment': 'uncertain',
                    'reason': 'Synthetic missing candidate remains a gap.', 'added_assumptions': [],
                    'omitted_assumptions': [], 'conflicts': [], 'unresolved_meaning': ['No executable candidate.'],
                    'mapping_checks': []}}
            self.broker.call(token, 'finish_research_call', lease=lease, call_id=call['call_id'],
                response={'status': 'completed', 'output': output},
                usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
            with self.assertRaises(REJECTIONS):
                self.broker.call(token, 'reserve_research_call', key='forbidden-retry', **args)
            if target is None:
                saved = self.broker.call(token, 'record_formalization', lease=lease, idea_id=idea,
                    catalog_id=catalog, candidate=None, semantic_report=None, provider_call_id=call['call_id'])
                self.assertTrue(self.broker.call(token, 'submit', lease=lease, artifact_id=saved['id'])['accepted'])
                self.op('release_batch', batch_id=batch, target_epoch=8)
                target = saved['id']
        inventory = self.op('inspect_research_epoch', epoch_id=epoch)['budget_overlay']['calls']
        self.assertEqual(len(inventory), 6)
        self.assertEqual(sum(call['allocated_tokens'] for call in inventory), 239501)
        self.assertEqual(sum(call['allocated_cost'] for call in inventory), 943752500)
        self.assertEqual([call['stage'] for call in inventory[-2:]], ['formalization/v1', 'semantic-review/v1'])

    def test_original_worker_slots_survive_reverse_dispatch_order_and_never_refund(self):
        epoch = self.create()
        leases = self.jobs(epoch, order=('second', 'first'))
        second = self.reserve(leases['second'], worker='second')
        with self.assertRaises(REJECTIONS):
            self.reserve(leases['second'], worker='second', key='while-pending', input_tokens=40000)
        self.finish(leases['second'], second, worker='second',
            usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
        for worker in ('second', 'first'):
            if worker == 'first':
                leases[worker] = self.broker.call(self.fixture.tokens[worker], 'claim')['lease']
                with self.assertRaises(REJECTIONS):
                    self.reserve(leases[worker], input_tokens=INITIAL[worker] + 1)
                first = self.reserve(leases[worker])
                self.finish(leases[worker], first, usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
            followup = self.reserve(leases[worker], worker=worker, key='followup', input_tokens=40000)
            self.finish(leases[worker], followup, worker=worker,
                usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
            with self.subTest(worker=worker), self.assertRaises(REJECTIONS):
                self.reserve(leases[worker], worker=worker, key='extra-after-zero-usage', input_tokens=1)
            self.complete_job(leases[worker], worker)
        view = self.op('inspect_research_epoch', epoch_id=epoch)
        self.assertEqual(view['usage']['tokens'], 0)
        calls = view['budget_overlay']['calls']
        self.assertEqual(len(calls), 4)
        self.assertEqual(sum(call['allocated_tokens'] for call in calls), 160486)
        self.assertEqual(sum(call['allocated_cost'] for call in calls), 581215000)

    def test_exact_conservative_cost_and_per_call_ceiling_are_checked_before_slot_use(self):
        epoch = self.create()
        lease = self.jobs(epoch)['first']
        expected = openai.cost_bound(INITIAL['first'], 6000)
        for change in ({'cost': 0}, {'cost': expected - 1}, {'cost': expected + 1},
                {'input_tokens': 74001}, {'output_token_limit': 6001},
                {'input_token_bound': True}, {'cost_bound_units': True}):
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                self.reserve(lease, **change)
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['budget_overlay']['calls'], [])
        call = self.reserve(lease)
        self.assertTrue(call['dispatch'])
        repeated = self.reserve(lease)
        self.assertFalse(repeated['dispatch'])
        self.assertEqual(repeated['call_id'], call['call_id'])

    def test_shared_pending_and_unknown_spend_block_new_reservation_without_free_slots(self):
        epoch = self.create()
        lease = self.jobs(epoch)['first']
        ledger = openai.SpendLedger(self.ledger_path, 5000000000)
        pending = ledger.reserve('a' * 64, 10, key='other-host-pending')
        with self.assertRaises(REJECTIONS):
            self.reserve(lease)
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['budget_overlay']['calls'], [])
        ledger.settle(pending, None)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease)
        self.assertEqual(ledger.snapshot()['charged_nano'], 10)
        self.assertTrue(ledger.snapshot()['halted'])

    def test_restart_retains_one_use_and_exact_nonrefundable_call_inventory(self):
        epoch = self.create()
        lease = self.jobs(epoch)['first']
        first = self.reserve(lease)
        self.finish(lease, first, usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
        inventory = deepcopy(self.op('inspect_research_epoch', epoch_id=epoch)['budget_overlay']['calls'])
        self.restart()
        self.assertEqual(self.create(), epoch)
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['budget_overlay']['calls'], inventory)
        with self.assertRaises(REJECTIONS):
            self.create(key='new-key-after-restart')
        followup = self.reserve(lease, key='followup', input_tokens=40000)
        self.finish(lease, followup, usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, key='third-after-restart', input_tokens=1)

    def test_claim_commit_survives_registry_rollback_and_cannot_be_reissued(self):
        original = self.broker._event
        def fail_after_claim(actor, kind, **fields):
            if kind == 'research_epoch_created':
                raise RuntimeError('Independent injected registry rollback after external claim')
            return original(actor, kind, **fields)
        with patch.object(self.broker, '_event', side_effect=fail_after_claim), self.assertRaises(RuntimeError):
            self.create()
        self.assertIsNone(self.broker._db.execute(
            'SELECT id FROM research_epochs WHERE request_key=?', ('one-approved-feedback-epoch',)).fetchone())
        self.restart()
        with self.assertRaises(REJECTIONS):
            self.create()
        with self.assertRaises(REJECTIONS):
            self.create(key='replacement-after-rollback')

    def test_external_reservation_fence_survives_registry_transaction_failure(self):
        epoch = self.create()
        lease = self.jobs(epoch)['first']
        original = self.broker._event
        def fail_after_fence(actor, kind, **fields):
            if kind == 'provider_call_reserved':
                raise RuntimeError('Independent injected registry rollback after reservation fence')
            return original(actor, kind, **fields)
        with patch.object(self.broker, '_event', side_effect=fail_after_fence), self.assertRaises(RuntimeError):
            self.reserve(lease)
        self.assertEqual(self.broker._db.execute(
            'SELECT COUNT(*) FROM research_calls WHERE epoch_id=?', (epoch,)).fetchone()[0], 0)
        self.restart()
        with self.assertRaises(REJECTIONS):
            self.reserve(lease)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, key='new-key-after-failed-commit')

    def test_same_path_stale_database_cannot_erase_consumed_call(self):
        epoch = self.create()
        lease = self.jobs(epoch)['first']
        stale = Path(self.scratch.name) / 'before-call.sqlite3'
        with closing(sqlite3.connect(stale)) as db:
            self.broker._db.backup(db)
        first = self.reserve(lease)
        self.finish(lease, first, usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
        registry = self.broker.directory / 'registry.sqlite3'
        self.broker.close()
        with closing(sqlite3.connect(stale)) as source, closing(sqlite3.connect(registry)) as target:
            source.backup(target)
        self.restart()
        with self.assertRaises(REJECTIONS):
            self.reserve(lease)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, key='different-request-after-restore')

    def test_revoke_is_operator_only_persistent_and_preserves_settlement_and_acknowledgment(self):
        epoch = self.create()
        lease = self.jobs(epoch)['first']
        first = self.reserve(lease)
        with self.assertRaises(Denied):
            self.broker.call(self.fixture.tokens['first'], 'revoke_research_epoch_budget', epoch_id=epoch)
        self.op('revoke_research_epoch_budget', epoch_id=epoch)
        self.restart()
        self.assertTrue(self.op('inspect_research_epoch', epoch_id=epoch)['budget_overlay']['revoked'])
        receipt = self.finish(lease, first, usage={'input_tokens': 11, 'output_tokens': 7, 'cost_units': 20000})
        self.assertTrue(receipt['within_reservation'])
        self.assertEqual(self.finish(lease, first,
            usage={'input_tokens': 11, 'output_tokens': 7, 'cost_units': 20000}), receipt)
        self.assertFalse(self.reserve(lease)['dispatch'])
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['tokens'], 18)
        with self.assertRaises(REJECTIONS):
            self.reserve(lease, key='followup-after-revoke', input_tokens=40000)
        with self.assertRaises(REJECTIONS):
            self.create(key='revoke-is-not-a-reset')

    def test_current_backup_in_another_registry_cannot_reuse_shared_ledger_claim(self):
        epoch = self.create()
        leases = self.jobs(epoch)
        first = self.reserve(leases['first'])
        self.finish(leases['first'], first, usage={'input_tokens': 0, 'output_tokens': 0, 'cost_units': 0})
        backup, restored = Path(self.scratch.name) / 'backup', Path(self.scratch.name) / 'restored'
        self.op('backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, self.broker.directory / 'operator.key')
        other = Broker(restored, clock=lambda: self.fixture.now, provider_routes=self.routes)
        self.addCleanup(other.close)
        with patch.object(other, '_inspect_data_use', return_value=deepcopy(self.feedback.data_inspector.return_value)), \
                patch.object(other, '_inspect_meaning_review', return_value=deepcopy(self.feedback.meaning_inspector.return_value)):
            self.assertEqual(other._epoch(epoch)['request'], self.broker._epoch(epoch)['request'])
            with self.assertRaises(REJECTIONS):
                other.call(other.admin_token, 'create_research_epoch', key='cross-registry-new-claim',
                    context_id=self.context, workers=['first', 'second'], profile=self.profile, budget_overlay=POLICY)
            with self.assertRaises(REJECTIONS):
                other.call(self.fixture.tokens['first'], 'reserve_research_call', lease=leases['first'],
                    key='restored-new-dispatch', request={
                        'model': self.profile['model'], 'prompt_version': self.profile['prompt_version'],
                        'messages': [{'role': 'system', 'content': self.profile['prompts']['first']}],
                        'tools': self.profile['tools'], 'generation_parameters': self.profile['generation_parameters']},
                    input_token_bound=40000, output_token_limit=6000,
                    cost_bound_units=openai.cost_bound(40000, 6000))

    def test_two_registries_cannot_claim_the_shared_one_use_grant_concurrently(self):
        backup, restored = Path(self.scratch.name) / 'before-claims', Path(self.scratch.name) / 'competitor'
        self.op('backup_bundle', destination=str(backup))
        restore_bundle(backup, restored, self.broker.directory / 'operator.key')
        other = Broker(restored, clock=lambda: self.fixture.now, provider_routes=self.routes)
        self.addCleanup(other.close)
        barrier = threading.Barrier(2)
        def attempt(host):
            barrier.wait(timeout=10)
            try:
                return host.call(host.admin_token, 'create_research_epoch', key='concurrent-claim',
                    context_id=self.context, workers=['first', 'second'], profile=deepcopy(self.profile),
                    budget_overlay=POLICY)
            except REJECTIONS as error:
                return error
        with patch.object(other, '_inspect_data_use', return_value=deepcopy(self.feedback.data_inspector.return_value)), \
                patch.object(other, '_inspect_meaning_review', return_value=deepcopy(self.feedback.meaning_inspector.return_value)), \
                ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(attempt, host) for host in (self.broker, other)]
            results = [future.result(timeout=20) for future in futures]
        self.assertEqual(sum(type(result) is dict and 'id' in result for result in results), 1)
        self.assertEqual(sum(isinstance(result, REJECTIONS) for result in results), 1)
        self.assertEqual(sum(host._db.execute('SELECT COUNT(*) FROM research_epochs WHERE request_key=?',
            ('concurrent-claim',)).fetchone()[0] for host in (self.broker, other)), 1)


if __name__ == '__main__':
    unittest.main()
