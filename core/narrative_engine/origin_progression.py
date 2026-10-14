"""Evidence-bound origin component reference owner (YWE-REQ-0055)."""

import hashlib
import json

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from .. import core_values as cv
from ..state_journal import CommitJournal, JournalError, TruthScope, _identifier, _object_bytes


FORMAT = "ywe.origin_progression.v1"


def _closed(value, keys):
    if type(value) is not dict or set(value) != set(keys.split()):
        raise JournalError("INVALID_POLICY")


def _items(value, minimum, maximum):
    if type(value) is not list or not minimum <= len(value) <= maximum:
        raise JournalError("INVALID_POLICY")


def _refs(value, minimum=1, maximum=65):
    _items(value, minimum, maximum)
    for item in value:
        _identifier(item)
    if len(set(value)) != len(value):
        raise JournalError("INVALID_POLICY")


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _provenance(value):
    _closed(value, "cosmic_pattern_snapshot_ref diagnostic_ref generation_plan_ref source_ash_refs")
    cv.CoreProvenance(**value)
    for key in ("cosmic_pattern_snapshot_ref", "diagnostic_ref", "generation_plan_ref"):
        _identifier(value[key])
    _refs(value["source_ash_refs"])


def _validator(schema, name):
    raw = _object_bytes(schema)
    schema = json.loads(raw)
    if (schema.get("$id") != "https://ywe.local/schemas/" + name + "_schema.json"
            or schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema"):
        raise JournalError("INVALID_POLICY")
    pending = [schema]
    while pending:
        node = pending.pop()
        if type(node) is dict:
            if "$ref" in node or "$dynamicRef" in node:
                raise JournalError("INVALID_POLICY")
            pending.extend(node.values())
        elif type(node) is list:
            pending.extend(node)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema), _digest(raw)


