"""Fixed WRW player evidence projection for the neutral branch owner.

This compatibility module deliberately reuses the actual PlayerStatePolicy
validator. No serialized witness is a substitute for replaying these qualifiers.
[YWE-REQ-0059]
"""

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from core.branch_state import _component_copy, _copy, _digest, _reject, _shape
from core.commit_set_journal import _component, _head, _head_of
from core.player_state import PlayerStatePolicy
from core.state_journal import JournalError, _identifier


ADAPTER_ID = "wrw.branch_player.v1"


def _player(component, owner_policy):
    _reject(type(owner_policy) is not PlayerStatePolicy, "INVALID_POLICY")
    component = _component_copy(component)
    _component(component, owner_policy.scope.world_id)
    _reject(component["scope"] != owner_policy.scope.to_record()
            or component["owner_policy_id"] != owner_policy.policy_id, "INVALID_SCOPE")
    state = component["state"]
    original = _copy(state)
    state = owner_policy.validated_state(state)
    _reject(state != original, "INVALID_PLAYER_STATE")
    return component


def _document(state, ref, kind):
    entry = state["records"].get(ref)
    _reject(entry is None or entry["kind"] != kind, "INVALID_PLAYER_STATE")
    return entry["document"]


def _origin(state):
    return _document(state, state["spine"]["origin_progression_state_ref"], "origin")


def _pair(before, after, owner_policy):
    before, after = _player(before, owner_policy), _player(after, owner_policy)
    _reject(before["component_id"] != after["component_id"] or before["scope"] != after["scope"]
            or after["revision"] != before["revision"] + 1, "INVALID_PLAYER_STATE")
    return before, after


def qualify_creation(component, creation_ref, *, owner_policy):
    """Bind an actual history-free initial player, never an imported reset."""
    _identifier(creation_ref)
    component = _player(component, owner_policy)
    state = component["state"]
    spine, origin = state["spine"], _origin(state)
    history = _document(state, spine["state_refs"]["player_branch_history_ref"], "branch_history")
    celestial = _document(state, spine["identity"]["celestial_identity_state_ref"], "celestial")
    _reject(state["format"] != "ywe.player_aggregate.v1" or "import_baseline" in state
            or spine["state_lifecycle"] != "initial" or state["accepted_updates"] or state["compensations"]
            or origin["actions"] or origin["memories"] or origin["advances"] or history["entries"]
            or celestial["identity_state"] != "veiled" or celestial["reveal_status"] != "not_revealed",
            "INVALID_CREATION")
    return _copy({"player_id": component["scope"]["subject_id"], "component_id": component["component_id"],
        "head": _head_of(component), "creation_ref": creation_ref, "source_sha256": component["state_sha256"]})


