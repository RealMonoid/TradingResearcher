"""Owned shared-template family development and protected final inventories."""
from itertools import permutations

from . import family_study
from .calibration_runs import CalibrationStudies
from .evaluation_policy import require
from .study_runs import InformationStudies


class FamilyStudies(InformationStudies):
    _study_input_schema='family-study-input/1'
    _study_result_schema='family-study-attempt/1'
    _study_authority='development_joint_family_study_not_scientific_admission'

    def __init__(self,broker):self.broker=broker
    def __getattr__(self,name):return getattr(self.broker,name)

    def _study_manifest(self,assigned,profile):return family_study.make_manifest(assigned,profile)

    def _study_failed_outcome(self,manifest,world,prior=None):
        return family_study.outcome_record(manifest,world,failed=True)


class FamilyCalibrationStudies(CalibrationStudies):
    _study_input_schema='family-calibration-input/1'
    _study_result_schema='family-calibration-attempt/1'
    _study_authority='conditional_joint_family_calibration_not_scientific_admission'
    _calibration_policy=family_study
    _calibration_identity_schema='joint-family-final-identity/1'
    _calibration_scope='distinct_binary_responses_on_one_shared_development_template'
    _mixed_truth_status='OWNED_SERIES_NOT_SCIENTIFIC_ADMISSION'
    _calibration_summary_schema='joint-family-final-calibration-summary/1'
    _event_semantics='FIXED_JOINT_WORLD_UNIONS_AND_PER_RESPONSE_DETECTION'
    _calibration_qualification=('All required cohorts use complete fixed 256-world denominators and owned attempts. '
        'Shared-template stress laws do not establish heterogeneous original-claim or market-process adequacy, '
        'ideal sampling independence, information sufficiency, full-process calibration or scientific admission.')

    def _development_runner(self):return FamilyStudies(self.broker)

    def _validate_development_family(self,manifest):
        require(manifest['schema']==family_study.MANIFEST,'Complete owned family development is required')
        family_study.validate_manifest(manifest)

    def _study_failed_outcome(self,manifest,world,prior=None):
        return family_study.outcome_record(manifest,world,failed=True)

    def _calibration_identity_extra(self,manifest):
        # Responses share the same template and are exchangeable under this
        # declared law. Relabeling/permuting them must not buy fresh final draws.
        width=len(manifest['profile']['responses']);patterns=manifest['profile']['patterns']
        normalized=min(tuple(sorted(tuple(pattern[i] for i in order) for pattern in patterns))
            for order in permutations(range(width)))
        return {'family_patterns':list(map(list,normalized))}
