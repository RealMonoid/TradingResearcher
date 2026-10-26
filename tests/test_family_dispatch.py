"""Family worlds have an owned operator boundary, including malformed requests."""
import tempfile
import unittest

from trading_researcher.coordination import Broker
from trading_researcher.codec import Invalid


class FamilyDispatchTests(unittest.TestCase):
    def test_family_operation_requires_exact_request(self):
        with tempfile.TemporaryDirectory() as directory:
            broker = Broker(directory)
            try:
                with self.assertRaisesRegex(Invalid, 'Exact population request required'):
                    broker.call(broker.admin_token, 'run_population_family')
            finally:
                broker.close()
