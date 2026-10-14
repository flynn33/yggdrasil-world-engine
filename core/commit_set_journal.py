"""Bounded atomic owner-set journal; trusted pure policies own domain authority.

Contract: docs/architecture/m4_commit_set_contract.md [YWE-REQ-0058].
This module neither changes TruthScope nor prepares independently writable stores.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import threading
from types import MappingProxyType

from core.state_journal import (
    JournalError, TruthScope, MAX_INTEGER, MAX_VALUE_BYTES, _DIGEST, _encode,
    _hash, _identifier, _integer, _object_bytes, _pairs, _parse_integer, _reject_number,
)


FORMAT = "ywe.commit_set_journal.v1"
MAX_COMPONENTS = 16
MAX_PROPOSALS = 8
MAX_STEPS = 32
MAX_ROUNDS = 64
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
STATE_LIMITS = (2 * 1024 * 1024, 131072, 40)
PACKET_LIMITS = (256 * 1024, 32768, 40)
REDUCTION_LIMITS = (8 * 1024 * 1024, 524288, 44)
DECISION_LIMITS = (65536, 8192, 16)
ENTRY_LIMITS = (512 * 1024, 65536, 44)
_PIN = {"component_id", "scope", "owner_policy_id"}
_HEAD = _PIN | {"revision", "head_digest", "state_sha256"}
_COMPONENT = _HEAD | {"state"}
_RAW_STEP = _PIN | {"principal", "proposal_id", "owner_request_ref", "packet", "state_after", "create"}
_PROPOSAL = {"principal", "proposal_id", "sequence", "predecessor_refs", "reads", "writes",
             "components", "compensations"}
_SELECTION = _PIN | {"owner_request_ref", "packet"}
_RAW_DECISION = {"principal", "proposal_id", "status", "code", "prior_decision", "step_indices"}
_COMPENSATION = {"component_id", "component_request_ref", "target_round_id", "target_principal",
                 "target_proposal_id", "target_component_request_ref", "target_component_head"}
_ENTRY = {"round_id", "expected_revision", "packet", "revision", "previous_digest",
          "before_state_digest", "after_state_digest", "decisions", "component_steps", "entry_digest"}


def _shape(value, fields):
    if type(value) is not dict or set(value) != fields:
        raise JournalError("INVALID_VALUE")


def _array(value, maximum, minimum=0):
    if type(value) is not list or len(value) < minimum:
        raise JournalError("INVALID_VALUE")
    if len(value) > maximum:
        raise JournalError("VALUE_LIMIT")


def _digest(value):
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise JournalError("INVALID_VALUE")


def _bounded_bytes(value, limits):
    """Same exact scalar domain as _object_bytes, with explicit aggregate budgets."""
    max_bytes, max_nodes, max_depth = limits
    pending, count = [(value, 0)], 0
    while pending:
        item, depth = pending.pop()
        count += 1
        if count > max_nodes or depth > max_depth:
            raise JournalError("VALUE_LIMIT")
        if item is None or type(item) is bool:
            continue
        if type(item) is int:
            if abs(item) > MAX_INTEGER:
                raise JournalError("INVALID_VALUE")
        elif type(item) is str:
            try:
                size = len(item.encode("utf-8"))
            except UnicodeError:
                raise JournalError("INVALID_VALUE") from None
            if size > MAX_VALUE_BYTES:
                raise JournalError("VALUE_LIMIT")
        elif type(item) is list:
            if len(item) > max_nodes:
                raise JournalError("VALUE_LIMIT")
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is dict:
            if len(item) > max_nodes or any(type(key) is not str for key in item):
                raise JournalError("INVALID_VALUE")
            pending.extend((child, depth + 1) for pair in item.items() for child in pair)
        else:
            raise JournalError("INVALID_VALUE")
    raw = _encode(value)
    if len(raw) > max_bytes:
        raise JournalError("VALUE_LIMIT")
    return raw


def _scope(value, world_id=None):
    _shape(value, {"world_id", "truth_scope", "subject_id"})
    scope = TruthScope(**value)
    if world_id is not None and scope.world_id != world_id:
        raise JournalError("INVALID_SCOPE")
    return scope


def _pin(value, world_id=None):
    _identifier(value["component_id"])
    _identifier(value["owner_policy_id"])
    _scope(value["scope"], world_id)


def _head(value, world_id=None):
    _shape(value, _HEAD)
    _pin(value, world_id)
    _integer(value["revision"], MAX_INTEGER)
    _digest(value["head_digest"])
    _digest(value["state_sha256"])


def _head_of(component):
    return {key: component[key] for key in _HEAD}


def _component(value, world_id):
    _shape(value, _COMPONENT)
    _head(_head_of(value), world_id)
    if _hash(_object_bytes(value["state"])) != value["state_sha256"]:
        raise JournalError("INVALID_VALUE")


def _binding(value):
    if type(value) is not CommitSetBinding:
        raise JournalError("INVALID_BINDING")


@dataclass(frozen=True)
class CommitSetBinding:
    world_id: str
    container_id: str

    def __post_init__(self):
        _identifier(self.world_id)
        _identifier(self.container_id)

    def to_record(self):
        return {"format": "ywe.commit_set_binding.v1", "world_id": self.world_id,
                "container_id": self.container_id}


@dataclass(frozen=True)
class RoundReceipt:
    revision: int
    entry_digest: str
    state_digest: str
    decisions_digest: str


def initial_component(binding, component_id, scope, owner_policy_id, state):
    _binding(binding)
    if type(scope) is not TruthScope or scope.world_id != binding.world_id:
        raise JournalError("INVALID_SCOPE")
    _identifier(component_id)
    _identifier(owner_policy_id)
    state_raw = _object_bytes(state)
    pin = {"component_id": component_id, "scope": scope.to_record(), "owner_policy_id": owner_policy_id}
    state_digest = _hash(state_raw)
    digest = _hash(_encode({"format": "ywe.component_genesis.v1", "binding": binding.to_record(),
                           **pin, "state_sha256": state_digest}))
    return {**pin, "revision": 0, "head_digest": digest, "state_sha256": state_digest,
            "state": json.loads(state_raw)}


def advance_component(binding, round_id, raw_step, previous_component):
    """Generate a deterministic head; caller must authenticate the staged prior."""
    _binding(binding)
    _identifier(round_id)
    _shape(raw_step, _RAW_STEP)
    _pin(raw_step, binding.world_id)
    for key in ("principal", "proposal_id", "owner_request_ref"):
        _identifier(raw_step[key])
    if type(raw_step["create"]) is not bool:
        raise JournalError("INVALID_VALUE")
    packet_raw = _object_bytes(raw_step["packet"])
    state_raw = _object_bytes(raw_step["state_after"])
    pin = {key: raw_step[key] for key in _PIN}
    if raw_step["create"]:
        if previous_component is not None:
            raise JournalError("INVALID_VALUE")
        before, revision = None, 1
    else:
        _component(previous_component, binding.world_id)
        if any(previous_component[key] != pin[key] for key in _PIN):
            raise JournalError("INVALID_VALUE")
        before, revision = _head_of(previous_component), previous_component["revision"] + 1
        _integer(revision, MAX_INTEGER)
    state_digest, packet_digest = _hash(state_raw), _hash(packet_raw)
    identity = {key: raw_step[key] for key in ("principal", "proposal_id", "owner_request_ref")}
    digest = _hash(_encode({"format": "ywe.component_step.v1", "binding": binding.to_record(),
        **pin, "previous_head": None if before is None else before["head_digest"],
        "revision": revision, "round_id": round_id, **identity, "packet_sha256": packet_digest,
        "before_state_sha256": None if before is None else before["state_sha256"],
        "after_state_sha256": state_digest}))
    after = {**pin, "revision": revision, "head_digest": digest, "state_sha256": state_digest}
    finalized = {"round_id": round_id, **pin, **identity, "packet_sha256": packet_digest,
                 "before": before, "after": after, "create": raw_step["create"]}
    return json.loads(_encode({**after, "state": json.loads(state_raw)})), json.loads(_encode(finalized))


def _unique_sorted(rows, key):
    identities = [key(row) for row in rows]
    if len(set(identities)) != len(identities):
        raise JournalError("INVALID_VALUE")
    return sorted(rows, key=key)


def _proposal_identity(proposal):
    return proposal["principal"], proposal["proposal_id"]


def canonical_round_packet(packet):
    packet = json.loads(_bounded_bytes(packet, PACKET_LIMITS))
    _shape(packet, {"format", "round_id", "sequence", "proposals"})
    if packet["format"] != "ywe.closed_round.v1":
        raise JournalError("INVALID_VALUE")
    _identifier(packet["round_id"])
    _integer(packet["sequence"], MAX_ROUNDS)
    _array(packet["proposals"], MAX_PROPOSALS, 1)
    for proposal in packet["proposals"]:
        _shape(proposal, _PROPOSAL)
        _identifier(proposal["principal"])
        _identifier(proposal["proposal_id"])
        _integer(proposal["sequence"], MAX_INTEGER)
        _array(proposal["predecessor_refs"], MAX_PROPOSALS)
        for predecessor in proposal["predecessor_refs"]:
            _shape(predecessor, {"principal", "proposal_id"})
            for value in predecessor.values():
                _identifier(value)
        proposal["predecessor_refs"] = _unique_sorted(proposal["predecessor_refs"], _proposal_identity)
        _array(proposal["reads"], MAX_COMPONENTS)
        for head in proposal["reads"]:
            _head(head)
        proposal["reads"] = _unique_sorted(proposal["reads"], lambda row: row["component_id"])
        _array(proposal["writes"], MAX_COMPONENTS)
        for component_id in proposal["writes"]:
            _identifier(component_id)
        proposal["writes"] = _unique_sorted(proposal["writes"], lambda row: row)
        _array(proposal["components"], MAX_COMPONENTS)
        for selection in proposal["components"]:
            _shape(selection, _SELECTION)
            _pin(selection)
            _identifier(selection["owner_request_ref"])
            _object_bytes(selection["packet"])
        proposal["components"] = _unique_sorted(proposal["components"], lambda row: row["component_id"])
        _array(proposal["compensations"], MAX_COMPONENTS)
        for mapping in proposal["compensations"]:
            _shape(mapping, _COMPENSATION)
            for key in _COMPENSATION - {"target_component_head"}:
                _identifier(mapping[key])
            _head(mapping["target_component_head"])
            if not any(row["component_id"] == mapping["component_id"] and
                       row["owner_request_ref"] == mapping["component_request_ref"]
                       for row in proposal["components"]):
                raise JournalError("INVALID_VALUE")
        proposal["compensations"] = _unique_sorted(proposal["compensations"],
            lambda row: (row["component_id"], row["component_request_ref"]))
    rows = _unique_sorted(packet["proposals"], _proposal_identity)
    identities = {_proposal_identity(row) for row in rows}
    for row in rows:
        if any(_proposal_identity(ref) not in identities for ref in row["predecessor_refs"]):
            raise JournalError("INVALID_VALUE")
    emitted, ordered = set(), []
    while rows:
        eligible = [row for row in rows if all(_proposal_identity(ref) in emitted
                                               for ref in row["predecessor_refs"])]
        if not eligible:
            raise JournalError("INVALID_VALUE")
        selected = min(eligible, key=lambda row: (row["sequence"], *_proposal_identity(row)))
        ordered.append(selected)
        emitted.add(_proposal_identity(selected))
        rows.remove(selected)
    packet["proposals"] = ordered
    return json.loads(_bounded_bytes(packet, PACKET_LIMITS))


def _state_bytes(state, binding, *, genesis=False):
    raw = _bounded_bytes(state, STATE_LIMITS)
    _shape(state, {"format", "world_id", "components"})
    if state["format"] != "ywe.commit_set_state.v1" or state["world_id"] != binding.world_id:
        raise JournalError("INVALID_VALUE")
    if type(state["components"]) is list and len(state["components"]) > MAX_COMPONENTS:
        raise JournalError("CAPACITY_EXCEEDED")
    _array(state["components"], MAX_COMPONENTS, 1)
    for component in state["components"]:
        _component(component, binding.world_id)
        if genesis and initial_component(binding, component["component_id"], _scope(component["scope"]),
                                          component["owner_policy_id"], component["state"]) != component:
            raise JournalError("INVALID_VALUE")
    if state["components"] != _unique_sorted(state["components"], lambda row: row["component_id"]):
        raise JournalError("INVALID_VALUE")
    return raw


def _prior_reference(value):
    _shape(value, {"round_id", "decision_index", "decision_sha256"})
    _identifier(value["round_id"])
    _integer(value["decision_index"], MAX_PROPOSALS - 1)
    _digest(value["decision_sha256"])


def _entry_preflight(entry, ordinal, binding):
    """Check every serialized envelope before replay invokes any owner."""
    _shape(entry, _ENTRY)
    _bounded_bytes(entry, ENTRY_LIMITS)
    _identifier(entry["round_id"])
    _integer(entry["revision"], MAX_ROUNDS)
    _integer(entry["expected_revision"], MAX_ROUNDS)
    if entry["revision"] != ordinal or entry["expected_revision"] != ordinal - 1:
        raise JournalError("INVALID_ARCHIVE")
    for key in ("previous_digest", "before_state_digest", "after_state_digest", "entry_digest"):
        _digest(entry[key])
    packet = canonical_round_packet(entry["packet"])
    if _encode(packet) != _encode(entry["packet"]) or packet["round_id"] != entry["round_id"] or packet["sequence"] != entry["expected_revision"]:
        raise JournalError("INVALID_ARCHIVE")
    for proposal in packet["proposals"]:
        for row in proposal["reads"] + proposal["components"]:
            _scope(row["scope"], binding.world_id)
    _array(entry["decisions"], MAX_PROPOSALS)
    _bounded_bytes(entry["decisions"], DECISION_LIMITS)
    if len(entry["decisions"]) != len(packet["proposals"]):
        raise JournalError("INVALID_ARCHIVE")
    for decision in entry["decisions"]:
        _shape(decision, _RAW_DECISION | {"proposal_sha256"})
        for key in ("principal", "proposal_id", "code"):
            _identifier(decision[key])
        _digest(decision["proposal_sha256"])
        if decision["status"] not in ("ACCEPTED", "REJECTED", "DUPLICATE"):
            raise JournalError("INVALID_ARCHIVE")
        if decision["prior_decision"] is not None:
            _prior_reference(decision["prior_decision"])
        _array(decision["step_indices"], MAX_STEPS)
        for index in decision["step_indices"]:
            _integer(index, MAX_STEPS - 1)
        if decision["status"] == "ACCEPTED":
            if decision["code"] != "ACCEPTED" or decision["prior_decision"] is not None:
                raise JournalError("INVALID_ARCHIVE")
        elif decision["status"] == "REJECTED":
            if decision["prior_decision"] is not None or decision["step_indices"]:
                raise JournalError("INVALID_ARCHIVE")
        elif decision["code"] != "DUPLICATE" or decision["prior_decision"] is None or decision["step_indices"]:
            raise JournalError("INVALID_ARCHIVE")
    _array(entry["component_steps"], MAX_STEPS)
    for step in entry["component_steps"]:
        _shape(step, _PIN | {"round_id", "principal", "proposal_id", "owner_request_ref",
                            "packet_sha256", "before", "after", "create"})
        _pin(step, binding.world_id)
        for key in ("round_id", "principal", "proposal_id", "owner_request_ref"):
            _identifier(step[key])
        _digest(step["packet_sha256"])
        if type(step["create"]) is not bool:
            raise JournalError("INVALID_ARCHIVE")
        if step["before"] is not None:
            _head(step["before"], binding.world_id)
        _head(step["after"], binding.world_id)
        if step["round_id"] != entry["round_id"] or step["create"] != (step["before"] is None):
            raise JournalError("INVALID_ARCHIVE")
        if step["create"] and step["after"]["revision"] != 1:
            raise JournalError("INVALID_ARCHIVE")
        if any(step[key] != step["after"][key] or step["before"] is not None and
               step[key] != step["before"][key] for key in _PIN):
            raise JournalError("INVALID_ARCHIVE")


def _archive_depth(value):
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 48:
            raise JournalError("INVALID_ARCHIVE")
        if type(item) is list:
            pending.extend((child, depth + 1) for child in item)
        elif type(item) is dict:
            pending.extend((child, depth + 1) for pair in item.items() for child in pair)


@dataclass(frozen=True, slots=True)
class CommitSetReadView:
    _decisions: object
    _requests: object
    _components: object
    _world_id: str

    def decision(self, principal, proposal_id):
        _identifier(principal)
        _identifier(proposal_id)
        raw = self._decisions.get((principal, proposal_id))
        return None if raw is None else json.loads(raw)

    def component_request(self, component_id, owner_request_ref):
        _identifier(component_id)
        _identifier(owner_request_ref)
        raw = self._requests.get((component_id, owner_request_ref))
        return None if raw is None else json.loads(raw)

    def component_at(self, exact_head):
        _head(exact_head, self._world_id)
        raw = self._components.get(_encode(exact_head))
        if raw is None:
            raise JournalError("UNKNOWN_COMPONENT_HEAD")
        return json.loads(raw)


@dataclass(frozen=True)
class _Snapshot:
    state: bytes
    entries: tuple
    rounds: object
    decisions: object
    requests: object
    components: object


class CommitSetJournal:
    """One publication point for component state, decisions and replay identities."""

    def __init__(self, binding, policy_id, initial_state, reducer):
        _binding(binding)
        _identifier(policy_id)
        if not callable(reducer):
            raise JournalError("INVALID_POLICY")
        self._binding = binding
        self._policy_id = policy_id
        self._initial = _state_bytes(initial_state, binding, genesis=True)
        self._reducer = reducer
        self._genesis = _hash(_encode(self._header()))
        self._lock = threading.RLock()
        self._reducing = self._reentry = False
        components = {_encode(_head_of(row)): _encode(row) for row in json.loads(self._initial)["components"]}
        empty = MappingProxyType({})
        self._snapshot = _Snapshot(self._initial, (), empty, empty, empty, MappingProxyType(components))
        self._archive_bytes(self._snapshot.state, self._snapshot.entries)

    def _header(self):
        return {"format": FORMAT, "binding": self._binding.to_record(), "policy_id": self._policy_id,
                "initial_state": json.loads(self._initial)}

    def _guard(self):
        if self._reducing:
            self._reentry = True
            raise JournalError("REENTRANT_ACCESS")

    def _archive_bytes(self, state, entries):
        raw = _encode({**self._header(), "entries": [json.loads(row) for row in entries],
                       "final_state": json.loads(state)})
        if len(raw) > MAX_ARCHIVE_BYTES:
            raise JournalError("VALUE_LIMIT")
        return raw

    def state(self):
        with self._lock:
            self._guard()
            return json.loads(self._snapshot.state)

    def vector(self):
        with self._lock:
            self._guard()
            return [_head_of(row) for row in json.loads(self._snapshot.state)["components"]]

    def decisions(self, round_id):
        with self._lock:
            self._guard()
            _identifier(round_id)
            indexed = self._snapshot.rounds.get(round_id)
            if indexed is None:
                raise JournalError("UNKNOWN_ROUND")
            return json.loads(self._snapshot.entries[indexed[1].revision - 1])["decisions"]

    def save(self):
        with self._lock:
            self._guard()
            return self._archive_bytes(self._snapshot.state, self._snapshot.entries)

    def head(self):
        with self._lock:
            self._guard()
            return json.loads(self._snapshot.entries[-1])["entry_digest"] if self._snapshot.entries else self._genesis

    def checkpoint(self):
        with self._lock:
            self._guard()
            return self.save(), self.head()

    def _history(self, snapshot):
        return CommitSetReadView(snapshot.decisions, snapshot.requests, snapshot.components, self._binding.world_id)

    def _check_packet_history(self, packet, history):
        for proposal in packet["proposals"]:
            prior = history.decision(*_proposal_identity(proposal))
            if prior is not None and prior["decision"]["proposal_sha256"] != _hash(_encode(proposal)):
                raise JournalError("IDENTITY_CONFLICT")
            for row in proposal["reads"] + proposal["components"]:
                _scope(row["scope"], self._binding.world_id)
            for mapping in proposal["compensations"]:
                _scope(mapping["target_component_head"]["scope"], self._binding.world_id)
                target = history.component_request(mapping["component_id"], mapping["target_component_request_ref"])
                selection = next(row for row in proposal["components"]
                                 if row["component_id"] == mapping["component_id"])
                if target is None or any(target[key] != mapping[target_key] for key, target_key in (
                        ("round_id", "target_round_id"), ("principal", "target_principal"),
                        ("proposal_id", "target_proposal_id"), ("head", "target_component_head"))) or any(
                            target["head"][key] != selection[key] for key in _PIN):
                    raise JournalError("UNKNOWN_COMPENSATION")

    def _finish_reduction(self, packet, result, snapshot, history):
        try:
            result = json.loads(_bounded_bytes(result, REDUCTION_LIMITS))
            if type(result) is not dict or set(result) not in (
                    {"decisions", "component_steps"}, {"decisions", "component_steps", "state"}):
                raise JournalError("INVALID_VALUE")
            _array(result["decisions"], MAX_PROPOSALS)
            _array(result["component_steps"], MAX_STEPS)
            if len(result["decisions"]) != len(packet["proposals"]):
                raise JournalError("INVALID_VALUE")
            state = json.loads(snapshot.state)
            staged = {row["component_id"]: row for row in state["components"]}
            decisions, finalized = [], []
            new_decisions, new_requests, new_components = dict(snapshot.decisions), dict(snapshot.requests), dict(snapshot.components)
            next_index = 0
            for ordinal, (proposal, decision) in enumerate(zip(packet["proposals"], result["decisions"])):
                _shape(decision, _RAW_DECISION)
                if _proposal_identity(decision) != _proposal_identity(proposal):
                    raise JournalError("INVALID_VALUE")
                _identifier(decision["code"])
                _array(decision["step_indices"], MAX_STEPS)
                for index in decision["step_indices"]:
                    _integer(index, MAX_STEPS - 1)
                prior = history.decision(*_proposal_identity(proposal))
                if prior is not None:
                    ref = {key: prior[key] for key in ("round_id", "decision_index", "decision_sha256")}
                    if decision["status"] != "DUPLICATE" or decision["code"] != "DUPLICATE" or _encode(decision["prior_decision"]) != _encode(ref) or decision["step_indices"]:
                        raise JournalError("INVALID_VALUE")
                elif decision["status"] == "REJECTED":
                    if decision["prior_decision"] is not None or decision["step_indices"]:
                        raise JournalError("INVALID_VALUE")
                elif decision["status"] == "ACCEPTED":
                    selections = proposal["components"]
                    expected = list(range(next_index, next_index + len(selections)))
                    if decision["code"] != "ACCEPTED" or decision["prior_decision"] is not None or decision["step_indices"] != expected or proposal["writes"] != [row["component_id"] for row in selections]:
                        raise JournalError("INVALID_VALUE")
                    for selection in selections:
                        if next_index >= len(result["component_steps"]):
                            raise JournalError("INVALID_VALUE")
                        step = result["component_steps"][next_index]
                        _shape(step, _RAW_STEP)
                        if _proposal_identity(step) != _proposal_identity(proposal) or any(
                                _encode(step[key]) != _encode(selection[key]) for key in _SELECTION):
                            raise JournalError("INVALID_VALUE")
                        identity = (step["component_id"], step["owner_request_ref"])
                        if identity in new_requests:
                            raise JournalError("IDENTITY_CONFLICT")
                        if step["create"] is True and step["component_id"] not in staged and len(staged) >= MAX_COMPONENTS:
                            raise JournalError("CAPACITY_EXCEEDED")
                        component, trace = advance_component(self._binding, packet["round_id"], step,
                                                            staged.get(step["component_id"]))
                        staged[step["component_id"]] = component
                        finalized.append(trace)
                        new_components[_encode(trace["after"])] = _encode(component)
                        new_requests[identity] = _encode({"round_id": packet["round_id"],
                            "principal": proposal["principal"], "proposal_id": proposal["proposal_id"],
                            "component_id": step["component_id"], "owner_request_ref": step["owner_request_ref"],
                            "step_index": next_index, "packet_sha256": trace["packet_sha256"], "head": trace["after"]})
                        next_index += 1
                else:
                    raise JournalError("INVALID_VALUE")
                complete = {**decision, "proposal_sha256": _hash(_encode(proposal))}
                decisions.append(complete)
                if prior is None:
                    new_decisions[_proposal_identity(proposal)] = _encode({"round_id": packet["round_id"],
                        "decision_index": ordinal, "decision_sha256": _hash(_encode(complete)), "decision": complete})
            if next_index != len(result["component_steps"]):
                raise JournalError("INVALID_VALUE")
            state["components"] = [staged[key] for key in sorted(staged)]
            state_raw = _state_bytes(state, self._binding)
            if "state" in result and _state_bytes(result["state"], self._binding) != state_raw:
                raise JournalError("INVALID_VALUE")
            decisions_raw = _bounded_bytes(decisions, DECISION_LIMITS)
            return state_raw, decisions_raw, finalized, new_decisions, new_requests, new_components
        except JournalError as error:
            if error.code in {"VALUE_LIMIT", "CAPACITY_EXCEEDED", "IDENTITY_CONFLICT"}:
                raise
            raise JournalError("INVALID_REDUCTION") from None
        except (ValueError, TypeError, KeyError, IndexError, UnicodeError, RecursionError):
            raise JournalError("INVALID_REDUCTION") from None

    def commit(self, round_id, expected_revision, packet):
        with self._lock:
            self._guard()
            _identifier(round_id)
            _integer(expected_revision, MAX_ROUNDS)
            raw = _bounded_bytes(packet, PACKET_LIMITS)
            packet = canonical_round_packet(packet)
            if raw != _encode(packet) or packet["round_id"] != round_id or packet["sequence"] != expected_revision:
                raise JournalError("INVALID_VALUE")
            request = {"round_id": round_id, "expected_revision": expected_revision, "packet": packet}
            fingerprint = _encode(request)
            snapshot = self._snapshot
            if round_id in snapshot.rounds:
                original, receipt = snapshot.rounds[round_id]
                if fingerprint != original:
                    raise JournalError("IDENTITY_CONFLICT")
                return receipt
            if expected_revision != len(snapshot.entries):
                raise JournalError("REVISION_CONFLICT")
            if len(snapshot.entries) >= MAX_ROUNDS:
                raise JournalError("CAPACITY_EXCEEDED")
            history = self._history(snapshot)
            self._check_packet_history(packet, history)
            declared_ids = {row["component_id"] for proposal in packet["proposals"] for row in proposal["components"]}
            current_ids = {row["component_id"] for row in json.loads(snapshot.state)["components"]}
            if len(current_ids | declared_ids) > MAX_COMPONENTS:
                raise JournalError("CAPACITY_EXCEEDED")
            self._reducing, self._reentry = True, False
            try:
                result = self._reducer(self._binding, json.loads(snapshot.state), json.loads(raw), history)
                if self._reentry:
                    raise JournalError("REENTRANT_ACCESS")
            except Exception:
                raise JournalError("POLICY_REJECTED") from None
            finally:
                self._reducing = False
            state, decisions, steps, decision_index, requests, components = self._finish_reduction(packet, result, snapshot, history)
            body = {**request, "revision": len(snapshot.entries) + 1,
                    "previous_digest": json.loads(snapshot.entries[-1])["entry_digest"] if snapshot.entries else self._genesis,
                    "before_state_digest": _hash(snapshot.state), "after_state_digest": _hash(state),
                    "decisions": json.loads(decisions), "component_steps": steps}
            digest = _hash(_encode(body))
            entry = _bounded_bytes({**body, "entry_digest": digest}, ENTRY_LIMITS)
            entries = snapshot.entries + (entry,)
            self._archive_bytes(state, entries)
            receipt = RoundReceipt(len(entries), digest, _hash(state), _hash(decisions))
            self._snapshot = _Snapshot(state, entries,
                MappingProxyType({**snapshot.rounds, round_id: (fingerprint, receipt)}),
                MappingProxyType(decision_index), MappingProxyType(requests), MappingProxyType(components))
            return receipt

    @classmethod
    def load(cls, raw, binding, policy_id, initial_state, reducer, trusted_head):
        if type(raw) is not bytes or len(raw) > MAX_ARCHIVE_BYTES:
            raise JournalError("INVALID_ARCHIVE")
        try:
            _digest(trusted_head)
        except JournalError:
            raise JournalError("INVALID_TRUSTED_HEAD") from None
        try:
            archive = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                parse_int=_parse_integer, parse_float=_reject_number, parse_constant=_reject_number)
            _archive_depth(archive)
            _shape(archive, {"format", "binding", "policy_id", "initial_state", "entries", "final_state"})
            journal = cls(binding, policy_id, initial_state, reducer)
            if any(archive[key] != value for key, value in journal._header().items()):
                raise JournalError("INVALID_ARCHIVE")
            # Validate supplied initial bytes too: Python numeric equality must not admit floats/bools.
            if _state_bytes(archive["initial_state"], binding, genesis=True) != journal._initial:
                raise JournalError("INVALID_ARCHIVE")
            _array(archive["entries"], MAX_ROUNDS)
            final = _state_bytes(archive["final_state"], binding)
            for ordinal, original in enumerate(archive["entries"], 1):
                _entry_preflight(original, ordinal, binding)
            for original in archive["entries"]:
                _shape(original, _ENTRY)
                original_raw = _bounded_bytes(original, ENTRY_LIMITS)
                _integer(original["revision"], MAX_ROUNDS)
                if original["revision"] != len(journal._snapshot.entries) + 1:
                    raise JournalError("INVALID_ARCHIVE")
                prior_count = len(journal._snapshot.entries)
                journal.commit(original["round_id"], original["expected_revision"], original["packet"])
                if len(journal._snapshot.entries) != prior_count + 1 or journal._snapshot.entries[-1] != original_raw:
                    raise JournalError("INVALID_ARCHIVE")
            if journal._snapshot.state != final or journal.head() != trusted_head:
                raise JournalError("INVALID_ARCHIVE")
            return journal
        except (JournalError, ValueError, TypeError, KeyError, UnicodeError, RecursionError):
            raise JournalError("INVALID_ARCHIVE") from None
