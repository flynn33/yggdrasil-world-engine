#!/usr/bin/env python3
"""Reject protected-path deletions unless explicitly approved."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

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


def protected_deletions(lines: list[str]) -> list[str]:
    hits: list[str] = []
    for line in lines:
        parts = line.split("\t")
        status = parts[0]
        paths = parts[1:]
        if not status.startswith(("D", "R")):
            continue
        for path in paths:
            if any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES):
                hits.append(line)
                break
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--head", default="HEAD")
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    hits = protected_deletions(diff_name_status(root, args.base, args.head))
    if hits and not approved(root):
        print("Non-destructive diff check failed:")
        for hit in hits:
            print(f"  - protected deletion/rename: {hit}")
        return 1
    print("Non-destructive diff check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
