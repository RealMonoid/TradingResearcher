"""Finite resource enforcement through native temporary broker/ledger behavior."""
from copy import deepcopy
import sqlite3
import unittest
from unittest.mock import patch

from inquiry_resource_support import Fixture, LedgerProvider, fake_post
from trading_researcher.auxiliary import run_auxiliary_once
from trading_researcher.codec import canonical, decode
from trading_researcher.errors import Denied
from trading_researcher.inquiry import resources
from trading_researcher.inquiry.worker import run_research_once


class InquiryResourceTests(unittest.TestCase):
    def fixture(self, **options):
        fixture = Fixture(**options)
        self.addCleanup(fixture.close)
        return fixture

    def test_declared_envelope_matches_independent_role_arithmetic(self):
        self.assertEqual(resources.TOKEN_CAP, 80000 * 4)
        self.assertEqual(sum(resources.INPUT_MAX), 272000)
        self.assertEqual(sum(resources.OUTPUT), 48000)
        self.assertEqual(272000 * 2500 + 48000 * 10000, 1160000000)
        self.assertEqual(1160000000 - resources.COST_CAP, 116722500)

    def test_two_native_discoveries_authenticate_actual_shared_ledger_usage(self):
        f = self.fixture()
        results = f.discover()
        state = f.op('inspect_research_epoch', epoch_id=f.epoch)
        self.assertEqual([c['stage'] for c in state['resource_disposition']['calls']], list(resources.STAGES[:2]))
        self.assertEqual(len(results), 2)
        self.assertEqual(state['usage']['calls'], 2)
        self.assertTrue(all(decode(row[0])['resource_settlement_verified'] for row in
            f.broker._db.execute('SELECT receipt FROM research_calls WHERE epoch_id=?', (f.epoch,))))
        self.assertEqual(f.ledger.snapshot()['charged_nano'], 3962122500)
        with self.assertRaises(sqlite3.IntegrityError), f.ledger._connect() as db:
            db.execute('UPDATE research_epoch_budget_grants SET calls=? WHERE approval=?', ('[]', resources.APPROVAL))

    def test_forged_cheap_native_usage_is_retained_and_halts_without_release(self):
        f = self.fixture()
        f.enqueue_discovery()
        with patch('trading_researcher.inquiry.worker._invoke', side_effect=lambda p, r, o, t, c: p.complete(r, o, t)):
            result = run_research_once(f.clients['first'], LedgerProvider(f, 'first', ledger=False))
        self.assertFalse(result['accepted'])
        state = f.op('inspect_research_epoch', epoch_id=f.epoch)
        self.assertEqual(state['state'], 'halted')
        self.assertIsNotNone(state['calls'][0]['reply'])
        receipt = decode(f.broker._db.execute('SELECT receipt FROM research_calls WHERE epoch_id=?', (f.epoch,)).fetchone()[0])
        self.assertFalse(receipt['resource_settlement_verified'])
        self.assertEqual(len(state['resource_disposition']['calls']), 1)

    def test_future_holds_deny_before_dispatch_and_do_not_consume_a_slot(self):
        f = self.fixture()
        f.enqueue_discovery()
        other = f.ledger.reserve('synthetic-other-work', 40000000, key='other')
        f.ledger.settle(other, 40000000)
        with patch('trading_researcher.inquiry.worker._invoke') as invoke:
            result = run_research_once(f.clients['first'], LedgerProvider(f, 'first', bound=74000))
        self.assertFalse(result['accepted'])
        invoke.assert_not_called()
        state = f.op('inspect_research_epoch', epoch_id=f.epoch)
        self.assertEqual(state['calls'], [])
        self.assertEqual(state['resource_disposition']['calls'], [])
        self.assertEqual(f.ledger.snapshot()['charged_nano'], 3996722500)

    def test_epoch_rollback_keeps_external_grant_consumed(self):
        f = self.fixture(create=False)
        event = f.broker._event
        def fail_after_claim(actor, name, **values):
            if name == 'research_epoch_created':
                raise RuntimeError('fixed post-claim crash')
            return event(actor, name, **values)
        with patch.object(f.broker, '_event', side_effect=fail_after_claim), self.assertRaises(RuntimeError):
            f.create_epoch()
        self.assertEqual(f.broker._db.execute('SELECT COUNT(*) FROM research_epochs').fetchone()[0], 0)
        with self.assertRaises(Denied):
            f.create_epoch(key='successor')
        with f.ledger._connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM research_epoch_budget_grants').fetchone()[0], 7)

    def test_full_four_stage_native_path_uses_counted_frozen_role_configs(self):
        from binding_support import resolve
        f = self.fixture(full=True)
        f.discover()
        spec, formal_job = f.auxiliary('formalization/v1')
        candidate = resolve(deepcopy(f.base.base['candidate']),
                            {'fixture:idea': f.idea, 'fixture:data_snapshot': f.base.snapshot['id']})
        output = {'status': 'final', 'candidate': candidate,
                  'semantic_report': deepcopy(f.base.base['semantic_report'])}
        post, calls = fake_post(output)
        with patch('trading_researcher.openai_provider._post', side_effect=post), patch(
                'trading_researcher.inquiry.dispatch._invoke', side_effect=lambda p, r, o, t, c: p.complete(r, o, t)):
            formal = run_auxiliary_once(f.clients['formal'], None)
        self.assertTrue(formal['accepted'], formal)
        self.assertEqual([name for name, _ in calls], ['/v1/responses/input_tokens', '/v1/responses/input_tokens', '/v1/responses'])
        self.assertEqual(calls[-1][1]['reasoning']['effort'], 'high')
        self.assertEqual(calls[-1][1]['max_output_tokens'], 32000)
        job = f.op('inspect', job_id=formal_job)
        f.op('release_batch', batch_id=job['batch_id'], target_epoch=3)
        target = f.op('get_artifact', artifact_id=formal['artifact_id'])
        self.assertEqual(target['body']['assessment']['status'], 'STRUCTURE_CHECKED')
        f.auxiliary('semantic-review/v1', target=target['id'])
        review = {'judgment': 'uncertain', 'reason': 'Synthetic transport test only.', 'added_assumptions': [],
                  'omitted_assumptions': [], 'conflicts': [], 'unresolved_meaning': ['No real model review.'],
                  'mapping_checks': [{'segment': i, 'judgment': 'uncertain', 'reason': 'Synthetic only.'}
                                     for i in range(len(target['body']['semantic_report']['segments']))]}
        post, calls = fake_post({'status': 'final', 'review': review})
        with patch('trading_researcher.openai_provider._post', side_effect=post), patch(
                'trading_researcher.inquiry.dispatch._invoke', side_effect=lambda p, r, o, t, c: p.complete(r, o, t)):
            result = run_auxiliary_once(f.clients['review'], None)
        self.assertTrue(result['accepted'], result)
        self.assertEqual(calls[-1][1]['reasoning']['effort'], 'low')
        self.assertEqual(calls[-1][1]['max_output_tokens'], 4000)
        state = f.op('inspect_research_epoch', epoch_id=f.epoch)
        self.assertEqual([c['stage'] for c in state['resource_disposition']['calls']], list(resources.STAGES))
        self.assertEqual(state['usage']['calls'], 4)
        self.assertTrue(all(decode(row[0])['resource_settlement_verified'] for row in
            f.broker._db.execute('SELECT receipt FROM research_calls WHERE epoch_id=?', (f.epoch,))))
        self.assertEqual(f.op('verify')['status'], 'PASS')


if __name__ == '__main__':
    unittest.main()
