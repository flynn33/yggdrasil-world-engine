#!/usr/bin/env python3
"""Execute source-bound rejection subjects and declared mutation scenarios offline."""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

import check_fixture_catalog as fixtures
from check_m0_truthful_baseline import normalized_text_sha256

SCENARIO_CATALOG = "data/validation/rejection_scenarios.json"
SCENARIO_SCHEMA_ID = "https://ywe.local/schemas/rejection_scenario_catalog_schema.json"
HASH_ALGORITHM = "sha256_utf8_lf_normalized"
PROJECTION_SCHEMA_PATH = "data/schemas/rejection_scenario_catalog_schema.json"
PROJECTION_DEFINITIONS = {
    "QuestCompletionConsequenceAssertion",
    "LocationConsequenceAssertion",
    "ConditionalWolfFunctionAssertion",
    "RealmThresholdAssertion",
    "RealmSharedTruthAssertion",
}


EXECUTION_CONTRACTS_PATH = "data/validation/rejection_execution_contracts.json"
EXECUTION_CONTRACTS_ID = "https://ywe.local/schemas/rejection_scenario_catalog_schema.json#/$defs/ExecutionContracts"
SCENARIO_DEFINITION_ID = "https://ywe.local/schemas/rejection_scenario_catalog_schema.json#/$defs/scenario"


def _typed_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def _contract_value(scenario):
    # Only description is cosmetic; all existing and future schema-declared
    # fields are correspondence-critical by default. Root pointer has one
    # supported equivalent spelling: absent or empty.
    value = dict(scenario)
    value.pop("description", None)
    value["descriptor_unit_pointer"] = value.get("descriptor_unit_pointer", "")
    return value


def validate_execution_contracts(root, registry, document):
    """Validate an independently authored ledger, then index unique rows."""
    errors = []
    contracts = {}
    try:
        validator = Draft202012Validator({"$ref": EXECUTION_CONTRACTS_ID}, registry=registry)
        errors.extend("Execution contract ledger: " + error.message
                      for error in validator.iter_errors(document))
        if errors:
            return errors, {}
        seen_units = set()
        for row in document["contracts"]:
            scenario_id = row["scenario_id"]
            unit = (row["descriptor_path"], row.get("descriptor_unit_pointer", ""))
            if scenario_id in contracts:
                errors.append("Duplicate approved rejection scenario ID: " + scenario_id)
            if unit in seen_units:
                errors.append("Duplicate approved rejection descriptor unit: " + repr(unit))
            seen_units.add(unit)
            contracts[scenario_id] = row
        if errors:
            return errors, {}
        return [], contracts
    except Exception as exc:
        return ["Unable to validate rejection execution contracts: " + str(exc)], {}


def load_execution_contracts(root, registry):
    try:
        document = fixtures.load_json(fixtures.repository_path(root, EXECUTION_CONTRACTS_PATH))
    except Exception as exc:
        return ["Unable to load rejection execution contracts: " + str(exc)], {}
    return validate_execution_contracts(root, registry, document)


def execution_contract_errors(root, registry, scenario, contracts=None):
    """Require reviewed correspondence before an execution counts as coverage."""
    if contracts is None:
        errors, contracts = load_execution_contracts(root, registry)
        if errors:
            return errors
    try:
        errors = ["Rejection scenario contract: " + error.message
                  for error in Draft202012Validator(
                      {"$ref": SCENARIO_DEFINITION_ID}, registry=registry
                  ).iter_errors(scenario)]
        if errors:
            return errors
        scenario_id = scenario["scenario_id"]
        if scenario_id not in contracts:
            return ["Unapproved rejection execution scenario: " + scenario_id]
        approved = _contract_value(contracts[scenario_id])
        candidate = _contract_value(scenario)
        if _typed_json(candidate) != _typed_json(approved):
            fields = sorted(key for key in set(candidate) | set(approved)
                            if key not in candidate or key not in approved
                            or _typed_json(candidate[key]) != _typed_json(approved[key]))
            return ["Rejection execution differs from approved descriptor contract "
                    + scenario_id + " at fields: " + ", ".join(fields)]
        return []
    except Exception as exc:
        return ["Unable to compare rejection execution contract: " + str(exc)]


