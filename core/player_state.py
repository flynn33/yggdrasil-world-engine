"""Atomic player reference admission (YWE-REQ-0056), with explicit trusted inputs."""

import json
import re

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .narrative_engine.origin_progression import (
    OriginProgressionPolicy, _closed, _digest, _items, _provenance, _refs,
)
from .player_state_rules import PlayerDomainPolicy
from .state_journal import CommitJournal, JournalError, TruthScope, _identifier, _object_bytes


FORMAT = "ywe.player_aggregate.v1"
IMPORTED_FORMAT = "ywe.player_aggregate.v2"
SCHEMAS = {
    "spine": "m4_player_runtime_state", "celestial": "celestial_identity_state",
    "agent": "player_agent_state", "branch_history": "player_branch_history",
    "plane": "m4_plane_attunement_state", "bloodline": "m4_bloodline_resonance_state",
    "wolf": "m4_wolf_resonance_summary", "raven": "raven_companion_state",
    "ability": "m4_ability_state", "manifestation": "wolf_manifestation_event",
    "action": "player_action_trace", "memory": "player_memory_record",
}
WIRE_VERSIONS = {
    "celestial": ("schema_version", "0.1.0"), "agent": ("schema_version", "0.1.0"),
    "branch_history": ("schema_version", "0.1.0"), "action": ("schema_version", "0.1.0"),
    "memory": ("schema_version", "0.1.0"), "raven": ("version", "1.0.0"),
    "manifestation": ("version", "1.0.0"), "plane": ("schema_version", "2.0.0"),
    "bloodline": ("schema_version", "2.0.0"), "wolf": ("schema_version", "2.0.0"),
    "ability": ("schema_version", "2.0.0"),
}
SLOTS = {
    "celestial": ("identity", "celestial_identity_state_ref"),
    "agent": ("state_refs", "player_agent_state_ref"),
    "plane": ("state_refs", "plane_attunement_state_ref"),
    "bloodline": ("state_refs", "bloodline_resonance_state_ref"),
    "wolf": ("state_refs", "wolf_resonance_summary_ref"),
    "raven": ("state_refs", "raven_companion_state_ref"),
}
COLLECTIONS = {
    "memory_refs": ("quest_history_refs", "major_choice_refs", "oath_refs", "discovery_refs"),
    "progression_refs": ("progression_signal_refs", "ability_pressure_refs",
                         "identity_reveal_pressure_refs", "threshold_access_refs"),
    "world_links": ("worldstate_delta_refs", "location_state_refs", "location_mutation_refs",
                    "future_generation_bias_refs", "diagnostic_noop_refs"),
    "relationship_links": ("npc_relationship_refs", "faction_standing_refs", "faction_claim_exposure_refs"),
    "manifestation_links": ("artifact_binding_refs", "creature_encounter_refs", "myth_participation_refs",
                            "myth_seed_refs", "prophecy_pressure_refs", "perception_overlay_refs"),
}
SOURCE_OPERATIONS = {
    "narrative_engine": {"origin", "celestial", "agent", "plane", "bloodline", "wolf", "raven",
                         "ability", "manifest", "dismiss", "append", "branch", "compensate"},
    "runtime_cosmology": {"origin", "agent", "branch", "append"},
    "realm_engine": {"origin", "plane", "append"},
    "perception_engine": {"origin", "append"},
    "quest_engine": {"origin", "append"},
}
CATEGORY_SCOPES = {
    "worldstate_delta_refs": {"shared_worldstate", "leaf_branch_state"},
    "current_leaf_branch_ref": {"leaf_branch_state"},
    "branch_event_ref": {"leaf_branch_state"},
    "current_location_ref": {"shared_worldstate", "leaf_branch_state"},
    "perception_overlay_refs": {"player_perception"},
    "mortal_identity_ref": {"player_state"},
    "evidence_refs": {"shared_worldstate", "leaf_branch_state", "player_state"},
}
CONTEXT_COLLECTIONS = (
    "branch_generation_context_refs", "branch_event_refs", "awakening_fragments",
    "narrative_memory_refs", "relationship_state_refs", "faction_stance_refs",
    "unresolved_tension_refs", "active_quest_refs", "completed_resolution_refs",
    "generation_context_refs",
)
CONTEXT_FIELDS = frozenset(CONTEXT_COLLECTIONS) | {
    "phase_confidence", "celestial_memory", "active_realm_form", "active_realm_form_ref", "perception_state_ref",
}
CONTEXT_SOURCES = {
    "narrative_engine": {"phase_confidence", "celestial_memory", "awakening_fragments",
                         "narrative_memory_refs", "relationship_state_refs", "faction_stance_refs",
                         "unresolved_tension_refs"},
    "runtime_cosmology": {"branch_generation_context_refs", "branch_event_refs", "generation_context_refs"},
    "realm_engine": {"active_realm_form", "active_realm_form_ref"},
    "perception_engine": {"perception_state_ref"},
    "quest_engine": {"active_quest_refs", "completed_resolution_refs"},
}


def _copy(value):
    return json.loads(_object_bytes(value))


def _reject(condition):
    if condition:
        raise JournalError("POLICY_REJECTED")


def _context_value(field, value):
    if field in CONTEXT_COLLECTIONS:
        _refs(value, 0, 128)
    elif field == "phase_confidence":
        _closed(value, "coefficient exponent")
        _reject(type(value["coefficient"]) is not str or len(value["coefficient"]) > 128
                or re.fullmatch(r"(?:0|-?[1-9](?:[0-9]*[1-9])?)", value["coefficient"]) is None
                or type(value["exponent"]) is not int or not -10000 <= value["exponent"] <= 10000
                or value["coefficient"] == "0" and value["exponent"] != 0)
    else:
        _identifier(value)


