from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_machine_readable_artifacts as machine_artifacts
import check_platform_agnosticism as platform_check
import check_repository_attribution_policy as attribution_policy
import check_specification_roadmap as roadmap_check
import update_version_references as version_updater
import validate_repository as repository_runner
import yaml


class RoadmapValidationTests(unittest.TestCase):
    def setUp(self):
        self.roadmap = json.loads(
            (ROOT / "data/governance/specification_roadmap.json").read_text(encoding="utf-8-sig")
        )

    def test_dependency_graph_is_acyclic(self):
        self.assertEqual([], roadmap_check.dependency_errors(self.roadmap["milestones"]))

    def test_dependency_cycle_is_rejected(self):
        milestones = copy.deepcopy(self.roadmap["milestones"])
        milestones[0]["dependencies"] = ["M10"]
        errors = roadmap_check.dependency_errors(milestones)
        self.assertTrue(any("cycle" in error.lower() for error in errors))

    def test_runner_context_selection(self):
        check = {"contexts": ["pull_request"]}
        self.assertTrue(repository_runner.check_applies(check, "pull_request"))
        self.assertFalse(repository_runner.check_applies(check, "local"))

    def test_roadmap_document_matches_machine_status(self):
        text = (ROOT / "docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md").read_text(
            encoding="utf-8-sig"
        )
        self.assertEqual([], roadmap_check.document_errors(text, self.roadmap["milestones"]))

    def test_roadmap_document_status_drift_is_rejected(self):
        text = (ROOT / "docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md").read_text(
            encoding="utf-8-sig"
        )
        drifted = text.replace("Status: `in_progress`", "Status: `planned`", 1)
        errors = roadmap_check.document_errors(drifted, self.roadmap["milestones"])
        self.assertTrue(any("status" in error.lower() for error in errors))

    def test_roadmap_document_scope_drift_is_rejected(self):
        text = (ROOT / "docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md").read_text(
            encoding="utf-8-sig"
        )
        drifted = text.replace("- Keep the platform implementation gate closed through M10.\n", "", 1)
        errors = roadmap_check.document_errors(drifted, self.roadmap["milestones"])
        self.assertTrue(any("deliverables" in error.lower() for error in errors))

    def test_subsystem_matrix_and_evidence_are_valid(self):
        text = (ROOT / "docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md").read_text(
            encoding="utf-8-sig"
        )
        self.assertEqual([], roadmap_check.subsystem_errors(ROOT, self.roadmap, text))

    def test_release_ready_subsystem_requires_complete_prerequisites(self):
        roadmap = copy.deepcopy(self.roadmap)
        roadmap["subsystems"][0]["maturity"]["release_ready"] = "complete"
        errors = roadmap_check.subsystem_errors(ROOT, roadmap)
        self.assertTrue(any("prerequisite" in error.lower() for error in errors))

    def test_completed_milestone_requires_acceptance_evidence(self):
        roadmap = copy.deepcopy(self.roadmap)
        roadmap["milestones"][0]["status"] = "complete"
        errors = roadmap_check.milestone_completion_errors(ROOT, roadmap["milestones"])
        self.assertTrue(any("acceptance evidence" in error.lower() for error in errors))


