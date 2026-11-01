"""Typed D094 revocation overlay, never generic provenance propagation."""
from .codec import Invalid, canonical, decode, digest, strings, text
from .errors import Conflict, Denied
from .revocations import (VERSIONS as LEGACY_VERSIONS, SCHEMA, AUTHORITY,
                          version_selector as legacy_selector)

PAIRED_VERSIONS={'paired-source-package/1','paired-reference-certificate/1','paired-composition-certificate/1'}
VERSIONS=LEGACY_VERSIONS|PAIRED_VERSIONS


def version_selector(artifact):
    schema=artifact['body'].get('schema') if type(artifact['body']) is dict else None
    if schema not in PAIRED_VERSIONS:
        return legacy_selector(artifact)
    if artifact['creator']!=artifact['origin'] or artifact['creator']!='controller':
        raise Denied('An owned paired technical version is required')
    if schema=='paired-source-package/1':
        footprint=artifact['body'].get('footprint')
        if (type(footprint) is not dict or not 1<=len(footprint)<=128
                or any(type(key) is not str or type(value) is not str or len(value)!=64
                    or set(value)-set('0123456789abcdef') for key,value in footprint.items())):
            raise Invalid('Exact paired retained source footprint required')
        return {'schema':schema,'footprint_sha256':digest(footprint)}
    return {'schema':schema,'artifact_id':artifact['id']}


class PairedRevocations:
    def _technical_dependencies(self,artifact):
        body=artifact['body']
        schema=body.get('schema') if type(body) is dict else None
        if schema in PAIRED_VERSIONS:
            version_selector(artifact)
        elif artifact['creator']!=artifact['origin'] or artifact['creator']!='controller':
            return super()._technical_dependencies(artifact)
        if schema=='paired-source-package/1':
            return []
        if schema=='paired-reference-certificate/1':
            return [body['source_package_id']]
        if schema=='paired-compiled-hypothesis/1':
            return [body[key] for key in ('data_snapshot_id','feature_certificate_id',
                                          'reference_certificate_id','source_package_id')]
        if schema in ('paired-composition-certificate/1','paired-reference-execution/1','paired-execution-input/1'):
            return [body['compiled_id']]
        return super()._technical_dependencies(artifact)

    def _revoke_dependency(self,actor,key,dependency_id,reason,evidence_refs):
        request=decode(canonical({'key':text(key,'revocation key'),'dependency_id':text(dependency_id,'dependency identity'),
            'reason':text(reason,'defect reason'),'evidence_refs':strings(evidence_refs,'defect evidence')}))
        if not 1<=len(request['evidence_refs'])<=32:raise Invalid('One through 32 retained defect evidence references required')
        for previous in self._revocation_records():
            if previous['body']['request']['key']==key:
                if previous['body']['request']!=request:raise Conflict('Revocation key already binds different evidence')
                return previous
        target=self._artifact(dependency_id)
        selector=version_selector(target)
        refs=sorted({dependency_id,*request['evidence_refs']})
        exposure=set(refs)
        for ref in refs:exposure.update(self._artifact(ref)['exposure'])
        affected=self._affected_dependency_uses(selector)
        saved=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
            'data_class':'operations','source_refs':refs,'exposure':sorted(exposure),
            'authority':AUTHORITY,
            'body':{'schema':SCHEMA,'created_at':self._now(),'request':request,'selector':selector,
                'affected_artifact_ids':affected,'affected_scope':'supported_typed_bindings_at_revocation',
                'status':'REVOKED','scientific_readiness':False,
                'qualification':'Operator-recorded defect and evidence; immutable history, no empirical falsification or deployment authority.'}})
        self._event(actor['name'],'dependency_revoked',artifact_id=saved['id'],dependency_id=dependency_id)
        return saved

    def _affected_dependency_uses(self,selector):
        # Capture the affected set at the event, then continue checking future
        # objects dynamically. Exposure, supersession and generic provenance are
        # deliberately absent from this reverse-use graph.
        reverse={};affected=set()
        for row in self._db.execute('SELECT id FROM artifacts'):
            artifact=self._artifact(row[0]);body=artifact['body']
            schema=body.get('schema') if type(body) is dict else None
            try:
                dependencies=self._technical_dependencies(artifact)
                if dependencies is None:continue
                if schema in VERSIONS and version_selector(artifact)==selector:affected.add(artifact['id'])
            except (Invalid,Denied,KeyError,TypeError):continue
            for dependency in dependencies:reverse.setdefault(dependency,set()).add(artifact['id'])
        pending=list(affected)
        while pending:
            for dependent in reverse.get(pending.pop(),()):
                if dependent not in affected:affected.add(dependent);pending.append(dependent)
        return sorted(affected)

    def _dependency_use(self,artifact_id):
        text(artifact_id,'artifact identity')
        records=self._revocation_records()
        by_selector={}
        for record in records:
            by_selector.setdefault(digest(record['body']['selector']),[]).append(record)
        pending=[artifact_id];seen=set();unknown=[];invalidations=[]
        while pending:
            identity=pending.pop()
            if identity in seen:continue
            if len(seen)>=4096:raise Invalid('Technical dependency closure exceeds the inspection envelope')
            seen.add(identity);artifact=self._artifact(identity);body=artifact['body']
            schema=body.get('schema') if type(body) is dict else None
            if schema in VERSIONS:
                for record in by_selector.get(digest(version_selector(artifact)),[]):
                    invalidations.append({'revocation_id':record['id'],'dependency_id':record['body']['request']['dependency_id'],
                        'used_version_id':identity})
            try:dependencies=self._technical_dependencies(artifact)
            except (KeyError,TypeError):dependencies=None
            if dependencies is None:unknown.append(identity)
            else:
                # Different typed fields may share one dependency. Validate each
                # identity before deduplicating the traversal edges.
                if type(dependencies) is not list or len(dependencies)>256:
                    raise Invalid('Technical dependencies must be a bounded list')
                pending.extend(dict.fromkeys(text(item,'technical dependency') for item in dependencies))
        return {'artifact_id':artifact_id,'status':'INVALIDATED_BY_DEPENDENCY' if invalidations else
            ('UNKNOWN_BINDING' if unknown else 'NOT_REVOKED'),'checked_versions':sorted(seen),
            'invalidations':sorted(invalidations,key=lambda item:(item['used_version_id'],item['revocation_id'])),
            'unknown_bindings':sorted(unknown),'scientific_readiness':False,
            'qualification':'Current supported technical bindings only; NOT_REVOKED is not validity or scientific admission.'}

