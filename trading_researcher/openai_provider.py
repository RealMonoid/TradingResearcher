"""Bounded API-key Responses transport; no scientific authority or invoice claim.

Prices are a dated standard-tier bound for the first explicitly authorized tests.
Input is conservatively charged at the default30m cache-write rate, not discounted.
The operator must reuse one spend ledger across all epochs in the approved scope.
"""
from copy import deepcopy
from contextlib import contextmanager
from dataclasses import dataclass,field
import hashlib
import http.client
import json
from pathlib import Path
import re
import sqlite3
import time
import uuid

from .codec import MAX_BYTES,Invalid,canonical,decode,digest,integer
from .errors import Conflict,Denied
from .provider_usage import report_connection,validate_receipt,validate_identity

MODEL='gpt-6.1-sol'
PRICING={'version':'openai-gpt-6.1-sol-standard-2026-10-25/1','currency':'USD','units_per_usd':1000000000,
    'input_upper_nano_per_token':2500,'output_nano_per_token':10000,'cache_lifetime':'30m',
    'qualification':'Conservative published-rate usage bound, including worst30m cache writes; not an invoice.',
    'sources':['https://developers.openai.com/api/docs/models/gpt-6.1-sol',
               'https://developers.openai.com/api/docs/guides/prompt-caching']}

def require(condition,message):
    if not condition:raise Invalid(message)


def provider_identity(reported_model=None):
    return {'requested_model':MODEL,'reported_model':reported_model,'catalog_name':'GPT-6.1 Sol',
        'catalog_version':'6.1','catalog_source':'https://developers.openai.com/api/docs/models/gpt-6.1-sol',
        'immutable_snapshot_id':None,'immutable_snapshot_status':'UNKNOWN'}

def configuration(input_token_limit=20000,output_token_limit=4096,now=None):
    result={'schema':'openai-responses-configuration/1','model':MODEL,'input_token_limit':input_token_limit,
        'output_token_limit':output_token_limit,'reasoning_effort':'low','pricing':deepcopy(PRICING),
        'expires_at':int(time.time() if now is None else now)+86400,'test_budget_nano':5000000000}
    _config(result);return result

def _config(config):
    require(type(config) is dict and set(config)=={'schema','model','input_token_limit','output_token_limit',
        'reasoning_effort','pricing','expires_at','test_budget_nano'},'Exact frozen API configuration required')
    require(config['schema']=='openai-responses-configuration/1' and config['model']==MODEL
        and config['reasoning_effort'] in ('low','medium','high','xhigh','max')
        and config['pricing']==PRICING,'Unsupported API model, reasoning or tariff')
    integer(config['expires_at'],'tariff expiry',1);integer(config['test_budget_nano'],'total test cap',1)
    require(config['test_budget_nano']<=5000000000,'Initial integration tests exceed the user-approved USD5 total')
    integer(config['input_token_limit'],'input token limit',1);integer(config['output_token_limit'],'output token limit',1)
    require(config['input_token_limit']+config['output_token_limit']<=80000,'Call exceeds the adopted total-token ceiling')
    canonical(config)

def cost_bound(input_tokens,output_tokens):
    integer(input_tokens,'input tokens');integer(output_tokens,'output tokens')
    return input_tokens*2500+output_tokens*10000

def _items(raw_items):
    require(type(raw_items) is list,'Expected provider output items')
    kept=[]
    for item in raw_items:
        require(type(item) is dict,'Invalid provider item')
        kind=item.get('type')
        if kind=='reasoning':
            names=('id','type','summary','encrypted_content','status')
            # Only documented public summaries and opaque continuation are retained.
        elif kind=='function_call':names=('id','type','call_id','name','arguments','status')
        elif kind=='message':names=('id','type','role','content','status','phase')
        else:raise Invalid('Unsupported hosted/provider output item')
        value={name:item[name] for name in names if name in item}
        if kind=='reasoning' and 'summary' in value:
            require(type(value['summary']) is list,'Invalid public reasoning summary')
            value['summary']=[_text_part(part,summary=True) for part in value['summary']]
        elif kind=='message':
            require(type(value.get('content')) is list,'Invalid native message content')
            value['content']=[_text_part(part) for part in value['content']]
        canonical(value);kept.append(value)
    return kept

