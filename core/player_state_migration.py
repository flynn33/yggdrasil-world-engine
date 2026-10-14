"""Source-bound, lossless player imports for YWE-REQ-0057.

Qualification is trusted composition input. The source document cannot create
that authority, fill missing history, or authorize a live player mutation.
"""

from decimal import Decimal, InvalidOperation
import hashlib
import json

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from .narrative_engine.origin_progression import OriginProgressionPolicy, _provenance
from .player_state import COLLECTIONS, SLOTS, WIRE_VERSIONS
from .player_state_rules import PlayerDomainPolicy
from .state_journal import JournalError, TruthScope, _identifier, _object_bytes
from .state_migration import (
    MigrationError, _bounded, _nonfinite, _pairs, _pointer, _q6,
)


SOURCE_SCHEMAS = {
    "closed_reference_v1": "player_runtime_state_schema",
    "historical_record_v1": "ash_generation_packet_schema",
}
TARGET_SCHEMAS = {
    "spine": "m4_player_runtime_state_v3_schema", "celestial": "celestial_identity_state_schema",
    "agent": "player_agent_state_schema", "branch_history": "player_branch_history_schema",
    "plane": "m4_plane_attunement_state_schema", "bloodline": "m4_bloodline_resonance_state_schema",
    "wolf": "m4_wolf_resonance_summary_schema", "raven": "raven_companion_state_schema",
    "ability": "m4_ability_state_schema", "manifestation": "wolf_manifestation_event_schema",
    "action": "player_action_trace_schema", "memory": "player_memory_record_schema",
    "origin": "m4_origin_imported_state_schema", "snapshot": "m4_player_snapshot_v2_schema",
}
RESOLUTION_KEYS = frozenset((
    "format source_sha256 world_id player_id player_profile origin_profile spine creation current_phase "
    "action_refs memory_refs consumed_action_refs records consumed_updates consumed_request_refs "
    "consumed_manifestation_event_ids manifestation_bindings realm_name_map fragment_bindings provenance").split())
CONTEXT_COLLECTIONS = (
    "branch_generation_context_refs", "branch_event_refs", "awakening_fragments", "narrative_memory_refs",
    "relationship_state_refs", "faction_stance_refs", "unresolved_tension_refs", "active_quest_refs",
    "completed_resolution_refs", "generation_context_refs",
)
CONTEXT_FIELDS = frozenset(CONTEXT_COLLECTIONS) | {
    "state_id", "sequence_id", "phase_confidence", "identity_reveal_policy", "origin", "celestial_memory",
    "active_realm_form", "perception_state_ref", "last_player_action_trace_ref", "authority_boundary",
    "ash_provenance", "update_policy",
}
HISTORICAL_FIELDS = CONTEXT_FIELDS | {
    "record_type", "version", "player_ref", "current_phase", "realm_attunement", "wolf_resonance",
    "bloodline_resonance", "current_leaf_branch_ref", "active_worldstate_delta_refs",
    "future_generation_bias_refs",
}
AUTHORITY = {"can_influence_generation_context": True, "may_mutate_ash_math": False,
             "may_rewrite_shared_world_truth": False, "may_mutate_base_world_ontology": False,
             "host_adapter_may_author": False}
UPDATE_POLICY = {"requires_delta": True, "append_first_memory": True,
                 "diagnostic_noop_allowed": True, "branch_event_required_for_branch_mutation": True}
ASH_FIELDS = frozenset(("cosmic_pattern_snapshot_ref diagnostic_ref generation_plan_ref source_ash_refs "
                        "axiom_diagnostic_refs pattern_vector_refs existence_potential_ref").split())


def _fail(condition, code="INVALID_QUALIFICATION"):
    if condition:
        raise MigrationError(code)


def _closed(value, keys, code="INVALID_QUALIFICATION"):
    _fail(type(value) is not dict or set(value) != set(keys), code)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _digest(value):
    return _sha(_object_bytes(value))


def _sha_value(value):
    _fail(type(value) is not str or len(value) != 64
          or any(char not in "0123456789abcdef" for char in value))


def _configuration_bytes(value):
    # Individual documents use journal bounds; a bounded schema/catalog bundle
    # has a larger external envelope and never becomes a journal snapshot.
    pending, count = [(value, 0)], 0
    while pending:
        item, depth = pending.pop()
        count += 1
        _fail(count > 65536 or depth > 40, "MIGRATION_LIMIT")
        if type(item) is dict:
            _fail(any(type(key) is not str for key in item))
            pending.extend((child, depth + 1) for pair in item.items() for child in pair)
        elif type(item) is list:
            pending.extend((child, depth + 1) for child in item)
        else:
            _fail(type(item) not in (str, int, bool, type(None)))
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                     allow_nan=False).encode("utf-8")
    _fail(len(raw) > 1048576, "MIGRATION_LIMIT")
    return raw