class OriginProgressionPolicy:
    """Trusted, detached component reduction without publication authority."""

    def __init__(self, world_id, player_id, profile, creation, grants, evidence,
                 action_schema, memory_schema):
        self._scope = TruthScope(world_id, "player_state", player_id)
        try:
            profile = json.loads(_object_bytes(profile))
            creation = json.loads(_object_bytes(creation))
            grants = json.loads(_object_bytes(grants))
            _closed(profile, "profile_id initial_phase phases transitions")
            _identifier(profile["profile_id"])
            _refs(profile["phases"], 1, 16)
            if profile["initial_phase"] not in profile["phases"]:
                raise JournalError("INVALID_POLICY")
            _items(profile["transitions"], 0, 32)
            self._edges = {}
            for edge in profile["transitions"]:
                _closed(edge, "from_phase to_phase minimum_actions")
                pair = edge["from_phase"], edge["to_phase"]
                if (any(item not in profile["phases"] for item in pair) or pair[0] == pair[1]
                        or pair in self._edges or type(edge["minimum_actions"]) is not int
                        or not 1 <= edge["minimum_actions"] <= 16):
                    raise JournalError("INVALID_POLICY")
                self._edges[pair] = edge["minimum_actions"]
            _closed(creation, "mortal_identity_ref identity_status provenance")
            _identifier(creation["mortal_identity_ref"])
            if creation["identity_status"] != "veiled":
                raise JournalError("INVALID_POLICY")
            _provenance(creation["provenance"])
            if not 1 <= len(grants) <= 32:
                raise JournalError("INVALID_POLICY")
            for principal, operations in grants.items():
                _identifier(principal)
                _refs(operations, 1, 2)
                if any(operation not in ("remember", "advance") for operation in operations):
                    raise JournalError("INVALID_POLICY")
            self._grants = grants
            action_validator, action_digest = _validator(action_schema, "player_action_trace")
            memory_validator, memory_digest = _validator(memory_schema, "player_memory_record")
            self._evidence = {}
            _items(evidence, 0, 128)
            total = 0
            for source in evidence:
                raw = _object_bytes(source)
                item = json.loads(raw)
                _closed(item, "evidence_ref world_id player_id operation prior_phase target_phase actions memories provenance")
                _identifier(item["evidence_ref"])
                if (item["evidence_ref"] in self._evidence or item["world_id"] != world_id
                        or item["player_id"] != player_id or item["operation"] not in ("remember", "advance")
                        or item["prior_phase"] not in profile["phases"] or item["target_phase"] not in profile["phases"]):
                    raise JournalError("INVALID_POLICY")
                _provenance(item["provenance"])
                _items(item["actions"], 1, 16)
                _items(item["memories"], 1, 16)
                actions = {}
                for action in item["actions"]:
                    if (type(action) is not dict or not action_validator.is_valid(action) or action.get("schema_id") != "ywe.player_action_trace.v1"
                            or action.get("schema_version") != "0.1.0" or action.get("player_id") != player_id
                            or action.get("significance") not in ("meaningful", "branch_forming", "mythic", "prophetic")):
                        raise JournalError("INVALID_POLICY")
                    _identifier(action["action_trace_id"])
                    _refs(action["source_refs"])
                    if "branch_ref" in action:
                        _identifier(action["branch_ref"])
                    if action["action_trace_id"] in actions:
                        raise JournalError("INVALID_POLICY")
                    actions[action["action_trace_id"]] = action
                memory_ids, covered = set(), set()
                for memory in item["memories"]:
                    if (type(memory) is not dict or not memory_validator.is_valid(memory) or memory.get("schema_id") != "ywe.player_memory_record.v1"
                            or memory.get("schema_version") != "0.1.0"):
                        raise JournalError("INVALID_POLICY")
                    _identifier(memory["memory_id"])
                    _refs(memory["source_refs"])
                    action = actions.get(memory["source_action_trace_ref"])
                    if (memory["memory_id"] in memory_ids or action is None
                            or "branch_ref" in memory and memory["branch_ref"] != action.get("branch_ref")):
                        raise JournalError("INVALID_POLICY")
                    memory_ids.add(memory["memory_id"])
                    covered.add(memory["source_action_trace_ref"])
                if covered != set(actions):
                    raise JournalError("INVALID_POLICY")
                total += len(raw)
                if total > 1048576:
                    raise JournalError("INVALID_POLICY")
                self._evidence[item["evidence_ref"]] = raw
            policy = {"format": FORMAT, "scope": self._scope.to_record(), "profile": profile,
                      "creation": creation, "grants": grants, "action_schema_sha256": action_digest,
                      "memory_schema_sha256": memory_digest}
            self._policy_id = "origin.v1:" + _digest(_object_bytes(policy))
            self._initial = _object_bytes({"format": FORMAT, "world_id": world_id, "player_id": player_id,
                "profile_id": profile["profile_id"], "creation": creation,
                "current_phase": profile["initial_phase"], "actions": [], "memories": [], "advances": []})
        except (JournalError, cv.CoreContractError, SchemaError, KeyError, TypeError, ValueError):
            raise JournalError("INVALID_POLICY") from None

    @property
    def scope(self):
        return self._scope

    @property
    def policy_id(self):
        return self._policy_id

    def initial_state(self):
        return json.loads(self._initial)

    def evidence(self, reference):
        """Return a detached validated bundle for trusted aggregate qualification."""
        _identifier(reference)
        raw = self._evidence.get(reference)
        if raw is None:
            raise JournalError("UNKNOWN_EVIDENCE")
        return json.loads(raw)

    def packet(self, principal, request_id, evidence_ref):
        _identifier(request_id)
        item = self.evidence(evidence_ref)
        if principal not in self._grants or item["operation"] not in self._grants[principal]:
            raise JournalError("UNAUTHORIZED_WRITER")
        return {"request_ref": request_id, "principal": principal,
                "evidence_ref": evidence_ref, "evidence_sha256": _digest(self._evidence[evidence_ref])}

    def reduce(self, state, packet):
        """Reduce an owner's verified component; neither argument is mutated."""
        state = json.loads(_object_bytes(state))
        packet = json.loads(_object_bytes(packet))
        _closed(packet, "request_ref principal evidence_ref evidence_sha256")
        if packet != self.packet(packet["principal"], packet["request_ref"], packet["evidence_ref"]):
            raise JournalError("POLICY_REJECTED")
        item = json.loads(self._evidence[packet["evidence_ref"]])
        if item["prior_phase"] != state["current_phase"]:
            raise JournalError("POLICY_REJECTED")
        old_actions = {row["action_trace_id"]: row for row in state["actions"]}
        new_actions = {row["action_trace_id"]: row for row in item["actions"]}
        if any(key in old_actions and old_actions[key] != row for key, row in new_actions.items()):
            raise JournalError("POLICY_REJECTED")
        old_memories = {row["memory_id"] for row in state["memories"]}
        if any(row["memory_id"] in old_memories for row in item["memories"]):
            raise JournalError("POLICY_REJECTED")
        if len(state["memories"]) + len(item["memories"]) > 128:
            raise JournalError("VALUE_LIMIT")
        if item["operation"] == "remember":
            if item["target_phase"] != state["current_phase"]:
                raise JournalError("POLICY_REJECTED")
        else:
            minimum = self._edges.get((state["current_phase"], item["target_phase"]))
            used = {ref for row in state["advances"] for ref in row["action_refs"]}
            if minimum is None or len(new_actions) < minimum or used.intersection(new_actions):
                raise JournalError("POLICY_REJECTED")
            state["advances"].append({"request_ref": packet["request_ref"], "evidence_ref": item["evidence_ref"],
                "from_phase": state["current_phase"], "to_phase": item["target_phase"], "action_refs": list(new_actions)})
            state["current_phase"] = item["target_phase"]
        state["actions"].extend(row for key, row in new_actions.items() if key not in old_actions)
        state["memories"].extend(item["memories"])
        return json.loads(_object_bytes(state))