class MachineArtifactTests(unittest.TestCase):
    def test_quality_debt_classifies_missing_identifier_and_annotations(self):
        documents = {
            "valid.json": {"$schema": "x", "$id": "y", "type": "object"},
            "missing.json": {"$schema": "x", "type": "object"},
            "annotation.json": {"$schema": "x", "$id": "z", "description": "record"},
        }
        debt = machine_artifacts.quality_debt(documents)
        self.assertEqual(["missing.json"], debt["declared_schema_missing_id"])
        self.assertEqual(["annotation.json"], debt["annotation_only_schema_documents"])

    def test_local_json_pointer_resolution(self):
        document = {"$defs": {"record": {"type": "object"}}}
        self.assertTrue(machine_artifacts.resolve_json_pointer(document, "#/$defs/record"))
        self.assertFalse(machine_artifacts.resolve_json_pointer(document, "#/$defs/missing"))

    def test_duplicate_yaml_key_is_rejected(self):
        with self.assertRaises(yaml.YAMLError):
            yaml.load("record:\n  value: one\n  value: two\n", Loader=machine_artifacts.UniqueKeyLoader)

    def test_schema_named_and_unbound_example_debt_is_classified(self):
        documents = {
            "data/schemas/legacy_schema.json": {"type": "object"},
            "examples/unbound.example.json": {"value": 1},
            "examples/bound.example.json": {"schema_ref": "example", "value": 1},
        }
        debt = machine_artifacts.quality_debt({}, documents)
        self.assertEqual(
            ["data/schemas/legacy_schema.json"],
            debt["schema_named_json_without_schema_declaration"],
        )
        self.assertEqual(["examples/unbound.example.json"], debt["unbound_json_examples"])


class AttributionPolicyTests(unittest.TestCase):
    def test_every_policy_rule_matches_its_runtime_value(self):
        active_rules = attribution_policy.rules()
        self.assertGreaterEqual(len(active_rules), 10)
        for rule in active_rules:
            self.assertEqual(rule.rule_id, attribution_policy.scan_value(rule.value, [rule]))

    def test_token_boundaries_allow_near_matches(self):
        token_rule = next(rule for rule in attribution_policy.rules() if rule.token_boundary)
        self.assertIsNone(attribution_policy.scan_value(f"prefix{token_rule.value}suffix", [token_rule]))

    def test_untracked_text_is_scanned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            marker = next(rule.value for rule in attribution_policy.rules() if rule.text_scope)
            (root / "untracked.md").write_text(f"{marker}\n", encoding="utf-8")
            errors = []
            attribution_policy.scan_repository_text(root, attribution_policy.rules(), errors)
            self.assertTrue(errors)

    def test_push_event_commit_range_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True
            )
            path = root / "record.txt"
            path.write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "record.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-q", "-m", "Base"], cwd=root, check=True)
            before = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            pushed = []
            for index in range(2):
                path.write_text(f"change {index}\n", encoding="utf-8")
                subprocess.run(["git", "add", "record.txt"], cwd=root, check=True)
                subprocess.run(["git", "commit", "-q", "-m", f"Change {index}"], cwd=root, check=True)
                pushed.append(
                    subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
                )
            after = pushed[-1]
            subprocess.run(
                ["git", "update-ref", "refs/remotes/origin/main", after], cwd=root, check=True
            )
            event_path = root / "event.json"
            event_path.write_text(json.dumps({"before": before, "after": after}), encoding="utf-8")
            with mock.patch.dict(os.environ, {"GITHUB_EVENT_PATH": str(event_path)}):
                refs = attribution_policy.commit_refs(root)
            self.assertEqual(set(pushed), set(refs))


class PlatformBoundaryTests(unittest.TestCase):
    def test_marker_free_platform_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "Game.cs").write_text("public class PlatformGame {}\n", encoding="utf-8")
            violations, _ = platform_check.platform_violations(root)
            self.assertTrue(any("Game.cs" in violation for violation in violations))

    def test_validation_tool_source_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "scripts" / "check_example.py"
            path.parent.mkdir(parents=True)
            path.write_text("value = 1\n", encoding="utf-8")
            violations, _ = platform_check.platform_violations(root)
            self.assertEqual([], violations)

    def test_product_source_outside_approved_paths_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "product" / "runtime.py"
            path.parent.mkdir(parents=True)
            path.write_text("value = 1\n", encoding="utf-8")
            violations, _ = platform_check.platform_violations(root)
            self.assertTrue(any("runtime.py" in violation for violation in violations))

    def test_platform_project_artifact_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "world.uproject").write_text("{}\n", encoding="utf-8")
            violations, _ = platform_check.platform_violations(root)
            self.assertTrue(any("world.uproject" in violation for violation in violations))