def execution_contract_inventory_errors(scenarios, contracts):
    """Full-catalog caller only: each approved row must execute exactly once."""
    errors = []
    seen = set()
    units = set()
    for scenario in scenarios:
        if not isinstance(scenario, dict) or not isinstance(scenario.get("scenario_id"), str):
            errors.append("Malformed rejection scenario in execution inventory")
            continue
        scenario_id = scenario["scenario_id"]
        if scenario_id in seen:
            errors.append("Duplicate candidate rejection scenario ID: " + scenario_id)
        seen.add(scenario_id)
        unit = (scenario.get("descriptor_path"), scenario.get("descriptor_unit_pointer", ""))
        if unit in units:
            errors.append("Duplicate candidate rejection descriptor unit: " + repr(unit))
        units.add(unit)
    missing = sorted(set(contracts) - seen)
    extra = sorted(seen - set(contracts))
    if missing:
        errors.append("Approved rejection executions missing from catalog: " + ", ".join(missing))
    if extra:
        errors.append("Unapproved rejection executions in catalog: " + ", ".join(extra))
    return errors


def json_equal(left, right) -> bool:
    """Keep JSON booleans distinct from numbers when checking source bindings."""
    return fixtures.signature_key(left) == fixtures.signature_key(right)


def schema_errors(registry, schema_id: str, instance) -> list:
    fixtures.resolve_schema_target(registry, schema_id)
    validator = Draft202012Validator({"$ref": schema_id}, registry=registry)
    return [
        leaf
        for error in validator.iter_errors(instance)
        for leaf in fixtures.leaf_errors(error)
    ]


def schema_witnesses(registry, schema_id: str, instance) -> set[str]:
    return {
        fixtures.signature_key(fixtures.error_signature(error))
        for error in schema_errors(registry, schema_id, instance)
    }


def schema_constraint_locations(root: Path, registry) -> dict[int, list[tuple[str, str]]]:
    """Index actual schema objects, including referenced resources, by source path."""
    locations = {}
    catalog = fixtures.load_json(fixtures.repository_path(root, fixtures.CONTRACT_CATALOG))
    for entry in catalog["schemas"]:
        resource = registry[entry["schema_id"]]
        schema_nodes = {id(node) for node in fixtures.schema_nodes(resource) if isinstance(node, dict)}

        def visit(value, parts: tuple) -> None:
            if isinstance(value, dict):
                if id(value) in schema_nodes:
                    locations.setdefault(id(value), []).append(
                        (entry["path"], fixtures.pointer_from_parts(parts))
                    )
                for key, child in value.items():
                    visit(child, parts + (key,))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    visit(child, parts + (index,))

        visit(resource.contents, ())
    return locations


def validate_mutation_values(scenario: dict, owners: dict, const_assertions: dict) -> None:
    """Bind every scalar replacement to an exact source literal or typed const inverse."""
    scalar_operations = {
        index for index, operation in enumerate(scenario["operations"])
        if operation["op"] == "replace" and not isinstance(operation["value"], (dict, list))
    }
    bound_operations = set()
    for binding in scenario.get("mutation_value_bindings", []):
        index = binding["operation_index"]
        if type(index) is not int or index not in scalar_operations or index in bound_operations:
            raise ValueError("Mutation value binding must select each scalar replacement exactly once")
        bound_operations.add(index)
        source = (binding["source_path"], binding["source_pointer"])
        if source not in owners or not json_equal(owners[source], binding["source_value"]):
            raise ValueError("Mutation value binding requires its exact source owner")
        operation = scenario["operations"][index]
        value = operation["value"]
        if binding["relation"] == "negated_boolean":
            if (
                type(binding["source_value"]) is not bool
                or type(value) is not bool
                or source not in const_assertions
                or operation["path"] not in const_assertions[source]
                or value is binding["source_value"]
            ):
                raise ValueError("Boolean mutation must negate its executed const at the same target")
        elif binding["relation"] == "equal":
            if type(value) is bool or not json_equal(value, binding["source_value"]):
                raise ValueError("Scalar mutation value differs from its exact source literal")
        else:
            raise ValueError("Unsupported mutation value relation")
    if bound_operations != scalar_operations:
        raise ValueError("Every scalar replacement requires an explicit mutation value binding")


