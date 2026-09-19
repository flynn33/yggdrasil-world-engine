#!/usr/bin/env python3
"""Validate Phase 9 pattern-vector and axiom-diagnostic schema semantics."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

PATTERN_VECTOR_PATH = "data/schemas/pattern_vector_schema.json"
AXIOM_SCHEMA_PATH = "data/schemas/axiom_diagnostic_packet_schema.json"
EXISTENCE_SCHEMA_PATH = "data/schemas/existence_potential_schema.json"
KERNEL_CONTRACT_PATH = "docs/architecture/existential_gameplay_kernel_contract.md"
BRANCH_EVENT_SCHEMA_PATH = "data/schemas/branch_event_schema.json"
BRANCH_EVENT_EXAMPLES_DIR = "examples/branch_reality"
PATTERN_VECTOR_EXAMPLE_PATH = "examples/branch_reality/pattern_vector_location_ravenfall_gate.example.json"
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

    try:
        Draft202012Validator.check_schema(data)
    except Exception as exc:
        errors.append(f"{PATTERN_VECTOR_PATH}: invalid JSON Schema: {exc}")
        return errors

    if data.get("$id") != "https://ywe.local/schemas/pattern_vector_schema.json":
        errors.append(f"{PATTERN_VECTOR_PATH}: missing canonical M2 $id")

    example_path = root / PATTERN_VECTOR_EXAMPLE_PATH
    if not example_path.is_file():
        errors.append(f"missing {PATTERN_VECTOR_EXAMPLE_PATH}")
        return errors

    example = load_json(root, PATTERN_VECTOR_EXAMPLE_PATH)
    validator = Draft202012Validator(data)
    valid_errors = list(validator.iter_errors(example))
    if valid_errors:
        errors.append(
            f"{PATTERN_VECTOR_EXAMPLE_PATH}: expected valid but failed: "
            f"{valid_errors[0].message}"
        )

    invalid_cases = {
        "missing_components": (
            {key: value for key, value in example.items() if key != "components"},
            "required",
        ),
        "unsupported_target_kind": (
            {**example, "target_kind": "unsupported_kind"},
            "enum",
        ),
        "entropy_above_one": (
            {**example, "components": {**example["components"], "H_entropy": 1.01}},
            "maximum",
        ),
        "fractal_dimension_below_one": (
            {**example, "components": {**example["components"], "D_fractal_dimension": 0.99}},
            "minimum",
        ),
        "unknown_component": (
            {**example, "components": {**example["components"], "unknown": 0.5}},
            "additionalProperties",
        ),
    }
    for case_name, (instance, expected_validator) in invalid_cases.items():
        case_errors = list(validator.iter_errors(instance))
        if not case_errors:
            errors.append(f"{PATTERN_VECTOR_PATH}: {case_name} was accepted")
        elif not any(error.validator == expected_validator for error in case_errors):
            errors.append(
                f"{PATTERN_VECTOR_PATH}: {case_name} failed for the wrong reason; "
                f"expected {expected_validator}, got {[error.validator for error in case_errors]}"
            )
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
