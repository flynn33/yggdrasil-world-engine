#!/usr/bin/env python3
"""Verify pending or immutable, source-bound historical M2 acceptance evidence."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from jsonschema import Draft202012Validator

EVIDENCE_PATH = "data/governance/m2_acceptance_evidence.json"
DOCUMENT_PATH = "docs/project/M2_CONTRACT_SCHEMA_FOUNDATION_ACCEPTANCE.md"
EVIDENCE_PATHS = (EVIDENCE_PATH, DOCUMENT_PATH)
SCHEMA_PATH = "data/schemas/m2_historical_acceptance_evidence_schema.json"
SCHEMA_ID = "https://ywe.local/schemas/m2_historical_acceptance_evidence_schema.json"
REPORT_SCHEMA = "data/schemas/repository_validation_report_schema.json"
ROADMAP_PATH = "data/governance/specification_roadmap.json"
CHECK_CATALOG = "data/validation/repository_checks.json"
REQUIREMENTS_PATH = "scripts/requirements.txt"
DIGEST_ALGORITHM = "sha256_sorted_path_nul_normalized_utf8_lf_sha256_nul"
TEXT_HASH_ALGORITHM = "sha256_utf8_lf_normalized"
METHODS = ("meta_schema", "instance", "reference", "identifier", "dependency", "negative", "property", "mutation")
HEADER_KEYS = {"schema_ref", "artifact_type", "artifact_version", "milestone_id", "outcome"}
PASS_KEYS = HEADER_KEYS | {"implementation_revision", "source_state", "check_catalog", "validation_environment",
                           "repository_report", "repository_report_sha256", "formation_report", "validation_operations",
                           "validation_methods", "acceptance_judgments"}
EXIT_CRITERIA = (
    "Every normative schema passes its meta-schema.",
    "Every reference resolves without a network dependency.",
    "Every normative fixture is bound to a schema.",
    "Every reject fixture fails for its intended requirement.",
    "The schema-quality debt inventory is empty.",
    "A roadmap-derived M2 acceptance gate passes from a clean offline checkout.",
)
DELIVERABLES = (
    "One JSON Schema 2020-12 profile, URI namespace, catalog, and offline resolver.",
    "Convert descriptive schema-named records into schemas or rename them by their actual role.",
    "Common identifier, reference, version, time, ordering, request, result, event, provenance, diagnostic, error, transaction, compensation, idempotency, retry, extension, and deprecation contracts.",
    "YAML structural schemas.",
    "Explicit fixture catalog mapping schema, instance pointer, expected result, and expected requirement or error identifiers.",
    "Positive, boundary, reject, recovery, replay, and migration fixtures.",
    "Meta-schema, instance, reference, identifier, dependency, negative, property, and mutation validation.",
    "Roadmap-derived M2 acceptance gate and durable acceptance evidence.",
)


def normalized_text(data: bytes) -> bytes:
    return data.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def unique_object(pairs: list) -> dict:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"Duplicate JSON key: {key}")
        value[key] = item
    return value


def load_json(data: bytes) -> dict:
    def invalid_constant(value: str) -> None:
        raise ValueError(f"Non-finite JSON number: {value}")
    value = json.loads(normalized_text(data), object_pairs_hook=unique_object, parse_constant=invalid_constant)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def json_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(json_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(json_equal(a, b) for a, b in zip(left, right))
    return left == right


def value_hash(value: object) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def text_hash(data: bytes) -> str:
    return hashlib.sha256(normalized_text(data)).hexdigest()


def git_environment() -> dict:
    env = os.environ.copy()
    env.update(GIT_ALLOW_PROTOCOL="file", GIT_TERMINAL_PROMPT="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")
    return env


def git(root: Path, *args: str, input_data: bytes | None = None) -> bytes:
    result = subprocess.run(["git", "-c", f"core.hooksPath={os.devnull}", *args], cwd=root,
                            input=input_data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=git_environment())
    if result.returncode:
        raise ValueError(f"Git {' '.join(args)} failed: {result.stderr.decode('utf-8', errors='replace').strip()}")
    return result.stdout


def ancestor(root: Path, earlier: str, later: str) -> bool:
    result = subprocess.run(["git", "merge-base", "--is-ancestor", earlier, later], cwd=root,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=git_environment())
    if result.returncode not in (0, 1):
        raise ValueError(f"Unable to establish Git ancestry: {result.stderr.decode('utf-8', errors='replace')}")
    return result.returncode == 0


def snapshot(root: Path, revision: str) -> tuple[dict[str, bytes], dict[str, str]]:
    """Read all tracked regular blobs, independently of archive export attributes."""
    entries, modes = [], {}
    for record in git(root, "ls-tree", "-r", "--full-tree", "-z", revision).split(b"\0"):
        if not record:
            continue
        header, raw_path = record.split(b"\t", 1)
        mode, kind, object_id = header.decode("ascii").split()
        path = raw_path.decode("utf-8")
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"Acceptance snapshot contains a non-regular tracked artifact: {path}")
        if path.startswith("/") or "\\" in path or any(part in {"", ".", ".."} for part in path.split("/")):
            raise ValueError(f"Noncanonical snapshot path: {path}")
        entries.append((path, object_id))
        modes[path] = mode
    if not entries:
        raise ValueError("Acceptance snapshot contains no tracked artifacts")
    payload = git(root, "cat-file", "--batch", input_data=("\n".join(item[1] for item in entries) + "\n").encode("ascii"))
    files, offset = {}, 0
    for path, object_id in entries:
        end = payload.index(b"\n", offset)
        header = payload[offset:end].decode("ascii").split()
        if len(header) != 3 or header[:2] != [object_id, "blob"]:
            raise ValueError(f"Unexpected Git object response for {path}")
        size = int(header[2])
        start = end + 1
        files[path] = payload[start:start + size]
        offset = start + size + 1
    if offset != len(payload):
        raise ValueError("Unexpected trailing Git object data")
    return files, modes


def source_state(files: dict[str, bytes]) -> dict:
    payload = bytearray()
    included = sorted(set(files) - set(EVIDENCE_PATHS))
    for path in included:
        payload.extend(path.encode("utf-8") + b"\0" + text_hash(files[path]).encode("ascii") + b"\0")
    return {"algorithm": DIGEST_ALGORITHM, "digest": hashlib.sha256(payload).hexdigest(),
            "file_count": len(included), "digest_exclusions": list(EVIDENCE_PATHS)}


def snapshot_json(files: dict[str, bytes], path: str) -> dict:
    if path not in files:
        raise ValueError(f"Historical snapshot lacks {path}")
    return load_json(files[path])


def schema_errors(value: dict, schema: dict, label: str) -> list[str]:
    Draft202012Validator.check_schema(schema)
    return [f"{label}: {error.message}" for error in Draft202012Validator(schema).iter_errors(value)]


def record_identity_errors(record: dict, outcome: str) -> list[str]:
    header = {"schema_ref": SCHEMA_PATH, "artifact_type": "ywe_m2_acceptance_evidence", "artifact_version": "1.0.0",
              "milestone_id": "M2", "outcome": outcome}
    if (set(record) != (HEADER_KEYS if outcome == "pending" else PASS_KEYS)
            or not json_equal({key: record.get(key) for key in HEADER_KEYS}, header)):
        return ["M2 evidence must preserve its exact record identity and closed pending/pass field set"]
    return []


def current_milestone_errors(roadmap: dict, accepted: bool) -> list[str]:
    m2 = next((item for item in roadmap.get("milestones", []) if item.get("id") == "M2"), None)
    if m2 is None:
        return ["Current roadmap lacks M2"]
    if not accepted:
        if roadmap.get("current_milestone") != "M2" or m2.get("status") != "in_progress" or m2.get("acceptance_evidence") != []:
            return ["Pending historical evidence cannot discharge a completed or promoted M2 milestone"]
        return []
    if m2.get("status") == "complete" or roadmap.get("current_milestone") != "M2":
        if m2.get("status") != "complete" or m2.get("acceptance_evidence") != list(EVIDENCE_PATHS):
            return ["Completed M2 must reference its exact immutable acceptance evidence pair"]
    return []


def accepted_introduction(root: Path) -> str | None:
    revisions = git(root, "log", "--full-history", "--reverse", "--topo-order", "--format=%H", "HEAD", "--", EVIDENCE_PATH).decode("ascii").splitlines()
    for revision in revisions:
        try:
            record = load_json(git(root, "show", f"{revision}:{EVIDENCE_PATH}"))
        except ValueError:
            continue
        if record.get("outcome") == "pass":
            return revision
    return None


def immutable_errors(root: Path, introduction: str, files: dict[str, bytes]) -> list[str]:
    errors = []
    for path in EVIDENCE_PATHS:
        original = files.get(path)
        current_path = root / path
        if original is None or not current_path.is_file():
            errors.append(f"Immutable M2 evidence is missing: {path}")
            continue
        if normalized_text(current_path.read_bytes()) != normalized_text(original):
            errors.append(f"Immutable M2 evidence differs from its first accepted introduction: {path}")
        revisions = git(root, "log", "--full-history", "--format=%H", "HEAD", "--", path).decode("ascii").splitlines()
        for revision in revisions:
            if not ancestor(root, introduction, revision):
                continue
            try:
                same = normalized_text(git(root, "show", f"{revision}:{path}")) == normalized_text(original)
            except ValueError:
                same = False
            if not same:
                errors.append(f"Immutable M2 evidence was changed or deleted at {revision}: {path}")
    return errors


def introduction_change_errors(root: Path, introduction: str) -> list[str]:
    """Require the accepted introduction itself to change only its evidence pair."""
    parents = git(root, "rev-list", "--parents", "-n", "1", introduction).decode("ascii").split()[1:]
    if not parents:
        return ["M2 evidence introduction must follow its tested implementation"]
    errors = []
    for parent in parents:
        changed = {path.decode("utf-8") for path in git(
            root, "diff", "--name-only", "--no-renames", "-z", parent, introduction
        ).split(b"\0") if path}
        unexpected = sorted(changed - set(EVIDENCE_PATHS))
        if unexpected:
            errors.append("M2 evidence introduction changes artifacts outside the fixed evidence pair: "
                          + ", ".join(unexpected))
    return errors


def report_errors(record: dict, files: dict[str, bytes]) -> list[str]:
    errors = []
    report = record["repository_report"]
    errors.extend(schema_errors(report, snapshot_json(files, REPORT_SCHEMA), "Historical repository report"))
    report_keys = {"artifact_type", "artifact_version", "execution_complete", "revision", "context", "check_catalog_sha256",
                   "selection", "offline", "dirty_before", "dirty_after", "tool_versions", "results", "summary"}
    if (set(report) != report_keys or report.get("artifact_type") != "ywe_repository_validation_report"
            or report.get("artifact_version") != "1.0.0"):
        errors.append("Historical repository report must preserve its exact captured identity and field set")
    if errors:
        return errors
    checks = snapshot_json(files, CHECK_CATALOG)["checks"]
    expected = [item for item in checks if "always" in item["contexts"] or "local" in item["contexts"]]
    catalog_hash = text_hash(files[CHECK_CATALOG])
    if record["check_catalog"] != {"path": CHECK_CATALOG, "hash_algorithm": TEXT_HASH_ALGORITHM, "sha256": catalog_hash}:
        errors.append("Historical check catalog identity or content hash differs")
    if (report["execution_complete"] is not True or report["context"] != "local"
            or report["revision"] != record["implementation_revision"]
            or report["check_catalog_sha256"] != catalog_hash
            or not json_equal(report["selection"], {"groups": [], "check_ids": []})
            or not json_equal(report["offline"], {"requested": True, "git_allow_protocol": "file"})
            or report["dirty_before"] != [] or report["dirty_after"] != []):
        errors.append("Historical repository execution must be complete, clean, unfiltered, local, offline, and bound to the tested revision")
    wanted_results = [{"check_id": item["id"], "blocking": item["blocking"], "return_code": 0} for item in expected]
    if not json_equal(report["results"], wanted_results):
        errors.append("Historical report must pass every applicable catalog check exactly once in catalog order with its declared severity")
    if not json_equal(report["summary"], {"passed": len(expected), "blocking_failures": 0, "advisories": 0}):
        errors.append("Historical full-suite summary differs from its complete passing results")
    if record["repository_report_sha256"] != value_hash(report):
        errors.append("Embedded historical repository report content hash differs")
    environment = record["validation_environment"]
    tools = report["tool_versions"]
    if (set(environment) != {"requirements_ref", "requirements_sha256", "pinned_tool_versions"}
            or set(tools) != {"python", "jsonschema", "PyYAML", "referencing"}
            or environment["requirements_ref"] != REQUIREMENTS_PATH
            or environment["requirements_sha256"] != text_hash(files[REQUIREMENTS_PATH])
            or not json_equal(environment["pinned_tool_versions"], tools)
            or any(not isinstance(tools.get(key), str) or not tools[key] for key in ("python", "jsonschema", "PyYAML", "referencing"))):
        errors.append("Historical validation environment does not preserve exact requirements and recorded tool versions")
    pins = {}
    for line in normalized_text(files[REQUIREMENTS_PATH]).decode("utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([^\s;]+)", line.strip())
        if not match or match[1] in pins:
            errors.append("Historical direct validation dependencies must have unique exact version pins")
            continue
        pins[match[1]] = match[2]
    if not {"jsonschema", "PyYAML"}.issubset(pins) or any(tools.get(name) != version for name, version in pins.items()):
        errors.append("Historical execution tool versions differ from its exact direct dependency pins")
    return errors


def formation_errors(record: dict, files: dict[str, bytes]) -> list[str]:
    errors = []
    roadmap = snapshot_json(files, ROADMAP_PATH)
    m2 = next((item for item in roadmap.get("milestones", []) if item.get("id") == "M2"), {})
    if m2.get("exit_criteria") != list(EXIT_CRITERIA) or m2.get("deliverables") != list(DELIVERABLES):
        errors.append("Historical M2 obligation statements differ from the accepted roadmap contract")
    report = record["formation_report"]
    if (report.get("artifact_type") != "ywe_m2_readiness_report" or report.get("artifact_version") != "1.0.0"
            or report.get("ready") is not False or report.get("errors") != []
            or report.get("revision") != record["implementation_revision"]
            or report.get("roadmap_sha256") != text_hash(files[ROADMAP_PATH])):
        errors.append("Historical formation report must bind the tested source and explicitly leave D8 pending")
    expected_judgments = []
    for group, prefix, statements in (("criteria", "C", EXIT_CRITERIA), ("deliverables", "D", DELIVERABLES)):
        obligations = report.get(group)
        if not isinstance(obligations, list) or len(obligations) != len(statements):
            errors.append(f"Historical formation report must preserve every ordered {group} obligation")
            continue
        for index, (item, statement) in enumerate(zip(obligations, statements)):
            identifier = f"M2-{prefix}{index + 1}"
            pending = identifier == "M2-D8"
            if (not isinstance(item, dict) or item.get("id") != identifier or item.get("statement") != statement
                    or item.get("status") != ("unverified" if pending else "pass")
                    or item.get("errors") != (["Durable M2 acceptance evidence is not recorded"] if pending else [])
                    or not isinstance(item.get("evidence"), dict)):
                errors.append(f"Historical formation obligation has no exact successful execution or pending D8: {identifier}")
            expected_judgments.append({"id": identifier, "statement": statement, "status": "pass",
                                       "basis": "immutable_introduction" if pending else "formation_report",
                                       "evidence_pointer": "/source_state" if pending else f"/formation_report/{group}/{index}"})
    if not json_equal(record["acceptance_judgments"], expected_judgments):
        errors.append("Historical acceptance must map all fourteen exact judgments to formation execution or immutable D8 introduction")
    methods = record["validation_methods"]
    if [item.get("method") for item in methods] != list(METHODS):
        errors.append("Historical method execution must contain exactly the eight ordered roadmap methods")
    for method in methods:
        cases = method.get("evidence", {}).get("cases", [])
        count = method.get("executed_case_count")
        if (method.get("status") != "pass" or method.get("execution_complete") is not True or method.get("errors") != []
                or type(count) is not int or count < 1 or not isinstance(cases, list) or len(cases) != count
                or method.get("successful_case_count") != count or any(case.get("result") != "pass" for case in cases)):
            errors.append(f"Historical method lacks complete, nonempty concrete passing execution: {method.get('method')}")
        if method.get("method") == "mutation" and (len(cases) != 3 or any(case.get("killed") is not True for case in cases)):
            errors.append("Historical mutation evidence must contain all three actually killed mutants")
    operations = record["validation_operations"]
    if {item.get("category") for item in operations} != {"recovery", "replay", "migration"}:
        errors.append("Historical lifecycle evidence must execute recovery, replay, and migration")
    seen = set()
    for operation in operations:
        key = operation.get("operation_id")
        stages = operation.get("stages")
        if (not isinstance(key, str) or not key or key in seen or operation.get("result") != "pass"
                or operation.get("validation_scope") != "schema_validation_operation" or not isinstance(stages, list) or not stages
                or any(stage.get("result") not in {"accept", "reject"} or not isinstance(stage.get("errors"), list)
                       or (stage.get("result") == "accept") != (stage.get("errors") == []) for stage in stages)):
            errors.append(f"Historical lifecycle operation lacks concrete exact passing stages: {key}")
        seen.add(key)
    return errors


REPLAY_WORKER = r'''
import json
from pathlib import Path
import sys
root, report_path, output_path = map(Path, sys.argv[1:])
sys.path.insert(0, str(root / "scripts"))
import check_m2_acceptance as acceptance
import check_m2_validation_operations as operations
import check_m2_validation_methods as methods
repository_report = json.loads(report_path.read_text(encoding="utf-8"))
gate = acceptance.build_report(root, repository_report, verify_historical=False)
operation_errors, operation_results = operations.validation_errors(root)
method_errors, method_results = methods.validation_errors(root)
payload = {"formation_report": gate,
           "validation_operations": {"errors": operation_errors, "results": operation_results},
           "validation_methods": {"errors": method_errors, "results": method_results}}
output_path.write_text(json.dumps(payload, ensure_ascii=False, allow_nan=False), encoding="utf-8")
'''


def replay_snapshot(root: Path, revision: str, repository_report: dict) -> dict:
    """Execute the tested implementation's formation and concrete D6/D7 evaluators."""
    with tempfile.TemporaryDirectory(prefix="ywe-m2-historical-replay-") as directory:
        temporary = Path(directory)
        checkout = temporary / "checkout"
        git(temporary, "clone", "--local", "--no-hardlinks", "--no-checkout", str(root.resolve()), str(checkout))
        git(checkout, "-c", "core.autocrlf=false", "checkout", "--detach", revision)
        if git(checkout, "status", "--porcelain", "--untracked-files=all").strip():
            raise ValueError("Historical replay checkout is not clean")
        report_path, output_path = temporary / "repository-report.json", temporary / "formation-results.json"
        report_path.write_text(json.dumps(repository_report, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        completed = subprocess.run([sys.executable, "-B", "-c", REPLAY_WORKER, str(checkout), str(report_path), str(output_path)],
                                   cwd=checkout, env=git_environment(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if completed.returncode or not output_path.is_file():
            detail = completed.stderr.decode("utf-8", errors="replace").strip()
            raise ValueError(f"Historical formation replay failed: {detail}")
        if git(checkout, "status", "--porcelain", "--untracked-files=all").strip():
            raise ValueError("Historical formation replay changed its tested source checkout")
        return load_json(output_path.read_bytes())


def validation_errors(root: Path) -> tuple[list[str], dict]:
    root = root.resolve()
    errors, metadata = [], {"status": "invalid", "outcome": "invalid", "milestone_id": "M2"}
    try:
        roadmap = load_json((root / ROADMAP_PATH).read_bytes())
        introduction = accepted_introduction(root)
        current_path = root / EVIDENCE_PATH
        if introduction is None:
            if current_path.is_file():
                current = load_json(current_path.read_bytes())
                schema = load_json((root / SCHEMA_PATH).read_bytes())
                errors.extend(record_identity_errors(current, "pending"))
                errors.extend(schema_errors(current, schema, "Pending M2 evidence"))
                if current.get("outcome") != "pending":
                    errors.append("A passing M2 evidence record must be committed at its immutable introduction before acceptance")
            errors.extend(current_milestone_errors(roadmap, accepted=False))
            if not errors:
                metadata.update(status="pending", outcome="pending", reason="M2 remains active; no immutable acceptance record has been introduced")
            return errors, metadata
        introduction_files, introduction_modes = snapshot(root, introduction)
        errors.extend(immutable_errors(root, introduction, introduction_files))
        record = snapshot_json(introduction_files, EVIDENCE_PATH)
        errors.extend(record_identity_errors(record, "pass"))
        revision = record.get("implementation_revision")
        if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
            raise ValueError("Historical implementation revision must be a full commit identifier")
        if git(root, "rev-parse", "--verify", f"{revision}^{{commit}}").decode("ascii").strip() != revision or not ancestor(root, revision, introduction):
            raise ValueError("Historical implementation revision must resolve locally and precede its accepted introduction")
        files, modes = snapshot(root, revision)
        schema = snapshot_json(files, SCHEMA_PATH)
        if schema.get("$id") != SCHEMA_ID or schema.get("x-ywe-requirement-id") != "YWE-REQ-0037":
            raise ValueError("Historical acceptance evidence schema identity or owning requirement differs")
        errors.extend(schema_errors(record, schema, "Historical M2 evidence"))
        if errors:
            return errors, metadata
        expected_state = source_state(files)
        if not json_equal(record["source_state"], expected_state) or source_state(introduction_files) != expected_state:
            errors.append("Historical tested and introduction source states differ from their exact fixed-exclusion digest")
        if {path: mode for path, mode in modes.items() if path not in EVIDENCE_PATHS} != {path: mode for path, mode in introduction_modes.items() if path not in EVIDENCE_PATHS}:
            errors.append("Historical tested and introduction source file modes differ")
        errors.extend(introduction_change_errors(root, introduction))
        errors.extend(report_errors(record, files))
        errors.extend(formation_errors(record, files))
        document = normalized_text(introduction_files[DOCUMENT_PATH]).decode("utf-8")
        markers = ["M2: ACCEPTED", revision, expected_state["digest"]] + [item["id"] for item in record["acceptance_judgments"]]
        if any(marker not in document for marker in markers):
            errors.append("Historical M2 acceptance document lacks its accepted outcome, tested source, or fourteen judgment identifiers")
        errors.extend(current_milestone_errors(roadmap, accepted=True))
        if errors:
            return errors, metadata
        replayed = replay_snapshot(root, revision, record["repository_report"])
        if not json_equal(replayed.get("formation_report"), record["formation_report"]):
            errors.append("Historical formation report differs from actual tested-implementation obligation replay")
        for key in ("validation_operations", "validation_methods"):
            actual = replayed.get(key, {})
            if actual.get("errors") != [] or not json_equal(actual.get("results"), record[key]):
                errors.append(f"Historical {key} differs from its actual concrete tested-implementation replay")
        if not errors:
            metadata.update(status="accepted", outcome="pass", introduction_revision=introduction, implementation_revision=revision,
                            source_state_digest=expected_state["digest"], discharged_obligations=[item["id"] for item in record["acceptance_judgments"]])
    except (OSError, ValueError, TypeError, KeyError, AttributeError, UnicodeError) as exc:
        errors.append(f"Unable to verify historical M2 acceptance: {exc}")
    return errors, metadata


def main() -> int:
    errors, metadata = validation_errors(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    if errors:
        print("M2 historical acceptance failed:")
        for error in errors:
            print("  - " + error)
        return 1
    if metadata["status"] == "pending":
        print("M2 historical acceptance evidence pending (milestone active; acceptance not discharged).")
    else:
        print(f"M2 historical acceptance passed (immutable introduction {metadata['introduction_revision']}; fourteen source-bound obligations).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
