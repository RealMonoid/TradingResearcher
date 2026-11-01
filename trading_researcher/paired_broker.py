"""Explicit D094 controller entry point; default Broker remains unchanged."""
import hashlib
from pathlib import Path
import tempfile

from .binding import require, hashes
from .codec import Invalid, canonical, digest, text
from .errors import Denied
from .certification import _environment_current
from .feedback_budget_broker import FeedbackBudgetBroker
from .paired_research import PairedResearch
from .paired_computation import PairedComputation
from .paired_revocations import PairedRevocations
from .paired_development import CONTRACT, PROFILE
from . import paired_budget, paired_runtime
from . import paired_correction_budget

ROOT=Path(__file__).resolve().parents[1]
TEST_SHA256='00fb8dd938d6400a7fd543bff36509da86aa2ca023f99a01bc2fe29fddaa8ff4'
TEST_COUNT=19
QUALIFICATION_AUTHORITY='paired_implementation_conformance_only'
HOST_FILES=('trading_researcher/paired_broker.py','trading_researcher/paired_research.py',
    'trading_researcher/paired_formalization.py','trading_researcher/paired_budget.py',
    'trading_researcher/epoch_budget_dispatch.py','trading_researcher/controller_providers.py',
    'trading_researcher/paired_computation.py','trading_researcher/paired_revocations.py',
    'trading_researcher/paired_correction_budget.py','docs/architecture/24_PAIRED_FORMAT_CORRECTION.md')


