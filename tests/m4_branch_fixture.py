"""Reusable branch qualifications with real player reduction.

World projections here are trusted synthetic owner outputs, not a world child
factory or a multiplayer coordinator. Historical component bodies are frozen
outputs of the real commit-set head helpers, explicitly supplied as trusted test
history. Production composition must obtain that view from journal replay.
"""

import copy
from types import MappingProxyType

from core.branch_state import BranchReadView, BranchStatePolicy, SCHEMAS, _digest
from core.branch_state_wrw import ADAPTER_ID, qualify_action, qualify_creation, qualify_player_effect, qualify_retention
from core.commit_set_journal import CommitSetBinding, CommitSetReadView, initial_component, advance_component, _head_of
from core.narrative_engine.origin_progression import OriginProgressionPolicy
from core.player_state import PlayerStatePolicy
from core.state_journal import TruthScope, _encode
from tests.m4_player_fixture import (
    BRANCH, PLAYER, PRINCIPAL, SOURCE, WORLD, configuration as player_configuration,
    consequence, document, evidence, provenance, record as player_record, reference as player_reference,
)


BINDING = CommitSetBinding(WORLD, "container:branches")
BOOTSTRAP_PRINCIPAL = "world:creator"
MERGE_PRINCIPAL = "cosmology:owner"


def scope(kind="leaf_branch_state", subject=BRANCH):
    return TruthScope(WORLD, kind, subject).to_record()


def schemas():
    return {kind: document("data/schemas/" + filename) for kind, filename in SCHEMAS.items()}


def qualified(ref, kind, value, source_scope=None):
    return {"ref": ref, "kind": kind, "scope": copy.deepcopy(source_scope or scope()),
            "document": copy.deepcopy(value), "sha256": _digest(value), "provenance": provenance()}


def reference(ref, category, subject=None, source=None, source_scope=None):
    value = {"category": category, "subject_ref": subject or ref,
             "source_sha256": _digest({"fixture": ref} if source is None else source)}
    return qualified(ref, "reference", value, source_scope)


def history(components=()):
    empty = MappingProxyType({})
    return CommitSetReadView(empty, empty,
        MappingProxyType({_encode(_head_of(row)): _encode(row) for row in components}), WORLD)


def step(component_id, state, policy_id, component_scope, *, previous=None, request="request:step", packet=None):
    return advance_component(BINDING, "round:" + request, {"component_id": component_id,
        "scope": component_scope, "owner_policy_id": policy_id, "principal": PRINCIPAL,
        "proposal_id": "proposal:" + request, "owner_request_ref": request,
        "packet": packet or {"request": request}, "state_after": state, "create": previous is None}, previous)[0]


