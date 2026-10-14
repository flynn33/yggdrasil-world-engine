"""Bounded world/location owner with a WRW player-source adapter (YWE-REQ-0060).

The concrete player/plane wire binding is WRW reference-profile compatibility
under YWE-REQ-0015; named player planes do not become mandatory Core ontology.
"""

import hashlib
import json
from urllib.parse import urljoin

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource, Unresolvable

from . import core_values as cv
from .realm_engine.realm import RealmEngine
from .state_journal import JournalError, TruthScope, _encode, _identifier, _object_bytes

FORMAT = "ywe.world_location_partition.v1"
SCHEMAS = {"source": "m4_world_location_source", "state": "m4_world_location_state",
    "profile": "m4_world_location_profile", "update": "m4_world_location_update",
    "phase11": "worldstate_location_mutation", "m3": "m3_core_domain",
    "overlay": "location_branch_overlay", "action": "player_action_trace",
    "plane": "m4_plane_attunement_state", "generation_state": "m3_generation_state",
    "realm_transition": "m3_generation_realm_transition", "normalization": "m3_generation_state_normalization",
    "normalization_plan": "m3_generation_normalization_plan", "module_capture": "m3_generation_module_capture",
    "topology": "m3_generation_topology_axiom", "planner": "m3_planner_emitter",
    "diagnostic_bundle": "m3_reference_diagnostic_bundle"}
BASE = "https://ywe.local/schemas/"
SCHEMA_IDS = {key: BASE + name + "_schema.json" for key, name in SCHEMAS.items()}
SCHEMA_IDS["overlay"] = BASE + "ywe.location_branch_overlay.v1.json"
HEAD_KEYS = frozenset("component_id scope owner_policy_id revision head_digest state_sha256".split())


def _copy(value):
    return json.loads(_object_bytes(value))


def _digest(value):
    return hashlib.sha256(_object_bytes(value)).hexdigest()


def _reject(condition, code="POLICY_REJECTED"):
    if condition:
        raise JournalError(code)


def _closed(value, keys):
    _reject(type(value) is not dict or set(value) != set(keys.split()), "INVALID_VALUE")


def _unique(rows, key):
    values = [row[key] for row in rows]
    _reject(len(values) != len(set(values)))


def _schema_copy(value):
    _reject(type(value) is not dict, "INVALID_POLICY")
    stack, count = [(value, 0, frozenset())], 0
    while stack:
        item, depth, parents = stack.pop()
        count += 1
        _reject(count > 32768 or depth > 64, "INVALID_POLICY")
        if type(item) in (dict, list):
            _reject(id(item) in parents, "INVALID_POLICY")
            parents = parents | {id(item)}
            if type(item) is dict:
                _reject(any(type(k) is not str for k in item), "INVALID_POLICY")
                _reject(depth != 0 and "$id" in item, "INVALID_POLICY")
                stack.extend((x, depth + 1, parents) for pair in item.items() for x in pair)
            else:
                stack.extend((x, depth + 1, parents) for x in item)
        elif type(item) is int:
            _reject(item.bit_length() > 256, "INVALID_POLICY")
        elif item is not None and type(item) not in (str, bool):
            raise JournalError("INVALID_POLICY")
    raw = _encode(value)
    _reject(len(raw) > 1048576, "INVALID_POLICY")
    return json.loads(raw), raw


def _unavailable(uri):
    raise NoSuchResource(ref=uri)


