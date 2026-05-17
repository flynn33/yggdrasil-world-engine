#!/usr/bin/env python3
"""Ensure Phase 8-9 required contracts, schemas, and validation files exist."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONTRACT_PATH = "data/validation/required_phase_8_9_artifacts.json"


def load_required_paths(root: Path) -> list[str]:
    path = root / CONTRACT_PATH
    if not path.is_file():
        return []

    contract = json.loads(path.read_text(encoding="utf-8-sig"))
    required: list[str] = [CONTRACT_PATH]
    for key in (
        "phase_8",
        "phase_9_architecture_contracts",
        "phase_9_schemas",
        "phase_9_validation",
    ):
        for rel in contract.get(key, []):
            if rel not in required:
                required.append(rel)
    return required


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    required = load_required_paths(root)
    missing = [rel for rel in required if not (root / rel).is_file()]

    if missing:
        print("Phase 8-9 required artifact check failed:")
        for rel in missing:
            print(f"  - missing {rel}")
        return 1

    print("Phase 8-9 required artifact check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