def _player_args():
    args = list(player_configuration())
    sources = [args[8].evidence("origin:first"), args[8].evidence("origin:second")]
    selected = {row["ref"]: row for row in args[5]}
    for name, score in (("left", 30000), ("right", 40000)):
        branch, update, event = "branch:" + name, "update:" + name, "event:" + name
        source = evidence("origin:" + name, update, "first_stirrings", "first_stirrings", 1, "remember")
        source["actions"][0].update(significance="branch_forming", branch_relevance="branch_event_created",
            branch_event_ref=event, location_ref="location:one", resulting_worldstate_delta_refs=["delta:" + name])
        action = source["actions"][0]
        agent = copy.deepcopy(selected["agent:initial"]["document"])
        agent.update(current_leaf_branch_ref=branch, current_location_ref="location:" + name,
            recent_action_trace_refs=[action["action_trace_id"]], branch_event_refs=[event])
        branch_history = copy.deepcopy(selected["history:initial"]["document"])
        branch_history.update(current_leaf_branch_ref=branch, entries=[{"branch_event_ref": event,
            "leaf_branch_ref": branch, "parent_branch_ref": BRANCH, "chosen_action": "cross_threshold",
            "source_action_trace_ref": action["action_trace_id"], "resulting_player_state_update_refs": [update],
            "resulting_worldstate_delta_refs": ["delta:" + name], "source_refs": ["evidence:play"]}])
        ability = copy.deepcopy(selected["ability:latent"]["document"])
        ability.update(branch_ref=branch, history_refs=["evidence:play"])
        plane = copy.deepcopy(selected["plane:stirring"]["document"])
        plane["planes"]["P4_Mental"]["score_q6"] = score
        consequence_record = consequence("consequence:" + name, update, source)
        consequence_record["document"]["external_result_refs"] = ["delta:" + name]
        args[5].extend([player_reference(branch, "current_leaf_branch_ref", "leaf_branch_state", branch, branch),
            player_reference("location:" + name, "current_location_ref", "leaf_branch_state", branch, branch),
            player_reference(event, "branch_event_ref", "leaf_branch_state", branch, branch),
            player_reference("delta:" + name, "worldstate_delta_refs", "leaf_branch_state", BRANCH),
            player_record("agent:" + name, "agent", agent, branch),
            player_record("history:" + name, "branch_history", branch_history, branch),
            player_record("ability:" + name, "ability", ability, branch),
            player_record("plane:" + name, "plane", plane, branch), consequence_record])
        args[6].append({"update_ref": update, "world_id": WORLD, "player_id": PLAYER, "branch_ref": BRANCH,
            "source_system": SOURCE, "operations": [{"kind": "origin", "evidence_ref": "origin:" + name},
                {"kind": "branch", "previous_branch_ref": BRANCH, "next_branch_ref": branch,
                 "next_location_ref": "location:" + name, "agent_ref": "agent:" + name,
                 "history_ref": "history:" + name, "event_ref": event},
                {"kind": "ability", "ability_id": "ability:oath", "previous_ref": "ability:latent",
                 "next_ref": "ability:" + name, "condition_refs": []},
                {"kind": "replace", "slot": "plane", "previous_ref": "plane:stirring",
                 "next_ref": "plane:" + name, "condition_refs": []}],
            "evidence_refs": ["evidence:play"], "consequence_ref": "consequence:" + name, "provenance": provenance()})
        sources.append(source)
    args[8] = OriginProgressionPolicy(WORLD, PLAYER,
        document("data/profiles/wrw_origin_progression.json")["profile"],
        {"mortal_identity_ref": "identity:mortal", "identity_status": "veiled", "provenance": provenance()},
        {PRINCIPAL: ["advance", "remember"]}, sources, args[7]["action"], args[7]["memory"])
    return args


def _profile(branch):
    bindings = [{"projection_ref": "projection:mental", "component_id": "component:player",
        "partition_id": "player", "target_kind": "player_component", "target_id": "plane:P4_Mental:score_q6",
        "definition_ref": "definition:mental", "mergeable": False}]
    for name in ("count", "gate"):
        bindings.append({"projection_ref": "projection:" + name, "component_id": "component:world",
            "partition_id": "world_location", "target_kind": "fact", "target_id": name,
            "definition_ref": "definition:" + name, "mergeable": True})
    return {"profile_id": "profile:branches", "component_id": "component:" + branch,
        "partition_id": "branch_lineage", "law_bindings": {"dependency_id": "dependency:test",
            "ash_sha256": _digest({"ash": "fixture"}), "core_contract_sha256": _digest({"core": "fixture"}),
            "realm_law_sha256": _digest({"realm": "fixture"})}, "action_adapter_id": ADAPTER_ID,
        "choice_rules": [{"rule_id": "choice:threshold", "action_kind": "choice",
            "action_tokens": ["cross_threshold"], "significance_values": ["meaningful"],
            "effect_projection_refs": [row["projection_ref"] for row in bindings], "minimum_effects": 1,
            "required_cosmology_refs": ["cosmology:one"], "required_asp_refs": ["asp:one"]}],
        "projections": bindings, "bootstrap_ref": "bootstrap:one" if branch == BRANCH else None}


def _records():
    shared = scope("shared_worldstate", WORLD)
    records = [reference("base:world", "base_world_ref", WORLD, source_scope=shared),
        qualified("pressure:none", "reference", {"category": "active_plane_pressure_ref", "subject_ref": "none", "source_sha256": _digest(None)}, shared),
        reference("cosmology:one", "cosmology_source_refs", source_scope=shared),
        reference("asp:one", "asp_component_refs", source_scope=shared),
        reference("location:one", "location_ref"), reference("agent:one", "agent_ref", PLAYER, source_scope=scope("player_state", PLAYER)),
        reference("definition:mental", "player_component", "plane:P4_Mental:score_q6", source_scope=scope("player_state", PLAYER))]
    for name, kind in (("count", "integer"), ("gate", "token")):
        definition = {"definition_ref": "definition:" + name, "slot_id": name, "domain": "local_world_condition",
            "subject_ref": "location:one", "realm_id": None, "location_id": "location:one", "value_kind": kind,
            "allowed_values": [] if kind == "integer" else ["closed", "open", "sealed"],
            "minimum": 0 if kind == "integer" else None, "maximum": 10 if kind == "integer" else None,
            "mutable": True, "mergeable": True, "projection_fact_id": "fact:" + name}
        records.append(qualified("definition:" + name, "definition", definition))
    return records


