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

    # Check primordial entities
    primordial = data.get("primordial_state", {})
    entities = primordial.get("entities", [])
    entity_names = [e.get("name") for e in entities]
    if "white_wolf" not in entity_names:
        errors.append("ASH violation: White Wolf missing from primordial state")
    if "dark_wolf" not in entity_names:
        errors.append("ASH violation: Dark Wolf missing from primordial state")

    # Check wolves are indestructible
    for entity in entities:
        if entity.get("name") in ("white_wolf", "dark_wolf"):
            if entity.get("destructible") is not False:
                errors.append(
                    f"ASH violation: {entity['name']} must be indestructible"
                )

    # Check realm count in cosmology
    if data.get("realm_count") != 9:
        errors.append("ASH violation: cosmology realm_count must be 9")

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
