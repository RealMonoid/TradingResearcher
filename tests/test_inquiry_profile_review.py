"""Independent D096 structure and scripted-controller evidence, never model merit."""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest

from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.errors import Conflict, Denied
from trading_researcher.inquiry import profiles as api
from trading_researcher.researcher import ScriptedProvider, TOOL_DEFINITIONS, run_research_once


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / 'docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md'
OWNER_SHA256 = '3d44c368e3e010c97ac857e4b08fdc8696e79bc9e55858bb55aa2849e9690caf'
VERSION = 'discovery-inquiry-feedback/2'
PRIVATE_IDEA = 'FIRST_PRIVATE_ORIGINAL_IDEA: retain the same untested condition and horizon.'


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(encoded(value)).hexdigest()


def base_profile(perspectives=False):
    profile = {'model': 'fixture/1', 'prompt_version': 'original-discovery/7',
        'max_calls': 8, 'max_tokens': 80000, 'max_seconds': 120,
        'max_cost_units': 0, 'currency': 'NONE', 'mode': 'fixture',
        'prompts': {'first': 'Invent freely. Keep original é and e\u0301.\n',
                    'second': 'Independently explore; preserve unusual unsupported ideas.  '},
        'tools': deepcopy(TOOL_DEFINITIONS),
        'generation_parameters': {'nested': {'unchanged': ['original', '雪']}},
        'max_output_tokens': 4096, 'call_timeout_seconds': 10, 'max_retries': 0}
    if perspectives:
        profile['perspective_profiles'] = {
            worker: {'model': 'fixture/' + worker, 'prompt_version': 'original-role/' + worker,
                'generation_parameters': {'role': worker, 'nested': {'unchanged': ['original']}},
                'max_output_tokens': 4096, 'call_timeout_seconds': 10, 'max_retries': 0}
            for worker in ('first', 'second')}
    return profile


def final(text, source_refs=(), kind='idea'):
    content = {'text': text}
    if kind == 'gap':
        content.update(reason='A required input remains unavailable; no market verdict.',
                       reopen_condition='An authorized independent input/check resolves this gap.')
    return {'status': 'final', 'record': {'kind': kind, 'content': content,
            'scope': {'fixture': 'qualified control only'}, 'source_refs': list(source_refs)}}


@dataclass
class InquiryTraceProvider(ScriptedProvider):
    """Record/read/correction script; the fixed source was already in context.

    This does not test purpose before first exposure or any model reasoning.
    """
    source_id: str = ''

    def complete(self, request, ordinal, timeout):
        prior_records = []
        for message in request['messages']:
            if message['role'] != 'tool':
                continue
            body = json.loads(message['content'])
            if (body['tool_request']['name'] == 'record_research'
                    and body['result']['status'] == 'ok'):
                prior_records.append(body['result']['value']['id'])
        if ordinal == 0:
            output = {'status': 'tools', 'calls': [{'id': 'purpose-before-result',
                'name': 'record_research', 'arguments': {'kind': 'observation',
                    'content': {'text': 'Purpose: audit the query binding before interpreting empty results. '
                        'A binding defect changes the next action to technical correction; a valid binding '
                        'leaves information limits unresolved.',
                        'uncertainty': 'Earlier rarity diagnosis is an unverified interpretation.'},
                    'scope': {'object': 'binding audit'}, 'source_refs': [self.source_id]}}]}
        elif ordinal == 1:
            output = {'status': 'tools', 'calls': [{'id': 'inspect-fixed-fact',
                'name': 'read_source', 'arguments': {'artifact_id': self.source_id}}]}
        elif ordinal == 2:
            output = {'status': 'tools', 'calls': [{'id': 'retain-correction',
                'name': 'record_research', 'arguments': {'kind': 'research_experience',
                    'content': {'text': 'Correct the earlier rarity diagnosis after the fixed binding finding.',
                        'interpretation': 'The inspected source says wrong-symbol binding, not observed rarity. '
                            'Withdraw that diagnosis; preserve the original condition and all earlier records.',
                        'uncertainty': 'This scripted procedural correction supplies no market evidence or benefit estimate.',
                        'next_action': 'Use only for this source/version; review when the binding definition changes. '
                            'Repair only if authorized and within the remaining budget.'},
                    'scope': {'applies_to': 'this source binding only'},
                    'source_refs': [self.source_id, prior_records[0]]}}]}
        else:
            output = final(PRIVATE_IDEA, [self.source_id, *prior_records])
        return {'response': {'status': 'completed', 'provider_id': 'scripted-fixture/1',
                'provider_request_id': 'inquiry-fixture-' + str(ordinal), 'output': output},
            'usage': {'input_tokens': len(encoded(request)), 'output_tokens': len(encoded(output)),
                      'cost_units': 0}}