def validate_schema_owners(root: Path, registry, scenario: dict, errors: list,
                           locations: dict[int, list[tuple[str, str]]]) -> None:
    """Link every executed keyword to its exact owner and declared projection source."""
    owners = {
        (item["path"], item["pointer"]): item["value"]
        for item in scenario["owner_bindings"]
    }
    actual = set()
    required_members = set()
    const_assertions = {}
    for error in errors:
        if not isinstance(error.schema, dict) or error.validator not in error.schema:
            raise ValueError("Executed rejection has no supported owned schema keyword")
        choices = locations.get(id(error.schema), [])
        keyword = fixtures.pointer_from_parts((error.validator,))
        owned = [
            (path, pointer + keyword)
            for path, pointer in choices
            if (path, pointer + keyword) in owners
            and json_equal(owners[(path, pointer + keyword)], error.validator_value)
        ]
        if len(owned) != 1:
            raise ValueError(
                f"Executed schema constraint requires an exact owning assertion binding: "
                f"{[(path, pointer + keyword) for path, pointer in choices]}"
            )
        actual.add(owned[0])
        if error.validator == "const":
            const_assertions.setdefault(owned[0], set()).add(fixtures.pointer_from_parts(error.absolute_path))
        if error.validator == "required":
            for index, name in enumerate(error.validator_value):
                if name in error.instance:
                    continue
                member = (owned[0][0], owned[0][1] + f"/{index}")
                if member not in owners or not json_equal(owners[member], name):
                    raise ValueError(
                        f"Missing required member requires its exact owning array binding: {member!r}"
                    )
                required_members.add(member)

    mappings = {}
    projection_schema = registry[SCENARIO_SCHEMA_ID].contents
    for mapping in scenario.get("projection_bindings", []):
        pointer = mapping["assertion_pointer"]
        key = (PROJECTION_SCHEMA_PATH, pointer)
        if pointer in mappings:
            raise ValueError(f"Duplicate projection assertion mapping: {pointer!r}")
        mappings[pointer] = mapping
        if key not in actual:
            raise ValueError("Projection mapping must identify an executed projection constraint")
        definition = next(
            (name for name in PROJECTION_DEFINITIONS if pointer.startswith(f"/$defs/{name}/")), None
        )
        if definition is None:
            raise ValueError("Projection mappings are restricted to declared local assertion definitions")
        parent_pointer = pointer.rsplit("/", 1)[0]
        if not fixtures.is_schema_pointer(projection_schema, parent_pointer):
            raise ValueError("Projection mapping must identify a schema keyword")
        value = fixtures.json_pointer(projection_schema, pointer)
        if not json_equal(value, mapping["assertion_value"]) or not json_equal(owners[key], value):
            raise ValueError("Projection assertion value differs from its exact binding")
        parent_schema = fixtures.json_pointer(projection_schema, parent_pointer)
        source_ref = parent_schema.get("x-ywe-source-ref") or projection_schema["$defs"][definition].get("x-ywe-source-ref")
        if not isinstance(source_ref, str) or not source_ref:
            raise ValueError("Projection assertion has no declared owning rule")
        declared_ref = mapping["source_path"] + "#" + mapping["source_pointer"]
        if declared_ref != source_ref:
            raise ValueError("Projection source differs from its declared owning rule")
        source_key = (mapping["source_path"], mapping["source_pointer"])
        if source_key not in owners or not json_equal(owners[source_key], mapping["source_value"]):
            raise ValueError("Projection mapping requires its exact source owner binding")
        source = fixtures.load_instance(fixtures.repository_path(root, mapping["source_path"]))
        if not json_equal(fixtures.json_pointer(source, mapping["source_pointer"]), mapping["source_value"]):
            raise ValueError("Projection source value differs from its declared mapping")

    for path, pointer in actual:
        if path == PROJECTION_SCHEMA_PATH and any(
            pointer.startswith(f"/$defs/{name}/") for name in PROJECTION_DEFINITIONS
        ) and pointer not in mappings:
            raise ValueError("Executed projection constraint requires an explicit source mapping")

    schema_positions = {location for choices in locations.values() for location in choices}
    projection_sources = {
        (mapping["source_path"], mapping["source_pointer"])
        for mapping in mappings.values()
    }
    if scenario["mode"] == "mutation":
        validate_mutation_values(scenario, owners, const_assertions)
    for path, pointer in owners:
        if not pointer:
            continue
        parent, token = pointer.rsplit("/", 1)
        keyword = token.replace("~1", "/").replace("~0", "~")
        required_member = False
        if parent:
            declaration_parent, declaration_token = parent.rsplit("/", 1)
            required_member = (
                declaration_token.replace("~1", "/").replace("~0", "~") == "required"
                and (path, declaration_parent) in schema_positions
            )
        if required_member and (path, pointer) not in required_members:
            raise ValueError(
                f"Bound required member was not exercised as a missing-member rejection: {(path, pointer)!r}"
            )
        if (
            (path, parent) in schema_positions and keyword in Draft202012Validator.VALIDATORS
        ):
            if (path, pointer) not in actual | required_members | projection_sources:
                raise ValueError(
                    f"Bound executable schema constraint was not exercised or mapped: {(path, pointer)!r}"
                )


