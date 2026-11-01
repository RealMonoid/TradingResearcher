"""Genuine native D098 fixture; provider replies/counts remain synthetic."""
from unittest.mock import patch

import exact_execution_support as legacy
from trading_researcher.exact_execution_v2 import ExactExecutionBrokerV2
from trading_researcher.exact_runtime_v2 import RESOURCE_CONTRACT


class ExactExecutionV2Fixture(legacy.ExactExecutionFixture):
    def __init__(self, **kwargs):
        # Select the new broker before normalization, certification, profiles,
        # finite epoch binding and every invocation; never reopen an old epoch.
        with patch.object(legacy, 'ExactExecutionBroker', ExactExecutionBrokerV2):
            super().__init__(**kwargs)

    def spec(self, kind):
        result = super().spec(kind)
        result['research_inputs']['resource_contract'] = RESOURCE_CONTRACT
        return result
