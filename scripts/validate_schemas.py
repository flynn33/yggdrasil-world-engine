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


def check_realm_mechanics_rules(root):
    """Verify the canonical realm mechanics rules artifact exists and has key sections."""
    rules_path = os.path.join(
        root, "data", "realm", "realm_mechanics_rules.yaml"
    )
    if not os.path.isfile(rules_path):
        return ["Realm mechanics rules artifact not found"]

    with open(rules_path) as f:
        content = f.read()

    required_markers = [
        "canonical_realm_set:",
        "attunement_rules:",
        "boundary_condition_rules:",
        "travel_and_shift_rules:",
        "realm_bleed_rules:",
        "manifestation_window_rules:",
        "site_rules:",
        "interaction_with_other_systems:",
        "truth_boundary_rules:",
        "validation_rules:",
        "physical_realm_access_is_always_true",
        "realm_shift_is_not_generic_fast_travel",
        "realm_truth_is_not_perception_overlay",
        "thin_veil_site",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Realm mechanics rules missing required marker: {marker}"
            )

    return errors


def check_faction_topology_schema(root):
    """Verify canonical faction topology schema exists and has required sections."""
    schema_path = os.path.join(
        root, "data", "faction_topology", "faction_topology_state_schema.yaml"
    )
    if not os.path.isfile(schema_path):
        return ["Faction topology state schema artifact not found"]

    with open(schema_path) as f:
        content = f.read()

    required_markers = [
        "core_surfaces:",
        "topology_state_record:",
        "FactionClaimRecord:",
        "FactionLegitimacyRecord:",
        "FactionSuccessionRecord:",
        "FactionSchismRecord:",
        "FactionReformRecord:",
        "FactionPresenceRecord:",
        "FactionCovertRelationRecord:",
        "invariants:",
        "validation_rules:",
        "faction_topology_is_structural_not_moral_slider",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Faction topology schema missing required marker: {marker}"
            )

    return errors


def check_realm_boundary_profiles(root):
    """Verify canonical realm boundary profiles artifact exists and has key sections."""
    rules_path = os.path.join(
        root, "data", "realm", "realm_boundary_profiles.yaml"
    )
    if not os.path.isfile(rules_path):
        return ["Realm boundary profiles artifact not found"]

    with open(rules_path) as f:
        content = f.read()

    required_markers = [
        "boundary_profile_schema:",
        "RealmBoundaryProfileRecord:",
        "profile_catalog:",
        "invariants:",
        "validation_rules:",
        "boundary_class:",
        "transition_permissions:",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Realm boundary profiles missing required marker: {marker}"
            )

    return errors


def check_realm_transition_examples(root):
    """Verify canonical realm transition examples artifact exists and has key sections."""
    rules_path = os.path.join(
        root, "data", "realm", "realm_transition_examples.yaml"
    )
    if not os.path.isfile(rules_path):
        return ["Realm transition examples artifact not found"]

    with open(rules_path) as f:
        content = f.read()

    required_markers = [
        "transition_example_schema:",
        "RealmTransitionExampleRecord:",
        "lawful_examples:",
        "unlawful_examples:",
        "validation_rules:",
        "realm_shift_is_not_generic_fast_travel",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Realm transition examples missing required marker: {marker}"
            )

    return errors


def check_realm_truth_boundary_contract(root):
    """Verify canonical realm truth boundary contract exists and has required sections."""
    contract_path = os.path.join(
        root, "docs", "architecture", "realm_truth_boundary_contract.md"
    )
    if not os.path.isfile(contract_path):
        return ["Realm truth boundary contract not found"]

    with open(contract_path) as f:
        content = f.read()

    required_markers = [
        "## Authority Order",
        "## Truth Layers",
        "## Boundary Rules",
        "## Cross-System Contracts",
        "## Multiplayer Safety Rules",
        "## Validation Requirements",
        "## Forbidden Design Moves",
        "## Status",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Realm truth boundary contract missing required marker: {marker}"
            )

    return errors


