"""Fresh, internally coherent qualification inputs for player admission tests.

These records are synthetic trusted-host inputs, not historical saves or proof
of remote authentication. Terminal digests hash the exact synthetic source
returned by ``reference_source``; no world or branch writer is exercised.
"""

import copy
import hashlib
import json
from pathlib import Path

from core.narrative_engine.origin_progression import OriginProgressionPolicy
from core.state_journal import _object_bytes


ROOT = Path(__file__).resolve().parents[1]
WORLD, PLAYER, BRANCH = "world:one", "player:one", "branch:one"
PRINCIPAL = "narrative:owner"
SOURCE = "narrative_engine"


def document(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def provenance():
    return {"cosmic_pattern_snapshot_ref": "snapshot:player", "diagnostic_ref": "diagnostic:player",
            "generation_plan_ref": "plan:player", "source_ash_refs": ["ash:canonical"]}


def record(ref, kind, value, branch=BRANCH):
    return {"ref": ref, "kind": kind, "world_id": WORLD, "player_id": PLAYER,
            "branch_ref": branch, "document": copy.deepcopy(value), "provenance": provenance()}


def reference_source(ref, category, truth_scope, subject_id):
    return {"fixture_source": ref, "category": category, "world_id": WORLD,
            "truth_scope": truth_scope, "subject_id": subject_id}


def reference(ref, category, truth_scope="player_state", subject_id=PLAYER, branch=BRANCH):
    source = reference_source(ref, category, truth_scope, subject_id)
    return record(ref, "reference", {"category": category, "truth_scope": truth_scope,
        "subject_id": subject_id, "source_sha256": hashlib.sha256(_object_bytes(source)).hexdigest()}, branch)


def evidence(name, update_ref, prior="mortal_unknowing", target="first_stirrings",
             count=2, operation="advance", branch=BRANCH):
    actions, memories = [], []
    for index in range(count):
        action_id = name + ":action:" + str(index)
        actions.append({"schema_id": "ywe.player_action_trace.v1", "schema_version": "0.1.0",
            "action_trace_id": action_id, "player_id": PLAYER, "action_kind": "choice",
            "significance": "meaningful", "branch_relevance": "contextual", "branch_ref": branch,
            "resulting_player_state_update_refs": [update_ref], "source_refs": ["evidence:play"]})
        memories.append({"schema_id": "ywe.player_memory_record.v1", "schema_version": "0.1.0",
            "memory_id": name + ":memory:" + str(index), "memory_kind": "identity_memory",
            "visibility_state": "felt", "source_action_trace_ref": action_id, "branch_ref": branch,
            "source_refs": ["qualified:play"]})
    return {"evidence_ref": name, "world_id": WORLD, "player_id": PLAYER,
        "operation": operation, "prior_phase": prior, "target_phase": target,
        "actions": actions, "memories": memories, "provenance": provenance()}


def consequence(name, update_ref, source, branch=BRANCH):
    return record(name, "consequence", {"consequence_id": name, "effect_id": name + ":effect",
        "update_ref": update_ref, "player_id": PLAYER, "branch_ref": branch,
        "action_refs": [item["action_trace_id"] for item in source["actions"]],
        "external_result_refs": []}, branch)


def configuration():
    """Return all nine PlayerStateStore arguments, freshly detached per call."""
    profile = document("data/profiles/wrw_player_progression.json")
    names = {"spine": "m4_player_runtime_state", "celestial": "celestial_identity_state",
        "agent": "player_agent_state", "branch_history": "player_branch_history",
        "plane": "m4_plane_attunement_state", "bloodline": "m4_bloodline_resonance_state",
        "wolf": "m4_wolf_resonance_summary", "raven": "raven_companion_state",
        "ability": "m4_ability_state", "manifestation": "wolf_manifestation_event",
        "action": "player_action_trace", "memory": "player_memory_record"}
    schemas = {kind: document("data/schemas/" + name + "_schema.json") for kind, name in names.items()}
    spine = document("examples/player_runtime_state/player_runtime_state_initial_mortal_veiled.example.json")
    spine.update(schema_id="ywe.player_runtime_state.v2", schema_version="2.0.0", player_id=PLAYER,
        current_leaf_branch_ref=BRANCH, current_location_ref="location:one",
        origin_progression_state_ref="origin:one", ability_state_refs=[])
    spine["identity"] = {"mortal_identity_ref": "identity:mortal",
        "celestial_identity_state_ref": "celestial:initial", "celestial_identity_initial_state": "veiled"}
    spine["state_refs"] = {"player_agent_state_ref": "agent:initial",
        "plane_attunement_state_ref": "plane:initial", "bloodline_resonance_state_ref": "bloodline:initial",
        "wolf_resonance_summary_ref": "wolf:initial", "player_branch_history_ref": "history:initial",
        "raven_companion_state_ref": "raven:initial", "wolf_manifestation_event_refs": [],
        "companion_reward_delta_refs": []}
    spine["asp_resilience"] = {"state_integrity_status": "valid", "asp_diagnostic_refs": ["diagnostic:initial"],
        "recovery_status": "none", "schema_version_history": ["2.0.0"]}
    spine["update_control"]["allowed_update_packet_schema"] = "ywe.player_state_update_packet.v2"
    celestial = {"schema_id": "ywe.celestial_identity_state.v1", "schema_version": "0.1.0",
        "identity_state": "veiled", "reveal_status": "not_revealed", "known_fragments": [],
        "evidence_refs": [], "forbidden": ["full_celestial_identity_at_character_creation",
            "identity_reveal_without_provenance"]}
    agent = {"schema_id": "ywe.player_agent_state.v1", "schema_version": "0.1.0",
        "agent_id": "agent:initial", "agent_kind": "player_mortal_instance",
        "mortal_instance_id": "identity:mortal", "current_leaf_branch_ref": BRANCH,
        "current_location_ref": "location:one", "self_reference_status": "veiled_self_model",
        "choice_capacity_status": "ordinary_choice_capacity", "recent_action_trace_refs": [],
        "branch_event_refs": [], "asp_resilience": {"state_integrity_status": "valid", "asp_diagnostic_refs": ["diagnostic:initial"]}}
    history = {"schema_id": "ywe.player_branch_history.v1", "schema_version": "0.1.0",
        "player_id": PLAYER, "current_leaf_branch_ref": BRANCH, "entries": []}
    plane_names = schemas["plane"]["properties"]["planes"]["required"]
    plane = {"schema_id": "ywe.plane_attunement_state.v2", "schema_version": "2.0.0",
        "planes": {name: {"score_q6": 10000, "pressure_state": "latent", "trend": "stable",
            "source_refs": ["qualified:creation"]} for name in plane_names},
        "dominant_plane_refs": [], "threshold_access_flags": [], "source_refs": ["qualified:creation"]}
    bloodline = {"schema_id": "ywe.bloodline_resonance_state.v2", "schema_version": "2.0.0",
        "signals": [{"bloodline_id": "lineage:seed", "status": "unknown", "score_q6": 10000,
            "stability": "stable", "revealed_to_player": False, "known_publicly": False,
            "source_refs": ["qualified:creation"]}], "source_refs": ["qualified:creation"]}
    wolf = {"schema_id": "ywe.wolf_resonance_summary.v2", "schema_version": "2.0.0",
        "white_wolf": {"resonance_q6": 10000, "signal_state": "latent", "source_refs": ["qualified:creation"]},
        "dark_wolf": {"resonance_q6": 10000, "signal_state": "latent", "source_refs": ["qualified:creation"]},
        "twin_coherence": {"coherence_q6": 500000, "coherence_state": "balanced", "source_refs": ["qualified:creation"]},
        "source_refs": ["qualified:creation"], "forbidden": ["wolf_morality_meter"]}
    raven = {"schema_id": "raven_companion_state_schema", "version": "1.0.0",
        "companion_id": profile["raven_companion_id"], "display_name": "Floki",
        "presence_rule": "always_with_player", "runtime_status": "active",
        "bound_player_identity": "identity:mortal", "identity_layers": ["player_bound_companion"],
        "primary_functions": ["threshold_recognition"], "absence_rule": "explicit_consequence_required",
        "source_refs": ["qualified:creation"]}
    records = [record(ref, kind, value) for ref, kind, value in (
        ("celestial:initial", "celestial", celestial), ("agent:initial", "agent", agent),
        ("history:initial", "branch_history", history), ("plane:initial", "plane", plane),
        ("bloodline:initial", "bloodline", bloodline), ("wolf:initial", "wolf", wolf),
        ("raven:initial", "raven", raven))]
    records.extend([reference("identity:mortal", "mortal_identity_ref"),
        reference(BRANCH, "current_leaf_branch_ref", "leaf_branch_state", BRANCH),
        reference("location:one", "current_location_ref", "leaf_branch_state", BRANCH),
        reference("diagnostic:initial", "asp_diagnostic_refs"),
        reference("evidence:play", "evidence_refs")])
    first = evidence("origin:first", "update:first")
    second = evidence("origin:second", "update:second", "first_stirrings", "first_stirrings", 1, "remember")
    suspected = copy.deepcopy(celestial)
    suspected.update(identity_state="suspected", reveal_status="player_suspects", evidence_refs=["evidence:play"])
    stirring = copy.deepcopy(plane)
    stirring["planes"]["P4_Mental"].update(score_q6=20000, pressure_state="rising", trend="increasing",
        source_refs=["qualified:play"])
    stirring["source_refs"] = ["qualified:creation", "qualified:play"]
    remembered = copy.deepcopy(stirring)
    remembered["planes"]["P4_Mental"]["score_q6"] = 30000
    ability = {"schema_id": "ywe.ability_state.v2", "schema_version": "2.0.0",
        "ability_id": "ability:oath", "player_id": PLAYER, "branch_ref": BRANCH,
        "current_state": "latent", "source_refs": ["evidence:play"], "history_refs": [], "sealed_reason_refs": []}
    records.extend([record("celestial:suspected", "celestial", suspected), record("plane:stirring", "plane", stirring),
        record("plane:remembered", "plane", remembered), record("ability:latent", "ability", ability),
        consequence("consequence:first", "update:first", first), consequence("consequence:second", "update:second", second)])
    updates = [{"update_ref": "update:first", "world_id": WORLD, "player_id": PLAYER, "branch_ref": BRANCH,
        "source_system": SOURCE, "operations": [{"kind": "origin", "evidence_ref": "origin:first"},
            {"kind": "replace", "slot": "celestial", "previous_ref": "celestial:initial", "next_ref": "celestial:suspected", "condition_refs": []},
            {"kind": "replace", "slot": "plane", "previous_ref": "plane:initial", "next_ref": "plane:stirring", "condition_refs": []},
            {"kind": "ability", "ability_id": "ability:oath", "previous_ref": None,
                "next_ref": "ability:latent", "condition_refs": []}],
        "evidence_refs": ["evidence:play"], "consequence_ref": "consequence:first", "provenance": provenance()},
        {"update_ref": "update:second", "world_id": WORLD, "player_id": PLAYER, "branch_ref": BRANCH,
        "source_system": SOURCE, "operations": [{"kind": "origin", "evidence_ref": "origin:second"},
            {"kind": "replace", "slot": "plane", "previous_ref": "plane:stirring", "next_ref": "plane:remembered", "condition_refs": []}],
        "evidence_refs": ["evidence:play"], "consequence_ref": "consequence:second", "provenance": provenance()}]
    grants = {PRINCIPAL: {"source_system": SOURCE, "operations": ["origin", "celestial", "agent", "plane",
        "bloodline", "wolf", "raven", "ability", "manifest", "dismiss", "append", "branch", "compensate"]}}
    origin_policy = OriginProgressionPolicy(WORLD, PLAYER,
        document("data/profiles/wrw_origin_progression.json")["profile"],
        {"mortal_identity_ref": "identity:mortal", "identity_status": "veiled", "provenance": provenance()},
        {PRINCIPAL: ["advance", "remember"]}, [first, second], schemas["action"], schemas["memory"])
    return WORLD, PLAYER, profile, spine, grants, records, updates, schemas, origin_policy