def apply_operations(instance, operations: list[dict]):
    """Apply only explicit replacements/removals of existing RFC 6901 targets."""
    result = copy.deepcopy(instance)
    paths = set()
    for operation in operations:
        path = operation["path"]
        if path in paths:
            raise ValueError(f"Duplicate mutation target: {path!r}")
        paths.add(path)
        fixtures.json_pointer(result, path)
        if operation["op"] == "replace":
            if set(operation) != {"op", "path", "value"}:
                raise ValueError("Replacement requires exactly op, path and value")
            replacement = copy.deepcopy(operation["value"])
            if path == "":
                result = replacement
                continue
        elif operation["op"] == "remove":
            if set(operation) != {"op", "path"} or path == "":
                raise ValueError("Removal requires a non-root existing target and no value")
        else:
            raise ValueError(f"Unsupported mutation operation: {operation['op']!r}")
        parent_pointer, encoded = path.rsplit("/", 1)
        parent = fixtures.json_pointer(result, parent_pointer)
        token = encoded.replace("~1", "/").replace("~0", "~")
        key = int(token) if isinstance(parent, list) else token
        if operation["op"] == "replace":
            parent[key] = replacement
        else:
            del parent[key]
    return result


def lexical_witnesses(subject, subject_pointer: str, terms) -> set[str]:
    if not isinstance(terms, list) or not terms or any(
        not isinstance(term, str) or not term.strip() for term in terms
    ):
        raise ValueError("Owning reject_terms must be a nonempty array of nonempty strings")
    if len(set(terms)) != len(terms):
        raise ValueError("Owning reject_terms contain duplicate terms")
    if isinstance(subject, str):
        subjects = [(subject_pointer, subject)]
    elif isinstance(subject, list) and subject and all(isinstance(value, str) for value in subject):
        subjects = [(subject_pointer + f"/{index}", value) for index, value in enumerate(subject)]
    else:
        raise ValueError("Lexical subject must be a string or a nonempty array of strings")
    witnesses = set()
    for pointer, text in subjects:
        matches = [term for term in terms if term.lower() in text.lower()]
        if not matches:
            raise ValueError(f"Lexical subject at {pointer!r} is accepted by its owning terms")
        witnesses.update(
            fixtures.signature_key({"subject_pointer": pointer, "term": term}) for term in matches
        )
    return witnesses


