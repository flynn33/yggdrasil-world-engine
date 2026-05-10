#!/usr/bin/env python3
"""Wiki Maintenance Agent — ASH Pattern System sentinel.

Checks:
  (a) Required wiki pages exist under wiki/ and are non-empty with a top heading.
  (b) Core navigation pages (Home and _Sidebar) include links to required pages.
  (c) Internal wiki links resolve to existing wiki pages/files.
  (d) Drift signal: if canonical docs/specs/governance/agent files changed in
      the event, at least one wiki/ file should also be updated.

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

from _common import finish, gh_error, gh_warning, read_text, rel, repo_root, walk_files

WIKI_DIR = "wiki"

REQUIRED_WIKI_FILES = {
    "Home.md",
    "_Sidebar.md",
    "Getting-Started.md",
    "Canonical-Math-Baseline.md",
    "Specification-Layers.md",
    "Recovery-and-Safety-Semantics.md",
    "Contracts-and-Verification.md",
    "Governance-and-Agents.md",
    "Downstream-Handoff-Guide.md",
    "Wiki-Maintenance-Playbook.md",
    "Glossary.md",
}

NAV_REQUIRED_PAGES = {
    "Getting-Started",
    "Canonical-Math-Baseline",
    "Specification-Layers",
    "Recovery-and-Safety-Semantics",
    "Contracts-and-Verification",
    "Governance-and-Agents",
    "Downstream-Handoff-Guide",
    "Wiki-Maintenance-Playbook",
    "Glossary",
}

WATCHED_PREFIXES = (
    "README.md",
    "docs/",
    "specs/",
    "governance/",
    "handoff-templates/",
    ".github/workflows/",
    ".github/scripts/",
)

MD_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TOP_HEADING_RE = re.compile(r"^#\s+.+", re.MULTILINE)


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


def wiki_files(root: Path) -> list[Path]:
    wiki_root = root / WIKI_DIR
    if not wiki_root.is_dir():
        return []
    return [p for p in walk_files(wiki_root) if p.suffix.lower() == ".md"]


def check_required_pages(root: Path) -> list[tuple[str, int, str]]:
    errors: list[tuple[str, int, str]] = []
    wiki_root = root / WIKI_DIR

    if not wiki_root.is_dir():
        return [(WIKI_DIR + "/", 1, "wiki/ directory is missing")]

    for name in sorted(REQUIRED_WIKI_FILES):
        path = wiki_root / name
        rp = rel(path, root)
        if not path.is_file():
            errors.append((rp, 1, "Required wiki page is missing"))
            continue

        text = read_text(path)
        if not text.strip():
            errors.append((rp, 1, "Required wiki page exists but is empty"))
            continue

        # GitHub wiki special files (_Sidebar.md, _Footer.md) are not required
        # to carry a top heading.
        if name.startswith("_"):
            continue

        if not TOP_HEADING_RE.search(text):
            errors.append((rp, 1, "Wiki page is missing a top markdown heading"))

    return errors


def referenced_wiki_pages(text: str) -> set[str]:
    refs: set[str] = set()
    for m in MD_LINK_RE.finditer(text):
        raw = m.group(1).strip()
        target = raw.split("#", 1)[0].strip()
        if not target:
            continue
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("#"):
            continue
        if target.endswith(".md"):
            target = target[:-3]
        target = target.lstrip("./")
        if "/" in target:
            continue
        refs.add(target)
    return refs


def check_navigation(root: Path) -> list[tuple[str, int, str]]:
    errors: list[tuple[str, int, str]] = []
    home = root / WIKI_DIR / "Home.md"
    sidebar = root / WIKI_DIR / "_Sidebar.md"

    if home.is_file():
        home_refs = referenced_wiki_pages(read_text(home))
        missing = sorted(NAV_REQUIRED_PAGES - home_refs)
        for page in missing:
            errors.append((rel(home, root), 1, f"Home.md navigation missing link to page: {page}"))

    if sidebar.is_file():
        side_refs = referenced_wiki_pages(read_text(sidebar))
        missing = sorted(NAV_REQUIRED_PAGES - side_refs)
        for page in missing:
            errors.append((rel(sidebar, root), 1, f"_Sidebar.md navigation missing link to page: {page}"))

    return errors


def resolve_internal_link(path: Path, target: str, root: Path) -> Path:
    wiki_root = root / WIKI_DIR

    # If target has file extension, resolve relative to current file.
    if "." in Path(target).name:
        return (path.parent / target).resolve()

    # Wiki page-style links: "Page-Name" -> wiki/Page-Name.md
    return (wiki_root / f"{target}.md").resolve()


def check_internal_links(root: Path) -> list[tuple[str, int, str]]:
    errors: list[tuple[str, int, str]] = []

    for path in wiki_files(root):
        text = read_text(path)
        if not text:
            continue

        for m in MD_LINK_RE.finditer(text):
            raw = m.group(1).strip()
            target = raw.split("#", 1)[0].strip()

            if not target:
                continue
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            if target.startswith("#"):
                continue

            target = target.lstrip("./")
            resolved = resolve_internal_link(path, target, root)
            if not resolved.exists():
                errors.append((
                    rel(path, root),
                    line_of(text, m.start()),
                    f"Broken internal wiki link: {raw}",
                ))

    return errors


def check_drift_signal(root: Path) -> tuple[list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    warnings: list[tuple[str, int, str]] = []
    errors: list[tuple[str, int, str]] = []

    changed = changed_files()
    if not changed:
        return warnings, errors

    watched_changed = any(
        f == "README.md" or any(f.startswith(prefix) for prefix in WATCHED_PREFIXES if prefix.endswith("/"))
        for f in changed
    )
    wiki_changed = any(f.startswith("wiki/") for f in changed)

    if watched_changed and not wiki_changed:
        # Warning-only signal: we want maintainers to consciously keep wiki aligned.
        warnings.append((
            "wiki/Home.md",
            1,
            "Canonical docs/specs/governance changed but no wiki/ page changed in this event",
        ))

    return warnings, errors


def main() -> int:
    root = repo_root()
    print("Wiki Maintenance Agent — checking wiki completeness and integrity...")

    all_errors: list[tuple[str, int, str]] = []

    required_errors = check_required_pages(root)
    nav_errors = check_navigation(root)
    link_errors = check_internal_links(root)
    drift_warnings, drift_errors = check_drift_signal(root)

    all_errors.extend(required_errors)
    all_errors.extend(nav_errors)
    all_errors.extend(link_errors)
    all_errors.extend(drift_errors)

    if required_errors:
        print(f"Required-page violations: {len(required_errors)}")
    if nav_errors:
        print(f"Navigation violations: {len(nav_errors)}")
    if link_errors:
        print(f"Broken-link violations: {len(link_errors)}")

    for e in required_errors + nav_errors + link_errors + drift_errors:
        print(f"  - {e[0]}:{e[1]}: {e[2]}")
        gh_error(*e)

    for w in drift_warnings:
        print(f"  WARNING {w[0]}:{w[1]}: {w[2]}")
        gh_warning(*w)

    if not all_errors and not drift_warnings:
        print("Wiki Maintenance Agent: no violations or warnings found.")
    elif not all_errors:
        print("Wiki Maintenance Agent: warnings only, no blocking violations.")

    return finish(bool(all_errors), "WIKI MAINTENANCE AGENT")


if __name__ == "__main__":
    sys.exit(main())
