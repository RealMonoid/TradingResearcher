"""Host-owned, version-bound conformance for the fixed reference implementation."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid

from .codec import MAX_BYTES, Invalid, canonical, decode, digest, integer, text
from .errors import Conflict, Denied


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = 'implementation-certificate/1'
PROFILE = 'reference-computation/1'
PINS = {
    'docs/architecture/14_RETAIL_RESEARCH_CONTRACT.md': 'e8513ced048dd3c60f30490736e666cadf4d3da0929002b4923a8d70ac31a76d',
    'trading_researcher/EXPRESSIONS.md': '522a810ec667ba2e4cdbf223d0446f196349484bb5119deeaf121d27bcfb5962',
    'trading_researcher/OUTCOMES.md': '633f06660ca6199c6e74283b783ecfc336ffce9acf058da4272c60e7699fac0a',
    'tests/fixtures/reference_expression_cases.json': 'df14f72459f791c3669236efa9b13d8a56e4c755ccdeb6f27f7b29375ac277b1',
    'tests/fixtures/reference_outcome_cases.json': 'e36ee6997ef7fb9f09e11156d4ed3d3c44ab6faea9caa7a7db44ea7c9f2e5817',
    'tests/test_expressions.py': 'a927ef0a44c0f81945ffa6e0f5f9858ac526838da5d01d80f6c04f641d52ba02',
    'tests/test_outcomes.py': '2ecaa33fa2b76792ed6df26924d6f43280138123ed93789d88108437b0237384',
}
FILES = tuple(sorted((*PINS, *(f'trading_researcher/{name}.py' for name in (
    '__init__', 'codec', 'errors', 'expressions', 'outcomes', 'certification')))))
EXPECTED_CHECKS = {'expression_cases': 112, 'outcome_cases': 31, 'supplemental_tests': 16,
                   'skipped': 0, 'failures': 0, 'errors': 0, 'unexpected_successes': 0,
                   'capability_probes': 9}
SCOPE = {'interfaces': ['research-ast/1', 'reference-cases/1', 'reference-contrast/1'],
         'authority': 'implementation_conformance_only',
         'not_certified': ['supplied_features_or_data', 'semantic_equivalence', 'scientific_evidence',
                           'calibration', 'D087_events', 'capital_authority', 'OS_sandbox']}


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_bundle():
    return {name: (ROOT / name).read_bytes() for name in FILES}


def _footprint(bundle):
    return {name: _sha(raw) for name, raw in sorted(bundle.items())}


def _pins_match(footprint):
    return set(footprint) == set(FILES) and all(footprint[name] == value for name, value in PINS.items())


def _runtime_identity():
    base = Path(sys.base_prefix).resolve()
    dlls = sorted(base.glob('python*.dll'))
    if len(dlls) > 16:
        raise Invalid('Unexpected Python runtime dependency count')
    return {'implementation': sys.implementation.name, 'version': sys.version,
            'platform': sys.platform, 'byteorder': sys.byteorder,
            'executable_sha256': _sha(Path(sys.executable).read_bytes()),
            'runtime_libraries': {path.name: _sha(path.read_bytes()) for path in dlls}}


def _runtime_path_allowed(path):
    path = Path(path).resolve()
    return (path.is_relative_to(Path(sys.base_prefix).resolve())
            and not {'site-packages', 'dist-packages'} & {part.casefold() for part in path.parts})


def _runtime_environment():
    base = Path(sys.base_prefix).resolve()
    libraries = {}
    for module_name, module in tuple(sys.modules.items()):
        file = getattr(module, '__file__', None)
        if not file:
            continue
        path = Path(file).resolve()
        if (_runtime_path_allowed(path) and path.is_file()
                and module_name.split('.')[0] in sys.stdlib_module_names):
            libraries[path.relative_to(base).as_posix()] = _sha(path.read_bytes())
        elif path.is_relative_to(ROOT) and path.relative_to(ROOT).as_posix() in FILES:
            continue
        else:
            raise Invalid('Executed module is outside the fixed dependency closure')
    return {'identity': _runtime_identity(), 'standard_library': dict(sorted(libraries.items())),
            'isolation': {'isolated': sys.flags.isolated, 'no_site': sys.flags.no_site,
                          'ignore_environment': sys.flags.ignore_environment,
                          'no_bytecode_writes': int(sys.dont_write_bytecode)}}


def _environment_current(environment):
    if (type(environment) is not dict or set(environment) != {'identity', 'standard_library', 'isolation'}
            or environment['identity'] != _runtime_identity()
            or environment['isolation'] != {'isolated': 1, 'no_site': 1, 'ignore_environment': 1,
                                             'no_bytecode_writes': 1}):
        return False
    libraries = environment['standard_library']
    if type(libraries) is not dict or not libraries or len(libraries) > 512:
        return False
    base = Path(sys.base_prefix).resolve()
    for name, value in libraries.items():
        if type(name) is not str:
            return False
        path = (base / name).resolve()
        if Path(name).is_absolute() or not _runtime_path_allowed(path) or not path.is_file():
            return False
        if _sha(path.read_bytes()) != value:
            return False
    return True


def _report(status, reason, footprint=None, checks=None, environment=None):
    return {'profile': PROFILE, 'scope': deepcopy(SCOPE), 'status': status, 'reason': reason,
            'footprint': footprint or {}, 'checks': checks or {}, 'environment': environment,
            'scientific_readiness': False}


def _require(condition):
    if not condition:
        raise Invalid('Conformance mismatch')


def _check_counts_valid(checks):
    if type(checks) is not dict or set(checks) != set(EXPECTED_CHECKS):
        return False
    for name, value in checks.items():
        maximum = EXPECTED_CHECKS[name] or EXPECTED_CHECKS['supplemental_tests']
        if type(value) is not int or not 0 <= value <= maximum:
            return False
    return True


def _child_validation():
    bundle = read_bundle()
    footprint = _footprint(bundle)
    if not _pins_match(footprint):
        return _report('CERTIFICATION_GAP', 'PINNED_INPUT_CHANGED', footprint)
    checks = dict.fromkeys(EXPECTED_CHECKS, 0)
    try:
        from .expressions import ExpressionGap, ReferenceEngine
        from .outcomes import materialize_reference, reference_contrast
        expression_cases = decode(bundle['tests/fixtures/reference_expression_cases.json'])
        _require(expression_cases['schema'] == 'reference-expression-cases/1'
                 and len(expression_cases['cases']) == 112)
        for case in expression_cases['cases']:
            original = deepcopy(case)
            program = {'schema': 'research-ast/1', 'catalog_hash': digest(case['catalog']),
                       'expression': case['expression']}
            try:
                result = ReferenceEngine(case['catalog'], case['rows']).evaluate(program, case['index'])
            except ExpressionGap as error:
                _require(case.get('error_code') == error.code)
            else:
                _require('error_code' not in case and result == case['expected'])
            _require(original == case)
            checks['expression_cases'] += 1
        outcome_cases = decode(bundle['tests/fixtures/reference_outcome_cases.json'])
        _require(outcome_cases['schema'] == 'reference-outcome-cases/1'
                 and len(outcome_cases['cases']) == 31)
        for case in outcome_cases['cases']:
            original = deepcopy(case)
            result = materialize_reference(case['request'], case['catalog'], case['rows'])
            contrast = reference_contrast(result)
            expected = case['expected']
            _require([x['status'] for x in result['cases']] == expected['case_states'])
            _require([x['outcome'] for x in result['cases']] == expected['outcome_values'])
            _require(all(contrast[key] == expected[key] for key in ('effect', 'scope_count', 'condition_count')))
            _require(result['scientific_readiness'] is False and contrast['scientific_readiness'] is False)
            _require(original == case)
            checks['outcome_cases'] += 1
        engine = ReferenceEngine({}, [{'time': 0, 'instrument': 'A', 'features': {}}])
        for op in ('call', 'eval', 'exec', 'import', 'read_file', 'write_file', 'request', 'network', 'callback'):
            try:
                engine.evaluate({'schema': 'research-ast/1', 'catalog_hash': digest({}),
                                 'expression': {'op': op}}, 0)
            except ExpressionGap as error:
                _require(error.code == 'LANGUAGE_GAP')
            else:
                raise Invalid('Unexpected expression capability')
            checks['capability_probes'] += 1
        suite = unittest.TestSuite()
        for name in ('test_expressions.py', 'test_outcomes.py'):
            suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=name))
        result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        checks.update(supplemental_tests=result.testsRun, skipped=len(result.skipped),
                      failures=len(result.failures), errors=len(result.errors),
                      unexpected_successes=len(result.unexpectedSuccesses))
        _require(result.wasSuccessful() and not result.expectedFailures and checks == EXPECTED_CHECKS)
        _require(_footprint(read_bundle()) == footprint)
        return _report('CERTIFIED', 'FIXED_CONFORMANCE_PASSED', footprint, checks, _runtime_environment())
    except Exception:
        return _report('CERTIFICATION_GAP', 'CONFORMANCE_FAILED', footprint, checks)


def run_reference_validation(bundle=None):
    """Validate a copied source snapshot; the broker rechecks workspace before storing."""
    footprint = {}
    try:
        bundle = read_bundle() if bundle is None else deepcopy(bundle)
        footprint = _footprint(bundle)
        if not _pins_match(footprint):
            return _report('CERTIFICATION_GAP', 'PINNED_INPUT_CHANGED', footprint)
        with tempfile.TemporaryDirectory(prefix='trading-reference-check-') as temporary:
            snapshot = Path(temporary)
            for name, raw in bundle.items():
                target = snapshot / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            bootstrap = ('import sys,runpy;sys.path.insert(0,sys.argv[1]);'
                         'runpy.run_module("trading_researcher.certification",run_name="__main__")')
            try:
                completed = subprocess.run(
                    [sys.executable, '-I', '-S', '-B', '-X', 'pycache_prefix=' + str(snapshot / 'cache'),
                     '-c', bootstrap, str(snapshot)], cwd=snapshot,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30, check=False)
            except subprocess.TimeoutExpired:
                return _report('CERTIFICATION_GAP', 'VALIDATOR_TIMEOUT', footprint)
            # Parent-owned verification, independent of the child's reported hashes.
            copied = {name: (snapshot / name).read_bytes() for name in FILES}
            if _footprint(copied) != footprint:
                return _report('CERTIFICATION_GAP', 'VALIDATION_SNAPSHOT_CHANGED', footprint)
            if completed.returncode != 0 or completed.stderr or len(completed.stdout) > 1048576:
                return _report('CERTIFICATION_GAP', 'VALIDATOR_PROCESS_FAILED', footprint)
            try:
                report = decode(completed.stdout)
            except Invalid:
                return _report('CERTIFICATION_GAP', 'INVALID_VALIDATOR_RESPONSE', footprint)
            if (type(report) is not dict or set(report) != set(_report('', ''))
                    or report['profile'] != PROFILE or report['scope'] != SCOPE
                    or report['footprint'] != footprint or report['scientific_readiness'] is not False
                    or report['status'] not in ('CERTIFIED', 'CERTIFICATION_GAP')
                    or len(canonical(report).encode('utf-8')) > MAX_BYTES - 8192):
                return _report('CERTIFICATION_GAP', 'INVALID_VALIDATOR_RESPONSE', footprint)
            if report['status'] == 'CERTIFIED' and (
                    report['reason'] != 'FIXED_CONFORMANCE_PASSED' or not _check_counts_valid(report['checks'])
                    or report['checks'] != EXPECTED_CHECKS
                    or not _environment_current(report['environment'])):
                return _report('CERTIFICATION_GAP', 'INVALID_VALIDATOR_RESPONSE', footprint)
            if report['status'] == 'CERTIFICATION_GAP' and (
                    report['environment'] is not None
                    or report['reason'] not in ('PINNED_INPUT_CHANGED', 'CONFORMANCE_FAILED')
                    or (report['reason'] == 'PINNED_INPUT_CHANGED' and report['checks'] != {})
                    or (report['reason'] == 'CONFORMANCE_FAILED' and not _check_counts_valid(report['checks']))):
                return _report('CERTIFICATION_GAP', 'INVALID_VALIDATOR_RESPONSE', footprint)
            return report
    except (OSError, ValueError, TypeError):
        return _report('CERTIFICATION_GAP', 'VALIDATOR_INPUT_OR_RUNTIME_UNAVAILABLE', footprint)


class ReferenceCertification:
    def _reference_attempts(self):
        attempts = {}
        for row in self._db.execute('SELECT envelope FROM events ORDER BY seq'):
            event = decode(row[0])
            if event['actor'] != 'controller':
                continue
            action, details = event['action'], event['details']
            identity = details.get('attempt_id')
            if action == 'reference_certification_started' and identity:
                attempts[identity] = {'attempt_id': identity, 'source_package_id': details['source_package_id'],
                    'state': 'STARTED', 'started_at': event['time'], 'ended_at': None, 'certificate_id': None}
            elif identity in attempts and action in ('reference_certification_checked', 'reference_certification_interrupted'):
                attempts[identity].update(state='COMPLETED' if action == 'reference_certification_checked' else 'INTERRUPTED',
                                         ended_at=event['time'], certificate_id=details.get('artifact_id'))
        return list(attempts.values())

    def _recover_reference_checks(self):
        # Owning the exclusive registry writer lock proves the earlier broker cannot commit.
        pending = [item for item in self._reference_attempts() if item['state'] == 'STARTED']
        if pending:
            with self._transaction():
                for item in pending:
                    self._event('controller', 'reference_certification_interrupted', attempt_id=item['attempt_id'],
                                source_package_id=item['source_package_id'], reason='previous_writer_ended_before_commit')

    def _inspect_reference_checks(self, actor, limit=50):
        integer(limit, 'limit', 1)
        if limit > 100:
            raise Invalid('Reference check view is bounded to 100 records')
        attempts = self._reference_attempts()
        return {'attempts': list(reversed(attempts[-limit:])), 'total': len(attempts),
                'pending': sum(item['state'] == 'STARTED' for item in attempts), 'scientific_authority': False}

    def _retain_reference_package(self, bundle):
        if set(bundle) != set(FILES) or any(type(raw) is not bytes for raw in bundle.values()):
            raise Invalid('Reference package must contain the exact allowlisted source closure')
        if sum(len(raw) for raw in bundle.values()) > 16 * 1024 * 1024:
            raise Invalid('Reference source package exceeds the 16 MiB resource envelope')
        files = {name: self._stage_blob_bytes(raw) for name, raw in sorted(bundle.items())}
        with self._transaction():
            for descriptor in files.values():
                self._register_blob(descriptor)
            result = self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'operations', 'source_refs': [], 'exposure': [],
                'blob_refs': sorted({value['sha256'] for value in files.values()}),
                'authority': 'retained_source_not_certified',
                'body': {'schema': 'reference-source-package/1', 'created_at': self._now(),
                         'profile': PROFILE, 'files': files, 'footprint': _footprint(bundle)}})
            self._event('controller', 'reference_source_retained', artifact_id=result['id'], profile=PROFILE)
            return result['id']

    def _load_reference_package(self, package_id):
        text(package_id, 'source_package_id')
        artifact = self._artifact(package_id)
        body = artifact['body']
        if (artifact['creator'] != 'controller' or artifact['origin'] != 'controller'
                or artifact.get('authority') != 'retained_source_not_certified'
                or type(body) is not dict or set(body) != {'schema', 'created_at', 'profile', 'files', 'footprint'}
                or body['schema'] != 'reference-source-package/1' or body['profile'] != PROFILE
                or type(body['files']) is not dict or set(body['files']) != set(FILES)):
            raise Invalid('Expected a host-owned source package for the exact reference profile')
        bundle, identities, size = {}, set(), 0
        for name, descriptor in body['files'].items():
            if type(descriptor) is not dict or set(descriptor) != {'sha256', 'size'}:
                raise Conflict('Malformed retained source descriptor')
            raw = self._read_blob_bytes(descriptor['sha256'])
            if type(descriptor['size']) is not int or len(raw) != descriptor['size']:
                raise Conflict('Retained source size differs from its manifest')
            size += len(raw)
            if size > 16 * 1024 * 1024:
                raise Conflict('Retained source package exceeds its resource envelope')
            bundle[name] = raw
            identities.add(descriptor['sha256'])
        if identities != set(artifact.get('blob_refs', [])) or _footprint(bundle) != body['footprint']:
            raise Conflict('Retained source references or footprint do not match')
        return bundle

    def _certify_reference_external(self, token, args, retained=False):
        with self._mutex:
            actor = self._principal(token)
            if actor['role'] != 'operator':
                raise Denied('Reference certification is owned by the host')
        expected = {'source_package_id'} if retained else set()
        if set(args) != expected:
            raise Invalid('Reference certification accepts no code, path or expectation overrides')
        package_id, bundle, report = args.get('source_package_id'), None, None
        if retained:
            try:
                with self._mutex:
                    bundle = self._load_reference_package(package_id)
            except Conflict:
                report = _report('CERTIFICATION_GAP', 'RETAINED_SOURCE_UNAVAILABLE')
        else:
            try:
                bundle = read_bundle()
                package_id = self._retain_reference_package(bundle)
            except (OSError, ValueError, TypeError, Conflict):
                report = _report('CERTIFICATION_GAP', 'SOURCE_PACKAGE_UNAVAILABLE')
        attempt_id = uuid.uuid4().hex
        with self._transaction():
            actor = self._principal(token)
            if actor['role'] != 'operator':
                raise Denied('Reference certification is owned by the host')
            self._event('controller', 'reference_certification_started', attempt_id=attempt_id,
                        source_package_id=package_id, retained=retained)
        if report is None:
            report = run_reference_validation(bundle)
        with self._transaction():
            actor = self._principal(token)
            if actor['role'] != 'operator':
                raise Denied('Reference certification is owned by the host')
            if report['status'] == 'CERTIFIED':
                try:
                    current = _footprint(self._load_reference_package(package_id)) == report['footprint']
                    if not retained:
                        current = current and _footprint(read_bundle()) == report['footprint']
                    current = current and _environment_current(report['environment'])
                except (OSError, ValueError, TypeError, Conflict):
                    current = False
                if not current:
                    report = {**report, 'status': 'CERTIFICATION_GAP',
                              'reason': 'SOURCE_CHANGED_DURING_VALIDATION'}
            body = {'schema': SCHEMA, 'created_at': self._now(), 'attempt_id': attempt_id,
                    'source_package_id': package_id,
                    'validation_mode': 'retained_package' if retained else 'installed_snapshot', **report}
            artifact = self._save_artifact({'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': 'operations', 'body': body,
                'source_refs': [package_id] if package_id else [],
                'exposure': [package_id] if package_id else [], 'authority': 'implementation_conformance_only'})
            self._event('controller', 'reference_certification_checked', artifact_id=artifact['id'],
                        status=body['status'], profile=PROFILE, attempt_id=attempt_id)
            canonical(artifact)
            return artifact

    def _reference_certificate_status(self, actor, certificate_id):
        text(certificate_id, 'certificate_id')
        artifact = self._artifact(certificate_id)
        body = artifact['body']
        if (artifact['creator'] != 'controller' or artifact['origin'] != 'controller'
                or artifact.get('authority') != 'implementation_conformance_only'
                or type(body) is not dict or body.get('schema') != SCHEMA
                or body.get('profile') != PROFILE or body.get('scope') != SCOPE):
            raise Invalid('Expected a host-issued certificate for the exact reference profile')
        status = 'CERTIFICATION_GAP'
        retained_status = 'NOT_VERIFIED'
        if body['status'] == 'CERTIFIED':
            try:
                package_id = body.get('source_package_id')
                if not package_id:
                    return {'certificate_id': certificate_id, 'status': 'LEGACY_UNBOUND',
                            'retained_source_status': 'NO_PACKAGE', 'scientific_readiness': False}
                retained_bundle = self._load_reference_package(package_id)
                if _footprint(retained_bundle) != body['footprint']:
                    raise Conflict('Certificate and retained source footprint differ')
                retained_status = 'VERIFIED'
            except (OSError, ValueError, TypeError, Conflict, Denied):
                return {'certificate_id': certificate_id, 'status': 'QUARANTINED',
                        'retained_source_status': 'UNAVAILABLE', 'scientific_readiness': False}
            try:
                current = _footprint(read_bundle()) == body['footprint']
                current = current and _pins_match(body['footprint']) and _environment_current(body['environment'])
            except (OSError, ValueError, TypeError):
                current = False
            status = 'CURRENT' if current else 'STALE'
        return {'certificate_id': certificate_id, 'status': status,
                'retained_source_status': retained_status,
                'scope': 'Installed reference snapshot only; later execution must use a fresh bound snapshot',
                'scientific_readiness': False}


if __name__ == '__main__':
    print(json.dumps(_child_validation(), ensure_ascii=False, sort_keys=True))
