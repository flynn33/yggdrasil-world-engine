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

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_m0_truthful_baseline as baseline
import check_m2_acceptance as acceptance
import validate_repository as runner


class RoadmapDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.roadmap = json.loads((ROOT / acceptance.ROADMAP).read_text(encoding="utf-8-sig"))

    def milestone(self, roadmap):
        return next(item for item in roadmap["milestones"] if item["id"] == "M2")

    def test_current_roadmap_has_an_exact_supported_mapping(self):
        self.assertEqual([], acceptance.roadmap_definition_errors(self.roadmap))
        self.assertEqual(6, len(self.milestone(self.roadmap)["exit_criteria"]))
        self.assertEqual(8, len(self.milestone(self.roadmap)["deliverables"]))

    def test_missing_or_duplicate_milestone_cannot_pass_definition(self):
        missing = copy.deepcopy(self.roadmap)
        missing["milestones"] = [item for item in missing["milestones"] if item["id"] != "M2"]
        duplicate = copy.deepcopy(self.roadmap)
        duplicate["milestones"].append(copy.deepcopy(self.milestone(duplicate)))
        for document in (missing, duplicate):
            with self.subTest(count=sum(item["id"] == "M2" for item in document["milestones"])):
                self.assertTrue(acceptance.roadmap_definition_errors(document))

    def test_added_removed_reordered_or_changed_obligations_require_a_new_mapping(self):
        for field in ("exit_criteria", "deliverables"):
            original = self.milestone(self.roadmap)[field]
            changes = (
                original + ["An additional obligation."],
                original[:-1],
                [original[1], original[0], *original[2:]],
                ["A replacement obligation.", *original[1:]],
            )
            for changed in changes:
                with self.subTest(field=field, changed=changed):
                    document = copy.deepcopy(self.roadmap)
                    self.milestone(document)[field] = changed
                    self.assertTrue(acceptance.roadmap_definition_errors(document))

    def test_definition_cli_does_not_claim_milestone_acceptance(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "check_m2_acceptance.py"), str(ROOT), "--check-definition"],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("milestone acceptance not evaluated", result.stdout)


class FixtureCoverageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.paths = []
        self.catalog = {"fixtures": []}
        self.results = []
        self.classification = json.loads(
            (ROOT / acceptance.CLASSIFICATION).read_text(encoding="utf-8-sig")
        )
        self.classification["ordered_rules"] = [
            copy.deepcopy(rule) for rule in self.classification["ordered_rules"]
            if rule["id"] in {"ACR-100", "ACR-900"}
        ]
        self.classification["ordered_rules"][1]["exclude"] = ["examples/**"]
        self.classification["overrides"] = []

    def write(self, relative, document):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        text = yaml.safe_dump(document) if path.suffix in {".yaml", ".yml"} else json.dumps(document)
        path.write_text(text + "\n", encoding="utf-8")
        if relative not in self.paths:
            self.paths.append(relative)

    def override(self, relative, classification):
        self.classification["overrides"].append({"path": relative, "classification": classification})

    def bind(self, relative, pointer="", successful=True):
        fixture_id = f"fixture.{len(self.catalog['fixtures'])}"
        self.catalog["fixtures"].append({
            "fixture_id": fixture_id,
            "path": relative,
            "instance_pointer": pointer,
            "schema_id": "https://ywe.local/schemas/record.json",
            "category": "positive",
            "expected_result": "accept",
            "expected_errors": [],
        })
        if successful:
            self.results.append({"fixture_id": fixture_id, "path": relative, "result": "accept"})

    def check(self):
        counts = {item["id"]: 0 for item in self.classification["classes"]}
        overrides = {item["path"]: item["classification"] for item in self.classification["overrides"]}
        for path in self.paths:
            classification = overrides.get(path, "example" if path.startswith("examples/") else "normative")
            counts[classification] += 1
        self.classification["coverage"]["counts_by_class"] = counts
        return acceptance.fixture_coverage(
            self.root, sorted(self.paths), self.classification, self.catalog, self.results
        )

    def test_full_root_binding_covers_json_yaml_and_yml_examples(self):
        for suffix in (".json", ".yaml", ".yml"):
            relative = "examples/record" + suffix
            self.write(relative, {"value": 1})
            self.bind(relative)
        errors, evidence = self.check()
        self.assertEqual([], errors)
        self.assertEqual(3, evidence["expected_unit_count"])
        self.assertEqual(3, evidence["successful_unit_count"])
        self.assertEqual(3, evidence["bound_path_count"])
        self.assertEqual([], evidence["uncovered_units"])

    def test_inline_schema_labels_do_not_replace_executed_bindings(self):
        for field in ("schema_id", "schema_ref", "$schema"):
            self.write(f"examples/{field.removeprefix('$')}.json", {field: "a.schema", "value": 1})
        errors, evidence = self.check()
        self.assertTrue(errors)
        self.assertEqual(3, len(evidence["uncovered_units"]))
        self.assertTrue(all(item["instance_pointer"] == "" for item in evidence["uncovered_units"]))

    def test_example_override_in_data_directory_is_included(self):
        relative = "data/realm/realm_transition_examples.yaml"
        self.write(relative, {"lawful_examples": [{"example_id": "record.1"}]})
        self.override(relative, "example")
        errors, evidence = self.check()
        self.assertTrue(errors)
        self.assertEqual([relative], evidence["structured_fixture_paths"])
        self.assertEqual([{"path": relative, "instance_pointer": ""}], evidence["uncovered_units"])
        self.bind(relative)
        self.assertEqual([], self.check()[0])

    def test_historical_override_is_excluded_from_current_fixture_coverage(self):
        relative = "examples/historical.json"
        self.write(relative, {"value": 1})
        self.override(relative, "historical")
        errors, evidence = self.check()
        self.assertEqual([], errors)
        self.assertEqual([], evidence["structured_fixture_paths"])
        self.assertEqual(0, evidence["expected_unit_count"])

    def test_nonstructured_example_is_not_a_json_schema_fixture(self):
        self.write("examples/explanation.md", {"value": "description"})
        errors, evidence = self.check()
        self.assertEqual([], errors)
        self.assertEqual([], evidence["structured_fixture_paths"])

    def test_property_binding_cannot_cover_an_entire_bare_record(self):
        relative = "examples/record.json"
        self.write(relative, {"value": 1, "unvalidated": "outside selected field"})
        self.bind(relative, "/value")
        errors, evidence = self.check()
        self.assertTrue(errors)
        self.assertEqual([{"path": relative, "instance_pointer": ""}], evidence["uncovered_units"])
        self.assertEqual(0, evidence["successful_unit_count"])

    def test_failed_fixture_entry_cannot_remove_an_uncovered_unit(self):
        relative = "examples/record.json"
        self.write(relative, {"value": "wrong type"})
        self.bind(relative, successful=False)
        errors, evidence = self.check()
        self.assertTrue(errors)
        self.assertEqual(0, evidence["successful_unit_count"])
        self.assertEqual([{"path": relative, "instance_pointer": ""}], evidence["uncovered_units"])

    def test_result_for_a_different_fixture_id_or_path_cannot_clear_coverage(self):
        relative = "examples/record.json"
        self.write(relative, {"value": 1})
        self.bind(relative, successful=False)
        for result in (
            {"fixture_id": "unknown", "path": relative, "result": "accept"},
            {"fixture_id": "fixture.0", "path": "examples/other.json", "result": "accept"},
        ):
            with self.subTest(result=result):
                self.results = [result]
                errors, evidence = self.check()
                self.assertTrue(errors)
                self.assertEqual(0, evidence["successful_unit_count"])

    def test_missing_or_multiple_classification_matches_fail(self):
        relative = "examples/record.json"
        self.write(relative, {"value": 1})
        self.bind(relative)
        original = copy.deepcopy(self.classification["ordered_rules"])
        missing = [original[1]]
        multiple = [*original, {**original[0], "id": "ACR-duplicate"}]
        for rules in (missing, multiple):
            with self.subTest(rules=rules):
                self.classification["ordered_rules"] = rules
                self.assertTrue(self.check()[0])

    def test_every_registered_bundle_requires_each_case_pointer(self):
        for relative in sorted(acceptance.BUNDLE_PATHS):
            with self.subTest(relative=relative):
                self.paths = []
                self.catalog = {"fixtures": []}
                self.results = []
                document = {"positive": {"first": {"value": 1}, "second": {"value": 2}}}
                if "legacy_example" in relative:
                    document = {
                        "description": "Structural cases.",
                        "legacy_fields": {"first": "legacy"},
                        "previews": {"second": {"value": 2}},
                    }
                    pointers = ["/legacy_fields/first", "/previews/second"]
                else:
                    pointers = ["/positive/first", "/positive/second"]
                document.update(acceptance.BUNDLE_METADATA.get(relative, {}))
                self.write(relative, document)
                for pointer in pointers:
                    self.bind(relative, pointer)
                errors, evidence = self.check()
                self.assertEqual([], errors)
                self.assertEqual(2, evidence["expected_unit_count"])
                self.assertEqual(2, evidence["successful_unit_count"])

    def test_root_only_binding_cannot_cover_a_registered_bundle(self):
        relative = "examples/contract_foundation/common_contract_cases.example.json"
        self.write(relative, {"positive": {"first": 1, "second": 2}})
        self.bind(relative)
        errors, evidence = self.check()
        self.assertTrue(errors)
        self.assertEqual(2, evidence["expected_unit_count"])
        self.assertEqual(0, evidence["successful_unit_count"])
        self.assertEqual(
            [{"path": relative, "instance_pointer": "/positive/first"},
             {"path": relative, "instance_pointer": "/positive/second"}],
            evidence["uncovered_units"],
        )

    def test_newly_added_bundle_case_cannot_hide_behind_existing_bindings(self):
        relative = "examples/contract_foundation/phase_12_representation_cases.example.json"
        self.write(relative, {"field": {"existing": "value"}})
        self.bind(relative, "/field/existing")
        self.assertEqual([], self.check()[0])
        self.write(relative, {"field": {"existing": "value", "new_case": None}})
        errors, evidence = self.check()
        self.assertTrue(errors)
        self.assertEqual(2, evidence["expected_unit_count"])
        self.assertEqual(1, evidence["successful_unit_count"])
        self.assertEqual([{"path": relative, "instance_pointer": "/field/new_case"}], evidence["uncovered_units"])

    def test_bundle_group_and_case_names_use_rfc6901_escaping(self):
        relative = "examples/contract_foundation/common_contract_cases.example.json"
        self.write(relative, {"group/part": {"case~name": 1}})
        self.bind(relative, "/group~1part/case~0name")
        self.assertEqual([], self.check()[0])

    def test_empty_or_nonmapping_bundle_layout_is_unverified(self):
        relative = "examples/contract_foundation/common_contract_cases.example.json"
        for document in ({}, [], {"positive": []}, {"positive": {}}, {"unexpected": "not a group"}):
            with self.subTest(document=document):
                self.write(relative, document)
                self.assertTrue(self.check()[0])

    def test_named_bundle_roles_cannot_be_relabelled_as_a_different_category(self):
        relative = "examples/contract_foundation/common_contract_cases.example.json"
        for group, category in (("positive", "boundary"), ("boundary", "positive"), ("reject", "positive")):
            with self.subTest(group=group, category=category):
                self.catalog = {"fixtures": []}
                self.results = []
                self.write(relative, {group: {"case": 1}})
                self.bind(relative, f"/{group}/case")
                self.catalog["fixtures"][0]["category"] = category
                self.assertTrue(self.check()[0])


class RepositoryEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.manifest = {
            "checks": [
                {"id": "syntax", "blocking": True, "contexts": ["always"]},
                {"id": "pr_guard", "blocking": True, "contexts": ["pull_request"]},
            ]
        }
        path = self.root / acceptance.CHECKS
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
        schema_path = "data/schemas/repository_validation_report_schema.json"
        (self.root / schema_path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / schema_path, self.root / schema_path)
        self.git("init", "-q")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Evidence fixture")
        self.report = runner.validation_report(self.root, self.manifest, "local", [], [], True)
        self.report["results"] = [{"check_id": "syntax", "blocking": True, "return_code": 0}]
        self.report["summary"] = {"passed": 1, "blocking_failures": 0, "advisories": 0}
        self.report["execution_complete"] = True

    def git(self, *args):
        return subprocess.run(
            [baseline.git_executable(), "-C", str(self.root), *args],
            check=True, capture_output=True,
        )

    def errors(self, report=None):
        return acceptance.repository_evidence_errors(
            self.root, self.report if report is None else report, self.manifest
        )

    def test_entire_passing_offline_report_from_clean_current_revision_is_valid(self):
        self.assertEqual([], self.errors())

    def test_missing_execution_report_cannot_establish_acceptance(self):
        self.assertTrue(acceptance.repository_evidence_errors(self.root, None, self.manifest))

    def test_only_local_full_suite_context_establishes_checkout_acceptance(self):
        self.assertEqual([], self.errors())
        for context in ("pull_request", "push", "manual"):
            with self.subTest(context=context):
                changed = copy.deepcopy(self.report)
                changed["context"] = context
                if context == "pull_request":
                    changed["results"].append({"check_id": "pr_guard", "blocking": True, "return_code": 0})
                    changed["summary"]["passed"] = 2
                errors = self.errors(changed)
                self.assertTrue(any("local full-suite context" in error for error in errors), errors)

    def test_partial_duplicate_unknown_or_reordered_check_results_are_rejected(self):
        self.manifest["checks"][1]["contexts"] = ["local"]
        (self.root / acceptance.CHECKS).write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Local check catalog")
        self.report = runner.validation_report(self.root, self.manifest, "local", [], [], True)
        first = {"check_id": "syntax", "blocking": True, "return_code": 0}
        second = {"check_id": "pr_guard", "blocking": True, "return_code": 0}
        self.report.update({"execution_complete": True, "results": [first, second],
                            "summary": {"passed": 2, "blocking_failures": 0, "advisories": 0}})
        self.assertEqual([], self.errors())
        for results in ([], [first], [first, first], [second, first],
                        [first, second, {**first, "check_id": "unknown"}]):
            with self.subTest(results=results):
                changed = copy.deepcopy(self.report)
                changed["results"] = results
                changed["summary"]["passed"] = len(results)
                errors = self.errors(changed)
                self.assertTrue(errors)
                if results:
                    self.assertTrue(any("every applicable check" in error for error in errors), errors)

    def test_filtered_selection_does_not_establish_full_acceptance(self):
        for selection in ({"groups": ["schema"], "check_ids": []},
                          {"groups": [], "check_ids": ["syntax"]}):
            with self.subTest(selection=selection):
                self.report["selection"] = selection
                self.assertTrue(self.errors())

    def test_stale_revision_or_catalog_digest_is_rejected(self):
        for field, value in (("revision", "0" * 40), ("check_catalog_sha256", "0" * 64)):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.report)
                changed[field] = value
                self.assertTrue(self.errors(changed))

    def test_recorded_dirty_state_before_or_after_execution_is_rejected(self):
        for field in ("dirty_before", "dirty_after"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.report)
                changed[field] = ["?? untracked.json"]
                self.assertTrue(self.errors(changed))

    def test_current_dirty_checkout_cannot_use_an_earlier_clean_report(self):
        (self.root / "untracked.txt").write_text("new work\n", encoding="utf-8")
        self.assertTrue(self.errors())

    def test_remote_git_protocols_must_have_been_denied(self):
        for offline in ({"requested": False, "git_allow_protocol": None},
                        {"requested": True, "git_allow_protocol": "https"}):
            with self.subTest(offline=offline):
                self.report["offline"] = offline
                self.assertTrue(self.errors())

    def test_failed_check_or_inconsistent_summary_is_rejected(self):
        failed = copy.deepcopy(self.report)
        failed["results"][0]["return_code"] = 1
        failed["summary"] = {"passed": 0, "blocking_failures": 1, "advisories": 0}
        inconsistent = copy.deepcopy(self.report)
        inconsistent["summary"]["passed"] = 2
        for document in (failed, inconsistent):
            with self.subTest(report=document):
                self.assertTrue(self.errors(document))

    def test_report_cannot_downgrade_registered_check_severity(self):
        self.report["results"][0]["blocking"] = False
        self.assertTrue(self.errors())

    def test_required_tool_versions_cannot_be_omitted(self):
        for name in ("python", "jsonschema", "PyYAML", "referencing"):
            with self.subTest(name=name):
                changed = copy.deepcopy(self.report)
                del changed["tool_versions"][name]
                self.assertTrue(self.errors(changed))

    def test_invalid_report_shape_is_rejected_before_semantic_evaluation(self):
        for document in ({}, {**self.report, "artifact_type": "another_report"},
                         {**self.report, "results": "PASS"}):
            with self.subTest(document=document):
                self.assertTrue(self.errors(document))

    def test_saving_report_inside_checkout_records_the_created_file_as_dirty(self):
        path = self.root / "evidence.json"
        runner.save_report(path, self.report, self.root)
        saved = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(saved["dirty_after"])
        self.assertTrue(self.errors(saved))

    def test_saving_report_outside_checkout_preserves_clean_evidence(self):
        with tempfile.TemporaryDirectory() as destination:
            path = Path(destination) / "evidence.json"
            runner.save_report(path, self.report, self.root)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(saved["execution_complete"])
            self.assertEqual([], saved["dirty_after"])
            self.assertEqual([], self.errors(saved))

    def test_passing_results_without_final_checkout_capture_remain_incomplete(self):
        report = runner.validation_report(self.root, self.manifest, "local", [], [], True)
        report["results"] = self.report["results"]
        report["summary"] = self.report["summary"]
        self.assertFalse(report["execution_complete"])
        self.assertTrue(self.errors(report))

    def test_failed_final_git_capture_persists_incomplete_report_and_gate_rejects_it(self):
        with tempfile.TemporaryDirectory() as destination:
            path = Path(destination) / "evidence.json"
            failure = subprocess.CalledProcessError(1, ["git", "status"])
            with mock.patch.object(runner, "git_state", side_effect=failure):
                with self.assertRaises(subprocess.CalledProcessError):
                    runner.save_report(path, self.report, self.root)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(saved["execution_complete"])
            self.assertTrue(self.errors(saved))

    def test_changed_revision_during_final_capture_persists_incomplete_report(self):
        with tempfile.TemporaryDirectory() as destination:
            path = Path(destination) / "evidence.json"
            with mock.patch.object(runner, "git_state", return_value=("0" * 40, [])):
                with self.assertRaisesRegex(ValueError, "revision changed"):
                    runner.save_report(path, self.report, self.root)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertFalse(saved["execution_complete"])
            self.assertTrue(self.errors(saved))