class PairedBroker(PairedRevocations,PairedComputation,PairedResearch,FeedbackBudgetBroker):
    PAIRED_RUNTIME=True

    def __init__(self,*args,paired_certificate_id=None,**kwargs):
        self._paired_certificate_id=paired_certificate_id
        super().__init__(*args,**kwargs)
        self._paired_loaded_sources=self._paired_source_identity()

    def _paired_source_identity(self):
        result={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
                for name in sorted(set(paired_runtime.FILES)|set(HOST_FILES))}
        if hasattr(self,'_paired_loaded_sources'):
            require(result==self._paired_loaded_sources,'Paired installed source changed; restart and requalify')
        return result

    def _research_spec_check(self,spec):
        super()._research_spec_check(spec)
        if 'research_epoch_id' not in spec:
            return
        epoch=self._epoch(spec['research_epoch_id'])
        paired=spec.get('research_inputs',{}).get('paired_contract')==CONTRACT
        if epoch['request'].get('budget_overlay')==paired_budget.POLICY:
            paired_budget.validate_job(self,epoch,spec)
        elif epoch['request'].get('budget_overlay')==paired_correction_budget.POLICY:
            paired_correction_budget.validate_job(self,epoch,spec)
        elif paired and epoch['request']['profile']['mode']=='live':
            raise Denied('Live paired research requires its one-use approved continuation')

    def _add_source(self,actor,body,data_class,exposure=None):
        if type(body) is dict and str(body.get('schema','')).startswith(('paired-source-package/',
                'paired-reference-certificate/','paired-compiled-hypothesis/','paired-reference-execution/',
                'paired-composition-certificate/')):
            raise Denied('Paired host records cannot be supplied as arbitrary sources')
        return super()._add_source(actor,body,data_class,exposure)

    def _paired_retain_package(self,bundle):
        require(set(bundle)==set(paired_runtime.FILES) and sum(map(len,bundle.values()))<=16*1024*1024)
        files={name:self._stage_blob_bytes(raw) for name,raw in sorted(bundle.items())}
        with self._transaction():
            for descriptor in files.values():
                self._register_blob(descriptor)
            return self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'operations','source_refs':[],'exposure':[],
                'blob_refs':sorted({item['sha256'] for item in files.values()}),
                'authority':'retained_source_not_certified','body':{'schema':'paired-source-package/1',
                    'profile':PROFILE,'created_at':self._now(),'files':files,'footprint':hashes(bundle),
                    'bootstrap_sha256':hashlib.sha256(paired_runtime.BOOTSTRAP.encode()).hexdigest()}})

    def _paired_package(self,identity):
        item=self._artifact(text(identity,'paired source package'))
        body=item['body']
        require(item['creator']==item['origin']=='controller' and item['authority']=='retained_source_not_certified'
            and body.get('schema')=='paired-source-package/1' and body.get('profile')==PROFILE
            and set(body.get('files',{}))==set(paired_runtime.FILES))
        self._require_usable_dependencies(identity)
        require(body['bootstrap_sha256']==hashlib.sha256(paired_runtime.BOOTSTRAP.encode()).hexdigest())
        bundle={}
        for name,descriptor in body['files'].items():
            raw=self._read_blob_bytes(descriptor['sha256'])
            require(len(raw)==descriptor['size'])
            bundle[name]=raw
        require(sum(map(len,bundle.values()))<=16*1024*1024 and hashes(bundle)==body['footprint']
            and set(item['blob_refs'])=={value['sha256'] for value in body['files'].values()})
        return bundle

    def certify_paired(self,token):
        with self._mutex:
            self._binding_owner(token)
            self._paired_source_identity()
        bundle=paired_runtime.read_bundle()
        require(hashlib.sha256(bundle[paired_runtime.TEST]).hexdigest()==TEST_SHA256,
                'Independent paired expectations changed')
        package=self._paired_retain_package(bundle)
        attempt=self._bound_start('paired_certification',package['id'])
        result,error=None,None
        try:
            with tempfile.TemporaryDirectory(prefix='trf-paired-cert-') as directory:
                result=paired_runtime.run_child(bundle,'certify',{'profile':PROFILE},directory)
            require(result['result']=={'schema':'paired-conformance-result/1','profile':PROFILE,
                'tests':TEST_COUNT,'failures':0,'errors':0,'skipped':0,'scientific_readiness':False})
            require(hashes(paired_runtime.read_bundle())==hashes(bundle))
        except Exception as exc:
            error={'type':type(exc).__name__,'reason':str(exc)}
        except BaseException:
            self._bound_interrupted(attempt)
            raise
        with self._transaction():
            self._binding_owner(token)
            self._paired_source_identity()
            self._require_usable_dependencies(package['id'])
            record=self._save_artifact({'version':'local-artifact/1','creator':'controller','origin':'controller',
                'data_class':'operations','source_refs':[package['id']],'exposure':[package['id']],
                'authority':QUALIFICATION_AUTHORITY,'body':{'schema':'paired-reference-certificate/1',
                    'profile':PROFILE,'created_at':self._now(),'attempt_id':attempt,
                    'status':'CERTIFIED' if error is None else 'CERTIFICATION_GAP','error':error,
                    'source_package_id':package['id'],'footprint':hashes(bundle),'result':result,
                    'scientific_readiness':False}})
            self._event('controller','bound_computation_checked',attempt_id=attempt,artifact_id=record['id'],status=record['body']['status'])
        if error is None:
            self._paired_certificate_id=record['id']
        return record

    def _paired_require_qualification(self):
        self._paired_source_identity()
        if self._paired_certificate_id is None:
            raise Denied('The paired interpreter has no selected owned qualification')
        certificate=self._artifact(self._paired_certificate_id)
        body=certificate['body']
        require(certificate['creator']==certificate['origin']=='controller'
            and certificate['authority']==QUALIFICATION_AUTHORITY
            and body.get('schema')=='paired-reference-certificate/1' and body.get('profile')==PROFILE
            and body.get('status')=='CERTIFIED' and body.get('scientific_readiness') is False)
        self._require_usable_dependencies(certificate['id'])
        bundle=self._paired_package(body['source_package_id'])
        result=body['result']
        require(body['footprint']==hashes(bundle)==hashes(paired_runtime.read_bundle())
            and body['footprint'][paired_runtime.TEST]==TEST_SHA256
            and result['footprint']==body['footprint'] and _environment_current(result['environment'])
            and result['result']=={'schema':'paired-conformance-result/1','profile':PROFILE,
                'tests':TEST_COUNT,'failures':0,'errors':0,'skipped':0,'scientific_readiness':False})
        return certificate,bundle
