from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import check_m0_truthful_baseline as m0
import check_non_destructive_diff as diff_check


def write_text(root: Path, relative_path: str, text: str) -> Path:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_json(root: Path, relative_path: str, value: object) -> Path:
    return write_text(root, relative_path, json.dumps(value, indent=2) + "\n")


def git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [m0.git_executable(), "-C", str(root), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def roadmap_fixture() -> dict:
    return {
        "repository_baseline": "2.0.23",
        "publication": {
            "state": "unreleased",
            "published_releases": 0,
            "github_release_objects": 0,
            "agnostic_specification_releases": 0,
        },
        "platform_gate": {
            "status": "deferred",
            "platform_work_authorized": False,
        },
        "current_milestone": "M0",
        "milestones": [
            {"id": "M0", "status": "in_progress", "acceptance_evidence": []},
            {"id": "M1", "status": "planned", "acceptance_evidence": []},
            *[
                {"id": f"M{number}", "status": "planned", "acceptance_evidence": []}
                for number in range(2, 11)
            ],
        ],
        "subsystems": [],
        "version_sources": [
            {"path": "VERSION", "kind": "plain"},
            {"path": "version.txt", "kind": "plain"},
        ],
    }


def non_destructive_policy(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "max_deleted_files": 10,
        "max_modified_files_without_review": 10,
        "max_renamed_files": 10,
        "protected_paths": ["docs/"],
        "fail_on_deleted_protected_paths": False,
    }
    value.update(overrides)
    return value


def passing_check_result(check_id: str, command: list[str] | None = None) -> dict:
    summary = f"PASS: {check_id} completed with exit code 0."
    return {
        "check_id": check_id,
        "command": command or ["{python}", f"scripts/{check_id}.py", "{root}"],
        "exit_code": 0,
        "outcome": "pass",
        "result_summary": summary,
        "result_summary_hash_algorithm": "sha256_utf8_lf_normalized",
        "result_summary_sha256": m0.sha256_bytes(m0.normalized_utf8_data(summary.encode("utf-8"))),
    }


def acceptance_document_fixture(evidence: dict) -> str:
    baseline = evidence["baseline"]
    lines = [
        "# M0 Truthful Baseline Acceptance",
        "",
        "## Baseline",
        "",
        f"- Base ref: `{baseline['base_ref']}`",
        f"- Base SHA: `{baseline['base_sha']}`",
        f"- Working branch: `{baseline['branch']}`",
        f"- Repository baseline version: `{baseline['repository_version']}`",
        "",
        "## Authority and Phase Alignment",
        "",
        "| Control | Result | Evidence |",
        "|---|---:|---|",
        "| Protected Phase 9 paths changed | NO | Pull-request diff |",
        "",
        "## M0 Deliverables",
        "",
        "| Deliverable | Status | Evidence |",
        "|---|---:|---|",
        "| Truthful baseline | PASS | JSON evidence |",
        "",
        "## M0 Exit Criteria",
        "",
        "| Exit criterion | Status | Evidence |",
        "|---|---:|---|",
    ]
    for criterion in evidence["exit_criteria"]:
        lines.append(f"| {criterion['id']} | PASS | JSON evidence |")
    lines.extend(["", "## Coverage Counts", "", "```text"])
    for label, value in m0.acceptance_metric_pairs(evidence):
        lines.append(f"{label}: {value}")
    lines.extend(["```", "", "## Gate Results", "", "| Gate | Result | Evidence |", "|---|---:|---|"])
    for gate in evidence["foundation_gates"]:
        lines.append(f"| {gate['id']} Foundation gate | PASS | JSON evidence |")
    lines.extend(["", "## Validation Results", ""])
    for run in evidence["validation_runs"]:
        lines.extend(
            [
                f"### {run['context']} context",
                "",
                "| Check | Result |",
                "|---|---:|",
            ]
        )
        for result in run["results"]:
            lines.append(f"| `{result['check_id']}` | PASS |")
        lines.append("")
    lines.extend(
        [
            "## Diff Review",
            "",
            "- Protected Phase 9 path diff: empty.",
            "",
            "## Acceptance Judgment",
            "",
            "```text",
            *m0.ACCEPTANCE_JUDGMENT_LINES,
            "```",
            "",
            "## Deferred Work",
            "",
            "All M1-M10 work remains governed by the roadmap and unauthorized until M10 acceptance.",
            "",
        ]
    )
    return "\n".join(lines)


def class_manifest(paths: list[str], classification: str = "informative") -> dict:
    counts = {name: 0 for name in sorted(m0.MATURITY_CLASSES)}
    counts[classification] = len(paths)
    return {
        "repository_baseline": "2.0.23",
        "tracked_path_snapshot": {
            "path_count": len(paths),
            "path_digest": m0.nul_digest(paths),
        },
        "classes": [{"id": name} for name in sorted(m0.MATURITY_CLASSES)],
        "ordered_rules": [
            {
                "id": "ACR-001",
                "priority": 10,
                "include": ["**"],
                "exclude": [],
                "classification": classification,
                "owner_role": "Test maintainers",
                "governing_source": paths[0],
                "rationale": "Test classification assignment.",
            }
        ],
        "overrides": [],
        "sensitive_sources": [],
        "coverage": {"counts_by_class": counts},
    }


def scope_manifest(paths: list[str], partition: str = "governance_validation") -> dict:
    counts = {name: 0 for name in sorted(m0.SCOPE_PARTITIONS)}
    counts[partition] = len(paths)
    return {
        "repository_baseline": "2.0.23",
        "tracked_path_snapshot": {
            "path_count": len(paths),
            "path_digest": m0.nul_digest(paths),
        },
        "partitions": [{"id": name} for name in sorted(m0.SCOPE_PARTITIONS)],
        "ordered_rules": [
            {
                "id": "SPR-001",
                "priority": 10,
                "include": ["**"],
                "exclude": [],
                "primary_partition": partition,
                "owner_role": "Test maintainers",
                "governing_source": paths[0],
                "rationale": "Test scope assignment.",
            }
        ],
        "overrides": [],
        "coverage": {"counts_by_partition": counts},
    }


class JsonAndPathTests(unittest.TestCase):
    def test_duplicate_json_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate.json"
            path.write_text('{"value": 1, "value": 2}\n', encoding="utf-8")
            with self.assertRaises(m0.DuplicateKeyError):
                m0.load_json(path)

    def test_absolute_drive_and_traversal_paths_are_rejected(self):
        for value in ("/absolute", "C:/outside", "../outside", "safe/../outside", "bad\\path"):
            with self.subTest(value=value):
                self.assertFalse(m0.is_safe_repository_path(value))

    def test_posix_repository_path_is_accepted(self):
        self.assertTrue(m0.is_safe_repository_path("data/governance/record.json"))

    def test_normalized_hash_is_line_ending_portable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.txt"
            second = root / "second.txt"
            first.write_bytes(b"one\r\ntwo\r\n")
            second.write_bytes(b"one\ntwo\n")
            self.assertEqual(m0.normalized_text_sha256(first), m0.normalized_text_sha256(second))

    def test_invalid_utf8_is_rejected_by_normalized_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.txt"
            path.write_bytes(b"\xff")
            with self.assertRaises(UnicodeDecodeError):
                m0.normalized_text_sha256(path)


class GlobAndClassificationTests(unittest.TestCase):
    def test_recursive_glob_matches_root_and_nested_files(self):
        pattern = m0.glob_to_regex("**/*.md")
        self.assertIsNotNone(pattern.fullmatch("README.md"))
        self.assertIsNotNone(pattern.fullmatch("docs/project/status.md"))
        self.assertIsNone(pattern.fullmatch("docs/project/status.json"))

    def test_unclassified_path_is_rejected(self):
        manifest = class_manifest(["known.md"])
        manifest["ordered_rules"][0]["include"] = ["known.md"]
        errors: list[str] = []
        assignments = m0.effective_assignments(
            ["known.md", "new.bin"], manifest, "classification", errors, "classification"
        )
        self.assertIn("known.md", assignments)
        self.assertTrue(any("no assignment" in error for error in errors))

    def test_different_priority_overlap_is_rejected(self):
        manifest = class_manifest(["docs/status.md"])
        second = copy.deepcopy(manifest["ordered_rules"][0])
        second["id"] = "ACR-002"
        second["priority"] = 100
        second["include"] = ["docs/**"]
        manifest["ordered_rules"].append(second)
        errors: list[str] = []
        assignments = m0.effective_assignments(
            ["docs/status.md"], manifest, "classification", errors, "classification"
        )
        self.assertEqual({}, assignments)
        self.assertTrue(any("multiply classifies" in error for error in errors))

    def test_duplicate_override_is_rejected(self):
        manifest = class_manifest(["README.md"])
        override = {
            "path": "README.md",
            "classification": "informative",
            "owner_role": "Test maintainers",
            "governing_source": "README.md",
            "rationale": "Explicit test override.",
        }
        manifest["overrides"] = [override, copy.deepcopy(override)]
        errors: list[str] = []
        m0.effective_assignments(
            ["README.md"], manifest, "classification", errors, "classification"
        )
        self.assertTrue(any("duplicate overrides" in error for error in errors))

    def test_invalid_glob_is_rejected(self):
        with self.assertRaises(ValueError):
            m0.glob_to_regex("../**")

    def test_declared_placeholder_must_have_placeholder_classification(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path_name = "notes.md"
            write_text(root, path_name, "# Notes\nStatus: placeholder awaiting finalized content\n")
            paths = [path_name]
            classification = class_manifest(paths, "informative")
            scope = scope_manifest(paths)
            errors: list[str] = []
            m0.validate_classification_scope(root, paths, classification, scope, "2.0.23", errors)
            self.assertTrue(any("not classified as placeholder" in error for error in errors))

    def test_placeholder_requires_later_release_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path_name = "notes.md"
            write_text(root, path_name, "Status: placeholder awaiting finalized content\n")
            classification = class_manifest([path_name], "placeholder")
            classification["ordered_rules"][0].update(
                {"future_milestone": "M1", "debt_ref": "QD-PH-12345678"}
            )
            scope = scope_manifest([path_name], "governance_validation")
            errors: list[str] = []
            m0.validate_classification_scope(
                root, [path_name], classification, scope, "2.0.23", errors
            )
            self.assertTrue(any("not routed to later_release_work" in error for error in errors))

    def test_superseded_artifact_without_replacement_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path_name = "historical-authority.md"
            write_text(root, path_name, "# Historical authority\n")
            classification = class_manifest([path_name], "superseded")
            scope = scope_manifest([path_name], "historical_evidence")
            errors: list[str] = []
            m0.validate_classification_scope(
                root, [path_name], classification, scope, "2.0.23", errors
            )
            self.assertTrue(any("missing superseded_by" in error for error in errors))

    def test_normative_later_release_scope_without_exception_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path_name = "deferred-contract.json"
            write_text(root, path_name, "{}\n")
            classification = class_manifest([path_name], "normative")
            scope = scope_manifest([path_name], "later_release_work")
            scope["ordered_rules"][0].update(
                {"future_milestone": "M9", "debt_ref": "QD-OW-014"}
            )
            errors: list[str] = []
            m0.validate_classification_scope(
                root, [path_name], classification, scope, "2.0.23", errors
            )
            self.assertTrue(any("without an explicit exception" in error for error in errors))

    def test_normative_later_release_scope_with_exception_is_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path_name = "deferred-contract.json"
            write_text(root, path_name, "{}\n")
            classification = class_manifest([path_name], "normative")
            scope = scope_manifest([path_name], "later_release_work")
            scope["ordered_rules"][0].update(
                {
                    "future_milestone": "M9",
                    "debt_ref": "QD-OW-014",
                    "normative_scope_exception": {
                        "rationale": "The contract is current while implementation remains deferred.",
                        "authority_ref": path_name,
                    },
                }
            )
            errors: list[str] = []
            m0.validate_classification_scope(
                root, [path_name], classification, scope, "2.0.23", errors
            )
            self.assertEqual([], errors)

    def test_stale_coverage_count_is_rejected(self):
        manifest = class_manifest(["README.md"])
        manifest["coverage"]["counts_by_class"]["informative"] = 2
        errors: list[str] = []
        m0.effective_assignments(
            ["README.md"], manifest, "classification", errors, "classification"
        )
        self.assertTrue(any("coverage counts are stale" in error for error in errors))


class PromiseTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        write_text(self.root, "README.md", "# Features\n## Infinite Quest Generation\n")
        self.roadmap = roadmap_fixture()
        self.entry = {
            "path": "README.md",
            "sha256": m0.normalized_text_sha256(self.root / "README.md"),
        }
        self.promise = {
            "repository_baseline": "2.0.23",
            "publication_state": "unreleased",
            "reviewed_surfaces": [self.entry],
            "reviewed_surface_aggregate_sha256": m0.reviewed_surface_digest([self.entry]),
            "promises": [
                {
                    "promise_id": "PRM-001",
                    "claim_type": "content_generation",
                    "disposition": "milestone_assigned",
                    "milestones": ["M5"],
                    "source_refs": [
                        {
                            "path": "README.md",
                            "locator_type": "markdown_heading",
                            "locator": "Features > Infinite Quest Generation",
                        }
                    ],
                }
            ],
            "summary": {
                "reviewed_surface_count": 1,
                "promise_count": 1,
                "assigned_count": 1,
                "excluded_count": 0,
                "unresolved_count": 0,
            },
        }

    def tearDown(self):
        self.directory.cleanup()

    def validate(self, value: dict) -> list[str]:
        errors: list[str] = []
        m0.validate_promises(
            self.root,
            ["README.md"],
            value,
            self.roadmap,
            "2.0.23",
            {},
            {},
            errors,
        )
        return errors

    def test_valid_promise_register_semantics(self):
        self.assertEqual([], self.validate(copy.deepcopy(self.promise)))

    def test_review_hash_drift_is_rejected(self):
        changed = copy.deepcopy(self.promise)
        changed["reviewed_surfaces"][0]["sha256"] = "0" * 64
        self.assertTrue(any("hash is stale" in error for error in self.validate(changed)))

    def test_missing_reviewed_public_surface_is_rejected(self):
        changed = copy.deepcopy(self.promise)
        changed["reviewed_surfaces"] = []
        changed["reviewed_surface_aggregate_sha256"] = m0.reviewed_surface_digest([])
        self.assertTrue(any("unreviewed public surfaces" in error for error in self.validate(changed)))

    def test_unknown_promise_milestone_is_rejected(self):
        changed = copy.deepcopy(self.promise)
        changed["promises"][0]["milestones"] = ["M99"]
        self.assertTrue(any("unknown milestones" in error for error in self.validate(changed)))

    def test_assigned_promise_without_milestone_is_rejected(self):
        changed = copy.deepcopy(self.promise)
        changed["promises"][0]["milestones"] = []
        self.assertTrue(any("no milestone assignment" in error for error in self.validate(changed)))

    def test_excluded_promise_requires_rationale_and_authority(self):
        changed = copy.deepcopy(self.promise)
        changed["promises"][0]["disposition"] = "formally_excluded"
        changed["promises"][0]["milestones"] = []
        self.assertTrue(any("lacks exclusion" in error for error in self.validate(changed)))

    def test_unresolved_promise_disposition_is_rejected(self):
        changed = copy.deepcopy(self.promise)
        changed["promises"][0]["disposition"] = "unresolved"
        self.assertTrue(
            any("unresolved or invalid disposition" in error for error in self.validate(changed))
        )

    def test_active_publication_claim_before_m10_is_rejected(self):
        changed = copy.deepcopy(self.promise)
        changed["promises"][0]["claim_type"] = "publication"
        changed["promises"][0]["milestones"] = ["M0"]
        self.assertTrue(
            any("active publication claim" in error for error in self.validate(changed))
        )

    def test_duplicate_promise_id_is_rejected(self):
        changed = copy.deepcopy(self.promise)
        changed["promises"].append(copy.deepcopy(changed["promises"][0]))
        self.assertTrue(any("IDs are duplicated" in error for error in self.validate(changed)))


class DebtTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        write_text(self.root, "VERSION", "2.0.23\n")
        write_text(self.root, "placeholder.md", "Status: placeholder awaiting finalized content\n")
        self.roadmap = roadmap_fixture()
        self.roadmap["subsystems"] = [
            {"id": "test_system", "open_work": ["Complete the test contract."]}
        ]
        write_json(self.root, m0.ROADMAP_PATH, self.roadmap)
        schema_debt = {"known_debt": {"missing_id": ["legacy.json"]}}
        write_json(self.root, m0.SCHEMA_DEBT_PATH, schema_debt)
        self.class_assignments = {
            "placeholder.md": {
                "classification": "placeholder",
                "debt_ref": "QD-PH-12345678",
            }
        }
        self.scope_assignments = {
            "placeholder.md": {
                "primary_partition": "later_release_work",
                "debt_ref": "QD-PH-12345678",
            }
        }
        self.records = [
            {
                "debt_id": "QD-PH-12345678",
                "status": "open",
                "owner_role": "Test maintainers",
                "assigned_milestone": "M1",
                "source_refs": [
                    {"kind": "repository_path", "path": "placeholder.md"}
                ],
                "resolution_evidence": [],
            },
            {
                "debt_id": "QD-OW-001",
                "status": "open",
                "owner_role": "Test maintainers",
                "assigned_milestone": "M1",
                "source_refs": [
                    {
                        "kind": "json_pointer",
                        "path": m0.ROADMAP_PATH,
                        "locator": "/subsystems/0/open_work/0",
                    }
                ],
                "resolution_evidence": [],
            },
        ]
        self.debt = self.build_debt()

    def tearDown(self):
        self.directory.cleanup()

    def build_debt(self) -> dict:
        schema_document = m0.load_json(self.root / m0.SCHEMA_DEBT_PATH)
        category_counts = {
            key: len(value) for key, value in schema_document["known_debt"].items()
        }
        placeholders = ["placeholder.md"]
        open_work = m0.roadmap_open_work(self.roadmap)
        statuses = {"open": 2, "resolved": 0, "accepted_exception": 0}
        return {
            "repository_baseline": "2.0.23",
            "schema_debt_subledger": {
                "sha256": m0.normalized_text_sha256(self.root / m0.SCHEMA_DEBT_PATH),
                "counts_by_category": category_counts,
                "category_occurrence_count": 1,
                "unique_path_count": 1,
            },
            "debts": copy.deepcopy(self.records),
            "summary": {
                "total": 2,
                **statuses,
                "by_milestone": {"M1": 2},
                "placeholder_count": 1,
                "roadmap_open_work_count": 1,
                "placeholder_paths_sha256": m0.nul_digest(placeholders),
                "roadmap_open_work_sha256": m0.nul_digest(
                    f"{subsystem}:{text}" for subsystem, text, _pointer in open_work
                ),
            },
        }

    def validate(self, value: dict) -> list[str]:
        errors: list[str] = []
        m0.validate_debt(
            self.root,
            value,
            self.roadmap,
            "2.0.23",
            self.class_assignments,
            self.scope_assignments,
            errors,
        )
        return errors

    def test_valid_debt_coverage(self):
        self.assertEqual([], self.validate(copy.deepcopy(self.debt)))

    def test_unregistered_placeholder_debt_is_rejected(self):
        changed = copy.deepcopy(self.debt)
        changed["debts"] = changed["debts"][1:]
        self.assertTrue(any("unregistered debt" in error for error in self.validate(changed)))

    def test_unregistered_open_work_is_rejected(self):
        changed = copy.deepcopy(self.debt)
        changed["debts"][1]["source_refs"] = []
        self.assertTrue(any("open-work items lack debt" in error for error in self.validate(changed)))

    def test_resolved_debt_without_evidence_is_rejected(self):
        changed = copy.deepcopy(self.debt)
        changed["debts"][0]["status"] = "resolved"
        self.assertTrue(any("lacks resolution evidence" in error for error in self.validate(changed)))

    def test_pretransition_allows_pending_acceptance_evidence_generation(self):
        missing_evidence = "data/governance/pending-m0-test-evidence.json"
        changed = copy.deepcopy(self.debt)
        changed["debts"][1]["status"] = "resolved"
        changed["debts"][1]["resolution_evidence"] = [missing_evidence]
        with mock.patch.object(m0, "M0_EVIDENCE_REFS", [missing_evidence]):
            errors = self.validate(changed)
        self.assertFalse(any("evidence does not exist" in error for error in errors))

    def test_completed_m0_rejects_missing_acceptance_evidence(self):
        missing_evidence = "data/governance/pending-m0-test-evidence.json"
        changed = copy.deepcopy(self.debt)
        changed["debts"][1]["status"] = "resolved"
        changed["debts"][1]["resolution_evidence"] = [missing_evidence]
        completed_roadmap = copy.deepcopy(self.roadmap)
        completed_roadmap["milestones"][0]["status"] = "complete"
        errors: list[str] = []
        with mock.patch.object(m0, "M0_EVIDENCE_REFS", [missing_evidence]):
            m0.validate_debt(
                self.root,
                changed,
                completed_roadmap,
                "2.0.23",
                self.class_assignments,
                self.scope_assignments,
                errors,
            )
        self.assertTrue(any("evidence does not exist" in error for error in errors))

    def test_open_debt_without_owner_or_milestone_is_rejected(self):
        for missing_field, expected_error in (
            ("owner_role", "missing owner_role"),
            ("assigned_milestone", "missing assigned_milestone"),
        ):
            with self.subTest(missing_field=missing_field):
                changed = copy.deepcopy(self.debt)
                del changed["debts"][0][missing_field]
                self.assertTrue(
                    any(expected_error in error for error in self.validate(changed))
                )

    def test_schema_subledger_hash_drift_is_rejected(self):
        changed = copy.deepcopy(self.debt)
        changed["schema_debt_subledger"]["sha256"] = "0" * 64
        self.assertTrue(any("sub-ledger hash is stale" in error for error in self.validate(changed)))

    def test_summary_drift_is_rejected(self):
        changed = copy.deepcopy(self.debt)
        changed["summary"]["placeholder_count"] = 99
        self.assertTrue(any("summary is stale" in error for error in self.validate(changed)))


class TruthManifestTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT
        self.roadmap = m0.load_json(ROOT / m0.ROADMAP_PATH)
        self.truth = m0.load_json(ROOT / m0.TRUTH_PATH)
        self.canonical_version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

    def validate(self, truth: dict) -> list[str]:
        errors: list[str] = []
        m0.validate_truth_manifest(
            self.root,
            truth,
            self.roadmap,
            self.canonical_version,
            errors,
        )
        return errors

    def test_current_milestone_mirror_drift_is_rejected(self):
        changed = copy.deepcopy(self.truth)
        changed["roadmap"]["current_milestone"] = "M10"
        self.assertTrue(any("current milestone" in error for error in self.validate(changed)))

    def test_publication_mirror_drift_is_rejected(self):
        for field, value in (
            ("state", "published"),
            ("github_release_objects", 1),
            ("agnostic_specification_releases", 1),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.truth)
                changed["publication"][field] = value
                self.assertTrue(any("publication values" in error for error in self.validate(changed)))

    def test_platform_gate_mirror_drift_is_rejected(self):
        for field, value in (
            ("authorized_after", "M9"),
            ("status", "authorized"),
            ("platform_work_authorized", True),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.truth)
                changed["platform_gate"][field] = value
                self.assertTrue(any("embedded platform gate" in error for error in self.validate(changed)))


class ReleasePolicyTests(unittest.TestCase):
    def setUp(self):
        self.root = ROOT
        self.roadmap = m0.load_json(ROOT / m0.ROADMAP_PATH)
        self.policy = m0.load_json(ROOT / m0.RELEASE_POLICY_PATH)
        self.debt = m0.load_json(ROOT / m0.DEBT_PATH)

    def validate(self, policy: dict, debt: dict | None = None) -> list[str]:
        errors: list[str] = []
        m0.validate_release_policy(
            self.root,
            self.roadmap,
            policy,
            "2.0.23",
            errors,
            self.debt if debt is None else debt,
        )
        return errors

    def test_non_publication_release_concepts_cannot_publish_specification(self):
        changed = copy.deepcopy(self.policy)
        concept = next(item for item in changed["concepts"] if item["id"] == "github_release_object")
        concept["creates_specification_publication"] = True
        self.assertTrue(any("github_release_object" in error for error in self.validate(changed)))

    def test_historical_release_exception_must_resolve_to_accepted_debt(self):
        changed_debt = copy.deepcopy(self.debt)
        record = next(
            item
            for item in changed_debt["debts"]
            if item["debt_id"] == self.policy["historical_exception_ref"]
        )
        record["status"] = "open"
        self.assertTrue(any("accepted historical-release debt" in error for error in self.validate(self.policy, changed_debt)))

    def test_existing_tag_count_must_match_live_git(self):
        changed = copy.deepcopy(self.policy)
        changed["tag_semantics"]["existing_tag_count"] += 1
        self.assertTrue(any("existing_tag_count" in error for error in self.validate(changed)))

    def test_tags_at_current_head_must_match_live_git(self):
        changed = copy.deepcopy(self.policy)
        changed["tag_semantics"]["tags_at_current_head"] = ["v999.0.0"]
        self.assertTrue(any("tags_at_current_head" in error for error in self.validate(changed)))


class SourceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        authority = "data/governance/artifact_classification_manifest.json"
        write_text(
            self.root,
            "docs/project/source_inventory.md",
            f"# Source inventory\n\nCurrent placeholder artifacts: `2`\n\nAuthority: `{authority}`\n",
        )
        write_text(
            self.root,
            "missing_source_documents.md",
            f"# Missing sources\n\n- Current placeholder records: 2\n- Authority: `{authority}`\n",
        )
        write_text(
            self.root,
            "SOURCE_AVAILABILITY_MANIFEST.md",
            "# Historical source availability provenance\n",
        )

    def tearDown(self):
        self.directory.cleanup()

    def validate(self) -> list[str]:
        errors: list[str] = []
        m0.validate_source_inventories(self.root, {"one.md", "two.md"}, errors)
        return errors

    def test_count_and_authority_are_sufficient_for_human_inventories(self):
        self.assertEqual([], self.validate())

    def test_stale_placeholder_count_is_rejected(self):
        path = self.root / "missing_source_documents.md"
        path.write_text(path.read_text(encoding="utf-8").replace("records: 2", "records: 1"), encoding="utf-8")
        self.assertTrue(any("placeholder count is stale" in error for error in self.validate()))


class PlatformAndTransitionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.roadmap = roadmap_fixture()
        policy = {
            "owner": "Jim Daley",
            "legal_owner": "James Daley",
            "owner_aliases": ["Jim Daley"],
            "operating_modes": {
                "spec_repo_mode": {
                    "applies_when": "repository == flynn33/yggdrasil-world-engine on any branch"
                },
                "engine_repo_mode": {
                    "description": "Separate downstream work after M10.",
                    "applies_when": (
                        "repository != flynn33/yggdrasil-world-engine and M10 == complete "
                        "and platform_work_authorized == true"
                    ),
                }
            },
            "platform_gate": {
                "authorized_after": "M10",
                "status": "deferred",
                "platform_work_authorized": False,
                "downstream_repository_required": True,
            },
        }
        write_json(self.root, "repository-contribution-policy.json", policy)
        write_json(self.root, "yggdrasil-instructions.json", {"project": {"owner": "Jim Daley"}})

    def tearDown(self):
        self.directory.cleanup()

    def test_valid_platform_and_identity_policy(self):
        errors: list[str] = []
        m0.validate_platform_and_identity_contracts(self.root, self.roadmap, errors)
        self.assertEqual([], errors)

    def test_platform_authorization_before_m10_is_rejected(self):
        changed = copy.deepcopy(self.roadmap)
        changed["platform_gate"] = {"status": "authorized", "platform_work_authorized": True}
        errors: list[str] = []
        m0.validate_platform_and_identity_contracts(self.root, changed, errors)
        self.assertTrue(any("before M10" in error for error in errors))

    def test_contribution_policy_authorization_before_m10_is_rejected(self):
        policy = m0.load_json(self.root / "repository-contribution-policy.json")
        policy["platform_gate"]["status"] = "authorized"
        policy["platform_gate"]["platform_work_authorized"] = True
        write_json(self.root, "repository-contribution-policy.json", policy)
        errors: list[str] = []
        m0.validate_platform_and_identity_contracts(self.root, self.roadmap, errors)
        self.assertTrue(any("disagrees with the roadmap" in error for error in errors))

    def test_platform_authorization_after_m10_is_accepted(self):
        changed = copy.deepcopy(self.roadmap)
        next(item for item in changed["milestones"] if item["id"] == "M10")["status"] = "complete"
        changed["platform_gate"] = {"status": "authorized", "platform_work_authorized": True}
        policy = m0.load_json(self.root / "repository-contribution-policy.json")
        policy["platform_gate"]["status"] = "authorized"
        policy["platform_gate"]["platform_work_authorized"] = True
        write_json(self.root, "repository-contribution-policy.json", policy)
        errors: list[str] = []
        m0.validate_platform_and_identity_contracts(self.root, changed, errors)
        self.assertEqual([], errors)

    def test_non_main_branch_product_mode_is_rejected(self):
        policy = m0.load_json(self.root / "repository-contribution-policy.json")
        policy["operating_modes"]["engine_repo_mode"]["applies_when"] = "branch != main"
        write_json(self.root, "repository-contribution-policy.json", policy)
        errors: list[str] = []
        m0.validate_platform_and_identity_contracts(self.root, self.roadmap, errors)
        self.assertTrue(any("non-main branch" in error for error in errors))

    def test_unknown_owner_alias_is_rejected(self):
        policy = m0.load_json(self.root / "repository-contribution-policy.json")
        policy["owner_aliases"] = ["Unknown Person"]
        write_json(self.root, "repository-contribution-policy.json", policy)
        errors: list[str] = []
        m0.validate_platform_and_identity_contracts(self.root, self.roadmap, errors)
        self.assertTrue(any("recognized alias" in error for error in errors))

    def test_m1_in_progress_while_m0_incomplete_is_rejected(self):
        changed = copy.deepcopy(self.roadmap)
        changed["milestones"][1]["status"] = "in_progress"
        errors = m0.transition_errors(self.root, changed)
        self.assertTrue(any("M1 cannot" in error for error in errors))

    def test_m0_complete_without_evidence_is_rejected(self):
        changed = copy.deepcopy(self.roadmap)
        changed["milestones"][0]["status"] = "complete"
        errors = m0.transition_errors(self.root, changed)
        self.assertTrue(any("must reference exactly" in error for error in errors))

    def test_historical_m0_transition_does_not_require_m1_to_remain_current(self):
        changed = copy.deepcopy(self.roadmap)
        changed["milestones"][0]["status"] = "complete"
        changed["milestones"][1]["status"] = "complete"
        changed["milestones"][2]["status"] = "in_progress"
        changed["current_milestone"] = "M2"
        errors = m0.transition_errors(self.root, changed)
        self.assertFalse(any("requires M1 to have been activated" in error for error in errors))
        self.assertFalse(any("cannot remain the current milestone" in error for error in errors))


class GitDiffTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Test User")
        git(self.root, "config", "user.email", "test@example.invalid")
        self.protected = "docs/architecture/base_world_ontology_contract.md"
        write_text(self.root, self.protected, "base\n")
        write_json(
            self.root,
            m0.PHASE_8_9_REQUIRED_PATH,
            {
                "phase_9_architecture_contracts": [self.protected],
                "phase_9_schemas": [],
                "phase_9_validation": [],
            },
        )
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Base")

    def tearDown(self):
        self.directory.cleanup()

    def test_protected_worktree_modification_is_rejected(self):
        write_text(self.root, self.protected, "changed\n")
        errors, hits = m0.protected_diff_errors(self.root, "HEAD")
        self.assertIn(self.protected, hits)
        self.assertTrue(any("protected Phase 9" in error for error in errors))

    def test_protected_rename_is_rejected(self):
        git(self.root, "mv", self.protected, "docs/architecture/renamed.md")
        errors, hits = m0.protected_diff_errors(self.root, "HEAD")
        self.assertIn(self.protected, hits)
        self.assertTrue(errors)

    def test_missing_base_ref_is_rejected(self):
        errors, _hits = m0.protected_diff_errors(self.root, "missing-ref")
        self.assertTrue(any("Unable to resolve" in error for error in errors))

    def test_untracked_candidate_path_is_enumerated(self):
        write_text(self.root, "new-governance.md", "new\n")
        errors: list[str] = []
        paths = m0.repository_candidate_paths(self.root, errors)
        self.assertEqual([], errors)
        self.assertIn("new-governance.md", paths)


class NonDestructiveChangeCollectionTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Test User")
        git(self.root, "config", "user.email", "test@example.invalid")
        write_text(self.root, ".gitignore", "ignored.tmp\n")
        for path in (
            "committed.txt",
            "staged.txt",
            "unstaged.txt",
            "overlap.txt",
            "docs/old.md",
        ):
            write_text(self.root, path, f"base {path}\n")
        git(self.root, "add", "--", ".")
        git(self.root, "commit", "-q", "-m", "baseline")
        self.base = git(self.root, "rev-parse", "HEAD").stdout.decode("ascii").strip()

    def tearDown(self):
        self.directory.cleanup()

    def test_union_includes_committed_staged_unstaged_and_nonignored_untracked(self):
        write_text(self.root, "committed.txt", "committed change\n")
        git(self.root, "add", "--", "committed.txt")
        git(self.root, "commit", "-q", "-m", "committed change")
        write_text(self.root, "staged.txt", "staged change\n")
        git(self.root, "add", "--", "staged.txt")
        write_text(self.root, "unstaged.txt", "unstaged change\n")
        write_text(self.root, "new.txt", "untracked\n")
        write_text(self.root, "ignored.tmp", "ignored\n")

        records, errors = diff_check.collect_change_records(self.root, self.base, "HEAD")
        summary = diff_check.summarize_changes(records)

        self.assertEqual([], errors)
        self.assertEqual(
            {"committed", "staged", "unstaged", "untracked"},
            {record.source for record in records},
        )
        self.assertEqual({"committed.txt", "staged.txt", "unstaged.txt"}, summary.modified)
        self.assertEqual({"new.txt"}, summary.added)
        self.assertNotIn("ignored.tmp", summary.added)
        evaluation = diff_check.evaluate_changes(
            self.root,
            self.base,
            "HEAD",
            non_destructive_policy(),
        )
        self.assertEqual([], evaluation.fatal_failures)
        self.assertEqual([], evaluation.policy_failures)

    def test_same_path_staged_and_unstaged_is_counted_once(self):
        write_text(self.root, "overlap.txt", "staged version\n")
        git(self.root, "add", "--", "overlap.txt")
        write_text(self.root, "overlap.txt", "unstaged version\n")

        records, errors = diff_check.collect_change_records(self.root, self.base, "HEAD")
        summary = diff_check.summarize_changes(records)

        self.assertEqual([], errors)
        self.assertEqual({"staged", "unstaged"}, {record.source for record in records})
        self.assertEqual({"overlap.txt"}, summary.modified)

    def test_uncommitted_deletion_is_subject_to_budget(self):
        (self.root / "unstaged.txt").unlink()

        evaluation = diff_check.evaluate_changes(
            self.root,
            self.base,
            "HEAD",
            non_destructive_policy(max_deleted_files=0),
        )

        self.assertEqual([], evaluation.fatal_failures)
        self.assertEqual({"unstaged.txt"}, evaluation.summary.deleted)
        self.assertTrue(
            any("deletions exceed budget 0" in item for item in evaluation.policy_failures)
        )

    def test_staged_rename_preserves_both_paths_and_is_subject_to_policy(self):
        git(self.root, "mv", "--", "docs/old.md", "docs/new.md")

        evaluation = diff_check.evaluate_changes(
            self.root,
            self.base,
            "HEAD",
            non_destructive_policy(
                max_renamed_files=0,
                fail_on_deleted_protected_paths=True,
            ),
        )

        self.assertEqual([], evaluation.fatal_failures)
        self.assertEqual({("docs/old.md", "docs/new.md")}, evaluation.summary.renamed)
        self.assertTrue(
            any("docs/old.md -> docs/new.md" in item for item in evaluation.policy_failures)
        )
        self.assertTrue(
            any("deleted or renamed protected paths" in item for item in evaluation.policy_failures)
        )


class NonDestructiveChangeParserTests(unittest.TestCase):
    def test_rename_record_preserves_old_and_new_paths(self):
        records, errors = diff_check.parse_name_status_z(
            b"R100\0docs/old.md\0docs/new.md\0",
            "test",
        )
        self.assertEqual([], errors)
        self.assertEqual(
            [diff_check.ChangeRecord("R100", ("docs/old.md", "docs/new.md"), "test")],
            records,
        )

    def test_truncated_rename_record_is_rejected(self):
        records, errors = diff_check.parse_name_status_z(
            b"R100\0docs/old.md\0",
            "test",
        )
        self.assertEqual([], records)
        self.assertTrue(any("truncated" in item for item in errors))

    def test_out_of_range_similarity_score_is_rejected(self):
        records, errors = diff_check.parse_name_status_z(
            b"R101\0docs/old.md\0docs/new.md\0",
            "test",
        )
        self.assertEqual([], records)
        self.assertTrue(any("malformed or unsupported" in item for item in errors))

    def test_unsafe_or_noncanonical_paths_are_rejected(self):
        unsafe_paths = (
            "../escape",
            "/absolute",
            "C:/absolute",
            "dir\\file",
            "dir//file",
            "./file",
            "line\nbreak",
        )
        for path in unsafe_paths:
            with self.subTest(path=path):
                payload = b"M\0" + path.encode("utf-8") + b"\0"
                records, errors = diff_check.parse_name_status_z(payload, "test")
                self.assertEqual([], records)
                self.assertTrue(any("unsafe or non-canonical" in item for item in errors))

    def test_non_nul_terminated_output_is_rejected(self):
        records, errors = diff_check.parse_name_status_z(b"M\0file.txt", "test")
        self.assertEqual([], records)
        self.assertTrue(any("not NUL terminated" in item for item in errors))

    def test_negative_budget_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be non-negative"):
            diff_check.int_policy_value({"limit": -1}, ("limit",), 0)


class ImplementationDiffStateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Test User")
        git(self.root, "config", "user.email", "test@example.invalid")
        write_text(self.root, "tracked.txt", "base\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Base")
        self.base_sha = git(self.root, "rev-parse", "HEAD").stdout.decode("ascii").strip()

    def tearDown(self):
        self.directory.cleanup()

    def test_complete_state_includes_committed_staged_unstaged_and_untracked_without_index_mutation(self):
        write_text(self.root, "committed.txt", "committed\n")
        git(self.root, "add", "committed.txt")
        git(self.root, "commit", "-q", "-m", "Committed implementation")
        write_text(self.root, "staged.txt", "staged\n")
        git(self.root, "add", "staged.txt")
        write_text(self.root, "tracked.txt", "unstaged\n")
        write_text(self.root, "untracked.txt", "untracked\n")
        write_json(self.root, m0.EVIDENCE_PATH, {"excluded": True})
        write_text(self.root, m0.ACCEPTANCE_DOCUMENT_PATH, "excluded\n")
        index_path = Path(
            git(self.root, "rev-parse", "--git-path", "index").stdout.decode("utf-8").strip()
        )
        if not index_path.is_absolute():
            index_path = self.root / index_path
        index_before = index_path.read_bytes()
        state = m0.implementation_diff_state(self.root, self.base_sha)
        index_after = index_path.read_bytes()
        self.assertEqual(index_before, index_after)
        self.assertEqual(3, state["files_created"])
        self.assertEqual(1, state["files_patched"])
        self.assertEqual(0, state["files_deleted"])
        self.assertEqual(0, state["files_renamed"])
        self.assertNotIn(m0.EVIDENCE_PATH, state["numstat"])
        self.assertNotIn(m0.ACCEPTANCE_DOCUMENT_PATH, state["numstat"])
        repeated = m0.implementation_diff_state(self.root, self.base_sha)
        self.assertEqual(state["diff_hash"], repeated["diff_hash"])
        self.assertEqual(state["diff_stat"], repeated["diff_stat"])

    def test_snapshot_state_excludes_acceptance_artifacts(self):
        write_text(self.root, "implementation.txt", "implementation\n")
        write_json(self.root, m0.EVIDENCE_PATH, {"excluded": True})
        write_text(self.root, m0.ACCEPTANCE_DOCUMENT_PATH, "excluded\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Acceptance snapshot")
        snapshot_sha = git(self.root, "rev-parse", "HEAD").stdout.decode("ascii").strip()
        state = m0.implementation_diff_state(
            self.root,
            self.base_sha,
            snapshot_ref=snapshot_sha,
        )
        self.assertEqual(1, state["files_created"])
        self.assertNotIn(m0.EVIDENCE_PATH, state["numstat"])
        self.assertNotIn(m0.ACCEPTANCE_DOCUMENT_PATH, state["numstat"])


class AcceptanceEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        write_text(
            self.root,
            "README.md",
            "".join(f"baseline line {number}\n" for number in range(1, 21)),
        )
        write_text(self.root, "VERSION", "2.0.23\n")
        self.roadmap = roadmap_fixture()
        write_json(self.root, m0.ROADMAP_PATH, self.roadmap)
        self.catalog = {
            "checks": [
                {
                    "id": "always_check",
                    "command": ["{python}", "scripts/always_check.py", "{root}"],
                    "contexts": ["always"],
                },
                {
                    "id": "pr_check",
                    "command": ["{python}", "scripts/pr_check.py", "{root}"],
                    "contexts": ["pull_request"],
                },
            ]
        }
        write_json(self.root, m0.CHECK_CATALOG_PATH, self.catalog)
        git(self.root, "init", "-q")
        git(self.root, "config", "user.name", "Test User")
        git(self.root, "config", "user.email", "test@example.invalid")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Ancestor")
        self.ancestor_sha = git(self.root, "rev-parse", "HEAD").stdout.decode("ascii").strip()
        write_text(self.root, "base-marker.txt", "base\n")
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Base")
        self.base_sha = git(self.root, "rev-parse", "HEAD").stdout.decode("ascii").strip()
        self.branch = git(self.root, "branch", "--show-current").stdout.decode("utf-8").strip()
        readme_path = self.root / "README.md"
        write_text(
            self.root,
            "README.md",
            readme_path.read_text(encoding="utf-8") + "implementation\n",
        )
        self.roadmap["milestones"][0]["status"] = "complete"
        self.roadmap["milestones"][0]["acceptance_evidence"] = list(m0.M0_EVIDENCE_REFS)
        self.roadmap["milestones"][1]["status"] = "in_progress"
        self.roadmap["current_milestone"] = "M1"
        write_json(self.root, m0.ROADMAP_PATH, self.roadmap)
        write_text(self.root, "implementation-note.txt", "untracked implementation state\n")
        candidate_errors: list[str] = []
        self.paths = m0.repository_candidate_paths(self.root, candidate_errors)
        self.assertEqual([], candidate_errors)
        self.diff_state = m0.implementation_diff_state(self.root, "HEAD")
        budget_entries, budget_errors = m0.expected_change_budget_entries(
            self.root,
            self.base_sha,
            self.diff_state["numstat"],
        )
        self.assertEqual([], budget_errors)
        readme_budget = budget_entries["README.md"]
        class_counts = {name: 0 for name in sorted(m0.MATURITY_CLASSES)}
        class_counts["informative"] = len(self.paths)
        self.classification = {"coverage": {"counts_by_class": class_counts}}
        scope_counts = {name: 0 for name in sorted(m0.SCOPE_PARTITIONS)}
        scope_counts["governance_validation"] = len(self.paths)
        self.scope = {"coverage": {"counts_by_partition": scope_counts}}
        promise_aggregate = "1" * 64
        self.promise_register = {
            "reviewed_surfaces": [{"path": "README.md", "sha256": "0" * 64}],
            "reviewed_surface_aggregate_sha256": promise_aggregate,
            "summary": {
                "reviewed_surface_count": 1,
                "promise_count": 1,
                "assigned_count": 1,
                "excluded_count": 0,
                "unresolved_count": 0,
            }
        }
        self.debt_inventory = {
            "summary": {
                "total": 1,
                "open": 1,
                "accepted_exception": 0,
                "resolved": 0,
                "by_milestone": {"M1": 1},
            }
        }
        self.evidence = {
            "artifact_version": m0.EVIDENCE_ARTIFACT_VERSION,
            "milestone_id": "M0",
            "outcome": "pass",
            "unresolved_issues": [],
            "source_inventory_result": "pass",
            "baseline": {
                "repository_version": "2.0.23",
                "base_ref": "HEAD",
                "base_sha": self.base_sha,
                "merge_base": self.base_sha,
                "branch": self.branch,
                "publication_state": self.roadmap["publication"]["state"],
                "tags_at_head": [],
                "platform_work_authorized": self.roadmap["platform_gate"][
                    "platform_work_authorized"
                ],
            },
            "exit_criteria": [
                {"id": f"m0-e{number}", "outcome": "pass"} for number in range(1, 4)
            ],
            "foundation_gates": [
                {"id": gate, "outcome": "pass"} for gate in sorted(m0.FOUNDATION_GATES)
            ],
            "protected_path_diff": {"base_ref": "HEAD", "changed_paths": []},
            "roadmap_transition": {
                "completed_milestone": "M0",
                "activated_milestone": "M1",
                "current_milestone": "M1",
            },
            "digest_exclusions": sorted(m0.M0_DIGEST_EXCLUSIONS),
            "repository_state_digest": m0.repository_state_digest(
                self.root, self.paths, m0.M0_DIGEST_EXCLUSIONS
            ),
            "diff_review": {
                "base_ref": "HEAD",
                **{
                    field: self.diff_state[field]
                    for field in (
                        "files_created",
                        "files_patched",
                        "files_deleted",
                        "files_renamed",
                        "diff_stat",
                        "diff_hash",
                    )
                },
                "implementation_tree_hash_algorithm": m0.REPOSITORY_STATE_DIGEST_ALGORITHM,
                "implementation_tree_hash": m0.repository_state_digest(
                    self.root, self.paths, m0.M0_DIGEST_EXCLUSIONS
                ),
                "diff_hash_algorithm": m0.DIFF_HASH_ALGORITHM,
                "hash_scope": (
                    "implementation-state-and-diff-excluding-the-two-m0-"
                    "acceptance-evidence-files"
                ),
                "change_budget_exceptions": [
                    {
                        "path": "README.md",
                        **readme_budget,
                        "rationale": "Required truthful-baseline test implementation change.",
                        "authority_refs": ["README.md"],
                        "result": "within_authorized_ceiling",
                    }
                ],
            },
            "check_catalog": {
                "sha256": m0.normalized_text_sha256(self.root / m0.CHECK_CATALOG_PATH)
            },
            "classification_metrics": {
                "tracked_paths": len(self.paths),
                "classified_paths": len(self.paths),
                "unclassified_paths": 0,
                "multiply_classified_paths": 0,
                **class_counts,
            },
            "scope_metrics": scope_counts,
            "promise_metrics": {
                "reviewed_surfaces": 1,
                "total": 1,
                "assigned": 1,
                "excluded": 0,
                "unresolved": 0,
            },
            "promise_source_evidence": {
                "register_ref": m0.PROMISE_PATH,
                "hash_algorithm": m0.NORMALIZED_TEXT_SHA256_ALGORITHM,
                "source_hash_count": 1,
                "reviewed_surface_aggregate_sha256": promise_aggregate,
            },
            "debt_metrics": {
                "total": 1,
                "open": 1,
                "accepted_exception": 0,
                "resolved": 0,
                **{f"milestone_m{number}": int(number == 1) for number in range(11)},
            },
            "validation_runs": [
                {
                    "context": "local",
                    "results": [
                        passing_check_result("always_check")
                    ],
                },
                {
                    "context": "pull_request",
                    "results": [
                        passing_check_result("always_check"),
                        passing_check_result("pr_check"),
                    ],
                },
            ],
        }
        write_text(
            self.root,
            m0.ACCEPTANCE_DOCUMENT_PATH,
            acceptance_document_fixture(self.evidence),
        )

    def tearDown(self):
        self.directory.cleanup()

    def validate(self, evidence: dict) -> list[str]:
        errors: list[str] = []
        m0.validate_acceptance_evidence(
            self.root,
            self.paths,
            evidence,
            self.roadmap,
            "HEAD",
            set(),
            errors,
            classification=self.classification,
            scope=self.scope,
            promise_register=self.promise_register,
            debt_inventory=self.debt_inventory,
        )
        return errors

    def commit_evidence(self, evidence: dict) -> None:
        write_json(self.root, m0.EVIDENCE_PATH, evidence)
        write_text(
            self.root,
            m0.ACCEPTANCE_DOCUMENT_PATH,
            acceptance_document_fixture(evidence),
        )
        git(self.root, "add", ".")
        git(self.root, "commit", "-q", "-m", "Record M0 acceptance")

    def test_valid_acceptance_evidence_semantics(self):
        self.assertEqual([], self.validate(copy.deepcopy(self.evidence)))

    def test_evidence_artifact_version_is_not_repository_version(self):
        changed = copy.deepcopy(self.evidence)
        changed["artifact_version"] = "2.0.23"
        self.assertTrue(
            any("artifact version" in error for error in self.validate(changed))
        )

    def test_scope_metrics_are_bound_to_scope_manifest_coverage(self):
        changed = copy.deepcopy(self.evidence)
        changed["scope_metrics"]["governance_validation"] += 1
        self.assertTrue(
            any("scope metrics" in error for error in self.validate(changed))
        )

    def test_promise_source_evidence_is_bound_to_register(self):
        mutations = (
            ("register_ref", "data/governance/forged.json"),
            ("hash_algorithm", "sha256_raw_bytes"),
            ("source_hash_count", 2),
            ("reviewed_surface_aggregate_sha256", "2" * 64),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.evidence)
                changed["promise_source_evidence"][field] = value
                self.assertTrue(
                    any(
                        "public-promise source evidence" in error
                        for error in self.validate(changed)
                    )
                )

    def test_missing_catalog_result_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["validation_runs"][0]["results"] = []
        self.assertTrue(any("catalog order" in error for error in self.validate(changed)))

    def test_duplicate_catalog_result_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["validation_runs"][0]["results"].append(
            copy.deepcopy(changed["validation_runs"][0]["results"][0])
        )
        self.assertTrue(any("catalog order" in error for error in self.validate(changed)))

    def test_nonzero_check_result_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["validation_runs"][0]["results"][0]["exit_code"] = 1
        self.assertTrue(any("non-passing check" in error for error in self.validate(changed)))

    def test_noncanonical_check_command_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["validation_runs"][0]["results"][0]["command"] = ["skip-checks"]
        self.assertTrue(any("non-canonical check command" in error for error in self.validate(changed)))

    def test_failed_check_result_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["validation_runs"][0]["results"][0]["outcome"] = "fail"
        self.assertTrue(any("non-passing check" in error for error in self.validate(changed)))

    def test_missing_result_summary_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        del changed["validation_runs"][0]["results"][0]["result_summary"]
        self.assertTrue(any("lacks a concise result summary" in error for error in self.validate(changed)))

    def test_wrong_result_summary_hash_algorithm_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["validation_runs"][0]["results"][0]["result_summary_hash_algorithm"] = "sha256_file_bytes"
        self.assertTrue(any("wrong result-summary hash algorithm" in error for error in self.validate(changed)))

    def test_stale_result_summary_hash_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["validation_runs"][0]["results"][0]["result_summary_sha256"] = "0" * 64
        self.assertTrue(any("result-summary hash is stale" in error for error in self.validate(changed)))

    def test_missing_pull_request_run_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["validation_runs"] = changed["validation_runs"][:1]
        self.assertTrue(any("local then pull_request" in error for error in self.validate(changed)))

    def test_stale_baseline_sha_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["baseline"]["base_sha"] = "0" * 40
        self.assertTrue(any("baseline SHA" in error for error in self.validate(changed)))

    def test_fabricated_ancestral_base_sha_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["baseline"]["base_sha"] = self.ancestor_sha
        self.assertTrue(any("resolved base ref" in error for error in self.validate(changed)))

    def test_stale_merge_base_branch_and_head_tags_are_rejected(self):
        mutations = (
            ("merge_base", "0" * 40, "merge base is stale"),
            ("branch", "fabricated/branch", "branch is stale"),
            ("tags_at_head", ["v999.0.0"], "tags_at_head is stale"),
        )
        for field, value, expected_error in mutations:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.evidence)
                changed["baseline"][field] = value
                self.assertTrue(any(expected_error in error for error in self.validate(changed)))

    def test_acceptance_publication_and_platform_must_match_roadmap(self):
        changed = copy.deepcopy(self.evidence)
        changed["baseline"]["publication_state"] = "published"
        changed["baseline"]["platform_work_authorized"] = True
        errors = self.validate(changed)
        self.assertTrue(any("publication state" in error for error in errors))
        self.assertTrue(any("platform authorization" in error for error in errors))

    def test_stale_diff_counts_stat_hash_and_tree_hash_are_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["diff_review"]["files_created"] += 1
        changed["diff_review"]["diff_stat"] = "fabricated diff stat"
        changed["diff_review"]["diff_hash"] = "0" * 64
        changed["diff_review"]["implementation_tree_hash"] = "f" * 64
        errors = self.validate(changed)
        for field in ("files_created", "diff_stat", "diff_hash"):
            self.assertTrue(any(field in error and "stale" in error for error in errors))
        self.assertTrue(any("implementation tree hash is stale" in error for error in errors))

    def test_untracked_implementation_change_stales_complete_diff_proof(self):
        write_text(self.root, "late-untracked.txt", "late implementation state\n")
        candidate_errors: list[str] = []
        self.paths = m0.repository_candidate_paths(self.root, candidate_errors)
        self.assertEqual([], candidate_errors)
        errors = self.validate(copy.deepcopy(self.evidence))
        self.assertTrue(any("files_created" in error and "stale" in error for error in errors))
        self.assertTrue(any("diff_hash" in error and "stale" in error for error in errors))

    def test_fabricated_change_budget_ledger_values_are_rejected(self):
        changed = copy.deepcopy(self.evidence)
        entry = changed["diff_review"]["change_budget_exceptions"][0]
        entry["original_lines"] += 1
        entry["percentage"] += 1
        entry["authorized_ceiling"] += 1
        errors = self.validate(changed)
        for field in ("original_lines", "percentage", "authorized_ceiling"):
            self.assertTrue(any(field in error and "stale" in error for error in errors))

    def test_over_ceiling_document_change_is_rejected(self):
        readme_path = self.root / "README.md"
        write_text(
            self.root,
            "README.md",
            readme_path.read_text(encoding="utf-8") + "one\ntwo\nthree\nfour\nfive\n",
        )
        candidate_errors: list[str] = []
        self.paths = m0.repository_candidate_paths(self.root, candidate_errors)
        self.assertEqual([], candidate_errors)
        self.assertTrue(
            any("exceeds authorized ceiling" in error for error in self.validate(self.evidence))
        )

    def test_failed_exit_criterion_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["exit_criteria"][0]["outcome"] = "fail"
        self.assertTrue(any("three passing" in error for error in self.validate(changed)))

    def test_protected_change_in_evidence_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["protected_path_diff"]["changed_paths"] = ["protected.md"]
        self.assertTrue(any("protected Phase 9" in error for error in self.validate(changed)))

    def test_state_digest_drift_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["repository_state_digest"] = "0" * 64
        self.assertTrue(any("state digest is stale" in error for error in self.validate(changed)))

    def test_acceptance_metrics_drift_is_rejected(self):
        changed = copy.deepcopy(self.evidence)
        changed["classification_metrics"]["tracked_paths"] = 2
        changed["promise_metrics"]["assigned"] = 0
        changed["debt_metrics"]["open"] = 0
        errors = self.validate(changed)
        self.assertTrue(any("classification metrics" in error for error in errors))
        self.assertTrue(any("public-promise metrics" in error for error in errors))
        self.assertTrue(any("quality-debt metrics" in error for error in errors))

    def test_empty_acceptance_markdown_is_rejected(self):
        write_text(self.root, m0.ACCEPTANCE_DOCUMENT_PATH, "")
        self.assertTrue(any("Markdown is empty" in error for error in self.validate(self.evidence)))

    def test_acceptance_markdown_missing_required_heading_is_rejected(self):
        document_path = self.root / m0.ACCEPTANCE_DOCUMENT_PATH
        document = document_path.read_text(encoding="utf-8")
        write_text(
            self.root,
            m0.ACCEPTANCE_DOCUMENT_PATH,
            document.replace("## Deferred Work", "Deferred Work"),
        )
        self.assertTrue(
            any("H2 headings must be exactly" in error for error in self.validate(self.evidence))
        )

    def test_acceptance_markdown_stale_metric_is_rejected(self):
        document_path = self.root / m0.ACCEPTANCE_DOCUMENT_PATH
        document = document_path.read_text(encoding="utf-8")
        tracked = self.evidence["classification_metrics"]["tracked_paths"]
        write_text(
            self.root,
            m0.ACCEPTANCE_DOCUMENT_PATH,
            document.replace(f"Tracked paths: {tracked}", f"Tracked paths: {tracked + 1}"),
        )
        self.assertTrue(
            any("headline metrics" in error for error in self.validate(self.evidence))
        )

    def test_acceptance_markdown_misleading_judgment_is_rejected(self):
        document_path = self.root / m0.ACCEPTANCE_DOCUMENT_PATH
        document = document_path.read_text(encoding="utf-8")
        write_text(
            self.root,
            m0.ACCEPTANCE_DOCUMENT_PATH,
            document.replace("M0: ACCEPTED", "M0: REJECTED"),
        )
        self.assertTrue(
            any("misleading" in error for error in self.validate(self.evidence))
        )

    def test_committed_acceptance_uses_immutable_snapshot_after_later_changes(self):
        committed = copy.deepcopy(self.evidence)
        self.commit_evidence(committed)
        write_text(self.root, "README.md", "later milestone change\n")
        self.assertEqual([], self.validate(committed))

    def test_committed_acceptance_does_not_stale_after_later_roadmap_progress(self):
        committed = copy.deepcopy(self.evidence)
        self.commit_evidence(committed)
        self.roadmap["milestones"][0]["status"] = "complete"
        self.roadmap["milestones"][1]["status"] = "complete"
        self.roadmap["milestones"][2]["status"] = "in_progress"
        self.roadmap["current_milestone"] = "M2"
        self.assertEqual([], self.validate(committed))

    def test_committed_acceptance_artifact_modification_is_rejected(self):
        committed = copy.deepcopy(self.evidence)
        self.commit_evidence(committed)
        changed = copy.deepcopy(committed)
        changed["baseline"]["branch"] = "rewritten-branch"
        write_json(self.root, m0.EVIDENCE_PATH, changed)
        self.assertTrue(any("changed after its introduction" in error for error in self.validate(changed)))

    def test_committed_acceptance_rejects_self_consistent_older_ancestor_base(self):
        committed = copy.deepcopy(self.evidence)
        forged_state = m0.implementation_diff_state(self.root, self.ancestor_sha)
        committed["baseline"]["base_sha"] = self.ancestor_sha
        committed["baseline"]["merge_base"] = self.ancestor_sha
        for field in (
            "files_created",
            "files_patched",
            "files_deleted",
            "files_renamed",
            "diff_stat",
            "diff_hash",
        ):
            committed["diff_review"][field] = forged_state[field]
        expected_entries, budget_errors = m0.expected_change_budget_entries(
            self.root,
            self.ancestor_sha,
            forged_state["numstat"],
        )
        self.assertEqual([], budget_errors)
        recorded_entry = committed["diff_review"]["change_budget_exceptions"][0]
        recorded_entry.update(expected_entries["README.md"])
        self.commit_evidence(committed)
        self.assertTrue(
            any("evidence-introduction parent" in error for error in self.validate(committed))
        )


class AcceptanceEvidenceSchemaTests(unittest.TestCase):
    def setUp(self):
        self.schema = m0.load_json(
            ROOT / "data/schemas/milestone_acceptance_evidence_schema.json"
        )
        sha256 = "0" * 64
        git_sha = "0" * 40

        def judgment(identifier: str) -> dict:
            return {
                "id": identifier,
                "outcome": "pass",
                "evidence_refs": ["data/governance/repository_truth_manifest.json"],
            }

        self.instance = {
            "artifact_type": "milestone_acceptance_evidence",
            "artifact_version": "1.0.0",
            "schema_ref": "data/schemas/milestone_acceptance_evidence_schema.json",
            "milestone_id": "M0",
            "outcome": "pass",
            "recorded_at": "2026-07-19T12:00:00Z",
            "baseline": {
                "repository_version": "2.0.23",
                "base_ref": "origin/main",
                "base_sha": git_sha,
                "merge_base": git_sha,
                "branch": "governance/m0-truthful-baseline-closure",
                "publication_state": "unreleased",
                "tags_at_head": [],
                "platform_work_authorized": False,
            },
            "authority_and_phase_alignment": {
                "authority_stack": "pass",
                "phase_8_9_anchors_present": "pass",
                "protected_paths_changed": False,
                "platform_code_added": False,
            },
            "repository_state_digest_algorithm": (
                "sha256_sorted_path_nul_normalized_utf8_lf_sha256_nul"
            ),
            "repository_state_digest": sha256,
            "digest_exclusions": sorted(m0.M0_DIGEST_EXCLUSIONS),
            "check_catalog": {
                "path": m0.CHECK_CATALOG_PATH,
                "hash_algorithm": "sha256_utf8_lf_normalized",
                "sha256": sha256,
            },
            "validation_runs": [
                {
                    "context": context,
                    "executed_at": "2026-07-19T12:00:00Z",
                    "results": [passing_check_result("m0_check")],
                }
                for context in ("local", "pull_request")
            ],
            "deliverables": [
                judgment(f"m0-d{number}") for number in range(1, 8)
            ],
            "exit_criteria": [
                judgment(f"m0-e{number}") for number in range(1, 4)
            ],
            "safety_criteria": [
                judgment(f"m0-s{number}") for number in range(1, 5)
            ],
            "foundation_gates": [
                judgment(f"9.{number}") for number in range(3, 9)
            ],
            "classification_metrics": {
                "tracked_paths": 986,
                "classified_paths": 986,
                "unclassified_paths": 0,
                "multiply_classified_paths": 0,
                "normative": 722,
                "informative": 41,
                "example": 160,
                "historical": 10,
                "deprecated": 1,
                "superseded": 6,
                "placeholder": 46,
            },
            "scope_metrics": {
                "ywe_core": 165,
                "ywe_extension_profile": 108,
                "ash_dependency_material": 77,
                "wrw_reference_profile": 242,
                "governance_validation": 316,
                "historical_evidence": 17,
                "later_release_work": 61,
            },
            "promise_metrics": {
                "reviewed_surfaces": 65,
                "total": 33,
                "assigned": 30,
                "excluded": 3,
                "unresolved": 0,
            },
            "promise_source_evidence": {
                "register_ref": m0.PROMISE_PATH,
                "hash_algorithm": "sha256_utf8_lf_normalized",
                "source_hash_count": 65,
                "reviewed_surface_aggregate_sha256": sha256,
            },
            "debt_metrics": {
                "total": 81,
                "open": 70,
                "accepted_exception": 1,
                "resolved": 10,
                **{f"milestone_m{number}": 0 for number in range(11)},
            },
            "debt_ownership_metrics": {
                "unowned_open_count": 0,
                "unassigned_open_count": 0,
            },
            "source_inventory_result": "pass",
            "diff_review": {
                "base_ref": "origin/main",
                "files_created": 20,
                "files_patched": 1,
                "files_deleted": 0,
                "files_renamed": 0,
                "diff_stat": "21 files changed, 100 insertions(+)",
                "implementation_tree_hash_algorithm": (
                    "sha256_sorted_path_nul_normalized_utf8_lf_sha256_nul"
                ),
                "implementation_tree_hash": sha256,
                "diff_hash_algorithm": "sha256_git_diff_binary",
                "diff_hash": sha256,
                "hash_scope": (
                    "implementation-state-and-diff-excluding-the-two-m0-"
                    "acceptance-evidence-files"
                ),
                "change_budget_exceptions": [
                    {
                        "path": "README.md",
                        "original_lines": 100,
                        "additions": 1,
                        "deletions": 1,
                        "percentage": 2.0,
                        "authorized_ceiling": 10.0,
                        "rationale": "Narrow repository truth correction.",
                        "authority_refs": [
                            "docs/project/artifact_classification_policy.md"
                        ],
                        "result": "within_authorized_ceiling",
                    }
                ],
            },
            "protected_path_diff": {
                "base_ref": "origin/main",
                "query": ["git", "diff", "--name-only", "origin/main"],
                "empty_output": True,
                "changed_paths": [],
            },
            "roadmap_transition": {
                "completed_milestone": "M0",
                "activated_milestone": "M1",
                "current_milestone": "M1",
            },
            "deferred_work": [
                {
                    "milestone": f"M{number}",
                    "status": "deferred",
                    "scope": f"M{number} roadmap implementation remains deferred.",
                }
                for number in range(1, 11)
            ],
            "unresolved_issues": [],
        }

    def validate(self, value: dict) -> list[str]:
        return m0.schema_validation_errors(value, self.schema, "acceptance")

    def test_comprehensive_repository_local_evidence_is_accepted(self):
        self.assertEqual([], self.validate(copy.deepcopy(self.instance)))

    def test_every_contract_section_is_required(self):
        for field in self.schema["required"]:
            with self.subTest(field=field):
                changed = copy.deepcopy(self.instance)
                del changed[field]
                self.assertTrue(self.validate(changed))

    def test_baseline_requires_merge_base_publication_and_tags(self):
        for field in ("merge_base", "publication_state", "tags_at_head"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.instance)
                del changed["baseline"][field]
                self.assertTrue(self.validate(changed))

    def test_validation_result_requires_summary_hash_contract(self):
        changed = copy.deepcopy(self.instance)
        result = changed["validation_runs"][0]["results"][0]
        del result["result_summary_sha256"]
        result["command"] = "python scripts/check.py"
        result["output_sha256"] = "0" * 64
        self.assertTrue(self.validate(changed))

    def test_local_and_pull_request_context_order_is_required(self):
        changed = copy.deepcopy(self.instance)
        changed["validation_runs"].reverse()
        self.assertTrue(self.validate(changed))

    def test_criterion_gate_and_deferred_identifiers_are_exact(self):
        mutations = (
            ("deliverables", 0, "id", "m0-d9"),
            ("exit_criteria", 0, "id", "m0-e9"),
            ("safety_criteria", 0, "id", "m0-s9"),
            ("foundation_gates", 0, "id", "9.9"),
            ("deferred_work", 0, "milestone", "M10"),
        )
        for collection, index, field, value in mutations:
            with self.subTest(collection=collection):
                changed = copy.deepcopy(self.instance)
                changed[collection][index][field] = value
                self.assertTrue(self.validate(changed))

    def test_promise_aggregate_and_debt_ownership_are_required(self):
        changed = copy.deepcopy(self.instance)
        del changed["promise_source_evidence"]["reviewed_surface_aggregate_sha256"]
        changed["debt_ownership_metrics"]["unowned_open_count"] = 1
        self.assertTrue(self.validate(changed))

    def test_diff_budget_and_protected_empty_result_are_enforced(self):
        changed = copy.deepcopy(self.instance)
        changed["diff_review"]["files_deleted"] = 1
        changed["diff_review"]["change_budget_exceptions"] = []
        changed["protected_path_diff"]["changed_paths"] = ["protected.md"]
        changed["protected_path_diff"]["empty_output"] = False
        self.assertTrue(self.validate(changed))

    def test_post_commit_and_remote_action_fields_are_external_only(self):
        changed = copy.deepcopy(self.instance)
        changed["local_commit_sha"] = "0" * 40
        changed["remote_actions"] = {"push": "not_performed"}
        self.assertTrue(self.validate(changed))


class SchemaAndVersionTests(unittest.TestCase):
    def test_all_m0_schemas_are_meta_schema_valid(self):
        for schema_path in m0.INSTANCE_SCHEMAS.values():
            with self.subTest(schema_path=schema_path):
                schema = m0.load_json(ROOT / schema_path)
                self.assertEqual([], m0.schema_validation_errors({}, schema, schema_path)[:0])
                m0.Draft202012Validator.check_schema(schema)

    def test_ordinary_classification_assignment_does_not_require_mirror_fields(self):
        schema = m0.load_json(ROOT / "data/schemas/artifact_classification_manifest_schema.json")
        assignment_schema = {
            "$schema": schema["$schema"],
            "$defs": schema["$defs"],
            "$ref": "#/$defs/common_assignment",
        }
        assignment = {
            "classification": "informative",
            "owner_role": "Repository maintainers",
            "governing_source": "README.md",
            "rationale": "This is an ordinary informative assignment.",
        }
        self.assertEqual(
            [],
            m0.schema_validation_errors(assignment, assignment_schema, "ordinary assignment"),
        )

    def test_version_mirror_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_text(root, "VERSION", "2.0.23\n")
            write_text(root, "version.txt", "9.9.9\n")
            roadmap = roadmap_fixture()
            _version, errors = m0.canonical_version_errors(root, roadmap)
            self.assertTrue(any("version.txt" in error for error in errors))


class WikiSyncVersionAuthorityTests(unittest.TestCase):
    def validate(self, workflow: str) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_text(root, m0.WIKI_SYNC_WORKFLOW_PATH, workflow)
            errors: list[str] = []
            m0.validate_wiki_sync_version_authority(root, errors)
            return errors

    def test_active_wiki_sync_reads_canonical_version(self):
        workflow = """name: Wiki Sync
on:
  push:
    paths:
      - 'VERSION'
      - 'version.txt'
jobs:
  sync:
    steps:
      - name: Read version
        run: echo "version=$(cat main-repo/VERSION)" >> "$GITHUB_OUTPUT"
"""
        self.assertEqual([], self.validate(workflow))

    def test_active_wiki_sync_legacy_version_value_read_is_rejected(self):
        workflow = """name: Wiki Sync
jobs:
  sync:
    steps:
      - name: Read version
        run: echo "version=$(cat main-repo/version.txt)" >> "$GITHUB_OUTPUT"
"""
        errors = self.validate(workflow)
        self.assertTrue(any("do not read canonical" in error for error in errors))
        self.assertTrue(any("version.txt as a value authority" in error for error in errors))

    def test_active_wiki_sync_version_path_is_case_sensitive(self):
        workflow = """name: Wiki Sync
jobs:
  sync:
    steps:
      - name: Read version
        run: echo "version=$(cat main-repo/version)" >> "$GITHUB_OUTPUT"
"""
        errors = self.validate(workflow)
        self.assertTrue(any("do not read canonical" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
