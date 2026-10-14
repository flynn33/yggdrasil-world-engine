"""Reusable, explicitly qualified world fixtures with actual player/M3 owners.

External heads are synthetic trusted test-host qualifications. Coordinator tests
must replace them with actual journal heads; these bytes do not authenticate one.
"""
import copy
import hashlib
import json
from pathlib import Path

from core import core_values as cv
from core.player_state import PlayerStatePolicy
from core.state_journal import TruthScope, _encode, _object_bytes
from core.world_location_state import SCHEMAS, WorldLocationPolicy
from tests.m4_player_fixture import configuration as player_configuration
from tests.test_m3_core_values import core_binding

ROOT = Path(__file__).resolve().parents[1]
WORLD, PLAYER, BRANCH = "world:one", "player:one", "branch:one"
SHARED = TruthScope(WORLD, "shared_worldstate", WORLD)


def digest(document):
    return hashlib.sha256(_object_bytes(document)).hexdigest()


def provenance():
    return {"cosmic_pattern_snapshot_ref": "source:ash", "diagnostic_ref": "diagnostic:world",
            "generation_plan_ref": "source:ash", "source_ash_refs": ["source:ash"]}


def record(ref, kind, document, scope=SHARED):
    return {"ref": ref, "kind": kind, "scope": scope.to_record(), "document": copy.deepcopy(document),
            "sha256": digest(document), "provenance": provenance()}


def source(ref, kind="ash_evidence", value=None, subject=WORLD):
    return record(ref, "source_evidence", {"format": "ywe.world_source_evidence.v1", "source_id": ref,
        "source_kind": kind, "subject_ref": subject, "value": value or {"kind": "token", "token": "qualified"},
        "source_refs": [], "provenance": provenance()})


def component(component_id, scope, policy_id, state):
    head = {"component_id": component_id, "scope": scope.to_record(), "owner_policy_id": policy_id,
            "revision": 0, "head_digest": digest({"fixture_head": component_id}), "state_sha256": digest(state)}
    return {**head, "state": copy.deepcopy(state)}