def _copy(value):
    return json.loads(_configuration_bytes(value))


def _refs(value, minimum=0):
    _fail(type(value) is not list or not minimum <= len(value) <= 128)
    for ref in value:
        _identifier(ref)
    _fail(len(set(value)) != len(value))
    return value


def _schemas(bundle, names):
    _closed(bundle, names)
    copied, hashes, by_uri = {}, {}, {}
    for kind, name in names.items():
        schema = _copy(bundle[kind])
        uri = "https://ywe.local/schemas/" + name + ".json"
        _fail(type(schema) is not dict or schema.get("$id") != uri
              or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema")
        Draft202012Validator.check_schema(schema)
        copied[kind], hashes[kind], by_uri[uri] = schema, _sha(_configuration_bytes(schema)), schema

    def resolve(ref, root):
        _fail(type(ref) is not str)
        uri, separator, fragment = ref.partition("#")
        target = root if not uri else by_uri.get(uri)
        _fail(target is None or separator and fragment and not fragment.startswith("/"))
        for part in fragment[1:].split("/") if fragment else ():
            part = part.replace("~1", "/").replace("~0", "~")
            _fail(type(target) is not dict or part not in target)
            target = target[part]
        _fail(type(target) not in (dict, bool))
        return target, root if not uri else by_uri[uri]

    checked = set()

    def visit(node, root, active):
        if type(node) not in (dict, list):
            return
        identity = id(node)
        _fail(identity in active)
        if identity in checked:
            return
        active = active | {identity}
        if type(node) is dict:
            _fail("$dynamicRef" in node or node is not root and "$id" in node)
            if "$ref" in node:
                target, target_root = resolve(node["$ref"], root)
                visit(target, target_root, active)
            for child in node.values():
                visit(child, root, active)
        else:
            for child in node:
                visit(child, root, active)
        checked.add(identity)

    for schema in copied.values():
        visit(schema, schema, set())

    def deny(uri):
        raise NoSuchResource(ref=uri)

    registry = Registry(retrieve=deny).with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in copied.values())
    return copied, hashes, {kind: Draft202012Validator(schema, registry=registry)
                            for kind, schema in copied.items()}


def _exact(value):
    _fail(type(value) not in (int, Decimal), "INVALID_SOURCE")
    decimal = value if type(value) is Decimal else Decimal(value)
    _fail(not decimal.is_finite(), "INVALID_SOURCE")
    sign, digits, exponent = decimal.as_tuple()
    coefficient = "".join(map(str, digits)).lstrip("0")
    if not coefficient:
        return {"coefficient": "0", "exponent": 0}
    while coefficient.endswith("0"):
        coefficient, exponent = coefficient[:-1], exponent + 1
    if sign:
        coefficient = "-" + coefficient
    _fail(len(coefficient) > 128 or not -10000 <= exponent <= 10000, "MIGRATION_LIMIT")
    return {"coefficient": coefficient, "exponent": exponent}


def _source_number(token):
    _fail(len(token) > 128, "MIGRATION_LIMIT")
    try:
        value = Decimal(token)
    except InvalidOperation:
        raise MigrationError("INVALID_SOURCE") from None
    _fail(not value.is_finite() or not -10000 <= value.as_tuple().exponent <= 10000, "INVALID_SOURCE")
    return value


def _source_integer(token):
    # Confidence is an exact decimal even when its JSON spelling has no dot.
    # Its own field conversion must not inherit the journal integer bound.
    _fail(len(token) > 128, "MIGRATION_LIMIT")
    return int(token)


def _presence(value, path=()):
    result = {}
    if type(value) is dict:
        for key, child in value.items():
            pointer = _pointer((*path, key))
            result[pointer] = "null" if child is None else "present"
            result.update(_presence(child, (*path, key)))
    elif type(value) is list:
        for index, child in enumerate(value):
            result.update(_presence(child, (*path, index)))
    return result