def _realm_form(document, world_id, branch):
    _closed(document, "form_name plane_id truth_scope subject_id source_sha256")
    for field in ("form_name", "plane_id", "subject_id"):
        _identifier(document[field])
    TruthScope(world_id, document["truth_scope"], document["subject_id"])
    _reject(document["truth_scope"] not in ("shared_worldstate", "leaf_branch_state")
            or document["truth_scope"] == "leaf_branch_state" and document["subject_id"] != branch)
    _reject(type(document["source_sha256"]) is not str
            or re.fullmatch(r"[0-9a-f]{64}", document["source_sha256"]) is None)


def _schema(schema, name):
    schema = _copy(schema)
    if (schema.get("$id") != "https://ywe.local/schemas/" + name + "_schema.json"
            or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"):
        raise JournalError("INVALID_POLICY")
    pending = [schema]
    while pending:
        node = pending.pop()
        if type(node) is dict:
            if "$dynamicRef" in node or "$ref" in node and (
                    type(node["$ref"]) is not str or not node["$ref"].startswith("#/")):
                raise JournalError("INVALID_POLICY")
            if node is not schema and "$id" in node:
                raise JournalError("INVALID_POLICY")
            pending.extend(node.values())
        elif type(node) is list:
            pending.extend(node)
    Draft202012Validator.check_schema(schema)
    checked = set()

    def check_local(node, active):
        if type(node) not in (dict, list):
            return
        identity = id(node)
        if identity in active:
            raise JournalError("INVALID_POLICY")
        if identity in checked:
            return
        active = active | {identity}
        if type(node) is dict:
            if "$ref" in node:
                target = schema
                for part in node["$ref"][2:].split("/"):
                    part = part.replace("~1", "/").replace("~0", "~")
                    if type(target) is not dict or part not in target:
                        raise JournalError("INVALID_POLICY")
                    target = target[part]
                if type(target) not in (dict, bool):
                    raise JournalError("INVALID_POLICY")
                check_local(target, active)
            for child in node.values():
                check_local(child, active)
        else:
            for child in node:
                check_local(child, active)
        checked.add(identity)

    check_local(schema, set())
    return Draft202012Validator(schema), _digest(_object_bytes(schema))


class PlayerStateStore:
    """Trusted catalog owner; expose only restricted handles to calling systems."""

    def __init__(self, world_id, player_id, profile, initial_spine, grants, records,
                 updates, schemas, origin_policy):
        self._initialize(world_id, player_id, profile, initial_spine, grants, records,
                         updates, schemas, origin_policy)

    def _initialize(self, world_id, player_id, profile, initial_spine, grants, records,
                    updates, schemas, origin_policy, migration_result=None, migration_resolution=None):
        self._scope = TruthScope(world_id, "player_state", player_id)
        try:
            self._imported = migration_result is not None
            self._realm_form_names = (_copy(migration_resolution["realm_name_map"]["mappings"])
                                      if self._imported else {})
            self._profile = _copy(profile)
            self._domain = PlayerDomainPolicy(self._profile)
            self._grants = _copy(grants)
            if not 1 <= len(self._grants) <= 32:
                raise JournalError("INVALID_POLICY")
            for principal, grant in self._grants.items():
                _identifier(principal)
                _closed(grant, "source_system operations")
                _refs(grant["operations"], 1, 16)
                if (grant["source_system"] not in SOURCE_OPERATIONS
                        or not set(grant["operations"]) <= (
                            SOURCE_OPERATIONS[grant["source_system"]] | ({"context"} if self._imported else set()))):
                    raise JournalError("INVALID_POLICY")
            if type(origin_policy) is not OriginProgressionPolicy or origin_policy.scope != self._scope:
                raise JournalError("INVALID_POLICY")
            self._origin = origin_policy
            self._validators, schema_hashes = {}, {}
            _closed(schemas, " ".join(SCHEMAS))
            for kind, name in SCHEMAS.items():
                if self._imported and kind == "spine":
                    name = "m4_player_runtime_state_v3"
                self._validators[kind], schema_hashes[kind] = _schema(schemas[kind], name)
            self._records = self._catalog(records, "ref")
            self._updates = self._catalog(updates, "update_ref")
            self._writers = {principal: object() for principal in self._grants}
            self._spine = _copy(initial_spine)
            if (not self._validators["spine"].is_valid(self._spine)
                    or not self._imported and self._spine["state_lifecycle"] != "initial"
                    or self._spine["player_id"] != player_id):
                raise JournalError("INVALID_POLICY")
            self._origin_ref = self._spine["origin_progression_state_ref"]
            _identifier(self._origin_ref)
            if self._origin_ref in self._records:
                raise JournalError("INVALID_POLICY")
            origin = origin_policy.initial_state()
            if origin["format"] != ("ywe.origin_progression.v2" if self._imported else "ywe.origin_progression.v1"):
                raise JournalError("INVALID_POLICY")
            if origin["creation"]["mortal_identity_ref"] != self._spine["identity"]["mortal_identity_ref"]:
                raise JournalError("INVALID_POLICY")
            self._initial = {"format": FORMAT, "world_id": world_id, "player_id": player_id,
                "profile_id": profile["profile_id"], "spine": self._spine,
                "records": {self._origin_ref: self._entry("origin", origin)},
                "accepted_updates": [], "compensations": []}
            if self._imported:
                self._initial = _copy(migration_result["baseline"])
                _reject(self._initial["format"] != IMPORTED_FORMAT
                        or self._initial["spine"] != self._spine
                        or self._initial["records"].get(self._origin_ref) != self._entry("origin", origin))
                for ref, entry in self._initial["records"].items():
                    if ref != self._origin_ref:
                        source = json.loads(self._records[ref])
                        _reject(entry != self._entry(source["kind"], source["document"]))
                original = _copy(self._initial)
                self._validate_state(self._initial, self._spine["state_lifecycle"] == "initial", [])
                _reject(original != self._initial)
            else:
                self._validate_state(self._initial, True, [])
            # Creation cannot smuggle historical consequences or unreplayed memory.
            if not self._imported or self._spine["state_lifecycle"] == "initial":
                for group in ("memory_refs", "world_links", "relationship_links", "manifestation_links",
                              "progression_refs", "update_control"):
                    for value in self._spine.get(group, {}).values():
                        if type(value) is list and value:
                            raise JournalError("INVALID_POLICY")
                if self._spine["state_refs"].get("wolf_manifestation_event_refs", []):
                    raise JournalError("INVALID_POLICY")
            policy = {"format": FORMAT, "scope": self._scope.to_record(), "profile": self._profile,
                      "initial_spine": self._spine, "grants": self._grants,
                      "schema_sha256": schema_hashes, "origin_policy_id": origin_policy.policy_id,
                      "initial_record_sha256": {ref: _digest(self._records[ref])
                          for ref in self._initial["records"] if ref != self._origin_ref}}
            if self._imported:
                policy.update(format=IMPORTED_FORMAT, migration_id=migration_result["migration_id"],
                              migration_target_sha256=migration_result["target_sha256"],
                              import_anchor=migration_result["import_anchor"])
            self._policy_id = ("player.v2:" if self._imported else "player.v1:") + _digest(_object_bytes(policy))
            self._journal = CommitJournal(self._scope, self._policy_id, self._initial, self._reduce)
        except (JournalError, SchemaError, KeyError, TypeError, ValueError):
            raise JournalError("INVALID_POLICY") from None

    @classmethod
    def from_migration(cls, result, migration, raw_source, *configuration):
        """Activate a freshly reverified source-bound baseline, never a bare snapshot."""
        from .player_state_migration import PlayerStateMigration

        try:
            _reject(type(migration) is not PlayerStateMigration or len(configuration) != 9)
            _reject(migration.verify(raw_source, result) is not True)
            qualification = migration.resolution()
            world, player, profile, spine, grants, records, updates, schemas, origin = configuration
            _reject((world, player) != (result["world_id"], result["player_id"])
                    or profile != qualification["player_profile"] or spine != result["baseline"]["spine"]
                    or type(origin) is not OriginProgressionPolicy
                    or origin.profile != qualification["origin_profile"]
                    or origin.initial_state()["creation"] != qualification["creation"])
            _closed(schemas, " ".join(SCHEMAS))
            for kind, schema in schemas.items():
                _reject(_digest(_object_bytes(schema)) != result["target_schema_digests"][kind])
            owner = cls.__new__(cls)
            owner._initialize(*configuration, migration_result=result, migration_resolution=qualification)
            actual = {ref: _digest(owner._records[ref]) for ref in owner._initial["records"]
                      if ref != owner._origin_ref}
            _reject(actual != result["selected_record_sha256"])
            return owner
        except (JournalError, KeyError, TypeError, ValueError, AttributeError):
            raise JournalError("INVALID_MIGRATION") from None

    def _catalog(self, sources, identity):
        _items(sources, 0, 128)
        catalog, total = {}, 0
        for source in sources:
            raw = _object_bytes(source)
            item = json.loads(raw)
            if identity == "ref":
                _closed(item, "ref kind world_id player_id branch_ref document provenance")
                kinds = set(SCHEMAS) - {"spine"} | {"reference", "consequence"}
                if self._imported:
                    kinds.update(("context", "realm_form"))
                if item["kind"] not in kinds:
                    raise JournalError("INVALID_POLICY")
                _object_bytes(item["document"])
                if item["kind"] in self._validators and not self._validators[item["kind"]].is_valid(item["document"]):
                    raise JournalError("INVALID_POLICY")
                if item["kind"] in WIRE_VERSIONS:
                    key, version = WIRE_VERSIONS[item["kind"]]
                    if item["document"].get(key) != version:
                        raise JournalError("INVALID_POLICY")
                if item["kind"] == "realm_form":
                    _realm_form(item["document"], self._scope.world_id, item["branch_ref"])
                if item["kind"] == "context":
                    keys = "field previous_value value phase"
                    if "resolution" in item["document"]:
                        keys += " resolution"
                        _reject(item["document"].get("field") not in ("active_quest_refs", "unresolved_tension_refs"))
                    _closed(item["document"], keys)
                    _reject(item["document"]["field"] not in CONTEXT_FIELDS)
                    _identifier(item["document"]["phase"])
                    for key in ("previous_value", "value"):
                        _context_value(item["document"]["field"], item["document"][key])
                    if "resolution" in item["document"]:
                        resolution = item["document"]["resolution"]
                        _closed(resolution, "removed_refs action_refs reason_refs disposition")
                        for key in ("removed_refs", "action_refs", "reason_refs"):
                            _refs(resolution[key], 1, 128)
                        _reject(resolution["disposition"] not in ("resolved", "cancelled"))
            else:
                _closed(item, "update_ref world_id player_id branch_ref source_system operations evidence_refs consequence_ref provenance")
                _items(item["operations"], 1, 16)
                _refs(item["evidence_refs"], 1, 128)
                _identifier(item["consequence_ref"])
            _identifier(item[identity])
            _identifier(item["branch_ref"])
            _provenance(item["provenance"])
            if (item[identity] in catalog or item["world_id"] != self._scope.world_id
                    or item["player_id"] != self._scope.subject_id):
                raise JournalError("INVALID_POLICY")
            total += len(raw)
            if total > 1048576:
                raise JournalError("VALUE_LIMIT")
            catalog[item[identity]] = raw
        return catalog

    @staticmethod
    def _entry(kind, document):
        return {"kind": kind, "document": _copy(document), "sha256": _digest(_object_bytes(document))}

    def _record(self, state, reference, kind, branch=None, category=None):
        _identifier(reference)
        raw = self._records.get(reference)
        if raw is None:
            raise JournalError("UNKNOWN_EVIDENCE")
        item = json.loads(raw)
        _reject(item["kind"] != kind or branch is not None and item["branch_ref"] != branch)
        document = item["document"]
        if kind == "reference":
            _closed(document, "category truth_scope subject_id source_sha256")
            _identifier(document["category"])
            TruthScope(self._scope.world_id, document["truth_scope"], document["subject_id"])
            digest = document["source_sha256"]
            _reject(type(digest) is not str or len(digest) != 64
                    or any(char not in "0123456789abcdef" for char in digest))
            _reject(category is not None and document["category"] != category)
            _reject(document["category"] in CATEGORY_SCOPES
                    and document["truth_scope"] not in CATEGORY_SCOPES[document["category"]])
            if document["truth_scope"] in ("player_state", "player_perception"):
                _reject(document["subject_id"] != self._scope.subject_id)
            if document["truth_scope"] == "leaf_branch_state":
                _reject(document["subject_id"] != item["branch_ref"])
        entry = self._entry(kind, document)
        _reject(reference in state["records"] and state["records"][reference] != entry)
        state["records"][reference] = entry
        return document

    def _context(self, state, initial=False, evidence=()):
        spine = state["spine"]
        return {"world_id": self._scope.world_id, "player_id": self._scope.subject_id,
                "mortal_identity_ref": spine["identity"]["mortal_identity_ref"],
                "branch_ref": spine["current_leaf_branch_ref"], "initial": initial,
                "evidence_refs": list(evidence)}

    def _validate_state(self, state, initial=False, evidence=()):
        spine = state["spine"]
        _reject(not self._validators["spine"].is_valid(spine))
        context = self._context(state, initial, evidence)
        branch = context["branch_ref"]
        origin = state["records"][self._origin_ref]["document"]
        actions = {row["action_trace_id"]: row for row in origin["actions"]}
        branch_record = self._record(state, branch, "reference", branch, "current_leaf_branch_ref")
        _reject(branch_record["truth_scope"] != "leaf_branch_state")
        self._record(state, context["mortal_identity_ref"], "reference", category="mortal_identity_ref")
        if "current_location_ref" in spine:
            self._record(state, spine["current_location_ref"], "reference", branch, "current_location_ref")
        for kind, (group, key) in SLOTS.items():
            document = self._record(state, spine[group][key], kind, branch if kind == "agent" else None)
            self._domain.validate(kind, document, context)
            if kind == "agent":
                _reject(document.get("current_location_ref") != spine.get("current_location_ref"))
                _refs(document.get("recent_action_trace_refs", []), 0, 128)
                _reject(not set(document.get("recent_action_trace_refs", [])) <= set(actions))
                for ref in document.get("branch_event_refs", []):
                    self._record(state, ref, "reference", category="branch_event_ref")
                for ref in document["asp_resilience"]["asp_diagnostic_refs"]:
                    self._record(state, ref, "reference", category="asp_diagnostic_refs")
                for key in ("pattern_vector_ref", "existence_potential_ref", "current_plane_pressure_ref"):
                    if key in document:
                        self._record(state, document[key], "reference", category=key)
                if "last_valid_snapshot_ref" in document["asp_resilience"]:
                    self._record(state, document["asp_resilience"]["last_valid_snapshot_ref"], "reference", category="last_valid_snapshot_ref")
        history = self._record(state, spine["state_refs"]["player_branch_history_ref"], "branch_history", branch)
        self._domain.validate("branch_history", history, context)
        if initial:
            _reject(bool(history["entries"]))
        for row in history["entries"]:
            action = actions.get(row["source_action_trace_ref"])
            _reject(action is None or action.get("branch_event_ref") != row["branch_event_ref"])
            self._record(state, row["branch_event_ref"], "reference", row["leaf_branch_ref"], "branch_event_ref")
            for ref in row.get("resulting_worldstate_delta_refs", []):
                self._record(state, ref, "reference", category="worldstate_delta_refs")
        abilities = set()
        for ref in spine["ability_state_refs"]:
            document = self._record(state, ref, "ability", branch)
            self._domain.validate("ability", document, context)
            _reject(document["ability_id"] in abilities)
            abilities.add(document["ability_id"])
        for ref in spine["state_refs"].get("wolf_manifestation_event_refs", []):
            document = self._record(state, ref, "manifestation", branch)
            self._domain.validate("manifestation", document, context)
        for group, keys in COLLECTIONS.items():
            for key in keys:
                refs = spine.get(group, {}).get(key, [])
                _refs(refs, 0, 128)
                for ref in refs:
                    self._record(state, ref, "reference", category=key)
        for key in ("pattern_vector_ref", "existence_potential_ref"):
            if key in spine["state_refs"]:
                self._record(state, spine["state_refs"][key], "reference", category=key)
        for ref in spine["state_refs"].get("companion_reward_delta_refs", []):
            self._record(state, ref, "reference", category="companion_reward_delta_refs")
        for ref in spine["asp_resilience"]["asp_diagnostic_refs"]:
            self._record(state, ref, "reference", category="asp_diagnostic_refs")
        if "last_valid_snapshot_ref" in spine["asp_resilience"]:
            self._record(state, spine["asp_resilience"]["last_valid_snapshot_ref"], "reference", category="last_valid_snapshot_ref")
        for kind, collection, identity in (("action", "actions", "action_trace_id"), ("memory", "memories", "memory_id")):
            key = "player_action_trace_refs" if kind == "action" else "player_memory_record_refs"
            _reject(spine["memory_refs"].get(key, []) != [row[identity] for row in origin[collection]])
            for row in origin[collection]:
                _reject(state["records"].get(row[identity]) != self._entry(kind, row))
        if self._imported:
            for action in origin["actions"]:
                if "branch_event_ref" in action:
                    self._record(state, action["branch_event_ref"], "reference", category="branch_event_ref")
                for ref in action.get("resulting_worldstate_delta_refs", []):
                    self._record(state, ref, "reference", action["branch_ref"], "worldstate_delta_refs")
            self._validate_runtime_context(state)
            for key in ("pending_update_packet_refs", "rejected_update_packet_refs"):
                for ref in spine["update_control"].get(key, []):
                    self._record(state, ref, "reference", category=key)
            imported = state["import_baseline"]
            known_updates = imported["consumed_update_refs"] + [row["update_ref"] for row in state["accepted_updates"]]
            _reject(spine["update_control"].get("accepted_update_packet_refs", []) != known_updates)
        _reject(len(state["records"]) > 128 or len(state["accepted_updates"]) > 128)
        _object_bytes(state)

    def _validate_runtime_context(self, state):
        context = state["spine"].get("runtime_context", {})
        branch = state["spine"]["current_leaf_branch_ref"]
        celestial_ref = state["spine"]["identity"]["celestial_identity_state_ref"]
        celestial = state["records"][celestial_ref]["document"]
        if "celestial_memory" in context:
            _reject(context["celestial_memory"] != celestial["identity_state"])
        if "phase_confidence" in context:
            _context_value("phase_confidence", context["phase_confidence"])
        origin = state["records"][self._origin_ref]["document"]
        actions = {row["action_trace_id"] for row in origin["actions"]}
        if context.get("last_player_action_trace_ref") is not None:
            _reject(context["last_player_action_trace_ref"] not in actions)
        if "active_realm_form" in context:
            _reject(context["active_realm_form"] not in self._realm_form_names)
            row = self._record(state, context["active_realm_form_ref"], "realm_form")
            _realm_form(row, self._scope.world_id, branch)
            plane = state["records"][state["spine"]["state_refs"]["plane_attunement_state_ref"]]["document"]
            _reject(row["form_name"] != context["active_realm_form"]
                    or row["plane_id"] != self._realm_form_names[context["active_realm_form"]]
                    or row["plane_id"] not in plane["planes"])
        if "perception_state_ref" in context:
            row = self._record(state, context["perception_state_ref"], "reference", category="perception_state_ref")
            _reject(row["truth_scope"] != "player_perception")
        fragment_hashes = {_digest(_object_bytes(row)) for row in celestial.get("known_fragments", [])}
        history = state["records"][state["spine"]["state_refs"]["player_branch_history_ref"]]["document"]
        events = {row["branch_event_ref"] for row in history["entries"]}
        events.update(row["branch_event_ref"] for row in origin["actions"] if "branch_event_ref" in row)
        for field in CONTEXT_COLLECTIONS:
            for ref in context.get(field, []):
                category = "branch_event_ref" if field == "branch_event_refs" else field
                row = self._record(state, ref, "reference", category=category)
                if field == "awakening_fragments":
                    _reject(row["truth_scope"] != "player_state" or row["source_sha256"] not in fragment_hashes)
                elif field == "branch_event_refs":
                    _reject(row["truth_scope"] != "leaf_branch_state" or ref not in events)
                else:
                    _reject(row["truth_scope"] == "player_perception")
        for field, value in context.get("ash_provenance", {}).items():
            for ref in value if type(value) is list else [value]:
                row = self._record(state, ref, "reference", category=field)
                _reject(row["truth_scope"] == "player_perception")

    def _change_context(self, state, operation, context, source, prior_phase, actions):
        _closed(operation, "kind context_ref condition_refs")
        _reject(not self._imported)
        _refs(operation["condition_refs"], 1, 128)
        _reject(not set(operation["condition_refs"]) <= set(context["evidence_refs"]))
        change = self._record(state, operation["context_ref"], "context", context["branch_ref"])
        current = state["spine"].get("runtime_context", {})
        field = change["field"]
        phase = state["records"][self._origin_ref]["document"]["current_phase"]
        _reject(field not in CONTEXT_SOURCES[source] or field not in current
                or change["phase"] != phase or change["previous_value"] != current[field]
                or change["value"] == current[field]
                and not (field == "phase_confidence" and phase != prior_phase))
        if field in CONTEXT_COLLECTIONS:
            _refs(change["value"], 0, 128)
            before, after = current[field], change["value"]
            if field in ("active_quest_refs", "unresolved_tension_refs"):
                retained = [ref for ref in before if ref in after]
                _reject(after[:len(retained)] != retained)
                removed = [ref for ref in before if ref not in after]
                if removed:
                    resolution = change.get("resolution")
                    _closed(resolution, "removed_refs action_refs reason_refs disposition")
                    _reject(resolution["removed_refs"] != removed or resolution["disposition"] not in ("resolved", "cancelled"))
                    _refs(resolution["action_refs"], 1, 16)
                    _refs(resolution["reason_refs"], 1, 128)
                    _reject(not set(resolution["reason_refs"]) <= set(operation["condition_refs"]))
                    selected = [row for row in actions if row["action_trace_id"] in resolution["action_refs"]]
                    _reject(len(selected) != len(resolution["action_refs"])
                            or not set(removed) <= {ref for row in selected for ref in row.get("affected_entity_refs", [])}
                            or field == "active_quest_refs" and any(row["action_kind"] != "quest_resolution" for row in selected))
                else:
                    _reject("resolution" in change)
            else:
                _reject(after[:len(before)] != before)
        current[field] = _copy({"value": change["value"]})["value"]
        return field

    def writer(self, principal):
        _identifier(principal)
        if principal not in self._writers:
            raise JournalError("UNAUTHORIZED_WRITER")
        return self._writers[principal]

    def _packet(self, principal, request_id, update_ref):
        _identifier(request_id)
        _identifier(update_ref)
        raw = self._updates.get(update_ref)
        if raw is None:
            raise JournalError("UNKNOWN_EVIDENCE")
        update = json.loads(raw)
        if principal not in self._grants or self._grants[principal]["source_system"] != update["source_system"]:
            raise JournalError("UNAUTHORIZED_WRITER")
        references = set(update["evidence_refs"]) | {update["consequence_ref"]}
        origin_packet = None
        compensates = None
        for operation in update["operations"]:
            if type(operation) is not dict:
                raise JournalError("POLICY_REJECTED")
            if operation.get("kind") == "origin":
                _reject(origin_packet is not None)
                origin_packet = self._origin.packet(principal, request_id, operation.get("evidence_ref"))
                for action in self._origin.evidence(operation["evidence_ref"])["actions"]:
                    references.update(action.get("resulting_worldstate_delta_refs", []))
                    if "branch_event_ref" in action:
                        references.add(action["branch_event_ref"])
            if operation.get("kind") == "compensate":
                compensates = operation.get("target_request_ref")
                _identifier(compensates)
            for key in ("previous_ref", "next_ref", "event_ref", "condition_ref", "previous_branch_ref",
                        "context_ref", "next_realm_form_ref",
                        "next_branch_ref", "next_location_ref", "agent_ref", "history_ref"):
                if key in operation and operation[key] is not None:
                    _identifier(operation[key])
                    references.add(operation[key])
            for key in ("refs", "condition_refs", "reason_refs"):
                if key in operation:
                    _refs(operation[key], 0, 128)
                    references.update(operation[key])
        hashes = {}
        # Include nested references that admission actually resolves, not arbitrary
        # strings (which could become catalog identities only in a later extension).
        pending = list(references)
        while pending:
            reference = pending.pop()
            if reference in hashes:
                continue
            _identifier(reference)
            if reference not in self._records:
                raise JournalError("UNKNOWN_EVIDENCE")
            raw_record = self._records[reference]
            hashes[reference] = _digest(raw_record)
            record = json.loads(raw_record)
            document, nested = record["document"], []
            if record["kind"] == "agent":
                nested.extend(document["asp_resilience"]["asp_diagnostic_refs"])
                nested.extend(document.get("branch_event_refs", []))
                for key in ("pattern_vector_ref", "existence_potential_ref", "current_plane_pressure_ref"):
                    if key in document:
                        nested.append(document[key])
                if "last_valid_snapshot_ref" in document["asp_resilience"]:
                    nested.append(document["asp_resilience"]["last_valid_snapshot_ref"])
            elif record["kind"] == "branch_history":
                for row in document["entries"]:
                    nested.append(row["branch_event_ref"])
                    nested.extend(row.get("resulting_worldstate_delta_refs", []))
            elif record["kind"] == "consequence":
                nested.extend(document.get("external_result_refs", []))
            elif record["kind"] == "context":
                field = document["field"]
                if field in CONTEXT_COLLECTIONS:
                    nested.extend(document["value"])
                elif field in ("active_realm_form_ref", "perception_state_ref"):
                    nested.append(document["value"])
            pending.extend(nested)
        return {"request_ref": request_id, "principal": principal, "update_ref": update_ref,
                "update_sha256": _digest(raw), "record_sha256": hashes,
                "origin_packet": origin_packet, "compensates": compensates}

    def _authorize(self, principal, operation):
        name = operation.get("slot") if operation.get("kind") == "replace" else operation.get("kind")
        if name not in self._grants[principal]["operations"]:
            raise JournalError("UNAUTHORIZED_WRITER")

    def _replace(self, state, operation, context):
        _closed(operation, "kind slot previous_ref next_ref condition_refs")
        slot = operation["slot"]
        _reject(slot not in SLOTS)
        group, key = SLOTS[slot]
        spine = state["spine"]
        _reject(spine[group][key] != operation["previous_ref"] or operation["previous_ref"] == operation["next_ref"])
        before = self._record(state, operation["previous_ref"], slot)
        after = self._record(state, operation["next_ref"], slot, context["branch_ref"])
        _reject(before == after)
        self._domain.transition(slot, before, after, context, operation["condition_refs"])
        spine[group][key] = operation["next_ref"]
        return {"slot": slot, "before": operation["previous_ref"], "after": operation["next_ref"]}

    def _ability(self, state, operation, context):
        _closed(operation, "kind ability_id previous_ref next_ref condition_refs")
        refs = state["spine"]["ability_state_refs"]
        matches = [ref for ref in refs if state["records"][ref]["document"]["ability_id"] == operation["ability_id"]]
        _reject(len(matches) > 1 or (matches[0] if matches else None) != operation["previous_ref"])
        before = state["records"][matches[0]]["document"] if matches else None
        after = self._record(state, operation["next_ref"], "ability", context["branch_ref"])
        _reject(after["ability_id"] != operation["ability_id"] or operation["previous_ref"] == operation["next_ref"]
                or before == after)
        self._domain.transition("ability", before, after, context, operation["condition_refs"])
        if matches:
            refs[refs.index(matches[0])] = operation["next_ref"]
        else:
            refs.append(operation["next_ref"])

    def _append(self, state, operation, source):
        _closed(operation, "kind collection refs")
        _reject(type(operation["collection"]) is not str or "." not in operation["collection"])
        group, key = operation["collection"].split(".", 1)
        _reject(group not in COLLECTIONS or key not in COLLECTIONS[group])
        if source == "perception_engine":
            _reject(key != "perception_overlay_refs")
        if source == "realm_engine":
            _reject(key not in ("threshold_access_refs", "location_state_refs"))
        if source == "quest_engine":
            _reject(key not in ("quest_history_refs", "future_generation_bias_refs"))
        _refs(operation["refs"], 1, 128)
        target = state["spine"].setdefault(group, {}).setdefault(key, [])
        _reject(bool(set(target).intersection(operation["refs"])))
        for ref in operation["refs"]:
            document = self._record(state, ref, "reference", category=key)
            if key == "perception_overlay_refs":
                _reject(document["truth_scope"] != "player_perception")
        target.extend(operation["refs"])

    def _branch(self, state, operation, context, actions, update_ref):
        keys = "kind previous_branch_ref next_branch_ref next_location_ref agent_ref history_ref event_ref"
        if self._imported and "next_realm_form_ref" in operation:
            keys += " next_realm_form_ref"
        _closed(operation, keys)
        spine = state["spine"]
        _reject(operation["previous_branch_ref"] != context["branch_ref"]
                or operation["next_branch_ref"] == context["branch_ref"])
        self._record(state, operation["next_branch_ref"], "reference", operation["next_branch_ref"], "current_leaf_branch_ref")
        self._record(state, operation["event_ref"], "reference", operation["next_branch_ref"], "branch_event_ref")
        before = self._record(state, spine["state_refs"]["player_branch_history_ref"], "branch_history")
        after = self._record(state, operation["history_ref"], "branch_history", operation["next_branch_ref"])
        _reject(after["entries"][:len(before["entries"])] != before["entries"]
                or len(after["entries"]) != len(before["entries"]) + 1)
        last = after["entries"][-1]
        action = next((row for row in actions if row["action_trace_id"] == last["source_action_trace_ref"]), None)
        _reject(last.get("parent_branch_ref") != context["branch_ref"]
                or last["leaf_branch_ref"] != operation["next_branch_ref"]
                or last["branch_event_ref"] != operation["event_ref"]
                or action is None or action.get("branch_event_ref") != operation["event_ref"]
                or last.get("resulting_player_state_update_refs") != [update_ref]
                or last.get("resulting_worldstate_delta_refs", []) != action.get("resulting_worldstate_delta_refs", []))
        agent_before = self._record(state, spine["state_refs"]["player_agent_state_ref"], "agent")
        agent_after = self._record(state, operation["agent_ref"], "agent", operation["next_branch_ref"])
        self._domain.transition("agent", agent_before, agent_after,
            {**context, "branch_ref": operation["next_branch_ref"]}, [])
        spine["current_leaf_branch_ref"] = operation["next_branch_ref"]
        spine["current_location_ref"] = operation["next_location_ref"]
        spine["state_refs"]["player_agent_state_ref"] = operation["agent_ref"]
        spine["state_refs"]["player_branch_history_ref"] = operation["history_ref"]
        if "next_realm_form_ref" in operation:
            _reject("active_realm_form" not in spine.get("runtime_context", {}))
            spine["runtime_context"]["active_realm_form_ref"] = operation["next_realm_form_ref"]

    def _compensate(self, state, operation, context):
        _closed(operation, "kind target_request_ref reason_refs")
        _refs(operation["reason_refs"], 1, 128)
        _reject(not set(operation["reason_refs"]) <= set(context["evidence_refs"]))
        target = next((item for item in state["accepted_updates"]
                       if item["request_ref"] == operation["target_request_ref"]), None)
        _reject(target is None or not target["reversible"] or any(
            item["target_request_ref"] == operation["target_request_ref"] for item in state["compensations"]))
        for change in target["changes"]:
            group, key = SLOTS[change["slot"]]
            _reject(state["spine"][group][key] != change["after"])
            state["spine"][group][key] = change["before"]
        state["compensations"].append(_copy(operation))

    def _reduce(self, scope, state, packet):
        _closed(packet, "request_ref principal update_ref update_sha256 record_sha256 origin_packet compensates")
        _reject(scope != self._scope or packet != self._packet(packet["principal"], packet["request_ref"], packet["update_ref"]))
        update = json.loads(self._updates[packet["update_ref"]])
        spine = state["spine"]
        if self._imported:
            _reject(packet["request_ref"] in state["import_baseline"]["consumed_request_refs"]
                    or update["update_ref"] in state["import_baseline"]["consumed_update_refs"])
        _reject(update["branch_ref"] != spine["current_leaf_branch_ref"]
                or any(row["update_ref"] == update["update_ref"] for row in state["accepted_updates"]))
        for operation in update["operations"]:
            self._authorize(packet["principal"], operation)
        for reference in update["evidence_refs"]:
            evidence = self._record(state, reference, "reference", update["branch_ref"], "evidence_refs")
            _reject(evidence["truth_scope"] == "player_perception")
        context = self._context(state, evidence=update["evidence_refs"])
        compensating = packet["compensates"] is not None
        _reject(compensating and (len(update["operations"]) != 1 or update["operations"][0].get("kind") != "compensate"))
        origin_operations = [op for op in update["operations"] if op.get("kind") == "origin"]
        _reject(not compensating and len(origin_operations) != 1)
        actions, changes = [], []
        prior_phase = state["records"][self._origin_ref]["document"]["current_phase"]
        reversible = not compensating
        if not compensating:
            _closed(origin_operations[0], "kind evidence_ref")
            bundle = self._origin.evidence(origin_operations[0]["evidence_ref"])
            actions = bundle["actions"]
            _reject(update["source_system"] != "narrative_engine" and bundle["operation"] != "remember")
            _reject(not set(update["evidence_refs"]) <= {ref for action in actions for ref in action["source_refs"]})
            retained_actions = {row["action_trace_id"]: row
                for row in state["records"][self._origin_ref]["document"]["actions"]}
            for action in actions:
                _reject(action.get("branch_ref") != context["branch_ref"]
                        or action["action_trace_id"] not in retained_actions
                        and action.get("resulting_player_state_update_refs") != [update["update_ref"]])
                for reference in action.get("resulting_worldstate_delta_refs", []):
                    self._record(state, reference, "reference", context["branch_ref"], "worldstate_delta_refs")
                if "branch_event_ref" in action:
                    self._record(state, action["branch_event_ref"], "reference", category="branch_event_ref")
            next_origin = self._origin.reduce(state["records"][self._origin_ref]["document"], packet["origin_packet"])
            state["records"][self._origin_ref] = self._entry("origin", next_origin)
            for kind, collection, key, identity in (
                    ("action", "actions", "player_action_trace_refs", "action_trace_id"),
                    ("memory", "memories", "player_memory_record_refs", "memory_id")):
                for row in bundle[collection]:
                    entry = self._entry(kind, row)
                    imported_action = (self._imported and kind == "action"
                        and self._initial["records"].get(row[identity]) == entry)
                    _reject(row[identity] == self._origin_ref or row[identity] in self._records and not imported_action
                            or row[identity] in state["records"] and state["records"][row[identity]] != entry)
                    state["records"][row[identity]] = entry
                spine["memory_refs"][key] = [row[identity] for row in next_origin[collection]]
            reversible = bundle["operation"] == "remember"
        branch_operations = [op for op in update["operations"] if op.get("kind") == "branch"]
        _reject(len(branch_operations) > 1)
        if branch_operations:
            _reject(any(op.get("kind") == "replace" and op.get("slot") == "agent"
                        for op in update["operations"]))
            self._branch(state, branch_operations[0], context, actions, update["update_ref"])
        destination_context = self._context(state, evidence=update["evidence_refs"])
        seen = set()
        context_fields = set()
        for operation in update["operations"]:
            kind = operation.get("kind")
            identity = (kind, operation.get("slot", operation.get("ability_id", operation.get("collection", operation.get("event_ref")))))
            if kind == "context":
                identity = (kind, operation.get("context_ref"))
            _reject(identity in seen)
            seen.add(identity)
            if kind == "origin":
                continue
            if kind == "replace":
                changes.append(self._replace(state, operation, destination_context))
                reversible = reversible and operation["slot"] in self._profile["reversible_slots"]
            else:
                reversible = False
                if kind == "ability":
                    self._ability(state, operation, destination_context)
                elif kind == "append":
                    self._append(state, operation, update["source_system"])
                elif kind == "context":
                    field = self._change_context(state, operation, destination_context, update["source_system"], prior_phase, actions)
                    _reject(field in context_fields)
                    context_fields.add(field)
                elif kind == "branch":
                    pass
                elif kind in ("manifest", "dismiss"):
                    required = "kind event_ref" if kind == "manifest" else "kind event_ref condition_ref"
                    _closed(operation, required)
                    already_retained = operation["event_ref"] in state["records"]
                    retained_event_ids = {entry["document"]["manifestation_event_id"]
                        for entry in state["records"].values() if entry["kind"] == "manifestation"}
                    if self._imported:
                        retained_event_ids.update(state["import_baseline"]["consumed_manifestation_event_ids"])
                    document = self._record(state, operation["event_ref"], "manifestation",
                        destination_context["branch_ref"] if kind == "manifest" else None)
                    self._domain.validate("manifestation", document, destination_context)
                    active = spine["state_refs"].setdefault("wolf_manifestation_event_refs", [])
                    if kind == "manifest":
                        _reject(operation["event_ref"] in active or already_retained
                                or document["manifestation_event_id"] in retained_event_ids)
                        active.append(operation["event_ref"])
                    else:
                        _reject(operation["event_ref"] not in active or operation["condition_ref"] not in update["evidence_refs"])
                        active.remove(operation["event_ref"])
                elif kind == "compensate":
                    self._compensate(state, operation, context)
                else:
                    raise JournalError("POLICY_REJECTED")
        # This admission deliberately follows domain reduction to test late-failure atomicity.
        consequence = self._record(state, update["consequence_ref"], "consequence", context["branch_ref"])
        _closed(consequence, "consequence_id effect_id update_ref player_id branch_ref action_refs external_result_refs")
        _identifier(consequence["consequence_id"])
        _identifier(consequence["effect_id"])
        _refs(consequence["action_refs"], 0, 16)
        _refs(consequence["external_result_refs"], 0, 128)
        _reject(consequence["update_ref"] != update["update_ref"]
                or consequence["player_id"] != self._scope.subject_id
                or consequence["branch_ref"] != context["branch_ref"]
                or set(consequence["action_refs"]) != {action["action_trace_id"] for action in actions})
        effect = [consequence["consequence_id"], consequence["effect_id"], self._scope.subject_id]
        _reject(any(row["effect"] == effect for row in state["accepted_updates"]))
        if self._imported:
            _reject(any(row["effect"] == effect for row in state["import_baseline"]["consumed_effects"]))
        results = {ref for action in actions for ref in action.get("resulting_worldstate_delta_refs", [])}
        _reject(set(consequence["external_result_refs"]) != results)
        state["accepted_updates"].append({"request_ref": packet["request_ref"], "update_ref": update["update_ref"],
            "consequence_ref": update["consequence_ref"], "effect": effect,
            "reversible": bool(reversible and changes), "changes": changes})
        spine["update_control"].setdefault("accepted_update_packet_refs", []).append(update["update_ref"])
        spine["state_lifecycle"] = "continuing"
        spine["identity"].pop("celestial_identity_initial_state", None)
        if self._imported:
            runtime = spine.get("runtime_context", {})
            phase = state["records"][self._origin_ref]["document"]["current_phase"]
            _reject(prior_phase != phase and "phase_confidence" in runtime
                    and "phase_confidence" not in context_fields)
            if "sequence_id" in runtime:
                runtime["sequence_id"] += 1
            if "last_player_action_trace_ref" in runtime and actions:
                runtime["last_player_action_trace_ref"] = actions[-1]["action_trace_id"]
        self._validate_state(state, evidence=update["evidence_refs"])
        return state

    def publish(self, writer, request_id, expected_revision, update_ref):
        principal = next((name for name, handle in self._writers.items() if writer is handle), None)
        if principal is None:
            raise JournalError("UNAUTHORIZED_WRITER")
        packet = self._packet(principal, request_id, update_ref)
        return self._journal.commit(request_id, expected_revision, packet, compensates=packet["compensates"])

    def state(self):
        return self._journal.state()

    def checkpoint(self):
        return self._journal.checkpoint()

    @classmethod
    def load(cls, raw, trusted_head, *configuration):
        owner = cls(*configuration)
        return cls._load_journal(owner, raw, trusted_head)

    @classmethod
    def load_migrated(cls, raw, trusted_head, result, migration, raw_source, *configuration):
        owner = cls.from_migration(result, migration, raw_source, *configuration)
        return cls._load_journal(owner, raw, trusted_head)

    @staticmethod
    def _load_journal(owner, raw, trusted_head):
        journal = CommitJournal.load(raw, owner._scope, owner._policy_id, owner._reduce, trusted_head)
        archive = json.loads(journal.save())
        if archive["initial_state"] != owner._initial or any(
                entry["request_id"] != entry["packet"]["request_ref"]
                or entry["compensates"] != entry["packet"]["compensates"] for entry in archive["entries"]):
            raise JournalError("INVALID_ARCHIVE")
        owner._journal = journal
        return owner