def _text_part(part,summary=False):
    require(type(part) is dict,'Invalid native text part')
    kind=part.get('type')
    if summary:
        require(kind=='summary_text' and type(part.get('text')) is str,'Invalid public summary text')
        return {'type':kind,'text':part['text']}
    if kind=='refusal':
        require(type(part.get('refusal')) is str,'Invalid refusal')
        return {'type':kind,'refusal':part['refusal']}
    require(kind=='output_text' and type(part.get('text')) is str,'Invalid output text')
    require(part.get('annotations',[])==[],'Unsupported provider annotations')
    return {'type':kind,'text':part['text'],'annotations':[]}

def wire_request(request,config):
    _config(config)
    require(type(request) is dict and set(request)=={'model','prompt_version','messages','tools','generation_parameters'},
        'Exact normalized research request required')
    require(request['model']==config['model'] and request['generation_parameters']=={'openai_responses':config},
        'API request differs from its frozen configuration')
    require(type(request['tools']) is list and type(request['messages']) is list,'Explicit tools and messages required')
    tools=[];names=set()
    for tool in request['tools']:
        require(type(tool) is dict and set(tool)=={'name','description','parameters'}
            and type(tool['name']) is str and tool['name'] not in names,'Invalid or repeated tool definition')
        names.add(tool['name']);tools.append({'type':'function',**deepcopy(tool),'strict':False})
    history=[];pending={};seen=set()
    for message in request['messages']:
        require(type(message) is dict and set(message)=={'role','content'} and type(message['content']) is str,
            'Normalized public messages required')
        role=message['role']
        if role in ('system','user'):
            require(not pending,'Tool output is missing before another user message')
            history.append(deepcopy(message))
        elif role=='assistant':
            require(not pending,'Prior tool results are missing')
            response=decode(message['content'])
            if response.get('status') in ('failed','timeout','cancelled','input_limit'):
                history.append({'role':'assistant','content':canonical({'status':response['status']})});continue
            require(response.get('provider_id')=='openai.responses/1','Cannot replay another provider as OpenAI')
            items=_items(response.get('provider_items'))
            for item in items:
                if item['type']=='function_call':
                    identity=item.get('call_id');name=item.get('name')
                    require(type(identity) is str and identity and identity not in seen and name in names,
                        'Unknown, duplicate or unpermitted provider call')
                    arguments=decode(item.get('arguments'))
                    require(type(arguments) is dict,'Tool arguments must be an object')
                    pending[identity]={'id':identity,'name':name,'arguments':arguments};seen.add(identity)
            history.extend(items)
        elif role=='tool':
            body=decode(message['content']);tool=body.get('tool_request',{});identity=tool.get('id')
            require(body.get('schema')=='provider-tool-result/1' and identity in pending
                and tool==pending[identity],'Unmatched or duplicated tool output')
            history.append({'type':'function_call_output','call_id':identity,'output':canonical(body['result'])})
            del pending[identity]
        else:raise Invalid('Unsupported request role')
    require(not pending,'Every native tool call needs exactly one result')
    result={'model':config['model'],'input':history,'tools':tools,'store':False,'stream':False,
        'service_tier':'default','max_output_tokens':config['output_token_limit'],
        'reasoning':{'effort':config['reasoning_effort']},'include':['reasoning.encrypted_content'],
        'parallel_tool_calls':False,'text':{'format':{'type':'json_object'}},
        'prompt_cache_options':{'ttl':'30m'}}
    canonical(result);return result

