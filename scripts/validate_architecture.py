#!/usr/bin/env python3
"""Validate the Yggdrasil World Engine repository architecture."""

import json
import os
import sys


def check_directory_structure(root):
    """Verify all required directories exist."""
    required_dirs = [
        "core/cosmology_engine",
        "core/realm_engine",
        "core/ash_pattern_engine",
        "core/narrative_engine",
        "core/perception_engine",
        "modules/quest_engine",
        "modules/myth_engine",
        "modules/prophecy_engine",
        "modules/artifact_engine",
        "modules/creature_engine",
        "data/realm_registry",
        "data/pattern_archetypes",
        "data/quest_archetypes",
        "data/myth_archetypes",
        "data/bloodline_registry",
        "data/perception",
        "lore/wrw_cosmology",
        "lore/wolf_canon",
        "lore/bloodline_history",
        "adapters/unity",
        "adapters/unreal",
        "adapters/godot",
        "docs/master_specification",
        "docs/architecture",
        "docs/ash_compliance",
    ]
    errors = []
    for d in required_dirs:
        full_path = os.path.join(root, d)
        if not os.path.isdir(full_path):
            errors.append(f"Missing directory: {d}")
    return errors


def check_core_engine_files(root):
    """Verify each core engine has required files."""
    core_engines = [
        "cosmology_engine",
        "realm_engine",
        "ash_pattern_engine",
        "narrative_engine",
        "perception_engine",
    ]
    errors = []
    for engine in core_engines:
        engine_dir = os.path.join(root, "core", engine)
        if not os.path.isdir(engine_dir):
            errors.append(f"Missing core engine directory: core/{engine}")
            continue
        required_files = ["README.md", "engine_interface.json"]
        for f in required_files:
            if not os.path.isfile(os.path.join(engine_dir, f)):
                errors.append(f"Missing file: core/{engine}/{f}")
    return errors


def check_module_files(root):
    """Verify each expansion module has required files."""
    modules = [
        "quest_engine",
        "myth_engine",
        "prophecy_engine",
        "artifact_engine",
        "creature_engine",
    ]
    errors = []
    for module in modules:
        module_dir = os.path.join(root, "modules", module)
        if not os.path.isdir(module_dir):
            errors.append(f"Missing module directory: modules/{module}")
            continue
        if not os.path.isfile(os.path.join(module_dir, "README.md")):
            errors.append(f"Missing file: modules/{module}/README.md")
    return errors


def check_data_schemas(root):
    """Verify required data schemas exist and are valid JSON."""
    required_schemas = [
        "data/player_schema.json",
        "data/realm_registry/realms.json",
        "data/pattern_archetypes/pattern_schema.json",
        "data/quest_archetypes/quest_seed_schema.json",
        "data/myth_archetypes/myth_schema.json",
        "data/bloodline_registry/bloodline_schema.json",
    ]
    errors = []
    for schema_path in required_schemas:
        full_path = os.path.join(root, schema_path)
        if not os.path.isfile(full_path):
            errors.append(f"Missing schema: {schema_path}")
            continue
        try:
            with open(full_path) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in {schema_path}: {e}")
    return errors


def check_canonical_data_artifacts(root):
    """Verify required canonical non-JSON data artifacts exist."""
    required_artifacts = [
        "data/perception/perception_overlay_rules.yaml",
    ]
    errors = []
    for artifact_path in required_artifacts:
        if not os.path.isfile(os.path.join(root, artifact_path)):
            errors.append(f"Missing canonical artifact: {artifact_path}")
    return errors


def check_governance_files(root):
    """Verify governance files exist."""
    required_files = [
        "yggdrasil-instructions.json",
        "agentic-coding-policy.json",
        "guide.md",
        "developer-guide.md",
        "wiki.md",
        "README.md",
        "LICENSE",
        "CONTRIBUTING.md",
    ]
    errors = []
    for f in required_files:
        if not os.path.isfile(os.path.join(root, f)):
            errors.append(f"Missing governance file: {f}")
    return errors


def check_adapter_files(root):
    """Verify adapter directories have required files."""
    adapters = ["unity", "unreal", "godot"]
    errors = []
    for adapter in adapters:
        adapter_dir = os.path.join(root, "adapters", adapter)
        if not os.path.isdir(adapter_dir):
            errors.append(f"Missing adapter directory: adapters/{adapter}")
            continue
        required_files = [
            "README.md",
            "adapter_interface.md",
            "environment_bridge.md",
            "entity_spawn_bridge.md",
        ]
        for f in required_files:
            if not os.path.isfile(os.path.join(adapter_dir, f)):
                errors.append(f"Missing file: adapters/{adapter}/{f}")
    return errors


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"Validating architecture at: {root}")

    all_errors = []
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Core Engine Files", check_core_engine_files),
        ("Module Files", check_module_files),
        ("Data Schemas", check_data_schemas),
        ("Canonical Data Artifacts", check_canonical_data_artifacts),
        ("Governance Files", check_governance_files),
        ("Adapter Files", check_adapter_files),
    ]

    for name, check_fn in checks:
        errors = check_fn(root)
        if errors:
            print(f"  FAIL: {name}")
            for e in errors:
                print(f"    - {e}")
            all_errors.extend(errors)
        else:
            print(f"  PASS: {name}")

    if all_errors:
        print(f"\n{len(all_errors)} architecture error(s) found.")
        sys.exit(1)
    else:
        print("\nArchitecture validation passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
