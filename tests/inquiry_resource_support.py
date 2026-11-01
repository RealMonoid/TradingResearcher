"""Real temporary registries/ledgers; synthetic provider observations only."""
from copy import deepcopy
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

from trading_researcher.codec import canonical, digest
from trading_researcher.epoch_budget import _schema
from trading_researcher.openai_provider import MODEL, SpendLedger, configuration, cost_bound, provider_identity, wire_request
from trading_researcher.auxiliary_views import PROFILE
from trading_researcher.meaning_reviews import PROMPT, PROTOCOL
from trading_researcher.inquiry import presentation, profiles, resources
from trading_researcher.inquiry.resource_host import FiniteInquiryBroker
from trading_researcher.inquiry.worker import run_research_once
from test_inquiry_runtime import LocalClient


class Fixture:
    def __init__(self, full=False, create=True):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.key = self.root / 'key.env'
        self.key.write_text('OPENAI_API_KEY=sk-' + 'x' * 48 + '\n')
        self.config = configuration(74000, 6000)
        self.ledger = SpendLedger(self.root / 'spend.sqlite3', 5000000000)
        old = self.ledger.reserve('synthetic-prior-spend', 3956722500, key='prior')
        self.ledger.settle(old, 3956722500)
        with self.ledger._connect() as db:
            _schema(db)
            for approval in resources.OLD_APPROVALS:
                db.execute('INSERT INTO research_epoch_budget_grants VALUES(?,?,?,1)',
                           (approval, canonical({'synthetic': True}), canonical([{'retained': True}])))
        self.route = {MODEL: {'provider': 'openai', 'key_file': str(self.key),
                             'budget_file': str(self.ledger.path), 'config': self.config}}
        self.base = None
        if full:
            from binding_support import BindingFixture
            import test_binance_normalize
            with patch.object(test_binance_normalize, 'Broker',
                              side_effect=lambda *a, **kw: FiniteInquiryBroker(*a, provider_routes=self.route, **kw)):
                self.base = BindingFixture()
            self.broker = self.base.broker
        else:
            self.broker = FiniteInquiryBroker(self.root / 'registry', provider_routes=self.route)
        self.token = self.broker.admin_token
        self.clients = {}
        for name, role, kind in [('first', 'discovery', 'research-record/v1'),
                                 ('second', 'discovery', 'research-record/v1'),
                                 ('formal', 'formalizer', 'formalization/v1'),
                                 ('review', 'formalizer', 'semantic-review/v1')]:
            token = self.op('register_worker', name=name, role=role, capabilities=[kind])['token']
            self.clients[name] = LocalClient(self.broker, token)
        self.catalog = (self.base.snapshot['body']['catalog_id'] if full else self.op('add_source',
            body={'schema': 'feature-catalog/1', 'features': {}}, data_class='development')['id'])
        self.refs = ([self.catalog, self.base.snapshot['id'], self.base.feature['body']['definitions_id']]
                     if full else [self.catalog])
        self.context = self.op('create_context', role='discovery', epoch=1, artifact_ids=self.refs)['id']
        self.role_profiles = {}
        for index, worker in ((2, 'formal'), (3, 'review')):
            config = configuration(resources.INPUT_MAX[index], resources.OUTPUT[index])
            config.update(source_presentation=PROFILE, reasoning_effort='high' if index == 2 else 'low')
            role = {'model': MODEL, 'prompt_version': 'synthetic-full-formalizer/1' if index == 2 else PROTOCOL,
                    'prompt': 'Faithfully preserve the complete supplied idea; retain unsupported meanings as gaps.' if index == 2 else PROMPT,
                    'generation_parameters': {'openai_responses': config}, 'max_output_tokens': resources.OUTPUT[index],
                    'call_timeout_seconds': resources.TIMEOUT[index], 'max_retries': 0}
            self.role_profiles[resources.STAGES[index]] = {'worker': worker, 'profile': role}
        self.policy = self.broker.prepare_resource_disposition(self.token, role_profiles=self.role_profiles,
                                discovery_run_ids={'first': 'synthetic-first', 'second': 'synthetic-second'})
        self.profile = {'model': MODEL, 'prompt_version': 'synthetic-discovery/1', 'mode': 'live',
                        'max_calls': 4, 'max_tokens': 320000, 'max_seconds': 1800,
                        'currency': 'USD', 'max_cost_units': 1043277500,
                        'prompts': {'first': 'Invent freely.', 'second': 'Independently explore.'},
                        'source_presentation': presentation.SCHEMA, 'tools': deepcopy(presentation.TOOLS),
                        'generation_parameters': {'openai_responses': self.config}, 'max_output_tokens': 6000,
                        'call_timeout_seconds': 240, 'max_retries': 0}
        self.bundle = profiles.build_profile(self.profile, Path(profiles.OWNER).read_bytes())
        self.binding = self.broker.prepare_inquiry_binding(self.token, base_profile=self.profile, bundle=self.bundle)
        if create:
            self.create_epoch()

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def close(self):
        if self.base:
            self.base.close()
        else:
            self.broker.close()
        self.temp.cleanup()

    def create_epoch(self, key='finite'):
        self.epoch = self.op('create_research_epoch', key=key, context_id=self.context,
            workers=['first', 'second'], profile=self.bundle['profile'], inquiry_binding=self.binding,
            resource_disposition=self.policy)['id']
        return self.epoch

    def enqueue_discovery(self):
        self.batch = self.op('create_batch', key='discoveries', epoch=1)['id']
        self.jobs = {}
        for name in ('first', 'second'):
            self.jobs[name] = self.op('enqueue', key='discovery-' + name, spec={
                'kind': 'research-record/v1', 'context_id': self.context, 'purpose': 'Synthetic resource-path test.',
                'allowed_workers': [name], 'max_attempts': 1, 'lease_seconds': 600,
                'deadline': int(time.time()) + 1800, 'dependencies': [], 'batch_id': self.batch,
                'research_epoch_id': self.epoch})['id']
        self.op('seal_batch', batch_id=self.batch)

    def discover(self):
        self.enqueue_discovery()
        results = []
        for name in ('first', 'second'):
            provider = LedgerProvider(self, name)
            with patch('trading_researcher.inquiry.worker._invoke',
                       side_effect=lambda p, r, o, t, c: p.complete(r, o, t)):
                result = run_research_once(self.clients[name], provider)
            assert result['accepted'], result
            results.append(result)
        self.idea = results[0]['record_ids'][-1]
        self.op('release_batch', batch_id=self.batch, target_epoch=2)
        return results

    def auxiliary(self, kind, target=None):
        index = resources.STAGES.index(kind)
        worker = 'formal' if index == 2 else 'review'
        definitions = [self.base.feature['body']['definitions_id']] if self.base else []
        refs = self.refs + [self.idea]
        if index == 3:
            refs = [self.catalog, self.idea, *definitions, target]
        context = self.op('create_context', role='formalizer', epoch=index,
                          artifact_ids=sorted(set(refs)))['id']
        inputs = ({'idea_id': self.idea, 'catalog_id': self.catalog, 'definition_ids': definitions}
                  if index == 2 else {'formalization_id': target, 'definition_ids': definitions})
        spec = {'kind': kind, 'context_id': context, 'purpose': 'Synthetic complete role-path test.',
                'allowed_workers': [worker], 'max_attempts': 1, 'lease_seconds': 600,
                'deadline': int(time.time()) + 1800, 'dependencies': [],
                'research_epoch_id': self.epoch, 'research_call_profile': self.role_profiles[kind]['profile'],
                'research_inputs': inputs}
        job = self.op('enqueue', key='stage-' + worker, spec=spec)['id']
        return spec, job