class ReadinessReportTests(unittest.TestCase):
    def test_live_report_keeps_all_roadmap_obligations_and_requires_execution_evidence(self):
        roadmap = json.loads((ROOT / acceptance.ROADMAP).read_text(encoding="utf-8-sig"))
        milestone = next(item for item in roadmap["milestones"] if item["id"] == "M2")
        report = acceptance.build_report(ROOT)
        self.assertEqual(milestone["exit_criteria"], [item["statement"] for item in report["criteria"]], report)
        self.assertEqual(milestone["deliverables"], [item["statement"] for item in report["deliverables"]], report)
        self.assertEqual([f"M2-C{index}" for index in range(1, 7)], [item["id"] for item in report["criteria"]])
        self.assertEqual([f"M2-D{index}" for index in range(1, 9)], [item["id"] for item in report["deliverables"]])
        self.assertEqual("unverified", report["criteria"][-1]["status"])
        self.assertEqual("unverified", report["deliverables"][-1]["status"])
        self.assertFalse(report["ready"])

    def test_default_cli_fails_readiness_without_executed_acceptance_evidence(self):
        with tempfile.TemporaryDirectory() as destination:
            output = Path(destination) / "readiness.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "check_m2_acceptance.py"), str(ROOT), "--output", str(output)],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(1, result.returncode, result.stdout + result.stderr)
            self.assertIn("M2 readiness: not ready", result.stdout)
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(report["ready"])
            self.assertEqual(6, len(report["criteria"]), report)
            self.assertEqual(8, len(report["deliverables"]), report)


