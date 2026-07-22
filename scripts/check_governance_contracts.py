#!/usr/bin/env python3
"""Validate repository governance, interface, licensing, and generation boundaries."""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

EXPECTED_LAYERS = ["Core", "Data", "Runtime", "Presentation", "Editor"]
CORE_ENGINES = {
    "cosmology_engine",
    "realm_engine",
    "ash_pattern_engine",
    "narrative_engine",
    "perception_engine",
}
CRITICAL_RULES = {"R001", "R002", "R003", "R004", "R006", "R007", "R008", "R011"}
WRW_CORE_MARKERS = (
    "Where Ravens Wait",
    "White Wolf",
    "Dark Wolf",
    "Divine Core",
    "Wolf resonance",
    "Wolf alignment",
)


def load_json(path: Path):
    with path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def find_true_flag(value, key: str, pointer=""):
    if isinstance(value, dict):
        if value.get(key) is True:
            yield pointer or "/"
        for child_key, child in value.items():
            yield from find_true_flag(child, key, f"{pointer}/{child_key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from find_true_flag(child, key, f"{pointer}/{index}")


def instruction_invariant_errors(instructions: dict) -> list[str]:
    """Validate the neutral-Core and WRW-profile invariant partitions."""
    errors: list[str] = []
    core = instructions.get("cosmological_invariants")
    wrw = instructions.get("wrw_reference_profile_invariants")
    if not isinstance(core, list) or any(not isinstance(item, str) or not item.strip() for item in core):
        errors.append("yggdrasil-instructions.json cosmological_invariants must be non-empty strings")
        core = []
    if not isinstance(wrw, list) or any(not isinstance(item, str) or not item.strip() for item in wrw):
        errors.append(
            "yggdrasil-instructions.json wrw_reference_profile_invariants must be non-empty strings"
        )
        wrw = []
    if len(core) < 3:
        errors.append("yggdrasil-instructions.json must define at least three neutral Core invariants")
    if len(wrw) < 7:
        errors.append("yggdrasil-instructions.json must define at least seven WRW profile invariants")
    if len(core) + len(wrw) < 10:
        errors.append("yggdrasil-instructions.json must define at least ten partitioned invariants")
    combined = [*core, *wrw]
    if len(combined) != len(set(combined)):
        errors.append("yggdrasil-instructions.json invariant partitions contain duplicate entries")
    for item in core:
        markers = [marker for marker in WRW_CORE_MARKERS if marker.casefold() in item.casefold()]
        if markers:
            errors.append(
                "yggdrasil-instructions.json neutral Core invariant contains WRW identity markers: "
                f"{markers}"
            )
    return errors


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []
    try:
        instructions = load_json(root / "yggdrasil-instructions.json")
        policy = load_json(root / "repository-contribution-policy.json")
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Governance contract check failed: {exc}")
        return 1

    required_instruction_keys = {
        "artifact_type",
        "artifact_version",
        "project",
        "principles",
        "architecture",
        "core_engines",
        "expansion_engines",
        "cosmological_invariants",
        "wrw_reference_profile_invariants",
    }
    missing = sorted(required_instruction_keys - set(instructions))
    if missing:
        errors.append(f"yggdrasil-instructions.json missing keys: {missing}")
    if instructions.get("project", {}).get("owner") != "Jim Daley":
        errors.append("yggdrasil-instructions.json owner must be Jim Daley")
    if "Forsetti" not in instructions.get("project", {}).get("framework", ""):
        errors.append("yggdrasil-instructions.json must identify the Forsetti framework")
    if len(instructions.get("principles", [])) < 5:
        errors.append("yggdrasil-instructions.json must define at least five principles")
    errors.extend(instruction_invariant_errors(instructions))

    layers = instructions.get("architecture", {}).get("layers", [])
    layer_names = [layer.get("name") for layer in layers]
    if layer_names != EXPECTED_LAYERS:
        errors.append(f"Architecture layers must be ordered {EXPECTED_LAYERS}; found {layer_names}")
    layer_positions = {name: index for index, name in enumerate(layer_names)}
    for index, layer in enumerate(layers):
        for dependency in layer.get("allowed_dependencies", []):
            dependency_index = layer_positions.get(dependency)
            if dependency_index is None or dependency_index >= index:
                errors.append(f"Layer {layer.get('name')} has invalid dependency {dependency}")
    if not CORE_ENGINES.issubset(set(instructions.get("core_engines", []))):
        errors.append("yggdrasil-instructions.json is missing a required core engine")

    if policy.get("owner") != "Jim Daley":
        errors.append("repository-contribution-policy.json owner must be Jim Daley")
    if "Forsetti" not in policy.get("framework", ""):
        errors.append("repository-contribution-policy.json must identify the Forsetti framework")
    rule_ids = {rule.get("id") for rule in policy.get("mandatory_rules", [])}
    if not CRITICAL_RULES.issubset(rule_ids):
        errors.append(f"Contribution policy is missing critical rules: {sorted(CRITICAL_RULES - rule_ids)}")
    for mode in ("spec_repo_mode", "engine_repo_mode"):
        if mode not in policy.get("operating_modes", {}):
            errors.append(f"Contribution policy is missing operating mode {mode}")

    for engine in sorted(CORE_ENGINES):
        path = root / "core" / engine / "engine_interface.json"
        if not path.is_file():
            errors.append(f"Missing core interface {path.relative_to(root)}")
            continue
        interface = load_json(path)
        for field in ("engine_id", "purpose", "layer", "methods"):
            if field not in interface:
                errors.append(f"{path.relative_to(root)} missing {field}")
        if interface.get("layer") != "core":
            errors.append(f"{path.relative_to(root)} must declare layer core")
        for dependency in interface.get("dependencies", []):
            if dependency.split(".")[-1] not in CORE_ENGINES:
                errors.append(f"{path.relative_to(root)} has unknown core dependency {dependency}")

    for module_path in sorted(path for path in (root / "modules").iterdir() if path.is_dir()):
        interfaces = sorted(module_path.glob("*_interface.json"))
        if not interfaces:
            errors.append(f"Missing module interface in {module_path.relative_to(root)}")
        for path in interfaces:
            interface = load_json(path)
            for field in ("engine_id", "purpose", "layer", "methods"):
                if field not in interface:
                    errors.append(f"{path.relative_to(root)} missing {field}")
            if interface.get("layer") != "module":
                errors.append(f"{path.relative_to(root)} must declare layer module")
            dependency_names = {value.split(".")[-1] for value in interface.get("dependencies", [])}
            if "ash_pattern_engine" not in dependency_names:
                errors.append(f"{path.relative_to(root)} must depend on ash_pattern_engine")

    for code_root in (root / "core", root / "modules"):
        for path in sorted(code_root.rglob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            except (OSError, SyntaxError, UnicodeDecodeError) as exc:
                errors.append(f"Unable to inspect {path.relative_to(root)}: {exc}")
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import) and any(alias.name == "random" for alias in node.names):
                    errors.append(f"Independent random source imported in {path.relative_to(root)}:{node.lineno}")
                if isinstance(node, ast.ImportFrom) and node.module == "random":
                    errors.append(f"Independent random source imported in {path.relative_to(root)}:{node.lineno}")

    for path in sorted(root.rglob("*.json")):
        if ".git" in path.parts:
            continue
        try:
            document = load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        for pointer in find_true_flag(document, "independent_random_allowed"):
            errors.append(f"{path.relative_to(root)}{pointer} permits an independent random source")

    readme = (root / "README.md").read_text(encoding="utf-8-sig")
    license_text = (root / "LICENSE").read_text(encoding="utf-8-sig")
    governance_text = (root / "docs/governance/forsetti_governance_alignment.md").read_text(
        encoding="utf-8-sig"
    )
    if "Apache License" not in license_text or "Apache License, Version 2.0" not in readme:
        errors.append("README and LICENSE must declare the Apache License, Version 2.0")
    if "MIT-licensed" in governance_text:
        errors.append("Forsetti governance documentation conflicts with the repository license")

    if errors:
        print("Governance contract check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("Governance contract check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
