#!/usr/bin/env python3
"""Validate pull request diffs against the repository non-destructive policy."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

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


def int_policy_value(policy: dict, names: tuple[str, ...], default: int) -> int:
    for name in names:
        if name in policy:
            try:
                return int(policy[name])
            except (TypeError, ValueError):
                raise ValueError(f"Non-destructive diff policy value {name} must be an integer: {policy[name]!r}")
    return default


def policy_paths(policy: dict) -> tuple[str, ...]:
    configured_paths = policy.get("protected_paths", PROTECTED_PREFIXES)
    if not isinstance(configured_paths, list):
        return PROTECTED_PREFIXES
    paths = tuple(path for path in configured_paths if isinstance(path, str) and path.strip())
    return paths if paths else PROTECTED_PREFIXES


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


def diff_name_status(root: Path, base: str, head: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-status", base, head],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return [line for line in result.stdout.splitlines() if line.strip()]


def classify_changes(lines: list[str]) -> tuple[list[str], list[str], list[str], list[str]]:
    deleted: list[str] = []
    renamed: list[str] = []
    modified: list[str] = []
    malformed: list[str] = []
    for line in lines:
        parts = line.split("\t")
        status = parts[0]
        paths = parts[1:]
        if status.startswith("D"):
            if paths:
                deleted.append(paths[0])
            else:
                malformed.append(line)
        elif status.startswith("R"):
            if len(paths) >= 2:
                renamed.append(paths[0])
            else:
                malformed.append(line)
        elif not status.startswith(("A", "C")):
            if paths:
                modified.append(paths[-1])
            else:
                malformed.append(line)
    return deleted, renamed, modified, malformed


def protected_deletions(deleted: list[str], renamed: list[str], protected_paths: tuple[str, ...]) -> list[str]:
    return [
        path
        for path in [*deleted, *renamed]
        if any(path_matches(path, protected_path) for protected_path in protected_paths)
    ]


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
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(f"Non-destructive diff check failed: {exc}")
        return 1

    deleted, renamed, modified, malformed = classify_changes(diff_name_status(root, args.base, args.head))

    failures: list[str] = []
    if malformed:
        failures.append(f"malformed name-status lines: {malformed}")
    if len(deleted) > max_deleted:
        failures.append(f"file deletions exceed budget {max_deleted}: {deleted}")
    if len(renamed) > max_renamed:
        failures.append(f"file renames exceed budget {max_renamed}: {renamed}")
    if len(modified) > max_modified:
        failures.append(f"modified files exceed budget {max_modified}: {len(modified)}")
    if policy.get("fail_on_deleted_protected_paths") is True:
        protected_hits = protected_deletions(deleted, renamed, policy_paths(policy))
        if protected_hits:
            failures.append(f"deleted or renamed protected paths: {protected_hits}")

    if failures and not approved(root):
        print("Non-destructive diff check failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("Non-destructive diff check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
