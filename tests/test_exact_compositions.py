"""Full engineering shape versus literal original-meaning synthetic oracles."""
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path
import random
import unittest

from trading_researcher.exact_compositions import ExactCompositionEngine

FIXTURE=json.loads((Path(__file__).parent/'fixtures/exact_composition_shape_2026-11-01.json').read_text(encoding='utf-8'))
D=900

def history():
    data=[]
    for i in range(50):
        values={'H':'120','L':'80','C':str(100+Decimal(i)/10),'Q':'100','B':'50'}
        if i==39:values.update(H='100.5',L='100',C='100.25',Q='250',B='125')
        data.append({'time':i*D,'instrument':'BTCUSDT','features':{
            key+'@1':{'value':value,'available_at':(i+1)*D} for key,value in values.items()}})
    return data

def change(data,index,key,value):data[index]['features'][key+'@1']['value']=value

def original_condition(data,t=40*D):
    """Literal complete inputs/validity and original mean log ranges, not DSL."""
    lookup={row['time']:row['features'] for row in data if row['instrument']=='BTCUSDT'}
    def read(s,key):
        sample=lookup.get(s,{}).get(key+'@1')
        if sample is None or sample['value'] is None or sample['available_at']>t:raise ValueError
        return Fraction(sample['value'])
    b=t-D
    try:
        h,l,q,buy=(read(b,key) for key in ('H','L','Q','B'))
        past=[tuple(read(b-k*D,key) for key in ('H','L','Q')) for k in range(1,33)]
    except ValueError:return None
    if not (h>=l>0 and q>0 and 0<=buy<=q):return None
    if any(not (hi>=lo>0 and quote>=0) for hi,lo,quote in past):return None
    mean_q=sum(quote for _,_,quote in past)/32
    if mean_q<=0:return None
    with localcontext() as ctx:
        ctx.prec=120
        log=lambda ratio:(Decimal(ratio.numerator)/Decimal(ratio.denominator)).ln()
        mean_w=sum((log(hi/lo) for hi,lo,_ in past),Decimal(0))/32
        if mean_w<=0:return None
        return bool(q>=2*mean_q and Fraction(45,100)<=buy/q<=Fraction(55,100)
                    and log(h/l)<=mean_w/2)

def evaluate(data,kind,when,cutoff=None,trace=None):
    engine=ExactCompositionEngine(FIXTURE['catalog'],data,allow_log=kind=='outcome')
    node=engine._program_node(FIXTURE['programs'][kind])
    return engine._calculate(node,when,'BTCUSDT',when if cutoff is None else cutoff,[1000000],trace).public()

class ExactCompositionShapeTests(unittest.TestCase):
    def test_original_complete_condition_fixed_cases_and_unknown_dominance(self):
        scenarios=[]
        base=history();scenarios.append(('qualifying',base,True))
        data=history();change(data,39,'Q','100');change(data,39,'B','50');scenarios.append(('volumefalse',data,False))
        data=history();change(data,39,'B','40');scenarios.append(('sharefalse',data,False))
        data=history();change(data,39,'H','200');scenarios.append(('rangefalse',data,False))
        for name,index,key,value in [('badbaselineHL',10,'H','70'),('negativebaselineQ',10,'Q','-1'),
            ('negativesignalB',39,'B','-1'),('excesssignalB',39,'B','251'),('zerosignalQ',39,'Q','0'),
            ('missingbaseline',10,'H',None),('missingsignal',39,'B',None)]:
            data=history();change(data,index,key,value);scenarios.append((name,data,None))
        data=history();change(data,39,'Q','100');change(data,39,'B','50');change(data,10,'H',None)
        scenarios.append(('knownfalseplusmissing',data,None))
        data=history();data[10]['features']['L@1']['available_at']=40*D+1;scenarios.append(('latebaseline',data,None))
        data=history();data.pop(7);scenarios.append(('missingearliestslot',data,None))
        data=history();data[39]['features'].pop('C@1');scenarios.append(('signalcloseunused',data,True))
        data=history()
        for i in range(7,39):change(data,i,'Q','0')
        scenarios.append(('zerobaselineQ',data,None))
        data=history()
        for i in range(7,39):change(data,i,'H','80')
        scenarios.append(('zerobaselinerange',data,None))
        for name,data,expected in scenarios:
            with self.subTest(name=name):
                self.assertEqual(original_condition(data),expected)
                self.assertEqual(evaluate(data,'condition',40*D)['value'],expected)

    def test_complete_condition_random_histories_against_original_logs(self):
        rng=random.Random(97001)
        for case in range(120):
            data=history()
            for i in range(7,40):
                lo=rng.randint(70,100);hi=lo+rng.randint(0,30);q=rng.randint(50,300)
                change(data,i,'H',str(hi));change(data,i,'L',str(lo));change(data,i,'Q',str(q))
                change(data,i,'B',str(Decimal(q)*rng.randint(35,65)/100))
            with self.subTest(case=case):
                self.assertEqual(evaluate(data,'condition',40*D)['value'],original_condition(data))

    def test_exact_log_range_equality_and_guard_trace(self):
        data=history()
        for i in range(7,39):change(data,i,'H','4');change(data,i,'L','1')
        change(data,39,'H','2');change(data,39,'L','1')
        # ln(2) == one half ln(4), exactly; no Decimal rounding oracle here.
        self.assertIs(evaluate(data,'condition',40*D)['value'],True)
        trace=[];evaluate(data,'condition',40*D,trace=lambda *event:trace.append(event))
        self.assertEqual({time for time,_,_ in trace},set(range(7*D,40*D,D)))
        self.assertFalse(any(time>=40*D for time,_,_ in trace))
        data[39]['features']['H@1']['available_at']=40*D+1
        self.assertIsNone(evaluate(data,'condition',40*D)['value'])

    def test_original_absolute_outcome_and_each_endpoint_domain(self):
        for first,last in [('100','110'),('110','100'),('100','100'),('-100','-110'),
            ('-100','110'),('100','-110'),('0','1'),('1','0'),(None,'1'),('1',None)]:
            with self.subTest(first=first,last=last):
                data=history();change(data,40,'C',first);change(data,44,'C',last)
                result=evaluate(data,'outcome',45*D)
                if first is None or last is None or Fraction(first)<=0 or Fraction(last)<=0:
                    self.assertIsNone(result['value']);continue
                bound=result['value'];read=lambda x:Fraction(int(x['numerator']),int(x['denominator']))
                with localcontext() as ctx:
                    ctx.prec=120;oracle=Fraction(abs((Decimal(last)/Decimal(first)).ln())*10000)
                self.assertLessEqual(read(bound['lower']),oracle)
                self.assertGreaterEqual(read(bound['upper']),oracle)
                self.assertLessEqual(read(bound['upper'])-read(bound['lower']),Fraction(1,10**12))
        data=history();trace=[]
        evaluate(data,'outcome',45*D,trace=lambda *event:trace.append(event))
        self.assertEqual({event[0] for event in trace},{40*D,44*D})
        self.assertIsNone(evaluate(data,'outcome',45*D,cutoff=45*D-1)['value'])

if __name__=='__main__':unittest.main()
