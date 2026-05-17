#!/usr/bin/env python3
"""Validate Phase 12 quest, NPC, and lore generation contract coverage."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"
DEFAULT_CONTRACT = "data/validation/quest_npc_lore_generation_gate_contract.json"


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
    schema_path = root / "data" / "schemas" / "quest_npc_lore_generation_schema.json"
    schema = load_json_checked(root, schema_path, errors)
    if schema is None:
        return

    defs = schema.get("$defs", {})
    for record_name in contract.get("required_schema_records", []):
        require(record_name in defs, f"Missing schema record: {record_name}", errors)

    field_contracts = {
        "QuestChainManifest": contract.get("required_quest_manifest_fields", []),
        "QuestResolutionPayload": contract.get("required_quest_resolution_fields", []),
        "NPCManifest": contract.get("required_npc_manifest_fields", []),
        "CodexRecord": contract.get("required_codex_record_fields", []),
        "MythRecord": contract.get("required_myth_record_fields", []),
    }
    for record_name, fields in field_contracts.items():
        required = required_fields(defs, record_name, errors)
        for field in fields:
            require(field in required, f"{record_name} missing required field: {field}", errors)

    completion_props = defs.get("CompletionModeSet", {}).get("properties", {})
    require(
        completion_props.get("minimum_mode_count", {}).get("minimum") == 2,
        "CompletionModeSet.minimum_mode_count must require minimum 2.",
        errors,
    )
    require(
        completion_props.get("completion_modes", {}).get("minItems") == 2,
        "CompletionModeSet.completion_modes must require at least two modes.",
        errors,
    )

    truth_props = defs.get("TruthFunction", {}).get("properties", {})
    require(
        truth_props.get("factual_world_truth_rewrite_allowed", {}).get("const") is False,
        "TruthFunction must forbid factual world truth rewrite.",
        errors,
    )
    myth_props = defs.get("MythRecord", {}).get("properties", {})
    require(
        myth_props.get("factual_world_truth_rewrite_allowed", {}).get("const") is False,
        "MythRecord must forbid factual world truth rewrite.",
        errors,
    )

    boundary_props = defs.get("AuthorityBoundary", {}).get("properties", {})
    expected_boundary = {
        "can_influence_generation_context": True,
        "may_mutate_ash_math": False,
        "may_rewrite_shared_world_truth": False,
        "may_mutate_base_world_ontology": False,
        "host_adapter_may_author": False,
        "may_create_independent_random_content": False,
        "quest_must_offer_multiple_completion_modes": True,
        "npc_claims_are_interpretive": True,
        "lore_may_overwrite_locked_canon": False,
        "myth_may_rewrite_factual_world_truth": False,
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
        "data/schemas/quest_npc_lore_generation_schema.json",
        "core/narrative_engine/quest_npc_lore_generation_rules.yaml",
        "core/narrative_engine/npc_synthesis_rules.yaml",
        "core/narrative_engine/codex_lore_generation_rules.yaml",
        "modules/quest_engine/quest_chain_templates.yaml",
        "data/schemas/myth_record_schema_expansion.json",
        "docs/architecture/quest_npc_lore_generation_v1.md",
        "data/schemas/ywe_generation_context_packet_schema.json",
        "data/schemas/ywe_interpretation_packet_schema.json",
        "data/schemas/ash_generation_packet_schema.json",
        "core/narrative_engine/ash_runtime_generation_flow.yaml",
        "data/quest_archetypes/quest_chain_manifest_schema.json",
        "data/schemas/npc_manifest_schema.json",
        "data/schemas/codex_lore_record_schema.json",
    ]
    text = "\n".join(read_text(root / path_name) for path_name in paths if (root / path_name).is_file())
    for marker in contract.get("required_markers", []):
        require(marker in text, f"Missing required marker: {marker}", errors)


def check_packet_spine(root: Path, errors: list[str]) -> None:
    packet_schema = load_json_checked(root, root / "data" / "schemas" / "ash_generation_packet_schema.json", errors)
    if packet_schema is not None:
        records = packet_schema.get("records", {})
        for record_name in (
            "QuestGenerationRequest",
            "QuestChainManifest",
            "QuestResolutionPayload",
            "NPCManifest",
            "NPCMemoryDelta",
            "CodexRecord",
            "MythRecord",
            "SocialDistributionDelta",
        ):
            require(record_name in records, f"ASH packet schema missing {record_name} record.", errors)

    context_schema = load_json_checked(
        root,
        root / "data" / "schemas" / "ywe_generation_context_packet_schema.json",
        errors,
    )
    if context_schema is not None:
        trigger_enum = context_schema.get("properties", {}).get("trigger_kind", {}).get("enum", [])
        for trigger in ("quest_generation", "npc_synthesis", "lore_generation", "future_generation_bias"):
            require(trigger in trigger_enum, f"YWEGenerationContextPacket trigger_kind missing {trigger}.", errors)
        optional_context = context_schema.get("properties", {}).get("optional_context", {}).get("properties", {})
        for field in (
            "future_generation_bias_update_refs",
            "quest_chain_manifest_refs",
            "quest_resolution_payload_refs",
            "npc_manifest_refs",
            "npc_memory_delta_refs",
            "codex_record_refs",
            "myth_record_refs",
            "social_distribution_delta_refs",
        ):
            require(field in optional_context, f"YWEGenerationContextPacket optional_context missing {field}.", errors)

    interpretation_schema = load_json_checked(
        root,
        root / "data" / "schemas" / "ywe_interpretation_packet_schema.json",
        errors,
    )
    if interpretation_schema is not None:
        policies = interpretation_schema.get("properties", {}).get("worldstate_delta_policy", {}).get("enum", [])
        for policy in (
            "quest_resolution_delta",
            "npc_memory_delta",
            "lore_visibility_delta",
            "myth_distribution_delta",
            "social_distribution_delta",
        ):
            require(policy in policies, f"YWEInterpretationPacket worldstate_delta_policy missing {policy}.", errors)


def check_promoted_placeholders(root: Path, errors: list[str]) -> None:
    promoted_paths = [
        "modules/quest_engine/quest_chain_templates.yaml",
        "core/narrative_engine/npc_synthesis_rules.yaml",
        "data/schemas/myth_record_schema_expansion.json",
    ]
    for path_name in promoted_paths:
        path = root / path_name
        if not path.is_file():
            continue
        text = read_text(path)
        require("placeholder_awaiting_finalized_content" not in text, f"{path_name} still declares placeholder status.", errors)
        require("active_contract" in text, f"{path_name} must declare active_contract status.", errors)


def check_examples(root: Path, errors: list[str]) -> None:
    examples_dir = root / "examples" / "quest_npc_lore_generation"
    if not examples_dir.is_dir():
        errors.append("Missing examples/quest_npc_lore_generation.")
        return

    schema = load_json_checked(
        root,
        root / "data" / "schemas" / "quest_npc_lore_generation_schema.json",
        errors,
    )
    if schema is None:
        return

    defs = schema.get("$defs", {})
    expected_record_types = {
        "QuestGenerationRequest",
        "QuestChainManifest",
        "QuestResolutionPayload",
        "NPCManifest",
        "NPCMemoryDelta",
        "CodexRecord",
        "MythSeedCandidate",
        "MythRecord",
        "SocialDistributionDelta",
    }
    required_by_record = {
        name: required_fields(defs, name, errors)
        for name in expected_record_types
    }
    seen_record_types: set[str] = set()

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
        seen_record_types.add(record_type)
        missing = required_by_record[record_type] - set(data.keys())
        for field in sorted(missing):
            errors.append(f"{path.relative_to(root).as_posix()} missing required field: {field}")

        boundary = data.get("authority_boundary")
        require(isinstance(boundary, dict), f"{path.relative_to(root).as_posix()} missing authority_boundary object.", errors)
        if isinstance(boundary, dict):
            require(boundary.get("may_mutate_ash_math") is False, f"{path.relative_to(root).as_posix()} may_mutate_ash_math must be false.", errors)
            require(boundary.get("host_adapter_may_author") is False, f"{path.relative_to(root).as_posix()} host_adapter_may_author must be false.", errors)
            require(boundary.get("may_create_independent_random_content") is False, f"{path.relative_to(root).as_posix()} may_create_independent_random_content must be false.", errors)

        if record_type == "QuestChainManifest":
            mode_set = data.get("completion_mode_set", {})
            mode_count = mode_set.get("minimum_mode_count")
            modes = mode_set.get("completion_modes", [])
            require(mode_count is not None and mode_count >= 2, f"{path.relative_to(root).as_posix()} minimum_mode_count must be at least 2.", errors)
            require(isinstance(modes, list) and len(modes) >= 2, f"{path.relative_to(root).as_posix()} must include at least two completion modes.", errors)

        if record_type == "MythRecord":
            require(data.get("factual_world_truth_rewrite_allowed") is False, f"{path.relative_to(root).as_posix()} must forbid factual world truth rewrite.", errors)

    missing_examples = expected_record_types - seen_record_types
    for record_type in sorted(missing_examples):
        errors.append(f"Missing example record_type: {record_type}")


def check_forbidden_claims(root: Path, contract: dict, errors: list[str]) -> None:
    scan_paths = [
        "data/schemas/quest_npc_lore_generation_schema.json",
        "core/narrative_engine/quest_npc_lore_generation_rules.yaml",
        "core/narrative_engine/npc_synthesis_rules.yaml",
        "core/narrative_engine/codex_lore_generation_rules.yaml",
        "modules/quest_engine/quest_chain_templates.yaml",
        "data/schemas/myth_record_schema_expansion.json",
        "docs/architecture/quest_npc_lore_generation_v1.md",
    ]
    combined = "\n".join(
        read_text(root / path_name)
        for path_name in scan_paths
        if (root / path_name).is_file()
    ).lower()
    for claim in contract.get("forbidden_current_truth_claims", []):
        require(claim.lower() not in combined, f"Forbidden current-truth claim found: {claim}", errors)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    contract_path = root / DEFAULT_CONTRACT
    if not contract_path.is_file():
        print(f"Quest NPC Lore Generation check failed: missing {DEFAULT_CONTRACT}")
        return 1

    try:
        contract = load_json(contract_path)
    except json.JSONDecodeError as exc:
        print(
            "Quest NPC Lore Generation check failed: "
            f"invalid {DEFAULT_CONTRACT} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
        return 1
    except OSError as exc:
        print(f"Quest NPC Lore Generation check failed: unable to read {DEFAULT_CONTRACT}: {exc}")
        return 1

    errors: list[str] = []
    check_required_files(root, contract, errors)
    check_schema(root, contract, errors)
    check_markers(root, contract, errors)
    check_packet_spine(root, errors)
    check_promoted_placeholders(root, errors)
    check_examples(root, errors)
    check_forbidden_claims(root, contract, errors)

    if errors:
        print("Quest NPC Lore Generation check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Quest NPC Lore Generation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
