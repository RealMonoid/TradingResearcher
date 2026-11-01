"""Structural transport checks; these synthetic mappings do not prove meaning."""
from copy import deepcopy
import unittest

from trading_researcher.paired_formalization import assess_candidate
from trading_researcher.formalization import assess_candidate as legacy_assess
from trading_researcher.paired_development import PairedReferenceEngine
from test_paired_runtime import payload


def draft():
    inputs,rows=payload()
    candidate=inputs['candidate']
    candidate.update(idea_ref='synthetic-idea',claim_kind='difference',comparator={'kind':'whole_scope'},
        estimand={'kind':'conditional-minus-scope-mean/1','unit':'basis_points','weighting':'equal_rows',
            'missingness':'scope-true-outcome-observed/1','condition_unknown':'exclude-from-condition-retain-in-scope',
            'nuisance_fit':'none','direction':'positive'},parameter_origins=[])
    engine=PairedReferenceEngine(inputs['catalog'],[],inputs['feature_definitions'],pair=['BTCUSDT','ETHUSDT'],allow_log=True)
    paths=['/horizons/outcome_bars']
    for path,program in (('/scope_ast',candidate['scope_ast']),('/condition_ast',candidate['condition_ast']),
                         ('/outcome/program',candidate['outcome']['program'])):
        paths.extend(path+suffix for suffix in engine.describe(program)['parameter_paths'])
    candidate['parameter_origins']=[{'path':path,'basis':'preexisting_specification','source_refs':[],
                                    'rationale':'Synthetic acceptance fixture only.'} for path in paths]
    mapping={'status':'equivalent','segments':[{'text':'Synthetic paired idea.','path':'/condition_ast',
        'interpretation':'Fixture mapping only, not an actual scientific judgment.'}],'differences':[]}
    return inputs,candidate,mapping


class PairedFormalizationTests(unittest.TestCase):
    def test_explicit_new_schema_is_checked_without_changing_old_acceptance(self):
        inputs,candidate,mapping=draft()
        args=('synthetic-idea','Synthetic paired idea.',candidate,mapping,inputs['catalog'],
              {candidate['test_universe']['data_snapshot_ref']})
        self.assertEqual(assess_candidate(*args,inputs['feature_definitions'])['status'],'STRUCTURE_CHECKED')
        self.assertEqual(legacy_assess(*args)['status'],'RETAINED_GAP')

    def test_pair_mapping_closure_and_units_are_retained_gaps(self):
        inputs,candidate,mapping=draft()
        mutators=[lambda c:c.update(schema='hypothesis-exec/1'),
            lambda c:c['test_universe'].update(pair=['ETHUSDT','BTCUSDT']),
            lambda c:c['estimand'].update(unit='ratio'),
            lambda c:c.update(parameter_origins=[]),
            lambda c:c['feature_refs'].pop(),
            lambda c:c['scope_ast'].update(schema='research-ast/2')]
        for mutate in mutators:
            changed=deepcopy(candidate)
            mutate(changed)
            result=assess_candidate('synthetic-idea','Synthetic paired idea.',changed,mapping,inputs['catalog'],
                {candidate['test_universe']['data_snapshot_ref']},inputs['feature_definitions'])
            self.assertEqual(result['status'],'RETAINED_GAP')
        result=assess_candidate('synthetic-idea','Changed original.',candidate,mapping,inputs['catalog'],
            {candidate['test_universe']['data_snapshot_ref']},inputs['feature_definitions'])
        self.assertEqual(result['status'],'RETAINED_GAP')


if __name__=='__main__':
    unittest.main()
