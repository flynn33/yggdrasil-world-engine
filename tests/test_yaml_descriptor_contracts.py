from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_fixture_catalog as fixtures
import check_yaml_descriptor_contracts as descriptors


class YamlDescriptorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = fixtures.load_instance(ROOT / descriptors.BUNDLE_PATH)
        cls.expectations = fixtures.load_json(ROOT / descriptors.CASE_EXPECTATIONS_PATH)
        cls.sources = {
            grammar: fixtures.load_instance(ROOT / spec["source"])
            for grammar, spec in descriptors.GRAMMARS.items()
        }

    def pattern(self):
        return copy.deepcopy(self.bundle["positive"]["pattern_minimal"])

    def module(self):
        return copy.deepcopy(self.bundle["positive"]["module_minimal"])

    def assert_semantic_error(self, instance, grammar, error_id, instance_pointer, rule):
        expected = [{
            "error_id": "YAML_DESCRIPTOR_" + error_id,
            "instance_pointer": instance_pointer,
            "schema_pointer": "/x-ywe-semantic-rules/" + rule,
        }]
        self.assertEqual(expected, descriptors.descriptor_errors(instance, grammar, ROOT))
        self.assertEqual(expected, descriptors.descriptor_semantic_errors(instance, grammar, ROOT))

    def test_all_owned_schemas_pass_the_repository_meta_schema(self):
        for relative in descriptors.SCHEMA_PATHS:
            with self.subTest(schema=relative):
                schema = fixtures.load_json(ROOT / relative)
                self.assertEqual(fixtures.DIALECT, schema["$schema"])
                Draft202012Validator.check_schema(schema)

    def test_exact_two_root_grammars_declare_owned_semantic_rules(self):
        for grammar, spec in descriptors.GRAMMARS.items():
            with self.subTest(grammar=grammar):
                schema = fixtures.load_json(ROOT / spec["schema"])
                self.assertEqual(spec["schema_id"], schema["$id"])
                self.assertEqual(grammar, schema["x-ywe-descriptor-grammar"])
                self.assertEqual("YWE-REQ-0027", schema["x-ywe-requirement-id"])
                self.assertEqual(spec["source"], schema["x-ywe-source-ref"])
                for rule in schema["x-ywe-semantic-rules"].values():
                    self.assertEqual("YWE-REQ-0027", rule["requirement_id"])

    def test_both_original_descriptor_roots_pass_both_stages(self):
        for grammar, instance in self.sources.items():
            with self.subTest(grammar=grammar):
                self.assertEqual([], list(descriptors.descriptor_validator(grammar, ROOT).iter_errors(instance)))
                self.assertEqual([], descriptors.descriptor_semantic_errors(instance, grammar, ROOT))
                self.assertEqual([], descriptors.descriptor_errors(instance, grammar, ROOT))

    def test_every_bundle_case_matches_its_complete_recorded_witnesses(self):
        self.assertEqual(42, len(self.expectations["cases"]))
        for case in self.expectations["cases"]:
            with self.subTest(case=case["instance_pointer"]):
                instance = fixtures.json_pointer(self.bundle, case["instance_pointer"])
                actual = descriptors.descriptor_errors(instance, case["grammar"], ROOT)
                self.assertEqual(
                    sorted(case["expected_errors"], key=fixtures.signature_key),
                    actual,
                )
                self.assertEqual(case["expected_result"], "reject" if actual else "accept")

    def test_semantic_witnesses_resolve_to_declared_schema_annotations(self):
        witnessed_cases = 0
        for case in self.expectations["cases"]:
            semantic = [
                error for error in case["expected_errors"]
                if error["error_id"].startswith("YAML_DESCRIPTOR_")
            ]
            if not semantic:
                continue
            witnessed_cases += 1
            schema = fixtures.load_json(ROOT / descriptors.GRAMMARS[case["grammar"]]["schema"])
            instance = fixtures.json_pointer(self.bundle, case["instance_pointer"])
            for error in semantic:
                with self.subTest(case=case["instance_pointer"], error=error):
                    declaration = fixtures.json_pointer(schema, error["schema_pointer"])
                    self.assertEqual("YWE-REQ-0027", declaration["requirement_id"])
                    fixtures.json_pointer(instance, error["instance_pointer"])
        self.assertEqual(13, witnessed_cases)

    def test_structural_failure_prevents_semantic_cascades(self):
        instance = self.pattern()
        instance["schema"]["ArchetypeRecord"]["properties"]["family"]["values_ref"] = 3
        self.assertEqual([{
            "error_id": "JSON_SCHEMA_TYPE",
            "instance_pointer": "/schema/ArchetypeRecord/properties/family/values_ref",
            "schema_pointer": "/properties/schema/additionalProperties/properties/properties/additionalProperties/properties/values_ref/type",
        }], descriptors.descriptor_errors(instance, "pattern", ROOT))

    def test_enum_and_record_reference_namespaces_are_distinct(self):
        instance = self.pattern()
        instance["schema"]["ArchetypeRecord"]["properties"]["family"]["values_ref"] = "ArchetypeRecord"
        self.assert_semantic_error(
            instance, "pattern", "ENUM_REFERENCE",
            "/schema/ArchetypeRecord/properties/family/values_ref", "enum_reference",
        )
        instance = self.pattern()
        instance["registry_shape"]["families"]["character"]["items_ref"] = "family"
        self.assert_semantic_error(
            instance, "pattern", "RECORD_REFERENCE",
            "/registry_shape/families/character/items_ref", "record_reference",
        )

    def test_list_enum_references_resolve_the_same_local_enum_namespace(self):
        instance = self.pattern()
        instance["schema"]["ArchetypeRecord"]["properties"]["realm"]["items_ref"] = "missing"
        self.assert_semantic_error(
            instance, "pattern", "ENUM_REFERENCE",
            "/schema/ArchetypeRecord/properties/realm/items_ref", "enum_reference",
        )

    def test_extension_required_names_can_use_inherited_properties(self):
        instance = self.pattern()
        instance["schema"]["ClusterRecord"]["additional_required"].append("name")
        instance["schema"]["ClusterRecord"]["required"] = ["family"]
        self.assertEqual([], descriptors.descriptor_errors(instance, "pattern", ROOT))

    def test_every_declared_record_required_list_is_checked(self):
        for record_name, key in (
            ("ArchetypeRecord", "required"),
            ("ArchetypeRecord", "additional_required"),
            ("ClusterRecord", "required"),
            ("ClusterRecord", "additional_required"),
        ):
            with self.subTest(record=record_name, key=key):
                instance = self.pattern()
                record = instance["schema"][record_name]
                index = len(record.get(key, []))
                record.setdefault(key, []).append("missing")
                self.assert_semantic_error(
                    instance, "pattern", "REQUIRED_MEMBER",
                    f"/schema/{record_name}/{key}/{index}", "required_name_membership",
                )

    def test_nested_map_required_names_use_their_own_property_surface(self):
        instance = self.pattern()
        field = instance["schema"]["ArchetypeRecord"]["properties"]["attributes"]
        field["required"] = ["name"]
        self.assert_semantic_error(
            instance, "pattern", "REQUIRED_MEMBER",
            "/schema/ArchetypeRecord/properties/attributes/required/0", "required_name_membership",
        )

    def test_missing_parent_reports_reference_without_guessing_inherited_membership(self):
        instance = self.pattern()
        extension = instance["schema"]["ClusterRecord"]
        extension["extends"] = "missing"
        extension["additional_required"] = ["unknown_inherited_field"]
        self.assert_semantic_error(
            instance, "pattern", "RECORD_REFERENCE",
            "/schema/ClusterRecord/extends", "record_reference",
        )

    def test_cycle_reports_only_actual_cycle_members(self):
        instance = self.pattern()
        extension = instance["schema"]["ClusterRecord"]
        extension["extends"] = "ClusterRecord"
        extension["additional_required"] = ["unknown_inherited_field"]
        instance["schema"]["Dependent"] = {
            "extends": "ClusterRecord",
            "additional_required": ["unknown_inherited_field"],
            "properties": {},
        }
        self.assert_semantic_error(
            instance, "pattern", "INHERITANCE_CYCLE",
            "/schema/ClusterRecord/extends", "inheritance_cycle",
        )

    def test_two_record_cycle_has_one_stable_witness_per_participant(self):
        instance = self.pattern()
        base = instance["schema"]["ArchetypeRecord"]
        del base["type"]
        base["extends"] = "ClusterRecord"
        base["additional_required"] = []
        self.assertEqual([
            {
                "error_id": "YAML_DESCRIPTOR_INHERITANCE_CYCLE",
                "instance_pointer": f"/schema/{name}/extends",
                "schema_pointer": "/x-ywe-semantic-rules/inheritance_cycle",
            }
            for name in ("ArchetypeRecord", "ClusterRecord")
        ], descriptors.descriptor_errors(instance, "pattern", ROOT))

    def test_forward_references_and_nonsemantic_annotations_are_preserved(self):
        for name in ("pattern_forward_record_reference", "pattern_open_annotations"):
            with self.subTest(case=name):
                self.assertEqual([], descriptors.descriptor_errors(self.bundle["boundary"][name], "pattern", ROOT))

    def test_semantic_pointers_escape_record_names(self):
        instance = self.pattern()
        instance["schema"]["Future/Record~name"] = {
            "extends": "Future/Record~name", "additional_required": [], "properties": {},
        }
        self.assert_semantic_error(
            instance, "pattern", "INHERITANCE_CYCLE",
            "/schema/Future~1Record~0name/extends", "inheritance_cycle",
        )

    def test_all_seven_source_inline_fields_need_their_named_enum_declaration(self):
        for field_parts, enum_name in descriptors.MODULE_ENUM_BINDINGS:
            with self.subTest(enum=enum_name):
                instance = copy.deepcopy(self.sources["module"])
                del instance["classification_enums"][enum_name]
                self.assert_semantic_error(
                    instance, "module", "ENUM_REFERENCE",
                    fixtures.pointer_from_parts(("core_schema", "ModuleCapabilityManifest") + field_parts),
                    "enum_reference",
                )

    def test_all_seven_source_inline_fields_must_match_declared_enum_members(self):
        for field_parts, enum_name in descriptors.MODULE_ENUM_BINDINGS:
            with self.subTest(enum=enum_name):
                instance = copy.deepcopy(self.sources["module"])
                instance["classification_enums"][enum_name].append("future_value")
                self.assert_semantic_error(
                    instance, "module", "INLINE_ENUM",
                    fixtures.pointer_from_parts(("core_schema", "ModuleCapabilityManifest") + field_parts),
                    "inline_enum_consistency",
                )

    def test_inline_enum_order_and_whitespace_do_not_change_its_member_set(self):
        self.assertEqual([], descriptors.descriptor_errors(
            self.bundle["boundary"]["module_union_spacing_and_order"], "module", ROOT,
        ))

    def test_duplicate_inline_alternatives_are_rejected(self):
        instance = self.module()
        instance["core_schema"]["ModuleCapabilityManifest"]["module_classification"] = (
            "core_engine | feature_module | core_engine"
        )
        self.assert_semantic_error(
            instance, "module", "INLINE_ENUM",
            "/core_schema/ModuleCapabilityManifest/module_classification", "inline_enum_consistency",
        )

    def test_module_required_names_must_be_declared_in_the_manifest(self):
        instance = self.module()
        instance["canonical_validation_rules"]["required_fields"] = ["missing"]
        self.assert_semantic_error(
            instance, "module", "REQUIRED_MEMBER",
            "/canonical_validation_rules/required_fields/0", "required_name_membership",
        )

    def test_declared_prose_rules_are_typed_without_claiming_their_domain_execution(self):
        instance = self.module()
        instance["canonical_validation_rules"]["truth_boundary_rules"] = [
            "Future domain rule requires a separate validator."
        ]
        self.assertEqual([], descriptors.descriptor_errors(instance, "module", ROOT))

    def test_unsupported_grammar_values_fail_at_the_api_boundary(self):
        for grammar in ("unknown", None, [], 3):
            with self.subTest(grammar=grammar):
                with self.assertRaises(ValueError):
                    descriptors.descriptor_errors({}, grammar, ROOT)

    def test_descriptor_checker_executes_sources_and_every_declared_case(self):
        errors, results = descriptors.validation_errors(ROOT)
        self.assertEqual([], errors)
        self.assertEqual(44, len(results))
        self.assertEqual(33, sum(result["result"] == "reject" for result in results))


class YamlDescriptorExpectationsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        paths = (
            *descriptors.SCHEMA_PATHS,
            *(spec["source"] for spec in descriptors.GRAMMARS.values()),
            descriptors.BUNDLE_PATH, descriptors.CASE_EXPECTATIONS_PATH,
        )
        for relative in paths:
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
        self.expectations = fixtures.load_json(self.root / descriptors.CASE_EXPECTATIONS_PATH)

    def check(self):
        (self.root / descriptors.CASE_EXPECTATIONS_PATH).write_text(
            json.dumps(self.expectations, indent=2) + "\n", encoding="utf-8",
        )
        return descriptors.validation_errors(self.root)[0]

    def test_missing_or_duplicate_case_binding_fails_complete_coverage(self):
        for change in ("missing", "duplicate"):
            with self.subTest(change=change):
                self.expectations = fixtures.load_json(ROOT / descriptors.CASE_EXPECTATIONS_PATH)
                if change == "missing":
                    self.expectations["cases"].pop()
                else:
                    self.expectations["cases"].append(copy.deepcopy(self.expectations["cases"][0]))
                self.assertTrue(any("cover each declared case exactly once" in error for error in self.check()))

    def test_changed_error_reason_or_location_fails_exact_witness_comparison(self):
        original = fixtures.load_json(ROOT / descriptors.CASE_EXPECTATIONS_PATH)
        index = next(
            index for index, case in enumerate(original["cases"])
            if case["expected_errors"][0:1]
            and case["expected_errors"][0]["error_id"].startswith("YAML_DESCRIPTOR_")
        )
        for key, value in (
            ("error_id", "YAML_DESCRIPTOR_DIFFERENT"),
            ("instance_pointer", "/different"),
            ("schema_pointer", "/x-ywe-semantic-rules/different"),
        ):
            with self.subTest(key=key):
                self.expectations = copy.deepcopy(original)
                self.expectations["cases"][index]["expected_errors"][0][key] = value
                self.assertTrue(any("exact witnesses differ" in error for error in self.check()))

    def test_reject_case_cannot_be_reclassified_as_an_accepted_positive(self):
        case = next(case for case in self.expectations["cases"] if case["expected_result"] == "reject")
        case["expected_result"] = "accept"
        case["expected_errors"] = []
        errors = self.check()
        self.assertTrue(any("case role differs" in error for error in errors))
        self.assertTrue(any("exact witnesses differ" in error for error in errors))

    def test_malformed_expectation_grammar_fails_before_case_execution(self):
        self.expectations["cases"][0]["grammar"] = "unknown"
        errors = self.check()
        self.assertTrue(any(error.startswith("Descriptor case expectations:") for error in errors))
        self.assertFalse(any("Unable to execute descriptor cases" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
