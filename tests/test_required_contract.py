"""The corrected population needs an exact handoff and cannot enter inference."""
from copy import deepcopy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from trading_researcher.auxiliary import AuxiliaryResearch
from trading_researcher.codec import Invalid
from trading_researcher.errors import Denied
from trading_researcher.evaluation_plans import EvaluationPlans
from trading_researcher.memory import SCHEMA as MEMORY
from test_bounded_auxiliary_contract import review_inputs
from test_bounded_scientific_gate import inputs


ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = 'trading_researcher/REQUIRED_INPUTS.md'
HASH = '2a851e4e24804c8623f4e486e3ed6e8c502753bf7b51da035a454e0b3c2e2f9c'
VERSION = 'case-diagnostics/2'


def review():
    host, spec, _ = review_inputs()
    original = host._job
    def job(identity):
        value = original(identity)
        value['spec']['research_inputs'] = {'reporting_contract': VERSION}
        return value
    host._job = job
    spec['research_inputs']['reporting_contract'] = VERSION
    return host, spec


class RequiredContractTests(unittest.TestCase):
    def test_formalizer_and_reviewer_receive_identical_pinned_meaning(self):
        host, spec = review()
        reviewer = AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)['reporting_contract']
        records = {'idea': {'id': 'idea', 'body': {'schema': MEMORY, 'kind': 'idea'}},
                   'catalog': {'id': 'catalog', 'body': {'schema': 'feature-catalog/1', 'features': {}}}}
        host = SimpleNamespace(_artifact=lambda identity: deepcopy(records[identity]),
            _context=lambda identity: {'id': 'context', 'role': 'formalizer', 'artifact_ids': ['idea', 'catalog']})
        spec = {'kind': 'formalization/v1', 'research_epoch_id': 'epoch', 'context_id': 'context',
            'allowed_workers': ['formalizer'], 'research_inputs': {'idea_id': 'idea', 'catalog_id': 'catalog',
                'definition_ids': [], 'reporting_contract': VERSION}}
        formalizer = AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)['reporting_contract']
        raw = (ROOT / DOCUMENT).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), HASH)
        self.assertEqual(formalizer, {'schema': VERSION, 'path': DOCUMENT, 'sha256': HASH, 'text': raw.decode('utf-8')})
        self.assertEqual(reviewer, formalizer)

    def test_review_cannot_downgrade_omit_or_add_the_contract(self):
        for version in (None, 'case-diagnostics/1'):
            host, spec = review()
            if version is None:
                del spec['research_inputs']['reporting_contract']
            else:
                spec['research_inputs']['reporting_contract'] = version
            with self.subTest(version=version), self.assertRaises(Invalid):
                AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)
        host, spec, _ = review_inputs()
        spec['research_inputs']['reporting_contract'] = VERSION
        with self.assertRaises(Invalid):
            AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)

    def test_missing_or_changed_new_source_fails_closed(self):
        original = Path.read_bytes
        for missing in (False, True):
            host, spec = review()
            def changed(path):
                if path.resolve() == (ROOT / DOCUMENT).resolve():
                    if missing:
                        raise OSError('Synthetic missing required-input source')
                    return original(path) + b'changed'
                return original(path)
            with self.subTest(missing=missing), patch.object(Path, 'read_bytes', changed), self.assertRaises(Invalid):
                AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)

    def test_new_target_is_denied_before_any_snapshot_or_diagnostic_access(self):
        host, request = inputs(bounded_target=True)
        original = host._artifact
        def artifact(identity):
            value = original(identity)
            if identity == 'compiled':
                value['body']['profile'] = 'bound-reference/4'
            return value
        host._artifact = artifact
        with self.assertRaises(Denied):
            EvaluationPlans._plan_inputs(host, {}, request)
        host._data_snapshot.assert_not_called()
        host._blob_path.assert_not_called()

    def test_both_new_diagnostic_schemas_are_denied_before_blob_access(self):
        for schema in ('required-input-bounded-reference-cases/1', 'diagnostic-required-input-bounded-reference-cases/1'):
            host, request = inputs(bounded_diagnostic=True)
            original = host._artifact
            def artifact(identity):
                value = original(identity)
                if identity == 'diagnostic':
                    value['body']['profile'] = 'bound-reference/4'
                    value['body']['result']['report']['schema'] = schema
                return value
            host._artifact = artifact
            with self.subTest(schema=schema), self.assertRaises(Denied):
                EvaluationPlans._plan_inputs(host, {}, request)
            host._blob_path.assert_not_called()


if __name__ == '__main__':
    unittest.main()
