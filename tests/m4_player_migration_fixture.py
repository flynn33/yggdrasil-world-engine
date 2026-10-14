"""Explicit synthetic source/qualification pairs for both legacy player forms."""

import copy
import hashlib
import json

from core.narrative_engine.origin_progression import OriginProgressionPolicy
from core.player_state import PlayerStateStore
from core.player_state_migration import CONTEXT_FIELDS, PlayerStateMigration, SOURCE_SCHEMAS, TARGET_SCHEMAS
from tests.m4_player_fixture import (
    BRANCH, PLAYER, PRINCIPAL, WORLD, configuration, document, evidence, provenance, record, reference,
)


def encode(source):
    return json.dumps(source, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def inputs(adapter_id="closed_reference_v1", continuing=False):
    """Return raw, source schemas, target schemas, resolution, old configuration.

    The catalog is synthetic qualified composition input. Continuing history is
    obtained by an actual existing v2 transaction, not fabricated receipts.
    """
    old = list(configuration())
    owner = PlayerStateStore(*old)
    if continuing:
        owner.publish(owner.writer(PRINCIPAL), "request:historical:first", 0, "update:first")
    state = owner.state()
    spine = copy.deepcopy(state["spine"])
    spine.update(schema_id="ywe.player_runtime_state.v3", schema_version="3.0.0")
    spine["update_control"]["allowed_update_packet_schema"] = "ywe.player_state_update_packet.v3"
    origin = state["records"][spine["origin_progression_state_ref"]]["document"]
    records = copy.deepcopy(old[5])
    existing = {row["ref"] for row in records}
    for ref, entry in state["records"].items():
        if entry["kind"] == "origin" or ref in existing:
            continue
        records.append(record(ref, entry["kind"], entry["document"], entry["document"].get("branch_ref", BRANCH)))
    source = copy.deepcopy(spine)
    source.update(schema_id="ywe.player_runtime_state.v1", schema_version="0.1.0")
    source.pop("origin_progression_state_ref")
    source.pop("ability_state_refs")
    source["state_refs"].pop("raven_companion_state_ref")
    source["update_control"]["allowed_update_packet_schema"] = "ywe.player_state_update_packet.v1"
    mapping = {"profile_id": old[2]["profile_id"], "mappings": {"physical": "P1_Physical", "mental": "P4_Mental"}}
    if adapter_id == "historical_record_v1":
        source = document("examples/player_runtime_state/player_runtime_state_initial.example.json")
        source.update(player_ref=PLAYER, current_leaf_branch_ref=BRANCH, current_phase=origin["current_phase"],
                      sequence_id=12 if continuing else 0, phase_confidence=0.875 if continuing else 1.0,
                      celestial_memory="suspected" if continuing else "veiled")
        by_ref = {row["ref"]: row["document"] for row in records}
        plane = by_ref[spine["state_refs"]["plane_attunement_state_ref"]]
        wolf = by_ref[spine["state_refs"]["wolf_resonance_summary_ref"]]
        source["realm_attunement"] = {"physical": plane["planes"]["P1_Physical"]["score_q6"] / 1000000,
                                      "mental": plane["planes"]["P4_Mental"]["score_q6"] / 1000000}
        source["wolf_resonance"] = {"white_wolf": wolf["white_wolf"]["resonance_q6"] / 1000000,
                                    "dark_wolf": wolf["dark_wolf"]["resonance_q6"] / 1000000,
                                    "interpretation": "symbiotic_attractors_not_morality_meter"}
        if continuing:
            source.update(active_quest_refs=["quest:second", "quest:first"],
                          unresolved_tension_refs=["tension:second", "tension:first"],
                          narrative_memory_refs=["legacy:memory:one"], generation_context_refs=["generation:one"],
                          last_player_action_trace_ref=origin["actions"][-1]["action_trace_id"])
        context = {key: copy.deepcopy(value) for key, value in source.items() if key in CONTEXT_FIELDS}
        context["phase_confidence"] = {"coefficient": "875", "exponent": -3} if continuing else {"coefficient": "1", "exponent": 0}
        context["wolf_interpretation"] = source["wolf_resonance"]["interpretation"]
        spine["runtime_context"] = context
        records.append(reference("physical", "active_realm_form", "leaf_branch_state", BRANCH))
        records.append(reference(source["perception_state_ref"], "perception_state_ref", "player_perception"))
        for field in ("branch_generation_context_refs", "narrative_memory_refs", "active_quest_refs",
                      "unresolved_tension_refs", "generation_context_refs"):
            records.extend(reference(ref, field) for ref in source[field])
        for field, value in source["ash_provenance"].items():
            for ref in value if type(value) is list else [value]:
                records.append(reference(ref, field))
    raw = encode(source)
    resolution = {"format": "ywe.player_migration_resolution.v1", "source_sha256": hashlib.sha256(raw).hexdigest(),
        "world_id": WORLD, "player_id": PLAYER, "player_profile": copy.deepcopy(old[2]),
        "origin_profile": document("data/profiles/wrw_origin_progression.json")["profile"],
        "spine": spine, "creation": origin["creation"], "current_phase": origin["current_phase"],
        "action_refs": [row["action_trace_id"] for row in origin["actions"]],
        "memory_refs": [row["memory_id"] for row in origin["memories"]],
        "consumed_action_refs": [row["action_trace_id"] for row in origin["actions"]],
        "records": records, "consumed_updates": [{"update_ref": "update:first", "consequence_ref": "consequence:first"}] if continuing else [],
        "consumed_request_refs": ["request:historical:first"] if continuing else [],
        "consumed_manifestation_event_ids": [], "manifestation_bindings": [],
        "realm_name_map": mapping, "fragment_bindings": [], "provenance": provenance()}
    sources = {key: document("data/schemas/" + name + ".json") for key, name in SOURCE_SCHEMAS.items()}
    targets = {key: document("data/schemas/" + name + ".json") for key, name in TARGET_SCHEMAS.items()}
    return raw, sources, targets, resolution, old


def configuration_for(result, resolution, targets, old):
    """Compose the actual nine-argument store configuration for a verified import."""
    args = list(old)
    args[0:4] = [resolution["world_id"], resolution["player_id"], resolution["player_profile"], result["baseline"]["spine"]]
    args[5] = resolution["records"]
    args[7] = {key: value for key, value in targets.items() if key not in ("origin", "snapshot")}
    first = evidence("origin:first", "update:first")
    second = evidence("origin:second", "update:second", "first_stirrings", "first_stirrings", 1, "remember")
    args[8] = OriginProgressionPolicy.from_baseline(result["origin_baseline"], resolution["world_id"], resolution["player_id"],
        resolution["origin_profile"], resolution["creation"], {PRINCIPAL: ["advance", "remember"]}, [first, second],
        targets["action"], targets["memory"])
    return tuple(args)


def build(adapter_id="closed_reference_v1", continuing=False):
    """Return (raw source bytes, migration, result, nine-argument configuration)."""
    raw, sources, targets, resolution, old = inputs(adapter_id, continuing)
    migration = PlayerStateMigration(adapter_id, sources, targets, resolution)
    result = migration.migrate(raw)
    return raw, migration, result, configuration_for(result, resolution, targets, old)
