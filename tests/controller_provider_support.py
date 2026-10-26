"""Small owned auxiliary fixture: no dataset, certificates or live API calls."""
from copy import deepcopy
from pathlib import Path
import tempfile
import time

from test_researcher import LocalClient
from trading_researcher.coordination import Broker
from trading_researcher import openai_provider as openai


class Fixture:
    def __init__(self, provider='openai'):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.config = openai.configuration(input_token_limit=20000, output_token_limit=1024)
        self.model = openai.MODEL
        self.parameter = 'openai_responses'
        if provider == 'anthropic':
            from trading_researcher import anthropic_provider as anthropic
            self.config = anthropic.configuration(aggregate_budget_nano=5000000000,
                budget_scope_ref='offline-controller-test', input_token_limit=20000, output_token_limit=1024)
            self.model, self.parameter = anthropic.MODEL, 'anthropic_messages'
        self.route = {self.model: {'provider': provider, 'key_file': str(self.root / 'unused-key'),
            'budget_file': str(self.root / 'unused-ledger'), 'config': self.config}}
        self.broker = Broker(self.root / 'registry', provider_routes=self.route)
        self.token = self.broker.admin_token
        self.counter = 0
        for name in ('first', 'second'):
            self.op('register_worker', name=name, role='discovery', capabilities=['research-record/v1'])

    def close(self):
        self.broker.close()
        self.temp.cleanup()

    def op(self, operation, **args):
        return self.broker.call(self.token, operation, **args)

    def case(self, **changes):
        self.counter += 1
        label = 'case-' + str(self.counter)
        idea = self.op('add_research', kind='idea', content={'text': 'An intentionally unsupported synthetic idea'},
                       scope={}, source_refs=[])['id']
        catalog = self.op('add_source', body={'schema': 'feature-catalog/1', 'features': {}}, data_class='development')['id']
        context = self.op('create_context', role='discovery', epoch=self.counter, artifact_ids=[idea,catalog])['id']
        generation = {self.parameter: deepcopy(self.config)}
        profile = {'model': self.model, 'prompt_version': 'fixture/1', 'max_calls': 12, 'max_tokens': 80000,
            'max_seconds': 1800, 'max_cost_units': 5000000000, 'currency': 'USD', 'mode': 'live',
            'prompts': {'first': 'First fixture', 'second': 'Second fixture'}, 'tools': [],
            'generation_parameters': generation, 'max_output_tokens': 1024, 'call_timeout_seconds': 10,
            'max_retries': 0, **changes}
        epoch = self.op('create_research_epoch', key=label, context_id=context, workers=['first','second'], profile=profile)['id']
        context = self.op('create_context', role='formalizer', epoch=self.counter, artifact_ids=[idea,catalog])['id']
        token = self.op('register_worker', name=label, role='formalizer', capabilities=['formalization/v1'])['token']
        call_profile = {key: profile[key] for key in ('model','prompt_version','generation_parameters',
                        'max_output_tokens','call_timeout_seconds','max_retries')}
        spec = {'kind':'formalization/v1', 'context_id':context, 'purpose':'Owned dispatch fixture',
            'allowed_workers':[label], 'max_attempts':2, 'lease_seconds':60, 'deadline':int(time.time())+1800,
            'dependencies':[], 'research_epoch_id':epoch, 'research_call_profile':{**call_profile,'prompt':'Retain unsupported meaning as a gap.'},
            'research_inputs':{'idea_id':idea,'catalog_id':catalog,'definition_ids':[]}}
        job = self.op('enqueue',key=label,spec=spec)['id']
        return {'spec':spec,'job':job,'epoch':epoch,'worker':token,'client':LocalClient(self.broker,token),
                'output':{'status':'final','candidate':None,'semantic_report':None}}

    @staticmethod
    def result(case):
        return {'response':{'status':'completed','provider_id':'offline-mock','output':case['output']},
                'usage':{'input_tokens':100,'output_tokens':100,'cost_units':1}}
