"""D083 bindings for exact runtime packages/certificates; old types delegate."""
from .codec import Invalid, canonical, decode, digest, strings, text
from .errors import Conflict, Denied
from .revocations import SCHEMA, AUTHORITY

PACKAGES = {'exact-source-package/1','exact-composition-source-package/1'}
VERSIONS = PACKAGES|{'exact-reference-certificate/1','exact-composition-certificate/1'}
PROFILE = 'exact-reference-computation/1'


def _schema(artifact):
    body = artifact['body']
    return body.get('schema') if type(body) is dict else None


def version_selector(artifact):
    schema = _schema(artifact)
    body = artifact['body']
    if schema not in VERSIONS:raise Invalid('Unsupported exact technical version')
    authority = ('retained_source_not_certified' if schema in PACKAGES else
                 'exact_implementation_conformance_only' if schema == 'exact-reference-certificate/1'
                 else 'exact_descriptive_development_only')
    expected_profile = 'exact-certified-composition/1' if schema.startswith('exact-composition-') else PROFILE
    data_class = 'development' if schema == 'exact-composition-certificate/1' else 'operations'
    if (artifact['creator'] != 'controller' or artifact['origin'] != 'controller'
            or artifact['data_class'] != data_class or artifact['authority'] != authority
            or body.get('profile') != expected_profile):
        raise Denied('An owned exact technical version is required')
    if schema in PACKAGES:
        footprint = body.get('footprint')
        if (type(footprint) is not dict or not 1 <= len(footprint) <= 128
                or any(type(key) is not str or type(value) is not str or len(value) != 64
                    or set(value)-set('0123456789abcdef') for key,value in footprint.items())):
            raise Invalid('Exact retained source footprint required')
        return {'schema':schema,'footprint_sha256':digest(footprint)}
    return {'schema':schema,'artifact_id':artifact['id']}


class ExactRevocations:
    def _technical_dependencies(self, artifact):
        schema = _schema(artifact)
        body = artifact['body']
        if schema in VERSIONS:
            version_selector(artifact)
            if schema in PACKAGES:return []
            refs = [text(body.get('source_package_id'),'exact source package dependency')]
            if schema == 'exact-composition-certificate/1':refs.append(text(body.get('compiled_id'),'exact compiled dependency'))
            return refs
        computations = {'exact-compilation-input/1','exact-compiled-hypothesis/1',
                        'exact-execution-input/1','exact-reference-execution/1'}
        if schema not in computations:return super()._technical_dependencies(artifact)
        if (artifact['creator'] != 'controller' or artifact['origin'] != 'controller'
                or artifact['authority'] != 'exact_descriptive_development_only'):
            raise Denied('An owned exact computation binding is required')
        if schema == 'exact-compilation-input/1':
            return [body['dependencies'][key] for key in ('data_snapshot_id','feature_certificate_id','reference_certificate_id')]
        if schema == 'exact-compiled-hypothesis/1':
            return [body[key] for key in ('input_id','data_snapshot_id','feature_certificate_id','reference_certificate_id','source_package_id')]
        return [body[key] for key in ('compiled_id','composition_id')]

    def _dependency_use(self, artifact_id):
        result = super()._dependency_use(artifact_id)
        invalidations = list(result['invalidations'])
        # The inherited traversal follows our typed edges; add only the new
        # version selectors to its existing revocation findings.
        records = self._revocation_records()
        for identity in result['checked_versions']:
            artifact = self._artifact(identity)
            if _schema(artifact) not in VERSIONS:continue
            selector = version_selector(artifact)
            for record in records:
                if record['body']['selector'] == selector:
                    invalidations.append({'revocation_id':record['id'],
                        'dependency_id':record['body']['request']['dependency_id'],'used_version_id':identity})
        if not invalidations:return result
        return {**result,'status':'INVALIDATED_BY_DEPENDENCY',
            'invalidations':sorted(invalidations,key=lambda item:(item['used_version_id'],item['revocation_id']))}

    def _affected_dependency_uses(self, selector):
        if selector.get('schema') not in VERSIONS:return super()._affected_dependency_uses(selector)
        reverse,affected = {},set()
        for row in self._db.execute('SELECT id FROM artifacts'):
            artifact = self._artifact(row[0])
            try:
                dependencies = self._technical_dependencies(artifact)
                if dependencies is None:continue
                if _schema(artifact) in VERSIONS and version_selector(artifact) == selector:
                    affected.add(artifact['id'])
            except (Invalid,Denied,KeyError,TypeError):continue
            for dependency in dependencies:reverse.setdefault(dependency,set()).add(artifact['id'])
        pending = list(affected)
        while pending:
            for dependent in reverse.get(pending.pop(),()):
                if dependent not in affected:
                    affected.add(dependent);pending.append(dependent)
        return sorted(affected)

    def _revoke_dependency(self, actor, key, dependency_id, reason, evidence_refs):
        target = self._artifact(text(dependency_id,'dependency identity'))
        if _schema(target) not in VERSIONS:
            return super()._revoke_dependency(actor,key,dependency_id,reason,evidence_refs)
        request = decode(canonical({'key':text(key,'revocation key'),'dependency_id':dependency_id,
            'reason':text(reason,'defect reason'),'evidence_refs':strings(evidence_refs,'defect evidence')}))
        if not 1 <= len(request['evidence_refs']) <= 32:
            raise Invalid('One through 32 retained defect evidence references required')
        for previous in self._revocation_records():
            if previous['body']['request']['key'] == key:
                if previous['body']['request'] != request:
                    raise Conflict('Revocation key already binds different evidence')
                return previous
        selector = version_selector(target)
        refs = sorted({dependency_id,*request['evidence_refs']})
        exposure = set(refs)
        for ref in refs:exposure.update(self._artifact(ref)['exposure'])
        saved = self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
            'data_class':'operations','source_refs':refs,'exposure':sorted(exposure),'authority':AUTHORITY,
            'body':{'schema':SCHEMA,'created_at':self._now(),'request':request,'selector':selector,
                'affected_artifact_ids':self._affected_dependency_uses(selector),
                'affected_scope':'supported_typed_bindings_at_revocation','status':'REVOKED','scientific_readiness':False,
                'qualification':'Operator-recorded defect and evidence; immutable history, no empirical falsification or deployment authority.'}})
        self._event(actor['name'],'dependency_revoked',artifact_id=saved['id'],dependency_id=dependency_id)
        return saved
