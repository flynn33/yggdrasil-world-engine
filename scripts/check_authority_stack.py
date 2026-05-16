#!/usr/bin/env python3
"""Scan repository text for authority-stack drift."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DEFAULT_CONFIG = "data/validation/repository_drift_guardrail_rules.json"
DEFAULT_EXTENSIONS = {".md", ".json", ".yaml", ".yml"}
DEFAULT_IGNORE_PREFIXES = {
    ".git/",
    "__MACOSX__/",
    "core/ash_pattern_engine/canonical/",
    "specs/",
}
DEFAULT_ALLOWED_CONTEXT = {
    "superseded",
    "historical",
    "earlier draft",
    "legacy phrasing",
    "incorrect framing",
    "forbidden",
    "invalid",
    "not current",
    "no longer current",
    "acceptance-marker",
}


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def load_config(root: Path, config_path: str) -> dict:
    path = root / config_path
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def iter_scannable(root: Path, config_path: str, config: dict):
    extensions = set(config.get("scan_extensions", DEFAULT_EXTENSIONS))
    ignore_prefixes = set(config.get("ignore_paths", DEFAULT_IGNORE_PREFIXES))
    skip_exact = {
        config_path,
        "data/validation/cosmology_authority_gate_contract.json",
        "scripts/check_authority_stack.py",
        "examples/invalid_authority_statement_rejection_cases.example.json",
    }
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in extensions:
            continue
        rp = rel(path, root)
        if rp in skip_exact:
            continue
        if any(rp.startswith(prefix) for prefix in ignore_prefixes):
            continue
        yield path


def surrounding_context(lines: list[str], index: int) -> str:
    start = max(0, index - 6)
    end = min(len(lines), index + 3)
    return "\n".join(lines[start:end]).lower()


def forbidden_hits(root: Path, config_path: str, config: dict) -> list[str]:
    allowed = set(config.get("allowed_context_terms", [])) | DEFAULT_ALLOWED_CONTEXT
    phrases = [
        item["phrase"] if isinstance(item, dict) else str(item)
        for item in config.get("forbidden_unqualified_phrases", [])
    ]
    hits: list[str] = []
    for path in iter_scannable(root, config_path, config):
        rp = rel(path, root)
        text = path.read_text(encoding="utf-8-sig")
        lines = text.splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            for phrase in phrases:
                if phrase.lower() not in lowered:
                    continue
                context = surrounding_context(lines, index)
                if any(token.lower() in context for token in allowed):
                    continue
                hits.append(f"{rp}:{index + 1}: {line.strip()}")
    return hits


def required_phrase_failures(root: Path, config: dict) -> list[str]:
    combined = []
    for path in (
        root / "docs" / "architecture" / "ywe_cosmology_authority_contract.md",
        root / "README.md",
        root / "docs" / "master_specification" / "YWE_MASTER_SPECIFICATION.md",
    ):
        if path.is_file():
            combined.append(path.read_text(encoding="utf-8-sig"))
    text = " ".join("\n".join(combined).split())
    return [
        phrase
        for phrase in config.get("required_present_phrases", [])
        if " ".join(phrase.split()) not in text
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    config = load_config(root, args.config)
    hits = forbidden_hits(root, args.config, config)
    missing = required_phrase_failures(root, config)

    if hits or missing:
        print("Authority stack check failed:")
        for hit in hits:
            print(f"  - forbidden unqualified phrase: {hit}")
        for phrase in missing:
            print(f"  - missing required phrase: {phrase}")
        return 1

    print("Authority stack check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
