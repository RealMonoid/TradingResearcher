"""Chronological resource decisions; no change to scientific inventory or rules."""
import hashlib
import re

from .codec import canonical, digest, integer, text
from .errors import Conflict
from .information_study import budget_state, summarize
from .binding import require


SCHEMA='study-resource-continuation/1'
AUTHORITY='bounded_resource_continuation_not_scientific_admission'
METADATA_BYTES=1024*1024
FIELDS={'key','study_id','expected_checkpoint','additional_compute_ms','additional_storage_bytes',
    'rationale','expected_progress','stop_reason'}
ACTIONS={'information_study_reserved','information_study_settled','information_study_continued'}


def validate_request(request):
    require(type(request) is dict and set(request)==FIELDS,'Exact resource continuation request required')
    for key in FIELDS-{'additional_compute_ms','additional_storage_bytes'}:text(request[key],key)
    require(re.fullmatch('[0-9a-f]{64}',request['expected_checkpoint']) is not None,'Exact resource checkpoint required')
    for key,maximum in (('additional_compute_ms',3600000),('additional_storage_bytes',4*1024**3)):
        integer(request[key],key);require(request[key]<=maximum,'Continuation tranche exceeds its bounded envelope')
    require(request['additional_compute_ms']+request['additional_storage_bytes']>0,'Nonempty continuation required')


