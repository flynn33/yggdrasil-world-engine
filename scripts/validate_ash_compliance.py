#!/usr/bin/env python3
"""Validate ASH cosmological compliance for the Yggdrasil World Engine."""

import json
import os
import sys


def check_realm_count(root):
    """Verify exactly nine canonical realms exist."""
    realms_path = os.path.join(root, "data", "realm_registry", "realms.json")
    if not os.path.isfile(realms_path):
        return ["Realm registry not found"]

    with open(realms_path) as f:
        data = json.load(f)

    realms = data.get("realms", [])
    if len(realms) != 9:
        return [f"ASH violation: expected 9 realms, found {len(realms)}"]
    return []


def check_cosmology_schema(root):
    """Verify cosmology schema contains required elements."""
    schema_path = os.path.join(
        root, "core", "cosmology_engine", "cosmology_schema.json"
    )
    if not os.path.isfile(schema_path):
        return ["Cosmology schema not found"]

    with open(schema_path) as f:
        data = json.load(f)

    errors = []

    primordial = data.get("primordial_state", {})
    if primordial.get("darkness") is not True:
        errors.append("ASH violation: primordial darkness must remain true")
    if primordial.get("consciousness_gathering") is not True:
        errors.append(
            "ASH violation: cosmology schema must record consciousness gathering in primordial darkness"
        )

    first_singularity = primordial.get("first_singularity", {})
    if first_singularity.get("name") != "dark_star":
        errors.append("ASH violation: first singularity must remain the Dark Star")

    creation_event = data.get("creation_event", {})
    if creation_event.get("trigger") != "dark_star_collapse":
        errors.append(
            "ASH violation: creation event trigger must remain dark_star_collapse"
        )

    required_sequence = [
        "gravity_emerges",
        "time_emerges",
        "void_forms_as_containment",
        "dark_star_collapses_into_divine_core",
        "nine_realms_stabilize",
        "architects_emerge_from_contained_consciousness",
        "first_wolves_emerge_from_light_dark_consciousness_matter_energy",
    ]
    sequence = creation_event.get("sequence", [])
    for step in required_sequence:
        if step not in sequence:
            errors.append(
                f"ASH violation: cosmology creation sequence missing {step}"
            )

    # Check realm count in cosmology
    if data.get("realm_count") != 9:
        errors.append("ASH violation: cosmology realm_count must be 9")

    realm_terms = data.get("realm_term_equivalence", {})
    if realm_terms.get("plane_equals_realm") is not True:
        errors.append("ASH violation: planes and realms must remain equivalent")

    ash_model = data.get("ash_model_foundation", {})
    if ash_model.get("model_name") != "ASH Model of the Universe":
        errors.append("ASH Model violation: cosmology schema must name ASH Model of the Universe as foundation")
    if ash_model.get("role") != "mathematical_and_ontological_foundation":
        errors.append("ASH Model violation: cosmology schema must record mathematical and ontological foundation role")
    if ash_model.get("engine_framework_foundation") is not True:
        errors.append("ASH Model violation: cosmology schema must mark the ASH Model as engine framework foundation")
    required_layers = {"archetype", "symbolic", "harmonic"}
    layers = ash_model.get("layers", [])
    if not isinstance(layers, list) or not all(isinstance(layer, str) for layer in layers):
        errors.append("ASH Model violation: cosmology schema layers must be a list of strings")
    elif set(layers) != required_layers:
        errors.append("ASH Model violation: cosmology schema must preserve archetype, symbolic, and harmonic layers")

    framework = data.get("engine_cosmology_framework", {})
    if framework.get("fixed_setting_bible") is not False:
        errors.append("YWE cosmology violation: engine cosmology must not be a fixed setting bible")
    if framework.get("designer_lore_extensible") is not True:
        errors.append("YWE cosmology violation: designer lore extensibility must remain true")
    if framework.get("realm_layers_are_structural_simulation_constants") is not True:
        errors.append("YWE cosmology violation: realm layers must remain structural simulation constants")

    wolf_canon = data.get("wolf_canon", {})
    if (
        wolf_canon.get("relationship")
        != "paired_symbiotic_companions_of_consciousness"
    ):
        errors.append(
            "ASH violation: wolves must remain paired symbiotic companions of consciousness"
        )
    if wolf_canon.get("all_consciousness_carries_both") is not True:
        errors.append(
            "ASH violation: cosmology schema must preserve that all consciousness carries both wolves"
        )
    if wolf_canon.get("ideal_state") != "balance":
        errors.append("ASH violation: wolf ideal state must remain balance")
    if wolf_canon.get("permanent_death") is not False:
        errors.append("ASH violation: wolves must remain permanently indestructible")
    if wolf_canon.get("opposition_type") != "complementary_non_moral_opposites":
        errors.append("ASH violation: wolves must remain complementary non-moral opposites")
    if wolf_canon.get("morality_system") is not False:
        errors.append("ASH violation: wolves must not become a morality system")
    if wolf_canon.get("physical_companion_presence") is not True:
        errors.append("ASH violation: wolves must physically accompany the player")
    if wolf_canon.get("quest_assistance") is not True:
        errors.append("ASH violation: wolves must preserve quest assistance")
    if wolf_canon.get("combat_assistance") is not True:
        errors.append("ASH violation: wolves must preserve combat assistance")
    if wolf_canon.get("temporary_loss_state") != "decoherence":
        errors.append(
            "ASH violation: wolves must use decoherence as their temporary loss state"
        )
    if wolf_canon.get("return_after_decoherence") is not True:
        errors.append("ASH violation: wolves must return after decoherence")
    if wolf_canon.get("each_has_what_the_other_needs") is not True:
        errors.append("ASH violation: wolf canon must preserve mutual need")

    return errors


