#!/usr/bin/env python3
"""Validate the complete repository diff against the non-destructive policy."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

DEFAULT_POLICY = "data/validation/check_non_destructive_diff_source_truth.spec.json"
PROTECTED_PREFIXES = (
    "docs/",
    "core/",
    "modules/",
    "data/",
    "lore/",
    "specs/",
    "conformance/",
    "governance/",
)
SINGLE_PATH_STATUSES = frozenset({"A", "B", "D", "M", "T", "U", "X"})
SCORED_STATUS = re.compile(r"^[CR](?:0|[1-9][0-9]?|100)$")
WINDOWS_DRIVE = re.compile(r"^[A-Za-z]:")


@dataclass(frozen=True)
class ChangeRecord:
    status: str
    paths: tuple[str, ...]
    source: str


@dataclass
class ChangeSummary:
    added: set[str] = field(default_factory=set)
    deleted: set[str] = field(default_factory=set)
    modified: set[str] = field(default_factory=set)
    renamed: set[tuple[str, str]] = field(default_factory=set)


@dataclass
class DiffEvaluation:
    summary: ChangeSummary = field(default_factory=ChangeSummary)
    fatal_failures: list[str] = field(default_factory=list)
    policy_failures: list[str] = field(default_factory=list)


def git_executable() -> str:
    discovered = shutil.which("git")
    if discovered:
        return discovered
    windows_fallback = Path("C:/Program Files/Git/cmd/git.exe")
    if windows_fallback.is_file():
        return str(windows_fallback)
    return "git"


def int_policy_value(policy: dict, names: tuple[str, ...], default: int) -> int:
    for name in names:
        if name in policy:
            try:
                value = int(policy[name])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Non-destructive diff policy value {name} must be an integer: "
                    f"{policy[name]!r}"
                ) from exc
            if value < 0:
                raise ValueError(
                    f"Non-destructive diff policy value {name} must be non-negative: {value}"
                )
            return value
    return default


def policy_paths(policy: dict) -> tuple[str, ...]:
    configured_paths = policy.get("protected_paths", PROTECTED_PREFIXES)
    if not isinstance(configured_paths, list):
        raise ValueError("Non-destructive diff protected_paths must be an array")
    paths = tuple(path for path in configured_paths if isinstance(path, str) and path.strip())
    if len(paths) != len(configured_paths) or not paths:
        raise ValueError("Non-destructive diff protected_paths contains an invalid path")
    return paths


def path_matches(path: str, protected_path: str) -> bool:
    normalized = protected_path.rstrip("/")
    return path == normalized or path.startswith(f"{normalized}/")


def load_policy(root: Path, policy_path: str) -> dict:
    path = root / policy_path
    if not path.is_file():
        raise FileNotFoundError(f"Non-destructive diff policy not found: {policy_path}")
    with path.open("r", encoding="utf-8") as handle:
        policy = json.load(handle)
    if not isinstance(policy, dict):
        raise ValueError(f"Non-destructive diff policy must be a JSON object: {policy_path}")
    return policy


def approved(root: Path) -> bool:
    if os.environ.get("APPROVED_DESTRUCTIVE_CHANGE", "").lower() in {"1", "true", "yes"}:
        return True
    return (root / "DESTRUCTIVE_CHANGE_REQUEST.md").is_file() and (
        root / "APPROVED_DESTRUCTIVE_CHANGE.md"
    ).is_file()


def run_git(root: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [git_executable(), "-C", str(root), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def decode_git_error(result: subprocess.CompletedProcess[bytes]) -> str:
    try:
        return result.stderr.decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError:
        return "git returned non-UTF-8 error output"


def verify_commit(root: Path, ref: str) -> str | None:
    if not ref or "\x00" in ref or ref.startswith("-"):
        return "Git comparison refs must be non-empty, option-safe, and NUL-free"
    result = run_git(root, ["rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"])
    if result.returncode:
        return (
            f"git rev-parse could not resolve commit {ref!r} "
            f"({result.returncode}): {decode_git_error(result)}"
        )
    return None


def safe_path(raw: bytes, label: str) -> tuple[str | None, str | None]:
    try:
        value = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None, f"{label} contains a non-UTF-8 path"
    path = PurePosixPath(value)
    unsafe = (
        not value
        or "\\" in value
        or "//" in value
        or value.startswith("/")
        or WINDOWS_DRIVE.match(value) is not None
        or path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    )
    if unsafe:
        return None, f"{label} contains an unsafe or non-canonical repository path: {value!r}"
    return value, None


def parse_name_status_z(payload: bytes, label: str) -> tuple[list[ChangeRecord], list[str]]:
    if not payload:
        return [], []
    if not payload.endswith(b"\x00"):
        return [], [f"{label} is not NUL terminated"]
    tokens = payload[:-1].split(b"\x00")
    records: list[ChangeRecord] = []
    errors: list[str] = []
    index = 0
    while index < len(tokens):
        try:
            status = tokens[index].decode("ascii", errors="strict")
        except UnicodeDecodeError:
            errors.append(f"{label} contains a non-ASCII status")
            break
        index += 1
        if status in SINGLE_PATH_STATUSES:
            path_count = 1
        elif SCORED_STATUS.fullmatch(status):
            path_count = 2
        else:
            errors.append(f"{label} contains malformed or unsupported status {status!r}")
            break
        if index + path_count > len(tokens):
            errors.append(f"{label} contains a truncated {status!r} record")
            break
        paths: list[str] = []
        for offset in range(path_count):
            path, path_error = safe_path(tokens[index + offset], label)
            if path_error:
                errors.append(path_error)
                break
            assert path is not None
            paths.append(path)
        if errors:
            break
        records.append(ChangeRecord(status, tuple(paths), label))
        index += path_count
    if errors:
        return [], errors
    return records, []


def parse_untracked_z(payload: bytes, label: str = "untracked") -> tuple[list[ChangeRecord], list[str]]:
    if not payload:
        return [], []
    if not payload.endswith(b"\x00"):
        return [], [f"{label} output is not NUL terminated"]
    records: list[ChangeRecord] = []
    errors: list[str] = []
    for token in payload[:-1].split(b"\x00"):
        path, path_error = safe_path(token, label)
        if path_error:
            errors.append(path_error)
        elif path is not None:
            records.append(ChangeRecord("A", (path,), label))
    return ([], errors) if errors else (records, [])


def collect_change_records(
    root: Path, base: str, head: str
) -> tuple[list[ChangeRecord], list[str]]:
    errors = [error for ref in (base, head) if (error := verify_commit(root, ref))]
    if errors:
        return [], errors
    commands = (
        ("committed", ["diff", "--name-status", "-z", "--find-renames", f"{base}...{head}", "--"]),
        ("staged", ["diff", "--cached", "--name-status", "-z", "--find-renames", "--"]),
        ("unstaged", ["diff", "--name-status", "-z", "--find-renames", "--"]),
    )
    records: list[ChangeRecord] = []
    for source, arguments in commands:
        result = run_git(root, arguments)
        if result.returncode:
            errors.append(
                f"git {' '.join(arguments)} failed ({result.returncode}): {decode_git_error(result)}"
            )
            continue
        parsed, parse_errors = parse_name_status_z(result.stdout, source)
        records.extend(parsed)
        errors.extend(parse_errors)
    untracked = run_git(root, ["ls-files", "--others", "--exclude-standard", "-z"])
    if untracked.returncode:
        errors.append(
            "git ls-files --others --exclude-standard -z failed "
            f"({untracked.returncode}): {decode_git_error(untracked)}"
        )
    else:
        parsed, parse_errors = parse_untracked_z(untracked.stdout)
        records.extend(parsed)
        errors.extend(parse_errors)
    return records, errors


def summarize_changes(records: list[ChangeRecord]) -> ChangeSummary:
    summary = ChangeSummary()
    for record in records:
        kind = record.status[0]
        if kind == "A":
            summary.added.add(record.paths[0])
        elif kind == "C":
            summary.added.add(record.paths[1])
        elif kind == "D":
            summary.deleted.add(record.paths[0])
        elif kind == "R":
            summary.renamed.add((record.paths[0], record.paths[1]))
        else:
            summary.modified.add(record.paths[0])
    renamed_sources = {source for source, _destination in summary.renamed}
    summary.modified.difference_update(summary.added | summary.deleted | renamed_sources)
    summary.added.difference_update(summary.deleted)
    return summary


def evaluate_changes(root: Path, base: str, head: str, policy: dict) -> DiffEvaluation:
    records, fatal_failures = collect_change_records(root, base, head)
    evaluation = DiffEvaluation(
        summary=summarize_changes(records),
        fatal_failures=fatal_failures,
    )
    if fatal_failures:
        return evaluation
    try:
        max_deleted = int_policy_value(
            policy,
            ("max_deleted_files", "max_files_deleted_without_human_review", "max_existing_file_deletions"),
            0,
        )
        max_modified = int_policy_value(
            policy,
            ("max_modified_files_without_review", "max_files_modified_without_human_review"),
            25,
        )
        max_renamed = int_policy_value(
            policy,
            ("max_renamed_files", "max_directory_renames", "max_file_renames"),
            0,
        )
        protected_paths = policy_paths(policy)
    except ValueError as exc:
        evaluation.fatal_failures.append(str(exc))
        return evaluation
    summary = evaluation.summary
    if len(summary.deleted) > max_deleted:
        evaluation.policy_failures.append(
            f"file deletions exceed budget {max_deleted}: {sorted(summary.deleted)}"
        )
    if len(summary.renamed) > max_renamed:
        rendered = [f"{old} -> {new}" for old, new in sorted(summary.renamed)]
        evaluation.policy_failures.append(f"file renames exceed budget {max_renamed}: {rendered}")
    if len(summary.modified) > max_modified:
        evaluation.policy_failures.append(
            f"modified files exceed budget {max_modified}: {len(summary.modified)}"
        )
    if policy.get("fail_on_deleted_protected_paths") is True:
        protected_hits = sorted(
            path
            for path in summary.deleted | {old for old, _new in summary.renamed}
            if any(path_matches(path, protected_path) for protected_path in protected_paths)
        )
        if protected_hits:
            evaluation.policy_failures.append(
                f"deleted or renamed protected paths: {protected_hits}"
            )
    return evaluation


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("--policy", default=DEFAULT_POLICY)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        policy = load_policy(root, args.policy)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"Non-destructive diff check failed: {exc}")
        return 1
    evaluation = evaluate_changes(root, args.base, args.head, policy)
    if evaluation.fatal_failures:
        print("Non-destructive diff check failed:")
        for failure in evaluation.fatal_failures:
            print(f"  - {failure}")
        return 1
    if evaluation.policy_failures and not approved(root):
        print("Non-destructive diff check failed:")
        for failure in evaluation.policy_failures:
            print(f"  - {failure}")
        return 1
    summary = evaluation.summary
    print(
        "Non-destructive diff check passed "
        f"({len(summary.modified)} modified, {len(summary.deleted)} deleted, "
        f"{len(summary.renamed)} renamed, {len(summary.added)} added/untracked)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
