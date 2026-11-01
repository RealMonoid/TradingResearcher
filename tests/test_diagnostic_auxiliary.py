"""An optional reporting contract must survive the exact formalization/review handoff."""
from copy import deepcopy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from trading_researcher.auxiliary import AuxiliaryResearch
from trading_researcher.codec import Invalid
from trading_researcher.memory import SCHEMA as MEMORY
from test_bounded_auxiliary_contract import review_inputs

ROOT = Path(__file__).resolve().parents[1]
PATH = 'trading_researcher/CASE_DIAGNOSTICS.md'
HASH = '54917962e900cc637cbe8e78b193f82842929078d65ca5e243f74a7dc855eed5'


class DiagnosticAuxiliaryTests(unittest.TestCase):
    def review(self):
        host, spec, _ = review_inputs()
        old = host._job
        def job(identity):
            value = old(identity)
            value['spec']['research_inputs'] = {'reporting_contract': 'case-diagnostics/1'}
            return value
        host._job = job
        spec['research_inputs']['reporting_contract'] = 'case-diagnostics/1'
        return host, spec

    def assert_contract(self, packet):
        raw = (ROOT/PATH).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), HASH)
        self.assertEqual(packet['reporting_contract'],
            {'schema': 'case-diagnostics/1', 'path': PATH, 'sha256': HASH, 'text': raw.decode('utf-8')})

    def test_explicit_review_receives_exact_reporting_source(self):
        host, spec = self.review()
        self.assert_contract(AuxiliaryResearch._auxiliary_packet_for_spec(host, spec))

    def test_review_cannot_omit_or_add_a_reporting_contract(self):
        host, spec = self.review()
        del spec['research_inputs']['reporting_contract']
        with self.assertRaises(Invalid):
            AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)
        host, spec, _ = review_inputs()
        spec['research_inputs']['reporting_contract'] = 'case-diagnostics/1'
        with self.assertRaises(Invalid):
            AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)

    def test_formalizer_and_reviewer_get_the_same_versioned_contract(self):
        records = {'idea': {'id': 'idea', 'body': {'schema': MEMORY, 'kind': 'idea'}},
                   'catalog': {'id': 'catalog', 'body': {'schema': 'feature-catalog/1', 'features': {}}}}
        host = SimpleNamespace(_artifact=lambda key: deepcopy(records[key]),
            _context=lambda key: {'id': 'context', 'role': 'formalizer', 'artifact_ids': ['idea', 'catalog']})
        spec = {'kind': 'formalization/v1', 'research_epoch_id': 'epoch', 'context_id': 'context',
            'allowed_workers': ['formalizer'], 'research_inputs': {'idea_id': 'idea', 'catalog_id': 'catalog',
                'definition_ids': [], 'reporting_contract': 'case-diagnostics/1'}}
        self.assert_contract(AuxiliaryResearch._auxiliary_packet_for_spec(host, spec))

    def test_unknown_missing_or_changed_reporting_source_fails_closed(self):
        host, spec = self.review()
        spec['research_inputs']['reporting_contract'] = 'arbitrary/path'
        with self.assertRaises(Invalid):
            AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)
        host, spec = self.review()
        original = Path.read_bytes
        for missing in (False, True):
            def changed(path):
                if path.resolve() == (ROOT/PATH).resolve():
                    if missing:raise OSError('Synthetic missing reporting source')
                    return original(path)+b'changed'
                return original(path)
            with patch.object(Path, 'read_bytes', changed), self.assertRaises(Invalid):
                AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)
