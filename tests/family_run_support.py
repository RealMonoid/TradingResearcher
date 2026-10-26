"""Owned synthetic development plan shared by family integration checks."""
from copy import deepcopy
from fractions import Fraction

from binding_support import BindingFixture
from trading_researcher.population_models import specification


class FamilyFixture:
    def __init__(self):
        self.fixture = BindingFixture()
        self.broker, self.token = self.fixture.broker, self.fixture.token
        candidate = deepcopy(self.fixture.base['candidate'])
        candidate['estimand']['unit'] = 'ratio'
        candidate['outcome']['scale'] = 'binary_probability'
        candidate['outcome']['program']['expression'] = {'op': 'gt',
            'left': {'op': 'feature', 'ref': 'BTCUSDT.close@binance-spot-15m-v1'},
            'right': {'op': 'literal', 'type': 'real', 'unit': 'USDT/BTC', 'value': '102'}}
        candidate['parameter_origins'].append({'path': '/outcome/program/expression/right/value',
            'basis': 'preexisting_specification', 'source_refs': [], 'rationale': 'Fixed synthetic family fixture'})
        case = {'change': {'candidate': candidate, 'original_idea_text': 'Synthetic binary family template.'}}
        formalization = self.fixture.create_formalization(case)
        compiled = self.fixture.compile(formalization, case)
        self.execution = self.op('execute_development', compiled_id=compiled['id'])
        self.plan = self.op('prepare_evaluation_plan', key='family-plan', compiled_id=compiled['id'], primary_count=2,
            dependence={'base_length': 1, 'rationale': 'Fixed synthetic fixture, not fitted.',
                'development_refs': [self.execution['id']],
                'randomness': {'algorithm': 'not-used-by-family', 'version': '1', 'seed': 1}})
        self.diagnostics = self.op('prepare_information_diagnostics', key='family-diagnostics',
            plan_id=self.plan['id'], execution_id=self.execution['id'], lags=[1, 2], limits={'max_seconds': 60})

    def op(self, op, **args): return self.broker.call(self.token, op, **args)

    def args(self, key):
        return {'key': key, 'plan_id': self.plan['id'], 'execution_id': self.execution['id'],
            'diagnostics_id': self.diagnostics['id'], 'specification': specification(2, Fraction(1, 2), 1, 'Fixed joint stress'),
            'components': [{'id': 'boundary', 'scenario': 1}, {'id': 'alternative', 'scenario': 2}],
            'time_rows': 64, 'seed': 101, 'bootstrap_seed': 102,
            'mc_noncoverage': {'numerator': '1', 'denominator': '100'}, 'limits': {'max_seconds': 180}}

    def close(self): self.fixture.close()
