from __future__ import annotations

import copy
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
import check_m0_truthful_baseline as m0
from test_m0_truthful_baseline import git, write_json


class ExactAssertionRevisionProofTests(unittest.TestCase):
    PATH = "data/schemas/protected_schema.json"

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Test User")
        git(self.root, "config", "user.email", "test@example.invalid")
        write_json(self.root, m0.PHASE_8_9_REQUIRED_PATH, {
            "phase_9_architecture_contracts": [], "phase_9_schemas": [self.PATH], "phase_9_validation": [],
        })
        self.source = {
            "schema_id": "legacy.v1", "required_fields": ["value"],
            "formula": "Phi = alpha1*C + alpha2*S + alpha3*P - alpha4*H",
            "example_shape": {"value": ["source.example"]},
        }
        write_json(self.root, self.PATH, self.source)
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Original descriptive source")
        self.source_revision = git(self.root, "rev-parse", "HEAD").stdout.decode().strip()
        self.original = {
            **copy.deepcopy(self.source), "$schema": fixtures.DIALECT,
            "$id": "https://ywe.local/schemas/protected_schema.json", "type": "object",
            "required": ["value"], "properties": {"value": {"type": "string", "minLength": 1}},
            "additionalProperties": True,
        }
        self.record = {
            "path": self.PATH, "legacy_value_sha256": m0.m2_contract_value_sha256(self.source),
            "migrated_value_sha256": m0.m2_contract_value_sha256(self.original),
            "added_keywords": sorted(set(self.original) - set(self.source)),
            "preserved_legacy_fields": sorted(self.source),
        }
        self.manifest = {"artifact_type": "test_original_migrations", "migrations": [copy.deepcopy(self.record)]}
        write_json(self.root, self.PATH, self.original)
        write_json(self.root, m0.M2_SCHEMA_MIGRATION_PATH, self.manifest)
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Original exact migration and proof")
        self.migration_revision = git(self.root, "rev-parse", "HEAD").stdout.decode().strip()
        self.current = copy.deepcopy(self.original)
        self.current["properties"]["value"] = {
            "type": ["string", "array"], "minLength": 1, "items": {"type": "string"},
            "x-ywe-requirement-id": "YWE-REQ-0030",
        }
        self.transition = {
            "prior_value_sha256": m0.m2_contract_value_sha256(self.original),
            "revised_value_sha256": m0.m2_contract_value_sha256(self.current),
            "requirement_id": "YWE-REQ-0030",
            "replacements": [{
                "pointer": "/properties/value", "before": copy.deepcopy(self.original["properties"]["value"]),
                "after": copy.deepcopy(self.current["properties"]["value"]),
            }],
        }
        self.group = {
            "path": self.PATH, "source_revision": self.source_revision,
            "migration_revision": self.migration_revision, "transitions": [self.transition],
        }
        self.manifest["assertion_revisions"] = [self.group]
        self.save()

    def save(self):
        write_json(self.root, self.PATH, self.current)
        write_json(self.root, m0.M2_SCHEMA_MIGRATION_PATH, self.manifest)

    def permanent_errors(self, base_ref="HEAD"):
        errors = []
        m0.validate_m2_migration_proofs(self.root, errors, self.source_revision, self.migration_revision, base_ref)
        return errors

    def assert_rejected(self):
        self.save()
        self.assertTrue(self.permanent_errors())
        errors, hits = m0.protected_diff_errors(self.root, self.migration_revision)
        self.assertTrue(errors)
        self.assertIn(self.PATH, hits)

    def test_exact_reviewed_replacement_accepts_source_and_original_migration_bases(self):
        self.assertEqual([], self.permanent_errors())
        for base in (self.source_revision, self.migration_revision):
            with self.subTest(base=base):
                self.assertEqual(([], set()), m0.protected_diff_errors(self.root, base))

    def test_reviewed_stage_is_a_valid_later_comparison_base(self):
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Reviewed representation correction")
        errors = []
        self.assertTrue(m0.approved_m2_schema_migration(self.root, "HEAD", self.PATH, self.manifest, errors))
        self.assertEqual([], errors)

    def test_unreviewed_baseline_cannot_be_used_even_if_current_stage_is_exact(self):
        changed = copy.deepcopy(self.original)
        changed["properties"]["value"]["description"] = "unreviewed assertion stage"
        write_json(self.root, self.PATH, changed)
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Unreviewed baseline")
        self.save()
        errors = []
        self.assertFalse(m0.approved_m2_schema_migration(self.root, "HEAD", self.PATH, self.manifest, errors))
        self.assertTrue(any("baseline" in error for error in errors))

    def test_unrelated_assertion_changes_fail_even_with_a_updated_result_hash(self):
        self.current["additionalProperties"] = False
        self.transition["revised_value_sha256"] = m0.m2_contract_value_sha256(self.current)
        self.assert_rejected()

    def test_changed_formula_cannot_be_hidden_by_an_updated_result_hash(self):
        self.current["formula"] = "Phi = alpha1*C + alpha2*S + alpha3*P + alpha4*H"
        self.transition["revised_value_sha256"] = m0.m2_contract_value_sha256(self.current)
        self.assert_rejected()

    def test_changed_source_example_shape_cannot_be_hidden_by_an_updated_result_hash(self):
        self.current["example_shape"]["value"] = ["changed.source"]
        self.transition["revised_value_sha256"] = m0.m2_contract_value_sha256(self.current)
        self.assert_rejected()

    def test_original_record_or_policy_changes_are_rejected(self):
        for key, value in (("legacy_value_sha256", "0" * 64), ("migrated_value_sha256", "1" * 64), ("preserved_legacy_fields", [])):
            with self.subTest(key=key):
                original = copy.deepcopy(self.manifest["migrations"][0])
                self.manifest["migrations"][0][key] = value
                self.assert_rejected()
                self.manifest["migrations"][0] = original
        self.manifest["unreviewed_policy"] = "allow legacy replacements"
        self.assert_rejected()

    def test_duplicate_paths_and_replacement_pointers_fail_closed(self):
        self.manifest["assertion_revisions"].append(copy.deepcopy(self.group))
        self.assert_rejected()
        self.manifest["assertion_revisions"].pop()
        self.transition["replacements"].append(copy.deepcopy(self.transition["replacements"][0]))
        self.assert_rejected()

    def test_nonformal_or_partial_assertion_pointers_are_rejected(self):
        for pointer in ("/formula", "/example_shape/value", "/required", "/properties/value/items"):
            with self.subTest(pointer=pointer):
                self.transition["replacements"][0]["pointer"] = pointer
                self.assert_rejected()

    def test_wrong_stage_hash_or_declared_value_is_rejected(self):
        for field in ("prior_value_sha256", "revised_value_sha256"):
            with self.subTest(field=field):
                original = self.transition[field]
                self.transition[field] = "0" * 64
                self.assert_rejected()
                self.transition[field] = original
        self.transition["replacements"][0]["after"]["type"] = "boolean"
        self.assert_rejected()

    def test_incorrect_immutable_source_or_migration_provenance_is_rejected(self):
        for field in ("source_revision", "migration_revision"):
            with self.subTest(field=field):
                original = self.group[field]
                self.group[field] = "0" * 40
                self.assert_rejected()
                self.group[field] = original

    def test_append_only_transition_chain_reconstructs_each_stage(self):
        previous = copy.deepcopy(self.current)
        self.current["properties"]["value"]["description"] = "Reviewed representation annotation"
        self.group["transitions"].append({
            "prior_value_sha256": m0.m2_contract_value_sha256(previous),
            "revised_value_sha256": m0.m2_contract_value_sha256(self.current),
            "requirement_id": "YWE-REQ-0030",
            "replacements": [{"pointer": "/properties/value", "before": previous["properties"]["value"], "after": copy.deepcopy(self.current["properties"]["value"])}],
        })
        self.save()
        self.assertEqual([], self.permanent_errors())
        self.assertEqual(([], set()), m0.protected_diff_errors(self.root, self.migration_revision))
        self.group["transitions"][1]["prior_value_sha256"] = self.record["migrated_value_sha256"]
        self.assert_rejected()

    def test_proof_removal_fails_after_merge_without_a_protected_target_diff(self):
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Reviewed correction with permanent proof")
        self.manifest.pop("assertion_revisions")
        write_json(self.root, m0.M2_SCHEMA_MIGRATION_PATH, self.manifest)
        self.assertEqual(([], set()), m0.protected_diff_errors(self.root, "HEAD"))
        self.assertTrue(self.permanent_errors())

    def test_original_proof_removal_unknown_targets_and_missing_manifest_fail_after_merge(self):
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Reviewed correction with permanent proof")
        original = copy.deepcopy(self.manifest)
        self.manifest["migrations"] = []
        self.save()
        self.assertTrue(self.permanent_errors())
        self.manifest = original
        self.manifest["assertion_revisions"].append({**copy.deepcopy(self.group), "path": "data/schemas/unregistered.json"})
        self.save()
        self.assertTrue(self.permanent_errors())
        (self.root / m0.M2_SCHEMA_MIGRATION_PATH).unlink()
        self.assertTrue(self.permanent_errors())

    def commit_second_transition(self):
        previous = copy.deepcopy(self.current)
        self.current["properties"]["value"]["description"] = "Accepted second assertion stage"
        self.group["transitions"].append({
            "prior_value_sha256": m0.m2_contract_value_sha256(previous),
            "revised_value_sha256": m0.m2_contract_value_sha256(self.current),
            "requirement_id": "YWE-REQ-0030",
            "replacements": [{"pointer": "/properties/value", "before": previous["properties"]["value"], "after": copy.deepcopy(self.current["properties"]["value"])}],
        })
        self.save()
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Accepted two-stage assertion history")

    def test_existing_chain_cannot_be_replaced_by_a_single_equivalent_transition(self):
        self.commit_second_transition()
        self.group["transitions"] = [{
            "prior_value_sha256": self.record["migrated_value_sha256"],
            "revised_value_sha256": m0.m2_contract_value_sha256(self.current),
            "requirement_id": "YWE-REQ-0030",
            "replacements": [{"pointer": "/properties/value", "before": copy.deepcopy(self.original["properties"]["value"]), "after": copy.deepcopy(self.current["properties"]["value"])}],
        }]
        self.save()
        self.assertEqual(([], set()), m0.protected_diff_errors(self.root, "HEAD"))
        self.assertTrue(any("baseline prefix" in error for error in self.permanent_errors()))

    def test_prior_stage_mutation_fails_without_a_protected_target_diff(self):
        self.commit_second_transition()
        self.group["transitions"][0]["requirement_id"] = "YWE-REQ-0001"
        self.save()
        self.assertEqual(([], set()), m0.protected_diff_errors(self.root, "HEAD"))
        self.assertTrue(any("baseline prefix" in error for error in self.permanent_errors()))

    def test_append_after_a_committed_prior_stage_is_allowed(self):
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Accepted first assertion stage")
        prior = git(self.root, "rev-parse", "HEAD").stdout.decode().strip()
        self.commit_second_transition()
        self.assertEqual([], self.permanent_errors(prior))

    def test_invalid_comparison_baseline_fails_closed(self):
        self.assertTrue(self.permanent_errors("missing-proof-baseline"))

    def test_comparison_before_manifest_existed_allows_initial_proof_addition(self):
        self.assertEqual([], self.permanent_errors(self.source_revision))


