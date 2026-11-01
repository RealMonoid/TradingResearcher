"""A technical grant cannot conceal operations knowledge or protected ancestry."""
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import patch

from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher.data_use import prior_knowledge, protected_knowledge_gaps
from trading_researcher.errors import Conflict, Denied
from trading_researcher.features import PROFILE, SCOPE


class FeatureReleaseKnowledgeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.broker = Broker(temporary.name, clock=lambda: 1000)
        self.addCleanup(self.broker.close)

    def save(self, body, *, creator='controller', origin='source', data_class='development',
             authority='fixture-metadata-only', sources=(), exposure=()):
        envelope = {'version': 'local-artifact/1', 'creator': creator, 'origin': origin,
                    'data_class': data_class, 'authority': authority, 'source_refs': sorted(sources),
                    'exposure': sorted(exposure), 'body': deepcopy(body)}
        with self.broker._transaction():
            return self.broker._save_artifact(envelope)

    def altered(self, original, mutate):
        envelope = deepcopy(original)
        envelope.pop('id')
        mutate(envelope)
        with self.broker._transaction():
            return self.broker._save_artifact(envelope)

    def chain(self, *, certificate_sources=(), grant_exposure=()):
        catalog = self.save({'schema': 'feature-catalog/1', 'features': {}})
        snapshot = self.save({'schema': 'data-snapshot/1', 'catalog_id': catalog['id'],
            'manifest': {'partition': 'development'}}, sources=[catalog['id']])
        definition = self.save({'schema': 'feature-definitions/1',
            'input_refs': sorted([snapshot['id'], catalog['id']])}, sources=[snapshot['id'], catalog['id']])
        certificate = self.save({'schema': 'feature-certificate/1', 'profile': PROFILE,
            'status': 'CERTIFIED', 'data_snapshot_id': snapshot['id'], 'definitions_id': definition['id'],
            'scientific_readiness': False}, origin='controller', authority=SCOPE['authority'],
            sources=[snapshot['id'], definition['id'], *certificate_sources])
        grant = self.save({'schema': 'feature-evidence-release/1', 'certificate_id': certificate['id'],
            'data_snapshot_id': snapshot['id'], 'definitions_id': definition['id'],
            'target_epoch': 7, 'created_at': 1000, 'scientific_readiness': False},
            origin='controller', data_class='operations', authority='development_feature_input_release_only',
            sources=[certificate['id'], snapshot['id'], definition['id']],
            exposure=[certificate['id'], snapshot['id'], definition['id'], *grant_exposure])
        return grant, certificate, snapshot, definition, catalog

    def not_exempt(self, artifact):
        try:
            result = prior_knowledge(self.broker, artifact)
        except (Invalid, Denied, Conflict):
            return
        self.assertNotIn(artifact['id'], result['technical_provenance_ids'])
        self.assertIn(artifact['id'], result['operations_knowledge_ids'])

    def test_owned_exact_grant_is_technical_without_status_or_source_scans(self):
        grant, *parents = self.chain()
        with patch.object(self.broker, '_feature_certificate_status', side_effect=AssertionError('Classification is not recertification')), \
                patch.object(self.broker, '_read_blob_bytes', side_effect=AssertionError('No source reads for provenance')):
            result = prior_knowledge(self.broker, grant)
        self.assertEqual(result['technical_provenance_ids'], [grant['id']])
        self.assertEqual(result['operations_knowledge_ids'], [])
        self.assertEqual(set(result['artifact_ids']), {grant['id'], *(item['id'] for item in parents)})
        self.assertEqual(protected_knowledge_gaps(result), [])

    def test_technical_wrapper_still_traverses_operations_and_protected_source_edges(self):
        operational = self.save({'schema': 'execution-observations/1', 'text': 'Synthetic fills'},
                                creator='operator', data_class='operations')
        protected = self.save({'schema': 'reserved-observations/1'}, creator='operator', data_class='assessment')
        grant, *_ = self.chain(certificate_sources=[operational['id'], protected['id']])
        result = prior_knowledge(self.broker, grant)
        self.assertEqual(result['technical_provenance_ids'], [grant['id']])
        self.assertEqual(result['operations_knowledge_ids'], [operational['id']])
        self.assertEqual(result['protected_knowledge_ids'], [protected['id']])
        self.assertEqual(protected_knowledge_gaps(result), [
            'PROTECTED_KNOWLEDGE_IN_CANDIDATE_ANCESTRY', 'OPERATIONS_KNOWLEDGE_REQUIRES_CONTROLLED_IMPORT'])

    def test_exposure_edges_and_opaque_annotations_survive_technical_classification(self):
        operational = self.save({'schema': 'operational-knowledge/1'}, creator='operator', data_class='operations')
        protected = self.save({'schema': 'protected-knowledge/1'}, creator='operator', data_class='assessment')
        grant, *_ = self.chain(grant_exposure=[operational['id'], protected['id'], 'opaque:prior-observation'])
        result = prior_knowledge(self.broker, grant)
        self.assertEqual(result['technical_provenance_ids'], [grant['id']])
        self.assertEqual(result['operations_knowledge_ids'], [operational['id']])
        self.assertEqual(result['protected_knowledge_ids'], [protected['id']])
        self.assertEqual(result['unresolved_exposure_refs'], ['opaque:prior-observation'])

    def test_schema_owner_authority_and_exact_body_cannot_be_forged(self):
        grant, *_ = self.chain()
        mutations = [
            lambda a: a.update(creator='operator'), lambda a: a.update(origin='source'),
            lambda a: a.update(authority='implementation_conformance_only'),
            lambda a: a.update(version='local-artifact/2'),
            lambda a: a['body'].update(schema='feature-evidence-release/2'),
            lambda a: a['body'].update(scientific_readiness=True),
            lambda a: a['body'].update(scientific_readiness=0),
            lambda a: a['body'].update(target_epoch=True), lambda a: a['body'].update(target_epoch=-1),
            lambda a: a['body'].update(created_at=True), lambda a: a['body'].update(created_at=-1),
            lambda a: a['body'].update(text='Arbitrary operational observations cannot hide in a grant'),
            lambda a: a['body'].pop('created_at'),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.not_exempt(self.altered(grant, mutate))

    def test_malformed_body_and_identity_types_fail_closed(self):
        grant, *_ = self.chain()
        for malformed in (None, [], 'not a grant', 1):
            with self.subTest(body=malformed):
                self.not_exempt(self.altered(grant, lambda a: a.update(body=malformed)))
        for name in ('certificate_id', 'data_snapshot_id', 'definitions_id'):
            for malformed in (None, [], '', 'not-a-sha256'):
                with self.subTest(field=name, value=malformed):
                    self.not_exempt(self.altered(grant, lambda a: a['body'].update({name: malformed})))

    def test_exact_sorted_refs_and_distinct_identity_roles_are_required(self):
        grant, certificate, snapshot, definition, _ = self.chain()
        extra = self.save({'schema': 'operations-extra/1'}, creator='operator', data_class='operations')
        mutations = [
            lambda a: a.update(source_refs=[]),
            lambda a: a.update(source_refs=list(reversed(a['source_refs']))),
            lambda a: a['source_refs'].append(a['source_refs'][0]),
            lambda a: a['source_refs'].append(extra['id']),
            lambda a: a['body'].update(definitions_id=snapshot['id']),
            lambda a: a['body'].update(certificate_id=definition['id'], definitions_id=certificate['id']),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                self.not_exempt(self.altered(grant, mutate))

    def test_linked_metadata_must_match_ownership_class_and_grant_ids(self):
        grant, certificate, snapshot, definition, _ = self.chain()
        mutations = [
            (certificate['id'], lambda a: a.update(creator='operator')),
            (certificate['id'], lambda a: a.update(data_class='assessment')),
            (certificate['id'], lambda a: a.update(authority='supplied_source_not_certified')),
            (certificate['id'], lambda a: a['body'].update(profile='different-profile/1')),
            (certificate['id'], lambda a: a['body'].update(status='CERTIFICATION_GAP')),
            (certificate['id'], lambda a: a['body'].update(definitions_id=snapshot['id'])),
            (certificate['id'], lambda a: a['body'].update(data_snapshot_id=definition['id'])),
            (snapshot['id'], lambda a: a.update(origin='controller')),
            (snapshot['id'], lambda a: a.update(data_class='assessment')),
            (snapshot['id'], lambda a: a['body'].update(schema='other-snapshot/1')),
            (definition['id'], lambda a: a.update(creator='operator')),
            (definition['id'], lambda a: a.update(data_class='assessment')),
            (definition['id'], lambda a: a['body'].update(input_refs=[])),
            (definition['id'], lambda a: a['body'].update(input_refs=None)),
            (certificate['id'], lambda a: a.update(body=None)),
        ]
        original = self.broker._artifact
        for index, (identity, mutate) in enumerate(mutations):
            changed = deepcopy(original(identity))
            mutate(changed)
            def artifact(requested):
                return deepcopy(changed) if requested == identity else original(requested)
            with self.subTest(index=index), patch.object(self.broker, '_artifact', artifact):
                self.not_exempt(grant)


if __name__ == '__main__':
    unittest.main()