def inputs(kind="fact", *, veil="TRUE", threshold=10000, leaf=False):
    """Return (eight constructor args, exact read_view, selected update ref)."""
    scope = TruthScope(WORLD, "leaf_branch_state", BRANCH) if leaf else SHARED
    schemas = {key: json.loads((ROOT / "data/schemas" / (name + "_schema.json")).read_text(encoding="utf-8"))
               for key, name in SCHEMAS.items()}
    player = PlayerStatePolicy(*player_configuration())
    player_state = player.initial_state()
    player_row = component("component:player", player.scope, player.policy_id, player_state)
    branch_row = component("component:branch", TruthScope(WORLD, "leaf_branch_state", BRANCH),
                           "branch:fixture", {"format": "ywe.branch_owner.v1", "world_id": WORLD,
                           "branch_id": BRANCH, "owner_player_id": PLAYER, "branch": None, "events": {}})
    view = {"format": "ywe.owner_read_view.v1", "world_id": WORLD, "components": [branch_row, player_row]}
    heads = [{k: v for k, v in row.items() if k != "state"} for row in view["components"]]
    view_hash = hashlib.sha256(_encode(heads)).hexdigest()
    binding = core_binding(realms=(cv.ProfileRealmDefinition("realm:material", 6, None, "Earth", 0, False, ("realm:material",)),
        cv.ProfileRealmDefinition("realm:echo", 2, None, "Echo", threshold, True, ("realm:material",))))
    records = [source("source:ash"), source("source:genesis", "genesis"),
               source("source:permission", "declared_condition", {"kind": "boolean", "value": True})]
    records.append(record("diagnostic:world", "diagnostic", {"diagnostic_ref": "diagnostic:world", "owner": "NARRATIVE",
        "rule": "PROVENANCE", "status": "COMPLETED", "failure_code": None, "field": None,
        "evidence_refs": ["source:ash"], "explanation": "Qualified reference consequence."}))
    records.append(record("condition:permission", "condition", {"kind": "declared_source", "source_ref": "source:permission",
        "source_sha256": records[2]["sha256"], "subject_ref": WORLD, "expected_value": {"kind": "boolean", "value": True}}))
    geography = {"format": "ywe.world_geography_anchor.v1", "world_id": WORLD,
        "locations": [{"location_id": "location:echo", "base_location_ref": "base:echo", "realm_ids": ["realm:echo"]},
                      {"location_id": "location:one", "base_location_ref": "base:one", "realm_ids": ["realm:material"]}],
        "fixed_facts": [], "source_evidence_refs": ["source:ash"]}
    records.append(record("anchor:geography", "geography", geography))
    before = {"status": "base", "phase": "ordinary", "stability": "stable", "active_plane_pressures": [],
        "access": [{"access_id": "access:gate", "state": "closed", "condition_refs": []}],
        "eligible_systems": [], "residue_refs": [], "future_generation_bias_refs": []}
    after = copy.deepcopy(before)
    after["status"] = "activated"
    after["access"][0]["state"] = "open"
    rules = [{"rule_id": "rule:open", "location_id": "location:one", "source_current": before,
              "target_current": after, "condition_refs": ["condition:permission"]}]
    locations = []
    for loc, realm, base in (("location:echo", "realm:echo", "base:echo"), ("location:one", "realm:material", "base:one")):
        locations.append({"location_id": loc, "base_location_ref": base, "realm_ids": [realm],
            "geography_sha256": digest(geography), "allowed_current_states": [
                {k: row[k] for k in ("status", "phase", "stability")} for row in (before, after)],
            "access_definitions": [{"access_id": "access:gate", "access_kind": "gate"}],
            "thin_veil_slots": [{"target_realm_id": "realm:echo", "slot_id": "fact:veil"}] if loc == "location:one" else []})
    definitions = []
    for slot, values, loc in (("fact:gate", ["closed", "open"], "location:one"),
                              ("fact:veil", ["FALSE", "TRUE", "UNAVAILABLE"], "location:one")):
        definitions.append({"definition_ref": "definition:" + slot, "slot_id": slot, "domain": "local_world_condition",
            "subject_ref": loc, "realm_id": "realm:material", "location_id": loc, "value_kind": "token",
            "allowed_values": values, "minimum": None, "maximum": None, "mutable": True,
            "mergeable": True, "projection_fact_id": "projection:" + slot})
    profile = {"profile_id": "world:profile", "component_id": "component:world", "law_ref": "anchor:law",
        "geography_ref": "anchor:geography", "realm_plane_bindings": [
            {"realm_id": "realm:echo", "plane_id": "P4_Mental"}, {"realm_id": "realm:material", "plane_id": "P1_Physical"}],
        "fact_definitions": definitions, "location_definitions": locations, "mutable_rules": rules}
    records.append(record("anchor:law", "law", {"format": "ywe.world_law_anchor.v1", "profile_id": profile["profile_id"],
        "core_binding_sha256": hashlib.sha256(cv.canonical_bytes(binding)).hexdigest(),
        "location_rule_refs": ["rule:open"], "source_evidence_refs": ["source:ash"]}))
    initial_locations = []
    for loc, realm, base in (("location:echo", "realm:echo", "base:echo"), ("location:one", "realm:material", "base:one")):
        ref = loc + ":initial"
        doc = {"location_id": loc, "base_location_ref": base, "realm_id": realm, "current": before,
               "source_delta_ref": "genesis:" + loc, "source_mutation_ref": "genesis:" + loc}
        seed = {k: doc[k] for k in ("location_id", "base_location_ref", "realm_id", "current")}
        records.append(source("genesis:" + loc, "genesis", {"kind": "token", "token": digest(seed)}, loc))
        records.append(record(ref, "resolved_location", doc, scope))
        initial_locations.append({"location_id": loc, "realm_id": realm, "current_record_ref": ref,
            "current_record_sha256": digest(doc), "history_event_refs": ["genesis:" + loc]})
    occupancy = {"player_id": PLAYER, "branch_ref": BRANCH, "location_id": "location:one", "realm_id": "realm:material"}
    records += [source("genesis:gate", "genesis", {"kind": "token", "token": "closed"}, "location:one"),
                source("genesis:veil", "genesis", {"kind": "token", "token": veil}, "location:one"),
                source("genesis:occupancy", "genesis", {"kind": "token", "token": digest(occupancy)}, PLAYER)]
    initial = {"format": "ywe.world_location_partition.v1", "scope": scope.to_record(), "component_id": profile["component_id"],
        "profile_id": profile["profile_id"], "law_sha256": next(x["sha256"] for x in records if x["ref"] == "anchor:law"),
        "geography_sha256": digest(geography), "facts": [
            {"slot_id": "fact:gate", "definition_ref": "definition:fact:gate", "value": {"kind": "token", "token": "closed"}, "source_event_ref": "genesis:gate"},
            {"slot_id": "fact:veil", "definition_ref": "definition:fact:veil", "value": {"kind": "token", "token": veil}, "source_event_ref": "genesis:veil"}],
        "locations": initial_locations, "occupancies": [{**occupancy, "source_event_ref": "genesis:occupancy"}],
        "records": {x["ref"]: copy.deepcopy(x) for x in records},
        "events": [], "consumed_effects": []}
    operation = {"kind": "fact", "operation_id": "operation:one", "slot_id": "fact:gate",
        "before": {"kind": "token", "token": "closed"}, "after": {"kind": "token", "token": "open"},
        "condition_refs": ["condition:permission"]}
    legacy_operation, target = "commit_public_fact", "fact:gate"
    mutation_refs = []
    boundary = {"can_influence_generation_context": True, "may_mutate_ash_math": False,
                "may_rewrite_shared_world_truth": False, "may_mutate_base_world_ontology": False, "host_adapter_may_author": False}
    persistence_scope = "leaf_branch" if leaf else "shared_world"
    if kind == "location":
        operation = {"kind": "location", "operation_id": "operation:one", "location_id": "location:one",
            "realm_id": "realm:material", "before_record_ref": "location:one:initial", "after_record_ref": "location:one:open",
            "mutation_ref": "mutation:one", "rule_id": "rule:open", "condition_refs": ["condition:permission"]}
        legacy_operation, target, mutation_refs = "set_status", "location:one", ["mutation:one"]
        records.append(record("location:one:open", "resolved_location", {"location_id": "location:one", "base_location_ref": "base:one",
            "realm_id": "realm:material", "current": after, "source_delta_ref": "delta:one", "source_mutation_ref": "mutation:one"}, scope))
        records.append(record("mutation:one", "location_mutation", {"record_type": "LocationMutationDelta", "version": "1.0.0",
            "mutation_delta_id": "mutation:one", "target_location_state_ref": "location:one:initial", "source_worldstate_delta_ref": "delta:one",
            "source_branch_event_ref": None, "source_player_runtime_state_ref": "component:player", "mutation_kind": "public_condition_changed",
            "changed_fields": [{"field_path": "access", "change_kind": "set_threshold_status", "reason": "Qualified open gate."},
                               {"field_path": "status", "change_kind": "set_status", "reason": "Qualified activated site."}],
            "persistence_scope": persistence_scope, "diagnostic_ref": "diagnostic:world", "generation_plan_ref": "source:ash",
            "source_ash_refs": ["source:ash"], "authority_boundary": boundary}, scope))
    if kind == "realm_shift":
        operation = {"kind": "realm_shift", "operation_id": "operation:one", "player_id": PLAYER,
            "before": {"location_id": "location:one", "realm_id": "realm:material"},
            "after": {"location_id": "location:echo", "realm_id": "realm:echo"}, "player_component_id": "component:player",
            "player_state_sha256": player_row["state_sha256"], "plane_state_ref": "plane:initial", "veil_slot_id": "fact:veil",
            "request_ref": "realm:request", "proposal_ref": "realm:proposal", "condition_refs": ["condition:permission"]}
        target = PLAYER
    records.append(record("action:world", "action", {"schema_id": "ywe.player_action_trace.v1", "schema_version": "0.1.0",
        "action_trace_id": "action:world", "player_id": PLAYER, "action_kind": "location_state_changed", "significance": "meaningful",
        "branch_relevance": "contextual", "branch_ref": BRANCH, "location_ref": "location:one", "affected_entity_refs": [target],
        "resulting_worldstate_delta_refs": ["delta:one"], "source_refs": ["source:ash"]}, TruthScope(WORLD, "player_state", PLAYER)))
    records.append(record("resolution:one", "resolution", {"format": "ywe.world_resolution.v1", "resolution_id": "resolution:one",
        "world_id": WORLD, "player_head": heads[1], "branch_head": heads[0], "action_refs": ["action:world"], "delta_ref": "delta:one",
        "location_mutation_refs": mutation_refs, "condition_refs": ["condition:permission"], "provenance": provenance()}, scope))
    records.append(record("delta:one", "delta", {"record_type": "WorldstateDeltaPacket", "version": "1.0.0", "delta_id": "delta:one",
        "sequence_id": 0, "source_resolution_payload": "resolution:one", "source_branch_event_ref": None,
        "player_runtime_state_ref": "component:player", "current_leaf_branch_ref": BRANCH, "affected_location_refs": ["location:one"],
        "location_mutation_refs": mutation_refs, "consequence_domains": ["local_world_condition"], "mutations": [
            {"operation_id": "operation:one", "domain": "local_world_condition", "operation": legacy_operation,
             "target_ref": target, "evidence_refs": ["condition:permission"]}],
        "persistence": {"scope": persistence_scope, "visibility": "branch_local" if leaf else "shared_world", "retention_policy": "persistent", "append_only": True},
        "reversibility": {"reversible": True, "requires_new_delta": True}, "authority_boundary": boundary,
        "ash_provenance": {**provenance(), "axiom_diagnostic_refs": [], "pattern_vector_refs": [], "existence_potential_ref": "source:ash"},
        "future_generation_bias_update_refs": []}, scope))
    update = {"update_ref": "update:world", "scope": scope.to_record(), "component_id": profile["component_id"],
        "delta_ref": "delta:one", "effect_id": "effect:world", "resolutions": [operation], "source_read_vector_sha256": view_hash,
        "retention": {"kind": "persistent"}, "compensates_effect_id": None, "provenance": provenance()}
    grants = {"narrative:owner": {"roles": ["narrative"]}, "realm:owner": {"roles": ["realm"]}}
    return (scope, profile, initial, grants, records, [update], schemas, binding), view, "update:world"