def check_pattern_engine_invariants(root):
    """Verify the ASH Pattern Engine enforces no-independent-random rule."""
    interface_path = os.path.join(
        root, "core", "ash_pattern_engine", "engine_interface.json"
    )
    if not os.path.isfile(interface_path):
        return ["ASH Pattern Engine interface not found"]

    with open(interface_path) as f:
        data = json.load(f)

    errors = []
    invariants = data.get("invariants", [])
    has_no_random_rule = any(
        "independent" in inv.lower() and "random" in inv.lower()
        for inv in invariants
    )
    if not has_no_random_rule:
        errors.append(
            "ASH violation: Pattern Engine must declare no-independent-random invariant"
        )

    return errors


def check_divine_core_endgame(root):
    """Verify Divine Core is marked as endgame in realm definitions."""
    defs_path = os.path.join(
        root, "data", "realm_registry", "realm_definitions.json"
    )
    if not os.path.isfile(defs_path):
        return []  # Optional file, not an error if missing

    with open(defs_path) as f:
        data = json.load(f)

    errors = []
    realms = data.get("realms", [])
    divine_core = next(
        (r for r in realms if r.get("realm_id") == "divine_core"), None
    )
    if divine_core and not divine_core.get("is_endgame"):
        errors.append("ASH violation: Divine Core must be marked as endgame")

    physical = next(
        (r for r in realms if r.get("realm_id") == "physical"), None
    )
    if physical and not physical.get("is_starting_realm"):
        errors.append("ASH violation: Physical realm must be the starting realm")

    return errors


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    print(f"Validating ASH compliance at: {root}")

    all_errors = []
    checks = [
        ("Realm Count", check_realm_count),
        ("Cosmology Schema", check_cosmology_schema),
        ("Pattern Engine Invariants", check_pattern_engine_invariants),
        ("Divine Core Endgame", check_divine_core_endgame),
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
        print(f"\n{len(all_errors)} ASH compliance error(s) found.")
        sys.exit(1)
    else:
        print("\nASH compliance validation passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
