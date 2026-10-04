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

import check_fixture_catalog as fixture_check


class JsonPointerTests(unittest.TestCase):
    def test_root_and_escaped_member_selection(self):
        document = {"a/b": {"~key": [0, {"": "selected"}]}, "a%2Fb": "literal"}
        self.assertIs(document, fixture_check.json_pointer(document, ""))
        self.assertEqual("selected", fixture_check.json_pointer(document, "/a~1b/~0key/1/"))
        self.assertEqual("literal", fixture_check.json_pointer(document, "/a%2Fb"))

    def test_invalid_or_unresolved_pointer_is_rejected(self):
        document = {"items": ["value"], "scalar": 1}
        for pointer in (
            "#", "#/items/0", "items/0", "/items/-", "/items/-1", "/items/01",
            "/items/1", "/missing", "/scalar/member", "/bad~", "/bad~2", None,
        ):
            with self.subTest(pointer=pointer):
                with self.assertRaises(ValueError):
                    fixture_check.json_pointer(document, pointer)

    def test_numeric_object_members_do_not_use_array_index_rules(self):
        self.assertEqual("member", fixture_check.json_pointer({"01": "member"}, "/01"))

    def test_error_signatures_escape_instance_and_schema_pointers(self):
        schema = {"properties": {"a/b~c": {"type": "integer"}}}
        error = next(Draft202012Validator(schema).iter_errors({"a/b~c": "wrong"}))
        self.assertEqual(
            {
                "error_id": "JSON_SCHEMA_TYPE",
                "instance_pointer": "/a~1b~0c",
                "schema_pointer": "/properties/a~1b~0c/type",
            },
            fixture_check.error_signature(error),
        )

    def test_nested_union_errors_retain_leaf_causes(self):
        schema = {"anyOf": [{"oneOf": [{"type": "string"}, {"type": "integer"}]}, {"type": "array"}]}
        error = next(Draft202012Validator(schema).iter_errors(None))
        leaves = list(fixture_check.leaf_errors(error))
        self.assertEqual(3, len(leaves))
        self.assertTrue(all(leaf.validator == "type" for leaf in leaves))
        self.assertEqual(
            {"/anyOf/0/oneOf/0/type", "/anyOf/0/oneOf/1/type", "/anyOf/1/type"},
            {fixture_check.error_signature(leaf)["schema_pointer"] for leaf in leaves},
        )