def check_source_inventory(root):
    """Verify source inventory exists and references promoted canonical artifacts."""
    inventory_path = os.path.join(root, "missing_source_documents.md")
    if not os.path.isfile(inventory_path):
        return ["Source inventory file not found: missing_source_documents.md"]

    with open(inventory_path) as f:
        content = f.read()

    required_entries = [
        "data/perception/perception_overlay_rules.yaml",
        "data/realm/realm_mechanics_rules.yaml",
        "data/realm/realm_boundary_profiles.yaml",
        "data/realm/realm_transition_examples.yaml",
        "data/faction_topology/faction_topology_state_schema.yaml",
        "docs/architecture/realm_truth_boundary_contract.md",
        "docs/architecture/authored_override_and_tooling_notes.md",
    ]

    errors = []
    for entry in required_entries:
        if entry not in content:
            errors.append(
                f"Source inventory missing canonical entry: {entry}"
            )

    return errors


def check_authored_override_notes(root):
    """Verify canonical authored override and tooling control notes exist and contain guardrail sections."""
    notes_path = os.path.join(
        root, "docs", "architecture", "authored_override_and_tooling_notes.md"
    )
    if not os.path.isfile(notes_path):
        return ["Authored override and tooling notes not found"]

    with open(notes_path) as f:
        content = f.read()

    required_markers = [
        "## Authority Order",
        "## Allowed Override Types",
        "## Forbidden Override Types",
        "## Override Strength Bands",
        "## Required Metadata for Every Override",
        "## Tooling Categories",
        "## Required Debug / Explainability Surfaces",
        "## Logging and Audit Rules",
        "## Multiplayer and Shared-State Safety",
        "## Forbidden Tooling Behaviors",
        "## Final Rule",
        "Authored content may guide YWE.",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Authored override notes missing required marker: {marker}"
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

    # Check canonical realm mechanics rules
    realm_mechanics_errors = check_realm_mechanics_rules(root)
    if realm_mechanics_errors:
        print("  FAIL: Realm Mechanics Rules")
        for e in realm_mechanics_errors:
            print(f"    - {e}")
        errors.extend(realm_mechanics_errors)
    else:
        print("  PASS: Realm Mechanics Rules")

    # Check canonical faction topology schema
    faction_topology_errors = check_faction_topology_schema(root)
    if faction_topology_errors:
        print("  FAIL: Faction Topology Schema")
        for e in faction_topology_errors:
            print(f"    - {e}")
        errors.extend(faction_topology_errors)
    else:
        print("  PASS: Faction Topology Schema")

    # Check canonical realm boundary profiles
    boundary_profile_errors = check_realm_boundary_profiles(root)
    if boundary_profile_errors:
        print("  FAIL: Realm Boundary Profiles")
        for e in boundary_profile_errors:
            print(f"    - {e}")
        errors.extend(boundary_profile_errors)
    else:
        print("  PASS: Realm Boundary Profiles")

    # Check canonical realm transition examples
    transition_example_errors = check_realm_transition_examples(root)
    if transition_example_errors:
        print("  FAIL: Realm Transition Examples")
        for e in transition_example_errors:
            print(f"    - {e}")
        errors.extend(transition_example_errors)
    else:
        print("  PASS: Realm Transition Examples")

    # Check source inventory reflects promoted canonical artifacts
    source_inventory_errors = check_source_inventory(root)
    if source_inventory_errors:
        print("  FAIL: Source Inventory")
        for e in source_inventory_errors:
            print(f"    - {e}")
        errors.extend(source_inventory_errors)
    else:
        print("  PASS: Source Inventory")

    # Check authored override and tooling control notes
    authored_notes_errors = check_authored_override_notes(root)
    if authored_notes_errors:
        print("  FAIL: Authored Override Notes")
        for e in authored_notes_errors:
            print(f"    - {e}")
        errors.extend(authored_notes_errors)
    else:
        print("  PASS: Authored Override Notes")

    # Check canonical realm truth boundary contract
    boundary_contract_errors = check_realm_truth_boundary_contract(root)
    if boundary_contract_errors:
        print("  FAIL: Realm Truth Boundary Contract")
        for e in boundary_contract_errors:
            print(f"    - {e}")
        errors.extend(boundary_contract_errors)
    else:
        print("  PASS: Realm Truth Boundary Contract")

    if errors:
        print(f"\n{len(errors)} schema error(s) found.")
        sys.exit(1)
    else:
        print("\nSchema validation passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