class OriginProgressionStore:
    """Trusted composition owns catalog/grants; callers receive restricted handles."""

    def __init__(self, world_id, player_id, profile, creation, grants, evidence,
                 action_schema, memory_schema):
        self._policy = OriginProgressionPolicy(world_id, player_id, profile, creation,
                                               grants, evidence, action_schema, memory_schema)
        self._scope = self._policy.scope
        self._policy_id = self._policy.policy_id
        self._initial = self._policy.initial_state()
        self._writers = {principal: object() for principal in self._policy._grants}
        self._journal = CommitJournal(self._scope, self._policy_id, self._initial, self._reduce)

    def writer(self, principal):
        """Trusted composition only: issue the principal's restricted local handle."""
        _identifier(principal)
        if principal not in self._writers:
            raise JournalError("UNAUTHORIZED_WRITER")
        return self._writers[principal]

    def _packet(self, principal, request_id, evidence_ref):
        return self._policy.packet(principal, request_id, evidence_ref)

    def _reduce(self, scope, state, packet):
        if scope != self._scope:
            raise JournalError("POLICY_REJECTED")
        return self._policy.reduce(state, packet)

    def publish(self, writer, request_id, expected_revision, evidence_ref):
        principal = next((name for name, handle in self._writers.items() if writer is handle), None)
        if principal is None:
            raise JournalError("UNAUTHORIZED_WRITER")
        packet = self._packet(principal, request_id, evidence_ref)
        return self._journal.commit(request_id, expected_revision, packet)

    def state(self):
        return self._journal.state()

    def checkpoint(self):
        return self._journal.checkpoint()

    @classmethod
    def load(cls, raw, trusted_head, *configuration):
        owner = cls(*configuration)
        journal = CommitJournal.load(raw, owner._scope, owner._policy_id, owner._reduce, trusted_head)
        archive = json.loads(journal.save())
        if archive["initial_state"] != owner._initial or any(
                entry["request_id"] != entry["packet"]["request_ref"] or entry["compensates"] is not None
                for entry in archive["entries"]):
            raise JournalError("INVALID_ARCHIVE")
        owner._journal = journal
        return owner
