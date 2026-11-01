"""Independent actual-role instruction binding and native transport controls."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import time
import unittest
from unittest.mock import patch

from inquiry_resource_support import Fixture, LedgerProvider, fake_post
from trading_researcher.auxiliary import request_for, run_auxiliary_once
from trading_researcher.auxiliary_views import REUSE_SCOPE, restore
from trading_researcher.codec import canonical, decode, digest, Invalid
from trading_researcher.errors import Denied
from trading_researcher.formalization import assess_candidate
from trading_researcher.coordination import Broker
from trading_researcher.inquiry import profiles
from trading_researcher.inquiry.worker import run_research_once
from trading_researcher.inquiry.resource_host import FiniteInquiryBroker
from trading_researcher.meaning_reviews import PROMPT, PROTOCOL
from trading_researcher.openai_provider import COMPACT_OUTPUT_SUFFIX, wire_request
from trading_researcher.paired_development import CONTRACT
from trading_researcher.paired_research import paired_contract


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/inquiry_actual_roles_2026-11-01.json'
FIXTURE_SHA256 = 'ddc5232c98f9b60aeb0134a14d9caf6658c4dedc4c29da66301b2da510144b42'
MATH = 'docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md'
REUSE = 'docs/architecture/20_BOUNDED_MATH_REUSE.md'


class InquiryActualRoleReviewTests(unittest.TestCase):
    def setUp(self):
        raw = FIXTURE.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), FIXTURE_SHA256)
        self.actual = json.loads(raw.decode('utf-8'))
        guard = patch('trading_researcher.openai_provider._post',
                      side_effect=AssertionError('Real HTTP forbidden in independent qualification'))
        guard.start(); self.addCleanup(guard.stop)

    def fixture(self, create=True):
        f = Fixture(create=False); self.addCleanup(f.close)
        # Exact dated prompts/settings are pinned above. Native CI copies renew
        # only expiry; this is never admission of the frozen historical profile.
        f.role_profiles['formalization/v1']['profile'] = deepcopy(self.actual['formalization_profile'])
        f.role_profiles['semantic-review/v1']['profile'] = deepcopy(self.actual['review_profile'])
        for kind, key in (('formalization/v1', 'formalization_profile'), ('semantic-review/v1', 'review_profile')):
            selected = f.role_profiles[kind]['profile']
            selected['generation_parameters']['openai_responses']['expires_at'] = int(time.time())+86400
            restored = deepcopy(selected)
            restored['generation_parameters']['openai_responses']['expires_at'] = \
                self.actual[key]['generation_parameters']['openai_responses']['expires_at']
            self.assertEqual(restored, self.actual[key])
        f.policy = f.broker.prepare_resource_disposition(f.token, role_profiles=f.role_profiles,
            discovery_run_ids=f.policy['discovery_run_ids'])
        if create: f.create_epoch()
        return f

    def assert_full_contracts(self, packet, wire, prompt):
        self.assertEqual(wire['input'][0], {'role': 'system', 'content': prompt})
        view = decode(wire['input'][1]['content'])
        self.assertEqual(restore(view), packet)
        self.assertEqual(view['activation_contract']['text'], (ROOT / REUSE).read_bytes().decode('utf-8'))
        self.assertEqual(view['activation_contract']['sha256'], hashlib.sha256((ROOT / REUSE).read_bytes()).hexdigest())
        self.assertEqual(packet['expression_contract']['text'], (ROOT / MATH).read_bytes().decode('utf-8'))
        self.assertEqual(packet['expression_contract']['sha256'], hashlib.sha256((ROOT / MATH).read_bytes()).hexdigest())
        self.assertEqual(view['source_packet_sha256'], digest(packet))

    def candidate(self, f):
        """Constants solely to reach a review packet, not a faithful-model claim."""
        truth = {'schema': 'research-ast/1', 'catalog_hash': digest(f.op('get_artifact', artifact_id=f.catalog)['body']['features']),
                 'expression': {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}}
        outcome = deepcopy(truth)
        outcome['expression'] = {'op': 'literal', 'type': 'real', 'unit': 'ratio', 'value': '0'}
        result = {'schema': 'hypothesis-exec/1', 'idea_ref': f.idea, 'claim_kind': 'difference',
            'estimand': {'kind': 'conditional-minus-scope-mean/1', 'unit': 'ratio', 'weighting': 'equal_rows',
                'missingness': 'scope-true-outcome-observed/1', 'condition_unknown': 'exclude-from-condition-retain-in-scope',
                'nuisance_fit': 'none', 'direction': 'nondirectional'},
            'scope_ast': truth, 'condition_ast': deepcopy(truth), 'outcome': {'program': outcome, 'scale': 'quantity'},
            'comparator': {'kind': 'whole_scope'}, 'horizons': {'grid_seconds': 900, 'outcome_bars': 1},
            'test_universe': {'start': '2023-01-01T00:00:00Z', 'end': '2023-01-02T00:00:00Z',
                'instruments': ['SYNTHETIC'], 'data_snapshot_ref': f.catalog},
            'parameter_origins': [], 'feature_refs': []}
        for path in ['/scope_ast/expression/value', '/condition_ast/expression/value',
                     '/outcome/program/expression/value', '/horizons/outcome_bars']:
            result['parameter_origins'].append({'path': path, 'basis': 'preexisting_specification',
                'source_refs': [f.idea], 'rationale': 'Synthetic controller fixture only; no model fidelity asserted.'})
        original = f.op('get_artifact', artifact_id=f.idea)['body']['content']['text']
        semantic = {'status': 'equivalent', 'segments': [{'text': original, 'path': '/scope_ast',
            'interpretation': 'Synthetic assertion solely for transport qualification; no actual faithful mapping.'}],
            'differences': []}
        return result, semantic

    def test_actual_candidates_exact_prefix_suffix_versions_resources_and_bounds(self):
        actual = self.actual
        old_scalar = actual['original_scalar_prompt']
        old_pair = actual['original_paired_prompt']
        formal, review = actual['formalization_profile'], actual['review_profile']
        self.assertEqual(formal['prompt'][:1500], old_scalar[:1500])
        self.assertEqual(formal['prompt'][:1500], old_pair[:1500])
        self.assertEqual(len(formal['prompt']), 8184)
        self.assertEqual(hashlib.sha256(formal['prompt'].encode()).hexdigest(), '8752022153d1291a684eee9535224937ced3c4f1b01518411f8ee01f2593389b')
        self.assertTrue(formal['prompt'].endswith(COMPACT_OUTPUT_SUFFIX))
        self.assertEqual(review['prompt'], PROMPT); self.assertEqual(review['prompt_version'], PROTOCOL)
        self.assertEqual(formal['prompt_version'], 'faithful-native-formalization/3')
        for role, in_limit, out, effort in ((formal, 48000, 32000, 'high'), (review, 76000, 4000, 'low')):
            cfg = role['generation_parameters']['openai_responses']
            self.assertEqual((role['model'], role['max_output_tokens'], role['call_timeout_seconds'], role['max_retries']),
                             ('gpt-6.1-sol', out, 360, 0))
            self.assertEqual((cfg['input_token_limit'], cfg['output_token_limit'], cfg['reasoning_effort']),
                             (in_limit, out, effort))
            self.assertEqual(cfg['bounded_math_scope'], REUSE_SCOPE)
        derived = profiles.build_profile(actual['discovery_base'], (ROOT / profiles.OWNER).read_bytes())
        self.assertEqual(derived['profile']['max_tokens'], 320000)
        self.assertEqual(sorted(map(len, derived['profile']['prompts'].values())), [8118, 8179])
        f = self.fixture()
        binding = f.op('inspect_research_epoch', epoch_id=f.epoch)['request']['inquiry_binding']['installed_sources']
        self.assertEqual(len(binding), 117)
        for name in (MATH, REUSE): self.assertEqual(binding[name], hashlib.sha256((ROOT / name).read_bytes()).hexdigest())

    def test_both_actual_scalar_roles_receive_complete_math_reuse_and_full_packet(self):
        f = self.fixture(); f.discover()
        spec, job = f.auxiliary('formalization/v1')
        packet = f.broker._auxiliary_packet_for_spec(spec)
        self.assertNotIn('candidate', packet)
        cfg = spec['research_call_profile']['generation_parameters']['openai_responses']
        self.assert_full_contracts(packet, wire_request(request_for(spec, packet), cfg), self.actual['formalization_profile']['prompt'])
        candidate, semantic = self.candidate(f)
        # Preserve the failed whole-body construction as a negative case. Native
        # owners pass only body.features into both expression engine families.
        catalog = f.op('get_artifact', artifact_id=f.catalog)['body']
        wrong = deepcopy(candidate)
        for program in (wrong['scope_ast'], wrong['condition_ast'], wrong['outcome']['program']):
            program['catalog_hash'] = digest(catalog)
        wrong_assessment = assess_candidate(f.idea,
            f.op('get_artifact', artifact_id=f.idea)['body']['content']['text'],
            wrong, semantic, catalog['features'], {*f.refs, f.idea})
        self.assertEqual(wrong_assessment['status'], 'RETAINED_GAP')
        self.assertEqual(wrong_assessment['gap']['code'], 'FEATURE_GAP')
        post, sent = fake_post({'status': 'final', 'candidate': candidate, 'semantic_report': semantic})
        with patch('trading_researcher.openai_provider._post', side_effect=post), \
                patch('trading_researcher.inquiry.dispatch._invoke', side_effect=lambda p,r,o,t,c:p.complete(r,o,t)):
            result = run_auxiliary_once(f.clients['formal'], None)
        self.assertTrue(result['accepted'], result)
        target = f.op('get_artifact', artifact_id=result['artifact_id'])
        self.assertEqual(target['body']['assessment']['status'], 'STRUCTURE_CHECKED')
        f.op('release_batch', batch_id=f.op('inspect', job_id=job)['batch_id'], target_epoch=3)
        review_spec, _ = f.auxiliary('semantic-review/v1', target=target['id'])
        lease = f.clients['review'].call('claim')['lease']
        review_packet = f.clients['review'].call('auxiliary_input', lease=lease)
        review_cfg = review_spec['research_call_profile']['generation_parameters']['openai_responses']
        self.assert_full_contracts(review_packet, wire_request(request_for(review_spec, review_packet), review_cfg), PROMPT)
        self.assertEqual(review_packet['formalization'], target)
        self.assertEqual(review_packet['formalization']['body']['original_idea']['content']['text'],
                         f.op('get_artifact', artifact_id=f.idea)['body']['content']['text'])
        # A structurally accepted synthetic assertion is no actual model semantic
        # pass, market result, public-target certificate, or future execution grant.

    def test_paired_native_denies_missing_evidence_while_pure_full_documents_remain_exact(self):
        f = self.fixture(); f.discover()
        context = f.op('create_context', role='formalizer', epoch=2,
                       artifact_ids=sorted({*f.refs, f.idea}))['id']
        spec = {'kind': 'formalization/v1', 'context_id': context, 'purpose': 'Paired transport fixture only.',
            'allowed_workers': ['formal'], 'max_attempts': 1, 'lease_seconds': 600,
            'deadline': int(time.time())+1800, 'dependencies': [], 'research_epoch_id': f.epoch,
            'research_call_profile': deepcopy(f.role_profiles['formalization/v1']['profile']),
            'research_inputs': {'idea_id': f.idea, 'catalog_id': f.catalog, 'definition_ids': [], 'paired_contract': CONTRACT}}
        with patch('trading_researcher.openai_provider._post') as post:
            with self.assertRaisesRegex(Denied, 'feature availability evidence'):
                f.op('enqueue', key='paired-transport', spec=spec)
            with_evidence = deepcopy(spec)
            with_evidence['research_inputs']['feature_certificate_id'] = f.catalog
            with patch.object(f.broker, '_paired_require_qualification',
                              wraps=f.broker._paired_require_qualification) as qualification:
                with self.assertRaises(Denied):
                    f.op('enqueue', key='paired-no-conformance', spec=with_evidence)
                self.assertGreater(qualification.call_count, 0)
            post.assert_not_called()
        # No qualification bypass: the following is a pure contract/transport
        # probe over explicit fixture sources, not a native authorized paired job.
        packet = {'schema': 'formalization-input/1', 'context_id': context,
            'inputs': spec['research_inputs'], 'sources': [
                f.op('get_artifact', artifact_id=n) for n in sorted({*f.refs, f.idea})],
            **paired_contract(spec['research_inputs'])}
        paths = ['docs/architecture/23_PAIRED_DEVELOPMENT.md', 'trading_researcher/PAIRED_DEVELOPMENT.md', MATH]
        self.assertEqual([doc['path'] for doc in packet['paired_contract']['documents']], paths)
        for doc, path in zip(packet['paired_contract']['documents'], paths, strict=True):
            self.assertEqual(doc['text'], (ROOT / path).read_bytes().decode('utf-8'))
            self.assertEqual(doc['sha256'], hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
        cfg = spec['research_call_profile']['generation_parameters']['openai_responses']
        wire = wire_request(request_for(spec, packet), cfg); view = decode(wire['input'][1]['content'])
        self.assertEqual(restore(view), packet)
        self.assertEqual(view['activation_contract']['text'], (ROOT / REUSE).read_bytes().decode('utf-8'))
        self.assertEqual(wire['input'][0]['content'], self.actual['formalization_profile']['prompt'])
        # This checks full scoped source delivery; no compatible new paired idea,
        # actual paired formalization or model interpretation is established.

    def test_preexisting_ordinary_scalar_packet_is_not_rewritten_by_new_entry_point(self):
        f = self.fixture(create=False)
        directory = f.broker.directory
        f.broker.close()
        f.broker = Broker(directory, provider_routes=f.route)
        ordinary = deepcopy(f.profile)
        ordinary['max_tokens'] = 80000
        ordinary.pop('source_presentation')
        ordinary['tools'] = []
        epoch = f.op('create_research_epoch', key='preexisting-ordinary', context_id=f.context,
            workers=['first', 'second'], profile=ordinary)['id']
        idea = f.op('add_research', kind='idea', content={'text': 'Historical packet preservation fixture.'},
                    scope={}, source_refs=[])['id']
        context = f.op('create_context', role='formalizer', epoch=2,
                       artifact_ids=sorted({f.catalog, idea}))['id']
        spec = {'kind': 'formalization/v1', 'context_id': context, 'purpose': 'Retain existing packet bytes.',
            'allowed_workers': ['formal'], 'max_attempts': 1, 'lease_seconds': 600,
            'deadline': int(time.time())+1800, 'dependencies': [], 'research_epoch_id': epoch,
            'research_call_profile': deepcopy(f.role_profiles['formalization/v1']['profile']),
            'research_inputs': {'idea_id': idea, 'catalog_id': f.catalog, 'definition_ids': []}}
        f.op('enqueue', key='historical-formal', spec=spec)
        before = f.broker._auxiliary_packet_for_spec(spec)
        self.assertNotIn('expression_contract', before)
        f.broker.close()
        f.broker = FiniteInquiryBroker(directory, provider_routes=f.route)
        self.assertEqual(f.broker._auxiliary_packet_for_spec(spec), before)
        self.assertFalse(f.broker._finite_inquiry_spec(spec))
        # Setup uses the ordinary public broker; no old grant is reset or used.

    def test_unknown_mismatched_discovery_flags_or_oversize_prompt_fail_before_grant(self):
        for defect in ('mismatch', 'unknown', 'discovery-flag', 'overlong'):
            with self.subTest(defect=defect):
                f = self.fixture(create=False)
                if defect == 'mismatch':
                    f.role_profiles['semantic-review/v1']['profile']['generation_parameters']['openai_responses'].pop('bounded_math_scope')
                elif defect == 'unknown':
                    f.role_profiles['formalization/v1']['profile']['generation_parameters']['openai_responses']['bounded_math_scope']='unknown-reuse/2'
                elif defect == 'overlong':
                    f.role_profiles['formalization/v1']['profile']['prompt'] += ' '*9
                else:
                    f.profile['generation_parameters']['openai_responses']['bounded_math_scope']=REUSE_SCOPE
                    f.bundle = profiles.build_profile(f.profile, (ROOT / profiles.OWNER).read_bytes())
                    f.binding = f.broker.prepare_inquiry_binding(f.token, base_profile=f.profile, bundle=f.bundle)
                f.policy = f.broker.prepare_resource_disposition(f.token, role_profiles=f.role_profiles,
                    discovery_run_ids=f.policy['discovery_run_ids'])
                with self.assertRaises((Invalid, Denied)): f.create_epoch()
                self.assertEqual(f.broker._db.execute('SELECT COUNT(*) FROM research_epochs').fetchone()[0], 0)
                with f.ledger._connect() as db:
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM research_epoch_budget_grants').fetchone()[0], 6)

    def test_modified_math_or_reuse_source_denies_fresh_binding(self):
        f = self.fixture(create=False)
        original = Path.read_bytes
        for relative in (MATH, REUSE):
            altered = (ROOT / relative).resolve()
            def read_bytes(path):
                raw = original(path)
                return raw+b'\nMODIFIED' if path.resolve()==altered else raw
            with self.subTest(source=relative), patch.object(Path, 'read_bytes', read_bytes), \
                    self.assertRaises((Invalid, Denied)):
                f.broker.prepare_inquiry_binding(f.token, base_profile=f.profile, bundle=f.bundle)
        self.assertEqual(f.broker._db.execute('SELECT COUNT(*) FROM research_epochs').fetchone()[0], 0)

    def test_one_owned_paired_four_stage_finite_path_without_qualification_or_ID_override(self):
        from test_binance_normalize import NormalizeTests
        from test_binance_quality import row
        from test_paired_pipeline import ORIGINAL, OwnedPairedFixture
        from trading_researcher.binance_archive import capture_provider_docs
        from trading_researcher.binance_ingest import retain_provider_documents
        from trading_researcher.paired_broker import PairedBroker

        f = self.fixture(create=False)
        normalizer = NormalizeTests()
        normalizer.root, normalizer.broker, normalizer.token = f.root, f.broker, f.token
        documents = ROOT / 'tests/fixtures/paired_provider_documents'
        expected_docs = {'README.md': '2e133d9945a9263a02781369078e72805eff074680f305cd5460016471c6caad',
            'TERMS_AND_CONDITIONS.md': '99c4921dbe023cd68c1a447775707d621453cc78aec6ac0bfe2e6c06a5114ee0'}
        raw_docs = {name: (documents/(name+'.source')).read_bytes() for name in expected_docs}
        self.assertEqual({name: hashlib.sha256(raw).hexdigest() for name,raw in raw_docs.items()}, expected_docs)
        captured = f.root/'paired-reviewed-documents'
        capture_provider_docs(captured, downloader=lambda url,limit:(raw_docs[url.rsplit('/',1)[-1]],{}))
        normalizer.docs = retain_provider_documents(f.broker, f.token, captured)['id']
        sources = [normalizer.source(b''.join(row(1577836800000+i*900000) for i in range(7)), symbol=name)
                   for name in ('BTCUSDT','ETHUSDT')]
        try:
            normalized = normalizer.run_normalize(sources, end='2020-01-01T02:00:00Z',
                instruments=['BTCUSDT','ETHUSDT'], delay=900)
        finally:
            f.broker = normalizer.broker
            for client in f.clients.values(): client.broker=f.broker
        snapshot = normalized['snapshot']
        feature = f.op('certify_features', data_snapshot_id=snapshot['id'])
        self.assertEqual(feature['body']['status'], 'CERTIFIED')
        directory = f.broker.directory
        def restart(cls, certificate=None):
            f.broker.close()
            f.broker = cls(directory, provider_routes=f.route, paired_certificate_id=certificate)
            for client in f.clients.values(): client.broker=f.broker
        restart(FiniteInquiryBroker)
        reference = f.broker.certify_paired(f.token)
        self.assertEqual(reference['body']['status'], 'CERTIFIED')
        restart(FiniteInquiryBroker, reference['id'])
        f.op('release_feature_evidence', certificate_id=feature['id'], target_epoch=1)
        f.catalog = snapshot['body']['catalog_id']
        definition = feature['body']['definitions_id']
        f.refs = [f.catalog, snapshot['id'], definition, feature['id']]
        f.context = f.op('create_context', role='discovery', epoch=1, artifact_ids=sorted(f.refs))['id']
        f.create_epoch(); f.enqueue_discovery()
        class PairedDiscovery(LedgerProvider):
            def complete(self, request, ordinal, timeout):
                result=super().complete(request,ordinal,timeout)
                result['response']['output']['record']['content']['text'] = ORIGINAL if self.worker=='first' else 'Independent B, never the selected target.'
                return result
        results=[]
        for name in ('first','second'):
            with patch('trading_researcher.inquiry.worker._invoke',side_effect=lambda p,r,o,t,c:p.complete(r,o,t)):
                result=run_research_once(f.clients[name],PairedDiscovery(f,name))
            self.assertTrue(result['accepted'],result); results.append(result)
        f.idea=results[0]['record_ids'][-1]
        f.op('release_batch',batch_id=f.batch,target_epoch=2)

        def spec(kind, target=None):
            index=2 if kind=='formalization/v1' else 3
            refs=sorted({*f.refs,f.idea,*([target] if target else [])})
            context=f.op('create_context',role='formalizer',epoch=index,artifact_ids=refs)['id']
            inputs={'idea_id':f.idea,'catalog_id':f.catalog} if index==2 else {'formalization_id':target}
            return {'kind':kind,'context_id':context,'purpose':'One owned positive paired finite-route fixture.',
                'allowed_workers':['formal' if index==2 else 'review'],'max_attempts':1,'lease_seconds':600,
                'deadline':int(time.time())+1800,'dependencies':[],'research_epoch_id':f.epoch,
                'research_call_profile':deepcopy(f.role_profiles[kind]['profile']),
                'research_inputs':{**inputs,'definition_ids':[definition],'feature_certificate_id':feature['id'],'paired_contract':CONTRACT}}
        formal_spec=spec('formalization/v1')
        # The real old broker retains its old-policy-only denial even with genuine
        # qualification and evidence. No budget.IDEA or qualification result patch.
        restart(PairedBroker,reference['id'])
        with self.assertRaisesRegex(Denied,'one-use approved continuation'):
            f.op('enqueue',key='old-broker-still-denies',spec=formal_spec)
        restart(FiniteInquiryBroker,reference['id'])
        job=f.op('enqueue',key='owned-positive-formal',spec=formal_spec)['id']
        packet=f.broker._auxiliary_packet_for_spec(formal_spec)
        self.assertEqual(packet['availability_evidence']['certificate_id'],feature['id'])
        self.assertEqual(len(packet['paired_contract']['documents']),3)
        self.assertNotIn('expression_contract',packet)
        # Reuse only the existing pure candidate builder; its constructor, which
        # overrides an old fixed IDEA, is deliberately never instantiated.
        holder=SimpleNamespace(broker=f.broker,catalog_id=f.catalog,idea=f.op('get_artifact',artifact_id=f.idea),
                               snapshot=snapshot,end='2020-01-01T02:00:00Z')
        candidate,mapping=OwnedPairedFixture.candidate(holder)
        post,sent=fake_post({'status':'final','candidate':candidate,'semantic_report':mapping})
        with patch('trading_researcher.openai_provider._post',side_effect=post), \
                patch('trading_researcher.inquiry.dispatch._invoke',side_effect=lambda p,r,o,t,c:p.complete(r,o,t)):
            formal=run_auxiliary_once(f.clients['formal'],None)
        self.assertTrue(formal['accepted'],formal)
        target=f.op('get_artifact',artifact_id=formal['artifact_id'])
        self.assertEqual(target['body']['schema'],'formalization-record/2')
        self.assertEqual(target['body']['assessment']['status'],'STRUCTURE_CHECKED')
        self.assertEqual(target['body']['original_idea']['content']['text'],ORIGINAL)
        view=decode(sent[-1][1]['input'][1]['content'])
        self.assertEqual(restore(view),packet)
        self.assertEqual(sent[-1][1]['max_output_tokens'],32000)
        f.op('release_batch',batch_id=f.op('inspect',job_id=job)['batch_id'],target_epoch=3)
        review_spec=spec('semantic-review/v1',target['id'])
        f.op('enqueue',key='owned-positive-review',spec=review_spec)
        review={'judgment':'uncertain','reason':'Synthetic transport/role fixture, no model judgment.',
            'added_assumptions':[],'omitted_assumptions':[],'conflicts':[],
            'unresolved_meaning':['No actual independent model reasoning was executed.'],
            'mapping_checks':[{'segment':i,'judgment':'uncertain','reason':'Synthetic only.'}
                              for i in range(len(mapping['segments']))]}
        post,sent=fake_post({'status':'final','review':review})
        with patch('trading_researcher.openai_provider._post',side_effect=post), \
                patch('trading_researcher.inquiry.dispatch._invoke',side_effect=lambda p,r,o,t,c:p.complete(r,o,t)):
            reviewed=run_auxiliary_once(f.clients['review'],None)
        self.assertTrue(reviewed['accepted'],reviewed)
        self.assertEqual(sent[-1][1]['max_output_tokens'],4000)
        self.assertEqual(sent[-1][1]['input'][0]['content'],PROMPT)
        review_packet=restore(decode(sent[-1][1]['input'][1]['content']))
        self.assertEqual(review_packet['paired_contract'],packet['paired_contract'])
        state=f.op('inspect_research_epoch',epoch_id=f.epoch)
        self.assertEqual([entry['stage'] for entry in state['resource_disposition']['calls']],
                         ['discovery:0','discovery:1','formalization/v1','semantic-review/v1'])
        self.assertEqual(state['usage']['calls'],4)
        for row in f.broker._db.execute('SELECT receipt FROM research_calls WHERE epoch_id=?',(f.epoch,)):
            self.assertTrue(decode(row[0])['resource_settlement_verified'])
        self.assertEqual(f.op('verify')['status'],'PASS')


if __name__ == '__main__':
    unittest.main()
