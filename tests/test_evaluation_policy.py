"""Independent policy arithmetic and profile membership, separate from scientific admission."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest

from trading_researcher.codec import Invalid
from trading_researcher import evaluation_policy as policy
from trading_researcher.outcomes import _rational, _read_rational


FIXTURE = Path(__file__).parent/'fixtures/reference_evaluation_policy_cases.json'
PIN = 'a65153fd2e7d2f647f4ddc2860d957f937c761dfe7f376e9a2289e72f6c92960'


def read_cases():
    raw=FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==PIN
    return json.loads(raw)['cases']


def profile_inputs(data):
    candidate={'schema':'hypothesis-exec/1','claim_kind':'difference',
        'estimand':{'kind':data['estimand'],'unit':data['estimand_unit'],'direction':'positive'},
        'comparator':{'kind':data['comparator']},'horizons':{'grid_seconds':data['grid_seconds'],'outcome_bars':data['outcome_bars']},
        'outcome':{'scale':data['outcome_scale'],'program':{'expression':data['outcome_program']}}}
    definitions=[{'feature_ref':ref,**definition} for ref,definition in data['verified_feature_definitions'].items()]
    description={'type':data['outcome_type'],'unit':data['outcome_unit']}
    return candidate,definitions,description


class EvaluationPolicyTests(unittest.TestCase):
    def test_independent_policy_arithmetic_and_admission_cases(self):
        # Allocation's ten behavioral fixtures belong to the future registry state
        # machine. They are deliberately not presented as exercised by this kernel.
        exercised=0
        for case in read_cases():
            op,data,expected=case['operation'],case['input'],case['expected']
            if op=='allocation_invariant':continue
            exercised+=1
            with self.subTest(case=case['name']):
                def evaluate():
                    if op=='classify_interval':
                        return {'scientific_outcome':policy.classify_interval(*data['effect_interval'],data['delta'],data['direction'])}
                    if op=='family_budget':
                        result=policy.family_budget(data['m'])
                        return {**result,'two_sided_tail_probability':_rational(_read_rational(result['marginal_noncoverage'])/2)}
                    if op=='block_lengths':
                        return {'lengths_bars':policy.block_lengths(data['max_outcome_horizon_bars'],data['base_length_bars']),
                            'resamples_per_length':policy.MAX_RESAMPLES}
                    if op=='profile_membership':
                        try:
                            result=policy.effect_profile(*profile_inputs(data),requested_delta=data['requested_delta'])
                        except Invalid:
                            return {'eligible':False,'profile':None,'delta':None}
                        names={'binary-probability-five-percentage-points/1':'binary_probability_5pp',
                            'simple-24h-return-ten-basis-points/1':'simple_return_24h_10bp'}
                        return {'eligible':True,'profile':names[result['profile']],'delta':result['delta']}
                    if op=='bootstrap_completeness':return policy.bootstrap_family_completeness(**data)
                    if op=='basic_interval':
                        result=policy.basic_interval(data['estimate'],data['replicates_sorted'],data['marginal_noncoverage'])
                        alpha=_read_rational(data['marginal_noncoverage'])
                        return {'basic_interval':[result['lower'],result['upper']],
                            'lower_quantile':policy.quantile(data['replicates_sorted'],_rational(alpha/2)),
                            'upper_quantile':policy.quantile(data['replicates_sorted'],_rational(1-alpha/2))}
                    if op=='enclosing_interval':
                        result=policy.enclosing_interval([None if item is None else {'lower':item[0],'upper':item[1]} for item in data['intervals']])
                        return {'interval':None if result is None else [result['lower'],result['upper']],
                            'decisive_classification_permitted':False,'retain_descriptive_results':True}
                    if op=='classification_readiness':
                        return policy.classification_readiness(**data)
                    if op=='release_policy':return policy.release_decision(**data)
                    raise AssertionError(op)
                if expected.get('reject') or expected.get('accepted') is False:
                    with self.assertRaises(Invalid):evaluate()
                else:
                    actual=evaluate()
                    for name,value in expected.items():
                        if name in ('theta_interval','lower_quantile_probability','upper_quantile_probability','lower_rank','upper_rank'):
                            continue
                        self.assertEqual(actual[name],value,name)
        self.assertEqual(exercised,81)

    def test_exact_quantile_handles_unsorted_and_invalid_draws(self):
        self.assertEqual(policy.quantile([_rational(Fraction(1)),_rational(Fraction(0))],_rational(Fraction(1,2))),_rational(Fraction(1,2)))
        for values in ([],[None],[{'numerator':True,'denominator':'1'}]):
            with self.subTest(values=values),self.assertRaises(Invalid):
                policy.quantile(values,_rational(Fraction(1,2)))


if __name__=='__main__':unittest.main()
