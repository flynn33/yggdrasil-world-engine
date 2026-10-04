from __future__ import annotations

import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_fixture_catalog as fixtures
import check_m2_validation_operations as operations


class ValidationOperationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="ywe-m2-operation-tests-")
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name) / "checkout"
        subprocess.run(
            ["git", "clone", "--quiet", "--shared", "--no-hardlinks", str(ROOT), str(cls.root)],
            check=True, capture_output=True,
        )
        errors = []
        for relative in operations.baseline.repository_candidate_paths(ROOT, errors):
            source = ROOT / relative
            if not source.is_file():
                raise AssertionError(f"Missing candidate source for operation tests: {relative}")
            target = cls.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        if errors:
            raise AssertionError(errors)
        cls.registry, errors = fixtures.load_registry(cls.root)
        if errors:
            raise AssertionError(errors)
        cls.schema = fixtures.load_json(cls.root / operations.CASE_SCHEMA)
        cls.original_bundle = fixtures.load_json(cls.root / operations.BUNDLE)
        cls.original_expectations = fixtures.load_json(cls.root / operations.EXPECTATIONS)
        cls.catalog = fixtures.load_json(cls.root / fixtures.FIXTURE_CATALOG)
        cls.locations = operations.rejection.schema_constraint_locations(cls.root, cls.registry)

    def setUp(self):
        self.bundle = copy.deepcopy(self.original_bundle)
        self.expectations = copy.deepcopy(self.original_expectations)

    def evaluate(self):
        return operations.evaluate_cases(self.root, self.schema, self.bundle, self.expectations, self.registry, self.catalog)

    def recovery(self):
        return self.bundle["recovery"]["retry_delay"]

    def replay(self, rejected=False):
        return self.bundle["replay"]["rejected_retry" if rejected else "accepted_retry"]

    def migration(self):
        return self.bundle["migration"]["protected_schema"]

    def run_recovery(self):
        return operations.execute_recovery(self.root, self.registry, self.catalog, self.recovery(), self.locations)

    def replace_file(self, relative, value):
        path = self.root / relative
        previous = path.read_bytes()
        self.addCleanup(path.write_bytes, previous)
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def source_binding(self, identifier):
        binding = next(item for item in self.catalog["fixtures"] if item["fixture_id"] == identifier)
        subject = fixtures.json_pointer(fixtures.load_instance(self.root / binding["path"]), binding["instance_pointer"])
        return {"fixture_id": identifier, "fixture_binding": {key: copy.deepcopy(binding[key]) for key in operations.BINDING_FIELDS},
                "instance_sha256": operations.value_hash(subject)}

    def operation_bindings(self, results):
        catalog = {"fixtures": []}
        fixture_results = []
        for item in results:
            identifier = item["operation_id"] + ".case"
            catalog["fixtures"].append({
                "fixture_id": identifier, "path": operations.BUNDLE,
                "instance_pointer": item["instance_pointer"], "schema_id": operations.CASE_SCHEMA_ID,
                "category": item["category"], "expected_result": "accept", "expected_errors": [],
            })
            fixture_results.append({"fixture_id": identifier, "path": operations.BUNDLE, "result": "accept"})
        return catalog, fixture_results

    def test_schema_and_all_four_actual_operations_pass(self):
        Draft202012Validator.check_schema(self.schema)
        self.assertEqual("YWE-REQ-0033", self.schema["x-ywe-requirement-id"])
        errors, results = self.evaluate()
        self.assertEqual([], errors)
        self.assertEqual(4, len(results))
        self.assertEqual({"recovery", "replay", "migration"}, {item["category"] for item in results})
        self.assertTrue(all(item["validation_scope"] == "schema_validation_operation" for item in results))
        self.assertEqual(["accept", "reject", "accept"], [item["result"] for item in results[0]["stages"]])

    def test_replay_executes_registered_descriptor_semantics_on_both_loads(self):
        case = self.replay(rejected=True)
        case.update(self.source_binding("yaml_descriptor.reject.pattern_unknown_enum_reference"))
        stages = operations.execute_replay(self.root, self.registry, self.catalog, case)
        self.assertEqual(["reject", "reject"], [item["result"] for item in stages])
        self.assertEqual(stages[0]["errors"], stages[1]["errors"])
        self.assertEqual("YAML_DESCRIPTOR_ENUM_REFERENCE", stages[0]["errors"][0]["error_id"])

    def test_actual_catalog_acceptance_and_operation_execution_intersect(self):
        errors, fixtures_results = fixtures.validation_errors(self.root)
        self.assertEqual([], errors)
        errors, results = self.evaluate()
        self.assertEqual([], errors)
        errors, evidence = operations.category_coverage(self.catalog, fixtures_results, results)
        self.assertEqual([], errors)
        self.assertEqual(2, len(evidence["executed_operations_by_category"]["replay"]))

    def test_category_metadata_alone_cannot_satisfy_lifecycle_coverage(self):
        catalog = {"fixtures": [dict(item, category=category) for category, item in zip(
            operations.CATEGORIES, self.catalog["fixtures"][:3]
        )]}
        fixture_results = [{"fixture_id": item["fixture_id"], "path": item["path"], "result": "accept"}
                           for item in catalog["fixtures"]]
        errors, _ = operations.category_coverage(catalog, fixture_results, [])
        self.assertEqual(3, len(errors))

    def test_operation_requires_successful_exact_pointer_schema_and_category_binding(self):
        _, results = self.evaluate()
        original, successful = self.operation_bindings(results)
        for field, value in (("instance_pointer", ""), ("schema_id", "https://ywe.local/schemas/common/retry.schema.json"),
                             ("category", "positive"), ("path", "examples/unrelated.json"), ("expected_result", "reject")):
            with self.subTest(field=field):
                catalog = copy.deepcopy(original)
                catalog["fixtures"][0][field] = value
                self.assertTrue(operations.category_coverage(catalog, successful, results)[0])
        self.assertTrue(operations.category_coverage(original, successful[1:], results)[0])
        failed = copy.deepcopy(successful)
        failed[0]["result"] = "reject"
        self.assertTrue(operations.category_coverage(original, failed, results)[0])

    def test_failed_or_duplicate_operation_results_cannot_clear_categories(self):
        _, results = self.evaluate()
        catalog, successful = self.operation_bindings(results)
        for field, value in (("result", "fail"), ("validation_scope", "runtime_replay"), ("category", "replay")):
            changed = copy.deepcopy(results)
            changed[0][field] = value
            self.assertTrue(operations.category_coverage(catalog, successful, changed)[0])
        self.assertTrue(operations.category_coverage(catalog, successful, results + results[:1])[0])

    def test_expectations_require_every_case_exactly_once(self):
        for action in ("missing", "extra", "duplicate"):
            self.expectations = copy.deepcopy(self.original_expectations)
            if action == "missing":
                self.expectations["cases"].pop()
            else:
                extra = copy.deepcopy(self.expectations["cases"][0])
                if action == "extra":
                    extra["instance_pointer"] = "/recovery/unknown"
                self.expectations["cases"].append(extra)
            errors, results = self.evaluate()
            self.assertTrue(errors)
            self.assertEqual([], results)

    def test_missing_group_wrong_scope_and_unregistered_fields_fail_the_case_format(self):
        for action in ("missing_group", "empty_group", "wrong_scope", "extra_field", "wrong_category"):
            self.bundle = copy.deepcopy(self.original_bundle)
            if action == "missing_group":
                del self.bundle["migration"]
            elif action == "empty_group":
                self.bundle["migration"] = {}
            elif action == "wrong_scope":
                self.recovery()["validation_scope"] = "runtime_recovery"
            elif action == "extra_field":
                self.replay()["replay_count"] = 1
            else:
                self.recovery()["category"] = "replay"
            errors, results = self.evaluate()
            self.assertTrue(errors)
            self.assertEqual([], results)

    def test_duplicate_operation_ids_fail_before_execution(self):
        self.replay()["operation_id"] = self.recovery()["operation_id"]
        errors, results = self.evaluate()
        self.assertTrue(errors)
        self.assertEqual([], results)

    def test_duplicate_recovery_owner_bindings_fail_the_case_format(self):
        self.recovery()["owner_bindings"].append(copy.deepcopy(self.recovery()["owner_bindings"][0]))
        errors, results = self.evaluate()
        self.assertTrue(errors)
        self.assertEqual([], results)

    def test_changed_expectation_identity_or_stage_witness_fails(self):
        self.expectations["cases"][0]["operation_id"] = "unrelated.operation"
        errors, results = self.evaluate()
        self.assertTrue(errors)
        self.assertFalse(any(item["category"] == "recovery" for item in results))
        self.expectations = copy.deepcopy(self.original_expectations)
        self.expectations["cases"][0]["expected_stages"][1]["errors"][0]["schema_pointer"] = "/unrelated/minimum"
        self.assertTrue(self.evaluate()[0])

    def test_recovery_rejects_negative_positive_control(self):
        self.recovery().update(self.source_binding("m2.common.retry_negative_delay.reject"))
        with self.assertRaisesRegex(ValueError, "accepted positive control"):
            self.run_recovery()

    def test_unknown_duplicate_or_changed_fixture_binding_fails(self):
        for action in ("unknown", "duplicate", "changed"):
            case = copy.deepcopy(self.recovery())
            catalog = copy.deepcopy(self.catalog)
            if action == "unknown":
                case["fixture_id"] = "unknown"
            elif action == "duplicate":
                catalog["fixtures"].append(copy.deepcopy(next(item for item in catalog["fixtures"] if item["fixture_id"] == case["fixture_id"])))
            else:
                case["fixture_binding"]["instance_pointer"] = "/positive/idempotency"
            with self.assertRaises(ValueError):
                operations.select_fixture(self.root, catalog, case)

    def test_changed_json_value_hash_fails_even_if_schema_would_accept(self):
        self.recovery()["instance_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "JSON value hash"):
            self.run_recovery()

    def test_valid_but_different_restore_value_is_rejected(self):
        self.recovery()["replacement"]["restored_value"] = 3
        with self.assertRaisesRegex(ValueError, "exact original"):
            self.run_recovery()

    def test_restore_preserves_exact_json_numeric_representation(self):
        self.recovery()["replacement"]["restored_value"] = 2
        with self.assertRaisesRegex(ValueError, "exact original"):
            self.run_recovery()

    def test_unchanged_or_valid_proposal_does_not_establish_recovery(self):
        for value in (2.0, 3):
            self.recovery()["replacement"]["invalid_value"] = value
            with self.assertRaises(ValueError):
                self.run_recovery()

    def test_recovery_requires_complete_intended_witness_not_an_unrelated_type_failure(self):
        self.recovery()["replacement"]["invalid_value"] = "invalid"
        with self.assertRaisesRegex(ValueError, "complete rejection"):
            self.run_recovery()

    def test_missing_or_extra_recovery_witness_is_rejected(self):
        for errors in ([], self.recovery()["expected_errors"] + [{
            "error_id": "JSON_SCHEMA_TYPE", "instance_pointer": "/retry_after", "schema_pointer": "/properties/retry_after/type",
        }]):
            self.recovery()["expected_errors"] = errors
            with self.assertRaisesRegex(ValueError, "complete rejection"):
                self.run_recovery()

    def test_same_minimum_elsewhere_cannot_replace_the_executed_assertion_owner(self):
        self.recovery()["owner_bindings"][0]["pointer"] = "/properties/attempt/minimum"
        with self.assertRaisesRegex(ValueError, "owning assertion"):
            self.run_recovery()

    def test_recovery_cannot_add_a_missing_member(self):
        self.recovery()["replacement"]["pointer"] = "/missing"
        with self.assertRaises(ValueError):
            self.run_recovery()

    def test_recovery_leaves_original_source_bytes_unchanged(self):
        path = self.root / self.recovery()["fixture_binding"]["path"]
        original = path.read_bytes()
        self.run_recovery()
        self.assertEqual(original, path.read_bytes())

    def test_replay_independently_loads_and_validates_both_accepted_and_rejected_inputs(self):
        for rejected in (False, True):
            with mock.patch.object(fixtures, "load_instance", wraps=fixtures.load_instance) as loader:
                with mock.patch.object(fixtures, "instance_witnesses", wraps=fixtures.instance_witnesses) as validator:
                    results = operations.execute_replay(self.root, self.registry, self.catalog, self.replay(rejected))
                    self.assertEqual(2, loader.call_count)
                    self.assertEqual(2, validator.call_count)
                    self.assertEqual(["reject" if rejected else "accept"] * 2, [item["result"] for item in results])

    def test_replay_rejects_a_changed_second_input(self):
        load = fixtures.load_instance
        count = 0
        def changed(path):
            nonlocal count
            result = load(path)
            count += 1
            if count == 2:
                result["positive"]["retry"]["retry_after"] = 3
            return result
        with mock.patch.object(fixtures, "load_instance", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "JSON value hash"):
                operations.execute_replay(self.root, self.registry, self.catalog, self.replay())

    def test_replay_rejects_a_changed_second_witness(self):
        witness = fixtures.signature_key(self.replay(True)["fixture_binding"]["expected_errors"][0])
        with mock.patch.object(fixtures, "instance_witnesses", side_effect=[{witness}, set()]):
            with self.assertRaisesRegex(ValueError, "recorded witnesses"):
                operations.execute_replay(self.root, self.registry, self.catalog, self.replay(True))

    def test_replay_detects_validator_input_mutation(self):
        def mutated(root, registry, schema_id, subject):
            subject["retry_after"] = 3
            return set()
        with mock.patch.object(fixtures, "instance_witnesses", side_effect=mutated):
            with self.assertRaisesRegex(ValueError, "altered its input"):
                operations.execute_replay(self.root, self.registry, self.catalog, self.replay())

    def test_runtime_provenance_cannot_replace_immutable_migration_revisions(self):
        self.migration()["source_revision"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "immutable original provenance"):
            operations.execute_migration(self.root, self.migration())

    def test_migration_requires_exact_record_history_and_current_stage_hashes(self):
        for key in ("record_sha256", "assertion_revision_sha256", "current_stage_sha256"):
            case = copy.deepcopy(self.migration())
            case[key] = "0" * 64
            with self.assertRaises(ValueError):
                operations.execute_migration(self.root, case)

    def test_migration_cannot_bind_another_protected_record_as_the_selected_stage(self):
        self.migration()["record_pointer"] = "/migrations/1"
        with self.assertRaisesRegex(ValueError, "same protected target"):
            operations.execute_migration(self.root, self.migration())

    def test_migration_executes_the_permanent_proof_verifier(self):
        verifier = operations.baseline.validate_m2_migration_proofs
        with mock.patch.object(operations.baseline, "validate_m2_migration_proofs", wraps=verifier) as checked:
            operations.execute_migration(self.root, self.migration())
            self.assertEqual(1, checked.call_count)
        def failed(root, errors):
            errors.append("missing permanent proof")
        with mock.patch.object(operations.baseline, "validate_m2_migration_proofs", side_effect=failed):
            with self.assertRaisesRegex(ValueError, "missing permanent proof"):
                operations.execute_migration(self.root, self.migration())

    def test_refreshed_hash_cannot_hide_an_original_manifest_record_edit(self):
        path = operations.baseline.M2_SCHEMA_MIGRATION_PATH
        manifest = fixtures.load_json(self.root / path)
        manifest["migrations"][0]["added_keywords"].append("unreviewed")
        self.replace_file(path, manifest)
        self.migration()["record_sha256"] = operations.value_hash(manifest["migrations"][0])
        with self.assertRaisesRegex(ValueError, "immutable historical proof"):
            operations.execute_migration(self.root, self.migration())

    def test_refreshed_hash_cannot_hide_a_changed_reconstruction_before_value(self):
        path = operations.baseline.M2_SCHEMA_MIGRATION_PATH
        manifest = fixtures.load_json(self.root / path)
        manifest["assertion_revisions"][0]["transitions"][0]["replacements"][0]["before"]["type"] = "integer"
        self.replace_file(path, manifest)
        self.migration()["assertion_revision_sha256"] = operations.value_hash(manifest["assertion_revisions"][0])
        with self.assertRaisesRegex(ValueError, "reconstruction failed"):
            operations.execute_migration(self.root, self.migration())

    def test_removed_assertion_proof_cannot_establish_migration(self):
        path = operations.baseline.M2_SCHEMA_MIGRATION_PATH
        manifest = fixtures.load_json(self.root / path)
        del manifest["assertion_revisions"]
        self.replace_file(path, manifest)
        with self.assertRaises(ValueError):
            operations.execute_migration(self.root, self.migration())

    def test_any_source_write_during_execution_invalidates_all_success_results(self):
        relative = self.recovery()["fixture_binding"]["path"]
        content = (self.root / relative).read_bytes()
        self.addCleanup((self.root / relative).write_bytes, content)
        actual = operations.rejection.schema_witnesses
        first = True
        def write_source(registry, schema_id, subject):
            nonlocal first
            if first:
                first = False
                (self.root / relative).write_bytes(content + b"\n")
            return actual(registry, schema_id, subject)
        with mock.patch.object(operations.rejection, "schema_witnesses", side_effect=write_source):
            errors, results = self.evaluate()
        self.assertTrue(any("changed a source input" in error for error in errors), errors)
        self.assertEqual([], results)

    def test_a_stale_resolved_schema_cannot_establish_operation_execution(self):
        relative = "data/schemas/common/retry.schema.json"
        schema = fixtures.load_json(self.root / relative)
        schema["properties"]["retry_after"]["minimum"] = -2
        self.replace_file(relative, schema)
        errors, results = self.evaluate()
        self.assertTrue(any("current source resource" in error for error in errors), errors)
        self.assertEqual([], results)


if __name__ == "__main__":
    unittest.main()