def _grants():
    return {BOOTSTRAP_PRINCIPAL: {"source_system": "world_bootstrap", "operations": ["bootstrap"]},
        PRINCIPAL: {"source_system": "narrative_engine", "operations": ["fork", "advance"]},
        MERGE_PRINCIPAL: {"source_system": "runtime_cosmology", "operations": ["merge"]}}


def context(branch, kind, heads, event=None):
    return {"context_id": "context:" + branch, "kind": kind, "world_id": WORLD, "owner_player_id": PLAYER,
        "target_branch_id": branch, "event_ref": event, "read_heads": copy.deepcopy(heads),
        "player_context_refs": ["player:creation"], "location_context_refs": ["location:one"],
        "cosmology_source_refs": ["base:world", "pressure:none", "cosmology:one"], "asp_component_refs": ["asp:one"],
        "diagnostic_refs": [], "future_generation_bias_refs": [], "provenance": provenance()}


def root_case():
    player_args = _player_args()
    player_policy = PlayerStatePolicy(*player_args)
    player = initial_component(BINDING, "component:player", player_policy.scope, player_policy.policy_id, player_policy.initial_state())
    world_state = {"facts": [{"slot_id": "count", "definition_ref": "definition:count",
        "value": {"kind": "integer", "value": 0}, "source_event_ref": "genesis:world"},
        {"slot_id": "gate", "definition_ref": "definition:gate", "value": {"kind": "token", "token": "closed"}, "source_event_ref": "genesis:world"}], "events": []}
    world = initial_component(BINDING, "component:world", TruthScope(WORLD, "shared_worldstate", WORLD), "world:test", world_state)
    profile, records = _profile(BRANCH), _records()
    records.append(reference("player:creation", "player_creation_ref", PLAYER, player["state"], scope("player_state", PLAYER)))
    heads = [_head_of(world), _head_of(player)]
    ctx = context(BRANCH, "root", heads)
    bootstrap = {"bootstrap_ref": "bootstrap:one", "world_id": WORLD, "owner_player_id": PLAYER, "branch_id": BRANCH,
        "world_heads": [_head_of(world)], "player_creation_ref": "player:creation", "initial_location_ref": "location:one",
        "initial_projection_refs": ["projection:initial:count", "projection:initial:gate"],
        "generation_context_ref": ctx["context_id"], "provenance": provenance()}
    records += [qualified(ctx["context_id"], "context", ctx), qualified("bootstrap:one", "bootstrap", bootstrap)]
    for slot in world_state["facts"]:
        records.append(qualified("projection:initial:" + slot["slot_id"], "projection",
            {"projection_ref": "projection:" + slot["slot_id"], "head": _head_of(world), "slot": slot}, scope("shared_worldstate", WORLD)))
    proposal = {"proposal_ref": "proposal:root", "world_id": WORLD, "owner_player_id": PLAYER, "target_branch_id": BRANCH,
        "source_system": "world_bootstrap", "operation": {"kind": "bootstrap", "bootstrap_ref": "bootstrap:one"},
        "generation_context_ref": ctx["context_id"], "expected_heads": sorted(heads, key=_encode), "provenance": provenance()}
    args = [WORLD, BRANCH, PLAYER, profile, _grants(), records, [proposal], schemas()]
    policy = BranchStatePolicy(*args)
    creation = qualify_creation(player, "player:creation", owner_policy=player_policy)
    view = BranchReadView(WORLD, [world, player], [], history([world, player]), [], [], [creation])
    packet = policy.packet(BOOTSTRAP_PRINCIPAL, "request:root", proposal["proposal_ref"])
    state = policy.reduce(policy.initial_state(), packet, view)
    component = step(policy.component_id, state, policy.policy_id, policy.scope.to_record(), request="root", packet=packet)
    return {"args": args, "policy": policy, "packet": packet, "view": view, "state": state,
        "component": component, "world": world, "player": player, "player_policy": player_policy, "player_args": player_args}


