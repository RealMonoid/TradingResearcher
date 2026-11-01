"""The new descriptive report cannot bypass the scalar scientific-plan gate."""
import unittest
from test_bounded_scientific_gate import inputs
from trading_researcher.evaluation_plans import EvaluationPlans
from trading_researcher.errors import Denied


class DiagnosticScientificGateTests(unittest.TestCase):
    def test_diagnostic_record_is_denied_before_blob_access(self):
        host, request = inputs(bounded_diagnostic=True)
        original = host._artifact
        def artifact(identity):
            value = original(identity)
            if identity == 'diagnostic':
                value['body']['profile'] = 'bound-reference/3'
                value['body']['result']['report']['schema'] = 'diagnostic-bounded-reference-cases/1'
            return value
        host._artifact = artifact
        with self.assertRaises(Denied):
            EvaluationPlans._plan_inputs(host, {}, request)
        host._blob_path.assert_not_called()
