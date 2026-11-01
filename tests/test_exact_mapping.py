"""Scoped inactive mapping feasibility, preserving legacy sources and goldens."""
from copy import deepcopy
from fractions import Fraction
import random
import unittest

from exact_mapping_support import programs,supplied
from test_exact_compositions import FIXTURE,D,history,change,original_condition
from test_exact_runtime import history as timed_history
from trading_researcher.case_diagnostics import _guard
from trading_researcher.codec import canonical
from trading_researcher.exact_compositions import ExactCompositionEngine
from trading_researcher.exact_outcomes import materialize_exact,add_exact_diagnostics
from trading_researcher.exact_runtime import compile_payload


def evaluate(program,rows,when,cutoff=None,trace=None):
    engine=ExactCompositionEngine(FIXTURE['catalog'],rows,allow_log=program is not None and
        program['expression']['op']=='mul')
    remaining=[1000000]
    value=engine._calculate(engine._program_node(program),when,'BTCUSDT',when if cutoff is None else cutoff,remaining,trace)
    return value.public(),1000000-remaining[0]


class ExactMappingTests(unittest.TestCase):
    def test_strict_guard_all_nine_values_and_original_source_preservation(self):
        before=canonical(FIXTURE);alternative=programs()
        literal=lambda value:{'op':'literal','type':'boolean','unit':None,'value':value}
        for valid in (False,None,True):
            for predicate in (False,None,True):
                expression={'op':'eq','left':{'op':'or','left':literal(valid),'right':literal(None)},
                    'right':literal(predicate)}
                program={**FIXTURE['programs']['scope'],'expression':expression}
                actual,_=evaluate(program,history(),40*D)
                self.assertIs(actual['value'],predicate if valid is True else None)
        self.assertEqual(canonical(FIXTURE),before)
        self.assertEqual(alternative['scope'],FIXTURE['programs']['scope'])
        # Existing syntax-only diagnostic protocol is deliberately NOT bypassed.
        self.assertIsNone(_guard(alternative['condition']['expression']))
        self.assertIsNotNone(_guard(FIXTURE['programs']['condition']['expression']))

    def test_full_condition_matches_literal_original_with_missing_invalid_and_late(self):
        rng=random.Random(971102);alternative=programs()['condition']
        for case in range(160):
            rows=history()
            for index in range(7,40):
                lo=rng.randint(10,100);hi=lo+rng.randint(0,35)
                change(rows,index,'L',str(lo));change(rows,index,'H',str(hi))
            if case%2==0:
                change(rows,39,'H','100.1');change(rows,39,'L','100')
            defect=case%8
            if defect==1:change(rows,10,'H',None)
            elif defect==2:change(rows,10,'Q','-1')
            elif defect==3:change(rows,39,'B','300')
            elif defect==4:rows[10]['features']['L@1']['available_at']=40*D+1
            elif defect==5:rows.pop(7)
            elif defect==6:change(rows,39,'Q','100');change(rows,39,'B','50')
            elif defect==7:rows[39]['features'].pop('C@1')
            with self.subTest(case=case):
                actual,_=evaluate(alternative,rows,40*D)
                self.assertIs(actual['value'],original_condition(rows))
        rows=history();old_trace=[];new_trace=[]
        old,old_cost=evaluate(FIXTURE['programs']['condition'],rows,40*D,trace=lambda *x:old_trace.append(x))
        new,new_cost=evaluate(alternative,rows,40*D,trace=lambda *x:new_trace.append(x))
        self.assertEqual(old,new);self.assertEqual(set(old_trace),set(new_trace))
        self.assertEqual((old_cost,new_cost),(1454,844))
        self.assertLess(len(new_trace),len(old_trace))

    def test_endpoint_domain_guards_keep_exact_valid_outcomes_and_required_coordinates(self):
        alternative=programs()['outcome']
        for first,last in [('100','110'),('110','100'),('100','100'),('-100','-110'),
                           ('-100','110'),('100','-110'),('0','1'),('1','0'),(None,'1'),('1',None)]:
            rows=history();change(rows,40,'C',first);change(rows,44,'C',last)
            old,_=evaluate(FIXTURE['programs']['outcome'],rows,45*D)
            new,_=evaluate(alternative,rows,45*D)
            with self.subTest(first=first,last=last):
                self.assertEqual(old['value'],new['value'])
                self.assertEqual(old['type'],new['type']);self.assertEqual(old['unit'],new['unit'])
                self.assertEqual(old['value'] is None,first is None or last is None or Fraction(first)<=0 or Fraction(last)<=0)
        rows=history();trace=[]
        _,cost=evaluate(alternative,rows,45*D,trace=lambda *x:trace.append(x))
        self.assertEqual({event[0] for event in trace},{40*D,44*D})
        self.assertIsNone(evaluate(alternative,rows,45*D,cutoff=45*D-1)[0]['value'])
        self.assertLess(cost,evaluate(FIXTURE['programs']['outcome'],rows,45*D)[1])

    def test_small_complete_case_projection_preserves_values_but_exposes_guard_gap(self):
        request=compile_payload(supplied())['request'];rows=timed_history()
        from test_exact_runtime import payload
        old=materialize_exact(compile_payload(payload())['request'],FIXTURE['catalog'],rows)
        new=materialize_exact(request,FIXTURE['catalog'],rows)
        self.assertEqual(new['cases'],old['cases'])
        self.assertLess(new['primitive_steps'],old['primitive_steps'])
        diagnostic=add_exact_diagnostics(new,FIXTURE['catalog'],rows,request['max_steps']-new['primitive_steps'])
        self.assertTrue(diagnostic['diagnostics']['processing_complete'])
        self.assertEqual(diagnostic['diagnostics']['guard_counts']['unrecognized'],55)


if __name__=='__main__':unittest.main()
