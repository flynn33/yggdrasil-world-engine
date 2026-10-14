"""Pure, bounded branch lineage and typed reconciliation. [YWE-REQ-0059]

The read view is trusted coordinator composition, like pure owner state inputs.
It does not authenticate a serialized state supplied by an external client.
"""

from __future__ import annotations

import json

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError
from referencing import Registry, Resource
from referencing.exceptions import NoSuchResource

from core.commit_set_journal import (
    CommitSetReadView, _bounded_bytes, _component, _head, _head_of,
)
from core.state_journal import JournalError, TruthScope, _encode, _hash, _identifier


FORMAT = "ywe.branch_owner.v1"
SCHEMAS = {
    "branch": "m4_leaf_branch_reality_state_schema.json",
    "event": "m4_branch_event_schema.json",
    "owner": "m4_branch_owner_schema.json",
    "context": "m4_branch_generation_context_schema.json",
    "world": "m4_world_location_state_schema.json",
}
SOURCES = {"world_bootstrap": {"bootstrap"}, "narrative_engine": {"fork", "advance"},
           "runtime_cosmology": {"merge"}}
KINDS = {"bootstrap": "Bootstrap", "context": "Context", "event": None,
         "decision": "Decision", "reference": "Reference", "definition": "Definition",
         "projection": "Projection", "resolution": "Resolution"}
HISTORY = ("branch_event_refs", "worldstate_delta_refs", "location_overlay_refs", "manifest_refs",
           "future_generation_bias_refs", "occurrences")


def _reject(condition, code="POLICY_REJECTED"):
    if condition:
        raise JournalError(code)


def _shape(value, keys):
    _reject(type(value) is not dict or set(value) != set(keys.split()), "INVALID_VALUE")


def _copy(value):
    return json.loads(_bounded_bytes(value, (65536, 4096, 32)))


def _config(value):
    return json.loads(_bounded_bytes(value, (2 * 1024 * 1024, 131072, 40)))


def _component_copy(value):
    # The owner state's budget is enforced independently by _component.
    return json.loads(_bounded_bytes(value, (69632, 4200, 34)))


def _digest(value):
    return _hash(_encode(value))


def _key(value):
    return _encode(value)


def _unique(rows, field):
    _reject(len({row[field] for row in rows}) != len(rows), "INVALID_VALUE")


def _presence(slot):
    return {"present": False} if slot is None else {"present": True, "value": slot["value"]}


def _occ_key(row):
    return _key([row["namespace"], row["identity_parts"]])


def _contains(value, digest):
    """Find an exact retained document, not a digest-valued assertion."""
    pending = [value]
    while pending:
        item = pending.pop()
        if _digest(item) == digest:
            return True
        if type(item) is dict:
            pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)
    return False


def _occurrence_matches(value, digest, source_ref):
    pending = [value]
    while pending:
        item = pending.pop()
        if type(item) is dict:
            if _digest(item) == digest:
                return source_ref in (item.get("event_ref"), item.get("delta_ref"), item.get("update_ref"))
            pending.extend(item.values())
        elif type(item) is list:
            pending.extend(item)
    return False


def _ordered_union(left, right, identity=_key):
    """Stable topological union; equal identity must have equal complete payload."""
    values, edges, incoming = {}, {}, {}
    for rows in (left, right):
        prior = None
        seen = set()
        for row in rows:
            key = identity(row)
            _reject(key in seen, "DUPLICATE_IDENTITY")
            seen.add(key)
            if key in values:
                _reject(values[key] != row, "IDENTITY_CONFLICT")
            edges.setdefault(key, set())
            incoming.setdefault(key, 0)
            values[key] = row
            if prior is not None and key not in edges[prior]:
                edges[prior].add(key)
                incoming[key] += 1
            prior = key
    ready = sorted(key for key in values if incoming[key] == 0)
    result = []
    while ready:
        key = ready.pop(0)
        result.append(values[key])
        for child in sorted(edges[key]):
            incoming[child] -= 1
            if incoming[child] == 0:
                ready.append(child)
                ready.sort()
    _reject(len(result) != len(values), "HISTORY_ORDER_CONFLICT")
    return result


def _schema_bundle(schemas):
    _shape(schemas, " ".join(SCHEMAS))
    schemas = _config(schemas)
    resources = {}
    try:
        for kind, filename in SCHEMAS.items():
            value = schemas[kind]
            _reject(type(value) is not dict or value.get("$id") != "https://ywe.local/schemas/" + filename
                    or value.get("$schema") != "https://json-schema.org/draft/2020-12/schema", "INVALID_SCHEMA")
            Draft202012Validator.check_schema(value)
            resources[value["$id"]] = value
        checked = set()

        def visit(node, root, active):
            if type(node) is dict:
                _reject("$dynamicRef" in node or "$dynamicAnchor" in node, "INVALID_SCHEMA")
                if "$ref" in node:
                    value = node["$ref"]
                    _reject(type(value) is not str, "INVALID_SCHEMA")
                    uri, sep, fragment = value.partition("#")
                    target_root = root if not uri else resources.get(uri)
                    _reject(target_root is None or sep and fragment and not fragment.startswith("/"), "INVALID_SCHEMA")
                    target = target_root
                    try:
                        for part in fragment.split("/")[1:]:
                            target = target[part.replace("~1", "/").replace("~0", "~")]
                    except (KeyError, TypeError):
                        raise JournalError("INVALID_SCHEMA") from None
                    marker = (target_root["$id"], fragment)
                    _reject(marker in active, "INVALID_SCHEMA")
                    if marker not in checked:
                        visit(target, target_root, active | {marker})
                        checked.add(marker)
                for name, value in node.items():
                    if name == "$id":
                        _reject(node is not root, "INVALID_SCHEMA")
                    elif name != "$ref":
                        visit(value, root, active)
            elif type(node) is list:
                for value in node:
                    visit(value, root, active)

        for kind in ("branch", "event", "owner", "context"):
            visit(schemas[kind], schemas[kind], set())

        def deny(uri):
            raise NoSuchResource(ref=uri)

        registry = Registry(retrieve=deny).with_resources(
            (uri, Resource.from_contents(value)) for uri, value in resources.items())
        validators = {kind: Draft202012Validator(value, registry=registry) for kind, value in schemas.items()}
        for name in schemas["context"]["$defs"]:
            validators[name] = Draft202012Validator(
                {"$ref": schemas["context"]["$id"] + "#/$defs/" + name}, registry=registry)
        return validators, {kind: _digest(value) for kind, value in schemas.items()}
    except (SchemaError, KeyError, TypeError, ValueError, RecursionError):
        raise JournalError("INVALID_SCHEMA") from None


