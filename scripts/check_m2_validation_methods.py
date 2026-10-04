#!/usr/bin/env python3
"""Execute the eight M2 schema-validation methods with concrete case evidence.

This foundation checks specification artifacts, not engine runtime behavior.
Schema mutations use new in-memory registries and never write source inputs.
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

import check_fixture_catalog as fixtures
import check_m0_truthful_baseline as baseline
import check_rejection_scenarios as rejection
import check_yaml_descriptor_contracts as descriptors

METHODS = ("meta_schema", "instance", "reference", "identifier", "dependency", "negative", "property", "mutation")
SCHEMA = "data/schemas/m2_validation_method_expectations_schema.json"
SCHEMA_ID = "https://ywe.local/schemas/m2_validation_method_expectations_schema.json"
EXPECTATIONS = "data/validation/m2_validation_method_expectations.json"
SCOPE = "schema_validation_foundation"
MUTANTS = ("ability_wolf_const", "identifier_max_length", "reference_required_kind")


def hashes(root: Path, paths) -> dict:
    return {path: baseline.normalized_text_sha256(fixtures.repository_path(root, path)) for path in sorted(set(paths))}


def witnesses(root: Path, registry, identifier, instance) -> list[dict]:
    return [json.loads(signature) for signature in sorted(fixtures.instance_witnesses(root, registry, identifier, instance))]


def matched(actual, expected) -> bool:
    return rejection.json_equal(sorted(actual, key=fixtures.signature_key), sorted(expected, key=fixtures.signature_key))


def load_context(root: Path) -> dict:
    contract_catalog = fixtures.load_json(root / fixtures.CONTRACT_CATALOG)
    catalog = fixtures.load_json(root / fixtures.FIXTURE_CATALOG)
    resources = [(entry, fixtures.load_json(fixtures.repository_path(root, entry["path"])))
                 for entry in contract_catalog["schemas"]]
    registry, registry_errors = fixtures.load_registry(root)
    return {"resources": resources, "contract_catalog": contract_catalog, "catalog": catalog,
            "registry": registry, "registry_errors": registry_errors}


def meta_schema(root: Path, context: dict, expectations: dict):
    errors, cases = [], []
    paths = baseline.repository_candidate_paths(root, errors)
    classification = fixtures.load_json(root / "data/governance/artifact_classification_manifest.json")
    assignments = baseline.effective_assignments(paths, classification, "classification", errors, "D7 classification")
    for relative in paths:
        if Path(relative).suffix.lower() != ".json" or assignments.get(relative, {}).get("classification") != "normative":
            continue
        schema = fixtures.load_json(root / relative)
        if not isinstance(schema, dict) or "$schema" not in schema:
            continue
        case = {"path": relative, "schema_id": schema.get("$id"), "result": "pass",
                "schema_sha256": baseline.normalized_text_sha256(root / relative)}
        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            case["result"] = "fail"
            errors.append(f"Normative meta-schema {relative}: {exc}")
        cases.append(case)
    return errors, cases, {"classification_sha256": baseline.normalized_text_sha256(root / "data/governance/artifact_classification_manifest.json")}


def instance(root: Path, context: dict, expectations: dict):
    errors = list(context["registry_errors"])
    registry = context["registry"]
    for path, schema_id in ((fixtures.CONTRACT_CATALOG, "https://ywe.local/schemas/contract_catalog_schema.json"),
                            (fixtures.FIXTURE_CATALOG, "https://ywe.local/schemas/fixture_catalog_schema.json")):
        errors.extend(f"{path}: {error.message}" for error in Draft202012Validator(
            {"$ref": schema_id}, registry=registry).iter_errors(fixtures.load_json(root / path)))
    bindings = context["catalog"]["fixtures"]
    errors.extend(fixtures.fixture_requirement_errors(root, registry, bindings))
    execution_errors, results = fixtures.evaluate_fixtures(root, registry, bindings)
    errors.extend(execution_errors)
    success = {item["fixture_id"] for item in results}
    cases = [{"fixture_id": item["fixture_id"], "path": item["path"], "instance_pointer": item["instance_pointer"],
              "schema_id": item["schema_id"], "expected_result": item["expected_result"],
              "expected_errors": item["expected_errors"], "result": "pass" if item["fixture_id"] in success else "fail"}
             for item in bindings]
    return errors, cases, {"source_hashes": hashes(root, (fixtures.CONTRACT_CATALOG, fixtures.FIXTURE_CATALOG))}


def reference(root: Path, context: dict, expectations: dict):
    errors, cases = list(context["registry_errors"]), []
    for entry, schema in context["resources"]:
        resource = Resource.from_contents(schema)
        for base, ref in sorted(fixtures.schema_references(resource, "")):
            case = {"path": entry["path"], "base": base, "reference": ref, "result": "pass"}
            try:
                fixtures.resolve_schema_target(context["registry"], ref, base)
            except Exception as exc:
                case["result"] = "fail"
                errors.append(f"Offline schema reference {entry['path']} {ref!r}: {exc}")
            cases.append(case)
    return errors, cases, {"retrieval_policy": "deny_unknown_resources", "includes_unused_subschemas": True,
                          "source_hashes": hashes(root, (fixtures.CONTRACT_CATALOG,))}


def identifier(root: Path, context: dict, expectations: dict):
    errors, cases, seen_ids, seen_paths, seen_anchors = [], [], set(), set(), set()
    for entry, schema in context["resources"]:
        failed = entry["path"] in seen_paths or schema.get("$id") != entry["schema_id"]
        seen_paths.add(entry["path"])
        cases.append({"namespace": "catalog_schema_path", "value": entry["path"], "result": "fail" if failed else "pass"})
        if failed:
            errors.append(f"Duplicate schema path or mismatched catalog identifier: {entry['path']}")
        resource = Resource.from_contents(schema)
        for value in sorted(fixtures.resource_identities(resource, "")):
            failed = value in seen_ids
            seen_ids.add(value)
            cases.append({"namespace": "schema_resource_id", "value": value, "result": "fail" if failed else "pass"})
            if failed:
                errors.append(f"Duplicate effective schema resource identifier: {value}")
        for value in sorted(fixtures.resource_anchors(resource, "")):
            failed = value in seen_anchors
            seen_anchors.add(value)
            cases.append({"namespace": "schema_anchor", "value": list(value), "result": "fail" if failed else "pass"})
            if failed:
                errors.append(f"Duplicate effective schema anchor: {value}")
    fixture_ids, fixture_bindings = set(), set()
    for binding in context["catalog"]["fixtures"]:
        identity = (binding["path"], binding["instance_pointer"], binding["schema_id"])
        failed = binding["fixture_id"] in fixture_ids or identity in fixture_bindings
        fixture_ids.add(binding["fixture_id"])
        fixture_bindings.add(identity)
        cases.append({"namespace": "fixture_id_and_binding", "value": binding["fixture_id"], "binding": list(identity),
                      "result": "fail" if failed else "pass"})
        if failed:
            errors.append(f"Duplicate fixture identifier or binding: {binding['fixture_id']}")
    errors.extend(context["registry_errors"])
    return errors, cases, {"source_hashes": hashes(root, (fixtures.CONTRACT_CATALOG, fixtures.FIXTURE_CATALOG)),
                          "domain_reference_resolution_claimed": False}


def dependency(root: Path, context: dict, expectations: dict):
    errors, cases = [], []
    ledger = fixtures.load_json(root / descriptors.CASE_EXPECTATIONS_PATH)
    bundle = fixtures.load_instance(root / descriptors.BUNDLE_PATH)
    for grammar, spec in descriptors.GRAMMARS.items():
        actual = descriptors.descriptor_errors(fixtures.load_instance(root / spec["source"]), grammar, root)
        cases.append({"path": spec["source"], "instance_pointer": "", "grammar": grammar,
                      "witnesses": actual, "result": "fail" if actual else "pass"})
        if actual:
            errors.append(f"Invalid source descriptor dependency surface: {grammar}")
    for pointer in expectations["dependency_case_pointers"]:
        selected = [item for item in ledger["cases"] if item["instance_pointer"] == pointer]
        if len(selected) != 1:
            raise ValueError(f"Dependency control is not uniquely declared: {pointer}")
        selected = selected[0]
        actual = descriptors.descriptor_errors(fixtures.json_pointer(bundle, pointer), selected["grammar"], root)
        passed = matched(actual, selected["expected_errors"]) and bool(actual) and all(
            error["error_id"].startswith("YAML_DESCRIPTOR_") for error in actual)
        cases.append({"path": descriptors.BUNDLE_PATH, "instance_pointer": pointer, "grammar": selected["grammar"],
                      "witnesses": actual, "expected_errors": selected["expected_errors"], "result": "pass" if passed else "fail"})
        if not passed:
            errors.append(f"Descriptor dependency control differs: {pointer}")
    sources = [descriptors.BUNDLE_PATH, descriptors.CASE_EXPECTATIONS_PATH]
    sources.extend(item[key] for item in descriptors.GRAMMARS.values() for key in ("source", "schema"))
    return errors, cases, {"source_hashes": hashes(root, sources), "runtime_scheduling_claimed": False}


def negative(root: Path, context: dict, expectations: dict):
    bindings = [item for item in context["catalog"]["fixtures"] if item["expected_result"] == "reject"]
    errors, results = fixtures.evaluate_fixtures(root, context["registry"], bindings)
    successful = {item["fixture_id"] for item in results}
    cases = [{"fixture_id": item["fixture_id"], "path": item["path"], "instance_pointer": item["instance_pointer"],
              "expected_errors": item["expected_errors"], "result": "pass" if item["fixture_id"] in successful else "fail"}
             for item in bindings]
    catalog = fixtures.load_json(root / rejection.SCENARIO_CATALOG)
    errors.extend(f"Rejection scenario catalog: {error.message}" for error in Draft202012Validator(
        {"$ref": rejection.SCENARIO_SCHEMA_ID}, registry=context["registry"]).iter_errors(catalog))
    scenario_errors, scenario_results = rejection.evaluate_scenarios(root, context["registry"], catalog["scenarios"])
    errors.extend(scenario_errors)
    successful = {item["scenario_id"] for item in scenario_results}
    for scenario in catalog["scenarios"]:
        cases.append({"scenario_id": scenario["scenario_id"], "descriptor_path": scenario["descriptor_path"],
                      "validation_scope": scenario["validation_scope"],
                      "result": "pass" if scenario["scenario_id"] in successful else "fail",
                      "execution": next((item for item in scenario_results if item["scenario_id"] == scenario["scenario_id"]), None)})
    if not bindings or not catalog["scenarios"]:
        errors.append("Negative method requires both exact fixture rejections and source-bound scenarios")
    return errors, cases, {"source_hashes": hashes(root, (fixtures.FIXTURE_CATALOG, rejection.SCENARIO_CATALOG))}


def property_cases(root: Path, context: dict, expectations: dict):
    spec = expectations["module_properties"]
    source = fixtures.load_instance(fixtures.repository_path(root, spec["source_path"]))
    original = fixtures.load_instance(fixtures.repository_path(root, spec["positive_path"]))
    errors, cases = [], []

    def execute(case_id, instance, expected):
        actual = witnesses(root, context["registry"], spec["schema_id"], instance)
        passed = matched(actual, expected)
        cases.append({"case_id": case_id, "schema_id": spec["schema_id"], "witnesses": actual,
                      "expected_errors": expected, "result": "pass" if passed else "fail"})
        if not passed:
            errors.append(f"Source-driven property differs: {case_id}")

    execute("module_positive_control", original, [])
    for parts, family in descriptors.MODULE_ENUM_BINDINGS:
        values = source["classification_enums"][family]
        if not values:
            raise ValueError(f"Empty source enum family: {family}")
        for value in values:
            candidate = copy.deepcopy(original)
            member = candidate
            for part in parts[:-1]:
                member = member[part]
            member[parts[-1]] = value
            execute(f"enum:{family}:{value}", candidate, [])
    required = source["canonical_validation_rules"]["required_fields"]
    if not required or len(required) != len(set(required)):
        raise ValueError("Source required fields must be nonempty and unique")
    for name in required:
        candidate = copy.deepcopy(original)
        del candidate[name]
        execute(f"required:{name}", candidate, [{"error_id": "JSON_SCHEMA_REQUIRED", "instance_pointer": "",
                                                 "schema_pointer": "/required", "missing_properties": [name]}])
    return errors, cases, {"source_hashes": hashes(root, (spec["source_path"], spec["positive_path"])),
                          "enum_family_count": len(descriptors.MODULE_ENUM_BINDINGS), "required_field_count": len(required),
                          "generation": "all_source_enum_members_and_each_source_required_field_removal"}


def mutation(root: Path, context: dict, expectations: dict):
    errors, cases = [], []
    catalog = context["catalog"]["fixtures"]
    resources_before = baseline.m2_contract_value_sha256([schema for _, schema in context["resources"]])
    for mutant in expectations["mutations"]:
        controls = []
        for identifier in (mutant["positive_fixture_id"], mutant["reject_fixture_id"]):
            selected = [item for item in catalog if item["fixture_id"] == identifier]
            if len(selected) != 1:
                raise ValueError(f"Mutation fixture is not uniquely registered: {identifier}")
            controls.append(selected[0])
        if [item["expected_result"] for item in controls] != ["accept", "reject"] or not controls[1]["expected_errors"]:
            raise ValueError("Mutation requires a positive and an exact rejecting control")
        selected = [(entry, schema) for entry, schema in context["resources"] if entry["path"] == mutant["schema_path"]]
        if len(selected) != 1:
            raise ValueError(f"Mutation resource is not uniquely registered: {mutant['schema_path']}")
        entry, original = selected[0]
        if any(item["schema_id"] != entry["schema_id"] for item in controls):
            raise ValueError("Mutation controls do not select their declared owning schema")
        if not rejection.json_equal(fixtures.json_pointer(original, mutant["assertion_pointer"]), mutant["before"]):
            raise ValueError(f"Mutation owning assertion changed: {mutant['mutant_id']}")
        control_errors, control_results = fixtures.evaluate_fixtures(root, context["registry"], controls)
        changed = rejection.apply_operations(original, mutant["operations"])
        if rejection.json_equal(changed, original):
            raise ValueError("Mutation makes no assertion change")
        Draft202012Validator.check_schema(changed)
        mutant_resources = [(item["schema_id"], Resource.from_contents(copy.deepcopy(
            changed if item["path"] == mutant["schema_path"] else schema))) for item, schema in context["resources"]]
        mutant_registry = Registry(retrieve=fixtures.deny_retrieval).with_resources(mutant_resources).crawl()
        mutant_errors, mutant_results = fixtures.evaluate_fixtures(root, mutant_registry, controls)
        reject_binding = controls[1]
        subject = fixtures.json_pointer(fixtures.load_instance(root / reject_binding["path"]), reject_binding["instance_pointer"])
        actual = witnesses(root, mutant_registry, reject_binding["schema_id"], subject)
        killed = (not control_errors and len(control_results) == 2 and bool(mutant_errors)
                  and any(item["fixture_id"] == controls[0]["fixture_id"] for item in mutant_results)
                  and not any(item["fixture_id"] == controls[1]["fixture_id"] for item in mutant_results)
                  and not matched(actual, reject_binding["expected_errors"]))
        cases.append({"mutant_id": mutant["mutant_id"], "schema_path": mutant["schema_path"],
                      "schema_sha256": baseline.normalized_text_sha256(root / mutant["schema_path"]),
                      "assertion_pointer": mutant["assertion_pointer"], "before": mutant["before"], "operations": mutant["operations"],
                      "positive_fixture_id": controls[0]["fixture_id"], "reject_fixture_id": controls[1]["fixture_id"],
                      "original_expected_errors": reject_binding["expected_errors"], "control_errors": control_errors,
                      "mutant_errors": mutant_errors, "mutant_witnesses": actual, "killed": killed,
                      "result": "pass" if killed else "fail"})
        if not killed:
            errors.append(f"Assertion mutant survived or its original controls failed: {mutant['mutant_id']}")
    if resources_before != baseline.m2_contract_value_sha256([schema for _, schema in context["resources"]]):
        errors.append("Assertion mutation changed an original schema resource")
    return errors, cases, {"registry_isolation": "independent_deep_copied_resources", "source_writes": False}


EXECUTORS = {"meta_schema": meta_schema, "instance": instance, "reference": reference, "identifier": identifier,
             "dependency": dependency, "negative": negative, "property": property_cases, "mutation": mutation}


def method_coverage(results: list[dict]) -> tuple[list[str], dict]:
    errors = []
    if not isinstance(results, list) or any(not isinstance(item, dict) for item in results):
        return ["Executed validation method records must be a list of objects"], {"validation_scope": SCOPE, "methods": results}
    if [item.get("method") for item in results] != list(METHODS):
        errors.append("Executed validation methods must contain the exact ordered eight methods once")
    for item in results:
        fields = {"method", "status", "execution_complete", "executed_case_count", "successful_case_count", "errors", "evidence"}
        evidence = item.get("evidence")
        cases = evidence.get("cases") if isinstance(evidence, dict) else None
        if (set(item) != fields or not isinstance(item.get("errors"), list) or not isinstance(cases, list)
                or any(not isinstance(case, dict) for case in cases)):
            errors.append(f"Invalid or skipped validation method record: {item.get('method')}")
            continue
        executed = item.get("executed_case_count")
        successful = item.get("successful_case_count")
        if (item.get("status") != "pass" or item.get("execution_complete") is not True or item.get("errors")
                or type(executed) is not int or executed <= 0 or executed != len(cases)
                or type(successful) is not int or successful != executed
                or any(case.get("result") != "pass" for case in cases)):
            errors.append(f"Validation method failed, incomplete or unexecuted: {item.get('method')}")
        if item.get("method") == "mutation" and (
                [case.get("mutant_id") for case in cases] != list(MUTANTS) or any(case.get("killed") is not True for case in cases)):
            errors.append("Every declared assertion mutant must execute and be killed")
    return errors, {"validation_scope": SCOPE, "methods": results}


def validation_errors(root: Path) -> tuple[list[str], list[dict]]:
    root = root.resolve()
    setup_errors, context, expectations = [], None, None
    try:
        schema = fixtures.load_json(root / SCHEMA)
        Draft202012Validator.check_schema(schema)
        if schema.get("$id") != SCHEMA_ID or schema.get("x-ywe-requirement-id") != "YWE-REQ-0036":
            raise ValueError("Method expectation schema identity/requirement differs")
        expectations = fixtures.load_json(root / EXPECTATIONS)
        setup_errors.extend(f"Method expectations: {error.message}" for error in Draft202012Validator(schema).iter_errors(expectations))
        context = load_context(root)
    except Exception as exc:
        setup_errors.append(f"Unable to initialize validation methods: {exc}")
    results = []
    for method in METHODS:
        errors, cases, evidence, complete = list(setup_errors), [], {}, False
        if not setup_errors:
            try:
                method_errors, cases, evidence = EXECUTORS[method](root, context, expectations)
                errors.extend(method_errors)
                complete = True
            except Exception as exc:
                errors.append(f"{method} execution failed: {exc}")
        if not cases:
            errors.append(f"{method} executed no cases")
        evidence["cases"] = cases
        results.append({"method": method, "status": "fail" if errors else "pass", "execution_complete": complete,
                        "executed_case_count": len(cases), "successful_case_count": sum(case.get("result") == "pass" for case in cases),
                        "errors": errors, "evidence": evidence})
    errors, _ = method_coverage(results)
    errors.extend(f"{item['method']}: {error}" for item in results for error in item["errors"])
    return errors, results


def main() -> int:
    errors, results = validation_errors(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
    if errors:
        print("M2 validation methods failed:")
        for error in errors:
            print("  - " + error)
        return 1
    counts = ", ".join(f"{item['method']}={item['executed_case_count']}" for item in results)
    print(f"M2 validation methods passed ({counts}; schema validation foundation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
