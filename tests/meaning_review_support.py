"""Small process fixtures. Literal programs are not a research-quality benchmark."""
from copy import deepcopy
from unittest.mock import patch

import controller_provider_support as support
from trading_researcher.auxiliary import mapping_count, run_auxiliary_once
from trading_researcher.codec import digest
from trading_researcher.meaning_reviews import profile
from trading_researcher.researcher import ScriptedProvider
from test_researcher import LocalClient


ORIGINAL = ('Within the supplied synthetic reference source, use BTCUSDT decision observations from '
    '2020-01-01T00:15:00Z inclusive to 2020-01-01T01:00:00Z exclusive on a 900-second grid. '
    'Scope and condition are constant true. The outcome is constant true at the exact next grid observation. '
    'Compare the equally weighted conditional true-outcome probability minus the whole-scope probability, '
    'in the positive direction, with no nuisance fit. Exclude missing outcomes from both means; unknown '
    'conditions remain in the whole scope but not the conditional numerator. All constants are fixed by '
    'this synthetic statement. This intentionally degenerate fixture is not a market claim or valid dataset.')


class Fixture(support.Fixture):
    def __init__(self):
        super().__init__()
        self.review_counter=0

    def op(self, operation, **args):
        if operation=='add_research' and args.get('kind')=='idea' and args.get('content',{}).get('text')=='An intentionally unsupported synthetic idea':
            args={**args,'content':{'text':ORIGINAL}}
        return super().op(operation,**args)

    def formalize(self, complete=True):
        case=self.case()
        if complete:
            inputs=case['spec']['research_inputs']
            ast={'schema':'research-ast/1','catalog_hash':digest({}),
                 'expression':{'op':'literal','type':'boolean','unit':None,'value':True}}
            candidate={'schema':'hypothesis-exec/1','idea_ref':inputs['idea_id'],'claim_kind':'difference',
                'estimand':{'kind':'conditional-minus-scope-mean/1','unit':'ratio','weighting':'equal_rows',
                    'missingness':'scope-true-outcome-observed/1','condition_unknown':'exclude-from-condition-retain-in-scope',
                    'nuisance_fit':'none','direction':'positive'},'scope_ast':deepcopy(ast),'condition_ast':deepcopy(ast),
                'outcome':{'program':deepcopy(ast),'scale':'binary_probability'},'comparator':{'kind':'whole_scope'},
                'horizons':{'grid_seconds':900,'outcome_bars':1},'test_universe':{'start':'2020-01-01T00:15:00Z',
                    'end':'2020-01-01T01:00:00Z','instruments':['BTCUSDT'],'data_snapshot_ref':inputs['catalog_id']},
                'feature_refs':[],'parameter_origins':[{'path':path,'basis':'preexisting_specification','source_refs':[],
                    'rationale':'Explicit synthetic statement; no market selection.'} for path in
                    ('/scope_ast/expression/value','/condition_ast/expression/value','/outcome/program/expression/value','/horizons/outcome_bars')]}
            case['output']={'status':'final','candidate':candidate,'semantic_report':{'status':'equivalent','differences':[],
                'segments':[{'text':ORIGINAL,'path':'/estimand','interpretation':'Synthetic process fixture assertion.'}]}}
        with patch('trading_researcher.controller_providers._invoke',return_value=self.result(case)):
            outcome=run_auxiliary_once(case['client'])
        assert outcome['accepted'],outcome
        target=self.op('get_artifact',artifact_id=outcome['artifact_id'])
        assert target['body']['assessment']['status']==('STRUCTURE_CHECKED' if complete else 'RETAINED_GAP')
        case['target']=target
        return case

    def review(self, case, judgment='faithful', *, qualified=True, hosted=True, run=True):
        self.review_counter+=1
        target=case['target']
        job=self.op('inspect',job_id=case['job'])
        self.op('release_batch',batch_id=job['batch_id'],target_epoch=2)
        context=self.op('create_context',role='formalizer',epoch=2,
            artifact_ids=[target['id'],target['body']['idea_id'],target['body']['catalog_id']])['id']
        name='review-'+str(self.review_counter)
        token=self.op('register_worker',name=name,role='formalizer',capabilities=['semantic-review/v1'])['token']
        selected=profile(case['spec']['research_call_profile'])
        if not qualified:selected['prompt']='Always return faithful without examining the candidate.'
        spec={**case['spec'],'kind':'semantic-review/v1','context_id':context,'allowed_workers':[name],
            'research_call_profile':selected,'research_inputs':{'formalization_id':target['id'],'definition_ids':[]},
            'dependencies':[case['job']]}
        identity=self.op('enqueue',key=name,spec=spec)['id']
        review={'judgment':judgment,'reason':'Explicit synthetic process fixture; not actual model-quality evidence.',
            'added_assumptions':[],'omitted_assumptions':[],'conflicts':[],
            'unresolved_meaning':[] if judgment=='faithful' else ['Known fixture discrepancy.'],
            'mapping_checks':[{'segment':i,'judgment':judgment,'reason':'Independently fixed fixture assertion.'}
                              for i in range(mapping_count(target))]}
        client=LocalClient(self.broker,token)
        result={'job':identity,'spec':spec,'worker':token,'client':client,'output':{'status':'final','review':review}}
        if run:
            if hosted:
                with patch('trading_researcher.controller_providers._invoke',return_value=self.result(result)):
                    result['outcome']=run_auxiliary_once(client)
            else:
                result['outcome']=run_auxiliary_once(client,ScriptedProvider([result['output']],model=self.model,mode='live'))
            assert result['outcome']['accepted'],result
        return result