def parse_response(raw,request_id,config):
    _config(config);require(type(raw) is dict,'Expected provider response object')
    metadata_valid=all(type(value) is str for value in (raw.get('id'),raw.get('model'),raw.get('status')))
    public={'provider_id':'openai.responses/1','provider_request_id':raw.get('id') if type(raw.get('id')) is str else None,
        'transport_request_id':request_id if type(request_id) is str else None,
        'resolved_model':raw.get('model') if type(raw.get('model')) is str else None,
        'status':raw.get('status') if type(raw.get('status')) is str else 'invalid_output',
        'output':None,'provider_items':[],'pricing':deepcopy(PRICING)}
    public['model_identity']=provider_identity(public['resolved_model'])
    usage=None
    try:
        measured=raw['usage'];a=integer(measured['input_tokens'],'reported input');b=integer(measured['output_tokens'],'reported output')
        require(raw.get('model')==config['model'] and raw.get('service_tier')=='default','Unverified served model/tier tariff')
        usage={'input_tokens':a,'output_tokens':b,'cost_units':cost_bound(a,b)}
    except (Invalid,KeyError,TypeError):pass
    details={'cached_input_tokens':None,'reasoning_output_tokens':None}
    if usage is not None:
        for name,group,field_name,parent in (
            ('cached_input_tokens','input_tokens_details','cached_tokens','input_tokens'),
            ('reasoning_output_tokens','output_tokens_details','reasoning_tokens','output_tokens')):
            candidate=measured.get(group,{})
            value=candidate.get(field_name) if type(candidate) is dict else None
            if type(value) is int and 0<=value<=usage[parent]:details[name]=value
    public['token_usage_details']=details
    identity_valid=raw.get('model')==config['model'] and raw.get('service_tier')=='default'
    bounds_exceeded=usage is not None and (usage['input_tokens']>config['input_token_limit']
        or usage['output_tokens']>config['output_token_limit'])
    if not metadata_valid or not identity_valid or usage is None or bounds_exceeded:
        public['status']='bounds_exceeded' if bounds_exceeded else 'unverified_response'
        result={'response':public,'usage':usage};canonical(result);return result
    try:
        items=_items(raw.get('output'));public['provider_items']=items
        calls=[];text_parts=[];ids=set();refused=False
        for item in items:
            if item['type']=='function_call':
                identity=item.get('call_id');name=item.get('name');arguments=decode(item.get('arguments'))
                require(type(identity) is str and identity and identity not in ids
                    and type(name) is str and type(arguments) is dict,'Malformed provider tool call')
                ids.add(identity);calls.append({'id':identity,'name':name,'arguments':arguments})
            elif item['type']=='message':
                require(item.get('role')=='assistant' and type(item.get('content')) is list,'Invalid provider message')
                for part in item['content']:
                    if part.get('type')=='refusal':refused=True
                    elif part.get('type')=='output_text':
                        require(type(part.get('text')) is str,'Invalid provider output text');text_parts.append(part['text'])
                    else:raise Invalid('Unsupported message content')
        if public['status']=='completed':
            if refused:public['status']='refused'
            elif calls:
                require(len(calls)<=16,'Too many provider tools');public['output']={'status':'tools','calls':calls}
            else:
                output=decode(''.join(text_parts));require(type(output) is dict,'Expected public JSON output')
                public['output']=output
    except (Invalid,KeyError,TypeError,AttributeError):public['status']='invalid_output';public['output']=None
    result={'response':public,'usage':usage};canonical(result);return result

