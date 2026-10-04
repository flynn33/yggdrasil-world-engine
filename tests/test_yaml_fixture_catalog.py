from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_fixture_catalog as fixture_check
import test_fixture_catalog as fixture_tests
from check_machine_readable_artifacts import UniqueKeyLoader


class YamlInstanceLoadingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, text: str, suffix: str = ".yaml") -> Path:
        path = self.root / ("instance" + suffix)
        path.write_text(text, encoding="utf-8")
        return path

    def test_yaml_and_yml_preserve_json_scalar_types(self):
        source = 'enabled: true\ndisabled: false\ncount: 3\nratio: 1.25\nabsent: null\ntext: "3"\n'
        for suffix in (".yaml", ".yml"):
            with self.subTest(suffix=suffix):
                result = fixture_check.load_instance(self.write(source, suffix))
                self.assertEqual(
                    {"enabled": True, "disabled": False, "count": 3, "ratio": 1.25, "absent": None, "text": "3"},
                    result,
                )
                self.assertIs(type(result["enabled"]), bool)
                self.assertIs(type(result["count"]), int)
                self.assertIs(type(result["ratio"]), float)
                self.assertIs(type(result["text"]), str)

    def test_duplicate_yaml_mapping_members_are_rejected_at_every_depth(self):
        for source in ("value: 1\nvalue: 2\n", "record:\n  value: 1\n  value: 2\n"):
            with self.subTest(source=source):
                with self.assertRaisesRegex(yaml.YAMLError, "duplicate key"):
                    fixture_check.load_instance(self.write(source))

    def test_yaml_values_without_json_representations_are_rejected(self):
        for source in (
            "1: value\n",
            "true: value\n",
            "date: 2026-10-03\n",
            "bytes: !!binary aGVsbG8=\n",
            "members: !!set {first: null}\n",
            "pairs: !!pairs [{first: 1}]\n",
            "ordered: !!omap [{first: 1}]\n",
            "number: .nan\n",
            "number: .inf\n",
            "number: -.inf\n",
            "value: &loop [*loop]\n",
        ):
            with self.subTest(source=source):
                with self.assertRaises((TypeError, ValueError, yaml.YAMLError)):
                    fixture_check.load_instance(self.write(source))

    def test_nonrecursive_yaml_aliases_preserve_values(self):
        result = fixture_check.load_instance(self.write("first: &record {value: 3}\nsecond: *record\n"))
        self.assertEqual({"first": {"value": 3}, "second": {"value": 3}}, result)

    def test_json_loader_behavior_is_preserved(self):
        path = self.write('{"enabled": false, "count": 3, "text": "true", "members": [null, 1.25]}\n', ".json")
        self.assertEqual(fixture_check.load_json(path), fixture_check.load_instance(path))

    def test_unsupported_instance_extension_is_rejected(self):
        with self.assertRaises(ValueError):
            fixture_check.load_instance(self.write("value: 3\n", ".txt"))


class YamlFixtureExecutionTests(unittest.TestCase):
    def setUp(self):
        self.workspace = fixture_tests.FixtureCatalogTests("test_valid_binding_selects_instance_in_document")
        self.workspace.setUp()
        self.addCleanup(self.workspace.doCleanups)

    def write_yaml(self, relative: str, value) -> None:
        path = self.workspace.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")

    def test_original_json_fixture_still_passes(self):
        errors, results = self.workspace.run_check()
        self.assertEqual([], errors)
        self.assertEqual("accept", results[0]["result"])
        self.assertEqual("examples/record.json", results[0]["path"])

    def test_yaml_fixture_selects_escaped_pointer_and_subschema(self):
        for suffix in ("yaml", "yml"):
            with self.subTest(suffix=suffix):
                relative = "examples/record." + suffix
                self.write_yaml(relative, {"a/b": {"~value": 7}})
                self.workspace.fixtures = [self.workspace.fixture(
                    path=relative, instance_pointer="/a~1b/~0value",
                    schema_id=self.workspace.SCHEMA_ID + "#/properties/value",
                )]
                errors, results = self.workspace.run_check()
                self.assertEqual([], errors)
                self.assertEqual([{"fixture_id": "record.positive", "path": relative, "result": "accept"}], results)

    def test_yaml_reject_witness_requires_exact_reason_and_locations(self):
        relative = "examples/record.yaml"
        self.write_yaml(relative, {"record": {"value": -1}})
        expected = {
            "error_id": "JSON_SCHEMA_MINIMUM",
            "instance_pointer": "/value",
            "schema_pointer": "/properties/value/minimum",
        }
        self.workspace.fixtures = [self.workspace.fixture(
            path=relative, category="reject", expected_result="reject", expected_errors=[expected],
        )]
        errors, results = self.workspace.run_check()
        self.assertEqual([], errors)
        self.assertEqual("reject", results[0]["result"])
        for field, wrong in (
            ("error_id", "JSON_SCHEMA_TYPE"),
            ("instance_pointer", "/other"),
            ("schema_pointer", "/properties/value/type"),
        ):
            with self.subTest(field=field):
                self.workspace.fixtures[0]["expected_errors"] = [{**expected, field: wrong}]
                errors, _ = self.workspace.run_check()
                self.assertTrue(any("expected reject" in error for error in errors), errors)

    def test_duplicate_yaml_mapping_cannot_be_an_expected_schema_rejection(self):
        path = self.workspace.root / "examples/record.yaml"
        path.write_text("record:\n  value: -1\n  value: 1\n", encoding="utf-8")
        self.workspace.fixtures = [self.workspace.fixture(
            path="examples/record.yaml", category="reject", expected_result="reject",
            expected_errors=[{
                "error_id": "JSON_SCHEMA_MINIMUM",
                "instance_pointer": "/value",
                "schema_pointer": "/properties/value/minimum",
            }],
        )]
        errors, results = self.workspace.run_check()
        self.assertTrue(any("duplicate key" in error for error in errors), errors)
        self.assertEqual([], results)


