"""Read-only calibration count command: explicit status, exit code and limits."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import test_calibration as support


class CalibrationCommandTests(unittest.TestCase):
    def invoke(self, request):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'request.json'
            path.write_text(json.dumps(request), encoding='utf-8')
            before = path.read_bytes()
            result = subprocess.run([sys.executable, '-B', '-m', 'trading_researcher',
                'assess-calibration-counts', '--request', str(path)],
                capture_output=True, text=True, timeout=20)
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual([item.name for item in Path(directory).iterdir()], ['request.json'])
            return result

    def test_complete_failed_and_incomplete_exit_codes(self):
        for variant, expected, code in [('complete', 'PASS_COUNTS_ONLY', 0),
                ('failed', 'FAIL_COUNTS_ONLY', 2), ('incomplete', 'NOT_ASSESSED', 2)]:
            with self.subTest(variant=variant):
                records = sum((support.observations(kind, 192 if kind == 'detection' else 0)
                               for kind in support.KINDS), [])
                if variant == 'failed':
                    records[:256] = support.observations('false_support', 18)
                elif variant == 'incomplete':
                    records.pop()
                result = self.invoke({'manifest': support.plan(), 'observations': records})
                self.assertEqual(result.returncode, code, result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report['status'], expected)
                self.assertFalse(report['scientific_readiness'])

    def test_unknown_request_fields_fail_without_a_success_report(self):
        result = self.invoke({'manifest': support.plan(), 'observations': [], 'approved': True})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, '')
        self.assertIn('Invalid', result.stderr)


if __name__ == '__main__':
    unittest.main()
