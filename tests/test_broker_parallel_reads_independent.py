"""Bounded shared-connection artifact-read regression, not a stress platform.

Six real host threads read genuinely retained immutable Broker artifacts. Each
result is compared to its independent exact original envelope/body. No native,
study, certificate, actual Registry or model work is performed.
"""
from concurrent.futures import ThreadPoolExecutor
from collections import Counter
from copy import deepcopy
from pathlib import Path
import sys
import sqlite3
import tempfile
import threading
import unittest

from trading_researcher.coordination import Broker
from trading_researcher.codec import digest


THREADS = 6
ROUNDS = 1200
FIXTURE_ARTIFACTS = 16


class BrokerParallelReadsIndependentTests(unittest.TestCase):
    observations = []

    def test_six_host_threads_read_exact_immutable_artifacts_on_one_real_broker_connection(self):
        with tempfile.TemporaryDirectory(prefix='trf-broker-parallel-read-') as temporary:
            broker = Broker(Path(temporary) / 'registry', clock=lambda: 1000)
            try:
                originals = [broker.call(broker.admin_token, 'add_source', data_class='operations',
                    body={'independent_parallel_read': ordinal,
                          'payload': chr(65 + ordinal) * 4096}) for ordinal in range(FIXTURE_ARTIFACTS)]
                expected = {artifact['id']: deepcopy(artifact) for artifact in originals}
                identities = [artifact['id'] for artifact in originals]
                before_events = broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
                barrier = threading.Barrier(THREADS)

                def read(thread_index):
                    counts = Counter(); error_types = Counter(); samples = []
                    for round_index in range(ROUNDS):
                        try:
                            barrier.wait(timeout=10)
                        except threading.BrokenBarrierError:
                            counts['barrier_failures'] += 1
                            break
                        identity = identities[(round_index * 7 + thread_index * 3) % FIXTURE_ARTIFACTS]
                        counts['queries'] += 1
                        try:
                            observed = broker._artifact(identity)
                            if observed == expected[identity]:
                                counts['exact'] += 1
                            else:
                                counts['mismatches'] += 1
                                if len(samples) < 3:
                                    samples.append({'kind': 'mismatch', 'expected_id': identity,
                                        'observed_id': observed.get('id') if isinstance(observed, dict) else None,
                                        'observed_ordinal': observed.get('body', {}).get('independent_parallel_read')
                                            if isinstance(observed, dict) else None})
                        except Exception as exc:
                            counts['exceptions'] += 1
                            error_types[type(exc).__name__] += 1
                            if len(samples) < 3:
                                samples.append({'kind': 'exception', 'type': type(exc).__name__,
                                                'message': str(exc)[:160]})
                    return counts, error_types, samples

                with ThreadPoolExecutor(max_workers=THREADS, thread_name_prefix='broker-read-regression') as executor:
                    results = list(executor.map(read, range(THREADS)))
                total = Counter(); error_types = Counter(); samples = []
                for counts, errors, examples in results:
                    total.update(counts); error_types.update(errors); samples.extend(examples)
                observation = {'threads': THREADS, 'rounds_per_thread': ROUNDS,
                    'fixture_artifacts': FIXTURE_ARTIFACTS, 'expected_queries': THREADS * ROUNDS,
                    'counts': {name: total[name] for name in ('queries', 'exact', 'mismatches', 'exceptions', 'barrier_failures')},
                    'exceptions_by_type': dict(sorted(error_types.items())), 'samples': samples[:8],
                    'fixture_envelopes_hash': digest(originals), 'python': sys.version,
                    'sqlite_version': sqlite3.sqlite_version, 'sqlite_threadsafety': sqlite3.threadsafety,
                    'gil_enabled': sys._is_gil_enabled() if hasattr(sys, '_is_gil_enabled') else None,
                    'scope': 'Actual Broker._artifact/shared SQLite connection; exact full immutable envelopes; no mutex or database adapter substitution.'}
                self.observations.append(observation)
                self.assertEqual(total['queries'], THREADS * ROUNDS, observation)
                self.assertEqual(total['barrier_failures'], 0, observation)
                self.assertEqual(total['mismatches'] + total['exceptions'], 0, observation)
                self.assertEqual(total['exact'], THREADS * ROUNDS, observation)
                # Read-only threads must not manufacture an event/artifact or
                # mutate the immutable originals once all workers have joined.
                self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM events').fetchone()[0], before_events)
                for identity, original in expected.items(): self.assertEqual(broker._artifact(identity), original)
                self.assertEqual(broker.call(broker.admin_token, 'verify')['status'], 'PASS')
            finally:
                broker.close()


if __name__ == '__main__':
    unittest.main()
