#!/usr/bin/env python3
"""Validate Phase 15 Quest Reward Resolver contract coverage."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

TEXT_ENCODING = "utf-8-sig"

PHASE_15_ACCEPTANCE_CONTRACT = "data/validation/phase_15_acceptance_contract.json"
PHASE_15_PREREQUISITE_GATE = "data/validation/phase_15_prerequisite_gate.json"
PHASE_15_REQUIRED_ARTIFACTS = "data/validation/phase_15_required_artifacts.json"
PHASE_15_FORBIDDEN_LANGUAGE = "data/validation/phase_15_forbidden_language_patterns.json"
PHASE_15_NON_DESTRUCTIVE_BUDGET = "data/validation/phase_15_non_destructive_change_budget.json"
PHASE_15_EXAMPLE_VALIDATION = "data/validation/ravenfall_gate_phase_15_example_validation.json"
PHASE_15_EXAMPLE_ROOT = "examples/quest_reward_resolver"

PHASE_14_PREREQ_FILES = [
    "docs/handoff/YWE_PHASE_14_ABILITY_POWER_ENGINE_COMPLETION_REPORT_2026-05-19.md",
    "docs/architecture/ability_power_engine_contract.md",
    "docs/architecture/ability_unlock_pressure_contract.md",
    "docs/architecture/ability_source_model_contract.md",
    "data/schemas/ability_state_schema.json",
    "data/schemas/ability_unlock_pressure_schema.json",
    "data/schemas/ability_source_ref_schema.json",
    "data/schemas/ability_state_update_packet_schema.json",
    "data/schemas/ability_consequence_packet_schema.json",
]

PHASE_15_VALIDATION_FILES = [
    PHASE_15_ACCEPTANCE_CONTRACT,
    PHASE_15_PREREQUISITE_GATE,
    PHASE_15_REQUIRED_ARTIFACTS,
    PHASE_15_FORBIDDEN_LANGUAGE,
    PHASE_15_NON_DESTRUCTIVE_BUDGET,
    PHASE_15_EXAMPLE_VALIDATION,
    "data/validation/phase_15_github_checks_matrix.json",
    "data/validation/quest_reward_ability_validation_rules.json",
    "data/validation/quest_reward_future_generation_bias_validation_rules.json",
    "data/validation/quest_reward_resolver_validation_rules.json",
    "data/validation/quest_reward_truth_scope_validation_rules.json",
    "data/validation/quest_reward_wolf_validation_rules.json",
    "data/validation/source_truth_guardrails_phase_15.json",
    "data/validation/package_payload_policy.json",
]

PHASE_15_CHECK_SPECS = [
    "data/validation/check_phase_14_acceptance_prereq.spec.json",
    "data/validation/check_required_phase_15_contracts.spec.json",
    "data/validation/check_phase_15_json_integrity.spec.json",
    "data/validation/check_quest_reward_resolution_packet_schema.spec.json",
    "data/validation/check_consequence_resolution_packet_schema.spec.json",
    "data/validation/check_no_random_reward_table_primary_model.spec.json",
    "data/validation/check_quest_reward_truth_scope.spec.json",
    "data/validation/check_quest_reward_delta_coverage.spec.json",
    "data/validation/check_wolf_reward_non_morality.spec.json",
    "data/validation/check_ability_reward_source_refs.spec.json",
    "data/validation/check_no_quest_completion_without_consequence.spec.json",
    "data/validation/check_ravenfall_gate_reward_examples.spec.json",
    "data/validation/check_non_destructive_diff_phase_15.spec.json",
    "data/validation/check_source_truth_phase_15.spec.json",
    "data/validation/check_no_wolf_death_reward_cost.spec.json",
    "data/validation/check_future_generation_bias_reward_refs.spec.json",
]

PHASE_15_SCHEMA_FILES = [
    "data/schemas/quest_reward_resolution_packet_schema.json",
    "data/schemas/consequence_resolution_packet_schema.json",
    "data/schemas/quest_completion_mode_schema.json",
    "data/schemas/quest_reward_input_context_schema.json",
    "data/schemas/quest_choice_outcome_schema.json",
    "data/schemas/reward_delta_bundle_schema.json",
    "data/schemas/player_state_reward_delta_schema.json",
    "data/schemas/branch_reward_delta_schema.json",
    "data/schemas/worldstate_reward_delta_schema.json",
    "data/schemas/location_reward_delta_schema.json",
    "data/schemas/wolf_reward_delta_schema.json",
    "data/schemas/ability_reward_delta_schema.json",
    "data/schemas/plane_attunement_reward_delta_schema.json",
    "data/schemas/lineage_reward_delta_schema.json",
    "data/schemas/perception_reward_delta_schema.json",
    "data/schemas/myth_seed_reward_delta_schema.json",
    "data/schemas/prophecy_pressure_reward_delta_schema.json",
    "data/schemas/faction_reward_delta_schema.json",
    "data/schemas/npc_relationship_reward_delta_schema.json",
    "data/schemas/artifact_eligibility_reward_delta_schema.json",
    "data/schemas/creature_eligibility_reward_delta_schema.json",
    "data/schemas/future_generation_bias_reward_delta_schema.json",
    "data/schemas/quest_reward_decoherence_event_schema.json",
    "data/schemas/quest_reward_risk_schema.json",
    "data/schemas/quest_reward_rule_schema.json",
    "data/schemas/quest_reward_resolver_ruleset_schema.json",
    "data/schemas/quest_reward_validation_result_schema.json",
    "data/schemas/quest_reward_manifest_handoff_schema.json",
    "data/schemas/quest_reward_diagnostic_noop_link_schema.json",
    "data/schemas/quest_reward_source_ref_schema.json",
    "data/schemas/quest_reward_resolver_trace_schema.json",
    "data/schemas/quest_reward_rejection_reason_schema.json",
    "data/schemas/quest_reward_resolution_summary_schema.json",
]

PHASE_15_SCAN_GLOBS = [
    "docs/architecture/quest_reward_*.md",
    "data/schemas/*reward*_schema.json",
    "data/schemas/consequence_resolution_packet_schema.json",
    "data/schemas/quest_completion_mode_schema.json",
    "data/schemas/quest_choice_outcome_schema.json",
    "data/validation/phase_15_*.json",
    "data/validation/quest_reward_*_validation_rules.json",
    "data/validation/check_*phase_15*.spec.json",
    "data/validation/check_*quest_reward*.spec.json",
    "data/validation/check_*reward*.spec.json",
    "examples/quest_reward_resolver/**/*.json",
]

REQUIRED_COMPLETION_MODES = {
    "reveal_oath",
    "conceal_oath",
    "bind_oath",
    "study_oath",
    "weaponize_oath",
}

REQUIRED_TRUTH_SCOPES = {
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

REQUIRED_DELTA_TYPES = {
    "player_state",
    "branch",
    "worldstate",
    "location",
    "wolf",
    "ability",
    "plane_attunement",
    "lineage",
    "perception",
    "myth_seed",
    "prophecy_pressure",
    "faction",
    "npc_relationship",
    "artifact_eligibility",
    "creature_eligibility",
    "future_generation_bias",
}

ALLOWED_FORBIDDEN_CONTEXT_TERMS = {
    "forbidden",
    "invalid",
    "reject",
    "rejected",
    "rejection",
    "failure_behavior",
    "failure_conditions",
    "fail if",
    "must not",
    "do not",
    "should not",
    "may not",
    "cannot",
    "not a morality",
    "not morality",
    "not moral",
    "not good",
    "not evil",
    "not death",
    "cannot be killed",
    "not topmost",
    "not the topmost",
    "decoherence",
    "temporarily",
}

DIRECT_NEGATION_PREFIXES = (
    "do not",
    "must not",
    "should not",
    "may not",
    "does not",
    "cannot",
    "can't",
    "not",
    "never",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding=TEXT_ENCODING)


def load_json(path: Path) -> Any:
    with path.open(encoding=TEXT_ENCODING) as handle:
        return json.load(handle)


def relative_name(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def load_json_checked(root: Path, path: Path, errors: list[str]) -> Any | None:
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
        errors.append("Unable to resolve git base ref for Phase 15 diff checks.")
        return []

    paths: dict[str, str] = {}
    for status, path in git_name_status(root, f"{base_ref}...HEAD"):
        paths[path] = status
    for status, path in git_name_status(root):
        paths[path] = status
    for status, path in git_name_status(root, "--cached"):
        paths[path] = status
    for status, path in git_untracked_paths(root):
        paths.setdefault(path, status)
    return [(status, path) for path, status in paths.items()]


def classify_change_paths(statuses: list[tuple[str, str]]) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    added: list[str] = []
    deleted: list[str] = []
    renamed: list[str] = []
    copied: list[str] = []
    existing_touched: list[str] = []
    for status, path in statuses:
        if status.startswith("A"):
            added.append(path)
            continue
        if status.startswith("D"):
            deleted.append(path)
            continue
        if status.startswith("R"):
            renamed.append(path)
            continue
        if status.startswith("C"):
            copied.append(path)
            continue
        existing_touched.append(path)
    return added, deleted, renamed, copied, existing_touched


def budget_limit(budget: dict[str, Any], *keys: str, default: int) -> int:
    limits = budget.get("limits")
    for key in keys:
        if isinstance(limits, dict) and key in limits:
            raw_value = limits[key]
            break
        if key in budget:
            raw_value = budget[key]
            break
    else:
        raw_value = default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def json_string_enum(schema: dict[str, Any], property_name: str) -> set[str]:
    value = schema.get("properties", {}).get(property_name, {}).get("enum", [])
    return {item for item in value if isinstance(item, str)} if isinstance(value, list) else set()


def required_fields(schema: dict[str, Any]) -> set[str]:
    fields = schema.get("required", [])
    return {field for field in fields if isinstance(field, str)} if isinstance(fields, list) else set()


def const_value(schema: dict[str, Any], property_name: str) -> Any:
    return schema.get("properties", {}).get(property_name, {}).get("const")


def phase_15_json_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for path_name in PHASE_15_VALIDATION_FILES + PHASE_15_CHECK_SPECS + PHASE_15_SCHEMA_FILES:
        paths.add(root / path_name)
    example_root = root / PHASE_15_EXAMPLE_ROOT
    if example_root.is_dir():
        paths.update(example_root.glob("*.json"))
    return sorted(paths)


def phase_15_scan_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in PHASE_15_SCAN_GLOBS:
        files.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(files)


def check_phase_14_prerequisite(root: Path, errors: list[str]) -> None:
    gate = load_json_checked(root, root / PHASE_15_PREREQUISITE_GATE, errors)
    if isinstance(gate, dict):
        requires = gate.get("requires", [])
        require(isinstance(requires, list), f"{PHASE_15_PREREQUISITE_GATE} requires must be a list.", errors)
        must_reject = gate.get("must_reject_if", [])
        require(isinstance(must_reject, list), f"{PHASE_15_PREREQUISITE_GATE} must_reject_if must be a list.", errors)

    for path_name in PHASE_14_PREREQ_FILES:
        require((root / path_name).is_file(), f"Missing Phase 15 prerequisite artifact: {path_name}", errors)

    ability_source = load_json_checked(root, root / "data/schemas/ability_source_ref_schema.json", errors)
    if isinstance(ability_source, dict):
        require("source_id" in required_fields(ability_source), "ability_source_ref_schema.json must still require source_id.", errors)
        require("source_kind" in required_fields(ability_source), "ability_source_ref_schema.json must still require source_kind.", errors)


def check_required_artifacts(root: Path, errors: list[str]) -> None:
    artifacts = load_json_checked(root, root / PHASE_15_REQUIRED_ARTIFACTS, errors)
    if not isinstance(artifacts, dict):
        return

    for file_name in artifacts.get("required_docs", []):
        require(isinstance(file_name, str), "Phase 15 required_docs entries must be strings.", errors)
        if isinstance(file_name, str):
            require((root / "docs" / "architecture" / file_name).is_file(), f"Missing Phase 15 architecture doc: {file_name}", errors)

    for file_name in artifacts.get("required_schemas", []):
        require(isinstance(file_name, str), "Phase 15 required_schemas entries must be strings.", errors)
        if isinstance(file_name, str):
            require((root / "data" / "schemas" / file_name).is_file(), f"Missing Phase 15 schema: {file_name}", errors)

    for file_name in artifacts.get("required_examples", []):
        require(isinstance(file_name, str), "Phase 15 required_examples entries must be strings.", errors)
        if isinstance(file_name, str):
            require((root / PHASE_15_EXAMPLE_ROOT / file_name).is_file(), f"Missing Phase 15 example: {file_name}", errors)

    for path_name in PHASE_15_VALIDATION_FILES + PHASE_15_CHECK_SPECS:
        require((root / path_name).is_file(), f"Missing Phase 15 validation or check artifact: {path_name}", errors)


def check_json_integrity(root: Path, errors: list[str]) -> None:
    for path in phase_15_json_files(root):
        load_json_checked(root, path, errors)


def check_schema_contracts(root: Path, errors: list[str]) -> None:
    resolution_path = "data/schemas/quest_reward_resolution_packet_schema.json"
    resolution = load_json_checked(root, root / resolution_path, errors)
    if isinstance(resolution, dict):
        required = required_fields(resolution)
        for field in ("packet_id", "schema_version", "quest_ref", "completion_mode", "resolution_status", "truth_scope", "provenance", "validation_status"):
            require(field in required, f"{resolution_path} required missing {field}.", errors)
        require(REQUIRED_COMPLETION_MODES <= json_string_enum(resolution, "completion_mode"), f"{resolution_path} missing Ravenfall completion modes.", errors)
        require(REQUIRED_TRUTH_SCOPES <= json_string_enum(resolution, "truth_scope"), f"{resolution_path} missing required truth scopes.", errors)
        require(
            {"reward_delta_bundle_ref", "emitted_delta_refs", "diagnostic_noop_ref", "future_generation_bias_refs"} <= set(resolution.get("properties", {})),
            f"{resolution_path} missing consequence/no-op/future-bias properties.",
            errors,
        )

    consequence_path = "data/schemas/consequence_resolution_packet_schema.json"
    consequence = load_json_checked(root, root / consequence_path, errors)
    if isinstance(consequence, dict):
        for field in ("packet_id", "quest_ref", "completion_mode", "provenance"):
            require(field in required_fields(consequence), f"{consequence_path} required missing {field}.", errors)
        require(
            {"delta_bundle_ref", "delta_refs", "diagnostic_noop_ref"} <= set(consequence.get("properties", {})),
            f"{consequence_path} missing delta/no-op routing properties.",
            errors,
        )

    bundle_path = "data/schemas/reward_delta_bundle_schema.json"
    bundle = load_json_checked(root, root / bundle_path, errors)
    if isinstance(bundle, dict):
        require(
            const_value(bundle, "requires_worldstate_delta_or_noop") is True,
            f"{bundle_path} must require worldstate delta or DiagnosticNoOp.",
            errors,
        )
        require({"delta_refs", "delta_types", "diagnostic_noop_ref"} <= set(bundle.get("properties", {})), f"{bundle_path} missing delta routing fields.", errors)

    ruleset_path = "data/schemas/quest_reward_resolver_ruleset_schema.json"
    ruleset = load_json_checked(root, root / ruleset_path, errors)
    if isinstance(ruleset, dict):
        require(const_value(ruleset, "is_random_reward_table") is False, f"{ruleset_path} must not be a random reward table.", errors)
        require(const_value(ruleset, "primary_model") == "consequence_routing", f"{ruleset_path} primary_model must be consequence_routing.", errors)

    wolf_path = "data/schemas/wolf_reward_delta_schema.json"
    wolf = load_json_checked(root, root / wolf_path, errors)
    if isinstance(wolf, dict):
        require(const_value(wolf, "is_morality_update") is False, f"{wolf_path} must forbid morality updates.", errors)
        require({"white_wolf_effects", "dark_wolf_effects", "twin_wolf_coherence_effects"} <= set(wolf.get("properties", {})), f"{wolf_path} missing twin-wolf effect fields.", errors)

    ability_path = "data/schemas/ability_reward_delta_schema.json"
    ability = load_json_checked(root, root / ability_path, errors)
    if isinstance(ability, dict):
        require("source_refs" in ability.get("properties", {}), f"{ability_path} missing source_refs.", errors)
        require("ability_state_update_packet_ref" in ability.get("properties", {}), f"{ability_path} missing ability_state_update_packet_ref.", errors)

    future_path = "data/schemas/future_generation_bias_reward_delta_schema.json"
    future = load_json_checked(root, root / future_path, errors)
    if isinstance(future, dict):
        require("future_generation_bias_update_refs" in future.get("properties", {}), f"{future_path} missing future_generation_bias_update_refs.", errors)
        require("bias_targets" in future.get("properties", {}), f"{future_path} missing bias_targets.", errors)

    prophecy_path = "data/schemas/prophecy_pressure_reward_delta_schema.json"
    prophecy = load_json_checked(root, root / prophecy_path, errors)
    if isinstance(prophecy, dict):
        require(const_value(prophecy, "guarantees_future") is False, f"{prophecy_path} must not guarantee future outcomes.", errors)


def check_delta_coverage(root: Path, errors: list[str]) -> None:
    expected_files = {
        "player_state": "data/schemas/player_state_reward_delta_schema.json",
        "branch": "data/schemas/branch_reward_delta_schema.json",
        "worldstate": "data/schemas/worldstate_reward_delta_schema.json",
        "location": "data/schemas/location_reward_delta_schema.json",
        "wolf": "data/schemas/wolf_reward_delta_schema.json",
        "ability": "data/schemas/ability_reward_delta_schema.json",
        "plane_attunement": "data/schemas/plane_attunement_reward_delta_schema.json",
        "lineage": "data/schemas/lineage_reward_delta_schema.json",
        "perception": "data/schemas/perception_reward_delta_schema.json",
        "myth_seed": "data/schemas/myth_seed_reward_delta_schema.json",
        "prophecy_pressure": "data/schemas/prophecy_pressure_reward_delta_schema.json",
        "faction": "data/schemas/faction_reward_delta_schema.json",
        "npc_relationship": "data/schemas/npc_relationship_reward_delta_schema.json",
        "artifact_eligibility": "data/schemas/artifact_eligibility_reward_delta_schema.json",
        "creature_eligibility": "data/schemas/creature_eligibility_reward_delta_schema.json",
        "future_generation_bias": "data/schemas/future_generation_bias_reward_delta_schema.json",
    }
    for delta_type, path_name in expected_files.items():
        data = load_json_checked(root, root / path_name, errors)
        if not isinstance(data, dict):
            continue
        required = required_fields(data)
        for field in ("delta_id", "quest_ref", "completion_mode", "truth_scope", "provenance"):
            require(field in required, f"{path_name} required missing {field}.", errors)
        require("truth_scope" in data.get("properties", {}), f"{path_name} missing truth_scope property.", errors)
        require("completion_mode" in data.get("properties", {}), f"{path_name} missing completion_mode property.", errors)

    bundle_example = load_json_checked(root, root / PHASE_15_EXAMPLE_ROOT / "quest_reward_delta_bundle_reveal_oath.example.json", errors)
    if isinstance(bundle_example, dict):
        delta_types = set(bundle_example.get("delta_types", []))
        require(bool(delta_types), "quest_reward_delta_bundle_reveal_oath.example.json must list delta_types.", errors)
        require(delta_types <= REQUIRED_DELTA_TYPES, f"Unknown reward delta types in reveal-oath bundle: {sorted(delta_types - REQUIRED_DELTA_TYPES)}", errors)


def has_noop_or_consequence(data: dict[str, Any]) -> bool:
    if isinstance(data.get("diagnostic_noop_ref"), str) and data["diagnostic_noop_ref"]:
        return True
    if isinstance(data.get("reward_delta_bundle_ref"), str) and data["reward_delta_bundle_ref"]:
        return True
    emitted = data.get("emitted_delta_refs")
    return isinstance(emitted, list) and any(isinstance(ref, str) and ref for ref in emitted)


def check_examples(root: Path, errors: list[str]) -> None:
    example_dir = root / PHASE_15_EXAMPLE_ROOT
    if not example_dir.is_dir():
        errors.append(f"Missing Phase 15 examples directory: {PHASE_15_EXAMPLE_ROOT}")
        return

    rules = load_json_checked(root, root / PHASE_15_EXAMPLE_VALIDATION, errors)
    required_modes = set()
    required_fields_in_examples = set()
    if isinstance(rules, dict):
        required_modes = {mode for mode in rules.get("required_examples", []) if isinstance(mode, str)}
        required_fields_in_examples = {field for field in rules.get("must_include", []) if isinstance(field, str)}

    seen_modes: set[str] = set()
    seen_invalid_reasons: set[str] = set()
    for path in sorted(example_dir.glob("*.json")):
        data = load_json_checked(root, path, errors)
        if not isinstance(data, dict):
            continue
        rel = relative_name(root, path)
        if path.name.startswith("invalid_"):
            reasons = data.get("invalid_because")
            require(isinstance(reasons, list) and reasons, f"{rel} invalid example missing invalid_because list.", errors)
            if isinstance(reasons, list):
                seen_invalid_reasons.update(reason for reason in reasons if isinstance(reason, str))
            require(isinstance(data.get("example"), dict), f"{rel} invalid example missing example object.", errors)
            continue

        if path.name == "quest_reward_delta_bundle_reveal_oath.example.json":
            require(isinstance(data.get("bundle_id"), str), f"{rel} missing bundle_id.", errors)
            require(isinstance(data.get("delta_types"), list) and data["delta_types"], f"{rel} missing delta_types.", errors)
            require(data.get("requires_worldstate_delta_or_noop") is True, f"{rel} must require worldstate delta or DiagnosticNoOp.", errors)
            require(isinstance(data.get("provenance"), dict), f"{rel} missing provenance object.", errors)
            continue

        if path.name == "quest_reward_diagnostic_noop_example.json":
            for field in ("schema_id", "version", "noop_id", "reason", "source_context", "evaluation"):
                require(field in data, f"{rel} missing {field}.", errors)
            require(data.get("schema_id") == "ywe.diagnostic_noop.v1", f"{rel} must use canonical DiagnosticNoOp schema_id.", errors)
            require(isinstance(data.get("source_context"), dict), f"{rel} source_context must be an object.", errors)
            evaluation = data.get("evaluation")
            require(isinstance(evaluation, dict), f"{rel} evaluation must be an object.", errors)
            if isinstance(evaluation, dict):
                require(evaluation.get("truth_scope") == "diagnostic_noop", f"{rel} evaluation truth_scope must be diagnostic_noop.", errors)
            continue

        if path.name == "quest_reward_input_context_ravenfall_gate.example.json":
            for field in ("context_id", "quest_ref", "player_runtime_state_ref", "leaf_branch_reality_ref", "phase_14_ability_gate_passed", "provenance"):
                require(field in data, f"{rel} missing {field}.", errors)
            require(data.get("phase_14_ability_gate_passed") is True, f"{rel} must pass Phase 14 ability gate.", errors)
            require(isinstance(data.get("provenance"), dict), f"{rel} missing provenance object.", errors)
            continue

        mode = data.get("completion_mode")
        if isinstance(mode, str):
            seen_modes.add(mode)
        for field in required_fields_in_examples:
            require(field in data, f"{rel} missing required example field: {field}", errors)
        require(data.get("validation_status") == "valid", f"{rel} must declare validation_status valid.", errors)
        require(isinstance(data.get("provenance"), dict), f"{rel} missing provenance object.", errors)
        require(has_noop_or_consequence(data), f"{rel} must emit consequence delta refs or DiagnosticNoOp.", errors)
        if isinstance(data.get("future_generation_bias_refs"), list):
            require(bool(data["future_generation_bias_refs"]), f"{rel} future_generation_bias_refs must not be empty.", errors)
        if "wolf_summary" in data:
            wolf_summary = data.get("wolf_summary")
            require(isinstance(wolf_summary, dict), f"{rel} wolf_summary must be an object.", errors)
        if "ability_summary" in data:
            ability_summary = data.get("ability_summary")
            require(isinstance(ability_summary, dict), f"{rel} ability_summary must be an object.", errors)

    require(required_modes <= seen_modes, f"Missing Ravenfall Gate Phase 15 completion-mode examples: {sorted(required_modes - seen_modes)}", errors)
    for reason in (
        "ability_reward_without_source_provenance",
        "quest_completion_without_consequence_packet",
        "random_reward_table_primary_model",
        "white_wolf_good_dark_wolf_evil_language",
    ):
        require(reason in seen_invalid_reasons, f"Missing invalid example reason: {reason}", errors)


def allowed_forbidden_pattern_reference(pattern: str, lines: list[str], index: int) -> bool:
    context = "\n".join(lines[max(0, index - 6) : min(len(lines), index + 3)]).lower()
    if any(term in context for term in ALLOWED_FORBIDDEN_CONTEXT_TERMS):
        return True

    lowered_line = lines[index].lower()
    pattern_re = re.escape(pattern.lower())
    negation_prefix_re = "|".join(re.escape(prefix) for prefix in DIRECT_NEGATION_PREFIXES)
    return re.search(rf"\b(?:{negation_prefix_re})\b[\w\s\"'`=_-]{{0,100}}{pattern_re}", lowered_line) is not None


def check_forbidden_language(root: Path, errors: list[str]) -> None:
    data = load_json_checked(root, root / PHASE_15_FORBIDDEN_LANGUAGE, errors)
    if not isinstance(data, dict):
        return
    raw_patterns = data.get("patterns", data.get("forbidden_patterns", []))
    if not isinstance(raw_patterns, list):
        errors.append(f"{PHASE_15_FORBIDDEN_LANGUAGE} patterns must be a list.")
        return
    patterns = [pattern for pattern in raw_patterns if isinstance(pattern, str) and pattern.strip()]
    for path in phase_15_scan_files(root):
        rel = relative_name(root, path)
        if rel == PHASE_15_FORBIDDEN_LANGUAGE:
            continue
        lines = read_text(path).splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            for pattern in patterns:
                if pattern.lower() not in lowered:
                    continue
                if allowed_forbidden_pattern_reference(pattern, lines, index):
                    continue
                errors.append(f"Forbidden Phase 15 phrase found in {rel}:{index + 1}: {line.strip()}")


def check_contract_terms(root: Path, errors: list[str]) -> None:
    required_terms = [
        "QuestRewardResolutionPacket",
        "ConsequenceResolutionPacket",
        "DiagnosticNoOp",
        "completion mode",
        "truth scope",
        "RewardDeltaBundle",
        "FutureGenerationBiasUpdate",
        "AbilityStateUpdatePacket",
        "AbilityUnlockPressure",
        "source_refs",
        "Twin Wolf",
        "decoherence",
        "worldstate",
        "location",
        "branch",
        "myth",
        "prophecy",
        "faction",
        "artifact",
        "creature",
    ]
    corpus = "\n".join(read_text(path) for path in phase_15_scan_files(root) if path.suffix == ".md")
    normalized = corpus.lower()
    for term in required_terms:
        require(term.lower() in normalized, f"Missing Phase 15 contract term: {term}", errors)


def check_github_checks_matrix(root: Path, errors: list[str]) -> None:
    matrix_path = "data/validation/phase_15_github_checks_matrix.json"
    matrix = load_json_checked(root, root / matrix_path, errors)
    if not isinstance(matrix, dict):
        return
    checks = matrix.get("checks")
    require(isinstance(checks, list), f"{matrix_path} checks must be a list.", errors)
    if not isinstance(checks, list):
        return
    check_set = {check for check in checks if isinstance(check, str)}
    for path_name in PHASE_15_CHECK_SPECS:
        spec = load_json_checked(root, root / path_name, errors)
        if not isinstance(spec, dict):
            continue
        spec_id = spec.get("spec_id")
        require(isinstance(spec_id, str), f"{path_name} missing spec_id.", errors)
        if isinstance(spec_id, str):
            require(spec_id in check_set, f"{matrix_path} checks missing {spec_id}.", errors)


def check_no_package_templates(root: Path, errors: list[str]) -> None:
    forbidden_repo_paths = [
        "00_CODEX_EXECUTION_PROMPT.md",
        "01_PHASE_15_SCOPE.md",
        "13_CODEX_COPY_PASTE_TASK.md",
        "14_REVIEW_AND_HANDOFF_TEMPLATE.md",
        "manifests/package_manifest.json",
        "manifests/package_checksums.json",
        "payload/docs/architecture/quest_reward_resolver_contract.md",
    ]
    for path_name in forbidden_repo_paths:
        require(not (root / path_name).exists(), f"Package-level artifact copied into repository: {path_name}", errors)

    template_markers = (
        "YWE_PHASE_15_QUEST_REWARD_RESOLVER_HANDOFF_PACKAGE",
        "copy only payload",
        "do not copy package-level",
        "fill this in",
    )
    for path in phase_15_scan_files(root):
        rel = relative_name(root, path)
        text = read_text(path).lower()
        for marker in template_markers:
            require(marker.lower() not in text, f"Package template marker found in {rel}: {marker}", errors)


def check_non_destructive_diff(root: Path, errors: list[str]) -> None:
    budget = load_json_checked(root, root / PHASE_15_NON_DESTRUCTIVE_BUDGET, errors)
    if not isinstance(budget, dict):
        return
    added, deleted, renamed, copied, existing_touched = classify_change_paths(git_change_paths(root, errors))

    max_added = budget_limit(budget, "max_expected_new_files", "max_new_files", default=120)
    max_deleted = budget_limit(budget, "delete_budget", "max_existing_file_deletions", default=0)
    max_renamed = budget_limit(budget, "max_directory_renames", default=0)
    max_copied = budget_limit(budget, "max_copied_paths", default=0)
    max_touched = budget_limit(budget, "max_expected_modified_files", "max_existing_files_touched_without_review", default=25)

    require(len(added) <= max_added, f"Phase 15 added files exceed budget {max_added}: {len(added)}", errors)
    require(len(deleted) <= max_deleted, f"Phase 15 file deletions exceed budget {max_deleted}: {deleted}", errors)
    require(len(renamed) <= max_renamed, f"Phase 15 renames exceed budget {max_renamed}: {renamed}", errors)
    require(len(copied) <= max_copied, f"Phase 15 copied paths exceed budget {max_copied}: {copied}", errors)
    require(
        len(existing_touched) <= max_touched,
        f"Phase 15 existing files touched exceed budget {max_touched}: {len(existing_touched)}",
        errors,
    )


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    contract = load_json_checked(root, root / PHASE_15_ACCEPTANCE_CONTRACT, errors)
    if isinstance(contract, dict):
        require(contract.get("requires_phase_14_gate") is True, f"{PHASE_15_ACCEPTANCE_CONTRACT} must require Phase 14 gate.", errors)
        gates = contract.get("acceptance_gates", [])
        for gate in ("phase_14_prerequisite_passes", "required_artifacts_present", "non_destructive_diff_passes"):
            require(isinstance(gates, list) and gate in gates, f"{PHASE_15_ACCEPTANCE_CONTRACT} missing gate: {gate}", errors)

    check_phase_14_prerequisite(root, errors)
    check_required_artifacts(root, errors)
    check_json_integrity(root, errors)
    check_schema_contracts(root, errors)
    check_delta_coverage(root, errors)
    check_examples(root, errors)
    check_forbidden_language(root, errors)
    check_contract_terms(root, errors)
    check_github_checks_matrix(root, errors)
    check_no_package_templates(root, errors)
    check_non_destructive_diff(root, errors)

    if errors:
        print("Quest Reward Resolver check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Quest Reward Resolver check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
