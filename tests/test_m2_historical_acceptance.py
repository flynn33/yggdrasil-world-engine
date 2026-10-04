"""Synthetic temporary Git snapshots test historical M2 evidence without live edits."""

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("m2_historical_under_test", ROOT / "scripts/check_m2_historical_acceptance.py")
historical = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(historical)


class HistoricalAcceptanceTests(unittest.TestCase):
    """Every recorded pass in this suite belongs to a synthetic external repository."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ywe-m2-historical-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repository"
        self.root.mkdir()
        historical.git(self.root, "init", "-q")
        historical.git(self.root, "config", "user.name", "Synthetic Fixture")
        historical.git(self.root, "config", "user.email", "fixture@invalid.test")
        historical.git(self.root, "config", "core.autocrlf", "false")
        self.write(historical.SCHEMA_PATH, (ROOT / historical.SCHEMA_PATH).read_bytes())
        self.write(historical.REPORT_SCHEMA, (ROOT / historical.REPORT_SCHEMA).read_bytes())
        self.roadmap = {"current_milestone": "M2", "milestones": [{"id": "M2", "status": "in_progress", "acceptance_evidence": [],
                           "exit_criteria": list(historical.EXIT_CRITERIA), "deliverables": list(historical.DELIVERABLES)}]}
        self.write_json(historical.ROADMAP_PATH, self.roadmap)
        self.checks = {"checks": [{"id": "synthetic_blocking", "blocking": True, "contexts": ["always"]},
                                  {"id": "synthetic_advisory", "blocking": False, "contexts": ["local"]}]}
        self.write_json(historical.CHECK_CATALOG, self.checks)
        self.write(historical.REQUIREMENTS_PATH, b"jsonschema==4.25.1\nPyYAML==6.0.3\n")
        self.pending = {"schema_ref": historical.SCHEMA_PATH, "artifact_type": "ywe_m2_acceptance_evidence",
                        "artifact_version": "1.0.0", "milestone_id": "M2", "outcome": "pending"}
        self.write_json(historical.EVIDENCE_PATH, self.pending)
        self.write(historical.DOCUMENT_PATH, b"Synthetic temporary fixture. M2: PENDING\n")
        self.operations = [{"operation_id": f"synthetic.{category}", "path": "synthetic-cases.json", "instance_pointer": f"/{category}/case",
                            "category": category, "validation_scope": "schema_validation_operation", "result": "pass",
                            "stages": [{"stage": "synthetic_execution", "result": "accept", "errors": []}]}
                           for category in ("recovery", "replay", "migration")]
        self.methods = [{"method": method, "status": "pass", "execution_complete": True,
                         "executed_case_count": 3 if method == "mutation" else 1,
                         "successful_case_count": 3 if method == "mutation" else 1, "errors": [],
                         "evidence": {"cases": [{"case_id": f"synthetic.{method}.{index}", "result": "pass", "killed": True}
                                               for index in range(3 if method == "mutation" else 1)]}}
                        for method in historical.METHODS]
        self.write_json("synthetic-operations.json", {"results": self.operations})
        self.write_json("synthetic-methods.json", {"results": self.methods})
        # The real worker imports these explicitly synthetic implementation modules.
        self.write("scripts/check_m2_validation_operations.py", b"import json\ndef validation_errors(root):\n    return [], json.loads((root / 'synthetic-operations.json').read_text())['results']\n")
        self.write("scripts/check_m2_validation_methods.py", b"import json\ndef validation_errors(root):\n    return [], json.loads((root / 'synthetic-methods.json').read_text())['results']\n")
        acceptance = """import hashlib, json, subprocess
def build_report(root, repository_report, *, verify_historical=True):
    if verify_historical:
        raise AssertionError('Historical replay must use formation mode')
    result = json.loads((root / 'synthetic-formation-template.json').read_text())
    result['revision'] = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    data = (root / 'data/governance/specification_roadmap.json').read_bytes().decode('utf-8-sig').replace('\\r\\n', '\\n').replace('\\r', '\\n').encode('utf-8')
    result['roadmap_sha256'] = hashlib.sha256(data).hexdigest()
    return result