class Phase9RepresentationTests(unittest.TestCase):
    CASES = (
        ("axiom_diagnostic_packet_schema.json", "axiom_diagnostic_a1_isolation.example.json", ["evaluated_axioms", "violations", "pressures", "stabilizers", "recommended_kernel_actions"]),
        ("existence_potential_schema.json", "existence_potential_evaluation.example.json", ["coefficients", "term_values", "phi_value", "interpretation_notes"]),
        ("branch_event_schema.json", "ravenfall_gate_branch_event_reveal_oath.example.json", ["decision_context", "available_actions"]),
        ("branch_event_schema.json", "ravenfall_gate_branch_event_conceal_oath.example.json", ["decision_context", "available_actions"]),
    )

    def documents(self, name, example):
        return fixtures.load_json(ROOT / "data/schemas" / name), fixtures.load_json(ROOT / "examples/branch_reality" / example)

    def test_original_full_root_examples_are_accepted(self):
        for name, example, _ in self.CASES:
            with self.subTest(example=example):
                schema, instance = self.documents(name, example)
                Draft202012Validator.check_schema(schema)
                self.assertEqual([], list(Draft202012Validator(schema).iter_errors(instance)))

    def test_legacy_nonempty_strings_remain_accepted_and_empty_strings_reject(self):
        for name, example, fields in self.CASES:
            schema, instance = self.documents(name, example)
            validator = Draft202012Validator(schema)
            for field in fields:
                with self.subTest(schema=name, field=field):
                    changed = copy.deepcopy(instance)
                    changed[field] = "legacy.descriptive.value"
                    self.assertEqual([], list(validator.iter_errors(changed)))
                    changed[field] = ""
                    errors = list(validator.iter_errors(changed))
                    self.assertEqual(1, len(errors))
                    self.assertEqual("minLength", errors[0].validator)
                    self.assertEqual([field], list(errors[0].path))

    def test_unspecified_container_and_member_emptiness_remains_available(self):
        for name, example, fields in self.CASES:
            schema, instance = self.documents(name, example)
            validator = Draft202012Validator(schema)
            for field in fields:
                with self.subTest(schema=name, field=field):
                    changed = copy.deepcopy(instance)
                    if field == "phi_value":
                        changed[field] = -1.0
                    else:
                        changed[field] = [] if isinstance(instance[field], list) else {}
                    self.assertEqual([], list(validator.iter_errors(changed)))
                    if isinstance(instance[field], list):
                        changed[field] = [{}] if field == "violations" else [""]
                        self.assertEqual([], list(validator.iter_errors(changed)))

    def test_wrong_representation_types_are_rejected_at_the_changed_field(self):
        for name, example, fields in self.CASES:
            schema, instance = self.documents(name, example)
            for field in fields:
                with self.subTest(schema=name, field=field):
                    changed = copy.deepcopy(instance)
                    changed[field] = True if field == "phi_value" else None
                    errors = list(Draft202012Validator(schema).iter_errors(changed))
                    self.assertEqual(1, len(errors))
                    self.assertEqual("type", errors[0].validator)
                    self.assertEqual([field], list(errors[0].path))

    def test_coefficients_and_terms_are_numeric_when_supplied_without_new_ranges_or_required_members(self):
        schema, instance = self.documents("existence_potential_schema.json", "existence_potential_evaluation.example.json")
        for field, member in (("coefficients", "alpha1"), ("term_values", "C_compressibility")):
            with self.subTest(field=field):
                changed = copy.deepcopy(instance)
                changed[field] = {member: -2.5, "external_context": {"unrestricted": None}}
                self.assertEqual([], list(Draft202012Validator(schema).iter_errors(changed)))
                changed[field][member] = "numeric-looking-text"
                errors = list(Draft202012Validator(schema).iter_errors(changed))
                self.assertEqual(1, len(errors))
                self.assertEqual("type", errors[0].validator)
                self.assertEqual([field, member], list(errors[0].path))

    def test_formula_descriptive_values_and_original_migration_proofs_are_preserved(self):
        errors = []
        m0.validate_m2_migration_proofs(ROOT, errors)
        self.assertEqual([], errors)
        schema, _ = self.documents("existence_potential_schema.json", "existence_potential_evaluation.example.json")
        self.assertEqual("Phi = alpha1*C + alpha2*S + alpha3*P - alpha4*H", schema["formula"])


if __name__ == "__main__":
    unittest.main()
