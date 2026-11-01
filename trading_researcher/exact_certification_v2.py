"""Owned D098 source certification; immutable v1 certificates stay v1."""
import hashlib
from pathlib import Path
import tempfile

from .binding import hashes, require
from .certification import _environment_current
from .codec import canonical, digest, integer, text
from .errors import Denied
from .exact_feedback import ExactFeedbackBroker
from .exact_revocations_v2 import ExactRevocationsV2
from .exact_certification import GOLDEN_PINS as LEGACY_GOLDEN_PINS
from .storage import blob_identity
from . import exact_runtime_v2 as runtime

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = 'exact_implementation_conformance_only'
SOURCE_AUTHORITY = 'retained_source_not_certified'
HOST_FILES = ('trading_researcher/exact_certification_v2.py','trading_researcher/exact_revocations_v2.py',
    'trading_researcher/exact_execution_v2.py','trading_researcher/exact_composition_v2.py',
    'trading_researcher/EXACT_NATIVE_V2.md','tests/test_exact_composition_v2_review.py')
LOADED = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in HOST_FILES}
GOLDEN_PINS = {
    **LEGACY_GOLDEN_PINS,
    'tests/test_exact_resources_v2.py':'f020205e3d1d1e8955d1f18f171a81cd3779f3a828f3d895d38956afd5202a99',
    'tests/test_exact_resources_v2_review.py':'62257bca25e3de38c2392b869f3418e5a4fc33caf961f227275212e5e3b423ae',
}
RESERVED = ('exact-source-package/','exact-reference-certificate/')


def _expected_result():
    return {'schema':'exact-conformance-result/2','profile':runtime.PROFILE,
            'resource_contract':runtime.RESOURCE_CONTRACT,'tests':runtime.EXPECTED_TESTS,
            'failures':0,'errors':0,'skipped':0,'scientific_readiness':False}


