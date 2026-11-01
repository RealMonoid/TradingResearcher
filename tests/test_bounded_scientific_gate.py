"""D089 boundary: descriptive intervals cannot enter scalar scientific plans.

These focused _plan_inputs tests stop at metadata/blob tripwires. They do not
fabricate an issued scientific plan or access any observations. Genuine bounded
artifact construction is separately exercised by test_bounded_binding.py.
"""
from copy import deepcopy
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from trading_researcher.errors import Denied
from trading_researcher.evaluation_plans import EvaluationPlans


class NextStageReached(Exception):
    pass


def inputs(bounded_target=False, bounded_diagnostic=False):
    compiled = {
        'id': 'compiled', 'creator': 'controller', 'origin': 'controller',
        'data_class': 'development', 'exposure': [],
        'body': {'schema': 'compiled-hypothesis/1', 'status': 'COMPILED',
                 'profile': 'bound-reference/2' if bounded_target else 'bound-reference/1',
                 'data_snapshot_id': 'snapshot', 'dependency_arguments': {},
                 'compilation': {'request': {
                     'schema': 'bounded-reference-case-request/1' if bounded_target else 'reference-case-request/1'}}},
    }
    descriptor = {'sha256': 'a' * 64, 'size': 1}
    diagnostic = {
        'id': 'diagnostic', 'creator': 'controller', 'origin': 'controller',
        'data_class': 'development', 'exposure': [], 'blob_refs': [descriptor['sha256']],
        'body': {'schema': 'reference-execution/1', 'status': 'DESCRIPTIVE_EXECUTION',
                 'profile': 'bound-reference/2' if bounded_diagnostic else 'bound-reference/1',
                 'data_snapshot_id': 'snapshot',
                 'case_format': 'bounded-reference-cases-jsonl/1' if bounded_diagnostic else 'reference-cases-jsonl/1',
                 'result': {'case_blob': descriptor, 'report': {
                     'schema': 'bounded-reference-cases/1' if bounded_diagnostic else 'reference-cases/1'}}},
    }
    records = {'compiled': compiled, 'diagnostic': diagnostic}
    snapshot = {'id': 'snapshot', 'data_class': 'development',
                'body': {'manifest': {'partition': 'development'}}}
    host = SimpleNamespace(
        _artifact=lambda identity: deepcopy(records[identity]),
        _require_usable_dependencies=Mock(),
        _data_snapshot=Mock(return_value=snapshot),
        _blob_path=Mock(side_effect=NextStageReached('Legacy diagnostic blob access reached')),
    )
    request = {'compiled_id': 'compiled', 'primary_count': 1,
               'dependence': {'development_refs': ['diagnostic']}}
    return host, request


class BoundedScientificGateTests(unittest.TestCase):
    def test_bounded_target_is_denied_before_snapshot_or_diagnostic_access(self):
        host, request = inputs(bounded_target=True, bounded_diagnostic=True)
        host._data_snapshot.side_effect = NextStageReached('Snapshot access reached')
        with self.assertRaises(Denied):
            EvaluationPlans._plan_inputs(host, {}, request)
        host._data_snapshot.assert_not_called()
        host._blob_path.assert_not_called()

    def test_bounded_diagnostic_is_denied_before_blob_access_for_scalar_target(self):
        host, request = inputs(bounded_diagnostic=True)
        with self.assertRaises(Denied):
            EvaluationPlans._plan_inputs(host, {}, request)
        host._blob_path.assert_not_called()

    def test_legacy_scalar_target_and_diagnostic_keep_existing_admission_route(self):
        host, request = inputs()
        with self.assertRaises(NextStageReached):
            EvaluationPlans._plan_inputs(host, {}, request)
        host._data_snapshot.assert_called_once_with('snapshot')
        host._blob_path.assert_called_once_with('a' * 64)


if __name__ == '__main__':
    unittest.main()
