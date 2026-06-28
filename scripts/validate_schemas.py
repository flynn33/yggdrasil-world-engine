#!/usr/bin/env python3
"""Validate all JSON files in the Yggdrasil World Engine repository."""

import json
import os
import sys

TEXT_ENCODING = "utf-8-sig"
EXCLUDED_DIRS = {".git", ".vs", "__pycache__", "node_modules"}
APPLIED_MODULE_CAPABILITY_MANIFESTS = [
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "cosmology_engine.yaml"
        ),
        "module_id": "com.ywe.core.cosmology-engine",
        "module_classification": "core_engine",
        "template_path": os.path.join(
            "core", "cosmology_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "realm_engine.yaml"
        ),
        "module_id": "com.ywe.core.realm-engine",
        "module_classification": "core_engine",
        "template_path": os.path.join(
            "core", "realm_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "ash_pattern_engine.yaml"
        ),
        "module_id": "com.ywe.core.ash-pattern-engine",
        "module_classification": "core_engine",
        "template_path": os.path.join(
            "core", "ash_pattern_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "narrative_engine.yaml"
        ),
        "module_id": "com.ywe.core.narrative-engine",
        "module_classification": "core_engine",
        "template_path": os.path.join(
            "core", "narrative_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "perception_engine.yaml"
        ),
        "module_id": "com.ywe.core.perception-engine",
        "module_classification": "core_engine",
        "template_path": os.path.join(
            "core", "perception_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "quest_engine.yaml"
        ),
        "module_id": "com.ywe.module.quest-engine",
        "module_classification": "feature_module",
        "template_path": os.path.join(
            "modules", "quest_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "myth_engine.yaml"
        ),
        "module_id": "com.ywe.module.myth-engine",
        "module_classification": "feature_module",
        "template_path": os.path.join(
            "modules", "myth_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "prophecy_engine.yaml"
        ),
        "module_id": "com.ywe.module.prophecy-engine",
        "module_classification": "feature_module",
        "template_path": os.path.join(
            "modules", "prophecy_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "artifact_engine.yaml"
        ),
        "module_id": "com.ywe.module.artifact-engine",
        "module_classification": "feature_module",
        "template_path": os.path.join(
            "modules", "artifact_engine", "forsetti_module_manifest.template.json"
        ),
    },
    {
        "path": os.path.join(
            "data", "module_capability", "manifests", "creature_engine.yaml"
        ),
        "module_id": "com.ywe.module.creature-engine",
        "module_classification": "feature_module",
        "template_path": os.path.join(
            "modules", "creature_engine", "forsetti_module_manifest.template.json"
        ),
    },
]


def read_text_file(filepath):
    """Read a repository text file using the expected encoding."""
    with open(filepath, encoding=TEXT_ENCODING) as f:
        return f.read()


def load_json_file(filepath):
    """Load a repository JSON file using the expected encoding."""
    with open(filepath, encoding=TEXT_ENCODING) as f:
        return json.load(f)


def get_manifest_placeholder_names(root):
    """Return placeholder source names tracked in SOURCE_AVAILABILITY_MANIFEST.md."""
    manifest_path = os.path.join(root, "SOURCE_AVAILABILITY_MANIFEST.md")
    if not os.path.isfile(manifest_path):
        return []

    content = read_text_file(manifest_path)
    lines = content.splitlines()
    placeholder_names = []
    in_section = False

    for line in lines:
        if line.startswith("## Present as placeholders"):
            in_section = True
            continue

        if in_section and line.startswith("## "):
            break

        if in_section and line.startswith("- `") and "` -> `" in line:
            parts = line.split("`")
            if len(parts) >= 2:
                placeholder_names.append(parts[1])

    return placeholder_names