class BranchReadView:
    """Detached current/staged owner outputs and journal-derived historical bodies."""

    def __init__(self, world_id, before, after, history, actions, effects, creations=None, retentions=None, staged_history=None):
        _identifier(world_id)
        _reject(type(history) is not CommitSetReadView or history._world_id != world_id, "INVALID_VIEW")
        self._world, self._history = world_id, history
        self._before, self._after = {}, {}
        for source, destination in ((before, self._before), (after, self._after)):
            _reject(type(source) is not list or len(source) > 16, "VALUE_LIMIT")
            for row in source:
                item = _component_copy(row)
                _component(item, world_id)
                _reject(item["component_id"] in destination, "INVALID_VIEW")
                destination[item["component_id"]] = _encode(item)
        staged_history = [] if staged_history is None else staged_history
        _reject(type(staged_history) is not list or len(staged_history) > 32, "VALUE_LIMIT")
        self._staged_history = {}
        for row in staged_history:
            item = _component_copy(row)
            _component(item, world_id)
            _reject(item["component_id"] not in self._before, "UNAUTHORIZED_READ")
            key = _key(_head_of(item))
            _reject(key in self._staged_history, "INVALID_VIEW")
            self._staged_history[key] = _encode(item)
        self._actions, self._effects = _copy(actions), _copy(effects)
        self._creations = _copy([] if creations is None else creations)
        self._retentions = _copy([] if retentions is None else retentions)
        _reject(any(type(rows) is not list or len(rows) > 32
                    for rows in (self._actions, self._effects, self._creations, self._retentions)), "VALUE_LIMIT")
        _reject(any(type(row) is not dict for rows in
                    (self._actions, self._effects, self._creations, self._retentions) for row in rows), "INVALID_VIEW")
        for row in self._actions:
            _shape(row, "adapter_id action_ref action_sha256 player_component_id player_before_head source_branch_head player_id source_branch_id target_branch_id location_ref action_kind chosen_action decision_ref player_update_ref consequence_ref resulting_delta_refs source_refs")
        for row in self._effects:
            _shape(row, "effect_ref projection_ref component_id before_head source_event_ref before after source_occurrence_sha256")
        for row in self._creations:
            _shape(row, "player_id component_id head creation_ref source_sha256")
        for row in self._retentions:
            _shape(row, "component_id before_head occurrences consumed")

    def before(self, component_id):
        _identifier(component_id)
        _reject(component_id not in self._before, "UNKNOWN_COMPONENT_HEAD")
        return json.loads(self._before[component_id])

    def after(self, component_id):
        _identifier(component_id)
        _reject(component_id not in self._after, "UNKNOWN_COMPONENT_HEAD")
        return json.loads(self._after[component_id])

    def component_at(self, head):
        _head(head, self._world)
        _reject(head["component_id"] not in self._before, "UNAUTHORIZED_READ")
        current = self._before.get(head["component_id"])
        if current is not None:
            value = json.loads(current)
            if _head_of(value) == head:
                return value
        staged = self._staged_history.get(_key(head))
        if staged is not None:
            return json.loads(staged)
        value = self._history.component_at(head)
        _component(value, self._world)
        _reject(_head_of(value) != head, "INVALID_VIEW")
        return _component_copy(value)

    def actions(self):
        return _copy(self._actions)

    def effects(self):
        return _copy(self._effects)

    def creations(self):
        return _copy(self._creations)

    def retentions(self):
        return _copy(self._retentions)


