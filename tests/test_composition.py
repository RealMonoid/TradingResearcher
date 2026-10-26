"""Owned composition conformance cannot be asserted through generic sources."""
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from trading_researcher.codec import Invalid
from trading_researcher.coordination import Broker
from trading_researcher import composition
from trading_researcher import binding, certification
from trading_researcher.codec import decode, digest


class CompositionAdmissionTests(unittest.TestCase):
    def test_independent_fixed_compiler_expectations(self):
        checked=composition.fixed_checks()
        self.assertEqual(checked['fixture_sha256'],composition.FIXTURE_SHA256)
        self.assertEqual(len(checked['passed_cases']),26)

    def test_self_consistent_but_false_metadata_fails_independent_expectations(self):
        original=composition.compile_payload
        for field in ('unit','parameter_paths','feature_refs'):
            def forged(payload):
                value=deepcopy(original(payload))
                value['programs']['condition_program'][field]='fabricated'
                return value
            with self.subTest(field=field),patch.object(composition,'compile_payload',side_effect=forged):
                with self.assertRaises(Invalid):composition.fixed_checks()

    def test_isolated_validator_rejects_a_corrupted_binding_driver(self):
        bundle={**certification.read_bundle(),binding.DRIVER:(binding.ROOT/binding.DRIVER).read_bytes(),
            composition.DRIVER:(composition.ROOT/composition.DRIVER).read_bytes(),
            composition.FIXTURE:(composition.ROOT/composition.FIXTURE).read_bytes()}
        first=decode(bundle[composition.FIXTURE])['cases'][0]
        original=bundle[binding.DRIVER]
        needle=b"    return {'request':deepcopy(request),'candidate_hash':digest(candidate),'programs':programs,"
        self.assertEqual(original.count(needle),1)
        bundle[binding.DRIVER]=original.replace(needle,b"    programs['condition_program']['unit']='forged'\n"+needle)
        with self.assertRaises(Invalid):
            composition.run_composition_child(bundle,first['payload'],digest(first['expected']))

    def test_changed_installed_validator_or_expectations_cannot_remain_current(self):
        # Status-only fixture: ownership/dependency validation has separate real
        # integration coverage; the installed-file currency check runs normally.
        retained={name:(composition.ROOT/name).read_bytes() for name in (composition.DRIVER,composition.FIXTURE)}
        artifact={'id':'fixture:certificate','creator':'controller','origin':'controller','authority':composition.AUTHORITY,
            'body':{'schema':composition.SCHEMA,'profile':composition.PROFILE,'status':'CONFORMANT',
                'compiled_id':'fixture:compiled','source_package_id':'fixture:package','report':{'environment':{}}}}
        class StatusFixture(composition.CompositionCertification):
            def _artifact(self,identity):return artifact
            def _require_usable_dependencies(self,identity):pass
            def _composition_inputs(self,actor,identity):pass
            def _load_composition_package(self,identity):return retained
        for changed in retained:
            with self.subTest(changed=changed),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                for name,raw in retained.items():
                    path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
                    path.write_bytes(raw+(b'\n' if name==changed else b''))
                with patch.object(composition,'ROOT',root),patch.object(composition,'_environment_current',return_value=True):
                    current=StatusFixture()._composition_certificate_status({},artifact['id'])
                self.assertEqual(current['status'],'STALE_VALIDATOR')
                self.assertEqual(current['composition_conformance'],'NOT_SATISFIED')

    def test_composition_namespaces_are_reserved(self):
        with tempfile.TemporaryDirectory() as directory:
            broker=Broker(directory)
            try:
                for schema in ('composition-certificate/1','composition-input/1','composition-source-package/1'):
                    with self.subTest(schema=schema),self.assertRaises(Invalid):
                        broker.call(broker.admin_token,'add_source',body={'schema':schema},data_class='development')
            finally:broker.close()


if __name__=='__main__':unittest.main()
