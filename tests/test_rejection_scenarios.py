from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_fixture_catalog as fixtures
import check_rejection_scenarios as rejection


class RejectionScenarioTests(unittest.TestCase):
    SCHEMA_PATH = "data/schemas/record.json"
    SCHEMA_ID = "https://ywe.local/schemas/record.json"
    DESCRIPTOR = "examples/rejection.json"
    BASE = "examples/positive.json"

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.entries = []
        self.schema = {
            "$schema": fixtures.DIALECT, "$id": self.SCHEMA_ID,
            "type": "object", "required": ["value"],
            "properties": {"value": {"type": "integer", "minimum": 0}},
            "additionalProperties": False,
        }
        self.register_schema(self.SCHEMA_PATH, self.schema)
        for name in ("contract_catalog_schema.json", "fixture_catalog_schema.json", "rejection_scenario_catalog_schema.json"):
            relative = "data/schemas/" + name
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)
            self.entries.append({"schema_id": "https://ywe.local/schemas/" + name, "path": relative})
        self.descriptor = {"invalid_reason": "negative value", "invalid_content": {"value": -1}, "must_reject": True}
        self.write(self.DESCRIPTOR, self.descriptor)
        self.write(self.BASE, {"value": 1})
        self.write("data/validation/terms.json", {"reject_terms": ["Unity", "Godot"]})
        self.write("data/validation/intent.json", {"negative_value": -1})
        self.scenarios = [self.direct()]
        self.approve_scenarios()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def register_schema(self, relative, schema):
        self.write(relative, schema)
        self.entries.append({"schema_id": schema["$id"], "path": relative})

    def common(self):
        return {
            "scenario_id": "record.reject", "descriptor_path": self.DESCRIPTOR,
            "descriptor_sha256": rejection.normalized_text_sha256(self.root / self.DESCRIPTOR),
            "hash_algorithm": rejection.HASH_ALGORITHM,
            "descriptor_bindings": [
                {"pointer": "/invalid_reason", "value": self.descriptor["invalid_reason"]},
                {"pointer": "/invalid_content", "value": copy.deepcopy(self.descriptor["invalid_content"])},
            ],
            "owner_bindings": [
                {"path": self.SCHEMA_PATH, "pointer": "/properties/value/minimum", "value": 0},
                {"path": "data/validation/intent.json", "pointer": "/negative_value", "value": -1},
            ],
            "description": "Reject the explicitly supplied negative subject.",
        }

    def direct(self):
        return {
            **self.common(), "mode": "direct", "validation_scope": "subject",
            "subject_pointer": "/invalid_content", "schema_id": self.SCHEMA_ID,
            "expected_errors": [{"error_id": "JSON_SCHEMA_MINIMUM", "instance_pointer": "/value", "schema_pointer": "/properties/value/minimum"}],
        }

    def mutation(self):
        return {
            **self.common(), "mode": "mutation", "validation_scope": "materialized_scenario",
            "base_path": self.BASE, "base_pointer": "", "schema_id": self.SCHEMA_ID,
            "operations": [{"op": "replace", "path": "/value", "value": -1}],
            "mutation_value_bindings": [{
                "operation_index": 0, "source_path": "data/validation/intent.json",
                "source_pointer": "/negative_value", "source_value": -1, "relation": "equal",
            }],
            "expected_errors": self.direct()["expected_errors"],
        }

    def lexical(self, subject="Unity and Godot"):
        self.descriptor["invalid_content"] = subject
        self.write(self.DESCRIPTOR, self.descriptor)
        return {
            **self.common(), "mode": "lexical", "validation_scope": "subject",
            "subject_pointer": "/invalid_content", "rule_path": "data/validation/terms.json",
            "reject_terms_pointer": "/reject_terms",
            "owner_bindings": [{"path": "data/validation/terms.json", "pointer": "/reject_terms", "value": ["Unity", "Godot"]}],
            "expected_matches": [{"subject_pointer": "/invalid_content", "term": term} for term in ("Unity", "Godot")],
        }

    def approve_scenarios(self):
        """Author the test approval before adversarial catalog changes."""
        self.write(rejection.EXECUTION_CONTRACTS_PATH, {
            "schema_ref": rejection.PROJECTION_SCHEMA_PATH + "#/$defs/ExecutionContracts",
            "artifact_type": "ywe_rejection_execution_contracts", "artifact_version": "1.0.0",
            "contracts": copy.deepcopy(self.scenarios),
        })

    def run_check(self):
        self.write(fixtures.CONTRACT_CATALOG, {
            "schema_ref": "data/schemas/contract_catalog_schema.json", "artifact_type": "ywe_contract_catalog",
            "artifact_version": "1.0.0", "schemas": self.entries,
        })
        self.write(rejection.SCENARIO_CATALOG, {
            "schema_ref": "data/schemas/rejection_scenario_catalog_schema.json",
            "artifact_type": "ywe_rejection_scenario_catalog", "artifact_version": "1.0.0",
            "scenarios": self.scenarios,
        })
        return rejection.validation_errors(self.root)

    def assert_failure(self, message):
        errors, _ = self.run_check()
        self.assertTrue(errors)
        self.assertTrue(any(message in error for error in errors), errors)

    def update_digest(self):
        self.scenarios[0]["descriptor_sha256"] = rejection.normalized_text_sha256(self.root / self.DESCRIPTOR)

    def test_direct_subject_requires_exact_rejection_and_reports_scope(self):
        errors, results = self.run_check()
        self.assertEqual([], errors)
        self.assertEqual([{"descriptor_path": self.DESCRIPTOR, "descriptor_unit_pointer": "", "scenario_id": "record.reject", "result": "reject", "validation_scope": "subject"}], results)

    def test_explicit_mutation_rejects_and_preserves_original_base(self):
        self.scenarios = [self.mutation()]
        before = (self.root / self.BASE).read_bytes()
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])
        self.assertEqual(before, (self.root / self.BASE).read_bytes())

    def test_lexical_matching_is_case_insensitive_with_complete_term_witnesses(self):
        self.scenarios = [self.lexical("unity and GODOT")]
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])

    def test_descriptor_digest_catches_changes_to_unselected_metadata(self):
        self.descriptor["new_metadata"] = "changed"
        self.write(self.DESCRIPTOR, self.descriptor)
        self.assert_failure("source digest differs")

    def test_source_digest_normalizes_lf_and_crlf(self):
        path = self.root / self.DESCRIPTOR
        normalized = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        path.write_bytes(normalized.replace(b"\n", b"\r\n"))
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])

    def test_refreshing_digest_does_not_hide_changed_reason_binding(self):
        self.descriptor["invalid_reason"] = "unrelated reason"
        self.write(self.DESCRIPTOR, self.descriptor)
        self.update_digest()
        self.assert_failure("Descriptor value differs at '/invalid_reason'")

    def test_boolean_binding_cannot_be_replaced_with_numeric_one(self):
        self.scenarios[0]["descriptor_bindings"].append({"pointer": "/must_reject", "value": True})
        self.descriptor["must_reject"] = 1
        self.write(self.DESCRIPTOR, self.descriptor)
        self.update_digest()
        self.assert_failure("Descriptor value differs at '/must_reject'")

    def test_missing_expected_reason_binding_is_rejected(self):
        self.scenarios[0]["descriptor_bindings"] = [
            {"pointer": "/invalid_content", "value": {"value": -1}},
            {"pointer": "/must_reject", "value": True},
        ]
        self.assert_failure("expected-reason binding")

    def test_selected_direct_subject_must_be_explicitly_bound(self):
        self.scenarios[0]["descriptor_bindings"][1] = {"pointer": "/must_reject", "value": True}
        self.assert_failure("explicit descriptor value binding")

    def test_changed_owning_assertion_invalidates_catalog_binding(self):
        self.schema["properties"]["value"]["minimum"] = -2
        self.write(self.SCHEMA_PATH, self.schema)
        self.assert_failure("Owning assertion differs")

    def test_unrelated_schema_owner_cannot_establish_executed_constraint(self):
        self.schema["properties"]["other"] = {"type": "integer", "minimum": 0}
        self.write(self.SCHEMA_PATH, self.schema)
        self.scenarios[0]["owner_bindings"] = [{
            "path": self.SCHEMA_PATH, "pointer": "/properties/other/minimum", "value": 0,
        }]
        self.assert_failure("exact owning assertion binding")

    def test_same_false_const_cannot_relabel_a_different_rejection_reason(self):
        self.schema["required"] = ["morality", "permanent_death"]
        self.schema["properties"] = {
            "morality": {"type": "boolean", "const": False},
            "permanent_death": {"type": "boolean", "const": False},
        }
        self.write(self.SCHEMA_PATH, self.schema)
        self.write(self.BASE, {"morality": False, "permanent_death": False})
        scenario = self.mutation()
        scenario["owner_bindings"] = [{
            "path": self.SCHEMA_PATH, "pointer": "/properties/morality/const", "value": False,
        }]
        scenario["operations"] = [{"op": "replace", "path": "/permanent_death", "value": True}]
        scenario["expected_errors"] = [{
            "error_id": "JSON_SCHEMA_CONST", "instance_pointer": "/permanent_death",
            "schema_pointer": "/properties/permanent_death/const",
        }]
        scenario["mutation_value_bindings"] = [{
            "operation_index": 0, "source_path": self.SCHEMA_PATH,
            "source_pointer": "/properties/permanent_death/const", "source_value": False,
            "relation": "negated_boolean",
        }]
        self.scenarios = [scenario]
        self.assert_failure("exact owning assertion binding")
        scenario["owner_bindings"].append({
            "path": self.SCHEMA_PATH, "pointer": "/properties/permanent_death/const", "value": False,
        })
        self.assert_failure("not exercised or mapped")

    def test_subschema_constraint_owner_uses_its_complete_source_pointer(self):
        scenario = self.direct()
        scenario["subject_pointer"] = "/invalid_content/value"
        scenario["descriptor_bindings"].append({"pointer": "/invalid_content/value", "value": -1})
        scenario["schema_id"] += "#/properties/value"
        scenario["expected_errors"] = [{
            "error_id": "JSON_SCHEMA_MINIMUM", "instance_pointer": "", "schema_pointer": "/minimum",
        }]
        self.scenarios = [scenario]
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])

    def test_referenced_constraint_requires_the_referenced_resource_owner(self):
        relative = "data/schemas/referenced.json"
        identifier = "https://ywe.local/schemas/referenced.json"
        self.register_schema(relative, {
            "$schema": fixtures.DIALECT, "$id": identifier,
            "$defs": {"NonNegative": {"type": "integer", "minimum": 0}},
        })
        self.schema["properties"]["value"] = {"$ref": identifier + "#/$defs/NonNegative"}
        self.write(self.SCHEMA_PATH, self.schema)
        self.scenarios[0]["owner_bindings"] = [{
            "path": relative, "pointer": "/$defs/NonNegative/minimum", "value": 0,
        }]
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])
        self.scenarios[0]["owner_bindings"] = [{
            "path": self.SCHEMA_PATH, "pointer": "/properties/value/$ref",
            "value": identifier + "#/$defs/NonNegative",
        }]
        self.assert_failure("exact owning assertion binding")

    def test_equal_keyword_at_another_resource_cannot_substitute_for_the_owner(self):
        relative = "data/schemas/unrelated.json"
        self.register_schema(relative, {
            "$schema": fixtures.DIALECT, "$id": "https://ywe.local/schemas/unrelated.json",
            "properties": {"value": {"type": "integer", "minimum": 0}},
        })
        self.scenarios[0]["owner_bindings"] = [{
            "path": relative, "pointer": "/properties/value/minimum", "value": 0,
        }]
        self.assert_failure("exact owning assertion binding")

    def test_lexical_assertion_requires_the_executed_terms_owner(self):
        self.scenarios = [self.lexical()]
        self.scenarios[0]["owner_bindings"] = self.common()["owner_bindings"]
        self.assert_failure("exact owning reject_terms binding")

    def test_identical_terms_at_another_pointer_do_not_bind_the_executed_rule(self):
        self.write("data/validation/terms.json", {
            "reject_terms": ["Unity", "Godot"], "other_terms": ["Unity", "Godot"],
        })
        self.scenarios = [self.lexical()]
        self.scenarios[0]["owner_bindings"][0]["pointer"] = "/other_terms"
        self.assert_failure("exact owning reject_terms binding")

    def test_owned_allowed_terms_cannot_be_executed_as_rejection_policy(self):
        self.scenarios = [self.lexical()]
        self.write("data/validation/terms.json", {"reject_terms": ["Unity", "Godot"],
                                                  "allowed_terms": ["Unity", "Godot"]})
        self.scenarios[0]["reject_terms_pointer"] = "/allowed_terms"
        self.scenarios[0]["owner_bindings"][0]["pointer"] = "/allowed_terms"
        self.assert_failure("explicitly declared reject_terms list")

    def projection(self):
        self.descriptor["invalid_content"] = ["default_party_member"]
        self.write(self.DESCRIPTOR, self.descriptor)
        schema_path = rejection.PROJECTION_SCHEMA_PATH
        pointer = "/$defs/ConditionalWolfFunctionAssertion/not"
        source_path = "data/validation/check_wolf_conditional_manifestation.spec.json"
        source_pointer = "/must_reject"
        source_value = ["always_present_wolves", "default_party_member", "white_good_dark_evil_score"]
        assertion_value = {"contains": {"const": "default_party_member"}}
        self.write(source_path, {"must_reject": source_value})
        return {
            **self.direct(),
            "validation_scope": "assertion_projection",
            "schema_id": rejection.SCENARIO_SCHEMA_ID + "#/$defs/ConditionalWolfFunctionAssertion",
            "expected_errors": [{"error_id": "JSON_SCHEMA_NOT", "instance_pointer": "", "schema_pointer": "/not"}],
            "owner_bindings": [
                {"path": schema_path, "pointer": pointer, "value": assertion_value},
                {"path": source_path, "pointer": source_pointer, "value": source_value},
            ],
            "projection_bindings": [{
                "assertion_pointer": pointer, "assertion_value": assertion_value,
                "source_path": source_path, "source_pointer": source_pointer, "source_value": source_value,
            }],
        }

    def test_projection_links_the_actual_constraint_to_its_declared_source(self):
        self.scenarios = [self.projection()]
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])

    def test_projection_cannot_use_only_its_prose_source_as_the_constraint_owner(self):
        self.scenarios = [self.projection()]
        self.scenarios[0]["owner_bindings"].pop(0)
        self.assert_failure("exact owning assertion binding")

    def test_projection_requires_an_explicit_mapping_even_with_both_owners(self):
        self.scenarios = [self.projection()]
        del self.scenarios[0]["projection_bindings"]
        self.assert_failure("explicit source mapping")

    def test_projection_mapping_cannot_select_an_unexecuted_constraint(self):
        self.scenarios = [self.projection()]
        self.scenarios[0]["projection_bindings"][0]["assertion_pointer"] = (
            "/$defs/ConditionalWolfFunctionAssertion/type"
        )
        self.assert_failure("executed projection constraint")

    def test_projection_mapping_preserves_exact_assertion_and_source_values(self):
        for field, value, message in (
            ("assertion_value", {"contains": {"const": "different"}}, "Projection assertion value differs"),
            ("source_value", ["different"], "exact source owner binding"),
        ):
            with self.subTest(field=field):
                self.scenarios = [self.projection()]
                self.scenarios[0]["projection_bindings"][0][field] = value
                self.assert_failure(message)

    def test_projection_source_must_match_the_owned_definition_annotation(self):
        self.scenarios = [self.projection()]
        mapping = self.scenarios[0]["projection_bindings"][0]
        mapping["source_path"] = "data/validation/terms.json"
        mapping["source_pointer"] = "/reject_terms"
        mapping["source_value"] = ["Unity", "Godot"]
        self.scenarios[0]["owner_bindings"].append({
            "path": mapping["source_path"], "pointer": mapping["source_pointer"],
            "value": mapping["source_value"],
        })
        self.assert_failure("declared owning rule")

    def test_projection_source_requires_a_separate_exact_owner_binding(self):
        self.scenarios = [self.projection()]
        self.scenarios[0]["owner_bindings"].pop()
        self.assert_failure("exact source owner binding")

    def test_projection_mappings_cannot_be_duplicated_or_attached_to_lexical_mode(self):
        self.scenarios = [self.projection()]
        self.scenarios[0]["projection_bindings"].append(copy.deepcopy(self.scenarios[0]["projection_bindings"][0]))
        self.assert_failure("has non-unique elements")
        projection_bindings = self.scenarios[0]["projection_bindings"][:1]
        self.scenarios = [self.lexical()]
        self.scenarios[0]["projection_bindings"] = projection_bindings
        self.assert_failure("should not be valid")

    def test_wrong_reason_and_wrong_error_locations_are_rejected(self):
        original = copy.deepcopy(self.scenarios[0]["expected_errors"][0])
        for field, value in (("error_id", "JSON_SCHEMA_TYPE"), ("instance_pointer", "/other"), ("schema_pointer", "/properties/value/type")):
            with self.subTest(field=field):
                self.scenarios[0]["expected_errors"] = [{**original, field: value}]
                self.assert_failure("Expected complete rejection witnesses")

    def test_extra_unrelated_failure_cannot_satisfy_intended_rejection(self):
        self.descriptor["invalid_content"]["extra"] = True
        self.write(self.DESCRIPTOR, self.descriptor)
        self.scenarios = [self.direct()]
        self.assert_failure("JSON_SCHEMA_ADDITIONALPROPERTIES")

    def test_valid_subject_cannot_be_declared_rejected(self):
        self.descriptor["invalid_content"] = {"value": 1}
        self.write(self.DESCRIPTOR, self.descriptor)
        self.scenarios = [self.direct()]
        self.assert_failure("observed []")

    def test_required_field_witness_distinguishes_different_missing_properties(self):
        self.schema["required"] = ["value", "other"]
        self.schema["properties"]["other"] = {"type": "integer"}
        self.write(self.SCHEMA_PATH, self.schema)
        self.descriptor["invalid_content"] = {"other": 1}
        self.write(self.DESCRIPTOR, self.descriptor)
        scenario = self.direct()
        scenario["expected_errors"] = [{"error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required", "missing_properties": ["other"]}]
        self.scenarios = [scenario]
        self.assert_failure('"missing_properties":["value"]')

    def test_rejected_mutation_base_cannot_produce_a_successful_scenario(self):
        self.write(self.BASE, {"value": -2})
        self.scenarios = [self.mutation()]
        self.assert_failure("Mutation base is rejected")

    def test_mutation_cannot_add_a_missing_field(self):
        self.scenarios = [self.mutation()]
        self.scenarios[0]["operations"][0]["path"] = "/missing"
        self.assert_failure("Unresolved JSON Pointer")

    def test_mutation_rejects_duplicate_target_paths(self):
        self.scenarios = [self.mutation()]
        self.scenarios[0]["operations"].append({"op": "replace", "path": "/value", "value": -2})
        self.assert_failure("Duplicate mutation target")

    def test_mutation_can_remove_existing_fields_with_precise_required_witness(self):
        self.scenarios = [self.mutation()]
        self.scenarios[0]["operations"] = [{"op": "remove", "path": "/value"}]
        del self.scenarios[0]["mutation_value_bindings"]
        self.scenarios[0]["expected_errors"] = [{"error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "", "schema_pointer": "/required", "missing_properties": ["value"]}]
        self.scenarios[0]["owner_bindings"] = [
            {"path": self.SCHEMA_PATH, "pointer": "/required", "value": ["value"]},
            {"path": self.SCHEMA_PATH, "pointer": "/required/0", "value": "value"},
        ]
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])

    def test_missing_required_member_cannot_substitute_for_the_intended_member(self):
        self.schema["required"] = ["relation_graph_ref", "pattern_vector_ref"]
        self.schema["properties"] = {
            "relation_graph_ref": {"type": "string"},
            "pattern_vector_ref": {"type": "string"},
        }
        self.write(self.SCHEMA_PATH, self.schema)
        self.write(self.BASE, {"relation_graph_ref": "relation", "pattern_vector_ref": "pattern"})
        scenario = self.mutation()
        scenario["operations"] = [{"op": "remove", "path": "/pattern_vector_ref"}]
        del scenario["mutation_value_bindings"]
        scenario["expected_errors"] = [{
            "error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "",
            "schema_pointer": "/required", "missing_properties": ["pattern_vector_ref"],
        }]
        scenario["owner_bindings"] = [
            {"path": self.SCHEMA_PATH, "pointer": "/required", "value": self.schema["required"]},
            {"path": self.SCHEMA_PATH, "pointer": "/required/0", "value": "relation_graph_ref"},
        ]
        self.scenarios = [scenario]
        self.assert_failure("exact owning array binding")
        scenario["owner_bindings"].append({
            "path": self.SCHEMA_PATH, "pointer": "/required/1", "value": "pattern_vector_ref",
        })
        self.assert_failure("required member was not exercised")
        scenario["operations"] = [{"op": "remove", "path": "/relation_graph_ref"}]
        scenario["expected_errors"][0]["missing_properties"] = ["relation_graph_ref"]
        scenario["owner_bindings"].pop()
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])

    def test_whole_required_array_cannot_replace_concrete_missing_member_bindings(self):
        scenario = self.mutation()
        scenario["operations"] = [{"op": "remove", "path": "/value"}]
        del scenario["mutation_value_bindings"]
        scenario["expected_errors"] = [{
            "error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "",
            "schema_pointer": "/required", "missing_properties": ["value"],
        }]
        scenario["owner_bindings"] = [{
            "path": self.SCHEMA_PATH, "pointer": "/required", "value": ["value"],
        }]
        self.scenarios = [scenario]
        self.assert_failure("exact owning array binding")

    def test_scalar_mutation_requires_an_explicit_exact_source_value(self):
        self.scenarios = [self.mutation()]
        del self.scenarios[0]["mutation_value_bindings"]
        self.assert_failure("explicit mutation value binding")
        self.scenarios = [self.mutation()]
        self.scenarios[0]["operations"][0]["value"] = -2
        self.assert_failure("exact source literal")
        self.scenarios = [self.mutation()]
        self.scenarios[0]["owner_bindings"].pop()
        self.assert_failure("exact source owner")

    def test_mutation_value_binding_cannot_select_a_missing_or_non_scalar_operation(self):
        for index in (1, True):
            with self.subTest(index=index):
                self.scenarios = [self.mutation()]
                self.scenarios[0]["mutation_value_bindings"][0]["operation_index"] = index
                self.assertTrue(self.run_check()[0])
        scenario = self.mutation()
        scenario["operations"] = [{"op": "remove", "path": "/value"}]
        scenario["expected_errors"] = [{
            "error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "",
            "schema_pointer": "/required", "missing_properties": ["value"],
        }]
        scenario["owner_bindings"] = [
            {"path": self.SCHEMA_PATH, "pointer": "/required", "value": ["value"]},
            {"path": self.SCHEMA_PATH, "pointer": "/required/0", "value": "value"},
        ]
        self.scenarios = [scenario]
        self.assert_failure("each scalar replacement exactly once")

    def test_mutation_value_binding_must_be_used_once_and_only_in_mutation_mode(self):
        self.scenarios = [self.mutation()]
        duplicate = copy.deepcopy(self.scenarios[0]["mutation_value_bindings"][0])
        self.write("data/validation/intent.json", {"negative_value": -1, "same_value": -1})
        self.scenarios[0]["owner_bindings"].append({
            "path": "data/validation/intent.json", "pointer": "/same_value", "value": -1,
        })
        duplicate["source_pointer"] = "/same_value"
        self.scenarios[0]["mutation_value_bindings"].append(duplicate)
        self.assert_failure("each scalar replacement exactly once")
        bindings = self.scenarios[0]["mutation_value_bindings"][:1]
        for mode in ("direct", "lexical"):
            with self.subTest(mode=mode):
                self.scenarios = [getattr(self, mode)()]
                self.scenarios[0]["mutation_value_bindings"] = bindings
                self.assert_failure("should not be valid")

    def test_unsafe_repository_paths_are_rejected_in_each_file_role(self):
        for mode, field in (("direct", "descriptor_path"), ("mutation", "base_path"), ("lexical", "rule_path")):
            for path in ("../outside.json", "C:/outside.json", "examples\\outside.json"):
                with self.subTest(mode=mode, field=field, path=path):
                    scenario = getattr(self, mode)()
                    scenario[field] = path
                    self.scenarios = [scenario]
                    errors, _ = self.run_check()
                    self.assertTrue(errors)

    def test_duplicate_scenario_id_or_execution_binding_is_rejected(self):
        self.scenarios.append(copy.deepcopy(self.scenarios[0]))
        self.assert_failure("Duplicate rejection scenario")
        self.scenarios[1]["scenario_id"] = "second.id"
        self.assert_failure("Duplicate rejection scenario")

    def test_unknown_external_schema_is_not_retrieved(self):
        self.scenarios[0]["schema_id"] = "https://unknown.invalid/record.json"
        self.assert_failure("https://unknown.invalid/record.json")

    def test_annotation_object_cannot_be_selected_as_owning_schema(self):
        self.schema["metadata"] = {"type": "integer"}
        self.write(self.SCHEMA_PATH, self.schema)
        self.scenarios[0]["schema_id"] = self.SCHEMA_ID + "#/metadata"
        self.assert_failure("Target does not resolve to a schema location")

    def test_empty_expected_witnesses_are_rejected_by_catalog_schema(self):
        self.scenarios[0]["expected_errors"] = []
        self.assert_failure("should be non-empty")

    def test_inapplicable_mode_fields_are_rejected_by_catalog_schema(self):
        self.scenarios[0]["rule_path"] = "data/validation/terms.json"
        self.assert_failure("should not be valid")

    def test_unsupported_mutation_operations_and_root_removal_are_rejected(self):
        for operation in ({"op": "add", "path": "/new", "value": 1}, {"op": "remove", "path": ""}, {"op": "remove", "path": "/value", "value": 1}, {"op": "replace", "path": "/value"}):
            with self.subTest(operation=operation):
                self.scenarios = [self.mutation()]
                self.scenarios[0]["operations"] = [operation]
                self.assertTrue(self.run_check()[0])

    def test_unresolved_descriptor_pointer_fails_closed(self):
        self.scenarios[0]["descriptor_bindings"][1]["pointer"] = "/missing"
        self.assert_failure("Unresolved JSON Pointer")

    def test_wrong_or_incomplete_lexical_witness_set_fails(self):
        original = self.lexical()
        for matches in ([{"subject_pointer": "/invalid_content", "term": "Unity"}], [{"subject_pointer": "/other", "term": "Unity"}], original["expected_matches"] + [{"subject_pointer": "/invalid_content", "term": "Unreal"}]):
            with self.subTest(matches=matches):
                self.scenarios = [{**original, "expected_matches": matches}]
                self.assert_failure("Expected complete rejection witnesses")

    def test_every_lexical_array_subject_requires_its_own_rejection(self):
        self.scenarios = [self.lexical(["Unity", "ordinary portable data"])]
        self.scenarios[0]["expected_matches"] = [{"subject_pointer": "/invalid_content/0", "term": "Unity"}]
        self.assert_failure("at '/invalid_content/1' is accepted")

    def test_lexical_array_reports_exact_member_pointers(self):
        self.scenarios = [self.lexical(["UNITY", "godot"])]
        self.scenarios[0]["expected_matches"] = [
            {"subject_pointer": "/invalid_content/0", "term": "Unity"},
            {"subject_pointer": "/invalid_content/1", "term": "Godot"},
        ]
        self.approve_scenarios()
        self.assertEqual([], self.run_check()[0])

    def test_lexical_subject_cannot_use_its_descriptor_as_a_rule_file(self):
        self.scenarios = [self.lexical()]
        self.scenarios[0]["rule_path"] = self.DESCRIPTOR
        self.assert_failure("does not match")

    def test_unresolved_owner_terms_pointer_and_malformed_term_values_fail(self):
        original = self.lexical()
        self.scenarios = [{**original, "reject_terms_pointer": "/missing"}]
        self.assert_failure("Unresolved JSON Pointer")
        for terms in ([], [""], [1], ["Unity", "Unity"]):
            with self.subTest(terms=terms):
                self.write("data/validation/terms.json", {"reject_terms": terms})
                scenario = copy.deepcopy(original)
                scenario["owner_bindings"][0]["value"] = terms
                self.scenarios = [scenario]
                self.assert_failure("reject_terms")

    def test_schema_catalog_drift_blocks_scenario_execution(self):
        self.write("data/schemas/undeclared.json", {"$schema": fixtures.DIALECT, "$id": "https://ywe.local/undeclared", "type": "string"})
        self.assert_failure("Schema catalog coverage differs")

    def player_units(self):
        scenario = self.direct()
        self.descriptor = {
            "schema_id": "ywe.phase_10_invalid_player_state_rejection_cases.v1",
            "cases": [
                {"case_id": "first", "reason": "negative value", "subject": {"value": -1}},
                {"case_id": "second", "reason": "different negative value", "subject": {"value": -2}},
            ],
        }
        self.write(self.DESCRIPTOR, self.descriptor)
        result = []
        for index in range(2):
            unit = f"/cases/{index}"
            selected = copy.deepcopy(scenario)
            selected.update(
                scenario_id=f"player.{index}", descriptor_unit_pointer=unit,
                descriptor_sha256=rejection.normalized_text_sha256(self.root / self.DESCRIPTOR),
                subject_pointer=unit + "/subject",
                descriptor_bindings=[
                    {"pointer": "/schema_id", "value": self.descriptor["schema_id"]},
                    {"pointer": unit + "/reason", "value": self.descriptor["cases"][index]["reason"]},
                    {"pointer": unit + "/subject", "value": self.descriptor["cases"][index]["subject"]},
                ],
            )
            result.append(selected)
        return result

    def test_player_collection_reports_each_executed_case_pointer(self):
        self.scenarios = self.player_units()
        self.approve_scenarios()
        errors, results = self.run_check()
        self.assertEqual([], errors)
        self.assertEqual(["/cases/0", "/cases/1"], [item["descriptor_unit_pointer"] for item in results])

    def test_player_unit_cannot_use_another_units_reason_binding(self):
        self.scenarios = self.player_units()
        self.scenarios[1]["descriptor_bindings"][1] = self.scenarios[0]["descriptor_bindings"][1]
        self.assert_failure("expected-reason binding")

    def test_selected_player_subject_cannot_cross_case_boundary(self):
        self.scenarios = self.player_units()[:1]
        self.scenarios[0]["subject_pointer"] = "/cases/1/subject"
        self.scenarios[0]["descriptor_bindings"].append({"pointer": "/cases/1/subject", "value": {"value": -2}})
        self.assert_failure("outside its descriptor unit")

    def test_unit_pointer_requires_the_known_collection_format(self):
        self.scenarios = self.player_units()[:1]
        self.descriptor["schema_id"] = "unknown_collection"
        self.write(self.DESCRIPTOR, self.descriptor)
        self.update_digest()
        self.assert_failure("declared player rejection collection")

    def test_unresolved_player_case_cannot_claim_execution(self):
        self.scenarios = self.player_units()[:1]
        self.scenarios[0]["descriptor_unit_pointer"] = "/cases/2"
        self.assert_failure("Unresolved JSON Pointer")

    def test_noncanonical_collection_unit_pointer_fails_shape_validation(self):
        self.scenarios = self.player_units()[:1]
        self.scenarios[0]["descriptor_unit_pointer"] = "/cases/01"
        self.assert_failure("does not match")

    def test_expected_rejection_reason_is_scoped_to_established_reward_formats(self):
        for schema_id in ("wolf_manifestation_event_schema", "quest_reward_resolution_packet_schema", "unrelated"):
            with self.subTest(schema_id=schema_id):
                self.descriptor = {
                    "schema_id": schema_id, "invalid_content": {"value": -1},
                    "invalid_reason": "negative value", "expected_rejection_reason": "negative value",
                }
                self.write(self.DESCRIPTOR, self.descriptor)
                scenario = self.direct()
                scenario["descriptor_bindings"][0] = {"pointer": "/expected_rejection_reason", "value": "negative value"}
                self.scenarios = [scenario]
                if schema_id == "unrelated":
                    self.assert_failure("expected-reason binding")
                else:
                    self.approve_scenarios()
                    self.assertEqual([], self.run_check()[0])


