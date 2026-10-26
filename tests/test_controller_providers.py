"""Offline host-dispatch checks; mocks do not establish a real API invocation."""
import unittest
from unittest.mock import patch

from controller_provider_support import Fixture
from trading_researcher.codec import Invalid
from trading_researcher.errors import Denied
from trading_researcher import openai_provider as openai


class ControllerProviderTests(unittest.TestCase):
    def setUp(self):
        self.fixture = Fixture()
        self.addCleanup(self.fixture.close)
        self.config = self.fixture.config
        self.route = self.fixture.route

    def case(self):
        return self.fixture.case()

    def result(self, case):
        return {'response': {'status': 'completed', 'provider_id': 'openai.responses/1',
            'output': case['output']}, 'usage': {'input_tokens': 100, 'output_tokens': 100, 'cost_units': 1}}

    def test_controller_derives_request_and_retains_one_dispatch(self):
        case = self.case()
        lease = case['client'].call('claim')['lease']
        with patch('trading_researcher.controller_providers._invoke', return_value=self.result(case)) as invoke:
            result = case['client'].call('invoke_auxiliary_provider', lease=lease, key='owned')
            again = case['client'].call('invoke_auxiliary_provider', lease=lease, key='owned')
        self.assertEqual(result, again)
        self.assertEqual(invoke.call_count, 1)
        adapter, request = invoke.call_args.args[:2]
        self.assertIs(type(adapter), openai.OpenAIResponsesProvider)
        self.assertEqual(request['tools'], [])
        self.assertEqual(request['model'], openai.MODEL)
        artifact = self.fixture.op('get_artifact', artifact_id=result['invocation_id'])
        self.assertEqual(artifact['body']['execution_path'], 'controller-direct-adapter/1')
        self.assertFalse(artifact['body']['scientific_readiness'])
        self.assertNotIn('key_file', str(artifact))
        with self.assertRaises(Denied):
            case['client'].call('finish_research_call', lease=lease, call_id=result['receipt']['call_id'], **self.result(case))

    def test_arbitrary_adapters_and_routes_are_not_rpc_arguments(self):
        case = self.case()
        lease = case['client'].call('claim')['lease']
        with self.assertRaises(Invalid):
            case['client'].call('invoke_auxiliary_provider', lease=lease, key='owned', provider='fixture')

    def test_controller_runner_preserves_formalization_boundary(self):
        from trading_researcher.auxiliary import run_auxiliary_once
        case = self.case()
        with patch('trading_researcher.controller_providers._invoke', return_value=self.result(case)):
            result = run_auxiliary_once(case['client'])
        self.assertTrue(result['accepted'], result)
        self.assertEqual(result['actual_independent_model_review'], 'UNVERIFIED')
        self.assertFalse(result['scientific_authority'])

    def test_real_child_missing_credential_retains_failure_without_network(self):
        case = self.case()
        lease = case['client'].call('claim')['lease']
        result = case['client'].call('invoke_auxiliary_provider', lease=lease, key='missing-credential')
        self.assertEqual(result['response']['status'], 'failed')
        self.assertEqual(result['response']['error_type'], 'FileNotFoundError')
        self.assertEqual(result['usage']['cost_units'], 0)
        artifact = self.fixture.op('get_artifact', artifact_id=result['invocation_id'])
        self.assertEqual(artifact['body']['response_status'], 'failed')
        self.assertFalse(artifact['body']['scientific_readiness'])
