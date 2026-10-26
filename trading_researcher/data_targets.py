"""Predeclared public data targets with explicit private, exact version bindings.

No protected observations or quality-dependent metadata enter the public target.
Binding is infrastructure, not allocation, exposure acceptance or scientific freeze.
"""
from .binding import require
from .codec import Invalid, canonical, decode, digest, text
from .data import PARTITIONS, window
from .errors import Conflict, Denied
from .features import binding
from .formalization import utc


TARGET='research-data-target/1'
BINDING='protected-data-binding/1'
PROFILE='declared-historical-target/1'
TARGET_AUTHORITY='declared_scope_not_data_access'
BINDING_AUTHORITY='exact_private_binding_not_scientific_admission'


def semantics(definition):
    return {key:definition['body'][key] for key in ('specification_version','parameters','definitions')}


class DataTargets:
    def _target_request_replay(self,schema,request):
        for row in self._db.execute("""SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?
                AND json_extract(envelope,'$.creator')='controller'
                AND json_extract(envelope,'$.body.request.key')=?""",(schema,request['key'])):
            previous=self._artifact(row[0])
            if previous['body']['request']!=request:raise Conflict('Target request key already binds different content')
            return previous
        return None

    def _target_feature(self,actor,certificate_id):
        certificate=self._artifact(text(certificate_id,'feature certificate identity'))
        status=self._feature_certificate_status(actor,certificate_id)
        require(status['status'] in ('CURRENT','STALE'),'An intact exact raw-feature certificate is required')
        original=binding(self,certificate['body']['data_snapshot_id'])
        definition=self._artifact(certificate['body']['definitions_id'])
        require(definition['body']['parameters']=={'delay_seconds':original['request']['delay_seconds']},
            'Definition delay differs from its certified normalization')
        return certificate,original,definition

    def _public_data_target(self,target_id):
        target=self._artifact(text(target_id,'declared target identity'));body=target['body']
        require(target['creator']=='controller' and target['origin']=='source' and target['data_class']=='development'
            and target['authority']==TARGET_AUTHORITY and type(body) is dict
            and body.get('schema')==TARGET and body.get('profile')==PROFILE,'Owned public target declaration required')
        return target

    def _declare_data_target(self,actor,key,partition,universe,development_feature_certificate_id):
        request=decode(canonical({'key':text(key,'target declaration key'),'partition':partition,'universe':universe,
            'development_feature_certificate_id':text(development_feature_certificate_id,'development certificate identity')}))
        previous=self._target_request_replay(TARGET,request)
        if previous is not None:return previous
        require(type(partition) is str and partition in ('assessment','corroboration'),'A declared protected calendar partition is required')
        start,end,instruments=window(universe)
        lower,upper=(int(utc(value).timestamp()) for value in PARTITIONS[partition])
        require(lower<=start<end<=upper,'Target crosses its declared calendar partition')
        certificate,original,definition=self._target_feature(actor,development_feature_certificate_id)
        snapshot=original['snapshot']
        require(snapshot['data_class']=='development' and snapshot['body']['manifest']['partition']=='development',
            'Public target semantics must come from development, never the protected target')
        require(set(instruments)<=set(original['request']['universe']['instruments']),'Target instruments lack declared feature semantics')
        refs=sorted({certificate['id'],definition['id'],snapshot['body']['catalog_id']})
        exposure=set(refs)
        for identity in refs:exposure.update(self._artifact(identity)['exposure'])
        # Only development provenance and explicit requested scope are used here.
        # In particular, this operation never looks for a protected data snapshot.
        target=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'source',
            'data_class':'development','source_refs':refs,'exposure':sorted(exposure),'authority':TARGET_AUTHORITY,
            'body':{'schema':TARGET,'profile':PROFILE,'created_at':self._now(),'request':request,
                'catalog_id':snapshot['body']['catalog_id'],'definitions_id':definition['id'],
                'semantics_sha256':digest(semantics(definition)),
                'availability':{'basis':'assumed','delay_seconds':original['request']['delay_seconds']},
                'selection_knowledge':{'external_selection_knowledge':'UNKNOWN','model_training_exposure':'UNKNOWN'},
                'scientific_readiness':False,'allocation_reserved':False,'frozen':False,
                'qualification':'Predeclared reference only. No protected rows, coverage, quality, private certification status or private target identity; no unseen-history claim.'}})
        self._event(actor['name'],'data_target_declared',artifact_id=target['id'])
        return target

    def _private_target_inputs(self,actor,request):
        target=self._public_data_target(request['target_id']);public=target['body']
        self._require_usable_dependencies(target['id'])
        _,development,definition=self._target_feature(actor,public['request']['development_feature_certificate_id'])
        require(definition['id']==public['definitions_id'] and digest(semantics(definition))==public['semantics_sha256']
            and development['snapshot']['body']['catalog_id']==public['catalog_id'],'Declared feature meaning changed')
        certificate,original,actual_definition=self._target_feature(actor,request['feature_certificate_id'])
        snapshot=original['snapshot'];manifest=snapshot['body']['manifest']
        require(snapshot['id']==request['data_snapshot_id'],'Protected certificate belongs to another snapshot')
        require(snapshot['data_class']=='assessment' and manifest['partition']==public['request']['partition'],
            'Private target partition differs from the declaration')
        start,end,instruments=window(public['request']['universe'])
        left,right,available=window(manifest['universe'])
        require(left<=start<end<=right and set(instruments)<=set(available),'Private snapshot does not cover declared scope')
        require(semantics(definition)==semantics(actual_definition),'Protected feature meaning differs from the public declaration')
        require(original['catalog']==development['catalog'],'Protected feature catalog differs from declared catalog')
        return {'target_id':target['id'],'data_snapshot_id':snapshot['id'],'feature_certificate_id':certificate['id'],
            'public_definitions_id':definition['id'],'private_definitions_id':actual_definition['id'],
            'public_catalog_id':public['catalog_id'],'private_catalog_id':snapshot['body']['catalog_id'],
            'semantics_sha256':public['semantics_sha256'],'partition':manifest['partition'],
            'declared_universe':public['request']['universe']}

    def _bind_data_target(self,actor,key,target_id,data_snapshot_id,feature_certificate_id):
        request={key_name:text(value,key_name) for key_name,value in {'key':key,'target_id':target_id,
            'data_snapshot_id':data_snapshot_id,'feature_certificate_id':feature_certificate_id}.items()}
        previous=self._target_request_replay(BINDING,request)
        if previous is not None:return previous
        self._public_data_target(target_id)
        refs=sorted({target_id,data_snapshot_id,feature_certificate_id});exposure=set(refs)
        for identity in refs:exposure.update(self._artifact(identity)['exposure'])
        resolved=None;failure=None
        try:resolved=self._private_target_inputs(actor,request)
        except (Invalid,Denied,Conflict,OSError,KeyError,TypeError,ValueError) as exc:failure=type(exc).__name__
        result=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
            'data_class':'assessment','source_refs':refs,'exposure':sorted(exposure),'authority':BINDING_AUTHORITY,
            'body':{'schema':BINDING,'profile':PROFILE,'created_at':self._now(),'request':request,
                'status':'TARGET_BOUND' if failure is None else 'TARGET_BINDING_GAP','resolved':resolved,'failure_type':failure,
                'scientific_readiness':False,'allocation_reserved':False,'frozen':False,
                'qualification':'Private exact reference resolution only; no protected execution, exposure admission, scientific allocation or freeze.'}})
        self._event(actor['name'],'private_data_target_checked',artifact_id=result['id'],status=result['body']['status'])
        return result

    def _checked_target_binding(self,actor,binding_id):
        artifact=self._artifact(text(binding_id,'private target binding'));body=artifact['body']
        require(artifact['creator']==artifact['origin']=='controller' and artifact['data_class']=='assessment'
            and artifact['authority']==BINDING_AUTHORITY and type(body) is dict
            and body.get('schema')==BINDING and body.get('profile')==PROFILE and body.get('status')=='TARGET_BOUND',
            'Owned successful private target binding required')
        self._require_usable_dependencies(binding_id)
        resolved=self._private_target_inputs(actor,body['request'])
        require(resolved==body['resolved'],'Private target binding changed')
        return artifact

    def _resolve_compilation_target(self,actor,candidate,catalog_id,sources,feature_certificate_id,binding_id):
        reference=candidate['test_universe']['data_snapshot_ref']
        require(reference in sources,'Requested target is outside the authorized formalization')
        if binding_id is None:
            snapshot=self._data_snapshot(reference)
            require(catalog_id==snapshot['body']['catalog_id'],'Formalization and data catalog identities differ')
            return snapshot,[]
        private=self._checked_target_binding(actor,binding_id);resolved=private['body']['resolved']
        require(resolved['target_id']==reference and resolved['public_catalog_id']==catalog_id
            and resolved['feature_certificate_id']==feature_certificate_id,'Private binding differs from the requested target or certificate')
        declared=resolved['declared_universe'];universe=candidate['test_universe']
        require({key:universe[key] for key in ('start','end','instruments')}==declared,
            'Formalized universe differs from the predeclared target')
        return self._data_snapshot(resolved['data_snapshot_id']),[private['id'],reference,catalog_id,resolved['public_definitions_id']]

    def _declared_definition_origins(self,definitions,catalog_id,reference):
        """Model-side meaning checks consult public development semantics only."""
        artifact=self._artifact(reference)
        if type(artifact['body']) is not dict or artifact['body'].get('schema')!=TARGET:return False
        public=self._public_data_target(reference)['body']
        require(catalog_id==public['catalog_id'] and [item['id'] for item in definitions]==[public['definitions_id']],
            'Review must use the exact publicly declared feature definitions')
        require(digest(semantics(definitions[0]))==public['semantics_sha256'],'Public definition meaning differs')
        return True