class WorldLocationPolicy:
    """Pure owner; callers supply coordinator-verified states and read bodies."""

    def __init__(self, scope, profile, initial_state, grants, records, updates, schemas, realm_binding):
        try:
            _reject(type(scope) is not TruthScope or scope.truth_scope not in
                    ("shared_worldstate", "leaf_branch_state"), "INVALID_POLICY")
            self._scope = scope
            self._profile, self._grants = _copy(profile), _copy(grants)
            self._schemas, resources, schema_hashes, total = {}, [], {}, 0
            _closed(schemas, " ".join(SCHEMAS))
            for key, name in SCHEMAS.items():
                schema, raw = _schema_copy(schemas[key])
                _reject(schema.get("$id") != SCHEMA_IDS[key], "INVALID_POLICY")
                Draft202012Validator.check_schema(schema)
                self._schemas[key] = schema
                resources.append((schema["$id"], Resource.from_contents(schema)))
                schema_hashes[key] = hashlib.sha256(raw).hexdigest()
                total += len(raw)
            _reject(total > 1048576, "INVALID_POLICY")
            self._registry = Registry(retrieve=_unavailable).with_resources(resources)
            for schema in self._schemas.values():
                self._schema_refs(schema)
            self._validate("profile", self._profile)
            _reject(type(realm_binding) is not cv.CoreBinding, "INVALID_POLICY")
            cv.revalidate_value(realm_binding)
            self._binding = realm_binding
            self._engine = RealmEngine(realm_binding)
            self._realm_ids = {r.realm_id for r in realm_binding.profile_realms}
            self._records = self._catalog(records, "ref", "source")
            self._updates = self._catalog(updates, "update_ref", "update")
            self._facts = {x["slot_id"]: x for x in self._profile["fact_definitions"]}
            self._locations = {x["location_id"]: x for x in self._profile["location_definitions"]}
            self._rules = {x["rule_id"]: x for x in self._profile["mutable_rules"]}
            self._planes = {x["realm_id"]: x["plane_id"] for x in self._profile["realm_plane_bindings"]}
            self._profile_check()
            _reject(not 1 <= len(self._grants) <= 32, "INVALID_POLICY")
            for principal, grant in self._grants.items():
                _identifier(principal)
                _closed(grant, "roles")
                roles = grant["roles"]
                _reject(type(roles) is not list or not roles or len(roles) > 2
                        or any(type(x) is not str for x in roles)
                        or roles != sorted(set(roles)) or not set(roles) <= {"narrative", "realm"})
            for item in self._records.values():
                self._record_check(item)
                for ref in self._links(item):
                    self.record(ref)
            self._initial = _copy(initial_state)
            self._state(self._initial, initial=True)
            for update in self._updates.values():
                _reject(update["scope"] != scope.to_record() or update["component_id"] != self.component_id)
                self._closure(update)
            identity = {"algorithm": FORMAT, "scope": scope.to_record(), "profile": _digest(self._profile),
                "initial": _digest(self._initial), "grants": _digest(self._grants), "schemas": schema_hashes,
                "binding": hashlib.sha256(cv.canonical_bytes(realm_binding)).hexdigest(),
                "anchors": {r: _digest(self.record(r)) for r in (profile["law_ref"], profile["geography_ref"])}}
            self._policy_id = "world-location:" + _digest(identity)
        except JournalError as exc:
            raise JournalError("INVALID_POLICY") from exc
        except (KeyError, TypeError, ValueError, RecursionError, Unresolvable, SchemaError) as exc:
            raise JournalError("INVALID_POLICY") from exc

    @property
    def scope(self):
        return self._scope

    @property
    def component_id(self):
        return self._profile["component_id"]

    @property
    def policy_id(self):
        return self._policy_id

    def initial_state(self):
        return _copy(self._initial)

    def record(self, ref):
        _identifier(ref)
        if ref not in self._records:
            raise JournalError("UNKNOWN_EVIDENCE")
        return _copy(self._records[ref])

    def update(self, update_ref):
        _identifier(update_ref)
        if update_ref not in self._updates:
            raise JournalError("UNKNOWN_EVIDENCE")
        return _copy(self._updates[update_ref])

    def definition(self, definition_ref):
        _identifier(definition_ref)
        for value in self._facts.values():
            if value["definition_ref"] == definition_ref:
                return _copy(value)
        raise JournalError("UNKNOWN_EVIDENCE")

    def realm(self, realm_id):
        _identifier(realm_id)
        if realm_id in self._planes:
            for definition in self._binding.profile_realms:
                if definition.realm_id == realm_id:
                    return _copy({"definition": definition.to_record(), "plane_id": self._planes[realm_id]})
        raise JournalError("UNKNOWN_EVIDENCE")

    def requirements(self, packet):
        packet = _copy(packet)
        self._validate("update", packet, "Packet")
        _reject(packet != self.packet(packet["principals"], packet["request_ref"], packet["update_ref"]))
        heads = {}
        for ref in packet["selected_record_sha256"]:
            row = self.record(ref)
            doc = row["document"]
            selected = ([doc["player_head"], doc["branch_head"]] if row["kind"] == "resolution" else
                        [doc["head"]] if row["kind"] == "condition" and "head" in doc else [])
            for head in selected:
                cid = head["component_id"]
                _reject(cid == self.component_id or cid in heads and heads[cid] != head)
                heads[cid] = head
        update = self._updates[packet["update_ref"]]
        for op in update["resolutions"]:
            if op["kind"] == "realm_shift":
                head = heads.get(op["player_component_id"])
                _reject(head is None or head["state_sha256"] != op["player_state_sha256"]
                        or head["scope"] != TruthScope(self.scope.world_id, "player_state", op["player_id"]).to_record())
        reads = [heads[key] for key in sorted(heads)]
        _reject(hashlib.sha256(_encode(reads)).hexdigest() != packet["read_vector_sha256"])
        return _copy({"reads": reads})

    def _schema_refs(self, schema):
        pending, checked = [(schema, schema["$id"], frozenset())], set()
        while pending:
            node, base, active = pending.pop()
            if type(node) not in (dict, list):
                continue
            marker = (base, id(node))
            _reject(marker in active, "INVALID_POLICY")
            if marker in checked:
                continue
            checked.add(marker)
            active = active | {marker}
            if type(node) is dict:
                _reject("$dynamicRef" in node or "$dynamicAnchor" in node, "INVALID_POLICY")
                if "$ref" in node:
                    uri = node["$ref"]
                    _reject(type(uri) is not str, "INVALID_POLICY")
                    resolved = self._registry.resolver(base).lookup(uri)
                    target_base = urljoin(base, uri).split("#")[0]
                    pending.append((resolved.contents, target_base, active))
                pending.extend((x, base, active) for x in node.values())
            else:
                pending.extend((x, base, active) for x in node)

    def _validate(self, key, value, definition=None):
        schema = self._schemas[key]
        if definition:
            schema = {"$ref": schema["$id"] + "#/$defs/" + definition}
        try:
            Draft202012Validator(schema, registry=self._registry).validate(value)
        except (ValidationError, Unresolvable, RecursionError):
            raise JournalError("INVALID_VALUE") from None

    def _catalog(self, rows, key, schema):
        _reject(type(rows) is not list or len(rows) > 128)
        result, size = {}, 0
        for row in rows:
            item = _copy(row)
            self._validate(schema, item)
            _identifier(item[key])
            _reject(item[key] in result)
            size += len(_object_bytes(item))
            _reject(size > 1048576)
            result[item[key]] = item
        return result

    def _doc(self, ref, kind=None):
        item = self.record(ref)
        _reject(kind is not None and item["kind"] != kind)
        return item["document"]

    def _scope_ok(self, scope, branch=None, player=None):
        parsed = TruthScope(**scope)
        _reject(parsed.world_id != self.scope.world_id or parsed.truth_scope == "player_perception")
        if parsed.truth_scope == "leaf_branch_state":
            _reject(branch is not None and parsed.subject_id != branch)
        elif parsed.truth_scope == "player_state":
            _reject(player is not None and parsed.subject_id != player)

    def _record_check(self, record):
        _reject(record["sha256"] != _digest(record["document"]))
        self._scope_ok(record["scope"])
        doc, kind = record["document"], record["kind"]
        self._doc(record["provenance"]["diagnostic_ref"], "diagnostic")
        pending = [doc]
        while pending:
            node = pending.pop()
            if type(node) is dict:
                for key, value in node.items():
                    if (key.endswith(("_id", "_ref")) and value is not None
                            and not (kind == "delta" and node is doc and key == "sequence_id")):
                        _identifier(value)
                    elif key.endswith("_refs") and type(value) is list:
                        _reject(len(value) > 65 or any(type(x) is not str for x in value)
                                or len(set(value)) != len(value))
                        for ref in value:
                            _identifier(ref)
                    pending.append(value)
            elif type(node) is list:
                pending.extend(node)
        if kind in ("law", "geography"):
            _reject(record["scope"]["truth_scope"] != "shared_worldstate")
        if kind == "action":
            _reject(doc["schema_version"] != "0.1.0")
        if kind == "overlay":
            _reject(set(doc) - set(self._schemas["overlay"]["properties"]) or doc["version"] != "1.0.0")
        if kind == "diagnostic":
            _reject(doc["diagnostic_ref"] != record["ref"])
        if kind == "source_evidence":
            _reject(doc["source_id"] != record["ref"])
            self._typed(doc["value"])
        if kind == "resolved_location":
            self._resolved(record["ref"])
        if kind == "condition" and doc["kind"] == "location":
            _reject((doc["field"] == "access_state") != (doc["access_id"] is not None))

    def _typed(self, value):
        self._validate("state", value, "TypedValue")
        if value["kind"] == "references":
            _reject(value["refs"] != sorted(set(value["refs"])))

    def _fact_value(self, definition, value):
        self._typed(value)
        kind = value["kind"]
        _reject(kind != definition["value_kind"])
        if kind == "integer":
            _reject(not definition["minimum"] <= value["value"] <= definition["maximum"])
        elif kind in ("token", "reference", "references"):
            actual = value["refs"] if kind == "references" else [value["token"] if kind == "token" else value["ref"]]
            _reject(not set(actual) <= set(definition["allowed_values"]))

    def _profile_check(self):
        p = self._profile
        for rows, key in [(p["fact_definitions"], "slot_id"), (p["fact_definitions"], "definition_ref"),
                          (p["fact_definitions"], "projection_fact_id"), (p["location_definitions"], "location_id"),
                          (p["mutable_rules"], "rule_id"), (p["realm_plane_bindings"], "realm_id")]:
            _unique(rows, key)
        _reject(not set(self._planes) <= self._realm_ids)
        law = self._doc(p["law_ref"], "law")
        geography = self._doc(p["geography_ref"], "geography")
        _reject(law["profile_id"] != p["profile_id"] or law["core_binding_sha256"] !=
                hashlib.sha256(cv.canonical_bytes(self._binding)).hexdigest()
                or law["location_rule_refs"] != sorted(self._rules)
                or geography["world_id"] != self.scope.world_id)
        expected = sorted([{"location_id": d["location_id"], "base_location_ref": d["base_location_ref"],
                            "realm_ids": d["realm_ids"]} for d in self._locations.values()], key=lambda x: x["location_id"])
        _reject(geography["locations"] != expected)
        for d in self._facts.values():
            kind = d["value_kind"]
            _reject(d["realm_id"] is not None and d["realm_id"] not in self._realm_ids
                    or d["location_id"] is not None and d["location_id"] not in self._locations)
            if kind == "integer":
                _reject(type(d["minimum"]) is not int or type(d["maximum"]) is not int
                        or d["minimum"] > d["maximum"] or d["allowed_values"])
            else:
                _reject(d["minimum"] is not None or d["maximum"] is not None
                        or bool(d["allowed_values"]) != (kind != "boolean"))
            _reject(d["allowed_values"] != sorted(set(d["allowed_values"])))
        for d in self._locations.values():
            _reject(d["geography_sha256"] != self.record(p["geography_ref"])["sha256"]
                    or not set(d["realm_ids"]) <= self._realm_ids)
            _unique(d["access_definitions"], "access_id")
            _unique(d["thin_veil_slots"], "target_realm_id")
            for veil in d["thin_veil_slots"]:
                fact = self._facts.get(veil["slot_id"])
                _reject(not fact or fact["location_id"] != d["location_id"]
                        or fact["value_kind"] != "token" or fact["allowed_values"] != ["FALSE", "TRUE", "UNAVAILABLE"]
                        or veil["target_realm_id"] not in self._realm_ids)
        for rule in self._rules.values():
            self._current(rule["location_id"], rule["source_current"])
            self._current(rule["location_id"], rule["target_current"])
            _reject(rule["source_current"] == rule["target_current"])
            for ref in rule["condition_refs"]:
                self._doc(ref, "condition")

    def _current(self, location, current):
        self._validate("state", current, "LocationCurrent")
        definition = self._locations.get(location)
        _reject(definition is None)
        _reject({k: current[k] for k in ("status", "phase", "stability")} not in definition["allowed_current_states"])
        _unique(current["access"], "access_id")
        _reject({x["access_id"] for x in current["access"]} != {x["access_id"] for x in definition["access_definitions"]}
                or not set(current["active_plane_pressures"]) <= set(self._planes.values()))
        for key in ("active_plane_pressures", "eligible_systems", "residue_refs", "future_generation_bias_refs"):
            _reject(current[key] != sorted(set(current[key])))
        for key, kind in [("residue_refs", "residue"), ("future_generation_bias_refs", "generation_bias")]:
            for ref in current[key]:
                _reject(self._doc(ref, "source_evidence")["source_kind"] != kind)
        for access in current["access"]:
            for ref in access["condition_refs"]:
                self._doc(ref, "condition")

    def _resolved(self, ref):
        doc = self._doc(ref, "resolved_location")
        definition = self._locations.get(doc["location_id"])
        _reject(not definition or doc["base_location_ref"] != definition["base_location_ref"]
                or doc["realm_id"] not in definition["realm_ids"])
        self._current(doc["location_id"], doc["current"])
        return doc

    def _state(self, state, initial=False):
        self._validate("state", state)
        _reject(state["scope"] != self.scope.to_record() or state["component_id"] != self.component_id
                or state["profile_id"] != self._profile["profile_id"]
                or state["law_sha256"] != self.record(self._profile["law_ref"])["sha256"]
                or state["geography_sha256"] != self.record(self._profile["geography_ref"])["sha256"])
        _unique(state["facts"], "slot_id")
        _reject({r["slot_id"] for r in state["facts"]} != set(self._facts))
        event_refs = {e["event_ref"] for e in state["events"]}
        for row in state["facts"]:
            d = self._facts[row["slot_id"]]
            _reject(row["definition_ref"] != d["definition_ref"])
            self._fact_value(d, row["value"])
            self._genesis_or_event(row["source_event_ref"], event_refs)
            if row["source_event_ref"] not in event_refs:
                self._seed(state, row["source_event_ref"], d["subject_ref"], row["value"])
        pairs = [(r["location_id"], r["realm_id"]) for r in state["locations"]]
        _reject(len(pairs) != len(set(pairs)))
        for row in state["locations"]:
            doc = self._resolved(row["current_record_ref"])
            _reject((doc["location_id"], doc["realm_id"]) != (row["location_id"], row["realm_id"])
                    or row["current_record_sha256"] != self.record(row["current_record_ref"])["sha256"]
                    or state["records"].get(row["current_record_ref"]) != self.record(row["current_record_ref"]))
            for ref in row["history_event_refs"]:
                self._genesis_or_event(ref, event_refs)
            if initial:
                seed = {key: doc[key] for key in ("location_id", "base_location_ref", "realm_id", "current")}
                _reject(doc["source_delta_ref"] != doc["source_mutation_ref"])
                self._seed(state, doc["source_delta_ref"], doc["location_id"], {"kind": "token", "token": _digest(seed)})
        _unique(state["occupancies"], "player_id")
        for row in state["occupancies"]:
            _reject((row["location_id"], row["realm_id"]) not in pairs
                    or self.scope.truth_scope == "leaf_branch_state" and row["branch_ref"] != self.scope.subject_id)
            self._genesis_or_event(row["source_event_ref"], event_refs)
            if row["source_event_ref"] not in event_refs:
                seed = {key: row[key] for key in ("player_id", "branch_ref", "location_id", "realm_id")}
                self._seed(state, row["source_event_ref"], row["player_id"], {"kind": "token", "token": _digest(seed)})
        for ref, record in state["records"].items():
            _reject(record != self.record(ref))
        _unique(state["events"], "event_ref")
        _unique(state["events"], "effect_id")
        expected_effects = []
        for event in state["events"]:
            update = self._updates.get(event["update_ref"])
            _reject(not update or event["effect_id"] != update["effect_id"] or event["delta_ref"] != update["delta_ref"])
            expected_effects.append({"effect_id": event["effect_id"], "delta_ref": event["delta_ref"],
                                     "delta_sha256": self.record(event["delta_ref"])["sha256"]})
        _reject(state["consumed_effects"] != expected_effects)
        _unique(state["consumed_effects"], "delta_ref")
        geography = self._doc(self._profile["geography_ref"], "geography")
        for fixed in geography["fixed_facts"]:
            definition = self._facts.get(fixed["fact_id"])
            _reject(not definition or definition["mutable"] or definition["subject_ref"] != fixed["subject_ref"]
                    or next(x["value"] for x in state["facts"] if x["slot_id"] == fixed["fact_id"]) != fixed["value"])
        if initial:
            _reject(state["events"] or state["consumed_effects"])
            pending, seen = list(state["records"]), set()
            while pending:
                ref = pending.pop()
                if ref not in seen:
                    record = self.record(ref)
                    _reject(state["records"].get(ref) != record)
                    seen.add(ref)
                    pending += self._links(record)
        _object_bytes(state)

    def _seed(self, state, ref, subject, value):
        record = self.record(ref)
        source = record["document"]
        _reject(record["kind"] != "source_evidence" or source["source_kind"] != "genesis"
                or source["subject_ref"] != subject or source["value"] != value
                or record["scope"] not in (self.scope.to_record(), TruthScope(self.scope.world_id, "shared_worldstate", self.scope.world_id).to_record())
                or state["records"].get(ref) != record)

    def _genesis_or_event(self, ref, events):
        if ref not in events:
            _reject(self._doc(ref, "source_evidence")["source_kind"] != "genesis")

    @staticmethod
    def _provenance_refs(p):
        return [p["cosmic_pattern_snapshot_ref"], p["diagnostic_ref"], p["generation_plan_ref"], *p["source_ash_refs"]]

    def _links(self, item):
        doc, kind = item["document"], item["kind"]
        refs = self._provenance_refs(item["provenance"])
        if "provenance" in doc:
            refs += self._provenance_refs(doc["provenance"])
        if kind in ("law", "geography"):
            refs += doc["source_evidence_refs"]
        elif kind == "source_evidence":
            refs += doc["source_refs"]
        elif kind == "diagnostic":
            refs += doc["evidence_refs"]
        elif kind == "condition" and doc["kind"] == "declared_source":
            refs.append(doc["source_ref"])
        elif kind == "resolution":
            refs += [doc["delta_ref"], *doc["action_refs"], *doc["location_mutation_refs"], *doc["condition_refs"]]
        elif kind == "delta":
            refs += [doc["source_resolution_payload"], *doc["location_mutation_refs"], *doc["future_generation_bias_update_refs"]]
            refs += self._provenance_refs(doc["ash_provenance"])
            refs += doc["ash_provenance"]["axiom_diagnostic_refs"] + doc["ash_provenance"]["pattern_vector_refs"]
            refs.append(doc["ash_provenance"]["existence_potential_ref"])
            for op in doc["mutations"]:
                refs += op["evidence_refs"]
        elif kind == "location_mutation":
            refs += [doc["source_worldstate_delta_ref"], doc["diagnostic_ref"], doc["generation_plan_ref"], *doc["source_ash_refs"]]
        elif kind == "action":
            refs += doc["source_refs"]
        elif kind == "resolved_location":
            refs += [doc["source_delta_ref"], doc["source_mutation_ref"], *doc["current"]["residue_refs"], *doc["current"]["future_generation_bias_refs"]]
            for access in doc["current"]["access"]:
                refs += access["condition_refs"]
        elif kind == "overlay":
            refs += doc["source_refs"].get("worldstate_delta_refs", [])
            if "location_state_record_ref" in doc["source_refs"]:
                refs.append(doc["source_refs"]["location_state_record_ref"])
            refs += doc.get("future_generation_bias_refs", [])
            refs += doc["overlay_body"].get("myth_pressure_refs", []) + doc["overlay_body"].get("prophecy_pressure_refs", [])
        return refs

    def _closure(self, update):
        pending = [self._profile["law_ref"], self._profile["geography_ref"], update["delta_ref"]]
        pending += self._provenance_refs(update["provenance"])
        for op in update["resolutions"]:
            pending += op["condition_refs"]
            for key in ("before_record_ref", "after_record_ref", "mutation_ref", "overlay_ref"):
                if key in op:
                    pending.append(op[key])
            if "rule_id" in op:
                _reject(op["rule_id"] not in self._rules)
                pending += self._rules[op["rule_id"]]["condition_refs"]
        pending += update["retention"].get("resolution_condition_refs", [])
        selected = {}
        while pending:
            ref = pending.pop()
            _identifier(ref)
            if ref in selected:
                continue
            item = self.record(ref)
            selected[ref] = _digest(item)
            _reject(len(selected) > 128)
            pending += self._links(item)
        return dict(sorted(selected.items()))

    def _authorize(self, principals, update):
        self._validate("update", principals, "Principals")
        for role, key in (("narrative", "narrative_principal"), ("realm", "realm_principal")):
            needed = role == "narrative" or any(r["kind"] != "fact" for r in update["resolutions"])
            principal = principals[key]
            _reject(needed and (principal is None or role not in self._grants.get(principal, {}).get("roles", [])),
                    "UNAUTHORIZED_WRITER")
            _reject(not needed and principal is not None, "UNAUTHORIZED_WRITER")

    def packet(self, principals, request_id, update_ref):
        _identifier(request_id)
        _identifier(update_ref)
        principals = _copy(principals)
        update = self._updates.get(update_ref)
        if update is None:
            raise JournalError("UNKNOWN_EVIDENCE")
        self._authorize(principals, update)
        return _copy({"request_ref": request_id, "principals": principals, "update_ref": update_ref,
            "update_sha256": _digest(update), "selected_record_sha256": self._closure(update),
            "read_vector_sha256": update["source_read_vector_sha256"]})

    def _view(self, view):
        _closed(view, "format world_id components")
        _reject(view["format"] != "ywe.owner_read_view.v1" or view["world_id"] != self.scope.world_id
                or type(view["components"]) is not list or len(view["components"]) > 16)
        result, heads = {}, []
        for original in view["components"]:
            # The owner state keeps its own bound; head metadata adds no privilege.
            _closed(original, "component_id scope owner_policy_id revision head_digest state_sha256 state")
            body = _copy(original["state"])
            head = _copy({k: original[k] for k in HEAD_KEYS})
            self._validate("source", head, "ComponentHead")
            self._scope_ok(head["scope"])
            _reject(head["component_id"] in result or head["state_sha256"] != _digest(body))
            result[head["component_id"]] = {**head, "state": body}
            heads.append(head)
        _reject(list(result) != sorted(result))
        return result, hashlib.sha256(_encode(heads)).hexdigest()

    def _read(self, head, view):
        row = view.get(head["component_id"])
        _reject(row is None or {k: row[k] for k in HEAD_KEYS} != head)
        return row["state"]

    def _plane(self, row, player_id):
        state = row["state"]
        _reject(row["scope"] != TruthScope(self.scope.world_id, "player_state", player_id).to_record()
                or state["world_id"] != self.scope.world_id or state["player_id"] != player_id)
        spine = state["spine"]
        ref = spine["state_refs"]["plane_attunement_state_ref"]
        record = state["records"][ref]
        _reject(record["kind"] != "plane" or record["sha256"] != _digest(record["document"]))
        self._validate("plane", record["document"])
        _reject(record["document"]["schema_version"] != "2.0.0")
        return spine, ref, record["document"]

    def _condition(self, ref, view):
        doc = self._doc(ref, "condition")
        kind = doc["kind"]
        if kind == "declared_source":
            record = self.record(doc["source_ref"])
            source = record["document"]
            _reject(record["kind"] != "source_evidence" or source["source_kind"] != "declared_condition"
                    or record["sha256"] != doc["source_sha256"] or source["subject_ref"] != doc["subject_ref"]
                    or source["value"] != doc["expected_value"])
            return
        state = self._read(doc["head"], view)
        if kind == "current_fact":
            self._validate("state", state)
            _reject(state["scope"] != doc["head"]["scope"] or state["component_id"] != doc["head"]["component_id"])
            row = next((x for x in state["facts"] if x["slot_id"] == doc["slot_id"]), None)
            _reject(row is None or row["value"] != doc["expected_value"])
        elif kind == "location":
            row = next((x for x in state["locations"] if (x["location_id"], x["realm_id"]) ==
                        (doc["location_id"], doc["realm_id"])), None)
            _reject(row is None)
            item = state["records"][row["current_record_ref"]]
            _reject(item["sha256"] != _digest(item["document"]))
            current = item["document"]["current"]
            value = current[doc["field"]] if doc["field"] != "access_state" else next(
                (x["state"] for x in current["access"] if x["access_id"] == doc["access_id"]), None)
            _reject(value != doc["expected_value"])
        elif kind == "player_plane":
            _, _, plane = self._plane(view[doc["head"]["component_id"]], doc["player_id"])
            _reject(doc["plane_id"] not in plane["planes"]
                    or plane["planes"][doc["plane_id"]]["score_q6"] < doc["minimum_q6"])
        else:
            _reject({k: doc[k] for k in ("effect_id", "delta_ref", "delta_sha256")} not in state["consumed_effects"])

    def _evidence(self, update, view):
        delta = self._doc(update["delta_ref"], "delta")
        _reject(delta["delta_id"] != update["delta_ref"] or delta.get("diagnostic_noop_ref") is not None
                or self.record(update["delta_ref"])["scope"] != self.scope.to_record())
        source = self._doc(delta["source_resolution_payload"], "resolution")
        player = self._read(source["player_head"], view)
        branch = self._read(source["branch_head"], view)
        pid, bid = player["player_id"], player["spine"]["current_leaf_branch_ref"]
        _reject(source["world_id"] != self.scope.world_id or source["delta_ref"] != update["delta_ref"]
                or source["player_head"]["scope"] != TruthScope(self.scope.world_id, "player_state", pid).to_record()
                or source["branch_head"]["scope"] != TruthScope(self.scope.world_id, "leaf_branch_state", bid).to_record()
                or delta["current_leaf_branch_ref"] != bid or delta["player_runtime_state_ref"] != source["player_head"]["component_id"]
                or self.scope.truth_scope == "leaf_branch_state" and self.scope.subject_id != bid
                or source["location_mutation_refs"] != delta["location_mutation_refs"])
        _closed(branch, "format world_id branch_id owner_player_id branch events")
        _reject(branch["format"] != "ywe.branch_owner.v1" or branch["world_id"] != self.scope.world_id
                or branch["branch_id"] != bid or branch["owner_player_id"] != pid or type(branch["events"]) is not dict)
        if delta["source_branch_event_ref"] is not None:
            event = branch["events"].get(delta["source_branch_event_ref"])
            _reject(event is None or event["branch_event_id"] != delta["source_branch_event_ref"]
                    or event["schema_id"] != "ywe.branch_event.v2" or event["schema_version"] != "2.0.0"
                    or event["world_id"] != self.scope.world_id or event["owner_player_id"] != pid
                    or event["target_branch_id"] != bid or update["delta_ref"] not in event["worldstate_delta_refs"])
        meaningful = False
        covered_targets = set()
        for ref in source["action_refs"]:
            record = self.record(ref)
            action = self._doc(ref, "action")
            self._scope_ok(record["scope"], bid, pid)
            _reject(action["player_id"] != pid or action.get("branch_ref") != bid
                    or not action["source_refs"] or update["delta_ref"] not in action.get("resulting_worldstate_delta_refs", [])
                    or action.get("location_ref") not in delta["affected_location_refs"])
            meaningful |= action["significance"] != "minor_record"
            covered_targets.update(action.get("affected_entity_refs", []))
        _reject(not meaningful)
        _reject(not {x["target_ref"] for x in delta["mutations"]} <= covered_targets
                or set(delta["consequence_domains"]) != {x["domain"] for x in delta["mutations"]})
        _unique(delta["mutations"], "operation_id")
        for ref in source["condition_refs"]:
            self._condition(ref, view)
        for p in (update["provenance"], delta["ash_provenance"], source["provenance"]):
            diagnostic = self._doc(p["diagnostic_ref"], "diagnostic")
            _reject(diagnostic["status"] != "COMPLETED" or diagnostic["failure_code"] is not None
                    or diagnostic["owner"] not in ("NARRATIVE", "REALM")
                    or diagnostic["rule"] not in ("PROVENANCE", "REALM_ACCESS", "STAGE_GATE"))
        persistence = delta["persistence"]
        _reject(not set(delta["affected_location_refs"]) <= set(self._locations))
        expected = "shared_world" if self.scope.truth_scope == "shared_worldstate" else "leaf_branch"
        visibility = "shared_world" if expected == "shared_world" else "branch_local"
        _reject(persistence["scope"] not in (expected, "realm_local")
                or persistence["visibility"] != ("realm_local" if persistence["scope"] == "realm_local" else visibility)
                or persistence["retention_policy"] != update["retention"]["kind"])
        if persistence["scope"] == "realm_local":
            _reject(any(r["kind"] == "fact" and self._facts[r["slot_id"]]["realm_id"] is None for r in update["resolutions"]))
        _reject(len(delta["mutations"]) != len(update["resolutions"]))
        return delta, source, player

    def _location_change(self, state, op, legacy, update, delta, view):
        before, after = self._resolved(op["before_record_ref"]), self._resolved(op["after_record_ref"])
        pair = (op["location_id"], op["realm_id"])
        row = next((x for x in state["locations"] if (x["location_id"], x["realm_id"]) == pair), None)
        _reject(row is None or row["current_record_ref"] != op["before_record_ref"]
                or any((d["location_id"], d["realm_id"]) != pair for d in (before, after))
                or self.record(op["after_record_ref"])["scope"] != self.scope.to_record())
        rule = self._rules[op["rule_id"]]
        _reject(rule["location_id"] != op["location_id"] or rule["source_current"] != before["current"]
                or rule["target_current"] != after["current"] or not set(rule["condition_refs"]) <= set(op["condition_refs"]))
        for ref in rule["condition_refs"]:
            self._condition(ref, view)
        _reject(legacy["target_ref"] != op["location_id"] or op["location_id"] not in delta["affected_location_refs"]
                or after["source_delta_ref"] != update["delta_ref"] or legacy["domain"] != "local_world_condition")
        changed = {key for key in before["current"] if before["current"][key] != after["current"][key]}
        _reject(not changed)
        if op["kind"] == "overlay":
            overlay = self._doc(op["overlay_ref"], "overlay")
            expected_sources = {"worldstate_delta_refs": [update["delta_ref"]],
                "player_state_snapshot_ref": delta["player_runtime_state_ref"],
                "location_state_record_ref": op["before_record_ref"]}
            if delta["source_branch_event_ref"] is not None:
                expected_sources["branch_event_ref"] = delta["source_branch_event_ref"]
            _reject(self.scope.truth_scope != "leaf_branch_state" or overlay["branch_id"] != self.scope.subject_id
                    or overlay["location_id"] != op["location_id"] or legacy["operation"] != "append_ref"
                    or self.record(op["overlay_ref"])["scope"] != self.scope.to_record()
                    or not changed <= {"access", "eligible_systems"} or overlay["source_refs"] != expected_sources
                    or overlay["overlay_id"] != op["overlay_ref"])
            _reject(after["source_mutation_ref"] != op["overlay_ref"])
        else:
            mutation = self._doc(op["mutation_ref"], "location_mutation")
            _reject(op["mutation_ref"] not in delta["location_mutation_refs"]
                    or mutation["mutation_delta_id"] != op["mutation_ref"]
                    or mutation["source_worldstate_delta_ref"] != update["delta_ref"]
                    or mutation["target_location_state_ref"] != op["before_record_ref"]
                    or mutation["source_player_runtime_state_ref"] != delta["player_runtime_state_ref"]
                    or mutation["source_branch_event_ref"] != delta["source_branch_event_ref"]
                    or mutation["persistence_scope"] != delta["persistence"]["scope"]
                    or after["source_mutation_ref"] != op["mutation_ref"]
                    or self.record(op["mutation_ref"])["scope"] != self.scope.to_record())
            fields = mutation["changed_fields"]
            _reject(len(fields) != len(changed) or {x["field_path"] for x in fields} != changed)
            classifications = {"status": "set_status", "phase": "set_status", "stability": "set_status",
                "access": "set_threshold_status", "eligible_systems": "append_ref",
                "active_plane_pressures": "adjust_plane_pressure", "residue_refs": "record_residue",
                "future_generation_bias_refs": "append_ref"}
            _reject(any(x["change_kind"] != classifications[x["field_path"]] for x in fields))
            operation = legacy["operation"]
            kinds = {"set_status": {"threshold_status_change", "public_condition_changed", "branch_local_condition_changed", "realm_bleed_contained"},
                     "activate_site": {"site_activation"}, "suppress_site": {"site_suppression"},
                     "adjust_pressure": {"plane_pressure_shift"}, "record_residue": {"residue_recorded"},
                     "append_ref": {"public_condition_changed", "branch_local_condition_changed"}}
            _reject(mutation["mutation_kind"] not in kinds.get(operation, set())
                    or mutation["mutation_kind"] == "realm_bleed_contained" and after["current"]["status"] != "contained")
            allowed = {"set_status": {"status", "phase", "stability", "access"},
                "activate_site": {"status", "access", "eligible_systems"},
                "suppress_site": {"status", "access", "eligible_systems"},
                "adjust_pressure": {"active_plane_pressures"}, "record_residue": {"residue_refs"},
                "append_ref": {"residue_refs", "future_generation_bias_refs", "eligible_systems"}}
            _reject(operation not in allowed or not changed <= allowed[operation]
                    or operation == "activate_site" and after["current"]["status"] != "activated"
                    or operation == "suppress_site" and after["current"]["status"] != "suppressed")
            if operation in ("append_ref", "record_residue"):
                _reject(any(not set(before["current"][k]) < set(after["current"][k]) for k in changed))
        row["current_record_ref"] = op["after_record_ref"]
        row["current_record_sha256"] = self.record(op["after_record_ref"])["sha256"]
        return {"target_kind": "location", "target_id": op["location_id"], "before": before, "after": after}, row

    def _shift(self, state, op, legacy, view, event_ref):
        _reject(legacy["operation"] != "commit_public_fact" or legacy["domain"] != "local_world_condition"
                or legacy["target_ref"] != op["player_id"])
        row = next((x for x in state["occupancies"] if x["player_id"] == op["player_id"]), None)
        _reject(row is None or {k: row[k] for k in ("location_id", "realm_id")} != op["before"]
                or op["before"] == op["after"])
        player = view.get(op["player_component_id"])
        _reject(player is None or player["state_sha256"] != op["player_state_sha256"])
        spine, plane_ref, plane = self._plane(player, op["player_id"])
        _reject(plane_ref != op["plane_state_ref"] or spine["current_leaf_branch_ref"] != row["branch_ref"]
                or spine["current_location_ref"] != row["location_id"])
        agent = player["state"]["records"][spine["state_refs"]["player_agent_state_ref"]]
        _reject(agent["kind"] != "agent" or agent["sha256"] != _digest(agent["document"])
                or agent["document"]["current_location_ref"] != row["location_id"]
                or agent["document"]["current_leaf_branch_ref"] != row["branch_ref"])
        target, source = op["after"]["realm_id"], op["before"]["realm_id"]
        _reject(not any((x["location_id"], x["realm_id"]) == (op["after"]["location_id"], target) for x in state["locations"]))
        plane_id = self._planes.get(target)
        _reject(plane_id not in plane["planes"])
        veildef = next((x for x in self._locations[row["location_id"]]["thin_veil_slots"] if x["target_realm_id"] == target), None)
        _reject(veildef is None or veildef["slot_id"] != op["veil_slot_id"])
        veil = next(x for x in state["facts"] if x["slot_id"] == op["veil_slot_id"])
        if self.scope.truth_scope == "leaf_branch_state":
            self._shared_veil(state, op, view, veil)
        fact = cv.AttunementFact(target, plane["planes"][plane_id]["score_q6"], veil["value"]["token"],
                                (plane_ref, veil["source_event_ref"]))
        request = cv.RealmAccessRequest(op["request_ref"], source, target, row["location_id"], (fact,))
        access = RealmEngine.evaluate_access(self._engine, request)
        _reject(type(access) is not cv.CoreResult or not RealmEngine.validate_owned_result(self._engine, access)
                or type(access.value) is not cv.RealmAccessResult or access.binding != self._binding
                or access.status != "COMPLETED" or access.value.eligible is not True or access.effect_status != "NONE"
                or cv.canonical_bytes(access.value.request) != cv.canonical_bytes(request))
        shift = RealmEngine.propose_shift(self._engine, access.value, proposal_ref=op["proposal_ref"])
        _reject(type(shift) is not cv.CoreResult or not RealmEngine.validate_owned_result(self._engine, shift)
                or type(shift.value) is not cv.RealmShiftProposal or shift.binding != self._binding
                or shift.status != "COMPLETED" or shift.effect_status != "PROPOSED_ONLY"
                or shift.value.before_realm_id != source or shift.value.target_realm_id != target
                or shift.value.proposal_ref != op["proposal_ref"]
                or cv.canonical_bytes(shift.value.access) != cv.canonical_bytes(access.value))
        before = _copy(row)
        row.update(op["after"], source_event_ref=event_ref)
        return {"target_kind": "occupancy", "target_id": row["player_id"], "before": before, "after": _copy(row)}, {
            "operation_id": op["operation_id"], "access_result": access.to_record(), "shift_result": shift.to_record()}

    def _shared_veil(self, state, op, view, veil):
        qualified = []
        for ref in op["condition_refs"]:
            condition = self._doc(ref, "condition")
            if condition["kind"] != "current_fact" or condition["slot_id"] != veil["slot_id"]:
                continue
            head = condition["head"]
            if head["scope"] != TruthScope(self.scope.world_id, "shared_worldstate", self.scope.world_id).to_record():
                continue
            shared = self._read(head, view)
            self._validate("state", shared)
            _reject(shared["component_id"] != head["component_id"] or shared["scope"] != head["scope"]
                    or any(shared[k] != state[k] for k in ("profile_id", "law_sha256", "geography_sha256")))
            slot = next((x for x in shared["facts"] if x["slot_id"] == veil["slot_id"]), None)
            _reject(slot is None or slot["definition_ref"] != veil["definition_ref"]
                    or slot["value"] != {"kind": "token", "token": "TRUE"}
                    or condition["expected_value"] != slot["value"])
            qualified.append(head)
        _reject(len(qualified) != 1)

    def reduce(self, state, packet, read_view):
        try:
            return self._reduce(_copy(state), _copy(packet), read_view)
        except JournalError:
            raise
        except (KeyError, TypeError, ValueError, StopIteration, RecursionError, Unresolvable):
            raise JournalError("POLICY_REJECTED") from None

    def _reduce(self, state, packet, read_view):
        self._state(state)
        self._validate("update", packet, "Packet")
        expected = self.packet(packet["principals"], packet["request_ref"], packet["update_ref"])
        _reject(packet != expected)
        update = self._updates[packet["update_ref"]]
        view, digest = self._view(read_view)
        _reject(digest != packet["read_vector_sha256"])
        _reject([{k: row[k] for k in HEAD_KEYS} for row in view.values()] != self.requirements(packet)["reads"])
        _reject(any(x["effect_id"] == update["effect_id"] or x["delta_ref"] == update["delta_ref"] for x in state["consumed_effects"]))
        delta, source, player = self._evidence(update, view)
        event_ref = "world-event:" + _digest({"scope": self.scope.to_record(), "component_id": self.component_id,
                                             "update_ref": update["update_ref"], "effect_id": update["effect_id"]})
        changes, realm_checks, targets = [], [], set()
        # Realm checks read the input state, never this update's prospective effects.
        original = _copy(state)
        for op, legacy in zip(update["resolutions"], delta["mutations"]):
            _reject(op["operation_id"] != legacy["operation_id"]
                    or not set(op["condition_refs"]) <= set(legacy["evidence_refs"]))
            for ref in op["condition_refs"]:
                self._condition(ref, view)
            key = (op["kind"] if op["kind"] in ("fact", "realm_shift") else "location",
                   op.get("slot_id", op.get("player_id", op.get("location_id"))))
            _reject(key in targets)
            targets.add(key)
            if op["kind"] == "fact":
                definition = self._facts[op["slot_id"]]
                row = next(x for x in state["facts"] if x["slot_id"] == op["slot_id"])
                _reject(not definition["mutable"] or row["value"] != op["before"] or op["before"] == op["after"]
                        or legacy["target_ref"] != op["slot_id"] or legacy["domain"] != definition["domain"])
                self._fact_value(definition, op["after"])
                operation = legacy["operation"]
                _reject(operation not in ("commit_public_fact", "adjust_pressure", "append_ref", "record_residue")
                        or operation == "adjust_pressure" and definition["value_kind"] != "integer")
                if operation in ("append_ref", "record_residue"):
                    _reject(definition["value_kind"] != "references" or not set(op["before"]["refs"]) < set(op["after"]["refs"]))
                row.update(value=op["after"], source_event_ref=event_ref)
                changes.append({"target_kind": "fact", "target_id": op["slot_id"], "before": op["before"], "after": op["after"]})
            elif op["kind"] == "realm_shift":
                change, result = self._shift(_copy(original), op, legacy, view, event_ref)
                next(x for x in state["occupancies"] if x["player_id"] == op["player_id"]).update(change["after"])
                changes.append(change)
                realm_checks.append(result)
            else:
                change, row = self._location_change(state, op, legacy, update, delta, view)
                row["history_event_refs"].append(event_ref)
                changes.append(change)
        target = update["compensates_effect_id"]
        if target is not None:
            previous = next((x for x in state["events"] if x["effect_id"] == target), None)
            _reject(previous is None or any(x["compensates_effect_id"] == target for x in state["events"]))
            _reject(not self._doc(previous["delta_ref"], "delta")["reversibility"]["reversible"])
            _reject(any(c["target_kind"] != "fact" for c in changes) or len(changes) != len(previous["changes"]))
            for now, old in zip(changes, previous["changes"]):
                _reject(now["target_kind"] != old["target_kind"] or now["target_id"] != old["target_id"]
                        or now["before"] != old["after"] or now["after"] != old["before"])
        for ref in packet["selected_record_sha256"]:
            state["records"][ref] = self.record(ref)
        state["events"].append({"event_ref": event_ref, "request_ref": packet["request_ref"],
            "effect_id": update["effect_id"], "update_ref": update["update_ref"], "delta_ref": update["delta_ref"],
            "source_read_vector_sha256": digest, "changes": changes, "realm_checks": realm_checks,
            "retention": update["retention"], "compensates_effect_id": target, "provenance": update["provenance"]})
        state["consumed_effects"].append({"effect_id": update["effect_id"], "delta_ref": update["delta_ref"],
                                         "delta_sha256": self.record(update["delta_ref"])["sha256"]})
        self._state(state)
        return _copy(state)

    def project_facts(self, state):
        state = _copy(state)
        try:
            self._state(state)
            return {"scope": self.scope.to_record(), "component_id": self.component_id,
                    "facts": sorted(state["facts"], key=lambda x: x["slot_id"])}
        except JournalError:
            raise
        except (KeyError, TypeError, ValueError, StopIteration):
            raise JournalError("POLICY_REJECTED") from None
