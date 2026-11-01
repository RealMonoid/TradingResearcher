"""D098 resource-role version; no provider, budget or production admission."""
from copy import deepcopy
import hashlib
from pathlib import Path

from . import exact_profiles as legacy, exact_runtime_v2 as runtime
from .auxiliary import reporting_contract, request_for, require
from .codec import canonical, digest, text
from .exact_research import contract_packet

ROOT=Path(__file__).resolve().parents[1]
OWNER='docs/architecture/27_EXACT_COMPUTATION_RESOURCES.md'
LEGACY_SOURCE_SHA256='2870ca08252a89a3913ceaf180f11ec5a051ced04aea7f203ac4098ebc477c88'
VERSION='faithful-exact-formalization/5'
SCHEMA='exact-resource-role-profile-construction/2'
RESOURCE_CONTRACT=runtime.RESOURCE_CONTRACT


def resource_packet():
    # Reuse the qualified retained source reader and its exact approved pin.
    # Use those checked bytes directly, without a second filesystem read.
    raw=runtime.read_bundle()[OWNER]
    return {'schema':RESOURCE_CONTRACT,
        'documents':[{'path':OWNER,'sha256':hashlib.sha256(raw).hexdigest(),'text':raw.decode('utf-8')}],
        'per_child_primitive_steps':runtime.MAX_STEPS,
        'aggregate_primitive_steps':runtime.AGGREGATE_STEPS,'shared_seconds':runtime.MAX_SECONDS}


def _contracts():
    return {**contract_packet(),**reporting_contract({'reporting_contract':'case-diagnostics/2'}),
        'resource_contract':resource_packet()}


def build(base,review):
    require(hashlib.sha256((ROOT/'trading_researcher/exact_profiles.py').read_bytes()).hexdigest()
        ==LEGACY_SOURCE_SHA256,'The qualified legacy role constructor changed')
    previous=legacy.build(base,review)
    profile=deepcopy(previous['formalization_profile'])
    require(profile['prompt'].count('10000000')==1,'Expected exactly one legacy primitive allowance')
    prompt=text(profile['prompt'].replace('10000000','20000000',1),'complete resource formalizer prompt')
    profile.update(prompt=prompt,prompt_version=VERSION)
    legacy._profile(profile)
    contracts=_contracts()
    return {**deepcopy(previous),'schema':SCHEMA,'formalization_profile':profile,
        'prior_construction_sha256':digest(previous),
        'prior_formalizer_prompt_sha256':previous['formalizer_prompt_sha256'],
        'formalizer_prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
        'contracts_sha256':digest(contracts),'resource_contract':deepcopy(contracts['resource_contract']),
        'prompt_characters':len(prompt),'resource_limit_change':True,
        'resource_change_basis':'D098; separately selected exact-computation-resources/2.0 only',
        'configuration_freshness':'NOT_CHECKED','native_admission':False,
        'model_behavior_verified':False,'scientific_readiness':False}


def _request(construction,packet,schema,role):
    require(type(construction) is dict and {'base_profile','review_profile'}<=set(construction),
        'Complete resource-role construction required')
    require(canonical(construction)==canonical(build(construction['base_profile'],construction['review_profile'])),
        'Modified or stale resource-role construction')
    require(type(packet) is dict and packet.get('schema')==schema and 'paired_contract' not in packet,
        'Correct scalar auxiliary packet required')
    inputs=packet.get('inputs')
    require(type(inputs) is dict and inputs.get('resource_contract')==RESOURCE_CONTRACT
        and inputs.get('expression_contract')=='bounded-exact-compositions/1.0'
        and inputs.get('reporting_contract')=='case-diagnostics/2',
        'Explicit matching mathematical/reporting/resource selectors required')
    require(all(canonical(packet.get(key))==canonical(value) for key,value in _contracts().items()),
        'Complete current mathematical/reporting/resource owner bytes required')
    return request_for({'research_call_profile':construction[role]},packet)


def request_candidate(construction,packet):
    return _request(construction,packet,'formalization-input/1','formalization_profile')


def review_request_candidate(construction,packet):
    return _request(construction,packet,'semantic-review-input/1','review_profile')