def fork_case(root=None, name="left", changes=None):
    root = root or root_case()
    branch, event_id, update = "branch:" + name, "event:" + name, "update:" + name
    player_policy = root["player_policy"]
    prior = player_policy.reduce(root["player"]["state"], player_policy.packet(PRINCIPAL, "request:first", "update:first"))
    before = step("component:player", prior, player_policy.policy_id, player_policy.scope.to_record(), previous=root["player"], request="first")
    after_state = player_policy.reduce(prior, player_policy.packet(PRINCIPAL, "request:" + name, update))
    after = step("component:player", after_state, player_policy.policy_id, player_policy.scope.to_record(), previous=before, request=name)
    profile, records = _profile(branch), _records()
    # The context qualification records bind exact actual before player bytes.
    records.append(reference("player:creation", "player_context_ref", PLAYER, before["state"], scope("player_state", PLAYER)))
    records.append(reference("delta:" + name, "worldstate_delta_refs", source_scope=scope("shared_worldstate", WORLD)))
    decision = {"decision_ref": "decision:" + name, "location_ref": "location:one", "player_context_ref": "player:creation",
        "available_actions": ["cross_threshold", "stay"], "chosen_action": "cross_threshold",
        "choice_significance": "meaningful", "qualifier": "choice:threshold", "source_action_ref": "origin:" + name + ":action:0"}
    parent = _head_of(root["component"])
    heads = [parent, _head_of(before), _head_of(root["world"])]
    ctx = context(branch, "choice", heads, event_id)
    world_state = copy.deepcopy(root["world"]["state"])
    changes = changes or ({"count": {"kind": "integer", "value": 1}} if name == "left" else {"gate": {"kind": "token", "token": "open"}})
    typed_changes, world_effects = [], []
    for slot in world_state["facts"]:
        if slot["slot_id"] in changes:
            old = copy.deepcopy(slot["value"])
            slot.update(value=copy.deepcopy(changes[slot["slot_id"]]), source_event_ref="delta:" + name)
            typed_changes.append({"slot_id": slot["slot_id"], "definition_ref": slot["definition_ref"],
                "before": {"present": True, "value": old}, "after": {"present": True, "value": slot["value"]},
                "source_occurrence_ref": "delta:" + name})
    occurrence = {"event_ref": "delta:" + name, "action_ref": decision["source_action_ref"], "changes": typed_changes}
    world_state["events"].append(occurrence)
    world_after = step("component:world", world_state, root["world"]["owner_policy_id"], root["world"]["scope"], previous=root["world"], request="world:" + name)
    for change in typed_changes:
        world_effects.append({"effect_ref": "effect:" + name + ":" + change["slot_id"], "projection_ref": "projection:" + change["slot_id"],
            "component_id": "component:world", "before_head": _head_of(root["world"]), "source_event_ref": "delta:" + name,
            "before": change["before"], "after": change["after"], "source_occurrence_sha256": _digest(occurrence)})
    event = {"schema_id": "ywe.branch_event.v2", "schema_version": "2.0.0", "branch_event_id": event_id,
        "event_kind": "choice", "world_id": WORLD, "owner_player_id": PLAYER, "target_branch_id": branch,
        "agent_ref": "agent:one", "base_world_ref": "base:world", "parent_heads": [parent], "common_base": None,
        "decision_context": decision["decision_ref"], "generation_context_ref": ctx["context_id"], "read_heads": heads,
        "changes": typed_changes, "resolution_refs": [], "worldstate_delta_refs": ["delta:" + name],
        "future_generation_bias_refs": [], "cosmology_source_refs": ctx["cosmology_source_refs"],
        "asp_component_refs": ctx["asp_component_refs"], "provenance": provenance()}
    for ref, kind, value in ((decision["decision_ref"], "decision", decision), (ctx["context_id"], "context", ctx), (event_id, "event", event)):
        records.append(qualified(ref, kind, value, scope(subject=branch)))
    proposal = {"proposal_ref": "proposal:" + name, "world_id": WORLD, "owner_player_id": PLAYER, "target_branch_id": branch,
        "source_system": SOURCE, "operation": {"kind": "fork", "parent_head": parent, "event_ref": event_id, "changes": typed_changes},
        "generation_context_ref": ctx["context_id"], "expected_heads": sorted(heads, key=_encode), "provenance": provenance()}
    args = [WORLD, branch, PLAYER, profile, _grants(), records, [proposal], schemas()]
    policy = BranchStatePolicy(*args)
    action = qualify_action(profile, decision, parent, before, after, decision["source_action_ref"], root["player_args"][7]["action"], owner_policy=player_policy)
    effect = qualify_player_effect(profile["projections"][0], before, after, update, owner_policy=player_policy)
    retention = qualify_retention(before, after, owner_policy=player_policy)
    view = BranchReadView(WORLD, [root["component"], before, root["world"]], [after, world_after], history([root["component"]]), [action], [effect] + world_effects, retentions=[retention])
    packet = policy.packet(PRINCIPAL, "request:" + name, proposal["proposal_ref"])
    state = policy.reduce(policy.initial_state(), packet, view)
    component = step(policy.component_id, state, policy.policy_id, policy.scope.to_record(), request="branch:" + name, packet=packet)
    return {"args": args, "policy": policy, "packet": packet, "view": view, "state": state, "component": component,
        "root": root, "before_player": before, "after_player": after, "after_world": world_after, "action": action,
        "effects": [effect] + world_effects, "decision": decision, "event": event}


