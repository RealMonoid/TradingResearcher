"""Explicit required-input implementation of the approved retained ETH meaning."""
from copy import deepcopy

from .bounded_math import BoundedReferenceEngine
from .bounded_outcomes import CASES as OLD_CASES, bounded_contrast, legacy_request, materialize_bounded
from .case_diagnostics import _Engine, _base_hash, _stream_hash, add_diagnostics
from .expressions import gap


CONTRACT = 'required-inputs/1'
CASES = 'required-input-bounded-reference-cases/1'
DIAGNOSTICS = 'diagnostic-required-input-bounded-reference-cases/1'
CONTRAST = 'required-input-bounded-reference-contrast/1'


class RequiredInputEngine(BoundedReferenceEngine):
    """Coordinates select expressions; only feature reads require market rows."""
    def _requires_observation(self, node):
        return node.op == 'feature'

    def _traces_observation(self, node):
        return node.op == 'feature'


class _RequiredDiagnosticEngine(_Engine, RequiredInputEngine):
    pass


def materialize_required(request, catalog, rows):
    legacy_request(request)
    engine = RequiredInputEngine(catalog, rows, allow_log=True)
    if not engine.describe(request.get('outcome_program'))['feature_refs']:
        gap('LANGUAGE_GAP', 'The required-input profile needs an actual raw outcome feature')
    result = materialize_bounded(request, catalog, rows, _engine_type=RequiredInputEngine,
                                 _require_container_rows=False)
    return {**result, 'schema': CASES, 'evaluation_contract': CONTRACT}


def _numerical_projection(report):
    if (type(report) is not dict or report.get('schema') != CASES
            or report.get('evaluation_contract') != CONTRACT):
        gap('EVALUATION_GAP', 'Expected the exact required-input base version')
    return {**report, 'schema': OLD_CASES}


def required_contrast(report):
    result = bounded_contrast(_numerical_projection(report))
    if not report['processing_complete']:
        result = {**result, 'status': 'RESOURCE_STOP'}
    return {**result, 'schema': CONTRAST, 'evaluation_contract': CONTRACT}


def add_required_diagnostics(report, catalog, rows, max_steps):
    projected = _numerical_projection(report)
    result = add_diagnostics(projected, catalog, rows, max_steps,
                              _engine_type=_RequiredDiagnosticEngine, _require_container_rows=False)
    result['schema'] = DIAGNOSTICS
    result['diagnostics']['schema'] = 'case-diagnostics/2'
    result['base_report_hash'] = _base_hash(report, result['base_case_stream_sha256'])
    return result


def required_base_projection(report):
    if (type(report) is not dict or report.get('schema') != DIAGNOSTICS
            or report.get('evaluation_contract') != CONTRACT
            or report.get('diagnostics', {}).get('schema') != 'case-diagnostics/2'):
        gap('EVALUATION_GAP', 'Expected the exact required-input diagnostic version')
    base = {k: deepcopy(v) for k, v in report.items()
            if k not in ('diagnostics', 'base_report_hash', 'base_case_stream_sha256', 'cases')}
    base['schema'] = CASES
    base['cases'] = [{k: deepcopy(v) for k, v in case.items() if k != 'diagnostics'}
                     for case in report['cases']]
    checksum = _stream_hash(base['cases'])
    if (checksum != report.get('base_case_stream_sha256')
            or _base_hash(base, checksum) != report.get('base_report_hash')):
        gap('EVALUATION_GAP', 'Required-input diagnostic projection changed its base')
    return base