def build(kind="fact", **options):
    args, view, update = inputs(kind, **options)
    owner = WorldLocationPolicy(*args)
    packet = owner.packet({"narrative_principal": "narrative:owner", "realm_principal": None if kind == "fact" else "realm:owner"},
                          "request:world", update)
    return owner, packet, view


def shared_veil_basis(args, view, value="TRUE"):
    """Add a current head/body produced by an actual distinct shared owner."""
    threshold = next(r.threshold_q6 for r in args[7].profile_realms if r.realm_id == "realm:echo")
    shared, _, _ = inputs("realm_shift", veil=value, threshold=threshold)
    shared[1]["component_id"] = "component:shared"
    shared[2]["component_id"] = "component:shared"
    shared[5][0]["component_id"] = "component:shared"
    actual = WorldLocationPolicy(*shared)
    row = component(actual.component_id, actual.scope, actual.policy_id, actual.initial_state())
    head = {k: v for k, v in row.items() if k != "state"}
    args[4].append(record("condition:shared-veil", "condition", {"kind":"current_fact", "head":head,
        "slot_id":"fact:veil", "expected_value":{"kind":"token","token":value}}, args[0]))
    args[5][0]["resolutions"][0]["condition_refs"].append("condition:shared-veil")
    delta = next(x for x in args[4] if x["ref"] == "delta:one")
    delta["document"]["mutations"][0]["evidence_refs"].append("condition:shared-veil")
    delta["sha256"] = digest(delta["document"])
    view["components"].append(row)
    view["components"].sort(key=lambda x:x["component_id"])
    heads = [{k:v for k,v in row.items() if k != "state"} for row in view["components"]]
    args[5][0]["source_read_vector_sha256"] = hashlib.sha256(_encode(heads)).hexdigest()
    return actual