class MutationPointerTests(unittest.TestCase):
    def test_escaped_object_members_and_array_indices_are_selected_exactly(self):
        original = {"a/b": {"~key": [1, 2]}}
        changed = rejection.apply_operations(original, [{"op": "replace", "path": "/a~1b/~0key/1", "value": 3}, {"op": "remove", "path": "/a~1b/~0key/0"}])
        self.assertEqual({"a/b": {"~key": [3]}}, changed)
        self.assertEqual({"a/b": {"~key": [1, 2]}}, original)

    def test_invalid_array_and_pointer_forms_cannot_mutate(self):
        for pointer in ("/items/-", "/items/-1", "/items/01", "/items/3", "/bad~2", "#", "items/0"):
            with self.subTest(pointer=pointer):
                with self.assertRaises(ValueError):
                    rejection.apply_operations({"items": [1]}, [{"op": "replace", "path": pointer, "value": 2}])

    def test_root_scalar_replacement_is_explicit_and_does_not_claim_a_packet(self):
        self.assertTrue(rejection.apply_operations(False, [{"op": "replace", "path": "", "value": True}]))


class RegisteredScenarioIntentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry, errors = fixtures.load_registry(ROOT)
        if errors:
            raise AssertionError(errors)
        cls.scenarios = {
            scenario["scenario_id"]: scenario
            for scenario in fixtures.load_json(ROOT / rejection.SCENARIO_CATALOG)["scenarios"]
        }

    def scenario(self, identifier):
        return copy.deepcopy(self.scenarios[identifier])

    def assert_rejected_catalog_claim(self, scenario):
        errors, results = rejection.evaluate_scenarios(ROOT, self.registry, [scenario])
        self.assertTrue(errors)
        self.assertEqual([], results)
        return errors

    def test_original_catalog_intent_bindings_all_pass(self):
        errors, results = rejection.evaluate_scenarios(ROOT, self.registry, list(self.scenarios.values()))
        self.assertEqual([], errors)
        self.assertEqual(26, len(results))
        self.assertEqual(2, sum(item["descriptor_path"] == "data/realm/realm_transition_examples.yaml"
                                for item in results))

    def test_npc_required_member_substitution_fails_with_retained_and_appended_owners(self):
        scenario = self.scenario("m2.phase12.npc_missing_relation_graph")
        scenario["operations"] = [{"op": "remove", "path": "/pattern_vector_ref"}]
        scenario["expected_errors"][0]["missing_properties"] = ["pattern_vector_ref"]
        errors = self.assert_rejected_catalog_claim(scenario)
        self.assertTrue(any("exact owning array binding" in error for error in errors))
        path = "data/schemas/npc_manifest_candidate_schema.json"
        required = fixtures.load_json(ROOT / path)["required"]
        scenario["owner_bindings"].append({
            "path": path, "pointer": "/required/" + str(required.index("pattern_vector_ref")),
            "value": "pattern_vector_ref",
        })
        errors = self.assert_rejected_catalog_claim(scenario)
        self.assertTrue(any("required member was not exercised" in error for error in errors))

    def test_unused_required_member_cannot_be_consumed_as_a_scalar_literal_source(self):
        scenario = self.scenario("m2.phase12.npc_missing_relation_graph")
        scenario["operations"] = [
            {"op": "remove", "path": "/pattern_vector_ref"},
            {"op": "replace", "path": "/npc_candidate_id", "value": "relation_graph_ref"},
        ]
        scenario["expected_errors"][0]["missing_properties"] = ["pattern_vector_ref"]
        path = "data/schemas/npc_manifest_candidate_schema.json"
        required = fixtures.load_json(ROOT / path)["required"]
        scenario["owner_bindings"].append({
            "path": path, "pointer": "/required/" + str(required.index("pattern_vector_ref")),
            "value": "pattern_vector_ref",
        })
        scenario["mutation_value_bindings"] = [{
            "operation_index": 1, "source_path": path,
            "source_pointer": "/required/" + str(required.index("relation_graph_ref")),
            "source_value": "relation_graph_ref", "relation": "equal",
        }]
        errors = self.assert_rejected_catalog_claim(scenario)
        self.assertTrue(any("required member was not exercised" in error for error in errors))

    def test_unused_initial_identity_const_cannot_be_consumed_as_a_literal_source(self):
        scenario = self.scenario("player.initial_identity_upfront")
        scenario["operations"] = [
            {"op": "remove", "path": "/celestial_identity_state_ref"},
            {"op": "replace", "path": "/mortal_identity_ref", "value": "veiled"},
        ]
        scenario["expected_errors"] = [{
            "error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "",
            "schema_pointer": "/required", "missing_properties": ["celestial_identity_state_ref"],
        }]
        path = "data/schemas/player_runtime_state_schema.json"
        prefix = "/$defs/initial_identity"
        required = fixtures.load_json(ROOT / path)["$defs"]["initial_identity"]["required"]
        scenario["owner_bindings"].extend([
            {"path": path, "pointer": prefix + "/required", "value": required},
            {"path": path, "pointer": prefix + "/required/1", "value": "celestial_identity_state_ref"},
        ])
        scenario["mutation_value_bindings"] = [{
            "operation_index": 1, "source_path": path,
            "source_pointer": prefix + "/properties/celestial_identity_initial_state/const",
            "source_value": "veiled", "relation": "equal",
        }]
        errors = self.assert_rejected_catalog_claim(scenario)
        self.assertTrue(any("not exercised or mapped" in error for error in errors))

    def test_unused_component_role_const_cannot_be_consumed_as_a_literal_source(self):
        scenario = self.scenario("player.asp_top_level_authority")
        path = "data/schemas/player_runtime_state_schema.json"
        schema = fixtures.load_json(ROOT / path)
        role_pointer = "/properties/authority/properties/ash_pattern_system_role/const"
        role = fixtures.json_pointer(schema, role_pointer)
        engine_pointer = "/properties/authority/properties/engine/const"
        scenario["operations"][0]["path"] = "/authority/engine"
        scenario["operations"].append({"op": "replace", "path": "/player_id", "value": role})
        scenario["expected_errors"] = [{
            "error_id": "JSON_SCHEMA_CONST", "instance_pointer": "/authority/engine",
            "schema_pointer": engine_pointer,
        }]
        scenario["owner_bindings"].append({
            "path": path, "pointer": engine_pointer, "value": fixtures.json_pointer(schema, engine_pointer),
        })
        scenario["mutation_value_bindings"].append({
            "operation_index": 1, "source_path": path, "source_pointer": role_pointer,
            "source_value": role, "relation": "equal",
        })
        errors = self.assert_rejected_catalog_claim(scenario)
        self.assertTrue(any("not exercised or mapped" in error for error in errors))

    def test_all_three_string_substitutions_fail_with_sources_and_errors_unchanged(self):
        for identifier in (
            "m2.ability.generic_xp_only_unlock",
            "player.initial_identity_upfront",
            "player.asp_top_level_authority",
        ):
            with self.subTest(scenario=identifier):
                scenario = self.scenario(identifier)
                scenario["operations"][0]["value"] = "arbitrary-unrelated-bogus"
                errors = self.assert_rejected_catalog_claim(scenario)
                self.assertTrue(any("exact source literal" in error for error in errors))

    def test_all_boolean_substitutions_preserve_json_scalar_type(self):
        counts = {"original": 0, "realm": 0}
        for original in self.scenarios.values():
            for index, operation in enumerate(original.get("operations", [])):
                if operation["op"] != "replace" or type(operation["value"]) is not bool:
                    continue
                counts["realm" if original["scenario_id"].startswith("realm.") else "original"] += 1
                with self.subTest(scenario=original["scenario_id"], operation=index):
                    scenario = self.scenario(original["scenario_id"])
                    scenario["operations"][index]["value"] = int(operation["value"])
                    self.assert_rejected_catalog_claim(scenario)
        self.assertEqual({"original": 8, "realm": 5}, counts)

    def test_boolean_inverse_must_use_the_executed_const_at_the_same_target(self):
        scenario = self.scenario("phase17.wolf_morality")
        source_pointer = "/properties/permanent_death/const"
        scenario["owner_bindings"].append({
            "path": "data/schemas/wolf_companion_trace_schema.json",
            "pointer": source_pointer, "value": False,
        })
        scenario["mutation_value_bindings"][0]["source_pointer"] = source_pointer
        errors = self.assert_rejected_catalog_claim(scenario)
        self.assertTrue(any("same target" in error for error in errors))

    def test_boolean_inverse_cannot_be_replaced_with_literal_equality(self):
        scenario = self.scenario("phase17.wolf_morality")
        scenario["mutation_value_bindings"][0]["relation"] = "equal"
        self.assert_rejected_catalog_claim(scenario)


class RealmRejectionIntentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry, errors = fixtures.load_registry(ROOT)
        if errors:
            raise AssertionError(errors)
        cls.scenarios = [item for item in fixtures.load_json(ROOT / rejection.SCENARIO_CATALOG)["scenarios"]
                         if item["scenario_id"].startswith("realm.")]
        if len(cls.scenarios) != 2:
            raise AssertionError("Both original realm unlawful descriptions must execute")

    def assert_invalid(self, scenario, message):
        errors, results = rejection.evaluate_scenarios(ROOT, self.registry, [scenario])
        self.assertEqual([], results)
        self.assertTrue(any(message in error for error in errors), errors)

    def test_both_units_execute_complete_source_owned_witnesses_without_source_writes(self):
        paths = {item["descriptor_path"] for item in self.scenarios}
        paths.update(owner["path"] for item in self.scenarios for owner in item["owner_bindings"])
        before = {path: (ROOT / path).read_bytes() for path in paths}
        errors, results = rejection.evaluate_scenarios(ROOT, self.registry, self.scenarios)
        self.assertEqual([], errors)
        self.assertEqual(["/unlawful_examples/0", "/unlawful_examples/1"],
                         [item["descriptor_unit_pointer"] for item in results])
        self.assertEqual(before, {path: (ROOT / path).read_bytes() for path in paths})

    def test_realm_unit_requires_its_whole_violated_rule_list_and_identity(self):
        for suffix in ("/violated_rules", "/example_id"):
            scenario = copy.deepcopy(self.scenarios[0])
            scenario["descriptor_bindings"] = [item for item in scenario["descriptor_bindings"]
                                               if not item["pointer"].endswith(suffix)]
            with self.subTest(suffix=suffix):
                self.assert_invalid(scenario, "identity and complete violated-rule bindings")

    def test_realm_unit_cannot_borrow_other_units_summary(self):
        scenario = copy.deepcopy(self.scenarios[1])
        scenario["descriptor_bindings"][1] = copy.deepcopy(self.scenarios[0]["descriptor_bindings"][1])
        self.assert_invalid(scenario, "expected-reason binding")

    def test_realm_projection_cannot_map_a_const_to_another_valid_source_rule(self):
        scenario = copy.deepcopy(self.scenarios[0])
        scenario["projection_bindings"][0].update({
            field: scenario["projection_bindings"][1][field]
            for field in ("source_path", "source_pointer", "source_value")
        })
        self.assert_invalid(scenario, "declared owning rule")

    def test_realm_units_require_the_declared_canonical_collection(self):
        scenario = copy.deepcopy(self.scenarios[0])
        scenario["descriptor_unit_pointer"] = "/lawful_examples/0"
        self.assert_invalid(scenario, "declared player rejection collection or realm unlawful collection")

    def test_realm_intended_reason_cannot_be_relabelled_with_the_other_units_vector(self):
        fields = ("owner_bindings", "projection_bindings", "mutation_value_bindings", "schema_id",
                  "base_path", "base_pointer", "operations", "expected_errors")
        for index in range(2):
            scenario = copy.deepcopy(self.scenarios[index])
            scenario.update({field: copy.deepcopy(self.scenarios[1 - index][field]) for field in fields})
            with self.subTest(unit=index):
                self.assert_invalid(scenario, "own its exact declared unlawful unit")

    def test_realm_rejection_must_execute_all_declared_violated_rules(self):
        scenario = copy.deepcopy(self.scenarios[0])
        scenario["operations"].pop()
        scenario["expected_errors"].pop()
        scenario["mutation_value_bindings"].pop()
        removed = scenario["projection_bindings"].pop()
        scenario["owner_bindings"] = [item for item in scenario["owner_bindings"] if
                                      (item["path"], item["pointer"]) not in {
                                          (rejection.PROJECTION_SCHEMA_PATH, removed["assertion_pointer"]),
                                          (removed["source_path"], removed["source_pointer"]),
                                      }]
        self.assert_invalid(scenario, "every declared violated rule")

    def test_realm_reason_text_cannot_be_rejected_by_unrelated_lexical_terms(self):
        scenario = copy.deepcopy(self.scenarios[1])
        for field in ("schema_id", "base_path", "base_pointer", "operations", "expected_errors",
                      "projection_bindings", "mutation_value_bindings"):
            scenario.pop(field)
        path = "data/validation/ability_combat_quest_use_validation_rules.json"
        pointer = "/allowed_use_modes"
        terms = fixtures.json_pointer(fixtures.load_json(ROOT / path), pointer)
        scenario.update(mode="lexical", validation_scope="subject", subject_pointer="/unlawful_examples/1/summary",
                        rule_path=path, reject_terms_pointer=pointer,
                        owner_bindings=[{"path": path, "pointer": pointer, "value": terms}],
                        expected_matches=[{"subject_pointer": "/unlawful_examples/1/summary", "term": "perception"}])
        self.assertEqual([], list(fixtures.Draft202012Validator(
            {"$ref": rejection.SCENARIO_SCHEMA_ID}, registry=self.registry
        ).iter_errors({"schema_ref": rejection.PROJECTION_SCHEMA_PATH,
                       "artifact_type": "ywe_rejection_scenario_catalog", "artifact_version": "1.0.0",
                       "scenarios": [scenario]})))
        self.assert_invalid(scenario, "declared assertion projection mutation")

    def test_each_realm_const_requires_its_source_mapping_and_exact_witness(self):
        for original in self.scenarios:
            for index in range(len(original["projection_bindings"])):
                with self.subTest(scenario=original["scenario_id"], assertion=index):
                    scenario = copy.deepcopy(original)
                    scenario["projection_bindings"].pop(index)
                    self.assert_invalid(scenario, "explicit source mapping")
                    scenario = copy.deepcopy(original)
                    scenario["expected_errors"].pop(index)
                    self.assert_invalid(scenario, "complete rejection witnesses")




class ExecutionContractCorrespondenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry,errors=fixtures.load_registry(ROOT)
        if errors:
            raise AssertionError(errors)
        cls.document=fixtures.load_json(ROOT/rejection.EXECUTION_CONTRACTS_PATH)
        cls.scenarios=fixtures.load_json(ROOT/rejection.SCENARIO_CATALOG)["scenarios"]
        errors,cls.approved=rejection.validate_execution_contracts(ROOT,cls.registry,cls.document)
        if errors:
            raise AssertionError(errors)
        cls.by_id={item["scenario_id"]:item for item in cls.scenarios}

    def compare(self,scenario):
        return rejection.execution_contract_errors(ROOT,self.registry,scenario,self.approved)

    def test_all_26_authentic_executions_and_exact_approved_controls_pass(self):
        self.assertEqual(26,len(self.approved))
        self.assertEqual([],rejection.execution_contract_inventory_errors(self.scenarios,self.approved))
        errors,results=rejection.evaluate_scenarios(ROOT,self.registry,self.scenarios)
        self.assertEqual([],errors)
        self.assertEqual(26,len(results))
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["scenario_id"]):
                self.assertEqual([],self.compare(scenario))

    def test_four_whole_execution_swaps_preserve_descriptor_and_low_level_checks_but_are_rejected(self):
        keep={"scenario_id","descriptor_path","descriptor_unit_pointer","descriptor_sha256",
              "hash_algorithm","descriptor_bindings","description"}
        pairs=(("phase17.wolf_morality","phase17.permanent_wolf_death"),
               ("phase17.permanent_wolf_death","phase17.wolf_morality"),
               ("player.asp_top_level_authority","player.wolf_morality"),
               ("player.wolf_morality","player.asp_top_level_authority"))
        for target,donor in pairs:
            with self.subTest(target=target,donor=donor):
                original=self.by_id[target]
                swapped={k:copy.deepcopy(v) for k,v in original.items() if k in keep}
                swapped.update({k:copy.deepcopy(v) for k,v in self.by_id[donor].items() if k not in keep})
                for key in keep:
                    self.assertEqual(original.get(key),swapped.get(key))
                # Isolate the reviewed correspondence guard to reproduce the
                # original independently valid but unrelated rejection.
                with patch.object(rejection, "execution_contract_errors", return_value=[]):
                    errors,results=rejection.evaluate_scenarios(ROOT,self.registry,[swapped])
                self.assertEqual([],errors)
                self.assertEqual(1,len(results))
                errors,results=rejection.evaluate_scenarios(ROOT,self.registry,[swapped])
                self.assertEqual([],results)
                self.assertTrue(any("differs from approved descriptor contract" in e for e in errors), errors)
                self.assertTrue(any("differs from approved descriptor contract" in e for e in self.compare(swapped)))

    def test_same_execution_under_unknown_id_cannot_clear_coverage(self):
        scenario=copy.deepcopy(self.scenarios[0])
        scenario["scenario_id"]="unreviewed.claim"
        self.assertTrue(any("Unapproved" in e for e in self.compare(scenario)))
        self.assertTrue(rejection.execution_contract_inventory_errors([scenario],self.approved))

    def test_duplicate_approved_id_and_unit_fail_closed(self):
        document=copy.deepcopy(self.document)
        document["contracts"].append(copy.deepcopy(document["contracts"][0]))
        errors,index=rejection.validate_execution_contracts(ROOT,self.registry,document)
        self.assertEqual({},index)
        self.assertTrue(any("Duplicate approved rejection scenario ID" in e for e in errors))
        self.assertTrue(any("Duplicate approved rejection descriptor unit" in e for e in errors))

    def test_duplicate_approved_unit_under_new_id_fails_closed(self):
        document=copy.deepcopy(self.document)
        row=copy.deepcopy(document["contracts"][0])
        row["scenario_id"]="another-approved-id"
        document["contracts"].append(row)
        errors,index=rejection.validate_execution_contracts(ROOT,self.registry,document)
        self.assertEqual({},index)
        self.assertTrue(any("Duplicate approved rejection descriptor unit" in e for e in errors))

    def test_missing_extra_and_duplicate_catalog_rows_cannot_clear_inventory(self):
        self.assertTrue(rejection.execution_contract_inventory_errors(self.scenarios[:-1],self.approved))
        extra=copy.deepcopy(self.scenarios[0]);extra["scenario_id"]="unapproved"
        self.assertTrue(rejection.execution_contract_inventory_errors(self.scenarios+[extra],self.approved))
        self.assertTrue(rejection.execution_contract_inventory_errors(self.scenarios+[self.scenarios[0]],self.approved))

    def test_wrong_ledger_wrapper_empty_or_malformed_rows_fail_closed(self):
        candidates=[]
        for key,value in (("artifact_type","other"),("artifact_version","2.0.0"),("contracts",[])):
            value_doc=copy.deepcopy(self.document);value_doc[key]=value;candidates.append(value_doc)
        value_doc=copy.deepcopy(self.document);value_doc["contracts"][0].pop("owner_bindings");candidates.append(value_doc)
        value_doc=copy.deepcopy(self.document);value_doc["unrecognized"]=True;candidates.append(value_doc)
        for document in candidates:
            with self.subTest(document_key=set(document)):
                errors,index=rejection.validate_execution_contracts(ROOT,self.registry,document)
                self.assertTrue(errors)
                self.assertEqual({},index)

    def test_absent_default_unit_and_cosmetic_description_are_supported_equivalents(self):
        scenario=copy.deepcopy(self.scenarios[0])
        scenario["descriptor_unit_pointer"]=""
        scenario["description"]="A revised human explanation of the same exact scoped assertion."
        self.assertEqual([],self.compare(scenario))
        scenario.pop("descriptor_unit_pointer")
        self.assertEqual([],self.compare(scenario))

    def test_source_reason_digest_and_binding_changes_are_correspondence_critical(self):
        for field in ("descriptor_sha256","descriptor_path","descriptor_bindings"):
            scenario=copy.deepcopy(self.scenarios[0])
            if field=="descriptor_sha256": scenario[field]="0"*64
            elif field=="descriptor_path": scenario[field]=self.scenarios[1][field]
            else: scenario[field][0]["value"]="Different intended reason"
            with self.subTest(field=field): self.assertTrue(self.compare(scenario))

    def test_scalar_boolean_integer_and_float_remain_distinct_json_values(self):
        original=self.by_id["phase17.wolf_morality"]
        for value in (1,1.0,"true"):
            scenario=copy.deepcopy(original);scenario["operations"][0]["value"]=value
            with self.subTest(value=repr(value)): self.assertTrue(self.compare(scenario))

    def test_same_witness_and_mutation_cannot_swap_source_owner_projection_or_scalar_mapping(self):
        for identifier,field in (("phase17.wolf_morality","owner_bindings"),
                                 ("realm.rte_invalid_fast_travel_bypass","projection_bindings"),
                                 ("phase17.wolf_morality","mutation_value_bindings")):
            scenario=copy.deepcopy(self.by_id[identifier]);scenario[field][0][next(iter(scenario[field][0]))]="wrong"
            with self.subTest(field=field): self.assertTrue(self.compare(scenario))

    def test_lexical_subject_rule_terms_and_match_set_all_belong_to_approved_contract(self):
        original=self.by_id["slice.platform_runtime_subject"]
        for field in ("subject_pointer","rule_path","reject_terms_pointer","expected_matches"):
            scenario=copy.deepcopy(original)
            if field=="expected_matches": scenario[field]=scenario[field][:-1]
            elif field=="rule_path": scenario[field]="data/validation/another.json"
            else: scenario[field]="/another"
            with self.subTest(field=field): self.assertTrue(self.compare(scenario))

    def test_missing_file_does_not_create_approval_from_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            errors,index=rejection.load_execution_contracts(Path(temporary),self.registry)
        self.assertTrue(errors)
        self.assertEqual({},index)

    def test_generic_framework_can_author_one_independent_contract_without_production_rows(self):
        scenario={"scenario_id":"synthetic.negative_integer","descriptor_path":"examples/rejection.json",
          "descriptor_sha256":"1"*64,"hash_algorithm":"sha256_utf8_lf_normalized",
          "descriptor_bindings":[{"pointer":"/invalid_reason","value":"negative value"},
                                 {"pointer":"/invalid_content","value":{"value":-1}}],
          "owner_bindings":[{"path":"data/schemas/record.json","pointer":"/properties/value/minimum","value":0}],
          "mode":"direct","validation_scope":"subject","description":"Authored synthetic integer assertion.",
          "subject_pointer":"/invalid_content","schema_id":"https://ywe.local/schemas/record.json",
          "expected_errors":[{"error_id":"JSON_SCHEMA_MINIMUM","instance_pointer":"/value","schema_pointer":"/properties/value/minimum"}]}
        document={"schema_ref":self.document["schema_ref"],"artifact_type":self.document["artifact_type"],
                  "artifact_version":"1.0.0","contracts":[copy.deepcopy(scenario)]}
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/rejection.EXECUTION_CONTRACTS_PATH
            path.parent.mkdir(parents=True);path.write_text(json.dumps(document),encoding="utf-8")
            errors,index=rejection.load_execution_contracts(root,self.registry)
            self.assertEqual([],errors)
            self.assertEqual([],rejection.execution_contract_errors(root,self.registry,scenario,index))
            self.assertEqual([],rejection.execution_contract_inventory_errors([scenario],index))
            scenario["expected_errors"][0]["schema_pointer"]="/properties/value/maximum"
            self.assertTrue(rejection.execution_contract_errors(root,self.registry,scenario,index))


if __name__ == "__main__":
    unittest.main()
