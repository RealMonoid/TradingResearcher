"""Original-specific oracle rejection and isolated synthetic qualification."""
from copy import deepcopy
import tempfile
import unittest

from trading_researcher.codec import Invalid
from trading_researcher.paired_composition import qualify, audit
from trading_researcher.paired_runtime import read_bundle,run_child,compile_payload
from trading_researcher.paired_development import materialize_paired
from test_paired_runtime import payload
from test_paired_development_adversarial import boolean, spread


class CompositionTests(unittest.TestCase):
    def test_full_original_probes_in_separate_retained_process(self):
        inputs,_=payload()
        with tempfile.TemporaryDirectory() as directory:
            result=run_child(read_bundle(),'composition',inputs,directory)['result']
        self.assertEqual(result['scenario_count'],91)
        self.assertEqual(result['checked_cases'],1092)

    def test_different_condition_and_shifted_outcome_do_not_certify(self):
        for kind in ('condition','outcome'):
            inputs,_=payload()
            if kind=='condition':inputs['candidate']['condition_ast']['expression']=boolean(False)
            else:inputs['candidate']['outcome']['program']['expression']=spread(2,5)
            with self.subTest(kind=kind),self.assertRaises(Invalid):
                qualify(inputs)

    def test_actual_case_audit_detects_missing_and_changed_results(self):
        inputs,rows=payload()
        request=compile_payload(inputs)['request']
        report=materialize_paired(request,inputs['catalog'],rows,inputs['feature_definitions'])
        self.assertEqual(audit(inputs,rows,report['cases'])['checked_cases'],8)
        with self.assertRaises(Invalid):audit(inputs,rows,report['cases'][:-1])
        changed=deepcopy(report['cases'])
        changed[2]['condition']=False
        with self.assertRaises(Invalid):audit(inputs,rows,changed)


if __name__=='__main__':unittest.main()
