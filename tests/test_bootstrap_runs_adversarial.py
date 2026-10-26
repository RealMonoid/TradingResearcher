"""Independent owned-bootstrap transport/retention probes; no scientific authority."""
from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_bootstrap_runs as support
import bootstrap_support
from trading_researcher import bootstrap_runs
from trading_researcher import binance_normalize
from trading_researcher import stationary_bootstrap
from trading_researcher.codec import Invalid, canonical, decode
from trading_researcher.errors import Conflict, Denied


class OwnedBootstrapAdversarialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        support.BootstrapRunTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        support.BootstrapRunTests.tearDownClass.__func__(cls)

    @classmethod
    def op(cls, operation, **args):
        return cls.broker.call(cls.token, operation, **args)

    def args(self, key):
        return {**support.BootstrapRunTests.args(self, key), 'limits': {'max_seconds': 180, 'max_segments': 1}}

    def retained(self, schema, key):
        found = []
        for row in self.broker._db.execute('SELECT envelope FROM artifacts'):
            value = decode(row['envelope'])
            body = value.get('body')
            if type(body) is dict and body.get('schema') == schema and body.get('request', {}).get('key') == key:
                found.append(value)
        return found

    def assert_fault_rejected(self, key, mutate):
        original = bootstrap_runs.run_child
        observed = []
        def faulty(*args, **kwargs):
            report, raw = original(*args, **kwargs)
            self.assertEqual(report['result']['status'], 'RESOURCE_STOP')
            report, raw = mutate(deepcopy(report), raw)
            observed.append(report)
            return report, raw
        with patch.object(bootstrap_runs, 'run_child', side_effect=faulty), self.assertRaises((Invalid, Conflict)):
            self.op('run_development_bootstrap', **self.args(key))
        self.assertEqual(len(observed), 1)
        self.assertEqual(self.retained('development-bootstrap/1', key), [])
        self.assertEqual(len(self.retained('bootstrap-input/1', key)), 1)

    def test_minimal_resource_stop_cannot_bypass_the_result_schema(self):
        def mutate(report, raw):
            report['result'] = {'status': 'RESOURCE_STOP', 'scientific_readiness': False,
                                'classification_permitted': False}
            return report, raw
        self.assert_fault_rejected('independent-minimal-resource-result', mutate)

    def test_resource_stop_cannot_change_bound_input_or_seed(self):
        def mutate(report, raw):
            report['result']['case_report_hash'] = '0'*64
            report['result']['design']['randomness']['seed'] += 1
            return report, raw
        self.assert_fault_rejected('independent-changed-resource-input', mutate)

    def test_resource_stop_counters_cannot_contradict_retained_draw_prefix(self):
        def mutate(report, raw):
            report['result']['cases'][0]['defined'] = 19999
            report['result']['cases'][0]['attempted'] = 19999
            return report, raw
        self.assert_fault_rejected('independent-changed-resource-counters', mutate)

    def test_resource_stop_cannot_commit_a_rehashed_malformed_draw_suffix(self):
        def mutate(report, raw):
            raw += b'{"forged":true}\n'
            report['draw_blob'] = {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}
            return report, raw
        self.assert_fault_rejected('independent-changed-resource-stream', mutate)

    def test_different_owned_execution_is_not_a_declared_plan_diagnostic(self):
        other = self.op('execute_development', compiled_id=self.compiled['id'])
        self.assertNotEqual(other['id'], self.execution['id'])
        with patch.object(self.broker, '_read_blob_bytes', side_effect=AssertionError('premature case/source bytes')):
            with self.assertRaises(Invalid):
                self.op('run_development_bootstrap', **{**self.args('independent-other-execution'), 'execution_id': other['id']})
        self.assertEqual(self.retained('bootstrap-input/1', 'independent-other-execution'), [])

    def test_prelaunch_transaction_failure_rolls_back_capsule_and_starts_no_child(self):
        key = 'independent-bootstrap-rollback'
        original = self.broker._event
        def event(actor, event_name, **data):
            if event_name == 'bound_computation_started' and data.get('kind') == 'development_bootstrap':
                raise RuntimeError('independent transaction injection')
            return original(actor, event_name, **data)
        with patch.object(self.broker, '_event', side_effect=event), \
                patch.object(bootstrap_runs, 'run_child', side_effect=AssertionError('uncommitted launch')) as launch:
            with self.assertRaises(RuntimeError):
                self.op('run_development_bootstrap', **self.args(key))
            launch.assert_not_called()
        self.assertEqual(self.retained('bootstrap-input/1', key), [])
        self.assertEqual(self.retained('development-bootstrap/1', key), [])

    def test_failed_request_retains_source_and_retries_without_checkout_calculator(self):
        args = self.args('independent-retry-retained-bootstrap')
        def fail(*unused, **kwargs):
            self.assertEqual(len(self.retained('bootstrap-input/1', args['key'])), 1)
            raise RuntimeError('independent admitted interruption')
        with patch.object(bootstrap_runs, 'run_child', side_effect=fail):
            with self.assertRaises(RuntimeError):
                self.op('run_development_bootstrap', **args)
        with self.assertRaises(Conflict):
            self.op('run_development_bootstrap', **{**args, 'limits': {'max_seconds': 179, 'max_segments': 1}})
        with patch.object(bootstrap_runs, 'source_bundle', side_effect=AssertionError('retained retry used checkout')):
            result = self.op('run_development_bootstrap', **args)
        self.assertEqual(result['body']['status'], 'RESOURCE_STOP')
        self.assertIs(result['body']['scientific_readiness'], False)
        self.assertIsNone(result['body']['verification'])
        self.assertEqual(result['body']['request'], args)

    def test_late_caller_mutation_cannot_rebind_the_admitted_request(self):
        args = self.args('independent-mutable-bootstrap-request')
        expected = deepcopy(args)
        original = bootstrap_runs.run_child
        def changed(*parameters, **kwargs):
            args['limits']['max_segments'] = 99999
            args['plan_id'] = 'caller-mutated-after-admission'
            return original(*parameters, **kwargs)
        with patch.object(bootstrap_runs, 'run_child', side_effect=changed):
            result = self.op('run_development_bootstrap', **args)
        self.assertEqual(result['body']['request'], expected)
        self.assertEqual(result['body']['result']['limits'], expected['limits'])