def qualify_action(profile, decision, source_branch_head, player_before, player_after,
                   action_ref, action_schema, *, owner_policy):
    """Derive the one new action linked to the actual staged branch-history row."""
    _identifier(action_ref)
    before, after = _pair(player_before, player_after, owner_policy)
    profile, decision = _copy(profile), _copy(decision)
    _head(source_branch_head, owner_policy.scope.world_id)
    _reject(profile.get("action_adapter_id") != ADAPTER_ID, "INVALID_POLICY")
    prior, staged = before["state"], after["state"]
    old_actions = {row["action_trace_id"]: row for row in _origin(prior)["actions"]}
    new_actions = {row["action_trace_id"]: row for row in _origin(staged)["actions"]}
    _reject(action_ref in old_actions or action_ref not in new_actions, "UNQUALIFIED_CHOICE")
    action = new_actions[action_ref]
    try:
        _reject(type(action_schema) is not dict
                or action_schema.get("$id") != "https://ywe.local/schemas/player_action_trace_schema.json", "INVALID_SCHEMA")
        Draft202012Validator.check_schema(action_schema)
        _reject(not Draft202012Validator(action_schema).is_valid(action), "UNQUALIFIED_CHOICE")
    except SchemaError:
        raise JournalError("INVALID_SCHEMA") from None
    _reject(action["schema_version"] != "0.1.0" or action["player_id"] != owner_policy.scope.subject_id
            or action.get("branch_ref") != prior["spine"]["current_leaf_branch_ref"]
            or action.get("location_ref") != prior["spine"]["current_location_ref"]
            or source_branch_head["scope"]["truth_scope"] != "leaf_branch_state"
            or source_branch_head["scope"]["subject_id"] != action["branch_ref"]
            or action["branch_relevance"] != "branch_event_created"
            or action["significance"] not in ("meaningful", "branch_forming", "mythic", "prophetic")
            or not action.get("source_refs"), "UNQUALIFIED_CHOICE")
    previous_updates = {row["update_ref"] for row in prior["accepted_updates"]}
    updates = [row for row in staged["accepted_updates"] if row["update_ref"] not in previous_updates]
    _reject(len(updates) != 1, "UNQUALIFIED_CHOICE")
    update = updates[0]
    consequence = _document(staged, update["consequence_ref"], "consequence")
    _reject(action.get("resulting_player_state_update_refs") != [update["update_ref"]]
            or action_ref not in consequence["action_refs"] or consequence["update_ref"] != update["update_ref"]
            or consequence["player_id"] != action["player_id"] or consequence["branch_ref"] != action["branch_ref"]
            or set(consequence["external_result_refs"]) != {
                ref for row in _origin(staged)["actions"] if row["action_trace_id"] in consequence["action_refs"]
                for ref in row.get("resulting_worldstate_delta_refs", [])}, "UNQUALIFIED_CHOICE")
    old_history = _document(prior, prior["spine"]["state_refs"]["player_branch_history_ref"], "branch_history")["entries"]
    history = _document(staged, staged["spine"]["state_refs"]["player_branch_history_ref"], "branch_history")["entries"]
    _reject(len(history) != len(old_history) + 1 or history[:-1] != old_history, "UNQUALIFIED_CHOICE")
    choice = history[-1]
    _reject(choice["source_action_trace_ref"] != action_ref or choice["branch_event_ref"] != action.get("branch_event_ref")
            or choice["parent_branch_ref"] != action["branch_ref"]
            or choice["leaf_branch_ref"] != staged["spine"]["current_leaf_branch_ref"]
            or choice["resulting_player_state_update_refs"] != [update["update_ref"]]
            or choice["resulting_worldstate_delta_refs"] != action.get("resulting_worldstate_delta_refs", [])
            or choice["chosen_action"] != decision.get("chosen_action")
            or action_ref != decision.get("source_action_ref") or action["location_ref"] != decision.get("location_ref")
            or type(decision.get("available_actions")) is not list or len(decision["available_actions"]) < 2
            or len(set(decision["available_actions"])) != len(decision["available_actions"])
            or decision["chosen_action"] not in decision["available_actions"], "UNQUALIFIED_CHOICE")
    rules = [rule for rule in profile["choice_rules"] if rule["action_kind"] == action["action_kind"]
             and choice["chosen_action"] in rule["action_tokens"]
             and decision["choice_significance"] in rule["significance_values"]]
    _reject(len(rules) != 1, "UNQUALIFIED_CHOICE")
    return _copy({"adapter_id": ADAPTER_ID, "action_ref": action_ref, "action_sha256": _digest(action),
        "player_component_id": before["component_id"], "player_before_head": _head_of(before),
        "source_branch_head": source_branch_head, "player_id": action["player_id"], "source_branch_id": action["branch_ref"],
        "target_branch_id": staged["spine"]["current_leaf_branch_ref"],
        "location_ref": action["location_ref"], "action_kind": action["action_kind"], "chosen_action": choice["chosen_action"],
        "decision_ref": decision["decision_ref"], "player_update_ref": update["update_ref"],
        "consequence_ref": update["consequence_ref"], "resulting_delta_refs": action.get("resulting_worldstate_delta_refs", []),
        "source_refs": action["source_refs"]})


def _value(state, target):
    spine = state["spine"]
    kind = "token"
    if target == "origin_phase":
        value = _origin(state)["current_phase"]
    elif target == "identity_state":
        value = _document(state, spine["identity"]["celestial_identity_state_ref"], "celestial")["identity_state"]
    elif target == "raven_status":
        value = _document(state, spine["state_refs"]["raven_companion_state_ref"], "raven")["runtime_status"]
    elif target.startswith("ability:"):
        ability_id = target[len("ability:"):]
        values = [_document(state, ref, "ability") for ref in spine["ability_state_refs"]]
        values = [row for row in values if row["ability_id"] == ability_id]
        _reject(len(values) > 1, "INVALID_PLAYER_STATE")
        if not values:
            return {"present": False}
        value = values[0]["current_state"]
    elif target.startswith("plane:") and target.endswith(":score_q6"):
        name = target[len("plane:"):-len(":score_q6")]
        document = _document(state, spine["state_refs"]["plane_attunement_state_ref"], "plane")
        _reject(name not in document["planes"], "UNSUPPORTED_PROJECTION")
        value, kind = document["planes"][name]["score_q6"], "integer"
    elif target.startswith("bloodline:") and target.endswith(":score_q6"):
        name = target[len("bloodline:"):-len(":score_q6")]
        document = _document(state, spine["state_refs"]["bloodline_resonance_state_ref"], "bloodline")
        values = [row for row in document["signals"] if row["bloodline_id"] == name]
        _reject(len(values) != 1, "UNSUPPORTED_PROJECTION")
        value, kind = values[0]["score_q6"], "integer"
    elif target in ("wolf:white_wolf:resonance_q6", "wolf:dark_wolf:resonance_q6", "wolf:twin_coherence:coherence_q6"):
        document = _document(state, spine["state_refs"]["wolf_resonance_summary_ref"], "wolf")
        _, name, field = target.split(":")
        value, kind = document[name][field], "integer"
    else:
        raise JournalError("UNSUPPORTED_PROJECTION")
    return {"present": True, "value": {"kind": kind, "token" if kind == "token" else "value": value}}


