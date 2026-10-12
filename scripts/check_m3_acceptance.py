#!/usr/bin/env python3
"""Evaluate complete M3 definitions and already executed source-bound case evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path, PureWindowsPath

from jsonschema import Draft202012Validator

import check_m0_truthful_baseline as baseline
import check_m2_historical_acceptance as historical
from check_m2_acceptance import repository_evidence_errors
from run_validation_unit_tests import MAPPING_PATH, normalized_sha256, source_receipt

ROADMAP = "data/governance/specification_roadmap.json"
CHECKS = "data/validation/repository_checks.json"
CANONICAL = "core/ash_pattern_engine/canonical"
INVARIANTS = CANONICAL + "/verification/invariant-spec.md"
CATEGORIES = CANONICAL + "/verification/conformance-categories.md"
DELIVERABLES = (
    "Final Cosmology, Realm, ASH Pattern, Narrative, Perception, and orchestration contracts.",
    "Context-aware state classification and complete diagnostics.",
    "Recovery, normalization, fallback selection, containment, and safe-halt state machines.",
    "Topology generation, role assignment, axiom evaluation, complete generation planning, and artifact-emitter traceability.",
    "Deterministic seed, selection, tie-break, numeric, canonical serialization, bias merge, decay, normalization, and conflict semantics.",
    "Standard platform-neutral module lifecycle and interface contract.",
    "Complete core failure, no-op, diagnostic, and resource-bound behavior.",
)
EXIT_CRITERIA = (
    "All 28 canonical invariants have executable tests.", "All five conformance categories pass.",
    "All states and transitions have exhaustive reference coverage.",
    "Identical input produces byte-stable canonical output.", "No core placeholder remains.",
)
AUDITED = "AUDITED_EXECUTABLE_CANDIDATE_NOT_EXECUTION_ACCEPTANCE"
EVIDENCE_PATH = "data/governance/m3_acceptance_evidence.json"
DOCUMENT_PATH = "docs/project/M3_CORE_CONTRACTS_ACCEPTANCE.md"
EVIDENCE_PATHS = (EVIDENCE_PATH, DOCUMENT_PATH)
HISTORICAL_SCHEMA = "data/schemas/m3_historical_acceptance_evidence_schema.json"
ARCHIVE_PATHS = tuple("data/governance/evidence/m3/" + name for name in
                      ("repository-report.json", "unit-cases.json", "unit-transcript.log", "acceptance-report.json"))
IMMUTABLE_PATHS = EVIDENCE_PATHS + ARCHIVE_PATHS


def text_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_definitions(root):
    source = (root / INVARIANTS).read_text(encoding="utf-8")
    if text_hash(source) != "2b7dbd52b539810b3f957ed23bcbcd7fffd068b3f01ea43f24b51a0e8f98866b":
        raise ValueError("Canonical invariant source differs from the adopted 28-invariant contract")
    category_source = (root / CATEGORIES).read_text(encoding="utf-8")
    if text_hash(category_source) != "979f287e3521a750997814d1bc3a85893433ce885cde6669c919511656799bf2":
        raise ValueError("Canonical category source differs from the adopted five-category contract")
    families = {}
    for number, section in re.findall(r"## Category ([1-5]):([^#]*(?:(?!\n## Category)[\s\S])*?)(?=\n## Category|\n## Category coverage|\Z)", category_source):
        for family in re.findall(r"^- `INV-([A-Z]+)-\d{3}`", section, re.M):
            if family in families:
                raise ValueError("Canonical category family is ambiguous")
            families[family] = int(number)
    rows = []
    for identifier, section in re.findall(r"^### (INV-[A-Z]+-\d{3})[^\n]*\n([\s\S]*?)(?=^### |\Z)", source, re.M):
        values = {}
        for field, marker in (("canonical_statement", "Statement"), ("canonical_test_criterion", "Test criterion"), ("canonical_sources", "Source")):
            matches = re.findall(r"^\*\*" + marker + r"\*\*: (.+)$", section, re.M)
            if len(matches) != 1:
                raise ValueError("Canonical invariant has missing or ambiguous " + marker)
            values[field] = matches[0]
        rows.append({"invariant_id": identifier, "category": families[identifier.split("-")[1]], **values})
    if len(rows) != 28 or len({row["invariant_id"] for row in rows}) != 28:
        raise ValueError("Canonical invariant set must contain exactly 28 unique rows")
    if dict(Counter(str(row["category"]) for row in rows)) != {"1": 9, "2": 5, "3": 5, "4": 4, "5": 5}:
        raise ValueError("Canonical category membership is incomplete")
    return rows


def expected_obligations(root):
    roadmap = baseline.load_json(root / ROADMAP)
    matches = [(index, item) for index, item in enumerate(roadmap["milestones"]) if item["id"] == "M3"]
    if len(matches) != 1:
        raise ValueError("Roadmap must contain exactly one M3 milestone")
    index, milestone = matches[0]
    if milestone["deliverables"] != list(DELIVERABLES) or milestone["exit_criteria"] != list(EXIT_CRITERIA):
        raise ValueError("Roadmap M3 obligations differ from the exact adopted ordered contract")
    modules = []
    for path in sorted((root / CANONICAL / "interfaces/contracts").glob("*.md")):
        modules.append({"id": "M3-MODULE-" + path.stem.upper(), "text": path.read_text(encoding="utf-8").splitlines()[0].removeprefix("# "),
                        "source_path": path.relative_to(root).as_posix(), "normalized_sha256": normalized_sha256(path), "locator": ""})
    if len(modules) != 9:
        raise ValueError("All nine canonical per-module contracts must be present")
    definitions = {"module_contracts": modules}
    for field, values, prefix in (("deliverables", DELIVERABLES, "D"), ("exit_criteria", EXIT_CRITERIA, "C")):
        definitions["roadmap_" + field] = [{"id": "M3-" + prefix + str(i + 1), "text": text, "source_path": ROADMAP,
            "normalized_sha256": text_hash(text), "locator": f"/milestones/{index}/{field}/{i}"} for i, text in enumerate(values)]
    return definitions


def mapped_source_errors(root, row):
    errors = []
    if not isinstance(row, dict):
        return ["Mapping row must be an object"]
    if row.get("status") != AUDITED:
        errors.append("Mapping has no completed substantive source-body audit")
    selectors = row.get("candidate_tests")
    sources = row.get("actual_test_source_receipts")
    if (not isinstance(selectors, list) or not 1 <= len(selectors) <= 128
            or any(not isinstance(value, str) or not value for value in selectors)
            or len(selectors) != len(set(selectors))):
        return errors + ["Mapping needs unique bounded actual test selectors"]
    if not isinstance(sources, list) or len(sources) != len(selectors):
        return errors + ["Every mapped selector needs an exact source receipt"]
    for selector, receipt in zip(selectors, sources):
        try:
            if (not isinstance(receipt, dict)
                    or any(not isinstance(receipt.get(key), str) for key in ("path", "class", "method"))):
                raise ValueError("Source receipt needs an object with exact string selectors")
            actual = source_receipt(root, receipt["path"], receipt["class"], receipt["method"])
            expected = receipt["path"].removesuffix(".py").replace("/", ".") + "." + receipt["class"] + "." + receipt["method"]
            if selector != expected or not receipt["path"].startswith("tests/") or actual != receipt:
                errors.append("Mapped selector/source body differs: " + str(selector))
        except (KeyError, OSError, TypeError, ValueError, SyntaxError) as exc:
            errors.append("Mapped source unavailable: " + str(selector) + ": " + str(exc))
    return errors


def definition_errors(root, mapping):
    errors = []
    if not isinstance(mapping, dict):
        return ["Mapping must be an object"]
    canonical = canonical_definitions(root)
    rows = mapping.get("required_invariants", [])
    if not isinstance(rows, list):
        rows = []
    if any(not isinstance(row, dict) for row in rows) or [row.get("invariant_id") for row in rows if isinstance(row, dict)] != [row["invariant_id"] for row in canonical]:
        errors.append("Mapping must preserve all 28 canonical IDs exactly in canonical order")
    for i, expected in enumerate(canonical):
        if i >= len(rows) or not isinstance(rows[i], dict):
            continue
        if any(rows[i].get(key) != value for key, value in expected.items()):
            errors.append("Canonical invariant statement, criterion, source or category differs: " + expected["invariant_id"])
        errors.extend(expected["invariant_id"] + ": " + error for error in mapped_source_errors(root, rows[i]))
    if mapping.get("category_sizes") != {"1": 9, "2": 5, "3": 5, "4": 4, "5": 5}:
        errors.append("Mapping must retain every exact canonical category size")
    for field, expected in expected_obligations(root).items():
        actual = mapping.get(field, [])
        if (not isinstance(actual, list) or any(not isinstance(row, dict) for row in actual)
                or [row.get("id") for row in actual if isinstance(row, dict)] != [row["id"] for row in expected]):
            errors.append("Mapping missing, duplicate or reordered obligations: " + field)
            continue
        for row, required in zip(actual, expected):
            if any(row.get(key) != value for key, value in required.items()):
                errors.append("Obligation definition/source differs: " + required["id"])
            errors.extend(required["id"] + ": " + error for error in mapped_source_errors(root, row))
    return errors


def executed_evidence_errors(root, repository_report, conformance_report, mapping, archived_unit_evidence=None):
    checks = baseline.load_json(root / CHECKS)
    errors = [error.replace("M2 checkout acceptance", "M3 checkout acceptance")
              for error in repository_evidence_errors(root, repository_report, checks)]
    if conformance_report is None:
        return errors + ["No actual executed case evidence was supplied"]
    schema = baseline.load_json(root / "data/schemas/unit_case_evidence_schema.json")
    shape = list(Draft202012Validator(schema).iter_errors(conformance_report))
    if shape:
        return errors + ["Case evidence shape: " + error.message for error in shape]
    cases = conformance_report["cases"]
    ids = [row["runtime_id"] for row in cases]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate runtime case identities cannot establish conformance")
    if conformance_report["discovery_order_sha256"] != text_hash(json.dumps(ids, separators=(",", ":"))):
        errors.append("Cases differ from their actual discovered order or include missing cases")
    digest = normalized_sha256(root / MAPPING_PATH)
    if conformance_report["mapping_before_sha256"] != digest or conformance_report["mapping_after_sha256"] != digest:
        errors.append("Executed evidence has a stale or changed mapping")
    if not conformance_report["execution_complete"] or not conformance_report["discovery_complete"]:
        errors.append("Child discovery/execution evidence is incomplete")
    if conformance_report["revision"] != baseline.checked_git_output(root, ["rev-parse", "HEAD"]).decode().strip():
        errors.append("Case execution targets a different revision")
    if conformance_report["dirty_before"] or conformance_report["dirty_after"]:
        errors.append("Case evidence executed in a dirty checkout")
    if conformance_report["offline_git_allow_protocol"] != "file":
        errors.append("Case execution did not deny remote Git protocols")
    if conformance_report["argv"] != ["discover", "-s", "tests", "-p", "test_*.py"]:
        errors.append("Case evidence is filtered or differs from ordinary discovery")
    if conformance_report["fixture_errors"] or conformance_report["source_integrity_errors"]:
        errors.append("Case evidence contains fixture or source-integrity errors")
    summary = conformance_report["summary"]
    if (summary is None or summary["tests_run"] != sum(row["starts"] for row in cases)
            or summary["successful"] is not True or any(summary[key] != 0 for key in ("failures", "errors", "unexpected_successes"))
            or conformance_report["return_code"] != 0):
        errors.append("Case execution summary does not establish a passing complete run")
    if any(row["starts"] != 1 or row["stops"] != 1 for row in cases):
        errors.append("Discovered cases have missing or duplicate actual start/stop callbacks")
    for row in cases:
        before = row["source_before"]
        if before is not None:
            try:
                current = source_receipt(root, before["path"], before["class"], before["method"])
                if before != current or row["source_after"] != current:
                    errors.append("Executed test source/body is stale: " + row["runtime_id"])
            except (OSError, TypeError, ValueError, SyntaxError) as exc:
                errors.append("Executed source readback failed: " + row["runtime_id"] + ": " + str(exc))
    results = repository_report.get("results", []) if isinstance(repository_report, dict) else []
    unit_rows = [row for row in results if isinstance(row, dict) and row.get("check_id") == "validation_unit_tests"] if isinstance(results, list) else []
    parent = unit_rows[0].get("unit_evidence") if len(unit_rows) == 1 else None
    if not isinstance(parent, dict) or parent.get("execution_complete") is not True:
        return errors + ["Parent closed unit transcript/receipt evidence is missing or incomplete"]
    try:
        receipt = Path(parent["receipt_path"])
        transcript = Path(parent["transcript_path"])
        if archived_unit_evidence is None:
            if not receipt.is_absolute() or not transcript.is_absolute():
                raise ValueError("Parent evidence paths must be absolute")
            if receipt.stat().st_size > 16_777_216 or transcript.stat().st_size > 67_108_864:
                raise ValueError("Parent evidence exceeds bounded input size")
            raw, log = receipt.read_bytes(), transcript.read_bytes()
        else:
            if (not isinstance(archived_unit_evidence, tuple) or len(archived_unit_evidence) != 2
                    or any(type(value) is not bytes for value in archived_unit_evidence)):
                raise ValueError("Historical evidence needs exact receipt/transcript byte archives")
            if any(not (Path(value).is_absolute() or PureWindowsPath(value).is_absolute())
                   for value in (parent["receipt_path"], parent["transcript_path"])):
                raise ValueError("Captured historical parent labels must be absolute paths")
            raw, log = archived_unit_evidence
        if len(raw) > 16_777_216 or len(log) > 67_108_864:
            raise ValueError("Parent evidence exceeds bounded input size")
        if hashlib.sha256(raw).hexdigest() != parent["receipt_sha256"] or hashlib.sha256(log).hexdigest() != parent["transcript_sha256"]:
            errors.append("Parent evidence bytes/hash differ")
        if historical.load_json(raw) != conformance_report:
            errors.append("Conformance input differs from the actual parent-bound child receipt")
        summaries = re.findall(rb"(?m)^Ran (\d+) tests? in ", log)
        if summary is None or not summaries or int(summaries[-1]) != summary["tests_run"]:
            errors.append("Parent full transcript lacks the matching actual runner summary")
    except (KeyError, OSError, TypeError, ValueError) as exc:
        errors.append("Parent evidence unavailable: " + str(exc))
    return errors


def case_errors(row, cases):
    errors = []
    sources = row.get("actual_test_source_receipts", [])
    if not isinstance(sources, list):
        return ["Mapped source receipts must be an array"]
    for expected in sources:
        if not isinstance(expected, dict) or any(not isinstance(expected.get(key), str) for key in ("path", "class", "method")):
            errors.append("Mapped source receipt is malformed")
            continue
        found = [case for case in cases if isinstance(case, dict) and case.get("source_before") == expected]
        if (len(found) != 1 or found[0].get("status") != "PASS" or found[0].get("starts") != 1
                or found[0].get("stops") != 1 or found[0].get("source_after") != expected
                or found[0].get("runtime_body_verified") is not True or found[0].get("source_error") is not None):
            errors.append("Mapped case absent, duplicate, stale or non-PASS: " + expected["path"] + ":" + expected["class"] + "." + expected["method"])
    return errors


def build_report(root, repository_report=None, conformance_report=None, *, archived_unit_evidence=None):
    root = Path(root).resolve()
    report = {"artifact_type": "ywe_m3_acceptance_report", "artifact_version": "1.0.0", "ready": False,
              "judgment": "NON-CONFORMANT", "revision": None, "mapping_sha256": None,
              "errors": [], "invariants": [], "categories": [], "modules": [], "deliverables": [], "criteria": [],
              "excluded_future_core_placeholders": []}
    try:
        mapping = baseline.load_json(root / MAPPING_PATH)
        if not isinstance(mapping, dict):
            report["errors"].append("Mapping must be an object")
            mapping = {}
        report["revision"] = baseline.checked_git_output(root, ["rev-parse", "HEAD"]).decode().strip()
        report["mapping_sha256"] = normalized_sha256(root / MAPPING_PATH)
        definitions = definition_errors(root, mapping)
        execution = executed_evidence_errors(root, repository_report, conformance_report, mapping, archived_unit_evidence)
        report["errors"].extend(definitions + execution)
        cases = conformance_report.get("cases", []) if isinstance(conformance_report, dict) else []
        if not isinstance(cases, list):
            cases = []
        expected_groups = {"required_invariants": canonical_definitions(root), **expected_obligations(root)}
        for field, result_field, id_field in (("required_invariants", "invariants", "invariant_id"),
                ("module_contracts", "modules", "id"), ("roadmap_deliverables", "deliverables", "id"),
                ("roadmap_exit_criteria", "criteria", "id")):
            rows = mapping.get(field, [])
            mapped = {row.get(id_field): row for row in rows if isinstance(row, dict) and isinstance(row.get(id_field), str)} if isinstance(rows, list) else {}
            for expected in expected_groups[field]:
                row = mapped.get(expected[id_field], {})
                errors = mapped_source_errors(root, row) + case_errors(row, cases)
                if definitions or execution:
                    errors.append("Joint definition and complete matching execution evidence are required")
                report[result_field].append({"id": expected[id_field], "text": expected.get("text", expected.get("canonical_statement", "")),
                    "status": "unverified" if conformance_report is None else "fail" if errors else "pass", "errors": errors})
        for category in range(1, 6):
            indices = [i for i, row in enumerate(expected_groups["required_invariants"]) if row["category"] == category]
            passed = bool(indices) and all(report["invariants"][i]["status"] == "pass" for i in indices)
            report["categories"].append({"id": category, "status": "pass" if passed else "fail"})
        scope_error_offset = len(report["errors"])
        paths = baseline.repository_candidate_paths(root, report["errors"])
        classes = baseline.effective_assignments(paths, baseline.load_json(root / "data/governance/artifact_classification_manifest.json"), "classification", report["errors"], "M3 classifications")
        scope = baseline.effective_assignments(paths, baseline.load_json(root / "data/governance/scope_partition_manifest.json"), "primary_partition", report["errors"], "M3 scope")
        for path, assignment in classes.items():
            if assignment.get("classification") != "placeholder":
                continue
            partition = scope.get(path, {})
            if partition.get("primary_partition") == "ywe_core" or assignment.get("current_milestone") == "M3":
                report["errors"].append("Accepted M3 Core placeholder remains: " + path)
            if path.startswith("core/"):
                future = assignment.get("future_milestone")
                if (partition.get("primary_partition") != "later_release_work"
                        or not isinstance(future, str) or re.fullmatch(r"M(?:[4-9]|10)", future) is None
                        or future != partition.get("future_milestone")):
                    report["errors"].append("Core placeholder lacks exact formal future exclusion: " + path)
                else:
                    report["excluded_future_core_placeholders"].append({"path": path, "milestone": assignment["future_milestone"], "debt_ref": assignment.get("debt_ref")})
        if len(report["errors"]) > scope_error_offset:
            criterion = next(row for row in report["criteria"] if row["id"] == "M3-C5")
            criterion["errors"].extend(report["errors"][scope_error_offset:])
            if conformance_report is not None:
                criterion["status"] = "fail"
        groups = ("invariants", "categories", "modules", "deliverables", "criteria")
        report["ready"] = not report["errors"] and all(report[field] and all(row["status"] == "pass" for row in report[field]) for field in groups)
        if report["ready"]:
            report["judgment"] = "CONFORMANT"
    except (KeyError, OSError, TypeError, ValueError, SyntaxError) as exc:
        report["errors"].append("M3 evidence unavailable: " + str(exc))
    return report


def source_state(files):
    included = sorted(set(files) - set(IMMUTABLE_PATHS))
    payload = b"".join(path.encode("utf-8") + b"\0" + historical.text_hash(files[path]).encode("ascii") + b"\0"
                       for path in included)
    return {"algorithm": historical.DIGEST_ALGORITHM, "digest": hashlib.sha256(payload).hexdigest(),
            "file_count": len(included), "digest_exclusions": list(IMMUTABLE_PATHS)}


def accepted_introduction(root):
    revisions = historical.git(root, "log", "--full-history", "--reverse", "--topo-order", "--format=%H",
                               "HEAD", "--", EVIDENCE_PATH).decode("ascii").splitlines()
    for revision in revisions:
        try:
            record = historical.load_json(historical.git(root, "show", f"{revision}:{EVIDENCE_PATH}"))
        except ValueError:
            continue
        if record.get("outcome") == "pass":
            return revision
    return None


def immutable_errors(root, introduction, files):
    errors = []
    for path in IMMUTABLE_PATHS:
        original = files.get(path)
        normalize = historical.normalized_text if path in EVIDENCE_PATHS else lambda value: value
        if original is None or not (root / path).is_file():
            errors.append("Immutable M3 evidence is missing: " + path)
            continue
        if normalize((root / path).read_bytes()) != normalize(original):
            errors.append("Immutable M3 evidence differs from its first accepted introduction: " + path)
        revisions = historical.git(root, "log", "--full-history", "--format=%H", "HEAD", "--", path).decode("ascii").splitlines()
        for revision in revisions:
            if not historical.ancestor(root, introduction, revision):
                continue
            try:
                same = normalize(historical.git(root, "show", f"{revision}:{path}")) == normalize(original)
            except ValueError:
                same = False
            if not same:
                errors.append(f"Immutable M3 evidence was changed or deleted at {revision}: {path}")
    return errors


HISTORICAL_WORKER = r'''
import json
from pathlib import Path
import sys
root, repository, cases, transcript, output = map(Path, sys.argv[1:])
sys.path.insert(0, str(root / "scripts"))
import check_m3_acceptance as acceptance
import check_m2_historical_acceptance as historical
report = acceptance.build_report(root, historical.load_json(repository.read_bytes()), historical.load_json(cases.read_bytes()),
    archived_unit_evidence=(cases.read_bytes(), transcript.read_bytes()))
output.write_text(json.dumps(report, ensure_ascii=False, allow_nan=False), encoding="utf-8")
'''


def replay_snapshot(root, revision, archives):
    """Re-evaluate archived evidence using tested code; never execute unit tests."""
    with tempfile.TemporaryDirectory(prefix="ywe-m3-historical-replay-") as directory:
        temporary = Path(directory)
        checkout = temporary / "checkout"
        historical.git(temporary, "clone", "--local", "--no-hardlinks", "--no-checkout", str(root.resolve()), str(checkout))
        historical.git(checkout, "-c", "core.autocrlf=false", "checkout", "--detach", revision)
        if historical.git(checkout, "status", "--porcelain", "--untracked-files=all").strip():
            raise ValueError("Historical M3 replay checkout is not clean")
        inputs = []
        for index, raw in enumerate(archives[:3]):
            path = temporary / (str(index) + ".evidence")
            path.write_bytes(raw)
            inputs.append(str(path))
        output = temporary / "replayed-report.json"
        completed = subprocess.run([sys.executable, "-B", "-c", HISTORICAL_WORKER, str(checkout), *inputs, str(output)],
                                   cwd=checkout, env=historical.git_environment(), capture_output=True)
        if completed.returncode or not output.is_file():
            raise ValueError("Historical M3 acceptance replay failed: " + completed.stderr.decode("utf-8", errors="replace"))
        if historical.git(checkout, "status", "--porcelain", "--untracked-files=all").strip():
            raise ValueError("Historical M3 replay changed its tested source checkout")
        return historical.load_json(output.read_bytes())


def historical_validation_errors(root):
    root = Path(root).resolve()
    errors, metadata = [], {"status": "invalid", "outcome": "invalid", "milestone_id": "M3"}
    try:
        roadmap = baseline.load_json(root / ROADMAP)
        milestone = next(item for item in roadmap["milestones"] if item["id"] == "M3")
        introduction = accepted_introduction(root)
        if introduction is None:
            record = historical.load_json((root / EVIDENCE_PATH).read_bytes())
            errors.extend(historical.schema_errors(record, historical.load_json((root / HISTORICAL_SCHEMA).read_bytes()), "Pending M3 evidence"))
            if record.get("outcome") != "pending":
                errors.append("Passing M3 evidence must be committed at its immutable introduction")
            if milestone.get("status") != "in_progress" or milestone.get("acceptance_evidence") != []:
                errors.append("Pending M3 evidence cannot discharge completed M3")
            if not errors:
                metadata.update(status="pending", outcome="pending")
            return errors, metadata
        introduced, introduced_modes = historical.snapshot(root, introduction)
        errors.extend(immutable_errors(root, introduction, introduced))
        record = historical.snapshot_json(introduced, EVIDENCE_PATH)
        revision = record.get("implementation_revision")
        if type(revision) is not str or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
            raise ValueError("M3 tested implementation needs a full commit identifier")
        parents = historical.git(root, "rev-list", "--parents", "-n", "1", introduction).decode("ascii").split()[1:]
        if parents != [revision]:
            errors.append("M3 immutable introduction must directly follow its tested implementation")
        files, modes = historical.snapshot(root, revision)
        schema = historical.snapshot_json(files, HISTORICAL_SCHEMA)
        if schema.get("$id") != "https://ywe.local/schemas/m3_historical_acceptance_evidence_schema.json" or schema.get("x-ywe-requirement-id") != "YWE-REQ-0051":
            raise ValueError("Tested M3 historical schema identity or requirement differs")
        errors.extend(historical.schema_errors(record, schema, "Historical M3 evidence"))
        if errors:
            return errors, metadata
        expected_state = source_state(files)
        if record["source_state"] != expected_state or source_state(introduced) != expected_state:
            errors.append("M3 tested and introduced source digests differ")
        if {path: mode for path, mode in modes.items() if path not in IMMUTABLE_PATHS} != {
                path: mode for path, mode in introduced_modes.items() if path not in IMMUTABLE_PATHS}:
            errors.append("M3 tested and introduced source modes differ")
        changed = {value.decode("utf-8") for value in historical.git(root, "diff", "--name-only", "--no-renames", "-z", revision, introduction).split(b"\0") if value}
        if changed - set(IMMUTABLE_PATHS):
            errors.append("M3 immutable introduction changes artifacts outside its fixed evidence paths")
        if record["mapping_sha256"] != historical.text_hash(files[MAPPING_PATH]):
            errors.append("M3 historical mapping identity differs")
        archives = []
        for path, artifact in zip(ARCHIVE_PATHS, record["artifacts"]):
            raw = introduced.get(path)
            if raw is None or len(raw) != artifact["size_bytes"] or hashlib.sha256(raw).hexdigest() != artifact["sha256"]:
                errors.append("M3 actual archive byte identity differs: " + path)
            archives.append(raw)
        if errors:
            return errors, metadata
        acceptance = historical.load_json(archives[3])
        errors.extend(historical.schema_errors(acceptance, historical.snapshot_json(files, "data/schemas/m3_acceptance_report_schema.json"), "Archived M3 acceptance"))
        if acceptance.get("ready") is not True or acceptance.get("judgment") != "CONFORMANT":
            errors.append("M3 archive lacks an actual complete CONFORMANT judgment")
        repository = historical.load_json(archives[0])
        tools = repository.get("tool_versions", {})
        requirements = historical.normalized_text(files["scripts/requirements.txt"]).decode("utf-8").splitlines()
        for line in requirements:
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)", line.strip())
            if match is None or tools.get(match[1]) != match[2]:
                errors.append("M3 execution dependency versions differ from exact tested requirements")
        document = historical.normalized_text(introduced[DOCUMENT_PATH]).decode("utf-8")
        markers = ["M3: ACCEPTED", revision, expected_state["digest"], record["mapping_sha256"]]
        markers.extend(row["id"] for field in ("invariants", "modules", "deliverables", "criteria") for row in acceptance[field])
        if any(marker not in document for marker in markers):
            errors.append("M3 acceptance document lacks source identity or complete obligation judgments")
        if milestone.get("status") == "complete" and milestone.get("acceptance_evidence") != list(EVIDENCE_PATHS):
            errors.append("Completed M3 must reference its exact immutable acceptance evidence pair")
        if milestone.get("status") not in {"in_progress", "complete"}:
            errors.append("Accepted M3 has an invalid current milestone status")
        if errors:
            return errors, metadata
        if replay_snapshot(root, revision, archives) != acceptance:
            errors.append("Archived M3 judgment differs from actual tested-implementation evidence replay")
        if not errors:
            metadata.update(status="accepted", outcome="pass", implementation_revision=revision,
                introduction_revision=introduction, source_state_digest=expected_state["digest"], mapping_sha256=record["mapping_sha256"])
    except (KeyError, OSError, TypeError, ValueError, SyntaxError, StopIteration) as exc:
        errors.append("Unable to verify historical M3 acceptance: " + str(exc))
    return errors, metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check-definition", action="store_true")
    parser.add_argument("--check-historical", action="store_true")
    parser.add_argument("--repository-report", type=Path)
    parser.add_argument("--conformance-report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.check_historical:
            errors, result = historical_validation_errors(args.root)
            result = {**result, "errors": errors}
            exit_code = bool(errors)
        elif args.check_definition:
            errors = definition_errors(args.root.resolve(), baseline.load_json(args.root / MAPPING_PATH))
            historical_errors, durable = historical_validation_errors(args.root)
            errors.extend(historical_errors)
            result = {"definition_valid": not errors, "runtime_acceptance_claimed": False, "durable_evidence": durable, "errors": errors}
            exit_code = bool(errors)
        else:
            repository = baseline.load_json(args.repository_report) if args.repository_report else None
            conformance = baseline.load_json(args.conformance_report) if args.conformance_report else None
            result = build_report(args.root, repository, conformance)
            exit_code = not result["ready"]
    except (KeyError, OSError, TypeError, ValueError, SyntaxError) as exc:
        result = {"definition_valid": False, "runtime_acceptance_claimed": False, "errors": [str(exc)]}
        exit_code = True
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
