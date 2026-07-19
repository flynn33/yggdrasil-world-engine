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
import check_governance_contracts as governance_contracts
import check_platform_agnosticism as platform_check
import check_repository_attribution_policy as attribution_policy
import check_specification_roadmap as roadmap_check
import update_version_references as version_updater
import validate_repository as repository_runner
import yaml


class GovernanceInvariantPartitionTests(unittest.TestCase):
    def setUp(self):
        self.instructions = json.loads(
            (ROOT / "yggdrasil-instructions.json").read_text(encoding="utf-8-sig")
        )

    def test_live_partition_is_valid(self):
        self.assertEqual([], governance_contracts.instruction_invariant_errors(self.instructions))

    def test_missing_wrw_partition_is_rejected(self):
        changed = copy.deepcopy(self.instructions)
        del changed["wrw_reference_profile_invariants"]
        errors = governance_contracts.instruction_invariant_errors(changed)
        self.assertTrue(any("WRW profile invariants" in error for error in errors))

    def test_wrw_identity_in_neutral_core_is_rejected(self):
        changed = copy.deepcopy(self.instructions)
        changed["cosmological_invariants"].append("White Wolf is a universal Core identity")
        errors = governance_contracts.instruction_invariant_errors(changed)
        self.assertTrue(any("WRW identity markers" in error for error in errors))

    def test_duplicate_partition_entry_is_rejected(self):
        changed = copy.deepcopy(self.instructions)
        changed["wrw_reference_profile_invariants"].append(
            changed["cosmological_invariants"][0]
        )
        errors = governance_contracts.instruction_invariant_errors(changed)
        self.assertTrue(any("duplicate" in error for error in errors))


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

    def test_readme_status_projection_matches_machine_status(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8-sig")
        self.assertEqual([], roadmap_check.readme_status_errors(text, self.roadmap))

    def test_readme_status_projection_content_drift_is_rejected(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8-sig")
        rendered = roadmap_check.render_readme_status(self.roadmap)
        accepted_line = next(
            line
            for line in rendered.splitlines()
            if line.startswith("| Accepted milestone gates |")
        )
        drifted = text.replace(accepted_line, accepted_line.replace("gates", "gate"), 1)
        errors = roadmap_check.readme_status_errors(drifted, self.roadmap)
        self.assertTrue(any("not synchronized" in error.lower() for error in errors))

    def test_readme_status_projection_machine_drift_is_rejected(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8-sig")
        drifted_roadmap = copy.deepcopy(self.roadmap)
        drifted_roadmap["milestones"][0]["title"] += " changed"
        errors = roadmap_check.readme_status_errors(text, drifted_roadmap)
        self.assertTrue(any("not synchronized" in error.lower() for error in errors))

    def test_readme_status_projection_does_not_claim_a_percentage(self):
        rendered = roadmap_check.render_readme_status(self.roadmap)
        self.assertNotIn("%", rendered)

    def test_readme_status_projection_rejects_reversed_markers(self):
        text = (
            f"{roadmap_check.README_STATUS_END}\n"
            f"{roadmap_check.README_STATUS_START}\n"
        )
        errors = roadmap_check.readme_status_errors(text, self.roadmap)
        self.assertTrue(any("out of order" in error.lower() for error in errors))

    def test_readme_status_projection_tracks_platform_authorization(self):
        completed_roadmap = copy.deepcopy(self.roadmap)
        completed_roadmap["platform_gate"]["status"] = "authorized"
        completed_roadmap["platform_gate"]["platform_work_authorized"] = True
        rendered = roadmap_check.render_readme_status(completed_roadmap)
        self.assertIn("platform-neutral YWE specification has passed", rendered)
        self.assertIn("Platform product work | 🟢 `authorized`", rendered)
        self.assertNotIn("products remain deferred", rendered)

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
        roadmap["milestones"][0]["acceptance_evidence"] = []
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

    @staticmethod
    def _read_json(root: Path, relative_path: str) -> dict:
        return json.loads((root / relative_path).read_text(encoding="utf-8-sig"))

    @staticmethod
    def _write_json(root: Path, relative_path: str, value: dict) -> None:
        (root / relative_path).write_text(
            json.dumps(value, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def _copy_version_update_fixture(self, temporary_root: Path) -> bytes:
        roadmap = self._read_json(ROOT, version_updater.ROADMAP_PATH)
        classification = self._read_json(ROOT, version_updater.CLASSIFICATION_PATH)
        promises = self._read_json(ROOT, version_updater.PROMISE_PATH)
        paths = {
            "CHANGELOG.md",
            version_updater.ROADMAP_PATH,
            *version_updater.BASELINE_MANIFEST_PATHS,
        }
        paths.update(source["path"] for source in roadmap["version_sources"])
        paths.update(source["path"] for source in classification["sensitive_sources"])
        paths.update(surface["path"] for surface in promises["reviewed_surfaces"])

        evidence_source = ROOT / version_updater.M0_EVIDENCE_PATH
        if evidence_source.is_file():
            paths.add(version_updater.M0_EVIDENCE_PATH)

        for relative_path in sorted(paths):
            source = ROOT / relative_path
            self.assertTrue(source.is_file(), relative_path)
            destination = temporary_root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

        evidence_path = temporary_root / version_updater.M0_EVIDENCE_PATH
        if not evidence_path.exists():
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.write_bytes(b'{"immutable_test_sentinel":true}\n')

        promises = self._read_json(temporary_root, version_updater.PROMISE_PATH)
        for surface in promises["reviewed_surfaces"]:
            surface["sha256"] = version_updater.normalized_text_sha256(
                temporary_root / surface["path"]
            )
        promises["reviewed_surface_aggregate_sha256"] = (
            version_updater.reviewed_surface_digest(promises["reviewed_surfaces"])
        )
        self._write_json(temporary_root, version_updater.PROMISE_PATH, promises)

        classification = self._read_json(temporary_root, version_updater.CLASSIFICATION_PATH)
        for source in classification["sensitive_sources"]:
            source["sha256"] = version_updater.normalized_text_sha256(
                temporary_root / source["path"]
            )
        self._write_json(
            temporary_root,
            version_updater.CLASSIFICATION_PATH,
            classification,
        )
        return evidence_path.read_bytes()

    @staticmethod
    def _tree_bytes(root: Path) -> dict[str, bytes]:
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*")
            if path.is_file()
        }

    def test_version_updater_round_trip_in_temporary_tree(self):
        live_version = (ROOT / "VERSION").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            evidence_before = self._copy_version_update_fixture(temporary_root)
            old_version = (temporary_root / "VERSION").read_text(
                encoding="utf-8-sig"
            ).strip()
            major, minor, patch = (int(part) for part in old_version.split("."))
            new_version = f"{major}.{minor}.{patch + 1}"
            debt_before = self._read_json(temporary_root, version_updater.DEBT_PATH)
            introduced_before = [
                debt["introduced_baseline"] for debt in debt_before["debts"]
            ]
            classification_before = self._read_json(
                temporary_root, version_updater.CLASSIFICATION_PATH
            )
            sensitive_before = {
                source["path"]: source["sha256"]
                for source in classification_before["sensitive_sources"]
            }
            promises_before = self._read_json(
                temporary_root, version_updater.PROMISE_PATH
            )
            surfaces_before = {
                surface["path"]: surface["sha256"]
                for surface in promises_before["reviewed_surfaces"]
            }

            self.assertEqual(
                (old_version, new_version),
                version_updater.update_version_references(temporary_root, new_version),
            )

            roadmap = self._read_json(temporary_root, version_updater.ROADMAP_PATH)
            classification = self._read_json(
                temporary_root, version_updater.CLASSIFICATION_PATH
            )
            scope = self._read_json(temporary_root, version_updater.SCOPE_PATH)
            truth = self._read_json(temporary_root, version_updater.TRUTH_PATH)
            release = self._read_json(
                temporary_root, version_updater.RELEASE_POLICY_PATH
            )
            promises = self._read_json(temporary_root, version_updater.PROMISE_PATH)
            debt = self._read_json(temporary_root, version_updater.DEBT_PATH)

            self.assertEqual(new_version, roadmap["repository_baseline"])
            self.assertEqual(new_version, classification["repository_baseline"])
            self.assertEqual(new_version, scope["repository_baseline"])
            self.assertEqual(new_version, truth["repository_baseline"]["value"])
            self.assertTrue(truth["repository_baseline"]["mirrors"])
            self.assertTrue(
                all(
                    mirror["value"] == new_version
                    for mirror in truth["repository_baseline"]["mirrors"]
                )
            )
            self.assertEqual(new_version, release["repository_baseline"]["value"])
            self.assertEqual(new_version, promises["repository_baseline"])
            self.assertEqual(new_version, debt["repository_baseline"])
            self.assertEqual(
                introduced_before,
                [item["introduced_baseline"] for item in debt["debts"]],
            )
            self.assertEqual(
                evidence_before,
                (temporary_root / version_updater.M0_EVIDENCE_PATH).read_bytes(),
            )

            for source in classification["sensitive_sources"]:
                self.assertEqual(
                    version_updater.normalized_text_sha256(
                        temporary_root / source["path"]
                    ),
                    source["sha256"],
                    source["path"],
                )
            self.assertNotEqual(
                sensitive_before[version_updater.ROADMAP_PATH],
                next(
                    source["sha256"]
                    for source in classification["sensitive_sources"]
                    if source["path"] == version_updater.ROADMAP_PATH
                ),
            )

            for surface in promises["reviewed_surfaces"]:
                self.assertEqual(
                    version_updater.normalized_text_sha256(
                        temporary_root / surface["path"]
                    ),
                    surface["sha256"],
                    surface["path"],
                )
            self.assertEqual(
                version_updater.reviewed_surface_digest(promises["reviewed_surfaces"]),
                promises["reviewed_surface_aggregate_sha256"],
            )
            self.assertNotEqual(
                surfaces_before["README.md"],
                next(
                    surface["sha256"]
                    for surface in promises["reviewed_surfaces"]
                    if surface["path"] == "README.md"
                ),
            )

            changelog = temporary_root / "CHANGELOG.md"
            changelog.write_text(
                changelog.read_text(encoding="utf-8-sig").replace(
                    "---\n", f"---\n\n## [{new_version}] — 2026-07-18\n", 1
                ),
                encoding="utf-8",
            )
            self.assertEqual([], roadmap_check.version_errors(temporary_root, roadmap))

        self.assertEqual(live_version, (ROOT / "VERSION").read_bytes())

    def test_version_updater_rejects_invalid_semver_without_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            version_path = temporary_root / "VERSION"
            version_path.write_text("2.0.23\n", encoding="utf-8")
            before = self._tree_bytes(temporary_root)
            for invalid_version in (
                "9.8",
                "01.2.3",
                "1.02.3",
                "1.2.03",
                "v1.2.3",
                "1.2.3-beta",
                " 1.2.3",
            ):
                with self.subTest(version=invalid_version):
                    with self.assertRaisesRegex(ValueError, "MAJOR.MINOR.PATCH"):
                        version_updater.update_version_references(
                            temporary_root,
                            invalid_version,
                        )
                    self.assertEqual(before, self._tree_bytes(temporary_root))

    def test_version_updater_rolls_back_partial_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            temporary_root = Path(directory)
            self._copy_version_update_fixture(temporary_root)
            old_version = (temporary_root / "VERSION").read_text(
                encoding="utf-8-sig"
            ).strip()
            major, minor, patch = (int(part) for part in old_version.split("."))
            new_version = f"{major}.{minor}.{patch + 1}"
            before = self._tree_bytes(temporary_root)
            real_replace = version_updater.os.replace
            replacement_calls = 0

            def fail_second_replacement(source, destination):
                nonlocal replacement_calls
                replacement_calls += 1
                if replacement_calls == 2:
                    raise OSError("simulated replacement failure")
                return real_replace(source, destination)

            with mock.patch.object(
                version_updater.os,
                "replace",
                side_effect=fail_second_replacement,
            ):
                with self.assertRaisesRegex(OSError, "simulated replacement failure"):
                    version_updater.update_version_references(temporary_root, new_version)

            self.assertEqual(before, self._tree_bytes(temporary_root))
            self.assertGreaterEqual(replacement_calls, 3)

    def test_version_updater_supports_numeric_dotted_segments(self):
        value = {"repository_baseline": {"mirrors": [{"value": "2.0.23"}]}}
        version_updater.set_dotted_value(
            value,
            "repository_baseline.mirrors.0.value",
            "9.8.7",
        )
        self.assertEqual(
            "9.8.7",
            version_updater.dotted_value(
                value,
                "repository_baseline.mirrors.0.value",
            ),
        )

    def test_contributor_identity_gate_remains_independent(self):
        text = (ROOT / ".github/workflows/contributor-identity-policy.yml").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("scripts/github/Test-ContributorIdentityPolicy.ps1", text)


if __name__ == "__main__":
    unittest.main()