class ResourceHistory:
    """Replay every relevant prefix, so later grants cannot heal earlier overruns."""
    def __init__(self,study):
        self.study=study;self.manifest=study['body']['manifest'];self.limits=self.manifest['profile']['budget']
        self.reservations=[];self.settlements=[];self.records={};self.results=[];self.orphan=False
        self.grants=[];self.additional_compute=0;self.additional_storage=0
        self.compute=0;self.storage=study['body']['initial_storage_bytes'];self.pending={};self.seen_attempts=set()
        self.overrun=self.storage>self.limits['max_storage_bytes'];self.unknown=False
        self.last_completed=0;self.no_progress=0
        self.hasher=hashlib.sha256(canonical({'schema':'study-resource-checkpoint/1','study_id':study['id'],
            'manifest_hash':digest(self.manifest),'source_footprint':study['body']['source_footprint']}).encode())

    @property
    def checkpoint(self):return self.hasher.hexdigest()

    def budget(self):
        value=budget_state(self.manifest,self.reservations,self.settlements,
            additional_compute_ms=self.additional_compute,additional_storage_bytes=self.additional_storage)
        value.update(initial_storage_bytes=self.study['body']['initial_storage_bytes'],
            continuation_storage_bytes=len(self.grants)*METADATA_BYTES,
            original_max_compute_ms=self.limits['max_compute_ms'],original_max_storage_bytes=self.limits['max_storage_bytes'],
            max_compute_ms=self.limits['max_compute_ms']+self.additional_compute,
            max_storage_bytes=self.limits['max_storage_bytes']+self.additional_storage)
        value['charged_storage_bytes']+=value['initial_storage_bytes']+value['continuation_storage_bytes']
        require(value['charged_compute_ms']==self.compute and value['charged_storage_bytes']==self.storage,
            'Chronological resource accounting differs')
        value['overrun']=value['overrun'] or self.overrun
        value['next_reservation_fits']=value['next_reservation_fits'] and not value['overrun'] and (
            self.storage+self.limits['attempt_storage_bytes']<=value['max_storage_bytes'])
        return value

    def terms(self,request):
        validate_request(request)
        require(request['study_id']==self.study['id'],'Continuation study differs')
        if request['expected_checkpoint']!=self.checkpoint:raise Conflict('Resource checkpoint is stale')
        budget=self.budget();records=list(self.records.values());summary=summarize(self.manifest,records)
        pending=next((w for w in self.manifest['worlds'] if w['id'] not in self.records
            or self.records[w['id']]['state']=='TECHNICAL_FAILURE'),None)
        require(not self.orphan and not self.unknown and not self.pending and not budget['overrun'],
            'Continuation cannot replace unresolved use or forgive a resource overrun')
        require(not summary['complete'] and not any(r['state']=='MODEL_GAP' for r in records)
            and pending is not None and budget['attempts_per_world'].get(pending['id'],0)<self.limits['max_attempts'],
            'Continuation requires unfinished work with an available frozen attempt')
        require(not budget['next_reservation_fits'],'Continuation requires a resource stop')
        require(self.compute+self.limits['attempt_compute_ms']<=budget['max_compute_ms']+request['additional_compute_ms']
            and self.storage+METADATA_BYTES+self.limits['attempt_storage_bytes']<=
                budget['max_storage_bytes']+request['additional_storage_bytes'],
            'Continuation must cover its metadata and the next full frozen reservation')
        completed=sum(r['state'] in ('VERIFIED','INFORMATION_GAP') for r in records)
        no_progress=0 if completed>self.last_completed else self.no_progress+1
        require(no_progress<=2,'Two continuations without completed-world inventory progress already recorded')
        return {'previous_continuation_id':self.grants[-1]['id'] if self.grants else None,
            'charged_compute_ms_before':self.compute,'charged_storage_bytes_before':self.storage,
            'completed_worlds_before':completed,'no_progress_continuations':no_progress}

    def references(self):
        refs=sorted({self.study['id']}|({self.grants[-1]['id']} if self.grants else set()))
        exposure=set(self.study['exposure'])|set(refs)
        if self.grants:exposure.update(self.grants[-1]['exposure'])
        return refs,sorted(exposure)

    def apply(self,event,load_artifact):
        details=event['details'];action=event['action']
        if event['actor']!='controller' or details.get('study_id')!=self.study['id'] or action not in ACTIONS:return
        if action=='information_study_reserved':
            item=details['reservation'];identity=item['attempt_id']
            require(identity not in self.seen_attempts,'Duplicate resource reservation')
            self.seen_attempts.add(identity)
            if self.pending:self.overrun=True
            self.pending[identity]=item;self.reservations.append(item)
            self.compute+=item['compute_ms'];self.storage+=item['storage_bytes']
        elif action=='information_study_settled':
            item=details['settlement'];identity=item['attempt_id']
            require(identity in self.pending,'Unreserved or duplicate resource settlement')
            reservation=self.pending.pop(identity);self.settlements.append(item)
            require(details['outcome']['world_id']==reservation['world_id'],'Resource settlement world differs')
            for field in ('compute_ms','storage_bytes'):
                observed=integer(item[field],field)
                charged=observed if item['usage_known'] else max(observed,reservation[field])
                if field=='compute_ms':self.compute+=charged-reservation[field]
                else:self.storage+=charged-reservation[field]
                self.overrun=self.overrun or observed>reservation[field]
            self.unknown=self.unknown or not item['usage_known'];self.orphan=self.orphan or details['orphan_uncertain']
            record=details['outcome'];self.records[record['world_id']]=record
            if details['artifact_id'] is not None:self.results.append(details['artifact_id'])
        else:
            require(set(details)=={'study_id','artifact_id'},'Exact continuation event required')
            grant=load_artifact(details['artifact_id']);body=grant['body']
            require(grant['creator']==grant['origin']=='controller' and grant['data_class']=='operations'
                and grant['authority']==AUTHORITY and type(body) is dict,'Owned resource decision required')
            request=body['request'];terms=self.terms(request);refs,exposure=self.references()
            integer(body['created_at'],'continuation creation time')
            require(body=={'schema':SCHEMA,'created_at':body['created_at'],'request':request,
                **terms,'scientific_readiness':False} and grant['source_refs']==refs
                and grant['exposure']==exposure and not grant['blob_refs'],'Resource continuation binding differs')
            self.additional_compute+=request['additional_compute_ms'];self.additional_storage+=request['additional_storage_bytes']
            self.grants.append(grant);self.storage+=METADATA_BYTES
            self.last_completed=terms['completed_worlds_before'];self.no_progress=terms['no_progress_continuations']
        self.overrun=self.overrun or self.compute>self.limits['max_compute_ms']+self.additional_compute or (
            self.storage>self.limits['max_storage_bytes']+self.additional_storage)
        self.hasher.update(b'\n'+canonical(event).encode())
