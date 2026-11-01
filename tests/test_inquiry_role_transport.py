"""Complete approved scalar contract delivery before and after formalization."""
from copy import deepcopy
from pathlib import Path
import unittest

from inquiry_resource_support import Fixture
from trading_researcher.auxiliary import request_for
from trading_researcher.auxiliary_views import REUSE_SCOPE, present, restore
from trading_researcher.codec import decode
from trading_researcher.errors import Denied
from trading_researcher.inquiry import resources
from trading_researcher.openai_provider import wire_request


class InquiryRoleTransportTests(unittest.TestCase):
    def fixture(self):
        value = Fixture(create=False)
        self.addCleanup(value.close)
        for role in value.role_profiles.values():
            role['profile']['generation_parameters']['openai_responses']['bounded_math_scope'] = REUSE_SCOPE
        value.policy = value.broker.prepare_resource_disposition(value.token,
            role_profiles=value.role_profiles, discovery_run_ids=value.policy['discovery_run_ids'])
        return value

    def test_both_roles_must_freeze_the_same_approved_reuse_selection(self):
        f = self.fixture()
        f.policy['role_profiles']['semantic-review/v1']['profile']['generation_parameters']['openai_responses'].pop('bounded_math_scope')
        with self.assertRaises(Denied):
            f.create_epoch()
        self.assertEqual(f.broker._db.execute('SELECT COUNT(*) FROM research_epochs').fetchone()[0], 0)

    def test_full_scalar_math_and_activation_sources_arrive_before_candidate(self):
        f = self.fixture()
        f.create_epoch()
        f.discover()
        spec, _ = f.auxiliary('formalization/v1')
        lease = f.clients['formal'].call('claim')['lease']
        packet = f.clients['formal'].call('auxiliary_input', lease=lease)
        self.assertEqual(packet['expression_contract']['text'], Path('docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md').read_text(encoding='utf-8'))
        request = request_for(spec, packet)
        config = spec['research_call_profile']['generation_parameters']['openai_responses']
        view = decode(wire_request(request, config)['input'][1]['content'])
        self.assertEqual(view['activation_contract']['text'], Path('docs/architecture/20_BOUNDED_MATH_REUSE.md').read_text(encoding='utf-8'))
        self.assertEqual(restore(view), packet)
        self.assertNotIn('candidate', packet)
        binding = f.op('inspect_research_epoch', epoch_id=f.epoch)['request']['inquiry_binding']['installed_sources']
        self.assertIn('docs/architecture/18_BOUNDED_MATH_PRIMITIVES.md', binding)
        self.assertIn('docs/architecture/20_BOUNDED_MATH_REUSE.md', binding)
        self.assertEqual(len(binding), 117)

    def test_unselected_scalar_transport_does_not_silently_activate_reuse(self):
        f = Fixture()
        self.addCleanup(f.close)
        f.discover()
        spec, _ = f.auxiliary('formalization/v1')
        lease = f.clients['formal'].call('claim')['lease']
        packet = f.clients['formal'].call('auxiliary_input', lease=lease)
        self.assertNotIn('expression_contract', packet)
        config = spec['research_call_profile']['generation_parameters']['openai_responses']
        view = decode(wire_request(request_for(spec, packet), config)['input'][1]['content'])
        self.assertNotIn('activation_contract', view)


if __name__ == '__main__':
    unittest.main()