def evaluate_scenarios(root: Path, registry, scenarios: list[dict]) -> tuple[list[str], list[dict]]:
    errors = []
    results = []
    seen_ids = set()
    seen_bindings = set()
    contract_errors, contracts = load_execution_contracts(root, registry)
    if contract_errors:
        return contract_errors, []
    locations = schema_constraint_locations(root, registry)
    for scenario in scenarios:
        scenario_id = scenario["scenario_id"]
        unit_pointer = scenario.get("descriptor_unit_pointer", "")
        binding = (scenario["descriptor_path"], unit_pointer, scenario["mode"], scenario.get("subject_pointer"),
                   scenario.get("schema_id"), scenario.get("base_path"), scenario.get("base_pointer"),
                   fixtures.signature_key(scenario.get("operations")), scenario.get("rule_path"),
                   scenario.get("reject_terms_pointer"))
        if scenario_id in seen_ids or binding in seen_bindings:
            errors.append(f"Duplicate rejection scenario ID or binding: {scenario_id}")
            continue
        seen_ids.add(scenario_id)
        seen_bindings.add(binding)
        try:
            descriptor_path = fixtures.repository_path(root, scenario["descriptor_path"])
            if scenario["hash_algorithm"] != HASH_ALGORITHM:
                raise ValueError("Unsupported descriptor hash algorithm")
            if normalized_text_sha256(descriptor_path) != scenario["descriptor_sha256"]:
                raise ValueError("Descriptor source digest differs from its recorded binding")
            descriptor = fixtures.load_instance(descriptor_path)
            reason_pointers = {"/reject_reason", "/invalid_reason"}
            required_unit_bindings = set()
            if unit_pointer:
                player_unit = (
                    re.fullmatch(r"/cases/(?:0|[1-9][0-9]*)", unit_pointer)
                    and isinstance(descriptor, dict)
                    and descriptor.get("schema_id") == "ywe.phase_10_invalid_player_state_rejection_cases.v1"
                )
                realm_unit = (
                    scenario["descriptor_path"] == "data/realm/realm_transition_examples.yaml"
                    and re.fullmatch(r"/unlawful_examples/(?:0|[1-9][0-9]*)", unit_pointer)
                    and isinstance(descriptor, dict)
                    and isinstance(descriptor.get("meta"), dict)
                    and descriptor["meta"].get("system") == "realm_transition_examples"
                )
                if not player_unit and not realm_unit:
                    raise ValueError("Descriptor units are supported only for the declared player rejection collection or realm unlawful collection")
                unit = fixtures.json_pointer(descriptor, unit_pointer)
                if not isinstance(unit, dict):
                    raise ValueError("Rejection unit must be an object")
                if realm_unit:
                    if scenario["mode"] != "mutation" or scenario["validation_scope"] != "assertion_projection":
                        raise ValueError("Realm unlawful units require their declared assertion projection mutation")
                    reason_pointers = {unit_pointer + "/summary"}
                    required_unit_bindings = {unit_pointer + "/example_id", unit_pointer + "/violated_rules"}
                    rules = unit.get("violated_rules")
                    if not isinstance(rules, list) or not rules or any(not isinstance(rule, str) or not rule.strip() for rule in rules):
                        raise ValueError("Realm rejection unit requires nonempty declared violated rules")
                else:
                    reason_pointers = {unit_pointer + "/reason"}
            elif isinstance(descriptor, dict) and descriptor.get("schema_id") in {
                "wolf_manifestation_event_schema", "quest_reward_resolution_packet_schema"
            }:
                reason_pointers.add("/expected_rejection_reason")
            bindings = scenario["descriptor_bindings"]
            binding_pointers = set()
            for item in bindings:
                pointer = item["pointer"]
                if pointer in binding_pointers:
                    raise ValueError(f"Duplicate descriptor binding pointer: {pointer!r}")
                binding_pointers.add(pointer)
                if not json_equal(fixtures.json_pointer(descriptor, pointer), item["value"]):
                    raise ValueError(f"Descriptor value differs at {pointer!r}")
            if not binding_pointers.intersection(reason_pointers):
                raise ValueError("Descriptor requires an explicit expected-reason binding")
            if not required_unit_bindings.issubset(binding_pointers):
                raise ValueError("Realm rejection unit requires exact identity and complete violated-rule bindings")
            for pointer in binding_pointers.intersection(reason_pointers):
                reason = fixtures.json_pointer(descriptor, pointer)
                if not isinstance(reason, str) or not reason.strip():
                    raise ValueError("Expected reason must be a nonempty string")
            owner_pointers = set()
            for item in scenario["owner_bindings"]:
                owner_binding = (item["path"], item["pointer"])
                if owner_binding in owner_pointers:
                    raise ValueError(f"Duplicate owner binding: {owner_binding!r}")
                owner_pointers.add(owner_binding)
                owner = fixtures.load_instance(fixtures.repository_path(root, item["path"]))
                if not json_equal(fixtures.json_pointer(owner, item["pointer"]), item["value"]):
                    raise ValueError(f"Owning assertion differs at {owner_binding!r}")

            mode = scenario["mode"]
            if mode in {"direct", "lexical"}:
                pointer = scenario["subject_pointer"]
                if unit_pointer and pointer != unit_pointer and not pointer.startswith(unit_pointer + "/"):
                    raise ValueError("Selected subject lies outside its descriptor unit")
                if pointer not in binding_pointers:
                    raise ValueError("Selected subject requires an explicit descriptor value binding")
                subject = fixtures.json_pointer(descriptor, pointer)
            if mode == "lexical":
                relative = scenario["rule_path"]
                if not relative.startswith("data/validation/"):
                    raise ValueError("Lexical reject_terms must belong to a data/validation rule file")
                rules = fixtures.load_instance(fixtures.repository_path(root, relative))
                terms = fixtures.json_pointer(rules, scenario["reject_terms_pointer"])
                if scenario["reject_terms_pointer"].rsplit("/", 1)[-1] not in {"reject_terms", "forbidden_patterns"}:
                    raise ValueError("Lexical assertions must select an explicitly declared reject_terms list or forbidden_patterns list")
                exact_owner = (relative, scenario["reject_terms_pointer"])
                if exact_owner not in owner_pointers or not any(
                    (item["path"], item["pointer"]) == exact_owner
                    and json_equal(item["value"], terms)
                    for item in scenario["owner_bindings"]
                ):
                    raise ValueError("Lexical assertion requires its exact owning reject_terms binding")
                witnessed = lexical_witnesses(subject, pointer, terms)
                expected = {fixtures.signature_key(item) for item in scenario["expected_matches"]}
            elif mode in {"direct", "mutation"}:
                if mode == "mutation":
                    base = fixtures.json_pointer(
                        fixtures.load_instance(fixtures.repository_path(root, scenario["base_path"])),
                        scenario["base_pointer"],
                    )
                    base_errors = schema_witnesses(registry, scenario["schema_id"], base)
                    if base_errors:
                        raise ValueError(f"Mutation base is rejected: {sorted(base_errors)}")
                    subject = apply_operations(base, scenario["operations"])
                executed_errors = schema_errors(registry, scenario["schema_id"], subject)
                witnessed = {
                    fixtures.signature_key(fixtures.error_signature(error))
                    for error in executed_errors
                }
                expected = {fixtures.signature_key(item) for item in scenario["expected_errors"]}
            else:
                raise ValueError(f"Unsupported rejection scenario mode: {mode!r}")
            if not witnessed or witnessed != expected:
                raise ValueError(f"Expected complete rejection witnesses {sorted(expected)}; observed {sorted(witnessed)}")
            if mode in {"direct", "mutation"}:
                validate_schema_owners(root, registry, scenario, executed_errors, locations)
                if unit_pointer and realm_unit:
                    selected = fixtures.resolve_schema_target(registry, scenario["schema_id"]).contents
                    if not isinstance(selected, dict) or selected.get("x-ywe-descriptor-unit-ref") != scenario["descriptor_path"] + "#" + unit_pointer:
                        raise ValueError("Realm assertion must own its exact declared unlawful unit")
                    witnessed_rules = {error.schema.get("x-ywe-violated-rule") for error in executed_errors
                                       if error.validator == "const" and isinstance(error.schema, dict)}
                    if not set(unit["violated_rules"]).issubset(witnessed_rules):
                        raise ValueError("Realm rejection must execute every declared violated rule")
            else:
                validate_schema_owners(root, registry, scenario, [], locations)
            correspondence_errors = execution_contract_errors(root, registry, scenario, contracts)
            if correspondence_errors:
                raise ValueError("; ".join(correspondence_errors))
            results.append({
                "descriptor_path": scenario["descriptor_path"],
                "descriptor_unit_pointer": unit_pointer,
                "scenario_id": scenario_id,
                "result": "reject",
                "validation_scope": scenario["validation_scope"],
            })
        except Exception as exc:
            errors.append(f"Rejection scenario {scenario_id}: {exc}")
    return errors, results


def validation_errors(root: Path) -> tuple[list[str], list[dict]]:
    try:
        registry, errors = fixtures.load_registry(root)
        if errors:
            return errors, []
        fixtures.resolve_schema_target(registry, SCENARIO_SCHEMA_ID)
        catalog = fixtures.load_json(fixtures.repository_path(root, SCENARIO_CATALOG))
        validator = Draft202012Validator({"$ref": SCENARIO_SCHEMA_ID}, registry=registry)
        errors.extend(f"{SCENARIO_CATALOG}: {error.message}" for error in validator.iter_errors(catalog))
        if errors:
            return errors, []
        errors, results = evaluate_scenarios(root, registry, catalog["scenarios"])
        contract_errors, contracts = load_execution_contracts(root, registry)
        errors.extend(contract_errors)
        if not contract_errors:
            errors.extend(execution_contract_inventory_errors(catalog["scenarios"], contracts))
        return errors, results
    except Exception as exc:
        return [f"Unable to load rejection scenario/schema catalogs: {exc}"], []


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors, results = validation_errors(root)
    if errors:
        print("Rejection scenario check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print(f"Rejection scenario check passed ({len(results)} source-bound rejections; offline schema resolution).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
