#!/usr/bin/env python3
"""Evaluate the roadmap's M2 obligations without changing milestone status."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator

import check_fixture_catalog as fixtures
import check_m0_truthful_baseline as baseline
import check_rejection_scenarios as rejection_scenarios
import check_m2_validation_operations as validation_operations
import check_m2_validation_methods as validation_methods
from check_machine_readable_artifacts import quality_debt
from validate_repository import check_applies

ROADMAP = "data/governance/specification_roadmap.json"
CHECKS = "data/validation/repository_checks.json"
DEBT = "data/validation/schema_quality_baseline.json"
CLASSIFICATION = "data/governance/artifact_classification_manifest.json"
SCOPE = "data/governance/scope_partition_manifest.json"
VALIDATION_COVERAGE = "data/validation/m2_validation_coverage.json"
EXIT_CRITERIA = (
    "Every normative schema passes its meta-schema.",
    "Every reference resolves without a network dependency.",
    "Every normative fixture is bound to a schema.",
    "Every reject fixture fails for its intended requirement.",
    "The schema-quality debt inventory is empty.",
    "A roadmap-derived M2 acceptance gate passes from a clean offline checkout.",
)
DELIVERABLES = (
    "One JSON Schema 2020-12 profile, URI namespace, catalog, and offline resolver.",
    "Convert descriptive schema-named records into schemas or rename them by their actual role.",
    "Common identifier, reference, version, time, ordering, request, result, event, provenance, diagnostic, error, transaction, compensation, idempotency, retry, extension, and deprecation contracts.",
    "YAML structural schemas.",
    "Explicit fixture catalog mapping schema, instance pointer, expected result, and expected requirement or error identifiers.",
    "Positive, boundary, reject, recovery, replay, and migration fixtures.",
    "Meta-schema, instance, reference, identifier, dependency, negative, property, and mutation validation.",
    "Roadmap-derived M2 acceptance gate and durable acceptance evidence.",
)
COMMON_CONTRACTS = (
    "identifier", "reference", "version", "time", "ordering", "request", "result",
    "event", "provenance", "diagnostic", "error", "transaction", "compensation",
    "idempotency", "retry", "extension", "deprecation",
)
VALIDATION_METHODS = (
    "meta_schema", "instance", "reference", "identifier", "dependency", "negative",
    "property", "mutation",
)
BUNDLE_PATHS = {
    "examples/contract_foundation/common_contract_cases.example.json",
    "examples/contract_foundation/phase_12_representation_cases.example.json",
    "examples/contract_foundation/module_capability_cases.example.yaml",
    "examples/contract_foundation/legacy_example_representation_cases.example.json",
    "examples/contract_foundation/pattern_archetype_registry_cases.example.yaml",
    "examples/contract_foundation/ability_semantic_cases.example.json",
    "examples/contract_foundation/yaml_descriptor_cases.example.yaml",
    "examples/contract_foundation/phase_9_representation_cases.example.json",
    "examples/contract_foundation/ravenfall_preview_format_cases.example.json",
    "examples/contract_foundation/m2_validation_operation_cases.example.json",
    "examples/contract_foundation/yaml_policy_document_cases.example.json",
    "examples/contract_foundation/realm_assertion_cases.example.json",
}
BUNDLE_METADATA = {
    "examples/contract_foundation/realm_assertion_cases.example.json": {
        "artifact_type": "realm_assertion_cases", "artifact_version": "1.0.0",
        "validation_scope": "assertion_projection",
    },
    "examples/contract_foundation/yaml_policy_document_cases.example.json": {
        "artifact_type": "yaml_policy_document_cases", "artifact_version": "1.0.0",
    },
    "examples/contract_foundation/ravenfall_preview_format_cases.example.json": {
        "artifact_type": "ravenfall_preview_format_cases", "artifact_version": "1.0.0",
    },
    "examples/contract_foundation/m2_validation_operation_cases.example.json": {
        "artifact_type": "m2_validation_operation_cases", "artifact_version": "1.0.0",
        "validation_scope": "schema_validation_operation",
    },
    "examples/contract_foundation/phase_9_representation_cases.example.json": {
        "artifact_type": "phase_9_representation_cases", "artifact_version": "1.0.0",
    },
    "examples/contract_foundation/ability_semantic_cases.example.json": {
        "artifact_type": "ability_semantic_cases", "artifact_version": "1.0.0",
    },
    "examples/contract_foundation/yaml_descriptor_cases.example.yaml": {
        "artifact_type": "yaml_descriptor_cases", "artifact_version": "1.0.0",
    },
    "examples/contract_foundation/pattern_archetype_registry_cases.example.yaml": {
        "artifact_type": "pattern_archetype_registry_cases", "artifact_version": "1.0.0",
    },
    "examples/contract_foundation/legacy_example_representation_cases.example.json": {
        "artifact_type": "legacy_example_representation_cases", "artifact_version": "1.0.0",
    },
}


def roadmap_definition_errors(roadmap: dict) -> list[str]:
    milestones = [item for item in roadmap.get("milestones", []) if item.get("id") == "M2"]
    if len(milestones) != 1:
        return ["The roadmap must contain exactly one M2 milestone"]
    errors = []
    for field, expected in (("exit_criteria", EXIT_CRITERIA), ("deliverables", DELIVERABLES)):
        if milestones[0].get(field) != list(expected):
            errors.append(f"M2 {field} differ from the supported ordered evaluator contract")
    return errors


def fixture_units(root: Path, relative: str) -> list[str]:
    if relative == "data/realm/realm_transition_examples.yaml":
        document = fixtures.load_instance(root / relative)
        if not isinstance(document, dict) or not isinstance(document.get("meta"), dict) or document["meta"].get("system") != "realm_transition_examples":
            raise ValueError("Realm guidance collection must retain its declared document identity")
        units = [""]
        for group in ("lawful_examples", "unlawful_examples"):
            cases = document.get(group)
            if not isinstance(cases, list) or not cases:
                raise ValueError("Realm guidance collection must contain both declared case roles")
            units.extend(f"/{group}/{index}" for index in range(len(cases)))
        return units
    if relative == "examples/player_runtime_state/invalid_player_state_rejection_cases.example.json":
        document = fixtures.load_instance(root / relative)
        if not isinstance(document, dict) or not isinstance(document.get("cases"), list) or not document["cases"]:
            raise ValueError("Player rejection collection must contain individual case descriptions")
        return [f"/cases/{index}" for index in range(len(document["cases"]))]
    if relative not in BUNDLE_PATHS:
        return [""]
    document = fixtures.load_instance(root / relative)
    if not isinstance(document, dict) or not document:
        raise ValueError("Registered fixture bundle must contain named case groups")
    units = []
    metadata = BUNDLE_METADATA.get(relative, {})
    for field, expected in metadata.items():
        if document.get(field) != expected:
            raise ValueError(f"Registered fixture bundle has invalid {field!r}")
    for group, cases in document.items():
        if group in metadata or (metadata and group == "description" and isinstance(cases, str)):
            continue
        if not isinstance(cases, dict) or not cases:
            raise ValueError(f"Registered fixture bundle group {group!r} must contain named cases")
        units.extend(fixtures.pointer_from_parts((group, case)) for case in cases)
    if not units:
        raise ValueError("Registered fixture bundle must contain at least one case")
    return sorted(units)


def rejection_coverage(root: Path, paths: list[str], successful: list[dict],
                       scenario_results: list[dict]) -> tuple[list[str], dict]:
    """Require an executed rejection for each source description, independently of format acceptance."""
    designated = [path for path in paths
                  if "invalid" in Path(path).name.lower() or ".reject." in Path(path).name.lower()]
    expected = {(path, pointer) for path in designated for pointer in fixture_units(root, path)}
    realm = "data/realm/realm_transition_examples.yaml"
    if realm in paths:
        expected.update((realm, pointer) for pointer in fixture_units(root, realm)
                        if pointer.startswith("/unlawful_examples/"))
    witnessed = {(item["path"], item["instance_pointer"]) for item in successful
                 if item["expected_result"] == "reject"}
    witnessed.update((item["descriptor_path"], item.get("descriptor_unit_pointer", ""))
                     for item in scenario_results if item["result"] == "reject")
    missing = [{"path": path, "instance_pointer": pointer} for path, pointer in sorted(expected - witnessed)]
    errors = [f"Rejection-designated units lack executed intended witnesses: {missing}"] if missing else []
    return errors, {"expected_rejection_units": len(expected),
                    "executed_rejection_units": len(expected & witnessed),
                    "unwitnessed_rejection_units": missing,
                    "unwitnessed_rejection_paths": sorted({item["path"] for item in missing})}


def fixture_coverage(root: Path, paths: list[str], classification: dict,
                     catalog: dict, results: list[dict]) -> tuple[list[str], dict]:
    errors = []
    assignments = baseline.effective_assignments(paths, classification, "classification", errors, "M2 classification")
    candidates = sorted(path for path in paths if assignments.get(path, {}).get("classification") == "example"
                        and Path(path).suffix.lower() in {".json", ".yaml", ".yml"})
    successful = {(item["fixture_id"], item["path"]) for item in results}
    bindings = set()
    for item in catalog.get("fixtures", []):
        if (item["fixture_id"], item["path"]) not in successful:
            continue
        group = item["instance_pointer"].split("/")[1:2]
        if item["path"] in BUNDLE_PATHS and group and group[0] in {"positive", "boundary", "reject"}:
            expected = "reject" if group[0] == "reject" else "accept"
            if item["category"] != group[0] or item["expected_result"] != expected:
                errors.append(f"Fixture bundle role differs from binding: {item['fixture_id']}")
                continue
        bindings.add((item["path"], item["instance_pointer"]))
    missing = []
    unit_count = 0
    for relative in candidates:
        try:
            units = fixture_units(root, relative)
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"Fixture layout is unverified for {relative}: {exc}")
            continue
        unit_count += len(units)
        missing.extend({"path": relative, "instance_pointer": pointer} for pointer in units
                       if (relative, pointer) not in bindings)
    if missing:
        errors.append(f"{len(missing)} classified fixture units have no successful exact binding")
    return errors, {
        "structured_fixture_paths": candidates,
        "expected_unit_count": unit_count,
        "successful_unit_count": unit_count - len(missing),
        "bound_path_count": len({path for path, _ in bindings if path in candidates}),
        "uncovered_units": missing,
    }


def repository_evidence_errors(root: Path, report: dict | None, check_manifest: dict) -> list[str]:
    if report is None:
        return ["No executed repository validation report was supplied"]
    schema = fixtures.load_json(root / "data/schemas/repository_validation_report_schema.json")
    errors = [f"Repository report: {error.message}" for error in Draft202012Validator(schema).iter_errors(report)]
    if errors:
        return errors
    if not report["execution_complete"]:
        errors.append("Repository evidence lacks a completed final checkout-state capture")
    if report["context"] != "local":
        errors.append("M2 checkout acceptance requires the local full-suite context")
    expected = [check for check in check_manifest["checks"] if check_applies(check, report["context"])]
    expected_ids = [check["id"] for check in expected]
    if [item["check_id"] for item in report["results"]] != expected_ids:
        errors.append("Repository evidence must include every applicable check exactly once in catalog order")
    if report["selection"] != {"groups": [], "check_ids": []}:
        errors.append("Filtered repository runs cannot establish full acceptance evidence")
    revision = baseline.checked_git_output(root, ["rev-parse", "HEAD"]).decode().strip()
    if report["revision"] != revision:
        errors.append("Repository evidence targets a different revision")
    if report["check_catalog_sha256"] != baseline.normalized_text_sha256(root / CHECKS):
        errors.append("Repository evidence targets a different check catalog")
    if report["dirty_before"] or report["dirty_after"]:
        errors.append("Repository evidence did not execute in a clean checkout")
    if baseline.checked_git_output(root, ["status", "--porcelain", "--untracked-files=all"]).strip():
        errors.append("The current acceptance checkout is dirty")
    if report["offline"] != {"requested": True, "git_allow_protocol": "file"}:
        errors.append("Repository evidence did not deny remote Git protocols")
    if any(item["return_code"] != 0 for item in report["results"]):
        errors.append("Repository evidence contains a failed check")
    if report["summary"] != {"passed": len(expected), "blocking_failures": 0, "advisories": 0}:
        errors.append("Repository evidence summary does not establish an entirely passing suite")
    if any(not report["tool_versions"].get(name) for name in ("python", "jsonschema", "PyYAML", "referencing")):
        errors.append("Repository evidence omits a required tool version")
    if [item["blocking"] for item in report["results"]] != [item["blocking"] for item in expected]:
        errors.append("Repository evidence changed check severity")
    return errors


def obligation(identifier: str, statement: str, errors: list[str], evidence: dict | None = None,
               unverified: bool = False) -> dict:
    return {"id": identifier, "statement": statement,
            "status": "unverified" if unverified else "fail" if errors else "pass",
            "errors": errors, "evidence": evidence or {}}


def build_report(root: Path, repository_report: dict | None = None, *, verify_historical: bool = True) -> dict:
    root = root.resolve()
    report = {"artifact_type": "ywe_m2_readiness_report", "artifact_version": "1.0.0",
              "ready": False, "criteria": [], "deliverables": [], "errors": []}
    try:
        roadmap = fixtures.load_json(root / ROADMAP)
        report["errors"].extend(roadmap_definition_errors(roadmap))
        report["roadmap_sha256"] = baseline.normalized_text_sha256(root / ROADMAP)
        report["revision"] = baseline.checked_git_output(root, ["rev-parse", "HEAD"]).decode().strip()
        paths = baseline.repository_candidate_paths(root, report["errors"])
        classification = fixtures.load_json(root / CLASSIFICATION)
        scope = fixtures.load_json(root / SCOPE)
        assignment_errors = []
        classes = baseline.effective_assignments(paths, classification, "classification", assignment_errors, "M2 classification")
        partitions = baseline.effective_assignments(paths, scope, "primary_partition", assignment_errors, "M2 scope")
        report["errors"].extend(assignment_errors)
        profile = fixtures.load_json(root / "data/validation/m2_json_contract_profile.json")
        json_documents = {path: fixtures.load_json(root / path) for path in paths if Path(path).suffix.lower() == ".json"}
        declarations = {path: value for path, value in json_documents.items()
                        if isinstance(value, dict) and "$schema" in value}
        normative = {path: value for path, value in declarations.items()
                     if classes.get(path, {}).get("classification") == "normative"}
        meta_errors = []
        for relative, schema in normative.items():
            try:
                Draft202012Validator.check_schema(schema)
            except Exception as exc:
                meta_errors.append(f"Invalid normative meta-schema {relative}: {exc}")
        registry, reference_errors = fixtures.load_registry(root)
        fixture_errors, results = fixtures.validation_errors(root)
        catalog = fixtures.load_json(root / fixtures.FIXTURE_CATALOG)
        coverage_errors, coverage = fixture_coverage(root, paths, classification, catalog, results)
        successful_ids = {item["fixture_id"] for item in results}
        successful = [item for item in catalog["fixtures"] if item["fixture_id"] in successful_ids]
        scenario_errors, scenario_results = rejection_scenarios.validation_errors(root)
        reject_errors, rejection_evidence = rejection_coverage(
            root, coverage["structured_fixture_paths"], successful, scenario_results)
        reject_errors.extend(fixture_errors + scenario_errors)
        actual_debt = quality_debt(declarations, json_documents,
                                   {item["path"] for item in results} if not fixture_errors else set())
        debt_errors = []
        if actual_debt != fixtures.load_json(root / DEBT).get("known_debt"):
            debt_errors.append("Actual schema debt differs from its registered baseline")
        if any(actual_debt.values()):
            debt_errors.append("Schema quality debt is not empty")
        checks = fixtures.load_json(root / CHECKS)
        evidence_errors = repository_evidence_errors(root, repository_report, checks)
        report["criteria"] = [
            obligation("M2-C1", EXIT_CRITERIA[0], meta_errors, {"normative_schema_count": len(normative), "declared_schema_count": len(declarations)}),
            obligation("M2-C2", EXIT_CRITERIA[1], reference_errors, {"retrieval_policy": "deny_unknown_resources"}),
            obligation("M2-C3", EXIT_CRITERIA[2], coverage_errors, coverage),
            obligation("M2-C4", EXIT_CRITERIA[3], reject_errors,
                       {**rejection_evidence, "executed_rejections": sum(item["expected_result"] == "reject" for item in successful),
                        "executed_scenarios": len(scenario_results)}),
            obligation("M2-C5", EXIT_CRITERIA[4], debt_errors, actual_debt),
            obligation("M2-C6", EXIT_CRITERIA[5], evidence_errors,
                       {"scope": "schema resolution and remote Git retrieval denied; dependencies prepared before execution"}, repository_report is None),
        ]
        profile_errors = list(meta_errors + reference_errors)
        if profile.get("dialect") != fixtures.DIALECT or profile.get("canonical_uri_namespace") != "https://ywe.local/schemas/" or profile.get("network_resolution_allowed") is not False:
            profile_errors.append("M2 profile differs from the supported dialect/namespace/offline policy")
        profile_errors.extend(f"Normative schema identifier is outside the canonical namespace: {path}" for path, value in normative.items()
                              if not isinstance(value.get("$id"), str) or not value["$id"].startswith("https://ywe.local/schemas/"))
        conversion_errors = [f"Descriptive schema debt remains: {kind}" for kind in (
            "declared_schema_missing_id", "annotation_only_schema_documents", "schema_named_json_without_schema_declaration") if actual_debt[kind]]
        common_errors = []
        for name in COMMON_CONTRACTS:
            relative = f"data/schemas/common/{name}.schema.json"
            schema = normative.get(relative)
            if schema is None:
                common_errors.append(f"Missing normative common contract: {name}")
                continue
            outcomes = {item["expected_result"] for item in successful if item["schema_id"] == schema["$id"]}
            if outcomes != {"accept", "reject"}:
                common_errors.append(f"Common contract lacks positive/reject execution: {name}")
        domain_yaml = sorted(path for path in paths if Path(path).suffix.lower() in {".yaml", ".yml"}
                             and classes.get(path, {}).get("classification") in {"normative", "example"}
                             and not path.startswith(".github/")
                             and partitions.get(path, {}).get("primary_partition") != "later_release_work")
        missing_yaml = []
        for relative in domain_yaml:
            units = fixture_units(root, relative)
            if any(not any(item["path"] == relative and item["instance_pointer"] == pointer
                           and (classes.get(relative, {}).get("classification") != "normative"
                                or item["expected_result"] == "accept")
                           for item in successful) for pointer in units):
                missing_yaml.append(relative)
        yaml_errors = [f"Domain YAML has no complete structural binding: {path}" for path in missing_yaml]
        identifier_errors = fixtures.fixture_requirement_errors(root, registry, catalog["fixtures"])
        categories = sorted({item["category"] for item in successful})
        category_errors = [f"No successful {category} fixture exists" for category in ("positive", "boundary", "reject") if category not in categories]
        operation_errors, operation_results = validation_operations.validation_errors(root)
        lifecycle_errors, lifecycle_evidence = validation_operations.category_coverage(catalog, results, operation_results)
        category_errors.extend(operation_errors + lifecycle_errors)
        validation_errors, method_results = validation_methods.validation_errors(root)
        method_errors, method_evidence = validation_methods.method_coverage(method_results)
        validation_errors.extend(method_errors)
        historical_errors = ["Durable M2 acceptance evidence is not recorded"]
        historical_evidence = {}
        if verify_historical:
            try:
                import check_m2_historical_acceptance as historical_acceptance

                historical_errors, historical_evidence = historical_acceptance.validation_errors(root)
                if historical_evidence.get("outcome") != "pass":
                    historical_errors.append("Durable M2 acceptance evidence is not accepted")
            except ImportError:
                pass
        report["deliverables"] = [
            obligation("M2-D1", DELIVERABLES[0], profile_errors),
            obligation("M2-D2", DELIVERABLES[1], conversion_errors),
            obligation("M2-D3", DELIVERABLES[2], common_errors),
            obligation("M2-D4", DELIVERABLES[3], yaml_errors, {"domain_yaml_paths": domain_yaml, "uncovered_paths": missing_yaml}),
            obligation("M2-D5", DELIVERABLES[4], fixture_errors + identifier_errors),
            obligation("M2-D6", DELIVERABLES[5], category_errors,
                       {"successful_categories": categories, **lifecycle_evidence}),
            obligation("M2-D7", DELIVERABLES[6], validation_errors, method_evidence),
            obligation("M2-D8", DELIVERABLES[7], evidence_errors + historical_errors, historical_evidence,
                       unverified=repository_report is None or not verify_historical or not historical_evidence
                       or historical_evidence.get("outcome") == "pending"),
        ]
        report["ready"] = not report["errors"] and all(item["status"] == "pass" for item in report["criteria"] + report["deliverables"])
    except Exception as exc:
        report["errors"].append(f"Unable to evaluate M2 readiness: {exc}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", type=Path)
    parser.add_argument("--check-definition", action="store_true")
    parser.add_argument("--repository-report", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--evidence-formation", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    if args.check_definition:
        try:
            errors = roadmap_definition_errors(fixtures.load_json(root / ROADMAP))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            errors = [f"Unable to evaluate the roadmap definition: {exc}"]
        if errors:
            print("M2 gate definition check failed: " + "; ".join(errors))
            return 1
        print("M2 gate definition check passed (six criteria and eight deliverables mapped; milestone acceptance not evaluated).")
        return 0
    repository_report = fixtures.load_json(args.repository_report) if args.repository_report else None
    report = build_report(root, repository_report, verify_historical=not args.evidence_formation)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("M2 readiness: " + ("ready" if report["ready"] else "not ready"))
    for item in report["criteria"] + report["deliverables"]:
        print(f"  {item['id']}: {item['status']} — {item['statement']}")
    for error in report["errors"]:
        print(f"  error: {error}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
