"""D083 technical-version revocation; historical records remain immutable/readable."""
import re

from .codec import Invalid, canonical, decode, digest, strings, text
from .errors import Conflict, Denied


SCHEMA='dependency-revocation/1'
AUTHORITY='technical_use_revocation_not_scientific_outcome'
PACKAGES={'reference-source-package/1','feature-source-package/1','binding-source-package/1','composition-source-package/1'}
VERSIONS=PACKAGES|{'data-snapshot/1','feature-definitions/1','feature-certificate/1','implementation-certificate/1','composition-certificate/1',
    'research-data-target/1','protected-data-binding/1'}
REQUEST_INPUTS={'bootstrap-input/1','information-diagnostics-input/1','population-world-input/1','information-study-input/1',
    'population-family-input/1','family-study-input/1'}
RESULT_INPUTS={'development-bootstrap/1','development-information-diagnostics/1','development-population-world/1',
    'development-information-study-attempt/1','evaluator-calibration-attempt/1','development-measurement/1',
    'development-population-family/1','family-study-attempt/1','family-calibration-attempt/1'}


def version_selector(artifact):
    body=artifact['body']
    schema=body.get('schema') if type(body) is dict else None
    if schema not in VERSIONS:raise Invalid('Unsupported technical-version type')
    origin='source' if schema in {'data-snapshot/1','feature-definitions/1','research-data-target/1'} else 'controller'
    if artifact['creator']!='controller' or artifact['origin']!=origin:
        raise Denied('An owned technical version is required')
    if schema in PACKAGES:
        footprint=body.get('footprint')
        if (type(footprint) is not dict or not 1<=len(footprint)<=128
                or any(type(k) is not str or type(v) is not str or not re.fullmatch('[0-9a-f]{64}',v)
                    for k,v in footprint.items())):
            raise Invalid('Exact retained package footprint required')
        return {'schema':schema,'footprint_sha256':digest(footprint)}
    return {'schema':schema,'artifact_id':artifact['id']}


class DependencyRevocations:
    def _revocation_records(self):
        return [self._artifact(row[0]) for row in self._db.execute(
            """SELECT id FROM artifacts WHERE json_extract(envelope,'$.body.schema')=?
                AND json_extract(envelope,'$.creator')='controller'
                AND json_extract(envelope,'$.origin')='controller'
                AND json_extract(envelope,'$.authority')=? ORDER BY rowid""",(SCHEMA,AUTHORITY))]

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

    def _technical_dependencies(self,artifact):
        body=artifact['body'];schema=body.get('schema') if type(body) is dict else None
        if schema in VERSIONS:version_selector(artifact)
        elif artifact['creator']!=artifact['origin'] or artifact['creator']!='controller':return None
        if schema in PACKAGES or schema=='data-snapshot/1':return []
        if schema=='research-data-target/1':return [body['request']['development_feature_certificate_id']]
        if schema=='protected-data-binding/1':return [body['request'][key] for key in ('target_id','data_snapshot_id','feature_certificate_id')]
        if schema=='feature-definitions/1':
            return [ref for ref in body.get('input_refs',[]) if self._artifact(ref)['body'].get('schema')=='data-snapshot/1']
        if schema=='feature-certificate/1':
            return [body[k] for k in ('data_snapshot_id','source_package_id','definitions_id') if body.get(k) is not None]
        if schema=='implementation-certificate/1':return [body['source_package_id']] if body.get('source_package_id') else []
        if schema=='compiled-hypothesis/1':
            args=body['dependency_arguments']
            return [body['data_snapshot_id'],body['source_package_id'],args['feature_certificate_id'],args['reference_certificate_id'],
                *([args['data_target_binding_id']] if 'data_target_binding_id' in args else [])]
        if schema=='reference-execution/1':return [body['compiled_id']]
        if schema=='data-use-assessment/1':return [body['compiled_id']]
        if schema=='composition-input/1':return [body['compiled_id'],body['source_package_id']]
        if schema=='composition-certificate/1':return [body['input_capsule_id']]
        if schema in {'evaluation-plan/1','evaluation-plan-input/1'}:
            request=body['request']
            return [request['compiled_id'],*request['dependence']['development_refs'],
                *([request['composition_certificate_id']] if 'composition_certificate_id' in request else []),
                *([request['data_use_assessment_id']] if 'data_use_assessment_id' in request else [])]
        if schema in REQUEST_INPUTS:
            request=body['request']
            return [request[k] for k in ('plan_id','execution_id','diagnostics_id') if k in request]
        if schema in ('evaluator-calibration-input/1','family-calibration-input/1'):return [body['request']['development_study_id']]
        if schema=='development-measurement-input/1':return [body['request']['snapshot_id']]
        if schema in RESULT_INPUTS:return [body['input_capsule_id']] if 'input_capsule_id' in body else [body['study_id']]
        return None

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

    def _inspect_dependency_use(self,actor,artifact_id):return self._dependency_use(artifact_id)

    def _require_usable_dependencies(self,artifact_id):
        status=self._dependency_use(artifact_id)['status']
        if status=='INVALIDATED_BY_DEPENDENCY':raise Denied('A used technical dependency is revoked')
        if status!='NOT_REVOKED':raise Invalid('Unsupported technical dependency binding')
