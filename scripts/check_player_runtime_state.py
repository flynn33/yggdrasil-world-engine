#!/usr/bin/env python3
"""Validate Player Runtime State v1 contract coverage."""

from __future__ import annotations

import json
import sys
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"
DEFAULT_CONTRACT = "data/validation/player_runtime_state_gate_contract.json"


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


def check_required_files(root: Path, contract: dict, errors: list[str]) -> None:
    for path_name in contract.get("required_files", []):
        require((root / path_name).is_file(), f"Missing required file: {path_name}", errors)


def check_schema(root: Path, contract: dict, errors: list[str]) -> None:
    schema_path = root / "data" / "schemas" / "player_runtime_state_schema.json"
    schema = load_json_checked(root, schema_path, errors)
    if schema is None:
        return

    defs = schema.get("$defs", {})
    for record_name in contract.get("required_schema_records", []):
        require(record_name in defs, f"Missing schema record: {record_name}", errors)

    runtime_required = defs.get("PlayerRuntimeState", {}).get("required", [])
    for field in contract.get("required_runtime_state_fields", []):
        require(field in runtime_required, f"PlayerRuntimeState missing required field: {field}", errors)

    delta_required = defs.get("PlayerRuntimeStateDelta", {}).get("required", [])
    for field in contract.get("required_delta_fields", []):
        require(field in delta_required, f"PlayerRuntimeStateDelta missing required field: {field}", errors)

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
        "data/schemas/player_runtime_state_schema.json",
        "core/narrative_engine/player_runtime_state_rules.yaml",
        "docs/architecture/player_runtime_state_v1.md",
        "data/schemas/ywe_generation_context_packet_schema.json",
        "data/schemas/ash_generation_packet_schema.json",
        "data/schemas/branch_generation_context_schema.json",
        "data/schemas/leaf_branch_reality_state_schema.json",
    ]
    text = "\n".join(read_text(root / path_name) for path_name in paths if (root / path_name).is_file())
    for marker in contract.get("required_markers", []):
        require(marker in text, f"Missing required marker: {marker}", errors)


def check_packet_spine(root: Path, errors: list[str]) -> None:
    context_schema = load_json_checked(
        root,
        root / "data" / "schemas" / "ywe_generation_context_packet_schema.json",
        errors,
    )
    if context_schema is not None:
        require(
            "player_runtime_state_ref" in context_schema.get("required", []),
            "YWEGenerationContextPacket must require player_runtime_state_ref.",
            errors,
        )

    packet_schema = load_json_checked(
        root,
        root / "data" / "schemas" / "ash_generation_packet_schema.json",
        errors,
    )
    if packet_schema is not None:
        records = packet_schema.get("records", {})
        require("PlayerRuntimeState" in records, "ASH packet schema missing PlayerRuntimeState record.", errors)
        require("PlayerRuntimeStateDelta" in records, "ASH packet schema missing PlayerRuntimeStateDelta record.", errors)

    branch_context = load_json_checked(
        root,
        root / "data" / "schemas" / "branch_generation_context_schema.json",
        errors,
    )
    if branch_context is not None:
        player_context_fields = branch_context.get("player_context_fields", [])
        require(
            "player_runtime_state_ref" in player_context_fields,
            "BranchGenerationContext must include player_runtime_state_ref.",
            errors,
        )


def check_examples(root: Path, errors: list[str]) -> None:
    examples_dir = root / "examples" / "player_runtime_state"
    if not examples_dir.is_dir():
        errors.append("Missing examples/player_runtime_state.")
        return

    schema = load_json_checked(root, root / "data" / "schemas" / "player_runtime_state_schema.json", errors)
    if schema is None:
        return

    defs = schema.get("$defs", {})
    runtime_required = defs.get("PlayerRuntimeState", {}).get("required")
    delta_required = defs.get("PlayerRuntimeStateDelta", {}).get("required")
    if not isinstance(runtime_required, list):
        errors.append("PlayerRuntimeState schema missing required field list.")
        return
    if not isinstance(delta_required, list):
        errors.append("PlayerRuntimeStateDelta schema missing required field list.")
        return

    runtime_required_set = set(runtime_required)
    delta_required_set = set(delta_required)
    for path in sorted(examples_dir.glob("*.json")):
        data = load_json_checked(root, path, errors)
        if data is None:
            continue
        if data.get("record_type") == "PlayerRuntimeState":
            missing = runtime_required_set - set(data.keys())
        elif data.get("record_type") == "PlayerRuntimeStateDelta":
            missing = delta_required_set - set(data.keys())
        else:
            missing = {"record_type"}
        for field in sorted(missing):
            errors.append(f"{path.relative_to(root).as_posix()} missing required field: {field}")


def check_forbidden_claims(root: Path, contract: dict, errors: list[str]) -> None:
    scan_paths = [
        "data/schemas/player_runtime_state_schema.json",
        "core/narrative_engine/player_runtime_state_rules.yaml",
        "docs/architecture/player_runtime_state_v1.md",
        "examples/player_runtime_state/player_runtime_state_initial.example.json",
        "examples/player_runtime_state/player_runtime_state_delta_branch_event.example.json",
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
        print(f"Player Runtime State check failed: missing {DEFAULT_CONTRACT}")
        return 1

    try:
        contract = load_json(contract_path)
    except json.JSONDecodeError as exc:
        print(
            "Player Runtime State check failed: "
            f"invalid {DEFAULT_CONTRACT} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        )
        return 1
    except OSError as exc:
        print(f"Player Runtime State check failed: unable to read {DEFAULT_CONTRACT}: {exc}")
        return 1
    errors: list[str] = []

    check_required_files(root, contract, errors)
    check_schema(root, contract, errors)
    check_markers(root, contract, errors)
    check_packet_spine(root, errors)
    check_examples(root, errors)
    check_forbidden_claims(root, contract, errors)

    if errors:
        print("Player Runtime State check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Player Runtime State check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
