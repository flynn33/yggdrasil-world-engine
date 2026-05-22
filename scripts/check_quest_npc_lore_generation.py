#!/usr/bin/env python3
"""Validate Phase 12 quest, NPC, and lore generation contract coverage."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"
DEFAULT_CONTRACT = "data/validation/quest_npc_lore_generation_gate_contract.json"
PHASE_12_PREREQUISITE_GATE = "data/validation/phase_12_prerequisite_gate.json"
PHASE_12_REQUIRED_ARTIFACTS = "data/validation/phase_12_required_artifacts.json"
PHASE_12_FORBIDDEN_LANGUAGE = "data/validation/phase_12_forbidden_language_patterns.json"
PHASE_12_NON_DESTRUCTIVE_BUDGET = "data/validation/phase_12_non_destructive_change_budget.json"
PHASE_12_RAVENFALL_EXAMPLES = "data/validation/ravenfall_gate_phase_12_example_validation.json"
PHASE_12_EXAMPLE_ROOT = "examples/phase_12_quest_npc_lore_generation"

PHASE_12_CHECK_SPECS = [
    "data/validation/check_phase_11_acceptance_prereq.spec.json",
    "data/validation/check_required_phase_12_contracts.spec.json",
    "data/validation/check_phase_12_json_integrity.spec.json",
    "data/validation/check_no_generic_random_quest_generation.spec.json",
    "data/validation/check_axiom_generation_contracts.spec.json",
    "data/validation/check_feature_manifest_provenance_phase_12.spec.json",
    "data/validation/check_npc_relation_and_self_reference.spec.json",
    "data/validation/check_lore_pattern_trace_provenance.spec.json",
    "data/validation/check_quest_npc_lore_truth_scope.spec.json",
    "data/validation/check_no_content_generation_without_context.spec.json",
    "data/validation/check_non_destructive_diff_phase_12.spec.json",
]

PHASE_12_VALIDATION_FILES = [
    PHASE_12_PREREQUISITE_GATE,
    PHASE_12_REQUIRED_ARTIFACTS,
    PHASE_12_FORBIDDEN_LANGUAGE,
    PHASE_12_NON_DESTRUCTIVE_BUDGET,
    PHASE_12_RAVENFALL_EXAMPLES,
    "data/validation/phase_12_acceptance_contract.json",
    "data/validation/phase_12_github_checks_matrix.json",
    "data/validation/phase_12_guardrail_rules.json",
    "data/validation/axiom_content_mapping_rules.json",
    "data/validation/quest_generation_validation_rules.json",
    "data/validation/npc_generation_validation_rules.json",
    "data/validation/lore_generation_validation_rules.json",
    "data/validation/content_provenance_validation_rules.json",
    "data/validation/truth_scope_content_validation_rules.json",
]

PHASE_12_SCAN_PATHS = [
    "docs/architecture/quest_generation_from_axioms_contract.md",
    "docs/architecture/npc_generation_from_branch_context_contract.md",
    "docs/architecture/lore_generation_from_pattern_trace_contract.md",
    "docs/architecture/existential_content_generation_integration_map.md",
    "docs/architecture/quest_npc_lore_truth_boundary_contract.md",
    "docs/architecture/quest_npc_lore_manifest_provenance_contract.md",
    "docs/architecture/content_generation_acceptance_contract.md",
    "docs/architecture/axiom_to_content_pressure_map.md",
    "docs/architecture/quest_npc_lore_generation_v1.md",
]

PHASE_12_ACTIVE_PROMOTED_FILES = [
    "docs/architecture/quest_npc_lore_generation_v1.md",
    "data/schemas/quest_npc_lore_generation_schema.json",
    "data/validation/quest_npc_lore_generation_gate_contract.json",
    "docs/handoff/YWE_PHASE_12_QUEST_NPC_LORE_GENERATION_HANDOFF_2026-05-17.md",
    "scripts/check_quest_npc_lore_generation.py",
]

ALLOWED_LINE_MARKERS = {
    "forbidden",
    "invalid",
    "reject",
    "rejected",
    "rejection",
    "disallow",
    "disallowed",
    "prohibit",
    "prohibited",
    "should_fail_rules",
}

DIRECT_NEGATION_PREFIXES = (
    "do not",
    "must not",
    "should not",
    "may not",
    "does not",
    "cannot",
    "can't",
)

DIRECT_NEGATION_PREFIX_RE = "|".join(re.escape(prefix) for prefix in DIRECT_NEGATION_PREFIXES)
ALLOWED_LINE_MARKER_TOKEN_RE = (
    rf"(?<!\w)(?:{'|'.join(re.escape(marker) for marker in sorted(ALLOWED_LINE_MARKERS))})(?!\w)"
)
DIRECT_NEGATION_CONTEXT_RE = re.compile(
    rf"\b(?:{DIRECT_NEGATION_PREFIX_RE})\b[\w\s\"'`-]{{0,80}}$"
)
ALLOWED_LINE_MARKER_PREFIX_RE = re.compile(
    rf"{ALLOWED_LINE_MARKER_TOKEN_RE}[^.!?;]{{0,80}}$"
)
ALLOWED_LINE_MARKER_SUFFIX_RE = re.compile(
    rf"^[^.!?;]{{0,80}}{ALLOWED_LINE_MARKER_TOKEN_RE}"
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
        errors.append("Unable to resolve git base ref for Phase 12 diff checks.")
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


def budget_limit(budget: dict, key: str, default: int) -> int:
    limits = budget.get("limits")
    raw_value = limits.get(key, default) if isinstance(limits, dict) else budget.get(key, default)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def allowed_forbidden_pattern_reference(pattern: str, line: str) -> bool:
    return allowed_forbidden_pattern_regex_reference(
        re.compile(re.escape(pattern.lower())),
        line.lower(),
    )


def allowed_forbidden_pattern_regex_reference(pattern_re: re.Pattern[str], lowered_line: str) -> bool:
    matches = list(pattern_re.finditer(lowered_line))
    return bool(matches) and all(allowed_forbidden_pattern_occurrence(lowered_line, match) for match in matches)


def allowed_forbidden_pattern_occurrence(lowered_line: str, match: re.Match[str]) -> bool:
    context_start = max(0, match.start() - 80)
    if has_clause_bound_marker(lowered_line, match):
        return True

    prefix_context = lowered_line[context_start:match.start()]
    if DIRECT_NEGATION_CONTEXT_RE.search(prefix_context):
        return True
    return False


def has_clause_bound_marker(lowered_line: str, match: re.Match[str]) -> bool:
    prefix_context = lowered_line[max(0, match.start() - 80):match.start()]
    suffix_context = lowered_line[match.end():min(len(lowered_line), match.end() + 80)]
    return (
        ALLOWED_LINE_MARKER_PREFIX_RE.search(prefix_context) is not None
        or ALLOWED_LINE_MARKER_SUFFIX_RE.search(suffix_context) is not None
    )


def check_forbidden_pattern_exemption_contract(errors: list[str]) -> None:
    pattern = "generic random quest generator"
    allowed_lines = [
        "Forbidden pattern example: generic random quest generator.",
        "Reject generic random quest generator outputs.",
        "Do not use a generic random quest generator.",
        "The generic random quest generator pattern is invalid.",
    ]
    blocked_lines = [
        "This paragraph is not related to a generic random quest generator being active.",
        "Invalid metadata appears here. A generic random quest generator is active.",
        "Forbidden pattern example: generic random quest generator. This line endorses a generic random quest generator.",
    ]
    for line in allowed_lines:
        require(
            allowed_forbidden_pattern_reference(pattern, line),
            f"Phase 12 forbidden-pattern exemption contract rejected explicit context: {line}",
            errors,
        )
    for line in blocked_lines:
        require(
            not allowed_forbidden_pattern_reference(pattern, line),
            f"Phase 12 forbidden-pattern exemption contract allowed incidental context: {line}",
            errors,
        )


def forbidden_pattern_message(root: Path, path: Path, line_number: int, line: str) -> str:
    return f"Forbidden Phase 12 claim found in {relative_name(root, path)}:{line_number}: {line.strip()}"


def check_phase_12_forbidden_pattern_probe(root: Path, errors: list[str]) -> None:
    with tempfile.TemporaryDirectory(prefix="ywe_phase_12_forbidden_probe_") as probe_root:
        probe_dir = Path(probe_root)
        probe_file = probe_dir / "phase_12_probe.md"
        probe_file.write_text(
            "This line is not enough context for a generic random quest generator to be active.\n",
            encoding=TEXT_ENCODING,
        )
        probe_errors: list[str] = []
        check_phase_12_forbidden_patterns_in_paths(root, [probe_dir], ["generic random quest generator"], probe_errors)
        require(bool(probe_errors), "Phase 12 forbidden-pattern probe failed to reject incidental not/context wording.", errors)


def check_phase_12_forbidden_patterns_in_paths(root: Path, scan_roots: list[Path], patterns: list[str], errors: list[str]) -> None:
    prepared_patterns = [
        (pattern.lower(), re.compile(re.escape(pattern.lower())))
        for pattern in patterns
    ]
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".json"}:
                continue
            lines = read_text(path).splitlines()
            for index, line in enumerate(lines):
                lowered = line.lower()
                for pattern_lower, pattern_re in prepared_patterns:
                    if pattern_lower not in lowered:
                        continue
                    if allowed_forbidden_pattern_regex_reference(pattern_re, lowered):
                        continue
                    errors.append(forbidden_pattern_message(root, path, index + 1, line))


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


def collect_json_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel_dir in ("data/schemas", "data/validation", "examples"):
        directory = root / rel_dir
        if directory.is_dir():
            paths.extend(sorted(directory.rglob("*.json")))
    return paths


def field_list(schema: dict, path_name: str, key: str, errors: list[str]) -> set[str]:
    fields = schema.get(key)
    if not isinstance(fields, list) or not all(isinstance(field, str) for field in fields):
        errors.append(f"{path_name} must define {key} as a string list.")
        return set()
    return set(fields)


def require_fields(schema: dict, path_name: str, key: str, required: set[str], errors: list[str]) -> None:
    fields = field_list(schema, path_name, key, errors)
    missing = required - fields
    for field in sorted(missing):
        errors.append(f"{path_name} {key} missing {field}.")


def check_phase_11_prerequisite(root: Path, errors: list[str]) -> None:
    gate = load_json_checked(root, root / PHASE_12_PREREQUISITE_GATE, errors)
    if not isinstance(gate, dict):
        return
    for path_name in gate.get("required_phase_11_artifacts", []):
        require((root / path_name).is_file(), f"Missing Phase 11 prerequisite artifact: {path_name}", errors)


def check_phase_12_required_artifacts(root: Path, errors: list[str]) -> None:
    artifacts = load_json_checked(root, root / PHASE_12_REQUIRED_ARTIFACTS, errors)
    if isinstance(artifacts, dict):
        for section in ("required_markdown", "required_json"):
            for path_name in artifacts.get(section, []):
                require((root / path_name).is_file(), f"Missing Phase 12 required artifact: {path_name}", errors)
        for file_name in artifacts.get("recommended_json", []):
            path_name = f"data/schemas/{file_name}"
            require((root / path_name).is_file(), f"Missing Phase 12 recommended schema: {path_name}", errors)

    for path_name in PHASE_12_VALIDATION_FILES + PHASE_12_CHECK_SPECS:
        require((root / path_name).is_file(), f"Missing Phase 12 validation or check artifact: {path_name}", errors)
    require((root / "conformance/phase-12-existential-quest-npc-lore-generation.md").is_file(), "Missing Phase 12 conformance artifact.", errors)
    require((root / PHASE_12_EXAMPLE_ROOT).is_dir(), f"Missing Phase 12 examples directory: {PHASE_12_EXAMPLE_ROOT}", errors)


def check_phase_12_json_integrity(root: Path, errors: list[str]) -> None:
    for path in collect_json_files(root):
        load_json_checked(root, path, errors)


def check_phase_12_check_spec_references(root: Path, errors: list[str]) -> None:
    scalar_path_keys = ("budget_ref",)
    list_path_keys = ("required_repository_paths",)
    for path_name in PHASE_12_CHECK_SPECS:
        spec = load_json_checked(root, root / path_name, errors)
        if not isinstance(spec, dict):
            continue
        for key in scalar_path_keys:
            ref = spec.get(key)
            if isinstance(ref, str):
                require((root / ref).is_file(), f"{path_name} {key} does not resolve to a repository file: {ref}", errors)
        for key in list_path_keys:
            refs = spec.get(key, [])
            if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
                errors.append(f"{path_name} {key} must be a list of repository-relative paths.")
                continue
            for ref in refs:
                require((root / ref).is_file(), f"{path_name} {key} entry does not resolve to a repository file: {ref}", errors)


def check_phase_12_code_agnostic_schemas(root: Path, errors: list[str]) -> None:
    expected_fields = {
        "data/schemas/quest_generation_context_schema.json": {
            "branch_reality_ref",
            "player_runtime_state_ref",
            "location_state_ref",
            "worldstate_delta_refs",
            "axiom_diagnostic_refs",
            "existence_potential_ref",
            "pattern_vector_refs",
            "plane_pressure_refs",
            "truth_scope",
            "future_generation_bias_refs",
            "provenance",
        },
        "data/schemas/npc_generation_context_schema.json": {
            "branch_reality_ref",
            "player_runtime_state_ref",
            "location_state_ref",
            "worldstate_delta_refs",
            "axiom_diagnostic_refs",
            "existence_potential_ref",
            "pattern_vector_ref",
            "relation_graph_ref",
            "truth_scope",
            "provenance",
        },
        "data/schemas/lore_generation_context_schema.json": {
            "branch_reality_ref",
            "player_runtime_state_ref",
            "location_state_ref",
            "pattern_trace_ref",
            "source_worldstate_delta_refs",
            "axiom_diagnostic_refs",
            "existence_potential_ref",
            "truth_scope",
            "visibility_rule_ref",
            "provenance",
        },
        "data/schemas/generated_lore_fragment_schema.json": {
            "lore_fragment_id",
            "lore_kind",
            "pattern_trace_ref",
            "source_axiom_pressure_refs",
            "source_worldstate_delta_refs",
            "source_branch_refs",
            "source_location_refs",
            "truth_scope",
            "visibility_conditions",
            "generated_text_policy",
            "provenance",
        },
        "data/schemas/content_generation_provenance_schema.json": {
            "provenance_id",
            "cosmology_source_ref",
            "branch_context_ref",
            "player_runtime_state_ref",
            "worldstate_or_location_ref",
            "existence_potential_ref",
            "pattern_vector_refs",
            "truth_scope",
        },
        "data/schemas/quest_manifest_candidate_schema.json": {
            "quest_candidate_id",
            "source_axiom_pressure_refs",
            "source_branch_context_refs",
            "source_player_context_refs",
            "source_location_context_refs",
            "source_worldstate_delta_refs",
            "truth_scope",
            "expected_consequence_classes",
            "content_provenance",
        },
        "data/schemas/npc_manifest_candidate_schema.json": {
            "npc_candidate_id",
            "relation_graph_ref",
            "branch_context_ref",
            "location_context_ref",
            "pattern_vector_ref",
            "existence_potential_ref",
            "truth_scope",
            "self_reference_state_ref",
            "provenance",
        },
    }
    for path_name, required in expected_fields.items():
        schema = load_json_checked(root, root / path_name, errors)
        if not isinstance(schema, dict):
            continue
        require_fields(schema, path_name, "required_fields", required, errors)
        require(isinstance(schema.get("forbidden"), list), f"{path_name} must define forbidden list.", errors)
        require(isinstance(schema.get("validation_notes"), list), f"{path_name} must define validation_notes list.", errors)


def check_phase_12_contract_terms(root: Path, errors: list[str]) -> None:
    combined = "\n".join(
        read_text(root / path_name)
        for path_name in PHASE_12_SCAN_PATHS
        if (root / path_name).is_file()
    ).lower()
    required_terms = [
        "a1",
        "a2",
        "a3",
        "a4",
        "a5",
        "a6",
        "existence potential",
        "pattern vector",
        "branch reality",
        "player runtime state",
        "worldstate delta",
        "location state",
        "truth scope",
        "provenance",
        "axiom pressure",
        "not arbitrary",
    ]
    for term in required_terms:
        require(term in combined, f"Missing Phase 12 contract term: {term}", errors)


def check_phase_12_examples(root: Path, errors: list[str]) -> None:
    rules = load_json_checked(root, root / PHASE_12_RAVENFALL_EXAMPLES, errors)
    example_root = root / PHASE_12_EXAMPLE_ROOT
    if not example_root.is_dir():
        errors.append(f"Missing Phase 12 examples directory: {PHASE_12_EXAMPLE_ROOT}")
        return

    files_by_name = {path.name: path for path in example_root.rglob("*.json")}
    if isinstance(rules, dict):
        for file_name in rules.get("required_examples", []):
            require(file_name in files_by_name, f"Missing Phase 12 Ravenfall Gate example: {file_name}", errors)

    required_by_file = {
        "ravenfall_gate_reveal_oath_quest_generation_context.example.json": {
            "context_id",
            "branch_reality_ref",
            "player_runtime_state_ref",
            "location_state_ref",
            "worldstate_delta_refs",
            "axiom_diagnostic_refs",
            "existence_potential_ref",
            "pattern_vector_refs",
            "truth_scope",
            "provenance",
        },
        "ravenfall_gate_conceal_oath_quest_generation_context.example.json": {
            "context_id",
            "branch_reality_ref",
            "player_runtime_state_ref",
            "location_state_ref",
            "worldstate_delta_refs",
            "axiom_diagnostic_refs",
            "existence_potential_ref",
            "pattern_vector_refs",
            "truth_scope",
            "provenance",
        },
        "ravenfall_gate_witness_npc_candidate.example.json": {
            "npc_candidate_id",
            "relation_graph_ref",
            "branch_context_ref",
            "location_context_ref",
            "pattern_vector_ref",
            "existence_potential_ref",
            "truth_scope",
            "self_reference_state_ref",
            "provenance",
        },
        "ravenfall_gate_keeper_npc_candidate.example.json": {
            "npc_candidate_id",
            "relation_graph_ref",
            "branch_context_ref",
            "location_context_ref",
            "pattern_vector_ref",
            "existence_potential_ref",
            "truth_scope",
            "self_reference_state_ref",
            "provenance",
        },
        "ravenfall_gate_public_oath_lore_fragment.example.json": {
            "lore_fragment_id",
            "lore_kind",
            "pattern_trace_ref",
            "source_axiom_pressure_refs",
            "source_worldstate_delta_refs",
            "source_branch_refs",
            "source_location_refs",
            "truth_scope",
            "visibility_conditions",
            "generated_text_policy",
            "provenance",
        },
        "ravenfall_gate_hidden_oath_lore_fragment.example.json": {
            "lore_fragment_id",
            "lore_kind",
            "pattern_trace_ref",
            "source_axiom_pressure_refs",
            "source_worldstate_delta_refs",
            "source_branch_refs",
            "source_location_refs",
            "truth_scope",
            "visibility_conditions",
            "generated_text_policy",
            "provenance",
        },
    }
    for file_name, required in required_by_file.items():
        path = files_by_name.get(file_name)
        if path is None:
            continue
        data = load_json_checked(root, path, errors)
        if not isinstance(data, dict):
            continue
        missing = required - set(data.keys())
        for field in sorted(missing):
            errors.append(f"{path.relative_to(root).as_posix()} missing required field: {field}")

    for path in example_root.rglob("*.json"):
        data = load_json_checked(root, path, errors)
        if not isinstance(data, dict):
            continue
        if "invalid" in path.name:
            require("should_fail_rules" in data, f"{path.relative_to(root).as_posix()} must list should_fail_rules.", errors)


def check_phase_12_forbidden_patterns(root: Path, errors: list[str]) -> None:
    data = load_json_checked(root, root / PHASE_12_FORBIDDEN_LANGUAGE, errors)
    if not isinstance(data, dict):
        return

    scan_roots = [
        root / "docs/architecture",
        root / "data/schemas",
        root / "examples/phase_12_quest_npc_lore_generation",
    ]
    patterns = [
        item.get("pattern", "")
        for item in data.get("forbidden_patterns", [])
        if isinstance(item, dict) and isinstance(item.get("pattern"), str)
    ]
    check_phase_12_forbidden_patterns_in_paths(root, scan_roots, patterns, errors)


def check_phase_12_non_destructive_diff(root: Path, errors: list[str]) -> None:
    budget = load_json_checked(root, root / PHASE_12_NON_DESTRUCTIVE_BUDGET, errors)
    if not isinstance(budget, dict):
        return
    deleted, renamed, copied, existing_touched = classify_change_paths(git_change_paths(root, errors))

    max_deleted = budget_limit(budget, "max_existing_file_deletions", 0)
    max_renamed = budget_limit(budget, "max_directory_renames", 0)
    max_copied = budget_limit(budget, "max_copied_paths", 0)
    max_touched = budget_limit(budget, "max_existing_files_touched_without_review", 25)

    require(len(deleted) <= max_deleted, f"Phase 12 file deletions exceed budget {max_deleted}: {deleted}", errors)
    require(len(renamed) <= max_renamed, f"Phase 12 renamed paths exceed budget {max_renamed}: {renamed}", errors)
    require(len(copied) <= max_copied, f"Phase 12 copied paths exceed budget {max_copied}: {copied}", errors)
    require(
        len(existing_touched) <= max_touched,
        f"Phase 12 existing files touched exceed budget {max_touched}: {len(existing_touched)}",
        errors,
    )


def check_phase_12_promoted_boundary(root: Path, errors: list[str]) -> None:
    marker = "DEFERRED - Phase 9 boundary violation; " + "do not consume until the matching owner-approved package is accepted."
    for path_name in PHASE_12_ACTIVE_PROMOTED_FILES:
        path = root / path_name
        if not path.is_file():
            continue
        require(marker not in read_text(path), f"{path_name} still contains Phase 12 deferred marker.", errors)


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
    check_phase_11_prerequisite(root, errors)
    check_phase_12_required_artifacts(root, errors)
    check_phase_12_json_integrity(root, errors)
    check_phase_12_check_spec_references(root, errors)
    check_phase_12_code_agnostic_schemas(root, errors)
    check_phase_12_contract_terms(root, errors)
    check_phase_12_examples(root, errors)
    check_forbidden_pattern_exemption_contract(errors)
    check_phase_12_forbidden_pattern_probe(root, errors)
    check_phase_12_forbidden_patterns(root, errors)
    check_phase_12_non_destructive_diff(root, errors)
    check_phase_12_promoted_boundary(root, errors)

    if errors:
        print("Quest NPC Lore Generation check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Quest NPC Lore Generation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
