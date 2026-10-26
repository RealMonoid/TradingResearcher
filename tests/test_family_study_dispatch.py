"""Family series expose only exact operator-owned request shapes."""
import tempfile
import unittest

from trading_researcher.coordination import Broker
from trading_researcher.codec import Invalid


class FamilyStudyDispatchTests(unittest.TestCase):
    def test_prepare_requires_exact_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            broker = Broker(directory)
            try:
                for operation in ('prepare_family_study', 'prepare_family_calibration'):
                    with self.subTest(operation=operation), self.assertRaisesRegex(Invalid, 'Exact study request required'):
                        broker.call(broker.admin_token, operation)
            finally: broker.close()
