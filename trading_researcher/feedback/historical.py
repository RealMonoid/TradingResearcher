"""Retained raw conformance for explicitly bound, already released feedback.

No feature-status override: the sole substituted check is installed-package
currency inside a private, read-only historical evidence view.
"""
from contextlib import closing, contextmanager
import hashlib
import os
from pathlib import Path
import sqlite3
import tempfile

from ..binding import require
from ..certification import _environment_current
from ..codec import Invalid, canonical, decode, digest, integer, strings, text
from ..errors import Conflict, Denied
from ..epoch_budget import AGGREGATE_CAP
from ..exact_execution_v2 import ExactExecutionBrokerV2
from ..features import binding, footprint, read_bundle, run_validation, validate_report, valid_names
from ..paired_computation import PairedComputation
from ..paired_development import CONTRACT
from ..paired_formalization import SCHEMA as FORMALIZATION, validate_record
from ..openai_provider import MODEL
from ..revocations import SCHEMA as REVOCATION, AUTHORITY as REVOCATION_AUTHORITY
from .. import review_continuation as legacy_review
from . import paired, breakout

ROOT = Path(__file__).resolve().parents[2]
FILE = 'trading_researcher/feedback/historical.py'
LOADED = hashlib.sha256((ROOT/FILE).read_bytes()).hexdigest()
SCHEMA = 'historical-feedback-qualification/1'
PROFILE = 'historical-raw-feedback-conformance/1'
AUTHORITY = 'historical_feedback_technical_conformance_only'
FIELDS = {'schema','profile','created_at','attempt_id','status','error','bindings',
          'feature_certificate_id','installed_package_id','installed_footprint',
          'host_sources','adapter_source','report','scientific_readiness'}