class LocalClient:
    timeout = 2

    def __init__(self, broker, token):
        self.broker, self.token = broker, token

    def call(self, operation, **arguments):
        return self.broker.call(self.token, operation, **arguments)


class InquiryProfileStructureReviewTests(unittest.TestCase):
    def setUp(self):
        self.contract = OWNER.read_bytes()
        self.assertEqual(hashlib.sha256(self.contract).hexdigest(), OWNER_SHA256)

    def test_exact_independent_profile_and_manifest_binding(self):
        base = base_profile(perspectives=True); before = encoded(base)
        result = api.build_profile(base, self.contract)
        changed = result['profile']; suffixes = []
        expected = deepcopy(base)
        for worker, original in base['prompts'].items():
            self.assertTrue(changed['prompts'][worker].startswith(original + '\n\n'))
            suffixes.append(changed['prompts'][worker][len(original) + 2:])
            expected['prompts'][worker] = original + '\n\n' + suffixes[-1]
            expected['perspective_profiles'][worker]['prompt_version'] = VERSION
        self.assertEqual(suffixes[0], suffixes[1])
        self.assertTrue(suffixes[0].startswith('[D096 inquiry-feedback/1.0 discovery addendum]'))
        expected['prompt_version'] = VERSION
        self.assertEqual(encoded(changed), encoded(expected))
        self.assertEqual(result['manifest'], {
            'schema': 'inquiry-discovery-profile/1', 'status': 'CANDIDATE_ONLY_NOT_ADMISSION',
            'contract': 'inquiry-feedback/1.0', 'decision': 'D096',
            'owner': 'docs/architecture/25_METACOGNITION_DUAL_SPACE_INQUIRY.md',
            'owner_sha256': OWNER_SHA256, 'prompt_version': VERSION,
            'base_prompt_version': 'original-discovery/7',
            'base_role_prompt_versions': {'first': 'original-role/first', 'second': 'original-role/second'},
            'base_profile_sha256': sha(base), 'profile_sha256': sha(changed),
            'instruction_utf8_sha256': hashlib.sha256(suffixes[0].encode('utf-8')).hexdigest(),
            'instruction_rules': ['I1', 'I2', 'I3', 'I4', 'I5', 'I6', 'I7', 'F1', 'F2', 'F3', 'F4', 'F5'],
            'behavioral_cases_proven': [], 'runtime_admission': False, 'scientific_authority': False})
        self.assertEqual(encoded(base), before)
        api.verify_profile(result, base, self.contract)

    def test_deep_detachment_in_both_directions_and_deterministic_build(self):
        base = base_profile(True); original = deepcopy(base)
        first = api.build_profile(base, self.contract)
        second = api.build_profile(base, self.contract)
        self.assertEqual(encoded(first), encoded(second))
        first['profile']['tools'][0]['parameters']['properties']['artifact_id']['type'] = 'changed'
        first['profile']['generation_parameters']['nested']['unchanged'].append('changed')
        first['profile']['perspective_profiles']['first']['generation_parameters']['nested']['unchanged'].append('changed')
        self.assertEqual(base, original)
        base['generation_parameters']['nested']['unchanged'].append('base changed')
        self.assertEqual(second['profile']['generation_parameters'], original['generation_parameters'])

    def test_exact_contract_bytes_not_normalized_translated_or_reencoded(self):
        wrong = [None, bytearray(self.contract), self.contract.decode('utf-8'), b'',
            self.contract + b'\n', b'\xef\xbb\xbf' + self.contract,
            self.contract.replace(b'\r\n', b'\n') if b'\r\n' in self.contract
            else self.contract.replace(b'\n', b'\r\n')]
        for contract in wrong:
            with self.subTest(type=type(contract).__name__), self.assertRaises(Invalid):
                api.build_profile(base_profile(), contract)

    @unittest.skipUnless((ROOT / '.trf-runtime/inquiry-profile-2026-11-01/source-refresh.json').exists(),
                         'Private source reconciliation absent')
    def test_authorized_refresh_preserves_old_owner_and_old_review_without_relabeling(self):
        work = ROOT / '.trf-runtime/inquiry-profile-2026-11-01'
        receipt = json.loads((work / 'source-refresh.json').read_text(encoding='utf-8'))
        old = (work / 'accepted-owner-before-clarification.md').read_bytes()
        new = (work / 'accepted-owner-after-clarification.md').read_bytes()
        self.assertEqual(hashlib.sha256(old).hexdigest(),
                         'b0aee80c2d8b2f19a26e755240fa72321d5f2466bfc3acf765770e4e525ffc8e')
        self.assertEqual(hashlib.sha256(new).hexdigest(), OWNER_SHA256)
        self.assertEqual(new, self.contract)
        start = new.index(b'### Controller integrity and diagnosis quality')
        end = new.index(b'Apply F5 through', start)
        self.assertEqual(end - start, 5669)
        self.assertEqual(new[:start] + new[end:], old)
        self.assertEqual(hashlib.sha256((work / 'independent-review.json').read_bytes()).hexdigest(),
                         '747951879b20d28fb2aba4db5356cfbd7b630efdfea3574e389565f0f9aa3fb0')
        self.assertEqual(receipt['old_review_sha256'],
                         '747951879b20d28fb2aba4db5356cfbd7b630efdfea3574e389565f0f9aa3fb0')
        with self.assertRaises(Invalid):
            api.build_profile(base_profile(), old)

    def test_two_explicit_valid_prompts_and_both_optional_roles_are_required(self):
        for prompts in (None, [], {}, {'first': 'one'}, {'first': 'a', 'second': 'b', 'third': 'c'},
                        {'first': None, 'second': 'b'}, {'first': '', 'second': 'b'},
                        {'first': '  ', 'second': 'b'}, {'': 'a', 'second': 'b'}):
            base = base_profile(); base['prompts'] = prompts
            with self.subTest(prompts=prompts), self.assertRaises(Invalid):
                api.build_profile(base, self.contract)
        for roles in (None, [], {'first': {}}, {'first': {}, 'second': {}},
                      {'first': {'prompt_version': 'a'}, 'foreign': {'prompt_version': 'b'}}):
            base = base_profile(); base['perspective_profiles'] = roles
            with self.subTest(roles=roles), self.assertRaises(Invalid):
                api.build_profile(base, self.contract)

    def test_exact_character_boundary_and_unicode_are_preserved_without_trimming(self):
        probe = base_profile(); original = probe['prompts']['first']
        appended = api.build_profile(probe, self.contract)['profile']['prompts']['first'][len(original):]
        capacity = 8192 - len(appended)
        self.assertGreater(capacity, 0)
        base = base_profile(); base['prompts']['first'] = '雪' * capacity
        self.assertEqual(len(api.build_profile(base, self.contract)['profile']['prompts']['first']), 8192)
        before = encoded(base); base['prompts']['first'] += 'x'; too_long = encoded(base)
        with self.assertRaises(Invalid):
            api.build_profile(base, self.contract)
        self.assertEqual(encoded(base), too_long)
        self.assertNotEqual(before, too_long)

    def test_repeat_application_cannot_hide_behind_an_old_version(self):
        base = base_profile(True); applied = api.build_profile(base, self.contract)['profile']
        disguised = deepcopy(applied)
        disguised['prompt_version'] = base['prompt_version']
        for name in disguised['perspective_profiles']:
            disguised['perspective_profiles'][name]['prompt_version'] = base['perspective_profiles'][name]['prompt_version']
        for changed in (applied, disguised):
            with self.assertRaises(Invalid):
                api.build_profile(changed, self.contract)
        role_only = base_profile(True)
        role_only['perspective_profiles']['second']['prompt_version'] = VERSION
        with self.assertRaises(Invalid):
            api.build_profile(role_only, self.contract)

    def test_structural_verification_rejects_all_binding_and_profile_substitutions(self):
        base = base_profile(True); bundle = api.build_profile(base, self.contract)
        mutations = []
        for key, value in (('owner_sha256', '0' * 64), ('base_profile_sha256', '0' * 64),
                           ('profile_sha256', '0' * 64), ('instruction_utf8_sha256', '0' * 64),
                           ('base_prompt_version', 'different'), ('base_role_prompt_versions', {}),
                           ('behavioral_cases_proven', ['AC-01']), ('runtime_admission', True),
                           ('scientific_authority', True)):
            altered = deepcopy(bundle); altered['manifest'][key] = value; mutations.append(altered)
        for key, value in (('max_calls', 100), ('model', 'different-model'), ('tools', []),
                           ('source_presentation', 'discovery-feedback-inline-bodies/1')):
            altered = deepcopy(bundle); altered['profile'][key] = value; mutations.append(altered)
        altered = deepcopy(bundle); altered['manifest']['extra'] = True; mutations.append(altered)
        altered = deepcopy(bundle); del altered['manifest']['owner']; mutations.append(altered)
        altered = deepcopy(bundle); altered['extra'] = True; mutations.append(altered)
        for altered in mutations:
            with self.assertRaises(Invalid):
                api.verify_profile(altered, base, self.contract)
        different_base = deepcopy(base); different_base['prompts']['first'] += ' changed'
        with self.assertRaises(Invalid):
            api.verify_profile(bundle, different_base, self.contract)

    def test_minimal_role_shapes_are_only_structural_not_controller_admission(self):
        base = base_profile()
        base['perspective_profiles'] = {name: {'prompt_version': 'old/' + name} for name in base['prompts']}
        bundle = api.build_profile(base, self.contract)
        self.assertFalse(bundle['manifest']['runtime_admission'])
        self.assertFalse(bundle['manifest']['scientific_authority'])

    @unittest.skipUnless((ROOT / '.trf-runtime/inline-feedback-bodies-2026-11-01/candidate.json').exists(),
                         'Private retained source prompts absent')
    def test_actual_retained_prompt_headroom_is_visible_and_overflow_is_not_repaired(self):
        candidate = json.loads((ROOT / '.trf-runtime/inline-feedback-bodies-2026-11-01/candidate.json').read_text(encoding='utf-8'))
        base = base_profile()
        base['prompts'] = {entry['perspective']: entry['request']['messages'][0]['content']
                           for entry in candidate['requests']}
        bundle = api.build_profile(base, self.contract)
        sizes = {name: len(value) for name, value in bundle['profile']['prompts'].items()}
        self.assertEqual(sorted(sizes.values()), [8118, 8179])
        self.assertEqual(min(8192 - n for n in sizes.values()), 13)
        longest = max(base['prompts'], key=lambda name: len(base['prompts'][name]))
        extra = 'x' * (8193 - sizes[longest])
        original = deepcopy(base); base['prompts'][longest] += extra
        with self.assertRaises(Invalid):
            api.build_profile(base, self.contract)
        self.assertEqual(base['prompts'][longest], original['prompts'][longest] + extra)


class InquiryControllerReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.broker = Broker(self.tmp.name)
        self.admin = LocalClient(self.broker, self.broker.admin_token)
        self.clients = {}
        for worker in ('first', 'second'):
            token = self.admin.call('register_worker', name=worker, role='discovery',
                                    capabilities=['research-record/v1'])['token']
            self.clients[worker] = LocalClient(self.broker, token)
        self.source = self.admin.call('add_research', kind='source',
            content={'text': 'FIXED CASE FACT: wrong-symbol binding; empty query is not evidence of rarity.',
                     'uri': 'fixture:binding-defect'}, scope={}, source_refs=[])['id']
        self.protected = self.admin.call('add_research', kind='observation',
            content={'text': 'UNRELEASED_PARTIAL_EFFECT'}, scope={}, source_refs=[],
            data_class='assessment')['id']
        self.context = self.admin.call('create_context', role='discovery', epoch=1,
                                      artifact_ids=[self.source])['id']

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def setup_epoch(self, *, perspectives=False, **changes):
        self.base = base_profile(perspectives); self.base.update(changes)
        self.bundle = api.build_profile(self.base, OWNER.read_bytes())
        self.epoch = self.admin.call('create_research_epoch', key='inquiry-epoch', context_id=self.context,
            workers=['first', 'second'], profile=self.bundle['profile'])['id']
        self.batch = self.admin.call('create_batch', key='inquiry-batch', epoch=1)['id']
        self.jobs = {}
        for worker in ('first', 'second'):
            self.jobs[worker] = self.admin.call('enqueue', key=worker, spec={
                'kind': 'research-record/v1', 'context_id': self.context,
                'purpose': 'Permitted purpose-led exploration; retain an unsupported idea or an honest gap.',
                'allowed_workers': [worker], 'max_attempts': 1, 'lease_seconds': 8,
                'deadline': int(time.time()) + 180, 'dependencies': [],
                'batch_id': self.batch, 'research_epoch_id': self.epoch})['id']
        self.admin.call('seal_batch', batch_id=self.batch)

    def calls(self):
        return self.admin.call('inspect_research_epoch', epoch_id=self.epoch)['calls']

    def test_effective_role_versions_and_original_prompts_reach_frozen_requests(self):
        self.setup_epoch(perspectives=True)
        for worker in ('first', 'second'):
            result = run_research_once(self.clients[worker], ScriptedProvider(
                [final('Unusual original ' + worker, [self.source])], model='fixture/' + worker))
            self.assertTrue(result['accepted'])
            self.assertFalse(result['genuine_discovery'])
        calls = self.calls(); self.assertEqual(len(calls), 2)
        for worker, call in zip(('first', 'second'), calls, strict=True):
            request = call['request']
            self.assertEqual(request['prompt_version'], VERSION)
            self.assertEqual(request['model'], 'fixture/' + worker)
            self.assertEqual(request['generation_parameters'], self.base['perspective_profiles'][worker]['generation_parameters'])
            self.assertEqual(request['messages'][0]['content'], self.bundle['profile']['prompts'][worker])
            self.assertTrue(request['messages'][0]['content'].startswith(self.base['prompts'][worker] + '\n\n'))
        # The stored epoch remains immutable under its request key.
        changed = deepcopy(self.bundle['profile']); changed['prompts']['first'] += ' mutation'
        with self.assertRaises(Conflict):
            self.admin.call('create_research_epoch', key='inquiry-epoch', context_id=self.context,
                            workers=['first', 'second'], profile=changed)

    def test_scripted_purpose_then_check_then_correction_preserves_original_and_peer_isolation(self):
        # The known finding is already visible in the initial source envelope.
        # This checks record/tool chronology and lineage, not unseen-result F1 compliance.
        self.setup_epoch()
        result = run_research_once(self.clients['first'], InquiryTraceProvider([], source_id=self.source))
        self.assertTrue(result['accepted'])
        self.assertFalse(result['genuine_discovery'])
        self.assertFalse(result['scientific_authority'])
        calls = self.calls(); self.assertEqual(len(calls), 4)
        purpose_id, correction_id, original_id = result['record_ids']
        purpose = self.admin.call('get_artifact', artifact_id=purpose_id)
        correction = self.admin.call('get_artifact', artifact_id=correction_id)
        original = self.admin.call('get_artifact', artifact_id=original_id)
        self.assertIn('Purpose: audit', purpose['body']['content']['text'])
        self.assertEqual(purpose['body']['kind'], 'observation')
        self.assertIn(purpose_id, correction['source_refs'])
        self.assertIn('Withdraw that diagnosis', correction['body']['content']['interpretation'])
        self.assertIn('this source binding only', correction['body']['scope']['applies_to'])
        self.assertEqual(original['body']['content']['text'], PRIVATE_IDEA)
        self.assertTrue({self.source, purpose_id, correction_id} <= set(original['exposure']))
        # The explicit read/result artifact follows the purpose record. First exposure
        # to the fixed fact preceded that record through the initial context, however.
        read_request = calls[1]['request']
        self.assertIn(purpose_id, str(read_request))
        read_result = next(json.loads(m['content']) for m in calls[2]['request']['messages']
                           if m['role'] == 'tool' and json.loads(m['content'])['tool_request']['id'] == 'inspect-fixed-fact')
        self.assertEqual(read_result['result']['status'], 'ok')
        self.assertIn('wrong-symbol binding', str(read_result['result']['value']))
        self.assertLessEqual(purpose['body']['created_at'], correction['body']['created_at'])
        # A second perspective cannot read the first private idea through memory search.
        search = {'status': 'tools', 'calls': [
            {'id': 'peer-direct-read', 'name': 'read_source', 'arguments': {'artifact_id': original_id}},
            {'id': 'private-probe', 'name': 'search_memory',
             'arguments': {'query': 'FIRST_PRIVATE_ORIGINAL_IDEA'}}]}
        second = run_research_once(self.clients['second'], ScriptedProvider(
            [search, final('SECOND_INDEPENDENT', [self.source])]))
        self.assertTrue(second['accepted'])
        second_calls = self.calls()[4:]
        self.assertNotIn(PRIVATE_IDEA, str(second_calls))
        self.assertNotIn(purpose_id, str(second_calls[0]['request']))
        self.assertNotIn(correction_id, str(second_calls[0]['request']))
        peer_result = next(json.loads(m['content']) for m in second_calls[1]['request']['messages']
                           if m['role'] == 'tool' and json.loads(m['content'])['tool_request']['id'] == 'peer-direct-read')
        self.assertEqual(peer_result['result']['status'], 'tool_denied')
        self.assertEqual(self.admin.call('verify')['status'], 'PASS')

    def test_protected_read_and_new_memory_fields_do_not_gain_authority_from_d096(self):
        self.setup_epoch()
        tools = {'status': 'tools', 'calls': [
            {'id': 'protected', 'name': 'read_source', 'arguments': {'artifact_id': self.protected}},
            {'id': 'new-schema', 'name': 'record_research', 'arguments': {
                'kind': 'observation', 'content': {'text': 'purpose', 'prospective_purpose': 'not admitted'},
                'scope': {}, 'source_refs': []}},
            {'id': 'evidence', 'name': 'record_research', 'arguments': {
                'kind': 'evidence', 'content': {'text': 'An LLM cannot publish evidence'},
                'scope': {}, 'source_refs': []}}]}
        result = run_research_once(self.clients['first'], ScriptedProvider(
            [tools, final('No input permission or schema expansion', [self.source], kind='gap')]))
        self.assertTrue(result['accepted'])
        self.assertFalse(result['scientific_authority'])
        results = [json.loads(m['content']) for m in self.calls()[1]['request']['messages'] if m['role'] == 'tool']
        self.assertEqual([x['result']['status'] for x in results], ['tool_denied'] * 3)
        self.assertNotIn('UNRELEASED_PARTIAL_EFFECT', str(self.calls()))
        self.assertNotIn(self.protected, self.admin.call('get_artifact', artifact_id=result['artifact_id'])['exposure'])

    def test_cap_stops_scripted_tool_continuation_without_reset_or_scientific_negative(self):
        self.setup_epoch(max_calls=1)
        result = run_research_once(self.clients['first'], InquiryTraceProvider([], source_id=self.source))
        self.assertEqual(result['state'], 'blocked')
        self.assertFalse(result['accepted'])
        self.assertFalse(result['scientific_authority'])
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(len(result['record_ids']), 1)
        retained = self.admin.call('get_artifact', artifact_id=result['record_ids'][0])
        self.assertEqual(retained['body']['kind'], 'observation')
        self.assertIn('Purpose:', retained['body']['content']['text'])

    def test_structural_acceptance_does_not_certify_retrospective_purpose_compliance(self):
        """Deliberate scripted F1 failure exposes the limit of profile construction."""
        self.setup_epoch()
        early_read = {'status': 'tools', 'calls': [{'id': 'read-before-purpose',
            'name': 'read_source', 'arguments': {'artifact_id': self.source}}]}
        late_purpose = {'status': 'tools', 'calls': [{'id': 'late-purpose',
            'name': 'record_research', 'arguments': {'kind': 'observation',
                'content': {'text': 'RETROSPECTIVE_PURPOSE_CASE: invented after the result was read.'},
                'scope': {}, 'source_refs': [self.source]}}]}
        result = run_research_once(self.clients['first'], ScriptedProvider(
            [early_read, late_purpose, final('A structurally valid unverified idea', [self.source])]))
        self.assertTrue(result['accepted'])
        self.assertFalse(result['genuine_discovery'])
        self.assertFalse(result['scientific_authority'])
        calls = self.calls()
        self.assertNotIn('RETROSPECTIVE_PURPOSE_CASE', str(calls[1]['request']))
        self.assertIn('RETROSPECTIVE_PURPOSE_CASE', str(calls[2]['request']))
        self.assertEqual(self.bundle['manifest']['behavioral_cases_proven'], [])
        # The controller retained the noncompliant script; it did not assess F1.

    def test_valid_records_do_not_certify_false_unresolved_or_lucky_diagnoses(self):
        """Deliberately bad scripted DQ claims remain unverified, not DQ passes."""
        facts = self.admin.call('add_research', kind='source', content={
            'text': 'SYNTHETIC FIXED FACTS: case one is a checked query-binding error, not event rarity. '
                'Case two has indistinguishable causes and no corroborating check. '
                'Case three includes a lucky outcome after a wrong cause and a costly unhelpful '
                'action after a correct cause; neither changes the diagnosis facts.',
            'uri': 'fixture:diagnosis-quality-boundaries'}, scope={}, source_refs=[])['id']
        self.context = self.admin.call('create_context', role='discovery', epoch=1,
                                      artifact_ids=[self.source, facts])['id']
        self.setup_epoch()
        claims = [
            ('DQ-01', 'Every record field and citation is valid, so the cause must be event rarity.'),
            ('DQ-02', 'Two LLMs agree, so the previously unresolved cause is now confirmed.'),
            ('DQ-03', 'The lucky profit validates the wrong explanation, and the correct cause '
                      'guarantees that its costly action was useful.')]
        output = {'status': 'tools', 'calls': [
            {'id': case, 'name': 'record_research', 'arguments': {
                'kind': 'research_experience',
                'content': {'text': 'Deliberately unsupported scripted claim ' + case,
                            'interpretation': claim},
                'scope': {'fixture_case': case}, 'source_refs': [facts]}}
            for case, claim in claims]}
        result = run_research_once(self.clients['first'], ScriptedProvider([
            output, final('All retained narratives are unverified controller fixtures.', [facts])]))
        self.assertTrue(result['accepted'])
        self.assertFalse(result['scientific_authority'])
        self.assertFalse(result['genuine_discovery'])
        self.assertEqual(len(result['record_ids']), 4)
        for identity, (case, claim) in zip(result['record_ids'][:3], claims, strict=True):
            record = self.admin.call('get_artifact', artifact_id=identity)
            self.assertEqual(record['body']['scope'], {'fixture_case': case})
            self.assertEqual(record['body']['content']['interpretation'], claim)
            self.assertIn(facts, record['source_refs'])
            self.assertEqual(record['authority'], 'unverified_work_product')
            self.assertEqual(record['data_class'], 'work_product')
            self.assertNotIn('diagnostic_quality', record['body'])
        self.assertEqual(self.bundle['manifest']['behavioral_cases_proven'], [])

    def test_later_release_context_inherits_original_exposure_without_rewriting_it(self):
        self.setup_epoch()
        first = run_research_once(self.clients['first'], ScriptedProvider([final(PRIVATE_IDEA, [self.source])]))
        second = run_research_once(self.clients['second'], ScriptedProvider([final('Second idea', [self.source])]))
        original_id = first['artifact_id']
        before = self.admin.call('get_artifact', artifact_id=original_id)
        with self.assertRaises(Denied):
            self.admin.call('create_context', role='discovery', epoch=2, artifact_ids=[original_id])
        released = self.admin.call('release_batch', batch_id=self.batch, target_epoch=2)
        self.assertTrue({original_id, second['artifact_id']} <= set(released['artifact_ids']))
        self.admin.call('create_context', role='discovery', epoch=2, artifact_ids=[original_id])
        self.assertEqual(self.admin.call('get_artifact', artifact_id=original_id), before)
        self.assertIn(self.source, before['exposure'])

    def test_profile_constructor_does_not_admit_malformed_roles_or_missing_body_table_runtime(self):
        malformed = base_profile()
        malformed['perspective_profiles'] = {name: {'prompt_version': 'old/' + name}
                                           for name in malformed['prompts']}
        candidate = api.build_profile(malformed, OWNER.read_bytes())
        with self.assertRaises(Invalid):
            self.admin.call('create_research_epoch', key='bad-role', context_id=self.context,
                            workers=['first', 'second'], profile=candidate['profile'])
        body_table = base_profile(); body_table['source_presentation'] = 'discovery-feedback-inline-bodies/1'
        candidate = api.build_profile(body_table, OWNER.read_bytes())
        with self.assertRaises(Invalid):
            self.admin.call('create_research_epoch', key='uninstalled-body-table', context_id=self.context,
                            workers=['first', 'second'], profile=candidate['profile'])


if __name__ == '__main__':
    unittest.main()