class LedgerProvider:
    model, mode = MODEL, 'live'

    def __init__(self, fixture, worker, bound=1128, ledger=True):
        self.fixture, self.worker, self.bound, self.write_ledger = fixture, worker, bound, ledger
        self.run_id = fixture.policy['discovery_run_ids'][worker]

    def reservation(self, request, output_limit):
        return {'input_token_bound': self.bound, 'output_token_limit': output_limit,
                'cost_bound_units': cost_bound(self.bound, output_limit)}

    def complete(self, request, ordinal, timeout):
        f, name = self.fixture, self.worker
        text = (f.base.base['original_idea_text'] if f.base else 'A synthetic unsupported original idea.')
        output = {'status': 'final', 'record': {'kind': 'idea', 'content': {'text': text + ('' if name == 'first' else ' Independent B.')},
                                              'scope': {}, 'source_refs': []}}
        run = f.policy['discovery_run_ids'][name]
        usage = {'input_tokens': 1000, 'output_tokens': 20, 'cost_units': 2700000}
        public = {'status': 'completed', 'provider_id': 'openai.responses/1', 'output': output,
                  'counted_input_tokens': 1000, 'wire_request_sha256': digest(wire_request(request, f.config)),
                  'aggregate_dispatch_id': run + ':0', 'model_identity': provider_identity(MODEL),
                  'token_usage_details': {'cached_input_tokens': 0, 'reasoning_output_tokens': 0},
                  'transport_request_id': 'synthetic-transport-' + name, 'provider_request_id': 'synthetic-response-' + name}
        if self.write_ledger:
            identity = f.ledger.reserve(public['wire_request_sha256'], cost_bound(self.bound, 6000), key=run + ':0',
                metadata={'run_id': run, 'ordinal': 0, 'epoch_id': f.epoch, 'worker': name, 'model': MODEL,
                          'prompt_version': request['prompt_version'], 'counted_input_tokens': 1000,
                          'model_identity': provider_identity()})
            f.ledger.settle(identity, usage['cost_units'], receipt={'usage': usage,
                'token_details': public['token_usage_details'], 'response_status': public['status'],
                'transport_request_id': public['transport_request_id'], 'provider_request_id': public['provider_request_id'],
                'model_identity': public['model_identity']})
        return {'response': public, 'usage': usage}


def fake_post(output):
    calls = []
    def post(endpoint, payload, key, deadline):
        calls.append((endpoint, deepcopy(payload)))
        if endpoint.endswith('/input_tokens'):
            return {'object': 'response.input_tokens', 'input_tokens': 1000}, 'synthetic-count'
        return {'id': 'synthetic-aux', 'model': MODEL, 'service_tier': 'default', 'status': 'completed',
                'usage': {'input_tokens': 1000, 'output_tokens': 20},
                'output': [{'type': 'message', 'role': 'assistant', 'status': 'completed',
                            'content': [{'type': 'output_text', 'text': canonical(output), 'annotations': []}]}]}, 'synthetic-aux-transport'
    return post, calls