class WorkflowContractTests(unittest.TestCase):
    def setUp(self):
        self.check_manifest = json.loads(
            (ROOT / "data/validation/repository_checks.json").read_text(encoding="utf-8-sig")
        )

    def test_required_check_contracts_are_exact(self):
        self.assertEqual([], roadmap_check.catalog_contract_errors(self.check_manifest))

    def test_required_check_contract_mutations_are_rejected(self):
        mutations = []

        removed = copy.deepcopy(self.check_manifest)
        removed["checks"] = removed["checks"][:-1]
        mutations.append(removed)

        changed_command = copy.deepcopy(self.check_manifest)
        changed_command["checks"][0]["command"] = ["{python}", "scripts/validate_architecture.py", "{root}"]
        mutations.append(changed_command)

        nonblocking = copy.deepcopy(self.check_manifest)
        nonblocking["checks"][0]["blocking"] = False
        mutations.append(nonblocking)

        narrowed_context = copy.deepcopy(self.check_manifest)
        narrowed_context["checks"][0]["contexts"] = ["manual"]
        mutations.append(narrowed_context)

        for mutation in mutations:
            with self.subTest():
                self.assertTrue(roadmap_check.catalog_contract_errors(mutation))

    def test_validation_workflows_use_the_catalog_runner(self):
        for relative_path in (
            ".github/workflows/main-ci.yml",
            ".github/workflows/ywe_repository_guardrails.yml",
            ".github/workflows/forsetti-compliance.yml",
            ".github/workflows/branch-guard.yml",
        ):
            text = (ROOT / relative_path).read_text(encoding="utf-8-sig")
            self.assertIn("validate_repository.py", text, relative_path)

    def test_version_workflow_does_not_publish_or_tag(self):
        text = (ROOT / ".github/workflows/versioning.yml").read_text(encoding="utf-8-sig")
        self.assertNotIn("pull_request:", text)
        self.assertNotIn("git tag", text)
        self.assertNotIn("git push origin main", text)
        self.assertIn("gh pr create", text)
        self.assertLess(text.index("Validate baseline update"), text.index("Commit baseline update branch"))
        self.assertEqual([], roadmap_check.publication_workflow_errors(ROOT, True))

    def test_pre_m10_publication_command_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow = root / ".github" / "workflows" / "publish.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text("steps:\n  - run: gh release create v1.0.0\n", encoding="utf-8")
            self.assertTrue(roadmap_check.publication_workflow_errors(root, True))

    def test_version_updater_round_trip_in_temporary_tree(self):
        roadmap = json.loads(
            (ROOT / "data/governance/specification_roadmap.json").read_text(encoding="utf-8-sig")
        )
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            paths = {"CHANGELOG.md", "data/governance/specification_roadmap.json"}
            paths.update(source["path"] for source in roadmap["version_sources"])
            for relative_path in paths:
                source = ROOT / relative_path
                destination = temporary_root / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            version_updater.update_version_references(temporary_root, "9.8.7")
            changelog = temporary_root / "CHANGELOG.md"
            changelog.write_text(
                changelog.read_text(encoding="utf-8-sig").replace(
                    "---\n", "---\n\n## [9.8.7] — 2026-07-18\n", 1
                ),
                encoding="utf-8",
            )
            updated = json.loads(
                (temporary_root / "data/governance/specification_roadmap.json").read_text(
                    encoding="utf-8-sig"
                )
            )
            self.assertEqual([], roadmap_check.version_errors(temporary_root, updated))

    def test_contributor_identity_gate_remains_independent(self):
        text = (ROOT / ".github/workflows/contributor-identity-policy.yml").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("scripts/github/Test-ContributorIdentityPolicy.ps1", text)


if __name__ == "__main__":
    unittest.main()
