#!/usr/bin/env python3
"""Reject Phase 9 branch-reality language drift."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PATTERN_PATH = "data/validation/forbidden_branch_language_patterns.json"
DEFAULT_SCAN_PATHS = ("docs", "data", "modules", "core", "examples")
SCANNABLE_SUFFIXES = {".md", ".json", ".yaml", ".yml"}
SKIP_EXACT = {
    PATTERN_PATH,
    "data/validation/branch_reality_guardrail_rules.json",
    "scripts/check_branch_reality_guardrail.py",
}
ALLOWED_CONTEXT_TERMS = {
    "forbidden",
    "invalid",
    "reject",
    "fails if",
    "do not",
    "must not",
    "not pre-generated",
    "not pregenerated",
    "not a pre-generated",
    "no pre-generated",
    "no pregenerated",
    "superseded",
    "historical",
}
REQUIRED_PHRASES = (
    "Leaf branches are not pre-generated",
    "runtime-generated leaf branch",
    "base world ontology",
)


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def load_patterns(root: Path) -> list[str]:
    data = json.loads((root / PATTERN_PATH).read_text(encoding="utf-8-sig"))
    return [
        item["pattern"] if isinstance(item, dict) else str(item)
        for item in data.get("patterns", [])
    ]


def surrounding_context(lines: list[str], index: int) -> str:
    start = max(0, index - 4)
    end = min(len(lines), index + 3)
    return "\n".join(lines[start:end]).lower()


def iter_scannable(root: Path):
    for prefix in DEFAULT_SCAN_PATHS:
        base = root / prefix
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in SCANNABLE_SUFFIXES:
                continue
            rp = rel(path, root)
            if rp in SKIP_EXACT:
                continue
            yield path


def forbidden_hits(root: Path, patterns: list[str]) -> list[str]:
    hits: list[str] = []
    for path in iter_scannable(root):
        lines = path.read_text(encoding="utf-8-sig").splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            for pattern in patterns:
                if pattern.lower() not in lowered:
                    continue
                context = surrounding_context(lines, index)
                if any(term in context for term in ALLOWED_CONTEXT_TERMS):
                    continue
                hits.append(f"{rel(path, root)}:{index + 1}: {line.strip()}")
    return hits


def missing_required_phrases(root: Path) -> list[str]:
    candidates = [
        root / "docs/architecture/leaf_branch_reality_contract.md",
        root / "docs/architecture/runtime_cosmology_foundation_contract.md",
        root / "docs/master_specification/YWE_MASTER_SPECIFICATION.md",
    ]
    combined = " ".join(
        path.read_text(encoding="utf-8-sig")
        for path in candidates
        if path.is_file()
    )
    normalized = " ".join(combined.split())
    return [
        phrase for phrase in REQUIRED_PHRASES if " ".join(phrase.split()) not in normalized
    ]


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    missing_file = not (root / PATTERN_PATH).is_file()
    if missing_file:
        print(f"Branch reality guardrail failed: missing {PATTERN_PATH}")
        return 1

    hits = forbidden_hits(root, load_patterns(root))
    missing = missing_required_phrases(root)
    if hits or missing:
        print("Branch reality guardrail failed:")
        for hit in hits:
            print(f"  - forbidden unqualified phrase: {hit}")
        for phrase in missing:
            print(f"  - missing required phrase: {phrase}")
        return 1

    print("Branch reality guardrail passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
