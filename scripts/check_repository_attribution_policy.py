#!/usr/bin/env python3
"""Validate repository attribution and process-residue policy."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"
TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".plist",
    ".ps1",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}

SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
}

SELF_PATH = "scripts/check_repository_attribution_policy.py"


@dataclass(frozen=True)
class Rule:
    rule_id: str
    value: str
    text_scope: bool = True
    path_scope: bool = True
    token_boundary: bool = True


def decoded(value: str) -> str:
    return base64.b64decode(value).decode("utf-8")


def rules() -> list[Rule]:
    encoded_rules = [
        ("ATTR001", "Q2hhdEdQVA==", True, True, True),
        ("ATTR002", "Q29kZXg=", True, True, True),
        ("ATTR003", "T3BlbkFJ", True, True, True),
        ("ATTR004", "Q2xhdWRl", True, True, True),
        ("ATTR005", "QW50aHJvcGlj", True, True, True),
        ("ATTR006", "R2VtaW5p", True, True, True),
        ("ATTR007", "Q29waWxvdA==", True, True, True),
        ("ATTR008", "R1BU", True, True, True),
        ("ATTR009", "TExN", True, True, True),
        ("ATTR010", "YXJ0aWZpY2lhbCBpbnRlbGxpZ2VuY2U=", True, False, True),
        ("ATTR011", "QUkgYXNzaXN0YW50", True, False, True),
        ("ATTR012", "Z2VuZXJhdGVkIGJ5IEFJ", True, False, True),
        ("ATTR013", "QUktZ2VuZXJhdGVk", True, False, True),
        ("PATH001", "aGFuZG9mZg==", False, True, True),
        ("PATH002", "cmVtZWRpYXRpb24=", False, True, True),
        ("PATH003", "Ym9vdHN0cmFwX3Byb21wdA==", False, True, False),
        ("PATH004", "YWdlbnRpYw==", False, True, True),
        ("PATH005", "bm8tYWk=", False, True, False),
    ]
    return [
        Rule(rule_id, decoded(value), text_scope, path_scope, token_boundary)
        for rule_id, value, text_scope, path_scope, token_boundary in encoded_rules
    ]


def compile_rule(rule: Rule) -> re.Pattern[str]:
    pattern = re.escape(rule.value)
    if rule.token_boundary:
        pattern = rf"(?<![A-Za-z0-9]){pattern}(?![A-Za-z0-9])"
    return re.compile(pattern, re.IGNORECASE)


def run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def git_lines(root: Path, args: list[str]) -> list[str]:
    result = run_git(root, args)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def current_branch(root: Path) -> str | None:
    result = run_git(root, ["branch", "--show-current"])
    if result.returncode != 0:
        return None
    branch = result.stdout.strip()
    return branch or None


def branch_names(root: Path) -> list[str]:
    names = []
    branch = current_branch(root)
    if branch:
        names.append(branch)
    for ref in git_lines(root, ["for-each-ref", "--format=%(refname:short)", "refs/remotes"]):
        if ref.endswith("/HEAD"):
            continue
        names.append(ref)
    return list(dict.fromkeys(names))


def base_ref(root: Path) -> str | None:
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref and git_ref_exists(root, f"origin/{github_base_ref}"):
        return f"origin/{github_base_ref}"
    base = os.environ.get("BASE_REF")
    if base and git_ref_exists(root, base):
        return base
    if git_ref_exists(root, "origin/main"):
        return "origin/main"
    if git_ref_exists(root, "main"):
        return "main"
    return None


def git_ref_exists(root: Path, ref: str) -> bool:
    result = run_git(root, ["rev-parse", "--verify", "--quiet", ref])
    return result.returncode == 0


def event_payload() -> dict:
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        return {}
    event_path = Path(path)
    if not event_path.is_file():
        return {}
    try:
        value = json.loads(event_path.read_text(encoding=TEXT_ENCODING))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def tracked_paths(root: Path) -> list[str]:
    return git_lines(root, ["ls-files"])


def changed_paths(root: Path) -> list[str]:
    base = base_ref(root)
    paths: list[str] = []
    if base:
        paths.extend(non_deleted_diff_paths(root, f"{base}...HEAD"))
    paths.extend(non_deleted_diff_paths(root))
    paths.extend(non_deleted_diff_paths(root, "--cached"))
    paths.extend(git_lines(root, ["ls-files", "--others", "--exclude-standard"]))
    return list(dict.fromkeys(paths))


def non_deleted_diff_paths(root: Path, *args: str) -> list[str]:
    result = run_git(root, ["diff", "--name-status", "--find-renames", *args])
    if result.returncode != 0:
        return []
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("D"):
            continue
        if len(parts) >= 2:
            paths.append(parts[-1])
    return paths


def commit_refs(root: Path) -> list[str]:
    event = event_payload()
    before = event.get("before")
    after = event.get("after")
    pull_request = event.get("pull_request")
    if isinstance(pull_request, dict):
        base = pull_request.get("base", {})
        head = pull_request.get("head", {})
        if isinstance(base, dict) and isinstance(head, dict):
            before = base.get("sha")
            after = head.get("sha")
    if isinstance(after, str) and git_ref_exists(root, after):
        if (
            isinstance(before, str)
            and before
            and not re.fullmatch(r"0+", before)
            and git_ref_exists(root, before)
        ):
            refs = git_lines(root, ["rev-list", f"{before}..{after}"])
            if refs:
                return refs
        return [after]

    base = base_ref(root)
    if base:
        refs = git_lines(root, ["rev-list", f"{base}..HEAD"])
        if refs:
            return refs
    head = git_lines(root, ["rev-parse", "--verify", "HEAD"])
    return head[:1]


def commit_metadata(root: Path) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for ref in commit_refs(root):
        result = run_git(root, ["show", "-s", "--format=%an%n%ae%n%cn%n%ce%n%B", ref])
        if result.returncode == 0:
            entries.append((f"commit:{ref}", result.stdout))
    return entries


def event_metadata() -> list[tuple[str, str]]:
    event = event_payload()
    entries: list[tuple[str, str]] = []
    pull_request = event.get("pull_request")
    if isinstance(pull_request, dict):
        for key in ("title", "body"):
            value = pull_request.get(key)
            if isinstance(value, str):
                entries.append((f"pull_request.{key}", value))
        head = pull_request.get("head")
        if isinstance(head, dict) and isinstance(head.get("ref"), str):
            entries.append(("pull_request.head.ref", head["ref"]))
    return entries


def is_text_path(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES


def iter_text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    repository_paths = list(dict.fromkeys([*tracked_paths(root), *changed_paths(root)]))
    for rel in repository_paths:
        if rel == SELF_PATH:
            continue
        path = root / rel
        if not path.is_file() or not is_text_path(path):
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        files.append(path)
    return files


def scan_value(value: str, active_rules: list[Rule]) -> str | None:
    for rule in active_rules:
        if compile_rule(rule).search(value):
            return rule.rule_id
    return None


def scan_paths(paths: list[str], active_rules: list[Rule], label: str, errors: list[str]) -> None:
    path_rules = [rule for rule in active_rules if rule.path_scope]
    for path_name in paths:
        rule_id = scan_value(path_name, path_rules)
        if rule_id:
            errors.append(f"Repository attribution policy violation: blocked marker in {label} {path_name} ({rule_id}).")


def scan_text_entries(entries: list[tuple[str, str]], active_rules: list[Rule], errors: list[str]) -> None:
    text_rules = [rule for rule in active_rules if rule.text_scope]
    for label, text in entries:
        rule_id = scan_value(text, text_rules)
        if rule_id:
            errors.append(f"Repository attribution policy violation: blocked marker in {label} ({rule_id}).")


def scan_repository_text(root: Path, active_rules: list[Rule], errors: list[str]) -> None:
    text_rules = [rule for rule in active_rules if rule.text_scope]
    for path in iter_text_files(root):
        rel = path.relative_to(root).as_posix()
        try:
            lines = path.read_text(encoding=TEXT_ENCODING).splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for index, line in enumerate(lines, start=1):
            rule_id = scan_value(line, text_rules)
            if rule_id:
                errors.append(f"Repository attribution policy violation: blocked marker in {rel}:{index} ({rule_id}).")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    active_rules = rules()
    errors: list[str] = []

    scan_paths(branch_names(root), active_rules, "branch", errors)
    scan_paths(tracked_paths(root), active_rules, "tracked path", errors)
    scan_paths(changed_paths(root), active_rules, "changed path", errors)
    scan_text_entries(commit_metadata(root), active_rules, errors)
    scan_text_entries(event_metadata(), active_rules, errors)
    scan_repository_text(root, active_rules, errors)

    if errors:
        print("Repository attribution policy check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Repository attribution policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