def is_placeholder_backed(root, entry_name):
    """Return whether a manifest-tracked placeholder entry is still placeholder-backed."""
    manifest_path = os.path.join(root, "SOURCE_AVAILABILITY_MANIFEST.md")
    if not os.path.isfile(manifest_path):
        return False

    content = read_text_file(manifest_path)
    target_path = None
    for line in content.splitlines():
        if line.startswith(f"- `{entry_name}` -> `"):
            parts = line.split("`")
            if len(parts) >= 4:
                target_path = parts[3]
                break

    if not target_path:
        return False

    full_path = os.path.join(root, target_path)
    if not os.path.isfile(full_path):
        return True

    placeholder_markers = [
        "placeholder awaiting finalized content",
        "placeholder_awaiting_finalized_content",
        "document structure placeholder",
        "module interface contract placeholder",
    ]
    file_content = read_text_file(full_path)
    return any(marker in file_content for marker in placeholder_markers)


def find_json_files(root):
    """Find all .json files in the repository."""
    json_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for f in filenames:
            if f.endswith(".json"):
                json_files.append(os.path.join(dirpath, f))
    return json_files


def validate_json_file(filepath):
    """Validate that a file contains valid JSON."""
    try:
        load_json_file(filepath)
        return None
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return str(e)


def check_realm_registry(root):
    """Verify the realm registry contains exactly nine canonical realms."""
    realms_path = os.path.join(root, "data", "realm_registry", "realms.json")
    if not os.path.isfile(realms_path):
        return ["Realm registry not found"]

    data = load_json_file(realms_path)

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

    data = load_json_file(schema_path)

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

    content = read_text_file(rules_path)

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

    content = read_text_file(rules_path)

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

    content = read_text_file(schema_path)

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

    content = read_text_file(rules_path)

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

    content = read_text_file(rules_path)

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


def check_module_capability_manifest_schema(root):
    """Verify canonical module capability manifest schema exists and has key sections."""
    schema_path = os.path.join(
        root, "data", "module_capability", "module_capability_manifest_schema.yaml"
    )
    if not os.path.isfile(schema_path):
        return ["Module capability manifest schema not found"]

    content = read_text_file(schema_path)

    required_markers = [
        "classification_enums:",
        "core_schema:",
        "ModuleCapabilityManifest:",
        "provides_capabilities:",
        "requires_capabilities:",
        "consumes_state:",
        "emits_state:",
        "non_delegable_responsibilities:",
        "delegable_compatible_responsibilities:",
        "suppression_conditions:",
        "compatible_external_capabilities:",
        "canonical_validation_rules:",
        "truth_boundary_rules:",
        "dependency_rules:",
        "anti_drift_rules:",
        "forsetti_governs_module_lifecycle",
        "external_environments_may_realize_but_may_not_author_ywe_truth",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Module capability manifest schema missing required marker: {marker}"
            )

    return errors


def check_first_darkness_and_divine_core(root):
    """Verify the primary origin cosmology lore artifact exists and carries key canon."""
    path = os.path.join(
        root, "lore", "wrw_cosmology", "first_darkness_and_divine_core.md"
    )
    if not os.path.isfile(path):
        return ["First Darkness and Divine Core lore artifact not found"]

    content = read_text_file(path)
    required_markers = [
        "Dark Star",
        "gravity",
        "time",
        "Void",
        "Divine Core",
        "nine realms or planes",
        "Architects",
        "first wolves",
        "**realm** and **plane** are equivalent",
        "Grand Architect",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"First Darkness and Divine Core lore artifact missing required marker: {marker}"
            )

    return errors


def check_two_wolves_and_balance(root):
    """Verify the canonical wolf balance lore artifact exists and carries key canon."""
    path = os.path.join(
        root, "lore", "wolf_canon", "two_wolves_and_balance.md"
    )
    if not os.path.isfile(path):
        return ["Two Wolves and Balance lore artifact not found"]

    content = read_text_file(path)
    required_markers = [
        "complementary opposites",
        "not moral opposites",
        "not good and evil",
        "not a morality system",
        "paired symbiotic companions of consciousness",
        "Every conscious being carries both",
        "Each wolf has what the other needs",
        "balance",
        "physically walk",
        "assist in quests",
        "assist in combat",
        "cannot be killed",
        "temporarily decohere",
        "later return",
        "not enemies",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Two Wolves and Balance lore artifact missing required marker: {marker}"
            )

    return errors


