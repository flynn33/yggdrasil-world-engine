"""Independent small evidence controls; these fixtures do not claim domain conformance."""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import check_m3_acceptance as acceptance
import check_m2_acceptance as foundation
import run_validation_unit_tests as recorder
import validate_repository as runner


class M3EvidenceGateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "fixture-checkout"
        self.root.mkdir()
        self.write("tests/test_fixture.py", 'import unittest\nclass FixtureCases(unittest.TestCase):\n    def test_witness(self):\n        self.assertEqual(9, 3 * 3)\n')
        paths = [acceptance.INVARIANTS, acceptance.CATEGORIES,
                 *[path.relative_to(ROOT).as_posix() for path in (ROOT / acceptance.CANONICAL / "interfaces/contracts").glob("*.md")],
                 "data/schemas/repository_validation_report_schema.json", "data/schemas/unit_case_evidence_schema.json",
                 "data/schemas/m3_acceptance_report_schema.json", acceptance.HISTORICAL_SCHEMA,
                 acceptance.EVIDENCE_PATH, acceptance.DOCUMENT_PATH, "scripts/requirements.txt", ".gitattributes",
                 *[path.relative_to(ROOT).as_posix() for path in (ROOT / "scripts").glob("*.py")]]
        for relative in paths:
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, path)
        self.write(acceptance.EVIDENCE_PATH, {"schema_ref": acceptance.HISTORICAL_SCHEMA,
            "artifact_type": "ywe_m3_acceptance_evidence", "artifact_version": "1.0.0", "milestone_id": "M3", "outcome": "pending"})
        self.write(acceptance.DOCUMENT_PATH, "M3: PENDING\nIndependent small evidence-control fixture; no product acceptance.\n")
        self.write(acceptance.ROADMAP, {"milestones": [{"id": "M3", "status": "in_progress", "acceptance_evidence": [], "deliverables": list(acceptance.DELIVERABLES),
                                                       "exit_criteria": list(acceptance.EXIT_CRITERIA)}]})
        self.manifest = {"checks": [{"id": "validation_unit_tests", "contexts": ["always"], "blocking": True}]}
        self.write(acceptance.CHECKS, self.manifest)
        self.write("data/governance/artifact_classification_manifest.json", {"ordered_rules": [{"id": "fixture", "include": ["**"], "classification": "normative"}], "coverage": {"counts_by_class": {}}})
        self.write("data/governance/scope_partition_manifest.json", {"ordered_rules": [{"id": "fixture", "include": ["**"], "primary_partition": "ywe_core"}], "coverage": {"counts_by_partition": {}}})
        source = recorder.source_receipt(self.root, "tests/test_fixture.py", "FixtureCases", "test_witness")
        audited = {"status": acceptance.AUDITED, "candidate_tests": ["tests.test_fixture.FixtureCases.test_witness"],
                   "actual_test_source_receipts": [source]}
        self.mapping = {"required_invariants": [{**row, **copy.deepcopy(audited)} for row in acceptance.canonical_definitions(self.root)],
                        "category_sizes": {"1": 9, "2": 5, "3": 5, "4": 4, "5": 5}}
        for field, rows in acceptance.expected_obligations(self.root).items():
            self.mapping[field] = [{**row, **copy.deepcopy(audited)} for row in rows]
        self.write(recorder.MAPPING_PATH, self.mapping)
        for command in (["git", "init", "--quiet"], ["git", "config", "user.name", "Test Fixture"],
                        ["git", "config", "user.email", "fixture@example.invalid"], ["git", "add", "."],
                        ["git", "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Small evidence fixture"]):
            subprocess.run(command, cwd=self.root, check=True, capture_output=True)
        self.repository = runner.validation_report(self.root, self.manifest, "local", [], [], True)
        environment = os.environ.copy()
        environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1", GIT_ALLOW_PROTOCOL="file")
        self.report_path = Path(self.temporary.name) / "repository-report.json"
        command = [sys.executable, str(ROOT / "scripts/run_validation_unit_tests.py"), "discover", "-s", "tests", "-p", "test_*.py"]
        return_code, self.parent = runner.run_unit_evidence(command, self.root, environment, self.report_path)
        self.assertEqual(0, return_code)
        self.repository["results"] = [{"check_id": "validation_unit_tests", "blocking": True, "return_code": return_code, "unit_evidence": self.parent}]
        self.repository["summary"] = {"passed": 1, "blocking_failures": 0, "advisories": 0}
        runner.save_report(self.report_path, self.repository, self.root)
        self.conformance = json.loads(Path(self.parent["receipt_path"]).read_text())

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def report(self, repository=None, conformance=None):
        return acceptance.build_report(self.root, self.repository if repository is None else repository,
                                       self.conformance if conformance is None else conformance)

    def publish_small_fixture(self, mutate=None, extra_source=False):
        """Commit an isolated one-case evidence fixture, never product conformance."""
        actual = self.report()
        self.assertTrue(actual["ready"], actual["errors"])
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.root).decode().strip()
        files, _ = acceptance.historical.snapshot(self.root, revision)
        state = acceptance.source_state(files)
        archives = [self.report_path.read_bytes(), Path(self.parent["receipt_path"]).read_bytes(),
                    Path(self.parent["transcript_path"]).read_bytes(), (json.dumps(actual, indent=2) + "\n").encode()]
        record = {"schema_ref": acceptance.HISTORICAL_SCHEMA, "artifact_type": "ywe_m3_acceptance_evidence",
            "artifact_version": "1.0.0", "milestone_id": "M3", "outcome": "pass", "implementation_revision": revision,
            "mapping_sha256": actual["mapping_sha256"], "source_state": state,
            "artifacts": [{"path": path, "sha256": acceptance.hashlib.sha256(raw).hexdigest(), "size_bytes": len(raw)}
                          for path, raw in zip(acceptance.ARCHIVE_PATHS, archives)]}
        if mutate:
            mutate(record, archives)
        for path, raw in zip(acceptance.ARCHIVE_PATHS, archives):
            destination = self.root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(raw)
        self.write(acceptance.EVIDENCE_PATH, record)
        markers = ["M3: ACCEPTED", revision, state["digest"], actual["mapping_sha256"]]
        markers += [row["id"] for field in ("invariants", "modules", "deliverables", "criteria") for row in actual[field]]
        self.write(acceptance.DOCUMENT_PATH, "\n".join(markers) + "\n")
        paths = list(acceptance.IMMUTABLE_PATHS)
        if extra_source:
            self.write("unverified-source.txt", "Introduced without execution\n")
            paths.append("unverified-source.txt")
        subprocess.run(["git", "add", "--", *paths], cwd=self.root, check=True, capture_output=True)
        subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Independent small historical fixture"],
                       cwd=self.root, check=True, capture_output=True)
        return record

    def test_matching_actual_small_execution_passes_gate_logic_and_preserves_all_obligations(self):
        report = self.report()
        self.assertTrue(report["ready"], report["errors"])
        self.assertEqual("CONFORMANT", report["judgment"])
        self.assertEqual([28, 5, 9, 7, 5], [len(report[field]) for field in ("invariants", "categories", "modules", "deliverables", "criteria")])
        schema = json.loads((ROOT / "data/schemas/m3_acceptance_report_schema.json").read_text())
        Draft202012Validator(schema).validate(report)
        for field in ("invariants", "categories", "modules", "deliverables", "criteria"):
            changed = copy.deepcopy(report)
            changed[field].pop()
            self.assertTrue(list(Draft202012Validator(schema).iter_errors(changed)))

    def test_missing_reports_remain_nonconformant_and_preserve_every_obligation(self):
        report = acceptance.build_report(self.root)
        self.assertFalse(report["ready"])
        self.assertEqual("NON-CONFORMANT", report["judgment"])
        self.assertEqual([28, 5, 9, 7, 5], [len(report[field]) for field in ("invariants", "categories", "modules", "deliverables", "criteria")])
        self.assertTrue(all(row["status"] == "unverified" for row in report["invariants"]))

    def test_filtered_dirty_stale_revision_catalog_and_false_repository_summary_fail(self):
        mutations = [("selection", {"groups": [], "check_ids": ["validation_unit_tests"]}),
                     ("dirty_before", [" M tests/test_fixture.py"]), ("dirty_after", ["?? evidence.json"]),
                     ("revision", "0" * 40), ("check_catalog_sha256", "0" * 64),
                     ("summary", {"passed": 2, "blocking_failures": 0, "advisories": 0}),
                     ("execution_complete", False), ("offline", {"requested": False, "git_allow_protocol": None})]
        for field, value in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.repository)
                changed[field] = value
                self.assertFalse(self.report(repository=changed)["ready"])

    def test_child_completion_revision_mapping_dirty_filter_and_summary_mutations_fail(self):
        mutations = [("execution_complete", False), ("discovery_complete", False), ("revision", "0" * 40),
                     ("mapping_before_sha256", "0" * 64), ("mapping_after_sha256", "0" * 64),
                     ("dirty_before", [" M tests/test_fixture.py"]), ("dirty_after", ["?? cases.json"]),
                     ("argv", ["test_fixture"]), ("offline_git_allow_protocol", None), ("summary", None)]
        for field, value in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.conformance)
                changed[field] = value
                self.assertFalse(self.report(conformance=changed)["ready"])

    def test_mapped_skip_expected_failure_unexpected_success_missing_duplicate_and_stale_cases_fail(self):
        for status in ("NOT_RUN", "SKIP", "EXPECTED_FAILURE", "UNEXPECTED_SUCCESS", "FAIL", "ERROR"):
            with self.subTest(status=status):
                changed = copy.deepcopy(self.conformance)
                changed["cases"][0]["status"] = status
                self.assertFalse(self.report(conformance=changed)["ready"])
        for kind in ("missing", "duplicate", "stale", "start", "stop", "order", "runtime_body", "source_error"):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(self.conformance)
                if kind == "missing":
                    changed["cases"] = []
                elif kind == "duplicate":
                    changed["cases"].append(copy.deepcopy(changed["cases"][0]))
                elif kind == "runtime_body":
                    changed["cases"][0]["runtime_body_verified"] = False
                elif kind == "source_error":
                    changed["cases"][0]["source_error"] = "Actual callable unavailable"
                elif kind == "stale":
                    changed["cases"][0]["source_before"]["body_sha256"] = "0" * 64
                elif kind == "order":
                    changed["discovery_order_sha256"] = "0" * 64
                else:
                    changed["cases"][0]["starts" if kind == "start" else "stops"] = 0
                self.assertFalse(self.report(conformance=changed)["ready"])

    def test_parent_missing_incomplete_changed_receipt_or_transcript_fails(self):
        for kind in ("missing", "incomplete", "receipt", "transcript"):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(self.repository)
                branch = changed["results"][0]["unit_evidence"]
                if kind == "missing":
                    del changed["results"][0]["unit_evidence"]
                elif kind == "incomplete":
                    branch["execution_complete"] = False
                else:
                    branch[kind + "_sha256"] = "0" * 64
                self.assertFalse(self.report(repository=changed)["ready"])

    def test_malformed_parent_branch_returns_nonconformant_complete_obligation_report(self):
        for branch in (None, [], "invalid", 1):
            with self.subTest(branch=branch):
                changed = copy.deepcopy(self.repository)
                changed["results"][0]["unit_evidence"] = branch
                report = self.report(repository=changed)
                self.assertFalse(report["ready"])
                self.assertEqual("NON-CONFORMANT", report["judgment"])
                self.assertEqual([28, 5, 9, 7, 5], [len(report[key]) for key in ("invariants", "categories", "modules", "deliverables", "criteria")])

    def test_missing_or_reordered_invariants_categories_modules_and_roadmap_definitions_fail(self):
        for field in ("required_invariants", "module_contracts", "roadmap_deliverables", "roadmap_exit_criteria"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.mapping)
                changed[field].pop()
                self.assertTrue(acceptance.definition_errors(self.root, changed))
                changed = copy.deepcopy(self.mapping)
                changed[field].reverse()
                self.assertTrue(acceptance.definition_errors(self.root, changed))
        changed = copy.deepcopy(self.mapping)
        changed["category_sizes"]["4"] = 0
        self.assertTrue(acceptance.definition_errors(self.root, changed))

    def test_statement_body_selector_and_source_definition_changes_fail(self):
        for kind in ("statement", "criterion", "category", "body", "selector", "status", "module", "roadmap"):
            with self.subTest(kind=kind):
                changed = copy.deepcopy(self.mapping)
                row = changed["required_invariants"][0]
                if kind == "statement":
                    row["canonical_statement"] += " changed"
                elif kind == "criterion":
                    row["canonical_test_criterion"] += " changed"
                elif kind == "category":
                    row["category"] = 5
                elif kind == "body":
                    row["actual_test_source_receipts"][0]["body_sha256"] = "0" * 64
                elif kind == "selector":
                    row["candidate_tests"][0] = "tests.test_fixture.FixtureCases.missing"
                elif kind == "status":
                    row["status"] = "PROPOSED"
                else:
                    changed["module_contracts" if kind == "module" else "roadmap_deliverables"][0]["normalized_sha256"] = "0" * 64
                self.assertTrue(acceptance.definition_errors(self.root, changed))

    def test_definition_check_does_not_require_or_claim_execution(self):
        self.assertEqual([], acceptance.definition_errors(self.root, self.mapping))
        self.assertFalse(acceptance.build_report(self.root)["ready"])

    def test_malformed_mapping_rows_selectors_and_receipts_fail_without_losing_obligations(self):
        mutations = [("required_invariants", None), ("required_invariants", [None]),
                     ("module_contracts", "invalid"), ("roadmap_deliverables", [None]),
                     ("roadmap_exit_criteria", [None])]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                changed = copy.deepcopy(self.mapping)
                changed[field] = value
                self.assertTrue(acceptance.definition_errors(self.root, changed))
                self.write(recorder.MAPPING_PATH, changed)
                report = self.report()
                self.assertFalse(report["ready"])
                self.assertEqual([28, 5, 9, 7, 5], [len(report[key]) for key in ("invariants", "categories", "modules", "deliverables", "criteria")])
        for field, value in (("candidate_tests", [{}]), ("actual_test_source_receipts", [None]),
                             ("actual_test_source_receipts", None)):
            changed = copy.deepcopy(self.mapping)
            changed["required_invariants"][0][field] = value
            self.assertTrue(acceptance.definition_errors(self.root, changed))
            self.write(recorder.MAPPING_PATH, changed)
            self.assertFalse(self.report()["ready"])
        self.write(recorder.MAPPING_PATH, [])
        report = self.report()
        self.assertFalse(report["ready"])
        self.assertEqual([28, 5, 9, 7, 5], [len(report[key]) for key in ("invariants", "categories", "modules", "deliverables", "criteria")])

    def test_actual_core_placeholder_fails_criterion_and_exact_future_exclusion_is_visible(self):
        relative = "core/future_placeholder.json"
        self.write(relative, {"pending": True})
        classification = {"ordered_rules": [{"id": "fixture", "include": ["**"], "classification": "normative"}],
            "overrides": [{"path": relative, "classification": "placeholder", "future_milestone": "M4", "debt_ref": "fixture-debt"}],
            "coverage": {"counts_by_class": {}}}
        self.write("data/governance/artifact_classification_manifest.json", classification)
        report = self.report()
        criterion = next(row for row in report["criteria"] if row["id"] == "M3-C5")
        self.assertEqual("fail", criterion["status"])
        self.assertTrue(any("Core placeholder remains" in error for error in criterion["errors"]))
        self.write("data/governance/scope_partition_manifest.json", {
            "ordered_rules": [{"id": "fixture", "include": ["**"], "primary_partition": "ywe_core"}],
            "overrides": [{"path": relative, "primary_partition": "later_release_work", "future_milestone": "M4"}],
            "coverage": {"counts_by_partition": {}}})
        report = self.report()
        self.assertEqual([{"path": relative, "milestone": "M4", "debt_ref": "fixture-debt"}], report["excluded_future_core_placeholders"])
        self.assertFalse(report["ready"], "Changed uncommitted fixture still cannot establish clean acceptance")

    def test_source_mutation_after_execution_cannot_be_accepted(self):
        path = self.root / "tests/test_fixture.py"
        path.write_text(path.read_text() + "\n# actual later change\n")
        report = self.report()
        self.assertFalse(report["ready"])
        self.assertTrue(any("source/body" in error or "dirty" in error for error in report["errors"]))

    def test_pending_historical_record_discharges_no_completed_milestone(self):
        errors, metadata = acceptance.historical_validation_errors(self.root)
        self.assertEqual([], errors)
        self.assertEqual("pending", metadata["outcome"])
        roadmap = json.loads((self.root / acceptance.ROADMAP).read_text())
        roadmap["milestones"][0]["status"] = "complete"
        self.write(acceptance.ROADMAP, roadmap)
        self.assertTrue(acceptance.historical_validation_errors(self.root)[0])

    def test_committed_actual_small_archives_replay_without_original_external_files(self):
        self.publish_small_fixture()
        Path(self.parent["receipt_path"]).unlink()
        Path(self.parent["transcript_path"]).unlink()
        errors, metadata = acceptance.historical_validation_errors(self.root)
        self.assertEqual([], errors)
        self.assertEqual("pass", metadata["outcome"])
        self.assertEqual("accepted", metadata["status"])
        self.assertEqual(1, self.conformance["summary"]["tests_run"])

    def test_historical_introduction_cannot_change_untested_source(self):
        self.publish_small_fixture(extra_source=True)
        errors, _ = acceptance.historical_validation_errors(self.root)
        self.assertTrue(any("source digests" in error or "outside" in error for error in errors), errors)

    def test_historical_archive_changes_and_record_mutations_cannot_be_accepted(self):
        self.publish_small_fixture()
        for relative in acceptance.IMMUTABLE_PATHS:
            with self.subTest(path=relative):
                path = self.root / relative
                before = path.read_bytes()
                path.write_bytes(before + b" ")
                try:
                    self.assertTrue(acceptance.historical_validation_errors(self.root)[0])
                finally:
                    path.write_bytes(before)

    def test_historical_committed_change_then_restoration_remains_invalid(self):
        self.publish_small_fixture()
        path = self.root / acceptance.ARCHIVE_PATHS[2]
        original = path.read_bytes()
        for raw in (original + b"Unreviewed change\n", original):
            path.write_bytes(raw)
            subprocess.run(["git", "add", "--", acceptance.ARCHIVE_PATHS[2]], cwd=self.root, check=True, capture_output=True)
            subprocess.run(["git", "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "Historical mutation control"],
                           cwd=self.root, check=True, capture_output=True)
        errors, _ = acceptance.historical_validation_errors(self.root)
        self.assertTrue(any("changed or deleted" in error for error in errors), errors)

    def test_historical_forged_archive_hash_refuses_before_replay(self):
        self.publish_small_fixture(mutate=lambda record, archives: record["artifacts"][1].update(sha256="0" * 64))
        errors, _ = acceptance.historical_validation_errors(self.root)
        self.assertTrue(any("archive byte identity" in error for error in errors), errors)

    def test_archive_path_labels_allow_cross_platform_readback_but_hashes_still_bind(self):
        changed = copy.deepcopy(self.repository)
        parent = changed["results"][0]["unit_evidence"]
        parent["receipt_path"] = "C:\\external\\actual-unit.json"
        parent["transcript_path"] = "C:\\external\\actual-transcript.log"
        raw = Path(self.parent["receipt_path"]).read_bytes()
        log = Path(self.parent["transcript_path"]).read_bytes()
        report = acceptance.build_report(self.root, changed, self.conformance, archived_unit_evidence=(raw, log))
        self.assertTrue(report["ready"], report["errors"])
        parent["receipt_sha256"] = "0" * 64
        self.assertFalse(acceptance.build_report(self.root, changed, self.conformance, archived_unit_evidence=(raw, log))["ready"])

    def test_each_evidence_format_specimen_needs_its_own_successful_fixture_binding(self):
        relative = "examples/validation_evidence/format_only_examples.json"
        specimens = json.loads((ROOT / relative).read_text())
        wanted = [f"/{index}" for index in range(len(specimens))]
        self.assertEqual(wanted, foundation.fixture_units(ROOT, relative))
        catalog = json.loads((ROOT / "data/validation/fixture_catalog.json").read_text())
        bindings = [row for row in catalog["fixtures"] if row["path"] == relative]
        self.assertEqual(set(wanted), {row["instance_pointer"] for row in bindings})
        classes = {"ordered_rules": [{"id": "specimens", "include": ["**"], "classification": "example"}]}
        # Isolated coverage inputs test the selector contract, not actual fixture execution.
        results = [{"fixture_id": row["fixture_id"], "path": relative} for row in bindings]
        self.assertEqual([], foundation.fixture_coverage(ROOT, [relative], classes, catalog, results)[0])
        errors, coverage = foundation.fixture_coverage(ROOT, [relative], classes, catalog, results[:-1])
        self.assertTrue(errors)
        self.assertEqual(1, len(coverage["uncovered_units"]))
        self.write(relative, [])
        with self.assertRaises(ValueError):
            foundation.fixture_units(self.root, relative)

    def test_historical_record_format_accepts_shapes_without_granting_execution(self):
        schema = json.loads((ROOT / acceptance.HISTORICAL_SCHEMA).read_text())
        examples = json.loads((ROOT / "examples/validation_evidence/format_only_examples.json").read_text())
        self.assertEqual(13, len(examples))
        for index in (7, 8):
            Draft202012Validator(schema).validate(examples[index])
        for index in (9, 10, 11, 12):
            self.assertTrue(list(Draft202012Validator(schema).iter_errors(examples[index])))
        self.assertEqual("0" * 40, examples[8]["implementation_revision"])
        self.assertEqual("pending", acceptance.historical_validation_errors(self.root)[1]["outcome"])

    def test_planner_emitter_collections_require_each_body_and_intended_rejection_binding(self):
        catalog = json.loads((ROOT / "data/validation/fixture_catalog.json").read_text())
        classes = {"ordered_rules": [{"id": "specimens", "include": ["**"], "classification": "example"}]}
        for name, count in (("planner_emitter_cases", 39), ("planner_emitter_rejections", 72)):
            relative = "examples/core_planner_emitter/" + name + ".example.json"
            wanted = ["", *[f"/cases/{index}/value" for index in range(count)]]
            self.assertEqual(wanted, foundation.fixture_units(ROOT, relative))
            bindings = [row for row in catalog["fixtures"] if row["path"] == relative]
            self.assertEqual(set(wanted), {row["instance_pointer"] for row in bindings})
            # These coverage inputs model removal of a binding, not runtime execution.
            results = [{"fixture_id": row["fixture_id"], "path": relative} for row in bindings]
            self.assertEqual([], foundation.fixture_coverage(ROOT, [relative], classes, catalog, results)[0])
            errors, coverage = foundation.fixture_coverage(ROOT, [relative], classes, catalog, results[1:])
            self.assertTrue(errors)
            self.assertEqual([{"path": relative, "instance_pointer": "/cases/0/value"}], coverage["uncovered_units"])
            if name == "planner_emitter_rejections":
                changed = copy.deepcopy(catalog)
                first = next(row for row in changed["fixtures"] if row["path"] == relative and row["instance_pointer"])
                first.update(category="positive", expected_result="accept", expected_errors=[])
                errors, _ = foundation.fixture_coverage(ROOT, [relative], classes, changed, results)
                self.assertTrue(any("intended rejection" in error for error in errors), errors)
        self.write(relative, {"cases": []})
        with self.assertRaises(ValueError):
            foundation.fixture_units(self.root, relative)


if __name__ == "__main__":
    unittest.main()
