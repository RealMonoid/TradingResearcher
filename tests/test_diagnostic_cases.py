"""DQ harness checks with scripted replies; never evidence of model behavior."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import time
import unittest

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.coordination import Broker
from trading_researcher.inquiry import diagnostic_cases as dq
from trading_researcher.inquiry.profiles import build_profile
from trading_researcher.researcher import ScriptedProvider, TOOL_DEFINITIONS, run_research_once


ROOT = Path(__file__).resolve().parents[1]


class LocalClient:
    timeout = 2

    def __init__(self, broker, token):
        self.broker, self.token = broker, token

    def call(self, operation, **args):
        return self.broker.call(self.token, operation, **args)


def profile():
    base = {'model': 'fixture/1', 'prompt_version': 'diagnostic-test-base/1',
            'max_calls': 4, 'max_tokens': 80000, 'max_seconds': 90,
            'max_cost_units': 0, 'currency': 'NONE', 'mode': 'fixture',
            'prompts': {'first': 'Investigate the supplied work item; preserve its meaning.',
                        'second': 'Independently investigate the supplied work item.'},
            'tools': deepcopy(TOOL_DEFINITIONS), 'generation_parameters': {},
            'max_output_tokens': 4096, 'call_timeout_seconds': 10, 'max_retries': 0}
    return build_profile(base, (ROOT / 'docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md').read_bytes())['profile']


class DiagnosticCaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.broker = Broker(self.tmp.name)
        self.admin = LocalClient(self.broker, self.broker.admin_token)
        self.workers = {}
        for name in ('first', 'second'):
            token = self.admin.call('register_worker', name=name, role='discovery',
                                    capabilities=['research-record/v1'])['token']
            self.workers[name] = LocalClient(self.broker, token)
        self.profile = profile()

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def install(self, case='case-a', **changes):
        self.profile.update(changes)
        prepared = dq.prepare_case(self.admin, case, self.profile, epoch=1)
        epoch = self.admin.call('create_research_epoch', key='case',
            context_id=prepared['context_id'], workers=list(self.workers), profile=self.profile)['id']
        batch = self.admin.call('create_batch', key='case', epoch=1)['id']
        for name in self.workers:
            self.admin.call('enqueue', key=name, spec={'kind': 'research-record/v1',
                'context_id': prepared['context_id'], 'purpose': dq.PURPOSE,
                'allowed_workers': [name], 'max_attempts': 1, 'lease_seconds': 8,
                'deadline': int(time.time()) + 120, 'dependencies': [],
                'batch_id': batch, 'research_epoch_id': epoch})
        self.admin.call('seal_batch', batch_id=batch)
        return prepared, epoch

    def test_seven_cases_include_four_base_cases_and_three_countervariants(self):
        self.assertEqual(dq.case_ids(), ['case-a', 'case-b', 'case-c', 'case-d', 'case-e', 'case-f', 'case-g'])
        for case in dq.case_ids():
            packet = dq.model_input(case)
            self.assertEqual(set(packet), {'purpose', 'facts'})
            self.assertEqual(packet['purpose'], dq.PURPOSE)
            for leak in ('DQ-01', 'DQ-02', 'DQ-03', 'criteria', 'must_pass', 'expected_behavior'):
                self.assertNotIn(leak, canonical(packet))
            self.assertTrue(dq.expectations(case)['criteria'])

    def test_binding_facts_independently_support_opposite_cases(self):
        bad = dq.model_input('case-a')['facts']
        good = dq.model_input('case-e')['facts']
        self.assertEqual(bad['query']['requested_symbol'], 'ALPHA')
        self.assertEqual(bad['query']['bound_symbol'], 'BETA')
        self.assertEqual(good['query']['bound_symbol'], 'ALPHA')
        self.assertEqual(sum(r['volume'] > 100 for r in bad['rows'] if r['symbol'] == 'ALPHA'), 1)
        self.assertEqual(sum(r['volume'] > 100 for r in bad['rows'] if r['symbol'] == 'BETA'), 0)
        self.assertEqual(sum(r['volume'] > 100 for r in good['rows'] if r['symbol'] == 'ALPHA'), 0)

    def test_unknown_case_and_modified_copy_cannot_rewrite_suite(self):
        with self.assertRaises(Invalid):
            dq.model_input('DQ-unknown')
        packet = dq.model_input('case-a'); packet['facts'].clear()
        self.assertTrue(dq.model_input('case-a')['facts'])

    def test_preparation_freezes_private_criteria_but_dispatches_nothing(self):
        prepared = dq.prepare_case(self.admin, 'case-a', self.profile, epoch=1)
        plan = self.admin.call('get_artifact', artifact_id=prepared['plan_id'])
        self.assertEqual(plan['data_class'], 'assessment')
        payload = json.loads(plan['body']['content']['text'])
        self.assertEqual(payload['criteria'], dq.expectations('case-a')['criteria'])
        self.assertEqual(payload['profile_sha256'], digest(self.profile))
        self.assertNotEqual(prepared['source_id'], prepared['plan_id'])
        self.assertEqual(set(prepared), {'plan_id', 'source_id', 'context_id'})

    def test_actual_worker_path_gets_only_facts_and_no_automatic_success(self):
        prepared, epoch = self.install()
        reply = {'status': 'final', 'record': {'kind': 'idea',
                 'content': {'text': 'All records are complete, so rarity is proven.'},
                 'scope': {}, 'source_refs': [prepared['source_id']]}}
        result = run_research_once(self.workers['first'], ScriptedProvider([reply]))
        self.assertTrue(result['accepted'])  # Deliberately wrong answer, structurally accepted.
        report = dq.collect_case(self.admin, prepared, epoch_id=epoch)
        self.assertEqual(report['behavioral_assessment'], 'NOT_ASSESSED')
        self.assertEqual(report['execution_kind'], 'SCRIPTED_CONTROL_ONLY')
        self.assertEqual(report['perspectives']['second']['call_count'], 0)
        wire = canonical(report['calls'][0]['request'])
        self.assertIn('ALPHA', wire)
        self.assertNotIn(prepared['plan_id'], wire)
        self.assertNotIn('DQ-01', wire)
        self.assertNotIn(dq.expectations('case-a')['criteria'][0], wire)
        self.assertIn('rarity is proven', canonical(report['calls']))

    def test_private_rubric_is_inaccessible_even_if_its_id_is_guessed(self):
        prepared, epoch = self.install('case-b')
        reply = {'status': 'tools', 'calls': [{'id': 'peek', 'name': 'read_source',
                  'arguments': {'artifact_id': prepared['plan_id']}}]}
        final = {'status': 'final', 'record': {'kind': 'idea', 'content': {'text': 'Unresolved.'},
                 'scope': {}, 'source_refs': []}}
        run_research_once(self.workers['first'], ScriptedProvider([reply, final]))
        report = dq.collect_case(self.admin, prepared, epoch_id=epoch)
        tool = next(json.loads(m['content']) for m in report['calls'][1]['request']['messages'] if m['role'] == 'tool')
        self.assertEqual(tool['result']['status'], 'tool_denied')

    def test_profile_and_context_substitution_fail_closed(self):
        prepared, epoch = self.install()
        other = dq.prepare_case(self.admin, 'case-b', self.profile, epoch=2)
        with self.assertRaises(Invalid):
            dq.collect_case(self.admin, other, epoch_id=epoch)
        wrong = deepcopy(prepared); wrong['plan_id'] = other['plan_id']
        with self.assertRaises(Invalid):
            dq.collect_case(self.admin, wrong, epoch_id=epoch)
        altered = deepcopy(self.profile); altered['max_calls'] += 1
        other_epoch = self.admin.call('create_research_epoch', key='changed-profile',
            context_id=prepared['context_id'], workers=list(self.workers), profile=altered)['id']
        with self.assertRaises(Invalid):
            dq.collect_case(self.admin, prepared, epoch_id=other_epoch)

    def test_countervariants_change_available_evidence_and_utility(self):
        ambiguous = dq.model_input('case-b')['facts']
        resolved = dq.model_input('case-f')['facts']
        self.assertEqual(ambiguous['payload'], resolved['payload'])
        self.assertNotIn('provider_receipt', ambiguous)
        self.assertNotIn('local_trace', ambiguous)
        self.assertGreater(resolved['provider_receipt']['returned_rows'], 0)
        self.assertNotEqual(resolved['local_trace']['lookup_key'], resolved['local_trace']['available_response_key'])
        wasted = dq.model_input('case-c')['facts']['follow_up']
        useful = dq.model_input('case-g')['facts']['follow_up']
        self.assertEqual(wasted['additional_observations'], 0)
        self.assertEqual(wasted['changed_decision'], 'none')
        self.assertEqual(useful['reference_case_after'], 'accepted')
        self.assertFalse(useful['original_condition_changed'])
        self.assertLess(useful['total_minutes'], wasted['total_minutes'])

    def test_replacement_plan_cannot_relax_expected_behavior(self):
        prepared, epoch = self.install()
        original = self.admin.call('get_artifact', artifact_id=prepared['plan_id'])
        plan = json.loads(original['body']['content']['text'])
        plan['criteria'] = ['Accept any answer.']
        replacement = self.admin.call('add_research', kind='source',
            content={'text': canonical(plan), 'uri': 'fixture:replacement'},
            scope={}, source_refs=[], data_class='assessment')['id']
        wrong = deepcopy(prepared); wrong['plan_id'] = replacement
        with self.assertRaises(Invalid):
            dq.collect_case(self.admin, wrong, epoch_id=epoch)

    def test_every_case_has_an_isolated_source_and_protected_expectations(self):
        sources, plans, contexts = set(), set(), set()
        for n, case in enumerate(dq.case_ids(), 1):
            prepared = dq.prepare_case(self.admin, case, self.profile, epoch=n)
            source = self.admin.call('get_artifact', artifact_id=prepared['source_id'])
            plan = self.admin.call('get_artifact', artifact_id=prepared['plan_id'])
            self.assertEqual(json.loads(source['body']['content']['text']), dq.model_input(case)['facts'])
            self.assertEqual(plan['data_class'], 'assessment')
            self.assertEqual(source['exposure'], [])
            sources.add(prepared['source_id']); plans.add(prepared['plan_id']); contexts.add(prepared['context_id'])
        self.assertEqual((len(sources), len(plans), len(contexts)), (7, 7, 7))
        self.assertFalse(sources & plans)

    def test_summaries_reject_mixed_profiles_and_caller_invented_passes(self):
        prepared, epoch = self.install()
        report = dq.collect_case(self.admin, prepared, epoch_id=epoch)
        invented = deepcopy(report); invented['behavioral_assessment'] = 'PASS'
        with self.assertRaises(Invalid):
            dq.summarize([invented])
        another = deepcopy(report); another['case_id'] = 'case-b'; another['profile_sha256'] = 'different'
        with self.assertRaises(Invalid):
            dq.summarize([report, another])

    def test_zero_calls_and_all_unrun_cases_remain_visible(self):
        prepared, epoch = self.install()
        report = dq.collect_case(self.admin, prepared, epoch_id=epoch)
        self.assertEqual(report['call_count'], 0)
        summary = dq.summarize([report])
        self.assertEqual(summary['planned_cases'], 7)
        self.assertEqual(summary['behavioral_passes'], 0)
        self.assertEqual(summary['cases']['case-b'], 'NOT_RUN')
        self.assertEqual(summary['cases']['case-a'], 'NO_CALLS')
        with self.assertRaises(Invalid):
            dq.summarize([report, report])

    def test_failed_continuation_is_retained_instead_of_a_dq_pass(self):
        prepared, epoch = self.install(max_calls=1)
        reply = {'status': 'tools', 'calls': [{'id': 'cap', 'name': 'capabilities', 'arguments': {}}]}
        result = run_research_once(self.workers['first'], ScriptedProvider([reply]))
        self.assertFalse(result['accepted'])
        report = dq.collect_case(self.admin, prepared, epoch_id=epoch)
        self.assertEqual(report['call_count'], 1)
        self.assertEqual(report['behavioral_assessment'], 'NOT_ASSESSED')
        self.assertIn('usage', report)


if __name__ == '__main__':
    unittest.main()
