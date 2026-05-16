#!/usr/bin/env python3
"""Parse every repository JSON file and fail on invalid JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path

IGNORE_PARTS = {".git", "__MACOSX__"}


def iter_json_files(root: Path):
    for path in root.rglob("*.json"):
        if any(part in IGNORE_PARTS for part in path.parts):
            continue
        if path.is_file():
            yield path


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    failures: list[str] = []
    count = 0
    for path in iter_json_files(root):
        count += 1
        try:
            with path.open(encoding="utf-8-sig") as handle:
                json.load(handle)
        except Exception as exc:
            failures.append(f"{path.relative_to(root).as_posix()}: {exc}")

    if failures:
        print("JSON integrity check failed:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"JSON integrity check passed ({count} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
