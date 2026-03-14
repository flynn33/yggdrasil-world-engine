#!/usr/bin/env python3
"""Validate all JSON files in the Yggdrasil World Engine repository."""

import json
import os
import sys


def find_json_files(root):
    """Find all .json files in the repository."""
    json_files = []
    for dirpath, _, filenames in os.walk(root):
        if ".git" in dirpath:
            continue
        for f in filenames:
            if f.endswith(".json"):
                json_files.append(os.path.join(dirpath, f))
    return json_files


def validate_json_file(filepath):
    """Validate that a file contains valid JSON."""
    try:
        with open(filepath) as f:
            json.load(f)
        return None
    except json.JSONDecodeError as e:
        return str(e)


def check_realm_registry(root):
    """Verify the realm registry contains exactly nine canonical realms."""
    realms_path = os.path.join(root, "data", "realm_registry", "realms.json")
    if not os.path.isfile(realms_path):
        return ["Realm registry not found"]

    with open(realms_path) as f:
        data = json.load(f)

    canonical_realms = [
        "divine_core", "celestial", "causal", "mental",
        "astral", "etheric", "physical", "shadow", "void",
    ]
    errors = []
    realms = data.get("realms", [])
    if len(realms) != 9:
        errors.append(f"Expected 9 realms, found {len(realms)}")
    for realm in canonical_realms:
        if realm not in realms:
            errors.append(f"Missing canonical realm: {realm}")
    return errors


def check_player_schema(root):
    """Verify the player schema has required fields."""
    schema_path = os.path.join(root, "data", "player_schema.json")
    if not os.path.isfile(schema_path):
        return ["Player schema not found"]

    with open(schema_path) as f:
        data = json.load(f)

    required_fields = [
        "origin", "celestial_memory", "realm_attunement",
        "wolf_alignment", "bloodline_resonance", "awakening_fragments",
    ]
    errors = []
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field in player schema: {field}")

    wolf = data.get("wolf_alignment", {})
    if "white_wolf" not in wolf:
        errors.append("Missing white_wolf in wolf_alignment")
    if "dark_wolf" not in wolf:
        errors.append("Missing dark_wolf in wolf_alignment")

    return errors


def check_perception_overlay_rules(root):
    """Verify the canonical perception overlay rules artifact exists and has key sections."""
    rules_path = os.path.join(
        root, "data", "perception", "perception_overlay_rules.yaml"
    )
    if not os.path.isfile(rules_path):
        return ["Perception overlay rules artifact not found"]

    with open(rules_path) as f:
        content = f.read()

    required_markers = [
        "truth_boundary_rules:",
        "multiplayer_rules:",
        "myth_and_prophecy_integration:",
        "faction_integration:",
        "validation_rules:",
        "perception_is_not_world_rewrite",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Perception overlay rules missing required marker: {marker}"
            )

    return errors


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"Validating schemas at: {root}")

    errors = []

    # Validate all JSON files
    json_files = find_json_files(root)
    print(f"  Found {len(json_files)} JSON files")
    for filepath in json_files:
        rel_path = os.path.relpath(filepath, root)
        error = validate_json_file(filepath)
        if error:
            print(f"  FAIL: {rel_path} -- {error}")
            errors.append(f"Invalid JSON: {rel_path}")
        else:
            print(f"  PASS: {rel_path}")

    # Check realm registry
    realm_errors = check_realm_registry(root)
    if realm_errors:
        print("  FAIL: Realm Registry")
        for e in realm_errors:
            print(f"    - {e}")
        errors.extend(realm_errors)
    else:
        print("  PASS: Realm Registry (9 canonical realms)")

    # Check player schema
    player_errors = check_player_schema(root)
    if player_errors:
        print("  FAIL: Player Schema")
        for e in player_errors:
            print(f"    - {e}")
        errors.extend(player_errors)
    else:
        print("  PASS: Player Schema")

    # Check canonical perception overlay rules
    perception_errors = check_perception_overlay_rules(root)
    if perception_errors:
        print("  FAIL: Perception Overlay Rules")
        for e in perception_errors:
            print(f"    - {e}")
        errors.extend(perception_errors)
    else:
        print("  PASS: Perception Overlay Rules")

    if errors:
        print(f"\n{len(errors)} schema error(s) found.")
        sys.exit(1)
    else:
        print("\nSchema validation passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
