#!/usr/bin/env python3
"""Validate the active Phase 8-9 boundary and deferred later-phase markers."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CONTRACT_PATH = "data/validation/phase_8_9_package_boundary_guardrail.json"
REQUIRED_PHASE_8_9_PATH = "data/validation/required_phase_8_9_artifacts.json"
TEXT_ENCODING = "utf-8-sig"


def relative_name(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_json_checked(root: Path, path: Path, errors: list[str]) -> dict | None:
    path_name = relative_name(root, path)
    if not path.is_file():
        errors.append(f"missing required JSON file: {path_name}")
        return None

    try:
        return json.loads(path.read_text(encoding=TEXT_ENCODING))
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path_name}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"unable to read {path_name}: {exc}")
    return None


def collect_required_phase_8_9(root: Path, errors: list[str]) -> list[str]:
    contract = load_json_checked(root, root / REQUIRED_PHASE_8_9_PATH, errors)
    if contract is None:
        return []

    required = [REQUIRED_PHASE_8_9_PATH]
    for key in (
        "phase_8",
        "phase_9_architecture_contracts",
        "phase_9_schemas",
        "phase_9_validation",
    ):
        required.extend(contract.get(key, []))
    return required


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []
    contract = load_json_checked(root, root / CONTRACT_PATH, errors)
    if contract is None:
        print("Phase 8-9 package boundary check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    marker = contract.get("deferred_marker")
    if not isinstance(marker, str) or not marker:
        errors.append(f"{CONTRACT_PATH} missing deferred_marker string")
        marker = ""

    for rel in collect_required_phase_8_9(root, errors):
        if not (root / rel).is_file():
            errors.append(f"missing Phase 8-9 artifact: {rel}")

    deferred_artifacts = contract.get("deferred_phase_artifacts", [])
    for rel in deferred_artifacts:
        if not (root / rel).is_file():
            errors.append(f"missing preserved deferred artifact: {rel}")

    marker_locations = list(dict.fromkeys([*contract.get("required_marker_locations", []), *deferred_artifacts]))
    for rel in marker_locations:
        path = root / rel
        if not path.is_file():
            errors.append(f"missing marker file: {rel}")
            continue
        try:
            marker_text = path.read_text(encoding=TEXT_ENCODING)
        except OSError as exc:
            errors.append(f"unable to read marker file {rel}: {exc}")
            continue
        if marker and marker not in marker_text:
            errors.append(f"missing deferred marker in {rel}")

    status_doc = root / "docs/project/repository_status.md"
    status_text = ""
    if status_doc.is_file():
        try:
            status_text = status_doc.read_text(encoding=TEXT_ENCODING)
        except OSError as exc:
            errors.append(f"unable to read repository status: {exc}")
    else:
        errors.append("missing repository status file: docs/project/repository_status.md")

    for expected in contract.get("required_status_markers", []):
        if expected not in status_text:
            errors.append(f"repository status missing marker: {expected}")

    if errors:
        print("Phase 8-9 package boundary check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Phase 8-9 package boundary check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
