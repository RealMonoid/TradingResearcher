"""Read-only inference usage reporting; reservations and token subsets stay separate."""
from pathlib import Path
from datetime import datetime,timezone
import sqlite3

from .codec import Invalid, canonical, decode, integer


IDENTITY_KEYS={'requested_model','reported_model','catalog_name','catalog_version','catalog_source',
               'immutable_snapshot_id','immutable_snapshot_status'}


def validate_identity(identity):
    if type(identity) is not dict or set(identity)!=IDENTITY_KEYS:
        raise Invalid('Exact model identity required')
    if any(value is not None and type(value) is not str for value in identity.values()):
        raise Invalid('Model identity fields must be strings or explicitly unknown')
    if identity['immutable_snapshot_status']!='UNKNOWN' or identity['immutable_snapshot_id'] is not None:
        raise Invalid('This adapter has no verified immutable provider snapshot')


def _utc(value):
    if value is None:return None
    integer(value,'host timestamp')
    return datetime.fromtimestamp(value,tz=timezone.utc).isoformat().replace('+00:00','Z')


def _identity(call):
    receipt=call['receipt'] or {};metadata=call['metadata']
    identity=receipt.get('model_identity',metadata.get('model_identity'))
    if identity is None:
        identity={name:None for name in IDENTITY_KEYS}
        identity.update(requested_model=metadata.get('model'),immutable_snapshot_status='UNKNOWN')
    validate_identity(identity)
    return identity


def validate_receipt(receipt,charge):
    if receipt is None:return
    if type(receipt) is not dict or not {'usage','token_details'}<=set(receipt) or set(receipt)-{
        'usage','token_details','response_status','transport_request_id','provider_request_id','model_identity'}:
        raise Invalid('Exact public accounting receipt required')
    if 'model_identity' in receipt:validate_identity(receipt['model_identity'])
    usage=receipt['usage']
    if usage is not None:
        if type(usage) is not dict or set(usage)!={'input_tokens','output_tokens','cost_units'}:
            raise Invalid('Malformed reported usage')
        for value in usage.values():integer(value,'reported usage')
        if usage['cost_units']!=charge:raise Invalid('Receipt and settled currency disagree')
    details=receipt['token_details']
    if type(details) is not dict or set(details)!={'cached_input_tokens','reasoning_output_tokens'}:
        raise Invalid('Exact optional token subsets required')
    for name,parent in (('cached_input_tokens','input_tokens'),('reasoning_output_tokens','output_tokens')):
        if details[name] is not None:
            integer(details[name],name)
            if usage is None or details[name]>usage[parent]:raise Invalid('Token subset exceeds known parent')


def _totals(calls):
    known=[call['receipt'] for call in calls if call['receipt'] is not None and call['receipt']['usage'] is not None]
    result={'calls':len(calls),'known_usage_calls':len(known),'unknown_usage_calls':len(calls)-len(known),
            'known_input_tokens':sum(r['usage']['input_tokens'] for r in known),
            'known_output_tokens':sum(r['usage']['output_tokens'] for r in known)}
    result['known_total_tokens']=result['known_input_tokens']+result['known_output_tokens']
    result['exact_total_tokens']=result['known_total_tokens'] if len(known)==len(calls) else None
    for key,label in (('cached_input_tokens','cached'),('reasoning_output_tokens','reasoning')):
        values=[r['token_details'][key] for r in known if r['token_details'][key] is not None]
        result['known_'+key]=sum(values)
        result[label+'_detail_calls']=len(values)
        result['exact_'+key]=sum(values) if len(values)==len(calls) else None
    return result


def report_connection(db):
    tables={row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    columns='m.created_at,m.body' if 'token_metadata' in tables else 'NULL,NULL'
    columns+=',r.body' if 'usage_receipts' in tables else ',NULL'
    columns+=',s.recorded_at' if 'dispatch_settlements' in tables else ',NULL'
    joins=' LEFT JOIN token_metadata m ON m.id=d.id' if 'token_metadata' in tables else ''
    joins+=' LEFT JOIN usage_receipts r ON r.id=d.id' if 'usage_receipts' in tables else ''
    joins+=' LEFT JOIN dispatch_settlements s ON s.id=d.id' if 'dispatch_settlements' in tables else ''
    rows=db.execute('SELECT d.id,d.request_hash,d.reserved,d.charged,d.state,'+columns+
        ' FROM dispatches d'+joins+' ORDER BY d.rowid').fetchall()
    calls=[{'dispatch_id':row[0],'request_sha256':row[1],'reserved_nano':row[2],
            'charged_nano':row[2] if row[3] is None else row[3],'state':row[4],'created_at':row[5],
            'admitted_at_utc':_utc(row[5]),'settled_at_utc':_utc(row[8]),
            'metadata':{} if row[6] is None else decode(row[6]),
            'receipt':None if row[7] is None else decode(row[7])} for row in rows]
    groups={};models={}
    for call in calls:
        call['provider']=call['metadata'].get('provider','openai')
        if call['provider'] not in ('openai','anthropic'):raise Invalid('Unknown accounting provider')
        call['model_identity']=_identity(call)
        model_key=canonical(call['model_identity'])
        meta=call['metadata'];key=(meta.get('epoch_id'),meta.get('run_id'),meta.get('worker'),model_key,call['provider'])
        groups.setdefault(key,[]).append(call)
        models.setdefault((call['provider'],model_key),[]).append(call)
    cap=db.execute('SELECT cap FROM budget WHERE singleton=1').fetchone()[0]
    charged=sum(call['charged_nano'] for call in calls)
    providers=sorted({call['provider'] for call in calls})
    return {'schema':'framework-provider-usage-report/3',
        'provider':providers[0] if len(providers)==1 else ('mixed' if providers else None),'providers':providers,
        'scope':'Inference dispatches in this ledger; excludes Codex chat and scripted fixture counters.',
        'qualification':'Provider-reported tokens. Known sums exclude unknown receipts. Cached/reasoning counts are subsets. Currency is a conservative published-rate bound, not an invoice.',
        'totals':_totals(calls),'runs':[{'epoch_id':key[0],'run_id':key[1],'worker':key[2],
            'model_identity':decode(key[3]),'provider':key[4],**_totals(group)}
            for key,group in groups.items()],
        'models':[{'provider':key[0],'model_identity':decode(key[1]),**_totals(group)} for key,group in models.items()],
        'timestamp_basis':'UTC; admission and durable local settlement, not provider execution start/end. Missing historical fields are not backfilled.',
        'money':{'currency':'USD','units_per_usd':1000000000,'cap_nano':cap,'charged_nano':charged,
            'available_nano':max(0,cap-charged),'halted':any(call['state']!='settled' for call in calls)},
        'calls':calls}


def read_usage_report(path):
    path=Path(path).resolve(strict=True)
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)
    try:
        db.execute('BEGIN')
        return report_connection(db)
    finally:db.close()
