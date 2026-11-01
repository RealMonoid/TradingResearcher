"""Independent pinned D089 semantics in AST2 reviewer packets, no provider calls."""
from copy import deepcopy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from trading_researcher.auxiliary import AuxiliaryResearch, request_for
from trading_researcher.codec import Invalid, canonical
from trading_researcher.meaning_reviews import PROMPT, PROTOCOL, profile


DOCUMENT = 'docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md'
DOCUMENT_HASH = '6f183599cede66f8a06b5cf01868c9db70e632b63cf683fff6c1cb1adc77100f'
PROMPT_HASH = '90ad1b1e774d554e0651b696873851c30909e10f74011f1bc28574186f5e7023'
ROOT = Path(__file__).resolve().parents[1]


def review_inputs(version='research-ast/2'):
    program = {'schema': version, 'catalog_hash': 'synthetic-catalog',
               'expression': {'op': 'literal', 'type': 'boolean', 'unit': None, 'value': True}}
    target = {
        'id': 'target', 'origin': 'worker', 'creator': 'original-formalizer', 'job_id': 'completed-job',
        'source_refs': ['idea', 'catalog'],
        'body': {'schema': 'formalization-record/1', 'idea_id': 'idea', 'catalog_id': 'catalog',
                 'authorization_snapshot': ['catalog', 'idea'],
                 'candidate': {'scope_ast': deepcopy(program), 'condition_ast': deepcopy(program),
                               'outcome': {'program': deepcopy(program)}, 'feature_refs': [],
                               'test_universe': {}}},
    }
    catalog = {'id': 'catalog', 'body': {'features': {}}}
    records = {'target': target, 'catalog': catalog}
    context = {'id': 'review-context', 'role': 'formalizer', 'artifact_ids': ['target', 'idea', 'catalog']}
    host = SimpleNamespace(
        _context=lambda identity: deepcopy(context),
        _artifact=lambda identity: deepcopy(records[identity]),
        _job=lambda identity: {'state': 'completed', 'result_id': 'target',
                              'spec': {'kind': 'formalization/v1', 'research_epoch_id': 'same-epoch'}},
    )
    spec = {'kind': 'semantic-review/v1', 'context_id': context['id'],
            'research_epoch_id': 'same-epoch', 'allowed_workers': ['independent-reviewer'],
            'research_inputs': {'formalization_id': 'target', 'definition_ids': []},
            'research_call_profile': profile({'model': 'synthetic/1', 'generation_parameters': {},
                                             'max_output_tokens': 512, 'call_timeout_seconds': 10,
                                             'max_retries': 0})}
    expected = {'schema': 'semantic-review-input/1', 'context_id': context['id'],
                'inputs': deepcopy(spec['research_inputs']), 'formalization': deepcopy(target),
                'catalog': deepcopy(catalog), 'definitions': [],
                'qualification': 'Assess meaning independently; supplied mappings are formalizer assertions. No assessment outcomes are supplied.'}
    return host, spec, expected


class BoundedAuxiliaryContractTests(unittest.TestCase):
    def test_ast2_packet_retains_exact_pinned_contract_and_binds_it_into_request(self):
        host, spec, expected = review_inputs()
        original = deepcopy(spec)
        raw = (ROOT / DOCUMENT).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), DOCUMENT_HASH)
        expected['expression_contract'] = {
            'schema': 'bounded-math/1.0', 'path': DOCUMENT,
            'sha256': DOCUMENT_HASH, 'text': raw.decode('utf-8')}
        packet = AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)
        self.assertEqual(packet, expected)
        self.assertEqual(hashlib.sha256(packet['expression_contract']['text'].encode('utf-8')).hexdigest(), DOCUMENT_HASH)
        request = request_for(spec, packet)
        self.assertEqual(request['messages'][1], {'role': 'user', 'content': canonical(expected)})
        self.assertEqual(request['messages'][0], {'role': 'system', 'content': PROMPT})
        self.assertEqual(spec, original)

    def test_missing_or_changed_contract_is_a_typed_gap_before_packet_use(self):
        host, spec, _ = review_inputs()
        real_read = Path.read_bytes
        for missing in (False, True):
            with self.subTest(missing=missing):
                def altered(path):
                    if path.resolve() == (ROOT / DOCUMENT).resolve():
                        if missing:
                            raise OSError('Synthetic missing D089 contract')
                        return real_read(path) + b'\nchanged semantic source\n'
                    return real_read(path)
                with patch.object(Path, 'read_bytes', altered):
                    with self.assertRaises(Invalid):
                        AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)

    def test_legacy_packet_and_prompt_bytes_stay_unchanged_without_contract_reads(self):
        host, spec, expected = review_inputs('research-ast/1')
        real_read = Path.read_bytes
        def no_contract_read(path):
            if path.resolve() == (ROOT / DOCUMENT).resolve():
                raise AssertionError('Legacy packet acquired a new contract dependency')
            return real_read(path)
        with patch.object(Path, 'read_bytes', no_contract_read):
            packet = AuxiliaryResearch._auxiliary_packet_for_spec(host, spec)
        self.assertEqual(packet, expected)
        self.assertNotIn('expression_contract', packet)
        self.assertEqual(PROTOCOL, 'meaning-comparison/1')
        self.assertEqual(hashlib.sha256(PROMPT.encode('utf-8')).hexdigest(), PROMPT_HASH)


if __name__ == '__main__':
    unittest.main()
