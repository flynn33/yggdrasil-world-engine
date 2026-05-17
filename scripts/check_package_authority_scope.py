#!/usr/bin/env python3
"""Validate that the repository is bound to the active user-supplied packages."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONTRACT_PATH = "data/validation/package_authority_scope_contract.json"


def load_contract(root: Path) -> dict:
    path = root / CONTRACT_PATH
    if not path.is_file():
        raise FileNotFoundError(CONTRACT_PATH)
    return json.loads(path.read_text(encoding="utf-8-sig"))


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def existing_forbidden_prefix_paths(root: Path, prefix: str) -> list[str]:
    base = root / prefix
    if not base.exists():
        return []
    if base.is_file():
        return [prefix]
    return sorted(rel(path, root) for path in base.rglob("*") if path.is_file())


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    try:
        contract = load_contract(root)
    except FileNotFoundError:
        print(f"Package authority scope check failed: missing {CONTRACT_PATH}")
        return 1

    missing_required = [
        path
        for path in contract.get("required_artifacts", [])
        if not (root / path).is_file()
    ]
    present_forbidden = [
        path
        for path in contract.get("forbidden_artifacts", [])
        if (root / path).exists()
    ]
    for prefix in contract.get("forbidden_prefixes", []):
        present_forbidden.extend(existing_forbidden_prefix_paths(root, prefix))

    missing_markers: list[str] = []
    for marker in contract.get("required_text_markers", []):
        path = root / marker["path"]
        expected = marker["contains"]
        if not path.is_file():
            missing_markers.append(f"{marker['path']} missing required marker {expected!r}")
            continue
        text = path.read_text(encoding="utf-8-sig")
        if expected not in text:
            missing_markers.append(f"{marker['path']} missing required marker {expected!r}")

    if missing_required or present_forbidden or missing_markers:
        print("Package authority scope check failed:")
        for path in missing_required:
            print(f"  - missing package-authorized artifact: {path}")
        for path in present_forbidden:
            print(f"  - out-of-scope artifact present: {path}")
        for marker in missing_markers:
            print(f"  - {marker}")
        return 1

    scope = contract.get("active_scope", {})
    packages = ", ".join(scope.get("authorized_packages", []))
    phases = ", ".join(scope.get("authorized_phases", []))
    print(f"Package authority scope check passed: {phases} from {packages}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
