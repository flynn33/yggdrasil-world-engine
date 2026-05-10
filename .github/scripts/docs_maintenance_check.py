#!/usr/bin/env python3
"""Docs Maintenance Agent — ASH Pattern System sentinel.

Checks:
  (a) Required documentation/governance files exist and are non-empty.
  (b) Required core headings remain present in key canonical docs.
  (c) README repository-map path references resolve to real files.
  (d) Internal markdown links across README/docs/governance/handoff/wiki resolve.
  (e) Drift signal: docs/governance/handoff updates without README update.

Blocking when REPORT_ONLY is unset or "0".
Exits 0 with full report when REPORT_ONLY=1.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from _common import finish, gh_error, gh_warning, read_text, rel, repo_root

REQUIRED_FILES = {
    "README.md",
    "docs/00-repository-purpose.md",
    "docs/01-design-philosophy.md",
    "docs/02-target-repository-shape.md",
    "docs/03-design-roadmap.md",
    "governance/repository-governance.md",
    "governance/ai-coding-handoff.md",
    "governance/github-agents-governance.md",
    "handoff-templates/README.md",
    "handoff-templates/common-downstream-handoff-requirements.md",
    "handoff-templates/desktop-implementation-handoff-template.md",
    "handoff-templates/mobile-implementation-handoff-template.md",
    "handoff-templates/service-implementation-handoff-template.md",
}

REQUIRED_HEADINGS = {
    "README.md": [
        "## Canonical Agnostic Repository",
        "## Repository purpose",
        "## Repository map",
        "## Intended use",
    ],
    "docs/03-design-roadmap.md": [
        "## Goal",
        "## Research math realignment sequence",
        "## Main-repository closeout",
    ],
    "governance/repository-governance.md": [
        "## Governance rules",
        "## Main-repository closeout",
    ],
    "governance/ai-coding-handoff.md": [
        "## Required coding-agent workflow",
        "## What the coding agent must preserve",
    ],
    "governance/github-agents-governance.md": [
        "## Agents",
        "## Rollout state",
    ],
}

README_REQUIRED_MARKERS = (
    "F2^9",
    "maintenance mode",
)

DOC_SCAN_PREFIXES = ("README.md", "docs/", "governance/", "handoff-templates/", "wiki/")
DRIFT_PREFIXES = ("docs/", "governance/", "handoff-templates/", "specs/")

MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
README_MAP_PATH_RE = re.compile(r"^-\s+`([^`]+)`\s+—", re.MULTILINE)


def git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return ""


def changed_files() -> list[str]:
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    payload = {}

    if event_path and Path(event_path).is_file():
        try:
            payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
        except Exception:
            payload = {}

    files: list[str] = []
    if event_name == "pull_request":
        base = payload.get("pull_request", {}).get("base", {}).get("sha", "")
        head = payload.get("pull_request", {}).get("head", {}).get("sha", "")
        if base and head:
            out = git("diff", "--name-only", base, head)
            if out:
                files = out.splitlines()
    else:
        before = payload.get("before", "")
        after = payload.get("after", "") or os.environ.get("GITHUB_SHA", "")
        if before and after and before != "0000000000000000000000000000000000000000":
            out = git("diff", "--name-only", before, after)
            if out:
                files = out.splitlines()
        elif after:
            out = git("show", "--name-only", "--format=", after)
            if out:
                files = [ln for ln in out.splitlines() if ln]

    if not files and not event_name:
        return []

    return files


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for prefix in DOC_SCAN_PREFIXES:
        p = root / prefix
        if p.is_file() and p.suffix.lower() == ".md":
            files.append(p)
            continue
        if p.is_dir():
            files.extend(sorted(p.rglob("*.md")))
    return files


def check_required_files(root: Path) -> list[tuple[str, int, str]]:
    errors: list[tuple[str, int, str]] = []
    for rp in sorted(REQUIRED_FILES):
        p = root / rp
        if not p.is_file():
            errors.append((rp, 1, "Required canonical documentation file is missing"))
            continue
        if not read_text(p).strip():
            errors.append((rp, 1, "Required canonical documentation file is empty"))
    return errors


def check_required_headings(root: Path) -> list[tuple[str, int, str]]:
    errors: list[tuple[str, int, str]] = []
    for rp, headings in REQUIRED_HEADINGS.items():
        p = root / rp
        text = read_text(p)
        if not text:
            continue
        for heading in headings:
            if heading not in text:
                errors.append((rp, 1, f"Required heading missing: {heading}"))
    return errors


def check_readme_markers(root: Path) -> list[tuple[str, int, str]]:
    errors: list[tuple[str, int, str]] = []
    text = read_text(root / "README.md")
    if not text:
        return errors
    for marker in README_REQUIRED_MARKERS:
        if marker not in text:
            errors.append(("README.md", 1, f"README baseline marker missing: {marker}"))
    return errors


def check_readme_map_paths(root: Path) -> list[tuple[str, int, str]]:
    errors: list[tuple[str, int, str]] = []
    readme = root / "README.md"
    text = read_text(readme)
    if not text:
        return errors

    for m in README_MAP_PATH_RE.finditer(text):
        mapped = m.group(1).strip()
        if mapped.startswith("http://") or mapped.startswith("https://"):
            continue
        p = root / mapped
        if not p.exists():
            errors.append(("README.md", line_of(text, m.start()), f"Repository-map path does not exist: {mapped}"))

    return errors


def resolve_internal_link(src: Path, raw_target: str, root: Path) -> Path | None:
    target = raw_target.split("#", 1)[0].split("?", 1)[0].strip()
    if not target:
        return None
    if target.startswith(("http://", "https://", "mailto:")):
        return None
    if target.startswith("#"):
        return None
    if target.startswith("/"):
        return (root / target.lstrip("/")).resolve()

    # GitHub wiki page-style links (e.g., [Home](Home), no extension) inside
    # wiki/*.md should resolve to wiki/<Page>.md.
    if src.parent == (root / "wiki") and "." not in Path(target).name and "/" not in target:
        return (root / "wiki" / f"{target}.md").resolve()

    return (src.parent / target).resolve()


def check_internal_links(root: Path) -> list[tuple[str, int, str]]:
    errors: list[tuple[str, int, str]] = []

    for path in markdown_files(root):
        text = read_text(path)
        if not text:
            continue

        for m in MD_LINK_RE.finditer(text):
            raw = m.group(1).strip()
            resolved = resolve_internal_link(path, raw, root)
            if resolved is None:
                continue

            if not resolved.exists():
                errors.append((
                    rel(path, root),
                    line_of(text, m.start()),
                    f"Broken markdown link target: {raw}",
                ))

    return errors


def check_readme_drift_warning() -> list[tuple[str, int, str]]:
    warnings: list[tuple[str, int, str]] = []
    changed = changed_files()
    if not changed:
        return warnings

    core_docs_changed = any(any(f.startswith(prefix) for prefix in DRIFT_PREFIXES) for f in changed)
    readme_changed = "README.md" in changed

    if core_docs_changed and not readme_changed:
        warnings.append((
            "README.md",
            1,
            "Canonical docs/specs changed without README update in same event",
        ))

    return warnings


def main() -> int:
    root = repo_root()
    print("Docs Maintenance Agent — checking README/docs/governance integrity...")

    required_errors = check_required_files(root)
    heading_errors = check_required_headings(root)
    marker_errors = check_readme_markers(root)
    map_errors = check_readme_map_paths(root)
    link_errors = check_internal_links(root)
    warnings = check_readme_drift_warning()

    all_errors = required_errors + heading_errors + marker_errors + map_errors + link_errors

    if required_errors:
        print(f"Required-file violations: {len(required_errors)}")
    if heading_errors:
        print(f"Required-heading violations: {len(heading_errors)}")
    if marker_errors:
        print(f"README marker violations: {len(marker_errors)}")
    if map_errors:
        print(f"README map-path violations: {len(map_errors)}")
    if link_errors:
        print(f"Broken-link violations: {len(link_errors)}")

    for e in all_errors:
        print(f"  - {e[0]}:{e[1]}: {e[2]}")
        gh_error(*e)

    for w in warnings:
        print(f"  WARNING {w[0]}:{w[1]}: {w[2]}")
        gh_warning(*w)

    if not all_errors and not warnings:
        print("Docs Maintenance Agent: no violations or warnings found.")
    elif not all_errors:
        print("Docs Maintenance Agent: warnings only, no blocking violations.")

    return finish(bool(all_errors), "DOCS MAINTENANCE AGENT")


if __name__ == "__main__":
    sys.exit(main())
