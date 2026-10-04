#!/usr/bin/env python3
"""Execute M2 validation recovery, replay and protected-schema migration cases.

These operations exercise validation tooling. They do not certify runtime state
restoration, event-log folding, persistence, or idempotent consequence application.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

import check_fixture_catalog as fixtures
import check_m0_truthful_baseline as baseline
import check_rejection_scenarios as rejection

CASE_SCHEMA = "data/schemas/m2_validation_operation_case_schema.json"
CASE_SCHEMA_ID = "https://ywe.local/schemas/m2_validation_operation_case_schema.json"
BUNDLE = "examples/contract_foundation/m2_validation_operation_cases.example.json"
EXPECTATIONS = "data/validation/m2_validation_operation_expectations.json"
CATEGORIES = ("recovery", "replay", "migration")
BINDING_FIELDS = ("path", "instance_pointer", "schema_id", "category", "expected_result", "expected_errors")


def value_hash(value) -> str:
    return baseline.m2_contract_value_sha256(value)


def stage(name: str, witnessed: set[str]) -> dict:
    return {"stage": name, "result": "reject" if witnessed else "accept",
            "errors": [json.loads(item) for item in sorted(witnessed)]}


def select_fixture(root: Path, catalog: dict, case: dict) -> tuple[dict, object]:
    matches = [item for item in catalog["fixtures"] if item["fixture_id"] == case["fixture_id"]]
    if len(matches) != 1:
        raise ValueError("Operation must select exactly one registered fixture ID")
    binding = matches[0]
    actual = {field: binding[field] for field in BINDING_FIELDS}
    if not rejection.json_equal(actual, case["fixture_binding"]):
        raise ValueError("Selected fixture differs from its explicit catalog binding")
    subject = fixtures.json_pointer(
        fixtures.load_instance(fixtures.repository_path(root, binding["path"])), binding["instance_pointer"]
    )
    if value_hash(subject) != case["instance_sha256"]:
        raise ValueError("Selected fixture differs from its recorded JSON value hash")
    return binding, subject


def recorded_witnesses(binding: dict) -> set[str]:
    return {fixtures.signature_key(item) for item in binding["expected_errors"]}


def execute_recovery(root: Path, registry, catalog: dict, case: dict, locations: dict) -> list[dict]:
    binding, original = select_fixture(root, catalog, case)
    if binding["expected_result"] != "accept" or recorded_witnesses(binding):
        raise ValueError("Recovery requires a registered accepted positive control")
    initial = rejection.schema_witnesses(registry, binding["schema_id"], original)
    if initial:
        raise ValueError("Recovery positive control was rejected")
    replacement = case["replacement"]
    previous = fixtures.json_pointer(original, replacement["pointer"])
    if not rejection.json_equal(previous, replacement["restored_value"]):
        raise ValueError("Recovery must restore the exact original JSON value")
    if rejection.json_equal(previous, replacement["invalid_value"]):
        raise ValueError("Recovery proposal must differ from the original value")
    invalid = rejection.apply_operations(original, [{
        "op": "replace", "path": replacement["pointer"], "value": replacement["invalid_value"],
    }])
    executed = rejection.schema_errors(registry, binding["schema_id"], invalid)
    witnessed = {fixtures.signature_key(fixtures.error_signature(item)) for item in executed}
    expected = {fixtures.signature_key(item) for item in case["expected_errors"]}
    if not witnessed or witnessed != expected:
        raise ValueError("Recovery proposal did not produce its exact complete rejection witnesses")
    for owner in case["owner_bindings"]:
        source = fixtures.load_instance(fixtures.repository_path(root, owner["path"]))
        if not rejection.json_equal(fixtures.json_pointer(source, owner["pointer"]), owner["value"]):
            raise ValueError("Recovery owning assertion differs from its exact binding")
    rejection.validate_schema_owners(root, registry, {
        "mode": "direct", "owner_bindings": case["owner_bindings"],
    }, executed, locations)
    recovered = rejection.apply_operations(invalid, [{
        "op": "replace", "path": replacement["pointer"], "value": replacement["restored_value"],
    }])
    if not rejection.json_equal(recovered, original) or value_hash(original) != case["instance_sha256"]:
        raise ValueError("Recovery altered the original input or did not restore it exactly")
    final = rejection.schema_witnesses(registry, binding["schema_id"], recovered)
    if final:
        raise ValueError("Recovered validation input was rejected")
    return [stage("positive_control", initial), stage("invalid_proposal", witnessed), stage("restored_input", final)]


def execute_replay(root: Path, registry, catalog: dict, case: dict) -> list[dict]:
    stages = []
    initial = None
    for name in ("first_validation", "replayed_validation"):
        # Load the repository subject separately for each validation; a copied
        # result or reused mutated object cannot establish validation replay.
        binding, subject = select_fixture(root, catalog, case)
        if initial is not None and not rejection.json_equal(subject, initial):
            raise ValueError("Replay loaded a different validation input")
        initial = copy.deepcopy(subject)
        witnessed = fixtures.instance_witnesses(root, registry, binding["schema_id"], subject)
        if witnessed != recorded_witnesses(binding):
            raise ValueError("Replay differs from the selected fixture's complete recorded witnesses")
        observed = "reject" if witnessed else "accept"
        if observed != binding["expected_result"] or value_hash(subject) != case["instance_sha256"]:
            raise ValueError("Replay result differs or validation altered its input")
        stages.append(stage(name, witnessed))
    if stages[0]["result"] != stages[1]["result"] or stages[0]["errors"] != stages[1]["errors"]:
        raise ValueError("Repeated validation produced different results")
    return stages


def execute_migration(root: Path, case: dict) -> list[dict]:
    if case["manifest_path"] != baseline.M2_SCHEMA_MIGRATION_PATH:
        raise ValueError("Migration cases must select the protected migration manifest")
    if (case["source_revision"] != baseline.M2_ORIGINAL_SOURCE_REVISION
            or case["migration_revision"] != baseline.M2_ORIGINAL_MIGRATION_REVISION):
        raise ValueError("Migration case differs from immutable original provenance")
    manifest = fixtures.load_json(fixtures.repository_path(root, case["manifest_path"]))
    record = fixtures.json_pointer(manifest, case["record_pointer"])
    group = fixtures.json_pointer(manifest, case["assertion_revision_pointer"])
    if record.get("path") != case["migration_path"] or group.get("path") != case["migration_path"]:
        raise ValueError("Migration record and assertion stages must select the same protected target")
    if value_hash(record) != case["record_sha256"] or value_hash(group) != case["assertion_revision_sha256"]:
        raise ValueError("Migration record or assertion history differs from its exact binding")
    current = fixtures.load_json(fixtures.repository_path(root, case["migration_path"]))
    if value_hash(current) != case["current_stage_sha256"]:
        raise ValueError("Migration target differs from the explicitly selected current stage")
    if not group.get("transitions") or group["transitions"][-1]["revised_value_sha256"] != case["current_stage_sha256"]:
        raise ValueError("Migration case does not select the final declared assertion stage")
    errors = []
    baseline.validate_m2_migration_proofs(root, errors)
    if errors:
        raise ValueError("Protected migration proof reconstruction failed: " + "; ".join(errors))
    return [stage("protected_proof_reconstruction", set())]


def evaluate_cases(root: Path, schema: dict, bundle: dict, expectations: dict,
                   registry, catalog: dict) -> tuple[list[str], list[dict]]:
    errors, results = [], []
    if not rejection.json_equal(registry[CASE_SCHEMA_ID].contents, schema):
        return ["Operation schema differs from the resolved registry resource"], []
    for value, definition in ((bundle, "Bundle"), (expectations, "Expectations")):
        validator = Draft202012Validator({"$ref": f"{CASE_SCHEMA_ID}#/$defs/{definition}"}, registry=registry)
        errors.extend(f"Operation {definition}: {error.message}" for error in validator.iter_errors(value))
    if errors:
        return errors, []
    expected = {}
    for item in expectations["cases"]:
        pointer = item["instance_pointer"]
        if pointer in expected:
            errors.append(f"Duplicate operation expectation pointer: {pointer}")
        expected[pointer] = item
    cases = {
        fixtures.pointer_from_parts((category, name)): case
        for category in CATEGORIES for name, case in bundle[category].items()
    }
    if set(expected) != set(cases):
        errors.append("Operation expectation pointers must cover every case exactly once")
    ids = [case["operation_id"] for case in cases.values()]
    if len(ids) != len(set(ids)):
        errors.append("Operation IDs must be unique")
    if errors:
        return errors, []
    resources = fixtures.load_json(root / fixtures.CONTRACT_CATALOG)["schemas"]
    touched = {fixtures.CONTRACT_CATALOG, fixtures.FIXTURE_CATALOG, baseline.M2_SCHEMA_MIGRATION_PATH,
               BUNDLE, EXPECTATIONS}
    touched.update(item["path"] for item in resources)
    touched.update(case["fixture_binding"]["path"] for case in cases.values() if "fixture_binding" in case)
    touched.update(item["path"] for item in fixtures.load_json(root / baseline.M2_SCHEMA_MIGRATION_PATH)["migrations"])
    before = {path: fixtures.repository_path(root, path).read_bytes() for path in touched}
    for resource in resources:
        if not rejection.json_equal(fixtures.load_json(root / resource["path"]), registry[resource["schema_id"]].contents):
            return ["A resolved operation schema differs from its current source resource"], []
    locations = rejection.schema_constraint_locations(root, registry)
    for pointer, case in cases.items():
        try:
            expectation = expected[pointer]
            category = pointer.split("/")[1]
            if (expectation["operation_id"] != case["operation_id"]
                    or expectation["category"] != category or case["category"] != category):
                raise ValueError("Operation identity or category differs from its exact case pointer")
            if category == "recovery":
                stages = execute_recovery(root, registry, catalog, case, locations)
            elif category == "replay":
                stages = execute_replay(root, registry, catalog, case)
            else:
                stages = execute_migration(root, case)
            if not rejection.json_equal(stages, expectation["expected_stages"]):
                raise ValueError("Operation stages differ from their complete recorded results")
            results.append({"operation_id": case["operation_id"], "path": BUNDLE,
                            "instance_pointer": pointer, "category": category,
                            "validation_scope": "schema_validation_operation", "result": "pass", "stages": stages})
        except Exception as exc:
            errors.append(f"Operation {case['operation_id']}: {exc}")
    if any(not fixtures.repository_path(root, path).is_file()
           or fixtures.repository_path(root, path).read_bytes() != content for path, content in before.items()):
        errors.append("Validation operations changed a source input, schema or protected history")
        return errors, []
    return errors, results


def validation_errors(root: Path) -> tuple[list[str], list[dict]]:
    root = root.resolve()
    try:
        registry, errors = fixtures.load_registry(root)
        if errors:
            return errors, []
        schema = fixtures.load_json(fixtures.repository_path(root, CASE_SCHEMA))
        Draft202012Validator.check_schema(schema)
        if schema.get("$id") != CASE_SCHEMA_ID:
            return ["Validation operation schema identity differs from its registered identifier"], []
        return evaluate_cases(root, schema, fixtures.load_instance(fixtures.repository_path(root, BUNDLE)),
                              fixtures.load_json(fixtures.repository_path(root, EXPECTATIONS)), registry,
                              fixtures.load_json(fixtures.repository_path(root, fixtures.FIXTURE_CATALOG)))
    except Exception as exc:
        return [f"Unable to load validation operation cases: {exc}"], []


def category_coverage(catalog: dict, fixture_results: list[dict], operation_results: list[dict]) -> tuple[list[str], dict]:
    """Count a lifecycle category only at an accepted, executed exact operation case."""
    successful = {(item["fixture_id"], item["path"]) for item in fixture_results if item["result"] == "accept"}
    executed, errors = {category: [] for category in CATEGORIES}, []
    seen = set()
    for operation in operation_results:
        key = (operation["path"], operation["instance_pointer"])
        if key in seen:
            errors.append(f"Duplicate executed operation case: {key}")
            continue
        seen.add(key)
        category = operation["category"]
        if (category not in CATEGORIES or operation["path"] != BUNDLE
                or operation["result"] != "pass" or operation["validation_scope"] != "schema_validation_operation"
                or not operation["instance_pointer"].startswith(f"/{category}/")):
            errors.append(f"Invalid executed lifecycle operation result: {key}")
            continue
        bindings = [item for item in catalog["fixtures"]
                    if (item["path"], item["instance_pointer"]) == key
                    and item["schema_id"] == CASE_SCHEMA_ID and item["category"] == category
                    and item["expected_result"] == "accept" and not item["expected_errors"]
                    and (item["fixture_id"], item["path"]) in successful]
        if len(bindings) != 1:
            errors.append(f"Executed operation lacks one successful exact lifecycle catalog binding: {key}")
            continue
        executed[category].append(operation["operation_id"])
    errors.extend(f"No bound successful {category} validation operation exists" for category in CATEGORIES if not executed[category])
    return errors, {"validation_scope": "schema_validation_operation", "executed_operations_by_category": executed}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    errors, results = validation_errors(root)
    if errors:
        print("M2 validation operations failed:")
        for error in errors:
            print("  - " + error)
        return 1
    print(f"M2 validation operations passed ({len(results)} cases; schema validation scope).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