class PlayerStateMigration:
    """Immutable qualification and schemas; pure exact source verification."""

    def __init__(self, adapter_id, source_schemas, target_schemas, resolution):
        try:
            _fail(adapter_id not in SOURCE_SCHEMAS, "UNSUPPORTED_FORMAT")
            self._adapter = adapter_id
            self._source_schemas, self._source_hashes, self._source_validators = _schemas(source_schemas, SOURCE_SCHEMAS)
            self._target_schemas, self._target_hashes, self._validators = _schemas(target_schemas, TARGET_SCHEMAS)
            self._resolution = _copy(resolution)
            r = self._resolution
            _closed(r, RESOLUTION_KEYS)
            _fail(r["format"] != "ywe.player_migration_resolution.v1")
            _sha_value(r["source_sha256"])
            self._scope = TruthScope(r["world_id"], "player_state", r["player_id"])
            self._domain = PlayerDomainPolicy(r["player_profile"])
            _provenance(r["provenance"])
            _fail(not self._validators["spine"].is_valid(r["spine"]))
            _fail(r["spine"]["player_id"] != r["player_id"])
            for key in ("action_refs", "memory_refs", "consumed_action_refs", "consumed_request_refs",
                        "consumed_manifestation_event_ids"):
                _refs(r[key])
            _closed(r["realm_name_map"], ("profile_id", "mappings"))
            _fail(r["realm_name_map"]["profile_id"] != r["player_profile"]["profile_id"]
                  or type(r["realm_name_map"]["mappings"]) is not dict)
            for name, plane in r["realm_name_map"]["mappings"].items():
                _identifier(name)
                _identifier(plane)
            _fail(type(r["fragment_bindings"]) is not list or len(r["fragment_bindings"]) > 128)
            fragments = set()
            for binding in r["fragment_bindings"]:
                _closed(binding, ("fragment_ref", "fragment_id"))
                _identifier(binding["fragment_ref"])
                _identifier(binding["fragment_id"])
                _fail(binding["fragment_ref"] in fragments)
                fragments.add(binding["fragment_ref"])
            _fail(type(r["manifestation_bindings"]) is not list or len(r["manifestation_bindings"]) > 128)
            for binding in r["manifestation_bindings"]:
                _closed(binding, ("manifestation_event_id", "record_ref"))
                _identifier(binding["manifestation_event_id"])
                _identifier(binding["record_ref"])
            _fail([row["manifestation_event_id"] for row in r["manifestation_bindings"]]
                  != r["consumed_manifestation_event_ids"])
            _fail(type(r["consumed_updates"]) is not list or len(r["consumed_updates"]) > 128)
            seen = set()
            for row in r["consumed_updates"]:
                _closed(row, ("update_ref", "consequence_ref"))
                _identifier(row["update_ref"])
                _identifier(row["consequence_ref"])
                _fail(row["update_ref"] in seen)
                seen.add(row["update_ref"])
            self._records = {}
            _fail(type(r["records"]) is not list or len(r["records"]) > 128)
            for row in r["records"]:
                _closed(row, ("ref", "kind", "world_id", "player_id", "branch_ref", "document", "provenance"))
                _object_bytes(row)
                _object_bytes(row["document"])
                _identifier(row["ref"])
                _identifier(row["branch_ref"])
                _provenance(row["provenance"])
                _fail(row["ref"] in self._records or row["ref"] == r["spine"]["origin_progression_state_ref"]
                      or row["world_id"] != r["world_id"] or row["player_id"] != r["player_id"])
                kind = row["kind"]
                _fail(kind not in set(WIRE_VERSIONS) | {"reference", "consequence", "context"})
                if kind in WIRE_VERSIONS:
                    key, version = WIRE_VERSIONS[kind]
                    _fail(row["document"].get(key) != version or not self._validators[kind].is_valid(row["document"]))
                self._records[row["ref"]] = row
        except MigrationError:
            raise
        except (JournalError, ValueError, TypeError, KeyError, UnicodeError, SchemaError, RecursionError):
            raise MigrationError("INVALID_QUALIFICATION") from None

    def resolution(self):
        return _copy(self._resolution)

    def schemas(self):
        return _copy(self._target_schemas)

    def _select(self, selected, ref, kind, category=None, branch=None):
        _identifier(ref)
        row = self._records.get(ref)
        _fail(row is None, "UNRESOLVED_REFERENCE")
        _fail(row["kind"] != kind or branch is not None and row["branch_ref"] != branch)
        doc = row["document"]
        if kind == "reference":
            _closed(doc, ("category", "truth_scope", "subject_id", "source_sha256"))
            _identifier(doc["category"])
            _sha_value(doc["source_sha256"])
            TruthScope(row["world_id"], doc["truth_scope"], doc["subject_id"])
            _fail(category is not None and doc["category"] != category)
            _fail(doc["truth_scope"] in ("player_state", "player_perception")
                  and doc["subject_id"] != row["player_id"])
            _fail(doc["truth_scope"] == "leaf_branch_state" and doc["subject_id"] != row["branch_ref"])
            scopes = {"current_leaf_branch_ref": {"leaf_branch_state"},
                "branch_event_ref": {"leaf_branch_state"}, "branch_event_refs": {"leaf_branch_state"},
                "current_location_ref": {"shared_worldstate", "leaf_branch_state"},
                "active_realm_form": {"shared_worldstate", "leaf_branch_state"},
                "mortal_identity_ref": {"player_state"}, "awakening_fragments": {"player_state"},
                "perception_state_ref": {"player_perception"}, "perception_overlay_refs": {"player_perception"},
                "worldstate_delta_refs": {"shared_worldstate", "leaf_branch_state"}}
            _fail(category in scopes and doc["truth_scope"] not in scopes[category])
        selected[ref] = row
        return doc

    def _select_baseline(self, source):
        r, selected = self._resolution, {}
        spine = r["spine"]
        branch = spine["current_leaf_branch_ref"]
        context = {"world_id": r["world_id"], "player_id": r["player_id"], "branch_ref": branch,
                   "mortal_identity_ref": spine["identity"]["mortal_identity_ref"],
                   "initial": spine["state_lifecycle"] == "initial", "evidence_refs": []}
        self._select(selected, branch, "reference", "current_leaf_branch_ref", branch)
        self._select(selected, context["mortal_identity_ref"], "reference", "mortal_identity_ref")
        if "current_location_ref" in spine:
            self._select(selected, spine["current_location_ref"], "reference", "current_location_ref", branch)
        for kind, (group, field) in SLOTS.items():
            doc = self._select(selected, spine[group][field], kind, branch=branch if kind == "agent" else None)
            self._domain.validate(kind, doc, context)
        agent = selected[spine["state_refs"]["player_agent_state_ref"]]["document"]
        _fail(agent.get("current_location_ref") != spine.get("current_location_ref"))
        _fail(not set(agent.get("recent_action_trace_refs", [])) <= set(r["action_refs"]))
        for field in ("pattern_vector_ref", "existence_potential_ref", "current_plane_pressure_ref"):
            if field in agent:
                self._select(selected, agent[field], "reference", field)
        for ref in agent.get("branch_event_refs", []):
            self._select(selected, ref, "reference", "branch_event_ref")
        history = self._select(selected, spine["state_refs"]["player_branch_history_ref"], "branch_history", branch=branch)
        self._domain.validate("branch_history", history, context)
        ability_ids = set()
        for ref in spine["ability_state_refs"]:
            doc = self._select(selected, ref, "ability", branch=branch)
            self._domain.validate("ability", doc, context)
            _fail(doc["ability_id"] in ability_ids)
            ability_ids.add(doc["ability_id"])
        for ref in spine["state_refs"].get("wolf_manifestation_event_refs", []):
            doc = self._select(selected, ref, "manifestation", branch=branch)
            self._domain.validate("manifestation", doc, context)
            _fail(doc["manifestation_event_id"] not in r["consumed_manifestation_event_ids"])
        for binding in r["manifestation_bindings"]:
            doc = self._select(selected, binding["record_ref"], "manifestation")
            _fail(doc["manifestation_event_id"] != binding["manifestation_event_id"])
            self._domain.validate("manifestation", doc, {**context, "initial": False})
        for group, keys in COLLECTIONS.items():
            for field in keys:
                refs = spine.get(group, {}).get(field, [])
                _refs(refs)
                for ref in refs:
                    self._select(selected, ref, "reference", field)
        for field in ("pattern_vector_ref", "existence_potential_ref"):
            if field in spine["state_refs"]:
                self._select(selected, spine["state_refs"][field], "reference", field)
        for ref in spine["state_refs"].get("companion_reward_delta_refs", []):
            self._select(selected, ref, "reference", "companion_reward_delta_refs")
        for obj in (spine, agent):
            for ref in obj["asp_resilience"]["asp_diagnostic_refs"]:
                self._select(selected, ref, "reference", "asp_diagnostic_refs")
            if "last_valid_snapshot_ref" in obj["asp_resilience"]:
                self._select(selected, obj["asp_resilience"]["last_valid_snapshot_ref"], "reference", "last_valid_snapshot_ref")
        actions = [self._select(selected, ref, "action") for ref in r["action_refs"]]
        memories = [self._select(selected, ref, "memory") for ref in r["memory_refs"]]
        _fail(r["action_refs"] != [row["action_trace_id"] for row in actions]
              or r["memory_refs"] != [row["memory_id"] for row in memories])
        _fail(spine["memory_refs"].get("player_action_trace_refs", []) != r["action_refs"]
              or spine["memory_refs"].get("player_memory_record_refs", []) != r["memory_refs"])
        action_by_id = {row["action_trace_id"]: row for row in actions}
        for action in actions:
            _fail(action["player_id"] != r["player_id"] or action.get("branch_ref") != selected[action["action_trace_id"]]["branch_ref"])
            if "branch_event_ref" in action:
                self._select(selected, action["branch_event_ref"], "reference", "branch_event_ref")
            _refs(action.get("resulting_worldstate_delta_refs", []))
            for ref in action.get("resulting_worldstate_delta_refs", []):
                self._select(selected, ref, "reference", "worldstate_delta_refs", action["branch_ref"])
        for memory in memories:
            action = action_by_id.get(memory["source_action_trace_ref"])
            _fail(action is None or memory.get("branch_ref", action["branch_ref"]) != action["branch_ref"]
                  or selected[memory["memory_id"]]["branch_ref"] != action["branch_ref"])
        for row in history["entries"]:
            action = action_by_id.get(row["source_action_trace_ref"])
            _fail(action is None or action.get("branch_event_ref") != row["branch_event_ref"])
            self._select(selected, row["branch_event_ref"], "reference", "branch_event_ref", row["leaf_branch_ref"])
            for ref in row.get("resulting_worldstate_delta_refs", []):
                self._select(selected, ref, "reference", "worldstate_delta_refs")
        for field in ("pending_update_packet_refs", "rejected_update_packet_refs"):
            for ref in spine["update_control"].get(field, []):
                self._select(selected, ref, "reference", field)
        consumed_effects, effects = [], set()
        for row in r["consumed_updates"]:
            doc = self._select(selected, row["consequence_ref"], "consequence")
            _closed(doc, ("consequence_id", "effect_id", "update_ref", "player_id", "branch_ref", "action_refs", "external_result_refs"))
            for field in ("consequence_id", "effect_id", "update_ref", "player_id", "branch_ref"):
                _identifier(doc[field])
            _refs(doc["action_refs"])
            _refs(doc["external_result_refs"])
            _fail(doc["update_ref"] != row["update_ref"] or doc["player_id"] != r["player_id"]
                  or doc["branch_ref"] != selected[row["consequence_ref"]]["branch_ref"])
            for ref in doc["action_refs"]:
                action = action_by_id.get(ref)
                _fail(action is None or action["branch_ref"] != doc["branch_ref"]
                      or row["update_ref"] not in action.get("resulting_player_state_update_refs", []))
            expected_results = {ref for action_ref in doc["action_refs"]
                                for ref in action_by_id[action_ref].get("resulting_worldstate_delta_refs", [])}
            _fail(set(doc["external_result_refs"]) != expected_results)
            for ref in doc["external_result_refs"]:
                self._select(selected, ref, "reference", "worldstate_delta_refs")
            effect = [doc["consequence_id"], doc["effect_id"], doc["player_id"]]
            _fail(tuple(effect) in effects)
            effects.add(tuple(effect))
            consumed_effects.append({**row, "effect": effect})
        _fail(spine["update_control"].get("accepted_update_packet_refs", []) != [row["update_ref"] for row in r["consumed_updates"]])
        if context["initial"]:
            _fail(actions or memories or history["entries"] or r["consumed_updates"]
                  or r["consumed_action_refs"] or r["consumed_request_refs"] or r["consumed_manifestation_event_ids"], "INCONSISTENT_BASELINE")
            for group in ("memory_refs", "world_links", "relationship_links", "manifestation_links", "progression_refs", "update_control"):
                _fail(any(type(value) is list and value for value in spine.get(group, {}).values()), "INCONSISTENT_BASELINE")
        self._select_context(selected, action_by_id, history)
        return selected, actions, memories, consumed_effects

    def _select_context(self, selected, actions, history):
        r, spine = self._resolution, self._resolution["spine"]
        context = spine.get("runtime_context", {})
        branch = spine["current_leaf_branch_ref"]
        for field in CONTEXT_COLLECTIONS:
            for ref in context.get(field, []):
                doc = self._select(selected, ref, "reference", "branch_event_ref" if field == "branch_event_refs" else field)
                _fail(doc["truth_scope"] == "player_perception")
        if "perception_state_ref" in context:
            self._select(selected, context["perception_state_ref"], "reference", "perception_state_ref")
        if context.get("last_player_action_trace_ref") is not None:
            _fail(context["last_player_action_trace_ref"] not in actions, "UNRESOLVED_REFERENCE")
        if "active_realm_form" in context:
            _fail(context["active_realm_form"] not in r["realm_name_map"]["mappings"])
            self._select(selected, context["active_realm_form"], "reference", "active_realm_form", branch)
        for field, value in context.get("ash_provenance", {}).items():
            for ref in value if type(value) is list else [value]:
                doc = self._select(selected, ref, "reference", field)
                _fail(doc["truth_scope"] == "player_perception")
        celestial = selected[spine["identity"]["celestial_identity_state_ref"]]["document"]
        if "celestial_memory" in context:
            _fail(context["celestial_memory"] != celestial["identity_state"])
        fragments = {row["fragment_id"]: row for row in celestial.get("known_fragments", [])}
        bindings = {row["fragment_ref"]: row["fragment_id"] for row in r["fragment_bindings"]}
        _fail(set(bindings) != set(context.get("awakening_fragments", [])))
        for ref, identity in bindings.items():
            _fail(identity not in fragments or selected[ref]["document"]["source_sha256"] != _digest(fragments[identity]))
        # A legacy branch-event collection remains historical; each event is
        # backed by the retained typed history rather than an arbitrary label.
        events = {row["branch_event_ref"] for row in history["entries"]} | {
            row["branch_event_ref"] for row in actions.values() if "branch_event_ref" in row}
        _fail(not set(context.get("branch_event_refs", [])) <= events)

    def _mapping(self, source, selected):
        r, spine, conversions, rows = self._resolution, self._resolution["spine"], [], []

        def row(path, target, operation="copy"):
            rows.append({"source_pointer": _pointer(path), "target_pointer": target, "operation": operation})

        def copied(value, path, target):
            row(path, target)
            if type(value) is dict:
                for key, child in value.items():
                    copied(child, (*path, key), target + _pointer((key,)))
            elif type(value) is list:
                for index, child in enumerate(value):
                    copied(child, (*path, index), target + "/" + str(index))

        if self._adapter == "closed_reference_v1":
            expected = _copy(spine)
            expected.pop("origin_progression_state_ref")
            expected.pop("ability_state_refs")
            _fail("runtime_context" in expected, "INCONSISTENT_BASELINE")
            if "raven_companion_state_ref" not in source["state_refs"]:
                expected["state_refs"].pop("raven_companion_state_ref")
            expected["schema_id"], expected["schema_version"] = "ywe.player_runtime_state.v1", "0.1.0"
            expected["update_control"]["allowed_update_packet_schema"] = source["update_control"]["allowed_update_packet_schema"]
            _fail(expected != source, "INCONSISTENT_BASELINE")
            copied(source, (), "/baseline/spine")
            for item in rows:
                if item["source_pointer"] in ("/schema_id", "/schema_version"):
                    item["operation"] = "schema_version"
                elif item["source_pointer"] == "/update_control/allowed_update_packet_schema":
                    item["operation"] = "protocol"
            return rows, conversions

        _fail(not set(source) <= HISTORICAL_FIELDS, "UNKNOWN_ACTIVE_FIELD")
        _fail(source["player_ref"] != r["player_id"] or source["current_leaf_branch_ref"] != spine["current_leaf_branch_ref"]
              or source["current_phase"] != r["current_phase"], "INCONSISTENT_BASELINE")
        context = {key: value for key, value in source.items() if key in CONTEXT_FIELDS}
        if "sequence_id" in context:
            _fail(type(context["sequence_id"]) is not int or abs(context["sequence_id"]) > 9007199254740991, "INVALID_SOURCE")
        if "phase_confidence" in context:
            exact = _exact(context["phase_confidence"])
            conversions.append({"source_pointer": "/phase_confidence", "target_pointer": "/baseline/spine/runtime_context/phase_confidence",
                                "source_decimal": str(context["phase_confidence"]), **exact})
            context["phase_confidence"] = exact
        authority, policy = context.get("authority_boundary"), context.get("update_policy")
        _closed(authority, AUTHORITY, "INVALID_SOURCE")
        _closed(policy, UPDATE_POLICY, "INVALID_SOURCE")
        _fail(type(authority["can_influence_generation_context"]) is not bool
              or any(authority[key] is not value for key, value in AUTHORITY.items() if key != "can_influence_generation_context")
              or type(policy["diagnostic_noop_allowed"]) is not bool
              or any(policy[key] is not value for key, value in UPDATE_POLICY.items() if key != "diagnostic_noop_allowed"), "INVALID_SOURCE")
        if "identity_reveal_policy" in context:
            _fail(context["identity_reveal_policy"] != "reveal_through_play", "INVALID_SOURCE")
        if "origin" in context:
            _fail(context["origin"] != "mortal", "INVALID_SOURCE")
        if "celestial_memory" in context:
            _fail(context["celestial_memory"] not in r["player_profile"]["identity_states"], "INVALID_SOURCE")
        ash = context["ash_provenance"]
        _fail(type(ash) is not dict or not set(ash) <= ASH_FIELDS, "UNKNOWN_ACTIVE_FIELD")
        _provenance({key: ash[key] for key in ("cosmic_pattern_snapshot_ref", "diagnostic_ref", "generation_plan_ref", "source_ash_refs")})

        def score(value, path, target, actual):
            q6 = _q6(value)
            _fail(q6 != actual, "INCONSISTENT_BASELINE")
            conversions.append({"source_pointer": _pointer(path), "target_pointer": target,
                                "source_decimal": str(value), "target_q6": q6})
            row(path, target, "exact_q6")

        plane_ref = spine["state_refs"]["plane_attunement_state_ref"]
        planes = selected[plane_ref]["document"]["planes"]
        if "realm_attunement" in source:
            _fail(type(source["realm_attunement"]) is not dict, "INVALID_SOURCE")
            for name, value in source["realm_attunement"].items():
                plane = r["realm_name_map"]["mappings"].get(name)
                _fail(plane not in planes, "INVALID_QUALIFICATION")
                score(value, ("realm_attunement", name), "/baseline/records" + _pointer((plane_ref, "document", "planes", plane, "score_q6")), planes[plane]["score_q6"])
        wolf_ref = spine["state_refs"]["wolf_resonance_summary_ref"]
        if "wolf_resonance" in source:
            wolf = source["wolf_resonance"]
            _fail(type(wolf) is not dict or not set(wolf) <= {"white_wolf", "dark_wolf", "interpretation"}, "UNKNOWN_ACTIVE_FIELD")
            for name in ("white_wolf", "dark_wolf"):
                if name in wolf:
                    score(wolf[name], ("wolf_resonance", name), "/baseline/records" + _pointer((wolf_ref, "document", name, "resonance_q6")), selected[wolf_ref]["document"][name]["resonance_q6"])
            if "interpretation" in wolf:
                _fail(wolf["interpretation"] != "symbiotic_attractors_not_morality_meter", "INVALID_SOURCE")
                context["wolf_interpretation"] = wolf["interpretation"]
                row(("wolf_resonance", "interpretation"), "/baseline/spine/runtime_context/wolf_interpretation")
        blood_ref = spine["state_refs"]["bloodline_resonance_state_ref"]
        if "bloodline_resonance" in source:
            blood = source["bloodline_resonance"]
            _fail(type(blood) is not dict, "INVALID_SOURCE")
            signals = {row["bloodline_id"]: (index, row) for index, row in enumerate(selected[blood_ref]["document"]["signals"])}
            for name, value in blood.items():
                _identifier(name)
                _fail(name not in signals, "INCONSISTENT_BASELINE")
                index, signal = signals[name]
                score(value, ("bloodline_resonance", name), "/baseline/records" + _pointer((blood_ref, "document", "signals", index, "score_q6")), signal["score_q6"])
        _fail(context != spine.get("runtime_context"), "INCONSISTENT_BASELINE")
        for source_field, target_field in (("active_worldstate_delta_refs", "worldstate_delta_refs"),
                                           ("future_generation_bias_refs", "future_generation_bias_refs")):
            if source_field in source:
                _fail(source[source_field] != spine["world_links"][target_field], "INCONSISTENT_BASELINE")
        for field, value in source.items():
            if field in CONTEXT_FIELDS:
                target = "/baseline/spine/runtime_context/" + field
                if field == "phase_confidence":
                    row((field,), target, "exact_decimal")
                else:
                    copied(value, (field,), target)
            elif field in ("record_type", "version"):
                row((field,), "/source_format" if field == "record_type" else "/source_version", "source_discriminator")
            elif field in ("realm_attunement", "wolf_resonance", "bloodline_resonance"):
                row((field,), "/baseline/records", "qualified_component")
            elif field == "current_phase":
                row((field,), "/origin_baseline/current_phase")
            else:
                target = {"player_ref": "/baseline/spine/player_id", "current_leaf_branch_ref": "/baseline/spine/current_leaf_branch_ref",
                    "active_worldstate_delta_refs": "/baseline/spine/world_links/worldstate_delta_refs",
                    "future_generation_bias_refs": "/baseline/spine/world_links/future_generation_bias_refs"}[field]
                copied(value, (field,), target)
        return rows, conversions

    def migrate(self, raw_source_bytes):
        try:
            _fail(type(raw_source_bytes) is not bytes, "INVALID_SOURCE")
            _fail(len(raw_source_bytes) > 65536, "MIGRATION_LIMIT")
            source = json.loads(raw_source_bytes.decode("utf-8"), object_pairs_hook=_pairs,
                                parse_float=_source_number, parse_int=_source_integer, parse_constant=_nonfinite)
            _bounded(source)
            _fail(type(source) is not dict, "INVALID_SOURCE")
            _fail("schema_id" in source and "record_type" in source, "UNSUPPORTED_FORMAT")
            r = self._resolution
            _fail(_sha(raw_source_bytes) != r["source_sha256"], "INVALID_QUALIFICATION")
            discriminator, version_key, format_id, version = (
                ("schema_id", "schema_version", "ywe.player_runtime_state.v1", "0.1.0")
                if self._adapter == "closed_reference_v1" else ("record_type", "version", "PlayerRuntimeState", "1.0.0"))
            _fail(source.get(discriminator) != format_id, "UNSUPPORTED_FORMAT")
            _fail(source.get(version_key) != version, "UNSUPPORTED_VERSION")
            validator = self._source_validators[self._adapter]
            if self._adapter == "historical_record_v1":
                _fail(not set(source) <= HISTORICAL_FIELDS, "UNKNOWN_ACTIVE_FIELD")
                definition = self._source_schemas[self._adapter]["$defs"]["PlayerRuntimeState"]
                validator = validator.evolve(schema=definition)
            _fail(not validator.is_valid(source), "INVALID_SOURCE")
            selected, actions, memories, effects = self._select_baseline(source)
            mappings, conversions = self._mapping(source, selected)
            qualified = {**r, "records": [selected[key] for key in sorted(selected)]}
            qualification_sha = _sha(_configuration_bytes(qualified))
            selected_hashes = {key: _digest(value) for key, value in sorted(selected.items())}
            anchor = _sha(_configuration_bytes({"adapter_id": self._adapter, "source_sha256": r["source_sha256"],
                "source_schema_digests": self._source_hashes, "target_schema_digests": self._target_hashes,
                "qualification_sha256": qualification_sha, "selected_record_sha256": selected_hashes}))
            origin_baseline = {"format": "ywe.origin_baseline.v1", "world_id": r["world_id"],
                "player_id": r["player_id"], "profile_id": r["origin_profile"]["profile_id"],
                "source_sha256": r["source_sha256"], "import_anchor": anchor, "current_phase": r["current_phase"],
                "actions": actions, "memories": memories, "consumed_action_refs": r["consumed_action_refs"],
                "provenance": r["provenance"]}
            origin = OriginProgressionPolicy.from_baseline(origin_baseline, r["world_id"], r["player_id"],
                r["origin_profile"], r["creation"], {"migration:validator": ["advance", "remember"]}, [],
                self._target_schemas["action"], self._target_schemas["memory"]).initial_state()
            _fail(origin["creation"]["mortal_identity_ref"] != r["spine"]["identity"]["mortal_identity_ref"])
            if r["spine"]["state_lifecycle"] == "initial":
                _fail(r["current_phase"] != r["origin_profile"]["initial_phase"], "INCONSISTENT_BASELINE")
            entries = {key: {"kind": value["kind"], "document": value["document"], "sha256": _digest(value["document"])}
                       for key, value in selected.items()}
            entries[r["spine"]["origin_progression_state_ref"]] = {"kind": "origin", "document": origin, "sha256": _digest(origin)}
            baseline = {"format": "ywe.player_aggregate.v2", "world_id": r["world_id"], "player_id": r["player_id"],
                "profile_id": r["player_profile"]["profile_id"], "spine": r["spine"], "records": entries,
                "accepted_updates": [], "compensations": [], "import_baseline": {
                    "source_sha256": r["source_sha256"], "import_anchor": anchor,
                    "consumed_update_refs": [row["update_ref"] for row in r["consumed_updates"]],
                    "consumed_request_refs": r["consumed_request_refs"], "consumed_effects": effects,
                    "consumed_manifestation_event_ids": r["consumed_manifestation_event_ids"], "provenance": r["provenance"]}}
            _fail(not self._validators["origin"].is_valid(origin) or not self._validators["snapshot"].is_valid(baseline), "INCONSISTENT_BASELINE")
            target_sha = _digest(baseline)
            result = {"format": "ywe.player_state_migration.v1", "adapter_id": self._adapter,
                "migration_id": "player." + self._adapter + ".v1", "world_id": r["world_id"], "player_id": r["player_id"],
                "source_format": format_id, "source_version": version, "source_sha256": r["source_sha256"],
                "source_schema_digests": self._source_hashes, "target_schema_digests": self._target_hashes,
                "qualification_sha256": qualification_sha, "selected_record_sha256": selected_hashes,
                "import_anchor": anchor, "source_presence_map": _presence(source), "field_mapping_rows": mappings,
                "decimal_conversion_rows": conversions, "origin_baseline": origin_baseline, "baseline": baseline,
                "target_sha256": target_sha}
            return _copy(result)
        except MigrationError:
            raise
        except JournalError as error:
            raise MigrationError("MIGRATION_LIMIT" if error.code == "VALUE_LIMIT" else "INVALID_QUALIFICATION") from None
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            raise MigrationError("INVALID_SOURCE") from None

    def verify(self, raw_source_bytes, result):
        try:
            return _configuration_bytes(result) == _configuration_bytes(self.migrate(raw_source_bytes))
        except (MigrationError, JournalError, ValueError, TypeError, UnicodeError, RecursionError):
            return False
