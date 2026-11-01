"""Independent D095 resource boundaries; no providers or actual registries.

BudgetHost uses a real temporary shared ledger and SQLite call inventory. Source
qualification and packet construction are explicit stubs, not evidence of
current production qualification. Synthetic identity pins are patched only in
these fixtures; production defaults are checked separately.
"""
from contextlib import closing
from copy import deepcopy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher import paired_correction_budget as correction
from trading_researcher import paired_budget as previous
from trading_researcher import epoch_budget_dispatch as dispatch
from trading_researcher import epoch_budget as ordinary
from trading_researcher import complete_feedback_budget as complete
from trading_researcher import openai_provider as openai
from trading_researcher.auxiliary import request_for
from trading_researcher.codec import canonical, digest
from trading_researcher.paired_broker import PairedBroker
from trading_researcher.feedback_budget_broker import FeedbackBudgetBroker
import test_paired_host_adversarial as support

BASE_PROMPT = 'Synthetic unchanged complete paired prompt.' + openai.COMPACT_OUTPUT_SUFFIX
CORRECT_PROMPT = BASE_PROMPT[:-len(openai.COMPACT_OUTPUT_SUFFIX)] + correction.FORMAT_CLARIFICATION + openai.COMPACT_OUTPUT_SUFFIX
SYNTHETIC_CANDIDATE = {'schema': 'synthetic-retained-format-gap/1', 'horizons': [{'grid_seconds': 900, 'outcome_bars': 5}]}
REJECTIONS = support.REJECTIONS


class CorrectionPromptTests(unittest.TestCase):
    def test_only_exact_insertion_before_formatting_suffix_is_permitted(self):
        profile = support.role_profile('formalization/v1')
        profile.pop('prompt')
        profile['prompts'] = {'formalizer': CORRECT_PROMPT}
        with patch.object(correction, 'BASE_PROMPT_SHA256', hashlib.sha256(BASE_PROMPT.encode()).hexdigest()):
            correction._call_settings(profile, 'formalization/v1')
            for prompt in (BASE_PROMPT, CORRECT_PROMPT + 'changed',
                           CORRECT_PROMPT.replace('unchanged', 'changed'),
                           correction.FORMAT_CLARIFICATION + BASE_PROMPT,
                           CORRECT_PROMPT.replace(correction.FORMAT_CLARIFICATION, correction.FORMAT_CLARIFICATION * 2)):
                with self.subTest(prompt=prompt[:70]), self.assertRaises(REJECTIONS):
                    correction._call_settings({**profile, 'prompts': {'formalizer': prompt}}, 'formalization/v1')


class CorrectionHost(support.BudgetHost):
    def __init__(self, root):
        super().__init__(root)
        self.epoch['request']['budget_overlay'] = correction.POLICY
        self.epoch['request_key'] = 'separate-correction-once'
        self.retained = {'id': correction.RETAINED_FORMALIZATION, 'origin': 'worker', 'body': {
            'idea_id': correction.IDEA, 'candidate': deepcopy(SYNTHETIC_CANDIDATE),
            'assessment': {'status': 'RETAINED_GAP'}}}
        self._artifact.side_effect = lambda identity: deepcopy(self.retained) if identity == correction.RETAINED_FORMALIZATION else {'id': identity}

    def job(self, kind='formalization/v1'):
        job = super().job(kind)
        if kind == 'formalization/v1':
            job['spec']['research_call_profile']['prompt'] = CORRECT_PROMPT
        return job

    def prior(self, count=1, revoked=True):
        # Test-only historical metadata seed. No claim that these synthetic
        # prior entries are actual provider calls or a qualified prior result.
        with self.ledger._connect() as db:
            ordinary._schema(db)
            calls = [{'call_id': 'old-call-' + str(index), 'stage': 'formalization/v1'} for index in range(count)]
            db.execute('INSERT INTO research_epoch_budget_grants VALUES(?,?,?,?)',
                       (previous.APPROVAL, canonical({'synthetic_prior': True}), canonical(calls), int(revoked)))

    def claim(self):
        dispatch.validate(self, self.context, self.profile, correction.POLICY)
        dispatch.claim(self, self.epoch)

    def reserve(self, kind='formalization/v1', identity='first-call', input_bound=None, **changes):
        job = self.job(kind)
        inputs, outputs = (62000, 18000) if kind == 'formalization/v1' else (76000, 4000)
        inputs = inputs if input_bound is None else input_bound
        args = {'input_bound': inputs, 'output_bound': outputs, 'cost': openai.cost_bound(inputs, outputs),
                'request': request_for(job['spec'], self._auxiliary_packet_for_spec(job['spec']))}
        return dispatch.reserve(self, self.epoch, job, identity, **{**args, **changes})


class CorrectionBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        for name, value in (('BASE_PROMPT_SHA256', hashlib.sha256(BASE_PROMPT.encode()).hexdigest()),
                            ('RETAINED_CANDIDATE_SHA256', digest(SYNTHETIC_CANDIDATE))):
            selected = patch.object(correction, name, value)
            selected.start()
            self.addCleanup(selected.stop)
        self.next_host = 0
        self.host = self.new_host()

    def new_host(self):
        root = Path(self.temp.name) / str(self.next_host)
        self.next_host += 1
        root.mkdir()
        host = CorrectionHost(root)
        self.addCleanup(host._db.close)
        return host

    def test_prior_attempt_must_exist_be_revoked_and_have_exactly_one_call(self):
        for count, revoked in ((None, False), (0, True), (1, False), (2, True)):
            host = self.new_host()
            if count is not None:
                host.prior(count, revoked)
            with self.subTest(count=count, revoked=revoked), self.assertRaises(REJECTIONS):
                host.claim()
            with host.ledger._connect() as db:
                ordinary._schema(db)
                self.assertIsNone(db.execute('SELECT 1 FROM research_epoch_budget_grants WHERE approval=?', (correction.APPROVAL,)).fetchone())
        self.host.prior()
        self.host.claim()
        self.assertEqual(dispatch.inspect(self.host, self.host.epoch)['calls'], [])

    def test_two_slots_are_nonrecyclable_and_prior_history_stays_unchanged(self):
        self.host.prior()
        with self.host.ledger._connect() as db:
            before = db.execute('SELECT * FROM research_epoch_budget_grants WHERE approval=?', (previous.APPROVAL,)).fetchone()
        self.host.claim()
        with self.assertRaises(REJECTIONS):
            self.host.reserve('semantic-review/v1', identity='premature-review')
        self.host.reserve(input_bound=1)
        self.host.committed('first-call')
        with self.assertRaises(REJECTIONS):
            self.host.reserve(identity='retry')
        self.host.reserve('semantic-review/v1', identity='second-call', input_bound=1)
        self.host.committed('second-call')
        state = dispatch.inspect(self.host, self.host.epoch)
        self.assertEqual([call['stage'] for call in state['calls']], ['formalization/v1', 'semantic-review/v1'])
        self.assertEqual(sum(call['allocated_tokens'] for call in state['calls']), 160000)
        self.assertEqual(sum(call['allocated_cost'] for call in state['calls']), 565000000)
        with self.assertRaises(REJECTIONS):
            self.host.reserve('semantic-review/v1', identity='third-call')
        with self.host.ledger._connect() as db:
            self.assertEqual(db.execute('SELECT * FROM research_epoch_budget_grants WHERE approval=?', (previous.APPROVAL,)).fetchone(), before)

    def test_duplicate_cross_registry_stale_inventory_restart_and_revoke(self):
        self.host.prior()
        self.host.claim()
        with self.assertRaises(REJECTIONS):
            self.host.claim()
        original = self.host.directory
        self.host.directory = Path(self.temp.name) / 'other-registry'
        with self.assertRaises(REJECTIONS):
            dispatch.inspect(self.host, self.host.epoch)
        with self.assertRaises(REJECTIONS):
            dispatch.claim(self.host, self.host.epoch)
        self.host.directory = original
        self.host.reserve()
        # External reservation survives an omitted registry transaction.
        with self.assertRaises(REJECTIONS):
            self.host.reserve('semantic-review/v1', identity='after-rollback')
        self.host.committed('first-call')
        self.host.ledger = openai.SpendLedger(self.host.ledger.path, 5000000000)
        self.assertEqual(len(dispatch.inspect(self.host, self.host.epoch)['calls']), 1)
        result = dispatch.revoke(self.host, self.host.epoch)
        self.assertTrue(result['pending_calls_still_require_settlement'])
        with self.assertRaises(REJECTIONS):
            self.host.reserve('semantic-review/v1', identity='after-revoke')
        self.assertTrue(dispatch.inspect(self.host, self.host.epoch)['revoked'])
        self.assertEqual(len(dispatch.inspect(self.host, self.host.epoch)['calls']), 1)

    def test_aggregate_spending_pending_unknown_and_exact_remaining_allowance(self):
        for spent, settled in ((1, False), (None, True), (4400000001, True), (4400000000, True)):
            host = self.new_host()
            host.prior()
            amount = 1 if spent is None else spent
            identity = host.ledger.reserve('f' * 64, amount, key='prior-money')
            if settled:
                host.ledger.settle(identity, spent)
            if spent == 4400000000 and settled:
                host.claim()
                self.assertEqual(dispatch.inspect(host, host.epoch)['calls'], [])
            else:
                with self.subTest(spent=spent, settled=settled), self.assertRaises(REJECTIONS):
                    host.claim()

    def test_retained_failure_and_protected_source_checks_cannot_be_substituted(self):
        for change in ('origin', 'idea', 'assessment', 'candidate'):
            original = deepcopy(self.host.retained)
            if change == 'origin': self.host.retained['origin'] = 'source'
            if change == 'idea': self.host.retained['body']['idea_id'] = 'another-idea'
            if change == 'assessment': self.host.retained['body']['assessment']['status'] = 'STRUCTURE_CHECKED'
            if change == 'candidate': self.host.retained['body']['candidate']['horizons'][0]['outcome_bars'] = 4
            with self.subTest(change=change), self.assertRaises(REJECTIONS):
                dispatch.validate(self.host, self.host.context, self.host.profile, correction.POLICY)
            self.host.retained = original
        self.host._paired_require_qualification.reset_mock()
        self.host._deny_final_calibration_ancestry.side_effect = support.Denied('Synthetic protected ancestry')
        with self.assertRaises(REJECTIONS):
            dispatch.validate(self.host, self.host.context, self.host.profile, correction.POLICY)
        self.host._paired_require_qualification.assert_not_called()

    def test_exact_limits_full_packet_no_discovery_and_no_cheapened_role(self):
        for changes in ({'max_tokens': 160001}, {'max_cost_units': 600000001}, {'max_calls': 3},
                        {'max_seconds': 1801}, {'max_retries': 1}, {'mode': 'fixture'}, {'tools': [{}]}):
            with self.subTest(changes=changes), self.assertRaises(REJECTIONS):
                dispatch.validate(self.host, self.host.context, {**self.host.profile, **changes}, correction.POLICY)
        self.host.prior()
        self.host.claim()
        for changes in ({'input_bound': 62001}, {'output_bound': 17999}, {'cost': 0}, {'request': {}}):
            with self.subTest(changes=changes), self.assertRaises(REJECTIONS):
                self.host.reserve(**changes)
        for kind in ('research-record/v1', 'discovery/v1'):
            with self.subTest(kind=kind), self.assertRaises(REJECTIONS):
                self.host.reserve(kind)
        for kind in ('formalization/v1', 'semantic-review/v1'):
            profile = self.host._effective_research_profile(self.host.job(kind))
            for key, value in (('model', 'cheaper-model'), ('max_retries', 1), ('call_timeout_seconds', 359)):
                with self.subTest(kind=kind, field=key), self.assertRaises(REJECTIONS):
                    correction._call_settings({**profile, key: value}, kind)
            changed = deepcopy(profile)
            changed['generation_parameters']['openai_responses']['reasoning_effort'] = 'medium'
            with self.assertRaises(REJECTIONS):
                correction._call_settings(changed, kind)
        self.assertEqual(dispatch.inspect(self.host, self.host.epoch)['calls'], [])

    def test_changed_source_pending_dispatch_and_expired_call_allowance_deny(self):
        self.host.prior()
        self.host.claim()
        self.host._paired_source_identity.return_value = {'synthetic.py': 'b' * 64}
        with self.assertRaises(REJECTIONS):
            self.host.reserve()
        self.host._paired_source_identity.return_value = {'synthetic.py': 'a' * 64}
        self.host.now += 1441
        with self.assertRaises(REJECTIONS):
            self.host.reserve()
        self.host.now -= 1441
        self.host.ledger.reserve('a' * 64, 1, key='pending')
        with self.assertRaises(REJECTIONS):
            self.host.reserve()
        self.assertEqual(dispatch.inspect(self.host, self.host.epoch)['calls'], [])

    def test_reviewer_requires_same_epoch_completed_nonnull_structurally_checked_target(self):
        self.host.prior()
        self.host.claim()
        formal = self.host.job()
        correction.validate_job(self.host, self.host.epoch, formal['spec'])
        self.host._db.execute('INSERT INTO job_specs VALUES(?,?)', ('formal', canonical(formal['spec'])))
        self.host._db.execute('INSERT INTO jobs VALUES(?,?,?)', ('formal', 'completed', 'target'))
        review = self.host.job('semantic-review/v1')['spec']
        review['research_inputs']['formalization_id'] = 'target'
        for candidate, status in ((None, 'STRUCTURE_CHECKED'), ({}, 'RETAINED_GAP'), ({}, 'STRUCTURE_CHECKED')):
            self.host._artifact.side_effect = lambda identity: {'body': {'candidate': candidate, 'assessment': {'status': status}}}
            if candidate is not None and status == 'STRUCTURE_CHECKED':
                correction.validate_job(self.host, self.host.epoch, review)
            else:
                with self.subTest(candidate=candidate, status=status), self.assertRaises(REJECTIONS):
                    correction.validate_job(self.host, self.host.epoch, review)
        review['research_inputs']['formalization_id'] = 'different-target'
        with self.assertRaises(REJECTIONS):
            correction.validate_job(self.host, self.host.epoch, review)
        with self.assertRaises(REJECTIONS):
            correction.validate_job(self.host, self.host.epoch, formal['spec'])


