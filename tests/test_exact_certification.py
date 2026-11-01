"""Real owned source/blob conformance, without a research epoch or market rows."""
from pathlib import Path
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid
from trading_researcher.errors import Denied
from trading_researcher.exact_certification import ExactRuntimeBroker, AUTHORITY
from trading_researcher import exact_runtime
import test_revocations as legacy_revocations


class ExactCertificateTests(unittest.TestCase):
    def test_owned_source_package_certificate_and_registry_survive_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'registry'
            broker=ExactRuntimeBroker(path,clock=lambda:1000)
            try:
                saved=broker.certify_exact_runtime(broker.admin_token)
                self.assertEqual(saved['body']['status'],'CERTIFIED')
                self.assertEqual(saved['authority'],AUTHORITY)
                self.assertEqual(saved['data_class'],'operations')
                self.assertEqual(saved['creator'],saved['origin'],'controller')
                self.assertFalse(saved['body']['scientific_readiness'])
                certificate,bundle=broker._require_exact_qualification()
                self.assertEqual(certificate,saved)
                self.assertEqual(bundle,exact_runtime.read_bundle())
                self.assertEqual(len(bundle),26)
                package=broker._artifact(saved['body']['source_package_id'])
                self.assertEqual(package['authority'],'retained_source_not_certified')
                self.assertEqual(set(package['body']['files']),set(exact_runtime.FILES))
                self.assertEqual(broker.call(broker.admin_token,'verify')['status'],'PASS')
                self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM research_calls').fetchone()[0],0)
                self.assertEqual(broker._db.execute('SELECT COUNT(*) FROM research_epochs').fetchone()[0],0)
            finally:broker.close()
            broker=ExactRuntimeBroker(path,clock=lambda:1000,exact_certificate_id=saved['id'])
            try:
                retained,retained_bundle=broker._require_exact_qualification()
                self.assertEqual(retained,saved)
                self.assertEqual(retained_bundle,bundle)
                self.assertEqual(broker.call(broker.admin_token,'verify')['status'],'PASS')
            finally:broker.close()

    def test_failed_child_retains_source_and_gap_without_selecting_certificate(self):
        with tempfile.TemporaryDirectory() as temp:
            broker=ExactRuntimeBroker(temp,clock=lambda:1000)
            try:
                with patch.object(exact_runtime,'run_child',side_effect=Invalid('Forced test-only child failure')):
                    record=broker.certify_exact_runtime(broker.admin_token)
                self.assertEqual(record['body']['status'],'CERTIFICATION_GAP')
                self.assertEqual(record['body']['error']['type'],'Invalid')
                self.assertIn('Forced test-only',record['body']['error']['reason'])
                self.assertIsNone(record['body']['result'])
                self.assertEqual(broker._exact_package(record['body']['source_package_id']),exact_runtime.read_bundle())
                with self.assertRaises(Denied):broker._require_exact_qualification()
                self.assertEqual(broker.call(broker.admin_token,'verify')['status'],'PASS')
            finally:broker.close()

    def test_owned_child_result_json_types_are_not_coerced(self):
        # Controlled malformed owned records test exact protocol validation;
        # generic API clients cannot create controller-origin certificates.
        with tempfile.TemporaryDirectory() as temp:
            broker=ExactRuntimeBroker(temp,clock=lambda:1000)
            try:
                certificate=broker.certify_exact_runtime(broker.admin_token)
                for field,value in (('scientific_readiness',0),('failures',False),('errors',False),('skipped',False)):
                    changed=deepcopy(certificate);changed.pop('id')
                    changed['body']['result']['result'][field]=value
                    with broker._transaction():injected=broker._save_artifact(changed)
                    broker._exact_certificate_id=injected['id']
                    with self.subTest(field=field),self.assertRaises(Invalid):
                        broker._require_exact_qualification()
            finally:broker.close()


class ExactLegacyRevocationTests(legacy_revocations.RevocationTests):
    """Run the existing three D083 expectations through the new broker MRO."""
    def setUp(self):
        with patch.object(legacy_revocations,'Broker',ExactRuntimeBroker):
            super().setUp()


if __name__=='__main__':unittest.main()