def check_trial_of_return_michael_lucifer_odin(root):
    """Verify the Trial of Return lore artifact exists and carries key canon."""
    path = os.path.join(
        root, "lore", "wrw_cosmology", "trial_of_return_michael_lucifer_odin.md"
    )
    if not os.path.isfile(path):
        return ["Trial of Return lore artifact not found"]

    content = read_text_file(path)
    required_markers = [
        "First War",
        "Great Trial",
        "Seventh Gate",
        "Odin",
        "Dark Wolf",
        "Michael",
        "Yggdrasil",
        "mortal is an instantiated expression of a celestial being",
        "not the source of all pantheons",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Trial of Return lore artifact missing required marker: {marker}"
            )

    return errors


def check_master_spec_lore_alignment(root):
    """Verify the master spec reflects the corrected lore canon without old phrases."""
    path = os.path.join(
        root, "docs", "master_specification", "YWE_MASTER_SPECIFICATION.md"
    )
    if not os.path.isfile(path):
        return ["Master specification not found for lore alignment check"]

    content = read_text_file(path)
    required_markers = [
        "Dark Star",
        "**realm** and **plane** are equivalent",
        "balance, not domination",
        "temporary coherence loss",
    ]
    forbidden_markers = [
        "White Wolf and Dark Wolf predate all realms",
        "wolf dematerializes",
        "rematerializes later",
    ]

    errors = []
    for marker in required_markers:
        if marker not in content:
            errors.append(
                f"Master specification missing corrected lore marker: {marker}"
            )

    for marker in forbidden_markers:
        if marker in content:
            errors.append(
                f"Master specification still contains stale lore phrasing: {marker}"
            )

    return errors


def check_applied_module_capability_manifests(root):
    """Verify canonical applied module capability manifests exist and align to templates."""
    manifests_dir = os.path.join(root, "data", "module_capability", "manifests")
    if not os.path.isdir(manifests_dir):
        return ["Applied module capability manifests directory not found"]

    required_markers = [
        'manifest_version: "0.2"',
        "authority_class:",
        "provides_capabilities:",
        "requires_capabilities:",
        "consumes_state:",
        "emits_state:",
        "non_delegable_responsibilities:",
        "delegable_compatible_responsibilities:",
        "suppression_conditions:",
        "compatible_external_capabilities:",
        "invariant_guardrails:",
        "validation_requirements:",
    ]
    placeholder_markers = [
        "placeholder awaiting finalized content",
        "placeholder_awaiting_finalized_content",
    ]

    errors = []
    for manifest in APPLIED_MODULE_CAPABILITY_MANIFESTS:
        manifest_path = os.path.join(root, manifest["path"])
        if not os.path.isfile(manifest_path):
            errors.append(
                f"Applied module capability manifest not found: {manifest['path']}"
            )
            continue

        content = read_text_file(manifest_path)
        if any(marker in content for marker in placeholder_markers):
            errors.append(
                f"Applied module capability manifest remains placeholder-backed: {manifest['path']}"
            )

        manifest_specific_markers = required_markers + [
            f"module_id: {manifest['module_id']}",
            f"module_classification: {manifest['module_classification']}",
        ]
        for marker in manifest_specific_markers:
            if marker not in content:
                errors.append(
                    f"Applied module capability manifest missing required marker '{marker}': {manifest['path']}"
                )

        template_path = os.path.join(root, manifest["template_path"])
        if not os.path.isfile(template_path):
            errors.append(
                f"Forsetti template manifest not found for applied capability manifest: {manifest['template_path']}"
            )
            continue

        template_json = load_json_file(template_path)
        if template_json.get("moduleID") != manifest["module_id"]:
            errors.append(
                "Applied module capability manifest module_id does not match "
                f"template moduleID for {manifest['path']}"
            )

    return errors


