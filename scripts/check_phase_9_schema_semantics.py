#!/usr/bin/env python3
"""Validate Phase 9 pattern-vector and axiom-diagnostic schema semantics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PATTERN_VECTOR_PATH = "data/schemas/pattern_vector_schema.json"
AXIOM_SCHEMA_PATH = "data/schemas/axiom_diagnostic_packet_schema.json"
EXISTENCE_SCHEMA_PATH = "data/schemas/existence_potential_schema.json"
KERNEL_CONTRACT_PATH = "docs/architecture/existential_gameplay_kernel_contract.md"
BRANCH_EVENT_SCHEMA_PATH = "data/schemas/branch_event_schema.json"
BRANCH_EVENT_EXAMPLES_DIR = "examples/branch_reality"
PATTERN_COMPONENTS = (
    "H_entropy",
    "K_algorithmic_complexity",
    "D_fractal_dimension",
    "S_symmetry_index",
    "L_generator_length",
)
REQUIRED_AXIOMS = ("A1", "A2", "A3", "A4", "A5", "A6")
REQUIRED_TERMS = ("Phi", "compressibility", "symmetry", "persistence", "entropy")


def load_json(root: Path, rel: str) -> dict:
    return json.loads((root / rel).read_text(encoding="utf-8-sig"))


def check_pattern_vector(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / PATTERN_VECTOR_PATH
    if not path.is_file():
        return [f"missing {PATTERN_VECTOR_PATH}"]

    data = load_json(root, PATTERN_VECTOR_PATH)
    components = data.get("components", {})
    for component in PATTERN_COMPONENTS:
        if component not in components:
            errors.append(f"{PATTERN_VECTOR_PATH}: missing components.{component}")
    return errors


def check_axioms(root: Path) -> list[str]:
    errors: list[str] = []
    for rel in (AXIOM_SCHEMA_PATH, EXISTENCE_SCHEMA_PATH, KERNEL_CONTRACT_PATH):
        if not (root / rel).is_file():
            errors.append(f"missing {rel}")
    if errors:
        return errors

    combined = "\n".join(
        (root / rel).read_text(encoding="utf-8-sig")
        for rel in (AXIOM_SCHEMA_PATH, EXISTENCE_SCHEMA_PATH, KERNEL_CONTRACT_PATH)
    )
    for axiom in REQUIRED_AXIOMS:
        if axiom not in combined:
            errors.append(f"missing axiom marker {axiom}")
    for term in REQUIRED_TERMS:
        if term.lower() not in combined.lower():
            errors.append(f"missing required term {term}")
    return errors


def check_branch_event_examples(root: Path) -> list[str]:
    errors: list[str] = []
    schema_path = root / BRANCH_EVENT_SCHEMA_PATH
    examples_dir = root / BRANCH_EVENT_EXAMPLES_DIR
    if not schema_path.is_file() or not examples_dir.is_dir():
        return errors

    required = set(load_json(root, BRANCH_EVENT_SCHEMA_PATH).get("required_fields", []))
    for path in sorted(examples_dir.glob("*branch_event*.example.json")):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        missing = sorted(required - set(data.keys()))
        if missing:
            errors.append(
                f"{path.relative_to(root).as_posix()}: missing required fields {', '.join(missing)}"
            )
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors = check_pattern_vector(root) + check_axioms(root) + check_branch_event_examples(root)
    if errors:
        print("Phase 9 schema semantic check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Phase 9 schema semantic check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
