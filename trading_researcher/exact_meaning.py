"""AST4 historical review of the complete finite-inquiry settlement receipt.

The immutable legacy validator and substantive comparison protocol stay intact.
All original invocation, full-packet, role and judgment checks are retained.
"""
from .auxiliary import mapping_count, request_for, validate_judgment
from datetime import datetime,timezone
import sqlite3

from .codec import Invalid, canonical, decode, digest, integer
from .exact_formalization import SCHEMA
from .meaning_reviews import require
from .inquiry import resources
from .openai_provider import provider_identity, wire_request

POLICY='exact-finite-meaning-receipt/1'
FIELDS={'call_id','response_id','late','within_reservation','accounting_valid','usage_unknown',
        'installed_sources_unchanged','resource_settlement_verified','resource_gap'}


class ExactMeaning:
    def _exact_review_accounting(self,job,call):
        # Historical inspection authenticates the already consumed settlement;
        # it neither requires an active grant nor creates/reuses a dispatch.
        try:
            epoch=self._epoch(job['spec']['research_epoch_id'])
            with resources._ledger(self)._connect() as db:
                db.execute('BEGIN')
                state=resources._row(self,epoch,db)
                entries=[entry for entry in state['calls'] if entry['call_id']==call['id']]
                require(len(entries)==1 and entries[0]['job_id']==job['id']
                    and entries[0]['stage']=='semantic-review/v1','Historical exact review has no matching consumed slot')
                entry=entries[0]
                cost=resources.authenticate(self,epoch,entry,db)
        except (OSError,sqlite3.Error,KeyError,TypeError,ValueError) as exc:
            raise Invalid('Historical exact review settlement is unavailable: '+str(exc)) from exc
        return {'entry':entry,'settled_cost_units':cost,'resource_binding_hash':digest(state['binding'])}

    def _historical_meaning_call(self,target,job,call):
        if target['body'].get('schema')!=SCHEMA:
            return super()._historical_meaning_call(target,job,call)
        require(call['state']=='recorded' and call['response_id'] is not None,'Review response is unresolved or invalid')
        receipt=decode(call['receipt'])
        require(type(receipt) is dict and set(receipt)==FIELDS and receipt['call_id']==call['id']
            and receipt['response_id']==call['response_id'],'Malformed or mismatched exact finite review receipt')
        require(receipt['late'] is False and receipt['within_reservation'] is True
            and receipt['accounting_valid'] is True and receipt['usage_unknown'] is False
            and receipt['installed_sources_unchanged'] is True and receipt['resource_settlement_verified'] is True
            and receipt['resource_gap'] is None,'Exact review accounting, source currentness or resource settlement is unverified')
        invocation=call['invocation']
        require(invocation is not None and invocation['result_id'] is not None,'No owned controller invocation')
        incoming,result=(self._artifact(invocation[n]) for n in ('input_id','result_id'))
        require(incoming['creator']==result['creator']=='controller'
            and incoming['body']['schema']=='provider-invocation-input/1'
            and result['body']['schema']=='provider-invocation/1'
            and incoming['body']['call_id']==result['body']['call_id']==call['id']
            and result['body']['input_id']==incoming['id']
            and result['body']['request_id']==incoming['body']['request_id']==call['request_id']
            and result['body']['response_id']==call['response_id']
            and result['body']['response_usable'] is True
            and result['body']['installed_sources_unchanged'] is True
            and result['body']['execution_path']=='controller-counted-inquiry-adapter/1'
            and canonical(result['body']['receipt'])==canonical(receipt),'Controller invocation binding differs')
        packet=self._auxiliary_packet_for_spec(job['spec'])
        request=self._artifact(call['request_id'])['body']['request']
        require(canonical(request)==canonical(request_for(job['spec'],packet))
            and digest(request)==incoming['body']['request_sha256'],'Review did not receive the exact frozen comparison packet')
        accounting=self._exact_review_accounting(job,call)
        config=job['spec']['research_call_profile']['generation_parameters']['openai_responses']
        wire_hash=digest(wire_request(request,config))
        require(canonical(incoming['body']['configuration'])==canonical(config)
            and accounting['entry']['wire_sha256']==wire_hash
            and incoming['body']['adapter_run_id']==accounting['entry']['run_id']
            and type(incoming['body']['adapter_ordinal']) is int and incoming['body']['adapter_ordinal']==0,
            'Counted review configuration, full wire or native dispatch differs')
        started,observed=(self._artifact(incoming['body'][name])
            for name in ('input_count_attempt_id','input_count_observation_id'))
        require(all(item['creator']==item['origin']=='controller' and item['job_id']==job['id']
            and item['generation']==call['generation'] and item['body']['schema']=='inquiry-input-count-attempt/1'
            and item['body']['epoch_id']==call['epoch_id'] and item['body']['request_sha256']==digest(request)
            and item['body']['wire_sha256']==wire_hash and item['id'] in incoming['source_refs']
            for item in (started,observed))
            and started['body']['state']=='STARTED' and canonical(started['body']['request'])==canonical(request)
            and observed['body']['state']=='OBSERVED' and observed['body']['attempt_id']==started['id']
            and type(incoming['body']['input_count_receipts']) is list and incoming['body']['input_count_receipts']
            and canonical(observed['body']['count_receipts'])==canonical(incoming['body']['input_count_receipts']),
            'Owned full-wire count observations differ')
        counts=incoming['body']['input_count_receipts']
        require(len(counts)==1,'One exact auxiliary input-count receipt required')
        counted=counts[0]
        require(type(counted) is dict and set(counted)=={'schema','wire_request_sha256','counted_input_tokens',
            'input_token_bound','transport_request_id','model_identity','observed_at_utc','qualification'},
            'Malformed exact input-count receipt')
        tokens=integer(counted['counted_input_tokens'],'historical counted input tokens')
        bound=integer(counted['input_token_bound'],'historical counted input bound')
        require(counted['schema']=='openai-exact-input-reservation/1' and counted['wire_request_sha256']==wire_hash
            and tokens<=config['input_token_limit'] and bound==min(tokens+128,config['input_token_limit'])
            and bound==accounting['entry']['input_bound']
            and canonical(counted['model_identity'])==canonical(provider_identity())
            and (counted['transport_request_id'] is None or type(counted['transport_request_id']) is str)
            and counted['qualification']=='Input-count receipt, not inference usage or an invoice.',
            'Count receipt differs from the frozen wire, model or authenticated native bound')
        try:observed_at=datetime.fromisoformat(counted['observed_at_utc'])
        except (TypeError,ValueError) as exc:raise Invalid('Invalid historical count UTC instant') from exc
        require(observed_at.tzinfo is not None and observed_at.utcoffset()==timezone.utc.utcoffset(observed_at)
            and 0<=observed_at.timestamp()<=incoming['body']['created_at']+1,
            'Historical count time is not UTC or precedes no retained invocation')
        require(call['owner']==job['spec']['allowed_workers'][0] and call['owner']!=target['creator'],
                'Formalizer cannot supply its own independent review')
        response=self._artifact(call['response_id'])['body']
        require(response['call_id']==call['id'],'Response belongs to a different call')
        public=response['response']
        require(public.get('status')=='completed' and type(public.get('output')) is dict
            and set(public['output'])=={'status','review'} and public['output']['status']=='final',
            'No complete meaning review was returned')
        validate_judgment(public['output']['review'],mapping_count(target))
        return public['output']['review'],packet

    def _meaning_inventory(self,target):
        inventory,refs=super()._meaning_inventory(target)
        if target['body'].get('schema')==SCHEMA:
            settlements=[]
            for job in inventory['jobs']:
                for call in job['calls']:
                    try:observed={'accounting':self._exact_review_accounting(job,call)}
                    except Exception as exc:observed={'error':{'type':type(exc).__name__,'reason':str(exc)}}
                    settlements.append({'call_id':call['id'],**observed})
            inventory={**inventory,'policy':{**inventory['policy'],
                'finite_receipt_policy':POLICY,'execution_sources':self._execution_sources()},
                'finite_review_settlements':settlements}
        return inventory,refs