class CorrectionRoutingTests(unittest.TestCase):
    def test_production_pins_and_old_policy_are_distinct_and_preserved(self):
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(correction.RETAINED_CANDIDATE_SHA256, '22569f7c2686a2ef23b1e9d357db2b7b4ec254cdb6106d2cb5c0cdbc24cc506e')
        self.assertEqual(correction.BASE_PROMPT_SHA256, '08279770164c8803a8ef8d69b0f1a5a131338286ebd5fa705db1af660696b095')
        self.assertEqual(hashlib.sha256((root / correction.SPEC).read_bytes()).hexdigest(), correction.SPEC_SHA256)
        self.assertEqual(hashlib.sha256((root / 'trading_researcher/paired_budget.py').read_bytes()).hexdigest(),
                         '48c079d7a807b0b7881c67cf820f62bd5e01561d2306ca0f12e53418f1d0193a')
        for module in (ordinary, complete, previous, correction):
            self.assertIs(dispatch._policy(module.POLICY), module)
        self.assertNotEqual(correction.APPROVAL, previous.APPROVAL)
        self.assertEqual(correction.PRIOR_APPROVAL, previous.APPROVAL)
        with self.assertRaises(REJECTIONS):
            dispatch._policy('arbitrary-successor')

    def test_actual_broker_operator_boundary_and_explicit_job_policy_routing(self):
        with tempfile.TemporaryDirectory() as root, closing(PairedBroker(Path(root) / 'registry')) as broker:
            worker = broker.call(broker.admin_token, 'register_worker', name='worker', role='discovery', capabilities=['research-record/v1'])['token']
            for operation, args in (('create_research_epoch', {'key': 'forged', 'context_id': 'absent', 'workers': [], 'profile': {}, 'budget_overlay': correction.POLICY}),
                                    ('revoke_research_epoch_budget', {'epoch_id': 'absent'})):
                with self.subTest(operation=operation), self.assertRaises(REJECTIONS):
                    broker.call(worker, operation, **args)
            # Routing-only seam: generic job validation and qualification are
            # covered separately. This checks the actual subclass dispatch.
            for module in (previous, correction):
                epoch = {'request': {'budget_overlay': module.POLICY}}
                spec = {'research_epoch_id': 'synthetic-epoch'}
                with patch.object(FeedbackBudgetBroker, '_research_spec_check'), \
                     patch.object(broker, '_epoch', return_value=epoch), \
                     patch.object(module, 'validate_job') as selected:
                    broker._research_spec_check(spec)
                    selected.assert_called_once_with(broker, epoch, spec)


if __name__ == '__main__':
    unittest.main()