class RunnerReportCliTests(unittest.TestCase):
    def setUp(self):
        self.fixture = RepositoryEvidenceTests(methodName="test_entire_passing_offline_report_from_clean_current_revision_is_valid")
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.manifest = self.fixture.manifest
        self.output_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.output_directory.cleanup)
        self.output = Path(self.output_directory.name) / "report.json"
        check = self.manifest["checks"][0]
        check.update({
            "name": "Offline environment witness",
            "groups": ["schema"],
            "command": ["{python}", "-c", "import os, sys; sys.exit(0 if os.environ.get('GIT_ALLOW_PROTOCOL') == 'file' else 7)"],
        })
        path = self.root / acceptance.ROADMAP
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"current_milestone": "M2"}) + "\n", encoding="utf-8")
        self.save_manifest()

    def save_manifest(self):
        path = self.root / acceptance.CHECKS
        path.write_text(json.dumps(self.manifest, indent=2) + "\n", encoding="utf-8")
        self.fixture.git("add", ".")
        self.fixture.git("-c", "commit.gpgsign=false", "commit", "-q", "-m", "Runner fixture")

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_repository.py"), "--root", str(self.root),
             "--context", "local", "--report", str(self.output), *args],
            check=False, capture_output=True, text=True,
        )

    def saved_report(self):
        return json.loads(self.output.read_text(encoding="utf-8"))

    def test_offline_cli_records_actual_results_clean_state_and_tool_versions(self):
        result = self.run_cli("--offline")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report = self.saved_report()
        self.assertTrue(report["execution_complete"])
        self.assertEqual({"requested": True, "git_allow_protocol": "file"}, report["offline"])
        self.assertEqual([{"check_id": "syntax", "blocking": True, "return_code": 0}], report["results"])
        self.assertEqual({"passed": 1, "blocking_failures": 0, "advisories": 0}, report["summary"])
        self.assertEqual([], report["dirty_before"])
        self.assertEqual([], report["dirty_after"])
        self.assertEqual([], acceptance.repository_evidence_errors(self.root, report, self.manifest))

    def test_blocking_failure_is_recorded_and_returns_failure(self):
        self.manifest["checks"][0]["command"] = ["{python}", "-c", "raise SystemExit(9)"]
        self.save_manifest()
        result = self.run_cli("--offline")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        report = self.saved_report()
        self.assertEqual(9, report["results"][0]["return_code"])
        self.assertEqual({"passed": 0, "blocking_failures": 1, "advisories": 0}, report["summary"])
        self.assertTrue(acceptance.repository_evidence_errors(self.root, report, self.manifest))

    def test_advisory_failure_does_not_become_m2_acceptance_when_runner_returns_zero(self):
        self.manifest["checks"][0].update({"blocking": False, "command": ["{python}", "-c", "raise SystemExit(3)"]})
        self.save_manifest()
        result = self.run_cli("--offline")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report = self.saved_report()
        self.assertEqual(3, report["results"][0]["return_code"])
        self.assertEqual({"passed": 0, "blocking_failures": 0, "advisories": 1}, report["summary"])
        self.assertTrue(acceptance.repository_evidence_errors(self.root, report, self.manifest))

    def test_filtered_passing_cli_records_selection_and_cannot_prove_full_acceptance(self):
        result = self.run_cli("--offline", "--check", "syntax")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report = self.saved_report()
        self.assertEqual({"groups": [], "check_ids": ["syntax"]}, report["selection"])
        self.assertTrue(acceptance.repository_evidence_errors(self.root, report, self.manifest))

    def test_cli_without_offline_flag_does_not_claim_retrieval_was_denied(self):
        self.manifest["checks"][0]["command"] = ["{python}", "-c", "raise SystemExit(0)"]
        self.save_manifest()
        result = self.run_cli()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        report = self.saved_report()
        self.assertEqual({"requested": False, "git_allow_protocol": None}, report["offline"])
        self.assertTrue(acceptance.repository_evidence_errors(self.root, report, self.manifest))

    def test_listing_checks_does_not_manufacture_execution_report(self):
        result = self.run_cli("--offline", "--list")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertIn("syntax:", result.stdout)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
