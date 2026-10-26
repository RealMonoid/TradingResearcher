"""Independent auxiliary-boundary probes; synthetic providers confer no science."""
from copy import deepcopy
import multiprocessing
import threading
import time
import unittest

import test_auxiliary_research as support
from auxiliary_support import AuxiliaryFixture
from test_researcher import LocalClient
from trading_researcher.auxiliary import request_for, run_auxiliary_once
from trading_researcher.codec import canonical
from trading_researcher.coordination import Broker, Conflict, Denied, Invalid
from trading_researcher.researcher import ScriptedProvider


class AuxiliaryAdmissionAdversarialTests(unittest.TestCase):
    setUp = support.AuxiliaryBudgetTests.setUp
    tearDown = support.AuxiliaryBudgetTests.tearDown
    op = support.AuxiliaryBudgetTests.op
    setup_epoch = support.AuxiliaryBudgetTests.setup_epoch
    reserve = support.AuxiliaryBudgetTests.reserve
    finish = support.AuxiliaryBudgetTests.finish
    complete_job = support.AuxiliaryBudgetTests.complete_job
    auxiliary = support.AuxiliaryBudgetTests.auxiliary
    first_done = support.AuxiliaryBudgetTests.first_done

    def prepare(self, **profile_changes):
        epoch = self.first_done()
        token, spec = self.auxiliary(epoch)
        spec['research_call_profile'].update(profile_changes)
        self.op('enqueue', key='aux', spec=spec)
        client = LocalClient(self.broker, token)
        lease = client.call('claim')['lease']
        packet = client.call('auxiliary_input', lease=lease)
        return epoch, token, spec, client, lease, request_for(spec, packet)

    def dispatch(self, client, lease, request, key='aux-call', **changes):
        return client.call('reserve_research_call', lease=lease, key=key, request=request,
            **{'input_token_bound': 1024, 'output_token_limit': 64, 'cost_bound_units': 0, **changes})

    def test_exact_two_message_packet_and_type_strict_profile(self):
        epoch, _, _, client, lease, request = self.prepare(generation_parameters={'seed': 1})
        variants = []
        variant = deepcopy(request)
        variant['generation_parameters']['seed'] = True
        variants.append(variant)
        variant = deepcopy(request)
        variant['messages'].append({'role': 'assistant', 'content': 'Unapproved extra context'})
        variants.append(variant)
        variant = deepcopy(request)
        variant['messages'][1]['content'] = '{}'
        variants.append(variant)
        variant = deepcopy(request)
        variant['tools'] = [{'name': 'read_artifact'}]
        variants.append(variant)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(Invalid):
                self.dispatch(client, lease, variant)
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['calls'], 1)

    def test_original_token_and_cost_caps_are_not_auxiliary_allowances(self):
        epoch, _, _, client, lease, request = self.prepare()
        # Discovery already charged 30 tokens; the original epoch remains 80k/zero cost.
        for changes in ({'input_token_bound': 79907}, {'cost_bound_units': 1}):
            with self.subTest(changes=changes), self.assertRaises(Denied):
                self.dispatch(client, lease, request, **changes)
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['tokens'], 30)

    def test_dispatch_timeout_retains_late_response_without_candidate_authority(self):
        epoch, _, spec, client, lease, request = self.prepare()
        intent = self.dispatch(client, lease, request)
        self.now = 1005  # Call deadline reached; lease is still valid until 1010.
        output = {'status': 'final', 'candidate': None, 'semantic_report': None}
        receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'],
            response={'status': 'completed', 'output': output}, usage=None)
        self.assertTrue(receipt['late'])
        with self.assertRaises(Invalid):
            client.call('record_formalization', lease=lease, **{k: spec['research_inputs'][k] for k in ('idea_id', 'catalog_id')},
                candidate=None, semantic_report=None, provider_call_id=intent['call_id'])
        call = self.op('inspect_research_epoch', epoch_id=epoch)['calls'][-1]
        self.assertEqual(call['reply']['response']['output'], output)
        self.assertTrue(call['usage_unknown'])

    def test_original_epoch_end_blocks_output_even_with_live_lease(self):
        epoch = self.first_done()
        token, spec = self.auxiliary(epoch)
        self.op('enqueue', key='aux', spec=spec)
        self.now = 1058
        client = LocalClient(self.broker, token)
        lease = client.call('claim')['lease']
        request = request_for(spec, client.call('auxiliary_input', lease=lease))
        intent = self.dispatch(client, lease, request)
        self.assertEqual(intent['deadline'], 1060)
        self.now = 1060
        receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'],
            response={'status': 'completed', 'output': {'status': 'final', 'candidate': None, 'semantic_report': None}})
        self.assertTrue(receipt['late'])
        with self.assertRaises(Denied):
            client.call('record_formalization', lease=lease, **{k: spec['research_inputs'][k] for k in ('idea_id', 'catalog_id')},
                candidate=None, semantic_report=None, provider_call_id=intent['call_id'])

    def test_unresolved_call_survives_restart_and_cannot_authorize_new_generation(self):
        epoch, token, spec, client, lease, request = self.prepare()
        intent = self.dispatch(client, lease, request)
        self.broker.close()
        self.broker = Broker(self.tmp.name, clock=lambda: self.now)
        client = LocalClient(self.broker, token)
        self.now = 1011
        new_lease = client.call('claim')['lease']
        self.assertGreater(new_lease['generation'], lease['generation'])
        with self.assertRaises(Denied):
            self.dispatch(client, new_lease, request, key='new-generation')
        receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'],
            response={'status': 'completed', 'output': {'status': 'final', 'candidate': None, 'semantic_report': None}})
        self.assertTrue(receipt['late'])
        with self.assertRaises(Denied):
            client.call('record_formalization', lease=new_lease, **{k: spec['research_inputs'][k] for k in ('idea_id', 'catalog_id')},
                candidate=None, semantic_report=None, provider_call_id=intent['call_id'])
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['usage']['tokens'], 1118)

    def test_completed_output_cannot_be_replaced_or_used_to_start_new_transport_retry(self):
        epoch, _, _, client, lease, request = self.prepare()
        intent = self.dispatch(client, lease, request)
        response = {'status': 'completed', 'output': {'status': 'refused', 'reason': 'Retain refusal'}}
        client.call('finish_research_call', lease=lease, call_id=intent['call_id'], response=response)
        with self.assertRaises(Conflict):
            client.call('finish_research_call', lease=lease, call_id=intent['call_id'], response={'status': 'failed'})
        with self.assertRaises(Denied):
            self.dispatch(client, lease, request, key='selective-retry')
        self.assertEqual(self.op('inspect_research_epoch', epoch_id=epoch)['calls'][-1]['reply']['response'], response)

    def test_generic_routes_cannot_mint_review_or_definition_authority(self):
        _, _, _, client, lease, _ = self.prepare()
        for schema in ('semantic-review-record/1', 'feature-definitions/1'):
            body = {'schema': schema, 'scientific_readiness': True}
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                self.op('add_source', body=body, data_class='development')
            with self.subTest(schema=schema), self.assertRaises(Invalid):
                client.call('put_artifact', lease=lease, body=body, source_refs=[])


class OwnedAuxiliaryAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = AuxiliaryFixture()

    @classmethod
    def tearDownClass(cls):
        cls.fixture.close()

    def setUp(self):
        self.clients = {}

    def remember(self, case):
        self.clients[case['spec']['allowed_workers'][0]] = case['client']
        return case

    def case(self, **kwargs):
        return self.remember(self.fixture.case(**kwargs))

    def review(self, case, target):
        return self.remember(self.fixture.review(case, target))

    def tearDown(self):
        # The coordinator intentionally preserves global FIFO: even an unclaimed
        # ready test job would prevent the next test's different worker claiming.
        # Read state, then use only the normal authenticated claim/block API.
        rows = self.fixture.broker._db.execute("SELECT id FROM jobs WHERE state IN ('ready','running') ORDER BY rowid").fetchall()
        for row in rows:
            job = self.fixture.op('inspect', job_id=row['id'])
            client = self.clients.get(job['spec']['allowed_workers'][0])
            if client is None:
                continue
            if job['state'] == 'ready':
                claimed = client.call('claim')
                if claimed is None:
                    continue
                lease = claimed['lease']
            else:
                lease = {'job_id': job['id'], 'generation': job['generation']}
            self.cleanup_attempt(client, lease)

    def cleanup_attempt(self, client, lease):
        try:
            client.call('block', lease=lease, reason='Independent test finished', needs=[], retry_when='Test only')
        except (Denied, Conflict):
            pass

    def respond(self, case, output=None):
        result = self.fixture.respond(case, output)
        self.addCleanup(self.cleanup_attempt, case['client'], result[0])
        return result

    def test_candidate_substitution_and_cross_attempt_call_are_rejected(self):
        case = self.case()
        lease, intent, _ = self.respond(case)
        output = deepcopy(case['output'])
        output['candidate']['horizons']['outcome_bars'] += 1
        with self.assertRaises(Invalid):
            case['client'].call('record_formalization', lease=lease, idea_id=case['idea']['id'], catalog_id=case['catalog'],
                candidate=output['candidate'], semantic_report=output['semantic_report'], provider_call_id=intent['call_id'])
        case['client'].call('block', lease=lease, reason='Test retry', needs=[], retry_when='Same frozen job')
        self.fixture.op('resume', job_id=case['job'], reason='Test old generation rejection')
        second = case['client'].call('claim')['lease']
        self.addCleanup(self.cleanup_attempt, case['client'], second)
        with self.assertRaises(Denied):
            case['client'].call('record_formalization', lease=second, idea_id=case['idea']['id'], catalog_id=case['catalog'],
                candidate=case['output']['candidate'], semantic_report=case['output']['semantic_report'], provider_call_id=intent['call_id'])

    def test_genuine_definition_cannot_be_rebound_to_another_catalog_envelope(self):
        case = self.case()
        qualifier = self.fixture.op('add_source', body={'qualification': 'Distinct supplied catalog provenance'},
            data_class='development')
        old = self.fixture.op('get_artifact', artifact_id=case['catalog'])
        other = self.fixture.op('add_source', body=old['body'], data_class='development', exposure=[qualifier['id']])
        self.assertNotEqual(other['id'], old['id'])
        context = self.fixture.op('create_context', role='formalizer', epoch=1,
            artifact_ids=[case['idea']['id'], other['id'], case['definitions'], self.fixture.base.snapshot['id']])
        spec = deepcopy(case['spec'])
        spec['context_id'] = context['id']
        spec['research_inputs']['catalog_id'] = other['id']
        with self.assertRaises(Invalid):
            self.fixture.broker._auxiliary_packet_for_spec(spec)

    def test_genuine_definition_cannot_be_rebound_to_another_owned_snapshot(self):
        case = self.case()
        original = self.fixture.base.snapshot['body']
        manifest = deepcopy(original['manifest'])
        manifest['provenance']['revision'] += '-independent-revision'
        other = self.fixture.op('register_data_snapshot', catalog_id=original['catalog_id'],
            row_source_ids=original['row_source_ids'], manifest=manifest)
        self.assertNotEqual(other['id'], self.fixture.base.snapshot['id'])
        output = deepcopy(case['output'])
        output['candidate']['test_universe']['data_snapshot_ref'] = other['id']
        # The ordinary draft path retains unauthorized/unbound representation as
        # a gap; that must not turn the old definitions into definitions of it.
        target = self.fixture.formalize(case, output)
        with self.assertRaises(Invalid):
            self.review(case, target)

    def test_self_review_and_unaccepted_draft_targets_are_rejected(self):
        case = self.case()
        lease, intent, _ = self.respond(case)
        args = dict(lease=lease, idea_id=case['idea']['id'], catalog_id=case['catalog'],
            candidate=case['output']['candidate'], semantic_report=case['output']['semantic_report'], provider_call_id=intent['call_id'])
        draft = case['client'].call('record_formalization', **args)
        accepted = case['client'].call('record_formalization', **args)
        self.assertTrue(case['client'].call('submit', lease=lease, artifact_id=accepted['id'])['accepted'])
        target = self.fixture.op('get_artifact', artifact_id=accepted['id'])
        review = self.review(case, target)
        spec = deepcopy(review['spec'])
        # The existing principal lacks semantic capability; include it as the target's
        # authenticated name, then separately exercise the dedicated target boundary.
        spec['allowed_workers'] = [case['worker_name']]
        with self.assertRaises((Denied, Invalid)):
            self.fixture.op('enqueue', key=case['label']+'-self', spec=spec)
        with self.assertRaisesRegex(Denied, 'own artifact'):
            self.fixture.broker._auxiliary_packet_for_spec(spec)
        context = self.fixture.op('create_context', role='formalizer', epoch=2,
            artifact_ids=[draft['id'], case['idea']['id'], case['catalog'], case['definitions']])
        spec = deepcopy(review['spec'])
        spec['context_id'] = context['id']
        spec['research_inputs']['formalization_id'] = draft['id']
        with self.assertRaises(Invalid):
            self.fixture.op('enqueue', key=case['label']+'-abandoned', spec=spec)

    def test_reviewer_packet_and_read_capability_exclude_formalizer_transcript(self):
        case = self.case()
        target = self.fixture.formalize(case)
        review = self.review(case, target)
        lease = review['client'].call('claim')['lease']
        self.addCleanup(self.cleanup_attempt, review['client'], lease)
        state = review['client'].call('research_call_state', lease=lease)
        self.assertEqual(state['calls'], [])
        self.assertEqual(set(state['profile']['prompts']), set(review['spec']['allowed_workers']))
        packet = review['client'].call('auxiliary_input', lease=lease)
        serialized = canonical(packet)
        self.assertNotIn('manual-fixture', serialized)
        self.assertNotIn(case['spec']['research_call_profile']['prompt'], serialized)
        first = self.fixture.op('inspect_research_epoch', epoch_id=case['epoch'])['calls'][0]
        response_id = next(a for a in target['source_refs'] if self.fixture.op('get_artifact', artifact_id=a)['body'].get('schema') == 'provider-response/1')
        with self.assertRaises(Denied):
            review['client'].call('read_artifact', lease=lease, artifact_id=response_id)
        self.assertEqual(first['reply']['response']['provider_id'], 'manual-fixture')

    def test_review_context_cannot_smuggle_unrelated_diagnostics(self):
        case = self.case()
        target = self.fixture.formalize(case)
        review = self.review(case, target)
        diagnostic = self.fixture.op('add_source', body={'diagnostic': 'unrelated'}, data_class='development')['id']
        context = self.fixture.op('create_context', role='formalizer', epoch=2,
            artifact_ids=[target['id'], case['idea']['id'], case['catalog'], case['definitions'], diagnostic])
        with self.assertRaises(Denied):
            self.fixture.op('enqueue', key=case['label']+'-diagnostic', spec={**review['spec'], 'context_id': context['id']})

    def test_relabelled_live_scripted_faithful_review_never_becomes_approval(self):
        case = self.case(mode='live')
        target = self.fixture.formalize(case)
        review = self.review(case, target)
        output = deepcopy(review['output'])
        output['review']['judgment'] = 'faithful'
        output['review']['unresolved_meaning'] = []
        for mapping in output['review']['mapping_checks']:
            mapping['judgment'] = 'faithful'
        result = run_auxiliary_once(review['client'], ScriptedProvider([output], mode='live'))
        self.assertTrue(result['accepted'], result)
        body = self.fixture.op('get_artifact', artifact_id=result['artifact_id'])['body']
        self.assertEqual(body['provider_mode'], 'live')
        self.assertEqual(body['actual_independent_model_review'], 'UNVERIFIED')
        self.assertIs(body['scientific_readiness'], False)
        self.assertIs(result['scientific_authority'], False)

    def test_malformed_mapping_and_forged_authority_are_retained_without_review(self):
        for change in ('missing-mapping', 'bool-index', 'authority-field', 'contradictory-faithful'):
            with self.subTest(change=change):
                case = self.case()
                target = self.fixture.formalize(case)
                review = self.review(case, target)
                output = deepcopy(review['output'])
                if change == 'missing-mapping':
                    output['review']['mapping_checks'] = []
                elif change == 'bool-index':
                    output['review']['mapping_checks'][0]['segment'] = False
                elif change == 'authority-field':
                    output['review']['scientific_readiness'] = True
                else:
                    output['review']['judgment'] = 'faithful'
                lease, intent, receipt = self.respond(review, output)
                with self.assertRaises(Invalid):
                    review['client'].call('record_semantic_review', lease=lease, call_id=intent['call_id'])
                retained = self.fixture.op('get_artifact', artifact_id=receipt['response_id'])['body']
                self.assertEqual(retained['response']['output'], output)
                self.cleanup_attempt(review['client'], lease)

    def test_midcall_cancellation_reaps_child_and_retains_unknown_charge(self):
        case = self.case()
        cancel = threading.Event()
        before = {p.pid for p in multiprocessing.active_children()}
        timer = threading.Timer(0.35, cancel.set)
        timer.start()
        try:
            result = run_auxiliary_once(case['client'], ScriptedProvider([case['output']], delay_seconds=10), cancel)
        finally:
            timer.cancel()
            timer.join()
        self.assertFalse(result['accepted'])
        self.assertEqual({p.pid for p in multiprocessing.active_children()}, before)
        epoch = self.fixture.op('inspect_research_epoch', epoch_id=case['epoch'])
        self.assertEqual(epoch['usage']['calls'], 1)
        self.assertTrue(epoch['calls'][0]['usage_unknown'])
        self.assertEqual(epoch['calls'][0]['reply']['response']['status'], 'cancelled')
        self.assertIsNone(self.fixture.op('inspect', job_id=case['job'])['result_id'])


if __name__ == '__main__':
    unittest.main()