"""
        self.write("scripts/check_m2_acceptance.py", acceptance.encode("utf-8"))
        self.formation = {"artifact_type": "ywe_m2_readiness_report", "artifact_version": "1.0.0", "ready": False,
                          "criteria": [], "deliverables": [], "errors": []}
        for group, prefix, statements in (("criteria", "C", historical.EXIT_CRITERIA), ("deliverables", "D", historical.DELIVERABLES)):
            self.formation[group] = [{"id": f"M2-{prefix}{index + 1}", "statement": statement,
                                      "status": "unverified" if prefix == "D" and index == 7 else "pass",
                                      "errors": ["Durable M2 acceptance evidence is not recorded"] if prefix == "D" and index == 7 else [],
                                      "evidence": {"synthetic": True}}
                                     for index, statement in enumerate(statements)]
        self.write_json("synthetic-formation-template.json", self.formation)
        self.base = self.commit("Synthetic implementation fixture")
        self.formation.update(revision=self.base, roadmap_sha256=historical.text_hash((self.root / historical.ROADMAP_PATH).read_bytes()))
        files, _ = historical.snapshot(self.root, self.base)
        self.report = {"artifact_type": "ywe_repository_validation_report", "artifact_version": "1.0.0", "execution_complete": True,
                       "revision": self.base, "context": "local", "check_catalog_sha256": historical.text_hash(files[historical.CHECK_CATALOG]),
                       "selection": {"groups": [], "check_ids": []}, "offline": {"requested": True, "git_allow_protocol": "file"},
                       "dirty_before": [], "dirty_after": [], "tool_versions": {"python": "3.12.10", "jsonschema": "4.25.1", "PyYAML": "6.0.3", "referencing": "0.36.2"},
                       "results": [{"check_id": item["id"], "blocking": item["blocking"], "return_code": 0} for item in self.checks["checks"]],
                       "summary": {"passed": 2, "blocking_failures": 0, "advisories": 0}}
        self.record = {**self.pending, "outcome": "pass", "implementation_revision": self.base,
                       "source_state": historical.source_state(files),
                       "check_catalog": {"path": historical.CHECK_CATALOG, "hash_algorithm": historical.TEXT_HASH_ALGORITHM, "sha256": self.report["check_catalog_sha256"]},
                       "validation_environment": {"requirements_ref": historical.REQUIREMENTS_PATH, "requirements_sha256": historical.text_hash(files[historical.REQUIREMENTS_PATH]),
                                                  "pinned_tool_versions": deepcopy(self.report["tool_versions"])},
                       "repository_report": deepcopy(self.report), "repository_report_sha256": historical.value_hash(self.report),
                       "formation_report": deepcopy(self.formation), "validation_operations": deepcopy(self.operations), "validation_methods": deepcopy(self.methods),
                       "acceptance_judgments": []}
        for group in ("criteria", "deliverables"):
            for index, item in enumerate(self.formation[group]):
                pending = item["id"] == "M2-D8"
                self.record["acceptance_judgments"].append({"id": item["id"], "statement": item["statement"], "status": "pass",
                    "basis": "immutable_introduction" if pending else "formation_report",
                    "evidence_pointer": "/source_state" if pending else f"/formation_report/{group}/{index}"})

    def write(self, path, content):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)

    def write_json(self, path, value):
        self.write(path, (json.dumps(value, indent=2) + "\n").encode("utf-8"))

    def commit(self, message):
        historical.git(self.root, "add", "--all")
        historical.git(self.root, "commit", "-q", "-m", message)
        return historical.git(self.root, "rev-parse", "HEAD").decode("ascii").strip()

    def introduce(self, mutate=None):
        record = deepcopy(self.record)
        if mutate:
            mutate(record)
        self.write_json(historical.EVIDENCE_PATH, record)
        markers = ["Synthetic temporary fixture. M2: ACCEPTED", record["implementation_revision"], record["source_state"]["digest"]]
        markers += [item["id"] for item in record["acceptance_judgments"]]
        self.write(historical.DOCUMENT_PATH, ("\n".join(markers) + "\n").encode("utf-8"))
        return self.commit("Synthetic acceptance introduction")

    def replayed(self):
        return {"formation_report": deepcopy(self.formation), "validation_operations": {"errors": [], "results": deepcopy(self.operations)},
                "validation_methods": {"errors": [], "results": deepcopy(self.methods)}}

    def check(self, replay=True):
        if replay:
            with patch.object(historical, "replay_snapshot", return_value=self.replayed()):
                return historical.validation_errors(self.root)
        return historical.validation_errors(self.root)

    def assert_invalid(self, substring):
        errors, metadata = self.check()
        self.assertTrue(errors)
        self.assertEqual("invalid", metadata["outcome"])
        self.assertIn(substring.lower(), "\n".join(errors).lower())

    def test_pending_record_passes_without_accepting_milestone(self):
        errors, metadata = self.check()
        self.assertEqual([], errors)
        self.assertEqual("pending", metadata["outcome"])

    def test_absent_record_is_only_pending_while_active(self):
        (self.root / historical.EVIDENCE_PATH).unlink()
        self.assertEqual("pending", self.check()[1]["outcome"])
        self.roadmap["milestones"][0]["status"] = "complete"
        self.write_json(historical.ROADMAP_PATH, self.roadmap)
        self.assert_invalid("completed or promoted")

    def test_pending_cannot_promote_m3(self):
        self.roadmap["current_milestone"] = "M3"
        self.write_json(historical.ROADMAP_PATH, self.roadmap)
        self.assert_invalid("completed or promoted")

    def test_uncommitted_passing_record_is_not_acceptance(self):
        self.write_json(historical.EVIDENCE_PATH, self.record)
        self.assert_invalid("must be committed")

    def test_actual_file_only_clone_worker_verifies_synthetic_introduction(self):
        introduction = self.introduce()
        errors, metadata = self.check(replay=False)
        self.assertEqual([], errors)
        self.assertEqual("pass", metadata["outcome"])
        self.assertEqual(introduction, metadata["introduction_revision"])
        self.assertEqual(14, len(metadata["discharged_obligations"]))

    def test_completed_m2_requires_exact_pair(self):
        self.introduce()
        self.roadmap.update(current_milestone="M3")
        self.roadmap["milestones"][0].update(status="complete", acceptance_evidence=[])
        self.write_json(historical.ROADMAP_PATH, self.roadmap)
        self.assert_invalid("exact immutable")
        self.roadmap["milestones"][0]["acceptance_evidence"] = list(historical.EVIDENCE_PATHS)
        self.write_json(historical.ROADMAP_PATH, self.roadmap)
        self.assertEqual([], self.check()[0])

    def test_future_catalog_change_does_not_reinterpret_historical_execution(self):
        self.introduce()
        self.checks["checks"].append({"id": "future_check", "blocking": True, "contexts": ["always"]})
        self.write_json(historical.CHECK_CATALOG, self.checks)
        self.write("future.txt", b"Legitimate later source change\n")
        self.commit("Synthetic future development")
        self.assertEqual([], self.check(replay=False)[0])

    def test_current_record_tampering_fails(self):
        self.introduce()
        self.write_json(historical.EVIDENCE_PATH, self.pending)
        self.assert_invalid("differs from its first")

    def test_committed_edit_then_restore_still_fails_immutability(self):
        self.introduce()
        original = (self.root / historical.DOCUMENT_PATH).read_bytes()
        self.write(historical.DOCUMENT_PATH, original + b"Tampering\n")
        self.commit("Synthetic evidence tampering")
        self.write(historical.DOCUMENT_PATH, original)
        self.commit("Synthetic restoration")
        self.assert_invalid("was changed or deleted")

    def test_merge_side_branch_tamper_then_restore_cannot_hide_history(self):
        self.introduce()
        original_branch = historical.git(self.root, "symbolic-ref", "--short", "HEAD").decode("ascii").strip()
        originals = {path: (self.root / path).read_bytes() for path in historical.EVIDENCE_PATHS}
        historical.git(self.root, "checkout", "-q", "-b", "synthetic-tamper")
        for path, data in originals.items():
            self.write(path, data + b"\n ")
        self.commit("Synthetic side branch evidence tamper")
        for path, data in originals.items():
            self.write(path, data)
        self.commit("Synthetic side branch restoration")
        historical.git(self.root, "checkout", "-q", original_branch)
        historical.git(self.root, "merge", "-q", "--no-ff", "-m", "Synthetic evidence merge", "synthetic-tamper")
        self.assert_invalid("was changed or deleted")

    def test_deleted_evidence_cannot_hide_accepted_history(self):
        self.introduce()
        (self.root / historical.EVIDENCE_PATH).unlink()
        self.commit("Synthetic deletion")
        self.assert_invalid("missing")

    def test_source_change_between_test_and_introduction_fails(self):
        self.write("unreviewed.txt", b"Unreviewed source\n")
        self.introduce()
        self.assert_invalid("source states differ")

    def test_fixed_exclusions_cannot_expand(self):
        self.introduce(lambda record: record["source_state"]["digest_exclusions"].append("scripts/check_m2_acceptance.py"))
        self.assert_invalid("historical m2 evidence")

    def test_wrong_source_digest_fails(self):
        self.introduce(lambda record: record["source_state"].update(digest="0" * 64))
        self.assert_invalid("source states differ")

    def test_unknown_implementation_commit_fails(self):
        self.introduce(lambda record: record.update(implementation_revision="f" * 40))
        self.assert_invalid("git rev-parse")

    def test_recorded_catalog_hash_is_source_bound(self):
        self.introduce(lambda record: record["check_catalog"].update(sha256="0" * 64))
        self.assert_invalid("catalog identity")

    def test_incomplete_or_filtered_or_nonoffline_reports_fail(self):
        changes = [{"execution_complete": False}, {"context": "pull_request"}, {"selection": {"groups": ["m2"], "check_ids": []}},
                   {"offline": {"requested": False, "git_allow_protocol": None}}, {"dirty_after": ["?? report.json"]}]
        files, _ = historical.snapshot(self.root, self.base)
        for change in changes:
            with self.subTest(change=change):
                record = deepcopy(self.record)
                record["repository_report"].update(change)
                record["repository_report_sha256"] = historical.value_hash(record["repository_report"])
                self.assertIn("complete, clean, unfiltered", "\n".join(historical.report_errors(record, files)))

    def test_missing_advisory_failure_or_wrong_severity_fails(self):
        files, _ = historical.snapshot(self.root, self.base)
        for action in (lambda rows: rows.pop(), lambda rows: rows[1].update(return_code=1), lambda rows: rows[1].update(blocking=True)):
            with self.subTest(action=action):
                record = deepcopy(self.record)
                action(record["repository_report"]["results"])
                self.assertIn("every applicable catalog check", "\n".join(historical.report_errors(record, files)))

    def test_report_hash_and_exact_pins_are_checked(self):
        files, _ = historical.snapshot(self.root, self.base)
        record = deepcopy(self.record)
        record["repository_report_sha256"] = "0" * 64
        self.assertIn("content hash differs", "\n".join(historical.report_errors(record, files)))
        record = deepcopy(self.record)
        record["repository_report"]["tool_versions"]["jsonschema"] = "4.0.0"
        record["validation_environment"]["pinned_tool_versions"]["jsonschema"] = "4.0.0"
        self.assertIn("exact direct dependency pins", "\n".join(historical.report_errors(record, files)))

    def test_self_reported_d8_pass_is_not_formation(self):
        self.introduce(lambda record: record["formation_report"]["deliverables"][7].update(status="pass", errors=[]))
        self.assert_invalid("pending d8")

    def test_all_fourteen_judgments_require_exact_pointer_basis(self):
        self.introduce(lambda record: record["acceptance_judgments"][13].update(basis="formation_report", evidence_pointer="/formation_report/deliverables/7"))
        self.assert_invalid("fourteen exact judgments")

    def test_missing_or_zero_method_cases_are_not_execution(self):
        files, _ = historical.snapshot(self.root, self.base)
        for action in (lambda record: record["validation_methods"][0].update(executed_case_count=0, successful_case_count=0),
                       lambda record: record["validation_methods"][0]["evidence"].update(cases=[]),
                       lambda record: record["validation_methods"][0].update(execution_complete=False),
                       lambda record: record["validation_methods"][0].update(executed_case_count=True)):
            with self.subTest(action=action):
                record = deepcopy(self.record)
                action(record)
                self.assertIn("concrete passing execution", "\n".join(historical.formation_errors(record, files)))

    def test_surviving_mutant_is_not_passing_evidence(self):
        self.introduce(lambda record: record["validation_methods"][7]["evidence"]["cases"][0].update(killed=False))
        self.assert_invalid("actually killed")

    def test_missing_lifecycle_category_fails(self):
        self.introduce(lambda record: record["validation_operations"][2].update(category="replay"))
        self.assert_invalid("recovery, replay, and migration")

    def test_exact_method_case_replay_rejects_fabricated_details(self):
        self.introduce(lambda record: record["validation_methods"][0]["evidence"]["cases"][0].update(case_id="fabricated"))
        self.assert_invalid("validation_methods differs")

    def test_exact_lifecycle_replay_rejects_fabricated_details(self):
        self.introduce(lambda record: record["validation_operations"][0]["stages"][0].update(stage="fabricated"))
        self.assert_invalid("validation_operations differs")

    def test_formation_replay_rejects_fabricated_obligation_evidence(self):
        self.introduce(lambda record: record["formation_report"]["criteria"][0]["evidence"].update(normative_schema_count=999999))
        self.assert_invalid("obligation replay")

    def test_failed_replay_is_not_acceptance(self):
        self.introduce()
        with patch.object(historical, "replay_snapshot", side_effect=ValueError("synthetic replay failed")):
            errors, metadata = historical.validation_errors(self.root)
        self.assertIn("synthetic replay failed", "\n".join(errors))
        self.assertEqual("invalid", metadata["outcome"])

    def test_snapshot_does_not_honor_export_ignore_as_exclusion(self):
        self.write("hidden.txt", b"Must be source-bound\n")
        self.write(".gitattributes", b"hidden.txt export-ignore\n")
        revision = self.commit("Synthetic export attributes")
        files, _ = historical.snapshot(self.root, revision)
        self.assertIn("hidden.txt", files)

    def test_malformed_nested_evidence_returns_failure_instead_of_crashing(self):
        self.introduce(lambda record: record["validation_methods"][0]["evidence"].update(cases=[1]))
        self.assert_invalid("unable to verify")

    def test_later_tracked_file_mode_change_does_not_invalidate_history(self):
        self.introduce()
        # Source mode is part of the introduction snapshot, even when text hashes match.
        historical.git(self.root, "update-index", "--chmod=+x", "scripts/check_m2_acceptance.py")
        historical.git(self.root, "commit", "-q", "-m", "Synthetic later mode change")
        # Later development is legitimate; introduction changes are tested independently.
        self.assertEqual([], self.check()[0])
        files, modes = historical.snapshot(self.root, self.base)
        self.assertEqual("100644", modes["scripts/check_m2_acceptance.py"])
        self.assertEqual(historical.source_state(files), self.record["source_state"])

    def test_record_identity_is_not_delegated_to_a_weakened_portable_schema(self):
        self.write_json(historical.SCHEMA_PATH, {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": historical.SCHEMA_ID,
                                               "x-ywe-requirement-id": "YWE-REQ-0037", "type": "object"})
        weakened_revision = self.commit("Synthetic weakened format")
        files, _ = historical.snapshot(self.root, weakened_revision)
        record = deepcopy(self.record)
        record.update(artifact_type="unrelated", implementation_revision=weakened_revision, source_state=historical.source_state(files))
        self.write_json(historical.EVIDENCE_PATH, record)
        self.write(historical.DOCUMENT_PATH, b"Synthetic fixture. M2: ACCEPTED\n")
        self.commit("Synthetic invalid identity introduction")
        self.assert_invalid("exact record identity")

    def test_json_duplicate_and_nonfinite_values_reject(self):
        for text in (b'{"outcome":"pending","outcome":"pass"}', b'{"value":NaN}', b'{"value":Infinity}'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    historical.load_json(text)

    def test_typed_json_comparison_does_not_accept_boolean_integer_substitution(self):
        self.assertFalse(historical.json_equal({"pass": True}, {"pass": 1}))
        self.assertFalse(historical.json_equal([False], [0]))


if __name__ == "__main__":
    unittest.main()