class ModuleCapabilityYamlSchemaTests(unittest.TestCase):
    SCHEMA_PATH = "data/schemas/module_capability_manifest_schema.json"
    SOURCE_PATH = "data/module_capability/module_capability_manifest_schema.yaml"
    MANIFEST_NAMES = (
        "ash_pattern_engine", "artifact_engine", "cosmology_engine", "creature_engine",
        "myth_engine", "narrative_engine", "perception_engine", "prophecy_engine",
        "quest_engine", "realm_engine",
    )

    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads((ROOT / cls.SCHEMA_PATH).read_text(encoding="utf-8-sig"))
        cls.source = yaml.load((ROOT / cls.SOURCE_PATH).read_text(encoding="utf-8-sig"), Loader=UniqueKeyLoader)
        cls.validator = Draft202012Validator(cls.schema)
        cls.manifest = yaml.load(
            (ROOT / "data/module_capability/manifests/ash_pattern_engine.yaml").read_text(encoding="utf-8-sig"),
            Loader=UniqueKeyLoader,
        )

    def signatures(self, instance):
        return sorted(
            (fixture_check.error_signature(leaf) for error in self.validator.iter_errors(instance)
             for leaf in fixture_check.leaf_errors(error)),
            key=fixture_check.signature_key,
        )

    def assert_exact_error(self, instance, error_id, instance_pointer, schema_pointer, **details):
        self.assertEqual([{
            "error_id": error_id, "instance_pointer": instance_pointer, "schema_pointer": schema_pointer, **details,
        }], self.signatures(instance))

    def test_schema_is_valid_and_required_fields_match_canonical_source(self):
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual(self.source["canonical_validation_rules"]["required_fields"], self.schema["required"])

    def test_all_ten_applied_yaml_manifests_validate(self):
        for name in self.MANIFEST_NAMES:
            with self.subTest(manifest=name):
                instance = fixture_check.load_instance(ROOT / f"data/module_capability/manifests/{name}.yaml")
                self.assertEqual([], self.signatures(instance))

    def test_each_required_root_field_has_an_exact_missing_property_witness(self):
        for field in self.source["canonical_validation_rules"]["required_fields"]:
            with self.subTest(field=field):
                instance = copy.deepcopy(self.manifest)
                del instance[field]
                self.assert_exact_error(instance, "JSON_SCHEMA_REQUIRED", "", "/required", missing_properties=[field])

    def test_root_requires_an_object(self):
        for instance in ([], "manifest", 1, True, None):
            with self.subTest(instance=instance):
                self.assert_exact_error(instance, "JSON_SCHEMA_TYPE", "", "/type")

    def test_root_enum_fields_reject_unknown_values(self):
        for field in ("module_classification", "authority_class", "activation_state"):
            with self.subTest(field=field):
                instance = copy.deepcopy(self.manifest)
                instance[field] = "unknown"
                self.assert_exact_error(instance, "JSON_SCHEMA_ENUM", f"/{field}", f"/properties/{field}/enum")

    def test_every_source_enum_value_is_accepted_by_its_declared_field(self):
        for family, collection, field in (
            ("module_classification", None, "module_classification"),
            ("authority_class", None, "authority_class"),
            ("activation_state", None, "activation_state"),
            ("dependency_strength", "requires_capabilities", "dependency_strength"),
            ("delegation_rule", "delegable_compatible_responsibilities", "delegation_rule"),
            ("suppression_reason", "suppression_conditions", "reason"),
            ("external_capability_class", "compatible_external_capabilities", "capability_class"),
        ):
            for value in self.source["classification_enums"][family]:
                with self.subTest(family=family, value=value):
                    instance = copy.deepcopy(self.manifest)
                    target = instance if collection is None else instance[collection][0]
                    target[field] = value
                    self.assertEqual([], self.signatures(instance))

    def test_root_integer_fields_reject_strings_and_booleans(self):
        for field in ("activation_priority", "dependency_order_index"):
            for value in ("3", True):
                with self.subTest(field=field, value=value):
                    instance = copy.deepcopy(self.manifest)
                    instance[field] = value
                    self.assert_exact_error(instance, "JSON_SCHEMA_TYPE", f"/{field}", f"/properties/{field}/type")

    def test_root_string_fields_reject_nonstring_values(self):
        descriptors = self.source["core_schema"]["ModuleCapabilityManifest"]
        for field, descriptor in descriptors.items():
            if descriptor != "string":
                continue
            with self.subTest(field=field):
                instance = copy.deepcopy(self.manifest)
                instance[field] = 3
                self.assert_exact_error(instance, "JSON_SCHEMA_TYPE", f"/{field}", f"/properties/{field}/type")

    def test_root_collections_reject_nonarrays_and_wrong_member_types(self):
        descriptors = self.source["core_schema"]["ModuleCapabilityManifest"]
        for field, descriptor in descriptors.items():
            if not isinstance(descriptor, list):
                continue
            with self.subTest(field=field, failure="collection"):
                instance = copy.deepcopy(self.manifest)
                instance[field] = False
                self.assert_exact_error(instance, "JSON_SCHEMA_TYPE", f"/{field}", f"/properties/{field}/type")
            with self.subTest(field=field, failure="member"):
                instance = copy.deepcopy(self.manifest)
                instance[field] = [False]
                self.assert_exact_error(instance, "JSON_SCHEMA_TYPE", f"/{field}/0", f"/properties/{field}/items/type")

    def test_nested_member_types_have_exact_witnesses(self):
        for collection, field, value in (
            ("provides_capabilities", "truth_sensitive", "true"),
            ("provides_capabilities", "scope", 3),
            ("requires_capabilities", "rationale", False),
            ("consumes_state", "required", "true"),
            ("emits_state", "persistence", []),
            ("delegable_compatible_responsibilities", "guardrails", False),
            ("compatible_external_capabilities", "constraints", False),
        ):
            with self.subTest(collection=collection, field=field):
                instance = copy.deepcopy(self.manifest)
                instance[collection][0][field] = value
                self.assert_exact_error(
                    instance, "JSON_SCHEMA_TYPE", f"/{collection}/0/{field}",
                    f"/properties/{collection}/items/properties/{field}/type",
                )

    def test_nested_enum_fields_reject_unknown_values(self):
        for collection, field in (
            ("requires_capabilities", "dependency_strength"),
            ("delegable_compatible_responsibilities", "delegation_rule"),
            ("suppression_conditions", "reason"),
            ("compatible_external_capabilities", "capability_class"),
        ):
            with self.subTest(collection=collection, field=field):
                instance = copy.deepcopy(self.manifest)
                instance[collection][0][field] = "unknown"
                self.assert_exact_error(
                    instance, "JSON_SCHEMA_ENUM", f"/{collection}/0/{field}",
                    f"/properties/{collection}/items/properties/{field}/enum",
                )

    def test_foundational_and_structural_truth_require_a_nondelegable_responsibility(self):
        for authority in ("foundational_truth", "structural_runtime_truth"):
            with self.subTest(authority=authority):
                instance = copy.deepcopy(self.manifest)
                instance["authority_class"] = authority
                instance["non_delegable_responsibilities"] = []
                self.assert_exact_error(
                    instance, "JSON_SCHEMA_MINITEMS", "/non_delegable_responsibilities",
                    "/allOf/0/then/properties/non_delegable_responsibilities/minItems",
                )

    def test_source_does_not_require_nonempty_arrays_for_other_authorities(self):
        instance = copy.deepcopy(self.manifest)
        instance["authority_class"] = "manifestation_logic"
        for field, descriptor in self.source["core_schema"]["ModuleCapabilityManifest"].items():
            if isinstance(descriptor, list):
                instance[field] = []
        self.assertEqual([], self.signatures(instance))

    def test_source_does_not_close_objects_or_require_nested_members(self):
        instance = copy.deepcopy(self.manifest)
        instance["future_root_field"] = {"value": True}
        for field, descriptor in self.source["core_schema"]["ModuleCapabilityManifest"].items():
            if isinstance(descriptor, list) and descriptor and isinstance(descriptor[0], dict):
                instance[field] = [{"future_member": "allowed"}]
        self.assertEqual([], self.signatures(instance))

    def test_scope_strings_are_not_restricted_by_an_unbound_enum(self):
        instance = copy.deepcopy(self.manifest)
        instance["owned_scope"] = ["future_scope"]
        instance["provides_capabilities"][0]["scope"] = "future_scope"
        instance["requires_capabilities"][0]["scope"] = "future_scope"
        self.assertEqual([], self.signatures(instance))

    def test_source_string_declarations_do_not_add_a_nonempty_constraint(self):
        instance = copy.deepcopy(self.manifest)
        for field, descriptor in self.source["core_schema"]["ModuleCapabilityManifest"].items():
            if descriptor == "string":
                instance[field] = ""
        self.assertEqual([], self.signatures(instance))


if __name__ == "__main__":
    unittest.main()