class BootstrapEnvelopeAdversarialTests(unittest.TestCase):
    def payload(self, source, design, limits):
        raw = ''.join(canonical(case)+'\n' for case in source['cases']).encode()
        return {'report': {k: v for k, v in source.items() if k != 'cases'},
                'case_blob': {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)},
                'design': design, 'limits': limits}

    def test_pending_input_cannot_be_relabelled_as_a_resource_stop(self):
        source = bootstrap_support.report(as_of=900)
        design = {'base_length': 1, 'primary_count': 2, 'randomness': stationary_bootstrap.randomness(713)}
        limits = {'max_seconds': 60, 'max_segments': 1}
        result = stationary_bootstrap.calculate(source, design, limits)
        self.assertEqual(result['status'], 'INPUT_GAP')
        result.update(status='RESOURCE_STOP', reason='caller_cancelled')
        with self.assertRaises(Invalid):
            bootstrap_runs.validate_result(result, self.payload(source, design, limits), b'', result['descriptive'])

    def test_segment_exhaustion_cannot_be_claimed_before_using_the_cap(self):
        source = bootstrap_support.report()
        design = {'base_length': 1, 'primary_count': 2, 'randomness': stationary_bootstrap.randomness(713)}
        limits = {'max_seconds': 60, 'max_segments': 1}
        result = stationary_bootstrap.calculate(source, design, limits, stop=lambda: True)
        self.assertEqual(result['status'], 'RESOURCE_STOP')
        self.assertEqual(result['cases'], [])
        result['reason'] = 'computation_segment_limit'
        with self.assertRaises(Invalid):
            bootstrap_runs.validate_result(result, self.payload(source, design, limits), b'', result['descriptive'])


class BootstrapChildLifecycleAdversarialTests(unittest.TestCase):
    def test_explicit_short_child_timeout_kills_and_reaps_actual_process(self):
        original = subprocess.Popen
        processes = []
        def launched(*args, **kwargs):
            process = original(*args, **kwargs)
            processes.append(process)
            return process
        with tempfile.TemporaryDirectory(prefix='trf-bootstrap-independent-timeout-') as folder:
            with patch.object(binance_normalize.subprocess, 'Popen', side_effect=launched):
                with self.assertRaises(Invalid):
                    binance_normalize._run_child([sys.executable, '-I', '-c', 'import time; time.sleep(60)'],
                                                Path(folder), timeout=0.15)
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll())


if __name__ == '__main__':
    unittest.main()
