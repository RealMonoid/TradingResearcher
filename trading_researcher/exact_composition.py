"""D084 metadata composition conformance for certified AST4 primitives.

This validates the compiler contract and exact candidate binding, not a natural-
language hypothesis, original-specific formula oracle or empirical outcome.
"""
import hashlib
import io
from pathlib import Path
import sys
import unittest

from .binding import environment, hashes, require, write_file
from .certification import _environment_current
from .codec import canonical, decode, digest
from . import exact_runtime

ROOT=Path(__file__).resolve().parents[1]
PROFILE='exact-certified-composition/1'
TEST='tests/test_exact_runtime_review.py'
TEST_SHA256='39cb6596fd8a354510fb838b6702848eaa208858c4be8d51477cc593796ef596'
CHECKS=('test_compile_new_window_spans_and_exact_mature_metadata',
        'test_protected_outside_manifest_version_unit_and_catalog_changes_reject')
DRIVER='trading_researcher/exact_composition.py'
FILES=tuple(sorted((*exact_runtime.FILES,TEST,DRIVER)))
BOOTSTRAP='import sys;sys.path.insert(0,sys.argv[1]);from trading_researcher.exact_composition import child_entry;child_entry(sys.argv[2])'


def read_bundle():
    bundle={**exact_runtime.read_bundle(),TEST:(ROOT/TEST).read_bytes(),DRIVER:(ROOT/DRIVER).read_bytes()}
    require(hashlib.sha256(bundle[TEST]).hexdigest()==TEST_SHA256,'Independent AST4 compiler expectations changed')
    return bundle


def expected(payload, compilation_hash):
    return {'profile':PROFILE,'compilation_hash':compilation_hash,'candidate_hash':digest(payload['candidate']),
        'checks':{'fixture_sha256':TEST_SHA256,'passed_cases':list(CHECKS)},'scientific_readiness':False}


def child_entry(request_path):
    request=decode(Path(request_path).read_bytes())
    require(type(request) is dict and set(request)=={'payload','compilation_hash','footprint'})
    require(set(request['footprint'])==set(FILES) and hashes(read_bundle())==request['footprint'])
    # These independently authored methods are pure metadata/golden checks.
    # No recursive child invocation or hypothesis-row evaluation is selected.
    sys.path.insert(0,str(ROOT/'tests'))
    from test_exact_runtime_review import ExactRuntimeReview
    suite=unittest.TestSuite(ExactRuntimeReview(name) for name in CHECKS)
    output=io.StringIO();checked=unittest.TextTestRunner(stream=output).run(suite)
    require(checked.testsRun==len(CHECKS) and checked.wasSuccessful() and not checked.skipped
        and not checked.expectedFailures and not checked.unexpectedSuccesses,output.getvalue())
    compilation=exact_runtime.compile_payload(request['payload'])
    require(digest(compilation)==request['compilation_hash'],'Candidate compilation differs from its retained binding')
    require(hashes(read_bundle())==request['footprint'])
    print(canonical({'result':expected(request['payload'],request['compilation_hash']),
        'request_hash':digest(request),'footprint':request['footprint'],
        'environment':environment(request['footprint'])}),flush=True)


def run_child(bundle,payload,compilation_hash,directory,*,timeout=1800):
    from .binance_normalize import _run_child
    require(type(bundle) is dict and set(bundle)==set(FILES) and type(timeout) is int and 1<=timeout<=1800)
    require(hashlib.sha256(bundle[TEST]).hexdigest()==TEST_SHA256)
    directory=Path(directory);footprint=hashes(bundle)
    request={'payload':payload,'compilation_hash':compilation_hash,'footprint':footprint}
    for name,raw in bundle.items():
        destination=directory/name;destination.parent.mkdir(parents=True,exist_ok=True);write_file(destination,raw)
    write_file(directory/'request.json',canonical(request).encode())
    result=_run_child([sys.executable,'-I','-S','-B','-c',BOOTSTRAP,str(directory),str(directory/'request.json')],directory,timeout=timeout)
    require(type(result) is dict and set(result)=={'result','request_hash','footprint','environment'}
        and result['request_hash']==digest(request) and result['footprint']==footprint
        and canonical(result['result'])==canonical(expected(payload,compilation_hash))
        and _environment_current(result['environment']))
    require(hashes({name:(directory/name).read_bytes() for name in bundle})==footprint)
    return result