class FixtureCatalogTests(unittest.TestCase):
    SCHEMA_PATH = "data/schemas/record.json"
    SCHEMA_ID = "https://ywe.local/schemas/record.json"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.schema = {
            "$schema": fixture_check.DIALECT,
            "$id": self.SCHEMA_ID,
            "type": "object",
            "required": ["value"],
            "properties": {"value": {"type": "integer", "minimum": 0}},
            "additionalProperties": False,
        }
        self.write(self.SCHEMA_PATH, self.schema)
        self.entries = [{"schema_id": self.SCHEMA_ID, "path": self.SCHEMA_PATH}]
        for name in ("contract_catalog_schema.json", "fixture_catalog_schema.json"):
            relative = "data/schemas/" + name
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
            self.entries.append({"schema_id": "https://ywe.local/schemas/" + name, "path": relative})
        self.write("examples/record.json", {"record": {"value": 1}})
        self.write("data/governance/normative_requirement_register.json", {
            "requirements": [{"requirement_id": "YWE-REQ-0020", "status": "active"}]
        })
        self.fixtures = [self.fixture()]
        self.save_catalogs()

    def write(self, relative: str, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def fixture(self, **changes):
        result = {
            "fixture_id": "record.positive",
            "path": "examples/record.json",
            "instance_pointer": "/record",
            "schema_id": self.SCHEMA_ID,
            "category": "positive",
            "expected_result": "accept",
            "expected_errors": [],
            "expected_requirement_ids": ["YWE-REQ-0020"],
        }
        result.update(changes)
        if result["expected_result"] == "reject":
            result.pop("expected_requirement_ids", None)
        return result

    def save_catalogs(self):
        self.write(fixture_check.CONTRACT_CATALOG, {
            "schema_ref": "data/schemas/contract_catalog_schema.json",
            "artifact_type": "ywe_contract_catalog",
            "artifact_version": "1.0.0",
            "schemas": self.entries,
        })
        self.write(fixture_check.FIXTURE_CATALOG, {
            "schema_ref": "data/schemas/fixture_catalog_schema.json",
            "artifact_type": "ywe_fixture_catalog",
            "artifact_version": "1.0.0",
            "fixtures": self.fixtures,
        })

    def run_check(self):
        self.save_catalogs()
        return fixture_check.validation_errors(self.root)

    def assert_rejected(self, expected_message: str | None = None):
        errors, _ = self.run_check()
        self.assertTrue(errors)
        if expected_message:
            self.assertTrue(any(expected_message in error for error in errors), errors)

    def test_valid_binding_selects_instance_in_document(self):
        errors, results = self.run_check()
        self.assertEqual([], errors)
        self.assertEqual(
            [{"fixture_id": "record.positive", "path": "examples/record.json", "result": "accept"}],
            results,
        )

    def test_accepted_fixture_requires_nonempty_unique_requirement_identifiers(self):
        for identifiers in (None, [], ["YWE-REQ-0020", "YWE-REQ-0020"], "YWE-REQ-0020"):
            with self.subTest(identifiers=identifiers):
                self.fixtures = [self.fixture()]
                if identifiers is None:
                    self.fixtures[0].pop("expected_requirement_ids")
                else:
                    self.fixtures[0]["expected_requirement_ids"] = identifiers
                self.assert_rejected()

    def test_unknown_or_retired_requirement_identity_cannot_establish_acceptance(self):
        self.fixtures[0]["expected_requirement_ids"] = ["YWE-REQ-9999"]
        self.assert_rejected("not registered and active")
        self.fixtures[0]["expected_requirement_ids"] = ["YWE-REQ-0020"]
        self.write("data/governance/normative_requirement_register.json", {
            "requirements": [{"requirement_id": "YWE-REQ-0020", "status": "superseded"}]
        })
        self.assert_rejected("not registered and active")

    def test_unrelated_registered_requirement_cannot_own_a_fixture(self):
        self.write("data/governance/normative_requirement_register.json", {
            "requirements": [{"requirement_id": "YWE-REQ-0019", "status": "active"}]
        })
        self.fixtures[0]["expected_requirement_ids"] = ["YWE-REQ-0019"]
        self.assert_rejected("does not own its selected contract")

    def test_specific_requirement_needs_both_target_annotation_and_registered_source(self):
        self.schema["x-ywe-requirement-id"] = "YWE-REQ-0021"
        self.write(self.SCHEMA_PATH, self.schema)
        self.fixtures[0]["expected_requirement_ids"] = ["YWE-REQ-0021"]
        self.write("data/governance/normative_requirement_register.json", {
            "requirements": [{"requirement_id": "YWE-REQ-0021", "status": "active", "source_refs": ["data/schemas/unrelated.json"]}]
        })
        self.assert_rejected("registered requirement source does not own")
        self.write("data/governance/normative_requirement_register.json", {
            "requirements": [{"requirement_id": "YWE-REQ-0021", "status": "active", "source_refs": [self.SCHEMA_PATH]}]
        })
        self.assertEqual([], self.run_check()[0])

    def test_requirement_source_fragment_cannot_certify_a_different_schema_surface(self):
        self.schema["properties"]["value"]["x-ywe-requirement-id"] = "YWE-REQ-0021"
        self.write(self.SCHEMA_PATH, self.schema)
        self.fixtures[0].update(schema_id=self.SCHEMA_ID + "#/properties/value",
                                instance_pointer="/record/value", expected_requirement_ids=["YWE-REQ-0021"])
        self.write("data/governance/normative_requirement_register.json", {
            "requirements": [{"requirement_id": "YWE-REQ-0021", "status": "active", "source_refs": [self.SCHEMA_PATH + "#/properties/unrelated"]}]
        })
        self.assert_rejected("registered requirement source does not own")
        self.write("data/governance/normative_requirement_register.json", {
            "requirements": [{"requirement_id": "YWE-REQ-0021", "status": "active", "source_refs": [self.SCHEMA_PATH + "#/properties/value"]}]
        })
        self.assertEqual([], self.run_check()[0])

    def test_owned_requirement_resolves_anchor_and_nested_resource_aliases(self):
        self.schema["$defs"] = {"value": {
            "$id": "owned.json", "$anchor": "Value", "type": "integer",
            "x-ywe-requirement-id": "YWE-REQ-0021",
        }}
        self.write(self.SCHEMA_PATH, self.schema)
        self.write("examples/record.json", {"record": 7})
        self.fixtures[0]["expected_requirement_ids"] = ["YWE-REQ-0021"]
        register = {"requirements": [{
            "requirement_id": "YWE-REQ-0021", "status": "active",
            "source_refs": [self.SCHEMA_PATH + "#/$defs/value"],
        }]}
        self.write("data/governance/normative_requirement_register.json", register)
        for target in (self.SCHEMA_ID + "#/$defs/value", "https://ywe.local/schemas/owned.json",
                       "https://ywe.local/schemas/owned.json#Value"):
            with self.subTest(target=target):
                self.fixtures[0]["schema_id"] = target
                self.assertEqual([], self.run_check()[0])
        register["requirements"][0]["source_refs"] = [self.SCHEMA_PATH + "#/properties/value"]
        self.write("data/governance/normative_requirement_register.json", register)
        self.assert_rejected("registered requirement source does not own")

    def test_equal_schema_values_do_not_substitute_for_actual_requirement_owner(self):
        value = {"type": "integer", "x-ywe-requirement-id": "YWE-REQ-0021"}
        self.schema["$defs"] = {"owned": value, "unrelated": copy.deepcopy(value)}
        self.write(self.SCHEMA_PATH, self.schema)
        self.write("examples/record.json", {"record": 7})
        self.fixtures[0].update(schema_id=self.SCHEMA_ID + "#/$defs/unrelated",
                                expected_requirement_ids=["YWE-REQ-0021"])
        self.write("data/governance/normative_requirement_register.json", {
            "requirements": [{"requirement_id": "YWE-REQ-0021", "status": "active",
                              "source_refs": [self.SCHEMA_PATH + "#/$defs/owned"]}]
        })
        self.assert_rejected("registered requirement source does not own")

    def test_invalid_instance_cannot_be_declared_accepted(self):
        self.write("examples/record.json", {"record": {"value": "wrong"}})
        self.assert_rejected("observed reject")

    def test_expected_rejection_requires_exact_keyword_and_locations(self):
        self.write("examples/record.json", {"record": {"value": -1}})
        expected = {
            "error_id": "JSON_SCHEMA_MINIMUM",
            "instance_pointer": "/value",
            "schema_pointer": "/properties/value/minimum",
        }
        self.fixtures = [self.fixture(category="reject", expected_result="reject", expected_errors=[expected])]
        self.assertEqual([], self.run_check()[0])
        for field, wrong_value in (
            ("error_id", "JSON_SCHEMA_TYPE"),
            ("instance_pointer", "/other"),
            ("schema_pointer", "/properties/value/type"),
        ):
            with self.subTest(field=field):
                self.fixtures[0]["expected_errors"] = [{**expected, field: wrong_value}]
                self.assert_rejected("expected reject")

    def test_missing_or_extra_failure_reason_does_not_pass(self):
        self.write("examples/record.json", {"record": {"value": -1, "extra": True}})
        self.fixtures = [self.fixture(
            category="reject", expected_result="reject",
            expected_errors=[{
                "error_id": "JSON_SCHEMA_MINIMUM", "instance_pointer": "/value",
                "schema_pointer": "/properties/value/minimum",
            }],
        )]
        self.assert_rejected("JSON_SCHEMA_ADDITIONALPROPERTIES")

    def test_valid_instance_cannot_be_declared_rejected(self):
        self.fixtures = [self.fixture(
            category="reject", expected_result="reject",
            expected_errors=[{
                "error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required",
                "missing_properties": ["value"],
            }],
        )]
        self.assert_rejected("observed accept")

    def test_rejection_distinguishes_missing_required_fields_at_same_schema_pointer(self):
        self.schema["required"] = ["first", "second"]
        self.schema["properties"] = {"first": {"type": "string"}, "second": {"type": "string"}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.write("examples/record.json", {"record": {"first": "present"}})
        self.fixtures = [self.fixture(
            category="reject", expected_result="reject", expected_errors=[{
                "error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required",
                "missing_properties": ["second"],
            }],
        )]
        self.assertEqual([], self.run_check()[0])
        self.write("examples/record.json", {"record": {"second": "present"}})
        self.assert_rejected("first")

    def test_duplicate_fixture_id_is_rejected(self):
        self.write("examples/second.json", {"record": {"value": 2}})
        self.fixtures.append(self.fixture(path="examples/second.json"))
        self.assert_rejected("Duplicate fixture ID or binding")

    def test_duplicate_binding_with_different_id_is_rejected(self):
        self.fixtures.append(self.fixture(fixture_id="record.second"))
        self.assert_rejected("Duplicate fixture ID or binding")

    def test_missing_fixture_file_is_rejected(self):
        self.fixtures[0]["path"] = "examples/missing.json"
        self.assert_rejected("unable to validate offline")

    def test_unsafe_fixture_paths_are_rejected(self):
        for relative in ("../outside.json", "/outside.json", "C:/outside.json", "examples\\record.json"):
            with self.subTest(path=relative):
                self.fixtures[0]["path"] = relative
                self.assert_rejected("unable to validate offline")

    def test_missing_fixture_pointer_is_rejected(self):
        self.fixtures[0]["instance_pointer"] = "/missing"
        self.assert_rejected("Unresolved JSON Pointer")

    def test_malformed_fixture_pointer_is_rejected(self):
        for pointer in ("record", "/record~2", "/record~"):
            with self.subTest(pointer=pointer):
                self.fixtures[0]["instance_pointer"] = pointer
                self.assert_rejected()

    def test_exact_subschema_target_allows_scalar_fixture(self):
        self.write("examples/record.json", {"record": 7})
        self.fixtures[0]["schema_id"] += "#/properties/value"
        self.assertEqual([], self.run_check()[0])

    def test_schema_annotation_cannot_be_fixture_target(self):
        self.schema["description"] = "record documentation"
        self.write(self.SCHEMA_PATH, self.schema)
        self.fixtures[0]["schema_id"] += "#/description"
        self.assert_rejected("does not resolve to a schema")

    def test_boolean_annotation_cannot_be_fixture_target(self):
        self.schema["deprecated"] = False
        self.write(self.SCHEMA_PATH, self.schema)
        self.fixtures[0].update(
            schema_id=self.SCHEMA_ID + "#/deprecated", category="reject", expected_result="reject",
            expected_errors=[{"error_id": "JSON_SCHEMA_NONE", "instance_pointer": "", "schema_pointer": ""}],
        )
        self.assert_rejected("does not resolve to a schema")

    def test_boolean_subschema_is_a_valid_exact_target(self):
        self.fixtures[0].update(
            schema_id=self.SCHEMA_ID + "#/additionalProperties", category="reject", expected_result="reject",
            expected_errors=[{"error_id": "JSON_SCHEMA_NONE", "instance_pointer": "", "schema_pointer": ""}],
        )
        self.assertEqual([], self.run_check()[0])

    def test_boolean_true_subschema_is_a_valid_exact_target(self):
        self.schema["$defs"] = {"open": True}
        self.write(self.SCHEMA_PATH, self.schema)
        self.fixtures[0]["schema_id"] += "#/$defs/open"
        self.assertEqual([], self.run_check()[0])

    def test_uri_encoded_boolean_subschema_pointer_resolves(self):
        self.fixtures[0].update(
            schema_id=self.SCHEMA_ID + "#/%61dditionalProperties", category="reject", expected_result="reject",
            expected_errors=[{"error_id": "JSON_SCHEMA_NONE", "instance_pointer": "", "schema_pointer": ""}],
        )
        self.assertEqual([], self.run_check()[0])

    def test_anchor_is_a_valid_exact_fixture_target(self):
        self.schema["$defs"] = {"number": {"$anchor": "number", "type": "integer"}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.write("examples/record.json", {"record": 7})
        self.fixtures[0]["schema_id"] += "#number"
        self.assertEqual([], self.run_check()[0])

    def test_legacy_definitions_are_valid_exact_fixture_targets(self):
        self.schema["definitions"] = {"number": {"type": "integer"}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.write("examples/record.json", {"record": 7})
        self.fixtures[0]["schema_id"] += "#/definitions/number"
        self.assertEqual([], self.run_check()[0])

    def test_content_schema_is_a_valid_exact_fixture_target(self):
        self.schema["contentSchema"] = {"type": "integer"}
        self.write(self.SCHEMA_PATH, self.schema)
        self.write("examples/record.json", {"record": 7})
        self.fixtures[0]["schema_id"] += "#/contentSchema"
        self.assertEqual([], self.run_check()[0])

    def test_unknown_external_fixture_schema_is_blocked_offline(self):
        self.fixtures[0]["schema_id"] = "https://unavailable.example/record.json"
        self.assert_rejected("unable to validate offline")

    def test_unused_external_reference_is_rejected(self):
        self.schema["$defs"] = {"unused": {"$ref": "https://unavailable.example/record.json"}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.assert_rejected("Unresolved offline schema reference")

    def test_unknown_dynamic_reference_is_rejected(self):
        self.schema["$defs"] = {"unused": {"$dynamicRef": "https://unavailable.example/record.json#node"}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.assert_rejected("Unresolved offline schema reference")

    def test_missing_local_anchor_is_rejected_even_when_unused(self):
        self.schema["$defs"] = {"unused": {"$ref": "#missing"}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.assert_rejected("Unresolved offline schema reference")

    def test_reference_shaped_annotation_is_not_schema_reference(self):
        self.schema["examples"] = [{"$ref": "https://unavailable.example/example-data"}]
        self.write(self.SCHEMA_PATH, self.schema)
        self.assertEqual([], self.run_check()[0])

    def test_local_anchor_reference_resolves(self):
        self.schema["properties"]["value"] = {"$ref": "#number"}
        self.schema["$defs"] = {"number": {"$anchor": "number", "type": "integer", "minimum": 0}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.assertEqual([], self.run_check()[0])

    def test_nested_resource_relative_reference_resolves(self):
        self.schema["properties"]["value"] = {"$ref": "#/$defs/nested"}
        self.schema["$defs"] = {"nested": {"$id": "nested.json", "$ref": "record.json#/$defs/number"}, "number": {"type": "integer"}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.assertEqual([], self.run_check()[0])

    def test_duplicate_schema_catalog_id_is_rejected(self):
        self.entries.append(copy.deepcopy(self.entries[0]))
        self.assert_rejected("Duplicate schema catalog entry")

    def test_nested_resource_cannot_shadow_catalogued_schema_identity(self):
        self.schema["$defs"] = {"shadow": {"$id": self.SCHEMA_ID, "type": "object"}}
        self.write(self.SCHEMA_PATH, self.schema)
        self.assert_rejected()

    def test_duplicate_anchors_in_one_resource_are_rejected(self):
        self.schema["$defs"] = {
            "first": {"$anchor": "same", "type": "integer"},
            "second": {"$anchor": "same", "type": "string"},
        }
        self.write(self.SCHEMA_PATH, self.schema)
        self.assert_rejected("Duplicate schema anchor")

    def test_schema_catalog_identifier_drift_is_rejected(self):
        self.entries[0]["schema_id"] = "https://ywe.local/schemas/different.json"
        self.assert_rejected("identifier mismatch")

    def test_uncatalogued_declared_schema_is_rejected(self):
        self.write("data/schemas/uncatalogued.json", {
            "$schema": fixture_check.DIALECT, "$id": "https://ywe.local/schemas/uncatalogued.json", "type": "string",
        })
        self.assert_rejected("coverage differs")

    def test_catalog_entry_without_schema_declaration_is_rejected(self):
        del self.schema["$schema"]
        self.write(self.SCHEMA_PATH, self.schema)
        self.assert_rejected("Unsupported schema dialect")

    def test_malformed_schema_declaration_is_rejected(self):
        self.schema["properties"]["value"] = {"type": "not-a-json-type"}
        self.write(self.SCHEMA_PATH, self.schema)
        self.assert_rejected("Invalid schema declaration")

    def test_empty_or_malformed_catalog_cannot_report_success(self):
        self.fixtures = []
        self.assert_rejected()
        self.fixtures = [self.fixture()]
        del self.fixtures[0]["instance_pointer"]
        self.assert_rejected()

    def test_format_remains_annotation_in_selected_profile(self):
        self.schema["properties"]["value"] = {"type": "string", "format": "date-time"}
        self.write(self.SCHEMA_PATH, self.schema)
        self.write("examples/record.json", {"record": {"value": "format is annotation"}})
        self.assertEqual([], self.run_check()[0])


if __name__ == "__main__":
    unittest.main()
