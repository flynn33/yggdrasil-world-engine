#!/usr/bin/env python3
"""Canonical Semantic Integrity Agent — ASH Pattern System sentinel.

Checks:
  (a) Non-canonical math-language reintroduction in active canonical files.
  (b) Handoff-template authority inversion.
  (c) Contradictory status language across README.md, docs/03-design-roadmap.md,
      and governance/ai-coding-handoff.md.

See governance/github-agents-governance.md for policy.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _common import (
    finish,
    gh_error,
    is_negative_context,
    read_text,
    rel,
    repo_root,
    walk_files,
)

ACTIVE_CANONICAL_ROOTS = [
    "README.md",
    "specs",
    "docs",
    "governance",
    "handoff-templates",
]

NON_CANONICAL_MATH_PATTERNS = [
    (re.compile(r"\[\s*8\s*,\s*4\s*,\s*4\s*\]"), "alternate codeword-notation claim"),
    (re.compile(r"\bderived\s+9(?:th)?\s+(?:control|parity)\s+bit\b", re.IGNORECASE), "derived-bit claim"),
    (re.compile(r"\b8[- ]?bit\s+core\s*\+\s*derived\s+9(?:th)?", re.IGNORECASE), "alternate state-decomposition claim"),
    (re.compile(r"\bb8\s*=\s*b0\s*(?:⊕|\^|XOR)", re.IGNORECASE), "coordinate-derivation formula"),
    (re.compile(r"\bparity\s+formula\b", re.IGNORECASE), "parity-derived baseline claim"),
]

HANDOFF_AUTHORITY_PATTERNS = [
    re.compile(r"handoff\s+templates?\s+(?:are|is)\s+(?:the\s+)?(?:semantic\s+)?authority", re.IGNORECASE),
    re.compile(r"handoff\s+templates?\s+override\w*\s+canonical", re.IGNORECASE),
    re.compile(r"handoff\s+templates?\s+define\w*\s+canonical", re.IGNORECASE),
    re.compile(r"handoff\s+templates?\s+own\w*\s+canonical", re.IGNORECASE),
]

STATUS_FILES = [
    "README.md",
    "docs/03-design-roadmap.md",
    "governance/ai-coding-handoff.md",
]

BROAD_COMPLETION = re.compile(r"\ball\s+specification\s+layers\s+are\s+complete\b", re.IGNORECASE)
ACTIVE_ALIGNMENT = re.compile(
    r"(\balignment\b|\brewrite\b|\broadmap\b)[^.\n]{0,80}\b(active|in\s+progress|current)\b|"
    r"\b(active|in\s+progress|current)\b[^.\n]{0,80}(\balignment\b|\brewrite\b|\broadmap\b)",
    re.IGNORECASE,
)


def iter_active_canonical_md(root: Path):
    for entry in ACTIVE_CANONICAL_ROOTS:
        p = root / entry
        if p.is_file() and p.suffix == ".md":
            yield p
        elif p.is_dir():
            for sub in p.rglob("*.md"):
                yield sub


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def check_non_canonical_math(root: Path) -> list[tuple[str, int, str]]:
    violations = []
    for path in iter_active_canonical_md(root):
        text = read_text(path)
        if not text:
            continue
        for pat, label in NON_CANONICAL_MATH_PATTERNS:
            for m in pat.finditer(text):
                if is_negative_context(text, m.start()):
                    continue
                violations.append((
                    rel(path, root),
                    line_of(text, m.start()),
                    f"Non-canonical math-language in active canonical file: {label}",
                ))
    return violations


def check_handoff_authority(root: Path) -> list[tuple[str, int, str]]:
    violations = []
    for path in walk_files(root):
        if path.suffix.lower() != ".md":
            continue
        text = read_text(path)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for pat in HANDOFF_AUTHORITY_PATTERNS:
                if pat.search(line):
                    violations.append((
                        rel(path, root),
                        line_no,
                        "Handoff templates must not claim canonical authority",
                    ))
                    break
    return violations


def check_status_contradiction(root: Path) -> list[tuple[str, int, str]]:
    errors = []
    completion_hits = []
    alignment_hits = []

    for rel_path in STATUS_FILES:
        p = root / rel_path
        if not p.is_file():
            continue
        text = read_text(p)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            if BROAD_COMPLETION.search(line):
                completion_hits.append((rel_path, line_no))
            if ACTIVE_ALIGNMENT.search(line):
                alignment_hits.append((rel_path, line_no))

    if completion_hits and alignment_hits:
        cites = ", ".join(f"{f}:{ln}" for f, ln in alignment_hits)
        for f, ln in completion_hits:
            errors.append((
                f,
                ln,
                f"Status contradiction: broad completion phrase co-occurs with active alignment language at {cites}",
            ))
    return errors


def main() -> int:
    root = repo_root()
    print("Canonical Semantic Integrity Agent — scanning active canonical files...")

    all_errors: list[tuple[str, int, str]] = []

    math_errors = check_non_canonical_math(root)
    for e in math_errors:
        print(f"  - {e[0]}:{e[1]}: {e[2]}")
        gh_error(*e)
    all_errors.extend(math_errors)

    handoff_errors = check_handoff_authority(root)
    for e in handoff_errors:
        print(f"  - {e[0]}:{e[1]}: {e[2]}")
        gh_error(*e)
    all_errors.extend(handoff_errors)

    status_errors = check_status_contradiction(root)
    for e in status_errors:
        print(f"  - {e[0]}:{e[1]}: {e[2]}")
        gh_error(*e)
    all_errors.extend(status_errors)

    if not all_errors:
        print("Canonical Semantic Integrity Agent: no violations found.")
    return finish(bool(all_errors), "CANONICAL SEMANTIC INTEGRITY AGENT")


if __name__ == "__main__":
    sys.exit(main())