class BranchStatePolicy:
    """Neutral branch owner. It returns state; only the coordinator publishes."""

    def __init__(self, world_id, branch_id, owner_player_id, profile, grants, records, proposals, schemas):
        for value in (world_id, branch_id, owner_player_id):
            _identifier(value)
        self._scope = TruthScope(world_id, "leaf_branch_state", branch_id)
        self._player = owner_player_id
        self._validators, hashes = _schema_bundle(schemas)
        self._profile, self._grants = _copy(profile), _copy(grants)
        self._valid("Profile", self._profile, "INVALID_POLICY")
        self._component_id = self._profile["component_id"]
        for field, key in (("projections", "projection_ref"), ("choice_rules", "rule_id")):
            _unique(self._profile[field], key)
        self._bindings = {row["projection_ref"]: row for row in self._profile["projections"]}
        _reject(type(grants) is not dict or not 1 <= len(grants) <= 32, "INVALID_POLICY")
        for principal, grant in self._grants.items():
            _identifier(principal)
            _shape(grant, "source_system operations")
            source, operations = grant["source_system"], grant["operations"]
            _reject(type(source) is not str or source not in SOURCES or type(operations) is not list
                    or not operations or any(type(item) is not str for item in operations)
                    or len(set(operations)) != len(operations) or not set(operations) <= SOURCES[source], "INVALID_POLICY")
        self._records = self._catalog(records)
        _reject(type(proposals) is not list or len(proposals) > 128, "VALUE_LIMIT")
        self._proposals = {}
        for proposal in proposals:
            proposal = _copy(proposal)
            self._valid("Proposal", proposal, "INVALID_POLICY")
            self._identity(proposal)
            _reject(proposal["proposal_ref"] in self._proposals, "INVALID_POLICY")
            self._proposals[proposal["proposal_ref"]] = _encode(proposal)
        for binding in self._bindings.values():
            definition = self.record(binding["definition_ref"])
            if binding["target_kind"] == "fact":
                _reject(definition["kind"] != "definition" or definition["document"]["slot_id"] != binding["target_id"]
                        or definition["document"]["mergeable"] != binding["mergeable"], "INVALID_POLICY")
            elif binding["target_kind"] == "player_component":
                _reject(definition["kind"] != "reference"
                        or definition["document"]["category"] != "player_component"
                        or definition["document"]["subject_ref"] != binding["target_id"], "INVALID_POLICY")
            else:
                # Location and observer projection adapters need their own fixed semantics.
                raise JournalError("UNSUPPORTED_PROJECTION")
        for rule in self._profile["choice_rules"]:
            _reject(not set(rule["effect_projection_refs"]) <= self._bindings.keys()
                    or rule["minimum_effects"] > len(rule["effect_projection_refs"]), "INVALID_POLICY")
        semantic = _copy(self._profile)
        del semantic["component_id"], semantic["bootstrap_ref"]
        for binding in semantic["projections"]:
            del binding["component_id"]
        self._profile_hash = _digest(semantic)
        self._initial = {"format": FORMAT, "world_id": world_id, "branch_id": branch_id,
                         "owner_player_id": owner_player_id, "branch": None, "events": {}}
        self._policy_id = "branch.v1:" + _digest({"format": FORMAT, "scope": self._scope.to_record(),
            "player": owner_player_id, "profile": self._profile, "grants": self._grants,
            "schemas": hashes, "bootstrap": None if profile["bootstrap_ref"] is None
            else self.record(profile["bootstrap_ref"])})

    @property
    def scope(self):
        return self._scope

    @property
    def component_id(self):
        return self._component_id

    @property
    def policy_id(self):
        return self._policy_id

    def initial_state(self):
        return _copy(self._initial)

    def record(self, ref):
        _identifier(ref)
        _reject(ref not in self._records, "UNKNOWN_EVIDENCE")
        return json.loads(self._records[ref])

    def _document(self, ref, kind):
        wrapper = self.record(ref)
        _reject(wrapper["kind"] != kind, "INVALID_EVIDENCE")
        return wrapper["document"]

    def _valid(self, name, value, code="POLICY_REJECTED"):
        _reject(not self._validators[name].is_valid(value), code)

    def _identity(self, value):
        _reject(value["world_id"] != self.scope.world_id or value["owner_player_id"] != self._player
                or value["target_branch_id"] != self.scope.subject_id, "INVALID_SCOPE")

    def _catalog(self, records):
        _reject(type(records) is not list or len(records) > 128, "VALUE_LIMIT")
        result = {}
        for item in records:
            item = _copy(item)
            _shape(item, "ref kind scope document sha256 provenance")
            _identifier(item["ref"])
            self._valid("Scope", item["scope"], "INVALID_POLICY")
            self._valid("Provenance", item["provenance"], "INVALID_POLICY")
            _reject(item["scope"]["world_id"] != self.scope.world_id or type(item["kind"]) is not str or item["kind"] not in KINDS
                    or item["ref"] in result or item["sha256"] != _digest(item["document"]), "INVALID_POLICY")
            self._valid("event" if item["kind"] == "event" else KINDS[item["kind"]], item["document"], "INVALID_POLICY")
            if item["kind"] == "definition":
                self._definition(item["document"])
            result[item["ref"]] = _encode(item)
        return result

    def _definition(self, definition):
        kind = definition["value_kind"]
        if kind == "integer":
            _reject(type(definition["minimum"]) is not int or type(definition["maximum"]) is not int
                    or definition["minimum"] > definition["maximum"] or definition["allowed_values"], "INVALID_POLICY")
        else:
            _reject(definition["minimum"] is not None or definition["maximum"] is not None
                    or (kind == "boolean") != (not definition["allowed_values"]), "INVALID_POLICY")

    def _value(self, definition_ref, value):
        definition = self.record(definition_ref)["document"]
        _reject(value["kind"] != definition["value_kind"])
        kind = value["kind"]
        if kind == "integer":
            _reject(not definition["minimum"] <= value["value"] <= definition["maximum"])
        if kind in ("token", "reference"):
            _reject(value["token" if kind == "token" else "ref"] not in definition["allowed_values"])
        if kind == "references":
            _reject(value["refs"] != sorted(set(value["refs"])) or not set(value["refs"]) <= set(definition["allowed_values"]))

    def _select(self, proposal):
        pending = [proposal["generation_context_ref"]] + [b["definition_ref"] for b in self._bindings.values()]
        operation = proposal["operation"]
        pending += [operation["bootstrap_ref"]] if operation["kind"] == "bootstrap" else [operation["event_ref"]]
        pending += operation.get("resolution_refs", [])
        selected = {}
        while pending:
            ref = pending.pop()
            if ref in selected:
                continue
            wrapper = self.record(ref)
            source_scope = wrapper["scope"]
            allowed_branches = {row["scope"]["subject_id"] for row in proposal["expected_heads"]
                                if row["scope"]["truth_scope"] == "leaf_branch_state"} | {self.scope.subject_id}
            _reject(source_scope["truth_scope"] == "player_perception"
                    or source_scope["truth_scope"] == "player_state" and source_scope["subject_id"] != self._player
                    or source_scope["truth_scope"] == "shared_worldstate" and source_scope["subject_id"] != self.scope.world_id
                    or source_scope["truth_scope"] == "leaf_branch_state" and source_scope["subject_id"] not in allowed_branches,
                    "INVALID_SCOPE")
            selected[ref] = _digest(wrapper)
            kind, document = wrapper["kind"], wrapper["document"]
            if kind == "context":
                for field in ("player_context_refs", "location_context_refs", "cosmology_source_refs",
                              "asp_component_refs", "diagnostic_refs", "future_generation_bias_refs"):
                    pending.extend(document[field])
            elif kind == "bootstrap":
                pending.extend([document["player_creation_ref"], document["initial_location_ref"], document["generation_context_ref"]])
                pending.extend(document["initial_projection_refs"])
            elif kind == "event":
                pending.extend([document["agent_ref"], document["base_world_ref"], document["generation_context_ref"]])
                if document["decision_context"] is not None:
                    pending.append(document["decision_context"])
                for field in ("resolution_refs", "worldstate_delta_refs", "future_generation_bias_refs", "cosmology_source_refs", "asp_component_refs"):
                    pending.extend(document[field])
            elif kind == "decision":
                pending.extend([document["location_ref"], document["player_context_ref"]])
            elif kind == "projection":
                pending.append(document["slot"]["definition_ref"])
            elif kind == "resolution":
                pending.extend(document["reason_refs"])
            _reject(len(selected) > 128, "VALUE_LIMIT")
        return selected

    def _authorize(self, principal, proposal_ref):
        for value in (principal, proposal_ref):
            _identifier(value)
        _reject(principal not in self._grants, "UNAUTHORIZED")
        _reject(proposal_ref not in self._proposals, "UNKNOWN_EVIDENCE")
        proposal = json.loads(self._proposals[proposal_ref])
        grant = self._grants[principal]
        _reject(proposal["source_system"] != grant["source_system"]
                or proposal["operation"]["kind"] not in grant["operations"], "UNAUTHORIZED")
        return proposal

    def packet(self, principal, request_id, proposal_ref):
        _identifier(request_id)
        proposal = self._authorize(principal, proposal_ref)
        return _copy({"format": "ywe.branch_packet.v1", "policy_id": self.policy_id,
                      "principal": principal, "request_id": request_id, "proposal_ref": proposal_ref,
                      "proposal_sha256": _digest(proposal), "record_sha256": self._select(proposal)})

    def _proposal(self, packet):
        _shape(packet, "format policy_id principal request_id proposal_ref proposal_sha256 record_sha256")
        _reject(packet != self.packet(packet["principal"], packet["request_id"], packet["proposal_ref"]), "PACKET_MISMATCH")
        return json.loads(self._proposals[packet["proposal_ref"]])

    def requirements(self, packet):
        proposal = self._proposal(_copy(packet))
        return self._requirements(proposal)

    def _requirements(self, proposal):
        context = self._document(proposal["generation_context_ref"], "context")
        reads, historical = list(context["read_heads"]), []
        operation = proposal["operation"]
        if operation["kind"] == "bootstrap":
            bootstrap = self._document(operation["bootstrap_ref"], "bootstrap")
            reads += bootstrap["world_heads"]
            for ref in bootstrap["initial_projection_refs"]:
                reads.append(self._document(ref, "projection")["head"])
        else:
            reads += operation.get("parent_heads", [operation.get("parent_head", operation.get("previous_head"))])
            if operation["kind"] == "merge":
                historical.append(operation["base_head"])
        reads = sorted({_key(row): row for row in reads}.values(), key=_key)
        _reject(len({row["component_id"] for row in reads}) != len(reads), "INVALID_READ_SET")
        complete = sorted({_key(row): row for row in reads + historical}.values(), key=_key)
        _reject(sorted(proposal["expected_heads"], key=_key) != complete, "INVALID_READ_SET")
        writes = [{"component_id": self.component_id, "partition_id": "branch_lineage",
                   "target_kind": "branch", "target_id": self.scope.subject_id}]
        for change in operation.get("changes", []):
            writes.append({"component_id": self.component_id, "partition_id": "branch_lineage",
                           "target_kind": "projection", "target_id": change["slot_id"]})
        creates = [] if operation["kind"] == "advance" else [{"component_id": self.component_id,
            "scope": self.scope.to_record(), "partition_id": "branch_lineage", "owner_policy_id": self.policy_id}]
        return _copy({"reads": reads, "historical_reads": historical,
                      "write_keys": sorted(writes, key=_key), "creates": creates})

    def _read(self, proposal, view):
        _reject(type(view) is not BranchReadView or view._world != self.scope.world_id, "INVALID_VIEW")
        requirements = self._requirements(proposal)
        for head in requirements["reads"]:
            _reject(_head_of(view.before(head["component_id"])) != head, "STALE_COMPONENT")
        for head in requirements["historical_reads"]:
            view.component_at(head)

    def genesis(self, principal, proposal_ref, view):
        proposal = self._authorize(principal, proposal_ref)
        _reject(proposal["operation"]["kind"] != "bootstrap", "INVALID_CREATION")
        self._select(proposal)
        self._read(proposal, view)
        context = self._context(proposal, view, "root")
        state = self.initial_state()
        state["branch"] = self._bootstrap(proposal, view, context)
        self._valid("owner", state)
        return _copy(state)

    def _branch(self, component):
        _reject(component["scope"]["truth_scope"] != "leaf_branch_state", "INVALID_SCOPE")
        state = component["state"]
        self._valid("owner", state)
        branch = state["branch"]
        _reject(branch is None or state["world_id"] != self.scope.world_id
                or state["owner_player_id"] != self._player
                or branch["world_id"] != self.scope.world_id or branch["owner_player_id"] != self._player
                or state["branch_id"] != branch["leaf_branch_id"]
                or branch["profile_id"] != self._profile["profile_id"]
                or branch["leaf_branch_id"] != component["scope"]["subject_id"]
                or branch["profile_sha256"] != self._profile_hash
                or branch["law_bindings"] != self._profile["law_bindings"], "INCOMPATIBLE_BRANCH")
        _unique(branch["current_slots"], "slot_id")
        for slot in branch["current_slots"]:
            self._value(slot["definition_ref"], slot["value"])
        _reject(set(state["events"]) != set(branch["history"]["branch_event_refs"]))
        for key, event in state["events"].items():
            _reject(key != event["branch_event_id"] or event["world_id"] != self.scope.world_id
                    or event["owner_player_id"] != self._player)
        return state

    def _context(self, proposal, view, kind):
        wrapper = self.record(proposal["generation_context_ref"])
        _reject(wrapper["kind"] != "context" or wrapper["scope"] != self.scope.to_record(), "INVALID_SCOPE")
        context = wrapper["document"]
        self._identity(context)
        _reject(context["kind"] != kind or context["context_id"] != proposal["generation_context_ref"])
        for head in context["read_heads"]:
            _reject(_head_of(view.before(head["component_id"])) != head, "STALE_COMPONENT")
        for ref in context["cosmology_source_refs"] + context["asp_component_refs"]:
            _reject(self.record(ref)["scope"]["truth_scope"] not in ("shared_worldstate", "leaf_branch_state"), "INVALID_SCOPE")
        return context

    def _bootstrap(self, proposal, view, context):
        ref = proposal["operation"]["bootstrap_ref"]
        _reject(ref != self._profile["bootstrap_ref"] or context["event_ref"] is not None)
        wrapper = self.record(ref)
        bootstrap = wrapper["document"]
        _reject(wrapper["kind"] != "bootstrap" or wrapper["scope"] != self.scope.to_record()
                or bootstrap["world_id"] != self.scope.world_id or bootstrap["owner_player_id"] != self._player
                or bootstrap["branch_id"] != self.scope.subject_id
                or bootstrap["generation_context_ref"] != proposal["generation_context_ref"], "INVALID_SCOPE")
        for raw in view._before.values():
            existing = json.loads(raw)
            state = existing["state"]
            _reject(type(state) is dict and state.get("format") == FORMAT and state.get("owner_player_id") == self._player
                    and state.get("branch") is not None, "ROOT_EXISTS")
        for head in bootstrap["world_heads"]:
            _reject(head["scope"] != TruthScope(self.scope.world_id, "shared_worldstate", self.scope.world_id).to_record()
                    or _head_of(view.before(head["component_id"])) != head, "INVALID_SCOPE")
        witnesses = [row for row in view.creations() if row.get("creation_ref") == bootstrap["player_creation_ref"]]
        _reject(len(witnesses) != 1, "INVALID_CREATION")
        witness = witnesses[0]
        _shape(witness, "player_id component_id head creation_ref source_sha256")
        player = view.before(witness["component_id"])
        creation = self.record(witness["creation_ref"])
        _reject(witness["player_id"] != self._player or witness["head"] != _head_of(player)
                or player["scope"] != TruthScope(self.scope.world_id, "player_state", self._player).to_record()
                or witness["source_sha256"] != player["state_sha256"] or creation["kind"] != "reference"
                or creation["document"]["category"] != "player_creation_ref"
                or creation["document"]["source_sha256"] != witness["source_sha256"], "INVALID_CREATION")
        base = [self.record(r) for r in context["cosmology_source_refs"]
                if self.record(r)["kind"] == "reference" and self.record(r)["document"]["category"] == "base_world_ref"]
        pressure = [self.record(r) for r in context["cosmology_source_refs"]
                    if self.record(r)["kind"] == "reference" and self.record(r)["document"]["category"] == "active_plane_pressure_ref"]
        _reject(len(base) != 1 or len(pressure) != 1)
        _reject(any(row["scope"]["truth_scope"] != "shared_worldstate" for row in base + pressure), "INVALID_SCOPE")
        pressure_ref = pressure[0]["ref"]
        if pressure[0]["document"]["subject_ref"] == "none":
            _reject(pressure[0]["document"]["source_sha256"] != _digest(None))
            pressure_ref = None
        slots = []
        for selected in bootstrap["initial_projection_refs"]:
            projection = self.record(selected)
            _reject(projection["kind"] != "projection")
            document = projection["document"]
            binding = self._bindings.get(document["projection_ref"])
            _reject(binding is None or binding["target_kind"] != "fact")
            component = view.before(binding["component_id"])
            _reject(_head_of(component) != document["head"] or component["scope"]["truth_scope"] not in ("leaf_branch_state", "shared_worldstate"), "INVALID_SCOPE")
            candidates = [slot for slot in component["state"].get("facts", []) if slot["slot_id"] == binding["target_id"]]
            _reject(candidates != [document["slot"]] or document["slot"]["definition_ref"] != binding["definition_ref"])
            self._value(binding["definition_ref"], document["slot"]["value"])
            slots.append(document["slot"])
        _unique(slots, "slot_id")
        return {"schema_id": "ywe.leaf_branch_reality_state.v2", "schema_version": "2.0.0",
            "world_id": self.scope.world_id, "leaf_branch_id": self.scope.subject_id,
            "owner_player_id": self._player, "truth_scope": "leaf_branch_state",
            "profile_id": self._profile["profile_id"], "profile_sha256": self._profile_hash,
            "law_bindings": self._profile["law_bindings"], "base_world_ref": base[0]["ref"],
            "lineage": {"kind": "root", "parents": [], "common_base": None, "bootstrap_ref": ref,
                        "event_ref": None, "shared_heads": bootstrap["world_heads"]},
            "branch_status": "active", "generation_context_ref": context["context_id"],
            "active_plane_pressure_ref": pressure_ref, "current_slots": sorted(slots, key=lambda row: row["slot_id"]),
            "derived_view_refs": [], "history": {key: [] for key in HISTORY}, "consumed": [],
            "provenance": proposal["provenance"]}

    def _event(self, proposal, context, parents, base):
        wrapper = self.record(proposal["operation"]["event_ref"])
        _reject(wrapper["kind"] != "event" or wrapper["scope"] != self.scope.to_record(), "INVALID_SCOPE")
        event = wrapper["document"]
        self._identity(event)
        _reject(event["branch_event_id"] != proposal["operation"]["event_ref"]
                or context["event_ref"] != event["branch_event_id"]
                or event["parent_heads"] != parents or event["common_base"] != base
                or event["generation_context_ref"] != context["context_id"]
                or event["read_heads"] != context["read_heads"]
                or event["future_generation_bias_refs"] != context["future_generation_bias_refs"]
                or event["cosmology_source_refs"] != context["cosmology_source_refs"]
                or event["asp_component_refs"] != context["asp_component_refs"])
        return event

    def _choice(self, event, parent, view):
        decision_wrapper = self.record(event["decision_context"])
        decision = decision_wrapper["document"]
        _reject(decision_wrapper["kind"] != "decision" or decision["chosen_action"] not in decision["available_actions"])
        actions = [a for a in view.actions() if a.get("action_ref") == decision["source_action_ref"]]
        _reject(len(actions) != 1, "UNQUALIFIED_CHOICE")
        action = actions[0]
        self._valid("Action", action)
        before, after = view.before(action["player_component_id"]), view.after(action["player_component_id"])
        _reject(action["adapter_id"] != self._profile["action_adapter_id"] or action["player_id"] != self._player
                or before["scope"] != TruthScope(self.scope.world_id, "player_state", self._player).to_record()
                or after["scope"] != before["scope"] or after["owner_policy_id"] != before["owner_policy_id"]
                or action["player_before_head"] != _head_of(before) or action["source_branch_head"] != parent
                or action["source_branch_id"] != parent["scope"]["subject_id"]
                or action["target_branch_id"] != event["target_branch_id"]
                or action["location_ref"] != decision["location_ref"]
                or action["decision_ref"] != decision["decision_ref"]
                or action["chosen_action"] != decision["chosen_action"]
                or action["resulting_delta_refs"] != event["worldstate_delta_refs"]
                or not _contains(after["state"], action["action_sha256"])
                or _contains(before["state"], action["action_sha256"]), "UNQUALIFIED_CHOICE")
        rules = [rule for rule in self._profile["choice_rules"] if rule["action_kind"] == action["action_kind"]
                 and action["chosen_action"] in rule["action_tokens"]
                 and decision["choice_significance"] in rule["significance_values"]
                 and set(rule["required_cosmology_refs"]) <= set(event["cosmology_source_refs"])
                 and set(rule["required_asp_refs"]) <= set(event["asp_component_refs"])]
        _reject(len(rules) != 1, "UNQUALIFIED_CHOICE")
        effects = {}
        for effect in view.effects():
            self._valid("Effect", effect)
            binding = self._bindings.get(effect["projection_ref"])
            _reject(binding is None or effect["component_id"] != binding["component_id"]
                    or effect["projection_ref"] in effects)
            prior, staged = view.before(effect["component_id"]), view.after(effect["component_id"])
            _reject(effect["before_head"] != _head_of(prior) or prior["scope"] != staged["scope"]
                    or prior["owner_policy_id"] != staged["owner_policy_id"]
                    or effect["before"] == effect["after"]
                    or not _occurrence_matches(staged["state"], effect["source_occurrence_sha256"], effect["source_event_ref"])
                    or _contains(prior["state"], effect["source_occurrence_sha256"]), "UNQUALIFIED_EFFECT")
            if binding["target_kind"] == "player_component":
                _reject(effect["component_id"] != action["player_component_id"]
                        or effect["source_event_ref"] != action["player_update_ref"], "UNQUALIFIED_EFFECT")
            else:
                for component, field in ((prior, "before"), (staged, "after")):
                    values = [slot for slot in component["state"].get("facts", []) if slot["slot_id"] == binding["target_id"]]
                    _reject(len(values) > 1 or effect[field] != _presence(values[0] if values else None), "UNQUALIFIED_EFFECT")
                _reject(effect["source_event_ref"] not in action["resulting_delta_refs"], "UNQUALIFIED_EFFECT")
            effects[effect["projection_ref"]] = effect
        allowed = set(rules[0]["effect_projection_refs"])
        _reject(len(set(effects) & allowed) < rules[0]["minimum_effects"], "UNQUALIFIED_EFFECT")
        return action, effects

    def _changes(self, branch, changes, effects):
        _unique(changes, "slot_id")
        slots = {row["slot_id"]: row for row in branch["current_slots"]}
        for change in changes:
            bindings = [b for b in self._bindings.values() if b["target_kind"] == "fact" and b["target_id"] == change["slot_id"]]
            _reject(len(bindings) != 1)
            binding = bindings[0]
            effect = effects.get(binding["projection_ref"])
            _reject(effect is None or effect["before"] != change["before"] or effect["after"] != change["after"]
                    or effect["source_event_ref"] != change["source_occurrence_ref"]
                    or change["definition_ref"] != binding["definition_ref"]
                    or change["before"] != _presence(slots.get(change["slot_id"])))
            definition = self.record(binding["definition_ref"])["document"]
            _reject(not definition["mutable"] or not change["after"]["present"], "UNSUPPORTED_DELETION")
            self._value(binding["definition_ref"], change["after"]["value"])
            slots[change["slot_id"]] = {"slot_id": change["slot_id"], "definition_ref": binding["definition_ref"],
                "value": change["after"]["value"], "source_event_ref": change["source_occurrence_ref"]}
        branch["current_slots"] = sorted(slots.values(), key=lambda row: row["slot_id"])

    def _ancestry(self, head, view, nodes, active):
        marker = _key(head)
        _reject(marker in active, "ANCESTRY_CYCLE")
        if marker in nodes:
            return
        _reject(len(nodes) >= 64, "VALUE_LIMIT")
        state = self._branch(view.component_at(head))
        branch = state["branch"]
        edges = list(branch["lineage"]["parents"])
        if branch["history"]["branch_event_refs"]:
            latest = state["events"][branch["history"]["branch_event_refs"][-1]]
            edges += latest["parent_heads"]
        edges = {_key(item): item for item in edges}
        _reject(marker in edges, "ANCESTRY_CYCLE")
        nodes[marker] = (head, state, set(edges))
        for parent in edges.values():
            self._ancestry(parent, view, nodes, active | {marker})

    def _merge(self, proposal, view, context):
        operation = proposal["operation"]
        parents = operation["parent_heads"]
        _reject(parents != sorted(parents, key=_key) or parents[0]["component_id"] == parents[1]["component_id"], "INVALID_LINEAGE")
        for head in parents:
            _reject(_head_of(view.before(head["component_id"])) != head, "STALE_COMPONENT")
        nodes = {}
        for head in parents:
            self._ancestry(head, view, nodes, set())

        def ancestors(key):
            result, pending = set(), [key]
            while pending:
                item = pending.pop()
                if item not in result:
                    result.add(item)
                    pending.extend(nodes[item][2])
            return result

        left_key, right_key = map(_key, parents)
        left_anc, right_anc = ancestors(left_key), ancestors(right_key)
        _reject(left_key in right_anc or right_key in left_anc, "INVALID_LINEAGE")
        common = left_anc & right_anc
        maximal = [key for key in common if not any(key != other and key in ancestors(other) for other in common)]
        _reject(len(maximal) != 1 or _key(operation["base_head"]) != maximal[0], "INVALID_COMMON_BASE")
        base, left, right = (nodes[key][1] for key in (maximal[0], left_key, right_key))
        event = self._event(proposal, context, parents, operation["base_head"])
        _reject(event["event_kind"] != "merge" or event["resolution_refs"] != operation["resolution_refs"]
                or event["base_world_ref"] != left["branch"]["base_world_ref"]
                or left["branch"]["base_world_ref"] != right["branch"]["base_world_ref"])
        result = _copy(left)
        branch = result["branch"]
        maps = [{row["slot_id"]: row for row in state["branch"]["current_slots"]} for state in (base, left, right)]
        resolutions = {}
        for ref in operation["resolution_refs"]:
            wrapper = self.record(ref)
            _reject(wrapper["kind"] != "resolution" or wrapper["scope"] != self.scope.to_record(), "INVALID_SCOPE")
            row = wrapper["document"]
            _reject(row["slot_id"] in resolutions)
            resolutions[row["slot_id"]] = row
        used, slots, changes = set(), [], []
        resolution_action, resolution_effects = None, {}
        if resolutions:
            _reject(event["decision_context"] is None, "UNQUALIFIED_RESOLUTION")
            decision = self.record(event["decision_context"])["document"]
            witnesses = [row for row in view.actions() if row.get("action_ref") == decision["source_action_ref"]]
            _reject(len(witnesses) != 1 or witnesses[0]["source_branch_head"] not in parents, "UNQUALIFIED_RESOLUTION")
            resolution_action, resolution_effects = self._choice(event, witnesses[0]["source_branch_head"], view)
        for slot_id in sorted(set().union(*maps)):
            b, l, r = (_presence(values.get(slot_id)) for values in maps)
            sources = [values[slot_id] for values in maps if slot_id in values]
            _reject(len({row["definition_ref"] for row in sources}) != 1)
            definition_ref = sources[0]["definition_ref"]
            binding = [row for row in self._bindings.values() if row["target_kind"] == "fact" and row["target_id"] == slot_id]
            _reject(len(binding) != 1 or not binding[0]["mergeable"] or binding[0]["definition_ref"] != definition_ref, "UNMERGEABLE_SLOT")
            if l == r:
                selected = l
            elif l == b:
                selected = r
            elif r == b:
                selected = l
            else:
                resolution = resolutions.get(slot_id)
                _reject(resolution is None, "MERGE_CONFLICT")
                _reject((resolution["base"], resolution["left"], resolution["right"]) != (b, l, r))
                selected = resolution["result"]
                used.add(slot_id)
                effect = resolution_effects.get(binding[0]["projection_ref"])
                _reject(effect is None or effect["after"] != selected
                        or effect["source_event_ref"] != resolution["source_occurrence_ref"]
                        or effect["before"] not in (l, r), "UNQUALIFIED_RESOLUTION")
                # A changed resolution requires a real new domain occurrence and matching current slot.
                component = view.after(binding[0]["component_id"])
                candidates = [row for row in component["state"].get("facts", []) if row["slot_id"] == slot_id]
                _reject(len(candidates) != 1 or _presence(candidates[0]) != selected
                        or candidates[0]["source_event_ref"] != resolution["source_occurrence_ref"], "UNQUALIFIED_RESOLUTION")
            _reject(not selected["present"], "UNSUPPORTED_DELETION")
            self._value(definition_ref, selected["value"])
            source = next((row for row in sources[1:] if row["value"] == selected["value"]), sources[0])
            source_ref = resolutions[slot_id]["source_occurrence_ref"] if slot_id in used else source["source_event_ref"]
            slots.append({"slot_id": slot_id, "definition_ref": definition_ref,
                          "value": selected["value"], "source_event_ref": source_ref})
            if selected != b:
                changes.append({"slot_id": slot_id, "definition_ref": definition_ref, "before": b,
                                "after": selected, "source_occurrence_ref": source_ref})
        _reject(used != set(resolutions) or event["changes"] != changes, "INVALID_RESOLUTION")
        branch["current_slots"] = slots
        for key in HISTORY:
            branch["history"][key] = _ordered_union(left["branch"]["history"][key], right["branch"]["history"][key],
                _occ_key if key == "occurrences" else _key)
        branch["consumed"] = _ordered_union(left["branch"]["consumed"], right["branch"]["consumed"], _occ_key)
        branch["derived_view_refs"] = _ordered_union(left["branch"]["derived_view_refs"], right["branch"]["derived_view_refs"], lambda row: _key(row["ref"]))
        for ref, value in right["events"].items():
            _reject(ref in result["events"] and result["events"][ref] != value, "IDENTITY_CONFLICT")
            result["events"][ref] = value
        branch["lineage"] = {"kind": "merge", "parents": parents, "common_base": operation["base_head"],
            "bootstrap_ref": None, "event_ref": event["branch_event_id"], "shared_heads": branch["lineage"]["shared_heads"]}
        return result, event, resolution_action

    def _retain(self, branch, action, view):
        identity = _key(["action", [self.scope.world_id, self._player, action["action_ref"]]])
        _reject(any(_occ_key(row) == identity for row in branch["consumed"]), "ALREADY_CONSUMED")
        bundles = [row for row in view.retentions() if row.get("component_id") == action["player_component_id"]]
        _reject(len(bundles) != 1, "UNQUALIFIED_RETENTION")
        bundle = bundles[0]
        _shape(bundle, "component_id before_head occurrences consumed")
        _reject(bundle["before_head"] != action["player_before_head"], "UNQUALIFIED_RETENTION")
        staged = view.after(bundle["component_id"])["state"]
        _reject(type(bundle["occurrences"]) is not list or type(bundle["consumed"]) is not list
                or len(bundle["occurrences"]) > 128 or len(bundle["consumed"]) > 128, "VALUE_LIMIT")
        for kind, rows in (("Occurrence", bundle["occurrences"]), ("Consumed", bundle["consumed"])):
            for row in rows:
                self._valid(kind, row)
                _reject(row["origin_component_id"] != bundle["component_id"]
                        or not _contains(staged, row["payload_sha256"]), "UNQUALIFIED_RETENTION")
        action_rows = [row for row in bundle["consumed"] if _occ_key(row) == identity]
        _reject(len(action_rows) != 1 or action_rows[0]["payload_sha256"] != action["action_sha256"], "UNQUALIFIED_RETENTION")
        consumed = {_occ_key(row): row for row in bundle["consumed"]}
        _reject(len(consumed) != len(bundle["consumed"]), "IDENTITY_CONFLICT")
        for row in bundle["occurrences"]:
            _reject(consumed.get(_occ_key(row)) != {k: v for k, v in row.items() if k != "record_ref"}, "UNQUALIFIED_RETENTION")
        branch["history"]["occurrences"] = _ordered_union(branch["history"]["occurrences"], bundle["occurrences"], _occ_key)
        branch["consumed"] = _ordered_union(branch["consumed"], bundle["consumed"], _occ_key)

    def _append(self, branch, occurrence, retained=True):
        identity = _occ_key(occurrence)
        _reject(any(_occ_key(row) == identity for row in branch["consumed"]), "ALREADY_CONSUMED")
        consumed = {key: value for key, value in occurrence.items() if key != "record_ref"}
        branch["consumed"].append(consumed)
        if retained:
            branch["history"]["occurrences"].append(occurrence)

    def reduce(self, state, packet, view):
        state, packet = _copy(state), _copy(packet)
        _reject(type(view) is not BranchReadView or view._world != self.scope.world_id, "INVALID_VIEW")
        proposal = self._proposal(packet)
        self._valid("owner", state)
        _reject(any(state[key] != self._initial[key] for key in ("format", "world_id", "branch_id", "owner_player_id")), "INVALID_SCOPE")
        operation = proposal["operation"]
        kind = operation["kind"]
        for name, rows in (("Action", view.actions()), ("Effect", view.effects())):
            for row in rows:
                self._valid(name, row, "INVALID_VIEW")
        if kind != "advance":
            _reject(self.component_id in view._before or any(
                (component := json.loads(raw))["scope"] == self.scope.to_record()
                and component["state"].get("format") == FORMAT for raw in view._before.values()), "BRANCH_EXISTS")
        self._read(proposal, view)
        _reject((kind == "advance") != (state["branch"] is not None), "INVALID_LINEAGE")
        context = self._context(proposal, view, "root" if kind == "bootstrap" else "merge" if kind == "merge" else "choice")
        event, action = None, None
        if kind == "bootstrap":
            state["branch"] = self._bootstrap(proposal, view, context)
        elif kind == "merge":
            state, event, action = self._merge(proposal, view, context)
        else:
            head = operation["parent_head" if kind == "fork" else "previous_head"]
            component = view.before(head["component_id"])
            _reject(_head_of(component) != head, "STALE_COMPONENT")
            source = self._branch(component)
            if kind == "advance":
                _reject(component["component_id"] != self.component_id or component["owner_policy_id"] != self.policy_id
                        or source != state, "STALE_COMPONENT")
            else:
                _reject(source["branch_id"] == self.scope.subject_id or self.component_id in view._before, "BRANCH_EXISTS")
                state = source
            event = self._event(proposal, context, [head], None)
            _reject(event["base_world_ref"] != state["branch"]["base_world_ref"])
            _reject(event["event_kind"] != "choice" or event["changes"] != operation["changes"])
            action, effects = self._choice(event, head, view)
            self._changes(state["branch"], operation["changes"], effects)
            if kind == "fork":
                state["branch"]["lineage"] = {"kind": "fork", "parents": [head], "common_base": None,
                    "bootstrap_ref": None, "event_ref": event["branch_event_id"],
                    "shared_heads": state["branch"]["lineage"]["shared_heads"]}
        state["branch_id"] = self.scope.subject_id
        branch = state["branch"]
        branch.update(leaf_branch_id=self.scope.subject_id, generation_context_ref=context["context_id"], provenance=proposal["provenance"])
        if action is not None:
            self._retain(branch, action, view)
        request_occurrence = {"namespace": "update", "identity_parts": [self.component_id, packet["principal"], packet["request_id"]],
            "payload_sha256": _digest(packet), "record_ref": proposal["proposal_ref"], "origin_component_id": self.component_id,
            "origin_request_ref": packet["request_id"], "origin_event_ref": None if event is None else event["branch_event_id"]}
        self._append(branch, request_occurrence, retained=False)
        if event is not None:
            event_id = event["branch_event_id"]
            _reject(event_id in state["events"], "ALREADY_CONSUMED")
            state["events"][event_id] = event
            branch["history"]["branch_event_refs"].append(event_id)
            for field in ("worldstate_delta_refs", "future_generation_bias_refs"):
                branch["history"][field] = _ordered_union(branch["history"][field], event[field])
            self._append(branch, {"namespace": "branch_event", "identity_parts": [self.scope.world_id, self._player, event_id],
                "payload_sha256": _digest(event), "record_ref": event_id, "origin_component_id": self.component_id,
                "origin_request_ref": packet["request_id"], "origin_event_ref": event_id})
        _reject(any(len(rows) > 128 for rows in [branch["current_slots"], branch["consumed"], *branch["history"].values()]), "VALUE_LIMIT")
        self._valid("owner", state)
        return _copy(state)
