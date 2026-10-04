#!/usr/bin/env python3
"""Validate the new descriptor format grammars and their declared meta references."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

import check_fixture_catalog as fixtures

GRAMMARS = {
    "pattern": {
        "schema": "data/schemas/pattern_registry_descriptor_schema.json",
        "schema_id": "https://ywe.local/schemas/pattern_registry_descriptor_schema.json",
        "source": "data/pattern_archetypes/ash_pattern_registry_schema.yaml",
    },
    "module": {
        "schema": "data/schemas/module_capability_descriptor_schema.json",
        "schema_id": "https://ywe.local/schemas/module_capability_descriptor_schema.json",
        "source": "data/module_capability/module_capability_manifest_schema.yaml",
    },
}
SCHEMA_PATHS = (
    "data/schemas/pattern_registry_descriptor_schema.json",
    "data/schemas/module_capability_descriptor_schema.json",
    "data/schemas/pattern_archetype_registry_schema.json",
    "data/schemas/module_capability_manifest_schema.json",
    "data/schemas/yaml_descriptor_case_expectations_schema.json",
)
BUNDLE_PATH = "examples/contract_foundation/yaml_descriptor_cases.example.yaml"
CASE_EXPECTATIONS_PATH = "examples/contract_foundation/yaml_descriptor_expectations.example.json"
MODULE_ENUM_BINDINGS = (
    (("module_classification",), "module_classification"),
    (("authority_class",), "authority_class"),
    (("activation_state",), "activation_state"),
    (("requires_capabilities", 0, "dependency_strength"), "dependency_strength"),
    (("delegable_compatible_responsibilities", 0, "delegation_rule"), "delegation_rule"),
    (("suppression_conditions", 0, "reason"), "suppression_reason"),
    (("compatible_external_capabilities", 0, "capability_class"), "external_capability_class"),
)


def grammar_spec(grammar: str) -> dict:
    if not isinstance(grammar, str) or grammar not in GRAMMARS:
        raise ValueError(f"Unsupported descriptor grammar: {grammar!r}")
    return GRAMMARS[grammar]


def descriptor_validator(grammar: str, root: Path) -> Draft202012Validator:
    spec = grammar_spec(grammar)
    root = Path(root)
    resources = []
    for relative in SCHEMA_PATHS:
        schema = fixtures.load_json(root / relative)
        Draft202012Validator.check_schema(schema)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    registry = Registry(retrieve=fixtures.deny_retrieval).with_resources(resources).crawl()
    return Draft202012Validator({"$ref": spec["schema_id"]}, registry=registry)


def _witness(error_id: str, parts: tuple, rule: str) -> dict:
    return {
        "error_id": "YAML_DESCRIPTOR_" + error_id,
        "instance_pointer": fixtures.pointer_from_parts(parts),
        "schema_pointer": "/x-ywe-semantic-rules/" + rule,
    }


def _pattern_semantics(instance: dict) -> list[dict]:
    errors = []
    enums = instance["enums"]
    records = instance["schema"]

    def visit_field(field: dict, parts: tuple) -> None:
        kind = field["type"]
        if kind == "enum" and field["values_ref"] not in enums:
            errors.append(_witness("ENUM_REFERENCE", parts + ("values_ref",), "enum_reference"))
        if kind == "list" and "items_ref" in field and field["items_ref"] not in enums:
            errors.append(_witness("ENUM_REFERENCE", parts + ("items_ref",), "enum_reference"))
        if kind == "map":
            check_required(field.get("required", []), set(field["properties"]), parts + ("required",))
            for name, child in field["properties"].items():
                visit_field(child, parts + ("properties", name))

    def check_required(required: list[str], available: set[str], parts: tuple) -> None:
        for index, name in enumerate(required):
            if name not in available:
                errors.append(_witness("REQUIRED_MEMBER", parts + (index,), "required_name_membership"))

    cycles = set()
    for origin in sorted(records):
        chain = []
        positions = {}
        current = origin
        while current in records and current not in positions:
            positions[current] = len(chain)
            chain.append(current)
            parent = records[current].get("extends")
            if parent is None:
                break
            current = parent
        else:
            if current in positions:
                cycles.update(chain[positions[current]:])
    for name in sorted(cycles):
        errors.append(_witness("INHERITANCE_CYCLE", ("schema", name, "extends"), "inheritance_cycle"))

    def effective_properties(name: str) -> set[str] | None:
        available = set()
        visited = set()
        current = name
        while current in records and current not in visited:
            visited.add(current)
            record = records[current]
            available.update(record["properties"])
            parent = record.get("extends")
            if parent is None:
                return available
            current = parent
        # A missing or cyclic parent prevents a reliable inherited field surface.
        return None

    for name, record in records.items():
        parts = ("schema", name)
        if "extends" in record and record["extends"] not in records:
            errors.append(_witness("RECORD_REFERENCE", parts + ("extends",), "record_reference"))
        available = effective_properties(name) if "extends" in record else set(record["properties"])
        if available is not None:
            for required_key in ("required", "additional_required"):
                check_required(record.get(required_key, []), available, parts + (required_key,))
        for field_name, field in record["properties"].items():
            visit_field(field, parts + ("properties", field_name))
    for family, declaration in instance["registry_shape"]["families"].items():
        if declaration["items_ref"] not in records:
            errors.append(_witness(
                "RECORD_REFERENCE", ("registry_shape", "families", family, "items_ref"), "record_reference"
            ))
    return errors


def _module_semantics(instance: dict) -> list[dict]:
    errors = []
    manifest = instance["core_schema"]["ModuleCapabilityManifest"]
    for index, name in enumerate(instance["canonical_validation_rules"]["required_fields"]):
        if name not in manifest:
            errors.append(_witness(
                "REQUIRED_MEMBER", ("canonical_validation_rules", "required_fields", index),
                "required_name_membership",
            ))
    for field_parts, enum_name in MODULE_ENUM_BINDINGS:
        current = manifest
        for part in field_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            elif isinstance(current, list) and isinstance(part, int) and part < len(current):
                current = current[part]
            else:
                break
        else:
            parts = ("core_schema", "ModuleCapabilityManifest") + field_parts
            if enum_name not in instance["classification_enums"]:
                errors.append(_witness("ENUM_REFERENCE", parts, "enum_reference"))
            elif not isinstance(current, str):
                errors.append(_witness("INLINE_ENUM", parts, "inline_enum_consistency"))
            else:
                alternatives = [alternative.strip() for alternative in current.split("|")]
                if (
                    set(alternatives) != set(instance["classification_enums"][enum_name])
                    or len(alternatives) != len(set(alternatives))
                ):
                    errors.append(_witness("INLINE_ENUM", parts, "inline_enum_consistency"))
    return errors


def descriptor_semantic_errors(instance, grammar: str, root: Path) -> list[dict]:
    """Return semantic-only witnesses after the caller has passed the grammar stage."""
    spec = grammar_spec(grammar)
    schema = fixtures.load_json(Path(root) / spec["schema"])
    errors = _pattern_semantics(instance) if grammar == "pattern" else _module_semantics(instance)
    for error in errors:
        # Each witness names an owned, declared semantic rule rather than a fake schema keyword.
        fixtures.json_pointer(schema, error["schema_pointer"])
    return sorted(
        {fixtures.signature_key(error): error for error in errors}.values(),
        key=fixtures.signature_key,
    )


def descriptor_errors(instance, grammar: str, root: Path) -> list[dict]:
    """Return grammar witnesses, or semantic witnesses when the grammar stage passes."""
    validator = descriptor_validator(grammar, root)
    errors = [
        fixtures.error_signature(leaf)
        for error in validator.iter_errors(instance)
        for leaf in fixtures.leaf_errors(error)
    ]
    if errors:
        return sorted(
            {fixtures.signature_key(error): error for error in errors}.values(),
            key=fixtures.signature_key,
        )
    return descriptor_semantic_errors(instance, grammar, root)


def validation_errors(root: Path) -> tuple[list[str], list[dict]]:
    """Execute both source roots and every explicitly recorded descriptor case."""
    root = Path(root)
    errors = []
    results = []
    for grammar, spec in GRAMMARS.items():
        try:
            witnessed = descriptor_errors(fixtures.load_instance(root / spec["source"]), grammar, root)
            if witnessed:
                errors.append(f"{spec['source']}: {json.dumps(witnessed, sort_keys=True)}")
            else:
                results.append({"path": spec["source"], "instance_pointer": "", "grammar": grammar, "result": "accept"})
        except Exception as exc:
            errors.append(f"{spec['source']}: unable to validate descriptor: {exc}")
    try:
        bundle = fixtures.load_instance(root / BUNDLE_PATH)
        expectations = fixtures.load_json(root / CASE_EXPECTATIONS_PATH)
        expectation_schema = fixtures.load_json(
            root / "data/schemas/yaml_descriptor_case_expectations_schema.json"
        )
        malformed = list(Draft202012Validator(expectation_schema).iter_errors(expectations))
        if malformed:
            return errors + [f"Descriptor case expectations: {error.message}" for error in malformed], results
        observed_pointers = {
            fixtures.pointer_from_parts((group, name))
            for group in ("positive", "boundary", "reject")
            for name in bundle[group]
        }
        expected_pointers = {case["instance_pointer"] for case in expectations["cases"]}
        if observed_pointers != expected_pointers or len(expected_pointers) != len(expectations["cases"]):
            errors.append("Descriptor case expectations must cover each declared case exactly once")
        for case in expectations["cases"]:
            instance = fixtures.json_pointer(bundle, case["instance_pointer"])
            witnessed = descriptor_errors(instance, case["grammar"], root)
            result = "reject" if witnessed else "accept"
            group = case["instance_pointer"].split("/")[1]
            if group not in {"positive", "boundary", "reject"} or (
                case["expected_result"] != ("reject" if group == "reject" else "accept")
            ):
                errors.append(f"Descriptor case role differs from its expectation: {case['instance_pointer']}")
            if result != case["expected_result"] or (
                {fixtures.signature_key(error) for error in witnessed}
                != {fixtures.signature_key(error) for error in case["expected_errors"]}
            ):
                errors.append(f"{case['instance_pointer']}: descriptor result or exact witnesses differ")
            else:
                results.append({
                    "path": BUNDLE_PATH, "instance_pointer": case["instance_pointer"],
                    "grammar": case["grammar"], "result": result,
                })
    except Exception as exc:
        errors.append(f"Unable to execute descriptor cases: {exc}")
    return errors, results


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors, results = validation_errors(root)
    if errors:
        print("YAML descriptor contract check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    rejected = sum(result["result"] == "reject" for result in results)
    print(f"YAML descriptor contract check passed ({len(results)} roots/cases; {rejected} intended rejections).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
