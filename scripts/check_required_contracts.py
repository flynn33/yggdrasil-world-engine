#!/usr/bin/env python3
"""Ensure required cosmology authority contracts and validation files exist."""

from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_REQUIRED_FILES = [
    "docs/architecture/ywe_cosmology_authority_contract.md",
    "docs/architecture/ash_pattern_system_component_contract.md",
    "data/validation/cosmology_authority_gate_contract.json",
    "data/validation/repository_drift_guardrail_rules.json",
]


def load_required_files(root: Path) -> list[str]:
    contract_path = root / "data" / "validation" / "cosmology_authority_gate_contract.json"
    if not contract_path.is_file():
        return DEFAULT_REQUIRED_FILES
    with contract_path.open(encoding="utf-8-sig") as handle:
        contract = json.load(handle)
    required = list(DEFAULT_REQUIRED_FILES)
    for path in contract.get("required_files", []):
        if path not in required:
            required.append(path)
    return required


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    missing = [path for path in load_required_files(root) if not (root / path).is_file()]
    if missing:
        print("Required contract check failed:")
        for path in missing:
            print(f"  - missing {path}")
        return 1
    print("Required contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
