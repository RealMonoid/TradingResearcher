"""Independent preimplementation arithmetic oracles and diagnostic boundaries."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import unittest

from trading_researcher.codec import Invalid, canonical, digest
from trading_researcher.expressions import ExpressionGap
from trading_researcher.information_diagnostics import diagnose, validate_lags
from trading_researcher.outcomes import materialize_reference, STATES


FIXTURES=Path(__file__).parent/'fixtures'
EXPECTED_HASHES={
    'information_diagnostics_cases.json':'e2b8233b7b8ed1917f9392eb0c989279837f88219843371f35740908ccbb6b6f',
    'information_diagnostics_expectations.md':'a30e91ec64b2e2bbc307a3e6b9ba4e54902aaa23dd4ed2ce926060eda670d065',
}


def fraction(value):
    return Fraction(int(value['numerator']),int(value['denominator']))


def rational(value):
    if value is None:return None
    value=Fraction(value)
    return {'numerator':str(value.numerator),'denominator':str(value.denominator)}


def moments(values,lags):
    mean=sum(values,Fraction(0))/len(values)
    result=[]
    for lag in [0,*lags]:
        pairs=max(0,len(values)-lag)
        product=(sum(((values[t-lag]-mean)*(values[t]-mean)
                      for t in range(lag,len(values))),Fraction(0))/pairs) if pairs else None
        result.append({'lag':lag,'pairs':pairs,'covariance':rational(product)})
    return {'mean':rational(mean),'lags':result}


class InformationDiagnosticsAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        data=json.loads((FIXTURES/'information_diagnostics_cases.json').read_text(encoding='utf-8'))
        cls.fixtures={value['id']:value for value in data['fixtures']}

    def fixture(self,name='six_time_hand_report'):
        return deepcopy(self.fixtures[name])

    def assert_moments(self,actual,expected):
        self.assertEqual(actual['mean'],expected['mean'])
        self.assertEqual(actual['lags'],[{'lag':v['lag'],'pairs':v['pairs'],
            'covariance':v['centered_product']} for v in expected['lags']])

    def assert_pair(self,actual,expected):
        self.assertEqual(actual['lag'],expected['lag'])
        self.assertEqual(actual['eligible_pairs'],expected['pairs'])
        self.assertEqual(actual['paired_left_mean'],expected['left_pair_mean'])
        self.assertEqual(actual['paired_right_mean'],expected['right_pair_mean'])
        self.assertEqual(actual['fixed_center_product'],expected['fixed_marginal_centered_product'])

    def test_independent_fixture_bytes_are_frozen_and_raw_counterpart_replays(self):
        for name,expected in EXPECTED_HASHES.items():
            self.assertEqual(hashlib.sha256((FIXTURES/name).read_bytes()).hexdigest(),expected)
        fixture=self.fixture('six_time_raw_coherent')
        self.assertEqual(materialize_reference(fixture['report']['request'],
            fixture['raw_catalog'],fixture['raw_rows']),fixture['report'])

    def test_pooled_unknown_counts_full_grid_score_and_residual_moments(self):
        fixture=self.fixture();expected=fixture['expected'];rows=[]
        result=diagnose(fixture['report'],fixture['lags'],on_contribution=rows.append)
        self.assertEqual(result['status'],'COMPUTED_DIAGNOSTICS')
        self.assertEqual(result['time_rows'],6)
        actual=result['totals'];want=expected['pooled']
        self.assertEqual(actual['scope'],{'count':want['eligible'],'successes':want['events'],'rate':want['q']})
        for group in ('true','false','unknown'):
            self.assertEqual(actual[group],{'count':want[group]['count'],'successes':want[group]['events'],
                                           'rate':want[group]['rate']})
        self.assertEqual(actual['condition_fraction'],want['w'])
        self.assertEqual(actual['observed_contrast'],want['effect'])
        fields={'N':'scope_count','S':'scope_successes','C':'condition_count','Z':'condition_successes'}
        for row,wanted in zip(rows,expected['contributions']):
            self.assertEqual(row['decision_time'],wanted['decision_time'])
            for key,field in fields.items():self.assertEqual(row[field],wanted[key])
        self.assertEqual(len(rows),6)
        self.assert_moments(result['grid_moments']['scope_count'],expected['global_moments']['N'])
        self.assert_moments(result['grid_moments']['condition_count'],expected['global_moments']['C'])
        self.assert_moments(result['grid_moments']['contrast_score'],expected['global_moments']['score'])
        scope=[Fraction(r['S'])-Fraction(3,7)*r['N'] for r in expected['contributions']]
        conditioned=[Fraction(r['Z'])-Fraction(1,2)*r['C'] for r in expected['contributions']]
        score=[6*a/4-6*b/7 for a,b in zip(conditioned,scope)]
        self.assertEqual(list(map(rational,score)),expected['score'])
        self.assertEqual(sum(score),0)
        for name,values in [('scope_residual',scope),('condition_residual',conditioned)]:
            actual=result['grid_moments'][name];wanted=moments(values,fixture['lags'])
            self.assertEqual(actual['mean'],wanted['mean'])
            self.assertEqual(actual['lags'],wanted['lags'])
        self.assertIsNone(result['n_min'])
        self.assertFalse(result['scientific_readiness'])
        self.assertFalse(result['classification_permitted'])

    def test_outcome_pair_marginals_follow_earlier_then_later_time_order(self):
        fixture=self.fixture();result=diagnose(fixture['report'],fixture['lags'])
        instruments={x['instrument']:x for x in result['instrument_diagnostics']}
        for name,expected in fixture['expected']['by_instrument'].items():
            actual=instruments[name]
            self.assertEqual(actual['groups']['scope']['rate'],expected['q'])
            self.assertEqual(actual['groups']['condition_fraction'],expected['w'])
            for row,wanted in zip(actual['outcome_lag_products'],expected['outcome_lags']):
                self.assert_pair(row,wanted)
            self.assertTrue(all('pair_order' in row for row in actual['outcome_lag_products']))
        for actual,expected in zip(result['cross_instrument_products'],fixture['expected']['common_time_outcome_pairs']):
            self.assert_pair(actual,expected)
            self.assertEqual(actual['left_instrument'],expected['left'])
            self.assertEqual(actual['right_instrument'],expected['right'])
            self.assertNotEqual(actual['left_center'],actual['paired_left_mean'])

    def test_boolean_or_noninteger_state_counts_are_not_integer_evidence(self):
        for bad in (True,'1','01',1.0):
            report=self.fixture()['report'];report['state_counts']['OUTCOME_MISSING']=bad
            with self.subTest(bad=bad),self.assertRaises((Invalid,ExpressionGap)):
                diagnose(report,[1])
        report=self.fixture()['report'];report['state_counts']['OUTCOME_PENDING']=False
        with self.assertRaises((Invalid,ExpressionGap)):diagnose(report,[1])

    def test_coherent_missing_row_fixture_keeps_extra_previous_outcome_gaps(self):
        fixture=self.fixture('six_time_raw_coherent');rows=[]
        result=diagnose(fixture['report'],fixture['lags'],on_contribution=rows.append)
        expected=fixture['expected'];pooled=expected['pooled']
        self.assertEqual(result['totals']['scope']['count'],5)
        self.assertEqual(result['totals']['scope']['rate'],pooled['q'])
        self.assertEqual(result['totals']['condition_fraction'],pooled['w'])
        self.assertEqual(result['totals']['observed_contrast'],pooled['effect'])
        self.assert_moments(result['grid_moments']['contrast_score'],expected['global_moments']['score'])
        instruments={x['instrument']:x for x in result['instrument_diagnostics']}
        for name,expected_instrument in expected['by_instrument'].items():
            actual=instruments[name]
            self.assertEqual(actual['groups']['scope']['rate'],expected_instrument['q'])
            self.assert_pair(actual['outcome_lag_products'][1],expected_instrument['lag1'])
        self.assert_pair(result['cross_instrument_products'][0],expected['common_time_outcome_pairs'][0])
        states=Counter()
        for record in instruments.values():states.update(record['state_counts'])
        self.assertEqual(dict(states),expected['exact_state_counts'])
        self.assertEqual([r['scope_count'] for r in rows],[2,0,0,2,1,0])

    def test_missing_denominator_and_zero_event_rate_remain_distinct(self):
        fixture=self.fixture('no_true_condition');result=diagnose(fixture['report'],fixture['lags'])
        self.assertEqual(result['status'],'COMPUTED_DIAGNOSTICS')
        self.assertEqual(result['totals']['scope']['count'],7)
        self.assertEqual(result['totals']['scope']['rate'],rational(Fraction(3,7)))
        self.assertEqual(result['totals']['false']['count'],6)
        self.assertEqual(result['totals']['unknown']['count'],1)
        self.assertIsNone(result['totals']['true']['rate'])
        self.assertIsNone(result['grid_moments']['contrast_score'])
        self.assertIn('no_conditioned_cases',result['model_identification_gaps'])
        self.assertIsNotNone(result['instrument_diagnostics'][0]['outcome_lag_products'][1]['fixed_center_product'])
        fixture=self.fixture('all_zero_observed_binary');result=diagnose(fixture['report'],fixture['lags'])
        self.assertEqual(result['totals']['scope']['rate'],rational(0))
        self.assertIn('degenerate_scope_rate',result['model_identification_gaps'])
        self.assertEqual(result['grid_moments']['contrast_score']['mean'],rational(0))
        self.assertEqual([r['covariance'] for r in result['grid_moments']['contrast_score']['lags']],
                         [rational(0),rational(0),rational(0),None])
        self.assertFalse(result['scientific_readiness'])
        self.assertIsNone(result['n_min'])

    def test_mask_runs_do_not_merge_different_ineligible_causes(self):
        fixture=self.fixture();result=diagnose(fixture['report'],fixture['lags'])
        instruments={x['instrument']:x for x in result['instrument_diagnostics']}
        runs=instruments['B']['mask_runs']
        self.assertIn({'state':'OUTCOME_MISSING','length':1,'runs':1},runs)
        self.assertIn({'state':'PARTITION_BOUNDARY','length':1,'runs':1},runs)
        self.assertIn({'state':'DATA_GAP','length':1,'runs':1},runs)
        self.assertIn({'state':'ELIGIBLE_unknown','length':1,'runs':1},instruments['A']['mask_runs'])
        self.assertFalse(any(row['length']==2 and row['state'] in ('OUTCOME_MISSING','DATA_GAP') for row in runs))

    def test_no_scope_retains_the_grid_without_inventing_outcomes_or_scores(self):
        fixture=self.fixture('six_time_raw_coherent');request=deepcopy(fixture['report']['request'])
        request['scope_program']['expression']={'op':'literal','type':'boolean','unit':None,'value':False}
        report=materialize_reference(request,fixture['raw_catalog'],fixture['raw_rows'])
        rows=[];result=diagnose(report,[1,6],on_contribution=rows.append)
        self.assertEqual(result['status'],'COMPUTED_DIAGNOSTICS')
        self.assertEqual(result['totals']['scope']['count'],0)
        self.assertIsNone(result['totals']['scope']['rate'])
        self.assertIsNone(result['grid_moments']['scope_residual'])
        self.assertIsNone(result['grid_moments']['contrast_score'])
        self.assertEqual([r['scope_count'] for r in rows],[0]*6)
        for instrument in result['instrument_diagnostics']:
            self.assertTrue(all(r['eligible_pairs']==0 and r['fixed_center_product'] is None
                                for r in instrument['outcome_lag_products']))
        self.assertIn('no_scope_cases',result['model_identification_gaps'])
        self.assertIsNone(result['n_min'])

    def test_callback_mutation_and_absence_do_not_change_inputs_or_retained_bytes(self):
        fixture=self.fixture();report=fixture['report'];lags=fixture['lags']
        before=deepcopy([report,lags]);records=[]
        def sink(row):
            records.append(canonical(row)+'\n')
            row['scope_count']=999
        result=diagnose(report,lags,on_contribution=sink)
        self.assertEqual([report,lags],before)
        self.assertEqual(result,diagnose(report,lags))
        self.assertEqual(result['contributions_sha256'],hashlib.sha256(''.join(records).encode()).hexdigest())
        expected_cases=''.join(canonical(c)+'\n' for c in report['cases']).encode()
        self.assertEqual(result['case_stream_sha256'],hashlib.sha256(expected_cases).hexdigest())
        self.assertEqual(result['case_report_hash'],digest({k:v for k,v in report.items() if k!='cases'}))
        class SinkFailed(Exception):pass
        def broken(row):raise SinkFailed('intentional fixture error')
        with self.assertRaises(SinkFailed):diagnose(report,lags,on_contribution=broken)

    def test_source_hashes_distinguish_case_and_header_changes(self):
        fixture=self.fixture();base=diagnose(fixture['report'],fixture['lags'])
        changed=deepcopy(fixture['report']);changed['cases'][0]['reason']='different_retained_reason'
        case=diagnose(changed,fixture['lags'])
        self.assertNotEqual(case['case_stream_sha256'],base['case_stream_sha256'])
        self.assertEqual(case['case_report_hash'],base['case_report_hash'])
        self.assertEqual(case['grid_moments'],base['grid_moments'])
        changed=deepcopy(fixture['report']);changed['primitive_steps']+=1
        header=diagnose(changed,fixture['lags'])
        self.assertNotEqual(header['case_report_hash'],base['case_report_hash'])
        self.assertEqual(header['case_stream_sha256'],base['case_stream_sha256'])

    def test_explicit_lag_and_instrument_resource_envelopes_do_not_truncate(self):
        fixture=self.fixture('six_time_raw_coherent')
        for lags in ([],[True],[0],[-1],[100001],[1,1],[2,1],list(range(1,18)),(1,2)):
            with self.subTest(lags=lags),self.assertRaises(Invalid):validate_lags(lags)
        self.assertEqual(validate_lags(list(range(1,17))),list(range(1,17)))
        self.assertEqual(validate_lags([100000]),[100000])
        for width in (16,17):
            request=deepcopy(fixture['report']['request'])
            request['universe']['instruments']=[f'I{i:02}' for i in range(width)]
            request['universe']['end']='1970-01-01T00:30:00Z'
            request['as_of']=request['universe']['end']
            rows=[{'time':t,'instrument':instrument,'features':{
                'condition@1':{'value':True,'available_at':t},
                'event@1':{'value':True,'available_at':t}}}
                for t in (0,900) for instrument in request['universe']['instruments']]
            report=materialize_reference(request,fixture['raw_catalog'],rows);emitted=[]
            result=diagnose(report,list(range(1,17)),on_contribution=emitted.append)
            if width==16:
                self.assertEqual(result['status'],'COMPUTED_DIAGNOSTICS')
                self.assertEqual(len(result['instrument_diagnostics']),16)
                self.assertEqual(len(result['cross_instrument_products']),120)
                self.assertEqual(len(emitted),2)
            else:
                self.assertEqual(result['status'],'RESOURCE_GAP')
                self.assertEqual(emitted,[])
                self.assertEqual(result['contribution_count'],0)
            self.assertIsNone(result['n_min'])

    def test_nonbinary_pending_review_and_incomplete_reports_keep_typed_gaps(self):
        fixture=self.fixture('six_time_raw_coherent');request=deepcopy(fixture['report']['request'])
        request['outcome_scale']='quantity'
        request['outcome_program']['expression']={'op':'literal','type':'real','unit':'ratio','value':'0.5'}
        quantity=materialize_reference(request,fixture['raw_catalog'],fixture['raw_rows'])
        pending_request=deepcopy(fixture['report']['request']);pending_request['as_of']='1970-01-01T00:00:00Z'
        pending=materialize_reference(pending_request,fixture['raw_catalog'],fixture['raw_rows'])
        incomplete=deepcopy(fixture['report']);incomplete['cases']=incomplete['cases'][:-2]
        incomplete.update(processed_case_count=10,processing_complete=False,outcomes_complete=False,status='RESOURCE_STOP',resource_reason='fixture_stop')
        counts=Counter(c['status'] for c in incomplete['cases'])
        incomplete['state_counts']={s:counts[s] for s in sorted(STATES)}
        review=deepcopy(fixture['report']);review['cases'][0]['status']='REVIEW_REQUIRED'
        review['cases'][0]['reason']='outcome_dependency_membership_uncertified'
        counts=Counter(c['status'] for c in review['cases'])
        review['state_counts']={s:counts[s] for s in sorted(STATES)};review['review_required']=True
        for report,wanted in [(quantity,'EVALUATION_GAP'),(pending,'INPUT_GAP'),(incomplete,'INPUT_GAP'),(review,'INPUT_GAP')]:
            with self.subTest(wanted=wanted,reason=report.get('resource_reason')):
                emitted=[];result=diagnose(report,[1],on_contribution=emitted.append)
                self.assertEqual(result['status'],wanted)
                self.assertEqual(emitted,[])
                self.assertIsNone(result['n_min'])
                self.assertFalse(result['scientific_readiness'])


if __name__=='__main__':unittest.main()