def merge_case(left=None, right=None):
    root = root_case() if left is None else left["root"]
    left, right = left or fork_case(root, "left"), right or fork_case(root, "right")
    branch, event_id = "branch:merge", "event:merge"
    parents = sorted([_head_of(left["component"]), _head_of(right["component"])], key=_encode)
    base = _head_of(root["component"])
    heads = parents
    profile, records = _profile(branch), _records()
    records.append(reference("player:creation", "player_context_ref", PLAYER, root["player"]["state"], scope("player_state", PLAYER)))
    ctx = context(branch, "merge", heads, event_id)
    base_slots = {row["slot_id"]: row for row in root["state"]["branch"]["current_slots"]}
    merged = {}
    for case in (left, right):
        for slot in case["state"]["branch"]["current_slots"]:
            if slot["value"] != base_slots[slot["slot_id"]]["value"]:
                merged[slot["slot_id"]] = slot
    changes = [{"slot_id": key, "definition_ref": value["definition_ref"],
        "before": {"present": True, "value": base_slots[key]["value"]}, "after": {"present": True, "value": value["value"]},
        "source_occurrence_ref": value["source_event_ref"]} for key, value in sorted(merged.items())]
    event = {"schema_id": "ywe.branch_event.v2", "schema_version": "2.0.0", "branch_event_id": event_id,
        "event_kind": "merge", "world_id": WORLD, "owner_player_id": PLAYER, "target_branch_id": branch,
        "agent_ref": "agent:one", "base_world_ref": "base:world", "parent_heads": parents, "common_base": base,
        "decision_context": None, "generation_context_ref": ctx["context_id"], "read_heads": heads,
        "changes": changes, "resolution_refs": [], "worldstate_delta_refs": [], "future_generation_bias_refs": [],
        "cosmology_source_refs": ctx["cosmology_source_refs"], "asp_component_refs": ctx["asp_component_refs"], "provenance": provenance()}
    records += [qualified(ctx["context_id"], "context", ctx, scope(subject=branch)), qualified(event_id, "event", event, scope(subject=branch))]
    proposal = {"proposal_ref": "proposal:merge", "world_id": WORLD, "owner_player_id": PLAYER, "target_branch_id": branch,
        "source_system": "runtime_cosmology", "operation": {"kind": "merge", "base_head": base, "parent_heads": parents,
            "event_ref": event_id, "resolution_refs": []}, "generation_context_ref": ctx["context_id"],
        "expected_heads": sorted(parents + [base], key=_encode), "provenance": provenance()}
    args = [WORLD, branch, PLAYER, profile, _grants(), records, [proposal], schemas()]
    policy = BranchStatePolicy(*args)
    view = BranchReadView(WORLD, [left["component"], right["component"], root["component"]], [], history([root["component"]]), [], [])
    packet = policy.packet(MERGE_PRINCIPAL, "request:merge", proposal["proposal_ref"])
    return {"args": args, "policy": policy, "packet": packet, "view": view, "left": left, "right": right, "root": root}
