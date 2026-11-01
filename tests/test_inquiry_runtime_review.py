"""Independent optional-runtime controls; scripts establish no AC/DQ model pass."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from trading_researcher.codec import canonical, Invalid
from trading_researcher.errors import Conflict, Denied
from trading_researcher.inquiry import presentation, profiles
from trading_researcher.inquiry.host import InquiryBroker
from trading_researcher.inquiry import worker as inquiry_worker
from trading_researcher.coordination import Broker
from trading_researcher.feedback import inline_bodies, reference_views
from trading_researcher import context_views
from trading_researcher.researcher import ScriptedProvider


ROOT = Path(__file__).resolve().parents[1]
OWNER = ROOT / profiles.OWNER
EXPECTED_TOOLS = ['read_source', 'search_memory', 'record_research', 'capabilities',
                  'measure_development', 'read_source_section', 'read_feedback_references',
                  'read_paired_feedback_references', 'read_feedback_ancestry_references']


def base_profile(**changes):
    result = {'model': 'fixture/1', 'prompt_version': 'independent-original/1',
        'max_calls': 4, 'max_tokens': 80000, 'max_seconds': 120,
        'max_cost_units': 0, 'currency': 'NONE', 'mode': 'fixture',
        'prompts': {'first': 'Invent freely; retain original meaning and unsupported ideas.',
                    'second': 'Independently invent; retain uncertainty and failures.'},
        'tools': deepcopy(presentation.TOOLS), 'source_presentation': inline_bodies.SCHEMA,
        'generation_parameters': {}, 'max_output_tokens': 2048,
        'call_timeout_seconds': 10, 'max_retries': 0}
    result.update(changes)
    return result


def final(text='Original unusual hypothesis; no empirical outcome asserted.', refs=()):
    return {'status': 'final', 'record': {'kind': 'idea', 'content': {'text': text},
            'scope': {'fixture': 'transport and access only'}, 'source_refs': list(refs)}}


class LocalClient:
    timeout = 2

    def __init__(self, broker, token):
        self.broker, self.token = broker, token

    def call(self, operation, **arguments):
        return self.broker.call(self.token, operation, **arguments)


def restore(value, original):
    """Independent recursive page assembly; check values against full originals."""
    if type(value) is dict and value.get('schema') == 'deferred-source-list/1':
        target = original
        for key in value['path']:
            target = target[int(key)] if type(target) is list else target[key]
        readers = {'read_source_section': context_views.source_section,
            'read_feedback_references': context_views.feedback_source_section,
            'read_paired_feedback_references': reference_views.reference_section,
            'read_feedback_ancestry_references': inline_bodies.ancestry_section}
        recovered, offset = [], 0
        while True:
            page = readers[value['tool']](original, value['path'], offset, 17)
            end = min(offset + 17, len(target))
            expected = {'schema': 'source-section/1', 'artifact_id': original['id'],
                'path': value['path'], 'list_sha256': hashlib.sha256(canonical(target).encode()).hexdigest(),
                'count': len(target), 'offset': offset,
                'next_offset': end if end < len(target) else None, 'values': target[offset:end]}
            if page != expected:
                raise AssertionError('Page differs from original ordered list')
            recovered.extend(page['values'])
            if page['next_offset'] is None:
                break
            offset = page['next_offset']
        if (len(recovered) != value['count'] or
                hashlib.sha256(canonical(recovered).encode()).hexdigest() != value['sha256']):
            raise AssertionError('Marker count or digest differs')
        return recovered
    if type(value) is dict:
        return {key: restore(child, original) for key, child in value.items()}
    if type(value) is list:
        return [restore(child, original) for child in value]
    return value


class InquiryPresentationReviewTests(unittest.TestCase):
    def test_exact_tool_inventory_and_profile_only_admission(self):
        self.assertEqual([tool['name'] for tool in presentation.TOOLS], EXPECTED_TOOLS)
        base = base_profile()
        profile = profiles.build_profile(base, OWNER.read_bytes())['profile']
        for change in ({'source_presentation': 'discovery-paired-feedback-view/1'},
                       {'tools': presentation.TOOLS[:-1]},
                       {'tools': list(reversed(presentation.TOOLS))}):
            with self.subTest(change=change):
                with self.assertRaises((Invalid, Denied)):
                    presentation.initial_messages({**profile, **change}, 'first', 'Purpose', [])

    def test_full_actual_thirteen_sources_reconstruct_and_remain_initially_visible(self):
        prepared = json.loads((ROOT / '.trf-runtime/development-admission-2026-10-31/prepared.json').read_text())
        originals = prepared['sources']
        self.assertEqual(len(originals), 13)
        profile = profiles.build_profile(base_profile(), OWNER.read_bytes())['profile']
        messages = presentation.initial_messages(profile, 'first', 'Independent full source check', originals)
        self.assertEqual([item['role'] for item in messages], ['system', 'user', 'user'])
        self.assertEqual(messages[0]['content'], profile['prompts']['first'])
        self.assertEqual(messages[1]['content'], presentation.NOTICE)
        packet = json.loads(messages[2]['content'])
        self.assertEqual(packet['schema'], 'discovery-feedback-inline-bodies/1')
        self.assertEqual(len(packet['inline_record_bodies']), 12)
        self.assertEqual([item['artifact_id'] for item in packet['sources']], [item['id'] for item in originals])
        self.assertEqual(sum(len(item.get('body', {}).get('retained_research_records', []))
                             for item in originals), 27)
        expanded = inline_bodies.expand(packet)
        for view, original in zip(expanded['sources'], originals, strict=True):
            self.assertEqual(restore(view['content'], original), original)
        # Complete reconstruction is a representation check, not model comprehension,
        # current native publication, actual packet admission, or first-exposure F1.

    def test_source_closure_checks_added_removed_modified_modules_and_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / 'trading_researcher'
            package.mkdir()
            code = package / 'first.py'; code.write_bytes(b'ORIGINAL\n')
            for name in presentation.SOURCE_DOCS:
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b'OWNER\n')
            with patch.object(presentation, 'ROOT', root):
                observed = presentation.source_identity()
                self.assertEqual(set(observed), {*presentation.SOURCE_DOCS, 'trading_researcher/first.py'})
                with patch.object(presentation, 'LOADED_SOURCES', observed):
                    self.assertEqual(presentation.current_sources(), observed)
                    extra = package / 'later.py'; extra.write_bytes(b'NEW\n')
                    with self.assertRaises(Denied): presentation.current_sources()
                    extra.unlink()
                    code.write_bytes(b'CHANGED\n')
                    with self.assertRaises(Denied): presentation.current_sources()
                    code.unlink()
                    with self.assertRaises(Denied): presentation.current_sources()
                    code.write_bytes(b'ORIGINAL\n')
                    (root / presentation.SOURCE_DOCS[0]).write_bytes(b'OWNER CHANGED\n')
                    with self.assertRaises(Denied): presentation.current_sources()


class InquiryBrokerReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.broker = InquiryBroker(self.tmp.name)
        self.admin = LocalClient(self.broker, self.broker.admin_token)
        self.clients = {}
        for name in ('first', 'second'):
            token = self.admin.call('register_worker', name=name, role='discovery',
                capabilities=['research-record/v1'])['token']
            self.clients[name] = LocalClient(self.broker, token)
        self.source = self.admin.call('add_research', kind='source',
            content={'text': 'KNOWN INITIAL FIXTURE FACT: a wrong-symbol query binding.',
                     'uri': 'fixture:independent-inquiry'}, scope={}, source_refs=[])['id']
        self.protected = self.admin.call('add_research', kind='observation',
            content={'text': 'HIDDEN_PARTIAL_ASSESSMENT'}, scope={}, source_refs=[],
            data_class='assessment')['id']
        self.context = self.admin.call('create_context', role='discovery', epoch=1,
            artifact_ids=[self.source])['id']

    def tearDown(self):
        self.broker.close()
        self.tmp.cleanup()

    def candidate(self, **changes):
        base = base_profile(**changes)
        bundle = profiles.build_profile(base, OWNER.read_bytes())
        binding = self.broker.prepare_inquiry_binding(self.broker.admin_token,
            base_profile=base, bundle=bundle)
        return base, bundle, binding

    def setup_epoch(self, **changes):
        self.base, self.bundle, self.binding = self.candidate(**changes)
        self.epoch = self.admin.call('create_research_epoch', key='independent-epoch',
            context_id=self.context, workers=['first', 'second'],
            profile=self.bundle['profile'], inquiry_binding=self.binding)['id']
        self.batch = self.admin.call('create_batch', key='independent-batch', epoch=1)['id']
        self.specs, self.jobs = {}, {}
        for name in ('first', 'second'):
            spec = {'kind': 'research-record/v1', 'context_id': self.context,
                'purpose': 'Free original exploration with permitted source-grounded clarification.',
                'allowed_workers': [name], 'max_attempts': 1, 'lease_seconds': 8,
                'deadline': int(time.time()) + 180, 'dependencies': [], 'batch_id': self.batch,
                'research_epoch_id': self.epoch}
            self.specs[name] = spec
            self.jobs[name] = self.admin.call('enqueue', key='independent-' + name, spec=spec)['id']
        self.admin.call('seal_batch', batch_id=self.batch)

    def state(self):
        return self.admin.call('inspect_research_epoch', epoch_id=self.epoch)

    def claim_request(self, name='first'):
        client = self.clients[name]
        claim = client.call('claim'); lease = claim['lease']
        profile = client.call('research_call_state', lease=lease)['profile']
        originals = [client.call('read_artifact', lease=lease, artifact_id=identity)
                     for identity in claim['context']['artifact_ids']]
        request = {'model': profile['model'], 'prompt_version': profile['prompt_version'],
            'tools': profile['tools'], 'generation_parameters': profile['generation_parameters'],
            'messages': presentation.initial_messages(profile, name, claim['spec']['purpose'], originals)}
        return client, lease, request

    def reserve(self, client, lease, request, key='call-0', **changes):
        args = {'input_token_bound': 12000, 'output_token_limit': 2048, 'cost_bound_units': 0}
        args.update(changes)
        return client.call('reserve_research_call', lease=lease, key=key, request=request, **args)

    def finish(self, client, lease, intent, output=None, usage=None):
        response = {'status': 'completed', 'output': final() if output is None else output,
                    'provider_id': 'independent-fixture/1'}
        usage = {'input_tokens': 12, 'output_tokens': 3, 'cost_units': 0} if usage is None else usage
        receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'],
            response=response, usage=usage)
        return response, receipt

    def test_explicit_operator_binding_and_tampered_base_manifest_sources_deny(self):
        base, bundle, binding = self.candidate()
        with self.assertRaises(Denied):
            self.broker.prepare_inquiry_binding(self.clients['first'].token,
                base_profile=base, bundle=bundle)
        for key in ('base_profile', 'profile_manifest', 'installed_sources'):
            mutated = deepcopy(binding)
            if key == 'base_profile': mutated[key]['generation_parameters'] = {'unbound': True}
            elif key == 'profile_manifest': mutated[key]['profile_sha256'] = '0' * 64
            else: mutated[key][next(iter(mutated[key]))] = '0' * 64
            with self.subTest(key=key), self.assertRaises((Invalid, Denied)):
                self.admin.call('create_research_epoch', key='tampered-' + key,
                    context_id=self.context, workers=['first', 'second'],
                    profile=bundle['profile'], inquiry_binding=mutated)
        for invalid in (None, {**binding, 'extra': True}, {**binding, 'schema': 'inquiry-runtime-binding/2'}):
            with self.assertRaises((Invalid, Denied)):
                self.admin.call('create_research_epoch', key='invalid-binding', context_id=self.context,
                    workers=['first', 'second'], profile=bundle['profile'], inquiry_binding=invalid)
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM research_epochs').fetchone()[0], 0)

    def test_native_request_packet_notice_profile_and_replay_are_exact(self):
        self.setup_epoch()
        client, lease, request = self.claim_request()
        changes = []
        for index in range(3):
            bad = deepcopy(request); bad['messages'][index]['content'] += ' UNBOUND'
            changes.append(bad)
        bad = deepcopy(request); bad['messages'].pop(1); changes.append(bad)
        for field, value in (('model', 'other'), ('prompt_version', 'old/1'),
                             ('tools', request['tools'][:-1]), ('generation_parameters', {'changed': True})):
            bad = deepcopy(request); bad[field] = value; changes.append(bad)
        for index, bad in enumerate(changes):
            with self.subTest(index=index), self.assertRaises((Invalid, Denied)):
                self.reserve(client, lease, bad, key='bad-' + str(index))
        self.assertEqual(self.state()['usage']['calls'], 0)
        intent = self.reserve(client, lease, request)
        replay = self.reserve(client, lease, request)
        self.assertFalse(replay['dispatch'])
        self.assertEqual(intent['call_id'], replay['call_id'])
        changed = deepcopy(request); changed['messages'][1]['content'] += ' UNBOUND'
        with self.assertRaises(Conflict): self.reserve(client, lease, changed)
        self.assertEqual(self.state()['calls'][0]['request'], request)
        self.assertEqual(self.state()['usage'], {'calls': 1, 'tokens': 14048, 'cost_units': 0})

    def test_continuation_requires_complete_ordered_retained_trajectory(self):
        self.setup_epoch()
        client, lease, request = self.claim_request()
        intent = self.reserve(client, lease, request)
        tool = {'id': 'actual-capability', 'name': 'capabilities', 'arguments': {}}
        response, receipt = self.finish(client, lease, intent, {'status': 'tools', 'calls': [tool]})
        expected = deepcopy(request)
        expected['messages'].append({'role': 'assistant', 'content': canonical(response)})
        with self.assertRaises(Denied): self.reserve(client, lease, expected, key='call-1')
        result = inquiry_worker._tool(client, lease, tool, intent['call_id'], presentation.TOOLS)
        body = {'schema': 'provider-tool-result/1', 'call_id': intent['call_id'],
            'tool_request': tool, 'result': {'status': 'ok', 'value': result}}
        client.call('put_artifact', lease=lease, body=body, source_refs=[])
        expected['messages'].append({'role': 'tool', 'content': canonical(body)})
        for index in (1, 3, 4):
            bad = deepcopy(expected); bad['messages'][index]['content'] += ' UNBOUND'
            with self.subTest(index=index), self.assertRaises(Invalid):
                self.reserve(client, lease, bad, key='bad-continuation-' + str(index))
        valid = self.reserve(client, lease, expected, key='call-1')
        self.finish(client, lease, valid)
        with self.assertRaises(Denied): self.reserve(client, lease, expected, key='terminal-followup')
        self.assertEqual(len(self.state()['calls']), 2)

    def test_source_drift_while_invoke_runs_commits_settlement_halt_and_no_use(self):
        self.setup_epoch()
        observed = presentation.source_identity(); drifted = False
        def identity():
            return {**observed, 'trading_researcher/added_after_dispatch.py': '0' * 64} if drifted else observed
        response = {'status': 'completed', 'output': final('DO_NOT_USE_DRIFT_RESULT'),
                    'provider_id': 'independent-fixture/1'}
        def invoke(*args):
            nonlocal drifted
            drifted = True
            return {'response': response, 'usage': {'input_tokens': 12, 'output_tokens': 3, 'cost_units': 0}}
        with patch.object(presentation, 'source_identity', side_effect=identity), \
                patch.object(inquiry_worker, '_invoke', side_effect=invoke):
            result = inquiry_worker.run_research_once(self.clients['first'], ScriptedProvider([final()]))
            self.assertFalse(result['accepted'])
            self.assertEqual(result['record_ids'], [])
            state = self.state()
            self.assertEqual(state['state'], 'halted')
            self.assertEqual(state['usage'], {'calls': 1, 'tokens': 15, 'cost_units': 0})
            self.assertEqual(state['calls'][0]['reply']['response'], response)
            row = self.broker._db.execute('SELECT receipt,response_id FROM research_calls').fetchone()
            receipt = json.loads(row['receipt'])
            self.assertFalse(receipt['installed_sources_unchanged'])
            self.assertEqual(receipt['response_id'], row['response_id'])
            self.assertIn(receipt['response_id'], result['transcript_ids'])
        self.assertEqual(self.state()['state'], 'halted')
        self.assertEqual(self.broker._db.execute(
            "SELECT COUNT(*) FROM artifacts WHERE json_extract(envelope,'$.creator')='first' "
            "AND json_extract(envelope,'$.body.schema')='research-record/1'").fetchone()[0], 0)

    def test_stale_lease_denies_pages_and_dispatch_but_retains_late_response(self):
        self.setup_epoch()
        client, lease, request = self.claim_request()
        intent = self.reserve(client, lease, request)
        with patch.object(self.broker, 'clock', return_value=int(time.time()) + 20):
            with self.assertRaises(Denied):
                client.call('read_artifact', lease=lease, artifact_id=self.source)
            with self.assertRaises(Denied):
                inquiry_worker._tool(client, lease, {'id': 'expired-page',
                    'name': 'read_feedback_ancestry_references', 'arguments': {
                        'artifact_id': self.source, 'path': [], 'offset': 0, 'limit': 1}},
                    tools=presentation.TOOLS)
            with self.assertRaises(Denied): self.reserve(client, lease, request, key='stale-call')
            response, receipt = self.finish(client, lease, intent)
            self.assertTrue(receipt['late'])
            self.assertEqual(self.state()['calls'][0]['reply']['response'], response)
        self.assertEqual(self.state()['usage']['tokens'], 15)

    def test_drift_preserves_unknown_usage_reservation_and_idempotent_receipt(self):
        self.setup_epoch()
        client, lease, request = self.claim_request()
        intent = self.reserve(client, lease, request)
        response = {'status': 'failed', 'reason': 'Uncertain provider accounting; retained.'}
        observed = presentation.source_identity()
        with patch.object(presentation, 'source_identity', return_value={**observed, 'extra.py': '0' * 64}):
            receipt = client.call('finish_research_call', lease=lease, call_id=intent['call_id'],
                                  response=response, usage=None)
            self.assertTrue(receipt['usage_unknown'])
            self.assertFalse(receipt['installed_sources_unchanged'])
            self.assertEqual(self.state()['usage']['tokens'], 14048)
            self.assertEqual(self.state()['state'], 'halted')
            again = client.call('finish_research_call', lease=lease, call_id=intent['call_id'],
                                response=response, usage=None)
            self.assertEqual(again, receipt)
            with self.assertRaises(Conflict):
                client.call('finish_research_call', lease=lease, call_id=intent['call_id'],
                            response={**response, 'changed': True}, usage=None)
        self.assertEqual(len(self.state()['calls']), 1)

    def test_peer_protected_and_malformed_pages_authenticate_parent_first(self):
        self.setup_epoch()
        first, lease, request = self.claim_request()
        own = first.call('record_research', lease=lease, kind='observation',
            content={'text': 'FIRST_PRIVATE_SCRATCH'}, scope={}, source_refs=[])['id']
        first.call('block', lease=lease, reason='Keep first scratch private while testing later perspective.',
                   needs=['fixture-only continuation'], retry_when='No automatic retry authorized.')
        peer, peer_lease, _ = self.claim_request('second')
        for name in EXPECTED_TOOLS[-2:]:
            for identity in (own, self.protected):
                tool = {'id': 'probe', 'name': name, 'arguments': {'artifact_id': identity,
                    'path': [None], 'offset': True, 'limit': 1000000}}
                with self.subTest(name=name, identity=identity), self.assertRaises(Denied):
                    inquiry_worker._tool(peer, peer_lease, tool, tools=presentation.TOOLS)
        search = peer.call('search_memory', lease=peer_lease, query='FIRST_PRIVATE_SCRATCH')
        self.assertEqual(search['records'], [])
        self.assertEqual(search['total'], 0)
        class Recorder:
            def __init__(self): self.reads = []
            def call(self, operation, **arguments):
                self.reads.append((operation, arguments)); raise Denied('Original parent unavailable')
        for name in EXPECTED_TOOLS[-2:]:
            recorder = Recorder()
            with self.assertRaises(Denied):
                inquiry_worker._tool(recorder, lease, {'id': 'probe', 'name': name,
                    'arguments': {'artifact_id': 'never-followed', 'path': [None],
                                  'offset': True, 'limit': 1000000}}, tools=presentation.TOOLS)
            self.assertEqual(recorder.reads, [('read_artifact', {'lease': lease, 'artifact_id': 'never-followed'})])

    def test_currentness_denies_enqueue_artifact_memory_reserve_and_completion(self):
        self.setup_epoch()
        client, lease, request = self.claim_request()
        retained = client.call('record_research', lease=lease, kind='idea',
            content={'text': 'Unverified original before source drift'}, scope={}, source_refs=[])['id']
        observed = presentation.source_identity()
        changed = {**observed, 'trading_researcher/new_module.py': '0' * 64}
        with patch.object(presentation, 'source_identity', return_value=changed):
            checks = [
                ('enqueue', lambda: self.admin.call('enqueue', key='drift-new-job', spec=self.specs['first'])),
                ('artifact', lambda: client.call('read_artifact', lease=lease, artifact_id=self.source)),
                ('memory', lambda: client.call('search_memory', lease=lease, query='KNOWN INITIAL')),
                ('reserve', lambda: self.reserve(client, lease, request)),
                ('completion', lambda: client.call('submit', lease=lease, artifact_id=retained)),
            ]
            for stage, operation in checks:
                with self.subTest(stage=stage), self.assertRaises((Denied, Invalid)):
                    operation()
        self.assertEqual(self.state()['usage']['calls'], 0)

    def test_new_page_routes_restore_actual_order_with_strict_paths_and_no_id_following(self):
        source = json.loads((ROOT / '.trf-runtime/development-admission-2026-10-31/prepared.json').read_text())['sources'][11]
        class AuthorizedFixture:
            def __init__(self, original): self.original, self.reads = original, []
            def call(self, operation, **arguments):
                self.reads.append((operation, arguments)); return deepcopy(self.original)
        lease = {'job_id': 'fixture-only', 'generation': 1}
        paths = [(EXPECTED_TOOLS[-2], ['body', 'cohort', 'artifact_ids']),
                 (EXPECTED_TOOLS[-1], ['body', 'evidence_at_publication', 'data_use', 'prior_knowledge', 'artifact_ids']),
                 (EXPECTED_TOOLS[-1], ['body', 'evidence_at_publication', 'data_use', 'prior_knowledge', 'context_ids'])]
        for name, path in paths:
            target = source
            for key in path: target = target[key]
            client = AuthorizedFixture(source)
            args = {'artifact_id': source['id'], 'path': path, 'offset': 0, 'limit': 3}
            result = inquiry_worker._tool(client, lease, {'id': 'page', 'name': name, 'arguments': args},
                                          tools=presentation.TOOLS)
            self.assertEqual(result['values'], target[:3])
            self.assertEqual(client.reads, [('read_artifact', {'lease': lease, 'artifact_id': source['id']})])
            for bad in ({'path': path + ['extra']}, {'offset': True}, {'offset': -1}, {'limit': 65}):
                with self.subTest(name=name, bad=bad), self.assertRaises(Invalid):
                    inquiry_worker._tool(client, lease, {'id': 'bad-page', 'name': name,
                        'arguments': {**args, **bad}}, tools=presentation.TOOLS)
        # This fixture grants a parent explicitly. It does not qualify native
        # publication-currentness admission of the old retained real manifest.

    def test_full_role_overlays_and_isolated_provider_visible_requests(self):
        selected = {name: {'model': 'fixture/' + name, 'prompt_version': 'original-role/' + name,
            'generation_parameters': {'perspective': name}, 'max_output_tokens': 2048,
            'call_timeout_seconds': 10, 'max_retries': 0} for name in ('first', 'second')}
        self.setup_epoch(perspective_profiles=selected)
        observed = []
        def invoke(provider, request, ordinal, seconds, cancelled):
            observed.append(deepcopy(request))
            return provider.complete(request, ordinal, seconds)
        with patch.object(inquiry_worker, '_invoke', side_effect=invoke):
            for name in ('first', 'second'):
                result = inquiry_worker.run_research_once(self.clients[name],
                    ScriptedProvider([final('PRIVATE_' + name)], model='fixture/' + name))
                self.assertTrue(result['accepted'])
                self.assertFalse(result['genuine_discovery'])
        self.assertEqual([call['request'] for call in self.state()['calls']], observed)
        for name, request in zip(('first', 'second'), observed, strict=True):
            self.assertEqual(request['model'], 'fixture/' + name)
            self.assertEqual(request['prompt_version'], 'discovery-inquiry-feedback/2')
            self.assertEqual(request['generation_parameters'], {'perspective': name})
            self.assertEqual(request['messages'][0]['content'], self.bundle['profile']['prompts'][name])
        self.assertNotIn('PRIVATE_first', canonical(observed[1]))

    def test_ordinary_caps_and_old_policy_grants_cannot_expand_or_reset(self):
        for field, value in (('max_tokens', 80001), ('max_calls', 13), ('max_seconds', 1801)):
            _, bundle, binding = self.candidate(**{field: value})
            with self.subTest(field=field), self.assertRaises(Invalid):
                self.admin.call('create_research_epoch', key='oversized-' + field,
                    context_id=self.context, workers=['first', 'second'],
                    profile=bundle['profile'], inquiry_binding=binding)
        _, bundle, binding = self.candidate()
        for field in ('budget_overlay', 'review_continuation'):
            with self.subTest(field=field), self.assertRaises(Denied):
                self.admin.call('create_research_epoch', key='forbidden-' + field,
                    context_id=self.context, workers=['first', 'second'], profile=bundle['profile'],
                    inquiry_binding=binding, **{field: 'old-consumed-policy'})
        self.assertEqual(self.broker._db.execute('SELECT COUNT(*) FROM research_epochs').fetchone()[0], 0)
        with tempfile.TemporaryDirectory() as directory:
            legacy = Broker(directory)
            try:
                # No old source file or global profile inventory was patched.
                self.assertNotIn(inline_bodies.SCHEMA, context_views.PRESENTATION_PROFILES)
                self.assertFalse(hasattr(legacy, 'prepare_inquiry_binding'))
            finally: legacy.close()


if __name__ == '__main__':
    unittest.main()