class HistoricalFeedbackBroker(ExactExecutionBrokerV2):
    """Opt-in controller entry; frozen brokers and their certificates are intact."""

    def __init__(self, *args, historical_qualification_ids=(), **kwargs):
        self._historical_qualification_ids = tuple(strings(list(historical_qualification_ids), 'historical qualifications'))
        require(len(self._historical_qualification_ids) <= 32)
        super().__init__(*args, **kwargs)

    def _execution_sources(self):
        current = hashlib.sha256((ROOT/FILE).read_bytes()).hexdigest()
        require(current == LOADED, 'Historical adapter changed; restart and independently requalify')
        return {**super()._execution_sources(), FILE: current}

    def call(self, token, op, **args):
        if op == 'qualify_historical_feedback':
            require(set(args) == {'release_ids'})
            return self.qualify_historical_feedback(token, **args)
        if op == 'historical_feedback_status':
            require(set(args) == {'qualification_id'})
            with self._mutex:
                self._binding_owner(token)
                item = self._historical_qualification(args['qualification_id'])
                return {'qualification_id': item['id'], 'status': 'CURRENT',
                        'feature_status_override': False, 'scientific_readiness': False}
        return super().call(token, op, **args)

    def _add_source(self, actor, body, data_class, exposure=None):
        if type(body) is dict and str(body.get('schema','')).startswith('historical-feedback-qualification/'):
            raise Denied('Historical qualifications require owned conformance')
        return super()._add_source(actor, body, data_class, exposure)

    def _put_artifact(self, actor, lease, body, source_refs):
        if type(body) is dict and str(body.get('schema','')).startswith('historical-feedback-qualification/'):
            raise Denied('Historical qualifications require owned conformance')
        return super()._put_artifact(actor, lease, body, source_refs)

    def _historical_bindings(self, release_ids):
        ids = strings(release_ids, 'historical releases')
        require(1 <= len(ids) <= 32 and len(set(ids)) == len(ids), 'One through 32 distinct releases required')
        result = []
        for identity in sorted(ids):
            item = self._artifact(identity)
            namespace = {paired.RELEASE: paired, breakout.RELEASE: breakout}.get(item['body'].get('schema'))
            require(namespace is not None, 'Only existing paired/breakout releases are supported')
            grant = namespace._owned(self, identity, namespace.RELEASE)
            self._deny_final_calibration_ancestry(grant)
            self._require_usable_dependencies(identity)
            manifest = namespace._owned(self, grant['body']['manifest_id'], namespace.MANIFEST)
            execution = self._artifact(manifest['body']['request']['execution_id'])
            compiled = self._artifact(execution['body']['compiled_id'])
            require(execution['data_class'] == compiled['data_class'] == 'development')
            result.append({'release_id': identity, 'schema': namespace.RELEASE,
                'compiled_id': compiled['id'], 'formalization_id': compiled['body']['formalization_id'],
                'feature_certificate_id': compiled['body']['feature_certificate_id'],
                'data_snapshot_id': compiled['body']['data_snapshot_id']})
        require(len({(x['feature_certificate_id'],x['data_snapshot_id']) for x in result}) == 1,
                'One exact original raw certificate and snapshot required')
        return result

    def _historical_raw(self, bindings):
        first = bindings[0]
        certificate = self._artifact(first['feature_certificate_id'])
        snapshot = self._artifact(first['data_snapshot_id'])
        # Before retained code, raw blobs or row loaders.
        require(snapshot['data_class'] == 'development'
            and snapshot['body'].get('schema') == 'data-snapshot/1'
            and snapshot['body'].get('manifest',{}).get('partition') == 'development',
            'Historical qualification cannot read protected inputs')
        self._deny_final_calibration_ancestry(snapshot)
        status = self._feature_certificate_status(None, certificate['id'], data_snapshot_id=snapshot['id'])
        require(status['status'] in ('CURRENT','STALE'), 'Original raw evidence is not intact')
        retained = self._load_feature_package(certificate['body']['source_package_id'])
        current = read_bundle()
        require(valid_names(current) and sum(map(len,current.values())) <= 16*1024*1024)
        require(set(retained) <= set(current) and all(current[name] == raw for name,raw in retained.items()),
                'Historical qualification permits addition-only source growth')
        require(_environment_current(certificate['body']['environment']))
        return certificate, retained, current, binding(self, snapshot['id'])

    def _historical_qualification(self, identity):
        item = self._artifact(text(identity, 'historical qualification'))
        body = item['body']
        require(item['creator'] == item['origin'] == 'controller' and item['data_class'] == 'operations'
            and item['authority'] == AUTHORITY and type(body) is dict and set(body) == FIELDS
            and body['schema'] == SCHEMA and body['profile'] == PROFILE
            and body['status'] == 'CERTIFIED' and body['error'] is None
            and body['scientific_readiness'] is False, 'Owned complete historical qualification required')
        self._require_usable_dependencies(identity)
        bindings = self._historical_bindings([x['release_id'] for x in body['bindings']])
        require(bindings == body['bindings'])
        certificate, retained, current, original = self._historical_raw(bindings)
        require(certificate['id'] == body['feature_certificate_id']
            and footprint(current) == body['installed_footprint']
            and footprint(self._load_feature_package(body['installed_package_id'])) == footprint(current)
            and self._execution_sources() == body['host_sources'])
        validate_report(body['report'], original, retained)
        require(body['report']['definitions'] == self._artifact(certificate['body']['definitions_id'])['body']['definitions'])
        descriptor = body['adapter_source']
        require(type(descriptor) is dict and set(descriptor) == {'sha256','size'}
            and item['blob_refs'] == [descriptor['sha256']])
        raw = self._read_blob_bytes(descriptor['sha256'])
        require(len(raw) == descriptor['size'] and raw == (ROOT/FILE).read_bytes()
            and hashlib.sha256(raw).hexdigest() == LOADED)
        require(item['source_refs'] == sorted({body['feature_certificate_id'], body['installed_package_id'],
            *[x['release_id'] for x in bindings]}))
        return item

    @contextmanager
    def _historical_view(self, provisional=None):
        bindings = []
        if provisional is None:
            for identity in self._historical_qualification_ids:
                bindings.extend(self._historical_qualification(identity)['body']['bindings'])
        else:
            # Only the owned qualification operation supplies this local value,
            # after full independent replay and before any successful artifact.
            bindings = provisional
        view = object.__new__(_HistoricalEvidenceView)
        view.__dict__ = self.__dict__.copy()
        view.__dict__.pop('admin_token', None)
        view._provider_routes = {}
        route = self._provider_routes.get(MODEL)
        config = route.get('config') if type(route) is dict else None
        view._historical_financial_route = ({'provider':route.get('provider'),
            'budget_file':route.get('budget_file'),'test_budget_nano':config.get('test_budget_nano')}
            if type(config) is dict else None)
        view._historical_allowed = {x['compiled_id']: x for x in bindings}
        view._historical_active_pair = None
        view._db = sqlite3.connect((self.directory/'registry.sqlite3').as_uri()+'?mode=ro', uri=True,
                                  isolation_level=None, check_same_thread=False)
        view._db.row_factory = sqlite3.Row
        view._db.execute('PRAGMA query_only=ON')
        try:
            yield view
        finally:
            view._db.close()

    def _check_feedback_context(self, context):
        if not self._historical_qualification_ids:
            return super()._check_feedback_context(context)
        with self._historical_view() as view:
            return ExactExecutionBrokerV2._check_feedback_context(view, context)

    def _released_feature_evidence(self, artifact, epoch, research_time):
        if not self._historical_qualification_ids:
            return super()._released_feature_evidence(artifact, epoch, research_time)
        with self._historical_view() as view:
            return ExactExecutionBrokerV2._released_feature_evidence(view, artifact, epoch, research_time)

    def qualify_historical_feedback(self, token, *, release_ids):
        with self._mutex:
            self._binding_owner(token)
            bindings = self._historical_bindings(release_ids)
            certificate, retained, current, original = self._historical_raw(bindings)
            installed = footprint(current)
            sources = self._execution_sources()
        package_id = self._retain_feature_package(current)
        adapter = self._stage_blob_bytes((ROOT/FILE).read_bytes())
        attempt = self._bound_start('historical_feedback_qualification', certificate['id'])
        report, error = None, None
        try:
            with tempfile.TemporaryDirectory(prefix='trf-historical-feedback-') as temporary:
                root = Path(temporary)
                self._backup_bundle_external(token, {'destination': str(root/'registry')})
                descriptor = os.open(root/'registry/operator.key', os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
                with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
                    stream.write(self.admin_token); stream.flush(); os.fsync(stream.fileno())
                # ONLY the original retained bundle executes in the fresh child.
                report = run_validation(retained, root/'registry', original['snapshot']['id'], root)
            validate_report(report, original, retained)
            require(report['definitions'] == self._artifact(certificate['body']['definitions_id'])['body']['definitions'])
            with self._mutex:
                require(self._historical_bindings(release_ids) == bindings)
                self._historical_raw(bindings)
                require(footprint(read_bundle()) == installed and self._execution_sources() == sources)
                with self._historical_view(provisional=bindings) as view:
                    for entry in bindings:
                        namespace = paired if entry['schema'] == paired.RELEASE else breakout
                        grant = namespace._owned(view, entry['release_id'], namespace.RELEASE)
                        namespace._check_grant(view, grant, grant['body']['target_epoch'], self._now())
        except Exception as exc:
            error = {'type':type(exc).__name__, 'reason':str(exc)}
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        try:
            canonical(report)
        except (Invalid, TypeError, ValueError) as exc:
            # Preserve the original validation failure; never coerce an invalid
            # host object into accepted numerical evidence or lose the gap.
            if error is None:
                error = {'type':type(exc).__name__, 'reason':str(exc)}
            error = {**error, 'report_retention':'NONCANONICAL_OBJECT_OMITTED'}
            report = None
        with self._transaction():
            self._binding_owner(token)
            if error is None:
                try:
                    require(self._historical_bindings(release_ids) == bindings)
                    self._historical_raw(bindings)
                    require(footprint(read_bundle()) == installed and self._execution_sources() == sources)
                    self._require_usable_dependencies(package_id)
                except Exception as exc:
                    error = {'type':type(exc).__name__, 'reason':str(exc)}
            self._register_blob(adapter)
            refs = sorted({certificate['id'],package_id,*[x['release_id'] for x in bindings]})
            exposure = sorted({*refs,*[ref for identity in refs for ref in self._artifact(identity)['exposure']]})
            item = self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'operations','authority':AUTHORITY,'source_refs':refs,'exposure':exposure,
                'blob_refs':[adapter['sha256']], 'body':{'schema':SCHEMA,'profile':PROFILE,
                    'created_at':self._now(),'attempt_id':attempt,'status':'CERTIFIED' if error is None else 'CERTIFICATION_GAP',
                    'error':error,'bindings':bindings,'feature_certificate_id':certificate['id'],
                    'installed_package_id':package_id,'installed_footprint':installed,'host_sources':sources,
                    'adapter_source':adapter,'report':report,'scientific_readiness':False}})
            self._event('controller','bound_computation_checked',attempt_id=attempt,
                        artifact_id=item['id'],status=item['body']['status'])
        # Selection is explicit caller configuration, never automatic admission.
        return item

    def _technical_dependencies(self, artifact):
        if type(artifact['body']) is dict and artifact['body'].get('schema') == SCHEMA:
            body = artifact['body']
            return [body['feature_certificate_id'],body['installed_package_id'],
                    *[entry['release_id'] for entry in body['bindings']]]
        return super()._technical_dependencies(artifact)

    def _dependency_use(self, artifact_id):
        result = super()._dependency_use(artifact_id)
        extra = []
        for record in self._revocation_records():
            selector = record['body']['selector']
            if selector.get('schema') == SCHEMA and selector.get('artifact_id') in result['checked_versions']:
                item = self._artifact(selector['artifact_id'])
                require(item['creator'] == item['origin'] == 'controller' and item['authority'] == AUTHORITY)
                extra.append({'revocation_id':record['id'],'dependency_id':record['body']['request']['dependency_id'],
                              'used_version_id':item['id']})
        if extra:
            result = {**result,'status':'INVALIDATED_BY_DEPENDENCY',
                'invalidations':sorted([*result['invalidations'],*extra],key=lambda x:(x['used_version_id'],x['revocation_id']))}
        return result

    def _revoke_dependency(self, actor, key, dependency_id, reason, evidence_refs):
        item = self._artifact(dependency_id)
        if type(item['body']) is not dict or item['body'].get('schema') != SCHEMA:
            return super()._revoke_dependency(actor,key,dependency_id,reason,evidence_refs)
        require(item['creator'] == item['origin'] == 'controller' and item['authority'] == AUTHORITY)
        request = decode(canonical({'key':text(key,'revocation key'),'dependency_id':text(dependency_id,'dependency'),
            'reason':text(reason,'defect reason'),'evidence_refs':strings(evidence_refs,'defect evidence')}))
        require(1 <= len(request['evidence_refs']) <= 32)
        for previous in self._revocation_records():
            if previous['body']['request']['key'] == key:
                if previous['body']['request'] != request:
                    raise Conflict('Revocation key already binds different evidence')
                return previous
        refs = sorted({dependency_id,*request['evidence_refs']})
        exposure = sorted({*refs,*[ref for identity in refs for ref in self._artifact(identity)['exposure']]})
        saved = self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
            'data_class':'operations','source_refs':refs,'exposure':exposure,'authority':REVOCATION_AUTHORITY,
            'body':{'schema':REVOCATION,'created_at':self._now(),'request':request,
                'selector':{'schema':SCHEMA,'artifact_id':item['id']},'affected_artifact_ids':[item['id']],
                'affected_scope':'supported_typed_bindings_at_revocation','status':'REVOKED','scientific_readiness':False,
                'qualification':'Technical historical-feedback qualification only; original result is retained.'}})
        self._event(actor['name'],'dependency_revoked',artifact_id=saved['id'],dependency_id=dependency_id)
        return saved


