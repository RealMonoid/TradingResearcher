"""Fixed synthetic transport benchmark inputs; no scientific admission fixture."""
from copy import deepcopy
import hashlib
from pathlib import Path
import zipfile

from test_population_models import fixture
from test_information_study import assigned, profile
from trading_researcher.codec import canonical
from trading_researcher.family_study import make_manifest
from trading_researcher.information_diagnostics import diagnose
from trading_researcher.population_models import specification


LEGACY = Path(__file__).parent / 'fixtures/study-source-0f1bf36.zip'
LEGACY_SHA = 'ee335215005ce138a058ea3499c5424ac929003a9243e80c139ed0c18dc96e2f'


def legacy_source():
    assert hashlib.sha256(LEGACY.read_bytes()).hexdigest() == LEGACY_SHA
    with zipfile.ZipFile(LEGACY) as archive:
        return {name:archive.read(name) for name in archive.namelist()}


def inputs():
    report = fixture(); diagnostics = diagnose(report, [1, 2])
    cases = b''.join((canonical(case)+'\n').encode() for case in report.pop('cases'))
    payload = {'report':report, 'diagnostics':diagnostics,
        'case_blob':{'sha256':hashlib.sha256(cases).hexdigest(), 'size':len(cases)}}
    bound = assigned()
    bound.update(base_length=1, primary_count=2, instruments=2, available_time_rows=64)
    config = profile()
    config.update(specifications=[specification(2, 0, 1, 'Fixed transport benchmark; not market-model adequacy.')],
        targets=[64], worlds_per_cell=1, seed=101, responses=['a','b'], patterns=[[0,0],[0,1],[1,1],[2,2]])
    config['budget'].update(attempt_compute_ms=180000, max_compute_ms=600000,
        max_storage_bytes=4*1024**3, attempt_storage_bytes=256*1024**2)
    manifest = make_manifest(bound, config)
    # Preselected mixed-truth cell. No search or retry to obtain a favorable result.
    world = deepcopy(manifest['worlds'][1])
    return payload, manifest, world, cases