class SpendLedger:
    """One persistent operator-selected cap shared by every initial test epoch."""
    def __init__(self,path,cap_nano):
        integer(cap_nano,'spend cap',1);self.path=Path(path);self.cap=cap_nano
        require(not self.path.is_symlink(),'Spend ledger cannot be a symlink')
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE IF NOT EXISTS budget(singleton INTEGER PRIMARY KEY CHECK(singleton=1),cap INTEGER NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS dispatches(id TEXT PRIMARY KEY,request_hash TEXT NOT NULL,reserved INTEGER NOT NULL,charged INTEGER,state TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS token_metadata(id TEXT PRIMARY KEY,created_at INTEGER NOT NULL,body TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS usage_receipts(id TEXT PRIMARY KEY,body TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS dispatch_settlements(id TEXT PRIMARY KEY,recorded_at INTEGER NOT NULL)')
            row=db.execute('SELECT cap FROM budget WHERE singleton=1').fetchone()
            if row is None:db.execute('INSERT INTO budget VALUES(1,?)',(cap_nano,))
            elif row[0]!=cap_nano:raise Conflict('Existing aggregate authorization cannot be reset or resized')

    @contextmanager
    def _connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        try:
            with db:yield db
        finally:db.close()

    def snapshot(self):
        with self._connect() as db:
            rows=db.execute('SELECT reserved,charged,state FROM dispatches').fetchall()
        charged=sum(reserved if amount is None else amount for reserved,amount,_ in rows)
        return {'cap_nano':self.cap,'charged_nano':charged,'available_nano':max(0,self.cap-charged),
            'pending':sum(state=='pending' for _,_,state in rows),'uncertain':sum(state=='uncertain' for _,_,state in rows),
            'halted':any(state in ('uncertain','overrun','blocked') for _,_,state in rows),'dispatches':len(rows),
            'qualification':'Conservative nanoUSD reservations/charges, not a provider invoice.'}

    def report(self):
        with self._connect() as db:
            db.execute('BEGIN')
            return report_connection(db)

    def reserve(self,request_hash,amount,*,key=None,metadata=None):
        integer(amount,'reservation',1);require(type(request_hash) is str and request_hash,'Request hash required')
        metadata={} if metadata is None else metadata
        require(type(metadata) is dict and not set(metadata)-{'run_id','epoch_id','worker','ordinal',
            'model','prompt_version','counted_input_tokens','model_identity','provider','budget_scope_ref'},'Unexpected accounting metadata')
        if 'provider' in metadata:
            require(metadata['provider'] in ('openai','anthropic'),'Unsupported accounting provider')
        if 'budget_scope_ref' in metadata:
            require(type(metadata['budget_scope_ref']) is str and 0<len(metadata['budget_scope_ref'])<=8192,
                'Explicit budget scope reference required')
        if 'model_identity' in metadata:
            validate_identity(metadata['model_identity'])
            require(metadata['model_identity']['requested_model']==metadata.get('model')
                and metadata['model_identity']['reported_model'] is None,'Admission cannot claim a served model')
        for name in ('run_id','epoch_id','worker','model','prompt_version'):
            require(metadata.get(name) is None or type(metadata[name]) is str,'Invalid accounting identity')
        for name in ('ordinal','counted_input_tokens'):
            if name in metadata:integer(metadata[name],name)
        metadata_text=canonical(metadata)
        key=uuid.uuid4().hex if key is None else key
        require(type(key) is str and 0<len(key)<=256,'Bounded dispatch identity required')
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if db.execute('SELECT 1 FROM dispatches WHERE id=?',(key,)).fetchone():raise Conflict('Dispatch identity already used')
            rows=db.execute('SELECT reserved,charged,state FROM dispatches').fetchall()
            if any(state!='settled' for _,_,state in rows):raise Conflict('Prior uncertain or unfinished dispatch prevents inference')
            if sum(reserved if charged is None else charged for reserved,charged,_ in rows)+amount>self.cap:
                raise Denied('Aggregate integration-test currency limit reached')
            db.execute('INSERT INTO dispatches VALUES(?,?,?,NULL,?)',(key,request_hash,amount,'pending'))
            db.execute('INSERT INTO token_metadata VALUES(?,?,?)',(key,int(time.time()),metadata_text))
        return key

    def settle(self,identity,charge,*,halt=False,receipt=None):
        if charge is not None:integer(charge,'charged currency')
        validate_receipt(receipt,charge)
        receipt_text=None if receipt is None else canonical(receipt)
        with self._connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT reserved,charged,state FROM dispatches WHERE id=?',(identity,)).fetchone()
            if row is None:raise Denied('Unknown currency reservation')
            if row[2]!='pending':
                prior=db.execute('SELECT body FROM usage_receipts WHERE id=?',(identity,)).fetchone()
                if row[1]==charge and (None if prior is None else prior[0])==receipt_text:return
                raise Conflict('A settled or unknown charge cannot be rewritten')
            state='uncertain' if charge is None else ('overrun' if charge>row[0] else ('blocked' if halt else 'settled'))
            db.execute('UPDATE dispatches SET charged=?,state=? WHERE id=?',(charge,state,identity))
            db.execute('INSERT INTO dispatch_settlements VALUES(?,?)',(identity,int(time.time())))
            if receipt_text is not None:db.execute('INSERT INTO usage_receipts VALUES(?,?)',(identity,receipt_text))

class WireFailure(Exception):
    def __init__(self,kind,status=None,request_id=None):
        super().__init__(kind);self.kind=kind;self.status=status;self.request_id=request_id

def _remaining(deadline):
    value=deadline-time.monotonic()
    if value<=0:raise WireFailure('deadline')
    return value

def _post(endpoint,payload,key,deadline):
    require(endpoint in ('/v1/responses/input_tokens','/v1/responses'),'Unsupported API endpoint')
    body=canonical(payload).encode();connection=http.client.HTTPSConnection('api.openai.com',443,timeout=_remaining(deadline))
    try:
        connection.request('POST',endpoint,body=body,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
        if connection.sock:connection.sock.settimeout(_remaining(deadline))
        response=connection.getresponse();identity=response.getheader('x-request-id')
        identity=identity if type(identity) is str and re.fullmatch(r'req_[A-Za-z0-9_-]{1,128}',identity) else None
        if not 200<=response.status<300:raise WireFailure('http_error',response.status,identity)
        blocks=[];size=0
        while True:
            remaining=_remaining(deadline)
            if connection.sock:connection.sock.settimeout(remaining)
            block=response.read1(min(65536,MAX_BYTES+1-size))
            if not block:break
            blocks.append(block);size+=len(block)
            if size>MAX_BYTES:raise WireFailure('response_size',request_id=identity)
        _remaining(deadline)
        def unique(pairs):
            result={}
            for name,value in pairs:
                if name in result:raise WireFailure('duplicate_json_key',request_id=identity)
                result[name]=value
            return result
        raw=json.loads(b''.join(blocks),object_pairs_hook=unique)
        require(type(raw) is dict,'Expected API object');return raw,identity
    except WireFailure:raise
    except Exception as exc:raise WireFailure(type(exc).__name__) from None
    finally:connection.close()

def _key(path):
    path=Path(path);require(not path.is_symlink() and path.stat().st_size<=65536,'Invalid credential destination')
    matches=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        found=re.fullmatch(r'OPENAI_API_KEY=(sk-[A-Za-z0-9_-]+)[ \t]*',line)
        if found:matches.append(found.group(1))
    require(len(matches)==1,'Exactly one configured API key required');return matches[0]

@dataclass
class OpenAIResponsesProvider:
    key_file: object=field(repr=False)
    budget_file: object
    config: dict
    run_id: str=field(default_factory=lambda:uuid.uuid4().hex)
    epoch_id: str|None=None
    worker: str|None=None
    model: str=field(default=MODEL,init=False)
    mode: str=field(default='live',init=False)

    def __post_init__(self):
        _config(self.config);self.config=deepcopy(self.config)

    def reservation(self,request,output_limit):
        wire_request(request,self.config)
        require(output_limit==self.config['output_token_limit'],'Output reservation differs from frozen API limit')
        require(time.time()<self.config['expires_at'],'Published tariff must be refreshed before use')
        return {'input_token_bound':self.config['input_token_limit'],'output_token_limit':output_limit,
            'cost_bound_units':cost_bound(self.config['input_token_limit'],output_limit)}

    def complete(self,request,ordinal,timeout):
        integer(ordinal,'call ordinal');deadline=time.monotonic()+timeout;reserved=None
        ledger=SpendLedger(self.budget_file,self.config['test_budget_nano'])
        try:
            bounds=self.reservation(request,self.config['output_token_limit']);payload=wire_request(request,self.config)
            key=_key(self.key_file)
            count_payload={name:payload[name] for name in ('model','input','tools','reasoning','text','parallel_tool_calls')}
            count,count_id=_post('/v1/responses/input_tokens',count_payload,key,deadline)
            require(count.get('object')=='response.input_tokens','Invalid token-count receipt')
            tokens=integer(count.get('input_tokens'),'counted input tokens')
            if tokens>bounds['input_token_bound']:
                return {'response':{'status':'input_limit','provider_id':'openai.responses/1','counted_input_tokens':tokens,
                    'transport_request_id':count_id},'usage':{'input_tokens':0,'output_tokens':0,'cost_units':0}}
            reserved=ledger.reserve(digest(payload),bounds['cost_bound_units'],key=self.run_id+':'+str(ordinal),
                metadata={'run_id':self.run_id,'epoch_id':self.epoch_id,'worker':self.worker,'ordinal':ordinal,
                    'model':self.model,'model_identity':provider_identity(),
                    'prompt_version':request['prompt_version'],'counted_input_tokens':tokens})
            raw,request_id=_post('/v1/responses',payload,key,deadline)
            result=parse_response(raw,request_id,self.config)
            usage=result['usage']
            result['response'].update(counted_input_tokens=tokens,wire_request_sha256=digest(payload),
                aggregate_dispatch_id=reserved,usage_charge_basis='conservative_published_rate_upper_bound')
            canonical(result)
            public=result['response']
            receipt={'usage':usage,'token_details':public['token_usage_details'],
                'response_status':public['status'],'transport_request_id':public['transport_request_id'],
                'provider_request_id':public['provider_request_id'],'model_identity':public['model_identity']}
            ledger.settle(reserved,None if usage is None else usage['cost_units'],
                halt=public['status'] in ('bounds_exceeded','unverified_response'),receipt=receipt)
            return result
        except Exception as exc:
            if reserved is not None:
                try:ledger.settle(reserved,None)
                except Exception:pass  # A failed write leaves the durable pending reservation in force.
            public={'status':'failed','provider_id':'openai.responses/1','error_type':type(exc).__name__}
            if isinstance(exc,WireFailure):public.update(error_kind=exc.kind,http_status=exc.status,transport_request_id=exc.request_id)
            return {'response':public,'usage':None if reserved is not None else {'input_tokens':0,'output_tokens':0,'cost_units':0}}
