#!/usr/bin/env python3
"""Validate the M0 repository truth, classification, and acceptance authorities."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    print("Missing validation dependencies. Install scripts/requirements.txt.")
    raise SystemExit(1)


TEXT_ENCODING = "utf-8-sig"
ROADMAP_PATH = "data/governance/specification_roadmap.json"
CHECK_CATALOG_PATH = "data/validation/repository_checks.json"
CLASSIFICATION_PATH = "data/governance/artifact_classification_manifest.json"
SCOPE_PATH = "data/governance/scope_partition_manifest.json"
TRUTH_PATH = "data/governance/repository_truth_manifest.json"
RELEASE_POLICY_PATH = "data/governance/release_publication_policy.json"
PROMISE_PATH = "data/governance/public_promise_register.json"
DEBT_PATH = "data/validation/repository_quality_debt_inventory.json"
SCHEMA_DEBT_PATH = "data/validation/schema_quality_baseline.json"
EVIDENCE_PATH = "data/governance/m0_acceptance_evidence.json"
ACCEPTANCE_DOCUMENT_PATH = "docs/project/M0_TRUTHFUL_BASELINE_ACCEPTANCE.md"
PHASE_8_9_REQUIRED_PATH = "data/validation/required_phase_8_9_artifacts.json"
WIKI_SYNC_WORKFLOW_PATH = ".github/workflows/wiki-sync.yml"

INSTANCE_SCHEMAS = {
    CLASSIFICATION_PATH: "data/schemas/artifact_classification_manifest_schema.json",
    SCOPE_PATH: "data/schemas/scope_partition_manifest_schema.json",
    TRUTH_PATH: "data/schemas/repository_truth_manifest_schema.json",
    RELEASE_POLICY_PATH: "data/schemas/release_publication_policy_schema.json",
    PROMISE_PATH: "data/schemas/public_promise_register_schema.json",
    DEBT_PATH: "data/schemas/repository_quality_debt_inventory_schema.json",
    EVIDENCE_PATH: "data/schemas/milestone_acceptance_evidence_schema.json",
}

M0_EVIDENCE_REFS = [EVIDENCE_PATH, ACCEPTANCE_DOCUMENT_PATH]
M0_DIGEST_EXCLUSIONS = set(M0_EVIDENCE_REFS)
REPOSITORY_STATE_DIGEST_ALGORITHM = "sha256_sorted_path_nul_normalized_utf8_lf_sha256_nul"
DIFF_HASH_ALGORITHM = "sha256_git_diff_binary"
EVIDENCE_ARTIFACT_VERSION = "1.0.0"
NORMALIZED_TEXT_SHA256_ALGORITHM = "sha256_utf8_lf_normalized"
M0_PREAUTHORIZED_CHANGE_BUDGETS = {
    "docs/project/source_inventory.md": 50.0,
    "missing_source_documents.md": 40.0,
    "docs/governance/README.md": 40.0,
    "docs/architecture/ASH_RUNTIME_GENERATION_FLOW_NOTES.md": 35.0,
    "SOURCE_AVAILABILITY_MANIFEST.md": 35.0,
    "guide.md": 35.0,
    "CONTRIBUTING.md": 35.0,
    "docs/architecture/forsetti_module_manifest_conventions.md": 30.0,
    "adapters/godot/README.md": 30.0,
    "adapters/unity/README.md": 30.0,
    "adapters/unreal/README.md": 30.0,
    "README.md": 10.0,
}
ACCEPTANCE_REQUIRED_HEADINGS = (
    "Baseline",
    "Authority and Phase Alignment",
    "M0 Deliverables",
    "M0 Exit Criteria",
    "Coverage Counts",
    "Gate Results",
    "Validation Results",
    "Diff Review",
    "Acceptance Judgment",
    "Deferred Work",
)
ACCEPTANCE_JUDGMENT_LINES = (
    "M0: ACCEPTED",
    "Roadmap transition recorded: M0 complete; M1 in progress",
    "Publication state: unreleased",
    "Platform work authorized: false",
    "Open M0 blockers: none",
)
MATURITY_CLASSES = {
    "normative",
    "informative",
    "example",
    "historical",
    "deprecated",
    "superseded",
    "placeholder",
}
SCOPE_PARTITIONS = {
    "ywe_core",
    "ywe_extension_profile",
    "ash_dependency_material",
    "wrw_reference_profile",
    "governance_validation",
    "historical_evidence",
    "later_release_work",
}
FOUNDATION_GATES = {f"9.{number}" for number in range(3, 9)}
PLACEHOLDER_STATUS = re.compile(
    r"(?im)^\s*[\"']?status[\"']?\s*:\s*[\"']?"
    r"placeholder(?:_|\s+)awaiting(?:_|\s+)finalized(?:_|\s+)content",
)
CURRENT_PLACEHOLDER_COUNT = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?current\s+placeholder\s+(?:artifacts|records)\s*:\s*`?([0-9]+)`?"
)


class DuplicateKeyError(ValueError):
    """Raised when a JSON object contains a duplicate member name."""


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key {key!r}")
        value[key] = item
    return value


def load_json(path: Path) -> Any:
    with path.open(encoding=TEXT_ENCODING) as handle:
        return json.load(handle, object_pairs_hook=unique_object)


def load_json_object(root: Path, relative_path: str, errors: list[str]) -> dict[str, Any] | None:
    path = root / relative_path
    if not path.is_file():
        errors.append(f"Missing required M0 artifact: {relative_path}")
        return None
    try:
        value = load_json(path)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"Unable to load {relative_path}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{relative_path} must contain a JSON object")
        return None
    return value


def schema_validation_errors(instance: Any, schema: dict[str, Any], label: str) -> list[str]:
    errors: list[str] = []
    try:
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
    except Exception as exc:
        return [f"{label}: invalid governing schema: {exc}"]
    for error in sorted(
        validator.iter_errors(instance),
        key=lambda item: ([str(part) for part in item.absolute_path], item.message),
    ):
        pointer = "/".join(str(part) for part in error.absolute_path) or "<root>"
        errors.append(f"{label}:{pointer}: {error.message}")
    return errors


def load_and_validate_instances(
    root: Path,
    required_instances: Iterable[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for instance_path in required_instances:
        instance = load_json_object(root, instance_path, errors)
        schema_path = INSTANCE_SCHEMAS[instance_path]
        schema = load_json_object(root, schema_path, errors)
        if instance is None or schema is None:
            continue
        instance_errors = schema_validation_errors(instance, schema, instance_path)
        errors.extend(instance_errors)
        if not instance_errors:
            documents[instance_path] = instance
    return documents


def is_safe_repository_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        return False
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return False
    parts = PurePosixPath(value).parts
    return bool(parts) and all(part not in {"", ".", ".."} for part in parts)


def repository_path_errors(
    root: Path,
    value: Any,
    label: str,
    *,
    require_file: bool = True,
) -> list[str]:
    if not is_safe_repository_path(value):
        return [f"{label} is not a safe repository-relative POSIX path: {value!r}"]
    path = (root / value).resolve(strict=False)
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return [f"{label} resolves outside the repository: {value!r}"]
    if require_file and not path.is_file():
        return [f"{label} does not exist: {value}"]
    return []


def split_repository_ref(value: str) -> tuple[str, str | None]:
    path, separator, pointer = value.partition("#")
    return path, pointer if separator else None


def resolve_json_pointer(document: Any, pointer: str) -> tuple[bool, Any]:
    if pointer in {"", "/"}:
        return True, document
    if not pointer.startswith("/"):
        return False, None
    current = document
    for encoded in pointer[1:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            return False, None
    return True, current


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def normalized_utf8_bytes(path: Path) -> bytes:
    """Return strict UTF-8 text with BOM removed and all line endings normalized to LF."""
    return normalized_utf8_data(path.read_bytes())


def normalized_utf8_data(value: bytes) -> bytes:
    """Normalize strict UTF-8 bytes without depending on the checkout line-ending policy."""
    text = value.decode("utf-8-sig", errors="strict")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def normalized_text_sha256(path: Path) -> str:
    return sha256_bytes(normalized_utf8_bytes(path))


def nul_digest(values: Iterable[str]) -> str:
    payload = b"".join(value.encode("utf-8") + b"\0" for value in sorted(set(values)))
    return sha256_bytes(payload)


def reviewed_surface_digest(entries: Iterable[dict[str, Any]]) -> str:
    payload = b"".join(
        str(entry.get("path", "")).encode("utf-8")
        + b"\t"
        + str(entry.get("sha256", "")).encode("ascii", errors="strict")
        + b"\n"
        for entry in sorted(entries, key=lambda item: item.get("path", ""))
    )
    return sha256_bytes(payload)


def git_executable() -> str:
    discovered = shutil.which("git")
    if discovered:
        return discovered
    windows_fallback = Path("C:/Program Files/Git/cmd/git.exe")
    if windows_fallback.is_file():
        return str(windows_fallback)
    return "git"


def run_git(
    root: Path,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [git_executable(), "-C", str(root), *args],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )


def git_error(result: subprocess.CompletedProcess[bytes]) -> str:
    return result.stderr.decode("utf-8", errors="replace").strip()


def resolved_git_commit(root: Path, ref: str) -> str:
    if not isinstance(ref, str) or not ref or ref.startswith("-") or "\x00" in ref:
        raise ValueError(f"unsafe Git commit ref: {ref!r}")
    result = run_git(root, ["rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"])
    if result.returncode != 0:
        raise OSError(f"unable to resolve Git commit {ref!r}: {git_error(result)}")
    value = result.stdout.decode("ascii", errors="strict").strip()
    if re.fullmatch(r"[a-f0-9]{40}", value) is None:
        raise ValueError(f"Git resolved {ref!r} to a non-canonical commit identifier: {value!r}")
    return value


def git_merge_base(root: Path, left: str, right: str) -> str:
    result = run_git(root, ["merge-base", "--", left, right])
    if result.returncode != 0:
        raise OSError(f"unable to calculate merge base for {left!r} and {right!r}: {git_error(result)}")
    value = result.stdout.decode("ascii", errors="strict").strip()
    if re.fullmatch(r"[a-f0-9]{40}", value) is None:
        raise ValueError(f"Git returned a non-canonical merge base: {value!r}")
    return value


def git_current_branch(root: Path) -> str:
    result = run_git(root, ["symbolic-ref", "--quiet", "--short", "HEAD"])
    if result.returncode != 0:
        raise OSError("unable to determine the current branch; HEAD may be detached")
    branch = result.stdout.decode("utf-8", errors="strict").strip()
    if not branch:
        raise ValueError("Git returned an empty current branch")
    return branch


def git_tags(root: Path, ref: str | None = None) -> list[str]:
    args = ["tag", "--list"] if ref is None else ["tag", "--points-at", ref]
    result = run_git(root, args)
    if result.returncode != 0:
        target = "repository" if ref is None else ref
        raise OSError(f"unable to enumerate Git tags for {target!r}: {git_error(result)}")
    tags = [line for line in result.stdout.decode("utf-8", errors="strict").splitlines() if line]
    if len(tags) != len(set(tags)):
        raise ValueError("Git returned duplicate tag names")
    return sorted(tags)


def git_ref_exists(root: Path, ref: str) -> bool:
    return run_git(root, ["rev-parse", "--verify", "--quiet", ref]).returncode == 0


def repository_candidate_paths(root: Path, errors: list[str]) -> list[str]:
    result = run_git(root, ["ls-files", "-z", "--cached", "--others", "--exclude-standard"])
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        errors.append(f"Unable to enumerate repository candidate paths: {detail}")
        return []
    try:
        names = [item for item in result.stdout.decode("utf-8", errors="strict").split("\0") if item]
    except UnicodeDecodeError as exc:
        errors.append(f"Repository contains a path that is not valid UTF-8: {exc}")
        return []
    valid: list[str] = []
    for name in names:
        if not is_safe_repository_path(name):
            errors.append(f"Git reported an unsafe repository path: {name!r}")
            continue
        if (root / name).is_file():
            valid.append(name)
    return sorted(set(valid))


def parse_name_status_z(payload: bytes) -> list[tuple[str, tuple[str, ...]]]:
    tokens = [token for token in payload.split(b"\0") if token]
    records: list[tuple[str, tuple[str, ...]]] = []
    index = 0
    while index < len(tokens):
        status = tokens[index].decode("ascii", errors="replace")
        index += 1
        path_count = 2 if status.startswith(("R", "C")) else 1
        if index + path_count > len(tokens):
            raise ValueError(f"truncated name-status record for {status!r}")
        paths = tuple(tokens[index + offset].decode("utf-8", errors="strict") for offset in range(path_count))
        records.append((status, paths))
        index += path_count
    return records


def changed_candidate_paths(root: Path, base_ref: str, errors: list[str]) -> set[str]:
    if not git_ref_exists(root, base_ref):
        errors.append(f"Unable to resolve required base ref for M0 diff validation: {base_ref}")
        return set()
    changes: set[str] = set()
    commands = [
        ["diff", "--name-status", "-z", "--find-renames", f"{base_ref}...HEAD"],
        ["diff", "--name-status", "-z", "--find-renames", "--cached"],
        ["diff", "--name-status", "-z", "--find-renames"],
    ]
    for command in commands:
        result = run_git(root, command)
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            errors.append(f"Unable to inspect M0 diff with {' '.join(command)}: {detail}")
            continue
        try:
            for _status, paths in parse_name_status_z(result.stdout):
                changes.update(paths)
        except (UnicodeDecodeError, ValueError) as exc:
            errors.append(f"Unable to parse M0 Git diff: {exc}")
    untracked = run_git(root, ["ls-files", "-z", "--others", "--exclude-standard"])
    if untracked.returncode != 0:
        errors.append("Unable to inspect untracked files for the M0 diff")
    else:
        try:
            changes.update(
                item for item in untracked.stdout.decode("utf-8", errors="strict").split("\0") if item
            )
        except UnicodeDecodeError as exc:
            errors.append(f"Unable to decode untracked path: {exc}")
    return changes


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    if not isinstance(pattern, str) or not pattern or "\\" in pattern or pattern.startswith("/"):
        raise ValueError(f"invalid repository glob {pattern!r}")
    if any(part == ".." for part in PurePosixPath(pattern).parts):
        raise ValueError(f"repository glob contains traversal {pattern!r}")
    expression = "^"
    index = 0
    while index < len(pattern):
        character = pattern[index]
        if character == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                index += 2
                if index < len(pattern) and pattern[index] == "/":
                    expression += "(?:.*/)?"
                    index += 1
                else:
                    expression += ".*"
                continue
            expression += "[^/]*"
        elif character == "?":
            expression += "[^/]"
        elif character == "[":
            closing = pattern.find("]", index + 1)
            if closing < 0:
                raise ValueError(f"unterminated character class in glob {pattern!r}")
            content = pattern[index + 1 : closing]
            if not content:
                raise ValueError(f"empty character class in glob {pattern!r}")
            if content[0] == "!":
                content = "^" + content[1:]
            expression += "[" + content.replace("\\", "\\\\") + "]"
            index = closing
        else:
            expression += re.escape(character)
        index += 1
    return re.compile(expression + "$")


def rule_matches(path: str, rule: dict[str, Any], errors: list[str], label: str) -> bool:
    try:
        included = any(glob_to_regex(pattern).fullmatch(path) for pattern in rule.get("include", []))
        excluded = any(glob_to_regex(pattern).fullmatch(path) for pattern in rule.get("exclude", []))
    except (re.error, ValueError) as exc:
        errors.append(f"{label} contains an invalid path glob: {exc}")
        return False
    return included and not excluded


def effective_assignments(
    paths: list[str],
    manifest: dict[str, Any],
    value_field: str,
    errors: list[str],
    label: str,
) -> dict[str, dict[str, Any]]:
    assignments: dict[str, dict[str, Any]] = {}
    overrides: dict[str, dict[str, Any]] = {}
    override_paths: list[str] = []
    for override in manifest.get("overrides", []):
        path = override.get("path")
        override_paths.append(path)
        if is_safe_repository_path(path):
            overrides[path] = override
        else:
            errors.append(f"{label} override contains unsafe path {path!r}")
    duplicates = sorted(path for path, count in Counter(override_paths).items() if count > 1)
    if duplicates:
        errors.append(f"{label} contains duplicate overrides: {duplicates}")

    rules = manifest.get("ordered_rules", [])
    rule_ids = [rule.get("id") for rule in rules]
    duplicate_rule_ids = sorted(item for item, count in Counter(rule_ids).items() if count > 1)
    if duplicate_rule_ids:
        errors.append(f"{label} contains duplicate rule IDs: {duplicate_rule_ids}")

    for path in paths:
        if path in overrides:
            assignments[path] = overrides[path]
            continue
        matches = [rule for rule in rules if rule_matches(path, rule, errors, f"{label} {rule.get('id')}")]
        if not matches:
            errors.append(f"{label} has no assignment for repository path: {path}")
            continue
        if len(matches) > 1:
            identifiers = [rule.get("id") for rule in matches]
            errors.append(f"{label} multiply classifies {path}: {identifiers}")
            continue
        assignments[path] = matches[0]

    assigned_values = Counter(
        assignment.get(value_field) for assignment in assignments.values() if assignment.get(value_field)
    )
    coverage_key = "counts_by_class" if value_field == "classification" else "counts_by_partition"
    recorded = manifest.get("coverage", {}).get(coverage_key, {})
    actual = {key: assigned_values.get(key, 0) for key in recorded}
    if recorded != actual:
        errors.append(f"{label} coverage counts are stale: recorded {recorded}; actual {actual}")
    return assignments


def declared_placeholder_paths(root: Path, paths: Iterable[str]) -> set[str]:
    placeholders: set[str] = set()
    for relative_path in paths:
        path = root / relative_path
        if path.suffix.lower() not in {".json", ".md", ".yaml", ".yml"}:
            continue
        try:
            with path.open(encoding=TEXT_ENCODING, errors="replace") as handle:
                prefix = handle.read(4096)
        except OSError:
            continue
        if PLACEHOLDER_STATUS.search(prefix):
            placeholders.add(relative_path)
    return placeholders


def assignment_reference_errors(
    root: Path,
    assignments: dict[str, dict[str, Any]],
    label: str,
) -> list[str]:
    errors: list[str] = []
    for path, assignment in assignments.items():
        for field in ("governing_source", "superseded_by", "migration_ref", "mirror_of", "synchronization_check_ref"):
            value = assignment.get(field)
            if value:
                errors.extend(repository_path_errors(root, value, f"{label} {path} {field}"))
    return errors


def validate_classification_scope(
    root: Path,
    paths: list[str],
    classification: dict[str, Any],
    scope: dict[str, Any],
    canonical_version: str,
    errors: list[str],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    if classification.get("repository_baseline") != canonical_version:
        errors.append("Artifact classification repository baseline does not match VERSION")
    if scope.get("repository_baseline") != canonical_version:
        errors.append("Scope partition repository baseline does not match VERSION")
    for label, manifest in (("Artifact classification", classification), ("Scope partition", scope)):
        snapshot = manifest.get("tracked_path_snapshot", {})
        actual_digest = nul_digest(paths)
        if snapshot.get("path_count") != len(paths):
            errors.append(
                f"{label} path snapshot count is {snapshot.get('path_count')}; expected {len(paths)}"
            )
        if snapshot.get("path_digest") != actual_digest:
            errors.append(f"{label} path snapshot digest is stale")

    sensitive_paths = [item.get("path") for item in classification.get("sensitive_sources", [])]
    duplicate_sensitive = sorted(
        path for path, count in Counter(sensitive_paths).items() if count > 1
    )
    if duplicate_sensitive:
        errors.append(f"Artifact classification contains duplicate sensitive sources: {duplicate_sensitive}")
    for source in classification.get("sensitive_sources", []):
        path_name = source.get("path")
        path_errors = repository_path_errors(root, path_name, "Classification sensitive source")
        errors.extend(path_errors)
        if path_errors:
            continue
        try:
            actual_hash = normalized_text_sha256(root / path_name)
        except UnicodeDecodeError as exc:
            errors.append(f"Classification sensitive source is not strict UTF-8: {path_name}: {exc}")
            continue
        if source.get("sha256") != actual_hash:
            errors.append(f"Classification sensitive-source hash is stale: {path_name}")

    class_ids = [item.get("id") for item in classification.get("classes", [])]
    if set(class_ids) != MATURITY_CLASSES or len(class_ids) != len(MATURITY_CLASSES):
        errors.append("Artifact classification must define each maturity class exactly once")
    partition_ids = [item.get("id") for item in scope.get("partitions", [])]
    if set(partition_ids) != SCOPE_PARTITIONS or len(partition_ids) != len(SCOPE_PARTITIONS):
        errors.append("Scope manifest must define each primary partition exactly once")

    class_assignments = effective_assignments(paths, classification, "classification", errors, "Artifact classification")
    scope_assignments = effective_assignments(paths, scope, "primary_partition", errors, "Scope partition")
    errors.extend(assignment_reference_errors(root, class_assignments, "Artifact classification"))
    errors.extend(assignment_reference_errors(root, scope_assignments, "Scope partition"))

    declared = declared_placeholder_paths(root, paths)
    classified = {
        path for path, assignment in class_assignments.items() if assignment.get("classification") == "placeholder"
    }
    if declared != classified:
        missing = sorted(declared - classified)
        stale = sorted(classified - declared)
        if missing:
            errors.append(f"Declared placeholder artifacts are not classified as placeholder: {missing}")
        if stale:
            errors.append(f"Placeholder classifications lack a current placeholder status marker: {stale}")

    for path in sorted(set(class_assignments) & set(scope_assignments)):
        maturity = class_assignments[path].get("classification")
        partition = scope_assignments[path].get("primary_partition")
        if maturity == "placeholder" and partition != "later_release_work":
            errors.append(f"Placeholder artifact is not routed to later_release_work: {path}")
        if maturity == "superseded" and not class_assignments[path].get("superseded_by"):
            errors.append(f"Superseded artifact is missing superseded_by: {path}")
        if maturity == "deprecated" and not class_assignments[path].get("migration_ref"):
            errors.append(f"Deprecated artifact is missing migration_ref: {path}")
        if maturity == "normative" and partition in {"historical_evidence", "later_release_work"}:
            exception = scope_assignments[path].get("normative_scope_exception")
            if not isinstance(exception, dict):
                errors.append(
                    f"Normative artifact uses incompatible scope partition {partition} without an explicit exception: {path}"
                )
            else:
                rationale = exception.get("rationale")
                authority_ref = exception.get("authority_ref")
                if not isinstance(rationale, str) or len(rationale.strip()) < 10:
                    errors.append(f"Normative scope exception lacks a substantive rationale: {path}")
                errors.extend(
                    repository_path_errors(
                        root,
                        authority_ref,
                        f"Normative scope exception authority for {path}",
                    )
                )
        if maturity == "placeholder":
            for field in ("future_milestone", "debt_ref"):
                if not class_assignments[path].get(field):
                    errors.append(f"Placeholder artifact {path} is missing {field}")
        if partition == "later_release_work":
            for field in ("future_milestone", "debt_ref"):
                if not scope_assignments[path].get(field):
                    errors.append(f"Later-release artifact {path} is missing {field}")
    return class_assignments, scope_assignments


def canonical_version_errors(root: Path, roadmap: dict[str, Any]) -> tuple[str, list[str]]:
    errors: list[str] = []
    try:
        version = (root / "VERSION").read_text(encoding=TEXT_ENCODING).strip()
    except OSError as exc:
        return "", [f"Unable to read canonical VERSION source: {exc}"]
    if roadmap.get("repository_baseline") != version:
        errors.append("Roadmap repository_baseline does not match VERSION")
    for source in roadmap.get("version_sources", []):
        path = root / source.get("path", "")
        if not path.is_file():
            errors.append(f"Missing declared version mirror: {source.get('path')}")
            continue
        try:
            kind = source.get("kind")
            if kind == "plain":
                actual = path.read_text(encoding=TEXT_ENCODING).strip()
            elif kind == "json_field":
                actual: Any = load_json(path)
                for part in source.get("field", "").split("."):
                    if isinstance(actual, dict):
                        actual = actual[part]
                    elif isinstance(actual, list) and part.isdigit():
                        actual = actual[int(part)]
                    else:
                        raise KeyError(part)
            elif kind == "text_template":
                marker = source.get("template", "").format(version=version)
                if marker not in path.read_text(encoding=TEXT_ENCODING):
                    errors.append(f"Version mirror {source.get('path')} is missing {marker!r}")
                continue
            else:
                errors.append(f"Unknown version source kind for {source.get('path')}")
                continue
            if actual != version:
                errors.append(f"Version mirror {source.get('path')} contains {actual!r}; expected {version!r}")
        except (OSError, KeyError, TypeError, json.JSONDecodeError, DuplicateKeyError) as exc:
            errors.append(f"Unable to validate version mirror {source.get('path')}: {exc}")
    return version, errors


def validate_release_policy(
    root: Path,
    roadmap: dict[str, Any],
    policy: dict[str, Any],
    canonical_version: str,
    errors: list[str],
    debt_inventory: dict[str, Any] | None = None,
) -> None:
    if policy.get("baseline_authority_ref") != "VERSION":
        errors.append("Release policy must identify VERSION as the canonical baseline authority")
    concept_ids = [item.get("id") for item in policy.get("concepts", [])]
    expected = {
        "repository_baseline_version",
        "git_tag",
        "changelog_entry",
        "github_release_object",
        "agnostic_specification_release",
        "downstream_product_release",
    }
    if set(concept_ids) != expected or len(concept_ids) != len(expected):
        errors.append("Release policy must define each publication concept exactly once")
    by_id = {item.get("id"): item for item in policy.get("concepts", [])}
    for concept_id in expected - {"agnostic_specification_release"}:
        if by_id.get(concept_id, {}).get("creates_specification_publication") is not False:
            errors.append(f"Release policy incorrectly treats {concept_id} as specification publication")
    if by_id.get("agnostic_specification_release", {}).get("creates_specification_publication") is not True:
        errors.append("An agnostic specification release must be the explicit specification publication event")
    try:
        all_tags = git_tags(root)
        tags_at_head = git_tags(root, "HEAD")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        errors.append(f"Unable to verify release-policy Git tag evidence: {exc}")
    else:
        tag_semantics = policy.get("tag_semantics", {})
        if tag_semantics.get("existing_tag_count") != len(all_tags):
            errors.append(
                "Release policy existing_tag_count disagrees with live Git: "
                f"recorded {tag_semantics.get('existing_tag_count')!r}; expected {len(all_tags)}"
            )
        if tag_semantics.get("tags_at_current_head") != tags_at_head:
            errors.append(
                "Release policy tags_at_current_head disagrees with live Git: "
                f"recorded {tag_semantics.get('tags_at_current_head')!r}; expected {tags_at_head}"
            )
    milestone_by_id = {item["id"]: item for item in roadmap.get("milestones", [])}
    publication = roadmap.get("publication", {})
    if milestone_by_id.get("M10", {}).get("status") != "complete":
        expected_pre_m10 = {
            "publication_state": publication.get("state"),
            "published_releases": publication.get("published_releases"),
            "github_release_objects": publication.get("github_release_objects"),
            "agnostic_specification_releases": publication.get("agnostic_specification_releases"),
            "platform_work_authorized": roadmap.get("platform_gate", {}).get("platform_work_authorized"),
        }
        if policy.get("pre_m10_constraints") != expected_pre_m10:
            errors.append("Release policy pre-M10 constraints disagree with the roadmap")
    for field in ("version_mirror_registry_ref", "publication_state_authority_ref", "platform_gate_authority_ref"):
        value = policy.get(field)
        if isinstance(value, str):
            path_name, pointer = split_repository_ref(value)
            errors.extend(repository_path_errors(root, path_name, f"Release policy {field}"))
            if pointer is not None and path_name == ROADMAP_PATH:
                valid, _ = resolve_json_pointer(roadmap, pointer)
                if not valid:
                    errors.append(f"Release policy {field} has an unresolved JSON pointer: {value}")
    if canonical_version and roadmap.get("repository_baseline") != canonical_version:
        errors.append("Release policy is evaluated against a roadmap with a stale repository baseline")
    if debt_inventory is not None:
        exception_ref = policy.get("historical_exception_ref")
        debt_by_id = {
            record.get("debt_id"): record for record in debt_inventory.get("debts", [])
        }
        exception = debt_by_id.get(exception_ref, {})
        if (
            exception.get("status") != "accepted_exception"
            or exception.get("category") != "historical_release_wording"
        ):
            errors.append(
                "Release policy historical exception must resolve to accepted historical-release debt"
            )


def validate_truth_manifest(
    root: Path,
    truth: dict[str, Any],
    roadmap: dict[str, Any],
    canonical_version: str,
    errors: list[str],
) -> None:
    baseline = truth.get("repository_baseline", {})
    if baseline.get("value") != canonical_version or baseline.get("canonical_source") != "VERSION":
        errors.append("Repository truth manifest baseline does not match canonical VERSION")
    truth_roadmap = truth.get("roadmap", {})
    if truth_roadmap.get("current_milestone") != roadmap.get("current_milestone"):
        errors.append("Repository truth current milestone disagrees with the roadmap")
    publication = roadmap.get("publication", {})
    expected_publication = {
        "state": publication.get("state"),
        "github_release_objects": publication.get("github_release_objects"),
        "agnostic_specification_releases": publication.get("agnostic_specification_releases"),
    }
    if truth.get("publication") != expected_publication:
        errors.append("Repository truth publication values disagree with the roadmap")
    roadmap_gate = roadmap.get("platform_gate", {})
    expected_platform_gate = {
        "authorized_after": roadmap_gate.get("authorized_after"),
        "status": roadmap_gate.get("status"),
        "platform_work_authorized": roadmap_gate.get("platform_work_authorized"),
        "branch_name_activates_platform_mode": False,
        "downstream_repository_required": True,
    }
    if truth.get("platform_gate") != expected_platform_gate:
        errors.append("Repository truth embedded platform gate disagrees with the roadmap")
    authority_stack = truth.get("authority_stack", {})
    expected_stack = {
        "game_layer": "Where Ravens Wait: Eternal Reckoning",
        "engine": "Yggdrasil World Engine",
        "foundation": "ASH Cosmological Model",
        "pattern_component": "ASH Pattern System",
    }
    for field, expected in expected_stack.items():
        if authority_stack.get(field) != expected:
            errors.append(f"Repository truth authority stack has incorrect {field}")
    ownership = truth.get("ownership", {})
    if ownership.get("legal_name") != "James Daley":
        errors.append("Repository truth legal owner must be James Daley")
    if set(ownership.get("recognized_aliases", [])) != {"Jim Daley"}:
        errors.append("Repository truth must record Jim Daley as the sole recognized owner alias")
    contact = ownership.get("commercial_contact", {})
    if contact.get("email") != "contact@ravenforgesoftware.com" or contact.get("purpose") != "commercial_licensing":
        errors.append("Repository truth commercial licensing contact is incorrect")
    for surface in ownership.get("identity_surfaces", []):
        path_name = surface.get("path")
        path_errors = repository_path_errors(root, path_name, "Ownership identity surface")
        errors.extend(path_errors)
        if path_errors:
            continue
        text = (root / path_name).read_text(encoding=TEXT_ENCODING, errors="replace")
        form = surface.get("name_form")
        if form in {"legal", "legal_with_alias"} and "James Daley" not in text:
            errors.append(f"Ownership surface lacks legal name James Daley: {path_name}")
        if form in {"recognized_alias", "legal_with_alias"} and "Jim Daley" not in text:
            errors.append(f"Ownership surface lacks recognized alias Jim Daley: {path_name}")
    for path_name, marker in (("LICENSE", "James Daley"), ("CLA.md", "Jim Daley")):
        try:
            text = (root / path_name).read_text(encoding=TEXT_ENCODING)
            if marker not in text:
                errors.append(f"{path_name} does not identify {marker}")
        except OSError as exc:
            errors.append(f"Unable to inspect {path_name}: {exc}")
    for path_name in (
        truth.get("publication_policy_ref"),
        truth.get("classification_manifest_ref"),
        truth.get("scope_partition_manifest_ref"),
        truth.get("public_promise_register_ref"),
        truth.get("quality_debt_inventory_ref"),
    ):
        if path_name:
            errors.extend(repository_path_errors(root, path_name, "Repository truth authority reference"))
    gate_ref = truth.get("platform_gate_ref")
    if isinstance(gate_ref, str):
        path_name, pointer = split_repository_ref(gate_ref)
        errors.extend(repository_path_errors(root, path_name, "Repository truth platform gate reference"))
        if path_name == ROADMAP_PATH and pointer is not None:
            valid, value = resolve_json_pointer(roadmap, pointer)
            if not valid or not isinstance(value, dict):
                errors.append("Repository truth platform gate reference is unresolved")


def expected_public_surfaces(
    paths: Iterable[str],
    class_assignments: dict[str, dict[str, Any]],
    scope_assignments: dict[str, dict[str, Any]],
) -> set[str]:
    exact = {
        "README.md",
        "developer-guide.md",
        "wiki.md",
        "docs/master_specification/YWE_MASTER_SPECIFICATION.md",
        "docs/project/YWE_AGNOSTIC_SPECIFICATION_ROADMAP.md",
        "docs/project/repository_status.md",
        "CONTRIBUTING.md",
    }
    allowed_suffixes = {".md", ".json", ".yaml", ".yml"}
    prefixes = ("docs/game/", "data/game/", "adapters/")
    expected = {
        path
        for path in paths
        if path in exact or (path.startswith(prefixes) and Path(path).suffix.lower() in allowed_suffixes)
    }
    for path in set(class_assignments) | set(scope_assignments):
        tags = set(class_assignments.get(path, {}).get("secondary_tags", []))
        tags.update(scope_assignments.get(path, {}).get("secondary_tags", []))
        if "public_surface" in tags:
            expected.add(path)
    return expected


def validate_source_locator(root: Path, source_ref: dict[str, Any], errors: list[str]) -> None:
    path_name = source_ref.get("path")
    path_errors = repository_path_errors(root, path_name, "Public promise source")
    errors.extend(path_errors)
    if path_errors:
        return
    path = root / path_name
    locator_type = source_ref.get("locator_type")
    locator = source_ref.get("locator", "")
    if locator_type == "json_pointer":
        try:
            document = load_json(path)
            valid, _ = resolve_json_pointer(document, locator)
        except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
            errors.append(f"Unable to inspect promise JSON locator in {path_name}: {exc}")
            return
        if not valid:
            errors.append(f"Public promise JSON locator is unresolved: {path_name}#{locator}")
        return
    text = path.read_text(encoding=TEXT_ENCODING, errors="replace")
    if locator_type == "line_range":
        lines = text.splitlines()
        start = source_ref.get("line_start", 0)
        end = source_ref.get("line_end", 0)
        if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > len(lines):
            errors.append(f"Public promise line range is invalid for {path_name}: {start}-{end}")
        elif locator not in "\n".join(lines[start - 1 : end]):
            errors.append(f"Public promise locator text is absent from {path_name}:{start}-{end}")
    elif locator_type == "markdown_heading":
        components = [part.strip() for part in re.split(r"[;>]", locator) if part.strip()]
        normalized_text = " ".join(text.lower().split())
        missing = [part for part in components if " ".join(part.lower().split()) not in normalized_text]
        if missing:
            errors.append(f"Public promise heading locator is absent from {path_name}: {missing}")
    elif locator not in text:
        errors.append(f"Public promise locator is absent from {path_name}: {locator!r}")


def validate_promises(
    root: Path,
    paths: list[str],
    promises: dict[str, Any],
    roadmap: dict[str, Any],
    canonical_version: str,
    class_assignments: dict[str, dict[str, Any]],
    scope_assignments: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if promises.get("repository_baseline") != canonical_version:
        errors.append("Public promise register repository baseline does not match VERSION")
    if promises.get("publication_state") != roadmap.get("publication", {}).get("state"):
        errors.append("Public promise publication state disagrees with the roadmap")
    surfaces = promises.get("reviewed_surfaces", [])
    surface_paths = [item.get("path") for item in surfaces]
    duplicates = sorted(path for path, count in Counter(surface_paths).items() if count > 1)
    if duplicates:
        errors.append(f"Public promise register contains duplicate reviewed surfaces: {duplicates}")
    reviewed = set(surface_paths)
    expected = expected_public_surfaces(paths, class_assignments, scope_assignments)
    missing_surfaces = sorted(expected - reviewed)
    if missing_surfaces:
        errors.append(f"Public promise register has unreviewed public surfaces: {missing_surfaces}")
    for surface in surfaces:
        path_name = surface.get("path")
        path_errors = repository_path_errors(root, path_name, "Reviewed public surface")
        errors.extend(path_errors)
        if not path_errors:
            try:
                actual_hash = normalized_text_sha256(root / path_name)
            except UnicodeDecodeError as exc:
                errors.append(f"Reviewed public surface is not strict UTF-8: {path_name}: {exc}")
                continue
            if actual_hash != surface.get("sha256"):
                errors.append(f"Reviewed public surface hash is stale: {path_name}")
    if promises.get("reviewed_surface_aggregate_sha256") != reviewed_surface_digest(surfaces):
        errors.append("Public promise reviewed-surface aggregate hash is stale")

    records = promises.get("promises", [])
    identifiers = [record.get("promise_id") for record in records]
    duplicate_ids = sorted(item for item, count in Counter(identifiers).items() if count > 1)
    if duplicate_ids:
        errors.append(f"Public promise IDs are duplicated: {duplicate_ids}")
    milestone_ids = {item.get("id") for item in roadmap.get("milestones", [])}
    m10_complete = any(
        item.get("id") == "M10" and item.get("status") == "complete"
        for item in roadmap.get("milestones", [])
    )
    for record in records:
        promise_id = record.get("promise_id")
        disposition = record.get("disposition")
        milestones = record.get("milestones", [])
        if disposition not in {"milestone_assigned", "formally_excluded"}:
            errors.append(f"Public promise {promise_id} has unresolved or invalid disposition: {disposition!r}")
        unknown = sorted(set(milestones) - milestone_ids)
        if unknown:
            errors.append(f"Public promise {promise_id} references unknown milestones: {unknown}")
        if disposition == "milestone_assigned" and not milestones:
            errors.append(f"Public promise {promise_id} has no milestone assignment")
        if disposition == "formally_excluded":
            if milestones:
                errors.append(f"Excluded public promise {promise_id} must not assign milestones")
            if not record.get("exclusion_reason") or not record.get("exclusion_authority_ref"):
                errors.append(f"Excluded public promise {promise_id} lacks exclusion rationale or authority")
        if (
            record.get("claim_type") == "publication"
            and disposition == "milestone_assigned"
            and (not m10_complete or roadmap.get("publication", {}).get("state") == "unreleased")
            and "M10" not in milestones
        ):
            errors.append(
                f"Public promise {promise_id} is an active publication claim before the M10 publication gate"
            )
        for source_ref in record.get("source_refs", []):
            if source_ref.get("path") not in reviewed:
                errors.append(f"Public promise {promise_id} cites an unreviewed surface: {source_ref.get('path')}")
            validate_source_locator(root, source_ref, errors)

    assigned = sum(record.get("disposition") == "milestone_assigned" for record in records)
    excluded = sum(record.get("disposition") == "formally_excluded" for record in records)
    summary = promises.get("summary", {})
    expected_summary = {
        "reviewed_surface_count": len(surfaces),
        "promise_count": len(records),
        "assigned_count": assigned,
        "excluded_count": excluded,
        "unresolved_count": 0,
    }
    if summary != expected_summary:
        errors.append(f"Public promise summary is stale: recorded {summary}; actual {expected_summary}")


def roadmap_open_work(roadmap: dict[str, Any]) -> list[tuple[str, str, str]]:
    records: list[tuple[str, str, str]] = []
    for subsystem_index, subsystem in enumerate(roadmap.get("subsystems", [])):
        subsystem_id = subsystem.get("id", f"index-{subsystem_index}")
        for work_index, text in enumerate(subsystem.get("open_work", [])):
            pointer = f"/subsystems/{subsystem_index}/open_work/{work_index}"
            records.append((subsystem_id, text, pointer))
    return records


def validate_debt(
    root: Path,
    debt: dict[str, Any],
    roadmap: dict[str, Any],
    canonical_version: str,
    class_assignments: dict[str, dict[str, Any]],
    scope_assignments: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    if debt.get("repository_baseline") != canonical_version:
        errors.append("Quality debt inventory repository baseline does not match VERSION")
    subledger = debt.get("schema_debt_subledger", {})
    schema_path = root / SCHEMA_DEBT_PATH
    if not schema_path.is_file():
        errors.append(f"Missing schema debt sub-ledger: {SCHEMA_DEBT_PATH}")
        schema_document: dict[str, Any] = {}
    else:
        schema_document = load_json(schema_path)
        try:
            schema_debt_hash = normalized_text_sha256(schema_path)
        except UnicodeDecodeError as exc:
            errors.append(f"Schema debt sub-ledger is not strict UTF-8: {exc}")
            schema_debt_hash = None
        if subledger.get("sha256") != schema_debt_hash:
            errors.append("Quality debt schema sub-ledger hash is stale")
    known_debt = schema_document.get("known_debt", {}) if isinstance(schema_document, dict) else {}
    category_counts = {
        key: len(value) for key, value in known_debt.items() if isinstance(value, list)
    }
    occurrence_count = sum(category_counts.values())
    unique_path_count = len(
        {path for values in known_debt.values() if isinstance(values, list) for path in values}
    )
    if subledger.get("counts_by_category") != category_counts:
        errors.append("Quality debt schema category counts are stale")
    if subledger.get("category_occurrence_count") != occurrence_count:
        errors.append("Quality debt schema occurrence count is stale")
    if subledger.get("unique_path_count") != unique_path_count:
        errors.append("Quality debt schema unique-path count is stale")

    records = debt.get("debts", [])
    identifiers = [record.get("debt_id") for record in records]
    duplicate_ids = sorted(item for item, count in Counter(identifiers).items() if count > 1)
    if duplicate_ids:
        errors.append(f"Quality debt IDs are duplicated: {duplicate_ids}")
    by_id = {record.get("debt_id"): record for record in records}
    milestone_ids = {item.get("id") for item in roadmap.get("milestones", [])}
    m0_complete = next(
        (
            item.get("status") == "complete"
            for item in roadmap.get("milestones", [])
            if item.get("id") == "M0"
        ),
        False,
    )
    covered_roadmap_pointers: set[str] = set()
    for record in records:
        debt_id = record.get("debt_id")
        milestone = record.get("assigned_milestone")
        if record.get("status") == "open":
            if not record.get("owner_role"):
                errors.append(f"Open quality debt {debt_id} is missing owner_role")
            if not milestone:
                errors.append(f"Open quality debt {debt_id} is missing assigned_milestone")
        if milestone not in milestone_ids:
            errors.append(f"Quality debt {debt_id} references unknown milestone {milestone!r}")
        status = record.get("status")
        if status == "resolved" and not record.get("resolution_evidence"):
            errors.append(f"Resolved quality debt {debt_id} lacks resolution evidence")
        if status == "accepted_exception" and not record.get("accepted_exception_rationale"):
            errors.append(f"Accepted quality exception {debt_id} lacks rationale")
        for evidence_ref in record.get("resolution_evidence", []):
            if (
                not m0_complete
                and evidence_ref in M0_EVIDENCE_REFS
                and is_safe_repository_path(evidence_ref)
                and not (root / evidence_ref).exists()
            ):
                continue
            errors.extend(repository_path_errors(root, evidence_ref, f"Quality debt {debt_id} evidence"))
        for source_ref in record.get("source_refs", []):
            kind = source_ref.get("kind")
            path_name = source_ref.get("path")
            if path_name:
                errors.extend(repository_path_errors(root, path_name, f"Quality debt {debt_id} source"))
            if kind == "json_pointer" and path_name:
                try:
                    source_document = load_json(root / path_name)
                    valid, _ = resolve_json_pointer(source_document, source_ref.get("locator", ""))
                except (OSError, json.JSONDecodeError, DuplicateKeyError):
                    valid = False
                if not valid:
                    errors.append(f"Quality debt {debt_id} has unresolved JSON pointer source")
                elif path_name == ROADMAP_PATH:
                    covered_roadmap_pointers.add(source_ref.get("locator", ""))

    placeholder_paths = sorted(
        path for path, assignment in class_assignments.items() if assignment.get("classification") == "placeholder"
    )
    for path in placeholder_paths:
        debt_ref = class_assignments[path].get("debt_ref") or scope_assignments.get(path, {}).get("debt_ref")
        if debt_ref not in by_id:
            errors.append(f"Placeholder artifact {path} references unregistered debt {debt_ref!r}")
        elif by_id[debt_ref].get("status") == "resolved":
            errors.append(f"Placeholder artifact {path} references resolved debt {debt_ref}")

    open_work = roadmap_open_work(roadmap)
    missing_open_work = [pointer for _subsystem, _text, pointer in open_work if pointer not in covered_roadmap_pointers]
    if missing_open_work:
        errors.append(f"Roadmap open-work items lack debt records: {missing_open_work}")

    statuses = Counter(record.get("status") for record in records)
    by_milestone = Counter(record.get("assigned_milestone") or "<missing>" for record in records)
    summary = debt.get("summary", {})
    expected_scalar = {
        "total": len(records),
        "open": statuses.get("open", 0),
        "resolved": statuses.get("resolved", 0),
        "accepted_exception": statuses.get("accepted_exception", 0),
        "by_milestone": dict(sorted(by_milestone.items())),
        "placeholder_count": len(placeholder_paths),
        "roadmap_open_work_count": len(open_work),
        "placeholder_paths_sha256": nul_digest(placeholder_paths),
        "roadmap_open_work_sha256": nul_digest(
            f"{subsystem}:{text}" for subsystem, text, _pointer in open_work
        ),
    }
    if summary != expected_scalar:
        errors.append(f"Quality debt summary is stale: recorded {summary}; actual {expected_scalar}")
    if m0_complete:
        open_m0 = [record.get("debt_id") for record in records if record.get("status") == "open" and record.get("assigned_milestone") == "M0"]
        if open_m0:
            errors.append(f"M0 cannot complete with open M0 quality debt: {open_m0}")


def validate_source_inventories(
    root: Path,
    placeholder_paths: set[str],
    errors: list[str],
) -> None:
    paths = {
        "docs/project/source_inventory.md": "current source routing",
        "missing_source_documents.md": "placeholder summary",
        "SOURCE_AVAILABILITY_MANIFEST.md": "historical provenance",
    }
    texts: dict[str, str] = {}
    for path_name in paths:
        path = root / path_name
        if not path.is_file():
            errors.append(f"Missing source inventory: {path_name}")
            continue
        texts[path_name] = path.read_text(encoding=TEXT_ENCODING, errors="replace")
    classification_ref = "data/governance/artifact_classification_manifest.json"
    for path_name in ("docs/project/source_inventory.md", "missing_source_documents.md"):
        text = texts.get(path_name)
        if text is None:
            continue
        if classification_ref not in text:
            errors.append(f"{path_name} does not identify the current classification authority")
        counts = {int(value) for value in CURRENT_PLACEHOLDER_COUNT.findall(text)}
        if counts != {len(placeholder_paths)}:
            errors.append(
                f"{path_name} current placeholder count is stale or ambiguous: "
                f"recorded {sorted(counts)}; expected {len(placeholder_paths)}"
            )
    provenance = texts.get("SOURCE_AVAILABILITY_MANIFEST.md", "").lower()
    if provenance and "historical" not in provenance and "provenance" not in provenance:
        errors.append("SOURCE_AVAILABILITY_MANIFEST.md is not marked as historical provenance")


def workflow_run_commands(workflow_text: str) -> str:
    lines = workflow_text.splitlines()
    commands: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        match = re.match(r"^(\s*)run:\s*(.*)$", line)
        if match is None:
            index += 1
            continue
        indentation = len(match.group(1))
        value = match.group(2).strip()
        if value in {"|", "|-", "|+", ">", ">-", ">+"}:
            index += 1
            while index < len(lines):
                command_line = lines[index]
                if not command_line.strip():
                    index += 1
                    continue
                command_indentation = len(command_line) - len(command_line.lstrip())
                if command_indentation <= indentation:
                    break
                stripped = command_line.strip()
                if not stripped.startswith("#"):
                    commands.append(stripped)
                index += 1
            continue
        if value and not value.startswith("#"):
            commands.append(value)
        index += 1
    return "\n".join(commands)


def command_reads_repository_path(commands: str, path: str) -> bool:
    escaped_path = re.escape(path)
    readers = r"(?:cat|head|tail|[Gg]et-[Cc]ontent)"
    return bool(
        re.search(
            rf"(?m)\b{readers}\b(?:\s+--)?\s+[\"']?{escaped_path}(?=$|[\"'\s|;)])",
            commands,
        )
        or re.search(
            rf"(?m)<\s*[\"']?{escaped_path}(?=$|[\"'\s;)])",
            commands,
        )
    )


def validate_wiki_sync_version_authority(root: Path, errors: list[str]) -> None:
    workflow_path = root / WIKI_SYNC_WORKFLOW_PATH
    try:
        workflow_text = workflow_path.read_text(encoding=TEXT_ENCODING)
    except (OSError, UnicodeDecodeError) as exc:
        errors.append(f"Unable to inspect {WIKI_SYNC_WORKFLOW_PATH}: {exc}")
        return
    commands = workflow_run_commands(workflow_text)
    if not command_reads_repository_path(commands, "main-repo/VERSION"):
        errors.append("Active wiki-sync commands do not read canonical main-repo/VERSION")
    if command_reads_repository_path(commands, "main-repo/version.txt"):
        errors.append("Active wiki-sync commands read main-repo/version.txt as a value authority")


def validate_platform_and_identity_contracts(
    root: Path,
    roadmap: dict[str, Any],
    errors: list[str],
) -> None:
    gate = roadmap.get("platform_gate", {})
    m10_complete = next(
        (item.get("status") == "complete" for item in roadmap.get("milestones", []) if item.get("id") == "M10"),
        False,
    )
    gate_state = (gate.get("status"), gate.get("platform_work_authorized"))
    if not m10_complete and gate_state != ("deferred", False):
        errors.append("Platform work is authorized before M10 completion")
    if m10_complete and gate_state not in {("deferred", False), ("authorized", True)}:
        errors.append("Post-M10 platform gate status and authorization are inconsistent")
    policy_path = root / "repository-contribution-policy.json"
    try:
        policy = load_json(policy_path)
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"Unable to inspect contribution policy: {exc}")
        return
    if policy.get("legal_owner") != "James Daley":
        errors.append("Contribution policy legal_owner must be James Daley")
    aliases = set(policy.get("owner_aliases", []))
    if policy.get("owner") not in aliases or aliases != {"Jim Daley"}:
        errors.append("Contribution policy display owner must be the recognized alias Jim Daley")
    serialized = json.dumps(policy, sort_keys=True).lower()
    if re.search(r"branch\s*!={1,2}\s*main|branch\s+is\s+not\s+main", serialized):
        errors.append("Contribution policy incorrectly makes every non-main branch product implementation work")
    engine_mode = policy.get("operating_modes", {}).get("engine_repo_mode", {})
    if "downstream" not in json.dumps(engine_mode).lower() or "m10" not in json.dumps(engine_mode).lower():
        errors.append("Contribution policy engine mode is not constrained to downstream work after M10")
    spec_condition = policy.get("operating_modes", {}).get("spec_repo_mode", {}).get("applies_when")
    if spec_condition != "repository == flynn33/yggdrasil-world-engine on any branch":
        errors.append("Contribution policy must apply specification mode to every branch in this repository")
    engine_condition = engine_mode.get("applies_when")
    if engine_condition != (
        "repository != flynn33/yggdrasil-world-engine and M10 == complete "
        "and platform_work_authorized == true"
    ):
        errors.append("Contribution policy downstream engine-mode condition is not exact")
    expected_platform_gate = {
        "authorized_after": "M10",
        "status": gate.get("status"),
        "platform_work_authorized": gate.get("platform_work_authorized"),
        "downstream_repository_required": True,
    }
    if policy.get("platform_gate") != expected_platform_gate:
        errors.append("Contribution policy platform gate disagrees with the roadmap boundary")
    try:
        instructions = load_json(root / "yggdrasil-instructions.json")
        if instructions.get("project", {}).get("owner") not in {"James Daley", "Jim Daley"}:
            errors.append("Yggdrasil instructions use an unrecognized owner identity")
    except (OSError, json.JSONDecodeError, DuplicateKeyError) as exc:
        errors.append(f"Unable to inspect yggdrasil-instructions.json: {exc}")


def protected_phase_9_paths(root: Path, errors: list[str]) -> tuple[set[str], tuple[str, ...]]:
    contract = load_json_object(root, PHASE_8_9_REQUIRED_PATH, errors)
    if contract is None:
        return set(), ("examples/branch_reality/",)
    protected: set[str] = set()
    for group in ("phase_9_architecture_contracts", "phase_9_schemas", "phase_9_validation"):
        values = contract.get(group)
        if not isinstance(values, list):
            errors.append(f"{PHASE_8_9_REQUIRED_PATH} is missing protected group {group}")
            continue
        protected.update(value for value in values if isinstance(value, str))
    return protected, ("examples/branch_reality/",)


def protected_diff_errors(root: Path, base_ref: str) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    changed = changed_candidate_paths(root, base_ref, errors)
    protected, prefixes = protected_phase_9_paths(root, errors)
    hits = sorted(
        path for path in changed if path in protected or any(path.startswith(prefix) for prefix in prefixes)
    )
    if hits:
        errors.append(f"M0 diff modifies protected Phase 9 paths: {hits}")
    return errors, set(hits)


def repository_state_digest(root: Path, paths: Iterable[str], exclusions: set[str]) -> str:
    files = {
        relative_path: (root / relative_path).read_bytes()
        for relative_path in sorted(set(paths) - exclusions)
        if (root / relative_path).is_file()
    }
    return repository_state_digest_from_files(files, exclusions)


def repository_state_digest_from_files(files: dict[str, bytes], exclusions: set[str]) -> str:
    payload = b""
    for relative_path in sorted(set(files) - exclusions):
        payload += relative_path.encode("utf-8") + b"\0"
        payload += sha256_bytes(normalized_utf8_data(files[relative_path])).encode("ascii") + b"\0"
    return sha256_bytes(payload)


def checked_git_output(
    root: Path,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> bytes:
    result = run_git(root, args, env=env)
    if result.returncode != 0:
        raise OSError(f"git {' '.join(args)} failed ({result.returncode}): {git_error(result)}")
    return result.stdout


def parse_numstat_z(payload: bytes) -> dict[str, tuple[int | None, int | None]]:
    if not payload:
        return {}
    if not payload.endswith(b"\0"):
        raise ValueError("Git numstat output is not NUL terminated")
    records: dict[str, tuple[int | None, int | None]] = {}
    for raw_record in payload[:-1].split(b"\0"):
        fields = raw_record.split(b"\t", 2)
        if len(fields) != 3 or not fields[2]:
            raise ValueError("Git numstat output contains a malformed or renamed-path record")
        path = fields[2].decode("utf-8", errors="strict")
        if not is_safe_repository_path(path):
            raise ValueError(f"Git numstat output contains an unsafe path: {path!r}")
        if path in records:
            raise ValueError(f"Git numstat output contains a duplicate path: {path}")

        def count(value: bytes) -> int | None:
            if value == b"-":
                return None
            decoded = value.decode("ascii", errors="strict")
            if not decoded.isdigit():
                raise ValueError(f"Git numstat output contains an invalid count: {decoded!r}")
            return int(decoded)

        records[path] = (count(fields[0]), count(fields[1]))
    return records


def implementation_diff_state(
    root: Path,
    base_ref: str,
    *,
    snapshot_ref: str | None = None,
) -> dict[str, Any]:
    """Build a complete implementation diff through an isolated temporary Git index."""
    base_sha = resolved_git_commit(root, base_ref)
    snapshot_sha = resolved_git_commit(root, snapshot_ref) if snapshot_ref is not None else None
    with tempfile.TemporaryDirectory(prefix="ywe-m0-index-") as directory:
        index_path = Path(directory) / "index"
        environment = os.environ.copy()
        environment["GIT_INDEX_FILE"] = str(index_path)
        environment["LC_ALL"] = "C"
        environment["LANG"] = "C"
        checked_git_output(root, ["read-tree", base_sha], env=environment)
        if snapshot_sha is None:
            checked_git_output(root, ["add", "-A", "--", "."], env=environment)
        else:
            checked_git_output(root, ["read-tree", snapshot_sha], env=environment)
        for excluded_path in sorted(M0_DIGEST_EXCLUSIONS):
            base_entry = run_git(root, ["cat-file", "-e", f"{base_sha}:{excluded_path}"])
            if base_entry.returncode == 0:
                checked_git_output(
                    root,
                    ["restore", "--staged", f"--source={base_sha}", "--", excluded_path],
                    env=environment,
                )
            else:
                checked_git_output(
                    root,
                    ["update-index", "--force-remove", "--", excluded_path],
                    env=environment,
                )
        checked_git_output(root, ["write-tree"], env=environment)
        name_status = checked_git_output(
            root,
            ["diff", "--cached", "--name-status", "-z", "--find-renames", base_sha, "--"],
            env=environment,
        )
        records = parse_name_status_z(name_status)
        counts = {
            "files_created": 0,
            "files_patched": 0,
            "files_deleted": 0,
            "files_renamed": 0,
        }
        for status, record_paths in records:
            for path in record_paths:
                if not is_safe_repository_path(path):
                    raise ValueError(f"Git diff contains an unsafe path: {path!r}")
            kind = status[:1]
            if kind in {"A", "C"}:
                counts["files_created"] += 1
            elif kind == "D":
                counts["files_deleted"] += 1
            elif kind == "R":
                counts["files_renamed"] += 1
            else:
                counts["files_patched"] += 1
        binary_diff = checked_git_output(
            root,
            ["diff", "--cached", "--binary", "--no-ext-diff", base_sha, "--"],
            env=environment,
        )
        shortstat = checked_git_output(
            root,
            ["diff", "--cached", "--shortstat", base_sha, "--"],
            env=environment,
        ).decode("utf-8", errors="strict").strip()
        numstat = parse_numstat_z(
            checked_git_output(
                root,
                ["diff", "--cached", "--numstat", "-z", "--no-renames", base_sha, "--"],
                env=environment,
            )
        )
    return {
        "base_sha": base_sha,
        "snapshot_sha": snapshot_sha,
        **counts,
        "diff_stat": shortstat,
        "diff_hash": sha256_bytes(binary_diff),
        "numstat": numstat,
    }


def original_text_line_count(root: Path, base_sha: str, path: str) -> int | None:
    result = run_git(root, ["cat-file", "blob", f"{base_sha}:{path}"])
    if result.returncode != 0:
        return None
    text = normalized_utf8_data(result.stdout).decode("utf-8", errors="strict")
    return len(text.splitlines())


def automatic_change_budget_limits(path: str) -> tuple[float, float]:
    low_risk = (
        path == "CHANGELOG.md"
        or path.startswith(".github/ISSUE_TEMPLATE/")
        or path == ".github/PULL_REQUEST_TEMPLATE.md"
        or path.endswith("/README.md")
    )
    medium_risk = (
        path in {"developer-guide.md", "guide.md"}
        or path.startswith("adapters/")
        or path.startswith("docs/architecture/")
    )
    if low_risk:
        return 20.0, 35.0
    if medium_risk:
        return 15.0, 25.0
    return 15.0, 20.0


def expected_change_budget_entries(
    root: Path,
    base_sha: str,
    numstat: dict[str, tuple[int | None, int | None]],
) -> tuple[dict[str, dict[str, int | float]], list[str]]:
    expected: dict[str, dict[str, int | float]] = {}
    errors: list[str] = []
    for path, (additions, deletions) in sorted(numstat.items()):
        if Path(path).suffix.lower() != ".md":
            continue
        try:
            original_lines = original_text_line_count(root, base_sha, path)
        except UnicodeDecodeError as exc:
            errors.append(f"Unable to score Markdown change budget for {path}: {exc}")
            continue
        if original_lines is None:
            continue
        if additions is None or deletions is None:
            errors.append(f"Markdown change budget cannot score binary diff counts: {path}")
            continue
        percentage = round((additions + deletions) / max(1, original_lines) * 100.0, 2)
        if path in M0_PREAUTHORIZED_CHANGE_BUDGETS:
            authorized_ceiling = M0_PREAUTHORIZED_CHANGE_BUDGETS[path]
            requires_exception = True
        else:
            normal_ceiling, authorized_ceiling = automatic_change_budget_limits(path)
            requires_exception = percentage > normal_ceiling
        if percentage > authorized_ceiling:
            errors.append(
                f"Markdown change budget exceeds authorized ceiling for {path}: "
                f"{percentage:.2f}% > {authorized_ceiling:.2f}%"
            )
        if requires_exception:
            expected[path] = {
                "original_lines": original_lines,
                "additions": additions,
                "deletions": deletions,
                "percentage": percentage,
                "authorized_ceiling": authorized_ceiling,
            }
    return expected, errors


def validate_change_budget_entries(
    root: Path,
    base_sha: str,
    numstat: dict[str, tuple[int | None, int | None]],
    recorded_entries: Any,
    errors: list[str],
) -> None:
    expected, budget_errors = expected_change_budget_entries(root, base_sha, numstat)
    errors.extend(budget_errors)
    if not isinstance(recorded_entries, list):
        errors.append("M0 acceptance change-budget ledger must be an array")
        return
    recorded_by_path: dict[str, dict[str, Any]] = {}
    for entry in recorded_entries:
        if not isinstance(entry, dict):
            errors.append("M0 acceptance change-budget ledger contains a non-object entry")
            continue
        path = entry.get("path")
        if not is_safe_repository_path(path):
            errors.append(f"M0 acceptance change-budget ledger contains an unsafe path: {path!r}")
            continue
        if path in recorded_by_path:
            errors.append(f"M0 acceptance change-budget ledger contains duplicate path {path}")
            continue
        recorded_by_path[path] = entry
    if set(recorded_by_path) != set(expected):
        errors.append(
            "M0 acceptance change-budget ledger paths are stale: "
            f"recorded {sorted(recorded_by_path)}; expected {sorted(expected)}"
        )
    for path in sorted(set(recorded_by_path) & set(expected)):
        entry = recorded_by_path[path]
        expected_fields = expected[path]
        for field in ("original_lines", "additions", "deletions"):
            if entry.get(field) != expected_fields[field]:
                errors.append(
                    f"M0 acceptance change-budget {field} is stale for {path}: "
                    f"recorded {entry.get(field)!r}; expected {expected_fields[field]!r}"
                )
        for field in ("percentage", "authorized_ceiling"):
            value = entry.get(field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or abs(float(value) - float(expected_fields[field])) > 1e-9
            ):
                errors.append(
                    f"M0 acceptance change-budget {field} is stale for {path}: "
                    f"recorded {value!r}; expected {expected_fields[field]!r}"
                )
        if entry.get("result") != "within_authorized_ceiling":
            errors.append(f"M0 acceptance change-budget result is not passing for {path}")


def repository_files_at_ref(root: Path, ref: str) -> dict[str, bytes]:
    result = run_git(root, ["archive", "--format=tar", ref])
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise OSError(f"unable to archive {ref}: {detail}")
    files: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            if not is_safe_repository_path(member.name):
                raise ValueError(f"Git archive contains an unsafe path: {member.name!r}")
            extracted = archive.extractfile(member)
            if extracted is None:
                raise OSError(f"unable to read archived file: {member.name}")
            files[member.name] = extracted.read()
    return files


def evidence_introduction_ref(root: Path) -> str | None:
    result = run_git(root, ["log", "--diff-filter=A", "--format=%H", "--", EVIDENCE_PATH])
    if result.returncode != 0:
        return None
    commits = [line for line in result.stdout.decode("ascii", errors="replace").splitlines() if line]
    return commits[0] if commits else None


def json_object_from_bytes(value: bytes, label: str) -> dict[str, Any]:
    document = json.loads(
        value.decode("utf-8-sig", errors="strict"),
        object_pairs_hook=unique_object,
    )
    if not isinstance(document, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return document


def markdown_h2_sections(document: str) -> tuple[list[str], dict[str, str]]:
    matches = list(re.finditer(r"(?m)^##[ \t]+([^\r\n]+?)[ \t]*$", document))
    headings = [match.group(1) for match in matches]
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(document)
        sections.setdefault(match.group(1), document[match.end() : end].strip())
    return headings, sections


def acceptance_metric_pairs(evidence: dict[str, Any]) -> list[tuple[str, Any]]:
    classification = evidence.get("classification_metrics", {})
    promises = evidence.get("promise_metrics", {})
    debt = evidence.get("debt_metrics", {})
    return [
        ("Tracked paths", classification.get("tracked_paths")),
        ("Classified paths", classification.get("classified_paths")),
        ("Unclassified paths", classification.get("unclassified_paths")),
        ("Multiply classified paths", classification.get("multiply_classified_paths")),
        ("Normative", classification.get("normative")),
        ("Informative", classification.get("informative")),
        ("Example", classification.get("example")),
        ("Historical", classification.get("historical")),
        ("Deprecated", classification.get("deprecated")),
        ("Superseded", classification.get("superseded")),
        ("Placeholder", classification.get("placeholder")),
        ("Reviewed public surfaces", promises.get("reviewed_surfaces")),
        ("Public promises", promises.get("total")),
        ("Assigned", promises.get("assigned")),
        ("Excluded", promises.get("excluded")),
        ("Unresolved", promises.get("unresolved")),
        ("Debt records", debt.get("total")),
        ("Open debt", debt.get("open")),
        ("Accepted exceptions", debt.get("accepted_exception")),
        ("Resolved debt", debt.get("resolved")),
    ]


def markdown_validation_contexts(section: str) -> tuple[list[str], dict[str, list[str]]]:
    matches = list(re.finditer(r"(?m)^###[ \t]+(local|pull_request) context[ \t]*$", section))
    contexts = [match.group(1) for match in matches]
    check_ids: dict[str, list[str]] = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(section)
        body = section[match.end() : end]
        check_ids[match.group(1)] = re.findall(
            r"(?m)^\|[ \t]*`([^`]+)`[ \t]*\|",
            body,
        )
    return contexts, check_ids


def acceptance_document_errors(document: str, evidence: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not document.strip():
        return ["M0 acceptance Markdown is empty"]
    headings, sections = markdown_h2_sections(document)
    if headings != list(ACCEPTANCE_REQUIRED_HEADINGS):
        errors.append(
            "M0 acceptance Markdown H2 headings must be exactly "
            f"{list(ACCEPTANCE_REQUIRED_HEADINGS)}; found {headings}"
        )
    for heading in ACCEPTANCE_REQUIRED_HEADINGS:
        if not sections.get(heading, "").strip():
            errors.append(f"M0 acceptance Markdown section is empty: {heading}")

    baseline = evidence.get("baseline", {})
    expected_baseline_claims = (
        f"Base ref: `{baseline.get('base_ref')}`",
        f"Base SHA: `{baseline.get('base_sha')}`",
        f"Working branch: `{baseline.get('branch')}`",
        f"Repository baseline version: `{baseline.get('repository_version')}`",
    )
    baseline_section = sections.get("Baseline", "")
    missing_baseline = [claim for claim in expected_baseline_claims if claim not in baseline_section]
    if missing_baseline:
        errors.append(
            f"M0 acceptance Markdown baseline does not match JSON evidence: {missing_baseline}"
        )

    authority_section = sections.get("Authority and Phase Alignment", "")
    if not re.search(
        r"(?m)^\|[ \t]*Protected Phase 9 paths changed[ \t]*\|[ \t]*NO[ \t]*\|",
        authority_section,
    ):
        errors.append("M0 acceptance Markdown lacks the protected-path NO authority result")

    deliverables_section = sections.get("M0 Deliverables", "")
    if not re.search(r"(?m)^\|[^\r\n]+\|[ \t]*PASS[ \t]*\|", deliverables_section):
        errors.append("M0 acceptance Markdown has no passing M0 deliverable")

    criteria_section = sections.get("M0 Exit Criteria", "")
    criteria_results = re.findall(
        r"(?m)^\|[ \t]*(?!Exit criterion\b|---)([^|]+?)\s*\|[ \t]*(PASS|FAIL)[ \t]*\|",
        criteria_section,
    )
    expected_criteria_count = len(evidence.get("exit_criteria", []))
    if len(criteria_results) != expected_criteria_count or any(
        outcome != "PASS" for _label, outcome in criteria_results
    ):
        errors.append("M0 acceptance Markdown exit-criterion results do not match JSON evidence")

    metric_section = sections.get("Coverage Counts", "")
    actual_metrics = [
        (label, int(value))
        for label, value in re.findall(
            r"(?m)^([A-Za-z][A-Za-z ]+):[ \t]*([0-9]+)[ \t]*$",
            metric_section,
        )
    ]
    expected_metrics = acceptance_metric_pairs(evidence)
    if actual_metrics != expected_metrics:
        errors.append("M0 acceptance Markdown headline metrics do not exactly match JSON evidence")

    gate_section = sections.get("Gate Results", "")
    actual_gates = re.findall(
        r"(?m)^\|[ \t]*(9\.[3-8])\b[^|]*\|[ \t]*(PASS|FAIL)[ \t]*\|",
        gate_section,
    )
    expected_gates = [(item.get("id"), "PASS") for item in evidence.get("foundation_gates", [])]
    if actual_gates != expected_gates:
        errors.append("M0 acceptance Markdown gate results do not match JSON evidence")

    validation_section = sections.get("Validation Results", "")
    actual_contexts, actual_check_ids = markdown_validation_contexts(validation_section)
    expected_contexts = [run.get("context") for run in evidence.get("validation_runs", [])]
    if actual_contexts != expected_contexts:
        errors.append("M0 acceptance Markdown validation contexts do not match JSON evidence")
    for run in evidence.get("validation_runs", []):
        context = run.get("context")
        expected_ids = [result.get("check_id") for result in run.get("results", [])]
        if actual_check_ids.get(context) != expected_ids:
            errors.append(
                f"M0 acceptance Markdown {context} check IDs do not match JSON evidence"
            )

    diff_section = sections.get("Diff Review", "")
    if not re.search(
        r"(?mi)^\s*-[ \t]*Protected Phase 9 path diff:[ \t]*empty\.[ \t]*$",
        diff_section,
    ):
        errors.append("M0 acceptance Markdown protected-path diff result is not empty")

    judgment_section = sections.get("Acceptance Judgment", "")
    claim_prefixes = tuple(line.split(":", 1)[0] + ":" for line in ACCEPTANCE_JUDGMENT_LINES)
    judgment_claims: list[str] = []
    for raw_line in judgment_section.splitlines():
        line = raw_line.strip().strip("`").strip()
        line = re.sub(r"^(?:[-*+]|>)[ \t]+", "", line)
        if line.startswith(claim_prefixes):
            judgment_claims.append(line)
    if judgment_claims != list(ACCEPTANCE_JUDGMENT_LINES):
        errors.append("M0 acceptance Markdown judgment is missing, contradictory, or misleading")

    deferred_section = sections.get("Deferred Work", "")
    if "M1-M10" not in deferred_section or "unauthorized until M10 acceptance" not in deferred_section:
        errors.append("M0 acceptance Markdown deferred-work boundary is incomplete")
    return errors


def transition_errors(root: Path, roadmap: dict[str, Any]) -> list[str]:
    """Validate the evidence/status relationship used by the roadmap bootstrap check."""
    errors: list[str] = []
    by_id = {item.get("id"): item for item in roadmap.get("milestones", [])}
    m0 = by_id.get("M0", {})
    m1 = by_id.get("M1", {})
    if m1.get("status") == "in_progress" and m0.get("status") != "complete":
        errors.append("M1 cannot be in progress while M0 is incomplete")
    if m0.get("status") != "complete":
        return errors
    if m0.get("acceptance_evidence") != M0_EVIDENCE_REFS:
        errors.append(f"Completed M0 must reference exactly {M0_EVIDENCE_REFS}")
    if m1.get("status") not in {"in_progress", "complete"}:
        errors.append("Completed M0 requires M1 to have been activated")
    current_milestone = roadmap.get("current_milestone")
    if current_milestone == "M0":
        errors.append("Completed M0 cannot remain the current milestone")
    evidence = load_json_object(root, EVIDENCE_PATH, errors)
    schema = load_json_object(root, INSTANCE_SCHEMAS[EVIDENCE_PATH], errors)
    if evidence is None or schema is None:
        return errors
    errors.extend(schema_validation_errors(evidence, schema, EVIDENCE_PATH))
    if evidence.get("milestone_id") != "M0" or evidence.get("outcome") != "pass":
        errors.append("Completed M0 requires passing M0 acceptance evidence")
    if evidence.get("unresolved_issues"):
        errors.append("Completed M0 acceptance evidence contains unresolved issues")
    transition = evidence.get("roadmap_transition", {})
    if transition != {
        "completed_milestone": "M0",
        "activated_milestone": "M1",
        "current_milestone": "M1",
    }:
        errors.append("M0 acceptance evidence does not record the M0-to-M1 transition")
    if not (root / ACCEPTANCE_DOCUMENT_PATH).is_file():
        errors.append(f"Completed M0 is missing {ACCEPTANCE_DOCUMENT_PATH}")
    return errors


def validate_acceptance_evidence(
    root: Path,
    paths: list[str],
    evidence: dict[str, Any] | None,
    roadmap: dict[str, Any],
    base_ref: str,
    protected_hits: set[str],
    errors: list[str],
    *,
    classification: dict[str, Any] | None = None,
    scope: dict[str, Any] | None = None,
    promise_register: dict[str, Any] | None = None,
    debt_inventory: dict[str, Any] | None = None,
) -> None:
    by_id = {item.get("id"): item for item in roadmap.get("milestones", [])}
    if evidence is None:
        if by_id.get("M0", {}).get("status") == "complete":
            errors.append("Completed M0 is missing acceptance evidence")
        return
    snapshot_ref = evidence_introduction_ref(root)
    snapshot_files: dict[str, bytes] | None = None
    document_evidence = evidence
    acceptance_document_data: bytes | None = None
    metric_paths = paths
    evidence_roadmap = roadmap
    if snapshot_ref is not None:
        try:
            snapshot_files = repository_files_at_ref(root, snapshot_ref)
        except (OSError, UnicodeDecodeError, ValueError, tarfile.TarError) as exc:
            errors.append(f"Unable to load the immutable M0 acceptance snapshot: {exc}")
        if snapshot_files is not None:
            for path_name in M0_EVIDENCE_REFS:
                historical = snapshot_files.get(path_name)
                current_path = root / path_name
                if historical is None:
                    errors.append(f"M0 acceptance snapshot omits {path_name}")
                    continue
                if not current_path.is_file():
                    errors.append(f"M0 acceptance artifact is missing: {path_name}")
                    continue
                try:
                    unchanged = normalized_utf8_data(historical) == normalized_utf8_bytes(current_path)
                except UnicodeDecodeError as exc:
                    errors.append(f"M0 acceptance artifact is not strict UTF-8: {path_name}: {exc}")
                    continue
                if not unchanged:
                    errors.append(f"M0 acceptance artifact changed after its introduction: {path_name}")
            snapshot_documents: list[tuple[str, str]] = [
                (ROADMAP_PATH, "roadmap"),
                (CLASSIFICATION_PATH, "classification"),
                (SCOPE_PATH, "scope"),
                (PROMISE_PATH, "promise"),
                (DEBT_PATH, "debt"),
            ]
            for path_name, document_kind in snapshot_documents:
                if path_name not in snapshot_files:
                    continue
                try:
                    snapshot_document = json_object_from_bytes(snapshot_files[path_name], path_name)
                except (UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
                    errors.append(f"Unable to load {path_name} from the M0 acceptance snapshot: {exc}")
                    continue
                if document_kind == "roadmap":
                    evidence_roadmap = snapshot_document
                elif document_kind == "classification":
                    classification = snapshot_document
                    metric_paths = sorted(snapshot_files)
                elif document_kind == "scope":
                    scope = snapshot_document
                elif document_kind == "promise":
                    promise_register = snapshot_document
                else:
                    debt_inventory = snapshot_document
            try:
                document_evidence = json_object_from_bytes(
                    snapshot_files[EVIDENCE_PATH],
                    EVIDENCE_PATH,
                )
            except (KeyError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
                errors.append(f"Unable to load M0 JSON evidence from its introduction snapshot: {exc}")
            acceptance_document_data = snapshot_files.get(ACCEPTANCE_DOCUMENT_PATH)
    if snapshot_files is None:
        try:
            acceptance_document_data = (root / ACCEPTANCE_DOCUMENT_PATH).read_bytes()
        except OSError as exc:
            errors.append(f"Unable to read {ACCEPTANCE_DOCUMENT_PATH}: {exc}")
    if acceptance_document_data is not None:
        try:
            acceptance_document = normalized_utf8_data(acceptance_document_data).decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"M0 acceptance Markdown is not strict UTF-8: {exc}")
        else:
            errors.extend(acceptance_document_errors(acceptance_document, document_evidence))
    if evidence.get("artifact_version") != EVIDENCE_ARTIFACT_VERSION:
        errors.append(
            "M0 acceptance evidence artifact version must be "
            f"{EVIDENCE_ARTIFACT_VERSION}"
        )
    if evidence.get("milestone_id") != "M0":
        errors.append("M0 acceptance evidence has an incorrect milestone identifier")
    if evidence.get("outcome") == "pass":
        if evidence.get("unresolved_issues"):
            errors.append("Passing M0 acceptance evidence must have no unresolved issues")
        if evidence.get("source_inventory_result") != "pass":
            errors.append("Passing M0 acceptance evidence requires source inventory reconciliation")
    baseline = evidence.get("baseline", {})
    if baseline.get("base_ref") != base_ref:
        errors.append("M0 acceptance baseline uses the wrong base ref")
    try:
        if snapshot_files is not None:
            version_source = snapshot_files["VERSION"]
            canonical_version = normalized_utf8_data(version_source).decode("utf-8").strip()
        else:
            canonical_version = (root / "VERSION").read_text(encoding=TEXT_ENCODING).strip()
    except (KeyError, OSError, UnicodeDecodeError) as exc:
        errors.append(f"Unable to verify M0 acceptance repository version: {exc}")
    else:
        if baseline.get("repository_version") != canonical_version:
            errors.append("M0 acceptance baseline repository version is stale")
    recorded_base_sha = baseline.get("base_sha", "")
    verification_head_ref = snapshot_ref or "HEAD"
    verified_base_sha: str | None = None
    try:
        verification_head_sha = resolved_git_commit(root, verification_head_ref)
        if snapshot_ref is None:
            expected_base_sha = resolved_git_commit(root, base_ref)
            if recorded_base_sha != expected_base_sha:
                errors.append(
                    "M0 acceptance baseline SHA does not equal the resolved base ref: "
                    f"recorded {recorded_base_sha!r}; expected {expected_base_sha}"
                )
            verified_base_sha = expected_base_sha
        else:
            expected_base_sha = resolved_git_commit(root, f"{snapshot_ref}^1")
            if recorded_base_sha != expected_base_sha:
                errors.append(
                    "M0 acceptance baseline SHA does not equal the immutable evidence-introduction "
                    f"parent: recorded {recorded_base_sha!r}; expected {expected_base_sha}"
                )
            verified_base_sha = expected_base_sha
        ancestry_result = run_git(
            root,
            ["merge-base", "--is-ancestor", verified_base_sha, verification_head_sha],
        )
        if ancestry_result.returncode != 0:
            errors.append("M0 acceptance baseline SHA is not an ancestor of the verified implementation state")
        expected_merge_base = git_merge_base(root, verified_base_sha, verification_head_sha)
        if baseline.get("merge_base") != expected_merge_base:
            errors.append(
                "M0 acceptance merge base is stale: "
                f"recorded {baseline.get('merge_base')!r}; expected {expected_merge_base}"
            )
        expected_tags = git_tags(root, verification_head_sha)
        if baseline.get("tags_at_head") != expected_tags:
            errors.append(
                "M0 acceptance tags_at_head is stale: "
                f"recorded {baseline.get('tags_at_head')!r}; expected {expected_tags}"
            )
        if snapshot_ref is None:
            expected_branch = git_current_branch(root)
            if baseline.get("branch") != expected_branch:
                errors.append(
                    "M0 acceptance branch is stale: "
                    f"recorded {baseline.get('branch')!r}; expected {expected_branch!r}"
                )
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        errors.append(f"Unable to verify M0 acceptance Git baseline: {exc}")
    expected_publication_state = evidence_roadmap.get("publication", {}).get("state")
    if baseline.get("publication_state") != expected_publication_state:
        errors.append("M0 acceptance publication state disagrees with the roadmap snapshot")
    expected_platform_authorized = evidence_roadmap.get("platform_gate", {}).get(
        "platform_work_authorized"
    )
    if baseline.get("platform_work_authorized") != expected_platform_authorized:
        errors.append("M0 acceptance platform authorization disagrees with the roadmap snapshot")
    criteria = evidence.get("exit_criteria", [])
    if len(criteria) != 3 or any(item.get("outcome") != "pass" for item in criteria):
        errors.append("M0 acceptance evidence must record exactly three passing exit criteria")
    gates = evidence.get("foundation_gates", [])
    gate_ids = [item.get("id") for item in gates]
    if set(gate_ids) != FOUNDATION_GATES or len(gate_ids) != len(FOUNDATION_GATES):
        errors.append("M0 acceptance evidence must record gates 9.3 through 9.8 exactly once")
    if any(item.get("outcome") != "pass" for item in gates):
        errors.append("M0 acceptance evidence contains a failed foundation gate")
    if evidence.get("protected_path_diff", {}).get("changed_paths") or protected_hits:
        errors.append("M0 acceptance evidence records a protected Phase 9 path change")
    if evidence.get("protected_path_diff", {}).get("base_ref") != base_ref:
        errors.append("M0 acceptance evidence protected diff uses the wrong base ref")
    if classification is not None:
        class_counts = classification.get("coverage", {}).get("counts_by_class", {})
        expected_classification_metrics = {
            "tracked_paths": len(metric_paths),
            "classified_paths": sum(class_counts.values()),
            "unclassified_paths": 0,
            "multiply_classified_paths": 0,
            **class_counts,
        }
        if evidence.get("classification_metrics") != expected_classification_metrics:
            errors.append("M0 acceptance classification metrics are stale")
    if scope is not None:
        scope_counts = scope.get("coverage", {}).get("counts_by_partition", {})
        expected_scope_metrics = {
            partition: scope_counts.get(partition, 0)
            for partition in sorted(SCOPE_PARTITIONS)
        }
        if evidence.get("scope_metrics") != expected_scope_metrics:
            errors.append("M0 acceptance scope metrics are stale")
    if promise_register is not None:
        promise_summary = promise_register.get("summary", {})
        expected_promise_metrics = {
            "reviewed_surfaces": promise_summary.get("reviewed_surface_count", 0),
            "total": promise_summary.get("promise_count", 0),
            "assigned": promise_summary.get("assigned_count", 0),
            "excluded": promise_summary.get("excluded_count", 0),
            "unresolved": promise_summary.get("unresolved_count", 0),
        }
        if evidence.get("promise_metrics") != expected_promise_metrics:
            errors.append("M0 acceptance public-promise metrics are stale")
        expected_promise_source_evidence = {
            "register_ref": PROMISE_PATH,
            "hash_algorithm": NORMALIZED_TEXT_SHA256_ALGORITHM,
            "source_hash_count": len(promise_register.get("reviewed_surfaces", [])),
            "reviewed_surface_aggregate_sha256": promise_register.get(
                "reviewed_surface_aggregate_sha256"
            ),
        }
        if evidence.get("promise_source_evidence") != expected_promise_source_evidence:
            errors.append("M0 acceptance public-promise source evidence is stale")
    if debt_inventory is not None:
        debt_summary = debt_inventory.get("summary", {})
        expected_debt_metrics = {
            "total": debt_summary.get("total", 0),
            "open": debt_summary.get("open", 0),
            "accepted_exception": debt_summary.get("accepted_exception", 0),
            "resolved": debt_summary.get("resolved", 0),
            **{
                f"milestone_m{number}": debt_summary.get("by_milestone", {}).get(f"M{number}", 0)
                for number in range(11)
            },
        }
        if evidence.get("debt_metrics") != expected_debt_metrics:
            errors.append("M0 acceptance quality-debt metrics are stale")
    exclusions = set(evidence.get("digest_exclusions", []))
    if exclusions != M0_DIGEST_EXCLUSIONS:
        errors.append(f"M0 acceptance digest exclusions must be exactly {sorted(M0_DIGEST_EXCLUSIONS)}")
    try:
        if snapshot_files is not None:
            actual_digest = repository_state_digest_from_files(snapshot_files, exclusions)
        else:
            actual_digest = repository_state_digest(root, paths, exclusions)
    except UnicodeDecodeError as exc:
        errors.append(f"M0 repository-state digest encountered non-UTF-8 content: {exc}")
        actual_digest = None
    if evidence.get("repository_state_digest") != actual_digest:
        errors.append("M0 acceptance repository-state digest is stale")
    diff_review = evidence.get("diff_review", {})
    if diff_review.get("base_ref") != base_ref:
        errors.append("M0 acceptance diff review uses the wrong base ref")
    if diff_review.get("implementation_tree_hash") != evidence.get("repository_state_digest"):
        errors.append("M0 acceptance implementation tree hash must equal the repository-state digest")
    if diff_review.get("implementation_tree_hash") != actual_digest:
        errors.append("M0 acceptance implementation tree hash is stale")
    if diff_review.get("implementation_tree_hash_algorithm") != REPOSITORY_STATE_DIGEST_ALGORITHM:
        errors.append("M0 acceptance implementation tree hash uses the wrong algorithm")
    if diff_review.get("diff_hash_algorithm") != DIFF_HASH_ALGORITHM:
        errors.append("M0 acceptance diff hash uses the wrong algorithm")
    diff_state: dict[str, Any] | None = None
    if verified_base_sha is not None:
        try:
            diff_state = implementation_diff_state(
                root,
                verified_base_sha,
                snapshot_ref=snapshot_ref,
            )
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            errors.append(f"Unable to recompute the M0 implementation diff: {exc}")
    if diff_state is not None:
        for field in (
            "files_created",
            "files_patched",
            "files_deleted",
            "files_renamed",
            "diff_stat",
            "diff_hash",
        ):
            if diff_review.get(field) != diff_state[field]:
                errors.append(
                    f"M0 acceptance diff-review {field} is stale: "
                    f"recorded {diff_review.get(field)!r}; expected {diff_state[field]!r}"
                )
        if diff_state["files_deleted"] != 0:
            errors.append("M0 implementation state contains a file deletion")
        if diff_state["files_renamed"] != 0:
            errors.append("M0 implementation state contains a file rename")
        validate_change_budget_entries(
            root,
            diff_state["base_sha"],
            diff_state["numstat"],
            diff_review.get("change_budget_exceptions"),
            errors,
        )
    catalog_path = root / CHECK_CATALOG_PATH
    try:
        if snapshot_files is not None:
            catalog_bytes = snapshot_files[CHECK_CATALOG_PATH]
            catalog_hash = sha256_bytes(normalized_utf8_data(catalog_bytes))
            catalog = json_object_from_bytes(catalog_bytes, CHECK_CATALOG_PATH)
        else:
            catalog_hash = normalized_text_sha256(catalog_path)
            catalog = load_json(catalog_path)
    except (KeyError, OSError, UnicodeDecodeError, json.JSONDecodeError, DuplicateKeyError, ValueError) as exc:
        errors.append(f"Unable to validate the M0 acceptance check catalog: {exc}")
        catalog_hash = None
        catalog = {"checks": []}
    if evidence.get("check_catalog", {}).get("sha256") != catalog_hash:
        errors.append("M0 acceptance check-catalog hash is stale")
    runs = evidence.get("validation_runs", [])
    contexts = [run.get("context") for run in runs]
    if contexts != ["local", "pull_request"]:
        errors.append(
            "M0 acceptance validation runs must record local then pull_request contexts exactly once"
        )
    for run in runs:
        context = run.get("context")
        expected_ids = [
            check.get("id")
            for check in catalog.get("checks", [])
            if "always" in check.get("contexts", []) or context in check.get("contexts", [])
        ]
        expected_checks = {
            check.get("id"): check
            for check in catalog.get("checks", [])
            if "always" in check.get("contexts", []) or context in check.get("contexts", [])
        }
        results = run.get("results", [])
        actual_ids = [result.get("check_id") for result in results]
        if actual_ids != expected_ids:
            errors.append(
                f"M0 acceptance {context} results do not match catalog order: {actual_ids}"
            )
        for result in results:
            expected_check = expected_checks.get(result.get("check_id"), {})
            if result.get("command") != expected_check.get("command"):
                errors.append(
                    f"M0 acceptance records a non-canonical check command: {result.get('check_id')}"
                )
            if result.get("exit_code") != 0 or result.get("outcome") != "pass":
                errors.append(
                    f"M0 acceptance records a non-passing check: {result.get('check_id')}"
                )
            result_summary = result.get("result_summary")
            if not isinstance(result_summary, str) or not result_summary.strip():
                errors.append(
                    f"M0 acceptance check lacks a concise result summary: {result.get('check_id')}"
                )
                continue
            if result.get("result_summary_hash_algorithm") != NORMALIZED_TEXT_SHA256_ALGORITHM:
                errors.append(
                    f"M0 acceptance check uses the wrong result-summary hash algorithm: {result.get('check_id')}"
                )
            actual_summary_hash = sha256_bytes(
                normalized_utf8_data(result_summary.encode("utf-8"))
            )
            if result.get("result_summary_sha256") != actual_summary_hash:
                errors.append(
                    f"M0 acceptance check result-summary hash is stale: {result.get('check_id')}"
                )


def validate_repository_truth(root: Path, base_ref: str) -> list[str]:
    errors: list[str] = []
    roadmap = load_json_object(root, ROADMAP_PATH, errors)
    if roadmap is None:
        return errors
    canonical_version, version_errors = canonical_version_errors(root, roadmap)
    errors.extend(version_errors)
    required = [CLASSIFICATION_PATH, SCOPE_PATH, TRUTH_PATH, RELEASE_POLICY_PATH, PROMISE_PATH, DEBT_PATH]
    evidence_exists = (root / EVIDENCE_PATH).is_file()
    if evidence_exists:
        required.append(EVIDENCE_PATH)
    documents = load_and_validate_instances(root, required, errors)
    paths = repository_candidate_paths(root, errors)

    classification = documents.get(CLASSIFICATION_PATH)
    scope = documents.get(SCOPE_PATH)
    class_assignments: dict[str, dict[str, Any]] = {}
    scope_assignments: dict[str, dict[str, Any]] = {}
    if classification is not None and scope is not None:
        class_assignments, scope_assignments = validate_classification_scope(
            root, paths, classification, scope, canonical_version, errors
        )

    truth = documents.get(TRUTH_PATH)
    debt_inventory = documents.get(DEBT_PATH)
    if truth is not None:
        validate_truth_manifest(root, truth, roadmap, canonical_version, errors)
    release_policy = documents.get(RELEASE_POLICY_PATH)
    if release_policy is not None:
        validate_release_policy(
            root,
            roadmap,
            release_policy,
            canonical_version,
            errors,
            debt_inventory,
        )
    promise_register = documents.get(PROMISE_PATH)
    if promise_register is not None:
        validate_promises(
            root,
            paths,
            promise_register,
            roadmap,
            canonical_version,
            class_assignments,
            scope_assignments,
            errors,
        )
    if debt_inventory is not None:
        validate_debt(
            root,
            debt_inventory,
            roadmap,
            canonical_version,
            class_assignments,
            scope_assignments,
            errors,
        )
    placeholder_paths = {
        path for path, assignment in class_assignments.items() if assignment.get("classification") == "placeholder"
    }
    validate_source_inventories(root, placeholder_paths, errors)
    validate_wiki_sync_version_authority(root, errors)
    validate_platform_and_identity_contracts(root, roadmap, errors)
    diff_errors, protected_hits = protected_diff_errors(root, base_ref)
    errors.extend(diff_errors)
    errors.extend(transition_errors(root, roadmap))
    validate_acceptance_evidence(
        root,
        paths,
        documents.get(EVIDENCE_PATH),
        roadmap,
        base_ref,
        protected_hits,
        errors,
        classification=classification,
        scope=scope,
        promise_register=promise_register,
        debt_inventory=debt_inventory,
    )
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=os.environ.get("BASE_REF", "origin/main"))
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors = validate_repository_truth(root, args.base)
    if errors:
        print("M0 truthful baseline check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("M0 truthful baseline check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
