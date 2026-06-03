#!/usr/bin/env python3
"""Validate Phase 15A companion and reward foundation artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

TEXT_ENCODING = "utf-8-sig"

REQUIRED_ARTIFACTS = "data/validation/phase_15a_required_artifacts.json"
ACCEPTANCE_CONTRACT = "data/validation/phase_15a_acceptance_contract.json"
PHASE_15A_VALIDATION_FILES = [
    "data/validation/check_wrw_er_game_identity_lock.spec.json",
    "data/validation/check_raven_companion_persistent_presence.spec.json",
    "data/validation/check_wolf_conditional_manifestation.spec.json",
    "data/validation/check_quest_reward_resolver_foundation.spec.json",
    "data/validation/check_no_platform_runtime_code_phase_15a.spec.json",
    "data/validation/phase_15a_forbidden_language_patterns.json",
    REQUIRED_ARTIFACTS,
    ACCEPTANCE_CONTRACT,
]

PHASE_15A_EXAMPLES = [
    "examples/companions/raven_companion_floki_initial_state.example.json",
    "examples/companions/wolf_manifestation_event_ravenfall_gate_buried_oath.example.json",
    "examples/quest_reward_resolver/ravenfall_gate_reveal_oath_reward_resolution.example.json",
    "examples/quest_reward_resolver/ravenfall_gate_conceal_oath_reward_resolution.example.json",
    "examples/quest_reward_resolver/consequence_resolution_reveal_oath.example.json",
    "examples/quest_reward_resolver/invalid_always_present_wolves.example.json",
    "examples/quest_reward_resolver/invalid_reward_without_consequence_packet.example.json",
]

PHASE_15A_MODULE_FILES = [
    "modules/companion_engine/README.md",
    "modules/companion_engine/engine_interface.json",
    "modules/companion_engine/companion_presence_rules_model.json",
    "modules/companion_engine/raven_companion_rules_model.json",
    "modules/companion_engine/wolf_manifestation_rules_model.json",
    "modules/quest_engine/quest_reward_resolver_rules_model.json",
    "modules/quest_engine/companion_reward_routing_rules_model.json",
]

PHASE_15A_CROSS_REFERENCE_FILES = [
    "docs/architecture/player_runtime_state_contract.md",
    "data/schemas/player_runtime_state_schema.json",
    "docs/architecture/twin_wolf_companion_canon_contract.md",
    "docs/architecture/ability_wolf_companion_integration_contract.md",
    "docs/architecture/quest_npc_lore_generation_v1.md",
    "docs/master_specification/YWE_MASTER_SPECIFICATION.md",
    "docs/glossary/ywe_design_glossary.md",
    "README.md",
]

FORBIDDEN_PLATFORM_EXTENSIONS = (".swift", ".metal", ".xcodeproj", ".xcworkspace")


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


def load_json_checked(root: Path, rel_path: str, errors: list[str]):
    path = root / rel_path
    if not path.is_file():
        errors.append(f"Missing required JSON file: {rel_path}")
        return None
    try:
        return load_json(path)
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid JSON in {rel_path}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        errors.append(f"Unable to read {rel_path}: {exc}")
    return None


def require_file(root: Path, rel_path: str, errors: list[str]) -> None:
    require((root / rel_path).is_file(), f"Missing Phase 15A artifact: {rel_path}", errors)


def git_changed_paths(root: Path) -> list[str]:
    paths: set[str] = set()
    commands = [
        ["git", "-C", str(root), "diff", "--name-only", "--find-renames", "origin/main...HEAD"],
        ["git", "-C", str(root), "diff", "--name-only"],
        ["git", "-C", str(root), "diff", "--cached", "--name-only"],
        ["git", "-C", str(root), "ls-files", "--others", "--exclude-standard"],
    ]
    for command in commands:
        try:
            result = subprocess.run(command, check=False, capture_output=True, text=True)
        except OSError:
            continue
        if result.returncode == 0:
            paths.update(line.strip() for line in result.stdout.splitlines() if line.strip())
    return sorted(paths)


def check_required_artifacts(root: Path, errors: list[str]) -> None:
    required = load_json_checked(root, REQUIRED_ARTIFACTS, errors)
    if isinstance(required, dict):
        for rel_path in required.get("required_files", []):
            require_file(root, rel_path, errors)
    for rel_path in PHASE_15A_VALIDATION_FILES + PHASE_15A_EXAMPLES + PHASE_15A_MODULE_FILES:
        require_file(root, rel_path, errors)


def check_game_identity(root: Path, errors: list[str]) -> None:
    manifest = load_json_checked(
        root,
        "data/game/where_ravens_wait_eternal_reckoning/game_identity_manifest.json",
        errors,
    )
    if not isinstance(manifest, dict):
        return
    identity = manifest.get("game_identity", {})
    boundary = identity.get("repository_boundary", {})
    position = manifest.get("canonical_position", {})
    require(identity.get("title") == "Where Ravens Wait: Eternal Reckoning", "WRW:ER title is not locked.", errors)
    require(identity.get("genre") == "single_player_rpg", "WRW:ER genre must be single_player_rpg.", errors)
    require(boundary.get("ywe_repository") == "agnostic_engine_blueprint", "YWE repository boundary must remain agnostic.", errors)
    require(
        position.get("where_ravens_wait_eternal_reckoning") == "first_single_player_rpg_built_with_ywe",
        "WRW:ER must be recorded as the first single-player RPG built with YWE.",
        errors,
    )


def check_campaign_identity(root: Path, errors: list[str]) -> None:
    manifest = load_json_checked(
        root,
        "data/game/where_ravens_wait_eternal_reckoning/campaign_identity_manifest.json",
        errors,
    )
    if not isinstance(manifest, dict):
        return
    model = manifest.get("campaign_identity_model", {})
    first_campaign = model.get("canonical_first_campaign", {})
    require(model.get("initial_mode") == "canonical_nathruun_campaign", "Initial mode must be Nathruun campaign.", errors)
    require("custom_wrw_origin" in model.get("locked_at_game_start", []), "Custom-origin mode must be locked at game start.", errors)
    require(first_campaign.get("player_identity") == "nathruun", "Canonical first campaign player identity must be Nathruun.", errors)
    require(
        first_campaign.get("persistent_raven_companion") == "floki_hrafen_vilgerson",
        "Floki must be Nathruun's persistent Raven Companion.",
        errors,
    )


def check_raven_companion(root: Path, errors: list[str]) -> None:
    example = load_json_checked(root, "examples/companions/raven_companion_floki_initial_state.example.json", errors)
    if isinstance(example, dict):
        require(example.get("companion_id") == "floki_hrafen_vilgerson", "Floki example companion_id is incorrect.", errors)
        require(example.get("display_name") == "Floki", "Floki example display_name is incorrect.", errors)
        require(example.get("presence_rule") == "always_with_player", "Raven Companion must always be with player.", errors)
        require(example.get("bound_player_identity") == "nathruun", "Floki must be bound to Nathruun.", errors)
        layers = set(example.get("identity_layers", []))
        require({"raven_companion", "ancestor", "historical_identity", "bloodline_memory_vector"} <= layers, "Floki identity layers are incomplete.", errors)

    player_schema = load_json_checked(root, "data/schemas/player_runtime_state_schema.json", errors)
    if isinstance(player_schema, dict):
        state_refs = player_schema.get("properties", {}).get("state_refs", {}).get("properties", {})
        require("raven_companion_state_ref" in state_refs, "PlayerRuntimeState.state_refs must expose raven_companion_state_ref.", errors)
        require("wolf_manifestation_event_refs" in state_refs, "PlayerRuntimeState.state_refs must expose wolf_manifestation_event_refs.", errors)


def check_wolf_manifestation(root: Path, errors: list[str]) -> None:
    example = load_json_checked(root, "examples/companions/wolf_manifestation_event_ravenfall_gate_buried_oath.example.json", errors)
    if isinstance(example, dict):
        trigger = example.get("manifestation_trigger", {})
        duration = example.get("manifestation_duration", {})
        forbidden = set(example.get("forbidden_interpretations", []))
        require(trigger.get("trigger_type") == "quest_chain_requirement", "Wolf manifestation trigger must be quest-chain grounded.", errors)
        require(bool(trigger.get("criteria_met")), "Wolf manifestation trigger must include criteria_met.", errors)
        require(duration.get("duration_type") == "entire_quest_chain", "Ravenfall Gate wolf duration must be quest-chain scoped.", errors)
        require(duration.get("ends_at") != "never", "Wolf manifestation cannot have an unbounded never-ending duration.", errors)
        require(
            {"morality_meter", "good_vs_evil_binary", "default_party_member", "generic_pet_system", "permanent_wolf_loss"} <= forbidden,
            "Wolf manifestation forbidden interpretations are incomplete.",
            errors,
        )

    invalid_example = load_json_checked(root, "examples/quest_reward_resolver/invalid_always_present_wolves.example.json", errors)
    if isinstance(invalid_example, dict):
        trigger = invalid_example.get("manifestation_trigger", {})
        duration = invalid_example.get("manifestation_duration", {})
        require(invalid_example.get("validation_status") == "invalid", "Invalid always-present wolves example must be marked invalid.", errors)
        require(trigger.get("criteria_met") == [], "Invalid always-present wolves example must carry empty criteria.", errors)
        require(duration.get("ends_at") == "never", "Invalid always-present wolves example must show unbounded duration.", errors)


def check_quest_reward(root: Path, errors: list[str]) -> None:
    valid_examples = [
        "examples/quest_reward_resolver/ravenfall_gate_reveal_oath_reward_resolution.example.json",
        "examples/quest_reward_resolver/ravenfall_gate_conceal_oath_reward_resolution.example.json",
    ]
    for rel_path in valid_examples:
        packet = load_json_checked(root, rel_path, errors)
        if not isinstance(packet, dict):
            continue
        require(packet.get("consequence_resolution_packet_ref"), f"{rel_path} lacks consequence_resolution_packet_ref.", errors)
        require(bool(packet.get("source_refs")), f"{rel_path} lacks source_refs.", errors)
        outputs = packet.get("reward_outputs", {})
        for field in ("player_state_update_refs", "companion_state_delta_refs", "worldstate_delta_refs", "location_mutation_refs"):
            require(bool(outputs.get(field)), f"{rel_path} lacks reward output field {field}.", errors)

    consequence = load_json_checked(root, "examples/quest_reward_resolver/consequence_resolution_reveal_oath.example.json", errors)
    if isinstance(consequence, dict):
        routes = consequence.get("routes", [])
        route_types = {route.get("route_type") for route in routes if isinstance(route, dict)}
        require(consequence.get("cause_ref") == "quest_reward.ravenfall_gate.reveal_oath.v1", "Consequence packet cause_ref is incorrect.", errors)
        require({"player_state", "raven_companion_state", "wolf_manifestation", "worldstate_delta", "location_mutation"} <= route_types, "Consequence routes are incomplete.", errors)

    invalid = load_json_checked(root, "examples/quest_reward_resolver/invalid_reward_without_consequence_packet.example.json", errors)
    if isinstance(invalid, dict):
        require(invalid.get("validation_status") == "invalid", "Invalid reward example must be marked invalid.", errors)
        require(invalid.get("consequence_resolution_packet_ref") == "", "Invalid reward example must have empty consequence ref.", errors)


def check_cross_references(root: Path, errors: list[str]) -> None:
    required_terms = {
        "docs/architecture/player_runtime_state_contract.md": ["raven_companion_state_ref", "wolf_manifestation_event_refs"],
        "docs/architecture/twin_wolf_companion_canon_contract.md": ["conditional manifestations", "not default party members"],
        "docs/architecture/ability_wolf_companion_integration_contract.md": ["manifested"],
        "docs/architecture/quest_npc_lore_generation_v1.md": ["Quest Reward Resolver"],
        "docs/master_specification/YWE_MASTER_SPECIFICATION.md": ["Floki", "QuestRewardResolutionPacket"],
        "docs/glossary/ywe_design_glossary.md": ["Raven Companion", "Floki Hrafen Vilgerson", "Quest Reward Resolver"],
        "README.md": ["Phase 15A", "Raven Companion", "Quest Reward Resolver"],
    }
    for rel_path, terms in required_terms.items():
        path = root / rel_path
        if not path.is_file():
            errors.append(f"Missing cross-reference target: {rel_path}")
            continue
        text = read_text(path)
        for term in terms:
            require(term in text, f"Missing Phase 15A term `{term}` in {rel_path}", errors)


def check_no_platform_runtime_code(root: Path, errors: list[str]) -> None:
    changed_paths = git_changed_paths(root)
    for rel_path in changed_paths:
        lower_path = rel_path.lower()
        if lower_path.endswith(FORBIDDEN_PLATFORM_EXTENSIONS):
            errors.append(f"Phase 15A added forbidden platform runtime artifact: {rel_path}")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []

    for rel_path in PHASE_15A_CROSS_REFERENCE_FILES:
        require_file(root, rel_path, errors)
    check_required_artifacts(root, errors)
    check_game_identity(root, errors)
    check_campaign_identity(root, errors)
    check_raven_companion(root, errors)
    check_wolf_manifestation(root, errors)
    check_quest_reward(root, errors)
    check_cross_references(root, errors)
    check_no_platform_runtime_code(root, errors)

    if errors:
        print("Phase 15A companion and reward foundation check failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Phase 15A companion and reward foundation check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