class _HistoricalEvidenceView(HistoricalFeedbackBroker):
    """Trusted in-process reader; not an OS sandbox or worker capability."""

    def __getattribute__(self, name):
        value = super().__getattribute__(name)
        if not name.startswith('_') and callable(value):
            raise Denied('Historical evidence view exposes no public operation')
        return value

    def _transaction(self):
        raise Denied('Historical evidence view cannot write')

    def _now(self):
        # Inherited readers need time; this does not expose a public operation.
        return integer(object.__getattribute__(self, 'clock')(), 'host time')

    def _stage_blob_bytes(self, *args, **kwargs):
        raise Denied('Historical evidence view cannot stage blobs')

    def _check_feedback_context(self, context):
        return ExactExecutionBrokerV2._check_feedback_context(self, context)

    def _released_feature_evidence(self, artifact, epoch, research_time):
        return ExactExecutionBrokerV2._released_feature_evidence(self, artifact, epoch, research_time)

    def _meaning_inventory(self, target):
        inventory, refs = super()._meaning_inventory(target)
        metadata = self._historical_financial_route
        if 'continuation_authorizations' not in inventory or metadata is None:
            return inventory, refs
        # The old meaning inspector requires a historical external fence, not
        # a usable provider. Preserve that exact inspection using only reads;
        # constructing SpendLedger would take a write transaction/create schema.
        original_epoch = self._job(target['job_id'])['spec'].get('research_epoch_id')
        entries = []
        for job in inventory['jobs']:
            if job['spec'].get('research_epoch_id') == original_epoch:
                continue
            try:
                require(metadata['provider'] == 'openai'
                    and type(metadata['test_budget_nano']) is int
                    and metadata['test_budget_nano'] == AGGREGATE_CAP,
                    'Historical inspection requires the existing host-selected USD5 ledger')
                path = Path(metadata['budget_file'])
                require(path.is_file() and not path.is_symlink(), 'Historical spend ledger is missing or unsupported')
                epoch = self._epoch(job['spec']['research_epoch_id'])
                with closing(sqlite3.connect(path.resolve().as_uri()+'?mode=ro', uri=True)) as db:
                    db.execute('PRAGMA query_only=ON')
                    db.execute('BEGIN')
                    cap = db.execute('SELECT cap FROM budget WHERE singleton=1').fetchone()
                    require(cap is not None and type(cap[0]) is int and cap[0] == AGGREGATE_CAP,
                            'Historical external budget differs from the existing cap')
                    state = legacy_review.row(self, epoch, db)
                    actual = [row[0] for row in self._db.execute(
                        'SELECT id FROM research_calls WHERE epoch_id=? ORDER BY rowid', (epoch['id'],))]
                    require(actual == [call['call_id'] for call in state['calls']],
                            'External review fence differs from retained native calls')
                # Same projection as the original inspector: administrative
                # closure stays revoked and never becomes dispatch permission.
                entry = {'job_id':job['id'],'binding':state['binding'],'calls':state['calls']}
            except (Invalid, Denied, OSError, sqlite3.Error, TypeError, KeyError, ValueError) as exc:
                entry = {'job_id':job['id'],'authorization_gap':str(exc)}
            entries.append(entry)
        return {**inventory, 'continuation_authorizations':entries}, refs

    def _paired_compiled(self, identity):
        selected = self._historical_allowed.get(identity)
        previous = self._historical_active_pair
        self._historical_active_pair = (selected['formalization_id'],selected['feature_certificate_id']) if selected else None
        try:
            # Unlisted compilations retain the complete original CURRENT-only
            # path, including when they happen to share the same form/cert pair.
            return PairedComputation._paired_compiled(self, identity)
        finally:
            self._historical_active_pair = previous

    def _paired_dependencies(self, formalization_id, feature_certificate_id):
        if (formalization_id,feature_certificate_id) != self._historical_active_pair:
            return PairedComputation._paired_dependencies(self,formalization_id,feature_certificate_id)
        # Frozen paired dependency checks, with ONLY installed-package currency
        # discharged by the fresh owned retained-source qualification above.
        target = self._artifact(text(formalization_id,'formalization identity'))
        require(target['origin'] == 'worker' and target['body'].get('schema') == FORMALIZATION,
                'Owned paired formalization required')
        job = self._job(target['job_id'])
        require(job['state'] == 'completed' and job['result_id'] == formalization_id
            and job['spec']['kind'] == 'formalization/v1'
            and job['spec'].get('research_inputs',{}).get('paired_contract') == CONTRACT)
        validate_record(target['body'],[self._artifact(ref) for ref in target['source_refs']])
        require(target['body']['assessment']['status'] == 'STRUCTURE_CHECKED')
        self._deny_final_calibration_ancestry(target)
        snapshot_id = target['body']['candidate']['test_universe']['data_snapshot_ref']
        require(snapshot_id in target['source_refs'])
        snapshot = self._artifact(snapshot_id); body = snapshot['body']
        if (snapshot['data_class'] != 'development' or body.get('schema') != 'data-snapshot/1'
                or body.get('manifest',{}).get('partition') != 'development'):
            raise Denied('Paired development cannot read protected outcomes')
        require(snapshot['creator'] == 'controller' and snapshot['origin'] == 'source'
            and body['catalog_id'] == target['body']['catalog_id'])
        certificate = self._artifact(text(feature_certificate_id,'feature certificate'))
        require(job['spec']['research_inputs'].get('feature_certificate_id') == certificate['id']
            and certificate['id'] in target['source_refs'])
        # Status remains STALE. Every other raw status is rejected unchanged.
        status = self._feature_certificate_status(None,certificate['id'],data_snapshot_id=snapshot_id)
        require(status['status'] in ('CURRENT','STALE'))
        definition = self._artifact(certificate['body']['definitions_id'])
        require(definition['id'] in target['body']['definition_ids'])
        catalog = self._artifact(body['catalog_id'])['body']['features']
        require(digest(catalog) == body['catalog_hash'] and digest(catalog) == digest({
            x['feature_ref']:{k:x[k] for k in ('type','unit')} for x in definition['body']['definitions']}))
        reference, bundle = self._paired_require_qualification()
        refs = sorted({target['id'],snapshot_id,certificate['id'],definition['id'],body['catalog_id'],reference['id']})
        for identity in (snapshot_id,certificate['id'],definition['id'],reference['id']):
            self._require_usable_dependencies(identity)
        return {'formalization':target,'snapshot':snapshot,'feature_certificate':certificate,
                'definition':definition,'catalog':catalog,'reference':reference,'bundle':bundle,'refs':refs}