def qualify_player_effect(binding, player_before, player_after, update_ref, *, owner_policy):
    """Compare fixed semantic values; aliases, branch pointers and counters do not count."""
    _identifier(update_ref)
    _shape(binding, "projection_ref component_id partition_id target_kind target_id definition_ref mergeable")
    before, after = _pair(player_before, player_after, owner_policy)
    _reject(binding["component_id"] != before["component_id"] or binding["target_kind"] != "player_component", "INVALID_SCOPE")
    prior, staged = before["state"], after["state"]
    _reject(any(row["update_ref"] == update_ref for row in prior["accepted_updates"]), "ALREADY_CONSUMED")
    updates = [row for row in staged["accepted_updates"] if row["update_ref"] == update_ref]
    _reject(len(updates) != 1, "UNQUALIFIED_EFFECT")
    old_value, new_value = _value(prior, binding["target_id"]), _value(staged, binding["target_id"])
    _reject(old_value == new_value, "UNQUALIFIED_EFFECT")
    return _copy({"effect_ref": update_ref + ":projection", "projection_ref": binding["projection_ref"],
        "component_id": before["component_id"], "before_head": _head_of(before), "source_event_ref": update_ref,
        "before": old_value, "after": new_value, "source_occurrence_sha256": _digest(updates[0])})


def qualify_retention(player_before, player_after, *, owner_policy):
    """Retain actual source identities; imported reservations have no fake receipt."""
    before, after = _pair(player_before, player_after, owner_policy)
    state, component_id = after["state"], after["component_id"]
    world, player = owner_policy.scope.world_id, owner_policy.scope.subject_id
    imported = state.get("import_baseline")
    anchor = None if imported is None else imported["import_anchor"]
    origin = _origin(state)
    updates = {row["update_ref"]: row for row in state["accepted_updates"]}
    actions = {row["action_trace_id"]: row for row in origin["actions"]}
    occurrences, consumed = [], []

    def add(namespace, identity, payload, ref, request, event, retained):
        _reject(request is None, "UNQUALIFIED_RETENTION")
        row = {"namespace": namespace, "identity_parts": identity, "payload_sha256": _digest(payload),
               "origin_component_id": component_id, "origin_request_ref": request, "origin_event_ref": event}
        consumed.append(row)
        if retained:
            occurrences.append({**row, "record_ref": ref})

    def action_origin(action):
        rows = [updates[ref] for ref in action.get("resulting_player_state_update_refs", []) if ref in updates]
        _reject(len(rows) > 1, "UNQUALIFIED_RETENTION")
        return (rows[0]["request_ref"], True) if rows else (anchor, False)

    for action in origin["actions"]:
        request, retained = action_origin(action)
        add("action", [world, player, action["action_trace_id"]], action, action["action_trace_id"],
            request, action.get("branch_event_ref") if retained else None, retained)
    for memory in origin["memories"]:
        action = actions.get(memory.get("source_action_trace_ref"))
        _reject(action is None, "UNQUALIFIED_RETENTION")
        request, retained = action_origin(action)
        add("memory", [world, player, memory["memory_id"]], memory, memory["memory_id"],
            request, action.get("branch_event_ref") if retained else None, retained)
    for update in state["accepted_updates"]:
        consequence = _document(state, update["consequence_ref"], "consequence")
        events = {actions[ref].get("branch_event_ref") for ref in consequence["action_refs"]}
        events.discard(None)
        _reject(len(events) > 1, "UNQUALIFIED_RETENTION")
        event = next(iter(events), None)
        add("update", [component_id, update["request_ref"]], update, update["update_ref"], update["request_ref"], event, True)
        add("update", [world, player, update["update_ref"]], update, update["update_ref"], update["request_ref"], event, False)
        add("effect", update["effect"], consequence, update["consequence_ref"], update["request_ref"], event, True)
    for ref, entry in state["records"].items():
        if entry["kind"] != "manifestation":
            continue
        document = entry["document"]
        event_id = document["manifestation_event_id"]
        if imported is not None and event_id in imported["consumed_manifestation_event_ids"]:
            continue
        receipts = [row for row in state["accepted_updates"] if any(
            operation["kind"] == "manifest" and operation["event_ref"] == ref
            for operation in owner_policy.update(row["update_ref"])["operations"])]
        _reject(len(receipts) != 1, "UNQUALIFIED_RETENTION")
        add("manifestation", [world, player, event_id], document, ref, receipts[0]["request_ref"], None, True)
    if imported is not None:
        for update_ref in imported["consumed_update_refs"]:
            add("update", [world, player, update_ref], imported, update_ref, anchor, None, False)
        for request in imported["consumed_request_refs"]:
            add("update", [component_id, request], imported, request, anchor, None, False)
        for effect in imported["consumed_effects"]:
            add("effect", effect["effect"], imported, effect["consequence_ref"], anchor, None, False)
        for event_id in imported["consumed_manifestation_event_ids"]:
            add("manifestation", [world, player, event_id], imported, event_id, anchor, None, False)
    return _copy({"component_id": component_id, "before_head": _head_of(before),
                  "occurrences": occurrences, "consumed": consumed})
