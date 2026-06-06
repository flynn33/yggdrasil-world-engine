#!/usr/bin/env python3
"""Validate Phase 14 ability and power engine contract coverage."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"

PHASE_14_ACCEPTANCE_CONTRACT = "data/validation/phase_14_acceptance_contract.json"
PHASE_14_REQUIRED_ARTIFACTS = "data/validation/phase_14_required_artifacts.json"
PHASE_14_PREREQUISITE_GATE = "data/validation/phase_14_prerequisite_gate.json"
PHASE_14_FORBIDDEN_LANGUAGE = "data/validation/phase_14_forbidden_language_patterns.json"
PHASE_14_NON_DESTRUCTIVE_BUDGET = "data/validation/phase_14_non_destructive_change_budget.json"
PHASE_14_EXAMPLE_VALIDATION = "data/validation/ravenfall_gate_phase_14_example_validation.json"
PHASE_14_EXAMPLE_ROOT = "examples/ability_power_engine"

PHASE_14_VALIDATION_FILES = [
    PHASE_14_ACCEPTANCE_CONTRACT,
    PHASE_14_PREREQUISITE_GATE,
    PHASE_14_REQUIRED_ARTIFACTS,
    PHASE_14_FORBIDDEN_LANGUAGE,
    PHASE_14_NON_DESTRUCTIVE_BUDGET,
    "data/validation/phase_14_guardrail_rules.json",
    "data/validation/phase_14_github_checks_matrix.json",
    "data/validation/ability_state_validation_rules.json",
    "data/validation/ability_unlock_pressure_validation_rules.json",
    "data/validation/ability_source_ref_validation_rules.json",
    "data/validation/ability_wolf_canon_validation_rules.json",
    "data/validation/ability_combat_quest_use_validation_rules.json",
    "data/validation/ability_consequence_validation_rules.json",
    "data/validation/ability_no_generic_skill_tree_validation_rules.json",
    PHASE_14_EXAMPLE_VALIDATION,
]

PHASE_14_CHECK_SPECS = [
    "data/validation/check_source_truth_alignment_prereq.spec.json",
    "data/validation/check_phase_13_wolf_canon_prereq.spec.json",
    "data/validation/check_required_phase_14_contracts.spec.json",
    "data/validation/check_phase_14_json_integrity.spec.json",
    "data/validation/check_no_generic_skill_tree.spec.json",
    "data/validation/check_ability_source_provenance.spec.json",
    "data/validation/check_ability_wolf_canon.spec.json",
    "data/validation/check_no_wolf_morality_ability_drift.spec.json",
    "data/validation/check_ability_consequence_packets.spec.json",
    "data/validation/check_ability_combat_quest_use.spec.json",
    "data/validation/check_ability_decoherence_not_death.spec.json",
    "data/validation/check_non_destructive_diff_phase_14.spec.json",
]

SOURCE_TRUTH_PREREQ_FILES = [
    "docs/project/source_inventory.md",
    "docs/architecture/ash_model_engine_cosmology_contract.md",
    "docs/architecture/ash_pattern_system_component_contract.md",
    "docs/architecture/ywe_cosmology_authority_contract.md",
    "data/validation/source_truth_alignment_contract.json",
]

TWIN_WOLF_PREREQ_FILES = [
    "docs/architecture/twin_wolf_companion_canon_contract.md",
    "data/schemas/twin_wolf_companion_state_schema.json",
    "data/validation/twin_wolf_canon_validation_rules.json",
]

PHASE_8_TO_12_PREREQ_FILES = [
    "data/schemas/leaf_branch_reality_state_schema.json",
    "data/schemas/player_runtime_state_schema.json",
    "data/schemas/worldstate_delta_packet_schema.json",
    "data/schemas/location_state_record_schema.json",
    "data/schemas/quest_generation_context_schema.json",
    "docs/architecture/player_runtime_state_contract.md",
    "docs/architecture/worldstate_location_mutation_v1.md",
    "docs/architecture/quest_npc_lore_generation_v1.md",
]

PHASE_14_SCAN_GLOBS = [
    "docs/architecture/ability_*.md",
    "data/schemas/ability_*_schema.json",
    "data/validation/ability_*_validation_rules.json",
    "data/validation/phase_14_*.json",
    "data/validation/check_ability_*.spec.json",
    "data/validation/check_no_generic_skill_tree.spec.json",
    "data/validation/check_no_wolf_morality_ability_drift.spec.json",
    "examples/ability_power_engine/**/*.json",
]

CONSEQUENCE_KIND_REF_FIELDS = {
    "worldstate_delta": "worldstate_delta_refs",
    "diagnostic_noop": "diagnostic_noop_ref",
    "player_state_update": "player_state_update_refs",
    "location_mutation_candidate": "location_mutation_candidate_refs",
    "future_generation_bias": "future_generation_bias_refs",
    "quest_progress_signal": "quest_progress_signal_refs",
    "npc_relationship_change": "npc_relationship_change_refs",
    "myth_seed_candidate": "myth_seed_candidate_refs",
    "prophecy_pressure_update": "prophecy_pressure_update_refs",
    "wolf_coherence_event": "wolf_coherence_event_refs",
    "ability_state_update": "ability_state_update_refs",
}

ALLOWED_FORBIDDEN_CONTEXT_TERMS = {
    "forbidden",
    "invalid",
    "reject",
    "rejected",
    "failure_conditions",
    "fail if",
    "must not",
    "do not",
    "should not",
    "may not",
    "cannot",
    "not a morality",
    "not moral",
    "not good and evil",
    "not topmost",
    "not the topmost",
    "not death",
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


def load_json(path: Path):
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
        errors.append("Unable to resolve git base ref for Phase 14 diff checks.")
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


def classify_change_paths(statuses: list[tuple[str, str]]) -> tuple[list[str], list[str], list[str], list[str]]:
    deleted: list[str] = []
    renamed: list[str] = []
    copied: list[str] = []
    existing_touched: list[str] = []
    for status, path in statuses:
        if status.startswith("A"):
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
    return deleted, renamed, copied, existing_touched


def budget_limit(limits: dict, key: str, default: int) -> int:
    raw_value = limits.get(key, default)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def all_phase_14_json_files(root: Path) -> list[Path]:
    paths: set[Path] = set()
    for path_name in PHASE_14_VALIDATION_FILES + PHASE_14_CHECK_SPECS:
        paths.add(root / path_name)
    for rel_dir in ("data/schemas", PHASE_14_EXAMPLE_ROOT):
        base = root / rel_dir
        if base.is_dir():
            paths.update(base.rglob("ability_*.json"))
            paths.update(base.rglob("*.example.json"))
    return sorted(paths)


def phase_14_scan_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in PHASE_14_SCAN_GLOBS:
        files.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(files)


def text_corpus(root: Path, path_names: list[str]) -> str:
    parts = [read_text(root / path_name) for path_name in path_names if (root / path_name).is_file()]
    return "\n".join(parts)


def has_nonempty_list(data: dict, key: str) -> bool:
    value = data.get(key)
    return isinstance(value, list) and len(value) > 0


def schema_const(data: dict) -> str | None:
    properties = data.get("properties", {})
    if not isinstance(properties, dict):
        return None
    schema_id = properties.get("schema_id", {})
    if not isinstance(schema_id, dict):
        return None
    value = schema_id.get("const")
    return value if isinstance(value, str) else None


def check_prerequisites(root: Path, errors: list[str]) -> None:
    gate = load_json_checked(root, root / PHASE_14_PREREQUISITE_GATE, errors)
    if isinstance(gate, dict):
        required_flags = gate.get("must_be_true", [])
        require(isinstance(required_flags, list), f"{PHASE_14_PREREQUISITE_GATE} must_be_true must be a list.", errors)
        forbidden_flags = gate.get("must_not_be_true", [])
        require(isinstance(forbidden_flags, list), f"{PHASE_14_PREREQUISITE_GATE} must_not_be_true must be a list.", errors)

    for path_name in SOURCE_TRUTH_PREREQ_FILES + TWIN_WOLF_PREREQ_FILES + PHASE_8_TO_12_PREREQ_FILES:
        require((root / path_name).is_file(), f"Missing Phase 14 prerequisite artifact: {path_name}", errors)

    source_truth_contract = load_json_checked(root, root / "data/validation/source_truth_alignment_contract.json", errors)
    corpus = text_corpus(root, SOURCE_TRUTH_PREREQ_FILES + TWIN_WOLF_PREREQ_FILES)
    if isinstance(source_truth_contract, dict):
        for phrase in source_truth_contract.get("required_statements", []):
            require(isinstance(phrase, str) and phrase in corpus, f"Missing source-truth prerequisite phrase: {phrase}", errors)

    wolf_rules = load_json_checked(root, root / "data/validation/twin_wolf_canon_validation_rules.json", errors)
    if isinstance(wolf_rules, dict):
        phrase_map = wolf_rules.get("required_truth_phrases", {})
        if not isinstance(phrase_map, dict):
            errors.append("Twin wolf validation rules must define required_truth_phrases.")
        else:
            normalized = corpus.lower()
            for truth in wolf_rules.get("required_truths", []):
                phrase = phrase_map.get(truth)
                require(
                    isinstance(phrase, str) and phrase.lower() in normalized,
                    f"Missing twin-wolf prerequisite truth: {truth}",
                    errors,
                )


def check_required_artifacts(root: Path, errors: list[str]) -> None:
    artifacts = load_json_checked(root, root / PHASE_14_REQUIRED_ARTIFACTS, errors)
    if not isinstance(artifacts, dict):
        return

    architecture_docs = artifacts.get("architecture_docs", [])
    schemas = artifacts.get("schemas", [])
    require(isinstance(architecture_docs, list), f"{PHASE_14_REQUIRED_ARTIFACTS} architecture_docs must be a list.", errors)
    require(isinstance(schemas, list), f"{PHASE_14_REQUIRED_ARTIFACTS} schemas must be a list.", errors)

    if isinstance(architecture_docs, list):
        for file_name in architecture_docs:
            require(isinstance(file_name, str), "Phase 14 architecture doc entries must be strings.", errors)
            if isinstance(file_name, str):
                require((root / "docs" / "architecture" / file_name).is_file(), f"Missing Phase 14 architecture doc: {file_name}", errors)

    if isinstance(schemas, list):
        for file_name in schemas:
            require(isinstance(file_name, str), "Phase 14 schema entries must be strings.", errors)
            if isinstance(file_name, str):
                require((root / "data" / "schemas" / file_name).is_file(), f"Missing Phase 14 schema: {file_name}", errors)

    for path_name in PHASE_14_VALIDATION_FILES + PHASE_14_CHECK_SPECS:
        require((root / path_name).is_file(), f"Missing Phase 14 validation or check artifact: {path_name}", errors)

    minimum = artifacts.get("examples_required_minimum", 10)
    try:
        minimum_count = int(minimum)
    except (TypeError, ValueError):
        errors.append(f"{PHASE_14_REQUIRED_ARTIFACTS} examples_required_minimum must be an integer.")
        minimum_count = 10
    example_files = sorted((root / PHASE_14_EXAMPLE_ROOT).glob("*.json"))
    require(len(example_files) >= minimum_count, f"Phase 14 examples below minimum {minimum_count}: {len(example_files)}", errors)


def check_json_integrity(root: Path, errors: list[str]) -> None:
    for path in all_phase_14_json_files(root):
        data = load_json_checked(root, path, errors)
        if not isinstance(data, dict):
            continue
        rel = relative_name(root, path)
        if rel.startswith("data/schemas/ability_"):
            require(schema_const(data) is not None, f"{rel} missing schema_id const.", errors)
            required = data.get("required", [])
            require(isinstance(required, list), f"{rel} required must be a list.", errors)
            if isinstance(required, list):
                require("schema_id" in required, f"{rel} required missing schema_id.", errors)
                require("schema_version" in required, f"{rel} required missing schema_version.", errors)
        elif rel.startswith(PHASE_14_EXAMPLE_ROOT):
            if data.get("invalid_example") is True:
                require(isinstance(data.get("reject_reason"), str), f"{rel} invalid example missing reject_reason.", errors)
            else:
                require(isinstance(data.get("schema_id"), str), f"{rel} valid example missing schema_id.", errors)


def check_schema_contracts(root: Path, errors: list[str]) -> None:
    expected = {
        "data/schemas/ability_manifest_schema.json": {
            "schema_id": "ywe.ability_manifest.v1",
            "required": {"source_refs", "use_modes", "consequence_policy_ref", "forbidden_interpretations"},
            "properties": {"consequence_policy_ref", "forbidden_interpretations"},
        },
        "data/schemas/ability_unlock_pressure_schema.json": {
            "schema_id": "ywe.ability_unlock_pressure.v1",
            "required": {"pressure_score", "pressure_sources"},
            "properties": {"recommended_state_transition"},
        },
        "data/schemas/ability_use_context_schema.json": {
            "schema_id": "ywe.ability_use_context.v1",
            "required": {"use_mode", "player_ref", "branch_ref", "source_refs", "expected_consequence_kinds"},
            "properties": {"expected_consequence_kinds", "wolf_companion_refs"},
        },
        "data/schemas/ability_consequence_packet_schema.json": {
            "schema_id": "ywe.ability_consequence_packet.v1",
            "required": {"use_context_ref", "consequence_kinds"},
            "properties": {
                "worldstate_delta_refs",
                "diagnostic_noop_ref",
                "player_state_update_refs",
                "location_mutation_candidate_refs",
                "future_generation_bias_refs",
                "quest_progress_signal_refs",
                "npc_relationship_change_refs",
                "myth_seed_candidate_refs",
                "prophecy_pressure_update_refs",
                "wolf_coherence_event_refs",
                "ability_state_update_refs",
            },
        },
        "data/schemas/ability_wolf_synergy_schema.json": {
            "schema_id": "ywe.ability_wolf_synergy.v1",
            "required": {"wolf_scope", "not_morality_system"},
            "properties": {"companion_presence_required", "decoherence_risk_ref", "recovery_path_refs"},
        },
        "data/schemas/ability_decoherence_state_schema.json": {
            "schema_id": "ywe.ability_decoherence_state.v1",
            "required": {"affected_ref", "temporary"},
            "properties": {"recovery_condition_refs", "forbidden_interpretations"},
        },
        "data/schemas/ability_state_update_packet_schema.json": {
            "schema_id": "ywe.ability_state_update_packet.v1",
            "required": {"ability_updates", "source_refs"},
            "properties": {"consequence_refs", "diagnostic_refs"},
        },
    }
    for path_name, contract in expected.items():
        data = load_json_checked(root, root / path_name, errors)
        if not isinstance(data, dict):
            continue
        require(schema_const(data) == contract["schema_id"], f"{path_name} has wrong schema_id const.", errors)
        raw_required = data.get("required", [])
        if not isinstance(raw_required, list):
            errors.append(f"{path_name} required must be a list.")
            raw_required = []
        required = {field for field in raw_required if isinstance(field, str)}
        if len(required) != len(raw_required):
            errors.append(f"{path_name} required entries must be strings.")
        for field in contract["required"]:
            require(field in required, f"{path_name} required missing {field}.", errors)
        properties = data.get("properties", {})
        if not isinstance(properties, dict):
            errors.append(f"{path_name} properties must be an object.")
            properties = {}
        for field in contract["properties"]:
            require(field in properties, f"{path_name} properties missing {field}.", errors)


def example_key(path: Path) -> str:
    key = path.name.removesuffix(".example.json")
    key = key.removeprefix("invalid_")
    for suffix in ("_manifest", "_ability"):
        if key.endswith(suffix):
            key = key.removesuffix(suffix)
    return key


def has_consequence_ref_payload(data: dict, field: str) -> bool:
    if field.endswith("_refs"):
        return has_nonempty_list(data, field)
    return isinstance(data.get(field), dict)


def check_consequence_ref_alignment(data: dict, rel: str, errors: list[str]) -> None:
    raw_kinds = data.get("consequence_kinds")
    if not isinstance(raw_kinds, list):
        return
    kinds = {kind for kind in raw_kinds if isinstance(kind, str)}
    for kind, ref_field in CONSEQUENCE_KIND_REF_FIELDS.items():
        has_payload = has_consequence_ref_payload(data, ref_field)
        if kind in kinds:
            require(has_payload, f"{rel} declares {kind} but missing {ref_field}.", errors)
        if has_payload:
            require(kind in kinds, f"{rel} populates {ref_field} but consequence_kinds missing {kind}.", errors)


def check_examples(root: Path, errors: list[str]) -> None:
    rules = load_json_checked(root, root / PHASE_14_EXAMPLE_VALIDATION, errors)
    example_root = root / PHASE_14_EXAMPLE_ROOT
    if not example_root.is_dir():
        errors.append(f"Missing Phase 14 examples directory: {PHASE_14_EXAMPLE_ROOT}")
        return
    files = sorted(example_root.glob("*.json"))
    valid_keys = {example_key(path) for path in files if not path.name.startswith("invalid_")}
    invalid_keys = {example_key(path) for path in files if path.name.startswith("invalid_")}

    if isinstance(rules, dict):
        for required_name in rules.get("required_examples", []):
            require(
                isinstance(required_name, str) and required_name in valid_keys,
                f"Missing required Phase 14 example: {required_name}",
                errors,
            )
        for invalid_name in rules.get("invalid_examples_must_be_rejected", []):
            require(
                isinstance(invalid_name, str) and invalid_name in invalid_keys,
                f"Missing required invalid Phase 14 example key: {invalid_name}",
                errors,
            )

    seen_schema_ids: set[str] = set()
    for path in files:
        data = load_json_checked(root, path, errors)
        if not isinstance(data, dict):
            continue
        rel = relative_name(root, path)
        if data.get("invalid_example") is True:
            candidate = data.get("candidate")
            require(isinstance(candidate, dict), f"{rel} invalid example missing candidate object.", errors)
            continue

        schema_id = data.get("schema_id")
        require(isinstance(schema_id, str), f"{rel} missing schema_id.", errors)
        if isinstance(schema_id, str):
            seen_schema_ids.add(schema_id)

        if schema_id == "ywe.ability_manifest.v1":
            require(has_nonempty_list(data, "source_refs"), f"{rel} missing source_refs.", errors)
            require(has_nonempty_list(data, "use_modes"), f"{rel} missing use_modes.", errors)
            require(isinstance(data.get("consequence_policy_ref"), dict), f"{rel} missing consequence_policy_ref.", errors)
            require(has_nonempty_list(data, "forbidden_interpretations"), f"{rel} missing forbidden_interpretations.", errors)
        elif schema_id == "ywe.ability_unlock_pressure.v1":
            require(has_nonempty_list(data, "pressure_sources"), f"{rel} missing pressure_sources.", errors)
            require(isinstance(data.get("pressure_score"), (int, float)), f"{rel} missing numeric pressure_score.", errors)
        elif schema_id == "ywe.ability_use_context.v1":
            require(has_nonempty_list(data, "source_refs"), f"{rel} missing source_refs.", errors)
            require(has_nonempty_list(data, "expected_consequence_kinds"), f"{rel} missing expected_consequence_kinds.", errors)
        elif schema_id == "ywe.ability_consequence_packet.v1":
            require(has_nonempty_list(data, "consequence_kinds"), f"{rel} missing consequence_kinds.", errors)
            check_consequence_ref_alignment(data, rel, errors)
        elif schema_id == "ywe.ability_wolf_synergy.v1":
            require(data.get("companion_presence_required") is True, f"{rel} companion_presence_required must be true.", errors)
            require(data.get("not_morality_system") is True, f"{rel} not_morality_system must be true.", errors)
            require(has_nonempty_list(data, "recovery_path_refs"), f"{rel} missing recovery_path_refs.", errors)
        elif schema_id == "ywe.ability_decoherence_state.v1":
            require(data.get("temporary") is True, f"{rel} decoherence must be temporary.", errors)
            require(has_nonempty_list(data, "recovery_condition_refs"), f"{rel} missing recovery_condition_refs.", errors)

    for schema_id in (
        "ywe.ability_manifest.v1",
        "ywe.ability_unlock_pressure.v1",
        "ywe.ability_use_context.v1",
        "ywe.ability_consequence_packet.v1",
        "ywe.ability_wolf_synergy.v1",
        "ywe.ability_decoherence_state.v1",
    ):
        require(schema_id in seen_schema_ids, f"Missing Phase 14 example with schema_id {schema_id}.", errors)


def allowed_forbidden_pattern_reference(pattern: str, lines: list[str], index: int) -> bool:
    context = "\n".join(lines[max(0, index - 6) : min(len(lines), index + 3)]).lower()
    if any(term in context for term in ALLOWED_FORBIDDEN_CONTEXT_TERMS):
        return True

    lowered_line = lines[index].lower()
    pattern_re = re.escape(pattern.lower())
    negation_prefix_re = "|".join(re.escape(prefix) for prefix in DIRECT_NEGATION_PREFIXES)
    return re.search(rf"\b(?:{negation_prefix_re})\b[\w\s\"'`=-]{{0,100}}{pattern_re}", lowered_line) is not None


def check_forbidden_language(root: Path, errors: list[str]) -> None:
    data = load_json_checked(root, root / PHASE_14_FORBIDDEN_LANGUAGE, errors)
    if not isinstance(data, dict):
        return
    raw_patterns = data.get("patterns", data.get("forbidden_patterns", []))
    if not isinstance(raw_patterns, list):
        errors.append(f"{PHASE_14_FORBIDDEN_LANGUAGE} patterns must be a list.")
        return
    patterns = [pattern for pattern in raw_patterns if isinstance(pattern, str) and pattern.strip()]
    for path in phase_14_scan_files(root):
        rel = relative_name(root, path)
        if rel == PHASE_14_FORBIDDEN_LANGUAGE:
            continue
        lines = read_text(path).splitlines()
        for index, line in enumerate(lines):
            lowered = line.lower()
            for pattern in patterns:
                if pattern.lower() not in lowered:
                    continue
                if allowed_forbidden_pattern_reference(pattern, lines, index):
                    continue
                errors.append(f"Forbidden Phase 14 phrase found in {rel}:{index + 1}: {line.strip()}")


def check_contract_terms(root: Path, errors: list[str]) -> None:
    required_terms = [
        "AbilityConsequencePacket",
        "AbilityStateUpdatePacket",
        "AbilityUnlockPressure",
        "source_refs",
        "branch reality",
        "lineage",
        "plane attunement",
        "artifact",
        "myth",
        "prophecy",
        "wolf",
        "combat",
        "quest",
        "decoherence",
        "recovery",
    ]
    corpus = "\n".join(read_text(path) for path in phase_14_scan_files(root) if path.suffix == ".md")
    normalized = corpus.lower()
    for term in required_terms:
        require(term.lower() in normalized, f"Missing Phase 14 contract term: {term}", errors)


def check_non_destructive_diff(root: Path, errors: list[str]) -> None:
    budget = load_json_checked(root, root / PHASE_14_NON_DESTRUCTIVE_BUDGET, errors)
    if not isinstance(budget, dict):
        return
    limits = budget.get("limits")
    if not isinstance(limits, dict):
        errors.append(f"{PHASE_14_NON_DESTRUCTIVE_BUDGET} limits must be an object.")
        return
    deleted, renamed, copied, existing_touched = classify_change_paths(git_change_paths(root, errors))

    max_deleted = budget_limit(limits, "max_existing_file_deletions", 0)
    max_renamed = budget_limit(limits, "max_directory_renames", 0)
    max_copied = budget_limit(limits, "max_copied_paths", 0)
    max_touched = budget_limit(limits, "max_existing_files_touched_without_review", 25)

    require(len(deleted) <= max_deleted, f"Phase 14 file deletions exceed budget {max_deleted}: {deleted}", errors)
    require(len(renamed) <= max_renamed, f"Phase 14 renames exceed budget {max_renamed}: {renamed}", errors)
    require(len(copied) <= max_copied, f"Phase 14 copied paths exceed budget {max_copied}: {copied}", errors)
    require(
        len(existing_touched) <= max_touched,
        f"Phase 14 existing files touched exceed budget {max_touched}: {len(existing_touched)}",
        errors,
    )


def check_no_package_templates(root: Path, errors: list[str]) -> None:
    forbidden_repo_paths = [
        "00_" + "CODE" + "X_EXECUTION_PROMPT.md",
        "01_REPOSITORY_PRECHECKS.md",
        "15_REVIEW_AND_HAND" + "OFF_TEMPLATE.md",
        "manifests/package_manifest.json",
        "checksum_manifest.json",
    ]
    for path_name in forbidden_repo_paths:
        require(not (root / path_name).exists(), f"Package-level template copied into repository: {path_name}", errors)

    template_markers = (
        "YWE_PHASE_14_ABILITY_POWER_ENGINE_HAND" + "OFF_PACKAGE",
        "copy " + "only payload",
        "do not copy " + "package-level",
        "implementation-" + "agent",
        "fill " + "this in",
    )
    for path in phase_14_scan_files(root):
        rel = relative_name(root, path)
        text = read_text(path).lower()
        for marker in template_markers:
            require(marker.lower() not in text, f"Package template marker found in {rel}: {marker}", errors)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    contract = load_json_checked(root, root / PHASE_14_ACCEPTANCE_CONTRACT, errors)
    if isinstance(contract, dict):
        require(contract.get("stop_on_failure") is True, f"{PHASE_14_ACCEPTANCE_CONTRACT} must stop on failure.", errors)
        gates = contract.get("required_gates", [])
        for gate in ("source_truth_alignment_gate", "phase_13_wolf_canon_gate", "non_destructive_diff_gate"):
            require(isinstance(gates, list) and gate in gates, f"{PHASE_14_ACCEPTANCE_CONTRACT} missing gate: {gate}", errors)

    check_prerequisites(root, errors)
    check_required_artifacts(root, errors)
    check_json_integrity(root, errors)
    check_schema_contracts(root, errors)
    check_examples(root, errors)
    check_forbidden_language(root, errors)
    check_contract_terms(root, errors)
    check_non_destructive_diff(root, errors)
    check_no_package_templates(root, errors)

    if errors:
        print("Ability Power Engine check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Ability Power Engine check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
