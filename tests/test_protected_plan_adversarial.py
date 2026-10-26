"""Independent isolation checks for the narrow host-private plan exception.

Host-owned records are synthetic. The downstream evidence consumers are mocked
to isolate ancestry routing; genuine certificate/qualification checks are covered
by the integration fixture, not claimed by these boundary tests.
"""
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.coordination import Broker
from trading_researcher.errors import Denied


class ProtectedPlanGuardTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.broker = Broker(temporary.name)
        self.addCleanup(self.broker.close)

    def owned(self, schema, data_class='assessment', refs=(), **body):
        with self.broker._transaction():
            return self.broker._save_artifact({
                'version': 'local-artifact/1', 'creator': 'controller',
                'origin': 'controller', 'data_class': data_class,
                'source_refs': list(refs), 'exposure': [],
                'authority': 'synthetic_guard_fixture_only',
                'body': {'schema': schema, **body}})

    def test_private_composition_exception_only_for_host_assessment_plan(self):
        private = self.owned('protected-data-binding/1')
        certificate = self.owned('composition-certificate/1', refs=[private['id']])
        for data_class in ('development', 'assessment'):
            compiled = self.owned('compiled-hypothesis/1', data_class, status='COMPILED')
            request = {'compiled_id': compiled['id'], 'composition_certificate_id': certificate['id']}
            with self.subTest(data_class=data_class), patch.object(
                    self.broker, '_composition_certificate_status', return_value={'fixture': 'consumer reached'}) as consumer:
                if data_class == 'assessment':
                    self.assertEqual(self.broker._plan_composition_evidence({}, request), {'fixture': 'consumer reached'})
                    consumer.assert_called_once_with({}, certificate['id'], compiled_id=compiled['id'])
                else:
                    with self.assertRaises(Denied):
                        self.broker._plan_composition_evidence({}, request)
                    consumer.assert_not_called()

    def test_private_data_use_exception_only_for_host_assessment_plan(self):
        private = self.owned('protected-data-binding/1')
        qualification = self.owned('data-use-assessment/1', refs=[private['id']])
        for data_class in ('development', 'assessment'):
            compiled = self.owned('compiled-hypothesis/1', data_class, status='COMPILED')
            request = {'compiled_id': compiled['id'], 'data_use_assessment_id': qualification['id']}
            with self.subTest(data_class=data_class), patch.object(
                    self.broker, '_inspect_data_use', return_value={'fixture': 'consumer reached'}) as consumer:
                if data_class == 'assessment':
                    self.assertEqual(self.broker._plan_data_use_evidence({}, request), {'fixture': 'consumer reached'})
                    consumer.assert_called_once_with({}, qualification['id'], compiled_id=compiled['id'])
                else:
                    with self.assertRaises(Denied):
                        self.broker._plan_data_use_evidence({}, request)
                    consumer.assert_not_called()

    def test_private_exception_never_permits_final_calibration_ancestry(self):
        private = self.owned('protected-data-binding/1')
        compiled = self.owned('compiled-hypothesis/1', status='COMPILED')
        for schema in ('evaluator-calibration-input/1', 'evaluator-calibration-attempt/1'):
            calibration = self.owned(schema)
            wrapper = self.owned('synthetic-wrapper/1', 'development', [calibration['id']])
            for field, method, schema_name, consumer_name in (
                    ('composition_certificate_id', '_plan_composition_evidence',
                     'composition-certificate/1', '_composition_certificate_status'),
                    ('data_use_assessment_id', '_plan_data_use_evidence',
                     'data-use-assessment/1', '_inspect_data_use')):
                artifact = self.owned(schema_name, refs=[private['id'], wrapper['id']])
                request = {'compiled_id': compiled['id'], field: artifact['id']}
                with self.subTest(schema=schema, field=field), patch.object(
                        self.broker, consumer_name, side_effect=AssertionError('Forbidden ancestry reached consumer')) as consumer:
                    with self.assertRaises(Denied):
                        getattr(self.broker, method)({}, request)
                    consumer.assert_not_called()


if __name__ == '__main__':
    unittest.main()
