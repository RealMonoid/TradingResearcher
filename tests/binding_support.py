"""Owned-registry fixture setup; fixed expectations live in the independent JSON bundle."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

import test_binance_normalize as normalization_tests


FIXTURE_PATH = Path(__file__).parent/'fixtures/reference_binding_cases.json'
FIXTURE_HASH = '484bf3f73850760502e41d1cdf070c4cd666dc2c384805cfed99cfc3598859f6'


def fixture():
    raw = FIXTURE_PATH.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == FIXTURE_HASH
    return json.loads(raw)


def resolve(value, aliases):
    if isinstance(value,dict):return {key:resolve(item,aliases) for key,item in value.items()}
    if isinstance(value,list):return [resolve(item,aliases) for item in value]
    return aliases.get(value,value) if isinstance(value,str) else value


class BindingFixture:
    def __init__(self, case=None):
        self.fixed = fixture()
        self.base = self.fixed['baseline']
        self.normalizer = normalization_tests.NormalizeTests()
        self.normalizer.setUp()
        self.root = self.normalizer.root
        change = (case or {}).get('change',{})
        source = self.normalizer.source(change.get('source_raw_csv',self.base['source']['raw_csv']).encode())
        result = self.normalizer.run_normalize([source],end='2020-01-01T01:00:00Z',
            delay=change.get('delay_seconds',self.base['delay_seconds']))
        self.broker,self.token = self.normalizer.broker,self.normalizer.broker.admin_token
        self.snapshot = result['snapshot']
        self.normalization = result['normalization']
        self.feature = self.broker.call(self.token,'certify_features',data_snapshot_id=self.snapshot['id'])
        assert self.feature['body']['status'] == 'CERTIFIED',self.feature['body']
        self.reference = self.broker.call(self.token,'certify_reference')
        assert self.reference['body']['status'] == 'CERTIFIED',self.reference['body']
        self.worker = self.broker.call(self.token,'register_worker',name='binding-formalizer',role='formalizer',
            capabilities=['formalization/v1'])['token']
        self.counter = 0

    def close(self):
        self.normalizer.tearDown()

    def create_formalization(self, case=None, submit=True, candidate_transform=None):
        self.counter += 1
        change = (case or {}).get('change',{})
        idea_text = change.get('original_idea_text',self.base['original_idea_text'])
        idea = self.broker.call(self.token,'add_research',kind='idea',content={'text':idea_text},scope={},source_refs=[])
        aliases = {'fixture:idea':idea['id'],'fixture:data_snapshot':self.snapshot['id']}
        candidate = resolve(deepcopy(change.get('candidate',self.base['candidate'])),aliases)
        if candidate_transform:candidate_transform(candidate)
        report = deepcopy(self.base['semantic_report'])
        report['segments'][0]['text'] = idea_text
        context = self.broker.call(self.token,'create_context',role='formalizer',epoch=self.counter,
            artifact_ids=[idea['id'],self.snapshot['body']['catalog_id'],self.snapshot['id']])
        self.broker.call(self.token,'enqueue',key='binding-'+str(self.counter),spec={
            'kind':'formalization/v1','context_id':context['id'],'purpose':'Independent synthetic binding fixture',
            'allowed_workers':['binding-formalizer'],'max_attempts':1,'lease_seconds':300,
            'deadline':int(time.time())+1800,'dependencies':[]})
        lease = self.broker.call(self.worker,'claim')['lease']
        saved = self.broker.call(self.worker,'record_formalization',lease=lease,idea_id=idea['id'],
            catalog_id=self.snapshot['body']['catalog_id'],candidate=candidate,semantic_report=report)
        if submit:
            outcome = self.broker.call(self.worker,'submit',lease=lease,artifact_id=saved['id'])
            assert outcome['accepted'],outcome
        return self.broker.call(self.token,'get_artifact',artifact_id=saved['id'])

    def compile(self, formalization=None, case=None, **overrides):
        formalization = formalization or self.create_formalization(case)
        options = {**self.base['compile_options'],**(case or {}).get('change',{}).get('compile_options',{})}
        arguments = {'formalization_id':formalization['id'],'feature_certificate_id':self.feature['id'],
            'reference_certificate_id':self.reference['id'],**options,**overrides}
        return self.broker.call(self.token,'compile_hypothesis',**arguments)
