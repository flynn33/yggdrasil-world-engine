from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import check_fixture_catalog as fixtures
import check_m2_validation_methods as methods


class ValidationMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="ywe-m2-method-tests-")
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name) / "checkout"
        subprocess.run(["git", "clone", "--quiet", "--shared", "--no-hardlinks", str(ROOT), str(cls.root)],
                       check=True, capture_output=True)
        errors = []
        for relative in methods.baseline.repository_candidate_paths(ROOT, errors):
            source, target = ROOT / relative, cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        if errors:
            raise AssertionError(errors)
        # The isolated checkout overlays new candidate paths; refresh its derived
        # classification counts without changing the source checkout's inventory.
        relative = "data/governance/artifact_classification_manifest.json"
        classification = fixtures.load_json(cls.root / relative)
        paths = methods.baseline.repository_candidate_paths(cls.root, errors)
        assignments = methods.baseline.effective_assignments(paths, classification, "classification", [], "Test overlay")
        counts = Counter(item["classification"] for item in assignments.values())
        classification["coverage"]["counts_by_class"] = {
            name: counts.get(name, 0) for name in classification["coverage"]["counts_by_class"]}
        (cls.root / relative).write_text(json.dumps(classification, indent=2) + "\n", encoding="utf-8")
        methods.baseline.effective_assignments(paths, classification, "classification", errors, "Test overlay")
        if errors:
            raise AssertionError(errors)
        cls.schema = fixtures.load_json(cls.root / methods.SCHEMA)
        cls.original_expectations = fixtures.load_json(cls.root / methods.EXPECTATIONS)
        cls.context = methods.load_context(cls.root)
        if cls.context["registry_errors"]:
            raise AssertionError(cls.context["registry_errors"])
        cls.actual_errors, cls.actual_results = methods.validation_errors(cls.root)

    def setUp(self):
        self.expectations = copy.deepcopy(self.original_expectations)

    def context_copy(self):
        context = dict(self.context)
        context["resources"] = copy.deepcopy(context["resources"])
        context["catalog"] = copy.deepcopy(context["catalog"])
        return context

    def registry_for(self, context):
        context["registry"] = Registry(retrieve=fixtures.deny_retrieval).with_resources(
            (entry["schema_id"], Resource.from_contents(schema)) for entry, schema in context["resources"]
        ).crawl()
        return context

    def schema_member(self, context, relative):
        return next(schema for entry, schema in context["resources"] if entry["path"] == relative)

    def replace_file(self, relative, value):
        path = self.root / relative
        previous = path.read_bytes()
        self.addCleanup(path.write_bytes, previous)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_actual_eight_methods_execute_and_pass(self):
        self.assertEqual([], self.actual_errors)
        self.assertEqual(list(methods.METHODS), [item["method"] for item in self.actual_results])
        self.assertTrue(all(item["execution_complete"] and item["status"] == "pass"
                            and item["executed_case_count"] > 0 for item in self.actual_results))
        self.assertEqual([], methods.method_coverage(self.actual_results)[0])

    def test_instance_and_negative_cover_every_actual_binding_and_scenario(self):
        by_method = {item["method"]: item for item in self.actual_results}
        self.assertEqual(len(self.context["catalog"]["fixtures"]), by_method["instance"]["executed_case_count"])
        expected = sum(item["expected_result"] == "reject" for item in self.context["catalog"]["fixtures"])
        scenarios = fixtures.load_json(self.root / methods.rejection.SCENARIO_CATALOG)["scenarios"]
        self.assertEqual(expected + len(scenarios), by_method["negative"]["executed_case_count"])

    def test_source_driven_properties_execute_all_members_and_required_removals(self):
        result = next(item for item in self.actual_results if item["method"] == "property")
        source = fixtures.load_instance(self.root / self.expectations["module_properties"]["source_path"])
        expected = 1 + sum(len(source["classification_enums"][family])
                           for _, family in methods.descriptors.MODULE_ENUM_BINDINGS)
        expected += len(source["canonical_validation_rules"]["required_fields"])
        self.assertEqual(expected, result["executed_case_count"])
        self.assertEqual(7, result["evidence"]["enum_family_count"])
        self.assertEqual(16, result["evidence"]["required_field_count"])

    def test_all_three_actual_mutants_are_killed_and_originals_preserved(self):
        paths = [item["schema_path"] for item in self.expectations["mutations"]]
        before = {path: (self.root / path).read_bytes() for path in paths}
        resources_before = copy.deepcopy(self.context["resources"])
        errors, cases, evidence = methods.mutation(self.root, self.context, self.expectations)
        self.assertEqual([], errors)
        self.assertEqual(list(methods.MUTANTS), [item["mutant_id"] for item in cases])
        self.assertTrue(all(item["killed"] and item["mutant_errors"] and not item["control_errors"] for item in cases))
        self.assertFalse(evidence["source_writes"])
        self.assertEqual(resources_before, self.context["resources"])
        self.assertEqual(before, {path: (self.root / path).read_bytes() for path in paths})

    def test_surviving_identifier_mutant_fails(self):
        self.expectations["mutations"][1]["operations"] = [{"op": "replace", "path": "/maxLength", "value": 255}]
        errors, cases, _ = methods.mutation(self.root, self.context, self.expectations)
        self.assertTrue(any("survived" in error for error in errors))
        self.assertFalse(cases[1]["killed"])
        self.assertEqual(cases[1]["original_expected_errors"], cases[1]["mutant_witnesses"])

    def test_mutant_rejecting_positive_control_cannot_count_as_killed(self):
        self.expectations["mutations"][0]["operations"] = [
            {"op": "replace", "path": "/properties/not_morality_system/const", "value": False}]
        errors, cases, _ = methods.mutation(self.root, self.context, self.expectations)
        self.assertTrue(errors)
        self.assertFalse(cases[0]["killed"])

    def test_original_exact_rejection_witness_must_pass_before_mutation(self):
        context = self.context_copy()
        selected = next(item for item in context["catalog"]["fixtures"]
                        if item["fixture_id"] == self.expectations["mutations"][0]["reject_fixture_id"])
        selected["expected_errors"][0]["schema_pointer"] = "/properties/wolf_scope/const"
        errors, cases, _ = methods.mutation(self.root, context, self.expectations)
        self.assertTrue(errors)
        self.assertTrue(cases[0]["control_errors"])
        self.assertFalse(cases[0]["killed"])

    def test_mutation_assertion_binding_distinguishes_boolean_from_number(self):
        self.expectations["mutations"][0]["before"] = 1
        with self.assertRaisesRegex(ValueError, "owning assertion changed"):
            methods.mutation(self.root, self.context, self.expectations)

    def test_no_effect_mutation_fails(self):
        self.expectations["mutations"][0]["operations"] = [
            {"op": "replace", "path": "/properties/not_morality_system/const", "value": True}]
        with self.assertRaisesRegex(ValueError, "no assertion change"):
            methods.mutation(self.root, self.context, self.expectations)

    def test_mutation_control_must_select_exact_owning_schema(self):
        self.expectations["mutations"][0]["positive_fixture_id"] = "m2.common.identifier.positive"
        with self.assertRaisesRegex(ValueError, "owning schema"):
            methods.mutation(self.root, self.context, self.expectations)

    def test_missing_mutation_control_fails(self):
        self.expectations["mutations"][0]["reject_fixture_id"] = "unregistered"
        with self.assertRaisesRegex(ValueError, "not uniquely registered"):
            methods.mutation(self.root, self.context, self.expectations)

    def test_enum_narrowing_is_detected_by_source_driven_properties(self):
        context = self.context_copy()
        schema = self.schema_member(context, "data/schemas/module_capability_manifest_schema.json")
        schema["properties"]["module_classification"]["enum"].remove("validation_service")
        self.registry_for(context)
        errors, cases, _ = methods.property_cases(self.root, context, self.expectations)
        self.assertTrue(any("enum:module_classification:validation_service" in error for error in errors))
        self.assertTrue(any(item["case_id"] == "enum:module_classification:validation_service"
                            and item["result"] == "fail" for item in cases))

    def test_required_weakening_is_detected_by_source_driven_properties(self):
        context = self.context_copy()
        self.schema_member(context, "data/schemas/module_capability_manifest_schema.json")["required"].remove("module_name")
        self.registry_for(context)
        errors, cases, _ = methods.property_cases(self.root, context, self.expectations)
        self.assertTrue(any("required:module_name" in error for error in errors))
        self.assertEqual([], next(item for item in cases if item["case_id"] == "required:module_name")["witnesses"])

    def test_unused_offline_reference_is_executed(self):
        context = self.context_copy()
        self.schema_member(context, "data/schemas/common/identifier.schema.json")["$defs"] = {
            "unused": {"$ref": "https://unregistered.invalid/schema"}}
        errors, cases, _ = methods.reference(self.root, context, self.expectations)
        self.assertTrue(any("unregistered.invalid" in error for error in errors))
        self.assertTrue(any(item["reference"] == "https://unregistered.invalid/schema" and item["result"] == "fail" for item in cases))

    def test_reference_like_annotations_are_not_schema_dependencies(self):
        context = self.context_copy()
        self.schema_member(context, "data/schemas/common/identifier.schema.json")["x-example"] = {
            "$ref": "https://unregistered.invalid/annotation"}
        errors, cases, _ = methods.reference(self.root, context, self.expectations)
        self.assertEqual([], errors)
        self.assertFalse(any(item["reference"] == "https://unregistered.invalid/annotation" for item in cases))

    def test_shadowed_nested_schema_identifier_fails(self):
        context = self.context_copy()
        self.schema_member(context, "data/schemas/common/identifier.schema.json")["$defs"] = {
            "nested": {"$id": "https://ywe.local/schemas/common/reference.schema.json", "type": "string"}}
        errors, _, _ = methods.identifier(self.root, context, self.expectations)
        self.assertTrue(any("Duplicate effective schema resource identifier" in error for error in errors))

    def test_duplicate_anchor_fails(self):
        context = self.context_copy()
        self.schema_member(context, "data/schemas/common/identifier.schema.json")["$defs"] = {
            "one": {"$anchor": "same", "type": "string"}, "two": {"$anchor": "same", "type": "integer"}}
        errors, _, _ = methods.identifier(self.root, context, self.expectations)
        self.assertTrue(any("Duplicate effective schema anchor" in error for error in errors))

    def test_duplicate_fixture_identifier_and_binding_fail(self):
        for field in ("fixture_id", "binding"):
            with self.subTest(field=field):
                context = self.context_copy()
                duplicate = copy.deepcopy(context["catalog"]["fixtures"][0])
                if field == "binding":
                    duplicate["fixture_id"] += ".different"
                context["catalog"]["fixtures"].append(duplicate)
                errors, _, _ = methods.identifier(self.root, context, self.expectations)
                self.assertTrue(any("Duplicate fixture identifier or binding" in error for error in errors))

    def test_wrong_dependency_witness_fails_exact_matching(self):
        ledger = fixtures.load_json(self.root / methods.descriptors.CASE_EXPECTATIONS_PATH)
        case = next(item for item in ledger["cases"] if item["instance_pointer"] == "/reject/pattern_two_record_inheritance_cycle")
        case["expected_errors"].pop()
        self.replace_file(methods.descriptors.CASE_EXPECTATIONS_PATH, ledger)
        errors, cases, _ = methods.dependency(self.root, self.context, self.expectations)
        self.assertTrue(any("pattern_two_record_inheritance_cycle" in error for error in errors))
        self.assertEqual(2, len(next(item for item in cases if item["instance_pointer"] == case["instance_pointer"])["witnesses"]))

    def test_dependency_missing_control_fails(self):
        self.expectations["dependency_case_pointers"].append("/reject/missing")
        with self.assertRaisesRegex(ValueError, "not uniquely declared"):
            methods.dependency(self.root, self.context, self.expectations)

    def test_meta_schema_executes_invalid_normative_declaration(self):
        self.replace_file("data/schemas/common/identifier.schema.json", dict(
            fixtures.load_json(self.root / "data/schemas/common/identifier.schema.json"), minLength=-1))
        errors, cases, _ = methods.meta_schema(self.root, self.context, self.expectations)
        self.assertTrue(any("identifier.schema.json" in error for error in errors))
        self.assertEqual("fail", next(item for item in cases if item["path"] == "data/schemas/common/identifier.schema.json")["result"])

    def test_expectations_cannot_remove_relabel_or_skip_methods_controls(self):
        for change in ("method", "dependency", "mutation", "scope", "extra"):
            with self.subTest(change=change):
                expectation = copy.deepcopy(self.expectations)
                if change == "method":
                    expectation["methods"].pop()
                elif change == "dependency":
                    expectation["dependency_case_pointers"].pop()
                elif change == "mutation":
                    expectation["mutations"].pop()
                elif change == "scope":
                    expectation["validation_scope"] = "runtime"
                else:
                    expectation["skipped"] = True
                self.assertTrue(list(Draft202012Validator(self.schema).iter_errors(expectation)))

    def test_execution_exception_produces_all_eight_records_and_fails_closed(self):
        executors = dict(methods.EXECUTORS)
        executors["reference"] = mock.Mock(side_effect=RuntimeError("probe failure"))
        # Other consumers still execute; use their already verified concrete results here.
        for item in self.actual_results:
            if item["method"] != "reference":
                executors[item["method"]] = mock.Mock(return_value=([], copy.deepcopy(item["evidence"]["cases"]), {}))
        with mock.patch.dict(methods.EXECUTORS, executors):
            errors, results = methods.validation_errors(self.root)
        self.assertTrue(any("probe failure" in error for error in errors))
        self.assertEqual(list(methods.METHODS), [item["method"] for item in results])
        result = next(item for item in results if item["method"] == "reference")
        self.assertFalse(result["execution_complete"])
        self.assertEqual(0, result["executed_case_count"])
        self.assertTrue(all(executors[method].called for method in methods.METHODS))

    def test_zero_execution_is_failure_even_when_consumer_returns_no_errors(self):
        executors = {method: mock.Mock(return_value=([], [], {})) for method in methods.METHODS}
        with mock.patch.dict(methods.EXECUTORS, executors):
            errors, results = methods.validation_errors(self.root)
        self.assertTrue(errors)
        self.assertTrue(all(item["status"] == "fail" and item["executed_case_count"] == 0 for item in results))

    def test_setup_failure_returns_every_method_without_claiming_execution(self):
        with mock.patch.object(methods, "load_context", side_effect=ValueError("missing registry")):
            errors, results = methods.validation_errors(self.root)
        self.assertTrue(any("missing registry" in error for error in errors))
        self.assertEqual(list(methods.METHODS), [item["method"] for item in results])
        self.assertTrue(all(not item["execution_complete"] and item["status"] == "fail"
                            and item["executed_case_count"] == 0 for item in results))

    def test_malformed_or_explicitly_skipped_records_fail_without_crashing(self):
        for malformed in (None, {}, [None]):
            with self.subTest(malformed=malformed):
                self.assertTrue(methods.method_coverage(malformed)[0])
        for field, value in (("evidence", None), ("errors", None), ("skipped", True)):
            with self.subTest(field=field):
                records = copy.deepcopy(self.actual_results)
                records[0][field] = value
                self.assertTrue(methods.method_coverage(records)[0])
        records = copy.deepcopy(self.actual_results)
        records[0]["evidence"]["cases"] = ["unexecuted"]
        self.assertTrue(methods.method_coverage(records)[0])

    def test_coverage_rejects_missing_extra_duplicate_zero_skipped_or_surviving(self):
        changes = ("missing", "extra", "duplicate", "zero", "skipped", "surviving", "count", "case_failure")
        for change in changes:
            with self.subTest(change=change):
                records = copy.deepcopy(self.actual_results)
                if change == "missing":
                    records.pop()
                elif change == "extra":
                    records.append(dict(records[0], method="runtime"))
                elif change == "duplicate":
                    records[1]["method"] = records[0]["method"]
                elif change == "zero":
                    records[0]["executed_case_count"] = 0
                elif change == "skipped":
                    records[0]["execution_complete"] = False
                elif change == "surviving":
                    records[-1]["evidence"]["cases"][0]["killed"] = False
                elif change == "count":
                    records[0]["successful_case_count"] -= 1
                else:
                    records[0]["evidence"]["cases"][0]["result"] = "fail"
                self.assertTrue(methods.method_coverage(records)[0])


if __name__ == "__main__":
    unittest.main()
