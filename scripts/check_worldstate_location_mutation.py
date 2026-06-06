#!/usr/bin/env python3
"""Validate Phase 11 worldstate and location mutation contract coverage."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

TEXT_ENCODING = "utf-8-sig"
DEFAULT_CONTRACT = "data/validation/worldstate_location_mutation_gate_contract.json"
PHASE_10_REQUIRED_ARTIFACTS = "data/validation/required_phase_10_artifacts.json"
PHASE_11_REQUIRED_ARTIFACTS = "data/validation/phase_11_required_artifacts.json"
PHASE_11_NON_DESTRUCTIVE_BUDGET = "data/validation/phase_11_non_destructive_change_budget.json"
PHASE_11_FORBIDDEN_LANGUAGE = "data/validation/phase_11_forbidden_language_patterns.json"
PHASE_11_RAVENFALL_EXAMPLES = "data/validation/ravenfall_gate_phase_11_example_validation.json"
PHASE_11_EXAMPLE_ROOT = "examples/phase_11_worldstate_location_mutation"

PHASE_11_EXTRA_REQUIRED_FILES = [
    "docs/architecture/worldstate_location_integration_map.md",
    "data/validation/phase_11_required_artifacts.json",
    "data/validation/phase_11_forbidden_language_patterns.json",
    "data/validation/phase_11_non_destructive_change_budget.json",
    "data/validation/phase_11_github_checks_matrix.json",
    "data/validation/truth_scope_validation_rules.json",
    "data/validation/worldstate_delta_validation_rules.json",
    "data/validation/location_mutation_validation_rules.json",
    "data/validation/location_branch_overlay_validation_rules.json",
    "data/validation/future_generation_bias_validation_rules.json",
]

PHASE_11_CHECK_SPECS = [
    "data/validation/check_phase_10_acceptance_prereq.spec.json",
    "data/validation/check_required_phase_11_contracts.spec.json",
    "data/validation/check_phase_11_json_integrity.spec.json",
    "data/validation/check_worldstate_delta_schema.spec.json",
    "data/validation/check_location_mutation_contracts.spec.json",
    "data/validation/check_truth_scope_guardrail.spec.json",
    "data/validation/check_no_static_only_location_model.spec.json",
    "data/validation/check_no_pregenerated_branch_tree_phase_11.spec.json",
    "data/validation/check_no_feature_consequence_without_packet.spec.json",
    "data/validation/check_future_generation_bias_refs.spec.json",
    "data/validation/check_ravenfall_gate_phase_11_examples.spec.json",
    "data/validation/check_non_destructive_diff_phase_11.spec.json",
]

PHASE_10_SEMANTIC_TARGETS = [
    "docs/architecture/player_runtime_state_contract.md",
    "docs/architecture/player_state_branch_integration_contract.md",
    "docs/architecture/celestial_identity_progression_contract.md",
    "docs/architecture/plane_attunement_runtime_contract.md",
    "docs/architecture/bloodline_resonance_runtime_contract.md",
    "docs/architecture/player_state_asp_resilience_contract.md",
    "data/schemas/player_runtime_state_schema.json",
]

PHASE_10_SEMANTIC_REQUIREMENTS = [
    ((("current leaf branch reality",),), "Phase 10 must reference current leaf branch reality."),
    (
        (("without replacing it",), ("replace leaf branch reality state",)),
        "Phase 10 must preserve that player state does not own or replace branch reality.",
    ),
    ((("revealed through play",),), "Phase 10 must preserve reveal-through-play identity progression."),
    (
        (("celestial_identity_initial_state", '"const": "veiled"'),),
        "Phase 10 must preserve veiled initial celestial identity.",
    ),
    ((("runtime pressure signal",),), "Phase 10 must preserve plane attunement as dynamic pressure."),
    (
        (("not a static class lock",),),
        "Phase 10 must preserve bloodline resonance as pressure, not class lock.",
    ),
    ((("treat wolf resonance as morality",),), "Phase 10 must preserve wolf resonance non-morality guardrail."),
    ((("playerstateupdatepacket",),), "Phase 10 must preserve PlayerStateUpdatePacket update control."),
    (
        (("ash pattern system is a ywe component",),),
        "Phase 10 must preserve ASH Pattern System component role.",
    ),
]

PHASE_11_JSON_SCAN_DIRS = (
    "data/schemas",
    "data/validation",
    "examples",
)

PHASE_11_SCAN_PATHS = [
    "docs/architecture/worldstate_delta_contract.md",
    "docs/architecture/location_state_resolver_contract.md",
    "docs/architecture/location_branch_overlay_contract.md",
    "docs/architecture/location_mutation_rule_contract.md",
    "docs/architecture/future_generation_bias_contract.md",
    "docs/architecture/shared_truth_vs_branch_truth_contract.md",
    "docs/architecture/consequence_classification_contract.md",
    "docs/architecture/worldstate_location_integration_map.md",
]

ALLOWED_TRUTH_SCOPES = {
    "base_world_truth",
    "shared_world_truth",
    "leaf_branch_truth",
    "player_perception",
    "mythic_interpretation",
    "prophetic_pressure",
    "faction_claim",
    "host_materialization",
    "diagnostic_noop",
}

ALLOWED_CONSEQUENCE_CLASSES = {
    "shared_world_truth_change",
    "leaf_branch_truth_change",
    "location_state_change",
    "location_access_change",
    "perception_overlay_change",
    "myth_pressure_change",
    "prophecy_pressure_change",
    "faction_claim_change",
    "npc_relationship_change",
    "artifact_binding_change",
    "creature_ecology_change",
    "ability_pressure_change",
    "player_state_reference",
    "future_generation_bias_update",
    "diagnostic_noop",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding=TEXT_ENCODING)


def load_json(path: Path):
    with path.open(encoding=TEXT_ENCODING) as handle:
        return json.load(handle)


def relative_name(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def load_json_checked(root: Path, path: Path, errors: list[str]):
    path_name = relative_name(root, path)
    if not path.is_file():
        errors.append(f"Missing required JSON file: {path_name}")
        return None

    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {path_name}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"Unable to read {path_name}: {exc}")
    return None


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def git_ref_exists(root: Path, ref: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "--quiet", ref],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def git_fetch_origin_branch(root: Path, branch: str) -> bool:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "fetch",
                "--no-tags",
                "--depth=1",
                "origin",
                f"{branch}:refs/remotes/origin/{branch}",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return False
    return result.returncode == 0


def default_base_ref(root: Path) -> str | None:
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidate = f"origin/{github_base_ref}"
        if git_ref_exists(root, candidate):
            return candidate
        if git_fetch_origin_branch(root, github_base_ref) and git_ref_exists(root, candidate):
            return candidate

    base_ref = os.environ.get("BASE_REF")
    if base_ref:
        if git_ref_exists(root, base_ref):
            return base_ref
        if base_ref.startswith("origin/"):
            branch = base_ref.removeprefix("origin/")
            if git_fetch_origin_branch(root, branch) and git_ref_exists(root, base_ref):
                return base_ref

    if git_ref_exists(root, "origin/main"):
        return "origin/main"
    if git_fetch_origin_branch(root, "main") and git_ref_exists(root, "origin/main"):
        return "origin/main"
    if git_ref_exists(root, "main"):
        return "main"
    return None


def parse_name_status(line: str) -> tuple[str, str] | None:
    parts = line.split("\t")
    if len(parts) < 2:
        return None
    return parts[0], parts[-1]


def git_diff_paths(root: Path, base_ref: str, head_ref: str = "HEAD") -> list[tuple[str, str]]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-status", "--find-renames", f"{base_ref}...{head_ref}"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [parsed for line in result.stdout.splitlines() if (parsed := parse_name_status(line)) is not None]


def git_name_status(root: Path, *args: str) -> list[tuple[str, str]]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-status", "--find-renames", *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [parsed for line in result.stdout.splitlines() if (parsed := parse_name_status(line)) is not None]


def git_untracked_paths(root: Path) -> list[tuple[str, str]]:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [("A", path) for path in result.stdout.splitlines() if path]


def git_change_paths(root: Path, errors: list[str]) -> list[tuple[str, str]]:
    base_ref = default_base_ref(root)
    if not base_ref:
        errors.append("Unable to resolve git base ref for Phase 11 diff checks.")
        return []
    paths: dict[str, str] = {}
    for status, path in git_diff_paths(root, base_ref):
        paths[path] = status
    for status, path in git_name_status(root):
        paths[path] = status
    for status, path in git_name_status(root, "--cached"):
        paths[path] = status
    for status, path in git_untracked_paths(root):
        paths.setdefault(path, status)
    return [(status, path) for path, status in paths.items()]


def classify_change_paths(statuses: list[tuple[str, str]]) -> tuple[list[str], list[str], list[str]]:
    deleted: list[str] = []
    renamed_or_copied: list[str] = []
    existing_touched: list[str] = []
    for status, path in statuses:
        if status.startswith("A"):
            continue
        if status.startswith("D"):
            deleted.append(path)
            continue
        if status.startswith(("R", "C")):
            renamed_or_copied.append(path)
            continue
        existing_touched.append(path)
    return deleted, renamed_or_copied, existing_touched


def collect_json_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel_dir in PHASE_11_JSON_SCAN_DIRS:
        directory = root / rel_dir
        if directory.is_dir():
            paths.extend(sorted(directory.rglob("*.json")))
    return paths


def object_property(schema: dict[str, Any], property_name: str) -> dict[str, Any]:
    value = schema.get("properties", {}).get(property_name, {})
    return value if isinstance(value, dict) else {}


def enum_values(schema: dict[str, Any], property_name: str) -> set[str]:
    prop = object_property(schema, property_name)
    raw_enum = prop.get("enum")
    if not isinstance(raw_enum, list):
        return set()
    return {item for item in raw_enum if isinstance(item, str)}


def property_schema(schema: dict[str, Any], schema_label: str, property_name: str, errors: list[str]) -> dict[str, Any]:
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        errors.append(f"{schema_label}.properties must be an object.")
        return {}
    prop = properties.get(property_name)
    if not isinstance(prop, dict):
        errors.append(f"{schema_label}.{property_name} must be an object schema.")
        return {}
    return prop


def object_field(value: dict[str, Any], field_name: str, label: str, errors: list[str]) -> dict[str, Any]:
    field = value.get(field_name)
    if not isinstance(field, dict):
        errors.append(f"{label}.{field_name} must be an object.")
        return {}
    return field


def enum_list(value: dict[str, Any], field_name: str, label: str, errors: list[str]) -> set[str]:
    raw_enum = value.get(field_name)
    if not isinstance(raw_enum, list):
        errors.append(f"{label}.{field_name} must be an enum list.")
        return set()
    return {item for item in raw_enum if isinstance(item, str)}


def required_fields(defs: dict, record_name: str, errors: list[str]) -> set[str]:
    fields = defs.get(record_name, {}).get("required")
    if not isinstance(fields, list):
        errors.append(f"{record_name} schema missing required field list.")
        return set()
    return set(fields)


def check_required_files(root: Path, contract: dict, errors: list[str]) -> None:
    for path_name in contract.get("required_files", []):
        require((root / path_name).is_file(), f"Missing required file: {path_name}", errors)


def check_schema(root: Path, contract: dict, errors: list[str]) -> None:
    schema_path = root / "data" / "schemas" / "worldstate_location_mutation_schema.json"
    schema = load_json_checked(root, schema_path, errors)
    if schema is None:
        return

    defs = schema.get("$defs", {})
    for record_name in contract.get("required_schema_records", []):
        require(record_name in defs, f"Missing schema record: {record_name}", errors)

    delta_required = required_fields(defs, "WorldstateDeltaPacket", errors)
    for field in contract.get("required_worldstate_delta_fields", []):
        require(field in delta_required, f"WorldstateDeltaPacket missing required field: {field}", errors)
    delta_props = defs.get("WorldstateDeltaPacket", {}).get("properties", {})
    require(
        delta_props.get("affected_location_refs", {}).get("$ref") == "#/$defs/NonEmptyStringRefList",
        "WorldstateDeltaPacket.affected_location_refs must use NonEmptyStringRefList.",
        errors,
    )
    require(
        defs.get("NonEmptyStringRefList", {}).get("minItems") == 1,
        "NonEmptyStringRefList must require at least one item.",
        errors,
    )

    location_delta_required = required_fields(defs, "LocationMutationDelta", errors)
    for field in contract.get("required_location_delta_fields", []):
        require(field in location_delta_required, f"LocationMutationDelta missing required field: {field}", errors)

    boundary_props = defs.get("AuthorityBoundary", {}).get("properties", {})
    expected_boundary = {
        "can_influence_generation_context": True,
        "may_mutate_ash_math": False,
        "may_rewrite_shared_world_truth": False,
        "may_mutate_base_world_ontology": False,
        "host_adapter_may_author": False,
    }
    for field, expected in expected_boundary.items():
        require(field in boundary_props, f"AuthorityBoundary missing property: {field}", errors)
        require(
            boundary_props.get(field, {}).get("const") is expected,
            f"AuthorityBoundary must set {field} to {str(expected).lower()}.",
            errors,
        )


def check_markers(root: Path, contract: dict, errors: list[str]) -> None:
    paths = [
        "data/schemas/worldstate_location_mutation_schema.json",
        "data/schemas/worldstate_delta_packet_schema.json",
        "core/narrative_engine/worldstate_location_mutation_rules.yaml",
        "core/narrative_engine/worldstate_delta_rules.yaml",
        "docs/architecture/worldstate_location_mutation_v1.md",
        "data/schemas/ywe_generation_context_packet_schema.json",
        "data/schemas/ash_generation_packet_schema.json",
        "data/schemas/branch_generation_context_schema.json",
        "data/schemas/player_runtime_state_schema.json",
        "data/schemas/leaf_branch_reality_state_schema.json",
    ]
    text = "\n".join(read_text(root / path_name) for path_name in paths if (root / path_name).is_file())
    for marker in contract.get("required_markers", []):
        require(marker in text, f"Missing required marker: {marker}", errors)


def check_packet_spine(root: Path, errors: list[str]) -> None:
    packet_schema = load_json_checked(root, root / "data" / "schemas" / "ash_generation_packet_schema.json", errors)
    if packet_schema is not None:
        records = packet_schema.get("records", {})
        for record_name in (
            "WorldstateDeltaPacket",
            "LocationMutationState",
            "LocationMutationDelta",
            "WorldstateMutationCommit",
            "DiagnosticNoOp",
            "FutureGenerationBiasUpdate",
        ):
            require(record_name in records, f"ASH packet schema missing {record_name} record.", errors)

    context_schema = load_json_checked(
        root,
        root / "data" / "schemas" / "ywe_generation_context_packet_schema.json",
        errors,
    )
    if context_schema is not None:
        require(
            "worldstate_delta_refs" in context_schema.get("required", []),
            "YWEGenerationContextPacket must require worldstate_delta_refs.",
            errors,
        )
        optional_context = context_schema.get("properties", {}).get("optional_context", {}).get("properties", {})
        for field in ("location_state_ref", "location_mutation_refs", "worldstate_mutation_commit_refs"):
            require(field in optional_context, f"YWEGenerationContextPacket optional_context missing {field}.", errors)

    branch_context = load_json_checked(
        root,
        root / "data" / "schemas" / "branch_generation_context_schema.json",
        errors,
    )
    if branch_context is not None:
        location_context_fields = branch_context.get("location_context_fields", [])
        for field in ("location_state_ref", "location_mutation_refs"):
            require(field in location_context_fields, f"BranchGenerationContext missing {field}.", errors)

    player_schema = load_json_checked(root, root / "data" / "schemas" / "player_runtime_state_schema.json", errors)
    if player_schema is not None:
        runtime_required = player_schema.get("$defs", {}).get("PlayerRuntimeState", {}).get("required", [])
        if runtime_required:
            for field in ("active_worldstate_delta_refs", "future_generation_bias_refs"):
                require(field in runtime_required, f"PlayerRuntimeState missing required field: {field}", errors)
        else:
            top_required = player_schema.get("required", [])
            world_links = player_schema.get("properties", {}).get("world_links", {}).get("properties", {})
            require("world_links" in top_required, "PlayerRuntimeState must require world_links.", errors)
            for field in ("worldstate_delta_refs", "future_generation_bias_refs"):
                require(field in world_links, f"PlayerRuntimeState.world_links missing property: {field}", errors)


def check_examples(root: Path, errors: list[str]) -> None:
    examples_dir = root / "examples" / "worldstate_location_mutation"
    if not examples_dir.is_dir():
        errors.append("Missing examples/worldstate_location_mutation.")
        return

    schema_rel = "data/schemas/worldstate_location_mutation_schema.json"
    if any(schema_rel in error for error in errors):
        return

    schema = load_json_checked(root, root / schema_rel, errors)
    if schema is None:
        return

    defs = schema.get("$defs", {})
    required_by_record = {
        name: required_fields(defs, name, errors)
        for name in (
            "WorldstateDeltaPacket",
            "LocationMutationState",
            "LocationMutationDelta",
            "WorldstateMutationCommit",
            "DiagnosticNoOp",
        )
    }
    for path in sorted(examples_dir.glob("*.json")):
        data = load_json_checked(root, path, errors)
        if data is None:
            continue
        record_type = data.get("record_type")
        if record_type not in required_by_record:
            errors.append(
                f"{path.relative_to(root).as_posix()} has unrecognized record_type: {record_type!r}"
            )
            continue
        missing = required_by_record[record_type] - set(data.keys())
        for field in sorted(missing):
            errors.append(f"{path.relative_to(root).as_posix()} missing required field: {field}")


def check_forbidden_claims(root: Path, contract: dict, errors: list[str]) -> None:
    scan_paths = [
        "data/schemas/worldstate_location_mutation_schema.json",
        "core/narrative_engine/worldstate_location_mutation_rules.yaml",
        "core/narrative_engine/worldstate_delta_rules.yaml",
        "docs/architecture/worldstate_location_mutation_v1.md",
        "examples/worldstate_location_mutation/worldstate_delta_ravenfall_gate_oath_revealed.example.json",
        "examples/worldstate_location_mutation/location_mutation_delta_ravenfall_gate_oath_revealed.example.json",
        "examples/worldstate_location_mutation/location_mutation_state_ravenfall_gate_after.example.json",
        "examples/worldstate_location_mutation/worldstate_mutation_commit_ravenfall_gate.example.json",
    ]
    combined = "\n".join(
        read_text(root / path_name)
        for path_name in scan_paths
        if (root / path_name).is_file()
    ).lower()
    for claim in contract.get("forbidden_current_truth_claims", []):
        require(claim.lower() not in combined, f"Forbidden current-truth claim found: {claim}", errors)


def check_phase_10_prerequisite(root: Path, errors: list[str]) -> None:
    contract = load_json_checked(root, root / PHASE_10_REQUIRED_ARTIFACTS, errors)
    if contract is not None:
        for section in ("required_markdown", "required_json"):
            for path_name in contract.get(section, []):
                require((root / path_name).is_file(), f"Missing Phase 10 prerequisite artifact: {path_name}", errors)

    normalized_text = "\n".join(
        read_text(root / path_name)
        for path_name in PHASE_10_SEMANTIC_TARGETS
        if (root / path_name).is_file()
    ).lower()
    for accepted_term_groups, message in PHASE_10_SEMANTIC_REQUIREMENTS:
        require(
            any(all(term in normalized_text for term in group) for group in accepted_term_groups),
            message,
            errors,
        )


def check_phase_11_required_artifacts(root: Path, errors: list[str]) -> None:
    contract = load_json_checked(root, root / PHASE_11_REQUIRED_ARTIFACTS, errors)
    if contract is not None:
        for section in ("required_markdown", "required_json"):
            for path_name in contract.get(section, []):
                require((root / path_name).is_file(), f"Missing Phase 11 required artifact: {path_name}", errors)

    for path_name in PHASE_11_EXTRA_REQUIRED_FILES + PHASE_11_CHECK_SPECS:
        require((root / path_name).is_file(), f"Missing Phase 11 check or support artifact: {path_name}", errors)


def check_phase_11_json_integrity(root: Path, errors: list[str]) -> None:
    for path in collect_json_files(root):
        load_json_checked(root, path, errors)


def check_phase_11_schema_contracts(root: Path, errors: list[str]) -> None:
    worldstate_schema = load_json_checked(root, root / "data/schemas/worldstate_delta_packet_schema.json", errors)
    if isinstance(worldstate_schema, dict):
        required = set(worldstate_schema.get("required", []))
        for field in ("truth_scope", "consequence_classes", "provenance", "validation"):
            require(field in required, f"WorldstateDeltaPacket schema must require {field}.", errors)
        require(
            enum_values(worldstate_schema, "truth_scope") == ALLOWED_TRUTH_SCOPES,
            "WorldstateDeltaPacket truth_scope enum must match Phase 11 allowed scopes.",
            errors,
        )
        classes_prop = property_schema(worldstate_schema, "WorldstateDeltaPacket", "consequence_classes", errors)
        classes_items = object_field(classes_prop, "items", "WorldstateDeltaPacket.consequence_classes", errors)
        class_enum = enum_list(classes_items, "enum", "WorldstateDeltaPacket.consequence_classes.items", errors)
        require(
            class_enum == ALLOWED_CONSEQUENCE_CLASSES,
            "WorldstateDeltaPacket consequence_classes enum must match Phase 11 allowed classes.",
            errors,
        )
        validation = property_schema(worldstate_schema, "WorldstateDeltaPacket", "validation", errors)
        validation_props = object_field(validation, "properties", "WorldstateDeltaPacket.validation", errors)
        require(
            "requires_delta_or_noop" in validation_props,
            "WorldstateDeltaPacket validation must include requires_delta_or_noop.",
            errors,
        )

    truth_scope_schema = load_json_checked(root, root / "data/schemas/truth_scope_schema.json", errors)
    if isinstance(truth_scope_schema, dict):
        allowed_prop = property_schema(truth_scope_schema, "TruthScope", "allowed_truth_scopes", errors)
        allowed_items = object_field(allowed_prop, "items", "TruthScope.allowed_truth_scopes", errors)
        allowed = enum_list(allowed_items, "enum", "TruthScope.allowed_truth_scopes.items", errors)
        require(set(allowed) == ALLOWED_TRUTH_SCOPES, "TruthScope schema must enumerate all Phase 11 truth scopes.", errors)

    consequence_schema = load_json_checked(root, root / "data/schemas/consequence_classification_schema.json", errors)
    if isinstance(consequence_schema, dict):
        allowed_prop = property_schema(
            consequence_schema,
            "ConsequenceClassification",
            "allowed_consequence_classes",
            errors,
        )
        allowed_items = object_field(
            allowed_prop,
            "items",
            "ConsequenceClassification.allowed_consequence_classes",
            errors,
        )
        allowed = enum_list(
            allowed_items,
            "enum",
            "ConsequenceClassification.allowed_consequence_classes.items",
            errors,
        )
        require(
            set(allowed) == ALLOWED_CONSEQUENCE_CLASSES,
            "ConsequenceClassification schema must enumerate all Phase 11 consequence classes.",
            errors,
        )

    future_bias_schema = load_json_checked(root, root / "data/schemas/future_generation_bias_update_schema.json", errors)
    if isinstance(future_bias_schema, dict):
        validation = property_schema(future_bias_schema, "FutureGenerationBiasUpdate", "validation", errors)
        validation_props = object_field(validation, "properties", "FutureGenerationBiasUpdate.validation", errors)
        does_not_materialize_content = object_field(
            validation_props,
            "does_not_materialize_content",
            "FutureGenerationBiasUpdate.validation.properties",
            errors,
        )
        require(
            does_not_materialize_content.get("const") is True,
            "FutureGenerationBiasUpdate must require does_not_materialize_content.",
            errors,
        )


def check_phase_11_contract_terms(root: Path, errors: list[str]) -> None:
    text = "\n".join(read_text(root / path_name) for path_name in PHASE_11_SCAN_PATHS if (root / path_name).is_file())
    required_terms = [
        "Every meaningful consequence must produce either",
        "WorldstateDeltaPacket",
        "DiagnosticNoOp",
        "locations are stateful",
        "mutate at runtime",
        "provenance",
        "Perception, myth, prophecy, and faction claim may alter interpretation",
        "They do not automatically rewrite shared world truth",
        "must not directly emit quests",
        "Branch overlays",
        "must not claim to rewrite base ontology",
    ]
    lower_text = text.lower()
    for term in required_terms:
        require(term.lower() in lower_text, f"Missing Phase 11 contract term: {term}", errors)


def check_phase_11_examples(root: Path, errors: list[str]) -> None:
    example_root = root / PHASE_11_EXAMPLE_ROOT
    require(example_root.is_dir(), f"Missing Phase 11 example directory: {PHASE_11_EXAMPLE_ROOT}", errors)

    ravenfall_contract = load_json_checked(root, root / PHASE_11_RAVENFALL_EXAMPLES, errors)
    if isinstance(ravenfall_contract, dict):
        ravenfall_dir = example_root / "ravenfall_gate"
        for filename in ravenfall_contract.get("required_examples", []):
            require((ravenfall_dir / filename).is_file(), f"Missing Ravenfall Gate Phase 11 example: {filename}", errors)

    for path in sorted(example_root.rglob("*.json")):
        data = load_json_checked(root, path, errors)
        if not isinstance(data, dict):
            continue
        path_name = relative_name(root, path)
        schema_id = data.get("schema_id")
        if schema_id == "ywe.worldstate_delta_packet.v1":
            require(data.get("truth_scope") in ALLOWED_TRUTH_SCOPES, f"{path_name} has invalid truth_scope.", errors)
            classes = data.get("consequence_classes")
            require(isinstance(classes, list) and bool(classes), f"{path_name} must include consequence_classes.", errors)
            if isinstance(classes, list):
                invalid = [item for item in classes if item not in ALLOWED_CONSEQUENCE_CLASSES]
                require(not invalid, f"{path_name} has invalid consequence_classes: {invalid}", errors)
            validation = data.get("validation", {})
            require(
                isinstance(validation, dict) and validation.get("requires_delta_or_noop") is True,
                f"{path_name} must assert requires_delta_or_noop.",
                errors,
            )
            require(
                isinstance(validation, dict) and validation.get("passes_truth_scope_guardrail") is True,
                f"{path_name} must assert passes_truth_scope_guardrail.",
                errors,
            )
        elif schema_id == "ywe.diagnostic_noop.v1":
            evaluation = data.get("evaluation", {})
            require(
                isinstance(evaluation, dict) and evaluation.get("truth_scope") in ALLOWED_TRUTH_SCOPES,
                f"{path_name} DiagnosticNoOp must carry a valid truth_scope.",
                errors,
            )
        elif schema_id == "ywe.location_branch_overlay.v1":
            validation = data.get("validation", {})
            require(data.get("truth_scope") == "leaf_branch_truth", f"{path_name} overlay must use leaf_branch_truth.", errors)
            for field in (
                "does_not_rewrite_base_ontology",
                "does_not_claim_shared_truth_without_delta",
                "is_runtime_generated_not_pregenerated_tree",
            ):
                require(
                    isinstance(validation, dict) and validation.get(field) is True,
                    f"{path_name} overlay validation must assert {field}.",
                    errors,
                )
        elif schema_id == "ywe.future_generation_bias_update.v1":
            validation = data.get("validation", {})
            require(
                isinstance(validation, dict) and validation.get("does_not_materialize_content") is True,
                f"{path_name} must not materialize content.",
                errors,
            )
        elif schema_id == "ywe.location_mutation_rule.v1":
            outputs = data.get("outputs", {})
            require(
                isinstance(outputs, dict)
                and (outputs.get("worldstate_delta_packet") is True or outputs.get("diagnostic_noop") is True),
                f"{path_name} mutation rule must output WorldstateDeltaPacket or DiagnosticNoOp.",
                errors,
            )


def check_phase_11_forbidden_language(root: Path, errors: list[str]) -> None:
    contract = load_json_checked(root, root / PHASE_11_FORBIDDEN_LANGUAGE, errors)
    if not isinstance(contract, dict):
        return

    scan_files = [root / path_name for path_name in PHASE_11_SCAN_PATHS]
    example_root = root / PHASE_11_EXAMPLE_ROOT
    if example_root.is_dir():
        scan_files.extend(sorted(example_root.rglob("*.json")))

    for item in contract.get("patterns", []):
        if not isinstance(item, dict):
            continue
        pattern = item.get("pattern")
        if not isinstance(pattern, str):
            continue
        lower_pattern = pattern.lower()
        for path in scan_files:
            if not path.is_file():
                continue
            lines = read_text(path).splitlines()
            for index, line in enumerate(lines):
                if lower_pattern not in line.lower():
                    continue
                context = "\n".join(lines[max(0, index - 6) : index + 2]).lower()
                is_rejection_context = any(
                    marker in context
                    for marker in (
                        "forbidden",
                        "forbid",
                        "reject",
                        "must not",
                        "do not",
                        "does not",
                        "fail if",
                        "never",
                    )
                )
                require(
                    is_rejection_context,
                    f"Forbidden Phase 11 language found outside rejection context: {pattern}",
                    errors,
                )


def check_phase_11_non_destructive_diff(root: Path, errors: list[str]) -> None:
    budget = load_json_checked(root, root / PHASE_11_NON_DESTRUCTIVE_BUDGET, errors)
    deleted, renamed_or_copied, existing_touched = classify_change_paths(git_change_paths(root, errors))
    limits = budget.get("limits", {}) if isinstance(budget, dict) else {}
    max_deleted = int(limits.get("max_existing_file_deletions", 0))
    max_renamed = int(limits.get("max_directory_renames", 0))
    max_touched = int(limits.get("max_existing_files_touched_without_review", 25))
    fail_on_protected = limits.get("fail_on_deleted_protected_paths", True)
    if fail_on_protected:
        protected_deletions = [
            path
            for path in deleted
            if path.startswith(("docs/", "data/", "conformance/", "examples/", "scripts/", ".github/"))
        ]
        require(not protected_deletions, f"Phase 11 deleted protected files: {protected_deletions}", errors)
    require(len(deleted) <= max_deleted, f"Phase 11 file deletions exceed budget {max_deleted}: {deleted}", errors)
    require(len(renamed_or_copied) <= max_renamed, f"Phase 11 renamed or copied paths exceed budget {max_renamed}: {renamed_or_copied}", errors)
    require(len(existing_touched) <= max_touched, f"Phase 11 existing files touched exceed budget {max_touched}: {len(existing_touched)}", errors)

    if isinstance(budget, dict):
        automatic_fail = set(budget.get("automatic_fail", []))
        require("platform_specific_runtime_implementation" in automatic_fail, "Phase 11 budget must forbid platform code.", errors)


def check_phase_11_package(root: Path, errors: list[str]) -> None:
    check_phase_10_prerequisite(root, errors)
    check_phase_11_required_artifacts(root, errors)
    check_phase_11_json_integrity(root, errors)
    check_phase_11_schema_contracts(root, errors)
    check_phase_11_contract_terms(root, errors)
    check_phase_11_examples(root, errors)
    check_phase_11_forbidden_language(root, errors)
    check_phase_11_non_destructive_diff(root, errors)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    contract_path = root / DEFAULT_CONTRACT
    if not contract_path.is_file():
        print(f"Worldstate Location Mutation check failed: missing {DEFAULT_CONTRACT}")
        return 1

    try:
        contract = load_json(contract_path)
    except json.JSONDecodeError as exc:
        print(
            "Worldstate Location Mutation check failed: "
            f"invalid {DEFAULT_CONTRACT} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
        return 1
    except OSError as exc:
        print(f"Worldstate Location Mutation check failed: unable to read {DEFAULT_CONTRACT}: {exc}")
        return 1

    errors: list[str] = []
    check_required_files(root, contract, errors)
    check_schema(root, contract, errors)
    check_markers(root, contract, errors)
    check_packet_spine(root, errors)
    check_examples(root, errors)
    check_forbidden_claims(root, contract, errors)
    check_phase_11_package(root, errors)

    if errors:
        print("Worldstate Location Mutation check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Worldstate Location Mutation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
