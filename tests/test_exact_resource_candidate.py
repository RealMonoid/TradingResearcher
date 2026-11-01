"""Inactive resource proposal: retain all old calculation/check boundaries."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from exact_mapping_support import supplied
from test_exact_runtime import history
from trading_researcher import exact_resource_candidate as candidate
from trading_researcher.codec import canonical
from trading_researcher.exact_outcomes import materialize_exact
from trading_researcher.exact_runtime import compile_payload
from trading_researcher.expressions import ExpressionGap


def request(count=55,steps=20000000):
    return {**compile_payload(supplied(count,max_steps=min(steps,10000000)))['request'],
        'schema':candidate.REQUEST,'max_steps':steps}


class ExactResourceCandidateTests(unittest.TestCase):
    def test_explicit_inactive_version_and_old_cap_preserved(self):
        proposal=request()
        self.assertEqual(candidate.ACTIVATION,'PENDING_SPECIFIC_RESOURCE_DECISION')
        with self.assertRaises(ExpressionGap):materialize_exact({**proposal,'schema':'exact-composition-case-request/1'},
            supplied()['catalog'],history())
        for limit in (True,0,20000001):
            with self.subTest(limit=limit),self.assertRaises(ExpressionGap):
                candidate.materialize({**proposal,'max_steps':limit},supplied()['catalog'],history())

    def test_plain_projection_and_full_observed_case_check_are_preserved(self):
        payload=supplied();proposal=request();rows=history()
        old=materialize_exact(compile_payload(payload)['request'],payload['catalog'],rows)
        base=candidate.materialize(proposal,payload['catalog'],rows)
        self.assertEqual(base['cases'],old['cases']);self.assertEqual(base['primitive_steps'],old['primitive_steps'])
        observed=candidate.add_diagnostics(base,payload['catalog'],rows,proposal['max_steps']-base['primitive_steps'])
        self.assertEqual(candidate.base_projection(observed),base)
        self.assertTrue(observed['diagnostics']['processing_complete'])
        self.assertEqual(observed['diagnostics']['guard_counts']['unrecognized'],0)
        before=canonical(base)
        def wrong(*args,**kwargs):
            return {**base['cases'][0],'scope':False}
        with patch.object(candidate,'_case',side_effect=wrong),self.assertRaises(ExpressionGap):
            candidate.add_diagnostics(base,payload['catalog'],rows,100000)
        self.assertEqual(canonical(base),before)

    def test_diagnostic_failure_keeps_plain_case_values_and_status(self):
        payload=supplied();base=candidate.materialize(request(),payload['catalog'],history())
        for limit in (0,1):
            stopped=candidate.add_diagnostics(base,payload['catalog'],history(),limit)
            self.assertFalse(stopped['diagnostics']['processing_complete'])
            self.assertEqual(candidate.base_projection(stopped),base)
        with patch.object(candidate,'MAX_CASE_BYTES',1):
            stopped=candidate.add_diagnostics(base,payload['catalog'],history(),100000)
        self.assertEqual(stopped['diagnostics']['processed_cases'],0)
        self.assertEqual(candidate.base_projection(stopped),base)
        self.assertTrue(base['processing_complete'])

    def test_actual_budget_and_canonical_base_binding_cannot_be_relabelled(self):
        payload=supplied();base=candidate.materialize(request(),payload['catalog'],history())
        with self.assertRaises(ExpressionGap):
            candidate.add_diagnostics(base,payload['catalog'],history(),20000000-base['primitive_steps']+1)
        observed=candidate.add_diagnostics(base,payload['catalog'],history(),100000)
        changed=deepcopy(observed);changed['cases'][0]['scope']=False
        with self.assertRaises(ExpressionGap):candidate.base_projection(changed)
        for mutate in (lambda item:item.update(primitive_steps=20000001),
                       lambda item:item.update(scientific_readiness=0),
                       lambda item:item.update(activation='ACCEPTED')):
            bad=deepcopy(base);mutate(bad)
            with self.assertRaises(ExpressionGap):candidate.contrast(bad)


if __name__=='__main__':unittest.main()