class ExactRuntimeBrokerV2(ExactRevocationsV2, ExactFeedbackBroker):

    def _exact_source_identity(self):
        # Explicit frozen parent entry avoids a dynamic execution/source cycle
        # while retaining the controlled-feedback and all inherited sources.
        parent = ExactFeedbackBroker._exact_source_identity(self)
        current = {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in HOST_FILES}
        require(current == LOADED, 'Exact qualification host changed; restart and independently requalify')
        bundle = runtime.read_bundle()
        require(all(hashlib.sha256(bundle[name]).hexdigest() == expected for name,expected in GOLDEN_PINS.items()),
                'Independent exact golden expectations changed')
        return {**parent,**hashes(bundle),**current}

    def _breakout_research_sources(self):
        return self._exact_source_identity()

    def _add_source(self, actor, body, data_class, exposure=None):
        if type(body) is dict and str(body.get('schema','')).startswith(RESERVED):
            raise Denied('Exact packages and certificates require owned qualification operations')
        return super()._add_source(actor,body,data_class,exposure)

    def _put_artifact(self, actor, lease, body, source_refs):
        if type(body) is dict and str(body.get('schema','')).startswith(RESERVED):
            raise Denied('Exact packages and certificates require owned qualification operations')
        return super()._put_artifact(actor,lease,body,source_refs)

    def _exact_retain_package(self, bundle):
        require(set(bundle) == set(runtime.FILES) and sum(map(len,bundle.values())) <= 16*1024*1024)
        files = {name:self._stage_blob_bytes(raw) for name,raw in sorted(bundle.items())}
        with self._transaction():
            for descriptor in files.values():self._register_blob(descriptor)
            return self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'operations','source_refs':[],'exposure':[],
                'blob_refs':sorted({item['sha256'] for item in files.values()}),'authority':SOURCE_AUTHORITY,
                'body':{'schema':'exact-source-package/2','profile':runtime.PROFILE,
                    'resource_contract':runtime.RESOURCE_CONTRACT,'created_at':self._now(),
                    'files':files,'footprint':hashes(bundle),
                    'bootstrap_sha256':hashlib.sha256(runtime.BOOTSTRAP.encode()).hexdigest()}})

    def _exact_package(self, identity):
        item = self._artifact(text(identity,'exact source package'))
        body = item['body']
        require(item['creator'] == item['origin'] == 'controller' and item['data_class'] == 'operations'
            and item['authority'] == SOURCE_AUTHORITY and type(body) is dict
            and body.get('schema') == 'exact-source-package/2' and body.get('profile') == runtime.PROFILE
            and body.get('resource_contract') == runtime.RESOURCE_CONTRACT
            and type(body.get('files')) is dict and set(body['files']) == set(runtime.FILES)
            and type(item.get('blob_refs')) is list,
            'An owned complete exact source package is required')
        self._require_usable_dependencies(identity)
        require(body.get('bootstrap_sha256') == hashlib.sha256(runtime.BOOTSTRAP.encode()).hexdigest())
        for descriptor in body['files'].values():
            require(type(descriptor) is dict and set(descriptor) == {'sha256','size'},
                    'Exact source descriptor must contain only sha256 and size')
            blob_identity(descriptor['sha256'])
            integer(descriptor['size'],'exact source byte size')
        require(sum(descriptor['size'] for descriptor in body['files'].values()) <= 16*1024*1024)
        bundle = {}
        for name,descriptor in body['files'].items():
            committed = self._db.execute('SELECT size FROM blobs WHERE sha256=?',(descriptor['sha256'],)).fetchone()
            require(committed is not None and committed['size'] == descriptor['size'],
                    'Exact source descriptor differs from committed blob metadata')
            raw = self._read_blob_bytes(descriptor['sha256'])
            require(len(raw) == descriptor['size'])
            bundle[name] = raw
        require(sum(map(len,bundle.values())) <= 16*1024*1024 and hashes(bundle) == body.get('footprint')
            and set(item['blob_refs']) == {value['sha256'] for value in body['files'].values()})
        return bundle

    def certify_exact_runtime(self, token):
        with self._mutex:
            self._binding_owner(token)
            sources = self._exact_source_identity()
            bundle = runtime.read_bundle()
        package = self._exact_retain_package(bundle)
        attempt = self._bound_start('exact_runtime_certification',package['id'])
        result,error = None,None
        try:
            with tempfile.TemporaryDirectory(prefix='trf-exact-cert-') as directory:
                result = runtime.run_child(bundle,'certify',{'profile':runtime.PROFILE},directory)
            require(canonical(result['result']) == canonical(_expected_result()))
            require(hashes(runtime.read_bundle()) == hashes(bundle) and self._exact_source_identity() == sources)
        except Exception as exc:
            error = {'type':type(exc).__name__,'reason':str(exc)}
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            self._binding_owner(token)
            try:
                require(self._exact_source_identity() == sources)
                self._require_usable_dependencies(package['id'])
            except Exception as exc:
                error = {'type':type(exc).__name__,'reason':str(exc)}
            record = self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'operations','source_refs':[package['id']],'exposure':[package['id']],
                'authority':AUTHORITY,'body':{'schema':'exact-reference-certificate/2','profile':runtime.PROFILE,
                    'resource_contract':runtime.RESOURCE_CONTRACT,
                    'created_at':self._now(),'attempt_id':attempt,'status':'CERTIFIED' if error is None else 'CERTIFICATION_GAP',
                    'error':error,'source_package_id':package['id'],'footprint':hashes(bundle),
                    'host_sources':sources,'result':result,'scientific_readiness':False}})
            self._event('controller','bound_computation_checked',attempt_id=attempt,
                        artifact_id=record['id'],status=record['body']['status'])
        if error is None:self._exact_certificate_id = record['id']
        return record

    def _require_exact_qualification(self):
        sources = self._exact_source_identity()
        if self._exact_certificate_id is None:
            raise Denied('No owned exact runtime qualification is selected')
        certificate = self._artifact(text(self._exact_certificate_id,'exact runtime certificate'))
        body = certificate['body']
        require(certificate['creator'] == certificate['origin'] == 'controller'
            and certificate['data_class'] == 'operations' and certificate['authority'] == AUTHORITY
            and type(body) is dict and body.get('schema') == 'exact-reference-certificate/2'
            and body.get('resource_contract') == runtime.RESOURCE_CONTRACT
            and body.get('profile') == runtime.PROFILE and body.get('status') == 'CERTIFIED'
            and body.get('scientific_readiness') is False, 'An owned exact implementation certificate is required')
        self._require_usable_dependencies(certificate['id'])
        bundle = self._exact_package(body['source_package_id'])
        result = body['result']
        require(type(result) is dict and result.get('mode') == 'certify'
            and result.get('request_hash') == digest({'profile':runtime.PROFILE})
            and body['footprint'] == hashes(bundle) == hashes(runtime.read_bundle())
            and body.get('host_sources') == sources and result.get('footprint') == body['footprint']
            and canonical(result.get('result')) == canonical(_expected_result())
            and _environment_current(result.get('environment')))
        return certificate,bundle