def check_realm_truth_boundary_contract(root):
    """Verify canonical realm truth boundary contract exists and has required sections."""
    contract_path = os.path.join(
        root, "docs", "architecture", "realm_truth_boundary_contract.md"
    )
    if not os.path.isfile(contract_path):
        return ["Realm truth boundary contract not found"]

    content = read_text_file(contract_path)

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

    content = read_text_file(inventory_path)

    required_entries = [
        "data/perception/perception_overlay_rules.yaml",
        "data/realm/realm_mechanics_rules.yaml",
        "data/realm/realm_boundary_profiles.yaml",
        "data/realm/realm_transition_examples.yaml",
        "data/module_capability/module_capability_manifest_schema.yaml",
        "data/module_capability/manifests/*.yaml",
        "data/faction_topology/faction_topology_state_schema.yaml",
        "lore/wrw_cosmology/first_darkness_and_divine_core.md",
        "lore/wrw_cosmology/trial_of_return_michael_lucifer_odin.md",
        "lore/wolf_canon/two_wolves_and_balance.md",
        "docs/architecture/realm_truth_boundary_contract.md",
        "docs/architecture/authored_override_and_tooling_notes.md",
        "docs/master_specification/YWE_MASTER_SPECIFICATION.md",
        "docs/project/repository_map.md",
    ]

    errors = []
    for entry in required_entries:
        if entry not in content:
            errors.append(
                f"Source inventory missing canonical entry: {entry}"
            )

    tracked_placeholders = [
        name for name in get_manifest_placeholder_names(root)
        if is_placeholder_backed(root, name)
    ]
    for placeholder_name in tracked_placeholders:
        if placeholder_name not in content:
            errors.append(
                f"Source inventory missing tracked placeholder entry: {placeholder_name}"
            )

    return errors


def check_authored_override_notes(root):
    """Verify canonical authored override and tooling control notes exist and contain guardrail sections."""
    notes_path = os.path.join(
        root, "docs", "architecture", "authored_override_and_tooling_notes.md"
    )
    if not os.path.isfile(notes_path):
        return ["Authored override and tooling notes not found"]

    content = read_text_file(notes_path)

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

    # Check canonical module capability manifest schema
    capability_manifest_errors = check_module_capability_manifest_schema(root)
    if capability_manifest_errors:
        print("  FAIL: Module Capability Manifest Schema")
        for e in capability_manifest_errors:
            print(f"    - {e}")
        errors.extend(capability_manifest_errors)
    else:
        print("  PASS: Module Capability Manifest Schema")

    applied_capability_manifest_errors = check_applied_module_capability_manifests(root)
    if applied_capability_manifest_errors:
        print("  FAIL: Applied Module Capability Manifests")
        for e in applied_capability_manifest_errors:
            print(f"    - {e}")
        errors.extend(applied_capability_manifest_errors)
    else:
        print("  PASS: Applied Module Capability Manifests")

    first_darkness_errors = check_first_darkness_and_divine_core(root)
    if first_darkness_errors:
        print("  FAIL: First Darkness and Divine Core Lore")
        for e in first_darkness_errors:
            print(f"    - {e}")
        errors.extend(first_darkness_errors)
    else:
        print("  PASS: First Darkness and Divine Core Lore")

    wolf_balance_errors = check_two_wolves_and_balance(root)
    if wolf_balance_errors:
        print("  FAIL: Two Wolves and Balance Lore")
        for e in wolf_balance_errors:
            print(f"    - {e}")
        errors.extend(wolf_balance_errors)
    else:
        print("  PASS: Two Wolves and Balance Lore")

    trial_of_return_errors = check_trial_of_return_michael_lucifer_odin(root)
    if trial_of_return_errors:
        print("  FAIL: Trial of Return Lore")
        for e in trial_of_return_errors:
            print(f"    - {e}")
        errors.extend(trial_of_return_errors)
    else:
        print("  PASS: Trial of Return Lore")

    master_spec_lore_errors = check_master_spec_lore_alignment(root)
    if master_spec_lore_errors:
        print("  FAIL: Master Spec Lore Alignment")
        for e in master_spec_lore_errors:
            print(f"    - {e}")
        errors.extend(master_spec_lore_errors)
    else:
        print("  PASS: Master Spec Lore Alignment")

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
