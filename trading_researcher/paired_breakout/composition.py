"""Candidate-bound synthetic checks and a direct original-formula row audit.

The independent oracle is test-owned and separately pinned. Its formulas and
synthetic data are never substituted for a model's actual candidate. A matching
finite test inventory supplements, rather than replaces, independent meaning
review, source certification and the development data-use boundary.
"""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
from pathlib import Path

from ..binding import require
from ..codec import digest
from ..outcomes import _instant
from ..paired_composition import compare_cases
from ..paired_development import materialize_paired, paired_contrast
from ..paired_runtime import compile_payload

ROOT = Path(__file__).resolve().parents[2]
IDEA_ID = '4abce1d5187d7fd229b52dd9a00e0beca8ee3947e9a1470dbc5351ff78c8872a'
PROFILE = 'paired-breakout-composition/1'
ORACLE = 'tests/paired_breakout_oracle.py'
ORACLE_SHA256 = '97e9288a835441ea5e039619b12782972d980eec50861b7b58dfcfe02e32d7d2'
START = '2023-01-01T00:00:00Z'
END = '2023-04-01T00:00:00Z'
SYNTHETIC_BARS = 30


def oracle_module():
    path = ROOT / ORACLE
    require(hashlib.sha256(path.read_bytes()).hexdigest() == ORACLE_SHA256,
            'Independent breakout expectations changed')
    spec = importlib.util.spec_from_file_location('independent_paired_breakout', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.IDEA_ID == IDEA_ID, 'Independent oracle binds another idea')
    return module


def original_compilation(payload):
    compiled = compile_payload(payload)
    candidate = payload['candidate']
    universe = candidate['test_universe']
    require(candidate['idea_ref'] == IDEA_ID,
            'Breakout composition belongs only to its retained original idea')
    require(universe['start'] == START and universe['end'] == END
            and universe['pair'] == ['BTCUSDT', 'ETHUSDT']
            and candidate['horizons'] == {'grid_seconds': 900, 'outcome_bars': 5}
            and candidate['outcome']['scale'] == 'quantity'
            and candidate['claim_kind'] == 'difference'
            and candidate['comparator'] == {'kind': 'whole_scope'}
            and candidate['estimand'] == {
                'kind': 'conditional-minus-scope-mean/1', 'unit': 'basis_points',
                'weighting': 'equal_rows', 'missingness': 'scope-true-outcome-observed/1',
                'condition_unknown': 'exclude-from-condition-retain-in-scope',
                'nuisance_fit': 'none', 'direction': 'positive'},
            'Original paired population, estimand or horizon differs')
    return compiled


def qualify(payload):
    compiled = original_compilation(payload)
    oracle = oracle_module()
    start, end = oracle.ORIGINAL_START, oracle.ORIGINAL_START + SYNTHETIC_BARS * 900
    stamp = lambda value: datetime.fromtimestamp(value, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    results, names = [], set()
    for name, rows, as_of in oracle.scenarios():
        require(type(name) is str and name and name not in names and len(names) < 1024,
                'Bounded unique synthetic scenarios required')
        names.add(name)
        request = deepcopy(compiled['request'])
        # Only the test interval is shortened. The submitted expressions,
        # pair, weighting, source definitions and all original constants stay.
        request['universe']['start'], request['universe']['end'] = stamp(start), stamp(end)
        request['as_of'] = stamp(end if as_of is None else as_of)
        report = materialize_paired(request, payload['catalog'], rows, payload['feature_definitions'])
        require(report['status'] == 'PROCESSED', 'Synthetic composition did not complete')
        paired_contrast(report)
        expected = oracle.oracle(rows, start, end, end if as_of is None else as_of)
        results.append({'name': name, **compare_cases(report['cases'], expected)})
    require(results, 'Independent composition inventory is empty')
    return {'schema': 'paired-breakout-composition-result/1', 'profile': PROFILE,
        'idea_id': IDEA_ID, 'candidate_hash': digest(payload['candidate']),
        'oracle_sha256': ORACLE_SHA256, 'scenarios': results, 'scenario_count': len(results),
        'checked_cases': sum(item['checked_cases'] for item in results),
        'scientific_readiness': False}


def audit(payload, rows, cases):
    original_compilation(payload)
    oracle = oracle_module()
    expected = oracle.oracle(rows, _instant(START), _instant(END), _instant(payload['as_of']))
    return {'schema': 'paired-breakout-row-audit/1', 'profile': PROFILE, 'idea_id': IDEA_ID,
        'oracle_sha256': ORACLE_SHA256, 'candidate_hash': digest(payload['candidate']),
        **compare_cases(cases, expected), 'scientific_readiness': False,
        'qualification': 'Independent Decimal100 cross-check; rigorous bounds belong to the certified evaluator.'}
